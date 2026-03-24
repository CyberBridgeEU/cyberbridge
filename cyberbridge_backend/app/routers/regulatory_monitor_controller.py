from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..services.regulatory_monitor_service import RegulatoryMonitorService
from ..services.seed_file_writer_service import SeedFileWriterService
from ..services.framework_snapshot_service import FrameworkSnapshotService
from ..repositories import regulatory_monitor_repository as repo
from ..dtos import regulatory_monitor_dtos as dtos
from ..dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/regulatory-monitor",
    tags=["regulatory-monitor"],
    responses={404: {"description": "Not found"}},
)


def _require_admin(current_user):
    """Require org_admin or super_admin role."""
    if current_user.role_name not in ["super_admin", "org_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org_admin and super_admin can access this resource"
        )


def _require_super_admin(current_user):
    """Require super_admin role."""
    if current_user.role_name != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can access this resource"
        )


# ==================== Settings ====================

@router.get("/settings", response_model=dtos.RegulatoryMonitorSettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_super_admin(current_user)
    settings = repo.get_settings(db)
    if not settings:
        settings = repo.create_default_settings(db)
        db.commit()
    return settings


@router.put("/settings", response_model=dtos.RegulatoryMonitorSettingsResponse)
def update_settings(
    settings_data: dtos.RegulatoryMonitorSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_super_admin(current_user)
    settings = repo.update_settings(db, settings_data.dict(exclude_unset=True))
    db.commit()
    return settings


# ==================== Sources ====================

@router.get("/sources", response_model=List[dtos.RegulatorySourceResponse])
def get_sources(
    framework_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_super_admin(current_user)
    return repo.get_sources(db, framework_type=framework_type)


@router.post("/sources", response_model=dtos.RegulatorySourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    source_data: dtos.RegulatorySourceCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_super_admin(current_user)
    source = repo.create_source(db, source_data.dict())
    db.commit()
    return source


@router.put("/sources/{source_id}", response_model=dtos.RegulatorySourceResponse)
def update_source(
    source_id: uuid.UUID,
    source_data: dtos.RegulatorySourceUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_super_admin(current_user)
    source = repo.update_source(db, source_id, source_data.dict(exclude_unset=True))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.commit()
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_super_admin(current_user)
    if not repo.delete_source(db, source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    db.commit()


# ==================== Scan Runs ====================

@router.post("/scan")
async def trigger_scan(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Trigger a manual regulatory web scan. Auto-enables the monitor if disabled."""
    _require_super_admin(current_user)

    # Auto-enable if disabled (manual trigger = user wants it to run)
    settings = repo.get_settings(db)
    if not settings:
        settings = repo.create_default_settings(db)
    if not settings.enabled:
        settings.enabled = True
        db.flush()
    db.commit()

    await RegulatoryMonitorService.run_web_scan()

    # Return latest scan run
    runs = repo.get_scan_runs(db, limit=1)
    if runs:
        return {
            "id": str(runs[0].id),
            "status": runs[0].status,
            "started_at": runs[0].started_at.isoformat() if runs[0].started_at else None,
            "completed_at": runs[0].completed_at.isoformat() if runs[0].completed_at else None,
            "frameworks_scanned": runs[0].frameworks_scanned,
            "changes_found": runs[0].changes_found,
            "error_message": runs[0].error_message
        }
    raise HTTPException(status_code=500, detail="Scan failed to create a run record")


@router.get("/scan-runs", response_model=List[dtos.ScanRunResponse])
def get_scan_runs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_admin(current_user)
    return repo.get_scan_runs(db, limit=limit)


@router.get("/scan-runs/{run_id}/results", response_model=List[dtos.ScanResultResponse])
def get_scan_results(
    run_id: uuid.UUID,
    framework_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_admin(current_user)
    return repo.get_scan_results(db, run_id, framework_type=framework_type)


# ==================== LLM Analysis ====================

@router.post("/analyze/{scan_run_id}/{framework_type}")
async def trigger_llm_analysis(
    scan_run_id: uuid.UUID,
    framework_type: str,
    body: Optional[dtos.LLMAnalysisRequest] = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Trigger LLM analysis for a specific framework's scan results.
    Calls the configured LLM to compare current framework content vs web findings.
    """
    _require_admin(current_user)

    # Verify scan run exists
    run = repo.get_scan_run(db, scan_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Scan run not found")

    if body and body.llm_response:
        # Parse and store pre-computed LLM response
        changes = RegulatoryMonitorService.store_llm_changes(
            db, scan_run_id, framework_type, body.llm_response
        )
        db.commit()
        return {"status": "completed", "changes_count": len(changes), "changes": changes}

    # Generate the analysis prompt
    result = RegulatoryMonitorService.run_llm_analysis(db, scan_run_id, framework_type)

    # If we got a prompt back, send it to the LLM automatically
    if isinstance(result, list) and len(result) == 1 and result[0].get("status") == "prompt_ready":
        prompt = result[0]["prompt"]
        try:
            from ..services.llm_service import LLMService
            llm_service = LLMService(db)
            llm_response = await llm_service.generate_text(prompt, timeout=600)

            # Parse the LLM response and store changes
            changes = RegulatoryMonitorService.store_llm_changes(
                db, scan_run_id, framework_type, llm_response
            )
            db.commit()
            return {"status": "completed", "changes_count": len(changes), "changes": changes}
        except Exception as e:
            logger.error(f"LLM analysis failed for {framework_type}: {e}")
            # Return the prompt so the user can try manually
            return {
                "status": "llm_error",
                "error": str(e),
                "prompt": prompt,
                "message": "Automatic LLM analysis failed. You can copy the prompt and run it manually."
            }

    return result


# ==================== Changes ====================

@router.get("/changes", response_model=List[dtos.RegulatoryChangeResponse])
def get_changes(
    framework_type: Optional[str] = None,
    change_status: Optional[str] = None,
    scan_run_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_admin(current_user)
    return repo.get_changes(db, framework_type=framework_type, status=change_status, scan_run_id=scan_run_id)


@router.get("/changes/{change_id}", response_model=dtos.RegulatoryChangeResponse)
def get_change(
    change_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_admin(current_user)
    change = repo.get_change(db, change_id)
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    return change


@router.put("/changes/{change_id}/review")
def review_change(
    change_id: uuid.UUID,
    review: dtos.ChangeReviewRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_admin(current_user)
    if review.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    change = repo.update_change(
        db, change_id,
        status=review.status,
        reviewed_by=uuid.UUID(current_user.id) if isinstance(current_user.id, str) else current_user.id,
        reviewed_at=datetime.utcnow()
    )
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    db.commit()
    return {"id": str(change.id), "status": change.status}


# ==================== Notifications ====================

@router.get("/notifications", response_model=dtos.NotificationResponse)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Check if there are new regulatory findings for the notification box."""
    _require_admin(current_user)

    findings = repo.get_new_findings_by_framework(db)
    pending = repo.get_pending_changes_count_by_framework(db)

    if findings:
        return {
            "has_findings": True,
            "scan_run_id": findings.get("scan_run_id"),
            "scan_date": findings.get("scan_date"),
            "frameworks": findings.get("frameworks", []),
            "pending_changes": pending
        }

    return {
        "has_findings": bool(pending),
        "scan_run_id": None,
        "scan_date": None,
        "frameworks": list(pending.keys()) if pending else [],
        "pending_changes": pending
    }


# ==================== Apply Changes ====================

@router.post("/changes/apply")
def apply_changes(
    request: dtos.ApplyChangesRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Apply approved regulatory changes to the org's framework DB."""
    _require_admin(current_user)

    user_id = uuid.UUID(current_user.id) if isinstance(current_user.id, str) else current_user.id

    try:
        result = RegulatoryMonitorService.apply_approved_changes(
            db, request.change_ids, request.framework_id, user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to apply changes: {str(e)}")


# ==================== Apply to Seed Templates ====================

@router.post("/changes/apply-to-seed")
def apply_to_seed(
    request: dtos.ApplyToSeedRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Generate and write a seed update Python file from approved changes (super_admin only)."""
    _require_super_admin(current_user)

    # Get approved changes
    changes = []
    for cid in request.change_ids:
        change = repo.get_change(db, cid)
        if change and change.status == "approved":
            changes.append(change)

    if not changes:
        raise HTTPException(status_code=400, detail="No approved changes found")

    try:
        # Determine next version
        version = SeedFileWriterService.get_next_version(request.framework_type)

        # Generate update file content
        content = SeedFileWriterService.generate_update_file(
            request.framework_type, version, changes, request.description
        )

        # Write to disk
        file_path = SeedFileWriterService.write_update_file(
            request.framework_type, version, content
        )

        # Validate
        valid = SeedFileWriterService.validate_update_file(file_path)

        # Mark changes as applied
        for change in changes:
            change.status = "applied"
            change.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "file_path": file_path,
            "version": version,
            "valid": valid,
            "changes_count": len(changes),
            "message": f"Seed update file written to {file_path}"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to write seed file: {str(e)}")


# ==================== Snapshot Endpoints ====================

@router.get("/frameworks/{framework_id}/snapshots", response_model=List[dtos.SnapshotResponse])
def list_snapshots(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_admin(current_user)
    return FrameworkSnapshotService.list_snapshots(db, framework_id)


@router.post("/frameworks/{framework_id}/snapshots/{snapshot_id}/revert")
def revert_to_snapshot(
    framework_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    _require_admin(current_user)
    user_id = uuid.UUID(current_user.id) if isinstance(current_user.id, str) else current_user.id

    try:
        result = FrameworkSnapshotService.revert_to_snapshot(db, framework_id, snapshot_id, user_id)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to revert: {str(e)}")
