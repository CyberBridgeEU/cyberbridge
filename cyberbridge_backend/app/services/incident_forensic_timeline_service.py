# services/incident_forensic_timeline_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import uuid

from ..models import models


def get_incident_timeline(db: Session, incident_id: uuid.UUID, current_user) -> List[Dict[str, Any]]:
    """
    Aggregate forensic timeline events for a given incident from multiple sources:
    - Incident lifecycle changes (History table)
    - Patches (IncidentPatches)
    - ENISA notifications (ENISANotifications)
    - Security advisories (SecurityAdvisories)
    - Evidence linked to the incident (IncidentEvidence)
    """
    events: List[Dict[str, Any]] = []
    incident_id_str = str(incident_id)

    # ------------------------------------------------------------------
    # 1. Incident lifecycle events from the History table
    # ------------------------------------------------------------------
    FIELD_LABELS = {
        "incident_status_id": "Status",
        "incident_severity_id": "Severity",
        "assigned_to": "Assignee",
        "reported_by": "Reported By",
        "discovered_at": "Discovered At",
        "resolved_at": "Resolved At",
        "containment_actions": "Containment Actions",
        "root_cause": "Root Cause",
        "remediation_steps": "Remediation Steps",
        "triage_status": "Triage Status",
        "cve_id": "CVE",
        "cwe_id": "CWE",
        "cvss_score": "CVSS Score",
        "affected_products": "Affected Products",
        "ai_analysis": "AI Analysis",
    }

    history_entries = (
        db.query(models.History)
        .filter(
            models.History.table_name_changed == "incidents",
            models.History.record_id == incident_id_str,
        )
        .order_by(models.History.last_timestamp)
        .all()
    )

    for entry in history_entries:
        ts = entry.last_timestamp.isoformat() if entry.last_timestamp else None

        if entry.action == "insert":
            new_data = json.loads(entry.new_data) if entry.new_data else {}
            events.append({
                "timestamp": ts,
                "event_type": "incident_created",
                "title": "Incident Created",
                "description": f"Incident reported: {new_data.get('title', '')}",
                "actor": entry.last_user_email,
                "metadata": new_data,
            })

        elif entry.action == "update":
            column = entry.column_name or "field"
            old_data = json.loads(entry.old_data) if entry.old_data else {}
            new_data = json.loads(entry.new_data) if entry.new_data else {}
            old_val = old_data.get("value", "")
            new_val = new_data.get("value", "")
            label = FIELD_LABELS.get(column, column.replace("_", " ").title())
            events.append({
                "timestamp": ts,
                "event_type": "field_updated",
                "title": f"{label} Updated",
                "description": f"Changed from '{old_val}' to '{new_val}'",
                "actor": entry.last_user_email,
                "metadata": {"column": column, "old": old_val, "new": new_val},
            })

    # ------------------------------------------------------------------
    # 2. Patch releases
    # ------------------------------------------------------------------
    patches = (
        db.query(models.IncidentPatches)
        .filter(models.IncidentPatches.incident_id == incident_id)
        .order_by(models.IncidentPatches.created_at)
        .all()
    )

    for patch in patches:
        events.append({
            "timestamp": patch.created_at.isoformat() if patch.created_at else None,
            "event_type": "patch_released",
            "title": f"Patch {patch.patch_version} Recorded",
            "description": patch.description or f"Patch version {patch.patch_version}",
            "actor": None,
            "metadata": {
                "patch_version": patch.patch_version,
                "sla_compliance": patch.sla_compliance,
                "release_date": patch.release_date.isoformat() if patch.release_date else None,
                "target_sla_date": patch.target_sla_date.isoformat() if patch.target_sla_date else None,
            },
        })

    # ------------------------------------------------------------------
    # 3. ENISA notification milestones
    # ------------------------------------------------------------------
    enisa = (
        db.query(models.ENISANotifications)
        .filter(models.ENISANotifications.incident_id == incident_id)
        .first()
    )

    if enisa:
        events.append({
            "timestamp": enisa.created_at.isoformat() if enisa.created_at else None,
            "event_type": "enisa_notification",
            "title": "ENISA Reporting Initialized",
            "description": f"ENISA reporting status: {enisa.reporting_status or 'pending'}",
            "actor": None,
            "metadata": {"reporting_status": enisa.reporting_status},
        })
        if enisa.early_warning_submitted and enisa.early_warning_submitted_at:
            events.append({
                "timestamp": enisa.early_warning_submitted_at.isoformat(),
                "event_type": "enisa_notification",
                "title": "ENISA Early Warning Submitted",
                "description": "24-hour early warning notification submitted to ENISA",
                "actor": None,
                "metadata": {},
            })
        if enisa.vuln_notification_submitted and enisa.vuln_notification_submitted_at:
            events.append({
                "timestamp": enisa.vuln_notification_submitted_at.isoformat(),
                "event_type": "enisa_notification",
                "title": "ENISA Vulnerability Notification Submitted",
                "description": "72-hour vulnerability notification submitted to ENISA",
                "actor": None,
                "metadata": {},
            })
        if enisa.final_report_submitted and enisa.final_report_submitted_at:
            events.append({
                "timestamp": enisa.final_report_submitted_at.isoformat(),
                "event_type": "enisa_notification",
                "title": "ENISA Final Report Submitted",
                "description": "Final incident report submitted to ENISA",
                "actor": None,
                "metadata": {},
            })

    # ------------------------------------------------------------------
    # 4. Security advisories linked to this incident
    # ------------------------------------------------------------------
    advisories = (
        db.query(models.SecurityAdvisories)
        .filter(models.SecurityAdvisories.incident_id == incident_id)
        .order_by(models.SecurityAdvisories.created_at)
        .all()
    )

    for adv in advisories:
        status = getattr(adv.advisory_status, "status_name", None) if adv.advisory_status else None
        events.append({
            "timestamp": adv.created_at.isoformat() if adv.created_at else None,
            "event_type": "advisory_published",
            "title": f"Security Advisory: {adv.advisory_code or adv.title}",
            "description": adv.title,
            "actor": None,
            "metadata": {
                "advisory_code": adv.advisory_code,
                "severity": adv.severity,
                "status": status,
                "published_at": adv.published_at.isoformat() if adv.published_at else None,
            },
        })

    # ------------------------------------------------------------------
    # 5. Evidence linked to this incident
    # ------------------------------------------------------------------
    incident_evidences = (
        db.query(models.IncidentEvidence)
        .filter(models.IncidentEvidence.incident_id == incident_id)
        .order_by(models.IncidentEvidence.created_at)
        .all()
    )

    for ie in incident_evidences:
        evidence = (
            db.query(models.EvidenceLibraryItem)
            .filter(models.EvidenceLibraryItem.id == ie.evidence_id)
            .first()
        )
        if evidence:
            events.append({
                "timestamp": ie.created_at.isoformat() if ie.created_at else None,
                "event_type": "evidence_linked",
                "title": f"Evidence Attached: {evidence.name}",
                "description": f"'{evidence.name}' ({evidence.evidence_type}) linked to incident",
                "actor": None,
                "metadata": {
                    "evidence_id": str(evidence.id),
                    "evidence_name": evidence.name,
                    "evidence_type": evidence.evidence_type,
                    "custody_status": evidence.custody_status,
                    "collection_method": evidence.collection_method,
                },
            })

    # Sort all events chronologically
    events.sort(key=lambda e: e["timestamp"] or "")
    return events


