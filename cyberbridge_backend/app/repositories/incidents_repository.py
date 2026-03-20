# incidents_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import datetime, timedelta
import re
import uuid
import logging
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


SLA_HOURS = {"Critical": 24, "High": 72, "Medium": 168, "Low": 720}  # 24h, 72h, 7d, 30d


def _calculate_sla_deadline(db: Session, severity_id, discovered_at):
    """Calculate SLA deadline based on severity and discovery date."""
    if not severity_id or not discovered_at:
        return None
    severity = db.query(models.RiskSeverity).filter(models.RiskSeverity.id == severity_id).first()
    if not severity:
        return None
    hours = SLA_HOURS.get(severity.risk_severity_name, 720)
    return discovered_at + timedelta(hours=hours)


def _compute_sla_status(sla_deadline):
    """Compute SLA status based on deadline vs current time."""
    if not sla_deadline:
        return None
    now = datetime.utcnow()
    if now > sla_deadline:
        return "overdue"
    remaining = (sla_deadline - now).total_seconds()
    total = 24 * 3600  # 24h warning threshold
    if remaining < total:
        return "at_risk"
    return "on_time"


def get_next_incident_code(db: Session, organisation_id) -> str:
    """Generate next INC-N code for the given organisation."""
    existing_codes = db.query(models.Incidents.incident_code).filter(
        models.Incidents.organisation_id == organisation_id,
        models.Incidents.incident_code.isnot(None)
    ).all()

    max_n = 0
    for (code,) in existing_codes:
        match = re.match(r'^INC-(\d+)$', code or '')
        if match:
            max_n = max(max_n, int(match.group(1)))

    return f"INC-{max_n + 1}"


def _enrich_incident(db: Session, incident):
    """Add severity name, status name, user email, linked counts."""
    try:
        # Get severity name
        severity = db.query(models.RiskSeverity).filter(
            models.RiskSeverity.id == incident.incident_severity_id
        ).first()
        if severity:
            incident.incident_severity = severity.risk_severity_name

        # Get status name
        status = db.query(models.IncidentStatuses).filter(
            models.IncidentStatuses.id == incident.incident_status_id
        ).first()
        if status:
            incident.incident_status = status.incident_status_name

        # Get last updated by email
        if incident.last_updated_by:
            user = db.query(models.User).filter(models.User.id == incident.last_updated_by).first()
            incident.last_updated_by_email = user.email if user else None
        else:
            incident.last_updated_by_email = None

        # Compute SLA status dynamically
        incident.sla_status = _compute_sla_status(incident.sla_deadline)

        # Linked counts
        incident.linked_frameworks_count = db.query(models.IncidentFramework).filter(
            models.IncidentFramework.incident_id == incident.id
        ).count()
        incident.linked_risks_count = db.query(models.IncidentRisk).filter(
            models.IncidentRisk.incident_id == incident.id
        ).count()
        incident.linked_assets_count = db.query(models.IncidentAsset).filter(
            models.IncidentAsset.incident_id == incident.id
        ).count()

    except Exception as e:
        logger.error(f"Error enriching incident {incident.id}: {str(e)}")


def get_incidents(db: Session, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.Incidents)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Incidents.organisation_id == current_user.organisation_id)

        incidents = query.order_by(models.Incidents.created_at.desc()).all()
        for incident in incidents:
            _enrich_incident(db, incident)
        return incidents
    except Exception as e:
        logger.error(f"Error getting incidents: {str(e)}")
        return []


def get_incident(db: Session, incident_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.Incidents).filter(models.Incidents.id == incident_id)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Incidents.organisation_id == current_user.organisation_id)
        incident = query.first()
        if incident:
            _enrich_incident(db, incident)
        return incident
    except Exception as e:
        logger.error(f"Error getting incident {incident_id}: {str(e)}")
        return None


def get_incident_statuses(db: Session):
    try:
        return db.query(models.IncidentStatuses).all()
    except Exception as e:
        logger.error(f"Error getting incident statuses: {str(e)}")
        return []


