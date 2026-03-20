# scan_schedule_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import uuid
from app.models import models
from typing import Optional, List


def create_scan_schedule(
    db: Session,
    scanner_type: str,
    scan_target: str,
    scan_type: Optional[str],
    scan_config: Optional[str],
    schedule_type: str,
    interval_months: int,
    interval_days: int,
    interval_hours: int,
    interval_minutes: int,
    interval_seconds: int,
    cron_day_of_week: Optional[str],
    cron_hour: Optional[int],
    cron_minute: Optional[int],
    is_enabled: bool,
    user_id: uuid.UUID,
    user_email: str,
    organisation_id: Optional[uuid.UUID],
    organisation_name: Optional[str],
    next_run_at: Optional[datetime] = None
) -> models.ScanSchedule:
    """Create a new scan schedule"""
    schedule = models.ScanSchedule(
        scanner_type=scanner_type,
        scan_target=scan_target,
        scan_type=scan_type,
        scan_config=scan_config,
        schedule_type=schedule_type,
        interval_months=interval_months,
        interval_days=interval_days,
        interval_hours=interval_hours,
        interval_minutes=interval_minutes,
        interval_seconds=interval_seconds,
        cron_day_of_week=cron_day_of_week,
        cron_hour=cron_hour,
        cron_minute=cron_minute,
        is_enabled=is_enabled,
        user_id=user_id,
        user_email=user_email,
        organisation_id=organisation_id,
        organisation_name=organisation_name,
        next_run_at=next_run_at
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def get_schedule_by_id(db: Session, schedule_id: uuid.UUID) -> Optional[models.ScanSchedule]:
    """Get a scan schedule by ID"""
    return db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()


def get_all_schedules(
    db: Session,
    organisation_id: Optional[uuid.UUID] = None,
    scanner_type: Optional[str] = None,
    is_enabled: Optional[bool] = None
) -> List[models.ScanSchedule]:
    """Get all scan schedules with optional filtering"""
    query = db.query(models.ScanSchedule).order_by(desc(models.ScanSchedule.created_at))

    if organisation_id:
        query = query.filter(models.ScanSchedule.organisation_id == organisation_id)
    if scanner_type:
        query = query.filter(models.ScanSchedule.scanner_type == scanner_type)
    if is_enabled is not None:
        query = query.filter(models.ScanSchedule.is_enabled == is_enabled)

    return query.all()


def get_all_enabled_schedules(db: Session) -> List[models.ScanSchedule]:
    """Get all enabled schedules (for scheduler startup)"""
    return db.query(models.ScanSchedule).filter(
        models.ScanSchedule.is_enabled == True
    ).all()


def update_schedule(
    db: Session,
    schedule_id: uuid.UUID,
    **kwargs
) -> Optional[models.ScanSchedule]:
    """Update a scan schedule"""
    schedule = db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()
    if not schedule:
        return None

    for key, value in kwargs.items():
        if hasattr(schedule, key):
            setattr(schedule, key, value)

    schedule.updated_at = datetime.now()
    db.commit()
    db.refresh(schedule)
    return schedule


def update_last_run(
    db: Session,
    schedule_id: uuid.UUID,
    status: str,
    error: Optional[str] = None,
    next_run_at: Optional[datetime] = None
) -> Optional[models.ScanSchedule]:
    """Update last run status after a scheduled scan executes"""
    schedule = db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()
    if not schedule:
        return None

    schedule.last_run_at = datetime.now()
    schedule.last_status = status
    schedule.last_error = error
    schedule.run_count = (schedule.run_count or 0) + 1
    if next_run_at:
        schedule.next_run_at = next_run_at
    schedule.updated_at = datetime.now()
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, schedule_id: uuid.UUID) -> bool:
    """Delete a scan schedule"""
    schedule = db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()
    if not schedule:
        return False
    db.delete(schedule)
    db.commit()
    return True


def toggle_schedule(db: Session, schedule_id: uuid.UUID) -> Optional[models.ScanSchedule]:
    """Toggle a scan schedule's enabled state"""
    schedule = db.query(models.ScanSchedule).filter(models.ScanSchedule.id == schedule_id).first()
    if not schedule:
        return None

    schedule.is_enabled = not schedule.is_enabled
    schedule.updated_at = datetime.now()
    db.commit()
    db.refresh(schedule)
    return schedule