def get_linked_evidence(db: Session, incident_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Return evidence items currently linked to the incident."""
    rows = (
        db.query(models.IncidentEvidence)
        .filter(models.IncidentEvidence.incident_id == incident_id)
        .all()
    )
    result = []
    for row in rows:
        ev = db.query(models.EvidenceLibraryItem).filter(models.EvidenceLibraryItem.id == row.evidence_id).first()
        if ev:
            result.append({
                "id": str(ev.id),
                "name": ev.name,
                "evidence_type": ev.evidence_type,
                "custody_status": ev.custody_status,
                "collection_method": ev.collection_method,
                "status": ev.status,
                "linked_at": row.created_at.isoformat() if row.created_at else None,
            })
    return result


def link_evidence(db: Session, incident_id: uuid.UUID, evidence_id: uuid.UUID) -> bool:
    existing = (
        db.query(models.IncidentEvidence)
        .filter(
            models.IncidentEvidence.incident_id == incident_id,
            models.IncidentEvidence.evidence_id == evidence_id,
        )
        .first()
    )
    if existing:
        return False
    db.add(models.IncidentEvidence(incident_id=incident_id, evidence_id=evidence_id))
    db.commit()
    return True


def unlink_evidence(db: Session, incident_id: uuid.UUID, evidence_id: uuid.UUID) -> bool:
    row = (
        db.query(models.IncidentEvidence)
        .filter(
            models.IncidentEvidence.incident_id == incident_id,
            models.IncidentEvidence.evidence_id == evidence_id,
        )
        .first()
    )
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
