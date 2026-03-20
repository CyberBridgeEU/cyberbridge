# ce_marking_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import datetime
import uuid
import logging
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


def get_ce_product_types(db: Session):
    return db.query(models.CEProductTypes).order_by(models.CEProductTypes.name).all()


def get_ce_document_types(db: Session):
    return db.query(models.CEDocumentTypes).order_by(models.CEDocumentTypes.sort_order).all()


def _enrich_checklist(db: Session, checklist):
    """Add asset_name, product_type_name, item/doc counts."""
    try:
        asset = db.query(models.Assets).filter(models.Assets.id == checklist.asset_id).first()
        checklist.asset_name = asset.name if asset else None

        if checklist.ce_product_type_id:
            pt = db.query(models.CEProductTypes).filter(models.CEProductTypes.id == checklist.ce_product_type_id).first()
            checklist.ce_product_type_name = pt.name if pt else None
        else:
            checklist.ce_product_type_name = None

        # Item counts
        total_items = db.query(models.CEChecklistItems).filter(
            models.CEChecklistItems.checklist_id == checklist.id
        ).count()
        completed_items = db.query(models.CEChecklistItems).filter(
            models.CEChecklistItems.checklist_id == checklist.id,
            models.CEChecklistItems.is_completed == True
        ).count()
        checklist.items_total = total_items
        checklist.items_completed = completed_items

        # Doc counts
        total_docs = db.query(models.CEDocumentStatuses).filter(
            models.CEDocumentStatuses.checklist_id == checklist.id
        ).count()
        completed_docs = db.query(models.CEDocumentStatuses).filter(
            models.CEDocumentStatuses.checklist_id == checklist.id,
            models.CEDocumentStatuses.status == "complete"
        ).count()
        checklist.docs_total = total_docs
        checklist.docs_completed = completed_docs
    except Exception as e:
        logger.error(f"Error enriching checklist {checklist.id}: {str(e)}")


def get_checklists(db: Session, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.CEMarkingChecklists)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.CEMarkingChecklists.organisation_id == current_user.organisation_id)
        checklists = query.order_by(models.CEMarkingChecklists.created_at.desc()).all()
        for cl in checklists:
            _enrich_checklist(db, cl)
        return checklists
    except Exception as e:
        logger.error(f"Error getting checklists: {str(e)}")
        return []


def get_checklist(db: Session, checklist_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.CEMarkingChecklists).filter(models.CEMarkingChecklists.id == checklist_id)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.CEMarkingChecklists.organisation_id == current_user.organisation_id)
        checklist = query.first()
        if checklist:
            _enrich_checklist(db, checklist)
        return checklist
    except Exception as e:
        logger.error(f"Error getting checklist {checklist_id}: {str(e)}")
        return None


def get_checklist_detail(db: Session, checklist_id: uuid.UUID, current_user: schemas.UserBase = None):
    """Get checklist with items and document statuses."""
    checklist = get_checklist(db, checklist_id, current_user)
    if not checklist:
        return None

    items = db.query(models.CEChecklistItems).filter(
        models.CEChecklistItems.checklist_id == checklist_id
    ).order_by(models.CEChecklistItems.sort_order).all()

    doc_statuses = db.query(models.CEDocumentStatuses).filter(
        models.CEDocumentStatuses.checklist_id == checklist_id
    ).all()

    # Enrich doc statuses with document type name
    for ds in doc_statuses:
        dt = db.query(models.CEDocumentTypes).filter(models.CEDocumentTypes.id == ds.document_type_id).first()
        ds.document_type_name = dt.name if dt else None

    checklist.items = items
    checklist.document_statuses = doc_statuses
    return checklist


def get_checklist_for_asset(db: Session, asset_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.CEMarkingChecklists).filter(models.CEMarkingChecklists.asset_id == asset_id)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.CEMarkingChecklists.organisation_id == current_user.organisation_id)
        checklist = query.first()
        if checklist:
            _enrich_checklist(db, checklist)
        return checklist
    except Exception as e:
        logger.error(f"Error getting checklist for asset {asset_id}: {str(e)}")
        return None


