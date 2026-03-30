"""
Chain of Custody Service
-------------------------
Tracks every custody handoff for evidence items. Each transfer is
hash-chained so any insertion, deletion, or modification is detectable.

Chain hash input (pipe-delimited canonical string):
  transfer_index | evidence_id | from_user_id | from_auditor_id |
  to_user_id | to_auditor_id | reason | custody_status_after |
  ip_address | transferred_at | previous_transfer_hash

Valid custody_status values:
  collected       — just uploaded / collected from source
  in_review       — under internal review
  with_auditor    — handed to an external auditor
  with_authority  — submitted to a regulatory authority
  released        — returned / no longer held

Valid reason values:
  collection | review | audit | authority | release
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import models

CUSTODY_GENESIS = "0" * 64  # sentinel for the first transfer


# ── Hash helpers ──────────────────────────────────────────────────────────────

def _canonical(
    transfer_index: int,
    evidence_id,
    from_user_id,
    from_auditor_id,
    to_user_id,
    to_auditor_id,
    reason: str,
    custody_status_after: str,
    ip_address: Optional[str],
    transferred_at: datetime,
    previous_hash: str,
) -> str:
    parts = [
        str(transfer_index),
        str(evidence_id),
        str(from_user_id) if from_user_id else "",
        str(from_auditor_id) if from_auditor_id else "",
        str(to_user_id) if to_user_id else "",
        str(to_auditor_id) if to_auditor_id else "",
        reason,
        custody_status_after,
        ip_address or "",
        transferred_at.astimezone(timezone.utc).isoformat(),
        previous_hash,
    ]
    return "|".join(parts)


def _compute_hash(
    transfer_index: int,
    evidence_id,
    from_user_id,
    from_auditor_id,
    to_user_id,
    to_auditor_id,
    reason: str,
    custody_status_after: str,
    ip_address: Optional[str],
    transferred_at: datetime,
    previous_hash: str,
) -> str:
    canonical = _canonical(
        transfer_index, evidence_id, from_user_id, from_auditor_id,
        to_user_id, to_auditor_id, reason, custody_status_after,
        ip_address, transferred_at, previous_hash,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get_chain_tip(db: Session, evidence_id) -> tuple[int, str]:
    """Return (next_transfer_index, previous_transfer_hash) for a new entry."""
    last = (
        db.query(models.CustodyTransfer)
        .filter(models.CustodyTransfer.evidence_id == evidence_id)
        .order_by(models.CustodyTransfer.transfer_index.desc())
        .first()
    )
    if last is None:
        return 0, CUSTODY_GENESIS
    return last.transfer_index + 1, last.transfer_hash


# ── Public API ────────────────────────────────────────────────────────────────

def record_transfer(
    db: Session,
    evidence_id,
    reason: str,
    custody_status_after: str,
    from_user_id=None,
    from_auditor_id=None,
    from_label: Optional[str] = None,
    to_user_id=None,
    to_auditor_id=None,
    to_label: Optional[str] = None,
    notes: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> models.CustodyTransfer:
    """
    Record a custody handoff and update the evidence custody_status.
    The transfer is automatically hash-chained to the previous one.
    """
    # Verify evidence exists
    evidence = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == evidence_id
    ).first()
    if not evidence:
        raise ValueError(f"Evidence {evidence_id} not found")

    transfer_index, previous_hash = _get_chain_tip(db, evidence_id)
    transferred_at = datetime.now(timezone.utc)

    transfer_hash = _compute_hash(
        transfer_index, evidence_id,
        from_user_id, from_auditor_id,
        to_user_id, to_auditor_id,
        reason, custody_status_after,
        ip_address, transferred_at, previous_hash,
    )

    transfer = models.CustodyTransfer(
        evidence_id=evidence_id,
        from_user_id=from_user_id,
        from_auditor_id=from_auditor_id,
        from_label=from_label,
        to_user_id=to_user_id,
        to_auditor_id=to_auditor_id,
        to_label=to_label,
        reason=reason,
        notes=notes,
        custody_status_after=custody_status_after,
        ip_address=ip_address,
        transferred_at=transferred_at,
        transfer_index=transfer_index,
        previous_transfer_hash=previous_hash,
        transfer_hash=transfer_hash,
    )

    db.add(transfer)

    # Update evidence custody status
    evidence.custody_status = custody_status_after
    db.commit()
    db.refresh(transfer)
    return transfer


def get_custody_chain(db: Session, evidence_id) -> list[dict]:
    """Return full custody history for an evidence item, oldest first."""
    transfers = (
        db.query(models.CustodyTransfer)
        .filter(models.CustodyTransfer.evidence_id == evidence_id)
        .order_by(models.CustodyTransfer.transfer_index.asc())
        .all()
    )

    result = []
    for t in transfers:
        result.append({
            "transfer_index": t.transfer_index,
            "id": str(t.id),
            "from_label": t.from_label,
            "to_label": t.to_label,
            "reason": t.reason,
            "custody_status_after": t.custody_status_after,
            "notes": t.notes,
            "ip_address": t.ip_address,
            "transferred_at": t.transferred_at.isoformat(),
            "transfer_hash": t.transfer_hash,
            "previous_transfer_hash": t.previous_transfer_hash,
        })
    return result


def get_current_holder(db: Session, evidence_id) -> Optional[dict]:
    """Return the most recent transfer (current custody holder)."""
    last = (
        db.query(models.CustodyTransfer)
        .filter(models.CustodyTransfer.evidence_id == evidence_id)
        .order_by(models.CustodyTransfer.transfer_index.desc())
        .first()
    )
    if not last:
        return None
    return {
        "transfer_index": last.transfer_index,
        "holder_label": last.to_label,
        "to_user_id": str(last.to_user_id) if last.to_user_id else None,
        "to_auditor_id": str(last.to_auditor_id) if last.to_auditor_id else None,
        "custody_status": last.custody_status_after,
        "since": last.transferred_at.isoformat(),
        "reason": last.reason,
    }


def verify_custody_chain(db: Session, evidence_id) -> dict:
    """
    Verify the hash chain for all custody transfers of an evidence item.
    Returns valid=True only if every transfer is intact and correctly linked.
    """
    transfers = (
        db.query(models.CustodyTransfer)
        .filter(models.CustodyTransfer.evidence_id == evidence_id)
        .order_by(models.CustodyTransfer.transfer_index.asc())
        .all()
    )

    if not transfers:
        return {
            "valid": True,
            "total_transfers": 0,
            "broken_at_index": None,
            "broken_transfer_id": None,
            "detail": "No custody transfers found for this evidence item.",
        }

    expected_previous = CUSTODY_GENESIS

    for t in transfers:
        if t.previous_transfer_hash != expected_previous:
            return {
                "valid": False,
                "total_transfers": len(transfers),
                "broken_at_index": t.transfer_index,
                "broken_transfer_id": str(t.id),
                "detail": (
                    f"Chain broken at transfer #{t.transfer_index}: "
                    f"previous_hash mismatch."
                ),
            }

        recomputed = _compute_hash(
            t.transfer_index, t.evidence_id,
            t.from_user_id, t.from_auditor_id,
            t.to_user_id, t.to_auditor_id,
            t.reason, t.custody_status_after,
            t.ip_address, t.transferred_at, t.previous_transfer_hash,
        )

        if recomputed != t.transfer_hash:
            return {
                "valid": False,
                "total_transfers": len(transfers),
                "broken_at_index": t.transfer_index,
                "broken_transfer_id": str(t.id),
                "detail": (
                    f"Transfer #{t.transfer_index} has been tampered with: "
                    f"hash mismatch."
                ),
            }

        expected_previous = t.transfer_hash

    return {
        "valid": True,
        "total_transfers": len(transfers),
        "broken_at_index": None,
        "broken_transfer_id": None,
        "detail": f"Custody chain intact. {len(transfers)} transfer(s) verified.",
    }
