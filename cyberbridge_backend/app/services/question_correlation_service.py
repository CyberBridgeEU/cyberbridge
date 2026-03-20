import logging
import os
import shutil
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional

from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)

def get_correlated_questions(db: Session, question_id: uuid.UUID, organisation_id: uuid.UUID = None,
                            scope_id: uuid.UUID = None, scope_entity_id: uuid.UUID = None) -> List[uuid.UUID]:
    """
    Get all question IDs that are in the same correlation group as the given question.
    This includes direct correlations and transitive correlations (correlation groups).
    For example: if A correlates with B and B correlates with C, then A, B, and C form a group.

    Correlations are now scope-specific:
    - Only returns questions correlated within the same scope (scope_id + scope_entity_id)
    - For 'Other' scope, scope_entity_id can be None
    """
    visited = set()
    correlation_group = set()

    def find_correlation_group(current_question_id: uuid.UUID):
        if current_question_id in visited:
            return

        visited.add(current_question_id)
        correlation_group.add(current_question_id)

        # Find all direct correlations for current question (filtered by organization and scope)
        query = db.query(models.QuestionCorrelation).filter(
            or_(
                models.QuestionCorrelation.question_a_id == current_question_id,
                models.QuestionCorrelation.question_b_id == current_question_id
            )
        )

        # Filter by organization if provided
        if organisation_id:
            query = query.filter(models.QuestionCorrelation.organisation_id == organisation_id)

        # Filter by scope if provided
        if scope_id:
            query = query.filter(models.QuestionCorrelation.scope_id == scope_id)

            # For scope_entity_id, we need to handle None values (for 'Other' scope)
            if scope_entity_id is not None:
                query = query.filter(models.QuestionCorrelation.scope_entity_id == scope_entity_id)
            else:
                # For 'Other' scope, only match correlations where scope_entity_id is also None
                query = query.filter(models.QuestionCorrelation.scope_entity_id.is_(None))

        correlations = query.all()

        # Recursively add all correlated questions to the group
        for correlation in correlations:
            if correlation.question_a_id == current_question_id:
                find_correlation_group(correlation.question_b_id)
            else:
                find_correlation_group(correlation.question_a_id)

    # Start building the correlation group from the given question
    find_correlation_group(question_id)

    # Remove the original question from the result (we only want the correlated ones)
    correlation_group.discard(question_id)

    return list(correlation_group)

def create_transitive_correlations(db: Session, new_correlation: models.QuestionCorrelation, created_by: uuid.UUID) -> None:
    """
    When a new correlation A↔B is created, find all questions already correlated with A or B,
    and create explicit correlations between all questions in the group.

    For example:
    - If A↔C already exists, and we create A↔B
    - This function will automatically create B↔C

    Transitive correlations are scope-specific - they only apply within the same scope.
    """
    try:
        logger.info(f"Creating transitive correlations for new correlation between {new_correlation.question_a_id} and {new_correlation.question_b_id}")

        # Get all questions in the correlation group that includes question_a (filtered by organization and scope)
        group_a = get_correlated_questions(
            db,
            new_correlation.question_a_id,
            new_correlation.organisation_id,
            new_correlation.scope_id,
            new_correlation.scope_entity_id
        )

        # Get all questions in the correlation group that includes question_b (filtered by organization and scope)
        group_b = get_correlated_questions(
            db,
            new_correlation.question_b_id,
            new_correlation.organisation_id,
            new_correlation.scope_id,
            new_correlation.scope_entity_id
        )

        # Combine both groups and add the two questions from the new correlation
        all_questions = set(group_a + group_b)
        all_questions.add(new_correlation.question_a_id)
        all_questions.add(new_correlation.question_b_id)

        logger.info(f"Total correlation group size: {len(all_questions)} questions")

        # Create correlations between all pairs in the group
        created_count = 0
        all_questions_list = list(all_questions)

        for i, question_1 in enumerate(all_questions_list):
            for j, question_2 in enumerate(all_questions_list):
                if i >= j:  # Skip self-correlations and duplicates (since correlation is bidirectional)
                    continue

                # Check if this correlation already exists
                existing = db.query(models.QuestionCorrelation).filter(
                    or_(
                        and_(
                            models.QuestionCorrelation.question_a_id == question_1,
                            models.QuestionCorrelation.question_b_id == question_2
                        ),
                        and_(
                            models.QuestionCorrelation.question_a_id == question_2,
                            models.QuestionCorrelation.question_b_id == question_1
                        )
                    )
                ).first()

                if not existing:
                    # Create the missing transitive correlation with the same scope
                    transitive_correlation = models.QuestionCorrelation(
                        question_a_id=question_1,
                        question_b_id=question_2,
                        organisation_id=new_correlation.organisation_id,
                        scope_id=new_correlation.scope_id,
                        scope_entity_id=new_correlation.scope_entity_id,
                        created_by=created_by
                    )
                    db.add(transitive_correlation)
                    created_count += 1
                    logger.info(f"Created transitive correlation between {question_1} and {question_2}")

        if created_count > 0:
            db.commit()
            logger.info(f"Successfully created {created_count} transitive correlations")
        else:
            logger.info("No new transitive correlations needed")

    except Exception as e:
        logger.error(f"Error creating transitive correlations: {str(e)}")
        db.rollback()
        raise

