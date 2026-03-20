# services/change_radar_service.py
"""
Change Radar Service - Detects changes between audit engagements.
Compares current vs prior engagement to identify:
- New/modified/deleted controls
- Evidence updates
- Policy changes
- Answer modifications
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import models
from app.repositories import audit_engagement_repository


def compare_engagements(
    db: Session,
    current_engagement_id: uuid.UUID,
    prior_engagement_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Compare two engagements and return a detailed change report.
    """
    # Get both engagements
    current = audit_engagement_repository.get_engagement(db, current_engagement_id)
    prior = audit_engagement_repository.get_engagement(db, prior_engagement_id)

    if not current or not prior:
        return {"error": "One or both engagements not found"}

    # Initialize report
    report = {
        "current_engagement": {
            "id": str(current.id),
            "name": current.name,
            "assessment_id": str(current.assessment_id) if current.assessment_id else None
        },
        "prior_engagement": {
            "id": str(prior.id),
            "name": prior.name,
            "assessment_id": str(prior.assessment_id) if prior.assessment_id else None
        },
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {},
        "controls": {},
        "evidence": {},
        "policies": {},
        "answers": {}
    }

    # Compare if both have assessments
    if current.assessment_id and prior.assessment_id:
        # Compare answers (controls)
        report["answers"] = compare_answers(
            db, current.assessment_id, prior.assessment_id
        )

        # Compare evidence
        report["evidence"] = compare_evidence(
            db, current.assessment_id, prior.assessment_id
        )

    # Generate summary
    report["summary"] = generate_summary(report)

    return report


