# routers/risk_assessments_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

from ..repositories import risk_assessment_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risks", tags=["risk-assessments"], responses={404: {"description": "Not found"}})


# ===========================
# Risk Assessment List (all risks with latest scores)
# ===========================

@router.get("/assessments", response_model=List[schemas.RiskWithAssessmentResponse])
def get_all_risks_with_assessments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """List all risks with their latest assessment scores"""
    try:
        return risk_assessment_repository.get_all_risks_with_assessments(db, current_user, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risks with assessments: {str(e)}"
        )


# ===========================
# Assessment CRUD per Risk
# ===========================

@router.get("/{risk_id}/assessments", response_model=List[schemas.RiskAssessmentResponse])
def get_assessments_for_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all assessments for a specific risk"""
    try:
        return risk_assessment_repository.get_assessments_for_risk(db, uuid.UUID(risk_id), current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching assessments: {str(e)}"
        )


@router.get("/{risk_id}/assessments/latest", response_model=schemas.RiskAssessmentDetailResponse)
def get_latest_assessment(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get the latest assessment for a risk"""
    try:
        assessment = risk_assessment_repository.get_latest_assessment(db, uuid.UUID(risk_id), current_user)
        if not assessment:
            raise HTTPException(status_code=404, detail="No assessments found for this risk")
        # Load treatment actions
        assessment.treatment_actions = risk_assessment_repository.get_treatment_actions(db, assessment.id)
        return assessment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching latest assessment: {str(e)}"
        )


@router.get("/{risk_id}/assessments/{assessment_id}", response_model=schemas.RiskAssessmentDetailResponse)
def get_assessment(
    risk_id: str,
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get a specific assessment with treatment actions"""
    try:
        assessment = risk_assessment_repository.get_assessment(db, uuid.UUID(risk_id), uuid.UUID(assessment_id), current_user)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        # Load treatment actions
        assessment.treatment_actions = risk_assessment_repository.get_treatment_actions(db, assessment.id)
        return assessment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching assessment: {str(e)}"
        )


@router.post("/{risk_id}/assessments", response_model=schemas.RiskAssessmentDetailResponse)
def create_assessment(
    risk_id: str,
    data: schemas.RiskAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Create a new assessment for a risk"""
    try:
        assessment = risk_assessment_repository.create_assessment(db, uuid.UUID(risk_id), data, current_user)
        assessment.treatment_actions = []
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating assessment: {str(e)}"
        )


@router.put("/{risk_id}/assessments/{assessment_id}", response_model=schemas.RiskAssessmentDetailResponse)
def update_assessment(
    risk_id: str,
    assessment_id: str,
    data: schemas.RiskAssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update an existing assessment"""
    try:
        assessment = risk_assessment_repository.update_assessment(
            db, uuid.UUID(risk_id), uuid.UUID(assessment_id), data, current_user
        )
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        # Load treatment actions for the detail response
        assessment.treatment_actions = risk_assessment_repository.get_treatment_actions(db, assessment.id)
        return assessment
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating assessment: {str(e)}"
        )


@router.delete("/{risk_id}/assessments/{assessment_id}")
def delete_assessment(
    risk_id: str,
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete an assessment"""
    try:
        result = risk_assessment_repository.delete_assessment(
            db, uuid.UUID(risk_id), uuid.UUID(assessment_id), current_user
        )
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return {"message": "Assessment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting assessment: {str(e)}"
        )


# ===========================
# Treatment Action CRUD
# ===========================

@router.get("/{risk_id}/assessments/{assessment_id}/actions", response_model=List[schemas.RiskTreatmentActionResponse])
def get_treatment_actions(
    risk_id: str,
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all treatment actions for an assessment"""
    try:
        # Verify assessment exists and belongs to risk
        assessment = risk_assessment_repository.get_assessment(db, uuid.UUID(risk_id), uuid.UUID(assessment_id), current_user)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return risk_assessment_repository.get_treatment_actions(db, uuid.UUID(assessment_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching treatment actions: {str(e)}"
        )


@router.post("/{risk_id}/assessments/{assessment_id}/actions", response_model=schemas.RiskTreatmentActionResponse)
def create_treatment_action(
    risk_id: str,
    assessment_id: str,
    data: schemas.RiskTreatmentActionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Create a new treatment action"""
    try:
        assessment = risk_assessment_repository.get_assessment(db, uuid.UUID(risk_id), uuid.UUID(assessment_id), current_user)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return risk_assessment_repository.create_treatment_action(db, uuid.UUID(assessment_id), data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating treatment action: {str(e)}"
        )


@router.put("/{risk_id}/assessments/{assessment_id}/actions/{action_id}", response_model=schemas.RiskTreatmentActionResponse)
def update_treatment_action(
    risk_id: str,
    assessment_id: str,
    action_id: str,
    data: schemas.RiskTreatmentActionUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update a treatment action"""
    try:
        result = risk_assessment_repository.update_treatment_action(db, uuid.UUID(action_id), data)
        if not result:
            raise HTTPException(status_code=404, detail="Treatment action not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating treatment action: {str(e)}"
        )


@router.delete("/{risk_id}/assessments/{assessment_id}/actions/{action_id}")
def delete_treatment_action(
    risk_id: str,
    assessment_id: str,
    action_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete a treatment action"""
    try:
        result = risk_assessment_repository.delete_treatment_action(db, uuid.UUID(action_id))
        if not result:
            raise HTTPException(status_code=404, detail="Treatment action not found")
        return {"message": "Treatment action deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting treatment action: {str(e)}"
        )
