# policy_repository.py
from sqlalchemy.orm import Session
import uuid
from app.models import models
from app.dtos import schemas
from sqlalchemy.orm import joinedload

# Policy CRUD operations
import re

def get_next_policy_code(db: Session, organisation_id):
    """Generate next POL-N code for the given organisation."""
    existing_codes = db.query(models.Policies.policy_code).filter(
        models.Policies.organisation_id == organisation_id,
        models.Policies.policy_code.isnot(None)
    ).all()

    max_n = 0
    for (code,) in existing_codes:
        match = re.match(r'^POL-(\d+)$', code or '')
        if match:
            max_n = max(max_n, int(match.group(1)))

    return f"POL-{max_n + 1}"

def _normalize_policy_code(policy_code: str | None) -> str | None:
    if policy_code is None:
        return None
    normalized = policy_code.strip()
    return normalized if normalized else None

def _policy_code_exists(
    db: Session,
    organisation_id,
    policy_code: str,
    exclude_policy_id: uuid.UUID | None = None
) -> bool:
    query = db.query(models.Policies.id).filter(
        models.Policies.organisation_id == organisation_id,
        models.Policies.policy_code == policy_code
    )
    if exclude_policy_id:
        query = query.filter(models.Policies.id != exclude_policy_id)
    return query.first() is not None

def _is_reserved_template_policy_code(db: Session, policy_code: str) -> bool:
    if not policy_code:
        return False
    return db.query(models.PolicyTemplate.id).filter(
        models.PolicyTemplate.policy_code == policy_code
    ).first() is not None


def get_policy(db: Session, policy_id: uuid.UUID, current_user: schemas.UserBase = None):
    query = db.query(models.Policies).filter(models.Policies.id == policy_id)
    
    # Filter by organization for non-super_admin users
    if current_user and current_user.role_name != "super_admin":
        query = query.filter(models.Policies.organisation_id == current_user.organisation_id)
    
    return query.first()

def get_policies(db: Session, current_user: schemas.UserBase = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Policies)
    
    # Filter by organization for non-super_admin users
    if current_user and current_user.role_name != "super_admin":
        query = query.filter(models.Policies.organisation_id == current_user.organisation_id)
    
    policies = query.offset(skip).limit(limit).all()

    # Enhance policies with related information
    for policy in policies:
        # Get policy status
        status = db.query(models.PolicyStatuses).filter(models.PolicyStatuses.id == policy.status_id).first()
        if status:
            policy.status = status.status

        # Get organization name
        organization = db.query(models.Organisations).filter(models.Organisations.id == policy.organisation_id).first()
        if organization:
            policy.organisation_name = organization.name

        # Get last updated by user email
        if policy.last_updated_by:
            last_updated_user = db.query(models.User).filter(models.User.id == policy.last_updated_by).first()
            if last_updated_user:
                policy.last_updated_by_email = last_updated_user.email
            else:
                policy.last_updated_by_email = None
        else:
            policy.last_updated_by_email = None

        # Get related frameworks
        policy_frameworks = db.query(models.PolicyFrameworks).filter(
            models.PolicyFrameworks.policy_id == policy.id
        ).all()

        framework_ids = [pf.framework_id for pf in policy_frameworks]
        frameworks = db.query(models.Framework).filter(
            models.Framework.id.in_(framework_ids)
        ).all()

        # Store both framework IDs and names for frontend filtering and display
        policy.frameworks = [str(framework.id) for framework in frameworks]
        policy.framework_names = [framework.name for framework in frameworks]

        # Get related objectives with chapter information
        print(f"DEBUG: Looking for policy objectives for policy ID: {policy.id}")
        policy_objectives = db.query(models.PolicyObjectives).filter(
            models.PolicyObjectives.policy_id == policy.id
        ).all()
        print(f"DEBUG: Found {len(policy_objectives)} policy objectives")

        objective_ids = [po.objective_id for po in policy_objectives]
        print(f"DEBUG: Extracted objective IDs: {objective_ids}")

        if objective_ids:
            # Get objectives with their chapter information using JOIN
            objectives_with_chapters = db.query(
                models.Objectives,
                models.Chapters.title.label('chapter_title')
            ).join(
                models.Chapters, models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Objectives.id.in_(objective_ids)
            ).all()

            print(f"DEBUG: Found objectives_with_chapters: {len(objectives_with_chapters)}")
            policy.objectives = [obj_tuple[0].title for obj_tuple in objectives_with_chapters]
            policy.chapters = list(set([obj_tuple[1] for obj_tuple in objectives_with_chapters if obj_tuple[1]]))
            print(f"DEBUG: Policy {policy.id} objectives: {policy.objectives}")
            print(f"DEBUG: Policy {policy.id} chapters: {policy.chapters}")
        else:
            policy.objectives = []
            policy.chapters = []

    return policies

