# control_repository.py
from sqlalchemy.orm import Session
import uuid
import re
import logging
from typing import Optional, List
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


def get_next_control_code(db: Session, organisation_id) -> str:
    """Generate next CTL-N code for the given organisation."""
    existing_codes = db.query(models.Control.code).filter(
        models.Control.organisation_id == organisation_id,
        models.Control.code.isnot(None)
    ).all()

    max_n = 0
    for (code,) in existing_codes:
        match = re.match(r'^CTL-(\d+)$', code or '')
        if match:
            max_n = max(max_n, int(match.group(1)))

    return f"CTL-{max_n + 1}"

# ControlSet CRUD operations
def get_control_set(db: Session, control_set_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.ControlSet).filter(models.ControlSet.id == control_set_id)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.ControlSet.organisation_id == current_user.organisation_id)

        return query.first()
    except Exception as e:
        logger.error(f"Error getting control set with ID {control_set_id}: {str(e)}")
        return None

def get_control_sets(db: Session, current_user: schemas.UserBase = None, skip: int = 0, limit: int = 100):
    try:
        query = db.query(models.ControlSet)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.ControlSet.organisation_id == current_user.organisation_id)

        return query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting control sets: {str(e)}")
        return []

def create_control_set(db: Session, control_set: dict, current_user: schemas.UserBase = None):
    try:
        db_control_set = models.ControlSet(
            name=control_set["name"],
            description=control_set.get("description"),
            organisation_id=current_user.organisation_id if current_user else None,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None
        )
        db.add(db_control_set)
        db.commit()
        db.refresh(db_control_set)
        return db_control_set
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating control set: {str(e)}")
        return None

# Control CRUD operations
def get_control(db: Session, control_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.Control).filter(models.Control.id == control_id)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Control.organisation_id == current_user.organisation_id)

        control = query.first()
        if control:
            _enrich_control_with_info(db, control)
        return control
    except Exception as e:
        logger.error(f"Error getting control with ID {control_id}: {str(e)}")
        return None

def get_controls(db: Session, control_set_id: uuid.UUID = None, current_user: schemas.UserBase = None, skip: int = 0, limit: int = 1000):
    try:
        query = db.query(models.Control)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Control.organisation_id == current_user.organisation_id)

        # Filter by control set if provided
        if control_set_id:
            query = query.filter(models.Control.control_set_id == control_set_id)

        controls = query.offset(skip).limit(limit).all()

        # Enhance controls with related information
        for control in controls:
            _enrich_control_with_info(db, control)

        return controls
    except Exception as e:
        logger.error(f"Error getting controls: {str(e)}")
        return []

def _enrich_control_with_info(db: Session, control):
    """Helper function to add related information to control object"""
    try:
        # Get organization name
        organization = db.query(models.Organisations).filter(models.Organisations.id == control.organisation_id).first()
        if organization:
            control.organisation_name = organization.name

        # Get control set name
        control_set = db.query(models.ControlSet).filter(models.ControlSet.id == control.control_set_id).first()
        if control_set:
            control.control_set_name = control_set.name

        # Get control status
        control_status = db.query(models.ControlStatus).filter(models.ControlStatus.id == control.control_status_id).first()
        if control_status:
            control.control_status_name = control_status.status_name

        # Get last updated by user email
        if control.last_updated_by:
            last_updated_user = db.query(models.User).filter(models.User.id == control.last_updated_by).first()
            if last_updated_user:
                control.last_updated_by_email = last_updated_user.email
            else:
                control.last_updated_by_email = None
        else:
            control.last_updated_by_email = None

        # Get linked risks count (distinct by risk_id, since a pair can span multiple frameworks)
        linked_risks_count = db.query(models.ControlRisk.risk_id).filter(models.ControlRisk.control_id == control.id).distinct().count()
        control.linked_risks_count = linked_risks_count

        # Get linked policies count (distinct by policy_id, since a pair can span multiple frameworks)
        linked_policies_count = db.query(models.ControlPolicy.policy_id).filter(models.ControlPolicy.control_id == control.id).distinct().count()
        control.linked_policies_count = linked_policies_count

    except Exception as e:
        logger.error(f"Error enriching control with ID {control.id}: {str(e)}")
        # Continue even if there's an error

def create_control(db: Session, control: dict, current_user: schemas.UserBase = None):
    try:
        control_code = control.get("code")
        if not control_code and current_user:
            control_code = get_next_control_code(db, current_user.organisation_id)

        db_control = models.Control(
            code=control_code,
            name=control["name"],
            description=control.get("description"),
            category=control.get("category"),
            owner=control.get("owner"),
            control_set_id=uuid.UUID(control["control_set_id"]),
            control_status_id=uuid.UUID(control["control_status_id"]),
            organisation_id=current_user.organisation_id if current_user else None,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None
        )
        db.add(db_control)
        db.commit()
        db.refresh(db_control)

        # Enrich with related info before returning
        _enrich_control_with_info(db, db_control)

        return db_control
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating control: {str(e)}")
        return None

