from sqlalchemy.orm import Session
from sqlalchemy import func, case, literal
import uuid
from app.models import models
from app.dtos import schemas

# Helper function to check if an assessment is completed
def is_assessment_completed(db: Session, assessment_id: uuid.UUID):
    """
    Check if an assessment is completed based on its answers.
    An assessment is considered completed if all answers have non-null values.
    """
    # Count total answers for the assessment
    total_answers = db.query(models.Answer).filter(models.Answer.assessment_id == assessment_id).count()

    # Count non-null answer values
    answered_count = db.query(models.Answer).filter(
        models.Answer.assessment_id == assessment_id,
        models.Answer.value.isnot(None)
    ).count()

    # Assessment is completed if all answers have values
    return total_answers > 0 and answered_count == total_answers

# Helper function to calculate assessment progress
def calculate_assessment_progress(db: Session, assessment_id: uuid.UUID):
    """
    Calculate the progress of an assessment based on its answers.
    Progress is calculated as (total not null answer values) / (total assessment answers).
    Returns a float between 0 and 1, or 0 if there are no answers.
    """
    # Count total answers for the assessment
    total_answers = db.query(models.Answer).filter(models.Answer.assessment_id == assessment_id).count()

    # Count non-null answer values
    answered_count = db.query(models.Answer).filter(
        models.Answer.assessment_id == assessment_id,
        models.Answer.value.isnot(None)
    ).count()

    # Calculate progress (avoid division by zero)
    if total_answers > 0:
        return (answered_count / total_answers)*100
    else:
        return 0

# Dashboard metrics
def get_dashboard_metrics(db: Session, current_user: schemas.UserBase):
    """
    Get dashboard metrics including total assessments, completed assessments, and compliance frameworks.
    Filters data based on user's role and organization.
    """
    # Base query for assessments
    assessments_query = db.query(models.Assessment)
    # Base query for frameworks
    frameworks_query = db.query(models.Framework)

    # Apply role-based filtering
    if current_user.role_name != "super_admin":
        # For org_admin and org_user, only show data from their organization
        assessments_query = assessments_query.join(
            models.User, 
            models.Assessment.user_id == models.User.id
        ).filter(models.User.organisation_id == current_user.organisation_id)

        frameworks_query = frameworks_query.filter(
            models.Framework.organisation_id == current_user.organisation_id
        )

    # For org_user, only show their own assessments
    if current_user.role_name == "org_user":
        assessments_query = assessments_query.filter(
            models.Assessment.user_id == current_user.id
        )

    # Count total assessments
    total_assessments = assessments_query.count()

    # Get all assessments
    assessments = assessments_query.all()

    # Count completed assessments
    completed_assessments = 0
    for assessment in assessments:
        if is_assessment_completed(db, assessment.id):
            completed_assessments += 1

    # Count compliance frameworks
    compliance_frameworks = frameworks_query.count()

    # Count total users, organizations, policies, risks based on role
    if current_user.role_name == "super_admin":
        # Super admin sees all data
        total_users = db.query(models.User).count()
        total_organizations = db.query(models.Organisations).count()
        total_policies = db.query(models.Policies).count()
        total_risks = db.query(models.Risks).count()
    else:
        # Org admin and org user see only their organization's data
        total_users = db.query(models.User).filter(
            models.User.organisation_id == current_user.organisation_id
        ).count()
        total_organizations = 1  # Only their own organization
        total_policies = db.query(models.Policies).filter(
            models.Policies.organisation_id == current_user.organisation_id
        ).count()
        total_risks = db.query(models.Risks).filter(
            models.Risks.organisation_id == current_user.organisation_id
        ).count()

    return {
        "totalAssessments": total_assessments,
        "completedAssessments": completed_assessments,
        "complianceFrameworks": compliance_frameworks,
        "totalUsers": total_users,
        "totalOrganizations": total_organizations,
        "totalPolicies": total_policies,
        "totalRisks": total_risks
    }

