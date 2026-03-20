# routers/evidence_integrity_controller.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid
import os

from app.database.database import get_db
from app.services import evidence_integrity_service
from app.models import models
from app.dtos import schemas

router = APIRouter(prefix="/evidence", tags=["Evidence Integrity"])


@router.get("/{evidence_id}/integrity", response_model=schemas.EvidenceIntegrityResponse)
def get_evidence_integrity(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get integrity information for an evidence file"""
    # Verify evidence exists
    evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    integrity_info = evidence_integrity_service.get_integrity_info(db, evidence_id)
    if not integrity_info:
        raise HTTPException(status_code=404, detail="No integrity record found for this evidence")

    return integrity_info


@router.post("/{evidence_id}/integrity/verify", response_model=schemas.EvidenceIntegrityVerificationResponse)
def verify_evidence_integrity(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Verify that an evidence file's current state matches its stored hash"""
    # Verify evidence exists
    evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Get file path
    base_path = os.environ.get("UPLOAD_PATH", "/app/uploads")
    file_path = os.path.join(base_path, evidence.filepath)

    result = evidence_integrity_service.verify_file_integrity(db, evidence_id, file_path)
    return result


@router.get("/{evidence_id}/integrity/receipt")
def download_integrity_receipt(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Download a PDF integrity receipt for an evidence file"""
    # Verify evidence exists
    evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    receipt_pdf = evidence_integrity_service.generate_integrity_receipt(db, evidence_id)
    if not receipt_pdf:
        raise HTTPException(status_code=404, detail="Could not generate integrity receipt")

    filename = f"integrity_receipt_{evidence.filename}_{evidence_id}.pdf"

    return StreamingResponse(
        receipt_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{evidence_id}/versions", response_model=schemas.EvidenceVersionHistoryResponse)
def get_evidence_version_history(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get complete version history for an evidence file"""
    # Verify evidence exists
    evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    history = evidence_integrity_service.get_version_history(db, evidence_id)

    return {
        "versions": history,
        "current_version": history[0]['version'] if history else 0,
        "total_versions": len(history)
    }
