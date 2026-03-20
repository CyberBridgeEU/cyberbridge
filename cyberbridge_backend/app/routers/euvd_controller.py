# euvd_controller.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
import logging
from typing import Optional
from datetime import datetime

from app.database.database import get_db
from app.repositories import euvd_repository
from app.services.euvd_service import EUVDService
from app.services.auth_service import get_current_active_user
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/euvd", tags=["EUVD Vulnerability Database"])


@router.get("/exploited")
async def get_exploited(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get cached exploited vulnerabilities."""
    try:
        vulns = euvd_repository.get_exploited(db, skip, limit, days)
        total = euvd_repository.get_exploited_count(db, days)
        return {
            "items": [_vuln_to_dict(v) for v in vulns],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching exploited vulns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/critical")
async def get_critical(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get cached critical vulnerabilities."""
    try:
        vulns = euvd_repository.get_critical(db, skip, limit, days)
        total = euvd_repository.get_critical_count(db, days)
        return {
            "items": [_vuln_to_dict(v) for v in vulns],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching critical vulns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get cached latest vulnerabilities."""
    try:
        vulns = euvd_repository.get_latest(db, skip, limit, days)
        total = euvd_repository.get_latest_count(db, days)
        return {
            "items": [_vuln_to_dict(v) for v in vulns],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching latest vulns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_euvd(
    text: Optional[str] = None,
    product: Optional[str] = None,
    vendor: Optional[str] = None,
    fromScore: Optional[float] = None,
    toScore: Optional[float] = None,
    exploited: Optional[bool] = None,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Proxy search to EUVD search API."""
    try:
        params = {}
        if text:
            params["text"] = text
        if product:
            params["product"] = product
        if vendor:
            params["vendor"] = vendor
        if fromScore is not None:
            params["fromScore"] = fromScore
        if toScore is not None:
            params["toScore"] = toScore
        if exploited is not None:
            params["exploited"] = str(exploited).lower()
        params["page"] = page
        params["size"] = size

        service = EUVDService(db)
        result = await service.search(params)
        return result
    except Exception as e:
        logger.error(f"Error searching EUVD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Trigger a manual EUVD sync."""
    try:
        if euvd_repository.is_sync_in_progress(db):
            raise HTTPException(status_code=409, detail="A sync is already in progress")

        sync_status = euvd_repository.create_sync_status(db, triggered_by=current_user.id)

        async def run_sync():
            sync_db = next(get_db())
            try:
                service = EUVDService(sync_db)
                await service.sync_all(sync_status.id)
            except Exception as e:
                logger.error(f"Manual EUVD sync failed: {e}")
            finally:
                sync_db.close()

        background_tasks.add_task(run_sync)

        return {"message": "EUVD sync started", "sync_id": str(sync_status.id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering EUVD sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status")
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get latest sync status."""
    try:
        status = euvd_repository.get_latest_sync_status(db)
        if not status:
            return {"status": "never_synced", "last_sync_at": None}
        return {
            "id": str(status.id),
            "status": status.status,
            "started_at": status.started_at.isoformat() if status.started_at else None,
            "completed_at": status.completed_at.isoformat() if status.completed_at else None,
            "vulns_processed": status.vulns_processed,
            "vulns_added": status.vulns_added,
            "vulns_updated": status.vulns_updated,
            "error_message": status.error_message,
            "created_at": status.created_at.isoformat() if status.created_at else None
        }
    except Exception as e:
        logger.error(f"Error fetching sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vulnerabilities/all")
async def delete_all_vulnerabilities(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete all cached vulnerabilities."""
    try:
        count = euvd_repository.delete_all(db)
        return {"deleted": count}
    except Exception as e:
        logger.error(f"Error deleting all EUVD vulns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vulnerabilities")
async def delete_vulnerabilities(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete cached vulnerabilities within a date range."""
    try:
        parsed_from = None
        parsed_to = None
        if date_from:
            parsed_from = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            parsed_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

        if not parsed_from and not parsed_to:
            raise HTTPException(status_code=400, detail="At least one of date_from or date_to is required")

        count = euvd_repository.delete_by_date_range(db, parsed_from, parsed_to)
        return {"deleted": count, "date_from": date_from, "date_to": date_to}
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error deleting EUVD vulns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get EUVD cache statistics."""
    try:
        return euvd_repository.get_stats(db)
    except Exception as e:
        logger.error(f"Error fetching EUVD stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_euvd_settings(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get EUVD sync settings."""
    try:
        settings = euvd_repository.get_euvd_settings(db)
        if not settings:
            settings = euvd_repository.create_euvd_settings(db)
        return {
            "id": str(settings.id),
            "sync_enabled": settings.sync_enabled,
            "sync_interval_hours": settings.sync_interval_hours,
            "sync_interval_seconds": settings.sync_interval_seconds,
            "last_sync_at": settings.last_sync_at.isoformat() if settings.last_sync_at else None,
            "created_at": settings.created_at.isoformat() if settings.created_at else None,
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
        }
    except Exception as e:
        logger.error(f"Error fetching EUVD settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_euvd_settings(
    update: schemas.EUVDSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update EUVD sync settings and reschedule the scheduler job."""
    try:
        settings = euvd_repository.update_euvd_settings(
            db,
            sync_enabled=update.sync_enabled,
            sync_interval_hours=update.sync_interval_hours,
            sync_interval_seconds=update.sync_interval_seconds
        )

        # Reschedule the scheduler job
        try:
            from app.main import scheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from app.services import euvd_service

            if settings.sync_enabled:
                try:
                    scheduler.reschedule_job(
                        'euvd_sync_job',
                        trigger=IntervalTrigger(
                            hours=settings.sync_interval_hours,
                            seconds=settings.sync_interval_seconds
                        )
                    )
                    logger.info(f"EUVD sync job rescheduled: {settings.sync_interval_hours}h {settings.sync_interval_seconds}s")
                except Exception:
                    # Job doesn't exist yet, add it
                    scheduler.add_job(
                        euvd_service.run_euvd_sync,
                        trigger=IntervalTrigger(
                            hours=settings.sync_interval_hours,
                            seconds=settings.sync_interval_seconds
                        ),
                        id='euvd_sync_job',
                        name='EUVD Sync',
                        replace_existing=True
                    )
                    logger.info(f"EUVD sync job added: {settings.sync_interval_hours}h {settings.sync_interval_seconds}s")
            else:
                try:
                    scheduler.pause_job('euvd_sync_job')
                    logger.info("EUVD sync job paused")
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Could not update scheduler: {e}")

        return {
            "id": str(settings.id),
            "sync_enabled": settings.sync_enabled,
            "sync_interval_hours": settings.sync_interval_hours,
            "sync_interval_seconds": settings.sync_interval_seconds,
            "last_sync_at": settings.last_sync_at.isoformat() if settings.last_sync_at else None,
            "created_at": settings.created_at.isoformat() if settings.created_at else None,
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating EUVD settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sync/history")
async def delete_sync_history(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete all EUVD sync history records (super_admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can delete sync history")
    try:
        count = euvd_repository.delete_all_sync_history(db)
        return {"deleted": count}
    except Exception as e:
        logger.error(f"Error deleting EUVD sync history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/history")
async def get_sync_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get EUVD sync history."""
    try:
        history = euvd_repository.get_sync_history(db, limit)
        return {
            "syncs": [
                {
                    "id": str(s.id),
                    "status": s.status,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "vulns_processed": s.vulns_processed or 0,
                    "vulns_added": s.vulns_added or 0,
                    "vulns_updated": s.vulns_updated or 0,
                    "error_message": s.error_message,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in history
            ],
            "total_count": len(history)
        }
    except Exception as e:
        logger.error(f"Error fetching EUVD sync history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _vuln_to_dict(v) -> dict:
    """Convert a vulnerability model to a dict for JSON response."""
    return {
        "id": str(v.id),
        "euvd_id": v.euvd_id,
        "description": v.description,
        "date_published": v.date_published.isoformat() if v.date_published else None,
        "date_updated": v.date_updated.isoformat() if v.date_updated else None,
        "base_score": v.base_score,
        "base_score_version": v.base_score_version,
        "base_score_vector": v.base_score_vector,
        "epss": v.epss,
        "assigner": v.assigner,
        "references": v.references,
        "aliases": v.aliases,
        "products": v.products,
        "vendors": v.vendors,
        "is_exploited": v.is_exploited,
        "is_critical": v.is_critical,
        "category": v.category,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }
