# scan_finding_repository.py
import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import models

logger = logging.getLogger(__name__)


def get_findings_for_risk(db: Session, risk_id: uuid.UUID) -> list[dict]:
    """Get all scan findings linked to a risk, with scan context."""
    try:
        rows = (
            db.query(
                models.ScanFinding,
                models.RiskScanFinding.is_auto_mapped,
                models.ScannerHistory.scan_target,
                models.ScannerHistory.timestamp,
            )
            .join(
                models.RiskScanFinding,
                models.RiskScanFinding.finding_id == models.ScanFinding.id,
            )
            .join(
                models.ScannerHistory,
                models.ScannerHistory.id == models.ScanFinding.scan_history_id,
            )
            .filter(models.RiskScanFinding.risk_id == risk_id)
            .order_by(models.ScanFinding.created_at.desc())
            .all()
        )

        results = []
        for finding, is_auto_mapped, scan_target, scan_timestamp in rows:
            results.append({
                "id": str(finding.id),
                "scan_history_id": str(finding.scan_history_id),
                "scanner_type": finding.scanner_type,
                "title": finding.title,
                "severity": finding.severity,
                "normalized_severity": finding.normalized_severity,
                "identifier": finding.identifier,
                "description": finding.description,
                "solution": finding.solution,
                "url_or_target": finding.url_or_target,
                "is_auto_mapped": is_auto_mapped,
                "is_remediated": finding.is_remediated,
                "remediated_at": finding.remediated_at.isoformat() if finding.remediated_at else None,
                "scan_target": scan_target,
                "scan_timestamp": scan_timestamp.isoformat() if scan_timestamp else None,
                "created_at": finding.created_at.isoformat() if finding.created_at else None,
            })
        return results
    except Exception as e:
        logger.error(f"Error getting findings for risk {risk_id}: {e}")
        return []


def get_risks_for_finding(db: Session, finding_id: uuid.UUID) -> list[dict]:
    """Get all risks linked to a finding."""
    try:
        rows = (
            db.query(models.Risks)
            .join(
                models.RiskScanFinding,
                models.RiskScanFinding.risk_id == models.Risks.id,
            )
            .filter(models.RiskScanFinding.finding_id == finding_id)
            .all()
        )

        return [
            {
                "id": str(risk.id),
                "risk_code": risk.risk_code,
                "risk_category_name": risk.risk_category_name,
            }
            for risk in rows
        ]
    except Exception as e:
        logger.error(f"Error getting risks for finding {finding_id}: {e}")
        return []


def get_finding_counts_for_risks(db: Session, risk_ids: list[uuid.UUID]) -> dict:
    """Batch query: return {risk_id: count} dict of linked findings per risk."""
    if not risk_ids:
        return {}
    try:
        rows = (
            db.query(
                models.RiskScanFinding.risk_id,
                func.count(models.RiskScanFinding.finding_id),
            )
            .filter(models.RiskScanFinding.risk_id.in_(risk_ids))
            .group_by(models.RiskScanFinding.risk_id)
            .all()
        )
        return {risk_id: count for risk_id, count in rows}
    except Exception as e:
        logger.error(f"Error getting finding counts for risks: {e}")
        return {}


def link_finding_to_risk(db: Session, finding_id: uuid.UUID, risk_id: uuid.UUID, is_auto: bool = False) -> bool:
    """Idempotently link a finding to a risk."""
    try:
        existing = db.query(models.RiskScanFinding).filter(
            models.RiskScanFinding.risk_id == risk_id,
            models.RiskScanFinding.finding_id == finding_id,
        ).first()
        if existing:
            return True

        junction = models.RiskScanFinding(
            risk_id=risk_id,
            finding_id=finding_id,
            is_auto_mapped=is_auto,
        )
        db.add(junction)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking finding {finding_id} to risk {risk_id}: {e}")
        return False


def unlink_finding_from_risk(db: Session, finding_id: uuid.UUID, risk_id: uuid.UUID) -> bool:
    """Remove the junction entry between a finding and a risk."""
    try:
        deleted = db.query(models.RiskScanFinding).filter(
            models.RiskScanFinding.risk_id == risk_id,
            models.RiskScanFinding.finding_id == finding_id,
        ).delete()
        db.commit()
        return deleted > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking finding {finding_id} from risk {risk_id}: {e}")
        return False


