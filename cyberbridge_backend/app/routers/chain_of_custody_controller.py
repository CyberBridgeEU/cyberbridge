from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database.database import get_db
from app.models import models
from app.services import chain_of_custody_service
from app.services.auth_service import get_current_active_user
from app.dtos import schemas

router = APIRouter(prefix="/custody", tags=["Chain of Custody"])

VALID_REASONS = {"collection", "review", "audit", "authority", "release"}
VALID_STATUSES = {"collected", "in_review", "with_auditor", "with_authority", "released"}


class TransferRequest(BaseModel):
    reason: str                          # collection | review | audit | authority | release
    custody_status_after: str            # new status after this transfer
    to_user_id: Optional[uuid.UUID] = None
    to_auditor_id: Optional[uuid.UUID] = None
    to_label: str                        # display name of the recipient
    notes: Optional[str] = None


@router.post("/{evidence_id}/transfer")
def record_custody_transfer(
    evidence_id: uuid.UUID,
    body: TransferRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """
    Record a custody transfer for an evidence item.
    The caller becomes the 'from' party; specify the 'to' party in the body.
    """
    # Validate evidence exists and belongs to org
    evidence = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == evidence_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if current_user.role_name != "super_admin" and evidence.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if body.reason not in VALID_REASONS:
        raise HTTPException(status_code=400, detail=f"reason must be one of: {VALID_REASONS}")
    if body.custody_status_after not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"custody_status_after must be one of: {VALID_STATUSES}")

    ip_address = request.client.host if request.client else None

    transfer = chain_of_custody_service.record_transfer(
        db=db,
        evidence_id=evidence_id,
        reason=body.reason,
        custody_status_after=body.custody_status_after,
        from_user_id=current_user.id,
        from_label=current_user.name if hasattr(current_user, "name") else current_user.email,
        to_user_id=body.to_user_id,
        to_auditor_id=body.to_auditor_id,
        to_label=body.to_label,
        notes=body.notes,
        ip_address=ip_address,
    )

    return {
        "transfer_index": transfer.transfer_index,
        "id": str(transfer.id),
        "evidence_id": str(evidence_id),
        "from_label": transfer.from_label,
        "to_label": transfer.to_label,
        "reason": transfer.reason,
        "custody_status_after": transfer.custody_status_after,
        "transferred_at": transfer.transferred_at.isoformat(),
        "transfer_hash": transfer.transfer_hash,
    }


@router.get("/{evidence_id}/chain")
def get_custody_chain(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Return the full custody history for an evidence item, oldest first."""
    evidence = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == evidence_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if current_user.role_name != "super_admin" and evidence.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    chain = chain_of_custody_service.get_custody_chain(db, evidence_id)
    return {
        "evidence_id": str(evidence_id),
        "evidence_name": evidence.name,
        "current_custody_status": evidence.custody_status,
        "total_transfers": len(chain),
        "transfers": chain,
    }


@router.get("/{evidence_id}/current")
def get_current_holder(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Return who currently holds custody of an evidence item."""
    evidence = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == evidence_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if current_user.role_name != "super_admin" and evidence.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    holder = chain_of_custody_service.get_current_holder(db, evidence_id)
    if not holder:
        return {
            "evidence_id": str(evidence_id),
            "custody_status": evidence.custody_status or "collected",
            "holder": None,
            "detail": "No transfers recorded — evidence remains with original uploader.",
        }

    return {
        "evidence_id": str(evidence_id),
        "evidence_name": evidence.name,
        **holder,
    }


@router.get("/{evidence_id}/verify")
def verify_custody_chain(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """
    Verify the hash chain for all custody transfers of an evidence item.
    Returns valid=True only if every transfer is intact and correctly linked.
    """
    evidence = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == evidence_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if current_user.role_name != "super_admin" and evidence.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = chain_of_custody_service.verify_custody_chain(db, evidence_id)
    return {**result, "evidence_id": str(evidence_id), "evidence_name": evidence.name}
