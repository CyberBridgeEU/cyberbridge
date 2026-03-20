# euvd_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.models import models


# ===========================
# EUVD Vulnerability CRUD
# ===========================

def _apply_days_filter(query, days: Optional[int] = None):
    """Apply a date_published filter for the last N days."""
    if days and days > 0:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(models.EUVDVulnerability.date_published >= cutoff)
    return query


def upsert_vulnerability(db: Session, data: Dict[str, Any]) -> tuple:
    """Insert or update a vulnerability by euvd_id. Returns (record, is_new)."""
    existing = db.query(models.EUVDVulnerability).filter(
        models.EUVDVulnerability.euvd_id == data["euvd_id"]
    ).first()

    if existing:
        for key, value in data.items():
            if key != "id" and key != "created_at":
                # For boolean flags, merge (OR) rather than overwrite
                if key in ("is_exploited", "is_critical") and value:
                    setattr(existing, key, True)
                else:
                    setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False
    else:
        record = models.EUVDVulnerability(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record, True


def get_exploited(db: Session, skip: int = 0, limit: int = 50, days: Optional[int] = None) -> List[models.EUVDVulnerability]:
    """Get exploited vulnerabilities."""
    query = db.query(models.EUVDVulnerability).filter(
        models.EUVDVulnerability.is_exploited == True
    )
    query = _apply_days_filter(query, days)
    return query.order_by(
        models.EUVDVulnerability.date_published.desc()
    ).offset(skip).limit(limit).all()


def get_exploited_count(db: Session, days: Optional[int] = None) -> int:
    query = db.query(func.count(models.EUVDVulnerability.id)).filter(
        models.EUVDVulnerability.is_exploited == True
    )
    query = _apply_days_filter(query, days)
    return query.scalar()


def get_critical(db: Session, skip: int = 0, limit: int = 50, days: Optional[int] = None) -> List[models.EUVDVulnerability]:
    """Get critical vulnerabilities."""
    query = db.query(models.EUVDVulnerability).filter(
        models.EUVDVulnerability.is_critical == True
    )
    query = _apply_days_filter(query, days)
    return query.order_by(
        models.EUVDVulnerability.date_published.desc()
    ).offset(skip).limit(limit).all()


def get_critical_count(db: Session, days: Optional[int] = None) -> int:
    query = db.query(func.count(models.EUVDVulnerability.id)).filter(
        models.EUVDVulnerability.is_critical == True
    )
    query = _apply_days_filter(query, days)
    return query.scalar()


def get_latest(db: Session, skip: int = 0, limit: int = 50, days: Optional[int] = None) -> List[models.EUVDVulnerability]:
    """Get latest vulnerabilities."""
    query = db.query(models.EUVDVulnerability)
    query = _apply_days_filter(query, days)
    return query.order_by(
        models.EUVDVulnerability.date_published.desc()
    ).offset(skip).limit(limit).all()


def get_latest_count(db: Session, days: Optional[int] = None) -> int:
    query = db.query(func.count(models.EUVDVulnerability.id))
    query = _apply_days_filter(query, days)
    return query.scalar()


def delete_all(db: Session) -> int:
    """Delete all cached vulnerabilities. Returns count deleted."""
    count = db.query(models.EUVDVulnerability).count()
    db.query(models.EUVDVulnerability).delete()
    db.commit()
    return count


def delete_by_date_range(db: Session, date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None) -> int:
    """Delete vulnerabilities within a date range (by date_published). Returns count deleted."""
    query = db.query(models.EUVDVulnerability)
    if date_from:
        query = query.filter(models.EUVDVulnerability.date_published >= date_from)
    if date_to:
        query = query.filter(models.EUVDVulnerability.date_published <= date_to)
    count = query.count()
    query.delete(synchronize_session='fetch')
    db.commit()
    return count


def get_stats(db: Session) -> Dict[str, Any]:
    """Get cache statistics."""
    total = db.query(func.count(models.EUVDVulnerability.id)).scalar()
    exploited = db.query(func.count(models.EUVDVulnerability.id)).filter(
        models.EUVDVulnerability.is_exploited == True
    ).scalar()
    critical = db.query(func.count(models.EUVDVulnerability.id)).filter(
        models.EUVDVulnerability.is_critical == True
    ).scalar()

    last_sync = db.query(models.EUVDSyncStatus).filter(
        models.EUVDSyncStatus.status == "completed"
    ).order_by(models.EUVDSyncStatus.completed_at.desc()).first()

    return {
        "total_cached": total,
        "exploited_count": exploited,
        "critical_count": critical,
        "last_sync_at": last_sync.completed_at.isoformat() if last_sync and last_sync.completed_at else None,
        "sync_status": last_sync.status if last_sync else None
    }


# ===========================
# EUVD Sync Status CRUD
# ===========================

def create_sync_status(db: Session, triggered_by: Optional[uuid.UUID] = None) -> models.EUVDSyncStatus:
    """Create a new sync status record."""
    sync_status = models.EUVDSyncStatus(
        status="pending",
        started_at=datetime.utcnow(),
        triggered_by=triggered_by
    )
    db.add(sync_status)
    db.commit()
    db.refresh(sync_status)
    return sync_status


def update_sync_status(db: Session, sync_id: uuid.UUID, status: str,
                       vulns_processed: int = 0, vulns_added: int = 0,
                       vulns_updated: int = 0, error_message: Optional[str] = None):
    """Update sync status record."""
    sync = db.query(models.EUVDSyncStatus).filter(models.EUVDSyncStatus.id == sync_id).first()
    if sync:
        sync.status = status
        sync.vulns_processed = vulns_processed
        sync.vulns_added = vulns_added
        sync.vulns_updated = vulns_updated
        if error_message:
            sync.error_message = error_message
        if status in ("completed", "failed"):
            sync.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(sync)
    return sync


def get_latest_sync_status(db: Session) -> Optional[models.EUVDSyncStatus]:
    """Get the most recent sync status."""
    return db.query(models.EUVDSyncStatus).order_by(
        models.EUVDSyncStatus.created_at.desc()
    ).first()


def is_sync_in_progress(db: Session) -> bool:
    """Check if a sync is currently running."""
    return db.query(models.EUVDSyncStatus).filter(
        models.EUVDSyncStatus.status.in_(["pending", "in_progress"])
    ).first() is not None


# ===========================
# EUVD Settings CRUD
# ===========================

def get_euvd_settings(db: Session) -> Optional[models.EUVDSettings]:
    """Get the single EUVD settings row."""
    return db.query(models.EUVDSettings).first()


def create_euvd_settings(db: Session) -> models.EUVDSettings:
    """Create default EUVD settings (enabled, 1hr interval)."""
    settings = models.EUVDSettings(
        sync_enabled=True,
        sync_interval_hours=1,
        sync_interval_seconds=0
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_euvd_settings(db: Session, sync_enabled: Optional[bool] = None,
                          sync_interval_hours: Optional[int] = None,
                          sync_interval_seconds: Optional[int] = None) -> Optional[models.EUVDSettings]:
    """Update EUVD settings fields."""
    settings = get_euvd_settings(db)
    if not settings:
        settings = create_euvd_settings(db)

    if sync_enabled is not None:
        settings.sync_enabled = sync_enabled
    if sync_interval_hours is not None:
        settings.sync_interval_hours = sync_interval_hours
    if sync_interval_seconds is not None:
        settings.sync_interval_seconds = sync_interval_seconds

    db.commit()
    db.refresh(settings)
    return settings


def get_sync_history(db: Session, limit: int = 20) -> List[models.EUVDSyncStatus]:
    """Get sync history ordered by created_at desc."""
    return db.query(models.EUVDSyncStatus).order_by(
        models.EUVDSyncStatus.created_at.desc()
    ).limit(limit).all()


def delete_all_sync_history(db: Session) -> int:
    """Delete all sync history records. Returns count deleted."""
    count = db.query(models.EUVDSyncStatus).count()
    db.query(models.EUVDSyncStatus).delete()
    db.commit()
    return count