def _build_all_findings_query(
    db: Session,
    organisation_id: uuid.UUID,
    scanner_type: Optional[str] = None,
    severity: Optional[str] = None,
    has_risks: Optional[bool] = None,
    search: Optional[str] = None,
    is_remediated: Optional[bool] = None,
):
    """Build the base query for get_all_findings / get_all_findings_count."""
    query = (
        db.query(
            models.ScanFinding,
            models.ScannerHistory.scan_target,
            models.ScannerHistory.timestamp,
        )
        .join(
            models.ScannerHistory,
            models.ScannerHistory.id == models.ScanFinding.scan_history_id,
        )
        .filter(models.ScanFinding.organisation_id == organisation_id)
    )

    if scanner_type:
        query = query.filter(models.ScanFinding.scanner_type == scanner_type)

    if severity:
        query = query.filter(models.ScanFinding.normalized_severity == severity.lower())

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (models.ScanFinding.title.ilike(pattern))
            | (models.ScanFinding.identifier.ilike(pattern))
            | (models.ScanFinding.description.ilike(pattern))
        )

    if has_risks is not None:
        risk_subq = (
            db.query(models.RiskScanFinding.finding_id)
            .filter(models.RiskScanFinding.finding_id == models.ScanFinding.id)
            .correlate(models.ScanFinding)
            .exists()
        )
        if has_risks:
            query = query.filter(risk_subq)
        else:
            query = query.filter(~risk_subq)

    if is_remediated is not None:
        query = query.filter(models.ScanFinding.is_remediated == is_remediated)

    return query


