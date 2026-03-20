# repositories/auditor_invitation_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
import secrets
from typing import Optional, List
from datetime import datetime, timedelta

from app.models import models


# ===========================
# Auditor Invitation CRUD Operations
# ===========================

def get_invitation(db: Session, invitation_id: uuid.UUID):
    """Get a single invitation by ID"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if invitation:
        _enrich_invitation(db, invitation)

    return invitation


def get_invitation_by_token(db: Session, access_token: str):
    """Get an invitation by its access token"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.access_token == access_token
    ).first()

    if invitation:
        _enrich_invitation(db, invitation)

    return invitation


def get_invitations_for_engagement(
    db: Session,
    engagement_id: uuid.UUID,
    status: Optional[str] = None
):
    """Get all invitations for an engagement"""
    query = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.engagement_id == engagement_id
    )

    if status:
        query = query.filter(models.AuditorInvitation.status == status)

    invitations = query.order_by(
        models.AuditorInvitation.created_at.desc()
    ).all()

    for invitation in invitations:
        _enrich_invitation(db, invitation)

    return invitations


def get_invitations_by_email(db: Session, email: str):
    """Get all invitations for a specific email"""
    invitations = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.email == email
    ).order_by(
        models.AuditorInvitation.created_at.desc()
    ).all()

    for invitation in invitations:
        _enrich_invitation(db, invitation)

    return invitations


def create_invitation(
    db: Session,
    engagement_id: uuid.UUID,
    email: str,
    auditor_role_id: uuid.UUID,
    invited_by: uuid.UUID,
    name: Optional[str] = None,
    company: Optional[str] = None,
    access_start: Optional[datetime] = None,
    access_end: Optional[datetime] = None,
    mfa_enabled: bool = False,
    ip_allowlist: Optional[List[str]] = None,
    download_restricted: bool = False,
    watermark_downloads: bool = True,
    token_expiry_hours: int = 72  # Default 72 hours for magic link
):
    """Create a new auditor invitation"""
    # Generate a secure access token
    access_token = secrets.token_urlsafe(64)
    token_expires_at = datetime.utcnow() + timedelta(hours=token_expiry_hours)

    invitation = models.AuditorInvitation(
        engagement_id=engagement_id,
        email=email.lower().strip(),
        name=name,
        company=company,
        auditor_role_id=auditor_role_id,
        access_token=access_token,
        token_expires_at=token_expires_at,
        access_start=access_start,
        access_end=access_end,
        mfa_enabled=mfa_enabled,
        download_restricted=download_restricted,
        watermark_downloads=watermark_downloads,
        status="pending",
        invited_by=invited_by
    )

    if ip_allowlist:
        invitation.ip_allowlist = ip_allowlist

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    _enrich_invitation(db, invitation)

    return invitation


def update_invitation(
    db: Session,
    invitation_id: uuid.UUID,
    name: Optional[str] = None,
    company: Optional[str] = None,
    auditor_role_id: Optional[uuid.UUID] = None,
    access_start: Optional[datetime] = None,
    access_end: Optional[datetime] = None,
    mfa_enabled: Optional[bool] = None,
    ip_allowlist: Optional[List[str]] = None,
    download_restricted: Optional[bool] = None,
    watermark_downloads: Optional[bool] = None
):
    """Update an existing invitation"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if not invitation:
        return None

    # Update fields if provided
    if name is not None:
        invitation.name = name
    if company is not None:
        invitation.company = company
    if auditor_role_id is not None:
        invitation.auditor_role_id = auditor_role_id
    if access_start is not None:
        invitation.access_start = access_start
    if access_end is not None:
        invitation.access_end = access_end
    if mfa_enabled is not None:
        invitation.mfa_enabled = mfa_enabled
    if ip_allowlist is not None:
        invitation.ip_allowlist = ip_allowlist
    if download_restricted is not None:
        invitation.download_restricted = download_restricted
    if watermark_downloads is not None:
        invitation.watermark_downloads = watermark_downloads

    db.commit()
    db.refresh(invitation)

    _enrich_invitation(db, invitation)

    return invitation


def update_invitation_status(
    db: Session,
    invitation_id: uuid.UUID,
    new_status: str
):
    """Update the status of an invitation"""
    valid_statuses = ["pending", "accepted", "expired", "revoked"]

    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if not invitation:
        return None

    invitation.status = new_status

    if new_status == "accepted":
        invitation.accepted_at = datetime.utcnow()

    db.commit()
    db.refresh(invitation)

    _enrich_invitation(db, invitation)

    return invitation


def mark_invitation_accessed(db: Session, invitation_id: uuid.UUID):
    """Update the last_accessed_at timestamp"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if not invitation:
        return None

    invitation.last_accessed_at = datetime.utcnow()

    db.commit()
    db.refresh(invitation)

    return invitation


