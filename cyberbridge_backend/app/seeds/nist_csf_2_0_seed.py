# app/seeds/nist_csf_2_0_seed.py
import io
import logging
from .base_seed import BaseSeed
from app.models import models
from app.constants.nist_csf_2_0_connections import NIST_CSF_2_0_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class NistCsf20Seed(BaseSeed):
    """Seed NIST CSF 2.0 framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating NIST CSF 2.0 framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create NIST CSF 2.0 Framework
        nist_csf_2_0_framework, created = self.get_or_create(
            models.Framework,
            {"name": "NIST CSF 2.0", "organisation_id": default_org.id},
            {
                "name": "NIST CSF 2.0",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("NIST CSF 2.0 framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == nist_csf_2_0_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == nist_csf_2_0_framework.id
            ).all()

            logger.info(f"Found existing NIST CSF 2.0 framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            # Keep links in sync even when framework/objectives already exist.
            if not self.skip_wire_connections:
                self._wire_connections(nist_csf_2_0_framework, default_org, existing_objectives)
            self.db.commit()

            return {
                "framework": nist_csf_2_0_framework,
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
                description="NIST CSF 2.0 conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=nist_csf_2_0_framework.id,
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
                        "framework_id": nist_csf_2_0_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": nist_csf_2_0_framework.id
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
            self._wire_connections(nist_csf_2_0_framework, default_org, objectives_list)

        self.db.commit()

        logger.info(f"Created NIST CSF 2.0 framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": nist_csf_2_0_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _wire_connections(self, framework, org, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to NIST CSF 2.0 objectives using the NIST_CSF_2_0_CONNECTIONS mapping.
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
            logger.warning("Missing lookup defaults - skipping NIST CSF 2.0 connection wiring")
            return

        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in NIST_CSF_2_0_CONNECTIONS.values():
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

        logger.info(f"NIST CSF 2.0 wiring: {len(risk_name_to_id)} risks ready")

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

        logger.info(f"NIST CSF 2.0 wiring: {len(control_code_to_id)} controls ready")

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
                        logger.warning(f"NIST CSF 2.0 wiring: docx conversion failed for {policy_code}: {conv_err}")
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

        logger.info(f"NIST CSF 2.0 wiring: {len(policy_code_to_id)} policies ready")

        obj_title_to_id = {obj.title: obj.id for obj in objectives_list}
        policy_framework_pairs = set()

        obj_risk_count = 0
        obj_ctrl_count = 0
        pol_obj_count = 0
        ctrl_risk_count = 0
        ctrl_pol_count = 0
        planned_control_risk_pairs = set()
        planned_control_policy_pairs = set()

        for obj_title, conn in NIST_CSF_2_0_CONNECTIONS.items():
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
            f"NIST CSF 2.0 wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return ['Q-PRM-03: Does the organization identify and allocate resources for management, operational, technical and privacy '
         'requirements within business process planning for projects / initiatives?.',
         'Q-GOV-08: Does the organization define the context of its business model and document the mission of the '
         'organization?.',
         'Q-PRM-02: Does the organization address all capital planning and investment requests, including the resources needed '
         'to implement the security & privacy programs and documents all exceptions to this requirement? .',
         'Q-THR-01: Does the organization implement a threat awareness program that includes a cross-organization '
         'information-sharing capability? .',
         'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
         'Q-TPM-06: Does the organization control personnel security requirements including security roles and '
         'responsibilities for third-party providers?.',
         'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of critical systems, '
         'components and services using a supply chain risk assessment process? .',
         'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or outsourcing of '
         'technology-related services?.',
         'Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, regulatory and contractual '
         'controls?.',
         'Q-BCD-01: Does the organization facilitate the implementation of contingency planning controls?.',
         'Q-PRM-05: Does the organization identify critical system components and functions by performing a criticality '
         'analysis for critical systems, system components or services at pre-defined decision points in the Secure '
         'Development Life Cycle (SDLC)? .',
         'Q-PRM-06: Does the organization define business processes with consideration for cybersecurity and privacy that '
         'determines:   -  The resulting risk to organizational operations, assets, individuals and other organizations; and  '
         '-  Information protection needs arising from the defined business processes and revises the processes as necessary, '
         'until an achievable set of protection needs is obtained?.',
         'Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.',
         'Q-RSK-01: Does the organization facilitate the implementation of risk management controls?.',
         'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, risk response and risk '
         'monitoring;  -  Constraints affecting risk assessments, risk response and risk monitoring;  -  The organizational '
         'risk tolerance; and  -  Priorities and trade-offs considered by the organization for managing risk?.',
         'Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) associated with the '
         'development, acquisition, maintenance and disposal of systems, system components and services, including documenting '
         'selected mitigating actions and monitoring performance against those plans?.',
         'Q-GOV-16-CM: Does the organization perform and document a SWOT (Strength, Weakness, Opportunity and Threats) '
         'analysis as a part of risk management and assessment process?.',
         'Q-GOV-16-CM: Does the organization define materiality threshold criteria capable of designating an incident as '
         'material?.',
         'Q-RSK-12-CM: Does the organization ensure teams are committed to a culture that considers and communicates '
         'technology-related risk?.',
         'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) to assist senior management '
         'in performance monitoring and trend analysis of the cybersecurity and privacy program?.',
         'Q-GOV-14: Does the organization incorporate cybersecurity and privacy principles into Business As Usual (BAU) '
         'practices through executive leadership involvement?.',
         'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide monitoring controls?.',
         'Q-GOV-04: Does the organization assign a qualified individual with the mission and resources to centrally-manage '
         'coordinate, develop, implement and maintain an enterprise-wide cybersecurity and privacy program? .',
         'Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.',
         'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards '
         'and procedures?.',
         'Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the continuous monitoring strategy '
         'that includes monitoring the effectiveness of security & privacy controls, compliance and change management?.',
         'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly upon identifying new '
         'security vulnerabilities, including using outside sources for security vulnerability information? .',
         'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the likelihood and magnitude of '
         "harm, from unauthorized access, use, disclosure, disruption, modification or destruction of the organization's "
         'systems and data?.',
         'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
         'Q-TPM-05: Does the organization identify, regularly review and document third-party confidentiality, Non-Disclosure '
         "Agreements (NDAs) and other contracts that reflect the organization's needs to protect systems and data?.",
         'Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain? .',
         'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service Providers (TSP) for '
         'compliance with established contractual requirements for cybersecurity and privacy controls? .',
         'Q-TPM-11: Does the organization ensure response/recovery planning and testing are conducted with critical '
         'suppliers/providers? .',
         'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  '
         'Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined '
         'information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit '
         'by designated organizational officials? .',
         'Q-MON-01.3: Does the organization continuously monitor inbound and outbound communications traffic for unusual or '
         'unauthorized activities or conditions?.',
         'Q-MON-16: Does the organization detect and respond to anomalous behavior that could indicate account compromise or '
         'other malicious activities?.',
         'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain sufficient detail to '
         "assess the security of the network's architecture;  -  Reflect the current architecture of the network environment; "
         'and  -  Document all sensitive/regulated data flows?.',
         'Q-DCH-13: Does the organization govern how external parties, systems and services are used to securely store, '
         'process and transmit data? .',
         'Q-BCD-02: Does the organization identify and document the critical systems, applications and services that support '
         'essential missions and business functions?.',
         'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with applicable statutory, '
         'regulatory and contractual requirements? .',
         'Q-AST-03.2: Does the organization govern the chronology of the origin, development, ownership, location and changes '
         'to a system, system components and associated data?.',
         'Q-AST-02.8: Does the organization create and maintain a map of technology assets where sensitive/regulated data is '
         'stored, transmitted or processed?.',
         'Q-DCH-08: Does the organization securely dispose of media when it is no longer required, using formal procedures? .',
         'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity commensurate with the '
         'classification or sensitivity of the information prior to disposal, release out of organizational control or release '
         'for reuse?.',
         'Q-MNT-05: Does the organization authorize, monitor and control remote, non-local maintenance and diagnostic '
         'activities?.',
         'Q-MNT-02: Does the organization conduct controlled maintenance activities throughout the lifecycle of the system, '
         'application or service?.',
         'Q-PRM-07: Does the organization ensure changes to systems within the Secure Development Life Cycle (SDLC) are '
         'controlled through formal change control procedures? .',
         'Q-AST-11: Does the organization authorize, control and track technology assets entering and exiting organizational '
         'facilities? .',
         'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by recurring vulnerability scanning '
         'of systems and web applications?.',
         'Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.',
         'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
         'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and assess cybersecurity and '
         'data protection risks?.',
         'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, tracked and remediated?.',
         'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing basis and ensure assets are '
         'protected against known attacks? .',
         'Q-RSK-02.1: Does the organization prioritize the impact level for systems, applications and/or services to provide '
         'additional granularity on potential disruptions?.',
         'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
         'Q-CHG-02: Does the organization govern the technical configuration change control processes?.',
         'Q-CFG-02: Does the organization develop, document and maintain secure baseline configurations for technology '
         'platform that are consistent with industry-accepted system hardening standards? .',
         'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar change-detection technology, on '
         'critical assets to generate alerts for unauthorized modifications? .',
         'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of data being transmitted? .',
         'Q-TDA-14: Does the organization require system developers and integrators to perform configuration management during '
         'system design, development, implementation and operation?.',
         'Q-VPM-05: Does the organization conduct software patching for all deployed operating systems, applications and '
         'firmware?.',
         'Q-CPL-02.1: Does the organization implement an internal audit function that is capable of providing senior '
         "organization management with insights into the appropriateness of the organization's technology and information "
         'governance processes?.',
         'Q-CPL-04: Does the organization thoughtfully plan audits by including input from operational risk and compliance '
         'partners to minimize the impact of audit-related activities on business operations?.',
         'Q-IRO-05.1: Does the organization incorporate simulated events into incident response training to facilitate '
         'effective response by personnel in crisis situations?.',
         "Q-VPM-10: Does the organization utilize 'red team' exercises to simulate attempts by adversaries to compromise "
         'systems and applications in accordance with organization-defined rules of engagement? .',
         'Q-BCD-03: Does the organization adequately train contingency personnel and applicable stakeholders in their '
         'contingency roles and responsibilities?.',
         'Q-BCD-11.5: Does the organization utilize sampling of available backups to test recovery capabilities as part of '
         'business continuity plan testing?.',
         'Q-IRO-06: Does the organization formally test incident response capabilities through realistic exercises to '
         'determine the operational effectiveness of those capabilities?.',
         'Q-IRO-06.1: Does the organization coordinate incident response testing with organizational elements responsible for '
         'related plans? .',
         'Q-BCD-06: Does the organization keep contingency plans current with business needs, technology changes and feedback '
         'from contingency plan testing activities?.',
         "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' activity every time the "
         'contingency plan is activated?.',
         'Q-IRO-04.2: Does the organization regularly review and modify incident response practices to incorporate lessons '
         'learned, business process changes and industry developments, as necessary?.',
         'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving cybersecurity and privacy '
         'incidents to reduce the likelihood or impact of future incidents? .',
         'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for its cybersecurity and '
         'privacy programs?.',
         'Q-CPL-02: Does the organization provide a security & privacy controls oversight function that reports to the '
         "organization's executive leadership?.",
         'Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.',
         'Q-IRO-04: Does the organization maintain and make available a current and viable Incident Response Plan (IRP) to all '
         'stakeholders?.',
         'Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.',
         'Q-IAC-15: Does the organization proactively govern account management of individual, group, system, application, '
         'guest and temporary accounts?.',
         'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users and processes acting on '
         'behalf of organizational users? .',
         'Q-IAC-07: Does the organization utilize a formal user registration and de-registration process that governs the '
         'assignment of access rights? .',
         'Q-IAC-04: Does the organization uniquely and centrally Authenticate, Authorize and Audit (AAA) devices before '
         'establishing a connection using bidirectional authentication that is cryptographically- based and replay resistant?.',
         'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access? .',
         'Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations to ensure strong criteria '
         'for password-based authentication?.',
         'Q-NET-14: Does the organization define, control and review organization-approved, secure remote access methods?.',
         'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the confidentiality of data being '
         'transmitted? .',
         'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known '
         'public standards and trusted cryptographic technologies?.',
         'Q-CRY-01.3: Does the organization ensure the confidentiality and integrity of information during preparation for '
         'transmission and during reception with cryptographic mechanisms?.',
         'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over users and resources?.',
         'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only authorized access to processes '
         'necessary to accomplish assigned tasks in accordance with organizational business functions? .',
         'Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network '
         'security controls?.',
         'Q-NET-14.5: Does the organization define secure telecommuting practices and govern remote access to systems and data '
         'for remote workers? .',
         'Q-PES-03: Does the organization enforce physical access authorizations for all physical access points (including '
         'designated entry/exit points) to facilities (excluding those areas within the facility officially designated as '
         'publicly accessible)?.',
         'Q-PES-03.4: Does the organization enforce physical access to critical information systems or sensitive/regulated '
         'data, in addition to the physical access controls for the facility?.',
         'Q-SAT-04: Does the organization document, retain and monitor individual training activities, including basic '
         'security awareness training, ongoing awareness training and specific-system training?.',
         'Q-SAT-02: Does the organization provide all employees and contractors appropriate awareness education and training '
         'that is relevant for their job function? .',
         'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and business function '
         'representatives that are capable of addressing cybersecurity and privacy incident response operations?.',
         'Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness '
         'controls? .',
         'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before authorizing access to the '
         'system or performing assigned duties;   -  When required by system changes; and   -  Annually thereafter?.',
         'Q-SAT-03.5: Does the organization provides specific training for privileged users to ensure privileged users '
         'understand their unique roles and responsibilities .',
         'Q-DCH-12: Does the organization restrict removable media in accordance with data handling and acceptable usage '
         'parameters?.',
         'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect and report unauthorized '
         'changes to system files and configurations?.',
         'Q-END-06.1: Does the organization validate configurations through integrity checking of software and firmware?.',
         'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? .',
         'Q-PES-13: Does the organization protect the system from information leakage due to electromagnetic signals '
         'emanations? .',
         'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent unauthorized disclosure of data '
         'at rest? .',
         'Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify '
         'the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) '
         'and Recovery Point Objectives (RPOs)?.',
         'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of the backup process, as '
         'well as the integrity and availability of the data? .',
         'Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems to a known state after a '
         'disruption, compromise or failure? .',
         'Q-CFG-03: Does the organization configure systems to provide only essential capabilities by specifically prohibiting '
         'or restricting the use of ports, protocols, and/or services? .',
         'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized cybersecurity and privacy '
         'practices in the specification, design, development, implementation and modification of systems and services?.',
         'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate incidents in accordance with '
         'established timelines and procedures?.',
         'Q-END-03.1: Does the organization alert personnel when an unauthorized installation of software is detected? .',
         'Q-END-03: Does the organization prohibit user installation of software without explicitly assigned privileged '
         'status? .',
         'Q-CFG-05.1: Does the organization configure systems to generate an alert when the unauthorized installation of '
         'software is detected? .',
         'Q-CFG-04: Does the organization enforce software usage restrictions to comply with applicable contract agreements '
         'and copyright laws?.',
         'Q-CHG-04.2: Does the organization prevent the installation of software and firmware components without verification '
         'that the component has been digitally signed using an organization-approved certificate authority? .',
         'Q-TDA-09: Does the organization require system developers/integrators consult with cybersecurity and privacy '
         'personnel to:   -  Create and implement a Security Test and Evaluation (ST&E) plan;  -  Implement a verifiable flaw '
         'remediation process to correct weaknesses and deficiencies identified during the security testing and evaluation '
         'process; and  -  Document the results of the security testing/evaluation and flaw remediation processes?.',
         'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
         'Q-TDA-05: Does the organization require the developers of systems, system components or services to produce a design '
         "specification and security architecture that:   -  Is consistent with and supportive of the organization's security "
         "architecture which is established within and is an integrated part of the organization's enterprise architecture;  "
         '-  Accurately and completely describes the required security functionality and the allocation of security controls '
         'among physical and logical components; and  -  Expresses how individual security functions, mechanisms and services '
         'work together to provide required security capabilities and a unified approach to protection?.',
         'Q-TDA-08: Does the organization manage separate development, testing and operational environments to reduce the '
         'risks of unauthorized access or changes to the operational environment and to ensure no impact to production '
         'systems?.',
         'Q-NET-02: Does the organization implement security functions as a layered structure that minimizes interactions '
         'between layers of the design and avoiding any dependence by lower layers on the functionality or correctness of '
         'higher layers? .',
         'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to monitor and control '
         'communications at the external network boundary and at key internal boundaries within the network?.',
         'Q-NET-06: Does the organization logically or physically segment information flows to accomplish network '
         'segmentation?.',
         'Q-BCD-09: Does the organization establish an alternate processing site that provides security measures equivalent to '
         'that of the primary site?.',
         'Q-BCD-08: Does the organization establish an alternate storage site that includes both the assets and necessary '
         'agreements to permit the storage and recovery of system backup information? .',
         'Q-BCD-12.2: Does the organization implement real-time or near-real-time failover capability to maintain availability '
         'of critical systems, applications and/or services?.',
         'Q-SEA-07.2: Does the organization enable systems to fail to an organization-defined known-state for types of '
         'failures, preserving system state information in failure? .',
         'Q-CAP-01: Does the organization facilitate the implementation of capacity management controls to ensure optimal '
         'system performance to meet expected and anticipated future capacity requirements?.',
         'Q-CAP-03: Does the organization conducted capacity planning so that necessary capacity for information processing, '
         'telecommunications and environmental support will exist during contingency operations? .',
         'Q-MON-16.3: Does the organization monitor for unauthorized activities, accounts, connections, devices and software?.',
         'Q-END-10: Does the organization address mobile code / operating system-independent applications? .',
         'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate malicious code?.',
         'Q-PES-05: Does the organization monitor for, detect and respond to physical security incidents?.',
         'Q-MON-16.1: Does the organization monitor internal personnel activity for potential security incidents?.',
         'Q-MON-16.2: Does the organization monitor third-party personnel activity for potential security incidents?.',
         "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, "
         'containment, eradication and recovery?.',
         'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across the enterprise by a '
         'Security Incident Event Manager (SIEM) or similar automated tool, to maintain situational awareness?.',
         'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy incidents? .',
         'Q-MON-06: Does the organization provide an event log report generation capability to aid in detecting and assessing '
         'anomalous activities? .',
         'Q-IRO-03: Does the organization define specific Indicators of Compromise (IOC) that identify the potential impact of '
         'likely cybersecurity events?.',
         'Q-IRO-08: Does the organization perform digital forensics and maintain the integrity of the chain of custody? .',
         'Q-IRO-02.6: Does the organization automatically disable systems involved in an incident that meet organizational '
         'criteria to be automatically disabled upon detection?.',
         'Q-IRO-02.3: Does the organization dynamically reconfigure information system components as part of the incident '
         'response capability? .',
         'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational incident response personnel '
         'within organization-defined time-periods; and  -  Externally to regulatory authorities and affected parties, as '
         'necessary?.',
         'Q-IRO-17-CM: Does the organization establish a post-incident procedure to verify the integrity of the affected '
         'systems before restoring them to normal operations?.',
         'Q-IRO-16: Does the organization proactively manage public relations associated with an incident and employ '
         'appropriate measures to repair the reputation of the organization?.']

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-PRM-03: Does the organization identify and allocate resources for management, '
                                   'operational, technical and privacy requirements within business process planning for '
                                   'projects / initiatives?.',
                                   'Q-GOV-08: Does the organization define the context of its business model and document the '
                                   'mission of the organization?.',
                                   'Q-PRM-02: Does the organization address all capital planning and investment requests, '
                                   'including the resources needed to implement the security & privacy programs and documents '
                                   'all exceptions to this requirement? .',
                                   'Q-THR-01: Does the organization implement a threat awareness program that includes a '
                                   'cross-organization information-sharing capability? .'],
          'objective_title': 'GV.OC-01:  The organizational mission is understood and informs cybersecurity risk management',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     "Ex1: Share the organization's mission (e.g., through vision and mission statements, "
                                     'marketing, and service strategies) to provide a basis for identifying risks that may '
                                     'impede that mission',
          'subchapter': 'GV.OC: Organizational Context '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-TPM-06: Does the organization control personnel security requirements including security '
                                   'roles and responsibilities for third-party providers?.',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.'],
          'objective_title': 'GV.OC-02:  Internal and external stakeholders are understood, and their needs and expectations '
                             'regarding cybersecurity risk management are understood and considered',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Identify relevant internal stakeholders and their cybersecurity-related '
                                     'expectations (e.g., performance and risk expectations of officers, directors, and '
                                     'advisors; cultural expectations of employees)\n'
                                     'Ex2: Identify relevant external stakeholders and their cybersecurity-related '
                                     'expectations (e.g., privacy expectations of customers, business expectations of '
                                     'partnerships, compliance expectations of regulators, ethics expectations of society)',
          'subchapter': 'GV.OC: Organizational Context '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, '
                                   'regulatory and contractual controls?.'],
          'objective_title': 'GV.OC-03:  Legal, regulatory, and contractual requirements regarding cybersecurity - including '
                             'privacy and civil liberties obligations - are understood and managed',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Determine a process to track and manage legal and regulatory requirements regarding '
                                     "protection of individuals' information (e.g., Health Insurance Portability and "
                                     'Accountability Act, California Consumer Privacy Act, General Data Protection '
                                     'Regulation)\n'
                                     'Ex2: Determine a process to track and manage contractual requirements for cybersecurity '
                                     'management of supplier, customer, and partner information\n'
                                     "Ex3: Align the organization's cybersecurity strategy with legal, regulatory, and "
                                     'contractual requirements',
          'subchapter': 'GV.OC: Organizational Context '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-BCD-01: Does the organization facilitate the implementation of contingency planning '
                                   'controls?.',
                                   'Q-PRM-05: Does the organization identify critical system components and functions by '
                                   'performing a criticality analysis for critical systems, system components or services at '
                                   'pre-defined decision points in the Secure Development Life Cycle (SDLC)? .',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.'],
          'objective_title': 'GV.OC-04:  Critical objectives, capabilities, and services that stakeholders depend on or expect '
                             'from the organization are understood and communicated',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Establish criteria for determining the criticality of capabilities and services as '
                                     'viewed by internal and external stakeholders\n'
                                     'Ex2: Determine (e.g., from a business impact analysis) assets and business operations '
                                     'that are vital to achieving mission objectives and the potential impact of a loss (or '
                                     'partial loss) of such operations\n'
                                     'Ex3: Establish and communicate resilience objectives (e.g., recovery time objectives) '
                                     'for delivering critical capabilities and services in various operating states (e.g., '
                                     'under attack, during recovery, normal operation)',
          'subchapter': 'GV.OC: Organizational Context '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-PRM-05: Does the organization identify critical system components and functions by '
                                   'performing a criticality analysis for critical systems, system components or services at '
                                   'pre-defined decision points in the Secure Development Life Cycle (SDLC)? .',
                                   'Q-PRM-06: Does the organization define business processes with consideration for '
                                   'cybersecurity and privacy that determines:   -  The resulting risk to organizational '
                                   'operations, assets, individuals and other organizations; and  -  Information protection '
                                   'needs arising from the defined business processes and revises the processes as necessary, '
                                   'until an achievable set of protection needs is obtained?.',
                                   'Q-GOV-08: Does the organization define the context of its business model and document the '
                                   'mission of the organization?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .'],
          'objective_title': 'GV.OC-05:  Outcomes, capabilities, and services that the organization depends on are understood '
                             'and communicated',
          'requirement_description': 'Implementation Examples: \n'
                                     "Ex1: Create an inventory of the organization's dependencies on external resources (e.g., "
                                     'facilities, cloud-based hosting providers) and their relationships to organizational '
                                     'assets and business functions\n'
                                     'Ex2: Identify and document external dependencies that are potential points of failure '
                                     "for the organization's critical capabilities and services, and share that information "
                                     'with appropriate personnel\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.OC: Organizational Context '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.'],
          'objective_title': 'GV.RM-01:  Risk management objectives are established and agreed to by organizational '
                             'stakeholders',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Update near-term and long-term cybersecurity risk management objectives as part of '
                                     'annual strategic planning and when major changes occur\n'
                                     'Ex2: Establish measurable objectives for cybersecurity risk management (e.g., manage the '
                                     'quality of user training, ensure adequate risk protection for industrial control '
                                     'systems)\n'
                                     'Ex3: Senior leaders agree about cybersecurity objectives and use them for measuring and '
                                     'managing risk and performance',
          'subchapter': 'GV.RM: Risk Management Strategy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.',
                                   'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, '
                                   'risk response and risk monitoring;  -  Constraints affecting risk assessments, risk '
                                   'response and risk monitoring;  -  The organizational risk tolerance; and  -  Priorities '
                                   'and trade-offs considered by the organization for managing risk?.'],
          'objective_title': 'GV.RM-02:  Risk appetite and risk tolerance statements are established, communicated, and '
                             'maintained',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Determine and communicate risk appetite statements that convey expectations about '
                                     'the appropriate level of risk for the organization\n'
                                     'Ex2: Translate risk appetite statements into specific, measurable, and broadly '
                                     'understandable risk tolerance statements\n'
                                     'Ex3: Refine organizational objectives and risk appetite periodically based on known risk '
                                     'exposure and residual risk',
          'subchapter': 'GV.RM: Risk Management Strategy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.'],
          'objective_title': 'GV.RM-03:  Cybersecurity risk management activities and outcomes are included in enterprise risk '
                             'management processes',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Aggregate and manage cybersecurity risks alongside other enterprise risks (e.g., '
                                     'compliance, financial, operational, regulatory, reputational, safety)\n'
                                     'Ex2: Include cybersecurity risk managers in enterprise risk management planning\n'
                                     'Ex3: Establish criteria for escalating cybersecurity risks within enterprise risk '
                                     'management',
          'subchapter': 'GV.RM: Risk Management Strategy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.',
                                   'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, '
                                   'risk response and risk monitoring;  -  Constraints affecting risk assessments, risk '
                                   'response and risk monitoring;  -  The organizational risk tolerance; and  -  Priorities '
                                   'and trade-offs considered by the organization for managing risk?.'],
          'objective_title': 'GV.RM-04:  Strategic direction that describes appropriate risk response options is established '
                             'and communicated',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Specify criteria for accepting and avoiding cybersecurity risk for various '
                                     'classifications of data\n'
                                     'Ex2: Determine whether to purchase cybersecurity insurance\n'
                                     'Ex3: Document conditions under which shared responsibility models are acceptable (e.g., '
                                     'outsourcing certain cybersecurity functions, having a third party perform financial '
                                     'transactions on behalf of the organization, using public cloud-based services)',
          'subchapter': 'GV.RM: Risk Management Strategy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': 'GV.RM-05:  Lines of communication across the organization are established for cybersecurity '
                             'risks, including risks from suppliers and other third parties',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Determine how to update senior executives, directors, and management on the '
                                     "organization's cybersecurity posture at agreed-upon intervals\n"
                                     'Ex2: Identify how all departments across the organization - such as management, '
                                     'operations, internal auditors, legal, acquisition, physical security, and HR - will '
                                     'communicate with each other about cybersecurity risks',
          'subchapter': 'GV.RM: Risk Management Strategy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.'],
          'objective_title': 'GV.RM-06:  A standardized method for calculating, documenting, categorizing, and prioritizing '
                             'cybersecurity risks is established and communicated',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Establish criteria for using a quantitative approach to cybersecurity risk '
                                     'analysis, and specify probability and exposure formulas\n'
                                     'Ex2: Create and use templates (e.g., a risk register) to document cybersecurity risk '
                                     'information (e.g., risk description, exposure, treatment, and ownership)\n'
                                     'Ex3: Establish criteria for risk prioritization at the appropriate levels within the '
                                     'enterprise\n'
                                     'Ex4: Use a consistent list of risk categories to support integrating, aggregating, and '
                                     'comparing cybersecurity risks',
          'subchapter': 'GV.RM: Risk Management Strategy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-GOV-16-CM: Does the organization perform and document a SWOT (Strength, Weakness, '
                                   'Opportunity and Threats) analysis as a part of risk management and assessment process?.',
                                   'Q-GOV-16-CM: Does the organization define materiality threshold criteria capable of '
                                   'designating an incident as material?.'],
          'objective_title': 'GV.RM-07:  Strategic opportunities (i.e., positive risks) are characterized and are included in '
                             'organizational cybersecurity risk discussions',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Define and communicate guidance and methods for identifying opportunities and '
                                     'including them in risk discussions (e.g., strengths, weaknesses, opportunities, and '
                                     'threats [SWOT] analysis)\n'
                                     'Ex2: Identify stretch goals and document them\n'
                                     'Ex3: Calculate, document, and prioritize positive risks alongside negative risks',
          'subchapter': 'GV.RM: Risk Management Strategy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-12-CM: Does the organization ensure teams are committed to a culture that considers '
                                   'and communicates technology-related risk?.',
                                   'Q-GOV-05.2: Does the organization develop, report and monitor Key Risk Indicators (KRIs) '
                                   'to assist senior management in performance monitoring and trend analysis of the '
                                   'cybersecurity and privacy program?.',
                                   'Q-GOV-14: Does the organization incorporate cybersecurity and privacy principles into '
                                   'Business As Usual (BAU) practices through executive leadership involvement?.'],
          'objective_title': 'GV.RR-01:  Organizational leadership is responsible and accountable for cybersecurity risk and '
                             'fosters a culture that is risk-aware, ethical, and continually improving',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Leaders (e.g., directors) agree on their roles and responsibilities in developing, '
                                     "implementing, and assessing the organization's cybersecurity strategy\n"
                                     "Ex2: Share leaders' expectations regarding a secure and ethical culture, especially when "
                                     'current events present the opportunity to highlight positive or negative examples of '
                                     'cybersecurity risk management\n'
                                     'Ex3: Leaders direct the CISO to maintain a comprehensive cybersecurity risk strategy and '
                                     'review and update it at least annually and after major events\n'
                                     'Ex4: Conduct reviews to ensure adequate authority and coordination among those '
                                     'responsible for managing cybersecurity risk',
          'subchapter': 'GV.RR: Roles, Responsibilities, and Authorities '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.',
                                   'Q-TPM-06: Does the organization control personnel security requirements including security '
                                   'roles and responsibilities for third-party providers?.',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? '
                                   '.'],
          'objective_title': 'GV.RR-02:  Roles, responsibilities, and authorities related to cybersecurity risk management are '
                             'established, communicated, understood, and enforced',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Document risk management roles and responsibilities in policy\n'
                                     'Ex2: Document who is responsible and accountable for cybersecurity risk management '
                                     'activities and how those teams and individuals are to be consulted and informed\n'
                                     'Ex3: Include cybersecurity responsibilities and performance requirements in personnel '
                                     'descriptions\n'
                                     'Ex4: Document performance goals for personnel with cybersecurity risk management '
                                     'responsibilities, and periodically measure performance to identify areas for '
                                     'improvement\n'
                                     'Ex5: Clearly articulate cybersecurity responsibilities within operations, risk '
                                     'functions, and internal audit functions',
          'subchapter': 'GV.RR: Roles, Responsibilities, and Authorities '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.'],
          'objective_title': 'GV.RR-03:  Adequate resources are allocated commensurate with the cybersecurity risk strategy, '
                             'roles, responsibilities, and policies',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Conduct periodic management reviews to ensure that those given cybersecurity risk '
                                     'management responsibilities have the necessary authority\n'
                                     'Ex2: Identify resource allocation and investment in line with risk tolerance and '
                                     'response\n'
                                     'Ex3: Provide adequate and sufficient people, process, and technical resources to support '
                                     'the cybersecurity strategy',
          'subchapter': 'GV.RR: Roles, Responsibilities, and Authorities '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-HRS-01: Does the organization facilitate the implementation of personnel security '
                                   'controls?.'],
          'objective_title': 'GV.RR-04:  Cybersecurity is included in human resources practices',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Integrate cybersecurity risk management considerations into human resources '
                                     'processes (e.g., personnel screening, onboarding, change notification, offboarding)\n'
                                     'Ex2: Consider cybersecurity knowledge to be a positive factor in hiring, training, and '
                                     'retention decisions\n'
                                     'Ex3: Conduct background checks prior to onboarding new personnel for sensitive roles, '
                                     'and periodically repeat background checks for personnel with such roles\n'
                                     'Ex4: Define and enforce obligations for personnel to be aware of, adhere to, and uphold '
                                     'security policies as they relate to their roles',
          'subchapter': 'GV.RR: Roles, Responsibilities, and Authorities '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': 'GV.PO-01:  Policy for managing cybersecurity risks is established based on organizational '
                             'context, cybersecurity strategy, and priorities and is communicated and enforced',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Create, disseminate, and maintain an understandable, usable risk management policy '
                                     'with statements of management intent, expectations, and direction\n'
                                     'Ex2: Periodically review policy and supporting processes and procedures to ensure that '
                                     'they align with risk management strategy objectives and priorities, as well as the '
                                     'high-level direction of the cybersecurity policy\n'
                                     'Ex3: Require approval from senior management on policy\n'
                                     'Ex4: Communicate cybersecurity risk management policy and supporting processes and '
                                     'procedures across the organization\n'
                                     'Ex5: Require personnel to acknowledge receipt of policy when first hired, annually, and '
                                     'whenever policy is updated',
          'subchapter': 'GV.PO: Policy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': 'GV.PO-02:  Policy for managing cybersecurity risks is reviewed, updated, communicated, and '
                             'enforced to reflect changes in requirements, threats, technology, and organizational mission',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Update policy based on periodic reviews of cybersecurity risk management results to '
                                     'ensure that policy and supporting processes and procedures adequately maintain risk at '
                                     'an acceptable level\n'
                                     "Ex2: Provide a timeline for reviewing changes to the organization's risk environment "
                                     "(e.g., changes in risk or in the organization's mission objectives), and communicate "
                                     'recommended policy updates\n'
                                     'Ex3: Update policy to reflect changes in legal and regulatory requirements\n'
                                     'Ex4: Update policy to reflect changes in technology (e.g., adoption of artificial '
                                     'intelligence) and changes to the business (e.g., acquisition of a new business, new '
                                     'contract requirements)',
          'subchapter': 'GV.PO: Policy '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the '
                                   'continuous monitoring strategy that includes monitoring the effectiveness of security & '
                                   'privacy controls, compliance and change management?.',
                                   'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .'],
          'objective_title': 'GV.OV-01:  Cybersecurity risk management strategy outcomes are reviewed to inform and adjust '
                             'strategy and direction',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Measure how well the risk management strategy and risk results have helped leaders '
                                     'make decisions and achieve organizational objectives\n'
                                     'Ex2: Examine whether cybersecurity risk strategies that impede operations or innovation '
                                     'should be adjusted',
          'subchapter': 'GV.OV: Oversight '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?.",
                                   'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
                                   'Q-RSK-01: Does the organization facilitate the implementation of risk management '
                                   'controls?.'],
          'objective_title': 'GV.OV-02:  The cybersecurity risk management strategy is reviewed and adjusted to ensure '
                             'coverage of organizational requirements and risks',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Review audit findings to confirm whether the existing cybersecurity strategy has '
                                     'ensured compliance with internal and external requirements\n'
                                     'Ex2: Review the performance oversight of those in cybersecurity-related roles to '
                                     'determine whether policy changes are necessary\n'
                                     'Ex3: Review strategy in light of cybersecurity incidents',
          'subchapter': 'GV.OV: Oversight '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the '
                                   'continuous monitoring strategy that includes monitoring the effectiveness of security & '
                                   'privacy controls, compliance and change management?.'],
          'objective_title': 'GV.OV-03:  Organizational cybersecurity risk management performance is evaluated and reviewed '
                             'for adjustments needed',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Review key performance indicators (KPIs) to ensure that organization-wide policies '
                                     'and procedures achieve objectives\n'
                                     'Ex2: Review key risk indicators (KRIs) to identify risks the organization faces, '
                                     'including likelihood and potential impact\n'
                                     'Ex3: Collect and communicate metrics on cybersecurity risk management with senior '
                                     'leadership',
          'subchapter': 'GV.OV: Oversight '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': 'GV.SC-01:  A cybersecurity supply chain risk management program, strategy, objectives, policies, '
                             'and processes are established and agreed to by organizational stakeholders',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Establish a strategy that expresses the objectives of the cybersecurity supply '
                                     'chain risk management program\n'
                                     'Ex2: Develop the cybersecurity supply chain risk management program, including a plan '
                                     '(with milestones), policies, and procedures that guide implementation and improvement of '
                                     'the program, and share the policies and procedures with the organizational stakeholders\n'
                                     'Ex3: Develop and implement program processes based on the strategy, objectives, '
                                     'policies, and procedures that are agreed upon and performed by the organizational '
                                     'stakeholders\n'
                                     'Ex4: Establish a cross-organizational mechanism that ensures alignment between functions '
                                     'that contribute to cybersecurity supply chain risk management, such as cybersecurity, '
                                     'IT, operations, legal, human resources, and engineering\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? '
                                   '.'],
          'objective_title': 'GV.SC-02:  Cybersecurity roles and responsibilities for suppliers, customers, and partners are '
                             'established, communicated, and coordinated internally and externally',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Identify one or more specific roles or positions that will be responsible and '
                                     'accountable for planning, resourcing, and executing cybersecurity supply chain risk '
                                     'management activities\n'
                                     'Ex2: Document cybersecurity supply chain risk management roles and responsibilities in '
                                     'policy\n'
                                     'Ex3: Create responsibility matrixes to document who will be responsible and accountable '
                                     'for cybersecurity supply chain risk management activities and how those teams and '
                                     'individuals will be consulted and informed\n'
                                     'Ex4: Include cybersecurity supply chain risk management responsibilities and performance '
                                     'requirements in personnel descriptions to ensure clarity and improve accountability\n'
                                     'Ex5: Document performance goals for personnel with cybersecurity risk '
                                     'management-specific responsibilities, and periodically measure them to demonstrate and '
                                     'improve performance\n'
                                     'Ex6: Develop roles and responsibilities for suppliers, customers, and business partners '
                                     'to address shared responsibilities for applicable cybersecurity risks, and integrate '
                                     'them into organizational policies and applicable third-party agreements\n'
                                     'Ex7: Internally communicate cybersecurity supply chain risk management roles and '
                                     'responsibilities for third parties\n'
                                     'Ex8: Establish rules and protocols for information sharing and reporting processes '
                                     'between the organization and its suppliers\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.'],
          'objective_title': 'GV.SC-03:  Cybersecurity supply chain risk management is integrated into cybersecurity and '
                             'enterprise risk management, risk assessment, and improvement processes',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Identify areas of alignment and overlap with cybersecurity and enterprise risk '
                                     'management\n'
                                     'Ex2: Establish integrated control sets for cybersecurity risk management and '
                                     'cybersecurity supply chain risk management\n'
                                     'Ex3: Integrate cybersecurity supply chain risk management into improvement processes\n'
                                     'Ex4: Escalate material cybersecurity risks in supply chains to senior management, and '
                                     'address them at the enterprise risk management level\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.'],
          'objective_title': 'GV.SC-04:  Suppliers are known and prioritized by criticality',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Develop criteria for supplier criticality based on, for example, the sensitivity of '
                                     "data processed or possessed by suppliers, the degree of access to the organization's "
                                     "systems, and the importance of the products or services to the organization's mission\n"
                                     'Ex2: Keep a record of all suppliers, and prioritize suppliers based on the criticality '
                                     'criteria\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': 'GV.SC-05:  Requirements to address cybersecurity risks in supply chains are established, '
                             'prioritized, and integrated into contracts and other types of agreements with suppliers and '
                             'other relevant third parties',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Establish security requirements for suppliers, products, and services commensurate '
                                     'with their criticality level and potential impact if compromised\n'
                                     'Ex2: Include all cybersecurity and supply chain requirements that third parties must '
                                     'follow and how compliance with the requirements may be verified in default contractual '
                                     'language\n'
                                     'Ex3: Define the rules and protocols for information sharing between the organization and '
                                     'its suppliers and sub-tier suppliers in agreements\n'
                                     'Ex4: Manage risk by including security requirements in agreements based on their '
                                     'criticality and potential impact if compromised\n'
                                     'Ex5: Define security requirements in service-level agreements (SLAs) for monitoring '
                                     'suppliers for acceptable security performance throughout the supplier relationship '
                                     'lifecycle\n'
                                     'Ex6: Contractually require suppliers to disclose cybersecurity features, functions, and '
                                     'vulnerabilities of their products and services for the life of the product or the term '
                                     'of service\n'
                                     'Ex7: Contractually require suppliers to provide and maintain a current component '
                                     'inventory (e.g., software or hardware bill of materials) for critical products\n'
                                     'Ex8: Contractually require suppliers to vet their employees and guard against insider '
                                     'threats\n'
                                     'Ex9: Contractually require suppliers to provide evidence of performing acceptable '
                                     'security practices through, for example, self-attestation, conformance to known '
                                     'standards, certifications, or inspections\n'
                                     'Ex10: Specify in contracts and other agreements the rights and responsibilities of the '
                                     'organization, its suppliers, and their supply chains, with respect to potential '
                                     'cybersecurity risks\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': 'GV.SC-06:  Planning and due diligence are performed to reduce risks before entering into formal '
                             'supplier or other third-party relationships',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Perform thorough due diligence on prospective suppliers that is consistent with '
                                     'procurement planning and commensurate with the level of risk, criticality, and '
                                     'complexity of each supplier relationship\n'
                                     'Ex2: Assess the suitability of the technology and cybersecurity capabilities and the '
                                     'risk management practices of prospective suppliers\n'
                                     'Ex3: Conduct supplier risk assessments against business and applicable cybersecurity '
                                     'requirements\n'
                                     'Ex4: Assess the authenticity, integrity, and security of critical products prior to '
                                     'acquisition and use\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .',
                                   'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.'],
          'objective_title': 'GV.SC-07:  The risks posed by a supplier, their products and services, and other third parties '
                             'are understood, recorded, prioritized, assessed, responded to, and monitored over the course of '
                             'the relationship',
          'requirement_description': 'Implementation Examples: \n'
                                     "Ex1: Adjust assessment formats and frequencies based on the third party's reputation and "
                                     'the criticality of the products or services they provide\n'
                                     "Ex2: Evaluate third parties' evidence of compliance with contractual cybersecurity "
                                     'requirements, such as self-attestations, warranties, certifications, and other '
                                     'artifacts\n'
                                     'Ex3: Monitor critical suppliers to ensure that they are fulfilling their security '
                                     'obligations throughout the supplier relationship lifecycle using a variety of methods '
                                     'and techniques, such as inspections, audits, tests, or other forms of evaluation\n'
                                     'Ex4: Monitor critical suppliers, services, and products for changes to their risk '
                                     'profiles, and reevaluate supplier criticality and risk impact accordingly\n'
                                     'Ex5: Plan for unexpected supplier and supply chain-related interruptions to ensure '
                                     'business continuity\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .'],
          'objective_title': 'GV.SC-08:  Relevant suppliers and other third parties are included in incident planning, '
                             'response, and recovery activities',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Define and use rules and protocols for reporting incident response and recovery '
                                     'activities and the status between the organization and its suppliers\n'
                                     'Ex2: Identify and document the roles and responsibilities of the organization and its '
                                     'suppliers for incident response\n'
                                     'Ex3: Include critical suppliers in incident response exercises and simulations\n'
                                     'Ex4: Define and coordinate crisis communication methods and protocols between the '
                                     'organization and its critical suppliers\n'
                                     'Ex5: Conduct collaborative lessons learned sessions with critical suppliers\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': 'GV.SC-09:  Supply chain security practices are integrated into cybersecurity and enterprise risk '
                             'management programs, and their performance is monitored throughout the technology product and '
                             'service life cycle',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Policies and procedures require provenance records for all acquired technology '
                                     'products and services\n'
                                     'Ex2: Periodically provide risk reporting to leaders about how acquired components are '
                                     'proven to be untampered and authentic\n'
                                     'Ex3: Communicate regularly among cybersecurity risk managers and operations personnel '
                                     'about the need to acquire software patches, updates, and upgrades only from '
                                     'authenticated and trustworthy software providers\n'
                                     'Ex4: Review policies to ensure that they require approved supplier personnel to perform '
                                     'maintenance on supplier products\n'
                                     'Ex5: Policies and procedure require checking upgrades to critical hardware for '
                                     'unauthorized changes\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'GV: GOVERN ',
          'conformity_questions': ['Q-RSK-09: Does the organization develop a plan for Supply Chain Risk Management (SCRM) '
                                   'associated with the development, acquisition, maintenance and disposal of systems, system '
                                   'components and services, including documenting selected mitigating actions and monitoring '
                                   'performance against those plans?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': 'GV.SC-10:  Cybersecurity supply chain risk management plans include provisions for activities '
                             'that occur after the conclusion of a partnership or service agreement',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Establish processes for terminating critical relationships under both normal and '
                                     'adverse circumstances\n'
                                     'Ex2: Define and implement plans for component end-of-life maintenance support and '
                                     'obsolescence\n'
                                     'Ex3: Verify that supplier access to organization resources is deactivated promptly when '
                                     'it is no longer needed\n'
                                     "Ex4: Verify that assets containing the organization's data are returned or properly "
                                     'disposed of in a timely, controlled, and safe manner\n'
                                     'Ex5: Develop and execute a plan for terminating or transitioning supplier relationships '
                                     'that takes supply chain security risk and resiliency into account\n'
                                     'Ex6: Mitigate risks to data and systems created by supplier termination\n'
                                     'Ex7: Manage data leakage risks associated with supplier termination\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'GV.SC: Cybersecurity Supply Chain Risk Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .'],
          'objective_title': 'ID.AM-01:  Inventories of hardware managed by the organization are maintained',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Maintain inventories for all types of hardware, including IT, IoT, OT, and mobile '
                                     'devices\n'
                                     'Ex2: Constantly monitor networks to detect new hardware and automatically update '
                                     'inventories',
          'subchapter': 'ID.AM: Asset Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .'],
          'objective_title': 'ID.AM-02:  Inventories of software, services, and systems managed by the organization are '
                             'maintained',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Maintain inventories for all types of software and services, including '
                                     'commercial-off-the-shelf, open-source, custom applications, API services, and '
                                     'cloud-based applications and services\n'
                                     'Ex2: Constantly monitor all platforms, including containers and virtual machines, for '
                                     'software and service inventory changes\n'
                                     "Ex3: Maintain an inventory of the organization's systems",
          'subchapter': 'ID.AM: Asset Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-MON-01.3: Does the organization continuously monitor inbound and outbound communications '
                                   'traffic for unusual or unauthorized activities or conditions?.',
                                   'Q-MON-16: Does the organization detect and respond to anomalous behavior that could '
                                   'indicate account compromise or other malicious activities?.',
                                   'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain '
                                   "sufficient detail to assess the security of the network's architecture;  -  Reflect the "
                                   'current architecture of the network environment; and  -  Document all sensitive/regulated '
                                   'data flows?.'],
          'objective_title': "ID.AM-03:  Representations of the organization's authorized network communication and internal "
                             'and external network data flows are maintained',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     "Ex1: Maintain baselines of communication and data flows within the organization's wired "
                                     'and wireless networks\n'
                                     'Ex2: Maintain baselines of communication and data flows between the organization and '
                                     'third parties\n'
                                     "Ex3: Maintain baselines of communication and data flows for the organization's "
                                     'infrastructure-as-a-service (IaaS) usage\n'
                                     'Ex4: Maintain documentation of expected network ports, protocols, and services that are '
                                     'typically used among authorized systems',
          'subchapter': 'ID.AM: Asset Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-DCH-13: Does the organization govern how external parties, systems and services are used '
                                   'to securely store, process and transmit data? .'],
          'objective_title': 'ID.AM-04:  Inventories of services provided by suppliers are maintained',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Inventory all external services used by the organization, including third-party '
                                     'infrastructure-as-a-service (IaaS), platform-as-a-service (PaaS), and '
                                     'software-as-a-service (SaaS) offerings; APIs; and other externally hosted application '
                                     'services\n'
                                     'Ex2: Update the inventory when a new external service is going to be utilized to ensure '
                                     "adequate cybersecurity risk management monitoring of the organization's use of that "
                                     'service\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'ID.AM: Asset Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-BCD-02: Does the organization identify and document the critical systems, applications '
                                   'and services that support essential missions and business functions?.',
                                   'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with '
                                   'applicable statutory, regulatory and contractual requirements? .'],
          'objective_title': 'ID.AM-05:  Assets are prioritized based on classification, criticality, resources, and impact on '
                             'the mission',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Define criteria for prioritizing each class of assets\n'
                                     'Ex2: Apply the prioritization criteria to assets\n'
                                     'Ex3: Track the asset priorities and update them periodically or when significant changes '
                                     'to the organization occur',
          'subchapter': 'ID.AM: Asset Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-AST-03.2: Does the organization govern the chronology of the origin, development, '
                                   'ownership, location and changes to a system, system components and associated data?.',
                                   'Q-AST-02.8: Does the organization create and maintain a map of technology assets where '
                                   'sensitive/regulated data is stored, transmitted or processed?.'],
          'objective_title': 'ID.AM-07:  Inventories of data and corresponding metadata for designated data types are '
                             'maintained',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Maintain a list of the designated data types of interest (e.g., personally '
                                     'identifiable information, protected health information, financial account numbers, '
                                     'organization intellectual property, operational technology data)\n'
                                     'Ex2: Continuously discover and analyze ad hoc data to identify new instances of '
                                     'designated data types\n'
                                     'Ex3: Assign data classifications to designated data types through tags or labels\n'
                                     'Ex4: Track the provenance, data owner, and geolocation of each instance of designated '
                                     'data types',
          'subchapter': 'ID.AM: Asset Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-DCH-08: Does the organization securely dispose of media when it is no longer required, '
                                   'using formal procedures? .',
                                   'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity '
                                   'commensurate with the classification or sensitivity of the information prior to disposal, '
                                   'release out of organizational control or release for reuse?.',
                                   'Q-MNT-05: Does the organization authorize, monitor and control remote, non-local '
                                   'maintenance and diagnostic activities?.',
                                   'Q-MNT-02: Does the organization conduct controlled maintenance activities throughout the '
                                   'lifecycle of the system, application or service?.',
                                   'Q-PRM-07: Does the organization ensure changes to systems within the Secure Development '
                                   'Life Cycle (SDLC) are controlled through formal change control procedures? .',
                                   'Q-AST-11: Does the organization authorize, control and track technology assets entering '
                                   'and exiting organizational facilities? .'],
          'objective_title': 'ID.AM-08:  Systems, hardware, software, services, and data are managed throughout their life '
                             'cycles',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Integrate cybersecurity considerations throughout the life cycles of systems, '
                                     'hardware, software, and services\n'
                                     'Ex2: Integrate cybersecurity considerations into product life cycles\n'
                                     'Ex3: Identify unofficial uses of technology to meet mission objectives (i.e., shadow '
                                     'IT)\n'
                                     'Ex4: Periodically identify redundant systems, hardware, software, and services that '
                                     "unnecessarily increase the organization's attack surface\n"
                                     'Ex5: Properly configure and secure systems, hardware, software, and services prior to '
                                     'their deployment in production\n'
                                     'Ex6: Update inventories when systems, hardware, software, and services are moved or '
                                     'transferred within the organization\n'
                                     "Ex7: Securely destroy stored data based on the organization's data retention policy "
                                     'using the prescribed destruction method, and keep and manage a record of the '
                                     'destructions\n'
                                     'Ex8: Securely sanitize data storage when hardware is being retired, decommissioned, '
                                     'reassigned, or sent for repairs or replacement\n'
                                     'Ex9: Offer methods for destroying paper, storage media, and other physical forms of data '
                                     'storage',
          'subchapter': 'ID.AM: Asset Management '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-01: Does the organization facilitate the implementation and monitoring of '
                                   'vulnerability management controls?.'],
          'objective_title': 'ID.RA-01:  Vulnerabilities in assets are identified, validated, and recorded',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Use vulnerability management technologies to identify unpatched and misconfigured '
                                     'software\n'
                                     'Ex2: Assess network and system architectures for design and implementation weaknesses '
                                     'that affect cybersecurity\n'
                                     'Ex3: Review, analyze, or test organization-developed software to identify design, '
                                     'coding, and default configuration vulnerabilities\n'
                                     'Ex4: Assess facilities that house critical computing assets for physical vulnerabilities '
                                     'and resilience issues\n'
                                     'Ex5: Monitor sources of cyber threat intelligence for information on new vulnerabilities '
                                     'in products and services\n'
                                     'Ex6: Review processes and procedures for weaknesses that could be exploited to affect '
                                     'cybersecurity',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-THR-03: Does the organization maintain situational awareness of evolving threats?.'],
          'objective_title': 'ID.RA-02:  Cyber threat intelligence is received from information sharing forums and sources',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Configure cybersecurity tools and technologies with detection or response '
                                     'capabilities to securely ingest cyber threat intelligence feeds\n'
                                     'Ex2: Receive and review advisories from reputable third parties on current threat actors '
                                     'and their tactics, techniques, and procedures (TTPs)\n'
                                     'Ex3: Monitor sources of cyber threat intelligence for information on the types of '
                                     'vulnerabilities that emerging technologies may have',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-RSK-03: Does the organization identify and document risks, both internal and external? '
                                   '.'],
          'objective_title': 'ID.RA-03:  Internal and external threats to the organization are identified and recorded',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Use cyber threat intelligence to maintain awareness of the types of threat actors '
                                     'likely to target the organization and the TTPs they are likely to use\n'
                                     'Ex2: Perform threat hunting to look for signs of threat actors within the environment\n'
                                     'Ex3: Implement processes for identifying internal threat actors',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.'],
          'objective_title': 'ID.RA-04:  Potential impacts and likelihoods of threats exploiting vulnerabilities are '
                             'identified and recorded',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Business leaders and cybersecurity risk management practitioners work together to '
                                     'estimate the likelihood and impact of risk scenarios and record them in risk registers\n'
                                     'Ex2: Enumerate the potential business impacts of unauthorized access to the '
                                     "organization's communications, systems, and data processed in or by those systems\n"
                                     'Ex3: Account for the potential impacts of cascading failures for systems of systems',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?."],
          'objective_title': 'ID.RA-05:  Threats, vulnerabilities, likelihoods, and impacts are used to understand inherent '
                             'risk and inform risk response prioritization',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Develop threat models to better understand risks to the data and identify '
                                     'appropriate risk responses\n'
                                     'Ex2: Prioritize cybersecurity resource allocations and investments based on estimated '
                                     'likelihoods and impacts',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing '
                                   'basis and ensure assets are protected against known attacks? .',
                                   'Q-RSK-02.1: Does the organization prioritize the impact level for systems, applications '
                                   'and/or services to provide additional granularity on potential disruptions?.',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .'],
          'objective_title': 'ID.RA-06:  Risk responses are chosen, prioritized, planned, tracked, and communicated',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     "Ex1: Apply the vulnerability management plan's criteria for deciding whether to accept, "
                                     'transfer, mitigate, or avoid risk\n'
                                     "Ex2: Apply the vulnerability management plan's criteria for selecting compensating "
                                     'controls to mitigate risk\n'
                                     'Ex3: Track the progress of risk response implementation (e.g., plan of action and '
                                     'milestones [POA&M], risk register, risk detail report)\n'
                                     'Ex4: Use risk assessment findings to inform risk response decisions and actions\n'
                                     'Ex5: Communicate planned risk responses to affected stakeholders in priority order',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': 'ID.RA-07:  Changes and exceptions are managed, assessed for risk impact, recorded, and tracked',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Implement and follow procedures for the formal documentation, review, testing, and '
                                     'approval of proposed changes and requested exceptions\n'
                                     'Ex2: Document the possible risks of making or not making each proposed change, and '
                                     'provide guidance on rolling back changes\n'
                                     'Ex3: Document the risks related to each requested exception and the plan for responding '
                                     'to those risks\n'
                                     'Ex4: Periodically review risks that were accepted based upon planned future actions or '
                                     'milestones',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-THR-03: Does the organization maintain situational awareness of evolving threats?.'],
          'objective_title': 'ID.RA-08:  Processes for receiving, analyzing, and responding to vulnerability disclosures are '
                             'established',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Conduct vulnerability information sharing between the organization and its '
                                     'suppliers following the rules and protocols defined in contracts\n'
                                     'Ex2: Assign responsibilities and verify the execution of procedures for processing, '
                                     'analyzing the impact of, and responding to cybersecurity threat, vulnerability, or '
                                     'incident disclosures by suppliers, customers, partners, and government cybersecurity '
                                     'organizations',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .',
                                   'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of '
                                   'data being transmitted? .',
                                   'Q-TDA-14: Does the organization require system developers and integrators to perform '
                                   'configuration management during system design, development, implementation and '
                                   'operation?.'],
          'objective_title': 'ID.RA-09:  The authenticity and integrity of hardware and software are assessed prior to '
                             'acquisition and use',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Assess the authenticity and cybersecurity of critical technology products and '
                                     'services prior to acquisition and use\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .',
                                   'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .',
                                   'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.'],
          'objective_title': 'ID.RA-10:  Critical suppliers are assessed prior to acquisition',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Conduct supplier risk assessments against business and applicable cybersecurity '
                                     'requirements, including the supply chain',
          'subchapter': 'ID.RA: Risk Assessment '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-VPM-05: Does the organization conduct software patching for all deployed operating '
                                   'systems, applications and firmware?.',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-CPL-02.1: Does the organization implement an internal audit function that is capable of '
                                   'providing senior organization management with insights into the appropriateness of the '
                                   "organization's technology and information governance processes?.",
                                   'Q-CPL-04: Does the organization thoughtfully plan audits by including input from '
                                   'operational risk and compliance partners to minimize the impact of audit-related '
                                   'activities on business operations?.'],
          'objective_title': 'ID.IM-01:  Improvements are identified from evaluations',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Perform self-assessments of critical services that take current threats and TTPs '
                                     'into consideration\n'
                                     'Ex2: Invest in third-party assessments or independent audits of the effectiveness of the '
                                     "organization's cybersecurity program to identify areas that need improvement\n"
                                     'Ex3: Constantly evaluate compliance with selected cybersecurity requirements through '
                                     'automated means',
          'subchapter': 'ID.IM: Improvement '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-IRO-05.1: Does the organization incorporate simulated events into incident response '
                                   'training to facilitate effective response by personnel in crisis situations?.',
                                   "Q-VPM-10: Does the organization utilize 'red team' exercises to simulate attempts by "
                                   'adversaries to compromise systems and applications in accordance with organization-defined '
                                   'rules of engagement? .',
                                   'Q-BCD-03: Does the organization adequately train contingency personnel and applicable '
                                   'stakeholders in their contingency roles and responsibilities?.',
                                   'Q-BCD-11.5: Does the organization utilize sampling of available backups to test recovery '
                                   'capabilities as part of business continuity plan testing?.',
                                   'Q-IRO-06: Does the organization formally test incident response capabilities through '
                                   'realistic exercises to determine the operational effectiveness of those capabilities?.',
                                   'Q-IRO-06.1: Does the organization coordinate incident response testing with organizational '
                                   'elements responsible for related plans? .',
                                   'Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .'],
          'objective_title': 'ID.IM-02:  Improvements are identified from security tests and exercises, including those done '
                             'in coordination with suppliers and relevant third parties',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Identify improvements for future incident response activities based on findings '
                                     'from incident response assessments (e.g., tabletop exercises and simulations, tests, '
                                     'internal reviews, independent audits)\n'
                                     'Ex2: Identify improvements for future business continuity, disaster recovery, and '
                                     'incident response activities based on exercises performed in coordination with critical '
                                     'service providers and product suppliers\n'
                                     'Ex3: Involve internal stakeholders (e.g., senior executives, legal department, HR) in '
                                     'security tests and exercises as appropriate\n'
                                     'Ex4: Perform penetration testing to identify opportunities to improve the security '
                                     'posture of selected high-risk systems as approved by leadership\n'
                                     'Ex5: Exercise contingency plans for responding to and recovering from the discovery that '
                                     'products or services did not originate with the contracted supplier or partner or were '
                                     'altered before receipt\n'
                                     'Ex6: Collect and analyze performance metrics using security tools and services to inform '
                                     'improvements to the cybersecurity program',
          'subchapter': 'ID.IM: Improvement '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-BCD-06: Does the organization keep contingency plans current with business needs, '
                                   'technology changes and feedback from contingency plan testing activities?.',
                                   "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' "
                                   'activity every time the contingency plan is activated?.',
                                   'Q-IRO-04.2: Does the organization regularly review and modify incident response practices '
                                   'to incorporate lessons learned, business process changes and industry developments, as '
                                   'necessary?.',
                                   'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?."],
          'objective_title': 'ID.IM-03:  Improvements are identified from execution of operational processes, procedures, and '
                             'activities',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Conduct collaborative lessons learned sessions with suppliers\n'
                                     'Ex2: Annually review cybersecurity policies, processes, and procedures to take lessons '
                                     'learned into account\n'
                                     'Ex3: Use metrics to assess operational cybersecurity performance over time',
          'subchapter': 'ID.IM: Improvement '},
         {'chapter_title': 'ID: IDENTIFY ',
          'conformity_questions': ['Q-BCD-03: Does the organization adequately train contingency personnel and applicable '
                                   'stakeholders in their contingency roles and responsibilities?.',
                                   'Q-BCD-11.5: Does the organization utilize sampling of available backups to test recovery '
                                   'capabilities as part of business continuity plan testing?.',
                                   'Q-IRO-06: Does the organization formally test incident response capabilities through '
                                   'realistic exercises to determine the operational effectiveness of those capabilities?.',
                                   'Q-IRO-06.1: Does the organization coordinate incident response testing with organizational '
                                   'elements responsible for related plans? .',
                                   "Q-BCD-05: Does the organization conduct a Root Cause Analysis (RCA) and 'lessons learned' "
                                   'activity every time the contingency plan is activated?.',
                                   'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .',
                                   'Q-BCD-01: Does the organization facilitate the implementation of contingency planning '
                                   'controls?.',
                                   'Q-IRO-01: Does the organization facilitate the implementation of incident response '
                                   'controls?.',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.'],
          'objective_title': 'ID.IM-04:  Incident response plans and other cybersecurity plans that affect operations are '
                             'established, communicated, maintained, and improved',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Establish contingency plans (e.g., incident response, business continuity, disaster '
                                     'recovery) for responding to and recovering from adverse events that can interfere with '
                                     "operations, expose confidential information, or otherwise endanger the organization's "
                                     'mission and viability\n'
                                     'Ex2: Include contact and communication information, processes for handling common '
                                     'scenarios, and criteria for prioritization, escalation, and elevation in all contingency '
                                     'plans\n'
                                     'Ex3: Create a vulnerability management plan to identify and assess all types of '
                                     'vulnerabilities and to prioritize, test, and implement risk responses\n'
                                     'Ex4: Communicate cybersecurity plans (including updates) to those responsible for '
                                     'carrying them out and to affected parties\n'
                                     'Ex5: Review and update all cybersecurity plans annually or when a need for significant '
                                     'improvements is identified',
          'subchapter': 'ID.IM: Improvement '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.',
                                   'Q-IAC-15: Does the organization proactively govern account management of individual, '
                                   'group, system, application, guest and temporary accounts?.'],
          'objective_title': 'PR.AA-01:  Identities and credentials for authorized users, services, and hardware are managed '
                             'by the organization',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Initiate requests for new access or additional access for employees, contractors, '
                                     'and others, and track, review, and fulfill the requests, with permission from system or '
                                     'data owners when needed\n'
                                     'Ex2: Issue, manage, and revoke cryptographic certificates and identity tokens, '
                                     'cryptographic keys (i.e., key management), and other credentials\n'
                                     'Ex3: Select a unique identifier for each device from immutable hardware characteristics '
                                     'or an identifier securely provisioned to the device\n'
                                     'Ex4: Physically label authorized hardware with an identifier for inventory and servicing '
                                     'purposes',
          'subchapter': 'PR.AA: Identity Management, Authentication, and Access Control '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-07: Does the organization utilize a formal user registration and de-registration '
                                   'process that governs the assignment of access rights? .'],
          'objective_title': 'PR.AA-02:  Identities are proofed and bound to credentials based on the context of interactions',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     "Ex1: Verify a person's claimed identity at enrollment time using government-issued "
                                     "identity credentials (e.g., passport, visa, driver's license)\n"
                                     'Ex2: Issue a different credential for each person (i.e., no credential sharing)',
          'subchapter': 'PR.AA: Identity Management, Authentication, and Access Control '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-IAC-04: Does the organization uniquely and centrally Authenticate, Authorize and Audit '
                                   '(AAA) devices before establishing a connection using bidirectional authentication that is '
                                   'cryptographically- based and replay resistant?.',
                                   'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote '
                                   'network access? .',
                                   'Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.'],
          'objective_title': 'PR.AA-03:  Users, services, and hardware are authenticated',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Require multifactor authentication\n'
                                     'Ex2: Enforce policies for the minimum strength of passwords, PINs, and similar '
                                     'authenticators\n'
                                     'Ex3: Periodically reauthenticate users, services, and hardware based on risk (e.g., in '
                                     'zero trust architectures)\n'
                                     'Ex4: Ensure that authorized personnel can access accounts essential for protecting '
                                     'safety under emergency conditions',
          'subchapter': 'PR.AA: Identity Management, Authentication, and Access Control '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of '
                                   'data being transmitted? .',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .',
                                   'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.',
                                   'Q-CRY-01.3: Does the organization ensure the confidentiality and integrity of information '
                                   'during preparation for transmission and during reception with cryptographic mechanisms?.'],
          'objective_title': 'PR.AA-04:  Identity assertions are protected, conveyed, and verified',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Protect identity assertions that are used to convey authentication and user '
                                     'information through single sign-on systems\n'
                                     'Ex2: Protect identity assertions that are used to convey authentication and user '
                                     'information between federated systems\n'
                                     'Ex3: Implement standards-based approaches for identity assertions in all contexts, and '
                                     'follow all guidance for the generation (e.g., data models, metadata), protection (e.g., '
                                     'digital signing, encryption), and verification (e.g., signature validation) of identity '
                                     'assertions',
          'subchapter': 'PR.AA: Identity Management, Authentication, and Access Control '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.',
                                   'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.',
                                   'Q-IAC-15: Does the organization proactively govern account management of individual, '
                                   'group, system, application, guest and temporary accounts?.'],
          'objective_title': 'PR.AA-05:  Access permissions, entitlements, and authorizations are defined in a policy, '
                             'managed, enforced, and reviewed, and incorporate the principles of least privilege and '
                             'separation of duties',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Review logical and physical access privileges periodically and whenever someone '
                                     'changes roles or leaves the organization, and promptly rescind privileges that are no '
                                     'longer needed\n'
                                     'Ex2: Take attributes of the requester and the requested resource into account for '
                                     "authorization decisions (e.g., geolocation, day/time, requester endpoint's cyber "
                                     'health)\n'
                                     'Ex3: Restrict access and privileges to the minimum necessary (e.g., zero trust '
                                     'architecture)\n'
                                     'Ex4: Periodically review the privileges associated with critical business functions to '
                                     'confirm proper separation of duties',
          'subchapter': 'PR.AA: Identity Management, Authentication, and Access Control '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-NET-01: Does the organization develop, govern & update procedures to facilitate the '
                                   'implementation of network security controls?.',
                                   'Q-NET-14.5: Does the organization define secure telecommuting practices and govern remote '
                                   'access to systems and data for remote workers? .',
                                   'Q-PES-03: Does the organization enforce physical access authorizations for all physical '
                                   'access points (including designated entry/exit points) to facilities (excluding those '
                                   'areas within the facility officially designated as publicly accessible)?.',
                                   'Q-PES-03.4: Does the organization enforce physical access to critical information systems '
                                   'or sensitive/regulated data, in addition to the physical access controls for the '
                                   'facility?.'],
          'objective_title': 'PR.AA-06:  Physical access to assets is managed, monitored, and enforced commensurate with risk',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Use security guards, security cameras, locked entrances, alarm systems, and other '
                                     'physical controls to monitor facilities and restrict access\n'
                                     'Ex2: Employ additional physical security controls for areas that contain high-risk '
                                     'assets\n'
                                     'Ex3: Escort guests, vendors, and other third parties within areas that contain '
                                     'business-critical assets',
          'subchapter': 'PR.AA: Identity Management, Authentication, and Access Control '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-SAT-04: Does the organization document, retain and monitor individual training '
                                   'activities, including basic security awareness training, ongoing awareness training and '
                                   'specific-system training?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .',
                                   'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   'Q-TPM-06: Does the organization control personnel security requirements including security '
                                   'roles and responsibilities for third-party providers?.',
                                   'Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .'],
          'objective_title': 'PR.AT-01:  Personnel are provided with awareness and training so that they possess the knowledge '
                             'and skills to perform general tasks with cybersecurity risks in mind',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Provide basic cybersecurity awareness and training to employees, contractors, '
                                     "partners, suppliers, and all other users of the organization's non-public resources\n"
                                     'Ex2: Train personnel to recognize social engineering attempts and other common attacks, '
                                     'report attacks and suspicious activity, comply with acceptable use policies, and perform '
                                     'basic cyber hygiene tasks (e.g., patching software, choosing passwords, protecting '
                                     'credentials)\n'
                                     'Ex3: Explain the consequences of cybersecurity policy violations, both to individual '
                                     'users and the organization as a whole\n'
                                     'Ex4: Periodically assess or test users on their understanding of basic cybersecurity '
                                     'practices\n'
                                     'Ex5: Require annual refreshers to reinforce existing practices and introduce new '
                                     'practices',
          'subchapter': 'PR.AT: Awareness and Training '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .',
                                   'Q-TPM-06: Does the organization control personnel security requirements including security '
                                   'roles and responsibilities for third-party providers?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-03.5: Does the organization provides specific training for privileged users to '
                                   'ensure privileged users understand their unique roles and responsibilities .'],
          'objective_title': 'PR.AT-02:  Individuals in specialized roles are provided with awareness and training so that '
                             'they possess the knowledge and skills to perform relevant tasks with cybersecurity risks in mind',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Identify the specialized roles within the organization that require additional '
                                     'cybersecurity training, such as physical and cybersecurity personnel, finance personnel, '
                                     'senior leadership, and anyone with access to business-critical data\n'
                                     'Ex2: Provide role-based cybersecurity awareness and training to all those in specialized '
                                     'roles, including contractors, partners, suppliers, and other third parties\n'
                                     'Ex3: Periodically assess or test users on their understanding of cybersecurity practices '
                                     'for their specialized roles\n'
                                     'Ex4: Require annual refreshers to reinforce existing practices and introduce new '
                                     'practices',
          'subchapter': 'PR.AT: Awareness and Training '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-DCH-12: Does the organization restrict removable media in accordance with data handling '
                                   'and acceptable usage parameters?.',
                                   'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect '
                                   'and report unauthorized changes to system files and configurations?.',
                                   'Q-END-06.1: Does the organization validate configurations through integrity checking of '
                                   'software and firmware?.',
                                   'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.',
                                   'Q-PES-13: Does the organization protect the system from information leakage due to '
                                   'electromagnetic signals emanations? .',
                                   'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .'],
          'objective_title': 'PR.DS-01:  The confidentiality, integrity, and availability of data-at-rest are protected',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Use encryption, digital signatures, and cryptographic hashes to protect the '
                                     'confidentiality and integrity of stored data in files, databases, virtual machine disk '
                                     'images, container images, and other resources\n'
                                     'Ex2: Use full disk encryption to protect data stored on user endpoints\n'
                                     'Ex3: Confirm the integrity of software by validating signatures\n'
                                     'Ex4: Restrict the use of removable media to prevent data exfiltration\n'
                                     'Ex5: Physically secure removable media containing unencrypted sensitive information, '
                                     'such as within locked offices or file cabinets',
          'subchapter': 'PR.DS: Data Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.',
                                   'Q-PES-13: Does the organization protect the system from information leakage due to '
                                   'electromagnetic signals emanations? .',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .'],
          'objective_title': 'PR.DS-02:  The confidentiality, integrity, and availability of data-in-transit are protected',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Use encryption, digital signatures, and cryptographic hashes to protect the '
                                     'confidentiality and integrity of network communications\n'
                                     'Ex2: Automatically encrypt or block outbound emails and other communications that '
                                     'contain sensitive data, depending on the data classification\n'
                                     'Ex3: Block access to personal email, file sharing, file storage services, and other '
                                     'personal communications applications and services from organizational systems and '
                                     'networks\n'
                                     'Ex4: Prevent reuse of sensitive data from production environments (e.g., customer '
                                     'records) in development, testing, and other non-production environments',
          'subchapter': 'PR.DS: Data Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.',
                                   'Q-PES-13: Does the organization protect the system from information leakage due to '
                                   'electromagnetic signals emanations? .'],
          'objective_title': 'PR.DS-10:  The confidentiality, integrity, and availability of data-in-use are protected',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Remove data that must remain confidential (e.g., from processors and memory) as '
                                     'soon as it is no longer needed\n'
                                     'Ex2: Protect data in use from access by other users and processes of the same platform',
          'subchapter': 'PR.DS: Data Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.',
                                   'Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of '
                                   'the backup process, as well as the integrity and availability of the data? .',
                                   'Q-BCD-12: Does the organization ensure the secure recovery and reconstitution of systems '
                                   'to a known state after a disruption, compromise or failure? .'],
          'objective_title': 'PR.DS-11:  Backups of data are created, protected, maintained, and tested',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Continuously back up critical data in near-real-time, and back up other data '
                                     'frequently at agreed-upon schedules\n'
                                     'Ex2: Test backups and restores for all types of data sources at least annually\n'
                                     'Ex3: Securely store some backups offline and offsite so that an incident or disaster '
                                     'will not damage them\n'
                                     'Ex4: Enforce geographic separation and geolocation restrictions for data backup storage',
          'subchapter': 'PR.DS: Data Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-CFG-03: Does the organization configure systems to provide only essential capabilities '
                                   'by specifically prohibiting or restricting the use of ports, protocols, and/or services? .',
                                   'Q-DCH-12: Does the organization restrict removable media in accordance with data handling '
                                   'and acceptable usage parameters?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .',
                                   'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.'],
          'objective_title': 'PR.PS-01:  Configuration management practices are established and applied',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Establish, test, deploy, and maintain hardened baselines that enforce the '
                                     "organization's cybersecurity policies and provide only essential capabilities (i.e., "
                                     'principle of least functionality)\n'
                                     'Ex2: Review all default configuration settings that may potentially impact cybersecurity '
                                     'when installing or upgrading software\n'
                                     'Ex3: Monitor implemented software for deviations from approved baselines',
          'subchapter': 'PR.PS: Platform Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-MNT-05: Does the organization authorize, monitor and control remote, non-local '
                                   'maintenance and diagnostic activities?.',
                                   'Q-VPM-01: Does the organization facilitate the implementation and monitoring of '
                                   'vulnerability management controls?.'],
          'objective_title': 'PR.PS-02:  Software is maintained, replaced, and removed commensurate with risk',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Perform routine and emergency patching within the timeframes specified in the '
                                     'vulnerability management plan\n'
                                     'Ex2: Update container images, and deploy new container instances to replace rather than '
                                     'update existing instances\n'
                                     'Ex3: Replace end-of-life software and service versions with supported, maintained '
                                     'versions\n'
                                     'Ex4: Uninstall and remove unauthorized software and services that pose undue risks\n'
                                     'Ex5: Uninstall and remove any unnecessary software components (e.g., operating system '
                                     'utilities) that attackers might misuse\n'
                                     'Ex6: Define and implement plans for software and service end-of-life maintenance support '
                                     'and obsolescence',
          'subchapter': 'PR.PS: Platform Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-AST-11: Does the organization authorize, control and track technology assets entering '
                                   'and exiting organizational facilities? .',
                                   'Q-MNT-02: Does the organization conduct controlled maintenance activities throughout the '
                                   'lifecycle of the system, application or service?.'],
          'objective_title': 'PR.PS-03:  Hardware is maintained, replaced, and removed commensurate with risk',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Replace hardware when it lacks needed security capabilities or when it cannot '
                                     'support software with needed security capabilities\n'
                                     'Ex2: Define and implement plans for hardware end-of-life maintenance support and '
                                     'obsolescence\n'
                                     'Ex3: Perform hardware disposal in a secure, responsible, and auditable manner',
          'subchapter': 'PR.PS: Platform Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.',
                                   'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.'],
          'objective_title': 'PR.PS-04:  Log records are generated and made available for continuous monitoring',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Configure all operating systems, applications, and services (including cloud-based '
                                     'services) to generate log records\n'
                                     "Ex2: Configure log generators to securely share their logs with the organization's "
                                     'logging infrastructure systems and services\n'
                                     'Ex3: Configure log generators to record the data needed by zero-trust architectures',
          'subchapter': 'PR.PS: Platform Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-END-03.1: Does the organization alert personnel when an unauthorized installation of '
                                   'software is detected? .',
                                   'Q-END-03: Does the organization prohibit user installation of software without explicitly '
                                   'assigned privileged status? .',
                                   'Q-CFG-05.1: Does the organization configure systems to generate an alert when the '
                                   'unauthorized installation of software is detected? .',
                                   'Q-CFG-04: Does the organization enforce software usage restrictions to comply with '
                                   'applicable contract agreements and copyright laws?.',
                                   'Q-CHG-04.2: Does the organization prevent the installation of software and firmware '
                                   'components without verification that the component has been digitally signed using an '
                                   'organization-approved certificate authority? .'],
          'objective_title': 'PR.PS-05:  Installation and execution of unauthorized software are prevented',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: When risk warrants it, restrict software execution to permitted products only or '
                                     'deny the execution of prohibited and unauthorized software\n'
                                     "Ex2: Verify the source of new software and the software's integrity before installing "
                                     'it\n'
                                     'Ex3: Configure platforms to use only approved DNS services that block access to known '
                                     'malicious domains\n'
                                     'Ex4: Configure platforms to allow the installation of organization-approved software '
                                     'only',
          'subchapter': 'PR.PS: Platform Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-TDA-09: Does the organization require system developers/integrators consult with '
                                   'cybersecurity and privacy personnel to:   -  Create and implement a Security Test and '
                                   'Evaluation (ST&E) plan;  -  Implement a verifiable flaw remediation process to correct '
                                   'weaknesses and deficiencies identified during the security testing and evaluation process; '
                                   'and  -  Document the results of the security testing/evaluation and flaw remediation '
                                   'processes?.',
                                   'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
                                   'Q-TDA-05: Does the organization require the developers of systems, system components or '
                                   'services to produce a design specification and security architecture that:   -  Is '
                                   "consistent with and supportive of the organization's security architecture which is "
                                   "established within and is an integrated part of the organization's enterprise "
                                   'architecture;  -  Accurately and completely describes the required security functionality '
                                   'and the allocation of security controls among physical and logical components; and  -  '
                                   'Expresses how individual security functions, mechanisms and services work together to '
                                   'provide required security capabilities and a unified approach to protection?.',
                                   'Q-PRM-07: Does the organization ensure changes to systems within the Secure Development '
                                   'Life Cycle (SDLC) are controlled through formal change control procedures? .'],
          'objective_title': 'PR.PS-06:  Secure software development practices are integrated, and their performance is '
                             'monitored throughout the software development life cycle',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Protect all components of organization-developed software from tampering and '
                                     'unauthorized access\n'
                                     'Ex2: Secure all software produced by the organization, with minimal vulnerabilities in '
                                     'their releases\n'
                                     'Ex3: Maintain the software used in production environments, and securely dispose of '
                                     'software once it is no longer needed',
          'subchapter': 'PR.PS: Platform Security '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-NET-01: Does the organization develop, govern & update procedures to facilitate the '
                                   'implementation of network security controls?.',
                                   'Q-TDA-08: Does the organization manage separate development, testing and operational '
                                   'environments to reduce the risks of unauthorized access or changes to the operational '
                                   'environment and to ensure no impact to production systems?.',
                                   'Q-NET-02: Does the organization implement security functions as a layered structure that '
                                   'minimizes interactions between layers of the design and avoiding any dependence by lower '
                                   'layers on the functionality or correctness of higher layers? .',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.'],
          'objective_title': 'PR.IR-01:  Networks and environments are protected from unauthorized logical access and usage',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Logically segment organization networks and cloud-based platforms according to '
                                     'trust boundaries and platform types (e.g., IT, IoT, OT, mobile, guests), and permit '
                                     'required communications only between segments\n'
                                     'Ex2: Logically segment organization networks from external networks, and permit only '
                                     "necessary communications to enter the organization's networks from the external "
                                     'networks\n'
                                     'Ex3: Implement zero trust architectures to restrict network access to each resource to '
                                     'the minimum necessary\n'
                                     'Ex4: Check the cyber health of endpoints before allowing them to access and use '
                                     'production resources',
          'subchapter': 'PR.IR: Technology Infrastructure Resilience '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, '
                                   'regulatory and contractual controls?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?."],
          'objective_title': "PR.IR-02:  The organization's technology assets are protected from environmental threats",
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Protect organizational equipment from known environmental threats, such as '
                                     'flooding, fire, wind, and excessive heat and humidity\n'
                                     'Ex2: Include protection from environmental threats and provisions for adequate operating '
                                     'infrastructure in requirements for service providers that operate systems on the '
                                     "organization's behalf",
          'subchapter': 'PR.IR: Technology Infrastructure Resilience '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-BCD-09: Does the organization establish an alternate processing site that provides '
                                   'security measures equivalent to that of the primary site?.',
                                   'Q-BCD-08: Does the organization establish an alternate storage site that includes both the '
                                   'assets and necessary agreements to permit the storage and recovery of system backup '
                                   'information? .',
                                   'Q-BCD-12.2: Does the organization implement real-time or near-real-time failover '
                                   'capability to maintain availability of critical systems, applications and/or services?.',
                                   'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.',
                                   'Q-SEA-07.2: Does the organization enable systems to fail to an organization-defined '
                                   'known-state for types of failures, preserving system state information in failure? .'],
          'objective_title': 'PR.IR-03:  Mechanisms are implemented to achieve resilience requirements in normal and adverse '
                             'situations',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Avoid single points of failure in systems and infrastructure\n'
                                     'Ex2: Use load balancing to increase capacity and improve reliability\n'
                                     'Ex3: Use high-availability components like redundant storage and power supplies to '
                                     'improve system reliability',
          'subchapter': 'PR.IR: Technology Infrastructure Resilience '},
         {'chapter_title': 'PR: PROTECT ',
          'conformity_questions': ['Q-CAP-01: Does the organization facilitate the implementation of capacity management '
                                   'controls to ensure optimal system performance to meet expected and anticipated future '
                                   'capacity requirements?.',
                                   'Q-CAP-03: Does the organization conducted capacity planning so that necessary capacity for '
                                   'information processing, telecommunications and environmental support will exist during '
                                   'contingency operations? .'],
          'objective_title': 'PR.IR-04:  Adequate resource capacity to ensure availability is maintained',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Monitor usage of storage, power, compute, network bandwidth, and other resources\n'
                                     'Ex2: Forecast future needs, and scale resources accordingly',
          'subchapter': 'PR.IR: Technology Infrastructure Resilience '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-MON-16.3: Does the organization monitor for unauthorized activities, accounts, '
                                   'connections, devices and software?.',
                                   'Q-END-10: Does the organization address mobile code / operating system-independent '
                                   'applications? .',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.'],
          'objective_title': 'DE.CM-01:  Networks and network services are monitored to find potentially adverse events',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Monitor DNS, BGP, and other network services for adverse events\n'
                                     'Ex2: Monitor wired and wireless networks for connections from unauthorized endpoints\n'
                                     'Ex3: Monitor facilities for unauthorized or rogue wireless networks\n'
                                     'Ex4: Compare actual network flows against baselines to detect deviations\n'
                                     'Ex5: Monitor network communications to identify changes in security postures for zero '
                                     'trust purposes\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.CM: Continuous Monitoring '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-PES-05: Does the organization monitor for, detect and respond to physical security '
                                   'incidents?.'],
          'objective_title': 'DE.CM-02:  The physical environment is monitored to find potentially adverse events',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Monitor logs from physical access control systems (e.g., badge readers) to find '
                                     'unusual access patterns (e.g., deviations from the norm) and failed access attempts\n'
                                     'Ex2: Review and monitor physical access records (e.g., from visitor registration, '
                                     'sign-in sheets)\n'
                                     'Ex3: Monitor physical access controls (e.g., locks, latches, hinge pins, alarms) for '
                                     'signs of tampering\n'
                                     'Ex4: Monitor the physical environment using alarm systems, cameras, and security guards\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.CM: Continuous Monitoring '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-MON-16.3: Does the organization monitor for unauthorized activities, accounts, '
                                   'connections, devices and software?.',
                                   'Q-MON-16.1: Does the organization monitor internal personnel activity for potential '
                                   'security incidents?.'],
          'objective_title': 'DE.CM-03:  Personnel activity and technology usage are monitored to find potentially adverse '
                             'events',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Use behavior analytics software to detect anomalous user activity to mitigate '
                                     'insider threats\n'
                                     'Ex2: Monitor logs from logical access control systems to find unusual access patterns '
                                     'and failed access attempts\n'
                                     'Ex3: Continuously monitor deception technology, including user accounts, for any usage\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.CM: Continuous Monitoring '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-MON-16.3: Does the organization monitor for unauthorized activities, accounts, '
                                   'connections, devices and software?.',
                                   'Q-MON-16.2: Does the organization monitor third-party personnel activity for potential '
                                   'security incidents?.'],
          'objective_title': 'DE.CM-06:  External service provider activities and services are monitored to find potentially '
                             'adverse events',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Monitor remote and onsite administration and maintenance activities that external '
                                     'providers perform on organizational systems\n'
                                     'Ex2: Monitor activity from cloud-based services, internet service providers, and other '
                                     'service providers for deviations from expected behavior\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'DE.CM: Continuous Monitoring '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-MON-16.3: Does the organization monitor for unauthorized activities, accounts, '
                                   'connections, devices and software?.',
                                   'Q-END-10: Does the organization address mobile code / operating system-independent '
                                   'applications? .',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.',
                                   'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .',
                                   'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of '
                                   'data being transmitted? .',
                                   'Q-TDA-14: Does the organization require system developers and integrators to perform '
                                   'configuration management during system design, development, implementation and operation?.',
                                   'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect '
                                   'and report unauthorized changes to system files and configurations?.',
                                   'Q-END-06.1: Does the organization validate configurations through integrity checking of '
                                   'software and firmware?.'],
          'objective_title': 'DE.CM-09:  Computing hardware and software, runtime environments, and their data are monitored '
                             'to find potentially adverse events',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Monitor email, web, file sharing, collaboration services, and other common attack '
                                     'vectors to detect malware, phishing, data leaks and exfiltration, and other adverse '
                                     'events\n'
                                     'Ex2: Monitor authentication attempts to identify attacks against credentials and '
                                     'unauthorized credential reuse\n'
                                     'Ex3: Monitor software configurations for deviations from security baselines\n'
                                     'Ex4: Monitor hardware and software for signs of tampering\n'
                                     'Ex5: Use technologies with a presence on endpoints to detect cyber health issues (e.g., '
                                     'missing patches, malware infections, unauthorized software), and redirect the endpoints '
                                     'to a remediation environment before access is authorized\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.CM: Continuous Monitoring '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'DE.AE-02:  Potentially adverse events are analyzed to better understand associated activities',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Use security information and event management (SIEM) or other tools to continuously '
                                     'monitor log events for known malicious and suspicious activity\n'
                                     'Ex2: Utilize up-to-date cyber threat intelligence in log analysis tools to improve '
                                     'detection accuracy and characterize threat actors, their methods, and indicators of '
                                     'compromise\n'
                                     'Ex3: Regularly conduct manual reviews of log events for technologies that cannot be '
                                     'sufficiently monitored through automation\n'
                                     'Ex4: Use log analysis tools to generate reports on their findings\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.AE: Adverse Event Analysis '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.',
                                   'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .'],
          'objective_title': 'DE.AE-03:  Information is correlated from multiple sources',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Constantly transfer log data generated by other sources to a relatively small '
                                     'number of log servers\n'
                                     'Ex2: Use event correlation technology (e.g., SIEM) to collect information captured by '
                                     'multiple sources\n'
                                     'Ex3: Utilize cyber threat intelligence to help correlate events among log sources\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.AE: Adverse Event Analysis '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'DE.AE-04:  The estimated impact and scope of adverse events are understood',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Use SIEMs or other tools to estimate impact and scope, and review and refine the '
                                     'estimates\n'
                                     'Ex2: A person creates their own estimates of impact and scope\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.AE: Adverse Event Analysis '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-MON-06: Does the organization provide an event log report generation capability to aid '
                                   'in detecting and assessing anomalous activities? .'],
          'objective_title': 'DE.AE-06:  Information on adverse events is provided to authorized staff and tools',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Use cybersecurity software to generate alerts and provide them to the security '
                                     'operations center (SOC), incident responders, and incident response tools\n'
                                     'Ex2: Incident responders and other authorized personnel can access log analysis findings '
                                     'at all times\n'
                                     "Ex3: Automatically create and assign tickets in the organization's ticketing system when "
                                     'certain types of alerts occur\n'
                                     "Ex4: Manually create and assign tickets in the organization's ticketing system when "
                                     'technical staff discover indicators of compromise\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.AE: Adverse Event Analysis '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ['Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.',
                                   'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .'],
          'objective_title': 'DE.AE-07:  Cyber threat intelligence and other contextual information are integrated into the '
                             'analysis',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Securely provide cyber threat intelligence feeds to detection technologies, '
                                     'processes, and personnel\n'
                                     'Ex2: Securely provide information from asset inventories to detection technologies, '
                                     'processes, and personnel\n'
                                     "Ex3: Rapidly acquire and analyze vulnerability disclosures for the organization's "
                                     'technologies from suppliers, vendors, and third-party security advisories\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.AE: Adverse Event Analysis '},
         {'chapter_title': 'DE: DETECT ',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'DE.AE-08:  Incidents are declared when adverse events meet the defined incident criteria',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Apply incident criteria to known and assumed characteristics of activity in order '
                                     'to determine whether an incident should be declared\n'
                                     'Ex2: Take known false positives into account when applying incident criteria\n'
                                     '1st: 1st Party Risk',
          'subchapter': 'DE.AE: Adverse Event Analysis '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.'],
          'objective_title': 'RS.MA-01:  The incident response plan is executed in coordination with relevant third parties '
                             'once an incident is declared',
          'requirement_description': 'Implementation Examples: \n'
                                     'Ex1: Detection technologies automatically report confirmed incidents\n'
                                     "Ex2: Request incident response assistance from the organization's incident response "
                                     'outsourcer\n'
                                     'Ex3: Designate an incident lead for each incident\n'
                                     'Ex4: Initiate execution of additional cybersecurity plans as needed to support incident '
                                     'response (for example, business continuity and disaster recovery)\n'
                                     '3rd: 3rd Party Risk',
          'subchapter': 'RS.MA: Incident Management '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-03: Does the organization define specific Indicators of Compromise (IOC) that '
                                   'identify the potential impact of likely cybersecurity events?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'RS.MA-02:  Incident reports are triaged and validated',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Preliminarily review incident reports to confirm that they are '
                                     'cybersecurity-related and necessitate incident response activities\n'
                                     'Ex2: Apply criteria to estimate the severity of an incident',
          'subchapter': 'RS.MA: Incident Management '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-03: Does the organization define specific Indicators of Compromise (IOC) that '
                                   'identify the potential impact of likely cybersecurity events?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'RS.MA-03:  Incidents are categorized and prioritized',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Further review and categorize incidents based on the type of incident (e.g., data '
                                     'breach, ransomware, DDoS, account compromise)\n'
                                     'Ex2: Prioritize incidents based on their scope, likely impact, and time-critical nature\n'
                                     'Ex3: Select incident response strategies for active incidents by balancing the need to '
                                     'quickly recover from an incident with the need to observe the attacker or conduct a more '
                                     'thorough investigation',
          'subchapter': 'RS.MA: Incident Management '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   'Q-IRO-03: Does the organization define specific Indicators of Compromise (IOC) that '
                                   'identify the potential impact of likely cybersecurity events?.'],
          'objective_title': 'RS.MA-04:  Incidents are escalated or elevated as needed',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Track and validate the status of all ongoing incidents\n'
                                     'Ex2: Coordinate incident escalation or elevation with designated internal and external '
                                     'stakeholders',
          'subchapter': 'RS.MA: Incident Management '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'RS.MA-05:  The criteria for initiating incident recovery are applied',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Apply incident recovery criteria to known and assumed characteristics of the '
                                     'incident to determine whether incident recovery processes should be initiated\n'
                                     'Ex2: Take the possible operational disruption of incident recovery activities into '
                                     'account',
          'subchapter': 'RS.MA: Incident Management '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-08: Does the organization perform digital forensics and maintain the integrity of '
                                   'the chain of custody? .'],
          'objective_title': 'RS.AN-03:  Analysis is performed to establish what has taken place during an incident and the '
                             'root cause of the incident',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Determine the sequence of events that occurred during the incident and which assets '
                                     'and resources were involved in each event\n'
                                     'Ex2: Attempt to determine what vulnerabilities, threats, and threat actors were directly '
                                     'or indirectly involved in the incident\n'
                                     'Ex3: Analyze the incident to find the underlying, systemic root causes\n'
                                     'Ex4: Check any cyber deception technology for additional information on attacker '
                                     'behavior',
          'subchapter': 'RS.AN: Incident Analysis '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-08: Does the organization perform digital forensics and maintain the integrity of '
                                   'the chain of custody? .'],
          'objective_title': "RS.AN-06:  Actions performed during an investigation are recorded, and the records' integrity "
                             'and provenance are preserved',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Require each incident responder and others (e.g., system administrators, '
                                     'cybersecurity engineers) who perform incident response tasks to record their actions and '
                                     'make the record immutable\n'
                                     'Ex2: Require the incident lead to document the incident in detail and be responsible for '
                                     'preserving the integrity of the documentation and the sources of all information being '
                                     'reported',
          'subchapter': 'RS.AN: Incident Analysis '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-08: Does the organization perform digital forensics and maintain the integrity of '
                                   'the chain of custody? .'],
          'objective_title': 'RS.AN-07:  Incident data and metadata are collected, and their integrity and provenance are '
                             'preserved',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Collect, preserve, and safeguard the integrity of all pertinent incident data and '
                                     'metadata (e.g., data source, date/time of collection) based on evidence preservation and '
                                     'chain-of-custody procedures',
          'subchapter': 'RS.AN: Incident Analysis '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-03: Does the organization define specific Indicators of Compromise (IOC) that '
                                   'identify the potential impact of likely cybersecurity events?.',
                                   'Q-IRO-02.6: Does the organization automatically disable systems involved in an incident '
                                   'that meet organizational criteria to be automatically disabled upon detection?.',
                                   'Q-IRO-02.3: Does the organization dynamically reconfigure information system components as '
                                   'part of the incident response capability? .'],
          'objective_title': "RS.AN-08:  An incident's magnitude is estimated and validated",
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Review other potential targets of the incident to search for indicators of '
                                     'compromise and evidence of persistence\n'
                                     'Ex2: Automatically run tools on targets to look for indicators of compromise and '
                                     'evidence of persistence',
          'subchapter': 'RS.AN: Incident Analysis '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.'],
          'objective_title': 'RS.CO-02:  Internal and external stakeholders are notified of incidents',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     "Ex1: Follow the organization's breach notification procedures after discovering a data "
                                     'breach incident, including notifying affected customers\n'
                                     'Ex2: Notify business partners and customers of incidents in accordance with contractual '
                                     'requirements\n'
                                     'Ex3: Notify law enforcement agencies and regulatory bodies of incidents based on '
                                     'criteria in the incident response plan and management approval',
          'subchapter': 'RS.CO: Incident Response Reporting and Communication '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ['Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.'],
          'objective_title': 'RS.CO-03:  Information is shared with designated internal and external stakeholders',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Securely share information consistent with response plans and information sharing '
                                     'agreements\n'
                                     "Ex2: Voluntarily share information about an attacker's observed TTPs, with all sensitive "
                                     'data removed, with an Information Sharing and Analysis Center (ISAC)\n'
                                     'Ex3: Notify HR when malicious insider activity occurs\n'
                                     'Ex4: Regularly update senior leadership on the status of major incidents\n'
                                     'Ex5: Follow the rules and protocols defined in contracts for incident information '
                                     'sharing between the organization and its suppliers\n'
                                     'Ex6: Coordinate crisis communication methods between the organization and its critical '
                                     'suppliers',
          'subchapter': 'RS.CO: Incident Response Reporting and Communication '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'RS.MI-01:  Incidents are contained',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Cybersecurity technologies (e.g., antivirus software) and cybersecurity features of '
                                     'other technologies (e.g., operating systems, network infrastructure devices) '
                                     'automatically perform containment actions\n'
                                     'Ex2: Allow incident responders to manually select and perform containment actions\n'
                                     'Ex3: Allow a third party (e.g., internet service provider, managed security service '
                                     'provider) to perform containment actions on behalf of the organization\n'
                                     'Ex4: Automatically transfer compromised endpoints to a remediation virtual local area '
                                     'network (VLAN)',
          'subchapter': 'RS.MI: Incident Mitigation '},
         {'chapter_title': 'RS: RESPOND ',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'RS.MI-02:  Incidents are eradicated',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Cybersecurity technologies and cybersecurity features of other technologies (e.g., '
                                     'operating systems, network infrastructure devices) automatically perform eradication '
                                     'actions\n'
                                     'Ex2: Allow incident responders to manually select and perform eradication actions\n'
                                     'Ex3: Allow a third party (e.g., managed security service provider) to perform '
                                     'eradication actions on behalf of the organization',
          'subchapter': 'RS.MI: Incident Mitigation '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ['Q-BCD-01: Does the organization facilitate the implementation of contingency planning '
                                   'controls?.'],
          'objective_title': 'RC.RP-01:  The recovery portion of the incident response plan is executed once initiated from '
                             'the incident response process',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Begin recovery procedures during or after incident response processes\n'
                                     'Ex2: Make all individuals with recovery responsibilities aware of the plans for recovery '
                                     'and the authorizations required to implement each aspect of the plans',
          'subchapter': 'RC.RP: Incident Recovery Plan Execution '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ['Q-BCD-01: Does the organization facilitate the implementation of contingency planning '
                                   'controls?.'],
          'objective_title': 'RC.RP-02:  Recovery actions are selected, scoped, prioritized, and performed',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Select recovery actions based on the criteria defined in the incident response plan '
                                     'and available resources\n'
                                     'Ex2: Change planned recovery actions based on a reassessment of organizational needs and '
                                     'resources',
          'subchapter': 'RC.RP: Incident Recovery Plan Execution '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ['Q-BCD-11.1: Does the organization routinely test backups that verifies the reliability of '
                                   'the backup process, as well as the integrity and availability of the data? .',
                                   'Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.'],
          'objective_title': 'RC.RP-03:  The integrity of backups and other restoration assets is verified before using them '
                             'for restoration',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Check restoration assets for indicators of compromise, file corruption, and other '
                                     'integrity issues before use',
          'subchapter': 'RC.RP: Incident Recovery Plan Execution '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ['Q-IRO-17-CM: Does the organization establish a post-incident procedure to verify the '
                                   'integrity of the affected systems before restoring them to normal operations?.'],
          'objective_title': 'RC.RP-04:  Critical mission functions and cybersecurity risk management are considered to '
                             'establish post-incident operational norms',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Use business impact and system categorization records (including service delivery '
                                     'objectives) to validate that essential services are restored in the appropriate order\n'
                                     'Ex2: Work with system owners to confirm the successful restoration of systems and the '
                                     'return to normal operations\n'
                                     'Ex3: Monitor the performance of restored systems to verify the adequacy of the '
                                     'restoration',
          'subchapter': 'RC.RP: Incident Recovery Plan Execution '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ['Q-IRO-17-CM: Does the organization establish a post-incident procedure to verify the '
                                   'integrity of the affected systems before restoring them to normal operations?.'],
          'objective_title': 'RC.RP-05:  The integrity of restored assets is verified, systems and services are restored, and '
                             'normal operating status is confirmed',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Check restored assets for indicators of compromise and remediation of root causes '
                                     'of the incident before production use\n'
                                     'Ex2: Verify the correctness and adequacy of the restoration actions taken before putting '
                                     'a restored system online',
          'subchapter': 'RC.RP: Incident Recovery Plan Execution '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ['Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .',
                                   'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .'],
          'objective_title': 'RC.RP-06:  The end of incident recovery is declared based on criteria, and incident-related '
                             'documentation is completed',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     'Ex1: Prepare an after-action report that documents the incident itself, the response and '
                                     'recovery actions taken, and lessons learned\n'
                                     'Ex2: Declare the end of incident recovery once the criteria are met',
          'subchapter': 'RC.RP: Incident Recovery Plan Execution '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.',
                                   'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   'Q-IRO-16: Does the organization proactively manage public relations associated with an '
                                   'incident and employ appropriate measures to repair the reputation of the organization?.'],
          'objective_title': 'RC.CO-03:  Recovery activities and progress in restoring operational capabilities are '
                             'communicated to designated internal and external stakeholders',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     '3rd: 3rd Party Risk\n'
                                     'Ex1: Securely share recovery information, including restoration progress, consistent '
                                     'with response plans and information sharing agreements\n'
                                     'Ex2: Regularly update senior leadership on recovery status and restoration progress for '
                                     'major incidents\n'
                                     'Ex3: Follow the rules and protocols defined in contracts for incident information '
                                     'sharing between the organization and its suppliers\n'
                                     'Ex4: Coordinate crisis communication between the organization and its critical suppliers',
          'subchapter': 'RC.CO: Incident Recovery Communication '},
         {'chapter_title': 'RC: RECOVER ',
          'conformity_questions': ['Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.',
                                   'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   'Q-IRO-16: Does the organization proactively manage public relations associated with an '
                                   'incident and employ appropriate measures to repair the reputation of the organization?.'],
          'objective_title': 'RC.CO-04:  Public updates on incident recovery are shared using approved methods and messaging',
          'requirement_description': 'Implementation Examples: \n'
                                     '1st: 1st Party Risk\n'
                                     "Ex1: Follow the organization's breach notification procedures for recovering from a data "
                                     'breach incident\n'
                                     'Ex2: Explain the steps being taken to recover from the incident and to prevent a '
                                     'recurrence',
          'subchapter': 'RC.CO: Incident Recovery Communication '}]
