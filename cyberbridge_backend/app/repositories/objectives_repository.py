# objectives_repository.py
from sqlalchemy.orm import Session
import sqlalchemy as sa
import uuid
import os
import logging
from typing import List, Optional
from app.models import models
from app.dtos import schemas
from app.services import scope_validation_service

logger = logging.getLogger(__name__)


def _enrich_objective_with_scope_info(db: Session, objective_data: dict) -> dict:
    """Helper function to add scope information to objective data"""
    try:
        if objective_data.get('scope_id') and objective_data.get('scope_entity_id'):
            scope_info = scope_validation_service.get_scope_info(
                db,
                objective_data['scope_id'],
                objective_data['scope_entity_id']
            )
            if scope_info:
                objective_data['scope_name'] = scope_info.get('scope_name')
                objective_data['scope_display_name'] = scope_info.get('entity_name')
    except Exception as e:
        logger.error(f"Error enriching objective with scope info: {str(e)}")
    return objective_data

def _clone_objectives_for_scope(
    db: Session,
    chapter_id: uuid.UUID,
    scope_id: uuid.UUID,
    scope_entity_id: Optional[uuid.UUID]
) -> int:
    """Clone unscoped objectives for a chapter into a scoped set."""
    base_objectives = db.query(models.Objectives).filter(
        models.Objectives.chapter_id == chapter_id,
        models.Objectives.scope_id.is_(None),
        models.Objectives.scope_entity_id.is_(None)
    ).order_by(models.Objectives.subchapter, models.Objectives.id).all()

    if not base_objectives:
        return 0

    for base in base_objectives:
        new_objective = models.Objectives(
            title=base.title,
            subchapter=base.subchapter,
            chapter_id=base.chapter_id,
            requirement_description=base.requirement_description,
            objective_utilities=base.objective_utilities,
            compliance_status_id=base.compliance_status_id,
            scope_id=scope_id,
            scope_entity_id=scope_entity_id,
            applicable_operators=base.applicable_operators
        )
        db.add(new_objective)
        db.flush()

        policy_ids = db.query(models.PolicyObjectives.policy_id).filter(
            models.PolicyObjectives.objective_id == base.id
        ).all()
        for policy_id, in policy_ids:
            db.add(models.PolicyObjectives(
                policy_id=policy_id,
                objective_id=new_objective.id
            ))

    return len(base_objectives)

# Chapter CRUD operations
def get_chapter(db: Session, chapter_id: uuid.UUID):
    return db.query(models.Chapters).filter(models.Chapters.id == chapter_id).first()

def get_chapters(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Chapters).offset(skip).limit(limit).all()

def create_chapter(db: Session, chapter: dict):
    db_chapter = models.Chapters(
        title=chapter["title"],
        framework_id=uuid.UUID(chapter["framework_id"])
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter

def update_chapter(db: Session, chapter_id: uuid.UUID, chapter: dict):
    db_chapter = get_chapter(db, chapter_id)
    if db_chapter:
        db_chapter.title = chapter["title"]
        db_chapter.framework_id = uuid.UUID(chapter["framework_id"])
        db.commit()
        db.refresh(db_chapter)
    return db_chapter

def delete_chapter(db: Session, chapter_id: uuid.UUID):
    db_chapter = get_chapter(db, chapter_id)
    if db_chapter:
        # Get all objectives associated with this chapter
        objectives = db.query(models.Objectives).filter(models.Objectives.chapter_id == chapter_id).all()

        for objective in objectives:
            # First delete any policy_objectives relationships
            db.query(models.PolicyObjectives).filter(models.PolicyObjectives.objective_id == objective.id).delete()

        # Then delete all objectives associated with this chapter
        db.query(models.Objectives).filter(models.Objectives.chapter_id == chapter_id).delete()

        # Finally delete the chapter
        db.delete(db_chapter)
        db.commit()
    return db_chapter

# Objective CRUD operations
def get_objective(db: Session, objective_id: uuid.UUID):
    return db.query(models.Objectives).filter(models.Objectives.id == objective_id).first()

def get_objectives(db: Session, skip: int = 0, limit: int = 100, current_user: schemas.UserBase = None):
    try:
        # Base query with JOIN to get objectives with chapter names
        # Only return base (unscoped) objectives — scoped clones are internal to the checklist
        query = db.query(
            models.Objectives,
            models.Chapters.title.label('chapter_title')
        ).join(
            models.Chapters, models.Objectives.chapter_id == models.Chapters.id
        ).join(
            models.Framework, models.Chapters.framework_id == models.Framework.id
        ).filter(
            models.Objectives.scope_id.is_(None),
            models.Objectives.scope_entity_id.is_(None)
        )

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Framework.organisation_id == current_user.organisation_id)

        objectives_with_chapters = query.offset(skip).limit(limit).all()
        
        # Convert to list of objectives with chapter_name attribute
        objectives = []
        for obj_tuple in objectives_with_chapters:
            objective = obj_tuple[0]  # The Objectives object
            chapter_title = obj_tuple[1]  # The chapter title
            objective.chapter_name = chapter_title
            objectives.append(objective)
        
        return objectives
    except Exception as e:
        logger.error(f"Error getting objectives: {str(e)}")
        return []

