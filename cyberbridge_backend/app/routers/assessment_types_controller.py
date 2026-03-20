# assessment_types_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database.database import get_db
from app.repositories import assessment_type_repository
from app.dtos import schemas

router = APIRouter(
    prefix="/assessment-types",
    tags=["assessment-types"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.AssessmentTypeResponse])
def read_assessment_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assessment_types = assessment_type_repository.get_assessment_types(db, skip=skip, limit=limit)
    return assessment_types

@router.get("/{assessment_type_id}", response_model=schemas.AssessmentTypeResponse)
def read_assessment_type(assessment_type_id: str, db: Session = Depends(get_db)):
    try:
        db_assessment_type = assessment_type_repository.get_assessment_type(db, assessment_type_id=uuid.UUID(assessment_type_id))
        if db_assessment_type is None:
            raise HTTPException(status_code=404, detail="Assessment type not found")
        return db_assessment_type
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assessment type ID format")