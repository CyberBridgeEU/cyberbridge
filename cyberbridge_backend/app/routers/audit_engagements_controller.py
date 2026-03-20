# routers/audit_engagements_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging

from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user, check_user_role
from ..repositories import (
    audit_engagement_repository,
    auditor_invitation_repository,
    assessment_repository
)
from ..services.notification_service import send_email
from ..services.auditor_auth_service import generate_magic_link_url
from ..config.environment import get_api_base_url, get_environment_name

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/audit-engagements",
    tags=["audit-engagements"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_active_user)]
)


# ===========================
# Auditor Roles Endpoints
# ===========================

@router.get("/roles", response_model=List[schemas.AuditorRoleResponse])
def get_auditor_roles(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all auditor roles (for dropdown selection)"""
    try:
        roles = audit_engagement_repository.get_auditor_roles(db)
        return roles
    except Exception as e:
        logger.error(f"Error fetching auditor roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching auditor roles: {str(e)}"
        )


# ===========================
# Audit Engagement CRUD Endpoints
# ===========================

@router.post("/", response_model=schemas.AuditEngagementResponse, status_code=status.HTTP_201_CREATED)
def create_audit_engagement(
    request: schemas.AuditEngagementCreateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Create a new audit engagement"""
    try:
        # Verify assessment exists
        assessment = assessment_repository.get_assessment(db, uuid.UUID(request.assessment_id))
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Parse prior_engagement_id if provided
        prior_engagement_id = None
        if request.prior_engagement_id:
            prior_engagement_id = uuid.UUID(request.prior_engagement_id)
            # Verify prior engagement exists
            prior_engagement = audit_engagement_repository.get_audit_engagement(db, prior_engagement_id)
            if not prior_engagement:
                raise HTTPException(status_code=404, detail="Prior engagement not found")

        engagement = audit_engagement_repository.create_audit_engagement(
            db=db,
            name=request.name,
            description=request.description,
            assessment_id=uuid.UUID(request.assessment_id),
            owner_id=current_user.id,
            organisation_id=current_user.organisation_id,
            audit_period_start=request.audit_period_start,
            audit_period_end=request.audit_period_end,
            planned_start_date=request.planned_start_date,
            planned_end_date=request.planned_end_date,
            in_scope_controls=request.in_scope_controls,
            in_scope_policies=request.in_scope_policies,
            in_scope_chapters=request.in_scope_chapters,
            prior_engagement_id=prior_engagement_id
        )

        return engagement

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating audit engagement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the audit engagement: {str(e)}"
        )


