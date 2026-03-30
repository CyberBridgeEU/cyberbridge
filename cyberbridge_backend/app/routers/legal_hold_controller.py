from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.database.database import get_db
from app.models import models
from app.services import legal_hold_service
from app.services.auth_service import get_current_active_user
from app.dtos import schemas

router = APIRouter(prefix="/legal-holds", tags=["Legal Holds"])


class ApplyHoldRequest(BaseModel):
    reason: str                             # litigation | regulatory_inquiry | investigation | audit_freeze | other
    case_reference: Optional[str] = None    # external ticket / case number
    expires_at: Optional[datetime] = None   # None = indefinite


class LiftHoldRequest(BaseModel):
    lift_reason: Optional[str] = None


def _check_org(current_user, organisation_id):
    if current_user.role_name != "super_admin" and current_user.organisation_id != organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized")


# ── Evidence holds ────────────────────────────────────────────────────────────

@router.post("/evidence/{evidence_id}")
def apply_hold_to_evidence(
    evidence_id: uuid.UUID,
    body: ApplyHoldRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Apply a legal hold to an evidence item. Blocks deletion until lifted."""
    if body.reason not in legal_hold_service.VALID_REASONS:
        raise HTTPException(status_code=400, detail=f"reason must be one of: {legal_hold_service.VALID_REASONS}")

    evidence = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == evidence_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    _check_org(current_user, evidence.organisation_id)

    hold = legal_hold_service.apply_hold(
        db=db,
        target_type="evidence",
        target_id=evidence_id,
        organisation_id=evidence.organisation_id,
        applied_by_user_id=current_user.id,
        reason=body.reason,
        case_reference=body.case_reference,
        expires_at=body.expires_at,
    )

    return {
        "hold_id": str(hold.id),
        "target_type": "evidence",
        "target_id": str(evidence_id),
        "evidence_name": evidence.name,
        "reason": hold.reason,
        "case_reference": hold.case_reference,
        "applied_at": hold.applied_at.isoformat(),
        "expires_at": hold.expires_at.isoformat() if hold.expires_at else None,
        "status": hold.status,
        "detail": "Legal hold applied. This evidence item cannot be deleted until the hold is lifted.",
    }


@router.get("/evidence/{evidence_id}")
def get_evidence_holds(
    evidence_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Return all holds (active and historical) for an evidence item."""
    evidence = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == evidence_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    _check_org(current_user, evidence.organisation_id)

    active = legal_hold_service.get_active_hold(db, "evidence", evidence_id)
    history = legal_hold_service.get_hold_history(db, "evidence", evidence_id)

    return {
        "evidence_id": str(evidence_id),
        "evidence_name": evidence.name,
        "is_under_hold": active is not None,
        "active_hold_id": str(active.id) if active else None,
        "total_holds": len(history),
        "holds": history,
    }


# ── Engagement holds ──────────────────────────────────────────────────────────

@router.post("/engagements/{engagement_id}")
def apply_hold_to_engagement(
    engagement_id: uuid.UUID,
    body: ApplyHoldRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Apply a legal hold to an audit engagement."""
    if body.reason not in legal_hold_service.VALID_REASONS:
        raise HTTPException(status_code=400, detail=f"reason must be one of: {legal_hold_service.VALID_REASONS}")

    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    # Resolve org_id via assessment → framework
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == engagement.assessment_id
    ).first()
    framework = db.query(models.Framework).filter(
        models.Framework.id == assessment.framework_id
    ).first() if assessment else None
    org_id = framework.organisation_id if framework else current_user.organisation_id
    _check_org(current_user, org_id)

    hold = legal_hold_service.apply_hold(
        db=db,
        target_type="engagement",
        target_id=engagement_id,
        organisation_id=org_id,
        applied_by_user_id=current_user.id,
        reason=body.reason,
        case_reference=body.case_reference,
        expires_at=body.expires_at,
    )

    return {
        "hold_id": str(hold.id),
        "target_type": "engagement",
        "target_id": str(engagement_id),
        "engagement_name": engagement.name,
        "reason": hold.reason,
        "case_reference": hold.case_reference,
        "applied_at": hold.applied_at.isoformat(),
        "expires_at": hold.expires_at.isoformat() if hold.expires_at else None,
        "status": hold.status,
        "detail": "Legal hold applied to engagement.",
    }


@router.get("/engagements/{engagement_id}")
def get_engagement_holds(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Return all holds for an audit engagement."""
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    active = legal_hold_service.get_active_hold(db, "engagement", engagement_id)
    history = legal_hold_service.get_hold_history(db, "engagement", engagement_id)

    return {
        "engagement_id": str(engagement_id),
        "engagement_name": engagement.name,
        "is_under_hold": active is not None,
        "active_hold_id": str(active.id) if active else None,
        "total_holds": len(history),
        "holds": history,
    }


# ── Lift a hold ───────────────────────────────────────────────────────────────

@router.delete("/{hold_id}")
def lift_hold(
    hold_id: uuid.UUID,
    body: LiftHoldRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Lift an active legal hold. The target can be deleted again after this."""
    hold = db.query(models.LegalHold).filter(models.LegalHold.id == hold_id).first()
    if not hold:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    _check_org(current_user, hold.organisation_id)

    try:
        updated = legal_hold_service.lift_hold(
            db=db,
            hold_id=hold_id,
            lifted_by_user_id=current_user.id,
            lift_reason=body.lift_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "hold_id": str(updated.id),
        "status": updated.status,
        "lifted_at": updated.lifted_at.isoformat(),
        "lift_reason": updated.lift_reason,
        "detail": "Legal hold lifted. The target can now be deleted.",
    }