def revoke_invitation(db: Session, invitation_id: uuid.UUID):
    """Revoke an invitation"""
    return update_invitation_status(db, invitation_id, "revoked")


def delete_invitation(db: Session, invitation_id: uuid.UUID) -> bool:
    """Delete an invitation"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if not invitation:
        return False

    db.delete(invitation)
    db.commit()
    return True


def regenerate_access_token(
    db: Session,
    invitation_id: uuid.UUID,
    token_expiry_hours: int = 72
):
    """Regenerate the access token for an invitation"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if not invitation:
        return None

    # Generate new token
    invitation.access_token = secrets.token_urlsafe(64)
    invitation.token_expires_at = datetime.utcnow() + timedelta(hours=token_expiry_hours)

    # Reset status to pending if it was expired
    if invitation.status == "expired":
        invitation.status = "pending"

    db.commit()
    db.refresh(invitation)

    _enrich_invitation(db, invitation)

    return invitation


def set_mfa_secret(db: Session, invitation_id: uuid.UUID, mfa_secret: str):
    """Set the MFA secret for an invitation"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if not invitation:
        return None

    invitation.mfa_secret = mfa_secret

    db.commit()
    db.refresh(invitation)

    return invitation


def expire_old_invitations(db: Session) -> int:
    """Expire invitations whose tokens have expired"""
    now = datetime.utcnow()

    expired_count = db.query(models.AuditorInvitation).filter(
        and_(
            models.AuditorInvitation.status == "pending",
            models.AuditorInvitation.token_expires_at < now
        )
    ).update({"status": "expired"})

    db.commit()

    return expired_count


def check_access_window(db: Session, invitation_id: uuid.UUID) -> bool:
    """Check if current time is within the invitation's access window"""
    invitation = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.id == invitation_id
    ).first()

    if not invitation:
        return False

    now = datetime.utcnow()

    # Check if access window is defined
    if invitation.access_start and now < invitation.access_start:
        return False

    if invitation.access_end and now > invitation.access_end:
        return False

    return True


def _enrich_invitation(db: Session, invitation):
    """Helper function to enrich invitation with related data"""
    # Get auditor role info
    role = db.query(models.AuditorRole).filter(
        models.AuditorRole.id == invitation.auditor_role_id
    ).first()

    if role:
        invitation.role_name = role.role_name
        invitation.can_comment = role.can_comment
        invitation.can_request_evidence = role.can_request_evidence
        invitation.can_add_findings = role.can_add_findings
        invitation.can_sign_off = role.can_sign_off

    # Get engagement info
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == invitation.engagement_id
    ).first()

    if engagement:
        invitation.engagement_name = engagement.name
        invitation.engagement_status = engagement.status

    # Get inviter info
    inviter = db.query(models.User).filter(
        models.User.id == invitation.invited_by
    ).first()

    if inviter:
        invitation.invited_by_name = inviter.name
        invitation.invited_by_email = inviter.email

    # Check if token is expired
    if invitation.token_expires_at:
        invitation.token_expired = datetime.utcnow() > invitation.token_expires_at
    else:
        invitation.token_expired = False

    # Check if currently within access window
    invitation.within_access_window = check_access_window(db, invitation.id)