def create_checklist(db: Session, data: dict, current_user: schemas.UserBase = None):
    try:
        organisation_id = current_user.organisation_id if current_user else None

        db_checklist = models.CEMarkingChecklists(
            asset_id=uuid.UUID(data["asset_id"]),
            ce_product_type_id=uuid.UUID(data["ce_product_type_id"]) if data.get("ce_product_type_id") else None,
            organisation_id=organisation_id,
            created_by=current_user.id if current_user else None,
            last_updated_by=current_user.id if current_user else None,
        )
        db.add(db_checklist)
        db.flush()

        # Auto-instantiate items from templates
        templates = db.query(models.CEChecklistTemplateItems).order_by(models.CEChecklistTemplateItems.sort_order).all()
        for tmpl in templates:
            item = models.CEChecklistItems(
                checklist_id=db_checklist.id,
                template_item_id=tmpl.id,
                category=tmpl.category,
                title=tmpl.title,
                description=tmpl.description,
                sort_order=tmpl.sort_order,
                is_mandatory=tmpl.is_mandatory,
            )
            db.add(item)

        # Auto-create document status rows
        doc_types = db.query(models.CEDocumentTypes).order_by(models.CEDocumentTypes.sort_order).all()
        for dt in doc_types:
            ds = models.CEDocumentStatuses(
                checklist_id=db_checklist.id,
                document_type_id=dt.id,
            )
            db.add(ds)

        db.commit()
        db.refresh(db_checklist)
        _enrich_checklist(db, db_checklist)
        return db_checklist
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating checklist: {str(e)}")
        raise


