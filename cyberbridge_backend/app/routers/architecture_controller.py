from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
from datetime import datetime
import json
import os
import shutil

from app.database.database import get_db
from app.dtos import schemas
from app.models import models
from app.services.auth_service import get_current_active_user

router = APIRouter(prefix="/architecture", tags=["Architecture"])


def _get_upload_base() -> str:
    base_path = os.environ.get("UPLOAD_PATH")
    if base_path:
        return base_path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "uploads")


def _parse_json_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _save_upload(file: UploadFile, folder: str, item_id: uuid.UUID) -> tuple[str, int, str]:
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


def _remove_upload(file_path: Optional[str]) -> None:
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


def _diagram_to_response(db: Session, diagram: models.ArchitectureDiagram) -> dict:
    framework_links = db.query(models.ArchitectureDiagramFramework).filter(
        models.ArchitectureDiagramFramework.diagram_id == diagram.id
    ).all()
    framework_ids = [str(link.framework_id) for link in framework_links]
    framework_names = []
    if framework_ids:
        framework_names = [
            fw.name for fw in db.query(models.Framework)
            .filter(models.Framework.id.in_(framework_ids)).all()
        ]

    risk_links = db.query(models.ArchitectureDiagramRisk).filter(
        models.ArchitectureDiagramRisk.diagram_id == diagram.id
    ).all()
    risk_ids = [str(link.risk_id) for link in risk_links]

    return {
        "id": str(diagram.id),
        "name": diagram.name,
        "description": diagram.description,
        "diagram_type": diagram.diagram_type,
        "file_name": diagram.file_name,
        "file_url": None,
        "file_size": diagram.file_size,
        "framework_ids": framework_ids,
        "framework_names": framework_names,
        "risk_ids": risk_ids,
        "owner": diagram.owner,
        "version": diagram.version,
        "created_at": diagram.created_at.isoformat() if diagram.created_at else None,
        "updated_at": diagram.updated_at.isoformat() if diagram.updated_at else None,
        "organisation_id": str(diagram.organisation_id) if diagram.organisation_id else None
    }


@router.get("/diagrams", response_model=List[schemas.ArchitectureDiagramResponse])
def list_diagrams(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    query = db.query(models.ArchitectureDiagram)
    if current_user.role_name != "super_admin":
        query = query.filter(models.ArchitectureDiagram.organisation_id == current_user.organisation_id)
    diagrams = query.order_by(models.ArchitectureDiagram.created_at.desc()).all()
    return [_diagram_to_response(db, diagram) for diagram in diagrams]


@router.post("/diagrams", response_model=schemas.ArchitectureDiagramResponse)
def create_diagram(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    diagram_type: str = Form(...),
    framework_ids: Optional[str] = Form(None),
    risk_ids: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    if not current_user.organisation_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organisation not found for user.")

    diagram = models.ArchitectureDiagram(
        name=name,
        description=description,
        diagram_type=diagram_type,
        owner=owner,
        version=version,
        organisation_id=current_user.organisation_id
    )
    db.add(diagram)
    db.commit()
    db.refresh(diagram)

    if file:
        filename, file_size, file_path = _save_upload(file, "architecture", diagram.id)
        diagram.file_name = filename
        diagram.file_size = file_size
        diagram.file_path = file_path

    framework_id_list = _parse_json_list(framework_ids)
    for framework_id in framework_id_list:
        db.add(models.ArchitectureDiagramFramework(
            diagram_id=diagram.id,
            framework_id=uuid.UUID(framework_id)
        ))

    risk_id_list = _parse_json_list(risk_ids)
    for risk_id in risk_id_list:
        db.add(models.ArchitectureDiagramRisk(
            diagram_id=diagram.id,
            risk_id=uuid.UUID(risk_id)
        ))

    db.commit()
    db.refresh(diagram)
    return _diagram_to_response(db, diagram)


@router.put("/diagrams/{diagram_id}", response_model=schemas.ArchitectureDiagramResponse)
def update_diagram(
    diagram_id: str,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    diagram_type: str = Form(...),
    framework_ids: Optional[str] = Form(None),
    risk_ids: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    diagram = db.query(models.ArchitectureDiagram).filter(
        models.ArchitectureDiagram.id == uuid.UUID(diagram_id)
    ).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    if current_user.role_name != "super_admin" and diagram.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this diagram")

    diagram.name = name
    diagram.description = description
    diagram.diagram_type = diagram_type
    diagram.owner = owner
    diagram.version = version

    if file:
        _remove_upload(diagram.file_path)
        filename, file_size, file_path = _save_upload(file, "architecture", diagram.id)
        diagram.file_name = filename
        diagram.file_size = file_size
        diagram.file_path = file_path

    db.query(models.ArchitectureDiagramFramework).filter(
        models.ArchitectureDiagramFramework.diagram_id == diagram.id
    ).delete()
    db.query(models.ArchitectureDiagramRisk).filter(
        models.ArchitectureDiagramRisk.diagram_id == diagram.id
    ).delete()

    framework_id_list = _parse_json_list(framework_ids)
    for framework_id in framework_id_list:
        db.add(models.ArchitectureDiagramFramework(
            diagram_id=diagram.id,
            framework_id=uuid.UUID(framework_id)
        ))

    risk_id_list = _parse_json_list(risk_ids)
    for risk_id in risk_id_list:
        db.add(models.ArchitectureDiagramRisk(
            diagram_id=diagram.id,
            risk_id=uuid.UUID(risk_id)
        ))

    db.commit()
    db.refresh(diagram)
    return _diagram_to_response(db, diagram)


@router.delete("/diagrams/{diagram_id}")
def delete_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    diagram = db.query(models.ArchitectureDiagram).filter(
        models.ArchitectureDiagram.id == uuid.UUID(diagram_id)
    ).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    if current_user.role_name != "super_admin" and diagram.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this diagram")

    db.query(models.ArchitectureDiagramFramework).filter(
        models.ArchitectureDiagramFramework.diagram_id == diagram.id
    ).delete()
    db.query(models.ArchitectureDiagramRisk).filter(
        models.ArchitectureDiagramRisk.diagram_id == diagram.id
    ).delete()

    _remove_upload(diagram.file_path)
    db.delete(diagram)
    db.commit()
    return {"success": True}
