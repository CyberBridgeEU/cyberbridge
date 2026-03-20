# crud.py
import os
import shutil
import zipfile
from io import BytesIO
from typing import List

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
import uuid

from app.dtos.schemas import UpdateAnswerRequest
from app.repositories import assessment_repository
from app.services.security_service import get_password_hash
from app.models import models
from app.dtos import schemas
from app.database.database import db_operation
from sqlalchemy import or_, and_

# Answer CRUD operations
def get_answer(db: Session, answer_id: uuid.UUID):
    return db.query(models.Answer).filter(models.Answer.id == answer_id).first()


def get_assessment_answers(db: Session, assessment_id: uuid.UUID):
    return db.query(models.Answer).filter(models.Answer.assessment_id == assessment_id).all()


@db_operation
def create_answer(db: Session, answer: schemas.AnswerCreate):
    db_answer = models.Answer(**answer.model_dump())
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer


@db_operation
def update_answer(answer: UpdateAnswerRequest, db: Session):
    db_answer = db.query(models.Answer).filter(models.Answer.id == uuid.UUID(answer.answer_id)).first()
    if db_answer:
        db_answer.value = answer.answer_value if answer.answer_value != "" else None
        if hasattr(answer, 'evidence_description') and answer.evidence_description is not None:
            db_answer.evidence_description = answer.evidence_description if answer.evidence_description != "" else None
        if hasattr(answer, 'policy_id'):
            if answer.policy_id is None or answer.policy_id == "":
                db_answer.policy_id = None
            else:
                policy_id = uuid.UUID(answer.policy_id)

                # Validate policy exists and get its organization
                policy = db.query(models.Policies).filter(models.Policies.id == policy_id).first()
                if not policy:
                    raise ValueError(f"Policy {policy_id} not found")

                # Get the answer's assessment and its associated user's organization
                assessment = db.query(models.Assessment).filter(models.Assessment.id == db_answer.assessment_id).first()
                if not assessment:
                    raise ValueError("Assessment not found for this answer")

                user = db.query(models.User).filter(models.User.id == assessment.user_id).first()
                if not user:
                    raise ValueError("User not found for this assessment")

                # Prevent cross-organization assignments
                if policy.organisation_id != user.organisation_id:
                    raise ValueError(f"Cross-organization assignment not allowed: Policy belongs to organization {policy.organisation_id} but Assessment belongs to organization {user.organisation_id}")

                db_answer.policy_id = policy_id
        db.commit()
        db.refresh(db_answer)
    return db_answer

def delete_existing_evidences(answer_id: uuid.UUID, db: Session):
    # Delete database records
    db.query(models.Evidence).filter(models.Evidence.answer_id == answer_id).delete()
    db.commit()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    evidence_directory = os.path.join(project_root, "uploads", str(answer_id))

    # Check if directory exists before attempting to delete it
    if os.path.exists(evidence_directory):
        shutil.rmtree(evidence_directory)  # This removes the folder and all its contents

    return


def get_answer_id_for_evidences(db: Session, evidence_ids: List[str]) -> str:
    """
    Get the common answer_id for a list of evidence IDs.
    Returns None if evidences belong to different answers or don't exist.
    """
    result = db.query(distinct(models.Evidence.answer_id)) \
        .filter(models.Evidence.id.in_(evidence_ids)) \
        .all()

    # Check if there's exactly one answer_id (all evidence belongs to same answer)
    if len(result) == 1:
        return str(result[0][0])
    return None


