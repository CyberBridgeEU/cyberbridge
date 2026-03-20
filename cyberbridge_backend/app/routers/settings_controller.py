from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
import csv
import io
import json

from app.database.database import get_db
from app.repositories import smtp_repository, sso_repository
from app.models import models
from app.services.auth_service import get_current_active_user
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

class SMTPConfig(BaseModel):
    label: Optional[str] = None
    smtp_server: str
    smtp_port: int
    sender_email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True

class EmailTestRequest(BaseModel):
    recipient_email: EmailStr

class FrameworkPermissionRequest(BaseModel):
    organization_id: str
    framework_ids: List[str]

class FrameworkTemplatePermissionRequest(BaseModel):
    organization_id: str
    template_ids: List[str]

class DomainBlacklistRequest(BaseModel):
    domain: str
    reason: str = None

class DomainBlacklistResponse(BaseModel):
    id: str
    domain: str
    is_blacklisted: bool
    reason: str = None

class LLMSettingsRequest(BaseModel):
    """Global LLM settings request - managed by super admin."""
    # Global AI toggle
    ai_enabled: Optional[bool] = None
    default_provider: Optional[str] = None
    # AI Policy Aligner global toggle
    ai_policy_aligner_enabled: Optional[bool] = None
    # Legacy/correlation settings
    custom_llm_url: Optional[str] = None
    custom_llm_payload: Optional[str] = None
    max_questions_per_framework: Optional[int] = None
    llm_timeout_seconds: Optional[int] = None
    min_confidence_threshold: Optional[int] = None
    max_correlations: Optional[int] = None

class LLMSettingsResponse(BaseModel):
    """Global LLM settings response."""
    id: str
    ai_enabled: bool
    default_provider: str
    custom_llm_url: Optional[str]
    custom_llm_payload: Optional[str]
    max_questions_per_framework: int
    llm_timeout_seconds: int
    min_confidence_threshold: int
    max_correlations: int
    created_at: str
    updated_at: str

class OrgLLMSettingsRequest(BaseModel):
    """Organization-specific LLM settings request."""
    llm_provider: str  # 'llamacpp', 'qlon', 'openai', 'anthropic', 'xai', 'google'
    # QLON configuration
    qlon_url: Optional[str] = None
    qlon_api_key: Optional[str] = None
    qlon_use_tools: Optional[bool] = True
    # OpenAI (ChatGPT) configuration
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    openai_base_url: Optional[str] = None  # Optional for custom endpoints
    # Anthropic (Claude) configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None
    # X AI (Grok) configuration
    xai_api_key: Optional[str] = None
    xai_model: Optional[str] = None
    xai_base_url: Optional[str] = None  # Default: https://api.x.ai/v1
    # Google (Gemini) configuration
    google_api_key: Optional[str] = None
    google_model: Optional[str] = None
    # Enable/disable for this org (disabled by default)
    is_enabled: Optional[bool] = False
    # AI Remediator settings
    ai_remediator_enabled: Optional[bool] = None
    remediator_prompt_zap: Optional[str] = None
    remediator_prompt_nmap: Optional[str] = None

class OrgLLMSettingsResponse(BaseModel):
    """Organization-specific LLM settings response."""
    id: str
    organisation_id: str
    llm_provider: str
    qlon_url: Optional[str]
    qlon_api_key: Optional[str]  # Will be masked in response
    qlon_use_tools: Optional[bool]
    # OpenAI (ChatGPT) fields
    openai_api_key: Optional[str]  # Will be masked in response
    openai_model: Optional[str]
    openai_base_url: Optional[str]
    # Anthropic (Claude) fields
    anthropic_api_key: Optional[str]  # Will be masked in response
    anthropic_model: Optional[str]
    # X AI (Grok) fields
    xai_api_key: Optional[str]  # Will be masked in response
    xai_model: Optional[str]
    xai_base_url: Optional[str]
    # Google (Gemini) fields
    google_api_key: Optional[str]  # Will be masked in response
    google_model: Optional[str]
    is_enabled: bool
    created_at: str
    updated_at: str

class ScannerSettingsRequest(BaseModel):
    scanners_enabled: Optional[bool] = None
    allowed_scanner_domains: Optional[List[str]] = None

class ScannerSettingsResponse(BaseModel):
    id: str
    scanners_enabled: bool
    allowed_scanner_domains: Optional[List[str]]
    created_at: str
    updated_at: str

class SSOSettingsRequest(BaseModel):
    label: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    microsoft_tenant_id: Optional[str] = None

class SuperAdminFocusedModeRequest(BaseModel):
    super_admin_focused_mode: bool

class SuperAdminFocusedModeResponse(BaseModel):
    super_admin_focused_mode: bool

class OrgCRAModeRequest(BaseModel):
    cra_mode: Optional[str] = None  # 'focused', 'extended', or '' to disable
    cra_operator_role: Optional[str] = None  # 'Manufacturer', 'Importer', 'Distributor', or null

class FrameworkPermissionResponse(BaseModel):
    id: str
    organization_id: str
    framework_id: str
    can_seed: bool

def load_smtp_config(db: Session) -> SMTPConfig | None:
    """Load SMTP configuration from database."""
    try:
        config = smtp_repository.get_active_smtp_config(db)
        if config:
            return SMTPConfig(
                label=config.label,
                smtp_server=config.smtp_server,
                smtp_port=config.smtp_port,
                sender_email=config.sender_email,
                username=config.username,
                password=config.password,
                use_tls=config.use_tls
            )
    except Exception as e:
        logger.error(f"Error loading SMTP config: {str(e)}")
    return None

def save_smtp_config(db: Session, config: SMTPConfig) -> None:
    """Save SMTP configuration to database."""
    try:
        config_data = config.dict()
        smtp_repository.create_smtp_config(db, config_data)
    except Exception as e:
        logger.error(f"Error saving SMTP config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save SMTP configuration")

@router.post("/smtp-config")
async def save_smtp_configuration(config: SMTPConfig, db: Session = Depends(get_db)):
    """Save SMTP configuration."""
    try:
        # Sanitize input to remove non-ASCII characters like non-breaking spaces
        config.smtp_server = config.smtp_server.strip().replace('\xa0', ' ')
        if config.username:
            config.username = config.username.strip().replace('\xa0', ' ')
        if config.password:
            config.password = config.password.strip().replace('\xa0', '')
        if config.sender_email:
            config.sender_email = config.sender_email.strip().replace('\xa0', ' ')
        if config.label:
            config.label = config.label.strip()

        # Test the SMTP configuration before saving
        server = smtplib.SMTP(config.smtp_server, config.smtp_port)
        if config.use_tls:
            server.starttls()
        # Only login if credentials are provided
        if config.username and config.password:
            server.login(config.username, config.password)
        server.quit()

        # If successful, save the configuration
        save_smtp_config(db, config)

        return {"message": "SMTP configuration saved successfully"}
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=400, detail="SMTP authentication failed. Please check your username and password.")
    except smtplib.SMTPConnectError:
        raise HTTPException(status_code=400, detail="Could not connect to SMTP server. Please check server and port.")
    except Exception as e:
        logger.error(f"Error saving SMTP config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save SMTP configuration: {str(e)}")

@router.get("/smtp-config")
async def get_smtp_configuration(db: Session = Depends(get_db)):
    """Get current active SMTP configuration (without password)."""
    config = load_smtp_config(db)
    if config:
        # Return config without password for security
        config_dict = config.dict()
        config_dict.pop('password', None)
        return config_dict
    return {"message": "No SMTP configuration found"}

