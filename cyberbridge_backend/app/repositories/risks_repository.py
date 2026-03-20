# risks_repository.py
from sqlalchemy.orm import Session
import re
import uuid
import logging
from typing import Optional
from app.models import models
from app.dtos import schemas
from app.services import scope_validation_service
from app.constants import risk_templates

logger = logging.getLogger(__name__)


def get_next_risk_code(db: Session, organisation_id) -> str:
    """Generate next RSK-N code for the given organisation."""
    existing_codes = db.query(models.Risks.risk_code).filter(
        models.Risks.organisation_id == organisation_id,
        models.Risks.risk_code.isnot(None)
    ).all()

    max_n = 0
    for (code,) in existing_codes:
        match = re.match(r'^RSK-(\d+)$', code or '')
        if match:
            max_n = max(max_n, int(match.group(1)))

    return f"RSK-{max_n + 1}"


def _normalize_risk_code(risk_code: str | None) -> str | None:
    if risk_code is None:
        return None
    normalized = risk_code.strip()
    return normalized if normalized else None


def _risk_code_exists(
    db: Session,
    organisation_id,
    risk_code: str,
    exclude_risk_id: uuid.UUID | None = None
) -> bool:
    query = db.query(models.Risks.id).filter(
        models.Risks.organisation_id == organisation_id,
        models.Risks.risk_code == risk_code
    )
    if exclude_risk_id:
        query = query.filter(models.Risks.id != exclude_risk_id)
    return query.first() is not None


def _is_reserved_template_risk_code(db: Session, risk_code: str) -> bool:
    if not risk_code:
        return False

    if db.query(models.RiskTemplate.id).filter(models.RiskTemplate.risk_code == risk_code).first() is not None:
        return True

    return any(template.get("risk_code") == risk_code for template in risk_templates.ALL_RISKS)

# Risk CRUD operations
def get_risk(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.Risks).filter(models.Risks.id == risk_id)
        
        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Risks.organisation_id == current_user.organisation_id)
        
        return query.first()
    except Exception as e:
        logger.error(f"Error getting risk with ID {risk_id}: {str(e)}")
        return None

def get_risks(db: Session, current_user: schemas.UserBase = None, skip: int = 0, limit: int = 100):
    try:
        query = db.query(models.Risks)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Risks.organisation_id == current_user.organisation_id)

        risks = query.offset(skip).limit(limit).all()

        # Enhance risks with related information
        for risk in risks:
            _enrich_risk_with_info(db, risk)

        # Batch-enrich with linked finding counts (avoids N+1)
        if risks:
            try:
                from app.repositories import scan_finding_repository
                risk_ids = [risk.id for risk in risks]
                counts = scan_finding_repository.get_finding_counts_for_risks(db, risk_ids)
                for risk in risks:
                    risk.linked_findings_count = counts.get(risk.id, 0)
            except Exception as enrich_err:
                logger.warning(f"Could not enrich risks with finding counts: {enrich_err}")

        return risks
    except Exception as e:
        logger.error(f"Error getting risks: {str(e)}")
        return []


def _enrich_risk_with_info(db: Session, risk):
    """Helper function to add related information to risk object"""
    try:
        # Get organization name
        organization = db.query(models.Organisations).filter(models.Organisations.id == risk.organisation_id).first()
        if organization:
            risk.organisation_name = organization.name

        # Get asset category
        asset_category = db.query(models.AssetCategories).filter(models.AssetCategories.id == risk.asset_category_id).first()
        if asset_category:
            risk.asset_category = asset_category.name

        # Get risk severity
        risk_severity = db.query(models.RiskSeverity).filter(models.RiskSeverity.id == risk.risk_severity_id).first()
        if risk_severity:
            risk.risk_severity = risk_severity.risk_severity_name

        # Get risk status
        risk_status = db.query(models.RiskStatuses).filter(models.RiskStatuses.id == risk.risk_status_id).first()
        if risk_status:
            risk.risk_status = risk_status.risk_status_name

        # Get last updated by user email
        if risk.last_updated_by:
            last_updated_user = db.query(models.User).filter(models.User.id == risk.last_updated_by).first()
            if last_updated_user:
                risk.last_updated_by_email = last_updated_user.email
            else:
                risk.last_updated_by_email = None
        else:
            risk.last_updated_by_email = None

        # Get scope information
        if risk.scope_id and hasattr(risk, 'scope_id'):
            scope_info = scope_validation_service.get_scope_info(
                db,
                risk.scope_id,
                risk.scope_entity_id
            )
            if scope_info:
                risk.scope_name = scope_info['scope_name']
                risk.scope_display_name = scope_info['entity_name']

    except Exception as e:
        logger.error(f"Error enhancing risk with ID {risk.id}: {str(e)}")
        # Continue even if there's an error

