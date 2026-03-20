# app/services/scope_validation_service.py
import logging
import uuid
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)

# Define which scope types are currently supported
# This allows enabling new scope types without code changes
SCOPE_TABLE_MAPPING = {
    'Product': 'products',
    'Organization': 'organisations',
    'Asset': 'assets',  # Asset scope for linking risks to assets
    'Other': None,  # Special case: no entity validation needed
    # Future scope types (uncomment when implemented):
    # 'Project': 'projects',
    # 'Process': 'processes',
}


def get_supported_scope_types() -> list[str]:
    """Get list of currently supported scope types"""
    return list(SCOPE_TABLE_MAPPING.keys())


def validate_scope(
    db: Session,
    scope_name: str,
    scope_entity_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Validate that scope entity exists in the correct table.

    Args:
        db: Database session
        scope_name: Name of scope type ('Product', 'Organization', 'Other', etc.)
        scope_entity_id: UUID of the entity (optional for 'Other' scope)

    Returns:
        Dict containing entity and scope_id

    Raises:
        ValueError: If scope type is not supported or entity doesn't exist
    """
    if scope_name not in SCOPE_TABLE_MAPPING:
        raise ValueError(
            f"Scope type '{scope_name}' is not supported. "
            f"Supported types: {', '.join(SCOPE_TABLE_MAPPING.keys())}"
        )

    # Get scope_id from scopes table
    scope = db.query(models.Scopes).filter(
        models.Scopes.scope_name == scope_name
    ).first()

    if not scope:
        raise ValueError(f"Scope type '{scope_name}' not found in database")

    # Special case: 'Other' scope doesn't require entity validation
    if scope_name == 'Other':
        return {
            'scope_id': scope.id,
            'scope_entity': None
        }

    # For other scope types, entity_id is required
    if not scope_entity_id:
        raise ValueError(f"{scope_name} scope requires scope_entity_id")

    # Verify the entity exists in the correct table
    entity = None

    if scope_name == 'Product':
        # Product scope now maps to Assets table
        entity = db.query(models.Assets).filter(
            models.Assets.id == scope_entity_id
        ).first()
    elif scope_name == 'Organization':
        entity = db.query(models.Organisations).filter(
            models.Organisations.id == scope_entity_id
        ).first()
    elif scope_name == 'Asset':
        entity = db.query(models.Assets).filter(
            models.Assets.id == scope_entity_id
        ).first()
    # Add more scope types here as they're implemented

    if not entity:
        raise ValueError(
            f"{scope_name} with ID {scope_entity_id} not found"
        )

    return {
        'scope_id': scope.id,
        'scope_entity': entity
    }


def get_scope_display_name(
    db: Session,
    scope_name: str,
    scope_entity_id: Optional[uuid.UUID] = None
) -> Optional[str]:
    """
    Get human-readable name for the scoped entity.

    Args:
        db: Database session
        scope_name: Name of scope type
        scope_entity_id: UUID of the entity (optional for 'Other')

    Returns:
        Human-readable name or None if not found
    """
    try:
        # Special case: 'Other' scope
        if scope_name == 'Other':
            return "Other/Flexible Scope"

        if not scope_entity_id:
            return None

        if scope_name == 'Product':
            # Product scope now maps to Assets table
            asset = db.query(models.Assets).filter(
                models.Assets.id == scope_entity_id
            ).first()
            if asset:
                return asset.name

        elif scope_name == 'Organization':
            org = db.query(models.Organisations).filter(
                models.Organisations.id == scope_entity_id
            ).first()
            if org:
                return org.name

        elif scope_name == 'Asset':
            asset = db.query(models.Assets).filter(
                models.Assets.id == scope_entity_id
            ).first()
            if asset:
                return asset.name

        # Add more scope types here

        return None
    except Exception as e:
        logger.error(f"Error getting scope display name: {str(e)}")
        return None


def get_scope_info(
    db: Session,
    scope_id: Optional[uuid.UUID],
    scope_entity_id: Optional[uuid.UUID]
) -> Optional[Dict[str, Any]]:
    """
    Get scope information for an assessment or risk.

    Args:
        db: Database session
        scope_id: UUID of scope type
        scope_entity_id: UUID of scoped entity (optional for "Other" scope)

    Returns:
        Dict with scope_name and entity_name, or None if no scope
    """
    if not scope_id:
        return None

    try:
        # Get scope type name
        scope = db.query(models.Scopes).filter(
            models.Scopes.id == scope_id
        ).first()

        if not scope:
            return None

        # For "Other" scope type, entity_name is always None
        if scope.scope_name == 'Other':
            return {
                'scope_name': scope.scope_name,
                'scope_id': scope_id,
                'scope_entity_id': None,
                'entity_name': None
            }

        # For other scope types, entity_id is required
        if not scope_entity_id:
            return None

        # Get entity display name
        entity_name = get_scope_display_name(db, scope.scope_name, scope_entity_id)

        return {
            'scope_name': scope.scope_name,
            'scope_id': scope_id,
            'scope_entity_id': scope_entity_id,
            'entity_name': entity_name
        }
    except Exception as e:
        logger.error(f"Error getting scope info: {str(e)}")
        return None


def validate_framework_scope(
    db: Session,
    framework_id: uuid.UUID,
    scope_name: Optional[str],
    scope_entity_id: Optional[uuid.UUID]
) -> None:
    """
    Validate that the provided scope matches framework requirements.

    Args:
        db: Database session
        framework_id: UUID of the framework
        scope_name: Provided scope type name
        scope_entity_id: Provided scope entity UUID

    Raises:
        ValueError: If scope doesn't meet framework requirements
    """
    # Get framework scope configuration
    framework = db.query(models.Framework).filter(
        models.Framework.id == framework_id
    ).first()

    if not framework:
        raise ValueError(f"Framework with ID {framework_id} not found")

    # If framework has no scope requirements, any scope is valid
    if not framework.scope_selection_mode:
        return

    # Check scope requirements based on mode
    if framework.scope_selection_mode == 'required':
        # 'Other' scope type doesn't require scope_entity_id
        if not scope_name or (not scope_entity_id and scope_name != 'Other'):
            allowed_types_str = ""
            if framework.allowed_scope_types:
                # The hybrid property already converts JSON to list
                allowed_types = framework.allowed_scope_types
                allowed_types_str = f" Allowed scope types: {', '.join(allowed_types)}"
            raise ValueError(
                f"Framework '{framework.name}' requires a scope.{allowed_types_str}"
            )

        # Check if provided scope is allowed
        if framework.allowed_scope_types:
            # The hybrid property already converts JSON to list
            allowed_types = framework.allowed_scope_types
            if scope_name not in allowed_types:
                raise ValueError(
                    f"Scope type '{scope_name}' is not allowed for framework '{framework.name}'. "
                    f"Allowed types: {', '.join(allowed_types)}"
                )

    elif framework.scope_selection_mode == 'optional':
        # Scope is optional, but if provided, must be valid
        if scope_name and scope_entity_id:
            if framework.allowed_scope_types:
                # The hybrid property already converts JSON to list
                allowed_types = framework.allowed_scope_types
                if scope_name not in allowed_types:
                    raise ValueError(
                        f"Scope type '{scope_name}' is not allowed for framework '{framework.name}'. "
                        f"Allowed types: {', '.join(allowed_types)}"
                    )

    # For 'flexible' mode, any scope is valid (no validation needed)


def get_framework_scope_config(
    db: Session,
    framework_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get scope configuration for a framework.

    Args:
        db: Database session
        framework_id: UUID of the framework

    Returns:
        Dict with scope configuration
    """
    framework = db.query(models.Framework).filter(
        models.Framework.id == framework_id
    ).first()

    if not framework:
        raise ValueError(f"Framework with ID {framework_id} not found")

    # The hybrid property already converts JSON to list, so just use it directly
    allowed_types = framework.allowed_scope_types or []

    return {
        'allowed_scope_types': allowed_types,
        'scope_selection_mode': framework.scope_selection_mode or 'optional',
        'supported_scope_types': get_supported_scope_types()
    }
