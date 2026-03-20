# routers/audit_notifications_controller.py
"""
Controller for audit notifications and control review status.
Handles endpoints for notification management and review workflow.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import logging

from ..database.database import get_db
from ..dtos import schemas
from ..models import models
from ..repositories import audit_notification_repository, audit_engagement_repository
from ..services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/audit",
    tags=["audit-notifications"],
    responses={404: {"description": "Not found"}}
)


# ===========================
# Notification Endpoints for Users
# ===========================

@router.get("/notifications", response_model=schemas.AuditNotificationListResponse)
def get_user_notifications(
    engagement_id: Optional[uuid.UUID] = None,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """Get notifications for the current user."""
    notifications = audit_notification_repository.get_notifications_for_user(
        db=db,
        user_id=current_user.id,
        engagement_id=engagement_id,
        unread_only=unread_only,
        skip=skip,
        limit=limit
    )

    unread_count = audit_notification_repository.get_unread_count_for_user(
        db=db,
        user_id=current_user.id,
        engagement_id=engagement_id
    )

    # Enrich notifications with sender names
    notification_responses = []
    for n in notifications:
        sender_name = None
        if n.sender_user_id:
            sender = db.query(models.User).filter(models.User.id == n.sender_user_id).first()
            sender_name = sender.name if sender else None
        elif n.sender_auditor_id:
            auditor = db.query(models.AuditorInvitation).filter(models.AuditorInvitation.id == n.sender_auditor_id).first()
            sender_name = auditor.name if auditor else "Auditor"

        notification_responses.append(schemas.AuditNotificationResponse(
            id=n.id,
            engagement_id=n.engagement_id,
            notification_type=n.notification_type,
            source_type=n.source_type,
            source_id=n.source_id,
            related_answer_id=n.related_answer_id,
            title=n.title,
            message=n.message,
            sender_user_id=n.sender_user_id,
            sender_auditor_id=n.sender_auditor_id,
            sender_name=sender_name,
            is_read=n.is_read,
            read_at=n.read_at,
            created_at=n.created_at
        ))

    return schemas.AuditNotificationListResponse(
        notifications=notification_responses,
        unread_count=unread_count,
        total_count=len(notification_responses)
    )


@router.get("/notifications/count")
def get_user_unread_count(
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """Get unread notification count for the current user."""
    count = audit_notification_repository.get_unread_count_for_user(
        db=db,
        user_id=current_user.id,
        engagement_id=engagement_id
    )
    return {"unread_count": count}


@router.post("/notifications/mark-read")
def mark_notifications_read(
    request: schemas.MarkNotificationsReadRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """Mark notifications as read."""
    if request.notification_ids:
        # Mark specific notifications as read
        count = 0
        for notification_id in request.notification_ids:
            notification = audit_notification_repository.mark_notification_as_read(db, notification_id)
            if notification and notification.recipient_user_id == current_user.id:
                count += 1
        return {"success": True, "marked_read": count}
    else:
        # Mark all as read
        count = audit_notification_repository.mark_all_notifications_as_read_for_user(
            db=db,
            user_id=current_user.id,
            engagement_id=request.engagement_id
        )
        return {"success": True, "marked_read": count}


@router.delete("/notifications/{notification_id}")
def delete_notification(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """Delete a notification."""
    # Verify the notification belongs to the user
    notification = db.query(models.AuditNotification).filter(
        models.AuditNotification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    if notification.recipient_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notifications"
        )

    audit_notification_repository.delete_notification(db, notification_id)
    return {"success": True, "message": "Notification deleted"}


# ===========================
# Control Review Status Endpoints
# ===========================

@router.get("/engagements/{engagement_id}/review-status", response_model=schemas.ReviewStatusCountsResponse)
def get_review_status_summary(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """Get summary of review statuses for an engagement."""
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    # Check user has access
    user_org_id = str(current_user.organisation_id) if current_user.organisation_id else None
    user_role = None
    if current_user.role_id:
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        user_role = role.role_name if role else None

    if str(engagement.organisation_id) != user_org_id and user_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    counts = audit_notification_repository.get_review_status_counts(db, engagement_id)
    return schemas.ReviewStatusCountsResponse(**counts)


@router.get("/engagements/{engagement_id}/controls/{answer_id}/review-status", response_model=schemas.ControlReviewStatusResponse)
def get_control_review_status(
    engagement_id: uuid.UUID,
    answer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """Get the review status for a specific control."""
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    # Check user has access
    user_org_id = str(current_user.organisation_id) if current_user.organisation_id else None
    user_role = None
    if current_user.role_id:
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        user_role = role.role_name if role else None

    if str(engagement.organisation_id) != user_org_id and user_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    status_record = audit_notification_repository.get_or_create_review_status(db, engagement_id, answer_id)

    # Get last updated by name
    last_updated_by_name = None
    if status_record.last_updated_by_user_id:
        user = db.query(models.User).filter(models.User.id == status_record.last_updated_by_user_id).first()
        last_updated_by_name = user.name if user else None
    elif status_record.last_updated_by_auditor_id:
        auditor = db.query(models.AuditorInvitation).filter(models.AuditorInvitation.id == status_record.last_updated_by_auditor_id).first()
        last_updated_by_name = auditor.name if auditor else "Auditor"

    return schemas.ControlReviewStatusResponse(
        id=status_record.id,
        engagement_id=status_record.engagement_id,
        answer_id=status_record.answer_id,
        status=status_record.status,
        status_note=status_record.status_note,
        last_updated_by_user_id=status_record.last_updated_by_user_id,
        last_updated_by_auditor_id=status_record.last_updated_by_auditor_id,
        last_updated_by_name=last_updated_by_name,
        created_at=status_record.created_at,
        updated_at=status_record.updated_at
    )


@router.put("/engagements/{engagement_id}/controls/{answer_id}/review-status", response_model=schemas.ControlReviewStatusResponse)
def update_control_review_status(
    engagement_id: uuid.UUID,
    answer_id: uuid.UUID,
    request: schemas.ControlReviewStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """Update the review status for a control."""
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    # Check user has access
    user_org_id = str(current_user.organisation_id) if current_user.organisation_id else None
    user_role = None
    if current_user.role_id:
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        user_role = role.role_name if role else None

    if str(engagement.organisation_id) != user_org_id and user_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    # Validate status
    valid_statuses = [
        "not_started", "pending_review", "information_requested", "response_provided",
        "in_review", "approved", "approved_with_exceptions", "needs_remediation"
    ]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    # Get old status for notification
    old_status_record = audit_notification_repository.get_review_status(db, engagement_id, answer_id)
    old_status = old_status_record.status if old_status_record else "not_started"

    # Update status
    status_record = audit_notification_repository.update_review_status(
        db=db,
        engagement_id=engagement_id,
        answer_id=answer_id,
        new_status=request.status,
        updated_by_user_id=current_user.id,
        status_note=request.status_note
    )

    # Create notification for status change if status actually changed
    if old_status != request.status:
        audit_notification_repository.notify_status_change(
            db=db,
            engagement=engagement,
            answer_id=answer_id,
            old_status=old_status,
            new_status=request.status,
            changed_by_user_id=current_user.id,
            changer_name=current_user.name
        )

    return schemas.ControlReviewStatusResponse(
        id=status_record.id,
        engagement_id=status_record.engagement_id,
        answer_id=status_record.answer_id,
        status=status_record.status,
        status_note=status_record.status_note,
        last_updated_by_user_id=status_record.last_updated_by_user_id,
        last_updated_by_auditor_id=status_record.last_updated_by_auditor_id,
        last_updated_by_name=current_user.name,
        created_at=status_record.created_at,
        updated_at=status_record.updated_at
    )
