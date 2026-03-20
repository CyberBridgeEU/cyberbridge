# routers/policies_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
import os
import mammoth
from ..utils.html_converter import convert_html_to_plain_text

from ..repositories import policy_repository, history_repository
from ..models import models
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user

router = APIRouter(prefix="/policies", tags=["policies"], responses={404: {"description": "Not found"}})

@router.get("")
def get_all_policies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        policies = policy_repository.get_policies(db, current_user, skip=skip, limit=limit)

        # Convert to dictionaries to include dynamically added attributes
        result = []
        for policy in policies:
            policy_dict = {
                'id': policy.id,
                'title': policy.title,
                'policy_code': policy.policy_code,
                'owner': policy.owner,
                'status_id': policy.status_id,
                'body': policy.body,
                'company_name': policy.company_name,
                'organisation_id': policy.organisation_id,
                'created_at': policy.created_at,
                'status': getattr(policy, 'status', None),
                'organisation_name': getattr(policy, 'organisation_name', None),
                'frameworks': getattr(policy, 'frameworks', []),  # Framework IDs for filtering
                'framework_names': getattr(policy, 'framework_names', []),  # Framework names for display
                'objectives': getattr(policy, 'objectives', []),
                'chapters': getattr(policy, 'chapters', [])
            }
            # Debug log to see what we're sending to frontend
            print(f"DEBUG: Controller sending policy {policy.id} with objectives: {policy_dict['objectives']} and chapters: {policy_dict['chapters']}")
            result.append(policy_dict)

        print(f"DEBUG: Controller returning {len(result)} policies")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching policies: {str(e)}"
        )

@router.get("/statuses", response_model=List[schemas.PolicyStatusResponse])
def get_all_policy_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        statuses = policy_repository.get_policy_statuses(db, skip=skip, limit=limit)
        return statuses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching policy statuses: {str(e)}"
        )

@router.get("/frameworks", response_model=List[schemas.PolicyFrameworkResponse])
def get_all_policy_frameworks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        policy_frameworks = policy_repository.get_policy_frameworks(db, skip=skip, limit=limit)
        return policy_frameworks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching policy frameworks: {str(e)}"
        )

@router.get("/objectives", response_model=List[schemas.PolicyObjectiveResponse])
def get_all_policy_objectives(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        policy_objectives = policy_repository.get_policy_objectives(db, skip=skip, limit=limit)
        return policy_objectives
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching policy objectives: {str(e)}"
        )

@router.post("", response_model=schemas.PolicyResponse)
def create_policy(policy: schemas.PolicyCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Create the policy
        new_policy = policy_repository.create_policy(db=db, policy=policy.model_dump(), current_user=current_user)

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="policies",
            record_id=str(new_policy.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "title": new_policy.title,
                "policy_code": new_policy.policy_code,
                "owner": new_policy.owner,
                "status_id": str(new_policy.status_id) if new_policy.status_id else None,
                "body": new_policy.body[:100] + "..." if new_policy.body and len(new_policy.body) > 100 else new_policy.body
            }
        )

        return new_policy
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy code already exists in your organization."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the policy: {str(e)}"
        )

