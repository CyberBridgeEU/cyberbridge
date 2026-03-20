# services/audit_dashboard_service.py
"""
Audit Dashboard Service - Provides statistics and metrics for audit engagements.
Includes:
- Engagement status summary
- Open comments count
- Findings by severity chart data
- Review progress tracking
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import models


def get_engagement_dashboard(
    db: Session,
    engagement_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard data for an engagement.
    """
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()

    if not engagement:
        return {"error": "Engagement not found"}

    return {
        "engagement_summary": get_engagement_summary(db, engagement),
        "findings_by_severity": get_findings_by_severity(db, engagement_id),
        "comments_summary": get_comments_summary(db, engagement_id),
        "review_progress": get_review_progress(db, engagement),
        "recent_activity": get_recent_activity(db, engagement_id),
        "sign_off_status": get_sign_off_status(db, engagement_id),
        "timeline": get_engagement_timeline(db, engagement)
    }


def get_engagement_summary(db: Session, engagement) -> Dict[str, Any]:
    """
    Get basic engagement summary.
    """
    # Get owner name
    owner_name = None
    if engagement.owner_id:
        owner = db.query(models.User).filter(models.User.id == engagement.owner_id).first()
        owner_name = owner.name if owner else None

    # Get framework name
    framework_name = None
    if engagement.assessment_id:
        assessment = db.query(models.Assessment).filter(
            models.Assessment.id == engagement.assessment_id
        ).first()
        if assessment and assessment.framework_id:
            framework = db.query(models.Framework).filter(
                models.Framework.id == assessment.framework_id
            ).first()
            framework_name = framework.name if framework else None

    # Count invitations
    invitations = db.query(models.AuditorInvitation).filter(
        models.AuditorInvitation.engagement_id == engagement.id
    ).all()

    active_auditors = len([i for i in invitations if i.status == 'accepted'])
    pending_invitations = len([i for i in invitations if i.status == 'pending'])

    return {
        "id": str(engagement.id),
        "name": engagement.name,
        "status": engagement.status,
        "owner_name": owner_name,
        "framework_name": framework_name,
        "audit_period": {
            "start": engagement.audit_period_start.isoformat() if engagement.audit_period_start else None,
            "end": engagement.audit_period_end.isoformat() if engagement.audit_period_end else None
        },
        "dates": {
            "planned_start": engagement.planned_start_date.isoformat() if engagement.planned_start_date else None,
            "actual_start": engagement.actual_start_date.isoformat() if engagement.actual_start_date else None,
            "planned_end": engagement.planned_end_date.isoformat() if engagement.planned_end_date else None,
            "actual_end": engagement.actual_end_date.isoformat() if engagement.actual_end_date else None
        },
        "active_auditors": active_auditors,
        "pending_invitations": pending_invitations
    }


def get_findings_by_severity(
    db: Session,
    engagement_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get findings grouped by severity for chart display.
    """
    findings = db.query(models.AuditFinding).filter(
        models.AuditFinding.engagement_id == engagement_id
    ).all()

    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    status_counts = {
        "draft": 0,
        "confirmed": 0,
        "remediation_in_progress": 0,
        "remediated": 0,
        "accepted": 0,
        "closed": 0
    }

    for finding in findings:
        if finding.severity in severity_counts:
            severity_counts[finding.severity] += 1
        if finding.status in status_counts:
            status_counts[finding.status] += 1

    return {
        "total": len(findings),
        "by_severity": severity_counts,
        "by_status": status_counts,
        "open_count": sum([
            status_counts["draft"],
            status_counts["confirmed"],
            status_counts["remediation_in_progress"]
        ]),
        "closed_count": sum([
            status_counts["remediated"],
            status_counts["accepted"],
            status_counts["closed"]
        ])
    }


def get_comments_summary(
    db: Session,
    engagement_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get comments summary with counts by type and status.
    """
    comments = db.query(models.AuditComment).filter(
        models.AuditComment.engagement_id == engagement_id
    ).all()

    type_counts = {
        "question": 0,
        "evidence_request": 0,
        "observation": 0,
        "potential_exception": 0
    }

    status_counts = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0
    }

    for comment in comments:
        if comment.comment_type in type_counts:
            type_counts[comment.comment_type] += 1
        if comment.status in status_counts:
            status_counts[comment.status] += 1

    # Calculate overdue (open or in_progress with past due_date)
    overdue = len([
        c for c in comments
        if c.due_date and c.due_date < datetime.utcnow() and c.status in ['open', 'in_progress']
    ])

    return {
        "total": len(comments),
        "by_type": type_counts,
        "by_status": status_counts,
        "open_count": status_counts["open"] + status_counts["in_progress"],
        "resolved_count": status_counts["resolved"] + status_counts["closed"],
        "overdue_count": overdue,
        "evidence_requests_pending": len([
            c for c in comments
            if c.comment_type == 'evidence_request' and c.status in ['open', 'in_progress']
        ])
    }


