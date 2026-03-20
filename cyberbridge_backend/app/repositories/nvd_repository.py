# nvd_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import uuid
from typing import Optional, List
from datetime import datetime
from app.models import models


# ===========================
# NVD Settings CRUD
# ===========================

def get_nvd_settings(db: Session) -> Optional[models.NVDSettings]:
    """Get the NVD settings (there should only be one record)"""
    return db.query(models.NVDSettings).first()


def create_nvd_settings(db: Session, api_key: Optional[str] = None, sync_enabled: bool = True,
                        sync_hour: int = 3, sync_minute: int = 0) -> models.NVDSettings:
    """Create NVD settings"""
    settings = models.NVDSettings(
        api_key=api_key,
        sync_enabled=sync_enabled,
        sync_hour=sync_hour,
        sync_minute=sync_minute
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_nvd_settings(db: Session, api_key: Optional[str] = None, sync_enabled: Optional[bool] = None,
                        sync_hour: Optional[int] = None, sync_minute: Optional[int] = None) -> Optional[models.NVDSettings]:
    """Update NVD settings"""
    settings = get_nvd_settings(db)
    if not settings:
        settings = create_nvd_settings(db, api_key, sync_enabled or True, sync_hour or 3, sync_minute or 0)
    else:
        if api_key is not None:
            settings.api_key = api_key
        if sync_enabled is not None:
            settings.sync_enabled = sync_enabled
        if sync_hour is not None:
            settings.sync_hour = sync_hour
        if sync_minute is not None:
            settings.sync_minute = sync_minute
        db.commit()
        db.refresh(settings)
    return settings


def update_last_sync_time(db: Session) -> None:
    """Update the last sync timestamp"""
    settings = get_nvd_settings(db)
    if settings:
        settings.last_sync_at = datetime.utcnow()
        db.commit()


# ===========================
# NVD Sync Status CRUD
# ===========================

def create_sync_status(db: Session, sync_type: str = "incremental",
                       triggered_by: Optional[uuid.UUID] = None) -> models.NVDSyncStatus:
    """Create a new sync status record"""
    sync_status = models.NVDSyncStatus(
        status="pending",
        sync_type=sync_type,
        triggered_by=triggered_by
    )
    db.add(sync_status)
    db.commit()
    db.refresh(sync_status)
    return sync_status


def get_sync_status(db: Session, sync_id: uuid.UUID) -> Optional[models.NVDSyncStatus]:
    """Get a specific sync status record"""
    return db.query(models.NVDSyncStatus).filter(models.NVDSyncStatus.id == sync_id).first()


def get_latest_sync_status(db: Session) -> Optional[models.NVDSyncStatus]:
    """Get the most recent sync status"""
    return db.query(models.NVDSyncStatus).order_by(models.NVDSyncStatus.created_at.desc()).first()


def get_sync_history(db: Session, limit: int = 10) -> List[models.NVDSyncStatus]:
    """Get sync history"""
    return db.query(models.NVDSyncStatus).order_by(models.NVDSyncStatus.created_at.desc()).limit(limit).all()


def update_sync_status(db: Session, sync_id: uuid.UUID, status: str,
                       cves_processed: int = 0, cves_added: int = 0, cves_updated: int = 0,
                       error_message: Optional[str] = None) -> Optional[models.NVDSyncStatus]:
    """Update sync status"""
    sync_status = get_sync_status(db, sync_id)
    if sync_status:
        sync_status.status = status
        sync_status.cves_processed = cves_processed
        sync_status.cves_added = cves_added
        sync_status.cves_updated = cves_updated
        sync_status.error_message = error_message

        if status == "in_progress" and not sync_status.started_at:
            sync_status.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            sync_status.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(sync_status)
    return sync_status


def is_sync_in_progress(db: Session) -> bool:
    """Check if there's an active sync"""
    active_sync = db.query(models.NVDSyncStatus).filter(
        models.NVDSyncStatus.status.in_(["pending", "in_progress"])
    ).first()
    return active_sync is not None


# ===========================
# CVE CRUD
# ===========================

def get_cve_by_cve_id(db: Session, cve_id: str) -> Optional[models.CVE]:
    """Get a CVE by its CVE ID (e.g., CVE-2021-44228)"""
    return db.query(models.CVE).filter(models.CVE.cve_id == cve_id).first()


def get_cve(db: Session, id: uuid.UUID) -> Optional[models.CVE]:
    """Get a CVE by its UUID"""
    return db.query(models.CVE).filter(models.CVE.id == id).first()


def create_cve(db: Session, cve_data: dict) -> models.CVE:
    """Create a new CVE record"""
    cve = models.CVE(**cve_data)
    db.add(cve)
    db.commit()
    db.refresh(cve)
    return cve


def update_cve(db: Session, cve_id: str, cve_data: dict) -> Optional[models.CVE]:
    """Update an existing CVE"""
    cve = get_cve_by_cve_id(db, cve_id)
    if cve:
        for key, value in cve_data.items():
            if hasattr(cve, key):
                setattr(cve, key, value)
        db.commit()
        db.refresh(cve)
    return cve


def upsert_cve(db: Session, cve_data: dict) -> tuple[models.CVE, bool]:
    """Insert or update a CVE. Returns (cve, is_new)"""
    cve_id = cve_data.get('cve_id')
    existing = get_cve_by_cve_id(db, cve_id)
    if existing:
        for key, value in cve_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False
    else:
        cve = create_cve(db, cve_data)
        return cve, True


def get_cves(db: Session, skip: int = 0, limit: int = 100,
             severity: Optional[str] = None, search: Optional[str] = None) -> List[models.CVE]:
    """Get CVEs with optional filtering"""
    query = db.query(models.CVE)

    if severity:
        query = query.filter(models.CVE.cvss_v3_severity == severity.upper())

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.CVE.cve_id.ilike(search_pattern),
                models.CVE.description.ilike(search_pattern)
            )
        )

    return query.order_by(models.CVE.published_date.desc()).offset(skip).limit(limit).all()


