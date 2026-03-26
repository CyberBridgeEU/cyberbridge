# submission_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import json
import logging

from app.database.database import get_db
from app.repositories import submission_repository
from app.services import submission_service
from app.services.auth_service import get_current_active_user, check_user_role
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["regulatory-submissions"])


@router.post("")
async def create_submission(
    request: schemas.SubmissionCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Create a regulatory submission and attempt to send certificate via email."""
    try:
        # Seed default emails if not yet done
        submission_repository.seed_default_emails(db, current_user.organisation_id)

        sub = submission_service.create_and_send_submission(
            db=db,
            current_user=current_user,
            authority_name=request.authority_name,
            recipient_emails=request.recipient_emails,
            attachment_types=request.attachment_types,
            certificate_id=request.certificate_id,
            framework_id=request.framework_id,
            subject=request.subject,
            body=request.body,
        )
        return {"id": str(sub.id), "status": sub.status, "message": "Submission created" + (" and email sent" if sub.status == "sent" else " (email not configured — saved as draft)")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create submission")


@router.get("")
async def list_submissions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """List all regulatory submissions for the current org."""
    try:
        # Seed default emails on first access
        submission_repository.seed_default_emails(db, current_user.organisation_id)

        rows = submission_repository.get_submissions_by_org(db, current_user.organisation_id)
        return [
            schemas.SubmissionResponse(
                id=r.id,
                certificate_id=r.certificate_id,
                certificate_number=r.certificate_number,
                framework_name=r.framework_name,
                authority_name=r.authority_name,
                recipient_emails=json.loads(r.recipient_emails) if isinstance(r.recipient_emails, str) else r.recipient_emails,
                attachment_types=json.loads(r.attachment_types) if r.attachment_types and isinstance(r.attachment_types, str) else (r.attachment_types or []),
                submission_method=r.submission_method,
                status=r.status,
                subject=r.subject,
                body=r.body,
                feedback=r.feedback,
                feedback_received_at=r.feedback_received_at,
                sent_at=r.sent_at,
                submitted_by_name=r.submitted_by_name,
                created_at=r.created_at,
            )
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Error listing submissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list submissions")


@router.post("/{sub_id}/feedback")
async def add_feedback(
    sub_id: uuid.UUID,
    request: schemas.SubmissionUpdateFeedbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Record feedback received from a regulatory authority."""
    sub = submission_repository.get_submission_by_id(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.organisation_id != current_user.organisation_id and current_user.role_name != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")

    updated = submission_repository.update_submission_feedback(db, sub_id, request.feedback)
    return {"message": "Feedback recorded", "status": updated.status}


@router.post("/{sub_id}/mark-sent")
async def mark_as_sent(
    sub_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Manually mark a submission as sent (for portal submissions)."""
    sub = submission_repository.get_submission_by_id(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.organisation_id != current_user.organisation_id and current_user.role_name != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")

    from datetime import datetime
    updated = submission_repository.update_submission_status(db, sub_id, "sent", datetime.utcnow())
    return {"message": "Submission marked as sent", "status": updated.status}


@router.post("/{sub_id}/mark-acknowledged")
async def mark_as_acknowledged(
    sub_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Mark a submission as acknowledged by the authority."""
    sub = submission_repository.get_submission_by_id(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.organisation_id != current_user.organisation_id and current_user.role_name != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")

    updated = submission_repository.update_submission_status(db, sub_id, "acknowledged")
    return {"message": "Submission marked as acknowledged", "status": updated.status}


# ---- Email Config Endpoints ----

@router.get("/email-configs")
async def list_email_configs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """List all email configs (default + custom) for the current org."""
    # Seed defaults if needed
    submission_repository.seed_default_emails(db, current_user.organisation_id)

    configs = submission_repository.get_email_configs(db, current_user.organisation_id)
    return [
        schemas.EmailConfigResponse(
            id=c.id,
            authority_name=c.authority_name,
            email=c.email,
            is_default=c.is_default,
        )
        for c in configs
    ]


@router.post("/email-configs")
async def add_email_config(
    request: schemas.EmailConfigCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Add a custom email config."""
    config = submission_repository.create_email_config(
        db, current_user.organisation_id, request.authority_name, request.email, current_user.id
    )
    return schemas.EmailConfigResponse(
        id=config.id,
        authority_name=config.authority_name,
        email=config.email,
        is_default=config.is_default,
    )


@router.delete("/email-configs/{config_id}")
async def delete_email_config(
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Delete a custom email config (cannot delete defaults)."""
    deleted = submission_repository.delete_email_config(db, config_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete default email config")
    return {"message": "Email config deleted"}
