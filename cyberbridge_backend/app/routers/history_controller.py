# routers/history_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid

from ..database.database import get_db
from ..services.auth_service import get_current_active_user, check_user_role
from ..repositories import history_repository
from ..dtos import schemas

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/")
def get_history(
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    action: Optional[str] = Query(None, description="Filter by action (insert, update, delete)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get history entries with optional filters"""
    try:
        # Only super_admin and org_admin can view history
        if current_user.role_name not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view history"
            )

        # For org_admin, filter by their organization
        # For super_admin, show all organizations
        organisation_filter = None if current_user.role_name == "super_admin" else current_user.organisation_id

        history_entries = history_repository.get_history(
            db=db,
            organisation_id=organisation_filter,
            table_name=table_name,
            action=action,
            limit=limit,
            offset=offset
        )

        # Format the response
        result = []
        for entry in history_entries:
            result.append({
                "id": str(entry.id),
                "table_name_changed": entry.table_name_changed,
                "record_id": entry.record_id,
                "initial_user_email": entry.initial_user_email,
                "last_user_email": entry.last_user_email,
                "last_timestamp": entry.last_timestamp.isoformat() if entry.last_timestamp else None,
                "column_name": entry.column_name,
                "old_data": json.loads(entry.old_data) if entry.old_data else None,
                "new_data": json.loads(entry.new_data) if entry.new_data else None,
                "action": entry.action,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching history: {str(e)}"
        )


@router.get("/record/{table_name}/{record_id}")
def get_record_history(
    table_name: str,
    record_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all history for a specific record"""
    try:
        # Only super_admin and org_admin can view history
        if current_user.role_name not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view history"
            )

        history_entries = history_repository.get_record_history(
            db=db,
            table_name=table_name,
            record_id=record_id
        )

        # Format the response
        result = []
        for entry in history_entries:
            result.append({
                "id": str(entry.id),
                "table_name_changed": entry.table_name_changed,
                "record_id": entry.record_id,
                "initial_user_email": entry.initial_user_email,
                "last_user_email": entry.last_user_email,
                "last_timestamp": entry.last_timestamp.isoformat() if entry.last_timestamp else None,
                "column_name": entry.column_name,
                "old_data": json.loads(entry.old_data) if entry.old_data else None,
                "new_data": json.loads(entry.new_data) if entry.new_data else None,
                "action": entry.action,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching record history: {str(e)}"
        )


@router.get("/tables")
def get_tracked_tables(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of tables being tracked"""
    try:
        # Only super_admin and org_admin can view history
        if current_user.role_name not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view history"
            )

        return {
            "tables": [
                {"name": "products", "display_name": "Products"},
                {"name": "policies", "display_name": "Policies"},
                {"name": "risks", "display_name": "Risks"},
                {"name": "objectives", "display_name": "Objectives"}
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/organization/{org_id}/clear-all")
def clear_all_history_for_organization(
    org_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clear all history records for a specific organization"""
    try:
        # Only super_admin and org_admin can clear history
        if current_user.role_name not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to clear history"
            )

        # Org_admins can only clear their own organization's history
        if current_user.role_name == "org_admin" and str(current_user.organisation_id) != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only clear history for your own organization"
            )

        # Delete all history records for the organization
        deleted_count = history_repository.clear_all_history_for_organization(
            db=db,
            organisation_id=uuid.UUID(org_id)
        )

        return {
            "message": f"Successfully cleared {deleted_count} history records",
            "deleted_count": deleted_count
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid organization ID: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while clearing history: {str(e)}"
        )