def get_review_progress(db: Session, engagement) -> Dict[str, Any]:
    """
    Calculate review progress based on controls/questions reviewed.
    """
    if not engagement.assessment_id:
        return {
            "total_controls": 0,
            "reviewed": 0,
            "pending": 0,
            "percentage": 0
        }

    # Get assessment answers
    answers = db.query(models.Answer).filter(
        models.Answer.assessment_id == engagement.assessment_id
    ).all()

    total = len(answers)

    # Count reviewed (has sign-off or comments resolved)
    reviewed = 0
    for answer in answers:
        # Check if there are resolved comments for this answer
        resolved_comments = db.query(models.AuditComment).filter(
            and_(
                models.AuditComment.engagement_id == engagement.id,
                models.AuditComment.target_type == 'answer',
                models.AuditComment.target_id == answer.id,
                models.AuditComment.status.in_(['resolved', 'closed'])
            )
        ).first()

        if resolved_comments:
            reviewed += 1

    # Also count sign-offs for controls
    control_sign_offs = db.query(models.AuditSignOff).filter(
        and_(
            models.AuditSignOff.engagement_id == engagement.id,
            models.AuditSignOff.sign_off_type == 'control'
        )
    ).count()

    # Use the higher of the two counts
    reviewed = max(reviewed, control_sign_offs)

    return {
        "total_controls": total,
        "reviewed": min(reviewed, total),
        "pending": max(0, total - reviewed),
        "percentage": round((min(reviewed, total) / total * 100), 1) if total > 0 else 0
    }


