# routers/auditor_auth_controller.py
"""
Auditor authentication endpoints for the Audit Engagement Workspace.
Handles magic link verification, MFA setup, and session management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
import logging

from ..database.database import get_db
from ..services import auditor_auth_service
from ..services.notification_service import send_email
from ..repositories import auditor_invitation_repository
from ..config.environment import get_api_base_url, get_environment_name

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auditor/auth",
    tags=["auditor-auth"],
    responses={404: {"description": "Not found"}}
)


# Request/Response Models
class MagicLinkRequest(BaseModel):
    email: EmailStr


class VerifyTokenRequest(BaseModel):
    access_token: str


class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_base64: str


class MFAVerifyRequest(BaseModel):
    invitation_id: str
    code: str


class AuditorSessionResponse(BaseModel):
    token: str
    expires_in_hours: int
    engagement_id: str
    engagement_name: Optional[str]
    role_name: Optional[str]
    can_comment: bool
    can_request_evidence: bool
    can_add_findings: bool
    can_sign_off: bool
    mfa_required: bool
    mfa_setup_required: bool


class TokenVerificationResponse(BaseModel):
    valid: bool
    invitation_id: Optional[str]
    email: Optional[str]
    name: Optional[str]
    engagement_name: Optional[str]
    mfa_enabled: bool
    mfa_setup_required: bool
    message: str


# Endpoints

@router.post("/request-magic-link")
def request_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db)
):
    """
    Request a magic link email for auditor login.
    If the auditor has pending invitations, sends them a login link.
    """
    try:
        # Find pending invitations for this email
        invitations = auditor_invitation_repository.get_invitations_by_email(db, request.email)
        active_invitations = [inv for inv in invitations if inv.status in ["pending", "accepted"]]

        if not active_invitations:
            # Don't reveal whether email exists - return success anyway
            return {
                "success": True,
                "message": "If you have an active invitation, a login link has been sent to your email."
            }

        # Send magic link email for each active invitation
        for invitation in active_invitations:
            # Regenerate token if expired
            if invitation.token_expired:
                invitation = auditor_invitation_repository.regenerate_access_token(db, invitation.id)

            _send_magic_link_email(db, invitation)

        return {
            "success": True,
            "message": "If you have an active invitation, a login link has been sent to your email."
        }

    except Exception as e:
        logger.error(f"Error requesting magic link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )


@router.post("/verify-token", response_model=TokenVerificationResponse)
def verify_magic_link_token(
    request: VerifyTokenRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify a magic link access token and return invitation details.
    Does not create a session - use /login endpoint for that.
    """
    try:
        success, invitation, error_message = auditor_auth_service.verify_magic_link_token(
            db, request.access_token
        )

        if not success:
            return TokenVerificationResponse(
                valid=False,
                invitation_id=str(invitation.id) if invitation else None,
                email=invitation.email if invitation else None,
                name=invitation.name if invitation else None,
                engagement_name=None,
                mfa_enabled=False,
                mfa_setup_required=False,
                message=error_message
            )

        # Check IP allowlist
        client_ip = http_request.client.host if http_request.client else None
        if client_ip and not auditor_auth_service.check_ip_allowlist(invitation, client_ip):
            return TokenVerificationResponse(
                valid=False,
                invitation_id=str(invitation.id),
                email=invitation.email,
                name=invitation.name,
                engagement_name=invitation.engagement_name,
                mfa_enabled=invitation.mfa_enabled,
                mfa_setup_required=False,
                message="Access denied from your IP address"
            )

        # Determine if MFA setup is required
        mfa_setup_required = invitation.mfa_enabled and not invitation.mfa_secret

        return TokenVerificationResponse(
            valid=True,
            invitation_id=str(invitation.id),
            email=invitation.email,
            name=invitation.name,
            engagement_name=invitation.engagement_name,
            mfa_enabled=invitation.mfa_enabled,
            mfa_setup_required=mfa_setup_required,
            message="Token verified successfully"
        )

    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying the token"
        )


@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    request: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Set up TOTP MFA for an auditor.
    Requires valid access token. Returns QR code and secret.
    """
    try:
        # Verify token first
        success, invitation, error_message = auditor_auth_service.verify_magic_link_token(
            db, request.access_token
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )

        if not invitation.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this invitation"
            )

        # Set up TOTP
        secret, provisioning_uri, qr_code_base64 = auditor_auth_service.setup_totp_mfa(
            db, invitation.id
        )

        return MFASetupResponse(
            secret=secret,
            provisioning_uri=provisioning_uri,
            qr_code_base64=qr_code_base64
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up MFA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while setting up MFA"
        )


@router.post("/mfa/verify")
def verify_mfa_code(
    request: MFAVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a TOTP code for MFA authentication.
    """
    try:
        is_valid = auditor_auth_service.verify_totp_code(
            db, uuid.UUID(request.invitation_id), request.code
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )

        return {"success": True, "message": "MFA code verified"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MFA code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying MFA code"
        )


