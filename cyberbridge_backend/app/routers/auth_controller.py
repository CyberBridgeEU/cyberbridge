# routers/auth_router.py
from datetime import timedelta
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import logging
import random
import string

from ..database.database import get_db
from ..services.auth_service import authenticate_user, create_access_token, Token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, check_user_role
from ..services.security_service import get_password_hash
from ..services import sso_service, notification_service
from ..repositories import user_repository, user_verification_repository, smtp_repository, user_sessions_repository
from ..config.environment import get_api_base_url, get_environment_name
from ..dtos import schemas
from ..models import models
from sqlalchemy import and_

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    auth_result = authenticate_user(db, form_data.username, form_data.password)

    # Handle different authentication scenarios
    if auth_result["status"] == "user_not_found" or auth_result["status"] == "invalid_password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif auth_result["status"] == "sso_user":
        provider = auth_result["auth_provider"].capitalize()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account uses {provider} SSO. Please use the '{provider}' button to sign in."
        )
    elif auth_result["status"] == "user_not_approved":
        user_status = auth_result.get("user_status", "pending_approval")
        if user_status == "pending_approval":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is pending approval. Please wait for administrator approval before logging in."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is not active (Status: {user_status}). Please contact administrator."
            )
    elif auth_result["status"] != "success":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_result["user"]
    # Create token data with user email as subject and role
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email, "role": user.role_name},expires_delta=access_token_expires)

    # Create user session record
    import uuid
    user_id = uuid.UUID(str(user.id)) if not isinstance(user.id, uuid.UUID) else user.id
    user_sessions_repository.create_user_session(db, user_id, user.email)

    return {"access_token": access_token, "token_type": "bearer", "role": user.role_name, "must_change_password": user.must_change_password}

@router.get("/organisations", response_model=list[schemas.OrganisationResponse])
def get_organisations_for_registration(db: Session = Depends(get_db)):
    """Public endpoint to get all organisations for registration purposes"""
    try:
        organisations = user_repository.get_all_organisations_public(db)
        return organisations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching organisations: {str(e)}"
        )

@router.get("/roles", response_model=list[schemas.RoleResponse])
def get_roles_for_registration(db: Session = Depends(get_db)):
    """Public endpoint to get org_admin and org_user roles for registration purposes"""
    try:
        roles = user_repository.get_registration_roles(db)
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching roles: {str(e)}"
        )

@router.post("/check-org-admin")
def check_org_admin_exists(request: schemas.OnlyIdInStringFormat, db: Session = Depends(get_db)):
    """Public endpoint to check if an organisation already has an admin"""
    try:
        existing_admin = user_repository.get_org_admin(db, request.id)
        return {"has_admin": existing_admin is not None}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while checking org admin: {str(e)}"
        )

