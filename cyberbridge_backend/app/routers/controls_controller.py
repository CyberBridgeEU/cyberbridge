# routers/controls_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging

from ..repositories import control_repository, history_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..constants.control_templates import get_available_control_sets, get_control_set_by_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/controls", tags=["controls"], responses={404: {"description": "Not found"}})

# Control Set endpoints
@router.get("/control-sets", response_model=List[schemas.ControlSetResponse])
def get_all_control_sets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        control_sets = control_repository.get_control_sets(db, current_user, skip=skip, limit=limit)
        return control_sets
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching control sets: {str(e)}"
        )

@router.post("/control-sets", response_model=schemas.ControlSetResponse)
def create_control_set(control_set: schemas.ControlSetCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        new_control_set = control_repository.create_control_set(db=db, control_set=control_set.model_dump(), current_user=current_user)
        return new_control_set
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the control set: {str(e)}"
        )

# Control Status endpoints
@router.get("/statuses", response_model=List[schemas.ControlStatusResponse])
def get_control_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        statuses = control_repository.get_control_statuses(db, skip=skip, limit=limit)
        return statuses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching control statuses: {str(e)}"
        )

# Control Templates endpoints
@router.get("/templates", response_model=List[schemas.ControlSetTemplateInfo])
def get_control_templates(current_user: schemas.UserBase = Depends(get_current_active_user)):
    """
    Get all available control set templates that can be imported.
    These are pre-loaded control sets embedded in the application.
    """
    try:
        templates = get_available_control_sets()
        return templates
    except Exception as e:
        logger.error(f"Error fetching control templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching control templates: {str(e)}"
        )

@router.get("/templates/{template_name}", response_model=schemas.ControlSetTemplateDetail)
def get_control_template_detail(template_name: str, current_user: schemas.UserBase = Depends(get_current_active_user)):
    """
    Get detailed information about a specific control set template, including all controls.
    """
    try:
        template = get_control_set_by_name(template_name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Control template '{template_name}' not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching control template detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching control template: {str(e)}"
        )