def create_risk(db: Session, risk: dict, current_user: schemas.UserBase = None):
    try:
        # Extract scope information if provided
        scope_name = risk.pop('scope_name', None)
        scope_entity_id_str = risk.pop('scope_entity_id', None)

        # Validate and add scope if provided
        scope_id = None
        scope_entity_id = None

        if scope_name:
            # Convert scope_entity_id to UUID if provided
            if scope_entity_id_str:
                scope_entity_id = uuid.UUID(scope_entity_id_str) if isinstance(scope_entity_id_str, str) else scope_entity_id_str

            # If entity-dependent scope has no entity, ignore scope instead of failing create
            if scope_name in {'Product', 'Asset', 'Organization'} and not scope_entity_id:
                logger.info(
                    f"Ignoring scope '{scope_name}' for risk create because no scope_entity_id was provided"
                )
                scope_name = None
            else:
                # Validate scope
                scope_result = scope_validation_service.validate_scope(
                    db,
                    scope_name,
                    scope_entity_id
                )
                scope_id = scope_result['scope_id']

        risk_code = _normalize_risk_code(risk.get("risk_code"))
        if not risk_code:
            raise ValueError("Risk code is required")

        organisation_id = current_user.organisation_id if current_user else None
        if _is_reserved_template_risk_code(db, risk_code):
            raise ValueError(
                f"Risk code '{risk_code}' is reserved for risk templates. Please use a unique custom code."
            )
        if organisation_id and _risk_code_exists(db, organisation_id, risk_code):
            raise ValueError(f"Risk code '{risk_code}' already exists in your organization.")

        asset_category_uuid = uuid.UUID(risk["asset_category_id"]) if risk["asset_category_id"] else None
        likelihood_uuid = uuid.UUID(risk["likelihood"])
        residual_risk_uuid = uuid.UUID(risk["residual_risk"])
        risk_severity_uuid = uuid.UUID(risk["risk_severity_id"])
        risk_status_uuid = uuid.UUID(risk["risk_status_id"])

        # Validate lookup references early to return actionable errors instead of generic 500s
        if asset_category_uuid:
            asset_category = db.query(models.AssetCategories).filter(models.AssetCategories.id == asset_category_uuid).first()
            if not asset_category:
                raise ValueError("Invalid asset_category_id. Please refresh and select a valid asset category.")

        likelihood = db.query(models.RiskSeverity).filter(models.RiskSeverity.id == likelihood_uuid).first()
        if not likelihood:
            raise ValueError("Invalid likelihood value. Please refresh and reselect likelihood.")

        residual_risk = db.query(models.RiskSeverity).filter(models.RiskSeverity.id == residual_risk_uuid).first()
        if not residual_risk:
            raise ValueError("Invalid residual_risk value. Please refresh and reselect residual risk.")

        risk_severity = db.query(models.RiskSeverity).filter(models.RiskSeverity.id == risk_severity_uuid).first()
        if not risk_severity:
            raise ValueError("Invalid risk_severity_id. Please refresh and reselect severity.")

        risk_status = db.query(models.RiskStatuses).filter(models.RiskStatuses.id == risk_status_uuid).first()
        if not risk_status:
            raise ValueError("Invalid risk_status_id. Please refresh and reselect status.")

        db_risk = models.Risks(
            asset_category_id=asset_category_uuid,
            risk_code=risk_code,
            risk_category_name=risk["risk_category_name"],
            risk_category_description=risk["risk_category_description"],
            risk_potential_impact=risk["risk_potential_impact"],
            risk_control=risk["risk_control"],
            likelihood=likelihood_uuid,
            residual_risk=residual_risk_uuid,
            risk_severity_id=risk_severity_uuid,
            risk_status_id=risk_status_uuid,
            assessment_status=risk.get("assessment_status") or "Not Assessed",
            organisation_id=current_user.organisation_id if current_user else None,
            scope_id=scope_id,
            scope_entity_id=scope_entity_id,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None
        )
        db.add(db_risk)
        db.commit()
        db.refresh(db_risk)

        # Enrich with scope info before returning
        _enrich_risk_with_info(db, db_risk)

        return db_risk
    except ValueError as e:
        db.rollback()
        logger.error(f"Validation error creating risk: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating risk: {str(e)}")
        raise

