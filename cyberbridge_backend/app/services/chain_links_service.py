"""
Service for importing framework chain links (risks, controls, policies, junction tables)
from pre-defined connections mappings. Allows existing production users to import links
without re-seeding their entire framework.
"""
import io
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import models
from app.seeds.cra_seed import CraSeed
from app.constants.cra_connections import CRA_CONNECTIONS
from app.constants.gdpr_connections import GDPR_CONNECTIONS
from app.constants.soc_2_connections import SOC2_CONNECTIONS
from app.constants.iso_27001_2022_connections import ISO_27001_2022_CONNECTIONS
from app.constants.nis2_directive_connections import NIS2_DIRECTIVE_CONNECTIONS
from app.constants.nist_csf_2_0_connections import NIST_CSF_2_0_CONNECTIONS
from app.constants.cmmc_2_0_connections import CMMC_2_0_CONNECTIONS
from app.constants.dora_2022_connections import DORA_2022_CONNECTIONS
from app.constants.pci_dss_v4_0_connections import PCI_DSS_V4_0_CONNECTIONS
from app.constants.ftc_safeguards_connections import FTC_SAFEGUARDS_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)

# Registry of which frameworks have connections mappings.
# - connections:              the dict mapping objective titles → {risks, controls, policies}
# - composite_key_chapters:   chapter titles that require "ChapterTitle::ObjectiveTitle" keys
# - control_set_strategy:     "baseline_only" or "baseline_and_iso" (ISO legacy for A-prefix codes)
FRAMEWORK_CONNECTIONS_REGISTRY = {
    "CRA": {
        "connections": CRA_CONNECTIONS,
        "composite_key_chapters": {"ANNEX I", "Vulnerability Handling"},
        "control_set_strategy": "baseline_only",
    },
    "GDPR": {
        "connections": GDPR_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_and_iso",
    },
    "SOC 2": {
        "connections": SOC2_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_and_iso",
    },
    "ISO 27001 2022": {
        "connections": ISO_27001_2022_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_only",
    },
    "NIS2 Directive": {
        "connections": NIS2_DIRECTIVE_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_only",
    },
    "NIST CSF 2.0": {
        "connections": NIST_CSF_2_0_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_only",
    },
    "CMMC 2.0": {
        "connections": CMMC_2_0_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_only",
    },
    "DORA 2022": {
        "connections": DORA_2022_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_only",
    },
    "PCI DSS v4.0": {
        "connections": PCI_DSS_V4_0_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_only",
    },
    "FTC Safeguards": {
        "connections": FTC_SAFEGUARDS_CONNECTIONS,
        "composite_key_chapters": set(),
        "control_set_strategy": "baseline_only",
    },
}

# Registry mapping framework names to their seed data for objective field comparisons.
# - get_data:               callable returning the objectives data list
# - composite_key_chapters: chapter titles that require "ChapterTitle::ObjectiveTitle" keys
# - data_format:            "nested" = { chapter_title, objectives: [...] }
# - field_mapping:          seed field name → DB column name
FRAMEWORK_OBJECTIVES_REGISTRY = {
    "CRA": {
        "get_data": CraSeed._get_objectives_data,
        "composite_key_chapters": {"ANNEX I", "Vulnerability Handling"},
        "data_format": "nested",
        "field_mapping": {
            "needs": "objective_utilities",
            "description": "requirement_description",
            "subchapter": "subchapter",
            "applicable_operators": "applicable_operators",
        }
    },
}


def has_mapping(framework_name: str) -> bool:
    """Check if a framework has a connections mapping in the registry."""
    return framework_name in FRAMEWORK_CONNECTIONS_REGISTRY


def is_already_imported(db: Session, framework_id: str) -> bool:
    """Check if chain links have already been imported for a framework
    by looking for any ObjectiveControl records tied to the framework's objectives."""
    exists = (
        db.query(models.ObjectiveControl.objective_id)
        .join(models.Objectives, models.ObjectiveControl.objective_id == models.Objectives.id)
        .join(models.Chapters, models.Objectives.chapter_id == models.Chapters.id)
        .filter(models.Chapters.framework_id == framework_id)
        .first()
    )
    return exists is not None


