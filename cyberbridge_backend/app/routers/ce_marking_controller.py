# routers/ce_marking_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid
import logging

from ..repositories import ce_marking_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ce-marking", tags=["ce-marking"], responses={404: {"description": "Not found"}})


# ===========================
# Lookup Endpoints
# ===========================

@router.get("/product-types", response_model=List[schemas.CEProductTypeResponse])
def get_product_types(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    return ce_marking_repository.get_ce_product_types(db)


@router.get("/document-types", response_model=List[schemas.CEDocumentTypeResponse])
def get_document_types(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    return ce_marking_repository.get_ce_document_types(db)


# ===========================
# Checklist CRUD
# ===========================

@router.get("/checklists", response_model=List[schemas.CEChecklistResponse])
def get_all_checklists(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    return ce_marking_repository.get_checklists(db, current_user)


@router.get("/checklists/{checklist_id}", response_model=schemas.CEChecklistDetailResponse)
def get_checklist_detail(checklist_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    checklist = ce_marking_repository.get_checklist_detail(db, uuid.UUID(checklist_id), current_user)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return checklist


@router.get("/checklists/asset/{asset_id}", response_model=schemas.CEChecklistResponse)
def get_checklist_for_asset(asset_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    checklist = ce_marking_repository.get_checklist_for_asset(db, uuid.UUID(asset_id), current_user)
    if not checklist:
        raise HTTPException(status_code=404, detail="No checklist found for this asset")
    return checklist


@router.post("/checklists", response_model=schemas.CEChecklistResponse)
def create_checklist(data: schemas.CEChecklistCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return ce_marking_repository.create_checklist(db, data.model_dump(), current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A checklist already exists for this asset")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating checklist: {str(e)}")


@router.put("/checklists/{checklist_id}", response_model=schemas.CEChecklistResponse)
def update_checklist(checklist_id: str, data: schemas.CEChecklistUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = ce_marking_repository.update_checklist(db, uuid.UUID(checklist_id), data.model_dump(exclude_unset=True), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Checklist not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating checklist: {str(e)}")


@router.delete("/checklists/{checklist_id}")
def delete_checklist(checklist_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = ce_marking_repository.delete_checklist(db, uuid.UUID(checklist_id), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Checklist not found")
        return {"message": "Checklist deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting checklist: {str(e)}")


# ===========================
# Checklist Items
# ===========================

@router.put("/items/{item_id}", response_model=schemas.CEChecklistItemResponse)
def update_checklist_item(item_id: str, data: schemas.CEChecklistItemUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = ce_marking_repository.update_checklist_item(db, uuid.UUID(item_id), data.model_dump(exclude_unset=True), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Checklist item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")


@router.post("/checklists/{checklist_id}/items", response_model=schemas.CEChecklistItemResponse)
def add_custom_item(checklist_id: str, data: schemas.CEChecklistItemCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = ce_marking_repository.add_custom_checklist_item(db, uuid.UUID(checklist_id), data.model_dump(), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Checklist not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding custom item: {str(e)}")


@router.delete("/items/{item_id}")
def delete_custom_item(item_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = ce_marking_repository.delete_checklist_item(db, uuid.UUID(item_id), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Checklist item not found")
        return {"message": "Custom item deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


# ===========================
# Document Statuses
# ===========================

@router.put("/documents/{status_id}", response_model=schemas.CEDocumentStatusResponse)
def update_document_status(status_id: str, data: schemas.CEDocumentStatusUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = ce_marking_repository.update_document_status(db, uuid.UUID(status_id), data.model_dump(exclude_unset=True), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Document status not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document status: {str(e)}")
