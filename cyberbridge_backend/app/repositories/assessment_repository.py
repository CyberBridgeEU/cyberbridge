# crud.py
from sqlalchemy.orm import Session
import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from app.services.security_service import get_password_hash
from app.services import scope_validation_service
from app.models import models
from app.dtos import schemas

# Assessment CRUD operations
def get_assessment(db: Session, assessment_id: uuid.UUID):
    return db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()

#used
def get_assessments(db: Session, skip: int = 0, limit: int = 100):
    assessments = db.query(models.Assessment).offset(skip).limit(limit).all()

    # Enrich with scope display names
    for assessment in assessments:
        _enrich_assessment_with_scope(db, assessment)

    return assessments


def _enrich_assessment_with_scope(db: Session, assessment):
    """Helper function to add scope information to assessment object"""
    if assessment.scope_id and hasattr(assessment, 'scope_id'):
        scope_info = scope_validation_service.get_scope_info(
            db,
            assessment.scope_id,
            assessment.scope_entity_id
        )
        if scope_info:
            assessment.scope_name = scope_info['scope_name']
            assessment.scope_display_name = scope_info['entity_name']


def get_assessments_by_scope(
    db: Session,
    scope_name: str,
    scope_entity_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
):
    """Get all assessments for a specific scoped entity"""

    # Get scope_id from scope name
    scope = db.query(models.Scopes).filter(
        models.Scopes.scope_name == scope_name
    ).first()

    if not scope:
        return []

    assessments = db.query(models.Assessment).filter(
        models.Assessment.scope_id == scope.id,
        models.Assessment.scope_entity_id == scope_entity_id
    ).offset(skip).limit(limit).all()

    # Enrich with scope display names
    for assessment in assessments:
        _enrich_assessment_with_scope(db, assessment)

    return assessments


def get_assessments_for_framework_and_user(db: Session, request: schemas.FrameworkAndUser, current_user: schemas.UserBase, skip: int = 0, limit: int = 100):
    # If user is org_user, only return assessments for the specific user
    if current_user.role_name == "org_user":
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id),
                        models.Assessment.user_id == uuid.UUID(request.user_id))
                .offset(skip).limit(limit).all())

    # If user is org_admin, return all assessments from their organization
    elif current_user.role_name == "org_admin":
        assessments = (db.query(models.Assessment)
                .join(models.User, models.Assessment.user_id == models.User.id)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id),
                        models.User.organisation_id == current_user.organisation_id)
                .offset(skip).limit(limit).all())

    # If user is super_admin, return all assessments
    elif current_user.role_name == "super_admin":
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id))
                .offset(skip).limit(limit).all())

    # Default case - return only user's assessments
    else:
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id),
                        models.Assessment.user_id == uuid.UUID(request.user_id))
                .offset(skip).limit(limit).all())

    # Enrich with scope display names
    for assessment in assessments:
        _enrich_assessment_with_scope(db, assessment)

    return assessments

def get_user_assessments(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Assessment).filter(models.Assessment.user_id == user_id).offset(skip).limit(limit).all()


def get_assessments_for_user(db: Session, user_id: uuid.UUID, current_user: schemas.UserBase, skip: int = 0, limit: int = 100):
    """Get all assessments for a user with framework and assessment type information"""

    # Query based on role
    if current_user.role_name == "org_user":
        # Regular users can only see their own assessments
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.user_id == user_id)
                .order_by(models.Assessment.updated_at.desc())
                .offset(skip).limit(limit).all())

    elif current_user.role_name == "org_admin":
        # Org admins can see all assessments in their organization for the requested user
        assessments = (db.query(models.Assessment)
                .join(models.User, models.Assessment.user_id == models.User.id)
                .filter(models.Assessment.user_id == user_id,
                        models.User.organisation_id == current_user.organisation_id)
                .order_by(models.Assessment.updated_at.desc())
                .offset(skip).limit(limit).all())

    elif current_user.role_name == "super_admin":
        # Super admins can see all assessments for any user
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.user_id == user_id)
                .order_by(models.Assessment.updated_at.desc())
                .offset(skip).limit(limit).all())

    else:
        # Default - only own assessments
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.user_id == user_id)
                .order_by(models.Assessment.updated_at.desc())
                .offset(skip).limit(limit).all())

    # Enrich with framework name, assessment type name, scope info, and progress
    enriched_assessments = []
    for assessment in assessments:
        # Get framework name
        framework = db.query(models.Framework).filter(models.Framework.id == assessment.framework_id).first()
        assessment.framework_name = framework.name if framework else None

        # Get assessment type name
        if assessment.assessment_type_id:
            assessment_type = db.query(models.AssessmentType).filter(models.AssessmentType.id == assessment.assessment_type_id).first()
            assessment.assessment_type_name = assessment_type.type_name if assessment_type else None
        else:
            assessment.assessment_type_name = None

        # Calculate progress - count answered questions vs total questions
        total_answers = db.query(models.Answer).filter(models.Answer.assessment_id == assessment.id).count()
        answered_count = db.query(models.Answer).filter(
            models.Answer.assessment_id == assessment.id,
            models.Answer.value.isnot(None),
            models.Answer.value != ''
        ).count()

        if total_answers > 0:
            assessment.progress = int((answered_count / total_answers) * 100)
        else:
            assessment.progress = 0

        # Enrich with scope info
        _enrich_assessment_with_scope(db, assessment)

        enriched_assessments.append(assessment)

    return enriched_assessments