@router.get("/smtp-configs")
async def get_all_smtp_configurations(db: Session = Depends(get_db)):
    """Get all SMTP configurations (without passwords)."""
    configs = smtp_repository.get_all_smtp_configs(db)
    return [
        {
            "id": str(c.id),
            "label": c.label,
            "smtp_server": c.smtp_server,
            "smtp_port": c.smtp_port,
            "sender_email": c.sender_email,
            "username": c.username,
            "use_tls": c.use_tls,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in configs
    ]

@router.delete("/smtp-config/{config_id}")
async def delete_smtp_configuration(config_id: str, db: Session = Depends(get_db)):
    """Delete an SMTP configuration."""
    import uuid
    try:
        deleted = smtp_repository.delete_smtp_config(db, uuid.UUID(config_id))
        if not deleted:
            raise HTTPException(status_code=404, detail="SMTP configuration not found")
        return {"message": "SMTP configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SMTP config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete SMTP configuration: {str(e)}")

@router.put("/smtp-config/{config_id}/activate")
async def activate_smtp_configuration(config_id: str, db: Session = Depends(get_db)):
    """Set an SMTP configuration as active (deactivates all others)."""
    import uuid
    try:
        config = smtp_repository.set_active_smtp_config(db, uuid.UUID(config_id))
        if not config:
            raise HTTPException(status_code=404, detail="SMTP configuration not found")
        return {"message": "SMTP configuration activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating SMTP config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to activate SMTP configuration: {str(e)}")

@router.put("/smtp-config/{config_id}/deactivate")
async def deactivate_smtp_configuration(config_id: str, db: Session = Depends(get_db)):
    """Deactivate an SMTP configuration."""
    import uuid
    try:
        config = smtp_repository.deactivate_smtp_config(db, uuid.UUID(config_id))
        if not config:
            raise HTTPException(status_code=404, detail="SMTP configuration not found")
        return {"message": "SMTP configuration deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating SMTP config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate SMTP configuration: {str(e)}")

@router.post("/test-email")
async def send_test_email(request: EmailTestRequest, db: Session = Depends(get_db)):
    """Send a test email using the configured SMTP settings."""
    config = load_smtp_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="SMTP configuration not found. Please configure SMTP settings first.")

    try:
        from_address = config.sender_email or config.username
        if not from_address:
            raise HTTPException(status_code=400, detail="No sender email or username configured.")

        # Create message
        message = MIMEMultipart()
        message["From"] = from_address
        message["To"] = request.recipient_email
        message["Subject"] = "CyberBridge SMTP Configuration Test"

        # Email body
        body = """
        <html>
        <body>
        <h2>CyberBridge SMTP Test Email</h2>
        <p>This is a test email sent from your CyberBridge application.</p>
        <p>If you received this email, your SMTP configuration is working correctly!</p>
        <hr>
        <p><small>This email was sent automatically from your CyberBridge system.</small></p>
        </body>
        </html>
        """

        message.attach(MIMEText(body, "html"))

        # Connect to server and send email
        server = smtplib.SMTP(config.smtp_server, config.smtp_port)
        if config.use_tls:
            server.starttls()
        # Only login if credentials are provided
        if config.username and config.password:
            server.login(config.username, config.password)

        text = message.as_string()
        server.sendmail(from_address, request.recipient_email, text)
        server.quit()

        return {"message": f"Test email sent successfully to {request.recipient_email}"}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=400, detail="SMTP authentication failed. Please check your SMTP configuration.")
    except smtplib.SMTPRecipientsRefused:
        raise HTTPException(status_code=400, detail="Recipient email address was refused by the server.")
    except smtplib.SMTPConnectError:
        raise HTTPException(status_code=400, detail="Could not connect to SMTP server. Please check your SMTP configuration.")
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

@router.post("/framework-permissions")
async def set_framework_permissions(request: FrameworkPermissionRequest, db: Session = Depends(get_db)):
    """Set which frameworks an organization can seed."""
    try:
        # Delete existing permissions for this organization
        db.query(models.OrganizationFrameworkPermissions).filter(
            models.OrganizationFrameworkPermissions.organization_id == request.organization_id
        ).delete()

        # Add new permissions for the selected frameworks
        for framework_id in request.framework_ids:
            permission = models.OrganizationFrameworkPermissions(
                organization_id=request.organization_id,
                framework_id=framework_id,
                can_seed=True
            )
            db.add(permission)

        db.commit()
        return {"message": "Framework permissions updated successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error setting framework permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update framework permissions: {str(e)}")

@router.get("/framework-permissions/{organization_id}")
async def get_framework_permissions(organization_id: str, db: Session = Depends(get_db)):
    """Get framework permissions for an organization."""
    try:
        permissions = db.query(models.OrganizationFrameworkPermissions).filter(
            models.OrganizationFrameworkPermissions.organization_id == organization_id
        ).all()

        return [
            {
                "id": str(permission.id),
                "organization_id": str(permission.organization_id),
                "framework_id": str(permission.framework_id),
                "can_seed": permission.can_seed
            }
            for permission in permissions
        ]

    except Exception as e:
        logger.error(f"Error getting framework permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get framework permissions: {str(e)}")

@router.get("/seedable-frameworks/{organization_id}")
async def get_seedable_frameworks(organization_id: str, db: Session = Depends(get_db)):
    """Get frameworks that an organization can seed from."""
    try:
        # Check if there are any permissions set for this organization
        existing_permissions = db.query(models.OrganizationFrameworkPermissions).filter(
            models.OrganizationFrameworkPermissions.organization_id == organization_id
        ).first()

        if not existing_permissions:
            # If no permissions are set, return all frameworks (default behavior)
            all_frameworks = db.query(models.Framework).all()
            return [
                {
                    "id": str(framework.id),
                    "name": framework.name,
                    "description": framework.description,
                    "organisation_id": str(framework.organisation_id)
                }
                for framework in all_frameworks
            ]
        else:
            # Return only frameworks that have explicit permissions
            frameworks = db.query(models.Framework).join(
                models.OrganizationFrameworkPermissions,
                and_(
                    models.Framework.id == models.OrganizationFrameworkPermissions.framework_id,
                    models.OrganizationFrameworkPermissions.organization_id == organization_id,
                    models.OrganizationFrameworkPermissions.can_seed == True
                )
            ).all()

            return [
                {
                    "id": str(framework.id),
                    "name": framework.name,
                    "description": framework.description,
                    "organisation_id": str(framework.organisation_id)
                }
                for framework in frameworks
            ]

    except Exception as e:
        logger.error(f"Error getting seedable frameworks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get seedable frameworks: {str(e)}")

@router.post("/framework-template-permissions")
async def set_framework_template_permissions(request: FrameworkTemplatePermissionRequest, db: Session = Depends(get_db)):
    """Set which framework templates an organization can seed."""
    try:
        # All available templates
        all_templates = [
            {"id": "CRA", "name": "CRA"},
            {"id": "ISO_27001_2022", "name": "ISO 27001 2022"},
            {"id": "NIS2_DIRECTIVE", "name": "NIS2 Directive"}
        ]

        # Delete existing permissions for this organization
        db.query(models.OrganizationFrameworkPermissions).filter(
            models.OrganizationFrameworkPermissions.organization_id == request.organization_id
        ).delete()

        # For each selected template, find or create corresponding framework and add permission
        for template_id in request.template_ids:
            # Find framework with matching template name/id
            template_name = next((t["name"] for t in all_templates if t["id"] == template_id), template_id)

            framework = db.query(models.Framework).filter(
                models.Framework.name == template_name
            ).first()

            if framework:
                permission = models.OrganizationFrameworkPermissions(
                    organization_id=request.organization_id,
                    framework_id=framework.id,
                    can_seed=True
                )
                db.add(permission)

        db.commit()
        return {"message": "Framework template permissions updated successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error setting framework template permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update framework template permissions: {str(e)}")