@router.post("/login", response_model=AuditorSessionResponse)
def auditor_login(
    request: VerifyTokenRequest,
    mfa_code: Optional[str] = None,
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Complete auditor login and create a session.
    If MFA is enabled, requires mfa_code parameter.
    """
    try:
        # Verify token
        success, invitation, error_message = auditor_auth_service.verify_magic_link_token(
            db, request.access_token
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )

        # Check IP allowlist
        client_ip = http_request.client.host if http_request and http_request.client else None
        if client_ip and not auditor_auth_service.check_ip_allowlist(invitation, client_ip):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from your IP address"
            )

        # Check MFA if enabled
        if invitation.mfa_enabled:
            if not invitation.mfa_secret:
                # MFA setup required but not completed
                return AuditorSessionResponse(
                    token="",
                    expires_in_hours=0,
                    engagement_id=str(invitation.engagement_id),
                    engagement_name=invitation.engagement_name,
                    role_name=invitation.role_name,
                    can_comment=invitation.can_comment or False,
                    can_request_evidence=invitation.can_request_evidence or False,
                    can_add_findings=invitation.can_add_findings or False,
                    can_sign_off=invitation.can_sign_off or False,
                    mfa_required=True,
                    mfa_setup_required=True
                )

            if not mfa_code:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="MFA code required"
                )

            if not auditor_auth_service.verify_totp_code(db, invitation.id, mfa_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code"
                )

        # Create session token
        session_token = auditor_auth_service.create_auditor_session(
            db, invitation, ip_address=client_ip
        )

        return AuditorSessionResponse(
            token=session_token,
            expires_in_hours=auditor_auth_service.AUDITOR_JWT_EXPIRE_HOURS,
            engagement_id=str(invitation.engagement_id),
            engagement_name=invitation.engagement_name,
            role_name=invitation.role_name,
            can_comment=invitation.can_comment or False,
            can_request_evidence=invitation.can_request_evidence or False,
            can_add_findings=invitation.can_add_findings or False,
            can_sign_off=invitation.can_sign_off or False,
            mfa_required=invitation.mfa_enabled,
            mfa_setup_required=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during auditor login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/logout")
def auditor_logout():
    """
    Log out the auditor session.
    Note: Since we use stateless JWTs, this is mostly a client-side operation.
    The client should discard the token.
    """
    return {"success": True, "message": "Logged out successfully"}


@router.get("/verify-session")
def verify_auditor_session(
    authorization: str,
    db: Session = Depends(get_db)
):
    """
    Verify an auditor session token is still valid.
    """
    try:
        # Extract token from Authorization header
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        success, payload, error_message = auditor_auth_service.verify_auditor_token(token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )

        return {
            "valid": True,
            "email": payload.get("email"),
            "engagement_id": payload.get("engagement_id"),
            "role_name": payload.get("role_name")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )


# Helper functions

def _send_magic_link_email(db: Session, invitation):
    """Send the magic link email to an auditor."""
    try:
        environment = get_environment_name()
        base_url = get_api_base_url()

        magic_link = auditor_auth_service.generate_magic_link_url(
            invitation.access_token, base_url
        )

        auditor_name = invitation.name or "Auditor"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a365d; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #e0e0e0; }}
                .info-box {{ background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 15px 0; }}
                .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
                .btn {{ display: inline-block; background-color: #5b9bd5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 15px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Audit Portal Access</h1>
                </div>
                <div class="content">
                    <p>Hello {auditor_name},</p>
                    <p>You have requested access to the CyberBridge Audit Portal.</p>

                    <div class="info-box">
                        <h3>Engagement</h3>
                        <p><strong>{invitation.engagement_name}</strong></p>
                    </div>

                    <p>Click the button below to securely access the audit portal:</p>

                    <p style="text-align: center;">
                        <a href="{magic_link}" class="btn">Access Audit Portal</a>
                    </p>

                    <p style="margin-top: 20px; font-size: 12px; color: #666;">
                        This link will expire in 72 hours. If you did not request this access, please ignore this email.
                    </p>

                    <p style="font-size: 12px; color: #666;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{magic_link}" style="color: #5b9bd5; word-break: break-all;">{magic_link}</a>
                    </p>
                </div>
                <div class="footer">
                    <p>CyberBridge - Cybersecurity Compliance Platform</p>
                    <p>Environment: {environment}</p>
                </div>
            </div>
        </body>
        </html>
        """

        subject = f"[CyberBridge] Access Link - {invitation.engagement_name}"
        send_email(db, invitation.email, subject, html_content)

    except Exception as e:
        logger.error(f"Error sending magic link email: {str(e)}")