def create_zip_file(db: Session, evidence_ids: List[str]) -> BytesIO:
    """
    Creates a zip file containing all evidence files for the given evidence IDs.
    Assumes all evidence IDs belong to the same answer.
    """
    # Get the common answer_id for all evidence
    answer_id = get_answer_id_for_evidences(db, evidence_ids)
    if not answer_id:
        raise ValueError("The selected files don't belong to the same answer or don't exist")

    # Create in-memory zip buffer
    zip_buffer = BytesIO()

    # Path to the uploads folder for this answer
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    answer_directory = os.path.join(project_root, "uploads", answer_id)

    # Check if directory exists
    if not os.path.exists(answer_directory):
        raise ValueError(f"Upload directory for answer {answer_id} not found")

    # Create zip file from the answer directory
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Walk through the directory
        for root, _, files in os.walk(answer_directory):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate arcname (path within zip) relative to parent directory
                arcname = os.path.relpath(file_path, os.path.dirname(answer_directory))
                zip_file.write(file_path, arcname=arcname)

    zip_buffer.seek(0)
    return zip_buffer


@db_operation
def update_evidence(evidence: schemas.EvidenceCreate ,db: Session):
    # Create new evidence
    db_evidence = models.Evidence(**evidence.model_dump())
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@db_operation
def update_assessment_answers(db: Session, answers: list[UpdateAnswerRequest]):
    for answer in answers:
        update_answer(answer, db)

def _get_existing_correlated_answer(db: Session, question_id: uuid.UUID, user_id: uuid.UUID, scope_id: uuid.UUID = None, scope_entity_id: uuid.UUID = None):
    """
    Find an existing answered question that matches the given question_id or is correlated with it.
    This includes:
    1. Same question from other assessments for the same user with MATCHING SCOPE (ONLY if the question has correlations)
    2. Correlated questions from different frameworks for the same user with MATCHING SCOPE
    Returns the most recent answer found.
    """
    # Get user's organisation_id for filtering correlations
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    # First, check if this question has any correlations at all (filtered by organization)
    from app.services.question_correlation_service import get_correlated_questions
    correlated_question_ids = get_correlated_questions(db, question_id, user.organisation_id)

    # If the question has no correlations, don't return any existing answers
    if not correlated_question_ids:
        return None

    # Build scope filter conditions
    scope_conditions = []
    if scope_id:
        scope_conditions.append(models.Assessment.scope_id == scope_id)

        # Also filter by scope_entity_id
        if scope_entity_id:
            scope_conditions.append(models.Assessment.scope_entity_id == scope_entity_id)
        else:
            scope_conditions.append(models.Assessment.scope_entity_id.is_(None))

    # PRIORITY 1: Check if this SAME QUESTION has been answered in other assessments
    # (Only if the question has correlations and from assessments with MATCHING SCOPE)
    same_question_query = (db.query(models.Answer)
                           .join(models.Assessment, models.Answer.assessment_id == models.Assessment.id)
                           .filter(
                               and_(
                                   models.Answer.question_id == question_id,  # Same question
                                   models.Assessment.user_id == user_id,  # Same user
                                   models.Answer.value.isnot(None),  # Only get answered questions
                                   models.Answer.value != "",
                                   *scope_conditions  # Add scope filters
                               )
                           )
                           .order_by(models.Answer.id.desc()))  # Get most recent answer

    same_question_answer = same_question_query.first()

    if same_question_answer:
        return same_question_answer

    # PRIORITY 2: Check for correlated questions if same question not found
    # Find existing answers for correlated questions from the same user with MATCHING SCOPE
    correlated_query = (db.query(models.Answer)
                        .join(models.Assessment, models.Answer.assessment_id == models.Assessment.id)
                        .filter(
                            and_(
                                models.Answer.question_id.in_(correlated_question_ids),
                                models.Assessment.user_id == user_id,
                                models.Answer.value.isnot(None),  # Only get answered questions
                                models.Answer.value != "",
                                *scope_conditions  # Add scope filters
                            )
                        )
                        .order_by(models.Answer.id.desc()))  # Get most recent answer

    correlated_answer = correlated_query.first()

    return correlated_answer