def update_risk(db: Session, risk_id: uuid.UUID, risk: dict, current_user: schemas.UserBase = None):
    try:
        db_risk = get_risk(db, risk_id, current_user)
        if db_risk:
            # Extract scope information if provided
            scope_name = risk.pop('scope_name', None)
            scope_entity_id_str = risk.pop('scope_entity_id', None)

            # Update basic risk fields
            db_risk.asset_category_id = uuid.UUID(risk["asset_category_id"]) if risk["asset_category_id"] else None
            new_risk_code = _normalize_risk_code(risk.get("risk_code"))
            if not new_risk_code:
                raise ValueError("Risk code is required")

            current_risk_code = _normalize_risk_code(db_risk.risk_code)
            if new_risk_code != current_risk_code and _is_reserved_template_risk_code(db, new_risk_code):
                raise ValueError(
                    f"Risk code '{new_risk_code}' is reserved for risk templates. Please use a unique custom code."
                )

            if _risk_code_exists(
                db,
                db_risk.organisation_id,
                new_risk_code,
                exclude_risk_id=risk_id
            ):
                raise ValueError(f"Risk code '{new_risk_code}' already exists in your organization.")

            db_risk.risk_code = new_risk_code
            db_risk.risk_category_name = risk["risk_category_name"]
            db_risk.risk_category_description = risk["risk_category_description"]
            db_risk.risk_potential_impact = risk["risk_potential_impact"]
            db_risk.risk_control = risk["risk_control"]
            db_risk.likelihood = uuid.UUID(risk["likelihood"])
            db_risk.residual_risk = uuid.UUID(risk["residual_risk"])
            db_risk.risk_severity_id = uuid.UUID(risk["risk_severity_id"])
            db_risk.risk_status_id = uuid.UUID(risk["risk_status_id"])
            db_risk.assessment_status = risk.get("assessment_status") or db_risk.assessment_status or "Not Assessed"
            db_risk.last_updated_by = current_user.id if current_user else None

            # Update scope if provided
            if scope_name:
                scope_entity_id = None
                if scope_entity_id_str:
                    scope_entity_id = uuid.UUID(scope_entity_id_str) if isinstance(scope_entity_id_str, str) else scope_entity_id_str

                # If entity-dependent scope has no entity, ignore scope update instead of failing
                if scope_name in {'Product', 'Asset', 'Organization'} and not scope_entity_id:
                    logger.info(
                        f"Ignoring scope '{scope_name}' for risk update {risk_id} because no scope_entity_id was provided"
                    )
                else:
                    # Validate scope
                    scope_result = scope_validation_service.validate_scope(
                        db,
                        scope_name,
                        scope_entity_id
                    )
                    db_risk.scope_id = scope_result['scope_id']
                    db_risk.scope_entity_id = scope_entity_id

            db.commit()
            db.refresh(db_risk)

            # Enrich with scope info before returning
            _enrich_risk_with_info(db, db_risk)

        return db_risk
    except ValueError as e:
        db.rollback()
        logger.error(f"Validation error updating risk with ID {risk_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating risk with ID {risk_id}: {str(e)}")
        raise