def get_assessments_for_framework_user_and_assessment_type(db: Session, request: schemas.FrameworkUserAndAssessmentType, current_user: schemas.UserBase, skip: int = 0, limit: int = 100):
    # If user is org_user, only return assessments for the specific user
    if current_user.role_name == "org_user":
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id),
                        models.Assessment.user_id == uuid.UUID(request.user_id),
                        models.Assessment.assessment_type_id == uuid.UUID(request.assessment_type_id))
                .offset(skip).limit(limit).all())

    # If user is org_admin, return all assessments from their organization
    elif current_user.role_name == "org_admin":
        assessments = (db.query(models.Assessment)
                .join(models.User, models.Assessment.user_id == models.User.id)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id),
                        models.Assessment.assessment_type_id == uuid.UUID(request.assessment_type_id),
                        models.User.organisation_id == current_user.organisation_id)
                .offset(skip).limit(limit).all())

    # If user is super_admin, return all assessments
    elif current_user.role_name == "super_admin":
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id),
                        models.Assessment.assessment_type_id == uuid.UUID(request.assessment_type_id))
                .offset(skip).limit(limit).all())

    # Default case - return only user's assessments
    else:
        assessments = (db.query(models.Assessment)
                .filter(models.Assessment.framework_id == uuid.UUID(request.framework_id),
                        models.Assessment.user_id == uuid.UUID(request.user_id),
                        models.Assessment.assessment_type_id == uuid.UUID(request.assessment_type_id))
                .offset(skip).limit(limit).all())

    # Enrich with scope display names
    for assessment in assessments:
        _enrich_assessment_with_scope(db, assessment)

    return assessments

#used
def create_assessment(
    db: Session,
    assessment: schemas.AssessmentCreate,
    scope_name: Optional[str] = None,
    scope_entity_id: Optional[uuid.UUID] = None
):
    """Create assessment with optional scope"""

    assessment_data = assessment.model_dump()

    # Validate and add scope if provided
    if scope_name:
        # Validate framework scope requirements
        scope_validation_service.validate_framework_scope(
            db,
            assessment.framework_id,
            scope_name,
            scope_entity_id
        )

        # Validate scope entity exists
        scope_result = scope_validation_service.validate_scope(
            db,
            scope_name,
            scope_entity_id
        )

        assessment_data['scope_id'] = scope_result['scope_id']
        assessment_data['scope_entity_id'] = scope_entity_id

    # Create assessment
    db_assessment = models.Assessment(**assessment_data)
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)

    return db_assessment


def get_incomplete_assessments_for_reminders(
    db: Session,
    days_threshold: int = 7,
    organisation_id: Optional[uuid.UUID] = None
) -> List[dict]:
    """
    Get assessments that are incomplete and haven't been updated for X days.
    Returns list of dicts with assessment details for notification purposes.
    """
    threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

    # Build query for incomplete assessments
    query = db.query(
        models.Assessment,
        models.User,
        models.Framework
    ).join(
        models.User, models.Assessment.user_id == models.User.id
    ).join(
        models.Framework, models.Assessment.framework_id == models.Framework.id
    ).filter(
        models.Assessment.completed_at.is_(None),  # Not completed
        models.Assessment.updated_at < threshold_date,  # Not updated recently
        models.User.status == 'active'  # Only active users
    )

    # Filter by organisation if specified
    if organisation_id:
        query = query.filter(models.User.organisation_id == organisation_id)

    results = query.all()

    # Enrich with progress information
    incomplete_assessments = []
    for assessment, user, framework in results:
        # Calculate progress
        total_answers = db.query(models.Answer).filter(
            models.Answer.assessment_id == assessment.id
        ).count()
        answered_count = db.query(models.Answer).filter(
            models.Answer.assessment_id == assessment.id,
            models.Answer.value.isnot(None),
            models.Answer.value != ''
        ).count()

        progress = int((answered_count / total_answers) * 100) if total_answers > 0 else 0

        # Skip if already 100% complete (just not marked as completed)
        if progress >= 100:
            continue

        # Calculate days since creation
        days_since_created = (datetime.utcnow() - assessment.created_at).days

        incomplete_assessments.append({
            "assessment_id": str(assessment.id),
            "assessment_name": assessment.name,
            "framework_name": framework.name,
            "user_id": str(user.id),
            "user_email": user.email,
            "organisation_id": str(user.organisation_id),
            "progress_percentage": progress,
            "days_incomplete": days_since_created,
            "created_at": assessment.created_at,
            "updated_at": assessment.updated_at
        })

    return incomplete_assessments

