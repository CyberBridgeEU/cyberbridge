# advisories_repository.py
from sqlalchemy.orm import Session
from datetime import datetime
import re
import uuid
import logging
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


def get_next_advisory_code(db: Session, organisation_id) -> str:
    """Generate next ADV-N code for the given organisation."""
    existing_codes = db.query(models.SecurityAdvisories.advisory_code).filter(
        models.SecurityAdvisories.organisation_id == organisation_id,
        models.SecurityAdvisories.advisory_code.isnot(None)
    ).all()

    max_n = 0
    for (code,) in existing_codes:
        match = re.match(r'^ADV-(\d+)$', code or '')
        if match:
            max_n = max(max_n, int(match.group(1)))

    return f"ADV-{max_n + 1}"


def _enrich_advisory(db: Session, advisory):
    """Add status_name and incident_code."""
    try:
        status = db.query(models.AdvisoryStatuses).filter(
            models.AdvisoryStatuses.id == advisory.advisory_status_id
        ).first()
        advisory.advisory_status_name = status.status_name if status else None

        if advisory.incident_id:
            incident = db.query(models.Incidents).filter(models.Incidents.id == advisory.incident_id).first()
            advisory.incident_code = incident.incident_code if incident else None
        else:
            advisory.incident_code = None
    except Exception as e:
        logger.error(f"Error enriching advisory {advisory.id}: {str(e)}")


def get_advisory_statuses(db: Session):
    return db.query(models.AdvisoryStatuses).all()


def get_advisories(db: Session, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.SecurityAdvisories)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.SecurityAdvisories.organisation_id == current_user.organisation_id)
        advisories = query.order_by(models.SecurityAdvisories.created_at.desc()).all()
        for adv in advisories:
            _enrich_advisory(db, adv)
        return advisories
    except Exception as e:
        logger.error(f"Error getting advisories: {str(e)}")
        return []


def get_advisory(db: Session, advisory_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.SecurityAdvisories).filter(models.SecurityAdvisories.id == advisory_id)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.SecurityAdvisories.organisation_id == current_user.organisation_id)
        advisory = query.first()
        if advisory:
            _enrich_advisory(db, advisory)
        return advisory
    except Exception as e:
        logger.error(f"Error getting advisory {advisory_id}: {str(e)}")
        return None


def create_advisory(db: Session, data: dict, current_user: schemas.UserBase = None):
    try:
        organisation_id = current_user.organisation_id if current_user else None
        advisory_code = get_next_advisory_code(db, organisation_id)

        advisory = models.SecurityAdvisories(
            advisory_code=advisory_code,
            title=data["title"],
            description=data.get("description"),
            affected_versions=data.get("affected_versions"),
            fixed_version=data.get("fixed_version"),
            severity=data.get("severity"),
            cve_ids=data.get("cve_ids"),
            workaround=data.get("workaround"),
            advisory_status_id=uuid.UUID(data["advisory_status_id"]),
            incident_id=uuid.UUID(data["incident_id"]) if data.get("incident_id") else None,
            organisation_id=organisation_id,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None,
        )

        # If status is "Published", set published_at
        status = db.query(models.AdvisoryStatuses).filter(
            models.AdvisoryStatuses.id == advisory.advisory_status_id
        ).first()
        if status and status.status_name == "Published":
            advisory.published_at = datetime.utcnow()

        db.add(advisory)
        db.commit()
        db.refresh(advisory)
        _enrich_advisory(db, advisory)
        return advisory
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating advisory: {str(e)}")
        raise


def update_advisory(db: Session, advisory_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        advisory = get_advisory(db, advisory_id, current_user)
        if not advisory:
            return None

        for field in ["title", "description", "affected_versions", "fixed_version",
                       "severity", "cve_ids", "workaround"]:
            if data.get(field) is not None:
                setattr(advisory, field, data[field])

        if data.get("advisory_status_id"):
            advisory.advisory_status_id = uuid.UUID(data["advisory_status_id"])
            # Check if now published
            status = db.query(models.AdvisoryStatuses).filter(
                models.AdvisoryStatuses.id == advisory.advisory_status_id
            ).first()
            if status and status.status_name == "Published" and not advisory.published_at:
                advisory.published_at = datetime.utcnow()

        if data.get("incident_id") is not None:
            advisory.incident_id = uuid.UUID(data["incident_id"]) if data["incident_id"] else None

        advisory.last_updated_by = current_user.id if current_user else None
        db.commit()
        db.refresh(advisory)
        _enrich_advisory(db, advisory)
        return advisory
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating advisory {advisory_id}: {str(e)}")
        raise


def delete_advisory(db: Session, advisory_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        advisory = get_advisory(db, advisory_id, current_user)
        if not advisory:
            return None
        db.delete(advisory)
        db.commit()
        return advisory
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting advisory {advisory_id}: {str(e)}")
        raise
