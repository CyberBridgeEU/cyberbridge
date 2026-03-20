# cti_controller.py
from fastapi import APIRouter, HTTPException, Depends, Query
import httpx
import logging

from app.services.cti_service import CTIService
from app.services.auth_service import get_current_active_user
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cti", tags=["Cyber Threat Intelligence"])

# Shared service instance
_cti_service = CTIService()


def _handle_cti_error(exc: Exception, context: str) -> HTTPException:
    """Map CTI service exceptions to appropriate HTTP responses."""
    if isinstance(exc, httpx.TimeoutException):
        logger.error("CTI service timeout – %s: %s", context, exc)
        return HTTPException(
            status_code=504,
            detail=f"CTI service timed out ({context})"
        )
    if isinstance(exc, httpx.HTTPStatusError):
        logger.error("CTI service HTTP error – %s: %s", context, exc)
        return HTTPException(
            status_code=502,
            detail=f"CTI service returned an error ({context}): {exc.response.status_code}"
        )
    if isinstance(exc, httpx.RequestError):
        logger.error("CTI service connection error – %s: %s", context, exc)
        return HTTPException(
            status_code=503,
            detail=f"Unable to reach CTI service ({context})"
        )
    logger.error("Unexpected error – %s: %s", context, exc)
    return HTTPException(
        status_code=500,
        detail=f"Failed to fetch CTI data ({context}): {str(exc)}"
    )


# ===========================
# Health
# ===========================

@router.get("/health")
async def cti_health(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Check connectivity to the CTI service microservice."""
    try:
        return await _cti_service.check_health()
    except Exception as exc:
        raise _handle_cti_error(exc, "health check")


# ===========================
# Statistics & Timeline
# ===========================

@router.get("/stats")
async def cti_stats(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get aggregated CTI statistics (counts by source)."""
    try:
        return await _cti_service.get_stats()
    except Exception as exc:
        raise _handle_cti_error(exc, "stats")


@router.get("/timeline")
async def cti_timeline(
    days: int = Query(7, ge=1, le=365, description="Number of days for the timeline"),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get CTI event timeline over the specified number of days."""
    try:
        return await _cti_service.get_timeline(days=days)
    except Exception as exc:
        raise _handle_cti_error(exc, "timeline")


# ===========================
# IDS / SIEM Alerts
# ===========================

@router.get("/suricata/alerts")
async def cti_suricata_alerts(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get Suricata IDS alerts summary from CTI service."""
    try:
        return await _cti_service.get_suricata_alerts()
    except Exception as exc:
        raise _handle_cti_error(exc, "suricata alerts")


@router.get("/wazuh/alerts")
async def cti_wazuh_alerts(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get Wazuh SIEM alerts summary from CTI service."""
    try:
        return await _cti_service.get_wazuh_alerts()
    except Exception as exc:
        raise _handle_cti_error(exc, "wazuh alerts")


# ===========================
# Malware & ATT&CK
# ===========================

@router.get("/malware")
async def cti_malware(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get CAPE malware sandbox results from CTI service."""
    try:
        return await _cti_service.get_malware()
    except Exception as exc:
        raise _handle_cti_error(exc, "malware")


@router.get("/attack-patterns")
async def cti_attack_patterns(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get MITRE ATT&CK patterns across all CTI sources."""
    try:
        return await _cti_service.get_attack_patterns()
    except Exception as exc:
        raise _handle_cti_error(exc, "attack patterns")


# ===========================
# Indicators
# ===========================

@router.get("/indicators")
async def cti_indicators(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all indicators across CTI sources (recent 100)."""
    try:
        return await _cti_service.get_indicators()
    except Exception as exc:
        raise _handle_cti_error(exc, "indicators")


# ===========================
# Scanner Results
# ===========================

@router.get("/nmap/results")
async def cti_nmap_results(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get Nmap port scan results summary from CTI service."""
    try:
        return await _cti_service.get_nmap_results()
    except Exception as exc:
        raise _handle_cti_error(exc, "nmap results")


@router.get("/zap/results")
async def cti_zap_results(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get ZAP web application scan results summary from CTI service."""
    try:
        return await _cti_service.get_zap_results()
    except Exception as exc:
        raise _handle_cti_error(exc, "zap results")


@router.get("/semgrep/results")
async def cti_semgrep_results(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get Semgrep SAST code analysis results summary from CTI service."""
    try:
        return await _cti_service.get_semgrep_results()
    except Exception as exc:
        raise _handle_cti_error(exc, "semgrep results")


@router.get("/osv/results")
async def cti_osv_results(
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get OSV dependency vulnerability scan results summary from CTI service."""
    try:
        return await _cti_service.get_osv_results()
    except Exception as exc:
        raise _handle_cti_error(exc, "osv results")
