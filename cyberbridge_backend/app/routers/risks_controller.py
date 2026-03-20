# routers/risks_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
import logging

from ..repositories import risks_repository, history_repository, scan_finding_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..services.notification_service import send_risk_status_critical_notification_to_org
from ..constants import risk_templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risks", tags=["risks"], responses={404: {"description": "Not found"}})

@router.get("", response_model=List[schemas.RiskResponse])
def get_all_risks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        risks = risks_repository.get_risks(db, current_user, skip=skip, limit=limit)
        return risks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risks: {str(e)}"
        )

@router.get("/categories", response_model=List[schemas.RiskCategoryResponse])
def get_risk_categories(asset_category_id: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        asset_category_uuid = uuid.UUID(asset_category_id) if asset_category_id else None
        categories = risks_repository.get_risk_categories(db, asset_category_id=asset_category_uuid, skip=skip, limit=limit)
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risk categories: {str(e)}"
        )

@router.get("/severities", response_model=List[schemas.RiskSeverityResponse])
def get_risk_severities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        severities = risks_repository.get_risk_severities(db, skip=skip, limit=limit)
        return severities
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risk severities: {str(e)}"
        )

@router.get("/statuses", response_model=List[schemas.RiskStatusResponse])
def get_risk_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        statuses = risks_repository.get_risk_statuses(db, skip=skip, limit=limit)
        return statuses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risk statuses: {str(e)}"
        )

@router.post("", response_model=schemas.RiskResponse)
def create_risk(risk: schemas.RiskCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Create the risk
        new_risk = risks_repository.create_risk(db=db, risk=risk.model_dump(), current_user=current_user)
        if not new_risk:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Risk creation failed"
            )

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="risks",
            record_id=str(new_risk.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "risk_category_name": new_risk.risk_category_name,
                "risk_category_description": new_risk.risk_category_description,
                "asset_category_id": str(new_risk.asset_category_id) if new_risk.asset_category_id else None,
                "assessment_status": new_risk.assessment_status,
                "likelihood": str(new_risk.likelihood) if new_risk.likelihood else None,
                "residual_risk": str(new_risk.residual_risk) if new_risk.residual_risk else None,
                "risk_severity_id": str(new_risk.risk_severity_id) if new_risk.risk_severity_id else None,
                "risk_status_id": str(new_risk.risk_status_id) if new_risk.risk_status_id else None
            }
        )

        # Send notification if severity is High or Critical
        if new_risk.risk_severity and new_risk.risk_severity.lower() in ['high', 'critical']:
            try:
                send_risk_status_critical_notification_to_org(
                    db=db,
                    organisation_id=str(current_user.organisation_id),
                    risk_name=new_risk.risk_category_name,
                    old_severity="New",
                    new_severity=new_risk.risk_severity,
                    risk_description=new_risk.risk_category_description,
                    changed_by_email=current_user.email,
                    exclude_user_id=str(current_user.id)
                )
            except Exception as notif_error:
                logger.warning(f"Failed to send risk notification: {str(notif_error)}")

        return new_risk
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Risk code already exists in your organization."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the risk: {str(e)}"
        )

