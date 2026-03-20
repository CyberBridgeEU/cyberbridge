# routers/assets_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

from ..repositories import assets_repository, history_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..seeds.asset_types_seed import AssetTypesSeed
from ..models import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"], responses={404: {"description": "Not found"}})


# ===========================
# Shared Lookup Endpoints
# ===========================

@router.get("/economic-operators", response_model=List[schemas.EconomicOperatorResponse])
def get_all_economic_operators(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all economic operators"""
    try:
        operators = assets_repository.get_economic_operators(db, skip=skip, limit=limit)
        return operators
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching economic operators: {str(e)}"
        )


@router.get("/criticalities", response_model=List[schemas.CriticalityResponse])
def get_all_criticalities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all criticalities with options"""
    try:
        criticalities = assets_repository.get_criticalities(db, skip=skip, limit=limit)
        return criticalities
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching criticalities: {str(e)}"
        )


@router.get("/categories", response_model=List[schemas.AssetCategoryResponse])
def get_all_asset_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all asset categories (used for risk categorization)"""
    try:
        categories = assets_repository.get_asset_categories(db, skip=skip, limit=limit)
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching asset categories: {str(e)}"
        )


# ===========================
# Asset Type Endpoints
# ===========================

@router.get("/types", response_model=List[schemas.AssetTypeResponse])
def get_all_asset_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all asset types with computed counts for the current organization"""
    try:
        asset_types = assets_repository.get_asset_types(db, current_user, skip=skip, limit=limit)
        return asset_types
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching asset types: {str(e)}"
        )


@router.post("/types/seed-defaults")
def seed_default_asset_types(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Seed the default 21 asset types for the current user's organization (idempotent)"""
    try:
        if current_user.role_name not in ['super_admin', 'org_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins and org admins can seed default asset types"
            )

        organisation = db.query(models.Organisations).filter(
            models.Organisations.id == current_user.organisation_id
        ).first()
        if not organisation:
            raise HTTPException(status_code=404, detail="Organisation not found")

        # Count existing asset types before seeding
        existing_count = db.query(models.AssetTypes).filter(
            models.AssetTypes.organisation_id == organisation.id
        ).count()

        AssetTypesSeed.seed_for_organization(db, organisation)
        db.commit()

        total_defaults = len(AssetTypesSeed.DEFAULT_ASSET_TYPES)

        # Count how many were actually new
        final_count = db.query(models.AssetTypes).filter(
            models.AssetTypes.organisation_id == organisation.id
        ).count()
        seeded_count = final_count - existing_count

        if seeded_count == 0:
            return {"seeded_count": 0, "message": f"All {total_defaults} default asset types already exist"}

        return {"seeded_count": seeded_count, "message": f"Successfully imported {seeded_count} default asset types"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while seeding default asset types: {str(e)}"
        )


@router.get("/types/{asset_type_id}", response_model=schemas.AssetTypeResponse)
def get_asset_type(
    asset_type_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get a single asset type by ID"""
    try:
        asset_type = assets_repository.get_asset_type(db, uuid.UUID(asset_type_id), current_user)
        if not asset_type:
            raise HTTPException(status_code=404, detail="Asset type not found")
        return asset_type
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the asset type: {str(e)}"
        )


@router.post("/types", response_model=schemas.AssetTypeResponse)
def create_asset_type(
    asset_type: schemas.AssetTypeCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Create a new asset type"""
    try:
        new_asset_type = assets_repository.create_asset_type(db, asset_type.model_dump(), current_user)

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="asset_types",
            record_id=str(new_asset_type.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "name": new_asset_type.name,
                "icon_name": new_asset_type.icon_name,
                "description": new_asset_type.description,
                "default_confidentiality": new_asset_type.default_confidentiality,
                "default_integrity": new_asset_type.default_integrity,
                "default_availability": new_asset_type.default_availability,
                "default_asset_value": new_asset_type.default_asset_value
            }
        )

        return new_asset_type
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the asset type: {str(e)}"
        )


@router.put("/types/{asset_type_id}", response_model=schemas.AssetTypeResponse)
def update_asset_type(
    asset_type_id: str,
    asset_type: schemas.AssetTypeUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update an existing asset type"""
    try:
        # Get the old data first
        old_asset_type = assets_repository.get_asset_type(db, uuid.UUID(asset_type_id), current_user)
        if not old_asset_type:
            raise HTTPException(status_code=404, detail="Asset type not found")

        asset_type_data = asset_type.model_dump()

        # Track changes
        changes = {}
        for key, new_value in asset_type_data.items():
            old_value = getattr(old_asset_type, key, None)
            if old_value != new_value:
                changes[key] = {
                    "old": str(old_value) if old_value else None,
                    "new": str(new_value) if new_value else None
                }

        # Update the asset type
        updated_asset_type = assets_repository.update_asset_type(db, uuid.UUID(asset_type_id), asset_type_data, current_user)

        # Track the update in history
        if changes:
            history_repository.track_update(
                db=db,
                table_name="asset_types",
                record_id=asset_type_id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes=changes
            )

        return updated_asset_type
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the asset type: {str(e)}"
        )


@router.delete("/types/{asset_type_id}")
def delete_asset_type(
    asset_type_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete an asset type (only if no assets are linked)"""
    try:
        # Get the old data first
        old_asset_type = assets_repository.get_asset_type(db, uuid.UUID(asset_type_id), current_user)
        if not old_asset_type:
            raise HTTPException(status_code=404, detail="Asset type not found")

        # Track the deletion in history
        history_repository.track_delete(
            db=db,
            table_name="asset_types",
            record_id=asset_type_id,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={
                "name": old_asset_type.name,
                "icon_name": old_asset_type.icon_name,
                "description": old_asset_type.description,
                "default_confidentiality": old_asset_type.default_confidentiality,
                "default_integrity": old_asset_type.default_integrity,
                "default_availability": old_asset_type.default_availability,
                "default_asset_value": old_asset_type.default_asset_value
            }
        )

        # Delete the asset type
        assets_repository.delete_asset_type(db, uuid.UUID(asset_type_id), current_user)

        return {"message": "Asset type deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the asset type: {str(e)}"
        )


# ===========================
# Asset Status Endpoints
# ===========================

@router.get("/statuses", response_model=List[schemas.AssetStatusResponse])
def get_all_asset_statuses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all asset statuses"""
    try:
        statuses = assets_repository.get_asset_statuses(db, skip=skip, limit=limit)
        return statuses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching asset statuses: {str(e)}"
        )


# ===========================
# Asset Endpoints
# ===========================

@router.get("", response_model=List[schemas.AssetResponse])
def get_all_assets(
    asset_type_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all assets with optional filtering by asset type"""
    try:
        asset_type_uuid = uuid.UUID(asset_type_id) if asset_type_id else None
        assets = assets_repository.get_assets(db, current_user, asset_type_id=asset_type_uuid, skip=skip, limit=limit)
        return assets
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching assets: {str(e)}"
        )


