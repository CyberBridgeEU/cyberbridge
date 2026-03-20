# routers/api_keys_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.database.database import get_db
from app.services.auth_service import get_current_active_user
from app.services.api_key_service import generate_api_key
from app.repositories import api_key_repository
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.get("/")
def list_api_keys(
    current_user: schemas.UserBase = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all API keys for the current user."""
    keys = api_key_repository.list_by_user(db, current_user.id)
    return {
        "api_keys": [
            {
                "id": str(k.id),
                "name": k.name,
                "description": k.description,
                "key_prefix": k.key_prefix,
                "is_active": k.is_active,
                "scopes": k.scopes,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "revoked_at": k.revoked_at.isoformat() if k.revoked_at else None,
            }
            for k in keys
        ]
    }


@router.post("/")
def create_api_key(
    name: str = Query(description="Name for this API key"),
    description: Optional[str] = Query(default=None, description="Optional description"),
    expires_in_days: Optional[int] = Query(default=None, ge=1, le=365, description="Days until expiration (None = never)"),
    current_user: schemas.UserBase = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new API key. The full key is returned ONLY once — store it securely.
    """
    full_key, key_hash, key_prefix = generate_api_key()

    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    api_key = api_key_repository.create_api_key(
        db=db,
        user_id=current_user.id,
        organisation_id=current_user.organisation_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        description=description,
        expires_at=expires_at,
    )

    return {
        "message": "API key created. Copy the key now — it will not be shown again.",
        "api_key": full_key,
        "id": str(api_key.id),
        "name": api_key.name,
        "key_prefix": key_prefix,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }


@router.delete("/{key_id}")
def revoke_api_key(
    key_id: str,
    current_user: schemas.UserBase = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke an API key."""
    import uuid as _uuid

    try:
        key_uuid = _uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key ID format")

    api_key = api_key_repository.revoke(db, key_uuid, current_user.id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"message": "API key revoked", "id": str(api_key.id)}
