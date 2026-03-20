# repositories/audit_engagement_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
from typing import Optional, List
from datetime import datetime

from app.models import models


# ===========================
# Audit Engagement CRUD Operations
# ===========================

def get_audit_engagement(db: Session, engagement_id: uuid.UUID):
    """Get a single audit engagement by ID"""
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()

    if engagement:
        _enrich_engagement(db, engagement)

    return engagement


def get_audit_engagements(
    db: Session,
    organisation_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    owner_id: Optional[uuid.UUID] = None
):
    """Get all audit engagements for an organization with optional filters"""
    query = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.organisation_id == organisation_id
    )

    if status:
        query = query.filter(models.AuditEngagement.status == status)

    if owner_id:
        query = query.filter(models.AuditEngagement.owner_id == owner_id)

    engagements = query.order_by(
        models.AuditEngagement.updated_at.desc()
    ).offset(skip).limit(limit).all()

    # Enrich each engagement
    for engagement in engagements:
        _enrich_engagement(db, engagement)

    return engagements


def get_audit_engagements_count(
    db: Session,
    organisation_id: uuid.UUID,
    status: Optional[str] = None,
    owner_id: Optional[uuid.UUID] = None
) -> int:
    """Get count of audit engagements for an organization"""
    query = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.organisation_id == organisation_id
    )

    if status:
        query = query.filter(models.AuditEngagement.status == status)

    if owner_id:
        query = query.filter(models.AuditEngagement.owner_id == owner_id)

    return query.count()


def create_audit_engagement(
    db: Session,
    name: str,
    assessment_id: uuid.UUID,
    owner_id: uuid.UUID,
    organisation_id: uuid.UUID,
    description: Optional[str] = None,
    audit_period_start: Optional[datetime] = None,
    audit_period_end: Optional[datetime] = None,
    planned_start_date: Optional[datetime] = None,
    planned_end_date: Optional[datetime] = None,
    in_scope_controls: Optional[List[str]] = None,
    in_scope_policies: Optional[List[str]] = None,
    in_scope_chapters: Optional[List[str]] = None,
    prior_engagement_id: Optional[uuid.UUID] = None
):
    """Create a new audit engagement"""
    engagement = models.AuditEngagement(
        name=name,
        description=description,
        assessment_id=assessment_id,
        audit_period_start=audit_period_start,
        audit_period_end=audit_period_end,
        status="draft",
        planned_start_date=planned_start_date,
        planned_end_date=planned_end_date,
        owner_id=owner_id,
        organisation_id=organisation_id,
        prior_engagement_id=prior_engagement_id
    )

    # Set scope arrays
    if in_scope_controls:
        engagement.in_scope_controls = in_scope_controls
    if in_scope_policies:
        engagement.in_scope_policies = in_scope_policies
    if in_scope_chapters:
        engagement.in_scope_chapters = in_scope_chapters

    db.add(engagement)
    db.commit()
    db.refresh(engagement)

    _enrich_engagement(db, engagement)

    return engagement


def update_audit_engagement(
    db: Session,
    engagement_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    audit_period_start: Optional[datetime] = None,
    audit_period_end: Optional[datetime] = None,
    planned_start_date: Optional[datetime] = None,
    planned_end_date: Optional[datetime] = None,
    actual_start_date: Optional[datetime] = None,
    actual_end_date: Optional[datetime] = None,
    in_scope_controls: Optional[List[str]] = None,
    in_scope_policies: Optional[List[str]] = None,
    in_scope_chapters: Optional[List[str]] = None,
    prior_engagement_id: Optional[uuid.UUID] = None
):
    """Update an existing audit engagement"""
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()

    if not engagement:
        return None

    # Update fields if provided
    if name is not None:
        engagement.name = name
    if description is not None:
        engagement.description = description
    if audit_period_start is not None:
        engagement.audit_period_start = audit_period_start
    if audit_period_end is not None:
        engagement.audit_period_end = audit_period_end
    if planned_start_date is not None:
        engagement.planned_start_date = planned_start_date
    if planned_end_date is not None:
        engagement.planned_end_date = planned_end_date
    if actual_start_date is not None:
        engagement.actual_start_date = actual_start_date
    if actual_end_date is not None:
        engagement.actual_end_date = actual_end_date
    if in_scope_controls is not None:
        engagement.in_scope_controls = in_scope_controls
    if in_scope_policies is not None:
        engagement.in_scope_policies = in_scope_policies
    if in_scope_chapters is not None:
        engagement.in_scope_chapters = in_scope_chapters
    if prior_engagement_id is not None:
        engagement.prior_engagement_id = prior_engagement_id

    db.commit()
    db.refresh(engagement)

    _enrich_engagement(db, engagement)

    return engagement


