"""
Audit Log Chain Service
-----------------------
Implements tamper-evident hash chaining for AuditActivityLog entries.

How it works:
  - Every new log entry gets a SHA256 hash computed over its content fields
    PLUS the hash of the previous entry in the same engagement's chain.
  - This creates a linked chain: changing any entry breaks every hash that
    follows it, making tampering immediately detectable.
  - chain_index tracks the sequential position (0, 1, 2, ...) per engagement.

Hash input (canonical string, pipe-delimited):
  chain_index | engagement_id | user_id | auditor_id | action |
  target_type | target_id | details | ip_address | created_at | previous_log_hash
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import models


# ── Sentinel value used as previous_log_hash for the very first entry ──────────
CHAIN_GENESIS = "0" * 64  # 64 zeros — a recognizable "no previous entry" marker


def _canonical_string(
    chain_index: int,
    engagement_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    auditor_id: Optional[uuid.UUID],
    action: str,
    target_type: Optional[str],
    target_id: Optional[uuid.UUID],
    details: Optional[str],   # raw JSON string (not parsed dict)
    ip_address: Optional[str],
    created_at: datetime,
    previous_log_hash: str,
) -> str:
    """Build a deterministic string representation of a log entry for hashing."""
    parts = [
        str(chain_index),
        str(engagement_id),
        str(user_id) if user_id else "",
        str(auditor_id) if auditor_id else "",
        action,
        target_type or "",
        str(target_id) if target_id else "",
        details or "",
        ip_address or "",
        created_at.astimezone(timezone.utc).isoformat(),
        previous_log_hash,
    ]
    return "|".join(parts)


def compute_log_hash(
    chain_index: int,
    engagement_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    auditor_id: Optional[uuid.UUID],
    action: str,
    target_type: Optional[str],
    target_id: Optional[uuid.UUID],
    details: Optional[str],
    ip_address: Optional[str],
    created_at: datetime,
    previous_log_hash: str,
) -> str:
    """Return the SHA256 hex digest for a log entry."""
    canonical = _canonical_string(
        chain_index, engagement_id, user_id, auditor_id,
        action, target_type, target_id, details,
        ip_address, created_at, previous_log_hash,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_chain_tip(db: Session, engagement_id: uuid.UUID) -> tuple[int, str]:
    """
    Return (next_chain_index, previous_log_hash) for a new entry.
    If no entries exist yet, returns (0, CHAIN_GENESIS).
    """
    last = (
        db.query(models.AuditActivityLog)
        .filter(
            models.AuditActivityLog.engagement_id == engagement_id,
            models.AuditActivityLog.log_hash.isnot(None),
        )
        .order_by(models.AuditActivityLog.chain_index.desc())
        .first()
    )

    if last is None:
        return 0, CHAIN_GENESIS

    return (last.chain_index + 1), last.log_hash


def verify_chain(db: Session, engagement_id: uuid.UUID) -> dict:
    """
    Verify the complete chain for an engagement.

    Returns a dict with:
      - valid (bool): True if every entry is intact and correctly linked
      - total_entries (int): number of chained entries checked
      - broken_at_index (int | None): chain_index of the first broken link, or None
      - broken_entry_id (str | None): UUID of the broken entry, or None
      - detail (str): human-readable summary
    """
    entries = (
        db.query(models.AuditActivityLog)
        .filter(
            models.AuditActivityLog.engagement_id == engagement_id,
            models.AuditActivityLog.log_hash.isnot(None),
        )
        .order_by(models.AuditActivityLog.chain_index.asc())
        .all()
    )

    if not entries:
        return {
            "valid": True,
            "total_entries": 0,
            "broken_at_index": None,
            "broken_entry_id": None,
            "detail": "No chained log entries found for this engagement.",
        }

    expected_previous = CHAIN_GENESIS

    for entry in entries:
        # 1. Check the stored previous_log_hash links correctly
        if entry.previous_log_hash != expected_previous:
            return {
                "valid": False,
                "total_entries": len(entries),
                "broken_at_index": entry.chain_index,
                "broken_entry_id": str(entry.id),
                "detail": (
                    f"Chain broken at index {entry.chain_index}: "
                    f"expected previous_hash={expected_previous[:16]}… "
                    f"but found {entry.previous_log_hash[:16] if entry.previous_log_hash else 'None'}…"
                ),
            }

        # 2. Recompute the hash and compare with stored value
        recomputed = compute_log_hash(
            chain_index=entry.chain_index,
            engagement_id=entry.engagement_id,
            user_id=entry.user_id,
            auditor_id=entry.auditor_id,
            action=entry.action,
            target_type=entry.target_type,
            target_id=entry.target_id,
            details=entry._details,  # raw JSON string
            ip_address=entry.ip_address,
            created_at=entry.created_at,
            previous_log_hash=entry.previous_log_hash,
        )

        if recomputed != entry.log_hash:
            return {
                "valid": False,
                "total_entries": len(entries),
                "broken_at_index": entry.chain_index,
                "broken_entry_id": str(entry.id),
                "detail": (
                    f"Entry at index {entry.chain_index} has been tampered with: "
                    f"stored hash={entry.log_hash[:16]}… "
                    f"but recomputed hash={recomputed[:16]}…"
                ),
            }

        expected_previous = entry.log_hash

    return {
        "valid": True,
        "total_entries": len(entries),
        "broken_at_index": None,
        "broken_entry_id": None,
        "detail": f"Chain intact. {len(entries)} entries verified successfully.",
    }