# Pie chart data
def get_pie_chart_data(db: Session, current_user: schemas.UserBase):
    """
    Get pie chart data showing the count of in-progress and completed assessments.
    Filters data based on user's role and organization.
    """
    # Base query for assessments
    assessments_query = db.query(models.Assessment)

    # Apply role-based filtering
    if current_user.role_name != "super_admin":
        # For org_admin and org_user, only show data from their organization
        assessments_query = assessments_query.join(
            models.User, 
            models.Assessment.user_id == models.User.id
        ).filter(models.User.organisation_id == current_user.organisation_id)

    # For org_user, only show their own assessments
    if current_user.role_name == "org_user":
        assessments_query = assessments_query.filter(
            models.Assessment.user_id == current_user.id
        )

    # Get all assessments
    assessments = assessments_query.all()

    # Count in-progress and completed assessments
    in_progress = 0
    completed = 0
    for assessment in assessments:
        if is_assessment_completed(db, assessment.id):
            completed += 1
        else:
            in_progress += 1

    return {
        "inProgress": in_progress,
        "completed": completed
    }

# Frameworks
def get_dashboard_frameworks(db: Session, current_user: schemas.UserBase, skip: int = 0, limit: int = 100):
    """
    Get frameworks for the dashboard.
    Returns frameworks from the user's organization.
    """
    # Base query for frameworks
    query = db.query(models.Framework)

    # Apply role-based filtering
    if current_user.role_name != "super_admin":
        # For org_admin and org_user, only show frameworks from their organization
        query = query.filter(
            models.Framework.organisation_id == current_user.organisation_id
        )

    frameworks = query.offset(skip).limit(limit).all()

    # Convert to the format expected by the frontend
    result = []
    for framework in frameworks:
        result.append({
            "id": str(framework.id),
            "name": framework.name,
            "description": framework.description
        })

    return result

# Assessments
def get_dashboard_assessments(db: Session, current_user: schemas.UserBase, skip: int = 0, limit: int = 100):
    """
    Get assessments for the dashboard.
    Filters based on user's role and organization.
    """
    # Base query for assessments with joins to get related data
    query = db.query(
        models.Assessment,
        models.Framework.name.label("framework_name"),
        models.User.email.label("user_email"),
        models.AssessmentType.type_name.label("assessment_type_name"),
        models.Organisations.name.label("organisation_name")
    ).join(
        models.Framework,
        models.Assessment.framework_id == models.Framework.id
    ).join(
        models.User,
        models.Assessment.user_id == models.User.id
    ).join(
        models.AssessmentType,
        models.Assessment.assessment_type_id == models.AssessmentType.id
    ).join(
        models.Organisations,
        models.User.organisation_id == models.Organisations.id
    )

    # Apply role-based filtering
    if current_user.role_name == "super_admin":
        # Super admin can see all assessments
        pass
    elif current_user.role_name == "org_admin":
        # Org admin can see all assessments in their organization
        query = query.filter(models.User.organisation_id == current_user.organisation_id)
    else:
        # Regular users can only see their own assessments
        query = query.filter(models.Assessment.user_id == current_user.id)

    # Execute query with pagination
    results = query.offset(skip).limit(limit).all()

    # Convert to the format expected by the frontend
    assessments = []
    for assessment, framework_name, user_email, assessment_type_name, organisation_name in results:
        # Check if assessment is completed
        completed = is_assessment_completed(db, assessment.id)

        # Calculate progress
        progress = calculate_assessment_progress(db, assessment.id)

        assessments.append({
            "id": str(assessment.id),
            "name": assessment.name,
            "framework": framework_name,
            "framework_id": str(assessment.framework_id),
            "user": user_email,
            "user_id": str(assessment.user_id),
            "assessment_type": assessment_type_name,
            "completed": completed,
            "progress": progress,
            "organisation": organisation_name
        })

    return assessments

# User Analytics
def get_user_analytics(db: Session, current_user: schemas.UserBase):
    """
    Get user analytics including registration trends, role distribution, and status distribution.
    """
    # Base query for users
    users_query = db.query(models.User)

    # Apply role-based filtering
    if current_user.role_name != "super_admin":
        users_query = users_query.filter(models.User.organisation_id == current_user.organisation_id)

    # User role distribution
    role_distribution = []
    if current_user.role_name == "super_admin":
        roles = db.query(models.Role).all()
        for role in roles:
            count = users_query.join(models.Role).filter(models.Role.id == role.id).count()
            if count > 0:
                role_distribution.append({
                    "role": role.role_name,
                    "count": count
                })
    else:
        # For non-super-admin, just show roles in their organization
        role_counts = users_query.join(models.Role).with_entities(
            models.Role.role_name, func.count(models.User.id)
        ).group_by(models.Role.role_name).all()

        for role_name, count in role_counts:
            role_distribution.append({
                "role": role_name,
                "count": count
            })

    # User status distribution
    status_distribution = []
    status_counts = users_query.with_entities(
        models.User.status, func.count(models.User.id)
    ).group_by(models.User.status).all()

    for status, count in status_counts:
        status_distribution.append({
            "status": status or "unknown",
            "count": count
        })

    # User registration trend (last 6 months)
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta

    registration_trend = []
    current_date = datetime.now()

    for i in range(6):
        month_start = (current_date - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)

        count = users_query.filter(
            models.User.created_at >= month_start,
            models.User.created_at <= month_end
        ).count()

        registration_trend.append({
            "month": month_start.strftime("%b %Y"),
            "count": count
        })

    # Reverse to show oldest month first
    registration_trend.reverse()

    return {
        "userRegistrationTrend": registration_trend,
        "userRoleDistribution": role_distribution,
        "userStatusDistribution": status_distribution
    }

# Assessment Analytics
def get_assessment_analytics(db: Session, current_user: schemas.UserBase):
    """
    Get assessment analytics including trends, framework completion, and types distribution.
    """
    # Base query for assessments
    assessments_query = db.query(models.Assessment)

    # Apply role-based filtering
    if current_user.role_name != "super_admin":
        assessments_query = assessments_query.join(
            models.User, models.Assessment.user_id == models.User.id
        ).filter(models.User.organisation_id == current_user.organisation_id)

    if current_user.role_name == "org_user":
        assessments_query = assessments_query.filter(
            models.Assessment.user_id == current_user.id
        )

    # Assessment trend (last 6 months)
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta

    assessment_trend = []
    current_date = datetime.now()

    for i in range(6):
        month_start = (current_date - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)

        month_assessments = assessments_query.filter(
            models.Assessment.created_at >= month_start,
            models.Assessment.created_at <= month_end
        ).all()

        completed = 0
        in_progress = 0

        for assessment in month_assessments:
            if is_assessment_completed(db, assessment.id):
                completed += 1
            else:
                in_progress += 1

        assessment_trend.append({
            "month": month_start.strftime("%b %Y"),
            "completed": completed,
            "inProgress": in_progress
        })

    # Reverse to show oldest month first
    assessment_trend.reverse()

    # Framework completion rates
    framework_completion = []
    frameworks_query = db.query(models.Framework)

    if current_user.role_name != "super_admin":
        frameworks_query = frameworks_query.filter(
            models.Framework.organisation_id == current_user.organisation_id
        )

    frameworks = frameworks_query.all()

    for framework in frameworks:
        framework_assessments = assessments_query.filter(
            models.Assessment.framework_id == framework.id
        ).all()

        total = len(framework_assessments)
        completed = 0

        for assessment in framework_assessments:
            if is_assessment_completed(db, assessment.id):
                completed += 1

        if total > 0:
            framework_completion.append({
                "framework": framework.name,
                "completion": completed,
                "total": total
            })

    # Assessment by type
    assessments_by_type = []
    type_counts = assessments_query.join(models.AssessmentType).with_entities(
        models.AssessmentType.type_name, func.count(models.Assessment.id)
    ).group_by(models.AssessmentType.type_name).all()

    for type_name, count in type_counts:
        assessments_by_type.append({
            "type": type_name,
            "count": count
        })

    return {
        "assessmentTrend": assessment_trend,
        "frameworkCompletion": framework_completion,
        "assessmentsByType": assessments_by_type
    }

