import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.scanner_results_service import (
    get_nmap_results,
    get_zap_results,
    get_semgrep_results,
    get_osv_results,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/nmap/results")
def nmap_results(db: Session = Depends(get_db)):
    try:
        return get_nmap_results(db)
    except Exception as exc:
        logger.error("get_nmap_results error: %s", exc)
        return {"total": 0, "open_ports": [], "by_service": [], "by_protocol": [], "hosts": [], "recent": []}


@router.get("/api/zap/results")
def zap_results(db: Session = Depends(get_db)):
    try:
        return get_zap_results(db)
    except Exception as exc:
        logger.error("get_zap_results error: %s", exc)
        return {"total": 0, "by_risk": {"High": 0, "Medium": 0, "Low": 0, "Info": 0}, "by_cwe": [], "top_vulnerabilities": [], "recent": []}


@router.get("/api/semgrep/results")
def semgrep_results(db: Session = Depends(get_db)):
    try:
        return get_semgrep_results(db)
    except Exception as exc:
        logger.error("get_semgrep_results error: %s", exc)
        return {"total": 0, "by_severity": {"ERROR": 0, "WARNING": 0, "INFO": 0}, "by_owasp": [], "by_check": [], "recent": []}


@router.get("/api/osv/results")
def osv_results(db: Session = Depends(get_db)):
    try:
        return get_osv_results(db)
    except Exception as exc:
        logger.error("get_osv_results error: %s", exc)
        return {"total": 0, "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}, "by_ecosystem": [], "top_packages": [], "recent": []}