def create_objective(db: Session, objective: dict):
    compliance_status_id = None
    if objective.get("compliance_status_id"):
        compliance_status_id = uuid.UUID(objective["compliance_status_id"])

    db_objective = models.Objectives(
        title=objective["title"],
        subchapter=objective["subchapter"],
        chapter_id=uuid.UUID(objective["chapter_id"]),
        requirement_description=objective["requirement_description"],
        objective_utilities=objective["objective_utilities"],
        compliance_status_id=compliance_status_id
    )
    db.add(db_objective)
    db.commit()
    db.refresh(db_objective)
    return db_objective

def update_objective(db: Session, objective_id: uuid.UUID, objective: dict):
    db_objective = get_objective(db, objective_id)
    if db_objective:
        compliance_status_id = None
        if objective.get("compliance_status_id"):
            compliance_status_id = uuid.UUID(objective["compliance_status_id"])

        db_objective.title = objective["title"]
        db_objective.subchapter = objective["subchapter"]
        db_objective.chapter_id = uuid.UUID(objective["chapter_id"])
        db_objective.requirement_description = objective["requirement_description"]
        db_objective.objective_utilities = objective["objective_utilities"]
        db_objective.compliance_status_id = compliance_status_id
        db.commit()
        db.refresh(db_objective)
    return db_objective

