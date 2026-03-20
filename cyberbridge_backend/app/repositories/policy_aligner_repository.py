# policy_aligner_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from typing import List, Optional
from datetime import datetime

from app.models import models


def create_alignment(
    db: Session,
    organisation_id: uuid.UUID,
    framework_id: uuid.UUID,
    question_id: uuid.UUID,
    policy_id: uuid.UUID,
    confidence_score: int,
    reasoning: Optional[str] = None
) -> models.PolicyQuestionAlignment:
    """Create a single policy-question alignment."""
    alignment = models.PolicyQuestionAlignment(
        organisation_id=organisation_id,
        framework_id=framework_id,
        question_id=question_id,
        policy_id=policy_id,
        confidence_score=confidence_score,
        reasoning=reasoning
    )
    db.add(alignment)
    db.commit()
    db.refresh(alignment)
    return alignment


def create_alignments_bulk(
    db: Session,
    organisation_id: uuid.UUID,
    framework_id: uuid.UUID,
    alignments: List[dict]
) -> int:
    """
    Create multiple policy-question alignments in bulk.

    Args:
        db: Database session
        organisation_id: Organization UUID
        framework_id: Framework UUID
        alignments: List of dicts with keys: question_id, policy_id, confidence_score, reasoning

    Returns:
        Number of alignments created
    """
    created_count = 0

    for alignment_data in alignments:
        try:
            alignment = models.PolicyQuestionAlignment(
                organisation_id=organisation_id,
                framework_id=framework_id,
                question_id=uuid.UUID(alignment_data['question_id']) if isinstance(alignment_data['question_id'], str) else alignment_data['question_id'],
                policy_id=uuid.UUID(alignment_data['policy_id']) if isinstance(alignment_data['policy_id'], str) else alignment_data['policy_id'],
                confidence_score=alignment_data['confidence_score'],
                reasoning=alignment_data.get('reasoning')
            )
            db.add(alignment)
            created_count += 1
        except Exception as e:
            # Skip invalid alignments but continue processing
            print(f"Error creating alignment: {e}")
            continue

    db.commit()
    return created_count


def get_alignments_for_framework(
    db: Session,
    framework_id: uuid.UUID
) -> List[models.PolicyQuestionAlignment]:
    """Get all policy-question alignments for a framework."""
    return db.query(models.PolicyQuestionAlignment).filter(
        models.PolicyQuestionAlignment.framework_id == framework_id
    ).all()


def get_alignments_for_framework_with_details(
    db: Session,
    framework_id: uuid.UUID
) -> List[dict]:
    """
    Get all policy-question alignments for a framework with question and policy details.

    Returns list of dicts with: question_id, question_text, policy_id, policy_title, confidence_score, reasoning
    """
    alignments = db.query(
        models.PolicyQuestionAlignment.id,
        models.PolicyQuestionAlignment.question_id,
        models.PolicyQuestionAlignment.policy_id,
        models.PolicyQuestionAlignment.confidence_score,
        models.PolicyQuestionAlignment.reasoning,
        models.PolicyQuestionAlignment.created_at,
        models.PolicyQuestionAlignment.updated_at,
        models.Question.text.label('question_text'),
        models.Policies.title.label('policy_title')
    ).join(
        models.Question, models.PolicyQuestionAlignment.question_id == models.Question.id
    ).join(
        models.Policies, models.PolicyQuestionAlignment.policy_id == models.Policies.id
    ).filter(
        models.PolicyQuestionAlignment.framework_id == framework_id
    ).all()

    return [
        {
            'id': str(a.id),
            'question_id': str(a.question_id),
            'question_text': a.question_text,
            'policy_id': str(a.policy_id),
            'policy_title': a.policy_title,
            'confidence_score': a.confidence_score,
            'reasoning': a.reasoning,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'updated_at': a.updated_at.isoformat() if a.updated_at else None
        }
        for a in alignments
    ]


def delete_alignments_for_framework(db: Session, framework_id: uuid.UUID) -> int:
    """Delete all policy-question alignments for a framework."""
    result = db.query(models.PolicyQuestionAlignment).filter(
        models.PolicyQuestionAlignment.framework_id == framework_id
    ).delete()
    db.commit()
    return result


def get_alignment_for_question(
    db: Session,
    framework_id: uuid.UUID,
    question_id: uuid.UUID
) -> Optional[models.PolicyQuestionAlignment]:
    """Get the policy alignment for a specific question within a framework."""
    return db.query(models.PolicyQuestionAlignment).filter(
        models.PolicyQuestionAlignment.framework_id == framework_id,
        models.PolicyQuestionAlignment.question_id == question_id
    ).first()


def get_alignment_status(db: Session, framework_id: uuid.UUID) -> dict:
    """
    Get the alignment status for a framework.

    Returns: {has_alignments, alignment_count, last_updated}
    """
    alignments = db.query(models.PolicyQuestionAlignment).filter(
        models.PolicyQuestionAlignment.framework_id == framework_id
    )

    count = alignments.count()

    if count == 0:
        return {
            'has_alignments': False,
            'alignment_count': 0,
            'last_updated': None
        }

    # Get the most recent update timestamp
    last_updated = db.query(func.max(models.PolicyQuestionAlignment.updated_at)).filter(
        models.PolicyQuestionAlignment.framework_id == framework_id
    ).scalar()

    return {
        'has_alignments': True,
        'alignment_count': count,
        'last_updated': last_updated.isoformat() if last_updated else None
    }


def get_policies_for_organisation(db: Session, organisation_id: uuid.UUID) -> List[dict]:
    """Get all policies for an organisation with their details."""
    policies = db.query(models.Policies).filter(
        models.Policies.organisation_id == organisation_id
    ).all()

    return [
        {
            'id': str(p.id),
            'title': p.title,
            'body': p.body
        }
        for p in policies
    ]


def get_framework_questions(db: Session, framework_id: uuid.UUID) -> List[dict]:
    """Get all questions for a framework."""
    questions = db.query(
        models.Question.id,
        models.Question.text
    ).join(
        models.FrameworkQuestion, models.Question.id == models.FrameworkQuestion.question_id
    ).filter(
        models.FrameworkQuestion.framework_id == framework_id
    ).all()

    return [
        {
            'id': str(q.id),
            'text': q.text
        }
        for q in questions
    ]


def get_organisation_id_for_framework(db: Session, framework_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Get the organisation ID for a framework."""
    framework = db.query(models.Framework).filter(
        models.Framework.id == framework_id
    ).first()

    return framework.organisation_id if framework else None