def delete_risk(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        db_risk = get_risk(db, risk_id, current_user)
        if not db_risk:
            return None

        # Check ownership permissions for org_user
        if current_user and current_user.role_name == "org_user":
            if db_risk.created_by != current_user.id:
                raise ValueError("org_user can only delete their own risks")

        db.delete(db_risk)
        db.commit()
        return db_risk
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting risk with ID {risk_id}: {str(e)}")
        return None

# Risk Category CRUD operations
def get_risk_category(db: Session, category_id: uuid.UUID):
    try:
        return db.query(models.RiskCategories).filter(models.RiskCategories.id == category_id).first()
    except Exception as e:
        logger.error(f"Error getting risk category with ID {category_id}: {str(e)}")
        return None

def get_risk_categories(db: Session, asset_category_id: uuid.UUID = None, skip: int = 0, limit: int = 100):
    try:
        query = db.query(models.RiskCategories)
        if asset_category_id:
            query = query.filter(models.RiskCategories.asset_category_id == asset_category_id)
        return query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting risk categories: {str(e)}")
        return []

# Risk Severity CRUD operations
def get_risk_severity(db: Session, severity_id: uuid.UUID):
    try:
        return db.query(models.RiskSeverity).filter(models.RiskSeverity.id == severity_id).first()
    except Exception as e:
        logger.error(f"Error getting risk severity with ID {severity_id}: {str(e)}")
        return None

def get_risk_severities(db: Session, skip: int = 0, limit: int = 100):
    try:
        return db.query(models.RiskSeverity).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting risk severities: {str(e)}")
        return []

# Risk Status CRUD operations
def get_risk_status(db: Session, status_id: uuid.UUID):
    try:
        return db.query(models.RiskStatuses).filter(models.RiskStatuses.id == status_id).first()
    except Exception as e:
        logger.error(f"Error getting risk status with ID {status_id}: {str(e)}")
        return None

def get_risk_statuses(db: Session, skip: int = 0, limit: int = 100):
    try:
        return db.query(models.RiskStatuses).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting risk statuses: {str(e)}")
        return []


# Helper functions for risk templates
def get_severity_id_by_name(db: Session, severity_name: str) -> Optional[uuid.UUID]:
    """Get severity UUID by name (Low, Medium, High, Critical)"""
    try:
        severity = db.query(models.RiskSeverity).filter(
            models.RiskSeverity.risk_severity_name.ilike(severity_name)
        ).first()
        return severity.id if severity else None
    except Exception as e:
        logger.error(f"Error getting severity by name '{severity_name}': {str(e)}")
        return None


def get_status_id_by_name(db: Session, status_name: str) -> Optional[uuid.UUID]:
    """Get status UUID by name (Accept, Reduce, Avoid, Transfer, Share)"""
    try:
        status = db.query(models.RiskStatuses).filter(
            models.RiskStatuses.risk_status_name.ilike(status_name)
        ).first()
        return status.id if status else None
    except Exception as e:
        logger.error(f"Error getting status by name '{status_name}': {str(e)}")
        return None


def bulk_create_risks(
    db: Session,
    risks_data: list,
    asset_category_id: uuid.UUID,
    likelihood_id: uuid.UUID,
    severity_id: uuid.UUID,
    residual_risk_id: uuid.UUID,
    status_id: uuid.UUID,
    current_user: schemas.UserBase = None,
    scope_name: str = None,
    scope_entity_id: uuid.UUID = None
) -> dict:
    """
    Bulk create risks from template data.
    Returns dict with created_ids, failed_count, and errors.
    """
    created_ids = []
    errors = []

    # Validate and get scope if provided
    scope_id = None
    if scope_name:
        try:
            scope_result = scope_validation_service.validate_scope(
                db,
                scope_name,
                scope_entity_id
            )
            scope_id = scope_result['scope_id']
        except Exception as e:
            logger.warning(f"Scope validation failed: {str(e)}")
            # Continue without scope

    for risk_data in risks_data:
        try:
            # Use template risk_code if available, otherwise auto-generate
            risk_code = _normalize_risk_code(risk_data.get("risk_code"))
            if not risk_code:
                raise ValueError("Risk template is missing risk_code")

            db_risk = models.Risks(
                asset_category_id=asset_category_id,
                risk_code=risk_code,
                risk_category_name=risk_data.get("risk_category_name", ""),
                risk_category_description=risk_data.get("risk_category_description", ""),
                risk_potential_impact=risk_data.get("risk_potential_impact", ""),
                risk_control=risk_data.get("risk_control", ""),
                likelihood=likelihood_id,
                residual_risk=residual_risk_id,
                risk_severity_id=severity_id,
                risk_status_id=status_id,
                assessment_status="Not Assessed",
                organisation_id=current_user.organisation_id if current_user else None,
                scope_id=scope_id,
                scope_entity_id=scope_entity_id,
                created_by=current_user.id if current_user else None,
                last_updated_by=current_user.id if current_user else None
            )
            db.add(db_risk)
            db.flush()  # Get the ID without committing
            created_ids.append(str(db_risk.id))
        except Exception as e:
            error_msg = f"Failed to create risk '{risk_data.get('risk_category_name', 'Unknown')}': {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Commit all at once if any were created
    if created_ids:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit bulk risk creation: {str(e)}")
            return {
                "created_ids": [],
                "failed_count": len(risks_data),
                "errors": [f"Database commit failed: {str(e)}"]
            }

    return {
        "created_ids": created_ids,
        "failed_count": len(errors),
        "errors": errors
    }


# ===========================
# Risk Connection operations
# ===========================

def get_controls_for_risk(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None, framework_id: uuid.UUID = None):
    """Get all controls that mitigate a specific risk, optionally filtered by framework"""
    try:
        # Verify risk exists and user has access
        risk = get_risk(db, risk_id, current_user)
        if not risk:
            return []

        # Get linked control IDs via ControlRisk junction
        link_query = db.query(models.ControlRisk).filter(
            models.ControlRisk.risk_id == risk_id
        )
        if framework_id:
            link_query = link_query.filter(models.ControlRisk.framework_id == framework_id)

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
        logger.error(f"Error getting controls for risk {risk_id}: {str(e)}")
        return []


def get_assets_for_risk(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get all assets linked to a specific risk"""
    try:
        # Get linked asset IDs via AssetRisk junction
        links = db.query(models.AssetRisk).filter(
            models.AssetRisk.risk_id == risk_id
        ).all()

        asset_ids = [link.asset_id for link in links]

        if not asset_ids:
            return []

        # Build query with organization filter
        query = db.query(models.Assets).filter(models.Assets.id.in_(asset_ids))

        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Assets.organisation_id == current_user.organisation_id)

        assets = query.all()

        # Enrich each asset
        from app.repositories import assets_repository
        for asset in assets:
            assets_repository._enrich_asset_with_info(db, asset)

        return assets
    except Exception as e:
        logger.error(f"Error getting assets for risk {risk_id}: {str(e)}")
        return []


def link_asset_to_risk(db: Session, risk_id: uuid.UUID, asset_id: uuid.UUID):
    """Link an asset to a risk"""
    try:
        existing = db.query(models.AssetRisk).filter(
            models.AssetRisk.risk_id == risk_id,
            models.AssetRisk.asset_id == asset_id
        ).first()
        if existing:
            return existing
        link = models.AssetRisk(risk_id=risk_id, asset_id=asset_id)
        db.add(link)
        db.commit()
        return link
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking asset {asset_id} to risk {risk_id}: {str(e)}")
        raise


def unlink_asset_from_risk(db: Session, risk_id: uuid.UUID, asset_id: uuid.UUID):
    """Unlink an asset from a risk"""
    try:
        link = db.query(models.AssetRisk).filter(
            models.AssetRisk.risk_id == risk_id,
            models.AssetRisk.asset_id == asset_id
        ).first()
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking asset {asset_id} from risk {risk_id}: {str(e)}")
        return False


def get_objectives_for_risk(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get all objectives linked to a specific risk"""
    try:
        links = db.query(models.ObjectiveRisk).filter(
            models.ObjectiveRisk.risk_id == risk_id
        ).all()

        objective_ids = [link.objective_id for link in links]
        if not objective_ids:
            return []

        query = db.query(models.Objectives).filter(models.Objectives.id.in_(objective_ids))
        objectives = query.all()

        result = []
        for obj in objectives:
            result.append({
                "id": str(obj.id),
                "title": obj.title,
                "subchapter": getattr(obj, "subchapter", None),
                "chapter_id": str(obj.chapter_id) if obj.chapter_id else None,
            })
        return result
    except Exception as e:
        logger.error(f"Error getting objectives for risk {risk_id}: {str(e)}")
        return []


def link_objective_to_risk(db: Session, risk_id: uuid.UUID, objective_id: uuid.UUID):
    """Link an objective to a risk"""
    try:
        existing = db.query(models.ObjectiveRisk).filter(
            models.ObjectiveRisk.risk_id == risk_id,
            models.ObjectiveRisk.objective_id == objective_id
        ).first()
        if existing:
            return existing
        link = models.ObjectiveRisk(risk_id=risk_id, objective_id=objective_id)
        db.add(link)
        db.commit()
        return link
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking objective {objective_id} to risk {risk_id}: {str(e)}")
        raise


def unlink_objective_from_risk(db: Session, risk_id: uuid.UUID, objective_id: uuid.UUID):
    """Unlink an objective from a risk"""
    try:
        link = db.query(models.ObjectiveRisk).filter(
            models.ObjectiveRisk.risk_id == risk_id,
            models.ObjectiveRisk.objective_id == objective_id
        ).first()
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking objective {objective_id} from risk {risk_id}: {str(e)}")
        return False
