from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
import uuid

from app.database.database import get_db
from app.models import models
from app.services.auth_service import get_current_active_user
from app.services.question_correlation_service import create_transitive_correlations, backfill_transitive_correlations
from app.services.llm_service import LLMService
from app.services import scope_validation_service
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-tools", tags=["AI Tools"])

class QuestionCorrelationRequest(BaseModel):
    question_a_id: str
    question_b_id: str
    framework_id_a: str  # Framework ID for question A
    framework_id_b: str  # Framework ID for question B
    scope_name: str  # e.g., 'Product', 'Organization', 'Other', etc.
    scope_entity_id: Optional[str] = None  # UUID of the entity (null for 'Other' scope)

class QuestionCorrelationResponse(BaseModel):
    id: str
    question_a_id: str
    question_b_id: str
    created_by: str
    created_at: str

class FrameworkQuestionsResponse(BaseModel):
    id: str
    text: str
    description: Optional[str]
    mandatory: bool

class AICorrelationRequest(BaseModel):
    framework_a_id: str
    framework_b_id: str
    assessment_type_id: str

class AICorrelationSuggestion(BaseModel):
    question_a_id: str
    question_b_id: str
    question_a_text: str
    question_b_text: str
    confidence: int
    reasoning: str

class AICorrelationResponse(BaseModel):
    suggestions: List[AICorrelationSuggestion]
    framework_a_name: str
    framework_b_name: str
    total_suggestions: int