def get_cve_count(db: Session) -> int:
    """Get total CVE count"""
    return db.query(models.CVE).count()


def get_cve_statistics(db: Session) -> dict:
    """Get CVE statistics"""
    total = db.query(models.CVE).count()

    severity_counts = db.query(
        models.CVE.cvss_v3_severity,
        func.count(models.CVE.id)
    ).group_by(models.CVE.cvss_v3_severity).all()

    severity_stats = {s or "UNKNOWN": c for s, c in severity_counts}

    latest_cve = db.query(models.CVE).order_by(models.CVE.published_date.desc()).first()
    oldest_cve = db.query(models.CVE).order_by(models.CVE.published_date.asc()).first()

    return {
        "total_cves": total,
        "severity_breakdown": severity_stats,
        "latest_cve_date": latest_cve.published_date if latest_cve else None,
        "oldest_cve_date": oldest_cve.published_date if oldest_cve else None,
        "cpe_match_count": db.query(models.CPEMatch).count()
    }


# ===========================
# CPE Match CRUD
# ===========================

def create_cpe_match(db: Session, cpe_data: dict) -> models.CPEMatch:
    """Create a new CPE match record"""
    cpe_match = models.CPEMatch(**cpe_data)
    db.add(cpe_match)
    db.commit()
    db.refresh(cpe_match)
    return cpe_match


def bulk_create_cpe_matches(db: Session, cpe_matches: List[dict]) -> int:
    """Bulk create CPE matches"""
    db.bulk_insert_mappings(models.CPEMatch, cpe_matches)
    db.commit()
    return len(cpe_matches)


