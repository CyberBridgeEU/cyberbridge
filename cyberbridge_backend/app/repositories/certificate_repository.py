# certificate_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from datetime import datetime, timedelta
from app.models import models


def create_certificate(db: Session, data: dict) -> models.ComplianceCertificate:
    cert = models.ComplianceCertificate(**data)
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


def get_certificates_by_org(db: Session, org_id: uuid.UUID, framework_id: uuid.UUID = None):
    """List certificates for an organisation (without pdf_data for performance)."""
    query = db.query(
        models.ComplianceCertificate.id,
        models.ComplianceCertificate.certificate_number,
        models.ComplianceCertificate.framework_id,
        models.ComplianceCertificate.organisation_id,
        models.ComplianceCertificate.overall_score,
        models.ComplianceCertificate.objectives_compliant_pct,
        models.ComplianceCertificate.assessments_completed_pct,
        models.ComplianceCertificate.policies_approved_pct,
        models.ComplianceCertificate.issued_at,
        models.ComplianceCertificate.expires_at,
        models.ComplianceCertificate.revoked,
        models.ComplianceCertificate.revoked_at,
        models.ComplianceCertificate.revoked_reason,
        models.ComplianceCertificate.verification_hash,
        models.Framework.name.label("framework_name"),
        models.Organisations.name.label("organisation_name"),
    ).join(
        models.Framework, models.ComplianceCertificate.framework_id == models.Framework.id
    ).join(
        models.Organisations, models.ComplianceCertificate.organisation_id == models.Organisations.id
    ).filter(
        models.ComplianceCertificate.organisation_id == org_id
    ).order_by(models.ComplianceCertificate.issued_at.desc())

    if framework_id:
        query = query.filter(models.ComplianceCertificate.framework_id == framework_id)

    return query.all()


def get_certificate_by_id(db: Session, cert_id: uuid.UUID) -> models.ComplianceCertificate:
    return db.query(models.ComplianceCertificate).filter(
        models.ComplianceCertificate.id == cert_id
    ).first()


def get_certificate_by_hash(db: Session, verification_hash: str):
    return db.query(
        models.ComplianceCertificate.certificate_number,
        models.ComplianceCertificate.framework_id,
        models.ComplianceCertificate.organisation_id,
        models.ComplianceCertificate.issued_at,
        models.ComplianceCertificate.expires_at,
        models.ComplianceCertificate.revoked,
        models.Framework.name.label("framework_name"),
        models.Organisations.name.label("organisation_name"),
    ).join(
        models.Framework, models.ComplianceCertificate.framework_id == models.Framework.id
    ).join(
        models.Organisations, models.ComplianceCertificate.organisation_id == models.Organisations.id
    ).filter(
        models.ComplianceCertificate.verification_hash == verification_hash
    ).first()


def generate_next_certificate_number(db: Session, abbreviation: str, year: int) -> str:
    """Generate sequential certificate number like CB-CRA-2026-001."""
    prefix = f"CB-{abbreviation}-{year}-"
    last = db.query(models.ComplianceCertificate).filter(
        models.ComplianceCertificate.certificate_number.like(f"{prefix}%")
    ).order_by(models.ComplianceCertificate.certificate_number.desc()).first()

    if last:
        last_seq = int(last.certificate_number.split("-")[-1])
        seq = last_seq + 1
    else:
        seq = 1

    return f"{prefix}{seq:03d}"


def revoke_certificate(db: Session, cert_id: uuid.UUID, reason: str):
    cert = db.query(models.ComplianceCertificate).filter(
        models.ComplianceCertificate.id == cert_id
    ).first()
    if not cert:
        return None
    cert.revoked = True
    cert.revoked_at = datetime.utcnow()
    cert.revoked_reason = reason
    db.commit()
    db.refresh(cert)
    return cert
