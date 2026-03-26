# routers/objectives_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import asyncio
import uuid
import os
import shutil

from ..repositories import objectives_repository, history_repository
from ..dtos import schemas
from ..database.database import get_db
from ..models import models
from ..services.auth_service import get_current_active_user
from ..services import objectives_ai_service
from ..services.roadmap_service import RoadmapService
from ..utils.cancellation import register_task, unregister_task

router = APIRouter(prefix="/objectives", tags=["objectives"], responses={404: {"description": "Not found"}})

@router.post("/create_chapter", response_model=schemas.ChapterResponse)
def create_chapter(chapter: schemas.ChapterCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return objectives_repository.create_chapter(db=db, chapter=chapter.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the chapter: {str(e)}"
        )

@router.post("/update_chapter", response_model=schemas.ChapterResponse)
def update_chapter(chapter: schemas.ChapterUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        chapter_data = chapter.model_dump()
        return objectives_repository.update_chapter(db=db, chapter_id=uuid.UUID(chapter.id), chapter=chapter_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the chapter: {str(e)}"
        )

@router.post("/delete_chapter")
def delete_chapter(request: schemas.OnlyIdInStringFormat, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        chapter = objectives_repository.delete_chapter(db=db, chapter_id=uuid.UUID(request.id))
        if chapter is None:
            raise HTTPException(status_code=404, detail="Chapter not found")
        return {"message": "Chapter deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the chapter: {str(e)}"
        )

@router.get("/get_all_chapters", response_model=List[schemas.ChapterResponse])
def get_all_chapters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        chapters = objectives_repository.get_chapters(db, skip=skip, limit=limit)
        return chapters
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching chapters: {str(e)}"
        )

@router.post("/create_objective", response_model=schemas.ObjectiveResponse)
def create_objective(objective: schemas.ObjectiveCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Create the objective
        new_objective = objectives_repository.create_objective(db=db, objective=objective.model_dump())

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="objectives",
            record_id=str(new_objective.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "title": new_objective.title,
                "requirement_description": new_objective.requirement_description,
                "chapter_id": str(new_objective.chapter_id) if new_objective.chapter_id else None,
                "compliance_status_id": str(new_objective.compliance_status_id) if new_objective.compliance_status_id else None
            }
        )

        return new_objective
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the objective: {str(e)}"
        )

@router.post("/update_objective", response_model=schemas.ObjectiveResponse)
def update_objective(objective: schemas.ObjectiveUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the old objective data first
        old_objective = objectives_repository.get_objective(db=db, objective_id=uuid.UUID(objective.id))
        if not old_objective:
            raise HTTPException(status_code=404, detail="Objective not found")

        objective_data = objective.model_dump()

        # Track changes
        changes = {}
        for key, new_value in objective_data.items():
            if key != 'id' and new_value is not None:
                old_value = getattr(old_objective, key, None)
                if old_value != new_value:
                    changes[key] = {
                        "old": str(old_value) if old_value else None,
                        "new": str(new_value) if new_value else None
                    }

        # Update the objective
        updated_objective = objectives_repository.update_objective(db=db, objective_id=uuid.UUID(objective.id), objective=objective_data)

        # Track the update in history if there were changes
        if changes:
            history_repository.track_update(
                db=db,
                table_name="objectives",
                record_id=objective.id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes=changes
            )

        return updated_objective
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the objective: {str(e)}"
        )

@router.post("/delete_objective")
def delete_objective(request: schemas.OnlyIdInStringFormat, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the objective data before deletion
        old_objective = objectives_repository.get_objective(db=db, objective_id=uuid.UUID(request.id))
        if not old_objective:
            raise HTTPException(status_code=404, detail="Objective not found")

        # Track the deletion in history
        history_repository.track_delete(
            db=db,
            table_name="objectives",
            record_id=request.id,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={
                "title": old_objective.title,
                "subchapter": old_objective.subchapter,
                "chapter_id": str(old_objective.chapter_id) if old_objective.chapter_id else None,
                "compliance_status_id": str(old_objective.compliance_status_id) if old_objective.compliance_status_id else None
            }
        )

        # Delete the objective
        objective = objectives_repository.delete_objective(db=db, objective_id=uuid.UUID(request.id))
        if objective is None:
            raise HTTPException(status_code=404, detail="Objective not found")
        return {"message": "Objective deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the objective: {str(e)}"
        )

@router.get("/get_all_objectives", response_model=List[schemas.ObjectiveResponse])
def get_all_objectives(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        objectives = objectives_repository.get_objectives(db, skip=skip, limit=limit, current_user=current_user)
        return objectives
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching objectives: {str(e)}"
        )

@router.get("/get_compliance_statuses", response_model=List[schemas.ComplianceStatusResponse])
def get_compliance_statuses(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        compliance_statuses = objectives_repository.get_compliance_statuses(db)
        return compliance_statuses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching compliance statuses: {str(e)}"
        )

@router.get("/objectives_checklist", response_model=List[schemas.ChapterWithObjectives])
def get_objectives_checklist(
    framework_id: str = None,
    scope_name: str = None,
    scope_entity_id: str = None,
    operator_role: str = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get objectives checklist with optional scope and operator role filtering.

    Args:
        framework_id: Optional framework ID to filter by
        scope_name: Optional scope type name (e.g., 'Product', 'Organization')
        scope_entity_id: Optional scope entity ID (e.g., product_id, org_id)
        operator_role: Optional economic operator role (e.g., 'Manufacturer', 'Importer', 'Distributor')
    """
    try:
        framework_uuid = None
        if framework_id:
            framework_uuid = uuid.UUID(framework_id)

        scope_entity_uuid = None
        if scope_entity_id:
            scope_entity_uuid = uuid.UUID(scope_entity_id)

        chapters_with_objectives = objectives_repository.get_chapters_with_objectives(
            db,
            framework_uuid,
            current_user,
            scope_name=scope_name,
            scope_entity_id=scope_entity_uuid,
            operator_role=operator_role
        )
        return chapters_with_objectives
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching objectives checklist: {str(e)}"
        )

@router.get("/by_frameworks", response_model=List[schemas.ObjectiveResponse])
def get_objectives_by_frameworks(framework_ids: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Parse comma-separated framework IDs
        framework_uuid_list = []
        if framework_ids:
            for framework_id in framework_ids.split(','):
                framework_uuid_list.append(uuid.UUID(framework_id.strip()))

        objectives = objectives_repository.get_objectives_by_framework_ids(db, framework_uuid_list, current_user)
        return objectives
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching objectives by frameworks: {str(e)}"
        )

@router.post("/analyze_with_ai")
async def analyze_objectives_with_ai(
    request: schemas.OnlyIdInStringFormat,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Analyze objectives using AI based on assessment answers, evidence files, and policies.
    Request body should contain framework_id.
    """
    print(f"DEBUG CONTROLLER: analyze_with_ai endpoint called with request.id={request.id}")
    print(f"DEBUG CONTROLLER: current_user type: {type(current_user)}, current_user: {current_user}")
    print(f"DEBUG CONTROLLER: current_user.id: {current_user.id if hasattr(current_user, 'id') else 'NO ID ATTR'}")
    try:
        print(f"DEBUG CONTROLLER: Converting request.id to UUID")
        framework_id = uuid.UUID(request.id)
        print(f"DEBUG CONTROLLER: framework_id={framework_id}, now converting user_id")
        user_id = uuid.UUID(str(current_user.id))
        print(f"DEBUG CONTROLLER: user_id={user_id}")

        # Call the AI service to analyze objectives (async)
        print(f"DEBUG CONTROLLER: About to call objectives_ai_service.analyze_objectives_with_ai")
        result = await objectives_ai_service.analyze_objectives_with_ai(
            db=db,
            framework_id=framework_id,
            user_id=user_id
        )
        print(f"DEBUG CONTROLLER: Result received: {result}")

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid framework ID: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during AI analysis: {str(e)}"
        )


@router.post("/roadmap/{objective_id}")
async def generate_objective_roadmap(
    objective_id: str,
    request: schemas.RoadmapRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Generate an AI-powered compliance roadmap for a single objective."""
    try:
        obj_uuid = uuid.UUID(objective_id)
        framework_uuid = uuid.UUID(request.framework_id)

        service = RoadmapService(db, current_user)
        user_id = str(current_user.id)

        # Register task so /scanners/cancel-llm can cancel it
        llm_task = asyncio.ensure_future(service.generate_roadmap(obj_uuid, framework_uuid))
        register_task(user_id, llm_task)
        try:
            result = await llm_task
        except asyncio.CancelledError:
            return {"success": False, "error": "Cancelled"}
        finally:
            unregister_task(user_id)

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate roadmap: {str(e)}"
        )


@router.post("/roadmap/bulk")
async def generate_bulk_roadmap(
    request: schemas.RoadmapBulkRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Generate AI-powered compliance roadmaps for multiple objectives."""
    try:
        framework_uuid = uuid.UUID(request.framework_id)
        objective_uuids = [uuid.UUID(oid) for oid in request.objective_ids]

        service = RoadmapService(db, current_user)
        result = await service.generate_roadmap_bulk(framework_uuid, objective_uuids)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk roadmap: {str(e)}"
        )


# ── Objective Evidence file helpers ──────────────────────────────────────────

def _get_upload_base() -> str:
    base_path = os.environ.get("UPLOAD_PATH")
    if base_path:
        return base_path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "uploads")


def _save_upload(file: UploadFile, folder: str, item_id: uuid.UUID) -> tuple:
    base_path = _get_upload_base()
    target_dir = os.path.join(base_path, folder, str(item_id))
    os.makedirs(target_dir, exist_ok=True)
    filename = file.filename
    disk_path = os.path.join(target_dir, filename)
    with open(disk_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file_size = os.path.getsize(disk_path)
    relative_path = os.path.join(folder, str(item_id), filename)
    return filename, file_size, relative_path


def _remove_upload(file_path: str | None) -> None:
    if not file_path:
        return
    base_path = _get_upload_base()
    disk_path = file_path
    if not os.path.isabs(file_path):
        disk_path = os.path.join(base_path, file_path)
    if os.path.exists(disk_path):
        os.remove(disk_path)
    parent_dir = os.path.dirname(disk_path)
    if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
        os.rmdir(parent_dir)


# ── Objective Evidence endpoints ─────────────────────────────────────────────

@router.post("/upload_evidence/{objective_id}")
def upload_objective_evidence(
    objective_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    try:
        obj_uuid = uuid.UUID(objective_id)
        objective = db.query(models.Objectives).filter(models.Objectives.id == obj_uuid).first()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective not found")

        # Remove existing file if replacing
        _remove_upload(objective.evidence_filepath)

        filename, file_size, relative_path = _save_upload(file, "objective_evidence", obj_uuid)

        objective.evidence_filename = filename
        objective.evidence_filepath = relative_path
        objective.evidence_file_type = file.content_type or ""
        objective.evidence_file_size = file_size
        db.commit()

        return {
            "message": "Evidence uploaded successfully",
            "evidence_filename": filename,
            "evidence_file_type": file.content_type or "",
            "evidence_file_size": file_size,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload evidence: {str(e)}",
        )


@router.get("/download_evidence/{objective_id}")
def download_objective_evidence(
    objective_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    try:
        obj_uuid = uuid.UUID(objective_id)
        objective = db.query(models.Objectives).filter(models.Objectives.id == obj_uuid).first()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective not found")
        if not objective.evidence_filepath:
            raise HTTPException(status_code=404, detail="No evidence file attached")

        base_path = _get_upload_base()
        disk_path = objective.evidence_filepath
        if not os.path.isabs(disk_path):
            disk_path = os.path.join(base_path, disk_path)
        if not os.path.exists(disk_path):
            raise HTTPException(status_code=404, detail="Evidence file not found on disk")

        return FileResponse(
            path=disk_path,
            filename=objective.evidence_filename,
            media_type=objective.evidence_file_type or "application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download evidence: {str(e)}",
        )


@router.post("/delete_evidence/{objective_id}")
def delete_objective_evidence(
    objective_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    try:
        obj_uuid = uuid.UUID(objective_id)
        objective = db.query(models.Objectives).filter(models.Objectives.id == obj_uuid).first()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective not found")
        if not objective.evidence_filepath:
            raise HTTPException(status_code=404, detail="No evidence file to delete")

        _remove_upload(objective.evidence_filepath)

        objective.evidence_filename = None
        objective.evidence_filepath = None
        objective.evidence_file_type = None
        objective.evidence_file_size = None
        db.commit()

        return {"message": "Evidence deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete evidence: {str(e)}",
        )
