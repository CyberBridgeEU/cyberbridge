from sqlalchemy.orm import Session
from app.models import models
from typing import Optional, List
import uuid


def get_active_sso_config(db: Session) -> Optional[models.SSOSettings]:
    """Get the active SSO configuration"""
    return db.query(models.SSOSettings).filter(
        models.SSOSettings.is_active == True
    ).first()


def get_all_sso_configs(db: Session) -> List[models.SSOSettings]:
    """Get all SSO configurations"""
    return db.query(models.SSOSettings).order_by(
        models.SSOSettings.created_at.desc()
    ).all()


def create_sso_config(db: Session, sso_config_data: dict) -> models.SSOSettings:
    """Create a new SSO configuration (does not auto-activate)"""
    sso_config = models.SSOSettings(**sso_config_data)

    db.add(sso_config)
    db.commit()
    db.refresh(sso_config)

    return sso_config


def update_sso_config(db: Session, config_id: uuid.UUID, sso_config_data: dict) -> Optional[models.SSOSettings]:
    """Update an existing SSO configuration"""
    sso_config = db.query(models.SSOSettings).filter(
        models.SSOSettings.id == config_id
    ).first()

    if sso_config:
        for key, value in sso_config_data.items():
            setattr(sso_config, key, value)

        db.commit()
        db.refresh(sso_config)

    return sso_config


def delete_sso_config(db: Session, config_id: uuid.UUID) -> bool:
    """Delete an SSO configuration by ID"""
    sso_config = db.query(models.SSOSettings).filter(
        models.SSOSettings.id == config_id
    ).first()

    if sso_config:
        db.delete(sso_config)
        db.commit()
        return True
    return False


def set_active_sso_config(db: Session, config_id: uuid.UUID) -> Optional[models.SSOSettings]:
    """Set one SSO config as active, deactivate all others"""
    # Deactivate all
    db.query(models.SSOSettings).update({models.SSOSettings.is_active: False})

    # Activate the selected one
    sso_config = db.query(models.SSOSettings).filter(
        models.SSOSettings.id == config_id
    ).first()

    if sso_config:
        sso_config.is_active = True
        db.commit()
        db.refresh(sso_config)

    return sso_config


def deactivate_sso_config(db: Session, config_id: uuid.UUID) -> Optional[models.SSOSettings]:
    """Deactivate a specific SSO configuration"""
    sso_config = db.query(models.SSOSettings).filter(
        models.SSOSettings.id == config_id
    ).first()

    if sso_config:
        sso_config.is_active = False
        db.commit()
        db.refresh(sso_config)

    return sso_config
