# risk_seeding_service.py
# Service to seed Common Risks for organizations

from sqlalchemy.orm import Session
import uuid
import logging
from typing import Optional

from ..models import models
from ..constants.risk_templates import COMMON_RISKS

logger = logging.getLogger(__name__)


def get_default_severity_id(db: Session, severity_name: str = "Medium") -> Optional[uuid.UUID]:
    """Get the default severity ID by name"""
    try:
        severity = db.query(models.RiskSeverity).filter(
            models.RiskSeverity.risk_severity_name.ilike(severity_name)
        ).first()
        return severity.id if severity else None
    except Exception as e:
        logger.error(f"Error getting severity by name '{severity_name}': {str(e)}")
        return None


def get_default_status_id(db: Session, status_name: str = "Accept") -> Optional[uuid.UUID]:
    """Get the default status ID by name"""
    try:
        status = db.query(models.RiskStatuses).filter(
            models.RiskStatuses.risk_status_name.ilike(status_name)
        ).first()
        return status.id if status else None
    except Exception as e:
        logger.error(f"Error getting status by name '{status_name}': {str(e)}")
        return None


def get_default_asset_category_id(db: Session, category_name: str = "Software") -> Optional[uuid.UUID]:
    """Get the default asset category ID by name, falling back to any available category"""
    try:
        asset_category = db.query(models.AssetCategories).filter(
            models.AssetCategories.name.ilike(category_name)
        ).first()
        if asset_category:
            return asset_category.id
        fallback = db.query(models.AssetCategories).order_by(models.AssetCategories.name.asc()).first()
        return fallback.id if fallback else None
    except Exception as e:
        logger.error(f"Error getting asset category by name '{category_name}': {str(e)}")
        return None


def seed_common_risks_for_organisation(
    db: Session,
    organisation_id: uuid.UUID,
    created_by_user_id: uuid.UUID = None
) -> dict:
    """
    Seed the 29 Common Risks for a given organisation.

    Args:
        db: Database session
        organisation_id: UUID of the organisation to seed risks for
        created_by_user_id: Optional UUID of the user creating the risks

    Returns:
        dict with created_count, failed_count, and any errors
    """
    created_count = 0
    errors = []

    try:
        # Get default IDs for severity, status, and product type
        medium_severity_id = get_default_severity_id(db, "Medium")
        accept_status_id = get_default_status_id(db, "Accept")
        software_asset_category_id = get_default_asset_category_id(db, "Software")

        if not medium_severity_id:
            errors.append("Could not find 'Medium' severity level")
            logger.error("Could not find 'Medium' severity level for risk seeding")
            return {"created_count": 0, "failed_count": len(COMMON_RISKS), "errors": errors}

        if not accept_status_id:
            errors.append("Could not find 'Accept' status")
            logger.error("Could not find 'Accept' status for risk seeding")
            return {"created_count": 0, "failed_count": len(COMMON_RISKS), "errors": errors}

        if not software_asset_category_id:
            errors.append("Could not find any asset category")
            logger.error("Could not find any asset category for risk seeding")
            return {"created_count": 0, "failed_count": len(COMMON_RISKS), "errors": errors}

        # Create each common risk
        for risk_data in COMMON_RISKS:
            try:
                db_risk = models.Risks(
                    asset_category_id=software_asset_category_id,
                    risk_code=risk_data.get("risk_code", ""),
                    risk_category_name=risk_data.get("risk_category_name", ""),
                    risk_category_description=risk_data.get("risk_category_description", ""),
                    risk_potential_impact=risk_data.get("risk_potential_impact", ""),
                    risk_control=risk_data.get("risk_control", ""),
                    likelihood=medium_severity_id,
                    residual_risk=medium_severity_id,
                    risk_severity_id=medium_severity_id,
                    risk_status_id=accept_status_id,
                    organisation_id=organisation_id,
                    scope_id=None,
                    scope_entity_id=None,
                    created_by=created_by_user_id,
                    last_updated_by=created_by_user_id
                )
                db.add(db_risk)
                created_count += 1
            except Exception as e:
                error_msg = f"Failed to create risk '{risk_data.get('risk_category_name', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Commit all risks at once
        if created_count > 0:
            db.commit()
            logger.info(f"Successfully seeded {created_count} common risks for organisation {organisation_id}")

        return {
            "created_count": created_count,
            "failed_count": len(errors),
            "errors": errors
        }

    except Exception as e:
        db.rollback()
        error_msg = f"Failed to seed common risks for organisation {organisation_id}: {str(e)}"
        logger.error(error_msg)
        return {
            "created_count": 0,
            "failed_count": len(COMMON_RISKS),
            "errors": [error_msg]
        }


def check_organisation_has_risks(db: Session, organisation_id: uuid.UUID) -> bool:
    """Check if an organisation already has any risks"""
    try:
        count = db.query(models.Risks).filter(
            models.Risks.organisation_id == organisation_id
        ).count()
        return count > 0
    except Exception as e:
        logger.error(f"Error checking if organisation {organisation_id} has risks: {str(e)}")
        return False


def seed_common_risks_if_empty(
    db: Session,
    organisation_id: uuid.UUID,
    created_by_user_id: uuid.UUID = None
) -> dict:
    """
    Seed common risks for an organisation only if it has no existing risks.

    Args:
        db: Database session
        organisation_id: UUID of the organisation
        created_by_user_id: Optional UUID of the user creating the risks

    Returns:
        dict with created_count, failed_count, errors, and skipped flag
    """
    if check_organisation_has_risks(db, organisation_id):
        logger.info(f"Organisation {organisation_id} already has risks, skipping seeding")
        return {
            "created_count": 0,
            "failed_count": 0,
            "errors": [],
            "skipped": True,
            "message": "Organisation already has risks"
        }

    result = seed_common_risks_for_organisation(db, organisation_id, created_by_user_id)
    result["skipped"] = False
    return result
