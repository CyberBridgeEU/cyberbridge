# submission_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import json
from datetime import datetime
from app.models import models


# ---- Certificate Submissions ----

def create_submission(db: Session, data: dict) -> models.CertificateSubmission:
    sub = models.CertificateSubmission(**data)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def get_submissions_by_org(db: Session, org_id: uuid.UUID):
    """List all submissions for an org, with optional certificate + framework info."""
    return db.query(
        models.CertificateSubmission.id,
        models.CertificateSubmission.certificate_id,
        models.CertificateSubmission.framework_id,
        models.CertificateSubmission.authority_name,
        models.CertificateSubmission.recipient_emails,
        models.CertificateSubmission.attachment_types,
        models.CertificateSubmission.submission_method,
        models.CertificateSubmission.status,
        models.CertificateSubmission.subject,
        models.CertificateSubmission.body,
        models.CertificateSubmission.feedback,
        models.CertificateSubmission.feedback_received_at,
        models.CertificateSubmission.sent_at,
        models.CertificateSubmission.created_at,
        models.ComplianceCertificate.certificate_number,
        models.Framework.name.label("framework_name"),
        models.User.name.label("submitted_by_name"),
    ).outerjoin(
        models.ComplianceCertificate,
        models.CertificateSubmission.certificate_id == models.ComplianceCertificate.id
    ).outerjoin(
        models.Framework,
        func.coalesce(
            models.CertificateSubmission.framework_id,
            models.ComplianceCertificate.framework_id
        ) == models.Framework.id
    ).join(
        models.User,
        models.CertificateSubmission.submitted_by_user_id == models.User.id
    ).filter(
        models.CertificateSubmission.organisation_id == org_id
    ).order_by(models.CertificateSubmission.created_at.desc()).all()


def get_submission_by_id(db: Session, sub_id: uuid.UUID):
    return db.query(models.CertificateSubmission).filter(
        models.CertificateSubmission.id == sub_id
    ).first()


def update_submission_status(db: Session, sub_id: uuid.UUID, status: str, sent_at: datetime = None):
    sub = get_submission_by_id(db, sub_id)
    if not sub:
        return None
    sub.status = status
    if sent_at:
        sub.sent_at = sent_at
    db.commit()
    db.refresh(sub)
    return sub


def update_submission_feedback(db: Session, sub_id: uuid.UUID, feedback: str):
    sub = get_submission_by_id(db, sub_id)
    if not sub:
        return None
    sub.feedback = feedback
    sub.feedback_received_at = datetime.utcnow()
    sub.status = "feedback_received"
    db.commit()
    db.refresh(sub)
    return sub


# ---- Email Configs ----

def get_email_configs(db: Session, org_id: uuid.UUID):
    return db.query(models.SubmissionEmailConfig).filter(
        models.SubmissionEmailConfig.organisation_id == org_id
    ).order_by(models.SubmissionEmailConfig.authority_name, models.SubmissionEmailConfig.email).all()


def create_email_config(db: Session, org_id: uuid.UUID, authority_name: str, email: str, user_id: uuid.UUID = None, is_default: bool = False):
    config = models.SubmissionEmailConfig(
        organisation_id=org_id,
        authority_name=authority_name,
        email=email,
        is_default=is_default,
        created_by_user_id=user_id,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def delete_email_config(db: Session, config_id: uuid.UUID):
    config = db.query(models.SubmissionEmailConfig).filter(
        models.SubmissionEmailConfig.id == config_id
    ).first()
    if config and not config.is_default:
        db.delete(config)
        db.commit()
        return True
    return False


def seed_default_emails(db: Session, org_id: uuid.UUID):
    """Seed default regulatory authority emails if none exist for this org."""
    existing = db.query(models.SubmissionEmailConfig).filter(
        models.SubmissionEmailConfig.organisation_id == org_id,
        models.SubmissionEmailConfig.is_default == True
    ).count()
    if existing > 0:
        return

    defaults = [
        ("ENISA", "vulnerabilities@enisa.europa.eu"),
        ("ENISA CSIRT", "csirt-coordination@enisa.europa.eu"),
        ("EU-CERT", "cert-eu@ec.europa.eu"),
    ]
    for authority, email in defaults:
        create_email_config(db, org_id, authority, email, is_default=True)
