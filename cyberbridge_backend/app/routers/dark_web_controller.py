# routers/dark_web_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from typing import Optional, List
import logging

from app.services.auth_service import get_current_active_user
from app.services.dark_web_service import DarkWebService
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dark-web", tags=["Dark Web Intelligence"])


def _get_service() -> DarkWebService:
    return DarkWebService()


# ------------------------------------------------------------------
# Scan endpoints
# ------------------------------------------------------------------

@router.post("/scan")
async def create_scan(
    keyword: str = Query(description="Keyword to search on the dark web"),
    engines: Optional[List[str]] = Query(default=None, description="Search engines to use"),
    exclude: Optional[List[str]] = Query(default=None, description="Search engines to exclude"),
    mp_units: int = Query(default=2, ge=1, le=10, description="Number of multiprocessing units"),
    proxy: str = Query(default="localhost:9050", description="Tor proxy address"),
    limit: int = Query(default=3, ge=1, le=50, description="Max pages per engine"),
    continuous_write: bool = Query(default=False, description="Write results progressively"),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Queue a new dark-web scan. Returns a scan_id for progress tracking."""
    try:
        service = _get_service()
        result = await service.create_scan(
            keyword=keyword,
            user_id=str(current_user.id),
            organisation_id=str(current_user.organisation_id),
            engines=engines,
            exclude=exclude,
            mp_units=mp_units,
            proxy=proxy,
            limit=limit,
            continuous_write=continuous_write,
        )
        return result
    except Exception as e:
        logger.error("Error creating dark-web scan: %s", e)
        raise HTTPException(status_code=500, detail=f"Error creating dark-web scan: {str(e)}")


@router.get("/scans")
async def list_scans(
    limit: int = Query(default=100, ge=1, description="Maximum number of scans to return"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """List dark-web scans for the current user."""
    try:
        service = _get_service()
        # Pass user_id so darkweb filters by owner (admin check done at backend level)
        result = await service.get_scans(
            limit=limit,
            status=status,
            user_id=str(current_user.id),
        )
        return result
    except Exception as e:
        logger.error("Error listing dark-web scans: %s", e)
        raise HTTPException(status_code=500, detail=f"Error listing dark-web scans: {str(e)}")


@router.get("/scan/json/{scan_id}")
async def get_scan_result_json(
    scan_id: str,
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Get the JSON results of a specific dark-web scan."""
    try:
        service = _get_service()
        result = await service.get_scan_result(scan_id)
        return result
    except Exception as e:
        logger.error("Error fetching dark-web scan %s: %s", scan_id, e)
        raise HTTPException(status_code=500, detail=f"Error fetching dark-web scan: {str(e)}")


@router.get("/scan/{scan_id}")
async def get_scan_result(
    scan_id: str,
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Get the status and results of a specific dark-web scan."""
    try:
        service = _get_service()
        result = await service.get_scan_result(scan_id)
        return result
    except Exception as e:
        logger.error("Error fetching dark-web scan %s: %s", scan_id, e)
        raise HTTPException(status_code=500, detail=f"Error fetching dark-web scan: {str(e)}")


@router.get("/scan/{scan_id}/pdf")
async def download_pdf(
    scan_id: str,
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Download the PDF report for a completed dark-web scan."""
    try:
        service = _get_service()
        pdf_bytes = await service.download_pdf(scan_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=dark_web_report_{scan_id[:8]}.pdf"
            },
        )
    except Exception as e:
        logger.error("Error downloading dark-web PDF for %s: %s", scan_id, e)
        raise HTTPException(status_code=500, detail=f"Error downloading dark-web PDF: {str(e)}")


@router.get("/download/pdf/{scan_id}")
async def download_pdf_alt(
    scan_id: str,
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Download the PDF report (alternative path used by frontend)."""
    return await download_pdf(scan_id, current_user)


@router.delete("/scan/{scan_id}")
async def delete_scan(
    scan_id: str,
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Delete a dark-web scan."""
    try:
        service = _get_service()
        result = await service.delete_scan(scan_id)
        return result
    except Exception as e:
        logger.error("Error deleting dark-web scan %s: %s", scan_id, e)
        raise HTTPException(status_code=500, detail=f"Error deleting dark-web scan: {str(e)}")


# ------------------------------------------------------------------
# Queue
# ------------------------------------------------------------------

@router.get("/queue/overview")
async def get_queue_overview(
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Get the dark-web scan queue overview."""
    try:
        service = _get_service()
        result = await service.get_queue_overview()
        return result
    except Exception as e:
        logger.error("Error fetching dark-web queue overview: %s", e)
        raise HTTPException(status_code=500, detail=f"Error fetching queue overview: {str(e)}")


# ------------------------------------------------------------------
# Settings – workers
# ------------------------------------------------------------------

@router.get("/settings/workers")
async def get_workers_settings(
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Get the current worker configuration from the dark-web scanner."""
    try:
        service = _get_service()
        result = await service.get_workers_settings()
        return result
    except Exception as e:
        logger.error("Error fetching dark-web worker settings: %s", e)
        raise HTTPException(status_code=500, detail=f"Error fetching worker settings: {str(e)}")


@router.put("/settings/workers")
async def update_workers_settings(
    max_workers: int = Query(description="New max_workers value (1-10)", ge=1, le=10),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Update the max concurrent workers on the dark-web scanner."""
    try:
        service = _get_service()
        result = await service.update_workers_settings(max_workers)
        return result
    except Exception as e:
        logger.error("Error updating dark-web worker settings: %s", e)
        raise HTTPException(status_code=500, detail=f"Error updating worker settings: {str(e)}")


# ------------------------------------------------------------------
# Settings – engines
# ------------------------------------------------------------------

@router.get("/settings/engines")
async def get_engines(
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Get available dark-web search engines and their enabled status."""
    try:
        service = _get_service()
        result = await service.get_engines()
        return result
    except Exception as e:
        logger.error("Error fetching dark-web engines: %s", e)
        raise HTTPException(status_code=500, detail=f"Error fetching engines: {str(e)}")


@router.put("/settings/engines")
async def update_engines(
    request_body: dict,
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Update which dark-web search engines are enabled."""
    try:
        enabled_engines = request_body.get("enabled_engines", [])
        if not enabled_engines:
            raise HTTPException(status_code=400, detail="At least one engine must be enabled")
        service = _get_service()
        result = await service.update_engines(enabled_engines)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating dark-web engines: %s", e)
        raise HTTPException(status_code=500, detail=f"Error updating engines: {str(e)}")


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------

@router.get("/health")
async def health_check():
    """Check the health of the dark-web scanner microservice."""
    try:
        service = _get_service()
        result = await service.check_health()
        return result
    except Exception as e:
        logger.error("Dark-web scanner health check failed: %s", e)
        return {
            "status": "unhealthy",
            "service": "dark-web-scanner",
            "error": str(e),
        }
