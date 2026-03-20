# risk_assessment_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sa_func
import uuid
import logging
from typing import Optional, List
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)


# ===========================
# Score/Severity Mapping
# ===========================

def score_to_severity(score: Optional[int]) -> Optional[str]:
    """Map a 1-25 risk score to severity label"""
    if score is None:
        return None
    if score <= 4:
        return "Low"
    elif score <= 10:
        return "Medium"
    elif score <= 16:
        return "High"
    else:
        return "Critical"


def likelihood_to_severity(likelihood: Optional[int]) -> Optional[str]:
    """Map a 1-5 likelihood value to categorical severity"""
    if likelihood is None:
        return None
    if likelihood <= 2:
        return "Low"
    elif likelihood == 3:
        return "Medium"
    elif likelihood == 4:
        return "High"
    else:
        return "Critical"


def _compute_score(impact: Optional[int], likelihood: Optional[int]) -> Optional[int]:
    if impact is not None and likelihood is not None:
        return impact * likelihood
    return None


# ===========================
# Assessment CRUD
# ===========================

def get_assessments_for_risk(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None) -> List:
    try:
        query = db.query(models.RiskAssessment).filter(
            models.RiskAssessment.risk_id == risk_id
        )
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.RiskAssessment.organisation_id == current_user.organisation_id)
        assessments = query.order_by(desc(models.RiskAssessment.assessment_number)).all()
        for a in assessments:
            _enrich_assessment(db, a)
        return assessments
    except Exception as e:
        logger.error(f"Error getting assessments for risk {risk_id}: {str(e)}")
        return []


def get_latest_assessment(db: Session, risk_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.RiskAssessment).filter(
            models.RiskAssessment.risk_id == risk_id
        )
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.RiskAssessment.organisation_id == current_user.organisation_id)
        assessment = query.order_by(desc(models.RiskAssessment.assessment_number)).first()
        if assessment:
            _enrich_assessment(db, assessment)
        return assessment
    except Exception as e:
        logger.error(f"Error getting latest assessment for risk {risk_id}: {str(e)}")
        return None


def get_assessment(db: Session, risk_id: uuid.UUID, assessment_id: uuid.UUID, current_user: schemas.UserBase = None):
    try:
        query = db.query(models.RiskAssessment).filter(
            models.RiskAssessment.id == assessment_id,
            models.RiskAssessment.risk_id == risk_id
        )
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.RiskAssessment.organisation_id == current_user.organisation_id)
        assessment = query.first()
        if assessment:
            _enrich_assessment(db, assessment)
        return assessment
    except Exception as e:
        logger.error(f"Error getting assessment {assessment_id}: {str(e)}")
        return None


def get_next_assessment_number(db: Session, risk_id: uuid.UUID) -> int:
    result = db.query(sa_func.max(models.RiskAssessment.assessment_number)).filter(
        models.RiskAssessment.risk_id == risk_id
    ).scalar()
    return (result or 0) + 1


def create_assessment(db: Session, risk_id: uuid.UUID, data: schemas.RiskAssessmentCreate, current_user: schemas.UserBase):
    try:
        assessment_number = get_next_assessment_number(db, risk_id)

        inherent_score = _compute_score(data.inherent_impact, data.inherent_likelihood)
        current_score = _compute_score(data.current_impact, data.current_likelihood)
        target_score = _compute_score(data.target_impact, data.target_likelihood)
        residual_score = _compute_score(data.residual_impact, data.residual_likelihood)

        db_assessment = models.RiskAssessment(
            risk_id=risk_id,
            assessment_number=assessment_number,
            description=data.description,
            inherent_impact=data.inherent_impact,
            inherent_likelihood=data.inherent_likelihood,
            inherent_risk_score=inherent_score,
            current_impact=data.current_impact,
            current_likelihood=data.current_likelihood,
            current_risk_score=current_score,
            target_impact=data.target_impact,
            target_likelihood=data.target_likelihood,
            target_risk_score=target_score,
            residual_impact=data.residual_impact,
            residual_likelihood=data.residual_likelihood,
            residual_risk_score=residual_score,
            impact_health=data.impact_health,
            impact_financial=data.impact_financial,
            impact_service=data.impact_service,
            impact_legal=data.impact_legal,
            impact_reputation=data.impact_reputation,
            status=data.status or "Draft",
            organisation_id=current_user.organisation_id,
            assessed_by=current_user.id
        )
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)

        # Auto-sync risk fields
        sync_risk_from_assessment(db, risk_id)

        _enrich_assessment(db, db_assessment)
        return db_assessment
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating assessment for risk {risk_id}: {str(e)}")
        raise


