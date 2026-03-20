from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from app.models import models
from app.dtos import schemas
from app.repositories.home_repository import calculate_assessment_progress, is_assessment_completed


def get_gap_analysis(db: Session, current_user: schemas.UserBase, framework_id: uuid.UUID = None):
    """
    Get comprehensive gap analysis data for compliance reporting.
    Returns summary, objectives analysis, assessment analysis, policy analysis,
    identified gaps, and chapter breakdown.
    """
    # Get frameworks filtered by org (+ optional framework_id)
    frameworks_query = db.query(models.Framework)

    if current_user.role_name != "super_admin":
        frameworks_query = frameworks_query.filter(
            models.Framework.organisation_id == current_user.organisation_id
        )

    if framework_id:
        frameworks_query = frameworks_query.filter(models.Framework.id == framework_id)

    frameworks = frameworks_query.all()
    framework_ids = [f.id for f in frameworks]

    if not framework_ids:
        return _empty_response()

    # Get chapters and objectives (base objectives only: scope_entity_id IS NULL)
    chapters = db.query(models.Chapters).filter(
        models.Chapters.framework_id.in_(framework_ids)
    ).all()
    chapter_ids = [c.id for c in chapters]
    chapter_map = {c.id: c.title for c in chapters}

    objectives = db.query(models.Objectives).filter(
        models.Objectives.chapter_id.in_(chapter_ids),
        models.Objectives.scope_entity_id.is_(None)
    ).all() if chapter_ids else []

    # Get compliance statuses lookup
    compliance_statuses = db.query(models.ComplianceStatuses).all()
    status_map = {s.id: s.status_name for s in compliance_statuses}
    status_key_map = {s.id: s.status_name.lower().replace(" ", "_") for s in compliance_statuses}

    # Count objectives by compliance status
    obj_counts = {
        "compliant": 0, "partially_compliant": 0, "not_compliant": 0,
        "in_review": 0, "not_assessed": 0, "not_applicable": 0
    }
    with_evidence = 0
    without_evidence = 0

    for obj in objectives:
        if obj.compliance_status_id and obj.compliance_status_id in status_key_map:
            key = status_key_map[obj.compliance_status_id]
            if key in obj_counts:
                obj_counts[key] += 1
            else:
                obj_counts["not_assessed"] += 1
        else:
            obj_counts["not_assessed"] += 1

        if obj.evidence_filename:
            with_evidence += 1
        else:
            without_evidence += 1

    total_objectives = len(objectives)
    applicable = total_objectives - obj_counts["not_applicable"]
    compliance_rate = round((obj_counts["compliant"] / applicable) * 100, 1) if applicable > 0 else 0

    # Assessment analysis
    assessments_query = db.query(models.Assessment).filter(
        models.Assessment.framework_id.in_(framework_ids)
    )
    if current_user.role_name != "super_admin":
        assessments_query = assessments_query.join(
            models.User, models.Assessment.user_id == models.User.id
        ).filter(models.User.organisation_id == current_user.organisation_id)
    if current_user.role_name == "org_user":
        assessments_query = assessments_query.filter(
            models.Assessment.user_id == current_user.id
        )

    assessments = assessments_query.all()
    total_assessments = len(assessments)
    completed_assessments = 0
    total_progress = 0.0
    total_questions = 0
    unanswered_questions = 0

    for assessment in assessments:
        progress = calculate_assessment_progress(db, assessment.id)
        total_progress += progress
        if is_assessment_completed(db, assessment.id):
            completed_assessments += 1
        # Count questions for this assessment
        total_a = db.query(models.Answer).filter(models.Answer.assessment_id == assessment.id).count()
        answered_a = db.query(models.Answer).filter(
            models.Answer.assessment_id == assessment.id,
            models.Answer.value.isnot(None)
        ).count()
        total_questions += total_a
        unanswered_questions += (total_a - answered_a)

    average_progress = round(total_progress / total_assessments, 1) if total_assessments > 0 else 0
    in_progress_assessments = total_assessments - completed_assessments
    completion_rate = round((completed_assessments / total_assessments) * 100, 1) if total_assessments > 0 else 0

    # Policy analysis
    policy_query = db.query(models.Policies).filter(
        models.Policies.organisation_id == current_user.organisation_id
    ) if current_user.role_name != "super_admin" else db.query(models.Policies)

    # If framework_id filter, only get policies linked to that framework
    if framework_id:
        policy_query = policy_query.join(
            models.PolicyFrameworks, models.Policies.id == models.PolicyFrameworks.policy_id
        ).filter(models.PolicyFrameworks.framework_id == framework_id)
    elif framework_ids:
        policy_query = policy_query.join(
            models.PolicyFrameworks, models.Policies.id == models.PolicyFrameworks.policy_id
        ).filter(models.PolicyFrameworks.framework_id.in_(framework_ids))

    policies = policy_query.all()
    total_policies = len(policies)

    # Get policy statuses
    policy_statuses = db.query(models.PolicyStatuses).all()
    policy_status_map = {ps.id: ps.status for ps in policy_statuses}

    status_counts = {}
    approved_count = 0
    for policy in policies:
        status_name = policy_status_map.get(policy.status_id, "Unknown")
        status_counts[status_name] = status_counts.get(status_name, 0) + 1
        if status_name.lower() == "approved":
            approved_count += 1

    by_status = [{"status": s, "count": c} for s, c in sorted(status_counts.items())]
    approved_percentage = round((approved_count / total_policies) * 100, 1) if total_policies > 0 else 0

    # Objectives with/without policy coverage
    objective_ids = [o.id for o in objectives]
    objectives_with_policies_set = set()
    if objective_ids:
        linked = db.query(models.PolicyObjectives.objective_id).filter(
            models.PolicyObjectives.objective_id.in_(objective_ids)
        ).distinct().all()
        objectives_with_policies_set = {r[0] for r in linked}

    objectives_with_policies = len(objectives_with_policies_set)
    objectives_without_policies = total_objectives - objectives_with_policies
    policy_coverage_percentage = round(
        (objectives_with_policies / total_objectives) * 100, 1
    ) if total_objectives > 0 else 0

    # Build gap lists (limit 50 per category)
    gaps_without_evidence = []
    gaps_not_compliant = []
    gaps_without_policies = []

    for obj in objectives:
        status_name = status_map.get(obj.compliance_status_id, "Not Assessed")
        chapter_title = chapter_map.get(obj.chapter_id, "Unknown")
        obj_info = {
            "id": str(obj.id),
            "title": obj.title,
            "chapter_title": chapter_title,
            "compliance_status": status_name
        }

        if not obj.evidence_filename and len(gaps_without_evidence) < 50:
            gaps_without_evidence.append(obj_info)

        status_key = status_key_map.get(obj.compliance_status_id, "not_assessed")
        if status_key == "not_compliant" and len(gaps_not_compliant) < 50:
            gaps_not_compliant.append(obj_info)

        if obj.id not in objectives_with_policies_set and len(gaps_without_policies) < 50:
            gaps_without_policies.append({
                "id": str(obj.id),
                "title": obj.title,
                "chapter_title": chapter_title
            })

    # Chapter breakdown
    chapter_breakdown = []
    chapter_objectives = {}
    for obj in objectives:
        if obj.chapter_id not in chapter_objectives:
            chapter_objectives[obj.chapter_id] = []
        chapter_objectives[obj.chapter_id].append(obj)

    for chapter in chapters:
        ch_objectives = chapter_objectives.get(chapter.id, [])
        ch_total = len(ch_objectives)
        if ch_total == 0:
            continue
        ch_compliant = 0
        ch_not_compliant = 0
        ch_not_assessed = 0
        for obj in ch_objectives:
            key = status_key_map.get(obj.compliance_status_id, "not_assessed")
            if key == "compliant":
                ch_compliant += 1
            elif key == "not_compliant":
                ch_not_compliant += 1
            elif key == "not_assessed":
                ch_not_assessed += 1
        ch_applicable = ch_total - sum(
            1 for o in ch_objectives
            if status_key_map.get(o.compliance_status_id, "not_assessed") == "not_applicable"
        )
        ch_rate = round((ch_compliant / ch_applicable) * 100, 1) if ch_applicable > 0 else 0
        chapter_breakdown.append({
            "chapter_title": chapter.title,
            "total_objectives": ch_total,
            "compliant": ch_compliant,
            "not_compliant": ch_not_compliant,
            "not_assessed": ch_not_assessed,
            "compliance_rate": ch_rate
        })

    # Overall score: 40% objectives compliance + 30% assessment completion + 30% policy approved %
    objectives_compliant_pct = (obj_counts["compliant"] / applicable * 100) if applicable > 0 else 0
    assessments_completed_pct = (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0
    overall_score = round(
        objectives_compliant_pct * 0.4 + assessments_completed_pct * 0.3 + approved_percentage * 0.3
    )

    return {
        "summary": {
            "total_frameworks": len(frameworks),
            "total_objectives": total_objectives,
            "total_assessments": total_assessments,
            "total_policies": total_policies,
            "overall_compliance_score": overall_score
        },
        "objectives_analysis": {
            "total": total_objectives,
            **obj_counts,
            "with_evidence": with_evidence,
            "without_evidence": without_evidence,
            "compliance_rate": compliance_rate
        },
        "assessment_analysis": {
            "total": total_assessments,
            "completed": completed_assessments,
            "in_progress": in_progress_assessments,
            "average_progress": average_progress,
            "unanswered_questions": unanswered_questions,
            "total_questions": total_questions,
            "completion_rate": completion_rate
        },
        "policy_analysis": {
            "total": total_policies,
            "by_status": by_status,
            "approved_count": approved_count,
            "approved_percentage": approved_percentage,
            "objectives_with_policies": objectives_with_policies,
            "objectives_without_policies": objectives_without_policies,
            "policy_coverage_percentage": policy_coverage_percentage
        },
        "gaps": {
            "objectives_without_evidence": gaps_without_evidence,
            "objectives_not_compliant": gaps_not_compliant,
            "objectives_without_policies": gaps_without_policies
        },
        "chapter_breakdown": chapter_breakdown
    }


def _empty_response():
    return {
        "summary": {
            "total_frameworks": 0, "total_objectives": 0,
            "total_assessments": 0, "total_policies": 0,
            "overall_compliance_score": 0
        },
        "objectives_analysis": {
            "total": 0, "compliant": 0, "partially_compliant": 0,
            "not_compliant": 0, "in_review": 0, "not_assessed": 0,
            "not_applicable": 0, "with_evidence": 0, "without_evidence": 0,
            "compliance_rate": 0
        },
        "assessment_analysis": {
            "total": 0, "completed": 0, "in_progress": 0,
            "average_progress": 0, "unanswered_questions": 0,
            "total_questions": 0, "completion_rate": 0
        },
        "policy_analysis": {
            "total": 0, "by_status": [], "approved_count": 0,
            "approved_percentage": 0, "objectives_with_policies": 0,
            "objectives_without_policies": 0, "policy_coverage_percentage": 0
        },
        "gaps": {
            "objectives_without_evidence": [],
            "objectives_not_compliant": [],
            "objectives_without_policies": []
        },
        "chapter_breakdown": []
    }
