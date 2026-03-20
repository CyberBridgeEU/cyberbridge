from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid
import logging

from app.database.database import get_db
from app.repositories import chain_map_repository
from app.services.auth_service import get_current_active_user
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chain-map", tags=["chain-map"])


@router.get("/connections")
async def get_chain_map_connections(
    framework_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all chain map connection data in a single bulk query."""
    try:
        return chain_map_repository.get_chain_map_connections(db, current_user, framework_id)
    except Exception as e:
        logger.error(f"Error fetching chain map connections: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chain map connections")
