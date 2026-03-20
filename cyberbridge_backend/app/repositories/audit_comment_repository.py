# repositories/audit_comment_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import uuid
from typing import Optional, List
from datetime import datetime

from app.models import models


# ===========================
# Audit Comment CRUD Operations
# ===========================

def get_comment(db: Session, comment_id: uuid.UUID):
    """Get a single audit comment by ID"""
    comment = db.query(models.AuditComment).filter(
        models.AuditComment.id == comment_id
    ).first()

    if comment:
        _enrich_comment(db, comment)

    return comment


def get_comments_for_engagement(
    db: Session,
    engagement_id: uuid.UUID,
    target_type: Optional[str] = None,
    target_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    comment_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all comments for an engagement with optional filters"""
    query = db.query(models.AuditComment).filter(
        models.AuditComment.engagement_id == engagement_id
    )

    if target_type:
        query = query.filter(models.AuditComment.target_type == target_type)

    if target_id:
        query = query.filter(models.AuditComment.target_id == target_id)

    if status:
        query = query.filter(models.AuditComment.status == status)

    if comment_type:
        query = query.filter(models.AuditComment.comment_type == comment_type)

    # Get root comments only (exclude replies)
    query = query.filter(models.AuditComment.parent_comment_id == None)

    comments = query.order_by(
        models.AuditComment.created_at.desc()
    ).offset(skip).limit(limit).all()

    # Enrich each comment and load replies
    for comment in comments:
        _enrich_comment(db, comment)
        # Load replies for each root comment
        comment.replies = db.query(models.AuditComment).filter(
            models.AuditComment.parent_comment_id == comment.id
        ).order_by(models.AuditComment.created_at.asc()).all()
        for reply in comment.replies:
            _enrich_comment(db, reply)

    return comments


def get_comment_thread(db: Session, comment_id: uuid.UUID):
    """Get a comment and all its replies (threaded)"""
    # Get the root comment
    root_comment = db.query(models.AuditComment).filter(
        models.AuditComment.id == comment_id
    ).first()

    if not root_comment:
        return None

    _enrich_comment(db, root_comment)

    # Get all replies
    replies = db.query(models.AuditComment).filter(
        models.AuditComment.parent_comment_id == comment_id
    ).order_by(models.AuditComment.created_at.asc()).all()

    for reply in replies:
        _enrich_comment(db, reply)

    root_comment.replies = replies
    return root_comment


def get_comments_for_target(
    db: Session,
    engagement_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID
):
    """Get all comments for a specific target (answer, evidence, etc.)"""
    comments = db.query(models.AuditComment).filter(
        and_(
            models.AuditComment.engagement_id == engagement_id,
            models.AuditComment.target_type == target_type,
            models.AuditComment.target_id == target_id,
            models.AuditComment.parent_comment_id == None  # Root comments only
        )
    ).order_by(models.AuditComment.created_at.desc()).all()

    for comment in comments:
        _enrich_comment(db, comment)
        # Load replies
        comment.replies = db.query(models.AuditComment).filter(
            models.AuditComment.parent_comment_id == comment.id
        ).order_by(models.AuditComment.created_at.asc()).all()
        for reply in comment.replies:
            _enrich_comment(db, reply)

    return comments


def create_comment(
    db: Session,
    engagement_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID,
    content: str,
    comment_type: str = "observation",
    author_user_id: Optional[uuid.UUID] = None,
    author_auditor_id: Optional[uuid.UUID] = None,
    parent_comment_id: Optional[uuid.UUID] = None,
    assigned_to_id: Optional[uuid.UUID] = None,
    assigned_to_auditor_id: Optional[uuid.UUID] = None,
    due_date: Optional[datetime] = None
):
    """Create a new audit comment"""
    comment = models.AuditComment(
        id=uuid.uuid4(),
        engagement_id=engagement_id,
        target_type=target_type,
        target_id=target_id,
        content=content,
        comment_type=comment_type,
        author_user_id=author_user_id,
        author_auditor_id=author_auditor_id,
        parent_comment_id=parent_comment_id,
        assigned_to_id=assigned_to_id,
        assigned_to_auditor_id=assigned_to_auditor_id,
        due_date=due_date,
        status="open"
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    _enrich_comment(db, comment)
    return comment


def update_comment(
    db: Session,
    comment_id: uuid.UUID,
    content: Optional[str] = None,
    comment_type: Optional[str] = None,
    assigned_to_id: Optional[uuid.UUID] = None,
    assigned_to_auditor_id: Optional[uuid.UUID] = None,
    due_date: Optional[datetime] = None
):
    """Update an audit comment"""
    comment = db.query(models.AuditComment).filter(
        models.AuditComment.id == comment_id
    ).first()

    if not comment:
        return None

    if content is not None:
        comment.content = content

    if comment_type is not None:
        comment.comment_type = comment_type

    if assigned_to_id is not None:
        comment.assigned_to_id = assigned_to_id

    if assigned_to_auditor_id is not None:
        comment.assigned_to_auditor_id = assigned_to_auditor_id

    if due_date is not None:
        comment.due_date = due_date

    db.commit()
    db.refresh(comment)

    _enrich_comment(db, comment)
    return comment


def update_comment_status(
    db: Session,
    comment_id: uuid.UUID,
    status: str
):
    """Update comment status"""
    comment = db.query(models.AuditComment).filter(
        models.AuditComment.id == comment_id
    ).first()

    if not comment:
        return None

    comment.status = status
    db.commit()
    db.refresh(comment)

    return comment


def resolve_comment(
    db: Session,
    comment_id: uuid.UUID,
    resolved_by_user_id: Optional[uuid.UUID] = None,
    resolved_by_auditor_id: Optional[uuid.UUID] = None,
    resolution_note: Optional[str] = None
):
    """Resolve a comment"""
    comment = db.query(models.AuditComment).filter(
        models.AuditComment.id == comment_id
    ).first()

    if not comment:
        return None

    comment.status = "resolved"
    comment.resolved_at = datetime.utcnow()
    comment.resolved_by_id = resolved_by_user_id
    comment.resolved_by_auditor_id = resolved_by_auditor_id
    comment.resolution_note = resolution_note

    db.commit()
    db.refresh(comment)

    _enrich_comment(db, comment)
    return comment


def delete_comment(db: Session, comment_id: uuid.UUID):
    """Delete an audit comment (and its replies via cascade)"""
    comment = db.query(models.AuditComment).filter(
        models.AuditComment.id == comment_id
    ).first()

    if not comment:
        return False

    db.delete(comment)
    db.commit()
    return True


def get_comment_count_for_engagement(db: Session, engagement_id: uuid.UUID):
    """Get count of comments for an engagement"""
    return db.query(func.count(models.AuditComment.id)).filter(
        models.AuditComment.engagement_id == engagement_id
    ).scalar()


def get_open_comment_count_for_engagement(db: Session, engagement_id: uuid.UUID):
    """Get count of open comments for an engagement"""
    return db.query(func.count(models.AuditComment.id)).filter(
        and_(
            models.AuditComment.engagement_id == engagement_id,
            models.AuditComment.status.in_(["open", "in_progress"])
        )
    ).scalar()


# ===========================
# Comment Attachment Operations
# ===========================

def get_comment_attachments(db: Session, comment_id: uuid.UUID):
    """Get all attachments for a comment"""
    return db.query(models.AuditCommentAttachment).filter(
        models.AuditCommentAttachment.comment_id == comment_id
    ).all()


def create_comment_attachment(
    db: Session,
    comment_id: uuid.UUID,
    filename: str,
    filepath: str,
    file_type: Optional[str] = None,
    file_size: Optional[int] = None,
    uploaded_by_user_id: Optional[uuid.UUID] = None,
    uploaded_by_auditor_id: Optional[uuid.UUID] = None
):
    """Create a comment attachment"""
    attachment = models.AuditCommentAttachment(
        id=uuid.uuid4(),
        comment_id=comment_id,
        filename=filename,
        filepath=filepath,
        file_type=file_type,
        file_size=file_size,
        uploaded_by_user_id=uploaded_by_user_id,
        uploaded_by_auditor_id=uploaded_by_auditor_id
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment


def delete_comment_attachment(db: Session, attachment_id: uuid.UUID):
    """Delete a comment attachment"""
    attachment = db.query(models.AuditCommentAttachment).filter(
        models.AuditCommentAttachment.id == attachment_id
    ).first()

    if not attachment:
        return False

    db.delete(attachment)
    db.commit()
    return True


# ===========================
# Helper Functions
# ===========================

def _enrich_comment(db: Session, comment):
    """Add computed properties to a comment"""
    # Get author name
    if comment.author_user_id:
        user = db.query(models.User).filter(models.User.id == comment.author_user_id).first()
        comment.author_name = user.name if user else None
        comment.author_type = "user"
    elif comment.author_auditor_id:
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == comment.author_auditor_id
        ).first()
        comment.author_name = invitation.name if invitation else invitation.email if invitation else None
        comment.author_type = "auditor"
    else:
        comment.author_name = None
        comment.author_type = None

    # Get assigned to name
    if comment.assigned_to_id:
        user = db.query(models.User).filter(models.User.id == comment.assigned_to_id).first()
        comment.assigned_to_name = user.name if user else None
    elif comment.assigned_to_auditor_id:
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == comment.assigned_to_auditor_id
        ).first()
        comment.assigned_to_name = invitation.name if invitation else invitation.email if invitation else None
    else:
        comment.assigned_to_name = None

    # Get resolved by name
    if comment.resolved_by_id:
        user = db.query(models.User).filter(models.User.id == comment.resolved_by_id).first()
        comment.resolved_by_name = user.name if user else None
    elif comment.resolved_by_auditor_id:
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == comment.resolved_by_auditor_id
        ).first()
        comment.resolved_by_name = invitation.name if invitation else invitation.email if invitation else None
    else:
        comment.resolved_by_name = None

    # Get reply count
    comment.reply_count = db.query(func.count(models.AuditComment.id)).filter(
        models.AuditComment.parent_comment_id == comment.id
    ).scalar()

    # Get attachment count
    comment.attachment_count = db.query(func.count(models.AuditCommentAttachment.id)).filter(
        models.AuditCommentAttachment.comment_id == comment.id
    ).scalar()

    return comment