def update_audit_engagement_status(
    db: Session,
    engagement_id: uuid.UUID,
    new_status: str
):
    """Update the status of an audit engagement"""
    valid_statuses = ["draft", "planned", "in_progress", "review", "completed", "closed"]

    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()

    if not engagement:
        return None

    old_status = engagement.status
    engagement.status = new_status

    # Update actual dates based on status transitions
    if new_status == "in_progress" and old_status in ["draft", "planned"]:
        engagement.actual_start_date = datetime.utcnow()
    elif new_status in ["completed", "closed"] and old_status not in ["completed", "closed"]:
        engagement.actual_end_date = datetime.utcnow()

    db.commit()
    db.refresh(engagement)

    _enrich_engagement(db, engagement)

    return engagement


def delete_audit_engagement(db: Session, engagement_id: uuid.UUID) -> bool:
    """Delete an audit engagement"""
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()

    if not engagement:
        return False

    db.delete(engagement)
    db.commit()
    return True


def get_engagement_by_assessment(db: Session, assessment_id: uuid.UUID):
    """Get all engagements for a specific assessment"""
    engagements = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.assessment_id == assessment_id
    ).order_by(models.AuditEngagement.created_at.desc()).all()

    for engagement in engagements:
        _enrich_engagement(db, engagement)

    return engagements


def _enrich_engagement(db: Session, engagement):
    """Helper function to enrich engagement with related data"""
    # Get assessment name and framework info
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == engagement.assessment_id
    ).first()

    if assessment:
        engagement.assessment_name = assessment.name

        # Get framework info
        framework = db.query(models.Framework).filter(
            models.Framework.id == assessment.framework_id
        ).first()
        if framework:
            engagement.framework_name = framework.name
            engagement.framework_id = framework.id

    # Get owner info
    owner = db.query(models.User).filter(
        models.User.id == engagement.owner_id
    ).first()

    if owner:
        engagement.owner_name = owner.name
        engagement.owner_email = owner.email

    # Get organisation name
    organisation = db.query(models.Organisations).filter(
        models.Organisations.id == engagement.organisation_id
    ).first()

    if organisation:
        engagement.organisation_name = organisation.name

    # Count invitations
    invitation_count = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.engagement_id == engagement.id
    ).count()
    engagement.invitation_count = invitation_count

    # Count active invitations
    active_invitation_count = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.engagement_id == engagement.id,
        models.AuditorInvitation.status.in_(["pending", "accepted"])
    ).count()
    engagement.active_invitation_count = active_invitation_count


# ===========================
# Auditor Role Operations
# ===========================

def get_auditor_roles(db: Session):
    """Get all auditor roles"""
    return db.query(models.AuditorRole).all()


def get_auditor_role(db: Session, role_id: uuid.UUID):
    """Get a specific auditor role by ID"""
    return db.query(models.AuditorRole).filter(
        models.AuditorRole.id == role_id
    ).first()


def get_auditor_role_by_name(db: Session, role_name: str):
    """Get a specific auditor role by name"""
    return db.query(models.AuditorRole).filter(
        models.AuditorRole.role_name == role_name
    ).first()
