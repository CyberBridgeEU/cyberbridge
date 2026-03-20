from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import requests
import logging
import asyncio

from app.utils.cancellation import register_task, trigger_cancel, unregister_task
import os
import uuid
import time
from urllib.parse import urlparse
from threading import Lock

from app.database.database import get_db
from app.services.llm_service import LLMService
from app.services.auth_service import get_current_user
from app.services.nmap_vulnerability_service import NmapVulnerabilityService

logger = logging.getLogger(__name__)

# ===========================
# Scan Results Cache for Pagination
# ===========================
# In-memory cache for scan results with TTL (30 minutes)
# Structure: { scan_id: { "results": {...}, "timestamp": time.time() } }
_scan_results_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = Lock()
CACHE_TTL_SECONDS = 1800  # 30 minutes


def _cache_scan_results(scan_id: str, results: Dict[str, Any]) -> None:
    """Cache scan results with timestamp for TTL."""
    with _cache_lock:
        _scan_results_cache[scan_id] = {
            "results": results,
            "timestamp": time.time()
        }
        # Cleanup old entries (older than TTL)
        current_time = time.time()
        expired_keys = [
            key for key, value in _scan_results_cache.items()
            if current_time - value["timestamp"] > CACHE_TTL_SECONDS
        ]
        for key in expired_keys:
            del _scan_results_cache[key]


def _get_cached_results(scan_id: str) -> Optional[Dict[str, Any]]:
    """Get cached scan results if not expired."""
    with _cache_lock:
        cached = _scan_results_cache.get(scan_id)
        if cached:
            if time.time() - cached["timestamp"] <= CACHE_TTL_SECONDS:
                return cached["results"]
            else:
                # Expired, remove it
                del _scan_results_cache[scan_id]
        return None