def create_policy(db: Session, policy: dict, current_user: schemas.UserBase = None):
    # Handle company name replacement in policy body
    policy_body = policy.get("body", "")
    if policy_body and policy.get("company_name"):
        policy_body = policy_body.replace("p_company_name", policy["company_name"])

    print(f"DEBUG: Creating policy with data: {policy}")

    policy_code = _normalize_policy_code(policy.get("policy_code"))
    if not policy_code:
        raise ValueError("Policy code is required")

    organisation_id = current_user.organisation_id if current_user else None

    # Reserve template codes for policies imported from the library
    if _is_reserved_template_policy_code(db, policy_code):
        raise ValueError(
            f"Policy code '{policy_code}' is reserved for policy templates. Please use a unique custom code."
        )

    if organisation_id and _policy_code_exists(db, organisation_id, policy_code):
        raise ValueError(f"Policy code '{policy_code}' already exists in your organization.")

    db_policy = models.Policies(
        title=policy["title"],
        policy_code=policy_code,
        owner=policy["owner"],
        status_id=uuid.UUID(policy["status_id"]),
        body=policy_body,
        company_name=policy.get("company_name"),
        organisation_id=current_user.organisation_id if current_user else None,
        created_by=current_user.id if current_user else None,
        last_updated_by=current_user.id if current_user else None
    )
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)

    # Handle framework relationships if provided
    if "framework_ids" in policy and policy["framework_ids"]:
        for framework_id in policy["framework_ids"]:
            try:
                add_framework_to_policy(db, db_policy.id, uuid.UUID(framework_id))
            except ValueError as e:
                # If cross-organization assignment is detected, rollback and raise error
                db.rollback()
                raise ValueError(f"Cannot assign framework {framework_id}: {str(e)}")

    # Handle objective relationships if provided
    if "objective_ids" in policy and policy["objective_ids"]:
        for obj in policy["objective_ids"]:
            add_objective_to_policy(db, db_policy.id, uuid.UUID(obj["id"]), obj["order"])

    return db_policy