@router.post("/correlate-questions")
async def correlate_questions(
    request: QuestionCorrelationRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Correlate two questions from different frameworks (creates correlation for user's organization)."""
    print(f"DEBUG: correlate_questions called with question_a={request.question_a_id}, question_b={request.question_b_id}")

    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can correlate questions")

    try:
        # Validate scope
        scope_entity_id_uuid = None
        if request.scope_entity_id and str(request.scope_entity_id).strip():
            try:
                scope_entity_id_uuid = uuid.UUID(request.scope_entity_id)
            except (ValueError, AttributeError):
                raise HTTPException(status_code=400, detail="Invalid scope_entity_id format")

        try:
            scope_validation = scope_validation_service.validate_scope(
                db=db,
                scope_name=request.scope_name,
                scope_entity_id=scope_entity_id_uuid
            )
            scope_id = scope_validation['scope_id']
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Validate framework scope compatibility
        try:
            framework_a_config = scope_validation_service.get_framework_scope_config(
                db=db,
                framework_id=uuid.UUID(request.framework_id_a)
            )
            framework_b_config = scope_validation_service.get_framework_scope_config(
                db=db,
                framework_id=uuid.UUID(request.framework_id_b)
            )

            # Get framework names for error messages
            framework_a = db.query(models.Framework).filter(
                models.Framework.id == request.framework_id_a
            ).first()
            framework_b = db.query(models.Framework).filter(
                models.Framework.id == request.framework_id_b
            ).first()

            if not framework_a or not framework_b:
                raise HTTPException(status_code=404, detail="One or both frameworks not found")

            # Find common allowed scope types
            allowed_a = set(framework_a_config['allowed_scope_types']) if framework_a_config['allowed_scope_types'] else set()
            allowed_b = set(framework_b_config['allowed_scope_types']) if framework_b_config['allowed_scope_types'] else set()

            # If either framework has no restrictions (empty allowed list), treat as allowing all scopes
            if not allowed_a and not allowed_b:
                # Both frameworks have no scope restrictions - any scope is allowed
                common_scopes = scope_validation_service.get_supported_scope_types()
            elif not allowed_a:
                # Framework A has no restrictions - use Framework B's allowed scopes
                common_scopes = list(allowed_b)
            elif not allowed_b:
                # Framework B has no restrictions - use Framework A's allowed scopes
                common_scopes = list(allowed_a)
            else:
                # Both have restrictions - find intersection
                common_scopes = list(allowed_a & allowed_b)

            # Check if frameworks have compatible scope types
            if not common_scopes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot correlate questions between '{framework_a.name}' and '{framework_b.name}'. "
                           f"These frameworks have incompatible scope requirements. "
                           f"'{framework_a.name}' allows: {', '.join(allowed_a) if allowed_a else 'Any'}. "
                           f"'{framework_b.name}' allows: {', '.join(allowed_b) if allowed_b else 'Any'}. "
                           f"No common scope types found. "
                           f"Solution: Add a common scope type (e.g., 'Other') to one or both frameworks' allowed scope types."
                )

            # Validate that selected scope is in the common allowed scopes
            if request.scope_name not in common_scopes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Scope type '{request.scope_name}' is not allowed by both frameworks. "
                           f"Common allowed scope types: {', '.join(common_scopes)}. "
                           f"Please select one of the common scope types."
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating framework scope compatibility: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to validate framework compatibility: {str(e)}")

        # Validate that questions exist
        question_a = db.query(models.Question).filter(models.Question.id == request.question_a_id).first()
        if not question_a:
            raise HTTPException(status_code=404, detail="Question A not found")

        question_b = db.query(models.Question).filter(models.Question.id == request.question_b_id).first()
        if not question_b:
            raise HTTPException(status_code=404, detail="Question B not found")

        # Validate that both questions have the same assessment type
        # (conformity questions can only correlate with conformity, audit with audit)
        if question_a.assessment_type_id != question_b.assessment_type_id:
            assessment_type_a = db.query(models.AssessmentType).filter(
                models.AssessmentType.id == question_a.assessment_type_id
            ).first()
            assessment_type_b = db.query(models.AssessmentType).filter(
                models.AssessmentType.id == question_b.assessment_type_id
            ).first()

            type_name_a = assessment_type_a.type_name.capitalize() if assessment_type_a else "Unknown"
            type_name_b = assessment_type_b.type_name.capitalize() if assessment_type_b else "Unknown"

            raise HTTPException(
                status_code=400,
                detail=f"Cannot correlate questions from different assessment types. Question A is '{type_name_a}' and Question B is '{type_name_b}'. Only questions of the same assessment type can be correlated."
            )

        # Validate that questions are from different frameworks
        # Get frameworks for each question
        framework_a = db.query(models.Framework).join(
            models.FrameworkQuestion,
            models.Framework.id == models.FrameworkQuestion.framework_id
        ).filter(models.FrameworkQuestion.question_id == request.question_a_id).first()

        framework_b = db.query(models.Framework).join(
            models.FrameworkQuestion,
            models.Framework.id == models.FrameworkQuestion.framework_id
        ).filter(models.FrameworkQuestion.question_id == request.question_b_id).first()

        if not framework_a or not framework_b:
            raise HTTPException(status_code=400, detail="Questions must be associated with frameworks")

        if framework_a.id == framework_b.id:
            raise HTTPException(status_code=400, detail="Cannot correlate questions from the same framework")

        # Check if correlation already exists (in either direction) for this org and scope
        correlation_query = db.query(models.QuestionCorrelation).filter(
            and_(
                or_(
                    and_(
                        models.QuestionCorrelation.question_a_id == request.question_a_id,
                        models.QuestionCorrelation.question_b_id == request.question_b_id
                    ),
                    and_(
                        models.QuestionCorrelation.question_a_id == request.question_b_id,
                        models.QuestionCorrelation.question_b_id == request.question_a_id
                    )
                ),
                # Check within the same organization
                models.QuestionCorrelation.organisation_id == current_user.organisation_id,
                # Check within the same scope
                models.QuestionCorrelation.scope_id == scope_id
            )
        )

        # Add scope_entity_id filter
        if scope_entity_id_uuid is not None:
            correlation_query = correlation_query.filter(
                models.QuestionCorrelation.scope_entity_id == scope_entity_id_uuid
            )
        else:
            # For 'Other' scope, match correlations with NULL scope_entity_id
            correlation_query = correlation_query.filter(
                models.QuestionCorrelation.scope_entity_id.is_(None)
            )

        existing_correlation = correlation_query.first()

        if existing_correlation:
            scope_display = scope_validation_service.get_scope_display_name(
                db, request.scope_name, scope_entity_id_uuid
            )
            raise HTTPException(
                status_code=400,
                detail=f"These questions are already correlated for scope '{scope_display}' in your organization"
            )

        # Check for framework-specific correlation restriction:
        # A question from one framework can only correlate with ONE question from another framework
        print(f"DEBUG: Checking framework-specific validation for {framework_a.name} <-> {framework_b.name}")
        print(f"DEBUG: REACHED FRAMEWORK-SPECIFIC VALIDATION SECTION")
        logger.info(f"Checking framework-specific validation for {framework_a.name} <-> {framework_b.name}")

        # Check if question_a already has a correlation with any question from framework_b
        # for the SAME scope (correlations should be per-scope)
        try:
            question_a_correlations_query = db.query(models.QuestionCorrelation).filter(
                and_(
                    or_(
                        models.QuestionCorrelation.question_a_id == request.question_a_id,
                        models.QuestionCorrelation.question_b_id == request.question_a_id
                    ),
                    models.QuestionCorrelation.scope_id == scope_id
                )
            )

            # Add scope_entity_id filter to make it scope-specific
            if scope_entity_id_uuid is not None:
                question_a_correlations_query = question_a_correlations_query.filter(
                    models.QuestionCorrelation.scope_entity_id == scope_entity_id_uuid
                )
            else:
                question_a_correlations_query = question_a_correlations_query.filter(
                    models.QuestionCorrelation.scope_entity_id.is_(None)
                )

            question_a_correlations = question_a_correlations_query.all()

            print(f"DEBUG: Found {len(question_a_correlations)} existing correlations for question_a")
            logger.info(f"Found {len(question_a_correlations)} existing correlations for question_a")

            if question_a_correlations:
                for correlation in question_a_correlations:
                    print(f"DEBUG: Processing correlation ID: {correlation.id}")

                    # Determine the other question ID
                    if str(correlation.question_a_id) == str(request.question_a_id):
                        other_question_id = correlation.question_b_id
                    else:
                        other_question_id = correlation.question_a_id

                    print(f"DEBUG: Other question ID: {other_question_id}")

                    # Find the framework of the other question
                    other_framework = db.query(models.Framework).join(
                        models.FrameworkQuestion,
                        models.Framework.id == models.FrameworkQuestion.framework_id
                    ).filter(models.FrameworkQuestion.question_id == other_question_id).first()

                    print(f"DEBUG: Other framework: {other_framework.name if other_framework else 'None'} (ID: {other_framework.id if other_framework else 'None'})")
                    print(f"DEBUG: Target framework: {framework_b.name} (ID: {framework_b.id})")

                    # Check if this correlation is with a question from the same target framework
                    if other_framework and str(other_framework.id) == str(framework_b.id):
                        logger.error(f"BLOCKING: Question from {framework_a.name} already correlated with framework {framework_b.name}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Question from {framework_a.name} is already correlated with another question from {framework_b.name}. Each question can only correlate with one question per framework."
                        )

        except HTTPException:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in framework-specific validation: {str(e)}")
            print(f"DEBUG: Unexpected exception in framework validation: {str(e)}")
            # For unexpected exceptions, continue but log the error

        # Check if question_b already has a correlation with any question from framework_a
        # for the SAME scope (correlations should be per-scope)
        try:
            question_b_correlations_query = db.query(models.QuestionCorrelation).filter(
                and_(
                    or_(
                        models.QuestionCorrelation.question_a_id == request.question_b_id,
                        models.QuestionCorrelation.question_b_id == request.question_b_id
                    ),
                    models.QuestionCorrelation.scope_id == scope_id
                )
            )

            # Add scope_entity_id filter to make it scope-specific
            if scope_entity_id_uuid is not None:
                question_b_correlations_query = question_b_correlations_query.filter(
                    models.QuestionCorrelation.scope_entity_id == scope_entity_id_uuid
                )
            else:
                question_b_correlations_query = question_b_correlations_query.filter(
                    models.QuestionCorrelation.scope_entity_id.is_(None)
                )

            question_b_correlations = question_b_correlations_query.all()

            print(f"DEBUG: Found {len(question_b_correlations)} existing correlations for question_b")
            logger.info(f"Found {len(question_b_correlations)} existing correlations for question_b")

            if question_b_correlations:
                for correlation in question_b_correlations:
                    print(f"DEBUG: Processing question_b correlation ID: {correlation.id}")

                    # Determine the other question ID
                    if str(correlation.question_a_id) == str(request.question_b_id):
                        other_question_id = correlation.question_b_id
                    else:
                        other_question_id = correlation.question_a_id

                    print(f"DEBUG: Question_b other question ID: {other_question_id}")

                    # Find the framework of the other question
                    other_framework = db.query(models.Framework).join(
                        models.FrameworkQuestion,
                        models.Framework.id == models.FrameworkQuestion.framework_id
                    ).filter(models.FrameworkQuestion.question_id == other_question_id).first()

                    print(f"DEBUG: Question_b other framework: {other_framework.name if other_framework else 'None'} (ID: {other_framework.id if other_framework else 'None'})")
                    print(f"DEBUG: Question_b target framework: {framework_a.name} (ID: {framework_a.id})")

                    # Check if this correlation is with a question from the same target framework
                    if other_framework and str(other_framework.id) == str(framework_a.id):
                        logger.error(f"BLOCKING: Question from {framework_b.name} already correlated with framework {framework_a.name}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Question from {framework_b.name} is already correlated with another question from {framework_a.name}. Each question can only correlate with one question per framework."
                        )

        except HTTPException:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in question_b framework-specific validation: {str(e)}")
            print(f"DEBUG: Unexpected exception in question_b framework validation: {str(e)}")
            # For unexpected exceptions, continue but log the error

        # Before creating correlation, synchronize answers from Question A to Question B
        # This ensures that Question A's answer is used as the source of truth
        # Only sync answers from assessments with matching scope
        try:
            # Build query for answers from question_a
            answers_a_query = db.query(models.Answer).join(
                models.Assessment,
                models.Answer.assessment_id == models.Assessment.id
            ).filter(
                and_(
                    models.Answer.question_id == request.question_a_id,
                    models.Assessment.user_id == current_user.id,
                    models.Answer.value.isnot(None),
                    models.Answer.value != "",
                    models.Assessment.scope_id == scope_id
                )
            )

            # Add scope_entity_id filter
            if scope_entity_id_uuid is not None:
                answers_a_query = answers_a_query.filter(
                    models.Assessment.scope_entity_id == scope_entity_id_uuid
                )
            else:
                answers_a_query = answers_a_query.filter(
                    models.Assessment.scope_entity_id.is_(None)
                )

            answers_a = answers_a_query.order_by(models.Answer.id.desc()).first()

            # Build query for answers from question_b
            answers_b_query = db.query(models.Answer).join(
                models.Assessment,
                models.Answer.assessment_id == models.Assessment.id
            ).filter(
                and_(
                    models.Answer.question_id == request.question_b_id,
                    models.Assessment.user_id == current_user.id,
                    models.Assessment.scope_id == scope_id
                )
            )

            # Add scope_entity_id filter
            if scope_entity_id_uuid is not None:
                answers_b_query = answers_b_query.filter(
                    models.Assessment.scope_entity_id == scope_entity_id_uuid
                )
            else:
                answers_b_query = answers_b_query.filter(
                    models.Assessment.scope_entity_id.is_(None)
                )

            answers_b = answers_b_query.all()

            # If question_a has an answer, sync it to all question_b answers
            # ONLY sync the answer value - NOT policies or evidence descriptions (framework-specific)
            if answers_a and answers_b:
                logger.info(f"Syncing answer from Question A to {len(answers_b)} Question B answers")
                for answer_b in answers_b:
                    answer_b.value = answers_a.value
                    # Do NOT copy policy_id or evidence_description (framework-specific)
                    logger.info(f"Updated answer {answer_b.id} with value: {answer_b.value}")
                db.commit()
                logger.info("Answer synchronization completed successfully")
        except Exception as e:
            logger.warning(f"Failed to synchronize answers before correlation: {str(e)}")
            # Don't fail the correlation if sync fails

        # Create new correlation for the user's organization with scope
        correlation = models.QuestionCorrelation(
            question_a_id=request.question_a_id,
            question_b_id=request.question_b_id,
            organisation_id=current_user.organisation_id,
            scope_id=scope_id,
            scope_entity_id=scope_entity_id_uuid,
            created_by=current_user.id
        )

        db.add(correlation)
        db.commit()
        db.refresh(correlation)

        # Create transitive correlations to ensure all questions in the group are interconnected
        try:
            logger.info(f"Creating transitive correlations for new correlation between {framework_a.name} and {framework_b.name}")
            create_transitive_correlations(db, correlation, current_user.id)
            logger.info("Transitive correlations created successfully")
        except Exception as e:
            logger.error(f"Error creating transitive correlations: {str(e)}")
            # Don't fail the main operation if transitive correlation creation fails
            print(f"WARNING: Failed to create transitive correlations: {str(e)}")

        return {
            "message": f"Questions successfully correlated between {framework_a.name} and {framework_b.name}",
            "correlation_id": str(correlation.id),
            "question_a": question_a.text[:100] + "..." if len(question_a.text) > 100 else question_a.text,
            "question_b": question_b.text[:100] + "..." if len(question_b.text) > 100 else question_b.text
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error correlating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to correlate questions: {str(e)}")

@router.get("/frameworks/common-scopes")
async def get_common_scope_types(
    framework_a_id: str,
    framework_b_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get common allowed scope types between two frameworks."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can access framework configurations")

    try:
        # Get framework scope configurations
        framework_a_config = scope_validation_service.get_framework_scope_config(
            db=db,
            framework_id=uuid.UUID(framework_a_id)
        )
        framework_b_config = scope_validation_service.get_framework_scope_config(
            db=db,
            framework_id=uuid.UUID(framework_b_id)
        )

        # Get framework names
        framework_a = db.query(models.Framework).filter(
            models.Framework.id == framework_a_id
        ).first()
        framework_b = db.query(models.Framework).filter(
            models.Framework.id == framework_b_id
        ).first()

        if not framework_a or not framework_b:
            raise HTTPException(status_code=404, detail="One or both frameworks not found")

        # Find common allowed scope types
        allowed_a = set(framework_a_config['allowed_scope_types']) if framework_a_config['allowed_scope_types'] else set()
        allowed_b = set(framework_b_config['allowed_scope_types']) if framework_b_config['allowed_scope_types'] else set()

        # If either framework has no restrictions, treat as allowing all scopes
        if not allowed_a and not allowed_b:
            common_scopes = scope_validation_service.get_supported_scope_types()
        elif not allowed_a:
            common_scopes = list(allowed_b)
        elif not allowed_b:
            common_scopes = list(allowed_a)
        else:
            common_scopes = list(allowed_a & allowed_b)

        return {
            "framework_a": {
                "id": str(framework_a.id),
                "name": framework_a.name,
                "allowed_scope_types": list(allowed_a) if allowed_a else "Any"
            },
            "framework_b": {
                "id": str(framework_b.id),
                "name": framework_b.name,
                "allowed_scope_types": list(allowed_b) if allowed_b else "Any"
            },
            "common_scope_types": common_scopes,
            "has_common_scopes": len(common_scopes) > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting common scope types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get common scope types: {str(e)}")

@router.get("/correlations/validate")
async def validate_existing_correlations(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Audit existing correlations to find ones that are now invalid due to framework scope incompatibility.
    Returns a list of invalid correlations with details about why they're invalid.
    """
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can validate correlations")

    try:
        # Get all correlations (filtered by organization for org_admin)
        if current_user.role_name == 'super_admin':
            correlations = db.query(models.QuestionCorrelation).all()
        else:
            correlations = db.query(models.QuestionCorrelation).filter(
                models.QuestionCorrelation.organisation_id == current_user.organisation_id
            ).all()

        invalid_correlations = []
        valid_correlations = []

        for correlation in correlations:
            # Get questions
            question_a = db.query(models.Question).filter(
                models.Question.id == correlation.question_a_id
            ).first()
            question_b = db.query(models.Question).filter(
                models.Question.id == correlation.question_b_id
            ).first()

            if not question_a or not question_b:
                continue

            # Get frameworks for these questions
            framework_a = db.query(models.Framework).join(
                models.FrameworkQuestion,
                models.Framework.id == models.FrameworkQuestion.framework_id
            ).filter(models.FrameworkQuestion.question_id == correlation.question_a_id).first()

            framework_b = db.query(models.Framework).join(
                models.FrameworkQuestion,
                models.Framework.id == models.FrameworkQuestion.framework_id
            ).filter(models.FrameworkQuestion.question_id == correlation.question_b_id).first()

            if not framework_a or not framework_b:
                continue

            # Get scope configurations
            framework_a_config = scope_validation_service.get_framework_scope_config(
                db=db,
                framework_id=framework_a.id
            )
            framework_b_config = scope_validation_service.get_framework_scope_config(
                db=db,
                framework_id=framework_b.id
            )

            # Get scope name for this correlation
            correlation_scope = db.query(models.Scopes).filter(
                models.Scopes.id == correlation.scope_id
            ).first()
            correlation_scope_name = correlation_scope.scope_name if correlation_scope else "Unknown"

            # Check if correlation scope is valid for both frameworks
            allowed_a = set(framework_a_config['allowed_scope_types']) if framework_a_config['allowed_scope_types'] else set()
            allowed_b = set(framework_b_config['allowed_scope_types']) if framework_b_config['allowed_scope_types'] else set()

            # Empty means "allow all"
            if not allowed_a and not allowed_b:
                # Both allow all - correlation is valid
                valid_correlations.append(str(correlation.id))
                continue

            # Determine valid scopes
            if not allowed_a:
                valid_scopes = allowed_b
            elif not allowed_b:
                valid_scopes = allowed_a
            else:
                valid_scopes = allowed_a & allowed_b

            # Check if correlation scope is in valid scopes
            is_valid = correlation_scope_name in valid_scopes if valid_scopes else False

            if not is_valid:
                invalid_correlations.append({
                    "correlation_id": str(correlation.id),
                    "question_a": {
                        "id": str(question_a.id),
                        "text": question_a.question_text[:100] + "..." if len(question_a.question_text) > 100 else question_a.question_text,
                        "framework_id": str(framework_a.id),
                        "framework_name": framework_a.name
                    },
                    "question_b": {
                        "id": str(question_b.id),
                        "text": question_b.question_text[:100] + "..." if len(question_b.question_text) > 100 else question_b.question_text,
                        "framework_id": str(framework_b.id),
                        "framework_name": framework_b.name
                    },
                    "current_scope": correlation_scope_name,
                    "framework_a_allowed_scopes": list(allowed_a) if allowed_a else "Any",
                    "framework_b_allowed_scopes": list(allowed_b) if allowed_b else "Any",
                    "valid_common_scopes": list(valid_scopes) if valid_scopes else [],
                    "issue": "Correlation scope '{}' is not allowed by both frameworks".format(correlation_scope_name),
                    "recommendation": "Delete this correlation or migrate to a valid common scope: {}".format(
                        ", ".join(valid_scopes) if valid_scopes else "No common scopes available - correlation should be deleted"
                    )
                })
            else:
                valid_correlations.append(str(correlation.id))

        return {
            "total_correlations": len(correlations),
            "valid_correlations_count": len(valid_correlations),
            "invalid_correlations_count": len(invalid_correlations),
            "invalid_correlations": invalid_correlations,
            "summary": {
                "has_invalid_correlations": len(invalid_correlations) > 0,
                "action_required": len(invalid_correlations) > 0,
                "message": "Found {} invalid correlation(s) that need attention".format(len(invalid_correlations)) if invalid_correlations else "All correlations are valid"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating existing correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate correlations: {str(e)}")

@router.post("/correlations/fix-invalid")
async def fix_invalid_correlations(
    action: str,  # "delete" or "migrate"
    target_scope: str = None,  # Required if action is "migrate"
    correlation_ids: List[str] = None,  # Optional: specific correlation IDs to fix, if None fixes all invalid
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Fix invalid correlations by either deleting them or migrating to a valid common scope.

    Args:
        action: Either "delete" to remove invalid correlations, or "migrate" to update scope
        target_scope: Required if action is "migrate" - the new scope to migrate to
        correlation_ids: Optional list of specific correlation IDs to fix. If None, processes all invalid correlations.
    """
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can fix correlations")

    if action not in ["delete", "migrate"]:
        raise HTTPException(status_code=400, detail="Action must be either 'delete' or 'migrate'")

    if action == "migrate" and not target_scope:
        raise HTTPException(status_code=400, detail="target_scope is required when action is 'migrate'")

    try:
        # First, validate to get list of invalid correlations
        validation_result = await validate_existing_correlations(db=db, current_user=current_user)

        if not validation_result["has_invalid_correlations"]:
            return {
                "message": "No invalid correlations found",
                "processed_count": 0,
                "action": action
            }

        # Determine which correlations to process
        if correlation_ids:
            # Filter to only process specified correlation IDs that are also invalid
            invalid_ids = {c["correlation_id"] for c in validation_result["invalid_correlations"]}
            target_ids = [cid for cid in correlation_ids if cid in invalid_ids]
        else:
            # Process all invalid correlations
            target_ids = [c["correlation_id"] for c in validation_result["invalid_correlations"]]

        if not target_ids:
            return {
                "message": "No matching invalid correlations found to process",
                "processed_count": 0,
                "action": action
            }

        processed_count = 0
        errors = []

        if action == "delete":
            # Delete invalid correlations
            for correlation_id in target_ids:
                try:
                    correlation = db.query(models.QuestionCorrelation).filter(
                        models.QuestionCorrelation.id == uuid.UUID(correlation_id)
                    ).first()

                    if correlation:
                        db.delete(correlation)
                        processed_count += 1
                except Exception as e:
                    errors.append({
                        "correlation_id": correlation_id,
                        "error": str(e)
                    })

            db.commit()

            return {
                "message": f"Successfully deleted {processed_count} invalid correlation(s)",
                "processed_count": processed_count,
                "action": action,
                "errors": errors if errors else None
            }

        elif action == "migrate":
            # Get target scope ID
            target_scope_obj = db.query(models.Scopes).filter(
                models.Scopes.scope_name == target_scope
            ).first()

            if not target_scope_obj:
                raise HTTPException(status_code=404, detail=f"Scope '{target_scope}' not found")

            # Migrate correlations to new scope
            for correlation_id in target_ids:
                try:
                    correlation = db.query(models.QuestionCorrelation).filter(
                        models.QuestionCorrelation.id == uuid.UUID(correlation_id)
                    ).first()

                    if correlation:
                        # Verify the target scope is valid for both frameworks
                        question_a = db.query(models.Question).filter(
                            models.Question.id == correlation.question_a_id
                        ).first()
                        question_b = db.query(models.Question).filter(
                            models.Question.id == correlation.question_b_id
                        ).first()

                        framework_a = db.query(models.Framework).join(
                            models.FrameworkQuestion,
                            models.Framework.id == models.FrameworkQuestion.framework_id
                        ).filter(models.FrameworkQuestion.question_id == correlation.question_a_id).first()

                        framework_b = db.query(models.Framework).join(
                            models.FrameworkQuestion,
                            models.Framework.id == models.FrameworkQuestion.framework_id
                        ).filter(models.FrameworkQuestion.question_id == correlation.question_b_id).first()

                        if framework_a and framework_b:
                            framework_a_config = scope_validation_service.get_framework_scope_config(
                                db=db, framework_id=framework_a.id
                            )
                            framework_b_config = scope_validation_service.get_framework_scope_config(
                                db=db, framework_id=framework_b.id
                            )

                            allowed_a = set(framework_a_config['allowed_scope_types']) if framework_a_config['allowed_scope_types'] else set()
                            allowed_b = set(framework_b_config['allowed_scope_types']) if framework_b_config['allowed_scope_types'] else set()

                            # Check if target scope is valid
                            if (not allowed_a or target_scope in allowed_a) and (not allowed_b or target_scope in allowed_b):
                                correlation.scope_id = target_scope_obj.id
                                # For "Other" scope, set scope_entity_id to None
                                if target_scope == "Other":
                                    correlation.scope_entity_id = None
                                processed_count += 1
                            else:
                                errors.append({
                                    "correlation_id": correlation_id,
                                    "error": f"Target scope '{target_scope}' is not valid for both frameworks"
                                })
                except Exception as e:
                    errors.append({
                        "correlation_id": correlation_id,
                        "error": str(e)
                    })

            db.commit()

            return {
                "message": f"Successfully migrated {processed_count} correlation(s) to scope '{target_scope}'",
                "processed_count": processed_count,
                "action": action,
                "target_scope": target_scope,
                "errors": errors if errors else None
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing invalid correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fix correlations: {str(e)}")

@router.get("/correlations")
async def get_question_correlations(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get question correlations (super admin sees all orgs, org admin sees only their org)."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can view question correlations")

    try:
        # Super admin sees all organizations' correlations
        if current_user.role_name == 'super_admin':
            correlations = db.query(models.QuestionCorrelation).all()
        else:
            # Org admin sees only their organization's correlations
            correlations = db.query(models.QuestionCorrelation).filter(
                models.QuestionCorrelation.organisation_id == current_user.organisation_id
            ).all()

        result = []
        for correlation in correlations:
            # Get question details
            question_a = db.query(models.Question).filter(models.Question.id == correlation.question_a_id).first()
            question_b = db.query(models.Question).filter(models.Question.id == correlation.question_b_id).first()

            # Get framework names
            framework_a = db.query(models.Framework).join(
                models.FrameworkQuestion,
                models.Framework.id == models.FrameworkQuestion.framework_id
            ).filter(models.FrameworkQuestion.question_id == correlation.question_a_id).first()

            framework_b = db.query(models.Framework).join(
                models.FrameworkQuestion,
                models.Framework.id == models.FrameworkQuestion.framework_id
            ).filter(models.FrameworkQuestion.question_id == correlation.question_b_id).first()

            # Get assessment types
            assessment_type_a = db.query(models.AssessmentType).filter(
                models.AssessmentType.id == question_a.assessment_type_id
            ).first()

            assessment_type_b = db.query(models.AssessmentType).filter(
                models.AssessmentType.id == question_b.assessment_type_id
            ).first()

            created_by_user = db.query(models.User).filter(models.User.id == correlation.created_by).first()

            # Get organisation info (all correlations are org-specific now)
            org = db.query(models.Organisations).filter(models.Organisations.id == correlation.organisation_id).first()
            organisation = org.name if org else "Unknown"

            # Get scope info
            scope_info = scope_validation_service.get_scope_info(
                db,
                correlation.scope_id,
                correlation.scope_entity_id
            )

            result.append({
                "id": str(correlation.id),
                "question_a": {
                    "id": str(question_a.id),
                    "text": question_a.text,
                    "framework": framework_a.name if framework_a else "Unknown",
                    "assessment_type": assessment_type_a.type_name.capitalize() if assessment_type_a else "Unknown"
                },
                "question_b": {
                    "id": str(question_b.id),
                    "text": question_b.text,
                    "framework": framework_b.name if framework_b else "Unknown",
                    "assessment_type": assessment_type_b.type_name.capitalize() if assessment_type_b else "Unknown"
                },
                "organisation": organisation,
                "organisation_id": str(correlation.organisation_id),
                "scope": {
                    "scope_name": scope_info['scope_name'] if scope_info else "Unknown",
                    "scope_id": str(scope_info['scope_id']) if scope_info else None,
                    "scope_entity_id": str(scope_info['scope_entity_id']) if scope_info and scope_info.get('scope_entity_id') else None,
                    "entity_name": scope_info['entity_name'] if scope_info else None
                },
                "created_by": created_by_user.email if created_by_user else "Unknown",
                "created_at": correlation.created_at.isoformat() if correlation.created_at else None
            })

        return result

    except Exception as e:
        logger.error(f"Error getting question correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get question correlations: {str(e)}")

@router.delete("/correlations/{correlation_id}")
async def delete_question_correlation(
    correlation_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete a question correlation (super admin can delete any org's, org admin can delete only their org's)."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can delete question correlations")

    try:
        correlation = db.query(models.QuestionCorrelation).filter(
            models.QuestionCorrelation.id == correlation_id
        ).first()

        if not correlation:
            raise HTTPException(status_code=404, detail="Question correlation not found")

        # Org admin can only delete their own org's correlations
        if current_user.role_name == 'org_admin':
            if correlation.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=403, detail="Cannot delete correlations from other organizations")

        db.delete(correlation)
        db.commit()

        return {"message": "Question correlation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting question correlation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete question correlation: {str(e)}")

@router.delete("/correlations")
async def delete_all_question_correlations(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete all question correlations (super admin deletes all, org admin deletes only their org's)."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can delete question correlations")

    try:
        # Build query based on role
        if current_user.role_name == 'super_admin':
            # Super admin can delete all correlations
            query = db.query(models.QuestionCorrelation)
        else:
            # Org admin can only delete their org's correlations (not global ones)
            query = db.query(models.QuestionCorrelation).filter(
                models.QuestionCorrelation.organisation_id == current_user.organisation_id
            )

        # Get count before deletion
        count = query.count()

        if count == 0:
            return {"message": "No correlations to delete", "deleted_count": 0}

        # Delete correlations
        query.delete()
        db.commit()

        logger.info(f"Deleted {count} question correlations by user {current_user.email}")
        return {"message": f"Successfully deleted {count} question correlations", "deleted_count": count}

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting all question correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete all question correlations: {str(e)}")

@router.get("/frameworks/{framework_id}/questions")
async def get_framework_questions(
    framework_id: str,
    assessment_type_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get questions for a specific framework and assessment type."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only super administrators and organization administrators can access this endpoint")

    try:
        # Validate framework exists
        framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Get questions for this framework and assessment type
        questions = db.query(models.Question).join(
            models.FrameworkQuestion,
            models.Question.id == models.FrameworkQuestion.question_id
        ).filter(
            and_(
                models.FrameworkQuestion.framework_id == framework_id,
                models.Question.assessment_type_id == assessment_type_id
            )
        ).order_by(models.FrameworkQuestion.order, models.Question.id).all()

        return [
            {
                "id": str(question.id),
                "text": question.text,
                "description": question.description,
                "mandatory": question.mandatory
            }
            for question in questions
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting framework questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get framework questions: {str(e)}")

@router.post("/check-answer-conflicts")
async def check_answer_conflicts(
    request: QuestionCorrelationRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Check if two questions have conflicting answers in the current user's assessments."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only super administrators and organization administrators can access this endpoint")

    try:
        # Get all answers for both questions from the current user's assessments
        answers_a = db.query(models.Answer).join(
            models.Assessment,
            models.Answer.assessment_id == models.Assessment.id
        ).filter(
            and_(
                models.Answer.question_id == request.question_a_id,
                models.Assessment.user_id == current_user.id,
                models.Answer.value.isnot(None),
                models.Answer.value != ""
            )
        ).all()

        answers_b = db.query(models.Answer).join(
            models.Assessment,
            models.Answer.assessment_id == models.Assessment.id
        ).filter(
            and_(
                models.Answer.question_id == request.question_b_id,
                models.Assessment.user_id == current_user.id,
                models.Answer.value.isnot(None),
                models.Answer.value != ""
            )
        ).all()

        # Check if both questions have answers
        if not answers_a or not answers_b:
            return {
                "has_conflict": False,
                "message": "No conflict - one or both questions don't have answers yet"
            }

        # Check if the answers are different
        # Get unique answer values for each question
        values_a = set(answer.value for answer in answers_a if answer.value)
        values_b = set(answer.value for answer in answers_b if answer.value)

        # If there are multiple different values within the same question or between questions
        has_conflict = len(values_a) > 1 or len(values_b) > 1 or (values_a and values_b and values_a != values_b)

        return {
            "has_conflict": has_conflict,
            "message": "Conflicting answers detected" if has_conflict else "No conflicts found",
            "question_a_answers": len(answers_a),
            "question_b_answers": len(answers_b),
            "unique_values_a": len(values_a),
            "unique_values_b": len(values_b)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking answer conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check answer conflicts: {str(e)}")

@router.get("/questions/{question_id}/correlations")
async def get_question_correlations_for_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all correlations for a specific question."""
    try:
        logger.info(f"Getting correlations for question {question_id}")

        # Validate question exists
        question = db.query(models.Question).filter(models.Question.id == question_id).first()
        if not question:
            logger.error(f"Question {question_id} not found")
            raise HTTPException(status_code=404, detail="Question not found")

        # Get all correlations where this question is either question_a or question_b
        # Filter by organization for org users
        correlation_filter = or_(
            models.QuestionCorrelation.question_a_id == question_id,
            models.QuestionCorrelation.question_b_id == question_id
        )

        if current_user.organisation_id:
            # Filter by organization for org users
            correlations = db.query(models.QuestionCorrelation).filter(
                and_(
                    correlation_filter,
                    models.QuestionCorrelation.organisation_id == current_user.organisation_id
                )
            ).all()
        else:
            # For super_admin without organization, show all correlations
            correlations = db.query(models.QuestionCorrelation).filter(correlation_filter).all()

        logger.info(f"Found {len(correlations)} correlations for question {question_id}")

        result = []
        for correlation in correlations:
            try:
                # Get question details
                question_a = db.query(models.Question).filter(models.Question.id == correlation.question_a_id).first()
                question_b = db.query(models.Question).filter(models.Question.id == correlation.question_b_id).first()

                if not question_a or not question_b:
                    logger.warning(f"Missing question data for correlation {correlation.id}")
                    continue

                # Get framework names
                framework_a = db.query(models.Framework).join(
                    models.FrameworkQuestion,
                    models.Framework.id == models.FrameworkQuestion.framework_id
                ).filter(models.FrameworkQuestion.question_id == correlation.question_a_id).first()

                framework_b = db.query(models.Framework).join(
                    models.FrameworkQuestion,
                    models.Framework.id == models.FrameworkQuestion.framework_id
                ).filter(models.FrameworkQuestion.question_id == correlation.question_b_id).first()

                # Get assessment types
                assessment_type_a = db.query(models.AssessmentType).filter(
                    models.AssessmentType.id == question_a.assessment_type_id
                ).first() if question_a.assessment_type_id else None

                assessment_type_b = db.query(models.AssessmentType).filter(
                    models.AssessmentType.id == question_b.assessment_type_id
                ).first() if question_b.assessment_type_id else None

                # Get creator details
                creator = db.query(models.User).filter(models.User.id == correlation.created_by).first() if correlation.created_by else None

                # Get scope information
                scope_info = scope_validation_service.get_scope_info(
                    db,
                    correlation.scope_id,
                    correlation.scope_entity_id
                )

                result.append({
                    "id": str(correlation.id),
                    "question_a": {
                        "id": str(question_a.id),
                        "text": question_a.text,
                        "framework": framework_a.name if framework_a else "Unknown",
                        "assessment_type": assessment_type_a.type_name if assessment_type_a else "Unknown"
                    },
                    "question_b": {
                        "id": str(question_b.id),
                        "text": question_b.text,
                        "framework": framework_b.name if framework_b else "Unknown",
                        "assessment_type": assessment_type_b.type_name if assessment_type_b else "Unknown"
                    },
                    "scope": {
                        "scope_name": scope_info['scope_name'] if scope_info else "Unknown",
                        "scope_id": str(scope_info['scope_id']) if scope_info else None,
                        "scope_entity_id": str(scope_info['scope_entity_id']) if scope_info and scope_info.get('scope_entity_id') else None,
                        "entity_name": scope_info['entity_name'] if scope_info else None
                    },
                    "created_by": creator.email if creator else "Unknown",
                    "created_at": correlation.created_at.isoformat() if correlation.created_at else ""
                })
            except Exception as correlation_error:
                logger.error(f"Error processing correlation {correlation.id}: {str(correlation_error)}")
                continue

        logger.info(f"Successfully processed {len(result)} correlations for question {question_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting correlations for question {question_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get correlations: {str(e)}")

@router.post("/backfill-transitive-correlations")
async def backfill_transitive_correlations_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Backfill transitive correlations for existing correlations (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can backfill transitive correlations")

    try:
        result = backfill_transitive_correlations(db)
        return result

    except Exception as e:
        logger.error(f"Error backfilling transitive correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to backfill transitive correlations: {str(e)}")

@router.post("/suggest-correlations")
async def suggest_correlations_with_ai(
    request: AICorrelationRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Use AI to suggest question correlations between two frameworks.

    This endpoint analyzes all questions from both frameworks and uses an LLM to identify
    semantically similar questions that should be correlated.
    """
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can use AI correlation suggestions")

    try:
        # Validate frameworks exist
        framework_a = db.query(models.Framework).filter(
            models.Framework.id == request.framework_a_id
        ).first()

        framework_b = db.query(models.Framework).filter(
            models.Framework.id == request.framework_b_id
        ).first()

        if not framework_a or not framework_b:
            raise HTTPException(status_code=404, detail="One or both frameworks not found")

        if framework_a.id == framework_b.id:
            raise HTTPException(status_code=400, detail="Cannot correlate questions from the same framework")

        # Validate assessment type exists
        assessment_type = db.query(models.AssessmentType).filter(
            models.AssessmentType.id == request.assessment_type_id
        ).first()

        if not assessment_type:
            raise HTTPException(status_code=404, detail="Assessment type not found")

        logger.info(f"Fetching questions for AI correlation analysis: {framework_a.name} <-> {framework_b.name}")

        # Get questions for framework A
        questions_a = db.query(models.Question).join(
            models.FrameworkQuestion,
            models.Question.id == models.FrameworkQuestion.question_id
        ).filter(
            and_(
                models.FrameworkQuestion.framework_id == request.framework_a_id,
                models.Question.assessment_type_id == request.assessment_type_id
            )
        ).all()

        # Get questions for framework B
        questions_b = db.query(models.Question).join(
            models.FrameworkQuestion,
            models.Question.id == models.FrameworkQuestion.question_id
        ).filter(
            and_(
                models.FrameworkQuestion.framework_id == request.framework_b_id,
                models.Question.assessment_type_id == request.assessment_type_id
            )
        ).all()

        if not questions_a or not questions_b:
            return AICorrelationResponse(
                suggestions=[],
                framework_a_name=framework_a.name,
                framework_b_name=framework_b.name,
                total_suggestions=0
            )

        logger.info(f"Found {len(questions_a)} questions in {framework_a.name} and {len(questions_b)} in {framework_b.name}")

        # Prepare question data for LLM
        questions_a_data = [
            {"id": str(q.id), "text": q.text}
            for q in questions_a
        ]

        questions_b_data = [
            {"id": str(q.id), "text": q.text}
            for q in questions_b
        ]

        # Get existing correlations to filter them out
        existing_correlations = db.query(models.QuestionCorrelation).filter(
            or_(
                and_(
                    models.QuestionCorrelation.question_a_id.in_([q.id for q in questions_a]),
                    models.QuestionCorrelation.question_b_id.in_([q.id for q in questions_b])
                ),
                and_(
                    models.QuestionCorrelation.question_a_id.in_([q.id for q in questions_b]),
                    models.QuestionCorrelation.question_b_id.in_([q.id for q in questions_a])
                )
            )
        ).all()

        existing_pairs = set()
        # Track which questions from framework A are already correlated with any question from framework B
        questions_a_ids_set = set([q.id for q in questions_a])
        questions_b_ids_set = set([q.id for q in questions_b])
        correlated_questions_from_a = set()

        for corr in existing_correlations:
            pair = tuple(sorted([str(corr.question_a_id), str(corr.question_b_id)]))
            existing_pairs.add(pair)

            # Check if question_a is from framework A and question_b is from framework B
            if corr.question_a_id in questions_a_ids_set and corr.question_b_id in questions_b_ids_set:
                correlated_questions_from_a.add(str(corr.question_a_id))
            # Check if question_a is from framework B and question_b is from framework A (reverse)
            elif corr.question_a_id in questions_b_ids_set and corr.question_b_id in questions_a_ids_set:
                correlated_questions_from_a.add(str(corr.question_b_id))

        logger.info(f"Found {len(existing_pairs)} existing correlations to filter out")
        logger.info(f"Found {len(correlated_questions_from_a)} questions from Framework A already correlated with Framework B")

        # Call LLM service
        llm_service = LLMService(db)
        suggestions = await llm_service.analyze_question_correlations(
            questions_a_data,
            questions_b_data,
            framework_a.name,
            framework_b.name
        )

        # Filter out existing correlations and questions already correlated
        filtered_suggestions = []
        for suggestion in suggestions:
            pair = tuple(sorted([suggestion['question_a_id'], suggestion['question_b_id']]))
            question_a_id = suggestion['question_a_id']

            # Skip if this exact pair already exists OR if question_a is already correlated with any question from framework B
            if pair not in existing_pairs and question_a_id not in correlated_questions_from_a:
                filtered_suggestions.append(AICorrelationSuggestion(
                    question_a_id=suggestion['question_a_id'],
                    question_b_id=suggestion['question_b_id'],
                    question_a_text=suggestion['question_a_text'],
                    question_b_text=suggestion['question_b_text'],
                    confidence=suggestion['confidence'],
                    reasoning=suggestion['reasoning']
                ))

        logger.info(f"Returning {len(filtered_suggestions)} correlation suggestions after filtering")

        return AICorrelationResponse(
            suggestions=filtered_suggestions,
            framework_a_name=framework_a.name,
            framework_b_name=framework_b.name,
            total_suggestions=len(filtered_suggestions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting correlations with AI: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI correlation suggestions: {str(e)}"
        )