def _paginate_vulnerabilities(vulnerabilities: list, page: int, page_size: int) -> Dict[str, Any]:
    """Paginate a list of vulnerabilities."""
    total = len(vulnerabilities)
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    return {
        "items": vulnerabilities[start_idx:end_idx],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

router = APIRouter(prefix="/scanners", tags=["scanners"])

# Scanner service URLs - read from environment variables with fallback to localhost
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://localhost:8011")
SEMGREP_SERVICE_URL = os.getenv("SEMGREP_SERVICE_URL", "http://localhost:8013")
OSV_SERVICE_URL = os.getenv("OSV_SERVICE_URL", "http://localhost:8012")
ZAP_SERVICE_URL = os.getenv("ZAP_SERVICE_URL", "http://localhost:8010")
SYFT_SERVICE_URL = os.getenv("SYFT_SERVICE_URL", "http://localhost:8014")


def clean_target_for_nmap(target: str) -> str:
    """
    Strip protocol (http://, https://) from target for nmap compatibility.
    Nmap expects hostnames or IPs, not URLs.
    """
    # If target contains ://, parse it as URL and extract hostname
    if "://" in target:
        parsed = urlparse(target)
        return parsed.netloc if parsed.netloc else parsed.path
    return target


def _format_vulnerabilities_as_text(processed_results: dict) -> str:
    """
    Format vulnerabilities as text for backward-compatible history display.
    """
    lines = []
    summary = processed_results.get("summary", {})
    vulnerabilities = processed_results.get("vulnerabilities", [])

    # Header with summary
    lines.append("=" * 60)
    lines.append("NETWORK SCAN RESULTS")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Total Findings: {summary.get('total', 0)}")
    lines.append(f"  - High: {summary.get('high', 0)}")
    lines.append(f"  - Medium: {summary.get('medium', 0)}")
    lines.append(f"  - Low: {summary.get('low', 0)}")
    lines.append(f"  - Info: {summary.get('info', 0)}")
    lines.append("")
    lines.append("-" * 60)

    # Group by severity
    for severity in ["High", "Medium", "Low", "Info"]:
        severity_vulns = [v for v in vulnerabilities if v.get("severity") == severity]
        if severity_vulns:
            lines.append("")
            lines.append(f"[{severity.upper()}] ({len(severity_vulns)} findings)")
            lines.append("-" * 40)
            for vuln in severity_vulns:
                lines.append(f"  * {vuln.get('title', 'Unknown')}")
                if vuln.get("host") and vuln.get("port"):
                    lines.append(f"    Host: {vuln.get('host')}:{vuln.get('port')}")
                elif vuln.get("host"):
                    lines.append(f"    Host: {vuln.get('host')}")
                if vuln.get("cve_id"):
                    lines.append(f"    CVE: {vuln.get('cve_id')}")
                if vuln.get("cvss_score"):
                    lines.append(f"    CVSS: {vuln.get('cvss_score')}")
                if vuln.get("description") and severity != "Info":
                    desc = vuln.get("description", "")[:200]
                    if len(vuln.get("description", "")) > 200:
                        desc += "..."
                    lines.append(f"    Description: {desc}")
                lines.append("")

    return "\n".join(lines)


@router.get("/nmap/scan/basic")
async def nmap_basic_scan(
    target: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform a basic Nmap scan with vulnerability severity categorization.
    Returns structured vulnerabilities with High, Medium, Low, and Info severity levels.
    CVEs are correlated from the NVD database based on detected services.

    Results are paginated and cached. Use the returned scan_id with the
    /nmap/results/{scan_id} endpoint to fetch additional pages.
    """
    try:
        # Clean target: strip protocol for nmap compatibility
        clean_target = clean_target_for_nmap(target)

        # Call Nmap service for raw scan
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/basic",
            params={"target": clean_target},
            timeout=300
        )
        response.raise_for_status()
        raw_results = response.json()

        # Process with vulnerability service (always used now, LLM toggle removed)
        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)

        # Add backward-compatible analysis field for history display
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        # Generate scan_id and cache the full results
        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)

        # Paginate vulnerabilities for response
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        # Return paginated response with scan_id for fetching more pages
        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/fast")
async def nmap_fast_scan(
    target: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform a fast Nmap scan with vulnerability severity categorization.
    Returns structured vulnerabilities with High, Medium, Low, and Info severity levels.
    """
    try:
        clean_target = clean_target_for_nmap(target)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/fast",
            params={"target": clean_target},
            timeout=300
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        # Generate scan_id and cache the full results
        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)

        # Paginate vulnerabilities for response
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/ports")
async def nmap_port_scan(
    target: str,
    ports: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform an Nmap port scan with vulnerability severity categorization."""
    try:
        clean_target = clean_target_for_nmap(target)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/ports",
            params={"target": clean_target, "ports": ports},
            timeout=300
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/all_ports")
async def nmap_all_ports_scan(
    target: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform an Nmap all ports scan with vulnerability severity categorization."""
    try:
        clean_target = clean_target_for_nmap(target)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/all_ports",
            params={"target": clean_target},
            timeout=600
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/aggressive")
async def nmap_aggressive_scan(
    target: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform an Nmap aggressive scan with vulnerability severity categorization."""
    try:
        clean_target = clean_target_for_nmap(target)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/aggressive",
            params={"target": clean_target},
            timeout=600
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/os")
async def nmap_os_scan(
    target: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform an Nmap OS detection scan with vulnerability severity categorization."""
    try:
        clean_target = clean_target_for_nmap(target)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/os",
            params={"target": clean_target},
            timeout=300
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/network")
async def nmap_network_scan(
    network: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform an Nmap network scan with vulnerability severity categorization."""
    try:
        clean_network = clean_target_for_nmap(network)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/network",
            params={"network": clean_network},
            timeout=300
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_network)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/stealth")
async def nmap_stealth_scan(
    target: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform an Nmap stealth scan with vulnerability severity categorization."""
    try:
        clean_target = clean_target_for_nmap(target)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/stealth",
            params={"target": clean_target},
            timeout=300
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/no_ping")
async def nmap_no_ping_scan(
    target: str,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Perform an Nmap scan without ping with vulnerability severity categorization."""
    try:
        clean_target = clean_target_for_nmap(target)
        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/no_ping",
            params={"target": clean_target},
            timeout=300
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nmap/scan/service_version")
async def nmap_service_version_scan(
    target: str,
    ports: Optional[str] = None,
    use_llm: bool = True,  # Kept for backward compatibility, but ignored
    page: int = Query(1, ge=1, description="Page number for results"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform an Nmap service version detection scan (-sV) with vulnerability severity categorization.
    Detects service names and versions running on open ports.
    Optionally specify ports to scan (e.g., "22,80,443" or "1-1000").
    """
    try:
        clean_target = clean_target_for_nmap(target)
        params = {"target": clean_target}
        if ports:
            params["ports"] = ports

        response = requests.get(
            f"{NMAP_SERVICE_URL}/scan/service_version",
            params=params,
            timeout=600  # Service detection can take longer
        )
        response.raise_for_status()
        raw_results = response.json()

        vuln_service = NmapVulnerabilityService(db)
        processed_results = vuln_service.process_scan_results(raw_results, clean_target)
        processed_results["analysis"] = _format_vulnerabilities_as_text(processed_results)

        scan_id = str(uuid.uuid4())
        _cache_scan_results(scan_id, processed_results)
        all_vulnerabilities = processed_results.get("vulnerabilities", [])
        paginated = _paginate_vulnerabilities(all_vulnerabilities, page, page_size)

        return {
            "success": processed_results.get("success", True),
            "scan_id": scan_id,
            "summary": processed_results.get("summary", {}),
            "vulnerabilities": paginated["items"],
            "pagination": {
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total": paginated["total"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_prev": paginated["has_prev"]
            },
            "raw_data": processed_results.get("raw_data"),
            "analysis": processed_results.get("analysis")
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Nmap service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Nmap results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Paginated Scan Results Endpoint
# ===========================

@router.get("/nmap/results/{scan_id}")
async def get_nmap_scan_results_paginated(
    scan_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_user)
):
    """
    Get paginated vulnerability results for a cached scan.

    Use this endpoint to fetch additional pages of results after an initial scan.
    The scan_id is returned from the initial scan response.
    Results are cached for 30 minutes.
    """
    cached_results = _get_cached_results(scan_id)

    if not cached_results:
        raise HTTPException(
            status_code=404,
            detail="Scan results not found or expired. Please run the scan again."
        )

    vulnerabilities = cached_results.get("vulnerabilities", [])
    summary = cached_results.get("summary", {})

    # Paginate the vulnerabilities
    paginated = _paginate_vulnerabilities(vulnerabilities, page, page_size)

    return {
        "success": True,
        "scan_id": scan_id,
        "summary": summary,
        "vulnerabilities": paginated["items"],
        "pagination": {
            "page": paginated["page"],
            "page_size": paginated["page_size"],
            "total": paginated["total"],
            "total_pages": paginated["total_pages"],
            "has_next": paginated["has_next"],
            "has_prev": paginated["has_prev"]
        }
    }


def get_effective_llm_settings_for_user(db: Session, user) -> dict:
    """
    Get the effective LLM settings for a user based on their organization.
    Returns org-specific settings if configured, otherwise global defaults.
    """
    from app.models import models

    # First check global AI enabled status
    global_settings = db.query(models.LLMSettings).first()
    if not global_settings or not getattr(global_settings, 'ai_enabled', True) == False:
        pass  # AI not disabled globally
    elif global_settings and global_settings.ai_enabled == False:
        return {
            "ai_enabled": False,
            "source": "global",
            "llm_provider": "llamacpp",
            "qlon_url": None,
            "qlon_api_key": None,
            "qlon_use_tools": True
        }

    # Get user's organization ID
    user_org_id = getattr(user, 'organisation_id', None)

    if user_org_id:
        # Check for org-specific settings
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == user_org_id
        ).first()

        if org_settings and org_settings.is_enabled:
            # Use org-specific settings
            return {
                "ai_enabled": True,
                "source": "organization",
                "llm_provider": org_settings.llm_provider,
                "qlon_url": org_settings.qlon_url,
                "qlon_api_key": org_settings.qlon_api_key,
                "qlon_use_tools": org_settings.qlon_use_tools if org_settings.qlon_use_tools is not None else True,
                "openai_api_key": getattr(org_settings, 'openai_api_key', None),
                "openai_model": getattr(org_settings, 'openai_model', None) or 'gpt-4o',
                "openai_base_url": getattr(org_settings, 'openai_base_url', None),
                "anthropic_api_key": getattr(org_settings, 'anthropic_api_key', None),
                "anthropic_model": getattr(org_settings, 'anthropic_model', None) or 'claude-sonnet-4-20250514',
                "xai_api_key": getattr(org_settings, 'xai_api_key', None),
                "xai_model": getattr(org_settings, 'xai_model', None) or 'grok-3',
                "xai_base_url": getattr(org_settings, 'xai_base_url', None),
                "google_api_key": getattr(org_settings, 'google_api_key', None),
                "google_model": getattr(org_settings, 'google_model', None) or 'gemini-2.0-flash',
            }

    # Use global defaults
    return {
        "ai_enabled": True,
        "source": "global",
        "llm_provider": getattr(global_settings, 'default_provider', 'llamacpp') or 'llamacpp' if global_settings else 'llamacpp',
        "qlon_url": None,
        "qlon_api_key": None,
        "qlon_use_tools": True
    }


@router.post("/cancel-llm")
async def cancel_llm_scan(
    current_user=Depends(get_current_user)
):
    """Cancel the active LLM scan for the current user."""
    user_id = str(current_user.id)
    logger.info(f"Cancel LLM request received for user {user_id}")
    cancelled = await trigger_cancel(user_id)
    logger.info(f"Cancel LLM result for user {user_id}: cancelled={cancelled}")
    return {"cancelled": cancelled}



@router.post("/semgrep/scan")
async def semgrep_scan(
    request: Request,
    file: UploadFile = File(...),
    config: str = "auto",
    use_llm: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform a Semgrep scan on uploaded ZIP file with optional LLM analysis.
    LLM settings are automatically determined based on the user's organization settings.

    Args:
        file: ZIP file containing source code to scan
        config: Semgrep configuration (auto, p/ci, p/security-audit, p/owasp-top-ten)
        use_llm: Whether to use LLM for analysis
    """
    try:
        # Forward file to Semgrep service
        files = {"file": (file.filename, file.file, file.content_type)}
        data = {"config": config}

        response = requests.post(
            f"{SEMGREP_SERVICE_URL}/scan-zip",
            files=files,
            data=data,
            timeout=600
        )
        response.raise_for_status()
        raw_results = response.json()

        # Create LLM service
        llm_service = LLMService(db)

        if not use_llm:
            # Use fallback formatter without calling LLM
            summary = llm_service._extract_semgrep_summary(raw_results)
            formatted_results = {
                "success": True,
                "analysis": llm_service._format_semgrep_fallback(summary),
                "summary": summary,
                "raw_data": raw_results
            }
            return formatted_results

        # Get effective LLM settings for the current user's organization
        effective_settings = get_effective_llm_settings_for_user(db, current_user)

        # Check if AI is enabled
        if not effective_settings.get("ai_enabled", True):
            summary = llm_service._extract_semgrep_summary(raw_results)
            formatted_results = {
                "success": True,
                "analysis": llm_service._format_semgrep_fallback(summary),
                "summary": summary,
                "raw_data": raw_results,
                "llm_note": "AI analysis is disabled globally"
            }
            return formatted_results

        effective_provider = effective_settings.get("llm_provider", "llamacpp")
        effective_qlon_url = effective_settings.get("qlon_url")
        effective_qlon_api_key = effective_settings.get("qlon_api_key")
        effective_qlon_use_tools = effective_settings.get("qlon_use_tools", True)

        # Wrap LLM call in a task so the cancel endpoint can cancel it
        user_id = str(current_user.id)
        if effective_provider == "llamacpp":
            llm_service.llm_backend = "llamacpp"

        if effective_provider == "qlon" and effective_qlon_url and effective_qlon_api_key:
            llm_coro = llm_service.process_semgrep_results_with_qlon(
                raw_results,
                qlon_url=effective_qlon_url,
                qlon_api_key=effective_qlon_api_key,
                use_tools=effective_qlon_use_tools
            )
        else:
            llm_coro = llm_service.process_semgrep_results(raw_results)

        llm_task = asyncio.ensure_future(llm_coro)
        register_task(user_id, llm_task)
        try:
            processed_results = await llm_task
            return processed_results
        except asyncio.CancelledError:
            logger.info("Semgrep LLM scan cancelled by user")
            summary = llm_service._extract_semgrep_summary(raw_results)
            return {"success": True, "analysis": llm_service._format_semgrep_fallback(summary), "summary": summary, "raw_data": raw_results, "cancelled": True}
        except Exception as llm_err:
            if "LLM_CANCELLED" in str(llm_err):
                logger.info("Semgrep LLM scan cancelled by user")
                summary = llm_service._extract_semgrep_summary(raw_results)
                return {"success": True, "analysis": llm_service._format_semgrep_fallback(summary), "summary": summary, "raw_data": raw_results, "cancelled": True}
            raise
        finally:
            unregister_task(user_id)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Semgrep service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code analysis scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Semgrep results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semgrep/scan-github")
async def semgrep_scan_github(
    request: Request,
    github_url: str,
    config: str = "auto",
    use_llm: bool = True,
    github_token: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform a Semgrep scan on a GitHub repository with optional LLM analysis.
    LLM settings are automatically determined based on the user's organization settings.

    Accepts GitHub repository URLs in formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo

    For private repositories, provide a GitHub Personal Access Token (PAT) via github_token.

    Args:
        github_url: GitHub repository URL
        config: Semgrep configuration
        use_llm: Whether to use LLM for analysis
        github_token: GitHub PAT for private repos
    """
    import tempfile
    import subprocess
    import shutil
    import zipfile
    import io

    try:
        # Validate and normalize GitHub URL
        normalized_url = github_url.strip()
        if not normalized_url.startswith('http'):
            normalized_url = f"https://{normalized_url}"

        # Remove trailing .git if present
        if normalized_url.endswith('.git'):
            normalized_url = normalized_url[:-4]

        # Validate it's a GitHub URL
        parsed = urlparse(normalized_url)
        if 'github.com' not in parsed.netloc:
            raise HTTPException(status_code=400, detail="Only GitHub repositories are supported")

        # Extract owner and repo from path
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL format. Expected: https://github.com/owner/repo")

        owner = path_parts[0]
        repo = path_parts[1]

        logger.info(f"Cloning GitHub repository: {owner}/{repo}")

        # Create temp directory for cloning
        temp_dir = tempfile.mkdtemp()
        repo_dir = os.path.join(temp_dir, repo)

        try:
            # Build clone URL with optional authentication for private repos
            if github_token:
                # Use token for authentication (works for private repos)
                clone_url = f"https://{github_token}@github.com/{owner}/{repo}.git"
                logger.info(f"Cloning private repository with token authentication")
            else:
                clone_url = f"https://github.com/{owner}/{repo}.git"

            # Clone the repository (shallow clone for speed)
            # Set GIT_TERMINAL_PROMPT=0 to prevent git from prompting for credentials
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"

            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, repo_dir],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                # Sanitize error message to not expose token
                error_msg = result.stderr
                if github_token and github_token in error_msg:
                    error_msg = error_msg.replace(github_token, "[TOKEN]")

                if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                    detail = "Authentication failed. For private repositories, please provide a valid GitHub Personal Access Token with 'repo' scope."
                elif "not found" in error_msg.lower() or "404" in error_msg:
                    detail = "Repository not found. Make sure the URL is correct and you have access to the repository."
                else:
                    detail = f"Failed to clone repository. Make sure it exists and is accessible. Error: {error_msg}"

                raise HTTPException(status_code=400, detail=detail)

            # Create a ZIP file from the cloned repo
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(repo_dir):
                    # Skip .git directory
                    dirs[:] = [d for d in dirs if d != '.git']
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, repo_dir)
                        zipf.write(file_path, arcname)

            zip_buffer.seek(0)

            # Send to Semgrep service
            files = {"file": (f"{repo}.zip", zip_buffer, "application/zip")}
            data = {"config": config}

            response = requests.post(
                f"{SEMGREP_SERVICE_URL}/scan-zip",
                files=files,
                data=data,
                timeout=600
            )
            response.raise_for_status()
            raw_results = response.json()

            # Create LLM service
            llm_service = LLMService(db)

            if not use_llm:
                # Use fallback formatter without calling LLM
                summary = llm_service._extract_semgrep_summary(raw_results)
                formatted_results = {
                    "success": True,
                    "analysis": llm_service._format_semgrep_fallback(summary),
                    "summary": summary,
                    "raw_data": raw_results,
                    "repository": f"{owner}/{repo}"
                }
                return formatted_results

            # Get effective LLM settings for the current user's organization
            effective_settings = get_effective_llm_settings_for_user(db, current_user)

            # Check if AI is enabled
            if not effective_settings.get("ai_enabled", True):
                summary = llm_service._extract_semgrep_summary(raw_results)
                formatted_results = {
                    "success": True,
                    "analysis": llm_service._format_semgrep_fallback(summary),
                    "summary": summary,
                    "raw_data": raw_results,
                    "repository": f"{owner}/{repo}",
                    "llm_note": "AI analysis is disabled globally"
                }
                return formatted_results

            effective_provider = effective_settings.get("llm_provider", "llamacpp")
            effective_qlon_url = effective_settings.get("qlon_url")
            effective_qlon_api_key = effective_settings.get("qlon_api_key")
            effective_qlon_use_tools = effective_settings.get("qlon_use_tools", True)

            # Wrap LLM call in a task so the cancel endpoint can cancel it
            user_id = str(current_user.id)
            if effective_provider == "llamacpp":
                llm_service.llm_backend = "llamacpp"

            if effective_provider == "qlon" and effective_qlon_url and effective_qlon_api_key:
                llm_coro = llm_service.process_semgrep_results_with_qlon(
                    raw_results,
                    qlon_url=effective_qlon_url,
                    qlon_api_key=effective_qlon_api_key,
                    use_tools=effective_qlon_use_tools
                )
            else:
                llm_coro = llm_service.process_semgrep_results(raw_results)

            llm_task = asyncio.ensure_future(llm_coro)
            register_task(user_id, llm_task)
            try:
                processed_results = await llm_task
                processed_results["repository"] = f"{owner}/{repo}"
                return processed_results
            except asyncio.CancelledError:
                logger.info("Semgrep GitHub LLM scan cancelled by user")
                summary = llm_service._extract_semgrep_summary(raw_results)
                return {"success": True, "analysis": llm_service._format_semgrep_fallback(summary), "summary": summary, "raw_data": raw_results, "repository": f"{owner}/{repo}", "cancelled": True}
            except Exception as llm_err:
                if "LLM_CANCELLED" in str(llm_err):
                    logger.info("Semgrep GitHub LLM scan cancelled by user")
                    summary = llm_service._extract_semgrep_summary(raw_results)
                    return {"success": True, "analysis": llm_service._format_semgrep_fallback(summary), "summary": summary, "raw_data": raw_results, "repository": f"{owner}/{repo}", "cancelled": True}
                raise
            finally:
                unregister_task(user_id)

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        logger.error("Git clone timed out")
        raise HTTPException(status_code=408, detail="Repository clone timed out. Try a smaller repository.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Semgrep service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code analysis scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing GitHub repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/osv/scan")
async def osv_scan(
    request: Request,
    file: UploadFile = File(...),
    use_llm: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform an OSV vulnerability scan on uploaded ZIP file with optional LLM analysis.
    LLM settings are automatically determined based on the user's organization settings.
    """
    try:
        # Forward file to OSV service
        files = {"file": (file.filename, file.file, file.content_type)}

        response = requests.post(
            f"{OSV_SERVICE_URL}/scan/zip",
            files=files,
            timeout=600
        )
        response.raise_for_status()
        raw_results = response.json()

        # Create LLM service
        llm_service = LLMService(db)

        if not use_llm:
            # Use fallback formatter without calling LLM
            summary = llm_service._extract_osv_summary(raw_results)
            formatted_results = {
                "success": True,
                "analysis": llm_service._format_osv_fallback(summary),
                "summary": summary,
                "raw_data": raw_results
            }
            return formatted_results

        # Get effective LLM settings for the current user's organization
        effective_settings = get_effective_llm_settings_for_user(db, current_user)

        # Check if AI is enabled
        if not effective_settings.get("ai_enabled", True):
            summary = llm_service._extract_osv_summary(raw_results)
            formatted_results = {
                "success": True,
                "analysis": llm_service._format_osv_fallback(summary),
                "summary": summary,
                "raw_data": raw_results,
                "llm_note": "AI analysis is disabled globally"
            }
            return formatted_results

        # Process with LLM (llama.cpp)
        effective_provider = effective_settings.get("llm_provider", "llamacpp")
        if effective_provider == "llamacpp":
            llm_service.llm_backend = "llamacpp"

        # Wrap LLM call in a task so the cancel endpoint can cancel it
        user_id = str(current_user.id)
        llm_task = asyncio.ensure_future(llm_service.process_osv_results(raw_results))
        register_task(user_id, llm_task)
        try:
            processed_results = await llm_task
            return processed_results
        except asyncio.CancelledError:
            logger.info("OSV LLM scan cancelled by user")
            summary = llm_service._extract_osv_summary(raw_results)
            return {"success": True, "analysis": llm_service._format_osv_fallback(summary), "summary": summary, "raw_data": raw_results, "cancelled": True}
        except Exception as llm_err:
            if "LLM_CANCELLED" in str(llm_err):
                logger.info("OSV LLM scan cancelled by user")
                summary = llm_service._extract_osv_summary(raw_results)
                return {"success": True, "analysis": llm_service._format_osv_fallback(summary), "summary": summary, "raw_data": raw_results, "cancelled": True}
            raise
        finally:
            unregister_task(user_id)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling OSV service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dependency scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing OSV results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/syft/scan")
async def syft_scan(
    request: Request,
    file: UploadFile = File(...),
    use_llm: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform a Syft SBOM scan on uploaded ZIP file with optional LLM analysis.
    Generates a CycloneDX JSON SBOM listing all software components/dependencies.
    """
    try:
        # Forward file to Syft service
        files = {"file": (file.filename, file.file, file.content_type)}

        response = requests.post(
            f"{SYFT_SERVICE_URL}/scan/zip",
            files=files,
            timeout=600
        )
        response.raise_for_status()
        raw_results = response.json()

        # Create LLM service
        llm_service = LLMService(db)

        if not use_llm:
            # Use fallback formatter without calling LLM
            summary = llm_service._extract_syft_summary(raw_results)
            formatted_results = {
                "success": True,
                "analysis": llm_service._format_syft_fallback(summary),
                "summary": summary,
                "raw_data": raw_results
            }
            return formatted_results

        # Get effective LLM settings for the current user's organization
        effective_settings = get_effective_llm_settings_for_user(db, current_user)

        # Check if AI is enabled
        if not effective_settings.get("ai_enabled", True):
            summary = llm_service._extract_syft_summary(raw_results)
            formatted_results = {
                "success": True,
                "analysis": llm_service._format_syft_fallback(summary),
                "summary": summary,
                "raw_data": raw_results,
                "llm_note": "AI analysis is disabled globally"
            }
            return formatted_results

        # Process with LLM (llama.cpp)
        effective_provider = effective_settings.get("llm_provider", "llamacpp")
        if effective_provider == "llamacpp":
            llm_service.llm_backend = "llamacpp"

        # Wrap LLM call in a task so the cancel endpoint can cancel it
        user_id = str(current_user.id)
        llm_task = asyncio.ensure_future(llm_service.process_syft_results(raw_results))
        register_task(user_id, llm_task)
        try:
            processed_results = await llm_task
            return processed_results
        except asyncio.CancelledError:
            logger.info("Syft LLM scan cancelled by user")
            summary = llm_service._extract_syft_summary(raw_results)
            return {"success": True, "analysis": llm_service._format_syft_fallback(summary), "summary": summary, "raw_data": raw_results, "cancelled": True}
        except Exception as llm_err:
            if "LLM_CANCELLED" in str(llm_err):
                logger.info("Syft LLM scan cancelled by user")
                summary = llm_service._extract_syft_summary(raw_results)
                return {"success": True, "analysis": llm_service._format_syft_fallback(summary), "summary": summary, "raw_data": raw_results, "cancelled": True}
            raise
        finally:
            unregister_task(user_id)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Syft service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SBOM scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Syft results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/syft/scan-github")
async def syft_scan_github(
    request: Request,
    github_url: str,
    use_llm: bool = True,
    github_token: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform a Syft SBOM scan on a GitHub repository with optional LLM analysis.
    Accepts GitHub repository URLs in formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo

    For private repositories, provide a GitHub Personal Access Token (PAT) via github_token.
    """
    import tempfile
    import subprocess
    import shutil
    import zipfile
    import io

    try:
        # Validate and normalize GitHub URL
        normalized_url = github_url.strip()
        if not normalized_url.startswith('http'):
            normalized_url = f"https://{normalized_url}"

        # Remove trailing .git if present
        if normalized_url.endswith('.git'):
            normalized_url = normalized_url[:-4]

        # Validate it's a GitHub URL
        parsed = urlparse(normalized_url)
        if 'github.com' not in parsed.netloc:
            raise HTTPException(status_code=400, detail="Only GitHub repositories are supported")

        # Extract owner and repo from path
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL format. Expected: https://github.com/owner/repo")

        owner = path_parts[0]
        repo = path_parts[1]

        logger.info(f"Cloning GitHub repository for Syft SBOM scan: {owner}/{repo}")

        # Create temp directory for cloning
        temp_dir = tempfile.mkdtemp()
        repo_dir = os.path.join(temp_dir, repo)

        try:
            # Build clone URL with optional authentication for private repos
            if github_token:
                clone_url = f"https://{github_token}@github.com/{owner}/{repo}.git"
                logger.info(f"Cloning private repository with token authentication")
            else:
                clone_url = f"https://github.com/{owner}/{repo}.git"

            # Clone the repository (shallow clone for speed)
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"

            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, repo_dir],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                error_msg = result.stderr
                if github_token and github_token in error_msg:
                    error_msg = error_msg.replace(github_token, "[TOKEN]")

                if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                    detail = "Authentication failed. For private repositories, please provide a valid GitHub Personal Access Token with 'repo' scope."
                elif "not found" in error_msg.lower() or "404" in error_msg:
                    detail = "Repository not found. Make sure the URL is correct and you have access to the repository."
                else:
                    detail = f"Failed to clone repository. Make sure it exists and is accessible. Error: {error_msg}"

                raise HTTPException(status_code=400, detail=detail)

            # Create a ZIP file from the cloned repo
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(repo_dir):
                    # Skip .git directory
                    dirs[:] = [d for d in dirs if d != '.git']
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, repo_dir)
                        zipf.write(file_path, arcname)

            zip_buffer.seek(0)

            # Send to Syft service
            files = {"file": (f"{repo}.zip", zip_buffer, "application/zip")}

            response = requests.post(
                f"{SYFT_SERVICE_URL}/scan/zip",
                files=files,
                timeout=600
            )
            response.raise_for_status()
            raw_results = response.json()

            # Create LLM service
            llm_service = LLMService(db)

            if not use_llm:
                summary = llm_service._extract_syft_summary(raw_results)
                formatted_results = {
                    "success": True,
                    "analysis": llm_service._format_syft_fallback(summary),
                    "summary": summary,
                    "raw_data": raw_results,
                    "repository": f"{owner}/{repo}"
                }
                return formatted_results

            # Get effective LLM settings for the current user's organization
            effective_settings = get_effective_llm_settings_for_user(db, current_user)

            # Check if AI is enabled
            if not effective_settings.get("ai_enabled", True):
                summary = llm_service._extract_syft_summary(raw_results)
                formatted_results = {
                    "success": True,
                    "analysis": llm_service._format_syft_fallback(summary),
                    "summary": summary,
                    "raw_data": raw_results,
                    "repository": f"{owner}/{repo}",
                    "llm_note": "AI analysis is disabled globally"
                }
                return formatted_results

            # Process with LLM (llama.cpp)
            effective_provider = effective_settings.get("llm_provider", "llamacpp")
            if effective_provider == "llamacpp":
                llm_service.llm_backend = "llamacpp"

            user_id = str(current_user.id)
            llm_task = asyncio.ensure_future(llm_service.process_syft_results(raw_results))
            register_task(user_id, llm_task)
            try:
                processed_results = await llm_task
                processed_results["repository"] = f"{owner}/{repo}"
                return processed_results
            except asyncio.CancelledError:
                logger.info("Syft GitHub LLM scan cancelled by user")
                summary = llm_service._extract_syft_summary(raw_results)
                return {"success": True, "analysis": llm_service._format_syft_fallback(summary), "summary": summary, "raw_data": raw_results, "repository": f"{owner}/{repo}", "cancelled": True}
            except Exception as llm_err:
                if "LLM_CANCELLED" in str(llm_err):
                    logger.info("Syft GitHub LLM scan cancelled by user")
                    summary = llm_service._extract_syft_summary(raw_results)
                    return {"success": True, "analysis": llm_service._format_syft_fallback(summary), "summary": summary, "raw_data": raw_results, "repository": f"{owner}/{repo}", "cancelled": True}
                raise
            finally:
                unregister_task(user_id)

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        logger.error("Git clone timed out")
        raise HTTPException(status_code=408, detail="Repository clone timed out. Try a smaller repository.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Syft service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SBOM scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing GitHub repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/osv/scan-github")
async def osv_scan_github(
    request: Request,
    github_url: str,
    use_llm: bool = True,
    github_token: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Perform an OSV vulnerability scan on a GitHub repository with optional LLM analysis.
    Accepts GitHub repository URLs in formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo

    For private repositories, provide a GitHub Personal Access Token (PAT) via github_token.
    """
    import tempfile
    import subprocess
    import shutil
    import zipfile
    import io

    try:
        # Validate and normalize GitHub URL
        normalized_url = github_url.strip()
        if not normalized_url.startswith('http'):
            normalized_url = f"https://{normalized_url}"

        # Remove trailing .git if present
        if normalized_url.endswith('.git'):
            normalized_url = normalized_url[:-4]

        # Validate it's a GitHub URL
        parsed = urlparse(normalized_url)
        if 'github.com' not in parsed.netloc:
            raise HTTPException(status_code=400, detail="Only GitHub repositories are supported")

        # Extract owner and repo from path
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL format. Expected: https://github.com/owner/repo")

        owner = path_parts[0]
        repo = path_parts[1]

        logger.info(f"Cloning GitHub repository for OSV scan: {owner}/{repo}")

        # Create temp directory for cloning
        temp_dir = tempfile.mkdtemp()
        repo_dir = os.path.join(temp_dir, repo)

        try:
            # Build clone URL with optional authentication for private repos
            if github_token:
                # Use token for authentication (works for private repos)
                clone_url = f"https://{github_token}@github.com/{owner}/{repo}.git"
                logger.info(f"Cloning private repository with token authentication")
            else:
                clone_url = f"https://github.com/{owner}/{repo}.git"

            # Clone the repository (shallow clone for speed)
            # Set GIT_TERMINAL_PROMPT=0 to prevent git from prompting for credentials
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"

            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, repo_dir],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                # Sanitize error message to not expose token
                error_msg = result.stderr
                if github_token and github_token in error_msg:
                    error_msg = error_msg.replace(github_token, "[TOKEN]")

                if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                    detail = "Authentication failed. For private repositories, please provide a valid GitHub Personal Access Token with 'repo' scope."
                elif "not found" in error_msg.lower() or "404" in error_msg:
                    detail = "Repository not found. Make sure the URL is correct and you have access to the repository."
                else:
                    detail = f"Failed to clone repository. Make sure it exists and is accessible. Error: {error_msg}"

                raise HTTPException(status_code=400, detail=detail)

            # Create a ZIP file from the cloned repo
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(repo_dir):
                    # Skip .git directory
                    dirs[:] = [d for d in dirs if d != '.git']
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, repo_dir)
                        zipf.write(file_path, arcname)

            zip_buffer.seek(0)

            # Send to OSV service
            files = {"file": (f"{repo}.zip", zip_buffer, "application/zip")}

            response = requests.post(
                f"{OSV_SERVICE_URL}/scan/zip",
                files=files,
                timeout=600
            )
            response.raise_for_status()
            raw_results = response.json()

            # Create LLM service
            llm_service = LLMService(db)

            if not use_llm:
                # Use fallback formatter without calling LLM
                summary = llm_service._extract_osv_summary(raw_results)
                formatted_results = {
                    "success": True,
                    "analysis": llm_service._format_osv_fallback(summary),
                    "summary": summary,
                    "raw_data": raw_results,
                    "repository": f"{owner}/{repo}"
                }
                return formatted_results

            # Get effective LLM settings for the current user's organization
            effective_settings = get_effective_llm_settings_for_user(db, current_user)

            # Check if AI is enabled
            if not effective_settings.get("ai_enabled", True):
                summary = llm_service._extract_osv_summary(raw_results)
                formatted_results = {
                    "success": True,
                    "analysis": llm_service._format_osv_fallback(summary),
                    "summary": summary,
                    "raw_data": raw_results,
                    "repository": f"{owner}/{repo}",
                    "llm_note": "AI analysis is disabled globally"
                }
                return formatted_results

            # Process with LLM (llama.cpp)
            effective_provider = effective_settings.get("llm_provider", "llamacpp")
            if effective_provider == "llamacpp":
                llm_service.llm_backend = "llamacpp"

            user_id = str(current_user.id)
            llm_task = asyncio.ensure_future(llm_service.process_osv_results(raw_results))
            register_task(user_id, llm_task)
            try:
                processed_results = await llm_task
                processed_results["repository"] = f"{owner}/{repo}"
                return processed_results
            except asyncio.CancelledError:
                logger.info("OSV GitHub LLM scan cancelled by user")
                summary = llm_service._extract_osv_summary(raw_results)
                return {"success": True, "analysis": llm_service._format_osv_fallback(summary), "summary": summary, "raw_data": raw_results, "repository": f"{owner}/{repo}", "cancelled": True}
            except Exception as llm_err:
                if "LLM_CANCELLED" in str(llm_err):
                    logger.info("OSV GitHub LLM scan cancelled by user")
                    summary = llm_service._extract_osv_summary(raw_results)
                    return {"success": True, "analysis": llm_service._format_osv_fallback(summary), "summary": summary, "raw_data": raw_results, "repository": f"{owner}/{repo}", "cancelled": True}
                raise
            finally:
                unregister_task(user_id)

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        logger.error("Git clone timed out")
        raise HTTPException(status_code=408, detail="Repository clone timed out. Try a smaller repository.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling OSV service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dependency scanner service error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing GitHub repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Scanner History Endpoints
# ===========================

from app.repositories import scanner_history_repository
from app.dtos.schemas import ScannerHistoryCreate, ScannerHistoryResponse, ScannerHistoryListResponse, ScannerHistoryAssetAssign
from app.services.notification_service import send_scan_completed_notification
from typing import List
import uuid
import json


def extract_scan_summary(scanner_type: str, results_json: str) -> dict:
    """Extract summary information from scan results based on scanner type"""
    try:
        results = json.loads(results_json) if isinstance(results_json, str) else results_json
    except (json.JSONDecodeError, TypeError):
        return {}

    scanner_type_lower = scanner_type.lower()

    if scanner_type_lower == "zap":
        # ZAP results: count alerts by severity
        alerts = results if isinstance(results, list) else results.get("alerts", [])
        high = sum(1 for a in alerts if a.get("risk", "").lower() == "high")
        medium = sum(1 for a in alerts if a.get("risk", "").lower() == "medium")
        low = sum(1 for a in alerts if a.get("risk", "").lower() == "low")
        informational = sum(1 for a in alerts if a.get("risk", "").lower() in ["informational", "info"])
        return {
            "total_alerts": len(alerts),
            "high": high,
            "medium": medium,
            "low": low,
            "informational": informational
        }

    elif scanner_type_lower == "nmap":
        # Nmap results: count hosts and ports
        raw_data = results.get("raw_data", results)
        output = raw_data.get("output", "") if isinstance(raw_data, dict) else ""

        # Parse basic nmap output
        hosts_up = output.count("Host is up") if output else 0
        open_ports = output.count("/open/") + output.count("open ") if output else 0

        services = []
        if output:
            import re
            service_matches = re.findall(r'\d+/tcp\s+open\s+(\S+)', output)
            services = list(set(service_matches))

        return {
            "total_hosts": 1,
            "hosts_up": max(1, hosts_up),
            "open_ports": open_ports,
            "services_found": services
        }

    elif scanner_type_lower == "semgrep":
        # Semgrep results
        raw_data = results.get("raw_data", results)
        findings = raw_data.get("results", []) if isinstance(raw_data, dict) else []

        error_count = sum(1 for f in findings if f.get("extra", {}).get("severity", "").lower() == "error")
        warning_count = sum(1 for f in findings if f.get("extra", {}).get("severity", "").lower() == "warning")
        info_count = sum(1 for f in findings if f.get("extra", {}).get("severity", "").lower() in ["info", "information"])

        return {
            "total_findings": len(findings),
            "error": error_count,
            "warning": warning_count,
            "info": info_count,
            "files_scanned": len(set(f.get("path", "") for f in findings))
        }

    elif scanner_type_lower == "osv":
        # OSV results
        raw_data = results.get("raw_data", results)
        vulnerabilities = raw_data.get("results", []) if isinstance(raw_data, dict) else []

        # Flatten vulnerabilities from all packages
        all_vulns = []
        for pkg_result in vulnerabilities:
            vulns = pkg_result.get("vulnerabilities", [])
            all_vulns.extend(vulns)

        critical = sum(1 for v in all_vulns if any(s.get("severity", "").upper() == "CRITICAL" for s in v.get("severity", [])))
        high = sum(1 for v in all_vulns if any(s.get("severity", "").upper() == "HIGH" for s in v.get("severity", [])))
        medium = sum(1 for v in all_vulns if any(s.get("severity", "").upper() == "MEDIUM" for s in v.get("severity", [])))
        low = sum(1 for v in all_vulns if any(s.get("severity", "").upper() == "LOW" for s in v.get("severity", [])))

        return {
            "total_vulnerabilities": len(all_vulns),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "packages_scanned": len(vulnerabilities)
        }

    elif scanner_type_lower == "syft":
        # Syft SBOM results (CycloneDX format)
        raw_data = results.get("raw_data", results)
        components = raw_data.get("components", []) if isinstance(raw_data, dict) else []

        # Count by type
        by_type = {}
        licenses = set()
        for comp in components:
            comp_type = comp.get("type", "unknown")
            by_type[comp_type] = by_type.get(comp_type, 0) + 1
            for license_entry in comp.get("licenses", []):
                license_obj = license_entry.get("license", {})
                license_id = license_obj.get("id", "") or license_obj.get("name", "")
                if license_id:
                    licenses.add(license_id)

        return {
            "total_components": len(components),
            "component_types": by_type,
            "unique_licenses": len(licenses)
        }

    return {}


@router.post("/history", response_model=ScannerHistoryResponse)
async def create_scanner_history_record(
    history_data: ScannerHistoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create a new scanner history record.
    """
    try:
        db_history = scanner_history_repository.create_scanner_history(
            db=db,
            scanner_type=history_data.scanner_type,
            user_id=uuid.UUID(history_data.user_id),
            user_email=history_data.user_email,
            organisation_id=uuid.UUID(history_data.organisation_id) if history_data.organisation_id else None,
            organisation_name=history_data.organisation_name,
            scan_target=history_data.scan_target,
            scan_type=history_data.scan_type,
            scan_config=history_data.scan_config,
            results=history_data.results,
            summary=history_data.summary,
            status=history_data.status,
            error_message=history_data.error_message,
            scan_duration=history_data.scan_duration
        )

        # Send notification if scan completed successfully
        if history_data.status == "completed":
            try:
                results_summary = extract_scan_summary(history_data.scanner_type, history_data.results)
                send_scan_completed_notification(
                    db=db,
                    user_id=history_data.user_id,
                    user_email=history_data.user_email,
                    scanner_type=history_data.scanner_type,
                    scan_target=history_data.scan_target,
                    results_summary=results_summary
                )
            except Exception as notif_error:
                # Log but don't fail the request if notification fails
                logger.warning(f"Failed to send scan completion notification: {str(notif_error)}")

            # Extract findings and auto-map to risks (skip syft - SBOM only)
            if history_data.scanner_type != "syft" and history_data.organisation_id:
                try:
                    from app.services.scan_finding_service import extract_and_store_findings, auto_map_findings_to_risks
                    org_id = uuid.UUID(history_data.organisation_id)
                    findings = extract_and_store_findings(
                        db=db,
                        scan_history_id=db_history.id,
                        scanner_type=history_data.scanner_type,
                        results_json=history_data.results,
                        organisation_id=org_id,
                    )
                    if findings:
                        mapped = auto_map_findings_to_risks(db, findings, org_id)
                        db.commit()
                        logger.info(f"Extracted {len(findings)} findings, auto-mapped {mapped} to risks")
                except Exception as extract_error:
                    logger.warning(f"Failed to extract/map scan findings: {str(extract_error)}")

        return db_history
    except Exception as e:
        logger.error(f"Error creating scanner history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[ScannerHistoryResponse])
async def get_all_scanner_history(
    scanner_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get all scanner history with optional filtering by scanner type and status.
    Super admins see all records, org admins/users see only their organization's records.
    """
    try:
        # Determine user's role and organization
        from app.repositories import user_repository
        user = user_repository.get_user_by_email(db, current_user)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user's role
        from app.models import models
        role = db.query(models.Role).filter(models.Role.id == user.role_id).first()

        # Filter by organization if not super_admin
        organisation_id = None if role and role.role_name == "super_admin" else user.organisation_id

        history = scanner_history_repository.get_all_scanner_history(
            db=db,
            scanner_type=scanner_type,
            organisation_id=organisation_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scanner history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{scanner_type}", response_model=List[ScannerHistoryListResponse])
async def get_scanner_history_by_type(
    scanner_type: str,
    limit: Optional[int] = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get scanner history filtered by scanner type (zap, nmap, semgrep, osv).
    Super admins see all records, org admins/users see only their organization's records.

    Note: This endpoint returns lightweight data WITHOUT full results for performance.
    Use /history/details/{history_id} to fetch full results for a specific record.
    """
    try:
        # Validate scanner type
        valid_types = ["zap", "nmap", "semgrep", "osv", "syft"]
        if scanner_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scanner type. Must be one of: {', '.join(valid_types)}"
            )

        # current_user is already a User object from get_current_user dependency
        from app.models import models
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()

        # Filter by organization if not super_admin
        organisation_id = None if role and role.role_name == "super_admin" else current_user.organisation_id

        # Use lightweight query (includes results for severity extraction only)
        history_rows = scanner_history_repository.get_scanner_history_by_scanner_type_lightweight(
            db=db,
            scanner_type=scanner_type,
            organisation_id=organisation_id,
            limit=limit
        )

        def extract_max_severity(results_str: str) -> str:
            """Extract max severity from results JSON without sending full results."""
            if not results_str:
                return "N/A"
            try:
                results = json.loads(results_str)

                # Check for ZAP format - array of alerts with 'risk' field
                if isinstance(results, list) and len(results) > 0:
                    risk_order = ["High", "Medium", "Low", "Informational"]
                    for risk in risk_order:
                        if any(alert.get("risk", "").lower() == risk.lower() for alert in results):
                            return "Info" if risk == "Informational" else risk
                    return "N/A"

                # Check for vulnerability-based format with summary (Nmap)
                if isinstance(results, dict):
                    summary = results.get("summary", {})
                    if summary.get("high", 0) > 0:
                        return "High"
                    if summary.get("medium", 0) > 0:
                        return "Medium"
                    if summary.get("low", 0) > 0:
                        return "Low"
                    if summary.get("info", 0) > 0:
                        return "Info"
                    # Check vulnerabilities array directly
                    vulns = results.get("vulnerabilities", [])
                    if vulns:
                        severity_order = ["High", "Medium", "Low", "Info"]
                        for sev in severity_order:
                            if any(v.get("severity") == sev for v in vulns):
                                return sev
                return "N/A"
            except:
                return "N/A"

        # Convert rows to response objects (without full results)
        return [
            ScannerHistoryListResponse(
                id=row.id,
                scanner_type=row.scanner_type,
                user_id=row.user_id,
                user_email=row.user_email,
                organisation_id=row.organisation_id,
                organisation_name=row.organisation_name,
                scan_target=row.scan_target,
                scan_type=row.scan_type,
                scan_config=row.scan_config,
                summary=row.summary,
                max_severity=extract_max_severity(row.results),
                status=row.status,
                error_message=row.error_message,
                scan_duration=row.scan_duration,
                timestamp=row.timestamp,
                asset_id=row.asset_id,
                asset_name=row.asset_name
            )
            for row in history_rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ ERROR: {str(e)}")
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        logger.error(f"Error fetching scanner history by type: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/details/{history_id}", response_model=ScannerHistoryResponse)
async def get_scanner_history_details(
    history_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get detailed information about a specific scanner history record.
    """
    try:
        history = scanner_history_repository.get_scanner_history_by_id(
            db=db,
            history_id=uuid.UUID(history_id)
        )

        if not history:
            raise HTTPException(status_code=404, detail="Scanner history not found")

        # current_user is already a User object from get_current_user dependency
        from app.models import models
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()

        # Super admin can view all, others can only view their org's records
        if role and role.role_name != "super_admin":
            if history.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=403, detail="Not authorized to view this record")

        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scanner history details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/history/{history_id}/asset")
async def assign_asset_to_scanner_history(
    history_id: str,
    payload: ScannerHistoryAssetAssign,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Assign or unassign an asset to a scanner history record.
    Send { "asset_id": "<uuid>" } to assign, or { "asset_id": null } to unassign.
    """
    try:
        from app.models import models

        history = scanner_history_repository.get_scanner_history_by_id(
            db=db, history_id=uuid.UUID(history_id)
        )
        if not history:
            raise HTTPException(status_code=404, detail="Scanner history not found")

        # Check org-level access
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()
        if role and role.role_name != "super_admin":
            if history.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=403, detail="Not authorized to modify this record")

        # Validate asset exists and belongs to the same org
        asset = None
        if payload.asset_id is not None:
            asset = db.query(models.Assets).filter(models.Assets.id == payload.asset_id).first()
            if not asset:
                raise HTTPException(status_code=404, detail="Asset not found")
            if asset.organisation_id != history.organisation_id:
                raise HTTPException(status_code=403, detail="Asset does not belong to the same organisation")

            # Ensure asset is not already assigned to another scan result
            existing = db.query(models.ScannerHistory).filter(
                models.ScannerHistory.asset_id == payload.asset_id,
                models.ScannerHistory.id != uuid.UUID(history_id)
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail="This asset is already assigned to another scan result")

        # Clear sbom on the previously linked asset when unassigning or reassigning
        if history.asset_id is not None and history.asset_id != payload.asset_id:
            prev_asset = db.query(models.Assets).filter(models.Assets.id == history.asset_id).first()
            if prev_asset:
                prev_asset.sbom = None
                db.flush()

        updated = scanner_history_repository.update_scanner_history_asset(
            db=db, history_id=uuid.UUID(history_id), asset_id=payload.asset_id
        )

        # Extract readable analysis text and copy into the asset's sbom field
        if asset is not None and history.results:
            import json
            try:
                results_data = json.loads(history.results) if isinstance(history.results, str) else history.results
                # Prefer the LLM analysis text, then summary text
                sbom_text = results_data.get("analysis") or results_data.get("output")
                if not sbom_text and results_data.get("summary"):
                    sbom_text = json.dumps(results_data["summary"], indent=2)
                if not sbom_text:
                    sbom_text = history.results
                asset.sbom = sbom_text
            except (json.JSONDecodeError, TypeError, AttributeError):
                asset.sbom = history.results
            db.commit()
            db.refresh(asset)

        return {"message": "Asset assignment updated", "asset_id": str(updated.asset_id) if updated.asset_id else None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning asset to scanner history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{history_id}")
async def delete_scanner_history_record(
    history_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Delete a scanner history record. Only accessible by super admins.
    """
    try:
        # current_user is already a User object from get_current_user dependency
        from app.models import models
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()

        if not role or role.role_name != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admins can delete scanner history")

        # Delete the record
        success = scanner_history_repository.delete_scanner_history(
            db=db,
            history_id=uuid.UUID(history_id)
        )

        if not success:
            raise HTTPException(status_code=404, detail="Scanner history not found")

        return {"success": True, "message": "Scanner history deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scanner history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/clear/{scanner_type}")
async def clear_scanner_history_by_type(
    scanner_type: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Delete all scanner history records for a specific scanner type.
    Users can only delete their organization's records.
    Super admins can delete all records for the scanner type.
    """
    try:
        # Validate scanner type
        valid_types = ["zap", "nmap", "semgrep", "osv", "syft"]
        if scanner_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scanner type. Must be one of: {', '.join(valid_types)}"
            )

        # current_user is already a User object from get_current_user dependency
        from app.models import models
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()

        # Filter by organization if not super_admin
        organisation_id = None if role and role.role_name == "super_admin" else current_user.organisation_id

        # Delete all history for this scanner type
        deleted_count = scanner_history_repository.delete_all_scanner_history_by_type(
            db=db,
            scanner_type=scanner_type,
            organisation_id=organisation_id
        )

        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} {scanner_type} history record(s)",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error clearing scanner history: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# AI Remediation Endpoint
# ===========================

from app.dtos.schemas import RemediationRequest, RemediationResponse


@router.post("/remediate", response_model=RemediationResponse)
async def generate_remediation(
    request: RemediationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Generate AI remediation guidance for scan results.

    Args:
        request: Contains scanner_type ('zap' or 'nmap') and history_id (UUID of scan record)

    Returns:
        RemediationResponse with AI-generated remediation guidance
    """
    try:
        # Validate scanner type
        valid_types = ["zap", "nmap"]
        if request.scanner_type not in valid_types:
            return RemediationResponse(
                success=False,
                scanner_type=request.scanner_type,
                history_id=request.history_id,
                error=f"Invalid scanner type. AI remediation is only available for: {', '.join(valid_types)}"
            )

        # Get the scan history record
        history = scanner_history_repository.get_scanner_history_by_id(
            db=db,
            history_id=uuid.UUID(request.history_id)
        )

        if not history:
            return RemediationResponse(
                success=False,
                scanner_type=request.scanner_type,
                history_id=request.history_id,
                error="Scanner history record not found"
            )

        # Check permission - user must have access to this record
        from app.models import models
        role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()

        if role and role.role_name != "super_admin":
            if history.organisation_id != current_user.organisation_id:
                return RemediationResponse(
                    success=False,
                    scanner_type=request.scanner_type,
                    history_id=request.history_id,
                    error="Not authorized to access this scan record"
                )

        # Check if AI remediator is enabled for the user's organization
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == current_user.organisation_id
        ).first()

        # Check AI remediator enabled
        ai_remediator_enabled = getattr(org_settings, 'ai_remediator_enabled', False) if org_settings else False

        if not ai_remediator_enabled:
            return RemediationResponse(
                success=False,
                scanner_type=request.scanner_type,
                history_id=request.history_id,
                scan_target=history.scan_target,
                error="AI Remediator is not enabled for your organization. Please enable it in Settings."
            )

        # Get effective LLM settings
        effective_settings = get_effective_llm_settings_for_user(db, current_user)

        if not effective_settings.get("ai_enabled", True):
            return RemediationResponse(
                success=False,
                scanner_type=request.scanner_type,
                history_id=request.history_id,
                scan_target=history.scan_target,
                error="AI is globally disabled. Please contact your administrator."
            )

        # Get custom prompts if configured
        custom_prompt = None
        if request.scanner_type == "zap" and org_settings:
            custom_prompt = getattr(org_settings, 'remediator_prompt_zap', None)
        elif request.scanner_type == "nmap" and org_settings:
            custom_prompt = getattr(org_settings, 'remediator_prompt_nmap', None)

        # Get LLM provider configuration from organization settings
        llm_provider = getattr(org_settings, 'llm_provider', 'llamacpp') if org_settings else 'llamacpp'
        qlon_url = getattr(org_settings, 'qlon_url', None) if org_settings else None
        qlon_api_key = getattr(org_settings, 'qlon_api_key', None) if org_settings else None
        qlon_use_tools = getattr(org_settings, 'qlon_use_tools', True) if org_settings else True

        logger.info(f"AI Remediator using LLM provider: {llm_provider}")
        if llm_provider == 'qlon':
            logger.info(f"QLON URL configured: {qlon_url is not None}, API Key configured: {qlon_api_key is not None}")

        # Create LLM service and generate remediation
        llm_service = LLMService(db)
        remediation = await llm_service.generate_remediation(
            scanner_type=request.scanner_type,
            scan_results=history.results,
            custom_prompt=custom_prompt,
            llm_provider=llm_provider,
            qlon_url=qlon_url,
            qlon_api_key=qlon_api_key,
            qlon_use_tools=qlon_use_tools
        )

        return RemediationResponse(
            success=True,
            scanner_type=request.scanner_type,
            history_id=request.history_id,
            remediation=remediation,
            scan_target=history.scan_target
        )

    except Exception as e:
        import traceback
        logger.error(f"Error generating remediation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RemediationResponse(
            success=False,
            scanner_type=request.scanner_type,
            history_id=request.history_id,
            error=f"Failed to generate remediation guidance: {str(e)}"
        )


# ===========================
# Scan Findings — Unified View
# ===========================

@router.get("/findings/stats")
async def get_findings_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Aggregate stats across all scan findings for the org."""
    try:
        from app.repositories import scan_finding_repository
        org_id = uuid.UUID(current_user.organisation_id) if isinstance(current_user.organisation_id, str) else current_user.organisation_id
        stats = scan_finding_repository.get_findings_stats(db, org_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting findings stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/findings")
async def get_all_findings(
    scanner_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    has_risks: Optional[bool] = Query(None),
    is_remediated: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Paginated listing of all scan findings with CVE enrichment."""
    import re
    try:
        from app.repositories import scan_finding_repository
        from app.repositories import nvd_repository

        org_id = uuid.UUID(current_user.organisation_id) if isinstance(current_user.organisation_id, str) else current_user.organisation_id

        findings = scan_finding_repository.get_all_findings(
            db, org_id, scanner_type, severity, has_risks, search, offset, limit, is_remediated
        )
        total = scan_finding_repository.get_all_findings_count(
            db, org_id, scanner_type, severity, has_risks, search, is_remediated
        )

        # Batch risk counts
        finding_ids = [uuid.UUID(f["id"]) for f in findings]
        risk_counts = scan_finding_repository.get_risk_counts_for_findings(db, finding_ids)

        # Collect unique CVE identifiers and batch lookup
        cve_pattern = re.compile(r"(CVE-\d{4}-\d+)", re.IGNORECASE)
        cve_ids_set: set[str] = set()
        for f in findings:
            if f.get("identifier"):
                matches = cve_pattern.findall(f["identifier"])
                cve_ids_set.update(m.upper() for m in matches)

        cve_cache: dict = {}
        for cve_id in cve_ids_set:
            cve_obj = nvd_repository.get_cve_by_cve_id(db, cve_id)
            if cve_obj:
                cve_cache[cve_id] = cve_obj

        # Build enriched response
        enriched = []
        for f in findings:
            cve_desc = None
            cvss_score = None
            cvss_severity = None
            cve_published = None

            if f.get("identifier"):
                matches = cve_pattern.findall(f["identifier"])
                for m in matches:
                    cve_obj = cve_cache.get(m.upper())
                    if cve_obj:
                        cve_desc = cve_obj.description
                        cvss_score = cve_obj.cvss_v3_score
                        cvss_severity = cve_obj.cvss_v3_severity
                        cve_published = cve_obj.published_date.isoformat() if cve_obj.published_date else None
                        break

            enriched.append({
                **f,
                "cve_description": cve_desc,
                "cvss_v31_score": cvss_score,
                "cvss_v31_severity": cvss_severity,
                "cve_published": cve_published,
                "linked_risks_count": risk_counts.get(f["id"], 0),
            })

        return {"findings": enriched, "total": total, "offset": offset, "limit": limit}
    except Exception as e:
        logger.error(f"Error getting all findings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Scan Finding — Remediation Toggle
# ===========================

@router.patch("/findings/{finding_id}/remediate")
async def toggle_finding_remediation(
    finding_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Toggle the remediation status of a scan finding."""
    try:
        from app.repositories import scan_finding_repository
        user_id = uuid.UUID(current_user.id) if isinstance(current_user.id, str) else current_user.id
        result = scan_finding_repository.toggle_remediation(db, uuid.UUID(finding_id), user_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling remediation for finding {finding_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Scan Finding → Risk Lookup
# ===========================

@router.get("/findings/{finding_id}/risks")
async def get_risks_for_finding(
    finding_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all risks linked to a specific scan finding."""
    try:
        from app.repositories import scan_finding_repository
        risks = scan_finding_repository.get_risks_for_finding(db, uuid.UUID(finding_id))
        return risks
    except Exception as e:
        logger.error(f"Error getting risks for finding {finding_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Scan Schedule Endpoints
# ===========================

from app.repositories import scan_schedule_repository
from pydantic import BaseModel
from typing import Optional as Opt
from datetime import datetime


class ScanScheduleCreate(BaseModel):
    scanner_type: str
    scan_target: str
    scan_type: Opt[str] = None
    scan_config: Opt[str] = None
    schedule_type: str = "interval"  # 'interval' or 'cron'
    interval_months: int = 0
    interval_days: int = 0
    interval_hours: int = 0
    interval_minutes: int = 0
    interval_seconds: int = 0
    cron_day_of_week: Opt[str] = None
    cron_hour: Opt[int] = None
    cron_minute: Opt[int] = None
    is_enabled: bool = True


class ScanScheduleUpdate(BaseModel):
    scan_target: Opt[str] = None
    scan_type: Opt[str] = None
    scan_config: Opt[str] = None
    schedule_type: Opt[str] = None
    interval_months: Opt[int] = None
    interval_days: Opt[int] = None
    interval_hours: Opt[int] = None
    interval_minutes: Opt[int] = None
    interval_seconds: Opt[int] = None
    cron_day_of_week: Opt[str] = None
    cron_hour: Opt[int] = None
    cron_minute: Opt[int] = None
    is_enabled: Opt[bool] = None


def _schedule_to_dict(schedule) -> dict:
    """Convert a ScanSchedule model to a serializable dict."""
    return {
        "id": str(schedule.id),
        "scanner_type": schedule.scanner_type,
        "scan_target": schedule.scan_target,
        "scan_type": schedule.scan_type,
        "scan_config": schedule.scan_config,
        "schedule_type": schedule.schedule_type,
        "interval_months": schedule.interval_months,
        "interval_days": schedule.interval_days,
        "interval_hours": schedule.interval_hours,
        "interval_minutes": schedule.interval_minutes,
        "interval_seconds": schedule.interval_seconds,
        "cron_day_of_week": schedule.cron_day_of_week,
        "cron_hour": schedule.cron_hour,
        "cron_minute": schedule.cron_minute,
        "is_enabled": schedule.is_enabled,
        "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        "last_status": schedule.last_status,
        "last_error": schedule.last_error,
        "run_count": schedule.run_count,
        "user_id": str(schedule.user_id),
        "user_email": schedule.user_email,
        "organisation_id": str(schedule.organisation_id) if schedule.organisation_id else None,
        "organisation_name": schedule.organisation_name,
        "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
        "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
    }


def _compute_next_run(schedule_data: dict) -> datetime:
    """Compute the next run time for a schedule."""
    from datetime import timedelta
    now = datetime.now()

    if schedule_data.get("schedule_type") == "cron":
        # For cron, compute next occurrence of the specified day/time
        import calendar
        target_hour = schedule_data.get("cron_hour", 0) or 0
        target_minute = schedule_data.get("cron_minute", 0) or 0
        day_of_week_str = schedule_data.get("cron_day_of_week", "*") or "*"

        if day_of_week_str == "*":
            # Every day at specified time
            candidate = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate
        else:
            # Specific day(s) of week
            day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
            target_days = [day_map.get(d.strip().lower(), 0) for d in day_of_week_str.split(",")]

            for offset in range(8):
                candidate = now + timedelta(days=offset)
                candidate = candidate.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                if candidate > now and candidate.weekday() in target_days:
                    return candidate
            return now + timedelta(days=7)  # Fallback
    else:
        # Interval-based
        total_seconds = (
            schedule_data.get("interval_months", 0) * 30 * 86400 +
            schedule_data.get("interval_days", 0) * 86400 +
            schedule_data.get("interval_hours", 0) * 3600 +
            schedule_data.get("interval_minutes", 0) * 60 +
            schedule_data.get("interval_seconds", 0)
        )
        if total_seconds <= 0:
            total_seconds = 3600  # Default 1 hour
        return now + timedelta(seconds=total_seconds)


@router.post("/schedules")
async def create_scan_schedule(
    schedule_data: ScanScheduleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new scan schedule."""
    try:
        valid_types = ["zap", "nmap", "semgrep", "osv", "syft"]
        if schedule_data.scanner_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scanner type. Must be one of: {', '.join(valid_types)}"
            )

        # Validate schedule has meaningful interval
        if schedule_data.schedule_type == "interval":
            total = (
                schedule_data.interval_months * 30 * 86400 +
                schedule_data.interval_days * 86400 +
                schedule_data.interval_hours * 3600 +
                schedule_data.interval_minutes * 60 +
                schedule_data.interval_seconds
            )
            if total <= 0:
                raise HTTPException(status_code=400, detail="Schedule interval must be greater than 0")

        # Get org info
        from app.models import models as m
        org = db.query(m.Organisations).filter(m.Organisations.id == current_user.organisation_id).first() if current_user.organisation_id else None

        next_run = _compute_next_run(schedule_data.model_dump())

        schedule = scan_schedule_repository.create_scan_schedule(
            db=db,
            scanner_type=schedule_data.scanner_type,
            scan_target=schedule_data.scan_target,
            scan_type=schedule_data.scan_type,
            scan_config=schedule_data.scan_config,
            schedule_type=schedule_data.schedule_type,
            interval_months=schedule_data.interval_months,
            interval_days=schedule_data.interval_days,
            interval_hours=schedule_data.interval_hours,
            interval_minutes=schedule_data.interval_minutes,
            interval_seconds=schedule_data.interval_seconds,
            cron_day_of_week=schedule_data.cron_day_of_week,
            cron_hour=schedule_data.cron_hour,
            cron_minute=schedule_data.cron_minute,
            is_enabled=schedule_data.is_enabled,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            organisation_name=org.name if org else None,
            next_run_at=next_run
        )

        # Register with the background scheduler
        try:
            from app.services.scan_scheduler_service import register_schedule
            register_schedule(schedule)
        except Exception as e:
            logger.warning(f"Could not register schedule with background scheduler: {e}")

        return _schedule_to_dict(schedule)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scan schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules")
async def get_scan_schedules(
    scanner_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all scan schedules for the current user's organization."""
    try:
        from app.models import models as m
        role = db.query(m.Role).filter(m.Role.id == current_user.role_id).first()
        org_id = None if role and role.role_name == "super_admin" else current_user.organisation_id

        schedules = scan_schedule_repository.get_all_schedules(
            db=db,
            organisation_id=org_id,
            scanner_type=scanner_type
        )
        return [_schedule_to_dict(s) for s in schedules]
    except Exception as e:
        logger.error(f"Error fetching scan schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/{schedule_id}")
async def get_scan_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get a specific scan schedule."""
    try:
        schedule = scan_schedule_repository.get_schedule_by_id(db, uuid.UUID(schedule_id))
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Check org access
        from app.models import models as m
        role = db.query(m.Role).filter(m.Role.id == current_user.role_id).first()
        if role and role.role_name != "super_admin":
            if schedule.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=403, detail="Not authorized")

        return _schedule_to_dict(schedule)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scan schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/schedules/{schedule_id}")
async def update_scan_schedule(
    schedule_id: str,
    update_data: ScanScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update a scan schedule."""
    try:
        schedule = scan_schedule_repository.get_schedule_by_id(db, uuid.UUID(schedule_id))
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Check org access
        from app.models import models as m
        role = db.query(m.Role).filter(m.Role.id == current_user.role_id).first()
        if role and role.role_name != "super_admin":
            if schedule.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=403, detail="Not authorized")

        # Build update kwargs (only non-None values)
        kwargs = {k: v for k, v in update_data.model_dump().items() if v is not None}

        # Recompute next_run if schedule params changed
        schedule_params_changed = any(k in kwargs for k in [
            "schedule_type", "interval_months", "interval_days", "interval_hours",
            "interval_minutes", "interval_seconds", "cron_day_of_week", "cron_hour", "cron_minute"
        ])
        if schedule_params_changed:
            # Merge current schedule values with updated ones
            merged = {
                "schedule_type": kwargs.get("schedule_type", schedule.schedule_type),
                "interval_months": kwargs.get("interval_months", schedule.interval_months),
                "interval_days": kwargs.get("interval_days", schedule.interval_days),
                "interval_hours": kwargs.get("interval_hours", schedule.interval_hours),
                "interval_minutes": kwargs.get("interval_minutes", schedule.interval_minutes),
                "interval_seconds": kwargs.get("interval_seconds", schedule.interval_seconds),
                "cron_day_of_week": kwargs.get("cron_day_of_week", schedule.cron_day_of_week),
                "cron_hour": kwargs.get("cron_hour", schedule.cron_hour),
                "cron_minute": kwargs.get("cron_minute", schedule.cron_minute),
            }
            kwargs["next_run_at"] = _compute_next_run(merged)

        updated = scan_schedule_repository.update_schedule(db, uuid.UUID(schedule_id), **kwargs)
        if not updated:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Re-register with background scheduler
        try:
            from app.services.scan_scheduler_service import update_scheduled_job
            update_scheduled_job(updated)
        except Exception as e:
            logger.warning(f"Could not update schedule in background scheduler: {e}")

        return _schedule_to_dict(updated)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scan schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedules/{schedule_id}")
async def delete_scan_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete a scan schedule."""
    try:
        schedule = scan_schedule_repository.get_schedule_by_id(db, uuid.UUID(schedule_id))
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Check org access
        from app.models import models as m
        role = db.query(m.Role).filter(m.Role.id == current_user.role_id).first()
        if role and role.role_name != "super_admin":
            if schedule.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=403, detail="Not authorized")

        # Remove from background scheduler
        try:
            from app.services.scan_scheduler_service import remove_scheduled_job
            remove_scheduled_job(str(schedule.id))
        except Exception as e:
            logger.warning(f"Could not remove schedule from background scheduler: {e}")

        success = scan_schedule_repository.delete_schedule(db, uuid.UUID(schedule_id))
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return {"success": True, "message": "Schedule deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scan schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/schedules/{schedule_id}/toggle")
async def toggle_scan_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Toggle a scan schedule's enabled/disabled state."""
    try:
        schedule = scan_schedule_repository.get_schedule_by_id(db, uuid.UUID(schedule_id))
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Check org access
        from app.models import models as m
        role = db.query(m.Role).filter(m.Role.id == current_user.role_id).first()
        if role and role.role_name != "super_admin":
            if schedule.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=403, detail="Not authorized")

        toggled = scan_schedule_repository.toggle_schedule(db, uuid.UUID(schedule_id))
        if not toggled:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Update background scheduler
        try:
            from app.services.scan_scheduler_service import update_scheduled_job
            update_scheduled_job(toggled)
        except Exception as e:
            logger.warning(f"Could not update schedule in background scheduler: {e}")

        return _schedule_to_dict(toggled)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling scan schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
