from sqlalchemy.orm import Session
from app.models import models
from typing import Optional
from datetime import datetime, timedelta
import uuid

def create_user_verification(db: Session, email: str, hashed_password: str, expiry_hours: int = 24) -> models.UserVerification:
    """Create a new user verification record"""
    verification = models.UserVerification(
        verification_key=uuid.uuid4(),
        email=email,
        hashed_password=hashed_password,
        expires_at=datetime.utcnow() + timedelta(hours=expiry_hours)
    )
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification

def get_verification_by_key(db: Session, verification_key: str) -> Optional[models.UserVerification]:
    """Get verification record by key"""
    try:
        key_uuid = uuid.UUID(verification_key)
        return db.query(models.UserVerification).filter(
            models.UserVerification.verification_key == key_uuid,
            models.UserVerification.expires_at > datetime.utcnow()
        ).first()
    except ValueError:
        return None

def delete_verification(db: Session, verification_id: uuid.UUID) -> None:
    """Delete a verification record"""
    db.query(models.UserVerification).filter(
        models.UserVerification.id == verification_id
    ).delete()
    db.commit()

def cleanup_expired_verifications(db: Session) -> int:
    """Clean up expired verification records"""
    count = db.query(models.UserVerification).filter(
        models.UserVerification.expires_at <= datetime.utcnow()
    ).delete()
    db.commit()
    return count

def get_verification_by_email(db: Session, email: str) -> Optional[models.UserVerification]:
    """Get active verification by email (to prevent duplicate registrations)"""
    return db.query(models.UserVerification).filter(
        models.UserVerification.email == email,
        models.UserVerification.expires_at > datetime.utcnow()
    ).first()

def update_verification_expiration(db: Session, verification_id: uuid.UUID, expiry_hours: int = 24) -> bool:
    """Update verification record expiration time"""
    updated = db.query(models.UserVerification).filter(
        models.UserVerification.id == verification_id
    ).update({
        'expires_at': datetime.utcnow() + timedelta(hours=expiry_hours)
    })
    db.commit()
    return updated > 0