@db_operation
def create_answers_for_assessment(db: Session, framework_id: uuid.UUID, assessment_id: uuid.UUID, assessment_type_id: uuid.UUID):
    # Get the assessment to find the user and scope
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise ValueError("Assessment not found")

    # Get the framework to find the organization
    framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
    if not framework:
        raise ValueError("Framework not found")

    # Check if AI Policy Aligner is enabled and get alignments if so
    policy_alignments = {}
    try:
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == framework.organisation_id
        ).first()

        if org_settings and hasattr(org_settings, 'ai_policy_aligner_enabled') and org_settings.ai_policy_aligner_enabled:
            # Get all alignments for this framework with confidence >= 80
            alignments = db.query(models.PolicyQuestionAlignment).filter(
                models.PolicyQuestionAlignment.framework_id == framework_id,
                models.PolicyQuestionAlignment.confidence_score >= 80
            ).all()

            # Build a lookup dict by question_id
            for alignment in alignments:
                policy_alignments[str(alignment.question_id)] = alignment.policy_id
    except Exception as e:
        # If there's any error getting alignments, continue without them
        import logging
        logging.getLogger(__name__).warning(f"Error getting policy alignments: {e}")

    # Get framework questions that match the specific assessment type
    framework_questions = (db.query(models.FrameworkQuestion)
                          .join(models.Question, models.FrameworkQuestion.question_id == models.Question.id)
                          .filter(models.FrameworkQuestion.framework_id == framework_id,
                                 models.Question.assessment_type_id == assessment_type_id)
                          .order_by(models.FrameworkQuestion.order)
                          .all())

    for framework_question in framework_questions:
        # Check if this question has correlated questions with existing answers
        # Pass scope information to filter by matching scope
        correlated_answer = _get_existing_correlated_answer(
            db,
            framework_question.question_id,
            assessment.user_id,
            assessment.scope_id,
            assessment.scope_entity_id
        )

        # Check if there's a policy alignment for this question
        question_id_str = str(framework_question.question_id)
        aligned_policy_id = policy_alignments.get(question_id_str)

        if correlated_answer:
            # Create answer with ONLY the answer value from correlated question
            # Do NOT copy policy_id, evidence_description, or evidence files
            # as these are framework-specific
            # BUT apply aligned policy_id if available
            answer_data = schemas.AnswerCreate(
                question_id=framework_question.question_id,
                assessment_id=assessment_id,
                value=correlated_answer.value,
                policy_id=aligned_policy_id  # Auto-populate from AI alignment if available
            )
            new_answer = create_answer(db, answer=answer_data)
        else:
            # Create answer with aligned policy_id if available
            answer_data = schemas.AnswerCreate(
                question_id=framework_question.question_id,
                assessment_id=assessment_id,
                policy_id=aligned_policy_id  # Auto-populate from AI alignment if available
            )
            create_answer(db, answer=answer_data)