# Policy Risk Analytics
def get_policy_risk_analytics(db: Session, current_user: schemas.UserBase):
    """
    Get policy and risk analytics including status distributions and product types.
    """
    # Policy status distribution
    policy_status_distribution = []
    policies_query = db.query(models.Policies)

    if current_user.role_name != "super_admin":
        # Policies don't have user_id, they have organisation_id
        policies_query = policies_query.filter(
            models.Policies.organisation_id == current_user.organisation_id
        )

    # For org_user, still show all policies in their organization since policies are shared
    # Note: Policies don't have user_id, they belong to organizations

    # Get policy status counts
    policy_status_counts = policies_query.join(
        models.PolicyStatuses, models.Policies.status_id == models.PolicyStatuses.id
    ).with_entities(
        models.PolicyStatuses.status, func.count(models.Policies.id)
    ).group_by(models.PolicyStatuses.status).all()

    for status_name, count in policy_status_counts:
        policy_status_distribution.append({
            "status": status_name,
            "count": count
        })

    # Risk severity distribution
    risk_severity_distribution = []
    risks_query = db.query(models.Risks)

    # Filter risks by organization for non-super_admin users
    if current_user.role_name != "super_admin":
        risks_query = risks_query.filter(
            models.Risks.organisation_id == current_user.organisation_id
        )

    severity_counts = risks_query.join(
        models.RiskSeverity, models.Risks.risk_severity_id == models.RiskSeverity.id
    ).with_entities(
        models.RiskSeverity.risk_severity_name, func.count(models.Risks.id)
    ).group_by(models.RiskSeverity.risk_severity_name).all()

    for severity_name, count in severity_counts:
        risk_severity_distribution.append({
            "severity": severity_name,
            "count": count
        })

    # Risk status distribution
    risk_status_distribution = []
    status_counts = risks_query.join(
        models.RiskStatuses, models.Risks.risk_status_id == models.RiskStatuses.id
    ).with_entities(
        models.RiskStatuses.risk_status_name, func.count(models.Risks.id)
    ).group_by(models.RiskStatuses.risk_status_name).all()

    for status_name, count in status_counts:
        risk_status_distribution.append({
            "status": status_name,
            "count": count
        })

    return {
        "policyStatusDistribution": policy_status_distribution,
        "riskSeverityDistribution": risk_severity_distribution,
        "riskStatusDistribution": risk_status_distribution,
        "productTypeDistribution": []
    }

# Assessment Funnel Analytics
def get_assessment_funnel_analytics(db: Session, current_user: schemas.UserBase):
    """
    Get assessment completion funnel data showing user drop-off at different stages.
    """
    # Base query for assessments
    assessments_query = db.query(models.Assessment)

    # Apply role-based filtering
    if current_user.role_name != "super_admin":
        assessments_query = assessments_query.join(
            models.User, models.Assessment.user_id == models.User.id
        ).filter(models.User.organisation_id == current_user.organisation_id)

    if current_user.role_name == "org_user":
        assessments_query = assessments_query.filter(
            models.Assessment.user_id == current_user.id
        )

    # Get all assessments
    assessments = assessments_query.all()

    # Initialize funnel stages
    funnel_stages = {
        "Started": 0,
        "25% Complete": 0,
        "50% Complete": 0,
        "75% Complete": 0,
        "Completed": 0
    }

    # Analyze each assessment
    for assessment in assessments:
        progress = calculate_assessment_progress(db, assessment.id)

        # Always count as started
        funnel_stages["Started"] += 1

        # Count based on progress thresholds
        if progress >= 100:
            funnel_stages["Completed"] += 1
            funnel_stages["75% Complete"] += 1
            funnel_stages["50% Complete"] += 1
            funnel_stages["25% Complete"] += 1
        elif progress >= 75:
            funnel_stages["75% Complete"] += 1
            funnel_stages["50% Complete"] += 1
            funnel_stages["25% Complete"] += 1
        elif progress >= 50:
            funnel_stages["50% Complete"] += 1
            funnel_stages["25% Complete"] += 1
        elif progress >= 25:
            funnel_stages["25% Complete"] += 1

    # Convert to array format for frontend
    funnel_data = []
    stages_order = ["Started", "25% Complete", "50% Complete", "75% Complete", "Completed"]

    for i, stage in enumerate(stages_order):
        count = funnel_stages[stage]
        previous_count = funnel_stages[stages_order[i-1]] if i > 0 else count
        dropoff_rate = ((previous_count - count) / previous_count * 100) if previous_count > 0 else 0

        funnel_data.append({
            "stage": stage,
            "count": count,
            "dropoffRate": round(dropoff_rate, 1)
        })

    return {
        "assessmentFunnel": funnel_data
    }