@router.post("/import-template", response_model=schemas.ControlImportResponse)
def import_controls_from_template(
    request: schemas.ControlTemplateImportRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Import controls from a pre-loaded template into the user's control register.
    """
    try:
        # Get the template
        template = get_control_set_by_name(request.template_name)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Control template '{request.template_name}' not found"
            )

        # Get default status (Not Implemented)
        default_status = control_repository.get_status_id_by_name(db, "Not Implemented")
        if not default_status:
            default_status_obj = control_repository.get_control_statuses(db)[0] if control_repository.get_control_statuses(db) else None
            if default_status_obj:
                default_status = default_status_obj.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No control statuses found. Please seed the database first."
                )

        # Get or create control set for this template
        control_set = control_repository.get_or_create_control_set(db, template["name"], current_user)
        if not control_set:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create control set for template: {template['name']}"
            )

        # Get existing codes in this org to skip duplicates
        from ..models import models as db_models
        existing_codes = {
            code for (code,) in db.query(db_models.Control.code).filter(
                db_models.Control.organisation_id == current_user.organisation_id,
                db_models.Control.code.isnot(None)
            ).all()
        }

        # Prepare controls data, filtering out duplicates
        controls_data = []
        skipped_count = 0
        skipped_errors = []
        for control in template["controls"]:
            if control["code"] in existing_codes:
                skipped_count += 1
                skipped_errors.append(f"{control['code']} already exists — skipped")
                continue
            controls_data.append({
                "code": control["code"],
                "name": control["name"],
                "description": control.get("description", "")
            })
            existing_codes.add(control["code"])  # Track within batch

        # Bulk create controls
        result = control_repository.bulk_create_controls(
            db=db,
            controls_data=controls_data,
            control_set_id=control_set.id,
            control_status_id=default_status,
            current_user=current_user
        )

        total_imported = len(result['created_ids'])
        total_failed = result['failed_count']
        all_errors = skipped_errors + result['errors']

        return schemas.ControlImportResponse(
            success=total_imported > 0 or skipped_count > 0,
            imported_count=total_imported,
            failed_count=total_failed + skipped_count,
            message=f"Imported {total_imported} controls from '{template['name']}', skipped {skipped_count} duplicate(s)",
            imported_control_ids=result['created_ids'],
            errors=all_errors
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing controls from template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while importing controls: {str(e)}"
        )

# Control endpoints
@router.get("", response_model=List[schemas.ControlResponse])
def get_all_controls(control_set_id: str = None, skip: int = 0, limit: int = 1000, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        control_set_uuid = uuid.UUID(control_set_id) if control_set_id else None
        controls = control_repository.get_controls(db, control_set_id=control_set_uuid, current_user=current_user, skip=skip, limit=limit)
        return controls
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching controls: {str(e)}"
        )

@router.get("/{control_id}", response_model=schemas.ControlResponse)
def get_control(control_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        control = control_repository.get_control(db=db, control_id=uuid.UUID(control_id), current_user=current_user)
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")
        return control
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the control: {str(e)}"
        )

@router.post("", response_model=schemas.ControlResponse)
def create_control(control: schemas.ControlCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Create the control
        new_control = control_repository.create_control(db=db, control=control.model_dump(), current_user=current_user)

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="controls",
            record_id=str(new_control.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "code": new_control.code,
                "name": new_control.name,
                "control_set_id": str(new_control.control_set_id),
                "control_status_id": str(new_control.control_status_id)
            }
        )

        return new_control
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the control: {str(e)}"
        )

@router.put("/{control_id}", response_model=schemas.ControlResponse)
def update_control(control_id: str, control: schemas.ControlUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the old control data first
        old_control = control_repository.get_control(db=db, control_id=uuid.UUID(control_id), current_user=current_user)
        if not old_control:
            raise HTTPException(status_code=404, detail="Control not found")

        control_data = control.model_dump()

        # Track changes
        changes = {}
        for key, new_value in control_data.items():
            if new_value is not None:
                old_value = getattr(old_control, key, None)
                if old_value != new_value:
                    changes[key] = {
                        "old": str(old_value) if old_value else None,
                        "new": str(new_value) if new_value else None
                    }

        # Update the control
        updated_control = control_repository.update_control(db=db, control_id=uuid.UUID(control_id), control=control_data, current_user=current_user)

        # Track the update in history if there were changes
        if changes:
            history_repository.track_update(
                db=db,
                table_name="controls",
                record_id=control_id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes=changes
            )

        return updated_control
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the control: {str(e)}"
        )

@router.delete("/{control_id}")
def delete_control(control_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the control before deleting for history tracking
        control = control_repository.get_control(db=db, control_id=uuid.UUID(control_id), current_user=current_user)
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")

        # Delete the control
        deleted_control = control_repository.delete_control(db=db, control_id=uuid.UUID(control_id), current_user=current_user)

        # Track the deletion in history
        history_repository.track_delete(
            db=db,
            table_name="controls",
            record_id=control_id,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={
                "code": control.code,
                "name": control.name,
                "control_set_id": str(control.control_set_id),
                "control_status_id": str(control.control_status_id)
            }
        )

        return {"detail": "Control deleted successfully"}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the control: {str(e)}"
        )

# Control-Risk linking endpoints
@router.post("/{control_id}/risks/{risk_id}")
def link_control_to_risk(
    control_id: str,
    risk_id: str,
    framework_id: str = Query(..., description="Framework ID for this connection"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    try:
        control_repository.link_control_to_risk(db, uuid.UUID(control_id), uuid.UUID(risk_id), uuid.UUID(framework_id))
        return {"detail": "Control linked to risk successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while linking control to risk: {str(e)}"
        )

@router.delete("/{control_id}/risks/{risk_id}")
def unlink_control_from_risk(
    control_id: str,
    risk_id: str,
    framework_id: str = Query(..., description="Framework ID for this connection"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    try:
        result = control_repository.unlink_control_from_risk(db, uuid.UUID(control_id), uuid.UUID(risk_id), uuid.UUID(framework_id))
        if result:
            return {"detail": "Control unlinked from risk successfully"}
        else:
            raise HTTPException(status_code=404, detail="Link not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while unlinking control from risk: {str(e)}"
        )

# Control-Policy linking endpoints
@router.post("/{control_id}/policies/{policy_id}")
def link_control_to_policy(
    control_id: str,
    policy_id: str,
    framework_id: str = Query(..., description="Framework ID for this connection"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    try:
        control_repository.link_control_to_policy(db, uuid.UUID(control_id), uuid.UUID(policy_id), uuid.UUID(framework_id))
        return {"detail": "Control linked to policy successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while linking control to policy: {str(e)}"
        )

@router.delete("/{control_id}/policies/{policy_id}")
def unlink_control_from_policy(
    control_id: str,
    policy_id: str,
    framework_id: str = Query(..., description="Framework ID for this connection"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    try:
        result = control_repository.unlink_control_from_policy(db, uuid.UUID(control_id), uuid.UUID(policy_id), uuid.UUID(framework_id))
        if result:
            return {"detail": "Control unlinked from policy successfully"}
        else:
            raise HTTPException(status_code=404, detail="Link not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while unlinking control from policy: {str(e)}"
        )


# ===========================
# Control Connection Query Endpoints
# ===========================

@router.get("/{control_id}/risks")
def get_risks_for_control(
    control_id: str,
    framework_id: Optional[str] = Query(None, description="Filter by framework ID"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all risks mitigated by a control"""
    try:
        fw_uuid = uuid.UUID(framework_id) if framework_id else None
        risks = control_repository.get_risks_for_control(db, uuid.UUID(control_id), current_user, framework_id=fw_uuid)
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
            detail=f"An error occurred while fetching risks for control: {str(e)}"
        )


@router.get("/{control_id}/policies")
def get_policies_for_control(
    control_id: str,
    framework_id: Optional[str] = Query(None, description="Filter by framework ID"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all policies that govern a control"""
    try:
        fw_uuid = uuid.UUID(framework_id) if framework_id else None
        policies = control_repository.get_policies_for_control(db, uuid.UUID(control_id), current_user, framework_id=fw_uuid)
        # Convert to dict format for response
        return [
            {
                "id": str(policy.id),
                "title": policy.title,
                "policy_code": policy.policy_code,
                "owner": policy.owner,
                "status": getattr(policy, "status", None),
                "body": policy.body[:200] + "..." if policy.body and len(policy.body) > 200 else policy.body,
            }
            for policy in policies
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching policies for control: {str(e)}"
        )