def update_policy(db: Session, policy_id: uuid.UUID, policy: dict, current_user: schemas.UserBase = None):
    db_policy = get_policy(db, policy_id, current_user)
    if db_policy:
        # Handle company name replacement in policy body
        policy_body = policy.get("body", "")
        if policy_body and policy.get("company_name"):
            policy_body = policy_body.replace("p_company_name", policy["company_name"])

        new_policy_code = _normalize_policy_code(policy.get("policy_code"))
        if not new_policy_code:
            raise ValueError("Policy code is required")

        current_policy_code = _normalize_policy_code(db_policy.policy_code)
        if new_policy_code != current_policy_code and _is_reserved_template_policy_code(db, new_policy_code):
            raise ValueError(
                f"Policy code '{new_policy_code}' is reserved for policy templates. Please use a unique custom code."
            )

        if _policy_code_exists(
            db,
            db_policy.organisation_id,
            new_policy_code,
            exclude_policy_id=policy_id
        ):
            raise ValueError(f"Policy code '{new_policy_code}' already exists in your organization.")

        db_policy.title = policy["title"]
        db_policy.policy_code = new_policy_code
        db_policy.owner = policy["owner"]
        db_policy.status_id = uuid.UUID(policy["status_id"])
        db_policy.body = policy_body
        db_policy.company_name = policy.get("company_name")
        db_policy.last_updated_by = current_user.id if current_user else None
        db.commit()
        db.refresh(db_policy)

        # Handle framework relationships if provided
        if "framework_ids" in policy and policy["framework_ids"] is not None:
            # Remove existing relationships
            db.query(models.PolicyFrameworks).filter(models.PolicyFrameworks.policy_id == policy_id).delete()
            db.commit()

            # Add new relationships
            for framework_id in policy["framework_ids"]:
                try:
                    add_framework_to_policy(db, policy_id, uuid.UUID(framework_id))
                except ValueError as e:
                    # If cross-organization assignment is detected, rollback and raise error
                    db.rollback()
                    raise ValueError(f"Cannot assign framework {framework_id}: {str(e)}")

        # Handle objective relationships if provided
        if "objective_ids" in policy and policy["objective_ids"] is not None:
            # Remove existing relationships
            db.query(models.PolicyObjectives).filter(models.PolicyObjectives.policy_id == policy_id).delete()
            db.commit()

            # Add new relationships
            for obj in policy["objective_ids"]:
                add_objective_to_policy(db, policy_id, uuid.UUID(obj["id"]), obj["order"])

    return db_policy

def update_policy_status(db: Session, policy_id: uuid.UUID, status_id: str, current_user: schemas.UserBase = None):
    db_policy = get_policy(db, policy_id, current_user)
    if db_policy:
        db_policy.status_id = uuid.UUID(status_id)
        db_policy.last_updated_by = current_user.id if current_user else None
        db.commit()
        db.refresh(db_policy)
    return db_policy

def delete_policy(db: Session, policy_id: uuid.UUID, current_user: schemas.UserBase = None):
    # First get the policy to ensure it belongs to the user's organization
    db_policy = get_policy(db, policy_id, current_user)
    if not db_policy:
        return None

    # Check ownership permissions for org_user
    if current_user and current_user.role_name == "org_user":
        if db_policy.created_by != current_user.id:
            raise ValueError("org_user can only delete their own policies")

    # Step 1: Check if policy is assigned to any assessment answers
    assigned_answers_count = db.query(models.Answer).filter(models.Answer.policy_id == policy_id).count()
    if assigned_answers_count > 0:
        raise ValueError(f"Deletion failed because there are {assigned_answers_count} answers that use this policy.")

    # Step 2: Delete related records in policy_frameworks and policy_objectives
    db.query(models.PolicyFrameworks).filter(models.PolicyFrameworks.policy_id == policy_id).delete()
    db.query(models.PolicyObjectives).filter(models.PolicyObjectives.policy_id == policy_id).delete()

    # Step 3: Delete the policy
    db.delete(db_policy)
    db.commit()
    return db_policy

# Policy Status CRUD operations
def get_policy_status(db: Session, status_id: uuid.UUID):
    return db.query(models.PolicyStatuses).filter(models.PolicyStatuses.id == status_id).first()

def get_policy_statuses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PolicyStatuses).offset(skip).limit(limit).all()

# Policy Framework relationship operations
def get_policy_frameworks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PolicyFrameworks).offset(skip).limit(limit).all()

def add_framework_to_policy(db: Session, policy_id: uuid.UUID, framework_id: uuid.UUID):
    # Get policy and framework to validate they belong to the same organization
    policy = db.query(models.Policies).filter(models.Policies.id == policy_id).first()
    framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()

    if not policy:
        raise ValueError("Policy not found")
    if not framework:
        raise ValueError("Framework not found")

    # Prevent cross-organization assignments
    if policy.organisation_id != framework.organisation_id:
        raise ValueError(f"Cross-organization assignment not allowed: Policy belongs to organization {policy.organisation_id} but Framework belongs to organization {framework.organisation_id}")

    db_policy_framework = models.PolicyFrameworks(
        policy_id=policy_id,
        framework_id=framework_id
    )
    db.add(db_policy_framework)
    db.commit()
    return db_policy_framework