def backfill_transitive_correlations(db: Session) -> dict:
    """
    Backfill transitive correlations for all existing correlations in the database.
    This should be run once to ensure all existing correlations have their transitive relationships.
    """
    try:
        logger.info("Starting backfill of transitive correlations")

        # Get all existing correlations
        all_correlations = db.query(models.QuestionCorrelation).all()
        logger.info(f"Found {len(all_correlations)} existing correlations")

        # Get all unique questions involved in correlations
        all_question_ids = set()
        for correlation in all_correlations:
            all_question_ids.add(correlation.question_a_id)
            all_question_ids.add(correlation.question_b_id)

        logger.info(f"Found {len(all_question_ids)} unique questions in correlations")

        # Group questions by their correlation groups
        processed_questions = set()
        correlation_groups = []

        for question_id in all_question_ids:
            if question_id not in processed_questions:
                # Get the full correlation group for this question
                group = get_correlated_questions(db, question_id)
                group.append(question_id)  # Include the question itself
                correlation_groups.append(group)

                # Mark all questions in this group as processed
                for q_id in group:
                    processed_questions.add(q_id)

        logger.info(f"Found {len(correlation_groups)} correlation groups")

        total_created = 0

        # For each group, ensure all pairs are correlated
        for group in correlation_groups:
            if len(group) <= 1:
                continue

            logger.info(f"Processing group with {len(group)} questions")

            for i, question_1 in enumerate(group):
                for j, question_2 in enumerate(group):
                    if i >= j:  # Skip self-correlations and duplicates
                        continue

                    # Check if this correlation already exists
                    existing = db.query(models.QuestionCorrelation).filter(
                        or_(
                            and_(
                                models.QuestionCorrelation.question_a_id == question_1,
                                models.QuestionCorrelation.question_b_id == question_2
                            ),
                            and_(
                                models.QuestionCorrelation.question_a_id == question_2,
                                models.QuestionCorrelation.question_b_id == question_1
                            )
                        )
                    ).first()

                    if not existing:
                        # Create the missing transitive correlation
                        # Use the first correlation's created_by for consistency
                        created_by = all_correlations[0].created_by if all_correlations else None

                        transitive_correlation = models.QuestionCorrelation(
                            question_a_id=question_1,
                            question_b_id=question_2,
                            created_by=created_by
                        )
                        db.add(transitive_correlation)
                        total_created += 1
                        logger.info(f"Created missing transitive correlation between {question_1} and {question_2}")

        if total_created > 0:
            db.commit()
            logger.info(f"Successfully created {total_created} missing transitive correlations")
        else:
            logger.info("No missing transitive correlations found")

        return {
            "message": "Transitive correlation backfill completed",
            "groups_processed": len(correlation_groups),
            "correlations_created": total_created,
            "total_questions": len(all_question_ids)
        }

    except Exception as e:
        logger.error(f"Error during transitive correlation backfill: {str(e)}")
        db.rollback()
        raise

def get_assessments_for_correlated_questions(db: Session, question_ids: List[uuid.UUID],
                                             organisation_id: uuid.UUID,
                                             scope_id: uuid.UUID = None,
                                             scope_entity_id: uuid.UUID = None) -> List[models.Assessment]:
    """
    Get all assessments from the same organization that contain any of the correlated questions.
    Now also filters by scope to ensure only assessments with matching scope are returned.
    """
    if not question_ids:
        return []

    # Build query for assessments that contain these questions and belong to the same organization
    query = db.query(models.Assessment).join(
        models.User, models.Assessment.user_id == models.User.id
    ).filter(
        and_(
            models.User.organisation_id == organisation_id,
            models.Assessment.id.in_(
                db.query(models.Answer.assessment_id).filter(
                    models.Answer.question_id.in_(question_ids)
                )
            )
        )
    )

    # Filter by scope if provided
    if scope_id:
        query = query.filter(models.Assessment.scope_id == scope_id)

        # Handle scope_entity_id (None for 'Other' scope)
        if scope_entity_id is not None:
            query = query.filter(models.Assessment.scope_entity_id == scope_entity_id)
        else:
            # For 'Other' scope, only match assessments where scope_entity_id is also None
            query = query.filter(models.Assessment.scope_entity_id.is_(None))

    assessments = query.all()

    return assessments

