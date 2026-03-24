import uuid
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.models import (
    RegulatorySource, RegulatoryMonitorSettings, RegulatoryScanRun,
    RegulatoryScanResult, RegulatoryChange
)

logger = logging.getLogger(__name__)


# ==================== Settings ====================

def get_settings(db: Session) -> Optional[RegulatoryMonitorSettings]:
    return db.query(RegulatoryMonitorSettings).first()


def create_default_settings(db: Session) -> RegulatoryMonitorSettings:
    settings = RegulatoryMonitorSettings(
        id=uuid.uuid4(),
        scan_frequency="weekly",
        scan_day_of_week="mon",
        scan_hour=4,
        searxng_url="http://searxng:8080",
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(settings)
    db.flush()
    return settings


def update_settings(db: Session, settings_data: dict) -> RegulatoryMonitorSettings:
    settings = get_settings(db)
    if not settings:
        settings = create_default_settings(db)

    for key, value in settings_data.items():
        if hasattr(settings, key) and key not in ("id", "created_at"):
            setattr(settings, key, value)
    settings.updated_at = datetime.utcnow()
    db.flush()
    return settings


# ==================== Sources ====================

def get_sources(db: Session, framework_type: str = None, enabled_only: bool = False) -> List[RegulatorySource]:
    query = db.query(RegulatorySource)
    if framework_type:
        query = query.filter(RegulatorySource.framework_type == framework_type)
    if enabled_only:
        query = query.filter(RegulatorySource.enabled == True)
    return query.order_by(RegulatorySource.framework_type, RegulatorySource.priority).all()


def get_source(db: Session, source_id: uuid.UUID) -> Optional[RegulatorySource]:
    return db.query(RegulatorySource).filter(RegulatorySource.id == source_id).first()


def create_source(db: Session, source_data: dict) -> RegulatorySource:
    source = RegulatorySource(
        id=uuid.uuid4(),
        **source_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(source)
    db.flush()
    return source


def update_source(db: Session, source_id: uuid.UUID, source_data: dict) -> Optional[RegulatorySource]:
    source = get_source(db, source_id)
    if not source:
        return None
    for key, value in source_data.items():
        if hasattr(source, key) and key not in ("id", "created_at"):
            setattr(source, key, value)
    source.updated_at = datetime.utcnow()
    db.flush()
    return source


def delete_source(db: Session, source_id: uuid.UUID) -> bool:
    source = get_source(db, source_id)
    if not source:
        return False
    db.delete(source)
    db.flush()
    return True


# ==================== Scan Runs ====================

def create_scan_run(db: Session) -> RegulatoryScanRun:
    run = RegulatoryScanRun(
        id=uuid.uuid4(),
        status="running",
        started_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(run)
    db.flush()
    return run


def update_scan_run(db: Session, run_id: uuid.UUID, **kwargs) -> Optional[RegulatoryScanRun]:
    run = db.query(RegulatoryScanRun).filter(RegulatoryScanRun.id == run_id).first()
    if not run:
        return None
    for key, value in kwargs.items():
        if hasattr(run, key):
            setattr(run, key, value)
    db.flush()
    return run


def get_scan_runs(db: Session, limit: int = 20) -> List[RegulatoryScanRun]:
    return db.query(RegulatoryScanRun).order_by(desc(RegulatoryScanRun.created_at)).limit(limit).all()


def get_scan_run(db: Session, run_id: uuid.UUID) -> Optional[RegulatoryScanRun]:
    return db.query(RegulatoryScanRun).filter(RegulatoryScanRun.id == run_id).first()


def get_latest_completed_run(db: Session) -> Optional[RegulatoryScanRun]:
    return db.query(RegulatoryScanRun).filter(
        RegulatoryScanRun.status == "completed",
        RegulatoryScanRun.changes_found > 0
    ).order_by(desc(RegulatoryScanRun.completed_at)).first()


# ==================== Scan Results ====================

def create_scan_result(db: Session, result_data: dict) -> RegulatoryScanResult:
    result = RegulatoryScanResult(
        id=uuid.uuid4(),
        **result_data,
        created_at=datetime.utcnow()
    )
    db.add(result)
    db.flush()
    return result


def get_scan_results(db: Session, run_id: uuid.UUID, framework_type: str = None) -> List[RegulatoryScanResult]:
    query = db.query(RegulatoryScanResult).filter(RegulatoryScanResult.scan_run_id == run_id)
    if framework_type:
        query = query.filter(RegulatoryScanResult.framework_type == framework_type)
    return query.order_by(RegulatoryScanResult.fetched_at).all()


def get_previous_content_hash(db: Session, framework_type: str, source_name: str) -> Optional[str]:
    """Get the most recent content hash for dedup."""
    result = db.query(RegulatoryScanResult).filter(
        RegulatoryScanResult.framework_type == framework_type,
        RegulatoryScanResult.source_name == source_name,
        RegulatoryScanResult.content_hash.isnot(None)
    ).order_by(desc(RegulatoryScanResult.created_at)).first()
    return result.content_hash if result else None


# ==================== Changes ====================

def create_change(db: Session, change_data: dict) -> RegulatoryChange:
    change = RegulatoryChange(
        id=uuid.uuid4(),
        **change_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(change)
    db.flush()
    return change


def get_changes(
    db: Session,
    framework_type: str = None,
    status: str = None,
    scan_run_id: uuid.UUID = None,
    limit: int = 100
) -> List[RegulatoryChange]:
    query = db.query(RegulatoryChange)
    if framework_type:
        query = query.filter(RegulatoryChange.framework_type == framework_type)
    if status:
        query = query.filter(RegulatoryChange.status == status)
    if scan_run_id:
        query = query.filter(RegulatoryChange.scan_run_id == scan_run_id)
    return query.order_by(desc(RegulatoryChange.created_at)).limit(limit).all()


def get_change(db: Session, change_id: uuid.UUID) -> Optional[RegulatoryChange]:
    return db.query(RegulatoryChange).filter(RegulatoryChange.id == change_id).first()


def update_change(db: Session, change_id: uuid.UUID, **kwargs) -> Optional[RegulatoryChange]:
    change = get_change(db, change_id)
    if not change:
        return None
    for key, value in kwargs.items():
        if hasattr(change, key):
            setattr(change, key, value)
    change.updated_at = datetime.utcnow()
    db.flush()
    return change


def get_pending_changes_count_by_framework(db: Session) -> dict:
    """Get count of pending changes grouped by framework_type, plus latest scan run info."""
    results = db.query(
        RegulatoryChange.framework_type,
        RegulatoryChange.scan_run_id
    ).filter(
        RegulatoryChange.status == "pending"
    ).all()

    counts = {}
    for r in results:
        ft = r.framework_type
        if ft not in counts:
            counts[ft] = {"count": 0, "scan_run_id": str(r.scan_run_id)}
        counts[ft]["count"] += 1

    return counts


def get_new_findings_by_framework(db: Session) -> dict:
    """Get frameworks with new scan results from the latest completed run."""
    latest_run = get_latest_completed_run(db)
    if not latest_run:
        return {}

    results = db.query(RegulatoryScanResult.framework_type).filter(
        RegulatoryScanResult.scan_run_id == latest_run.id
    ).distinct().all()

    return {
        "scan_run_id": str(latest_run.id),
        "scan_date": latest_run.completed_at.isoformat() if latest_run.completed_at else None,
        "frameworks": [r.framework_type for r in results]
    }
