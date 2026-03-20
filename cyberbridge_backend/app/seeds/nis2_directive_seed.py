# app/seeds/nis2_directive_seed.py
import io
import logging
import re
from .base_seed import BaseSeed
from app.models import models
from app.constants.nis2_directive_connections import NIS2_DIRECTIVE_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class NIS2DirectiveSeed(BaseSeed):
    """Seed NIS2 Directive framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating NIS2 Directive framework and questions...")

        # Get default organization (assuming first one is default)
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]
        audit_assessment_type = self.assessment_types["audit"]

        # Create NIS2 Directive Framework
        nis2_directive_framework, created = self.get_or_create(
            models.Framework,
            {"name": "NIS2 Directive", "organisation_id": default_org.id},
            {
                "name": "NIS2 Directive",
                "description": "NIS2 Directive (EU) 2022/2555 cybersecurity compliance framework for network and information systems",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("NIS2 Directive framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == nis2_directive_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == nis2_directive_framework.id
            ).all()

            logger.info(f"Found existing NIS2 Directive framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            # Keep links in sync even when framework/objectives already exist.
            if not self.skip_wire_connections:
                self._wire_connections(nis2_directive_framework, default_org, existing_objectives)
            self.db.commit()

            return {
                "framework": nis2_directive_framework,
                "conformity_questions": existing_questions,
                "objectives": existing_objectives
            }

        # Parse NIS2 Directive data from the Excel file
        nis2_directive_data = self._parse_nis2_directive_data()

        # Extract unique questions from the seed data (preserve order)
        logger.info("Extracting unique conformity questions from seed data...")
        seen_questions = set()
        unique_questions_list = []
        for item in nis2_directive_data:
            for q in item['conformity_questions']:
                if q and q not in seen_questions:
                    seen_questions.add(q)
                    unique_questions_list.append(q)

        logger.info(f"Found {len(unique_questions_list)} unique conformity questions")

        # Extract unique objectives from the seed data (preserve order)
        logger.info("Extracting unique objectives from seed data...")
        seen_objectives = {}
        unique_objectives_data = []
        for item in nis2_directive_data:
            obj_title = item['objective_title']
            if obj_title not in seen_objectives:
                seen_objectives[obj_title] = True
                unique_objectives_data.append(item)

        logger.info(f"Found {len(unique_objectives_data)} unique objectives")

        # Create conformity questions (only unique ones)
        conformity_questions = []
        question_order = 1

        for conf_q_text in unique_questions_list:
            # Always create new questions for each framework (no get_or_create)
            question = models.Question(
                text=conf_q_text,
                description="NIS2 Directive conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=nis2_directive_framework.id,
                question_id=question.id,
                order=question_order
            )
            self.db.add(framework_question)

            question_order += 1

        # Note: Audit questions are kept from the original implementation
        # They are not modified in this reconstruction

        # Create chapters and objectives (only unique ones)
        chapters_dict = {}
        objectives_list = []

        for item in unique_objectives_data:
            chapter_title = item['chapter_title']

            # Create or get chapter
            if chapter_title not in chapters_dict:
                chapter, created = self.get_or_create(
                    models.Chapters,
                    {
                        "title": chapter_title,
                        "framework_id": nis2_directive_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": nis2_directive_framework.id
                    }
                )
                chapters_dict[chapter_title] = chapter

            # Create objective
            chapter = chapters_dict[chapter_title]
            objective, created = self.get_or_create(
                models.Objectives,
                {
                    "title": item['objective_title'],
                    "chapter_id": chapter.id
                },
                {
                    "title": item['objective_title'],
                    "subchapter": item['subchapter'],
                    "chapter_id": chapter.id,
                    "requirement_description": item['requirement_description'],
                    "objective_utilities": item['objective_utilities']
                }
            )
            objectives_list.append(objective)

        self.db.flush()

        # Wire connections: risks, controls, policies -> objectives
        if not self.skip_wire_connections:
            self._wire_connections(nis2_directive_framework, default_org, objectives_list)
        self.db.commit()

        return {
            "frameworks": {"NIS2 Directive": nis2_directive_framework},
            "nis2_directive_conformity_questions": conformity_questions,
            "nis2_directive_chapters": list(chapters_dict.values()),
            "nis2_directive_objectives": objectives_list
        }

    def _wire_connections(self, framework, org, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to NIS2 Directive objectives using the NIS2_DIRECTIVE_CONNECTIONS mapping.
        """
        import mammoth

        medium_severity = self.db.query(models.RiskSeverity).filter(
            models.RiskSeverity.risk_severity_name == "Medium"
        ).first()
        accept_status = self.db.query(models.RiskStatuses).filter(
            models.RiskStatuses.risk_status_name == "Accept"
        ).first()
        not_implemented = self.db.query(models.ControlStatus).filter(
            models.ControlStatus.status_name == "Not Implemented"
        ).first()
        draft_status = self.db.query(models.PolicyStatuses).filter(
            models.PolicyStatuses.status == "Draft"
        ).first()
        default_asset_category = self.db.query(models.AssetCategories).filter(
            models.AssetCategories.name == "Software"
        ).first()
        if not default_asset_category:
            default_asset_category = self.db.query(models.AssetCategories).first()

        if not all([medium_severity, accept_status, not_implemented, draft_status]):
            logger.warning("Missing lookup defaults - skipping NIS2 Directive connection wiring")
            return

        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in NIS2_DIRECTIVE_CONNECTIONS.values():
            all_risk_names.update(conn["risks"])
            all_control_codes.update(conn["controls"])
            all_policy_codes.update(conn["policies"])

        risk_name_to_id = {}
        if all_risk_names:
            risk_templates = self.db.query(models.RiskTemplate).filter(
                models.RiskTemplate.risk_category_name.in_(all_risk_names)
            ).all()
            risk_template_map = {rt.risk_category_name: rt for rt in risk_templates}

            risk_name_to_asset_category_id = {}
            risk_category_rows = self.db.query(
                models.RiskCategories.risk_category_name,
                models.RiskCategories.asset_category_id
            ).filter(
                models.RiskCategories.risk_category_name.in_(all_risk_names),
                models.RiskCategories.asset_category_id.isnot(None)
            ).all()
            for risk_name, asset_category_id in risk_category_rows:
                if risk_name not in risk_name_to_asset_category_id:
                    risk_name_to_asset_category_id[risk_name] = asset_category_id

            existing_risks = self.db.query(models.Risks).filter(
                models.Risks.organisation_id == org.id,
                models.Risks.risk_category_name.in_(all_risk_names)
            ).all()
            for risk in existing_risks:
                if not risk.asset_category_id:
                    risk.asset_category_id = (
                        risk_name_to_asset_category_id.get(risk.risk_category_name)
                        or (default_asset_category.id if default_asset_category else None)
                    )
                risk_name_to_id[risk.risk_category_name] = risk.id

            max_code_rows = self.db.query(models.Risks.risk_code).filter(
                models.Risks.organisation_id == org.id,
                models.Risks.risk_code.isnot(None)
            ).all()
            existing_codes = [row[0] for row in max_code_rows if row[0] and row[0].startswith("RSK-")]
            next_rsk_num = 1
            if existing_codes:
                nums = []
                for code in existing_codes:
                    try:
                        nums.append(int(code.split("-")[1]))
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
                self.db.add(risk)
                self.db.flush()
                risk_name_to_id[risk_name] = risk.id

        logger.info(f"NIS2 Directive wiring: {len(risk_name_to_id)} risks ready")

        control_code_to_id = {}
        baseline_set, _ = self.get_or_create(
            models.ControlSet,
            {"name": "Baseline Controls", "organisation_id": org.id},
            {
                "name": "Baseline Controls",
                "description": "General baseline controls covering HR, Governance, Risk Management, Security, and Compliance",
                "organisation_id": org.id
            }
        )

        ctrl_template_map = {}
        if all_control_codes:
            control_templates = self.db.query(models.ControlTemplate).filter(
                models.ControlTemplate.code.in_(all_control_codes)
            ).all()
            ctrl_template_map = {ct.code: ct for ct in control_templates}

            existing_controls = self.db.query(models.Control).filter(
                models.Control.organisation_id == org.id,
                models.Control.code.in_(all_control_codes)
            ).all()
            for control in existing_controls:
                control_code_to_id[control.code] = control.id

            for code in sorted(all_control_codes):
                if code in control_code_to_id:
                    continue
                tmpl = ctrl_template_map.get(code)
                control = models.Control(
                    code=code,
                    name=tmpl.name if tmpl else code,
                    description=tmpl.description if tmpl else "",
                    control_set_id=baseline_set.id,
                    control_status_id=not_implemented.id,
                    organisation_id=org.id,
                )
                self.db.add(control)
                self.db.flush()
                control_code_to_id[code] = control.id

        logger.info(f"NIS2 Directive wiring: {len(control_code_to_id)} controls ready")

        def _policy_sort_key(policy_code: str):
            parts = policy_code.split("-")
            if len(parts) == 2 and parts[1].isdigit():
                return (parts[0], int(parts[1]), policy_code)
            return (policy_code, 0, policy_code)

        policy_code_to_id = {}
        if all_policy_codes:
            existing_policies = self.db.query(models.Policies).filter(
                models.Policies.organisation_id == org.id,
                models.Policies.policy_code.in_(all_policy_codes)
            ).all()
            for policy in existing_policies:
                policy_code_to_id[policy.policy_code] = policy.id

            policy_templates = self.db.query(models.PolicyTemplate).filter(
                models.PolicyTemplate.policy_code.in_(all_policy_codes)
            ).all()
            pol_template_map = {pt.policy_code: pt for pt in policy_templates}

            for policy_code in sorted(all_policy_codes, key=_policy_sort_key):
                if policy_code in policy_code_to_id:
                    continue
                tmpl = pol_template_map.get(policy_code)
                body_text = ""
                if tmpl and tmpl.content_docx:
                    try:
                        docx_stream = io.BytesIO(tmpl.content_docx)
                        result = mammoth.convert_to_html(docx_stream)
                        body_text = convert_html_to_plain_text(result.value)
                    except Exception as conv_err:
                        logger.warning(f"NIS2 Directive wiring: docx conversion failed for {policy_code}: {conv_err}")
                policy = models.Policies(
                    title=tmpl.title if tmpl else policy_code,
                    policy_code=policy_code,
                    status_id=draft_status.id,
                    body=body_text,
                    organisation_id=org.id,
                )
                self.db.add(policy)
                self.db.flush()
                policy_code_to_id[policy_code] = policy.id

        logger.info(f"NIS2 Directive wiring: {len(policy_code_to_id)} policies ready")

        obj_title_to_id = {obj.title: obj.id for obj in objectives_list}
        policy_framework_pairs = set()

        obj_risk_count = 0
        obj_ctrl_count = 0
        pol_obj_count = 0
        ctrl_risk_count = 0
        ctrl_pol_count = 0
        planned_control_risk_pairs = set()
        planned_control_policy_pairs = set()

        for obj_title, conn in NIS2_DIRECTIVE_CONNECTIONS.items():
            obj_id = obj_title_to_id.get(obj_title)
            if not obj_id:
                continue

            resolved_risk_ids = []
            resolved_control_ids = []
            resolved_policy_ids = []

            for risk_name in conn["risks"]:
                risk_id = risk_name_to_id.get(risk_name)
                if not risk_id:
                    continue
                resolved_risk_ids.append(risk_id)
                existing = self.db.query(models.ObjectiveRisk).filter_by(
                    objective_id=obj_id, risk_id=risk_id
                ).first()
                if not existing:
                    self.db.add(models.ObjectiveRisk(objective_id=obj_id, risk_id=risk_id))
                    obj_risk_count += 1

            for control_ref in conn["controls"]:
                control_id = control_code_to_id.get(control_ref)
                if not control_id:
                    continue
                resolved_control_ids.append(control_id)
                existing = self.db.query(models.ObjectiveControl).filter_by(
                    objective_id=obj_id, control_id=control_id
                ).first()
                if not existing:
                    self.db.add(models.ObjectiveControl(objective_id=obj_id, control_id=control_id))
                    obj_ctrl_count += 1

            for policy_ref in conn["policies"]:
                policy_id = policy_code_to_id.get(policy_ref)
                if not policy_id:
                    continue
                resolved_policy_ids.append(policy_id)
                existing = self.db.query(models.PolicyObjectives).filter_by(
                    policy_id=policy_id, objective_id=obj_id
                ).first()
                if not existing:
                    self.db.add(models.PolicyObjectives(policy_id=policy_id, objective_id=obj_id))
                    pol_obj_count += 1
                policy_framework_pairs.add((policy_id, framework.id))

            for control_id in resolved_control_ids:
                for risk_id in resolved_risk_ids:
                    pair = (control_id, risk_id, framework.id)
                    if pair in planned_control_risk_pairs:
                        continue
                    existing = self.db.query(models.ControlRisk).filter_by(
                        control_id=control_id, risk_id=risk_id, framework_id=framework.id
                    ).first()
                    if not existing:
                        self.db.add(models.ControlRisk(control_id=control_id, risk_id=risk_id, framework_id=framework.id))
                        ctrl_risk_count += 1
                    planned_control_risk_pairs.add(pair)

            for control_id in resolved_control_ids:
                for policy_id in resolved_policy_ids:
                    pair = (control_id, policy_id, framework.id)
                    if pair in planned_control_policy_pairs:
                        continue
                    existing = self.db.query(models.ControlPolicy).filter_by(
                        control_id=control_id, policy_id=policy_id, framework_id=framework.id
                    ).first()
                    if not existing:
                        self.db.add(models.ControlPolicy(control_id=control_id, policy_id=policy_id, framework_id=framework.id))
                        ctrl_pol_count += 1
                    planned_control_policy_pairs.add(pair)

        pf_count = 0
        for policy_id, framework_id in policy_framework_pairs:
            existing = self.db.query(models.PolicyFrameworks).filter_by(
                policy_id=policy_id, framework_id=framework_id
            ).first()
            if not existing:
                self.db.add(models.PolicyFrameworks(policy_id=policy_id, framework_id=framework_id))
                pf_count += 1

        self.db.flush()
        logger.info(
            f"NIS2 Directive wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )

    def _parse_nis2_directive_data(self):
        """Parse the NIS2 Directive data structure from the Excel file"""
        # Complete NIS2 Directive data with 363 objectives and 3223 conformity questions from the Excel file
        nis2_directive_items = [
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.1: Policy on the security of network and information systems",
                        "objective_title": "1.1.1: For the purpose of Article 21(2), point (a) of Directive (EU) 2022/2555, the policy on the security of network and information systems shall",
                        "requirement_description": "(a) set out the relevant entities' approach to managing the security of their network and information systems;\n(b) be appropriate to and complementary with the relevant entities' business strategy and objectives;\n(c) set out network and information security objectives;\n(d) include a commitment to continual improvement of the security of network and information systems;\n(e) include a commitment to provide the appropriate resources needed for its implementation, including the necessary staff, financial resources, processes, tools and technologies;\n(f) be communicated to and acknowledged by relevant employees and relevant interested external parties;\n(g) lay down roles and responsibilities pursuant to point 1.2;\n(h) list the documentation to be kept and the duration of retention of the documentation;\n(i) list the topic-specific policies;\n(j) lay down indicators and measures to monitor its implementation and the current status of relevant entities' maturity level of network and information security;\n(k) indicate the date of the formal approval by the management bodies of the relevant entities (the 'management bodies').",
                        "objective_utilities": "Establishes governance framework for network and information security",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.1: Policy on the security of network and information systems",
                        "objective_title": "1.1.1: For the purpose of Article 21(2), point (a) of Directive (EU) 2022/2555, the policy on the security of network and information systems shall",
                        "requirement_description": "(a) set out the relevant entities' approach to managing the security of their network and information systems;\n(b) be appropriate to and complementary with the relevant entities' business strategy and objectives;\n(c) set out network and information security objectives;\n(d) include a commitment to continual improvement of the security of network and information systems;\n(e) include a commitment to provide the appropriate resources needed for its implementation, including the necessary staff, financial resources, processes, tools and technologies;\n(f) be communicated to and acknowledged by relevant employees and relevant interested external parties;\n(g) lay down roles and responsibilities pursuant to point 1.2;\n(h) list the documentation to be kept and the duration of retention of the documentation;\n(i) list the topic-specific policies;\n(j) lay down indicators and measures to monitor its implementation and the current status of relevant entities' maturity level of network and information security;\n(k) indicate the date of the formal approval by the management bodies of the relevant entities (the 'management bodies').",
                        "objective_utilities": "Establishes governance framework for network and information security",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.1: Policy on the security of network and information systems",
                        "objective_title": "1.1.2: The network and information system security policy shall be reviewed and, where appropriate, updated by management bodies at least annually and when significant incidents or significant changes to operations or risks occur. The result of the reviews shall be documented.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.1: Policy on the security of network and information systems",
                        "objective_title": "1.1.2: The network and information system security policy shall be reviewed and, where appropriate, updated by management bodies at least annually and when significant incidents or significant changes to operations or risks occur. The result of the reviews shall be documented.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.1: As part of their policy on the security of network and information systems referred to in point 1.1, the relevant entities shall lay down responsibilities and authorities for network and information system security and assign them to roles, allocate them according to the relevant entities' needs, and communicate them to the management bodies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.1: As part of their policy on the security of network and information systems referred to in point 1.1, the relevant entities shall lay down responsibilities and authorities for network and information system security and assign them to roles, allocate them according to the relevant entities' needs, and communicate them to the management bodies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.2: The relevant entities shall require all personnel and third parties to apply network and information system security in accordance with the established network and information security policy, topic-specific policies and procedures of the relevant entities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.2: The relevant entities shall require all personnel and third parties to apply network and information system security in accordance with the established network and information security policy, topic-specific policies and procedures of the relevant entities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.3: At least one person shall report directly to the management bodies on matters of network and information system security.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.3: At least one person shall report directly to the management bodies on matters of network and information system security.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.4: Depending on the size of the relevant entities, network and information system security shall be covered by dedicated roles or duties carried out in addition to existing roles.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.4: Depending on the size of the relevant entities, network and information system security shall be covered by dedicated roles or duties carried out in addition to existing roles.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.5: Conflicting duties and conflicting areas of responsibility shall be segregated, where applicable.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.5: Conflicting duties and conflicting areas of responsibility shall be segregated, where applicable.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.6: Roles, responsibilities and authorities shall be reviewed and, where appropriate, updated by management bodies at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "1: Policy on the security of network and information systems (Article 21(2), point (a) of Directive (EU) 2022/2555).",
                        "subchapter": "1.2: Roles, responsibilities and authorities",
                        "objective_title": "1.2.6: Roles, responsibilities and authorities shall be reviewed and, where appropriate, updated by management bodies at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.1: For the purpose of Article 21(2), point (a) of Directive (EU) 2022/2555, the relevant entities shall establish and maintain an appropriate risk management framework to identify and address the risks posed to the security of network and information systems. The relevant entities shall perform and document risk assessments and, based on the results, establish, implement and monitor a risk treatment plan. Risk assessment results and residual risks shall be accepted by management bodies or, where applicable, by persons who are accountable and have the authority to manage risks, provided that the relevant entities ensure adequate reporting to the management bodies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.1: For the purpose of Article 21(2), point (a) of Directive (EU) 2022/2555, the relevant entities shall establish and maintain an appropriate risk management framework to identify and address the risks posed to the security of network and information systems. The relevant entities shall perform and document risk assessments and, based on the results, establish, implement and monitor a risk treatment plan. Risk assessment results and residual risks shall be accepted by management bodies or, where applicable, by persons who are accountable and have the authority to manage risks, provided that the relevant entities ensure adequate reporting to the management bodies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.2: For the purpose of point 2.1.1, the relevant entities shall establish procedures for identification, analysis, assessment and treatment of risks ('cybersecurity risk management process'). The cybersecurity risk management process shall be an integral part of the relevant entities' overall risk management process, where applicable. As part of the cybersecurity risk management process, the relevant entities shall:",
                        "requirement_description": "(a) follow a risk management methodology;\n(b) establish the risk tolerance level in accordance with the risk appetite of the relevant entities;\n(c) establish and maintain relevant risk criteria;\n(d) in line with an all-hazards approach, identify and document the risks posed to the security of network and information systems, in particular in relation to third parties and risks that could lead to disruptions in the availability, integrity, authenticity and confidentiality of the network and information systems, including the identification of single point of failures;\n(e) analyse the risks posed to the security of network and information systems, including threat, likelihood, impact, and risk level, taking into account cyber threat intelligence and vulnerabilities;\n(f) evaluate the identified risks based on the risk criteria;\n(g) identify and prioritise appropriate risk treatment options and measures;\n(h) continuously monitor the implementation of the risk treatment measures;\n(i) identify who is responsible for implementing the risk treatment measures and when they should be implemented;\n(j) document the chosen risk treatment measures in a risk treatment plan and the reasons justifying the acceptance of residual risks in a comprehensible manner.",
                        "objective_utilities": "Enables systematic identification and management of cybersecurity risks",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.2: For the purpose of point 2.1.1, the relevant entities shall establish procedures for identification, analysis, assessment and treatment of risks ('cybersecurity risk management process'). The cybersecurity risk management process shall be an integral part of the relevant entities' overall risk management process, where applicable. As part of the cybersecurity risk management process, the relevant entities shall:",
                        "requirement_description": "(a) follow a risk management methodology;\n(b) establish the risk tolerance level in accordance with the risk appetite of the relevant entities;\n(c) establish and maintain relevant risk criteria;\n(d) in line with an all-hazards approach, identify and document the risks posed to the security of network and information systems, in particular in relation to third parties and risks that could lead to disruptions in the availability, integrity, authenticity and confidentiality of the network and information systems, including the identification of single point of failures;\n(e) analyse the risks posed to the security of network and information systems, including threat, likelihood, impact, and risk level, taking into account cyber threat intelligence and vulnerabilities;\n(f) evaluate the identified risks based on the risk criteria;\n(g) identify and prioritise appropriate risk treatment options and measures;\n(h) continuously monitor the implementation of the risk treatment measures;\n(i) identify who is responsible for implementing the risk treatment measures and when they should be implemented;\n(j) document the chosen risk treatment measures in a risk treatment plan and the reasons justifying the acceptance of residual risks in a comprehensible manner.",
                        "objective_utilities": "Enables systematic identification and management of cybersecurity risks",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.3: When identifying and prioritising appropriate risk treatment options and measures, the relevant entities shall take into account the risk assessment results, the results of the procedure to assess the effectiveness of cybersecurity risk-management measures, the cost of implementation in relation to the expected benefit, the asset classification referred to in point 12.1, and the business impact analysis referred to in point 4.1.3.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.3: When identifying and prioritising appropriate risk treatment options and measures, the relevant entities shall take into account the risk assessment results, the results of the procedure to assess the effectiveness of cybersecurity risk-management measures, the cost of implementation in relation to the expected benefit, the asset classification referred to in point 12.1, and the business impact analysis referred to in point 4.1.3.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.4: The relevant entities shall review and, where appropriate, update the risk assessment results and the risk treatment plan at planned intervals and at least annually, and when significant changes to operations or risks or significant incidents occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.1: Risk management framework",
                        "objective_title": "2.1.4: The relevant entities shall review and, where appropriate, update the risk assessment results and the risk treatment plan at planned intervals and at least annually, and when significant changes to operations or risks or significant incidents occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.2: Compliance monitoring",
                        "objective_title": "2.2.1: The relevant entities shall regularly review the compliance with their policies on network and information system security, topic-specific policies, rules, and standards. The management bodies shall be informed of the status of network and information security on the basis of the compliance reviews by means of regular reporting.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.2: Compliance monitoring",
                        "objective_title": "2.2.1: The relevant entities shall regularly review the compliance with their policies on network and information system security, topic-specific policies, rules, and standards. The management bodies shall be informed of the status of network and information security on the basis of the compliance reviews by means of regular reporting.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.2: Compliance monitoring",
                        "objective_title": "2.2.2: The relevant entities shall put in place an effective compliance reporting system which shall be appropriate to their structures, operating environments and threat landscapes. The compliance reporting system shall be capable to provide to the management bodies an informed view of the current state of the relevant entities' management of risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.2: Compliance monitoring",
                        "objective_title": "2.2.2: The relevant entities shall put in place an effective compliance reporting system which shall be appropriate to their structures, operating environments and threat landscapes. The compliance reporting system shall be capable to provide to the management bodies an informed view of the current state of the relevant entities' management of risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.2: Compliance monitoring",
                        "objective_title": "2.2.3: The relevant entities shall perform the compliance monitoring at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.2: Compliance monitoring",
                        "objective_title": "2.2.3: The relevant entities shall perform the compliance monitoring at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.1: The relevant entities shall review independently their approach to managing network and information system security and its implementation including people, processes and technologies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.1: The relevant entities shall review independently their approach to managing network and information system security and its implementation including people, processes and technologies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.2: The relevant entities shall develop and maintain processes to conduct independent reviews which shall be carried out by individuals with appropriate audit competence. Where the independent review is conducted by staff members of the relevant entity, the persons conducting the reviews shall not be in the line of authority of the personnel of the area under review. If the size of the relevant entities does not allow such separation of line of authority, the relevant entities shall put in place alternative measures to guarantee the impartiality of the reviews.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.2: The relevant entities shall develop and maintain processes to conduct independent reviews which shall be carried out by individuals with appropriate audit competence. Where the independent review is conducted by staff members of the relevant entity, the persons conducting the reviews shall not be in the line of authority of the personnel of the area under review. If the size of the relevant entities does not allow such separation of line of authority, the relevant entities shall put in place alternative measures to guarantee the impartiality of the reviews.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.3: The results of the independent reviews, including the results from the compliance monitoring pursuant to point 2.2 and the monitoring and measurement pursuant to point 7, shall be reported to the management bodies. Corrective actions shall be taken or residual risk accepted according to the relevant entities' risk acceptance criteria.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.3: The results of the independent reviews, including the results from the compliance monitoring pursuant to point 2.2 and the monitoring and measurement pursuant to point 7, shall be reported to the management bodies. Corrective actions shall be taken or residual risk accepted according to the relevant entities' risk acceptance criteria.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.4: The independent reviews shall take place at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "2: Risk management policy (Article 21(2), point (a) of Directive (EU) 2022/2555)",
                        "subchapter": "2.3: Independent review of information and network security",
                        "objective_title": "2.3.4: The independent reviews shall take place at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.1: Incident handling policy",
                        "objective_title": "3.1.1: For the purpose of Article 21(2), point (b) of Directive (EU) 2022/2555, the relevant entities shall establish and implement an incident handling policy laying down the roles, responsibilities, and procedures for detecting, analysing, containing or responding to, recovering from, documenting and reporting of incidents in a timely manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.1: Incident handling policy",
                        "objective_title": "3.1.1: For the purpose of Article 21(2), point (b) of Directive (EU) 2022/2555, the relevant entities shall establish and implement an incident handling policy laying down the roles, responsibilities, and procedures for detecting, analysing, containing or responding to, recovering from, documenting and reporting of incidents in a timely manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.1: Incident handling policy",
                        "objective_title": "3.1.2: The policy referred to in point 3.1.1 shall be coherent with the business continuity and disaster recovery plan referred to in point 4.1. The policy shall include:",
                        "requirement_description": "(a) a categorisation system for incidents that is consistent with the event assessment and classification carried out pursuant to point 3.4.1;\n(b) effective communication plans including for escalation and reporting;\n(c) assignment of roles to detect and appropriately respond to incidents to competent employees;\n(d) documents to be used in the course of incident detection and response such as incident response manuals, escalation charts, contact lists and templates.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.1: Incident handling policy",
                        "objective_title": "3.1.2: The policy referred to in point 3.1.1 shall be coherent with the business continuity and disaster recovery plan referred to in point 4.1. The policy shall include:",
                        "requirement_description": "(a) a categorisation system for incidents that is consistent with the event assessment and classification carried out pursuant to point 3.4.1;\n(b) effective communication plans including for escalation and reporting;\n(c) assignment of roles to detect and appropriately respond to incidents to competent employees;\n(d) documents to be used in the course of incident detection and response such as incident response manuals, escalation charts, contact lists and templates.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.1: Incident handling policy",
                        "objective_title": "3.1.3: The roles, responsibilities and procedures laid down in the policy shall be tested and reviewed and, where appropriate, updated at planned intervals and after significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.1: Incident handling policy",
                        "objective_title": "3.1.3: The roles, responsibilities and procedures laid down in the policy shall be tested and reviewed and, where appropriate, updated at planned intervals and after significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.1: The relevant entities shall lay down procedures and use tools to monitor and log activities on their network and information systems to detect events that could be considered as incidents and respond accordingly to mitigate the impact.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.1: The relevant entities shall lay down procedures and use tools to monitor and log activities on their network and information systems to detect events that could be considered as incidents and respond accordingly to mitigate the impact.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.2: To the extent feasible, monitoring shall be automated and carried out either continuously or in periodic intervals, subject to business capabilities. The relevant entities shall implement their monitoring activities in a way which minimises false positives and false negatives.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.2: To the extent feasible, monitoring shall be automated and carried out either continuously or in periodic intervals, subject to business capabilities. The relevant entities shall implement their monitoring activities in a way which minimises false positives and false negatives.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.3: Based on the procedures referred to in point 3.2.1, the relevant entities shall maintain, document, and review logs. The relevant entities shall establish a list of assets to be subject to logging based on the results of the risk assessment carried out pursuant to point 2.1. Where appropriate, logs shall include:",
                        "requirement_description": "(a) relevant outbound and inbound network traffic;\n(b) creation, modification or deletion of users of the relevant entities' network and information systems and extension of the permissions;\n(c) access to systems and applications;\n(d) authentication-related events;\n(e) all privileged access to systems and applications, and activities performed by administrative accounts;\n(f) access or changes to critical configuration and backup files;\n(g) event logs and logs from security tools, such as antivirus, intrusion detection systems or firewalls;\n(h) use of system resources, as well as their performance;\n(i) physical access to facilities;\n(j) access to and use of their network equipment and devices;\n(k) activation, stopping and pausing of the various logs;\n(l) environmental events.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.3: Based on the procedures referred to in point 3.2.1, the relevant entities shall maintain, document, and review logs. The relevant entities shall establish a list of assets to be subject to logging based on the results of the risk assessment carried out pursuant to point 2.1. Where appropriate, logs shall include:",
                        "requirement_description": "(a) relevant outbound and inbound network traffic;\n(b) creation, modification or deletion of users of the relevant entities' network and information systems and extension of the permissions;\n(c) access to systems and applications;\n(d) authentication-related events;\n(e) all privileged access to systems and applications, and activities performed by administrative accounts;\n(f) access or changes to critical configuration and backup files;\n(g) event logs and logs from security tools, such as antivirus, intrusion detection systems or firewalls;\n(h) use of system resources, as well as their performance;\n(i) physical access to facilities;\n(j) access to and use of their network equipment and devices;\n(k) activation, stopping and pausing of the various logs;\n(l) environmental events.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.4: The logs shall be regularly reviewed for any unusual or unwanted trends. Where appropriate, the relevant entities shall lay down appropriate values for alarm thresholds. If the laid down values for alarm threshold are exceeded, an alarm shall be triggered, where appropriate, automatically. The relevant entities shall ensure that, in case of an alarm, a qualified and appropriate response is initiated in a timely manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.4: The logs shall be regularly reviewed for any unusual or unwanted trends. Where appropriate, the relevant entities shall lay down appropriate values for alarm thresholds. If the laid down values for alarm threshold are exceeded, an alarm shall be triggered, where appropriate, automatically. The relevant entities shall ensure that, in case of an alarm, a qualified and appropriate response is initiated in a timely manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.5: The relevant entities shall maintain and back up logs for a predefined period and shall protect them from unauthorised access or changes.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.5: The relevant entities shall maintain and back up logs for a predefined period and shall protect them from unauthorised access or changes.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.6: To the extent feasible, the relevant entities shall ensure that all systems have synchronised time sources to be able to correlate logs between systems for event assessment. The relevant entities shall establish and keep a list of all assets that are being logged and ensure that monitoring and logging systems are redundant. The availability of the monitoring and logging systems shall be monitored independent of the systems they are monitoring.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.6: To the extent feasible, the relevant entities shall ensure that all systems have synchronised time sources to be able to correlate logs between systems for event assessment. The relevant entities shall establish and keep a list of all assets that are being logged and ensure that monitoring and logging systems are redundant. The availability of the monitoring and logging systems shall be monitored independent of the systems they are monitoring.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.7: The procedures as well as the list of assets that are being logged shall be reviewed and, where appropriate, updated at regular intervals and after significant incidents.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.2: Monitoring and logging",
                        "objective_title": "3.2.7: The procedures as well as the list of assets that are being logged shall be reviewed and, where appropriate, updated at regular intervals and after significant incidents.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.3: Event reporting",
                        "objective_title": "3.3.1: The relevant entities shall put in place a simple mechanism allowing their employees, suppliers, and customers to report suspicious events.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.3: Event reporting",
                        "objective_title": "3.3.1: The relevant entities shall put in place a simple mechanism allowing their employees, suppliers, and customers to report suspicious events.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.3: Event reporting",
                        "objective_title": "3.3.2: The relevant entities shall, where appropriate, communicate the event reporting mechanism to their suppliers and customers, and shall regularly train their employees how to use the mechanism.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.3: Event reporting",
                        "objective_title": "3.3.2: The relevant entities shall, where appropriate, communicate the event reporting mechanism to their suppliers and customers, and shall regularly train their employees how to use the mechanism.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.4: Event assessment and classification",
                        "objective_title": "3.4.1: The relevant entities shall assess suspicious events to determine whether they constitute incidents and, if so, determine their nature and severity.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.4: Event assessment and classification",
                        "objective_title": "3.4.1: The relevant entities shall assess suspicious events to determine whether they constitute incidents and, if so, determine their nature and severity.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.4: Event assessment and classification",
                        "objective_title": "3.4.2: For the purpose of point 3.4.1, the relevant entities shall act in the following manner:",
                        "requirement_description": "(a) carry out the assessment based on predefined criteria laid down in advance, and on a triage to determine prioritisation of incident containment and eradication;\n(b) assess the existence of recurring incidents as referred to in Article 4 of this Regulation on a quarterly basis;\n(c) review the appropriate logs for the purposes of event assessment and classification;\n(d) put in place a process for log correlation and analysis, and\n(e) reassess and reclassify events in case of new information becoming available or after analysis of previously available information.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.4: Event assessment and classification",
                        "objective_title": "3.4.2: For the purpose of point 3.4.1, the relevant entities shall act in the following manner:",
                        "requirement_description": "(a) carry out the assessment based on predefined criteria laid down in advance, and on a triage to determine prioritisation of incident containment and eradication;\n(b) assess the existence of recurring incidents as referred to in Article 4 of this Regulation on a quarterly basis;\n(c) review the appropriate logs for the purposes of event assessment and classification;\n(d) put in place a process for log correlation and analysis, and\n(e) reassess and reclassify events in case of new information becoming available or after analysis of previously available information.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.1: The relevant entities shall respond to incidents in accordance with documented procedures and in a timely manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.1: The relevant entities shall respond to incidents in accordance with documented procedures and in a timely manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.2: The incident response procedures shall include the following stages:",
                        "requirement_description": "(a) incident containment, to prevent the consequences of the incident from spreading;\n(b) eradication, to prevent the incident from continuing or reappearing,\n(c) recovery from the incident, where necessary.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.2: The incident response procedures shall include the following stages:",
                        "requirement_description": "(a) incident containment, to prevent the consequences of the incident from spreading;\n(b) eradication, to prevent the incident from continuing or reappearing,\n(c) recovery from the incident, where necessary.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.3: The relevant entities shall establish communication plans and procedures:",
                        "requirement_description": "(a) with the Computer Security Incident Response Teams (CSIRTs) or, where applicable, the competent authorities, related to incident notification;\n(b) for communication among staff members of the relevant entity, and for communication with relevant stakeholders external to the relevant entity.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.3: The relevant entities shall establish communication plans and procedures:",
                        "requirement_description": "(a) with the Computer Security Incident Response Teams (CSIRTs) or, where applicable, the competent authorities, related to incident notification;\n(b) for communication among staff members of the relevant entity, and for communication with relevant stakeholders external to the relevant entity.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.4: The relevant entities shall log incident response activities in accordance with the procedures referred to in point 3.2.1, and record evidence.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally and on a regular basis?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.5: The relevant entities shall test at planned intervals their incident response procedures.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.5: Incident response",
                        "objective_title": "3.5.5: The relevant entities shall test at planned intervals their incident response procedures.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.6: Post-incident reviews",
                        "objective_title": "3.6.1: Where appropriate, the relevant entities shall carry out post-incident reviews after recovery from incidents. The post-incident reviews shall identify, where possible, the root cause of the incident and result in documented lessons learned to reduce the occurrence and consequences of future incidents.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.6: Post-incident reviews",
                        "objective_title": "3.6.1: Where appropriate, the relevant entities shall carry out post-incident reviews after recovery from incidents. The post-incident reviews shall identify, where possible, the root cause of the incident and result in documented lessons learned to reduce the occurrence and consequences of future incidents.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.6: Post-incident reviews",
                        "objective_title": "3.6.2: The relevant entities shall ensure that post-incident reviews contribute to improving their approach to network and information security, to risk treatment measures, and to incident handling, detection and response procedures.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.6: Post-incident reviews",
                        "objective_title": "3.6.2: The relevant entities shall ensure that post-incident reviews contribute to improving their approach to network and information security, to risk treatment measures, and to incident handling, detection and response procedures.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.6: Post-incident reviews",
                        "objective_title": "3.6.3: The relevant entities shall review at planned intervals if incidents led to post-incident reviews.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "3: Incident handling (Article 21(2), point (b), of Directive (EU) 2022/2555)",
                        "subchapter": "3.6: Post-incident reviews",
                        "objective_title": "3.6.3: The relevant entities shall review at planned intervals if incidents led to post-incident reviews.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, containment, eradication and recovery?.",
                                    "Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.1: For the purpose of Article 21(2), point (c) of Directive (EU) 2022/2555, the relevant entities shall lay down and maintain a business continuity and disaster recovery plan to apply in the case of incidents.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.1: For the purpose of Article 21(2), point (c) of Directive (EU) 2022/2555, the relevant entities shall lay down and maintain a business continuity and disaster recovery plan to apply in the case of incidents.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.2: The relevant entities' operations shall be restored according to the business continuity and disaster recovery plan. The plan shall be based on the results of the risk assessment carried out pursuant to point 2.1 and shall include, where appropriate, the following:",
                        "requirement_description": "(a) purpose, scope and audience;\n(b) roles and responsibilities;\n(c) key contacts and (internal and external) communication channels;\n(d) conditions for plan activation and deactivation;\n(e) order of recovery for operations;\n(f) recovery plans for specific operations, including recovery objectives;\n(g) required resources, including backups and redundancies;\n(h) restoring and resuming activities from temporary measures.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.2: The relevant entities' operations shall be restored according to the business continuity and disaster recovery plan. The plan shall be based on the results of the risk assessment carried out pursuant to point 2.1 and shall include, where appropriate, the following:",
                        "requirement_description": "(a) purpose, scope and audience;\n(b) roles and responsibilities;\n(c) key contacts and (internal and external) communication channels;\n(d) conditions for plan activation and deactivation;\n(e) order of recovery for operations;\n(f) recovery plans for specific operations, including recovery objectives;\n(g) required resources, including backups and redundancies;\n(h) restoring and resuming activities from temporary measures.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.3: The relevant entities shall carry out a business impact analysis to assess the potential impact of severe disruptions to their business operations and shall, based on the results of the business impact analysis, establish continuity requirements for the network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.3: The relevant entities shall carry out a business impact analysis to assess the potential impact of severe disruptions to their business operations and shall, based on the results of the business impact analysis, establish continuity requirements for the network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.4: The business continuity plan and disaster recovery plan shall be tested, reviewed and, where appropriate, updated at planned intervals and following significant incidents or significant changes to operations or risks. The relevant entities shall ensure that the plans incorporate lessons learnt from such tests.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.1: Business continuity and disaster recovery plan",
                        "objective_title": "4.1.4: The business continuity plan and disaster recovery plan shall be tested, reviewed and, where appropriate, updated at planned intervals and following significant incidents or significant changes to operations or risks. The relevant entities shall ensure that the plans incorporate lessons learnt from such tests.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.1: The relevant entities shall maintain backup copies of data and provide sufficient available resources, including facilities, network and information systems and staff, to ensure an appropriate level of redundancy.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.1: The relevant entities shall maintain backup copies of data and provide sufficient available resources, including facilities, network and information systems and staff, to ensure an appropriate level of redundancy.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.2: Based on the results of the risk assessment carried out pursuant to point 2.1 and the business continuity plan, the relevant entities shall lay down backup plans which include the following:",
                        "requirement_description": "(a) recovery times;\n(b) assurance that backup copies are complete and accurate, including configuration data and data stored in cloud computing service environment;\n(c) storing backup copies (online or offline) in a safe location or locations, which are not in the same network as the system, and are at sufficient distance to escape any damage from a disaster at the main site;\n(d) appropriate physical and logical access controls to backup copies, in accordance with the asset classification level;\n(e) restoring data from backup copies;\n(f) retention periods based on business and regulatory requirements.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.2: Based on the results of the risk assessment carried out pursuant to point 2.1 and the business continuity plan, the relevant entities shall lay down backup plans which include the following:",
                        "requirement_description": "(a) recovery times;\n(b) assurance that backup copies are complete and accurate, including configuration data and data stored in cloud computing service environment;\n(c) storing backup copies (online or offline) in a safe location or locations, which are not in the same network as the system, and are at sufficient distance to escape any damage from a disaster at the main site;\n(d) appropriate physical and logical access controls to backup copies, in accordance with the asset classification level;\n(e) restoring data from backup copies;\n(f) retention periods based on business and regulatory requirements.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.3: The relevant entities shall perform regular integrity checks on the backup copies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.3: The relevant entities shall perform regular integrity checks on the backup copies.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.4: Based on the results of the risk assessment carried out pursuant to point 2.1 and the business continuity plan, the relevant entities shall ensure sufficient availability of resources by at least partial redundancy of the following:",
                        "requirement_description": "(a) network and information systems;\n(b) assets, including facilities, equipment and supplies;\n(c) personnel with the necessary responsibility, authority and competence;\n(d) appropriate communication channels.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.4: Based on the results of the risk assessment carried out pursuant to point 2.1 and the business continuity plan, the relevant entities shall ensure sufficient availability of resources by at least partial redundancy of the following:",
                        "requirement_description": "(a) network and information systems;\n(b) assets, including facilities, equipment and supplies;\n(c) personnel with the necessary responsibility, authority and competence;\n(d) appropriate communication channels.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.5: Where appropriate, the relevant entities shall ensure that monitoring and adjustment of resources, including facilities, systems and personnel, is duly informed by backup and redundancy requirements.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.5: Where appropriate, the relevant entities shall ensure that monitoring and adjustment of resources, including facilities, systems and personnel, is duly informed by backup and redundancy requirements.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.6: The relevant entities shall carry out regular testing of the recovery of backup copies and redundancies to ensure that, in recovery conditions, they can be relied upon and cover the copies, processes and knowledge to perform an effective recovery. The relevant entities shall document the results of the tests and, where needed, take corrective action.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.2: Backup and redundancy management",
                        "objective_title": "4.2.6: The relevant entities shall carry out regular testing of the recovery of backup copies and redundancies to ensure that, in recovery conditions, they can be relied upon and cover the copies, processes and knowledge to perform an effective recovery. The relevant entities shall document the results of the tests and, where needed, take corrective action.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.1: The relevant entities shall put in place a process for crisis management.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.1: The relevant entities shall put in place a process for crisis management.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.2: The relevant entities shall ensure that the crisis management process addresses at least the following elements:",
                        "requirement_description": "(a) roles and responsibilities for personnel and, where appropriate, suppliers and service providers, specifying the allocation of roles in crisis situations, including specific steps to follow;\n(b) appropriate communication means between the relevant entities and relevant competent authorities;\n(c) application of appropriate measures to ensure the maintenance of network and information system security in crisis situations.\nFor the purpose of point (b), the flow of information between the relevant entities and relevant competent authorities shall include both obligatory communications, such as incident reports and related timelines, and non-obligatory communications.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.2: The relevant entities shall ensure that the crisis management process addresses at least the following elements:",
                        "requirement_description": "(a) roles and responsibilities for personnel and, where appropriate, suppliers and service providers, specifying the allocation of roles in crisis situations, including specific steps to follow;\n(b) appropriate communication means between the relevant entities and relevant competent authorities;\n(c) application of appropriate measures to ensure the maintenance of network and information system security in crisis situations.\nFor the purpose of point (b), the flow of information between the relevant entities and relevant competent authorities shall include both obligatory communications, such as incident reports and related timelines, and non-obligatory communications.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.3: The relevant entities shall implement a process for managing and making use of information received from the CSIRTs or, where applicable, the competent authorities, concerning incidents, vulnerabilities, threats or possible mitigation measures.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.3: The relevant entities shall implement a process for managing and making use of information received from the CSIRTs or, where applicable, the competent authorities, concerning incidents, vulnerabilities, threats or possible mitigation measures.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.4: The relevant entities shall test, review and, where appropriate, update the crisis management plan on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "4: Business continuity and crisis management (Article 21(2), point (c), of Directive (EU) 2022/2555)",
                        "subchapter": "4.3: Crisis management",
                        "objective_title": "4.3.4: The relevant entities shall test, review and, where appropriate, update the crisis management plan on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.1: For the purpose of Article 21(2), point (d) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a supply chain security policy which governs the relations with their direct suppliers and service providers in order to mitigate the identified risks to the security of network and information systems. In the supply chain security policy, the relevant entities shall identify their role in the supply chain and communicate it to their direct suppliers and service providers.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.1: For the purpose of Article 21(2), point (d) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a supply chain security policy which governs the relations with their direct suppliers and service providers in order to mitigate the identified risks to the security of network and information systems. In the supply chain security policy, the relevant entities shall identify their role in the supply chain and communicate it to their direct suppliers and service providers.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.2: As part of the supply chain security policy referred to in point 5.1.1, the relevant entities shall lay down criteria to select and contract suppliers and service providers. Those criteria shall include the following:",
                        "requirement_description": "(a) the cybersecurity practices of the suppliers and service providers, including their secure development procedures;\n(b) the ability of the suppliers and service providers to meet cybersecurity specifications set by the relevant entities;\n(c) the overall quality and resilience of ICT products and ICT services and the cybersecurity risk-management measures embedded in them, including the risks and classification level of the ICT products and ICT services;\n(d) the ability of the relevant entities to diversify sources of supply and limit vendor lock-in, where applicable.",
                        "objective_utilities": "Enables systematic identification and management of cybersecurity risks",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.2: As part of the supply chain security policy referred to in point 5.1.1, the relevant entities shall lay down criteria to select and contract suppliers and service providers. Those criteria shall include the following:",
                        "requirement_description": "(a) the cybersecurity practices of the suppliers and service providers, including their secure development procedures;\n(b) the ability of the suppliers and service providers to meet cybersecurity specifications set by the relevant entities;\n(c) the overall quality and resilience of ICT products and ICT services and the cybersecurity risk-management measures embedded in them, including the risks and classification level of the ICT products and ICT services;\n(d) the ability of the relevant entities to diversify sources of supply and limit vendor lock-in, where applicable.",
                        "objective_utilities": "Enables systematic identification and management of cybersecurity risks",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.3: When establishing their supply chain security policy, relevant entities shall take into account the results of the coordinated security risk assessments of critical supply chains carried out in accordance with Article 22(1) of Directive (EU) 2022/2555, where applicable.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.3: When establishing their supply chain security policy, relevant entities shall take into account the results of the coordinated security risk assessments of critical supply chains carried out in accordance with Article 22(1) of Directive (EU) 2022/2555, where applicable.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.4: Based on the supply chain security policy and taking into account the results of the risk assessment carried out in accordance with point 2.1 of this Annex, the relevant entities shall ensure that their contracts with the suppliers and service providers specify, where appropriate through service level agreements, the following, where appropriate:",
                        "requirement_description": "(a) cybersecurity requirements for the suppliers or service providers, including requirements as regards the security in acquisition of ICT services or ICT products set out in point 6.1;\n(b) requirements regarding awareness, skills and training, and where appropriate certifications, required from the suppliers' or service providers' employees;\n(c) requirements regarding the verification of the background of the suppliers' and service providers' employees;\n(d) an obligation on suppliers and service providers to notify, without undue delay, the relevant entities of incidents that present a risk to the security of the network and information systems of those entities;\n(e) the right to audit or right to receive audit reports;\n(f) an obligation on suppliers and service providers to handle vulnerabilities that present a risk to the security of the network and information systems of the relevant entities;\n(g) requirements regarding subcontracting and, where the relevant entities allow subcontracting, cybersecurity requirements for subcontractors in accordance with the cybersecurity requirements referred to in point (a);(h) obligations on the suppliers and service providers at the termination of the contract, such as retrieval and disposal of the information obtained by the suppliers and service providers in the exercise of their tasks.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.4: Based on the supply chain security policy and taking into account the results of the risk assessment carried out in accordance with point 2.1 of this Annex, the relevant entities shall ensure that their contracts with the suppliers and service providers specify, where appropriate through service level agreements, the following, where appropriate:",
                        "requirement_description": "(a) cybersecurity requirements for the suppliers or service providers, including requirements as regards the security in acquisition of ICT services or ICT products set out in point 6.1;\n(b) requirements regarding awareness, skills and training, and where appropriate certifications, required from the suppliers' or service providers' employees;\n(c) requirements regarding the verification of the background of the suppliers' and service providers' employees;\n(d) an obligation on suppliers and service providers to notify, without undue delay, the relevant entities of incidents that present a risk to the security of the network and information systems of those entities;\n(e) the right to audit or right to receive audit reports;\n(f) an obligation on suppliers and service providers to handle vulnerabilities that present a risk to the security of the network and information systems of the relevant entities;\n(g) requirements regarding subcontracting and, where the relevant entities allow subcontracting, cybersecurity requirements for subcontractors in accordance with the cybersecurity requirements referred to in point (a);(h) obligations on the suppliers and service providers at the termination of the contract, such as retrieval and disposal of the information obtained by the suppliers and service providers in the exercise of their tasks.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.5: The relevant entities shall take into account the elements referred to in point 5.1.2 and 5.1.3 as part of the selection process of new suppliers and service providers, as well as part of the procurement process referred to in point 6.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.5: The relevant entities shall take into account the elements referred to in point 5.1.2 and 5.1.3 as part of the selection process of new suppliers and service providers, as well as part of the procurement process referred to in point 6.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.6: The relevant entities shall review the supply chain security policy, and monitor, evaluate and, where necessary, act upon changes in the cybersecurity practices of suppliers and service providers, at planned intervals and when significant changes to operations or risks or significant incidents related to the provision of ICT services or having impact on the security of the ICT products from suppliers and service providers occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.6: The relevant entities shall review the supply chain security policy, and monitor, evaluate and, where necessary, act upon changes in the cybersecurity practices of suppliers and service providers, at planned intervals and when significant changes to operations or risks or significant incidents related to the provision of ICT services or having impact on the security of the ICT products from suppliers and service providers occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.7: For the purpose of point 5.1.6, the relevant entities shall:",
                        "requirement_description": "(a) regularly monitor reports on the implementation of the service level agreements, where applicable;\n(b) review incidents related to ICT products and ICT services from suppliers and service providers;\n(c) assess the need for unscheduled reviews and document the findings in a comprehensible manner;\n(d) analyse the risks presented by changes related to ICT products and ICT services from suppliers and service providers and, where appropriate, take mitigating measures in a timely manner.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.1: Supply chain security policy",
                        "objective_title": "5.1.7: For the purpose of point 5.1.6, the relevant entities shall:",
                        "requirement_description": "(a) regularly monitor reports on the implementation of the service level agreements, where applicable;\n(b) review incidents related to ICT products and ICT services from suppliers and service providers;\n(c) assess the need for unscheduled reviews and document the findings in a comprehensible manner;\n(d) analyse the risks presented by changes related to ICT products and ICT services from suppliers and service providers and, where appropriate, take mitigating measures in a timely manner.",
                        "objective_utilities": "Ensures effective response to and recovery from cybersecurity incidents",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.2: Directory of suppliers and service provider",
                        "objective_title": "5.2.1: The relevant entities shall maintain and keep up to date a registry of their direct suppliers and service providers, including:",
                        "requirement_description": "(a) contact points for each direct supplier and service provider;\n(b) a list of ICT products, ICT services, and ICT processes provided by the direct supplier or service provider to the relevant entities.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "5: Supply chain security (Article 21(2), point (d), of Directive (EU) 2022/2555)",
                        "subchapter": "5.2: Directory of suppliers and service provider",
                        "objective_title": "5.2.1: The relevant entities shall maintain and keep up to date a registry of their direct suppliers and service providers, including:",
                        "requirement_description": "(a) contact points for each direct supplier and service provider;\n(b) a list of ICT products, ICT services, and ICT processes provided by the direct supplier or service provider to the relevant entities.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the development, acquisition, maintenance and disposal of systems, system components and services, including documenting selected mitigating actions and monitoring performance against those plans?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Security in acquisition of ICT services or ICT products",
                        "objective_title": "6.1.1: For the purpose of Article 21(2), point (e) of Directive (EU) 2022/2555, the relevant entities shall set and implement processes to manage risks stemming from the acquisition of ICT services or ICT products for components that are critical for the relevant entities' security of network and information systems, based on the risk assessment carried out pursuant to point 2.1, from suppliers or service providers throughout their life cycle.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Security in acquisition of ICT services or ICT products",
                        "objective_title": "6.1.1: For the purpose of Article 21(2), point (e) of Directive (EU) 2022/2555, the relevant entities shall set and implement processes to manage risks stemming from the acquisition of ICT services or ICT products for components that are critical for the relevant entities' security of network and information systems, based on the risk assessment carried out pursuant to point 2.1, from suppliers or service providers throughout their life cycle.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Security in acquisition of ICT services or ICT products",
                        "objective_title": "6.1.2: For the purpose of point 6.1.1, the processes referred to in point 6.1.1 shall include:",
                        "requirement_description": "(a) security requirements to apply to the ICT services or ICT products to be acquired;\n(b) requirements regarding security updates throughout the entire lifetime of the ICT services or ICT products, or replacement after the end of the support period;\n(c) information describing the hardware and software components used in the ICT services or ICT products;\n(d) information describing the implemented cybersecurity functions of the ICT services or ICT products and the configuration required for their secure operation;\n(e) assurance that the ICT services or ICT products comply with the security requirements according to point (a);\n(f) methods for validating that the delivered ICT services or ICT products are compliant to the stated security requirements, as well as documentation of the results of the validation.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-03: Does the organization identify and assign a risk ranking to newly discovered security vulnerabilities using reputable outside sources for security vulnerability information?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Security in acquisition of ICT services or ICT products",
                        "objective_title": "6.1.2: For the purpose of point 6.1.1, the processes referred to in point 6.1.1 shall include:",
                        "requirement_description": "(a) security requirements to apply to the ICT services or ICT products to be acquired;\n(b) requirements regarding security updates throughout the entire lifetime of the ICT services or ICT products, or replacement after the end of the support period;\n(c) information describing the hardware and software components used in the ICT services or ICT products;\n(d) information describing the implemented cybersecurity functions of the ICT services or ICT products and the configuration required for their secure operation;\n(e) assurance that the ICT services or ICT products comply with the security requirements according to point (a);\n(f) methods for validating that the delivered ICT services or ICT products are compliant to the stated security requirements, as well as documentation of the results of the validation.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-03: Does the organization identify and assign a risk ranking to newly discovered security vulnerabilities using reputable outside sources for security vulnerability information?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Security in acquisition of ICT services or ICT products",
                        "objective_title": "6.1.3: The relevant entities shall review and, where appropriate, update the processes at planned intervals and when significant incidents occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Security in acquisition of ICT services or ICT products",
                        "objective_title": "6.1.3: The relevant entities shall review and, where appropriate, update the processes at planned intervals and when significant incidents occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.1: Before developing a network and information system, including software, the relevant entities shall lay down rules for the secure development of network and information systems and apply them when developing network and information systems in-house, or when outsourcing the development of network and information systems. The rules shall cover all development phases, including specification, design, development, implementation and testing.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.1: Before developing a network and information system, including software, the relevant entities shall lay down rules for the secure development of network and information systems and apply them when developing network and information systems in-house, or when outsourcing the development of network and information systems. The rules shall cover all development phases, including specification, design, development, implementation and testing.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.2: For the purpose of point 6.2.1, the relevant entities shall:",
                        "requirement_description": "(a) carry out an analysis of security requirements at the specification and design phases of any development or acquisition project undertaken by the relevant entities or on behalf of those entities;\n(b) apply principles for engineering secure systems and secure coding principles to any information system development activities such as promoting cybersecurity-by-design, zero-trust architectures;\n(c) lay down security requirements regarding development environments;\n(d) establish and implement security testing processes in the development life cycle;\n(e) appropriately select, protect and manage security test data;\n(f) sanitise and anonymise testing data according to the risk assessment carried out pursuant to point 2.1.",
                        "objective_utilities": "Integrates security throughout system lifecycle",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.2: For the purpose of point 6.2.1, the relevant entities shall:",
                        "requirement_description": "(a) carry out an analysis of security requirements at the specification and design phases of any development or acquisition project undertaken by the relevant entities or on behalf of those entities;\n(b) apply principles for engineering secure systems and secure coding principles to any information system development activities such as promoting cybersecurity-by-design, zero-trust architectures;\n(c) lay down security requirements regarding development environments;\n(d) establish and implement security testing processes in the development life cycle;\n(e) appropriately select, protect and manage security test data;\n(f) sanitise and anonymise testing data according to the risk assessment carried out pursuant to point 2.1.",
                        "objective_utilities": "Integrates security throughout system lifecycle",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.3: For outsourced development of network and information systems, the relevant entities shall also apply the policies and procedures referred to in points 5 and 6.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.3: For outsourced development of network and information systems, the relevant entities shall also apply the policies and procedures referred to in points 5 and 6.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.4: The relevant entities shall review and, where necessary, update their secure development rules at planned intervals.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.2: Secure development life cycle",
                        "objective_title": "6.2.4: The relevant entities shall review and, where necessary, update their secure development rules at planned intervals.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.3: Configuration management",
                        "objective_title": "6.3.1: The relevant entities shall take the appropriate measures to establish, document, implement, and monitor configurations, including security configurations of hardware, software, services and networks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.3: Configuration management",
                        "objective_title": "6.3.1: The relevant entities shall take the appropriate measures to establish, document, implement, and monitor configurations, including security configurations of hardware, software, services and networks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.3: Configuration management",
                        "objective_title": "6.3.2: For the purpose of point 6.3.1, the relevant entities shall:",
                        "requirement_description": "(a) lay down and ensure security in configurations for their hardware, software, services and networks;\n(b) lay down and implement processes and tools to enforce the laid down secure configurations for hardware, software, services and networks, for newly installed systems as well as for systems in operation over their lifetime.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.3: Configuration management",
                        "objective_title": "6.3.2: For the purpose of point 6.3.1, the relevant entities shall:",
                        "requirement_description": "(a) lay down and ensure security in configurations for their hardware, software, services and networks;\n(b) lay down and implement processes and tools to enforce the laid down secure configurations for hardware, software, services and networks, for newly installed systems as well as for systems in operation over their lifetime.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.3: Configuration management",
                        "objective_title": "6.3.3: The relevant entities shall review and, where appropriate, update configurations at planned intervals or when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.3: Configuration management",
                        "objective_title": "6.3.3: The relevant entities shall review and, where appropriate, update configurations at planned intervals or when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.1: The relevant entities shall apply change management procedures to control changes of network and information systems. Where applicable, the procedures shall be consistent with the relevant entities' general policies concerning change management.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.1: The relevant entities shall apply change management procedures to control changes of network and information systems. Where applicable, the procedures shall be consistent with the relevant entities' general policies concerning change management.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.2: The procedures referred to in point 6.4.1 shall be applied for releases, modifications and emergency changes of any software and hardware in operation and changes to the configuration. The procedures shall ensure that those changes are documented and, based on the risk assessment carried out pursuant to point 2.1, tested and assessed in view of the potential impact before being implemented.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.2: The procedures referred to in point 6.4.1 shall be applied for releases, modifications and emergency changes of any software and hardware in operation and changes to the configuration. The procedures shall ensure that those changes are documented and, based on the risk assessment carried out pursuant to point 2.1, tested and assessed in view of the potential impact before being implemented.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.3: In the event that the regular change management procedures could not be followed due to an emergency, the relevant entities shall document the result of the change, and the explanation for why the procedures could not be followed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.3: In the event that the regular change management procedures could not be followed due to an emergency, the relevant entities shall document the result of the change, and the explanation for why the procedures could not be followed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.4: The relevant entities shall review and, where appropriate, update the procedures at planned intervals and when significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.4: Change management, repairs and maintenance",
                        "objective_title": "6.4.4: The relevant entities shall review and, where appropriate, update the procedures at planned intervals and when significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.5: Security testing",
                        "objective_title": "6.5.1: The relevant entities shall establish, implement and apply a policy and procedures for security testing.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.5: Security testing",
                        "objective_title": "6.5.1: The relevant entities shall establish, implement and apply a policy and procedures for security testing.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.5: Security testing",
                        "objective_title": "6.5.2: The relevant entities shall:",
                        "requirement_description": "(a) establish, based on the risk assessment carried out pursuant to point 2.1, the need, scope, frequency and type of security tests;\n(b) carry out security tests according to a documented test methodology, covering the components identified as relevant for secure operation in a risk analysis;\n(c) document the type, scope, time and results of the tests, including assessment of criticality and mitigating actions for each finding;\n(d) apply mitigating actions in case of critical findings.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.5: Security testing",
                        "objective_title": "6.5.2: The relevant entities shall:",
                        "requirement_description": "(a) establish, based on the risk assessment carried out pursuant to point 2.1, the need, scope, frequency and type of security tests;\n(b) carry out security tests according to a documented test methodology, covering the components identified as relevant for secure operation in a risk analysis;\n(c) document the type, scope, time and results of the tests, including assessment of criticality and mitigating actions for each finding;\n(d) apply mitigating actions in case of critical findings.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.5: Security testing",
                        "objective_title": "6.5.3: The relevant entities shall review and, where appropriate, update their security testing policies at planned intervals.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.5: Security testing",
                        "objective_title": "6.5.3: The relevant entities shall review and, where appropriate, update their security testing policies at planned intervals.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.6: Security patch management",
                        "objective_title": "6.6.1: The relevant entities shall specify and apply procedures, coherent with the change management procedures referred to in point 6.4.1 as well as with vulnerability management, risk management and other relevant management procedures, for ensuring that:",
                        "requirement_description": "(a) security patches are applied within a reasonable time after they become available;\n(b) security patches are tested before being applied in production systems;\n(c) security patches come from trusted sources and are checked for integrity;\n(d) additional measures are implemented and residual risks are accepted in cases where a patch is not available or not applied pursuant to point 6.6.2.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.6: Security patch management",
                        "objective_title": "6.6.1: The relevant entities shall specify and apply procedures, coherent with the change management procedures referred to in point 6.4.1 as well as with vulnerability management, risk management and other relevant management procedures, for ensuring that:",
                        "requirement_description": "(a) security patches are applied within a reasonable time after they become available;\n(b) security patches are tested before being applied in production systems;\n(c) security patches come from trusted sources and are checked for integrity;\n(d) additional measures are implemented and residual risks are accepted in cases where a patch is not available or not applied pursuant to point 6.6.2.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.6: Security patch management",
                        "objective_title": "6.6.2: By way of derogation from point 6.6.1(a), the relevant entities may choose not to apply security patches when the disadvantages of applying the security patches outweigh the cybersecurity benefits. The relevant entities shall duly document and substantiate the reasons for any such decision.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.6: Security patch management",
                        "objective_title": "6.6.2: By way of derogation from point 6.6.1(a), the relevant entities may choose not to apply security patches when the disadvantages of applying the security patches outweigh the cybersecurity benefits. The relevant entities shall duly document and substantiate the reasons for any such decision.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.7: Network security",
                        "objective_title": "6.7.1: The relevant entities shall take the appropriate measures to protect their network and information systems from cyber threats.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.7: Network security",
                        "objective_title": "6.7.1: The relevant entities shall take the appropriate measures to protect their network and information systems from cyber threats.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.7: Network security",
                        "objective_title": "6.7.2: For the purpose of point 6.7.1, the relevant entities shall:",
                        "requirement_description": "(a) document the architecture of the network in a comprehensible and up to date manner;\n(b) determine and apply controls to protect the relevant entities' internal network domains from unauthorised access;\n(c) configure controls to prevent accesses and network communication not required for the operation of the relevant entities;\n(d) determine and apply controls for remote access to network and information systems, including access by service providers;\n(e) not use systems used for administration of the security policy implementation for other purposes;\n(f) explicitly forbid or deactivate unneeded connections and services;\n(g) where appropriate, exclusively allow access to the relevant entities' network and information systems by devices authorised by those entities;\n(h) allow connections of service providers only after an authorisation request and for a set time period, such as the duration of a maintenance operation;\n(i) establish communication between distinct systems only through trusted channels that are isolated using logical, cryptographic or physical separation from other communication channels and provide assured identification of their end points and protection of the channel data from modification or disclosure;\n(j) adopt an implementation plan for the full transition towards latest generation network layer communication protocols in a secure, appropriate and gradual way and establish measures to accelerate such transition;\n(k) adopt an implementation plan for the deployment of internationally agreed and interoperable modern e-mail communications standards to secure e-mail communications to mitigate vulnerabilities linked to e-mail-related threats and establish measures to accelerate such deployment;\n(l) apply best practices for the security of the DNS, and for Internet routing security and routing hygiene of traffic originating from and destined to the network.",
                        "objective_utilities": "Establishes governance framework for network and information security",
                        "conformity_questions": [
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.7: Network security",
                        "objective_title": "6.7.2: For the purpose of point 6.7.1, the relevant entities shall:",
                        "requirement_description": "(a) document the architecture of the network in a comprehensible and up to date manner;\n(b) determine and apply controls to protect the relevant entities' internal network domains from unauthorised access;\n(c) configure controls to prevent accesses and network communication not required for the operation of the relevant entities;\n(d) determine and apply controls for remote access to network and information systems, including access by service providers;\n(e) not use systems used for administration of the security policy implementation for other purposes;\n(f) explicitly forbid or deactivate unneeded connections and services;\n(g) where appropriate, exclusively allow access to the relevant entities' network and information systems by devices authorised by those entities;\n(h) allow connections of service providers only after an authorisation request and for a set time period, such as the duration of a maintenance operation;\n(i) establish communication between distinct systems only through trusted channels that are isolated using logical, cryptographic or physical separation from other communication channels and provide assured identification of their end points and protection of the channel data from modification or disclosure;\n(j) adopt an implementation plan for the full transition towards latest generation network layer communication protocols in a secure, appropriate and gradual way and establish measures to accelerate such transition;\n(k) adopt an implementation plan for the deployment of internationally agreed and interoperable modern e-mail communications standards to secure e-mail communications to mitigate vulnerabilities linked to e-mail-related threats and establish measures to accelerate such deployment;\n(l) apply best practices for the security of the DNS, and for Internet routing security and routing hygiene of traffic originating from and destined to the network.",
                        "objective_utilities": "Establishes governance framework for network and information security",
                        "conformity_questions": [
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.7: Network security",
                        "objective_title": "6.7.3: The relevant entities shall review and, where appropriate, update these measures at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.7: Network security",
                        "objective_title": "6.7.3: The relevant entities shall review and, where appropriate, update these measures at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.8: Network segmentation",
                        "objective_title": "6.8.1: The relevant entities shall segment systems into networks or zones in accordance with the results of the risk assessment referred to in point 2.1. They shall segment their systems and networks from third parties' systems and networks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.8: Network segmentation",
                        "objective_title": "6.8.1: The relevant entities shall segment systems into networks or zones in accordance with the results of the risk assessment referred to in point 2.1. They shall segment their systems and networks from third parties' systems and networks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.8: Network segmentation",
                        "objective_title": "6.8.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) consider the functional, logical and physical relationship, including location, between trustworthy systems and services;\n(b) grant access to a network or zone based on an assessment of its security requirements;\n(c) keep systems that are critical to the relevant entities operation or to safety in secured zones;\n(d) deploy a demilitarised zone within their communication networks to ensure secure communication originating from or destined to their networks;\n(e) restrict access and communications between and within zones to those necessary for the operation of the relevant entities or for safety;\n(f) separate the dedicated network for administration of network and information systems from the relevant entities' operational network;\n(g) segregate network administration channels from other network traffic;\n(h) separate the production systems for the relevant entities' services from systems used in development and testing, including backups.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.8: Network segmentation",
                        "objective_title": "6.8.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) consider the functional, logical and physical relationship, including location, between trustworthy systems and services;\n(b) grant access to a network or zone based on an assessment of its security requirements;\n(c) keep systems that are critical to the relevant entities operation or to safety in secured zones;\n(d) deploy a demilitarised zone within their communication networks to ensure secure communication originating from or destined to their networks;\n(e) restrict access and communications between and within zones to those necessary for the operation of the relevant entities or for safety;\n(f) separate the dedicated network for administration of network and information systems from the relevant entities' operational network;\n(g) segregate network administration channels from other network traffic;\n(h) separate the production systems for the relevant entities' services from systems used in development and testing, including backups.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.8: Network segmentation",
                        "objective_title": "6.8.3: The relevant entities shall review and, where appropriate, update network segmentation at planned intervals and when significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.8: Network segmentation",
                        "objective_title": "6.8.3: The relevant entities shall review and, where appropriate, update network segmentation at planned intervals and when significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.9: Protection against malicious and unauthorised software",
                        "objective_title": "6.9.1: The relevant entities shall protect their network and information systems against malicious and unauthorised software.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.9: Protection against malicious and unauthorised software",
                        "objective_title": "6.9.1: The relevant entities shall protect their network and information systems against malicious and unauthorised software.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.9: Protection against malicious and unauthorised software",
                        "objective_title": "6.9.2: For that purpose, the relevant entities shall in particular implement measures that detect or prevent the use of malicious or unauthorised software. The relevant entities shall, where appropriate, ensure that their network and information systems are equipped with detection and response software, which is updated regularly in accordance with the risk assessment carried out pursuant to point 2.1 and the contractual agreements with the providers.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.9: Protection against malicious and unauthorised software",
                        "objective_title": "6.9.2: For that purpose, the relevant entities shall in particular implement measures that detect or prevent the use of malicious or unauthorised software. The relevant entities shall, where appropriate, ensure that their network and information systems are equipped with detection and response software, which is updated regularly in accordance with the risk assessment carried out pursuant to point 2.1 and the contractual agreements with the providers.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.1: The relevant entities shall obtain information about technical vulnerabilities in their network and information systems, evaluate their exposure to such vulnerabilities, and take appropriate measures to manage the vulnerabilities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.1: The relevant entities shall obtain information about technical vulnerabilities in their network and information systems, evaluate their exposure to such vulnerabilities, and take appropriate measures to manage the vulnerabilities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.2: For the purpose of point 6.10.1, the relevant entities shall:",
                        "requirement_description": "(a) monitor information about vulnerabilities through appropriate channels, such as announcements of CSIRTs, competent authorities or information provided by suppliers or service providers;\n(b) perform, where appropriate, vulnerability scans, and record evidence of the results of the scans, at planned intervals;\n(c) address, without undue delay, vulnerabilities identified by the relevant entities as critical to their operations;\n(d) ensure that their vulnerability handling is compatible with their change management, security patch management, risk management and incident management procedures;\n(e) lay down a procedure for disclosing vulnerabilities in accordance with the applicable national coordinated vulnerability disclosure policy.",
                        "objective_utilities": "Establishes governance framework for network and information security",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.2: For the purpose of point 6.10.1, the relevant entities shall:",
                        "requirement_description": "(a) monitor information about vulnerabilities through appropriate channels, such as announcements of CSIRTs, competent authorities or information provided by suppliers or service providers;\n(b) perform, where appropriate, vulnerability scans, and record evidence of the results of the scans, at planned intervals;\n(c) address, without undue delay, vulnerabilities identified by the relevant entities as critical to their operations;\n(d) ensure that their vulnerability handling is compatible with their change management, security patch management, risk management and incident management procedures;\n(e) lay down a procedure for disclosing vulnerabilities in accordance with the applicable national coordinated vulnerability disclosure policy.",
                        "objective_utilities": "Establishes governance framework for network and information security",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.3: When justified by the potential impact of the vulnerability, the relevant entities shall create and implement a plan to mitigate the vulnerability. In other cases, the relevant entities shall document and substantiate the reason why the vulnerability does not require remediation.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.3: When justified by the potential impact of the vulnerability, the relevant entities shall create and implement a plan to mitigate the vulnerability. In other cases, the relevant entities shall document and substantiate the reason why the vulnerability does not require remediation.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.4: The relevant entities shall review and, where appropriate, update at planned intervals the channels they use for monitoring vulnerability information.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "6: Security in network and information systems acquisition, development and maintenance (Article 21(2), point (e), of Directive (EU) 2022/2555)",
                        "subchapter": "6.1: Vulnerability handling and disclosure",
                        "objective_title": "6.10.4: The relevant entities shall review and, where appropriate, update at planned intervals the channels they use for monitoring vulnerability information.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "subchapter": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "objective_title": "7.1: For the purpose of Article 21(2), point (f) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a policy and procedures to assess whether the cybersecurity risk-management measures taken by the relevant entity are effectively implemented and maintained.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally and on a regular basis?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "subchapter": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "objective_title": "7.1: For the purpose of Article 21(2), point (f) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a policy and procedures to assess whether the cybersecurity risk-management measures taken by the relevant entity are effectively implemented and maintained.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally and on a regular basis?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "subchapter": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "objective_title": "7.2: The policy and procedures referred to in point 7.1 shall take into account results of the risk assessment pursuant to point 2.1 and past significant incidents. The relevant entities shall determine:",
                        "requirement_description": "(a) what cybersecurity risk-management measures are to be monitored and measured, including processes and controls;\n(b) the methods for monitoring, measurement, analysis and evaluation, as applicable, to ensure valid results;\n(c) when the monitoring and measuring is to be performed;\n(d) who is responsible for monitoring and measuring the effectiveness of the cybersecurity risk-management measures;\n(e) when the results from monitoring and measurement are to be analysed and evaluated;\n(f) who has to analyse and evaluate these results.",
                        "objective_utilities": "Enables systematic identification and management of cybersecurity risks",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally and on a regular basis?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "subchapter": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "objective_title": "7.2: The policy and procedures referred to in point 7.1 shall take into account results of the risk assessment pursuant to point 2.1 and past significant incidents. The relevant entities shall determine:",
                        "requirement_description": "(a) what cybersecurity risk-management measures are to be monitored and measured, including processes and controls;\n(b) the methods for monitoring, measurement, analysis and evaluation, as applicable, to ensure valid results;\n(c) when the monitoring and measuring is to be performed;\n(d) who is responsible for monitoring and measuring the effectiveness of the cybersecurity risk-management measures;\n(e) when the results from monitoring and measurement are to be analysed and evaluated;\n(f) who has to analyse and evaluate these results.",
                        "objective_utilities": "Enables systematic identification and management of cybersecurity risks",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally and on a regular basis?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "subchapter": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "objective_title": "7.3: The relevant entities shall review and, where appropriate, update the policy and procedures at planned intervals and when significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally and on a regular basis?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "subchapter": "7: Policies and procedures to assess the effectiveness of cybersecurity risk-management measures (Article 21(2), point (f), of Directive (EU) 2022/2555)",
                        "objective_title": "7.3: The relevant entities shall review and, where appropriate, update the policy and procedures at planned intervals and when significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally and on a regular basis?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.1: Awareness raising and basic cyber hygiene practices",
                        "objective_title": "8.1.1: For the purpose of Article 21(2), point (g) of Directive (EU) 2022/2555, the relevant entities shall ensure that their employees, including members of management bodies, as well as direct suppliers and service providers are aware of risks, are informed of the importance of cybersecurity and apply cyber hygiene practices.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.1: Awareness raising and basic cyber hygiene practices",
                        "objective_title": "8.1.1: For the purpose of Article 21(2), point (g) of Directive (EU) 2022/2555, the relevant entities shall ensure that their employees, including members of management bodies, as well as direct suppliers and service providers are aware of risks, are informed of the importance of cybersecurity and apply cyber hygiene practices.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.1: Awareness raising and basic cyber hygiene practices",
                        "objective_title": "8.1.2: For the purpose of point 8.1.1, the relevant entities shall offer to their employees, including members of management bodies, as well as to direct suppliers and service providers where appropriate in accordance with point 5.1.4, an awareness raising programme, which shall:",
                        "requirement_description": "(a) be scheduled over time, so that the activities are repeated and cover new employees;\n(b) be established in line with the network and information security policy, topic-specific policies and relevant procedures on network and information security;\n(c) cover relevant cyber threats, the cybersecurity risk-management measures in place, contact points and resources for additional information and advice on cybersecurity matters, as well as cyber hygiene practices for users.",
                        "objective_utilities": "Establishes governance framework for network and information security",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-01.2: Does the organization provide governance oversight reporting and recommendations to those entrusted to make executive decisions about matters considered material to the organization's cybersecurity and privacy program?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.1: Awareness raising and basic cyber hygiene practices",
                        "objective_title": "8.1.3: The awareness raising programme shall, where appropriate, be tested in terms of effectiveness. The awareness raising programme shall be updated and offered at planned intervals taking into account changes in cyber hygiene practices, and the current threat landscape and risks posed to the relevant entities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.1: Awareness raising and basic cyber hygiene practices",
                        "objective_title": "8.1.3: The awareness raising programme shall, where appropriate, be tested in terms of effectiveness. The awareness raising programme shall be updated and offered at planned intervals taking into account changes in cyber hygiene practices, and the current threat landscape and risks posed to the relevant entities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.1: The relevant entities shall identify employees, whose roles require security relevant skill sets and expertise, and ensure that they receive regular training on network and information system security.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.1: The relevant entities shall identify employees, whose roles require security relevant skill sets and expertise, and ensure that they receive regular training on network and information system security.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.2: The relevant entities shall establish, implement and apply a training program in line with the network and information security policy, topic-specific policies and other relevant procedures on network and information security which lays down the training needs for certain roles and positions based on criteria.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.2: The relevant entities shall establish, implement and apply a training program in line with the network and information security policy, topic-specific policies and other relevant procedures on network and information security which lays down the training needs for certain roles and positions based on criteria.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.3: The training referred to in point 8.2.1 shall be relevant to the job function of the employee and its effectiveness shall be assessed. Training shall take into consideration security measures in place and cover the following:",
                        "requirement_description": "(a) instructions regarding the secure configuration and operation of the network and information systems, including mobile devices;\n(b) briefing on known cyber threats;\n(c) training of the behaviour when security-relevant events occur.",
                        "objective_utilities": "Builds organizational cybersecurity capability and culture",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.3: The training referred to in point 8.2.1 shall be relevant to the job function of the employee and its effectiveness shall be assessed. Training shall take into consideration security measures in place and cover the following:",
                        "requirement_description": "(a) instructions regarding the secure configuration and operation of the network and information systems, including mobile devices;\n(b) briefing on known cyber threats;\n(c) training of the behaviour when security-relevant events occur.",
                        "objective_utilities": "Builds organizational cybersecurity capability and culture",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.4: The relevant entities shall apply training to staff members who transfer to new positions or roles which require security relevant skill sets and expertise.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.4: The relevant entities shall apply training to staff members who transfer to new positions or roles which require security relevant skill sets and expertise.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.5: The program shall be updated and run periodically taking into account applicable policies and rules, assigned roles, responsibilities, as well as known cyber threats and technological developments.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "8: Basic cyber hygiene practices and security training (Article 21(2), point (g), of Directive (EU) 2022/2555)",
                        "subchapter": "8.2: Security training",
                        "objective_title": "8.2.5: The program shall be updated and run periodically taking into account applicable policies and rules, assigned roles, responsibilities, as well as known cyber threats and technological developments.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "subchapter": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "objective_title": "9.1: For the purpose of Article 21(2), point (h) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a policy and procedures related to cryptography, with a view to ensuring adequate and effective use of cryptography to protect the confidentiality, authenticity and integrity of data in line with the relevant entities' asset classification and the results of the risk assessment carried out pursuant to point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known public standards and trusted cryptographic technologies?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "subchapter": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "objective_title": "9.1: For the purpose of Article 21(2), point (h) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a policy and procedures related to cryptography, with a view to ensuring adequate and effective use of cryptography to protect the confidentiality, authenticity and integrity of data in line with the relevant entities' asset classification and the results of the risk assessment carried out pursuant to point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known public standards and trusted cryptographic technologies?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "subchapter": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "objective_title": "9.2: The policy and procedures referred to in point 9.1 shall establish:",
                        "requirement_description": "(a) in accordance with the relevant entities' classification of assets, the type, strength and quality of the cryptographic measures required to protect the relevant entities' assets, including data at rest and data in transit;\n(b) based on point (a), the protocols or families of protocols to be adopted, as well as cryptographic algorithms, cipher strength, cryptographic solutions and usage practices to be approved and required for use in the relevant entities, following, where appropriate, a cryptographic agility approach;\n(c) the relevant entities' approach to key management, including, where appropriate, methods for the following:\n(i) generating different keys for cryptographic systems and applications;\n(ii) issuing and obtaining public key certificates;\n(iii) distributing keys to intended entities, including how to activate keys when received;\n(iv) storing keys, including how authorised users obtain access to keys;\n(v) changing or updating keys, including rules on when and how to change keys;\n(vi) dealing with compromised keys;\n(vii) revoking keys including how to withdraw or deactivate keys;\n(viii) recovering lost or corrupted keys;\n(ix) backing up or archiving keys;\n(x) destroying keys;\n(xi) logging and auditing of key management-related activities;\n(xii) setting activation and deactivation dates for keys ensuring that the keys can only be used for the specified period of time according to the organization's rules on key management.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known public standards and trusted cryptographic technologies?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "subchapter": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "objective_title": "9.2: The policy and procedures referred to in point 9.1 shall establish:",
                        "requirement_description": "(a) in accordance with the relevant entities' classification of assets, the type, strength and quality of the cryptographic measures required to protect the relevant entities' assets, including data at rest and data in transit;\n(b) based on point (a), the protocols or families of protocols to be adopted, as well as cryptographic algorithms, cipher strength, cryptographic solutions and usage practices to be approved and required for use in the relevant entities, following, where appropriate, a cryptographic agility approach;\n(c) the relevant entities' approach to key management, including, where appropriate, methods for the following:\n(i) generating different keys for cryptographic systems and applications;\n(ii) issuing and obtaining public key certificates;\n(iii) distributing keys to intended entities, including how to activate keys when received;\n(iv) storing keys, including how authorised users obtain access to keys;\n(v) changing or updating keys, including rules on when and how to change keys;\n(vi) dealing with compromised keys;\n(vii) revoking keys including how to withdraw or deactivate keys;\n(viii) recovering lost or corrupted keys;\n(ix) backing up or archiving keys;\n(x) destroying keys;\n(xi) logging and auditing of key management-related activities;\n(xii) setting activation and deactivation dates for keys ensuring that the keys can only be used for the specified period of time according to the organization's rules on key management.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known public standards and trusted cryptographic technologies?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "subchapter": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "objective_title": "9.3: The relevant entities shall review and, where appropriate, update their policy and procedures at planned intervals, taking into account the state of the art in cryptography.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known public standards and trusted cryptographic technologies?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "subchapter": "9: Cryptography (Article 21(2), point (h), of Directive (EU) 2022/2555)",
                        "objective_title": "9.3: The relevant entities shall review and, where appropriate, update their policy and procedures at planned intervals, taking into account the state of the art in cryptography.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known public standards and trusted cryptographic technologies?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.1: Human resources security",
                        "objective_title": "10.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall ensure that their employees and direct suppliers and service providers, wherever applicable, understand and commit to their security responsibilities, as appropriate for the offered services and the job and in line with the relevant entities' policy on the security of network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.1: Human resources security",
                        "objective_title": "10.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall ensure that their employees and direct suppliers and service providers, wherever applicable, understand and commit to their security responsibilities, as appropriate for the offered services and the job and in line with the relevant entities' policy on the security of network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.1: Human resources security",
                        "objective_title": "10.1.2: The requirement referred to in point 10.1.1 shall include the following:",
                        "requirement_description": "(a) mechanisms to ensure that all employees, direct suppliers and service providers, wherever applicable, understand and follow the standard cyber hygiene practices that the relevant entities apply pursuant to point 8.1;\n(b) mechanisms to ensure that all users with administrative or privileged access are aware of and act in accordance with their roles, responsibilities and authorities;\n(c) mechanisms to ensure that members of management bodies understand and act in accordance with their role, responsibilities and authorities regarding network and information system security;\n(d) mechanisms for hiring personnel qualified for the respective roles, such as reference checks, vetting procedures, validation of certifications, or written tests.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.1: Human resources security",
                        "objective_title": "10.1.2: The requirement referred to in point 10.1.1 shall include the following:",
                        "requirement_description": "(a) mechanisms to ensure that all employees, direct suppliers and service providers, wherever applicable, understand and follow the standard cyber hygiene practices that the relevant entities apply pursuant to point 8.1;\n(b) mechanisms to ensure that all users with administrative or privileged access are aware of and act in accordance with their roles, responsibilities and authorities;\n(c) mechanisms to ensure that members of management bodies understand and act in accordance with their role, responsibilities and authorities regarding network and information system security;\n(d) mechanisms for hiring personnel qualified for the respective roles, such as reference checks, vetting procedures, validation of certifications, or written tests.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.1: Human resources security",
                        "objective_title": "10.1.3: The relevant entities shall review the assignment of personnel to specific roles as referred to in point 1.2, as well as their commitment of human resources in that regard, at planned intervals and at least annually. They shall updatethe assignment where necessary.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.1: Human resources security",
                        "objective_title": "10.1.3: The relevant entities shall review the assignment of personnel to specific roles as referred to in point 1.2, as well as their commitment of human resources in that regard, at planned intervals and at least annually. They shall updatethe assignment where necessary.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.2: Verification of background",
                        "objective_title": "10.2.1: The relevant entities shall ensure to the extent feasible verification of the background of their employees, and where applicable of direct suppliers and service providers in accordance with point 5.1.4, if necessary for their role, responsibilities and authorisations.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.2: Verification of background",
                        "objective_title": "10.2.1: The relevant entities shall ensure to the extent feasible verification of the background of their employees, and where applicable of direct suppliers and service providers in accordance with point 5.1.4, if necessary for their role, responsibilities and authorisations.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.2: Verification of background",
                        "objective_title": "10.2.2: For the purpose of point 10.2.1, the relevant entities shall:",
                        "requirement_description": "(a) put in place criteria, which set out which roles, responsibilities and authorities shall only be exercised by persons whose background has been verified;\n(b) ensure that verification referred to in point 10.2.1 is performed on these persons before they start exercising these roles, responsibilities and authorities, which shall take into consideration the applicable laws, regulations, and ethics in proportion to the business requirements, the asset classification as referred to in point 12.1 and the network and information systems to be accessed, and the perceived risks.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.2: Verification of background",
                        "objective_title": "10.2.2: For the purpose of point 10.2.1, the relevant entities shall:",
                        "requirement_description": "(a) put in place criteria, which set out which roles, responsibilities and authorities shall only be exercised by persons whose background has been verified;\n(b) ensure that verification referred to in point 10.2.1 is performed on these persons before they start exercising these roles, responsibilities and authorities, which shall take into consideration the applicable laws, regulations, and ethics in proportion to the business requirements, the asset classification as referred to in point 12.1 and the network and information systems to be accessed, and the perceived risks.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.2: Verification of background",
                        "objective_title": "10.2.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and update it where necessary.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.2: Verification of background",
                        "objective_title": "10.2.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and update it where necessary.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.3: Termination or change of employment procedures",
                        "objective_title": "10.3.1: The relevant entities shall ensure that network and information system security responsibilities and duties that remain valid after termination or change of employment of their employees are contractually defined and enforced.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.3: Termination or change of employment procedures",
                        "objective_title": "10.3.1: The relevant entities shall ensure that network and information system security responsibilities and duties that remain valid after termination or change of employment of their employees are contractually defined and enforced.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.3: Termination or change of employment procedures",
                        "objective_title": "10.3.2: For the purpose of point 10.3.1, the relevant entities shall include in the individual's terms and conditions of employment, contract or agreement the responsibilities and duties that are still valid after termination of employment or contract, such as confidentiality clauses.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.3: Termination or change of employment procedures",
                        "objective_title": "10.3.2: For the purpose of point 10.3.1, the relevant entities shall include in the individual's terms and conditions of employment, contract or agreement the responsibilities and duties that are still valid after termination of employment or contract, such as confidentiality clauses.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.4: Disciplinary process",
                        "objective_title": "10.4.1: The relevant entities shall establish, communicate and maintain a disciplinary process for handling violations of network and information system security policies. The process shall take into consideration relevant legal, statutory, contractual and business requirements.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.4: Disciplinary process",
                        "objective_title": "10.4.1: The relevant entities shall establish, communicate and maintain a disciplinary process for handling violations of network and information system security policies. The process shall take into consideration relevant legal, statutory, contractual and business requirements.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.4: Disciplinary process",
                        "objective_title": "10.4.2: The relevant entities shall review and, where appropriate, update the disciplinary process at planned intervals, and when necessary due to legal changes or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "10: Human resources security (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "10.4: Disciplinary process",
                        "objective_title": "10.4.2: The relevant entities shall review and, where appropriate, update the disciplinary process at planned intervals, and when necessary due to legal changes or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall establish, document and implement logical and physical access control policies for the access to their network and information systems, based on business requirements as well as network and information system security requirements.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall establish, document and implement logical and physical access control policies for the access to their network and information systems, based on business requirements as well as network and information system security requirements.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall establish, document and implement logical and physical access control policies for the access to their network and information systems, based on business requirements as well as network and information system security requirements.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.2: The policies referred to in point 11.1.1. shall:",
                        "requirement_description": "(a) address access by persons, including staff, visitors, and external entities such as suppliers and service providers;\n(b) address access by network and information systems;\n(c) ensure that access is only granted to users that have been adequately authenticated.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.2: The policies referred to in point 11.1.1. shall:",
                        "requirement_description": "(a) address access by persons, including staff, visitors, and external entities such as suppliers and service providers;\n(b) address access by network and information systems;\n(c) ensure that access is only granted to users that have been adequately authenticated.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.2: The policies referred to in point 11.1.1. shall:",
                        "requirement_description": "(a) address access by persons, including staff, visitors, and external entities such as suppliers and service providers;\n(b) address access by network and information systems;\n(c) ensure that access is only granted to users that have been adequately authenticated.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.3: The relevant entities shall review and, where appropriate, update the policies at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.3: The relevant entities shall review and, where appropriate, update the policies at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.1: Access control policy",
                        "objective_title": "11.1.3: The relevant entities shall review and, where appropriate, update the policies at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.1: The relevant entities shall provide, modify, remove and document access rights to network and information systems in accordance with the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.1: The relevant entities shall provide, modify, remove and document access rights to network and information systems in accordance with the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.1: The relevant entities shall provide, modify, remove and document access rights to network and information systems in accordance with the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.2: The relevant entities shall:",
                        "requirement_description": "(a) assign and revoke access rights based on the principles of need-to-know, least privilege and separation of duties;\n(b) ensure that access rights are modified accordingly upon termination or change of employment;\n(c) ensure that access to network and information systems is authorised by the relevant persons;\n(d) ensure that access rights appropriately address third-party access, such as visitors, suppliers and service providers, in particular by limiting access rights in scope and in duration;\n(e) maintain a register of access rights granted;\n(f) apply logging to the management of access rights.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.2: The relevant entities shall:",
                        "requirement_description": "(a) assign and revoke access rights based on the principles of need-to-know, least privilege and separation of duties;\n(b) ensure that access rights are modified accordingly upon termination or change of employment;\n(c) ensure that access to network and information systems is authorised by the relevant persons;\n(d) ensure that access rights appropriately address third-party access, such as visitors, suppliers and service providers, in particular by limiting access rights in scope and in duration;\n(e) maintain a register of access rights granted;\n(f) apply logging to the management of access rights.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.2: The relevant entities shall:",
                        "requirement_description": "(a) assign and revoke access rights based on the principles of need-to-know, least privilege and separation of duties;\n(b) ensure that access rights are modified accordingly upon termination or change of employment;\n(c) ensure that access to network and information systems is authorised by the relevant persons;\n(d) ensure that access rights appropriately address third-party access, such as visitors, suppliers and service providers, in particular by limiting access rights in scope and in duration;\n(e) maintain a register of access rights granted;\n(f) apply logging to the management of access rights.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.3: The relevant entities shall review access rights at planned intervals and shall modify them based on organisational changes. The relevant entities shall document the results of the review including the necessary changes of access rights.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.3: The relevant entities shall review access rights at planned intervals and shall modify them based on organisational changes. The relevant entities shall document the results of the review including the necessary changes of access rights.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.2: Management of access rights",
                        "objective_title": "11.2.3: The relevant entities shall review access rights at planned intervals and shall modify them based on organisational changes. The relevant entities shall document the results of the review including the necessary changes of access rights.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.1: The relevant entities shall maintain policies for management of privileged accounts and system administration accounts as part of the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.1: The relevant entities shall maintain policies for management of privileged accounts and system administration accounts as part of the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.1: The relevant entities shall maintain policies for management of privileged accounts and system administration accounts as part of the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.2: The policies referred to in point 11.3.1 shall:",
                        "requirement_description": "(a) establish strong identification, authentication such as multi-factor authentication, and authorisation procedures for privileged accounts and system administration accounts;\n(b) set up specific accounts to be used for system administration operations exclusively, such as installation, configuration, management or maintenance;\n(c) individualise and restrict system administration privileges to the highest extent possible,\n(d) provide that system administration accounts are only used to connect to system administration systems.",
                        "objective_utilities": "Strengthens identity verification mechanisms",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.2: The policies referred to in point 11.3.1 shall:",
                        "requirement_description": "(a) establish strong identification, authentication such as multi-factor authentication, and authorisation procedures for privileged accounts and system administration accounts;\n(b) set up specific accounts to be used for system administration operations exclusively, such as installation, configuration, management or maintenance;\n(c) individualise and restrict system administration privileges to the highest extent possible,\n(d) provide that system administration accounts are only used to connect to system administration systems.",
                        "objective_utilities": "Strengthens identity verification mechanisms",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.2: The policies referred to in point 11.3.1 shall:",
                        "requirement_description": "(a) establish strong identification, authentication such as multi-factor authentication, and authorisation procedures for privileged accounts and system administration accounts;\n(b) set up specific accounts to be used for system administration operations exclusively, such as installation, configuration, management or maintenance;\n(c) individualise and restrict system administration privileges to the highest extent possible,\n(d) provide that system administration accounts are only used to connect to system administration systems.",
                        "objective_utilities": "Strengthens identity verification mechanisms",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.3: The relevant entities shall review access rights of privileged accounts and system administration accounts at planned intervals and be modified based on organisational changes, and shall document the results of the review, including the necessary changes of access rights.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.3: The relevant entities shall review access rights of privileged accounts and system administration accounts at planned intervals and be modified based on organisational changes, and shall document the results of the review, including the necessary changes of access rights.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.3: Privileged accounts and system administration accounts",
                        "objective_title": "11.3.3: The relevant entities shall review access rights of privileged accounts and system administration accounts at planned intervals and be modified based on organisational changes, and shall document the results of the review, including the necessary changes of access rights.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.4: Administration systems",
                        "objective_title": "11.4.1: The relevant entities shall restrict and control the use of system administration systems in accordance with the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.4: Administration systems",
                        "objective_title": "11.4.1: The relevant entities shall restrict and control the use of system administration systems in accordance with the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.4: Administration systems",
                        "objective_title": "11.4.1: The relevant entities shall restrict and control the use of system administration systems in accordance with the access control policy referred to in point 11.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.4: Administration systems",
                        "objective_title": "11.4.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) only use system administration systems for system administration purposes, and not for any other operations;\n(b) separate logically such systems from application software not used for system administrative purposes,\n(c) protect access to system administration systems through authentication and encryption.",
                        "objective_utilities": "Protects information confidentiality and integrity",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.4: Administration systems",
                        "objective_title": "11.4.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) only use system administration systems for system administration purposes, and not for any other operations;\n(b) separate logically such systems from application software not used for system administrative purposes,\n(c) protect access to system administration systems through authentication and encryption.",
                        "objective_utilities": "Protects information confidentiality and integrity",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.4: Administration systems",
                        "objective_title": "11.4.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) only use system administration systems for system administration purposes, and not for any other operations;\n(b) separate logically such systems from application software not used for system administrative purposes,\n(c) protect access to system administration systems through authentication and encryption.",
                        "objective_utilities": "Protects information confidentiality and integrity",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.1: The relevant entities shall manage the full life cycle of identities of network and information systems and their users.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.1: The relevant entities shall manage the full life cycle of identities of network and information systems and their users.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.1: The relevant entities shall manage the full life cycle of identities of network and information systems and their users.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) set up unique identities for network and information systems and their users;\n(b) link the identity of users to a single person;\n(c) ensure oversight of identities of network and information systems;\n(d) apply logging to the management of identitie",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) set up unique identities for network and information systems and their users;\n(b) link the identity of users to a single person;\n(c) ensure oversight of identities of network and information systems;\n(d) apply logging to the management of identitie",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) set up unique identities for network and information systems and their users;\n(b) link the identity of users to a single person;\n(c) ensure oversight of identities of network and information systems;\n(d) apply logging to the management of identitie",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.3: The relevant entities shall only permit identities assigned to multiple persons, such as shared identities, where they are necessary for business or operational reasons and are subject to an explicit approval process and documentation. The relevant entities shall take identities assigned to multiple persons into account in the cybersecurity risk management framework referred to in point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.3: The relevant entities shall only permit identities assigned to multiple persons, such as shared identities, where they are necessary for business or operational reasons and are subject to an explicit approval process and documentation. The relevant entities shall take identities assigned to multiple persons into account in the cybersecurity risk management framework referred to in point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.3: The relevant entities shall only permit identities assigned to multiple persons, such as shared identities, where they are necessary for business or operational reasons and are subject to an explicit approval process and documentation. The relevant entities shall take identities assigned to multiple persons into account in the cybersecurity risk management framework referred to in point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.4: The relevant entities shall regularly review the identities for network and information systems and their users and, if no longer needed, deactivate them without delay.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.4: The relevant entities shall regularly review the identities for network and information systems and their users and, if no longer needed, deactivate them without delay.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.5: Identification",
                        "objective_title": "11.5.4: The relevant entities shall regularly review the identities for network and information systems and their users and, if no longer needed, deactivate them without delay.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.1: The relevant entities shall implement secure authentication procedures and technologies based on access restrictions and the policy on access control.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.1: The relevant entities shall implement secure authentication procedures and technologies based on access restrictions and the policy on access control.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.1: The relevant entities shall implement secure authentication procedures and technologies based on access restrictions and the policy on access control.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) ensure the strength of authentication is appropriate to the classification of the asset to be accessed;\n(b) control the allocation to users and management of secret authentication information by a process that ensures the confidentiality of the information, including advising personnel on appropriate handling of authentication information;\n(c) require the change of authentication credentials initially, at predefined intervals and upon suspicion that the credentials were compromised;\n(d) require the reset of authentication credentials and the blocking of users after a predefined number of unsuccessful log-in attempts;\n(e) terminate inactive sessions after a predefined period of inactivity; and\n(f) require separate credentials to access privileged access or administrative accounts.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) ensure the strength of authentication is appropriate to the classification of the asset to be accessed;\n(b) control the allocation to users and management of secret authentication information by a process that ensures the confidentiality of the information, including advising personnel on appropriate handling of authentication information;\n(c) require the change of authentication credentials initially, at predefined intervals and upon suspicion that the credentials were compromised;\n(d) require the reset of authentication credentials and the blocking of users after a predefined number of unsuccessful log-in attempts;\n(e) terminate inactive sessions after a predefined period of inactivity; and\n(f) require separate credentials to access privileged access or administrative accounts.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) ensure the strength of authentication is appropriate to the classification of the asset to be accessed;\n(b) control the allocation to users and management of secret authentication information by a process that ensures the confidentiality of the information, including advising personnel on appropriate handling of authentication information;\n(c) require the change of authentication credentials initially, at predefined intervals and upon suspicion that the credentials were compromised;\n(d) require the reset of authentication credentials and the blocking of users after a predefined number of unsuccessful log-in attempts;\n(e) terminate inactive sessions after a predefined period of inactivity; and\n(f) require separate credentials to access privileged access or administrative accounts.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.3: The relevant entities shall to the extent feasible use state-of-the-art authentication methods, in accordance with the associated assessed risk and the classification of the asset to be accessed, and unique authentication information.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.3: The relevant entities shall to the extent feasible use state-of-the-art authentication methods, in accordance with the associated assessed risk and the classification of the asset to be accessed, and unique authentication information.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.3: The relevant entities shall to the extent feasible use state-of-the-art authentication methods, in accordance with the associated assessed risk and the classification of the asset to be accessed, and unique authentication information.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.4: The relevant entities shall review the authentication procedures and technologies at planned intervals.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.4: The relevant entities shall review the authentication procedures and technologies at planned intervals.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.6: Authentication",
                        "objective_title": "11.6.4: The relevant entities shall review the authentication procedures and technologies at planned intervals.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.7: Multi-factor authentication",
                        "objective_title": "11.7.1: The relevant entities shall ensure that users are authenticated by multiple authentication factors or continuous authentication mechanisms for accessing the relevant entities' network and information systems, where appropriate, in accordance with the classification of the asset to be accessed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.7: Multi-factor authentication",
                        "objective_title": "11.7.1: The relevant entities shall ensure that users are authenticated by multiple authentication factors or continuous authentication mechanisms for accessing the relevant entities' network and information systems, where appropriate, in accordance with the classification of the asset to be accessed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.7: Multi-factor authentication",
                        "objective_title": "11.7.1: The relevant entities shall ensure that users are authenticated by multiple authentication factors or continuous authentication mechanisms for accessing the relevant entities' network and information systems, where appropriate, in accordance with the classification of the asset to be accessed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.7: Multi-factor authentication",
                        "objective_title": "11.7.2: The relevant entities shall ensure that the strength of authentication is appropriate for the classification of the asset to be accessed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.7: Multi-factor authentication",
                        "objective_title": "11.7.2: The relevant entities shall ensure that the strength of authentication is appropriate for the classification of the asset to be accessed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "11: Access control (Article 21(2), points (i) and (j), of Directive (EU) 2022/2555)",
                        "subchapter": "11.7: Multi-factor authentication",
                        "objective_title": "11.7.2: The relevant entities shall ensure that the strength of authentication is appropriate for the classification of the asset to be accessed.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall lay down classification levels of all assets, including information, in scope of their network and information systems for the level of protection required.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall lay down classification levels of all assets, including information, in scope of their network and information systems for the level of protection required.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall lay down classification levels of all assets, including information, in scope of their network and information systems for the level of protection required.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.2: For the purpose of point 12.1.1, the relevant entities shall:",
                        "requirement_description": "(a) lay down a system of classification levels for assets;\n(b) associate all assets with a classification level, based on confidentiality, integrity, authenticity and availability requirements, to indicate the protection required according to their sensitivity, criticality, risk and business value;\n(c) align the availability requirements of the assets with the delivery and recovery objectives set out in their business continuity and disaster recovery plans.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.2: For the purpose of point 12.1.1, the relevant entities shall:",
                        "requirement_description": "(a) lay down a system of classification levels for assets;\n(b) associate all assets with a classification level, based on confidentiality, integrity, authenticity and availability requirements, to indicate the protection required according to their sensitivity, criticality, risk and business value;\n(c) align the availability requirements of the assets with the delivery and recovery objectives set out in their business continuity and disaster recovery plans.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.2: For the purpose of point 12.1.1, the relevant entities shall:",
                        "requirement_description": "(a) lay down a system of classification levels for assets;\n(b) associate all assets with a classification level, based on confidentiality, integrity, authenticity and availability requirements, to indicate the protection required according to their sensitivity, criticality, risk and business value;\n(c) align the availability requirements of the assets with the delivery and recovery objectives set out in their business continuity and disaster recovery plans.",
                        "objective_utilities": "Maintains critical operations during cybersecurity disruptions",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.3: The relevant entities shall conduct periodic reviews of the classification levels of assets and update them, where appropriate.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.3: The relevant entities shall conduct periodic reviews of the classification levels of assets and update them, where appropriate.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.1: Asset classification",
                        "objective_title": "12.1.3: The relevant entities shall conduct periodic reviews of the classification levels of assets and update them, where appropriate.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.1: The relevant entities shall establish, implement and apply a policy for the proper handling of assets, including information, in accordance with their network and information security policy, and shall communicate the policy on proper handling of assets to anyone who uses or handles assets.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.1: The relevant entities shall establish, implement and apply a policy for the proper handling of assets, including information, in accordance with their network and information security policy, and shall communicate the policy on proper handling of assets to anyone who uses or handles assets.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.1: The relevant entities shall establish, implement and apply a policy for the proper handling of assets, including information, in accordance with their network and information security policy, and shall communicate the policy on proper handling of assets to anyone who uses or handles assets.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.2: The policy shall:",
                        "requirement_description": "(a) cover the entire life cycle of the assets, including acquisition, use, storage, transportation and disposal;\n(b) provide rules on the safe use, safe storage, safe transport, and the irretrievable deletion and destruction of the assets;\n(c) provide that the transfer shall take place in a secure manner, in accordance with the type of asset to be transferred.",
                        "objective_utilities": "Integrates security throughout system lifecycle",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.2: The policy shall:",
                        "requirement_description": "(a) cover the entire life cycle of the assets, including acquisition, use, storage, transportation and disposal;\n(b) provide rules on the safe use, safe storage, safe transport, and the irretrievable deletion and destruction of the assets;\n(c) provide that the transfer shall take place in a secure manner, in accordance with the type of asset to be transferred.",
                        "objective_utilities": "Integrates security throughout system lifecycle",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.2: The policy shall:",
                        "requirement_description": "(a) cover the entire life cycle of the assets, including acquisition, use, storage, transportation and disposal;\n(b) provide rules on the safe use, safe storage, safe transport, and the irretrievable deletion and destruction of the assets;\n(c) provide that the transfer shall take place in a secure manner, in accordance with the type of asset to be transferred.",
                        "objective_utilities": "Integrates security throughout system lifecycle",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.2: Handling of assets",
                        "objective_title": "12.2.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.1: The relevant entities shall establish, implement and apply a policy on the management of removable storage media and communicate it to their employees and third parties who handle removable storage media at the relevant entities' premises or other locations where the removable media is connected to the relevant entities' network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.1: The relevant entities shall establish, implement and apply a policy on the management of removable storage media and communicate it to their employees and third parties who handle removable storage media at the relevant entities' premises or other locations where the removable media is connected to the relevant entities' network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.1: The relevant entities shall establish, implement and apply a policy on the management of removable storage media and communicate it to their employees and third parties who handle removable storage media at the relevant entities' premises or other locations where the removable media is connected to the relevant entities' network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.2: The policy shall:",
                        "requirement_description": "(a) provide for a technical prohibition of the connection of removable media unless there is an organisational reason for their use;\n(b) provide for disabling self-execution from such media and scanning the media for malicious code before they are used on the relevant entities' systems;\n(c) provide measures for controlling and protecting portable storage devices containing data while in transit and in storage;\n(d) where appropriate, provide measures for the use of cryptographic techniques to protect data on removable storage media.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.2: The policy shall:",
                        "requirement_description": "(a) provide for a technical prohibition of the connection of removable media unless there is an organisational reason for their use;\n(b) provide for disabling self-execution from such media and scanning the media for malicious code before they are used on the relevant entities' systems;\n(c) provide measures for controlling and protecting portable storage devices containing data while in transit and in storage;\n(d) where appropriate, provide measures for the use of cryptographic techniques to protect data on removable storage media.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.2: The policy shall:",
                        "requirement_description": "(a) provide for a technical prohibition of the connection of removable media unless there is an organisational reason for their use;\n(b) provide for disabling self-execution from such media and scanning the media for malicious code before they are used on the relevant entities' systems;\n(c) provide measures for controlling and protecting portable storage devices containing data while in transit and in storage;\n(d) where appropriate, provide measures for the use of cryptographic techniques to protect data on removable storage media.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.3: Removable media policy",
                        "objective_title": "12.3.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.1: The relevant entities shall develop and maintain a complete, accurate, up-to-date and consistent inventory of their assets. They shall record changes to the entries in the inventory in a traceable manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.1: The relevant entities shall develop and maintain a complete, accurate, up-to-date and consistent inventory of their assets. They shall record changes to the entries in the inventory in a traceable manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.1: The relevant entities shall develop and maintain a complete, accurate, up-to-date and consistent inventory of their assets. They shall record changes to the entries in the inventory in a traceable manner.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.2: The granularity of the inventory of the assets shall be at a level appropriate for the needs of the relevant entities. The inventory shall include the following:",
                        "requirement_description": "(a) the list of operations and services and their description,\n(b) the list of network and information systems and other associated assets supporting the relevant entities' operations and services.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.2: The granularity of the inventory of the assets shall be at a level appropriate for the needs of the relevant entities. The inventory shall include the following:",
                        "requirement_description": "(a) the list of operations and services and their description,\n(b) the list of network and information systems and other associated assets supporting the relevant entities' operations and services.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.2: The granularity of the inventory of the assets shall be at a level appropriate for the needs of the relevant entities. The inventory shall include the following:",
                        "requirement_description": "(a) the list of operations and services and their description,\n(b) the list of network and information systems and other associated assets supporting the relevant entities' operations and services.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.3: The relevant entities shall regularly review and update the inventory and their assets and document the history of changes.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.3: The relevant entities shall regularly review and update the inventory and their assets and document the history of changes.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.4: Asset inventory",
                        "objective_title": "12.4.3: The relevant entities shall regularly review and update the inventory and their assets and document the history of changes.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.5: Deposit, return or deletion of assets upon termination of employment",
                        "objective_title": "12.5.1: The relevant entities shall establish, implement and apply procedures which ensure that their assets which are under custody of personnel are deposited, returned or deleted upon termination of employment, and shall document the deposit, return and deletion of those assets. Where the deposit, return or deletion of assets is not possible, the relevant entities shall ensure that the assets can no longer access the relevant entities' network and information systems in accordance with point 12.2.2.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.5: Deposit, return or deletion of assets upon termination of employment",
                        "objective_title": "12.5.1: The relevant entities shall establish, implement and apply procedures which ensure that their assets which are under custody of personnel are deposited, returned or deleted upon termination of employment, and shall document the deposit, return and deletion of those assets. Where the deposit, return or deletion of assets is not possible, the relevant entities shall ensure that the assets can no longer access the relevant entities' network and information systems in accordance with point 12.2.2.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "12: Asset management (Article 21(2), point (i), of Directive (EU) 2022/2555)",
                        "subchapter": "12.5: Deposit, return or deletion of assets upon termination of employment",
                        "objective_title": "12.5.1: The relevant entities shall establish, implement and apply procedures which ensure that their assets which are under custody of personnel are deposited, returned or deleted upon termination of employment, and shall document the deposit, return and deletion of those assets. Where the deposit, return or deletion of assets is not possible, the relevant entities shall ensure that the assets can no longer access the relevant entities' network and information systems in accordance with point 12.2.2.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.1: For the purpose of Article 21(2)(c) of Directive (EU) 2022/2555, the relevant entities shall prevent loss, damage or compromise of network and information systems or interruption to their operations due to the failure and disruption of supporting utilities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.1: For the purpose of Article 21(2)(c) of Directive (EU) 2022/2555, the relevant entities shall prevent loss, damage or compromise of network and information systems or interruption to their operations due to the failure and disruption of supporting utilities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.1: For the purpose of Article 21(2)(c) of Directive (EU) 2022/2555, the relevant entities shall prevent loss, damage or compromise of network and information systems or interruption to their operations due to the failure and disruption of supporting utilities.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.2: For that purpose, the relevant entities shall, where appropriate:",
                        "requirement_description": "(a) protect facilities from power failures and other disruptions caused by failures in supporting utilities such as electricity, telecommunications, water supply, gas, sewage, ventilation and air conditioning;\n(b) consider the use of redundancy in utilities services;\n(c) protect utility services for electricity and telecommunications, which transport data or supply network and information systems, against interception and damage;\n(d) monitor the utility services referred to in point (c) and report to the competent internal or external personnel events outside the minimum and maximum control thresholds referred to in point 13.2.2(b) affecting the utility services;\n(e) conclude contracts for the emergency supply with corresponding services, such as for the fuel for emergency power supply;\n(f) ensure continuous effectiveness, monitor, maintain and test the supply of the network and information systems necessary for the operation of the service offered, in particular the electricity, temperature and humidity control, telecommunications and Internet connection.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.2: For that purpose, the relevant entities shall, where appropriate:",
                        "requirement_description": "(a) protect facilities from power failures and other disruptions caused by failures in supporting utilities such as electricity, telecommunications, water supply, gas, sewage, ventilation and air conditioning;\n(b) consider the use of redundancy in utilities services;\n(c) protect utility services for electricity and telecommunications, which transport data or supply network and information systems, against interception and damage;\n(d) monitor the utility services referred to in point (c) and report to the competent internal or external personnel events outside the minimum and maximum control thresholds referred to in point 13.2.2(b) affecting the utility services;\n(e) conclude contracts for the emergency supply with corresponding services, such as for the fuel for emergency power supply;\n(f) ensure continuous effectiveness, monitor, maintain and test the supply of the network and information systems necessary for the operation of the service offered, in particular the electricity, temperature and humidity control, telecommunications and Internet connection.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.2: For that purpose, the relevant entities shall, where appropriate:",
                        "requirement_description": "(a) protect facilities from power failures and other disruptions caused by failures in supporting utilities such as electricity, telecommunications, water supply, gas, sewage, ventilation and air conditioning;\n(b) consider the use of redundancy in utilities services;\n(c) protect utility services for electricity and telecommunications, which transport data or supply network and information systems, against interception and damage;\n(d) monitor the utility services referred to in point (c) and report to the competent internal or external personnel events outside the minimum and maximum control thresholds referred to in point 13.2.2(b) affecting the utility services;\n(e) conclude contracts for the emergency supply with corresponding services, such as for the fuel for emergency power supply;\n(f) ensure continuous effectiveness, monitor, maintain and test the supply of the network and information systems necessary for the operation of the service offered, in particular the electricity, temperature and humidity control, telecommunications and Internet connection.",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.3: The relevant entities shall test, review and, where appropriate, update the protection measures on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.3: The relevant entities shall test, review and, where appropriate, update the protection measures on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.1: Supporting utilities",
                        "objective_title": "13.1.3: The relevant entities shall test, review and, where appropriate, update the protection measures on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.1: For the purpose of Article 21(2)(e) of Directive (EU) 2022/2555, the relevant entities shall prevent or reduce the consequences of events originating from physical and environmental threats, such as natural disasters and other intentional or unintentional threats, based on the results of the risk assessment carried out pursuant to point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.1: For the purpose of Article 21(2)(e) of Directive (EU) 2022/2555, the relevant entities shall prevent or reduce the consequences of events originating from physical and environmental threats, such as natural disasters and other intentional or unintentional threats, based on the results of the risk assessment carried out pursuant to point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.1: For the purpose of Article 21(2)(e) of Directive (EU) 2022/2555, the relevant entities shall prevent or reduce the consequences of events originating from physical and environmental threats, such as natural disasters and other intentional or unintentional threats, based on the results of the risk assessment carried out pursuant to point 2.1.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.2: For that purpose, the relevant entities shall, where appropriate:",
                        "requirement_description": "(a) design and implement protection measures against physical and environmental threats;\n(b) determine minimum and maximum control thresholds for physical and environmental threats;\n(c) monitor environmental parameters and report to the competent internal or external personnel events outside the minimum and maximum control thresholds referred to in point (b).",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.2: For that purpose, the relevant entities shall, where appropriate:",
                        "requirement_description": "(a) design and implement protection measures against physical and environmental threats;\n(b) determine minimum and maximum control thresholds for physical and environmental threats;\n(c) monitor environmental parameters and report to the competent internal or external personnel events outside the minimum and maximum control thresholds referred to in point (b).",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.2: For that purpose, the relevant entities shall, where appropriate:",
                        "requirement_description": "(a) design and implement protection measures against physical and environmental threats;\n(b) determine minimum and maximum control thresholds for physical and environmental threats;\n(c) monitor environmental parameters and report to the competent internal or external personnel events outside the minimum and maximum control thresholds referred to in point (b).",
                        "objective_utilities": "Ensures appropriate personnel security measures",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.3: The relevant entities shall test, review and, where appropriate, update the protection measures against physical and environmental threats on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.3: The relevant entities shall test, review and, where appropriate, update the protection measures against physical and environmental threats on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.2: Protection against physical and environmental threats",
                        "objective_title": "13.2.3: The relevant entities shall test, review and, where appropriate, update the protection measures against physical and environmental threats on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.1: For the purpose of Article 21(2)(i) of Directive (EU) 2022/2555, the relevant entities shall prevent and monitor unauthorised physical access, damage and interference to their network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.1: For the purpose of Article 21(2)(i) of Directive (EU) 2022/2555, the relevant entities shall prevent and monitor unauthorised physical access, damage and interference to their network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.1: For the purpose of Article 21(2)(i) of Directive (EU) 2022/2555, the relevant entities shall prevent and monitor unauthorised physical access, damage and interference to their network and information systems.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) on the basis of the risk assessment carried out pursuant to point 2.1, lay down and use security perimeters to protect areas where network and information systems and other associated assets are located;\n(b) protect the areas referred to in point (a) by appropriate entry controls and access points;\n(c) design and implement physical security for offices, rooms and facilities,\n(d) continuously monitor their premises for unauthorised physical access.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) on the basis of the risk assessment carried out pursuant to point 2.1, lay down and use security perimeters to protect areas where network and information systems and other associated assets are located;\n(b) protect the areas referred to in point (a) by appropriate entry controls and access points;\n(c) design and implement physical security for offices, rooms and facilities,\n(d) continuously monitor their premises for unauthorised physical access.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.2: For that purpose, the relevant entities shall:",
                        "requirement_description": "(a) on the basis of the risk assessment carried out pursuant to point 2.1, lay down and use security perimeters to protect areas where network and information systems and other associated assets are located;\n(b) protect the areas referred to in point (a) by appropriate entry controls and access points;\n(c) design and implement physical security for offices, rooms and facilities,\n(d) continuously monitor their premises for unauthorised physical access.",
                        "objective_utilities": "Supports NIS2 Directive compliance requirements",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.3: The relevant entities shall test, review and, where appropriate, update the physical access control measures on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.3: The relevant entities shall test, review and, where appropriate, update the physical access control measures on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            },
            {
                        "chapter_title": "13: Environmental and physical security (Article 21(2), points (c), (e) and (i) of Directive (EU) 2022/2555)",
                        "subchapter": "13.3: Perimeter and physical access control",
                        "objective_title": "13.3.3: The relevant entities shall test, review and, where appropriate, update the physical access control measures on a regular basis or following significant incidents or significant changes to operations or risks.",
                        "requirement_description": "",
                        "objective_utilities": "Supports NIS2 compliance objectives",
                        "conformity_questions": [
                                    "Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.",
                                    "Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.",
                                    "Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, contract tools and procurement methods to meet unique business needs?.",
                                    "Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network security controls?.",
                                    "Q-MNT-01: Does the organization develop, disseminate, review & update procedures to facilitate the implementation of maintenance controls across the enterprise?.",
                                    "Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.",
                                    "Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.",
                                    "Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a disruption, compromise or failure?.",
                                    "Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.",
                                    "Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.",
                                    "Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit by designated organizational officials?.",
                                    "Q-AST-01: Does the organization facilitate the implementation of asset management controls?.",
                                    "Q-GOV-15.2: Does the organization compel data and/or process owners to implement required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15.1: Does the organization compel data and/or process owners to select required cybersecurity and privacy controls for each system, application and/or service under their control?.",
                                    "Q-GOV-15: Does the organization compel data and/or process owners to operationalize cybersecurity and privacy practices for each system, application and/or service under their control?.",
                                    "Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards and procedures?.",
                                    "Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?."
                        ]
            }
]
        
        return nis2_directive_items