@router.put("/{policy_id}", response_model=schemas.PolicyResponse)
def update_policy(policy_id: str, policy: schemas.PolicyUpdate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the old policy data first
        old_policy = policy_repository.get_policy(db=db, policy_id=uuid.UUID(policy_id), current_user=current_user)
        if not old_policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        policy_data = policy.model_dump()

        # Track changes
        changes = {}
        for key, new_value in policy_data.items():
            if new_value is not None:
                old_value = getattr(old_policy, key, None)
                if old_value != new_value:
                    # For content field, truncate for history
                    if key == "content":
                        old_val_display = old_value[:100] + "..." if old_value and len(old_value) > 100 else old_value
                        new_val_display = new_value[:100] + "..." if new_value and len(new_value) > 100 else new_value
                        changes[key] = {"old": old_val_display, "new": new_val_display}
                    else:
                        changes[key] = {
                            "old": str(old_value) if old_value else None,
                            "new": str(new_value) if new_value else None
                        }

        # Update the policy
        updated_policy = policy_repository.update_policy(db=db, policy_id=uuid.UUID(policy_id), policy=policy_data, current_user=current_user)

        # Track the update in history if there were changes
        if changes:
            history_repository.track_update(
                db=db,
                table_name="policies",
                record_id=policy_id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes=changes
            )

        # Auto-sync linked objectives compliance when policy status changes
        if "status_id" in changes:
            # Detect if this policy lost its Approved status
            approved_status = db.query(models.PolicyStatuses).filter(models.PolicyStatuses.status == "Approved").first()
            old_was_approved = approved_status and changes["status_id"]["old"] == str(approved_status.id)
            new_is_approved = approved_status and changes["status_id"]["new"] == str(approved_status.id)
            lost_approval = old_was_approved and not new_is_approved

            updated_objectives = policy_repository.sync_objectives_for_policy(db, uuid.UUID(policy_id), policy_lost_approval=lost_approval)
            for obj_update in updated_objectives:
                history_repository.track_update(
                    db=db,
                    table_name="objectives",
                    record_id=obj_update["objective_id"],
                    user_id=current_user.id,
                    user_email=current_user.email,
                    organisation_id=current_user.organisation_id,
                    changes={"compliance_status": {"old": None, "new": f"{obj_update['new_status']} (auto: policy status changed)"}}
                )

        return updated_policy
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
            detail="Policy code already exists in your organization."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the policy: {str(e)}"
        )