def get_framework_entity_counts(db: Session, framework_id: str) -> dict:
    """Get framework-scoped entity counts (risks, controls, policies, objectives)
    by querying junction tables tied to the framework's objectives."""
    chapter_ids = [
        row.id for row in
        db.query(models.Chapters.id).filter(models.Chapters.framework_id == framework_id).all()
    ]
    if not chapter_ids:
        return {"objectives": 0, "risks": 0, "controls": 0, "policies": 0}

    objective_ids = [
        row.id for row in
        db.query(models.Objectives.id).filter(models.Objectives.chapter_id.in_(chapter_ids)).all()
    ]
    objectives_count = len(objective_ids)
    if not objective_ids:
        return {"objectives": objectives_count, "risks": 0, "controls": 0, "policies": 0}

    risks_count = db.query(func.count(func.distinct(models.ObjectiveRisk.risk_id))).filter(
        models.ObjectiveRisk.objective_id.in_(objective_ids)
    ).scalar() or 0

    controls_count = db.query(func.count(func.distinct(models.ObjectiveControl.control_id))).filter(
        models.ObjectiveControl.objective_id.in_(objective_ids)
    ).scalar() or 0

    policies_count = db.query(func.count(func.distinct(models.PolicyFrameworks.policy_id))).filter(
        models.PolicyFrameworks.framework_id == framework_id
    ).scalar() or 0

    return {
        "objectives": objectives_count,
        "risks": risks_count,
        "controls": controls_count,
        "policies": policies_count,
    }