def update_assessment(db: Session, risk_id: uuid.UUID, assessment_id: uuid.UUID, data: schemas.RiskAssessmentUpdate, current_user: schemas.UserBase):
    try:
        db_assessment = get_assessment(db, risk_id, assessment_id, current_user)
        if not db_assessment:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_assessment, field, value)

        # Recompute scores
        db_assessment.inherent_risk_score = _compute_score(db_assessment.inherent_impact, db_assessment.inherent_likelihood)
        db_assessment.current_risk_score = _compute_score(db_assessment.current_impact, db_assessment.current_likelihood)
        db_assessment.target_risk_score = _compute_score(db_assessment.target_impact, db_assessment.target_likelihood)
        db_assessment.residual_risk_score = _compute_score(db_assessment.residual_impact, db_assessment.residual_likelihood)

        db.commit()
        db.refresh(db_assessment)

        # Auto-sync risk fields
        sync_risk_from_assessment(db, risk_id)

        _enrich_assessment(db, db_assessment)
        return db_assessment
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating assessment {assessment_id}: {str(e)}")
        raise


def delete_assessment(db: Session, risk_id: uuid.UUID, assessment_id: uuid.UUID, current_user: schemas.UserBase):
    try:
        db_assessment = get_assessment(db, risk_id, assessment_id, current_user)
        if not db_assessment:
            return None

        db.delete(db_assessment)
        db.commit()

        # Re-sync risk fields after deletion
        sync_risk_from_assessment(db, risk_id)

        return db_assessment
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting assessment {assessment_id}: {str(e)}")
        return None


# ===========================
# Auto-sync logic
# ===========================

def sync_risk_from_assessment(db: Session, risk_id: uuid.UUID):
    """Sync risk register fields from the latest assessment"""
    try:
        risk = db.query(models.Risks).filter(models.Risks.id == risk_id).first()
        if not risk:
            return

        # Get the latest assessment
        latest = db.query(models.RiskAssessment).filter(
            models.RiskAssessment.risk_id == risk_id
        ).order_by(desc(models.RiskAssessment.assessment_number)).first()

        if not latest:
            # No assessments remain
            risk.assessment_status = "Not Assessed"
            db.commit()
            return

        # Map inherent_risk_score -> severity name -> risk_severity_id UUID
        inherent_severity_name = score_to_severity(latest.inherent_risk_score)
        if inherent_severity_name:
            severity = db.query(models.RiskSeverity).filter(
                models.RiskSeverity.risk_severity_name.ilike(inherent_severity_name)
            ).first()
            if severity:
                risk.risk_severity_id = severity.id

        # Map inherent_likelihood -> categorical -> likelihood UUID
        likelihood_name = likelihood_to_severity(latest.inherent_likelihood)
        if likelihood_name:
            likelihood_sev = db.query(models.RiskSeverity).filter(
                models.RiskSeverity.risk_severity_name.ilike(likelihood_name)
            ).first()
            if likelihood_sev:
                risk.likelihood = likelihood_sev.id

        # Map residual_risk_score -> severity name -> residual_risk UUID
        residual_score = latest.residual_risk_score if latest.residual_risk_score is not None else latest.inherent_risk_score
        residual_severity_name = score_to_severity(residual_score)
        if residual_severity_name:
            residual_sev = db.query(models.RiskSeverity).filter(
                models.RiskSeverity.risk_severity_name.ilike(residual_severity_name)
            ).first()
            if residual_sev:
                risk.residual_risk = residual_sev.id

        # Update assessment_status
        if latest.status in ("Draft", "In Progress"):
            risk.assessment_status = "Assessment in progress"
        elif latest.status == "Completed":
            risk.assessment_status = "Assessed"

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error syncing risk {risk_id} from assessment: {str(e)}")


# ===========================
# List view: Risks with latest assessment
# ===========================