@router.patch("/{policy_id}/status")
def update_policy_status(policy_id: str, patch: schemas.PolicyStatusPatch, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        old_policy = policy_repository.get_policy(db=db, policy_id=uuid.UUID(policy_id), current_user=current_user)
        if not old_policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        old_status_id = str(old_policy.status_id) if old_policy.status_id else None

        updated_policy = policy_repository.update_policy_status(
            db=db, policy_id=uuid.UUID(policy_id), status_id=patch.status_id, current_user=current_user
        )

        if old_status_id != patch.status_id:
            history_repository.track_update(
                db=db,
                table_name="policies",
                record_id=policy_id,
                user_id=current_user.id,
                user_email=current_user.email,
                organisation_id=current_user.organisation_id,
                changes={"status_id": {"old": old_status_id, "new": patch.status_id}}
            )

            # Detect if this policy lost its Approved status
            approved_status = db.query(models.PolicyStatuses).filter(models.PolicyStatuses.status == "Approved").first()
            old_was_approved = approved_status and old_status_id == str(approved_status.id)
            new_is_approved = approved_status and patch.status_id == str(approved_status.id)
            lost_approval = old_was_approved and not new_is_approved

            updated_objectives = policy_repository.sync_objectives_for_policy(db, uuid.UUID(policy_id), policy_lost_approval=lost_approval)
            for obj_update in updated_objectives:
                history_repository.track_update(
                    db=db,
                    table_name="objectives",
                    record_id=obj_update["objective_id"],
                    user_id=current_user.id,
                    user_email=current_user.email,
                    organisation_id=current_user.organisation_id,
                    changes={"compliance_status": {"old": None, "new": f"{obj_update['new_status']} (auto: policy status changed)"}}
                )

        return {"message": "Policy status updated successfully", "id": str(updated_policy.id), "status_id": str(updated_policy.status_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating policy status: {str(e)}"
        )

@router.delete("/{policy_id}")
def delete_policy(policy_id: str, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Get the policy data before deletion
        old_policy = policy_repository.get_policy(db=db, policy_id=uuid.UUID(policy_id), current_user=current_user)
        if not old_policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        # Track the deletion in history
        history_repository.track_delete(
            db=db,
            table_name="policies",
            record_id=policy_id,
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={
                "title": old_policy.title,
                "policy_code": old_policy.policy_code,
                "owner": old_policy.owner,
                "status_id": str(old_policy.status_id) if old_policy.status_id else None,
                "body": old_policy.body[:100] + "..." if old_policy.body and len(old_policy.body) > 100 else old_policy.body
            }
        )

        # If the policy was Approved, sync linked objectives before deletion
        # (must happen before delete, since delete removes the PolicyObjectives links)
        approved_status = db.query(models.PolicyStatuses).filter(models.PolicyStatuses.status == "Approved").first()
        if approved_status and old_policy.status_id == approved_status.id:
            updated_objectives = policy_repository.sync_objectives_for_policy(db, uuid.UUID(policy_id), policy_lost_approval=True)
            for obj_update in updated_objectives:
                history_repository.track_update(
                    db=db,
                    table_name="objectives",
                    record_id=obj_update["objective_id"],
                    user_id=current_user.id,
                    user_email=current_user.email,
                    organisation_id=current_user.organisation_id,
                    changes={"compliance_status": {"old": None, "new": f"{obj_update['new_status']} (auto: approved policy deleted)"}}
                )

        # Delete the policy
        policy = policy_repository.delete_policy(db=db, policy_id=uuid.UUID(policy_id), current_user=current_user)
        if policy is None:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {"message": "Policy deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        # Handle business rule violations (like policy assigned to answers)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the policy: {str(e)}"
        )

@router.post("/add_framework", response_model=schemas.PolicyFrameworkResponse)
def add_framework_to_policy(framework: schemas.PolicyFrameworkCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return policy_repository.add_framework_to_policy(
            db=db, 
            policy_id=uuid.UUID(framework.policy_id), 
            framework_id=uuid.UUID(framework.framework_id)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while adding framework to policy: {str(e)}"
        )

@router.post("/remove_framework")
def remove_framework_from_policy(framework: schemas.PolicyFrameworkCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = policy_repository.remove_framework_from_policy(
            db=db, 
            policy_id=uuid.UUID(framework.policy_id), 
            framework_id=uuid.UUID(framework.framework_id)
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Policy-Framework relationship not found")
        return {"message": "Framework removed from policy successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing framework from policy: {str(e)}"
        )

@router.post("/add_objective", response_model=schemas.PolicyObjectiveResponse)
def add_objective_to_policy(objective: schemas.PolicyObjectiveCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = policy_repository.add_objective_to_policy(
            db=db,
            policy_id=uuid.UUID(objective.policy_id),
            objective_id=uuid.UUID(objective.objective_id),
            order=objective.order
        )
        # Sync compliance status in case the policy is already Approved
        policy_repository.sync_objectives_for_policy(db, uuid.UUID(objective.policy_id))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while adding objective to policy: {str(e)}"
        )

@router.post("/update_objective_order", response_model=schemas.PolicyObjectiveResponse)
def update_objective_order(objective: schemas.PolicyObjectiveCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        return policy_repository.update_objective_order(
            db=db, 
            policy_id=uuid.UUID(objective.policy_id), 
            objective_id=uuid.UUID(objective.objective_id),
            order=objective.order
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating objective order: {str(e)}"
        )

@router.post("/remove_objective")
def remove_objective_from_policy(objective: schemas.PolicyObjectiveBase, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        result = policy_repository.remove_objective_from_policy(
            db=db, 
            policy_id=uuid.UUID(objective.policy_id), 
            objective_id=uuid.UUID(objective.objective_id)
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Policy-Objective relationship not found")
        return {"message": "Objective removed from policy successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing objective from policy: {str(e)}"
        )

@router.get("/templates", response_model=List[schemas.PolicyTemplateResponse])
def get_policy_templates(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    """Get all policy templates from the policy_templates table"""
    try:
        from ..models import models
        templates = db.query(models.PolicyTemplate).order_by(models.PolicyTemplate.policy_code).all()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching policy templates: {str(e)}"
        )


@router.post("/templates/import", response_model=schemas.PolicyTemplateImportResponse)
def import_policy_templates(
    request: schemas.PolicyTemplateImportRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Import selected policy templates as new policies"""
    try:
        from ..models import models

        # Get templates by IDs
        template_ids = [uuid.UUID(tid) for tid in request.template_ids]
        templates = db.query(models.PolicyTemplate).filter(
            models.PolicyTemplate.id.in_(template_ids)
        ).all()

        if not templates:
            raise HTTPException(status_code=404, detail="No templates found for the given IDs")

        # Get existing policy codes for this org to avoid duplicates
        existing_codes = {
            code for (code,) in db.query(models.Policies.policy_code).filter(
                models.Policies.organisation_id == current_user.organisation_id,
                models.Policies.policy_code.isnot(None)
            ).all()
        }

        # Get "Draft" status ID
        draft_status = db.query(models.PolicyStatuses).filter(
            models.PolicyStatuses.status == "Draft"
        ).first()
        if not draft_status:
            raise HTTPException(status_code=500, detail="Draft policy status not found")

        from ..repositories.policy_repository import get_next_policy_code

        imported_codes = []
        skipped = 0
        errors = []

        for template in templates:
            # Determine policy code: use template's code, or auto-generate
            policy_code = template.policy_code
            if not policy_code:
                policy_code = get_next_policy_code(db, current_user.organisation_id)

            # Skip if policy code already exists in this org
            if policy_code in existing_codes:
                skipped += 1
                errors.append(f"{policy_code} already exists — skipped")
                continue

            # Convert docx content to plain text if available
            body_text = ""
            if template.content_docx:
                import io
                try:
                    docx_stream = io.BytesIO(template.content_docx)
                    result = mammoth.convert_to_html(docx_stream)
                    body_text = convert_html_to_plain_text(result.value)
                except Exception as conv_err:
                    errors.append(f"{policy_code}: docx conversion failed — {str(conv_err)}")

            db_policy = models.Policies(
                title=template.title or template.filename.replace('.docx', '').replace('_', ' ').title(),
                policy_code=policy_code,
                owner=None,
                status_id=draft_status.id,
                body=body_text,
                company_name=None,
                organisation_id=current_user.organisation_id,
                created_by=current_user.id,
                last_updated_by=current_user.id
            )
            db.add(db_policy)
            imported_codes.append(policy_code)
            existing_codes.add(policy_code)  # Track within same batch

        db.commit()

        return schemas.PolicyTemplateImportResponse(
            success=True,
            imported_count=len(imported_codes),
            skipped_count=skipped,
            message=f"Imported {len(imported_codes)} template(s), skipped {skipped} duplicate(s)",
            imported_policy_codes=imported_codes,
            errors=errors
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while importing templates: {str(e)}"
        )


@router.get("/files")
def get_policy_files(current_user: schemas.UserBase = Depends(get_current_active_user)):
    """Get list of all .docx files in the policies_files directory"""
    try:
        policies_dir = os.path.join(os.path.dirname(__file__), "..", "policies_files")
        policies_dir = os.path.abspath(policies_dir)
        
        if not os.path.exists(policies_dir):
            return {"files": []}
        
        files = []
        for filename in os.listdir(policies_dir):
            if filename.lower().endswith('.docx'):
                file_path = os.path.join(policies_dir, filename)
                file_stats = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "modified": file_stats.st_mtime
                })
        
        # Sort by filename
        files.sort(key=lambda x: x['filename'])
        return {"files": files}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while listing policy files: {str(e)}"
        )

@router.get("/files/{filename}/preview")
def get_policy_file_preview(filename: str, current_user: schemas.UserBase = Depends(get_current_active_user)):
    """Convert a .docx file to HTML for preview"""
    try:
        policies_dir = os.path.join(os.path.dirname(__file__), "..", "policies_files")
        policies_dir = os.path.abspath(policies_dir)
        file_path = os.path.join(policies_dir, filename)
        
        # Security check - ensure file is within policies_files directory
        if not file_path.startswith(policies_dir):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        if not os.path.exists(file_path) or not filename.lower().endswith('.docx'):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Convert docx to HTML using mammoth
        with open(file_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html_content = result.value
            messages = result.messages
        
        return {
            "filename": filename,
            "html_content": html_content,
            "conversion_messages": [str(msg) for msg in messages]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while previewing policy file: {str(e)}"
        )


# ===========================
# Policy Connection Query Endpoints
# ===========================

@router.get("/{policy_id}/objectives")
def get_objectives_for_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all objectives addressed by a policy"""
    try:
        objectives = policy_repository.get_objectives_for_policy(db, uuid.UUID(policy_id), current_user)
        # Convert to dict format for response
        return [
            {
                "id": str(obj.id),
                "title": obj.title,
                "subchapter": obj.subchapter,
                "chapter_title": getattr(obj, "chapter_title", None),
            }
            for obj in objectives
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching objectives for policy: {str(e)}"
        )


@router.get("/{policy_id}/controls")
def get_controls_for_policy(
    policy_id: str,
    framework_id: Optional[str] = Query(None, description="Filter by framework ID"),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all controls governed by a policy"""
    try:
        fw_uuid = uuid.UUID(framework_id) if framework_id else None
        controls = policy_repository.get_controls_for_policy(db, uuid.UUID(policy_id), current_user, framework_id=fw_uuid)
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
            detail=f"An error occurred while fetching controls for policy: {str(e)}"
        )