@router.get("/framework-template-permissions/{organization_id}")
async def get_framework_template_permissions(organization_id: str, db: Session = Depends(get_db)):
    """Get framework template permissions for an organization."""
    try:
        # All available templates
        all_templates = [
            {"id": "CRA", "name": "CRA"},
            {"id": "ISO_27001_2022", "name": "ISO 27001 2022"},
            {"id": "NIS2_DIRECTIVE", "name": "NIS2 Directive"}
        ]

        # Check if there are any permissions set for this organization
        existing_permissions = db.query(models.OrganizationFrameworkPermissions).filter(
            models.OrganizationFrameworkPermissions.organization_id == organization_id
        ).first()

        if not existing_permissions:
            # No permissions set - default to all templates allowed
            return [template["id"] for template in all_templates]

        # Get frameworks that are allowed for seeding
        allowed_frameworks = db.query(models.Framework).join(
            models.OrganizationFrameworkPermissions,
            and_(
                models.Framework.id == models.OrganizationFrameworkPermissions.framework_id,
                models.OrganizationFrameworkPermissions.organization_id == organization_id,
                models.OrganizationFrameworkPermissions.can_seed == True
            )
        ).all()

        # Map framework names back to template IDs
        allowed_template_ids = []
        for framework in allowed_frameworks:
            for template in all_templates:
                if template["name"] == framework.name or template["id"] == framework.name:
                    allowed_template_ids.append(template["id"])
                    break

        return allowed_template_ids

    except Exception as e:
        logger.error(f"Error getting framework template permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get framework template permissions: {str(e)}")