def update_control(db: Session, control_id: uuid.UUID, control: dict, current_user: schemas.UserBase = None):
    try:
        db_control = get_control(db, control_id, current_user)
        if db_control:
            db_control.code = control["code"]
            db_control.name = control["name"]
            db_control.description = control.get("description")
            db_control.category = control.get("category")
            db_control.owner = control.get("owner")
            db_control.control_set_id = uuid.UUID(control["control_set_id"])
            db_control.control_status_id = uuid.UUID(control["control_status_id"])
            db_control.last_updated_by = current_user.id if current_user else None

            db.commit()
            db.refresh(db_control)

            # Enrich with related info before returning
            _enrich_control_with_info(db, db_control)

        return db_control
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating control with ID {control_id}: {str(e)}")
        return None

def delete_control(db: Session, control_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        db_control = get_control(db, control_id, current_user)
        if not db_control:
            return None

        # Check ownership permissions for org_user
        if current_user and current_user.role_name == "org_user":
            if db_control.created_by != current_user.id:
                raise ValueError("org_user can only delete their own controls")

        db.delete(db_control)
        db.commit()
        return db_control
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting control with ID {control_id}: {str(e)}")
        return None

# Control Status CRUD operations
def get_control_status(db: Session, status_id: uuid.UUID):
    try:
        return db.query(models.ControlStatus).filter(models.ControlStatus.id == status_id).first()
    except Exception as e:
        logger.error(f"Error getting control status with ID {status_id}: {str(e)}")
        return None

def get_control_statuses(db: Session, skip: int = 0, limit: int = 100):
    try:
        return db.query(models.ControlStatus).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting control statuses: {str(e)}")
        return []

# Helper functions for control imports
def get_status_id_by_name(db: Session, status_name: str) -> Optional[uuid.UUID]:
    """Get control status UUID by name"""
    try:
        status = db.query(models.ControlStatus).filter(
            models.ControlStatus.status_name.ilike(status_name)
        ).first()
        return status.id if status else None
    except Exception as e:
        logger.error(f"Error getting control status by name '{status_name}': {str(e)}")
        return None

def get_or_create_control_set(db: Session, name: str, current_user: schemas.UserBase = None) -> models.ControlSet:
    """Get existing control set or create new one"""
    try:
        # Try to find existing control set
        query = db.query(models.ControlSet).filter(models.ControlSet.name == name)

        if current_user:
            query = query.filter(models.ControlSet.organisation_id == current_user.organisation_id)

        control_set = query.first()

        if not control_set:
            # Create new control set
            control_set = models.ControlSet(
                name=name,
                organisation_id=current_user.organisation_id if current_user else None,
                created_by=current_user.id if current_user else None,
                last_updated_by=current_user.id if current_user else None
            )
            db.add(control_set)
            db.commit()
            db.refresh(control_set)

        return control_set
    except Exception as e:
        db.rollback()
        logger.error(f"Error getting or creating control set '{name}': {str(e)}")
        return None

def bulk_create_controls(
    db: Session,
    controls_data: list,
    control_set_id: uuid.UUID,
    control_status_id: uuid.UUID,
    current_user: schemas.UserBase = None
) -> dict:
    """
    Bulk create controls from template data.
    Returns dict with created_ids, failed_count, and errors.
    """
    created_ids = []
    errors = []

    # Calculate next auto-gen code for controls without codes
    next_code_str = get_next_control_code(db, current_user.organisation_id) if current_user else "CTL-1"
    next_code_n = int(re.match(r'^CTL-(\d+)$', next_code_str).group(1))

    for control_data in controls_data:
        try:
            control_code = control_data.get("code", "")
            if not control_code:
                control_code = f"CTL-{next_code_n}"
                next_code_n += 1

            db_control = models.Control(
                code=control_code,
                name=control_data.get("name", ""),
                description=control_data.get("description"),
                category=control_data.get("category"),
                owner=control_data.get("owner"),
                control_set_id=control_set_id,
                control_status_id=control_status_id,
                organisation_id=current_user.organisation_id if current_user else None,
                created_by=current_user.id if current_user else None,
                last_updated_by=current_user.id if current_user else None
            )
            db.add(db_control)
            db.flush()  # Get the ID without committing
            created_ids.append(str(db_control.id))
        except Exception as e:
            error_msg = f"Failed to create control '{control_data.get('code', 'Unknown')}': {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Commit all at once if any were created
    if created_ids:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit bulk control creation: {str(e)}")
            return {
                "created_ids": [],
                "failed_count": len(controls_data),
                "errors": [f"Database commit failed: {str(e)}"]
            }

    return {
        "created_ids": created_ids,
        "failed_count": len(errors),
        "errors": errors
    }

# Control-Risk link operations
def link_control_to_risk(db: Session, control_id: uuid.UUID, risk_id: uuid.UUID, framework_id: uuid.UUID):
    """Link a control to a risk within a specific framework"""
    try:
        # Check if link already exists
        existing = db.query(models.ControlRisk).filter(
            models.ControlRisk.control_id == control_id,
            models.ControlRisk.risk_id == risk_id,
            models.ControlRisk.framework_id == framework_id
        ).first()

        if existing:
            return existing

        link = models.ControlRisk(control_id=control_id, risk_id=risk_id, framework_id=framework_id)
        db.add(link)
        db.commit()
        return link
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking control to risk: {str(e)}")
        return None

def unlink_control_from_risk(db: Session, control_id: uuid.UUID, risk_id: uuid.UUID, framework_id: uuid.UUID):
    """Unlink a control from a risk within a specific framework"""
    try:
        link = db.query(models.ControlRisk).filter(
            models.ControlRisk.control_id == control_id,
            models.ControlRisk.risk_id == risk_id,
            models.ControlRisk.framework_id == framework_id
        ).first()

        if link:
            db.delete(link)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking control from risk: {str(e)}")
        return False

# Control-Policy link operations
def link_control_to_policy(db: Session, control_id: uuid.UUID, policy_id: uuid.UUID, framework_id: uuid.UUID):
    """Link a control to a policy within a specific framework"""
    try:
        # Check if link already exists
        existing = db.query(models.ControlPolicy).filter(
            models.ControlPolicy.control_id == control_id,
            models.ControlPolicy.policy_id == policy_id,
            models.ControlPolicy.framework_id == framework_id
        ).first()

        if existing:
            return existing

        link = models.ControlPolicy(control_id=control_id, policy_id=policy_id, framework_id=framework_id)
        db.add(link)
        db.commit()
        return link
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking control to policy: {str(e)}")
        return None

def unlink_control_from_policy(db: Session, control_id: uuid.UUID, policy_id: uuid.UUID, framework_id: uuid.UUID):
    """Unlink a control from a policy within a specific framework"""
    try:
        link = db.query(models.ControlPolicy).filter(
            models.ControlPolicy.control_id == control_id,
            models.ControlPolicy.policy_id == policy_id,
            models.ControlPolicy.framework_id == framework_id
        ).first()

        if link:
            db.delete(link)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking control from policy: {str(e)}")
        return False


# ===========================
# Control Connection Query operations
# ===========================

def get_risks_for_control(db: Session, control_id: uuid.UUID, current_user: schemas.UserBase = None, framework_id: uuid.UUID = None):
    """Get all risks mitigated by a specific control, optionally filtered by framework"""
    try:
        # Verify control exists and user has access
        control = get_control(db, control_id, current_user)
        if not control:
            return []

        # Get linked risk IDs via ControlRisk junction
        link_query = db.query(models.ControlRisk).filter(
            models.ControlRisk.control_id == control_id
        )
        if framework_id:
            link_query = link_query.filter(models.ControlRisk.framework_id == framework_id)

        links = link_query.all()

        risk_ids = [link.risk_id for link in links]

        if not risk_ids:
            return []

        # Build query with organization filter
        query = db.query(models.Risks).filter(models.Risks.id.in_(risk_ids))

        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Risks.organisation_id == current_user.organisation_id)

        risks = query.all()

        # Enrich each risk
        from app.repositories import risks_repository
        for risk in risks:
            risks_repository._enrich_risk_with_info(db, risk)

        return risks
    except Exception as e:
        logger.error(f"Error getting risks for control {control_id}: {str(e)}")
        return []


def get_policies_for_control(db: Session, control_id: uuid.UUID, current_user: schemas.UserBase = None, framework_id: uuid.UUID = None):
    """Get all policies that govern a specific control, optionally filtered by framework"""
    try:
        # Verify control exists and user has access
        control = get_control(db, control_id, current_user)
        if not control:
            return []

        # Get linked policy IDs via ControlPolicy junction
        link_query = db.query(models.ControlPolicy).filter(
            models.ControlPolicy.control_id == control_id
        )
        if framework_id:
            link_query = link_query.filter(models.ControlPolicy.framework_id == framework_id)

        links = link_query.all()

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
        logger.error(f"Error getting policies for control {control_id}: {str(e)}")
        return []