def import_chain_links(db: Session, framework_id: str, organisation_id: str) -> dict:
    """
    Import chain links for a framework from its connections mapping.
    Creates org-level risks, controls, policies and wires 6 junction tables.

    Returns a dict with counts suitable for ChainLinksImportResult.
    """
    import mammoth

    # Load framework
    framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
    if not framework:
        raise ValueError("Framework not found")

    config = FRAMEWORK_CONNECTIONS_REGISTRY.get(framework.name)
    if not config:
        raise ValueError(f"No chain links mapping available for framework '{framework.name}'")

    connections = config["connections"]
    composite_key_chapters = config["composite_key_chapters"]
    control_set_strategy = config["control_set_strategy"]

    warnings = []

    # ── Step 1: Look up defaults ──
    medium_severity = db.query(models.RiskSeverity).filter(
        models.RiskSeverity.risk_severity_name == "Medium"
    ).first()
    accept_status = db.query(models.RiskStatuses).filter(
        models.RiskStatuses.risk_status_name == "Accept"
    ).first()
    not_implemented = db.query(models.ControlStatus).filter(
        models.ControlStatus.status_name == "Not Implemented"
    ).first()
    draft_status = db.query(models.PolicyStatuses).filter(
        models.PolicyStatuses.status == "Draft"
    ).first()
    default_asset_category = db.query(models.AssetCategories).filter(
        models.AssetCategories.name == "Software"
    ).first()
    if not default_asset_category:
        default_asset_category = db.query(models.AssetCategories).first()

    if not all([medium_severity, accept_status, not_implemented, draft_status]):
        raise ValueError("Missing lookup defaults (RiskSeverity/RiskStatuses/ControlStatus/PolicyStatuses)")

    # Collect all unique entity references from the mapping
    all_risk_names = set()
    all_control_codes = set()
    all_policy_codes = set()
    for conn in connections.values():
        all_risk_names.update(conn["risks"])
        all_control_codes.update(conn["controls"])
        all_policy_codes.update(conn["policies"])

    org = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
    if not org:
        raise ValueError("Organisation not found")

    # ── Step 2: Create org-level risks (idempotent) ──
    risk_name_to_id = {}
    risks_created = 0

    # Fetch risk templates by name
    risk_templates = db.query(models.RiskTemplate).filter(
        models.RiskTemplate.risk_category_name.in_(all_risk_names)
    ).all()
    risk_template_map = {rt.risk_category_name: rt for rt in risk_templates}

    # Prefer asset category from risk categories when available
    risk_name_to_asset_category_id = {}
    risk_category_rows = db.query(
        models.RiskCategories.risk_category_name,
        models.RiskCategories.asset_category_id
    ).filter(
        models.RiskCategories.risk_category_name.in_(all_risk_names),
        models.RiskCategories.asset_category_id.isnot(None)
    ).all()
    for risk_name, asset_category_id in risk_category_rows:
        if risk_name not in risk_name_to_asset_category_id:
            risk_name_to_asset_category_id[risk_name] = asset_category_id

    # Check existing org risks
    existing_risks = db.query(models.Risks).filter(
        models.Risks.organisation_id == org.id,
        models.Risks.risk_category_name.in_(all_risk_names)
    ).all()
    for r in existing_risks:
        if not r.asset_category_id:
            r.asset_category_id = (
                risk_name_to_asset_category_id.get(r.risk_category_name)
                or (default_asset_category.id if default_asset_category else None)
            )
        risk_name_to_id[r.risk_category_name] = r.id

    # Determine next RSK code for this org
    max_code_row = db.query(models.Risks.risk_code).filter(
        models.Risks.organisation_id == org.id,
        models.Risks.risk_code.isnot(None)
    ).all()
    existing_codes = [r[0] for r in max_code_row if r[0] and r[0].startswith("RSK-")]
    next_rsk_num = 1
    if existing_codes:
        nums = []
        for c in existing_codes:
            try:
                nums.append(int(c.split("-")[1]))
            except (IndexError, ValueError):
                pass
        if nums:
            next_rsk_num = max(nums) + 1

    for risk_name in sorted(all_risk_names):
        if risk_name in risk_name_to_id:
            continue
        tmpl = risk_template_map.get(risk_name)
        asset_category_id = (
            risk_name_to_asset_category_id.get(risk_name)
            or (default_asset_category.id if default_asset_category else None)
        )
        risk_code = f"RSK-{next_rsk_num}"
        next_rsk_num += 1
        risk = models.Risks(
            asset_category_id=asset_category_id,
            risk_code=risk_code,
            risk_category_name=risk_name,
            risk_category_description=tmpl.risk_category_description if tmpl else "",
            risk_potential_impact=tmpl.risk_potential_impact if tmpl else "",
            risk_control=tmpl.risk_control if tmpl else "",
            likelihood=medium_severity.id,
            residual_risk=medium_severity.id,
            risk_severity_id=medium_severity.id,
            risk_status_id=accept_status.id,
            organisation_id=org.id,
        )
        db.add(risk)
        db.flush()
        risk_name_to_id[risk_name] = risk.id
        risks_created += 1

    logger.info(f"Chain links import: {len(risk_name_to_id)} risks ready ({risks_created} new)")

    # ── Step 3: Create org-level controls (idempotent) ──
    control_code_to_id = {}
    controls_created = 0

    # Get or create Baseline ControlSet
    baseline_set = db.query(models.ControlSet).filter(
        models.ControlSet.name == "Baseline Controls",
        models.ControlSet.organisation_id == org.id
    ).first()
    if not baseline_set:
        baseline_set = models.ControlSet(
            name="Baseline Controls",
            description="General baseline controls covering HR, Governance, Risk Management, Security, and Compliance",
            organisation_id=org.id
        )
        db.add(baseline_set)
        db.flush()

    iso_set = None
    if control_set_strategy == "baseline_and_iso":
        iso_set = db.query(models.ControlSet).filter(
            models.ControlSet.name == "ISO 27001 Controls (Legacy)",
            models.ControlSet.organisation_id == org.id
        ).first()
        if not iso_set:
            iso_set = models.ControlSet(
                name="ISO 27001 Controls (Legacy)",
                description="ISO/IEC 27001 controls - Information security management systems (legacy format)",
                organisation_id=org.id
            )
            db.add(iso_set)
            db.flush()

    # Fetch control templates
    control_templates = db.query(models.ControlTemplate).filter(
        models.ControlTemplate.code.in_(all_control_codes)
    ).all()
    ctrl_template_map = {ct.code: ct for ct in control_templates}

    # Check existing org controls
    existing_controls = db.query(models.Control).filter(
        models.Control.organisation_id == org.id,
        models.Control.code.in_(all_control_codes)
    ).all()
    for c in existing_controls:
        control_code_to_id[c.code] = c.id

    for code in sorted(all_control_codes):
        if code in control_code_to_id:
            continue
        tmpl = ctrl_template_map.get(code)
        # A-prefix codes go to ISO legacy set when using baseline_and_iso strategy
        if control_set_strategy == "baseline_and_iso" and iso_set and code.startswith("A"):
            ctrl_set_id = iso_set.id
        else:
            ctrl_set_id = baseline_set.id
        control = models.Control(
            code=code,
            name=tmpl.name if tmpl else code,
            description=tmpl.description if tmpl else "",
            control_set_id=ctrl_set_id,
            control_status_id=not_implemented.id,
            organisation_id=org.id,
        )
        db.add(control)
        db.flush()
        control_code_to_id[code] = control.id
        controls_created += 1

    logger.info(f"Chain links import: {len(control_code_to_id)} controls ready ({controls_created} new)")

    # ── Step 4: Create org-level policies (idempotent) ──
    policy_code_to_id = {}
    policies_created = 0

    # Check existing org policies
    existing_policies = db.query(models.Policies).filter(
        models.Policies.organisation_id == org.id,
        models.Policies.policy_code.in_(all_policy_codes)
    ).all()
    for p in existing_policies:
        policy_code_to_id[p.policy_code] = p.id

    # Fetch policy templates
    policy_templates = db.query(models.PolicyTemplate).filter(
        models.PolicyTemplate.policy_code.in_(all_policy_codes)
    ).all()
    pol_template_map = {pt.policy_code: pt for pt in policy_templates}

    for pol_code in sorted(all_policy_codes, key=lambda x: int(x.split("-")[1])):
        if pol_code in policy_code_to_id:
            continue
        tmpl = pol_template_map.get(pol_code)
        body_text = ""
        if tmpl and tmpl.content_docx:
            try:
                docx_stream = io.BytesIO(tmpl.content_docx)
                result = mammoth.convert_to_html(docx_stream)
                body_text = convert_html_to_plain_text(result.value)
            except Exception as conv_err:
                logger.warning(f"Chain links import: docx conversion failed for {pol_code}: {conv_err}")
                warnings.append(f"Policy {pol_code}: docx conversion failed")
        policy = models.Policies(
            title=tmpl.title if tmpl else pol_code,
            policy_code=pol_code,
            status_id=draft_status.id,
            body=body_text,
            organisation_id=org.id,
        )
        db.add(policy)
        db.flush()
        policy_code_to_id[pol_code] = policy.id
        policies_created += 1

    logger.info(f"Chain links import: {len(policy_code_to_id)} policies ready ({policies_created} new)")

    # ── Step 5: Create connections (6 junction tables) ──
    # Build objective lookup
    chapters = db.query(models.Chapters).filter(
        models.Chapters.framework_id == framework_id
    ).all()
    chapter_id_to_title = {ch.id: ch.title for ch in chapters}

    # Only use base (unscoped) objectives for chain link connections
    objectives = db.query(models.Objectives).filter(
        models.Objectives.chapter_id.in_([ch.id for ch in chapters]),
        models.Objectives.scope_id.is_(None),
        models.Objectives.scope_entity_id.is_(None)
    ).all()

    obj_key_to_id = {}
    for obj in objectives:
        ch_title = chapter_id_to_title.get(obj.chapter_id, "")
        if ch_title in composite_key_chapters:
            key = f"{ch_title}::{obj.title}"
        else:
            key = obj.title
        obj_key_to_id[key] = obj.id

    # Track unique PolicyFramework links
    policy_framework_pairs = set()

    obj_risk_count = 0
    obj_ctrl_count = 0
    pol_obj_count = 0
    ctrl_risk_count = 0
    ctrl_pol_count = 0
    planned_control_risk_pairs = set()
    planned_control_policy_pairs = set()

    for obj_key, conn in connections.items():
        obj_id = obj_key_to_id.get(obj_key)
        if not obj_id:
            warnings.append(f"Objective not found for key '{obj_key}'")
            continue

        resolved_risk_ids = []
        resolved_control_ids = []
        resolved_policy_ids = []

        # ObjectiveRisk links
        for risk_name in conn["risks"]:
            risk_id = risk_name_to_id.get(risk_name)
            if not risk_id:
                continue
            resolved_risk_ids.append(risk_id)
            existing = db.query(models.ObjectiveRisk).filter_by(
                objective_id=obj_id, risk_id=risk_id
            ).first()
            if not existing:
                db.add(models.ObjectiveRisk(objective_id=obj_id, risk_id=risk_id))
                obj_risk_count += 1

        # ObjectiveControl links
        for ctrl_code in conn["controls"]:
            ctrl_id = control_code_to_id.get(ctrl_code)
            if not ctrl_id:
                continue
            resolved_control_ids.append(ctrl_id)
            existing = db.query(models.ObjectiveControl).filter_by(
                objective_id=obj_id, control_id=ctrl_id
            ).first()
            if not existing:
                db.add(models.ObjectiveControl(objective_id=obj_id, control_id=ctrl_id))
                obj_ctrl_count += 1

        # PolicyObjective links
        for pol_code in conn["policies"]:
            pol_id = policy_code_to_id.get(pol_code)
            if not pol_id:
                continue
            resolved_policy_ids.append(pol_id)
            existing = db.query(models.PolicyObjectives).filter_by(
                policy_id=pol_id, objective_id=obj_id
            ).first()
            if not existing:
                db.add(models.PolicyObjectives(policy_id=pol_id, objective_id=obj_id))
                pol_obj_count += 1
            policy_framework_pairs.add((pol_id, framework.id))

        # Derive ControlRisk links
        for ctrl_id in resolved_control_ids:
            for risk_id in resolved_risk_ids:
                pair = (ctrl_id, risk_id, framework.id)
                if pair in planned_control_risk_pairs:
                    continue
                existing = db.query(models.ControlRisk).filter_by(
                    control_id=ctrl_id, risk_id=risk_id, framework_id=framework.id
                ).first()
                if not existing:
                    db.add(models.ControlRisk(control_id=ctrl_id, risk_id=risk_id, framework_id=framework.id))
                    ctrl_risk_count += 1
                planned_control_risk_pairs.add(pair)

        # Derive ControlPolicy links
        for ctrl_id in resolved_control_ids:
            for pol_id in resolved_policy_ids:
                pair = (ctrl_id, pol_id, framework.id)
                if pair in planned_control_policy_pairs:
                    continue
                existing = db.query(models.ControlPolicy).filter_by(
                    control_id=ctrl_id, policy_id=pol_id, framework_id=framework.id
                ).first()
                if not existing:
                    db.add(models.ControlPolicy(control_id=ctrl_id, policy_id=pol_id, framework_id=framework.id))
                    ctrl_pol_count += 1
                planned_control_policy_pairs.add(pair)

    # PolicyFramework links
    pf_count = 0
    for pol_id, fw_id in policy_framework_pairs:
        existing = db.query(models.PolicyFrameworks).filter_by(
            policy_id=pol_id, framework_id=fw_id
        ).first()
        if not existing:
            db.add(models.PolicyFrameworks(policy_id=pol_id, framework_id=fw_id))
            pf_count += 1

    db.flush()

    links_created = {
        "objective_risk": obj_risk_count,
        "objective_control": obj_ctrl_count,
        "policy_objective": pol_obj_count,
        "control_risk": ctrl_risk_count,
        "control_policy": ctrl_pol_count,
        "policy_framework": pf_count,
    }
    total_links = sum(links_created.values())

    logger.info(
        f"Chain links import complete for '{framework.name}': "
        f"{obj_risk_count} objective-risk, {obj_ctrl_count} objective-control, "
        f"{pol_obj_count} policy-objective, {ctrl_risk_count} control-risk, "
        f"{ctrl_pol_count} control-policy, {pf_count} policy-framework"
    )

    return {
        "success": True,
        "framework_name": framework.name,
        "message": f"Successfully imported {total_links} chain links for {framework.name}",
        "risks_created": risks_created,
        "controls_created": controls_created,
        "policies_created": policies_created,
        "links_created": links_created,
        "warnings": warnings,
    }


