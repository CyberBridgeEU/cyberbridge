# routers/audit_comments_controller.py
"""
Controller for audit comments and attachments.
Handles CRUD operations and threading for audit engagement comments.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import logging
import os
import shutil
from datetime import datetime

from ..database.database import get_db
from ..dtos import schemas
from ..models import models
from ..repositories import audit_comment_repository, audit_engagement_repository, audit_notification_repository
from ..services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/audit-engagements",
    tags=["audit-comments"],
    responses={404: {"description": "Not found"}}
)


# ===========================
# Comment Endpoints
# ===========================

@router.get("/{engagement_id}/comments", response_model=schemas.AuditCommentListResponse)
def get_engagement_comments(
    engagement_id: uuid.UUID,
    target_type: Optional[str] = None,
    target_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    comment_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Get all comments for an audit engagement with optional filters.
    Returns root comments only (not replies).
    """
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    # Check user has access to the engagement's organization
    user_org_id = str(current_user.organisation_id) if current_user.organisation_id else None

    # Get user's role name
    user_role = None
    if current_user.role_id:
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        user_role = role.role_name if role else None

    if str(engagement.organisation_id) != user_org_id and user_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    comments = audit_comment_repository.get_comments_for_engagement(
        db, engagement_id, target_type, target_id, status, comment_type, skip, limit
    )

    total_count = audit_comment_repository.get_comment_count_for_engagement(db, engagement_id)

    return schemas.AuditCommentListResponse(
        comments=[_comment_with_replies_to_response(c) for c in comments],
        total_count=total_count
    )


