from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.database.database import get_db
from app.models import models
from app.services import audit_log_chain_service

router = APIRouter(prefix="/audit", tags=["Audit Log Chain"])


@router.get("/engagements/{engagement_id}/logs/verify-chain")
def verify_audit_log_chain(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Verify the tamper-evident hash chain for an engagement's activity logs.

    Returns whether the chain is intact, how many entries were checked,
    and — if broken — exactly which entry was tampered with.
    """
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    result = audit_log_chain_service.verify_chain(db, engagement_id)
    return result


@router.get("/engagements/{engagement_id}/logs/chain-info")
def get_chain_info(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Return a summary of the current chain state for an engagement:
    total chained entries, the latest chain_index, and the tip hash.
    """
    engagement = db.query(models.AuditEngagement).filter(
        models.AuditEngagement.id == engagement_id
    ).first()
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    next_index, tip_hash = audit_log_chain_service.get_chain_tip(db, engagement_id)
    total = next_index  # next_index == number of chained entries so far

    return {
        "engagement_id": str(engagement_id),
        "total_chained_entries": total,
        "latest_chain_index": total - 1 if total > 0 else None,
        "chain_tip_hash": tip_hash if total > 0 else None,
        "genesis_hash": audit_log_chain_service.CHAIN_GENESIS,
    }
