# enisa_repository.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import logging
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


def _compute_reporting_status(notification):
    """Compute overall reporting status from individual phases."""
    submitted = []
    if notification.early_warning_required:
        submitted.append(notification.early_warning_submitted)
    if notification.vuln_notification_required:
        submitted.append(notification.vuln_notification_submitted)
    if notification.final_report_required:
        submitted.append(notification.final_report_submitted)

    if not submitted:
        return "not_started"

    all_submitted = all(submitted)
    any_submitted = any(submitted)

    if all_submitted:
        return "complete"

    # Check if any deadlines are overdue
    now = datetime.utcnow()
    overdue = False
    if notification.early_warning_required and not notification.early_warning_submitted:
        if notification.early_warning_deadline and now > notification.early_warning_deadline:
            overdue = True
    if notification.vuln_notification_required and not notification.vuln_notification_submitted:
        if notification.vuln_notification_deadline and now > notification.vuln_notification_deadline:
            overdue = True
    if notification.final_report_required and not notification.final_report_submitted:
        if notification.final_report_deadline and now > notification.final_report_deadline:
            overdue = True

    if overdue:
        return "overdue"
    if any_submitted:
        return "partially_complete"
    return "in_progress"


def get_enisa_notification(db: Session, incident_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.ENISANotifications).filter(
            models.ENISANotifications.incident_id == incident_id
        )
        notification = query.first()
        if notification:
            notification.reporting_status = _compute_reporting_status(notification)
        return notification
    except Exception as e:
        logger.error(f"Error getting ENISA notification for incident {incident_id}: {str(e)}")
        return None


def create_enisa_notification(db: Session, incident_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        organisation_id = current_user.organisation_id if current_user else None

        # Get incident discovered_at for deadline calculation
        incident = db.query(models.Incidents).filter(models.Incidents.id == incident_id).first()
        if not incident:
            raise ValueError("Incident not found")

        base_time = incident.discovered_at or incident.created_at

        notification = models.ENISANotifications(
            incident_id=incident_id,
            early_warning_deadline=base_time + timedelta(hours=24),
            vuln_notification_deadline=base_time + timedelta(hours=72),
            final_report_deadline=base_time + timedelta(days=14),
            early_warning_content=data.get("early_warning_content"),
            vuln_notification_content=data.get("vuln_notification_content"),
            final_report_content=data.get("final_report_content"),
            reporting_status="in_progress",
            organisation_id=organisation_id,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        notification.reporting_status = _compute_reporting_status(notification)
        return notification
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ENISA notification: {str(e)}")
        raise


def update_enisa_notification(db: Session, notification_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        notification = db.query(models.ENISANotifications).filter(
            models.ENISANotifications.id == notification_id
        ).first()
        if not notification:
            return None

        now = datetime.utcnow()

        # Update early warning
        if data.get("early_warning_submitted") is not None:
            notification.early_warning_submitted = data["early_warning_submitted"]
            if data["early_warning_submitted"]:
                notification.early_warning_submitted_at = now
        if data.get("early_warning_content") is not None:
            notification.early_warning_content = data["early_warning_content"]

        # Update vulnerability notification
        if data.get("vuln_notification_submitted") is not None:
            notification.vuln_notification_submitted = data["vuln_notification_submitted"]
            if data["vuln_notification_submitted"]:
                notification.vuln_notification_submitted_at = now
        if data.get("vuln_notification_content") is not None:
            notification.vuln_notification_content = data["vuln_notification_content"]

        # Update final report
        if data.get("final_report_submitted") is not None:
            notification.final_report_submitted = data["final_report_submitted"]
            if data["final_report_submitted"]:
                notification.final_report_submitted_at = now
        if data.get("final_report_content") is not None:
            notification.final_report_content = data["final_report_content"]

        notification.last_updated_by = current_user.id if current_user else None

        # Recompute status
        notification.reporting_status = _compute_reporting_status(notification)

        db.commit()
        db.refresh(notification)
        return notification
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating ENISA notification {notification_id}: {str(e)}")
        raise