def update_checklist(db: Session, checklist_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        db_checklist = get_checklist(db, checklist_id, current_user)
        if not db_checklist:
            return None

        for field in ["ce_placement", "ce_placement_notes", "notified_body_required",
                       "notified_body_name", "notified_body_number", "notified_body_certificate_ref",
                       "version_identifier", "build_identifier", "doc_publication_url",
                       "product_variants", "status"]:
            if data.get(field) is not None:
                setattr(db_checklist, field, data[field])

        if data.get("ce_product_type_id") is not None:
            db_checklist.ce_product_type_id = uuid.UUID(data["ce_product_type_id"]) if data["ce_product_type_id"] else None

        db_checklist.last_updated_by = current_user.id if current_user else None
        db.commit()
        db.refresh(db_checklist)
        _enrich_checklist(db, db_checklist)
        return db_checklist
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating checklist {checklist_id}: {str(e)}")
        raise


def delete_checklist(db: Session, checklist_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        db_checklist = get_checklist(db, checklist_id, current_user)
        if not db_checklist:
            return None
        db.delete(db_checklist)
        db.commit()
        return db_checklist
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting checklist {checklist_id}: {str(e)}")
        raise


def _compute_readiness_score(db: Session, checklist_id: uuid.UUID):
    """Compute readiness score: (mandatory completed + docs complete) / (total mandatory + total docs) * 100"""
    mandatory_total = db.query(models.CEChecklistItems).filter(
        models.CEChecklistItems.checklist_id == checklist_id,
        models.CEChecklistItems.is_mandatory == True
    ).count()
    mandatory_completed = db.query(models.CEChecklistItems).filter(
        models.CEChecklistItems.checklist_id == checklist_id,
        models.CEChecklistItems.is_mandatory == True,
        models.CEChecklistItems.is_completed == True
    ).count()
    docs_total = db.query(models.CEDocumentStatuses).filter(
        models.CEDocumentStatuses.checklist_id == checklist_id
    ).count()
    docs_completed = db.query(models.CEDocumentStatuses).filter(
        models.CEDocumentStatuses.checklist_id == checklist_id,
        models.CEDocumentStatuses.status == "complete"
    ).count()

    denominator = mandatory_total + docs_total
    if denominator == 0:
        return 0.0
    return round((mandatory_completed + docs_completed) / denominator * 100, 1)


def update_checklist_item(db: Session, item_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        item = db.query(models.CEChecklistItems).filter(models.CEChecklistItems.id == item_id).first()
        if not item:
            return None

        if data.get("is_completed") is not None:
            item.is_completed = data["is_completed"]
            if data["is_completed"]:
                item.completed_at = datetime.utcnow()
                item.completed_by = current_user.id if current_user else None
            else:
                item.completed_at = None
                item.completed_by = None

        if data.get("notes") is not None:
            item.notes = data["notes"]

        db.commit()

        # Recalculate readiness score
        score = _compute_readiness_score(db, item.checklist_id)
        checklist = db.query(models.CEMarkingChecklists).filter(models.CEMarkingChecklists.id == item.checklist_id).first()
        if checklist:
            checklist.readiness_score = score
            db.commit()

        db.refresh(item)
        return item
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating checklist item {item_id}: {str(e)}")
        raise


def add_custom_checklist_item(db: Session, checklist_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        checklist = db.query(models.CEMarkingChecklists).filter(models.CEMarkingChecklists.id == checklist_id).first()
        if not checklist:
            return None

        # Get max sort_order for this checklist
        max_order = db.query(sql_func.max(models.CEChecklistItems.sort_order)).filter(
            models.CEChecklistItems.checklist_id == checklist_id
        ).scalar() or 0

        item = models.CEChecklistItems(
            checklist_id=checklist_id,
            template_item_id=None,
            category=data["category"],
            title=data["title"],
            description=data.get("description"),
            sort_order=max_order + 1,
            is_mandatory=data.get("is_mandatory", False),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding custom item: {str(e)}")
        raise


def delete_checklist_item(db: Session, item_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        item = db.query(models.CEChecklistItems).filter(models.CEChecklistItems.id == item_id).first()
        if not item:
            return None
        # Only allow deleting custom items (no template)
        if item.template_item_id is not None:
            raise ValueError("Cannot delete template-based items")
        checklist_id = item.checklist_id
        db.delete(item)
        db.commit()

        # Recalculate score
        score = _compute_readiness_score(db, checklist_id)
        checklist = db.query(models.CEMarkingChecklists).filter(models.CEMarkingChecklists.id == checklist_id).first()
        if checklist:
            checklist.readiness_score = score
            db.commit()

        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting checklist item {item_id}: {str(e)}")
        raise


def update_document_status(db: Session, status_id: uuid.UUID, data: dict, current_user: schemas.UserBase = None):
    try:
        ds = db.query(models.CEDocumentStatuses).filter(models.CEDocumentStatuses.id == status_id).first()
        if not ds:
            return None

        if data.get("status") is not None:
            ds.status = data["status"]
            if data["status"] == "complete":
                ds.completed_at = datetime.utcnow()
                ds.completed_by = current_user.id if current_user else None
            elif ds.status != "complete":
                ds.completed_at = None
                ds.completed_by = None

        if data.get("document_reference") is not None:
            ds.document_reference = data["document_reference"]
        if data.get("notes") is not None:
            ds.notes = data["notes"]

        db.commit()

        # Recalculate readiness score
        score = _compute_readiness_score(db, ds.checklist_id)
        checklist = db.query(models.CEMarkingChecklists).filter(models.CEMarkingChecklists.id == ds.checklist_id).first()
        if checklist:
            checklist.readiness_score = score
            db.commit()

        db.refresh(ds)
        # Enrich with doc type name
        dt = db.query(models.CEDocumentTypes).filter(models.CEDocumentTypes.id == ds.document_type_id).first()
        ds.document_type_name = dt.name if dt else None
        return ds
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating document status {status_id}: {str(e)}")
        raise
