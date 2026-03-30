"""
Legal Hold Service
-------------------
Prevents deletion or modification of evidence items and audit engagements
when a legal hold is active.

How it works:
  - Any authorised user can apply a legal hold to an evidence item or
    audit engagement, providing a reason and an optional case reference.
  - While a hold is active, the system refuses any delete operation on
    the target (HTTP 423 Locked).
  - A hold can be explicitly lifted by an authorised user. Full history
    is preserved — holds are never deleted, only transitioned to 'lifted'.
  - Holds can optionally carry an expiry date; expired holds are treated
    as inactive for delete-guard purposes.

Valid reason values:
  litigation | regulatory_inquiry | investigation | audit_freeze | other

Valid target_type values:
  evidence | engagement
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import models

VALID_REASONS = {"litigation", "regulatory_inquiry", "investigation", "audit_freeze", "other"}
VALID_TARGET_TYPES = {"evidence", "engagement"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Core operations ───────────────────────────────────────────────────────────

def apply_hold(
    db: Session,
    target_type: str,
    target_id,
    organisation_id,
    applied_by_user_id,
    reason: str,
    case_reference: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> models.LegalHold:
    """Apply a legal hold to a target. Multiple active holds per target are allowed."""
    hold = models.LegalHold(
        target_type=target_type,
        target_id=target_id,
        organisation_id=organisation_id,
        reason=reason,
        case_reference=case_reference,
        applied_by_user_id=applied_by_user_id,
        applied_at=_now(),
        expires_at=expires_at,
        status="active",
    )
    db.add(hold)
    db.commit()
    db.refresh(hold)
    return hold


def lift_hold(
    db: Session,
    hold_id,
    lifted_by_user_id,
    lift_reason: Optional[str] = None,
) -> models.LegalHold:
    """Lift an active legal hold. Raises ValueError if hold is not active."""
    hold = db.query(models.LegalHold).filter(models.LegalHold.id == hold_id).first()
    if not hold:
        raise ValueError(f"Legal hold {hold_id} not found")
    if hold.status != "active":
        raise ValueError(f"Legal hold {hold_id} is already {hold.status}")

    hold.status = "lifted"
    hold.lifted_at = _now()
    hold.lifted_by_user_id = lifted_by_user_id
    hold.lift_reason = lift_reason
    db.commit()
    db.refresh(hold)
    return hold


def get_active_hold(
    db: Session,
    target_type: str,
    target_id,
) -> Optional[models.LegalHold]:
    """
    Return the first active (non-expired) hold for a target, or None.
    This is what the delete guard calls.
    """
    now = _now()
    return (
        db.query(models.LegalHold)
        .filter(
            models.LegalHold.target_type == target_type,
            models.LegalHold.target_id == target_id,
            models.LegalHold.status == "active",
            # Either no expiry, or expiry is in the future
            (models.LegalHold.expires_at == None) | (models.LegalHold.expires_at > now),
        )
        .first()
    )


def is_under_hold(db: Session, target_type: str, target_id) -> bool:
    """Quick boolean check — True if any active non-expired hold exists."""
    return get_active_hold(db, target_type, target_id) is not None


def get_hold_history(db: Session, target_type: str, target_id) -> list[dict]:
    """Return all holds for a target (active, lifted, expired) newest first."""
    holds = (
        db.query(models.LegalHold)
        .filter(
            models.LegalHold.target_type == target_type,
            models.LegalHold.target_id == target_id,
        )
        .order_by(models.LegalHold.applied_at.desc())
        .all()
    )

    result = []
    for h in holds:
        # Auto-mark expired holds for display (don't write to DB here)
        display_status = h.status
        if h.status == "active" and h.expires_at and h.expires_at < _now():
            display_status = "expired"

        result.append({
            "id": str(h.id),
            "reason": h.reason,
            "case_reference": h.case_reference,
            "applied_by_user_id": str(h.applied_by_user_id),
            "applied_at": h.applied_at.isoformat(),
            "expires_at": h.expires_at.isoformat() if h.expires_at else None,
            "status": display_status,
            "lifted_at": h.lifted_at.isoformat() if h.lifted_at else None,
            "lifted_by_user_id": str(h.lifted_by_user_id) if h.lifted_by_user_id else None,
            "lift_reason": h.lift_reason,
        })
    return result


def expire_stale_holds(db: Session) -> int:
    """
    Mark all holds whose expires_at has passed as 'expired'.
    Returns the number of holds updated. Safe to call on a schedule.
    """
    now = _now()
    expired = (
        db.query(models.LegalHold)
        .filter(
            models.LegalHold.status == "active",
            models.LegalHold.expires_at != None,
            models.LegalHold.expires_at <= now,
        )
        .all()
    )
    for h in expired:
        h.status = "expired"
    if expired:
        db.commit()
    return len(expired)
