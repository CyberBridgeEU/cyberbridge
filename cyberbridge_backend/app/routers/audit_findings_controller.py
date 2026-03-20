# routers/audit_findings_controller.py
"""
Controller for audit findings and sign-offs.
Handles CRUD operations for audit findings and sign-off workflows.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import logging
from datetime import datetime

from ..database.database import get_db
from ..dtos import schemas
from ..repositories import audit_finding_repository, audit_engagement_repository
from ..services import auth_service, auditor_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/audit-engagements",
    tags=["audit-findings"],
    responses={404: {"description": "Not found"}}
)


# ===========================
# Finding Endpoints
# ===========================

@router.get("/{engagement_id}/findings", response_model=schemas.AuditFindingListResponse)
def get_engagement_findings(
    engagement_id: uuid.UUID,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Get all findings for an audit engagement with optional filters.
    """
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    if str(engagement.organisation_id) != current_user.get("organisation_id") and current_user.get("role_name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    findings = audit_finding_repository.get_findings_for_engagement(
        db, engagement_id, severity, category, status_filter, skip, limit
    )

    total_count = audit_finding_repository.get_finding_count_for_engagement(db, engagement_id)

    return schemas.AuditFindingListResponse(
        findings=[_finding_to_response(f) for f in findings],
        total_count=total_count
    )


@router.get("/{engagement_id}/findings/stats")
def get_findings_statistics(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Get findings statistics for an engagement.
    """
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    if str(engagement.organisation_id) != current_user.get("organisation_id") and current_user.get("role_name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    total_count = audit_finding_repository.get_finding_count_for_engagement(db, engagement_id)
    by_severity = audit_finding_repository.get_findings_by_severity(db, engagement_id)

    return {
        "total_findings": total_count,
        "by_severity": by_severity
    }


@router.get("/{engagement_id}/findings/{finding_id}", response_model=schemas.AuditFindingResponse)
def get_finding(
    engagement_id: uuid.UUID,
    finding_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Get a specific finding.
    """
    finding = audit_finding_repository.get_finding(db, finding_id)

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )

    if finding.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding does not belong to this engagement"
        )

    # Verify user has access to the engagement
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if str(engagement.organisation_id) != current_user.get("organisation_id") and current_user.get("role_name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    return _finding_to_response(finding)


@router.post("/{engagement_id}/findings", response_model=schemas.AuditFindingResponse, status_code=status.HTTP_201_CREATED)
def create_finding(
    engagement_id: uuid.UUID,
    request: schemas.AuditFindingCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Create a new finding for an audit engagement.
    """
    # Verify engagement exists
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    if str(engagement.organisation_id) != current_user.get("organisation_id") and current_user.get("role_name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    # Validate severity
    valid_severities = ["low", "medium", "high", "critical"]
    if request.severity not in valid_severities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid severity. Must be one of: {valid_severities}"
        )

    # Validate category
    valid_categories = ["control_deficiency", "documentation_gap", "compliance_issue", "process_weakness"]
    if request.category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {valid_categories}"
        )

    finding = audit_finding_repository.create_finding(
        db=db,
        engagement_id=engagement_id,
        title=request.title,
        description=request.description,
        severity=request.severity,
        category=request.category,
        related_controls=request.related_controls,
        related_evidence=request.related_evidence,
        remediation_plan=request.remediation_plan,
        remediation_owner_id=request.remediation_owner_id,
        remediation_due_date=request.remediation_due_date,
        author_user_id=uuid.UUID(current_user.get("user_id"))
    )

    # Log activity
    audit_finding_repository.create_activity_log(
        db=db,
        engagement_id=engagement_id,
        action="created_finding",
        user_id=uuid.UUID(current_user.get("user_id")),
        target_type="finding",
        target_id=finding.id,
        details={"title": request.title, "severity": request.severity}
    )

    return _finding_to_response(finding)


@router.put("/{engagement_id}/findings/{finding_id}", response_model=schemas.AuditFindingResponse)
def update_finding(
    engagement_id: uuid.UUID,
    finding_id: uuid.UUID,
    request: schemas.AuditFindingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Update an audit finding.
    """
    finding = audit_finding_repository.get_finding(db, finding_id)

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )

    if finding.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding does not belong to this engagement"
        )

    # Validate severity if provided
    if request.severity:
        valid_severities = ["low", "medium", "high", "critical"]
        if request.severity not in valid_severities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity. Must be one of: {valid_severities}"
            )

    # Validate category if provided
    if request.category:
        valid_categories = ["control_deficiency", "documentation_gap", "compliance_issue", "process_weakness"]
        if request.category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )

    updated_finding = audit_finding_repository.update_finding(
        db=db,
        finding_id=finding_id,
        title=request.title,
        description=request.description,
        severity=request.severity,
        category=request.category,
        related_controls=request.related_controls,
        related_evidence=request.related_evidence,
        remediation_plan=request.remediation_plan,
        remediation_owner_id=request.remediation_owner_id,
        remediation_due_date=request.remediation_due_date
    )

    return _finding_to_response(updated_finding)


