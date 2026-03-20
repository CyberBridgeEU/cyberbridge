# incident_patches_repository.py
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


def _compute_sla_compliance(patch):
    """Compute SLA compliance based on actual vs target dates."""
    if not patch.target_sla_date:
        return None
    if patch.actual_resolution_date:
        return "on_time" if patch.actual_resolution_date <= patch.target_sla_date else "overdue"
    now = datetime.utcnow()
    if now > patch.target_sla_date:
        return "overdue"
    # At risk if within 25% of remaining time
    total = (patch.target_sla_date - patch.created_at).total_seconds()
    elapsed = (now - patch.created_at).total_seconds()
    if total > 0 and elapsed / total > 0.75:
        return "at_risk"
    return "on_time"


def get_patches_for_incident(db: Session, incident_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        patches = db.query(models.IncidentPatches).filter(
            models.IncidentPatches.incident_id == incident_id
        ).order_by(models.IncidentPatches.created_at.desc()).all()
        for p in patches:
            p.sla_compliance = _compute_sla_compliance(p)
        return patches
    except Exception as e:
        logger.error(f"Error getting patches for incident {incident_id}: {str(e)}")
        return []


def create_patch(db: Session, incident_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        organisation_id = current_user.organisation_id if current_user else None

        # Inherit target SLA from incident if not provided
        target_sla_date = data.get("target_sla_date")
        if not target_sla_date:
            incident = db.query(models.Incidents).filter(models.Incidents.id == incident_id).first()
            if incident and incident.sla_deadline:
                target_sla_date = incident.sla_deadline

        patch = models.IncidentPatches(
            incident_id=incident_id,
            patch_version=data["patch_version"],
            description=data.get("description"),
            release_date=data.get("release_date"),
            target_sla_date=target_sla_date,
            actual_resolution_date=data.get("actual_resolution_date"),
            organisation_id=organisation_id,
            created_by=current_user.id if current_user else None,
        )
        db.add(patch)
        db.commit()
        db.refresh(patch)
        patch.sla_compliance = _compute_sla_compliance(patch)
        return patch
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating patch: {str(e)}")
        raise


def update_patch(db: Session, patch_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        patch = db.query(models.IncidentPatches).filter(models.IncidentPatches.id == patch_id).first()
        if not patch:
            return None

        for field in ["patch_version", "description", "release_date", "target_sla_date", "actual_resolution_date"]:
            if data.get(field) is not None:
                setattr(patch, field, data[field])

        db.commit()
        db.refresh(patch)
        patch.sla_compliance = _compute_sla_compliance(patch)
        return patch
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating patch {patch_id}: {str(e)}")
        raise


def delete_patch(db: Session, patch_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        patch = db.query(models.IncidentPatches).filter(models.IncidentPatches.id == patch_id).first()
        if not patch:
            return None
        db.delete(patch)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting patch {patch_id}: {str(e)}")
        raise