def get_all_findings(
    db: Session,
    organisation_id: uuid.UUID,
    scanner_type: Optional[str] = None,
    severity: Optional[str] = None,
    has_risks: Optional[bool] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    is_remediated: Optional[bool] = None,
) -> list[dict]:
    """Paginated query returning findings with scan context."""
    try:
        query = _build_all_findings_query(db, organisation_id, scanner_type, severity, has_risks, search, is_remediated)
        rows = (
            query
            .order_by(models.ScanFinding.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for finding, scan_target, scan_timestamp in rows:
            results.append({
                "id": str(finding.id),
                "scan_history_id": str(finding.scan_history_id),
                "scanner_type": finding.scanner_type,
                "title": finding.title,
                "severity": finding.severity,
                "normalized_severity": finding.normalized_severity,
                "identifier": finding.identifier,
                "description": finding.description,
                "solution": finding.solution,
                "url_or_target": finding.url_or_target,
                "extra_data": finding.extra_data,
                "is_remediated": finding.is_remediated,
                "remediated_at": finding.remediated_at.isoformat() if finding.remediated_at else None,
                "remediated_by": str(finding.remediated_by) if finding.remediated_by else None,
                "scan_target": scan_target,
                "scan_timestamp": scan_timestamp.isoformat() if scan_timestamp else None,
                "created_at": finding.created_at.isoformat() if finding.created_at else None,
            })
        return results
    except Exception as e:
        logger.error(f"Error getting all findings: {e}")
        return []


def get_all_findings_count(
    db: Session,
    organisation_id: uuid.UUID,
    scanner_type: Optional[str] = None,
    severity: Optional[str] = None,
    has_risks: Optional[bool] = None,
    search: Optional[str] = None,
    is_remediated: Optional[bool] = None,
) -> int:
    """Count query with same filters for pagination."""
    try:
        base = _build_all_findings_query(db, organisation_id, scanner_type, severity, has_risks, search, is_remediated)
        return base.count()
    except Exception as e:
        logger.error(f"Error counting findings: {e}")
        return 0


def get_findings_stats(db: Session, organisation_id: uuid.UUID) -> dict:
    """Aggregate stats: total, by_scanner, by_severity, linked_to_risks."""
    try:
        base = db.query(models.ScanFinding).filter(
            models.ScanFinding.organisation_id == organisation_id
        )
        total = base.count()

        by_scanner_rows = (
            base.with_entities(models.ScanFinding.scanner_type, func.count(models.ScanFinding.id))
            .group_by(models.ScanFinding.scanner_type)
            .all()
        )
        by_scanner = {scanner: count for scanner, count in by_scanner_rows}

        by_severity_rows = (
            base.with_entities(models.ScanFinding.normalized_severity, func.count(models.ScanFinding.id))
            .group_by(models.ScanFinding.normalized_severity)
            .all()
        )
        by_severity = {(sev or "unknown"): count for sev, count in by_severity_rows}

        linked_to_risks = (
            db.query(func.count(func.distinct(models.RiskScanFinding.finding_id)))
            .join(models.ScanFinding, models.ScanFinding.id == models.RiskScanFinding.finding_id)
            .filter(models.ScanFinding.organisation_id == organisation_id)
            .scalar()
        ) or 0

        remediated = base.filter(models.ScanFinding.is_remediated == True).count()

        return {
            "total": total,
            "by_scanner": by_scanner,
            "by_severity": by_severity,
            "linked_to_risks": linked_to_risks,
            "remediated": remediated,
        }
    except Exception as e:
        logger.error(f"Error getting findings stats: {e}")
        return {"total": 0, "by_scanner": {}, "by_severity": {}, "linked_to_risks": 0, "remediated": 0}


def get_risk_counts_for_findings(db: Session, finding_ids: list[uuid.UUID]) -> dict:
    """Batch query returning {finding_id: count} for risk link badges."""
    if not finding_ids:
        return {}
    try:
        rows = (
            db.query(
                models.RiskScanFinding.finding_id,
                func.count(models.RiskScanFinding.risk_id),
            )
            .filter(models.RiskScanFinding.finding_id.in_(finding_ids))
            .group_by(models.RiskScanFinding.finding_id)
            .all()
        )
        return {str(fid): count for fid, count in rows}
    except Exception as e:
        logger.error(f"Error getting risk counts for findings: {e}")
        return {}


def get_findings_for_suggestion(db: Session, organisation_id: uuid.UUID, limit: int = 200) -> tuple[list[dict], dict]:
    """Return findings sorted by severity (critical first), prioritizing unremediated, plus stats dict.
    Returns (findings_list, stats_dict) in a single pass to avoid two DB calls."""
    try:
        from app.constants.assessment_scan_rules import SEVERITY_ORDER

        base = db.query(models.ScanFinding).filter(
            models.ScanFinding.organisation_id == organisation_id
        )
        total = base.count()
        if total == 0:
            return [], {"total": 0, "by_scanner": {}, "by_severity": {}, "remediated": 0}

        # Stats aggregation
        by_scanner_rows = (
            base.with_entities(models.ScanFinding.scanner_type, func.count(models.ScanFinding.id))
            .group_by(models.ScanFinding.scanner_type).all()
        )
        by_scanner = {scanner: count for scanner, count in by_scanner_rows}

        by_severity_rows = (
            base.with_entities(models.ScanFinding.normalized_severity, func.count(models.ScanFinding.id))
            .group_by(models.ScanFinding.normalized_severity).all()
        )
        by_severity = {(sev or "unknown"): count for sev, count in by_severity_rows}

        remediated_count = base.filter(models.ScanFinding.is_remediated == True).count()

        stats = {
            "total": total,
            "by_scanner": by_scanner,
            "by_severity": by_severity,
            "remediated": remediated_count,
        }

        # Fetch findings: unremediated first, then by severity
        rows = (
            base
            .order_by(
                models.ScanFinding.is_remediated.asc(),  # unremediated first
                models.ScanFinding.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

        # Sort in Python by severity since normalized_severity is text
        def severity_key(f):
            return SEVERITY_ORDER.get((f.normalized_severity or "").lower(), 5)

        rows_sorted = sorted(rows, key=lambda f: (f.is_remediated, severity_key(f)))

        findings = []
        for f in rows_sorted:
            findings.append({
                "id": str(f.id),
                "scanner_type": f.scanner_type,
                "title": f.title,
                "severity": f.severity,
                "normalized_severity": f.normalized_severity,
                "identifier": f.identifier,
                "description": f.description,
                "solution": f.solution,
                "url_or_target": f.url_or_target,
                "is_remediated": f.is_remediated,
            })

        return findings, stats
    except Exception as e:
        logger.error(f"Error getting findings for suggestion: {e}")
        return [], {"total": 0, "by_scanner": {}, "by_severity": {}, "remediated": 0}


def toggle_remediation(db: Session, finding_id: uuid.UUID, user_id: uuid.UUID) -> Optional[dict]:
    """Toggle the is_remediated flag on a scan finding."""
    try:
        finding = db.query(models.ScanFinding).filter(models.ScanFinding.id == finding_id).first()
        if not finding:
            return None

        new_value = not finding.is_remediated
        finding.is_remediated = new_value
        if new_value:
            finding.remediated_at = datetime.utcnow()
            finding.remediated_by = user_id
        else:
            finding.remediated_at = None
            finding.remediated_by = None

        db.commit()
        db.refresh(finding)

        return {
            "id": str(finding.id),
            "is_remediated": finding.is_remediated,
            "remediated_at": finding.remediated_at.isoformat() if finding.remediated_at else None,
            "remediated_by": str(finding.remediated_by) if finding.remediated_by else None,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling remediation for finding {finding_id}: {e}")
        return None