def create_incident(db: Session, incident: dict, current_user: schemas.UserBase = None):
    try:
        organisation_id = current_user.organisation_id if current_user else None

        # Auto-generate code if not provided
        incident_code = incident.get("incident_code")
        if not incident_code and organisation_id:
            incident_code = get_next_incident_code(db, organisation_id)

        severity_id = uuid.UUID(incident["incident_severity_id"])
        discovered_at = incident.get("discovered_at")
        sla_deadline = _calculate_sla_deadline(db, severity_id, discovered_at)

        db_incident = models.Incidents(
            incident_code=incident_code,
            title=incident["title"],
            description=incident.get("description"),
            incident_severity_id=severity_id,
            incident_status_id=uuid.UUID(incident["incident_status_id"]),
            reported_by=incident.get("reported_by"),
            assigned_to=incident.get("assigned_to"),
            discovered_at=discovered_at,
            resolved_at=incident.get("resolved_at"),
            containment_actions=incident.get("containment_actions"),
            root_cause=incident.get("root_cause"),
            remediation_steps=incident.get("remediation_steps"),
            vulnerability_source=incident.get("vulnerability_source"),
            cvss_score=incident.get("cvss_score"),
            cve_id=incident.get("cve_id"),
            cwe_id=incident.get("cwe_id"),
            triage_status=incident.get("triage_status"),
            affected_products=incident.get("affected_products"),
            sla_deadline=sla_deadline,
            organisation_id=organisation_id,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None,
        )
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        _enrich_incident(db, db_incident)
        return db_incident
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating incident: {str(e)}")
        raise


def update_incident(db: Session, incident_id: uuid.UUID, incident: dict, current_user: schemas.UserBase = None):
    try:
        db_incident = get_incident(db, incident_id, current_user)
        if not db_incident:
            return None

        db_incident.incident_code = incident.get("incident_code") or db_incident.incident_code
        db_incident.title = incident["title"]
        db_incident.description = incident.get("description")
        db_incident.incident_severity_id = uuid.UUID(incident["incident_severity_id"])
        db_incident.incident_status_id = uuid.UUID(incident["incident_status_id"])
        db_incident.reported_by = incident.get("reported_by")
        db_incident.assigned_to = incident.get("assigned_to")
        db_incident.discovered_at = incident.get("discovered_at")
        db_incident.resolved_at = incident.get("resolved_at")
        db_incident.containment_actions = incident.get("containment_actions")
        db_incident.root_cause = incident.get("root_cause")
        db_incident.remediation_steps = incident.get("remediation_steps")
        # Post-market triage fields
        db_incident.vulnerability_source = incident.get("vulnerability_source")
        db_incident.cvss_score = incident.get("cvss_score")
        db_incident.cve_id = incident.get("cve_id")
        db_incident.cwe_id = incident.get("cwe_id")
        db_incident.triage_status = incident.get("triage_status")
        db_incident.affected_products = incident.get("affected_products")
        # Recalculate SLA if severity or discovered_at changed
        severity_id = uuid.UUID(incident["incident_severity_id"])
        discovered_at = incident.get("discovered_at")
        db_incident.sla_deadline = _calculate_sla_deadline(db, severity_id, discovered_at)
        db_incident.last_updated_by = current_user.id if current_user else None

        db.commit()
        db.refresh(db_incident)
        _enrich_incident(db, db_incident)
        return db_incident
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating incident {incident_id}: {str(e)}")
        raise


