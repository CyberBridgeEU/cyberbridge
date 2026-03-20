# scanner_history_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import uuid
from app.models import models
from typing import Optional, List


def create_scanner_history(
    db: Session,
    scanner_type: str,
    user_id: uuid.UUID,
    user_email: str,
    organisation_id: Optional[uuid.UUID],
    organisation_name: Optional[str],
    scan_target: str,
    scan_type: Optional[str],
    scan_config: Optional[str],
    results: str,
    summary: Optional[str],
    status: str = "completed",
    error_message: Optional[str] = None,
    scan_duration: Optional[float] = None
):
    """Create a new scanner history record"""
    db_history = models.ScannerHistory(
        scanner_type=scanner_type,
        user_id=user_id,
        user_email=user_email,
        organisation_id=organisation_id,
        organisation_name=organisation_name,
        scan_target=scan_target,
        scan_type=scan_type,
        scan_config=scan_config,
        results=results,
        summary=summary,
        status=status,
        error_message=error_message,
        scan_duration=scan_duration,
        timestamp=datetime.now()
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def get_scanner_history_by_id(db: Session, history_id: uuid.UUID):
    """Get a single scanner history record by ID"""
    return db.query(models.ScannerHistory).filter(models.ScannerHistory.id == history_id).first()


def get_all_scanner_history(
    db: Session,
    scanner_type: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    organisation_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0
):
    """Get all scanner history with optional filtering"""
    query = db.query(models.ScannerHistory).order_by(desc(models.ScannerHistory.timestamp))

    if scanner_type:
        query = query.filter(models.ScannerHistory.scanner_type == scanner_type)
    if user_id:
        query = query.filter(models.ScannerHistory.user_id == user_id)
    if organisation_id:
        query = query.filter(models.ScannerHistory.organisation_id == organisation_id)
    if status:
        query = query.filter(models.ScannerHistory.status == status)
    if from_date:
        query = query.filter(models.ScannerHistory.timestamp >= from_date)
    if to_date:
        query = query.filter(models.ScannerHistory.timestamp <= to_date)

    if limit:
        query = query.limit(limit).offset(offset)

    return query.all()


def get_scanner_history_by_scanner_type(
    db: Session,
    scanner_type: str,
    organisation_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None
):
    """Get scanner history filtered by scanner type"""
    query = db.query(models.ScannerHistory).filter(
        models.ScannerHistory.scanner_type == scanner_type
    ).order_by(desc(models.ScannerHistory.timestamp))

    if organisation_id:
        query = query.filter(models.ScannerHistory.organisation_id == organisation_id)

    if limit:
        query = query.limit(limit)

    return query.all()


def get_scanner_history_count(
    db: Session,
    scanner_type: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    organisation_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None
):
    """Get count of scanner history records with optional filtering"""
    query = db.query(func.count(models.ScannerHistory.id))

    if scanner_type:
        query = query.filter(models.ScannerHistory.scanner_type == scanner_type)
    if user_id:
        query = query.filter(models.ScannerHistory.user_id == user_id)
    if organisation_id:
        query = query.filter(models.ScannerHistory.organisation_id == organisation_id)
    if status:
        query = query.filter(models.ScannerHistory.status == status)

    return query.scalar()


def delete_scanner_history(db: Session, history_id: uuid.UUID):
    """Delete a scanner history record"""
    try:
        db_history = get_scanner_history_by_id(db, history_id)
        if db_history:
            db.delete(db_history)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e


def delete_old_scanner_history(db: Session, days: int, organisation_id: Optional[uuid.UUID] = None):
    """Delete scanner history records older than specified days"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = db.query(models.ScannerHistory).filter(models.ScannerHistory.timestamp < cutoff_date)

        if organisation_id:
            query = query.filter(models.ScannerHistory.organisation_id == organisation_id)

        deleted_count = query.delete()
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        raise e


def delete_all_scanner_history_by_type(
    db: Session,
    scanner_type: str,
    organisation_id: Optional[uuid.UUID] = None
):
    """Delete all scanner history records for a specific scanner type"""
    try:
        query = db.query(models.ScannerHistory).filter(
            models.ScannerHistory.scanner_type == scanner_type
        )

        if organisation_id:
            query = query.filter(models.ScannerHistory.organisation_id == organisation_id)

        deleted_count = query.delete()
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        raise e


def get_scanner_history_by_scanner_type_lightweight(
    db: Session,
    scanner_type: str,
    organisation_id: Optional[uuid.UUID] = None,
    limit: Optional[int] = None
):
    """
    Get scanner history filtered by scanner type with minimal data for listing.
    Includes results for severity extraction but these won't be sent to client.
    """
    query = db.query(
        models.ScannerHistory.id,
        models.ScannerHistory.scanner_type,
        models.ScannerHistory.user_id,
        models.ScannerHistory.user_email,
        models.ScannerHistory.organisation_id,
        models.ScannerHistory.organisation_name,
        models.ScannerHistory.scan_target,
        models.ScannerHistory.scan_type,
        models.ScannerHistory.scan_config,
        models.ScannerHistory.summary,
        models.ScannerHistory.results,  # Include for severity extraction
        models.ScannerHistory.status,
        models.ScannerHistory.error_message,
        models.ScannerHistory.scan_duration,
        models.ScannerHistory.timestamp,
        models.ScannerHistory.asset_id,
        models.Assets.name.label('asset_name')
    ).outerjoin(
        models.Assets, models.ScannerHistory.asset_id == models.Assets.id
    ).filter(
        models.ScannerHistory.scanner_type == scanner_type
    ).order_by(desc(models.ScannerHistory.timestamp))

    if organisation_id:
        query = query.filter(models.ScannerHistory.organisation_id == organisation_id)

    if limit:
        query = query.limit(limit)

    return query.all()


def update_scanner_history_asset(
    db: Session,
    history_id: uuid.UUID,
    asset_id: Optional[uuid.UUID]
):
    """Update the asset_id on a scanner history record"""
    db_history = get_scanner_history_by_id(db, history_id)
    if not db_history:
        return None
    db_history.asset_id = asset_id
    db.commit()
    db.refresh(db_history)
    return db_history