def delete_cpe_matches_for_cve(db: Session, cve_id: uuid.UUID) -> int:
    """Delete all CPE matches for a CVE"""
    count = db.query(models.CPEMatch).filter(models.CPEMatch.cve_id == cve_id).delete()
    db.commit()
    return count


def find_cpe_matches(db: Session, vendor: str, product: str, version: Optional[str] = None) -> List[models.CPEMatch]:
    """Find CPE matches for a vendor/product/version combination"""
    query = db.query(models.CPEMatch).filter(
        models.CPEMatch.vulnerable == True,
        models.CPEMatch.cpe_vendor == vendor.lower(),
        models.CPEMatch.cpe_product == product.lower()
    )

    # If version specified, also filter by version constraints
    if version:
        # Get all matches and filter by version range in Python
        # (Complex version comparison is better done in application code)
        matches = query.all()
        return [m for m in matches if _version_matches(version, m)]

    return query.all()


def find_cves_for_service(db: Session, vendor: str, product: str, version: Optional[str] = None,
                          limit: int = 50) -> List[dict]:
    """
    Find CVEs for a vendor/product/version combination with full CVE details.
    Uses a single JOIN query instead of N+1 queries for performance.

    Args:
        db: Database session
        vendor: Vendor name (e.g., 'apache')
        product: Product name (e.g., 'httpd')
        version: Optional version string
        limit: Maximum number of CVEs to return (default 50, to prevent overwhelming results)

    Returns:
        List of dicts with CVE details, ordered by severity (highest first)
    """
    # Single query that joins CPEMatch with CVE table
    query = db.query(models.CPEMatch, models.CVE).join(
        models.CVE, models.CPEMatch.cve_id == models.CVE.id
    ).filter(
        models.CPEMatch.vulnerable == True,
        models.CPEMatch.cpe_vendor == vendor.lower(),
        models.CPEMatch.cpe_product == product.lower()
    ).order_by(
        models.CVE.cvss_v3_score.desc().nullslast()
    )

    # Get all matches first for version filtering
    all_matches = query.all()

    # Filter by version if specified
    if version:
        all_matches = [(m, c) for m, c in all_matches if _version_matches(version, m)]

    # Apply limit after version filtering
    limited_matches = all_matches[:limit]

    # Convert to dict format
    results = []
    seen_cve_ids = set()  # Avoid duplicates

    for cpe_match, cve in limited_matches:
        if cve.cve_id in seen_cve_ids:
            continue
        seen_cve_ids.add(cve.cve_id)

        results.append({
            "cve_id": cve.cve_id,
            "description": cve.description,
            "cvss_v3_score": cve.cvss_v3_score,
            "cvss_v3_severity": cve.cvss_v3_severity,
            "references": cve.references,
            "cwe_ids": cve.cwe_ids,
            "published_date": cve.published_date
        })

    return results


def _version_matches(version: str, cpe_match: models.CPEMatch) -> bool:
    """Check if a version matches the CPE version constraints"""
    from packaging import version as pkg_version

    try:
        v = pkg_version.parse(version)

        # If CPE has exact version, check exact match
        if cpe_match.cpe_version and cpe_match.cpe_version != '*':
            return str(v) == cpe_match.cpe_version or version == cpe_match.cpe_version

        # Check version ranges
        if cpe_match.version_start_including:
            try:
                if v < pkg_version.parse(cpe_match.version_start_including):
                    return False
            except:
                pass

        if cpe_match.version_start_excluding:
            try:
                if v <= pkg_version.parse(cpe_match.version_start_excluding):
                    return False
            except:
                pass

        if cpe_match.version_end_including:
            try:
                if v > pkg_version.parse(cpe_match.version_end_including):
                    return False
            except:
                pass

        if cpe_match.version_end_excluding:
            try:
                if v >= pkg_version.parse(cpe_match.version_end_excluding):
                    return False
            except:
                pass

        return True
    except:
        # If version parsing fails, do string comparison
        if cpe_match.cpe_version:
            return version == cpe_match.cpe_version
        return True