def delete_objective(db: Session, objective_id: uuid.UUID):
    db_objective = get_objective(db, objective_id)
    if db_objective:
        try:
            print(f"Starting deletion of objective: {objective_id}")

            # Clean up evidence file if one exists
            if db_objective.evidence_filepath:
                try:
                    base_path = os.environ.get("UPLOAD_PATH")
                    if not base_path:
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        base_path = os.path.join(project_root, "uploads")
                    disk_path = db_objective.evidence_filepath
                    if not os.path.isabs(disk_path):
                        disk_path = os.path.join(base_path, disk_path)
                    if os.path.exists(disk_path):
                        os.remove(disk_path)
                    parent_dir = os.path.dirname(disk_path)
                    if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                except Exception as file_err:
                    logger.error(f"Error cleaning up evidence file for objective {objective_id}: {str(file_err)}")

            # First delete any policy_objectives relationships
            policy_obj_deleted = db.query(models.PolicyObjectives).filter(
                models.PolicyObjectives.objective_id == objective_id
            ).delete(synchronize_session=False)
            if policy_obj_deleted > 0:
                print(f"Deleted {policy_obj_deleted} policy_objective associations")

            # Then delete the objective
            db.delete(db_objective)
            db.commit()
            print(f"Successfully deleted objective: {objective_id}")
        except Exception as e:
            print(f"Error deleting objective {objective_id}: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise e
    return db_objective

# Compliance Status CRUD operations
def get_compliance_statuses(db: Session):
    return db.query(models.ComplianceStatuses).all()

def get_compliance_status(db: Session, status_id: uuid.UUID):
    return db.query(models.ComplianceStatuses).filter(models.ComplianceStatuses.id == status_id).first()

# Objectives Checklist functionality
def get_chapters_with_objectives(
    db: Session,
    framework_id: uuid.UUID = None,
    current_user: schemas.UserBase = None,
    scope_name: str = None,
    scope_entity_id: uuid.UUID = None,
    operator_role: str = None
):
    """Get all chapters with their objectives and compliance statuses for the checklist.

    Args:
        db: Database session
        framework_id: Optional framework ID to filter by
        current_user: Current user for org-based filtering
        scope_name: Optional scope type name (e.g., 'Product', 'Organization')
        scope_entity_id: Optional scope entity ID (e.g., product_id, org_id)
        operator_role: Optional economic operator role (e.g., 'Manufacturer', 'Importer', 'Distributor')
    """

    if framework_id:
        # Filter by framework_id and ensure the framework belongs to the current user's organization
        if current_user and current_user.role_name != "super_admin":
            # First verify the framework belongs to the user's organization
            framework = db.query(models.Framework).filter(
                models.Framework.id == framework_id,
                models.Framework.organisation_id == current_user.organisation_id
            ).first()
            if not framework:
                return []  # Return empty list if framework doesn't belong to user's org

        chapters = db.query(models.Chapters).filter(models.Chapters.framework_id == framework_id).order_by(models.Chapters.id).all()
    else:
        # If no framework_id provided, get chapters from all frameworks of the user's organization
        if current_user and current_user.role_name != "super_admin":
            # Get all frameworks belonging to user's organization, then get their chapters
            user_framework_ids = db.query(models.Framework.id).filter(
                models.Framework.organisation_id == current_user.organisation_id
            ).all()
            framework_ids = [fw.id for fw in user_framework_ids]
            chapters = db.query(models.Chapters).filter(
                models.Chapters.framework_id.in_(framework_ids)
            ).order_by(models.Chapters.id).all() if framework_ids else []
        else:
            chapters = db.query(models.Chapters).order_by(models.Chapters.id).all()

    # Get scope_id if scope_name is provided
    scope_id = None
    if scope_name:
        scope = db.query(models.Scopes).filter(models.Scopes.scope_name == scope_name).first()
        if scope:
            scope_id = scope.id

    scoped_mode = False
    if scope_id and scope_name:
        if scope_name == 'Other' and scope_entity_id is None:
            scoped_mode = True
        elif scope_entity_id is not None:
            scoped_mode = True

    # If scoped mode is requested, ensure scoped objectives exist per chapter
    if scoped_mode:
        created_count = 0
        for chapter in chapters:
            existing = db.query(models.Objectives.id).filter(
                models.Objectives.chapter_id == chapter.id,
                models.Objectives.scope_id == scope_id,
                models.Objectives.scope_entity_id == scope_entity_id
            ).first()
            if not existing:
                created_count += _clone_objectives_for_scope(
                    db,
                    chapter.id,
                    scope_id,
                    scope_entity_id
                )
        if created_count > 0:
            db.commit()

    asset_policy_ids = None
    if scoped_mode and scope_name in ('Product', 'Asset') and scope_entity_id is not None:
        asset_policy_rows = db.query(models.ControlPolicy.policy_id).join(
            models.ControlRisk, models.ControlPolicy.control_id == models.ControlRisk.control_id
        ).join(
            models.AssetRisk, models.ControlRisk.risk_id == models.AssetRisk.risk_id
        ).filter(
            models.AssetRisk.asset_id == scope_entity_id
        ).distinct().all()
        asset_policy_ids = {policy_id for (policy_id,) in asset_policy_rows}

    # Pre-load policy status lookup
    status_lookup = {}
    for ps in db.query(models.PolicyStatuses).all():
        status_lookup[ps.id] = ps.status

    # For each chapter, get objectives with compliance status details
    result = []
    for chapter in chapters:
        chapter_data = {
            "id": chapter.id,
            "title": chapter.title,
            "framework_id": chapter.framework_id,
            "created_at": chapter.created_at,
            "updated_at": chapter.updated_at,
            "objectives": []
        }

        # Build objectives query with optional scope filtering
        objectives_query = db.query(models.Objectives).filter(
            models.Objectives.chapter_id == chapter.id
        )

        # Apply scope filtering
        if scoped_mode:
            objectives_query = objectives_query.filter(
                models.Objectives.scope_id == scope_id,
                models.Objectives.scope_entity_id == scope_entity_id
            )
        elif scope_name or scope_entity_id:
            # Scope selected but not fully specified (e.g., scope type without entity)
            objectives_query = objectives_query.filter(models.Objectives.id.is_(None))
        else:
            objectives_query = objectives_query.filter(
                models.Objectives.scope_id.is_(None),
                models.Objectives.scope_entity_id.is_(None)
            )

        # Apply economic operator role filtering
        if operator_role:
            objectives_query = objectives_query.filter(
                sa.or_(
                    models.Objectives.applicable_operators.is_(None),
                    models.Objectives.applicable_operators.contains(operator_role)
                )
            )

        objectives = objectives_query.order_by(models.Objectives.subchapter, models.Objectives.id).all()

        for objective in objectives:
            compliance_status_name = None
            if objective.compliance_status_id:
                compliance_status = db.query(models.ComplianceStatuses).filter(
                    models.ComplianceStatuses.id == objective.compliance_status_id
                ).first()
                if compliance_status:
                    compliance_status_name = compliance_status.status_name

            # Get policies linked to this objective
            policy_rows = db.query(models.Policies.id, models.Policies.title, models.Policies.status_id).join(
                models.PolicyObjectives,
                models.Policies.id == models.PolicyObjectives.policy_id
            ).filter(
                models.PolicyObjectives.objective_id == objective.id
            ).all()
            policy_list = [
                {"id": str(policy_id), "title": title, "status_id": str(status_id) if status_id else None, "status": status_lookup.get(status_id, "")}
                for policy_id, title, status_id in policy_rows
                if asset_policy_ids is None or policy_id in asset_policy_ids
            ]

            if scoped_mode:
                # For all scoped modes, also include policies from the base objective
                base_objective_ids = db.query(models.Objectives.id).filter(
                    models.Objectives.chapter_id == objective.chapter_id,
                    models.Objectives.title == objective.title,
                    models.Objectives.subchapter == objective.subchapter,
                    models.Objectives.scope_id.is_(None),
                    models.Objectives.scope_entity_id.is_(None)
                ).all()
                if base_objective_ids:
                    base_policy_rows = db.query(models.Policies.id, models.Policies.title, models.Policies.status_id).join(
                        models.PolicyObjectives,
                        models.Policies.id == models.PolicyObjectives.policy_id
                    ).filter(
                        models.PolicyObjectives.objective_id.in_([obj_id for (obj_id,) in base_objective_ids])
                    ).all()
                    policy_list.extend([
                        {"id": str(policy_id), "title": title, "status_id": str(status_id) if status_id else None, "status": status_lookup.get(status_id, "")}
                        for policy_id, title, status_id in base_policy_rows
                        if asset_policy_ids is None or policy_id in asset_policy_ids
                    ])

            # Deduplicate by policy id while preserving order
            seen = set()
            policy_list = [p for p in policy_list if not (p["id"] in seen or seen.add(p["id"]))]

            objective_data = {
                "id": objective.id,
                "title": objective.title,
                "subchapter": objective.subchapter,
                "chapter_id": objective.chapter_id,
                "requirement_description": objective.requirement_description,
                "objective_utilities": objective.objective_utilities,
                "compliance_status_id": objective.compliance_status_id,
                "compliance_status": compliance_status_name,
                "policies": policy_list,
                "scope_id": objective.scope_id,
                "scope_entity_id": objective.scope_entity_id,
                "applicable_operators": objective.applicable_operators,
                "evidence_filename": objective.evidence_filename,
                "evidence_file_type": objective.evidence_file_type,
                "evidence_file_size": objective.evidence_file_size,
                "created_at": objective.created_at,
                "updated_at": objective.updated_at
            }

            # Enrich with scope display info
            objective_data = _enrich_objective_with_scope_info(db, objective_data)

            chapter_data["objectives"].append(objective_data)

        result.append(chapter_data)

    return result

def get_objectives_by_framework_ids(db: Session, framework_ids: List[uuid.UUID], current_user: schemas.UserBase = None):
    """Get objectives for specific framework IDs"""
    try:
        if not framework_ids:
            return []
        
        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            # Verify all frameworks belong to the user's organization
            user_frameworks = db.query(models.Framework.id).filter(
                models.Framework.id.in_(framework_ids),
                models.Framework.organisation_id == current_user.organisation_id
            ).all()
            verified_framework_ids = [fw.id for fw in user_frameworks]
        else:
            verified_framework_ids = framework_ids
        
        if not verified_framework_ids:
            return []
        
        # Get chapters for the verified frameworks
        chapters = db.query(models.Chapters).filter(
            models.Chapters.framework_id.in_(verified_framework_ids)
        ).all()
        
        if not chapters:
            return []
        
        chapter_ids = [chapter.id for chapter in chapters]
        
        # Get objectives with chapter names using JOIN
        objectives_with_chapters = db.query(
            models.Objectives,
            models.Chapters.title.label('chapter_title')
        ).join(
            models.Chapters, models.Objectives.chapter_id == models.Chapters.id
        ).filter(
            models.Objectives.chapter_id.in_(chapter_ids)
        ).all()
        
        # Convert to list of objectives with chapter_name attribute
        objectives = []
        for obj_tuple in objectives_with_chapters:
            objective = obj_tuple[0]  # The Objectives object
            chapter_title = obj_tuple[1]  # The chapter title
            objective.chapter_name = chapter_title
            objectives.append(objective)
        
        return objectives
    except Exception as e:
        logger.error(f"Error getting objectives by framework IDs: {str(e)}")
        return []