@router.get("/{engagement_id}/comments/target/{target_type}/{target_id}")
def get_comments_for_target(
    engagement_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Get all comments (with replies) for a specific target item.
    """
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    # Get user's org and role
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

    comments = audit_comment_repository.get_comments_for_target(
        db, engagement_id, target_type, target_id
    )

    return [_comment_with_replies_to_response(c) for c in comments]


@router.get("/{engagement_id}/comments/{comment_id}", response_model=schemas.AuditCommentWithRepliesResponse)
def get_comment_thread(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Get a comment and all its replies (thread view).
    """
    comment = audit_comment_repository.get_comment_thread(db, comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    # Verify user has access to the engagement
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)

    # Get user's org and role
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

    return _comment_with_replies_to_response(comment)


@router.post("/{engagement_id}/comments", response_model=schemas.AuditCommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    engagement_id: uuid.UUID,
    request: schemas.AuditCommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Create a new comment on an audit engagement item.
    Can be a root comment or a reply to another comment.
    """
    # Verify engagement exists
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    # Get user's org and role
    user_org_id = str(current_user.organisation_id) if current_user.organisation_id else None
    user_role = None
    if current_user.role_id:
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        user_role = role.role_name if role else None

    # Check user has access
    if str(engagement.organisation_id) != user_org_id and user_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement"
        )

    # Validate target_type
    valid_target_types = ["answer", "evidence", "objective", "policy"]
    if request.target_type not in valid_target_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target_type. Must be one of: {valid_target_types}"
        )

    # Validate comment_type
    valid_comment_types = ["question", "evidence_request", "observation", "potential_exception"]
    if request.comment_type not in valid_comment_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid comment_type. Must be one of: {valid_comment_types}"
        )

    # If replying, verify parent comment exists
    if request.parent_comment_id:
        parent = audit_comment_repository.get_comment(db, request.parent_comment_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )
        if parent.engagement_id != engagement_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment does not belong to this engagement"
            )

    comment = audit_comment_repository.create_comment(
        db=db,
        engagement_id=engagement_id,
        target_type=request.target_type,
        target_id=request.target_id,
        content=request.content,
        comment_type=request.comment_type,
        author_user_id=current_user.id,
        parent_comment_id=request.parent_comment_id,
        assigned_to_id=request.assigned_to_id,
        assigned_to_auditor_id=request.assigned_to_auditor_id,
        due_date=request.due_date
    )

    # Create notifications for relevant parties
    try:
        audit_notification_repository.notify_users_of_new_comment(
            db=db,
            comment=comment,
            engagement=engagement,
            sender_name=current_user.name
        )
    except Exception as e:
        logger.error(f"Failed to create notifications: {e}")

    # Update review status if this is a comment on an answer (control)
    if request.target_type == "answer":
        try:
            # User responding to auditor - change status to "response_provided"
            current_status = audit_notification_repository.get_review_status(
                db, engagement_id, request.target_id
            )
            if current_status and current_status.status == "information_requested":
                audit_notification_repository.update_review_status(
                    db=db,
                    engagement_id=engagement_id,
                    answer_id=request.target_id,
                    new_status="response_provided",
                    updated_by_user_id=current_user.id,
                    status_note=f"Response provided by {current_user.name}"
                )
        except Exception as e:
            logger.error(f"Failed to update review status: {e}")

    return _comment_to_response(comment)


@router.put("/{engagement_id}/comments/{comment_id}", response_model=schemas.AuditCommentResponse)
def update_comment(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    request: schemas.AuditCommentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Update an audit comment.
    """
    comment = audit_comment_repository.get_comment(db, comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    # Get user's role
    user_role = None
    if current_user.role_id:
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        user_role = role.role_name if role else None

    # Check if user is the author or has admin rights
    if comment.author_user_id != current_user.id and user_role not in ["super_admin", "org_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )

    updated_comment = audit_comment_repository.update_comment(
        db=db,
        comment_id=comment_id,
        content=request.content,
        comment_type=request.comment_type,
        assigned_to_id=request.assigned_to_id,
        assigned_to_auditor_id=request.assigned_to_auditor_id,
        due_date=request.due_date
    )

    return _comment_to_response(updated_comment)


@router.patch("/{engagement_id}/comments/{comment_id}/resolve", response_model=schemas.AuditCommentResponse)
def resolve_comment(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    request: schemas.AuditCommentResolveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Resolve a comment.
    """
    comment = audit_comment_repository.get_comment(db, comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    resolved_comment = audit_comment_repository.resolve_comment(
        db=db,
        comment_id=comment_id,
        resolved_by_user_id=current_user.id,
        resolution_note=request.resolution_note
    )

    return _comment_to_response(resolved_comment)


@router.patch("/{engagement_id}/comments/{comment_id}/status")
def update_comment_status(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    status_update: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Update comment status (open, in_progress, resolved, closed).
    """
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status_update not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    comment = audit_comment_repository.get_comment(db, comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    updated_comment = audit_comment_repository.update_comment_status(
        db, comment_id, status_update
    )

    return {"success": True, "status": updated_comment.status}


@router.delete("/{engagement_id}/comments/{comment_id}")
def delete_comment(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Delete a comment (and all its replies).
    """
    comment = audit_comment_repository.get_comment(db, comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    # Get user's role
    user_role = None
    if current_user.role_id:
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        user_role = role.role_name if role else None

    # Check if user is the author or has admin rights
    if comment.author_user_id != current_user.id and user_role not in ["super_admin", "org_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )

    success = audit_comment_repository.delete_comment(db, comment_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment"
        )

    return {"success": True, "message": "Comment deleted successfully"}


# ===========================
# Comment Attachment Endpoints
# ===========================

@router.get("/{engagement_id}/comments/{comment_id}/attachments")
def get_comment_attachments(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Get all attachments for a comment.
    """
    comment = audit_comment_repository.get_comment(db, comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    attachments = audit_comment_repository.get_comment_attachments(db, comment_id)

    return [_attachment_to_response(a) for a in attachments]


@router.post("/{engagement_id}/comments/{comment_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_comment_attachment(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Upload an attachment to a comment.
    """
    comment = audit_comment_repository.get_comment(db, comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    # Create upload directory
    upload_dir = f"uploads/audit_comments/{engagement_id}/{comment_id}"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    filepath = os.path.join(upload_dir, unique_filename)

    # Save file
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save attachment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save attachment"
        )

    # Get file size
    file_size = os.path.getsize(filepath)

    # Create attachment record
    attachment = audit_comment_repository.create_comment_attachment(
        db=db,
        comment_id=comment_id,
        filename=file.filename,
        filepath=filepath,
        file_type=file.content_type,
        file_size=file_size,
        uploaded_by_user_id=current_user.id
    )

    return _attachment_to_response(attachment)


@router.delete("/{engagement_id}/comments/{comment_id}/attachments/{attachment_id}")
def delete_comment_attachment(
    engagement_id: uuid.UUID,
    comment_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Delete a comment attachment.
    """
    # Verify comment exists
    comment = audit_comment_repository.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.engagement_id != engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this engagement"
        )

    success = audit_comment_repository.delete_comment_attachment(db, attachment_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    return {"success": True, "message": "Attachment deleted successfully"}


# ===========================
# Statistics Endpoints
# ===========================

@router.get("/{engagement_id}/comments/stats")
def get_comment_statistics(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_service.get_current_user)
):
    """
    Get comment statistics for an engagement.
    """
    # Verify engagement exists and user has access
    engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit engagement not found"
        )

    # Get user's org and role
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

    total_comments = audit_comment_repository.get_comment_count_for_engagement(db, engagement_id)
    open_comments = audit_comment_repository.get_open_comment_count_for_engagement(db, engagement_id)

    return {
        "total_comments": total_comments,
        "open_comments": open_comments,
        "resolved_comments": total_comments - open_comments
    }


# ===========================
# Helper Functions
# ===========================

def _comment_to_response(comment) -> schemas.AuditCommentResponse:
    """Convert a comment model to response schema."""
    return schemas.AuditCommentResponse(
        id=comment.id,
        engagement_id=comment.engagement_id,
        target_type=comment.target_type,
        target_id=comment.target_id,
        content=comment.content,
        comment_type=comment.comment_type,
        status=comment.status,
        parent_comment_id=comment.parent_comment_id,
        assigned_to_id=comment.assigned_to_id,
        assigned_to_auditor_id=comment.assigned_to_auditor_id,
        due_date=comment.due_date,
        resolved_at=comment.resolved_at,
        resolved_by_id=comment.resolved_by_id,
        resolved_by_auditor_id=comment.resolved_by_auditor_id,
        resolution_note=comment.resolution_note,
        author_user_id=comment.author_user_id,
        author_auditor_id=comment.author_auditor_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author_name=getattr(comment, 'author_name', None),
        author_type=getattr(comment, 'author_type', None),
        assigned_to_name=getattr(comment, 'assigned_to_name', None),
        resolved_by_name=getattr(comment, 'resolved_by_name', None),
        reply_count=getattr(comment, 'reply_count', 0),
        attachment_count=getattr(comment, 'attachment_count', 0)
    )


def _comment_with_replies_to_response(comment) -> schemas.AuditCommentWithRepliesResponse:
    """Convert a comment with replies to response schema."""
    base_response = _comment_to_response(comment)
    replies = [_comment_to_response(r) for r in getattr(comment, 'replies', [])]

    return schemas.AuditCommentWithRepliesResponse(
        **base_response.dict(),
        replies=replies
    )


def _attachment_to_response(attachment) -> schemas.AuditCommentAttachmentResponse:
    """Convert an attachment model to response schema."""
    return schemas.AuditCommentAttachmentResponse(
        id=attachment.id,
        comment_id=attachment.comment_id,
        filename=attachment.filename,
        filepath=attachment.filepath,
        file_type=attachment.file_type,
        file_size=attachment.file_size,
        uploaded_by_user_id=attachment.uploaded_by_user_id,
        uploaded_by_auditor_id=attachment.uploaded_by_auditor_id,
        created_at=attachment.created_at
    )
