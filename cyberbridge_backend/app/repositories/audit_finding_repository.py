# repositories/audit_finding_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import uuid
from typing import Optional, List
from datetime import datetime

from app.models import models


# ===========================
# Audit Finding CRUD Operations
# ===========================

def get_finding(db: Session, finding_id: uuid.UUID):
    """Get a single audit finding by ID"""
    finding = db.query(models.AuditFinding).filter(
        models.AuditFinding.id == finding_id
    ).first()

    if finding:
        _enrich_finding(db, finding)

    return finding


def get_findings_for_engagement(
    db: Session,
    engagement_id: uuid.UUID,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all findings for an engagement with optional filters"""
    query = db.query(models.AuditFinding).filter(
        models.AuditFinding.engagement_id == engagement_id
    )

    if severity:
        query = query.filter(models.AuditFinding.severity == severity)

    if category:
        query = query.filter(models.AuditFinding.category == category)

    if status:
        query = query.filter(models.AuditFinding.status == status)

    findings = query.order_by(
        models.AuditFinding.created_at.desc()
    ).offset(skip).limit(limit).all()

    # Enrich each finding
    for finding in findings:
        _enrich_finding(db, finding)

    return findings


def create_finding(
    db: Session,
    engagement_id: uuid.UUID,
    title: str,
    category: str,
    description: Optional[str] = None,
    severity: str = "medium",
    related_controls: Optional[List[str]] = None,
    related_evidence: Optional[List[str]] = None,
    remediation_plan: Optional[str] = None,
    remediation_owner_id: Optional[uuid.UUID] = None,
    remediation_due_date: Optional[datetime] = None,
    author_user_id: Optional[uuid.UUID] = None,
    author_auditor_id: Optional[uuid.UUID] = None
):
    """Create a new audit finding"""
    finding = models.AuditFinding(
        id=uuid.uuid4(),
        engagement_id=engagement_id,
        title=title,
        description=description,
        severity=severity,
        category=category,
        related_controls=related_controls,
        related_evidence=related_evidence,
        remediation_plan=remediation_plan,
        remediation_owner_id=remediation_owner_id,
        remediation_due_date=remediation_due_date,
        author_user_id=author_user_id,
        author_auditor_id=author_auditor_id,
        status="draft"
    )

    db.add(finding)
    db.commit()
    db.refresh(finding)

    _enrich_finding(db, finding)
    return finding


def update_finding(
    db: Session,
    finding_id: uuid.UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    related_controls: Optional[List[str]] = None,
    related_evidence: Optional[List[str]] = None,
    remediation_plan: Optional[str] = None,
    remediation_owner_id: Optional[uuid.UUID] = None,
    remediation_due_date: Optional[datetime] = None
):
    """Update an audit finding"""
    finding = db.query(models.AuditFinding).filter(
        models.AuditFinding.id == finding_id
    ).first()

    if not finding:
        return None

    if title is not None:
        finding.title = title

    if description is not None:
        finding.description = description

    if severity is not None:
        finding.severity = severity

    if category is not None:
        finding.category = category

    if related_controls is not None:
        finding.related_controls = related_controls

    if related_evidence is not None:
        finding.related_evidence = related_evidence

    if remediation_plan is not None:
        finding.remediation_plan = remediation_plan

    if remediation_owner_id is not None:
        finding.remediation_owner_id = remediation_owner_id

    if remediation_due_date is not None:
        finding.remediation_due_date = remediation_due_date

    db.commit()
    db.refresh(finding)

    _enrich_finding(db, finding)
    return finding


def update_finding_status(db: Session, finding_id: uuid.UUID, status: str):
    """Update finding status"""
    finding = db.query(models.AuditFinding).filter(
        models.AuditFinding.id == finding_id
    ).first()

    if not finding:
        return None

    finding.status = status
    db.commit()
    db.refresh(finding)

    _enrich_finding(db, finding)
    return finding


def delete_finding(db: Session, finding_id: uuid.UUID):
    """Delete an audit finding"""
    finding = db.query(models.AuditFinding).filter(
        models.AuditFinding.id == finding_id
    ).first()

    if not finding:
        return False

    db.delete(finding)
    db.commit()
    return True


def get_finding_count_for_engagement(db: Session, engagement_id: uuid.UUID):
    """Get count of findings for an engagement"""
    return db.query(func.count(models.AuditFinding.id)).filter(
        models.AuditFinding.engagement_id == engagement_id
    ).scalar()


def get_findings_by_severity(db: Session, engagement_id: uuid.UUID):
    """Get findings grouped by severity"""
    results = db.query(
        models.AuditFinding.severity,
        func.count(models.AuditFinding.id).label('count')
    ).filter(
        models.AuditFinding.engagement_id == engagement_id
    ).group_by(models.AuditFinding.severity).all()

    return {r.severity: r.count for r in results}


# ===========================
# Audit Sign-Off Operations
# ===========================

def get_sign_off(db: Session, sign_off_id: uuid.UUID):
    """Get a single sign-off by ID"""
    sign_off = db.query(models.AuditSignOff).filter(
        models.AuditSignOff.id == sign_off_id
    ).first()

    if sign_off:
        _enrich_sign_off(db, sign_off)

    return sign_off


def get_sign_offs_for_engagement(
    db: Session,
    engagement_id: uuid.UUID,
    sign_off_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all sign-offs for an engagement"""
    query = db.query(models.AuditSignOff).filter(
        models.AuditSignOff.engagement_id == engagement_id
    )

    if sign_off_type:
        query = query.filter(models.AuditSignOff.sign_off_type == sign_off_type)

    if status:
        query = query.filter(models.AuditSignOff.status == status)

    sign_offs = query.order_by(
        models.AuditSignOff.signed_at.desc()
    ).offset(skip).limit(limit).all()

    for sign_off in sign_offs:
        _enrich_sign_off(db, sign_off)

    return sign_offs


def get_sign_off_for_target(
    db: Session,
    engagement_id: uuid.UUID,
    sign_off_type: str,
    target_id: Optional[uuid.UUID] = None
):
    """Get sign-off for a specific target"""
    query = db.query(models.AuditSignOff).filter(
        and_(
            models.AuditSignOff.engagement_id == engagement_id,
            models.AuditSignOff.sign_off_type == sign_off_type
        )
    )

    if target_id:
        query = query.filter(models.AuditSignOff.target_id == target_id)
    else:
        query = query.filter(models.AuditSignOff.target_id == None)

    sign_off = query.order_by(models.AuditSignOff.signed_at.desc()).first()

    if sign_off:
        _enrich_sign_off(db, sign_off)

    return sign_off


def create_sign_off(
    db: Session,
    engagement_id: uuid.UUID,
    sign_off_type: str,
    status: str,
    signer_auditor_id: uuid.UUID,
    target_id: Optional[uuid.UUID] = None,
    comments: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Create a new sign-off with a digital signature."""
    from app.services import digital_signature_service

    sign_off = models.AuditSignOff(
        id=uuid.uuid4(),
        engagement_id=engagement_id,
        sign_off_type=sign_off_type,
        target_id=target_id,
        status=status,
        comments=comments,
        signer_auditor_id=signer_auditor_id,
        signed_at=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(sign_off)
    db.flush()  # populate sign_off.id and signed_at without a full commit

    # Resolve org_id via engagement → assessment → framework
    try:
        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()
        if engagement:
            assessment = db.query(models.Assessment).filter(
                models.Assessment.id == engagement.assessment_id
            ).first()
            if assessment:
                framework = db.query(models.Framework).filter(
                    models.Framework.id == assessment.framework_id
                ).first()
                if framework:
                    from app.services import digital_signature_service, timestamp_authority_service
                    payload = digital_signature_service.sign_off_payload(sign_off)
                    # Sign
                    sig_hex, key_id = digital_signature_service.sign_payload(
                        payload, framework.organisation_id, db
                    )
                    sign_off.signature = sig_hex
                    sign_off.signing_key_id = key_id
                    # Timestamp (non-blocking)
                    ts_token = timestamp_authority_service.request_timestamp(
                        payload, db, target_type="sign_off", target_id=sign_off.id
                    )
                    if ts_token:
                        sign_off.timestamp_token_id = ts_token.id
    except Exception:
        # Signing/timestamping is non-blocking — sign-off still created if it fails
        pass

    db.commit()
    db.refresh(sign_off)

    _enrich_sign_off(db, sign_off)
    return sign_off


def get_sign_off_count_for_engagement(db: Session, engagement_id: uuid.UUID):
    """Get count of sign-offs for an engagement"""
    return db.query(func.count(models.AuditSignOff.id)).filter(
        models.AuditSignOff.engagement_id == engagement_id
    ).scalar()


# ===========================
# Audit Activity Log Operations
# ===========================

def create_activity_log(
    db: Session,
    engagement_id: uuid.UUID,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    auditor_id: Optional[uuid.UUID] = None,
    target_type: Optional[str] = None,
    target_id: Optional[uuid.UUID] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Create an activity log entry with tamper-evident hash chaining."""
    from app.services import audit_log_chain_service
    import json
    from datetime import datetime, timezone

    # Resolve chain position before creating the entry
    chain_index, previous_log_hash = audit_log_chain_service.get_chain_tip(db, engagement_id)

    # Serialize details to raw JSON string (same format stored in _details column)
    details_str = json.dumps(details) if details is not None else None

    # Use a fixed timestamp so the hash is stable
    created_at = datetime.now(timezone.utc)

    log = models.AuditActivityLog(
        id=uuid.uuid4(),
        engagement_id=engagement_id,
        user_id=user_id,
        auditor_id=auditor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=created_at,
        chain_index=chain_index,
        previous_log_hash=previous_log_hash,
    )

    # Compute hash over the full entry content
    log.log_hash = audit_log_chain_service.compute_log_hash(
        chain_index=chain_index,
        engagement_id=engagement_id,
        user_id=user_id,
        auditor_id=auditor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details_str,
        ip_address=ip_address,
        created_at=created_at,
        previous_log_hash=previous_log_hash,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def get_activity_logs_for_engagement(
    db: Session,
    engagement_id: uuid.UUID,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get activity logs for an engagement"""
    query = db.query(models.AuditActivityLog).filter(
        models.AuditActivityLog.engagement_id == engagement_id
    )

    if action:
        query = query.filter(models.AuditActivityLog.action == action)

    logs = query.order_by(
        models.AuditActivityLog.created_at.desc()
    ).offset(skip).limit(limit).all()

    for log in logs:
        _enrich_activity_log(db, log)

    return logs


# ===========================
# Helper Functions
# ===========================

def _enrich_finding(db: Session, finding):
    """Add computed properties to a finding"""
    # Get author name
    if finding.author_user_id:
        user = db.query(models.User).filter(models.User.id == finding.author_user_id).first()
        finding.author_name = user.name if user else None
    elif finding.author_auditor_id:
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == finding.author_auditor_id
        ).first()
        finding.author_name = invitation.name if invitation else invitation.email if invitation else None
    else:
        finding.author_name = None

    # Get remediation owner name
    if finding.remediation_owner_id:
        user = db.query(models.User).filter(models.User.id == finding.remediation_owner_id).first()
        finding.remediation_owner_name = user.name if user else None
    else:
        finding.remediation_owner_name = None

    return finding


def _enrich_sign_off(db: Session, sign_off):
    """Add computed properties to a sign-off"""
    if sign_off.signer_auditor_id:
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == sign_off.signer_auditor_id
        ).first()
        sign_off.signer_name = invitation.name if invitation else None
        sign_off.signer_email = invitation.email if invitation else None
    else:
        sign_off.signer_name = None
        sign_off.signer_email = None

    return sign_off


def _enrich_activity_log(db: Session, log):
    """Add computed properties to an activity log"""
    if log.user_id:
        user = db.query(models.User).filter(models.User.id == log.user_id).first()
        log.actor_name = user.name if user else None
        log.actor_type = "user"
    elif log.auditor_id:
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == log.auditor_id
        ).first()
        log.actor_name = invitation.name if invitation else invitation.email if invitation else None
        log.actor_type = "auditor"
    else:
        log.actor_name = None
        log.actor_type = None

    return log
