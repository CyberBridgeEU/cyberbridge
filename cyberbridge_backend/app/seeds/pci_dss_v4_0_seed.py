# app/seeds/pci_dss_v4_0_seed.py
import io
import logging
from .base_seed import BaseSeed
from app.models import models
from app.constants.pci_dss_v4_0_connections import PCI_DSS_V4_0_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class PciDssV40Seed(BaseSeed):
    """Seed PCI DSS v4.0 framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating PCI DSS v4.0 framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create PCI DSS v4.0 Framework
        pci_dss_v4_0_framework, created = self.get_or_create(
            models.Framework,
            {"name": "PCI DSS v4.0", "organisation_id": default_org.id},
            {
                "name": "PCI DSS v4.0",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("PCI DSS v4.0 framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == pci_dss_v4_0_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == pci_dss_v4_0_framework.id
            ).all()

            logger.info(f"Found existing PCI DSS v4.0 framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            # Keep links in sync even when framework/objectives already exist.
            if not self.skip_wire_connections:
                self._wire_connections(pci_dss_v4_0_framework, default_org, existing_objectives)
            self.db.commit()

            return {
                "framework": pci_dss_v4_0_framework,
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
                description="PCI DSS v4.0 conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=pci_dss_v4_0_framework.id,
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
                        "framework_id": pci_dss_v4_0_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": pci_dss_v4_0_framework.id
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
            self._wire_connections(pci_dss_v4_0_framework, default_org, objectives_list)

        self.db.commit()

        logger.info(f"Created PCI DSS v4.0 framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": pci_dss_v4_0_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _wire_connections(self, framework, org, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to PCI DSS v4.0 objectives using the PCI_DSS_V4_0_CONNECTIONS mapping.
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
            logger.warning("Missing lookup defaults - skipping PCI DSS v4.0 connection wiring")
            return

        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in PCI_DSS_V4_0_CONNECTIONS.values():
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

        logger.info(f"PCI DSS v4.0 wiring: {len(risk_name_to_id)} risks ready")

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

        logger.info(f"PCI DSS v4.0 wiring: {len(control_code_to_id)} controls ready")

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
                        logger.warning(f"PCI DSS v4.0 wiring: docx conversion failed for {policy_code}: {conv_err}")
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

        logger.info(f"PCI DSS v4.0 wiring: {len(policy_code_to_id)} policies ready")

        obj_title_to_id = {obj.title: obj.id for obj in objectives_list}
        policy_framework_pairs = set()

        obj_risk_count = 0
        obj_ctrl_count = 0
        pol_obj_count = 0
        ctrl_risk_count = 0
        ctrl_pol_count = 0
        planned_control_risk_pairs = set()
        planned_control_policy_pairs = set()

        for obj_title, conn in PCI_DSS_V4_0_CONNECTIONS.items():
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
            f"PCI DSS v4.0 wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar mechanisms, to identify '
         'and document day-to-day procedures to enable the proper execution of assigned tasks?.',
         'Q-OPS-01: Does the organization facilitate the implementation of operational security controls?.',
         'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and procedures at planned '
         'intervals or if significant changes occur to ensure their continuing suitability, adequacy and effectiveness? .',
         'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and privacy policies, standards '
         'and procedures?.',
         'Q-HRS-03.1: Does the organization communicate with users about their roles and responsibilities to maintain a safe '
         'and secure working environment?.',
         'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
         'Q-GOV-04: Does the organization assign a qualified individual with the mission and resources to centrally-manage '
         'coordinate, develop, implement and maintain an enterprise-wide cybersecurity and privacy program? .',
         'Q-SEA-03: Does the organization implement security functions as a layered structure minimizing interactions between '
         'layers of the design and avoiding any dependence by lower layers on the functionality or correctness of higher '
         'layers? .',
         'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to separate untrusted networks '
         'from trusted networks?.',
         'Q-NET-06: Does the organization logically or physically segment information flows to accomplish network '
         'segmentation?.',
         'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more restrictive baseline '
         'configurations?.',
         'Q-CFG-02: Does the organization develop, document and maintain secure baseline configurations for technology '
         'platform that are consistent with industry-accepted system hardening standards? .',
         'Q-CLD-01: Does the organization facilitate the implementation of cloud management controls to ensure cloud instances '
         'are secure and in-line with industry practices? .',
         'Q-CHG-02.1: Does the organization prohibit unauthorized changes, unless organization-approved change requests are '
         'received?.',
         'Q-CHG-02: Does the organization govern the technical configuration change control processes?.',
         'Q-CHG-01: Does the organization facilitate the implementation of a change management program?.',
         'Q-NET-12.1: Does the organization protect external and internal wireless links from signal parameter attacks through '
         'monitoring for unauthorized wireless connections, including scanning for unauthorized wireless access points and '
         'taking appropriate action, if an unauthorized connection is discovered?.',
         'Q-NET-02.2: Does the organization implement and manage a secure guest network? .',
         'Q-AST-04.2: Does the organization ensure control applicability is appropriately-determined for systems, '
         'applications, services and third parties by graphically representing applicable boundaries?.',
         'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain sufficient detail to '
         "assess the security of the network's architecture;  -  Reflect the current architecture of the network environment; "
         'and  -  Document all sensitive/regulated data flows?.',
         'Q-TDA-02.1: Does the organization require the developers of systems, system components or services to identify early '
         'in the Secure Development Life Cycle (SDLC), the functions, ports, protocols and services intended for use? .',
         'Q-TPM-04.2: Does the organization require process owners to identify the ports, protocols and other services '
         'required for the use of such services? .',
         'Q-TDA-02.5: Does the organization require process owners to identify, document and justify the business need for the '
         'ports, protocols and other services necessary to operate their technology solutions? .',
         'Q-TDA-02.6: Does the organization mitigate the risk associated with the use of insecure ports, protocols and '
         'services necessary to operate technology solutions? .',
         'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to reduce risk and exposure to '
         'threats?.',
         'Q-CFG-03: Does the organization configure systems to provide only essential capabilities by specifically prohibiting '
         'or restricting the use of ports, protocols, and/or services? .',
         'Q-NET-04.6: Does the organization enforce the use of human reviews for Access Control Lists (ACLs) and similar '
         'rulesets on a routine basis? .',
         'Q-CFG-03.1: Does the organization periodically review system configurations to identify and disable unnecessary '
         'and/or non-secure functions, ports, protocols and services?.',
         "Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the organization's "
         'cybersecurity and privacy policies and standards? .',
         'Q-CFG-02.6: Does the organization configure network devices to synchronize startup and running configuration files? '
         '.',
         'Q-CHG-04: Does the organization enforce configuration restrictions in an effort to restrict the ability of users to '
         'conduct unauthorized changes?.',
         'Q-NET-04.1: Does the organization configure firewall and router configurations to deny network traffic by default '
         'and allow network traffic by exception (e.g., deny all, permit by exception)? .',
         'Q-NET-04: Does the organization design, implement and review firewall and router configurations to restrict '
         'connections between untrusted networks and internal systems? .',
         'Q-NET-03.5: Does the organization prevent the unauthorized exfiltration of sensitive/regulated data across managed '
         'interfaces?.',
         'Q-NET-03.7: Does the organization employ boundary protections to isolate systems, services and process that support '
         'critical missions and/or business functions? .',
         'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to monitor and control '
         'communications at the external network boundary and at key internal boundaries within the network?.',
         'Q-NET-03.8: Does the organization implement separate network addresses (e.g., different subnets) to connect to '
         'systems in different security domains?.',
         'Q-NET-02: Does the organization implement security functions as a layered structure that minimizes interactions '
         'between layers of the design and avoiding any dependence by lower layers on the functionality or correctness of '
         'higher layers? .',
         'Q-NET-03.1: Does the organization limit the number of concurrent external network connections to its systems?.',
         'Q-NET-08.2: Does the organization require wireless network segments to implement Wireless Intrusion Detection / '
         'Prevention Systems (WIDS/WIPS) technologies?.',
         'Q-NET-08: Does the organization implement Network Intrusion Detection / Prevention Systems (NIDS/NIPS) used to '
         'detect and/or prevent intrusions into the network? .',
         'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS / IPS) technologies on '
         'critical systems, key network segments and network choke points?.',
         'Q-NET-05.1: Does the organization prohibit the direct connection of a sensitive system to an external network '
         'without the use of an organization-defined boundary protection device? .',
         'Q-DCH-15: Does the organization control publicly-accessible content?.',
         'Q-VPM-06.8: Does the organization define what information is allowed to be discoverable by adversaries and take '
         'corrective actions to remediated non-compliant systems?.',
         'Q-NET-03.3: Does the organization prevent the public disclosure of internal address information? .',
         'Q-END-05: Does the organization utilize host-based firewall software, or a similar technology, on all information '
         'systems, where technically feasible?.',
         'Q-END-02: Does the organization protect the confidentiality, integrity, availability and safety of endpoint '
         'devices?.',
         'Q-END-01: Does the organization facilitate the implementation of endpoint security controls?.',
         'Q-CFG-03.4: Does the organization prevent systems from creating split tunneling connections or similar techniques '
         'that could be used to exfiltrate data?.',
         'Q-IAC-10.8: Does the organization ensure vendor-supplied defaults are changed as part of the installation process?.',
         'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, individual, or responsible '
         'organization level to establish a common understanding of requirements for asset protection?.',
         'Q-SEA-04.1: Does the organization isolate security functions from non-security functions? .',
         'Q-END-16.1: Does the organization implement underlying software separation mechanisms to facilitate security '
         'function isolation? .',
         'Q-END-16: Does the organization ensure  security functions are restricted to authorized individuals and enforce '
         'least privilege control requirements for necessary job functions?.',
         'Q-TDA-05.1: Does the organization secure physical diagnostic and test interfaces to prevent misuse?.',
         'Q-MNT-05.3: Does the organization cryptographically protect the integrity and confidentiality of remote, non-local '
         'maintenance and diagnostic communications? .',
         'Q-CRY-06: Does the organization use cryptographic mechanisms to protect the confidentiality and integrity of '
         'non-console administrative access?.',
         'Q-CRY-02: Does the organization use cryptographic mechanisms authenticate to a cryptographic module?.',
         'Q-NET-15.1: Does the organization implement authentication and cryptographic mechanisms used to protect wireless '
         'access?.',
         'Q-CRY-07: Does the organization protect wireless access via secure authentication and encryption?.',
         'Q-CRY-09.3: Does the organization ensure the availability of information in the event of the loss of cryptographic '
         'keys by individual users? .',
         'Q-TPM-04.4: Does the organization restrict the location of information processing/storage based on business '
         'requirements? .',
         'Q-DCH-18: Does the organization retain media and data in accordance with applicable statutory, regulatory and '
         'contractual obligations? .',
         'Q-DCH-06.5: Does the organization prohibit the storage of sensitive authentication data after authorization? .',
         'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent unauthorized disclosure of data '
         'at rest? .',
         'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known '
         'public standards and trusted cryptographic technologies?.',
         'Q-PRI-05.3: Does the organization mask sensitive information through data anonymization, pseudonymization, redaction '
         'or de-identification? .',
         'Q-DCH-03.2: Does the organization apply data masking to sensitive information that is displayed or printed? .',
         'Q-NET-14: Does the organization define, control and review organization-approved, secure remote access methods?.',
         'Q-DCH-01.2: Does the organization protect sensitive/regulated data wherever it is stored?.',
         'Q-CRY-09: Does the organization facilitate cryptographic key management controls to protect the confidentiality, '
         'integrity and availability of keys?.',
         'Q-CRY-09.4: Does the organization facilitate the secure distribution of symmetric and asymmetric cryptographic keys '
         'using industry recognized key management technology and processes? .',
         'Q-CRY-08.1: Does the organization have appropriate resiliency mechanisms to ensure the availability of data in the '
         'event of the loss of cryptographic keys?.',
         'Q-IAC-12: Does the organization ensure cryptographic modules adhere to applicable statutory, regulatory and '
         'contractual requirements for security strength?.',
         'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of data being transmitted? .',
         'Q-CRY-09.6: Does the organization ensure customers are provided with appropriate key management guidance whenever '
         'cryptographic keys are shared?.',
         'Q-NET-12: Does the organization use strong cryptography and security protocols to safeguard sensitive/regulated data '
         'during transmission over open, public networks?.',
         'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the confidentiality of data being '
         'transmitted? .',
         'Q-NET-12.2: Does the organization prohibit the transmission of unprotected sensitive/regulated data by end-user '
         'messaging technologies?.',
         'Q-END-04.2: Does the organization document antimalware technologies?.',
         'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate malicious code?.',
         'Q-END-04.6: Does the organization perform periodic evaluations evolving malware threats to assess systems that are '
         'generally not considered to be commonly affected by malicious software? .',
         'Q-END-04.1: Does the organization automatically update antimalware technologies, including signature definitions? .',
         'Q-END-04.7: Does the organization ensure that anti-malware technologies are continuously running and cannot be '
         'disabled or altered by non-privileged users, unless specifically authorized by management on a case-by-case basis '
         'for a limited time period? .',
         'Q-END-04.3: Does the organization centrally-manage antimalware technologies?.',
         'Q-END-08: Does the organization utilize anti-phishing and spam protection technologies to detect and take action on '
         'unsolicited messages transported by electronic mail?.',
         'Q-TDA-15: Does the organization require system developers and integrators to create a Security Test and Evaluation '
         '(ST&E) plan and implement the plan under the witness of an independent party? .',
         'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
         'Q-TDA-05: Does the organization require the developers of systems, system components or services to produce a design '
         "specification and security architecture that:   -  Is consistent with and supportive of the organization's security "
         "architecture which is established within and is an integrated part of the organization's enterprise architecture;  "
         '-  Accurately and completely describes the required security functionality and the allocation of security controls '
         'among physical and logical components; and  -  Expresses how individual security functions, mechanisms and services '
         'work together to provide required security capabilities and a unified approach to protection?.',
         'Q-TDA-02.3: Does the organization require software vendors/manufacturers to demonstrate that their software '
         'development processes employ industry-recognized secure practices for secure programming, engineering methods, '
         'quality control processes and validation techniques to minimize flawed or malformed software?.',
         'Q-TDA-01: Does the organization facilitate the implementation of tailored development and acquisition strategies, '
         'contract tools and procurement methods to meet unique business needs?.',
         'Q-IAO-04: Does the organization require system developers and integrators to create and execute a Security Test and '
         'Evaluation (ST&E) plan to identify and remediate flaws during development?.',
         'Q-TDA-13: Does the organization ensure that the developers of systems, applications and/or services have the '
         'requisite skillset and appropriate access authorizations?.',
         'Q-TDA-06.3: Does the organization utilize a Software Assurance Maturity Model (SAMM) to govern a secure development '
         'lifecycle for the development of systems, applications and services?.',
         'Q-SAT-03.8: Does the organization ensure application development and operations (DevOps) personnel receive '
         'Continuing Professional Education (CPE) training on Secure Software Development Practices (SSDP) to appropriately '
         'address evolving threats?.',
         'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before authorizing access to the '
         'system or performing assigned duties;   -  When required by system changes; and   -  Annually thereafter?.',
         'Q-HRS-03.2: Does the organization ensure that all security-related positions are staffed by qualified individuals '
         'who have the necessary skill set? .',
         'Q-TDA-09: Does the organization require system developers/integrators consult with cybersecurity and privacy '
         'personnel to:   -  Create and implement a Security Test and Evaluation (ST&E) plan;  -  Implement a verifiable flaw '
         'remediation process to correct weaknesses and deficiencies identified during the security testing and evaluation '
         'process; and  -  Document the results of the security testing/evaluation and flaw remediation processes?.',
         'Q-TDA-06.5: Does the organization have an independent review of the software design to confirm that all '
         'cybersecurity and privacy requirements are met and that any identified risks are satisfactorily addressed?.',
         'Q-TDA-09.5: Does the organization perform application-level penetration testing of custom-made applications and '
         'services?.',
         'Q-TDA-09.4: Does the organization utilize testing methods to ensure systems, services and products continue to '
         'operate as intended when subject to invalid or unexpected inputs on its interfaces?.',
         'Q-TDA-09.3: Does the organization require the developers of systems, system components or services to employ dynamic '
         'code analysis tools to identify and remediate common flaws and document the results of the analysis? .',
         'Q-TDA-09.2: Does the organization require the developers of systems, system components or services to employ static '
         'code analysis tools to identify and remediate common flaws and document the results of the analysis? .',
         'Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
         'Q-VPM-03: Does the organization identify and assign a risk ranking to newly discovered security vulnerabilities '
         'using reputable outside sources for security vulnerability information? .',
         'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface management activities?.',
         'Q-VPM-01: Does the organization facilitate the implementation and monitoring of vulnerability management controls?.',
         'Q-THR-06: Does the organization establish a Vulnerability Disclosure Program (VDP) to assist with the secure '
         'development and maintenance of products and services that receives unsolicited input from the public about '
         'vulnerabilities in organizational systems, services and processes?.',
         'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
         'Q-GOV-07: Does the organization establish contact with selected groups and associations within the cybersecurity & '
         'privacy communities to:   -  Facilitate ongoing cybersecurity and privacy education and training for organizational '
         'personnel;  -  Maintain currency with recommended cybersecurity and privacy practices, techniques and technologies; '
         'and  -  Share current security-related information including threats, vulnerabilities and incidents? .',
         'Q-TDA-04.2: Does the organization require a Software Bill of Materials (SBOM) for systems, applications and services '
         'that lists software packages in use, including versions and applicable licenses?.',
         'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects the current system;   -  '
         'Is at the level of granularity deemed necessary for tracking and reporting;  -  Includes organization-defined '
         'information deemed necessary to achieve effective property accountability; and  -  Is available for review and audit '
         'by designated organizational officials? .',
         'Q-AST-01: Does the organization facilitate the implementation of asset management controls?.',
         'Q-VPM-05: Does the organization conduct software patching for all deployed operating systems, applications and '
         'firmware?.',
         'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing basis and ensure assets are '
         'protected against known attacks? .',
         'Q-WEB-03: Does the organization deploy Web Application Firewalls (WAFs) to provide defense-in-depth protection for '
         'application-specific threats? .',
         'Q-WEB-01: Does the organization facilitate the implementation of an enterprise-wide web management policy, as well '
         'as associated standards, controls and procedures?.',
         "Q-VPM-06.6: Does the organization perform quarterly external vulnerability scans (outside the organization's network "
         'looking inward) via a reputable vulnerability service provider, which include rescans until passing results are '
         'obtained or all high vulnerabilities are resolved, as defined by the Common Vulnerability Scoring System (CVSS)?.',
         'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by recurring vulnerability scanning '
         'of systems and web applications?.',
         'Q-WEB-01.1: Does the organization prevent unauthorized code from being present in a secure page as it is rendered in '
         "a client's browser?.",
         'Q-CHG-02.2: Does the organization appropriately test and document proposed changes in a non-production environment '
         'before changes are implemented in a production environment?.',
         'Q-CHG-06.1: Does the organization report the results of cybersecurity and privacy function verification to '
         'appropriate organizational management?.',
         'Q-CHG-06: Does the organization verify the functionality of security controls when anomalies are discovered?.',
         'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, prior to the implementation '
         'of the change?.',
         'Q-TDA-08: Does the organization manage separate development, testing and operational environments to reduce the '
         'risks of unauthorized access or changes to the operational environment and to ensure no impact to production '
         'systems?.',
         'Q-TDA-07: Does the organization maintain a segmented development network to ensure a secure development environment? '
         '.',
         'Q-HRS-11: Does the organization implement and maintain Separation of Duties (SoD) to prevent potential inappropriate '
         'activity without collusion?.',
         'Q-TDA-10: Does the organization approve, document and control the use of live data in development and test '
         'environments?.',
         'Q-PRI-05.4: Does the organization restrict the use of Personal Data (PD) to only the authorized purpose(s) '
         'consistent with applicable laws, regulations and in privacy notices? .',
         'Q-PRI-05.1: Does the organization address the use of Personal Data (PD) for internal testing, training and research '
         'that:  -  Takes measures to limit or minimize the amount of PD used for internal testing, training and research '
         'purposes; and  -  Authorizes the use of PD when such information is required for internal testing, training and '
         'research?.',
         'Q-TDA-08.1: Does the organization ensure secure migration practices purge systems, applications and services of '
         'test/development/staging data and accounts before it is migrated into a production environment?.',
         'Q-CFG-02.4: Does the organization manage baseline configurations for development and test environments separately '
         'from operational baseline configurations to minimize the risk of unintentional changes?.',
         'Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only authorized access to processes '
         'necessary to accomplish assigned tasks in accordance with organizational business functions? .',
         'Q-IAC-20.1: Does the organization limit access to sensitive/regulated data to only those individuals whose job '
         'requires such access?.',
         'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that conform to the principle of '
         "'least privilege?'.",
         'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over users and resources?.',
         'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users and processes acting on '
         'behalf of organizational users? .',
         'Q-IAC-01: Does the organization facilitate the implementation of identification and access management controls?.',
         'Q-IAC-21.3: Does the organization restrict the assignment of privileged accounts to organization-defined personnel '
         'or roles without management approval?.',
         'Q-IAC-16: Does the organization restrict and control privileged access rights for users and services?.',
         'Q-IAC-07.1: Does the organization revoke user access rights following changes in personnel roles and duties, if no '
         'longer necessary or permitted? .',
         'Q-IAC-07: Does the organization utilize a formal user registration and de-registration process that governs the '
         'assignment of access rights? .',
         'Q-IAC-17: Does the organization periodically-review the privileges assigned to individuals and service accounts to '
         'validate the need for such privileges and reassign or remove unnecessary privileges, as necessary?.',
         'Q-IAC-16.1: Does the organization inventory all privileged accounts and validate that each person with elevated '
         'privileges is authorized by the appropriate level of organizational management? .',
         'Q-IAC-20.2: Does the organization restrict access to database containing sensitive/regulated data to only necessary '
         'services or those individuals whose job requires such access?.',
         'Q-MON-03.7: Does the organization ensure databases produce audit records that contain sufficient information to '
         'monitor database activities that includes, at a minimum:  -  Access to particularly important information;  -  '
         'Addition of new users, especially privileged users;  -  Any query containing comments;  -  Any query containing '
         'multiple embedded queries;  -  Any query or database alerts or failures;  -  Attempts to elevate privileges;  -  '
         'Attempted access that is successful or unsuccessful;  -  Changes to the database structure;  -  Changes to user '
         'roles or database permissions;  -  Database administrator actions;  -  Database logons and logoffs;  -  '
         'Modifications to data; and  -  Use of executable commands?.',
         'Q-IAC-09.1: Does the organization ensure proper user identification management for non-consumer users and '
         'administrators? .',
         'Q-IAC-09: Does the organization govern naming standards for usernames and systems?.',
         'Q-IAC-19: Does the organization prevent the sharing of generic IDs, passwords or other generic authentication '
         'methods?.',
         'Q-IAC-15.5: Does the organization authorize the use of shared/group accounts only under certain organization-defined '
         'conditions?.',
         'Q-IAC-02.1: Does the organization require individuals to be authenticated with an individual authenticator when a '
         'group authenticator is utilized? .',
         'Q-TPM-05.3: Does the organization ensure Third-Party Service Providers (TSP) use unique authentication factors for '
         'each of its customers?.',
         'Q-TPM-05: Does the organization identify, regularly review and document third-party confidentiality, Non-Disclosure '
         "Agreements (NDAs) and other contracts that reflect the organization's needs to protect systems and data?.",
         "Q-TPM-04: Does the organization mitigate the risks associated with third-party access to the organization's systems "
         'and data?.',
         'Q-TPM-01: Does the organization facilitate the implementation of third-party management controls?.',
         'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote network access? .',
         'Q-IAC-05.1: Does the organization ensure third-party service providers provide current and accurate information for '
         "any third-party user with access to the organization's data or assets?.",
         'Q-IAC-05: Does the organization identify and authenticate third-party systems and services?.',
         'Q-IAC-03.2: Does the organization accept Federal Identity, Credential and Access Management (FICAM)-approved '
         'third-party credentials? .',
         'Q-IAC-15: Does the organization proactively govern account management of individual, group, system, application, '
         'guest and temporary accounts?.',
         'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
         'Q-IAC-07.2: Does the organization revoke user access rights in a timely manner, upon termination of employment or '
         'contract?.',
         "Q-HRS-09.2: Does the organization expedite the process of removing 'high risk' individual's access to systems and "
         'applications upon termination, as determined by management?.',
         'Q-HRS-09: Does the organization govern the termination of individual employment?.',
         'Q-IAC-15.3: Does the organization use automated mechanisms to disable inactive accounts after an '
         'organization-defined time period? .',
         'Q-NET-14.6: Does the organization proactively control and monitor third-party accounts used to access, support, or '
         'maintain system components via remote access?.',
         'Q-MNT-05.4: Does the organization provide remote disconnect verification to ensure remote, non-local maintenance and '
         'diagnostic sessions are properly terminated?.',
         'Q-MNT-05.1: Does the organization audit remote, non-local maintenance and diagnostic sessions and review the '
         'maintenance records of the sessions? .',
         'Q-MNT-05: Does the organization authorize, monitor and control remote, non-local maintenance and diagnostic '
         'activities?.',
         'Q-NET-07: Does the organization terminate remote sessions at the end of the session or after an organization-defined '
         'time period of inactivity? .',
         'Q-IAC-25: Does the organization use automated mechanisms to log out users, both locally on the network and for '
         'remote sessions, at the end of the session or after an organization-defined period of inactivity? .',
         'Q-IAC-24: Does the organization initiate a session lock after an organization-defined time period of inactivity, or '
         'upon receiving a request from a user and retain the session lock until the user reestablishes access using '
         'established identification and authentication methods?.',
         'Q-IAC-14: Does the organization force users and devices to re-authenticate according to organization-defined '
         'circumstances that necessitate re-authentication? .',
         'Q-IAC-10.2: Does the organization validate certificates by constructing and verifying a certification path to an '
         'accepted trust anchor including checking certificate status information for PKI-based authentication?.',
         'Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations to ensure strong criteria '
         'for password-based authentication?.',
         'Q-IAC-28: Does the organization collect, validate and verify identity evidence of a user?.',
         'Q-IAC-22: Does the organization enforce a limit for consecutive invalid login attempts by a user during an '
         'organization-defined time period and automatically locks the account when the maximum number of unsuccessful '
         'attempts is exceeded?.',
         'Q-SAT-02: Does the organization provide all employees and contractors appropriate awareness education and training '
         'that is relevant for their job function? .',
         'Q-SAT-01: Does the organization facilitate the implementation of security workforce development and awareness '
         'controls? .',
         'Q-WEB-06: Does the organization implement Strong Customer Authentication (SCA) for consumers to reasonably prove '
         'their identity?.',
         'Q-IAC-18: Does the organization compel users to follow accepted practices in the use of authentication mechanisms '
         '(e.g. passwords, passphrases, physical or logical security tokens, smart cards, certificates, etc.)? .',
         'Q-IAC-10.7: Does the organization ensure organization-defined token quality requirements are satisfied for hardware '
         'token-based authentication?.',
         'Q-IAC-10.5: Does the organization protect authenticators commensurate with the sensitivity of the information to '
         'which use of the authenticator permits access? .',
         'Q-IAC-06.1: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate network access for '
         'privileged accounts? .',
         'Q-IAC-06.4: Does the organization implement Multi-Factor Authentication (MFA) for remote access to privileged and '
         'non-privileged accounts such that one of the factors is securely provided by a device separate from the system '
         'gaining access? .',
         'Q-IAC-06.3: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate local access for '
         'privileged accounts? .',
         'Q-IAC-06.2: Does the organization utilize Multi-Factor Authentication (MFA) to authenticate network access for '
         'non-privileged accounts? .',
         'Q-SEA-01: Does the organization facilitate the implementation of industry-recognized cybersecurity and privacy '
         'practices in the specification, design, development, implementation and modification of systems and services?.',
         'Q-IAC-02.2: Does the organization employ replay-resistant network access authentication?.',
         'Q-IAC-20.3: Does the organization restrict and tightly control utility programs that are capable of overriding '
         'system and application controls?.',
         'Q-IAC-15.7: Does the organization review all system accounts and disable any account that cannot be associated with '
         'a business process and owner? .',
         'Q-IAC-10.6: Does the organization ensure that unencrypted, static authenticators are not embedded in applications, '
         'scripts or stored on function keys? .',
         'Q-PES-01: Does the organization facilitate the operation of physical and environmental protection controls? .',
         'Q-PES-03: Does the organization enforce physical access authorizations for all physical access points (including '
         'designated entry/exit points) to facilities (excluding those areas within the facility officially designated as '
         'publicly accessible)?.',
         'Q-PES-03.3: Does the organization generate a log entry for each access through controlled ingress and egress '
         'points?.',
         'Q-PES-03.1: Does the organization limit and monitor physical access through controlled ingress and egress points?.',
         'Q-PES-02.1: Does the organization authorize physical access to facilities based on the position or role of the '
         'individual?.',
         'Q-PES-02: Does the organization maintain a current list of personnel with authorized access to organizational '
         'facilities (except for those areas within the facility officially designated as publicly accessible)?.',
         'Q-PES-05.2: Does the organization monitor physical access to critical information systems or sensitive/regulated '
         'data, in addition to the physical access monitoring of the facility?.',
         'Q-PES-05.1: Does the organization monitor physical intrusion alarms and surveillance equipment? .',
         'Q-PES-05: Does the organization monitor for, detect and respond to physical security incidents?.',
         'Q-PES-12.2: Does the organization restrict access to printers and other system output devices to prevent '
         'unauthorized individuals from obtaining the output? .',
         'Q-PES-12.1: Does the organization protect power and telecommunications cabling carrying data or supporting '
         'information services from interception, interference or damage? .',
         'Q-PES-12: Does the organization locate system components within the facility to minimize potential damage from '
         'physical and environmental hazards and to minimize the opportunity for unauthorized access? .',
         'Q-PES-03.2: Does the organization protect system components from unauthorized physical access (e.g., lockable '
         'physical casings)? .',
         'Q-PES-04.1: Does the organization allow only authorized personnel access to secure areas? .',
         'Q-PES-04: Does the organization design and implement physical access controls for offices, rooms and facilities?.',
         'Q-PES-06.3: Does the organization restrict unescorted access to facilities to personnel with required security '
         'clearances, formal access authorizations and validated the need for access? .',
         'Q-PES-06.2: Does the organization requires at least one (1) form of government-issued photo identification to '
         'authenticate individuals before they can gain access to the facility?.',
         'Q-PES-06.1: Does the organization easily distinguish between onsite personnel and visitors, especially in areas '
         'where sensitive/regulated data is accessible?.',
         'Q-PES-06: Does the organization identify, authorize and monitor visitors before allowing access to the facility '
         '(other than areas designated as publicly accessible)? .',
         'Q-PES-06.6: Does the organization ensure visitor badges, or other issued identification, are surrendered before '
         'visitors leave the facility or are deactivated at a pre-determined time/date of expiration?.',
         'Q-PES-06.5: Does the organization minimize the collection of Personal Data (PD) contained in visitor access '
         'records?.',
         'Q-DCH-06.1: Does the organization physically secure all media that contains sensitive information?.',
         'Q-DCH-06: Does the organization:   -  Physically control and securely store digital and non-digital media within '
         'controlled areas using organization-defined security measures; and  -  Protect system media until the media are '
         'destroyed or sanitized using approved equipment, techniques and procedures?.',
         'Q-DCH-01.1: Does the organization ensure data stewardship is assigned, documented and communicated? .',
         'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? .',
         'Q-BCD-11.2: Does the organization store backup copies of critical software and other security-related information in '
         'a separate facility or in a fire-rated container that is not collocated with the system being backed up?.',
         'Q-BCD-11: Does the organization create recurring backups of data, software and/or system images, as well as verify '
         'the integrity of these backups, to ensure the availability of the data to satisfying Recovery Time Objectives (RTOs) '
         'and Recovery Point Objectives (RPOs)?.',
         'Q-DCH-06.2: Does the organization maintain inventory logs of all sensitive media and conduct sensitive media '
         'inventories at least annually? .',
         'Q-BCD-02.4: Does the organization perform periodic security reviews of storage locations that contain sensitive / '
         'regulated data?.',
         'Q-RSK-02: Does the organization categorizes systems and data in accordance with applicable local, state and Federal '
         'laws that:  -  Document the security categorization results (including supporting rationale) in the security plan '
         'for systems; and  -  Ensure the security categorization decision is reviewed and approved by the asset owner?.',
         'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with applicable statutory, '
         'regulatory and contractual requirements? .',
         'Q-DCH-07.1: Does the organization identify custodians throughout the transport of digital or non-digital media?.',
         'Q-DCH-07: Does the organization protect and control digital and non-digital media during transport outside of '
         'controlled areas using appropriate security measures?.',
         'Q-AST-05.1: Does the organization obtain management approval for any sensitive / regulated media that is transferred '
         "outside of the organization's facilities?.",
         'Q-AST-05: Does the organization maintain strict control over the internal or external distribution of any kind of '
         'sensitive/regulated media?.',
         'Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for an organization-defined '
         'time period to fulfill the purpose(s) identified in the notice or as required by law;  -  Disposes of, destroys, '
         'erases, and/or anonymizes the PI, regardless of the method of storage; and  -  Uses organization-defined techniques '
         'or methods to ensure secure deletion or destruction of PD (including originals, copies and archived records)?.',
         'Q-DCH-08: Does the organization securely dispose of media when it is no longer required, using formal procedures? .',
         'Q-DCH-09.1: Does the organization supervise, track, document and verify media sanitization and disposal actions? .',
         'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity commensurate with the '
         'classification or sensitivity of the information prior to disposal, release out of organizational control or release '
         'for reuse?.',
         'Q-AST-09: Does the organization securely dispose of, destroy or repurpose system components using '
         'organization-defined techniques and methods to prevent such components from entering the gray market?.',
         'Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness training that is specific '
         "to the cyber threats that the user might encounter the user's specific day-to-day business operations?.",
         'Q-SAT-03.3: Does the organization ensure that every user accessing a system processing, storing or transmitting '
         'sensitive information is formally trained in data handling requirements?.',
         'Q-AST-15.1: Does the organization physically and logically inspect critical systems to detect evidence of tampering? '
         '.',
         'Q-AST-15: Does the organization verify logical configuration settings and the physical integrity of critical '
         'technology assets throughout their lifecycle?.',
         'Q-AST-07: Does the organization appropriately protect devices that capture sensitive/regulated data via direct '
         'physical interaction from tampering and substitution?.',
         'Q-AST-06: Does the organization implement enhanced protection measures for unattended systems to protect against '
         'tampering and unauthorized access?.',
         'Q-AST-08: Does the organization periodically inspect systems and system components for Indicators of Compromise '
         '(IoC)?.',
         'Q-MON-03.2: Does the organization link system access to individual users or service accounts?.',
         'Q-MON-03: Does the organization configure systems to produce audit records that contain sufficient information to, '
         'at a minimum:  -  Establish what type of event occurred;  -  When (date and time) the event occurred;  -  Where the '
         'event occurred;  -  The source of the event;  -  The outcome (success or failure) of the event; and   -  The '
         'identity of any user/subject associated with the event? .',
         'Q-MON-03.3: Does the organization log and review the actions of users and/or services with elevated privileges?.',
         'Q-IAC-21.4: Does the organization audit the execution of privileged functions? .',
         'Q-MON-08.2: Does the organization restrict access to the management of event logs to privileged users with a '
         'specific business need?.',
         'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized access, modification and '
         'deletion?.',
         'Q-MON-08.1: Does the organization back up event logs onto a physically different system or system component than the '
         'Security Incident Event Manager (SIEM) or similar automated tool?.',
         'Q-MON-02.2: Does the organization centrally collect, review and analyze audit records from multiple sources?.',
         'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or similar automated tool, to '
         'support the centralized collection of security-related event logs?.',
         'Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect and report unauthorized '
         'changes to system files and configurations?.',
         'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar change-detection technology, on '
         'critical assets to generate alerts for unauthorized modifications? .',
         'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate incidents in accordance with '
         'established timelines and procedures?.',
         'Q-MON-01.4: Does the organization monitor, correlate and respond to alerts from physical, cybersecurity, privacy and '
         'supply chain activities to achieve integrated situational awareness? .',
         'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or similar automated tool, to '
         'support near real-time analysis and incident escalation?.',
         'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across the enterprise by a '
         'Security Incident Event Manager (SIEM) or similar automated tool, to maintain situational awareness?.',
         'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide monitoring controls?.',
         'Q-MON-10: Does the organization retain event logs for a time period consistent with records retention requirements '
         'to provide support for after-the-fact investigations of security incidents and to meet statutory, regulatory and '
         'contractual retention requirements? .',
         'Q-SEA-20: Does the organization utilize time-synchronization technology to synchronize all critical system clocks? .',
         'Q-MON-07.1: Does the organization synchronize internal system clocks with an authoritative time source? .',
         'Q-MON-07: Does the organization configure systems to use an authoritative time source to generate time stamps for '
         'event logs? .',
         'Q-MON-02.7: Does the organization compile audit records into an organization-wide audit trail that is '
         'time-correlated?.',
         'Q-TPM-11: Does the organization ensure response/recovery planning and testing are conducted with critical '
         'suppliers/providers? .',
         'Q-SEA-01.1: Does the organization centrally-manage the organization-wide management and implementation of '
         'cybersecurity and privacy controls and related processes?.',
         'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy assessments, incidents and '
         'audits to ensure proper remediation has been performed?.',
         'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
         'Q-IRO-01: Does the organization facilitate the implementation of incident response controls?.',
         'Q-END-06.2: Does the organization detect and respond to unauthorized configuration changes as cybersecurity '
         'incidents?.',
         'Q-CFG-02.8: Does the organization respond to unauthorized changes to configuration settings as security incidents? .',
         'Q-CPL-03: Does the organization ensure managers regularly review the processes and documented procedures within '
         'their area of responsibility to adhere to appropriate security policies, standards and other applicable '
         'requirements?.',
         'Q-CPL-02: Does the organization provide a security & privacy controls oversight function that reports to the '
         "organization's executive leadership?.",
         'Q-NET-15.5: Does the organization test for the presence of Wireless Access Points (WAPs) and identify all authorized '
         'and unauthorized WAPs within the facility(ies)? .',
         'Q-NET-15: Does the organization control authorized wireless usage and monitor for unauthorized wireless access?.',
         'Q-NET-01: Does the organization develop, govern & update procedures to facilitate the implementation of network '
         'security controls?.',
         'Q-VPM-06.2: Does the organization identify the breadth and depth of coverage for vulnerability scanning that define '
         'the system components scanned and types of vulnerabilities that are checked for? .',
         'Q-VPM-06.1: Does the organization update vulnerability scanning tools?.',
         'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, tracked and remediated?.',
         'Q-VPM-06.7: Does the organization perform quarterly internal vulnerability scans, that includes all segments of the '
         "organization's internal network, as well as rescans until passing results are obtained or all high vulnerabilities "
         'are resolved, as defined by the Common Vulnerability Scoring System (CVSS)?.',
         'Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to perform penetration '
         'testing?.',
         'Q-VPM-07: Does the organization conduct penetration testing on systems and web applications?.',
         'Q-SAT-03.2: Does the organization provide training to personnel on organization-defined indicators of malware to '
         'recognize suspicious communications and anomalous behavior?.',
         'Q-MON-15: Does the organization conduct covert channel analysis to identify aspects of communications that are '
         'potential avenues for covert channels?.',
         'Q-MON-11.1: Does the organization analyze network traffic to detect covert data exfiltration?.',
         'Q-WEB-13: Does the organization detect and respond to Indicators of Compromise (IoC) for unauthorized alterations, '
         'additions, deletions or changes on websites that store, process and/or transmit sensitive / regulated data? .',
         'Q-HRS-05.1: Does the organization define acceptable and unacceptable rules of behavior for the use of technologies, '
         'including consequences for unacceptable behavior?.',
         'Q-HRS-05: Does the organization require all employees and contractors to apply cybersecurity and privacy principles '
         'in their daily work?.',
         'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational incident response personnel '
         'within organization-defined time-periods; and  -  Externally to regulatory authorities and affected parties, as '
         'necessary?.',
         'Q-HRS-05.4: Does the organization govern usage policies for critical technologies? .',
         'Q-HRS-05.3: Does the organization establish usage restrictions and implementation guidance for communications '
         'technologies based on the potential to cause damage to systems, if used maliciously? .',
         'Q-HRS-01: Does the organization facilitate the implementation of personnel security controls?.',
         'Q-RSK-07: Does the organization routinely update risk assessments and react accordingly upon identifying new '
         'security vulnerabilities, including using outside sources for security vulnerability information? .',
         'Q-RSK-04.1: Does the organization maintain a risk register that facilitates monitoring and reporting of risks?.',
         'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the likelihood and magnitude of '
         "harm, from unauthorized access, use, disclosure, disruption, modification or destruction of the organization's "
         'systems and data?.',
         'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
         'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, risk response and risk '
         'monitoring;  -  Constraints affecting risk assessments, risk response and risk monitoring;  -  The organizational '
         'risk tolerance; and  -  Priorities and trade-offs considered by the organization for managing risk?.',
         'Q-CRY-01.5: Does the organization identify, document and review deployed cryptographic cipher suites and protocols '
         'to proactively respond to industry trends regarding the continued viability of utilized cryptographic cipher suites '
         'and protocols?.',
         'Q-SEA-07.1: Does the organization manage the usable lifecycles of systems? .',
         'Q-SEA-02.3: Does the organization conduct ongoing technical debt reviews of hardware and software technologies to '
         'remediate outdated and/or unsupported technologies?.',
         'Q-TPM-05.4: Does the organization formally document a Customer Responsibility Matrix (CRM), delineating assigned '
         'responsibilities for controls between the Cloud Service Provider (CSP) and its customers.?.',
         'Q-CLD-06.1: Does the organization formally document a Customer Responsibility Matrix (CRM), delineating assigned '
         'responsibilities for controls between the Cloud Service Provider (CSP) and its customers?.',
         'Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service Providers (TSP) for '
         'compliance with established contractual requirements for cybersecurity and privacy controls? .',
         'Q-CPL-01.1: Does the organization document and review instances of non-compliance with statutory, regulatory and/or '
         'contractual obligations to develop appropriate risk mitigation actions?.',
         "Q-CLD-12: Does the organization prevent 'side channel attacks' when using a Content Delivery Network (CDN) by "
         "restricting access to the origin server's IP address to the CDN and an authorized management network?.",
         'Q-CPL-01.2: Does the organization document and validate the scope of cybersecurity and privacy controls that are '
         'determined to meet statutory, regulatory and/or contractual compliance obligations?.',
         'Q-AST-04.3: Does the organization create and maintain a current inventory of systems, applications and services that '
         'are in scope for statutory, regulatory and/or contractual compliance obligations that provides sufficient detail to '
         'determine control applicability, based on asset scope categorization?.',
         'Q-TPM-05.5: Does the organization perform recurring validation of the Responsible, Accountable, Supportive, '
         'Consulted & Informed (RASCI) matrix, or similar documentation, to ensure cybersecurity and privacy control '
         'assignments accurately reflect current business practices, compliance obligations, technologies and stakeholders? .',
         'Q-SAT-04: Does the organization document, retain and monitor individual training activities, including basic '
         'security awareness training, ongoing awareness training and specific-system training?.',
         "Q-HRS-05.7: Does the organization ensure personnel receive recurring familiarization with the organization's "
         'cybersecurity and privacy policies and provide acknowledgement?.',
         'Q-SAT-02.2: Does the organization include awareness training on recognizing and reporting potential and actual '
         'instances of social engineering and social mining?.',
         'Q-HRS-04.1: Does the organization ensure that individuals accessing a system that stores, transmits or processes '
         'information requiring special protection satisfy organization-defined personnel screening criteria?.',
         'Q-HRS-04: Does the organization manage personnel security risk by screening individuals prior to authorizing '
         'access?.',
         'Q-HRS-02.1: Does the organization ensure that every user accessing a system that processes, stores, or transmits '
         'sensitive information is cleared and regularly trained to handle the information in question?.',
         'Q-HRS-02: Does the organization manage personnel security risk by assigning a risk designation to all positions and '
         'establishing screening criteria for individuals filling those positions?.',
         'Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of Third-Party Service Providers '
         '(TSP) that can potentially impact the Confidentiality, Integrity, Availability and/or Safety (CIAS) of the '
         "organization's systems, applications, services and data?.",
         'Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or outsourcing of '
         'technology-related services?.',
         'Q-PRI-01.6: Does the organization ensure Personal Data (PD) is protected by security safeguards that are sufficient '
         'and appropriately scoped to protect the confidentiality and integrity of the PD?.',
         'Q-IRO-04: Does the organization maintain and make available a current and viable Incident Response Plan (IRP) to all '
         'stakeholders?.',
         'Q-IRO-06: Does the organization formally test incident response capabilities through realistic exercises to '
         'determine the operational effectiveness of those capabilities?.',
         'Q-IRO-04.2: Does the organization regularly review and modify incident response practices to incorporate lessons '
         'learned, business process changes and industry developments, as necessary?.',
         'Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and business function '
         'representatives that are capable of addressing cybersecurity and privacy incident response operations?.',
         'Q-IRO-05: Does the organization train personnel in their incident response roles and responsibilities?.',
         "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection and analysis, "
         'containment, eradication and recovery?.',
         'Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving cybersecurity and privacy '
         'incidents to reduce the likelihood or impact of future incidents? .',
         'Q-IRO-12: Does the organization respond to sensitive information spills?.',
         'Q-CLD-06: Does the organization ensure multi-tenant owned or managed assets (physical and virtual) are designed and '
         'governed such that provider and customer (tenant) user access is appropriately segmented from other tenant users?.',
         'Q-CLD-06.2: Does the organization ensure Multi-Tenant Service Providers (MTSP) facilitate security event logging '
         'capabilities for its customers that are consistent with applicable statutory, regulatory and/or contractual '
         'obligations?.',
         'Q-CLD-06.3: Does the organization ensure Multi-Tenant Service Providers (MTSP) facilitate prompt forensic '
         'investigations in the event of a suspected or confirmed security incident?.',
         'Q-CLD-06.4: Does the organization ensure Multi-Tenant Service Providers (MTSP) facilitate prompt response to '
         'suspected or confirmed security incidents and vulnerabilities, including timely notification to affected customers?.']

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '1.1.1: All security policies and operational procedures that are identified in Requirement 1 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 1 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '1.1: Processes and mechanisms for installing and maintaining network security controls are defined '
                        'and understood.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '1.1.2: Roles and responsibilities for performing activities in Requirement 1 are documented, '
                             'assigned, and understood.',
          'requirement_description': 'Roles and responsibilities for performing activities in Requirement 1 are documented, '
                                     'assigned, and understood. ',
          'subchapter': '1.1: Processes and mechanisms for installing and maintaining network security controls are defined '
                        'and understood.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-SEA-03: Does the organization implement security functions as a layered structure '
                                   'minimizing interactions between layers of the design and avoiding any dependence by lower '
                                   'layers on the functionality or correctness of higher layers? .',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .',
                                   'Q-CLD-01: Does the organization facilitate the implementation of cloud management controls '
                                   'to ensure cloud instances are secure and in-line with industry practices? .'],
          'objective_title': '1.2.1: Configuration standards for NSC rulesets are Defined, Implemented and Maintained.',
          'requirement_description': '\n'
                                     'Configuration standards for NSC rulesets are: \n'
                                     '• Defined. \n'
                                     '• Implemented. \n'
                                     '• Maintained.',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-CHG-02.1: Does the organization prohibit unauthorized changes, unless '
                                   'organization-approved change requests are received?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CHG-01: Does the organization facilitate the implementation of a change management '
                                   'program?.'],
          'objective_title': '1.2.2: All changes to network connections and to configurations of NSCs are approved and managed '
                             'in accordance with the change control process defined at Requirement 6.5.1.',
          'requirement_description': '\n'
                                     'All changes to network connections and configurations of NSCs are approved and managed '
                                     'in accordance with the change control process defined at Requirement 6.5.1. \n'
                                     'Applicability Notes \n'
                                     'Changes to network connections include the addition, removal, or modification of a '
                                     'connection. Changes to NSC configurations include those related to the component itself '
                                     'as well as those affecting how it performs its security function.',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-02.2: Does the organization implement and manage a secure guest network? .',
                                   'Q-AST-04.2: Does the organization ensure control applicability is appropriately-determined '
                                   'for systems, applications, services and third parties by graphically representing '
                                   'applicable boundaries?.',
                                   'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain '
                                   "sufficient detail to assess the security of the network's architecture;  -  Reflect the "
                                   'current architecture of the network environment; and  -  Document all sensitive/regulated '
                                   'data flows?.'],
          'objective_title': '1.2.3: An accurate network diagram(s) is maintained.',
          'requirement_description': '\n'
                                     'An accurate network diagram(s) is maintained that shows all connections between the CDE '
                                     'and other networks, including any wireless networks. \n'
                                     'Applicability Notes \n'
                                     'A current network diagram(s) or other technical or topological solution that identifies '
                                     'network connections and devices can be used to meet this requirement.',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-TDA-02.1: Does the organization require the developers of systems, system components or '
                                   'services to identify early in the Secure Development Life Cycle (SDLC), the functions, '
                                   'ports, protocols and services intended for use? .',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-AST-04: Does the organization maintain network architecture diagrams that:   -  Contain '
                                   "sufficient detail to assess the security of the network's architecture;  -  Reflect the "
                                   'current architecture of the network environment; and  -  Document all sensitive/regulated '
                                   'data flows?.'],
          'objective_title': '1.2.4: An accurate data-flow diagram(s) is maintained.',
          'requirement_description': '\n'
                                     'An accurate data-flow diagram(s) is maintained that meets the following: \n'
                                     '• Shows all account data flows across systems and networks. \n'
                                     '• Updated as needed upon changes to the environment. \n'
                                     'Applicability Notes \n'
                                     'A data-flow diagram(s) or other technical or topological solution that identifies flows '
                                     'of account data across systems and networks can be used to meet this requirement.',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-TPM-04.2: Does the organization require process owners to identify the ports, protocols '
                                   'and other services required for the use of such services? .',
                                   'Q-TDA-02.5: Does the organization require process owners to identify, document and justify '
                                   'the business need for the ports, protocols and other services necessary to operate their '
                                   'technology solutions? .',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.'],
          'objective_title': '1.2.5: All services, protocols and ports allowed  are identified, approved, and have a defined '
                             'business need.',
          'requirement_description': '\n'
                                     'All services, protocols and ports allowed are identified, approved, and have a defined '
                                     'business need.',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-TDA-02.6: Does the organization mitigate the risk associated with the use of insecure '
                                   'ports, protocols and services necessary to operate technology solutions? .',
                                   'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to '
                                   'reduce risk and exposure to threats?.',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-CFG-03: Does the organization configure systems to provide only essential capabilities '
                                   'by specifically prohibiting or restricting the use of ports, protocols, and/or services? .',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '1.2.6: Security features are defined and implemented for all services, protocols, and ports that '
                             'are in use and considered to be insecure, such that the risk is mitigated.',
          'requirement_description': 'Security features are defined and implemented for all services, protocols, and ports '
                                     'that are in use and considered to be insecure, such that the risk is mitigated. ',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-04.6: Does the organization enforce the use of human reviews for Access Control '
                                   'Lists (ACLs) and similar rulesets on a routine basis? .',
                                   'Q-CFG-03.1: Does the organization periodically review system configurations to identify '
                                   'and disable unnecessary and/or non-secure functions, ports, protocols and services?.',
                                   'Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the '
                                   "organization's cybersecurity and privacy policies and standards? ."],
          'objective_title': '1.2.7: Configurations of NSCs are reviewed at least once every six months to confirm they are '
                             'relevant and effective.',
          'requirement_description': 'Configurations of NSCs are reviewed at least once every six months to confirm they are '
                                     'relevant and effective. ',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-CFG-02.6: Does the organization configure network devices to synchronize startup and '
                                   'running configuration files? .',
                                   'Q-CHG-04: Does the organization enforce configuration restrictions in an effort to '
                                   'restrict the ability of users to conduct unauthorized changes?.'],
          'objective_title': '1.2.8: Configuration files for NSCs are secured from unauthorized access and kept consistent '
                             'with active network configurations.',
          'requirement_description': '\n'
                                     'Configuration files for NSCs are: \n'
                                     '• Secured from unauthorized access. \n'
                                     '• Kept consistent with active network configurations. \n'
                                     'Applicability Notes \n'
                                     'Any file or setting used to configure or synchronize NSCs is considered a “configuration '
                                     'file.” This includes files, automated and system-based controls, scripts, settings, '
                                     'infrastructure as code, or other parameters that are backed up, archived, or stored '
                                     'remotely.',
          'subchapter': '1.2: Network security controls (NSCs) are configured and maintained.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-04.1: Does the organization configure firewall and router configurations to deny '
                                   'network traffic by default and allow network traffic by exception (e.g., deny all, permit '
                                   'by exception)? .',
                                   'Q-NET-04: Does the organization design, implement and review firewall and router '
                                   'configurations to restrict connections between untrusted networks and internal systems? .'],
          'objective_title': '1.3.1: Inbound traffic to the CDE is restricted.',
          'requirement_description': '\n'
                                     'Inbound traffic to the CDE is restricted as follows: \n'
                                     '• To only traffic that is necessary, \n'
                                     '• All other traffic is specifically denied.',
          'subchapter': '1.3: Network access to and from the cardholder data environment is restricted.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-04.1: Does the organization configure firewall and router configurations to deny '
                                   'network traffic by default and allow network traffic by exception (e.g., deny all, permit '
                                   'by exception)? .',
                                   'Q-NET-04: Does the organization design, implement and review firewall and router '
                                   'configurations to restrict connections between untrusted networks and internal systems? .',
                                   'Q-NET-03.5: Does the organization prevent the unauthorized exfiltration of '
                                   'sensitive/regulated data across managed interfaces?.'],
          'objective_title': '1.3.2: Outbound traffic from the CDE is restricted.',
          'requirement_description': '\n'
                                     'Outbound traffic from the CDE is restricted as follows: \n'
                                     '• To only traffic that is necessary. \n'
                                     '• All other traffic is specifically denied.',
          'subchapter': '1.3: Network access to and from the cardholder data environment is restricted.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-04.1: Does the organization configure firewall and router configurations to deny '
                                   'network traffic by default and allow network traffic by exception (e.g., deny all, permit '
                                   'by exception)? .',
                                   'Q-NET-03.7: Does the organization employ boundary protections to isolate systems, services '
                                   'and process that support critical missions and/or business functions? .',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-NET-02.2: Does the organization implement and manage a secure guest network? .'],
          'objective_title': '1.3.3: NSCs are installed between all wireless networks and the CDE, regardless of whether the '
                             'wireless network is a CDE.',
          'requirement_description': '\n'
                                     'NSCs are installed between all wireless networks and the CDE, regardless of whether the '
                                     'wireless network is a CDE, such that: \n'
                                     '• All wireless traffic from wireless networks into the CDE is denied by default. \n'
                                     '• Only wireless traffic with an authorized business purpose is allowed into the CDE.',
          'subchapter': '1.3: Network access to and from the cardholder data environment is restricted.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-SEA-03: Does the organization implement security functions as a layered structure '
                                   'minimizing interactions between layers of the design and avoiding any dependence by lower '
                                   'layers on the functionality or correctness of higher layers? .',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-NET-03.8: Does the organization implement separate network addresses (e.g., different '
                                   'subnets) to connect to systems in different security domains?.',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-NET-02: Does the organization implement security functions as a layered structure that '
                                   'minimizes interactions between layers of the design and avoiding any dependence by lower '
                                   'layers on the functionality or correctness of higher layers? .',
                                   'Q-CFG-03: Does the organization configure systems to provide only essential capabilities '
                                   'by specifically prohibiting or restricting the use of ports, protocols, and/or services? '
                                   '.'],
          'objective_title': '1.4.1: NSCs are implemented between trusted and untrusted networks.',
          'requirement_description': 'NSCs are implemented between trusted and untrusted networks.',
          'subchapter': '1.4: Network connections between trusted and untrusted networks are controlled.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
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
                                   'Q-CFG-03: Does the organization configure systems to provide only essential capabilities '
                                   'by specifically prohibiting or restricting the use of ports, protocols, and/or services? '
                                   '.'],
          'objective_title': '1.4.2: Inbound traffic from untrusted networks to trusted networks is restricted.',
          'requirement_description': '\n'
                                     'Inbound traffic from untrusted networks to trusted networks is restricted to: \n'
                                     '• Communications with system components that are authorized to provide publicly '
                                     'accessible services, protocols, and ports. \n'
                                     '• Stateful responses to communications initiated by system components in a trusted '
                                     'network. \n'
                                     '• All other traffic is denied. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'The intent of this requirement is to address communication sessions between trusted and '
                                     'untrusted networks, rather than the specifics of protocols. This requirement does not '
                                     'limit the use of UDP or other connectionless network protocols if state is maintained by '
                                     'the NSC.',
          'subchapter': '1.4: Network connections between trusted and untrusted networks are controlled.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-08.2: Does the organization require wireless network segments to implement Wireless '
                                   'Intrusion Detection / Prevention Systems (WIDS/WIPS) technologies?.',
                                   'Q-NET-08: Does the organization implement Network Intrusion Detection / Prevention Systems '
                                   '(NIDS/NIPS) used to detect and/or prevent intrusions into the network? .',
                                   'Q-NET-04: Does the organization design, implement and review firewall and router '
                                   'configurations to restrict connections between untrusted networks and internal systems? .',
                                   'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS '
                                   '/ IPS) technologies on critical systems, key network segments and network choke points?.'],
          'objective_title': '1.4.3: Anti-spoofing measures are implemented to detect and block forged source IP addresses '
                             'from entering the trusted network.',
          'requirement_description': 'Anti-spoofing measures are implemented to detect and block forged source IP addresses '
                                     'from entering the trusted network.',
          'subchapter': '1.4: Network connections between trusted and untrusted networks are controlled.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-NET-05.1: Does the organization prohibit the direct connection of a sensitive system to '
                                   'an external network without the use of an organization-defined boundary protection device? '
                                   '.',
                                   'Q-DCH-15: Does the organization control publicly-accessible content?.'],
          'objective_title': '1.4.4: System components that store cardholder data are not directly accessible from untrusted '
                             'networks.',
          'requirement_description': '\n'
                                     'System components that store cardholder data are not directly accessible from untrusted '
                                     'networks. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement is not intended to apply to storage of account data in volatile memory '
                                     'but does apply where memory is being treated as persistent storage (for example, RAM '
                                     'disk). Account data can only be stored in volatile memory during the time necessary to '
                                     'support the associated business process (for example, until completion of the related '
                                     'payment card transaction).',
          'subchapter': '1.4: Network connections between trusted and untrusted networks are controlled.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-VPM-06.8: Does the organization define what information is allowed to be discoverable by '
                                   'adversaries and take corrective actions to remediated non-compliant systems?.',
                                   'Q-NET-03.3: Does the organization prevent the public disclosure of internal address '
                                   'information? .'],
          'objective_title': '1.4.5: The disclosure of internal IP addresses and routing information is limited to only '
                             'authorized parties.',
          'requirement_description': 'The disclosure of internal IP addresses and routing information is limited to only '
                                     'authorized parties.',
          'subchapter': '1.4: Network connections between trusted and untrusted networks are controlled.'},
         {'chapter_title': 'Requirement 1: Install and Maintain Network Security Controls',
          'conformity_questions': ['Q-END-05: Does the organization utilize host-based firewall software, or a similar '
                                   'technology, on all information systems, where technically feasible?.',
                                   'Q-END-02: Does the organization protect the confidentiality, integrity, availability and '
                                   'safety of endpoint devices?.',
                                   'Q-END-01: Does the organization facilitate the implementation of endpoint security '
                                   'controls?.',
                                   'Q-CFG-03.4: Does the organization prevent systems from creating split tunneling '
                                   'connections or similar techniques that could be used to exfiltrate data?.',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.'],
          'objective_title': '1.5.1: Security controls are implemented on any computing devices, including company- and '
                             'employee-owned devices, that connect to both untrusted networks (including the Internet) and the '
                             'CDE',
          'requirement_description': '\n'
                                     'Security controls are implemented on any computing devices, including company- and '
                                     'employee-owned devices, that connect to both untrusted networks (including the Internet) '
                                     'and the CDE as follows. \n'
                                     '• Specific configuration settings are defined to prevent threats being introduced into '
                                     'the entity’s network. \n'
                                     '• Security controls are actively running. \n'
                                     '• Security controls are not alterable by users of the computing devices unless '
                                     'specifically documented and authorized by management on a case-by-case basis for a '
                                     'limited period. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'These security controls may be temporarily disabled only if there is legitimate '
                                     'technical need, as authorized by management on a case-by-case basis. If these security '
                                     'controls need to be disabled for a specific purpose, it must be formally authorized. '
                                     'Additional security measures may also need to be implemented for the period during which '
                                     'these security controls are not active. This requirement applies to employee-owned and '
                                     'company-owned computing devices. Systems that cannot be managed by corporate policy '
                                     'introduce weaknesses and provide opportunities that malicious individuals may exploit.',
          'subchapter': '1.5: Risks to the CDE from computing devices that are able to connect to both untrusted networks and '
                        'the CDE are'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '2.1.1: All security policies and operational procedures that are identified in Requirement 2 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 2 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '2.1: Processes and mechanisms for applying secure configurations to all system components are defined '
                        'and unders'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '2.1.2: Roles and responsibilities for performing activities in Requirement 2 are documented, '
                             'assigned, and understood.  New requirement- effective immediately',
          'requirement_description': '\n'
                                     'Roles and responsibilities for performing activities in Requirement 2 are documented, '
                                     'assigned, and understood. \n'
                                     '* New requirement - effective immediately',
          'subchapter': '2.1: Processes and mechanisms for applying secure configurations to all system components are defined '
                        'and unders'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '2.2.1: Configuration standards are developed, implemented, and maintained',
          'requirement_description': '\n'
                                     'Configuration standards are developed, implemented, and maintained to: \n'
                                     '• Cover all system components. \n'
                                     '• Address all known security vulnerabilities. \n'
                                     '• Be consistent with industry-accepted system hardening standards or vendor hardening '
                                     'recommendations. \n'
                                     '• Be updated as new vulnerability issues are identified, as defined in Requirement '
                                     '6.3.1. \n'
                                     '• Be applied when new systems are configured and verified as in place before or '
                                     'immediately after a system component is connected to a production environment.',
          'subchapter': '2.2: System components are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-IAC-10.8: Does the organization ensure vendor-supplied defaults are changed as part of '
                                   'the installation process?.',
                                   'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, '
                                   'individual, or responsible organization level to establish a common understanding of '
                                   'requirements for asset protection?.'],
          'objective_title': '2.2.2: Vendor default accounts are managed',
          'requirement_description': '\n'
                                     'Vendor default accounts are managed as follows: \n'
                                     '• If the vendor default account(s) will be used, the default password is changed per '
                                     'Requirement 8.3.6. \n'
                                     '• If the vendor default account(s) will not be used, the account is removed or '
                                     'disabled. \n'
                                     'Applicability Notes \n'
                                     'This applies to ALL vendor default accounts and passwords, including, but not limited '
                                     'to, those used by operating systems, software that provides security services, '
                                     'application and system accounts, point-of-sale (POS) terminals, payment applications, '
                                     'and Simple Network Management Protocol (SNMP) defaults. This requirement also applies '
                                     'where a system component is not installed within an entity’s environment, for example, '
                                     'software and applications that are part of the CDE and are accessed via a cloud '
                                     'subscription service.',
          'subchapter': '2.2: System components are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-SEA-04.1: Does the organization isolate security functions from non-security functions? '
                                   '.',
                                   'Q-END-16.1: Does the organization implement underlying software separation mechanisms to '
                                   'facilitate security function isolation? .',
                                   'Q-END-16: Does the organization ensure  security functions are restricted to authorized '
                                   'individuals and enforce least privilege control requirements for necessary job '
                                   'functions?.'],
          'objective_title': '2.2.3: Primary functions requiring different security levels are managed',
          'requirement_description': '\n'
                                     'Primary functions requiring different security levels are managed as follows: \n'
                                     '• Only one primary function exists on a system component, OR \n'
                                     '• Primary functions with differing security levels that exist on the same system '
                                     'component are isolated from each other, OR \n'
                                     '• Primary functions with differing security levels on the same system component are all '
                                     'secured to the level required by the function with the highest security need.',
          'subchapter': '2.2: System components are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to '
                                   'reduce risk and exposure to threats?.',
                                   'Q-CFG-03: Does the organization configure systems to provide only essential capabilities '
                                   'by specifically prohibiting or restricting the use of ports, protocols, and/or services? .',
                                   'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, '
                                   'individual, or responsible organization level to establish a common understanding of '
                                   'requirements for asset protection?.'],
          'objective_title': '2.2.4: Only necessary services, protocols, daemons, and functions are enabled, and all '
                             'unnecessary functionality is removed or disabled.',
          'requirement_description': 'Only necessary services, protocols, daemons, and functions are enabled, and all '
                                     'unnecessary functionality is removed or disabled. ',
          'subchapter': '2.2: System components are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-TDA-02.6: Does the organization mitigate the risk associated with the use of insecure '
                                   'ports, protocols and services necessary to operate technology solutions? .',
                                   'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, '
                                   'individual, or responsible organization level to establish a common understanding of '
                                   'requirements for asset protection?.'],
          'objective_title': '2.2.5: If any insecure services, protocols, or daemons are present then i.) Business '
                             'justification is documented.ii.) Additional security features are documented and implemented '
                             'that reduce the risk of using insecure services, protocols, or daemons.',
          'requirement_description': '\n'
                                     'If any insecure services, protocols, or daemons are present: \n'
                                     '• Business justification is documented. \n'
                                     '• Additional security features are documented and implemented that reduce the risk of '
                                     'using insecure services, protocols, or daemons.',
          'subchapter': '2.2: System components are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-TDA-05.1: Does the organization secure physical diagnostic and test interfaces to '
                                   'prevent misuse?.'],
          'objective_title': '2.2.6: System security parameters are configured to prevent misuse.',
          'requirement_description': 'System security parameters are configured to prevent misuse.',
          'subchapter': '2.2: System components are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-MNT-05.3: Does the organization cryptographically protect the integrity and '
                                   'confidentiality of remote, non-local maintenance and diagnostic communications? .',
                                   'Q-CRY-06: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality and integrity of non-console administrative access?.',
                                   'Q-CRY-02: Does the organization use cryptographic mechanisms authenticate to a '
                                   'cryptographic module?.'],
          'objective_title': '2.2.7: All non-console administrative access is encrypted using strong cryptography.',
          'requirement_description': 'All non-console administrative access is encrypted using strong cryptography.\n'
                                     'Applicability Notes\n'
                                     'This includes administrative access via browser-based interfaces and application '
                                     'programming interfaces (APIs).',
          'subchapter': '2.2: System components are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-NET-15.1: Does the organization implement authentication and cryptographic mechanisms '
                                   'used to protect wireless access?.',
                                   'Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-IAC-10.8: Does the organization ensure vendor-supplied defaults are changed as part of '
                                   'the installation process?.',
                                   'Q-CRY-07: Does the organization protect wireless access via secure authentication and '
                                   'encryption?.'],
          'objective_title': '2.3.1: For wireless environments connected to the CDE or transmitting account data, all wireless '
                             'vendor defaults are changed at installation or are confirmed to be secure.',
          'requirement_description': '\n'
                                     'For wireless environments connected to the CDE or transmitting account data, all '
                                     'wireless vendor defaults are changed at installation or are confirmed to be secure, '
                                     'including but not limited to: \n'
                                     '• Default wireless encryption keys. \n'
                                     '• Passwords on wireless access points. \n'
                                     '• SNMP defaults, \n'
                                     '• Any other security-related wireless vendor defaults. \n'
                                     'Applicability Notes \n'
                                     'This includes, but is not limited to, default wireless encryption keys, passwords on '
                                     'wireless access points, SNMP defaults, and any other security-related wireless vendor '
                                     'defaults.',
          'subchapter': '2.3: Wireless environments are configured and managed securely.'},
         {'chapter_title': 'Requirement 2: Apply Secure Configurations to All System Components',
          'conformity_questions': ['Q-NET-15.1: Does the organization implement authentication and cryptographic mechanisms '
                                   'used to protect wireless access?.',
                                   'Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-CRY-09.3: Does the organization ensure the availability of information in the event of '
                                   'the loss of cryptographic keys by individual users? .',
                                   'Q-CRY-07: Does the organization protect wireless access via secure authentication and '
                                   'encryption?.'],
          'objective_title': '2.3.2: For wireless environments connected to the CDE or transmitting account data, wireless '
                             'encryption keys are changed',
          'requirement_description': '\n'
                                     'For wireless environments connected to the CDE or transmitting account data, wireless '
                                     'encryption keys are changed as follows: \n'
                                     '• Whenever personnel with knowledge of the key leave the company or the role for which '
                                     'the knowledge was necessary. \n'
                                     '• Whenever a key is suspected of or known to be compromised.',
          'subchapter': '2.3: Wireless environments are configured and managed securely.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '3.1.1: All security policies and operational procedures that are identified in Requirement 3 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 3 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '3.1: Processes and mechanisms for performing activities in Requirement 3 are defined and understood.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '3.1.2: Roles and responsibilities for performing activities in Requirement 3 are documented, '
                             'assigned, and understood.* New requirement- effective immediately',
          'requirement_description': '\n'
                                     'Roles and responsibilities for performing activities in Requirement 3 are documented, '
                                     'assigned, and understood. New requirement - effective immediately',
          'subchapter': '3.1: Processes and mechanisms for performing activities in Requirement 3 are defined and understood.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-TPM-04.4: Does the organization restrict the location of information processing/storage '
                                   'based on business requirements? .',
                                   'Q-DCH-18: Does the organization retain media and data in accordance with applicable '
                                   'statutory, regulatory and contractual obligations? .'],
          'objective_title': '3.2.1: Account data storage is kept to a minimum through implementation of data retention and '
                             'disposal policies, procedures, and processes',
          'requirement_description': '\n'
                                     'Account data storage is kept to a minimum through implementation of data retention and '
                                     'disposal policies, procedures, and processes that include at least the following: \n'
                                     '• Coverage for all locations of stored account data. \n'
                                     '• Coverage for any sensitive authentication data (SAD) stored prior to completion of '
                                     'authorization. This bullet is a best practice until its effective date; refer to '
                                     'Applicability Notes below for details. \n'
                                     '• Limiting data storage amount and retention time to that which is required for legal or '
                                     'regulatory, and/or business requirements. \n'
                                     '• Specific retention requirements for stored account data that defines length of '
                                     'retention period and includes a documented business justification. \n'
                                     '• Processes for secure deletion or rendering account data unrecoverable when no longer '
                                     'needed per the retention policy. \n'
                                     '• A process for verifying, at least once every three months, that stored account data '
                                     'exceeding the defined retention period has been securely deleted or rendered '
                                     'unrecoverable. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'Where account data is stored by a TPSP (for example, in a cloud environment), entities '
                                     'are responsible for working with their service providers to understand how the TPSP '
                                     'meets this requirement for the entity. Considerations include ensuring that all '
                                     'geographic instances of a data element are securely deleted. The bullet above (for '
                                     'coverage of SAD stored prior to completion of authorization) is a best practice until 31 '
                                     'March 2025, after which it will be required as part of Requirement 3.2.1 and must be '
                                     'fully considered during a PCI DSS assessment.',
          'subchapter': '3.2: Storage of account data is kept to a minimum.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-DCH-06.5: Does the organization prohibit the storage of sensitive authentication data '
                                   'after authorization? .'],
          'objective_title': '3.3.1: SAD is not retained after authorization, even if encrypted. All sensitive authentication '
                             'data received is rendered unrecoverable upon completion of the authorization process',
          'requirement_description': '\n'
                                     'SAD is not retained after authorization, even if encrypted. All sensitive authentication '
                                     'data received is rendered unrecoverable upon completion of the authorization process '
                                     'Applicability Notes This requirement does not apply to issuers and companies that '
                                     'support issuing services (where SAD is needed for a legitimate issuing business need) '
                                     'and have a business justification to store the sensitive authentication data. Refer to '
                                     'Requirement 3.3.3 for additional requirements specifically for issuers. Sensitive '
                                     'authentication data includes the data cited in Requirements 3.3.1.1 through 3.3.1.3.',
          'subchapter': '3.3: Sensitive authentication data is not stored after authorization.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-DCH-06.5: Does the organization prohibit the storage of sensitive authentication data '
                                   'after authorization? .'],
          'objective_title': '3.3.1.1: The full contents of any track are not retained upon completion of the authorization '
                             'process.',
          'requirement_description': '\n'
                                     'The full contents of any track are not retained upon completion of the authorization '
                                     'process. Applicability Notes In the normal course of business, the following data '
                                     'elements from the track may need to be retained: \n'
                                     '• Cardholder name. \n'
                                     '• Primary account number (PAN). \n'
                                     '• Expiration date. \n'
                                     '• Service code. \n'
                                     'To minimize risk, store securely only these data elements as needed for business.',
          'subchapter': '3.3: Sensitive authentication data is not stored after authorization.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-DCH-06.5: Does the organization prohibit the storage of sensitive authentication data '
                                   'after authorization? .'],
          'objective_title': '3.3.1.2: The card verification code is not retained upon completion of the authorization '
                             'process.',
          'requirement_description': 'The card verification code is not retained upon completion of the authorization '
                                     'process.\n'
                                     'Applicability Notes\n'
                                     'The card verification code is the three- or four-digit number printed on the front or '
                                     'back of a payment card used to verify card-not-present transactions.',
          'subchapter': '3.3: Sensitive authentication data is not stored after authorization.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-DCH-06.5: Does the organization prohibit the storage of sensitive authentication data '
                                   'after authorization? .'],
          'objective_title': '3.3.1.3: The personal identification number (PIN) and the PIN block are not retained upon '
                             'completion of the authorization process.',
          'requirement_description': 'The personal identification number (PIN) and the PIN block are not retained upon '
                                     'completion of the authorization process.\n'
                                     'Applicability Notes\n'
                                     'PIN blocks are encrypted during the natural course of transaction processes, but even if '
                                     'an entity encrypts the PIN block again, it is still not allowed to be stored after the '
                                     'completion of the authorization process.',
          'subchapter': '3.3: Sensitive authentication data is not stored after authorization.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .',
                                   'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.'],
          'objective_title': '3.3.2: SAD that is stored electronically prior to completion of authorization is encrypted using '
                             'strong cryptography.',
          'requirement_description': 'SAD that is stored electronically prior to completion of authorization is encrypted '
                                     'using strong cryptography. \n'
                                     'Applicability Notes\n'
                                     'Whether SAD is permitted to be stored prior to authorization is determined by the '
                                     'organizations that manage compliance programs (for example, payment brands and '
                                     'acquirers). Contact the organizations of interest for any additional criteria.\n'
                                     'This requirement applies to all storage of SAD, even if no PAN is present in the '
                                     'environment.\n'
                                     'Refer to Requirement 3.2.1 for an additional requirement that applies if SAD is stored '
                                     'prior to completion of authorization.\n'
                                     'This requirement does not apply to issuers and companies that support issuing services '
                                     'where there is a legitimate issuing business justification to store SAD). \n'
                                     'Refer to Requirement 3.3.3 for requirements specifically for issuers. \n'
                                     'This requirement does not replace how PIN blocks are required to be managed, nor does it '
                                     'mean that a properly encrypted PIN block needs to be encrypted again. \n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '3.3: Sensitive authentication data is not stored after authorization.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-DCH-06.5: Does the organization prohibit the storage of sensitive authentication data '
                                   'after authorization? .'],
          'objective_title': '3.3.3: Additional requirement for issuers and companies that support issuing services and store '
                             'sensitive authentication data.',
          'requirement_description': '\n'
                                     'Additional requirement for issuers and companies that support issuing services and store '
                                     'sensitive authentication data: Any storage of sensitive authentication data is: \n'
                                     '• Limited to that which is needed for a legitimate issuing business need and is '
                                     'secured. \n'
                                     '• Encrypted using strong cryptography. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement applies only to issuers and companies that support issuing services and '
                                     'store sensitive authentication data. Entities that issue payment cards or that perform '
                                     'or support issuing services will often create and control sensitive authentication data '
                                     'as part of the issuing function. It is allowable for companies that perform, facilitate, '
                                     'or support issuing services to store sensitive authentication data ONLY IF they have a '
                                     'legitimate business need to store such data. PCI DSS requirements are intended for all '
                                     'entities that store, process, or transmit account data, including issuers. The only '
                                     'exception for issuers and issuer processors is that sensitive authentication data may be '
                                     'retained if there is a legitimate reason to do so. Any such data must be stored securely '
                                     'and in accordance with all PCI DSS and specific payment brand requirements. (continued '
                                     'on next page) The bullet above (for encrypting stored SAD with strong cryptography) is a '
                                     'best practice until 31 March 2025, after which it will be required as part of '
                                     'Requirement 3.3.3 and must be fully considered during a PCI DSS assessment.',
          'subchapter': '3.3: Sensitive authentication data is not stored after authorization.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-PRI-05.3: Does the organization mask sensitive information through data anonymization, '
                                   'pseudonymization, redaction or de-identification? .',
                                   'Q-DCH-03.2: Does the organization apply data masking to sensitive information that is '
                                   'displayed or printed? .'],
          'objective_title': '3.4.1: PAN is masked when displayed (the BIN and last four digits are the maximum number of '
                             'digits to be displayed), such that only personnel with a legitimate business need can see more '
                             'than the BIN and last four digits of the PAN.',
          'requirement_description': 'PAN is masked when displayed (the BIN and last four digits are the maximum number of '
                                     'digits to be displayed), such that only personnel with a legitimate business need can '
                                     'see more than the BIN and last four digits of the PAN.\n'
                                     'Applicability Notes\n'
                                     'This requirement does not supersede stricter requirements in place for displays of '
                                     'cardholder data—for example, legal or payment brand requirements for point-of-sale (POS) '
                                     'receipts.\n'
                                     'This requirement relates to protection of PAN where it is displayed on screens, paper '
                                     'receipts, printouts, etc., and is not to be confused with Requirement 3.5.1 for '
                                     'protection of PAN when stored, processed, or transmitted. \n',
          'subchapter': '3.4: Access to displays of full PAN and ability to copy account data is restricted.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.'],
          'objective_title': '3.4.2: When using remote-access technologies, technical controls prevent copy and/or relocation '
                             'of PAN for all personnel, except for those with documented, explicit authorization and a '
                             'legitimate, defined business need.',
          'requirement_description': 'When using remote-access technologies, technical controls prevent copy and/or relocation '
                                     'of PAN for all personnel, except for those with documented, explicit authorization and a '
                                     'legitimate, defined business need.\n'
                                     'Applicability Notes\n'
                                     'Storing or relocating PAN onto local hard drives, removable electronic media, and other '
                                     'storage devices brings these devices into scope for PCI DSS.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '3.4: Access to displays of full PAN and ability to copy account data is restricted.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-DCH-01.2: Does the organization protect sensitive/regulated data wherever it is '
                                   'stored?.'],
          'objective_title': '3.5.1: PAN is rendered unreadable anywhere it is stored.',
          'requirement_description': '\n'
                                     'PAN is rendered unreadable anywhere it is stored by using any of the following '
                                     'approaches: \n'
                                     '• One-way hashes based on strong cryptography of the entire PAN. \n'
                                     '• Truncation (hashing cannot be used to replace the truncated segment of PAN). \n'
                                     '• Index tokens. \n'
                                     '• Strong cryptography with associated key-management processes and procedures. \n'
                                     '• Where hashed and truncated versions of the same PAN, or different truncation formats '
                                     'of the same PAN, are present in an environment, additional controls are in place to '
                                     'ensure that the different versions cannot be correlated to reconstruct the original '
                                     'PAN. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'It is a relatively trivial effort for a malicious individual to reconstruct original PAN '
                                     'data if they have access to both the truncated and hashed version of a PAN. This '
                                     'requirement applies to PANs stored in primary storage (databases, or flat files such as '
                                     'text files spreadsheets) as well as non-primary storage (backup, audit logs, exception, '
                                     'or troubleshooting logs) must all be protected. This requirement does not preclude the '
                                     'use of temporary files containing cleartext PAN while encrypting and decrypting PAN.',
          'subchapter': '3.5: PAN is secured wherever it is stored.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.5.1.1: Hashes used to render PAN unreadable (per the first bullet of Requirement 3.5.1), are '
                             'keyed cryptographic hashes of the entire PAN, with associated key-management processes and '
                             'procedures in accordance with Requirements 3.6 and 3.7.',
          'requirement_description': 'Hashes used to render PAN unreadable (per the first bullet of Requirement 3.5.1), are '
                                     'keyed cryptographic hashes of the entire PAN, with associated key-management processes '
                                     'and procedures in accordance with Requirements 3.6 and 3.7.\n'
                                     'Applicability Notes\n'
                                     'This requirement applies to PANs stored in primary storage (databases, or flat files '
                                     'such as text files spreadsheets) as well as non-primary storage (backup, audit logs, '
                                     'exception, or troubleshooting logs) must all be protected. \n'
                                     'This requirement does not preclude the use of temporary files containing cleartext PAN '
                                     'while encrypting and decrypting PAN. \n'
                                     'This requirement is considered a best practice until 31 March 2025, after which it will '
                                     'be required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '3.5: PAN is secured wherever it is stored.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .'],
          'objective_title': '3.5.1.2: If disk-level or partition-level encryption (rather than file-, column-, or field-level '
                             'database encryption) is used to render PAN unreadable, it is implemented only as follows.',
          'requirement_description': '\n'
                                     'If disk-level or partition-level encryption (rather than file-, column-, or field-level '
                                     'database encryption) is used to render PAN unreadable, it is implemented only as follows '
                                     ': \n'
                                     '• On removable electronic media OR \n'
                                     '• If used for non-removable electronic media, PAN is also rendered unreadable via '
                                     'another mechanism that meets Requirement 3.5.1. Note: Disk or partition encryption '
                                     'implementations must also meet all other PCI DSS encryption and key-management '
                                     'requirements. \n'
                                     'Applicability Notes \n'
                                     'While disk encryption may still be present on these types of devices, it cannot be the '
                                     'only mechanism used to protect PAN stored on those systems. Any stored PAN must also be '
                                     'rendered unreadable per Requirement 3.5.1—for example, through truncation or a '
                                     'data-level encryption mechanism. Full disk encryption helps to protect data in the event '
                                     'of physical loss of a disk and therefore its use is appropriate only for removable '
                                     'electronic media storage devices. Media that is part of a data center architecture (for '
                                     'example, hot-swappable drives, bulk tape-backups) is considered non-removable electronic '
                                     'media to which Requirement 3.5.1 applies. Disk or partition encryption implementations '
                                     'must also meet all other PCI DSS encryption and key-management requirements. This '
                                     'requirement is a best practice until 31 March 2025, after which it will be required and '
                                     'must be fully considered during a PCI DSS assessment.',
          'subchapter': '3.5: PAN is secured wherever it is stored.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .'],
          'objective_title': '3.5.1.3: If disk-level or partition-level encryption is used (rather than file-, column-, or '
                             'field--level database encryption) to render PAN unreadable, it is managed.',
          'requirement_description': '\n'
                                     'If disk-level or partition-level encryption is used (rather than file-, column-, or '
                                     'field--level database encryption) to render PAN unreadable, it is managed as follows:, \n'
                                     '• Logical access is managed separately and independently of native operating system '
                                     'authentication and access control mechanisms. \n'
                                     '• Decryption keys are not associated with user accounts. \n'
                                     '• Authentication factors (passwords, passphrases, or cryptographic keys) that allow '
                                     'access to unencrypted data are stored securely. \n'
                                     'Applicability Notes\n'
                                     ' Disk or partition encryption implementations must also meet all other PCI DSS '
                                     'encryption and key-management requirements.',
          'subchapter': '3.5: PAN is secured wherever it is stored.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09.4: Does the organization facilitate the secure distribution of symmetric and '
                                   'asymmetric cryptographic keys using industry recognized key management technology and '
                                   'processes? .',
                                   'Q-CRY-09.3: Does the organization ensure the availability of information in the event of '
                                   'the loss of cryptographic keys by individual users? .',
                                   'Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.',
                                   'Q-CRY-08.1: Does the organization have appropriate resiliency mechanisms to ensure the '
                                   'availability of data in the event of the loss of cryptographic keys?.'],
          'objective_title': '3.6.1: Procedures are defined and implemented to protect cryptographic keys used to protect '
                             'stored account data against disclosure and misuse.',
          'requirement_description': '\n'
                                     'Procedures are defined and implemented to protect cryptographic keys used to protect '
                                     'stored account data against disclosure and misuse that include: \n'
                                     '• Access to keys is restricted to the fewest number of custodians necessary. \n'
                                     '• Key-encrypting keys are at least as strong as the data-encrypting keys they protect. \n'
                                     '• Key-encrypting keys are stored separately from data-encrypting keys.\n'
                                     ' • Keys are stored securely in the fewest possible locations and forms. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement applies to keys used to encrypt stored account data and to '
                                     'key-encrypting keys used to protect data-encrypting keys. The requirement to protect '
                                     'keys used to protect stored account data from disclosure and misuse applies to both '
                                     'data-encrypting keys and key-encrypting keys. Because one key-encrypting key may grant '
                                     'access to many data-encrypting keys, the key-encrypting keys require strong protection '
                                     'measures.',
          'subchapter': '3.6: Cryptographic keys used to protect stored account data are secured.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-IAC-12: Does the organization ensure cryptographic modules adhere to applicable '
                                   'statutory, regulatory and contractual requirements for security strength?.',
                                   'Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.',
                                   'Q-CRY-02: Does the organization use cryptographic mechanisms authenticate to a '
                                   'cryptographic module?.'],
          'objective_title': '3.6.1.1: Additional requirement for service providers only: A documented description of the '
                             'cryptographic architecture is maintained.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: A documented description of the '
                                     'cryptographic architecture is maintained that includes: \n'
                                     '• Details of all algorithms, protocols, and keys used for the protection of stored '
                                     'account data, including key strength and expiry date. \n'
                                     '• Preventing the use of the same cryptographic keys in production and test environments. '
                                     'This bullet is a best practice until its effective date; refer to \n'
                                     'Applicability Notes below for details. \n'
                                     '• Description of the key usage for each key. \n'
                                     '• Inventory of any hardware security modules (HSMs), key management systems (KMS), and '
                                     'other secure cryptographic devices (SCDs) used for key management, including type and '
                                     'location of devices, as outlined in Requirement 12.3.4. Applicability Notes This '
                                     'requirement applies only when the entity being assessed is a service provider. In cloud '
                                     'HSM implementations, responsibility for the cryptographic architecture according to this '
                                     'Requirement will be shared between the cloud provider and the cloud customer. The bullet '
                                     'above (for including, in the cryptographic architecture, that the use of the same '
                                     'cryptographic keys in production and test is prevented) is a best practice until 31 '
                                     'March 2025, after which it will be required as part of Requirement 3.6.1.1 and must be '
                                     'fully considered during a PCI DSS assessment.',
          'subchapter': '3.6: Cryptographic keys used to protect stored account data are secured.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-IAC-12: Does the organization ensure cryptographic modules adhere to applicable '
                                   'statutory, regulatory and contractual requirements for security strength?.',
                                   'Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.',
                                   'Q-CRY-02: Does the organization use cryptographic mechanisms authenticate to a '
                                   'cryptographic module?.'],
          'objective_title': '3.6.1.2: Secret and private keys used to encrypt/decrypt stored account data are stored.',
          'requirement_description': '\n'
                                     'Secret and private keys used to encrypt/decrypt stored account data are stored in one '
                                     '(or more) of the following forms at all times: \n'
                                     '• Encrypted with a key-encrypting key that is at least as strong as the data-encrypting '
                                     'key, and that is stored separately from the data-encrypting key. \n'
                                     '• Within a secure cryptographic device (SCD), such as a hardware security module (HSM) '
                                     'or PTS-approved point-of-interaction device. \n'
                                     '• As at least two full-length key components or key shares, in accordance with an '
                                     'industry-accepted method. \n'
                                     'Applicability Notes\n'
                                     ' It is not required that public keys be stored in one of these forms. Cryptographic keys '
                                     'stored as part of a key management system (KMS) that employs SCDs are acceptable. A '
                                     'cryptographic key that is split into two parts does not meet this requirement. Secret or '
                                     'private keys stored as key components or key shares must be generated via one of the '
                                     'following: \n'
                                     '• Using an approved random number generator and within an SCD, OR \n'
                                     '• According to ISO 19592 or equivalent industry standard for generation of secret key '
                                     'shares.',
          'subchapter': '3.6: Cryptographic keys used to protect stored account data are secured.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.6.1.3: Access to cleartext cryptographic key components is restricted to the fewest number of '
                             'custodians necessary.',
          'requirement_description': 'Access to cleartext cryptographic key components is restricted to the fewest number of '
                                     'custodians necessary.',
          'subchapter': '3.6: Cryptographic keys used to protect stored account data are secured.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.6.1.4: Cryptographic keys are stored in the fewest possible locations.',
          'requirement_description': 'Cryptographic keys are stored in the fewest possible locations. ',
          'subchapter': '3.6: Cryptographic keys used to protect stored account data are secured.'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.7.1: Key-management policies and procedures are implemented to include generation of strong '
                             'cryptographic keys used to protect stored account data.',
          'requirement_description': 'Key-management policies and procedures are implemented to include generation of strong '
                                     'cryptographic keys used to protect stored account data.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.7.2: Key-management policies and procedures are implemented to include secure distribution of '
                             'cryptographic keys used to protect stored account data.',
          'requirement_description': 'Key-management policies and procedures are implemented to include secure distribution of '
                                     'cryptographic keys used to protect stored account data.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-IAC-12: Does the organization ensure cryptographic modules adhere to applicable '
                                   'statutory, regulatory and contractual requirements for security strength?.',
                                   'Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.',
                                   'Q-CRY-02: Does the organization use cryptographic mechanisms authenticate to a '
                                   'cryptographic module?.'],
          'objective_title': '3.7.3: Key-management policies and procedures are implemented to include secure storage of '
                             'cryptographic keys used to protect stored account data.',
          'requirement_description': 'Key-management policies and procedures are implemented to include secure storage of '
                                     'cryptographic keys used to protect stored account data.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.7.4: Key management policies and procedures are implemented for cryptographic key changes for '
                             'keys that have reached the end of their cryptoperiod, as defined by the associated application '
                             'vendor or key owner, and based on industry best practices and guidelines',
          'requirement_description': '\n'
                                     'Key management policies and procedures are implemented for cryptographic key changes for '
                                     'keys that have reached the end of their cryptoperiod, as defined by the associated '
                                     'application vendor or key owner, and based on industry best practices and guidelines, '
                                     'including the following: \n'
                                     '• A defined cryptoperiod for each key type in use. \n'
                                     '• A process for key changes at the end of the defined cryptoperiod.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09.3: Does the organization ensure the availability of information in the event of '
                                   'the loss of cryptographic keys by individual users? .',
                                   'Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.',
                                   'Q-CRY-04: Does the organization use cryptographic mechanisms to protect the integrity of '
                                   'data being transmitted? .'],
          'objective_title': '3.7.5: Key management policies procedures are implemented to include the retirement, '
                             'replacement, or destruction of keys used to protect stored account data.',
          'requirement_description': '\n'
                                     'Key management policies procedures are implemented to include the retirement, '
                                     'replacement, or destruction of keys used to protect stored account data, as deemed '
                                     'necessary when: \n'
                                     '• The key has reached the end of its defined cryptoperiod. \n'
                                     '• The integrity of the key has been weakened, including when personnel with knowledge of '
                                     'a cleartext key component leaves the company, or the role for which the key component '
                                     'was known. \n'
                                     '• The key is suspected of or known to be compromised. Retired or replaced keys are not '
                                     'used for encryption operations. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' If retired or replaced cryptographic keys need to be retained, these keys must be '
                                     'securely archived (for example, by using a key-encryption key).',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.7.6: Where manual cleartext cryptographic key-management operations are performed by '
                             'personnel, key-management policies and procedures are implemented include managing these '
                             'operations using split knowledge and dual control.',
          'requirement_description': '\n'
                                     'Where manual cleartext cryptographic key-management operations are performed by '
                                     'personnel, key-management policies and procedures are implemented include managing these '
                                     'operations using split knowledge and dual control. \n'
                                     'Applicability Notes\n'
                                     ' This control is applicable for manual key-management operations or where key management '
                                     'is not controlled by the encryption product. A cryptographic key that is simply split '
                                     'into two parts does not meet this requirement. Secret or private keys stored as key '
                                     'components or key shares must be generated via one of the following: \n'
                                     '• Using an approved random number generator and within a secure cryptographic device '
                                     '(SCD), such as a hardware security module (HSM) or PTS-approved point-of-interaction '
                                     'device, OR \n'
                                     '• According to ISO 19592 or equivalent industry standard for generation of secret key '
                                     'shares.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': '3.7.7: Key management policies and procedures are implemented to include the prevention of '
                             'unauthorized substitution of cryptographic keys.',
          'requirement_description': 'Key management policies and procedures are implemented to include the prevention of '
                                     'unauthorized substitution of cryptographic keys.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? '
                                   '.'],
          'objective_title': '3.7.8: Key management policies and procedures are implemented to include that cryptographic key '
                             'custodians formally acknowledge (in writing or electronically) that they understand and accept '
                             'their key-custodian responsibilities.',
          'requirement_description': 'Key management policies and procedures are implemented to include that cryptographic key '
                                     'custodians formally acknowledge (in writing or electronically) that they understand and '
                                     'accept their key-custodian responsibilities.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 3: Protect Stored Account Data',
          'conformity_questions': ['Q-CRY-09.6: Does the organization ensure customers are provided with appropriate key '
                                   'management guidance whenever cryptographic keys are shared?.'],
          'objective_title': '3.7.9: Additional requirement for service providers only: Where a service provider shares '
                             'cryptographic keys with its customers for transmission or storage of account data, guidance on '
                             'secure transmission, storage and updating of such keys is documented and distributed to the '
                             "service provider's customers.",
          'requirement_description': 'Additional requirement for service providers only: Where a service provider shares '
                                     'cryptographic keys with its customers for transmission or storage of account data, '
                                     'guidance on secure transmission, storage and updating of such keys is documented and '
                                     "distributed to the service provider's customers.\n"
                                     'Applicability Notes\n'
                                     'This requirement applies only when the entity being assessed is a service provider.',
          'subchapter': '3.7: Where cryptography is used to protect stored account data, key management processes and '
                        'procedures covering'},
         {'chapter_title': 'Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '4.1.1: All security policies and operational procedures that are identified in Requirement 4 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 4 '
                                     'are: \n'
                                     '• Documented \n'
                                     '• Kept up to date \n'
                                     '• In use \n'
                                     '• Known to all affected parties',
          'subchapter': '4.1: Processes and mechanisms for performing activities in Requirement 4 are defined and documented.'},
         {'chapter_title': 'Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '4.1.2: Roles and responsibilities for performing activities in Requirement 4 are documented, '
                             'assigned, and understood.  New requirement- effective immediately',
          'requirement_description': 'Roles and responsibilities for performing activities in Requirement 4 are documented, '
                                     'assigned, and understood. \n'
                                     'New requirement - effective immediately',
          'subchapter': '4.1: Processes and mechanisms for performing activities in Requirement 4 are defined and documented.'},
         {'chapter_title': 'Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission',
          'conformity_questions': ['Q-NET-15.1: Does the organization implement authentication and cryptographic mechanisms '
                                   'used to protect wireless access?.',
                                   'Q-NET-12: Does the organization use strong cryptography and security protocols to '
                                   'safeguard sensitive/regulated data during transmission over open, public networks?.'],
          'objective_title': '4.2.1: Strong cryptography and security protocols are implemented to safeguard PAN during '
                             'transmission over open, public networks.',
          'requirement_description': '\n'
                                     'Strong cryptography and security protocols are implemented as follows to safeguard PAN '
                                     'during transmission over open, public networks: \n'
                                     '• Only trusted keys and certificates are accepted. \n'
                                     '• Certificates used to safeguard PAN during transmission over open, public networks are '
                                     'confirmed as valid and are not expired or revoked. This bullet is a best practice until '
                                     'its effective date; refer to applicability notes below for details. \n'
                                     '• The protocol in use supports only secure versions or configurations and does not '
                                     'support fallback to, or use of insecure versions, algorithms, key sizes, or '
                                     'implementations. \n'
                                     '• The encryption strength is appropriate for the encryption methodology in use. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' There could be occurrences where an entity receives cardholder data unsolicited via an '
                                     'insecure communication channel that was not intended for the purpose of receiving '
                                     'sensitive data. In this situation, the entity can choose to either include the channel '
                                     'in the scope of their CDE and secure it according to PCI DSS or implement measures to '
                                     'prevent the channel from being used for cardholder data. A self-signed certificate may '
                                     'also be acceptable if the certificate is issued by an internal CA within the '
                                     'organization, the certificate’s author is confirmed, and the certificate is verified—for '
                                     'example, via hash or signature—and has not expired. Note that self-signed certificates '
                                     'where the Distinguished Name (DN) field in the “issued by” and “issued to” field is the '
                                     'same are not acceptable. The bullet above (for confirming that certificates used to '
                                     'safeguard PAN during transmission over open, public networks are valid and are not '
                                     'expired or revoked) is a best practice until 31 March 2025, after which it will be '
                                     'required as part of Requirement 4.2.1 and must be fully considered during a PCI DSS '
                                     'assessment.',
          'subchapter': '4.2: PAN is protected with strong cryptography during transmission.'},
         {'chapter_title': 'Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission',
          'conformity_questions': ['Q-CRY-09: Does the organization facilitate cryptographic key management controls to '
                                   'protect the confidentiality, integrity and availability of keys?.'],
          'objective_title': "4.2.1.1: An inventory of the entity's trusted keys and certificates is maintained.",
          'requirement_description': 'An inventory of the entity’s trusted keys and certificates is maintained.\n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.\n',
          'subchapter': '4.2: PAN is protected with strong cryptography during transmission.'},
         {'chapter_title': 'Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission',
          'conformity_questions': ['Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-CRY-07: Does the organization protect wireless access via secure authentication and '
                                   'encryption?.',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .'],
          'objective_title': '4.2.1.2: Wireless networks transmitting PAN or connected to the CDE use industry best practices '
                             'to implement strong cryptography for authentication and transmission.',
          'requirement_description': 'Wireless networks transmitting PAN or connected to the CDE use industry best practices '
                                     'to implement strong cryptography for authentication and transmission. ',
          'subchapter': '4.2: PAN is protected with strong cryptography during transmission.'},
         {'chapter_title': 'Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission',
          'conformity_questions': ['Q-NET-12.2: Does the organization prohibit the transmission of unprotected '
                                   'sensitive/regulated data by end-user messaging technologies?.'],
          'objective_title': '4.2.2: PAN is secured with strong cryptography whenever it is sent via end-user messaging '
                             'technologies.',
          'requirement_description': 'PAN is secured with strong cryptography whenever it is sent via end-user messaging '
                                     'technologies.\n'
                                     'Applicability Notes\n'
                                     'This requirement also applies if a customer, or other third-party, requests that PAN is '
                                     'sent to them via end-user messaging technologies.\n'
                                     'There could be occurrences where an entity receives unsolicited cardholder data via an '
                                     'insecure communication channel that was not intended for transmissions of sensitive '
                                     'data. In this situation, the entity can choose to either include the channel in the '
                                     'scope of their CDE and secure it according to PCI DSS or delete the cardholder data and '
                                     'implement measures to prevent the channel from being used for cardholder data.\n',
          'subchapter': '4.2: PAN is protected with strong cryptography during transmission.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '5.1.1: All security policies and operational procedures that are identified in Requirement 5 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': 'All security policies and operational procedures that are identified in Requirement 5 '
                                     'are:\n'
                                     '•\t Documented\n'
                                     '•\t Kept up to date\n'
                                     '•\t In use\n'
                                     '•\t Known to all affected parties',
          'subchapter': '5.1: Processes and mechanisms for protecting all systems and networks from malicious software are '
                        'defined and un'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-END-04.2: Does the organization document antimalware technologies?.',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '5.1.2: Roles and responsibilities for performing activities in Requirement 5 are documented, '
                             'assigned, and understood.  New requirement- effective immediately',
          'requirement_description': 'Roles and responsibilities for performing activities in Requirement 5 are documented, '
                                     'assigned, and understood. \n'
                                     'New requirement - effective immediately',
          'subchapter': '5.1: Processes and mechanisms for protecting all systems and networks from malicious software are '
                        'defined and un'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.2.1: An anti-malware solution(s) is deployed on all system components, except for those system '
                             'components identified in periodic evaluations per Requirement 5.2.3 that concludes the system '
                             'components are not at risk from malware.',
          'requirement_description': 'An anti-malware solution(s) is deployed on all system components, except for those '
                                     'system components identified in periodic evaluations per Requirement 5.2.3 that '
                                     'concludes the system components are not at risk from malware.',
          'subchapter': '5.2: Malicious software (malware) is prevented, or detected and addressed.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.2.2: The deployed anti-malware solution(s), detects all known types of malware and removes, '
                             'blocks, or contains all known types of malware.',
          'requirement_description': 'The deployed anti-malware solution(s):\n'
                                     '•\t Detects all known types of malware.\n'
                                     '•\t Removes, blocks, or contains all known types of malware. ',
          'subchapter': '5.2: Malicious software (malware) is prevented, or detected and addressed.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.6: Does the organization perform periodic evaluations evolving malware threats to '
                                   'assess systems that are generally not considered to be commonly affected by malicious '
                                   'software? .'],
          'objective_title': '5.2.3: Any system components that are not at risk for malware are evaluated periodically.',
          'requirement_description': '\n'
                                     'Any system components that are not at risk for malware are evaluated periodically to '
                                     'include the following: \n'
                                     '• A documented list of all system components not at risk for malware. \n'
                                     '• Identification and evaluation of evolving malware threats for those system '
                                     'components. \n'
                                     '• Confirmation whether such system components continue to not require anti-malware '
                                     'protection. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' System components covered by this requirement are those for which there is no '
                                     'anti-malware solution deployed per Requirement 5.2.1.',
          'subchapter': '5.2: Malicious software (malware) is prevented, or detected and addressed.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.6: Does the organization perform periodic evaluations evolving malware threats to '
                                   'assess systems that are generally not considered to be commonly affected by malicious '
                                   'software? .'],
          'objective_title': '5.2.3.1: The frequency of periodic evaluations of system components identified as not at risk '
                             "for malware is defined in the entity's targeted risk analysis, which is performed according to "
                             'all elements specified in Requirement 12.3.1.',
          'requirement_description': 'The frequency of periodic evaluations of system components identified as not at risk for '
                                     'malware is defined in the entity’s targeted risk analysis, which is performed according '
                                     'to all elements specified in Requirement 12.3.1. \n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '5.2: Malicious software (malware) is prevented, or detected and addressed.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.1: Does the organization automatically update antimalware technologies, including '
                                   'signature definitions? .',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.3.1: The anti-malware solution(s) is kept current via automatic updates.',
          'requirement_description': 'The anti-malware solution(s) is kept current via automatic updates.',
          'subchapter': '5.3: Anti-malware mechanisms and processes are active, maintained, and monitored.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.7: Does the organization ensure that anti-malware technologies are continuously '
                                   'running and cannot be disabled or altered by non-privileged users, unless specifically '
                                   'authorized by management on a case-by-case basis for a limited time period? .',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.3.2: The anti-malware solution(s):- Performs periodic scans and active or real-time scans OR- '
                             'Performs continuous behavioral analysis of systems or processes.',
          'requirement_description': 'The anti-malware solution(s):\n'
                                     '•\t Performs periodic scans and active or real-time scans\n'
                                     'OR \n'
                                     '•\t Performs continuous behavioral analysis of systems or processes.',
          'subchapter': '5.3: Anti-malware mechanisms and processes are active, maintained, and monitored.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.7: Does the organization ensure that anti-malware technologies are continuously '
                                   'running and cannot be disabled or altered by non-privileged users, unless specifically '
                                   'authorized by management on a case-by-case basis for a limited time period? .',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.3.2.1: If periodic malware scans are performed to meet Requirement 5.3.2, the frequency of '
                             "scans is defined in the entity's targeted risk analysis, which is performed according to all "
                             'elements specified in Requirement 12.3.1.',
          'requirement_description': 'If periodic malware scans are performed to meet Requirement 5.3.2, the frequency of '
                                     'scans is defined in the entity’s targeted risk analysis, which is performed according to '
                                     'all elements specified in Requirement 12.3.1. \n'
                                     'Applicability Notes\n'
                                     'This requirement applies to entities conducting periodic malware scans to meet '
                                     'Requirement 5.3.2.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '5.3: Anti-malware mechanisms and processes are active, maintained, and monitored.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.7: Does the organization ensure that anti-malware technologies are continuously '
                                   'running and cannot be disabled or altered by non-privileged users, unless specifically '
                                   'authorized by management on a case-by-case basis for a limited time period? .',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.3.3: For removable electronic media, the anti-malware solution(s): - Performs automatic scans '
                             'of when the media is inserted, connected, or logically mounted, OR- Performs continuous '
                             'behavioral analysis of systems or processes when the media is inserted, connected, or logically '
                             'mounted.',
          'requirement_description': '\n'
                                     'For removable electronic media, the anti-malware solution(s): \n'
                                     '• Performs automatic scans of when the media is inserted, connected, or logically '
                                     'mounted, OR \n'
                                     '• Performs continuous behavioral analysis of systems or processes when the media is '
                                     'inserted, connected, or logically mounted.\n'
                                     ' \n'
                                     ' Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '5.3: Anti-malware mechanisms and processes are active, maintained, and monitored.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.3: Does the organization centrally-manage antimalware technologies?.',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.3.4: Audit logs for the anti-malware solution(s) are enabled and retained in accordance with '
                             'Requirement 10.5.1.',
          'requirement_description': 'Audit logs for the anti-malware solution(s) are enabled and retained in accordance with '
                                     'Requirement 10.5.1.',
          'subchapter': '5.3: Anti-malware mechanisms and processes are active, maintained, and monitored.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-04.7: Does the organization ensure that anti-malware technologies are continuously '
                                   'running and cannot be disabled or altered by non-privileged users, unless specifically '
                                   'authorized by management on a case-by-case basis for a limited time period? .',
                                   'Q-END-04: Does the organization utilize antimalware technologies to detect and eradicate '
                                   'malicious code?.'],
          'objective_title': '5.3.5: Anti-malware mechanisms cannot be disabled or altered by users, unless specifically '
                             'documented, and authorized by management on a case-by-case basis for a limited time period.',
          'requirement_description': 'Anti-malware mechanisms cannot be disabled or altered by users, unless specifically '
                                     'documented, and authorized by management on a case-by-case basis for a limited time '
                                     'period. \n'
                                     'Applicability Notes\n'
                                     'Anti-malware solutions may be temporarily disabled only if there is a legitimate '
                                     'technical need, as authorized by management on a case-by-case basis. If anti-malware '
                                     'protection needs to be disabled for a specific purpose, it must be formally authorized. '
                                     'Additional security measures may also need to be implemented for the period during which '
                                     'anti-malware protection is not active.',
          'subchapter': '5.3: Anti-malware mechanisms and processes are active, maintained, and monitored.'},
         {'chapter_title': 'Requirement 5: Protect All Systems and Networks from Malicious Software',
          'conformity_questions': ['Q-END-08: Does the organization utilize anti-phishing and spam protection technologies to '
                                   'detect and take action on unsolicited messages transported by electronic mail?.'],
          'objective_title': '5.4.1: Processes and automated mechanisms are in place to detect and protect personnel against '
                             'phishing attacks.',
          'requirement_description': 'Processes and automated mechanisms are in place to detect and protect personnel against '
                                     'phishing attacks. \n'
                                     'Applicability Notes\n'
                                     'This requirement applies to the automated mechanism. It is not intended that the systems '
                                     'and services providing such automated mechanisms (such as email servers) are brought '
                                     'into scope for PCI DSS.\n'
                                     'The focus of this requirement is on protecting personnel with access to system '
                                     'components in-scope for PCI DSS.\n'
                                     'Meeting this requirement for technical and automated controls to detect and protect '
                                     'personnel against phishing is not the same as Requirement 12.6.3.1 for security '
                                     'awareness training. Meeting this requirement does not also meet the requirement for '
                                     'providing personnel with security awareness training, and vice versa.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '5.4: Anti-phishing mechanisms protect users against phishing attacks.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '6.1.1: All security policies and operational procedures that are identified in Requirement 6 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 6 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '6.1: Processes and mechanisms for developing and maintaining secure systems and software are defined '
                        'and underst'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '6.1.2: Roles and responsibilities for performing activities in Requirement 6 are documented, '
                             'assigned, and understood.  New requirement- effective immediately.',
          'requirement_description': 'Roles and responsibilities for performing activities in Requirement 6 are documented, '
                                     'assigned, and understood. \n'
                                     'New requirement - effective immediately',
          'subchapter': '6.1: Processes and mechanisms for developing and maintaining secure systems and software are defined '
                        'and underst'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
                                   'Q-TDA-05: Does the organization require the developers of systems, system components or '
                                   'services to produce a design specification and security architecture that:   -  Is '
                                   "consistent with and supportive of the organization's security architecture which is "
                                   "established within and is an integrated part of the organization's enterprise "
                                   'architecture;  -  Accurately and completely describes the required security functionality '
                                   'and the allocation of security controls among physical and logical components; and  -  '
                                   'Expresses how individual security functions, mechanisms and services work together to '
                                   'provide required security capabilities and a unified approach to protection?.',
                                   'Q-TDA-02.3: Does the organization require software vendors/manufacturers to demonstrate '
                                   'that their software development processes employ industry-recognized secure practices for '
                                   'secure programming, engineering methods, quality control processes and validation '
                                   'techniques to minimize flawed or malformed software?.',
                                   'Q-TDA-01: Does the organization facilitate the implementation of tailored development and '
                                   'acquisition strategies, contract tools and procurement methods to meet unique business '
                                   'needs?.',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '6.2.1: Bespoke and custom software are developed securely.',
          'requirement_description': '\n'
                                     'Bespoke and custom software are developed securely, as follows: \n'
                                     '• Based on industry standards and/or best practices for secure development. \n'
                                     '• In accordance with PCI DSS (for example, secure authentication and logging). \n'
                                     '• Incorporating consideration of information security issues during each stage of the '
                                     'software development lifecycle. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This applies to all software developed for or by the entity for the entity’s own use. '
                                     'This includes both bespoke and custom software. This does not apply to third-party '
                                     'software.',
          'subchapter': '6.2: Bespoke and custom software is developed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-TDA-13: Does the organization ensure that the developers of systems, applications and/or '
                                   'services have the requisite skillset and appropriate access authorizations?.',
                                   'Q-TDA-06.3: Does the organization utilize a Software Assurance Maturity Model (SAMM) to '
                                   'govern a secure development lifecycle for the development of systems, applications and '
                                   'services?.',
                                   'Q-SAT-03.8: Does the organization ensure application development and operations (DevOps) '
                                   'personnel receive Continuing Professional Education (CPE) training on Secure Software '
                                   'Development Practices (SSDP) to appropriately address evolving threats?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.',
                                   'Q-HRS-03.2: Does the organization ensure that all security-related positions are staffed '
                                   'by qualified individuals who have the necessary skill set? .'],
          'objective_title': '6.2.2: Software development personnel working on bespoke and custom software are trained at '
                             'least once every 12 months.',
          'requirement_description': '\n'
                                     'Software development personnel working on bespoke and custom software are trained at '
                                     'least once every 12 months as follows: \n'
                                     '• On software security relevant to their job function and development languages. \n'
                                     '• Including secure software design and secure coding techniques. \n'
                                     '• Including, if security testing tools are used, how to use the tools for detecting '
                                     'vulnerabilities in software. \n'
                                     ' \n'
                                     'Applicability Notes: \n'
                                     'This requirement for code reviews applies to all bespoke and custom software (both '
                                     'internal and public facing), as part of the system development lifecycle. Public-facing '
                                     'web applications are also subject to additional controls, to address ongoing threats and '
                                     'vulnerabilities after implementation, as defined at PCI DSS Requirement 6.4. Code '
                                     'reviews may be performed using either manual or automated processes, or a combination of '
                                     'both.',
          'subchapter': '6.2: Bespoke and custom software is developed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-TDA-09: Does the organization require system developers/integrators consult with '
                                   'cybersecurity and privacy personnel to:   -  Create and implement a Security Test and '
                                   'Evaluation (ST&E) plan;  -  Implement a verifiable flaw remediation process to correct '
                                   'weaknesses and deficiencies identified during the security testing and evaluation process; '
                                   'and  -  Document the results of the security testing/evaluation and flaw remediation '
                                   'processes?.',
                                   'Q-TDA-06.5: Does the organization have an independent review of the software design to '
                                   'confirm that all cybersecurity and privacy requirements are met and that any identified '
                                   'risks are satisfactorily addressed?.',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '6.2.3: Bespoke and custom software is reviewed prior to being released into production or to '
                             'customers, to identify and correct potential coding vulnerabilities.',
          'requirement_description': '\n'
                                     'Bespoke and custom software is reviewed prior to being released into production or to '
                                     'customers, to identify and correct potential coding vulnerabilities, as follows: \n'
                                     '• Code reviews ensure code is developed according to secure coding guidelines. \n'
                                     '• Code reviews look for both existing and emerging software vulnerabilities. \n'
                                     '• Appropriate corrections are implemented prior to release.',
          'subchapter': '6.2: Bespoke and custom software is developed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-TDA-09: Does the organization require system developers/integrators consult with '
                                   'cybersecurity and privacy personnel to:   -  Create and implement a Security Test and '
                                   'Evaluation (ST&E) plan;  -  Implement a verifiable flaw remediation process to correct '
                                   'weaknesses and deficiencies identified during the security testing and evaluation process; '
                                   'and  -  Document the results of the security testing/evaluation and flaw remediation '
                                   'processes?.',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '6.2.3.1: If manual code reviews are performed for bespoke and custom software prior to release '
                             'to production.',
          'requirement_description': '\n'
                                     'If manual code reviews are performed for bespoke and custom software prior to release to '
                                     'production, code changes are: \n'
                                     '• Reviewed by individuals other than the originating code author, and who are '
                                     'knowledgeable about code-review techniques and secure coding practices.\n'
                                     ' • Reviewed and approved by management prior to release. \n'
                                     'Applicability Notes\n'
                                     ' Manual code reviews can be conducted by knowledgeable internal personnel or '
                                     'knowledgeable third-party personnel. An individual that has been formally granted '
                                     'accountability for release control and who is neither the original code author nor the '
                                     'code reviewer fulfills the criteria of being management.',
          'subchapter': '6.2: Bespoke and custom software is developed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-TDA-09.5: Does the organization perform application-level penetration testing of '
                                   'custom-made applications and services?.',
                                   'Q-TDA-09.4: Does the organization utilize testing methods to ensure systems, services and '
                                   'products continue to operate as intended when subject to invalid or unexpected inputs on '
                                   'its interfaces?.',
                                   'Q-TDA-09.3: Does the organization require the developers of systems, system components or '
                                   'services to employ dynamic code analysis tools to identify and remediate common flaws and '
                                   'document the results of the analysis? .',
                                   'Q-TDA-09.2: Does the organization require the developers of systems, system components or '
                                   'services to employ static code analysis tools to identify and remediate common flaws and '
                                   'document the results of the analysis? .',
                                   'Q-TDA-09: Does the organization require system developers/integrators consult with '
                                   'cybersecurity and privacy personnel to:   -  Create and implement a Security Test and '
                                   'Evaluation (ST&E) plan;  -  Implement a verifiable flaw remediation process to correct '
                                   'weaknesses and deficiencies identified during the security testing and evaluation process; '
                                   'and  -  Document the results of the security testing/evaluation and flaw remediation '
                                   'processes?.',
                                   'Q-TDA-06: Does the organization develop applications based on secure coding principles? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '6.2.4: Software engineering techniques or other methods are defined and in use by software '
                             'development personnel to prevent or mitigate common software attacks and related vulnerabilities '
                             'for bespoke and custom software.',
          'requirement_description': '\n'
                                     'Software engineering techniques or other methods are defined and in use by software '
                                     'development personnel to prevent or mitigate common software attacks and related '
                                     'vulnerabilities for bespoke and custom software, including but not limited to the '
                                     'following: \n'
                                     '• Injection attacks, including SQL, LDAP, XPath, or other command, parameter, object, '
                                     'fault, or injection-type flaws. \n'
                                     '• Attacks on data and data structures, including attempts to manipulate buffers, '
                                     'pointers, input data, or shared data. \n'
                                     '• Attacks on cryptography usage, including attempts to exploit weak, insecure, or '
                                     'inappropriate cryptographic implementations, algorithms, cipher suites, or modes of '
                                     'operation. • Attacks on business logic, including attempts to abuse or bypass '
                                     'application features and functionalities through the manipulation of APIs, communication '
                                     'protocols and channels, client-side functionality, or other system/application functions '
                                     'and resources. This includes cross-site scripting (XSS) and cross-site request forgery '
                                     '(CSRF). \n'
                                     '• Attacks on access control mechanisms, including attempts to bypass or abuse '
                                     'identification, authentication, or authorization mechanisms, or attempts to exploit '
                                     'weaknesses in the implementation of such mechanisms. \n'
                                     '• Attacks via any “high-risk” vulnerabilities identified in the vulnerability '
                                     'identification process, as defined in Requirement 6.3.1. Applicability Notes This '
                                     'applies to all software developed for or by the entity for the entity’s own use. This '
                                     'includes both bespoke and custom software. This does not apply to third-party software.',
          'subchapter': '6.2: Bespoke and custom software is developed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
                                   'Q-VPM-03: Does the organization identify and assign a risk ranking to newly discovered '
                                   'security vulnerabilities using reputable outside sources for security vulnerability '
                                   'information? .',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.',
                                   'Q-VPM-01: Does the organization facilitate the implementation and monitoring of '
                                   'vulnerability management controls?.',
                                   'Q-THR-06: Does the organization establish a Vulnerability Disclosure Program (VDP) to '
                                   'assist with the secure development and maintenance of products and services that receives '
                                   'unsolicited input from the public about vulnerabilities in organizational systems, '
                                   'services and processes?.',
                                   'Q-THR-03: Does the organization maintain situational awareness of evolving threats?.',
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.',
                                   'Q-GOV-07: Does the organization establish contact with selected groups and associations '
                                   'within the cybersecurity & privacy communities to:   -  Facilitate ongoing cybersecurity '
                                   'and privacy education and training for organizational personnel;  -  Maintain currency '
                                   'with recommended cybersecurity and privacy practices, techniques and technologies; and  -  '
                                   'Share current security-related information including threats, vulnerabilities and '
                                   'incidents? .'],
          'objective_title': '6.3.1: Security vulnerabilities are identified and managed.',
          'requirement_description': '\n'
                                     'Security vulnerabilities are identified and managed as follows: \n'
                                     '• New security vulnerabilities are identified using industry-recognized sources for '
                                     'security vulnerability information, including alerts from international and national '
                                     'computer emergency response teams (CERTs). \n'
                                     '• Vulnerabilities are assigned a risk ranking based on industry best practices and '
                                     'consideration of potential impact. \n'
                                     '• Risk rankings, at a minimum, identify all vulnerabilities considered to be a high-risk '
                                     'or critical to the environment. \n'
                                     '• Vulnerabilities for bespoke and custom, and third-party software (for example '
                                     'operating systems and databases) are covered. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement is not achieved by, nor is it the same as, vulnerability scans '
                                     'performed for Requirements 11.3.1 and 11.3.2. This requirement is for a process to '
                                     'actively monitor industry sources for vulnerability information and for the entity to '
                                     'determine the risk ranking to be associated with each vulnerability.',
          'subchapter': '6.3: Security vulnerabilities are identified and addressed.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.',
                                   'Q-TDA-04.2: Does the organization require a Software Bill of Materials (SBOM) for systems, '
                                   'applications and services that lists software packages in use, including versions and '
                                   'applicable licenses?.',
                                   'Q-AST-04.2: Does the organization ensure control applicability is appropriately-determined '
                                   'for systems, applications, services and third parties by graphically representing '
                                   'applicable boundaries?.',
                                   'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-AST-01: Does the organization facilitate the implementation of asset management '
                                   'controls?.'],
          'objective_title': '6.3.2: An inventory of bespoke and custom software, and third-party software components '
                             'incorporated into bespoke and custom software is maintained to facilitate vulnerability and '
                             'patch management.',
          'requirement_description': 'An inventory of bespoke and custom software, and third-party software components '
                                     'incorporated into bespoke and custom software is maintained to facilitate vulnerability '
                                     'and patch management. \n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '6.3: Security vulnerabilities are identified and addressed.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
                                   'Q-VPM-05: Does the organization conduct software patching for all deployed operating '
                                   'systems, applications and firmware?.',
                                   'Q-VPM-04: Does the organization address new threats and vulnerabilities on an ongoing '
                                   'basis and ensure assets are protected against known attacks? .',
                                   'Q-VPM-01: Does the organization facilitate the implementation and monitoring of '
                                   'vulnerability management controls?.'],
          'objective_title': '6.3.3: All system components are protected from known vulnerabilities by installing applicable '
                             'security patches/updates.',
          'requirement_description': '\n'
                                     'All system components are protected from known vulnerabilities by installing applicable '
                                     'security patches/updates as follows: \n'
                                     '• Critical or high-security patches/updates (identified according to the risk ranking '
                                     'process at Requirement 6.3.1) are installed within one month of release. \n'
                                     '• All other applicable security patches/updates are installed within an appropriate time '
                                     'frame as determined by the entity (for example, within three months of release).',
          'subchapter': '6.3: Security vulnerabilities are identified and addressed.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-WEB-03: Does the organization deploy Web Application Firewalls (WAFs) to provide '
                                   'defense-in-depth protection for application-specific threats? .',
                                   'Q-WEB-01: Does the organization facilitate the implementation of an enterprise-wide web '
                                   'management policy, as well as associated standards, controls and procedures?.',
                                   'Q-VPM-06.6: Does the organization perform quarterly external vulnerability scans (outside '
                                   "the organization's network looking inward) via a reputable vulnerability service provider, "
                                   'which include rescans until passing results are obtained or all high vulnerabilities are '
                                   'resolved, as defined by the Common Vulnerability Scoring System (CVSS)?.',
                                   'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '6.4.1: For public-facing web applications, new threats and vulnerabilities are addressed on an '
                             'ongoing basis and these applications are protected against known attacks.',
          'requirement_description': '\n'
                                     'For public-facing web applications, new threats and vulnerabilities are addressed on an '
                                     'ongoing basis and these applications are protected against known attacks as follows: \n'
                                     '• Reviewing public-facing web applications via manual or automated application '
                                     'vulnerability security assessment tools or methods as follows: \n'
                                     '• At least once every 12 months and after significant changes. \n'
                                     '• By an entity that specializes in application security. \n'
                                     '• Including, at a minimum, all common software attacks in Requirement 6.2.4. \n'
                                     '• All vulnerabilities are ranked in accordance with requirement 6.3.1. \n'
                                     '• All vulnerabilities are corrected. \n'
                                     '• The application is re-evaluated after the corrections OR \n'
                                     '• Installing an automated technical solution(s) that continually detects and prevents '
                                     'web-based attacks as follows: \n'
                                     '• Installed in front of public-facing web applications to detect and prevent web-based '
                                     'attacks. \n'
                                     '• Actively running and up to date as applicable. \n'
                                     '• Generating audit logs. \n'
                                     '• Configured to either block web-based attacks or generate an alert that is immediately '
                                     'investigated. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This assessment is not the same as the vulnerability scans performed for Requirement '
                                     '11.3.1 and 11.3.2. This requirement will be superseded by Requirement 6.4.2 after 31 '
                                     'March 2025 when Requirement 6.4.2 becomes effective.',
          'subchapter': '6.4: Public-facing web applications are protected against attacks.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-WEB-03: Does the organization deploy Web Application Firewalls (WAFs) to provide '
                                   'defense-in-depth protection for application-specific threats? .',
                                   'Q-WEB-01: Does the organization facilitate the implementation of an enterprise-wide web '
                                   'management policy, as well as associated standards, controls and procedures?.',
                                   'Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .',
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '6.4.2: For public-facing web applications, an automated technical solution is deployed that '
                             'continually detects and prevents web-based attacks.',
          'requirement_description': '\n'
                                     'For public-facing web applications, an automated technical solution is deployed that '
                                     'continually detects and prevents web-based attacks, with at least the following: \n'
                                     '• Is installed in front of public-facing web applications and is configured to detect '
                                     'and prevent web-based attacks. \n'
                                     '• Actively running and up to date as applicable. \n'
                                     '• Generating audit logs. \n'
                                     '• Configured to either block web-based attacks or generate an alert that is immediately '
                                     'investigated. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This new requirement will replace Requirement 6.4.1 once its effective date is reached. '
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '6.4: Public-facing web applications are protected against attacks.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-WEB-01.1: Does the organization prevent unauthorized code from being present in a secure '
                                   "page as it is rendered in a client's browser?.",
                                   'Q-VPM-05.1: Does the organization centrally-manage the flaw remediation process? .'],
          'objective_title': "6.4.3: All payment page scripts that are loaded and executed in the consumer's browser are "
                             'managed.',
          'requirement_description': '\n'
                                     'All payment page scripts that are loaded and executed in the consumer’s browser are '
                                     'managed as follows:\n'
                                     ' • A method is implemented to confirm that each script is authorized. \n'
                                     '• A method is implemented to assure the integrity of each script. \n'
                                     '• An inventory of all scripts is maintained with written justification as to why each is '
                                     'necessary.\n'
                                     ' \n'
                                     ' Applicability Notes \n'
                                     'This requirement applies to all scripts loaded from the entity’s environment and scripts '
                                     'loaded from third and fourth parties. This requirement is a best practice until 31 March '
                                     '2025, after which it will be required and must be fully considered during a PCI DSS '
                                     'assessment.',
          'subchapter': '6.4: Public-facing web applications are protected against attacks.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-CHG-02.2: Does the organization appropriately test and document proposed changes in a '
                                   'non-production environment before changes are implemented in a production environment?.',
                                   'Q-CHG-02.1: Does the organization prohibit unauthorized changes, unless '
                                   'organization-approved change requests are received?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CHG-01: Does the organization facilitate the implementation of a change management '
                                   'program?.'],
          'objective_title': '6.5.1: Changes to all system components in the production environment are made according to '
                             'established procedures.',
          'requirement_description': '\n'
                                     'Changes to all system components in the production environment are made according to '
                                     'established procedures that include: \n'
                                     '• Reason for, and description of, the change. \n'
                                     '• Documentation of security impact. \n'
                                     '• Documented change approval by authorized parties. \n'
                                     '• Testing to verify that the change does not adversely impact system security. \n'
                                     '• For bespoke and custom software changes, all updates are tested for compliance with '
                                     'Requirement 6.2.4 before being deployed into production. \n'
                                     '• Procedures to address failures and return to a secure state.',
          'subchapter': '6.5: Changes to all system components are managed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-IAC-10.8: Does the organization ensure vendor-supplied defaults are changed as part of '
                                   'the installation process?.',
                                   'Q-CHG-06.1: Does the organization report the results of cybersecurity and privacy function '
                                   'verification to appropriate organizational management?.',
                                   'Q-CHG-06: Does the organization verify the functionality of security controls when '
                                   'anomalies are discovered?.',
                                   'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, '
                                   'prior to the implementation of the change?.',
                                   'Q-CHG-02.2: Does the organization appropriately test and document proposed changes in a '
                                   'non-production environment before changes are implemented in a production environment?.',
                                   'Q-CHG-01: Does the organization facilitate the implementation of a change management '
                                   'program?.',
                                   'Q-AST-03: Does the organization assign asset ownership responsibilities to a team, '
                                   'individual, or responsible organization level to establish a common understanding of '
                                   'requirements for asset protection?.'],
          'objective_title': '6.5.2: Upon completion of a significant change, all applicable PCI DSS requirements are '
                             'confirmed to be in place on all new or changed systems and networks, and documentation is '
                             'updated as applicable.',
          'requirement_description': 'Upon completion of a significant change, all applicable PCI DSS requirements are '
                                     'confirmed to be in place on all new or changed systems and networks, and documentation '
                                     'is updated as applicable.\n'
                                     'Applicability Notes\n'
                                     'These significant changes should also be captured and reflected in the entity’s annual '
                                     'PCI DSS scope confirmation activity per Requirement 12.5.2.',
          'subchapter': '6.5: Changes to all system components are managed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-08: Does the organization manage separate development, testing and operational '
                                   'environments to reduce the risks of unauthorized access or changes to the operational '
                                   'environment and to ensure no impact to production systems?.',
                                   'Q-TDA-07: Does the organization maintain a segmented development network to ensure a '
                                   'secure development environment? .',
                                   'Q-CHG-01: Does the organization facilitate the implementation of a change management '
                                   'program?.'],
          'objective_title': '6.5.3: Pre-production environments are separated from production environments and the separation '
                             'is enforced with access controls.',
          'requirement_description': 'Pre-production environments are separated from production environments and the '
                                     'separation is enforced with access controls.',
          'subchapter': '6.5: Changes to all system components are managed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-HRS-11: Does the organization implement and maintain Separation of Duties (SoD) to '
                                   'prevent potential inappropriate activity without collusion?.'],
          'objective_title': '6.5.4: Roles and functions are separated between production and pre-production environments to '
                             'provide accountability such that only reviewed and approved changes are deployed.',
          'requirement_description': 'Roles and functions are separated between production and pre-production environments to '
                                     'provide accountability such that only reviewed and approved changes are deployed.\n'
                                     'Applicability Notes\n'
                                     'In environments with limited personnel where individuals perform multiple roles or '
                                     'functions, this same goal can be achieved with additional procedural controls that '
                                     'provide accountability. For example, a developer may also be an administrator that uses '
                                     'an administrator-level account with elevated privileges in the development environment '
                                     'and, for their developer role, they use a separate account with user-level access to the '
                                     'production environment.',
          'subchapter': '6.5: Changes to all system components are managed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-10: Does the organization approve, document and control the use of live data in '
                                   'development and test environments?.',
                                   'Q-PRI-05.4: Does the organization restrict the use of Personal Data (PD) to only the '
                                   'authorized purpose(s) consistent with applicable laws, regulations and in privacy notices? '
                                   '.',
                                   'Q-PRI-05.1: Does the organization address the use of Personal Data (PD) for internal '
                                   'testing, training and research that:  -  Takes measures to limit or minimize the amount of '
                                   'PD used for internal testing, training and research purposes; and  -  Authorizes the use '
                                   'of PD when such information is required for internal testing, training and research?.'],
          'objective_title': '6.5.5: Live PANs are not used in pre-production environments, except where those environments '
                             'are included in the CDE and protected in accordance with all applicable PCI DSS requirements.',
          'requirement_description': 'Live PANs are not used in pre-production environments, except where those environments '
                                     'are included in the CDE and protected in accordance with all applicable PCI DSS '
                                     'requirements.',
          'subchapter': '6.5: Changes to all system components are managed securely.'},
         {'chapter_title': 'Requirement 6: Develop and Maintain Secure Systems and Software',
          'conformity_questions': ['Q-TDA-09: Does the organization require system developers/integrators consult with '
                                   'cybersecurity and privacy personnel to:   -  Create and implement a Security Test and '
                                   'Evaluation (ST&E) plan;  -  Implement a verifiable flaw remediation process to correct '
                                   'weaknesses and deficiencies identified during the security testing and evaluation process; '
                                   'and  -  Document the results of the security testing/evaluation and flaw remediation '
                                   'processes?.',
                                   'Q-TDA-08.1: Does the organization ensure secure migration practices purge systems, '
                                   'applications and services of test/development/staging data and accounts before it is '
                                   'migrated into a production environment?.',
                                   'Q-TDA-08: Does the organization manage separate development, testing and operational '
                                   'environments to reduce the risks of unauthorized access or changes to the operational '
                                   'environment and to ensure no impact to production systems?.',
                                   'Q-CFG-02.4: Does the organization manage baseline configurations for development and test '
                                   'environments separately from operational baseline configurations to minimize the risk of '
                                   'unintentional changes?.',
                                   'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, '
                                   'prior to the implementation of the change?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.'],
          'objective_title': '6.5.6: Test data and test accounts are removed from system components before the system goes '
                             'into production.',
          'requirement_description': 'Test data and test accounts are removed from system components before the system goes '
                                     'into production.',
          'subchapter': '6.5: Changes to all system components are managed securely.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '7.1.1: All security policies and operational procedures that are identified in Requirement 7 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 7 '
                                     'are: \n'
                                     '• Documented, \n'
                                     '• Kept up to date \n'
                                     '• In use \n'
                                     '• Known to all affected parties.',
          'subchapter': '7.1: Processes and mechanisms for restricting access to system components and cardholder data by '
                        'business need t'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '7.1.2: Roles and responsibilities for performing activities in Requirement 7 are documented, '
                             'assigned, and understood.  New requirement- effective immediately',
          'requirement_description': 'Roles and responsibilities for performing activities in Requirement 7 are documented, '
                                     'assigned, and understood. \n'
                                     'New requirement - effective immediately',
          'subchapter': '7.1: Processes and mechanisms for restricting access to system components and cardholder data by '
                        'business need t'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-IAC-20.1: Does the organization limit access to sensitive/regulated data to only those '
                                   'individuals whose job requires such access?.',
                                   'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that '
                                   "conform to the principle of 'least privilege?'.",
                                   'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.'],
          'objective_title': '7.2.1: An access control model is defined and includes granting access.',
          'requirement_description': '\n'
                                     'An access control model is defined and includes granting access as follows: \n'
                                     '• Appropriate access depending on the entity’s business and access needs. \n'
                                     '• Access to system components and data resources that is based on users’ job '
                                     'classification and functions. \n'
                                     '• The least privileges required (for example, user, administrator) to perform a job '
                                     'function.',
          'subchapter': '7. 2: Access to system components and data is appropriately defined and assigned.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-IAC-20.1: Does the organization limit access to sensitive/regulated data to only those '
                                   'individuals whose job requires such access?.',
                                   'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that '
                                   "conform to the principle of 'least privilege?'.",
                                   'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.'],
          'objective_title': '7.2.2: Access is assigned to users, including privileged users, based on:- Job classification '
                             'and function.- Least privileges necessary to perform job responsibilities.',
          'requirement_description': '\n'
                                     'Access is assigned to users, including privileged users, based on: \n'
                                     '• Job classification and function. \n'
                                     '• Least privileges necessary to perform job responsibilities.',
          'subchapter': '7. 2: Access to system components and data is appropriately defined and assigned.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-21.3: Does the organization restrict the assignment of privileged accounts to '
                                   'organization-defined personnel or roles without management approval?.',
                                   'Q-IAC-16: Does the organization restrict and control privileged access rights for users '
                                   'and services?.',
                                   'Q-IAC-07.1: Does the organization revoke user access rights following changes in personnel '
                                   'roles and duties, if no longer necessary or permitted? .',
                                   'Q-IAC-07: Does the organization utilize a formal user registration and de-registration '
                                   'process that governs the assignment of access rights? .'],
          'objective_title': '7.2.3: Required privileges are approved by authorized personnel.',
          'requirement_description': 'Required privileges are approved by authorized personnel.',
          'subchapter': '7. 2: Access to system components and data is appropriately defined and assigned.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-17: Does the organization periodically-review the privileges assigned to individuals '
                                   'and service accounts to validate the need for such privileges and reassign or remove '
                                   'unnecessary privileges, as necessary?.',
                                   'Q-IAC-16.1: Does the organization inventory all privileged accounts and validate that each '
                                   'person with elevated privileges is authorized by the appropriate level of organizational '
                                   'management? .'],
          'objective_title': '7.2.4: All user accounts and related access privileges, including third-party/vendor accounts, '
                             'are reviewed.',
          'requirement_description': '\n'
                                     'All user accounts and related access privileges, including third-party/vendor accounts, '
                                     'are reviewed as follows: \n'
                                     '• At least once every six months\n'
                                     ' • To ensure user accounts and access remain appropriate based on job function. \n'
                                     '• Any inappropriate access is addressed. \n'
                                     '• Management acknowledges that access remains appropriate. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement applies to all user accounts and related access privileges, including '
                                     'those used by personnel and third parties/vendors, and accounts used to access '
                                     'third-party cloud services. See Requirements 7.2.5 and 7.2.5.1 and 8.6.1 through 8.6.3 '
                                     'for controls for application and system accounts. This requirement is a best practice '
                                     'until 31 March 2025, after which it will be required and must be fully considered during '
                                     'a PCI DSS assessment.',
          'subchapter': '7. 2: Access to system components and data is appropriately defined and assigned.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.',
                                   'Q-IAC-20.1: Does the organization limit access to sensitive/regulated data to only those '
                                   'individuals whose job requires such access?.',
                                   'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that '
                                   "conform to the principle of 'least privilege?'.",
                                   'Q-IAC-16: Does the organization restrict and control privileged access rights for users '
                                   'and services?.',
                                   'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.'],
          'objective_title': '7.2.5: All application and system accounts and related access privileges are assigned and '
                             'managed.',
          'requirement_description': '\n'
                                     'All application and system accounts and related access privileges are assigned and '
                                     'managed as follows: \n'
                                     '• Based on the least privileges necessary for the operability of the system or '
                                     'application. \n'
                                     '• Access is limited to the systems, applications, or processes that specifically require '
                                     'their use. \n'
                                     'Applicability Notes \n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '7. 2: Access to system components and data is appropriately defined and assigned.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-17: Does the organization periodically-review the privileges assigned to individuals '
                                   'and service accounts to validate the need for such privileges and reassign or remove '
                                   'unnecessary privileges, as necessary?.'],
          'objective_title': '7.2.5.1: All access by application and system accounts and related access privileges are '
                             'reviewed.',
          'requirement_description': '\n'
                                     'All access by application and system accounts and related access privileges are reviewed '
                                     'as follows: \n'
                                     '• Periodically (at the frequency defined in the entity’s targeted risk analysis, which '
                                     'is performed according to all elements specified in Requirement 12.3.1). \n'
                                     '• The application/ system access remains appropriate for the function being performed. \n'
                                     '• Any inappropriate access is addressed. \n'
                                     '• Management acknowledges that access remains appropriate. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '7. 2: Access to system components and data is appropriately defined and assigned.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-20.2: Does the organization restrict access to database containing '
                                   'sensitive/regulated data to only necessary services or those individuals whose job '
                                   'requires such access?.',
                                   'Q-IAC-20.1: Does the organization limit access to sensitive/regulated data to only those '
                                   'individuals whose job requires such access?.',
                                   'Q-IAC-20: Does the organization enforce Logical Access Control (LAC) permissions that '
                                   "conform to the principle of 'least privilege?'.",
                                   'Q-MON-03.7: Does the organization ensure databases produce audit records that contain '
                                   'sufficient information to monitor database activities that includes, at a minimum:  -  '
                                   'Access to particularly important information;  -  Addition of new users, especially '
                                   'privileged users;  -  Any query containing comments;  -  Any query containing multiple '
                                   'embedded queries;  -  Any query or database alerts or failures;  -  Attempts to elevate '
                                   'privileges;  -  Attempted access that is successful or unsuccessful;  -  Changes to the '
                                   'database structure;  -  Changes to user roles or database permissions;  -  Database '
                                   'administrator actions;  -  Database logons and logoffs;  -  Modifications to data; and  -  '
                                   'Use of executable commands?.'],
          'objective_title': '7.2.6: All user access to query repositories of stored cardholder data is restricted.',
          'requirement_description': '\n'
                                     'All user access to query repositories of stored cardholder data is restricted as '
                                     'follows: \n'
                                     ' \n'
                                     '• Via applications or other programmatic methods, with access and allowed actions based '
                                     'on user roles and least privileges. \n'
                                     '• Only the responsible administrator(s) can directly access or query repositories of '
                                     'stored CHD. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement applies to controls for user access to query repositories of stored '
                                     'cardholder data. See Requirements 7.2.5 and 7.2.5.1 and 8.6.1 through 8.6.3 for controls '
                                     'for application and system accounts.',
          'subchapter': '7. 2: Access to system components and data is appropriately defined and assigned.'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.'],
          'objective_title': "7.3.1: An access control system(s) is in place that restricts access based on a user's need to "
                             'know and covers all system components.',
          'requirement_description': 'An access control system(s) is in place that restricts access based on a user’s need to '
                                     'know and covers all system components.',
          'subchapter': '7.3: Logical access to system components and data is managed via an access control system(s).'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.'],
          'objective_title': '7.3.2: The access control system(s) is configured to enforce privileges assigned to individuals, '
                             'applications, and systems based on job classification and function.',
          'requirement_description': 'The access control system(s) is configured to enforce privileges assigned to '
                                     'individuals, applications, and systems based on job classification and function.',
          'subchapter': '7.3: Logical access to system components and data is managed via an access control system(s).'},
         {'chapter_title': 'Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know',
          'conformity_questions': ['Q-IAC-21: Does the organization utilize the concept of least privilege, allowing only '
                                   'authorized access to processes necessary to accomplish assigned tasks in accordance with '
                                   'organizational business functions? .',
                                   'Q-IAC-08: Does the organization enforce a Role-Based Access Control (RBAC) policy over '
                                   'users and resources?.',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.'],
          'objective_title': '7.3.3: The access control system(s) is set to ï¿½deny all- by default.',
          'requirement_description': '\nThe access control system(s) is set to “deny all” by default.',
          'subchapter': '7.3: Logical access to system components and data is managed via an access control system(s).'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '8.1.1: All security policies and operational procedures that are identified in Requirement 8 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 8 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '8. 1: Processes and mechanisms to perform activities in Requirement 8 are defined and understood.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '8.1.2: Roles and responsibilities for performing activities in Requirement 8 are documented, '
                             'assigned, and understood. New requirement- effective immediately.',
          'requirement_description': 'Roles and responsibilities for performing activities in Requirement 8 are documented, '
                                     'assigned, and understood.\n'
                                     'New requirement - effective immediately',
          'subchapter': '8. 1: Processes and mechanisms to perform activities in Requirement 8 are defined and understood.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-09.1: Does the organization ensure proper user identification management for '
                                   'non-consumer users and administrators? .',
                                   'Q-IAC-09: Does the organization govern naming standards for usernames and systems?.'],
          'objective_title': '8.2.1: All users are assigned a unique ID before access to system components or cardholder data '
                             'is allowed.',
          'requirement_description': 'All users are assigned a unique ID before access to system components or cardholder data '
                                     'is allowed.\n'
                                     'Applicability Notes\n'
                                     'This requirement is not intended to apply to user accounts within point-of-sale '
                                     'terminals that have access to only one card number at a time to facilitate a single '
                                     'transaction (such as IDs used by cashiers on point-of-sale terminals).',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-19: Does the organization prevent the sharing of generic IDs, passwords or other '
                                   'generic authentication methods?.',
                                   'Q-IAC-15.5: Does the organization authorize the use of shared/group accounts only under '
                                   'certain organization-defined conditions?.',
                                   'Q-IAC-02.1: Does the organization require individuals to be authenticated with an '
                                   'individual authenticator when a group authenticator is utilized? .'],
          'objective_title': '8.2.2: Group, shared, or generic accounts, or other shared authentication credentials are only '
                             'used when necessary on an exception basis, and are managed.',
          'requirement_description': '\n'
                                     'Group, shared, or generic accounts, or other shared authentication credentials are only '
                                     'used when necessary on an exception basis, and are managed as follows: • Account use is '
                                     'prevented unless needed for an exceptional circumstance. \n'
                                     '• Use is limited to the time needed for the exceptional circumstance. \n'
                                     '• Business justification for use is documented. \n'
                                     '• Use is explicitly approved by management. \n'
                                     '• Individual user identity is confirmed before access to an account is granted. \n'
                                     '• Every action taken is attributable to an individual user. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is not intended to apply to user accounts within point-of-sale '
                                     'terminals that have access to only one card number at a time to facilitate a single '
                                     'transaction (such as IDs used by cashiers on point-of-sale terminals).',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-TPM-05.3: Does the organization ensure Third-Party Service Providers (TSP) use unique '
                                   'authentication factors for each of its customers?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?.",
                                   'Q-TPM-04: Does the organization mitigate the risks associated with third-party access to '
                                   "the organization's systems and data?.",
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.',
                                   'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote '
                                   'network access? .',
                                   'Q-IAC-05.1: Does the organization ensure third-party service providers provide current and '
                                   "accurate information for any third-party user with access to the organization's data or "
                                   'assets?.',
                                   'Q-IAC-05: Does the organization identify and authenticate third-party systems and '
                                   'services?.',
                                   'Q-IAC-03.2: Does the organization accept Federal Identity, Credential and Access '
                                   'Management (FICAM)-approved third-party credentials? .'],
          'objective_title': '8.2.3: Additional requirement for service providers only: Service providers with remote access '
                             'to customer premises use unique authentication factors for each customer premises.',
          'requirement_description': 'Additional requirement for service providers only: Service providers with remote access '
                                     'to customer premises use unique authentication factors for each customer premises.\n'
                                     'Applicability Notes\n'
                                     'This requirement applies only when the entity being assessed is a service provider.\n'
                                     'This requirement is not intended to apply to service providers accessing their own '
                                     'shared services environments, where multiple customer environments are hosted.\n'
                                     'If service provider employees use shared authentication factors to remotely access '
                                     'customer premises, these factors must be unique per customer and managed in accordance '
                                     'with Requirement 8.2.2.',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-15: Does the organization proactively govern account management of individual, '
                                   'group, system, application, guest and temporary accounts?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
                                   'Q-IAC-07.2: Does the organization revoke user access rights in a timely manner, upon '
                                   'termination of employment or contract?.',
                                   'Q-IAC-07.1: Does the organization revoke user access rights following changes in personnel '
                                   'roles and duties, if no longer necessary or permitted? .',
                                   'Q-IAC-07: Does the organization utilize a formal user registration and de-registration '
                                   'process that governs the assignment of access rights? .'],
          'objective_title': '8.2.4: Addition, deletion, and modification of user IDs, authentication factors, and other '
                             'identifier objects are managed.',
          'requirement_description': '\n'
                                     'Addition, deletion, and modification of user IDs, authentication factors, and other '
                                     'identifier objects are managed as follows: \n'
                                     '• Authorized with the appropriate approval. \n'
                                     '• Implemented with only the privileges specified on the documented approval. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies to all user accounts, including employees, contractors, '
                                     'consultants, temporary workers and third-party vendors.',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-07.2: Does the organization revoke user access rights in a timely manner, upon '
                                   'termination of employment or contract?.',
                                   'Q-IAC-07.1: Does the organization revoke user access rights following changes in personnel '
                                   'roles and duties, if no longer necessary or permitted? .',
                                   "Q-HRS-09.2: Does the organization expedite the process of removing 'high risk' "
                                   "individual's access to systems and applications upon termination, as determined by "
                                   'management?.',
                                   'Q-HRS-09: Does the organization govern the termination of individual employment?.'],
          'objective_title': '8.2.5: Access for terminated users is immediately revoked.',
          'requirement_description': 'Access for terminated users is immediately revoked',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-15.3: Does the organization use automated mechanisms to disable inactive accounts '
                                   'after an organization-defined time period? .'],
          'objective_title': '8.2.6: Inactive user accounts are removed or disabled within 90 days of inactivity.',
          'requirement_description': 'Inactive user accounts are removed or disabled within 90 days of inactivity. ',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-NET-14.6: Does the organization proactively control and monitor third-party accounts '
                                   'used to access, support, or maintain system components via remote access?.',
                                   'Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.',
                                   'Q-MNT-05.4: Does the organization provide remote disconnect verification to ensure remote, '
                                   'non-local maintenance and diagnostic sessions are properly terminated?.',
                                   'Q-MNT-05.1: Does the organization audit remote, non-local maintenance and diagnostic '
                                   'sessions and review the maintenance records of the sessions? .',
                                   'Q-MNT-05: Does the organization authorize, monitor and control remote, non-local '
                                   'maintenance and diagnostic activities?.'],
          'objective_title': '8.2.7: Accounts used by third parties to access, support, or maintain system components via '
                             'remote access are managed.',
          'requirement_description': '\n'
                                     'Accounts used by third parties to access, support, or maintain system components via '
                                     'remote access are managed as follows: \n'
                                     '• Enabled only during the time period needed and disabled when not in use. \n'
                                     '• Use is monitored for unexpected activity.',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-NET-07: Does the organization terminate remote sessions at the end of the session or '
                                   'after an organization-defined time period of inactivity? .',
                                   'Q-IAC-25: Does the organization use automated mechanisms to log out users, both locally on '
                                   'the network and for remote sessions, at the end of the session or after an '
                                   'organization-defined period of inactivity? .',
                                   'Q-IAC-24: Does the organization initiate a session lock after an organization-defined time '
                                   'period of inactivity, or upon receiving a request from a user and retain the session lock '
                                   'until the user reestablishes access using established identification and authentication '
                                   'methods?.',
                                   'Q-IAC-14: Does the organization force users and devices to re-authenticate according to '
                                   'organization-defined circumstances that necessitate re-authentication? .'],
          'objective_title': '8.2.8: If a user session has been idle for more than 15 minutes, the user is required to '
                             're-authenticate to re-activate the terminal or session.',
          'requirement_description': 'If a user session has been idle for more than 15 minutes, the user is required to '
                                     're-authenticate to re-activate the terminal or session.\n'
                                     'Applicability Notes\n'
                                     'This requirement is not intended to apply to user accounts on point-of-sale terminals '
                                     'that have access to only one card number at a time to facilitate a single transaction '
                                     '(such as IDs used by cashiers on point-of-sale terminals).\n'
                                     'This requirement is not meant to prevent legitimate activities from being performed '
                                     'while the console/PC is unattended. ',
          'subchapter': '8.2: User identification and related accounts for users and administrators are strictly managed '
                        'throughout an ac'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.2: Does the organization validate certificates by constructing and verifying a '
                                   'certification path to an accepted trust anchor including checking certificate status '
                                   'information for PKI-based authentication?.',
                                   'Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.'],
          'objective_title': '8.3.1: All user access to system components for users and administrators is authenticated via at '
                             'least one of the following authentication factors:- Something you know, such as a password or '
                             'passphrase.- Something you have, such as a token device or smart card.- Something you are, such '
                             'as a biometric element.',
          'requirement_description': '\n'
                                     'All user access to system components for users and administrators is authenticated via '
                                     'at least one of the following authentication factors: \n'
                                     '• Something you know, such as a password or passphrase. \n'
                                     '• Something you have, such as a token device or smart card. \n'
                                     '• Something you are, such as a biometric element. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement is not intended to apply to user accounts on point-of-sale terminals '
                                     'that have access to only one card number at a time to facilitate a single transaction '
                                     '(such as IDs used by cashiers on point-of-sale terminals). This requirement does not '
                                     'supersede multi-factor authentication (MFA) requirements but applies to those in-scope '
                                     'systems not otherwise subject to MFA requirements. A digital certificate is a valid '
                                     'option for “something you have” if it is unique for a particular user.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .',
                                   'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '8.3.2: Strong cryptography is used to render all authentication factors unreadable during '
                             'transmission and storage on all system components.',
          'requirement_description': 'Strong cryptography is used to render all authentication factors unreadable during '
                                     'transmission and storage on all system components. ',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-28: Does the organization collect, validate and verify identity evidence of a user?.',
                                   'Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.'],
          'objective_title': '8.3.3: User identity is verified before modifying any authentication factor.',
          'requirement_description': 'User identity is verified before modifying any authentication factor.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-22: Does the organization enforce a limit for consecutive invalid login attempts by '
                                   'a user during an organization-defined time period and automatically locks the account when '
                                   'the maximum number of unsuccessful attempts is exceeded?.'],
          'objective_title': '8.3.4: Invalid authentication attempts are limited by:- Locking out the user ID after not more '
                             "than 10 attempts.- Setting the lockout duration to a minimum of 30 minutes or until the user's "
                             'identity is confirmed.',
          'requirement_description': '\n'
                                     'Invalid authentication attempts are limited by: \n'
                                     '• Locking out the user ID after not more than 10 attempts. \n'
                                     '• Setting the lockout duration to a minimum of 30 minutes or until the user’s identity '
                                     'is confirmed. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is not intended to apply to user accounts on point-of-sale terminals '
                                     'that have access to only one card number at a time to facilitate a single transaction '
                                     '(such as IDs used by cashiers on point-of-sale terminals).',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
                                   'Q-IAC-07: Does the organization utilize a formal user registration and de-registration '
                                   'process that governs the assignment of access rights? .'],
          'objective_title': '8.3.5: If passwords/passphrases are used as authentication factors to meet Requirement 8.3.1, '
                             'they are set and reset for each user.',
          'requirement_description': '\n'
                                     'If passwords/passphrases are used as authentication factors to meet Requirement 8.3.1, '
                                     'they are set and reset for each user as follows: \n'
                                     '• Set to a unique value for first-time use and upon reset. \n'
                                     '• Forced to be changed immediately after the first use.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.'],
          'objective_title': '8.3.6: If passwords/passphrases are used as authentication factors to meet Requirement 8.3.1, '
                             'they meet the following minimum level of complexity.',
          'requirement_description': '\n'
                                     'If passwords/passphrases are used as authentication factors to meet Requirement 8.3.1, '
                                     'they meet the following minimum level of complexity: \n'
                                     '• A minimum length of 12 characters (or IF the system does not support 12 characters, a '
                                     'minimum length of eight characters). \n'
                                     '• Contain both numeric and alphabetic characters. Applicability Notes This requirement '
                                     'is not intended to apply to: \n'
                                     '• User accounts on point-of-sale terminals that have access to only one card number at a '
                                     'time to facilitate a single transaction (such as IDs used by cashiers on point-of-sale '
                                     'terminals). \n'
                                     '• Application or system accounts, which are governed by requirements in section 8.6. '
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment. Until 31 March 2025, passwords '
                                     'must be a minimum length of seven characters in accordance with PCI DSS v3.2.1 '
                                     'Requirement 8.2.3.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.'],
          'objective_title': '8.3.7: Individuals are not allowed to submit a new password/passphrase that is the same as any '
                             'of the last four passwords/passphrases used.',
          'requirement_description': 'Individuals are not allowed to submit a new password/passphrase that is the same as any '
                                     'of the last four passwords/passphrases used.\n'
                                     'Applicability Notes\n'
                                     'This requirement is not intended to apply to user accounts on point-of-sale terminals '
                                     'that have access to only one card number at a time to facilitate a single transaction '
                                     '(such as IDs used by cashiers on point-of-sale terminals).',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .',
                                   'Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .',
                                   'Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '8.3.8: Authentication policies and procedures are documented and communicated to all users .',
          'requirement_description': '\n'
                                     'Authentication policies and procedures are documented and communicated to all users '
                                     'including: \n'
                                     '• Guidance on selecting strong authentication factors. \n'
                                     '• Guidance for how users should protect their authentication factors. \n'
                                     '• Instructions not to reuse previously used passwords/passphrases. \n'
                                     '• Instructions to change passwords/passphrases if there is any suspicion or knowledge '
                                     'that the password/passphrases have been compromised and how to report the incident.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.',
                                   'Q-IAC-02: Does the organization uniquely identify and authenticate organizational users '
                                   'and processes acting on behalf of organizational users? .'],
          'objective_title': '8.3.9: If passwords/passphrases are used as the only authentication factor for user access '
                             '(i.e., in any single-factor authentication implementation) then either:- Passwords/passphrases '
                             'are changed at least once every 90 days,  OR- The security posture of accounts is dynamically '
                             'analyzed, and real-time access to resources is automatically determined accordingly.',
          'requirement_description': '\n'
                                     'If passwords/passphrases are used as the only authentication factor for user access '
                                     '(i.e., in any single-factor authentication implementation) then either: \n'
                                     '• Passwords/passphrases are changed at least once every 90 days, OR\n'
                                     '• The security posture of accounts is dynamically analyzed, and real-time access to '
                                     'resources is automatically determined accordingly. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies to in-scope system components that are not in the CDE because '
                                     'these components are not subject to MFA requirements. This requirement is not intended '
                                     'to apply to user accounts on point-of-sale terminals that have access to only one card '
                                     'number at a time to facilitate a single transaction (such as IDs used by cashiers on '
                                     'point-of-sale terminals). This requirement does not apply to service providers’ customer '
                                     'accounts but does apply to accounts for service provider personnel.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-WEB-06: Does the organization implement Strong Customer Authentication (SCA) for '
                                   'consumers to reasonably prove their identity?.',
                                   'Q-IAC-15: Does the organization proactively govern account management of individual, '
                                   'group, system, application, guest and temporary accounts?.'],
          'objective_title': '8.3.10: Additional requirement for service providers only: If passwords/passphrases are used as '
                             'the only authentication factor for customer user access to cardholder data (i.e., in any '
                             'single-factor authentication implementation), then guidance is provided to customer users.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: If passwords/passphrases are used as '
                                     'the only authentication factor for customer user access to cardholder data (i.e., in any '
                                     'single-factor authentication implementation), then guidance is provided to customer '
                                     'users including: \n'
                                     '• Guidance for customers to change their user passwords/passphrases periodically. \n'
                                     '• Guidance as to when, and under what circumstances, passwords/passphrases are to be '
                                     'changed. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider. '
                                     'This requirement does not apply to accounts of consumer users accessing their own '
                                     'payment card information. This requirement for service providers will be superseded by '
                                     'Requirement 8.3.10.1 once 8.3.10.1 becomes effective.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.'],
          'objective_title': '8.3.10.1: Additional requirement for service providers only: If passwords/passphrases are used '
                             'as the only authentication factor for customer user access (i.e., in any single-factor '
                             'authentication implementation).',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: If passwords/passphrases are used as '
                                     'the only authentication factor for customer user access (i.e., in any single-factor '
                                     'authentication implementation) then either: \n'
                                     '• Passwords/passphrases are changed at least once every 90 days, OR \n'
                                     '• The security posture of accounts is dynamically analyzed, and real-time access to '
                                     'resources is automatically determined accordingly. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider. '
                                     'This requirement does not apply to accounts of consumer users accessing their own '
                                     'payment card information. This requirement is a best practice until 31 March 2025, after '
                                     'which it will be required and must be fully considered during a PCI DSS assessment. '
                                     'Until this requirement is effective on 31 March 2025, service providers may meet either '
                                     'Requirement 8.3.10 or 8.3.10.1.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-18: Does the organization compel users to follow accepted practices in the use of '
                                   'authentication mechanisms (e.g. passwords, passphrases, physical or logical security '
                                   'tokens, smart cards, certificates, etc.)? .',
                                   'Q-IAC-10.7: Does the organization ensure organization-defined token quality requirements '
                                   'are satisfied for hardware token-based authentication?.',
                                   'Q-IAC-10.5: Does the organization protect authenticators commensurate with the sensitivity '
                                   'of the information to which use of the authenticator permits access? .',
                                   'Q-IAC-10.2: Does the organization validate certificates by constructing and verifying a '
                                   'certification path to an accepted trust anchor including checking certificate status '
                                   'information for PKI-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.'],
          'objective_title': '8.3.11: Where authentication factors such as physical or logical security tokens, smart cards, '
                             'or certificates are used:- Factors are assigned to an individual user and not shared among '
                             'multiple users.- Physical and/or logical controls ensure only the intended user can use that '
                             'factor to gain access.',
          'requirement_description': '\n'
                                     'Where authentication factors such as physical or logical security tokens, smart cards, '
                                     'or certificates are used: \n'
                                     '• Factors are assigned to an individual user and not shared among multiple users. \n'
                                     '• Physical and/or logical controls ensure only the intended user can use that factor to '
                                     'gain access.',
          'subchapter': '8.3: Strong authentication for users and administrators is established and managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-06.1: Does the organization utilize Multi-Factor Authentication (MFA) to '
                                   'authenticate network access for privileged accounts? .'],
          'objective_title': '8.4.1: MFA is implemented for all non-console access into the CDE for personnel with '
                             'administrative access.',
          'requirement_description': 'MFA is implemented for all non-console access into the CDE for personnel with '
                                     'administrative access. \n'
                                     'Applicability Notes\n'
                                     'The requirement for MFA for non-console administrative access applies to all personnel '
                                     'with elevated or increased privileges accessing the CDE via a non-console '
                                     'connection—that is, via logical access occurring over a network interface rather than '
                                     'via a direct, physical connection. \n'
                                     'MFA is considered a best practice for non-console administrative access to in-scope '
                                     'system components that are not part of the CDE.',
          'subchapter': '8.4: Multi-factor authentication (MFA) systems are configured to prevent misuse.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
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
          'objective_title': '8.4.2: MFA is implemented for all access into the CDE.',
          'requirement_description': 'MFA is implemented for all access into the CDE.\n'
                                     'Applicability Notes\n'
                                     'This requirement does not apply to: \n'
                                     '•\t Application or system accounts performing automated functions.\n'
                                     '•\t User accounts on point-of-sale terminals that have access to only one card number at '
                                     'a time to facilitate a single transaction (such as IDs used by cashiers on point-of-sale '
                                     'terminals).\n'
                                     'MFA is required for both types of access specified in Requirements 8.4.2 and 8.4.3. '
                                     'Therefore, applying MFA to one type of access does not replace the need to apply another '
                                     'instance of MFA to the other type of access. If an individual first connects to the '
                                     'entity’s network via remote access, and then later initiates a connection into the CDE '
                                     'from within the network, per this requirement the individual would authenticate using '
                                     'MFA twice, once when connecting via remote access to the entity’s network and once when '
                                     'connecting via non-console administrative access from the entity’s network into the '
                                     'CDE.\n'
                                     '(continued on next page)\n'
                                     'The MFA requirements apply for all types of system components, including cloud, hosted '
                                     'systems, and on-premises applications, network security devices, workstations, servers, '
                                     'and endpoints, and includes access directly to an entity’s networks or systems as well '
                                     'as web-based access to an application or function. \n'
                                     'MFA for remote access into the CDE can be implemented at the network or '
                                     'system/application level; it does not have to be applied at both levels. For example, if '
                                     'MFA is used when a user connects to the CDE network, it does not have to be used when '
                                     'the user logs into each system or application within the CDE.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '8.4: Multi-factor authentication (MFA) systems are configured to prevent misuse.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote '
                                   'network access? .'],
          'objective_title': "8.4.3: MFA is implemented for all remote network access originating from outside the entity's "
                             'network that could access or impact the CDE.',
          'requirement_description': '\n'
                                     'MFA is implemented for all remote network access originating from outside the entity’s '
                                     'network that could access or impact the CDE as follows: \n'
                                     '• All remote access by all personnel, both users and administrators, originating from '
                                     'outside the entity’s network. \n'
                                     '• All remote access by third parties and vendors. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' The requirement for MFA for remote access originating from outside the entity’s network '
                                     'applies to all user accounts that can access the network remotely, where that remote '
                                     'access leads to or could lead to access into the CDE. If remote access is to a part of '
                                     'the entity’s network that is properly segmented from the CDE, such that remote users '
                                     'cannot access or impact the CDE, MFA for remote access to that part of the network is '
                                     'not required. However, MFA is required for any remote access to networks with access to '
                                     'the CDE and is recommended for all remote access to the entity’s networks. The MFA '
                                     'requirements apply for all types of system components, including cloud, hosted systems, '
                                     'and on-premises applications, network security devices, workstations, servers, and '
                                     'endpoints, and includes access directly to an entity’s networks or systems as well as '
                                     'web-based access to an application or function.',
          'subchapter': '8.4: Multi-factor authentication (MFA) systems are configured to prevent misuse.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-SEA-01: Does the organization facilitate the implementation of industry-recognized '
                                   'cybersecurity and privacy practices in the specification, design, development, '
                                   'implementation and modification of systems and services?.',
                                   'Q-IAC-06: Does the organization require Multi-Factor Authentication (MFA) for remote '
                                   'network access? .',
                                   'Q-IAC-02.2: Does the organization employ replay-resistant network access authentication?.',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.'],
          'objective_title': '8.5.1: MFA systems are implemented.',
          'requirement_description': '\n'
                                     'MFA systems are implemented as follows: \n'
                                     '• The MFA system is not susceptible to replay attacks. \n'
                                     '• MFA systems cannot be bypassed by any users, including administrative users unless '
                                     'specifically documented, and authorized by management on an exception basis, for a '
                                     'limited time period. \n'
                                     '• At least two different types of authentication factors are used. \n'
                                     '• Success of all authentication factors is required before access is granted. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '8.5: Multi-factor authentication is implemented to secure access to the CDE.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-20.3: Does the organization restrict and tightly control utility programs that are '
                                   'capable of overriding system and application controls?.',
                                   'Q-IAC-19: Does the organization prevent the sharing of generic IDs, passwords or other '
                                   'generic authentication methods?.',
                                   'Q-IAC-15.7: Does the organization review all system accounts and disable any account that '
                                   'cannot be associated with a business process and owner? .',
                                   'Q-IAC-15: Does the organization proactively govern account management of individual, '
                                   'group, system, application, guest and temporary accounts?.',
                                   'Q-IAC-05.1: Does the organization ensure third-party service providers provide current and '
                                   "accurate information for any third-party user with access to the organization's data or "
                                   'assets?.',
                                   'Q-IAC-01: Does the organization facilitate the implementation of identification and access '
                                   'management controls?.'],
          'objective_title': '8.6.1: If accounts used by systems or applications can be used for interactive login, they are '
                             'managed.',
          'requirement_description': '\n'
                                     'If accounts used by systems or applications can be used for interactive login, they are '
                                     'managed as follows: \n'
                                     '• Interactive use is prevented unless needed for an exceptional circumstance. \n'
                                     '• Interactive use is limited to the time needed for the exceptional circumstance. \n'
                                     '• Business justification for interactive use is documented. \n'
                                     '• Interactive use is explicitly approved by management. \n'
                                     '• Individual user identity is confirmed before access to account is granted. \n'
                                     '• Every action taken is attributable to an individual user.\n'
                                     ' \n'
                                     ' Applicability Notes \n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '8.6: Use of application and system accounts and associated authentication factors are strictly '
                        'managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.6: Does the organization ensure that unencrypted, static authenticators are not '
                                   'embedded in applications, scripts or stored on function keys? .'],
          'objective_title': '8.6.2: Passwords/passphrases for any application and system accounts that can be used for '
                             'interactive login are not hard coded in scripts, configuration/property files, or bespoke and '
                             'custom source code. Note: stored passwords/ passphrases are required to be encrypted in '
                             'accordance with PCI DSS Requirement 8.3.2.',
          'requirement_description': 'Passwords/passphrases for any application and system accounts that can be used for '
                                     'interactive login are not hard coded in scripts, configuration/property files, or '
                                     'bespoke and custom source code. Note: stored passwords/ passphrases are required to be '
                                     'encrypted in accordance with PCI DSS Requirement 8.3.2.\n'
                                     'Applicability Notes\n'
                                     'Stored passwords/passphrases are required to be encrypted in accordance with PCI DSS '
                                     'Requirement 8.3.2.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '8.6: Use of application and system accounts and associated authentication factors are strictly '
                        'managed.'},
         {'chapter_title': 'Requirement 8: Identify Users and Authenticate Access to System Components',
          'conformity_questions': ['Q-IAC-10.1: Does the organization enforce complexity, length and lifespan considerations '
                                   'to ensure strong criteria for password-based authentication?.',
                                   'Q-IAC-10: Does the organization securely manage authenticators for users and devices?.'],
          'objective_title': '8.6.3: Passwords/passphrases for any application and system accounts are protected against '
                             'misuse.',
          'requirement_description': '\n'
                                     'Passwords/passphrases for any application and system accounts are protected against '
                                     'misuse as follows: \n'
                                     '• Passwords/passphrases are changed periodically (at the frequency defined in the '
                                     'entity’s targeted risk analysis, which is performed according to all elements specified '
                                     'in Requirement 12.3.1) and upon suspicion or confirmation of compromise. \n'
                                     '• Passwords/passphrases are constructed with sufficient complexity appropriate for how '
                                     'frequently the entity changes the passwords/passphrases. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '8.6: Use of application and system accounts and associated authentication factors are strictly '
                        'managed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-PES-01: Does the organization facilitate the operation of physical and environmental '
                                   'protection controls? .',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '9.1.1: All security policies and operational procedures that are identified in Requirement 9 are '
                             'documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 9 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '9.1: Processes and mechanisms for performing activities in Requirement 9 are defined and understood.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-03: Does the organization enforce physical access authorizations for all physical '
                                   'access points (including designated entry/exit points) to facilities (excluding those '
                                   'areas within the facility officially designated as publicly accessible)?.',
                                   'Q-PES-01: Does the organization facilitate the operation of physical and environmental '
                                   'protection controls? .',
                                   'Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '9.1.2: Roles and responsibilities for performing activities in Requirement 9 are documented, '
                             'assigned, and understood. New requirement- effective immediately.',
          'requirement_description': 'Roles and responsibilities for performing activities in Requirement 9 are documented, '
                                     'assigned, and understood.\n'
                                     'New requirement - effective immediately',
          'subchapter': '9.1: Processes and mechanisms for performing activities in Requirement 9 are defined and understood.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-03.3: Does the organization generate a log entry for each access through controlled '
                                   'ingress and egress points?.',
                                   'Q-PES-03.1: Does the organization limit and monitor physical access through controlled '
                                   'ingress and egress points?.',
                                   'Q-PES-03: Does the organization enforce physical access authorizations for all physical '
                                   'access points (including designated entry/exit points) to facilities (excluding those '
                                   'areas within the facility officially designated as publicly accessible)?.',
                                   'Q-PES-02.1: Does the organization authorize physical access to facilities based on the '
                                   'position or role of the individual?.',
                                   'Q-PES-02: Does the organization maintain a current list of personnel with authorized '
                                   'access to organizational facilities (except for those areas within the facility officially '
                                   'designated as publicly accessible)?.'],
          'objective_title': '9.2.1: Appropriate facility entry controls are in place to restrict physical access to systems '
                             'in the CDE.',
          'requirement_description': 'Appropriate facility entry controls are in place to restrict physical access to systems '
                                     'in the CDE.',
          'subchapter': '9.2: Physical access controls manage entry into the cardholder data environment.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-05.2: Does the organization monitor physical access to critical information systems '
                                   'or sensitive/regulated data, in addition to the physical access monitoring of the '
                                   'facility?.',
                                   'Q-PES-05.1: Does the organization monitor physical intrusion alarms and surveillance '
                                   'equipment? .',
                                   'Q-PES-05: Does the organization monitor for, detect and respond to physical security '
                                   'incidents?.',
                                   'Q-PES-03.3: Does the organization generate a log entry for each access through controlled '
                                   'ingress and egress points?.'],
          'objective_title': '9.2.1.1: Individual physical access to sensitive areas within the CDE is monitored with either '
                             'video cameras or physical access control mechanisms (or both) .',
          'requirement_description': '\n'
                                     'Individual physical access to sensitive areas within the CDE is monitored with either '
                                     'video cameras or physical access control mechanisms (or both) as follows: \n'
                                     '• Entry and exit points to/from sensitive areas within the CDE are monitored. \n'
                                     '• Monitoring devices or mechanisms are protected from tampering or disabling. \n'
                                     '• Collected data is reviewed and correlated with other entries. \n'
                                     '• Collected data is stored for at least three months, unless otherwise restricted by '
                                     'law.',
          'subchapter': '9.2: Physical access controls manage entry into the cardholder data environment.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-12.2: Does the organization restrict access to printers and other system output '
                                   'devices to prevent unauthorized individuals from obtaining the output? .',
                                   'Q-PES-12.1: Does the organization protect power and telecommunications cabling carrying '
                                   'data or supporting information services from interception, interference or damage? .',
                                   'Q-PES-12: Does the organization locate system components within the facility to minimize '
                                   'potential damage from physical and environmental hazards and to minimize the opportunity '
                                   'for unauthorized access? .'],
          'objective_title': '9.2.2: Physical and/or logical controls are implemented to restrict use of publicly accessible '
                             'network jacks within the facility.',
          'requirement_description': 'Physical and/or logical controls are implemented to restrict use of publicly accessible '
                                     'network jacks within the facility.',
          'subchapter': '9.2: Physical access controls manage entry into the cardholder data environment.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-12.2: Does the organization restrict access to printers and other system output '
                                   'devices to prevent unauthorized individuals from obtaining the output? .',
                                   'Q-PES-12.1: Does the organization protect power and telecommunications cabling carrying '
                                   'data or supporting information services from interception, interference or damage? .',
                                   'Q-PES-12: Does the organization locate system components within the facility to minimize '
                                   'potential damage from physical and environmental hazards and to minimize the opportunity '
                                   'for unauthorized access? .'],
          'objective_title': '9.2.3: Physical access to wireless access points, gateways, networking/communications hardware, '
                             'and telecommunication lines within the facility is restricted.',
          'requirement_description': 'Physical access to wireless access points, gateways, networking/communications hardware, '
                                     'and telecommunication lines within the facility is restricted.',
          'subchapter': '9.2: Physical access controls manage entry into the cardholder data environment.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-12: Does the organization locate system components within the facility to minimize '
                                   'potential damage from physical and environmental hazards and to minimize the opportunity '
                                   'for unauthorized access? .',
                                   'Q-PES-03.2: Does the organization protect system components from unauthorized physical '
                                   'access (e.g., lockable physical casings)? .'],
          'objective_title': '9.2.4: Access to consoles in sensitive areas is restricted via locking when not in use.',
          'requirement_description': 'Access to consoles in sensitive areas is restricted via locking when not in use.',
          'subchapter': '9.2: Physical access controls manage entry into the cardholder data environment.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-03.1: Does the organization limit and monitor physical access through controlled '
                                   'ingress and egress points?.',
                                   'Q-PES-02.1: Does the organization authorize physical access to facilities based on the '
                                   'position or role of the individual?.',
                                   'Q-PES-02: Does the organization maintain a current list of personnel with authorized '
                                   'access to organizational facilities (except for those areas within the facility officially '
                                   'designated as publicly accessible)?.'],
          'objective_title': '9.3.1: Procedures are implemented for authorizing and managing physical access of personnel to '
                             'the CDE.',
          'requirement_description': '\n'
                                     'Procedures are implemented for authorizing and managing physical access of personnel to '
                                     'the CDE, including: \n'
                                     '• Identifying personnel.\n'
                                     ' • Managing changes to an individual’s physical access requirements. \n'
                                     '• Revoking or terminating personnel identification. \n'
                                     '• Limiting access to the identification process or system to authorized personnel.',
          'subchapter': '9.3: Physical access to the cardholder data environment for personnel and visitors is authorized and '
                        'managed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-04.1: Does the organization allow only authorized personnel access to secure areas? '
                                   '.',
                                   'Q-PES-04: Does the organization design and implement physical access controls for offices, '
                                   'rooms and facilities?.',
                                   'Q-PES-02.1: Does the organization authorize physical access to facilities based on the '
                                   'position or role of the individual?.'],
          'objective_title': '9.3.1.1: Physical access to sensitive areas within the CDE for personnel is controlled.',
          'requirement_description': '\n'
                                     'Physical access to sensitive areas within the CDE for personnel is controlled as '
                                     'follows: \n'
                                     '• Access is authorized and based on individual job function. \n'
                                     '• Access is revoked immediately upon termination. \n'
                                     '• All physical access mechanisms, such as keys, access cards, etc., are returned or '
                                     'disabled upon termination.',
          'subchapter': '9.3: Physical access to the cardholder data environment for personnel and visitors is authorized and '
                        'managed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-06.3: Does the organization restrict unescorted access to facilities to personnel '
                                   'with required security clearances, formal access authorizations and validated the need for '
                                   'access? .',
                                   'Q-PES-06.2: Does the organization requires at least one (1) form of government-issued '
                                   'photo identification to authenticate individuals before they can gain access to the '
                                   'facility?.',
                                   'Q-PES-06.1: Does the organization easily distinguish between onsite personnel and '
                                   'visitors, especially in areas where sensitive/regulated data is accessible?.',
                                   'Q-PES-06: Does the organization identify, authorize and monitor visitors before allowing '
                                   'access to the facility (other than areas designated as publicly accessible)? .'],
          'objective_title': '9.3.2: Procedures are implemented for authorizing and managing visitor access to the CDE.',
          'requirement_description': '\n'
                                     'Procedures are implemented for authorizing and managing visitor access to the CDE, '
                                     'including: \n'
                                     '• Visitors are authorized before entering. \n'
                                     '• Visitors are escorted at all times. \n'
                                     '• Visitors are clearly identified and given a badge or other identification that '
                                     'expires. \n'
                                     '• Visitor badges or other identification visibly distinguishes visitors from personnel.',
          'subchapter': '9.3: Physical access to the cardholder data environment for personnel and visitors is authorized and '
                        'managed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-06.6: Does the organization ensure visitor badges, or other issued identification, '
                                   'are surrendered before visitors leave the facility or are deactivated at a pre-determined '
                                   'time/date of expiration?.',
                                   'Q-PES-06: Does the organization identify, authorize and monitor visitors before allowing '
                                   'access to the facility (other than areas designated as publicly accessible)? .'],
          'objective_title': '9.3.3: Visitor badges or identification are surrendered or deactivated before visitors leave the '
                             'facility or at the date of expiration.',
          'requirement_description': 'Visitor badges or identification are surrendered or deactivated before visitors leave '
                                     'the facility or at the date of expiration.',
          'subchapter': '9.3: Physical access to the cardholder data environment for personnel and visitors is authorized and '
                        'managed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PES-06.5: Does the organization minimize the collection of Personal Data (PD) contained '
                                   'in visitor access records?.',
                                   'Q-PES-06: Does the organization identify, authorize and monitor visitors before allowing '
                                   'access to the facility (other than areas designated as publicly accessible)? .'],
          'objective_title': '9.3.4: A visitor log is used to maintain a physical record of visitor activity within the '
                             'facility and within sensitive areas.',
          'requirement_description': '\n'
                                     'A visitor log is used to maintain a physical record of visitor activity within the '
                                     'facility and within sensitive areas, including: \n'
                                     '• The visitor’s name and the organization represented. \n'
                                     '• The date and time of the visit. \n'
                                     '• The name of the personnel authorizing physical access. \n'
                                     '• Retaining the log for at least three months, unless otherwise restricted by law.',
          'subchapter': '9.3: Physical access to the cardholder data environment for personnel and visitors is authorized and '
                        'managed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-DCH-06.1: Does the organization physically secure all media that contains sensitive '
                                   'information?.',
                                   'Q-DCH-06: Does the organization:   -  Physically control and securely store digital and '
                                   'non-digital media within controlled areas using organization-defined security measures; '
                                   'and  -  Protect system media until the media are destroyed or sanitized using approved '
                                   'equipment, techniques and procedures?.',
                                   'Q-DCH-01.1: Does the organization ensure data stewardship is assigned, documented and '
                                   'communicated? .',
                                   'Q-DCH-01: Does the organization facilitate the implementation of data protection controls? '
                                   '.'],
          'objective_title': '9.4.1: All media with cardholder data is physically secured.',
          'requirement_description': 'All media with cardholder data is physically secured. ',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-BCD-11.2: Does the organization store backup copies of critical software and other '
                                   'security-related information in a separate facility or in a fire-rated container that is '
                                   'not collocated with the system being backed up?.',
                                   'Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.'],
          'objective_title': '9.4.1.1: Offline media backups with cardholder data are stored in a secure location.',
          'requirement_description': 'Offline media backups with cardholder data are stored in a secure location. ',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-DCH-06.2: Does the organization maintain inventory logs of all sensitive media and '
                                   'conduct sensitive media inventories at least annually? .',
                                   'Q-DCH-06.1: Does the organization physically secure all media that contains sensitive '
                                   'information?.',
                                   'Q-DCH-06: Does the organization:   -  Physically control and securely store digital and '
                                   'non-digital media within controlled areas using organization-defined security measures; '
                                   'and  -  Protect system media until the media are destroyed or sanitized using approved '
                                   'equipment, techniques and procedures?.',
                                   'Q-BCD-11: Does the organization create recurring backups of data, software and/or system '
                                   'images, as well as verify the integrity of these backups, to ensure the availability of '
                                   'the data to satisfying Recovery Time Objectives (RTOs) and Recovery Point Objectives '
                                   '(RPOs)?.',
                                   'Q-BCD-02.4: Does the organization perform periodic security reviews of storage locations '
                                   'that contain sensitive / regulated data?.'],
          'objective_title': '9.4.1.2: The security of the offline media backup location(s) with cardholder data is reviewed '
                             'at least once every 12 months.',
          'requirement_description': 'The security of the offline media backup location(s) with cardholder data is reviewed at '
                                     'least once every 12 months.',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-RSK-02: Does the organization categorizes systems and data in accordance with applicable '
                                   'local, state and Federal laws that:  -  Document the security categorization results '
                                   '(including supporting rationale) in the security plan for systems; and  -  Ensure the '
                                   'security categorization decision is reviewed and approved by the asset owner?.',
                                   'Q-DCH-02: Does the organization ensure data and assets are categorized in accordance with '
                                   'applicable statutory, regulatory and contractual requirements? .'],
          'objective_title': '9.4.2: All media with cardholder data is classified in accordance with the sensitivity of the '
                             'data.',
          'requirement_description': 'All media with cardholder data is classified in accordance with the sensitivity of the '
                                     'data.',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-DCH-07.1: Does the organization identify custodians throughout the transport of digital '
                                   'or non-digital media?.',
                                   'Q-DCH-07: Does the organization protect and control digital and non-digital media during '
                                   'transport outside of controlled areas using appropriate security measures?.'],
          'objective_title': '9.4.3: Media with cardholder data sent outside the facility is secured.',
          'requirement_description': '\n'
                                     'Media with cardholder data sent outside the facility is secured as follows: \n'
                                     '• Media sent outside the facility is logged.\n'
                                     '• Media is sent by secured courier or other delivery method that can be accurately '
                                     'tracked. \n'
                                     '• Offsite tracking logs include details about media location.',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-AST-05.1: Does the organization obtain management approval for any sensitive / regulated '
                                   "media that is transferred outside of the organization's facilities?.",
                                   'Q-AST-05: Does the organization maintain strict control over the internal or external '
                                   'distribution of any kind of sensitive/regulated media?.'],
          'objective_title': '9.4.4: Management approves all media with cardholder data that is moved outside the facility '
                             '(including when media is distributed to individuals).',
          'requirement_description': 'Management approves all media with cardholder data that is moved outside the facility '
                                     '(including when media is distributed to individuals).\n'
                                     'Applicability Notes\n'
                                     'Individuals approving media movements should have the appropriate level of management '
                                     'authority to grant this approval. However, it is not specifically required that such '
                                     'individuals have “manager” as part of their title.',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-DCH-06.2: Does the organization maintain inventory logs of all sensitive media and '
                                   'conduct sensitive media inventories at least annually? .'],
          'objective_title': '9.4.5: Inventory logs of all electronic media with cardholder data are maintained.',
          'requirement_description': 'Inventory logs of all electronic media with cardholder data are maintained. ',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-DCH-06.2: Does the organization maintain inventory logs of all sensitive media and '
                                   'conduct sensitive media inventories at least annually? .'],
          'objective_title': '9.4.5.1: Inventories of electronic media with cardholder data are conducted at least once every '
                             '12 months.',
          'requirement_description': 'Inventories of electronic media with cardholder data are conducted at least once every '
                                     '12 months. ',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for '
                                   'an organization-defined time period to fulfill the purpose(s) identified in the notice or '
                                   'as required by law;  -  Disposes of, destroys, erases, and/or anonymizes the PI, '
                                   'regardless of the method of storage; and  -  Uses organization-defined techniques or '
                                   'methods to ensure secure deletion or destruction of PD (including originals, copies and '
                                   'archived records)?.',
                                   'Q-DCH-18: Does the organization retain media and data in accordance with applicable '
                                   'statutory, regulatory and contractual obligations? .',
                                   'Q-DCH-08: Does the organization securely dispose of media when it is no longer required, '
                                   'using formal procedures? .'],
          'objective_title': '9.4.6: Hard-copy materials with cardholder data are destroyed when no longer needed for business '
                             'or legal reasons.',
          'requirement_description': '\n'
                                     'Hard-copy materials with cardholder data are destroyed when no longer needed for '
                                     'business or legal reasons, as follows: \n'
                                     '• Materials are cross-cut shredded, incinerated, or pulped so that cardholder data '
                                     'cannot be reconstructed. \n'
                                     '• Materials are stored in secure storage containers prior to destruction. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' These requirements for media destruction when that media is no longer needed for '
                                     'business or legal reasons are separate and distinct from PCI DSS Requirement 3.2.1, '
                                     'which is for securely deleting cardholder data when no longer needed per the entity’s '
                                     'cardholder data retention policies.',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for '
                                   'an organization-defined time period to fulfill the purpose(s) identified in the notice or '
                                   'as required by law;  -  Disposes of, destroys, erases, and/or anonymizes the PI, '
                                   'regardless of the method of storage; and  -  Uses organization-defined techniques or '
                                   'methods to ensure secure deletion or destruction of PD (including originals, copies and '
                                   'archived records)?.',
                                   'Q-DCH-18: Does the organization retain media and data in accordance with applicable '
                                   'statutory, regulatory and contractual obligations? .',
                                   'Q-DCH-09.1: Does the organization supervise, track, document and verify media sanitization '
                                   'and disposal actions? .',
                                   'Q-DCH-09: Does the organization sanitize digital media with the strength and integrity '
                                   'commensurate with the classification or sensitivity of the information prior to disposal, '
                                   'release out of organizational control or release for reuse?.',
                                   'Q-AST-09: Does the organization securely dispose of, destroy or repurpose system '
                                   'components using organization-defined techniques and methods to prevent such components '
                                   'from entering the gray market?.'],
          'objective_title': '9.4.7: Electronic media with cardholder data is destroyed when no longer needed for business or '
                             'legal reasons via one of the following:- The electronic media is destroyed.- The cardholder data '
                             'is rendered unrecoverable so that it cannot be reconstructed.',
          'requirement_description': 'Electronic media with cardholder data is destroyed when no longer needed for business or '
                                     'legal reasons via one of the following: \n'
                                     '•\t The electronic media is destroyed.\n'
                                     '•\t The cardholder data is rendered unrecoverable so that it cannot be reconstructed. \n'
                                     'Applicability Notes\n'
                                     'These requirements for media destruction when that media is no longer needed for '
                                     'business or legal reasons are separate and distinct from PCI DSS Requirement 3.2.1, '
                                     'which is for securely deleting cardholder data when no longer needed per the entity’s '
                                     'cardholder data retention policies.',
          'subchapter': '9.4: Media with cardholder data is securely stored, accessed, distributed, and destroyed.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness '
                                   "training that is specific to the cyber threats that the user might encounter the user's "
                                   'specific day-to-day business operations?.',
                                   'Q-SAT-03.3: Does the organization ensure that every user accessing a system processing, '
                                   'storing or transmitting sensitive information is formally trained in data handling '
                                   'requirements?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .',
                                   'Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .',
                                   'Q-AST-15.1: Does the organization physically and logically inspect critical systems to '
                                   'detect evidence of tampering? .',
                                   'Q-AST-15: Does the organization verify logical configuration settings and the physical '
                                   'integrity of critical technology assets throughout their lifecycle?.',
                                   'Q-AST-07: Does the organization appropriately protect devices that capture '
                                   'sensitive/regulated data via direct physical interaction from tampering and substitution?.',
                                   'Q-AST-06: Does the organization implement enhanced protection measures for unattended '
                                   'systems to protect against tampering and unauthorized access?.',
                                   'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-AST-01: Does the organization facilitate the implementation of asset management '
                                   'controls?.'],
          'objective_title': '9.5.1: POI devices that capture payment card data via direct physical interaction with the '
                             'payment card form factor are protected from tampering and unauthorized substitution.',
          'requirement_description': '\n'
                                     'POI devices that capture payment card data via direct physical interaction with the '
                                     'payment card form factor are protected from tampering and unauthorized substitution, '
                                     'including the following: \n'
                                     '• Maintaining a list of POI devices. \n'
                                     '• Periodically inspecting POI devices to look for tampering or unauthorized '
                                     'substitution. \n'
                                     '• Training personnel to be aware of suspicious behavior and to report tampering or '
                                     'unauthorized substitution of devices. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' These requirements apply to deployed POI devices used in card-present transactions '
                                     '(that is, a payment card form factor such as a card that is swiped, tapped, or dipped). '
                                     'This requirement is not intended to apply to manual PAN key-entry components such as '
                                     'computer keyboards. This requirement is recommended, but not required, for manual PAN '
                                     'key-entry components such as computer keyboards. This requirement does not apply to '
                                     'commercial off-the-shelf (COTS) devices (for example, smartphones or tablets), which are '
                                     'mobile merchant-owned devices designed for mass-market distribution.',
          'subchapter': '9.5: Point-of-interaction (POI) devices are protected from tampering and unauthorized substitution.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-AST-07: Does the organization appropriately protect devices that capture '
                                   'sensitive/regulated data via direct physical interaction from tampering and substitution?.',
                                   'Q-AST-02: Does the organization inventory technology assets that:  -  Accurately reflects '
                                   'the current system;   -  Is at the level of granularity deemed necessary for tracking and '
                                   'reporting;  -  Includes organization-defined information deemed necessary to achieve '
                                   'effective property accountability; and  -  Is available for review and audit by designated '
                                   'organizational officials? .',
                                   'Q-AST-01: Does the organization facilitate the implementation of asset management '
                                   'controls?.'],
          'objective_title': '9.5.1.1: An up-to-date list of POI devices is maintained, including:- Make and model of the '
                             'device.- Location of device.- Device serial number or other methods of unique identification.',
          'requirement_description': '\n'
                                     'An up-to-date list of POI devices is maintained, including: \n'
                                     '• Make and model of the device. \n'
                                     '• Location of device. \n'
                                     '• Device serial number or other methods of unique identification.',
          'subchapter': '9.5: Point-of-interaction (POI) devices are protected from tampering and unauthorized substitution.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-AST-15.1: Does the organization physically and logically inspect critical systems to '
                                   'detect evidence of tampering? .',
                                   'Q-AST-08: Does the organization periodically inspect systems and system components for '
                                   'Indicators of Compromise (IoC)?.',
                                   'Q-AST-07: Does the organization appropriately protect devices that capture '
                                   'sensitive/regulated data via direct physical interaction from tampering and '
                                   'substitution?.'],
          'objective_title': '9.5.1.2: POI device surfaces are periodically inspected to detect tampering and unauthorized '
                             'substitution.',
          'requirement_description': 'POI device surfaces are periodically inspected to detect tampering and unauthorized '
                                     'substitution. ',
          'subchapter': '9.5: Point-of-interaction (POI) devices are protected from tampering and unauthorized substitution.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-AST-08: Does the organization periodically inspect systems and system components for '
                                   'Indicators of Compromise (IoC)?.'],
          'objective_title': '9.5.1.2.1: The frequency of periodic POI device inspections and the type of inspections '
                             "performed is defined in the entity's targeted risk analysis, which is performed according to all "
                             'elements specified in Requirement 12.3.1.',
          'requirement_description': 'The frequency of periodic POI device inspections and the type of inspections performed '
                                     'is defined in the entity’s targeted risk analysis, which is performed according to all '
                                     'elements specified in Requirement 12.3.1.\n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '9.5: Point-of-interaction (POI) devices are protected from tampering and unauthorized substitution.'},
         {'chapter_title': 'Requirement 9: Restrict Physical Access to Cardholder Data',
          'conformity_questions': ['Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness '
                                   "training that is specific to the cyber threats that the user might encounter the user's "
                                   'specific day-to-day business operations?.',
                                   'Q-SAT-03.3: Does the organization ensure that every user accessing a system processing, '
                                   'storing or transmitting sensitive information is formally trained in data handling '
                                   'requirements?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .',
                                   'Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .'],
          'objective_title': '9.5.1.3: Training is provided for personnel in POI environments to be aware of attempted '
                             'tampering or replacement of POI devices.',
          'requirement_description': '\n'
                                     'Training is provided for personnel in POI environments to be aware of attempted '
                                     'tampering or replacement of POI devices, and includes: \n'
                                     '• Verifying the identity of any third-party persons claiming to be repair or maintenance '
                                     'personnel, before granting them access to modify or troubleshoot devices. \n'
                                     '• Procedures to ensure devices are not installed, replaced, or returned without '
                                     'verification. \n'
                                     '• Being aware of suspicious behavior around devices. \n'
                                     '• Reporting suspicious behavior and indications of device tampering or substitution to '
                                     'appropriate personnel.',
          'subchapter': '9.5: Point-of-interaction (POI) devices are protected from tampering and unauthorized substitution.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '10.1.1: All security policies and operational procedures that are identified in Requirement 10 '
                             'are documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 10 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '10.1: Processes and mechanisms for performing activities in Requirement 10 are defined and '
                        'documented.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '10.1.2: Roles and responsibilities for performing activities in Requirement 10 are documented, '
                             'assigned, and understood. New requirement- effective immediately.',
          'requirement_description': ' Roles and responsibilities for performing activities in Requirement 10 are documented, '
                                     'assigned, and understood.\n'
                                     'New requirement - effective immediately\n',
          'subchapter': '10.1: Processes and mechanisms for performing activities in Requirement 10 are defined and '
                        'documented.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1: Audit logs are enabled and active for all system components and cardholder data.',
          'requirement_description': 'Audit logs are enabled and active for all system components and cardholder data.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.3: Does the organization log and review the actions of users and/or services with '
                                   'elevated privileges?.',
                                   'Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1.1: Audit logs capture all individual user access to cardholder data.',
          'requirement_description': 'Audit logs capture all individual user access to cardholder data.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-IAC-21.4: Does the organization audit the execution of privileged functions? .',
                                   'Q-MON-03.3: Does the organization log and review the actions of users and/or services with '
                                   'elevated privileges?.',
                                   'Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1.2: Audit logs capture all actions taken by any individual with administrative access, '
                             'including any interactive use of application or system accounts.',
          'requirement_description': 'Audit logs capture all actions taken by any individual with administrative access, '
                                     'including any interactive use of application or system accounts.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.3: Does the organization log and review the actions of users and/or services with '
                                   'elevated privileges?.',
                                   'Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1.3: Audit logs capture all access to audit logs.',
          'requirement_description': 'Audit logs capture all access to audit logs.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.3: Does the organization log and review the actions of users and/or services with '
                                   'elevated privileges?.',
                                   'Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1.4: Audit logs capture all invalid logical access attempts.',
          'requirement_description': 'Audit logs capture all invalid logical access attempts.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.3: Does the organization log and review the actions of users and/or services with '
                                   'elevated privileges?.',
                                   'Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1.5: Audit logs capture all changes to identification and authentication credentials '
                             'including, but not limited to:- Creation of new accounts.- Elevation of privileges.- All '
                             'changes, additions, or deletions to accounts with administrative access.',
          'requirement_description': '\n'
                                     'Audit logs capture all changes to identification and authentication credentials '
                                     'including, but not limited to: \n'
                                     '• Creation of new accounts. \n'
                                     '• Elevation of privileges. \n'
                                     '• All changes, additions, or deletions to accounts with administrative access.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.3: Does the organization log and review the actions of users and/or services with '
                                   'elevated privileges?.',
                                   'Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1.6: Audit logs capture the following:- All initialization of new audit logs, and- All '
                             'starting, stopping, or pausing of the existing audit logs.',
          'requirement_description': '\n'
                                     'Audit logs capture the following: \n'
                                     '• All initialization of new audit logs, and \n'
                                     '• All starting, stopping, or pausing of the existing audit logs.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.3: Does the organization log and review the actions of users and/or services with '
                                   'elevated privileges?.',
                                   'Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.1.7: Audit logs capture all creation and deletion of system-level objects.',
          'requirement_description': 'Audit logs capture all creation and deletion of system-level objects.',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-03.2: Does the organization link system access to individual users or service '
                                   'accounts?.',
                                   'Q-MON-03: Does the organization configure systems to produce audit records that contain '
                                   'sufficient information to, at a minimum:  -  Establish what type of event occurred;  -  '
                                   'When (date and time) the event occurred;  -  Where the event occurred;  -  The source of '
                                   'the event;  -  The outcome (success or failure) of the event; and   -  The identity of any '
                                   'user/subject associated with the event? .',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.2.2: Audit logs record the following details for each auditable event:- User identification.- '
                             'Type of event.- Date and time.- Success and failure indication.- Origination of event.- Identity '
                             'or name of affected data, system component, resource, or service (for example, name and '
                             'protocol).',
          'requirement_description': '\n'
                                     'Audit logs record the following details for each auditable event: \n'
                                     '• User identification. \n'
                                     '• Type of event. \n'
                                     '• Date and time. \n'
                                     '• Success and failure indication. \n'
                                     '• Origination of event. \n'
                                     '• Identity or name of affected data, system component, resource, or service (for '
                                     'example, name and protocol).',
          'subchapter': '10.2: Audit logs are implemented to support the detection of anomalies and suspicious activity, and '
                        'the forensic'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-08.2: Does the organization restrict access to the management of event logs to '
                                   'privileged users with a specific business need?.',
                                   'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized '
                                   'access, modification and deletion?.'],
          'objective_title': '10.3.1: Read access to audit logs files is limited to those with a job-related need.',
          'requirement_description': ' Read access to audit logs files is limited to those with a job-related need.',
          'subchapter': '10.3: Audit logs are protected from destruction and unauthorized modifications.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-08.2: Does the organization restrict access to the management of event logs to '
                                   'privileged users with a specific business need?.',
                                   'Q-MON-08: Does the organization protect event logs and audit tools from unauthorized '
                                   'access, modification and deletion?.'],
          'objective_title': '10.3.2: Audit log files are protected to prevent modifications by individuals.',
          'requirement_description': ' Audit log files are protected to prevent modifications by individuals.',
          'subchapter': '10.3: Audit logs are protected from destruction and unauthorized modifications.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-08.1: Does the organization back up event logs onto a physically different system or '
                                   'system component than the Security Incident Event Manager (SIEM) or similar automated '
                                   'tool?.',
                                   'Q-MON-02.2: Does the organization centrally collect, review and analyze audit records from '
                                   'multiple sources?.',
                                   'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or '
                                   'similar automated tool, to support the centralized collection of security-related event '
                                   'logs?.'],
          'objective_title': '10.3.3: Audit log files, including those for external-facing technologies, are promptly backed '
                             'up to a secure, central, internal log server(s) or other media that is difficult to modify.',
          'requirement_description': ' Audit log files, including those for external-facing technologies, are promptly backed '
                                     'up to a secure, central, internal log server(s) or other media that is difficult to '
                                     'modify.',
          'subchapter': '10.3: Audit logs are protected from destruction and unauthorized modifications.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect '
                                   'and report unauthorized changes to system files and configurations?.',
                                   'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .'],
          'objective_title': '10.3.4: File integrity monitoring or change-detection mechanisms is used on audit logs to ensure '
                             'that existing log data cannot be changed without generating alerts.',
          'requirement_description': ' File integrity monitoring or change-detection mechanisms is used on audit logs to '
                                     'ensure that existing log data cannot be changed without generating alerts.',
          'subchapter': '10.3: Audit logs are protected from destruction and unauthorized modifications.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-02.2: Does the organization centrally collect, review and analyze audit records from '
                                   'multiple sources?.',
                                   'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or '
                                   'similar automated tool, to support the centralized collection of security-related event '
                                   'logs?.',
                                   'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.',
                                   'Q-MON-01.4: Does the organization monitor, correlate and respond to alerts from physical, '
                                   'cybersecurity, privacy and supply chain activities to achieve integrated situational '
                                   'awareness? .',
                                   'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or '
                                   'similar automated tool, to support near real-time analysis and incident escalation?.'],
          'objective_title': '10.4.1: Audit logs are reviewed at least once daily.',
          'requirement_description': '\n'
                                     'The following audit logs are reviewed at least once daily: \n'
                                     '• All security events. \n'
                                     '• Logs of all system components that store, process, or transmit CHD and/or SAD. \n'
                                     '• Logs of all critical system components. \n'
                                     '• Logs of all servers and system components that perform security functions (for '
                                     'example, network security controls, intrusion-detection systems/intrusion-prevention '
                                     'systems (IDS/IPS), authentication servers).',
          'subchapter': '10.4: Audit logs are reviewed to identify anomalies or suspicious activity.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-02.2: Does the organization centrally collect, review and analyze audit records from '
                                   'multiple sources?.',
                                   'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.',
                                   'Q-MON-02: Does the organization utilize a Security Incident Event Manager (SIEM) or '
                                   'similar automated tool, to support the centralized collection of security-related event '
                                   'logs?.',
                                   'Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.',
                                   'Q-MON-01.4: Does the organization monitor, correlate and respond to alerts from physical, '
                                   'cybersecurity, privacy and supply chain activities to achieve integrated situational '
                                   'awareness? .',
                                   'Q-MON-01.2: Does the organization utilize a Security Incident Event Manager (SIEM), or '
                                   'similar automated tool, to support near real-time analysis and incident escalation?.'],
          'objective_title': '10.4.1.1: Automated mechanisms are used to perform audit log reviews.',
          'requirement_description': 'Automated mechanisms are used to perform audit log reviews.\n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '10.4: Audit logs are reviewed to identify anomalies or suspicious activity.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.'],
          'objective_title': '10.4.2: Logs of all other system components (those not specified in Requirement 10.4.1) are '
                             'reviewed periodically.',
          'requirement_description': ' Logs of all other system components (those not specified in Requirement 10.4.1) are '
                                     'reviewed periodically.\n'
                                     'Applicability Notes\n'
                                     'This requirement is applicable to all other in-scope system components not included in '
                                     'Requirement 10.4.1.',
          'subchapter': '10.4: Audit logs are reviewed to identify anomalies or suspicious activity.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.'],
          'objective_title': '10.4.2.1: The frequency of periodic log reviews for all other system components (not defined in '
                             "Requirement 10.4.1) is defined in the entity's targeted risk analysis, which is performed "
                             'according to all elements specified in Requirement 12.3.1.',
          'requirement_description': 'The frequency of periodic log reviews for all other system components (not defined in '
                                     'Requirement 10.4.1) is defined in the entity’s targeted risk analysis, which is '
                                     'performed according to all elements specified in Requirement 12.3.1.\n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '10.4: Audit logs are reviewed to identify anomalies or suspicious activity.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-MON-01.8: Does the organization review event logs on an ongoing basis and escalate '
                                   'incidents in accordance with established timelines and procedures?.',
                                   'Q-MON-01.4: Does the organization monitor, correlate and respond to alerts from physical, '
                                   'cybersecurity, privacy and supply chain activities to achieve integrated situational '
                                   'awareness? .',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.'],
          'objective_title': '10.4.3: Exceptions and anomalies identified during the review process are addressed.',
          'requirement_description': ' Exceptions and anomalies identified during the review process are addressed.',
          'subchapter': '10.4: Audit logs are reviewed to identify anomalies or suspicious activity.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-PRI-05: Does the organization:   -  Retain Personal Data (PD), including metadata, for '
                                   'an organization-defined time period to fulfill the purpose(s) identified in the notice or '
                                   'as required by law;  -  Disposes of, destroys, erases, and/or anonymizes the PI, '
                                   'regardless of the method of storage; and  -  Uses organization-defined techniques or '
                                   'methods to ensure secure deletion or destruction of PD (including originals, copies and '
                                   'archived records)?.',
                                   'Q-DCH-18: Does the organization retain media and data in accordance with applicable '
                                   'statutory, regulatory and contractual obligations? .',
                                   'Q-MON-10: Does the organization retain event logs for a time period consistent with '
                                   'records retention requirements to provide support for after-the-fact investigations of '
                                   'security incidents and to meet statutory, regulatory and contractual retention '
                                   'requirements? .'],
          'objective_title': '10.5.1: Retain audit log history for at least 12 months, with at least the most recent three '
                             'months immediately available for analysis.',
          'requirement_description': ' Retain audit log history for at least 12 months, with at least the most recent three '
                                     'months immediately available for analysis.',
          'subchapter': '10.5: Audit log history is retained and available for analysis.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-SEA-20: Does the organization utilize time-synchronization technology to synchronize all '
                                   'critical system clocks? .',
                                   'Q-MON-07.1: Does the organization synchronize internal system clocks with an authoritative '
                                   'time source? .',
                                   'Q-MON-07: Does the organization configure systems to use an authoritative time source to '
                                   'generate time stamps for event logs? .',
                                   'Q-MON-02.7: Does the organization compile audit records into an organization-wide audit '
                                   'trail that is time-correlated?.',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.6.1: System clocks and time are synchronized using time-synchronization technology.',
          'requirement_description': ' System clocks and time are synchronized using time-synchronization technology. \n'
                                     'Applicability Notes\n'
                                     'Keeping time-synchronization technology current includes managing vulnerabilities and '
                                     'patching the technology according to PCI DSS Requirements 6.3.1 and 6.3.3.',
          'subchapter': '10.6: Time-synchronization mechanisms support consistent time settings across all systems.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-SEA-20: Does the organization utilize time-synchronization technology to synchronize all '
                                   'critical system clocks? .',
                                   'Q-MON-07.1: Does the organization synchronize internal system clocks with an authoritative '
                                   'time source? .',
                                   'Q-MON-07: Does the organization configure systems to use an authoritative time source to '
                                   'generate time stamps for event logs? .',
                                   'Q-MON-02.7: Does the organization compile audit records into an organization-wide audit '
                                   'trail that is time-correlated?.',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.6.2: Systems are configured to the correct and consistent time.',
          'requirement_description': '\n'
                                     'Systems are configured to the correct and consistent time as follows: \n'
                                     '• One or more designated time servers are in use. \n'
                                     '• Only the designated central time server(s) receives time from external sources. \n'
                                     '• Time received from external sources is based on International Atomic Time or '
                                     'Coordinated Universal Time (UTC). \n'
                                     '• The designated time server(s) accept time updates only from specific industry-accepted '
                                     'external sources. • Where there is more than one designated time server, the time '
                                     'servers peer with one another to keep accurate time. \n'
                                     '• Internal systems receive time information only from designated central time server(s).',
          'subchapter': '10.6: Time-synchronization mechanisms support consistent time settings across all systems.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-SEA-20: Does the organization utilize time-synchronization technology to synchronize all '
                                   'critical system clocks? .',
                                   'Q-MON-07.1: Does the organization synchronize internal system clocks with an authoritative '
                                   'time source? .',
                                   'Q-MON-07: Does the organization configure systems to use an authoritative time source to '
                                   'generate time stamps for event logs? .',
                                   'Q-MON-02.7: Does the organization compile audit records into an organization-wide audit '
                                   'trail that is time-correlated?.',
                                   'Q-CFG-02.5: Does the organization configure systems utilized in high-risk areas with more '
                                   'restrictive baseline configurations?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .'],
          'objective_title': '10.6.3: Time synchronization settings and data are protected.',
          'requirement_description': '\n'
                                     'Time synchronization settings and data are protected as follows: \n'
                                     '• Access to time data is restricted to only personnel with a business need. \n'
                                     '• Any changes to time settings on critical systems are logged, monitored, and reviewed.',
          'subchapter': '10.6: Time-synchronization mechanisms support consistent time settings across all systems.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .',
                                   'Q-SEA-04.1: Does the organization isolate security functions from non-security functions? '
                                   '.',
                                   'Q-SEA-01.1: Does the organization centrally-manage the organization-wide management and '
                                   'implementation of cybersecurity and privacy controls and related processes?.',
                                   'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
                                   'Q-IRO-01: Does the organization facilitate the implementation of incident response '
                                   'controls?.',
                                   'Q-END-16: Does the organization ensure  security functions are restricted to authorized '
                                   'individuals and enforce least privilege control requirements for necessary job functions?.',
                                   'Q-END-06.2: Does the organization detect and respond to unauthorized configuration changes '
                                   'as cybersecurity incidents?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.',
                                   'Q-CFG-02.8: Does the organization respond to unauthorized changes to configuration '
                                   'settings as security incidents? .',
                                   'Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the '
                                   "organization's cybersecurity and privacy policies and standards? .",
                                   'Q-CPL-03: Does the organization ensure managers regularly review the processes and '
                                   'documented procedures within their area of responsibility to adhere to appropriate '
                                   'security policies, standards and other applicable requirements?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?."],
          'objective_title': '10.7.1: Additional requirement for service providers only: Failures of critical security control '
                             'systems are detected, alerted, and addressed promptly.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: Failures of critical security control '
                                     'systems are detected, alerted, and addressed promptly, including but not limited to '
                                     'failure of the following critical security control systems: \n'
                                     '• Network security controls \n'
                                     '• IDS/IPS \n'
                                     '• FIM \n'
                                     '• Anti-malware solutions \n'
                                     '• Physical access controls \n'
                                     '• Logical access controls \n'
                                     '• Audit logging mechanisms \n'
                                     '• Segmentation controls (if used) \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider. '
                                     'This requirement will be superseded by Requirement 10.7.2 as of 31 March 2025.',
          'subchapter': '10.7: Failures of critical security control systems are detected, reported, and responded to '
                        'promptly.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .',
                                   'Q-SEA-01.1: Does the organization centrally-manage the organization-wide management and '
                                   'implementation of cybersecurity and privacy controls and related processes?.',
                                   'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
                                   'Q-IRO-01: Does the organization facilitate the implementation of incident response '
                                   'controls?.',
                                   'Q-END-06.2: Does the organization detect and respond to unauthorized configuration changes '
                                   'as cybersecurity incidents?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.',
                                   'Q-CFG-02.8: Does the organization respond to unauthorized changes to configuration '
                                   'settings as security incidents? .',
                                   'Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the '
                                   "organization's cybersecurity and privacy policies and standards? .",
                                   'Q-CPL-03: Does the organization ensure managers regularly review the processes and '
                                   'documented procedures within their area of responsibility to adhere to appropriate '
                                   'security policies, standards and other applicable requirements?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?."],
          'objective_title': '10.7.2: Failures of critical security control systems are detected, alerted, and addressed '
                             'promptly.',
          'requirement_description': '\n'
                                     'Failures of critical security control systems are detected, alerted, and addressed '
                                     'promptly, including but not limited to failure of the following critical security '
                                     'control systems: \n'
                                     '• Network security controls. \n'
                                     '• IDS/IPS. \n'
                                     '• Change-detection mechanisms. \n'
                                     '• Anti-malware solutions. \n'
                                     '• Physical access controls. \n'
                                     '• Logical access controls. \n'
                                     '• Audit logging mechanisms. \n'
                                     '• Segmentation controls (if used). \n'
                                     '• Audit log review mechanisms.\n'
                                     '• Automated security testing tools (if used). \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement applies to all entities, including service providers, and will '
                                     'supersede Requirement 10.7.1 as of 31 March 2025. It includes two additional critical '
                                     'security control systems not in Requirement 10.7.1. This requirement is a best practice '
                                     'until 31 March 2025, after which it will be required and must be fully considered during '
                                     'a PCI DSS assessment.',
          'subchapter': '10.7: Failures of critical security control systems are detected, reported, and responded to '
                        'promptly.'},
         {'chapter_title': 'Requirement 10: Log and Monitor All Access to System Components and Cardholder Data',
          'conformity_questions': ['Q-TPM-11: Does the organization ensure response/recovery planning and testing are '
                                   'conducted with critical suppliers/providers? .',
                                   'Q-SEA-01.1: Does the organization centrally-manage the organization-wide management and '
                                   'implementation of cybersecurity and privacy controls and related processes?.',
                                   'Q-RSK-06.1: Does the organization respond to findings from cybersecurity and privacy '
                                   'assessments, incidents and audits to ensure proper remediation has been performed?.',
                                   'Q-RSK-06: Does the organization remediate risks to an acceptable level? .',
                                   'Q-IRO-01: Does the organization facilitate the implementation of incident response '
                                   'controls?.',
                                   'Q-END-06.2: Does the organization detect and respond to unauthorized configuration changes '
                                   'as cybersecurity incidents?.',
                                   'Q-MON-01: Does the organization facilitate the implementation of enterprise-wide '
                                   'monitoring controls?.',
                                   'Q-CFG-02.8: Does the organization respond to unauthorized changes to configuration '
                                   'settings as security incidents? .',
                                   'Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the '
                                   "organization's cybersecurity and privacy policies and standards? .",
                                   'Q-CPL-03: Does the organization ensure managers regularly review the processes and '
                                   'documented procedures within their area of responsibility to adhere to appropriate '
                                   'security policies, standards and other applicable requirements?.',
                                   'Q-CPL-02: Does the organization provide a security & privacy controls oversight function '
                                   "that reports to the organization's executive leadership?.",
                                   'Q-CHG-06: Does the organization verify the functionality of security controls when '
                                   'anomalies are discovered?.'],
          'objective_title': '10.7.3: Failures of any critical security controls systems are responded to promptly.',
          'requirement_description': '\n'
                                     'Failures of any critical security controls systems are responded to promptly, including '
                                     'but not limited to: \n'
                                     '• Restoring security functions. \n'
                                     '• Identifying and documenting the duration (date and time from start to end) of the '
                                     'security failure. \n'
                                     '• Identifying and documenting the cause(s) of failure, and documenting required '
                                     'remediation. \n'
                                     '• Identifying and addressing any security issues that arose during the failure. \n'
                                     '• Determining whether further actions are required as a result of the security '
                                     'failure. \n'
                                     '• Implementing controls to prevent the cause of failure from reoccurring. \n'
                                     '• Resuming monitoring of security controls. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement applies only when the entity being assessed is a service provider, '
                                     'until the 31 March 2025, after which this requirement will apply to all entities. This '
                                     'is a current v3.2.1 requirement that applies to service providers only. However, this '
                                     'requirement is a best practice for all other entities until 31 March 2025, after which '
                                     'it will be required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '10.7: Failures of critical security control systems are detected, reported, and responded to '
                        'promptly.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-OPS-01: Does the organization facilitate the implementation of operational security '
                                   'controls?.',
                                   'Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '11.1.1: All security policies and operational procedures that are identified in Requirement 11 '
                             'are documented, kept up to date, in use and known to all affected parties.',
          'requirement_description': '\n'
                                     'All security policies and operational procedures that are identified in Requirement 11 '
                                     'are: \n'
                                     '• Documented. \n'
                                     '• Kept up to date. \n'
                                     '• In use. \n'
                                     '• Known to all affected parties.',
          'subchapter': '11.1: Processes and mechanisms for performing activities in Requirement 11 are defined and '
                        'understood.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '11.1.2: Roles and responsibilities for performing activities in Requirement 11 are documented, '
                             'assigned, and understood. New requirement- effective immediately.',
          'requirement_description': ' Roles and responsibilities for performing activities in Requirement 11 are documented, '
                                     'assigned, and understood.\n'
                                     'New requirement - effective immediately',
          'subchapter': '11.1: Processes and mechanisms for performing activities in Requirement 11 are defined and '
                        'understood.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-NET-15.5: Does the organization test for the presence of Wireless Access Points (WAPs) '
                                   'and identify all authorized and unauthorized WAPs within the facility(ies)? .',
                                   'Q-NET-15: Does the organization control authorized wireless usage and monitor for '
                                   'unauthorized wireless access?.',
                                   'Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-NET-03.1: Does the organization limit the number of concurrent external network '
                                   'connections to its systems?.',
                                   'Q-NET-02.2: Does the organization implement and manage a secure guest network? .',
                                   'Q-NET-01: Does the organization develop, govern & update procedures to facilitate the '
                                   'implementation of network security controls?.'],
          'objective_title': '11.2.1: Authorized and unauthorized wireless access points are managed.',
          'requirement_description': '\n'
                                     'Authorized and unauthorized wireless access points are managed as follows: \n'
                                     '• The presence of wireless (Wi-Fi) access points is tested for, \n'
                                     '• All authorized and unauthorized wireless access points are detected and identified, \n'
                                     '• Testing, detection, and identification occurs at least once every three months. \n'
                                     '• If automated monitoring is used, personnel are notified via generated alerts. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' The requirement applies even when a policy exists that prohibits the use of wireless '
                                     'technology since attackers do not read and follow company policy. Methods used to meet '
                                     'this requirement must be sufficient to detect and identify both authorized and '
                                     'unauthorized devices, including unauthorized devices attached to devices that themselves '
                                     'are authorized.',
          'subchapter': '11.2: Wireless access points are identified and monitored, and unauthorized wireless access points '
                        'are addressed'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': [],
          'objective_title': '11.2 2: An inventory of authorized wireless access points is maintained, including a documented '
                             'business justification.',
          'requirement_description': ' An inventory of authorized wireless access points is maintained, including a documented '
                                     'business justification.',
          'subchapter': '11.2: Wireless access points are identified and monitored, and unauthorized wireless access points '
                        'are addressed'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-06.2: Does the organization identify the breadth and depth of coverage for '
                                   'vulnerability scanning that define the system components scanned and types of '
                                   'vulnerabilities that are checked for? .',
                                   'Q-VPM-06.1: Does the organization update vulnerability scanning tools?.',
                                   'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.'],
          'objective_title': '11.3.1: Internal vulnerability scans are performed.',
          'requirement_description': '\n'
                                     'Internal vulnerability scans are performed as follows: \n'
                                     '• At least once every three months. \n'
                                     '• High-risk and critical vulnerabilities (per the entity’s vulnerability risk rankings '
                                     'defined at Requirement 6.3.1) are resolved. \n'
                                     '• Rescans are performed that confirm all high-risk and critical vulnerabilities (as '
                                     'noted above) have been resolved. \n'
                                     '• Scan tool is kept up to date with latest vulnerability information. \n'
                                     '• Scans are performed by qualified personnel and organizational independence of the '
                                     'tester exists. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' It is not required to use a QSA or ASV to conduct internal vulnerability scans. '
                                     'Internal vulnerability scans can be performed by qualified, internal staff that are '
                                     'reasonably independent of the system component(s) being scanned (for example, a network '
                                     'administrator should not be responsible for scanning the network), or an entity may '
                                     'choose to have internal vulnerability scans performed by a firm specializing in '
                                     'vulnerability scanning.',
          'subchapter': '11.3: External and internal vulnerabilities are regularly identified, prioritized, and addressed.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.'],
          'objective_title': '11.3.1.1: All other applicable vulnerabilities (those not ranked as high-risk or critical (per '
                             "the entity's vulnerability risk rankings defined at Requirement 6.3.1) are managed.",
          'requirement_description': '\n'
                                     'All other applicable vulnerabilities (those not ranked as high-risk or critical (per the '
                                     'entity’s vulnerability risk rankings defined at Requirement 6.3.1) are managed as '
                                     'follows: \n'
                                     '• Addressed based on the risk defined in the entity’s targeted risk analysis, which is '
                                     'performed according to all elements specified in Requirement 12.3.1. \n'
                                     '• Rescans are conducted as needed. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'The timeframe for addressing lower-risk vulnerabilities is subject to the results of a '
                                     'risk analysis per Requirement 12.3.1 that includes (minimally) identification of assets '
                                     'being protected, threats, and likelihood and/or impact of a threat being realized. This '
                                     'requirement is a best practice until 31 March 2025, after which it will be required and '
                                     'must be fully considered during a PCI DSS assessment.',
          'subchapter': '11.3: External and internal vulnerabilities are regularly identified, prioritized, and addressed.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-06.7: Does the organization perform quarterly internal vulnerability scans, that '
                                   "includes all segments of the organization's internal network, as well as rescans until "
                                   'passing results are obtained or all high vulnerabilities are resolved, as defined by the '
                                   'Common Vulnerability Scoring System (CVSS)?.',
                                   'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.'],
          'objective_title': '11.3.1.2: Internal vulnerability scans are performed via authenticated scanning.',
          'requirement_description': '\n'
                                     'Internal vulnerability scans are performed via authenticated scanning as follows: \n'
                                     '• Systems that are unable to accept credentials for authenticated scanning are '
                                     'documented. \n'
                                     '• Sufficient privileges are used, for those systems that accept credentials for '
                                     'scanning. \n'
                                     '• If accounts used for authenticated scanning can be used for interactive login, they '
                                     'are managed in accordance with Requirement 8.2.2. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' The authenticated scanning tools can be either host-based or network-based. '
                                     '“Sufficient” privileges are those needed to access system resources such that a thorough '
                                     'scan can be conducted that detects known vulnerabilities. This requirement does not '
                                     'apply to system components that cannot accept credentials for scanning. Examples of '
                                     'systems that may not accept credentials for scanning include some network and security '
                                     'appliances, mainframes, and containers. This requirement is a best practice until 31 '
                                     'March 2025, after which it will be required and must be fully considered during a PCI '
                                     'DSS assessment.',
          'subchapter': '11.3: External and internal vulnerabilities are regularly identified, prioritized, and addressed.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-06.7: Does the organization perform quarterly internal vulnerability scans, that '
                                   "includes all segments of the organization's internal network, as well as rescans until "
                                   'passing results are obtained or all high vulnerabilities are resolved, as defined by the '
                                   'Common Vulnerability Scoring System (CVSS)?.',
                                   'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.'],
          'objective_title': '11.3.1.3: Internal vulnerability scans are performed after any significant change.',
          'requirement_description': '\n'
                                     'Internal vulnerability scans are performed after any significant change as follows: \n'
                                     '• High-risk and critical vulnerabilities (per the entity’s vulnerability risk rankings '
                                     'defined at Requirement 6.3.1 are resolved. \n'
                                     '• Rescans are conducted as needed. \n'
                                     '• Scans are performed by qualified personnel and organizational independence of the '
                                     'tester exists (not required to be a QSA or ASV). \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'Authenticated internal vulnerability scanning per Requirement 11.3.1.2 is not required '
                                     'for scans performed after significant changes.',
          'subchapter': '11.3: External and internal vulnerabilities are regularly identified, prioritized, and addressed.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-06.6: Does the organization perform quarterly external vulnerability scans (outside '
                                   "the organization's network looking inward) via a reputable vulnerability service provider, "
                                   'which include rescans until passing results are obtained or all high vulnerabilities are '
                                   'resolved, as defined by the Common Vulnerability Scoring System (CVSS)?.'],
          'objective_title': '11.3.2: External vulnerability scans are performed.',
          'requirement_description': '\n'
                                     'External vulnerability scans are performed as follows: \n'
                                     '• At least once every three months. \n'
                                     '• By a PCI SSC Approved Scanning Vendor (ASV). \n'
                                     '• Vulnerabilities are resolved and ASV Program Guide requirements for a passing scan are '
                                     'met. \n'
                                     '• Rescans are performed as needed to confirm that vulnerabilities are resolved per the '
                                     'ASV Program Guide requirements for a passing scan. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'For initial PCI DSS compliance, it is not required that four passing scans be completed '
                                     'within 12 months if the assessor verifies: 1) the most recent scan result was a passing '
                                     'scan, 2) the entity has documented policies and procedures requiring scanning at least '
                                     'once every three months, and 3) vulnerabilities noted in the scan results have been '
                                     'corrected as shown in a re-scan(s). (continued on next page) However, for subsequent '
                                     'years after the initial PCI DSS assessment, passing scans at least every three months '
                                     'must have occurred. ASV scanning tools can scan a vast array of network types and '
                                     'topologies. Any specifics about the target environment (for example, load balancers, '
                                     'third-party providers, ISPs, specific configurations, protocols in use, scan '
                                     'interference) should be worked out between the ASV and scan customer. Refer to the ASV '
                                     'Program Guide published on the PCI SSC website for scan customer responsibilities, scan '
                                     'preparation, etc.',
          'subchapter': '11.3: External and internal vulnerabilities are regularly identified, prioritized, and addressed.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-06.6: Does the organization perform quarterly external vulnerability scans (outside '
                                   "the organization's network looking inward) via a reputable vulnerability service provider, "
                                   'which include rescans until passing results are obtained or all high vulnerabilities are '
                                   'resolved, as defined by the Common Vulnerability Scoring System (CVSS)?.',
                                   'Q-VPM-06: Does the organization detect vulnerabilities and configuration errors by '
                                   'recurring vulnerability scanning of systems and web applications?.',
                                   'Q-VPM-02: Does the organization ensure that vulnerabilities are properly identified, '
                                   'tracked and remediated?.',
                                   'Q-VPM-01.1: Does the organization define and manage the scope for its attack surface '
                                   'management activities?.'],
          'objective_title': '11.3.2.1: External vulnerability scans are performed after any significant change.',
          'requirement_description': '\n'
                                     'External vulnerability scans are performed after any significant change as follows: \n'
                                     '• Vulnerabilities that are scored 4.0 or higher by the CVSS are resolved. \n'
                                     '• Rescans are conducted as needed. \n'
                                     '• Scans are performed by qualified personnel and organizational independence of the '
                                     'tester exists (not required to be a QSA or ASV).',
          'subchapter': '11.3: External and internal vulnerabilities are regularly identified, prioritized, and addressed.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to '
                                   'perform penetration testing?.',
                                   'Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.',
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.',
                                   'Q-DCH-18: Does the organization retain media and data in accordance with applicable '
                                   'statutory, regulatory and contractual obligations? .'],
          'objective_title': '11.4.1: A penetration testing methodology is defined, documented, and implemented by the entity.',
          'requirement_description': '\n'
                                     'A penetration testing methodology is defined, documented, and implemented by the entity, '
                                     'and includes: \n'
                                     '• Industry-accepted penetration testing approaches. \n'
                                     '• Coverage for the entire CDE perimeter and critical systems. \n'
                                     '• Testing from both inside and outside the network.\n'
                                     '• Testing to validate any segmentation and scope-reduction controls. \n'
                                     '• Application-layer penetration testing to identify, at a minimum, the vulnerabilities '
                                     'listed in Requirement 6.2.4. \n'
                                     '• Network-layer penetration tests that encompass all components that support network '
                                     'functions as well as operating systems. \n'
                                     '• Review and consideration of threats and vulnerabilities experienced in the last 12 '
                                     'months.\n'
                                     ' • Documented approach to assessing and addressing the risk posed by exploitable '
                                     'vulnerabilities and security weaknesses found during penetration testing. \n'
                                     '• Retention of penetration testing results and remediation activities results for at '
                                     'least 12 months. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'Testing from inside the network (or “internal penetration testing”) means testing from '
                                     'both inside the CDE and into the CDE from trusted and untrusted internal networks. '
                                     'Testing from outside the network (or “external” penetration testing” means testing the '
                                     'exposed external perimeter of trusted networks, and critical systems connected to or '
                                     'accessible to public network infrastructures.',
          'subchapter': '11.4: External and internal penetration testing is regularly performed, and exploitable '
                        'vulnerabilities and secu'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to '
                                   'perform penetration testing?.',
                                   'Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.'],
          'objective_title': "11.4.2: Internal penetration testing is performed:- Per the entity's defined methodology- At "
                             'least once every 12 months.',
          'requirement_description': '\n'
                                     'Internal penetration testing is performed: \n'
                                     '• Per the entity’s defined methodology \n'
                                     '• At least once every 12 months \n'
                                     '• After any significant infrastructure or application upgrade or change \n'
                                     '• By a qualified internal resource or qualified external third-party \n'
                                     '• Organizational independence of the tester exists (not required to be a QSA or ASV).',
          'subchapter': '11.4: External and internal penetration testing is regularly performed, and exploitable '
                        'vulnerabilities and secu'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to '
                                   'perform penetration testing?.',
                                   'Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.'],
          'objective_title': "11.4.3: External penetration testing is performed:- Per the entity's defined methodology- At "
                             'least once every 12 months.',
          'requirement_description': '\n'
                                     'External penetration testing is performed: \n'
                                     '• Per the entity’s defined methodology \n'
                                     '• At least once every 12 months \n'
                                     '• After any significant infrastructure or application upgrade or change \n'
                                     '• By a qualified internal resource or qualified external third party \n'
                                     '• Organizational independence of the tester exists (not required to be a QSA or ASV).',
          'subchapter': '11.4: External and internal penetration testing is regularly performed, and exploitable '
                        'vulnerabilities and secu'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.',
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '11.4.4: Exploitable vulnerabilities and security weaknesses found during penetration testing are '
                             'corrected.',
          'requirement_description': '\n'
                                     'Exploitable vulnerabilities and security weaknesses found during penetration testing are '
                                     'corrected as follows: \n'
                                     '• In accordance with the entity’s assessment of the risk posed by the security issue as '
                                     'defined in Require ment 6.3.1. \n'
                                     '• Penetration testing is repeated to verify the corrections.',
          'subchapter': '11.4: External and internal penetration testing is regularly performed, and exploitable '
                        'vulnerabilities and secu'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to '
                                   'perform penetration testing?.',
                                   'Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.',
                                   'Q-SEA-04.1: Does the organization isolate security functions from non-security functions? '
                                   '.',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-END-16: Does the organization ensure  security functions are restricted to authorized '
                                   'individuals and enforce least privilege control requirements for necessary job '
                                   'functions?.'],
          'objective_title': '11.4.5: If segmentation is used to isolate the CDE from other networks, penetration tests are '
                             'performed on segmentation controls as follows:- At least once every 12 months and after any '
                             'changes to segmentation controls/methods.',
          'requirement_description': '\n'
                                     'If segmentation is used to isolate the CDE from other networks, penetration tests are '
                                     'performed on segmentation controls as follows: \n'
                                     '• At least once every 12 months and after any changes to segmentation controls/methods\n'
                                     '• Covering all segmentation controls/methods in use.\n'
                                     '• According to the entity’s defined penetration testing methodology. \n'
                                     '• Confirming that the segmentation controls/methods are operational and effective, and '
                                     'isolate the CDE from all out-of-scope systems. \n'
                                     '• Confirming effectiveness of any use of isolation to separate systems with differing '
                                     'security levels (see Requirement 2.2.3). \n'
                                     '• Performed by a qualified internal resource or qualified external third party. \n'
                                     '• Organizational independence of the tester exists (not required to be a QSA or ASV).',
          'subchapter': '11.4: External and internal penetration testing is regularly performed, and exploitable '
                        'vulnerabilities and secu'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-07.1: Does the organization utilize an independent assessor or penetration team to '
                                   'perform penetration testing?.',
                                   'Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.',
                                   'Q-SEA-04.1: Does the organization isolate security functions from non-security functions? '
                                   '.',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-END-16: Does the organization ensure  security functions are restricted to authorized '
                                   'individuals and enforce least privilege control requirements for necessary job '
                                   'functions?.'],
          'objective_title': '11.4.6: Additional requirement for service providers only: If segmentation is used to isolate '
                             'the CDE from other networks, penetration tests are performed on segmentation controls as '
                             'follows:- At least once every six months and after any changes to segmentation controls/methods '
                             '.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: If segmentation is used to isolate '
                                     'the CDE from other networks, penetration tests are performed on segmentation controls as '
                                     'follows: \n'
                                     '• At least once every six months and after any changes to segmentation '
                                     'controls/methods. \n'
                                     '• Covering all segmentation controls/methods in use. \n'
                                     '• According to the entity’s defined penetration testing methodology.\n'
                                     ' • Confirming that the segmentation controls/methods are operational and effective, and '
                                     'isolate the CDE from all out-of-scope systems. \n'
                                     '• Confirming effectiveness of any use of isolation to separate systems with differing '
                                     'security levels (see Requirement 2.2.3). \n'
                                     '• Performed by a qualified internal resource or qualified external third party. \n'
                                     '• Organizational independence of the tester exists (not required to be a QSA or ASV). \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider.',
          'subchapter': '11.4: External and internal penetration testing is regularly performed, and exploitable '
                        'vulnerabilities and secu'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-VPM-07: Does the organization conduct penetration testing on systems and web '
                                   'applications?.'],
          'objective_title': '11.4.7: Additional requirement for third-party hosted/cloud service providers only: Third-party '
                             'hosted/cloud service providers support to their customers for external penetration testing per '
                             'Requirement 11.4.3 and 11.4.4.',
          'requirement_description': '\n'
                                     'Additional requirement for third-party hosted/cloud service providers only: Third-party '
                                     'hosted/cloud service providers support to their customers for external penetration '
                                     'testing per Requirement 11.4.3 and 11.4.4. Applicability Notes To meet this requirement, '
                                     'third-party hosted/cloud service providers may either: \n'
                                     '• Provide evidence to its customers to show that penetration testing has been performed '
                                     'according to Requirements 11.4.3 and 11.4.4 on the customers’ subscribed infrastructure, '
                                     'or \n'
                                     '• Provide prompt access to each of their customers, so customers can perform their own '
                                     'penetration testing. Evidence provided to customers can include redacted penetration '
                                     'testing results but needs to include sufficient information to prove that all elements '
                                     'of Requirements 11.4.3 and 11.4.4 have been met on the customer’s behalf. This '
                                     'requirement applies only when the entity being assessed is a service provider managing '
                                     'third-party hosted/cloud environments. This requirement is a best practice until 31 '
                                     'March 2025, after which it will be required and must be fully considered during a PCI '
                                     'DSS assessment.',
          'subchapter': '11.4: External and internal penetration testing is regularly performed, and exploitable '
                        'vulnerabilities and secu'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-SAT-03.2: Does the organization provide training to personnel on organization-defined '
                                   'indicators of malware to recognize suspicious communications and anomalous behavior?.',
                                   'Q-NET-08: Does the organization implement Network Intrusion Detection / Prevention Systems '
                                   '(NIDS/NIPS) used to detect and/or prevent intrusions into the network? .',
                                   'Q-NET-03: Does the organization implement boundary protection mechanisms utilized to '
                                   'monitor and control communications at the external network boundary and at key internal '
                                   'boundaries within the network?.',
                                   'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS '
                                   '/ IPS) technologies on critical systems, key network segments and network choke points?.'],
          'objective_title': '11.5.1: Intrusion-detection and/or intrusion-prevention techniques are used to detect and/or '
                             'prevent intrusions into the network.',
          'requirement_description': '\n'
                                     'Intrusion-detection and/or intrusion-prevention techniques are used to detect and/or '
                                     'prevent intrusions into the network as follows: \n'
                                     '• All traffic is monitored at the perimeter of the CDE. \n'
                                     '• All traffic is monitored at critical points in the CDE. \n'
                                     '• Personnel are alerted to suspected compromises.\n'
                                     '• All intrusion-detection and prevention engines, baselines, and signatures are kept up '
                                     'to date.',
          'subchapter': '11.5: Network intrusions and unexpected file changes are detected and responded to.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-SAT-03.2: Does the organization provide training to personnel on organization-defined '
                                   'indicators of malware to recognize suspicious communications and anomalous behavior?.',
                                   'Q-NET-08: Does the organization implement Network Intrusion Detection / Prevention Systems '
                                   '(NIDS/NIPS) used to detect and/or prevent intrusions into the network? .',
                                   'Q-MON-15: Does the organization conduct covert channel analysis to identify aspects of '
                                   'communications that are potential avenues for covert channels?.',
                                   'Q-MON-11.1: Does the organization analyze network traffic to detect covert data '
                                   'exfiltration?.',
                                   'Q-MON-01.1: Does the organization implement Intrusion Detection / Prevention Systems (IDS '
                                   '/ IPS) technologies on critical systems, key network segments and network choke points?.'],
          'objective_title': '11.5.1.1: Additional requirement for service providers only: Intrusion-detection and/or '
                             'intrusion-prevention techniques detect, alert on/prevent, and address covert malware '
                             'communication channels.',
          'requirement_description': 'Additional requirement for service providers only: Intrusion-detection and/or '
                                     'intrusion-prevention techniques detect, alert on/prevent, and address covert malware '
                                     'communication channels.\n'
                                     'Applicability Notes\n'
                                     'This requirement applies only when the entity being assessed is a service provider.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '11.5: Network intrusions and unexpected file changes are detected and responded to.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-END-06: Does the organization utilize File Integrity Monitor (FIM) technology to detect '
                                   'and report unauthorized changes to system files and configurations?.',
                                   'Q-MON-01.7: Does the organization utilize a File Integrity Monitor (FIM), or similar '
                                   'change-detection technology, on critical assets to generate alerts for unauthorized '
                                   'modifications? .'],
          'objective_title': '11.5.2: A change-detection mechanism (for example, file integrity monitoring tools) is deployed.',
          'requirement_description': '\n'
                                     'A change-detection mechanism (for example, file integrity monitoring tools) is deployed '
                                     'as follows: \n'
                                     '• To alert personnel to unauthorized modification (including changes, additions, and '
                                     'deletions) of critical files \n'
                                     '• To perform critical file comparisons at least once weekly. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' For change-detection purposes, critical files are usually those that do not regularly '
                                     'change, but the modification of which could indicate a system compromise or risk of '
                                     'compromise. Change-detection mechanisms such as file integrity monitoring products '
                                     'usually come pre-configured with critical files for the related operating system. Other '
                                     'critical files, such as those for custom applications, must be evaluated and defined by '
                                     'the entity (that is, the merchant or service provider).',
          'subchapter': '11.5: Network intrusions and unexpected file changes are detected and responded to.'},
         {'chapter_title': 'Requirement 11: Test Security of Systems and Networks Regularly',
          'conformity_questions': ['Q-WEB-13: Does the organization detect and respond to Indicators of Compromise (IoC) for '
                                   'unauthorized alterations, additions, deletions or changes on websites that store, process '
                                   'and/or transmit sensitive / regulated data? .'],
          'objective_title': '11.6.1: A change- and tamper-detection mechanism is deployed.',
          'requirement_description': '\n'
                                     'A change- and tamper-detection mechanism is deployed as follows: \n'
                                     '• To alert personnel to unauthorized modification (including indicators of compromise, '
                                     'changes, additions, and deletions) to the HTTP headers and the contents of payment pages '
                                     'as received by the consumer browser. \n'
                                     '• The mechanism is configured to evaluate the received HTTP header and payment page. \n'
                                     '• The mechanism functions are performed as follows: \n'
                                     '- At least once every seven days OR \n'
                                     '- Periodically (at the frequency defined in the entity’s targeted risk analysis, which '
                                     'is performed according to all elements specified in Requirement 12.3.1). \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'The intention of this requirement is not that an entity installs software in the systems '
                                     'or browsers of its consumers, but rather that the entity uses techniques such as those '
                                     'described under Examples in the PCI DSS Guidance to prevent and detect unexpected script '
                                     'activities. This requirement is a best practice until 31 March 2025, after which it will '
                                     'be required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '11.6: Unauthorized changes on payment pages are detected and responded to.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '12.1.1: An overall information security policy is:- Established.- Published.- Maintained.- '
                             'Disseminated to all relevant personnel, as well as to relevant vendors and business partners.',
          'requirement_description': '\n'
                                     'An overall information security policy is: \n'
                                     '• Established. \n'
                                     '• Published. \n'
                                     '• Maintained. \n'
                                     '• Disseminated to all relevant personnel, as well as to relevant vendors and business '
                                     'partners.',
          'subchapter': '12.1: A comprehensive information security policy that governs and provides direction for protection '
                        'of the enti'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-GOV-03: Does the organization review cybersecurity and privacy policies, standards and '
                                   'procedures at planned intervals or if significant changes occur to ensure their continuing '
                                   'suitability, adequacy and effectiveness? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '12.1.2: The information security policy is:- Reviewed at least once every 12 months.- Updated as '
                             'needed to reflect changes to business objectives or risks to the environment.',
          'requirement_description': '\n'
                                     'The information security policy is: \n'
                                     '• Reviewed at least once every 12 months. \n'
                                     '• Updated as needed to reflect changes to business objectives or risks to the '
                                     'environment.',
          'subchapter': '12.1: A comprehensive information security policy that governs and provides direction for protection '
                        'of the enti'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-HRS-05.1: Does the organization define acceptable and unacceptable rules of behavior for '
                                   'the use of technologies, including consequences for unacceptable behavior?.',
                                   'Q-HRS-05: Does the organization require all employees and contractors to apply '
                                   'cybersecurity and privacy principles in their daily work?.',
                                   'Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.',
                                   'Q-HRS-03: Does the organization define cybersecurity responsibilities for all personnel? .',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .',
                                   'Q-GOV-02: Does the organization establish, maintain and disseminate cybersecurity and '
                                   'privacy policies, standards and procedures?.'],
          'objective_title': '12.1.3: The security policy clearly defines information security roles and responsibilities for '
                             'all personnel, and all personnel are aware and acknowledge their information security '
                             'responsibilities.',
          'requirement_description': ' The security policy clearly defines information security roles and responsibilities for '
                                     'all personnel, and all personnel are aware and acknowledge their information security '
                                     'responsibilities.',
          'subchapter': '12.1: A comprehensive information security policy that governs and provides direction for protection '
                        'of the enti'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-GOV-04: Does the organization assign a qualified individual with the mission and '
                                   'resources to centrally-manage coordinate, develop, implement and maintain an '
                                   'enterprise-wide cybersecurity and privacy program? .'],
          'objective_title': '12.1.4: Responsibility for information security is formally assigned to a Chief Information '
                             'Security Officer or other information security knowledgeable member of executive management.',
          'requirement_description': ' Responsibility for information security is formally assigned to a Chief Information '
                                     'Security Officer or other information security knowledgeable member of executive '
                                     'management. ',
          'subchapter': '12.1: A comprehensive information security policy that governs and provides direction for protection '
                        'of the enti'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.',
                                   'Q-HRS-05.4: Does the organization govern usage policies for critical technologies? .',
                                   'Q-HRS-05.3: Does the organization establish usage restrictions and implementation guidance '
                                   'for communications technologies based on the potential to cause damage to systems, if used '
                                   'maliciously? .',
                                   'Q-HRS-05.1: Does the organization define acceptable and unacceptable rules of behavior for '
                                   'the use of technologies, including consequences for unacceptable behavior?.',
                                   'Q-HRS-05: Does the organization require all employees and contractors to apply '
                                   'cybersecurity and privacy principles in their daily work?.',
                                   'Q-HRS-01: Does the organization facilitate the implementation of personnel security '
                                   'controls?.'],
          'objective_title': '12.2.1: Acceptable use policies for end-user technologies are documented and implemented, '
                             'including:- Explicit approval by authorized parties.- Acceptable uses of the technology.- List '
                             'of products approved by the company for employee use, including hardware and software.',
          'requirement_description': '\n'
                                     'Acceptable use policies for end-user technologies are documented and implemented, '
                                     'including: \n'
                                     '• Explicit approval by authorized parties. \n'
                                     '• Acceptable uses of the technology. \n'
                                     '• List of products approved by the company for employee use, including hardware and '
                                     'software. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' Examples of end-user technologies for which acceptable use policies are expected, '
                                     'include but are not limited to, remote access and wireless technologies, laptops, '
                                     'tablets, mobile phones, and removable electronic media, email usage, and Internet usage.',
          'subchapter': '12.2: Acceptable use policies for end-user technologies are defined and implemented.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .',
                                   'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to '
                                   'reduce risk and exposure to threats?.',
                                   'Q-RSK-04.1: Does the organization maintain a risk register that facilitates monitoring and '
                                   'reporting of risks?.',
                                   'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?.",
                                   'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
                                   'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, '
                                   'risk response and risk monitoring;  -  Constraints affecting risk assessments, risk '
                                   'response and risk monitoring;  -  The organizational risk tolerance; and  -  Priorities '
                                   'and trade-offs considered by the organization for managing risk?.'],
          'objective_title': '12.3.1: Each PCI DSS requirement that provides flexibility for how frequently it is performed '
                             '(for example, requirements to be performed periodically) is supported by a targeted risk '
                             'analysis that is documented.',
          'requirement_description': '\n'
                                     'Each PCI DSS requirement that provides flexibility for how frequently it is performed '
                                     '(for example, requirements to be performed periodically) is supported by a targeted risk '
                                     'analysis that is documented and includes: \n'
                                     '• Identification of the assets being protected. \n'
                                     '• Identification of the threat(s) that the requirement is protecting against. \n'
                                     '• Identification of factors that contribute to the likelihood and/or impact of a threat '
                                     'being realized. \n'
                                     '• Resulting analysis that determines, and includes justification for, how frequently the '
                                     'requirement must be performed to minimize the likelihood of the threat being realized. \n'
                                     '• Review of each targeted risk analysis at least once every 12 months to determine '
                                     'whether the results are still valid or if an updated risk analysis is needed. \n'
                                     '• Performance of updated risk analyses when needed, as determined by the annual '
                                     'review. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.3: Targeted risks to the cardholder data environment are formally identified, evaluated, and '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-RSK-07: Does the organization routinely update risk assessments and react accordingly '
                                   'upon identifying new security vulnerabilities, including using outside sources for '
                                   'security vulnerability information? .',
                                   'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to '
                                   'reduce risk and exposure to threats?.',
                                   'Q-RSK-04.1: Does the organization maintain a risk register that facilitates monitoring and '
                                   'reporting of risks?.',
                                   'Q-RSK-04: Does the organization conduct an annual assessment of risk that includes the '
                                   'likelihood and magnitude of harm, from unauthorized access, use, disclosure, disruption, '
                                   "modification or destruction of the organization's systems and data?.",
                                   'Q-RSK-03: Does the organization identify and document risks, both internal and external? .',
                                   'Q-RSK-01.1: Does the organization identify:  -  Assumptions affecting risk assessments, '
                                   'risk response and risk monitoring;  -  Constraints affecting risk assessments, risk '
                                   'response and risk monitoring;  -  The organizational risk tolerance; and  -  Priorities '
                                   'and trade-offs considered by the organization for managing risk?.'],
          'objective_title': '12.3.2: A targeted risk analysis is performed for each PCI DSS requirement that the entity meets '
                             'with the customized approach.',
          'requirement_description': '\n'
                                     'A targeted risk analysis is performed for each PCI DSS requirement that the entity meets '
                                     'with the customized approach, to include: \n'
                                     '• Documented evidence detailing each element specified in Appendix B: Guidance and '
                                     'Instructions for Using Customized Approach (including, at a minimum, a controls matrix '
                                     'and risk analysis). \n'
                                     '• Approval of documented evidence by senior management. \n'
                                     '• Performance of the targeted analysis of risk at least once every 12 months. New '
                                     'requirement - effective immediately \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This only applies to entities using a Customized Approach.',
          'subchapter': '12.3: Targeted risks to the cardholder data environment are formally identified, evaluated, and '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-CRY-01.5: Does the organization identify, document and review deployed cryptographic '
                                   'cipher suites and protocols to proactively respond to industry trends regarding the '
                                   'continued viability of utilized cryptographic cipher suites and protocols?.',
                                   'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.'],
          'objective_title': '12.3.3: Cryptographic cipher suites and protocols in use are documented and reviewed at least '
                             'once every 12 months.',
          'requirement_description': '\n'
                                     'Cryptographic cipher suites and protocols in use are documented and reviewed at least '
                                     'once every 12 months, including at least the following: • An up-to-date inventory of all '
                                     'cryptographic cipher suites and protocols in use, including purpose and where used.\n'
                                     ' • Active monitoring of industry trends regarding continued viability of all '
                                     'cryptographic cipher suites and protocols in use. \n'
                                     '• A documented strategy to respond to anticipated changes in cryptographic '
                                     'vulnerabilities. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' The requirement applies to all cryptographic suites and protocols used to meet PCI DSS '
                                     'requirements. This requirement is a best practice until 31 March 2025, after which it '
                                     'will be required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.3: Targeted risks to the cardholder data environment are formally identified, evaluated, and '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-SEA-07.1: Does the organization manage the usable lifecycles of systems? .',
                                   'Q-SEA-02.3: Does the organization conduct ongoing technical debt reviews of hardware and '
                                   'software technologies to remediate outdated and/or unsupported technologies?.'],
          'objective_title': '12.3.4: Hardware and software technologies in use are reviewed at least once every 12 months.',
          'requirement_description': '\n'
                                     'Hardware and software technologies in use are reviewed at least once every 12 months, '
                                     'including at least the following: \n'
                                     '• Analysis that the technologies continue to receive security fixes from vendors '
                                     'promptly. \n'
                                     '• Analysis that the technologies continue to support (and do not preclude) the entity’s '
                                     'PCI DSS compliance. \n'
                                     '• Documentation of any industry announcements or trends related to a technology, such as '
                                     'when a vendor has announced “end of life” plans for a technology. \n'
                                     '• Documentation of a plan, approved by senior management, to remediate outdated '
                                     'technologies, including those for which vendors have announced “end of life” plans. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.3: Targeted risks to the cardholder data environment are formally identified, evaluated, and '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.4: Does the organization formally document a Customer Responsibility Matrix '
                                   '(CRM), delineating assigned responsibilities for controls between the Cloud Service '
                                   'Provider (CSP) and its customers.?.',
                                   'Q-CLD-06.1: Does the organization formally document a Customer Responsibility Matrix '
                                   '(CRM), delineating assigned responsibilities for controls between the Cloud Service '
                                   'Provider (CSP) and its customers?.'],
          'objective_title': '12.4.1: Additional requirement for service providers only: Responsibility is established by '
                             'executive management for the protection of cardholder data and a PCI DSS compliance program to '
                             'include:- Overall accountability for maintaining PCI DSS compliance.- Defining a charter for a '
                             'PCI DSS compliance program and communication to executive management.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: Responsibility is established by '
                                     'executive management for the protection of cardholder data and a PCI DSS compliance '
                                     'program to include: \n'
                                     '• Overall accountability for maintaining PCI DSS compliance. \n'
                                     '• Defining a charter for a PCI DSS compliance program and communication to executive '
                                     'management. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider. '
                                     'Executive management may include C-level positions, board of directors, or equivalent. '
                                     'The specific titles will depend on the particular organizational structure. '
                                     'Responsibility for the PCI DSS compliance program may be assigned to individual roles '
                                     'and/or to business units within the organization.',
          'subchapter': '12.4: PCI DSS compliance is managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?.",
                                   'Q-CPL-03.2: Does the organization regularly review technology assets for adherence to the '
                                   "organization's cybersecurity and privacy policies and standards? .",
                                   'Q-CPL-03: Does the organization ensure managers regularly review the processes and '
                                   'documented procedures within their area of responsibility to adhere to appropriate '
                                   'security policies, standards and other applicable requirements?.',
                                   'Q-CPL-01.1: Does the organization document and review instances of non-compliance with '
                                   'statutory, regulatory and/or contractual obligations to develop appropriate risk '
                                   'mitigation actions?.',
                                   "Q-CLD-12: Does the organization prevent 'side channel attacks' when using a Content "
                                   "Delivery Network (CDN) by restricting access to the origin server's IP address to the CDN "
                                   'and an authorized management network?.'],
          'objective_title': '12.4.2: Additional requirement for service providers only: Reviews are performed at least once '
                             'every three months to confirm personnel are performing their tasks in accordance with all '
                             'security policies and all operational procedures.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: Reviews are performed at least once '
                                     'every three months to confirm personnel are performing their tasks in accordance with '
                                     'all security policies and all operational procedures. Reviews are performed by personnel '
                                     'other than those responsible for performing the given task and include, but not limited '
                                     'to, the following tasks: \n'
                                     '• Daily log reviews. \n'
                                     '• Configuration reviews for network security controls. \n'
                                     '• Applying configuration standards to new systems. \n'
                                     '• Responding to security alerts. \n'
                                     '• Change-management processes. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider.',
          'subchapter': '12.4: PCI DSS compliance is managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?.",
                                   'Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.'],
          'objective_title': '12.4.2.1: Additional requirement for service providers only: Reviews conducted in accordance '
                             'with Requirement 12.4.2 are documented.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: Reviews conducted in accordance with '
                                     'Requirement 12.4.2 are documented to include: \n'
                                     '• Results of the reviews. \n'
                                     '• Documented remediation actions taken for any tasks that were found to not be performed '
                                     'at Requirement 12.4.2. \n'
                                     '• Review and sign-off of results by personnel assigned responsibility for the PCI DSS '
                                     'compliance program. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider.',
          'subchapter': '12.4: PCI DSS compliance is managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-CPL-01.2: Does the organization document and validate the scope of cybersecurity and '
                                   'privacy controls that are determined to meet statutory, regulatory and/or contractual '
                                   'compliance obligations?.',
                                   'Q-AST-04.3: Does the organization create and maintain a current inventory of systems, '
                                   'applications and services that are in scope for statutory, regulatory and/or contractual '
                                   'compliance obligations that provides sufficient detail to determine control applicability, '
                                   'based on asset scope categorization?.'],
          'objective_title': '12.5.1: An inventory of system components that are in scope for PCI DSS, including a description '
                             'of function/use, is maintained and kept current.',
          'requirement_description': ' An inventory of system components that are in scope for PCI DSS, including a '
                                     'description of function/use, is maintained and kept current.',
          'subchapter': '12.5: PCI DSS scope is documented and validated.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-04.4: Does the organization restrict the location of information processing/storage '
                                   'based on business requirements? .',
                                   'Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-CPL-01.2: Does the organization document and validate the scope of cybersecurity and '
                                   'privacy controls that are determined to meet statutory, regulatory and/or contractual '
                                   'compliance obligations?.'],
          'objective_title': '12.5.2: PCI DSS scope is documented and confirmed by the entity at least once every 12 months '
                             'and upon significant change to the in-scope environment.',
          'requirement_description': '\n'
                                     'PCI DSS scope is documented and confirmed by the entity at least once every 12 months '
                                     'and upon significant change to the in-scope environment. At a minimum, the scoping '
                                     'validation includes: \n'
                                     '• Identifying all data flows for the various payment stages (for example, authorization, '
                                     'capture settlement, chargebacks, and refunds) and acceptance channels (for example, '
                                     'card-present, card-not-present, and e-commerce). \n'
                                     '• Updating all data-flow diagrams per Requirement 1.2.4. \n'
                                     '• Identifying all locations where account data is stored, processed, and transmitted, '
                                     'including but not limited to: 1) any locations outside of the currently defined CDE, 2) '
                                     'applications that process CHD, 3) transmissions between systems and networks, and 4) '
                                     'file backups. \n'
                                     '• Identifying all system components in the CDE, connected to the CDE, or that could '
                                     'impact security of the CDE. \n'
                                     '• Identifying all segmentation controls in use and the environment(s) from which the CDE '
                                     'is segmented, including justification for environments being out of scope.\n'
                                     ' • Identifying all connections from third-party entities with access to the CDE. \n'
                                     '• Confirming that all identified data flows, account data, system components, '
                                     'segmentation controls, and connections from third parties with access to the CDE are '
                                     'included in scope. New requirement - effective immediately \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This annual confirmation of PCI DSS scope is an activity expected to be performed by the '
                                     'entity under assessment, and is not the same, nor is it intended to be replaced by, the '
                                     'scoping confirmation performed by the entity’s assessor during the annual assessment.',
          'subchapter': '12.5: PCI DSS scope is documented and validated.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.5: Does the organization perform recurring validation of the Responsible, '
                                   'Accountable, Supportive, Consulted & Informed (RASCI) matrix, or similar documentation, to '
                                   'ensure cybersecurity and privacy control assignments accurately reflect current business '
                                   'practices, compliance obligations, technologies and stakeholders? .',
                                   'Q-AST-04.3: Does the organization create and maintain a current inventory of systems, '
                                   'applications and services that are in scope for statutory, regulatory and/or contractual '
                                   'compliance obligations that provides sufficient detail to determine control applicability, '
                                   'based on asset scope categorization?.',
                                   'Q-AST-04.2: Does the organization ensure control applicability is appropriately-determined '
                                   'for systems, applications, services and third parties by graphically representing '
                                   'applicable boundaries?.'],
          'objective_title': '12.5.2.1: Additional requirement for service providers only: PCI DSS scope is documented and '
                             'confirmed by the entity at least once every six months and after significant changes. At a '
                             'minimum, the scoping validation includes all the elements specified in Requirement 12.5.2.',
          'requirement_description': 'Additional requirement for service providers only: PCI DSS scope is documented and '
                                     'confirmed by the entity at least once every six months and after significant changes. At '
                                     'a minimum, the scoping validation includes all the elements specified in Requirement '
                                     '12.5.2.\n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.5: PCI DSS scope is documented and validated.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.5: Does the organization perform recurring validation of the Responsible, '
                                   'Accountable, Supportive, Consulted & Informed (RASCI) matrix, or similar documentation, to '
                                   'ensure cybersecurity and privacy control assignments accurately reflect current business '
                                   'practices, compliance obligations, technologies and stakeholders? .'],
          'objective_title': '12.5.3: Additional requirement for service providers only: Significant changes to organizational '
                             'structure result in a documented (internal) review of the impact to PCI DSS scope and '
                             'applicability of controls, with results communicated to executive management.',
          'requirement_description': ' Additional requirement for service providers only: Significant changes to '
                                     'organizational structure result in a documented (internal) review of the impact to PCI '
                                     'DSS scope and applicability of controls, with results communicated to executive '
                                     'management.\n'
                                     'Applicability Notes\n'
                                     'This requirement applies only when the entity being assessed is a service provider.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.5: PCI DSS scope is documented and validated.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-SAT-04: Does the organization document, retain and monitor individual training '
                                   'activities, including basic security awareness training, ongoing awareness training and '
                                   'specific-system training?.',
                                   'Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .'],
          'objective_title': '12.6.1: A formal security awareness program is implemented to make all personnel aware of the '
                             "entity's information security policy and procedures and their role in protecting the cardholder "
                             'data.',
          'requirement_description': ' A formal security awareness program is implemented to make all personnel aware of the '
                                     'entity’s information security policy and procedures and their role in protecting the '
                                     'cardholder data.',
          'subchapter': '12.6: Security awareness education is an ongoing activity'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-SAT-01: Does the organization facilitate the implementation of security workforce '
                                   'development and awareness controls? .'],
          'objective_title': '12.6.2: The security awareness program is:- Reviewed at least once every 12 months, and- Updated '
                             'as needed to address any new threats and vulnerabilities that may impact the security of the '
                             "entity's CDE, or the information provided to personnel about their role in protecting cardholder "
                             'data.',
          'requirement_description': '\n'
                                     'The security awareness program is: \n'
                                     '• Reviewed at least once every 12 months, and \n'
                                     '• Updated as needed to address any new threats and vulnerabilities that may impact the '
                                     'security of the entity’s CDE, or the information provided to personnel about their role '
                                     'in protecting cardholder data. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.6: Security awareness education is an ongoing activity'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness '
                                   "training that is specific to the cyber threats that the user might encounter the user's "
                                   'specific day-to-day business operations?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .',
                                   'Q-HRS-05.7: Does the organization ensure personnel receive recurring familiarization with '
                                   "the organization's cybersecurity and privacy policies and provide acknowledgement?.",
                                   'Q-HRS-03.1: Does the organization communicate with users about their roles and '
                                   'responsibilities to maintain a safe and secure working environment?.'],
          'objective_title': '12.6.3: Personnel receive security awareness training as follows:- Upon hire and at least once '
                             'every 12 months.',
          'requirement_description': '\n'
                                     'Personnel receive security awareness training as follows: \n'
                                     '• Upon hire and at least once every 12 months. \n'
                                     '• Multiple methods of communication are used.\n'
                                     '• Personnel acknowledge at least once every 12 months that they have read and understood '
                                     'the information security policy and procedures.',
          'subchapter': '12.6: Security awareness education is an ongoing activity'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness '
                                   "training that is specific to the cyber threats that the user might encounter the user's "
                                   'specific day-to-day business operations?.',
                                   'Q-SAT-03.3: Does the organization ensure that every user accessing a system processing, '
                                   'storing or transmitting sensitive information is formally trained in data handling '
                                   'requirements?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.',
                                   'Q-SAT-02.2: Does the organization include awareness training on recognizing and reporting '
                                   'potential and actual instances of social engineering and social mining?.',
                                   'Q-SAT-02: Does the organization provide all employees and contractors appropriate '
                                   'awareness education and training that is relevant for their job function? .'],
          'objective_title': '12.6.3.1: Security awareness training includes awareness of threats and vulnerabilities that '
                             'could impact the security of the CDE, including but not limited to:- Phishing and related '
                             'attacks.- Social engineering.',
          'requirement_description': '\n'
                                     'Security awareness training includes awareness of threats and vulnerabilities that could '
                                     'impact the security of the CDE, including but not limited to: \n'
                                     '• Phishing and related attacks. \n'
                                     '• Social engineering. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' See Requirement 5.4.1 for guidance on the difference between technical and automated '
                                     'controls to detect and protect users from phishing attacks, and this requirement for '
                                     'providing users security awareness training about phishing and social engineering. These '
                                     'are two separate and distinct requirements, and one is not met by implementing controls '
                                     'required by the other one. This requirement is a best practice until 31 March 2025, '
                                     'after which it will be required and must be fully considered during a PCI DSS '
                                     'assessment.',
          'subchapter': '12.6: Security awareness education is an ongoing activity'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-SAT-03.6: Does the organization provide role-based cybersecurity and privacy awareness '
                                   "training that is specific to the cyber threats that the user might encounter the user's "
                                   'specific day-to-day business operations?.',
                                   'Q-SAT-03.3: Does the organization ensure that every user accessing a system processing, '
                                   'storing or transmitting sensitive information is formally trained in data handling '
                                   'requirements?.',
                                   'Q-SAT-03: Does the organization provide role-based security-related training:   -  Before '
                                   'authorizing access to the system or performing assigned duties;   -  When required by '
                                   'system changes; and   -  Annually thereafter?.'],
          'objective_title': '12.6.3.2: Security awareness training includes awareness about the acceptable use of end-user '
                             'technologies in accordance with Requirement 12.2.1.',
          'requirement_description': 'Security awareness training includes awareness about the acceptable use of end-user '
                                     'technologies in accordance with Requirement 12.2.1.\n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.6: Security awareness education is an ongoing activity'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-HRS-04.1: Does the organization ensure that individuals accessing a system that stores, '
                                   'transmits or processes information requiring special protection satisfy '
                                   'organization-defined personnel screening criteria?.',
                                   'Q-HRS-04: Does the organization manage personnel security risk by screening individuals '
                                   'prior to authorizing access?.',
                                   'Q-HRS-02.1: Does the organization ensure that every user accessing a system that '
                                   'processes, stores, or transmits sensitive information is cleared and regularly trained to '
                                   'handle the information in question?.',
                                   'Q-HRS-02: Does the organization manage personnel security risk by assigning a risk '
                                   'designation to all positions and establishing screening criteria for individuals filling '
                                   'those positions?.',
                                   'Q-HRS-01: Does the organization facilitate the implementation of personnel security '
                                   'controls?.'],
          'objective_title': '12.7.1: Potential personnel who will have access to the CDE are screened, within the constraints '
                             'of local laws, prior to hire to minimize the risk of attacks from internal sources.',
          'requirement_description': ' Potential personnel who will have access to the CDE are screened, within the '
                                     'constraints of local laws, prior to hire to minimize the risk of attacks from internal '
                                     'sources. \n'
                                     'Applicability Notes\n'
                                     'For those potential personnel to be hired for positions such as store cashiers, who only '
                                     'have access to one card number at a time when facilitating a transaction, this '
                                     'requirement is a recommendation only.',
          'subchapter': '12.7: Personnel are screened to reduce risks from insider threats.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.5: Does the organization perform recurring validation of the Responsible, '
                                   'Accountable, Supportive, Consulted & Informed (RASCI) matrix, or similar documentation, to '
                                   'ensure cybersecurity and privacy control assignments accurately reflect current business '
                                   'practices, compliance obligations, technologies and stakeholders? .',
                                   'Q-TPM-01.1: Does the organization maintain a current, accurate and complete list of '
                                   'Third-Party Service Providers (TSP) that can potentially impact the Confidentiality, '
                                   "Integrity, Availability and/or Safety (CIAS) of the organization's systems, applications, "
                                   'services and data?.',
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-NET-14: Does the organization define, control and review organization-approved, secure '
                                   'remote access methods?.',
                                   'Q-CLD-01: Does the organization facilitate the implementation of cloud management controls '
                                   'to ensure cloud instances are secure and in-line with industry practices? .'],
          'objective_title': '12.8.1: A list of all third-party service providers (TPSPs) with which account data is shared or '
                             'that could affect the security of account data is maintained, including a description for each '
                             'of the services provided.',
          'requirement_description': ' A list of all third-party service providers (TPSPs) with which account data is shared '
                                     'or that could affect the security of account data is maintained, including a description '
                                     'for each of the services provided.\n'
                                     'Applicability Notes\n'
                                     'The use of a PCI DSS compliant TPSP does not make an entity PCI DSS compliant, nor does '
                                     'it remove the entity’s responsibility for its own PCI DSS compliance.',
          'subchapter': '12.8: Risk to information assets associated with third-party service provider (TPSP) relationships is '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.4: Does the organization formally document a Customer Responsibility Matrix '
                                   '(CRM), delineating assigned responsibilities for controls between the Cloud Service '
                                   'Provider (CSP) and its customers.?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': '12.8.2: Written agreements with TPSPs are maintained as follows:- Written agreements are '
                             'maintained with all TPSPs with which account data is shared or that could affect the security of '
                             'the CDE.',
          'requirement_description': '\n'
                                     'Written agreements with TPSPs are maintained as follows: \n'
                                     '• Written agreements are maintained with all TPSPs with which account data is shared or '
                                     'that could affect the security of the CDE. \n'
                                     '• Written agreements include acknowledgements from TPSPs that they are responsible for '
                                     'the security of account data the TPSPs possess or otherwise store, process, or transmit '
                                     'on behalf of the entity, or to the extent that they could impact the security of the '
                                     'entity’s CDE. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' The exact wording of an acknowledgment will depend on the agreement between the two '
                                     'parties, the details of the service being provided, and the responsibilities assigned to '
                                     'each party. The acknowledgment does not have to include the exact wording provided in '
                                     'this requirement. Evidence that a TPSP is meeting PCI DSS requirements (for example, a '
                                     'PCI DSS Attestation of Compliance (AOC) or a declaration on a company’s website) is not '
                                     'the same as a written agreement specified in this requirement.',
          'subchapter': '12.8: Risk to information assets associated with third-party service provider (TPSP) relationships is '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-04.1: Does the organization conduct a risk assessment prior to the acquisition or '
                                   'outsourcing of technology-related services?.',
                                   'Q-TPM-04: Does the organization mitigate the risks associated with third-party access to '
                                   "the organization's systems and data?."],
          'objective_title': '12.8.3: An established process is implemented for engaging TPSPs, including proper due diligence '
                             'prior to engagement.',
          'requirement_description': ' An established process is implemented for engaging TPSPs, including proper due '
                                     'diligence prior to engagement.',
          'subchapter': '12.8: Risk to information assets associated with third-party service provider (TPSP) relationships is '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-08: Does the organization monitor, regularly review and audit Third-Party Service '
                                   'Providers (TSP) for compliance with established contractual requirements for cybersecurity '
                                   'and privacy controls? .'],
          'objective_title': '12.8.4: A program is implemented to monitor TPSPs- PCI DSS compliance status at least once every '
                             '12 months.',
          'requirement_description': ' A program is implemented to monitor TPSPs’ PCI DSS compliance status at least once '
                                     'every 12 months. \n'
                                     'Applicability Notes\n'
                                     'Where an entity has an agreement with a TPSP for meeting PCI DSS requirements on behalf '
                                     'of the entity (for example, via a firewall service), the entity must work with the TPSP '
                                     'to make sure the applicable PCI DSS requirements are met. If the TPSP does not meet '
                                     'those applicable PCI DSS requirements, then those requirements are also “not in place” '
                                     'for the entity.',
          'subchapter': '12.8: Risk to information assets associated with third-party service provider (TPSP) relationships is '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.4: Does the organization formally document a Customer Responsibility Matrix '
                                   '(CRM), delineating assigned responsibilities for controls between the Cloud Service '
                                   'Provider (CSP) and its customers.?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?."],
          'objective_title': '12.8.5: Information is maintained about which PCI DSS requirements are managed by each TPSP, '
                             'which are managed by the entity, and any that are shared between the TPSP and the entity.',
          'requirement_description': ' Information is maintained about which PCI DSS requirements are managed by each TPSP, '
                                     'which are managed by the entity, and any that are shared between the TPSP and the '
                                     'entity.',
          'subchapter': '12.8: Risk to information assets associated with third-party service provider (TPSP) relationships is '
                        'managed.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.4: Does the organization formally document a Customer Responsibility Matrix '
                                   '(CRM), delineating assigned responsibilities for controls between the Cloud Service '
                                   'Provider (CSP) and its customers.?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?.",
                                   'Q-TPM-04: Does the organization mitigate the risks associated with third-party access to '
                                   "the organization's systems and data?.",
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.',
                                   'Q-PRI-01.6: Does the organization ensure Personal Data (PD) is protected by security '
                                   'safeguards that are sufficient and appropriately scoped to protect the confidentiality and '
                                   'integrity of the PD?.'],
          'objective_title': '12.9.1: Additional requirement for service providers only: TPSPs acknowledge in writing to '
                             'customers that they are responsible for the security of account data the TPSP possesses or '
                             'otherwise stores, processes, or transmits on behalf of the customer, or to the extent that they '
                             "could impact the security of the customer's CDE.",
          'requirement_description': ' Additional requirement for service providers only: TPSPs acknowledge in writing to '
                                     'customers that they are responsible for the security of account data the TPSP possesses '
                                     'or otherwise stores, processes, or transmits on behalf of the customer, or to the extent '
                                     'that they could impact the security of the customer’s CDE. \n'
                                     'Applicability Notes\n'
                                     'This requirement applies only when the entity being assessed is a service provider.\n'
                                     'The exact wording of an acknowledgment will depend on the agreement between the two '
                                     'parties, the details of the service being provided, and the responsibilities assigned to '
                                     'each party. The acknowledgment does not have to include the exact wording provided in '
                                     'this requirement.',
          'subchapter': '12.9: Third-party service providers (TPSPs) support their customers- PCI DSS compliance.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-TPM-05.4: Does the organization formally document a Customer Responsibility Matrix '
                                   '(CRM), delineating assigned responsibilities for controls between the Cloud Service '
                                   'Provider (CSP) and its customers.?.',
                                   'Q-TPM-05: Does the organization identify, regularly review and document third-party '
                                   'confidentiality, Non-Disclosure Agreements (NDAs) and other contracts that reflect the '
                                   "organization's needs to protect systems and data?.",
                                   'Q-TPM-04: Does the organization mitigate the risks associated with third-party access to '
                                   "the organization's systems and data?.",
                                   'Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': '12.9.2: Additional requirement for service providers only: TPSPs support their customers- '
                             'requests for information to meet Requirements 12.8.4 and 12.8.5.',
          'requirement_description': '\n'
                                     'Additional requirement for service providers only: TPSPs support their customers’ '
                                     'requests for information to meet Requirements 12.8.4 and 12.8.5 by providing the '
                                     'following upon customer request: \n'
                                     '• PCI DSS compliance status information for any service the TPSP performs on behalf of '
                                     'customers (Requirement 12.8.4). \n'
                                     '• Information about which PCI DSS requirements are the responsibility of the TPSP and '
                                     'which are the responsibility of the customer, including any shared responsibilities '
                                     '(Requirement 12.8.5). New requirement - effective immediately \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement applies only when the entity being assessed is a service provider.',
          'subchapter': '12.9: Third-party service providers (TPSPs) support their customers- PCI DSS compliance.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.'],
          'objective_title': '12.10.1: An incident response plan exists and is ready to be activated in the event of a '
                             'suspected or confirmed security incident.',
          'requirement_description': '\n'
                                     'An incident response plan exists and is ready to be activated in the event of a '
                                     'suspected or confirmed security incident. The plan includes, but is not limited to: \n'
                                     '• Roles, responsibilities, and communication and contact strategies in the event of a '
                                     'suspected or confirmed security incident, including notification of payment brands and '
                                     'acquirers, at a minimum. \n'
                                     '• Incident response procedures with specific containment and mitigation activities for '
                                     'different types of incidents. \n'
                                     '• Business recovery and continuity procedures. \n'
                                     '• Data backup processes. \n'
                                     '• Analysis of legal requirements for reporting compromises. \n'
                                     '• Coverage and responses of all critical system components. \n'
                                     '• Reference or inclusion of incident response procedures from the payment brands.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-IRO-06: Does the organization formally test incident response capabilities through '
                                   'realistic exercises to determine the operational effectiveness of those capabilities?.',
                                   'Q-IRO-04.2: Does the organization regularly review and modify incident response practices '
                                   'to incorporate lessons learned, business process changes and industry developments, as '
                                   'necessary?.'],
          'objective_title': '12.10.2: At least once every 12 months, the security incident response plan is:- Reviewed and '
                             'the content is updated as needed.- Tested, including all elements listed in Requirement 12.10.1.',
          'requirement_description': '\n'
                                     'At least once every 12 months, the security incident response plan is: \n'
                                     '• Reviewed and the content is updated as needed. \n'
                                     '• Tested, including all elements listed in Requirement 12.10.1.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-IRO-07: Does the organization establish an integrated team of cybersecurity, IT and '
                                   'business function representatives that are capable of addressing cybersecurity and privacy '
                                   'incident response operations?.'],
          'objective_title': '12.10.3: Specific personnel are designated to be available on a 24/7 basis to respond to '
                             'suspected or confirmed security incidents.',
          'requirement_description': 'Specific personnel are designated to be available on a 24/7 basis to respond to '
                                     'suspected or confirmed security incidents.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-IRO-05: Does the organization train personnel in their incident response roles and '
                                   'responsibilities?.'],
          'objective_title': '12.10.4: Personnel responsible for responding to suspected and confirmed security incidents are '
                             'appropriately and periodically trained on their incident response responsibilities.',
          'requirement_description': 'Personnel responsible for responding to suspected and confirmed security incidents are '
                                     'appropriately and periodically trained on their incident response responsibilities.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-IRO-05: Does the organization train personnel in their incident response roles and '
                                   'responsibilities?.'],
          'objective_title': '12.10.4.1: The frequency of periodic training for incident response personnel is defined in the '
                             "entity's targeted risk analysis which is performed according to all elements specified in "
                             'Requirement 12.3.1.',
          'requirement_description': 'The frequency of periodic training for incident response personnel is defined in the '
                                     'entity’s targeted risk analysis which is performed according to all elements specified '
                                     'in Requirement 12.3.1.\n'
                                     'Applicability Notes\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-NET-12.1: Does the organization protect external and internal wireless links from signal '
                                   'parameter attacks through monitoring for unauthorized wireless connections, including '
                                   'scanning for unauthorized wireless access points and taking appropriate action, if an '
                                   'unauthorized connection is discovered?.',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.',
                                   "Q-IRO-02: Does the organization's incident handling processes cover preparation, detection "
                                   'and analysis, containment, eradication and recovery?.',
                                   'Q-MON-02.1: Does the organization use automated mechanisms to correlate logs from across '
                                   'the enterprise by a Security Incident Event Manager (SIEM) or similar automated tool, to '
                                   'maintain situational awareness?.'],
          'objective_title': '12.10.5: The security incident response plan includes monitoring and responding to alerts from '
                             'security monitoring systems.',
          'requirement_description': '\n'
                                     'The security incident response plan includes monitoring and responding to alerts from '
                                     'security monitoring systems, including but not limited to: \n'
                                     '• Intrusion-detection and intrusion-prevention systems. \n'
                                     '• Network security controls. \n'
                                     '• Change-detection mechanisms for critical files. \n'
                                     '• The change-and tamper-detection mechanism for payment pages. This bullet is a best '
                                     'practice until its effective date; refer to Applicability Notes below for details. \n'
                                     '• Detection of unauthorized wireless access points. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' The bullet above (for monitoring and responding to alerts from a change- and '
                                     'tamper-detection mechanism for payment pages) is a best practice until 31 March 2025, '
                                     'after which it will be required as part of Requirement 12.10.5 and must be fully '
                                     'considered during a PCI DSS assessment.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-IRO-13: Does the organization incorporate lessons learned from analyzing and resolving '
                                   'cybersecurity and privacy incidents to reduce the likelihood or impact of future '
                                   'incidents? .',
                                   'Q-IRO-04.2: Does the organization regularly review and modify incident response practices '
                                   'to incorporate lessons learned, business process changes and industry developments, as '
                                   'necessary?.'],
          'objective_title': '12.10.6: The security incident response plan is modified and evolved according to lessons '
                             'learned and to incorporate industry developments.',
          'requirement_description': 'The security incident response plan is modified and evolved according to lessons learned '
                                     'and to incorporate industry developments.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Requirement 12: Support information security with organizational policies and programs',
          'conformity_questions': ['Q-IRO-12: Does the organization respond to sensitive information spills?.',
                                   'Q-IRO-04: Does the organization maintain and make available a current and viable Incident '
                                   'Response Plan (IRP) to all stakeholders?.'],
          'objective_title': '12.10.7: Incident response procedures are in place, to be initiated upon the detection of stored '
                             'PAN anywhere it is not expected.',
          'requirement_description': '\n'
                                     'Incident response procedures are in place, to be initiated upon the detection of stored '
                                     'PAN anywhere it is not expected, and include: \n'
                                     '• Determining what to do if PAN is discovered outside the CDE, including its retrieval, '
                                     'secure deletion, and/or migration into the currently defined CDE, as applicable. \n'
                                     '• Identifying whether sensitive authentication data is stored with PAN. \n'
                                     '• Determining where the account data came from and how it ended up where it was not '
                                     'expected. \n'
                                     '• Remediating data leaks or process gaps that resulted in the account data being where '
                                     'it was not expected. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': '12.10: Suspected and confirmed security incidents that could impact the CDE are responded to '
                        'immediately.'},
         {'chapter_title': 'Appendix A1: Additional PCI DSS Requirements for Shared Hosting Providers',
          'conformity_questions': ['Q-CLD-06: Does the organization ensure multi-tenant owned or managed assets (physical and '
                                   'virtual) are designed and governed such that provider and customer (tenant) user access is '
                                   'appropriately segmented from other tenant users?.'],
          'objective_title': 'A1.1.1: Logical separation is implemented as follows:- The provider cannot access its customers- '
                             "environments without authorization.- Customers cannot access the provider's environment without "
                             'authorization.',
          'requirement_description': '\n'
                                     'Logical separation is implemented as follows: \n'
                                     '• The provider cannot access its customers’ environments without authorization. \n'
                                     '• Customers cannot access the provider’s environment without authorization. \n'
                                     ' \n'
                                     'Applicability Notes \n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': 'A1.1: Multi-tenant service providers protect and segregate all customer environments and data.'},
         {'chapter_title': 'Appendix A1: Additional PCI DSS Requirements for Shared Hosting Providers',
          'conformity_questions': ['Q-CLD-06: Does the organization ensure multi-tenant owned or managed assets (physical and '
                                   'virtual) are designed and governed such that provider and customer (tenant) user access is '
                                   'appropriately segmented from other tenant users?.'],
          'objective_title': 'A1.1.2: Controls are implemented such that each customer only has permission to access its own '
                             'cardholder data and CDE.',
          'requirement_description': ' Controls are implemented such that each customer only has permission to access its own '
                                     'cardholder data and CDE.',
          'subchapter': 'A1.1: Multi-tenant service providers protect and segregate all customer environments and data.'},
         {'chapter_title': 'Appendix A1: Additional PCI DSS Requirements for Shared Hosting Providers',
          'conformity_questions': ['Q-CLD-06: Does the organization ensure multi-tenant owned or managed assets (physical and '
                                   'virtual) are designed and governed such that provider and customer (tenant) user access is '
                                   'appropriately segmented from other tenant users?.'],
          'objective_title': 'A1.1.3: Controls are implemented such that each customer can only access resources allocated to '
                             'them.',
          'requirement_description': ' Controls are implemented such that each customer can only access resources allocated to '
                                     'them.',
          'subchapter': 'A1.1: Multi-tenant service providers protect and segregate all customer environments and data.'},
         {'chapter_title': 'Appendix A1: Additional PCI DSS Requirements for Shared Hosting Providers',
          'conformity_questions': ['Q-NET-08.1: Does the organization require De-Militarized Zone (DMZ) network segments to '
                                   'separate untrusted networks from trusted networks?.',
                                   'Q-NET-06: Does the organization logically or physically segment information flows to '
                                   'accomplish network segmentation?.',
                                   'Q-CLD-06: Does the organization ensure multi-tenant owned or managed assets (physical and '
                                   'virtual) are designed and governed such that provider and customer (tenant) user access is '
                                   'appropriately segmented from other tenant users?.'],
          'objective_title': 'A1.1.4: The effectiveness of logical separation controls used to separate customer environments '
                             'is confirmed at least once every six months via penetration testing.',
          'requirement_description': ' The effectiveness of logical separation controls used to separate customer environments '
                                     'is confirmed at least once every six months via penetration testing. \n'
                                     'Applicability Notes\n'
                                     'The testing of adequate separation between customers in a multi-tenant service provider '
                                     'environment is in addition to the penetration tests specified in Requirement 11.4.6.\n'
                                     'This requirement is a best practice until 31 March 2025, after which it will be required '
                                     'and must be fully considered during a PCI DSS assessment.',
          'subchapter': 'A1.1: Multi-tenant service providers protect and segregate all customer environments and data.'},
         {'chapter_title': 'Appendix A1: Additional PCI DSS Requirements for Shared Hosting Providers',
          'conformity_questions': ['Q-CLD-06.2: Does the organization ensure Multi-Tenant Service Providers (MTSP) facilitate '
                                   'security event logging capabilities for its customers that are consistent with applicable '
                                   'statutory, regulatory and/or contractual obligations?.'],
          'objective_title': "A1.2.1: Audit log capability is enabled for each customer's environment that is consistent with "
                             'PCI DSS Requirement 10.',
          'requirement_description': '\n'
                                     'Audit log capability is enabled for each customer’s environment that is consistent with '
                                     'PCI DSS Requirement 10, including: \n'
                                     '• Logs are enabled for common third-party applications. \n'
                                     '• Logs are active by default. \n'
                                     '• Logs are available for review only by the owning customer. \n'
                                     '• Log locations are clearly communicated to the owning customer. \n'
                                     '• Log data and availability is consistent with PCI DSS Requirement 10',
          'subchapter': 'A1.2: Multi-tenant service providers facilitate logging and incident response for all customers.'},
         {'chapter_title': 'Appendix A1: Additional PCI DSS Requirements for Shared Hosting Providers',
          'conformity_questions': ['Q-CLD-06.3: Does the organization ensure Multi-Tenant Service Providers (MTSP) facilitate '
                                   'prompt forensic investigations in the event of a suspected or confirmed security '
                                   'incident?.'],
          'objective_title': 'A1.2.2: Processes or mechanisms are implemented to support and/or facilitate prompt forensic '
                             'investigations in the event of a suspected or confirmed security incident for any customer.',
          'requirement_description': ' Processes or mechanisms are implemented to support and/or facilitate prompt forensic '
                                     'investigations in the event of a suspected or confirmed security incident for any '
                                     'customer.',
          'subchapter': 'A1.2: Multi-tenant service providers facilitate logging and incident response for all customers.'},
         {'chapter_title': 'Appendix A1: Additional PCI DSS Requirements for Shared Hosting Providers',
          'conformity_questions': ['Q-TDA-15: Does the organization require system developers and integrators to create a '
                                   'Security Test and Evaluation (ST&E) plan and implement the plan under the witness of an '
                                   'independent party? .',
                                   'Q-IAO-04: Does the organization require system developers and integrators to create and '
                                   'execute a Security Test and Evaluation (ST&E) plan to identify and remediate flaws during '
                                   'development?.',
                                   'Q-IRO-10: Does the organization report incidents:  -  Internally to organizational '
                                   'incident response personnel within organization-defined time-periods; and  -  Externally '
                                   'to regulatory authorities and affected parties, as necessary?.',
                                   'Q-CLD-06.4: Does the organization ensure Multi-Tenant Service Providers (MTSP) facilitate '
                                   'prompt response to suspected or confirmed security incidents and vulnerabilities, '
                                   'including timely notification to affected customers?.'],
          'objective_title': 'A1.2.3: Processes or mechanisms are implemented for reporting and addressing suspected or '
                             'confirmed security incidents and vulnerabilities.',
          'requirement_description': '\n'
                                     'Processes or mechanisms are implemented for reporting and addressing suspected or '
                                     'confirmed security incidents and vulnerabilities, including: \n'
                                     '• Customers can securely report security incidents and vulnerabilities to the '
                                     'provider. \n'
                                     '• The provider addresses and remediates suspected or confirmed security incidents and '
                                     'vulnerabilities according to Requirement 6.3.1. \n'
                                     ' \n'
                                     'Applicability Notes\n'
                                     ' This requirement is a best practice until 31 March 2025, after which it will be '
                                     'required and must be fully considered during a PCI DSS assessment.',
          'subchapter': 'A1.2: Multi-tenant service providers facilitate logging and incident response for all customers.'},
         {'chapter_title': 'Appendix A2: Additional PCI DSS Requirements for Entities using SSL/Early TLS for Card-Present POS '
                           'POI Terminal Connections',
          'conformity_questions': ['Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .'],
          'objective_title': 'A2.1.1: Where POS POI terminals at the merchant or payment acceptance location use SSL and/or '
                             'early TLS, the entity confirms the devices are not susceptible to any known exploits for those '
                             'protocols.',
          'requirement_description': ' Where POS POI terminals at the merchant or payment acceptance location use SSL and/or '
                                     'early TLS, the entity confirms the devices are not susceptible to any known exploits for '
                                     'those protocols.\n'
                                     'Applicability Notes\n'
                                     'This requirement is intended to apply to the entity with the POS POI terminal, such as a '
                                     'merchant. This requirement is not intended for service providers who serve as the '
                                     'termination or connection point to those POS POI terminals. Requirements A2.1.2 and '
                                     'A2.1.3 apply to POS POI service providers.\n'
                                     'The allowance for POS POI terminals that are not currently susceptible to exploits is '
                                     'based on currently known risks. If new exploits are introduced to which POS POI '
                                     'terminals are susceptible, the POS POI terminals will need to be updated immediately.',
          'subchapter': 'A2.1: :Additional PCI DSS Requirements for Entities using SSL/Early TLS for Card-Present POS POI '
                        'Terminal Connect'},
         {'chapter_title': 'Appendix A2: Additional PCI DSS Requirements for Entities using SSL/Early TLS for Card-Present POS '
                           'POI Terminal Connections',
          'conformity_questions': ['Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .'],
          'objective_title': 'A2.1.2: Additional requirement for service providers only: All service providers with existing '
                             'connection points to POS POI terminals that use SSL and/or early TLS as defined in A2.1 have a '
                             'formal Risk Mitigation and Migration Plan in place.',
          'requirement_description': ' Additional requirement for service providers only: All service providers with existing '
                                     'connection points to POS POI terminals that use SSL and/or early TLS as defined in A2.1 '
                                     'have a formal Risk Mitigation and Migration Plan in place that includes:\n'
                                     '•\t Description of usage, including what data is being transmitted, types and number of '
                                     'systems that use and/or support SSL/early TLS, and type of environment. \n'
                                     '•\t Risk-assessment results and risk-reduction controls in place.\n'
                                     '•\t Description of processes to monitor for new vulnerabilities associated with '
                                     'SSL/early TLS.\n'
                                     '•\t Description of change control processes that are implemented to ensure SSL/early TLS '
                                     'is not implemented into new environments.\n'
                                     '•\t Overview of migration project plan to replace SSL/early TLS at a future date.\n'
                                     'Applicability Notes\n'
                                     'This requirement applies only when the entity being assessed is a service provider.',
          'subchapter': 'A2.1: :Additional PCI DSS Requirements for Entities using SSL/Early TLS for Card-Present POS POI '
                        'Terminal Connect'},
         {'chapter_title': 'Appendix A2: Additional PCI DSS Requirements for Entities using SSL/Early TLS for Card-Present POS '
                           'POI Terminal Connections',
          'conformity_questions': ['Q-TPM-01: Does the organization facilitate the implementation of third-party management '
                                   'controls?.'],
          'objective_title': 'A2.1.3: Additional requirement for service providers only: All service providers provide a '
                             'secure service offering.',
          'requirement_description': ' Additional requirement for service providers only: All service providers provide a '
                                     'secure service offering.\n'
                                     'Applicability Notes\n'
                                     'This requirement applies only when the entity being assessed is a service provider.',
          'subchapter': 'A2.1: :Additional PCI DSS Requirements for Entities using SSL/Early TLS for Card-Present POS POI '
                        'Terminal Connect'}]