@router.post("/domain-blacklist")
async def add_domain_to_blacklist(
    request: DomainBlacklistRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Add a domain to the blacklist (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can manage domain blacklist")

    try:
        # Check if domain is already in blacklist
        existing = db.query(models.DomainBlacklist).filter(
            models.DomainBlacklist.domain == request.domain
        ).first()

        if existing:
            # Update existing entry
            existing.is_blacklisted = True
            existing.reason = request.reason
            existing.blacklisted_by = current_user.id
            existing.updated_at = func.now()
        else:
            # Create new entry
            blacklist_entry = models.DomainBlacklist(
                domain=request.domain,
                is_blacklisted=True,
                reason=request.reason,
                blacklisted_by=current_user.id
            )
            db.add(blacklist_entry)

        # Deactivate all users with this domain
        db.query(models.User).filter(
            models.User.email.like(f"%@{request.domain}")
        ).update({models.User.status: "inactive"})

        db.commit()
        return {"message": f"Domain {request.domain} has been blacklisted and all users deactivated"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding domain to blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to blacklist domain: {str(e)}")

@router.delete("/domain-blacklist/{domain}")
async def remove_domain_from_blacklist(
    domain: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Remove a domain from blacklist (whitelist it) - super admin only."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can manage domain blacklist")

    try:
        # Find blacklist entry
        blacklist_entry = db.query(models.DomainBlacklist).filter(
            models.DomainBlacklist.domain == domain
        ).first()

        if not blacklist_entry:
            raise HTTPException(status_code=404, detail="Domain not found in blacklist")

        # Update to whitelisted
        blacklist_entry.is_blacklisted = False
        blacklist_entry.updated_at = func.now()

        # Reactivate org_admin and super_admin users for this domain
        admin_roles = db.query(models.Role).filter(
            models.Role.role_name.in_(["org_admin", "super_admin"])
        ).all()

        if admin_roles:
            admin_role_ids = [role.id for role in admin_roles]
            db.query(models.User).filter(
                and_(
                    models.User.email.like(f"%@{domain}"),
                    models.User.role_id.in_(admin_role_ids)
                )
            ).update({models.User.status: "active"})

        db.commit()
        return {"message": f"Domain {domain} has been whitelisted and admin users reactivated"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error removing domain from blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to whitelist domain: {str(e)}")

@router.get("/domain-blacklist")
async def get_domain_blacklist(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all blacklisted domains (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can view domain blacklist")

    try:
        blacklisted_domains = db.query(models.DomainBlacklist).filter(
            models.DomainBlacklist.is_blacklisted == True
        ).all()

        return [
            {
                "id": str(entry.id),
                "domain": entry.domain,
                "is_blacklisted": entry.is_blacklisted,
                "reason": entry.reason,
                "blacklisted_by": str(entry.blacklisted_by),
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
            }
            for entry in blacklisted_domains
        ]

    except Exception as e:
        logger.error(f"Error getting domain blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get domain blacklist: {str(e)}")

@router.get("/domain-status/{domain}")
async def check_domain_status(domain: str, db: Session = Depends(get_db)):
    """Check if a domain is blacklisted (public endpoint for registration validation)."""
    try:
        blacklist_entry = db.query(models.DomainBlacklist).filter(
            and_(
                models.DomainBlacklist.domain == domain,
                models.DomainBlacklist.is_blacklisted == True
            )
        ).first()

        return {
            "domain": domain,
            "is_blacklisted": blacklist_entry is not None,
            "reason": blacklist_entry.reason if blacklist_entry else None
        }

    except Exception as e:
        logger.error(f"Error checking domain status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check domain status: {str(e)}")

@router.post("/domain-blacklist/bulk-csv")
async def bulk_blacklist_from_csv(
    file: UploadFile = File(...),
    reason: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Bulk add domains to blacklist from CSV file (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can manage domain blacklist")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    try:
        # Read CSV content
        content = await file.read()
        decoded_content = content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(decoded_content))

        stats = {
            "processed": 0,
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "errors": []
        }

        default_reason = reason or "Bulk upload from CSV"

        for row_num, row in enumerate(csv_reader, 1):
            if not row or not row[0].strip():  # Skip empty rows
                continue

            stats["processed"] += 1

            try:
                # Support both single column (domain only) and two column (domain, reason) format
                domain = row[0].strip().lower()
                row_reason = row[1].strip() if len(row) > 1 and row[1].strip() else default_reason

                # Basic domain validation
                if not domain or '@' in domain or ' ' in domain or not '.' in domain:
                    stats["errors"].append(f"Row {row_num}: Invalid domain format '{domain}'")
                    stats["skipped"] += 1
                    continue

                # Check if domain already exists
                existing = db.query(models.DomainBlacklist).filter(
                    models.DomainBlacklist.domain == domain
                ).first()

                if existing:
                    # Update existing entry
                    existing.is_blacklisted = True
                    existing.reason = row_reason
                    existing.blacklisted_by = current_user.id
                    existing.updated_at = func.now()
                    stats["updated"] += 1
                else:
                    # Create new entry
                    blacklist_entry = models.DomainBlacklist(
                        domain=domain,
                        is_blacklisted=True,
                        reason=row_reason,
                        blacklisted_by=current_user.id
                    )
                    db.add(blacklist_entry)
                    stats["added"] += 1

                # Deactivate all users with this domain
                affected_users = db.query(models.User).filter(
                    models.User.email.like(f"%@{domain}")
                ).update({models.User.status: "inactive"})

            except Exception as row_error:
                stats["errors"].append(f"Row {row_num}: {str(row_error)}")
                stats["skipped"] += 1
                logger.error(f"Error processing row {row_num}: {str(row_error)}")

        # Commit all changes
        db.commit()

        return {
            "message": "CSV processing completed",
            "stats": stats
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing CSV file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {str(e)}")
    finally:
        await file.close()

@router.get("/domain-blacklist/sample-csv")
async def download_sample_csv(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Download a sample CSV file for domain blacklist bulk upload (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can download sample CSV")

    # Create sample CSV content
    sample_data = [
        ["domain", "reason"],
        ["example.com", "Blocked due to security concerns"],
        ["malicious-domain.org", "Known phishing domain"],
        ["spam-source.net", ""],
        ["untrusted-site.info", "Policy violation"]
    ]

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(sample_data)
    csv_content = output.getvalue()
    output.close()

    # Create streaming response
    def generate():
        yield csv_content.encode('utf-8')

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=domain_blacklist_sample.csv"
        }
    )
@router.get("/llm")
async def get_llm_settings(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get global LLM settings."""
    try:
        # Get the first (and should be only) LLM settings record
        llm_settings = db.query(models.LLMSettings).first()

        if not llm_settings:
            raise HTTPException(status_code=404, detail="LLM settings not found")

        return {
            "id": str(llm_settings.id),
            "ai_enabled": llm_settings.ai_enabled if llm_settings.ai_enabled is not None else True,
            "ai_policy_aligner_enabled": llm_settings.ai_policy_aligner_enabled if hasattr(llm_settings, 'ai_policy_aligner_enabled') else False,
            "default_provider": llm_settings.default_provider or 'llamacpp',
            "custom_llm_url": llm_settings.custom_llm_url,
            "custom_llm_payload": llm_settings.custom_llm_payload,
            "max_questions_per_framework": llm_settings.max_questions_per_framework,
            "llm_timeout_seconds": llm_settings.llm_timeout_seconds,
            "min_confidence_threshold": llm_settings.min_confidence_threshold,
            "max_correlations": llm_settings.max_correlations,
            "created_at": llm_settings.created_at.isoformat() if llm_settings.created_at else None,
            "updated_at": llm_settings.updated_at.isoformat() if llm_settings.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LLM settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM settings: {str(e)}")


@router.put("/llm")
async def update_llm_settings(
    request: LLMSettingsRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update global LLM settings (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can update LLM settings")

    try:
        # Get the first (and should be only) LLM settings record
        llm_settings = db.query(models.LLMSettings).first()

        if not llm_settings:
            raise HTTPException(status_code=404, detail="LLM settings not found")

        # Update global AI settings
        if request.ai_enabled is not None:
            llm_settings.ai_enabled = request.ai_enabled
        if request.default_provider is not None:
            llm_settings.default_provider = request.default_provider
        # Update AI Policy Aligner global setting
        if request.ai_policy_aligner_enabled is not None:
            llm_settings.ai_policy_aligner_enabled = request.ai_policy_aligner_enabled

        # Update legacy/correlation fields if provided
        if request.custom_llm_url is not None:
            llm_settings.custom_llm_url = request.custom_llm_url
        if request.custom_llm_payload is not None:
            llm_settings.custom_llm_payload = request.custom_llm_payload
        if request.max_questions_per_framework is not None:
            llm_settings.max_questions_per_framework = request.max_questions_per_framework
        if request.llm_timeout_seconds is not None:
            llm_settings.llm_timeout_seconds = request.llm_timeout_seconds
        if request.min_confidence_threshold is not None:
            llm_settings.min_confidence_threshold = request.min_confidence_threshold
        if request.max_correlations is not None:
            llm_settings.max_correlations = request.max_correlations

        llm_settings.updated_at = func.now()

        db.commit()
        db.refresh(llm_settings)

        return {
            "id": str(llm_settings.id),
            "ai_enabled": llm_settings.ai_enabled if llm_settings.ai_enabled is not None else True,
            "ai_policy_aligner_enabled": llm_settings.ai_policy_aligner_enabled if hasattr(llm_settings, 'ai_policy_aligner_enabled') else False,
            "default_provider": llm_settings.default_provider or 'llamacpp',
            "custom_llm_url": llm_settings.custom_llm_url,
            "custom_llm_payload": llm_settings.custom_llm_payload,
            "max_questions_per_framework": llm_settings.max_questions_per_framework,
            "llm_timeout_seconds": llm_settings.llm_timeout_seconds,
            "min_confidence_threshold": llm_settings.min_confidence_threshold,
            "max_correlations": llm_settings.max_correlations,
            "created_at": llm_settings.created_at.isoformat() if llm_settings.created_at else None,
            "updated_at": llm_settings.updated_at.isoformat() if llm_settings.updated_at else None,
            "message": "LLM settings updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating LLM settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update LLM settings: {str(e)}")


@router.get("/scanners")
async def get_scanner_settings(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get global scanner settings."""
    try:
        # Get the first (and should be only) scanner settings record
        scanner_settings = db.query(models.ScannerSettings).first()

        if not scanner_settings:
            raise HTTPException(status_code=404, detail="Scanner settings not found")

        # Parse allowed_scanner_domains from JSON
        allowed_domains = []
        if scanner_settings.allowed_scanner_domains:
            try:
                allowed_domains = json.loads(scanner_settings.allowed_scanner_domains)
            except json.JSONDecodeError:
                logger.warning("Failed to parse allowed_scanner_domains, returning empty list")
                allowed_domains = []

        return {
            "id": str(scanner_settings.id),
            "scanners_enabled": scanner_settings.scanners_enabled,
            "allowed_scanner_domains": allowed_domains,
            "created_at": scanner_settings.created_at.isoformat() if scanner_settings.created_at else None,
            "updated_at": scanner_settings.updated_at.isoformat() if scanner_settings.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scanner settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scanner settings: {str(e)}")


@router.put("/scanners")
async def update_scanner_settings(
    request: ScannerSettingsRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update global scanner settings (super admin and org admin)."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can update scanner settings")

    try:
        # Get the first (and should be only) scanner settings record
        scanner_settings = db.query(models.ScannerSettings).first()

        if not scanner_settings:
            raise HTTPException(status_code=404, detail="Scanner settings not found")

        # Update scanner fields if provided
        if request.scanners_enabled is not None:
            scanner_settings.scanners_enabled = request.scanners_enabled
        if request.allowed_scanner_domains is not None:
            # Store as JSON string
            scanner_settings.allowed_scanner_domains = json.dumps(request.allowed_scanner_domains)

        scanner_settings.updated_at = func.now()

        db.commit()
        db.refresh(scanner_settings)

        # Parse allowed_scanner_domains for response
        allowed_domains = []
        if scanner_settings.allowed_scanner_domains:
            try:
                allowed_domains = json.loads(scanner_settings.allowed_scanner_domains)
            except json.JSONDecodeError:
                allowed_domains = []

        return {
            "id": str(scanner_settings.id),
            "scanners_enabled": scanner_settings.scanners_enabled,
            "allowed_scanner_domains": allowed_domains,
            "created_at": scanner_settings.created_at.isoformat() if scanner_settings.created_at else None,
            "updated_at": scanner_settings.updated_at.isoformat() if scanner_settings.updated_at else None,
            "message": "Scanner settings updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating scanner settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update scanner settings: {str(e)}")


# ===========================
# Super Admin Focused Mode
# ===========================

@router.get("/super-admin-focused-mode")
async def get_super_admin_focused_mode(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get the super admin focused mode setting."""
    try:
        llm_settings = db.query(models.LLMSettings).first()

        if not llm_settings:
            return {"super_admin_focused_mode": False}

        return {
            "super_admin_focused_mode": llm_settings.super_admin_focused_mode if hasattr(llm_settings, 'super_admin_focused_mode') and llm_settings.super_admin_focused_mode is not None else False
        }

    except Exception as e:
        logger.error(f"Error getting super admin focused mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get super admin focused mode: {str(e)}")


@router.put("/super-admin-focused-mode")
async def update_super_admin_focused_mode(
    request: SuperAdminFocusedModeRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update the super admin focused mode setting (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can update this setting")

    try:
        llm_settings = db.query(models.LLMSettings).first()

        if not llm_settings:
            raise HTTPException(status_code=404, detail="LLM settings not found")

        llm_settings.super_admin_focused_mode = request.super_admin_focused_mode
        llm_settings.updated_at = func.now()

        db.commit()
        db.refresh(llm_settings)

        return {
            "super_admin_focused_mode": llm_settings.super_admin_focused_mode,
            "message": "Super admin focused mode updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating super admin focused mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update super admin focused mode: {str(e)}")


# ===========================
# Organization LLM Settings
# ===========================

@router.get("/org-llm/{organisation_id}")
async def get_org_llm_settings(
    organisation_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get LLM settings for a specific organization."""
    # Check permission - user must be super_admin or belong to this org
    if current_user.role_name != 'super_admin' and str(current_user.organisation_id) != organisation_id:
        raise HTTPException(status_code=403, detail="You don't have permission to view this organization's LLM settings")

    try:
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == organisation_id
        ).first()

        if not org_settings:
            # Return default/empty settings if none configured
            return {
                "configured": False,
                "organisation_id": organisation_id,
                "message": "No custom LLM settings configured for this organization. Using global defaults."
            }

        # Helper function to mask API keys
        def mask_api_key(key):
            if key and len(key) > 4:
                return f"••••••••{key[-4:]}"
            elif key:
                return "••••••••"
            return None

        return {
            "configured": True,
            "id": str(org_settings.id),
            "organisation_id": str(org_settings.organisation_id),
            "llm_provider": org_settings.llm_provider,
            # QLON settings
            "qlon_url": org_settings.qlon_url,
            "qlon_api_key": mask_api_key(org_settings.qlon_api_key),
            "qlon_use_tools": org_settings.qlon_use_tools,
            # OpenAI (ChatGPT) settings
            "openai_api_key": mask_api_key(getattr(org_settings, 'openai_api_key', None)),
            "openai_model": getattr(org_settings, 'openai_model', None),
            "openai_base_url": getattr(org_settings, 'openai_base_url', None),
            # Anthropic (Claude) settings
            "anthropic_api_key": mask_api_key(getattr(org_settings, 'anthropic_api_key', None)),
            "anthropic_model": getattr(org_settings, 'anthropic_model', None),
            # X AI (Grok) settings
            "xai_api_key": mask_api_key(getattr(org_settings, 'xai_api_key', None)),
            "xai_model": getattr(org_settings, 'xai_model', None),
            "xai_base_url": getattr(org_settings, 'xai_base_url', None),
            # Google (Gemini) settings
            "google_api_key": mask_api_key(getattr(org_settings, 'google_api_key', None)),
            "google_model": getattr(org_settings, 'google_model', None),
            "is_enabled": org_settings.is_enabled,
            # AI Remediator settings
            "ai_remediator_enabled": org_settings.ai_remediator_enabled if hasattr(org_settings, 'ai_remediator_enabled') else False,
            "remediator_prompt_zap": org_settings.remediator_prompt_zap if hasattr(org_settings, 'remediator_prompt_zap') else None,
            "remediator_prompt_nmap": org_settings.remediator_prompt_nmap if hasattr(org_settings, 'remediator_prompt_nmap') else None,
            "created_at": org_settings.created_at.isoformat() if org_settings.created_at else None,
            "updated_at": org_settings.updated_at.isoformat() if org_settings.updated_at else None
        }

    except Exception as e:
        logger.error(f"Error getting org LLM settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization LLM settings: {str(e)}")


@router.put("/org-llm/{organisation_id}")
async def update_org_llm_settings(
    organisation_id: str,
    request: OrgLLMSettingsRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Create or update LLM settings for a specific organization (org_admin or super_admin)."""
    # Check permission - user must be super_admin or org_admin of this org
    if current_user.role_name == 'super_admin':
        pass  # Super admin can update any org
    elif current_user.role_name == 'org_admin' and str(current_user.organisation_id) == organisation_id:
        pass  # Org admin can update their own org
    else:
        raise HTTPException(status_code=403, detail="You don't have permission to update this organization's LLM settings")

    try:
        # Verify organization exists
        org = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check if settings already exist
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == organisation_id
        ).first()

        # Helper function to mask API keys
        def mask_api_key(key):
            if key and len(key) > 4:
                return f"••••••••{key[-4:]}"
            elif key:
                return "••••••••"
            return None

        if org_settings:
            # Update existing settings
            org_settings.llm_provider = request.llm_provider
            # QLON settings
            org_settings.qlon_url = request.qlon_url
            if request.qlon_api_key is not None:
                org_settings.qlon_api_key = request.qlon_api_key
            org_settings.qlon_use_tools = request.qlon_use_tools
            # OpenAI (ChatGPT) settings
            if request.openai_api_key is not None:
                org_settings.openai_api_key = request.openai_api_key
            org_settings.openai_model = request.openai_model
            org_settings.openai_base_url = request.openai_base_url
            # Anthropic (Claude) settings
            if request.anthropic_api_key is not None:
                org_settings.anthropic_api_key = request.anthropic_api_key
            org_settings.anthropic_model = request.anthropic_model
            # X AI (Grok) settings
            if request.xai_api_key is not None:
                org_settings.xai_api_key = request.xai_api_key
            org_settings.xai_model = request.xai_model
            org_settings.xai_base_url = request.xai_base_url
            # Google (Gemini) settings
            if request.google_api_key is not None:
                org_settings.google_api_key = request.google_api_key
            org_settings.google_model = request.google_model
            # Common settings
            org_settings.is_enabled = request.is_enabled if request.is_enabled is not None else True
            # AI Remediator settings
            if request.ai_remediator_enabled is not None:
                org_settings.ai_remediator_enabled = request.ai_remediator_enabled
            if request.remediator_prompt_zap is not None:
                org_settings.remediator_prompt_zap = request.remediator_prompt_zap.strip() if request.remediator_prompt_zap.strip() else None
            if request.remediator_prompt_nmap is not None:
                org_settings.remediator_prompt_nmap = request.remediator_prompt_nmap.strip() if request.remediator_prompt_nmap.strip() else None
            org_settings.updated_at = func.now()
        else:
            # Create new settings
            org_settings = models.OrganizationLLMSettings(
                organisation_id=organisation_id,
                llm_provider=request.llm_provider,
                # QLON settings
                qlon_url=request.qlon_url,
                qlon_api_key=request.qlon_api_key,
                qlon_use_tools=request.qlon_use_tools,
                # OpenAI (ChatGPT) settings
                openai_api_key=request.openai_api_key,
                openai_model=request.openai_model,
                openai_base_url=request.openai_base_url,
                # Anthropic (Claude) settings
                anthropic_api_key=request.anthropic_api_key,
                anthropic_model=request.anthropic_model,
                # X AI (Grok) settings
                xai_api_key=request.xai_api_key,
                xai_model=request.xai_model,
                xai_base_url=request.xai_base_url,
                # Google (Gemini) settings
                google_api_key=request.google_api_key,
                google_model=request.google_model,
                # Common settings
                is_enabled=request.is_enabled if request.is_enabled is not None else True,
                ai_remediator_enabled=request.ai_remediator_enabled if request.ai_remediator_enabled is not None else False,
                remediator_prompt_zap=request.remediator_prompt_zap.strip() if request.remediator_prompt_zap and request.remediator_prompt_zap.strip() else None,
                remediator_prompt_nmap=request.remediator_prompt_nmap.strip() if request.remediator_prompt_nmap and request.remediator_prompt_nmap.strip() else None
            )
            db.add(org_settings)

        db.commit()
        db.refresh(org_settings)

        return {
            "id": str(org_settings.id),
            "organisation_id": str(org_settings.organisation_id),
            "llm_provider": org_settings.llm_provider,
            # QLON settings
            "qlon_url": org_settings.qlon_url,
            "qlon_api_key": mask_api_key(org_settings.qlon_api_key),
            "qlon_use_tools": org_settings.qlon_use_tools,
            # OpenAI (ChatGPT) settings
            "openai_api_key": mask_api_key(getattr(org_settings, 'openai_api_key', None)),
            "openai_model": getattr(org_settings, 'openai_model', None),
            "openai_base_url": getattr(org_settings, 'openai_base_url', None),
            # Anthropic (Claude) settings
            "anthropic_api_key": mask_api_key(getattr(org_settings, 'anthropic_api_key', None)),
            "anthropic_model": getattr(org_settings, 'anthropic_model', None),
            # X AI (Grok) settings
            "xai_api_key": mask_api_key(getattr(org_settings, 'xai_api_key', None)),
            "xai_model": getattr(org_settings, 'xai_model', None),
            "xai_base_url": getattr(org_settings, 'xai_base_url', None),
            # Google (Gemini) settings
            "google_api_key": mask_api_key(getattr(org_settings, 'google_api_key', None)),
            "google_model": getattr(org_settings, 'google_model', None),
            "is_enabled": org_settings.is_enabled,
            "created_at": org_settings.created_at.isoformat() if org_settings.created_at else None,
            "updated_at": org_settings.updated_at.isoformat() if org_settings.updated_at else None,
            "message": "Organization LLM settings updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating org LLM settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update organization LLM settings: {str(e)}")


@router.delete("/org-llm/{organisation_id}")
async def delete_org_llm_settings(
    organisation_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete LLM settings for a specific organization (reverts to global defaults)."""
    # Check permission - user must be super_admin or org_admin of this org
    if current_user.role_name == 'super_admin':
        pass
    elif current_user.role_name == 'org_admin' and str(current_user.organisation_id) == organisation_id:
        pass
    else:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this organization's LLM settings")

    try:
        result = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == organisation_id
        ).delete()

        if result == 0:
            raise HTTPException(status_code=404, detail="No LLM settings found for this organization")

        db.commit()
        return {"message": "Organization LLM settings deleted. Organization will now use global defaults."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting org LLM settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete organization LLM settings: {str(e)}")


@router.get("/org-llm/effective/{organisation_id}")
async def get_effective_llm_settings(
    organisation_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get the effective LLM settings for an organization.
    This returns the org's custom settings if configured, otherwise the global defaults.
    Used by scanners to determine which LLM to use.
    """
    try:
        # First check global AI enabled status
        global_settings = db.query(models.LLMSettings).first()
        if not global_settings or not global_settings.ai_enabled:
            return {
                "ai_enabled": False,
                "message": "AI is globally disabled"
            }

        # Check for org-specific settings
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == organisation_id
        ).first()

        if org_settings and org_settings.is_enabled:
            # Use org-specific settings
            return {
                "ai_enabled": True,
                "source": "organization",
                "llm_provider": org_settings.llm_provider,
                "qlon_url": org_settings.qlon_url,
                "qlon_api_key": org_settings.qlon_api_key,
                "qlon_use_tools": org_settings.qlon_use_tools if org_settings.qlon_use_tools is not None else True
            }
        else:
            # Use global defaults
            return {
                "ai_enabled": True,
                "source": "global",
                "llm_provider": global_settings.default_provider or 'llamacpp',
                "qlon_url": None,
                "qlon_api_key": None,
                "qlon_use_tools": True
            }

    except Exception as e:
        logger.error(f"Error getting effective LLM settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get effective LLM settings: {str(e)}")


# ===========================
# AI Feature Settings
# ===========================

# Default prompts for AI Remediator
DEFAULT_ZAP_PROMPT = """You are a cybersecurity expert specializing in web application security.

Analyze the following OWASP ZAP scan results and provide detailed remediation guidance.

For each vulnerability, provide:
1. **Vulnerability Explanation**: Brief description of the security issue
2. **Risk Assessment**: Why this is a security concern
3. **Remediation Steps**: Specific, actionable steps to fix the vulnerability
4. **Code Examples**: Where applicable, provide secure code patterns
5. **Prevention**: How to prevent this in the future

ZAP Scan Results:
{scan_results}

Provide clear, structured guidance that developers can follow."""

DEFAULT_NMAP_PROMPT = """You are a network security expert specializing in infrastructure hardening.

Analyze the following Nmap scan results and provide detailed remediation guidance.

For each finding, provide:
1. **Service Analysis**: Explanation of the detected service
2. **Security Concerns**: Potential risks with open ports/services
3. **Remediation Steps**: Actions to secure or close unnecessary services
4. **Configuration Examples**: Firewall rules, service hardening
5. **Best Practices**: Industry-standard recommendations

Nmap Scan Results:
{scan_results}

Prioritize findings by risk level. Focus on practical improvements."""

DEFAULT_POLICY_ALIGNER_PROMPT = """You are an expert in cybersecurity compliance and policy management. Your task is to analyze policies and framework questions to identify which policy best addresses each question.

For each question, identify the most relevant policy based on:
1. Direct coverage of the question's requirements
2. Alignment with the question's security domain (access control, data protection, etc.)
3. Completeness of the policy in addressing the question

Return a JSON array with your alignments:
[
  {
    "question_id": "uuid",
    "policy_id": "uuid",
    "confidence_score": 85,
    "reasoning": "Brief explanation of why this policy addresses this question"
  }
]

Only include alignments with confidence >= 80. If no policy adequately addresses a question, omit it from the results."""


@router.get("/org-llm/{organisation_id}/ai-features")
async def get_ai_feature_settings(
    organisation_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get AI feature settings for a specific organization."""
    # Check permission - user must be super_admin or belong to this org
    if current_user.role_name != 'super_admin' and str(current_user.organisation_id) != organisation_id:
        raise HTTPException(status_code=403, detail="You don't have permission to view this organization's AI feature settings")

    try:
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == organisation_id
        ).first()

        if not org_settings:
            # Return defaults if no settings configured
            return {
                "ai_remediator_enabled": False,
                "remediator_prompt_zap": None,
                "remediator_prompt_nmap": None,
                "default_prompt_zap": DEFAULT_ZAP_PROMPT,
                "default_prompt_nmap": DEFAULT_NMAP_PROMPT,
                "ai_policy_aligner_enabled": False,
                "policy_aligner_prompt": None,
                "default_policy_aligner_prompt": DEFAULT_POLICY_ALIGNER_PROMPT
            }

        return {
            "ai_remediator_enabled": org_settings.ai_remediator_enabled if hasattr(org_settings, 'ai_remediator_enabled') else False,
            "remediator_prompt_zap": org_settings.remediator_prompt_zap if hasattr(org_settings, 'remediator_prompt_zap') else None,
            "remediator_prompt_nmap": org_settings.remediator_prompt_nmap if hasattr(org_settings, 'remediator_prompt_nmap') else None,
            "default_prompt_zap": DEFAULT_ZAP_PROMPT,
            "default_prompt_nmap": DEFAULT_NMAP_PROMPT,
            "ai_policy_aligner_enabled": org_settings.ai_policy_aligner_enabled if hasattr(org_settings, 'ai_policy_aligner_enabled') else False,
            "policy_aligner_prompt": org_settings.policy_aligner_prompt if hasattr(org_settings, 'policy_aligner_prompt') else None,
            "default_policy_aligner_prompt": DEFAULT_POLICY_ALIGNER_PROMPT
        }

    except Exception as e:
        logger.error(f"Error getting AI feature settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI feature settings: {str(e)}")


@router.put("/org-llm/{organisation_id}/ai-features")
async def update_ai_feature_settings(
    organisation_id: str,
    request: schemas.AIFeatureSettingsRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update AI feature settings for a specific organization (org_admin or super_admin)."""
    # Check permission - user must be super_admin or org_admin of this org
    if current_user.role_name == 'super_admin':
        pass  # Super admin can update any org
    elif current_user.role_name == 'org_admin' and str(current_user.organisation_id) == organisation_id:
        pass  # Org admin can update their own org
    else:
        raise HTTPException(status_code=403, detail="You don't have permission to update this organization's AI feature settings")

    try:
        # Verify organization exists
        org = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check if settings already exist
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == organisation_id
        ).first()

        if org_settings:
            # Update existing settings
            if request.ai_remediator_enabled is not None:
                org_settings.ai_remediator_enabled = request.ai_remediator_enabled
            if request.remediator_prompt_zap is not None:
                org_settings.remediator_prompt_zap = request.remediator_prompt_zap if request.remediator_prompt_zap.strip() else None
            if request.remediator_prompt_nmap is not None:
                org_settings.remediator_prompt_nmap = request.remediator_prompt_nmap if request.remediator_prompt_nmap.strip() else None
            # AI Policy Aligner settings
            if request.ai_policy_aligner_enabled is not None:
                org_settings.ai_policy_aligner_enabled = request.ai_policy_aligner_enabled
            if request.policy_aligner_prompt is not None:
                org_settings.policy_aligner_prompt = request.policy_aligner_prompt if request.policy_aligner_prompt.strip() else None
            org_settings.updated_at = func.now()
        else:
            # Create new settings with defaults
            org_settings = models.OrganizationLLMSettings(
                organisation_id=organisation_id,
                llm_provider='llamacpp',  # Default provider
                is_enabled=False,  # AI disabled by default
                ai_remediator_enabled=request.ai_remediator_enabled if request.ai_remediator_enabled is not None else False,
                remediator_prompt_zap=request.remediator_prompt_zap if request.remediator_prompt_zap and request.remediator_prompt_zap.strip() else None,
                remediator_prompt_nmap=request.remediator_prompt_nmap if request.remediator_prompt_nmap and request.remediator_prompt_nmap.strip() else None,
                ai_policy_aligner_enabled=request.ai_policy_aligner_enabled if request.ai_policy_aligner_enabled is not None else False,
                policy_aligner_prompt=request.policy_aligner_prompt if request.policy_aligner_prompt and request.policy_aligner_prompt.strip() else None
            )
            db.add(org_settings)

        db.commit()
        db.refresh(org_settings)

        return {
            "ai_remediator_enabled": org_settings.ai_remediator_enabled if hasattr(org_settings, 'ai_remediator_enabled') else False,
            "remediator_prompt_zap": org_settings.remediator_prompt_zap if hasattr(org_settings, 'remediator_prompt_zap') else None,
            "remediator_prompt_nmap": org_settings.remediator_prompt_nmap if hasattr(org_settings, 'remediator_prompt_nmap') else None,
            "default_prompt_zap": DEFAULT_ZAP_PROMPT,
            "default_prompt_nmap": DEFAULT_NMAP_PROMPT,
            "ai_policy_aligner_enabled": org_settings.ai_policy_aligner_enabled if hasattr(org_settings, 'ai_policy_aligner_enabled') else False,
            "policy_aligner_prompt": org_settings.policy_aligner_prompt if hasattr(org_settings, 'policy_aligner_prompt') else None,
            "default_policy_aligner_prompt": DEFAULT_POLICY_ALIGNER_PROMPT,
            "message": "AI feature settings updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating AI feature settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update AI feature settings: {str(e)}")


# ===========================
# SSO Settings
# ===========================

@router.get("/sso")
async def get_sso_settings(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Lightweight SSO status read for any authenticated user.
    Derives enabled/configured from the active config."""
    try:
        sso_settings = sso_repository.get_active_sso_config(db)

        if not sso_settings:
            return {
                "sso_enabled": False,
                "google_configured": False,
                "microsoft_configured": False,
            }

        google_configured = bool(sso_settings.google_client_id and sso_settings.google_client_secret)
        microsoft_configured = bool(sso_settings.microsoft_client_id and sso_settings.microsoft_client_secret)

        return {
            "sso_enabled": sso_settings.is_active and (google_configured or microsoft_configured),
            "google_configured": google_configured,
            "microsoft_configured": microsoft_configured,
        }

    except Exception as e:
        logger.error(f"Error getting SSO settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get SSO settings: {str(e)}")


@router.get("/sso-configs")
async def get_all_sso_configurations(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all SSO configurations (masked secrets, super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can view SSO configurations")

    try:
        configs = sso_repository.get_all_sso_configs(db)

        def mask_secret(val):
            if val and len(val) > 4:
                return f"{'*' * 8}{val[-4:]}"
            elif val:
                return "********"
            return ""

        return [
            {
                "id": str(c.id),
                "label": c.label,
                "google_client_id": c.google_client_id or "",
                "google_client_secret": mask_secret(c.google_client_secret),
                "google_configured": bool(c.google_client_id and c.google_client_secret),
                "microsoft_client_id": c.microsoft_client_id or "",
                "microsoft_client_secret": mask_secret(c.microsoft_client_secret),
                "microsoft_tenant_id": c.microsoft_tenant_id or "common",
                "microsoft_configured": bool(c.microsoft_client_id and c.microsoft_client_secret),
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in configs
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SSO configs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get SSO configurations: {str(e)}")


@router.post("/sso-config")
async def create_sso_configuration(
    request: SSOSettingsRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Create a new SSO configuration (super admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can create SSO configurations")

    try:
        config_data = {
            "label": request.label.strip() if request.label else None,
            "google_client_id": request.google_client_id if request.google_client_id else None,
            "google_client_secret": request.google_client_secret if request.google_client_secret else None,
            "microsoft_client_id": request.microsoft_client_id if request.microsoft_client_id else None,
            "microsoft_client_secret": request.microsoft_client_secret if request.microsoft_client_secret else None,
            "microsoft_tenant_id": request.microsoft_tenant_id if request.microsoft_tenant_id else "common",
        }

        sso_repository.create_sso_config(db, config_data)
        return {"message": "SSO configuration created successfully"}

    except Exception as e:
        logger.error(f"Error creating SSO config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create SSO configuration: {str(e)}")


@router.put("/sso-config/{config_id}")
async def update_sso_configuration(
    config_id: str,
    request: SSOSettingsRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update an existing SSO configuration (super admin only)."""
    import uuid as uuid_mod
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can update SSO configurations")

    try:
        config_data = {}
        if request.label is not None:
            config_data["label"] = request.label.strip() if request.label else None
        if request.google_client_id is not None:
            config_data["google_client_id"] = request.google_client_id if request.google_client_id else None
        if request.google_client_secret is not None:
            config_data["google_client_secret"] = request.google_client_secret if request.google_client_secret else None
        if request.microsoft_client_id is not None:
            config_data["microsoft_client_id"] = request.microsoft_client_id if request.microsoft_client_id else None
        if request.microsoft_client_secret is not None:
            config_data["microsoft_client_secret"] = request.microsoft_client_secret if request.microsoft_client_secret else None
        if request.microsoft_tenant_id is not None:
            config_data["microsoft_tenant_id"] = request.microsoft_tenant_id if request.microsoft_tenant_id else "common"

        config = sso_repository.update_sso_config(db, uuid_mod.UUID(config_id), config_data)
        if not config:
            raise HTTPException(status_code=404, detail="SSO configuration not found")
        return {"message": "SSO configuration updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating SSO config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update SSO configuration: {str(e)}")


@router.delete("/sso-config/{config_id}")
async def delete_sso_configuration(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete an SSO configuration (super admin only)."""
    import uuid as uuid_mod
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can delete SSO configurations")

    try:
        deleted = sso_repository.delete_sso_config(db, uuid_mod.UUID(config_id))
        if not deleted:
            raise HTTPException(status_code=404, detail="SSO configuration not found")
        return {"message": "SSO configuration deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SSO config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete SSO configuration: {str(e)}")


@router.put("/sso-config/{config_id}/activate")
async def activate_sso_configuration(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Set an SSO configuration as active (deactivates all others). Super admin only."""
    import uuid as uuid_mod
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can activate SSO configurations")

    try:
        config = sso_repository.set_active_sso_config(db, uuid_mod.UUID(config_id))
        if not config:
            raise HTTPException(status_code=404, detail="SSO configuration not found")
        return {"message": "SSO configuration activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating SSO config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to activate SSO configuration: {str(e)}")


@router.put("/sso-config/{config_id}/deactivate")
async def deactivate_sso_configuration(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Deactivate an SSO configuration. Super admin only."""
    import uuid as uuid_mod
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can deactivate SSO configurations")

    try:
        config = sso_repository.deactivate_sso_config(db, uuid_mod.UUID(config_id))
        if not config:
            raise HTTPException(status_code=404, detail="SSO configuration not found")
        return {"message": "SSO configuration deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating SSO config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate SSO configuration: {str(e)}")


# ===========================
# Organization CRA Mode
# ===========================

@router.get("/org-cra-mode/{organisation_id}")
async def get_org_cra_mode(
    organisation_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get CRA mode settings for an organization. Any authenticated user in the org can read."""
    # Check permission - user must be super_admin or belong to this org
    if current_user.role_name != 'super_admin' and str(current_user.organisation_id) != organisation_id:
        raise HTTPException(status_code=403, detail="You don't have permission to view this organization's CRA mode settings")

    try:
        org = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        return {
            "cra_mode": org.cra_mode,
            "cra_operator_role": org.cra_operator_role
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting org CRA mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization CRA mode: {str(e)}")


@router.put("/org-cra-mode/{organisation_id}")
async def update_org_cra_mode(
    organisation_id: str,
    request: OrgCRAModeRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update CRA mode settings for an organization (super_admin or org_admin of that org)."""
    if current_user.role_name == 'super_admin':
        pass
    elif current_user.role_name == 'org_admin' and str(current_user.organisation_id) == organisation_id:
        pass
    else:
        raise HTTPException(status_code=403, detail="You don't have permission to update this organization's CRA mode settings")

    try:
        org = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if request.cra_mode is not None:
            valid_modes = ['focused', 'extended']
            if request.cra_mode == '':
                org.cra_mode = None
                org.cra_operator_role = None
            elif request.cra_mode in valid_modes:
                org.cra_mode = request.cra_mode
            else:
                raise HTTPException(status_code=400, detail=f"Invalid CRA mode. Must be one of: {', '.join(valid_modes)}")

        if request.cra_operator_role is not None:
            # Validate operator role
            valid_roles = ['Manufacturer', 'Importer', 'Distributor']
            if request.cra_operator_role not in valid_roles and request.cra_operator_role != '':
                raise HTTPException(status_code=400, detail=f"Invalid operator role. Must be one of: {', '.join(valid_roles)}")
            org.cra_operator_role = request.cra_operator_role if request.cra_operator_role else None

        org.updated_at = func.now()
        db.commit()
        db.refresh(org)

        return {
            "cra_mode": org.cra_mode,
            "cra_operator_role": org.cra_operator_role,
            "message": "CRA mode settings updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating org CRA mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update organization CRA mode: {str(e)}")


# ===========================
# Login/Register Logo Management
# ===========================

class LoginLogoCreateRequest(BaseModel):
    name: str
    logo: str  # base64 data URL
    is_global: bool = False
    organisation_ids: List[str] = []

class LoginLogoUpdateRequest(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    is_global: Optional[bool] = None
    is_active: Optional[bool] = None
    organisation_ids: Optional[List[str]] = None

class LoginLogoResponse(BaseModel):
    id: str
    name: str
    logo: str
    is_global: bool
    is_active: bool
    organisation_ids: List[str]
    organisation_names: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]


def _build_logo_response(logo: models.LoginLogo, db: Session) -> dict:
    """Build response dict for a LoginLogo."""
    org_ids = [str(lo.organisation_id) for lo in logo.organisations]
    org_names = []
    if org_ids:
        orgs = db.query(models.Organisations).filter(models.Organisations.id.in_(org_ids)).all()
        org_names = [o.name for o in orgs]
    return {
        "id": str(logo.id),
        "name": logo.name,
        "logo": logo.logo,
        "is_global": logo.is_global,
        "is_active": logo.is_active,
        "organisation_ids": org_ids,
        "organisation_names": org_names,
        "created_at": logo.created_at.isoformat() if logo.created_at else None,
        "updated_at": logo.updated_at.isoformat() if logo.updated_at else None,
    }


@router.post("/login-logos")
async def create_login_logo(
    request: LoginLogoCreateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Create a new login/register page logo. Super admin only."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can manage login logos")

    try:
        import uuid as uuid_mod
        logo = models.LoginLogo(
            name=request.name,
            logo=request.logo,
            is_global=request.is_global,
            is_active=True,
            created_by=current_user.id,
        )
        db.add(logo)
        db.flush()

        if not request.is_global and request.organisation_ids:
            for org_id in request.organisation_ids:
                link = models.LoginLogoOrganisation(
                    logo_id=logo.id,
                    organisation_id=uuid_mod.UUID(org_id),
                )
                db.add(link)

        db.commit()
        db.refresh(logo)
        return _build_logo_response(logo, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating login logo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create login logo: {str(e)}")


@router.get("/login-logos")
async def get_login_logos(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """List all login logos with org assignments. Super admin only."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can view login logos")

    try:
        logos = db.query(models.LoginLogo).order_by(models.LoginLogo.created_at.desc()).all()
        return [_build_logo_response(l, db) for l in logos]

    except Exception as e:
        logger.error(f"Error listing login logos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list login logos: {str(e)}")


@router.put("/login-logos/{logo_id}")
async def update_login_logo(
    logo_id: str,
    request: LoginLogoUpdateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update a login logo. Super admin only."""
    import uuid as uuid_mod
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can manage login logos")

    try:
        logo = db.query(models.LoginLogo).filter(models.LoginLogo.id == uuid_mod.UUID(logo_id)).first()
        if not logo:
            raise HTTPException(status_code=404, detail="Login logo not found")

        if request.name is not None:
            logo.name = request.name
        if request.logo is not None:
            logo.logo = request.logo
        if request.is_global is not None:
            logo.is_global = request.is_global
        if request.is_active is not None:
            logo.is_active = request.is_active

        if request.organisation_ids is not None:
            # Replace all org links
            db.query(models.LoginLogoOrganisation).filter(
                models.LoginLogoOrganisation.logo_id == logo.id
            ).delete()
            if not logo.is_global:
                for org_id in request.organisation_ids:
                    link = models.LoginLogoOrganisation(
                        logo_id=logo.id,
                        organisation_id=uuid_mod.UUID(org_id),
                    )
                    db.add(link)

        db.commit()
        db.refresh(logo)
        return _build_logo_response(logo, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating login logo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update login logo: {str(e)}")


@router.delete("/login-logos/{logo_id}")
async def delete_login_logo(
    logo_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete a login logo. Super admin only. CASCADE cleans junction table."""
    import uuid as uuid_mod
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can manage login logos")

    try:
        logo = db.query(models.LoginLogo).filter(models.LoginLogo.id == uuid_mod.UUID(logo_id)).first()
        if not logo:
            raise HTTPException(status_code=404, detail="Login logo not found")

        db.delete(logo)
        db.commit()
        return {"message": "Login logo deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting login logo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete login logo: {str(e)}")
