# app/seeds/cmmc_2_0_seed.py
import io
import logging
from .base_seed import BaseSeed
from app.models import models
from app.constants.cmmc_2_0_connections import CMMC_2_0_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class Cmmc20Seed(BaseSeed):
    """Seed CMMC 2.0 framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating CMMC 2.0 framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create CMMC 2.0 Framework
        cmmc_2_0_framework, created = self.get_or_create(
            models.Framework,
            {"name": "CMMC 2.0", "organisation_id": default_org.id},
            {
                "name": "CMMC 2.0",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("CMMC 2.0 framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == cmmc_2_0_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == cmmc_2_0_framework.id
            ).all()

            logger.info(f"Found existing CMMC 2.0 framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            # Keep links in sync even when framework/objectives already exist.
            if not self.skip_wire_connections:
                self._wire_connections(cmmc_2_0_framework, default_org, existing_objectives)
            self.db.commit()

            return {
                "framework": cmmc_2_0_framework,
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
                description="CMMC 2.0 conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=cmmc_2_0_framework.id,
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
                        "framework_id": cmmc_2_0_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": cmmc_2_0_framework.id
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
            self._wire_connections(cmmc_2_0_framework, default_org, objectives_list)

        self.db.commit()

        logger.info(f"Created CMMC 2.0 framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": cmmc_2_0_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _wire_connections(self, framework, org, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to CMMC 2.0 objectives using the CMMC_2_0_CONNECTIONS mapping.
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
            logger.warning("Missing lookup defaults - skipping CMMC 2.0 connection wiring")
            return

        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in CMMC_2_0_CONNECTIONS.values():
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

        logger.info(f"CMMC 2.0 wiring: {len(risk_name_to_id)} risks ready")

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

        logger.info(f"CMMC 2.0 wiring: {len(control_code_to_id)} controls ready")

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
                        logger.warning(f"CMMC 2.0 wiring: docx conversion failed for {policy_code}: {conv_err}")
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

        logger.info(f"CMMC 2.0 wiring: {len(policy_code_to_id)} policies ready")

        obj_title_to_id = {obj.title: obj.id for obj in objectives_list}
        policy_framework_pairs = set()

        obj_risk_count = 0
        obj_ctrl_count = 0
        pol_obj_count = 0
        ctrl_risk_count = 0
        ctrl_pol_count = 0
        planned_control_risk_pairs = set()
        planned_control_policy_pairs = set()

        for obj_title, conn in CMMC_2_0_CONNECTIONS.items():
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
            f"CMMC 2.0 wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return ['Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that conform to the principle of '
         "'least privilege?'.",
         'Q-IAC-15: Does the organization proactively govern account management of individual, group, system, application, '
         'guest and temporary accounts?.',
         'Q-DCH-13: Does the organization govern how external parties, systems and services are used to securely store, '
         'process and transmit data? .',
         'Q-DCH-15: Does the organization control publicly-accessible content?.',
         'Q-NET-04: Does the organization design, implement and review firewall and router configurations to restrict '
         'connections between untrusted networks and internal systems? .',
         'Q-HRS-11: Does the organization implement and maintain Separation of Duties (SoD) to prevent potential inappropriate '
         'activity without collusion?.',
         'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only authorized access to processes '
         'necessary to accomplish assigned tasks in accordance with organizational business functions? .',
         'Q-IAC-21.2: Does the organization prohibit privileged users from using privileged accounts, while performing '
         'non-security functions? .',
         'Q-IAC-21.5: Does the organization prevent non-privileged users from executing privileged functions to include '
         'disabling, circumventing or altering implemented security safeguards / countermeasures? .',
         'Q-IAC-22: Does the organization enforce a limit for consecutive invalid login attempts by a user during an '
         'organization-defined time period and automatically locks the account when the maximum number of unsuccessful '
         'attempts is exceeded?.',
         'Q-SEA-18: Does the organization utilize system use notification / logon banners that display an approved system use '
         'notification message or banner before granting access to the system that provides privacy and security notices?.',
         'Q-IAC-24: Does the organization initiate a session lock after an organization-defined time period of inactivity, or '
         'upon receiving a request from a user and retain the session lock until the user reestablishes access using '
         'established identification and authentication methods?.',
         'Q-IAC-25: Does the organization use automated mechanisms to log out users, both locally on the network and for '
         'remote sessions, at the end of the session or after an organization-defined period of inactivity? .',
         'Q-NET-14.1: Does the organization use automated mechanisms to monitor and control remote access sessions? .',
         'Q-NET-14.2: Does the organization cryptographically protect the confidentiality and integrity of remote access '
         'sessions (e.g., VPN)?.',
         'Q-NET-14.3: Does the organization route all remote accesses through managed network access control points (e.g., VPN '
         'concentrator)?.',
         'Q-NET-14.4: Does the organization restrict the execution of privileged commands and access to security-relevant '
         'information via remote access only for compelling operational needs? .',
         'Q-NET-15: Does the organization control authorized wireless usage and monitor for unauthorized wireless access?.',
         'Q-NET-15.1: Does the organization implement authentication and cryptographic mechanisms used to protect wireless '
         'access?.',
         'Q-MDM-02: Does the organization implement  ensure strong access control mechanisms for mobile devices enforce '
         'requirements for the connection of mobile devices to organizational systems?.',
         'Q-MDM-03: Does the organization use cryptographic mechanisms to protect the confidentiality and integrity of '
         'information on mobile devices through full-device or container encryption?.',
         'Q-DCH-13.2: Does the organization restrict or prohibit the use of portable storage devices by users on external '
         'systems? .',
         'Q-SAT-02: Does the organization provide all employees and contractors appropriate awareness education and training '
         'that is relevant for their job function? .',
         'Q-THR-05: Does the organization utilize security awareness training on recognizing and reporting potential '
         'indicators of insider threat?.',
         'Q-MON-10: Does the organization retain event logs for a time period consistent with records retention requirements '
         'to provide support for after-the-fact investigations of security incidents and to meet statutory, regulatory and '
         'contractual retention requirements? .',
         'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate incidents in accordance with '
         'established timelines and procedures?.',
         'Q-MON-05: Does the organization alert appropriate personnel in the event of a log processing failure and take '
         'actions to remedy the disruption?.',
         'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across the enterprise by a '
         'Security Incident Event Manager (SIEM) or similar automated tool, to maintain situational awareness?.',
         'Q-MON-06: Does the organization provide an event log report generation capability to aid in detecting and assessing '
         'anomalous activities? .',
         'Q-MON-07.1: Does the organization synchronize internal system clocks with an authoritative time source? .',
         'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized access, modification and '
         'deletion?.',
         'Q-MON-08.2: Does the organization restrict access to the management of event logs to privileged users with a '
         'specific business need?.',
         'Q-CFG-02: Does the organization develop, document and maintain secure baseline configurations for technology '
         'platform that are consistent with industry-accepted system hardening standards? .',
         'Q-CHG-02: Does the organization govern the technical configuration change control processes?.',
         'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, prior to the implementation '
         'of the change?.',
         'Q-CHG-04: Does the organization enforce configuration restrictions in an effort to restrict the ability of users to '
         'conduct unauthorized changes?.',
         'Q-CFG-03: Does the organization configure systems to provide only essential capabilities by specifically prohibiting '
         'or restricting the use of ports, protocols, and/or services? .',
         'Q-CFG-03.1: Does the organization periodically review system configurations to identify and disable unnecessary '
         'and/or non-secure functions, ports, protocols and services?.',
         'Q-CFG-03.3: Does the organization whitelist or blacklist applications in an order to limit what is authorized to '
         'execute on systems?.',
         'Q-CFG-05: Does the organization restrict the ability of non-privileged users to install unauthorized software?.',
         'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users and processes acting on '
         'behalf of organizational users? .',
         'Q-IAC-06.3: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate local access for '
         'privileged accounts? .',
         'Q-IAC-06.2: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate network access for '
         'non-privileged accounts? .',
         'Q-IAC-06.1: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate network access for '
         'privileged accounts? .',
         'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access? .',
         'Q-IAC-02.2: Does the organization employ replay-resistant network access authentication?.',
         'Q-IAC-09: Does the organization govern naming standards for usernames and systems?.',
         'Q-IAC-15.3: Does the organization use automated mechanisms to disable inactive accounts after an '
         'organization-defined time period? .',
         'Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations to ensure strong criteria '
         'for password-based authentication?.',
         'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
         'Q-IAC-10.5: Does the organization protect authenticators commensurate with the sensitivity of the information to '
         'which use of the authenticator permits access? .',
         'Q-IAC-11: Does the organization obscure the feedback of authentication information during the authentication process '
         'to protect the information from possible exploitation/use by unauthorized individuals? .',
         "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, "
         'containment, eradication and recovery?.',
         'Q-IRO-06: Does the organization formally test incident response capabilities through realistic exercises to '
         'determine the operational effectiveness of those capabilities?.',
         'Q-MNT-02: Does the organization conduct controlled maintenance activities throughout the lifecycle of the system, '
         'application or service?.',
         'Q-MNT-04: Does the organization control and monitor the use of system maintenance tools? .',
         'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity commensurate with the '
         'classification or sensitivity of the information prior to disposal, release out of organizational control or release '
         'for reuse?.',
         'Q-MNT-04.2: Does the organization check media containing diagnostic and test programs for malicious code before the '
         'media are used? .',
         'Q-MNT-05: Does the organization authorize, monitor and control remote, non-local maintenance and diagnostic '
         'activities?.',
         'Q-MNT-06: Does the organization maintain a current list of authorized maintenance organizations or personnel?.',
         'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? .',
         'Q-DCH-03: Does the organization control and restrict access to digital and non-digital media to authorized '
         'individuals? .',
         'Q-DCH-04: Does the organization mark media in accordance with data protection requirements so that personnel are '
         'alerted to distribution limitations, handling caveats and applicable security requirements? .',
         'Q-DCH-07: Does the organization protect and control digital and non-digital media during transport outside of '
         'controlled areas using appropriate security measures?.',
         'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent unauthorized disclosure of data '
         'at rest? .',
         'Q-DCH-10: Does the organization restrict the use of types of digital media on systems or system components? .',
         'Q-DCH-10.2: Does the organization prohibit the use of portable storage devices in organizational information systems '
         'when such devices have no identifiable owner?.',
         'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized disclosure and/or '
         'modification of backup information/.',
         'Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify '
         'the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) '
         'and Recovery Point Objectives (RPOs)?.',
         'Q-HRS-04: Does the organization manage personnel security risk by screening individuals prior to authorizing '
         'access?.',
         'Q-HRS-09: Does the organization govern the termination of individual employment?.',
         'Q-HRS-08: Does the organization adjust logical and physical access authorizations to systems and facilities upon '
         'personnel reassignment or transfer, in a timely manner?.',
         'Q-PES-02: Does the organization maintain a current list of personnel with authorized access to organizational '
         'facilities (except for those areas within the facility officially designated as publicly accessible)?.',
         'Q-PES-06.3: Does the organization restrict unescorted access to facilities to personnel with required security '
         'clearances, formal access authorizations and validated the need for access? .',
         'Q-PES-06: Does the organization identify, authorize and monitor visitors before allowing access to the facility '
         '(other than areas designated as publicly accessible)? .',
         'Q-PES-03.3: Does the organization generate a log entry for each access through controlled ingress and egress '
         'points?.',
         'Q-PES-03: Does the organization enforce physical access authorizations for all physical access points (including '
         'designated entry/exit points) to facilities (excluding those areas within the facility officially designated as '
         'publicly accessible)?.',
         'Q-PES-01: Does the organization facilitate the operation of physical and environmental protection controls? .',
         'Q-PES-11: Does the organization utilize appropriate management, operational and technical controls at alternate work '
         'sites?.',
         'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the likelihood and magnitude of '
         "harm, from unauthorized access, use, disclosure, disruption, modification or destruction of the organization's "
         'systems and data?.',
         'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by recurring vulnerability scanning '
         'of systems and web applications?.',
         'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
         'Q-CPL-02: Does the organization provide a security & privacy controls oversight function that reports to the '
         "organization's executive leadership?.",
         'Q-IAO-05: Does the organization use a Plan of Action and Milestones (POA&M), or similar mechanisms, to document '
         'planned remedial actions to correct weaknesses or deficiencies noted during the assessment of the security controls '
         'and to reduce or eliminate known vulnerabilities?.',
         'Q-AST-04.1: Does the organization determine cybersecurity and privacy control applicability by identifying, '
         'assigning and documenting the appropriate asset scope categorization for all systems, applications, services and '
         'personnel (internal and third-parties)?.',
         'Q-IAO-03: Does the organization generate System Security & Privacy Plans (SSPPs), or similar document repositories, '
         'to identify and maintain key architectural information on each critical system, application or service, as well as '
         'influencing inputs, entities, systems, applications and processes, providing a historical record of the data and its '
         'origins?.',
         'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to monitor and control '
         'communications at the external network boundary and at key internal boundaries within the network?.',
         'Q-NET-06: Does the organization logically or physically segment information flows to accomplish network '
         'segmentation?.',
         'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized cybersecurity and privacy '
         'practices in the specification, design, development, implementation and modification of systems and services?.',
         'Q-CLD-03: Does the organization host security-specific technologies in a dedicated subnet?.',
         'Q-SEA-03.2: Does the organization separate user functionality (including user interface services) from system '
         'management functionality? .',
         'Q-SEA-05: Does the organization prevent unauthorized and unintended information transfer via shared system '
         'resources? .',
         'Q-NET-04.1: Does the organization configure firewall and router configurations to deny network traffic by default '
         'and allow network traffic by exception (e.g., deny all, permit by exception)? .',
         'Q-CFG-03.4: Does the organization prevent systems from creating split tunneling connections or similar techniques '
         'that could be used to exfiltrate data?.',
         'Q-CRY-01.1: Does the organization use cryptographic mechanisms to prevent unauthorized disclosure of information as '
         'an alternate to physical safeguards? .',
         'Q-NET-07: Does the organization terminate remote sessions at the end of the session or after an organization-defined '
         'time period of inactivity? .',
         'Q-CRY-08: Does the organization securely implement an internal Public Key Infrastructure (PKI) infrastructure or '
         'obtain PKI services from a reputable PKI service provider?.',
         'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known '
         'public standards and trusted cryptographic technologies?.',
         'Q-END-10: Does the organization address mobile code / operating system-independent applications? .',
         'Q-NET-13: Does the organization protect the confidentiality, integrity and availability of electronic messaging '
         'communications?.',
         'Q-NET-09: Does the organization protect the authenticity and integrity of communications sessions? .',
         'Q-END-02: Does the organization protect the confidentiality, integrity, availability and safety of endpoint '
         'devices?.',
         'Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.',
         'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate malicious code?.',
         'Q-END-04.1: Does the organization automatically update antimalware technologies, including signature definitions? .',
         'Q-END-04.7: Does the organization ensure that anti-malware technologies are continuously running and cannot be '
         'disabled or altered by non-privileged users, unless specifically authorized by management on a case-by-case basis '
         'for a limited time period? .',
         'Q-MON-01.3: Does the organization continuously monitor inbound and outbound communications traffic for unusual or '
         'unauthorized activities or conditions?.']

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that '
                                   "conform to the principle of 'least privilege?'."],
          'objective_title': 'AC.L1-3.1.1: Authorized Access Control',
          'requirement_description': 'Limit information system access to authorized users, processes acting on behalf of '
                                     'authorized users, or devices (including other information systems).\n'
                                     '-  FAR Clause 52.204-21 b.1.i\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.1',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-15: Does the organization proactively govern account management of individual, '
                                   'group, system, application, guest and temporary accounts?.'],
          'objective_title': 'AC.L1-3.1.2: Transaction & Function Control',
          'requirement_description': 'Limit information system access to the types of transactions and functions that '
                                     'authorized users are permitted to execute. \n'
                                     '-  FAR Clause 52.204-21 b.1.ii\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.2',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-DCH-13: Does the organization govern how external parties, systems and services are used '
                                   'to securely store, process and transmit data? .'],
          'objective_title': 'AC.L1-3.1.20: External Connections',
          'requirement_description': 'Verify and control/limit connections to and use of external information systems. \n'
                                     '-  FAR Clause 52.204-21 b.1.iii\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.20',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-DCH-15: Does the organization control publicly-accessible content?.'],
          'objective_title': 'AC.L1-3.1.22: Control Public Information',
          'requirement_description': 'Control information posted or processed on publicly accessible information systems.\n'
                                     '-  FAR Clause 52.204-21 b.1.iv\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.22',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-NET-04: Does the organization design, implement and review firewall and router '
                                   'configurations to restrict connections between untrusted networks and internal systems? .'],
          'objective_title': 'AC.L2-3.1.3: Control CUI Flow',
          'requirement_description': 'Control the flow of CUI in accordance with approved authorizations. \n'
                                     '-  NIST SP 800-171 Rev 2 3.1.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-HRS-11: Does the organization implement and maintain Separation of Duties (SoD) to '
                                   'prevent potential inappropriate activity without collusion?.'],
          'objective_title': 'AC.L2-3.1.4: Separation of Duties',
          'requirement_description': 'Separate the duties of individuals to reduce the risk of malevolent activity without '
                                     'collusion.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .'],
          'objective_title': 'AC.L2-3.1.5: Least Privilege',
          'requirement_description': 'Employ the principle of least privilege, including for specific security functions and '
                                     'privileged accounts.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.5',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-21.2: Does the organization prohibit privileged users from using privileged '
                                   'accounts, while performing non-security functions? .'],
          'objective_title': 'AC.L2-3.1.6: Non-Privileged Account Use',
          'requirement_description': 'Use non-privileged accounts or roles when accessing nonsecurity functions.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-21.5: Does the organization prevent non-privileged users from executing privileged '
                                   'functions to include disabling, circumventing or altering implemented security safeguards '
                                   '/ countermeasures? .'],
          'objective_title': 'AC.L2-3.1.7: Privileged Functions',
          'requirement_description': 'Prevent non-privileged users from executing privileged functions and capture the '
                                     'execution of such functions in audit logs.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.7',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-22: Does the organization enforce a limit for consecutive invalid login attempts by '
                                   'a user during an organization-defined time period and automatically locks the account when '
                                   'the maximum number of unsuccessful attempts is exceeded?.'],
          'objective_title': 'AC.L2-3.1.8: Unsuccessful Logon Attempts',
          'requirement_description': 'Limit unsuccessful logon attempts. \n-  NIST SP 800-171 Rev 2 3.1.8 ',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-SEA-18: Does the organization utilize system use notification / logon banners that '
                                   'display an approved system use notification message or banner before granting access to '
                                   'the system that provides privacy and security notices?.'],
          'objective_title': 'AC.L2-3.1.9: Privacy & Security Notices',
          'requirement_description': 'Provide privacy and security notices consistent with applicable CUI rules.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.9',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-24: Does the organization initiate a session lock after an organization-defined time '
                                   'period of inactivity, or upon receiving a request from a user and retain the session lock '
                                   'until the user reestablishes access using established identification and authentication '
                                   'methods?.'],
          'objective_title': 'AC.L2-3.1.10: Session Lock',
          'requirement_description': 'Use session lock with pattern-hiding displays to prevent access and viewing of data '
                                     'after a period of inactivity. \n'
                                     '-  NIST SP 800-171 Rev 2 3.1.10',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-IAC-25: Does the organization use automated mechanisms to log out users, both locally on '
                                   'the network and for remote sessions, at the end of the session or after an '
                                   'organization-defined period of inactivity? .'],
          'objective_title': 'AC.L2-3.1.11: Session Termination',
          'requirement_description': 'Terminate (automatically) a user session after a defined condition.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.11',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-NET-14.1: Does the organization use automated mechanisms to monitor and control remote '
                                   'access sessions? .'],
          'objective_title': 'AC.L2-3.1.12: Control Remote Access',
          'requirement_description': 'Monitor and control remote access sessions.\n-  NIST SP 800-171 Rev 2 3.1.12',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-NET-14.2: Does the organization cryptographically protect the confidentiality and '
                                   'integrity of remote access sessions (e.g., VPN)?.'],
          'objective_title': 'AC.L2-3.1.13: Remote Access Confidentiality',
          'requirement_description': 'Employ cryptographic mechanisms to protect the confidentiality of remote access '
                                     'sessions.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.13',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-NET-14.3: Does the organization route all remote accesses through managed network access '
                                   'control points (e.g., VPN concentrator)?.'],
          'objective_title': 'AC.L2-3.1.14: Remote Access Routing',
          'requirement_description': 'Route remote access via managed access control points. \n-  NIST SP 800-171 Rev 2 3.1.14',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-NET-14.4: Does the organization restrict the execution of privileged commands and access '
                                   'to security-relevant information via remote access only for compelling operational needs? '
                                   '.'],
          'objective_title': 'AC.L2-3.1.15: Privileged Remote Access',
          'requirement_description': 'Authorize remote execution of privileged commands and remote access to security-relevant '
                                     'information. \n'
                                     '-  NIST SP 800-171 Rev 2 3.1.15',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-NET-15: Does the organization control authorized wireless usage and monitor for '
                                   'unauthorized wireless access?.'],
          'objective_title': 'AC.L2-3.1.16: Wireless Access Authorization',
          'requirement_description': 'Authorize wireless access prior to allowing such connections.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.16',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-NET-15.1: Does the organization implement authentication and cryptographic mechanisms '
                                   'used to protect wireless access?.'],
          'objective_title': 'AC.L2-3.1.17: Wireless Access Protection',
          'requirement_description': 'Protect wireless access using authentication and encryption. \n'
                                     '-  NIST SP 800-171 Rev 2 3.1.17',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-MDM-02: Does the organization implement  ensure strong access control mechanisms for '
                                   'mobile devices enforce requirements for the connection of mobile devices to organizational '
                                   'systems?.'],
          'objective_title': 'AC.L2-3.1.18: Mobile Device Connection',
          'requirement_description': 'Control connection of mobile devices.\n-  NIST SP 800-171 Rev 2 3.1.18',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-MDM-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality and integrity of information on mobile devices through full-device or '
                                   'container encryption?.'],
          'objective_title': 'AC.L2-3.1.19: Encrypt CUI on Mobile',
          'requirement_description': 'Encrypt CUI on mobile devices and mobile computing platforms. \n'
                                     '-  NIST SP 800-171 Rev 2 3.1.19',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AC: ACCESS CONTROL',
          'conformity_questions': ['Q-DCH-13.2: Does the organization restrict or prohibit the use of portable storage devices '
                                   'by users on external systems? .'],
          'objective_title': 'AC.L2-3.1.21: Portable Storage Use',
          'requirement_description': 'Limit use of portable storage devices on external systems.\n'
                                     '-  NIST SP 800-171 Rev 2 3.1.21',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AT: AWARENESS AND TRAINING',
          'conformity_questions': ['Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .'],
          'objective_title': 'AT.L2-3.2.1: Role-Based Risk Awareness',
          'requirement_description': 'Ensure that managers, systems administrators, and users of organizational systems are '
                                     'made aware of the security risks associated with their activities and of the applicable '
                                     'policies, standards, and procedures related to the security of those systems.\n'
                                     '-  NIST SP 800-171 Rev 2 3.2.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AT: AWARENESS AND TRAINING',
          'conformity_questions': [],
          'objective_title': 'AT.L2-3.2.2: Role-Based Training',
          'requirement_description': 'Ensure that personnel are trained to carry out their assigned information '
                                     'security-related duties and responsibilities. \n'
                                     '-  NIST SP 800-171 Rev 2 3.2.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AT: AWARENESS AND TRAINING',
          'conformity_questions': ['Q-THR-05: Does the organization utilize security awareness training on recognizing and '
                                   'reporting potential indicators of insider threat?.'],
          'objective_title': 'AT.L2-3.2.3: Insider Threat Awareness',
          'requirement_description': 'Provide security awareness training on recognizing and reporting potential indicators of '
                                     'insider threat.\n'
                                     '-  NIST SP 800-171 Rev 2 3.2.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-10: Does the organization retain event logs for a time period consistent with '
                                   'records retention requirements to provide support for after-the-fact investigations of '
                                   'security incidents and to meet statutory, regulatory and contractual retention '
                                   'requirements? .'],
          'objective_title': 'AU.L2-3.3.1: System Auditing',
          'requirement_description': 'Create and retain system audit logs and records to the extent needed to enable the '
                                     'monitoring, analysis, investigation, and reporting of unlawful or unauthorized system '
                                     'activity. \n'
                                     '-  NIST SP 800-171 Rev 2 3.3.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': [],
          'objective_title': 'AU.L2-3.3.2: User Accountability',
          'requirement_description': 'Ensure that the actions of individual system users can be uniquely traced to those '
                                     'users, so they can be held accountable for their actions.\n'
                                     '-  NIST SP 800-171 Rev 2 3.3.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.'],
          'objective_title': 'AU.L2-3.3.3: Event Review',
          'requirement_description': 'Review and update logged events.\n-  NIST SP 800-171 Rev 2 3.3.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-05: Does the organization alert appropriate personnel in the event of a log '
                                   'processing failure and take actions to remedy the disruption?.'],
          'objective_title': 'AU.L2-3.3.4: Audit Failure Alerting',
          'requirement_description': 'Alert in the event of an audit logging process failure. \n-  NIST SP 800-171 Rev 2 3.3.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.'],
          'objective_title': 'AU.L2-3.3.5: Audit Correlation',
          'requirement_description': 'Correlate audit record review, analysis, and reporting processes for investigation and '
                                     'response to indications of unlawful, unauthorized, suspicious, or unusual activity.\n'
                                     '-  NIST SP 800-171 Rev 2 3.3.5',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-06: Does the organization provide an event log report generation capability to aid '
                                   'in detecting and assessing anomalous activities? .'],
          'objective_title': 'AU.L2-3.3.6: Reduction & Reporting',
          'requirement_description': 'Provide audit record reduction and report generation to support on-demand analysis and '
                                     'reporting.\n'
                                     '-  NIST SP 800-171 Rev 2 3.3.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-07.1: Does the organization synchronize internal system clocks with an authoritative '
                                   'time source? .'],
          'objective_title': 'AU.L2-3.3.7: Authoritative Time Source',
          'requirement_description': 'Provide a system capability that compares and synchronizes internal system clocks with '
                                     'an authoritative source to generate time stamps for audit records.\n'
                                     '-  NIST SP 800-171 Rev 2 3.3.7',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-08: Does the organization protect event logs and audit tools from unauthorized '
                                   'access, modification and deletion?.'],
          'objective_title': 'AU.L2-3.3.8: Audit Protection',
          'requirement_description': 'Protect audit information and audit logging tools from unauthorized access, '
                                     'modification, and deletion.\n'
                                     '-  NIST SP 800-171 Rev 2 3.3.8',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'AU: AUDIT AND ACCOUNTABILITY',
          'conformity_questions': ['Q-MON-08.2: Does the organization restrict access to the management of event logs to '
                                   'privileged users with a specific business need?.'],
          'objective_title': 'AU.L2-3.3.9: Audit Management',
          'requirement_description': 'Limit management of audit logging functionality to a subset of privileged users. \n'
                                     '-  NIST SP 800-171 Rev 2 3.3.9',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': [],
          'objective_title': 'CM.L2-3.4.1: System Baselining',
          'requirement_description': 'Establish and maintain baseline configurations and inventories of organizational systems '
                                     '(including hardware, software, firmware, and documentation) throughout the respective '
                                     'system development life cycles.\n'
                                     '-  NIST SP 800-171 Rev 2 3.4.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': 'CM.L2-3.4.2: Security Configuration Enforcement',
          'requirement_description': 'Establish and enforce security configuration settings for information technology '
                                     'products employed in organizational systems.\n'
                                     '-  NIST SP 800-171 Rev 2 3.4.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.'],
          'objective_title': 'CM.L2-3.4.3: System Change Management',
          'requirement_description': 'Track, review, approve or disapprove, and log changes to organizational systems. \n'
                                     '-  NIST SP 800-171 Rev 2 3.4.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, '
                                   'prior to the implementation of the change?.'],
          'objective_title': 'CM.L2-3.4.4: Security Impact Analysis',
          'requirement_description': 'Analyze the security impact of changes prior to implementation. \n'
                                     '-  NIST SP 800-171 Rev 2 3.4.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CHG-04: Does the organization enforce configuration restrictions in an effort to '
                                   'restrict the ability of users to conduct unauthorized changes?.'],
          'objective_title': 'CM.L2-3.4.5: Access Restrictions for Change',
          'requirement_description': 'Define, document, approve, and enforce physical and logical access restrictions '
                                     'associated with changes to organizational systems.\n'
                                     '-  NIST SP 800-171 Rev 2 3.4.5',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CFG-03: Does the organization configure systems to provide only essential capabilities '
                                   'by specifically prohibiting or restricting the use of ports, protocols, and/or services? '
                                   '.'],
          'objective_title': 'CM.L2-3.4.6: Least Functionality',
          'requirement_description': 'Employ the principle of least functionality by configuring organizational systems to '
                                     'provide only essential capabilities. \n'
                                     '-  NIST SP 800-171 Rev 2 3.4.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CFG-03.1: Does the organization periodically review system configurations to identify '
                                   'and disable unnecessary and/or non-secure functions, ports, protocols and services?.'],
          'objective_title': 'CM.L2-3.4.7: Nonessential Functionality',
          'requirement_description': 'Restrict, disable, or prevent the use of nonessential programs, functions, ports, '
                                     'protocols, and services. \n'
                                     '-  NIST SP 800-171 Rev 2 3.4.7',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CFG-03.3: Does the organization whitelist or blacklist applications in an order to limit '
                                   'what is authorized to execute on systems?.'],
          'objective_title': 'CM.L2-3.4.8: Application Execution Policy',
          'requirement_description': 'Apply deny-by-exception (blacklisting) policy to prevent the use of unauthorized '
                                     'software or deny-all, permit-by-exception (whitelisting) policy to allow the execution '
                                     'of authorized software. \n'
                                     '-  NIST SP 800-171 Rev 2 3.4.8',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CM: CONFIGURATION MANAGEMENT',
          'conformity_questions': ['Q-CFG-05: Does the organization restrict the ability of non-privileged users to install '
                                   'unauthorized software?.'],
          'objective_title': 'CM.L2-3.4.9: User-Installed Software',
          'requirement_description': 'Control and monitor user-installed software.\n-  NIST SP 800-171 Rev 2 3.4.9',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .'],
          'objective_title': 'IA.L1-3.5.1: Identification',
          'requirement_description': 'Identify information system users, processes acting on behalf of users, or devices.\n'
                                     '-  FAR Clause 52.204-21 b.1.v\n'
                                     '-  NIST SP 800-171 Rev 2 3.5.1',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .'],
          'objective_title': 'IA.L1-3.5.2: Authentication',
          'requirement_description': 'Authenticate (or verify) the identities of those users, processes, or devices, as a '
                                     'prerequisite to allowing access to organizational information systems.\n'
                                     '-  FAR Clause 52.204-21 b.1.vi\n'
                                     '-  NIST SP 800-171 Rev 2 3.5.2',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-06.3: Does the organization utilize Multi-Factor Authentication (MFA) to '
                                   'authenticate local access for privileged accounts? .',
                                   'Q-IAC-06.2: Does the organization utilize Multi-Factor Authentication (MFA) to '
                                   'authenticate network access for non-privileged accounts? .',
                                   'Q-IAC-06.1: Does the organization utilize Multi-Factor Authentication (MFA) to '
                                   'authenticate network access for privileged accounts? .',
                                   'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote '
                                   'network access? .'],
          'objective_title': 'IA.L2-3.5.3: Multifactor Authentication',
          'requirement_description': 'Use multifactor authentication for local and network access to privileged accounts and '
                                     'for network access to non-privileged accounts. \n'
                                     '-  NIST SP 800-171 Rev 2 3.5.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-02.2: Does the organization employ replay-resistant network access authentication?.'],
          'objective_title': 'IA.L2-3.5.4: Replay-Resistant Authentication',
          'requirement_description': 'Employ replay-resistant authentication mechanisms for network access to privileged and '
                                     'non-privileged accounts.\n'
                                     '-  NIST SP 800-171 Rev 2 3.5.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-09: Does the organization govern naming standards for usernames and systems?.'],
          'objective_title': 'IA.L2-3.5.5: Identifier Reuse',
          'requirement_description': 'Prevent reuse of identifiers for a defined period. \n-  NIST SP 800-171 Rev 2 3.5.5',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-15.3: Does the organization use automated mechanisms to disable inactive accounts '
                                   'after an organization-defined time period? .'],
          'objective_title': 'IA.L2-3.5.6: Identifier Handling',
          'requirement_description': 'Disable identifiers after a defined period of inactivity. \n'
                                     '-  NIST SP 800-171 Rev 2 3.5.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.'],
          'objective_title': 'IA.L2-3.5.7: Password Complexity',
          'requirement_description': 'Enforce a minimum password complexity and change of characters when new passwords are '
                                     'created.\n'
                                     '-  NIST SP 800-171 Rev 2 3.5.7',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-10: Does the organization securely manage authenticators for users and devices?.'],
          'objective_title': 'IA.L2-3.5.8: Password Reuse',
          'requirement_description': 'Prohibit password reuse for a specified number of generations.\n'
                                     '-  NIST SP 800-171 Rev 2 3.5.8',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-10: Does the organization securely manage authenticators for users and devices?.'],
          'objective_title': 'IA.L2-3.5.9: Temporary Passwords',
          'requirement_description': 'Allow temporary password use for system logons with an immediate change to a permanent '
                                     'password. \n'
                                     '-  NIST SP 800-171 Rev 2 3.5.9',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-10.5: Does the organization protect authenticators commensurate with the sensitivity '
                                   'of the information to which use of the authenticator permits access? .'],
          'objective_title': 'IA.L2-3.5.10: Cryptographically-Protected Passwords',
          'requirement_description': 'Store and transmit only cryptographically-protected passwords. \n'
                                     '-  NIST SP 800-171 Rev 2 3.5.10',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IA: IDENTIFICATION AND AUTHENTICATION',
          'conformity_questions': ['Q-IAC-11: Does the organization obscure the feedback of authentication information during '
                                   'the authentication process to protect the information from possible exploitation/use by '
                                   'unauthorized individuals? .'],
          'objective_title': 'IA.L2-3.5.11: Obscure Feedback',
          'requirement_description': 'Obscure feedback of authentication information. \n-  NIST SP 800-171 Rev 2 3.5.11',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IR: INCIDENT RESPONSE',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'IR.L2-3.6.1: Incident Handling',
          'requirement_description': 'Establish an operational incident-handling capability for organizational systems that '
                                     'includes preparation, detection, analysis, containment, recovery, and user response '
                                     'activities.\n'
                                     '-  NIST SP 800-171 Rev 2 3.6.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IR: INCIDENT RESPONSE',
          'conformity_questions': ["Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.'],
          'objective_title': 'IR.L2-3.6.2: Incident Reporting',
          'requirement_description': 'Track, document, and report incidents to designated officials and/or authorities both '
                                     'internal and external to the organization.\n'
                                     '-  NIST SP 800-171 Rev 2 3.6.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'IR: INCIDENT RESPONSE',
          'conformity_questions': ['Q-IRO-06: Does the organization formally test incident response capabilities through '
                                   'realistic exercises to determine the operational effectiveness of those capabilities?.'],
          'objective_title': 'IR.L2-3.6.3: Incident Response Testing',
          'requirement_description': 'Test the organizational incident response capability.\n-  NIST SP 800-171 Rev 2 3.6.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MA: MAINTENANCE',
          'conformity_questions': ['Q-MNT-02: Does the organization conduct controlled maintenance activities throughout the '
                                   'lifecycle of the system, application or service?.'],
          'objective_title': 'MA.L2-3.7.1: Perform Maintenance',
          'requirement_description': 'Perform maintenance on organizational systems.\n-  NIST SP 800-171 Rev 2 3.7.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MA: MAINTENANCE',
          'conformity_questions': ['Q-MNT-04: Does the organization control and monitor the use of system maintenance tools? '
                                   '.'],
          'objective_title': 'MA.L2-3.7.2: System Maintenance Control',
          'requirement_description': 'Provide controls on the tools, techniques, mechanisms, and personnel used to conduct '
                                     'system maintenance.\n'
                                     '-  NIST SP 800-171 Rev 2 3.7.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MA: MAINTENANCE',
          'conformity_questions': ['Q-DCH-09: Does the organization sanitize digital media with the strength and integrity '
                                   'commensurate with the classification or sensitivity of the information prior to disposal, '
                                   'release out of organizational control or release for reuse?.'],
          'objective_title': 'MA.L2-3.7.3: Equipment Sanitization',
          'requirement_description': 'Ensure equipment removed for off-site maintenance is sanitized of any CUI. \n'
                                     '-  NIST SP 800-171 Rev 2 3.7.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MA: MAINTENANCE',
          'conformity_questions': ['Q-MNT-04.2: Does the organization check media containing diagnostic and test programs for '
                                   'malicious code before the media are used? .'],
          'objective_title': 'MA.L2-3.7.4: Media Inspection',
          'requirement_description': 'Check media containing diagnostic and test programs for malicious code before the media '
                                     'are used in organizational systems. \n'
                                     '-  NIST SP 800-171 Rev 2 3.7.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MA: MAINTENANCE',
          'conformity_questions': ['Q-MNT-05: Does the organization authorize, monitor and control remote, non-local '
                                   'maintenance and diagnostic activities?.'],
          'objective_title': 'MA.L2-3.7.5: Nonlocal Maintenance',
          'requirement_description': 'Require multifactor authentication to establish nonlocal maintenance sessions via '
                                     'external network connections and terminate such connections when nonlocal maintenance is '
                                     'complete.\n'
                                     '-  NIST SP 800-171 Rev 2 3.7.5',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MA: MAINTENANCE',
          'conformity_questions': ['Q-MNT-06: Does the organization maintain a current list of authorized maintenance '
                                   'organizations or personnel?.'],
          'objective_title': 'MA.L2-3.7.6: Maintenance Personnel',
          'requirement_description': 'Supervise the maintenance activities of maintenance personnel without required access '
                                     'authorization. \n'
                                     '-  NIST SP 800-171 Rev 2 3.7.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-DCH-09: Does the organization sanitize digital media with the strength and integrity '
                                   'commensurate with the classification or sensitivity of the information prior to disposal, '
                                   'release out of organizational control or release for reuse?.'],
          'objective_title': 'MP.L1-3.8.3: Media Disposal',
          'requirement_description': 'Sanitize or destroy information system media containing Federal Contract Information '
                                     'before disposal or release for reuse.\n'
                                     '-  FAR Clause 52.204-21 b.1.vii\n'
                                     '-  NIST SP 800-171 Rev 2 3.8.3',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.'],
          'objective_title': 'MP.L2-3.8.1: Media Protection',
          'requirement_description': 'Protect (i.e., physically control and securely store) system media containing CUI, both '
                                     'paper and digital. \n'
                                     '-  NIST SP 800-171 Rev 2 3.8.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-DCH-03: Does the organization control and restrict access to digital and non-digital '
                                   'media to authorized individuals? .'],
          'objective_title': 'MP.L2-3.8.2: Media Access',
          'requirement_description': 'Limit access to CUI on system media to authorized users.\n-  NIST SP 800-171 Rev 2 3.8.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-DCH-04: Does the organization mark media in accordance with data protection requirements '
                                   'so that personnel are alerted to distribution limitations, handling caveats and applicable '
                                   'security requirements? .'],
          'objective_title': 'MP.L2-3.8.4: Media Markings',
          'requirement_description': 'Mark media with necessary CUI markings and distribution limitations.\n'
                                     '-  NIST SP 800-171 Rev 2 3.8.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-DCH-07: Does the organization protect and control digital and non-digital media during '
                                   'transport outside of controlled areas using appropriate security measures?.'],
          'objective_title': 'MP.L2-3.8.5: Media Accountability',
          'requirement_description': 'Control access to media containing CUI and maintain accountability for media during '
                                     'transport outside of controlled areas. \n'
                                     '-  NIST SP 800-171 Rev 2 3.8.5',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .'],
          'objective_title': 'MP.L2-3.8.6: Portable Storage Encryption',
          'requirement_description': 'Implement cryptographic mechanisms to protect the confidentiality of CUI stored on '
                                     'digital media during transport unless otherwise protected by alternative physical '
                                     'safeguards. \n'
                                     '-  NIST SP 800-171 Rev 2 3.8.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-DCH-10: Does the organization restrict the use of types of digital media on systems or '
                                   'system components? .'],
          'objective_title': 'MP.L2-3.8.7: Removable Media',
          'requirement_description': 'Control the use of removable media on system components.\n-  NIST SP 800-171 Rev 2 3.8.7',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-DCH-10.2: Does the organization prohibit the use of portable storage devices in '
                                   'organizational information systems when such devices have no identifiable owner?.'],
          'objective_title': 'MP.L2-3.8.8: Shared Media',
          'requirement_description': 'Prohibit the use of portable storage devices when such devices have no identifiable '
                                     'owner.\n'
                                     '-  NIST SP 800-171 Rev 2 3.8.8',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'MP: MEDIA PROTECTION',
          'conformity_questions': ['Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized '
                                   'disclosure and/or modification of backup information/.',
                                   'Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.'],
          'objective_title': 'MP.L2-3.8.9: Protect Backups',
          'requirement_description': 'Protect the confidentiality of backup CUI at storage locations. \n'
                                     '-  NIST SP 800-171 Rev 2 3.8.9',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'PS: PERSONNEL SECURITY',
          'conformity_questions': ['Q-HRS-04: Does the organization manage personnel security risk by screening individuals '
                                   'prior to authorizing access?.'],
          'objective_title': 'PS.L2-3.9.1: Screen Individuals',
          'requirement_description': 'Screen individuals prior to authorizing access to organizational systems containing '
                                     'CUI.\n'
                                     '-  NIST SP 800-171 Rev 2 3.9.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'PS: PERSONNEL SECURITY',
          'conformity_questions': ['Q-HRS-09: Does the organization govern the termination of individual employment?.',
                                   'Q-HRS-08: Does the organization adjust logical and physical access authorizations to '
                                   'systems and facilities upon personnel reassignment or transfer, in a timely manner?.'],
          'objective_title': 'PS.L2-3.9.2: Personnel Actions',
          'requirement_description': 'Ensure that organizational systems containing CUI are protected during and after '
                                     'personnel actions such as terminations and transfers.\n'
                                     '-  NIST SP 800-171 Rev 2 3.9.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'PE: PHYSICAL PROTECTION',
          'conformity_questions': ['Q-PES-02: Does the organization maintain a current list of personnel with authorized '
                                   'access to organizational facilities (except for those areas within the facility officially '
                                   'designated as publicly accessible)?.'],
          'objective_title': 'PE.L1-3.10.1: Limit Physical Access',
          'requirement_description': 'Limit physical access to organizational information systems, equipment, and the '
                                     'respective operating environments to authorized individuals. \n'
                                     '-  FAR Clause 52.204-21 b.1.viii\n'
                                     '-  NIST SP 800-171 Rev 2 3.10.1',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'PE: PHYSICAL PROTECTION',
          'conformity_questions': ['Q-PES-06.3: Does the organization restrict unescorted access to facilities to personnel '
                                   'with required security clearances, formal access authorizations and validated the need for '
                                   'access? .',
                                   'Q-PES-06: Does the organization identify, authorize and monitor visitors before allowing '
                                   'access to the facility (other than areas designated as publicly accessible)? .'],
          'objective_title': 'PE.L1-3.10.3: Escort Visitors',
          'requirement_description': 'Escort visitors and monitor visitor activity. \n'
                                     '-  FAR Clause 52.204-21 Partial b.1.ix \n'
                                     '-  NIST SP 800-171 Rev 2 3.10.3',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'PE: PHYSICAL PROTECTION',
          'conformity_questions': ['Q-PES-03.3: Does the organization generate a log entry for each access through controlled '
                                   'ingress and egress points?.'],
          'objective_title': 'PE.L1-3.10.4: Physical Access Logs',
          'requirement_description': 'Maintain audit logs of physical access.\n'
                                     '-  FAR Clause 52.204-21 Partial b.1.ix \n'
                                     '-  NIST SP 800-171 Rev 2 3.10.4',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'PE: PHYSICAL PROTECTION',
          'conformity_questions': ['Q-PES-03: Does the organization enforce physical access authorizations for all physical '
                                   'access points (including designated entry/exit points) to facilities (excluding those '
                                   'areas within the facility officially designated as publicly accessible)?.'],
          'objective_title': 'PE.L1-3.10.5: Manage Physical Access',
          'requirement_description': 'Control and manage physical access devices.\n'
                                     '-  FAR Clause 52.204-21 Partial b.1.ix \n'
                                     '-  NIST SP 800-171 Rev 2 3.10.5',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'PE: PHYSICAL PROTECTION',
          'conformity_questions': ['Q-PES-01: Does the organization facilitate the operation of physical and environmental '
                                   'protection controls? .'],
          'objective_title': 'PE.L2-3.10.2: Monitor Facility',
          'requirement_description': 'Protect and monitor the physical facility and support infrastructure for organizational '
                                     'systems.\n'
                                     '-  NIST SP 800-171 Rev 2 3.10.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'PE: PHYSICAL PROTECTION',
          'conformity_questions': ['Q-PES-11: Does the organization utilize appropriate management, operational and technical '
                                   'controls at alternate work sites?.'],
          'objective_title': 'PE.L2-3.10.6: Alternative Work Sites',
          'requirement_description': 'Enforce safeguarding measures for CUI at alternate work sites.\n'
                                     '-  NIST SP 800-171 Rev 2 3.10.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'RA: RISK ASSESSMENT',
          'conformity_questions': ['Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?."],
          'objective_title': 'RA.L2-3.11.1: Risk Assessments',
          'requirement_description': 'Periodically assess the risk to organizational operations (including mission, functions, '
                                     'image, or reputation), organizational assets, and individuals, resulting from the '
                                     'operation of organizational systems and the associated processing, storage, or '
                                     'transmission of CUI.\n'
                                     '-  NIST SP 800-171 Rev 2 3.11.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'RA: RISK ASSESSMENT',
          'conformity_questions': ['Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.'],
          'objective_title': 'RA.L2-3.11.2: Vulnerability Scan',
          'requirement_description': 'Scan for vulnerabilities in organizational systems and applications periodically and '
                                     'when new vulnerabilities affecting those systems and applications are identified. \n'
                                     '-  NIST SP 800-171 Rev 2 3.11.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'RA: RISK ASSESSMENT',
          'conformity_questions': ['Q-RSK-06: Does the organization remediate risks to an acceptable level? .'],
          'objective_title': 'RA.L2-3.11.3: Vulnerability Remediation',
          'requirement_description': 'Remediate vulnerabilities in accordance with risk assessments.\n'
                                     '-  NIST SP 800-171 Rev 2 3.11.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CA: SECURITY ASSESSMENT',
          'conformity_questions': ['Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?."],
          'objective_title': 'CA.L2-3.12.1: Security Control Assessment',
          'requirement_description': 'Periodically assess the security controls in organizational systems to determine if the '
                                     'controls are effective in their application. \n'
                                     '-  NIST SP 800-171 Rev 2 3.12.1',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CA: SECURITY ASSESSMENT',
          'conformity_questions': ['Q-IAO-05: Does the organization use a Plan of Action and Milestones (POA&M), or similar '
                                   'mechanisms, to document planned remedial actions to correct weaknesses or deficiencies '
                                   'noted during the assessment of the security controls and to reduce or eliminate known '
                                   'vulnerabilities?.'],
          'objective_title': 'CA.L2-3.12.2: Plan of Action',
          'requirement_description': 'Develop and implement plans of action designed to correct deficiencies and reduce or '
                                     'eliminate vulnerabilities in organizational systems.\n'
                                     '-  NIST SP 800-171 Rev 2 3.12.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CA: SECURITY ASSESSMENT',
          'conformity_questions': ['Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?.",
                                   'Q-AST-04.1: Does the organization determine cybersecurity and privacy control '
                                   'applicability by identifying, assigning and documenting the appropriate asset scope '
                                   'categorization for all systems, applications, services and personnel (internal and '
                                   'third-parties)?.'],
          'objective_title': 'CA.L2-3.12.3: Security Control Monitoring',
          'requirement_description': 'Monitor security controls on an ongoing basis to ensure the continued effectiveness of '
                                     'the controls. \n'
                                     '-  NIST SP 800-171 Rev 2 3.12.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'CA: SECURITY ASSESSMENT',
          'conformity_questions': ['Q-IAO-03: Does the organization generate System Security & Privacy Plans (SSPPs), or '
                                   'similar document repositories, to identify and maintain key architectural information on '
                                   'each critical system, application or service, as well as influencing inputs, entities, '
                                   'systems, applications and processes, providing a historical record of the data and its '
                                   'origins?.'],
          'objective_title': 'CA.L2-3.12.4: System Security Plan',
          'requirement_description': 'Develop, document, and periodically update system security plans that describe system '
                                     'boundaries, system environments of operation, how security requirements are implemented, '
                                     'and the relationships with or connections to other systems. \n'
                                     '-  NIST SP 800-171 Rev 2 3.12.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.'],
          'objective_title': 'SC.L1-3.13.1: Boundary Protection',
          'requirement_description': 'Monitor, control, and protect organizational communications (i.e., information '
                                     'transmitted or received by organizational information systems) at the external '
                                     'boundaries and key internal boundaries of the information systems.\n'
                                     '-  FAR Clause 52.204-21 b.1.x\n'
                                     '-  NIST SP 800-171 Rev 2 3.13.1',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.'],
          'objective_title': 'SC.L1-3.13.5: Public-Access System Separation',
          'requirement_description': 'Implement subnetworks for publicly accessible system components that are physically or '
                                     'logically separated from internal networks.\n'
                                     '-  FAR Clause 52.204-21 b.1.xi\n'
                                     '-  NIST SP 800-171 Rev 2 3.13.5',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.',
                                   'Q-CLD-03: Does the organization host security-specific technologies in a dedicated '
                                   'subnet?.'],
          'objective_title': 'SC.L2-3.13.2: Security Engineering',
          'requirement_description': 'Employ architectural designs, software development techniques, and systems engineering '
                                     'principles that promote effective information security within organizational systems.\n'
                                     '-  NIST SP 800-171 Rev 2 3.13.2',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-SEA-03.2: Does the organization separate user functionality (including user interface '
                                   'services) from system management functionality? .'],
          'objective_title': 'SC.L2-3.13.3: Role Separation',
          'requirement_description': 'Separate user functionality from system management functionality. \n'
                                     '-  NIST SP 800-171 Rev 2 3.13.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-SEA-05: Does the organization prevent unauthorized and unintended information transfer '
                                   'via shared system resources? .'],
          'objective_title': 'SC.L2-3.13.4: Shared Resource Control',
          'requirement_description': 'Prevent unauthorized and unintended information transfer via shared system resources. \n'
                                     '-  NIST SP 800-171 Rev 2 3.13.4',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-NET-04.1: Does the organization configure firewall and router configurations to deny '
                                   'network traffic by default and allow network traffic by exception (e.g., deny all, permit '
                                   'by exception)? .'],
          'objective_title': 'SC.L2-3.13.6: Network Communication by Exception',
          'requirement_description': 'Deny network communications traffic by default and allow network communications traffic '
                                     'by exception (i.e., deny all, permit by exception).\n'
                                     '-  NIST SP 800-171 Rev 2 3.13.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-CFG-03.4: Does the organization prevent systems from creating split tunneling '
                                   'connections or similar techniques that could be used to exfiltrate data?.'],
          'objective_title': 'SC.L2-3.13.7: Split Tunneling',
          'requirement_description': 'Prevent remote devices from simultaneously establishing non-remote connections with '
                                     'organizational systems and communicating via some other connection to resources in '
                                     'external networks (i.e., split tunneling). \n'
                                     '-  NIST SP 800-171 Rev 2 3.13.7',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-CRY-01.1: Does the organization use cryptographic mechanisms to prevent unauthorized '
                                   'disclosure of information as an alternate to physical safeguards? .'],
          'objective_title': 'SC.L2-3.13.8: Data in Transit',
          'requirement_description': 'Implement cryptographic mechanisms to prevent unauthorized disclosure of CUI during '
                                     'transmission unless otherwise protected by alternative physical safeguards.\n'
                                     '-  NIST SP 800-171 Rev 2 3.13.8',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-NET-07: Does the organization terminate remote sessions at the end of the session or '
                                   'after an organization-defined time period of inactivity? .'],
          'objective_title': 'SC.L2-3.13.9: Connections Termination',
          'requirement_description': 'Terminate network connections associated with communications sessions at the end of the '
                                     'sessions or after a defined period of inactivity. \n'
                                     '-  NIST SP 800-171 Rev 2 3.13.9',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-CRY-08: Does the organization securely implement an internal Public Key Infrastructure '
                                   '(PKI) infrastructure or obtain PKI services from a reputable PKI service provider?.'],
          'objective_title': 'SC.L2-3.13.10: Key Management',
          'requirement_description': 'Establish and manage cryptographic keys for cryptography employed in organizational '
                                     'systems. \n'
                                     '-  NIST SP 800-171 Rev 2 3.13.10',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.'],
          'objective_title': 'SC.L2-3.13.11: CUI Encryption',
          'requirement_description': 'Employ FIPS-validated cryptography when used to protect the confidentiality of CUI. \n'
                                     '-  NIST SP 800-171 Rev 2 3.13.11',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': [],
          'objective_title': 'SC.L2-3.13.12: Collaborative Device Control',
          'requirement_description': 'Prohibit remote activation of collaborative computing devices and provide indication of '
                                     'devices in use to users present at the device. \n'
                                     '-  NIST SP 800-171 Rev 2 3.13.12',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-END-10: Does the organization address mobile code / operating system-independent '
                                   'applications? .'],
          'objective_title': 'SC.L2-3.13.13: Mobile Code',
          'requirement_description': 'Control and monitor the use of mobile code. \n-  NIST SP 800-171 Rev 2 3.13.13',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-NET-13: Does the organization protect the confidentiality, integrity and availability of '
                                   'electronic messaging communications?.'],
          'objective_title': 'SC.L2-3.13.14: Voice over Internet Protocol',
          'requirement_description': 'Control and monitor the use of Voice over Internet Protocol (VoIP) technologies.\n'
                                     '-  NIST SP 800-171 Rev 2 3.13.14',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-NET-09: Does the organization protect the authenticity and integrity of communications '
                                   'sessions? .'],
          'objective_title': 'SC.L2-3.13.15: Communications Authenticity',
          'requirement_description': 'Protect the authenticity of communications sessions.\n-  NIST SP 800-171 Rev 2 3.13.15',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SC: SYSTEM AND COMMUNICATIONS PROTECTION',
          'conformity_questions': ['Q-END-02: Does the organization protect the confidentiality, integrity, availability and '
                                   'safety of endpoint devices?.'],
          'objective_title': 'SC.L2-3.13.16: Data at Rest',
          'requirement_description': 'Protect the confidentiality of CUI at rest.\n-  NIST SP 800-171 Rev 2 3.13.16',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SI: SYSTEM AND INFORMATION INTEGRITY',
          'conformity_questions': ['Q-VPM-01: Does the organization facilitate the implementation and monitoring of '
                                   'vulnerability management controls?.'],
          'objective_title': 'SI.L1-3.14.1: Flaw Remediation',
          'requirement_description': 'Identify, report, and correct information and information system flaws in a timely '
                                     'manner.\n'
                                     '-  FAR Clause 52.204-21 b.1.xii\n'
                                     '-  NIST SP 800-171 Rev 2 3.14.1',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'SI: SYSTEM AND INFORMATION INTEGRITY',
          'conformity_questions': ['Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': 'SI.L1-3.14.2: Malicious Code Protection',
          'requirement_description': 'Provide protection from malicious code at appropriate locations within organizational '
                                     'information systems.\n'
                                     '-  FAR Clause 52.204-21 b.1.xiii\n'
                                     '-  NIST SP 800-171 Rev 2 3.14.2',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'SI: SYSTEM AND INFORMATION INTEGRITY',
          'conformity_questions': ['Q-END-04.1: Does the organization automatically update antimalware technologies, including '
                                   'signature definitions? .'],
          'objective_title': 'SI.L1-3.14.4: Update Malicious Code Protection',
          'requirement_description': 'Update malicious code protection mechanisms when new releases are available.\n'
                                     '-  FAR Clause 52.204-21 b.1.xiv\n'
                                     '-  NIST SP 800-171 Rev 2 3.14.4',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'SI: SYSTEM AND INFORMATION INTEGRITY',
          'conformity_questions': ['Q-END-04.7: Does the organization ensure that anti-malware technologies are continuously '
                                   'running and cannot be disabled or altered by non-privileged users, unless specifically '
                                   'authorized by management on a case-by-case basis for a limited time period? .'],
          'objective_title': 'SI.L1-3.14.5: System & File Scanning',
          'requirement_description': 'Perform periodic scans of the information system and real-time scans of files from '
                                     'external sources as files are downloaded, opened, or executed.\n'
                                     '-  FAR Clause 52.204-21 b.1.xv\n'
                                     '-  NIST SP 800-171 Rev 2 3.14.5',
          'subchapter': 'L1: Level 1'},
         {'chapter_title': 'SI: SYSTEM AND INFORMATION INTEGRITY',
          'conformity_questions': ['Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.'],
          'objective_title': 'SI.L2-3.14.3: Security Alerts & Advisories',
          'requirement_description': 'Monitor system security alerts and advisories and take action in response.\n'
                                     '-  NIST SP 800-171 Rev 2 3.14.3',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SI: SYSTEM AND INFORMATION INTEGRITY',
          'conformity_questions': ['Q-MON-01.3: Does the organization continuously monitor inbound and outbound communications '
                                   'traffic for unusual or unauthorized activities or conditions?.'],
          'objective_title': 'SI.L2-3.14.6: Monitor Communications for Attacks',
          'requirement_description': 'Monitor organizational systems, including inbound and outbound communications traffic, '
                                     'to detect attacks and indicators of potential attacks.\n'
                                     '-  NIST SP 800-171 Rev 2 3.14.6',
          'subchapter': 'L2: Level 2'},
         {'chapter_title': 'SI: SYSTEM AND INFORMATION INTEGRITY',
          'conformity_questions': ['Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.'],
          'objective_title': 'SI.L2-3.14.7: Identify Unauthorized Use',
          'requirement_description': 'Identify unauthorized use of organizational systems. \n-  NIST SP 800-171 Rev 2 3.14.7',
          'subchapter': 'L2: Level 2'}]
