# app/seeds/soc_2_seed.py
import io
import logging
from .base_seed import BaseSeed
from app.models import models
from app.constants.soc_2_connections import SOC2_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class Soc2Seed(BaseSeed):
    """Seed SOC 2 framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating SOC 2 framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create SOC 2 Framework
        soc_2_framework, created = self.get_or_create(
            models.Framework,
            {"name": "SOC 2", "organisation_id": default_org.id},
            {
                "name": "SOC 2",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("SOC 2 framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == soc_2_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == soc_2_framework.id
            ).all()

            # Keep links in sync even when framework/objectives already exist.
            # This is idempotent and allows updated mapping files to apply.
            if not self.skip_wire_connections:
                self._wire_connections(soc_2_framework, default_org, existing_objectives)
            self.db.commit()

            logger.info(f"Found existing SOC 2 framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            return {
                "framework": soc_2_framework,
                "conformity_questions": existing_questions,
                "objectives": existing_objectives
            }

        # Get unique questions and objectives
        unique_conformity_questions = self._get_unique_conformity_questions()
        unique_objectives_data = self._get_unique_objectives()

        # Create conformity questions
        conformity_questions = []
        question_order = 1

        for conf_q_text in unique_conformity_questions:
            # Always create new questions for each framework (no sharing across frameworks)
            question = models.Question(
                text=conf_q_text,
                description="SOC 2 conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=soc_2_framework.id,
                question_id=question.id,
                order=question_order
            )
            self.db.add(framework_question)

            question_order += 1

        # Create chapters and objectives
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
                        "framework_id": soc_2_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": soc_2_framework.id
                    }
                )
                chapters_dict[chapter_title] = chapter

            chapter = chapters_dict[chapter_title]

            # Create objective
            objective, created = self.get_or_create(
                models.Objectives,
                {
                    "title": item['objective_title'],
                    "chapter_id": chapter.id
                },
                {
                    "title": item['objective_title'],
                    "subchapter": item.get('subchapter'),
                    "chapter_id": chapter.id,
                    "requirement_description": item.get('requirement_description')
                }
            )
            objectives_list.append(objective)

        self.db.flush()

        # Wire connections: risks, controls, policies -> objectives
        if not self.skip_wire_connections:
            self._wire_connections(soc_2_framework, default_org, objectives_list)

        self.db.commit()

        logger.info(f"Created SOC 2 framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": soc_2_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _wire_connections(self, framework, org, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to SOC 2 objectives using the SOC2_CONNECTIONS mapping.
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
            logger.warning("Missing lookup defaults - skipping SOC 2 connection wiring")
            return

        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in SOC2_CONNECTIONS.values():
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

        logger.info(f"SOC 2 wiring: {len(risk_name_to_id)} risks ready")

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
        iso_set, _ = self.get_or_create(
            models.ControlSet,
            {"name": "ISO 27001 Controls (Legacy)", "organisation_id": org.id},
            {
                "name": "ISO 27001 Controls (Legacy)",
                "description": "ISO/IEC 27001 controls - Information security management systems (legacy format)",
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
                control_set_id = iso_set.id if code.startswith("A") else baseline_set.id
                control = models.Control(
                    code=code,
                    name=tmpl.name if tmpl else code,
                    description=tmpl.description if tmpl else "",
                    control_set_id=control_set_id,
                    control_status_id=not_implemented.id,
                    organisation_id=org.id,
                )
                self.db.add(control)
                self.db.flush()
                control_code_to_id[code] = control.id

        logger.info(f"SOC 2 wiring: {len(control_code_to_id)} controls ready")

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
                        logger.warning(f"SOC 2 wiring: docx conversion failed for {policy_code}: {conv_err}")
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

        logger.info(f"SOC 2 wiring: {len(policy_code_to_id)} policies ready")

        obj_title_to_id = {obj.title: obj.id for obj in objectives_list}
        policy_framework_pairs = set()

        obj_risk_count = 0
        obj_ctrl_count = 0
        pol_obj_count = 0
        ctrl_risk_count = 0
        ctrl_pol_count = 0
        planned_control_risk_pairs = set()
        planned_control_policy_pairs = set()

        for obj_title, conn in SOC2_CONNECTIONS.items():
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
            f"SOC 2 wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return ['Q-HRS-07.1: Does the organization conduct employee misconduct investigations when there is reasonable assurance that '
         'a policy has been violated? .',
         'Q-HRS-05.1: Does the organization define acceptable and unacceptable rules of behavior for the use of technologies, '
         'including consequences for unacceptable behavior?.',
         'Q-HRS-05: Does the organization require all employees and contractors to apply cybersecurity and privacy principles '
         'in their daily work?.',
         'Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.',
         'Q-CPL-02: Does the organization provide a security & privacy controls oversight function that reports to the '
         "organization's executive leadership?.",
         'Q-HRS-03.2: Does the organization ensure that all security-related positions are staffed by qualified individuals '
         'who have the necessary skill set? .',
         'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
         'Q-HRS-02: Does the organization manage personnel security risk by assigning a risk designation to all positions and '
         'establishing screening criteria for individuals filling those positions?.',
         'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) to assist senior management '
         'in performance monitoring and trend analysis of the cybersecurity and privacy program?.',
         'Q-GOV-05.1: Does the organization develop, report and monitor Key Performance Indicators (KPIs) to assist '
         'organizational management in performance monitoring and trend analysis of the cybersecurity and privacy program?.',
         'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for its cybersecurity and '
         'privacy programs?.',
         'Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?.',
         'Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.',
         'Q-PRM-06: Does the organization define business processes with consideration for cybersecurity and privacy that '
         'determines:   -  The resulting risk to organizational operations, assets, individuals and other organizations; and  '
         '-  Information protection needs arising from the defined business processes and revises the processes as necessary, '
         'until an achievable set of protection needs is obtained?.',
         'Q-GOV-04: Does the organization assign a qualified individual with the mission and resources to centrally-manage '
         'coordinate, develop, implement and maintain an enterprise-wide cybersecurity and privacy program? .',
         'Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness '
         'controls? .',
         'Q-PRM-03: Does the organization identify and allocate resources for management, operational, technical and privacy '
         'requirements within business process planning for projects / initiatives?.',
         'Q-PRM-02: Does the organization address all capital planning and investment requests, including the resources needed '
         'to implement the security & privacy programs and documents all exceptions to this requirement? .',
         'Q-HRS-04.2: Does the organization verify that individuals accessing a system processing, storing, or transmitting '
         'sensitive information are formally indoctrinated for all the relevant types of information to which they have access '
         'on the system?.',
         'Q-HRS-04.1: Does the organization ensure that individuals accessing a system that stores, transmits or processes '
         'information requiring special protection satisfy organization-defined personnel screening criteria?.',
         'Q-HRS-04: Does the organization manage personnel security risk by screening individuals prior to authorizing '
         'access?.',
         'Q-HRS-03.1: Does the organization communicate with users about their roles and responsibilities to maintain a safe '
         'and secure working environment?.',
         'Q-HRS-02.1: Does the organization ensure that every user accessing a system that processes, stores, or transmits '
         'sensitive information is cleared and regularly trained to handle the information in question?.',
         'Q-HRS-09.3: Does the organization govern former employee behavior by notifying terminated individuals of applicable, '
         'legally binding post-employment requirements for the protection of organizational information?.',
         "Q-HRS-09.2: Does the organization expedite the process of removing 'high risk' individual's access to systems and "
         'applications upon termination, as determined by management?.',
         "Q-HRS-09.1: Does the organization retrieve organization-owned assets upon termination of an individual's "
         'employment?.',
         'Q-HRS-09: Does the organization govern the termination of individual employment?.',
         'Q-HRS-08: Does the organization adjust logical and physical access authorizations to systems and facilities upon '
         'personnel reassignment or transfer, in a timely manner?.',
         'Q-HRS-07: Does the organization sanction personnel failing to comply with established security policies, standards '
         'and procedures? .',
         'Q-HRS-06.1: Does the organization require Non-Disclosure Agreements (NDAs) or similar confidentiality agreements '
         'that reflect the needs to protect data and operational details, for both employees and third-parties?.',
         'Q-HRS-06: Does the organization require internal and third-party users to sign appropriate access agreements prior '
         'to being granted access? .',
         'Q-OPS-03: Does the organization define supporting business processes and implement appropriate governance and '
         "service management to ensure appropriate planning, delivery and support of the organization's technology "
         'capabilities supporting business functions, workforce, and/or customers based on industry-recognized standards? .',
         'Q-DCH-22: Does the organization check for the accuracy, relevance, timeliness, impact, completeness and '
         'de-identification of information across the information lifecycle?.',
         'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with applicable statutory, '
         'regulatory and contractual requirements? .',
         'Q-DCH-01.1: Does the organization ensure data stewardship is assigned, documented and communicated? .',
         'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? .',
         'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain sufficient detail to '
         "assess the security of the network's architecture;  -  Reflect the current architecture of the network environment; "
         'and  -  Document all sensitive/regulated data flows?.',
         'Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar mechanisms, to identify '
         'and document day-to-day procedures to enable the proper execution of assigned tasks?.',
         'Q-OPS-01: Does the organization facilitate the implementation of operational security controls?.',
         'Q-SEA-02.1: Does the organization standardize technology and process terminology to reduce confusion amongst groups '
         'and departments? .',
         'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized cybersecurity and privacy '
         'practices in the specification, design, development, implementation and modification of systems and services?.',
         'Q-PRM-05: Does the organization identify critical system components and functions by performing a criticality '
         'analysis for critical systems, system components or services at pre-defined decision points in the Secure '
         'Development Life Cycle (SDLC)? .',
         'Q-PRM-01: Does the organization facilitate the implementation of cybersecurity and privacy-related resource planning '
         'controls?.',
         'Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, regulatory and contractual '
         'controls?.',
         'Q-PRI-14: Does the organization develop, disseminate and update reports to internal senior management, as well as '
         'external oversight bodies, as appropriate, to demonstrate accountability with specific statutory and regulatory '
         'privacy program mandates?.',
         'Q-IRO-14: Does the organization maintain incident response contacts with applicable regulatory and law enforcement '
         'agencies? .',
         'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational incident response personnel '
         'within organization-defined time-periods; and  -  Externally to regulatory authorities and affected parties, as '
         'necessary?.',
         'Q-GOV-06: Does the organization identify and document appropriate contacts within relevant law enforcement and '
         'regulatory bodies?.',
         'Q-SEA-02: Does the organization develop an enterprise architecture, aligned with industry-recognized leading '
         'practices, with consideration for cybersecurity and privacy principles that addresses risk to organizational '
         'operations, assets, individuals, other organizations? .',
         'Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the '
         'development, acquisition, maintenance and disposal of systems, system components and services, including documenting '
         'selected mitigating actions and monitoring performance against those plans?.',
         'Q-PRM-04: Does the organization assess cybersecurity and privacy controls in system project development to determine '
         'the extent to which the controls are implemented correctly, operating as intended and producing the desired outcome '
         'with respect to meeting the requirements?.',
         'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and assess cybersecurity and '
         'data protection risks?.',
         'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy assessments, incidents and '
         'audits to ensure proper remediation has been performed?.',
         'Q-THR-04: Does the organization implement an insider threat program that includes a cross-discipline insider threat '
         'incident handling team? .',
         'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the potential attack vectors that '
         'attackers could use to attack the organization? .',
         'Q-THR-01: Does the organization implement a threat awareness program that includes a cross-organization '
         'information-sharing capability? .',
         'Q-TPM-04.3: Does the organization ensure that the interests of third-party service providers are consistent with and '
         'reflect organizational interests?.',
         "Q-TPM-04: Does the organization mitigate the risks associated with third-party access to the organization's systems "
         'and data?.',
         'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools and procurement methods '
         'for the purchase of unique systems, system components or services?.',
         'Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.',
         'Q-TPM-10: Does the organization control changes to services by suppliers, taking into account the criticality of '
         'business information, systems and processes that are in scope by the third-party?.',
         'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service Providers (TSP) for '
         'compliance with established contractual requirements for cybersecurity and privacy controls? .',
         'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or outsourcing of '
         'technology-related services?.',
         'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, prior to the implementation '
         'of the change?.',
         'Q-CHG-02.3: Does the organization include a cybersecurity representative in the configuration change control review '
         'process?.',
         'Q-CHG-02.2: Does the organization appropriately test and document proposed changes in a non-production environment '
         'before changes are implemented in a production environment?.',
         'Q-CHG-02: Does the organization govern the technical configuration change control processes?.',
         'Q-CHG-01: Does the organization facilitate the implementation of a change management program?.',
         'Q-IAO-06: Does the organization perform Information Assurance Program (IAP) activities to evaluate the design, '
         'implementation and effectiveness of technical cybersecurity and privacy controls?.',
         'Q-IAO-04: Does the organization require system developers and integrators to create and execute a Security Test and '
         'Evaluation (ST&E) plan to identify and remediate flaws during development?.',
         'Q-IAO-03.1: Does the organization plan and coordinate Information Assurance Program (IAP) activities with affected '
         'stakeholders before conducting such activities in order to reduce the potential impact on operations? .',
         'Q-IAO-02.2: Does the organization conduct specialized assessments for:   -  Statutory, regulatory and contractual '
         'compliance obligations;  -  Monitoring capabilities;   -  Mobile devices;  -  Databases;  -  Application security;  '
         '-  Embedded technologies (e.g., IoT, OT, etc.);  -  Vulnerability management;   -  Malicious code;   -  Insider '
         'threats and  -  Performance/load testing? .',
         'Q-IAO-02.1: Does the organization ensure assessors or assessment teams have the appropriate independence to conduct '
         'cybersecurity and privacy control assessments? .',
         'Q-IAO-02: Does the organization formally assess the cybersecurity and privacy controls in systems, applications and '
         'services through Information Assurance Program (IAP) activities to determine the extent to which the controls are '
         'implemented correctly, operating as intended and producing the desired outcome with respect to meeting expected '
         'requirements?.',
         'Q-IAO-01: Does the organization facilitate the implementation of cybersecurity and privacy assessment and '
         'authorization controls? .',
         'Q-CPL-04: Does the organization thoughtfully plan audits by including input from operational risk and compliance '
         'partners to minimize the impact of audit-related activities on business operations?.',
         "Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the organization's "
         'cybersecurity and privacy policies and standards? .',
         'Q-CPL-03: Does the organization ensure managers regularly review the processes and documented procedures within '
         'their area of responsibility to adhere to appropriate security policies, standards and other applicable '
         'requirements?.',
         'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing basis and ensure assets are '
         'protected against known attacks? .',
         'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, tracked and remediated?.',
         'Q-TPM-09: Does the organization address weaknesses or deficiencies in supply chain elements identified during '
         'independent or organizational assessments of such elements? .',
         'Q-TDA-15: Does the organization require system developers and integrators to create a Security Test and Evaluation '
         '(ST&E) plan and implement the plan under the witness of an independent party? .',
         'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
         'Q-IAO-05: Does the organization use a Plan of Action and Milestones (POA&M), or similar mechanisms, to document '
         'planned remedial actions to correct weaknesses or deficiencies noted during the assessment of the security controls '
         'and to reduce or eliminate known vulnerabilities?.',
         'Q-OPS-02: Does the organization develop a security Concept of Operations (CONOPS) that documents management, '
         'operational and technical measures implemented to apply defense-in-depth techniques?.',
         'Q-SEA-01.1: Does the organization centrally-manage the organization-wide management and implementation of '
         'cybersecurity and privacy controls and related processes?.',
         'Q-HRS-11: Does the organization implement and maintain Separation of Duties (SoD) to prevent potential inappropriate '
         'activity without collusion?.',
         'Q-TDA-02: Does the organization ensure risk-based technical and functional specifications are established to define '
         'a Minimum Viable Product (MVP)?.',
         'Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, '
         'contract tools and procurement methods to meet unique business needs?.',
         'Q-RSK-10: Does the organization conduct a Data Protection Impact Assessment (DPIA) on systems, applications and '
         'services that store, process and/or transmit Personal Data (PD) to identify and remediate reasonably-expected '
         'risks?.',
         'Q-PRM-07: Does the organization ensure changes to systems within the Secure Development Life Cycle (SDLC) are '
         'controlled through formal change control procedures? .',
         'Q-HRS-10: Does the organization govern third-party personnel by reviewing and monitoring third-party cybersecurity '
         'and privacy roles and responsibilities?.',
         'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and procedures at planned '
         'intervals or if significant changes occur to ensure their continuing suitability, adequacy and effectiveness? .',
         'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards '
         'and procedures?.',
         'Q-NET-06.1: Does the organization implement security management subnets to isolate security tools and support '
         'components from other internal system components by implementing separate subnetworks with managed interfaces to '
         'other components of the system? .',
         'Q-NET-06: Does the organization logically or physically segment information flows to accomplish network '
         'segmentation?.',
         'Q-NET-05.1: Does the organization prohibit the direct connection of a sensitive system to an external network '
         'without the use of an organization-defined boundary protection device? .',
         'Q-NET-04: Does the organization design, implement and review firewall and router configurations to restrict '
         'connections between untrusted networks and internal systems? .',
         'Q-NET-03.1: Does the organization limit the number of concurrent external network connections to its systems?.',
         'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to monitor and control '
         'communications at the external network boundary and at key internal boundaries within the network?.',
         'Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network '
         'security controls?.',
         'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only authorized access to processes '
         'necessary to accomplish assigned tasks in accordance with organizational business functions? .',
         'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that conform to the principle of '
         "'least privilege?'.",
         'Q-IAC-16: Does the organization restrict and control privileged access rights for users and services?.',
         'Q-IAC-15: Does the organization proactively govern account management of individual, group, system, application, '
         'guest and temporary accounts?.',
         'Q-IAC-10.8: Does the organization ensure vendor-supplied defaults are changed as part of the installation process?.',
         'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
         'Q-IAC-09.1: Does the organization ensure proper user identification management for non-consumer users and '
         'administrators? .',
         'Q-IAC-09: Does the organization govern naming standards for usernames and systems?.',
         'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over users and resources?.',
         'Q-IAC-05: Does the organization identify and authenticate third-party systems and services?.',
         'Q-IAC-04: Does the organization uniquely and centrally Authenticate, Authorize and Audit (AAA) devices before '
         'establishing a connection using bidirectional authentication that is cryptographically- based and replay resistant?.',
         'Q-IAC-03: Does the organization uniquely and centrally Authenticate, Authorize and Audit (AAA) third-party users and '
         'processes that provide services to the organization?.',
         'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users and processes acting on '
         'behalf of organizational users? .',
         'Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.',
         'Q-CRY-09.2: Does the organization facilitate the production and management of asymmetric cryptographic keys using '
         'Federal Information Processing Standards (FIPS)-compliant key management technology and processes that protect the '
         "user's private key?.",
         'Q-CRY-09.1: Does the organization facilitate the production and management of symmetric cryptographic keys using '
         'Federal Information Processing Standards (FIPS)-compliant key management technology and processes? .',
         'Q-CRY-09: Does the organization facilitate cryptographic key management controls to protect the confidentiality, '
         'integrity and availability of keys?.',
         'Q-CRY-08: Does the organization securely implement an internal Public Key Infrastructure (PKI) infrastructure or '
         'obtain PKI services from a reputable PKI service provider?.',
         'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent unauthorized disclosure of data '
         'at rest? .',
         'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the confidentiality of data being '
         'transmitted? .',
         'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known '
         'public standards and trusted cryptographic technologies?.',
         'Q-IAC-17: Does the organization periodically-review the privileges assigned to individuals and service accounts to '
         'validate the need for such privileges and reassign or remove unnecessary privileges, as necessary?.',
         'Q-PES-03: Does the organization enforce physical access authorizations for all physical access points (including '
         'designated entry/exit points) to facilities (excluding those areas within the facility officially designated as '
         'publicly accessible)?.',
         'Q-PES-02.1: Does the organization authorize physical access to facilities based on the position or role of the '
         'individual?.',
         'Q-PES-02: Does the organization maintain a current list of personnel with authorized access to organizational '
         'facilities (except for those areas within the facility officially designated as publicly accessible)?.',
         'Q-PES-01: Does the organization facilitate the operation of physical and environmental protection controls? .',
         'Q-TDA-11.2: [deprecated - incorporated into AST-09].',
         'Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for an organization-defined '
         'time period to fulfill the purpose(s) identified in the notice or as required by law;  -  Disposes of, destroys, '
         'erases, and/or anonymizes the PI, regardless of the method of storage; and  -  Uses organization-defined techniques '
         'or methods to ensure secure deletion or destruction of PD (including originals, copies and archived records)?.',
         'Q-DCH-21: Does the organization securely dispose of, destroy or erase information?.',
         'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity commensurate with the '
         'classification or sensitivity of the information prior to disposal, release out of organizational control or release '
         'for reuse?.',
         'Q-DCH-08: Does the organization securely dispose of media when it is no longer required, using formal procedures? .',
         'Q-AST-09: Does the organization securely dispose of, destroy or repurpose system components using '
         'organization-defined techniques and methods to prevent such components from entering the gray market?.',
         'Q-NET-14: Does the organization define, control and review organization-approved, secure remote access methods?.',
         'Q-NET-13: Does the organization protect the confidentiality, integrity and availability of electronic messaging '
         'communications?.',
         'Q-NET-12.1: Does the organization protect external and internal wireless links from signal parameter attacks through '
         'monitoring for unauthorized wireless connections, including scanning for unauthorized wireless access points and '
         'taking appropriate action, if an unauthorized connection is discovered?.',
         'Q-NET-12: Does the organization use strong cryptography and security protocols to safeguard sensitive/regulated data '
         'during transmission over open, public networks?.',
         'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to separate untrusted networks '
         'from trusted networks?.',
         'Q-NET-04.1: Does the organization configure firewall and router configurations to deny network traffic by default '
         'and allow network traffic by exception (e.g., deny all, permit by exception)? .',
         'Q-NET-02: Does the organization implement security functions as a layered structure that minimizes interactions '
         'between layers of the design and avoiding any dependence by lower layers on the functionality or correctness of '
         'higher layers? .',
         'Q-NET-12.2: Does the organization prohibit the transmission of unprotected sensitive/regulated data by end-user '
         'messaging technologies?.',
         'Q-MDM-03: Does the organization use cryptographic mechanisms to protect the confidentiality and integrity of '
         'information on mobile devices through full-device or container encryption?.',
         'Q-MDM-01: Does the organization develop, govern & update procedures to facilitate the implementation of mobile '
         'device management controls?.',
         'Q-DCH-17: Does the organization secure ad-hoc exchanges of large digital files with internal or external parties?.',
         'Q-DCH-14: Does the organization utilize a process to assist users in making information sharing decisions to ensure '
         'data is appropriately protected?.',
         'Q-DCH-13.2: Does the organization restrict or prohibit the use of portable storage devices by users on external '
         'systems? .',
         'Q-DCH-13: Does the organization govern how external parties, systems and services are used to securely store, '
         'process and transmit data? .',
         'Q-DCH-12: Does the organization restrict removable media in accordance with data handling and acceptable usage '
         'parameters?.',
         'Q-DCH-10: Does the organization restrict the use of types of digital media on systems or system components? .',
         'Q-CFG-04.2: Does the organization allow only approved Internet browsers and email clients to run on systems?.',
         'Q-NET-08: Does the organization implement Network Intrusion Detection / Prevention Systems (NIDS/NIPS) used to '
         'detect and/or prevent intrusions into the network? .',
         'Q-END-07: Does the organization utilize Host-based Intrusion Detection / Prevention Systems (HIDS / HIPS) on '
         'sensitive systems?.',
         'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect and report unauthorized '
         'changes to system files and configurations?.',
         'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate malicious code?.',
         'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar change-detection technology, on '
         'critical assets to generate alerts for unauthorized modifications? .',
         'Q-CHG-02.1: Does the organization prohibit unauthorized changes, unless organization-approved change requests are '
         'received?.',
         'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by recurring vulnerability scanning '
         'of systems and web applications?.',
         'Q-END-06.1: Does the organization validate configurations through integrity checking of software and firmware?.',
         'Q-CFG-02: Does the organization develop, document and maintain secure baseline configurations for technology '
         'platform that are consistent with industry-accepted system hardening standards? .',
         'Q-CFG-01: Does the organization facilitate the implementation of configuration management controls?.',
         'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
         'Q-MON-16: Does the organization detect and respond to anomalous behavior that could indicate account compromise or '
         'other malicious activities?.',
         'Q-MON-06: Does the organization provide an event log report generation capability to aid in detecting and assessing '
         'anomalous activities? .',
         'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across the enterprise by a '
         'Security Incident Event Manager (SIEM) or similar automated tool, to maintain situational awareness?.',
         'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or similar automated tool, to '
         'support the centralized collection of security-related event logs?.',
         'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate incidents in accordance with '
         'established timelines and procedures?.',
         'Q-MON-01.6: Does the organization utilize Host-based Intrusion Detection / Prevention Systems (HIDS / HIPS) to '
         'actively alert on or block unwanted activities and send logs to a Security Incident Event Manager (SIEM), or similar '
         'automated tool, to maintain situational awareness?.',
         'Q-MON-01.5: Does the organization utilize Wireless Intrusion Detection / Protection Systems (WIDS / WIPS) to '
         'identify rogue wireless devices and to detect attack attempts via wireless networks? .',
         'Q-MON-01.4: Does the organization monitor, correlate and respond to alerts from physical, cybersecurity, privacy and '
         'supply chain activities to achieve integrated situational awareness? .',
         'Q-MON-01.3: Does the organization continuously monitor inbound and outbound communications traffic for unusual or '
         'unauthorized activities or conditions?.',
         'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or similar automated tool, to '
         'support near real-time analysis and incident escalation?.',
         'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS / IPS) technologies on '
         'critical systems, key network segments and network choke points?.',
         'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide monitoring controls?.',
         'Q-TPM-11: Does the organization ensure response/recovery planning and testing are conducted with critical '
         'suppliers/providers? .',
         'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the likelihood and magnitude of '
         "harm, from unauthorized access, use, disclosure, disruption, modification or destruction of the organization's "
         'systems and data?.',
         'Q-IRO-04.1: Does the organization address data breaches, or other incidents involving the unauthorized disclosure of '
         'sensitive or regulated data, according to applicable laws, regulations and contractual obligations? .',
         'Q-IRO-04: Does the organization maintain and make available a current and viable Incident Response Plan (IRP) to all '
         'stakeholders?.',
         "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, "
         'containment, eradication and recovery?.',
         'Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.',
         'Q-END-06.2: Does the organization detect and respond to unauthorized configuration changes as cybersecurity '
         'incidents?.',
         "Q-IRO-11.2: Does the organization establish a direct, cooperative relationship between the organization's incident "
         'response capability and external service providers?.',
         'Q-IRO-10.4: Does the organization provide cybersecurity and privacy incident information to the provider of the '
         'product or service and other organizations involved in the supply chain for systems or system components related to '
         'the incident?.',
         'Q-IRO-10.2: Does the organization report sensitive/regulated data incidents in a timely manner?.',
         'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy incidents? .',
         'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and business function '
         'representatives that are capable of addressing cybersecurity and privacy incident response operations?.',
         'Q-BCD-13: Does the organization protect backup and restoration hardware and software?.',
         'Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a '
         'disruption, compromise or failure? .',
         'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of the backup process, as '
         'well as the integrity and availability of the data? .',
         'Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify '
         'the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) '
         'and Recovery Point Objectives (RPOs)?.',
         'Q-BCD-06: Does the organization keep contingency plans current with business needs, technology changes and feedback '
         'from contingency plan testing activities?.',
         "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' activity every time the "
         'contingency plan is activated?.',
         "Q-BCD-04: Does the organization conduct tests and/or exercises to evaluate the contingency plan's effectiveness and "
         "the organization's readiness to execute the plan?.",
         'Q-BCD-02.3: Does the organization resume essential missions and business functions within an organization-defined '
         'time period of contingency plan activation? .',
         'Q-BCD-02.2: Does the organization plan for the continuance of essential missions and business functions with little '
         'or no loss of operational continuity and sustain that continuity until full system restoration at primary processing '
         'and/or storage sites?.',
         'Q-BCD-02.1: Does the organization plan for the resumption of all missions and business functions within Recovery '
         "Time Objectives (RTOs) of the contingency plan's activation?.",
         'Q-BCD-02: Does the organization identify and document the critical systems, applications and services that support '
         'essential missions and business functions?.',
         'Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.',
         'Q-CFG-02.2: Does the organization use automated mechanisms to govern and report on baseline configurations of the '
         'systems? .',
         'Q-CFG-02.1: Does the organization review and update baseline configurations:  -  At least annually;  -  When '
         'required due to so; or  -  As part of system component installations and upgrades?.',
         'Q-CHG-05: Does the organization ensure stakeholders are made aware of and understand the impact of proposed changes? '
         '.',
         'Q-TPM-07: Does the organization monitor for evidence of unauthorized exfiltration or disclosure of organizational '
         'information? .',
         'Q-TPM-06: Does the organization control personnel security requirements including security roles and '
         'responsibilities for third-party providers?.',
         'Q-TPM-05: Does the organization identify, regularly review and document third-party confidentiality, Non-Disclosure '
         "Agreements (NDAs) and other contracts that reflect the organization's needs to protect systems and data?.",
         'Q-TPM-04.4: Does the organization restrict the location of information processing/storage based on business '
         'requirements? .',
         'Q-TPM-03.3: Does the organization address identified weaknesses or deficiencies in the security of the supply chain '
         '.',
         'Q-TPM-03.2: Does the organization utilize security safeguards to limit harm from potential adversaries who identify '
         "and target the organization's supply chain? .",
         'Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain? .',
         'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of critical systems, '
         'components and services using a supply chain risk assessment process? .',
         'Q-BCD-07: Does the organization implement alternative or compensating controls to satisfy security functions when '
         'the primary means of implementing the security function is unavailable or compromised? .',
         'Q-RSK-09.1: Does the organization assess supply chain risks associated with systems, system components and '
         'services?.',
         'Q-DCH-03: Does the organization control and restrict access to digital and non-digital media to authorized '
         'individuals? .',
         'Q-MON-10: Does the organization retain event logs for a time period consistent with records retention requirements '
         'to provide support for after-the-fact investigations of security incidents and to meet statutory, regulatory and '
         'contractual retention requirements? .',
         'Q-TDA-06.1: Does the organization require the developer of the system, system component or service to perform a '
         'criticality analysis at organization-defined decision points in the Secure Development Life Cycle (SDLC)?.',
         'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
         'Q-TDA-18: Does the organization check the validity of information inputs? .',
         'Q-PES-12.2: Does the organization restrict access to printers and other system output devices to prevent '
         'unauthorized individuals from obtaining the output? .',
         'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized access, modification and '
         'deletion?.',
         'Q-MON-03: Does the organization configure systems to produce audit records that contain sufficient information to, '
         'at a minimum:  -  Establish what type of event occurred;  -  When (date and time) the event occurred;  -  Where the '
         'event occurred;  -  The source of the event;  -  The outcome (success or failure) of the event; and   -  The '
         'identity of any user/subject associated with the event? .',
         'Q-DCH-18: Does the organization retain media and data in accordance with applicable statutory, regulatory and '
         'contractual obligations? .',
         'Q-PES-15: Does the organization employ safeguards against Electromagnetic Pulse (EMP) damage for systems and system '
         'components?.',
         'Q-PES-13: Does the organization protect the system from information leakage due to electromagnetic signals '
         'emanations? .',
         'Q-PES-12: Does the organization locate system components within the facility to minimize potential damage from '
         'physical and environmental hazards and to minimize the opportunity for unauthorized access? .',
         'Q-PES-11: Does the organization utilize appropriate management, operational and technical controls at alternate work '
         'sites?.',
         'Q-PES-10: Does the organization isolate information processing facilities from points such as delivery and loading '
         'areas and other points to avoid unauthorized access? .',
         'Q-PES-09.1: Does the organization trigger an alarm or notification of temperature and humidity changes that be '
         'potentially harmful to personnel or equipment? .',
         'Q-PES-09: Does the organization maintain and monitor temperature and humidity levels within the facility?.',
         'Q-PES-08.2: Does the organization utilize fire suppression devices/systems that provide automatic notification of '
         'any activation to organizational personnel and emergency responders? .',
         'Q-PES-08.1: Does the organization utilize and maintain fire detection devices/systems that activate automatically '
         'and notify organizational personnel and emergency responders in the event of a fire? .',
         'Q-PES-08: Does the organization utilize and maintain fire suppression and detection devices/systems for the system '
         'that are supported by an independent energy. source? .',
         'Q-PES-07.5: Does the organization protect systems from damage resulting from water leakage by providing master '
         'shutoff valves that are accessible, working properly and known to key personnel? .',
         'Q-PES-07.4: Does the organization utilize and maintain automatic emergency lighting that activates in the event of a '
         'power outage or disruption and that covers emergency exits and evacuation routes within the facility? .',
         'Q-PES-07.3: Does the organization protect supply long-term alternate power, capable of maintaining '
         'minimally-required operational capability, in the event of an extended loss of the primary power source?.',
         'Q-PES-07.2: Does the organization shut off power in emergency situations by:  -  Placing emergency shutoff switches '
         'or devices in close proximity to systems or system components to facilitate safe and easy access for personnel; and  '
         '-  Protecting emergency power shutoff capability from unauthorized activation?.',
         'Q-PES-07.1: Does the organization utilize automatic voltage controls for critical system components? .',
         'Q-PES-07: Does the organization protect power equipment and power cabling for the system from damage and '
         'destruction? .',
         'Q-BCD-12.2: Does the organization implement real-time or near-real-time failover capability to maintain availability '
         'of critical systems, applications and/or services?.',
         'Q-BCD-12.1: Does the organization utilize specialized backup mechanisms that will allow transaction recovery for '
         'transaction-based applications and services in accordance with Recovery Point Objectives (RPOs)?.',
         'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized disclosure and/or '
         'modification of backup information/.',
         'Q-BCD-11.3: Does the organization reimage assets from configuration-controlled and integrity-protected images that '
         'represent a secure, operational state?.',
         'Q-BCD-11.2: Does the organization store backup copies of critical software and other security-related information in '
         'a separate facility or in a fire-rated container that is not collocated with the system being backed up?.',
         'Q-BCD-10.1: Does the organization formalize primary and alternate telecommunications service agreements contain '
         'priority-of-service provisions that support availability requirements, including Recovery Time Objectives (RTOs)?.',
         'Q-BCD-10: Does the organization reduce the likelihood of a single point of failure with primary telecommunications '
         'services?.',
         'Q-BCD-09.3: Does the organization address priority-of-service provisions in alternate processing and storage sites '
         'that support availability requirements, including Recovery Time Objectives (RTOs)? .',
         'Q-BCD-09.2: Does the organization identify potential accessibility problems to the alternate processing site and '
         'possible mitigation actions, in the event of an area-wide disruption or disaster?.',
         'Q-BCD-09.1: Does the organization separate the alternate processing site from the primary processing site to reduce '
         'susceptibility to similar threats?.',
         'Q-BCD-09: Does the organization establish an alternate processing site that provides security measures equivalent to '
         'that of the primary site?.',
         'Q-BCD-08.2: Does the organization identify and mitigate potential accessibility problems to the alternate storage '
         'site in the event of an area-wide disruption or disaster?.',
         'Q-BCD-08.1: Does the organization separate the alternate storage site from the primary storage site to reduce '
         'susceptibility to similar threats?.',
         'Q-BCD-08: Does the organization establish an alternate storage site that includes both the assets and necessary '
         'agreements to permit the storage and recovery of system backup information? .',
         'Q-BCD-03.1: Does the organization incorporate simulated events into contingency training to facilitate effective '
         'response by personnel in crisis situations?.',
         'Q-PRI-02: Does the organization:  -  Make privacy notice(s) available to individuals upon first interacting with an '
         'organization and subsequently as necessary?  -  Ensure that privacy notices are clear and easy-to-understand, '
         'expressing information about Personal Data (PD) processing in plain language?.',
         'Q-PRI-01.3: Does the organization:   -  Ensure that the public has access to information about organizational '
         'privacy activities and can communicate with its Chief Privacy Officer (CPO) or similar role;  -  Ensure that '
         'organizational privacy practices are publicly available through organizational websites or otherwise; and  -  '
         'Utilize publicly facing email addresses and/or phone lines to enable the public to provide feedback and/or direct '
         'questions to privacy offices regarding privacy practices?.',
         'Q-PRI-01.2: Does the organization provide additional formal notice to individuals from whom the information is being '
         'collected that includes:  -  Notice of the authority of organizations to collect Personal Data (PD);   -  Whether '
         'providing Personal Data (PD) is mandatory or optional;   -  The principal purpose or purposes for which the Personal '
         'Data (PD) is to be used;   -  The intended disclosures or routine uses of the information; and   -  The consequences '
         'of not providing all or some portion of the information requested?.',
         'Q-PRI-03.2: Does the organization present authorizations to process Personal Data (PD) in conjunction with the data '
         'action, when: -  The original circumstances under which an individual gave consent have changed; or -  A significant '
         'amount of time has passed since an individual gave consent?.',
         'Q-PRI-03: Does the organization authorize the processing of their Personal Data (PD) prior to its collection that:  '
         '-  Uses plain language and provide examples to illustrate the potential privacy risks of the authorization; and  -  '
         'Provides a means for users to decline the authorization?.',
         'Q-PRI-05.4: Does the organization restrict the use of Personal Data (PD) to only the authorized purpose(s) '
         'consistent with applicable laws, regulations and in privacy notices? .',
         'Q-PRI-05.1: Does the organization address the use of Personal Data (PD) for internal testing, training and research '
         'that:  -  Takes measures to limit or minimize the amount of PD used for internal testing, training and research '
         'purposes; and  -  Authorizes the use of PD when such information is required for internal testing, training and '
         'research?.',
         'Q-DCH-09.3: Does the organization facilitate the sanitization of Personal Data (PD)?.',
         'Q-PRI-06.1: Does the organization establish and implement a process for:  -  Individuals to have inaccurate Personal '
         'Data (PD) maintained by the organization corrected or amended; and  -  Disseminating corrections or amendments of PD '
         'to other authorized users of the PI?.',
         'Q-DCH-22.1: Does the organization utilize technical controls to correct Personal Data (PD) that is inaccurate or '
         'outdated, incorrectly determined regarding impact, or incorrectly de-identified?.',
         'Q-PRI-12: Does the organization develop processes to identify and record the method under which Personal Data (PD) '
         'is updated and the frequency that such updates occur?.',
         'Q-PRI-07: Does the organization discloses Personal Data (PD) to third-parties only for the purposes identified in '
         'the privacy notice and with the implicit or explicit consent of the individual? .',
         'Q-PRI-14.1: Does the organization develop and maintain an accounting of disclosures of Personal Data (PD) held by '
         'the organization and make the accounting of disclosures available to the person named in the record, upon request?.',
         'Q-IRO-12: Does the organization respond to sensitive information spills?.',
         'Q-PRI-07.1: Does the organization includes privacy requirements in contracts and other acquisition-related documents '
         'that establish privacy roles and responsibilities for contractors and service providers? .',
         'Q-PRI-08: Does the organization implement a process for ensuring that organizational plans for conducting '
         'cybersecurity and privacy testing, training and monitoring activities associated with organizational systems are '
         'developed and performed? .',
         'Q-PRI-10: Does the organization issue guidelines ensuring and maximizing the quality, utility, objectivity, '
         'integrity, impact determination and de-identification of Personal Data (PD) across the information lifecycle?.',
         'Q-PRI-06.4: Does the organization implement a process for receiving and responding to complaints, concerns or '
         'questions from individuals about the organizational privacy practices?.']

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'CE: control environment',
          'conformity_questions': ['Q-HRS-07.1: Does the organization conduct employee misconduct investigations when there is '
                                   'reasonable assurance that a policy has been violated? .',
                                   'Q-HRS-05.1: Does the organization define acceptable and unacceptable rules of behavior for '
                                   'the use of technologies, including consequences for unacceptable behavior?.',
                                   'Q-HRS-05: Does the organization require all employees and contractors to apply '
                                   'cybersecurity and privacy principles in their daily work?.',
                                   'Q-HRS-01: Does the organization facilitate the implementation of personnel security '
                                   'controls?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?."],
          'objective_title': 'CC1.1.1: Sets the Tone at the Top',
          'requirement_description': 'The board of directors and management, at all levels, demonstrate through their '
                                     'directives, actions, and behavior the importance of integrity and ethical values to '
                                     'support the functioning of the system of internal control.',
          'subchapter': 'CC1.1: COSO Principle 1: The entity demonstrates a commitment to integrity and ethical values.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.1.2: Establishes Standards of Conduct',
          'requirement_description': 'The expectations of the board of directors and senior management concerning integrity '
                                     "and ethical values are defined in the entity's standards of conduct and understood at "
                                     'all levels of the entity and by outsourced service providers and business partners.',
          'subchapter': 'CC1.1: COSO Principle 1: The entity demonstrates a commitment to integrity and ethical values.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.1.3: Evaluates Adherence to Standards of Conduct',
          'requirement_description': 'Processes are in place to evaluate the performance of individuals and teams against the '
                                     "entity's expected standards of conduct.",
          'subchapter': 'CC1.1: COSO Principle 1: The entity demonstrates a commitment to integrity and ethical values.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.1.4: Addresses Deviations in a Timely Manner',
          'requirement_description': "Deviations from the entity's expected standards of conduct are identified and remedied "
                                     'in a timely and consistent manner.',
          'subchapter': 'CC1.1: COSO Principle 1: The entity demonstrates a commitment to integrity and ethical values.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.1.5: Considers Contractors and Vendor Employees in Demonstrating Its Commitment',
          'requirement_description': 'Management and the board of directors consider the use of contractors and vendor '
                                     'employees in its processes for establishing standards of conduct, evaluating adherence '
                                     'to those standards, and addressing deviations in a timely manner. ',
          'subchapter': 'CC1.1: COSO Principle 1: The entity demonstrates a commitment to integrity and ethical values.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': ['Q-HRS-03.2: Does the organization ensure that all security-related positions are staffed '
                                   'by qualified individuals who have the necessary skill set? .',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-HRS-02: Does the organization manage personnel security risk by assigning a risk '
                                   'designation to all positions and establishing screening criteria for individuals filling '
                                   'those positions?.',
                                   'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) '
                                   'to assist senior management in performance monitoring and trend analysis of the '
                                   'cybersecurity and privacy program?.',
                                   'Q-GOV-05.1: Does the organization develop, report and monitor Key Performance Indicators '
                                   '(KPIs) to assist organizational management in performance monitoring and trend analysis of '
                                   'the cybersecurity and privacy program?.',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.',
                                   'Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and '
                                   'privacy controls?.'],
          'objective_title': 'CC1.2.1: Establishes Oversight Responsibilities',
          'requirement_description': 'The board of directors identifies and accepts its oversight responsibilities in relation '
                                     'to established requirements and expectations.',
          'subchapter': 'CC1.2: COSO Principle 2: The board of directors demonstrates independence from management and '
                        'exercises oversight of the development and performance of internal control.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.2.2: Applies Relevant Expertise',
          'requirement_description': 'The board of directors defines, maintains, and periodically evaluates the skills and '
                                     'expertise needed among its members to enable them to ask probing questions of senior '
                                     'management and take commensurate action.',
          'subchapter': 'CC1.2: COSO Principle 2: The board of directors demonstrates independence from management and '
                        'exercises oversight of the development and performance of internal control.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.2.3: Operates Independently',
          'requirement_description': 'The board of directors has sufficient members who are independent from management and '
                                     'objective in evaluations and decision making.',
          'subchapter': 'CC1.2: COSO Principle 2: The board of directors demonstrates independence from management and '
                        'exercises oversight of the development and performance of internal control.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.2.4: Supplements Board Expertise',
          'requirement_description': 'The board of directors supplements its expertise relevant to security, availability, '
                                     'processing integrity, confidentiality, and privacy, as needed, through the use of a '
                                     'subcommittee or consultants.',
          'subchapter': 'CC1.2: COSO Principle 2: The board of directors demonstrates independence from management and '
                        'exercises oversight of the development and performance of internal control.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': ['Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.',
                                   'Q-HRS-03.2: Does the organization ensure that all security-related positions are staffed '
                                   'by qualified individuals who have the necessary skill set? .',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': 'CC1.3.1: Considers All Structures of the Entity',
          'requirement_description': 'Management and the board of directors consider the multiple structures used (including '
                                     'operating units, legal entities, geographic distribution, and outsourced service '
                                     'providers) to support the achievement of objectives.',
          'subchapter': 'CC1.3: COSO Principle 3: Management establishes, with board oversight, structures, reporting lines, '
                        'and appropriate authorities and responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.3.2: Establishes Reporting Lines',
          'requirement_description': "Management designs and evaluates lines of reporting for each entity'structure to enable "
                                     'execution of authorities and responsibilities and flow of information to manage the '
                                     'activities of the entity.',
          'subchapter': 'CC1.3: COSO Principle 3: Management establishes, with board oversight, structures, reporting lines, '
                        'and appropriate authorities and responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.3.3: Defines, Assigns, and Limits Authorities and Responsibilities',
          'requirement_description': 'Management and the board of directors delegate authority, define responsibilities, and '
                                     'use appropriate processes and technology to assign responsibility and segregate duties '
                                     'as necessary at the various levels of the organization.',
          'subchapter': 'CC1.3: COSO Principle 3: Management establishes, with board oversight, structures, reporting lines, '
                        'and appropriate authorities and responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.3.4: Addresses Specific Requirements When Defining Authorities and Responsibilities',
          'requirement_description': 'Management and the board of directors consider requirements relevant to security, '
                                     'availability, processing integrity, confidentiality, and privacy when defining '
                                     'authorities and responsibilities. ',
          'subchapter': 'CC1.3: COSO Principle 3: Management establishes, with board oversight, structures, reporting lines, '
                        'and appropriate authorities and responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.3.5: Considers Interactions With External Parties When Establishing Structures, Reporting '
                             'Lines, Authorities, and Responsibilities',
          'requirement_description': 'Management and the board of directors consider the need for the entity to interact with '
                                     'and monitor the activities of external parties when establishing structures, reporting '
                                     'lines, authorities, and responsibilities. ',
          'subchapter': 'CC1.3: COSO Principle 3: Management establishes, with board oversight, structures, reporting lines, '
                        'and appropriate authorities and responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.3.6: Establishes Structures, Reporting Lines, and Authorities to Support Compliance With '
                             'Legal and Contractual Privacy Requirements',
          'requirement_description': 'When establishing structures, reporting lines, and authorities, management considers '
                                     'legal and contractual privacy requirements and objectives.',
          'subchapter': 'CC1.3: COSO Principle 3: Management establishes, with board oversight, structures, reporting lines, '
                        'and appropriate authorities and responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': ['Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .',
                                   'Q-PRM-03: Does the organization identify and allocate resources for management, '
                                   'operational, technical and privacy requirements within business process planning for '
                                   'projects / initiatives?.',
                                   'Q-PRM-02: Does the organization address all capital planning and investment requests, '
                                   'including the resources needed to implement the security & privacy programs and documents '
                                   'all exceptions to this requirement? .',
                                   'Q-HRS-04.2: Does the organization verify that individuals accessing a system processing, '
                                   'storing, or transmitting sensitive information are formally indoctrinated for all the '
                                   'relevant types of information to which they have access on the system?.',
                                   'Q-HRS-04.1: Does the organization ensure that individuals accessing a system that stores, '
                                   'transmits or processes information requiring special protection satisfy '
                                   'organization-defined personnel screening criteria?.',
                                   'Q-HRS-04: Does the organization manage personnel security risk by screening individuals '
                                   'prior to authorizing access?.',
                                   'Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-02.1: Does the organization ensure that every user accessing a system that '
                                   'processes, stores, or transmits sensitive information is cleared and regularly trained to '
                                   'handle the information in question?.',
                                   'Q-HRS-01: Does the organization facilitate the implementation of personnel security '
                                   'controls?.'],
          'objective_title': 'CC1.4.1: Establishes Policies and Practices',
          'requirement_description': 'Policies and practices reflect expectations of competence necessary to support the '
                                     'achievement of objectives.',
          'subchapter': 'CC1.4: COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain '
                        'competent individuals in alignment with objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.4.2: Evaluates Competence and Addresses Shortcomings',
          'requirement_description': 'The board of directors and management evaluate competence across the entity and in '
                                     'outsourced service providers in relation to established policies and practices and act '
                                     'as necessary to address shortcomings.',
          'subchapter': 'CC1.4: COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain '
                        'competent individuals in alignment with objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.4.3: Attracts, Develops, and Retains Individuals',
          'requirement_description': 'The entity provides the mentoring and training needed to attract, develop, and retain '
                                     'sufficient and competent personnel and outsourced service providers to support the '
                                     'achievement of objectives.',
          'subchapter': 'CC1.4: COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain '
                        'competent individuals in alignment with objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.4.4: Plans and Prepares for Succession',
          'requirement_description': 'Senior management and the board of directors develop contingency plans for assignments '
                                     'of responsibility important for internal control.',
          'subchapter': 'CC1.4: COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain '
                        'competent individuals in alignment with objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.4.5: Considers the Background of Individuals',
          'requirement_description': 'The entity considers the background of potential and existing personnel, contractors, '
                                     'and vendor employees when determining whether to employ and retain the individuals. ',
          'subchapter': 'CC1.4: COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain '
                        'competent individuals in alignment with objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.4.6: Considers the Technical Competency of Individuals',
          'requirement_description': 'The entity considers the technical competency of potential and existing personnel, '
                                     'contractors, and vendor employees when determining whether to employ and retain the '
                                     'individuals. ',
          'subchapter': 'CC1.4: COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain '
                        'competent individuals in alignment with objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.4.7: Provides Training to Maintain Technical Competencies',
          'requirement_description': ' The entity provides training programs, including continuing education and training, to '
                                     'ensure skill sets and technical competency of existing personnel, contractors, and '
                                     'vendor employees are developed and maintained.',
          'subchapter': 'CC1.4: COSO Principle 4: The entity demonstrates a commitment to attract, develop, and retain '
                        'competent individuals in alignment with objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': ['Q-HRS-09.3: Does the organization govern former employee behavior by notifying terminated '
                                   'individuals of applicable, legally binding post-employment requirements for the protection '
                                   'of organizational information?.',
                                   "Q-HRS-09.2: Does the organization expedite the process of removing 'high risk' "
                                   "individual's access to systems and applications upon termination, as determined by "
                                   'management?.',
                                   'Q-HRS-09.1: Does the organization retrieve organization-owned assets upon termination of '
                                   "an individual's employment?.",
                                   'Q-HRS-09: Does the organization govern the termination of individual employment?.',
                                   'Q-HRS-08: Does the organization adjust logical and physical access authorizations to '
                                   'systems and facilities upon personnel reassignment or transfer, in a timely manner?.',
                                   'Q-HRS-07.1: Does the organization conduct employee misconduct investigations when there is '
                                   'reasonable assurance that a policy has been violated? .',
                                   'Q-HRS-07: Does the organization sanction personnel failing to comply with established '
                                   'security policies, standards and procedures? .',
                                   'Q-HRS-06.1: Does the organization require Non-Disclosure Agreements (NDAs) or similar '
                                   'confidentiality agreements that reflect the needs to protect data and operational details, '
                                   'for both employees and third-parties?.',
                                   'Q-HRS-06: Does the organization require internal and third-party users to sign appropriate '
                                   'access agreements prior to being granted access? .',
                                   'Q-HRS-03.2: Does the organization ensure that all security-related positions are staffed '
                                   'by qualified individuals who have the necessary skill set? .',
                                   'Q-HRS-01: Does the organization facilitate the implementation of personnel security '
                                   'controls?.',
                                   'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) '
                                   'to assist senior management in performance monitoring and trend analysis of the '
                                   'cybersecurity and privacy program?.',
                                   'Q-GOV-05.1: Does the organization develop, report and monitor Key Performance Indicators '
                                   '(KPIs) to assist organizational management in performance monitoring and trend analysis of '
                                   'the cybersecurity and privacy program?.',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.'],
          'objective_title': 'CC1.5.1: Enforces Accountability Through Structures, Authorities, and Responsibilities',
          'requirement_description': 'Management and the board of directors establish the mechanisms to communicate and hold '
                                     'individuals accountable for performance of internal control responsibilities across the '
                                     'entity and implement corrective action as necessary.',
          'subchapter': 'CC1.5: COSO Principle 5: The entity holds individuals accountable for their internal control '
                        'responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.5.2: Establishes Performance Measures, Incentives, and Rewards',
          'requirement_description': 'Management and the board of directors establish performance measures, incentives, and '
                                     'other rewards appropriate for responsibilities at all levels of the entity, reflecting '
                                     'appropriate dimensions of performance and expected standards of conduct, and considering '
                                     'the achievement of both short-term and longer-term objectives.',
          'subchapter': 'CC1.5: COSO Principle 5: The entity holds individuals accountable for their internal control '
                        'responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.5.3: Evaluates Performance Measures, Incentives, and Rewards for Ongoing Relevance',
          'requirement_description': 'Management and the board of directors align incentives and rewards with the fulfillment '
                                     'of internal control responsibilities in the achievement of objectives.',
          'subchapter': 'CC1.5: COSO Principle 5: The entity holds individuals accountable for their internal control '
                        'responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.5.4: Considers Excessive Pressures',
          'requirement_description': 'Management and the board of directors evaluate and adjust pressures associated with the '
                                     'achievement of objectives as they assign responsibilities, develop performance measures, '
                                     'and evaluate performance.',
          'subchapter': 'CC1.5: COSO Principle 5: The entity holds individuals accountable for their internal control '
                        'responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.5.5: Evaluates Performance and Rewards or Disciplines Individuals',
          'requirement_description': 'Management and the board of directors evaluate performance of internal control '
                                     'responsibilities, including adherence to standards of conduct and expected levels of '
                                     'competence, and provide rewards or exercise disciplinary action, as appropriate.',
          'subchapter': 'CC1.5: COSO Principle 5: The entity holds individuals accountable for their internal control '
                        'responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CE: control environment',
          'conformity_questions': [],
          'objective_title': 'CC1.5.6: Takes Disciplinary Actions',
          'requirement_description': 'A sanctions process is defined, and applied as needed, when an employee violates the '
                                     "entity's privacy policies or when an employee's negligent behavior causes a privacy "
                                     'incident.',
          'subchapter': 'CC1.5: COSO Principle 5: The entity holds individuals accountable for their internal control '
                        'responsibilities in the pursuit of objectives.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': ['Q-OPS-03: Does the organization define supporting business processes and implement '
                                   'appropriate governance and service management to ensure appropriate planning, delivery and '
                                   "support of the organization's technology capabilities supporting business functions, "
                                   'workforce, and/or customers based on industry-recognized standards? .',
                                   'Q-DCH-22: Does the organization check for the accuracy, relevance, timeliness, impact, '
                                   'completeness and de-identification of information across the information lifecycle?.',
                                   'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with '
                                   'applicable statutory, regulatory and contractual requirements? .',
                                   'Q-DCH-01.1: Does the organization ensure data stewardship is assigned, documented and '
                                   'communicated? .',
                                   'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.',
                                   'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain '
                                   "sufficient detail to assess the security of the network's architecture;  -  Reflect the "
                                   'current architecture of the network environment; and  -  Document all sensitive/regulated '
                                   'data flows?.'],
          'objective_title': 'CC2.1.1: Identifies Information Requirements',
          'requirement_description': 'A process is in place to identify the information required and expected to support the '
                                     'functioning of the other components of internal control and the achievement of the '
                                     "entity's objectives.",
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.2: Captures Internal and External Sources of Data',
          'requirement_description': 'Information systems capture internal and external sources of data.',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.3: Processes Relevant Data Into Information',
          'requirement_description': 'Information systems process and transform relevant data into information.',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.4: Maintains Quality Throughout Processing',
          'requirement_description': 'Information systems produce information that is timely, current, accurate, complete, '
                                     'accessible, protected, verifiable, and retained. Information is reviewed to assess its '
                                     'relevance in supporting the internal control components. ',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.5: Documents Data Flow',
          'requirement_description': 'The entity documents and uses internal and external information and data flows to '
                                     'support the design and operation of controls.',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.6: Manages Assets',
          'requirement_description': 'The entity identifies, documents, and maintains records of system components such as '
                                     'infrastructure, software, and other information assets. Information assets include '
                                     'physical endpoint devices and systems, virtual systems, data and data flows, external '
                                     'information systems, and organizational roles.',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.7: Classifies Information',
          'requirement_description': 'The entity classifies information by its relevant characteristics (for example, '
                                     'personally identifiable information, confidential customer information, and intellectual '
                                     'property) to support identification of threats to the information and the design and '
                                     'operation of controls.',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.8: Uses Information That Is Complete and Accurate',
          'requirement_description': 'The entity uses information and reports that are complete, accurate, current, and valid '
                                     'in the operation of controls.',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.1.9: Manages the Location of Assets',
          'requirement_description': 'The entity identifies, documents, and maintains records of physical location and custody '
                                     'of information assets, particularly for those stored outside the physical security '
                                     'control of the entity (for example, software and data stored on vendor devices or '
                                     'employee mobile phones under a bring-your-own-device policy).',
          'subchapter': 'CC2.1: COSO Principle 13: The entity obtains or generates and uses relevant, quality information to '
                        'support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-SEA-02.1: Does the organization standardize technology and process terminology to reduce '
                                   'confusion amongst groups and departments? .',
                                   'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.',
                                   'Q-PRM-05: Does the organization identify critical system components and functions by '
                                   'performing a criticality analysis for critical systems, system components or services at '
                                   'pre-defined decision points in the Secure Development Life Cycle (SDLC)? .',
                                   'Q-PRM-01: Does the organization facilitate the implementation of cybersecurity and '
                                   'privacy-related resource planning controls?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?.",
                                   'Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, '
                                   'regulatory and contractual controls?.',
                                   'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) '
                                   'to assist senior management in performance monitoring and trend analysis of the '
                                   'cybersecurity and privacy program?.',
                                   'Q-GOV-05.1: Does the organization develop, report and monitor Key Performance Indicators '
                                   '(KPIs) to assist organizational management in performance monitoring and trend analysis of '
                                   'the cybersecurity and privacy program?.',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.'],
          'objective_title': 'CC2.2.1: Communicates Internal Control Information',
          'requirement_description': 'A process is in place to communicate required information to enable all personnel to '
                                     'understand and carry out their internal control responsibilities.',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.2: Communicates With the Board of Directors',
          'requirement_description': 'Communication exists between management and the board of directors so that both have '
                                     "information needed to fulfill their roles with respect to the entity's objectives.",
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.3: Provides Separate Communication Lines',
          'requirement_description': 'Separate communication channels, such as whistle-blower hotlines, are in place and serve '
                                     'as fail-safe mechanisms to enable anonymous or confidential communication when normal '
                                     'channels are inoperative or ineffective.',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.4: Selects Relevant Method of Communication',
          'requirement_description': 'The method of communication considers the timing, audience, and nature of the '
                                     'information.',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.5: Communicates Responsibilities',
          'requirement_description': 'Entity personnel with responsibility for designing, developing, implementing, operating, '
                                     'maintaining, or monitoring system controls receive communications about their '
                                     'responsibilities, including changes in their responsibilities, and have the information '
                                     'necessary to carry out those responsibilities. ',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.6: Communicates Information on Reporting Failures, Incidents, Concerns, and Other Matters',
          'requirement_description': 'Entity personnel are provided with information on how to report systems failures, '
                                     'incidents, concerns, and other complaints.',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.7: Communicates Objectives and Changes to Objectives',
          'requirement_description': 'The entity communicates its objectives and changes to those objectives to personnel in a '
                                     'timely manner. ',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.8: Communicates Information to Improve Security Knowledge and Awareness',
          'requirement_description': 'The entity communicates information to improve security knowledge and awareness and to '
                                     'model appropriate security behaviors to personnel through a security awareness training '
                                     'program. ',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.9: Communicates Information About System Operation and Boundaries',
          'requirement_description': 'The entity prepares and communicates information about the design and operation of the '
                                     'system and its boundaries to authorized personnel to enable them to understand their '
                                     'role in the system and the results of system operation.',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.10: Communicates System Objectives',
          'requirement_description': 'The entity communicates its objectives to personnel to enable them to carry out their '
                                     'responsibilities. ',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.11: Communicates System Changes',
          'requirement_description': "System changes that affect responsibilities or the achievement of the entity's "
                                     'objectives are communicated in a timely manner. ',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.12: Communicates Information to Improve Privacy Knowledge and Awareness',
          'requirement_description': 'The entity communicates information to improve privacy knowledge and awareness and to '
                                     'model appropriate behaviors to personnel through a privacy awareness training program.',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.2.13: Communicates Incident Reporting Methods',
          'requirement_description': 'The entity has communicated to employees and others within the entity the process used '
                                     'to report a suspected privacy incident.',
          'subchapter': 'CC2.2: COSO Principle 14: The entity internally communicates information, including objectives and '
                        'responsibilities for internal control, necessary to support the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': ['Q-PRI-14: Does the organization develop, disseminate and update reports to internal senior '
                                   'management, as well as external oversight bodies, as appropriate, to demonstrate '
                                   'accountability with specific statutory and regulatory privacy program mandates?.',
                                   'Q-IRO-14: Does the organization maintain incident response contacts with applicable '
                                   'regulatory and law enforcement agencies? .',
                                   'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?.",
                                   'Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, '
                                   'regulatory and contractual controls?.',
                                   'Q-GOV-06: Does the organization identify and document appropriate contacts within relevant '
                                   'law enforcement and regulatory bodies?.'],
          'objective_title': 'CC2.3.1: Communicates to External Parties',
          'requirement_description': 'Processes are in place to communicate relevant and timely information to external '
                                     'parties, including shareholders, partners, owners, regulators, customers, financial '
                                     'analysts, and other external parties.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.2: Enables Inbound Communications',
          'requirement_description': 'Open communication channels allow input from customers, consumers, suppliers, external '
                                     'auditors, regulators, financial analysts, and others, providing management and the board '
                                     'of directors with relevant information.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.3: Communicates With the Board of Directors',
          'requirement_description': 'Relevant information resulting from assessments conducted by external parties is '
                                     'communicated to the board of directors.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.4: Provides Separate Communication Lines',
          'requirement_description': 'Separate communication channels, such as whistle-blower hotlines, are in place and serve '
                                     'as fail-safe mechanisms to enable anonymous or confidential communication when normal '
                                     'channels are inoperative or ineffective.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.5: Selects Relevant Method of Communication',
          'requirement_description': 'The method of communication considers the timing, audience, and nature of the '
                                     'communication and legal, regulatory, and fiduciary requirements and expectations. ',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.6: Communicates Objectives Related to Confidentiality and Changes to Those Objectives',
          'requirement_description': 'The entity communicates, to external users, vendors, business partners, and others whose '
                                     "products or services, or both, are part of the system, the entity's objectives related "
                                     'to confidentiality and the protection of confidential information, as well as changes to '
                                     'those objectives.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.7: Communicates Objectives Related to Privacy and Changes to Those Objectives',
          'requirement_description': 'The entity communicates, to external users, vendors, business partners, and others whose '
                                     "products or services, or both, are part of the system, the entity's objectives related "
                                     'to privacy and the protection of personal information, as well as changes to those '
                                     'objectives.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.8: Communicates Information About System Operation and Boundaries',
          'requirement_description': 'The entity prepares and communicates information about the design and operation of the '
                                     'system and its boundaries to authorized external users to permit users to understand '
                                     'their role in the system and the results of system operation. ',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.9: Communicates System Objectives',
          'requirement_description': 'The entity communicates its system objectives to appropriate external users. ',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.10: Communicates System Responsibilities',
          'requirement_description': 'External users with responsibility for designing, developing, implementing, operating, '
                                     'maintaining, and monitoring system controls receive information about such '
                                     'responsibilities and have the information necessary to carry out such responsibilities.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.11: Communicates Information on Reporting System Failures, Incidents, Concerns, and Other '
                             'Matters',
          'requirement_description': 'External users are provided with information on how to report systems failures, '
                                     'incidents, concerns, and other complaints to appropriate entity personnel. ',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'CI: communication and information',
          'conformity_questions': [],
          'objective_title': 'CC2.3.12: Communicates Incident Reporting Methods',
          'requirement_description': 'The entity communicates to user entities, third parties, data subjects, and others the '
                                     'process used to report a suspected privacy incident.',
          'subchapter': 'CC2.3: COSO Principle 15: The entity communicates with external parties regarding matters affecting '
                        'the functioning of internal control.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': ['Q-SEA-02: Does the organization develop an enterprise architecture, aligned with '
                                   'industry-recognized leading practices, with consideration for cybersecurity and privacy '
                                   'principles that addresses risk to organizational operations, assets, individuals, other '
                                   'organizations? .',
                                   'Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.',
                                   'Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.',
                                   'Q-PRM-04: Does the organization assess cybersecurity and privacy controls in system '
                                   'project development to determine the extent to which the controls are implemented '
                                   'correctly, operating as intended and producing the desired outcome with respect to meeting '
                                   'the requirements?.',
                                   'Q-PRM-01: Does the organization facilitate the implementation of cybersecurity and '
                                   'privacy-related resource planning controls?.'],
          'objective_title': "CC3.1.1: Reflects Management's Choices",
          'requirement_description': "Operations objectives reflect management's choices about structure, industry "
                                     'considerations, and performance of the entity.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.2: Considers Tolerances for Risk',
          'requirement_description': 'Management considers the acceptable levels of variation relative to the achievement of '
                                     'operations objectives.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.3: Includes Operations and Financial Performance Goals',
          'requirement_description': 'The organization reflects the desired level of operations and financial performance for '
                                     'the entity within operations objectives.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.4: Forms a Basis for Committing of Resources',
          'requirement_description': 'Management uses operations objectives as a basis for allocating resources needed to '
                                     'attain desired operations and financial performance.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.5: Complies With Applicable Accounting Standards',
          'requirement_description': 'Financial reporting objectives are consistent with accounting principles suitable and '
                                     'available for that entity. The accounting principles selected are appropriate in the '
                                     'circumstances.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.6: Considers Materiality',
          'requirement_description': 'Management considers materiality in financial statement presentation.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.7: Reflects Entity Activities',
          'requirement_description': 'External reporting reflects the underlying transactions and events to show qualitative '
                                     'characteristics and assertions.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.8: Complies With Externally Established Frameworks',
          'requirement_description': 'Management establishes objectives consistent with laws and regulations or standards and '
                                     'frameworks of recognized external organizations.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.9: Considers the Required Level of Precision',
          'requirement_description': 'Management reflects the required level of precision and accuracy suitable for user needs '
                                     'and based on criteria established by third parties in nonfinancial reporting.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.10: Reflects Entity Activities',
          'requirement_description': 'External reporting reflects the underlying transactions and events within a range of '
                                     'acceptable limits.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': "CC3.1.11: Reflects Management's Choices",
          'requirement_description': 'Internal reporting provides management with accurate and complete information regarding '
                                     "management's choices and information needed in managing the entity.",
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.12: Considers the Required Level of Precision',
          'requirement_description': 'Management reflects the required level of precision and accuracy suitable for user needs '
                                     'in nonfinancial reporting objectives and materiality within financial reporting '
                                     'objectives.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.13: Reflects Entity Activities',
          'requirement_description': 'Internal reporting reflects the underlying transactions and events within a range of '
                                     'acceptable limits.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.14: Reflects External Laws and Regulations',
          'requirement_description': 'Laws and regulations establish minimum standards of conduct, which the entity integrates '
                                     'into compliance objectives.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.15: Considers Tolerances for Risk',
          'requirement_description': 'Management considers the acceptable levels of variation relative to the achievement of '
                                     'operations objectives.',
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.1.16: Establishes Sub Objectives for Risk Assessment',
          'requirement_description': 'Management identifies sub-objectives for use in risk assessment related to security, '
                                     'availability, processing integrity, confidentiality, and privacy to support the '
                                     "achievement of the entity's objectives.",
          'subchapter': "CC3.1: COSO Principle 6: The entity'specifies objectives with sufficient clarity to enable the "
                        'identification and assessment of risks relating to objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': ['Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.',
                                   'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.'],
          'objective_title': 'CC3.2.1: Includes Entity, Subsidiary, Division, Operating Unit, and Functional Levels',
          'requirement_description': 'The entity identifies and assesses risk at the entity, subsidiary, division, operating '
                                     'unit, and functional levels relevant to the achievement of objectives.',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.2: Analyzes Internal and External Factors',
          'requirement_description': 'Risk identification considers both internal and external factors and their impact on the '
                                     'achievement of objectives.',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.3: Involves Appropriate Levels of Management',
          'requirement_description': 'The entity puts into place effective risk assessment mechanisms that involve appropriate '
                                     'levels of management.',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.4: Estimates Significance of Risks Identified',
          'requirement_description': 'Identified risks are analyzed through a process that includes estimating the potential '
                                     'significance of the risk. ',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.5: Determines How to Respond to Risks',
          'requirement_description': 'Risk assessment includes considering how the risk should be managed and whether to '
                                     'accept, avoid, reduce, or share the risk.',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.6: Identifies Threats to Objectives',
          'requirement_description': 'The entity identifies threats to the achievement of its objectives from intentional '
                                     '(including malicious) and unintentional acts and environmental events.',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.7: Analyzes Threats and Vulnerabilities From Vendors, Business Partners, and Other Parties',
          'requirement_description': "The entity's risk assessment process includes the analysis of potential threats and "
                                     'vulnerabilities arising from vendors providing goods and services, as well as threats '
                                     'and vulnerabilities arising from business partners, customers, and other third parties '
                                     "with access to the entity's information systems. ",
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.8: Assesses the Significance of the Risks',
          'requirement_description': 'The entity assesses the significance of the identified risks, including (1) determining '
                                     'the criticality of system components, including information assets, in achieving the '
                                     'objectives; (2) assessing the susceptibility of the identified vulnerabilities to the '
                                     'identified threats; (3) assessing the likelihood of the identified risks;(4) assessing '
                                     'the magnitude of the effect of potential risks to the achievement of the objectives; (5) '
                                     'considering the potential effects of unidentified threats and vulnerabilities on the '
                                     'assessed risks; (6) developing risk mitigation strategies to address the assessed risks; '
                                     'and (7) evaluating the appropriateness of residual risk (including whether to accept, '
                                     'reduce, or share such risks).',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.2.9: Identifies Vulnerability of System Components',
          'requirement_description': 'The entity identifies the vulnerabilities of system components, including system '
                                     'processes, infrastructure, software, and other information assets.',
          'subchapter': 'CC3.2: COSO Principle 7: The entity identifies risks to the achievement of its objectives across the '
                        'entity and analyzes risks as a basis for determining how the risks should be managed.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': ['Q-THR-04: Does the organization implement an insider threat program that includes a '
                                   'cross-discipline insider threat incident handling team? .',
                                   'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the '
                                   'potential attack vectors that attackers could use to attack the organization? .',
                                   'Q-THR-01: Does the organization implement a threat awareness program that includes a '
                                   'cross-organization information-sharing capability? .',
                                   'Q-TPM-04.3: Does the organization ensure that the interests of third-party service '
                                   'providers are consistent with and reflect organizational interests?.',
                                   'Q-TPM-04: Does the organization mitigate the risks associated with third-party access to '
                                   "the organization's systems and data?.",
                                   'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools '
                                   'and procurement methods for the purchase of unique systems, system components or '
                                   'services?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.'],
          'objective_title': 'CC3.3.1: Considers Various Types of Fraud',
          'requirement_description': 'The assessment of fraud considers fraudulent reporting, possible loss of assets, and '
                                     'corruption resulting from the various ways that fraud and misconduct can occur.',
          'subchapter': 'CC3.3: COSO Principle 8: The entity considers the potential for fraud in assessing risks to the '
                        'achievement of objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.3.2: Assesses Incentives and Pressures',
          'requirement_description': 'The assessment of fraud risks considers incentives and pressures.',
          'subchapter': 'CC3.3: COSO Principle 8: The entity considers the potential for fraud in assessing risks to the '
                        'achievement of objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.3.3: Assesses Opportunities',
          'requirement_description': 'The assessment of fraud risk considers opportunities for unauthorized acquisition, use, '
                                     "or disposal of assets, altering the entity's reporting records, or committing other "
                                     'inappropriate acts.',
          'subchapter': 'CC3.3: COSO Principle 8: The entity considers the potential for fraud in assessing risks to the '
                        'achievement of objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.3.4: Assesses Attitudes and Rationalizations',
          'requirement_description': 'The assessment of fraud risk considers how management and other personnel might engage '
                                     'in or justify inappropriate actions.',
          'subchapter': 'CC3.3: COSO Principle 8: The entity considers the potential for fraud in assessing risks to the '
                        'achievement of objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.3.5: Considers the Risks Related to the Use of IT and Access to Information',
          'requirement_description': 'The assessment of fraud risks includes consideration of internal and external threats '
                                     'and vulnerabilities that arise specifically from the use of IT and access to '
                                     'information. ',
          'subchapter': 'CC3.3: COSO Principle 8: The entity considers the potential for fraud in assessing risks to the '
                        'achievement of objectives.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': ['Q-TPM-10: Does the organization control changes to services by suppliers, taking into '
                                   'account the criticality of business information, systems and processes that are in scope '
                                   'by the third-party?.',
                                   'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.',
                                   'Q-PRM-01: Does the organization facilitate the implementation of cybersecurity and '
                                   'privacy-related resource planning controls?.',
                                   'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, '
                                   'prior to the implementation of the change?.',
                                   'Q-CHG-02.3: Does the organization include a cybersecurity representative in the '
                                   'configuration change control review process?.',
                                   'Q-CHG-02.2: Does the organization appropriately test and document proposed changes in a '
                                   'non-production environment before changes are implemented in a production environment?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CHG-01: Does the organization facilitate the implementation of a change management '
                                   'program?.'],
          'objective_title': 'CC3.4.1: Assesses Changes in the External Environment',
          'requirement_description': 'The risk identification process considers changes to the regulatory, economic, and '
                                     'physical environment in which the entity operates.',
          'subchapter': 'CC3.4: COSO Principle 9: The entity identifies and assesses changes that could significantly impact '
                        'the system of internal control.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.4.2: Assesses Changes in the Business Model',
          'requirement_description': 'The entity considers the potential impacts of new business lines, dramatically altered '
                                     'compositions of existing business lines, acquired or divested business operations on the '
                                     'system of internal control, rapid growth, changing reliance on foreign geographies, and '
                                     'new technologies.',
          'subchapter': 'CC3.4: COSO Principle 9: The entity identifies and assesses changes that could significantly impact '
                        'the system of internal control.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.4.3: Assesses Changes in Leadership',
          'requirement_description': 'The entity considers changes in management and respective attitudes and philosophies on '
                                     'the system of internal control.',
          'subchapter': 'CC3.4: COSO Principle 9: The entity identifies and assesses changes that could significantly impact '
                        'the system of internal control.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.4.4: Assess Changes in Systems and Technology',
          'requirement_description': "The risk identification process considers changes arising from changes in the entity's "
                                     'systems and changes in the technology environment. ',
          'subchapter': 'CC3.4: COSO Principle 9: The entity identifies and assesses changes that could significantly impact '
                        'the system of internal control.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.4.5: Assess Changes in Vendor and Business Partner',
          'requirement_description': 'The risk identification process considers changes in vendor and business partner '
                                     'relationships. ',
          'subchapter': 'CC3.4: COSO Principle 9: The entity identifies and assesses changes that could significantly impact '
                        'the system of internal control.'},
         {'chapter_title': 'RA: risk assessment',
          'conformity_questions': [],
          'objective_title': 'CC3.4.6: Assesses Changes in Threats and Vulnerabilities',
          'requirement_description': 'The risk identification process assesses changes in (1) internal and external threats to '
                                     "and vulnerabilities of the components of the entity's systems and (2) the likelihood and "
                                     "magnitude of the resultant risks to the achievement of the entity's objectives.",
          'subchapter': 'CC3.4: COSO Principle 9: The entity identifies and assesses changes that could significantly impact '
                        'the system of internal control.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': ['Q-SEA-02: Does the organization develop an enterprise architecture, aligned with '
                                   'industry-recognized leading practices, with consideration for cybersecurity and privacy '
                                   'principles that addresses risk to organizational operations, assets, individuals, other '
                                   'organizations? .',
                                   'Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.',
                                   'Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.',
                                   'Q-PRM-05: Does the organization identify critical system components and functions by '
                                   'performing a criticality analysis for critical systems, system components or services at '
                                   'pre-defined decision points in the Secure Development Life Cycle (SDLC)? .',
                                   'Q-PRM-04: Does the organization assess cybersecurity and privacy controls in system '
                                   'project development to determine the extent to which the controls are implemented '
                                   'correctly, operating as intended and producing the desired outcome with respect to meeting '
                                   'the requirements?.',
                                   'Q-PRM-03: Does the organization identify and allocate resources for management, '
                                   'operational, technical and privacy requirements within business process planning for '
                                   'projects / initiatives?.',
                                   'Q-IAO-06: Does the organization perform Information Assurance Program (IAP) activities to '
                                   'evaluate the design, implementation and effectiveness of technical cybersecurity and '
                                   'privacy controls?.',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.',
                                   'Q-IAO-03.1: Does the organization plan and coordinate Information Assurance Program (IAP) '
                                   'activities with affected stakeholders before conducting such activities in order to reduce '
                                   'the potential impact on operations? .',
                                   'Q-IAO-02.2: Does the organization conduct specialized assessments for:   -  Statutory, '
                                   'regulatory and contractual compliance obligations;  -  Monitoring capabilities;   -  '
                                   'Mobile devices;  -  Databases;  -  Application security;  -  Embedded technologies (e.g., '
                                   'IoT, OT, etc.);  -  Vulnerability management;   -  Malicious code;   -  Insider threats '
                                   'and  -  Performance/load testing? .',
                                   'Q-IAO-02.1: Does the organization ensure assessors or assessment teams have the '
                                   'appropriate independence to conduct cybersecurity and privacy control assessments? .',
                                   'Q-IAO-02: Does the organization formally assess the cybersecurity and privacy controls in '
                                   'systems, applications and services through Information Assurance Program (IAP) activities '
                                   'to determine the extent to which the controls are implemented correctly, operating as '
                                   'intended and producing the desired outcome with respect to meeting expected requirements?.',
                                   'Q-IAO-01: Does the organization facilitate the implementation of cybersecurity and privacy '
                                   'assessment and authorization controls? .',
                                   'Q-CPL-04: Does the organization thoughtfully plan audits by including input from '
                                   'operational risk and compliance partners to minimize the impact of audit-related '
                                   'activities on business operations?.',
                                   'Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the '
                                   "organization's cybersecurity and privacy policies and standards? .",
                                   'Q-CPL-03: Does the organization ensure managers regularly review the processes and '
                                   'documented procedures within their area of responsibility to adhere to appropriate '
                                   'security policies, standards and other applicable requirements?.',
                                   'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) '
                                   'to assist senior management in performance monitoring and trend analysis of the '
                                   'cybersecurity and privacy program?.',
                                   'Q-GOV-05.1: Does the organization develop, report and monitor Key Performance Indicators '
                                   '(KPIs) to assist organizational management in performance monitoring and trend analysis of '
                                   'the cybersecurity and privacy program?.',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.'],
          'objective_title': 'CC4.1.1: Considers a Mix of Ongoing and Separate Evaluations',
          'requirement_description': 'Management includes a balance of ongoing and separate evaluations.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.1.2: Considers Rate of Change',
          'requirement_description': 'Management considers the rate of change in business and business processes when '
                                     'selecting and developing ongoing and separate evaluations.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.1.3: Establishes Baseline Understanding',
          'requirement_description': 'The design and current state of an internal control system are used to establish a '
                                     'baseline for ongoing and separate evaluations.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.1.4: Uses Knowledgeable Personnel',
          'requirement_description': 'Evaluators performing ongoing and separate evaluations have sufficient knowledge to '
                                     'understand what is being evaluated.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.1.5: Integrates With Business Processes',
          'requirement_description': 'Ongoing evaluations are built into the business processes and adjust to changing '
                                     'conditions.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.1.6: Adjusts Scope and Frequency',
          'requirement_description': 'Management varies the scope and frequency of separate evaluations depending on risk.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.1.7: Objectively Evaluates',
          'requirement_description': 'Separate evaluations are performed periodically to provide objective feedback.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.1.8: Considers Different Types of Ongoing and Separate Evaluations',
          'requirement_description': 'Management uses a variety of ongoing and separate risk and control evaluations, to '
                                     'determine whether internal controls are present and functioning. Depending on the '
                                     "entity's objectives, such risk and control evaluations may include first- and "
                                     'second-line monitoring and control testing, internal audit assessments, compliance '
                                     'assessments, resilience assessments, vulnerability  scans, security assessment, '
                                     'penetration testing, and thirdparty assessments.',
          'subchapter': "CC4.1: COSO Principle 16: The entity'selects, develops, and performs ongoing and/or separate "
                        'evaluations to ascertain whether the components of internal control are present and functioning.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': ['Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing '
                                   'basis and ensure assets are protected against known attacks? .',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-TPM-09: Does the organization address weaknesses or deficiencies in supply chain '
                                   'elements identified during independent or organizational assessments of such elements? .',
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
                                   'Q-IAO-05: Does the organization use a Plan of Action and Milestones (POA&M), or similar '
                                   'mechanisms, to document planned remedial actions to correct weaknesses or deficiencies '
                                   'noted during the assessment of the security controls and to reduce or eliminate known '
                                   'vulnerabilities?.',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': 'CC4.2.1: Assesses Results',
          'requirement_description': 'Management and the board of directors, as appropriate, assess results of ongoing and '
                                     'separate evaluations.',
          'subchapter': 'CC4.2: COSO Principle 17: The entity evaluates and communicates internal control deficiencies in a '
                        'timely manner to those parties responsible for taking corrective action, including senior management '
                        'and the board of directors, as appropriate.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.2.2: Communicates Deficiencies',
          'requirement_description': 'Deficiencies are communicated to parties responsible for taking corrective action and to '
                                     'senior management and the board of directors, as appropriate.',
          'subchapter': 'CC4.2: COSO Principle 17: The entity evaluates and communicates internal control deficiencies in a '
                        'timely manner to those parties responsible for taking corrective action, including senior management '
                        'and the board of directors, as appropriate.'},
         {'chapter_title': 'MA: monitoring activities',
          'conformity_questions': [],
          'objective_title': 'CC4.2.3: Monitors Corrective Action',
          'requirement_description': 'Management tracks whether deficiencies are remedied on a timely basis.',
          'subchapter': 'CC4.2: COSO Principle 17: The entity evaluates and communicates internal control deficiencies in a '
                        'timely manner to those parties responsible for taking corrective action, including senior management '
                        'and the board of directors, as appropriate.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': ['Q-OPS-02: Does the organization develop a security Concept of Operations (CONOPS) that '
                                   'documents management, operational and technical measures implemented to apply '
                                   'defense-in-depth techniques?.',
                                   'Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-SEA-02: Does the organization develop an enterprise architecture, aligned with '
                                   'industry-recognized leading practices, with consideration for cybersecurity and privacy '
                                   'principles that addresses risk to organizational operations, assets, individuals, other '
                                   'organizations? .',
                                   'Q-SEA-01.1: Does the organization centrally-manage the organization-wide management and '
                                   'implementation of cybersecurity and privacy controls and related processes?.',
                                   'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.',
                                   'Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.',
                                   'Q-HRS-11: Does the organization implement and maintain Separation of Duties (SoD) to '
                                   'prevent potential inappropriate activity without collusion?.'],
          'objective_title': 'CC5.1.1: Integrates With Risk Assessment',
          'requirement_description': 'Control activities help ensure that risk responses that address and mitigate risks are '
                                     'carried out.  ',
          'subchapter': "CC5.1: COSO Principle 10: The entity'selects and develops control activities that contribute to the "
                        'mitigation of risks to the achievement of objectives to acceptable levels.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': "CC5.1.2: Considers entity'specific Factors",
          'requirement_description': 'Management considers how the environment, complexity, nature, and scope of its '
                                     'operations, as well as the specific characteristics of its organization, affect the '
                                     'selection and development of control activities.',
          'subchapter': "CC5.1: COSO Principle 10: The entity'selects and develops control activities that contribute to the "
                        'mitigation of risks to the achievement of objectives to acceptable levels.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.1.3: Determines Relevant Business Processes',
          'requirement_description': 'Management determines which relevant business processes require control activities.',
          'subchapter': "CC5.1: COSO Principle 10: The entity'selects and develops control activities that contribute to the "
                        'mitigation of risks to the achievement of objectives to acceptable levels.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.1.4: Evaluates a Mix of Control Activity Types',
          'requirement_description': 'Control activities include a range and variety of controls and may include a balance of '
                                     'approaches to mitigate risks, considering both manual and automated controls, and '
                                     'preventive and detective controls.',
          'subchapter': "CC5.1: COSO Principle 10: The entity'selects and develops control activities that contribute to the "
                        'mitigation of risks to the achievement of objectives to acceptable levels.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.1.5: Considers at What Level Activities Are Applied',
          'requirement_description': 'Management considers control activities at various levels in the entity.',
          'subchapter': "CC5.1: COSO Principle 10: The entity'selects and develops control activities that contribute to the "
                        'mitigation of risks to the achievement of objectives to acceptable levels.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.1.6: Addresses Segregation of Duties',
          'requirement_description': 'Management segregates incompatible duties, and where such segregation is not practical, '
                                     'management selects and develops alternative control activities.',
          'subchapter': "CC5.1: COSO Principle 10: The entity'selects and develops control activities that contribute to the "
                        'mitigation of risks to the achievement of objectives to acceptable levels.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': ['Q-TDA-02: Does the organization ensure risk-based technical and functional specifications '
                                   'are established to define a Minimum Viable Product (MVP)?.',
                                   'Q-TDA-01: Does the organization facilitate the implementation of tailored development and '
                                   'acquisition strategies, contract tools and procurement methods to meet unique business '
                                   'needs?.',
                                   'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.',
                                   'Q-RSK-10: Does the organization conduct a Data Protection Impact Assessment (DPIA) on '
                                   'systems, applications and services that store, process and/or transmit Personal Data (PD) '
                                   'to identify and remediate reasonably-expected risks?.',
                                   'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.',
                                   'Q-PRM-07: Does the organization ensure changes to systems within the Secure Development '
                                   'Life Cycle (SDLC) are controlled through formal change control procedures? .',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.',
                                   'Q-PRM-05: Does the organization identify critical system components and functions by '
                                   'performing a criticality analysis for critical systems, system components or services at '
                                   'pre-defined decision points in the Secure Development Life Cycle (SDLC)? .',
                                   'Q-PRM-04: Does the organization assess cybersecurity and privacy controls in system '
                                   'project development to determine the extent to which the controls are implemented '
                                   'correctly, operating as intended and producing the desired outcome with respect to meeting '
                                   'the requirements?.',
                                   'Q-PRM-01: Does the organization facilitate the implementation of cybersecurity and '
                                   'privacy-related resource planning controls?.'],
          'objective_title': 'CC5.2.1: Determines Dependency Between the Use of Technology in Business Processes and '
                             'Technology General Controls',
          'requirement_description': 'Management understands and determines the dependency and linkage between business '
                                     'processes, automated control activities, and technology general controls.',
          'subchapter': 'CC5.2: COSO Principle 11: The entity also selects and develops general control activities over '
                        'technology to support the achievement of objectives.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.2.2: Establishes Relevant Technology Infrastructure Control Activities',
          'requirement_description': 'Management selects and develops control activities over the technology infrastructure, '
                                     'which are designed and implemented to help ensure the completeness, accuracy, and '
                                     'availability of technology processing.',
          'subchapter': 'CC5.2: COSO Principle 11: The entity also selects and develops general control activities over '
                        'technology to support the achievement of objectives.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.2.3: Establishes Relevant Security Management Process Controls Activities',
          'requirement_description': 'Management selects and develops control activities that are designed and implemented to '
                                     'restrict technology access rights to authorized users commensurate with their job '
                                     "responsibilities and to protect the entity's assets from external threats.",
          'subchapter': 'CC5.2: COSO Principle 11: The entity also selects and develops general control activities over '
                        'technology to support the achievement of objectives.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.2.4: Establishes Relevant Technology Acquisition, Development, and Maintenance Process '
                             'Control Activities',
          'requirement_description': 'Management selects and develops control activities over the acquisition, development, '
                                     'and maintenance of technology and its infrastructure to achieve management?s objectives.',
          'subchapter': 'CC5.2: COSO Principle 11: The entity also selects and develops general control activities over '
                        'technology to support the achievement of objectives.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-HRS-10: Does the organization govern third-party personnel by reviewing and monitoring '
                                   'third-party cybersecurity and privacy roles and responsibilities?.',
                                   'Q-HRS-03.2: Does the organization ensure that all security-related positions are staffed '
                                   'by qualified individuals who have the necessary skill set? .',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': 'CC5.3.1: Establishes Policies and Procedures to Support Deployment of Management ?s Directives',
          'requirement_description': 'Management establishes control activities that are built into business processes and '
                                     'employees? day-to-day activities through policies establishing what is expected and '
                                     'relevant procedures specifying actions.',
          'subchapter': 'CC5.3: COSO Principle 12: The entity deploys control activities through policies that establish what '
                        'is expected and in procedures that put policies into action.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.3.2: Establishes Responsibility and Accountability for Executing Policies and Procedures',
          'requirement_description': 'Management establishes responsibility and accountability for control activities with '
                                     'management (or other designated personnel) of the business unit or function in which the '
                                     'relevant risks reside.',
          'subchapter': 'CC5.3: COSO Principle 12: The entity deploys control activities through policies that establish what '
                        'is expected and in procedures that put policies into action.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.3.3: Performs in a Timely Manner',
          'requirement_description': 'Responsible personnel perform control activities in a timely manner as defined by the '
                                     'policies and procedures.',
          'subchapter': 'CC5.3: COSO Principle 12: The entity deploys control activities through policies that establish what '
                        'is expected and in procedures that put policies into action.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.3.4: Takes Corrective Action',
          'requirement_description': 'Responsible personnel investigate and act on matters identified as a result of executing '
                                     'control activities.',
          'subchapter': 'CC5.3: COSO Principle 12: The entity deploys control activities through policies that establish what '
                        'is expected and in procedures that put policies into action.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.3.5: Performs Using Competent Personnel',
          'requirement_description': 'Competent personnel with sufficient authority perform control activities with diligence '
                                     'and continuing focus.',
          'subchapter': 'CC5.3: COSO Principle 12: The entity deploys control activities through policies that establish what '
                        'is expected and in procedures that put policies into action.'},
         {'chapter_title': 'CA: control activities',
          'conformity_questions': [],
          'objective_title': 'CC5.3.6: Reassesses Policies and Procedures',
          'requirement_description': 'Management periodically reviews control activities to determine their continued '
                                     'relevance and refreshes them when necessary.',
          'subchapter': 'CC5.3: COSO Principle 12: The entity deploys control activities through policies that establish what '
                        'is expected and in procedures that put policies into action.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-NET-06.1: Does the organization implement security management subnets to isolate '
                                   'security tools and support components from other internal system components by '
                                   'implementing separate subnetworks with managed interfaces to other components of the '
                                   'system? .',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-05.1: Does the organization prohibit the direct connection of a sensitive system to '
                                   'an external network without the use of an organization-defined boundary protection device? '
                                   '.',
                                   'Q-NET-04: Does the organization design, implement and review firewall and router '
                                   'configurations to restrict connections between untrusted networks and internal systems? .',
                                   'Q-NET-03.1: Does the organization limit the number of concurrent external network '
                                   'connections to its systems?.',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-NET-01: Does the organization develop, govern & update procedures to facilitate the '
                                   'implementation of network security controls?.',
                                   'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that '
                                   "conform to the principle of 'least privilege?'.",
                                   'Q-IAC-16: Does the organization restrict and control privileged access rights for users '
                                   'and services?.',
                                   'Q-IAC-15: Does the organization proactively govern account management of individual, '
                                   'group, system, application, guest and temporary accounts?.',
                                   'Q-IAC-10.8: Does the organization ensure vendor-supplied defaults are changed as part of '
                                   'the installation process?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
                                   'Q-IAC-09.1: Does the organization ensure proper user identification management for '
                                   'non-consumer users and administrators? .',
                                   'Q-IAC-09: Does the organization govern naming standards for usernames and systems?.',
                                   'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.',
                                   'Q-IAC-05: Does the organization identify and authenticate third-party systems and '
                                   'services?.',
                                   'Q-IAC-04: Does the organization uniquely and centrally Authenticate, Authorize and Audit '
                                   '(AAA) devices before establishing a connection using bidirectional authentication that is '
                                   'cryptographically- based and replay resistant?.',
                                   'Q-IAC-03: Does the organization uniquely and centrally Authenticate, Authorize and Audit '
                                   '(AAA) third-party users and processes that provide services to the organization?.',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.',
                                   'Q-CRY-09.2: Does the organization facilitate the production and management of asymmetric '
                                   'cryptographic keys using Federal Information Processing Standards (FIPS)-compliant key '
                                   "management technology and processes that protect the user's private key?.",
                                   'Q-CRY-09.1: Does the organization facilitate the production and management of symmetric '
                                   'cryptographic keys using Federal Information Processing Standards (FIPS)-compliant key '
                                   'management technology and processes? .',
                                   'Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.',
                                   'Q-CRY-08: Does the organization securely implement an internal Public Key Infrastructure '
                                   '(PKI) infrastructure or obtain PKI services from a reputable PKI service provider?.',
                                   'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .',
                                   'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.'],
          'objective_title': 'CC6.1.1: Identifies and Manages the Inventory of Information Assets',
          'requirement_description': 'The entity identifies, inventories, classifies, and manages information assets, (for '
                                     'example, infrastructure, software, and data).',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.2: Restricts  Logical Access',
          'requirement_description': 'The entity restricts logical access to information assets, including, infrastructure '
                                     '(for example, server, storage, network elements, APIs, and endpoint devices), software, '
                                     'and data (at rest, during processing, or in transmission) through the use of access '
                                     'control software, rule sets, and standard configuration hardening processes.',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.3: Identifies and Authenticates Users',
          'requirement_description': 'The entity identifies and authenticates persons, infrastructure, and software prior to '
                                     'accessing information assets, whether locally or remotely. The entity uses more complex '
                                     'or advanced user authentication techniques such as multifactor authentication when such '
                                     'protections are deemed appropriate based on its risk mitigation strategy.',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.4: Considers Network Segmentation',
          'requirement_description': 'The entity uses network segmentation, zero trust architectures, and other techniques to '
                                     "isolate unrelated portions of the entity's information technology from each other based "
                                     "on the entity's risk mitigation strategy.",
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.5: Manages Points of Access',
          'requirement_description': 'Points of access by outside entities and the types of data that flow through the points '
                                     'of access are identified, inventoried, and managed. The types of individuals and systems '
                                     'using each point of access are identified, documented, and managed. ',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.6: Restricts Access to Information Assets',
          'requirement_description': 'Combinations of data classification, separate data structures, port restrictions, access '
                                     'protocol restrictions, user identification, and digital certificates are used to '
                                     'establish access control rules and configuration standards for information assets.  ',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.7: Manages Identification and Authentication',
          'requirement_description': 'Identification and authentication requirements are established, documented, and managed '
                                     'for individuals and systems accessing entity information, infrastructure and software.',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.8: Manages Credentials for Infrastructure and Software',
          'requirement_description': 'New internal and external infrastructure and software  are registered, authorized, and '
                                     'documented prior to being granted access credentials and implemented on the network or '
                                     'access point. Credentials are removed and access is disabled when access is no longer '
                                     'required or the infrastructure and software are no longer in use. ',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.9: Uses Encryption to Protect Data',
          'requirement_description': 'The entity uses encryption to protect data (at rest, during processing, or in '
                                     "transmission ) when such protections are deemed appropriate based on the entity's risk "
                                     'mitigation strategy.',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.10: Protects Cryptographic Keys',
          'requirement_description': 'The entity protects cryptographic keys during generation, storage, use, and destruction. '
                                     'Cryptographic modules, algorithms, key lengths, and architectures are appropriate based '
                                     "on the entity's risk mitigation strategy.",
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.11: Assesses New Architectures',
          'requirement_description': 'The entity identifies new system architectures and assesses their security prior to '
                                     'implementation into the system environment.',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.12: Restricts Access to and Use of Confidential Information for Identified Purposes',
          'requirement_description': 'Logical access to and use of confidential information is restricted to identified '
                                     'purposes.',
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.1.13: Restricts Access to and the Use of Personal Information',
          'requirement_description': 'Logical access to and use of personal information is restricted to authorized personnel '
                                     'who require such access to fulfill the identified purposes to support the achievement of '
                                     "the entity's objectives related to privacy.",
          'subchapter': 'CC6.1: The entity implements logical access security software, infrastructure, and architectures over '
                        "protected information assets to protect them from security events to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-IAC-17: Does the organization periodically-review the privileges assigned to individuals '
                                   'and service accounts to validate the need for such privileges and reassign or remove '
                                   'unnecessary privileges, as necessary?.'],
          'objective_title': 'CC6.2.1: Creates Access Credentials to Protected Information Assets',
          'requirement_description': 'The entity creates credentials for accessing protected information assets based on an '
                                     "authorization from the system's asset owner or authorized custodian. Authorization is "
                                     'required for the creation of all types of credentials of individuals (for example, '
                                     'employees, contractors, vendors, and business partner personnel), systems, and software.',
          'subchapter': 'CC6.2: Prior to issuing system credentials and granting system access, the entity registers and '
                        'authorizes new internal and external users whose access is administered by the entity. For those '
                        'users whose access is administered by the entity, user system credentials are removed when user '
                        'access is no longer authorized.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.2.2: Reviews Validity of Access Credentials',
          'requirement_description': 'The entity reviews access credentials on a periodic basis for validity (for example, '
                                     'employees, contractors, vendors, and business partner personnel) and inappropriate '
                                     'system or service accounts.',
          'subchapter': 'CC6.2: Prior to issuing system credentials and granting system access, the entity registers and '
                        'authorizes new internal and external users whose access is administered by the entity. For those '
                        'users whose access is administered by the entity, user system credentials are removed when user '
                        'access is no longer authorized.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.2.3: Prevents the Use of Credentials When No Longer Valid',
          'requirement_description': 'Processes are in place to disable, destroy, or otherwise prevent the use of access '
                                     'credentials when no longer valid.',
          'subchapter': 'CC6.2: Prior to issuing system credentials and granting system access, the entity registers and '
                        'authorizes new internal and external users whose access is administered by the entity. For those '
                        'users whose access is administered by the entity, user system credentials are removed when user '
                        'access is no longer authorized.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.'],
          'objective_title': 'CC6.3.1: Creates or Modifies Access to Protected Information Assets',
          'requirement_description': 'Processes are in place to create or modify access to protected information assets based '
                                     'on authorization  from the asset?s owner.',
          'subchapter': 'CC6.3: The entity authorizes, modifies, or removes access to data, software, functions, and other '
                        'protected information assets based on roles, responsibilities, or the system design and changes, '
                        'giving consideration to the concepts of least privilege and segregation of duties, to meet the '
                        "entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.3.2: Removes Access to Protected Information Asset',
          'requirement_description': 'Processes are in place to remove access to protected information assets when no longer '
                                     'required.',
          'subchapter': 'CC6.3: The entity authorizes, modifies, or removes access to data, software, functions, and other '
                        'protected information assets based on roles, responsibilities, or the system design and changes, '
                        'giving consideration to the concepts of least privilege and segregation of duties, to meet the '
                        "entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.3.3: Uses Access Control Structures',
          'requirement_description': 'The entity uses access control structures, such as role-based access controls, to '
                                     'restrict access to protected information assets, limit privileges, and support '
                                     'segregation of incompatible functions.',
          'subchapter': 'CC6.3: The entity authorizes, modifies, or removes access to data, software, functions, and other '
                        'protected information assets based on roles, responsibilities, or the system design and changes, '
                        'giving consideration to the concepts of least privilege and segregation of duties, to meet the '
                        "entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.3.4: Reviews Access Roles and Rules',
          'requirement_description': 'The appropriateness of access roles and access rules is reviewed on a periodic basis for '
                                     'unnecessary and inappropriate individuals (for example, employees, contractors, vendors, '
                                     'business partner personnel) and inappropriate system or service accounts. Access roles '
                                     'and rules are modified as appropriate.',
          'subchapter': 'CC6.3: The entity authorizes, modifies, or removes access to data, software, functions, and other '
                        'protected information assets based on roles, responsibilities, or the system design and changes, '
                        'giving consideration to the concepts of least privilege and segregation of duties, to meet the '
                        "entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-PES-03: Does the organization enforce physical access authorizations for all physical '
                                   'access points (including designated entry/exit points) to facilities (excluding those '
                                   'areas within the facility officially designated as publicly accessible)?.',
                                   'Q-PES-02.1: Does the organization authorize physical access to facilities based on the '
                                   'position or role of the individual?.',
                                   'Q-PES-02: Does the organization maintain a current list of personnel with authorized '
                                   'access to organizational facilities (except for those areas within the facility officially '
                                   'designated as publicly accessible)?.',
                                   'Q-PES-01: Does the organization facilitate the operation of physical and environmental '
                                   'protection controls? .'],
          'objective_title': 'CC6.4.1: Creates or Modifies Physical Access',
          'requirement_description': 'Processes are in place to create or modify physical access by employees, contractors, '
                                     'vendors, and business partner personnel to facilities such as data centers, office '
                                     'spaces, and work areas, based on appropriate authorization.',
          'subchapter': 'CC6.4: The entity restricts physical access to facilities and protected information assets (for '
                        'example, data center facilities,  back-up media storage, and other sensitive locations) to authorized '
                        "personnel to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.4.2: Removes Physical Access',
          'requirement_description': 'Processes are in place to remove physical access to facilities and protected information '
                                     'assets when an employee, contractor, vendor, or business partner no longer requires '
                                     'access.',
          'subchapter': 'CC6.4: The entity restricts physical access to facilities and protected information assets (for '
                        'example, data center facilities,  back-up media storage, and other sensitive locations) to authorized '
                        "personnel to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.4.3: Reviews Physical Access',
          'requirement_description': 'Processes are in place to periodically review physical access to help ensure consistency '
                                     'with job responsibilities.',
          'subchapter': 'CC6.4: The entity restricts physical access to facilities and protected information assets (for '
                        'example, data center facilities,  back-up media storage, and other sensitive locations) to authorized '
                        "personnel to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.4.4: Recovers Physical Devices',
          'requirement_description': 'Processes are in place to recover entity devices (for example, badges, laptops, and '
                                     'mobile devices) when an employee, contractor, vendor, or business partner no longer '
                                     'requires access.',
          'subchapter': 'CC6.4: The entity restricts physical access to facilities and protected information assets (for '
                        'example, data center facilities,  back-up media storage, and other sensitive locations) to authorized '
                        "personnel to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-TDA-11.2: [deprecated - incorporated into AST-09].',
                                   'Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for '
                                   'an organization-defined time period to fulfill the purpose(s) identified in the notice or '
                                   'as required by law;  -  Disposes of, destroys, erases, and/or anonymizes the PI, '
                                   'regardless of the method of storage; and  -  Uses organization-defined techniques or '
                                   'methods to ensure secure deletion or destruction of PD (including originals, copies and '
                                   'archived records)?.',
                                   'Q-DCH-21: Does the organization securely dispose of, destroy or erase information?.',
                                   'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity '
                                   'commensurate with the classification or sensitivity of the information prior to disposal, '
                                   'release out of organizational control or release for reuse?.',
                                   'Q-DCH-08: Does the organization securely dispose of media when it is no longer required, '
                                   'using formal procedures? .',
                                   'Q-AST-09: Does the organization securely dispose of, destroy or repurpose system '
                                   'components using organization-defined techniques and methods to prevent such components '
                                   'from entering the gray market?.'],
          'objective_title': 'CC6.5.1: Identifies Data and Software for Disposal',
          'requirement_description': 'Procedures are in place to identify data and software stored on equipment to be disposed '
                                     'and to render such data and software unreadable.',
          'subchapter': 'CC6.5: The entity discontinues logical and physical protections over physical assets only after the '
                        'ability to read or recover data and software from those assets has been diminished and is no longer '
                        'required to meet the entity?s objectives.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.5.2: Removes Data and Software for disposal',
          'requirement_description': 'Procedures are in place to remove, delete, or otherwise render data and software '
                                     'inaccessible from physical assets and other devices owned by the entity, its vendors, '
                                     'and employees when the data and software are no longer required on the asset or the '
                                     'asset will no longer be under the control of the entity.',
          'subchapter': 'CC6.5: The entity discontinues logical and physical protections over physical assets only after the '
                        'ability to read or recover data and software from those assets has been diminished and is no longer '
                        "required to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.',
                                   'Q-NET-13: Does the organization protect the confidentiality, integrity and availability of '
                                   'electronic messaging communications?.',
                                   'Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-NET-12: Does the organization use strong cryptography and security protocols to '
                                   'safeguard sensitive/regulated data during transmission over open, public networks?.',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-04.1: Does the organization configure firewall and router configurations to deny '
                                   'network traffic by default and allow network traffic by exception (e.g., deny all, permit '
                                   'by exception)? .',
                                   'Q-NET-04: Does the organization design, implement and review firewall and router '
                                   'configurations to restrict connections between untrusted networks and internal systems? .',
                                   'Q-NET-03.1: Does the organization limit the number of concurrent external network '
                                   'connections to its systems?.',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-NET-02: Does the organization implement security functions as a layered structure that '
                                   'minimizes interactions between layers of the design and avoiding any dependence by lower '
                                   'layers on the functionality or correctness of higher layers? .',
                                   'Q-NET-01: Does the organization develop, govern & update procedures to facilitate the '
                                   'implementation of network security controls?.'],
          'objective_title': 'CC6.6.1: Restricts Access',
          'requirement_description': 'The types of activities that can occur through a communication channel (for example, FTP '
                                     'site, router port) are restricted. ',
          'subchapter': 'CC6.6: The entity implements logical access security measures to protect against threats from sources '
                        'outside its system boundaries.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.6.2: Protects Identification and Authentication Credentials',
          'requirement_description': 'Identification and authentication credentials are protected during transmission outside '
                                     'its system boundaries.',
          'subchapter': 'CC6.6: The entity implements logical access security measures to protect against threats from sources '
                        'outside its system boundaries.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.6.3: Requires Additional Authentication or Credentials',
          'requirement_description': 'Additional authentication information or credentials are required when accessing the '
                                     'system from outside its boundaries.',
          'subchapter': 'CC6.6: The entity implements logical access security measures to protect against threats from sources '
                        'outside its system boundaries.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.6.4: Implements Boundary Protection Systems',
          'requirement_description': 'Boundary protection systems (for example, firewalls, demilitarized zones, intrusion '
                                     'detection or prevention systems, and endpoint detection and response systems) are '
                                     'configured, implemented, and maintained to protect external access points.',
          'subchapter': 'CC6.6: The entity implements logical access security measures to protect against threats from sources '
                        'outside its system boundaries.'},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-NET-13: Does the organization protect the confidentiality, integrity and availability of '
                                   'electronic messaging communications?.',
                                   'Q-NET-12.2: Does the organization prohibit the transmission of unprotected '
                                   'sensitive/regulated data by end-user messaging technologies?.',
                                   'Q-MDM-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality and integrity of information on mobile devices through full-device or '
                                   'container encryption?.',
                                   'Q-MDM-01: Does the organization develop, govern & update procedures to facilitate the '
                                   'implementation of mobile device management controls?.',
                                   'Q-DCH-17: Does the organization secure ad-hoc exchanges of large digital files with '
                                   'internal or external parties?.',
                                   'Q-DCH-14: Does the organization utilize a process to assist users in making information '
                                   'sharing decisions to ensure data is appropriately protected?.',
                                   'Q-DCH-13.2: Does the organization restrict or prohibit the use of portable storage devices '
                                   'by users on external systems? .',
                                   'Q-DCH-13: Does the organization govern how external parties, systems and services are used '
                                   'to securely store, process and transmit data? .',
                                   'Q-DCH-12: Does the organization restrict removable media in accordance with data handling '
                                   'and acceptable usage parameters?.',
                                   'Q-DCH-10: Does the organization restrict the use of types of digital media on systems or '
                                   'system components? .',
                                   'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.',
                                   'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .',
                                   'Q-CFG-04.2: Does the organization allow only approved Internet browsers and email clients '
                                   'to run on systems?.'],
          'objective_title': 'CC6.7.1: Restricts the Ability to Perform Transmission',
          'requirement_description': 'Data loss prevention processes and technologies are used to restrict ability to '
                                     'authorize and execute transmission, movement and removal of information.',
          'subchapter': 'CC6.7: The entity restricts the transmission, movement, and removal of information to authorized '
                        'internal and external users and processes, and protects it during transmission, movement, or removal '
                        "to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.7.2: Uses Encryption Technologies or Secure Communication Channels to Protect Data',
          'requirement_description': 'Encryption technologies or secured communication channels are used to protect '
                                     'transmission of data and other communications beyond connectivity access points.',
          'subchapter': 'CC6.7: The entity restricts the transmission, movement, and removal of information to authorized '
                        'internal and external users and processes, and protects it during transmission, movement, or removal '
                        "to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.7.3: Protects Removal Media',
          'requirement_description': 'Encryption technologies and physical asset protections are used for removable media '
                                     '(such as USB drives and back-up tapes), as appropriate.',
          'subchapter': 'CC6.7: The entity restricts the transmission, movement, and removal of information to authorized '
                        'internal and external users and processes, and protects it during transmission, movement, or removal '
                        "to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.7.4: Protects Endpoint Devices',
          'requirement_description': 'Processes and controls are in place to protect endpoint devices (such as mobile devices, '
                                     'desktops, and sensors).',
          'subchapter': 'CC6.7: The entity restricts the transmission, movement, and removal of information to authorized '
                        'internal and external users and processes, and protects it during transmission, movement, or removal '
                        "to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': ['Q-NET-08: Does the organization implement Network Intrusion Detection / Prevention Systems '
                                   '(NIDS/NIPS) used to detect and/or prevent intrusions into the network? .',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-END-07: Does the organization utilize Host-based Intrusion Detection / Prevention '
                                   'Systems (HIDS / HIPS) on sensitive systems?.',
                                   'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect '
                                   'and report unauthorized changes to system files and configurations?.',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.',
                                   'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .',
                                   'Q-CHG-02.1: Does the organization prohibit unauthorized changes, unless '
                                   'organization-approved change requests are received?.'],
          'objective_title': 'CC6.8.1: Restricts Installation and modification Application and Software',
          'requirement_description': 'The ability to install and modify applications and software is restricted to authorized '
                                     'individuals. Utility software capable of bypassing normal operating or security '
                                     'procedures is limited to use by authorized individuals and is monitored regularly.',
          'subchapter': 'CC6.8: The entity implements controls to prevent or detect and act upon the introduction of '
                        "unauthorized or malicious software to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.8.2: Detects Unauthorized Changes to Software and Configuration Parameters',
          'requirement_description': 'Processes are in place to detect changes to software and configuration parameters that '
                                     'may be indicative of unauthorized or malicious software.',
          'subchapter': 'CC6.8: The entity implements controls to prevent or detect and act upon the introduction of '
                        "unauthorized or malicious software to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.8.3: Uses a Defined Change Control Process',
          'requirement_description': 'A management-defined change control process is used for the implementation of software. ',
          'subchapter': 'CC6.8: The entity implements controls to prevent or detect and act upon the introduction of '
                        "unauthorized or malicious software to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.8.4: Uses Antivirus and Anti-Malware Software',
          'requirement_description': 'Antivirus and anti-malware software on servers and endpoint devices is configured, '
                                     'implemented and maintained to provide for the interception or detection and remediation '
                                     'of malware.',
          'subchapter': 'CC6.8: The entity implements controls to prevent or detect and act upon the introduction of '
                        "unauthorized or malicious software to meet the entity's objectives."},
         {'chapter_title': 'LPAC: logical and physical access controls',
          'conformity_questions': [],
          'objective_title': 'CC6.8.5: Scans Information Assets From Outside the Entity for Malware and Other Unauthorized '
                             'Software',
          'requirement_description': 'Procedures are in place to scan information assets that have been transferred or '
                                     "returned to the entity's custody for malware and other unauthorized software. Detected "
                                     "malware or other software is removed prior to connection to the entity's network.",
          'subchapter': 'CC6.8: The entity implements controls to prevent or detect and act upon the introduction of '
                        "unauthorized or malicious software to meet the entity's objectives."},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': ['Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-END-06.1: Does the organization validate configurations through integrity checking of '
                                   'software and firmware?.',
                                   'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .',
                                   'Q-CFG-01: Does the organization facilitate the implementation of configuration management '
                                   'controls?.'],
          'objective_title': 'CC7.1.1: Uses Defined Configuration Standards',
          'requirement_description': 'The entity has defined configuration standards to be used for hardening systems.',
          'subchapter': 'CC7.1: To meet its objectives, the entity uses detection and monitoring procedures to identify (1) '
                        'changes to configurations that result in the introduction of new vulnerabilities, and (2) '
                        'susceptibilities to newly discovered vulnerabilities.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.1.2: Monitors Infrastructure and Software',
          'requirement_description': 'The entity monitors infrastructure and software for noncompliance with the standards, '
                                     "which could threaten the achievement of the entity's objectives.  ",
          'subchapter': 'CC7.1: To meet its objectives, the entity uses detection and monitoring procedures to identify (1) '
                        'changes to configurations that result in the introduction of new vulnerabilities, and (2) '
                        'susceptibilities to newly discovered vulnerabilities.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.1.3: Implements Change',
          'requirement_description': 'The IT system includes a change-detection mechanism (for example, file integrity '
                                     'monitoring tools) to alert personnel to unauthorized modifications of critical system '
                                     'files, configuration files, or content files. ',
          'subchapter': 'CC7.1: To meet its objectives, the entity uses detection and monitoring procedures to identify (1) '
                        'changes to configurations that result in the introduction of new vulnerabilities, and (2) '
                        'susceptibilities to newly discovered vulnerabilities.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.1.4: Detects Unknown or Unauthorized Components',
          'requirement_description': 'Procedures are in place to detect the introduction of unknown or unauthorized '
                                     'components.  ',
          'subchapter': 'CC7.1: To meet its objectives, the entity uses detection and monitoring procedures to identify (1) '
                        'changes to configurations that result in the introduction of new vulnerabilities, and (2) '
                        'susceptibilities to newly discovered vulnerabilities.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.1.5: Conducts Vulnerability Scans',
          'requirement_description': 'The entity conducts infrastructure and software vulnerability scans designed to identify '
                                     'potential vulnerabilities or misconfigurations on a periodic basis and after significant '
                                     'changes are made to the environment. Action is taken to remediate identified '
                                     "deficiencies in a timely manner to support the achievement of the entity's objectives.",
          'subchapter': 'CC7.1: To meet its objectives, the entity uses detection and monitoring procedures to identify (1) '
                        'changes to configurations that result in the introduction of new vulnerabilities, and (2) '
                        'susceptibilities to newly discovered vulnerabilities.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': ['Q-OPS-02: Does the organization develop a security Concept of Operations (CONOPS) that '
                                   'documents management, operational and technical measures implemented to apply '
                                   'defense-in-depth techniques?.',
                                   'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
                                   'Q-MON-16: Does the organization detect and respond to anomalous behavior that could '
                                   'indicate account compromise or other malicious activities?.',
                                   'Q-MON-06: Does the organization provide an event log report generation capability to aid '
                                   'in detecting and assessing anomalous activities? .',
                                   'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.',
                                   'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or '
                                   'similar automated tool, to support the centralized collection of security-related event '
                                   'logs?.',
                                   'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.',
                                   'Q-MON-01.6: Does the organization utilize Host-based Intrusion Detection / Prevention '
                                   'Systems (HIDS / HIPS) to actively alert on or block unwanted activities and send logs to a '
                                   'Security Incident Event Manager (SIEM), or similar automated tool, to maintain situational '
                                   'awareness?.',
                                   'Q-MON-01.5: Does the organization utilize Wireless Intrusion Detection / Protection '
                                   'Systems (WIDS / WIPS) to identify rogue wireless devices and to detect attack attempts via '
                                   'wireless networks? .',
                                   'Q-MON-01.4: Does the organization monitor, correlate and respond to alerts from physical, '
                                   'cybersecurity, privacy and supply chain activities to achieve integrated situational '
                                   'awareness? .',
                                   'Q-MON-01.3: Does the organization continuously monitor inbound and outbound communications '
                                   'traffic for unusual or unauthorized activities or conditions?.',
                                   'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or '
                                   'similar automated tool, to support near real-time analysis and incident escalation?.',
                                   'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS '
                                   '/ IPS) technologies on critical systems, key network segments and network choke points?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.'],
          'objective_title': 'CC7.2.1: Implements Detection Policies, Procedures, and Tools',
          'requirement_description': 'Detection policies, procedures, and tools are defined and implemented on infrastructure '
                                     'and software to identify potential intrusions, inappropriate access, and anomalies in '
                                     'the operation of or unusual activity on systems Procedures may include (1) a defined '
                                     'governance process for security event detection and management; (2) use of intelligence '
                                     'sources to identify newly discovered threats and vulnerabilities; and (3) logging of '
                                     'unusual system activities.',
          'subchapter': 'CC7.2: The entity monitors system components and the operation of those components for anomalies that '
                        "are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to "
                        'meet its objectives; anomalies are analyzed to determine whether they represent security events.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.2.2: Designs Detection Measures',
          'requirement_description': 'Detection measures are designed to identify anomalies that could result from actual or '
                                     'attempted (1) compromise of physical barriers; (2) unauthorized actions of authorized '
                                     'personnel; (3) use of compromised identification and authentication credentials; (4) '
                                     'unauthorized access from outside the system boundaries; (5) compromise of authorized '
                                     'external parties; and (6) implementation or connection of unauthorized hardware and '
                                     'software. ',
          'subchapter': 'CC7.2: The entity monitors system components and the operation of those components for anomalies that '
                        "are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to "
                        'meet its objectives; anomalies are analyzed to determine whether they represent security events.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.2.3: Implements Filters to Analyze Anomalies',
          'requirement_description': 'Management has implemented procedures to filter, summarize, and analyze anomalies to '
                                     'identify security events.',
          'subchapter': 'CC7.2: The entity monitors system components and the operation of those components for anomalies that '
                        "are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to "
                        'meet its objectives; anomalies are analyzed to determine whether they represent security events.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.2.4: Monitors Detection Tools for Effective Operation',
          'requirement_description': 'Management has implemented processes to monitor and maintain the effectiveness of '
                                     'detection tools.',
          'subchapter': 'CC7.2: The entity monitors system components and the operation of those components for anomalies that '
                        "are indicative of malicious acts, natural disasters, and errors affecting the entity's ability to "
                        'meet its objectives; anomalies are analyzed to determine whether they represent security events.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': ['Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .',
                                   'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?.",
                                   'Q-IRO-04.1: Does the organization address data breaches, or other incidents involving the '
                                   'unauthorized disclosure of sensitive or regulated data, according to applicable laws, '
                                   'regulations and contractual obligations? .',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.',
                                   'Q-IRO-01: Does the organization facilitate the implementation of incident response '
                                   'controls?.',
                                   'Q-END-06.2: Does the organization detect and respond to unauthorized configuration changes '
                                   'as cybersecurity incidents?.',
                                   'Q-MON-06: Does the organization provide an event log report generation capability to aid '
                                   'in detecting and assessing anomalous activities? .',
                                   'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.',
                                   'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or '
                                   'similar automated tool, to support the centralized collection of security-related event '
                                   'logs?.'],
          'objective_title': 'CC7.3.1: Responds to Security Incidents',
          'requirement_description': 'Procedures are in place for responding to security incidents and evaluating the '
                                     'effectiveness of those policies and procedures on a periodic basis. ',
          'subchapter': 'CC7.3: The entity evaluates security events to determine whether they could or have resulted in a '
                        'failure of the entity to meet its objectives (security incidents) and, if so, takes actions to '
                        'prevent or address such failures.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.3.2: Communicates and Reviews Detected Security Events',
          'requirement_description': 'Detected security events are communicated to and reviewed by the individuals responsible '
                                     'for the management of the security program and actions are taken, if necessary.',
          'subchapter': 'CC7.3: The entity evaluates security events to determine whether they could or have resulted in a '
                        'failure of the entity to meet its objectives (security incidents) and, if so, takes actions to '
                        'prevent or address such failures.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.3.3: Develops and Implements Procedures to Analyze Security Incidents',
          'requirement_description': 'Procedures are in place to analyze security incidents and determine system impact.',
          'subchapter': 'CC7.3: The entity evaluates security events to determine whether they could or have resulted in a '
                        'failure of the entity to meet its objectives (security incidents) and, if so, takes actions to '
                        'prevent or address such failures.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.3.4: Assesses the Impact on Personal Information',
          'requirement_description': 'Detected security events are evaluated to determine whether they could or did result in '
                                     'the unauthorized disclosure or use of personal information and whether there has been a '
                                     'failure to comply with applicable laws or regulations. ',
          'subchapter': 'CC7.3: The entity evaluates security events to determine whether they could or have resulted in a '
                        'failure of the entity to meet its objectives (security incidents) and, if so, takes actions to '
                        'prevent or address such failures.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.3.5: Determines Personal Information Used or Disclosed',
          'requirement_description': 'When an unauthorized use or disclosure of personal information has occurred, the '
                                     'affected information is identified and actions are taken to help prevent future '
                                     'recurrence and address control failures to support the achievement of entity objectives.',
          'subchapter': 'CC7.3: The entity evaluates security events to determine whether they could or have resulted in a '
                        'failure of the entity to meet its objectives (security incidents) and, if so, takes actions to '
                        'prevent or address such failures.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.3.6: Assesses the Impact on Confidential Information',
          'requirement_description': 'Detected security events are evaluated to determine whether they could or did result in '
                                     'the unauthorized disclosure or use of confidential information.',
          'subchapter': 'CC7.3: The entity evaluates security events to determine whether they could or have resulted in a '
                        'failure of the entity to meet its objectives (security incidents) and, if so, takes actions to '
                        'prevent or address such failures.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.3.7: Determines Confidential Information Used or Disclosed',
          'requirement_description': 'When an unauthorized use or disclosure of confidential information has occurred, the '
                                     'affected information is identified and actions are taken to help prevent future '
                                     'recurrence and address control failures to support the achievement of entity objectives.',
          'subchapter': 'CC7.3: The entity evaluates security events to determine whether they could or have resulted in a '
                        'failure of the entity to meet its objectives (security incidents) and, if so, takes actions to '
                        'prevent or address such failures.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': ['Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
                                   'Q-IRO-14: Does the organization maintain incident response contacts with applicable '
                                   'regulatory and law enforcement agencies? .',
                                   'Q-IRO-11.2: Does the organization establish a direct, cooperative relationship between the '
                                   "organization's incident response capability and external service providers?.",
                                   'Q-IRO-10.4: Does the organization provide cybersecurity and privacy incident information '
                                   'to the provider of the product or service and other organizations involved in the supply '
                                   'chain for systems or system components related to the incident?.',
                                   'Q-IRO-10.2: Does the organization report sensitive/regulated data incidents in a timely '
                                   'manner?.',
                                   'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .',
                                   'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.',
                                   'Q-IRO-01: Does the organization facilitate the implementation of incident response '
                                   'controls?.'],
          'objective_title': 'CC7.4.1: Assigns Roles and Responsibilities',
          'requirement_description': 'Roles and responsibilities for the design, implementation, maintenance, and execution of '
                                     'the incident-response program are assigned, including the use of external resources when '
                                     'necessary.',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.2: Contains and Responds to Security Incidents',
          'requirement_description': 'Procedures are in place to respond to and contain security incidents that actively '
                                     'threaten entity objectives.',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.3: Mitigates Ongoing Security Incidents',
          'requirement_description': 'Procedures are in place to mitigate the effects of ongoing security incidents.',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.4: Resolves Security Incidents',
          'requirement_description': 'Procedures are in place to resolve security incidents through closure of '
                                     'vulnerabilities, removal of unauthorized access, and other remediation actions.',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.5: Restores Operations',
          'requirement_description': 'Procedures are in place to restore data and business operations to an interim state that '
                                     'permits the achievement of entity objectives.',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.6: Develops and Implements Communication of Security Incidents',
          'requirement_description': 'Protocols for communicating, in a timely manner, information regarding security. '
                                     'incidents and actions taken to affected parties are developed and implemented to support '
                                     "the achievement of the entity's objectives.",
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.7: Obtains Understanding of Nature of Incident and Determines Containment Strategy',
          'requirement_description': 'An understanding of the nature (for example, the method by which the incident occurred '
                                     'and the affected system resources) and severity of the security incident is obtained to '
                                     'determine the appropriate response and containment strategy, including (1) a '
                                     'determination of the appropriate response time frame, and (2) the determination and '
                                     'execution of the containment approach. ',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.8: Remediates Identified Vulnerabilities',
          'requirement_description': 'Identified vulnerabilities are remediated through the development and execution of '
                                     'remediation activities.  ',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.9: Communicates Remediation Activities',
          'requirement_description': 'Remediation activities are documented and communicated in accordance with the incident '
                                     'response program. ',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.10: Evaluates the Effectiveness of Incident Resposes',
          'requirement_description': 'The design of incident response activities is evaluated for effectiveness on a periodic '
                                     'basis.  ',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.11: Periodically Evaluates Incidents',
          'requirement_description': 'Periodically, management reviews incidents related to security, availability, processing '
                                     'integrity, confidentiality, and privacy and identifies the need for system changes based '
                                     'on incident patterns and root causes.',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.12: Communicates Unauthorized Use and Disclosure',
          'requirement_description': 'Events that resulted in unauthorized use or disclosure of personal information are '
                                     'communicated to the data subjects, legal and regulatory authorities, and others as '
                                     'required.  ',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.13: Application of Sanctions',
          'requirement_description': 'The conduct of individuals and organizations operating under the authority of the entity '
                                     'and involved in the unauthorized use or disclosure of personal information is evaluated '
                                     'and, if appropriate, sanctioned in accordance with entity policies and legal and '
                                     'regulatory requirements.  ',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.4.14: Applies Breach Response Procedures',
          'requirement_description': 'Breach response procedures are defined and applied in the event of a confirmed privacy '
                                     'incident.',
          'subchapter': 'CC7.4: The entity responds to identified security incidents by executing a defined incident response '
                        'program to understand, contain, remediate, and communicate security incidents, as appropriate.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': ['Q-BCD-13: Does the organization protect backup and restoration hardware and software?.',
                                   'Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems '
                                   'to a known state after a disruption, compromise or failure? .',
                                   'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of '
                                   'the backup process, as well as the integrity and availability of the data? .',
                                   'Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.',
                                   'Q-BCD-06: Does the organization keep contingency plans current with business needs, '
                                   'technology changes and feedback from contingency plan testing activities?.',
                                   "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' "
                                   'activity every time the contingency plan is activated?.',
                                   'Q-BCD-04: Does the organization conduct tests and/or exercises to evaluate the contingency '
                                   "plan's effectiveness and the organization's readiness to execute the plan?.",
                                   'Q-BCD-02.3: Does the organization resume essential missions and business functions within '
                                   'an organization-defined time period of contingency plan activation? .',
                                   'Q-BCD-02.2: Does the organization plan for the continuance of essential missions and '
                                   'business functions with little or no loss of operational continuity and sustain that '
                                   'continuity until full system restoration at primary processing and/or storage sites?.',
                                   'Q-BCD-02.1: Does the organization plan for the resumption of all missions and business '
                                   "functions within Recovery Time Objectives (RTOs) of the contingency plan's activation?.",
                                   'Q-BCD-02: Does the organization identify and document the critical systems, applications '
                                   'and services that support essential missions and business functions?.',
                                   'Q-BCD-01: Does the organization facilitate the implementation of contingency planning '
                                   'controls?.'],
          'objective_title': 'CC7.5.1: Restores the Affected Environment',
          'requirement_description': 'The activities restore the affected environment to functional operation by rebuilding '
                                     'systems, updating software, installing patches, modifying access controls, and changing '
                                     'configurations, as needed. ',
          'subchapter': 'CC7.5: The entity identifies, develops, and implements activities to recover from identified security '
                        'incidents.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.5.2: Communicates Information About the Incident',
          'requirement_description': 'Communications about the nature of the incident, recovery actions taken, and activities '
                                     'required for the prevention of future security incidents are made to management and '
                                     'others as appropriate (internal and external).   ',
          'subchapter': 'CC7.5: The entity identifies, develops, and implements activities to recover from identified security '
                        'incidents.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.5.3: Determines Root Cause of the Incident',
          'requirement_description': 'The root cause of the incident is determined. ',
          'subchapter': 'CC7.5: The entity identifies, develops, and implements activities to recover from identified security '
                        'incidents.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.5.4: Implements Changes to Prevent and Detect Recurrences',
          'requirement_description': 'Additional architecture or changes to preventive and detective controls are implemented '
                                     'to prevent and detect incident recurrences in a timely manner.  ',
          'subchapter': 'CC7.5: The entity identifies, develops, and implements activities to recover from identified security '
                        'incidents.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.5.5: Improves Response and Recovery Procedures',
          'requirement_description': 'Lessons learned are analyzed, and the incident response plan and recovery procedures are '
                                     'improved. ',
          'subchapter': 'CC7.5: The entity identifies, develops, and implements activities to recover from identified security '
                        'incidents.'},
         {'chapter_title': 'SO: system operations',
          'conformity_questions': [],
          'objective_title': 'CC7.5.6: Implements Incident Recovery Plan Testing',
          'requirement_description': 'Incident recovery plan testing is performed on a periodic basis. The testing includes '
                                     '(1) development of testing scenarios based on threat likelihood and magnitude; (2) '
                                     'consideration of relevant system components from across the entity that can impair '
                                     'availability; (3) scenarios that consider the potential for the lack of availability of '
                                     'key personnel; and (4) revision of resilience posture and continuity plans based on test '
                                     'results.',
          'subchapter': 'CC7.5: The entity identifies, develops, and implements activities to recover from identified security '
                        'incidents.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': ['Q-PRM-07: Does the organization ensure changes to systems within the Secure Development '
                                   'Life Cycle (SDLC) are controlled through formal change control procedures? .',
                                   'Q-CFG-02.2: Does the organization use automated mechanisms to govern and report on '
                                   'baseline configurations of the systems? .',
                                   'Q-CFG-02.1: Does the organization review and update baseline configurations:  -  At least '
                                   'annually;  -  When required due to so; or  -  As part of system component installations '
                                   'and upgrades?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .',
                                   'Q-CHG-05: Does the organization ensure stakeholders are made aware of and understand the '
                                   'impact of proposed changes? .',
                                   'Q-CHG-02.2: Does the organization appropriately test and document proposed changes in a '
                                   'non-production environment before changes are implemented in a production environment?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CHG-01: Does the organization facilitate the implementation of a change management '
                                   'program?.'],
          'objective_title': 'CC8.1.1: Manages Changes Throughout the System Lifecycle',
          'requirement_description': 'A process for managing system changes throughout the lifecycle of the system and its '
                                     'components (infrastructure, data, software and manual and automated procedures) is used '
                                     'to support the achievement of entity objectives. ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.2: Authorizes Changes',
          'requirement_description': 'A process is in place to authorize system and architecture changes prior to design, '
                                     'development, or acquisition and configuration.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.3: Designs and Develops Changes',
          'requirement_description': 'A process is in place to design and develop system changes in a secure manner to support '
                                     'the achievement of entity objectives.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.4: Documents Changes',
          'requirement_description': 'A process is in place to document system changes to support ongoing maintenance of the '
                                     'system and to support internal and external users in performing their responsibilities. ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.5: Tracks System Changes',
          'requirement_description': 'A process is in place to track system changes prior to implementation. ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.6: Configures Software',
          'requirement_description': 'A process is in place to select, implement, maintain and monitor the configuration '
                                     'parameters used to control the functionality of developed and acquired software. ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.7: Tests System Changes',
          'requirement_description': 'A process is in place to test internally developed and acquired system changes prior to '
                                     'implementation into the production environment. Examples of testing may include unit, '
                                     'integration, regression, static and dynamic application source code, quality assurance, '
                                     'or automated testing (whether point in time or continuous).',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.8: Approves System Changes',
          'requirement_description': 'A process is in place to approve system changes prior to implementation.  ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.9: Deploys System Changes',
          'requirement_description': 'A process is in place to implement system changes with consideration of segregation of '
                                     'responsibilities (for example, restricting unilateral code development or testing and '
                                     'implementation by a single user) to prevent or detect unauthorized changes.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.10: Identifies and Evaluates System Changes',
          'requirement_description': 'Objectives affected by system changes are identified, and the ability of the modified '
                                     'system to support the achievement of the objectives is evaluated throughout the system '
                                     'development life cycle.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.11: Identifies Changes in Infrastructure, Data, Software, and Procedures Required to '
                             'Remediate Incidents',
          'requirement_description': 'Changes in infrastructure, data, software, and procedures required to remediate '
                                     'incidents are identified, and the change process is initiated upon identification. ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.12: Creates Baseline Configuration of IT Technology',
          'requirement_description': 'A baseline configuration of IT and control systems is created and maintained.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.13: Provides for Changes Necessary in Emergency Situations',
          'requirement_description': 'A process is in place for authorizing, designing, testing, approving and implementing '
                                     'changes necessary in emergency situations (that is, changes that need to be implemented '
                                     'in an urgent timeframe). ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.14: Protects Confidential Information',
          'requirement_description': 'The entity protects confidential information during system design, development, testing, '
                                     "implementation, and change processes to support the achievement of  the entity's "
                                     'objectives related to confidentiality.  ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.15: Protects Personal Information',
          'requirement_description': 'The entity protects personal information during system design, development, testing, '
                                     "implementation, and change processes to support the achievement of  the entity's "
                                     'objectives related to privacy.  ',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.16: Manages Patch Changes',
          'requirement_description': 'A process is in place to identify, evaluate, test, approve, and implement patches in a '
                                     'timely manner on infrastructure and software.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.17: Considers System Resilience',
          'requirement_description': 'The entity considers system resilience when designing its systems and tests resilience '
                                     "during development to help ensure the entity's ability to respond to, recover from, and "
                                     'resume operations through significant disruptions.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'CM: change management',
          'conformity_questions': [],
          'objective_title': 'CC8.1.18: Privacy by Design',
          'requirement_description': 'The entity considers privacy requirements in the design of its systems and processes and '
                                     'limits the collection and processing of personal information to what is necessary for '
                                     'the identified purpose.',
          'subchapter': 'CC8.1: The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, '
                        'and implements changes to infrastructure, data, software, and procedures to meet its objectives.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': ['Q-TPM-10: Does the organization control changes to services by suppliers, taking into '
                                   'account the criticality of business information, systems and processes that are in scope '
                                   'by the third-party?.',
                                   'Q-TPM-09: Does the organization address weaknesses or deficiencies in supply chain '
                                   'elements identified during independent or organizational assessments of such elements? .',
                                   'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .',
                                   'Q-TPM-07: Does the organization monitor for evidence of unauthorized exfiltration or '
                                   'disclosure of organizational information? .',
                                   'Q-TPM-06: Does the organization control personnel security requirements including security '
                                   'roles and responsibilities for third-party providers?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?.",
                                   'Q-TPM-04.4: Does the organization restrict the location of information processing/storage '
                                   'based on business requirements? .',
                                   'Q-TPM-03.3: Does the organization address identified weaknesses or deficiencies in the '
                                   'security of the supply chain .',
                                   'Q-TPM-03.2: Does the organization utilize security safeguards to limit harm from potential '
                                   "adversaries who identify and target the organization's supply chain? .",
                                   'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools '
                                   'and procurement methods for the purchase of unique systems, system components or '
                                   'services?.',
                                   'Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-BCD-07: Does the organization implement alternative or compensating controls to satisfy '
                                   'security functions when the primary means of implementing the security function is '
                                   'unavailable or compromised? .',
                                   'Q-BCD-01: Does the organization facilitate the implementation of contingency planning '
                                   'controls?.'],
          'objective_title': 'CC9.1.1: Considers Mitigation of Risks of Business Disruption',
          'requirement_description': 'Risk mitigation activities include the development of planned policies, procedures, '
                                     'communications, and alternative processing solutions to respond to, mitigate, and '
                                     'recover from incidents that disrupt business operations. Those resilience policies and '
                                     'procedures include monitoring processes and information and communications to support '
                                     "the achievement of the entity's objectives during response, mitigation, and recovery "
                                     'efforts.  ',
          'subchapter': 'CC9.1: The entity identifies, selects, and develops risk mitigation activities for risks arising from '
                        'potential business disruptions.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.1.2: Considers the Use of Insurance to Mitigate Financial Impact Risks',
          'requirement_description': 'The risk management activities consider the use of insurance to offset the financial '
                                     'impact of loss events that would otherwise impair the ability of the entity to support '
                                     'the achievement of its objectives.',
          'subchapter': 'CC9.1: The entity identifies, selects, and develops risk mitigation activities for risks arising from '
                        'potential business disruptions.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': ['Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.',
                                   'Q-RSK-09.1: Does the organization assess supply chain risks associated with systems, '
                                   'system components and services?.'],
          'objective_title': 'CC9.2.1: Establishes Requirements for Vendor and Business Partner Engagements',
          'requirement_description': 'The entity establishes specific requirements for vendor and business partner engagements '
                                     'that include (1) scope of services and product specifications, (2) roles and '
                                     'responsibilities, (3) compliance requirements, and (4) service levels. ',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.2: Assesses Vendor and Business Partner Risks',
          'requirement_description': 'The entity assesses, on a periodic basis, the risks that vendors and business partners '
                                     '(and those entities? vendors and business partners) represent to the achievement of the '
                                     "entity's objectives.  ",
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.3: Assigns Responsibility and Accountability for Managing Vendors and Business Partners',
          'requirement_description': 'The entity assigns responsibility and accountability for the management of risks and '
                                     'changes to services associated with vendors and business partners.',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.4: Establishes Communication Protocols for Vendors and Business Partners',
          'requirement_description': 'The entity establishes communication and resolution protocols for service or product '
                                     'issues related to vendors and business partners.  ',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.5: Establishes Exception Handling Procedures From Vendors and Business Partners',
          'requirement_description': 'The entity establishes exception handling procedures for service or product issues '
                                     'related to vendors and business partners. ',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.6: Assesses Vendor and Business Partner Performance',
          'requirement_description': 'The entity periodically assesses the vendors and business partners, as frequently as '
                                     'warranted, based on the risk associated with the vendor or business partner.',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.7: Implements Procedures for Addressing Issues Identified During Vendor and Business '
                             'Partner Assessments',
          'requirement_description': 'The entity implements procedures for addressing issues identified with vendor and '
                                     'business partner relationships.   ',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.8: Implements Procedures for Terminating Vendor and Business Partner Relationships',
          'requirement_description': 'The entity implements procedures for terminating vendor and business partner '
                                     'relationships. based on predefined considerations. Those procedures may include safe '
                                     'return of data and its removal from the vendor or business partner system.',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.9: Obtains Confidentiality Commitments From Vendors and Business Partners',
          'requirement_description': "The entity obtains confidentiality commitments that are consistent with the entity's "
                                     'confidentiality commitments and requirements from vendors and business partners who have '
                                     'access to confidential information. ',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.10: Assesses Compliance With Confidentiality Commitments of Vendors and Business Partners',
          'requirement_description': ' On a periodic and as-needed basis, the entity assesses compliance by vendors and '
                                     "business partners with the entity's confidentiality commitments and requirements. ",
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.11: Obtains Privacy Commitments From Vendors and Business Partners',
          'requirement_description': "The entity obtains privacy commitments, consistent with the entity's privacy commitments "
                                     'and requirements, from vendors and business partners who have access to personal '
                                     'information. ',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.12: Assesses Compliance With Privacy Commitments of Vendors and Business Partners',
          'requirement_description': ' On a periodic and as-needed basis, the entity assesses compliance by vendors and '
                                     "business partners with the entity's privacy commitments and requirements and takes "
                                     'corrective action as necessary.',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'RM: risk mitigation',
          'conformity_questions': [],
          'objective_title': 'CC9.2.13: Identifies Vulnerabilities',
          'requirement_description': 'The entity evaluates vulnerabilities arising from vendor and business partner '
                                     "relationships, including third-party access to the entity's IT systems and connections "
                                     'with third-party networks.',
          'subchapter': 'CC9.2: The entity assesses and manages risks associated with vendors and business partners.'},
         {'chapter_title': 'C: additional criteria for confidentiality',
          'conformity_questions': ['Q-DCH-03: Does the organization control and restrict access to digital and non-digital '
                                   'media to authorized individuals? .',
                                   'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with '
                                   'applicable statutory, regulatory and contractual requirements? .',
                                   'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.'],
          'objective_title': 'C1.1.1: Defines and Identifies Confidential information',
          'requirement_description': 'Procedures are in place to define, identify and designate confidential information when '
                                     'it is received or created.',
          'subchapter': "C1.1: The entity identifies and maintains confidential information to meet the entity's objectives "
                        'related to confidentiality.'},
         {'chapter_title': 'C: additional criteria for confidentiality',
          'conformity_questions': [],
          'objective_title': 'C1.1.2: Protects Confidential Information from Destruction',
          'requirement_description': 'Policies and Procedures are in place to protect confidential information from erasure or '
                                     'destruction during the specified retention period of the information. ',
          'subchapter': "C1.1: The entity identifies and maintains confidential information to meet the entity's objectives "
                        'related to confidentiality.'},
         {'chapter_title': 'C: additional criteria for confidentiality',
          'conformity_questions': [],
          'objective_title': 'C1.1.3: Retains Confidential Information',
          'requirement_description': 'Confidential information is retained for no longer than necessary to fulfill the '
                                     'identified purpose, unless a law or regulation specifically requires otherwise.',
          'subchapter': "C1.1: The entity identifies and maintains confidential information to meet the entity's objectives "
                        'related to confidentiality.'},
         {'chapter_title': 'C: additional criteria for confidentiality',
          'conformity_questions': ['Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for '
                                   'an organization-defined time period to fulfill the purpose(s) identified in the notice or '
                                   'as required by law;  -  Disposes of, destroys, erases, and/or anonymizes the PI, '
                                   'regardless of the method of storage; and  -  Uses organization-defined techniques or '
                                   'methods to ensure secure deletion or destruction of PD (including originals, copies and '
                                   'archived records)?.',
                                   'Q-DCH-21: Does the organization securely dispose of, destroy or erase information?.',
                                   'Q-MON-10: Does the organization retain event logs for a time period consistent with '
                                   'records retention requirements to provide support for after-the-fact investigations of '
                                   'security incidents and to meet statutory, regulatory and contractual retention '
                                   'requirements? .'],
          'objective_title': 'C1.2.1: Identifies Confidential Information for Destruction',
          'requirement_description': 'Procedures are in place to identify confidential information requiring destruction when '
                                     'the end of the retention period is reached. ',
          'subchapter': "C1.2: The entity disposes of confidential information to meet the entity's objectives related to "
                        'confidentiality.'},
         {'chapter_title': 'C: additional criteria for confidentiality',
          'conformity_questions': [],
          'objective_title': 'C1.2.2: Destroys Confidential Information',
          'requirement_description': 'Policies and Procedures are in place to automatically or manually erase or otherwise '
                                     'destroy confidential information that has been identified for destruction.',
          'subchapter': "C1.2: The entity disposes of confidential information to meet the entity's objectives related to "
                        'confidentiality.'},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': ['Q-TDA-06.1: Does the organization require the developer of the system, system component or '
                                   'service to perform a criticality analysis at organization-defined decision points in the '
                                   'Secure Development Life Cycle (SDLC)?.',
                                   'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
                                   'Q-OPS-03: Does the organization define supporting business processes and implement '
                                   'appropriate governance and service management to ensure appropriate planning, delivery and '
                                   "support of the organization's technology capabilities supporting business functions, "
                                   'workforce, and/or customers based on industry-recognized standards? .',
                                   'Q-RSK-10: Does the organization conduct a Data Protection Impact Assessment (DPIA) on '
                                   'systems, applications and services that store, process and/or transmit Personal Data (PD) '
                                   'to identify and remediate reasonably-expected risks?.',
                                   'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.'],
          'objective_title': 'PI1.1.1: Identifies Functional and Nonfunctional Requirements and Information Specifications',
          'requirement_description': 'The entity identifies and communicates functional and nonfunctional requirements related '
                                     'to system processing and information specifications required to support the use of '
                                     'products and services.',
          'subchapter': 'PI1.1: The entity obtains or generates, uses, and communicates relevant, quality information '
                        'regarding the objectives related to processing, including definitions of data processed and product '
                        'and service specifications, to support the use of products and services.'},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.1.2: Defines Data Necessary to Support a Product or Service',
          'requirement_description': 'When data is provided as part of a service or product or as part of a reporting '
                                     'obligation related to a product or service: \n'
                                     ' 1. The definition and purpose of the data is available to the users of the data. \n'
                                     ' 2. The definition of the data includes the following information:\n'
                                     '  a. The population of events or instances included in the set of data\n'
                                     '  b. The nature of each element (for example, field) of the set of data (that is, the '
                                     'event or instance to which the data element relates, for example, transaction price of a '
                                     'sale of XYZ Corporation stock for the last trade in that stock on a given day)\n'
                                     '  c. The sources of the data within the set\n'
                                     '  d. The units of measurement of data elements (for example, fields)\n'
                                     '  e. The accuracy/, correctness/, or precision of measurement\n'
                                     '  f. The uncertainty or confidence interval inherent in each data element and in the '
                                     'population of those elements\n'
                                     '  g. The datetime periods over which the set of data was measured or the period of time '
                                     'during which the events the data relates to occurred\n'
                                     '  h. In addition to the date or period of time, the factors that determined the '
                                     'inclusion and exclusion of items in the data elements and population\n'
                                     ' 3. The definition of the data is complete and accurate.\n'
                                     ' 4. The description of the data identifies any information that is necessary to '
                                     'understand each data element and the population in a manner consistent with its '
                                     'definition and intended purpose (metadata) that has not been included within the data.',
          'subchapter': 'PI1.1: The entity obtains or generates, uses, and communicates relevant, quality information '
                        'regarding the objectives related to processing, including definitions of data processed and product '
                        'and service specifications, to support the use of products and services.'},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': ['Q-TDA-18: Does the organization check the validity of information inputs? .',
                                   'Q-TDA-06: Does the organization develop applications based on secure coding principles? .'],
          'objective_title': 'PI1.2.1: Defines Characteristics of Processing Inputs',
          'requirement_description': 'The characteristics of processing inputs that are necessary to meet requirements are '
                                     'defined.',
          'subchapter': 'PI1.2: The entity implements policies and procedures over system inputs, including controls over '
                        "completeness and accuracy, to result in products, services, and reporting to meet the entity's "
                        'objectives.'},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.2.2: Evaluates Processing Inputs',
          'requirement_description': 'Processing inputs are evaluated for compliance with defined input requirements.',
          'subchapter': 'PI1.2: The entity implements policies and procedures over system inputs, including controls over '
                        "completeness and accuracy, to result in products, services, and reporting to meet the entity's "
                        'objectives.'},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.2.3: Creates and Maintains Records of System Input',
          'requirement_description': 'Records of system input activities are created and maintained completely and accurately '
                                     'in a timely manner.',
          'subchapter': 'PI1.2: The entity implements policies and procedures over system inputs, including controls over '
                        "completeness and accuracy, to result in products, services, and reporting to meet the entity's "
                        'objectives.'},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': ['Q-TDA-06: Does the organization develop applications based on secure coding principles? .'],
          'objective_title': 'PI1.3.1: Defines Processing Specifications',
          'requirement_description': 'The processing specifications that are necessary to meet product or service requirements '
                                     'are defined.',
          'subchapter': 'PI1.3: The entity implements policies and procedures over system processing to result in products, '
                        "services, and reporting to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.3.2: Defines Processing Activities',
          'requirement_description': 'Processing activities are defined to result in products or services that meet '
                                     'specifications.',
          'subchapter': 'PI1.3: The entity implements policies and procedures over system processing to result in products, '
                        "services, and reporting to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.3.3: Detects and Corrects Processing or Production Activity Errors',
          'requirement_description': 'Errors encountered in the processing or production activities are detected and corrected '
                                     'in a timely manner.',
          'subchapter': 'PI1.3: The entity implements policies and procedures over system processing to result in products, '
                        "services, and reporting to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.3.4: Records System Processing Activities',
          'requirement_description': 'System processing activities are recorded completely and accurately in a timely manner.',
          'subchapter': 'PI1.3: The entity implements policies and procedures over system processing to result in products, '
                        "services, and reporting to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.3.5: Processes Inputs',
          'requirement_description': 'Inputs are processed completely, accurately, and timely as authorized in accordance with '
                                     'defined processing activities. ',
          'subchapter': 'PI1.3: The entity implements policies and procedures over system processing to result in products, '
                        "services, and reporting to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': ['Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
                                   'Q-PES-12.2: Does the organization restrict access to printers and other system output '
                                   'devices to prevent unauthorized individuals from obtaining the output? .',
                                   'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized '
                                   'access, modification and deletion?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .'],
          'objective_title': 'PI1.4.1: Protects Output',
          'requirement_description': 'Output is protected when stored or delivered, or both, to prevent theft, destruction, '
                                     'corruption, or deterioration that would prevent output from meeting specifications. ',
          'subchapter': 'PI1.4: The entity implements policies and procedures to make available or deliver output completely, '
                        "accurately, and timely in accordance with specifications to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.4.2: Distributes Output Only to Intended Parties',
          'requirement_description': 'Output is distributed or made available only to intended parties.',
          'subchapter': 'PI1.4: The entity implements policies and procedures to make available or deliver output completely, '
                        "accurately, and timely in accordance with specifications to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.4.3: Distributes Output Completely and Accurately',
          'requirement_description': 'Procedures are in place to provide for the completeness, accuracy, and timeliness of '
                                     'distributed output. ',
          'subchapter': 'PI1.4: The entity implements policies and procedures to make available or deliver output completely, '
                        "accurately, and timely in accordance with specifications to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.4.4: Creates and Maintains Records of System Output Activities',
          'requirement_description': 'Records of system output activities are created and maintained completely and accurately '
                                     'in a timely manner.',
          'subchapter': 'PI1.4: The entity implements policies and procedures to make available or deliver output completely, '
                        "accurately, and timely in accordance with specifications to meet the entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': ['Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
                                   'Q-DCH-18: Does the organization retain media and data in accordance with applicable '
                                   'statutory, regulatory and contractual obligations? .',
                                   'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.',
                                   'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized '
                                   'access, modification and deletion?.'],
          'objective_title': 'PI1.5.1: Protects Stored Items',
          'requirement_description': 'Stored items are protected to prevent theft, corruption, destruction, or deterioration '
                                     'that would prevent output from meeting specifications.',
          'subchapter': 'PI1.5: The entity implements policies and procedures to store inputs, items in processing, and '
                        'outputs completely, accurately, and timely in accordance with system specifications to meet the '
                        "entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.5.2: Archives and Protects System Records',
          'requirement_description': 'System records are archived, and archives are protected against theft, corruption, '
                                     'destruction, or deterioration that would prevent them from being used. ',
          'subchapter': 'PI1.5: The entity implements policies and procedures to store inputs, items in processing, and '
                        'outputs completely, accurately, and timely in accordance with system specifications to meet the '
                        "entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.5.3: Stores Data Completely and Accurately',
          'requirement_description': 'Procedures are in place to provide for the complete, accurate, and timely storage of '
                                     'data. ',
          'subchapter': 'PI1.5: The entity implements policies and procedures to store inputs, items in processing, and '
                        'outputs completely, accurately, and timely in accordance with system specifications to meet the '
                        "entity's objectives."},
         {'chapter_title': 'PI: additional criteria for processing integrity',
          'conformity_questions': [],
          'objective_title': 'PI1.5.4: Creates and Maintains Records of Storage Activities',
          'requirement_description': 'Records of system storage activities are created and maintained completely and '
                                     'accurately in a timely manner.',
          'subchapter': 'PI1.5: The entity implements policies and procedures to store inputs, items in processing, and '
                        'outputs completely, accurately, and timely in accordance with system specifications to meet the '
                        "entity's objectives."},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.1.1: Measures Current Usage',
          'requirement_description': 'The use of the system components is measured to establish a baseline for capacity '
                                     'management and to use when monitoring and evaluating the risk of impaired availability '
                                     'due to capacity constraints. ',
          'subchapter': 'A1.1: The entity maintains, monitors, and evaluates current processing capacity and use of system '
                        'components (infrastructure, data, and software) to manage capacity demand and to enable the '
                        'implementation of additional capacity to help meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.1.2: Forecasts Capacity',
          'requirement_description': 'The expected average and peak use of system components is forecasted and compared to '
                                     'system capacity and associated tolerances. Forecasting considers system resilience and '
                                     'capacity in the event of the failure of system components that constrain capacity. ',
          'subchapter': 'A1.1: The entity maintains, monitors, and evaluates current processing capacity and use of system '
                        'components (infrastructure, data, and software) to manage capacity demand and to enable the '
                        'implementation of additional capacity to help meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.1.3: Makes Changes Based on Forecasts',
          'requirement_description': 'The system change management process is initiated when forecasted usage exceeds capacity '
                                     'tolerances. ',
          'subchapter': 'A1.1: The entity maintains, monitors, and evaluates current processing capacity and use of system '
                        'components (infrastructure, data, and software) to manage capacity demand and to enable the '
                        'implementation of additional capacity to help meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': ['Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?.",
                                   'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
                                   'Q-PES-15: Does the organization employ safeguards against Electromagnetic Pulse (EMP) '
                                   'damage for systems and system components?.',
                                   'Q-PES-13: Does the organization protect the system from information leakage due to '
                                   'electromagnetic signals emanations? .',
                                   'Q-PES-12: Does the organization locate system components within the facility to minimize '
                                   'potential damage from physical and environmental hazards and to minimize the opportunity '
                                   'for unauthorized access? .',
                                   'Q-PES-11: Does the organization utilize appropriate management, operational and technical '
                                   'controls at alternate work sites?.',
                                   'Q-PES-10: Does the organization isolate information processing facilities from points such '
                                   'as delivery and loading areas and other points to avoid unauthorized access? .',
                                   'Q-PES-09.1: Does the organization trigger an alarm or notification of temperature and '
                                   'humidity changes that be potentially harmful to personnel or equipment? .',
                                   'Q-PES-09: Does the organization maintain and monitor temperature and humidity levels '
                                   'within the facility?.',
                                   'Q-PES-08.2: Does the organization utilize fire suppression devices/systems that provide '
                                   'automatic notification of any activation to organizational personnel and emergency '
                                   'responders? .',
                                   'Q-PES-08.1: Does the organization utilize and maintain fire detection devices/systems that '
                                   'activate automatically and notify organizational personnel and emergency responders in the '
                                   'event of a fire? .',
                                   'Q-PES-08: Does the organization utilize and maintain fire suppression and detection '
                                   'devices/systems for the system that are supported by an independent energy. source? .',
                                   'Q-PES-07.5: Does the organization protect systems from damage resulting from water leakage '
                                   'by providing master shutoff valves that are accessible, working properly and known to key '
                                   'personnel? .',
                                   'Q-PES-07.4: Does the organization utilize and maintain automatic emergency lighting that '
                                   'activates in the event of a power outage or disruption and that covers emergency exits and '
                                   'evacuation routes within the facility? .',
                                   'Q-PES-07.3: Does the organization protect supply long-term alternate power, capable of '
                                   'maintaining minimally-required operational capability, in the event of an extended loss of '
                                   'the primary power source?.',
                                   'Q-PES-07.2: Does the organization shut off power in emergency situations by:  -  Placing '
                                   'emergency shutoff switches or devices in close proximity to systems or system components '
                                   'to facilitate safe and easy access for personnel; and  -  Protecting emergency power '
                                   'shutoff capability from unauthorized activation?.',
                                   'Q-PES-07.1: Does the organization utilize automatic voltage controls for critical system '
                                   'components? .',
                                   'Q-PES-07: Does the organization protect power equipment and power cabling for the system '
                                   'from damage and destruction? .',
                                   'Q-PES-01: Does the organization facilitate the operation of physical and environmental '
                                   'protection controls? .',
                                   'Q-BCD-12.2: Does the organization implement real-time or near-real-time failover '
                                   'capability to maintain availability of critical systems, applications and/or services?.',
                                   'Q-BCD-12.1: Does the organization utilize specialized backup mechanisms that will allow '
                                   'transaction recovery for transaction-based applications and services in accordance with '
                                   'Recovery Point Objectives (RPOs)?.',
                                   'Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems '
                                   'to a known state after a disruption, compromise or failure? .',
                                   'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized '
                                   'disclosure and/or modification of backup information/.',
                                   'Q-BCD-11.3: Does the organization reimage assets from configuration-controlled and '
                                   'integrity-protected images that represent a secure, operational state?.',
                                   'Q-BCD-11.2: Does the organization store backup copies of critical software and other '
                                   'security-related information in a separate facility or in a fire-rated container that is '
                                   'not collocated with the system being backed up?.',
                                   'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of '
                                   'the backup process, as well as the integrity and availability of the data? .',
                                   'Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.',
                                   'Q-BCD-10.1: Does the organization formalize primary and alternate telecommunications '
                                   'service agreements contain priority-of-service provisions that support availability '
                                   'requirements, including Recovery Time Objectives (RTOs)?.',
                                   'Q-BCD-10: Does the organization reduce the likelihood of a single point of failure with '
                                   'primary telecommunications services?.',
                                   'Q-BCD-09.3: Does the organization address priority-of-service provisions in alternate '
                                   'processing and storage sites that support availability requirements, including Recovery '
                                   'Time Objectives (RTOs)? .',
                                   'Q-BCD-09.2: Does the organization identify potential accessibility problems to the '
                                   'alternate processing site and possible mitigation actions, in the event of an area-wide '
                                   'disruption or disaster?.',
                                   'Q-BCD-09.1: Does the organization separate the alternate processing site from the primary '
                                   'processing site to reduce susceptibility to similar threats?.',
                                   'Q-BCD-09: Does the organization establish an alternate processing site that provides '
                                   'security measures equivalent to that of the primary site?.',
                                   'Q-BCD-08.2: Does the organization identify and mitigate potential accessibility problems '
                                   'to the alternate storage site in the event of an area-wide disruption or disaster?.',
                                   'Q-BCD-08.1: Does the organization separate the alternate storage site from the primary '
                                   'storage site to reduce susceptibility to similar threats?.',
                                   'Q-BCD-08: Does the organization establish an alternate storage site that includes both the '
                                   'assets and necessary agreements to permit the storage and recovery of system backup '
                                   'information? .'],
          'objective_title': 'A1.2.1: Identifies Environmental Threats',
          'requirement_description': 'As part of the risk assessment process, management identifies environmental threats that '
                                     'could impair the availability of the system, including threats resulting from adverse '
                                     'weather, failure of environmental control systems, electrical discharge, fire, and '
                                     'water.  ',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.2: Designs Detection Measures',
          'requirement_description': 'Detection measures are implemented to identify anomalies that could result from '
                                     'environmental threat events. ',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.3: Implements and Maintains Environmental Protection Mechanisms',
          'requirement_description': 'Management implements and maintains environmental protection mechanisms to prevent and '
                                     'mitigate against environmental events.  ',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.4: Implements Alerts to Analyze Anomalies',
          'requirement_description': 'Management implements alerts that are communicated to personnel for analysis to identify '
                                     'environmental threat events.',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.5: Responds to Environmental Threat Events',
          'requirement_description': 'Procedures are in place for responding to environmental threat events and for evaluating '
                                     'the effectiveness of those policies and procedures on a periodic basis. This includes '
                                     'automatic mitigation systems (for example, uninterruptable power system and generator '
                                     'back-up subsystem).',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.6: Communicates and Reviews Detected Environmental Threat Events',
          'requirement_description': 'Detected environmental threat events are communicated to and reviewed by the individuals '
                                     'responsible for the management of the system, and actions are taken, if necessary.',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.7: Determines Data Requiring Backup',
          'requirement_description': 'Data is evaluated to determine whether backup is required. ',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.8: Performs Data Backup',
          'requirement_description': 'Procedures are in place for backing up data, monitoring to detect back-up failures, and '
                                     'initiating corrective action when such failures occur. ',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.9: Addresses Offsite Storage',
          'requirement_description': 'Back-up data is stored in a location at a distance from its principal storage location '
                                     'sufficient that the likelihood of a security or environmental threat event affecting '
                                     'both sets of data is reduced to an appropriate level.  ',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.10: Implements Alternate Processing Infrastructure',
          'requirement_description': 'Measures are implemented for migrating processing to alternate infrastructure in the '
                                     'event normal processing infrastructure becomes unavailable.  Measures may include '
                                     'geographic separation, redundancy, and failover capabilities for components.',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.2.11: Considers Data Recoverability',
          'requirement_description': 'Management identifies threats to data recoverability (for example, ransomware attacks) '
                                     'that could impair the availability of the system and related data and implements '
                                     'mitigation procedures.',
          'subchapter': 'A1.2: The entity authorizes, designs, develops or acquires, implements, operates, approves, '
                        'maintains, and monitors environmental protections, software, data back-up processes, and recovery '
                        'infrastructure to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': ['Q-BCD-04: Does the organization conduct tests and/or exercises to evaluate the contingency '
                                   "plan's effectiveness and the organization's readiness to execute the plan?.",
                                   'Q-BCD-03.1: Does the organization incorporate simulated events into contingency training '
                                   'to facilitate effective response by personnel in crisis situations?.'],
          'objective_title': 'A1.3.1: Implements Business Continuity Plan Testing',
          'requirement_description': "Business continuity plan testing is performed on a periodic basis to test the entity's "
                                     'ability to respond to, recover from, and resume operations through significant '
                                     'disruptions. Testing includes (1) development of testing scenarios based on threat '
                                     'likelihood and magnitude; (2) consideration of system components from across the entity '
                                     'and vendors that can impair availability; (3) scenarios that consider the potential for '
                                     'the lack of availability of key personnel or vendors; and (4) revision of continuity '
                                     'plans and systems based on test results.',
          'subchapter': 'A1.3: The entity tests recovery plan procedures supporting system recovery to meet its objectives.'},
         {'chapter_title': 'A: additional criteria for availability',
          'conformity_questions': [],
          'objective_title': 'A1.3.2: Tests Integrity and Completeness of Back-Up Data',
          'requirement_description': 'The integrity and completeness of back-up information is tested on a periodic basis. ',
          'subchapter': 'A1.3: The entity tests recovery plan procedures supporting system recovery to meet its objectives.'},
         {'chapter_title': 'P: privacy criteria related to notice and commun',
          'conformity_questions': ['Q-PRI-02: Does the organization:  -  Make privacy notice(s) available to individuals upon '
                                   'first interacting with an organization and subsequently as necessary?  -  Ensure that '
                                   'privacy notices are clear and easy-to-understand, expressing information about Personal '
                                   'Data (PD) processing in plain language?.',
                                   'Q-PRI-01.3: Does the organization:   -  Ensure that the public has access to information '
                                   'about organizational privacy activities and can communicate with its Chief Privacy Officer '
                                   '(CPO) or similar role;  -  Ensure that organizational privacy practices are publicly '
                                   'available through organizational websites or otherwise; and  -  Utilize publicly facing '
                                   'email addresses and/or phone lines to enable the public to provide feedback and/or direct '
                                   'questions to privacy offices regarding privacy practices?.',
                                   'Q-PRI-01.2: Does the organization provide additional formal notice to individuals from '
                                   'whom the information is being collected that includes:  -  Notice of the authority of '
                                   'organizations to collect Personal Data (PD);   -  Whether providing Personal Data (PD) is '
                                   'mandatory or optional;   -  The principal purpose or purposes for which the Personal Data '
                                   '(PD) is to be used;   -  The intended disclosures or routine uses of the information; '
                                   'and   -  The consequences of not providing all or some portion of the information '
                                   'requested?.'],
          'objective_title': 'P1.1.1: Communicates to Data Subjects',
          'requirement_description': 'Notice is provided to data subjects regarding the following: \n'
                                     ' 1.\tPurpose for collecting personal information\n'
                                     ' 2.\t Choice and consent\n'
                                     ' 3.\tTypes of personal information collected\n'
                                     ' 4.\tMethods of collection (for example, use of cookies or other tracking techniques)\n'
                                     ' 5.\tUse, retention, and disposal\n'
                                     ' 6.\tAccess\n'
                                     ' 7.\tDisclosure to third parties\n'
                                     ' 8.\tSecurity for privacy\n'
                                     ' 9.\tQuality, including data subjects? responsibilities for quality\n'
                                     ' 10.\tMonitoring and enforcement\n'
                                     ' If personal information is collected from sources other than the individual, such '
                                     'sources are described in the privacy notice.',
          'subchapter': "P1.1: The entity provides notice to data subjects about its privacy practices to meet the entity's "
                        'objectives related to privacy. The notice is updated and communicated to data subjects in a timely '
                        "manner for changes to the entity's privacy practices, including changes in the use of personal "
                        "information, to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to notice and commun',
          'conformity_questions': [],
          'objective_title': 'P1.1.2: Provides Notice to Data Subjects',
          'requirement_description': 'Notice is provided to data subjects (1) at or before the time personal information is '
                                     'collected or as soon as practical thereafter, (2) at or before the entity changes its '
                                     'privacy notice or as soon as practical thereafter, or (3) before personal information is '
                                     'used for new purposes not previously identified.',
          'subchapter': "P1.1: The entity provides notice to data subjects about its privacy practices to meet the entity's "
                        'objectives related to privacy. The notice is updated and communicated to data subjects in a timely '
                        "manner for changes to the entity's privacy practices, including changes in the use of personal "
                        "information, to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to notice and commun',
          'conformity_questions': [],
          'objective_title': 'P1.1.3: Covers Entities and Activities in Notice',
          'requirement_description': 'An objective description of the entities and activities covered is included in the '
                                     "entity's privacy notice.",
          'subchapter': "P1.1: The entity provides notice to data subjects about its privacy practices to meet the entity's "
                        'objectives related to privacy. The notice is updated and communicated to data subjects in a timely '
                        "manner for changes to the entity's privacy practices, including changes in the use of personal "
                        "information, to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to notice and commun',
          'conformity_questions': [],
          'objective_title': 'P1.1.4: Uses Clear Language and Presents a Current Privacy Notice in a Location Easily Found by '
                             'Data Subjects',
          'requirement_description': "The entity's privacy notice is current, dated, uses clear language, and is in a location "
                                     'that can be easily found by data subjects.',
          'subchapter': "P1.1: The entity provides notice to data subjects about its privacy practices to meet the entity's "
                        'objectives related to privacy. The notice is updated and communicated to data subjects in a timely '
                        "manner for changes to the entity's privacy practices, including changes in the use of personal "
                        "information, to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to notice and commun',
          'conformity_questions': [],
          'objective_title': 'P1.1.5: Reviews the Privacy Notice',
          'requirement_description': 'A process is defined to periodically review the content of the privacy notice and to '
                                     'implement any identified updates.',
          'subchapter': "P1.1: The entity provides notice to data subjects about its privacy practices to meet the entity's "
                        'objectives related to privacy. The notice is updated and communicated to data subjects in a timely '
                        "manner for changes to the entity's privacy practices, including changes in the use of personal "
                        "information, to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to notice and commun',
          'conformity_questions': [],
          'objective_title': 'P1.1.6: Communicates Changes to Notice',
          'requirement_description': 'Data subjects are informed when changes are made to the privacy notice and the nature of '
                                     'such changes.',
          'subchapter': "P1.1: The entity provides notice to data subjects about its privacy practices to meet the entity's "
                        'objectives related to privacy. The notice is updated and communicated to data subjects in a timely '
                        "manner for changes to the entity's privacy practices, including changes in the use of personal "
                        "information, to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to notice and commun',
          'conformity_questions': [],
          'objective_title': 'P1.1.7: Retains Prior Notices',
          'requirement_description': 'Prior versions of the privacy notice are retained in accordance with internal '
                                     'requirements to document prior communications.',
          'subchapter': "P1.1: The entity provides notice to data subjects about its privacy practices to meet the entity's "
                        'objectives related to privacy. The notice is updated and communicated to data subjects in a timely '
                        "manner for changes to the entity's privacy practices, including changes in the use of personal "
                        "information, to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to choice and consen',
          'conformity_questions': ['Q-PRI-03.2: Does the organization present authorizations to process Personal Data (PD) in '
                                   'conjunction with the data action, when: -  The original circumstances under which an '
                                   'individual gave consent have changed; or -  A significant amount of time has passed since '
                                   'an individual gave consent?.',
                                   'Q-PRI-03: Does the organization authorize the processing of their Personal Data (PD) prior '
                                   'to its collection that:  -  Uses plain language and provide examples to illustrate the '
                                   'potential privacy risks of the authorization; and  -  Provides a means for users to '
                                   'decline the authorization?.'],
          'objective_title': 'P2.1.1: Communicates to Data Subjects',
          'requirement_description': 'Data subjects are informed (a) about the choices available to them with respect to the '
                                     'collection, use, and disclosure of personal information and (b) that implicit or '
                                     'explicit consent is required to collect, use, and disclose personal information, unless '
                                     'a law or regulation specifically requires or allows otherwise.',
          'subchapter': 'P2.1: The entity communicates choices available regarding the collection, use, retention, disclosure, '
                        'and disposal of personal information to the data subjects and the consequences, if any, of each '
                        'choice. Explicit consent for the collection, use, retention, disclosure, and disposal of personal '
                        'information is obtained from data subjects or other authorized persons, if required. Such consent is '
                        "obtained only for the intended purpose of the information to meet the entity's objectives related to "
                        "privacy. The entity's basis for determining implicit consent for the collection, use, retention, "
                        'disclosure, and disposal of personal information is documented.'},
         {'chapter_title': 'P: privacy criteria related to choice and consen',
          'conformity_questions': [],
          'objective_title': 'P2.1.2: Communicates Consequences of Denying or Withdrawing Consent',
          'requirement_description': 'When personal information is collected, data subjects are informed of the consequences '
                                     'of refusing to provide personal information or denying or withdrawing consent to use '
                                     'personal information for purposes identified in the notice.',
          'subchapter': 'P2.1: The entity communicates choices available regarding the collection, use, retention, disclosure, '
                        'and disposal of personal information to the data subjects and the consequences, if any, of each '
                        'choice. Explicit consent for the collection, use, retention, disclosure, and disposal of personal '
                        'information is obtained from data subjects or other authorized persons, if required. Such consent is '
                        "obtained only for the intended purpose of the information to meet the entity's objectives related to "
                        "privacy. The entity's basis for determining implicit consent for the collection, use, retention, "
                        'disclosure, and disposal of personal information is documented.'},
         {'chapter_title': 'P: privacy criteria related to choice and consen',
          'conformity_questions': [],
          'objective_title': 'P2.1.3: Obtains Implicit or Explicit Consent',
          'requirement_description': 'Implicit or explicit consent is obtained from data subjects at or before the time '
                                     'personal information is collected or soon thereafter. The individual?s preferences '
                                     'expressed in his or her consent are confirmed and implemented.',
          'subchapter': 'P2.1: The entity communicates choices available regarding the collection, use, retention, disclosure, '
                        'and disposal of personal information to the data subjects and the consequences, if any, of each '
                        'choice. Explicit consent for the collection, use, retention, disclosure, and disposal of personal '
                        'information is obtained from data subjects or other authorized persons, if required. Such consent is '
                        "obtained only for the intended purpose of the information to meet the entity's objectives related to "
                        "privacy. The entity's basis for determining implicit consent for the collection, use, retention, "
                        'disclosure, and disposal of personal information is documented.'},
         {'chapter_title': 'P: privacy criteria related to choice and consen',
          'conformity_questions': [],
          'objective_title': 'P2.1.4: Documents and Obtains Consent for New Purpose and Uses',
          'requirement_description': 'If information that was previously collected is to be used for purposes not previously '
                                     'identified in the privacy notice, the new purpose is documented, the data subject is '
                                     'notified, and implicit or explicit consent is obtained prior to such new use or purpose.',
          'subchapter': 'P2.1: The entity communicates choices available regarding the collection, use, retention, disclosure, '
                        'and disposal of personal information to the data subjects and the consequences, if any, of each '
                        'choice. Explicit consent for the collection, use, retention, disclosure, and disposal of personal '
                        'information is obtained from data subjects or other authorized persons, if required. Such consent is '
                        "obtained only for the intended purpose of the information to meet the entity's objectives related to "
                        "privacy. The entity's basis for determining implicit consent for the collection, use, retention, "
                        'disclosure, and disposal of personal information is documented.'},
         {'chapter_title': 'P: privacy criteria related to choice and consen',
          'conformity_questions': [],
          'objective_title': 'P2.1.5: Obtains Explicit Consent for Sensitive Information',
          'requirement_description': 'Explicit consent is obtained directly from the data subject when sensitive personal '
                                     'information is collected, used, or disclosed, unless a law or regulation specifically '
                                     'requires otherwise.',
          'subchapter': 'P2.1: The entity communicates choices available regarding the collection, use, retention, disclosure, '
                        'and disposal of personal information to the data subjects and the consequences, if any, of each '
                        'choice. Explicit consent for the collection, use, retention, disclosure, and disposal of personal '
                        'information is obtained from data subjects or other authorized persons, if required. Such consent is '
                        "obtained only for the intended purpose of the information to meet the entity's objectives related to "
                        "privacy. The entity's basis for determining implicit consent for the collection, use, retention, "
                        'disclosure, and disposal of personal information is documented.'},
         {'chapter_title': 'P: privacy criteria related to choice and consen',
          'conformity_questions': [],
          'objective_title': 'P2.1.6: Obtains Consent for Data Transfers',
          'requirement_description': 'Consent is obtained before personal information is transferred to or from an '
                                     "individual's device. ",
          'subchapter': 'P2.1: The entity communicates choices available regarding the collection, use, retention, disclosure, '
                        'and disposal of personal information to the data subjects and the consequences, if any, of each '
                        'choice. Explicit consent for the collection, use, retention, disclosure, and disposal of personal '
                        'information is obtained from data subjects or other authorized persons, if required. Such consent is '
                        "obtained only for the intended purpose of the information to meet the entity's objectives related to "
                        "privacy. The entity's basis for determining implicit consent for the collection, use, retention, "
                        'disclosure, and disposal of personal information is documented.'},
         {'chapter_title': 'P: privacy criteria related to collection',
          'conformity_questions': [],
          'objective_title': 'P3.1.1: Limits the Collection of Personal Information',
          'requirement_description': 'The collection of personal information is limited to that necessary to support the '
                                     "achievement of the entity's objectives.",
          'subchapter': "P3.1: Personal information is collected consistent with the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to collection',
          'conformity_questions': [],
          'objective_title': 'P3.1.2: Collects Information by Fair and Lawful Means',
          'requirement_description': 'Methods of collecting personal information are reviewed by management before they are '
                                     'implemented to confirm that personal information is obtained (a) fairly, without '
                                     'intimidation or deception, and (b) lawfully, adhering to all relevant rules of law, '
                                     'whether derived from statute or common law, relating to the collection of personal '
                                     'information.',
          'subchapter': "P3.1: Personal information is collected consistent with the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to collection',
          'conformity_questions': [],
          'objective_title': 'P3.1.3: Collects Information From Reliable Sources',
          'requirement_description': 'Management confirms that third parties from whom personal information is collected (that '
                                     'is, sources other than the individual) are reliable sources that collect information '
                                     'fairly and lawfully.',
          'subchapter': "P3.1: Personal information is collected consistent with the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to collection',
          'conformity_questions': [],
          'objective_title': 'P3.1.4: Informs Data Subjects When Additional Information Is Acquired',
          'requirement_description': 'Data subjects are informed if the entity develops or acquires additional information '
                                     'about them for its use. ',
          'subchapter': "P3.1: Personal information is collected consistent with the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to collection',
          'conformity_questions': ['Q-PRI-03.2: Does the organization present authorizations to process Personal Data (PD) in '
                                   'conjunction with the data action, when: -  The original circumstances under which an '
                                   'individual gave consent have changed; or -  A significant amount of time has passed since '
                                   'an individual gave consent?.',
                                   'Q-PRI-03: Does the organization authorize the processing of their Personal Data (PD) prior '
                                   'to its collection that:  -  Uses plain language and provide examples to illustrate the '
                                   'potential privacy risks of the authorization; and  -  Provides a means for users to '
                                   'decline the authorization?.'],
          'objective_title': 'P3.2.1: Informs Data Subjects of Consequences of Failure to Provide Consent',
          'requirement_description': 'Data subjects are informed of the consequences of failing to provide the entity with '
                                     'explicit consent.',
          'subchapter': 'P3.2: For information requiring explicit consent, the entity communicates the need for such consent, '
                        'as well as the consequences of a failure to provide consent for the request for personal information, '
                        "and obtains the consent prior to the collection of the information to meet the entity's objectives "
                        'related to privacy.'},
         {'chapter_title': 'P: privacy criteria related to collection',
          'conformity_questions': [],
          'objective_title': 'P3.2.2: Documents Explicit Consent to Retain Informatation',
          'requirement_description': ' Documentation of explicit consent for the collection, use, or disclosure of sensitive '
                                     'personal information is retained to support the achievement of entity objectives related '
                                     'to privacy. ',
          'subchapter': 'P3.2: For information requiring explicit consent, the entity communicates the need for such consent, '
                        'as well as the consequences of a failure to provide consent for the request for personal information, '
                        "and obtains the consent prior to the collection of the information to meet the entity's objectives "
                        'related to privacy.'},
         {'chapter_title': 'P: privacy criteria related to use, retention, a',
          'conformity_questions': ['Q-PRI-05.4: Does the organization restrict the use of Personal Data (PD) to only the '
                                   'authorized purpose(s) consistent with applicable laws, regulations and in privacy notices? '
                                   '.',
                                   'Q-PRI-05.1: Does the organization address the use of Personal Data (PD) for internal '
                                   'testing, training and research that:  -  Takes measures to limit or minimize the amount of '
                                   'PD used for internal testing, training and research purposes; and  -  Authorizes the use '
                                   'of PD when such information is required for internal testing, training and research?.'],
          'objective_title': 'P4.1.1: Uses Personal Information for Intended Purposes',
          'requirement_description': 'Personal information is used only for the intended purposes for which it was collected '
                                     'and only when implicit or explicit consent has been obtained unless a law or regulation '
                                     'specifically requires otherwise.',
          'subchapter': "P4.1: The entity limits the use of personal information to the purposes identified in the entity's "
                        'objectives related to privacy.'},
         {'chapter_title': 'P: privacy criteria related to use, retention, a',
          'conformity_questions': ['Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for '
                                   'an organization-defined time period to fulfill the purpose(s) identified in the notice or '
                                   'as required by law;  -  Disposes of, destroys, erases, and/or anonymizes the PI, '
                                   'regardless of the method of storage; and  -  Uses organization-defined techniques or '
                                   'methods to ensure secure deletion or destruction of PD (including originals, copies and '
                                   'archived records)?.'],
          'objective_title': 'P4.2.1: Retains Personal Information',
          'requirement_description': 'Personal information is retained for no longer than necessary to fulfill the stated '
                                     'purposes, unless a law or regulation specifically requires otherwise.',
          'subchapter': "P4.2: The entity retains personal information consistent with the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to use, retention, a',
          'conformity_questions': [],
          'objective_title': 'P4.2.2: Protects Personal Information',
          'requirement_description': 'Policies and procedures have been implemented to protect personal information from '
                                     'erasure or destruction during the specified retention period of the information. ',
          'subchapter': "P4.2: The entity retains personal information consistent with the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to use, retention, a',
          'conformity_questions': ['Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for '
                                   'an organization-defined time period to fulfill the purpose(s) identified in the notice or '
                                   'as required by law;  -  Disposes of, destroys, erases, and/or anonymizes the PI, '
                                   'regardless of the method of storage; and  -  Uses organization-defined techniques or '
                                   'methods to ensure secure deletion or destruction of PD (including originals, copies and '
                                   'archived records)?.',
                                   'Q-DCH-21: Does the organization securely dispose of, destroy or erase information?.',
                                   'Q-DCH-09.3: Does the organization facilitate the sanitization of Personal Data (PD)?.'],
          'objective_title': 'P4.3.1: Captures, Identifies, and Flags Requests for Deletion',
          'requirement_description': 'Requests for deletion of personal information are captured, and information related to '
                                     'the requests is identified and flagged for destruction to support the achievement of the '
                                     "entity's objectives related to privacy. ",
          'subchapter': "P4.3: The entity'securely disposes of personal information to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to use, retention, a',
          'conformity_questions': [],
          'objective_title': 'P4.3.2: Disposes of, Destroys, and Redacts Personal Information',
          'requirement_description': 'Personal information no longer retained is anonymized, disposed of, or destroyed in a '
                                     'manner that prevents loss, theft, misuse, or unauthorized access.',
          'subchapter': "P4.3: The entity'securely disposes of personal information to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to use, retention, a',
          'conformity_questions': [],
          'objective_title': 'P4.3.3: Destroys Personal Information',
          'requirement_description': 'Policies and procedures are implemented to erase or otherwise destroy personal '
                                     'information that has been identified for destruction.',
          'subchapter': "P4.3: The entity'securely disposes of personal information to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': ['Q-PRI-06.1: Does the organization establish and implement a process for:  -  Individuals '
                                   'to have inaccurate Personal Data (PD) maintained by the organization corrected or amended; '
                                   'and  -  Disseminating corrections or amendments of PD to other authorized users of the '
                                   'PI?.',
                                   'Q-DCH-22.1: Does the organization utilize technical controls to correct Personal Data (PD) '
                                   'that is inaccurate or outdated, incorrectly determined regarding impact, or incorrectly '
                                   'de-identified?.'],
          'objective_title': "P5.1.1: Authenticates Data Subjects' Identity",
          'requirement_description': 'The identity of data subjects who request access to their personal information is '
                                     'authenticated before they are given access to that information.',
          'subchapter': 'P5.1: The entity grants identified and authenticated data subjects the ability to access their stored '
                        'personal information for review and, upon request, provides physical or electronic copies of that '
                        "information to data subjects to meet the entity's objectives related to privacy. If access is denied, "
                        'data subjects are informed of the denial and reason for such denial, as required, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': [],
          'objective_title': 'P5.1.2: Permits Data Subjects Access to Their Personal Information',
          'requirement_description': 'Data subjects are able to determine whether the entity maintains personal information '
                                     'about them and, upon request, may obtain access to their personal information.',
          'subchapter': 'P5.1: The entity grants identified and authenticated data subjects the ability to access their stored '
                        'personal information for review and, upon request, provides physical or electronic copies of that '
                        "information to data subjects to meet the entity's objectives related to privacy. If access is denied, "
                        'data subjects are informed of the denial and reason for such denial, as required, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': [],
          'objective_title': 'P5.1.3: Provides Understandable Personal Information Within Reasonable Time',
          'requirement_description': 'Personal information is provided to data subjects in an understandable form, in a '
                                     'reasonable time frame, and at a reasonable cost, if any.',
          'subchapter': 'P5.1: The entity grants identified and authenticated data subjects the ability to access their stored '
                        'personal information for review and, upon request, provides physical or electronic copies of that '
                        "information to data subjects to meet the entity's objectives related to privacy. If access is denied, "
                        'data subjects are informed of the denial and reason for such denial, as required, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': [],
          'objective_title': 'P5.1.4: Informs Data Subjects If Access Is Denied',
          'requirement_description': 'When data subjects are denied access to their personal information, the entity informs '
                                     'them of the denial and the reason for the denial in a timely manner, unless prohibited '
                                     'by law or regulation.',
          'subchapter': 'P5.1: The entity grants identified and authenticated data subjects the ability to access their stored '
                        'personal information for review and, upon request, provides physical or electronic copies of that '
                        "information to data subjects to meet the entity's objectives related to privacy. If access is denied, "
                        'data subjects are informed of the denial and reason for such denial, as required, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': [],
          'objective_title': 'P5.1.5: Responds to Data Controller Requests',
          'requirement_description': 'The entity has a process to respond to data subject requests received from data '
                                     'controllers in accordance with service agreements and privacy objectives. Such process '
                                     'may include authentication of the request, permitting access where appropriate, '
                                     'responding within a reasonable time, and notification if the request is denied.',
          'subchapter': 'P5.1: The entity grants identified and authenticated data subjects the ability to access their stored '
                        'personal information for review and, upon request, provides physical or electronic copies of that '
                        "information to data subjects to meet the entity's objectives related to privacy. If access is denied, "
                        'data subjects are informed of the denial and reason for such denial, as required, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': ['Q-PRI-12: Does the organization develop processes to identify and record the method under '
                                   'which Personal Data (PD) is updated and the frequency that such updates occur?.'],
          'objective_title': 'P5.2.1: Communicates Denial of Access Requests',
          'requirement_description': 'Data subjects are informed, in writing, of the reason a request for access to their '
                                     "personal information was denied, the source of the entity's legal right to deny such "
                                     "access, if applicable, and the individual's right, if any, to challenge such denial, as "
                                     'specifically permitted or required by law or regulation. ',
          'subchapter': 'P5.2: The entity corrects, amends, or appends personal information based on information provided by '
                        'data subjects and communicates such information to third parties, as committed or required, to meet '
                        "the entity's objectives related to privacy. If a request for correction is denied, data subjects are "
                        "informed of the denial and reason for such denial to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': [],
          'objective_title': 'P5.2.2: Permits Data Subjects to Update or Correct Personal Information',
          'requirement_description': 'Data subjects are able to update or correct personal information held by the entity. The '
                                     'entity provides such updated or corrected communicates updates, corrections, and '
                                     'deletion requests  to third parties that were previously provided with the data '
                                     "subject's personal information consistent with the entity's objective related to "
                                     'privacy.',
          'subchapter': 'P5.2: The entity corrects, amends, or appends personal information based on information provided by '
                        'data subjects and communicates such information to third parties, as committed or required, to meet '
                        "the entity's objectives related to privacy. If a request for correction is denied, data subjects are "
                        "informed of the denial and reason for such denial to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': [],
          'objective_title': 'P5.2.3: Communicates Denial of Correction Requests',
          'requirement_description': 'Data subjects are informed, in writing, about the reason a request for correction of '
                                     'personal information was denied and how they may appeal.',
          'subchapter': 'P5.2: The entity corrects, amends, or appends personal information based on information provided by '
                        'data subjects and communicates such information to third parties, as committed or required, to meet '
                        "the entity's objectives related to privacy. If a request for correction is denied, data subjects are "
                        "informed of the denial and reason for such denial to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to access',
          'conformity_questions': [],
          'objective_title': 'P5.2.4: Responds to Data Controller Requests',
          'requirement_description': 'The entity has a process to respond to data controllers update requests, including '
                                     'updates to personal information and denial of requests, in accordance with service '
                                     "agreements to support the achievement of the entity's objectives related to privacy.",
          'subchapter': 'P5.2: The entity corrects, amends, or appends personal information based on information provided by '
                        'data subjects and communicates such information to third parties, as committed or required, to meet '
                        "the entity's objectives related to privacy. If a request for correction is denied, data subjects are "
                        "informed of the denial and reason for such denial to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': ['Q-PRI-07: Does the organization discloses Personal Data (PD) to third-parties only for the '
                                   'purposes identified in the privacy notice and with the implicit or explicit consent of the '
                                   'individual? .'],
          'objective_title': 'P6.1.1: Communicates Privacy Policies to Third Parties',
          'requirement_description': 'Privacy policies or other specific instructions or requirements for handling personal '
                                     'information are communicated to third parties to whom personal information is disclosed.',
          'subchapter': 'P6.1: The entity discloses personal information to third parties with the explicit consent of data '
                        "subjects, and such consent is obtained prior to disclosure to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.1.2: Discloses Personal Information Only When Appropriate',
          'requirement_description': 'Personal information is disclosed to third parties only for the purposes for which it '
                                     'was collected or created and only when implicit or explicit consent has been obtained '
                                     'from the data subject, unless a law or regulation specifically requires otherwise.',
          'subchapter': 'P6.1: The entity discloses personal information to third parties with the explicit consent of data '
                        "subjects, and such consent is obtained prior to disclosure to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.1.3: Discloses Personal Information Only to Appropriate Third Parties',
          'requirement_description': 'Personal information is disclosed only to third parties who have agreements with the '
                                     'entity to protect personal information in a manner consistent with the relevant aspects '
                                     "of the entity's privacy notice or other specific instructions or requirements. ",
          'subchapter': 'P6.1: The entity discloses personal information to third parties with the explicit consent of data '
                        "subjects, and such consent is obtained prior to disclosure to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.1.4: Discloses Information to Third Parties for New Purposes and Uses',
          'requirement_description': 'Personal information is disclosed to third parties for new purposes or uses only with '
                                     'the prior implicit or explicit consent of data subjects.',
          'subchapter': 'P6.1: The entity discloses personal information to third parties with the explicit consent of data '
                        "subjects, and such consent is obtained prior to disclosure to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': ['Q-PRI-14.1: Does the organization develop and maintain an accounting of disclosures of '
                                   'Personal Data (PD) held by the organization and make the accounting of disclosures '
                                   'available to the person named in the record, upon request?.'],
          'objective_title': 'P6.2.1: Creates and Retains Record of Authorized Disclosures',
          'requirement_description': 'The entity creates and maintains a record of authorized disclosures of personal '
                                     'information that is complete, accurate, and timely. ',
          'subchapter': 'P6.2: The entity creates and retains a complete, accurate, and timely record of authorized '
                        "disclosures of personal information to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': ['Q-PRI-14.1: Does the organization develop and maintain an accounting of disclosures of '
                                   'Personal Data (PD) held by the organization and make the accounting of disclosures '
                                   'available to the person named in the record, upon request?.',
                                   'Q-IRO-12: Does the organization respond to sensitive information spills?.',
                                   'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-IRO-04.1: Does the organization address data breaches, or other incidents involving the '
                                   'unauthorized disclosure of sensitive or regulated data, according to applicable laws, '
                                   'regulations and contractual obligations? .'],
          'objective_title': 'P6.3.1: Creates and Retains Record of Detected or Reported Unauthorized Disclosures',
          'requirement_description': 'The entity creates and maintains a record of detected or reported unauthorized '
                                     'disclosures of personal information that is complete, accurate, and timely.',
          'subchapter': 'P6.3: The entity creates and retains a complete, accurate, and timely record of detected or reported '
                        "unauthorized disclosures (including breaches) of personal information to meet the entity's objectives "
                        'related to privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': ['Q-PRI-07.1: Does the organization includes privacy requirements in contracts and other '
                                   'acquisition-related documents that establish privacy roles and responsibilities for '
                                   'contractors and service providers? .'],
          'objective_title': 'P6.4.1: Evaluates Third-Party Compliance With Privacy Commitments',
          'requirement_description': 'The entity has procedures in place to evaluate whether third parties have effective '
                                     'controls to meet the terms of the agreement, instructions, or requirements.',
          'subchapter': 'P6.4: The entity obtains privacy commitments from vendors and other third parties who have access to '
                        "personal information to meet the entity's objectives related to privacy. The entity assesses those "
                        'parties? compliance on a periodic and as-needed basis and takes corrective action, if necessary.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.4.2: Remediates Misuse of Personal Information by a Third Party',
          'requirement_description': 'The entity takes remedial action in response to misuse of personal information by a '
                                     'third party to whom the entity has transferred such information.',
          'subchapter': 'P6.4: The entity obtains privacy commitments from vendors and other third parties who have access to '
                        "personal information to meet the entity's objectives related to privacy. The entity assesses those "
                        'parties? compliance on a periodic and as-needed basis and takes corrective action, if necessary.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.4.3: Obtains Commitments to Report Unauthorized Disclosures',
          'requirement_description': 'A process exists for obtaining commitments from vendors and other third parties to '
                                     'report to the entity actual or suspected unauthorized disclosures of personal '
                                     'information.',
          'subchapter': 'P6.4: The entity obtains privacy commitments from vendors and other third parties who have access to '
                        "personal information to meet the entity's objectives related to privacy. The entity assesses those "
                        'parties? compliance on a periodic and as-needed basis and takes corrective action, if necessary.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': ['Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .',
                                   'Q-PRI-08: Does the organization implement a process for ensuring that organizational plans '
                                   'for conducting cybersecurity and privacy testing, training and monitoring activities '
                                   'associated with organizational systems are developed and performed? .'],
          'objective_title': 'P6.5.1: Remediates Misuse of Personal Information by a Third Party',
          'requirement_description': 'The entity takes remedial action in response to misuse of personal information by a '
                                     'third party to whom the entity has transferred such information.',
          'subchapter': 'P6.5: The entity obtains commitments from vendors and other third parties with access to personal '
                        'information to notify the entity in the event of actual or suspected unauthorized disclosures of '
                        'personal information. Such notifications are reported to appropriate personnel and acted on in '
                        "accordance with established incident response procedures to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.5.2: Reports Actual or Suspected Unauthorized Disclosures',
          'requirement_description': 'A process exists for obtaining commitments from vendors and other third parties to '
                                     'report to the entity actual or suspected unauthorized disclosures of personal '
                                     'information.',
          'subchapter': 'P6.5: The entity obtains commitments from vendors and other third parties with access to personal '
                        'information to notify the entity in the event of actual or suspected unauthorized disclosures of '
                        'personal information. Such notifications are reported to appropriate personnel and acted on in '
                        "accordance with established incident response procedures to meet the entity's objectives related to "
                        'privacy.'},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': ['Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .',
                                   'Q-IRO-04.1: Does the organization address data breaches, or other incidents involving the '
                                   'unauthorized disclosure of sensitive or regulated data, according to applicable laws, '
                                   'regulations and contractual obligations? .'],
          'objective_title': 'P6.6.1: Identifies Reporting Requirements',
          'requirement_description': 'The entity has a process for determining whether notification of a privacy breach is '
                                     'required, including the method to be used, the timeline, and the identification of '
                                     'recipients of such notifications.',
          'subchapter': 'P6.6: The entity provides notification of breaches and incidents to affected data subjects, '
                        "regulators, and others to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.6.2: Provides Notice of Breaches and Incidents',
          'requirement_description': 'The entity has a process for providing notice of breaches and incidents to affected data '
                                     "subjects, regulators, and others to support the achievement of the entity's objectives "
                                     'related to privacy.  ',
          'subchapter': 'P6.6: The entity provides notification of breaches and incidents to affected data subjects, '
                        "regulators, and others to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': ['Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-IRO-04.1: Does the organization address data breaches, or other incidents involving the '
                                   'unauthorized disclosure of sensitive or regulated data, according to applicable laws, '
                                   'regulations and contractual obligations? .'],
          'objective_title': 'P6.7.1: Identifies Types of Personal Information and Handling Process',
          'requirement_description': 'The types of personal information and sensitive personal information and the related '
                                     'processes, systems, and third parties involved in the handling of such information are '
                                     'identified.',
          'subchapter': 'P6.7: The entity provides data subjects with an accounting of the personal information held and '
                        'disclosure of the data subjects? personal information, upon the data subjects? request, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.7.2: Captures, Identifies, and Communicates Requests for Information',
          'requirement_description': 'Requests for an accounting of personal information held and disclosures of the data '
                                     'subjects? personal information are captured, and information related to the requests is '
                                     "identified and communicated to data subjects to support the achievement of the entity's "
                                     'objectives related to privacy.',
          'subchapter': 'P6.7: The entity provides data subjects with an accounting of the personal information held and '
                        'disclosure of the data subjects? personal information, upon the data subjects? request, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to disclosure and no',
          'conformity_questions': [],
          'objective_title': 'P6.7.3: Responds to Data Controller Requests',
          'requirement_description': 'The entity has a process to respond to data controller requests for an accounting of '
                                     'personal information held in accordance with service agreements and privacy objectives.',
          'subchapter': 'P6.7: The entity provides data subjects with an accounting of the personal information held and '
                        'disclosure of the data subjects? personal information, upon the data subjects? request, to meet the '
                        "entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to quality',
          'conformity_questions': ['Q-PRI-10: Does the organization issue guidelines ensuring and maximizing the quality, '
                                   'utility, objectivity, integrity, impact determination and de-identification of Personal '
                                   'Data (PD) across the information lifecycle?.'],
          'objective_title': 'P7.1.1: Ensures Accuracy and Completeness of Personal Information',
          'requirement_description': 'Personal information is accurate and complete for the purposes for which it is to be '
                                     'used.',
          'subchapter': 'P7.1: The entity collects and maintains accurate, up-to-date, complete, and relevant personal '
                        "information to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to quality',
          'conformity_questions': [],
          'objective_title': 'P7.1.2: Ensures Relevance of Personal Information',
          'requirement_description': 'Personal information is relevant to the purposes for which it is to be used.',
          'subchapter': 'P7.1: The entity collects and maintains accurate, up-to-date, complete, and relevant personal '
                        "information to meet the entity's objectives related to privacy."},
         {'chapter_title': 'P: privacy criteria related to monitoring and en',
          'conformity_questions': ['Q-PRI-06.4: Does the organization implement a process for receiving and responding to '
                                   'complaints, concerns or questions from individuals about the organizational privacy '
                                   'practices?.'],
          'objective_title': 'P8.1.1: Communicates to Data Subjects',
          'requirement_description': 'Data subjects are informed about how to contact the entity with inquiries, complaints, '
                                     'and disputes.',
          'subchapter': 'P8.1: The entity implements a process for receiving, addressing, resolving, and communicating the '
                        'resolution of inquiries, complaints, and disputes from data subjects and others and periodically '
                        "monitors compliance to meet the entity's objectives related to privacy. Corrections and other "
                        'necessary actions related to identified deficiencies are made or taken in a timely manner.'},
         {'chapter_title': 'P: privacy criteria related to monitoring and en',
          'conformity_questions': [],
          'objective_title': 'P8.1.2: Addresses Inquiries, Complaints, and Disputes',
          'requirement_description': 'A process is in place to address inquiries, complaints, and disputes.',
          'subchapter': 'P8.1: The entity implements a process for receiving, addressing, resolving, and communicating the '
                        'resolution of inquiries, complaints, and disputes from data subjects and others and periodically '
                        "monitors compliance to meet the entity's objectives related to privacy. Corrections and other "
                        'necessary actions related to identified deficiencies are made or taken in a timely manner.'},
         {'chapter_title': 'P: privacy criteria related to monitoring and en',
          'conformity_questions': [],
          'objective_title': 'P8.1.3: Documents and Communicates Dispute Resolution',
          'requirement_description': 'Each complaint is addressed, and the resolution is documented and communicated to the '
                                     'individual.',
          'subchapter': 'P8.1: The entity implements a process for receiving, addressing, resolving, and communicating the '
                        'resolution of inquiries, complaints, and disputes from data subjects and others and periodically '
                        "monitors compliance to meet the entity's objectives related to privacy. Corrections and other "
                        'necessary actions related to identified deficiencies are made or taken in a timely manner.'},
         {'chapter_title': 'P: privacy criteria related to monitoring and en',
          'conformity_questions': [],
          'objective_title': 'P8.1.4: Documents and Reports Compliance Review Results',
          'requirement_description': 'Compliance with objectives related to privacy are reviewed and documented, and the '
                                     'results of such reviews are reported to management. If problems are identified, '
                                     'remediation plans are developed and implemented.',
          'subchapter': 'P8.1: The entity implements a process for receiving, addressing, resolving, and communicating the '
                        'resolution of inquiries, complaints, and disputes from data subjects and others and periodically '
                        "monitors compliance to meet the entity's objectives related to privacy. Corrections and other "
                        'necessary actions related to identified deficiencies are made or taken in a timely manner.'},
         {'chapter_title': 'P: privacy criteria related to monitoring and en',
          'conformity_questions': [],
          'objective_title': 'P8.1.5: Documents and Reports Instances of Noncompliance',
          'requirement_description': 'Instances of noncompliance with objectives related to privacy are documented and '
                                     'reported and, if needed, corrective and disciplinary measures are taken on a timely '
                                     'basis.',
          'subchapter': 'P8.1: The entity implements a process for receiving, addressing, resolving, and communicating the '
                        'resolution of inquiries, complaints, and disputes from data subjects and others and periodically '
                        "monitors compliance to meet the entity's objectives related to privacy. Corrections and other "
                        'necessary actions related to identified deficiencies are made or taken in a timely manner.'},
         {'chapter_title': 'P: privacy criteria related to monitoring and en',
          'conformity_questions': [],
          'objective_title': 'P8.1.6: Performs Ongoing Monitoring',
          'requirement_description': 'Ongoing procedures are performed for monitoring the effectiveness of controls over '
                                     'personal information and for taking timely corrective actions when necessary.',
          'subchapter': 'P8.1: The entity implements a process for receiving, addressing, resolving, and communicating the '
                        'resolution of inquiries, complaints, and disputes from data subjects and others and periodically '
                        "monitors compliance to meet the entity's objectives related to privacy. Corrections and other "
                        'necessary actions related to identified deficiencies are made or taken in a timely manner.'}]
