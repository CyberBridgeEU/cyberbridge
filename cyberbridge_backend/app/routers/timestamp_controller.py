from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.database.database import get_db
from app.models import models
from app.services import timestamp_authority_service, digital_signature_service

router = APIRouter(prefix="/timestamps", tags=["RFC 3161 Timestamps"])


def _get_token_or_404(db: Session, token_id) -> models.TimestampToken:
    token = db.query(models.TimestampToken).filter(
        models.TimestampToken.id == token_id
    ).first()
    if not token:
        raise HTTPException(status_code=404, detail="Timestamp token not found")
    return token


@router.get("/certificates/{cert_id}")
def get_certificate_timestamp(cert_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the trusted timestamp record for a compliance certificate."""
    cert = db.query(models.ComplianceCertificate).filter(
        models.ComplianceCertificate.id == cert_id
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not cert.timestamp_token_id:
        return {
            "has_timestamp": False,
            "detail": "No trusted timestamp has been issued for this certificate.",
            "certificate_number": cert.certificate_number,
        }

    token = _get_token_or_404(db, cert.timestamp_token_id)
    return {
        "has_timestamp": True,
        "certificate_number": cert.certificate_number,
        "tsa_url": token.tsa_url,
        "gen_time": token.gen_time.isoformat() if token.gen_time else None,
        "hash_algorithm": token.hash_algorithm,
        "payload_hash": token.payload_hash,
        "tsa_serial": token.tsa_serial,
        "status": token.status,
        "token_size_bytes": len(token.token_b64) * 3 // 4,  # approx decoded size
    }


@router.post("/certificates/{cert_id}/verify")
def verify_certificate_timestamp(cert_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Verify the RFC 3161 timestamp on a compliance certificate.
    Confirms the certificate data existed at the stated time and has not been
    modified since the TSA issued the token.
    """
    cert = db.query(models.ComplianceCertificate).filter(
        models.ComplianceCertificate.id == cert_id
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not cert.timestamp_token_id:
        return {
            "valid": False,
            "detail": "No timestamp token found for this certificate.",
            "certificate_number": cert.certificate_number,
        }

    token = _get_token_or_404(db, cert.timestamp_token_id)
    payload = digital_signature_service.certificate_payload(cert)
    result = timestamp_authority_service.verify_timestamp_token(token, payload)

    return {**result, "certificate_number": cert.certificate_number}


@router.get("/sign-offs/{sign_off_id}")
def get_sign_off_timestamp(sign_off_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the trusted timestamp record for an audit sign-off."""
    sign_off = db.query(models.AuditSignOff).filter(
        models.AuditSignOff.id == sign_off_id
    ).first()
    if not sign_off:
        raise HTTPException(status_code=404, detail="Sign-off not found")
    if not sign_off.timestamp_token_id:
        return {
            "has_timestamp": False,
            "detail": "No trusted timestamp for this sign-off.",
            "sign_off_id": str(sign_off_id),
        }

    token = _get_token_or_404(db, sign_off.timestamp_token_id)
    return {
        "has_timestamp": True,
        "sign_off_id": str(sign_off_id),
        "sign_off_type": sign_off.sign_off_type,
        "tsa_url": token.tsa_url,
        "gen_time": token.gen_time.isoformat() if token.gen_time else None,
        "hash_algorithm": token.hash_algorithm,
        "payload_hash": token.payload_hash,
        "tsa_serial": token.tsa_serial,
        "status": token.status,
    }


@router.post("/sign-offs/{sign_off_id}/verify")
def verify_sign_off_timestamp(sign_off_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Verify the RFC 3161 timestamp on an audit sign-off.
    """
    sign_off = db.query(models.AuditSignOff).filter(
        models.AuditSignOff.id == sign_off_id
    ).first()
    if not sign_off:
        raise HTTPException(status_code=404, detail="Sign-off not found")
    if not sign_off.timestamp_token_id:
        return {
            "valid": False,
            "detail": "No timestamp token found for this sign-off.",
        }

    token = _get_token_or_404(db, sign_off.timestamp_token_id)
    payload = digital_signature_service.sign_off_payload(sign_off)
    result = timestamp_authority_service.verify_timestamp_token(token, payload)

    return {**result, "sign_off_id": str(sign_off_id)}
