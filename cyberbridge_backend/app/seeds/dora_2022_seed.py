# app/seeds/dora_2022_seed.py
import logging
import json
import io
from .base_seed import BaseSeed
from app.models import models
from app.constants.dora_2022_connections import DORA_2022_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class Dora2022Seed(BaseSeed):
    """Seed DORA 2022 framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating DORA 2022 framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create DORA 2022 Framework
        dora_2022_framework, created = self.get_or_create(
            models.Framework,
            {"name": "DORA 2022", "organisation_id": default_org.id},
            {
                "name": "DORA 2022",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("DORA 2022 framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == dora_2022_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == dora_2022_framework.id
            ).all()

            logger.info(f"Found existing DORA 2022 framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            # Keep links in sync even when framework/objectives already exist.
            if not self.skip_wire_connections:
                self._wire_connections(dora_2022_framework, default_org, existing_objectives)
            self.db.commit()

            return {
                "framework": dora_2022_framework,
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
                description="DORA 2022 conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=dora_2022_framework.id,
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
                        "framework_id": dora_2022_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": dora_2022_framework.id
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

        # Wire connections: risks, controls, policies -> objectives
        if not self.skip_wire_connections:
            self._wire_connections(dora_2022_framework, default_org, objectives_list)

        self.db.commit()

        logger.info(f"Created DORA 2022 framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": dora_2022_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _wire_connections(self, framework, org, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to DORA 2022 objectives using the DORA_2022_CONNECTIONS mapping.
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
            logger.warning("Missing lookup defaults - skipping DORA 2022 connection wiring")
            return

        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in DORA_2022_CONNECTIONS.values():
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

        logger.info(f"DORA 2022 wiring: {len(risk_name_to_id)} risks ready")

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

        logger.info(f"DORA 2022 wiring: {len(control_code_to_id)} controls ready")

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
                        logger.warning(f"DORA 2022 wiring: docx conversion failed for {policy_code}: {conv_err}")
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

        logger.info(f"DORA 2022 wiring: {len(policy_code_to_id)} policies ready")

        obj_title_to_id = {obj.title: obj.id for obj in objectives_list}
        policy_framework_pairs = set()

        obj_risk_count = 0
        obj_ctrl_count = 0
        pol_obj_count = 0
        ctrl_risk_count = 0
        ctrl_pol_count = 0
        planned_control_risk_pairs = set()
        planned_control_policy_pairs = set()

        for obj_title, conn in DORA_2022_CONNECTIONS.items():
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
            f"DORA 2022 wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return ['Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?.',
         'Q-GOV-09: Does the organization establish control objectives as the basis for the selection, implementation and '
         "management of the organization's internal control system?.",
         'Q-GOV-01.2: Does the organization provide governance oversight reporting and recommendations to those entrusted to '
         "make executive decisions about matters considered material to the organization's cybersecurity and privacy program?.",
         'Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering '
         'committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally '
         'and on a regular basis?.',
         'Q-GOV-04: Does the organization assign a qualified individual with the mission and resources to centrally-manage '
         'coordinate, develop, implement and maintain an enterprise-wide cybersecurity and privacy program? .',
         'Q-GOV-07: Does the organization establish contact with selected groups and associations within the cybersecurity & '
         'privacy communities to:   -  Facilitate ongoing cybersecurity and privacy education and training for organizational '
         'personnel;  -  Maintain currency with recommended cybersecurity and privacy practices, techniques and technologies; '
         'and  -  Share current security-related information including threats, vulnerabilities and incidents? .',
         'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, risk response and risk '
         'monitoring;  -  Constraints affecting risk assessments, risk response and risk monitoring;  -  The organizational '
         'risk tolerance; and  -  Priorities and trade-offs considered by the organization for managing risk?.',
         'Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.',
         'Q-RSK-01.2-CM: Does the organization reduce the magnitude or likelihood of potential impacts by resourcing the '
         'capability required to manage technology-related risks?.',
         'Q-RSK-01.4-CM: Does the organization define organizational risk threshold?.',
         'Q-RSK-01.3-CM: Does the organization define organizational risk tolerance(s)?.',
         'Q-RSK-05: Does the organization identify and assign a risk ranking to newly discovered security vulnerabilities that '
         'is based on industry-recognized practices? .',
         'Q-RSK-04.1: Does the organization maintain a risk register that facilitates monitoring and reporting of risks?.',
         'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the likelihood and magnitude of '
         "harm, from unauthorized access, use, disclosure, disruption, modification or destruction of the organization's "
         'systems and data?.',
         'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
         'Q-RSK-02.1: Does the organization prioritize the impact level for systems, applications and/or services to provide '
         'additional granularity on potential disruptions?.',
         'Q-RSK-02: Does the organization categorizes systems and data in accordance with applicable local, state and Federal '
         'laws that:  -  Document the security categorization results (including supporting rationale) in the security plan '
         'for systems; and  -  Ensure the security categorization decision is reviewed and approved by the asset owner?.',
         'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and assess cybersecurity and '
         'data protection risks?.',
         'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly upon identifying new '
         'security vulnerabilities, including using outside sources for security vulnerability information? .',
         'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to reduce risk and exposure to '
         'threats?.',
         'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy assessments, incidents and '
         'audits to ensure proper remediation has been performed?.',
         'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
         'Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the continuous monitoring strategy '
         'that includes monitoring the effectiveness of security & privacy controls, compliance and change management?.',
         'Q-CPL-02.1: Does the organization implement an internal audit function that is capable of providing senior '
         "organization management with insights into the appropriateness of the organization's technology and information "
         'governance processes?.',
         'Q-IAO-02.3: Does the organization accept and respond to the results of external assessments that are performed by '
         'impartial, external organizations? .',
         'Q-IAO-02.4: Does the organization produce a Security Assessment Report (SAR) at the conclusion of a security '
         'assessment to certify the results of the assessment and assist with any remediation actions?.',
         'Q-BCD-02.1: Does the organization plan for the resumption of all missions and business functions within Recovery '
         "Time Objectives (RTOs) of the contingency plan's activation?.",
         'Q-BCD-02.3: Does the organization resume essential missions and business functions within an organization-defined '
         'time period of contingency plan activation? .',
         'Q-BCD-02.2: Does the organization plan for the continuance of essential missions and business functions with little '
         'or no loss of operational continuity and sustain that continuity until full system restoration at primary processing '
         'and/or storage sites?.',
         'Q-BCD-02: Does the organization identify and document the critical systems, applications and services that support '
         'essential missions and business functions?.',
         'Q-TDA-05: Does the organization require the developers of systems, system components or services to produce a design '
         "specification and security architecture that:   -  Is consistent with and supportive of the organization's security "
         "architecture which is established within and is an integrated part of the organization's enterprise architecture;  "
         '-  Accurately and completely describes the required security functionality and the allocation of security controls '
         'among physical and logical components; and  -  Expresses how individual security functions, mechanisms and services '
         'work together to provide required security capabilities and a unified approach to protection?.',
         'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for its cybersecurity and '
         'privacy programs?.',
         'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) to assist senior management '
         'in performance monitoring and trend analysis of the cybersecurity and privacy program?.',
         'Q-GOV-05.1: Does the organization develop, report and monitor Key Performance Indicators (KPIs) to assist '
         'organizational management in performance monitoring and trend analysis of the cybersecurity and privacy program?.',
         'Q-TPM-03.3: Does the organization address identified weaknesses or deficiencies in the security of the supply chain '
         '.',
         'Q-TPM-03.2: Does the organization utilize security safeguards to limit harm from potential adversaries who identify '
         "and target the organization's supply chain? .",
         'Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain? .',
         'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of critical systems, '
         'components and services using a supply chain risk assessment process? .',
         'Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the '
         'development, acquisition, maintenance and disposal of systems, system components and services, including documenting '
         'selected mitigating actions and monitoring performance against those plans?.',
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
         'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  '
         'Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined '
         'information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit '
         'by designated organizational officials? .',
         'Q-CAP-03: Does the organization conducted capacity planning so that necessary capacity for information processing, '
         'telecommunications and environmental support will exist during contingency operations? .',
         'Q-CAP-01: Does the organization facilitate the implementation of capacity management controls to ensure optimal '
         'system performance to meet expected and anticipated future capacity requirements?.',
         'Q-AST-04.2: Does the organization ensure control applicability is appropriately-determined for systems, '
         'applications, services and third parties by graphically representing applicable boundaries?.',
         'Q-AST-04.3: Does the organization create and maintain a current inventory of systems, applications and services that '
         'are in scope for statutory, regulatory and/or contractual compliance obligations that provides sufficient detail to '
         'determine control applicability, based on asset scope categorization?.',
         'Q-AST-04.1: Does the organization determine cybersecurity and privacy control applicability by identifying, '
         'assigning and documenting the appropriate asset scope categorization for all systems, applications, services and '
         'personnel (internal and third-parties)?.',
         'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain sufficient detail to '
         "assess the security of the network's architecture;  -  Reflect the current architecture of the network environment; "
         'and  -  Document all sensitive/regulated data flows?.',
         'Q-AST-03.1: Does the organization include capturing the name, position and/or role of individuals '
         'responsible/accountable for administering assets as part of the technology asset inventory process?.',
         'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, individual, or responsible '
         'organization level to establish a common understanding of requirements for asset protection?.',
         'Q-AST-01: Does the organization facilitate the implementation of asset management controls?.',
         'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by recurring vulnerability scanning '
         'of systems and web applications?.',
         'Q-VPM-03: Does the organization identify and assign a risk ranking to newly discovered security vulnerabilities '
         'using reputable outside sources for security vulnerability information? .',
         'Q-CHG-02: Does the organization govern the technical configuration change control processes?.',
         'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, prior to the implementation '
         'of the change?.',
         'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and procedures at planned '
         'intervals or if significant changes occur to ensure their continuing suitability, adequacy and effectiveness? .',
         'Q-AST-02.8: Does the organization create and maintain a map of technology assets where sensitive/regulated data is '
         'stored, transmitted or processed?.',
         'Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.',
         'Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of Third-Party Service Providers '
         '(TSP) that can potentially impact the Confidentiality, Integrity, Availability and/or Safety (CIAS) of the '
         "organization's systems, applications, services and data?.",
         'Q-AST-02.3: Does the organization prevent system components from being duplicated in other asset inventories? .',
         'Q-AST-02.2: Does the organization use automated mechanisms to detect and alert upon the detection of unauthorized '
         'hardware, software and firmware components?.',
         'Q-AST-02.1: Does the organization update asset inventories as part of component installations, removals and asset '
         'upgrades? .',
         'Q-AST-03.2: Does the organization govern the chronology of the origin, development, ownership, location and changes '
         'to a system, system components and associated data?.',
         'Q-MON-16: Does the organization detect and respond to anomalous behavior that could indicate account compromise or '
         'other malicious activities?.',
         'Q-MON-06: Does the organization provide an event log report generation capability to aid in detecting and assessing '
         'anomalous activities? .',
         'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate incidents in accordance with '
         'established timelines and procedures?.',
         'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar change-detection technology, on '
         'critical assets to generate alerts for unauthorized modifications? .',
         'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or similar automated tool, to '
         'support near real-time analysis and incident escalation?.',
         'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS / IPS) technologies on '
         'critical systems, key network segments and network choke points?.',
         'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide monitoring controls?.',
         'Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify '
         'the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) '
         'and Recovery Point Objectives (RPOs)?.',
         'Q-BCD-10: Does the organization reduce the likelihood of a single point of failure with primary telecommunications '
         'services?.',
         'Q-BCD-09: Does the organization establish an alternate processing site that provides security measures equivalent to '
         'that of the primary site?.',
         'Q-BCD-08: Does the organization establish an alternate storage site that includes both the assets and necessary '
         'agreements to permit the storage and recovery of system backup information? .',
         'Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.',
         'Q-BCD-13: Does the organization protect backup and restoration hardware and software?.',
         'Q-BCD-12.3: Does the organization utilize electronic discovery (eDiscovery) that covers current and archived '
         'communication transactions?.',
         'Q-BCD-12.4: Does the organization restore systems, applications and/or services within organization-defined '
         'restoration time-periods from configuration-controlled and integrity-protected information; representing a known, '
         'operational state for the asset?.',
         'Q-BCD-12.2: Does the organization implement real-time or near-real-time failover capability to maintain availability '
         'of critical systems, applications and/or services?.',
         'Q-BCD-12.1: Does the organization utilize specialized backup mechanisms that will allow transaction recovery for '
         'transaction-based applications and services in accordance with Recovery Point Objectives (RPOs)?.',
         'Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a '
         'disruption, compromise or failure? .',
         'Q-CPL-03: Does the organization ensure managers regularly review the processes and documented procedures within '
         'their area of responsibility to adhere to appropriate security policies, standards and other applicable '
         'requirements?.',
         'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards '
         'and procedures?.',
         'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to monitor and control '
         'communications at the external network boundary and at key internal boundaries within the network?.',
         'Q-NET-14.2: Does the organization cryptographically protect the confidentiality and integrity of remote access '
         'sessions (e.g., VPN)?.',
         'Q-NET-13: Does the organization protect the confidentiality, integrity and availability of electronic messaging '
         'communications?.',
         'Q-NET-10.2: Does the organization perform data origin authentication and data integrity verification on the Domain '
         'Name Service (DNS) resolution responses received from authoritative sources when requested by client systems? .',
         'Q-NET-09: Does the organization protect the authenticity and integrity of communications sessions? .',
         'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect and report unauthorized '
         'changes to system files and configurations?.',
         'Q-END-02: Does the organization protect the confidentiality, integrity, availability and safety of endpoint '
         'devices?.',
         'Q-CRY-06: Does the organization use cryptographic mechanisms to protect the confidentiality and integrity of '
         'non-console administrative access?.',
         'Q-CRY-05.1: Does the organization use cryptographic mechanisms to protect the confidentiality and integrity of '
         'sensitive/regulated data residing on storage media?.',
         'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of data being transmitted? .',
         'Q-AST-18: Does the organization provision and protect the confidentiality, integrity and authenticity of product '
         'supplier keys and data that can be used as a roots of trust basis for integrity verification?.',
         'Q-MON-11: Does the organization monitor for evidence of unauthorized exfiltration or disclosure of non-public '
         'information? .',
         'Q-MON-11.2: Does the organization detect unauthorized network services and alert incident response personnel? .',
         'Q-MON-11.1: Does the organization analyze network traffic to detect covert data exfiltration?.',
         'Q-MON-01.11: Does the organization alert incident response personnel of detected suspicious events and implement '
         'actions to terminate suspicious events?.',
         'Q-MON-04: Does the organization allocate and proactively manage sufficient event log storage capacity to reduce the '
         'likelihood of such capacity being exceeded?.',
         'Q-MON-05: Does the organization alert appropriate personnel in the event of a log processing failure and take '
         'actions to remedy the disruption?.',
         'Q-MON-05.1: Does the organization provide 24x7x365 near real-time alerting capability when an event log processing '
         'failure occurs?.',
         'Q-MON-05.2: Does the organization alert appropriate personnel when the allocated volume reaches an '
         'organization-defined percentage of maximum event log storage capacity?.',
         'Q-MON-01.10: Does the organization monitor deactivated accounts for attempted usage?.',
         'Q-MON-01.14: Does the organization implement enhanced activity monitoring for individuals who have been identified '
         'as posing an increased level of risk? .',
         'Q-MON-01.15: Does the organization implement enhanced activity monitoring for privileged users?.',
         'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized access, modification and '
         'deletion?.',
         'Q-MON-08.3: Does the organization protect the integrity of event logs and audit tools with cryptographic mechanisms? '
         '.',
         'Q-BCD-01.2: Does the organization coordinate internal contingency plans with the contingency plans of external '
         'service providers to ensure that contingency requirements can be satisfied?.',
         'Q-BCD-01.1: Does the organization coordinate contingency plan development with internal and external elements '
         'responsible for related plans? .',
         'Q-IRO-04: Does the organization maintain and make available a current and viable Incident Response Plan (IRP) to all '
         'stakeholders?.',
         'Q-IRO-02.5: Does the organization coordinate with approved third-parties to achieve a cross-organization perspective '
         'on incident awareness and more effective incident responses? .',
         'Q-IRO-02.4: Does the organization identify classes of incidents and actions to take to ensure the continuation of '
         'organizational missions and business functions?.',
         'Q-IRO-02.3: Does the organization dynamically reconfigure information system components as part of the incident '
         'response capability? .',
         'Q-IRO-02.6: Does the organization automatically disable systems involved in an incident that meet organizational '
         'criteria to be automatically disabled upon detection?.',
         "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, "
         'containment, eradication and recovery?.',
         'Q-IRO-04.3: Does the organization use qualitative and quantitative data from incident response testing to:  - '
         'Determine the effectiveness of incident response processes; - Continuously improve incident response processes; and '
         '- Provide incident response measures and metrics that are accurate, consistent, and in a reproducible format?.',
         'Q-IRO-04.2: Does the organization regularly review and modify incident response practices to incorporate lessons '
         'learned, business process changes and industry developments, as necessary?.',
         'Q-BCD-11.5: Does the organization utilize sampling of available backups to test recovery capabilities as part of '
         'business continuity plan testing?.',
         'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of the backup process, as '
         'well as the integrity and availability of the data? .',
         'Q-BCD-06: Does the organization keep contingency plans current with business needs, technology changes and feedback '
         'from contingency plan testing activities?.',
         'Q-BCD-04.2: Does the organization test the contingency plan at the alternate processing site to both familiarize '
         'contingency personnel with the facility and evaluate the capabilities of the alternate processing site to support '
         'contingency operations? .',
         'Q-BCD-04.1: Does the organization coordinate contingency plan testing with internal and external elements '
         'responsible for related plans? .',
         "Q-BCD-04: Does the organization conduct tests and/or exercises to evaluate the contingency plan's effectiveness and "
         "the organization's readiness to execute the plan?.",
         'Q-IRO-06.1: Does the organization coordinate incident response testing with organizational elements responsible for '
         'related plans? .',
         'Q-IRO-06: Does the organization formally test incident response capabilities through realistic exercises to '
         'determine the operational effectiveness of those capabilities?.',
         "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' activity every time the "
         'contingency plan is activated?.',
         'Q-IRO-14: Does the organization maintain incident response contacts with applicable regulatory and law enforcement '
         'agencies? .',
         'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational incident response personnel '
         'within organization-defined time-periods; and  -  Externally to regulatory authorities and affected parties, as '
         'necessary?.',
         'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and business function '
         'representatives that are capable of addressing cybersecurity and privacy incident response operations?.',
         'Q-IRO-05: Does the organization train personnel in their incident response roles and responsibilities?.',
         'Q-IRO-09.1: Does the organization use automated mechanisms to assist in the tracking, collection and analysis of '
         'information from actual and potential cybersecurity and privacy incidents?.',
         'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy incidents? .',
         'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving cybersecurity and privacy '
         'incidents to reduce the likelihood or impact of future incidents? .',
         'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized disclosure and/or '
         'modification of backup information/.',
         'Q-BCD-11.6: Does the organization transfer backup data to the alternate storage site at a rate that is capable of '
         'meeting both Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.',
         'Q-BCD-11.2: Does the organization store backup copies of critical software and other security-related information in '
         'a separate facility or in a fire-rated container that is not collocated with the system being backed up?.',
         'Q-BCD-01.4: Does the organization configure the alternate storage site to facilitate recovery operations in '
         'accordance with Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs)?.',
         'Q-BCD-09.5: Does the organization plan and prepare for both natural and manmade circumstances that preclude '
         'returning to the primary processing site?.',
         'Q-BCD-09.2: Does the organization identify potential accessibility problems to the alternate processing site and '
         'possible mitigation actions, in the event of an area-wide disruption or disaster?.',
         'Q-BCD-09.1: Does the organization separate the alternate processing site from the primary processing site to reduce '
         'susceptibility to similar threats?.',
         'Q-IRO-17-CM: Does the organization establish a post-incident procedure to verify the integrity of the affected '
         'systems before restoring them to normal operations?.',
         'Q-THR-05: Does the organization utilize security awareness training on recognizing and reporting potential '
         'indicators of insider threat?.',
         'Q-THR-04: Does the organization implement an insider threat program that includes a cross-discipline insider threat '
         'incident handling team? .',
         'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
         'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the potential attack vectors that '
         'attackers could use to attack the organization? .',
         'Q-THR-01: Does the organization implement a threat awareness program that includes a cross-organization '
         'information-sharing capability? .',
         'Q-THR-06: Does the organization establish a Vulnerability Disclosure Program (VDP) to assist with the secure '
         'development and maintenance of products and services that receives unsolicited input from the public about '
         'vulnerabilities in organizational systems, services and processes?.',
         'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing basis and ensure assets are '
         'protected against known attacks? .',
         'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, tracked and remediated?.',
         "Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the organization's "
         'cybersecurity and privacy policies and standards? .',
         'Q-CPL-03.1: Does the organization utilize independent assessors to evaluate security & privacy controls at planned '
         'intervals or when the system, service or project undergoes significant changes?.',
         'Q-CPL-02: Does the organization provide a security & privacy controls oversight function that reports to the '
         "organization's executive leadership?.",
         'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before authorizing access to the '
         'system or performing assigned duties;   -  When required by system changes; and   -  Annually thereafter?.',
         'Q-SAT-02: Does the organization provide all employees and contractors appropriate awareness education and training '
         'that is relevant for their job function? .',
         'Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness '
         'controls? .',
         'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized cybersecurity and privacy '
         'practices in the specification, design, development, implementation and modification of systems and services?.',
         'Q-SEA-02: Does the organization develop an enterprise architecture, aligned with industry-recognized leading '
         'practices, with consideration for cybersecurity and privacy principles that addresses risk to organizational '
         'operations, assets, individuals, other organizations? .',
         'Q-GOV-06: Does the organization identify and document appropriate contacts within relevant law enforcement and '
         'regulatory bodies?.',
         'Q-IRO-20: Does the organization have a written down policy to communicate about incidents to external and internal '
         'audience?.',
         'Q-AST-31-CM: Does the organization categorize technology assets?.',
         'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with applicable statutory, '
         'regulatory and contractual requirements? .',
         'Q-DCH-11: Does the organization reclassify data, including associated systems, applications and services, '
         'commensurate with the security category and/or classification level of the information?.',
         'Q-IRO-16: Does the organization proactively manage public relations associated with an incident and employ '
         'appropriate measures to repair the reputation of the organization?.',
         'Q-IRO-11: Does the organization provide incident response advice and assistance to users of systems for the handling '
         'and reporting of actual and potential cybersecurity and privacy incidents? .',
         'Q-IRO-11.1: Does the organization use automated mechanisms to increase the availability of incident response-related '
         'information and support? .',
         "Q-IRO-11.2: Does the organization establish a direct, cooperative relationship between the organization's incident "
         'response capability and external service providers?.',
         'Q-TPM-11: Does the organization ensure response/recovery planning and testing are conducted with critical '
         'suppliers/providers? .',
         'Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to perform penetration '
         'testing?.',
         'Q-VPM-07: Does the organization conduct penetration testing on systems and web applications?.',
         'Q-VPM-05.2: Does the organization use automated mechanisms to determine the state of system components with regard '
         'to flaw remediation? .',
         'Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
         'Q-VPM-06.8: Does the organization define what information is allowed to be discoverable by adversaries and take '
         'corrective actions to remediated non-compliant systems?.',
         'Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.',
         'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface management activities?.',
         'Q-THR-07: Does the organization perform cyber threat hunting that uses Indicators of Compromise (IoC) to detect, '
         'track and disrupt threats that evade existing security controls?.',
         'Q-TDA-09.5: Does the organization perform application-level penetration testing of custom-made applications and '
         'services?.',
         'Q-TPM-09: Does the organization address weaknesses or deficiencies in supply chain elements identified during '
         'independent or organizational assessments of such elements? .',
         'Q-TPM-04.3: Does the organization ensure that the interests of third-party service providers are consistent with and '
         'reflect organizational interests?.',
         'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or outsourcing of '
         'technology-related services?.',
         "Q-TPM-04: Does the organization mitigate the risks associated with third-party access to the organization's systems "
         'and data?.',
         'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools and procurement methods '
         'for the purchase of unique systems, system components or services?.',
         'Q-TPM-05.2: Does the organization ensure cybersecurity and privacy requirements are included in contracts that '
         'flow-down to applicable sub-contractors and suppliers?.',
         'Q-TPM-05.1: Does the organization compel Third-Party Service Providers (TSP) to provide notification of actual or '
         'potential compromises in the supply chain that can potentially affect or have adversely affected systems, '
         'applications and/or services that the organization utilizes?.',
         'Q-TPM-05: Does the organization identify, regularly review and document third-party confidentiality, Non-Disclosure '
         "Agreements (NDAs) and other contracts that reflect the organization's needs to protect systems and data?.",
         'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service Providers (TSP) for '
         'compliance with established contractual requirements for cybersecurity and privacy controls? .',
         'Q-TPM-05.7-CM: Does the organization include "break clauses"" within contracts for failure to meet contract criteria '
         'for cybersecurity and/or privacy controls?".',
         'Q-TPM-05.6: Does the organization obtain a First-Party Declaration (1PD) from applicable Third-Party Service '
         'Providers (TSP) that provides assurance of compliance with specified statutory, regulatory and contractual '
         'obligations for cybersecurity and privacy controls, including any flow-down requirements to subcontractors? .']

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and '
                                   'privacy controls?.',
                                   'Q-GOV-09: Does the organization establish control objectives as the basis for the '
                                   "selection, implementation and management of the organization's internal control system?."],
          'objective_title': 'Article 5.1: Financial entities shall have in place an internal governance and control framework '
                             'that ensures an effective and prudent management of ICT risk, in accordance with Article 6(4), '
                             'in order to achieve a high level of digital operational resilience.',
          'requirement_description': None,
          'subchapter': 'Article 5: Governance & Organisation'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-GOV-01.2: Does the organization provide governance oversight reporting and '
                                   'recommendations to those entrusted to make executive decisions about matters considered '
                                   "material to the organization's cybersecurity and privacy program?.",
                                   'Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment '
                                   'through a steering committee or advisory board, comprising of key cybersecurity, privacy '
                                   'and business executives, which meets formally and on a regular basis?.'],
          'objective_title': 'Article 5.2: The management body of the financial entity shall define, approve, oversee and be '
                             'responsible for the implementation of all arrangements related to the ICT risk management '
                             'framework referred to in Article 6(1).',
          'requirement_description': '\n'
                                     'For the purposes of the first subparagraph, the management body shall:\n'
                                     '(a) bear the ultimate responsibility for managing the financial entity’s ICT risk;\n'
                                     '(b) put in place policies that aim to ensure the maintenance of high standards of '
                                     'availability, authenticity, integrity and confidentiality, of data;\n'
                                     '(c) set clear roles and responsibilities for all ICT-related functions and establish '
                                     'appropriate governance arrangements to ensure effective and timely communication, '
                                     'cooperation and coordination among those functions;\n'
                                     '(d) bear the overall responsibility for setting and approving the digital operational '
                                     'resilience strategy as referred to in Article 6(8), including the determination of the '
                                     'appropriate risk tolerance level of ICT risk of the financial entity, as referred to in '
                                     'Article 6(8), point (b);\n'
                                     '(e) approve, oversee and periodically review the implementation of the financial '
                                     'entity’s ICT business continuity policy and ICT response and recovery plans, referred '
                                     'to, respectively, in Article 11(1) and (3), which may be adopted as a dedicated specific '
                                     'policy forming an integral part of the financial entity’s overall business continuity '
                                     'policy and response and recovery plan;\n'
                                     '(f) approve and periodically review the financial entity’s ICT internal audit plans, ICT '
                                     'audits and material modifications to them;\n'
                                     '(g) allocate and periodically review the appropriate budget to fulfil the financial '
                                     'entity’s digital operational resilience needs in respect of all types of resources, '
                                     'including relevant ICT security awareness programmes and digital operational resilience '
                                     'training referred to in Article 13(6), and ICT skills for all staff;\n'
                                     '(h) approve and periodically review the financial entity’s policy on arrangements '
                                     'regarding the use of ICT services provided by ICT third-party service providers;\n'
                                     '(i) put in place, at corporate level, reporting channels enabling it to be duly informed '
                                     'of the following:\n'
                                     '(i) arrangements concluded with ICT third-party service providers on the use of ICT '
                                     'services,\n'
                                     '(ii) any relevant planned material changes regarding the ICT third-party service '
                                     'providers,\n'
                                     '(iii) the potential impact of such changes on the critical or important functions '
                                     'subject to those arrangements, including a risk analysis summary to assess the impact of '
                                     'those changes, and at least major ICT-related incidents and their impact, as well as '
                                     'response, recovery and corrective measures.',
          'subchapter': 'Article 5: Governance & Organisation'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': 'Article 5.3: Financial entities, other than microenterprises, shall establish a role in order to '
                             'monitor the arrangements concluded with ICT third-party service providers on the use of ICT '
                             'services, or shall designate a member of senior management as responsible for overseeing the '
                             'related risk exposure and relevant documentation.',
          'requirement_description': None,
          'subchapter': 'Article 5: Governance & Organisation'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-GOV-07: Does the organization establish contact with selected groups and associations '
                                   'within the cybersecurity & privacy communities to:   -  Facilitate ongoing cybersecurity '
                                   'and privacy education and training for organizational personnel;  -  Maintain currency '
                                   'with recommended cybersecurity and privacy practices, techniques and technologies; and  -  '
                                   'Share current security-related information including threats, vulnerabilities and '
                                   'incidents? .'],
          'objective_title': 'Article 5.4: Members of the management body of the financial entity shall actively keep up to '
                             'date with sufficient knowledge and skills to understand and assess ICT risk and its impact on '
                             'the operations of the financial entity, including by following specific training on a regular '
                             'basis, commensurate to the ICT risk being managed.',
          'requirement_description': None,
          'subchapter': 'Article 5: Governance & Organisation'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, '
                                   'risk response and risk monitoring;  -  Constraints affecting risk assessments, risk '
                                   'response and risk monitoring;  -  The organizational risk tolerance; and  -  Priorities '
                                   'and trade-offs considered by the organization for managing risk?.',
                                   'Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.'],
          'objective_title': 'Article 6.1: Financial entities shall have a sound, comprehensive and well-documented ICT risk '
                             'management framework as part of their overall risk management system, which enables them to '
                             'address ICT risk quickly, efficiently and comprehensively and to ensure a high level of digital '
                             'operational resilience.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-RSK-01.2-CM: Does the organization reduce the magnitude or likelihood of potential '
                                   'impacts by resourcing the capability required to manage technology-related risks?.',
                                   'Q-RSK-01.4-CM: Does the organization define organizational risk threshold?.',
                                   'Q-RSK-01.3-CM: Does the organization define organizational risk tolerance(s)?.',
                                   'Q-RSK-05: Does the organization identify and assign a risk ranking to newly discovered '
                                   'security vulnerabilities that is based on industry-recognized practices? .',
                                   'Q-RSK-04.1: Does the organization maintain a risk register that facilitates monitoring and '
                                   'reporting of risks?.',
                                   'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?.",
                                   'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
                                   'Q-RSK-02.1: Does the organization prioritize the impact level for systems, applications '
                                   'and/or services to provide additional granularity on potential disruptions?.',
                                   'Q-RSK-02: Does the organization categorizes systems and data in accordance with applicable '
                                   'local, state and Federal laws that:  -  Document the security categorization results '
                                   '(including supporting rationale) in the security plan for systems; and  -  Ensure the '
                                   'security categorization decision is reviewed and approved by the asset owner?.'],
          'objective_title': 'Article 6.2: The ICT risk management framework shall include at least strategies, policies, '
                             'procedures, ICT protocols and tools that are necessary to duly and adequately protect all '
                             'information assets and ICT assets, including computer software, hardware, servers, as well as to '
                             'protect all relevant physical components and infrastructures, such as premises, data centres and '
                             'sensitive designated areas, to ensure that all information assets and ICT assets are adequately '
                             'protected from risks including damage and unauthorised access or usage.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.',
                                   'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .',
                                   'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to '
                                   'reduce risk and exposure to threats?.',
                                   'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .'],
          'objective_title': 'Article 6.3: In accordance with their ICT risk management framework, financial entities shall '
                             'minimise the impact of ICT risk by deploying appropriate strategies, policies, procedures, ICT '
                             'protocols and tools. They shall provide complete and updated information on ICT risk and on '
                             'their ICT risk management framework to the competent authorities upon their request.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and '
                                   'privacy controls?.'],
          'objective_title': 'Article 6.4: Financial entities, other than microenterprises, shall assign the responsibility '
                             'for managing and overseeing ICT risk to a control function and ensure an appropriate level of '
                             'independence of such control function in order to avoid conflicts of interest. Financial '
                             'entities shall ensure appropriate segregation and independence of ICT risk management functions, '
                             'control functions, and internal audit functions, according to the three lines of defence model, '
                             'or an internal risk management and control model.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the '
                                   'continuous monitoring strategy that includes monitoring the effectiveness of security & '
                                   'privacy controls, compliance and change management?.',
                                   'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.',
                                   'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .'],
          'objective_title': 'Article 6.5: The ICT risk management framework shall be documented and reviewed at least once a '
                             'year, or periodically in the case of microenterprises, as well as upon the occurrence of major '
                             'ICT-related incidents, and following supervisory instructions or conclusions derived from '
                             'relevant digital operational resilience testing or audit processes. It shall be continuously '
                             'improved on the basis of lessons derived from implementation and monitoring. A report on the '
                             'review of the ICT risk management framework shall be submitted to the competent authority upon '
                             'its request.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-CPL-02.1: Does the organization implement an internal audit function that is capable of '
                                   'providing senior organization management with insights into the appropriateness of the '
                                   "organization's technology and information governance processes?."],
          'objective_title': 'Article 6.6: The ICT risk management framework of financial entities, other than '
                             'microenterprises, shall be subject to internal audit by auditors on a regular basis in line with '
                             "the financial entities' audit plan. Those auditors shall possess sufficient knowledge, skills "
                             'and expertise in ICT risk, as well as appropriate independence. The frequency and focus of ICT '
                             'audits shall be commensurate to the ICT risk of the financial entity.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IAO-02.3: Does the organization accept and respond to the results of external '
                                   'assessments that are performed by impartial, external organizations? .',
                                   'Q-IAO-02.4: Does the organization produce a Security Assessment Report (SAR) at the '
                                   'conclusion of a security assessment to certify the results of the assessment and assist '
                                   'with any remediation actions?.'],
          'objective_title': 'Article 6.7: Based on the conclusions from the internal audit review, financial entities shall '
                             'establish a formal follow-up process, including rules for the timely verification and '
                             'remediation of critical ICT audit findings.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-02.1: Does the organization plan for the resumption of all missions and business '
                                   "functions within Recovery Time Objectives (RTOs) of the contingency plan's activation?.",
                                   'Q-BCD-02.3: Does the organization resume essential missions and business functions within '
                                   'an organization-defined time period of contingency plan activation? .',
                                   'Q-BCD-02.2: Does the organization plan for the continuance of essential missions and '
                                   'business functions with little or no loss of operational continuity and sustain that '
                                   'continuity until full system restoration at primary processing and/or storage sites?.',
                                   'Q-BCD-02: Does the organization identify and document the critical systems, applications '
                                   'and services that support essential missions and business functions?.',
                                   'Q-TDA-05: Does the organization require the developers of systems, system components or '
                                   'services to produce a design specification and security architecture that:   -  Is '
                                   "consistent with and supportive of the organization's security architecture which is "
                                   "established within and is an integrated part of the organization's enterprise "
                                   'architecture;  -  Accurately and completely describes the required security functionality '
                                   'and the allocation of security controls among physical and logical components; and  -  '
                                   'Expresses how individual security functions, mechanisms and services work together to '
                                   'provide required security capabilities and a unified approach to protection?.',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.',
                                   'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) '
                                   'to assist senior management in performance monitoring and trend analysis of the '
                                   'cybersecurity and privacy program?.',
                                   'Q-GOV-05.1: Does the organization develop, report and monitor Key Performance Indicators '
                                   '(KPIs) to assist organizational management in performance monitoring and trend analysis of '
                                   'the cybersecurity and privacy program?.',
                                   'Q-RSK-01.3-CM: Does the organization define organizational risk tolerance(s)?.',
                                   'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.'],
          'objective_title': 'Article 6.8: The ICT risk management framework shall include a digital operational resilience '
                             'strategy setting out how the framework shall be implemented. To that end, the digital '
                             'operational resilience strategy shall include methods to address ICT risk and attain specific '
                             'ICT objectives, by:',
          'requirement_description': '\n'
                                     '(a) explaining how the ICT risk management framework supports the financial entity’s '
                                     'business strategy and objectives;\n'
                                     '(b) establishing the risk tolerance level for ICT risk, in accordance with the risk '
                                     'appetite of the financial entity, and analysing the impact tolerance for ICT '
                                     'disruptions;\n'
                                     '(c) setting out clear information security objectives, including key performance '
                                     'indicators and key risk metrics;\n'
                                     '(d) explaining the ICT reference architecture and any changes needed to reach specific '
                                     'business objectives;\n'
                                     '(e) outlining the different mechanisms put in place to detect ICT-related incidents, '
                                     'prevent their impact and provide protection from it;\n'
                                     '(f) evidencing the current digital operational resilience situation on the basis of the '
                                     'number of major ICT-related incidents reported and the effectiveness of preventive '
                                     'measures;\n'
                                     '(g) implementing digital operational resilience testing, in accordance with Chapter IV '
                                     'of this Regulation;\n'
                                     '(h) outlining a communication strategy in the event of ICT-related incidents the '
                                     'disclosure of which is required in accordance with Article 14.',
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-TPM-03.3: Does the organization address identified weaknesses or deficiencies in the '
                                   'security of the supply chain .',
                                   'Q-TPM-03.2: Does the organization utilize security safeguards to limit harm from potential '
                                   "adversaries who identify and target the organization's supply chain? .",
                                   'Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.'],
          'objective_title': 'Article 6.9: Financial entities may, in the context of the digital operational resilience '
                             'strategy referred to in paragraph 8, define a holistic ICT multi-vendor strategy, at group or '
                             'entity level, showing key dependencies on ICT third-party service providers and explaining the '
                             'rationale behind the procurement mix of ICT third-party service providers.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IAO-02.4: Does the organization produce a Security Assessment Report (SAR) at the '
                                   'conclusion of a security assessment to certify the results of the assessment and assist '
                                   'with any remediation actions?.',
                                   'Q-IAO-02.3: Does the organization accept and respond to the results of external '
                                   'assessments that are performed by impartial, external organizations? .',
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
                                   'intended and producing the desired outcome with respect to meeting expected '
                                   'requirements?.'],
          'objective_title': 'Article 6.10: Financial entities may, in accordance with Union and national sectoral law, '
                             'outsource the tasks of verifying compliance with ICT risk management requirements to intra-group '
                             'or external undertakings. In case of such outsourcing, the financial entity remains fully '
                             'responsible for the verification of compliance with the ICT risk management requirements.',
          'requirement_description': None,
          'subchapter': 'Article 6: ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-CAP-03: Does the organization conducted capacity planning so that necessary capacity for '
                                   'information processing, telecommunications and environmental support will exist during '
                                   'contingency operations? .',
                                   'Q-CAP-01: Does the organization facilitate the implementation of capacity management '
                                   'controls to ensure optimal system performance to meet expected and anticipated future '
                                   'capacity requirements?.'],
          'objective_title': 'Article 7.1:  ICT systems, protocols and tools',
          'requirement_description': '\n'
                                     'In order to address and manage ICT risk, financial entities shall use and maintain '
                                     'updated ICT systems, protocols and tools that are:\n'
                                     '(a) appropriate to the magnitude of operations supporting the conduct of their '
                                     'activities, in accordance with the proportionality principle as referred to in Article '
                                     '4;\n'
                                     '(b) reliable;\n'
                                     '(c) equipped with sufficient capacity to accurately process the data necessary for the '
                                     'performance of activities and the timely provision of services, and to deal with peak '
                                     'orders, message or transaction volumes, as needed, including where new technology is '
                                     'introduced;\n'
                                     '(d) technologically resilient in order to adequately deal with additional information '
                                     'processing needs as required under stressed market conditions or other adverse '
                                     'situations.',
          'subchapter': 'Article 7: ICT systems, protocols and tools'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-AST-04.2: Does the organization ensure control applicability is appropriately-determined '
                                   'for systems, applications, services and third parties by graphically representing '
                                   'applicable boundaries?.',
                                   'Q-AST-04.3: Does the organization create and maintain a current inventory of systems, '
                                   'applications and services that are in scope for statutory, regulatory and/or contractual '
                                   'compliance obligations that provides sufficient detail to determine control applicability, '
                                   'based on asset scope categorization?.',
                                   'Q-AST-04.1: Does the organization determine cybersecurity and privacy control '
                                   'applicability by identifying, assigning and documenting the appropriate asset scope '
                                   'categorization for all systems, applications, services and personnel (internal and '
                                   'third-parties)?.',
                                   'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain '
                                   "sufficient detail to assess the security of the network's architecture;  -  Reflect the "
                                   'current architecture of the network environment; and  -  Document all sensitive/regulated '
                                   'data flows?.',
                                   'Q-AST-03.1: Does the organization include capturing the name, position and/or role of '
                                   'individuals responsible/accountable for administering assets as part of the technology '
                                   'asset inventory process?.',
                                   'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, '
                                   'individual, or responsible organization level to establish a common understanding of '
                                   'requirements for asset protection?.',
                                   'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-AST-01: Does the organization facilitate the implementation of asset management '
                                   'controls?.'],
          'objective_title': 'Article 8.1: As part of the ICT risk management framework referred to in Article 6(1), financial '
                             'entities shall identify, classify and adequately document all ICT supported business functions, '
                             'roles and responsibilities, the information assets and ICT assets supporting those functions, '
                             'and their roles and dependencies in relation to ICT risk. Financial entities shall review as '
                             'needed, and at least yearly, the adequacy of this classification and of any relevant '
                             'documentation.',
          'requirement_description': None,
          'subchapter': 'Article 8: Identification'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-03: Does the organization identify and assign a risk ranking to newly discovered '
                                   'security vulnerabilities using reputable outside sources for security vulnerability '
                                   'information? .',
                                   'Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the '
                                   'continuous monitoring strategy that includes monitoring the effectiveness of security & '
                                   'privacy controls, compliance and change management?.',
                                   'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, '
                                   'risk response and risk monitoring;  -  Constraints affecting risk assessments, risk '
                                   'response and risk monitoring;  -  The organizational risk tolerance; and  -  Priorities '
                                   'and trade-offs considered by the organization for managing risk?.',
                                   'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .'],
          'objective_title': 'Article 8.2: Financial entities shall, on a continuous basis, identify all sources of ICT risk, '
                             'in particular the risk exposure to and from other financial entities, and assess cyber threats '
                             'and ICT vulnerabilities relevant to their ICT supported business functions, information assets '
                             'and ICT assets. Financial entities shall review on a regular basis, and at least yearly, the '
                             'risk scenarios impacting them.',
          'requirement_description': None,
          'subchapter': 'Article 8: Identification'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, '
                                   'prior to the implementation of the change?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .'],
          'objective_title': 'Article 8.3: Financial entities, other than microenterprises, shall perform a risk assessment '
                             'upon each major change in the network and information system infrastructure, in the processes or '
                             'procedures affecting their ICT supported business functions, information assets or ICT assets.',
          'requirement_description': None,
          'subchapter': 'Article 8: Identification'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-AST-02.8: Does the organization create and maintain a map of technology assets where '
                                   'sensitive/regulated data is stored, transmitted or processed?.',
                                   'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain '
                                   "sufficient detail to assess the security of the network's architecture;  -  Reflect the "
                                   'current architecture of the network environment; and  -  Document all sensitive/regulated '
                                   'data flows?.'],
          'objective_title': 'Article 8.4: Financial entities shall identify all information assets and ICT assets, including '
                             'those on remote sites, network resources and hardware equipment, and shall map those considered '
                             'critical. They shall map the configuration of the information assets and ICT assets and the '
                             'links and interdependencies between the different information assets and ICT assets.',
          'requirement_description': None,
          'subchapter': 'Article 8: Identification'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of '
                                   'Third-Party Service Providers (TSP) that can potentially impact the Confidentiality, '
                                   "Integrity, Availability and/or Safety (CIAS) of the organization's systems, applications, "
                                   'services and data?.'],
          'objective_title': 'Article 8.5: Financial entities shall identify and document all processes that are dependent on '
                             'ICT third-party service providers, and shall identify interconnections with ICT third-party '
                             'service providers that provide services that support critical or important functions.',
          'requirement_description': None,
          'subchapter': 'Article 8: Identification'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-AST-02.3: Does the organization prevent system components from being duplicated in other '
                                   'asset inventories? .',
                                   'Q-AST-02.2: Does the organization use automated mechanisms to detect and alert upon the '
                                   'detection of unauthorized hardware, software and firmware components?.',
                                   'Q-AST-02.1: Does the organization update asset inventories as part of component '
                                   'installations, removals and asset upgrades? .',
                                   'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-AST-03.2: Does the organization govern the chronology of the origin, development, '
                                   'ownership, location and changes to a system, system components and associated data?.'],
          'objective_title': 'Article 8.6: For the purposes of paragraphs 1, 4 and 5, financial entities shall maintain '
                             'relevant inventories and update them periodically and every time any major change as referred to '
                             'in paragraph 3 occurs.',
          'requirement_description': None,
          'subchapter': 'Article 8: Identification'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .'],
          'objective_title': 'Article 8.7: Financial entities, other than microenterprises, shall on a regular basis, and at '
                             'least yearly, conduct a specific ICT risk assessment on all legacy ICT systems and, in any case '
                             'before and after connecting technologies, applications or systems.',
          'requirement_description': None,
          'subchapter': 'Article 8: Identification'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-MON-16: Does the organization detect and respond to anomalous behavior that could '
                                   'indicate account compromise or other malicious activities?.',
                                   'Q-MON-06: Does the organization provide an event log report generation capability to aid '
                                   'in detecting and assessing anomalous activities? .',
                                   'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.',
                                   'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .',
                                   'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or '
                                   'similar automated tool, to support near real-time analysis and incident escalation?.',
                                   'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS '
                                   '/ IPS) technologies on critical systems, key network segments and network choke points?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.'],
          'objective_title': 'Article 9.1: For the purposes of adequately protecting ICT systems and with a view to organising '
                             'response measures, financial entities shall continuously monitor and control the security and '
                             'functioning of ICT systems and tools and shall minimise the impact of ICT risk on ICT systems '
                             'through the deployment of appropriate ICT security tools, policies and procedures.',
          'requirement_description': None,
          'subchapter': 'Article 9: Protection and prevention'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.',
                                   'Q-BCD-10: Does the organization reduce the likelihood of a single point of failure with '
                                   'primary telecommunications services?.',
                                   'Q-BCD-09: Does the organization establish an alternate processing site that provides '
                                   'security measures equivalent to that of the primary site?.',
                                   'Q-BCD-08: Does the organization establish an alternate storage site that includes both the '
                                   'assets and necessary agreements to permit the storage and recovery of system backup '
                                   'information? .',
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
          'objective_title': 'Article 9.2: Financial entities shall design, procure and implement ICT security policies, '
                             'procedures, protocols and tools that aim to ensure the resilience, continuity and availability '
                             'of ICT systems, in particular for those supporting critical or important functions, and to '
                             'maintain high standards of availability, authenticity, integrity and confidentiality of data, '
                             'whether at rest, in use or in transit.',
          'requirement_description': None,
          'subchapter': 'Article 9: Protection and prevention'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-13: Does the organization protect backup and restoration hardware and software?.',
                                   'Q-BCD-12.3: Does the organization utilize electronic discovery (eDiscovery) that covers '
                                   'current and archived communication transactions?.',
                                   'Q-BCD-12.4: Does the organization restore systems, applications and/or services within '
                                   'organization-defined restoration time-periods from configuration-controlled and '
                                   'integrity-protected information; representing a known, operational state for the asset?.',
                                   'Q-BCD-12.2: Does the organization implement real-time or near-real-time failover '
                                   'capability to maintain availability of critical systems, applications and/or services?.',
                                   'Q-BCD-12.1: Does the organization utilize specialized backup mechanisms that will allow '
                                   'transaction recovery for transaction-based applications and services in accordance with '
                                   'Recovery Point Objectives (RPOs)?.',
                                   'Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems '
                                   'to a known state after a disruption, compromise or failure? .'],
          'objective_title': 'Article 9.3: In order to achieve the objectives referred to in paragraph 2, financial entities '
                             'shall use ICT solutions and processes that are appropriate in accordance with Article 4. Those '
                             'ICT solutions and processes shall:',
          'requirement_description': '(a) ensure the security of the means of transfer of data;\n'
                                     '(b) minimise the risk of corruption or loss of data, unauthorised access and technical '
                                     'flaws that may hinder business activity;\n'
                                     '(c) prevent the lack of availability, the impairment of the authenticity and integrity, '
                                     'the breaches of confidentiality and the loss of data;\n'
                                     '(d) ensure that data is protected from risks arising from data management, including '
                                     'poor administration, processing-related risks and human error.',
          'subchapter': 'Article 9: Protection and prevention'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-CPL-03: Does the organization ensure managers regularly review the processes and '
                                   'documented procedures within their area of responsibility to adhere to appropriate '
                                   'security policies, standards and other applicable requirements?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-NET-14.2: Does the organization cryptographically protect the confidentiality and '
                                   'integrity of remote access sessions (e.g., VPN)?.',
                                   'Q-NET-13: Does the organization protect the confidentiality, integrity and availability of '
                                   'electronic messaging communications?.',
                                   'Q-NET-10.2: Does the organization perform data origin authentication and data integrity '
                                   'verification on the Domain Name Service (DNS) resolution responses received from '
                                   'authoritative sources when requested by client systems? .',
                                   'Q-NET-09: Does the organization protect the authenticity and integrity of communications '
                                   'sessions? .',
                                   'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect '
                                   'and report unauthorized changes to system files and configurations?.',
                                   'Q-END-02: Does the organization protect the confidentiality, integrity, availability and '
                                   'safety of endpoint devices?.',
                                   'Q-CRY-06: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality and integrity of non-console administrative access?.',
                                   'Q-CRY-05.1: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality and integrity of sensitive/regulated data residing on storage media?.',
                                   'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of '
                                   'data being transmitted? .',
                                   'Q-AST-18: Does the organization provision and protect the confidentiality, integrity and '
                                   'authenticity of product supplier keys and data that can be used as a roots of trust basis '
                                   'for integrity verification?.'],
          'objective_title': 'Article 9.4: As part of the ICT risk management framework referred to in Article 6(1), financial '
                             'entities shall:',
          'requirement_description': '(a) develop and document an information security policy defining rules to protect the '
                                     'availability, authenticity, integrity and confidentiality of data, information assets '
                                     'and ICT assets, including those of their customers, where applicable;\n'
                                     '(b) following a risk-based approach, establish a sound network and infrastructure '
                                     'management structure using appropriate techniques, methods and protocols that may '
                                     'include implementing automated mechanisms to isolate affected information assets in the '
                                     'event of cyber-attacks;\n'
                                     '(c) implement policies that limit the physical or logical access to information assets '
                                     'and ICT assets to what is required for legitimate and approved functions and activities '
                                     'only, and establish to that end a set of policies, procedures and controls that address '
                                     'access rights and ensure a sound administration thereof;\n'
                                     '(d) implement policies and protocols for strong authentication mechanisms, based on '
                                     'relevant standards and dedicated control systems, and protection measures of '
                                     'cryptographic keys whereby data is encrypted based on results of approved data '
                                     'classification and ICT risk assessment processes;\n'
                                     '(e) implement documented policies, procedures and controls for ICT change management, '
                                     'including changes to software, hardware, firmware components, systems or security '
                                     'parameters, that are based on a risk assessment approach and are an integral part of the '
                                     "financial entity's overall change management process, in order to ensure that all "
                                     'changes to ICT systems are recorded, tested, assessed, approved, implemented and '
                                     'verified in a controlled manner;\n'
                                     '(f) have appropriate and comprehensive documented policies for patches and updates.\n'
                                     'For the purposes of the first subparagraph, point (b), financial entities shall design '
                                     'the network connection infrastructure in a way that allows it to be instantaneously '
                                     'severed or segmented in order to minimise and prevent contagion, especially for '
                                     'interconnected financial processes.\n'
                                     'For the purposes of the first subparagraph, point (e), the ICT change management process '
                                     'shall be approved by appropriate lines of management and shall have specific protocols '
                                     'in place.',
          'subchapter': 'Article 9: Protection and prevention'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-MON-16: Does the organization detect and respond to anomalous behavior that could '
                                   'indicate account compromise or other malicious activities?.',
                                   'Q-MON-06: Does the organization provide an event log report generation capability to aid '
                                   'in detecting and assessing anomalous activities? .',
                                   'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.',
                                   'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .',
                                   'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or '
                                   'similar automated tool, to support near real-time analysis and incident escalation?.',
                                   'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS '
                                   '/ IPS) technologies on critical systems, key network segments and network choke points?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.'],
          'objective_title': 'Article 9.1: Financial entities shall have in place mechanisms to promptly detect anomalous '
                             'activities, in accordance with Article 17, including ICT network performance issues and '
                             'ICT-related incidents, and to identify potential material single points of failure.\n'
                             'All detection mechanisms referred to in the first subparagraph shall be regularly tested in '
                             'accordance with Article 25.',
          'requirement_description': None,
          'subchapter': 'Article 9: Protection and prevention'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-MON-11: Does the organization monitor for evidence of unauthorized exfiltration or '
                                   'disclosure of non-public information? .',
                                   'Q-MON-11.2: Does the organization detect unauthorized network services and alert incident '
                                   'response personnel? .',
                                   'Q-MON-11.1: Does the organization analyze network traffic to detect covert data '
                                   'exfiltration?.',
                                   'Q-MON-01.11: Does the organization alert incident response personnel of detected '
                                   'suspicious events and implement actions to terminate suspicious events?.'],
          'objective_title': 'Article 10.2: The detection mechanisms referred to in paragraph 1 shall enable multiple layers '
                             'of control, define alert thresholds and criteria to trigger and initiate ICT-related incident '
                             'response processes, including automatic alert mechanisms for relevant staff in charge of '
                             'ICT-related incident response.',
          'requirement_description': None,
          'subchapter': 'Article 10: Detection'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-MON-04: Does the organization allocate and proactively manage sufficient event log '
                                   'storage capacity to reduce the likelihood of such capacity being exceeded?.',
                                   'Q-MON-05: Does the organization alert appropriate personnel in the event of a log '
                                   'processing failure and take actions to remedy the disruption?.',
                                   'Q-MON-05.1: Does the organization provide 24x7x365 near real-time alerting capability when '
                                   'an event log processing failure occurs?.',
                                   'Q-MON-05.2: Does the organization alert appropriate personnel when the allocated volume '
                                   'reaches an organization-defined percentage of maximum event log storage capacity?.',
                                   'Q-MON-01.10: Does the organization monitor deactivated accounts for attempted usage?.',
                                   'Q-MON-01.14: Does the organization implement enhanced activity monitoring for individuals '
                                   'who have been identified as posing an increased level of risk? .',
                                   'Q-MON-01.15: Does the organization implement enhanced activity monitoring for privileged '
                                   'users?.'],
          'objective_title': 'Article 10.3: Financial entities shall devote sufficient resources and capabilities to monitor '
                             'user activity, the occurrence of ICT anomalies and ICT-related incidents, in particular '
                             'cyber-attacks.',
          'requirement_description': None,
          'subchapter': 'Article 10: Detection'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-MON-08: Does the organization protect event logs and audit tools from unauthorized '
                                   'access, modification and deletion?.',
                                   'Q-MON-08.3: Does the organization protect the integrity of event logs and audit tools with '
                                   'cryptographic mechanisms? .'],
          'objective_title': 'Article 10.4: Data reporting service providers shall, in addition, have in place systems that '
                             'can effectively check trade reports for completeness, identify omissions and obvious errors, and '
                             'request re-transmission of those reports.',
          'requirement_description': None,
          'subchapter': 'Article 10: Detection'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-01.2: Does the organization coordinate internal contingency plans with the '
                                   'contingency plans of external service providers to ensure that contingency requirements '
                                   'can be satisfied?.',
                                   'Q-BCD-01.1: Does the organization coordinate contingency plan development with internal '
                                   'and external elements responsible for related plans? .',
                                   'Q-BCD-01: Does the organization facilitate the implementation of contingency planning '
                                   'controls?.'],
          'objective_title': 'Article 11.1: As part of the ICT risk management framework referred to in Article 6(1) and based '
                             'on the identification requirements set out in Article 8, financial entities shall put in place a '
                             'comprehensive ICT business continuity policy, which may be adopted as a dedicated specific '
                             'policy, forming an integral part of the overall business continuity policy of the financial '
                             'entity.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.',
                                   'Q-IRO-02.5: Does the organization coordinate with approved third-parties to achieve a '
                                   'cross-organization perspective on incident awareness and more effective incident '
                                   'responses? .',
                                   'Q-IRO-02.4: Does the organization identify classes of incidents and actions to take to '
                                   'ensure the continuation of organizational missions and business functions?.',
                                   'Q-IRO-02.3: Does the organization dynamically reconfigure information system components as '
                                   'part of the incident response capability? .',
                                   'Q-IRO-02.6: Does the organization automatically disable systems involved in an incident '
                                   'that meet organizational criteria to be automatically disabled upon detection?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'Article 11.2: Financial entities shall implement the ICT business continuity policy through '
                             'dedicated, appropriate and documented arrangements, plans, procedures and mechanisms aiming to:',
          'requirement_description': "(a) ensure the continuity of the financial entity's critical or important functions;\n"
                                     '(b) quickly, appropriately and effectively respond to, and resolve, all ICT-related '
                                     'incidents in a way that limits damage and prioritises the resumption of activities and '
                                     'recovery actions;\n'
                                     '(c) activate, without delay, dedicated plans that enable containment measures, processes '
                                     'and technologies suited to each type of ICT-related incident and prevent further damage, '
                                     'as well as tailored response and recovery procedures established in accordance with '
                                     'Article 12;\n'
                                     '(d) estimate preliminary impacts, damages and losses;\n'
                                     '(e) set out communication and crisis management actions that ensure that updated '
                                     'information is transmitted to all relevant internal staff and external stakeholders in '
                                     'accordance with Article 14, and report to the competent authorities in accordance with '
                                     'Article 19.',
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-04.3: Does the organization use qualitative and quantitative data from incident '
                                   'response testing to:  - Determine the effectiveness of incident response processes; - '
                                   'Continuously improve incident response processes; and - Provide incident response measures '
                                   'and metrics that are accurate, consistent, and in a reproducible format?.',
                                   'Q-IRO-04.2: Does the organization regularly review and modify incident response practices '
                                   'to incorporate lessons learned, business process changes and industry developments, as '
                                   'necessary?.'],
          'objective_title': 'Article 11.3: As part of the ICT risk management framework referred to in Article 6(1), '
                             'financial entities shall implement associated ICT response and recovery plans which, in the case '
                             'of financial entities other than microenterprises, shall be subject to independent internal '
                             'audit reviews.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-11.5: Does the organization utilize sampling of available backups to test recovery '
                                   'capabilities as part of business continuity plan testing?.',
                                   'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of '
                                   'the backup process, as well as the integrity and availability of the data? .',
                                   'Q-BCD-06: Does the organization keep contingency plans current with business needs, '
                                   'technology changes and feedback from contingency plan testing activities?.',
                                   'Q-BCD-04.2: Does the organization test the contingency plan at the alternate processing '
                                   'site to both familiarize contingency personnel with the facility and evaluate the '
                                   'capabilities of the alternate processing site to support contingency operations? .',
                                   'Q-BCD-04.1: Does the organization coordinate contingency plan testing with internal and '
                                   'external elements responsible for related plans? .',
                                   'Q-BCD-04: Does the organization conduct tests and/or exercises to evaluate the contingency '
                                   "plan's effectiveness and the organization's readiness to execute the plan?."],
          'objective_title': 'Article 11.4: Financial entities shall put in place, maintain and periodically test appropriate '
                             'ICT business continuity plans, notably with regard to critical or important functions outsourced '
                             'or contracted through arrangements with ICT third-party service providers.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-04.3: Does the organization use qualitative and quantitative data from incident '
                                   'response testing to:  - Determine the effectiveness of incident response processes; - '
                                   'Continuously improve incident response processes; and - Provide incident response measures '
                                   'and metrics that are accurate, consistent, and in a reproducible format?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-BCD-06: Does the organization keep contingency plans current with business needs, '
                                   'technology changes and feedback from contingency plan testing activities?.',
                                   'Q-BCD-01.2: Does the organization coordinate internal contingency plans with the '
                                   'contingency plans of external service providers to ensure that contingency requirements '
                                   'can be satisfied?.',
                                   'Q-BCD-01.1: Does the organization coordinate contingency plan development with internal '
                                   'and external elements responsible for related plans? .'],
          'objective_title': 'Article 11.5: As part of the overall business continuity policy, financial entities shall '
                             'conduct a business impact analysis (BIA) of their exposures to severe business disruptions. '
                             'Under the BIA, financial entities shall assess the potential impact of severe business '
                             'disruptions by means of quantitative and qualitative criteria, using internal and external data '
                             'and scenario analysis, as appropriate. The BIA shall consider the criticality of identified and '
                             'mapped business functions, support processes, third-party dependencies and information assets, '
                             'and their interdependencies. Financial entities shall ensure that ICT assets and ICT services '
                             'are designed and used in full alignment with the BIA, in particular with regard to adequately '
                             'ensuring the redundancy of all critical components.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-04.3: Does the organization use qualitative and quantitative data from incident '
                                   'response testing to:  - Determine the effectiveness of incident response processes; - '
                                   'Continuously improve incident response processes; and - Provide incident response measures '
                                   'and metrics that are accurate, consistent, and in a reproducible format?.',
                                   'Q-IRO-06.1: Does the organization coordinate incident response testing with organizational '
                                   'elements responsible for related plans? .',
                                   'Q-IRO-06: Does the organization formally test incident response capabilities through '
                                   'realistic exercises to determine the operational effectiveness of those capabilities?.',
                                   'Q-BCD-06: Does the organization keep contingency plans current with business needs, '
                                   'technology changes and feedback from contingency plan testing activities?.',
                                   "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' "
                                   'activity every time the contingency plan is activated?.',
                                   'Q-BCD-04.2: Does the organization test the contingency plan at the alternate processing '
                                   'site to both familiarize contingency personnel with the facility and evaluate the '
                                   'capabilities of the alternate processing site to support contingency operations? .',
                                   'Q-BCD-04.1: Does the organization coordinate contingency plan testing with internal and '
                                   'external elements responsible for related plans? .',
                                   'Q-BCD-04: Does the organization conduct tests and/or exercises to evaluate the contingency '
                                   "plan's effectiveness and the organization's readiness to execute the plan?."],
          'objective_title': 'Article 11.6: As part of their comprehensive ICT risk management, financial entities shall:',
          'requirement_description': '(a) test the ICT business continuity plans and the ICT response and recovery plans in '
                                     'relation to ICT systems supporting all functions at least yearly, as well as in the '
                                     'event of any substantive changes to ICT systems supporting critical or important '
                                     'functions;\n'
                                     '(b) test the crisis communication plans established in accordance with Article 14.\n'
                                     'For the purposes of the first subparagraph, point (a), financial entities, other than '
                                     'microenterprises, shall include in the testing plans scenarios of cyber-attacks and '
                                     'switchovers between the primary ICT infrastructure and the redundant capacity, backups '
                                     'and redundant facilities necessary to meet the obligations set out in Article 12.\n'
                                     'Financial entities shall regularly review their ICT business continuity policy and ICT '
                                     'response and recovery plans, taking into account the results of tests carried out in '
                                     'accordance with the first subparagraph and recommendations stemming from audit checks or '
                                     'supervisory reviews.',
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-14: Does the organization maintain incident response contacts with applicable '
                                   'regulatory and law enforcement agencies? .',
                                   'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   'Q-IRO-05: Does the organization train personnel in their incident response roles and '
                                   'responsibilities?.'],
          'objective_title': 'Article 11.7: Financial entities, other than microenterprises, shall have a crisis management '
                             'function, which, in the event of activation of their ICT business continuity plans or ICT '
                             'response and recovery plans, shall, inter alia, set out clear procedures to manage internal and '
                             'external crisis communications in accordance with Article 14.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-09.1: Does the organization use automated mechanisms to assist in the tracking, '
                                   'collection and analysis of information from actual and potential cybersecurity and privacy '
                                   'incidents?.',
                                   'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .'],
          'objective_title': 'Article 11.8: Financial entities shall keep readily accessible records of activities before and '
                             'during disruption events when their ICT business continuity plans and ICT response and recovery '
                             'plans are activated.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of '
                                   'the backup process, as well as the integrity and availability of the data? .',
                                   'Q-BCD-04: Does the organization conduct tests and/or exercises to evaluate the contingency '
                                   "plan's effectiveness and the organization's readiness to execute the plan?.",
                                   'Q-BCD-04.1: Does the organization coordinate contingency plan testing with internal and '
                                   'external elements responsible for related plans? .'],
          'objective_title': 'Article 11.9: Central securities depositories shall provide the competent authorities with '
                             'copies of the results of the ICT business continuity tests, or of similar exercises.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .'],
          'objective_title': 'Article 11.10:  Financial entities, other than microenterprises, shall report to the competent '
                             'authorities, upon their request, an estimation of aggregated annual costs and losses caused by '
                             'major ICT-related incidents.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': [],
          'objective_title': 'Article 11.11:  In accordance with Article 16 of Regulations (EU) No 1093/2010, (EU) No '
                             '1094/2010 and (EU) No 1095/2010, the ESAs, through the Joint Committee, shall by 17 July 2024 '
                             'develop common guidelines on the estimation of aggregated annual costs and losses referred to in '
                             'paragraph 10.',
          'requirement_description': None,
          'subchapter': 'Article 11: Response and recovery'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-11.5: Does the organization utilize sampling of available backups to test recovery '
                                   'capabilities as part of business continuity plan testing?.',
                                   'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of '
                                   'the backup process, as well as the integrity and availability of the data? .',
                                   'Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.'],
          'objective_title': 'Article 12.1: For the purpose of ensuring the restoration of ICT systems and data with minimum '
                             'downtime, limited disruption and loss, as part of their ICT risk management framework, financial '
                             'entities shall develop and document:',
          'requirement_description': '(a) backup policies and procedures specifying the scope of the data that is subject to '
                                     'the backup and the minimum frequency of the backup, based on the criticality of '
                                     'information or the confidentiality level of the data;\n'
                                     '(b) restoration and recovery procedures and methods.',
          'subchapter': 'Article 12: Backup policies and procedures, restoration and recovery procedures and methods'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-11.5: Does the organization utilize sampling of available backups to test recovery '
                                   'capabilities as part of business continuity plan testing?.',
                                   'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized '
                                   'disclosure and/or modification of backup information/.',
                                   'Q-BCD-11.6: Does the organization transfer backup data to the alternate storage site at a '
                                   'rate that is capable of meeting both Recovery Time Objectives (RTOs) and Recovery Point '
                                   'Objectives (RPOs)?.',
                                   'Q-BCD-08: Does the organization establish an alternate storage site that includes both the '
                                   'assets and necessary agreements to permit the storage and recovery of system backup '
                                   'information? .'],
          'objective_title': 'Article 12.2: Financial entities shall set up backup systems that can be activated in accordance '
                             'with the backup policies and procedures, as well as restoration and recovery procedures and '
                             'methods. The activation of backup systems shall not jeopardise the security of the network and '
                             'information systems or the availability, authenticity, integrity or confidentiality of data. '
                             'Testing of the backup procedures and restoration and recovery procedures and methods shall be '
                             'undertaken periodically.',
          'requirement_description': None,
          'subchapter': 'Article 12: Backup policies and procedures, restoration and recovery procedures and methods'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-11.6: Does the organization transfer backup data to the alternate storage site at a '
                                   'rate that is capable of meeting both Recovery Time Objectives (RTOs) and Recovery Point '
                                   'Objectives (RPOs)?.',
                                   'Q-BCD-11.2: Does the organization store backup copies of critical software and other '
                                   'security-related information in a separate facility or in a fire-rated container that is '
                                   'not collocated with the system being backed up?.'],
          'objective_title': 'Article 12.3: When restoring backup data using own systems, financial entities shall use ICT '
                             'systems that are physically and logically segregated from the source ICT system. The ICT systems '
                             'shall be securely protected from any unauthorised access or ICT corruption and allow for the '
                             'timely restoration of services making use of data and system backups as necessary.',
          'requirement_description': None,
          'subchapter': 'Article 12: Backup policies and procedures, restoration and recovery procedures and methods'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-08: Does the organization establish an alternate storage site that includes both the '
                                   'assets and necessary agreements to permit the storage and recovery of system backup '
                                   'information? .',
                                   'Q-BCD-01.4: Does the organization configure the alternate storage site to facilitate '
                                   'recovery operations in accordance with Recovery Time Objectives (RTOs) and Recovery Point '
                                   'Objectives (RPOs)?.',
                                   'Q-CAP-03: Does the organization conducted capacity planning so that necessary capacity for '
                                   'information processing, telecommunications and environmental support will exist during '
                                   'contingency operations? .'],
          'objective_title': 'Article 12.4: Financial entities, other than microenterprises, shall maintain redundant ICT '
                             'capacities equipped with resources, capabilities and functions that are adequate to ensure '
                             'business needs. Microenterprises shall assess the need to maintain such redundant ICT capacities '
                             'based on their risk profile.',
          'requirement_description': '\n'
                                     'For central counterparties, the recovery plans shall enable the recovery of all '
                                     'transactions at the time of disruption to allow the central counterparty to continue to '
                                     'operate with certainty and to complete settlement on the scheduled date.\n'
                                     'Data reporting service providers shall additionally maintain adequate resources and have '
                                     'back-up and restoration facilities in place in order to offer and maintain their '
                                     'services at all times.',
          'subchapter': 'Article 12: Backup policies and procedures, restoration and recovery procedures and methods'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-09.5: Does the organization plan and prepare for both natural and manmade '
                                   'circumstances that preclude returning to the primary processing site?.',
                                   'Q-BCD-09.2: Does the organization identify potential accessibility problems to the '
                                   'alternate processing site and possible mitigation actions, in the event of an area-wide '
                                   'disruption or disaster?.',
                                   'Q-BCD-09.1: Does the organization separate the alternate processing site from the primary '
                                   'processing site to reduce susceptibility to similar threats?.',
                                   'Q-BCD-09: Does the organization establish an alternate processing site that provides '
                                   'security measures equivalent to that of the primary site?.'],
          'objective_title': 'Article 12.5: Central securities depositories shall maintain at least one secondary processing '
                             'site endowed with adequate resources, capabilities, functions and staffing arrangements to '
                             'ensure business needs.',
          'requirement_description': None,
          'subchapter': 'Article 12: Backup policies and procedures, restoration and recovery procedures and methods'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-BCD-02.2: Does the organization plan for the continuance of essential missions and '
                                   'business functions with little or no loss of operational continuity and sustain that '
                                   'continuity until full system restoration at primary processing and/or storage sites?.',
                                   'Q-BCD-02.1: Does the organization plan for the resumption of all missions and business '
                                   "functions within Recovery Time Objectives (RTOs) of the contingency plan's activation?.",
                                   'Q-BCD-02: Does the organization identify and document the critical systems, applications '
                                   'and services that support essential missions and business functions?.'],
          'objective_title': 'Article 12.6: In determining the recovery time and recovery point objectives for each function, '
                             'financial entities shall take into account whether it is a critical or important function and '
                             'the potential overall impact on market efficiency. Such time objectives shall ensure that, in '
                             'extreme scenarios, the agreed service levels are met.',
          'requirement_description': 'The secondary processing site shall be:\n'
                                     '(a) located at a geographical distance from the primary processing site to ensure that '
                                     'it bears a distinct risk profile and to prevent it from being affected by the event '
                                     'which has affected the primary site;\n'
                                     '(b) capable of ensuring the continuity of critical or important functions identically to '
                                     'the primary site, or providing the level of services necessary to ensure that the '
                                     'financial entity performs its critical operations within the recovery objectives;\n'
                                     "(c) immediately accessible to the financial entity's staff to ensure continuity of "
                                     'critical or important functions in the event that the primary processing site has become '
                                     'unavailable.',
          'subchapter': 'Article 12: Backup policies and procedures, restoration and recovery procedures and methods'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-17-CM: Does the organization establish a post-incident procedure to verify the '
                                   'integrity of the affected systems before restoring them to normal operations?.'],
          'objective_title': 'Article 12.7: When recovering from an ICT-related incident, financial entities shall perform '
                             'necessary checks, including any multiple checks and reconciliations, in order to ensure that the '
                             'highest level of data integrity is maintained. These checks shall also be performed when '
                             'reconstructing data from external stakeholders, in order to ensure that all data is consistent '
                             'between systems.',
          'requirement_description': None,
          'subchapter': 'Article 12: Backup policies and procedures, restoration and recovery procedures and methods'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-THR-05: Does the organization utilize security awareness training on recognizing and '
                                   'reporting potential indicators of insider threat?.',
                                   'Q-THR-04: Does the organization implement an insider threat program that includes a '
                                   'cross-discipline insider threat incident handling team? .',
                                   'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
                                   'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the '
                                   'potential attack vectors that attackers could use to attack the organization? .',
                                   'Q-THR-01: Does the organization implement a threat awareness program that includes a '
                                   'cross-organization information-sharing capability? .',
                                   'Q-THR-06: Does the organization establish a Vulnerability Disclosure Program (VDP) to '
                                   'assist with the secure development and maintenance of products and services that receives '
                                   'unsolicited input from the public about vulnerabilities in organizational systems, '
                                   'services and processes?.',
                                   'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing '
                                   'basis and ensure assets are protected against known attacks? .',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-GOV-07: Does the organization establish contact with selected groups and associations '
                                   'within the cybersecurity & privacy communities to:   -  Facilitate ongoing cybersecurity '
                                   'and privacy education and training for organizational personnel;  -  Maintain currency '
                                   'with recommended cybersecurity and privacy practices, techniques and technologies; and  -  '
                                   'Share current security-related information including threats, vulnerabilities and '
                                   'incidents? .'],
          'objective_title': 'Article 13.1: Financial entities shall have in place capabilities and staff to gather '
                             'information on vulnerabilities and cyber threats, ICT-related incidents, in particular '
                             'cyber-attacks, and analyse the impact they are likely to have on their digital operational '
                             'resilience.',
          'requirement_description': None,
          'subchapter': 'Article 13: Learning and evolving'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ["Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' "
                                   'activity every time the contingency plan is activated?.',
                                   'Q-IRO-04.2: Does the organization regularly review and modify incident response practices '
                                   'to incorporate lessons learned, business process changes and industry developments, as '
                                   'necessary?.',
                                   'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .'],
          'objective_title': 'Article 13.2: Financial entities shall put in place post ICT-related incident reviews after a '
                             'major ICT-related incident disrupts their core activities, analysing the causes of disruption '
                             'and identifying required improvements to the ICT operations or within the ICT business '
                             'continuity policy referred to in Article 11.',
          'requirement_description': 'Financial entities, other than microenterprises, shall, upon request, communicate to the '
                                     'competent authorities, the changes that were implemented following post ICT-related '
                                     'incident reviews as referred to in the first subparagraph.\n'
                                     'The post ICT-related incident reviews referred to in the first subparagraph shall '
                                     'determine whether the established procedures were followed and the actions taken were '
                                     'effective, including in relation to the following:\n'
                                     '(a) the promptness in responding to security alerts and determining the impact of '
                                     'ICT-related incidents and their severity;\n'
                                     '(b) the quality and speed of performing a forensic analysis, where deemed appropriate;\n'
                                     '(c) the effectiveness of incident escalation within the financial entity;\n'
                                     '(d) the effectiveness of internal and external communication.',
          'subchapter': 'Article 13: Learning and evolving'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .',
                                   'Q-IRO-04.2: Does the organization regularly review and modify incident response practices '
                                   'to incorporate lessons learned, business process changes and industry developments, as '
                                   'necessary?.',
                                   "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' "
                                   'activity every time the contingency plan is activated?.'],
          'objective_title': 'Article 13.3: Lessons derived from the digital operational resilience testing carried out in '
                             'accordance with Articles 26 and 27 and from real life ICT-related incidents, in particular '
                             'cyber-attacks, along with challenges faced upon the activation of ICT business continuity plans '
                             'and ICT response and recovery plans, together with relevant information exchanged with '
                             'counterparts and assessed during supervisory reviews, shall be duly incorporated on a continuous '
                             'basis into the ICT risk assessment process. Those findings shall form the basis for appropriate '
                             'reviews of relevant components of the ICT risk management framework referred to in Article 6(1).',
          'requirement_description': None,
          'subchapter': 'Article 13: Learning and evolving'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.'],
          'objective_title': 'Article 13.4: Financial entities shall monitor the effectiveness of the implementation of their '
                             'digital operational resilience strategy set out in Article 6(8). They shall map the evolution of '
                             'ICT risk over time, analyse the frequency, types, magnitude and evolution of ICT-related '
                             'incidents, in particular cyber-attacks and their patterns, with a view to understanding the '
                             'level of ICT risk exposure, in particular in relation to critical or important functions, and '
                             'enhance the cyber maturity and preparedness of the financial entity.',
          'requirement_description': None,
          'subchapter': 'Article 13: Learning and evolving'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the '
                                   "organization's cybersecurity and privacy policies and standards? .",
                                   'Q-CPL-03.1: Does the organization utilize independent assessors to evaluate security & '
                                   'privacy controls at planned intervals or when the system, service or project undergoes '
                                   'significant changes?.',
                                   'Q-CPL-03: Does the organization ensure managers regularly review the processes and '
                                   'documented procedures within their area of responsibility to adhere to appropriate '
                                   'security policies, standards and other applicable requirements?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?."],
          'objective_title': 'Article 13.5: Senior ICT staff shall report at least yearly to the management body on the '
                             'findings referred to in paragraph 3 and put forward recommendations.',
          'requirement_description': None,
          'subchapter': 'Article 13: Learning and evolving'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .',
                                   'Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .'],
          'objective_title': 'Article 13.6: Financial entities shall develop ICT security awareness programmes and digital '
                             'operational resilience training as compulsory modules in their staff training schemes. Those '
                             'programmes and training shall be applicable to all employees and to senior management staff, and '
                             'shall have a level of complexity commensurate to the remit of their functions. Where '
                             'appropriate, financial entities shall also include ICT third-party service providers in their '
                             'relevant training schemes in accordance with Article 30(2), point (i).',
          'requirement_description': None,
          'subchapter': 'Article 13: Learning and evolving'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.',
                                   'Q-SEA-02: Does the organization develop an enterprise architecture, aligned with '
                                   'industry-recognized leading practices, with consideration for cybersecurity and privacy '
                                   'principles that addresses risk to organizational operations, assets, individuals, other '
                                   'organizations? .'],
          'objective_title': 'Article 13.7: Financial entities, other than microenterprises, shall monitor relevant '
                             'technological developments on a continuous basis, also with a view to understanding the possible '
                             'impact of the deployment of such new technologies on ICT security requirements and digital '
                             'operational resilience. They shall keep up-to-date with the latest ICT risk management '
                             'processes, in order to effectively combat current or new forms of cyber-attacks.',
          'requirement_description': None,
          'subchapter': 'Article 13: Learning and evolving'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.',
                                   'Q-IRO-14: Does the organization maintain incident response contacts with applicable '
                                   'regulatory and law enforcement agencies? .',
                                   'Q-GOV-06: Does the organization identify and document appropriate contacts within relevant '
                                   'law enforcement and regulatory bodies?.'],
          'objective_title': 'Article 14.1: As part of the ICT risk management framework referred to in Article 6(1), '
                             'financial entities shall have in place crisis communication plans enabling a responsible '
                             'disclosure of, at least, major ICT-related incidents or vulnerabilities to clients and '
                             'counterparts as well as to the public, as appropriate.',
          'requirement_description': None,
          'subchapter': 'Article 14: Communication'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-20: Does the organization have a written down policy to communicate about incidents '
                                   'to external and internal audience?.'],
          'objective_title': 'Article 14.2: As part of the ICT risk management framework, financial entities shall implement '
                             'communication policies for internal staff and for external stakeholders. Communication policies '
                             'for staff shall take into account the need to differentiate between staff involved in ICT risk '
                             'management, in particular the staff responsible for response and recovery, and staff that needs '
                             'to be informed.',
          'requirement_description': None,
          'subchapter': 'Article 14: Communication'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-IRO-20: Does the organization have a written down policy to communicate about incidents '
                                   'to external and internal audience?.'],
          'objective_title': 'Article 14.3: At least one person in the financial entity shall be tasked with implementing the '
                             'communication strategy for ICT-related incidents and fulfil the public and media function for '
                             'that purpose.',
          'requirement_description': None,
          'subchapter': 'Article 14: Communication'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': [],
          'objective_title': 'Article 15.1: Further harmonisation of ICT risk management tools, methods, processes and '
                             'policies',
          'requirement_description': '\n'
                                     'The ESAs shall, through the Joint Committee, in consultation with the European Union '
                                     'Agency on Cybersecurity (ENISA), develop common draft regulatory technical standards in '
                                     'order to:\n'
                                     '(a) specify further elements to be included in the ICT security policies, procedures, '
                                     'protocols and tools referred to in Article 9(2), with a view to ensuring the security of '
                                     'networks, enable adequate safeguards against intrusions and data misuse, preserve the '
                                     'availability, authenticity, integrity and confidentiality of data, including '
                                     'cryptographic techniques, and guarantee an accurate and prompt data transmission without '
                                     'major disruptions and undue delays;\n'
                                     '(b) develop further components of the controls of access management rights referred to '
                                     'in Article 9(4), point (c), and associated human resource policy specifying access '
                                     'rights, procedures for granting and revoking rights, monitoring anomalous behaviour in '
                                     'relation to ICT risk through appropriate indicators, including for network use patterns, '
                                     'hours, IT activity and unknown devices;\n'
                                     '(c) develop further the mechanisms specified in Article 10(1) enabling a prompt '
                                     'detection of anomalous activities and the criteria set out in Article 10(2) triggering '
                                     'ICT-related incident detection and response processes;\n'
                                     '(d) specify further the components of the ICT business continuity policy referred to in '
                                     'Article 11(1);\n'
                                     '(e) specify further the testing of ICT business continuity plans referred to in Article '
                                     '11(6) to ensure that such testing duly takes into account scenarios in which the quality '
                                     'of the provision of a critical or important function deteriorates to an unacceptable '
                                     'level or fails, and duly considers the potential impact of the insolvency, or other '
                                     'failures, of any relevant ICT third-party service provider and, where relevant, the '
                                     'political risks in the respective providers’ jurisdictions;\n'
                                     '(f) specify further the components of the ICT response and recovery plans referred to in '
                                     'Article 11(3);\n'
                                     '(g) specifying further the content and format of the report on the review of the ICT '
                                     'risk management framework referred to in Article 6(5);\n'
                                     'When developing those draft regulatory technical standards, the ESAs shall take into '
                                     'account the size and the overall risk profile of the financial entity, and the nature, '
                                     'scale and complexity of its services, activities and operations, while duly taking into '
                                     'consideration any specific feature arising from the distinct nature of activities across '
                                     'different financial services sectors.\n'
                                     'The ESAs shall submit those draft regulatory technical standards to the Commission by 17 '
                                     'January 2024.\n'
                                     'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'regulatory technical standards referred to in the first paragraph in accordance with '
                                     'Articles 10 to 14 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No '
                                     '1095/2010.',
          'subchapter': 'Article 15: Further harmonisation of ICT risk management tools, methods, processes and policies'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': [],
          'objective_title': 'Article 16.1: Articles 5 to 15 of this Regulation shall not apply to small and '
                             'non-interconnected investment firms, payment institutions exempted pursuant to Directive (EU) '
                             '2015/2366; institutions exempted pursuant to Directive 2013/36/EU in respect of which Member '
                             'States have decided not to apply the option referred to in Article 2(4) of this Regulation; '
                             'electronic money institutions exempted pursuant to Directive 2009/110/EC; and small institutions '
                             'for occupational retirement provision.',
          'requirement_description': 'Without prejudice to the first subparagraph, the entities listed in the first '
                                     'subparagraph shall:\n'
                                     '(a) put in place and maintain a sound and documented ICT risk management framework that '
                                     'details the mechanisms and measures aimed at a quick, efficient and comprehensive '
                                     'management of ICT risk, including for the protection of relevant physical components and '
                                     'infrastructures;\n'
                                     '(b) continuously monitor the security and functioning of all ICT systems;\n'
                                     '(c) minimise the impact of ICT risk through the use of sound, resilient and updated ICT '
                                     'systems, protocols and tools which are appropriate to support the performance of their '
                                     'activities and the provision of services and adequately protect availability, '
                                     'authenticity, integrity and confidentiality of data in the network and information '
                                     'systems;\n'
                                     '(d) allow sources of ICT risk and anomalies in the network and information systems to be '
                                     'promptly identified and detected and ICT-related incidents to be swiftly handled;\n'
                                     '(e) identify key dependencies on ICT third-party service providers;\n'
                                     '(f) ensure the continuity of critical or important functions, through business '
                                     'continuity plans and response and recovery measures, which include, at least, back-up '
                                     'and restoration measures;\n'
                                     '(g) test, on a regular basis, the plans and measures referred to in point (f), as well '
                                     'as the effectiveness of the controls implemented in accordance with points (a) and (c);\n'
                                     '(h) implement, as appropriate, relevant operational conclusions resulting from the tests '
                                     'referred to in point (g) and from post-incident analysis into the ICT risk assessment '
                                     'process and develop, according to needs and ICT risk profile, ICT security awareness '
                                     'programmes and digital operational resilience training for staff and management.',
          'subchapter': 'Article 16: Simplified ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': ['Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .'],
          'objective_title': 'Article 16.2: The ICT risk management framework referred to in paragraph 1, second subparagraph, '
                             'point (a), shall be documented and reviewed periodically and upon the occurrence of major '
                             'ICT-related incidents in compliance with supervisory instructions. It shall be continuously '
                             'improved on the basis of lessons derived from implementation and monitoring. A report on the '
                             'review of the ICT risk management framework shall be submitted to the competent authority upon '
                             'its request.',
          'requirement_description': None,
          'subchapter': 'Article 16: Simplified ICT risk management framework'},
         {'chapter_title': 'Chapter II: ICT Risk Management',
          'conformity_questions': [],
          'objective_title': 'Article 16.3: The ESAs shall, through the Joint Committee, in consultation with the ENISA, '
                             'develop common draft regulatory technical standards in order to:',
          'requirement_description': '(a) specify further the elements to be included in the ICT risk management framework '
                                     'referred to in paragraph 1, second subparagraph, point (a);\n'
                                     '(b) specify further the elements in relation to systems, protocols and tools to minimise '
                                     'the impact of ICT risk referred to in paragraph 1, second subparagraph, point (c), with '
                                     'a view to ensuring the security of networks, enabling adequate safeguards against '
                                     'intrusions and data misuse and preserving the availability, authenticity, integrity and '
                                     'confidentiality of data;\n'
                                     '(c) specify further the components of the ICT business continuity plans referred to in '
                                     'paragraph 1, second subparagraph, point (f);\n'
                                     '(d) specify further the rules on the testing of business continuity plans and ensure the '
                                     'effectiveness of the controls referred to in paragraph 1, second subparagraph, point (g) '
                                     'and ensure that such testing duly takes into account scenarios in which the quality of '
                                     'the provision of a critical or important function deteriorates to an unacceptable level '
                                     'or fails;\n'
                                     '(e) specify further the content and format of the report on the review of the ICT risk '
                                     'management framework referred to in paragraph 2.\n'
                                     'When developing those draft regulatory technical standards, the ESAs shall take into '
                                     'account the size and the overall risk profile of the financial entity, and the nature, '
                                     'scale and complexity of its services, activities and operations.\n'
                                     'The ESAs shall submit those draft regulatory technical standards to the Commission by 17 '
                                     'January 2024.\n'
                                     'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'regulatory technical standards referred to in the first subparagraph in accordance with '
                                     'Articles 10 to 14 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No '
                                     '1095/2010.',
          'subchapter': 'Article 16: Simplified ICT risk management framework'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 17.1: Financial entities shall define, establish and implement an ICT-related incident '
                             'management process to detect, manage and notify ICT-related incidents.',
          'requirement_description': None,
          'subchapter': 'Article 17: ICT-related incident management process'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 17.2: Financial entities shall record all ICT-related incidents and significant cyber '
                             'threats. Financial entities shall establish appropriate procedures and processes to ensure a '
                             'consistent and integrated monitoring, handling and follow-up of ICT-related incidents, to ensure '
                             'that root causes are identified, documented and addressed in order to prevent the occurrence of '
                             'such incidents.',
          'requirement_description': None,
          'subchapter': 'Article 17: ICT-related incident management process'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 17.3: The ICT-related incident management process referred to in paragraph 1 shall:',
          'requirement_description': '(a) put in place early warning indicators;\n'
                                     '(b) establish procedures to identify, track, log, categorise and classify ICT-related '
                                     'incidents according to their priority and severity and according to the criticality of '
                                     'the services impacted, in accordance with the criteria set out in Article 18(1);\n'
                                     '(c) assign roles and responsibilities that need to be activated for different '
                                     'ICT-related incident types and scenarios;\n'
                                     '(d) set out plans for communication to staff, external stakeholders and media in '
                                     'accordance with Article 14 and for notification to clients, for internal escalation '
                                     'procedures, including ICT-related customer complaints, as well as for the provision of '
                                     'information to financial entities that act as counterparts, as appropriate;\n'
                                     '(e) ensure that at least major ICT-related incidents are reported to relevant senior '
                                     'management and inform the management body of at least major ICT-related incidents, '
                                     'explaining the impact, response and additional controls to be established as a result of '
                                     'such ICT-related incidents;\n'
                                     '(f) establish ICT-related incident response procedures to mitigate impacts and ensure '
                                     'that services become operational and secure in a timely manner.',
          'subchapter': 'Article 17: ICT-related incident management process'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': ['Q-IRO-02.4: Does the organization identify classes of incidents and actions to take to '
                                   'ensure the continuation of organizational missions and business functions?.'],
          'objective_title': 'Article 18.1: Financial entities shall classify ICT-related incidents and shall determine their '
                             'impact based on the following criteria:',
          'requirement_description': '(a) the number and/or relevance of clients or financial counterparts affected and, where '
                                     'applicable, the amount or number of transactions affected by the ICT-related incident, '
                                     'and whether the ICT-related incident has caused reputational impact;\n'
                                     '(b) the duration of the ICT-related incident, including the service downtime;\n'
                                     '(c) the geographical spread with regard to the areas affected by the ICT-related '
                                     'incident, particularly if it affects more than two Member States;\n'
                                     '(d) the data losses that the ICT-related incident entails, in relation to availability, '
                                     'authenticity, integrity or confidentiality of data;\n'
                                     "(e) the criticality of the services affected, including the financial entity's "
                                     'transactions and operations;\n'
                                     '(f) the economic impact, in particular direct and indirect costs and losses, of the '
                                     'ICT-related incident in both absolute and relative terms.',
          'subchapter': 'Article 18: Classification of ICT-related incidents and cyber threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': ['Q-AST-31-CM: Does the organization categorize technology assets?.',
                                   'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with '
                                   'applicable statutory, regulatory and contractual requirements? .',
                                   'Q-DCH-11: Does the organization reclassify data, including associated systems, '
                                   'applications and services, commensurate with the security category and/or classification '
                                   'level of the information?.'],
          'objective_title': 'Article 18.2: Financial entities shall classify cyber threats as significant based on the '
                             "criticality of the services at risk, including the financial entity's transactions and "
                             'operations, number and/or relevance of clients or financial counterparts targeted and the '
                             'geographical spread of the areas at risk.',
          'requirement_description': None,
          'subchapter': 'Article 18: Classification of ICT-related incidents and cyber threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 18.3: The ESAs shall, through the Joint Committee and in consultation with the ECB and '
                             'ENISA, develop common draft regulatory technical standards further specifying the following:',
          'requirement_description': '(a) the criteria set out in paragraph 1, including materiality thresholds for '
                                     'determining major ICT-related incidents or, as applicable, major operational or security '
                                     'payment-related incidents, that are subject to the reporting obligation laid down in '
                                     'Article 19(1);\n'
                                     '(b) the criteria to be applied by competent authorities for the purpose of assessing the '
                                     'relevance of major ICT-related incidents or, as applicable, major operational or '
                                     'security payment-related incidents, to relevant competent authorities in other Member '
                                     "States', and the details of reports of major ICT-related incidents or, as applicable, "
                                     'major operational or security payment-related incidents, to be shared with other '
                                     'competent authorities pursuant to Article 19(6) and (7);\n'
                                     '(c) the criteria set out in paragraph 2 of this Article, including high materiality '
                                     'thresholds for determining significant cyber threats.',
          'subchapter': 'Article 18: Classification of ICT-related incidents and cyber threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 18.4: When developing the common draft regulatory technical standards referred to in '
                             'paragraph 3 of this Article, the ESAs shall take into account the criteria set out in Article '
                             '4(2), as well as international standards, guidance and specifications developed and published by '
                             'ENISA, including, where appropriate, specifications for other economic sectors. For the purposes '
                             'of applying the criteria set out in Article 4(2), the ESAs shall duly consider the need for '
                             'microenterprises and small and medium-sized enterprises to mobilise sufficient resources and '
                             'capabilities to ensure that ICT-related incidents are managed swiftly.',
          'requirement_description': 'The ESAs shall submit those common draft regulatory technical standards to the '
                                     'Commission by 17 January 2024.\n'
                                     'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'regulatory technical standards referred to in paragraph 3 in accordance with Articles 10 '
                                     'to 14 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010.',
          'subchapter': 'Article 18: Classification of ICT-related incidents and cyber threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': ['Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-IRO-14: Does the organization maintain incident response contacts with applicable '
                                   'regulatory and law enforcement agencies? .'],
          'objective_title': 'Article 19.1: Financial entities shall report major ICT-related incidents to the relevant '
                             'competent authority as referred to in Article 46 in accordance with paragraph 4 of this Article.',
          'requirement_description': 'Where a financial entity is subject to supervision by more than one national competent '
                                     'authority referred to in Article 46, Member States shall designate a single competent '
                                     'authority as the relevant competent authority responsible for carrying out the functions '
                                     'and duties provided for in this Article.\n'
                                     'Credit institutions classified as significant, in accordance with Article 6(4) of '
                                     'Regulation (EU) No 1024/2013, shall report major ICT-related incidents to the relevant '
                                     'national competent authority designated in accordance with Article 4 of Directive '
                                     '2013/36/EU, which shall immediately transmit that report to the ECB.\n'
                                     'For the purpose of the first subparagraph, financial entities shall produce, after '
                                     'collecting and analysing all relevant information, the initial notification and reports '
                                     'referred to in paragraph 4 of this Article using the templates referred to in Article 20 '
                                     'and submit them to the competent authority. In the event that a technical impossibility '
                                     'prevents the submission of the initial notification using the template, financial '
                                     'entities shall notify the competent authority about it via alternative means.\n'
                                     'The initial notification and reports referred to in paragraph 4 shall include all '
                                     'information necessary for the competent authority to determine the significance of the '
                                     'major ICT-related incident and assess possible cross-border impacts.\n'
                                     'Without prejudice to the reporting pursuant to the first subparagraph by the financial '
                                     'entity to the relevant competent authority, Member States may additionally determine '
                                     'that some or all financial entities shall also provide the initial notification and each '
                                     'report referred to in paragraph 4 of this Article using the templates referred to in '
                                     'Article 20 to the competent authorities or the computer security incident response teams '
                                     '(CSIRTs) designated or established in accordance with Directive (EU) 2022/2555.',
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': ['Q-THR-06: Does the organization establish a Vulnerability Disclosure Program (VDP) to '
                                   'assist with the secure development and maintenance of products and services that receives '
                                   'unsolicited input from the public about vulnerabilities in organizational systems, '
                                   'services and processes?.'],
          'objective_title': 'Article 19.2: Financial entities may, on a voluntary basis, notify significant cyber threats to '
                             'the relevant competent authority when they deem the threat to be of relevance to the financial '
                             'system, service users or clients. The relevant competent authority may provide such information '
                             'to other relevant authorities referred to in paragraph 6.',
          'requirement_description': 'Credit institutions classified as significant, in accordance with Article 6(4) of '
                                     'Regulation (EU) No 1024/2013, may, on a voluntary basis, notify significant cyber '
                                     'threats to relevant national competent authority, designated in accordance with Article '
                                     '4 of Directive 2013/36/EU, which shall immediately transmit the notification to the '
                                     'ECB.\n'
                                     'Member States may determine that those financial entities that on a voluntary basis '
                                     'notify in accordance with the first subparagraph may also transmit that notification to '
                                     'the CSIRTs designated or established in accordance with Directive (EU) 2022/2555.',
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': ['Q-IRO-16: Does the organization proactively manage public relations associated with an '
                                   'incident and employ appropriate measures to repair the reputation of the organization?.',
                                   'Q-IRO-11: Does the organization provide incident response advice and assistance to users '
                                   'of systems for the handling and reporting of actual and potential cybersecurity and '
                                   'privacy incidents? .',
                                   'Q-IRO-11.1: Does the organization use automated mechanisms to increase the availability of '
                                   'incident response-related information and support? .',
                                   'Q-IRO-11.2: Does the organization establish a direct, cooperative relationship between the '
                                   "organization's incident response capability and external service providers?.",
                                   'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the '
                                   'potential attack vectors that attackers could use to attack the organization? .'],
          'objective_title': 'Article 19.3: Where a major ICT-related incident occurs and has an impact on the financial '
                             'interests of clients, financial entities shall, without undue delay as soon as they become aware '
                             'of it, inform their clients about the major ICT-related incident and about the measures that '
                             'have been taken to mitigate the adverse effects of such incident.',
          'requirement_description': 'In the case of a significant cyber threat, financial entities shall, where applicable, '
                                     'inform their clients that are potentially affected of any appropriate protection '
                                     'measures which the latter may consider taking.',
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 19.4: Financial entities shall, within the time limits to be laid down in accordance '
                             'with Article 20, first paragraph, point (a), point (ii), submit the following to the relevant '
                             'competent authority:',
          'requirement_description': '(a) an initial notification;\n'
                                     '(b) an intermediate report after the initial notification referred to in point (a), as '
                                     'soon as the status of the original incident has changed significantly or the handling of '
                                     'the major ICT-related incident has changed based on new information available, followed, '
                                     'as appropriate, by updated notifications every time a relevant status update is '
                                     'available, as well as upon a specific request of the competent authority;\n'
                                     '(c) a final report, when the root cause analysis has been completed, regardless of '
                                     'whether mitigation measures have already been implemented, and when the actual impact '
                                     'figures are available to replace estimates.',
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 19.5: Financial entities may outsource, in accordance with Union and national sectoral '
                             'law, the reporting obligations under this Article to a third-party service provider. In case of '
                             'such outsourcing, the financial entity remains fully responsible for the fulfilment of the '
                             'incident reporting requirements.',
          'requirement_description': None,
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': ['Q-IRO-14: Does the organization maintain incident response contacts with applicable '
                                   'regulatory and law enforcement agencies? .',
                                   'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.'],
          'objective_title': 'Article 19.6: Upon receipt of the initial notification and of each report referred to in '
                             'paragraph 4, the competent authority shall, in a timely manner, provide details of the major '
                             'ICT-related incident to the following recipients based, as applicable, on their respective '
                             'competences:',
          'requirement_description': '(a) EBA, ESMA or EIOPA;\n'
                                     '(b) the ECB, in the case of financial entities referred to in Article 2(1), points (a), '
                                     '(b) and (d);\n'
                                     '(c) the competent authorities, single points of contact or CSIRTs designated or '
                                     'established in accordance with Directive (EU) 2022/2555;\n'
                                     '(d) the resolution authorities, as referred to in Article 3 of Directive 2014/59/EU, and '
                                     'the Single Resolution Board (SRB) with respect to entities referred to in Article 7(2) '
                                     'of Regulation (EU) No 806/2014 of the European Parliament and of the Council, and with '
                                     'respect to entities and groups referred to in Article 7(4)(b) and (5) of Regulation (EU) '
                                     'No 806/2014 if such details concern incidents that pose a risk to ensuring critical '
                                     'functions within the meaning of Article 2(1), point (35), of Directive 2014/59/EU; and\n'
                                     '(e) other relevant public authorities under national law.',
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 19.7: Following receipt of information in accordance with paragraph 6, EBA, ESMA or '
                             'EIOPA and the ECB, in consultation with ENISA and in cooperation with the relevant competent '
                             'authority, shall assess whether the major ICT-related incident is relevant for competent '
                             'authorities in other Member States. Following that assessment, EBA, ESMA or EIOPA shall, as soon '
                             'as possible, notify relevant competent authorities in other Member States accordingly. The ECB '
                             'shall notify the members of the European System of Central Banks on issues relevant to the '
                             'payment system. Based on that notification, the competent authorities shall, where appropriate, '
                             'take all of the necessary measures to protect the immediate stability of the financial system.',
          'requirement_description': None,
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 19.8: The notification to be done by ESMA pursuant to paragraph 7 of this Article shall '
                             'be without prejudice to the responsibility of the competent authority to urgently transmit the '
                             'details of the major ICT-related incident to the relevant authority in the host Member State, '
                             'where a central securities depository has significant cross-border activity in the host Member '
                             'State, the major ICT-related incident is likely to have severe consequences for the financial '
                             'markets of the host Member State and where there are cooperation arrangements among competent '
                             'authorities related to the supervision of financial entities.',
          'requirement_description': None,
          'subchapter': 'Article 19: Reporting of major ICT-related incidents and voluntary notification of significant cyber '
                        'threats'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 20.1: Harmonisation of reporting content and templates',
          'requirement_description': 'The ESAs, through the Joint Committee, and in consultation with ENISA and the ECB, shall '
                                     'develop:\n'
                                     '(a) common draft regulatory technical standards in order to:\n'
                                     '(i) establish the content of the reports for major ICT-related incidents in order to '
                                     'reflect the criteria laid down in Article 18(1) and incorporate further elements, such '
                                     'as details for establishing the relevance of the reporting for other Member States and '
                                     'whether it constitutes a major operational or security payment-related incident or not;\n'
                                     '(ii) determine the time limits for the initial notification and for each report referred '
                                     'to in Article 19(4);\n'
                                     '(iii) establish the content of the notification for significant cyber threats.\n'
                                     'When developing those draft regulatory technical standards, the ESAs shall take into '
                                     'account the size and the overall risk profile of the financial entity, and the nature, '
                                     'scale and complexity of its services, activities and operations, and in particular, with '
                                     'a view to ensuring that, for the purposes of this paragraph, point (a), point (ii), '
                                     'different time limits may reflect, as appropriate, specificities of financial sectors, '
                                     'without prejudice to maintaining a consistent approach to ICT-related incident reporting '
                                     'pursuant to this Regulation and to Directive (EU) 2022/2555. The ESAs shall, as '
                                     'applicable, provide justification when deviating from the approaches taken in the '
                                     'context of that Directive;\n'
                                     '(b) common draft implementing technical standards in order to establish the standard '
                                     'forms, templates and procedures for financial entities to report a major ICT-related '
                                     'incident and to notify a significant cyber threat.\n'
                                     'The ESAs shall submit the common draft regulatory technical standards referred to in the '
                                     'first paragraph, point (a), and the common draft implementing technical standards '
                                     'referred to in the first paragraph, point (b), to the Commission by 17 July 2024.\n'
                                     'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'common regulatory technical standards referred to in the first paragraph, point (a), in '
                                     'accordance with Articles 10 to 14 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 '
                                     'and (EU) No 1095/2010.\n'
                                     'Power is conferred on the Commission to adopt the common implementing technical '
                                     'standards referred to in the first paragraph, point (b), in accordance with Article 15 '
                                     'of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010.',
          'subchapter': 'Article 20: Harmonisation of reporting content and templates'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 21.1: The ESAs, through the Joint Committee, and in consultation with the ECB and ENISA, '
                             'shall prepare a joint report assessing the feasibility of further centralisation of incident '
                             'reporting through the establishment of a single EU Hub for major ICT-related incident reporting '
                             'by financial entities. The joint report shall explore ways to facilitate the flow of ICT-related '
                             'incident reporting, reduce associated costs and underpin thematic analyses with a view to '
                             'enhancing supervisory convergence.',
          'requirement_description': None,
          'subchapter': 'Article 21: Centralisation of reporting of major ICT-related incidents'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 21.2: The joint report referred to in paragraph 1 shall comprise at least the following '
                             'elements:',
          'requirement_description': '(a) prerequisites for the establishment of a single EU Hub;\n'
                                     '(b) benefits, limitations and risks, including risks associated with the high '
                                     'concentration of sensitive information;\n'
                                     '(c) the necessary capability to ensure interoperability with regard to other relevant '
                                     'reporting schemes;\n'
                                     '(d) elements of operational management;\n'
                                     '(e) conditions of membership;\n'
                                     '(f) technical arrangements for financial entities and national competent authorities to '
                                     'access the single EU Hub;\n'
                                     '(g) a preliminary assessment of financial costs incurred by setting-up the operational '
                                     'platform supporting the single EU Hub, including the requisite expertise.',
          'subchapter': 'Article 21: Centralisation of reporting of major ICT-related incidents'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 21.3: The ESAs shall submit the report referred to in paragraph 1 to the European '
                             'Parliament, to the Council and to the Commission by 17 January 2025.',
          'requirement_description': None,
          'subchapter': 'Article 21: Centralisation of reporting of major ICT-related incidents'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 22.1: Without prejudice to the technical input, advice or remedies and subsequent '
                             'follow-up which may be provided, where applicable, in accordance with national law, by the '
                             'CSIRTs under Directive (EU) 2022/2555, the competent authority shall, upon receipt of the '
                             'initial notification and of each report as referred to in Article 19(4), acknowledge receipt and '
                             'may, where feasible, provide in a timely manner relevant and proportionate feedback or '
                             'high-level guidance to the financial entity, in particular by making available any relevant '
                             'anonymised information and intelligence on similar threats, and may discuss remedies applied at '
                             'the level of the financial entity and ways to minimise and mitigate adverse impact across the '
                             'financial sector. Without prejudice to the supervisory feedback received, financial entities '
                             'shall remain fully responsible for the handling and for consequences of the ICT-related '
                             'incidents reported pursuant to Article 19(1).',
          'requirement_description': None,
          'subchapter': 'Article 22: Supervisory feedback'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 22.2: The ESAs shall, through the Joint Committee, on an anonymised and aggregated '
                             'basis, report yearly on major ICT-related incidents, the details of which shall be provided by '
                             'competent authorities in accordance with Article 19(6), setting out at least the number of major '
                             'ICT-related incidents, their nature and their impact on the operations of financial entities or '
                             'clients, remedial actions taken and costs incurred.',
          'requirement_description': 'The ESAs shall issue warnings and produce high-level statistics to support ICT threat '
                                     'and vulnerability assessments.',
          'subchapter': 'Article 22: Supervisory feedback'},
         {'chapter_title': 'Chapter III: ICT-related incident management, classification and reporting',
          'conformity_questions': [],
          'objective_title': 'Article 23.1: Operational or security payment-related incidents concerning credit institutions,  '
                             'payment institutions, account information service providers, and electronic money institutions',
          'requirement_description': 'The requirements laid down in this Chapter shall also apply to operational or security '
                                     'payment-related incidents and to major operational or security payment-related '
                                     'incidents, where they concern credit institutions, payment institutions, account '
                                     'information service providers, and electronic money institutions.',
          'subchapter': 'Article 23: Operational or security payment-related incidents concerning credit institutions,  '
                        'payment institutions, account information service providers, and electronic money institutions'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-IRO-04.3: Does the organization use qualitative and quantitative data from incident '
                                   'response testing to:  - Determine the effectiveness of incident response processes; - '
                                   'Continuously improve incident response processes; and - Provide incident response measures '
                                   'and metrics that are accurate, consistent, and in a reproducible format?.'],
          'objective_title': 'Article 24.1: For the purpose of assessing preparedness for handling ICT-related incidents, of '
                             'identifying weaknesses, deficiencies and gaps in digital operational resilience, and of promptly '
                             'implementing corrective measures, financial entities, other than microenterprises, shall, taking '
                             'into account the criteria set out in Article 4(2), establish, maintain and review a sound and '
                             'comprehensive digital operational resilience testing programme as an integral part of the ICT '
                             'risk-management framework referred to in Article 6.',
          'requirement_description': None,
          'subchapter': 'Article 24: General requirements for the performance of digital operational resilience testing'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-IRO-06.1: Does the organization coordinate incident response testing with organizational '
                                   'elements responsible for related plans? .',
                                   'Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .',
                                   'Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to '
                                   'perform penetration testing?.',
                                   'Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.'],
          'objective_title': 'Article 24.2: The digital operational resilience testing programme shall include a range of '
                             'assessments, tests, methodologies, practices and tools to be applied in accordance with Articles '
                             '25 and 26.',
          'requirement_description': None,
          'subchapter': 'Article 24: General requirements for the performance of digital operational resilience testing'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 24.3: When conducting the digital operational resilience testing programme referred to '
                             'in paragraph 1 of this Article, financial entities, other than microenterprises, shall follow a '
                             'risk-based approach taking into account the criteria set out in Article 4(2) duly considering '
                             'the evolving landscape of ICT risk, any specific risks to which the financial entity concerned '
                             'is or might be exposed, the criticality of information assets and of services provided, as well '
                             'as any other factor the financial entity deems appropriate.',
          'requirement_description': None,
          'subchapter': 'Article 24: General requirements for the performance of digital operational resilience testing'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 24.4: Financial entities, other than microenterprises, shall ensure that tests are '
                             'undertaken by independent parties, whether internal or external. Where tests are undertaken by '
                             'an internal tester, financial entities shall dedicate sufficient resources and ensure that '
                             'conflicts of interest are avoided throughout the design and execution phases of the test.',
          'requirement_description': None,
          'subchapter': 'Article 24: General requirements for the performance of digital operational resilience testing'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-VPM-05.2: Does the organization use automated mechanisms to determine the state of '
                                   'system components with regard to flaw remediation? .',
                                   'Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
                                   'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.',
                                   'Q-VPM-06.8: Does the organization define what information is allowed to be discoverable by '
                                   'adversaries and take corrective actions to remediated non-compliant systems?.',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .'],
          'objective_title': 'Article 24.5: Financial entities, other than microenterprises, shall establish procedures and '
                             'policies to prioritise, classify and remedy all issues revealed throughout the performance of '
                             'the tests and shall establish internal validation methodologies to ascertain that all identified '
                             'weaknesses, deficiencies or gaps are fully addressed.',
          'requirement_description': None,
          'subchapter': 'Article 24: General requirements for the performance of digital operational resilience testing'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 24.6: Financial entities, other than microenterprises, shall ensure, at least yearly, '
                             'that appropriate tests are conducted on all ICT systems and applications supporting critical or '
                             'important functions.',
          'requirement_description': None,
          'subchapter': 'Article 24: General requirements for the performance of digital operational resilience testing'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-IAO-02.2: Does the organization conduct specialized assessments for:   -  Statutory, '
                                   'regulatory and contractual compliance obligations;  -  Monitoring capabilities;   -  '
                                   'Mobile devices;  -  Databases;  -  Application security;  -  Embedded technologies (e.g., '
                                   'IoT, OT, etc.);  -  Vulnerability management;   -  Malicious code;   -  Insider threats '
                                   'and  -  Performance/load testing? .',
                                   'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-01: Does the organization facilitate the implementation and monitoring of '
                                   'vulnerability management controls?.'],
          'objective_title': 'Article 25.1: The digital operational resilience testing programme referred to in Article 24 '
                             'shall provide, in accordance with the criteria set out in Article 4(2), for the execution of '
                             'appropriate tests, such as vulnerability assessments and scans, open source analyses, network '
                             'security assessments, gap analyses, physical security reviews, questionnaires and scanning '
                             'software solutions, source code reviews where feasible, scenario-based tests, compatibility '
                             'testing, performance testing, end-to-end testing and penetration testing.',
          'requirement_description': None,
          'subchapter': 'Article 25: Testing of ICT tools and systems'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.'],
          'objective_title': 'Article 25.2: Central securities depositories and central counterparties shall perform '
                             'vulnerability assessments before any deployment or redeployment of new or existing applications '
                             'and infrastructure components, and ICT services supporting critical or important functions of '
                             'the financial entity.',
          'requirement_description': None,
          'subchapter': 'Article 25: Testing of ICT tools and systems'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-VPM-03: Does the organization identify and assign a risk ranking to newly discovered '
                                   'security vulnerabilities using reputable outside sources for security vulnerability '
                                   'information? .',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.'],
          'objective_title': 'Article 25.3: Microenterprises shall perform the tests referred to in paragraph 1 by combining a '
                             'risk-based approach with a strategic planning of ICT testing, by duly considering the need to '
                             'maintain a balanced approach between the scale of resources and the time to be allocated to the '
                             'ICT testing provided for in this Article, on the one hand, and the urgency, type of risk, '
                             'criticality of information assets and of services provided, as well as any other relevant '
                             "factor, including the financial entity's ability to take calculated risks, on the other hand.",
          'requirement_description': None,
          'subchapter': 'Article 25: Testing of ICT tools and systems'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to '
                                   'perform penetration testing?.',
                                   'Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.',
                                   'Q-THR-07: Does the organization perform cyber threat hunting that uses Indicators of '
                                   'Compromise (IoC) to detect, track and disrupt threats that evade existing security '
                                   'controls?.',
                                   'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
                                   'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the '
                                   'potential attack vectors that attackers could use to attack the organization? .'],
          'objective_title': 'Article 26.1: Financial entities, other than entities referred to in Article 16(1), first '
                             'subparagraph, and other than microenterprises, which are identified in accordance with paragraph '
                             '8, third subparagraph, of this Article, shall carry out at least every 3 years advanced testing '
                             'by means of TLPT. Based on the risk profile of the financial entity and taking into account '
                             'operational circumstances, the competent authority may, where necessary, request the financial '
                             'entity to reduce or increase this frequency.',
          'requirement_description': None,
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-TDA-09.5: Does the organization perform application-level penetration testing of '
                                   'custom-made applications and services?.'],
          'objective_title': 'Article 26.2: Each threat-led penetration test shall cover several or all critical or important '
                             'functions of a financial entity, and shall be performed on live production systems supporting '
                             'such functions.',
          'requirement_description': 'Financial entities shall identify all relevant underlying ICT systems, processes and '
                                     'technologies supporting critical or important functions and ICT services, including '
                                     'those supporting the critical or important functions which have been outsourced or '
                                     'contracted to ICT third-party service providers.\n'
                                     'Financial entities shall assess which critical or important functions need to be covered '
                                     'by the TLPT. The result of this assessment shall determine the precise scope of TLPT and '
                                     'shall be validated by the competent authorities.',
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': ['Q-TPM-09: Does the organization address weaknesses or deficiencies in supply chain '
                                   'elements identified during independent or organizational assessments of such elements? .'],
          'objective_title': 'Article 26.3: Where ICT third-party service providers are included in the scope of TLPT, the '
                             'financial entity shall take the necessary measures and safeguards to ensure the participation of '
                             'such ICT third-party service providers in the TLPT and shall retain at all times full '
                             'responsibility for ensuring compliance with this Regulation.',
          'requirement_description': None,
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.4: Without prejudice to paragraph 2, first and second subparagraphs, where the '
                             'participation of an ICT third-party service provider in the TLPT, referred to in paragraph 3, is '
                             'reasonably expected to have an adverse impact on the quality or security of services delivered '
                             'by the ICT third-party service provider to customers that are entities falling outside the scope '
                             'of this Regulation, or on the confidentiality of the data related to such services, the '
                             'financial entity and the ICT third-party service provider may agree in writing that the ICT '
                             'third-party service provider directly enters into contractual arrangements with an external '
                             'tester, for the purpose of conducting, under the direction of one designated financial entity, a '
                             'pooled TLPT involving several financial entities (pooled testing) to which the ICT third-party '
                             'service provider provides ICT services.',
          'requirement_description': 'That pooled testing shall cover the relevant range of ICT services supporting critical '
                                     'or important functions contracted to the respective ICT third-party service provider by '
                                     'the financial entities. The pooled testing shall be considered TLPT carried out by the '
                                     'financial entities participating in the pooled testing.\n'
                                     'The number of financial entities participating in the pooled testing shall be duly '
                                     'calibrated taking into account the complexity and types of services involved.',
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.5: Financial entities shall, with the cooperation of ICT third-party service '
                             'providers and other parties involved, including the testers but excluding the competent '
                             'authorities, apply effective risk management controls to mitigate the risks of any potential '
                             'impact on data, damage to assets, and disruption to critical or important functions, services or '
                             'operations at the financial entity itself, its counterparts or to the financial sector.',
          'requirement_description': None,
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.6: At the end of the testing, after reports and remediation plans have been agreed, '
                             'the financial entity and, where applicable, the external testers shall provide to the authority, '
                             'designated in accordance with paragraph 9 or 10, a summary of the relevant findings, the '
                             'remediation plans and the documentation demonstrating that the TLPT has been conducted in '
                             'accordance with the requirements.',
          'requirement_description': None,
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.7: Authorities shall provide financial entities with an attestation confirming that '
                             'the test was performed in accordance with the requirements as evidenced in the documentation in '
                             'order to allow for mutual recognition of threat led penetration tests between competent '
                             'authorities. The financial entity shall notify the relevant competent authority of the '
                             'attestation, the summary of the relevant findings and the remediation plans.',
          'requirement_description': 'Without prejudice to such attestation, financial entities shall remain at all times '
                                     'fully responsible for the impact of the tests referred to in paragraph 4.',
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.8: Financial entities shall contract testers for the purposes of undertaking TLPT in '
                             'accordance with Article 27. When financial entities use internal testers for the purposes of '
                             'undertaking TLPT, they shall contract external testers every three tests.',
          'requirement_description': 'Credit institutions that are classified as significant in accordance with Article 6(4) '
                                     'of Regulation (EU) No 1024/2013, shall only use external testers in accordance with '
                                     'Article 27(1), points (a) to (e).\n'
                                     'Competent authorities shall identify financial entities that are required to perform '
                                     'TLPT taking into account the criteria set out in Article 4(2), based on an assessment of '
                                     'the following:\n'
                                     '(a) impact-related factors, in particular the extent to which the services provided and '
                                     'activities undertaken by the financial entity impact the financial sector;\n'
                                     '(b) possible financial stability concerns, including the systemic character of the '
                                     'financial entity at Union or national level, as applicable;\n'
                                     '(c) specific ICT risk profile, level of ICT maturity of the financial entity or '
                                     'technology features involved.',
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.9: Member States may designate a single public authority in the financial sector to '
                             'be responsible for TLPT-related matters in the financial sector at national level and shall '
                             'entrust it with all competences and tasks to that effect.',
          'requirement_description': None,
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.10:  In the absence of a designation in accordance with paragraph 9 of this Article, '
                             'and without prejudice to the power to identify the financial entities that are required to '
                             'perform TLPT, a competent authority may delegate the exercise of some or all of the tasks '
                             'referred to in this Article and Article 27 to another national authority in the financial '
                             'sector.',
          'requirement_description': None,
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 26.11:  The ESAs shall, in agreement with the ECB, develop joint draft regulatory '
                             'technical standards in accordance with the TIBER-EU framework in order to specify further:',
          'requirement_description': '(a) the criteria used for the purpose of the application of paragraph 8, second '
                                     'subparagraph;\n'
                                     '(b) the requirements and standards governing the use of internal testers;\n'
                                     '(c) the requirements in relation to:\n'
                                     '(i) the scope of TLPT referred to in paragraph 2;\n'
                                     '(ii) the testing methodology and approach to be followed for each specific phase of the '
                                     'testing process;\n'
                                     '(iii) the results, closure and remediation stages of the testing;\n'
                                     '(d) the type of supervisory and other relevant cooperation which are needed for the '
                                     'implementation of TLPT, and for the facilitation of mutual recognition of that testing, '
                                     'in the context of financial entities that operate in more than one Member State, to '
                                     'allow an appropriate level of supervisory involvement and a flexible implementation to '
                                     'cater for specificities of financial sub-sectors or local financial markets.\n'
                                     'When developing those draft regulatory technical standards, the ESAs shall give due '
                                     'consideration to any specific feature arising from the distinct nature of activities '
                                     'across different financial services sectors.\n'
                                     'The ESAs shall submit those draft regulatory technical standards to the Commission by 17 '
                                     'July 2024.\n'
                                     'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'regulatory technical standards referred to in the first subparagraph in accordance with '
                                     'Articles 10 to 14 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No '
                                     '1095/2010.',
          'subchapter': 'Article 26: Advanced testing of ICT tools,  systems and processes based on TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 27.1: Financial entities shall only use testers for the carrying out of TLPT, that:',
          'requirement_description': '(a) are of the highest suitability and reputability;\n'
                                     '(b) possess technical and organisational capabilities and demonstrate specific expertise '
                                     'in threat intelligence, penetration testing and red team testing;\n'
                                     '(c) are certified by an accreditation body in a Member State or adhere to formal codes '
                                     'of conduct or ethical frameworks;\n'
                                     '(d) provide an independent assurance, or an audit report, in relation to the sound '
                                     'management of risks associated with the carrying out of TLPT, including the due '
                                     "protection of the financial entity's confidential information and redress for the "
                                     'business risks of the financial entity;\n'
                                     '(e) are duly and fully covered by relevant professional indemnity insurances, including '
                                     'against risks of misconduct and negligence.',
          'subchapter': 'Article 27: Requirements for testers for the carrying out of TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 27.2: When using internal testers, financial entities shall ensure that, in addition to '
                             'the requirements in paragraph 1, the following conditions are met:',
          'requirement_description': '(a) such use has been approved by the relevant competent authority or by the single '
                                     'public authority designated in accordance with Article 26(9) and (10);\n'
                                     '(b) the relevant competent authority has verified that the financial entity has '
                                     'sufficient dedicated resources and ensured that conflicts of interest are avoided '
                                     'throughout the design and execution phases of the test; and\n'
                                     '(c) the threat intelligence provider is external to the financial entity.',
          'subchapter': 'Article 27: Requirements for testers for the carrying out of TLPT'},
         {'chapter_title': 'Chapter IV:  Digital operational resilience testing',
          'conformity_questions': [],
          'objective_title': 'Article 27.3: Financial entities shall ensure that contracts concluded with external testers '
                             'require a sound management of the TLPT results and that any data processing thereof, including '
                             'any generation, store, aggregation, draft, report, communication or destruction, do not create '
                             'risks to the financial entity.',
          'requirement_description': None,
          'subchapter': 'Article 27: Requirements for testers for the carrying out of TLPT'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .',
                                   'Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of '
                                   'Third-Party Service Providers (TSP) that can potentially impact the Confidentiality, '
                                   "Integrity, Availability and/or Safety (CIAS) of the organization's systems, applications, "
                                   'services and data?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .'],
          'objective_title': 'Article 28.1: Financial entities shall manage ICT third-party risk as an integral component of '
                             'ICT risk within their ICT risk management framework as referred to in Article 6(1), and in '
                             'accordance with the following principles:',
          'requirement_description': '(a) financial entities that have in place contractual arrangements for the use of ICT '
                                     'services to run their business operations shall, at all times, remain fully responsible '
                                     'for compliance with, and the discharge of, all obligations under this Regulation and '
                                     'applicable financial services law;\n'
                                     "(b) financial entities' management of ICT third-party risk shall be implemented in light "
                                     'of the principle of proportionality, taking into account:\n'
                                     '(i) the nature, scale, complexity and importance of ICT-related dependencies,\n'
                                     '(ii) the risks arising from contractual arrangements on the use of ICT services '
                                     'concluded with ICT third-party service providers, taking into account the criticality or '
                                     'importance of the respective service, process or function, and the potential impact on '
                                     'the continuity and availability of financial services and activities, at individual and '
                                     'at group level.',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-04.3: Does the organization ensure that the interests of third-party service '
                                   'providers are consistent with and reflect organizational interests?.',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.',
                                   'Q-TPM-04: Does the organization mitigate the risks associated with third-party access to '
                                   "the organization's systems and data?.",
                                   'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools '
                                   'and procurement methods for the purchase of unique systems, system components or '
                                   'services?.',
                                   'Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .'],
          'objective_title': 'Article 28.2: As part of their ICT risk management framework, financial entities, other than '
                             'entities referred to in Article 16(1), first subparagraph, and other than microenterprises, '
                             'shall adopt, and regularly review, a strategy on ICT third-party risk, taking into account the '
                             'multi-vendor strategy referred to in Article 6(9), where applicable. The strategy on ICT '
                             'third-party risk shall include a policy on the use of ICT services supporting critical or '
                             'important functions provided by ICT third-party service providers and shall apply on an '
                             'individual basis and, where relevant, on a sub-consolidated and consolidated basis. The '
                             'management body shall, on the basis of an assessment of the overall risk profile of the '
                             'financial entity and the scale and complexity of the business services, regularly review the '
                             'risks identified in respect to contractual arrangements on the use of ICT services supporting '
                             'critical or important functions.',
          'requirement_description': None,
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of '
                                   'Third-Party Service Providers (TSP) that can potentially impact the Confidentiality, '
                                   "Integrity, Availability and/or Safety (CIAS) of the organization's systems, applications, "
                                   'services and data?.',
                                   'Q-TPM-05.2: Does the organization ensure cybersecurity and privacy requirements are '
                                   'included in contracts that flow-down to applicable sub-contractors and suppliers?.',
                                   'Q-TPM-05.1: Does the organization compel Third-Party Service Providers (TSP) to provide '
                                   'notification of actual or potential compromises in the supply chain that can potentially '
                                   'affect or have adversely affected systems, applications and/or services that the '
                                   'organization utilizes?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': 'Article 28.3: As part of their ICT risk management framework, financial entities shall maintain '
                             'and update at entity level, and at sub-consolidated and consolidated levels, a register of '
                             'information in relation to all contractual arrangements on the use of ICT services provided by '
                             'ICT third-party service providers.',
          'requirement_description': 'The contractual arrangements referred to in the first subparagraph shall be '
                                     'appropriately documented, distinguishing between those that cover ICT services '
                                     'supporting critical or important functions and those that do not.\n'
                                     'Financial entities shall report at least yearly to the competent authorities on the '
                                     'number of new arrangements on the use of ICT services, the categories of ICT third-party '
                                     'service providers, the type of contractual arrangements and the ICT services and '
                                     'functions which are being provided.\n'
                                     'Financial entities shall make available to the competent authority, upon its request, '
                                     'the full register of information or, as requested, specified sections thereof, along '
                                     'with any information deemed necessary to enable the effective supervision of the '
                                     'financial entity.\n'
                                     'Financial entities shall inform the competent authority in a timely manner about any '
                                     'planned contractual arrangement on the use of ICT services supporting critical or '
                                     'important functions as well as when a function has become critical or important.',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.',
                                   'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools '
                                   'and procurement methods for the purchase of unique systems, system components or '
                                   'services?.',
                                   'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .',
                                   'Q-TPM-05.2: Does the organization ensure cybersecurity and privacy requirements are '
                                   'included in contracts that flow-down to applicable sub-contractors and suppliers?.'],
          'objective_title': 'Article 28.4: Before entering into a contractual arrangement on the use of ICT services, '
                             'financial entities shall:',
          'requirement_description': '(a) assess whether the contractual arrangement covers the use of ICT services supporting '
                                     'a critical or important function;\n'
                                     '(b) assess if supervisory conditions for contracting are met;\n'
                                     '(c) identify and assess all relevant risks in relation to the contractual arrangement, '
                                     'including the possibility that such contractual arrangement may contribute to '
                                     'reinforcing ICT concentration risk as referred to in Article 29;\n'
                                     '(d) undertake all due diligence on prospective ICT third-party service providers and '
                                     'ensure throughout the selection and assessment processes that the ICT third-party '
                                     'service provider is suitable;\n'
                                     '(e) identify and assess conflicts of interest that the contractual arrangement may '
                                     'cause.',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05.2: Does the organization ensure cybersecurity and privacy requirements are '
                                   'included in contracts that flow-down to applicable sub-contractors and suppliers?.',
                                   'Q-TPM-04.3: Does the organization ensure that the interests of third-party service '
                                   'providers are consistent with and reflect organizational interests?.',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.'],
          'objective_title': 'Article 28.5: Financial entities may only enter into contractual arrangements with ICT '
                             'third-party service providers that comply with appropriate information security standards. When '
                             'those contractual arrangements concern critical or important functions, financial entities '
                             'shall, prior to concluding the arrangements, take due consideration of the use, by ICT '
                             'third-party service providers, of the most up-to-date and highest quality information security '
                             'standards.',
          'requirement_description': None,
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .'],
          'objective_title': 'Article 28.6: In exercising access, inspection and audit rights over the ICT third-party service '
                             'provider, financial entities shall, on the basis of a risk-based approach, pre-determine the '
                             'frequency of audits and inspections as well as the areas to be audited through adhering to '
                             'commonly accepted audit standards in line with any supervisory instruction on the use and '
                             'incorporation of such audit standards.',
          'requirement_description': 'Where contractual arrangements concluded with ICT third-party service providers on the '
                                     'use of ICT services entail high technical complexity, the financial entity shall verify '
                                     'that auditors, whether internal or external, or a pool of auditors, possess appropriate '
                                     'skills and knowledge to effectively perform the relevant audits and assessments.',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05.7-CM: Does the organization include "break clauses"" within contracts for failure '
                                   'to meet contract criteria for cybersecurity and/or privacy controls?".'],
          'objective_title': 'Article 28.7: Financial entities shall ensure that contractual arrangements on the use of ICT '
                             'services may be terminated in any of the following circumstances:',
          'requirement_description': '(a) significant breach by the ICT third-party service provider of applicable laws, '
                                     'regulations or contractual terms;\n'
                                     '(b) circumstances identified throughout the monitoring of ICT third-party risk that are '
                                     'deemed capable of altering the performance of the functions provided through the '
                                     'contractual arrangement, including material changes that affect the arrangement or the '
                                     'situation of the ICT third-party service provider;\n'
                                     "(c) ICT third-party service provider's evidenced weaknesses pertaining to its overall "
                                     'ICT risk management and in particular in the way it ensures the availability, '
                                     'authenticity, integrity and, confidentiality, of data, whether personal or otherwise '
                                     'sensitive data, or non-personal data;\n'
                                     '(d) where the competent authority can no longer effectively supervise the financial '
                                     'entity as a result of the conditions of, or circumstances related to, the respective '
                                     'contractual arrangement.',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05.7-CM: Does the organization include "break clauses"" within contracts for failure '
                                   'to meet contract criteria for cybersecurity and/or privacy controls?".'],
          'objective_title': 'Article 28.8: For ICT services supporting critical or important functions, financial entities '
                             'shall put in place exit strategies. The exit strategies shall take into account risks that may '
                             'emerge at the level of ICT third-party service providers, in particular a possible failure on '
                             'their part, a deterioration of the quality of the ICT services provided, any business disruption '
                             'due to inappropriate or failed provision of ICT services or any material risk arising in '
                             'relation to the appropriate and continuous deployment of the respective ICT service, or the '
                             'termination of contractual arrangements with ICT third-party service providers under any of the '
                             'circumstances listed in paragraph 7.',
          'requirement_description': 'Financial entities shall ensure that they are able to exit contractual arrangements '
                                     'without:\n'
                                     '(a) disruption to their business activities,\n'
                                     '(b) limiting compliance with regulatory requirements,\n'
                                     '(c) detriment to the continuity and quality of services provided to clients.\n'
                                     'Exit plans shall be comprehensive, documented and, in accordance with the criteria set '
                                     'out in Article 4(2), shall be sufficiently tested and reviewed periodically.\n'
                                     'Financial entities shall identify alternative solutions and develop transition plans '
                                     'enabling them to remove the contracted ICT services and the relevant data from the ICT '
                                     'third-party service provider and to securely and integrally transfer them to alternative '
                                     'providers or reincorporate them in-house.\n'
                                     'Financial entities shall have appropriate contingency measures in place to maintain '
                                     'business continuity in the event of the circumstances referred to in the first '
                                     'subparagraph.',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 28.9: The ESAs shall, through the Joint Committee, develop draft implementing technical '
                             'standards to establish the standard templates for the purposes of the register of information '
                             'referred to in paragraph 3, including information that is common to all contractual arrangements '
                             'on the use of ICT services. The ESAs shall submit those draft implementing technical standards '
                             'to the Commission by 17 January 2024.',
          'requirement_description': 'Power is conferred on the Commission to adopt the implementing technical standards '
                                     'referred to in the first subparagraph in accordance with Article 15 of Regulations (EU) '
                                     'No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010.',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 28.10:  The ESAs shall, through the Joint Committee, develop draft regulatory technical '
                             'standards to further specify the detailed content of the policy referred to in paragraph 2 in '
                             'relation to the contractual arrangements on the use of ICT services supporting critical or '
                             'important functions provided by ICT third-party service providers.',
          'requirement_description': 'When developing those draft regulatory technical standards, the ESAs shall take into '
                                     'account the size and the overall risk profile of the financial entity, and the nature, '
                                     'scale and complexity of its services, activities and operations. The ESAs shall submit '
                                     'those draft regulatory technical standards to the Commission by 17 January 2024.\n'
                                     'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'regulatory technical standards referred to in the first subparagraph in accordance with '
                                     'Articles 10 to 14 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No '
                                     '1095/2010',
          'subchapter': 'Article 28: General principles'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05.6: Does the organization obtain a First-Party Declaration (1PD) from applicable '
                                   'Third-Party Service Providers (TSP) that provides assurance of compliance with specified '
                                   'statutory, regulatory and contractual obligations for cybersecurity and privacy controls, '
                                   'including any flow-down requirements to subcontractors? .'],
          'objective_title': 'Article 29.1: When performing the identification and assessment of risks referred to in Article '
                             '28(4), point (c), financial entities shall also take into account whether the envisaged '
                             'conclusion of a contractual arrangement in relation to ICT services supporting critical or '
                             'important functions would lead to any of the following:',
          'requirement_description': '(a) contracting an ICT third-party service provider that is not easily substitutable; '
                                     'or\n'
                                     '(b) having in place multiple contractual arrangements in relation to the provision of '
                                     'ICT services supporting critical or important functions with the same ICT third-party '
                                     'service provider or with closely connected ICT third-party service providers.\n'
                                     'Financial entities shall weigh the benefits and costs of alternative solutions, such as '
                                     'the use of different ICT third-party service providers, taking into account if and how '
                                     'envisaged solutions match the business needs and objectives set out in their digital '
                                     'resilience strategy.',
          'subchapter': 'Article 29: Preliminary assessment of ICT concentration risk at entity level'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 29.2: Where the contractual arrangements on the use of ICT services supporting critical '
                             'or important functions include the possibility that an ICT third-party service provider further '
                             'subcontracts ICT services supporting a critical or important function to other ICT third-party '
                             'service providers, financial entities shall weigh benefits and risks that may arise in '
                             'connection with such subcontracting, in particular in the case of an ICT subcontractor '
                             'established in a third-country.',
          'requirement_description': 'Where contractual arrangements concern ICT services supporting critical or important '
                                     'functions, financial entities shall duly consider the insolvency law provisions that '
                                     "would apply in the event of the ICT third-party service provider's bankruptcy as well as "
                                     'any constraint that may arise in respect to the urgent recovery of the financial '
                                     "entity's data.\n"
                                     'Where contractual arrangements on the use of ICT services supporting critical or '
                                     'important functions are concluded with an ICT third-party service provider established '
                                     'in a third country, financial entities shall, in addition to the considerations referred '
                                     'to in the second subparagraph, also consider the compliance with Union data protection '
                                     'rules and the effective enforcement of the law in that third country.\n'
                                     'Where the contractual arrangements on the use of ICT services supporting critical or '
                                     'important functions provide for subcontracting, financial entities shall assess whether '
                                     'and how potentially long or complex chains of subcontracting may impact their ability to '
                                     'fully monitor the contracted functions and the ability of the competent authority to '
                                     'effectively supervise the financial entity in that respect.',
          'subchapter': 'Article 29: Preliminary assessment of ICT concentration risk at entity level'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': 'Article 30.1: The rights and obligations of the financial entity and of the ICT third-party '
                             'service provider shall be clearly allocated and set out in writing. The full contract shall '
                             'include the service level agreements and be documented in one written document which shall be '
                             'available to the parties on paper, or in a document with another downloadable, durable and '
                             'accessible format.',
          'requirement_description': None,
          'subchapter': 'Article 30: Key contractual provisions'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05.2: Does the organization ensure cybersecurity and privacy requirements are '
                                   'included in contracts that flow-down to applicable sub-contractors and suppliers?.',
                                   'Q-TPM-05.1: Does the organization compel Third-Party Service Providers (TSP) to provide '
                                   'notification of actual or potential compromises in the supply chain that can potentially '
                                   'affect or have adversely affected systems, applications and/or services that the '
                                   'organization utilizes?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': 'Article 30.2: The contractual arrangements on the use of ICT services shall include at least the '
                             'following elements:',
          'requirement_description': '(a) a clear and complete description of all functions and ICT services to be provided by '
                                     'the ICT third-party service provider, indicating whether subcontracting of an ICT '
                                     'service supporting a critical or important function, or material parts thereof, is '
                                     'permitted and, when that is the case, the conditions applying to such subcontracting;\n'
                                     '(b) the locations, namely the regions or countries, where the contracted or '
                                     'subcontracted functions and ICT services are to be provided and where data is to be '
                                     'processed, including the storage location, and the requirement for the ICT third-party '
                                     'service provider to notify the financial entity in advance if it envisages changing such '
                                     'locations;\n'
                                     '(c) provisions on availability, authenticity, integrity and confidentiality in relation '
                                     'to the protection of data, including personal data;\n'
                                     '(d) provisions on ensuring access, recovery and return in an easily accessible format of '
                                     'personal and non-personal data processed by the financial entity in the event of the '
                                     'insolvency, resolution or discontinuation of the business operations of the ICT '
                                     'third-party service provider, or in the event of the termination of the contractual '
                                     'arrangements;\n'
                                     '(e) service level descriptions, including updates and revisions thereof;\n'
                                     '(f) the obligation of the ICT third-party service provider to provide assistance to the '
                                     'financial entity at no additional cost, or at a cost that is determined ex-ante, when an '
                                     'ICT incident that is related to the ICT service provided to the financial entity '
                                     'occurs;\n'
                                     '(g) the obligation of the ICT third-party service provider to fully cooperate with the '
                                     'competent authorities and the resolution authorities of the financial entity, including '
                                     'persons appointed by them;\n'
                                     '(h) termination rights and related minimum notice periods for the termination of the '
                                     'contractual arrangements, in accordance with the expectations of competent authorities '
                                     'and resolution authorities;\n'
                                     '(i) the conditions for the participation of ICT third-party service providers in the '
                                     "financial entities' ICT security awareness programmes and digital operational resilience "
                                     'training in accordance with Article 13(6).',
          'subchapter': 'Article 30: Key contractual provisions'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': 'Article 30.3: The contractual arrangements on the use of ICT services supporting critical or '
                             'important functions shall include, in addition to the elements referred to in paragraph 2, at '
                             'least the following:',
          'requirement_description': '(a) full service level descriptions, including updates and revisions thereof with '
                                     'precise quantitative and qualitative performance targets within the agreed service '
                                     'levels to allow effective monitoring by the financial entity of ICT services and enable '
                                     'appropriate corrective actions to be taken, without undue delay, when agreed service '
                                     'levels are not met;\n'
                                     '(b) notice periods and reporting obligations of the ICT third-party service provider to '
                                     'the financial entity, including notification of any development that might have a '
                                     "material impact on the ICT third-party service provider's ability to effectively provide "
                                     'the ICT services supporting critical or important functions in line with agreed service '
                                     'levels;\n'
                                     '(c) requirements for the ICT third-party service provider to implement and test business '
                                     'contingency plans and to have in place ICT security measures, tools and policies that '
                                     'provide an appropriate level of security for the provision of services by the financial '
                                     'entity in line with its regulatory framework;\n'
                                     '(d) the obligation of the ICT third-party service provider to participate and fully '
                                     "cooperate in the financial entity's TLPT as referred to in Articles 26 and 27;\n"
                                     "(e) the right to monitor, on an ongoing basis, the ICT third-party service provider's "
                                     'performance, which entails the following:\n'
                                     '(i) unrestricted rights of access, inspection and audit by the financial entity, or an '
                                     'appointed third party, and by the competent authority, and the right to take copies of '
                                     'relevant documentation on-site if they are critical to the operations of the ICT '
                                     'third-party service provider, the effective exercise of which is not impeded or limited '
                                     'by other contractual arrangements or implementation policies;\n'
                                     "(ii) the right to agree on alternative assurance levels if other clients' rights are "
                                     'affected;\n'
                                     '(iii) the obligation of the ICT third-party service provider to fully cooperate during '
                                     'the onsite inspections and audits performed by the competent authorities, the Lead '
                                     'Overseer, financial entity or an appointed third party; and\n'
                                     '(iv) the obligation to provide details on the scope, procedures to be followed and '
                                     'frequency of such inspections and audits;\n'
                                     '(f) exit strategies, in particular the establishment of a mandatory adequate transition '
                                     'period:\n'
                                     '(i) during which the ICT third-party service provider will continue providing the '
                                     'respective functions, or ICT services, with a view to reducing the risk of disruption at '
                                     'the financial entity or to ensure its effective resolution and restructuring;\n'
                                     '(ii) allowing the financial entity to migrate to another ICT third-party service '
                                     'provider or change to in-house solutions consistent with the complexity of the service '
                                     'provided.\n'
                                     'By way of derogation from point (e), the ICT third-party service provider and the '
                                     "financial entity that is a microenterprise may agree that the financial entity's rights "
                                     'of access, inspection and audit can be delegated to an independent third party, '
                                     'appointed by the ICT third-party service provider, and that the financial entity is able '
                                     "to request information and assurance on the ICT third-party service provider's "
                                     'performance from the third party at any time.',
          'subchapter': 'Article 30: Key contractual provisions'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': 'Article 30.4: When negotiating contractual arrangements, financial entities and ICT third-party '
                             'service providers shall consider the use of standard contractual clauses developed by public '
                             'authorities for specific services.',
          'requirement_description': None,
          'subchapter': 'Article 30: Key contractual provisions'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': ['Q-TPM-05.2: Does the organization ensure cybersecurity and privacy requirements are '
                                   'included in contracts that flow-down to applicable sub-contractors and suppliers?.'],
          'objective_title': 'Article 30.5: The ESAs shall, through the Joint Committee, develop draft regulatory technical '
                             'standards to specify further the elements referred to in paragraph 2, point (a), which a '
                             'financial entity needs to determine and assess when subcontracting ICT services supporting '
                             'critical or important functions.',
          'requirement_description': 'When developing those draft regulatory technical standards, the ESAs shall take into '
                                     'consideration the size and overall risk profile of the financial entity, and the nature, '
                                     'scale and complexity of its services, activities and operations.\n'
                                     'The ESAs shall submit those draft regulatory technical standards to the Commission by 17 '
                                     'July 2024.\n'
                                     'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'regulatory technical standards referred to in the first subparagraph in accordance with '
                                     'Articles 10 to 14 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No '
                                     '1095/2010.',
          'subchapter': 'Article 30: Key contractual provisions'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.1: The ESAs, through the Joint Committee and upon recommendation from the Oversight '
                             'Forum established pursuant to Article 32(1), shall:',
          'requirement_description': '(a) designate the ICT third-party service providers that are critical for financial '
                                     'entities, following an assessment that takes into account the criteria specified in '
                                     'paragraph 2;\n'
                                     '(b) appoint as Lead Overseer for each critical ICT third-party service provider the ESA '
                                     'that is responsible, in accordance with Regulations (EU) No 1093/2010, (EU) No 1094/2010 '
                                     'or (EU) No 1095/2010, for the financial entities having together the largest share of '
                                     'total assets out of the value of total assets of all financial entities using the '
                                     'services of the relevant critical ICT third-party service provider, as evidenced by the '
                                     'sum of the individual balance sheets of those financial entities.',
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.2: The designation referred to in paragraph 1, point (a), shall be based on all of '
                             'the following criteria in relation to ICT services provided by the ICT third-party service '
                             'provider:',
          'requirement_description': '(a) the systemic impact on the stability, continuity or quality of the provision of '
                                     'financial services in the event that the relevant ICT third-party service provider would '
                                     'face a large scale operational failure to provide its services, taking into account the '
                                     'number of financial entities and the total value of assets of financial entities to '
                                     'which the relevant ICT third-party service provider provides services;\n'
                                     '(b) the systemic character or importance of the financial entities that rely on the '
                                     'relevant ICT third-party service provider, assessed in accordance with the following '
                                     'parameters:\n'
                                     '(i) the number of global systemically important institutions (G-SIIs) or other '
                                     'systemically important institutions (O-SIIs) that rely on the respective ICT third-party '
                                     'service provider;\n'
                                     '(ii) the interdependence between the G-SIIs or O-SIIs referred to in point (i) and other '
                                     'financial entities, including situations where the G-SIIs or O-SIIs provide financial '
                                     'infrastructure services to other financial entities;\n'
                                     '(c) the reliance of financial entities on the services provided by the relevant ICT '
                                     'third-party service provider in relation to critical or important functions of financial '
                                     'entities that ultimately involve the same ICT third-party service provider, irrespective '
                                     'of whether financial entities rely on those services directly or indirectly, through '
                                     'subcontracting arrangements;\n'
                                     '(d) the degree of substitutability of the ICT third-party service provider, taking into '
                                     'account the following parameters:\n'
                                     '(i) the lack of real alternatives, even partial, due to the limited number of ICT '
                                     'third-party service providers active on a specific market, or the market share of the '
                                     'relevant ICT third-party service provider, or the technical complexity or sophistication '
                                     'involved, including in relation to any proprietary technology, or the specific features '
                                     "of the ICT third-party service provider's organisation or activity;\n"
                                     '(ii) difficulties in relation to partially or fully migrating the relevant data and '
                                     'workloads from the relevant ICT third-party service provider to another ICT third-party '
                                     'service provider, due either to significant financial costs, time or other resources '
                                     'that the migration process may entail, or to increased ICT risk or other operational '
                                     'risks to which the financial entity may be exposed through such migration.',
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.3: Where the ICT third-party service provider belongs to a group, the criteria '
                             'referred to in paragraph 2 shall be considered in relation to the ICT services provided by the '
                             'group as a whole.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.4: Critical ICT third-party service providers which are part of a group shall '
                             'designate one legal person as a coordination point to ensure adequate representation and '
                             'communication with the Lead Overseer.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.5: The Lead Overseer shall notify the ICT third-party service provider of the outcome '
                             'of the assessment leading to the designation referred in paragraph 1, point (a). Within 6 weeks '
                             'from the date of the notification, the ICT third-party service provider may submit to the Lead '
                             'Overseer a reasoned statement with any relevant information for the purposes of the assessment. '
                             'The Lead Overseer shall consider the reasoned statement and may request additional information '
                             'to be submitted within 30 calendar days of the receipt of such statement.',
          'requirement_description': 'After designating an ICT third-party service provider as critical, the ESAs, through the '
                                     'Joint Committee, shall notify the ICT third-party service provider of such designation '
                                     'and the starting date as from which they will effectively be subject to oversight '
                                     'activities. That starting date shall be no later than one month after the notification. '
                                     'The ICT third-party service provider shall notify the financial entities to which they '
                                     'provide services of their designation as critical.',
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.6: The Commission is empowered to adopt a delegated act in accordance with Article 57 '
                             'to supplement this Regulation by specifying further the criteria referred to in paragraph 2 of '
                             'this Article, by 17 July 2024.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.7: The designation referred to in paragraph 1, point (a), shall not be used until the '
                             'Commission has adopted a delegated act in accordance with paragraph 6.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.8: The designation referred to in paragraph 1, point (a), shall not apply to the '
                             'following:',
          'requirement_description': '(i) financial entities providing ICT services to other financial entities;\n'
                                     '(ii) ICT third-party service providers that are subject to oversight frameworks '
                                     'established for the purposes of supporting the tasks referred to in Article 127(2) of '
                                     'the Treaty on the Functioning of the European Union;\n'
                                     '(iii) ICT intra-group service providers;\n'
                                     '(iv) ICT third-party service providers providing ICT services solely in one Member State '
                                     'to financial entities that are only active in that Member State.',
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.9: The ESAs, through the Joint Committee, shall establish, publish and update yearly '
                             'the list of critical ICT third-party service providers at Union level.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.10:  For the purposes of paragraph 1, point (a), competent authorities shall, on a '
                             'yearly and aggregated basis, transmit the reports referred to in Article 28(3), third '
                             'subparagraph, to the Oversight Forum established pursuant to Article 32. The Oversight Forum '
                             'shall assess the ICT third-party dependencies of financial entities based on the information '
                             'received from the competent authorities.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.11:  The ICT third-party service providers that are not included in the list referred '
                             'to in paragraph 9 may request to be designated as critical in accordance with paragraph 1, point '
                             '(a).',
          'requirement_description': 'For the purpose of the first subparagraph, the ICT third-party service provider shall '
                                     'submit a reasoned application to EBA, ESMA or EIOPA, which, through the Joint Committee, '
                                     'shall decide whether to designate that ICT third-party service provider as critical in '
                                     'accordance with paragraph 1, point (a).\n'
                                     'The decision referred to in the second subparagraph shall be adopted and notified to the '
                                     'ICT third-party service provider within 6 months of receipt of the application.',
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.12:  Financial entities shall only make use of the services of an ICT third-party '
                             'service provider established in a third country and which has been designated as critical in '
                             'accordance with paragraph 1, point (a), if the latter has established a subsidiary in the Union '
                             'within the 12 months following the designation.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 31.13:  The critical ICT third-party service provider referred to in paragraph 12 shall '
                             'notify the Lead Overseer of any changes to the structure of the management of the subsidiary '
                             'established in the Union.',
          'requirement_description': None,
          'subchapter': 'Article 31: Designation of critical ICT third-party service providers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.1: The Joint Committee, in accordance with Article 57(1) of Regulations (EU) No '
                             '1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010, shall establish the Oversight Forum as a '
                             'sub-committee for the purposes of supporting the work of the Joint Committee and of the Lead '
                             'Overseer referred to in Article 31(1), point (b), in the area of ICT third-party risk across '
                             'financial sectors. The Oversight Forum shall prepare the draft joint positions and the draft '
                             'common acts of the Joint Committee in that area.',
          'requirement_description': 'The Oversight Forum shall regularly discuss relevant developments on ICT risk and '
                                     'vulnerabilities and promote a consistent approach in the monitoring of ICT third-party '
                                     'risk at Union level.',
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.2: The Oversight Forum shall, on a yearly basis, undertake a collective assessment of '
                             'the results and findings of the oversight activities conducted for all critical ICT third-party '
                             'service providers and promote coordination measures to increase the digital operational '
                             'resilience of financial entities, foster best practices on addressing ICT concentration risk and '
                             'explore mitigants for cross-sector risk transfers.',
          'requirement_description': None,
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.3: The Oversight Forum shall submit comprehensive benchmarks for critical ICT '
                             'third-party service providers to be adopted by the Joint Committee as joint positions of the '
                             'ESAs in accordance with Article 56(1) of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and '
                             '(EU) No 1095/2010.',
          'requirement_description': None,
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.4: The Oversight Forum shall be composed of:',
          'requirement_description': '(a) the Chairpersons of the ESAs;\n'
                                     '(b) one high-level representative from the current staff of the relevant competent '
                                     'authority referred to in Article 46 from each Member State;\n'
                                     '(c) the Executive Directors of each ESA and one representative from the Commission, from '
                                     'the ESRB, from ECB and from ENISA as observers;\n'
                                     '(d) where appropriate, one additional representative of a competent authority referred '
                                     'to in Article 46 from each Member State as observer;\n'
                                     '(e) where applicable, one representative of the competent authorities designated or '
                                     'established in accordance with Directive (EU) 2022/2555 responsible for the supervision '
                                     'of an essential or important entity subject to that Directive, which has been designated '
                                     'as a critical ICT third-party service provider, as observer.\n'
                                     'The Oversight Forum may, where appropriate, seek the advice of independent experts '
                                     'appointed in accordance with paragraph 6.',
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.5: Each Member State shall designate the relevant competent authority whose staff '
                             'member shall be the high-level representative referred in paragraph 4, first subparagraph, point '
                             '(b), and shall inform the Lead Overseer thereof.',
          'requirement_description': 'The ESAs shall publish on their website the list of high-level representatives from the '
                                     'current staff of the relevant competent authority designated by Member States.',
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.6: The independent experts referred to in paragraph 4, second subparagraph, shall be '
                             'appointed by the Oversight Forum from a pool of experts selected following a public and '
                             'transparent application process.',
          'requirement_description': 'The independent experts shall be appointed on the basis of their expertise in financial '
                                     'stability, digital operational resilience and ICT security matters. They shall act '
                                     'independently and objectively in the sole interest of the Union as a whole and shall '
                                     'neither seek nor take instructions from Union institutions or bodies, from any '
                                     'government of a Member State or from any other public or private body.',
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.7: In accordance with Article 16 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 '
                             'and (EU) No 1095/2010, the ESAs shall by 17 July 2024 issue, for the purposes of this Section, '
                             'guidelines on the cooperation between the ESAs and the competent authorities covering the '
                             'detailed procedures and conditions for the allocation and execution of tasks between competent '
                             'authorities and the ESAs and the details on the exchanges of information which are necessary for '
                             'competent authorities to ensure the follow-up of recommendations pursuant to Article 35(1), '
                             'point (d), addressed to critical ICT third-party service providers.',
          'requirement_description': None,
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.8: The requirements set out in this Section shall be without prejudice to the '
                             'application of Directive (EU) 2022/2555 and of other Union rules on oversight applicable to '
                             'providers of cloud computing services.',
          'requirement_description': None,
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 32.9: The ESAs, through the Joint Committee and based on preparatory work conducted by '
                             'the Oversight Forum, shall, on yearly basis, submit a report on the application of this Section '
                             'to the European Parliament, the Council and the Commission.',
          'requirement_description': None,
          'subchapter': 'Article 32: Structure of the Oversight Framework'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 33.1: The Lead Overseer, appointed in accordance with Article 31(1), point (b), shall '
                             'conduct the oversight of the assigned critical ICT third-party service providers and shall be, '
                             'for the purposes of all matters related to the oversight, the primary point of contact for those '
                             'critical ICT third-party service providers.',
          'requirement_description': None,
          'subchapter': 'Article 33: Tasks of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 33.2: For the purposes of paragraph 1, the Lead Overseer shall assess whether each '
                             'critical ICT third-party service provider has in place comprehensive, sound and effective rules, '
                             'procedures, mechanisms and arrangements to manage the ICT risk which it may pose to financial '
                             'entities.',
          'requirement_description': 'The assessment referred to in the first subparagraph shall focus mainly on ICT services '
                                     'provided by the critical ICT third-party service provider supporting the critical or '
                                     'important functions of financial entities. Where necessary to address all relevant '
                                     'risks, that assessment shall extend to ICT services supporting functions other than '
                                     'those that are critical or important.',
          'subchapter': 'Article 33: Tasks of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 33.3: The assessment referred to in paragraph 2 shall cover:',
          'requirement_description': '(a) ICT requirements to ensure, in particular, the security, availability, continuity, '
                                     'scalability and quality of services which the critical ICT third-party service provider '
                                     'provides to financial entities, as well as the ability to maintain at all times high '
                                     'standards of availability, authenticity, integrity or confidentiality of data;\n'
                                     '(b) the physical security contributing to ensuring the ICT security, including the '
                                     'security of premises, facilities, data centres;\n'
                                     '(c) the risk management processes, including ICT risk management policies, ICT business '
                                     'continuity policy and ICT response and recovery plans;\n'
                                     '(d) the governance arrangements, including an organisational structure with clear, '
                                     'transparent and consistent lines of responsibility and accountability rules enabling '
                                     'effective ICT risk management;\n'
                                     '(e) the identification, monitoring and prompt reporting of material ICT-related '
                                     'incidents to financial entities, the management and resolution of those incidents, in '
                                     'particular cyber-attacks;\n'
                                     '(f) the mechanisms for data portability, application portability and interoperability, '
                                     'which ensure an effective exercise of termination rights by the financial entities;\n'
                                     '(g) the testing of ICT systems, infrastructure and controls;\n'
                                     '(h) the ICT audits;\n'
                                     '(i) the use of relevant national and international standards applicable to the provision '
                                     'of its ICT services to the financial entities.',
          'subchapter': 'Article 33: Tasks of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 33.4: Based on the assessment referred to in paragraph 2, and in coordination with the '
                             'Joint Oversight Network (JON) referred to in Article 34(1), the Lead Overseer shall adopt a '
                             'clear, detailed and reasoned individual oversight plan describing the annual oversight '
                             'objectives and the main oversight actions planned for each critical ICT third-party service '
                             'provider. That plan shall be communicated yearly to the critical ICT third-party service '
                             'provider.',
          'requirement_description': 'Prior to the adoption of the oversight plan, the Lead Overseer shall communicate the '
                                     'draft oversight plan to the critical ICT third-party service provider.\n'
                                     'Upon receipt of the draft oversight plan, the critical ICT third-party service provider '
                                     'may submit a reasoned statement within 15 calendar days evidencing the expected impact '
                                     'on customers which are entities falling outside of the scope of this Regulation and '
                                     'where appropriate, formulating solutions to mitigate risks.',
          'subchapter': 'Article 33: Tasks of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 33.5: Once the annual oversight plans referred to in paragraph 4 have been adopted and '
                             'notified to the critical ICT third-party service providers, competent authorities may take '
                             'measures concerning such critical ICT third-party service providers only in agreement with the '
                             'Lead Overseer.',
          'requirement_description': None,
          'subchapter': 'Article 33: Tasks of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 34.1: To ensure a consistent approach to oversight activities and with a view to '
                             'enabling coordinated general oversight strategies and cohesive operational approaches and work '
                             'methodologies, the three Lead Overseers appointed in accordance with Article 31(1), point (b), '
                             'shall set up a JON to coordinate among themselves in the preparatory stages and to coordinate '
                             'the conduct of oversight activities over their respective overseen critical ICT third-party '
                             'service providers, as well as in the course of any action that may be needed pursuant to Article '
                             '42.',
          'requirement_description': None,
          'subchapter': 'Article 34: Operational coordination between Lead Overseers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 34.2: For the purposes of paragraph 1, the Lead Overseers shall draw up a common '
                             'oversight protocol specifying the detailed procedures to be followed for carrying out the '
                             'day-to-day coordination and for ensuring swift exchanges and reactions. The protocol shall be '
                             'periodically revised to reflect operational needs, in particular the evolution of practical '
                             'oversight arrangements.',
          'requirement_description': None,
          'subchapter': 'Article 34: Operational coordination between Lead Overseers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 34.3: The Lead Overseers may, on an ad-hoc basis, call on the ECB and ENISA to provide '
                             'technical advice, share hands-on experience or join specific coordination meetings of the JON.',
          'requirement_description': None,
          'subchapter': 'Article 34: Operational coordination between Lead Overseers'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.1: For the purposes of carrying out the duties laid down in this Section, the Lead '
                             'Overseer shall have the following powers in respect of the critical ICT third-party service '
                             'providers:',
          'requirement_description': '(a) to request all relevant information and documentation in accordance with Article '
                                     '37;\n'
                                     '(b) to conduct general investigations and inspections in accordance with Articles 38 and '
                                     '39, respectively;\n'
                                     '(c) to request, after the completion of the oversight activities, reports specifying the '
                                     'actions that have been taken or the remedies that have been implemented by the critical '
                                     'ICT third-party service providers in relation to the recommendations referred to in '
                                     'point (d) of this paragraph;\n'
                                     '(d) to issue recommendations on the areas referred to in Article 33(3), in particular '
                                     'concerning the following:\n'
                                     '(i) the use of specific ICT security and quality requirements or processes, in '
                                     'particular in relation to the roll-out of patches, updates, encryption and other '
                                     'security measures which the Lead Overseer deems relevant for ensuring the ICT security '
                                     'of services provided to financial entities;\n'
                                     '(ii) the use of conditions and terms, including their technical implementation, under '
                                     'which the critical ICT third-party service providers provide ICT services to financial '
                                     'entities, which the Lead Overseer deems relevant for preventing the generation of single '
                                     'points of failure, the amplification thereof, or for minimising the possible systemic '
                                     "impact across the Union's financial sector in the event of ICT concentration risk;\n"
                                     '(iii) any planned subcontracting, where the Lead Overseer deems that further '
                                     'subcontracting, including subcontracting arrangements which the critical ICT third-party '
                                     'service providers plan to enter into with ICT third-party service providers or with ICT '
                                     'subcontractors established in a third country, may trigger risks for the provision of '
                                     'services by the financial entity, or risks to the financial stability, based on the '
                                     'examination of the information gathered in accordance with Articles 37 and 38;\n'
                                     '(iv) refraining from entering into a further subcontracting arrangement, where the '
                                     'following cumulative conditions are met:\n'
                                     '-the envisaged subcontractor is an ICT third-party service provider or an ICT '
                                     'subcontractor established in a third country;\n'
                                     '-the subcontracting concerns critical or important functions of the financial entity; '
                                     'and\n'
                                     '-the Lead Overseer deems that the use of such subcontracting poses a clear and serious '
                                     'risk to the financial stability of the Union or to financial entities, including to the '
                                     'ability of financial entities to comply with supervisory requirements.\n'
                                     'For the purpose of point (iv) of this point, ICT third-party service providers shall, '
                                     'using the template referred to in Article 41(1), point (b), transmit the information '
                                     'regarding subcontracting to the Lead Overseer.',
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.2: When exercising the powers referred to in this Article, the Lead Overseer shall:',
          'requirement_description': '(a) ensure regular coordination within the JON, and in particular shall seek consistent '
                                     'approaches, as appropriate, with regard to the oversight of critical ICT third-party '
                                     'service providers;\n'
                                     '(b) take due account of the framework established by Directive (EU) 2022/2555 and, where '
                                     'necessary, consult the relevant competent authorities designated or established in '
                                     'accordance with that Directive, in order to avoid duplication of technical and '
                                     'organisational measures that might apply to critical ICT third-party service providers '
                                     'pursuant to that Directive;\n'
                                     '(c) seek to minimise, to the extent possible, the risk of disruption to services '
                                     'provided by critical ICT third-party service providers to customers that are entities '
                                     'falling outside the scope of this Regulation.',
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.3: The Lead Overseer shall consult the Oversight Forum before exercising the powers '
                             'referred to in paragraph 1.',
          'requirement_description': 'Before issuing recommendations in accordance with paragraph 1, point (d), the Lead '
                                     'Overseer shall give the opportunity to the ICT third-party service provider to provide, '
                                     'within 30 calendar days, relevant information evidencing the expected impact on '
                                     'customers that are entities falling outside the scope of this Regulation and, where '
                                     'appropriate, formulating solutions to mitigate risks.',
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.4: The Lead Overseer shall inform the JON of the outcome of the exercise of the '
                             'powers referred to in paragraph 1, points (a) and (b). The Lead Overseer shall, without undue '
                             'delay, transmit the reports referred to in paragraph 1, point (c), to the JON and to the '
                             'competent authorities of the financial entities using the ICT services of that critical ICT '
                             'third-party service provider.',
          'requirement_description': None,
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.5: Critical ICT third-party service providers shall cooperate in good faith with the '
                             'Lead Overseer, and assist it in the fulfilment of its tasks.',
          'requirement_description': None,
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.6: In the event of whole or partial non-compliance with the measures required to be '
                             'taken pursuant to the exercise of the powers under paragraph 1, points (a), (b) and (c), and '
                             'after the expiry of a period of at least 30 calendar days from the date on which the critical '
                             'ICT third-party service provider received notification of the respective measures, the Lead '
                             'Overseer shall adopt a decision imposing a periodic penalty payment to compel the critical ICT '
                             'third-party service provider to comply with those measures.',
          'requirement_description': None,
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.7: The periodic penalty payment referred to in paragraph 6 shall be imposed on a '
                             'daily basis until compliance is achieved and for no more than a period of six months following '
                             'the notification of the decision to impose a periodic penalty payment to the critical ICT '
                             'third-party service provider.',
          'requirement_description': None,
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.8: The amount of the periodic penalty payment, calculated from the date stipulated in '
                             'the decision imposing the periodic penalty payment, shall be up to 1 % of the average daily '
                             'worldwide turnover of the critical ICT third-party service provider in the preceding business '
                             'year. When determining the amount of the penalty payment, the Lead Overseer shall take into '
                             'account the following criteria regarding non-compliance with the measures referred to in '
                             'paragraph 6:',
          'requirement_description': '(a) the gravity and the duration of non-compliance;\n'
                                     '(b) whether non-compliance has been committed intentionally or negligently;\n'
                                     '(c) the level of cooperation of the ICT third-party service provider with the Lead '
                                     'Overseer.\n'
                                     'For the purposes of the first subparagraph, in order to ensure a consistent approach, '
                                     'the Lead Overseer shall engage in consultation within the JON.',
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.9: Penalty payments shall be of an administrative nature and shall be enforceable. '
                             'Enforcement shall be governed by the rules of civil procedure in force in the Member State on '
                             'the territory of which inspections and access shall be carried out. Courts of the Member State '
                             'concerned shall have jurisdiction over complaints related to irregular conduct of enforcement. '
                             'The amounts of the penalty payments shall be allocated to the general budget of the European '
                             'Union.',
          'requirement_description': None,
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.10:  The Lead Overseer shall disclose to the public every periodic penalty payment '
                             'that has been imposed, unless such disclosure would seriously jeopardise the financial markets '
                             'or cause disproportionate damage to the parties involved.',
          'requirement_description': None,
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 35.11:  Before imposing a periodic penalty payment under paragraph 6, the Lead Overseer '
                             'shall give the representatives of the critical ICT third-party service provider subject to the '
                             'proceedings the opportunity to be heard on the findings and shall base its decisions only on '
                             'findings on which the critical ICT third-party service provider subject to the proceedings has '
                             'had an opportunity to comment.',
          'requirement_description': 'The rights of the defence of the persons subject to the proceedings shall be fully '
                                     'respected in the proceedings. The critical ICT third-party service provider subject to '
                                     'the proceedings shall be entitled to have access to the file, subject to the legitimate '
                                     'interest of other persons in the protection of their business secrets. The right of '
                                     'access to the file shall not extend to confidential information or to the Lead '
                                     "Overseer's internal preparatory documents.",
          'subchapter': 'Article 35: Powers of the Lead Overseer'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 36.1: When oversight objectives cannot be attained by means of interacting with the '
                             'subsidiary set up for the purpose of Article 31(12), or by exercising oversight activities on '
                             'premises located in the Union, the Lead Overseer may exercise the powers, referred to in the '
                             'following provisions, on any premises located in a third-country which is owned, or used in any '
                             'way, for the purposes of providing services to Union financial entities, by a critical ICT '
                             'third-party service provider, in connection with its business operations, functions or services, '
                             'including any administrative, business or operational offices, premises, lands, buildings or '
                             'other properties:',
          'requirement_description': '(a) in Article 35(1), point (a); and\n'
                                     '(b) in Article 35(1), point (b), in accordance with Article 38(2), points (a), (b) and '
                                     '(d), and in Article 39(1) and (2), point (a).\n'
                                     'The powers referred to in the first subparagraph may be exercised subject to all of the '
                                     'following conditions:\n'
                                     '(i) the conduct of an inspection in a third-country is deemed necessary by the Lead '
                                     'Overseer to allow it to fully and effectively perform its duties under this Regulation;\n'
                                     '(ii) the inspection in a third-country is directly related to the provision of ICT '
                                     'services to financial entities in the Union;\n'
                                     '(iii) the critical ICT third-party service provider concerned consents to the conduct of '
                                     'an inspection in a third-country; and\n'
                                     '(iv) the relevant authority of the third-country concerned has been officially notified '
                                     'by the Lead Overseer and raised no objection thereto.',
          'subchapter': 'Article 36: Exercise of the powers of the Lead Overseer outside the Union'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 36.2: Without prejudice to the respective competences of the Union institutions and of '
                             'Member States, for the purposes of paragraph 1, EBA, ESMA or EIOPA shall conclude administrative '
                             'cooperation arrangements with the relevant authority of the third country in order to enable the '
                             'smooth conduct of inspections in the third country concerned by the Lead Overseer and its '
                             'designated team for its mission in that third country. Those cooperation arrangements shall not '
                             'create legal obligations in respect of the Union and its Member States nor shall they prevent '
                             'Member States and their competent authorities from concluding bilateral or multilateral '
                             'arrangements with those third countries and their relevant authorities.',
          'requirement_description': 'Those cooperation arrangements shall specify at least the following elements:\n'
                                     '(a) the procedures for the coordination of oversight activities carried out under this '
                                     'Regulation and any analogous monitoring of ICT third-party risk in the financial sector '
                                     'exercised by the relevant authority of the third country concerned, including details '
                                     'for transmitting the agreement of the latter to allow the conduct, by the Lead Overseer '
                                     'and its designated team, of general investigations and on-site inspections as referred '
                                     'to in paragraph 1, first subparagraph, on the territory under its jurisdiction;\n'
                                     '(b) the mechanism for the transmission of any relevant information between EBA, ESMA or '
                                     'EIOPA and the relevant authority of the third country concerned, in particular in '
                                     'connection with information that may be requested by the Lead Overseer pursuant to '
                                     'Article 37;\n'
                                     '(c) the mechanisms for the prompt notification by the relevant authority of the '
                                     'third-country concerned to EBA, ESMA or EIOPA of cases where an ICT third-party service '
                                     'provider established in a third country and designated as critical in accordance with '
                                     'Article 31(1), point (a), is deemed to have infringed the requirements to which it is '
                                     'obliged to adhere pursuant to the applicable law of the third country concerned when '
                                     'providing services to financial institutions in that third country, as well as the '
                                     'remedies and penalties applied;\n'
                                     '(d) the regular transmission of updates on regulatory or supervisory developments on the '
                                     'monitoring of ICT third-party risk of financial institutions in the third country '
                                     'concerned;\n'
                                     '(e) the details for allowing, if needed, the participation of one representative of the '
                                     'relevant third-country authority in the inspections conducted by the Lead Overseer and '
                                     'the designated team.',
          'subchapter': 'Article 36: Exercise of the powers of the Lead Overseer outside the Union'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 36.3: When the Lead Overseer is not able to conduct oversight activities outside the '
                             'Union, referred to in paragraphs 1 and 2, the Lead Overseer shall:',
          'requirement_description': '(a) exercise its powers under Article 35 on the basis of all facts and documents '
                                     'available to it;\n'
                                     '(b) document and explain any consequence of its inability to conduct the envisaged '
                                     'oversight activities as referred to in this Article.\n'
                                     'The potential consequences referred to in point (b) of this paragraph shall be taken '
                                     "into consideration in the Lead Overseer's recommendations issued pursuant to Article "
                                     '35(1), point (d).',
          'subchapter': 'Article 36: Exercise of the powers of the Lead Overseer outside the Union'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 37.1: The Lead Overseer may, by simple request or by decision, require critical ICT '
                             'third-party service providers to provide all information that is necessary for the Lead Overseer '
                             'to carry out its duties under this Regulation, including all relevant business or operational '
                             'documents, contracts, policies, documentation, ICT security audit reports, ICT-related incident '
                             'reports, as well as any information relating to parties to whom the critical ICT third-party '
                             'service provider has outsourced operational functions or activities.',
          'requirement_description': None,
          'subchapter': 'Article 37: Request for information'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 37.2: When sending a simple request for information under paragraph 1, the Lead Overseer '
                             'shall:',
          'requirement_description': '(a) refer to this Article as the legal basis of the request;\n'
                                     '(b) state the purpose of the request;\n'
                                     '(c) specify what information is required;\n'
                                     '(d) set a time limit within which the information is to be provided;\n'
                                     '(e) inform the representative of the critical ICT third-party service provider from whom '
                                     'the information is requested that he or she is not obliged to provide the information, '
                                     'but in the event of a voluntary reply to the request the information provided must not '
                                     'be incorrect or misleading.',
          'subchapter': 'Article 37: Request for information'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 37.3: When requiring by decision to supply information under paragraph 1, the Lead '
                             'Overseer shall:',
          'requirement_description': '(a) refer to this Article as the legal basis of the request;\n'
                                     '(b) state the purpose of the request;\n'
                                     '(c) specify what information is required;\n'
                                     '(d) set a time limit within which the information is to be provided;\n'
                                     '(e) indicate the periodic penalty payments provided for in Article 35(6) where the '
                                     'production of the required information is incomplete or when such information is not '
                                     'provided within the time limit referred to in point (d) of this paragraph;\n'
                                     "(f) indicate the right to appeal the decision to ESA's Board of Appeal and to have the "
                                     'decision reviewed by the Court of Justice of the European Union (Court of Justice) in '
                                     'accordance with Articles 60 and 61 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 '
                                     'and (EU) No 1095/2010.',
          'subchapter': 'Article 37: Request for information'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 37.4: The representatives of the critical ICT third-party service providers shall supply '
                             'the information requested. Lawyers duly authorised to act may supply the information on behalf '
                             'of their clients. The critical ICT third-party service provider shall remain fully responsible '
                             'if the information supplied is incomplete, incorrect or misleading.',
          'requirement_description': None,
          'subchapter': 'Article 37: Request for information'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 37.5: The Lead Overseer shall, without delay, transmit a copy of the decision to supply '
                             'information to the competent authorities of the financial entities using the services of the '
                             'relevant critical ICT third-party service providers and to the JON.',
          'requirement_description': None,
          'subchapter': 'Article 37: Request for information'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 38.1: In order to carry out its duties under this Regulation, the Lead Overseer, '
                             'assisted by the joint examination team referred to in Article 40(1), may, where necessary, '
                             'conduct investigations of critical ICT third-party service providers.',
          'requirement_description': None,
          'subchapter': 'Article 38: General investigations'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 38.2: The Lead Overseer shall have the power to:',
          'requirement_description': '(a) examine records, data, procedures and any other material relevant to the execution '
                                     'of its tasks, irrespective of the medium on which they are stored;\n'
                                     '(b) take or obtain certified copies of, or extracts from, such records, data, documented '
                                     'procedures and any other material;\n'
                                     '(c) summon representatives of the critical ICT third-party service provider for oral or '
                                     'written explanations on facts or documents relating to the subject matter and purpose of '
                                     'the investigation and to record the answers;\n'
                                     '(d) interview any other natural or legal person who consents to be interviewed for the '
                                     'purpose of collecting information relating to the subject matter of an investigation;\n'
                                     '(e) request records of telephone and data traffic.',
          'subchapter': 'Article 38: General investigations'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 38.3: The officials and other persons authorised by the Lead Overseer for the purposes '
                             'of the investigation referred to in paragraph 1 shall exercise their powers upon production of a '
                             'written authorisation specifying the subject matter and purpose of the investigation.',
          'requirement_description': 'That authorisation shall also indicate the periodic penalty payments provided for in '
                                     'Article 35(6) where the production of the required records, data, documented procedures '
                                     'or any other material, or the answers to questions asked to representatives of the ICT '
                                     'third-party service provider are not provided or are incomplete.',
          'subchapter': 'Article 38: General investigations'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 38.4: The representatives of the critical ICT third-party service providers are required '
                             'to submit to the investigations on the basis of a decision of the Lead Overseer. The decision '
                             'shall specify the subject matter and purpose of the investigation, the periodic penalty payments '
                             'provided for in Article 35(6), the legal remedies available under Regulations (EU) No 1093/2010, '
                             '(EU) No 1094/2010 and (EU) No 1095/2010, and the right to have the decision reviewed by the '
                             'Court of Justice.',
          'requirement_description': None,
          'subchapter': 'Article 38: General investigations'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 38.5: In good time before the start of the investigation, the Lead Overseer shall inform '
                             'competent authorities of the financial entities using the ICT services of that critical ICT '
                             'third-party service provider of the envisaged investigation and of the identity of the '
                             'authorised persons.',
          'requirement_description': 'The Lead Overseer shall communicate to the JON all information transmitted pursuant to '
                                     'the first subparagraph.',
          'subchapter': 'Article 38: General investigations'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 39.1: In order to carry out its duties under this Regulation, the Lead Overseer, '
                             'assisted by the joint examination teams referred to in Article 40(1), may enter in, and conduct '
                             'all necessary onsite inspections on, any business premises, land or property of the ICT '
                             'third-party service providers, such as head offices, operation centres, secondary premises, as '
                             'well as to conduct off-site inspections.',
          'requirement_description': 'For the purposes of exercising the powers referred to in the first subparagraph, the '
                                     'Lead Overseer shall consult the JON.',
          'subchapter': 'Article 39: Inspections'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 39.2: The officials and other persons authorised by the Lead Overseer to conduct an '
                             'on-site inspection shall have the power to:',
          'requirement_description': '(a) enter any such business premises, land or property; and\n'
                                     '(b) seal any such business premises, books or records, for the period of, and to the '
                                     'extent necessary for, the inspection.\n'
                                     'The officials and other persons authorised by the Lead Overseer shall exercise their '
                                     'powers upon production of a written authorisation specifying the subject matter and the '
                                     'purpose of the inspection, and the periodic penalty payments provided for in Article '
                                     '35(6) where the representatives of the critical ICT third-party service providers '
                                     'concerned do not submit to the inspection.',
          'subchapter': 'Article 39: Inspections'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 39.3: In good time before the start of the inspection, the Lead Overseer shall inform '
                             'the competent authorities of the financial entities using that ICT third-party service provider.',
          'requirement_description': None,
          'subchapter': 'Article 39: Inspections'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 39.4: Inspections shall cover the full range of relevant ICT systems, networks, devices, '
                             'information and data either used for, or contributing to, the provision of ICT services to '
                             'financial entities.',
          'requirement_description': None,
          'subchapter': 'Article 39: Inspections'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 39.5: Before any planned on-site inspection, the Lead Overseer shall give reasonable '
                             'notice to the critical ICT third-party service providers, unless such notice is not possible due '
                             'to an emergency or crisis situation, or if it would lead to a situation where the inspection or '
                             'audit would no longer be effective.',
          'requirement_description': None,
          'subchapter': 'Article 39: Inspections'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 39.6: The critical ICT third-party service provider shall submit to on-site inspections '
                             'ordered by decision of the Lead Overseer. The decision shall specify the subject matter and '
                             'purpose of the inspection, fix the date on which the inspection shall begin and shall indicate '
                             'the periodic penalty payments provided for in Article 35(6), the legal remedies available under '
                             'Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010, as well as the right to '
                             'have the decision reviewed by the Court of Justice.',
          'requirement_description': None,
          'subchapter': 'Article 39: Inspections'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 39.7: Where the officials and other persons authorised by the Lead Overseer find that a '
                             'critical ICT third-party service provider opposes an inspection ordered pursuant to this '
                             'Article, the Lead Overseer shall inform the critical ICT third-party service provider of the '
                             'consequences of such opposition, including the possibility for competent authorities of the '
                             'relevant financial entities to require financial entities to terminate the contractual '
                             'arrangements concluded with that critical ICT third-party service provider.',
          'requirement_description': None,
          'subchapter': 'Article 39: Inspections'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 40.1: When conducting oversight activities, in particular general investigations or '
                             'inspections, the Lead Overseer shall be assisted by a joint examination team established for '
                             'each critical ICT third-party service provider.',
          'requirement_description': None,
          'subchapter': 'Article 40: Ongoing oversight'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 40.2: The joint examination team referred to in paragraph 1 shall be composed of staff '
                             'members from:',
          'requirement_description': '(a) the ESAs;\n'
                                     '(b) the relevant competent authorities supervising the financial entities to which the '
                                     'critical ICT third-party service provider provides ICT services;\n'
                                     '(c) the national competent authority referred to in Article 32(4), point (e), on a '
                                     'voluntary basis;\n'
                                     '(d) one national competent authority from the Member State where the critical ICT '
                                     'third-party service provider is established, on a voluntary basis.\n'
                                     'Members of the joint examination team shall have expertise in ICT matters and in '
                                     'operational risk. The joint examination team shall work under the coordination of a '
                                     "designated Lead Overseer staff member (the 'Lead Overseer coordinator').",
          'subchapter': 'Article 40: Ongoing oversight'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 40.3: Within 3 months of the completion of an investigation or inspection, the Lead '
                             'Overseer, after consulting the Oversight Forum, shall adopt recommendations to be addressed to '
                             'the critical ICT third-party service provider pursuant to the powers referred to in Article 35.',
          'requirement_description': None,
          'subchapter': 'Article 40: Ongoing oversight'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 40.4: The recommendations referred to in paragraph 3 shall be immediately communicated '
                             'to the critical ICT third-party service provider and to the competent authorities of the '
                             'financial entities to which it provides ICT services.',
          'requirement_description': 'For the purposes of fulfilling the oversight activities, the Lead Overseer may take into '
                                     'consideration any relevant third-party certifications and ICT third-party internal or '
                                     'external audit reports made available by the critical ICT third-party service provider.',
          'subchapter': 'Article 40: Ongoing oversight'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 41.1: The ESAs shall, through the Joint Committee, develop draft regulatory technical '
                             'standards to specify:',
          'requirement_description': '(a) the information to be provided by an ICT third-party service provider in the '
                                     'application for a voluntary request to be designated as critical under Article 31(11);\n'
                                     '(b) the content, structure and format of the information to be submitted, disclosed or '
                                     'reported by the ICT third-party service providers pursuant to Article 35(1), including '
                                     'the template for providing information on subcontracting arrangements;\n'
                                     '(c) the criteria for determining the composition of the joint examination team ensuring '
                                     'a balanced participation of staff members from the ESAs and from the relevant competent '
                                     'authorities, their designation, tasks, and working arrangements.\n'
                                     "(d) the details of the competent authorities' assessment of the measures taken by "
                                     'critical ICT third-party service providers based on the recommendations of the Lead '
                                     'Overseer pursuant to Article 42(3).',
          'subchapter': 'Article 41: Harmonisation of conditions enabling the conduct of the oversight activities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 41.2: The ESAs shall submit those draft regulatory technical standards to the Commission '
                             'by 17 July 2024.',
          'requirement_description': 'Power is delegated to the Commission to supplement this Regulation by adopting the '
                                     'regulatory technical standards referred to in paragraph 1 in accordance with the '
                                     'procedure laid down in Articles 10 to 14 of Regulations (EU) No 1093/2010, (EU) No '
                                     '1094/2010 and (EU) No 1095/2010.',
          'subchapter': 'Article 41: Harmonisation of conditions enabling the conduct of the oversight activities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.1: Within 60 calendar days of the receipt of the recommendations issued by the Lead '
                             'Overseer pursuant to Article 35(1), point (d), critical ICT third-party service providers shall '
                             'either notify the Lead Overseer of their intention to follow the recommendations or provide a '
                             'reasoned explanation for not following such recommendations. The Lead Overseer shall immediately '
                             'transmit this information to the competent authorities of the financial entities concerned.',
          'requirement_description': None,
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.2: The Lead Overseer shall publicly disclose where a critical ICT third-party service '
                             'provider fails to notify the Lead Overseer in accordance with paragraph 1 or where the '
                             'explanation provided by the critical ICT third-party service provider is not deemed sufficient. '
                             'The information published shall disclose the identity of the critical ICT third-party service '
                             'provider as well as information on the type and nature of the non-compliance. Such information '
                             'shall be limited to what is relevant and proportionate for the purpose of ensuring public '
                             'awareness, unless such publication would cause disproportionate damage to the parties involved '
                             'or could seriously jeopardise the orderly functioning and integrity of financial markets or the '
                             'stability of the whole or part of the financial system of the Union.',
          'requirement_description': 'The Lead Overseer shall notify the ICT third-party service provider of that public '
                                     'disclosure.',
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.3: Competent authorities shall inform the relevant financial entities of the risks '
                             'identified in the recommendations addressed to critical ICT third-party service providers in '
                             'accordance with Article 35(1), point (d).',
          'requirement_description': 'When managing ICT third-party risk, financial entities shall take into account the risks '
                                     'referred to in the first subparagraph.',
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.4: Where a competent authority deems that a financial entity fails to take into '
                             'account or to sufficiently address within its management of ICT third-party risk the specific '
                             'risks identified in the recommendations, it shall notify the financial entity of the possibility '
                             'of a decision being taken, within 60 calendar days of the receipt of such notification, pursuant '
                             'to paragraph 6, in the absence of appropriate contractual arrangements aiming to address such '
                             'risks.',
          'requirement_description': None,
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.5: Upon receiving the reports referred to in Article 35(1), point (c), and prior to '
                             'taking a decision as referred to in paragraph 6 of this Article, competent authorities may, on a '
                             'voluntary basis, consult the competent authorities designated or established in accordance with '
                             'Directive (EU) 2022/2555 responsible for the supervision of an essential or important entity '
                             'subject to that Directive, which has been designated as a critical ICT third-party service '
                             'provider.',
          'requirement_description': None,
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.6: Competent authorities may, as a measure of last resort, following the notification '
                             'and, if appropriate, the consultation as set out in paragraph 4 and 5 of this Article, in '
                             'accordance with Article 50, take a decision requiring financial entities to temporarily suspend, '
                             'either in part or completely, the use or deployment of a service provided by the critical ICT '
                             'third-party service provider until the risks identified in the recommendations addressed to '
                             'critical ICT third-party service providers have been addressed. Where necessary, they may '
                             'require financial entities to terminate, in part or completely, the relevant contractual '
                             'arrangements concluded with the critical ICT third-party service providers.',
          'requirement_description': None,
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.7: Where a critical ICT third-party service provider refuses to endorse '
                             'recommendations, based on a divergent approach from the one advised by the Lead Overseer, and '
                             'such a divergent approach may adversely impact a large number of financial entities, or a '
                             'significant part of the financial sector, and individual warnings issued by competent '
                             'authorities have not resulted in consistent approaches mitigating the potential risk to '
                             'financial stability, the Lead Overseer may, after consulting the Oversight Forum, issue '
                             'non-binding and non-public opinions to competent authorities, in order to promote consistent and '
                             'convergent supervisory follow-up measures, as appropriate.',
          'requirement_description': None,
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.8: Upon receiving the reports referred to in Article 35(1), point (c), competent '
                             'authorities, when taking a decision as referred to in paragraph 6 of this Article, shall take '
                             'into account the type and magnitude of risk that is not addressed by the critical ICT '
                             'third-party service provider, as well as the seriousness of the non-compliance, having regard to '
                             'the following criteria:',
          'requirement_description': '(a) the gravity and the duration of the non-compliance;\n'
                                     '(b) whether the non-compliance has revealed serious weaknesses in the critical ICT '
                                     "third-party service provider's procedures, management systems, risk management and "
                                     'internal controls;\n'
                                     '(c) whether a financial crime was facilitated, occasioned or is otherwise attributable '
                                     'to the non-compliance;\n'
                                     '(d) whether the non-compliance has been intentional or negligent;\n'
                                     '(e) whether the suspension or termination of the contractual arrangements introduces a '
                                     "risk for continuity of the financial entity's business operations notwithstanding the "
                                     "financial entity's efforts to avoid disruption in the provision of its services;\n"
                                     '(f) where applicable, the opinion of the competent authorities designated or established '
                                     'in accordance with Directive (EU) 2022/2555 responsible for the supervision of an '
                                     'essential or important entity subject to that Directive, which has been designated as a '
                                     'critical ICT third-party service provider, requested on a voluntary basis in accordance '
                                     'with paragraph 5 of this Article. Competent authorities shall grant financial entities '
                                     'the necessary period of time to enable them to adjust the contractual arrangements with '
                                     'critical ICT third-party service providers in order to avoid detrimental effects on '
                                     'their digital operational resilience and to allow them to deploy exit strategies and '
                                     'transition plans as referred to in Article 28.',
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.9: The decision referred to in paragraph 6 of this Article shall be notified to the '
                             'members of the Oversight Forum referred to in Article 32(4), points (a), (b) and (c), and to the '
                             'JON.',
          'requirement_description': 'The critical ICT third-party service providers affected by the decisions provided for in '
                                     'paragraph 6 shall fully cooperate with the financial entities impacted, in particular in '
                                     'the context of the process of suspension or termination of their contractual '
                                     'arrangements.',
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.10:  Competent authorities shall regularly inform the Lead Overseer on the approaches '
                             'and measures taken in their supervisory tasks in relation to financial entities as well as on '
                             'the contractual arrangements concluded by financial entities where critical ICT third-party '
                             'service providers have not endorsed in part or entirely recommendations addressed to them by the '
                             'Lead Overseer.',
          'requirement_description': None,
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 42.11:  The Lead Overseer may, upon request, provide further clarifications on the '
                             'recommendations issued to guide the competent authorities on the follow-up measures.',
          'requirement_description': None,
          'subchapter': 'Article 42: Follow-up by competent authorities'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 43.1: The Lead Overseer shall, in accordance with the delegated act referred to in '
                             'paragraph 2 of this Article, charge critical ICT third-party service providers fees that fully '
                             "cover the Lead Overseer's necessary expenditure in relation to the conduct of oversight tasks "
                             'pursuant to this Regulation, including the reimbursement of any costs which may be incurred as a '
                             'result of work carried out by the joint examination team referred to in Article 40, as well as '
                             'the costs of advice provided by the independent experts as referred to in Article 32(4), second '
                             'subparagraph, in relation to matters falling under the remit of direct oversight activities.',
          'requirement_description': 'The amount of a fee charged to a critical ICT third-party service provider shall cover '
                                     'all costs derived from the execution of the duties set out in this Section and shall be '
                                     'proportionate to its turnover.',
          'subchapter': 'Article 43: Oversight fees'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 43.2: The Commission is empowered to adopt a delegated act in accordance with Article 57 '
                             'to supplement this Regulation by determining the amount of the fees and the way in which they '
                             'are to be paid by 17 July 2024.',
          'requirement_description': None,
          'subchapter': 'Article 43: Oversight fees'},
         {'chapter_title': 'Chapter V: Managing of ICT third-party risk',
          'conformity_questions': [],
          'objective_title': 'Article 44.1: Without prejudice to Article 36, EBA, ESMA and EIOPA may, in accordance with '
                             'Article 33 of Regulations (EU) No 1093/2010, (EU) No 1095/2010 and (EU) No 1094/2010, '
                             'respectively, conclude administrative arrangements with third-country regulatory and supervisory '
                             'authorities to foster international cooperation on ICT third-party risk across different '
                             'financial sectors, in particular by developing best practices for the review of ICT risk '
                             'management practices and controls, mitigation measures and incident responses.',
          'requirement_description': None,
          'subchapter': 'Article 44: International cooperation'},
         {'chapter_title': 'Chapter VI:  Information-sharing arrangements',
          'conformity_questions': ['Q-THR-01: Does the organization implement a threat awareness program that includes a '
                                   'cross-organization information-sharing capability? .'],
          'objective_title': 'Article 45.1: Financial entities may exchange amongst themselves cyber threat information and '
                             'intelligence, including indicators of compromise, tactics, techniques, and procedures, cyber '
                             'security alerts and configuration tools, to the extent that such information and intelligence '
                             'sharing:',
          'requirement_description': '(a) aims to enhance the digital operational resilience of financial entities, in '
                                     'particular through raising awareness in relation to cyber threats, limiting or impeding '
                                     "the cyber threats' ability to spread, supporting defence capabilities, threat detection "
                                     'techniques, mitigation strategies or response and recovery stages;\n'
                                     '(b) takes places within trusted communities of financial entities;\n'
                                     '(c) is implemented through information-sharing arrangements that protect the potentially '
                                     'sensitive nature of the information shared, and that are governed by rules of conduct in '
                                     'full respect of business confidentiality, protection of personal data in accordance with '
                                     'Regulation (EU) 2016/679 and guidelines on competition policy.',
          'subchapter': 'Article 45: Information-sharing arrangements on cyber threat information and intelligence'},
         {'chapter_title': 'Chapter VI:  Information-sharing arrangements',
          'conformity_questions': ['Q-THR-01: Does the organization implement a threat awareness program that includes a '
                                   'cross-organization information-sharing capability? .'],
          'objective_title': 'Article 45.2: For the purpose of paragraph 1, point (c), the information-sharing arrangements '
                             'shall define the conditions for participation and, where appropriate, shall set out the details '
                             'on the involvement of public authorities and the capacity in which they may be associated to the '
                             'information-sharing arrangements, on the involvement of ICT third-party service providers, and '
                             'on operational elements, including the use of dedicated IT platforms.',
          'requirement_description': None,
          'subchapter': 'Article 45: Information-sharing arrangements on cyber threat information and intelligence'},
         {'chapter_title': 'Chapter VI:  Information-sharing arrangements',
          'conformity_questions': ['Q-THR-01: Does the organization implement a threat awareness program that includes a '
                                   'cross-organization information-sharing capability? .'],
          'objective_title': 'Article 45.3: Financial entities shall notify competent authorities of their participation in '
                             'the information-sharing arrangements referred to in paragraph 1, upon validation of their '
                             'membership, or, as applicable, of the cessation of their membership, once it takes effect.',
          'requirement_description': None,
          'subchapter': 'Article 45: Information-sharing arrangements on cyber threat information and intelligence'}]
