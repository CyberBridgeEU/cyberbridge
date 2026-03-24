# nvd_controller.py
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import asyncio
import uuid

from app.database.database import get_db
from app.repositories import nvd_repository
from app.services.nvd_service import NVDService, VulnerabilityCorrelator, run_nvd_sync
from app.services.auth_service import get_current_active_user
from app.dtos import schemas
from app.models import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nvd", tags=["NVD Vulnerability Sync"])


# ===========================
# NVD Settings Endpoints
# ===========================

@router.get("/settings", response_model=schemas.NVDSettingsResponse)
async def get_nvd_settings(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get NVD sync settings (super_admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can view NVD settings")

    try:
        settings = nvd_repository.get_nvd_settings(db)

        if not settings:
            # Create default settings if none exist
            settings = nvd_repository.create_nvd_settings(db)

        return schemas.NVDSettingsResponse(
            id=settings.id,
            api_key="********" if settings.api_key else None,
            sync_enabled=settings.sync_enabled,
            sync_hour=settings.sync_hour,
            sync_minute=settings.sync_minute,
            last_sync_at=settings.last_sync_at,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
            has_api_key=bool(settings.api_key)
        )

    except Exception as e:
        logger.error(f"Error getting NVD settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get NVD settings: {str(e)}")


@router.put("/settings", response_model=schemas.NVDSettingsResponse)
async def update_nvd_settings(
    request: schemas.NVDSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update NVD sync settings (super_admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can update NVD settings")

    try:
        # Validate sync_hour and sync_minute
        if request.sync_hour is not None and (request.sync_hour < 0 or request.sync_hour > 23):
            raise HTTPException(status_code=400, detail="sync_hour must be between 0 and 23")
        if request.sync_minute is not None and (request.sync_minute < 0 or request.sync_minute > 59):
            raise HTTPException(status_code=400, detail="sync_minute must be between 0 and 59")

        settings = nvd_repository.update_nvd_settings(
            db,
            api_key=request.api_key,
            sync_enabled=request.sync_enabled,
            sync_hour=request.sync_hour,
            sync_minute=request.sync_minute
        )

        return schemas.NVDSettingsResponse(
            id=settings.id,
            api_key="********" if settings.api_key else None,
            sync_enabled=settings.sync_enabled,
            sync_hour=settings.sync_hour,
            sync_minute=settings.sync_minute,
            last_sync_at=settings.last_sync_at,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
            has_api_key=bool(settings.api_key)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating NVD settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update NVD settings: {str(e)}")


# ===========================
# Sync Management Endpoints
# ===========================

@router.post("/sync", response_model=schemas.NVDSyncStatusResponse)
async def trigger_sync(
    request: schemas.NVDSyncTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Trigger a manual NVD sync (super_admin only)."""
    if current_user.role_name != 'super_admin':
        raise HTTPException(status_code=403, detail="Only super administrators can trigger NVD sync")

    try:
        # Check if sync is already in progress
        if nvd_repository.is_sync_in_progress(db):
            raise HTTPException(status_code=409, detail="An NVD sync is already in progress")

        # Get settings for API key
        settings = nvd_repository.get_nvd_settings(db)

        # Create sync status record
        sync_type = "full" if request.full_sync else "incremental"
        sync_status = nvd_repository.create_sync_status(
            db,
            sync_type=sync_type,
            triggered_by=current_user.id
        )

        # Get user email for response
        user = db.query(models.User).filter(models.User.id == current_user.id).first()

        # Run sync in background
        async def run_sync():
            sync_db = next(get_db())
            try:
                api_key = settings.api_key if settings else None
                service = NVDService(sync_db, api_key)
                await service.sync_cves(sync_status.id, full_sync=request.full_sync)
            except Exception as e:
                logger.error(f"Background NVD sync failed: {str(e)}")
            finally:
                sync_db.close()

        # Schedule the background task
        background_tasks.add_task(asyncio.run, run_sync())

        return schemas.NVDSyncStatusResponse(
            id=sync_status.id,
            status=sync_status.status,
            sync_type=sync_status.sync_type,
            started_at=sync_status.started_at,
            completed_at=sync_status.completed_at,
            cves_processed=sync_status.cves_processed,
            cves_added=sync_status.cves_added,
            cves_updated=sync_status.cves_updated,
            error_message=sync_status.error_message,
            triggered_by=sync_status.triggered_by,
            triggered_by_email=user.email if user else None,
            created_at=sync_status.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering NVD sync: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger NVD sync: {str(e)}")


@router.get("/sync/status", response_model=Optional[schemas.NVDSyncStatusResponse])
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get the latest sync status."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can view NVD sync status")

    try:
        sync_status = nvd_repository.get_latest_sync_status(db)

        if not sync_status:
            return None

        # Get user email if triggered by a user
        triggered_by_email = None
        if sync_status.triggered_by:
            user = db.query(models.User).filter(models.User.id == sync_status.triggered_by).first()
            triggered_by_email = user.email if user else None

        return schemas.NVDSyncStatusResponse(
            id=sync_status.id,
            status=sync_status.status,
            sync_type=sync_status.sync_type,
            started_at=sync_status.started_at,
            completed_at=sync_status.completed_at,
            cves_processed=sync_status.cves_processed,
            cves_added=sync_status.cves_added,
            cves_updated=sync_status.cves_updated,
            error_message=sync_status.error_message,
            triggered_by=sync_status.triggered_by,
            triggered_by_email=triggered_by_email,
            created_at=sync_status.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.get("/sync/history", response_model=schemas.NVDSyncHistoryResponse)
async def get_sync_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get sync history."""
    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only administrators can view NVD sync history")

    try:
        syncs = nvd_repository.get_sync_history(db, limit=limit)

        sync_responses = []
        for sync in syncs:
            triggered_by_email = None
            if sync.triggered_by:
                user = db.query(models.User).filter(models.User.id == sync.triggered_by).first()
                triggered_by_email = user.email if user else None

            sync_responses.append(schemas.NVDSyncStatusResponse(
                id=sync.id,
                status=sync.status,
                sync_type=sync.sync_type,
                started_at=sync.started_at,
                completed_at=sync.completed_at,
                cves_processed=sync.cves_processed,
                cves_added=sync.cves_added,
                cves_updated=sync.cves_updated,
                error_message=sync.error_message,
                triggered_by=sync.triggered_by,
                triggered_by_email=triggered_by_email,
                created_at=sync.created_at
            ))

        return schemas.NVDSyncHistoryResponse(
            syncs=sync_responses,
            total_count=len(sync_responses)
        )

    except Exception as e:
        logger.error(f"Error getting sync history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")


# ===========================
# Statistics Endpoints
# ===========================

@router.get("/statistics", response_model=schemas.NVDStatisticsResponse)
async def get_nvd_statistics(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get NVD database statistics."""
    try:
        stats = nvd_repository.get_cve_statistics(db)
        settings = nvd_repository.get_nvd_settings(db)

        return schemas.NVDStatisticsResponse(
            total_cves=stats["total_cves"],
            severity_breakdown=stats["severity_breakdown"],
            latest_cve_date=stats["latest_cve_date"],
            oldest_cve_date=stats["oldest_cve_date"],
            cpe_match_count=stats["cpe_match_count"],
            last_sync_at=settings.last_sync_at if settings else None,
            sync_enabled=settings.sync_enabled if settings else True
        )

    except Exception as e:
        logger.error(f"Error getting NVD statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get NVD statistics: {str(e)}")


# ===========================
# CVE Search Endpoints
# ===========================

@router.get("/cves", response_model=schemas.CVEListResponse)
async def search_cves(
    search: str = None,
    severity: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Search CVEs in the local database."""
    try:
        cves = nvd_repository.get_cves(db, skip=skip, limit=limit, severity=severity, search=search)
        total = nvd_repository.get_cve_count(db)

        cve_responses = []
        for cve in cves:
            cve_responses.append(schemas.CVEResponse(
                id=cve.id,
                cve_id=cve.cve_id,
                description=cve.description,
                cvss_v3_score=cve.cvss_v3_score,
                cvss_v3_severity=cve.cvss_v3_severity,
                cvss_v3_vector=cve.cvss_v3_vector,
                cvss_v2_score=cve.cvss_v2_score,
                cvss_v2_severity=cve.cvss_v2_severity,
                published_date=cve.published_date,
                last_modified_date=cve.last_modified_date,
                vuln_status=cve.vuln_status,
                references=cve.references,
                cwe_ids=cve.cwe_ids,
                created_at=cve.created_at,
                updated_at=cve.updated_at
            ))

        return schemas.CVEListResponse(
            cves=cve_responses,
            total_count=total
        )

    except Exception as e:
        logger.error(f"Error searching CVEs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search CVEs: {str(e)}")


@router.get("/cves/{cve_id}", response_model=schemas.CVEResponse)
async def get_cve(
    cve_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get a specific CVE by CVE ID (e.g., CVE-2021-44228)."""
    try:
        cve = nvd_repository.get_cve_by_cve_id(db, cve_id)

        if not cve:
            raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")

        return schemas.CVEResponse(
            id=cve.id,
            cve_id=cve.cve_id,
            description=cve.description,
            cvss_v3_score=cve.cvss_v3_score,
            cvss_v3_severity=cve.cvss_v3_severity,
            cvss_v3_vector=cve.cvss_v3_vector,
            cvss_v2_score=cve.cvss_v2_score,
            cvss_v2_severity=cve.cvss_v2_severity,
            published_date=cve.published_date,
            last_modified_date=cve.last_modified_date,
            vuln_status=cve.vuln_status,
            references=cve.references,
            cwe_ids=cve.cwe_ids,
            created_at=cve.created_at,
            updated_at=cve.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CVE: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get CVE: {str(e)}")


# ===========================
# Vulnerability Correlation Endpoints
# ===========================

@router.post("/correlate/{scan_id}", response_model=schemas.CorrelateResponse)
async def correlate_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Correlate an Nmap scan with known CVEs."""
    try:
        # Validate scan_id
        try:
            scan_uuid = uuid.UUID(scan_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scan ID format")

        # Verify scan exists and is an Nmap scan
        scan = db.query(models.ScannerHistory).filter(
            models.ScannerHistory.id == scan_uuid,
            models.ScannerHistory.scanner_type == "nmap"
        ).first()

        if not scan:
            raise HTTPException(status_code=404, detail="Nmap scan not found")

        # Check permissions - user must be super_admin, org_admin, or the scan owner
        if current_user.role_name not in ['super_admin', 'org_admin'] and str(scan.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="You don't have permission to correlate this scan")

        # Run correlation
        correlator = VulnerabilityCorrelator(db)
        vulnerabilities = correlator.correlate_scan(scan_uuid)

        return schemas.CorrelateResponse(
            success=True,
            scan_id=scan_id,
            vulnerabilities_found=len(vulnerabilities),
            message=f"Found {len(vulnerabilities)} potential vulnerabilities"
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error correlating scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to correlate scan: {str(e)}")


@router.get("/vulnerabilities/{scan_id}", response_model=schemas.ScanVulnerabilitiesResponse)
async def get_scan_vulnerabilities(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get vulnerabilities found for a specific Nmap scan."""
    try:
        # Validate scan_id
        try:
            scan_uuid = uuid.UUID(scan_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scan ID format")

        # Verify scan exists
        scan = db.query(models.ScannerHistory).filter(
            models.ScannerHistory.id == scan_uuid,
            models.ScannerHistory.scanner_type == "nmap"
        ).first()

        if not scan:
            raise HTTPException(status_code=404, detail="Nmap scan not found")

        # Check permissions
        if current_user.role_name not in ['super_admin', 'org_admin'] and str(scan.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="You don't have permission to view this scan's vulnerabilities")

        # Get vulnerabilities with CVE details
        vulnerabilities = nvd_repository.get_vulnerabilities_with_cve_details(db, scan_uuid)

        # Get summary
        summary = nvd_repository.get_vulnerability_summary(db, scan_uuid)

        return schemas.ScanVulnerabilitiesResponse(
            scan_id=scan_id,
            scan_target=scan.scan_target,
            scan_timestamp=scan.timestamp,
            vulnerabilities=[schemas.ServiceVulnerabilityResponse(**v) for v in vulnerabilities],
            summary=summary
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scan vulnerabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scan vulnerabilities: {str(e)}")
