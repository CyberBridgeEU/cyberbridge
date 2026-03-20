# routers/questions_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from .. import models
from ..repositories import question_repository
from ..dtos import schemas
from ..database.database import get_db

router = APIRouter(prefix="/questions",tags=["questions"],responses={404: {"description": "Not found"}},)


@router.post("/", response_model=schemas.QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    return question_repository.create_question(db=db, question=question)


@router.get("/", response_model=List[schemas.QuestionResponse])
def read_questions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    questions = question_repository.get_questions(db, skip=skip, limit=limit)
    return questions


@router.get("/{question_id}", response_model=schemas.QuestionResponse)
def read_question(question_id: uuid.UUID, db: Session = Depends(get_db)):
    db_question = question_repository.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question

@router.post("/for_frameworks", response_model=List[schemas.FrameworksQuestionsResponse])
def read_questions_for_frameworks(framework_ids: schemas.FrameworkIdsRequest, db: Session = Depends(get_db)):
    try:
        questions = question_repository.get_all_questions_for_frameworks(db, framework_ids=framework_ids)
        return questions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error fetching questions for frameworks: {str(e)}")

@router.put("/{question_id}", response_model=schemas.QuestionResponse)
def update_question(question_id: uuid.UUID, question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    try:
        db_question = question_repository.get_question(db, question_id=question_id)
        if db_question is None:
            raise HTTPException(status_code=404, detail="Question not found")

        # Update question attributes
        for key, value in question.model_dump().items():
            setattr(db_question, key, value)

        db.commit()
        db.refresh(db_question)
        return db_question
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"An error occurred while updating the question: {str(e)}")


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        # First check if the question exists
        db_question = question_repository.get_question(db, question_id=question_id)
        if db_question is None:
            raise HTTPException(status_code=404, detail="Question not found")

        # Use the repository function to delete the question and its associated records
        success = question_repository.delete_question(db, question_id=question_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete question and its associated records"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error occurred while deleting the question: {str(e)}"
        )