@router.get("/", response_model=schemas.AuditEngagementListResponse)
def get_audit_engagements(
    status_filter: Optional[str] = None,
    owner_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all audit engagements for the user's organization"""
    try:
        owner_id = current_user.id if owner_only else None

        engagements = audit_engagement_repository.get_audit_engagements(
            db=db,
            organisation_id=current_user.organisation_id,
            skip=skip,
            limit=limit,
            status=status_filter,
            owner_id=owner_id
        )

        total_count = audit_engagement_repository.get_audit_engagements_count(
            db=db,
            organisation_id=current_user.organisation_id,
            status=status_filter,
            owner_id=owner_id
        )

        return schemas.AuditEngagementListResponse(
            engagements=engagements,
            total_count=total_count
        )

    except Exception as e:
        logger.error(f"Error fetching audit engagements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching audit engagements: {str(e)}"
        )


@router.get("/{engagement_id}", response_model=schemas.AuditEngagementResponse)
def get_audit_engagement(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get a specific audit engagement"""
    try:
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)

        if not engagement:
            raise HTTPException(status_code=404, detail="Audit engagement not found")

        # Check organization access
        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return engagement

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit engagement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the audit engagement: {str(e)}"
        )


@router.put("/{engagement_id}", response_model=schemas.AuditEngagementResponse)
def update_audit_engagement(
    engagement_id: uuid.UUID,
    request: schemas.AuditEngagementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Update an audit engagement"""
    try:
        # Verify engagement exists and user has access
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Audit engagement not found")

        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        # Parse prior_engagement_id if provided
        prior_engagement_id = None
        if request.prior_engagement_id:
            prior_engagement_id = uuid.UUID(request.prior_engagement_id)

        updated_engagement = audit_engagement_repository.update_audit_engagement(
            db=db,
            engagement_id=engagement_id,
            name=request.name,
            description=request.description,
            audit_period_start=request.audit_period_start,
            audit_period_end=request.audit_period_end,
            planned_start_date=request.planned_start_date,
            planned_end_date=request.planned_end_date,
            actual_start_date=request.actual_start_date,
            actual_end_date=request.actual_end_date,
            in_scope_controls=request.in_scope_controls,
            in_scope_policies=request.in_scope_policies,
            in_scope_chapters=request.in_scope_chapters,
            prior_engagement_id=prior_engagement_id
        )

        return updated_engagement

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating audit engagement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the audit engagement: {str(e)}"
        )


@router.patch("/{engagement_id}/status", response_model=schemas.AuditEngagementResponse)
def update_audit_engagement_status(
    engagement_id: uuid.UUID,
    request: schemas.AuditEngagementStatusUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Update the status of an audit engagement"""
    try:
        # Verify engagement exists and user has access
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Audit engagement not found")

        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        updated_engagement = audit_engagement_repository.update_audit_engagement_status(
            db=db,
            engagement_id=engagement_id,
            new_status=request.status
        )

        return updated_engagement

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating audit engagement status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the audit engagement status: {str(e)}"
        )


@router.delete("/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audit_engagement(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Delete an audit engagement"""
    try:
        # Verify engagement exists and user has access
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Audit engagement not found")

        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        success = audit_engagement_repository.delete_audit_engagement(db, engagement_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete audit engagement")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting audit engagement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the audit engagement: {str(e)}"
        )


# ===========================
# Auditor Invitation Endpoints
# ===========================

@router.post("/{engagement_id}/invitations", response_model=schemas.AuditorInvitationWithTokenResponse, status_code=status.HTTP_201_CREATED)
def create_auditor_invitation(
    engagement_id: uuid.UUID,
    request: schemas.AuditorInvitationCreateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Create and send an auditor invitation"""
    try:
        # Verify engagement exists and user has access
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Audit engagement not found")

        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        # Verify auditor role exists
        auditor_role = audit_engagement_repository.get_auditor_role(db, uuid.UUID(request.auditor_role_id))
        if not auditor_role:
            raise HTTPException(status_code=404, detail="Auditor role not found")

        # Create the invitation
        invitation = auditor_invitation_repository.create_invitation(
            db=db,
            engagement_id=engagement_id,
            email=request.email,
            auditor_role_id=uuid.UUID(request.auditor_role_id),
            invited_by=current_user.id,
            name=request.name,
            company=request.company,
            access_start=request.access_start,
            access_end=request.access_end,
            mfa_enabled=request.mfa_enabled,
            ip_allowlist=request.ip_allowlist,
            download_restricted=request.download_restricted,
            watermark_downloads=request.watermark_downloads
        )

        # Send invitation email
        _send_invitation_email(db, invitation, engagement, current_user)

        return invitation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating auditor invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the auditor invitation: {str(e)}"
        )


@router.get("/{engagement_id}/invitations", response_model=schemas.AuditorInvitationListResponse)
def get_auditor_invitations(
    engagement_id: uuid.UUID,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all invitations for an engagement"""
    try:
        # Verify engagement exists and user has access
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Audit engagement not found")

        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        invitations = auditor_invitation_repository.get_invitations_for_engagement(
            db=db,
            engagement_id=engagement_id,
            status=status_filter
        )

        return schemas.AuditorInvitationListResponse(
            invitations=invitations,
            total_count=len(invitations)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching auditor invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching auditor invitations: {str(e)}"
        )


@router.get("/{engagement_id}/invitations/{invitation_id}", response_model=schemas.AuditorInvitationResponse)
def get_auditor_invitation(
    engagement_id: uuid.UUID,
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get a specific invitation"""
    try:
        invitation = auditor_invitation_repository.get_invitation(db, invitation_id)
        if not invitation or str(invitation.engagement_id) != str(engagement_id):
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Verify user has access to the engagement
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return invitation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching auditor invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the auditor invitation: {str(e)}"
        )


@router.put("/{engagement_id}/invitations/{invitation_id}", response_model=schemas.AuditorInvitationResponse)
def update_auditor_invitation(
    engagement_id: uuid.UUID,
    invitation_id: uuid.UUID,
    request: schemas.AuditorInvitationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Update an auditor invitation"""
    try:
        invitation = auditor_invitation_repository.get_invitation(db, invitation_id)
        if not invitation or str(invitation.engagement_id) != str(engagement_id):
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Verify user has access to the engagement
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        # Parse auditor_role_id if provided
        auditor_role_id = None
        if request.auditor_role_id:
            auditor_role_id = uuid.UUID(request.auditor_role_id)

        updated_invitation = auditor_invitation_repository.update_invitation(
            db=db,
            invitation_id=invitation_id,
            name=request.name,
            company=request.company,
            auditor_role_id=auditor_role_id,
            access_start=request.access_start,
            access_end=request.access_end,
            mfa_enabled=request.mfa_enabled,
            ip_allowlist=request.ip_allowlist,
            download_restricted=request.download_restricted,
            watermark_downloads=request.watermark_downloads
        )

        return updated_invitation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating auditor invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the auditor invitation: {str(e)}"
        )


@router.delete("/{engagement_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_auditor_invitation(
    engagement_id: uuid.UUID,
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Revoke an auditor invitation"""
    try:
        invitation = auditor_invitation_repository.get_invitation(db, invitation_id)
        if not invitation or str(invitation.engagement_id) != str(engagement_id):
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Verify user has access to the engagement
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        auditor_invitation_repository.revoke_invitation(db, invitation_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking auditor invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while revoking the auditor invitation: {str(e)}"
        )


@router.post("/{engagement_id}/invitations/{invitation_id}/resend", response_model=schemas.AuditorInvitationWithTokenResponse)
def resend_auditor_invitation(
    engagement_id: uuid.UUID,
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Resend an auditor invitation (regenerates token)"""
    try:
        invitation = auditor_invitation_repository.get_invitation(db, invitation_id)
        if not invitation or str(invitation.engagement_id) != str(engagement_id):
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Verify user has access to the engagement
        engagement = audit_engagement_repository.get_audit_engagement(db, engagement_id)
        if str(engagement.organisation_id) != str(current_user.organisation_id) and current_user.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        # Regenerate token
        updated_invitation = auditor_invitation_repository.regenerate_access_token(db, invitation_id)

        # Resend invitation email
        _send_invitation_email(db, updated_invitation, engagement, current_user)

        return updated_invitation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending auditor invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while resending the auditor invitation: {str(e)}"
        )


# ===========================
# Helper Functions
# ===========================

def _send_invitation_email(db: Session, invitation, engagement, inviter):
    """Send the auditor invitation email"""
    try:
        environment = get_environment_name()
        base_url = get_api_base_url()

        # Generate the magic link URL for the auditor to access the portal
        magic_link = generate_magic_link_url(invitation.access_token, base_url)

        auditor_name = invitation.name or "Auditor"
        role_name = invitation.role_name or "Auditor"

        # Format access window if defined
        access_window_html = ""
        if invitation.access_start or invitation.access_end:
            start_str = invitation.access_start.strftime("%B %d, %Y") if invitation.access_start else "Immediately"
            end_str = invitation.access_end.strftime("%B %d, %Y") if invitation.access_end else "No expiry"
            access_window_html = f"""
            <p><strong>Access Window:</strong> {start_str} - {end_str}</p>
            """

        mfa_html = ""
        if invitation.mfa_enabled:
            mfa_html = """
            <p><strong>Security:</strong> Multi-factor authentication will be required.</p>
            """

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
                    <h1>Audit Engagement Invitation</h1>
                </div>
                <div class="content">
                    <p>Hello {auditor_name},</p>
                    <p>You have been invited to participate as an auditor in a compliance assessment review.</p>

                    <div class="info-box">
                        <h3>Engagement Details</h3>
                        <p><strong>Engagement:</strong> {engagement.name}</p>
                        <p><strong>Your Role:</strong> {role_name.replace('_', ' ').title()}</p>
                        <p><strong>Invited By:</strong> {inviter.name} ({inviter.email})</p>
                        {access_window_html}
                        {mfa_html}
                    </div>

                    <p>Click the button below to accept this invitation and access the audit portal:</p>

                    <p style="text-align: center;">
                        <a href="{magic_link}" class="btn">Access Audit Portal</a>
                    </p>

                    <p style="margin-top: 20px; font-size: 12px; color: #666;">
                        This invitation will expire in 72 hours. If you did not expect this invitation, please ignore this email.
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

        subject = f"[CyberBridge] Audit Engagement Invitation - {engagement.name}"
        send_email(db, invitation.email, subject, html_content)

    except Exception as e:
        logger.error(f"Error sending invitation email: {str(e)}")
        # Don't raise - invitation was created, email failure shouldn't fail the request