@router.patch("/{engagement_id}/findings/{finding_id}/status", response_model=schemas.AuditFindingResponse)
def update_finding_status(
    engagement_id: uuid.UUID,
    finding_id: uuid.UUID,
    request: schemas.AuditFindingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Update finding status.
    """
    valid_statuses = ["draft", "confirmed", "remediation_in_progress", "remediated", "accepted", "closed"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    finding = audit_finding_repository.get_finding(db, finding_id)

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )

    if finding.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding does not belong to this engagement"
        )

    updated_finding = audit_finding_repository.update_finding_status(
        db, finding_id, request.status
    )

    # Log activity
    audit_finding_repository.create_activity_log(
        db=db,
        engagement_id=engagement_id,
        action="updated_finding_status",
        user_id=uuid.UUID(current_user.get("user_id")),
        target_type="finding",
        target_id=finding_id,
        details={"new_status": request.status}
    )

    return _finding_to_response(updated_finding)


@router.delete("/{engagement_id}/findings/{finding_id}")
def delete_finding(
    engagement_id: uuid.UUID,
    finding_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Delete an audit finding.
    """
    finding = audit_finding_repository.get_finding(db, finding_id)

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )

    if finding.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding does not belong to this engagement"
        )

    # Only admins can delete findings
    if current_user.get("role_name") not in ["super_admin", "org_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete findings"
        )

    success = audit_finding_repository.delete_finding(db, finding_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete finding"
        )

    return {"success": True, "message": "Finding deleted successfully"}


# ===========================
# Sign-Off Endpoints
# ===========================

@router.get("/{engagement_id}/sign-offs", response_model=schemas.AuditSignOffListResponse)
def get_engagement_sign_offs(
    engagement_id: uuid.UUID,
    sign_off_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Get all sign-offs for an audit engagement.
    """
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    if str(engagement.organisation_id) != current_user.get("organisation_id") and current_user.get("role_name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    sign_offs = audit_finding_repository.get_sign_offs_for_engagement(
        db, engagement_id, sign_off_type, status_filter, skip, limit
    )

    total_count = audit_finding_repository.get_sign_off_count_for_engagement(db, engagement_id)

    return schemas.AuditSignOffListResponse(
        sign_offs=[_sign_off_to_response(s) for s in sign_offs],
        total_count=total_count
    )


@router.post("/{engagement_id}/sign-offs", response_model=schemas.AuditSignOffResponse, status_code=status.HTTP_201_CREATED)
def create_sign_off(
    engagement_id: uuid.UUID,
    request: schemas.AuditSignOffCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Create a sign-off (internal user on behalf of auditor).
    For auditor self-sign-off, use the auditor review endpoints.
    """
    # Verify engagement exists
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    if str(engagement.organisation_id) != current_user.get("organisation_id") and current_user.get("role_name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    # Validate sign_off_type
    valid_types = ["control", "section", "engagement"]
    if request.sign_off_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sign_off_type. Must be one of: {valid_types}"
        )

    # Validate status
    valid_statuses = ["approved", "approved_with_exceptions", "rejected"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    # For now, internal users cannot create sign-offs directly
    # This endpoint is reserved for future use when internal users can sign on behalf of auditors
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sign-offs must be created by auditors through the review portal"
    )


# ===========================
# Activity Log Endpoints
# ===========================

@router.get("/{engagement_id}/activity-logs", response_model=schemas.AuditActivityLogListResponse)
def get_activity_logs(
    engagement_id: uuid.UUID,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    Get activity logs for an audit engagement.
    """
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    if str(engagement.organisation_id) != current_user.get("organisation_id") and current_user.get("role_name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    logs = audit_finding_repository.get_activity_logs_for_engagement(
        db, engagement_id, action, skip, limit
    )

    return schemas.AuditActivityLogListResponse(
        logs=[_activity_log_to_response(l) for l in logs],
        total_count=len(logs)
    )


# ===========================
# Helper Functions
# ===========================

def _finding_to_response(finding) -> schemas.AuditFindingResponse:
    """Convert a finding model to response schema."""
    return schemas.AuditFindingResponse(
        id=finding.id,
        engagement_id=finding.engagement_id,
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
        category=finding.category,
        related_controls=finding.related_controls,
        related_evidence=finding.related_evidence,
        remediation_plan=finding.remediation_plan,
        remediation_owner_id=finding.remediation_owner_id,
        remediation_due_date=finding.remediation_due_date,
        status=finding.status,
        author_user_id=finding.author_user_id,
        author_auditor_id=finding.author_auditor_id,
        created_at=finding.created_at,
        updated_at=finding.updated_at,
        author_name=getattr(finding, 'author_name', None),
        remediation_owner_name=getattr(finding, 'remediation_owner_name', None)
    )


def _sign_off_to_response(sign_off) -> schemas.AuditSignOffResponse:
    """Convert a sign-off model to response schema."""
    return schemas.AuditSignOffResponse(
        id=sign_off.id,
        engagement_id=sign_off.engagement_id,
        sign_off_type=sign_off.sign_off_type,
        target_id=sign_off.target_id,
        status=sign_off.status,
        comments=sign_off.comments,
        signer_auditor_id=sign_off.signer_auditor_id,
        signed_at=sign_off.signed_at,
        ip_address=sign_off.ip_address,
        created_at=sign_off.created_at,
        signer_name=getattr(sign_off, 'signer_name', None),
        signer_email=getattr(sign_off, 'signer_email', None)
    )


def _activity_log_to_response(log) -> schemas.AuditActivityLogResponse:
    """Convert an activity log model to response schema."""
    return schemas.AuditActivityLogResponse(
        id=log.id,
        engagement_id=log.engagement_id,
        user_id=log.user_id,
        auditor_id=log.auditor_id,
        action=log.action,
        target_type=log.target_type,
        target_id=log.target_id,
        details=log.details,
        ip_address=log.ip_address,
        created_at=log.created_at,
        actor_name=getattr(log, 'actor_name', None),
        actor_type=getattr(log, 'actor_type', None)
    )