def _build_seed_objective_map(framework_name: str) -> dict | None:
    """Build a { composite_key → { field_name: value } } map from seed data
    for the given framework.  Returns None if no objectives registry entry."""
    obj_config = FRAMEWORK_OBJECTIVES_REGISTRY.get(framework_name)
    if not obj_config:
        return None

    seed_data = obj_config["get_data"]()
    composite_key_chapters = obj_config["composite_key_chapters"]
    field_mapping = obj_config["field_mapping"]
    result = {}

    if obj_config["data_format"] == "nested":
        for chapter in seed_data:
            ch_title = chapter["chapter_title"]
            for obj in chapter["objectives"]:
                if ch_title in composite_key_chapters:
                    key = f"{ch_title}::{obj['title']}"
                else:
                    key = obj["title"]
                fields = {}
                for seed_field, db_col in field_mapping.items():
                    if seed_field in obj:
                        fields[db_col] = obj[seed_field]
                result[key] = fields

    return result


def check_chain_links_updates(db: Session, framework_id: str, organisation_id: str) -> dict:
    """
    Read-only check: compare DB state against seed files and connections mapping.
    Returns counts of missing entities, missing links, and objective field differences.
    """
    framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
    if not framework:
        raise ValueError("Framework not found")

    config = FRAMEWORK_CONNECTIONS_REGISTRY.get(framework.name)
    if not config:
        raise ValueError(f"No chain links mapping available for framework '{framework.name}'")

    connections = config["connections"]
    composite_key_chapters = config["composite_key_chapters"]

    # ── Count missing entities ──
    all_risk_names = set()
    all_control_codes = set()
    all_policy_codes = set()
    for conn in connections.values():
        all_risk_names.update(conn["risks"])
        all_control_codes.update(conn["controls"])
        all_policy_codes.update(conn["policies"])

    existing_risk_names = set(
        r[0] for r in db.query(models.Risks.risk_category_name).filter(
            models.Risks.organisation_id == organisation_id,
            models.Risks.risk_category_name.in_(all_risk_names)
        ).all()
    )
    existing_control_codes = set(
        c[0] for c in db.query(models.Control.code).filter(
            models.Control.organisation_id == organisation_id,
            models.Control.code.in_(all_control_codes)
        ).all()
    )
    existing_policy_codes = set(
        p[0] for p in db.query(models.Policies.policy_code).filter(
            models.Policies.organisation_id == organisation_id,
            models.Policies.policy_code.in_(all_policy_codes)
        ).all()
    )

    new_risks = len(all_risk_names - existing_risk_names)
    new_controls = len(all_control_codes - existing_control_codes)
    new_policies = len(all_policy_codes - existing_policy_codes)

    # ── Count missing links ──
    chapters = db.query(models.Chapters).filter(
        models.Chapters.framework_id == framework_id
    ).all()
    chapter_id_to_title = {ch.id: ch.title for ch in chapters}

    # Only use base (unscoped) objectives for chain link checks
    objectives = db.query(models.Objectives).filter(
        models.Objectives.chapter_id.in_([ch.id for ch in chapters]),
        models.Objectives.scope_id.is_(None),
        models.Objectives.scope_entity_id.is_(None)
    ).all()

    obj_key_to_id = {}
    obj_key_to_obj = {}
    for obj in objectives:
        ch_title = chapter_id_to_title.get(obj.chapter_id, "")
        if ch_title in composite_key_chapters:
            key = f"{ch_title}::{obj.title}"
        else:
            key = obj.title
        obj_key_to_id[key] = obj.id
        obj_key_to_obj[key] = obj

    # Build existing entity lookups (name/code → id)
    risk_name_to_id = {
        r.risk_category_name: r.id for r in db.query(models.Risks).filter(
            models.Risks.organisation_id == organisation_id,
            models.Risks.risk_category_name.in_(all_risk_names)
        ).all()
    }
    control_code_to_id = {
        c.code: c.id for c in db.query(models.Control).filter(
            models.Control.organisation_id == organisation_id,
            models.Control.code.in_(all_control_codes)
        ).all()
    }
    policy_code_to_id = {
        p.policy_code: p.id for p in db.query(models.Policies).filter(
            models.Policies.organisation_id == organisation_id,
            models.Policies.policy_code.in_(all_policy_codes)
        ).all()
    }

    new_obj_risk = 0
    new_obj_ctrl = 0
    new_pol_obj = 0
    new_ctrl_risk = 0
    new_ctrl_pol = 0
    new_pol_fw = 0
    policy_framework_codes = set()
    planned_cr = set()
    planned_cp = set()

    for obj_key, conn in connections.items():
        obj_id = obj_key_to_id.get(obj_key)
        if not obj_id:
            continue

        conn_risk_names = []
        conn_control_codes = []
        conn_policy_codes = []

        for risk_name in conn["risks"]:
            conn_risk_names.append(risk_name)
            risk_id = risk_name_to_id.get(risk_name)
            if not risk_id:
                new_obj_risk += 1
            elif not db.query(models.ObjectiveRisk).filter_by(
                objective_id=obj_id, risk_id=risk_id
            ).first():
                new_obj_risk += 1

        for ctrl_code in conn["controls"]:
            conn_control_codes.append(ctrl_code)
            ctrl_id = control_code_to_id.get(ctrl_code)
            if not ctrl_id:
                new_obj_ctrl += 1
            elif not db.query(models.ObjectiveControl).filter_by(
                objective_id=obj_id, control_id=ctrl_id
            ).first():
                new_obj_ctrl += 1

        for pol_code in conn["policies"]:
            conn_policy_codes.append(pol_code)
            pol_id = policy_code_to_id.get(pol_code)
            if not pol_id:
                new_pol_obj += 1
            elif not db.query(models.PolicyObjectives).filter_by(
                policy_id=pol_id, objective_id=obj_id
            ).first():
                new_pol_obj += 1
            policy_framework_codes.add(pol_code)

        for ctrl_code in conn_control_codes:
            for risk_name in conn_risk_names:
                pair = (ctrl_code, risk_name)
                if pair in planned_cr:
                    continue
                ctrl_id = control_code_to_id.get(ctrl_code)
                risk_id = risk_name_to_id.get(risk_name)
                if not ctrl_id or not risk_id:
                    new_ctrl_risk += 1
                elif not db.query(models.ControlRisk).filter_by(
                    control_id=ctrl_id, risk_id=risk_id, framework_id=framework_id
                ).first():
                    new_ctrl_risk += 1
                planned_cr.add(pair)

        for ctrl_code in conn_control_codes:
            for pol_code in conn_policy_codes:
                pair = (ctrl_code, pol_code)
                if pair in planned_cp:
                    continue
                ctrl_id = control_code_to_id.get(ctrl_code)
                pol_id = policy_code_to_id.get(pol_code)
                if not ctrl_id or not pol_id:
                    new_ctrl_pol += 1
                elif not db.query(models.ControlPolicy).filter_by(
                    control_id=ctrl_id, policy_id=pol_id, framework_id=framework_id
                ).first():
                    new_ctrl_pol += 1
                planned_cp.add(pair)

    for pol_code in policy_framework_codes:
        pol_id = policy_code_to_id.get(pol_code)
        if not pol_id:
            new_pol_fw += 1
        elif not db.query(models.PolicyFrameworks).filter_by(
            policy_id=pol_id, framework_id=framework_id
        ).first():
            new_pol_fw += 1

    new_links = {
        "objective_risk": new_obj_risk,
        "objective_control": new_obj_ctrl,
        "policy_objective": new_pol_obj,
        "control_risk": new_ctrl_risk,
        "control_policy": new_ctrl_pol,
        "policy_framework": new_pol_fw,
    }

    # ── Compare objective fields with seed data ──
    objective_field_changes = []
    seed_map = _build_seed_objective_map(framework.name)
    if seed_map:
        for obj_key, seed_fields in seed_map.items():
            obj = obj_key_to_obj.get(obj_key)
            if not obj:
                continue
            changes = {}
            for db_col, seed_val in seed_fields.items():
                db_val = getattr(obj, db_col, None)
                # Normalize None → "" for comparison
                norm_seed = seed_val if seed_val is not None else ""
                norm_db = db_val if db_val is not None else ""
                if str(norm_seed) != str(norm_db):
                    changes[db_col] = {"old": str(norm_db), "new": str(norm_seed)}
            if changes:
                objective_field_changes.append({
                    "objective_title": obj.title,
                    "objective_key": obj_key,
                    "changes": changes,
                })

    has_updates = (
        new_risks > 0 or new_controls > 0 or new_policies > 0
        or any(v > 0 for v in new_links.values())
        or len(objective_field_changes) > 0
    )

    return {
        "has_updates": has_updates,
        "new_risks": new_risks,
        "new_controls": new_controls,
        "new_policies": new_policies,
        "new_links": new_links,
        "objective_field_changes": objective_field_changes,
        "framework_name": framework.name,
    }


