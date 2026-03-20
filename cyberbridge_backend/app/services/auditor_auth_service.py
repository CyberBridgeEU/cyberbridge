# services/auditor_auth_service.py
"""
Auditor authentication service for the Audit Engagement Workspace.
Handles magic link authentication, TOTP MFA, and auditor JWT tokens.
"""

import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import jwt
from sqlalchemy.orm import Session
import uuid

from ..repositories import auditor_invitation_repository
from ..models import models
from ..config.environment import get_api_base_url

# JWT Configuration for Auditors (separate from user JWT)
AUDITOR_JWT_SECRET_KEY = secrets.token_urlsafe(32)  # In production, use environment variable
AUDITOR_JWT_ALGORITHM = "HS256"
AUDITOR_JWT_EXPIRE_HOURS = 8  # Session duration


def verify_magic_link_token(db: Session, access_token: str) -> Tuple[bool, Optional[models.AuditorInvitation], str]:
    """
    Verify a magic link access token.

    Returns:
        Tuple of (success, invitation, error_message)
    """
    if not access_token:
        return False, None, "No access token provided"

    invitation = auditor_invitation_repository.get_invitation_by_token(db, access_token)

    if not invitation:
        return False, None, "Invalid access token"

    # Check if token is expired
    if invitation.token_expires_at and datetime.utcnow() > invitation.token_expires_at:
        return False, invitation, "Access token has expired"

    # Check invitation status
    if invitation.status == "revoked":
        return False, invitation, "This invitation has been revoked"

    if invitation.status == "expired":
        return False, invitation, "This invitation has expired"

    # Check access window
    if not auditor_invitation_repository.check_access_window(db, invitation.id):
        return False, invitation, "Current time is outside the allowed access window"

    return True, invitation, ""


def setup_totp_mfa(db: Session, invitation_id: uuid.UUID) -> Tuple[str, str, str]:
    """
    Set up TOTP MFA for an auditor invitation.

    Returns:
        Tuple of (secret, provisioning_uri, qr_code_base64)
    """
    invitation = auditor_invitation_repository.get_invitation(db, invitation_id)
    if not invitation:
        raise ValueError("Invitation not found")

    # Generate TOTP secret
    secret = pyotp.random_base32()

    # Create provisioning URI for QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=invitation.email,
        issuer_name="CyberBridge Audit Portal"
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Save the secret to the invitation
    auditor_invitation_repository.set_mfa_secret(db, invitation_id, secret)

    return secret, provisioning_uri, qr_code_base64


def verify_totp_code(db: Session, invitation_id: uuid.UUID, code: str) -> bool:
    """
    Verify a TOTP code for an auditor.

    Returns:
        True if code is valid, False otherwise
    """
    invitation = auditor_invitation_repository.get_invitation(db, invitation_id)
    if not invitation or not invitation.mfa_secret:
        return False

    totp = pyotp.TOTP(invitation.mfa_secret)
    return totp.verify(code)


def create_auditor_session(
    db: Session,
    invitation: models.AuditorInvitation,
    ip_address: Optional[str] = None
) -> str:
    """
    Create a JWT session token for an authenticated auditor.

    Returns:
        JWT token string
    """
    # Update invitation status to accepted if pending
    if invitation.status == "pending":
        auditor_invitation_repository.update_invitation_status(db, invitation.id, "accepted")

    # Mark as accessed
    auditor_invitation_repository.mark_invitation_accessed(db, invitation.id)

    # Get engagement details
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == invitation.engagement_id
    ).first()

    # Get auditor role permissions
    role = db.query(models.AuditorRole).filter(
        models.AuditorRole.id == invitation.auditor_role_id
    ).first()

    # Build JWT payload
    expire = datetime.utcnow() + timedelta(hours=AUDITOR_JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(invitation.id),
        "type": "auditor",
        "email": invitation.email,
        "name": invitation.name,
        "company": invitation.company,
        "engagement_id": str(invitation.engagement_id),
        "engagement_name": engagement.name if engagement else None,
        "organisation_id": str(engagement.organisation_id) if engagement else None,
        "role_name": role.role_name if role else None,
        "can_comment": role.can_comment if role else False,
        "can_request_evidence": role.can_request_evidence if role else False,
        "can_add_findings": role.can_add_findings if role else False,
        "can_sign_off": role.can_sign_off if role else False,
        "download_restricted": invitation.download_restricted,
        "watermark_downloads": invitation.watermark_downloads,
        "exp": expire,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, AUDITOR_JWT_SECRET_KEY, algorithm=AUDITOR_JWT_ALGORITHM)
    return token


def verify_auditor_token(token: str) -> Tuple[bool, Optional[dict], str]:
    """
    Verify an auditor JWT token.

    Returns:
        Tuple of (success, payload, error_message)
    """
    try:
        payload = jwt.decode(token, AUDITOR_JWT_SECRET_KEY, algorithms=[AUDITOR_JWT_ALGORITHM])

        # Verify this is an auditor token
        if payload.get("type") != "auditor":
            return False, None, "Invalid token type"

        return True, payload, ""

    except jwt.ExpiredSignatureError:
        return False, None, "Session has expired"
    except jwt.JWTError as e:
        return False, None, f"Invalid token: {str(e)}"


def check_ip_allowlist(invitation: models.AuditorInvitation, client_ip: str) -> bool:
    """
    Check if client IP is in the invitation's allowlist.

    Returns:
        True if allowed (or no allowlist configured), False otherwise
    """
    if not invitation.ip_allowlist:
        return True  # No restriction

    allowlist = invitation.ip_allowlist
    if isinstance(allowlist, str):
        import json
        try:
            allowlist = json.loads(allowlist)
        except:
            return True  # Invalid allowlist, allow by default

    if not allowlist or len(allowlist) == 0:
        return True

    return client_ip in allowlist


def generate_magic_link_url(access_token: str, base_url: Optional[str] = None) -> str:
    """
    Generate the full magic link URL for an auditor invitation.
    """
    if not base_url:
        base_url = get_api_base_url()

    # The frontend will handle this route
    return f"{base_url}/auditor/login?token={access_token}"
