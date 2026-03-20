# repositories/audit_notification_repository.py
"""
Repository for audit notifications and control review status.
Handles CRUD operations for tracking review workflow and notifications.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List
import uuid
from datetime import datetime

from ..models import models


# ===========================
# Control Review Status Functions
# ===========================

def get_review_status(
    db: Session,
    engagement_id: uuid.UUID,
    answer_id: uuid.UUID
) -> Optional[models.ControlReviewStatus]:
    """Get the review status for a specific control in an engagement."""
    return db.query(models.ControlReviewStatus).filter(
        models.ControlReviewStatus.engagement_id == engagement_id,
        models.ControlReviewStatus.answer_id == answer_id
    ).first()


def get_or_create_review_status(
    db: Session,
    engagement_id: uuid.UUID,
    answer_id: uuid.UUID
) -> models.ControlReviewStatus:
    """Get or create a review status record for a control."""
    status = get_review_status(db, engagement_id, answer_id)
    if not status:
        status = models.ControlReviewStatus(
            engagement_id=engagement_id,
            answer_id=answer_id,
            status="not_started"
        )
        db.add(status)
        db.commit()
        db.refresh(status)
    return status


def update_review_status(
    db: Session,
    engagement_id: uuid.UUID,
    answer_id: uuid.UUID,
    new_status: str,
    updated_by_user_id: Optional[uuid.UUID] = None,
    updated_by_auditor_id: Optional[uuid.UUID] = None,
    status_note: Optional[str] = None
) -> models.ControlReviewStatus:
    """Update the review status for a control."""
    status = get_or_create_review_status(db, engagement_id, answer_id)

    status.status = new_status
    status.last_updated_by_user_id = updated_by_user_id
    status.last_updated_by_auditor_id = updated_by_auditor_id
    if status_note:
        status.status_note = status_note
    status.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(status)
    return status


def get_all_review_statuses_for_engagement(
    db: Session,
    engagement_id: uuid.UUID
) -> List[models.ControlReviewStatus]:
    """Get all review statuses for an engagement."""
    return db.query(models.ControlReviewStatus).filter(
        models.ControlReviewStatus.engagement_id == engagement_id
    ).all()


def get_review_status_counts(
    db: Session,
    engagement_id: uuid.UUID
) -> dict:
    """Get counts of each review status for an engagement."""
    results = db.query(
        models.ControlReviewStatus.status,
        func.count(models.ControlReviewStatus.id)
    ).filter(
        models.ControlReviewStatus.engagement_id == engagement_id
    ).group_by(models.ControlReviewStatus.status).all()

    counts = {
        "not_started": 0,
        "pending_review": 0,
        "information_requested": 0,
        "response_provided": 0,
        "in_review": 0,
        "approved": 0,
        "approved_with_exceptions": 0,
        "needs_remediation": 0
    }
    for status, count in results:
        counts[status] = count

    return counts


# ===========================
# Notification Functions
# ===========================

def create_notification(
    db: Session,
    engagement_id: uuid.UUID,
    notification_type: str,
    source_type: str,
    source_id: uuid.UUID,
    title: str,
    message: Optional[str] = None,
    recipient_user_id: Optional[uuid.UUID] = None,
    recipient_auditor_id: Optional[uuid.UUID] = None,
    sender_user_id: Optional[uuid.UUID] = None,
    sender_auditor_id: Optional[uuid.UUID] = None,
    related_answer_id: Optional[uuid.UUID] = None
) -> models.AuditNotification:
    """Create a new notification."""
    notification = models.AuditNotification(
        engagement_id=engagement_id,
        notification_type=notification_type,
        source_type=source_type,
        source_id=source_id,
        title=title,
        message=message,
        recipient_user_id=recipient_user_id,
        recipient_auditor_id=recipient_auditor_id,
        sender_user_id=sender_user_id,
        sender_auditor_id=sender_auditor_id,
        related_answer_id=related_answer_id,
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications_for_user(
    db: Session,
    user_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50
) -> List[models.AuditNotification]:
    """Get notifications for a user."""
    query = db.query(models.AuditNotification).filter(
        models.AuditNotification.recipient_user_id == user_id
    )

    if engagement_id:
        query = query.filter(models.AuditNotification.engagement_id == engagement_id)

    if unread_only:
        query = query.filter(models.AuditNotification.is_read == False)

    return query.order_by(desc(models.AuditNotification.created_at)).offset(skip).limit(limit).all()


def get_notifications_for_auditor(
    db: Session,
    auditor_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50
) -> List[models.AuditNotification]:
    """Get notifications for an auditor."""
    query = db.query(models.AuditNotification).filter(
        models.AuditNotification.recipient_auditor_id == auditor_id
    )

    if engagement_id:
        query = query.filter(models.AuditNotification.engagement_id == engagement_id)

    if unread_only:
        query = query.filter(models.AuditNotification.is_read == False)

    return query.order_by(desc(models.AuditNotification.created_at)).offset(skip).limit(limit).all()


def get_unread_count_for_user(
    db: Session,
    user_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None
) -> int:
    """Get count of unread notifications for a user."""
    query = db.query(func.count(models.AuditNotification.id)).filter(
        models.AuditNotification.recipient_user_id == user_id,
        models.AuditNotification.is_read == False
    )

    if engagement_id:
        query = query.filter(models.AuditNotification.engagement_id == engagement_id)

    return query.scalar() or 0


def get_unread_count_for_auditor(
    db: Session,
    auditor_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None
) -> int:
    """Get count of unread notifications for an auditor."""
    query = db.query(func.count(models.AuditNotification.id)).filter(
        models.AuditNotification.recipient_auditor_id == auditor_id,
        models.AuditNotification.is_read == False
    )

    if engagement_id:
        query = query.filter(models.AuditNotification.engagement_id == engagement_id)

    return query.scalar() or 0


def mark_notification_as_read(
    db: Session,
    notification_id: uuid.UUID
) -> Optional[models.AuditNotification]:
    """Mark a notification as read."""
    notification = db.query(models.AuditNotification).filter(
        models.AuditNotification.id == notification_id
    ).first()

    if notification:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)

    return notification


def mark_all_notifications_as_read_for_user(
    db: Session,
    user_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None
) -> int:
    """Mark all notifications as read for a user. Returns count of updated notifications."""
    query = db.query(models.AuditNotification).filter(
        models.AuditNotification.recipient_user_id == user_id,
        models.AuditNotification.is_read == False
    )

    if engagement_id:
        query = query.filter(models.AuditNotification.engagement_id == engagement_id)

    count = query.update({
        models.AuditNotification.is_read: True,
        models.AuditNotification.read_at: datetime.utcnow()
    }, synchronize_session=False)

    db.commit()
    return count


def mark_all_notifications_as_read_for_auditor(
    db: Session,
    auditor_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None
) -> int:
    """Mark all notifications as read for an auditor. Returns count of updated notifications."""
    query = db.query(models.AuditNotification).filter(
        models.AuditNotification.recipient_auditor_id == auditor_id,
        models.AuditNotification.is_read == False
    )

    if engagement_id:
        query = query.filter(models.AuditNotification.engagement_id == engagement_id)

    count = query.update({
        models.AuditNotification.is_read: True,
        models.AuditNotification.read_at: datetime.utcnow()
    }, synchronize_session=False)

    db.commit()
    return count


def delete_notification(
    db: Session,
    notification_id: uuid.UUID
) -> bool:
    """Delete a notification."""
    notification = db.query(models.AuditNotification).filter(
        models.AuditNotification.id == notification_id
    ).first()

    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False


# ===========================
# Helper Functions for Creating Notifications
# ===========================

def notify_users_of_new_comment(
    db: Session,
    comment: models.AuditComment,
    engagement: models.AuditEngagement,
    sender_name: str
):
    """
    Create notifications for relevant users when a new comment is posted.
    - If auditor posts: notify the engagement owner and assigned user
    - If user posts: notify all auditors on the engagement
    """
    # Determine sender type
    is_auditor_comment = comment.author_auditor_id is not None

    if is_auditor_comment:
        # Auditor posted - notify the engagement owner
        create_notification(
            db=db,
            engagement_id=engagement.id,
            notification_type="new_comment",
            source_type="comment",
            source_id=comment.id,
            title=f"New comment from auditor",
            message=f"{sender_name} left a comment on a control",
            recipient_user_id=engagement.owner_id,
            sender_auditor_id=comment.author_auditor_id,
            related_answer_id=comment.target_id if comment.target_type == "answer" else None
        )

        # Also notify assigned user if different from owner
        if comment.assigned_to_id and comment.assigned_to_id != engagement.owner_id:
            create_notification(
                db=db,
                engagement_id=engagement.id,
                notification_type="new_comment",
                source_type="comment",
                source_id=comment.id,
                title=f"New comment from auditor",
                message=f"{sender_name} left a comment that is assigned to you",
                recipient_user_id=comment.assigned_to_id,
                sender_auditor_id=comment.author_auditor_id,
                related_answer_id=comment.target_id if comment.target_type == "answer" else None
            )
    else:
        # User posted - notify all auditors on the engagement
        auditor_invitations = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.engagement_id == engagement.id,
            models.AuditorInvitation.status == "accepted"
        ).all()

        for invitation in auditor_invitations:
            create_notification(
                db=db,
                engagement_id=engagement.id,
                notification_type="comment_reply" if comment.parent_comment_id else "new_comment",
                source_type="comment",
                source_id=comment.id,
                title=f"Response from {sender_name}",
                message=f"{sender_name} responded to your comment" if comment.parent_comment_id else f"{sender_name} left a comment",
                recipient_auditor_id=invitation.id,
                sender_user_id=comment.author_user_id,
                related_answer_id=comment.target_id if comment.target_type == "answer" else None
            )


def notify_status_change(
    db: Session,
    engagement: models.AuditEngagement,
    answer_id: uuid.UUID,
    old_status: str,
    new_status: str,
    changed_by_user_id: Optional[uuid.UUID] = None,
    changed_by_auditor_id: Optional[uuid.UUID] = None,
    changer_name: str = "Someone"
):
    """
    Create notifications when a control's review status changes.
    """
    # Map status to human-readable text
    status_labels = {
        "not_started": "Not Started",
        "pending_review": "Pending Review",
        "information_requested": "Information Requested",
        "response_provided": "Response Provided",
        "in_review": "In Review",
        "approved": "Approved",
        "approved_with_exceptions": "Approved with Exceptions",
        "needs_remediation": "Needs Remediation"
    }

    new_status_label = status_labels.get(new_status, new_status)

    if changed_by_auditor_id:
        # Auditor changed status - notify engagement owner
        create_notification(
            db=db,
            engagement_id=engagement.id,
            notification_type="status_change",
            source_type="control",
            source_id=answer_id,
            title=f"Control status: {new_status_label}",
            message=f"{changer_name} changed a control status to {new_status_label}",
            recipient_user_id=engagement.owner_id,
            sender_auditor_id=changed_by_auditor_id,
            related_answer_id=answer_id
        )
    else:
        # User changed status - notify all auditors
        auditor_invitations = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.engagement_id == engagement.id,
            models.AuditorInvitation.status == "accepted"
        ).all()

        for invitation in auditor_invitations:
            create_notification(
                db=db,
                engagement_id=engagement.id,
                notification_type="status_change",
                source_type="control",
                source_id=answer_id,
                title=f"Control status: {new_status_label}",
                message=f"{changer_name} changed a control status to {new_status_label}",
                recipient_auditor_id=invitation.id,
                sender_user_id=changed_by_user_id,
                related_answer_id=answer_id
            )
