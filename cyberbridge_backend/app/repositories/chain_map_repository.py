from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def get_chain_map_connections(db: Session, current_user, framework_id):
    """
    Fetch all chain map connections in 4 bulk queries instead of N+1 per-entity calls.
    Returns {assetRisks, riskControls, controlPolicies, policyObjectives} as Record<str, list[str]>.
    """
    org_id = str(current_user.organisation_id)
    fw_id = str(framework_id)
    is_super_admin = current_user.role_name == "super_admin"

    # 1. asset_risks: grouped by asset_id (no framework filter)
    asset_risks_sql = text("""
        SELECT CAST(ar.asset_id AS text), CAST(ar.risk_id AS text)
        FROM asset_risks ar
        JOIN assets a ON a.id = ar.asset_id
        WHERE (:is_super_admin OR a.organisation_id = CAST(:org_id AS uuid))
    """)
    asset_risks_rows = db.execute(asset_risks_sql, {
        "org_id": org_id,
        "is_super_admin": is_super_admin,
    }).fetchall()

    asset_risks = defaultdict(list)
    for asset_id, risk_id in asset_risks_rows:
        asset_risks[asset_id].append(risk_id)

    # 2. control_risks: grouped by risk_id, filtered by framework_id
    risk_controls_sql = text("""
        SELECT CAST(cr.risk_id AS text), CAST(cr.control_id AS text)
        FROM control_risks cr
        JOIN controls c ON c.id = cr.control_id
        WHERE cr.framework_id = CAST(:fw_id AS uuid)
          AND (:is_super_admin OR c.organisation_id = CAST(:org_id AS uuid))
    """)
    risk_controls_rows = db.execute(risk_controls_sql, {
        "fw_id": fw_id,
        "org_id": org_id,
        "is_super_admin": is_super_admin,
    }).fetchall()

    risk_controls = defaultdict(list)
    for risk_id, control_id in risk_controls_rows:
        risk_controls[risk_id].append(control_id)

    # 3. control_policies: grouped by control_id, filtered by framework_id
    control_policies_sql = text("""
        SELECT CAST(cp.control_id AS text), CAST(cp.policy_id AS text)
        FROM control_policies cp
        JOIN policies p ON p.id = cp.policy_id
        WHERE cp.framework_id = CAST(:fw_id AS uuid)
          AND (:is_super_admin OR p.organisation_id = CAST(:org_id AS uuid))
    """)
    control_policies_rows = db.execute(control_policies_sql, {
        "fw_id": fw_id,
        "org_id": org_id,
        "is_super_admin": is_super_admin,
    }).fetchall()

    control_policies = defaultdict(list)
    for control_id, policy_id in control_policies_rows:
        control_policies[control_id].append(policy_id)

    # 4. policy_objectives: grouped by policy_id, filtered by framework via chapters
    policy_objectives_sql = text("""
        SELECT CAST(po.policy_id AS text), CAST(po.objective_id AS text)
        FROM policy_objectives po
        JOIN objectives o ON o.id = po.objective_id
        JOIN chapters ch ON ch.id = o.chapter_id
        JOIN policies p ON p.id = po.policy_id
        WHERE ch.framework_id = CAST(:fw_id AS uuid)
          AND (:is_super_admin OR p.organisation_id = CAST(:org_id AS uuid))
    """)
    policy_objectives_rows = db.execute(policy_objectives_sql, {
        "fw_id": fw_id,
        "org_id": org_id,
        "is_super_admin": is_super_admin,
    }).fetchall()

    policy_objectives = defaultdict(list)
    for policy_id, objective_id in policy_objectives_rows:
        policy_objectives[policy_id].append(objective_id)

    return {
        "assetRisks": dict(asset_risks),
        "riskControls": dict(risk_controls),
        "controlPolicies": dict(control_policies),
        "policyObjectives": dict(policy_objectives),
    }