@router.get("/{asset_id}", response_model=schemas.AssetResponse)
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get a single asset by ID"""
    try:
        asset = assets_repository.get_asset(db, uuid.UUID(asset_id), current_user)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the asset: {str(e)}"
        )


@router.post("", response_model=schemas.AssetResponse)
def create_asset(
    asset: schemas.AssetCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Create a new asset"""
    try:
        new_asset = assets_repository.create_asset(db, asset.model_dump(), current_user)

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="assets",
            record_id=str(new_asset.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "name": new_asset.name,
                "description": new_asset.description,
                "asset_type_id": str(new_asset.asset_type_id)
            }
        )

        return new_asset
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the asset: {str(e)}"
        )


@router.put("/{asset_id}", response_model=schemas.AssetResponse)
def update_asset(
    asset_id: str,
    asset: schemas.AssetUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Update an existing asset"""
    try:
        # Get the old data first
        old_asset = assets_repository.get_asset(db, uuid.UUID(asset_id), current_user)
        if not old_asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset_data = asset.model_dump()

        # Track changes
        changes = {}
        for key, new_value in asset_data.items():
            old_value = getattr(old_asset, key, None)
            # Convert UUID to string for comparison
            if isinstance(old_value, uuid.UUID):
                old_value = str(old_value)
            if old_value != new_value:
                changes[key] = {
                    "old": str(old_value) if old_value else None,
                    "new": str(new_value) if new_value else None
                }

        # Update the asset
        updated_asset = assets_repository.update_asset(db, uuid.UUID(asset_id), asset_data, current_user)

        # Track the update in history
        if changes:
            history_repository.track_update(
                db=db,
                table_name="assets",
                record_id=asset_id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes=changes
            )

        return updated_asset
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the asset: {str(e)}"
        )


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete an asset"""
    try:
        # Get the old data first
        old_asset = assets_repository.get_asset(db, uuid.UUID(asset_id), current_user)
        if not old_asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Track the deletion in history
        history_repository.track_delete(
            db=db,
            table_name="assets",
            record_id=asset_id,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={
                "name": old_asset.name,
                "description": old_asset.description,
                "asset_type_id": str(old_asset.asset_type_id)
            }
        )

        # Delete the asset
        assets_repository.delete_asset(db, uuid.UUID(asset_id), current_user)

        return {"message": "Asset deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the asset: {str(e)}"
        )


# ===========================
# Asset-Risk Connection Endpoints
# ===========================

@router.get("/{asset_id}/risks")
def get_risks_for_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all risks linked to an asset"""
    try:
        risks = assets_repository.get_risks_for_asset(db, uuid.UUID(asset_id), current_user)
        # Convert to dict format for response
        return [
            {
                "id": str(risk.id),
                "risk_code": risk.risk_code,
                "risk_category_name": risk.risk_category_name,
                "risk_category_description": risk.risk_category_description,
                "risk_severity": getattr(risk, "risk_severity", None),
                "risk_status": getattr(risk, "risk_status", None),
                "risk_potential_impact": risk.risk_potential_impact,
            }
            for risk in risks
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risks for asset: {str(e)}"
        )


@router.post("/{asset_id}/risks/{risk_id}")
def link_asset_to_risk(
    asset_id: str,
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Link an asset to a risk"""
    try:
        assets_repository.link_asset_to_risk(db, uuid.UUID(asset_id), uuid.UUID(risk_id), current_user)
        return {"detail": "Asset linked to risk successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while linking asset to risk: {str(e)}"
        )


@router.delete("/{asset_id}/risks/{risk_id}")
def unlink_asset_from_risk(
    asset_id: str,
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Unlink an asset from a risk"""
    try:
        result = assets_repository.unlink_asset_from_risk(db, uuid.UUID(asset_id), uuid.UUID(risk_id), current_user)
        if result:
            return {"detail": "Asset unlinked from risk successfully"}
        else:
            raise HTTPException(status_code=404, detail="Link not found")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while unlinking asset from risk: {str(e)}"
        )
