# certificate_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging
from io import BytesIO

from app.database.database import get_db
from app.repositories import certificate_repository
from app.services import certificate_service
from app.services.auth_service import get_current_active_user, check_user_role
from app.dtos import schemas
from app.models import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.post("/generate")
async def generate_certificate(
    request: schemas.CertificateGenerateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Generate a compliance certificate for a framework with 100% score."""
    try:
        cert = certificate_service.generate_certificate(db, current_user, request.framework_id)
        # Return the PDF directly
        pdf_bytes = cert.pdf_data
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="PDF generation failed")
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{cert.certificate_number}.pdf"'}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating certificate: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate certificate")


@router.get("")
async def list_certificates(
    framework_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """List certificates for the current user's organisation."""
    try:
        rows = certificate_repository.get_certificates_by_org(
            db, current_user.organisation_id, framework_id
        )
        return [
            schemas.CertificateResponse(
                id=r.id,
                certificate_number=r.certificate_number,
                framework_name=r.framework_name,
                organisation_name=r.organisation_name,
                overall_score=r.overall_score,
                objectives_compliant_pct=r.objectives_compliant_pct,
                assessments_completed_pct=r.assessments_completed_pct,
                policies_approved_pct=r.policies_approved_pct,
                issued_at=r.issued_at,
                expires_at=r.expires_at,
                revoked=r.revoked,
                revoked_at=r.revoked_at,
                revoked_reason=r.revoked_reason,
                verification_hash=r.verification_hash,
            )
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Error listing certificates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list certificates")


@router.get("/verify/{verification_hash}")
async def verify_certificate(
    verification_hash: str,
    db: Session = Depends(get_db),
):
    """Public endpoint to verify a certificate by its hash."""
    row = certificate_repository.get_certificate_by_hash(db, verification_hash)
    if not row:
        raise HTTPException(status_code=404, detail="Certificate not found")

    from datetime import datetime
    is_valid = not row.revoked and row.expires_at > datetime.utcnow()
    return schemas.CertificateVerifyResponse(
        certificate_number=row.certificate_number,
        organisation_name=row.organisation_name,
        framework_name=row.framework_name,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        is_valid=is_valid,
    )


@router.get("/{cert_id}/download")
async def download_certificate(
    cert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Download a certificate PDF."""
    cert = certificate_repository.get_certificate_by_id(db, cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.organisation_id != current_user.organisation_id and current_user.role_name != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if not cert.pdf_data:
        raise HTTPException(status_code=404, detail="PDF not available")

    return StreamingResponse(
        BytesIO(cert.pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{cert.certificate_number}.pdf"'}
    )


@router.post("/{cert_id}/revoke")
async def revoke_certificate(
    cert_id: uuid.UUID,
    request: schemas.CertificateRevokeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(check_user_role(["org_admin", "super_admin"]))
):
    """Revoke a certificate."""
    cert = certificate_repository.get_certificate_by_id(db, cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.organisation_id != current_user.organisation_id and current_user.role_name != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if cert.revoked:
        raise HTTPException(status_code=400, detail="Certificate is already revoked")

    revoked = certificate_repository.revoke_certificate(db, cert_id, request.reason)
    return {"message": "Certificate revoked", "certificate_number": revoked.certificate_number}
