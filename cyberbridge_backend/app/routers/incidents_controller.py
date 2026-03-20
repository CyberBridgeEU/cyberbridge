# routers/incidents_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid
import logging

from ..repositories import incidents_repository, history_repository, incident_patches_repository, enisa_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"], responses={404: {"description": "Not found"}})


@router.get("", response_model=List[schemas.IncidentResponse])
def get_all_incidents(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return incidents_repository.get_incidents(db, current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching incidents: {str(e)}"
        )


@router.get("/statuses", response_model=List[schemas.IncidentStatusResponse])
def get_incident_statuses(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return incidents_repository.get_incident_statuses(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching incident statuses: {str(e)}"
        )


@router.post("", response_model=schemas.IncidentResponse)
def create_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        new_incident = incidents_repository.create_incident(db, incident.model_dump(), current_user)
        if not new_incident:
            raise HTTPException(status_code=500, detail="Incident creation failed")

        history_repository.track_insert(
            db=db,
            table_name="incidents",
            record_id=str(new_incident.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "title": new_incident.title,
                "incident_code": new_incident.incident_code,
                "incident_severity_id": str(new_incident.incident_severity_id),
                "incident_status_id": str(new_incident.incident_status_id),
            }
        )

        return new_incident
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Incident code already exists in your organization.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the incident: {str(e)}")


@router.put("/{incident_id}", response_model=schemas.IncidentResponse)
def update_incident(incident_id: str, incident: schemas.IncidentUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        old_incident = incidents_repository.get_incident(db, uuid.UUID(incident_id), current_user)
        if not old_incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident_data = incident.model_dump()
        changes = {}
        for key, new_value in incident_data.items():
            if new_value is not None:
                old_value = getattr(old_incident, key, None)
                if old_value != new_value:
                    changes[key] = {"old": str(old_value) if old_value else None, "new": str(new_value) if new_value else None}

        updated = incidents_repository.update_incident(db, uuid.UUID(incident_id), incident_data, current_user)
        if not updated:
            raise HTTPException(status_code=404, detail="Incident not found")

        if changes:
            history_repository.track_update(
                db=db,
                table_name="incidents",
                record_id=incident_id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes=changes
            )

        return updated
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Incident code already exists in your organization.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the incident: {str(e)}")


@router.delete("/{incident_id}")
def delete_incident(incident_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        old_incident = incidents_repository.get_incident(db, uuid.UUID(incident_id), current_user)
        if not old_incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        history_repository.track_delete(
            db=db,
            table_name="incidents",
            record_id=incident_id,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={"title": old_incident.title, "incident_code": old_incident.incident_code}
        )

        result = incidents_repository.delete_incident(db, uuid.UUID(incident_id), current_user)
        if result is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        return {"message": "Incident deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the incident: {str(e)}")


# ===========================
# AI Analysis Endpoint
# ===========================

@router.post("/{incident_id}/analyze")
async def analyze_incident(incident_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        incident = incidents_repository.get_incident(db, uuid.UUID(incident_id), current_user)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        incident_data = {
            "title": incident.title,
            "description": incident.description,
            "severity": getattr(incident, "incident_severity", None),
            "status": getattr(incident, "incident_status", None),
            "reported_by": incident.reported_by,
            "discovered_at": str(incident.discovered_at) if incident.discovered_at else None,
            "containment_actions": incident.containment_actions,
            "root_cause": incident.root_cause,
            "remediation_steps": incident.remediation_steps,
        }

        llm_service = LLMService(db)
        analysis = await llm_service.analyze_incident(incident_data)

        updated = incidents_repository.save_ai_analysis(db, uuid.UUID(incident_id), analysis, current_user)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to save analysis")

        return {"analysis": analysis, "incident_id": incident_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing incident {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")


# ===========================
# Connection Endpoints
# ===========================

@router.get("/{incident_id}/frameworks")
def get_frameworks_for_incident(incident_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        frameworks = incidents_repository.get_frameworks_for_incident(db, uuid.UUID(incident_id), current_user)
        return [{"id": str(f.id), "name": f.name, "description": f.description} for f in frameworks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching frameworks: {str(e)}")


@router.post("/{incident_id}/frameworks/{framework_id}")
def link_framework(incident_id: str, framework_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        success = incidents_repository.link_framework(db, uuid.UUID(incident_id), uuid.UUID(framework_id))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to link framework")
        return {"message": "Framework linked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking framework: {str(e)}")


@router.delete("/{incident_id}/frameworks/{framework_id}")
def unlink_framework(incident_id: str, framework_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        success = incidents_repository.unlink_framework(db, uuid.UUID(incident_id), uuid.UUID(framework_id))
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"message": "Framework unlinked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking framework: {str(e)}")


@router.get("/{incident_id}/risks")
def get_risks_for_incident(incident_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        risks = incidents_repository.get_risks_for_incident(db, uuid.UUID(incident_id), current_user)
        return [
            {"id": str(r.id), "risk_code": r.risk_code, "risk_category_name": r.risk_category_name,
             "risk_severity": getattr(r, "risk_severity", None), "risk_status": getattr(r, "risk_status", None)}
            for r in risks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching risks: {str(e)}")


@router.post("/{incident_id}/risks/{risk_id}")
def link_risk(incident_id: str, risk_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        success = incidents_repository.link_risk(db, uuid.UUID(incident_id), uuid.UUID(risk_id))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to link risk")
        return {"message": "Risk linked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking risk: {str(e)}")


@router.delete("/{incident_id}/risks/{risk_id}")
def unlink_risk(incident_id: str, risk_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        success = incidents_repository.unlink_risk(db, uuid.UUID(incident_id), uuid.UUID(risk_id))
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"message": "Risk unlinked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking risk: {str(e)}")


@router.get("/{incident_id}/assets")
def get_assets_for_incident(incident_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        assets = incidents_repository.get_assets_for_incident(db, uuid.UUID(incident_id), current_user)
        return [
            {"id": str(a.id), "name": a.name, "description": a.description,
             "ip_address": a.ip_address, "asset_type_name": getattr(a, "asset_type_name", None),
             "status_name": getattr(a, "status_name", None)}
            for a in assets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching assets: {str(e)}")


@router.post("/{incident_id}/assets/{asset_id}")
def link_asset(incident_id: str, asset_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        success = incidents_repository.link_asset(db, uuid.UUID(incident_id), uuid.UUID(asset_id))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to link asset")
        return {"message": "Asset linked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking asset: {str(e)}")


@router.delete("/{incident_id}/assets/{asset_id}")
def unlink_asset(incident_id: str, asset_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        success = incidents_repository.unlink_asset(db, uuid.UUID(incident_id), uuid.UUID(asset_id))
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        return {"message": "Asset unlinked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking asset: {str(e)}")


# ===========================
# Post-Market Metrics
# ===========================

@router.get("/metrics/post-market", response_model=schemas.PostMarketMetricsResponse)
def get_post_market_metrics(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return incidents_repository.get_post_market_metrics(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


# ===========================
# Patch Tracking Endpoints
# ===========================

@router.get("/{incident_id}/patches", response_model=List[schemas.IncidentPatchResponse])
def get_patches(incident_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    return incident_patches_repository.get_patches_for_incident(db, uuid.UUID(incident_id), current_user)


@router.post("/{incident_id}/patches", response_model=schemas.IncidentPatchResponse)
def create_patch(incident_id: str, data: schemas.IncidentPatchCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return incident_patches_repository.create_patch(db, uuid.UUID(incident_id), data.model_dump(), current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Patch version already exists for this incident")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating patch: {str(e)}")


@router.put("/patches/{patch_id}", response_model=schemas.IncidentPatchResponse)
def update_patch(patch_id: str, data: schemas.IncidentPatchUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = incident_patches_repository.update_patch(db, uuid.UUID(patch_id), data.model_dump(exclude_unset=True), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Patch not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating patch: {str(e)}")


@router.delete("/patches/{patch_id}")
def delete_patch(patch_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = incident_patches_repository.delete_patch(db, uuid.UUID(patch_id), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Patch not found")
        return {"message": "Patch deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting patch: {str(e)}")


# ===========================
# ENISA Reporting Endpoints
# ===========================

@router.get("/{incident_id}/enisa", response_model=schemas.ENISANotificationResponse)
def get_enisa_notification(incident_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    notification = enisa_repository.get_enisa_notification(db, uuid.UUID(incident_id), current_user)
    if not notification:
        raise HTTPException(status_code=404, detail="ENISA notification not found")
    return notification


@router.post("/{incident_id}/enisa", response_model=schemas.ENISANotificationResponse)
def create_enisa_notification(incident_id: str, data: schemas.ENISANotificationCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return enisa_repository.create_enisa_notification(db, uuid.UUID(incident_id), data.model_dump(), current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="ENISA notification already exists for this incident")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ENISA notification: {str(e)}")


@router.put("/enisa/{notification_id}", response_model=schemas.ENISANotificationResponse)
def update_enisa_notification(notification_id: str, data: schemas.ENISANotificationUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = enisa_repository.update_enisa_notification(db, uuid.UUID(notification_id), data.model_dump(exclude_unset=True), current_user)
        if not result:
            raise HTTPException(status_code=404, detail="ENISA notification not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating ENISA notification: {str(e)}")