def get_recent_activity(
    db: Session,
    engagement_id: uuid.UUID,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get recent activity for the engagement.
    """
    logs = db.query(models.AuditActivityLog).filter(
        models.AuditActivityLog.engagement_id == engagement_id
    ).order_by(models.AuditActivityLog.created_at.desc()).limit(limit).all()

    activities = []
    for log in logs:
        # Get actor name
        actor_name = "System"
        if log.user_id:
            user = db.query(models.User).filter(models.User.id == log.user_id).first()
            actor_name = user.name if user else "Unknown User"
        elif log.auditor_id:
            invitation = db.query(models.AuditorInvitation).filter(
                models.AuditorInvitation.id == log.auditor_id
            ).first()
            actor_name = invitation.name if invitation else "Unknown Auditor"

        activities.append({
            "id": str(log.id),
            "action": log.action,
            "actor_name": actor_name,
            "target_type": log.target_type,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })

    return activities


def get_sign_off_status(
    db: Session,
    engagement_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get sign-off status summary.
    """
    sign_offs = db.query(models.AuditSignOff).filter(
        models.AuditSignOff.engagement_id == engagement_id
    ).all()

    by_type = {
        "control": 0,
        "section": 0,
        "engagement": 0
    }

    by_status = {
        "approved": 0,
        "approved_with_exceptions": 0,
        "rejected": 0
    }

    for so in sign_offs:
        if so.sign_off_type in by_type:
            by_type[so.sign_off_type] += 1
        if so.status in by_status:
            by_status[so.status] += 1

    # Check for final engagement sign-off
    final_sign_off = db.query(models.AuditSignOff).filter(
        and_(
            models.AuditSignOff.engagement_id == engagement_id,
            models.AuditSignOff.sign_off_type == 'engagement',
            models.AuditSignOff.status.in_(['approved', 'approved_with_exceptions'])
        )
    ).first()

    return {
        "total": len(sign_offs),
        "by_type": by_type,
        "by_status": by_status,
        "has_final_sign_off": final_sign_off is not None,
        "final_sign_off": {
            "status": final_sign_off.status,
            "signed_at": final_sign_off.signed_at.isoformat() if final_sign_off and final_sign_off.signed_at else None
        } if final_sign_off else None
    }


def get_engagement_timeline(db: Session, engagement) -> Dict[str, Any]:
    """
    Get engagement timeline with key milestones.
    """
    milestones = []

    # Created
    if engagement.created_at:
        milestones.append({
            "event": "Engagement Created",
            "date": engagement.created_at.isoformat(),
            "completed": True
        })

    # Planned start
    if engagement.planned_start_date:
        milestones.append({
            "event": "Planned Start",
            "date": engagement.planned_start_date.isoformat(),
            "completed": engagement.actual_start_date is not None
        })

    # Actual start
    if engagement.actual_start_date:
        milestones.append({
            "event": "Audit Started",
            "date": engagement.actual_start_date.isoformat(),
            "completed": True
        })

    # Status changes
    status_progress = {
        "draft": 0,
        "planned": 1,
        "in_progress": 2,
        "review": 3,
        "completed": 4,
        "closed": 5
    }

    current_stage = status_progress.get(engagement.status, 0)

    milestones.append({
        "event": "In Progress",
        "date": None,
        "completed": current_stage >= 2
    })

    milestones.append({
        "event": "Under Review",
        "date": None,
        "completed": current_stage >= 3
    })

    milestones.append({
        "event": "Completed",
        "date": engagement.actual_end_date.isoformat() if engagement.actual_end_date else None,
        "completed": current_stage >= 4
    })

    # Calculate days remaining or overdue
    days_info = None
    if engagement.planned_end_date:
        delta = engagement.planned_end_date - datetime.utcnow().date() if hasattr(engagement.planned_end_date, 'date') else engagement.planned_end_date - datetime.utcnow()
        if hasattr(delta, 'days'):
            days = delta.days
        else:
            days = delta
        days_info = {
            "days_remaining": max(0, days) if isinstance(days, int) else 0,
            "is_overdue": days < 0 if isinstance(days, int) else False
        }

    return {
        "milestones": milestones,
        "current_status": engagement.status,
        "days_info": days_info
    }


def get_organization_audit_summary(
    db: Session,
    organisation_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get audit summary for an entire organization.
    """
    engagements = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.organisation_id == organisation_id
    ).all()

    by_status = {}
    total_findings = 0
    total_open_comments = 0

    for eng in engagements:
        status = eng.status or "unknown"
        by_status[status] = by_status.get(status, 0) + 1

        # Count findings
        findings_count = db.query(models.AuditFinding).filter(
            models.AuditFinding.engagement_id == eng.id
        ).count()
        total_findings += findings_count

        # Count open comments
        open_comments = db.query(models.AuditComment).filter(
            and_(
                models.AuditComment.engagement_id == eng.id,
                models.AuditComment.status.in_(['open', 'in_progress'])
            )
        ).count()
        total_open_comments += open_comments

    return {
        "total_engagements": len(engagements),
        "by_status": by_status,
        "total_findings": total_findings,
        "total_open_comments": total_open_comments,
        "active_engagements": by_status.get("in_progress", 0) + by_status.get("review", 0)
    }