# CRA DoC Readiness Metrics
def get_cra_doc_readiness(db: Session, current_user: schemas.UserBase):
    """
    Get CRA Declaration of Conformity readiness metrics.
    Calculates objective compliance and assessment completion for CRA frameworks.
    """
    # Find CRA framework(s) for the user's organisation
    frameworks_query = db.query(models.Framework).filter(
        func.lower(models.Framework.name).contains("cra")
    )

    if current_user.role_name != "super_admin":
        frameworks_query = frameworks_query.filter(
            models.Framework.organisation_id == current_user.organisation_id
        )

    cra_frameworks = frameworks_query.all()

    if not cra_frameworks:
        return {
            "objectives": {"total": 0, "compliant": 0, "partially_compliant": 0, "not_compliant": 0, "in_review": 0, "not_assessed": 0, "not_applicable": 0},
            "assessments": {"total": 0, "completed": 0, "average_progress": 0},
            "readiness_score": 0,
            "is_ready": False,
            "has_cra_framework": False
        }

    cra_framework_ids = [f.id for f in cra_frameworks]

    # Get chapters for CRA frameworks
    chapters = db.query(models.Chapters).filter(
        models.Chapters.framework_id.in_(cra_framework_ids)
    ).all()
    chapter_ids = [c.id for c in chapters]

    # Get objectives for those chapters
    # Prefer scoped objectives (scope_entity_id is not null), fall back to base objectives
    all_objectives = db.query(models.Objectives).filter(
        models.Objectives.chapter_id.in_(chapter_ids)
    ).all() if chapter_ids else []

    # Separate scoped vs base objectives per chapter
    scoped_objectives = [o for o in all_objectives if o.scope_entity_id is not None]
    base_objectives = [o for o in all_objectives if o.scope_entity_id is None]

    # Use scoped objectives if they exist, otherwise use base objectives
    objectives = scoped_objectives if scoped_objectives else base_objectives

    # Get compliance statuses for lookup
    compliance_statuses = db.query(models.ComplianceStatuses).all()
    status_map = {s.id: s.status_name.lower().replace(" ", "_") for s in compliance_statuses}

    # Count objectives by compliance status
    obj_counts = {
        "total": len(objectives),
        "compliant": 0,
        "partially_compliant": 0,
        "not_compliant": 0,
        "in_review": 0,
        "not_assessed": 0,
        "not_applicable": 0
    }

    for obj in objectives:
        if obj.compliance_status_id and obj.compliance_status_id in status_map:
            status_key = status_map[obj.compliance_status_id]
            if status_key in obj_counts:
                obj_counts[status_key] += 1
        else:
            obj_counts["not_assessed"] += 1

    # Get CRA assessments
    assessments_query = db.query(models.Assessment).filter(
        models.Assessment.framework_id.in_(cra_framework_ids)
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

    for assessment in assessments:
        progress = calculate_assessment_progress(db, assessment.id)
        total_progress += progress
        if is_assessment_completed(db, assessment.id):
            completed_assessments += 1

    average_progress = round(total_progress / total_assessments, 1) if total_assessments > 0 else 0

    # Calculate readiness score
    applicable_objectives = obj_counts["total"] - obj_counts["not_applicable"]
    objectives_compliant_pct = (obj_counts["compliant"] / applicable_objectives * 100) if applicable_objectives > 0 else 0
    assessments_completed_pct = (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0

    readiness_score = round(objectives_compliant_pct * 0.6 + assessments_completed_pct * 0.4)
    is_ready = readiness_score >= 80

    return {
        "objectives": obj_counts,
        "assessments": {
            "total": total_assessments,
            "completed": completed_assessments,
            "average_progress": average_progress
        },
        "readiness_score": readiness_score,
        "is_ready": is_ready,
        "has_cra_framework": True
    }
