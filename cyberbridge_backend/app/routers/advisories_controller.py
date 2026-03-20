# routers/advisories_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid
import logging

from ..repositories import advisories_repository, history_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advisories", tags=["security-advisories"], responses={404: {"description": "Not found"}})


@router.get("/statuses", response_model=List[schemas.AdvisoryStatusResponse])
def get_advisory_statuses(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    return advisories_repository.get_advisory_statuses(db)


@router.get("", response_model=List[schemas.SecurityAdvisoryResponse])
def get_all_advisories(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    return advisories_repository.get_advisories(db, current_user)


@router.get("/{advisory_id}", response_model=schemas.SecurityAdvisoryResponse)
def get_advisory(advisory_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    advisory = advisories_repository.get_advisory(db, uuid.UUID(advisory_id), current_user)
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    return advisory


@router.post("", response_model=schemas.SecurityAdvisoryResponse)
def create_advisory(data: schemas.SecurityAdvisoryCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        advisory = advisories_repository.create_advisory(db, data.model_dump(), current_user)

        history_repository.track_insert(
            db=db,
            table_name="security_advisories",
            record_id=str(advisory.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={"title": advisory.title, "advisory_code": advisory.advisory_code}
        )

        return advisory
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Advisory code already exists in your organization.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating advisory: {str(e)}")


@router.put("/{advisory_id}", response_model=schemas.SecurityAdvisoryResponse)
def update_advisory(advisory_id: str, data: schemas.SecurityAdvisoryUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = advisories_repository.update_advisory(db, uuid.UUID(advisory_id), data.model_dump(), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Advisory not found")
        return result
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Advisory code conflict.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating advisory: {str(e)}")


@router.delete("/{advisory_id}")
def delete_advisory(advisory_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = advisories_repository.delete_advisory(db, uuid.UUID(advisory_id), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Advisory not found")
        return {"message": "Advisory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting advisory: {str(e)}")
