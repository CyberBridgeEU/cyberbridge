# api_key_repository.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
import uuid
import logging

from app.models import models

logger = logging.getLogger(__name__)


def create_api_key(
    db: Session,
    user_id: uuid.UUID,
    organisation_id: uuid.UUID,
    key_hash: str,
    key_prefix: str,
    name: str,
    description: Optional[str] = None,
    scopes: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> models.ApiKey:
    api_key = models.ApiKey(
        user_id=user_id,
        organisation_id=organisation_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        description=description,
        scopes=scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def get_by_key_hash(db: Session, key_hash: str) -> Optional[models.ApiKey]:
    return (
        db.query(models.ApiKey)
        .filter(models.ApiKey.key_hash == key_hash, models.ApiKey.is_active == True)
        .first()
    )


def list_by_user(db: Session, user_id: uuid.UUID) -> List[models.ApiKey]:
    return (
        db.query(models.ApiKey)
        .filter(models.ApiKey.user_id == user_id)
        .order_by(models.ApiKey.created_at.desc())
        .all()
    )


def revoke(db: Session, key_id: uuid.UUID, revoked_by: uuid.UUID) -> Optional[models.ApiKey]:
    api_key = db.query(models.ApiKey).filter(models.ApiKey.id == key_id).first()
    if api_key:
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = revoked_by
        db.commit()
        db.refresh(api_key)
    return api_key


def update_last_used(db: Session, key_id: uuid.UUID) -> None:
    db.query(models.ApiKey).filter(models.ApiKey.id == key_id).update(
        {"last_used_at": datetime.utcnow()}
    )
    db.commit()
