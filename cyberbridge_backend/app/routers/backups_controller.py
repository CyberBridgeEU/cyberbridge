# backups_controller.py
"""
Backup & Restore API Controller

Provides endpoints for managing organization backups:
- GET /backups/config/{org_id} - Get backup configuration
- PUT /backups/config/{org_id} - Update backup configuration
- GET /backups/list/{org_id} - List all backups for an organization
- POST /backups/create/{org_id} - Create a manual backup
- GET /backups/download/{backup_id} - Download a backup file
- POST /backups/restore/{org_id} - Restore from a backup
- DELETE /backups/{backup_id} - Delete a backup

Access: org_admin and super_admin roles only
"""
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dtos import schemas
from app.models import models
from app.repositories import backup_repository
from app.services import backup_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/backups", tags=["Backups"])


def _check_backup_permission(current_user: schemas.FullUserResponse, organisation_id: uuid.UUID):
    """
    Check if the current user has permission to access backup functionality.
    Only org_admin and super_admin roles are allowed.
    org_admin can only access their own organization's backups.
    """
    if current_user.role_name not in ['org_admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins and super admins can access backup functionality"
        )

    if current_user.role_name == 'org_admin' and current_user.organisation_id != organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access backups for your own organization"
        )


@router.get("/config/{org_id}", response_model=schemas.BackupConfigResponse)
def get_backup_config(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.FullUserResponse = Depends(get_current_user)
):
    """Get backup configuration for an organization"""
    organisation_id = uuid.UUID(org_id)
    _check_backup_permission(current_user, organisation_id)

    org = backup_repository.get_organisation_backup_config(db, organisation_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )

    return schemas.BackupConfigResponse(
        backup_enabled=org.backup_enabled,
        backup_frequency=org.backup_frequency,
        backup_retention_years=org.backup_retention_years,
        last_backup_at=org.last_backup_at,
        last_backup_status=org.last_backup_status
    )


@router.put("/config/{org_id}", response_model=schemas.BackupConfigResponse)
def update_backup_config(
    org_id: str,
    config: schemas.BackupConfigUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.FullUserResponse = Depends(get_current_user)
):
    """Update backup configuration for an organization"""
    organisation_id = uuid.UUID(org_id)
    _check_backup_permission(current_user, organisation_id)

    # Validate frequency if provided
    if config.backup_frequency and config.backup_frequency not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup frequency. Must be 'daily', 'weekly', or 'monthly'"
        )

    # Validate retention years if provided
    if config.backup_retention_years is not None:
        if config.backup_retention_years < 1 or config.backup_retention_years > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retention years must be between 1 and 100"
            )

    org = backup_repository.update_organisation_backup_config(
        db=db,
        organisation_id=organisation_id,
        backup_enabled=config.backup_enabled,
        backup_frequency=config.backup_frequency,
        backup_retention_years=config.backup_retention_years
    )

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )

    return schemas.BackupConfigResponse(
        backup_enabled=org.backup_enabled,
        backup_frequency=org.backup_frequency,
        backup_retention_years=org.backup_retention_years,
        last_backup_at=org.last_backup_at,
        last_backup_status=org.last_backup_status
    )


@router.get("/list/{org_id}", response_model=schemas.BackupListResponse)
def list_backups(
    org_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.FullUserResponse = Depends(get_current_user)
):
    """List all backups for an organization"""
    organisation_id = uuid.UUID(org_id)
    _check_backup_permission(current_user, organisation_id)

    backups = backup_repository.get_backups_for_organisation(db, organisation_id, skip, limit)
    total_count = backup_repository.get_backup_count_for_organisation(db, organisation_id)

    return schemas.BackupListResponse(
        backups=[schemas.BackupResponse.model_validate(b) for b in backups],
        total_count=total_count
    )


@router.post("/create/{org_id}", response_model=schemas.BackupResponse)
def create_backup(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.FullUserResponse = Depends(get_current_user)
):
    """Create a manual backup for an organization"""
    organisation_id = uuid.UUID(org_id)
    _check_backup_permission(current_user, organisation_id)

    try:
        backup = backup_service.create_backup_for_organisation(
            db=db,
            organisation_id=organisation_id,
            backup_type='manual',
            created_by=current_user.id
        )
        return schemas.BackupResponse.model_validate(backup)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )


@router.get("/download/{backup_id}")
def download_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.FullUserResponse = Depends(get_current_user)
):
    """Download a backup file"""
    backup_uuid = uuid.UUID(backup_id)
    backup = backup_repository.get_backup_by_id(db, backup_uuid)

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found"
        )

    _check_backup_permission(current_user, backup.organisation_id)

    filepath = Path(backup.filepath)
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found on server"
        )

    return FileResponse(
        path=filepath,
        filename=backup.filename,
        media_type='application/zip'
    )


@router.post("/restore/{org_id}", response_model=schemas.BackupRestoreResponse)
def restore_backup(
    org_id: str,
    request: schemas.BackupRestoreRequest,
    db: Session = Depends(get_db),
    current_user: schemas.FullUserResponse = Depends(get_current_user)
):
    """
    Restore organization data from a backup.

    IMPORTANT: This operation will replace existing organization data!
    You must set confirm=true to proceed with the restore.
    """
    organisation_id = uuid.UUID(org_id)
    _check_backup_permission(current_user, organisation_id)

    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must set confirm=true to proceed with restore. This operation will replace existing data!"
        )

    backup_uuid = uuid.UUID(request.backup_id)

    try:
        result = backup_service.restore_backup_for_organisation(
            db=db,
            organisation_id=organisation_id,
            backup_id=backup_uuid
        )
        return schemas.BackupRestoreResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )


@router.delete("/{backup_id}")
def delete_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.FullUserResponse = Depends(get_current_user)
):
    """Delete a backup file and record"""
    backup_uuid = uuid.UUID(backup_id)
    backup = backup_repository.get_backup_by_id(db, backup_uuid)

    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found"
        )

    _check_backup_permission(current_user, backup.organisation_id)

    success = backup_service.delete_backup_file(db, backup_uuid)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete backup"
        )

    return {"message": "Backup deleted successfully"}