def compare_answers(
    db: Session,
    current_assessment_id: uuid.UUID,
    prior_assessment_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Compare answers between two assessments.
    """
    # Get all answers for both assessments
    current_answers = db.query(models.Answer).filter(
        models.Answer.assessment_id == current_assessment_id
    ).all()

    prior_answers = db.query(models.Answer).filter(
        models.Answer.assessment_id == prior_assessment_id
    ).all()

    # Create lookup by question_id for prior answers
    prior_lookup = {str(a.question_id): a for a in prior_answers}
    current_lookup = {str(a.question_id): a for a in current_answers}

    changes = {
        "new": [],
        "modified": [],
        "deleted": [],
        "unchanged": 0
    }

    # Check current answers against prior
    for answer in current_answers:
        question_id = str(answer.question_id)

        if question_id not in prior_lookup:
            # New answer
            changes["new"].append({
                "question_id": question_id,
                "answer_id": str(answer.id),
                "current_value": answer.answer_value,
                "current_status": answer.compliance_status
            })
        else:
            prior_answer = prior_lookup[question_id]

            # Check if modified
            if (answer.answer_value != prior_answer.answer_value or
                answer.compliance_status != prior_answer.compliance_status):
                changes["modified"].append({
                    "question_id": question_id,
                    "answer_id": str(answer.id),
                    "prior_answer_id": str(prior_answer.id),
                    "prior_value": prior_answer.answer_value,
                    "current_value": answer.answer_value,
                    "prior_status": prior_answer.compliance_status,
                    "current_status": answer.compliance_status,
                    "value_changed": answer.answer_value != prior_answer.answer_value,
                    "status_changed": answer.compliance_status != prior_answer.compliance_status
                })
            else:
                changes["unchanged"] += 1

    # Check for deleted (in prior but not in current)
    for question_id, prior_answer in prior_lookup.items():
        if question_id not in current_lookup:
            changes["deleted"].append({
                "question_id": question_id,
                "prior_answer_id": str(prior_answer.id),
                "prior_value": prior_answer.answer_value,
                "prior_status": prior_answer.compliance_status
            })

    return changes


def compare_evidence(
    db: Session,
    current_assessment_id: uuid.UUID,
    prior_assessment_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Compare evidence files between two assessments.
    """
    # Get answers to find evidence
    current_answer_ids = [a.id for a in db.query(models.Answer).filter(
        models.Answer.assessment_id == current_assessment_id
    ).all()]

    prior_answer_ids = [a.id for a in db.query(models.Answer).filter(
        models.Answer.assessment_id == prior_assessment_id
    ).all()]

    # Get evidence
    current_evidence = db.query(models.Evidence).filter(
        models.Evidence.answer_id.in_(current_answer_ids)
    ).all() if current_answer_ids else []

    prior_evidence = db.query(models.Evidence).filter(
        models.Evidence.answer_id.in_(prior_answer_ids)
    ).all() if prior_answer_ids else []

    # Create lookup by filename for comparison
    prior_by_filename = {e.filename: e for e in prior_evidence}
    current_by_filename = {e.filename: e for e in current_evidence}

    changes = {
        "new": [],
        "updated": [],
        "removed": [],
        "unchanged": 0
    }

    # Check current evidence
    for evidence in current_evidence:
        if evidence.filename not in prior_by_filename:
            changes["new"].append({
                "id": str(evidence.id),
                "filename": evidence.filename,
                "file_type": evidence.file_type,
                "file_size": evidence.file_size,
                "uploaded_at": evidence.uploaded_at.isoformat() if evidence.uploaded_at else None
            })
        else:
            prior_ev = prior_by_filename[evidence.filename]

            # Check if file was updated (different size or newer upload date)
            if (evidence.file_size != prior_ev.file_size or
                (evidence.uploaded_at and prior_ev.uploaded_at and
                 evidence.uploaded_at > prior_ev.uploaded_at)):
                changes["updated"].append({
                    "current_id": str(evidence.id),
                    "prior_id": str(prior_ev.id),
                    "filename": evidence.filename,
                    "prior_size": prior_ev.file_size,
                    "current_size": evidence.file_size,
                    "prior_uploaded": prior_ev.uploaded_at.isoformat() if prior_ev.uploaded_at else None,
                    "current_uploaded": evidence.uploaded_at.isoformat() if evidence.uploaded_at else None
                })
            else:
                changes["unchanged"] += 1

    # Check for removed evidence
    for filename, prior_ev in prior_by_filename.items():
        if filename not in current_by_filename:
            changes["removed"].append({
                "id": str(prior_ev.id),
                "filename": prior_ev.filename,
                "file_type": prior_ev.file_type,
                "file_size": prior_ev.file_size
            })

    return changes


def generate_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of all changes.
    """
    answers = report.get("answers", {})
    evidence = report.get("evidence", {})

    return {
        "total_answer_changes": (
            len(answers.get("new", [])) +
            len(answers.get("modified", [])) +
            len(answers.get("deleted", []))
        ),
        "new_answers": len(answers.get("new", [])),
        "modified_answers": len(answers.get("modified", [])),
        "deleted_answers": len(answers.get("deleted", [])),
        "unchanged_answers": answers.get("unchanged", 0),

        "total_evidence_changes": (
            len(evidence.get("new", [])) +
            len(evidence.get("updated", [])) +
            len(evidence.get("removed", []))
        ),
        "new_evidence": len(evidence.get("new", [])),
        "updated_evidence": len(evidence.get("updated", [])),
        "removed_evidence": len(evidence.get("removed", [])),
        "unchanged_evidence": evidence.get("unchanged", 0),

        "has_significant_changes": (
            len(answers.get("new", [])) > 0 or
            len(answers.get("modified", [])) > 0 or
            len(answers.get("deleted", [])) > 0 or
            len(evidence.get("new", [])) > 0 or
            len(evidence.get("updated", [])) > 0 or
            len(evidence.get("removed", [])) > 0
        )
    }


def get_engagement_history(
    db: Session,
    engagement_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """
    Get the history of engagements linked through prior_engagement_id.
    Returns a list from oldest to newest.
    """
    history = []
    current_id = engagement_id

    # Walk backwards through prior engagements
    visited = set()
    while current_id and current_id not in visited:
        visited.add(current_id)

        engagement = audit_engagement_repository.get_engagement(db, current_id)
        if not engagement:
            break

        history.append({
            "id": str(engagement.id),
            "name": engagement.name,
            "status": engagement.status,
            "audit_period_start": engagement.audit_period_start.isoformat() if engagement.audit_period_start else None,
            "audit_period_end": engagement.audit_period_end.isoformat() if engagement.audit_period_end else None,
            "created_at": engagement.created_at.isoformat() if engagement.created_at else None
        })

        current_id = engagement.prior_engagement_id

    # Reverse to get oldest first
    history.reverse()
    return history


def get_change_timeline(
    db: Session,
    engagement_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """
    Get a timeline of changes across all engagement history.
    """
    history = get_engagement_history(db, engagement_id)

    if len(history) < 2:
        return []

    timeline = []

    # Compare each consecutive pair
    for i in range(1, len(history)):
        prior = history[i - 1]
        current = history[i]

        comparison = compare_engagements(
            db,
            uuid.UUID(current["id"]),
            uuid.UUID(prior["id"])
        )

        timeline.append({
            "from_engagement": prior,
            "to_engagement": current,
            "summary": comparison.get("summary", {})
        })

    return timeline