@db_operation
def fetch_answers_for_assessment(db: Session, assessment_id: uuid.UUID, current_user=None):
    # Get the assessment to check its scope
    db_assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    assessment_scope_id = db_assessment.scope_id if db_assessment else None
    assessment_scope_entity_id = db_assessment.scope_entity_id if db_assessment else None

    # Base query with organization domain included in framework names
    query = (
        db.query(
            models.Answer.id.label('answer_id'),
            models.Answer.assessment_id,
            models.Answer.question_id,
            models.Answer.value.label('answer_value'),
            models.Answer.evidence_description,
            models.Answer.policy_id,
            models.Question.text.label('question_text'),
            models.Question.description.label('question_description'),
            models.Question.mandatory.label('is_question_mandatory'),
            models.AssessmentType.type_name.label('assessment_type'),
            models.Policies.title.label('policy_title'),
            func.string_agg(
                func.distinct(func.concat(models.Framework.name, '(', models.Organisations.domain, ')')),
                ', '
            ).label('framework_names'),
            func.min(models.FrameworkQuestion.order).label('min_order')
        )
        .join(models.Question, models.Answer.question_id == models.Question.id)
        .join(models.AssessmentType, models.Question.assessment_type_id == models.AssessmentType.id)
        .join(models.FrameworkQuestion, models.Question.id == models.FrameworkQuestion.question_id)
        .join(models.Framework, models.FrameworkQuestion.framework_id == models.Framework.id)
        .join(models.Organisations, models.Framework.organisation_id == models.Organisations.id)
        .outerjoin(models.Policies, models.Answer.policy_id == models.Policies.id)
        .filter(models.Answer.assessment_id == assessment_id)
    )

    # Filter frameworks by organization for org_admin and org_user
    if current_user and current_user.role_name in ['org_admin', 'org_user']:
        query = query.filter(models.Framework.organisation_id == current_user.organisation_id)
    # super_admin sees all frameworks (no additional filter needed)

    results = (
        query.group_by(
            models.Answer.id,
            models.Answer.assessment_id,
            models.Answer.question_id,
            models.Answer.value,
            models.Answer.evidence_description,
            models.Answer.policy_id,
            models.Question.text,
            models.Question.description,
            models.Question.mandatory,
            models.AssessmentType.type_name,
            models.Policies.title
        )
        .order_by('min_order')
        .all()
    )

    # Convert SQLAlchemy results to a list of dictionaries that we can modify
    result_list = [result._asdict() for result in results]

    # Add evidence files and correlation status for each answer
    for result_dict in result_list:
        evidence_files = db.query(models.Evidence).filter(models.Evidence.answer_id == result_dict['answer_id']).all()

        # Convert evidence files to serializable dictionaries
        result_dict['files'] = [
            {
                'id': str(file.id),
                'name': file.filename,
                'type': file.file_type,
                'size': file.file_size,
                'path': file.filepath
            }
            for file in evidence_files
        ]

        # Check if this question has correlations with other questions IN THE USER'S ORGANIZATION
        # and matching the ASSESSMENT'S SCOPE
        correlation_filter = or_(
            models.QuestionCorrelation.question_a_id == result_dict['question_id'],
            models.QuestionCorrelation.question_b_id == result_dict['question_id']
        )

        # Build scope filter
        scope_filters = []
        if assessment_scope_id:
            scope_filters.append(models.QuestionCorrelation.scope_id == assessment_scope_id)

            # Also filter by scope_entity_id
            if assessment_scope_entity_id:
                scope_filters.append(models.QuestionCorrelation.scope_entity_id == assessment_scope_entity_id)
            else:
                scope_filters.append(models.QuestionCorrelation.scope_entity_id.is_(None))

        if current_user and current_user.organisation_id:
            # Filter by organization and scope for org users
            filters_to_apply = [
                correlation_filter,
                models.QuestionCorrelation.organisation_id == current_user.organisation_id
            ]
            if scope_filters:
                filters_to_apply.extend(scope_filters)

            correlations_exist = db.query(models.QuestionCorrelation).filter(
                and_(*filters_to_apply)
            ).first()
        else:
            # For super_admin or when no current_user, filter by scope only
            filters_to_apply = [correlation_filter]
            if scope_filters:
                filters_to_apply.extend(scope_filters)

            correlations_exist = db.query(models.QuestionCorrelation).filter(
                and_(*filters_to_apply)
            ).first()

        result_dict['is_correlated'] = correlations_exist is not None

    return result_list


def delete_answers_for_assessment(db: Session, assessment_id: uuid.UUID):
    print(f"DEBUG: delete_answers_for_assessment called with db={db}, assessment_id={assessment_id}")
    db_assessment = assessment_repository.get_assessment(db, assessment_id=assessment_id)
    if not db_assessment:
        return None

    db_answers_for_assessment = db.query(models.Answer).filter(models.Answer.assessment_id == assessment_id).all()
    for db_answer in db_answers_for_assessment:
        delete_existing_evidences(answer_id=db_answer.id, db=db)
        db.delete(db_answer)

    db.delete(db_assessment)
    db.commit()

    return db_assessment