@router.put("/{risk_id}", response_model=schemas.RiskResponse)
def update_risk(risk_id: str, risk: schemas.RiskUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the old risk data first
        old_risk = risks_repository.get_risk(db=db, risk_id=uuid.UUID(risk_id), current_user=current_user)
        if not old_risk:
            raise HTTPException(status_code=404, detail="Risk not found")

        # Store old severity for notification comparison
        old_severity = old_risk.risk_severity if hasattr(old_risk, 'risk_severity') else None

        risk_data = risk.model_dump()

        # Track changes
        changes = {}
        for key, new_value in risk_data.items():
            if new_value is not None:
                old_value = getattr(old_risk, key, None)
                if old_value != new_value:
                    changes[key] = {
                        "old": str(old_value) if old_value else None,
                        "new": str(new_value) if new_value else None
                    }

        # Update the risk
        updated_risk = risks_repository.update_risk(db=db, risk_id=uuid.UUID(risk_id), risk=risk_data, current_user=current_user)
        if not updated_risk:
            raise HTTPException(status_code=404, detail="Risk not found")

        # Track the update in history if there were changes
        if changes:
            history_repository.track_update(
                db=db,
                table_name="risks",
                record_id=risk_id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes=changes
            )

        # Send notification if severity changed TO High or Critical
        new_severity = updated_risk.risk_severity if hasattr(updated_risk, 'risk_severity') else None
        if new_severity and new_severity.lower() in ['high', 'critical']:
            # Only send if severity actually changed (not just editing other fields)
            old_sev_lower = old_severity.lower() if old_severity else None
            new_sev_lower = new_severity.lower()
            if old_sev_lower != new_sev_lower:
                try:
                    send_risk_status_critical_notification_to_org(
                        db=db,
                        organisation_id=str(current_user.organisation_id),
                        risk_name=updated_risk.risk_category_name,
                        old_severity=old_severity or "Unknown",
                        new_severity=new_severity,
                        risk_description=updated_risk.risk_category_description,
                        changed_by_email=current_user.email,
                        exclude_user_id=str(current_user.id)
                    )
                except Exception as notif_error:
                    logger.warning(f"Failed to send risk severity change notification: {str(notif_error)}")

        return updated_risk
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Risk code already exists in your organization."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the risk: {str(e)}"
        )

