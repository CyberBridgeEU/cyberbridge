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

router = APIRouter(prefix="/evidence", tags=["Evidence Library"])


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


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None


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


def _evidence_to_response(db: Session, item: models.EvidenceLibraryItem) -> dict:
    framework_links = db.query(models.EvidenceLibraryFramework).filter(
        models.EvidenceLibraryFramework.evidence_id == item.id
    ).all()
    framework_ids = [str(link.framework_id) for link in framework_links]
    framework_names = []
    if framework_ids:
        framework_names = [
            fw.name for fw in db.query(models.Framework)
            .filter(models.Framework.id.in_(framework_ids)).all()
        ]

    control_links = db.query(models.EvidenceLibraryControl).filter(
        models.EvidenceLibraryControl.evidence_id == item.id
    ).all()
    control_ids = [str(link.control_id) for link in control_links]
    control_names = []
    if control_ids:
        controls = db.query(models.Control).filter(models.Control.id.in_(control_ids)).all()
        control_names = [
            f"{control.code} - {control.name}" if control.code else control.name
            for control in controls
        ]

    return {
        "id": str(item.id),
        "name": item.name,
        "description": item.description,
        "evidence_type": item.evidence_type,
        "file_name": item.file_name,
        "file_url": None,
        "file_size": item.file_size,
        "framework_ids": framework_ids,
        "framework_names": framework_names,
        "control_ids": control_ids,
        "control_names": control_names,
        "owner": item.owner,
        "collected_date": item.collected_date.isoformat() if item.collected_date else None,
        "valid_until": item.valid_until.isoformat() if item.valid_until else None,
        "status": item.status,
        "collection_method": item.collection_method,
        "audit_notes": item.audit_notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "organisation_id": str(item.organisation_id) if item.organisation_id else None
    }


@router.get("", response_model=List[schemas.EvidenceLibraryItemResponse])
@router.get("/", response_model=List[schemas.EvidenceLibraryItemResponse])
def list_evidence(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    query = db.query(models.EvidenceLibraryItem)
    if current_user.role_name != "super_admin":
        query = query.filter(models.EvidenceLibraryItem.organisation_id == current_user.organisation_id)
    items = query.order_by(models.EvidenceLibraryItem.created_at.desc()).all()
    return [_evidence_to_response(db, item) for item in items]


@router.post("", response_model=schemas.EvidenceLibraryItemResponse)
@router.post("/", response_model=schemas.EvidenceLibraryItemResponse)
def create_evidence(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    evidence_type: str = Form(...),
    framework_ids: Optional[str] = Form(None),
    control_ids: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    collected_date: str = Form(...),
    valid_until: Optional[str] = Form(None),
    evidence_status: str = Form(...),
    collection_method: str = Form(...),
    audit_notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    if not current_user.organisation_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organisation not found for user.")

    item = models.EvidenceLibraryItem(
        name=name,
        description=description,
        evidence_type=evidence_type,
        owner=owner,
        collected_date=_parse_date(collected_date),
        valid_until=_parse_date(valid_until),
        status=evidence_status,
        collection_method=collection_method,
        audit_notes=audit_notes,
        organisation_id=current_user.organisation_id
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    if file:
        filename, file_size, file_path = _save_upload(file, "evidence_library", item.id)
        item.file_name = filename
        item.file_size = file_size
        item.file_path = file_path

    framework_id_list = _parse_json_list(framework_ids)
    for framework_id in framework_id_list:
        db.add(models.EvidenceLibraryFramework(
            evidence_id=item.id,
            framework_id=uuid.UUID(framework_id)
        ))

    control_id_list = _parse_json_list(control_ids)
    for control_id in control_id_list:
        db.add(models.EvidenceLibraryControl(
            evidence_id=item.id,
            control_id=uuid.UUID(control_id)
        ))

    db.commit()
    db.refresh(item)
    return _evidence_to_response(db, item)


@router.put("/{evidence_id}", response_model=schemas.EvidenceLibraryItemResponse)
def update_evidence(
    evidence_id: str,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    evidence_type: str = Form(...),
    framework_ids: Optional[str] = Form(None),
    control_ids: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    collected_date: str = Form(...),
    valid_until: Optional[str] = Form(None),
    evidence_status: str = Form(...),
    collection_method: str = Form(...),
    audit_notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    item = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == uuid.UUID(evidence_id)
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if current_user.role_name != "super_admin" and item.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this evidence")

    item.name = name
    item.description = description
    item.evidence_type = evidence_type
    item.owner = owner
    item.collected_date = _parse_date(collected_date)
    item.valid_until = _parse_date(valid_until)
    item.status = evidence_status
    item.collection_method = collection_method
    item.audit_notes = audit_notes

    if file:
        _remove_upload(item.file_path)
        filename, file_size, file_path = _save_upload(file, "evidence_library", item.id)
        item.file_name = filename
        item.file_size = file_size
        item.file_path = file_path

    db.query(models.EvidenceLibraryFramework).filter(
        models.EvidenceLibraryFramework.evidence_id == item.id
    ).delete()
    db.query(models.EvidenceLibraryControl).filter(
        models.EvidenceLibraryControl.evidence_id == item.id
    ).delete()

    framework_id_list = _parse_json_list(framework_ids)
    for framework_id in framework_id_list:
        db.add(models.EvidenceLibraryFramework(
            evidence_id=item.id,
            framework_id=uuid.UUID(framework_id)
        ))

    control_id_list = _parse_json_list(control_ids)
    for control_id in control_id_list:
        db.add(models.EvidenceLibraryControl(
            evidence_id=item.id,
            control_id=uuid.UUID(control_id)
        ))

    db.commit()
    db.refresh(item)
    return _evidence_to_response(db, item)


@router.delete("/{evidence_id}")
def delete_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    item = db.query(models.EvidenceLibraryItem).filter(
        models.EvidenceLibraryItem.id == uuid.UUID(evidence_id)
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if current_user.role_name != "super_admin" and item.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this evidence")

    db.query(models.EvidenceLibraryFramework).filter(
        models.EvidenceLibraryFramework.evidence_id == item.id
    ).delete()
    db.query(models.EvidenceLibraryControl).filter(
        models.EvidenceLibraryControl.evidence_id == item.id
    ).delete()

    _remove_upload(item.file_path)
    db.delete(item)
    db.commit()
    return {"success": True}
