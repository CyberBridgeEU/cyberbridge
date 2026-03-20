# backup_repository.py
from sqlalchemy.orm import Session
import uuid
from typing import Optional, List
from datetime import datetime
from app.models import models


def create_backup(
    db: Session,
    organisation_id: uuid.UUID,
    filename: str,
    filepath: str,
    file_size: int,
    expires_at: datetime,
    backup_type: str = 'scheduled',
    status: str = 'completed',
    error_message: Optional[str] = None,
    records_count: Optional[str] = None,
    evidence_files_count: Optional[int] = None,
    is_encrypted: bool = True,
    created_by: Optional[uuid.UUID] = None
) -> models.Backup:
    """Create a new backup record"""
    db_backup = models.Backup(
        organisation_id=organisation_id,
        filename=filename,
        filepath=filepath,
        file_size=file_size,
        backup_type=backup_type,
        status=status,
        error_message=error_message,
        records_count=records_count,
        evidence_files_count=evidence_files_count,
        is_encrypted=is_encrypted,
        created_by=created_by,
        expires_at=expires_at
    )
    db.add(db_backup)
    db.commit()
    db.refresh(db_backup)
    return db_backup


def get_backup_by_id(db: Session, backup_id: uuid.UUID) -> Optional[models.Backup]:
    """Get a backup record by ID"""
    return db.query(models.Backup).filter(models.Backup.id == backup_id).first()


def get_backups_for_organisation(
    db: Session,
    organisation_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> List[models.Backup]:
    """Get all backup records for an organization, ordered by created_at descending"""
    return (
        db.query(models.Backup)
        .filter(models.Backup.organisation_id == organisation_id)
        .order_by(models.Backup.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_backup_count_for_organisation(db: Session, organisation_id: uuid.UUID) -> int:
    """Get total count of backups for an organization"""
    return db.query(models.Backup).filter(
        models.Backup.organisation_id == organisation_id
    ).count()


def get_expired_backups(db: Session) -> List[models.Backup]:
    """Get all backups that have passed their expiration date"""
    return (
        db.query(models.Backup)
        .filter(models.Backup.expires_at < datetime.utcnow())
        .all()
    )


def delete_backup(db: Session, backup_id: uuid.UUID) -> bool:
    """Delete a backup record by ID. Returns True if deleted, False if not found."""
    backup = db.query(models.Backup).filter(models.Backup.id == backup_id).first()
    if backup:
        db.delete(backup)
        db.commit()
        return True
    return False


def update_backup_status(
    db: Session,
    backup_id: uuid.UUID,
    status: str,
    error_message: Optional[str] = None,
    records_count: Optional[str] = None,
    evidence_files_count: Optional[int] = None,
    file_size: Optional[int] = None
) -> Optional[models.Backup]:
    """Update the status and optional fields of a backup record"""
    backup = db.query(models.Backup).filter(models.Backup.id == backup_id).first()
    if backup:
        backup.status = status
        if error_message is not None:
            backup.error_message = error_message
        if records_count is not None:
            backup.records_count = records_count
        if evidence_files_count is not None:
            backup.evidence_files_count = evidence_files_count
        if file_size is not None:
            backup.file_size = file_size
        db.commit()
        db.refresh(backup)
    return backup


# Organization backup config functions
def get_organisation_backup_config(db: Session, organisation_id: uuid.UUID) -> Optional[models.Organisations]:
    """Get organization with backup configuration"""
    return db.query(models.Organisations).filter(
        models.Organisations.id == organisation_id
    ).first()


def update_organisation_backup_config(
    db: Session,
    organisation_id: uuid.UUID,
    backup_enabled: Optional[bool] = None,
    backup_frequency: Optional[str] = None,
    backup_retention_years: Optional[int] = None
) -> Optional[models.Organisations]:
    """Update organization backup configuration"""
    org = db.query(models.Organisations).filter(
        models.Organisations.id == organisation_id
    ).first()

    if org:
        if backup_enabled is not None:
            org.backup_enabled = backup_enabled
        if backup_frequency is not None:
            org.backup_frequency = backup_frequency
        if backup_retention_years is not None:
            org.backup_retention_years = backup_retention_years

        db.commit()
        db.refresh(org)

    return org


def update_organisation_last_backup(
    db: Session,
    organisation_id: uuid.UUID,
    last_backup_at: datetime,
    last_backup_status: str
) -> Optional[models.Organisations]:
    """Update the last backup timestamp and status for an organization"""
    org = db.query(models.Organisations).filter(
        models.Organisations.id == organisation_id
    ).first()

    if org:
        org.last_backup_at = last_backup_at
        org.last_backup_status = last_backup_status
        db.commit()
        db.refresh(org)

    return org


def get_organisations_due_for_backup(db: Session) -> List[models.Organisations]:
    """
    Get all organizations that are due for a scheduled backup.
    Checks backup_enabled and compares last_backup_at with backup_frequency.
    """
    from datetime import timedelta

    now = datetime.utcnow()
    orgs = db.query(models.Organisations).filter(
        models.Organisations.backup_enabled == True
    ).all()

    due_orgs = []
    for org in orgs:
        # If never backed up, it's due
        if org.last_backup_at is None:
            due_orgs.append(org)
            continue

        # Calculate when next backup is due based on frequency
        if org.backup_frequency == 'daily':
            next_backup = org.last_backup_at + timedelta(days=1)
        elif org.backup_frequency == 'weekly':
            next_backup = org.last_backup_at + timedelta(weeks=1)
        else:  # monthly (default)
            # Approximate a month as 30 days
            next_backup = org.last_backup_at + timedelta(days=30)

        if now >= next_backup:
            due_orgs.append(org)

    return due_orgs
