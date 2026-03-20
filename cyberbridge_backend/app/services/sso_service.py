# sso_service.py
import os
import secrets
import logging
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from ..models import models
from ..repositories import sso_repository
from ..config.environment import get_frontend_url

load_dotenv()

logger = logging.getLogger(__name__)

# Frontend URL for redirects (auto-detects environment)
FRONTEND_URL = get_frontend_url()

# Google endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Microsoft endpoints (tenant is dynamic, built per-request)
MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"


def get_sso_settings(db: Session):
    """Read the active SSO config from the database."""
    return sso_repository.get_active_sso_config(db)


def get_available_providers(db: Session) -> list[str]:
    """Return list of configured SSO providers based on active DB config."""
    settings = get_sso_settings(db)
    if not settings or not settings.is_active:
        return []

    providers = []
    if settings.google_client_id and settings.google_client_secret:
        providers.append("google")
    if settings.microsoft_client_id and settings.microsoft_client_secret:
        providers.append("microsoft")
    return providers


def get_provider_status(db: Session) -> dict:
    """Return SSO status for login page (enabled + per-provider configured flags)."""
    settings = get_sso_settings(db)
    if not settings:
        return {"sso_enabled": False, "google_configured": False, "microsoft_configured": False, "providers": []}

    google_configured = bool(settings.google_client_id and settings.google_client_secret)
    microsoft_configured = bool(settings.microsoft_client_id and settings.microsoft_client_secret)

    sso_enabled = settings.is_active and (google_configured or microsoft_configured)

    providers = []
    if sso_enabled:
        if google_configured:
            providers.append("google")
        if microsoft_configured:
            providers.append("microsoft")

    return {
        "sso_enabled": sso_enabled,
        "google_configured": google_configured,
        "microsoft_configured": microsoft_configured,
        "providers": providers,
    }


def generate_state() -> str:
    """Generate a random state string for CSRF protection."""
    return secrets.token_urlsafe(32)


def create_google_auth_url(db: Session, redirect_uri: str, state: str) -> str:
    """Build Google OAuth2 authorization URL with OIDC scopes."""
    settings = get_sso_settings(db)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    query = "&".join(f"{k}={httpx.URL('', params={k: v}).params[k]}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_google_code(db: Session, code: str, redirect_uri: str) -> dict:
    """Exchange Google auth code for tokens, then fetch userinfo.
    Returns {"email": ..., "name": ...} or raises an exception."""
    settings = get_sso_settings(db)
    with httpx.Client(timeout=30) as client:
        # Exchange code for tokens
        token_response = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_response.raise_for_status()
        tokens = token_response.json()

        # Fetch user info
        userinfo_response = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

    email = userinfo.get("email")
    name = userinfo.get("name", email.split("@")[0] if email else "")

    if not email:
        raise ValueError("Google did not return an email address")

    return {"email": email.lower(), "name": name}


def create_microsoft_auth_url(db: Session, redirect_uri: str, state: str) -> str:
    """Build Microsoft OAuth2 authorization URL."""
    settings = get_sso_settings(db)
    tenant_id = settings.microsoft_tenant_id or "common"
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"

    params = {
        "client_id": settings.microsoft_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile User.Read",
        "state": state,
        "response_mode": "query",
        "prompt": "select_account",
    }
    query = "&".join(f"{k}={httpx.URL('', params={k: v}).params[k]}" for k, v in params.items())
    return f"{auth_url}?{query}"


def exchange_microsoft_code(db: Session, code: str, redirect_uri: str) -> dict:
    """Exchange Microsoft auth code for tokens, then fetch profile via MS Graph.
    Returns {"email": ..., "name": ...} or raises an exception."""
    settings = get_sso_settings(db)
    tenant_id = settings.microsoft_tenant_id or "common"
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    with httpx.Client(timeout=30) as client:
        # Exchange code for tokens
        token_response = client.post(
            token_url,
            data={
                "code": code,
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "scope": "openid email profile User.Read",
            },
        )
        token_response.raise_for_status()
        tokens = token_response.json()

        # Fetch user profile from MS Graph
        profile_response = client.get(
            MICROSOFT_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        profile_response.raise_for_status()
        profile = profile_response.json()

    # Microsoft returns email in 'mail' or 'userPrincipalName'
    email = profile.get("mail") or profile.get("userPrincipalName")
    name = profile.get("displayName", email.split("@")[0] if email else "")

    if not email:
        raise ValueError("Microsoft did not return an email address")

    return {"email": email.lower(), "name": name}