# ===========================
# Nmap Service Vulnerability CRUD
# ===========================

def create_service_vulnerability(db: Session, vuln_data: dict) -> models.NmapServiceVulnerability:
    """Create a new service vulnerability correlation"""
    vuln = models.NmapServiceVulnerability(**vuln_data)
    db.add(vuln)
    db.commit()
    db.refresh(vuln)
    return vuln


def bulk_create_service_vulnerabilities(db: Session, vulnerabilities: List[dict]) -> int:
    """Bulk create service vulnerabilities"""
    for vuln_data in vulnerabilities:
        vuln = models.NmapServiceVulnerability(**vuln_data)
        db.add(vuln)
    db.commit()
    return len(vulnerabilities)


def get_vulnerabilities_for_scan(db: Session, scan_history_id: uuid.UUID) -> List[models.NmapServiceVulnerability]:
    """Get all vulnerabilities found for a scan"""
    return db.query(models.NmapServiceVulnerability).filter(
        models.NmapServiceVulnerability.scan_history_id == scan_history_id
    ).all()


def get_vulnerabilities_with_cve_details(db: Session, scan_history_id: uuid.UUID) -> List[dict]:
    """Get vulnerabilities with full CVE details"""
    results = db.query(
        models.NmapServiceVulnerability,
        models.CVE
    ).join(
        models.CVE, models.NmapServiceVulnerability.cve_id == models.CVE.id
    ).filter(
        models.NmapServiceVulnerability.scan_history_id == scan_history_id
    ).order_by(
        models.CVE.cvss_v3_score.desc().nullslast()
    ).all()

    vulnerabilities = []
    for vuln, cve in results:
        vulnerabilities.append({
            "id": str(vuln.id),
            "host": vuln.host,
            "port": vuln.port,
            "protocol": vuln.protocol,
            "service_name": vuln.service_name,
            "service_product": vuln.service_product,
            "service_version": vuln.service_version,
            "generated_cpe": vuln.generated_cpe,
            "confidence": vuln.confidence,
            "match_type": vuln.match_type,
            "cve_id": cve.cve_id,
            "cve_description": cve.description,
            "cvss_v3_score": cve.cvss_v3_score,
            "cvss_v3_severity": cve.cvss_v3_severity,
            "cvss_v3_vector": cve.cvss_v3_vector,
            "published_date": cve.published_date.isoformat() if cve.published_date else None,
            "references": cve.references,
            "cwe_ids": cve.cwe_ids
        })

    return vulnerabilities


def delete_vulnerabilities_for_scan(db: Session, scan_history_id: uuid.UUID) -> int:
    """Delete all vulnerabilities for a scan (for re-correlation)"""
    count = db.query(models.NmapServiceVulnerability).filter(
        models.NmapServiceVulnerability.scan_history_id == scan_history_id
    ).delete()
    db.commit()
    return count


def get_vulnerability_summary(db: Session, scan_history_id: uuid.UUID) -> dict:
    """Get a summary of vulnerabilities for a scan"""
    results = db.query(
        models.CVE.cvss_v3_severity,
        func.count(models.NmapServiceVulnerability.id)
    ).join(
        models.CVE, models.NmapServiceVulnerability.cve_id == models.CVE.id
    ).filter(
        models.NmapServiceVulnerability.scan_history_id == scan_history_id
    ).group_by(models.CVE.cvss_v3_severity).all()

    severity_counts = {s or "UNKNOWN": c for s, c in results}

    total = sum(severity_counts.values())

    # Get unique hosts affected
    unique_hosts = db.query(func.count(func.distinct(models.NmapServiceVulnerability.host))).filter(
        models.NmapServiceVulnerability.scan_history_id == scan_history_id
    ).scalar()

    return {
        "total_vulnerabilities": total,
        "severity_breakdown": severity_counts,
        "unique_hosts_affected": unique_hosts or 0
    }
