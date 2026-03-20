# assets_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import logging
from typing import Optional, List

from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


# ===========================
# Shared Lookup operations
# ===========================

def get_economic_operators(db: Session, skip: int = 0, limit: int = 100):
    """Get all economic operators"""
    return db.query(models.EconomicOperators).offset(skip).limit(limit).all()


def get_criticalities(db: Session, skip: int = 0, limit: int = 100):
    """Get all criticalities with their options"""
    criticalities = db.query(models.Criticalities).offset(skip).limit(limit).all()

    for criticality in criticalities:
        options = db.query(models.CriticalityOptions).filter(
            models.CriticalityOptions.criticality_id == criticality.id
        ).all()
        criticality.options = options

    return criticalities


def get_asset_categories(db: Session, skip: int = 0, limit: int = 100):
    """Get all asset categories (used by risk categorization)"""
    return db.query(models.AssetCategories).offset(skip).limit(limit).all()


# ===========================
# Asset Type CRUD operations
# ===========================

def get_asset_type(db: Session, asset_type_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get a single asset type by ID"""
    try:
        query = db.query(models.AssetTypes).filter(models.AssetTypes.id == asset_type_id)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.AssetTypes.organisation_id == current_user.organisation_id)

        return query.first()
    except Exception as e:
        logger.error(f"Error getting asset type with ID {asset_type_id}: {str(e)}")
        return None


def get_asset_types(db: Session, current_user: schemas.UserBase = None, skip: int = 0, limit: int = 100):
    """Get all asset types with computed counts"""
    try:
        query = db.query(models.AssetTypes)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.AssetTypes.organisation_id == current_user.organisation_id)

        asset_types = query.order_by(models.AssetTypes.name).offset(skip).limit(limit).all()

        # Enhance asset types with counts
        for asset_type in asset_types:
            _enrich_asset_type_with_counts(db, asset_type, current_user)

        return asset_types
    except Exception as e:
        logger.error(f"Error getting asset types: {str(e)}")
        return []


def _enrich_asset_type_with_counts(db: Session, asset_type, current_user: schemas.UserBase = None):
    """Helper function to add computed counts to asset type"""
    try:
        # Count assets of this type
        asset_count = db.query(func.count(models.Assets.id)).filter(
            models.Assets.asset_type_id == asset_type.id
        ).scalar() or 0
        asset_type.asset_count = asset_count

        # Get the Asset scope ID
        asset_scope = db.query(models.Scopes).filter(
            models.Scopes.scope_name == 'Asset'
        ).first()

        risk_count = 0
        risk_level = "Low"

        if asset_scope:
            # Get all asset IDs of this type
            asset_ids = db.query(models.Assets.id).filter(
                models.Assets.asset_type_id == asset_type.id
            ).all()
            asset_ids = [a[0] for a in asset_ids]

            if asset_ids:
                # Count risks linked to these assets
                risk_count = db.query(func.count(models.Risks.id)).filter(
                    models.Risks.scope_id == asset_scope.id,
                    models.Risks.scope_entity_id.in_(asset_ids)
                ).scalar() or 0

                # Determine risk level based on highest severity
                risks = db.query(models.Risks).filter(
                    models.Risks.scope_id == asset_scope.id,
                    models.Risks.scope_entity_id.in_(asset_ids)
                ).all()

                severities = set()
                for risk in risks:
                    if risk.risk_severity_id:
                        severity = db.query(models.RiskSeverity).filter(
                            models.RiskSeverity.id == risk.risk_severity_id
                        ).first()
                        if severity:
                            severities.add(severity.risk_severity_name.lower())

                # Determine overall risk level
                if 'critical' in severities or 'high' in severities:
                    risk_level = "Severe"
                elif 'medium' in severities:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"

        asset_type.risk_count = risk_count
        asset_type.risk_level = risk_level

    except Exception as e:
        logger.error(f"Error enriching asset type {asset_type.id}: {str(e)}")
        asset_type.asset_count = 0
        asset_type.risk_count = 0
        asset_type.risk_level = "Low"


def create_asset_type(db: Session, asset_type: dict, current_user: schemas.UserBase = None):
    """Create a new asset type"""
    try:
        db_asset_type = models.AssetTypes(
            name=asset_type["name"],
            icon_name=asset_type.get("icon_name"),
            description=asset_type.get("description"),
            default_confidentiality=asset_type.get("default_confidentiality"),
            default_integrity=asset_type.get("default_integrity"),
            default_availability=asset_type.get("default_availability"),
            default_asset_value=asset_type.get("default_asset_value"),
            organisation_id=current_user.organisation_id if current_user else None,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None
        )
        db.add(db_asset_type)
        db.commit()
        db.refresh(db_asset_type)

        # Enrich with counts
        _enrich_asset_type_with_counts(db, db_asset_type, current_user)

        return db_asset_type
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating asset type: {str(e)}")
        raise


def update_asset_type(db: Session, asset_type_id: uuid.UUID, asset_type: dict, current_user: schemas.UserBase = None):
    """Update an existing asset type"""
    try:
        db_asset_type = get_asset_type(db, asset_type_id, current_user)
        if not db_asset_type:
            return None

        db_asset_type.name = asset_type["name"]
        db_asset_type.icon_name = asset_type.get("icon_name")
        db_asset_type.description = asset_type.get("description")
        db_asset_type.default_confidentiality = asset_type.get("default_confidentiality")
        db_asset_type.default_integrity = asset_type.get("default_integrity")
        db_asset_type.default_availability = asset_type.get("default_availability")
        db_asset_type.default_asset_value = asset_type.get("default_asset_value")
        db_asset_type.last_updated_by = current_user.id if current_user else None

        db.commit()
        db.refresh(db_asset_type)

        # Enrich with counts
        _enrich_asset_type_with_counts(db, db_asset_type, current_user)

        return db_asset_type
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating asset type {asset_type_id}: {str(e)}")
        raise


def delete_asset_type(db: Session, asset_type_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Delete an asset type (only if no assets are linked)"""
    try:
        db_asset_type = get_asset_type(db, asset_type_id, current_user)
        if not db_asset_type:
            return None

        # Check for linked assets
        asset_count = db.query(func.count(models.Assets.id)).filter(
            models.Assets.asset_type_id == asset_type_id
        ).scalar() or 0

        if asset_count > 0:
            raise ValueError(f"Cannot delete asset type with {asset_count} linked asset(s). Please delete or reassign the assets first.")

        db.delete(db_asset_type)
        db.commit()
        return db_asset_type
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting asset type {asset_type_id}: {str(e)}")
        raise


# ===========================
# Asset CRUD operations
# ===========================

def get_asset(db: Session, asset_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get a single asset by ID"""
    try:
        query = db.query(models.Assets).filter(models.Assets.id == asset_id)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Assets.organisation_id == current_user.organisation_id)

        asset = query.first()
        if asset:
            _enrich_asset_with_info(db, asset)

        return asset
    except Exception as e:
        logger.error(f"Error getting asset with ID {asset_id}: {str(e)}")
        return None


def get_assets(db: Session, current_user: schemas.UserBase = None, asset_type_id: uuid.UUID = None, skip: int = 0, limit: int = 100):
    """Get all assets with optional filtering by asset type"""
    try:
        query = db.query(models.Assets)

        # Filter by organization for non-super_admin users
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Assets.organisation_id == current_user.organisation_id)

        # Filter by asset type if provided
        if asset_type_id:
            query = query.filter(models.Assets.asset_type_id == asset_type_id)

        assets = query.order_by(models.Assets.name).offset(skip).limit(limit).all()

        # Enhance assets with related info
        for asset in assets:
            _enrich_asset_with_info(db, asset)

        return assets
    except Exception as e:
        logger.error(f"Error getting assets: {str(e)}")
        return []


def _compute_overall_asset_value(asset):
    """Compute OAV as the highest of C, I, A, Asset Value (conservative approach)"""
    level_order = {'high': 3, 'medium': 2, 'low': 1}
    values = [
        asset.confidentiality,
        asset.integrity,
        asset.availability,
        asset.asset_value,
    ]
    highest = 0
    for v in values:
        if v and v.lower() in level_order:
            highest = max(highest, level_order[v.lower()])
    reverse_map = {3: 'high', 2: 'medium', 1: 'low'}
    asset.overall_asset_value = reverse_map.get(highest)


def _enrich_asset_with_scan_status(db: Session, asset):
    """Helper function to add scan status info to asset based on ip_address"""
    try:
        # Default scan status values
        asset.has_scan = False
        asset.last_scan_date = None
        asset.last_scan_status = None
        asset.last_scan_type = None
        asset.last_scan_scanner = None
        # Separate tracking for network and application scans
        asset.network_scan_status = None
        asset.network_scan_date = None
        asset.application_scan_status = None
        asset.application_scan_date = None

        # Only check for scans if asset has an ip_address
        if not asset.ip_address:
            return

        # Normalize the ip_address for matching
        # We need to match against scan_target which could be:
        # - Exact match
        # - URL that contains the ip/hostname
        # - IP that matches the hostname portion
        ip_address = asset.ip_address.strip()

        # Strip protocol and path for broader matching
        normalized_target = ip_address.lower()
        if normalized_target.startswith('http://'):
            normalized_target = normalized_target[7:]
        elif normalized_target.startswith('https://'):
            normalized_target = normalized_target[8:]
        # Remove trailing path
        if '/' in normalized_target:
            normalized_target = normalized_target.split('/')[0]

        from sqlalchemy import or_, func as sql_func

        # Query for the most recent Network scan (nmap)
        latest_network_scan = db.query(models.ScannerHistory).filter(
            models.ScannerHistory.organisation_id == asset.organisation_id,
            models.ScannerHistory.scanner_type == 'nmap',
            or_(
                models.ScannerHistory.scan_target == ip_address,
                sql_func.lower(models.ScannerHistory.scan_target).contains(normalized_target)
            )
        ).order_by(models.ScannerHistory.timestamp.desc()).first()

        if latest_network_scan:
            asset.has_scan = True
            asset.network_scan_status = latest_network_scan.status
            asset.network_scan_date = latest_network_scan.timestamp

        # Query for the most recent Application scan (zap)
        latest_app_scan = db.query(models.ScannerHistory).filter(
            models.ScannerHistory.organisation_id == asset.organisation_id,
            models.ScannerHistory.scanner_type == 'zap',
            or_(
                models.ScannerHistory.scan_target == ip_address,
                sql_func.lower(models.ScannerHistory.scan_target).contains(normalized_target)
            )
        ).order_by(models.ScannerHistory.timestamp.desc()).first()

        if latest_app_scan:
            asset.has_scan = True
            asset.application_scan_status = latest_app_scan.status
            asset.application_scan_date = latest_app_scan.timestamp

        # Set the "last scan" fields to the most recent of either type
        if latest_network_scan and latest_app_scan:
            if latest_network_scan.timestamp > latest_app_scan.timestamp:
                asset.last_scan_date = latest_network_scan.timestamp
                asset.last_scan_status = latest_network_scan.status
                asset.last_scan_type = latest_network_scan.scan_type
                asset.last_scan_scanner = latest_network_scan.scanner_type
            else:
                asset.last_scan_date = latest_app_scan.timestamp
                asset.last_scan_status = latest_app_scan.status
                asset.last_scan_type = latest_app_scan.scan_type
                asset.last_scan_scanner = latest_app_scan.scanner_type
        elif latest_network_scan:
            asset.last_scan_date = latest_network_scan.timestamp
            asset.last_scan_status = latest_network_scan.status
            asset.last_scan_type = latest_network_scan.scan_type
            asset.last_scan_scanner = latest_network_scan.scanner_type
        elif latest_app_scan:
            asset.last_scan_date = latest_app_scan.timestamp
            asset.last_scan_status = latest_app_scan.status
            asset.last_scan_type = latest_app_scan.scan_type
            asset.last_scan_scanner = latest_app_scan.scanner_type

    except Exception as e:
        logger.error(f"Error enriching asset {asset.id} with scan status: {str(e)}")
        # Set default values on error
        asset.has_scan = False
        asset.last_scan_date = None
        asset.last_scan_status = None
        asset.last_scan_type = None
        asset.last_scan_scanner = None
        asset.network_scan_status = None
        asset.network_scan_date = None
        asset.application_scan_status = None
        asset.application_scan_date = None


def _enrich_asset_with_info(db: Session, asset):
    """Helper function to add related info to asset"""
    try:
        # Get asset type info
        asset_type = None
        if asset.asset_type_id:
            asset_type = db.query(models.AssetTypes).filter(
                models.AssetTypes.id == asset.asset_type_id
            ).first()
            if asset_type:
                asset.asset_type_name = asset_type.name
                asset.asset_type_icon = asset_type.icon_name
            else:
                asset.asset_type_name = None
                asset.asset_type_icon = None

        # Get asset status info
        if asset.asset_status_id:
            status = db.query(models.AssetStatuses).filter(
                models.AssetStatuses.id == asset.asset_status_id
            ).first()
            asset.status_name = status.status if status else None
        else:
            asset.status_name = None

        # Get economic operator info
        if asset.economic_operator_id:
            operator = db.query(models.EconomicOperators).filter(
                models.EconomicOperators.id == asset.economic_operator_id
            ).first()
            asset.economic_operator_name = operator.name if operator else None
        else:
            asset.economic_operator_name = None

        # Get criticality info
        if asset.criticality_id:
            criticality = db.query(models.Criticalities).filter(
                models.Criticalities.id == asset.criticality_id
            ).first()
            asset.criticality_label = criticality.label if criticality else None
        else:
            asset.criticality_label = None

        # Get last updated by email
        if asset.last_updated_by:
            user = db.query(models.User).filter(
                models.User.id == asset.last_updated_by
            ).first()
            asset.last_updated_by_email = user.email if user else None
        else:
            asset.last_updated_by_email = None

        # CIA inheritance: if inherit_cia is True, overlay type defaults
        if getattr(asset, 'inherit_cia', True) and asset_type:
            asset.confidentiality = asset_type.default_confidentiality
            asset.integrity = asset_type.default_integrity
            asset.availability = asset_type.default_availability
            asset.asset_value = asset_type.default_asset_value

        # Compute overall asset value
        _compute_overall_asset_value(asset)

        # Get scan status for this asset
        _enrich_asset_with_scan_status(db, asset)

    except Exception as e:
        logger.error(f"Error enriching asset {asset.id}: {str(e)}")


def create_asset(db: Session, asset: dict, current_user: schemas.UserBase = None):
    """Create a new asset"""
    try:
        db_asset = models.Assets(
            name=asset["name"],
            version=asset.get("version"),
            justification=asset.get("justification"),
            license_model=asset.get("license_model"),
            description=asset.get("description"),
            sbom=asset.get("sbom"),
            ip_address=asset.get("ip_address"),
            asset_type_id=uuid.UUID(asset["asset_type_id"]),
            asset_status_id=uuid.UUID(asset["asset_status_id"]) if asset.get("asset_status_id") else None,
            economic_operator_id=uuid.UUID(asset["economic_operator_id"]) if asset.get("economic_operator_id") else None,
            criticality_id=uuid.UUID(asset["criticality_id"]) if asset.get("criticality_id") else None,
            criticality_option=asset.get("criticality_option"),
            confidentiality=asset.get("confidentiality"),
            integrity=asset.get("integrity"),
            availability=asset.get("availability"),
            asset_value=asset.get("asset_value"),
            inherit_cia=asset.get("inherit_cia", True),
            organisation_id=current_user.organisation_id if current_user else None,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None
        )
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)

        # Enrich with info
        _enrich_asset_with_info(db, db_asset)

        return db_asset
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating asset: {str(e)}")
        raise


def update_asset(db: Session, asset_id: uuid.UUID, asset: dict, current_user: schemas.UserBase = None):
    """Update an existing asset"""
    try:
        db_asset = get_asset(db, asset_id, current_user)
        if not db_asset:
            return None

        db_asset.name = asset["name"]
        db_asset.version = asset.get("version")
        db_asset.justification = asset.get("justification")
        db_asset.license_model = asset.get("license_model")
        db_asset.description = asset.get("description")
        db_asset.sbom = asset.get("sbom")
        db_asset.ip_address = asset.get("ip_address")
        db_asset.asset_type_id = uuid.UUID(asset["asset_type_id"])
        db_asset.asset_status_id = uuid.UUID(asset["asset_status_id"]) if asset.get("asset_status_id") else None
        db_asset.economic_operator_id = uuid.UUID(asset["economic_operator_id"]) if asset.get("economic_operator_id") else None
        db_asset.criticality_id = uuid.UUID(asset["criticality_id"]) if asset.get("criticality_id") else None
        db_asset.criticality_option = asset.get("criticality_option")
        db_asset.confidentiality = asset.get("confidentiality")
        db_asset.integrity = asset.get("integrity")
        db_asset.availability = asset.get("availability")
        db_asset.asset_value = asset.get("asset_value")
        db_asset.inherit_cia = asset.get("inherit_cia", True)
        db_asset.last_updated_by = current_user.id if current_user else None

        db.commit()
        db.refresh(db_asset)

        # Enrich with info
        _enrich_asset_with_info(db, db_asset)

        return db_asset
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating asset {asset_id}: {str(e)}")
        raise


def delete_asset(db: Session, asset_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Delete an asset"""
    try:
        db_asset = get_asset(db, asset_id, current_user)
        if not db_asset:
            return None

        # Check ownership permissions for org_user
        if current_user and current_user.role_name == "org_user":
            if db_asset.created_by != current_user.id:
                raise ValueError("org_user can only delete their own assets")

        db.delete(db_asset)
        db.commit()
        return db_asset
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting asset {asset_id}: {str(e)}")
        raise


# ===========================
# Asset Status operations
# ===========================

def get_asset_statuses(db: Session, skip: int = 0, limit: int = 100):
    """Get all asset statuses"""
    try:
        return db.query(models.AssetStatuses).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting asset statuses: {str(e)}")
        return []


# ===========================
# Asset-Risk Connection operations
# ===========================

def link_asset_to_risk(db: Session, asset_id: uuid.UUID, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Link an asset to a risk (many-to-many)"""
    try:
        # Verify asset exists and user has access
        asset = get_asset(db, asset_id, current_user)
        if not asset:
            raise ValueError("Asset not found or access denied")

        # Verify risk exists
        from app.repositories import risks_repository
        risk = risks_repository.get_risk(db, risk_id, current_user)
        if not risk:
            raise ValueError("Risk not found or access denied")

        # Check if link already exists
        existing = db.query(models.AssetRisk).filter(
            models.AssetRisk.asset_id == asset_id,
            models.AssetRisk.risk_id == risk_id
        ).first()

        if existing:
            return existing

        link = models.AssetRisk(asset_id=asset_id, risk_id=risk_id)
        db.add(link)
        db.commit()
        return link
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking asset to risk: {str(e)}")
        raise


def unlink_asset_from_risk(db: Session, asset_id: uuid.UUID, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Unlink an asset from a risk"""
    try:
        # Verify asset exists and user has access
        asset = get_asset(db, asset_id, current_user)
        if not asset:
            raise ValueError("Asset not found or access denied")

        link = db.query(models.AssetRisk).filter(
            models.AssetRisk.asset_id == asset_id,
            models.AssetRisk.risk_id == risk_id
        ).first()

        if link:
            db.delete(link)
            db.commit()
            return True
        return False
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking asset from risk: {str(e)}")
        raise


def get_risks_for_asset(db: Session, asset_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get all risks linked to a specific asset"""
    try:
        # Verify asset exists and user has access
        asset = get_asset(db, asset_id, current_user)
        if not asset:
            return []

        # Get linked risk IDs
        links = db.query(models.AssetRisk).filter(
            models.AssetRisk.asset_id == asset_id
        ).all()

        risk_ids = [link.risk_id for link in links]

        if not risk_ids:
            return []

        # Get the risks with enrichment
        from app.repositories import risks_repository
        risks = db.query(models.Risks).filter(
            models.Risks.id.in_(risk_ids)
        ).all()

        # Enrich each risk
        for risk in risks:
            risks_repository._enrich_risk_with_info(db, risk)

        return risks
    except Exception as e:
        logger.error(f"Error getting risks for asset {asset_id}: {str(e)}")
        return []


def get_assets_for_risk(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get all assets linked to a specific risk"""
    try:
        # Get linked asset IDs
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
        for asset in assets:
            _enrich_asset_with_info(db, asset)

        return assets
    except Exception as e:
        logger.error(f"Error getting assets for risk {risk_id}: {str(e)}")
        return []
