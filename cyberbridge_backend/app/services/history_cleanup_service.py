"""
History Cleanup Service

Provides functionality to automatically clean up old history records based on
per-organization configuration settings.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models import models

logger = logging.getLogger(__name__)


def cleanup_history_for_organization(org_id: str, retention_days: int, db: Session) -> int:
    """
    Delete history records older than retention_days for a specific organization.

    Args:
        org_id: UUID of the organization
        retention_days: Number of days to retain history records
        db: Database session

    Returns:
        Number of records deleted
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Delete old history records for this organization
        deleted_count = db.query(models.History).filter(
            models.History.organisation_id == org_id,
            models.History.created_at < cutoff_date
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(
            f"Cleaned up {deleted_count} history records for organization {org_id} "
            f"older than {cutoff_date.isoformat()}"
        )

        return deleted_count

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cleanup history for organization {org_id}: {str(e)}")
        raise


def cleanup_all_organizations():
    """
    Run cleanup for all organizations that have cleanup enabled.
    This is the main function called by the scheduler.
    """
    db: Session = SessionLocal()
    total_deleted = 0

    try:
        # Get all organizations with cleanup enabled
        organizations = db.query(models.Organisations).filter(
            models.Organisations.history_cleanup_enabled == True
        ).all()

        logger.info(f"Starting history cleanup for {len(organizations)} organizations")

        for org in organizations:
            try:
                deleted = cleanup_history_for_organization(
                    org_id=str(org.id),
                    retention_days=org.history_retention_days,
                    db=db
                )
                total_deleted += deleted

            except Exception as e:
                logger.error(f"Failed to cleanup history for organization {org.id}: {str(e)}")
                continue

        logger.info(f"History cleanup completed. Total records deleted: {total_deleted}")

        return total_deleted

    except Exception as e:
        logger.error(f"History cleanup job failed: {str(e)}")
        raise

    finally:
        db.close()


def manual_cleanup_organization(org_id: str, db: Session) -> dict:
    """
    Manually trigger cleanup for a specific organization (for admin use).

    Args:
        org_id: UUID of the organization
        db: Database session

    Returns:
        Dictionary with cleanup results
    """
    try:
        # Get organization settings
        org = db.query(models.Organisations).filter(
            models.Organisations.id == org_id
        ).first()

        if not org:
            return {
                "success": False,
                "message": "Organization not found",
                "deleted_count": 0
            }

        deleted_count = cleanup_history_for_organization(
            org_id=org_id,
            retention_days=org.history_retention_days,
            db=db
        )

        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} old history records",
            "deleted_count": deleted_count,
            "retention_days": org.history_retention_days
        }

    except Exception as e:
        logger.error(f"Manual cleanup failed for organization {org_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Cleanup failed: {str(e)}",
            "deleted_count": 0
        }
