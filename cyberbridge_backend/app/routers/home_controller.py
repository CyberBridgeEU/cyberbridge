from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from ..repositories import home_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user

# Create router with prefix and tags
router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)

# Endpoint for dashboard metrics
@router.get("/metrics", response_model=Dict[str, int])
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get dashboard metrics including total assessments, completed assessments, and compliance frameworks.
    """
    try:
        metrics = home_repository.get_dashboard_metrics(db, current_user)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching dashboard metrics: {str(e)}"
        )

# Endpoint for pie chart data
@router.get("/pie-chart-data", response_model=Dict[str, int])
def get_pie_chart_data(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get pie chart data showing the count of in-progress and completed assessments.
    """
    try:
        pie_chart_data = home_repository.get_pie_chart_data(db, current_user)
        return pie_chart_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching pie chart data: {str(e)}"
        )

# Endpoint for frameworks
@router.get("/frameworks", response_model=List[Dict[str, Any]])
def get_frameworks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get frameworks for the dashboard.
    """
    try:
        frameworks = home_repository.get_dashboard_frameworks(db, current_user, skip, limit)
        return frameworks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching frameworks: {str(e)}"
        )

# Endpoint for assessments
@router.get("/assessments", response_model=List[Dict[str, Any]])
def get_assessments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get assessments for the dashboard.
    """
    try:
        assessments = home_repository.get_dashboard_assessments(db, current_user, skip, limit)
        return assessments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching assessments: {str(e)}"
        )

# Endpoint for user analytics
@router.get("/user-analytics", response_model=Dict[str, Any])
def get_user_analytics(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get user analytics including registration trends, role distribution, and status distribution.
    """
    try:
        print(f"🔍 DEBUG: get_user_analytics endpoint called with user: {current_user.email}")
        analytics = home_repository.get_user_analytics(db, current_user)
        print(f"✅ DEBUG: get_user_analytics completed successfully")
        return analytics
    except Exception as e:
        print(f"❌ DEBUG: Exception in get_user_analytics: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ DEBUG: Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching user analytics: {str(e)}"
        )

# Endpoint for assessment analytics
@router.get("/assessment-analytics", response_model=Dict[str, Any])
def get_assessment_analytics(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get assessment analytics including trends, framework completion, and types distribution.
    """
    try:
        analytics = home_repository.get_assessment_analytics(db, current_user)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching assessment analytics: {str(e)}"
        )

# Endpoint for policy risk analytics
@router.get("/policy-risk-analytics", response_model=Dict[str, Any])
def get_policy_risk_analytics(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get policy and risk analytics including status distributions and product types.
    """
    try:
        print(f"🔍 DEBUG: get_policy_risk_analytics endpoint called with user: {current_user.email}")
        analytics = home_repository.get_policy_risk_analytics(db, current_user)
        print(f"✅ DEBUG: get_policy_risk_analytics completed successfully")
        return analytics
    except Exception as e:
        print(f"❌ DEBUG: Exception in get_policy_risk_analytics: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ DEBUG: Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching policy risk analytics: {str(e)}"
        )

# Endpoint for assessment funnel analytics
@router.get("/assessment-funnel", response_model=Dict[str, Any])
def get_assessment_funnel_analytics(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get assessment completion funnel data showing user drop-off at different stages.
    """
    try:
        print(f"🔍 DEBUG: get_assessment_funnel_analytics endpoint called with user: {current_user.email}")
        analytics = home_repository.get_assessment_funnel_analytics(db, current_user)
        print(f"✅ DEBUG: get_assessment_funnel_analytics completed successfully")
        return analytics
    except Exception as e:
        print(f"❌ DEBUG: Exception in get_assessment_funnel_analytics: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ DEBUG: Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching assessment funnel analytics: {str(e)}"
        )

# Endpoint for CRA DoC readiness metrics
@router.get("/cra-doc-readiness", response_model=Dict[str, Any])
def get_cra_doc_readiness(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get CRA Declaration of Conformity readiness metrics including objective compliance
    and assessment completion rates.
    """
    try:
        readiness = home_repository.get_cra_doc_readiness(db, current_user)
        return readiness
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching CRA DoC readiness: {str(e)}"
        )