# api_key_service.py
import hashlib
import secrets
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from datetime import datetime

from app.models import models
from app.repositories import api_key_repository


def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        (full_key, key_hash, key_prefix)

    Format: cb_<32_random_chars>
    """
    random_part = secrets.token_urlsafe(32)[:32]
    full_key = f"cb_{random_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:10]
    return full_key, key_hash, key_prefix


def hash_api_key(key: str) -> str:
    """Hash an API key for database lookup."""
    return hashlib.sha256(key.encode()).hexdigest()


def validate_api_key(db: Session, raw_key: str) -> Optional[models.User]:
    """
    Validate an API key and return the associated user if valid.

    Returns None if key is invalid, expired, or revoked.
    """
    key_hash = hash_api_key(raw_key)
    api_key = api_key_repository.get_by_key_hash(db, key_hash)

    if not api_key:
        return None

    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None

    # Update last used timestamp
    api_key_repository.update_last_used(db, api_key.id)

    return api_key.user