def remove_framework_from_policy(db: Session, policy_id: uuid.UUID, framework_id: uuid.UUID):
    db_policy_framework = db.query(models.PolicyFrameworks).filter(
        models.PolicyFrameworks.policy_id == policy_id,
        models.PolicyFrameworks.framework_id == framework_id
    ).first()

    if db_policy_framework:
        db.delete(db_policy_framework)
        db.commit()
    return db_policy_framework

# Policy Objective relationship operations
def get_policy_objectives(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PolicyObjectives).offset(skip).limit(limit).all()

def add_objective_to_policy(db: Session, policy_id: uuid.UUID, objective_id: uuid.UUID, order: int):
    db_policy_objective = models.PolicyObjectives(
        policy_id=policy_id,
        objective_id=objective_id,
        order=order
    )
    db.add(db_policy_objective)
    db.commit()
    db.refresh(db_policy_objective)

    # Ensure policy is linked to the objective's framework
    objective = db.query(models.Objectives).filter(models.Objectives.id == objective_id).first()
    if objective:
        chapter = db.query(models.Chapters).filter(models.Chapters.id == objective.chapter_id).first()
        if chapter and chapter.framework_id:
            existing_framework_link = db.query(models.PolicyFrameworks).filter(
                models.PolicyFrameworks.policy_id == policy_id,
                models.PolicyFrameworks.framework_id == chapter.framework_id
            ).first()
            if not existing_framework_link:
                db.add(models.PolicyFrameworks(
                    policy_id=policy_id,
                    framework_id=chapter.framework_id
                ))
                db.commit()
    return db_policy_objective

def update_objective_order(db: Session, policy_id: uuid.UUID, objective_id: uuid.UUID, order: int):
    db_policy_objective = db.query(models.PolicyObjectives).filter(
        models.PolicyObjectives.policy_id == policy_id,
        models.PolicyObjectives.objective_id == objective_id
    ).first()

    if db_policy_objective:
        db_policy_objective.order = order
        db.commit()
        db.refresh(db_policy_objective)
    return db_policy_objective

def remove_objective_from_policy(db: Session, policy_id: uuid.UUID, objective_id: uuid.UUID):
    objective = db.query(models.Objectives).filter(models.Objectives.id == objective_id).first()
    framework_id = None
    if objective:
        chapter = db.query(models.Chapters).filter(models.Chapters.id == objective.chapter_id).first()
        if chapter:
            framework_id = chapter.framework_id

    db_policy_objective = db.query(models.PolicyObjectives).filter(
        models.PolicyObjectives.policy_id == policy_id,
        models.PolicyObjectives.objective_id == objective_id
    ).first()

    if db_policy_objective:
        db.delete(db_policy_objective)
        db.commit()

    if framework_id:
        remaining = db.query(models.PolicyObjectives).join(
            models.Objectives, models.PolicyObjectives.objective_id == models.Objectives.id
        ).join(
            models.Chapters, models.Objectives.chapter_id == models.Chapters.id
        ).filter(
            models.PolicyObjectives.policy_id == policy_id,
            models.Chapters.framework_id == framework_id
        ).count()

        if remaining == 0:
            db.query(models.PolicyFrameworks).filter(
                models.PolicyFrameworks.policy_id == policy_id,
                models.PolicyFrameworks.framework_id == framework_id
            ).delete()
            db.commit()

    return db_policy_objective


# ===========================
# Policy Connection Query operations
# ===========================