def get_all_risks_with_assessments(db: Session, current_user: schemas.UserBase, skip: int = 0, limit: int = 100):
    """Get all risks with their latest assessment scores for the list page"""
    try:
        query = db.query(models.Risks)
        if current_user and current_user.role_name != "super_admin":
            query = query.filter(models.Risks.organisation_id == current_user.organisation_id)

        risks = query.offset(skip).limit(limit).all()
        result = []

        for risk in risks:
            # Get latest assessment for this risk
            latest = db.query(models.RiskAssessment).filter(
                models.RiskAssessment.risk_id == risk.id
            ).order_by(desc(models.RiskAssessment.assessment_number)).first()

            # Get assessment count
            count = db.query(sa_func.count(models.RiskAssessment.id)).filter(
                models.RiskAssessment.risk_id == risk.id
            ).scalar() or 0

            # Get risk severity name
            risk_severity_name = None
            if risk.risk_severity_id:
                sev = db.query(models.RiskSeverity).filter(models.RiskSeverity.id == risk.risk_severity_id).first()
                if sev:
                    risk_severity_name = sev.risk_severity_name

            risk_data = {
                "id": risk.id,
                "risk_code": risk.risk_code,
                "risk_category_name": risk.risk_category_name,
                "risk_category_description": risk.risk_category_description,
                "assessment_status": risk.assessment_status,
                "organisation_id": risk.organisation_id,
                "risk_severity": risk_severity_name,
                "inherent_risk_score": latest.inherent_risk_score if latest else None,
                "current_risk_score": latest.current_risk_score if latest else None,
                "target_risk_score": latest.target_risk_score if latest else None,
                "residual_risk_score": latest.residual_risk_score if latest else None,
                "inherent_severity": score_to_severity(latest.inherent_risk_score) if latest else None,
                "current_severity": score_to_severity(latest.current_risk_score) if latest else None,
                "target_severity": score_to_severity(latest.target_risk_score) if latest else None,
                "residual_severity": score_to_severity(latest.residual_risk_score) if latest else None,
                "last_assessed_at": latest.updated_at if latest else None,
                "assessment_count": count,
            }
            result.append(risk_data)

        return result
    except Exception as e:
        logger.error(f"Error getting risks with assessments: {str(e)}")
        return []


# ===========================
# Treatment Action CRUD
# ===========================

def create_treatment_action(db: Session, assessment_id: uuid.UUID, data: schemas.RiskTreatmentActionCreate):
    try:
        db_action = models.RiskTreatmentAction(
            assessment_id=assessment_id,
            description=data.description,
            due_date=data.due_date,
            owner=data.owner,
            status=data.status or "Open"
        )
        db.add(db_action)
        db.commit()
        db.refresh(db_action)
        return db_action
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating treatment action: {str(e)}")
        raise


def update_treatment_action(db: Session, action_id: uuid.UUID, data: schemas.RiskTreatmentActionUpdate):
    try:
        db_action = db.query(models.RiskTreatmentAction).filter(
            models.RiskTreatmentAction.id == action_id
        ).first()
        if not db_action:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_action, field, value)

        # Auto-set completed_at when status changes to Completed
        if data.status == "Completed" and db_action.completed_at is None:
            from datetime import datetime
            db_action.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(db_action)
        return db_action
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating treatment action {action_id}: {str(e)}")
        raise


def delete_treatment_action(db: Session, action_id: uuid.UUID):
    try:
        db_action = db.query(models.RiskTreatmentAction).filter(
            models.RiskTreatmentAction.id == action_id
        ).first()
        if not db_action:
            return None
        db.delete(db_action)
        db.commit()
        return db_action
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting treatment action {action_id}: {str(e)}")
        return None


def get_treatment_actions(db: Session, assessment_id: uuid.UUID):
    try:
        return db.query(models.RiskTreatmentAction).filter(
            models.RiskTreatmentAction.assessment_id == assessment_id
        ).order_by(models.RiskTreatmentAction.created_at).all()
    except Exception as e:
        logger.error(f"Error getting treatment actions for assessment {assessment_id}: {str(e)}")
        return []


# ===========================
# Enrichment
# ===========================

def _enrich_assessment(db: Session, assessment):
    """Add computed fields to assessment"""
    try:
        # Severity labels
        assessment.inherent_severity = score_to_severity(assessment.inherent_risk_score)
        assessment.current_severity = score_to_severity(assessment.current_risk_score)
        assessment.target_severity = score_to_severity(assessment.target_risk_score)
        assessment.residual_severity = score_to_severity(assessment.residual_risk_score)

        # Assessed by email
        if assessment.assessed_by:
            user = db.query(models.User).filter(models.User.id == assessment.assessed_by).first()
            if user:
                assessment.assessed_by_email = user.email

        # Risk info
        if assessment.risk_id:
            risk = db.query(models.Risks).filter(models.Risks.id == assessment.risk_id).first()
            if risk:
                assessment.risk_code = risk.risk_code
                assessment.risk_category_name = risk.risk_category_name
    except Exception as e:
        logger.error(f"Error enriching assessment {assessment.id}: {str(e)}")
