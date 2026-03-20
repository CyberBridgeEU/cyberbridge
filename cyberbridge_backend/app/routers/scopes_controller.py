# app/routers/scopes_controller.py
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services import scope_validation_service
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/scopes",
    tags=["scopes"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=List[schemas.ScopeTypeResponse])
def get_scope_types(db: Session = Depends(get_db)):
    """Get all available scope types"""
    supported_types = scope_validation_service.get_supported_scope_types()

    # Get scope IDs from database
    from app.models import models
    scopes = db.query(models.Scopes).all()
    scope_map = {scope.scope_name: scope for scope in scopes}

    result = []
    for scope_type in supported_types:
        if scope_type in scope_map:
            result.append({
                "id": str(scope_map[scope_type].id),
                "scope_name": scope_type,
                "created_at": scope_map[scope_type].created_at
            })

    return result