def apply_chain_links_updates(db: Session, framework_id: str, organisation_id: str) -> dict:
    """
    Apply chain link updates: import missing entities/links (via import_chain_links)
    and update objective fields that differ from seed data.
    """
    # 1. Import missing entities and links (idempotent)
    import_result = import_chain_links(db, framework_id, organisation_id)

    # 2. Update objective fields from seed data
    framework = db.query(models.Framework).filter(models.Framework.id == framework_id).first()
    seed_map = _build_seed_objective_map(framework.name) if framework else None
    objectives_updated = 0
    warnings = list(import_result.get("warnings", []))

    if seed_map and framework:
        config = FRAMEWORK_CONNECTIONS_REGISTRY[framework.name]
        composite_key_chapters = config["composite_key_chapters"]

        chapters = db.query(models.Chapters).filter(
            models.Chapters.framework_id == framework_id
        ).all()
        chapter_id_to_title = {ch.id: ch.title for ch in chapters}

        # Only use base (unscoped) objectives for field updates
        objectives = db.query(models.Objectives).filter(
            models.Objectives.chapter_id.in_([ch.id for ch in chapters]),
            models.Objectives.scope_id.is_(None),
            models.Objectives.scope_entity_id.is_(None)
        ).all()

        obj_key_to_obj = {}
        for obj in objectives:
            ch_title = chapter_id_to_title.get(obj.chapter_id, "")
            if ch_title in composite_key_chapters:
                key = f"{ch_title}::{obj.title}"
            else:
                key = obj.title
            obj_key_to_obj[key] = obj

        for obj_key, seed_fields in seed_map.items():
            obj = obj_key_to_obj.get(obj_key)
            if not obj:
                continue
            updated = False
            for db_col, seed_val in seed_fields.items():
                db_val = getattr(obj, db_col, None)
                norm_seed = seed_val if seed_val is not None else ""
                norm_db = db_val if db_val is not None else ""
                if str(norm_seed) != str(norm_db):
                    setattr(obj, db_col, seed_val)
                    updated = True
            if updated:
                objectives_updated += 1

        db.flush()

    total_links = sum(import_result["links_created"].values())
    total_changes = (
        import_result["risks_created"] + import_result["controls_created"]
        + import_result["policies_created"] + total_links + objectives_updated
    )

    return {
        "success": True,
        "framework_name": import_result["framework_name"],
        "message": f"Successfully applied {total_changes} updates for {import_result['framework_name']}",
        "risks_created": import_result["risks_created"],
        "controls_created": import_result["controls_created"],
        "policies_created": import_result["policies_created"],
        "links_created": import_result["links_created"],
        "objectives_updated": objectives_updated,
        "warnings": warnings,
    }