def copy_evidence_files(db: Session, source_answer_id: uuid.UUID, target_answer_id: uuid.UUID) -> None:
    """
    Copy evidence files from source answer to target answer.
    This includes copying the physical files and creating database records.
    """
    try:
        # Get source evidence files
        source_evidence = db.query(models.Evidence).filter(
            models.Evidence.answer_id == source_answer_id
        ).all()

        if not source_evidence:
            return

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source_dir = os.path.join(project_root, "uploads", str(source_answer_id))
        target_dir = os.path.join(project_root, "uploads", str(target_answer_id))

        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Copy each evidence file
        for evidence in source_evidence:
            if os.path.exists(evidence.filepath):
                # Copy the physical file
                target_filepath = os.path.join(target_dir, evidence.filename)
                shutil.copy2(evidence.filepath, target_filepath)

                # Create new evidence record
                new_evidence = models.Evidence(
                    filename=evidence.filename,
                    file_size=evidence.file_size,
                    file_type=evidence.file_type,
                    filepath=target_filepath,
                    answer_id=target_answer_id
                )
                db.add(new_evidence)

        db.commit()

    except Exception as e:
        logger.error(f"Error copying evidence files from {source_answer_id} to {target_answer_id}: {str(e)}")
        db.rollback()
        raise

def synchronize_correlated_answers(db: Session, source_answer: models.Answer) -> None:
    """
    Synchronize answers across correlated questions ONLY within the same scope.
    This function finds:
    1. All correlated questions and updates their answers in assessments with matching scope
    2. All instances of the same question across assessments ONLY if the question has correlations
       and the assessments have matching scope (scope_id + scope_entity_id)

    Scope filtering ensures:
    - Assessments with scope 'Product: Widget X' only sync with other 'Product: Widget X' assessments
    - Assessments with scope 'Other' only sync with other 'Other' scope assessments
    """
    try:
        # Get the source assessment
        source_assessment = db.query(models.Assessment).filter(
            models.Assessment.id == source_answer.assessment_id
        ).first()

        if not source_assessment:
            logger.error(f"Source assessment not found for answer {source_answer.id}")
            return

        # Get the user's organisation_id
        user = db.query(models.User).filter(models.User.id == source_assessment.user_id).first()
        if not user:
            logger.error(f"User not found for assessment {source_assessment.id}")
            return

        # Get the source assessment's scope
        source_scope_id = source_assessment.scope_id
        source_scope_entity_id = source_assessment.scope_entity_id

        # Check if this question has any correlations (filtered by organization and scope)
        correlated_question_ids = get_correlated_questions(
            db,
            source_answer.question_id,
            user.organisation_id,
            source_scope_id,
            source_scope_entity_id
        )

        # If the question has no correlations in this scope, do not synchronize anything
        if not correlated_question_ids:
            return

        # STEP 1: Synchronize the SAME QUESTION across all assessments with matching scope
        # (Only if the question has correlations in this scope)
        same_question_query = db.query(models.Answer).join(
            models.Assessment, models.Answer.assessment_id == models.Assessment.id
        ).join(
            models.User, models.Assessment.user_id == models.User.id
        ).filter(
            and_(
                models.Answer.question_id == source_answer.question_id,  # Same question
                models.User.organisation_id == user.organisation_id,  # Same organization
                models.Answer.id != source_answer.id  # Exclude source answer
            )
        )

        # Filter by scope
        if source_scope_id:
            same_question_query = same_question_query.filter(
                models.Assessment.scope_id == source_scope_id
            )

            # Handle scope_entity_id (None for 'Other' scope)
            if source_scope_entity_id is not None:
                same_question_query = same_question_query.filter(
                    models.Assessment.scope_entity_id == source_scope_entity_id
                )
            else:
                # For 'Other' scope, only match assessments where scope_entity_id is also None
                same_question_query = same_question_query.filter(
                    models.Assessment.scope_entity_id.is_(None)
                )

        same_question_answers = same_question_query.all()

        for target_answer in same_question_answers:
            sync_answer_data(db, source_answer, target_answer)

        # STEP 2: Synchronize CORRELATED QUESTIONS across different frameworks (same scope only)

        if correlated_question_ids:
            # Get assessments that contain correlated questions for the same organization and scope
            target_assessments = get_assessments_for_correlated_questions(
                db,
                correlated_question_ids,
                user.organisation_id,
                source_scope_id,
                source_scope_entity_id
            )

            for assessment in target_assessments:
                # Find answers in this assessment that correspond to correlated questions
                target_answers = db.query(models.Answer).filter(
                    and_(
                        models.Answer.assessment_id == assessment.id,
                        models.Answer.question_id.in_(correlated_question_ids)
                    )
                ).all()

                for target_answer in target_answers:
                    # Skip if this is the same answer we're syncing from
                    if target_answer.id == source_answer.id:
                        continue

                    sync_answer_data(db, source_answer, target_answer)

        db.commit()

    except Exception as e:
        logger.error(f"Error synchronizing correlated answers: {str(e)}")
        db.rollback()
        raise

def sync_answer_data(db: Session, source_answer: models.Answer, target_answer: models.Answer) -> None:
    """
    Helper function to sync data from source answer to target answer.
    ONLY syncs the answer value - NOT policies, evidence descriptions, or evidence files
    as these are framework-specific.
    """
    try:
        # Update target answer with ONLY the answer value
        target_answer.value = source_answer.value

        # Do NOT copy:
        # - policy_id (framework-specific)
        # - evidence_description (framework-specific)
        # - evidence files (framework-specific)

    except Exception as e:
        logger.error(f"Error syncing answer data from {source_answer.id} to {target_answer.id}: {str(e)}")
        raise