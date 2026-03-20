# crud.py
from typing import List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Session
import uuid
from app.services.security_service import get_password_hash
from app.models import models
from app.dtos import schemas

# Question CRUD operations
def get_question(db: Session, question_id: uuid.UUID):
    return db.query(models.Question).filter(models.Question.id == question_id).first()


def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Question).offset(skip).limit(limit).all()


def get_all_questions_for_frameworks(db: Session, framework_ids: schemas.FrameworkIdsRequest):
    return (
        db.query(
            models.Question.id.cast(String).label("key"),
            models.Question.id.cast(String).label("question_id"),
            models.Framework.id.cast(String).label("framework_id"),
            models.Framework.name.label("framework_name"),
            models.Framework.description.label("framework_description"),
            models.Question.text.label("question_text"),
            models.Question.mandatory.label("is_question_mandatory"),
            models.AssessmentType.type_name.label("assessment_type"),
            models.FrameworkQuestion.order.label("order"),
        )
        .join(models.FrameworkQuestion, models.Framework.id == models.FrameworkQuestion.framework_id)
        .join(models.Question, models.FrameworkQuestion.question_id == models.Question.id)
        .join(models.AssessmentType, models.Question.assessment_type_id == models.AssessmentType.id)
        .filter(models.Framework.id.in_(framework_ids.framework_ids))
        .order_by(models.FrameworkQuestion.order)
        .all()
    )


def create_question(db: Session, question: schemas.QuestionCreate):
    db_question = models.Question(**question.model_dump())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def delete_question(db: Session, question_id: uuid.UUID) -> bool:
    """
    Delete a question and its associated records.

    Steps:
    1. Find all answers for the question
    2. For each answer, delete associated evidence
    3. Delete all answers for the question
    4. Remove the question from framework_questions table
    5. Check if question is still associated with any frameworks
    6. If not, delete the question from questions table

    Args:
        db: Database session
        question_id: UUID of the question to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Find all answers for the question
        answers = db.query(models.Answer).filter(models.Answer.question_id == question_id).all()

        # For each answer, delete associated evidence
        for answer in answers:
            db.query(models.Evidence).filter(models.Evidence.answer_id == answer.id).delete()

        # Delete all answers for the question
        db.query(models.Answer).filter(models.Answer.question_id == question_id).delete()

        # Remove the question from framework_questions table
        db.query(models.FrameworkQuestion).filter(models.FrameworkQuestion.question_id == question_id).delete()

        # Check if question is still associated with any frameworks
        remaining_frameworks = db.query(models.FrameworkQuestion).filter(
            models.FrameworkQuestion.question_id == question_id
        ).count()

        # If no frameworks are associated, delete the question
        if remaining_frameworks == 0:
            db.query(models.Question).filter(models.Question.id == question_id).delete()

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting question: {str(e)}")
        return False
