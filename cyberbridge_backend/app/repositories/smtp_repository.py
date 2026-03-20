from sqlalchemy.orm import Session
from app.models import models
from typing import Optional, List
import uuid

def get_active_smtp_config(db: Session) -> Optional[models.SMTPConfiguration]:
    """Get the active SMTP configuration"""
    return db.query(models.SMTPConfiguration).filter(
        models.SMTPConfiguration.is_active == True
    ).first()

def get_all_smtp_configs(db: Session) -> List[models.SMTPConfiguration]:
    """Get all SMTP configurations"""
    return db.query(models.SMTPConfiguration).order_by(
        models.SMTPConfiguration.created_at.desc()
    ).all()

def create_smtp_config(db: Session, smtp_config_data: dict) -> models.SMTPConfiguration:
    """Create a new SMTP configuration (does not auto-deactivate others)"""
    smtp_config = models.SMTPConfiguration(**smtp_config_data)

    db.add(smtp_config)
    db.commit()
    db.refresh(smtp_config)

    return smtp_config

def update_smtp_config(db: Session, config_id: uuid.UUID, smtp_config_data: dict) -> Optional[models.SMTPConfiguration]:
    """Update an existing SMTP configuration"""
    smtp_config = db.query(models.SMTPConfiguration).filter(
        models.SMTPConfiguration.id == config_id
    ).first()

    if smtp_config:
        for key, value in smtp_config_data.items():
            setattr(smtp_config, key, value)

        db.commit()
        db.refresh(smtp_config)

    return smtp_config

def delete_smtp_config(db: Session, config_id: uuid.UUID) -> bool:
    """Delete an SMTP configuration by ID"""
    smtp_config = db.query(models.SMTPConfiguration).filter(
        models.SMTPConfiguration.id == config_id
    ).first()

    if smtp_config:
        db.delete(smtp_config)
        db.commit()
        return True
    return False

def set_active_smtp_config(db: Session, config_id: uuid.UUID) -> Optional[models.SMTPConfiguration]:
    """Set one SMTP config as active, deactivate all others"""
    # Deactivate all
    db.query(models.SMTPConfiguration).update({models.SMTPConfiguration.is_active: False})

    # Activate the selected one
    smtp_config = db.query(models.SMTPConfiguration).filter(
        models.SMTPConfiguration.id == config_id
    ).first()

    if smtp_config:
        smtp_config.is_active = True
        db.commit()
        db.refresh(smtp_config)

    return smtp_config

def deactivate_smtp_config(db: Session, config_id: uuid.UUID) -> Optional[models.SMTPConfiguration]:
    """Deactivate a specific SMTP configuration"""
    smtp_config = db.query(models.SMTPConfiguration).filter(
        models.SMTPConfiguration.id == config_id
    ).first()

    if smtp_config:
        smtp_config.is_active = False
        db.commit()
        db.refresh(smtp_config)

    return smtp_config
