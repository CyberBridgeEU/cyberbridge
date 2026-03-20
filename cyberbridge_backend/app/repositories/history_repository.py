# repositories/history_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime
from ..models import models


def resolve_foreign_key_value(db: Session, table_name: str, column_name: str, value: Any) -> str:
    """Resolve foreign key IDs to human-readable values"""
    if not value or not isinstance(value, str):
        return str(value) if value is not None else "null"

    # Check if this looks like a UUID (foreign key)
    try:
        uuid_val = uuid.UUID(str(value))
    except (ValueError, TypeError):
        return str(value)

    # Map foreign key columns to their display values
    foreign_key_mappings = {
        "compliance_status_id": (models.ComplianceStatuses, "status_name"),
        "policy_status_id": (models.PolicyStatuses, "status"),
        "asset_category_id": (models.AssetCategories, "name"),
        "economic_operator_id": (models.EconomicOperators, "name"),
        "criticality_id": (models.Criticalities, "label"),
        "risk_status_id": (models.RiskStatuses, "risk_status_name"),
        "risk_severity_id": (models.RiskSeverity, "risk_severity_name"),
        "role_id": (models.Role, "role_name"),
        "organisation_id": (models.Organisations, "name"),
        "framework_id": (models.Framework, "name"),
        "chapter_id": (models.Chapters, "title"),
    }

    if column_name in foreign_key_mappings:
        model_class, display_field = foreign_key_mappings[column_name]
        try:
            record = db.query(model_class).filter(model_class.id == uuid_val).first()
            if record:
                return getattr(record, display_field, str(value))
        except Exception as e:
            # If anything goes wrong, just return the original value
            pass

    return str(value)


def create_history_entry(
    db: Session,
    table_name: str,
    record_id: str,
    action: str,
    user_id: uuid.UUID,
    user_email: str,
    organisation_id: uuid.UUID,
    column_name: Optional[str] = None,
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
    initial_user_id: Optional[uuid.UUID] = None,
    initial_user_email: Optional[str] = None
) -> models.History:
    """Create a history entry for tracking changes"""

    history_entry = models.History(
        table_name_changed=table_name,
        record_id=str(record_id),
        organisation_id=organisation_id,
        action=action,
        last_user_id=user_id,
        last_user_email=user_email,
        column_name=column_name,
        old_data=json.dumps(old_data) if old_data else None,
        new_data=json.dumps(new_data) if new_data else None,
        initial_user_id=initial_user_id,
        initial_user_email=initial_user_email,
        last_timestamp=datetime.utcnow()
    )

    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    return history_entry


def track_insert(
    db: Session,
    table_name: str,
    record_id: str,
    user_id: uuid.UUID,
    user_email: str,
    organisation_id: uuid.UUID,
    new_data: Dict[str, Any]
) -> models.History:
    """Track an INSERT operation"""
    return create_history_entry(
        db=db,
        table_name=table_name,
        record_id=record_id,
        action="insert",
        user_id=user_id,
        user_email=user_email,
        organisation_id=organisation_id,
        new_data=new_data,
        initial_user_id=user_id,
        initial_user_email=user_email
    )


def track_update(
    db: Session,
    table_name: str,
    record_id: str,
    user_id: uuid.UUID,
    user_email: str,
    organisation_id: uuid.UUID,
    changes: Dict[str, Dict[str, Any]]  # {"column_name": {"old": value, "new": value}}
) -> List[models.History]:
    """Track UPDATE operations for each changed column"""
    history_entries = []

    # Get initial user info if exists
    initial_history = db.query(models.History).filter(
        models.History.table_name_changed == table_name,
        models.History.record_id == str(record_id),
        models.History.action == "insert"
    ).first()

    initial_user_id = initial_history.initial_user_id if initial_history else user_id
    initial_user_email = initial_history.initial_user_email if initial_history else user_email

    for column_name, values in changes.items():
        # Resolve foreign key values to human-readable names
        old_resolved = resolve_foreign_key_value(db, table_name, column_name, values["old"])
        new_resolved = resolve_foreign_key_value(db, table_name, column_name, values["new"])

        history_entry = create_history_entry(
            db=db,
            table_name=table_name,
            record_id=record_id,
            action="update",
            user_id=user_id,
            user_email=user_email,
            organisation_id=organisation_id,
            column_name=column_name,
            old_data={"value": old_resolved},
            new_data={"value": new_resolved},
            initial_user_id=initial_user_id,
            initial_user_email=initial_user_email
        )
        history_entries.append(history_entry)

    return history_entries


def track_delete(
    db: Session,
    table_name: str,
    record_id: str,
    user_id: uuid.UUID,
    user_email: str,
    organisation_id: uuid.UUID,
    old_data: Dict[str, Any]
) -> models.History:
    """Track a DELETE operation"""

    # Get initial user info if exists
    initial_history = db.query(models.History).filter(
        models.History.table_name_changed == table_name,
        models.History.record_id == str(record_id),
        models.History.action == "insert"
    ).first()

    return create_history_entry(
        db=db,
        table_name=table_name,
        record_id=record_id,
        action="delete",
        user_id=user_id,
        user_email=user_email,
        organisation_id=organisation_id,
        old_data=old_data,
        initial_user_id=initial_history.initial_user_id if initial_history else user_id,
        initial_user_email=initial_history.initial_user_email if initial_history else user_email
    )


def get_history(
    db: Session,
    organisation_id: Optional[uuid.UUID] = None,
    table_name: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[models.History]:
    """Get history entries with optional filters"""
    query = db.query(models.History)

    if organisation_id:
        query = query.filter(models.History.organisation_id == organisation_id)

    if table_name:
        query = query.filter(models.History.table_name_changed == table_name)

    if user_id:
        query = query.filter(
            (models.History.last_user_id == user_id) |
            (models.History.initial_user_id == user_id)
        )

    if action:
        query = query.filter(models.History.action == action)

    return query.order_by(desc(models.History.last_timestamp)).offset(offset).limit(limit).all()


def get_record_history(
    db: Session,
    table_name: str,
    record_id: str
) -> List[models.History]:
    """Get all history for a specific record"""
    return db.query(models.History).filter(
        models.History.table_name_changed == table_name,
        models.History.record_id == str(record_id)
    ).order_by(desc(models.History.last_timestamp)).all()


def get_all_history(
    db: Session,
    limit: int = 100,
    offset: int = 0
) -> List[models.History]:
    """Get all history entries"""
    return db.query(models.History).order_by(
        desc(models.History.last_timestamp)
    ).offset(offset).limit(limit).all()


def clear_all_history_for_organization(
    db: Session,
    organisation_id: uuid.UUID
) -> int:
    """Delete all history records for a specific organization"""
    deleted_count = db.query(models.History).filter(
        models.History.organisation_id == organisation_id
    ).delete(synchronize_session=False)

    db.commit()
    return deleted_count