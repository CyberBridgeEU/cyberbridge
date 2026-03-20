# app/seeds/ftc_safeguards_seed.py
import io
import logging
from .base_seed import BaseSeed
from app.models import models
from app.constants.ftc_safeguards_connections import FTC_SAFEGUARDS_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class FtcSafeguardsSeed(BaseSeed):
    """Seed FTC Safeguards framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating FTC Safeguards framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create FTC Safeguards Framework
        ftc_safeguards_framework, created = self.get_or_create(
            models.Framework,
            {"name": "FTC Safeguards", "organisation_id": default_org.id},
            {
                "name": "FTC Safeguards",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("FTC Safeguards framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == ftc_safeguards_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == ftc_safeguards_framework.id
            ).all()

            logger.info(f"Found existing FTC Safeguards framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            # Keep links in sync even when framework/objectives already exist.
            if not self.skip_wire_connections:
                self._wire_connections(ftc_safeguards_framework, default_org, existing_objectives)
            self.db.commit()

            return {
                "framework": ftc_safeguards_framework,
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
                description="FTC Safeguards conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=ftc_safeguards_framework.id,
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
                        "framework_id": ftc_safeguards_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": ftc_safeguards_framework.id
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
            self._wire_connections(ftc_safeguards_framework, default_org, objectives_list)

        self.db.commit()

        logger.info(f"Created FTC Safeguards framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": ftc_safeguards_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _wire_connections(self, framework, org, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to FTC Safeguards objectives using the FTC_SAFEGUARDS_CONNECTIONS mapping.
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
            logger.warning("Missing lookup defaults - skipping FTC Safeguards connection wiring")
            return

        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in FTC_SAFEGUARDS_CONNECTIONS.values():
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

        logger.info(f"FTC Safeguards wiring: {len(risk_name_to_id)} risks ready")

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

        logger.info(f"FTC Safeguards wiring: {len(control_code_to_id)} controls ready")

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
                        logger.warning(f"FTC Safeguards wiring: docx conversion failed for {policy_code}: {conv_err}")
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

        logger.info(f"FTC Safeguards wiring: {len(policy_code_to_id)} policies ready")

        obj_title_to_id = {obj.title: obj.id for obj in objectives_list}
        policy_framework_pairs = set()

        obj_risk_count = 0
        obj_ctrl_count = 0
        pol_obj_count = 0
        ctrl_risk_count = 0
        ctrl_pol_count = 0
        planned_control_risk_pairs = set()
        planned_control_policy_pairs = set()

        for obj_title, conn in FTC_SAFEGUARDS_CONNECTIONS.items():
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
            f"FTC Safeguards wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return ['Q-GOV-04: Does the organization assign a qualified individual with the mission and resources to centrally-manage '
         'coordinate, develop, implement and maintain an enterprise-wide cybersecurity and privacy program? .',
         'Q-GOV-01.2: Does the organization provide governance oversight reporting and recommendations to those entrusted to '
         "make executive decisions about matters considered material to the organization's cybersecurity and privacy program?.",
         'Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment through a steering '
         'committee or advisory board, comprising of key cybersecurity, privacy and business executives, which meets formally '
         'and on a regular basis?.',
         'Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and privacy controls?.',
         'Q-RSK-04.1: Does the organization maintain a risk register that facilitates monitoring and reporting of risks?.',
         'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the likelihood and magnitude of '
         "harm, from unauthorized access, use, disclosure, disruption, modification or destruction of the organization's "
         'systems and data?.',
         'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
         'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy assessments, incidents and '
         'audits to ensure proper remediation has been performed?.',
         'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
         'Q-RSK-05: Does the organization identify and assign a risk ranking to newly discovered security vulnerabilities that '
         'is based on industry-recognized practices? .',
         'Q-IAC-21.1: Does the organization limit access to security functions to explicitly-authorized privileged users?.',
         'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only authorized access to processes '
         'necessary to accomplish assigned tasks in accordance with organizational business functions? .',
         'Q-IAC-20.6: Does the organization revoke logical and physical access authorizations?.',
         'Q-IAC-20.5: Does the organization enforce dual authorization for privileged commands?.',
         'Q-IAC-20.4: Does the organization restrict executing administrative tasks or tasks requiring elevated access to a '
         'dedicated machine?.',
         'Q-IAC-20.3: Does the organization restrict and tightly control utility programs that are capable of overriding '
         'system and application controls?.',
         'Q-IAC-20.2: Does the organization restrict access to database containing sensitive/regulated data to only necessary '
         'services or those individuals whose job requires such access?.',
         'Q-IAC-20.1: Does the organization limit access to sensitive/regulated data to only those individuals whose job '
         'requires such access?.',
         'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that conform to the principle of '
         "'least privilege?'.",
         'Q-IAC-18: Does the organization compel users to follow accepted practices in the use of authentication mechanisms '
         '(e.g. passwords, passphrases, physical or logical security tokens, smart cards, certificates, etc.)? .',
         'Q-IAC-17: Does the organization periodically-review the privileges assigned to individuals and service accounts to '
         'validate the need for such privileges and reassign or remove unnecessary privileges, as necessary?.',
         'Q-IAC-16.2: Does the organization separate privileged accounts between infrastructure environments to reduce the '
         'risk of a compromise in one infrastructure environment from laterally affecting other infrastructure environments?.',
         'Q-IAC-16.1: Does the organization inventory all privileged accounts and validate that each person with elevated '
         'privileges is authorized by the appropriate level of organizational management? .',
         'Q-IAC-16: Does the organization restrict and control privileged access rights for users and services?.',
         'Q-IAC-07.2: Does the organization revoke user access rights in a timely manner, upon termination of employment or '
         'contract?.',
         'Q-IAC-07.1: Does the organization revoke user access rights following changes in personnel roles and duties, if no '
         'longer necessary or permitted? .',
         'Q-IAC-07: Does the organization utilize a formal user registration and de-registration process that governs the '
         'assignment of access rights? .',
         'Q-IAC-02.1: Does the organization require individuals to be authenticated with an individual authenticator when a '
         'group authenticator is utilized? .',
         'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users and processes acting on '
         'behalf of organizational users? .',
         "Q-IAC-21.7: Does the organization prevent applications from executing at higher privilege levels than the user's "
         'privileges? .',
         'Q-IAC-21.6: Does the organization authorize remote access to perform privileged commands on critical systems or '
         'where sensitive/regulated data is stored, transmitted and/or processed only for compelling operational needs?.',
         'Q-IAC-21.5: Does the organization prevent non-privileged users from executing privileged functions to include '
         'disabling, circumventing or altering implemented security safeguards / countermeasures? .',
         'Q-IAC-21.4: Does the organization audit the execution of privileged functions? .',
         'Q-IAC-21.3: Does the organization restrict the assignment of privileged accounts to organization-defined personnel '
         'or roles without management approval?.',
         'Q-IAC-21.2: Does the organization prohibit privileged users from using privileged accounts, while performing '
         'non-security functions? .',
         'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, individual, or responsible '
         'organization level to establish a common understanding of requirements for asset protection?.',
         'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  '
         'Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined '
         'information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit '
         'by designated organizational officials? .',
         'Q-CRY-07: Does the organization protect wireless access via secure authentication and encryption?.',
         'Q-CRY-06: Does the organization use cryptographic mechanisms to protect the confidentiality and integrity of '
         'non-console administrative access?.',
         'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent unauthorized disclosure of data '
         'at rest? .',
         'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of data being transmitted? .',
         'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the confidentiality of data being '
         'transmitted? .',
         'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known '
         'public standards and trusted cryptographic technologies?.',
         'Q-TDA-19: Does the organization handle error conditions by:   -  Identifying potentially security-relevant error '
         'conditions;  -  Generating error messages that provide information necessary for corrective actions without '
         'revealing sensitive or potentially harmful information in error logs and administrative messages that could be '
         'exploited; and  -  Revealing error messages only to authorized personnel?.',
         'Q-TDA-18: Does the organization check the validity of information inputs? .',
         'Q-TDA-16: Does the organization require the developers of systems, system components or services to provide training '
         'on the correct use and operation of the system, system component or service?.',
         'Q-TDA-15: Does the organization require system developers and integrators to create a Security Test and Evaluation '
         '(ST&E) plan and implement the plan under the witness of an independent party? .',
         'Q-TDA-10: Does the organization approve, document and control the use of live data in development and test '
         'environments?.',
         'Q-TDA-09: Does the organization require system developers/integrators consult with cybersecurity and privacy '
         'personnel to:   -  Create and implement a Security Test and Evaluation (ST&E) plan;  -  Implement a verifiable flaw '
         'remediation process to correct weaknesses and deficiencies identified during the security testing and evaluation '
         'process; and  -  Document the results of the security testing/evaluation and flaw remediation processes?.',
         'Q-TDA-08: Does the organization manage separate development, testing and operational environments to reduce the '
         'risks of unauthorized access or changes to the operational environment and to ensure no impact to production '
         'systems?.',
         'Q-TDA-07: Does the organization maintain a segmented development network to ensure a secure development environment? '
         '.',
         'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
         'Q-TDA-02.1: Does the organization require the developers of systems, system components or services to identify early '
         'in the Secure Development Life Cycle (SDLC), the functions, ports, protocols and services intended for use? .',
         'Q-IAC-06.4: Does the organization implement Multi-Factor Authentication (MFA) for remote access to privileged and '
         'non-privileged accounts such that one of the factors is securely provided by a device separate from the system '
         'gaining access? .',
         'Q-IAC-06.3: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate local access for '
         'privileged accounts? .',
         'Q-IAC-06.2: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate network access for '
         'non-privileged accounts? .',
         'Q-IAC-06.1: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate network access for '
         'privileged accounts? .',
         'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access? .',
         'Q-DCH-09.5: Does the organization enforce dual authorization for the destruction, disposal or sanitization of '
         'digital media that contains sensitive/regulated data?.',
         'Q-DCH-09.4: Does the organization apply nondestructive sanitization techniques to portable storage devices prior to '
         'first use?.',
         'Q-DCH-09.3: Does the organization facilitate the sanitization of Personal Data (PD)?.',
         'Q-DCH-09.2: Does the organization test sanitization equipment and procedures to verify that the intended result is '
         'achieved? .',
         'Q-DCH-09.1: Does the organization supervise, track, document and verify media sanitization and disposal actions? .',
         'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity commensurate with the '
         'classification or sensitivity of the information prior to disposal, release out of organizational control or release '
         'for reuse?.',
         'Q-DCH-08: Does the organization securely dispose of media when it is no longer required, using formal procedures? .',
         'Q-CHG-04: Does the organization enforce configuration restrictions in an effort to restrict the ability of users to '
         'conduct unauthorized changes?.',
         'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, prior to the implementation '
         'of the change?.',
         'Q-CHG-02: Does the organization govern the technical configuration change control processes?.',
         'Q-CHG-01: Does the organization facilitate the implementation of a change management program?.',
         'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized access, modification and '
         'deletion?.',
         'Q-MON-06: Does the organization provide an event log report generation capability to aid in detecting and assessing '
         'anomalous activities? .',
         'Q-MON-05: Does the organization alert appropriate personnel in the event of a log processing failure and take '
         'actions to remedy the disruption?.',
         'Q-MON-04: Does the organization allocate and proactively manage sufficient event log storage capacity to reduce the '
         'likelihood of such capacity being exceeded?.',
         'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or similar automated tool, to '
         'support the centralized collection of security-related event logs?.',
         'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide monitoring controls?.',
         'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and procedures at planned '
         'intervals or if significant changes occur to ensure their continuing suitability, adequacy and effectiveness? .',
         'Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the continuous monitoring strategy '
         'that includes monitoring the effectiveness of security & privacy controls, compliance and change management?.',
         'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by recurring vulnerability scanning '
         'of systems and web applications?.',
         'Q-VPM-05: Does the organization conduct software patching for all deployed operating systems, applications and '
         'firmware?.',
         'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing basis and ensure assets are '
         'protected against known attacks? .',
         'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, tracked and remediated?.',
         'Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.',
         'Q-SAT-04: Does the organization document, retain and monitor individual training activities, including basic '
         'security awareness training, ongoing awareness training and specific-system training?.',
         'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before authorizing access to the '
         'system or performing assigned duties;   -  When required by system changes; and   -  Annually thereafter?.',
         'Q-SAT-02: Does the organization provide all employees and contractors appropriate awareness education and training '
         'that is relevant for their job function? .',
         'Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness '
         'controls? .',
         'Q-GOV-07: Does the organization establish contact with selected groups and associations within the cybersecurity & '
         'privacy communities to:   -  Facilitate ongoing cybersecurity and privacy education and training for organizational '
         'personnel;  -  Maintain currency with recommended cybersecurity and privacy practices, techniques and technologies; '
         'and  -  Share current security-related information including threats, vulnerabilities and incidents? .',
         'Q-SAT-03.8: Does the organization ensure application development and operations (DevOps) personnel receive '
         'Continuing Professional Education (CPE) training on Secure Software Development Practices (SSDP) to appropriately '
         'address evolving threats?.',
         'Q-SAT-03.7: Does the organization ensure cybersecurity and privacy personnel receive Continuing Professional '
         'Education (CPE) training to maintain currency and proficiency with industry-recognized secure practices that are '
         'pertinent to their assigned roles and responsibilities?.',
         'Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness training that is specific '
         "to the cyber threats that the user might encounter the user's specific day-to-day business operations?.",
         'Q-SAT-03.5: Does the organization provides specific training for privileged users to ensure privileged users '
         'understand their unique roles and responsibilities .',
         'Q-THR-05: Does the organization utilize security awareness training on recognizing and reporting potential '
         'indicators of insider threat?.',
         'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
         'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the potential attack vectors that '
         'attackers could use to attack the organization? .',
         'Q-THR-01: Does the organization implement a threat awareness program that includes a cross-organization '
         'information-sharing capability? .',
         'Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of critical systems, '
         'components and services using a supply chain risk assessment process? .',
         'Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of Third-Party Service Providers '
         '(TSP) that can potentially impact the Confidentiality, Integrity, Availability and/or Safety (CIAS) of the '
         "organization's systems, applications, services and data?.",
         'Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.',
         'Q-TPM-05: Does the organization identify, regularly review and document third-party confidentiality, Non-Disclosure '
         "Agreements (NDAs) and other contracts that reflect the organization's needs to protect systems and data?.",
         'Q-TPM-04.4: Does the organization restrict the location of information processing/storage based on business '
         'requirements? .',
         'Q-TPM-04.3: Does the organization ensure that the interests of third-party service providers are consistent with and '
         'reflect organizational interests?.',
         'Q-TPM-04.2: Does the organization require process owners to identify the ports, protocols and other services '
         'required for the use of such services? .',
         'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or outsourcing of '
         'technology-related services?.',
         "Q-TPM-04: Does the organization mitigate the risks associated with third-party access to the organization's systems "
         'and data?.',
         'Q-TPM-03.3: Does the organization address identified weaknesses or deficiencies in the security of the supply chain '
         '.',
         'Q-TPM-03.2: Does the organization utilize security safeguards to limit harm from potential adversaries who identify '
         "and target the organization's supply chain? .",
         'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools and procurement methods '
         'for the purchase of unique systems, system components or services?.',
         'Q-TPM-03: Does the organization evaluate security risks associated with the services and product supply chain? .',
         'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for its cybersecurity and '
         'privacy programs?.',
         'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and assess cybersecurity and '
         'data protection risks?.',
         'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly upon identifying new '
         'security vulnerabilities, including using outside sources for security vulnerability information? .',
         'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to reduce risk and exposure to '
         'threats?.',
         'Q-IRO-02.6: Does the organization automatically disable systems involved in an incident that meet organizational '
         'criteria to be automatically disabled upon detection?.',
         'Q-IRO-02.5: Does the organization coordinate with approved third-parties to achieve a cross-organization perspective '
         'on incident awareness and more effective incident responses? .',
         'Q-IRO-02.4: Does the organization identify classes of incidents and actions to take to ensure the continuation of '
         'organizational missions and business functions?.',
         'Q-IRO-02.3: Does the organization dynamically reconfigure information system components as part of the incident '
         'response capability? .',
         'Q-IRO-02.2: Does the organization prevent identity theft from occurring? .',
         'Q-IRO-02.1: Does the organization use automated mechanisms to support the incident handling process? .',
         "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, "
         'containment, eradication and recovery?.',
         'Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.',
         'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy incidents? .',
         'Q-IRO-06.1: Does the organization coordinate incident response testing with organizational elements responsible for '
         'related plans? .',
         'Q-IRO-04.1: Does the organization address data breaches, or other incidents involving the unauthorized disclosure of '
         'sensitive or regulated data, according to applicable laws, regulations and contractual obligations? .',
         'Q-IRO-04: Does the organization maintain and make available a current and viable Incident Response Plan (IRP) to all '
         'stakeholders?.',
         'Q-IRO-03: Does the organization define specific Indicators of Compromise (IOC) that identify the potential impact of '
         'likely cybersecurity events?.',
         'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and business function '
         'representatives that are capable of addressing cybersecurity and privacy incident response operations?.',
         'Q-IRO-05: Does the organization train personnel in their incident response roles and responsibilities?.',
         'Q-IRO-10.4: Does the organization provide cybersecurity and privacy incident information to the provider of the '
         'product or service and other organizations involved in the supply chain for systems or system components related to '
         'the incident?.',
         'Q-IRO-10.1: Does the organization use automated mechanisms to assist in the reporting of cybersecurity and privacy '
         'incidents?.',
         'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational incident response personnel '
         'within organization-defined time-periods; and  -  Externally to regulatory authorities and affected parties, as '
         'necessary?.',
         'Q-IRO-05.1: Does the organization incorporate simulated events into incident response training to facilitate '
         'effective response by personnel in crisis situations?.',
         'Q-IRO-04.3: Does the organization use qualitative and quantitative data from incident response testing to:  - '
         'Determine the effectiveness of incident response processes; - Continuously improve incident response processes; and '
         '- Provide incident response measures and metrics that are accurate, consistent, and in a reproducible format?.',
         'Q-IRO-04.2: Does the organization regularly review and modify incident response practices to incorporate lessons '
         'learned, business process changes and industry developments, as necessary?.',
         'Q-IRO-14: Does the organization maintain incident response contacts with applicable regulatory and law enforcement '
         'agencies? .',
         'Q-IRO-10.3: Does the organization report system vulnerabilities associated with reported cybersecurity and privacy '
         'incidents to organization-defined personnel or roles?.',
         'Q-IRO-10.2: Does the organization report sensitive/regulated data incidents in a timely manner?.',
         'Q-IRO-09.1: Does the organization use automated mechanisms to assist in the tracking, collection and analysis of '
         'information from actual and potential cybersecurity and privacy incidents?.',
         'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving cybersecurity and privacy '
         'incidents to reduce the likelihood or impact of future incidents? .',
         'Q-IAO-06: Does the organization perform Information Assurance Program (IAP) activities to evaluate the design, '
         'implementation and effectiveness of technical cybersecurity and privacy controls?.',
         'Q-IAO-02: Does the organization formally assess the cybersecurity and privacy controls in systems, applications and '
         'services through Information Assurance Program (IAP) activities to determine the extent to which the controls are '
         'implemented correctly, operating as intended and producing the desired outcome with respect to meeting expected '
         'requirements?.',
         'Q-GOV-09: Does the organization establish control objectives as the basis for the selection, implementation and '
         "management of the organization's internal control system?.",
         'Q-GOV-08: Does the organization define the context of its business model and document the mission of the '
         'organization?.']

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '314.4.a.1: Retain responsibility for compliance with this part',
          'requirement_description': '\n'
                                     'Designate a qualified individual responsible for overseeing and implementing your '
                                     'information security program and enforcing your information security program (for '
                                     "purposes of this part, 'Qualified Individual'). The Qualified Individual may be employed "
                                     'by you, an affiliate, or a service provider.',
          'subchapter': '314.4.a: Qualified Individual'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-01.2: Does the organization provide governance oversight reporting and '
                                   'recommendations to those entrusted to make executive decisions about matters considered '
                                   "material to the organization's cybersecurity and privacy program?."],
          'objective_title': '314.4.a.2: Designate a senior member of your personnel responsible for direction and oversight '
                             'of the Qualified Individual',
          'requirement_description': None,
          'subchapter': '314.4.a: Qualified Individual'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-01.1: Does the organization coordinate cybersecurity, privacy and business alignment '
                                   'through a steering committee or advisory board, comprising of key cybersecurity, privacy '
                                   'and business executives, which meets formally and on a regular basis?.',
                                   'Q-GOV-01: Does the organization staff a function to centrally-govern cybersecurity and '
                                   'privacy controls?.'],
          'objective_title': '314.4.a.3: Require the service provider or affiliate to maintain an information security program '
                             'that protects you in accordance with the requirements of this part',
          'requirement_description': None,
          'subchapter': '314.4.a: Qualified Individual'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-RSK-04.1: Does the organization maintain a risk register that facilitates monitoring and '
                                   'reporting of risks?.',
                                   'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?.",
                                   'Q-RSK-03: Does the organization identify and document risks, both internal and external? '
                                   '.'],
          'objective_title': '314.4.b.1: The risk assessment shall be written',
          'requirement_description': '\n'
                                     'Base your information security program on a risk assessment that identifies reasonably '
                                     'foreseeable internal and external risks to the security, confidentiality, and integrity '
                                     'of customer information that could result in the unauthorized disclosure, misuse, '
                                     'alteration, destruction, or other compromise of such information, and assesses the '
                                     'sufficiency of any safeguards in place to control these risks. \n'
                                     'The risk assessment shall be written and shall include \n'
                                     '(i) Criteria for the evaluation and categorization of identified security risks or '
                                     'threats you face; \n'
                                     '(ii) Criteria for the assessment of the confidentiality, integrity, and availability of '
                                     'your information systems and customer information, including the adequacy of the '
                                     'existing controls in the context of the identified risks or threats you face; and \n'
                                     '(iii) Requirements describing how identified risks will be mitigated or accepted based '
                                     'on the risk assessment and how the information security program will address the risks.',
          'subchapter': '314.4.b: Risk Assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
                                   'Q-RSK-05: Does the organization identify and assign a risk ranking to newly discovered '
                                   'security vulnerabilities that is based on industry-recognized practices? .'],
          'objective_title': '314.4.b.2: Periodically perform additional risk assessments',
          'requirement_description': 'You shall periodically perform additional risk assessments that reexamine the reasonably '
                                     'foreseeable internal and external risks to the security, confidentiality, and integrity '
                                     'of customer information that could result in the unauthorized disclosure, misuse, '
                                     'alteration, destruction, or other compromise of such information, and reassess the '
                                     'sufficiency of any safeguards in place to control these risks',
          'subchapter': '314.4.b: Risk Assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IAC-21.1: Does the organization limit access to security functions to '
                                   'explicitly-authorized privileged users?.',
                                   'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-IAC-20.6: Does the organization revoke logical and physical access authorizations?.',
                                   'Q-IAC-20.5: Does the organization enforce dual authorization for privileged commands?.',
                                   'Q-IAC-20.4: Does the organization restrict executing administrative tasks or tasks '
                                   'requiring elevated access to a dedicated machine?.',
                                   'Q-IAC-20.3: Does the organization restrict and tightly control utility programs that are '
                                   'capable of overriding system and application controls?.',
                                   'Q-IAC-20.2: Does the organization restrict access to database containing '
                                   'sensitive/regulated data to only necessary services or those individuals whose job '
                                   'requires such access?.',
                                   'Q-IAC-20.1: Does the organization limit access to sensitive/regulated data to only those '
                                   'individuals whose job requires such access?.',
                                   'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that '
                                   "conform to the principle of 'least privilege?'.",
                                   'Q-IAC-18: Does the organization compel users to follow accepted practices in the use of '
                                   'authentication mechanisms (e.g. passwords, passphrases, physical or logical security '
                                   'tokens, smart cards, certificates, etc.)? .',
                                   'Q-IAC-17: Does the organization periodically-review the privileges assigned to individuals '
                                   'and service accounts to validate the need for such privileges and reassign or remove '
                                   'unnecessary privileges, as necessary?.',
                                   'Q-IAC-16.2: Does the organization separate privileged accounts between infrastructure '
                                   'environments to reduce the risk of a compromise in one infrastructure environment from '
                                   'laterally affecting other infrastructure environments?.',
                                   'Q-IAC-16.1: Does the organization inventory all privileged accounts and validate that each '
                                   'person with elevated privileges is authorized by the appropriate level of organizational '
                                   'management? .',
                                   'Q-IAC-16: Does the organization restrict and control privileged access rights for users '
                                   'and services?.',
                                   'Q-IAC-07.2: Does the organization revoke user access rights in a timely manner, upon '
                                   'termination of employment or contract?.',
                                   'Q-IAC-07.1: Does the organization revoke user access rights following changes in personnel '
                                   'roles and duties, if no longer necessary or permitted? .',
                                   'Q-IAC-07: Does the organization utilize a formal user registration and de-registration '
                                   'process that governs the assignment of access rights? .',
                                   'Q-IAC-02.1: Does the organization require individuals to be authenticated with an '
                                   'individual authenticator when a group authenticator is utilized? .',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-21.7: Does the organization prevent applications from executing at higher privilege '
                                   "levels than the user's privileges? .",
                                   'Q-IAC-21.6: Does the organization authorize remote access to perform privileged commands '
                                   'on critical systems or where sensitive/regulated data is stored, transmitted and/or '
                                   'processed only for compelling operational needs?.',
                                   'Q-IAC-21.5: Does the organization prevent non-privileged users from executing privileged '
                                   'functions to include disabling, circumventing or altering implemented security safeguards '
                                   '/ countermeasures? .',
                                   'Q-IAC-21.4: Does the organization audit the execution of privileged functions? .',
                                   'Q-IAC-21.3: Does the organization restrict the assignment of privileged accounts to '
                                   'organization-defined personnel or roles without management approval?.',
                                   'Q-IAC-21.2: Does the organization prohibit privileged users from using privileged '
                                   'accounts, while performing non-security functions? .'],
          'objective_title': '314.4.c.1: Implementing and periodically reviewing access controls, including technical and, as '
                             'appropriate, physical controls',
          'requirement_description': '\n'
                                     'Implementing and periodically reviewing access controls, including technical and, as '
                                     'appropriate, physical controls to:\n'
                                     ' \n'
                                     '(i) Authenticate and permit access only to authorized users to protect against the '
                                     'unauthorized acquisition of customer information; and \n'
                                     "(ii) Limit authorized users' access only to customer information that they need to "
                                     'perform their duties and functions, or, in the case of customers, to access their own '
                                     'information;',
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-AST-03: Does the organization assign asset ownership responsibilities to a team, '
                                   'individual, or responsible organization level to establish a common understanding of '
                                   'requirements for asset protection?.',
                                   'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .'],
          'objective_title': '314.4.c.2: Identify and manage the data, personnel, devices, systems, and facilities that enable '
                             'you to achieve business purposes in accordance with their relative importance to business '
                             'objectives and your risk strategy',
          'requirement_description': None,
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-CRY-07: Does the organization protect wireless access via secure authentication and '
                                   'encryption?.',
                                   'Q-CRY-06: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality and integrity of non-console administrative access?.',
                                   'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .',
                                   'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of '
                                   'data being transmitted? .',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .',
                                   'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.'],
          'objective_title': '314.4.c.3: Protect by encryption all customer information held or transmitted by you both in '
                             'transit over external networks and at rest',
          'requirement_description': 'Protect by encryption all customer information held or transmitted by you both in '
                                     'transit over external networks and at rest. To the extent you determine that encryption '
                                     'of customer information, either in transit over external networks or at rest, is '
                                     'infeasible, you may instead secure such customer information using effective alternative '
                                     'compensating controls reviewed and approved by your Qualified Individual;',
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-TDA-19: Does the organization handle error conditions by:   -  Identifying potentially '
                                   'security-relevant error conditions;  -  Generating error messages that provide information '
                                   'necessary for corrective actions without revealing sensitive or potentially harmful '
                                   'information in error logs and administrative messages that could be exploited; and  -  '
                                   'Revealing error messages only to authorized personnel?.',
                                   'Q-TDA-18: Does the organization check the validity of information inputs? .',
                                   'Q-TDA-16: Does the organization require the developers of systems, system components or '
                                   'services to provide training on the correct use and operation of the system, system '
                                   'component or service?.',
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-TDA-10: Does the organization approve, document and control the use of live data in '
                                   'development and test environments?.',
                                   'Q-TDA-09: Does the organization require system developers/integrators consult with '
                                   'cybersecurity and privacy personnel to:   -  Create and implement a Security Test and '
                                   'Evaluation (ST&E) plan;  -  Implement a verifiable flaw remediation process to correct '
                                   'weaknesses and deficiencies identified during the security testing and evaluation process; '
                                   'and  -  Document the results of the security testing/evaluation and flaw remediation '
                                   'processes?.',
                                   'Q-TDA-08: Does the organization manage separate development, testing and operational '
                                   'environments to reduce the risks of unauthorized access or changes to the operational '
                                   'environment and to ensure no impact to production systems?.',
                                   'Q-TDA-07: Does the organization maintain a segmented development network to ensure a '
                                   'secure development environment? .',
                                   'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
                                   'Q-TDA-02.1: Does the organization require the developers of systems, system components or '
                                   'services to identify early in the Secure Development Life Cycle (SDLC), the functions, '
                                   'ports, protocols and services intended for use? .'],
          'objective_title': '314.4.c.4: Adopt secure development practices for in-house developed applications',
          'requirement_description': 'Adopt secure development practices for in-house developed applications utilized by you '
                                     'for transmitting, accessing, or storing customer information and procedures for '
                                     'evaluating, assessing, or testing the security of externally developed applications you '
                                     'utilize to transmit, access, or store customer information',
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IAC-06.4: Does the organization implement Multi-Factor Authentication (MFA) for remote '
                                   'access to privileged and non-privileged accounts such that one of the factors is securely '
                                   'provided by a device separate from the system gaining access? .',
                                   'Q-IAC-06.3: Does the organization utilize Multi-Factor Authentication (MFA) to '
                                   'authenticate local access for privileged accounts? .',
                                   'Q-IAC-06.2: Does the organization utilize Multi-Factor Authentication (MFA) to '
                                   'authenticate network access for non-privileged accounts? .',
                                   'Q-IAC-06.1: Does the organization utilize Multi-Factor Authentication (MFA) to '
                                   'authenticate network access for privileged accounts? .',
                                   'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote '
                                   'network access? .'],
          'objective_title': '314.4.c.5: Implement multi-factor authentication for any individual accessing any information '
                             'system',
          'requirement_description': 'Implement multi-factor authentication for any individual accessing any information '
                                     'system, unless your Qualified Individual has approved in writing the use of reasonably '
                                     'equivalent or more secure access controls;',
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-DCH-09.5: Does the organization enforce dual authorization for the destruction, disposal '
                                   'or sanitization of digital media that contains sensitive/regulated data?.',
                                   'Q-DCH-09.4: Does the organization apply nondestructive sanitization techniques to portable '
                                   'storage devices prior to first use?.',
                                   'Q-DCH-09.3: Does the organization facilitate the sanitization of Personal Data (PD)?.',
                                   'Q-DCH-09.2: Does the organization test sanitization equipment and procedures to verify '
                                   'that the intended result is achieved? .',
                                   'Q-DCH-09.1: Does the organization supervise, track, document and verify media sanitization '
                                   'and disposal actions? .',
                                   'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity '
                                   'commensurate with the classification or sensitivity of the information prior to disposal, '
                                   'release out of organizational control or release for reuse?.',
                                   'Q-DCH-08: Does the organization securely dispose of media when it is no longer required, '
                                   'using formal procedures? .'],
          'objective_title': '314.4.c.6: Secure disposal and retention',
          'requirement_description': '\n'
                                     '(i) Develop, implement, and maintain procedures for the secure disposal of customer '
                                     'information in any format no later than two years after the last date the information is '
                                     'used in connection with the provision of a product or service to the customer to which '
                                     'it relates, unless such information is necessary for business operations or for other '
                                     'legitimate business purposes, is otherwise required to be retained by law or regulation, '
                                     'or where targeted disposal is not reasonably feasible due to the manner in which the '
                                     'information is maintained; and \n'
                                     '(ii) Periodically review your data retention policy to minimize the unnecessary '
                                     'retention of data;',
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-CHG-04: Does the organization enforce configuration restrictions in an effort to '
                                   'restrict the ability of users to conduct unauthorized changes?.',
                                   'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, '
                                   'prior to the implementation of the change?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CHG-01: Does the organization facilitate the implementation of a change management '
                                   'program?.'],
          'objective_title': '314.4.c.7: Adopt procedures for change management',
          'requirement_description': None,
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-MON-08: Does the organization protect event logs and audit tools from unauthorized '
                                   'access, modification and deletion?.',
                                   'Q-MON-06: Does the organization provide an event log report generation capability to aid '
                                   'in detecting and assessing anomalous activities? .',
                                   'Q-MON-05: Does the organization alert appropriate personnel in the event of a log '
                                   'processing failure and take actions to remedy the disruption?.',
                                   'Q-MON-04: Does the organization allocate and proactively manage sufficient event log '
                                   'storage capacity to reduce the likelihood of such capacity being exceeded?.',
                                   'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or '
                                   'similar automated tool, to support the centralized collection of security-related event '
                                   'logs?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.'],
          'objective_title': '314.4.c.8: Implement policies, procedures, and controls designed to monitor and log the activity '
                             'of authorized users and detect unauthorized access or use of, or tampering with, customer '
                             'information by such users',
          'requirement_description': None,
          'subchapter': '314.4.c: Implement safeguards to control the risks you identity through risk assessment'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-RSK-11: Does the organization ensure risk monitoring as an integral part of the '
                                   'continuous monitoring strategy that includes monitoring the effectiveness of security & '
                                   'privacy controls, compliance and change management?.'],
          'objective_title': "314.4.d.1: Regularly test or otherwise monitor the effectiveness of the safeguards' key "
                             'controls, systems, and procedures, including those to detect actual and attempted attacks on, or '
                             'intrusions into, information systems',
          'requirement_description': None,
          'subchapter': '314.4.d: Monitor the effectiveness of the safeguards'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-05: Does the organization conduct software patching for all deployed operating '
                                   'systems, applications and firmware?.',
                                   'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing '
                                   'basis and ensure assets are protected against known attacks? .',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-01: Does the organization facilitate the implementation and monitoring of '
                                   'vulnerability management controls?.'],
          'objective_title': '314.4.d.2: For information systems, the monitoring and testing shall include continuous '
                             'monitoring or periodic penetration testing and vulnerability assessments',
          'requirement_description': '\n'
                                     'For information systems, the monitoring and testing shall include continuous monitoring '
                                     'or periodic penetration testing and vulnerability assessments. Absent effective '
                                     'continuous monitoring or other systems to detect, on an ongoing basis, changes in '
                                     'information systems that may create vulnerabilities, you shall conduct: \n'
                                     '(i) Annual penetration testing of your information systems determined each given year '
                                     'based on relevant identified risks in accordance with the risk assessment; and \n'
                                     '(ii) Vulnerability assessments, including any systemic scans or reviews of information '
                                     'systems reasonably designed to identify publicly known security vulnerabilities in your '
                                     'information systems based on the risk assessment, at least every six months; and '
                                     'whenever there are material changes to your operations or business arrangements; and '
                                     'whenever there are circumstances you know or have reason to know may have a material '
                                     'impact on your information security program.',
          'subchapter': '314.4.d: Monitor the effectiveness of the safeguards'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-SAT-04: Does the organization document, retain and monitor individual training '
                                   'activities, including basic security awareness training, ongoing awareness training and '
                                   'specific-system training?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .',
                                   'Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .'],
          'objective_title': '314.4.e.1: Providing your personnel with security awareness training that is updated as '
                             'necessary to reflect risks identified by the risk assessment;',
          'requirement_description': None,
          'subchapter': '314.4.e: Implement policies and procedures to ensure that personnel are able to enact your '
                        'information security program'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-07: Does the organization establish contact with selected groups and associations '
                                   'within the cybersecurity & privacy communities to:   -  Facilitate ongoing cybersecurity '
                                   'and privacy education and training for organizational personnel;  -  Maintain currency '
                                   'with recommended cybersecurity and privacy practices, techniques and technologies; and  -  '
                                   'Share current security-related information including threats, vulnerabilities and '
                                   'incidents? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '314.4.e.2: Utilizing qualified information security personnel employed by you or an affiliate or '
                             'service provider sufficient to manage your information security risks and to perform or oversee '
                             'the information security program;',
          'requirement_description': None,
          'subchapter': '314.4.e: Implement policies and procedures to ensure that personnel are able to enact your '
                        'information security program'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-SAT-03.8: Does the organization ensure application development and operations (DevOps) '
                                   'personnel receive Continuing Professional Education (CPE) training on Secure Software '
                                   'Development Practices (SSDP) to appropriately address evolving threats?.',
                                   'Q-SAT-03.7: Does the organization ensure cybersecurity and privacy personnel receive '
                                   'Continuing Professional Education (CPE) training to maintain currency and proficiency with '
                                   'industry-recognized secure practices that are pertinent to their assigned roles and '
                                   'responsibilities?.',
                                   'Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness '
                                   "training that is specific to the cyber threats that the user might encounter the user's "
                                   'specific day-to-day business operations?.',
                                   'Q-SAT-03.5: Does the organization provides specific training for privileged users to '
                                   'ensure privileged users understand their unique roles and responsibilities .'],
          'objective_title': '314.4.e.3: Providing information security personnel with security updates and training '
                             'sufficient to address relevant security risks',
          'requirement_description': None,
          'subchapter': '314.4.e: Implement policies and procedures to ensure that personnel are able to enact your '
                        'information security program'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-07: Does the organization establish contact with selected groups and associations '
                                   'within the cybersecurity & privacy communities to:   -  Facilitate ongoing cybersecurity '
                                   'and privacy education and training for organizational personnel;  -  Maintain currency '
                                   'with recommended cybersecurity and privacy practices, techniques and technologies; and  -  '
                                   'Share current security-related information including threats, vulnerabilities and '
                                   'incidents? .',
                                   'Q-THR-05: Does the organization utilize security awareness training on recognizing and '
                                   'reporting potential indicators of insider threat?.',
                                   'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
                                   'Q-THR-02: Does the organization develop Indicators of Exposure (IOE) to understand the '
                                   'potential attack vectors that attackers could use to attack the organization? .',
                                   'Q-THR-01: Does the organization implement a threat awareness program that includes a '
                                   'cross-organization information-sharing capability? .'],
          'objective_title': '314.4.e.4: Verifying that key information security personnel take steps to maintain current '
                             'knowledge of changing information security threats and countermeasures',
          'requirement_description': None,
          'subchapter': '314.4.e: Implement policies and procedures to ensure that personnel are able to enact your '
                        'information security program'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-TPM-02: Does the organization identify, prioritize and assess suppliers and partners of '
                                   'critical systems, components and services using a supply chain risk assessment process? .',
                                   'Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of '
                                   'Third-Party Service Providers (TSP) that can potentially impact the Confidentiality, '
                                   "Integrity, Availability and/or Safety (CIAS) of the organization's systems, applications, "
                                   'services and data?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': '314.4.f.1: Taking reasonable steps to select and retain service providers that are capable of '
                             'maintaining appropriate safeguards for the customer information at issue',
          'requirement_description': None,
          'subchapter': '314.4.f: Oversee service providers'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': [],
          'objective_title': '314.4.f.2: Requiring your service providers by contract to implement and maintain such '
                             'safeguards; and',
          'requirement_description': None,
          'subchapter': '314.4.f: Oversee service providers'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?.",
                                   'Q-TPM-04.4: Does the organization restrict the location of information processing/storage '
                                   'based on business requirements? .',
                                   'Q-TPM-04.3: Does the organization ensure that the interests of third-party service '
                                   'providers are consistent with and reflect organizational interests?.',
                                   'Q-TPM-04.2: Does the organization require process owners to identify the ports, protocols '
                                   'and other services required for the use of such services? .',
                                   'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.',
                                   'Q-TPM-04: Does the organization mitigate the risks associated with third-party access to '
                                   "the organization's systems and data?.",
                                   'Q-TPM-03.3: Does the organization address identified weaknesses or deficiencies in the '
                                   'security of the supply chain .',
                                   'Q-TPM-03.2: Does the organization utilize security safeguards to limit harm from potential '
                                   "adversaries who identify and target the organization's supply chain? .",
                                   'Q-TPM-03.1: Does the organization utilize tailored acquisition strategies, contract tools '
                                   'and procurement methods for the purchase of unique systems, system components or '
                                   'services?.',
                                   'Q-TPM-03: Does the organization evaluate security risks associated with the services and '
                                   'product supply chain? .'],
          'objective_title': '314.4.f.3: Periodically assessing your service providers based on the risk they present and the '
                             'continued adequacy of their safeguards',
          'requirement_description': None,
          'subchapter': '314.4.f: Oversee service providers'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.',
                                   'Q-RSK-08: Does the organization conduct a Business Impact Analysis (BIA) to identify and '
                                   'assess cybersecurity and data protection risks?.',
                                   'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .',
                                   'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to '
                                   'reduce risk and exposure to threats?.'],
          'objective_title': '314.4.g.1: Evaluate and adjust your information security program in light of the results of the '
                             'testing and monitoring',
          'requirement_description': 'Evaluate and adjust your information security program in light of the results of the '
                                     'testing and monitoring required by paragraph (d) of this section; any material changes '
                                     'to your operations or business arrangements; the results of risk assessments performed '
                                     'under paragraph (b)(2) of this section; or any other circumstances that you know or have '
                                     'reason to know may have a material impact on your information security program.',
          'subchapter': '314.4.g: Evaluate and adjust your information security program in light of the results of the testing '
                        'and monitoring'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IRO-02.6: Does the organization automatically disable systems involved in an incident '
                                   'that meet organizational criteria to be automatically disabled upon detection?.',
                                   'Q-IRO-02.5: Does the organization coordinate with approved third-parties to achieve a '
                                   'cross-organization perspective on incident awareness and more effective incident '
                                   'responses? .',
                                   'Q-IRO-02.4: Does the organization identify classes of incidents and actions to take to '
                                   'ensure the continuation of organizational missions and business functions?.',
                                   'Q-IRO-02.3: Does the organization dynamically reconfigure information system components as '
                                   'part of the incident response capability? .',
                                   'Q-IRO-02.2: Does the organization prevent identity theft from occurring? .',
                                   'Q-IRO-02.1: Does the organization use automated mechanisms to support the incident '
                                   'handling process? .',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.',
                                   'Q-IRO-01: Does the organization facilitate the implementation of incident response '
                                   'controls?.'],
          'objective_title': '314.4.h.1: The goals of the incident response plan',
          'requirement_description': None,
          'subchapter': '314.4.h: Establish a written incident response plan'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .',
                                   'Q-IRO-06.1: Does the organization coordinate incident response testing with organizational '
                                   'elements responsible for related plans? .',
                                   'Q-IRO-04.1: Does the organization address data breaches, or other incidents involving the '
                                   'unauthorized disclosure of sensitive or regulated data, according to applicable laws, '
                                   'regulations and contractual obligations? .',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.',
                                   'Q-IRO-03: Does the organization define specific Indicators of Compromise (IOC) that '
                                   'identify the potential impact of likely cybersecurity events?.'],
          'objective_title': '314.4.h.2: The internal processes for responding to a security event',
          'requirement_description': None,
          'subchapter': '314.4.h: Establish a written incident response plan'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.',
                                   'Q-IRO-05: Does the organization train personnel in their incident response roles and '
                                   'responsibilities?.'],
          'objective_title': '314.4.h.3: Definition of clear roles, responsibilities, and levels of decision-making authority',
          'requirement_description': None,
          'subchapter': '314.4.h: Establish a written incident response plan'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IRO-10.4: Does the organization provide cybersecurity and privacy incident information '
                                   'to the provider of the product or service and other organizations involved in the supply '
                                   'chain for systems or system components related to the incident?.',
                                   'Q-IRO-10.1: Does the organization use automated mechanisms to assist in the reporting of '
                                   'cybersecurity and privacy incidents?.',
                                   'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.'],
          'objective_title': '314.4.h.4: External and internal communications and information sharing',
          'requirement_description': None,
          'subchapter': '314.4.h: Establish a written incident response plan'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IRO-05.1: Does the organization incorporate simulated events into incident response '
                                   'training to facilitate effective response by personnel in crisis situations?.',
                                   'Q-IRO-04.3: Does the organization use qualitative and quantitative data from incident '
                                   'response testing to:  - Determine the effectiveness of incident response processes; - '
                                   'Continuously improve incident response processes; and - Provide incident response measures '
                                   'and metrics that are accurate, consistent, and in a reproducible format?.',
                                   'Q-IRO-04.2: Does the organization regularly review and modify incident response practices '
                                   'to incorporate lessons learned, business process changes and industry developments, as '
                                   'necessary?.',
                                   'Q-IRO-02.4: Does the organization identify classes of incidents and actions to take to '
                                   'ensure the continuation of organizational missions and business functions?.'],
          'objective_title': '314.4.h.5: Identification of requirements for the remediation of any identified weaknesses in '
                             'information systems and associated controls',
          'requirement_description': None,
          'subchapter': '314.4.h: Establish a written incident response plan'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IRO-14: Does the organization maintain incident response contacts with applicable '
                                   'regulatory and law enforcement agencies? .',
                                   'Q-IRO-10.3: Does the organization report system vulnerabilities associated with reported '
                                   'cybersecurity and privacy incidents to organization-defined personnel or roles?.',
                                   'Q-IRO-10.2: Does the organization report sensitive/regulated data incidents in a timely '
                                   'manner?.',
                                   'Q-IRO-09.1: Does the organization use automated mechanisms to assist in the tracking, '
                                   'collection and analysis of information from actual and potential cybersecurity and privacy '
                                   'incidents?.',
                                   'Q-IRO-09: Does the organization document, monitor and report cybersecurity and privacy '
                                   'incidents? .'],
          'objective_title': '314.4.h.6: Documentation and reporting regarding security events and related incident response '
                             'activities;',
          'requirement_description': None,
          'subchapter': '314.4.h: Establish a written incident response plan'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .'],
          'objective_title': '314.4.h.7: The evaluation and revision as necessary of the incident response plan following a '
                             'security event.',
          'requirement_description': None,
          'subchapter': '314.4.h: Establish a written incident response plan'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-IAO-06: Does the organization perform Information Assurance Program (IAP) activities to '
                                   'evaluate the design, implementation and effectiveness of technical cybersecurity and '
                                   'privacy controls?.',
                                   'Q-IAO-02: Does the organization formally assess the cybersecurity and privacy controls in '
                                   'systems, applications and services through Information Assurance Program (IAP) activities '
                                   'to determine the extent to which the controls are implemented correctly, operating as '
                                   'intended and producing the desired outcome with respect to meeting expected '
                                   'requirements?.'],
          'objective_title': '314.4.i.1: The overall status of the information security program',
          'requirement_description': 'Require your Qualified Individual to report in writing, regularly and at least annually, '
                                     'to your board of directors or equivalent governing body. If no such board of directors '
                                     'or equivalent governing body exists, such report shall be timely presented to a senior '
                                     'officer responsible for your information security program. ',
          'subchapter': '314.4.i: Reporting to board or senior officers'},
         {'chapter_title': 'Part 314: Standards for Safeguarding Customer Information',
          'conformity_questions': ['Q-GOV-09: Does the organization establish control objectives as the basis for the '
                                   "selection, implementation and management of the organization's internal control system?.",
                                   'Q-GOV-08: Does the organization define the context of its business model and document the '
                                   'mission of the organization?.',
                                   'Q-GOV-05: Does the organization develop, report, and monitor measures of performance for '
                                   'its cybersecurity and privacy programs?.'],
          'objective_title': '314.4.i.2: Material matters related to the information security program',
          'requirement_description': 'Material matters related to the information security program, addressing issues such as '
                                     'risk assessment, risk management and control decisions, service provider arrangements, '
                                     "results of testing, security events or violations and management's responses thereto, "
                                     'and recommendations for changes in the information security program',
          'subchapter': '314.4.i: Reporting to board or senior officers'}]
