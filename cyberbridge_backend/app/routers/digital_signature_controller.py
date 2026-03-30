from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.database.database import get_db
from app.models import models
from app.services import digital_signature_service

router = APIRouter(prefix="/signatures", tags=["Digital Signatures"])


@router.get("/orgs/{org_id}/public-key")
def get_org_public_key(org_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Return the organisation's current RSA public key in PEM format.
    Anyone can use this to independently verify signatures.
    """
    org = db.query(models.Organisations).filter(models.Organisations.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    pem = digital_signature_service.get_public_key_pem(db, org_id)
    if not pem:
        # Key doesn't exist yet — generate it now so it's ready
        key_record = digital_signature_service.get_or_create_org_key(db, org_id)
        pem = key_record.public_key_pem

    return {
        "organisation_id": str(org_id),
        "public_key_pem": pem,
        "algorithm": "RSA-2048-PKCS1v15-SHA256",
    }


@router.post("/certificates/{cert_id}/verify")
def verify_certificate_signature(cert_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Verify the digital signature on a compliance certificate.
    Confirms the certificate has not been modified since it was issued.
    """
    cert = db.query(models.ComplianceCertificate).filter(
        models.ComplianceCertificate.id == cert_id
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if not cert.signature:
        return {
            "valid": False,
            "detail": "This certificate has no digital signature (issued before signing was enabled).",
            "certificate_number": cert.certificate_number,
        }

    payload = digital_signature_service.certificate_payload(cert)
    result = digital_signature_service.verify_signature(
        payload, cert.signature, cert.organisation_id, db
    )

    return {
        **result,
        "certificate_number": cert.certificate_number,
        "issued_at": cert.issued_at.isoformat(),
        "expires_at": cert.expires_at.isoformat(),
    }


@router.post("/sign-offs/{sign_off_id}/verify")
def verify_sign_off_signature(sign_off_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Verify the digital signature on an audit sign-off.
    Confirms the sign-off record has not been modified since it was created.
    """
    sign_off = db.query(models.AuditSignOff).filter(
        models.AuditSignOff.id == sign_off_id
    ).first()
    if not sign_off:
        raise HTTPException(status_code=404, detail="Sign-off not found")

    if not sign_off.signature:
        return {
            "valid": False,
            "detail": "This sign-off has no digital signature.",
            "sign_off_id": str(sign_off_id),
        }

    # Resolve org_id via engagement → assessment → framework
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == sign_off.engagement_id
    ).first()
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == engagement.assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    framework = db.query(models.Framework).filter(
        models.Framework.id == assessment.framework_id
    ).first()
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    payload = digital_signature_service.sign_off_payload(sign_off)
    result = digital_signature_service.verify_signature(
        payload, sign_off.signature, framework.organisation_id, db
    )

    return {
        **result,
        "sign_off_id": str(sign_off_id),
        "sign_off_type": sign_off.sign_off_type,
        "status": sign_off.status,
        "signed_at": sign_off.signed_at.isoformat(),
    }
