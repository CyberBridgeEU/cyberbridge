# assessment_type_repository.py
from sqlalchemy.orm import Session
import uuid
from app.models import models
from app.dtos import schemas

def get_assessment_type(db: Session, assessment_type_id: uuid.UUID):
    return db.query(models.AssessmentType).filter(models.AssessmentType.id == assessment_type_id).first()

def get_assessment_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AssessmentType).offset(skip).limit(limit).all()

def get_assessment_type_by_name(db: Session, type_name: str):
    return db.query(models.AssessmentType).filter(models.AssessmentType.type_name == type_name).first()