def get_objectives_for_policy(db: Session, policy_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get all objectives addressed by a specific policy"""
    try:
        # Verify policy exists and user has access
        policy = get_policy(db, policy_id, current_user)
        if not policy:
            return []

        # Get linked objective IDs via PolicyObjectives junction
        links = db.query(models.PolicyObjectives).filter(
            models.PolicyObjectives.policy_id == policy_id
        ).order_by(models.PolicyObjectives.order).all()

        objective_ids = [link.objective_id for link in links]

        if not objective_ids:
            return []

        # Get objectives with chapter info
        objectives = db.query(models.Objectives).filter(
            models.Objectives.id.in_(objective_ids)
        ).all()

        # Enrich objectives with chapter info
        for obj in objectives:
            chapter = db.query(models.Chapters).filter(
                models.Chapters.id == obj.chapter_id
            ).first()
            if chapter:
                obj.chapter_title = chapter.title

        return objectives
    except Exception as e:
        print(f"Error getting objectives for policy {policy_id}: {str(e)}")
        return []


def get_controls_for_policy(db: Session, policy_id: uuid.UUID, current_user: schemas.UserBase = None, framework_id: uuid.UUID = None):
    """Get all controls governed by a specific policy, optionally filtered by framework"""
    try:
        # Verify policy exists and user has access
        policy = get_policy(db, policy_id, current_user)
        if not policy:
            return []

        # Get linked control IDs via ControlPolicy junction
        link_query = db.query(models.ControlPolicy).filter(
            models.ControlPolicy.policy_id == policy_id
        )
        if framework_id:
            link_query = link_query.filter(models.ControlPolicy.framework_id == framework_id)

        links = link_query.all()

        control_ids = [link.control_id for link in links]

        if not control_ids:
            return []

        # Build query with organization filter
        query = db.query(models.Control).filter(models.Control.id.in_(control_ids))

        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Control.organisation_id == current_user.organisation_id)

        controls = query.all()

        # Enrich each control
        from app.repositories import control_repository
        for control in controls:
            control_repository._enrich_control_with_info(db, control)

        return controls
    except Exception as e:
        print(f"Error getting controls for policy {policy_id}: {str(e)}")
        return []


def sync_objective_compliance_from_policies(db: Session, objective_id: uuid.UUID, changed_policy_id: uuid.UUID = None, policy_lost_approval: bool = False):
    """Sync an objective's compliance status based on its linked policies.
    - If every linked policy is 'Approved', set the objective to 'compliant'.
    - If a policy lost its Approved status (policy_lost_approval=True), the
      objective is currently 'compliant', AND all OTHER linked policies are still
      Approved (meaning all were approved before this change), downgrade to 'in review'.
    - If the objective has no linked policies, do nothing.
    Returns the objective id and new status name if changed, else None."""

    objective = db.query(models.Objectives).filter(
        models.Objectives.id == objective_id
    ).first()
    if not objective:
        return None

    # Collect all objective IDs whose PolicyObjectives links should be considered.
    # For scoped clones, also include policies from the base (unscoped) objective.
    objective_ids_to_check = [objective_id]
    if objective.scope_id is not None:
        base_obj_ids = db.query(models.Objectives.id).filter(
            models.Objectives.chapter_id == objective.chapter_id,
            models.Objectives.title == objective.title,
            models.Objectives.subchapter == objective.subchapter,
            models.Objectives.scope_id.is_(None),
            models.Objectives.scope_entity_id.is_(None)
        ).all()
        objective_ids_to_check.extend(obj_id for (obj_id,) in base_obj_ids)

    # Get all policies linked to this objective (and its base, if scoped)
    linked_policies = db.query(models.Policies).join(
        models.PolicyObjectives,
        models.Policies.id == models.PolicyObjectives.policy_id
    ).filter(
        models.PolicyObjectives.objective_id.in_(objective_ids_to_check)
    ).distinct().all()

    if not linked_policies:
        return None

    # Check if ALL linked policies have "Approved" status
    approved_status = db.query(models.PolicyStatuses).filter(
        models.PolicyStatuses.status == "Approved"
    ).first()
    if not approved_status:
        return None

    all_approved = all(p.status_id == approved_status.id for p in linked_policies)

    # Get the "compliant" compliance status
    compliant_status = db.query(models.ComplianceStatuses).filter(
        models.ComplianceStatuses.status_name == "compliant"
    ).first()
    if not compliant_status:
        return None

    if all_approved:
        # Upgrade: all policies approved → set objective to compliant
        if objective.compliance_status_id != compliant_status.id:
            objective.compliance_status_id = compliant_status.id
            db.commit()
            return {"objective_id": str(objective_id), "new_status": "compliant"}
    elif policy_lost_approval and objective.compliance_status_id == compliant_status.id:
        # Downgrade only if all OTHER policies (excluding the one that just changed)
        # are still Approved — meaning before this change, ALL were approved.
        other_policies = [p for p in linked_policies if p.id != changed_policy_id]
        all_others_approved = all(p.status_id == approved_status.id for p in other_policies)
        if all_others_approved:
            in_review_status = db.query(models.ComplianceStatuses).filter(
                models.ComplianceStatuses.status_name == "in review"
            ).first()
            if in_review_status:
                objective.compliance_status_id = in_review_status.id
                db.commit()
                return {"objective_id": str(objective_id), "new_status": "in review"}

    return None


def sync_objectives_for_policy(db: Session, policy_id: uuid.UUID, policy_lost_approval: bool = False):
    """Check and update compliance status for all objectives linked to a given policy.
    Also processes scoped clones of base objectives so that scope-specific views stay in sync.
    If policy_lost_approval is True, objectives that are 'compliant' will be downgraded to 'in review'
    only if all other linked policies are still Approved (meaning all were approved before this change)."""
    linked_objective_ids = db.query(models.PolicyObjectives.objective_id).filter(
        models.PolicyObjectives.policy_id == policy_id
    ).all()

    all_objective_ids = set()
    for (objective_id,) in linked_objective_ids:
        all_objective_ids.add(objective_id)
        # If this is a base (unscoped) objective, also sync its scoped clones
        base_obj = db.query(models.Objectives).filter(
            models.Objectives.id == objective_id,
            models.Objectives.scope_id.is_(None)
        ).first()
        if base_obj:
            scoped_clone_ids = db.query(models.Objectives.id).filter(
                models.Objectives.chapter_id == base_obj.chapter_id,
                models.Objectives.title == base_obj.title,
                models.Objectives.subchapter == base_obj.subchapter,
                models.Objectives.scope_id.isnot(None)
            ).all()
            for (clone_id,) in scoped_clone_ids:
                all_objective_ids.add(clone_id)

    updated = []
    for objective_id in all_objective_ids:
        result = sync_objective_compliance_from_policies(db, objective_id, changed_policy_id=policy_id, policy_lost_approval=policy_lost_approval)
        if result:
            updated.append(result)
    return updated


def get_policies_for_objective(db: Session, objective_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get all policies that address a specific objective"""
    try:
        # Get linked policy IDs via PolicyObjectives junction
        links = db.query(models.PolicyObjectives).filter(
            models.PolicyObjectives.objective_id == objective_id
        ).all()

        policy_ids = [link.policy_id for link in links]

        if not policy_ids:
            return []

        # Build query with organization filter
        query = db.query(models.Policies).filter(models.Policies.id.in_(policy_ids))

        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Policies.organisation_id == current_user.organisation_id)

        policies = query.all()

        # Enrich each policy with status info
        for policy in policies:
            status = db.query(models.PolicyStatuses).filter(
                models.PolicyStatuses.id == policy.status_id
            ).first()
            if status:
                policy.status = status.status

        return policies
    except Exception as e:
        print(f"Error getting policies for objective {objective_id}: {str(e)}")
        return []