@router.get("/login-logo")
def get_login_logo(domain: str = None, db: Session = Depends(get_db)):
    """Public endpoint to resolve the login/register page logo.
    If domain is provided, tries org-specific logo first, then falls back to global.
    """
    try:
        # 1. If domain provided, find org-specific logo
        if domain:
            org = db.query(models.Organisations).filter(
                models.Organisations.domain == domain
            ).first()
            if org:
                # Find active logo linked to this org
                org_logo = (
                    db.query(models.LoginLogo)
                    .join(models.LoginLogoOrganisation, models.LoginLogo.id == models.LoginLogoOrganisation.logo_id)
                    .filter(
                        models.LoginLogoOrganisation.organisation_id == org.id,
                        models.LoginLogo.is_active == True,
                        models.LoginLogo.is_global == False,
                    )
                    .order_by(models.LoginLogo.created_at.asc())
                    .first()
                )
                if org_logo:
                    return {"logo": org_logo.logo, "name": org_logo.name}

        # 2. Fallback to global active logo
        global_logo = (
            db.query(models.LoginLogo)
            .filter(
                models.LoginLogo.is_global == True,
                models.LoginLogo.is_active == True,
            )
            .order_by(models.LoginLogo.created_at.asc())
            .first()
        )
        if global_logo:
            return {"logo": global_logo.logo, "name": global_logo.name}

        # 3. No match
        return {"logo": None, "name": None}

    except Exception as e:
        logger.error(f"Error resolving login logo: {str(e)}")
        return {"logo": None, "name": None}


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserRegistration, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        db_user = user_repository.get_user_by_email(db, email=str(user_data.email))
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check if domain is blacklisted
        email_domain = str(user_data.email).split('@')[1]
        blacklisted_domain = db.query(models.DomainBlacklist).filter(
            and_(
                models.DomainBlacklist.domain == email_domain,
                models.DomainBlacklist.is_blacklisted == True
            )
        ).first()

        if blacklisted_domain:
            reason = f" Reason: {blacklisted_domain.reason}" if blacklisted_domain.reason else ""
            raise HTTPException(
                status_code=400,
                detail=f"Registration not allowed for domain {email_domain}.{reason}"
            )
        
        # Check if role is valid (only org_admin and org_user allowed for registration)
        role = user_repository.get_role_by_id(db, user_data.role_id)
        if not role or role.role_name not in ['org_admin', 'org_user']:
            raise HTTPException(status_code=400, detail="Invalid role for registration")
        
        # Check if organisation exists
        organisation = user_repository.get_organisation_by_id(db, user_data.organisation_id)
        if not organisation:
            raise HTTPException(status_code=400, detail="Organisation not found")
        
        # If role is org_admin, check if org already has an admin
        if role.role_name == 'org_admin':
            existing_admin = user_repository.get_org_admin(db, user_data.organisation_id)
            if existing_admin:
                raise HTTPException(status_code=400, detail="Organisation already has an admin")
        
        # Create user with proper schema
        user_create_data = schemas.UserCreateInOrganisation(
            email=user_data.email,
            password=user_data.password,
            role_id=user_data.role_id,
            organisation_id=user_data.organisation_id
        )
        
        created_user = user_repository.create_user_in_organisation(db=db, user=user_create_data)
        
        # Convert UUIDs to strings for response
        response_data = {
            "id": str(created_user.id),
            "email": str(created_user.email),
            "role_id": str(created_user.role_id),
            "organisation_id": str(created_user.organisation_id),
            "status": created_user.status,
            "created_at": created_user.created_at,
            "updated_at": created_user.updated_at
        }
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )

@router.post("/register-with-verification", status_code=status.HTTP_201_CREATED)
def register_user_with_verification(user_data: schemas.UserVerificationRegistration, db: Session = Depends(get_db)):
    """Register a new user with email verification"""
    try:
        # Check if email already exists in users table
        db_user = user_repository.get_user_by_email(db, email=str(user_data.email))
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check if domain is blacklisted
        email_domain = str(user_data.email).split('@')[1]
        blacklisted_domain = db.query(models.DomainBlacklist).filter(
            and_(
                models.DomainBlacklist.domain == email_domain,
                models.DomainBlacklist.is_blacklisted == True
            )
        ).first()

        if blacklisted_domain:
            reason = f" Reason: {blacklisted_domain.reason}" if blacklisted_domain.reason else ""
            raise HTTPException(
                status_code=400,
                detail=f"Registration not allowed for domain {email_domain}.{reason}"
            )

        # Check if there's already a pending verification for this email
        existing_verification = user_verification_repository.get_verification_by_email(db, str(user_data.email))
        if existing_verification:
            raise HTTPException(status_code=400, detail="Verification email already sent. Please check your email or wait for it to expire.")
        
        # Hash the password using the same security service used throughout the app
        hashed_password = get_password_hash(user_data.password)
        
        # Create verification record
        verification = user_verification_repository.create_user_verification(
            db=db,
            email=str(user_data.email),
            hashed_password=hashed_password,
            expiry_hours=24
        )
        
        # Send verification email
        send_verification_email(db, str(user_data.email), str(verification.verification_key))
        
        return {"message": "Registration initiated. Please check your email for verification link."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in registration with verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )

def send_verification_email(db: Session, email: str, verification_key: str):
    """Send verification email to user"""
    api_base_url = get_api_base_url()
    verification_url = f"{api_base_url}/auth/verify-email?key={verification_key}"

    logger.info(f"Sending verification email to {email} from {get_environment_name()} environment with URL: {api_base_url}")

    html_content = f"""
    <html>
    <body>
    <h2>Welcome to CyberBridge!</h2>
    <p>Thank you for registering with CyberBridge. Please click the link below to verify your email address and complete your registration:</p>
    <p><a href="{verification_url}" style="background-color: #1890ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email Address</a></p>
    <p>Or copy and paste this link into your browser:</p>
    <p>{verification_url}</p>
    <p><strong>This verification link will expire in 24 hours.</strong></p>
    <hr>
    <p><small>If you did not request this registration, please ignore this email.</small></p>
    </body>
    </html>
    """

    success = notification_service.send_email(db, email, "CyberBridge Account Verification", html_content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email. Please contact administrator.")

@router.get("/verify-email")
def verify_email(key: str, db: Session = Depends(get_db)):
    """Verify email address and complete user registration"""
    try:
        # Get verification record
        verification = user_verification_repository.get_verification_by_key(db, key)
        if not verification:
            raise HTTPException(status_code=400, detail="Invalid or expired verification link")
        
        # Extract domain from email to determine organization
        email = verification.email
        email_domain = email.split('@')[1].lower()
        # Create a user-friendly organization name from the domain
        # e.g., "mycompany.com" -> "Mycompany" (capitalized, without TLD)
        org_name = email_domain.split('.')[0].capitalize()
        
        # Check if organization with this domain already exists
        existing_org = user_repository.get_organisation_by_domain(db, email_domain)
        
        if existing_org:
            # Organization exists, user gets org_user role
            organisation_id = existing_org.id
            role = user_repository.get_role_by_name(db, "org_user")
        else:
            # First user from this domain, create organization and make them org_admin
            org_data = {
                "name": org_name,
                "domain": email_domain
            }
            organisation = user_repository.create_organisation_from_dict(db, org_data)
            organisation_id = organisation.id
            role = user_repository.get_role_by_name(db, "org_admin")
        
        if not role:
            raise HTTPException(status_code=500, detail="Role configuration error")
        
        # Create user with pre-hashed password
        created_user = user_repository.create_user_with_hashed_password(
            db=db,
            email=email,
            hashed_password=verification.hashed_password,
            role_id=str(role.id),
            organisation_id=str(organisation_id)
        )
        
        # Delete the verification record
        user_verification_repository.delete_verification(db, verification.id)

        # Redirect to frontend success page
        from ..services.sso_service import FRONTEND_URL
        return RedirectResponse(
            url=f"{FRONTEND_URL}/verify-success?email={quote(email)}&organization={quote(org_name)}&role={quote(role.role_name)}"
        )

    except HTTPException as he:
        from ..services.sso_service import FRONTEND_URL
        error_msg = quote(he.detail if isinstance(he.detail, str) else "Verification failed")
        return RedirectResponse(url=f"{FRONTEND_URL}/verify-success?error={error_msg}")
    except Exception as e:
        logger.error(f"Error in email verification: {str(e)}")
        from ..services.sso_service import FRONTEND_URL
        error_msg = quote("An error occurred during verification. Please try again or contact support.")
        return RedirectResponse(url=f"{FRONTEND_URL}/verify-success?error={error_msg}")

@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification_email(request: schemas.ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification email for existing pending verification"""
    try:
        # Check if user already exists in users table
        db_user = user_repository.get_user_by_email(db, email=str(request.email))
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered and verified. Please try logging in.")

        # Check if there's a pending verification for this email
        existing_verification = user_verification_repository.get_verification_by_email(db, str(request.email))
        if not existing_verification:
            raise HTTPException(status_code=400, detail="No pending verification found for this email. Please register first.")

        # Update the expiration time to give user more time
        user_verification_repository.update_verification_expiration(db, existing_verification.id, expiry_hours=24)

        # Resend verification email with the same verification key
        send_verification_email(db, str(request.email), str(existing_verification.verification_key))

        return {"message": "Verification email has been resent successfully. Please check your email."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in resend verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while resending verification email: {str(e)}"
        )

def generate_temporary_password(length: int = 10) -> str:
    """Generate a secure temporary password"""
    # Mix of uppercase, lowercase, digits, and symbols
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%&"

    # Ensure at least one character from each category
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%&")
    ]

    # Fill the rest randomly
    for _ in range(length - 4):
        password.append(random.choice(characters))

    # Shuffle the password
    random.shuffle(password)
    return ''.join(password)

def send_temporary_password_email(db: Session, email: str, temporary_password: str):
    """Send temporary password email to user"""
    logger.info(f"Sending temporary password email to {email}")

    html_content = f"""
    <html>
    <body>
    <h2>CyberBridge Password Reset</h2>
    <p>You have requested a password reset for your CyberBridge account.</p>
    <p><strong>Your temporary password is:</strong></p>
    <p style="background-color: #f0f0f0; padding: 15px; font-family: monospace; font-size: 18px; border-radius: 5px; letter-spacing: 2px;">
        <strong>{temporary_password}</strong>
    </p>
    <p><strong>Next steps:</strong></p>
    <ol>
        <li>Log in to CyberBridge using this temporary password</li>
        <li>For security, we recommend changing this password in your account settings</li>
    </ol>
    <p><em>This temporary password will work immediately and does not expire.</em></p>
    <hr>
    <p><small>If you did not request this password reset, please contact your administrator immediately.</small></p>
    </body>
    </html>
    """

    success = notification_service.send_email(db, email, "CyberBridge - Temporary Password", html_content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send temporary password email. Please contact administrator.")

def send_invitation_email(db: Session, email: str, temporary_password: str):
    """Send invitation email to a newly created user with their temporary password"""
    from ..services.sso_service import FRONTEND_URL
    login_url = f"{FRONTEND_URL}/login"

    logger.info(f"Sending invitation email to {email}")

    html_content = f"""
    <html>
    <body>
    <h2>Welcome to CyberBridge!</h2>
    <p>You've been invited to join your organization on CyberBridge, a cybersecurity compliance platform.</p>
    <p><strong>Your login credentials:</strong></p>
    <table style="border-collapse: collapse; margin: 15px 0;">
        <tr>
            <td style="padding: 8px 15px; background-color: #f0f0f0; font-weight: bold;">Email</td>
            <td style="padding: 8px 15px; background-color: #f0f0f0;">{email}</td>
        </tr>
        <tr>
            <td style="padding: 8px 15px; background-color: #f9f9f9; font-weight: bold;">Temporary Password</td>
            <td style="padding: 8px 15px; background-color: #f9f9f9; font-family: monospace; font-size: 16px; letter-spacing: 1px;">{temporary_password}</td>
        </tr>
    </table>
    <p><a href="{login_url}" style="background-color: #5B9BD5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Log in to CyberBridge</a></p>
    <p><strong>Next steps:</strong></p>
    <ol>
        <li>Click the button above or go to <a href="{login_url}">{login_url}</a></li>
        <li>Sign in with your email and temporary password</li>
        <li>Change your password in account settings for security</li>
    </ol>
    <hr>
    <p><small>If you did not expect this invitation, please contact your organization administrator.</small></p>
    </body>
    </html>
    """

    success = notification_service.send_email(db, email, "You've been invited to CyberBridge", html_content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send invitation email. Please contact administrator.")

@router.post("/send-invitation", status_code=status.HTTP_200_OK)
def send_user_invitation(
    request: schemas.SendInvitationRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """Send invitation email with temporary password to a newly created user"""
    try:
        send_invitation_email(db, str(request.email), request.temporary_password)
        return {"message": "Invitation email sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation email."
        )

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send temporary password to user's email for password reset"""
    try:
        # Check if user exists and is active
        db_user = user_repository.get_user_by_email(db, email=str(request.email))
        if not db_user:
            # For security, don't reveal if email exists or not
            return {"message": "If the email address exists in our system, a temporary password has been sent."}

        # Only allow password reset for active users (approved accounts)
        if db_user.status != "active":
            return {"message": "If the email address exists in our system, a temporary password has been sent."}

        # Block password reset for SSO users
        if db_user.auth_provider != "local":
            return {"message": "If the email address exists in our system, a temporary password has been sent."}

        # Generate temporary password
        temporary_password = generate_temporary_password()

        # Update user password in database
        hashed_temp_password = get_password_hash(temporary_password)
        import uuid
        updated_user = user_repository.update_user_password_hash(db, uuid.UUID(str(db_user.id)), hashed_temp_password)

        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password. Please try again.")

        # Send temporary password via email
        send_temporary_password_email(db, str(request.email), temporary_password)

        return {"message": "If the email address exists in our system, a temporary password has been sent."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in forgot password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing password reset request."
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user and update session record with logout timestamp"""
    try:
        import uuid
        # Get the latest session for this user
        user_id = uuid.UUID(str(current_user.id)) if not isinstance(current_user.id, uuid.UUID) else current_user.id
        latest_session = user_sessions_repository.get_latest_user_session(db, user_id)

        # Update the session with logout timestamp if it doesn't have one already
        if latest_session and not latest_session.logout_timestamp:
            user_sessions_repository.update_user_session_logout(db, latest_session.id)

        # Clear last_activity so user immediately disappears from online users
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            db_user.last_activity = None
            db.commit()

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout."
        )


# ===========================
# SSO Endpoints
# ===========================

@router.get("/sso/providers")
def get_sso_providers(db: Session = Depends(get_db)):
    """Public endpoint to get SSO provider status (enabled + configured flags)"""
    return sso_service.get_provider_status(db)


@router.get("/sso/google/login")
def sso_google_login(db: Session = Depends(get_db)):
    """Redirect user to Google OAuth2 consent screen"""
    if "google" not in sso_service.get_available_providers(db):
        raise HTTPException(status_code=400, detail="Google SSO is not configured")

    api_base_url = get_api_base_url()
    redirect_uri = f"{api_base_url}/auth/sso/google/callback"
    state = sso_service.generate_state()
    auth_url = sso_service.create_google_auth_url(db, redirect_uri, state)
    return RedirectResponse(url=auth_url)


@router.get("/sso/google/callback")
def sso_google_callback(code: str, state: str = "", db: Session = Depends(get_db)):
    """Handle Google OAuth2 callback after user authenticates"""
    frontend_url = sso_service.FRONTEND_URL

    try:
        api_base_url = get_api_base_url()
        redirect_uri = f"{api_base_url}/auth/sso/google/callback"
        userinfo = sso_service.exchange_google_code(db, code, redirect_uri)
        email = userinfo["email"]

        return _handle_sso_callback(db, email, "google", frontend_url)

    except Exception as e:
        logger.error(f"Google SSO callback error: {str(e)}")
        error_msg = quote("Authentication failed. Please try again.")
        return RedirectResponse(url=f"{frontend_url}/sso/callback?error={error_msg}")


@router.get("/sso/microsoft/login")
def sso_microsoft_login(db: Session = Depends(get_db)):
    """Redirect user to Microsoft OAuth2 consent screen"""
    if "microsoft" not in sso_service.get_available_providers(db):
        raise HTTPException(status_code=400, detail="Microsoft SSO is not configured")

    api_base_url = get_api_base_url()
    redirect_uri = f"{api_base_url}/auth/sso/microsoft/callback"
    state = sso_service.generate_state()
    auth_url = sso_service.create_microsoft_auth_url(db, redirect_uri, state)
    return RedirectResponse(url=auth_url)


@router.get("/sso/microsoft/callback")
def sso_microsoft_callback(code: str, state: str = "", db: Session = Depends(get_db)):
    """Handle Microsoft OAuth2 callback after user authenticates"""
    frontend_url = sso_service.FRONTEND_URL

    try:
        api_base_url = get_api_base_url()
        redirect_uri = f"{api_base_url}/auth/sso/microsoft/callback"
        userinfo = sso_service.exchange_microsoft_code(db, code, redirect_uri)
        email = userinfo["email"]

        return _handle_sso_callback(db, email, "microsoft", frontend_url)

    except Exception as e:
        logger.error(f"Microsoft SSO callback error: {str(e)}")
        error_msg = quote("Authentication failed. Please try again.")
        return RedirectResponse(url=f"{frontend_url}/sso/callback?error={error_msg}")


def _handle_sso_callback(db: Session, email: str, provider: str, frontend_url: str):
    """Common SSO callback logic: look up user, validate, issue JWT or redirect with error."""
    import uuid as uuid_module

    user = user_repository.get_user_by_email(db, email=email)

    if not user:
        error_msg = quote("No account found for this email. Please contact your administrator.")
        return RedirectResponse(url=f"{frontend_url}/sso/callback?error={error_msg}")

    if user.auth_provider != provider:
        if user.auth_provider == "local":
            error_msg = quote("This account uses password login. Please sign in with your email and password.")
        else:
            error_msg = quote(f"This account uses {user.auth_provider.capitalize()} SSO. Please use the correct sign-in method.")
        return RedirectResponse(url=f"{frontend_url}/sso/callback?error={error_msg}")

    if user.status == "pending_approval":
        error_msg = quote("Your account is pending approval. Please wait for administrator approval.")
        return RedirectResponse(url=f"{frontend_url}/sso/callback?error={error_msg}")

    if user.status != "active":
        error_msg = quote(f"Your account is not active (Status: {user.status}). Please contact your administrator.")
        return RedirectResponse(url=f"{frontend_url}/sso/callback?error={error_msg}")

    # Issue JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role_name},
        expires_delta=access_token_expires
    )

    # Create user session record
    user_id = uuid_module.UUID(str(user.id)) if not isinstance(user.id, uuid_module.UUID) else user.id
    user_sessions_repository.create_user_session(db, user_id, user.email)

    return RedirectResponse(url=f"{frontend_url}/sso/callback?token={access_token}")