@router.delete("/{risk_id}")
def delete_risk(risk_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the risk data before deletion
        old_risk = risks_repository.get_risk(db=db, risk_id=uuid.UUID(risk_id), current_user=current_user)
        if not old_risk:
            raise HTTPException(status_code=404, detail="Risk not found")

        # Track the deletion in history
        history_repository.track_delete(
            db=db,
            table_name="risks",
            record_id=risk_id,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={
                "risk_category_name": old_risk.risk_category_name,
                "risk_category_description": old_risk.risk_category_description,
                "asset_category_id": str(old_risk.asset_category_id) if old_risk.asset_category_id else None,
                "assessment_status": old_risk.assessment_status,
                "likelihood": str(old_risk.likelihood) if old_risk.likelihood else None,
                "residual_risk": str(old_risk.residual_risk) if old_risk.residual_risk else None,
                "risk_severity_id": str(old_risk.risk_severity_id) if old_risk.risk_severity_id else None,
                "risk_status_id": str(old_risk.risk_status_id) if old_risk.risk_status_id else None
            }
        )

        # Delete the risk
        risk = risks_repository.delete_risk(db=db, risk_id=uuid.UUID(risk_id), current_user=current_user)
        if risk is None:
            raise HTTPException(status_code=404, detail="Risk not found")
        return {"message": "Risk deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        # Handle business rule violations (like ownership violations)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the risk: {str(e)}"
        )


# ===========================
# Risk Template Endpoints
# ===========================

@router.get("/templates", response_model=schemas.RiskTemplatesListResponse)
def get_risk_template_categories(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all available risk template categories"""
    try:
        categories = risk_templates.get_all_categories()
        return schemas.RiskTemplatesListResponse(
            categories=[
                schemas.RiskTemplateCategoryResponse(**cat) for cat in categories
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching risk template categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risk template categories: {str(e)}"
        )


@router.get("/templates/{category_id}", response_model=schemas.RiskTemplateRisksResponse)
def get_risk_templates_by_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all risk templates for a specific category"""
    try:
        # Get category info
        category = risk_templates.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk template category '{category_id}' not found"
            )

        # Get risks for category
        risks = risk_templates.get_risks_by_category(category_id)

        return schemas.RiskTemplateRisksResponse(
            category_id=category_id,
            category_name=category["name"],
            risks=[schemas.RiskTemplateItem(**risk) for risk in risks]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk templates for category '{category_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching risk templates: {str(e)}"
        )


@router.post("/templates/import", response_model=schemas.RiskTemplateImportResponse)
def import_risk_templates(
    import_request: schemas.RiskTemplateImportRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Import selected risk templates as new risks"""
    try:
        from ..models import models

        # Validate category exists
        category = risk_templates.get_category_by_id(import_request.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk template category '{import_request.category_id}' not found"
            )

        # Validate required fields
        if not import_request.selected_risks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No risks selected for import"
            )

        # Convert string UUIDs to UUID objects
        try:
            asset_category_id = uuid.UUID(import_request.asset_category_id)
            likelihood_id = uuid.UUID(import_request.default_likelihood)
            severity_id = uuid.UUID(import_request.default_severity)
            residual_risk_id = uuid.UUID(import_request.default_residual_risk)
            status_id = uuid.UUID(import_request.default_status)
            scope_entity_id = uuid.UUID(import_request.scope_entity_id) if import_request.scope_entity_id else None
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {str(e)}"
            )

        # Get existing risk codes for this org to avoid duplicates
        existing_codes = {
            code for (code,) in db.query(models.Risks.risk_code).filter(
                models.Risks.organisation_id == current_user.organisation_id,
                models.Risks.risk_code.isnot(None)
            ).all()
        }

        # Convert selected risks to dict format, skipping duplicate codes
        risks_data = []
        skipped_count = 0
        skipped_errors = []
        for risk in import_request.selected_risks:
            template_risk_code = risk.risk_code.strip() if risk.risk_code else None
            if not template_risk_code:
                skipped_count += 1
                skipped_errors.append(f"{risk.risk_category_name}: missing risk_code — skipped")
                continue
            if template_risk_code and template_risk_code in existing_codes:
                skipped_count += 1
                skipped_errors.append(f"{template_risk_code} already exists — skipped")
                continue

            risks_data.append({
                "risk_code": template_risk_code,
                "risk_category_name": risk.risk_category_name,
                "risk_category_description": risk.risk_category_description,
                "risk_potential_impact": risk.risk_potential_impact,
                "risk_control": risk.risk_control
            })

            if template_risk_code:
                existing_codes.add(template_risk_code)  # track within same batch

        if not risks_data:
            return schemas.RiskTemplateImportResponse(
                success=skipped_count > 0,
                imported_count=0,
                failed_count=skipped_count,
                message=f"No new risks imported from '{category['name']}'. Skipped {skipped_count} duplicate(s).",
                imported_risk_ids=[],
                errors=skipped_errors
            )

        # Bulk create risks
        result = risks_repository.bulk_create_risks(
            db=db,
            risks_data=risks_data,
            asset_category_id=asset_category_id,
            likelihood_id=likelihood_id,
            severity_id=severity_id,
            residual_risk_id=residual_risk_id,
            status_id=status_id,
            current_user=current_user,
            scope_name=import_request.scope_name,
            scope_entity_id=scope_entity_id
        )

        imported_count = len(result["created_ids"])
        failed_count = result["failed_count"] + skipped_count
        total = len(import_request.selected_risks)
        all_errors = skipped_errors + result["errors"]

        # Track import in history
        if imported_count > 0:
            history_repository.track_insert(
                db=db,
                table_name="risks",
                record_id=f"bulk_import_{import_request.category_id}",
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                new_data={
                    "action": "bulk_import",
                    "category": import_request.category_id,
                    "imported_count": imported_count,
                    "risk_ids": result["created_ids"]
                }
            )

        return schemas.RiskTemplateImportResponse(
            success=imported_count > 0 or skipped_count > 0,
            imported_count=imported_count,
            failed_count=failed_count,
            message=f"Successfully imported {imported_count} of {total} risks from '{category['name']}' template, skipped {skipped_count} duplicate(s)",
            imported_risk_ids=result["created_ids"],
            errors=all_errors
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing risk templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while importing risk templates: {str(e)}"
        )


# ===========================
# Risk Connection Endpoints
# ===========================

@router.get("/{risk_id}/assets")
def get_assets_for_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all assets linked to a risk"""
    try:
        assets = risks_repository.get_assets_for_risk(db, uuid.UUID(risk_id), current_user)
        # Convert to dict format for response
        return [
            {
                "id": str(asset.id),
                "name": asset.name,
                "description": asset.description,
                "ip_address": asset.ip_address,
                "asset_type_name": getattr(asset, "asset_type_name", None),
                "asset_type_icon": getattr(asset, "asset_type_icon", None),
                "status_name": getattr(asset, "status_name", None),
                "criticality_label": getattr(asset, "criticality_label", None),
            }
            for asset in assets
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching assets for risk: {str(e)}"
        )


@router.get("/{risk_id}/controls")
def get_controls_for_risk(
    risk_id: str,
    framework_id: Optional[str] = Query(None, description="Filter by framework ID"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all controls that mitigate a risk"""
    try:
        fw_uuid = uuid.UUID(framework_id) if framework_id else None
        controls = risks_repository.get_controls_for_risk(db, uuid.UUID(risk_id), current_user, framework_id=fw_uuid)
        # Convert to dict format for response
        return [
            {
                "id": str(control.id),
                "code": control.code,
                "name": control.name,
                "description": control.description,
                "category": control.category,
                "owner": control.owner,
                "control_status_name": getattr(control, "control_status_name", None),
                "control_set_name": getattr(control, "control_set_name", None),
            }
            for control in controls
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching controls for risk: {str(e)}"
        )


# ===========================
# Risk → Scan Finding Endpoints
# ===========================

@router.get("/{risk_id}/findings", response_model=List[schemas.ScanFindingResponse])
def get_findings_for_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all scan findings linked to a risk"""
    try:
        findings = scan_finding_repository.get_findings_for_risk(db, uuid.UUID(risk_id))
        return findings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching findings for risk: {str(e)}"
        )


@router.post("/{risk_id}/findings/{finding_id}")
def link_finding_to_risk(
    risk_id: str,
    finding_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Manually link a scan finding to a risk"""
    try:
        success = scan_finding_repository.link_finding_to_risk(
            db, uuid.UUID(finding_id), uuid.UUID(risk_id), is_auto=False
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to link finding to risk")
        return {"message": "Finding linked to risk successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while linking finding to risk: {str(e)}"
        )


@router.post("/{risk_id}/assets/{asset_id}")
def link_asset_to_risk(
    risk_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Link an asset to a risk"""
    try:
        risks_repository.link_asset_to_risk(db, uuid.UUID(risk_id), uuid.UUID(asset_id))
        return {"message": "Asset linked to risk successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while linking asset to risk: {str(e)}"
        )


@router.delete("/{risk_id}/assets/{asset_id}")
def unlink_asset_from_risk(
    risk_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Unlink an asset from a risk"""
    try:
        success = risks_repository.unlink_asset_from_risk(db, uuid.UUID(risk_id), uuid.UUID(asset_id))
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"message": "Asset unlinked from risk successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while unlinking asset from risk: {str(e)}"
        )


@router.get("/{risk_id}/objectives")
def get_objectives_for_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all objectives linked to a risk"""
    try:
        objectives = risks_repository.get_objectives_for_risk(db, uuid.UUID(risk_id), current_user)
        return objectives
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching objectives for risk: {str(e)}"
        )


@router.post("/{risk_id}/objectives/{objective_id}")
def link_objective_to_risk(
    risk_id: str,
    objective_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Link an objective to a risk"""
    try:
        risks_repository.link_objective_to_risk(db, uuid.UUID(risk_id), uuid.UUID(objective_id))
        return {"message": "Objective linked to risk successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while linking objective to risk: {str(e)}"
        )


@router.delete("/{risk_id}/objectives/{objective_id}")
def unlink_objective_from_risk(
    risk_id: str,
    objective_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Unlink an objective from a risk"""
    try:
        success = risks_repository.unlink_objective_from_risk(db, uuid.UUID(risk_id), uuid.UUID(objective_id))
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"message": "Objective unlinked from risk successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while unlinking objective from risk: {str(e)}"
        )


@router.delete("/{risk_id}/findings/{finding_id}")
def unlink_finding_from_risk(
    risk_id: str,
    finding_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Unlink a scan finding from a risk"""
    try:
        success = scan_finding_repository.unlink_finding_from_risk(
            db, uuid.UUID(finding_id), uuid.UUID(risk_id)
        )
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"message": "Finding unlinked from risk successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while unlinking finding from risk: {str(e)}"
        )