def delete_incident(db: Session, incident_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        db_incident = get_incident(db, incident_id, current_user)
        if not db_incident:
            return None

        if current_user and current_user.role_name == "org_user":
            if db_incident.created_by != current_user.id:
                raise ValueError("org_user can only delete their own incidents")

        db.delete(db_incident)
        db.commit()
        return db_incident
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting incident {incident_id}: {str(e)}")
        raise


def save_ai_analysis(db: Session, incident_id: uuid.UUID, analysis: str, current_user: schemas.UserBase = None):
    """Save AI analysis result to incident."""
    try:
        db_incident = get_incident(db, incident_id, current_user)
        if not db_incident:
            return None
        db_incident.ai_analysis = analysis
        db_incident.last_updated_by = current_user.id if current_user else None
        db.commit()
        db.refresh(db_incident)
        _enrich_incident(db, db_incident)
        return db_incident
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving AI analysis for incident {incident_id}: {str(e)}")
        raise


# ===========================
# Connection operations
# ===========================

def get_frameworks_for_incident(db: Session, incident_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        links = db.query(models.IncidentFramework).filter(
            models.IncidentFramework.incident_id == incident_id
        ).all()
        framework_ids = [link.framework_id for link in links]
        if not framework_ids:
            return []

        query = db.query(models.Framework).filter(models.Framework.id.in_(framework_ids))
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Framework.organisation_id == current_user.organisation_id)
        return query.all()
    except Exception as e:
        logger.error(f"Error getting frameworks for incident {incident_id}: {str(e)}")
        return []


def link_framework(db: Session, incident_id: uuid.UUID, framework_id: uuid.UUID):
    try:
        existing = db.query(models.IncidentFramework).filter(
            models.IncidentFramework.incident_id == incident_id,
            models.IncidentFramework.framework_id == framework_id
        ).first()
        if existing:
            return True
        link = models.IncidentFramework(incident_id=incident_id, framework_id=framework_id)
        db.add(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking framework to incident: {str(e)}")
        return False


def unlink_framework(db: Session, incident_id: uuid.UUID, framework_id: uuid.UUID):
    try:
        link = db.query(models.IncidentFramework).filter(
            models.IncidentFramework.incident_id == incident_id,
            models.IncidentFramework.framework_id == framework_id
        ).first()
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking framework from incident: {str(e)}")
        return False


def get_risks_for_incident(db: Session, incident_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        links = db.query(models.IncidentRisk).filter(
            models.IncidentRisk.incident_id == incident_id
        ).all()
        risk_ids = [link.risk_id for link in links]
        if not risk_ids:
            return []

        query = db.query(models.Risks).filter(models.Risks.id.in_(risk_ids))
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Risks.organisation_id == current_user.organisation_id)

        risks = query.all()
        from app.repositories import risks_repository
        for risk in risks:
            risks_repository._enrich_risk_with_info(db, risk)
        return risks
    except Exception as e:
        logger.error(f"Error getting risks for incident {incident_id}: {str(e)}")
        return []


def link_risk(db: Session, incident_id: uuid.UUID, risk_id: uuid.UUID):
    try:
        existing = db.query(models.IncidentRisk).filter(
            models.IncidentRisk.incident_id == incident_id,
            models.IncidentRisk.risk_id == risk_id
        ).first()
        if existing:
            return True
        link = models.IncidentRisk(incident_id=incident_id, risk_id=risk_id)
        db.add(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking risk to incident: {str(e)}")
        return False


def unlink_risk(db: Session, incident_id: uuid.UUID, risk_id: uuid.UUID):
    try:
        link = db.query(models.IncidentRisk).filter(
            models.IncidentRisk.incident_id == incident_id,
            models.IncidentRisk.risk_id == risk_id
        ).first()
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking risk from incident: {str(e)}")
        return False


def get_assets_for_incident(db: Session, incident_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        links = db.query(models.IncidentAsset).filter(
            models.IncidentAsset.incident_id == incident_id
        ).all()
        asset_ids = [link.asset_id for link in links]
        if not asset_ids:
            return []

        query = db.query(models.Assets).filter(models.Assets.id.in_(asset_ids))
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Assets.organisation_id == current_user.organisation_id)

        assets = query.all()
        from app.repositories import assets_repository
        for asset in assets:
            assets_repository._enrich_asset_with_info(db, asset)
        return assets
    except Exception as e:
        logger.error(f"Error getting assets for incident {incident_id}: {str(e)}")
        return []


def link_asset(db: Session, incident_id: uuid.UUID, asset_id: uuid.UUID):
    try:
        existing = db.query(models.IncidentAsset).filter(
            models.IncidentAsset.incident_id == incident_id,
            models.IncidentAsset.asset_id == asset_id
        ).first()
        if existing:
            return True
        link = models.IncidentAsset(incident_id=incident_id, asset_id=asset_id)
        db.add(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking asset to incident: {str(e)}")
        return False


def unlink_asset(db: Session, incident_id: uuid.UUID, asset_id: uuid.UUID):
    try:
        link = db.query(models.IncidentAsset).filter(
            models.IncidentAsset.incident_id == incident_id,
            models.IncidentAsset.asset_id == asset_id
        ).first()
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking asset from incident: {str(e)}")
        return False


# ===========================
# Post-Market Metrics
# ===========================

def get_post_market_metrics(db: Session, current_user: schemas.UserBase = None):
    """Aggregated post-market surveillance metrics."""
    try:
        query = db.query(models.Incidents)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Incidents.organisation_id == current_user.organisation_id)

        incidents = query.all()
        now = datetime.utcnow()

        total = len(incidents)
        open_vulns = sum(1 for i in incidents if i.triage_status and i.triage_status not in ("Fixed", "Verified", "Closed"))
        overdue = sum(1 for i in incidents if i.sla_deadline and now > i.sla_deadline and i.resolved_at is None)
        at_risk = sum(1 for i in incidents if i.sla_deadline and i.resolved_at is None and _compute_sla_status(i.sla_deadline) == "at_risk")

        # Avg resolution time for resolved incidents
        resolved = [i for i in incidents if i.resolved_at and i.discovered_at]
        avg_hours = None
        if resolved:
            total_hours = sum((i.resolved_at - i.discovered_at).total_seconds() / 3600 for i in resolved)
            avg_hours = round(total_hours / len(resolved), 1)

        # SLA compliance rate
        sla_incidents = [i for i in incidents if i.sla_deadline and i.resolved_at]
        sla_rate = None
        if sla_incidents:
            on_time = sum(1 for i in sla_incidents if i.resolved_at <= i.sla_deadline)
            sla_rate = round(on_time / len(sla_incidents) * 100, 1)

        # Patches count
        patch_query = db.query(sql_func.count(models.IncidentPatches.id))
        if current_user and current_user.role_name != "super_admin":
            patch_query = patch_query.filter(models.IncidentPatches.organisation_id == current_user.organisation_id)
        patches_count = patch_query.scalar() or 0

        # Advisories published
        adv_query = db.query(sql_func.count(models.SecurityAdvisories.id)).filter(
            models.SecurityAdvisories.published_at.isnot(None)
        )
        if current_user and current_user.role_name != "super_admin":
            adv_query = adv_query.filter(models.SecurityAdvisories.organisation_id == current_user.organisation_id)
        advisories_published = adv_query.scalar() or 0

        # ENISA counts
        enisa_query = db.query(models.ENISANotifications)
        if current_user and current_user.role_name != "super_admin":
            enisa_query = enisa_query.filter(models.ENISANotifications.organisation_id == current_user.organisation_id)
        enisa_all = enisa_query.all()
        enisa_complete = sum(1 for n in enisa_all if _compute_reporting_status_simple(n))
        enisa_pending = len(enisa_all) - enisa_complete

        return {
            "total_incidents": total,
            "open_vulnerabilities": open_vulns,
            "overdue_count": overdue,
            "at_risk_count": at_risk,
            "avg_resolution_hours": avg_hours,
            "sla_compliance_rate": sla_rate,
            "patches_released": patches_count,
            "advisories_published": advisories_published,
            "enisa_pending": enisa_pending,
            "enisa_complete": enisa_complete,
        }
    except Exception as e:
        logger.error(f"Error getting post-market metrics: {str(e)}")
        return {}


def _compute_reporting_status_simple(notification):
    """Simple check if all required ENISA phases are submitted."""
    phases = []
    if notification.early_warning_required:
        phases.append(notification.early_warning_submitted)
    if notification.vuln_notification_required:
        phases.append(notification.vuln_notification_submitted)
    if notification.final_report_required:
        phases.append(notification.final_report_submitted)
    return all(phases) if phases else False
