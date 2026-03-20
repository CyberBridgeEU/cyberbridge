from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

from app.database.database import get_db
from app.repositories import gap_analysis_repository
from app.services.auth_service import get_current_active_user
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gap-analysis", tags=["gap-analysis"])


@router.get("")
async def get_gap_analysis(
    framework_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get comprehensive gap analysis data for compliance reporting."""
    try:
        return gap_analysis_repository.get_gap_analysis(db, current_user, framework_id)
    except Exception as e:
        logger.error(f"Error fetching gap analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch gap analysis data")
