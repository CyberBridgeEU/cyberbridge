# routers/audit_dashboard_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.database.database import get_db
from app.services import change_radar_service, audit_dashboard_service
from app.repositories import audit_engagement_repository

router = APIRouter(prefix="/audit-engagements", tags=["Audit Dashboard"])


# ===========================
# Dashboard Endpoints
# ===========================

@router.get("/{engagement_id}/dashboard")
def get_engagement_dashboard(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for an audit engagement.
    Includes summary, findings, comments, progress, and activity.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return audit_dashboard_service.get_engagement_dashboard(db, engagement_id)


@router.get("/{engagement_id}/dashboard/findings")
def get_findings_summary(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get findings summary by severity and status.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return audit_dashboard_service.get_findings_by_severity(db, engagement_id)


@router.get("/{engagement_id}/dashboard/comments")
def get_comments_summary(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get comments summary by type and status.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return audit_dashboard_service.get_comments_summary(db, engagement_id)


@router.get("/{engagement_id}/dashboard/progress")
def get_review_progress(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get review progress for the engagement.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return audit_dashboard_service.get_review_progress(db, engagement)


@router.get("/{engagement_id}/dashboard/sign-offs")
def get_sign_off_status(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get sign-off status summary.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return audit_dashboard_service.get_sign_off_status(db, engagement_id)


# ===========================
# Change Radar Endpoints
# ===========================

@router.get("/{engagement_id}/change-radar")
def get_change_radar(
    engagement_id: uuid.UUID,
    prior_engagement_id: uuid.UUID = Query(None, description="ID of prior engagement to compare against"),
    db: Session = Depends(get_db)
):
    """
    Get change radar comparison between current and prior engagement.
    If prior_engagement_id not provided, uses the linked prior_engagement_id from the current engagement.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    # Use linked prior engagement if not specified
    if not prior_engagement_id:
        prior_engagement_id = engagement.prior_engagement_id

    if not prior_engagement_id:
        raise HTTPException(
            status_code=400,
            detail="No prior engagement specified and current engagement has no linked prior engagement"
        )

    # Verify prior engagement exists
    prior = audit_engagement_repository.get_engagement(db, prior_engagement_id)
    if not prior:
        raise HTTPException(status_code=404, detail="Prior engagement not found")

    return change_radar_service.compare_engagements(db, engagement_id, prior_engagement_id)


@router.get("/{engagement_id}/change-radar/history")
def get_engagement_history(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get the complete history chain of engagements linked through prior_engagement_id.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return change_radar_service.get_engagement_history(db, engagement_id)


@router.get("/{engagement_id}/change-radar/timeline")
def get_change_timeline(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get a timeline of changes across all engagement history.
    Compares each consecutive pair of engagements.
    """
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return change_radar_service.get_change_timeline(db, engagement_id)


# ===========================
# Organization Summary
# ===========================

@router.get("/organization/{organisation_id}/summary")
def get_organization_audit_summary(
    organisation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get audit summary for an entire organization.
    Includes total engagements, status breakdown, and aggregate metrics.
    """
    return audit_dashboard_service.get_organization_audit_summary(db, organisation_id)
