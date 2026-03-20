# app/seeds/hipaa_privacy_rule_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class HipaaPrivacyRuleSeed(BaseSeed):
    """Seed HIPAA Privacy Rule framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating HIPAA Privacy Rule framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create HIPAA Privacy Rule Framework
        hipaa_privacy_rule_framework, created = self.get_or_create(
            models.Framework,
            {"name": "HIPAA Privacy Rule", "organisation_id": default_org.id},
            {
                "name": "HIPAA Privacy Rule",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("HIPAA Privacy Rule framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == hipaa_privacy_rule_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == hipaa_privacy_rule_framework.id
            ).all()

            logger.info(f"Found existing HIPAA Privacy Rule framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            return {
                "framework": hipaa_privacy_rule_framework,
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
                description="HIPAA Privacy Rule conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=hipaa_privacy_rule_framework.id,
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
                        "framework_id": hipaa_privacy_rule_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": hipaa_privacy_rule_framework.id
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

        self.db.commit()

        logger.info(f"Created HIPAA Privacy Rule framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": hipaa_privacy_rule_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return ['Q-HRS-06.1: Does the organization require Non-Disclosure Agreements (NDAs) or similar confidentiality agreements '
         'that reflect the needs to protect data and operational details, for both employees and third-parties?.',
         'Q-DCH-05.6: Does the organization require personnel to associate and maintain the association of cybersecurity and '
         'privacy attributes with individuals and objects in accordance with cybersecurity and privacy policies?.',
         'Q-DCH-10.1: Does the organization restrict the use and distribution of sensitive/regulated data? .',
         'Q-HRS-05.2: Does the organization have rules of behavior that contain explicit restrictions on the use of social '
         'media and networking sites, posting information on commercial websites and sharing account information? .',
         'Q-IAC-20.7: Does the organization define and document the types of accounts allowed and prohibited on systems, '
         'applications and services?.',
         'Q-CFG-08: Does the organization configure systems, applications and processes to restrict access to '
         'sensitive/regulated data?.',
         'Q-DCH-01.4: Does the organization explicitly define authorizations for specific individuals and/or roles for logical '
         'and /or physical access to sensitive/regulated data?.',
         'Q-MON-03.1: Does the organization protect sensitive/regulated data contained in log files? .',
         'Q-AST-09: Does the organization securely dispose of, destroy or repurpose system components using '
         'organization-defined techniques and methods to prevent such components from entering the gray market?.',
         'Q-MON-09.1: Does the organization bind the identity of the information producer to the information generated?.',
         'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized disclosure and/or '
         'modification of backup information/.',
         'Q-CRY-01.3: Does the organization ensure the confidentiality and integrity of information during preparation for '
         'transmission and during reception with cryptographic mechanisms?.',
         'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the confidentiality of data being '
         'transmitted? .',
         'Q-END-02: Does the organization protect the confidentiality, integrity, availability and safety of endpoint '
         'devices?.',
         'Q-DCH-04: Does the organization mark media in accordance with data protection requirements so that personnel are '
         'alerted to distribution limitations, handling caveats and applicable security requirements? .',
         'Q-HRS-06.2: Does the organization notify terminated individuals of applicable, legally-binding post-employment '
         'requirements for the protection of sensitive organizational information?.',
         'Q-HRS-09.3: Does the organization govern former employee behavior by notifying terminated individuals of applicable, '
         'legally binding post-employment requirements for the protection of organizational information?.',
         'Q-IRO-10.3: Does the organization report system vulnerabilities associated with reported cybersecurity and privacy '
         'incidents to organization-defined personnel or roles?.',
         'Q-VPM-06.8: Does the organization define what information is allowed to be discoverable by adversaries and take '
         'corrective actions to remediated non-compliant systems?.',
         'Q-CFG-04.1: Does the organization establish parameters for the secure use of open source software? .',
         'Q-CFG-02.7: Does the organization document, assess risk and approve or deny deviations to standardized '
         'configurations..',
         'Q-AAT-01.1: Does the organization identify, understand, document and manage applicable statutory and regulatory '
         'requirements for Artificial Intelligence (AI) and Autonomous Technologies (AAT).',
         'Q-GOV-15.4: Does the organization compel data and/or process owners to obtain authorization for the production use '
         'of each system, application and/or service under their control?.',
         'Q-AST-02.4: Does the organization document and govern instances of approved deviations from established baseline '
         'configurations?.',
         'Q-CFG-05: Does the organization restrict the ability of non-privileged users to install unauthorized software?.',
         'Q-CHG-04.5: Does the organization restrict software library privileges to those individuals with a pertinent '
         'business need for access? .',
         'Q-BCD-11.8: Does the organization implement and enforce dual authorization for the deletion or destruction of '
         'sensitive backup media and data?.',
         'Q-CFG-04: Does the organization enforce software usage restrictions to comply with applicable contract agreements '
         'and copyright laws?.',
         'Q-AST-05.1: Does the organization obtain management approval for any sensitive / regulated media that is transferred '
         "outside of the organization's facilities?.",
         'Q-AST-12: Does the organization restrict the possession and usage of personally-owned technology devices within '
         'organization-controlled facilities?.',
         'Q-END-14.6: Does the organization configure collaborative computing devices to provide physically-present '
         'individuals with an explicit indication of use?.',
         'Q-PRI-14.1: Does the organization develop and maintain an accounting of disclosures of Personal Data (PD) held by '
         'the organization and make the accounting of disclosures available to the person named in the record, upon request?.',
         'Q-PRI-04.4: Does the organization promptly inform data subjects of the utilization purpose when their Personal Data '
         '(PD) is acquired and not received directly from the data subject, except where that utilization purpose was '
         'disclosed in advance to the data subject?.',
         'Q-DCH-10.2: Does the organization prohibit the use of portable storage devices in organizational information systems '
         'when such devices have no identifiable owner?.',
         'Q-IRO-12.2: Does the organization ensure incident response training material provides coverage for sensitive '
         'information spillage response?.',
         'Q-MON-02.5: Does the organization specify the permitted actions for both users and systems associated with the '
         'review, analysis and reporting of audit information? .',
         'Q-DCH-12: Does the organization restrict removable media in accordance with data handling and acceptable usage '
         'parameters?.',
         'Q-CFG-03.3: Does the organization whitelist or blacklist applications in an order to limit what is authorized to '
         'execute on systems?.',
         'Q-DCH-03.1: Does the organization limit the disclosure of data to authorized parties? .',
         'Q-PRI-07.4: Does the organization reject unauthorized disclosure requests?.',
         'Q-NET-03.3: Does the organization prevent the public disclosure of internal address information? .',
         'Q-PRI-17: Does the organization craft disclosures and communications to data subjects such that the material is '
         'readily accessible and written in a manner that is concise, unambiguous and understandable by a reasonable person?.',
         'Q-GOV-02.1: Does the organization prohibit exceptions to standards, except when the exception has been formally '
         'assessed for risk impact, approved and recorded?.',
         'Q-GOV-06: Does the organization identify and document appropriate contacts within relevant law enforcement and '
         'regulatory bodies?.',
         'Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, regulatory and contractual '
         'controls?.',
         'Q-GOV-17: Does the organization submit status reporting of its cybersecurity and/or data privacy program to '
         'applicable statutory and/or regulatory authorities, as required?.',
         'Q-CRY-01.1: Does the organization use cryptographic mechanisms to prevent unauthorized disclosure of information as '
         'an alternate to physical safeguards? .',
         'Q-AST-02.10: Does the organization track the geographic location of system components?.',
         'Q-PRI-14.2: Does the organization notify data subjects of applicable legal requests to disclose Personal Data (PD)?.',
         'Q-HRS-15: Does the organization empower personnel to efficiently report suspicious activities and/or behavior '
         'without fear of reprisal or other negative consequences?.',
         'Q-IRO-02.5: Does the organization coordinate with approved third-parties to achieve a cross-organization perspective '
         'on incident awareness and more effective incident responses? .',
         'Q-IRO-10.2: Does the organization report sensitive/regulated data incidents in a timely manner?.',
         'Q-THR-06.1: Does the organization enable public submissions of discovered or potential security vulnerabilities?.',
         'Q-CPL-06: Does the organization constrain the host government from having unrestricted and non-monitored access to '
         "the organization's systems, applications and services that could potentially violate other applicable statutory, "
         'regulatory and/or contractual obligations..',
         'Q-MON-03.5: Does the organization limit Personal Data (PD) contained in audit records to the elements identified in '
         'the privacy risk assessment?.',
         'Q-CLD-10: Does the organization limit and manage the storage of sensitive/regulated data in public cloud providers? '
         '.',
         'Q-SAT-03.9: Does the organization provide specialized counterintelligence awareness training that enables personnel '
         'to collect, interpret and act upon a range of data sources that may signal the presence of a hostile actor?.',
         'Q-DCH-21: Does the organization securely dispose of, destroy or erase information?.',
         'Q-DCH-09.3: Does the organization facilitate the sanitization of Personal Data (PD)?.',
         'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent unauthorized disclosure of data '
         'at rest? .',
         'Q-MDM-08: Does the organization limit data retention on mobile devices to the smallest usable dataset and '
         'timeframe?.',
         'Q-AST-15: Does the organization verify logical configuration settings and the physical integrity of critical '
         'technology assets throughout their lifecycle?.',
         'Q-BCD-13.1: Does the organization verify the integrity of backups and other restoration assets prior to using them '
         'for restoration?.',
         'Q-AST-18: Does the organization provision and protect the confidentiality, integrity and authenticity of product '
         'supplier keys and data that can be used as a roots of trust basis for integrity verification?.',
         'Q-AST-19: Does the organization establish usage restrictions and implementation guidance for telecommunication '
         'equipment based on the potential to cause damage, if used maliciously?.',
         'Q-CRY-01.4: Does the organization conceal or randomize communication patterns with cryptographic mechanisms?.',
         'Q-PES-02.1: Does the organization authorize physical access to facilities based on the position or role of the '
         'individual?.',
         'Q-PES-04.1: Does the organization allow only authorized personnel access to secure areas? .',
         'Q-PES-03.1: Does the organization limit and monitor physical access through controlled ingress and egress points?.',
         'Q-SEA-02.1: Does the organization standardize technology and process terminology to reduce confusion amongst groups '
         'and departments? .',
         'Q-TPM-06: Does the organization control personnel security requirements including security roles and '
         'responsibilities for third-party providers?.',
         'Q-IAC-09: Does the organization govern naming standards for usernames and systems?.',
         'Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections controls using known '
         'public standards and trusted cryptographic technologies?.',
         'Q-CFG-02: Does the organization develop, document and maintain secure baseline configurations for technology '
         'platform that are consistent with industry-accepted system hardening standards? .',
         'Q-DCH-13.3: Does the organization ensure that the requirements for the protection of sensitive information '
         'processed, stored or transmitted on external systems, are implemented in accordance with applicable statutory, '
         'regulatory and contractual obligations?.',
         'Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to reduce risk and exposure to '
         'threats?.',
         'Q-NET-04.7: Does the organization enforce information flow control using security policy filters as a basis for flow '
         'control decisions?.',
         'Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar mechanisms, to identify '
         'and document day-to-day procedures to enable the proper execution of assigned tasks?.',
         'Q-WEB-01: Does the organization facilitate the implementation of an enterprise-wide web management policy, as well '
         'as associated standards, controls and procedures?.',
         'Q-CHG-02: Does the organization govern the technical configuration change control processes?.',
         'Q-CHG-04.4: Does the organization limit operational privileges for implementing changes?.',
         'Q-CLD-08: Does the organization ensure interoperability by requiring cloud providers to use industry-recognized '
         'formats and provide documentation of custom changes for review?.',
         'Q-DCH-24: Does the organization identify and document the location of information and the specific system components '
         'on which the information resides?.',
         'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, prior to the implementation '
         'of the change?.',
         'Q-MON-14.1: Does the organization share event logs with third-party organizations based on specific '
         'cross-organizational sharing agreements?.',
         'Q-IAC-03.4: Does the organization disassociate user attributes or credential assertion relationships among '
         'individuals, credential service providers and relying parties?.',
         'Q-HRS-06: Does the organization require internal and third-party users to sign appropriate access agreements prior '
         'to being granted access? .']

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(a)(1): Covered entities: Permitted uses and disclosures. A covered entity is permitted '
                             'to use or disclose protected health information as follows',
          'requirement_description': '(i) To the individual;\n'
                                     '\n'
                                     '(ii) For treatment, payment, or health care operations, as permitted by and in '
                                     'compliance with  164.506;\n'
                                     '\n'
                                     '(iii) Incident to a use or disclosure otherwise permitted or required by this subpart, '
                                     'provided that the covered entity has complied with the applicable requirements of  '
                                     '164.502(b), 164.514(d), and 164.530(c) with respect to such otherwise permitted or '
                                     'required use or disclosure;\n'
                                     '\n'
                                     '(iv) Except for uses and disclosures prohibited under  164.502(a)(5)(i), pursuant to and '
                                     'in compliance with a valid authorization under  164.508;\n'
                                     '\n'
                                     '(v) Pursuant to an agreement under, or as otherwise permitted by,  164.510; and\n'
                                     '\n'
                                     '(vi) As permitted by and in compliance with this section,  164.512,  164.514(e), (f), or '
                                     '(g).',
          'subchapter': '164.502(a): Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-HRS-06.1: Does the organization require Non-Disclosure Agreements (NDAs) or similar '
                                   'confidentiality agreements that reflect the needs to protect data and operational details, '
                                   'for both employees and third-parties?.'],
          'objective_title': '164.502(a)(2): Covered entities: Required disclosures. A covered entity is required to disclose '
                             'protected health information',
          'requirement_description': '(i) To an individual, when requested under, and required by  164.524 or  164.528; and\n'
                                     '\n'
                                     '(ii) When required by the Secretary under subpart C of part 160 of this subchapter to '
                                     "investigate or determine the covered entity's compliance with this subchapter.",
          'subchapter': "164.502(a): Standard: Disclosures for workers' compensation."},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(a)(3): Business associates: Permitted uses and disclosures.  A business associate may '
                             'use or disclose protected health information only as permitted or required by its business '
                             'associate contract or other arrangement pursuant to  164.504(e) or as required by law. The '
                             'business associate may not use or disclose protected health information in a manner that would '
                             'violate the requirements of this subpart, if done by the covered entity, except for the purposes '
                             'specified under  164.504(e)(2)(i)(A) or (B) if such uses or disclosures are permitted by its '
                             'contract or other arrangement. ',
          'requirement_description': None,
          'subchapter': '164.502(a): Standard: De-identification of protected health information.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-DCH-05.6: Does the organization require personnel to associate and maintain the '
                                   'association of cybersecurity and privacy attributes with individuals and objects in '
                                   'accordance with cybersecurity and privacy policies?.',
                                   'Q-HRS-06.1: Does the organization require Non-Disclosure Agreements (NDAs) or similar '
                                   'confidentiality agreements that reflect the needs to protect data and operational details, '
                                   'for both employees and third-parties?.'],
          'objective_title': '164.502(a)(4): Business associates: Required uses and disclosures. A business associate is '
                             'required to disclose protected health information',
          'requirement_description': '(i) When required by the Secretary under subpart C of part 160 of this subchapter to '
                                     "investigate or determine the business associate's compliance with this subchapter.\n"
                                     '\n'
                                     "(ii) To the covered entity, individual, or individual's designee, as necessary to "
                                     "satisfy a covered entity's obligations under  164.524(c)(2)(ii) and (3)(ii) with respect "
                                     "to an individual's request for an electronic copy of protected health information.",
          'subchapter': '164.502(a): Standard: minimum necessary requirements.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-DCH-10.1: Does the organization restrict the use and distribution of sensitive/regulated '
                                   'data? .',
                                   'Q-HRS-05.2: Does the organization have rules of behavior that contain explicit '
                                   'restrictions on the use of social media and networking sites, posting information on '
                                   'commercial websites and sharing account information? .',
                                   'Q-IAC-20.7: Does the organization define and document the types of accounts allowed and '
                                   'prohibited on systems, applications and services?.'],
          'objective_title': '164.502(a)(5): Prohibited uses and disclosures',
          'requirement_description': '\n'
                                     '\n'
                                     '(i) Use and disclosure of genetic information for underwriting purposes:  '
                                     'Notwithstanding any other provision of this subpart, a health plan, excluding an issuer '
                                     'of a long-term care policy falling within paragraph (1)(viii) of the definition of '
                                     'health plan, shall not use or disclose protected health information that is genetic '
                                     'information for underwriting purposes. For purposes of paragraph (a)(5)(i) of this '
                                     'section, underwriting purposes means, with respect to a health plan:\n'
                                     '\n'
                                     '(A) Except as provided in paragraph (a)(5)(i)(B) of this section:\n'
                                     '\n'
                                     '(1) Rules for, or determination of, eligibility (including enrollment and continued '
                                     'eligibility) for, or determination of, benefits under the plan, coverage, or policy '
                                     '(including changes in deductibles or other cost-sharing mechanisms in return for '
                                     'activities such as completing a health risk assessment or participating in a wellness '
                                     'program);\n'
                                     '\n'
                                     '(2) The computation of premium or contribution amounts under the plan, coverage, or '
                                     'policy (including discounts, rebates, payments in kind, or other premium differential '
                                     'mechanisms in return for activities such as completing a health risk assessment or '
                                     'participating in a wellness program);\n'
                                     '\n'
                                     '(3) The application of any pre-existing condition exclusion under the plan, coverage, or '
                                     'policy; and\n'
                                     '\n'
                                     '(4) Other activities related to the creation, renewal, or replacement of a contract of '
                                     'health insurance or health benefits.\n'
                                     '\n'
                                     '(B) Underwriting purposes does not include determinations of medical appropriateness '
                                     'where an individual seeks a benefit under the plan, coverage, or policy.\n'
                                     '\n'
                                     '(ii) Sale of protected health information:\n'
                                     '\n'
                                     '(A) Except pursuant to and in compliance with  164.508(a)(4), a covered entity or '
                                     'business associate may not sell protected health information.\n'
                                     '\n'
                                     '(B) For purposes of this paragraph, sale of protected health information means:\n'
                                     '\n'
                                     '(1) Except as provided in paragraph (a)(5)(ii)(B)(2) of this section, a disclosure of '
                                     'protected health information by a covered entity or business associate, if applicable, '
                                     'where the covered entity or business associate directly or indirectly receives '
                                     'remuneration from or on behalf of the recipient of the protected health information in '
                                     'exchange for the protected health information.\n'
                                     '\n'
                                     '(2) Sale of protected health information does not include a disclosure of protected '
                                     'health information:\n'
                                     '\n'
                                     '(i) For public health purposes pursuant to  164.512(b) or  164.514(e);\n'
                                     '\n'
                                     '(ii) For research purposes pursuant to  164.512(i) or  164.514(e), where the only '
                                     'remuneration received by the covered entity or business associate is a reasonable '
                                     'cost-based fee to cover the cost to prepare and transmit the protected health '
                                     'information for such purposes;\n'
                                     '\n'
                                     '(iii) For treatment and payment purposes pursuant to  164.506(a);\n'
                                     '\n'
                                     '(iv) For the sale, transfer, merger, or consolidation of all or part of the covered '
                                     'entity and for related due diligence as described in paragraph (6)(iv) of the definition '
                                     'of health care operations and pursuant to  164.506(a);\n'
                                     '\n'
                                     '(v) To or by a business associate for activities that the business associate undertakes '
                                     'on behalf of a covered entity, or on behalf of a business associate in the case of a '
                                     'subcontractor, pursuant to  164.502(e) and 164.504(e), and the only remuneration '
                                     'provided is by the covered entity to the business associate, or by the business '
                                     'associate to the subcontractor, if applicable, for the performance of such activities;\n'
                                     '\n'
                                     '(vi) To an individual, when requested under  164.524 or  164.528;\n'
                                     '\n'
                                     '(vii) Required by law as permitted under  164.512(a); and\n'
                                     '\n'
                                     '(viii) For any other purpose permitted by and in accordance with the applicable '
                                     'requirements of this subpart, where the only remuneration received by the covered entity '
                                     'or business associate is a reasonable, cost-based fee to cover the cost to prepare and '
                                     'transmit the protected health information for such purpose or a fee otherwise expressly '
                                     'permitted by other law.',
          'subchapter': '164.502(a): Standard: Limited data set.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(b)(1): Standard: Minimum necessary ',
          'requirement_description': 'Minimum necessary applies. When using or disclosing protected health information or when '
                                     'requesting protected health information from another covered entity or business '
                                     'associate, a covered entity or business associate must make reasonable efforts to limit '
                                     'protected health information to the minimum necessary to accomplish the intended purpose '
                                     'of the use, disclosure, or request.\n'
                                     '\n'
                                     '(2) Minimum necessary does not apply.  This requirement does not apply to:\n'
                                     '\n'
                                     '(i) Disclosures to or requests by a health care provider for treatment;\n'
                                     '\n'
                                     '(ii) Uses or disclosures made to the individual, as permitted under paragraph (a)(1)(i) '
                                     'of this section or as required by paragraph (a)(2)(i) of this section;\n'
                                     '\n'
                                     '(iii) Uses or disclosures made pursuant to an authorization under  164.508;\n'
                                     '\n'
                                     '(iv) Disclosures made to the Secretary in accordance with subpart C of part 160 of this '
                                     'subchapter;\n'
                                     '\n'
                                     '(v) Uses or disclosures that are required by law, as described by  164.512(a); and\n'
                                     '\n'
                                     '(vi) Uses or disclosures that are required for compliance with applicable requirements '
                                     'of this subchapter.',
          'subchapter': '164.502(b): Fundraising communications'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-CFG-08: Does the organization configure systems, applications and processes to restrict '
                                   'access to sensitive/regulated data?.',
                                   'Q-DCH-01.4: Does the organization explicitly define authorizations for specific '
                                   'individuals and/or roles for logical and /or physical access to sensitive/regulated data?.',
                                   'Q-MON-03.1: Does the organization protect sensitive/regulated data contained in log files? '
                                   '.'],
          'objective_title': '164.502(c)(1): Uses and disclosures of protected health information subject to an agreed upon '
                             'restriction.',
          'requirement_description': 'A covered entity that has agreed to a restriction pursuant to  164.522(a)(1) may not use '
                                     'or disclose the protected health information covered by the restriction in violation of '
                                     'such restriction, except as otherwise provided in  164.522(a).',
          'subchapter': '164.502(c): Standard: Uses and disclosures for underwriting and related purposes.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-AST-09: Does the organization securely dispose of, destroy or repurpose system '
                                   'components using organization-defined techniques and methods to prevent such components '
                                   'from entering the gray market?.',
                                   'Q-MON-09.1: Does the organization bind the identity of the information producer to the '
                                   'information generated?.',
                                   'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized '
                                   'disclosure and/or modification of backup information/.'],
          'objective_title': '164.502(d)(1): Uses and disclosures to create de-identified information.',
          'requirement_description': ' A covered entity may use protected health information to create information that is not '
                                     'individually identifiable health information or disclose protected health information '
                                     'only to a business associate for such purpose, whether or not the de-identified '
                                     'information is to be used by the covered entity.',
          'subchapter': '164.502(d): Standard: Verification requirements.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-AST-09: Does the organization securely dispose of, destroy or repurpose system '
                                   'components using organization-defined techniques and methods to prevent such components '
                                   'from entering the gray market?.',
                                   'Q-MON-09.1: Does the organization bind the identity of the information producer to the '
                                   'information generated?.',
                                   'Q-BCD-11.4: Does the organization use cryptographic mechanisms to prevent the unauthorized '
                                   'disclosure and/or modification of backup information/.'],
          'objective_title': '164.502(d)(2): Uses and disclosures of de-identified information.',
          'requirement_description': 'Health information that meets the standard and implementation specifications for '
                                     'de-identification under  164.514(a) and (b) is considered not to be individually '
                                     'identifiable health information, i.e., de-identified. The requirements of this subpart '
                                     'do not apply to information that has been de-identified in accordance with the '
                                     'applicable requirements of  164.514, provided that:\n'
                                     '(i) Disclosure of a code or other means of record identification designed to enable '
                                     'coded or otherwise de-identified information to be re-identified constitutes disclosure '
                                     'of protected health information; and \n'
                                     '(ii) If de-identified information is re-identified, a covered entity may use or disclose '
                                     'such re-identified information only as permitted or required by this subpart.',
          'subchapter': '164.502(d): Standard: Notice of privacy practices'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(e)(1): Standard: Disclosures to business associates.',
          'requirement_description': '(i) A covered entity may disclose protected health information to a business associate '
                                     'and may allow a business associate to create, receive, maintain, or transmit protected '
                                     'health information on its behalf, if the covered entity obtains satisfactory assurance '
                                     'that the business associate will appropriately safeguard the information. A covered '
                                     'entity is not required to obtain such satisfactory assurances from a business associate '
                                     'that is a subcontractor.\n'
                                     '\n'
                                     '(ii) A business associate may disclose protected health information to a business '
                                     'associate that is a subcontractor and may allow the subcontractor to create, receive, '
                                     'maintain, or transmit protected health information on its behalf, if the business '
                                     'associate obtains satisfactory assurances, in accordance with  164.504(e)(1)(i), that '
                                     'the subcontractor will appropriately safeguard the information.\n'
                                     '\n'
                                     'Implementation specification: Documentation.  The satisfactory assurances required by '
                                     'paragraph (e)(1) of this section must be documented through a written contract or other '
                                     'written agreement or arrangement with the business associate that meets the applicable '
                                     'requirements of  164.504(e).',
          'subchapter': '164.502(e): Standard: Right of an individual to request restriction of uses and disclosures.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(f)(1): Standard: Deceased individuals.',
          'requirement_description': 'A covered entity must comply with the requirements of this subpart with respect to the '
                                     'protected health information of a deceased individual for a period of 50 years following '
                                     'the death of the individual.',
          'subchapter': '164.502(f): Standard: Confidential communications requirements.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(g)(1): Standard: Personal representatives.',
          'requirement_description': 'As specified in this paragraph, a covered entity must, except as provided in paragraphs '
                                     '(g)(3) and (g)(5) of this section, treat a personal representative as the individual for '
                                     'purposes of this subchapter.\n'
                                     '(2) Implementation specification: Adults and emancipated minors.  If under applicable '
                                     'law a person has authority to act on behalf of an individual who is an adult or an '
                                     'emancipated minor in making decisions related to health care, a covered entity must '
                                     'treat such person as a personal representative under this subchapter, with respect to '
                                     'protected health information relevant to such personal representation.\n'
                                     '\n'
                                     '(3)\n'
                                     '\n'
                                     '(i) Implementation specification: Unemancipated minors.  If under applicable law a '
                                     'parent, guardian, or other person acting in loco parentis has authority to act on behalf '
                                     'of an individual who is an unemancipated minor in making decisions related to health '
                                     'care, a covered entity must treat such person as a personal representative under this '
                                     'subchapter, with respect to protected health information relevant to such personal '
                                     'representation, except that such person may not be a personal representative of an '
                                     'unemancipated minor, and the minor has the authority to act as an individual, with '
                                     'respect to protected health information pertaining to a health care service, if:\n'
                                     '\n'
                                     '(A) The minor consents to such health care service; no other consent to such health care '
                                     'service is required by law, regardless of whether the consent of another person has also '
                                     'been obtained; and the minor has not requested that such person be treated as the '
                                     'personal representative;\n'
                                     '\n'
                                     '(B) The minor may lawfully obtain such health care service without the consent of a '
                                     'parent, guardian, or other person acting in loco parentis, and the minor, a court, or '
                                     'another person authorized by law consents to such health care service; or\n'
                                     '\n'
                                     '(C) A parent, guardian, or other person acting in loco parentis assents to an agreement '
                                     'of confidentiality between a covered health care provider and the minor with respect to '
                                     'such health care service.\n'
                                     '\n'
                                     '(ii) Notwithstanding the provisions of paragraph (g)(3)(i) of this section:\n'
                                     '\n'
                                     '(A) If, and to the extent, permitted or required by an applicable provision of State or '
                                     'other law, including applicable case law, a covered entity may disclose, or provide '
                                     'access in accordance with  164.524 to, protected health information about an '
                                     'unemancipated minor to a parent, guardian, or other person acting in loco parentis;\n'
                                     '\n'
                                     '(B) If, and to the extent, prohibited by an applicable provision of State or other law, '
                                     'including applicable case law, a covered entity may not disclose, or provide access in '
                                     'accordance with  164.524 to, protected health information about an unemancipated minor '
                                     'to a parent, guardian, or other person acting in loco parentis; and\n'
                                     '\n'
                                     '(C) Where the parent, guardian, or other person acting in loco parentis, is not the '
                                     'personal representative under paragraphs (g)(3)(i)(A), (B), or (C) of this section and '
                                     'where there is no applicable access provision under State or other law, including case '
                                     'law, a covered entity may provide or deny access under  164.524 to a parent, guardian, '
                                     'or other person acting in loco parentis, if such action is consistent with State or '
                                     'other applicable law, provided that such decision must be made by a licensed health care '
                                     'professional, in the exercise of professional judgment.\n'
                                     '\n'
                                     '(4) Implementation specification: Deceased individuals.  If under applicable law an '
                                     'executor, administrator, or other person has authority to act on behalf of a deceased '
                                     "individual or of the individual's estate, a covered entity must treat such person as a "
                                     'personal representative under this subchapter, with respect to protected health '
                                     'information relevant to such personal representation.\n'
                                     '\n'
                                     '(5) Implementation specification: Abuse, neglect, endangerment situations.  '
                                     'Notwithstanding a State law or any requirement of this paragraph to the contrary, a '
                                     'covered entity may elect not to treat a person as the personal representative of an '
                                     'individual if:\n'
                                     '\n'
                                     '(i) The covered entity has a reasonable belief that:\n'
                                     '\n'
                                     '(A) The individual has been or may be subjected to domestic violence, abuse, or neglect '
                                     'by such person; or\n'
                                     '\n'
                                     '(B) Treating such person as the personal representative could endanger the individual; '
                                     'and\n'
                                     '\n'
                                     '(ii) The covered entity, in the exercise of professional judgment, decides that it is '
                                     "not in the best interest of the individual to treat the person as the individual's "
                                     'personal representative.',
          'subchapter': '164.502(g): Standard: Access to protected health information'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-CRY-01.3: Does the organization ensure the confidentiality and integrity of information '
                                   'during preparation for transmission and during reception with cryptographic mechanisms?.',
                                   'Q-CRY-03: Does the organization use cryptographic mechanisms to protect the '
                                   'confidentiality of data being transmitted? .',
                                   'Q-END-02: Does the organization protect the confidentiality, integrity, availability and '
                                   'safety of endpoint devices?.'],
          'objective_title': '164.502(h)(1): Standard: Confidential communications.',
          'requirement_description': 'A covered health care provider or health plan must comply with the applicable '
                                     'requirements of  164.522(b) in communicating protected health information.',
          'subchapter': '164.502(h): Standard: Right to amend.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-DCH-04: Does the organization mark media in accordance with data protection requirements '
                                   'so that personnel are alerted to distribution limitations, handling caveats and applicable '
                                   'security requirements? .'],
          'objective_title': '164.502(i)(1): Standard: Uses and disclosures consistent with notice.',
          'requirement_description': 'A covered entity that is required by  164.520 to have a notice may not use or disclose '
                                     'protected health information in a manner inconsistent with such notice. A covered entity '
                                     'that is required by  164.520(b)(1)(iii) to include a specific statement in its notice if '
                                     'it intends to engage in an activity listed in  164.520(b)(1)(iii)(A)-(C), may not use or '
                                     'disclose protected health information for such activities, unless the required statement '
                                     'is included in the notice.',
          'subchapter': '164.502(i): Standard: Right to an accounting of disclosures of protected health information.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(j)(1): Standard: Disclosures by whistleblowers',
          'requirement_description': 'A covered entity is not considered to have violated the requirements of this subpart if '
                                     'a member of its workforce or a business associate discloses protected health '
                                     'information, provided that:\n'
                                     '\n'
                                     '(i) The workforce member or business associate believes in good faith that the covered '
                                     'entity has engaged in conduct that is unlawful or otherwise violates professional or '
                                     'clinical standards, or that the care, services, or conditions provided by the covered '
                                     'entity potentially endangers one or more patients, workers, or the public; and\n'
                                     '\n'
                                     '(ii) The disclosure is to:\n'
                                     '\n'
                                     '(A) A health oversight agency or public health authority authorized by law to '
                                     'investigate or otherwise oversee the relevant conduct or conditions of the covered '
                                     'entity or to an appropriate health care accreditation organization for the purpose of '
                                     'reporting the allegation of failure to meet professional standards or misconduct by the '
                                     'covered entity; or\n'
                                     '\n'
                                     '(B) An attorney retained by or on behalf of the workforce member or business associate '
                                     'for the purpose of determining the legal options of the workforce member or business '
                                     'associate with regard to the conduct described in paragraph (j)(1)(i) of this section.',
          'subchapter': '164.502(j): Standard: Personnel designations.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': ['Q-HRS-06.2: Does the organization notify terminated individuals of applicable, '
                                   'legally-binding post-employment requirements for the protection of sensitive '
                                   'organizational information?.',
                                   'Q-HRS-09.3: Does the organization govern former employee behavior by notifying terminated '
                                   'individuals of applicable, legally binding post-employment requirements for the protection '
                                   'of organizational information?.',
                                   'Q-IRO-10.3: Does the organization report system vulnerabilities associated with reported '
                                   'cybersecurity and privacy incidents to organization-defined personnel or roles?.'],
          'objective_title': '164.502(j)(2): Disclosures by workforce members who are victims of a crime',
          'requirement_description': 'A covered entity is not considered to have violated the requirements of this subpart if '
                                     'a member of its workforce who is the victim of a criminal act discloses protected health '
                                     'information to a law enforcement official, provided that:\n'
                                     '\n'
                                     '(i) The protected health information disclosed is about the suspected perpetrator of the '
                                     'criminal act; and\n'
                                     '\n'
                                     '(ii) The protected health information disclosed is limited to the information listed in  '
                                     '164.512(f)(2)(i)',
          'subchapter': '164.502(j): Standard: Training.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(e)(1): Standard: Business associate contracts.',
          'requirement_description': '(i) A covered entity may disclose protected health information to a business associate '
                                     'and may allow a business associate to create, receive, maintain, or transmit protected '
                                     'health information on its behalf, if the covered entity obtains satisfactory assurance '
                                     'that the business associate will appropriately safeguard the information. A covered '
                                     'entity is not required to obtain such satisfactory assurances from a business associate '
                                     'that is a subcontractor.\n'
                                     '\n'
                                     '(ii) A business associate may disclose protected health information to a business '
                                     'associate that is a subcontractor and may allow the subcontractor to create, receive, '
                                     'maintain, or transmit protected health information on its behalf, if the business '
                                     'associate obtains satisfactory assurances, in accordance with  164.504(e)(1)(i), that '
                                     'the subcontractor will appropriately safeguard the information.\n'
                                     '\n'
                                     'Implementation specification: Documentation.  The satisfactory assurances required by '
                                     'paragraph (e)(1) of this section must be documented through a written contract or other '
                                     'written agreement or arrangement with the business associate that meets the applicable '
                                     'requirements of  164.504(e).',
          'subchapter': '164.502(e): Standard: Safeguards.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(f)(1): Standard: Requirements for group health plans.',
          'requirement_description': 'A covered entity must comply with the requirements of this subpart with respect to the '
                                     'protected health information of a deceased individual for a period of 50 years following '
                                     'the death of the individual.',
          'subchapter': '164.502(f): Standard: Complaints to the covered entity.'},
         {'chapter_title': '164.502: Uses and disclosures of protected health information: General rules.',
          'conformity_questions': [],
          'objective_title': '164.502(f)(1): Standard: Requirements for a covered entity with multiple covered functions.',
          'requirement_description': 'A covered entity must comply with the requirements of this subpart with respect to the '
                                     'protected health information of a deceased individual for a period of 50 years following '
                                     'the death of the individual.',
          'subchapter': '164.502(f): Standard: Sanctions.'},
         {'chapter_title': '164.506: Uses and disclosures to carry out treatment, payment, or health care operations.',
          'conformity_questions': ['Q-VPM-06.8: Does the organization define what information is allowed to be discoverable by '
                                   'adversaries and take corrective actions to remediated non-compliant systems?.',
                                   'Q-CFG-04.1: Does the organization establish parameters for the secure use of open source '
                                   'software? .',
                                   'Q-CFG-02.7: Does the organization document, assess risk and approve or deny deviations to '
                                   'standardized configurations..'],
          'objective_title': '164.506(a): Standard: Permitted uses and disclosures',
          'requirement_description': 'Except with respect to uses or disclosures that require an authorization under  '
                                     '164.508(a)(2) through (4) or that are prohibited under  164.502(a)(5)(i), a covered '
                                     'entity may use or disclose protected health information for treatment, payment, or '
                                     'health care operations as set forth in paragraph (c) of this section, provided that such '
                                     'use or disclosure is consistent with other applicable requirements of this subpart.',
          'subchapter': '164.506(a): Standard: Mitigation.'},
         {'chapter_title': '164.506: Uses and disclosures to carry out treatment, payment, or health care operations.',
          'conformity_questions': [],
          'objective_title': '164.506(b): Standard: Consent for uses and disclosures permitted.',
          'requirement_description': '(1) A covered entity may obtain consent of the individual to use or disclose protected '
                                     'health information to carry out treatment, payment, or health care operations.\n'
                                     '\n'
                                     '(2) Consent, under paragraph (b) of this section, shall not be effective to permit a use '
                                     'or disclosure of protected health information when an authorization, under  164.508, is '
                                     'required or when another condition must be met for such use or disclosure to be '
                                     'permissible under this subpart.\n'
                                     '\n'
                                     '(c) Implementation specifications: Treatment, payment, or health care operations.\n'
                                     '\n'
                                     '(1) A covered entity may use or disclose protected health information for its own '
                                     'treatment, payment, or health care operations.\n'
                                     '\n'
                                     '(2) A covered entity may disclose protected health information for treatment activities '
                                     'of a health care provider.\n'
                                     '\n'
                                     '(3) A covered entity may disclose protected health information to another covered entity '
                                     'or a health care provider for the payment activities of the entity that receives the '
                                     'information.\n'
                                     '\n'
                                     '(4) A covered entity may disclose protected health information to another covered entity '
                                     'for health care operations activities of the entity that receives the information, if '
                                     'each entity either has or had a relationship with the individual who is the subject of '
                                     'the protected health information being requested, the protected health information '
                                     'pertains to such relationship, and the disclosure is:\n'
                                     '\n'
                                     '(i) For a purpose listed in paragraph (1) or (2) of the definition of health care '
                                     'operations; or\n'
                                     '\n'
                                     '(ii) For the purpose of health care fraud and abuse detection or compliance.\n'
                                     '\n'
                                     '(5) A covered entity that participates in an organized health care arrangement may '
                                     'disclose protected health information about an individual to other participants in the '
                                     'organized health care arrangement for any health care operations activities of the '
                                     'organized health care arrangement.',
          'subchapter': '164.506(b): Standard: Refraining from intimidating or retaliatory acts.'},
         {'chapter_title': '164.508: Uses and disclosures for which an authorization is required.',
          'conformity_questions': ['Q-AAT-01.1: Does the organization identify, understand, document and manage applicable '
                                   'statutory and regulatory requirements for Artificial Intelligence (AI) and Autonomous '
                                   'Technologies (AAT).',
                                   'Q-GOV-15.4: Does the organization compel data and/or process owners to obtain '
                                   'authorization for the production use of each system, application and/or service under '
                                   'their control?.',
                                   'Q-AST-02.4: Does the organization document and govern instances of approved deviations '
                                   'from established baseline configurations?.'],
          'objective_title': '164.508(a)(1): Authorization required: General rule.',
          'requirement_description': 'Except as otherwise permitted or required by this subchapter, a covered entity may not '
                                     'use or disclose protected health information without an authorization that is valid '
                                     'under this section. When a covered entity obtains or receives a valid authorization for '
                                     'its use or disclosure of protected health information, such use or disclosure must be '
                                     'consistent with such authorization.',
          'subchapter': '164.508(a): Standard: Waiver of rights.'},
         {'chapter_title': '164.508: Uses and disclosures for which an authorization is required.',
          'conformity_questions': [],
          'objective_title': '164.508(a)(2): Authorization required: Psychotherapy notes.',
          'requirement_description': 'Notwithstanding any provision of this subpart, other than the transition provisions in  '
                                     '164.532, a covered entity must obtain an authorization for any use or disclosure of '
                                     'psychotherapy notes, except:\n'
                                     '\n'
                                     '(i) To carry out the following treatment, payment, or health care operations:\n'
                                     '\n'
                                     '(A) Use by the originator of the psychotherapy notes for treatment;\n'
                                     '\n'
                                     '(B) Use or disclosure by the covered entity for its own training programs in which '
                                     'students, trainees, or practitioners in mental health learn under supervision to '
                                     'practice or improve their skills in group, joint, family, or individual counseling; or\n'
                                     '\n'
                                     '(C) Use or disclosure by the covered entity to defend itself in a legal action or other '
                                     'proceeding brought by the individual; and\n'
                                     '\n'
                                     '(ii) A use or disclosure that is required by  164.502(a)(2)(ii) or permitted by  '
                                     '164.512(a);  164.512(d) with respect to the oversight of the originator of the '
                                     'psychotherapy notes;  164.512(g)(1); or  164.512(j)(1)(i).',
          'subchapter': '164.508(a): Standard: Policies and procedures.'},
         {'chapter_title': '164.508: Uses and disclosures for which an authorization is required.',
          'conformity_questions': ['Q-CFG-05: Does the organization restrict the ability of non-privileged users to install '
                                   'unauthorized software?.',
                                   'Q-GOV-15.4: Does the organization compel data and/or process owners to obtain '
                                   'authorization for the production use of each system, application and/or service under '
                                   'their control?.',
                                   'Q-CHG-04.5: Does the organization restrict software library privileges to those '
                                   'individuals with a pertinent business need for access? .'],
          'objective_title': '164.508(a)(3): Authorization required: Marketing.',
          'requirement_description': '(i) Notwithstanding any provision of this subpart, other than the transition provisions '
                                     'in  164.532, a covered entity must obtain an authorization for any use or disclosure of '
                                     'protected health information for marketing, except if the communication is in the form '
                                     'of:\n'
                                     '\n'
                                     '(A) A face-to-face communication made by a covered entity to an individual; or\n'
                                     '\n'
                                     '(B) A promotional gift of nominal value provided by the covered entity.\n'
                                     '\n'
                                     '(ii) If the marketing involves financial remuneration, as defined in paragraph (3) of '
                                     'the definition of marketing at  164.501, to the covered entity from a third party, the '
                                     'authorization must state that such remuneration is involved.',
          'subchapter': '164.508(a): Standard: Policies and procedures.'},
         {'chapter_title': '164.508: Uses and disclosures for which an authorization is required.',
          'conformity_questions': ['Q-GOV-15.4: Does the organization compel data and/or process owners to obtain '
                                   'authorization for the production use of each system, application and/or service under '
                                   'their control?.',
                                   'Q-CHG-04.5: Does the organization restrict software library privileges to those '
                                   'individuals with a pertinent business need for access? .',
                                   'Q-BCD-11.8: Does the organization implement and enforce dual authorization for the '
                                   'deletion or destruction of sensitive backup media and data?.'],
          'objective_title': '164.508(a)(4): Authorization required: Sale of protected health information.',
          'requirement_description': '(i) Notwithstanding any provision of this subpart, other than the transition provisions '
                                     'in  164.532, a covered entity must obtain an authorization for any disclosure of '
                                     'protected health information which is a sale of protected health information, as defined '
                                     'in  164.501 of this subpart.\n'
                                     '\n'
                                     '(ii) Such authorization must state that the disclosure will result in remuneration to '
                                     'the covered entity.',
          'subchapter': '164.508(a): Standard: Documentation.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': ['Q-CFG-04: Does the organization enforce software usage restrictions to comply with '
                                   'applicable contract agreements and copyright laws?.',
                                   'Q-AST-05.1: Does the organization obtain management approval for any sensitive / regulated '
                                   "media that is transferred outside of the organization's facilities?.",
                                   'Q-AST-12: Does the organization restrict the possession and usage of personally-owned '
                                   'technology devices within organization-controlled facilities?.'],
          'objective_title': '164.510(a)(1): Permitted uses and disclosure.',
          'requirement_description': 'Except when an objection is expressed in accordance with paragraphs (a)(2) or (3) of '
                                     'this section, a covered health care provider may:\n'
                                     '\n'
                                     '(i) Use the following protected health information to maintain a directory of '
                                     'individuals in its facility:\n'
                                     '\n'
                                     "(A) The individual's name;\n"
                                     '\n'
                                     "(B) The individual's location in the covered health care provider's facility;\n"
                                     '\n'
                                     "(C) The individual's condition described in general terms that does not communicate "
                                     'specific medical information about the individual; and\n'
                                     '\n'
                                     "(D) The individual's religious affiliation; and\n"
                                     '\n'
                                     '(ii) Use or disclose for directory purposes such information:\n'
                                     '\n'
                                     '(A) To members of the clergy; or\n'
                                     '\n'
                                     '(B) Except for religious affiliation, to other persons who ask for the individual by '
                                     'name.',
          'subchapter': '164.510(a): Standard: Group health plans.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': [],
          'objective_title': '164.510(a)(2): Opportunity to object.',
          'requirement_description': 'A covered health care provider must inform an individual of the protected health '
                                     'information that it may include in a directory and the persons to whom it may disclose '
                                     'such information (including disclosures to clergy of information regarding religious '
                                     'affiliation) and provide the individual with the opportunity to restrict or prohibit '
                                     'some or all of the uses or disclosures permitted by paragraph (a)(1) of this section.',
          'subchapter': '164.510(a): Standard: Effect of prior authorizations.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': [],
          'objective_title': '164.510(a)(3): Emergency circumstances.',
          'requirement_description': '(i) If the opportunity to object to uses or disclosures required by paragraph (a)(2) of '
                                     "this section cannot practicably be provided because of the individual's incapacity or an "
                                     'emergency treatment circumstance, a covered health care provider may use or disclose '
                                     'some or all of the protected health information permitted by paragraph (a)(1) of this '
                                     "section for the facility's directory, if such disclosure is:\n"
                                     '\n'
                                     '(A) Consistent with a prior expressed preference of the individual, if any, that is '
                                     'known to the covered health care provider; and\n'
                                     '\n'
                                     "(B) In the individual's best interest as determined by the covered health care provider, "
                                     'in the exercise of professional judgment.\n'
                                     '\n'
                                     '(ii) The covered health care provider must inform the individual and provide an '
                                     'opportunity to object to uses or disclosures for directory purposes as required by '
                                     'paragraph (a)(2) of this section when it becomes practicable to do so.',
          'subchapter': '164.510(a): Standard: Effect of prior contracts or other arrangements with business associates.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': ['Q-CFG-04: Does the organization enforce software usage restrictions to comply with '
                                   'applicable contract agreements and copyright laws?.',
                                   'Q-AST-05.1: Does the organization obtain management approval for any sensitive / regulated '
                                   "media that is transferred outside of the organization's facilities?.",
                                   'Q-AST-12: Does the organization restrict the possession and usage of personally-owned '
                                   'technology devices within organization-controlled facilities?.'],
          'objective_title': '164.510(b)(1): Permitted uses and disclosures.',
          'requirement_description': '(i) A covered entity may, in accordance with paragraphs (b)(2), (b)(3), or (b)(5) of '
                                     'this section, disclose to a family member, other relative, or a close personal friend of '
                                     'the individual, or any other person identified by the individual, the protected health '
                                     "information directly relevant to such person's involvement with the individual's health "
                                     "care or payment related to the individual's health care.\n"
                                     '\n'
                                     '(ii) A covered entity may use or disclose protected health information to notify, or '
                                     'assist in the notification of (including identifying or locating), a family member, a '
                                     'personal representative of the individual, or another person responsible for the care of '
                                     "the individual of the individual's location, general condition, or death. Any such use "
                                     'or disclosure of protected health information for such notification purposes must be in '
                                     'accordance with paragraphs (b)(2), (b)(3), (b)(4), or (b)(5) of this section, as '
                                     'applicable.',
          'subchapter': '164.510(b): Effect of prior data use agreements.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': ['Q-END-14.6: Does the organization configure collaborative computing devices to provide '
                                   'physically-present individuals with an explicit indication of use?.',
                                   'Q-PRI-14.1: Does the organization develop and maintain an accounting of disclosures of '
                                   'Personal Data (PD) held by the organization and make the accounting of disclosures '
                                   'available to the person named in the record, upon request?.',
                                   'Q-PRI-04.4: Does the organization promptly inform data subjects of the utilization purpose '
                                   'when their Personal Data (PD) is acquired and not received directly from the data subject, '
                                   'except where that utilization purpose was disclosed in advance to the data subject?.'],
          'objective_title': '164.510(b)(2): Uses and disclosures with the individual present.',
          'requirement_description': 'If the individual is present for, or otherwise available prior to, a use or disclosure '
                                     'permitted by paragraph (b)(1) of this section and has the capacity to make health care '
                                     'decisions, the covered entity may use or disclose the protected health information if '
                                     'it:\n'
                                     '\n'
                                     "(i) Obtains the individual's agreement;\n"
                                     '\n'
                                     '(ii) Provides the individual with the opportunity to object to the disclosure, and the '
                                     'individual does not express an objection; or\n'
                                     '\n'
                                     '(iii) Reasonably infers from the circumstances, based on the exercise of professional '
                                     'judgment, that the individual does not object to the disclosure.',
          'subchapter': '164.510(b): Health care providers.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': ['Q-AST-12: Does the organization restrict the possession and usage of personally-owned '
                                   'technology devices within organization-controlled facilities?.',
                                   'Q-END-14.6: Does the organization configure collaborative computing devices to provide '
                                   'physically-present individuals with an explicit indication of use?.',
                                   'Q-DCH-10.2: Does the organization prohibit the use of portable storage devices in '
                                   'organizational information systems when such devices have no identifiable owner?.'],
          'objective_title': '164.510(b)(3): Limited uses and disclosures when the individual is not present.',
          'requirement_description': 'If the individual is not present, or the opportunity to agree or object to the use or '
                                     "disclosure cannot practicably be provided because of the individual's incapacity or an "
                                     'emergency circumstance, the covered entity may, in the exercise of professional '
                                     'judgment, determine whether the disclosure is in the best interests of the individual '
                                     'and, if so, disclose only the protected health information that is directly relevant to '
                                     "the person's involvement with the individual's care or payment related to the "
                                     "individual's health care or needed for notification purposes. A covered entity may use "
                                     'professional judgment and its experience with common practice to make reasonable '
                                     "inferences of the individual's best interest in allowing a person to act on behalf of "
                                     'the individual to pick up filled prescriptions, medical supplies, X-rays, or other '
                                     'similar forms of protected health information.',
          'subchapter': '164.510(b): Health plans.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': ['Q-IRO-12.2: Does the organization ensure incident response training material provides '
                                   'coverage for sensitive information spillage response?.'],
          'objective_title': '164.510(b)(4): Uses and disclosures for disaster relief purposes.',
          'requirement_description': 'A covered entity may use or disclose protected health information to a public or private '
                                     'entity authorized by law or by its charter to assist in disaster relief efforts, for the '
                                     'purpose of coordinating with such entities the uses or disclosures permitted by '
                                     'paragraph (b)(1)(ii) of this section. The requirements in paragraphs (b)(2), (b)(3), or '
                                     '(b)(5) of this section apply to such uses and disclosures to the extent that the covered '
                                     'entity, in the exercise of professional judgment, determines that the requirements do '
                                     'not interfere with the ability to respond to the emergency circumstances.',
          'subchapter': '164.510(b): Health clearinghouses.'},
         {'chapter_title': '164.510: Uses and disclosures requiring an opportunity for the individual to agree or to object.',
          'conformity_questions': [],
          'objective_title': '164.510(b)(5): Uses and disclosures when the individual is deceased.',
          'requirement_description': 'If the individual is deceased, a covered entity may disclose to a family member, or '
                                     'other persons identified in paragraph (b)(1) of this section who were involved in the '
                                     "individual's care or payment for health care prior to the individual's death, protected "
                                     "health information of the individual that is relevant to such person's involvement, "
                                     'unless doing so is inconsistent with any prior expressed preference of the individual '
                                     'that is known to the covered entity.',
          'subchapter': "164.510(b):  Standard: Uses and disclosures for involvement in the individual's care and notification "
                        'purposes'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(a)(1): Standard: Uses and disclosures required by law.',
          'requirement_description': '(1) A covered entity may use or disclose protected health information to the extent that '
                                     'such use or disclosure is required by law and the use or disclosure complies with and is '
                                     'limited to the relevant requirements of such law.\n'
                                     '\n'
                                     '(2) A covered entity must meet the requirements described in paragraph (c), (e), or (f) '
                                     'of this section for uses or disclosures required by law.',
          'subchapter': '164.512(a):  Standard: Uses and disclosures required by law.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-MON-02.5: Does the organization specify the permitted actions for both users and systems '
                                   'associated with the review, analysis and reporting of audit information? .',
                                   'Q-AST-05.1: Does the organization obtain management approval for any sensitive / regulated '
                                   "media that is transferred outside of the organization's facilities?.",
                                   'Q-CFG-04: Does the organization enforce software usage restrictions to comply with '
                                   'applicable contract agreements and copyright laws?.'],
          'objective_title': '164.512(b)(1): Permitted uses and disclosures.',
          'requirement_description': 'A covered entity may use or disclose protected health information for the public health '
                                     'activities and purposes described in this paragraph to:\n'
                                     '\n'
                                     '(i) A public health authority that is authorized by law to collect or receive such '
                                     'information for the purpose of preventing or controlling disease, injury, or disability, '
                                     'including, but not limited to, the reporting of disease, injury, vital events such as '
                                     'birth or death, and the conduct of public health surveillance, public health '
                                     'investigations, and public health interventions; or, at the direction of a public health '
                                     'authority, to an official of a foreign government agency that is acting in collaboration '
                                     'with a public health authority;\n'
                                     '\n'
                                     '(ii) A public health authority or other appropriate government authority authorized by '
                                     'law to receive reports of child abuse or neglect;\n'
                                     '\n'
                                     '(iii) A person subject to the jurisdiction of the Food and Drug Administration (FDA) '
                                     'with respect to an FDA-regulated product or activity for which that person has '
                                     'responsibility, for the purpose of activities related to the quality, safety or '
                                     'effectiveness of such FDA-regulated product or activity. Such purposes include:\n'
                                     '\n'
                                     '(A) To collect or report adverse events (or similar activities with respect to food or '
                                     'dietary supplements), product defects or problems (including problems with the use or '
                                     'labeling of a product), or biological product deviations;\n'
                                     '\n'
                                     '(B) To track FDA-regulated products;\n'
                                     '\n'
                                     '(C) To enable product recalls, repairs, or replacement, or lookback (including locating '
                                     'and notifying individuals who have received products that have been recalled, withdrawn, '
                                     'or are the subject of lookback); or\n'
                                     '\n'
                                     '(D) To conduct post marketing surveillance;\n'
                                     '\n'
                                     '(iv) A person who may have been exposed to a communicable disease or may otherwise be at '
                                     'risk of contracting or spreading a disease or condition, if the covered entity or public '
                                     'health authority is authorized by law to notify such person as necessary in the conduct '
                                     'of a public health intervention or investigation; or\n'
                                     '\n'
                                     '(v) An employer, about an individual who is a member of the workforce of the employer, '
                                     'if:\n'
                                     '\n'
                                     '(A) The covered entity is a covered health care provider who provides health care to the '
                                     'individual at the request of the employer:\n'
                                     '\n'
                                     '(1) To conduct an evaluation relating to medical surveillance of the workplace; or\n'
                                     '\n'
                                     '(2) To evaluate whether the individual has a work-related illness or injury;\n'
                                     '\n'
                                     '(B) The protected health information that is disclosed consists of findings concerning a '
                                     'work-related illness or injury or a workplace-related medical surveillance;\n'
                                     '\n'
                                     '(C) The employer needs such findings in order to comply with its obligations, under 29 '
                                     'CFR parts 1904 through 1928, 30 CFR parts 50 through 90, or under state law having a '
                                     'similar purpose, to record such illness or injury or to carry out responsibilities for '
                                     'workplace medical surveillance; and\n'
                                     '\n'
                                     '(D) The covered health care provider provides written notice to the individual that '
                                     'protected health information relating to the medical surveillance of the workplace and '
                                     'work-related illnesses and injuries is disclosed to the employer:\n'
                                     '\n'
                                     '(1) By giving a copy of the notice to the individual at the time the health care is '
                                     'provided; or\n'
                                     '\n'
                                     '(2) If the health care is provided on the work site of the employer, by posting the '
                                     'notice in a prominent place at the location where the health care is provided.\n'
                                     '\n'
                                     '(vi) A school, about an individual who is a student or prospective student of the '
                                     'school, if:\n'
                                     '\n'
                                     '(A) The protected health information that is disclosed is limited to proof of '
                                     'immunization;\n'
                                     '\n'
                                     '(B) The school is required by State or other law to have such proof of immunization '
                                     'prior to admitting the individual; and\n'
                                     '\n'
                                     '(C) The covered entity obtains and documents the agreement to the disclosure from '
                                     'either:\n'
                                     '\n'
                                     '(1) A parent, guardian, or other person acting in loco parentis of the individual, if '
                                     'the individual is an unemancipated minor; or\n'
                                     '\n'
                                     '(2) The individual, if the individual is an adult or emancipated minor.',
          'subchapter': '164.512(b):  Standard: Uses and disclosures for public health activities'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-DCH-12: Does the organization restrict removable media in accordance with data handling '
                                   'and acceptable usage parameters?.',
                                   'Q-CFG-03.3: Does the organization whitelist or blacklist applications in an order to limit '
                                   'what is authorized to execute on systems?.'],
          'objective_title': '164.512(b)(2): Permitted uses.',
          'requirement_description': 'If the covered entity also is a public health authority, the covered entity is permitted '
                                     'to use protected health information in all cases in which it is permitted to disclose '
                                     'such information for public health activities under paragraph (b)(1) of this section.',
          'subchapter': '164.512(b):  Standard: Uses and disclosures for public health activities'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-DCH-03.1: Does the organization limit the disclosure of data to authorized parties? .',
                                   'Q-PRI-07.4: Does the organization reject unauthorized disclosure requests?.',
                                   'Q-NET-03.3: Does the organization prevent the public disclosure of internal address '
                                   'information? .'],
          'objective_title': '164.512(c)(1): Permitted disclosures.',
          'requirement_description': 'Except for reports of child abuse or neglect permitted by paragraph (b)(1)(ii) of this '
                                     'section, a covered entity may disclose protected health information about an individual '
                                     'whom the covered entity reasonably believes to be a victim of abuse, neglect, or '
                                     'domestic violence to a government authority, including a social service or protective '
                                     'services agency, authorized by law to receive reports of such abuse, neglect, or '
                                     'domestic violence:\n'
                                     '\n'
                                     '(i) To the extent the disclosure is required by law and the disclosure complies with and '
                                     'is limited to the relevant requirements of such law;\n'
                                     '\n'
                                     '(ii) If the individual agrees to the disclosure; or\n'
                                     '\n'
                                     '(iii) To the extent the disclosure is expressly authorized by statute or regulation '
                                     'and:\n'
                                     '\n'
                                     '(A) The covered entity, in the exercise of professional judgment, believes the '
                                     'disclosure is necessary to prevent serious harm to the individual or other potential '
                                     'victims; or\n'
                                     '\n'
                                     '(B) If the individual is unable to agree because of incapacity, a law enforcement or '
                                     'other public official authorized to receive the report represents that the protected '
                                     'health information for which disclosure is sought is not intended to be used against the '
                                     'individual and that an immediate enforcement activity that depends upon the disclosure '
                                     'would be materially and adversely affected by waiting until the individual is able to '
                                     'agree to the disclosure.',
          'subchapter': '164.512(c):  Standard: Disclosures about victims of abuse, neglect or domestic violence'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(c)(2): Informing the individual.',
          'requirement_description': 'A covered entity that makes a disclosure permitted by paragraph (c)(1) of this section '
                                     'must promptly inform the individual that such a report has been or will be made, except '
                                     'if:\n'
                                     '\n'
                                     '(i) The covered entity, in the exercise of professional judgment, believes informing the '
                                     'individual would place the individual at risk of serious harm; or\n'
                                     '\n'
                                     '(ii) The covered entity would be informing a personal representative, and the covered '
                                     'entity reasonably believes the personal representative is responsible for the abuse, '
                                     'neglect, or other injury, and that informing such person would not be in the best '
                                     'interests of the individual as determined by the covered entity, in the exercise of '
                                     'professional judgment.',
          'subchapter': '164.512(c):  Standard: Disclosures about victims of abuse, neglect or domestic violence'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-PRI-17: Does the organization craft disclosures and communications to data subjects such '
                                   'that the material is readily accessible and written in a manner that is concise, '
                                   'unambiguous and understandable by a reasonable person?.',
                                   'Q-DCH-03.1: Does the organization limit the disclosure of data to authorized parties? .',
                                   'Q-PRI-07.4: Does the organization reject unauthorized disclosure requests?.'],
          'objective_title': '164.512(d)(1): Permitted disclosures.',
          'requirement_description': 'A covered entity may disclose protected health information to a health oversight agency '
                                     'for oversight activities authorized by law, including audits; civil, administrative, or '
                                     'criminal investigations; inspections; licensure or disciplinary actions; civil, '
                                     'administrative, or criminal proceedings or actions; or other activities necessary for '
                                     'appropriate oversight of:\n'
                                     '\n'
                                     '(i) The health care system;\n'
                                     '\n'
                                     '(ii) Government benefit programs for which health information is relevant to beneficiary '
                                     'eligibility;\n'
                                     '\n'
                                     '(iii) Entities subject to government regulatory programs for which health information is '
                                     'necessary for determining compliance with program standards; or\n'
                                     '\n'
                                     '(iv) Entities subject to civil rights laws for which health information is necessary for '
                                     'determining compliance.',
          'subchapter': '164.512(d):  Standard: Uses and disclosures for health oversight activities'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-GOV-02.1: Does the organization prohibit exceptions to standards, except when the '
                                   'exception has been formally assessed for risk impact, approved and recorded?.'],
          'objective_title': '164.512(d)(2): Exception to health oversight activities.',
          'requirement_description': 'For the purpose of the disclosures permitted by paragraph (d)(1) of this section, a '
                                     'health oversight activity does not include an investigation or other activity in which '
                                     'the individual is the subject of the investigation or activity and such investigation or '
                                     'other activity does not arise out of and is not directly related to:\n'
                                     '\n'
                                     '(i) The receipt of health care;\n'
                                     '\n'
                                     '(ii) A claim for public benefits related to health; or\n'
                                     '\n'
                                     "(iii) Qualification for, or receipt of, public benefits or services when a patient's "
                                     'health is integral to the claim for public benefits or services.',
          'subchapter': '164.512(d):  Standard: Uses and disclosures for health oversight activities'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-GOV-06: Does the organization identify and document appropriate contacts within relevant '
                                   'law enforcement and regulatory bodies?.'],
          'objective_title': '164.512(d)(3): Joint activities or investigations.',
          'requirement_description': 'Nothwithstanding paragraph (d)(2) of this section, if a health oversight activity or '
                                     'investigation is conducted in conjunction with an oversight activity or investigation '
                                     'relating to a claim for public benefits not related to health, the joint activity or '
                                     'investigation is considered a health oversight activity for purposes of paragraph (d) of '
                                     'this section.',
          'subchapter': '164.512(d):  Standard: Uses and disclosures for health oversight activities'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-DCH-12: Does the organization restrict removable media in accordance with data handling '
                                   'and acceptable usage parameters?.',
                                   'Q-CFG-03.3: Does the organization whitelist or blacklist applications in an order to limit '
                                   'what is authorized to execute on systems?.'],
          'objective_title': '164.512(d)(4): Permitted uses.',
          'requirement_description': 'If a covered entity also is a health oversight agency, the covered entity may use '
                                     'protected health information for health oversight activities as permitted by paragraph '
                                     '(d) of this section.',
          'subchapter': '164.512(d):  Standard: Uses and disclosures for health oversight activities'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-PRI-17: Does the organization craft disclosures and communications to data subjects such '
                                   'that the material is readily accessible and written in a manner that is concise, '
                                   'unambiguous and understandable by a reasonable person?.',
                                   'Q-DCH-03.1: Does the organization limit the disclosure of data to authorized parties? .',
                                   'Q-PRI-07.4: Does the organization reject unauthorized disclosure requests?.'],
          'objective_title': '164.512(e)(1): Permitted disclosures.',
          'requirement_description': 'A covered entity may disclose protected health information in the course of any judicial '
                                     'or administrative proceeding:\n'
                                     '\n'
                                     '(i) In response to an order of a court or administrative tribunal, provided that the '
                                     'covered entity discloses only the protected health information expressly authorized by '
                                     'such order; or\n'
                                     '\n'
                                     '(ii) In response to a subpoena, discovery request, or other lawful process, that is not '
                                     'accompanied by an order of a court or administrative tribunal, if:\n'
                                     '\n'
                                     '(A) The covered entity receives satisfactory assurance, as described in paragraph '
                                     '(e)(1)(iii) of this section, from the party seeking the information that reasonable '
                                     'efforts have been made by such party to ensure that the individual who is the subject of '
                                     'the protected health information that has been requested has been given notice of the '
                                     'request; or\n'
                                     '\n'
                                     '(B) The covered entity receives satisfactory assurance, as described in paragraph '
                                     '(e)(1)(iv) of this section, from the party seeking the information that reasonable '
                                     'efforts have been made by such party to secure a qualified protective order that meets '
                                     'the requirements of paragraph (e)(1)(v) of this section.\n'
                                     '\n'
                                     '(iii) For the purposes of paragraph (e)(1)(ii)(A) of this section, a covered entity '
                                     'receives satisfactory assurances from a party seeking protected health information if '
                                     'the covered entity receives from such party a written statement and accompanying '
                                     'documentation demonstrating that:\n'
                                     '\n'
                                     '(A) The party requesting such information has made a good faith attempt to provide '
                                     "written notice to the individual (or, if the individual's location is unknown, to mail a "
                                     "notice to the individual's last known address);\n"
                                     '\n'
                                     '(B) The notice included sufficient information about the litigation or proceeding in '
                                     'which the protected health information is requested to permit the individual to raise an '
                                     'objection to the court or administrative tribunal; and\n'
                                     '\n'
                                     '(C) The time for the individual to raise objections to the court or administrative '
                                     'tribunal has elapsed, and:\n'
                                     '\n'
                                     '(1) No objections were filed; or\n'
                                     '\n'
                                     '(2) All objections filed by the individual have been resolved by the court or the '
                                     'administrative tribunal and the disclosures being sought are consistent with such '
                                     'resolution.\n'
                                     '\n'
                                     '(iv) For the purposes of paragraph (e)(1)(ii)(B) of this section, a covered entity '
                                     'receives satisfactory assurances from a party seeking protected health information, if '
                                     'the covered entity receives from such party a written statement and accompanying '
                                     'documentation demonstrating that:\n'
                                     '\n'
                                     '(A) The parties to the dispute giving rise to the request for information have agreed to '
                                     'a qualified protective order and have presented it to the court or administrative '
                                     'tribunal with jurisdiction over the dispute; or\n'
                                     '\n'
                                     '(B) The party seeking the protected health information has requested a qualified '
                                     'protective order from such court or administrative tribunal.\n'
                                     '\n'
                                     '(v) For purposes of paragraph (e)(1) of this section, a qualified protective order '
                                     'means, with respect to protected health information requested under paragraph (e)(1)(ii) '
                                     'of this section, an order of a court or of an administrative tribunal or a stipulation '
                                     'by the parties to the litigation or administrative proceeding that:\n'
                                     '\n'
                                     '(A) Prohibits the parties from using or disclosing the protected health information for '
                                     'any purpose other than the litigation or proceeding for which such information was '
                                     'requested; and\n'
                                     '\n'
                                     '(B) Requires the return to the covered entity or destruction of the protected health '
                                     'information (including all copies made) at the end of the litigation or proceeding.\n'
                                     '\n'
                                     '(vi) Notwithstanding paragraph (e)(1)(ii) of this section, a covered entity may disclose '
                                     'protected health information in response to lawful process described in paragraph '
                                     '(e)(1)(ii) of this section without receiving satisfactory assurance under paragraph '
                                     '(e)(1)(ii)(A) or (B) of this section, if the covered entity makes reasonable efforts to '
                                     'provide notice to the individual sufficient to meet the requirements of paragraph '
                                     '(e)(1)(iii) of this section or to seek a qualified protective order sufficient to meet '
                                     'the requirements of paragraph (e)(1)(v) of this section.',
          'subchapter': '164.512(e):  Standard: Disclosures for judicial and administrative proceedings '},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(e)(2): Other uses and disclosures under this section.',
          'requirement_description': 'The provisions of this paragraph do not supersede other provisions of this section that '
                                     'otherwise permit or restrict uses or disclosures of protected health information.',
          'subchapter': '164.512(e):  Standard: Disclosures for judicial and administrative proceedings '},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-DCH-04: Does the organization mark media in accordance with data protection requirements '
                                   'so that personnel are alerted to distribution limitations, handling caveats and applicable '
                                   'security requirements? .',
                                   'Q-CPL-01: Does the organization facilitate the implementation of relevant statutory, '
                                   'regulatory and contractual controls?.',
                                   'Q-GOV-17: Does the organization submit status reporting of its cybersecurity and/or data '
                                   'privacy program to applicable statutory and/or regulatory authorities, as required?.'],
          'objective_title': '164.512(f)(1): Permitted disclosures: Pursuant to process and as otherwise required by law.',
          'requirement_description': 'A covered entity may disclose protected health information:\n'
                                     '\n'
                                     '(i) As required by law including laws that require the reporting of certain types of '
                                     'wounds or other physical injuries, except for laws subject to paragraph (b)(1)(ii) or '
                                     '(c)(1)(i) of this section; or\n'
                                     '\n'
                                     '(ii) In compliance with and as limited by the relevant requirements of:\n'
                                     '\n'
                                     '(A) A court order or court-ordered warrant, or a subpoena or summons issued by a '
                                     'judicial officer;\n'
                                     '\n'
                                     '(B) A grand jury subpoena; or\n'
                                     '\n'
                                     '(C) An administrative request, including an administrative subpoena or summons, a civil '
                                     'or an authorized investigative demand, or similar process authorized under law, provided '
                                     'that:\n'
                                     '\n'
                                     '(1) The information sought is relevant and material to a legitimate law enforcement '
                                     'inquiry;\n'
                                     '\n'
                                     '(2) The request is specific and limited in scope to the extent reasonably practicable in '
                                     'light of the purpose for which the information is sought; and\n'
                                     '\n'
                                     '(3) De-identified information could not reasonably be used.',
          'subchapter': '164.512(f):  Standard: Disclosures for law enforcement purposes.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-CRY-01.1: Does the organization use cryptographic mechanisms to prevent unauthorized '
                                   'disclosure of information as an alternate to physical safeguards? .',
                                   'Q-MON-09.1: Does the organization bind the identity of the information producer to the '
                                   'information generated?.',
                                   'Q-AST-02.10: Does the organization track the geographic location of system components?.'],
          'objective_title': '164.512(f)(2): Permitted disclosures: Limited information for identification and location '
                             'purposes.',
          'requirement_description': 'Except for disclosures required by law as permitted by paragraph (f)(1) of this section, '
                                     'a covered entity may disclose protected health information in response to a law '
                                     "enforcement official's request for such information for the purpose of identifying or "
                                     'locating a suspect, fugitive, material witness, or missing person, provided that:\n'
                                     '\n'
                                     '(i) The covered entity may disclose only the following information:\n'
                                     '\n'
                                     '(A) Name and address;\n'
                                     '\n'
                                     '(B) Date and place of birth;\n'
                                     '\n'
                                     '(C) Social security number;\n'
                                     '\n'
                                     '(D) ABO blood type and rh factor;\n'
                                     '\n'
                                     '(E) Type of injury;\n'
                                     '\n'
                                     '(F) Date and time of treatment;\n'
                                     '\n'
                                     '(G) Date and time of death, if applicable; and\n'
                                     '\n'
                                     '(H) A description of distinguishing physical characteristics, including height, weight, '
                                     'gender, race, hair and eye color, presence or absence of facial hair (beard or '
                                     'moustache), scars, and tattoos.\n'
                                     '\n'
                                     '(ii) Except as permitted by paragraph (f)(2)(i) of this section, the covered entity may '
                                     'not disclose for the purposes of identification or location under paragraph (f)(2) of '
                                     "this section any protected health information related to the individual's DNA or DNA "
                                     'analysis, dental records, or typing, samples or analysis of body fluids or tissue.',
          'subchapter': '164.512(f):  Standard: Disclosures for law enforcement purposes.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(f)(3): Permitted disclosure: Victims of a crime.',
          'requirement_description': 'Except for disclosures required by law as permitted by paragraph (f)(1) of this section, '
                                     'a covered entity may disclose protected health information in response to a law '
                                     "enforcement official's request for such information about an individual who is or is "
                                     'suspected to be a victim of a crime, other than disclosures that are subject to '
                                     'paragraph (b) or (c) of this section, if:\n'
                                     '\n'
                                     '(i) The individual agrees to the disclosure; or\n'
                                     '\n'
                                     "(ii) The covered entity is unable to obtain the individual's agreement because of "
                                     'incapacity or other emergency circumstance, provided that:\n'
                                     '\n'
                                     '(A) The law enforcement official represents that such information is needed to determine '
                                     'whether a violation of law by a person other than the victim has occurred, and such '
                                     'information is not intended to be used against the victim;\n'
                                     '\n'
                                     '(B) The law enforcement official represents that immediate law enforcement activity that '
                                     'depends upon the disclosure would be materially and adversely affected by waiting until '
                                     'the individual is able to agree to the disclosure; and\n'
                                     '\n'
                                     '(C) The disclosure is in the best interests of the individual as determined by the '
                                     'covered entity, in the exercise of professional judgment.',
          'subchapter': '164.512(f):  Standard: Disclosures for law enforcement purposes.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-PRI-14.1: Does the organization develop and maintain an accounting of disclosures of '
                                   'Personal Data (PD) held by the organization and make the accounting of disclosures '
                                   'available to the person named in the record, upon request?.',
                                   'Q-PRI-14.2: Does the organization notify data subjects of applicable legal requests to '
                                   'disclose Personal Data (PD)?.'],
          'objective_title': '164.512(f)(4): Permitted disclosure: Decedents.',
          'requirement_description': 'A covered entity may disclose protected health information about an individual who has '
                                     'died to a law enforcement official for the purpose of alerting law enforcement of the '
                                     'death of the individual if the covered entity has a suspicion that such death may have '
                                     'resulted from criminal conduct.',
          'subchapter': '164.512(f):  Standard: Disclosures for law enforcement purposes.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-HRS-15: Does the organization empower personnel to efficiently report suspicious '
                                   'activities and/or behavior without fear of reprisal or other negative consequences?.'],
          'objective_title': '164.512(f)(5): Permitted disclosure: Crime on premises.',
          'requirement_description': 'A covered entity may disclose to a law enforcement official protected health information '
                                     'that the covered entity believes in good faith constitutes evidence of criminal conduct '
                                     'that occurred on the premises of the covered entity.',
          'subchapter': '164.512(f):  Standard: Disclosures for law enforcement purposes.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-IRO-02.5: Does the organization coordinate with approved third-parties to achieve a '
                                   'cross-organization perspective on incident awareness and more effective incident '
                                   'responses? .',
                                   'Q-IRO-10.2: Does the organization report sensitive/regulated data incidents in a timely '
                                   'manner?.',
                                   'Q-HRS-15: Does the organization empower personnel to efficiently report suspicious '
                                   'activities and/or behavior without fear of reprisal or other negative consequences?.'],
          'objective_title': '164.512(f)(6): Permitted disclosure: Reporting crime in emergencies.',
          'requirement_description': '(i) A covered health care provider providing emergency health care in response to a '
                                     'medical emergency, other than such emergency on the premises of the covered health care '
                                     'provider, may disclose protected health information to a law enforcement official if '
                                     'such disclosure appears necessary to alert law enforcement to:\n'
                                     '\n'
                                     '(A) The commission and nature of a crime;\n'
                                     '\n'
                                     '(B) The location of such crime or of the victim(s) of such crime; and\n'
                                     '\n'
                                     '(C) The identity, description, and location of the perpetrator of such crime.\n'
                                     '\n'
                                     '(ii) If a covered health care provider believes that the medical emergency described in '
                                     'paragraph (f)(6)(i) of this section is the result of abuse, neglect, or domestic '
                                     'violence of the individual in need of emergency health care, paragraph (f)(6)(i) of this '
                                     'section does not apply and any disclosure to a law enforcement official for law '
                                     'enforcement purposes is subject to paragraph (c) of this section.',
          'subchapter': '164.512(f):  Standard: Disclosures for law enforcement purposes.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(g)(1): Coroners and medical examiners.',
          'requirement_description': 'A covered entity may disclose protected health information to a coroner or medical '
                                     'examiner for the purpose of identifying a deceased person, determining a cause of death, '
                                     'or other duties as authorized by law. A covered entity that also performs the duties of '
                                     'a coroner or medical examiner may use protected health information for the purposes '
                                     'described in this paragraph.',
          'subchapter': '164.512(g):  Standard: Uses and disclosures about decedents'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(g)(2): Funeral directors.',
          'requirement_description': 'A covered entity may disclose protected health information to funeral directors, '
                                     'consistent with applicable law, as necessary to carry out their duties with respect to '
                                     'the decedent. If necessary for funeral directors to carry out their duties, the covered '
                                     'entity may disclose the protected health information prior to, and in reasonable '
                                     "anticipation of, the individual's death.",
          'subchapter': '164.512(g):  Standard: Uses and disclosures about decedents'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(h)(1): Standard: Uses and disclosures for cadaveric organ, eye or tissue donation '
                             'purposes.',
          'requirement_description': 'A covered entity may use or disclose protected health information to organ procurement '
                                     'organizations or other entities engaged in the procurement, banking, or transplantation '
                                     'of cadaveric organs, eyes, or tissue for the purpose of facilitating organ, eye or '
                                     'tissue donation and transplantation.',
          'subchapter': '164.512(h):  Standard: Uses and disclosures for cadaveric organ, eye or tissue donation purposes.'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-MON-02.5: Does the organization specify the permitted actions for both users and systems '
                                   'associated with the review, analysis and reporting of audit information? .',
                                   'Q-AST-05.1: Does the organization obtain management approval for any sensitive / regulated '
                                   "media that is transferred outside of the organization's facilities?.",
                                   'Q-CFG-04: Does the organization enforce software usage restrictions to comply with '
                                   'applicable contract agreements and copyright laws?.'],
          'objective_title': '164.512(i)(1): Permitted uses and disclosures.',
          'requirement_description': 'A covered entity may use or disclose protected health information for research, '
                                     'regardless of the source of funding of the research, provided that:\n'
                                     '\n'
                                     '(i) Board approval of a waiver of authorization.  The covered entity obtains '
                                     'documentation that an alteration to or waiver, in whole or in part, of the individual '
                                     'authorization required by  164.508 for use or disclosure of protected health information '
                                     'has been approved by either:\n'
                                     '\n'
                                     '(A) An Institutional Review Board (IRB), established in accordance with 7 CFR lc.107, 10 '
                                     'CFR 745.107, 14 CFR 1230.107, 15 CFR 27.107, 16 CFR 1028.107, 21 CFR 56.107, 22 CFR '
                                     '225.107, 24 CFR 60.107, 28 CFR 46.107, 32 CFR 219.107, 34 CFR 97.107, 38 CFR 16.107, 40 '
                                     'CFR 26.107, 45 CFR 46.107, 45 CFR 690.107, or 49 CFR 11.107; or\n'
                                     '\n'
                                     '(B) A privacy board that:\n'
                                     '\n'
                                     '(1) Has members with varying backgrounds and appropriate professional competency as '
                                     "necessary to review the effect of the research protocol on the individual's privacy "
                                     'rights and related interests;\n'
                                     '\n'
                                     '(2) Includes at least one member who is not affiliated with the covered entity, not '
                                     'affiliated with any entity conducting or sponsoring the research, and not related to any '
                                     'person who is affiliated with any of such entities; and\n'
                                     '\n'
                                     '(3) Does not have any member participating in a review of any project in which the '
                                     'member has a conflict of interest.\n'
                                     '\n'
                                     '(ii) Reviews preparatory to research.  The covered entity obtains from the researcher '
                                     'representations that:\n'
                                     '\n'
                                     '(A) Use or disclosure is sought solely to review protected health information as '
                                     'necessary to prepare a research protocol or for similar purposes preparatory to '
                                     'research;\n'
                                     '\n'
                                     '(B) No protected health information is to be removed from the covered entity by the '
                                     'researcher in the course of the review; and\n'
                                     '\n'
                                     '(C) The protected health information for which use or access is sought is necessary for '
                                     'the research purposes.\n'
                                     '\n'
                                     "(iii) Research on decedent's information.  The covered entity obtains from the "
                                     'researcher:\n'
                                     '\n'
                                     '(A) Representation that the use or disclosure sought is solely for research on the '
                                     'protected health information of decedents;\n'
                                     '\n'
                                     '(B) Documentation, at the request of the covered entity, of the death of such '
                                     'individuals; and\n'
                                     '\n'
                                     '(C) Representation that the protected health information for which use or disclosure is '
                                     'sought is necessary for the research purposes.',
          'subchapter': '164.512(i):  Standard: Uses and disclosures for research purposes'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-AST-02.4: Does the organization document and govern instances of approved deviations '
                                   'from established baseline configurations?.',
                                   'Q-CFG-02.7: Does the organization document, assess risk and approve or deny deviations to '
                                   'standardized configurations..'],
          'objective_title': '164.512(i)(2): Documentation of waiver approval.',
          'requirement_description': 'For a use or disclosure to be permitted based on documentation of approval of an '
                                     'alteration or waiver, under paragraph (i)(1)(i) of this section, the documentation must '
                                     'include all of the following:\n'
                                     '\n'
                                     '(i) Identification and date of action.  A statement identifying the IRB or privacy board '
                                     'and the date on which the alteration or waiver of authorization was approved;\n'
                                     '\n'
                                     '(ii) Waiver criteria.  A statement that the IRB or privacy board has determined that the '
                                     'alteration or waiver, in whole or in part, of authorization satisfies the following '
                                     'criteria:\n'
                                     '\n'
                                     '(A) The use or disclosure of protected health information involves no more than a '
                                     'minimal risk to the privacy of individuals, based on, at least, the presence of the '
                                     'following elements;\n'
                                     '\n'
                                     '(1) An adequate plan to protect the identifiers from improper use and disclosure;\n'
                                     '\n'
                                     '(2) An adequate plan to destroy the identifiers at the earliest opportunity consistent '
                                     'with conduct of the research, unless there is a health or research justification for '
                                     'retaining the identifiers or such retention is otherwise required by law; and\n'
                                     '\n'
                                     '(3) Adequate written assurances that the protected health information will not be reused '
                                     'or disclosed to any other person or entity, except as required by law, for authorized '
                                     'oversight of the research study, or for other research for which the use or disclosure '
                                     'of protected health information would be permitted by this subpart;\n'
                                     '\n'
                                     '(B) The research could not practicably be conducted without the waiver or alteration; '
                                     'and\n'
                                     '\n'
                                     '(C) The research could not practicably be conducted without access to and use of the '
                                     'protected health information.\n'
                                     '\n'
                                     '(iii) Protected health information needed.  A brief description of the protected health '
                                     'information for which use or access has been determined to be necessary by the '
                                     'institutional review board or privacy board, pursuant to paragraph (i)(2)(ii)(C) of this '
                                     'section;\n'
                                     '\n'
                                     '(iv) Review and approval procedures.  A statement that the alteration or waiver of '
                                     'authorization has been reviewed and approved under either normal or expedited review '
                                     'procedures, as follows:\n'
                                     '\n'
                                     '(A) An IRB must follow the requirements of the Common Rule, including the normal review '
                                     'procedures (7 CFR 1c.108(b), 10 CFR 745.108(b), 14 CFR 1230.108(b), 15 CFR 27.108(b), 16 '
                                     'CFR 1028.108(b), 21 CFR 56.108(b), 22 CFR 225.108(b), 24 CFR 60.108(b), 28 CFR '
                                     '46.108(b), 32 CFR 219.108(b), 34 CFR 97.108(b), 38 CFR 16.108(b), 40 CFR 26.108(b), 45 '
                                     'CFR 46.108(b), 45 CFR 690.108(b), or 49 CFR 11.108(b)) or the expedited review '
                                     'procedures (7 CFR 1c.110, 10 CFR 745.110, 14 CFR 1230.110, 15 CFR 27.110, 16 CFR '
                                     '1028.110, 21 CFR 56.110, 22 CFR 225.110, 24 CFR 60.110, 28 CFR 46.110, 32 CFR 219.110, '
                                     '34 CFR 97.110, 38 CFR 16.110, 40 CFR 26.110, 45 CFR 46.110, 45 CFR 690.110, or 49 CFR '
                                     '11.110);\n'
                                     '\n'
                                     '(B) A privacy board must review the proposed research at convened meetings at which a '
                                     'majority of the privacy board members are present, including at least one member who '
                                     'satisfies the criterion stated in paragraph (i)(1)(i)(B)(2) of this section, and the '
                                     'alteration or waiver of authorization must be approved by the majority of the privacy '
                                     'board members present at the meeting, unless the privacy board elects to use an '
                                     'expedited review procedure in accordance with paragraph (i)(2)(iv)(C) of this section;\n'
                                     '\n'
                                     '(C) A privacy board may use an expedited review procedure if the research involves no '
                                     'more than minimal risk to the privacy of the individuals who are the subject of the '
                                     'protected health information for which use or disclosure is being sought. If the privacy '
                                     'board elects to use an expedited review procedure, the review and approval of the '
                                     'alteration or waiver of authorization may be carried out by the chair of the privacy '
                                     'board, or by one or more members of the privacy board as designated by the chair; and\n'
                                     '\n'
                                     '(v) Required signature.  The documentation of the alteration or waiver of authorization '
                                     'must be signed by the chair or other member, as designated by the chair, of the IRB or '
                                     'the privacy board, as applicable.',
          'subchapter': '164.512(i):  Standard: Uses and disclosures for research purposes'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-THR-06.1: Does the organization enable public submissions of discovered or potential '
                                   'security vulnerabilities?.'],
          'objective_title': '164.512(j)(1): Permitted disclosures.',
          'requirement_description': 'A covered entity may, consistent with applicable law and standards of ethical conduct, '
                                     'use or disclose protected health information, if the covered entity, in good faith, '
                                     'believes the use or disclosure:\n'
                                     '\n'
                                     '(i)\n'
                                     '\n'
                                     '(A) Is necessary to prevent or lessen a serious and imminent threat to the health or '
                                     'safety of a person or the public; and\n'
                                     '\n'
                                     '(B) Is to a person or persons reasonably able to prevent or lessen the threat, including '
                                     'the target of the threat; or\n'
                                     '\n'
                                     '(ii) Is necessary for law enforcement authorities to identify or apprehend an '
                                     'individual:\n'
                                     '\n'
                                     '(A) Because of a statement by an individual admitting participation in a violent crime '
                                     'that the covered entity reasonably believes may have caused serious physical harm to the '
                                     'victim; or\n'
                                     '\n'
                                     '(B) Where it appears from all the circumstances that the individual has escaped from a '
                                     'correctional institution or from lawful custody, as those terms are defined in  164.501.',
          'subchapter': '164.512(j):  Standard: Uses and disclosures to avert a serious threat to health or safety'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-CPL-06: Does the organization constrain the host government from having unrestricted and '
                                   "non-monitored access to the organization's systems, applications and services that could "
                                   'potentially violate other applicable statutory, regulatory and/or contractual '
                                   'obligations..',
                                   'Q-CFG-05: Does the organization restrict the ability of non-privileged users to install '
                                   'unauthorized software?.',
                                   'Q-CFG-03.3: Does the organization whitelist or blacklist applications in an order to limit '
                                   'what is authorized to execute on systems?.'],
          'objective_title': '164.512(j)(2): Use or disclosure not permitted.',
          'requirement_description': 'A use or disclosure pursuant to paragraph (j)(1)(ii)(A) of this section may not be made '
                                     'if the information described in paragraph (j)(1)(ii)(A) of this section is learned by '
                                     'the covered entity:\n'
                                     '\n'
                                     '(i) In the course of treatment to affect the propensity to commit the criminal conduct '
                                     'that is the basis for the disclosure under paragraph (j)(1)(ii)(A) of this section, or '
                                     'counseling or therapy; or\n'
                                     '\n'
                                     '(ii) Through a request by the individual to initiate or to be referred for the '
                                     'treatment, counseling, or therapy described in paragraph (j)(2)(i) of this section.',
          'subchapter': '164.512(j):  Standard: Uses and disclosures to avert a serious threat to health or safety'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-MON-03.5: Does the organization limit Personal Data (PD) contained in audit records to '
                                   'the elements identified in the privacy risk assessment?.',
                                   'Q-CLD-10: Does the organization limit and manage the storage of sensitive/regulated data '
                                   'in public cloud providers? .',
                                   'Q-DCH-03.1: Does the organization limit the disclosure of data to authorized parties? .'],
          'objective_title': '164.512(j)(3): Limit on information that may be disclosed.',
          'requirement_description': 'A disclosure made pursuant to paragraph (j)(1)(ii)(A) of this section shall contain only '
                                     'the statement described in paragraph (j)(1)(ii)(A) of this section and the protected '
                                     'health information described in paragraph (f)(2)(i) of this section.',
          'subchapter': '164.512(j):  Standard: Uses and disclosures to avert a serious threat to health or safety'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(j)(4): Presumption of good faith belief.',
          'requirement_description': 'A covered entity that uses or discloses protected health information pursuant to '
                                     'paragraph (j)(1) of this section is presumed to have acted in good faith with regard to '
                                     'a belief described in paragraph (j)(1)(i) or (ii) of this section, if the belief is '
                                     "based upon the covered entity's actual knowledge or in reliance on a credible "
                                     'representation by a person with apparent knowledge or authority.',
          'subchapter': '164.512(j):  Standard: Uses and disclosures to avert a serious threat to health or safety'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(k)(1): Military and veterans activities',
          'requirement_description': '(i) Armed Forces personnel.  A covered entity may use and disclose the protected health '
                                     'information of individuals who are Armed Forces personnel for activities deemed '
                                     'necessary by appropriate military command authorities to assure the proper execution of '
                                     'the military mission, if the appropriate military authority has published by notice in '
                                     'the Federal Register the following information:\n'
                                     '\n'
                                     '(A) Appropriate military command authorities; and\n'
                                     '\n'
                                     '(B) The purposes for which the protected health information may be used or disclosed.\n'
                                     '\n'
                                     '(ii) Separation or discharge from military service.  A covered entity that is a '
                                     'component of the Departments of Defense or Homeland Security may disclose to the '
                                     'Department of Veterans Affairs (DVA) the protected health information of an individual '
                                     'who is a member of the Armed Forces upon the separation or discharge of the individual '
                                     "from military service for the purpose of a determination by DVA of the individual's "
                                     'eligibility for or entitlement to benefits under laws administered by the Secretary of '
                                     'Veterans Affairs.\n'
                                     '\n'
                                     '(iii) Veterans.  A covered entity that is a component of the Department of Veterans '
                                     'Affairs may use and disclose protected health information to components of the '
                                     'Department that determine eligibility for or entitlement to, or that provide, benefits '
                                     'under the laws administered by the Secretary of Veterans Affairs.\n'
                                     '\n'
                                     '(iv) Foreign military personnel.  A covered entity may use and disclose the protected '
                                     'health information of individuals who are foreign military personnel to their '
                                     'appropriate foreign military authority for the same purposes for which uses and '
                                     'disclosures are permitted for Armed Forces personnel under the notice published in the '
                                     'Federal Register pursuant to paragraph (k)(1)(i) of this section.',
          'subchapter': '164.512(k):  Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': ['Q-SAT-03.9: Does the organization provide specialized counterintelligence awareness '
                                   'training that enables personnel to collect, interpret and act upon a range of data sources '
                                   'that may signal the presence of a hostile actor?.'],
          'objective_title': '164.512(k)(2): National security and intelligence activities.',
          'requirement_description': 'A covered entity may disclose protected health information to authorized federal '
                                     'officials for the conduct of lawful intelligence, counter-intelligence, and other '
                                     'national security activities authorized by the National Security Act (50 U.S.C. 401, et '
                                     'seq.) and implementing authority (e.g., Executive Order 12333). ',
          'subchapter': '164.512(k):  Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(k)(3): Protective services for the President and others.',
          'requirement_description': 'A covered entity may disclose protected health information to authorized Federal '
                                     'officials for the provision of protective services to the President or other persons '
                                     'authorized by 18 U.S.C. 3056 or to foreign heads of state or other persons authorized by '
                                     '22 U.S.C. 2709(a)(3), or for the conduct of investigations authorized by 18 U.S.C. 871 '
                                     'and 879.',
          'subchapter': '164.512(k):  Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(k)(4): Medical suitability determinations.',
          'requirement_description': 'A covered entity that is a component of the Department of State may use protected health '
                                     'information to make medical suitability determinations and may disclose whether or not '
                                     'the individual was determined to be medically suitable to the officials in the '
                                     'Department of State who need access to such information for the following purposes:\n'
                                     '\n'
                                     '(i) For the purpose of a required security clearance conducted pursuant to Executive '
                                     'Orders 10450 and 12968;\n'
                                     '\n'
                                     '(ii) As necessary to determine worldwide availability or availability for mandatory '
                                     'service abroad under sections 101(a)(4) and 504 of the Foreign Service Act; or\n'
                                     '\n'
                                     '(iii) For a family to accompany a Foreign Service member abroad, consistent with section '
                                     '101(b)(5) and 904 of the Foreign Service Act.',
          'subchapter': '164.512(k):  Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(k)(5): Correctional institutions and other law enforcement custodial situations',
          'requirement_description': '(i) Permitted disclosures.  A covered entity may disclose to a correctional institution '
                                     'or a law enforcement official having lawful custody of an inmate or other individual '
                                     'protected health information about such inmate or individual, if the correctional '
                                     'institution or such law enforcement official represents that such protected health '
                                     'information is necessary for:\n'
                                     '\n'
                                     '(A) The provision of health care to such individuals;\n'
                                     '\n'
                                     '(B) The health and safety of such individual or other inmates;\n'
                                     '\n'
                                     '(C) The health and safety of the officers or employees of or others at the correctional '
                                     'institution;\n'
                                     '\n'
                                     '(D) The health and safety of such individuals and officers or other persons responsible '
                                     'for the transporting of inmates or their transfer from one institution, facility, or '
                                     'setting to another;\n'
                                     '\n'
                                     '(E) Law enforcement on the premises of the correctional institution; or\n'
                                     '\n'
                                     '(F) The administration and maintenance of the safety, security, and good order of the '
                                     'correctional institution.\n'
                                     '\n'
                                     '(ii) Permitted uses.  A covered entity that is a correctional institution may use '
                                     'protected health information of individuals who are inmates for any purpose for which '
                                     'such protected health information may be disclosed.\n'
                                     '\n'
                                     '(iii) No application after release.  For the purposes of this provision, an individual '
                                     'is no longer an inmate when released on parole, probation, supervised release, or '
                                     'otherwise is no longer in lawful custody.',
          'subchapter': '164.512(k):  Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(k)(6): Covered entities that are government programs providing public benefits.',
          'requirement_description': '(i) A health plan that is a government program providing public benefits may disclose '
                                     'protected health information relating to eligibility for or enrollment in the health '
                                     'plan to another agency administering a government program providing public benefits if '
                                     'the sharing of eligibility or enrollment information among such government agencies or '
                                     'the maintenance of such information in a single or combined data system accessible to '
                                     'all such government agencies is required or expressly authorized by statute or '
                                     'regulation.\n'
                                     '\n'
                                     '(ii) A covered entity that is a government agency administering a government program '
                                     'providing public benefits may disclose protected health information relating to the '
                                     'program to another covered entity that is a government agency administering a government '
                                     'program providing public benefits if the programs serve the same or similar populations '
                                     'and the disclosure of protected health information is necessary to coordinate the '
                                     'covered functions of such programs or to improve administration and management relating '
                                     'to the covered functions of such programs.',
          'subchapter': '164.512(k):  Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': '164.512(k)(7): National Instant Criminal Background Check System.',
          'requirement_description': 'A covered entity may use or disclose protected health information for purposes of '
                                     'reporting to the National Instant Criminal Background Check System the identity of an '
                                     'individual who is prohibited from possessing a firearm under 18 U.S.C. 922(g)(4), '
                                     'provided the covered entity:\n'
                                     '\n'
                                     '(i) Is a State agency or other entity that is, or contains an entity that is:\n'
                                     '\n'
                                     '(A) An entity designated by the State to report, or which collects information for '
                                     'purposes of reporting, on behalf of the State, to the National Instant Criminal '
                                     'Background Check System; or\n'
                                     '\n'
                                     '(B) A court, board, commission, or other lawful authority that makes the commitment or '
                                     'adjudication that causes an individual to become subject to 18 U.S.C. 922(g)(4); and\n'
                                     '\n'
                                     '(ii) Discloses the information only to:\n'
                                     '\n'
                                     '(A) The National Instant Criminal Background Check System; or\n'
                                     '\n'
                                     '(B) An entity designated by the State to report, or which collects information for '
                                     'purposes of reporting, on behalf of the State, to the National Instant Criminal '
                                     'Background Check System; and\n'
                                     '\n'
                                     '(iii)\n'
                                     '\n'
                                     '(A) Discloses only the limited demographic and certain other information needed for '
                                     'purposes of reporting to the National Instant Criminal Background Check System; and\n'
                                     '\n'
                                     '(B) Does not disclose diagnostic or clinical information for such purposes.',
          'subchapter': '164.512(k):  Standard: Uses and disclosures for specialized government functions'},
         {'chapter_title': '164.512: Uses and disclosures for which an authorization or opportunity to agree or object is not '
                           'required.',
          'conformity_questions': [],
          'objective_title': "164.512(l)(1): Standard: Disclosures for workers' compensation.",
          'requirement_description': 'A covered entity may disclose protected health information as authorized by and to the '
                                     "extent necessary to comply with laws relating to workers' compensation or other similar "
                                     'programs, established by law, that provide benefits for work-related injuries or illness '
                                     'without regard to fault.',
          'subchapter': "164.512(l):  Standard: Disclosures for workers' compensation.  "},
         {'chapter_title': '164.514: Other requirements relating to uses and disclosures of protected health information.',
          'conformity_questions': ['Q-DCH-21: Does the organization securely dispose of, destroy or erase information?.',
                                   'Q-DCH-09.3: Does the organization facilitate the sanitization of Personal Data (PD)?.',
                                   'Q-CRY-05: Does the organization use cryptographic mechanisms on systems to prevent '
                                   'unauthorized disclosure of data at rest? .'],
          'objective_title': '164.514(a)(1): Standard: De-identification of protected health information.',
          'requirement_description': 'Health information that does not identify an individual and with respect to which there '
                                     'is no reasonable basis to believe that the information can be used to identify an '
                                     'individual is not individually identifiable health information.\n'
                                     '\n'
                                     'Implementation specifications: Requirements for de-identification of protected health '
                                     'information.  A covered entity may determine that health information is not individually '
                                     'identifiable health information only if:\n'
                                     '\n'
                                     '(1) A person with appropriate knowledge of and experience with generally accepted '
                                     'statistical and scientific principles and methods for rendering information not '
                                     'individually identifiable:\n'
                                     '\n'
                                     '(i) Applying such principles and methods, determines that the risk is very small that '
                                     'the information could be used, alone or in combination with other reasonably available '
                                     'information, by an anticipated recipient to identify an individual who is a subject of '
                                     'the information; and\n'
                                     '\n'
                                     '(ii) Documents the methods and results of the analysis that justify such determination; '
                                     'or\n'
                                     '\n'
                                     '(2)\n'
                                     '\n'
                                     '(i) The following identifiers of the individual or of relatives, employers, or household '
                                     'members of the individual, are removed:\n'
                                     '\n'
                                     '(A) Names;\n'
                                     '\n'
                                     '(B) All geographic subdivisions smaller than a State, including street address, city, '
                                     'county, precinct, zip code, and their equivalent geocodes, except for the initial three '
                                     'digits of a zip code if, according to the current publicly available data from the '
                                     'Bureau of the Census:\n'
                                     '\n'
                                     '(1) The geographic unit formed by combining all zip codes with the same three initial '
                                     'digits contains more than 20,000 people; and\n'
                                     '\n'
                                     '(2) The initial three digits of a zip code for all such geographic units containing '
                                     '20,000 or fewer people is changed to 000.\n'
                                     '\n'
                                     '(C) All elements of dates (except year) for dates directly related to an individual, '
                                     'including birth date, admission date, discharge date, date of death; and all ages over '
                                     '89 and all elements of dates (including year) indicative of such age, except that such '
                                     'ages and elements may be aggregated into a single category of age 90 or older;\n'
                                     '\n'
                                     '(D) Telephone numbers;\n'
                                     '\n'
                                     '(E) Fax numbers;\n'
                                     '\n'
                                     '(F) Electronic mail addresses;\n'
                                     '\n'
                                     '(G) Social security numbers;\n'
                                     '\n'
                                     '(H) Medical record numbers;\n'
                                     '\n'
                                     '(I) Health plan beneficiary numbers;\n'
                                     '\n'
                                     '(J) Account numbers;\n'
                                     '\n'
                                     '(K) Certificate/license numbers;\n'
                                     '\n'
                                     '(L) Vehicle identifiers and serial numbers, including license plate numbers;\n'
                                     '\n'
                                     '(M) Device identifiers and serial numbers;\n'
                                     '\n'
                                     '(N) Web Universal Resource Locators (URLs);\n'
                                     '\n'
                                     '(O) Internet Protocol (IP) address numbers;\n'
                                     '\n'
                                     '(P) Biometric identifiers, including finger and voice prints;\n'
                                     '\n'
                                     '(Q) Full face photographic images and any comparable images; and\n'
                                     '\n'
                                     '(R) Any other unique identifying number, characteristic, or code, except as permitted by '
                                     'paragraph (c) of this section; and\n'
                                     '\n'
                                     '(ii) The covered entity does not have actual knowledge that the information could be '
                                     'used alone or in combination with other information to identify an individual who is a '
                                     'subject of the information.\n'
                                     '\n'
                                     '(c) Implementation specifications: Re-identification.  A covered entity may assign a '
                                     'code or other means of record identification to allow information de-identified under '
                                     'this section to be re-identified by the covered entity, provided that:\n'
                                     '\n'
                                     '(1) Derivation.  The code or other means of record identification is not derived from or '
                                     'related to information about the individual and is not otherwise capable of being '
                                     'translated so as to identify the individual; and\n'
                                     '\n'
                                     '(2) Security.  The covered entity does not use or disclose the code or other means of '
                                     'record identification for any other purpose, and does not disclose the mechanism for '
                                     're-identification.',
          'subchapter': '164.514(a):  Standard: De-identification of protected health information.'},
         {'chapter_title': '164.514: Other requirements relating to uses and disclosures of protected health information.',
          'conformity_questions': [],
          'objective_title': '164.514(d)(1): Standard: minimum necessary requirements.',
          'requirement_description': 'In order to comply with  164.502(b) and this section, a covered entity must meet the '
                                     'requirements of paragraphs (d)(2) through (d)(5) of this section with respect to a '
                                     'request for, or the use and disclosure of, protected health information.\n'
                                     '\n'
                                     '(2) Implementation specifications: Minimum necessary uses of protected health '
                                     'information.\n'
                                     '\n'
                                     '(i) A covered entity must identify:\n'
                                     '\n'
                                     '(A) Those persons or classes of persons, as appropriate, in its workforce who need '
                                     'access to protected health information to carry out their duties; and\n'
                                     '\n'
                                     '(B) For each such person or class of persons, the category or categories of protected '
                                     'health information to which access is needed and any conditions appropriate to such '
                                     'access.\n'
                                     '\n'
                                     '(ii) A covered entity must make reasonable efforts to limit the access of such persons '
                                     'or classes identified in paragraph (d)(2)(i)(A) of this section to protected health '
                                     'information consistent with paragraph (d)(2)(i)(B) of this section.\n'
                                     '\n'
                                     '(3) Implementation specification: Minimum necessary disclosures of protected health '
                                     'information.\n'
                                     '\n'
                                     '(i) For any type of disclosure that it makes on a routine and recurring basis, a covered '
                                     'entity must implement policies and procedures (which may be standard protocols) that '
                                     'limit the protected health information disclosed to the amount reasonably necessary to '
                                     'achieve the purpose of the disclosure.\n'
                                     '\n'
                                     '(ii) For all other disclosures, a covered entity must:\n'
                                     '\n'
                                     '(A) Develop criteria designed to limit the protected health information disclosed to the '
                                     'information reasonably necessary to accomplish the purpose for which disclosure is '
                                     'sought; and\n'
                                     '\n'
                                     '(B) Review requests for disclosure on an individual basis in accordance with such '
                                     'criteria.\n'
                                     '\n'
                                     '(iii) A covered entity may rely, if such reliance is reasonable under the circumstances, '
                                     'on a requested disclosure as the minimum necessary for the stated purpose when:\n'
                                     '\n'
                                     '(A) Making disclosures to public officials that are permitted under  164.512, if the '
                                     'public official represents that the information requested is the minimum necessary for '
                                     'the stated purpose(s);\n'
                                     '\n'
                                     '(B) The information is requested by another covered entity;\n'
                                     '\n'
                                     '(C) The information is requested by a professional who is a member of its workforce or '
                                     'is a business associate of the covered entity for the purpose of providing professional '
                                     'services to the covered entity, if the professional represents that the information '
                                     'requested is the minimum necessary for the stated purpose(s); or\n'
                                     '\n'
                                     '(D) Documentation or representations that comply with the applicable requirements of  '
                                     '164.512(i) have been provided by a person requesting the information for research '
                                     'purposes.\n'
                                     '\n'
                                     '(4) Implementation specifications: Minimum necessary requests for protected health '
                                     'information.\n'
                                     '\n'
                                     '(i) A covered entity must limit any request for protected health information to that '
                                     'which is reasonably necessary to accomplish the purpose for which the request is made, '
                                     'when requesting such information from other covered entities.\n'
                                     '\n'
                                     '(ii) For a request that is made on a routine and recurring basis, a covered entity must '
                                     'implement policies and procedures (which may be standard protocols) that limit the '
                                     'protected health information requested to the amount reasonably necessary to accomplish '
                                     'the purpose for which the request is made.\n'
                                     '\n'
                                     '(iii) For all other requests, a covered entity must:\n'
                                     '\n'
                                     '(A) Develop criteria designed to limit the request for protected health information to '
                                     'the information reasonably necessary to accomplish the purpose for which the request is '
                                     'made; and\n'
                                     '\n'
                                     '(B) Review requests for disclosure on an individual basis in accordance with such '
                                     'criteria.\n'
                                     '\n'
                                     '(5) Implementation specification: Other content requirement.  For all uses, disclosures, '
                                     'or requests to which the requirements in paragraph (d) of this section apply, a covered '
                                     'entity may not use, disclose or request an entire medical record, except when the entire '
                                     'medical record is specifically justified as the amount that is reasonably necessary to '
                                     'accomplish the purpose of the use, disclosure, or request.',
          'subchapter': '164.514(d):   Standard: minimum necessary requirements. '},
         {'chapter_title': '164.514: Other requirements relating to uses and disclosures of protected health information.',
          'conformity_questions': ['Q-MDM-08: Does the organization limit data retention on mobile devices to the smallest '
                                   'usable dataset and timeframe?.'],
          'objective_title': '164.514(e)(1): Standard: Limited data set.',
          'requirement_description': 'A covered entity may use or disclose a limited data set that meets the requirements of '
                                     'paragraphs (e)(2) and (e)(3) of this section, if the covered entity enters into a data '
                                     'use agreement with the limited data set recipient, in accordance with paragraph (e)(4) '
                                     'of this section.\n'
                                     '\n'
                                     '(2) Implementation specification: Limited data set:  A limited data set is protected '
                                     'health information that excludes the following direct identifiers of the individual or '
                                     'of relatives, employers, or household members of the individual:\n'
                                     '\n'
                                     '(i) Names;\n'
                                     '\n'
                                     '(ii) Postal address information, other than town or city, State, and zip code;\n'
                                     '\n'
                                     '(iii) Telephone numbers;\n'
                                     '\n'
                                     '(iv) Fax numbers;\n'
                                     '\n'
                                     '(v) Electronic mail addresses;\n'
                                     '\n'
                                     '(vi) Social security numbers;\n'
                                     '\n'
                                     '(vii) Medical record numbers;\n'
                                     '\n'
                                     '(viii) Health plan beneficiary numbers;\n'
                                     '\n'
                                     '(ix) Account numbers;\n'
                                     '\n'
                                     '(x) Certificate/license numbers;\n'
                                     '\n'
                                     '(xi) Vehicle identifiers and serial numbers, including license plate numbers;\n'
                                     '\n'
                                     '(xii) Device identifiers and serial numbers;\n'
                                     '\n'
                                     '(xiii) Web Universal Resource Locators (URLs);\n'
                                     '\n'
                                     '(xiv) Internet Protocol (IP) address numbers;\n'
                                     '\n'
                                     '(xv) Biometric identifiers, including finger and voice prints; and\n'
                                     '\n'
                                     '(xvi) Full face photographic images and any comparable images.\n'
                                     '\n'
                                     '(3) Implementation specification: Permitted purposes for uses and disclosures.\n'
                                     '\n'
                                     '(i) A covered entity may use or disclose a limited data set under paragraph (e)(1) of '
                                     'this section only for the purposes of research, public health, or health care '
                                     'operations.\n'
                                     '\n'
                                     '(ii) A covered entity may use protected health information to create a limited data set '
                                     'that meets the requirements of paragraph (e)(2) of this section, or disclose protected '
                                     'health information only to a business associate for such purpose, whether or not the '
                                     'limited data set is to be used by the covered entity.\n'
                                     '\n'
                                     '(4) Implementation specifications: Data use agreement -\n'
                                     '\n'
                                     '(i) Agreement required.  A covered entity may use or disclose a limited data set under '
                                     'paragraph (e)(1) of this section only if the covered entity obtains satisfactory '
                                     'assurance, in the form of a data use agreement that meets the requirements of this '
                                     'section, that the limited data set recipient will only use or disclose the protected '
                                     'health information for limited purposes.\n'
                                     '\n'
                                     '(ii) Contents.  A data use agreement between the covered entity and the limited data set '
                                     'recipient must:\n'
                                     '\n'
                                     '(A) Establish the permitted uses and disclosures of such information by the limited data '
                                     'set recipient, consistent with paragraph (e)(3) of this section. The data use agreement '
                                     'may not authorize the limited data set recipient to use or further disclose the '
                                     'information in a manner that would violate the requirements of this subpart, if done by '
                                     'the covered entity;\n'
                                     '\n'
                                     '(B) Establish who is permitted to use or receive the limited data set; and\n'
                                     '\n'
                                     '(C) Provide that the limited data set recipient will:\n'
                                     '\n'
                                     '(1) Not use or further disclose the information other than as permitted by the data use '
                                     'agreement or as otherwise required by law;\n'
                                     '\n'
                                     '(2) Use appropriate safeguards to prevent use or disclosure of the information other '
                                     'than as provided for by the data use agreement;\n'
                                     '\n'
                                     '(3) Report to the covered entity any use or disclosure of the information not provided '
                                     'for by its data use agreement of which it becomes aware;\n'
                                     '\n'
                                     '(4) Ensure that any agents to whom it provides the limited data set agree to the same '
                                     'restrictions and conditions that apply to the limited data set recipient with respect to '
                                     'such information; and\n'
                                     '\n'
                                     '(5) Not identify the information or contact the individuals.\n'
                                     '\n'
                                     '(iii) Compliance.\n'
                                     '\n'
                                     '(A) A covered entity is not in compliance with the standards in paragraph (e) of this '
                                     'section if the covered entity knew of a pattern of activity or practice of the limited '
                                     'data set recipient that constituted a material breach or violation of the data use '
                                     'agreement, unless the covered entity took reasonable steps to cure the breach or end the '
                                     'violation, as applicable, and, if such steps were unsuccessful:\n'
                                     '\n'
                                     '(1) Discontinued disclosure of protected health information to the recipient; and\n'
                                     '\n'
                                     '(2) Reported the problem to the Secretary.\n'
                                     '\n'
                                     '(B) A covered entity that is a limited data set recipient and violates a data use '
                                     'agreement will be in noncompliance with the standards, implementation specifications, '
                                     'and requirements of paragraph (e) of this section.',
          'subchapter': '164.514(e):  Standard: Limited data set.'},
         {'chapter_title': '164.514: Other requirements relating to uses and disclosures of protected health information.',
          'conformity_questions': [],
          'objective_title': '164.514(f)(1): Standard: Uses and disclosures for fundraising.',
          'requirement_description': 'Subject to the conditions of paragraph (f)(2) of this section, a covered entity may use, '
                                     'or disclose to a business associate or to an institutionally related foundation, the '
                                     'following protected health information for the purpose of raising funds for its own '
                                     'benefit, without an authorization meeting the requirements of  164.508:\n'
                                     '\n'
                                     '(i) Demographic information relating to an individual, including name, address, other '
                                     'contact information, age, gender, and date of birth;\n'
                                     '\n'
                                     '(ii) Dates of health care provided to an individual;\n'
                                     '\n'
                                     '(iii) Department of service information;\n'
                                     '\n'
                                     '(iv) Treating physician;\n'
                                     '\n'
                                     '(v) Outcome information; and\n'
                                     '\n'
                                     '(vi) Health insurance status.\n'
                                     '\n'
                                     '(2) Implementation specifications: Fundraising requirements.\n'
                                     '\n'
                                     '(i) A covered entity may not use or disclose protected health information for '
                                     'fundraising purposes as otherwise permitted by paragraph (f)(1) of this section unless a '
                                     "statement required by  164.520(b)(1)(iii)(A) is included in the covered entity's notice "
                                     'of privacy practices.\n'
                                     '\n'
                                     '(ii) With each fundraising communication made to an individual under this paragraph, a '
                                     'covered entity must provide the individual with a clear and conspicuous opportunity to '
                                     'elect not to receive any further fundraising communications. The method for an '
                                     'individual to elect not to receive further fundraising communications may not cause the '
                                     'individual to incur an undue burden or more than a nominal cost.\n'
                                     '\n'
                                     "(iii) A covered entity may not condition treatment or payment on the individual's choice "
                                     'with respect to the receipt of fundraising communications.\n'
                                     '\n'
                                     '(iv) A covered entity may not make fundraising communications to an individual under '
                                     'this paragraph where the individual has elected not to receive such communications under '
                                     'paragraph (f)(2)(ii) of this section.\n'
                                     '\n'
                                     '(v) A covered entity may provide an individual who has elected not to receive further '
                                     'fundraising communications with a method to opt back in to receive such communications.',
          'subchapter': '164.514(f):  Fundraising communications'},
         {'chapter_title': '164.514: Other requirements relating to uses and disclosures of protected health information.',
          'conformity_questions': [],
          'objective_title': '164.514(g)(1): Standard: Uses and disclosures for underwriting and related purposes.',
          'requirement_description': 'If a health plan receives protected health information for the purpose of underwriting, '
                                     'premium rating, or other activities relating to the creation, renewal, or replacement of '
                                     'a contract of health insurance or health benefits, and if such health insurance or '
                                     'health benefits are not placed with the health plan, such health plan may only use or '
                                     'disclose such protected health information for such purpose or as may be required by '
                                     'law, subject to the prohibition at  164.502(a)(5)(i) with respect to genetic information '
                                     'included in the protected health information.',
          'subchapter': '164.514(g):  Standard: Uses and disclosures for underwriting and related purposes.'},
         {'chapter_title': '164.514: Other requirements relating to uses and disclosures of protected health information.',
          'conformity_questions': ['Q-AST-15: Does the organization verify logical configuration settings and the physical '
                                   'integrity of critical technology assets throughout their lifecycle?.',
                                   'Q-BCD-13.1: Does the organization verify the integrity of backups and other restoration '
                                   'assets prior to using them for restoration?.',
                                   'Q-AST-18: Does the organization provision and protect the confidentiality, integrity and '
                                   'authenticity of product supplier keys and data that can be used as a roots of trust basis '
                                   'for integrity verification?.'],
          'objective_title': '164.514(h)(1): Standard: Verification requirements.',
          'requirement_description': 'Prior to any disclosure permitted by this subpart, a covered entity must:\n'
                                     '\n'
                                     '(i) Except with respect to disclosures under  164.510, verify the identity of a person '
                                     'requesting protected health information and the authority of any such person to have '
                                     'access to protected health information under this subpart, if the identity or any such '
                                     'authority of such person is not known to the covered entity; and\n'
                                     '\n'
                                     '(ii) Obtain any documentation, statements, or representations, whether oral or written, '
                                     'from the person requesting the protected health information when such documentation, '
                                     'statement, or representation is a condition of the disclosure under this subpart.\n'
                                     '\n'
                                     '(2) Implementation specifications: Verification -\n'
                                     '\n'
                                     '(i) Conditions on disclosures.  If a disclosure is conditioned by this subpart on '
                                     'particular documentation, statements, or representations from the person requesting the '
                                     'protected health information, a covered entity may rely, if such reliance is reasonable '
                                     'under the circumstances, on documentation, statements, or representations that, on their '
                                     'face, meet the applicable requirements.\n'
                                     '\n'
                                     '(A) The conditions in  164.512(f)(1)(ii)(C) may be satisfied by the administrative '
                                     'subpoena or similar process or by a separate written statement that, on its face, '
                                     'demonstrates that the applicable requirements have been met.\n'
                                     '\n'
                                     '(B) The documentation required by  164.512(i)(2) may be satisfied by one or more written '
                                     'statements, provided that each is appropriately dated and signed in accordance with  '
                                     '164.512(i)(2)(i) and (v).\n'
                                     '\n'
                                     '(ii) Identity of public officials.  A covered entity may rely, if such reliance is '
                                     'reasonable under the circumstances, on any of the following to verify identity when the '
                                     'disclosure of protected health information is to a public official or a person acting on '
                                     'behalf of the public official:\n'
                                     '\n'
                                     '(A) If the request is made in person, presentation of an agency identification badge, '
                                     'other official credentials, or other proof of government status;\n'
                                     '\n'
                                     '(B) If the request is in writing, the request is on the appropriate government '
                                     'letterhead; or\n'
                                     '\n'
                                     '(C) If the disclosure is to a person acting on behalf of a public official, a written '
                                     'statement on appropriate government letterhead that the person is acting under the '
                                     "government's authority or other evidence or documentation of agency, such as a contract "
                                     'for services, memorandum of understanding, or purchase order, that establishes that the '
                                     'person is acting on behalf of the public official.\n'
                                     '\n'
                                     '(iii) Authority of public officials.  A covered entity may rely, if such reliance is '
                                     'reasonable under the circumstances, on any of the following to verify authority when the '
                                     'disclosure of protected health information is to a public official or a person acting on '
                                     'behalf of the public official:\n'
                                     '\n'
                                     '(A) A written statement of the legal authority under which the information is requested, '
                                     'or, if a written statement would be impracticable, an oral statement of such legal '
                                     'authority;\n'
                                     '\n'
                                     '(B) If a request is made pursuant to legal process, warrant, subpoena, order, or other '
                                     'legal process issued by a grand jury or a judicial or administrative tribunal is '
                                     'presumed to constitute legal authority.\n'
                                     '\n'
                                     '(iv) Exercise of professional judgment.  The verification requirements of this paragraph '
                                     'are met if the covered entity relies on the exercise of professional judgment in making '
                                     'a use or disclosure in accordance with  164.510 or acts on a good faith belief in making '
                                     'a disclosure in accordance with 164.512(j).',
          'subchapter': '164.514(h):   Standard: Verification requirements.'},
         {'chapter_title': '164.520: Notice of privacy practices for protected health information.',
          'conformity_questions': [],
          'objective_title': '164.520(a)(1): Right to notice.',
          'requirement_description': 'Except as provided by paragraph (a)(2) or (3) of this section, an individual has a right '
                                     'to adequate notice of the uses and disclosures of protected health information that may '
                                     "be made by the covered entity, and of the individual's rights and the covered entity's "
                                     'legal duties with respect to protected health information.\n'
                                     '\n'
                                     '(2) Exception for group health plans.\n'
                                     '\n'
                                     '(i) An individual enrolled in a group health plan has a right to notice:\n'
                                     '\n'
                                     '(A) From the group health plan, if, and to the extent that, such an individual does not '
                                     'receive health benefits under the group health plan through an insurance contract with a '
                                     'health insurance issuer or HMO; or\n'
                                     '\n'
                                     '(B) From the health insurance issuer or HMO with respect to the group health plan '
                                     'through which such individuals receive their health benefits under the group health '
                                     'plan.\n'
                                     '\n'
                                     '(ii) A group health plan that provides health benefits solely through an insurance '
                                     'contract with a health insurance issuer or HMO, and that creates or receives protected '
                                     'health information in addition to summary health information as defined in  164.504(a) '
                                     'or information on whether the individual is participating in the group health plan, or '
                                     'is enrolled in or has disenrolled from a health insurance issuer or HMO offered by the '
                                     'plan, must:\n'
                                     '\n'
                                     '(A) Maintain a notice under this section; and\n'
                                     '\n'
                                     '(B) Provide such notice upon request to any person. The provisions of paragraph (c)(1) '
                                     'of this section do not apply to such group health plan.\n'
                                     '\n'
                                     '(iii) A group health plan that provides health benefits solely through an insurance '
                                     'contract with a health insurance issuer or HMO, and does not create or receive protected '
                                     'health information other than summary health information as defined in  164.504(a) or '
                                     'information on whether an individual is participating in the group health plan, or is '
                                     'enrolled in or has disenrolled from a health insurance issuer or HMO offered by the '
                                     'plan, is not required to maintain or provide a notice under this section.\n'
                                     '\n'
                                     '(3) Exception for inmates.  An inmate does not have a right to notice under this '
                                     'section, and the requirements of this section do not apply to a correctional institution '
                                     'that is a covered entity.\n'
                                     '\n'
                                     '(b) Implementation specifications: Content of notice -\n'
                                     '\n'
                                     '(1) Required elements.  The covered entity must provide a notice that is written in '
                                     'plain language and that contains the elements required by this paragraph.\n'
                                     '\n'
                                     '(i) Header.  The notice must contain the following statement as a header or otherwise '
                                     'prominently displayed: \n'
                                     '\n'
                                     'THIS NOTICE DESCRIBES HOW MEDICAL INFORMATION ABOUT YOU MAY BE USED AND DISCLOSED AND '
                                     'HOW YOU CAN GET ACCESS TO THIS INFORMATION. PLEASE REVIEW IT CAREFULLY."\n'
                                     '\n'
                                     '(ii) Uses and disclosures.  The notice must contain:\n'
                                     '\n'
                                     '(A) A description',
          'subchapter': '164.520(a):  Standard: Notice of privacy practices'},
         {'chapter_title': '164.522: Rights to request privacy protection for protected health information.',
          'conformity_questions': ['Q-CFG-08: Does the organization configure systems, applications and processes to restrict '
                                   'access to sensitive/regulated data?.',
                                   'Q-AST-12: Does the organization restrict the possession and usage of personally-owned '
                                   'technology devices within organization-controlled facilities?.',
                                   'Q-CHG-04.5: Does the organization restrict software library privileges to those '
                                   'individuals with a pertinent business need for access? .'],
          'objective_title': '164.522(a)(1): Standard: Right of an individual to request restriction of uses and disclosures.',
          'requirement_description': '(i) A covered entity must permit an individual to request that the covered entity '
                                     'restrict:\n'
                                     '\n'
                                     '(A) Uses or disclosures of protected health information about the individual to carry '
                                     'out treatment, payment, or health care operations; and\n'
                                     '\n'
                                     '(B) Disclosures permitted under  164.510(b).\n'
                                     '\n'
                                     '(ii) Except as provided in paragraph (a)(1)(vi) of this section, a covered entity is not '
                                     'required to agree to a restriction.\n'
                                     '\n'
                                     '(iii) A covered entity that agrees to a restriction under paragraph (a)(1)(i) of this '
                                     'section may not use or disclose protected health information in violation of such '
                                     'restriction, except that, if the individual who requested the restriction is in need of '
                                     'emergency treatment and the restricted protected health information is needed to provide '
                                     'the emergency treatment, the covered entity may use the restricted protected health '
                                     'information, or may disclose such information to a health care provider, to provide such '
                                     'treatment to the individual.\n'
                                     '\n'
                                     '(iv) If restricted protected health information is disclosed to a health care provider '
                                     'for emergency treatment under paragraph (a)(1)(iii) of this section, the covered entity '
                                     'must request that such health care provider not further use or disclose the '
                                     'information.\n'
                                     '\n'
                                     '(v) A restriction agreed to by a covered entity under paragraph (a) of this section, is '
                                     'not effective under this subpart to prevent uses or disclosures permitted or required '
                                     'under  164.502(a)(2)(ii),  164.510(a) or  164.512.\n'
                                     '\n'
                                     '(vi) A covered entity must agree to the request of an individual to restrict disclosure '
                                     'of protected health information about the individual to a health plan if:\n'
                                     '\n'
                                     '(A) The disclosure is for the purpose of carrying out payment or health care operations '
                                     'and is not otherwise required by law; and\n'
                                     '\n'
                                     '(B) The protected health information pertains solely to a health care item or service '
                                     'for which the individual, or person other than the health plan on behalf of the '
                                     'individual, has paid the covered entity in full.\n'
                                     '\n'
                                     '(2) Implementation specifications: Terminating a restriction.  A covered entity may '
                                     'terminate a restriction, if:\n'
                                     '\n'
                                     '(i) The individual agrees to or requests the termination in writing;\n'
                                     '\n'
                                     '(ii) The individual orally agrees to the termination and the oral agreement is '
                                     'documented; or\n'
                                     '\n'
                                     '(iii) The covered entity informs the individual that it is terminating its agreement to '
                                     'a restriction, except that such termination is:\n'
                                     '\n'
                                     '(A) Not effective for protected health information restricted under paragraph (a)(1)(vi) '
                                     'of this section; and\n'
                                     '\n'
                                     '(B) Only effective with respect to protected health information created or received '
                                     'after it has so informed the individual.\n'
                                     '\n'
                                     '(3) Implementation specification: Documentation.  A covered entity must document a '
                                     'restriction in accordance with  160.530(j) of this subchapter.',
          'subchapter': '164.522(a):  Standard: Right of an individual to request restriction of uses and disclosures.'},
         {'chapter_title': '164.522: Rights to request privacy protection for protected health information.',
          'conformity_questions': ['Q-CRY-01.3: Does the organization ensure the confidentiality and integrity of information '
                                   'during preparation for transmission and during reception with cryptographic mechanisms?.',
                                   'Q-AST-19: Does the organization establish usage restrictions and implementation guidance '
                                   'for telecommunication equipment based on the potential to cause damage, if used '
                                   'maliciously?.',
                                   'Q-CRY-01.4: Does the organization conceal or randomize communication patterns with '
                                   'cryptographic mechanisms?.'],
          'objective_title': '164.522(b)(1): Standard: Confidential communications requirements.',
          'requirement_description': '(i) A covered health care provider must permit individuals to request and must '
                                     'accommodate reasonable requests by individuals to receive communications of protected '
                                     'health information from the covered health care provider by alternative means or at '
                                     'alternative locations.\n'
                                     '\n'
                                     '(ii) A health plan must permit individuals to request and must accommodate reasonable '
                                     'requests by individuals to receive communications of protected health information from '
                                     'the health plan by alternative means or at alternative locations, if the individual '
                                     'clearly states that the disclosure of all or part of that information could endanger the '
                                     'individual.\n'
                                     '\n'
                                     '(2) Implementation specifications: Conditions on providing confidential communications.\n'
                                     '\n'
                                     '(i) A covered entity may require the individual to make a request for a confidential '
                                     'communication described in paragraph (b)(1) of this section in writing.\n'
                                     '\n'
                                     '(ii) A covered entity may condition the provision of a reasonable accommodation on:\n'
                                     '\n'
                                     '(A) When appropriate, information as to how payment, if any, will be handled; and\n'
                                     '\n'
                                     '(B) Specification of an alternative address or other method of contact.\n'
                                     '\n'
                                     '(iii) A covered health care provider may not require an explanation from the individual '
                                     'as to the basis for the request as a condition of providing communications on a '
                                     'confidential basis.\n'
                                     '\n'
                                     '(iv) A health plan may require that a request contain a statement that disclosure of all '
                                     'or part of the information to which the request pertains could endanger the individual.',
          'subchapter': '164.522(b):  Standard: Confidential communications requirements.'},
         {'chapter_title': '164.524: Access of individuals to protected health information.',
          'conformity_questions': ['Q-PES-02.1: Does the organization authorize physical access to facilities based on the '
                                   'position or role of the individual?.',
                                   'Q-PES-04.1: Does the organization allow only authorized personnel access to secure areas? '
                                   '.',
                                   'Q-PES-03.1: Does the organization limit and monitor physical access through controlled '
                                   'ingress and egress points?.'],
          'objective_title': '164.524(a)(1): Right of access.',
          'requirement_description': 'Except as otherwise provided in paragraph (a)(2) or (a)(3) of this section, an '
                                     'individual has a right of access to inspect and obtain a copy of protected health '
                                     'information about the individual in a designated record set, for as long as the '
                                     'protected health information is maintained in the designated record set, except for:\n'
                                     '\n'
                                     '(i) Psychotherapy notes; and\n'
                                     '\n'
                                     '(ii) Information compiled in reasonable anticipation of, or for use in, a civil, '
                                     'criminal, or administrative action or proceeding.\n'
                                     '\n'
                                     'Except as otherwise provided in paragraph (a)(2) or (a)(3) of this section, an '
                                     'individual has a right of access to inspect and obtain a copy of protected health '
                                     'information about the individual in a designated record set, for as long as the '
                                     'protected health information is maintained in the designated record set, except for:\n'
                                     '\n'
                                     '(i) Psychotherapy notes; and\n'
                                     '\n'
                                     '(ii) Information compiled in reasonable anticipation of, or for use in, a civil, '
                                     'criminal, or administrative action or proceeding.\n'
                                     '\n'
                                     '(2) Unreviewable grounds for denial.  A covered entity may deny an individual access '
                                     'without providing the individual an opportunity for review, in the following '
                                     'circumstances.\n'
                                     '\n'
                                     '(i) The protected health information is excepted from the right of access by paragraph '
                                     '(a)(1) of this section.\n'
                                     '\n'
                                     '(ii) A covered entity that is a correctional institution or a covered health care '
                                     'provider acting under the direction of the correctional institution may deny, in whole '
                                     "or in part, an inmate's request to obtain a copy of protected health information, if "
                                     'obtaining such copy would jeopardize the health, safety, security, custody, or '
                                     'rehabilitation of the individual or of other inmates, or the safety of any officer, '
                                     'employee, or other person at the correctional institution or responsible for the '
                                     'transporting of the inmate.\n'
                                     '\n'
                                     "(iii) An individual's access to protected health information created or obtained by a "
                                     'covered health care provider in the course of research that includes treatment may be '
                                     'temporarily suspended for as long as the research is in progress, provided that the '
                                     'individual has agreed to the denial of access when consenting to participate in the '
                                     'research that includes treatment, and the covered health care provider has informed the '
                                     'individual that the right of access will be reinstated upon completion of the research.\n'
                                     '\n'
                                     "(iv) An individual's access to protected health information that is contained in records "
                                     'that are subject to the Privacy Act, 5 U.S.C. 552a, may be denied, if the denial of '
                                     'access under the Privacy Act would meet the requirements of that law.\n'
                                     '\n'
                                     "(v) An individual's access may be denied if the protected health information was "
                                     'obtained from someone other than a health care provider under a promise of '
                                     'confidentiality and the access requested would be reasonably likely to reveal the source '
                                     'of the information.\n'
                                     '\n'
                                     '(3) Reviewable grounds for denial.  A covered entity may deny an individual access, '
                                     'provided that the individual is given a right to have such denials reviewed, as required '
                                     'by paragraph (a)(4) of this section, in the following circumstances:\n'
                                     '\n'
                                     '(i) A licensed health care professional has determined, in the exercise of professional '
                                     'judgment, that the access requested is reasonably likely to endanger the life or '
                                     'physical safety of the individual or another person;\n'
                                     '\n'
                                     '(ii) The protected health information makes reference to another person (unless such '
                                     'other person is a health care provider) and a licensed health care professional has '
                                     'determined, in the exercise of professional judgment, that the access requested is '
                                     'reasonably likely to cause substantial harm to such other person; or\n'
                                     '\n'
                                     "(iii) The request for access is made by the individual's personal representative and a "
                                     'licensed health care professional has determined, in the exercise of professional '
                                     'judgment, that the provision of access to such personal representative is reasonably '
                                     'likely to cause substantial harm to the individual or another person.\n'
                                     '\n'
                                     '(4) Review of a denial of access.  If access is denied on a ground permitted under '
                                     'paragraph (a)(3) of this section, the individual has the right to have the denial '
                                     'reviewed by a licensed health care professional who is designated by the covered entity '
                                     'to act as a reviewing official and who did not participate in the original decision to '
                                     'deny. The covered entity must provide or deny access in accordance with the '
                                     'determination of the reviewing official under paragraph (d)(4) of this section.\n'
                                     '\n'
                                     '(b) Implementation specifications: Requests for access and timely action -\n'
                                     '\n'
                                     "(1) Individual's request for access.  The covered entity must permit an individual to "
                                     'request access to inspect or to obtain a copy of the protected health information about '
                                     'the individual that is maintained in a designated record set. The covered entity may '
                                     'require individuals to make requests for access in writing, provided that it informs '
                                     'individuals of such a requirement.\n'
                                     '\n'
                                     '(2) Timely action by the covered entity.\n'
                                     '\n'
                                     '(i) Except as provided in paragraph (b)(2)(ii) of this section, the covered entity must '
                                     'act on a request for access no later than 30 days after receipt of the request as '
                                     'follows.\n'
                                     '\n'
                                     '(A) If the covered entity grants the request, in whole or in part, it must inform the '
                                     'individual of the acceptance of the request and provide the access requested, in '
                                     'accordance with paragraph (c) of this section.\n'
                                     '\n'
                                     '(B) If the covered entity denies the request, in whole or in part, it must provide the '
                                     'individual with a written denial, in accordance with paragraph (d) of this section.\n'
                                     '\n'
                                     '(ii) If the covered entity is unable to take an action required by paragraph '
                                     '(b)(2)(i)(A) or (B) of this section within the time required by paragraph (b)(2)(i) of '
                                     'this section, as applicable, the covered entity may extend the time for such actions by '
                                     'no more than 30 days, provided that:\n'
                                     '\n'
                                     '(A) The covered entity, within the time limit set by paragraph (b)(2)(i) of this '
                                     'section, as applicable, provides the individual with a written statement of the reasons '
                                     'for the delay and the date by which the covered entity will complete its action on the '
                                     'request; and\n'
                                     '\n'
                                     '(B) The covered entity may have only one such extension of time for action on a request '
                                     'for access.\n'
                                     '\n'
                                     '(c) Implementation specifications: Provision of access.  If the covered entity provides '
                                     'an individual with access, in whole or in part, to protected health information, the '
                                     'covered entity must comply with the following requirements.\n'
                                     '\n'
                                     '(1) Providing the access requested.  The covered entity must provide the access '
                                     'requested by individuals, including inspection or obtaining a copy, or both, of the '
                                     'protected health information about them in designated record sets. If the same protected '
                                     'health information that is the subject of a request for access is maintained in more '
                                     'than one designated record set or at more than one location, the covered entity need '
                                     'only produce the protected health information once in response to a request for access.\n'
                                     '\n'
                                     '(2) Form of access requested.\n'
                                     '\n'
                                     '(i) The covered entity must provide the individual with access to the protected health '
                                     'information in the form and format requested by the individual, if it is readily '
                                     'producible in such form and format; or, if not, in a readable hard copy form or such '
                                     'other form and format as agreed to by the covered entity and the individual.\n'
                                     '\n'
                                     '(ii) Notwithstanding paragraph (c)(2)(i) of this section, if the protected health '
                                     'information that is the subject of a request for access is maintained in one or more '
                                     'designated record sets electronically and if the individual requests an electronic copy '
                                     'of such information, the covered entity must provide the individual with access to the '
                                     'protected health information in the electronic form and format requested by the '
                                     'individual, if it is readily producible in such form and format; or, if not, in a '
                                     'readable electronic form and format as agreed to by the covered entity and the '
                                     'individual.\n'
                                     '\n'
                                     '(iii) The covered entity may provide the individual with a summary of the protected '
                                     'health information requested, in lieu of providing access to the protected health '
                                     'information or may provide an explanation of the protected health information to which '
                                     'access has been provided, if:\n'
                                     '\n'
                                     '(A) The individual agrees in advance to such a summary or explanation; and\n'
                                     '\n'
                                     '(B) The individual agrees in advance to the fees imposed, if any, by the covered entity '
                                     'for such summary or explanation.\n'
                                     '\n'
                                     '(3) Time and manner of access.\n'
                                     '\n'
                                     '(i) The covered entity must provide the access as requested by the individual in a '
                                     'timely manner as required by paragraph (b)(2) of this section, including arranging with '
                                     'the individual for a convenient time and place to inspect or obtain a copy of the '
                                     'protected health information, or mailing the copy of the protected health information at '
                                     "the individual's request. The covered entity may discuss the scope, format, and other "
                                     'aspects of the request for access with the individual as necessary to facilitate the '
                                     'timely provision of access.\n'
                                     '\n'
                                     "(ii) If an individual's request for access directs the covered entity to transmit the "
                                     'copy of protected health information directly to another person designated by the '
                                     'individual, the covered entity must provide the copy to the person designated by the '
                                     "individual. The individual's request must be in writing, signed by the individual, and "
                                     'clearly identify the designated person and where to send the copy of protected health '
                                     'information.\n'
                                     '\n'
                                     '(4) Fees.  If the individual requests a copy of the protected health information or '
                                     'agrees to a summary or explanation of such information, the covered entity may impose a '
                                     'reasonable, cost-based fee, provided that the fee includes only the cost of:\n'
                                     '\n'
                                     '(i) Labor for copying the protected health information requested by the individual, '
                                     'whether in paper or electronic form;\n'
                                     '\n'
                                     '(ii) Supplies for creating the paper copy or electronic media if the individual requests '
                                     'that the electronic copy be provided on portable media;\n'
                                     '\n'
                                     '(iii) Postage, when the individual has requested the copy, or the summary or '
                                     'explanation, be mailed; and\n'
                                     '\n'
                                     '(iv) Preparing an explanation or summary of the protected health information, if agreed '
                                     'to by the individual as required by paragraph (c)(2)(iii) of this section.\n'
                                     '\n'
                                     '(d) Implementation specifications: Denial of access.  If the covered entity denies '
                                     'access, in whole or in part, to protected health information, the covered entity must '
                                     'comply with the following requirements.\n'
                                     '\n'
                                     '(1) Making other information accessible.  The covered entity must, to the extent '
                                     'possible, give the individual access to any other protected health information '
                                     'requested, after excluding the protected health information as to which the covered '
                                     'entity has a ground to deny access.\n'
                                     '\n'
                                     '(2) Denial.  The covered entity must provide a timely, written denial to the individual, '
                                     'in accordance with paragraph (b)(2) of this section. The denial must be in plain '
                                     'language and contain:\n'
                                     '\n'
                                     '(i) The basis for the denial;\n'
                                     '\n'
                                     "(ii) If applicable, a statement of the individual's review rights under paragraph (a)(4) "
                                     'of this section, including a description of how the individual may exercise such review '
                                     'rights; and\n'
                                     '\n'
                                     '(iii) A description of how the individual may complain to the covered entity pursuant to '
                                     'the complaint procedures in  164.530(d) or to the Secretary pursuant to the procedures '
                                     'in  160.306. The description must include the name, or title, and telephone number of '
                                     'the contact person or office designated in  164.530(a)(1)(ii).\n'
                                     '\n'
                                     '(3) Other responsibility.  If the covered entity does not maintain the protected health '
                                     "information that is the subject of the individual's request for access, and the covered "
                                     'entity knows where the requested information is maintained, the covered entity must '
                                     'inform the individual where to direct the request for access.\n'
                                     '\n'
                                     '(4) Review of denial requested.  If the individual has requested a review of a denial '
                                     'under paragraph (a)(4) of this section, the covered entity must designate a licensed '
                                     'health care professional, who was not directly involved in the denial to review the '
                                     'decision to deny access. The covered entity must promptly refer a request for review to '
                                     'such designated reviewing official. The designated reviewing official must determine, '
                                     'within a reasonable period of time, whether or not to deny the access requested based on '
                                     'the standards in paragraph (a)(3) of this section. The covered entity must promptly '
                                     'provide written notice to the individual of the determination of the designated '
                                     'reviewing official and take other action as required by this section to carry out the '
                                     "designated reviewing official's determination.\n"
                                     '\n'
                                     '(e) Implementation specification: Documentation.  A covered entity must document the '
                                     'following and retain the documentation as required by  164.530(j):\n'
                                     '\n'
                                     '(1) The designated record sets that are subject to access by individuals; and\n'
                                     '\n'
                                     '(2) The titles of the persons or offices responsible for receiving and processing '
                                     'requests for access by individuals.',
          'subchapter': '164.524(a):  Standard: Access to protected health information'},
         {'chapter_title': '164.526: Amendment of protected health information.',
          'conformity_questions': [],
          'objective_title': '164.526(a)(1): Standard: Right to amend.',
          'requirement_description': '(1) Right to amend.  An individual has the right to have a covered entity amend '
                                     'protected health information or a record about the individual in a designated record set '
                                     'for as long as the protected health information is maintained in the designated record '
                                     'set.\n'
                                     '\n'
                                     "(2) Denial of amendment.  A covered entity may deny an individual's request for "
                                     'amendment, if it determines that the protected health information or record that is the '
                                     'subject of the request:\n'
                                     '\n'
                                     '(i) Was not created by the covered entity, unless the individual provides a reasonable '
                                     'basis to believe that the originator of protected health information is no longer '
                                     'available to act on the requested amendment;\n'
                                     '\n'
                                     '(ii) Is not part of the designated record set;\n'
                                     '\n'
                                     '(iii) Would not be available for inspection under  164.524; or\n'
                                     '\n'
                                     '(iv) Is accurate and complete.\n'
                                     '\n'
                                     '(b) Implementation specifications: Requests for amendment and timely action -\n'
                                     '\n'
                                     "(1) Individual's request for amendment.  The covered entity must permit an individual to "
                                     'request that the covered entity amend the protected health information maintained in the '
                                     'designated record set. The covered entity may require individuals to make requests for '
                                     'amendment in writing and to provide a reason to support a requested amendment, provided '
                                     'that it informs individuals in advance of such requirements.\n'
                                     '\n'
                                     '(2) Timely action by the covered entity.\n'
                                     '\n'
                                     "(i) The covered entity must act on the individual's request for an amendment no later "
                                     'than 60 days after receipt of such a request, as follows.\n'
                                     '\n'
                                     '(A) If the covered entity grants the requested amendment, in whole or in part, it must '
                                     'take the actions required by paragraphs (c)(1) and (2) of this section.\n'
                                     '\n'
                                     '(B) If the covered entity denies the requested amendment, in whole or in part, it must '
                                     'provide the individual with a written denial, in accordance with paragraph (d)(1) of '
                                     'this section.\n'
                                     '\n'
                                     '(ii) If the covered entity is unable to act on the amendment within the time required by '
                                     'paragraph (b)(2)(i) of this section, the covered entity may extend the time for such '
                                     'action by no more than 30 days, provided that:\n'
                                     '\n'
                                     '(A) The covered entity, within the time limit set by paragraph (b)(2)(i) of this '
                                     'section, provides the individual with a written statement of the reasons for the delay '
                                     'and the date by which the covered entity will complete its action on the request; and\n'
                                     '\n'
                                     '(B) The covered entity may have only one such extension of time for action on a request '
                                     'for an amendment.\n'
                                     '\n'
                                     '(c) Implementation specifications: Accepting the amendment.  If the covered entity '
                                     'accepts the requested amendment, in whole or in part, the covered entity must comply '
                                     'with the following requirements.\n'
                                     '\n'
                                     '(1) Making the amendment.  The covered entity must make the appropriate amendment to the '
                                     'protected health information or record that is the subject of the request for amendment '
                                     'by, at a minimum, identifying the records in the designated record set that are affected '
                                     'by the amendment and appending or otherwise providing a link to the location of the '
                                     'amendment.\n'
                                     '\n'
                                     '(2) Informing the individual.  In accordance with paragraph (b) of this section, the '
                                     'covered entity must timely inform the individual that the amendment is accepted and '
                                     "obtain the individual's identification of and agreement to have the covered entity "
                                     'notify the relevant persons with which the amendment needs to be shared in accordance '
                                     'with paragraph (c)(3) of this section.\n'
                                     '\n'
                                     '(3) Informing others.  The covered entity must make reasonable efforts to inform and '
                                     'provide the amendment within a reasonable time to:\n'
                                     '\n'
                                     '(i) Persons identified by the individual as having received protected health information '
                                     'about the individual and needing the amendment; and\n'
                                     '\n'
                                     '(ii) Persons, including business associates, that the covered entity knows have the '
                                     'protected health information that is the subject of the amendment and that may have '
                                     'relied, or could foreseeably rely, on such information to the detriment of the '
                                     'individual.\n'
                                     '\n'
                                     '(d) Implementation specifications: Denying the amendment.  If the covered entity denies '
                                     'the requested amendment, in whole or in part, the covered entity must comply with the '
                                     'following requirements.\n'
                                     '\n'
                                     '(1) Denial.  The covered entity must provide the individual with a timely, written '
                                     'denial, in accordance with paragraph (b)(2) of this section. The denial must use plain '
                                     'language and contain:\n'
                                     '\n'
                                     '(i) The basis for the denial, in accordance with paragraph (a)(2) of this section;\n'
                                     '\n'
                                     "(ii) The individual's right to submit a written statement disagreeing with the denial "
                                     'and how the individual may file such a statement;\n'
                                     '\n'
                                     '(iii) A statement that, if the individual does not submit a statement of disagreement, '
                                     "the individual may request that the covered entity provide the individual's request for "
                                     'amendment and the denial with any future disclosures of the protected health information '
                                     'that is the subject of the amendment; and\n'
                                     '\n'
                                     '(iv) A description of how the individual may complain to the covered entity pursuant to '
                                     'the complaint procedures established in  164.530(d) or to the Secretary pursuant to the '
                                     'procedures established in  160.306. The description must include the name, or title, and '
                                     'telephone number of the contact person or office designated in  164.530(a)(1)(ii).\n'
                                     '\n'
                                     '(2) Statement of disagreement.  The covered entity must permit the individual to submit '
                                     'to the covered entity a written statement disagreeing with the denial of all or part of '
                                     'a requested amendment and the basis of such disagreement. The covered entity may '
                                     'reasonably limit the length of a statement of disagreement.\n'
                                     '\n'
                                     '(3) Rebuttal statement.  The covered entity may prepare a written rebuttal to the '
                                     "individual's statement of disagreement. Whenever such a rebuttal is prepared, the "
                                     'covered entity must provide a copy to the individual who submitted the statement of '
                                     'disagreement.\n'
                                     '\n'
                                     '(4) Recordkeeping.  The covered entity must, as appropriate, identify the record or '
                                     'protected health information in the designated record set that is the subject of the '
                                     "disputed amendment and append or otherwise link the individual's request for an "
                                     "amendment, the covered entity's denial of the request, the individual's statement of "
                                     "disagreement, if any, and the covered entity's rebuttal, if any, to the designated "
                                     'record set.\n'
                                     '\n'
                                     '(5) Future disclosures.\n'
                                     '\n'
                                     '(i) If a statement of disagreement has been submitted by the individual, the covered '
                                     'entity must include the material appended in accordance with paragraph (d)(4) of this '
                                     'section, or, at the election of the covered entity, an accurate summary of any such '
                                     'information, with any subsequent disclosure of the protected health information to which '
                                     'the disagreement relates.\n'
                                     '\n'
                                     '(ii) If the individual has not submitted a written statement of disagreement, the '
                                     "covered entity must include the individual's request for amendment and its denial, or an "
                                     'accurate summary of such information, with any subsequent disclosure of the protected '
                                     'health information only if the individual has requested such action in accordance with '
                                     'paragraph (d)(1)(iii) of this section.\n'
                                     '\n'
                                     '(iii) When a subsequent disclosure described in paragraph (d)(5)(i) or (ii) of this '
                                     'section is made using a standard transaction under part 162 of this subchapter that does '
                                     'not permit the additional material to be included with the disclosure, the covered '
                                     'entity may separately transmit the material required by paragraph (d)(5)(i) or (ii) of '
                                     'this section, as applicable, to the recipient of the standard transaction.\n'
                                     '\n'
                                     '(e) Implementation specification: Actions on notices of amendment.  A covered entity '
                                     "that is informed by another covered entity of an amendment to an individual's protected "
                                     'health information, in accordance with paragraph (c)(3) of this section, must amend the '
                                     'protected health information in designated record sets as provided by paragraph (c)(1) '
                                     'of this section.\n'
                                     '\n'
                                     '(f) Implementation specification: Documentation.  A covered entity must document the '
                                     'titles of the persons or offices responsible for receiving and processing requests for '
                                     'amendments by individuals and retain the documentation as required by  164.530(j).',
          'subchapter': '164.526(a):  Standard: Right to amend.'},
         {'chapter_title': '164.528: Accounting of disclosures of protected health information.',
          'conformity_questions': [],
          'objective_title': '164.528(a)(1): Standard: Right to an accounting of disclosures of protected health information.',
          'requirement_description': '(1) An individual has a right to receive an accounting of disclosures of protected '
                                     'health information made by a covered entity in the six years prior to the date on which '
                                     'the accounting is requested, except for disclosures:\n'
                                     '\n'
                                     '(i) To carry out treatment, payment and health care operations as provided in  164.506;\n'
                                     '\n'
                                     '(ii) To individuals of protected health information about them as provided in  164.502;\n'
                                     '\n'
                                     '(iii) Incident to a use or disclosure otherwise permitted or required by this subpart, '
                                     'as provided in  164.502;\n'
                                     '\n'
                                     '(iv) Pursuant to an authorization as provided in  164.508;\n'
                                     '\n'
                                     "(v) For the facility's directory or to persons involved in the individual's care or "
                                     'other notification purposes as provided in  164.510;\n'
                                     '\n'
                                     '(vi) For national security or intelligence purposes as provided in  164.512(k)(2);\n'
                                     '\n'
                                     '(vii) To correctional institutions or law enforcement officials as provided in  '
                                     '164.512(k)(5);\n'
                                     '\n'
                                     '(viii) As part of a limited data set in accordance with  164.514(e); or\n'
                                     '\n'
                                     '(ix) That occurred prior to the compliance date for the covered entity.\n'
                                     '\n'
                                     '(2)\n'
                                     '\n'
                                     "(i) The covered entity must temporarily suspend an individual's right to receive an "
                                     'accounting of disclosures to a health oversight agency or law enforcement official, as '
                                     'provided in  164.512(d) or (f), respectively, for the time specified by such agency or '
                                     'official, if such agency or official provides the covered entity with a written '
                                     'statement that such an accounting to the individual would be reasonably likely to impede '
                                     "the agency's activities and specifying the time for which such a suspension is "
                                     'required.\n'
                                     '\n'
                                     '(ii) If the agency or official statement in paragraph (a)(2)(i) of this section is made '
                                     'orally, the covered entity must:\n'
                                     '\n'
                                     '(A) Document the statement, including the identity of the agency or official making the '
                                     'statement;\n'
                                     '\n'
                                     "(B) Temporarily suspend the individual's right to an accounting of disclosures subject "
                                     'to the statement; and\n'
                                     '\n'
                                     '(C) Limit the temporary suspension to no longer than 30 days from the date of the oral '
                                     'statement, unless a written statement pursuant to paragraph (a)(2)(i) of this section is '
                                     'submitted during that time.\n'
                                     '\n'
                                     '(3) An individual may request an accounting of disclosures for a period of time less '
                                     'than six years from the date of the request.\n'
                                     '\n'
                                     '(b) Implementation specifications: Content of the accounting.  The covered entity must '
                                     'provide the individual with a written accounting that meets the following requirements.\n'
                                     '\n'
                                     '(1) Except as otherwise provided by paragraph (a) of this section, the accounting must '
                                     'include disclosures of protected health information that occurred during the six years '
                                     '(or such shorter time period at the request of the individual as provided in paragraph '
                                     '(a)(3) of this section) prior to the date of the request for an accounting, including '
                                     'disclosures to or by business associates of the covered entity.\n'
                                     '\n'
                                     '(2) Except as otherwise provided by paragraphs (b)(3) or (b)(4) of this section, the '
                                     'accounting must include for each disclosure:\n'
                                     '\n'
                                     '(i) The date of the disclosure;\n'
                                     '\n'
                                     '(ii) The name of the entity or person who received the protected health information and, '
                                     'if known, the address of such entity or person;\n'
                                     '\n'
                                     '(iii) A brief description of the protected health information disclosed; and\n'
                                     '\n'
                                     '(iv) A brief statement of the purpose of the disclosure that reasonably informs the '
                                     'individual of the basis for the disclosure or, in lieu of such statement, a copy of a '
                                     'written request for a disclosure under  164.502(a)(2)(ii) or  164.512, if any.\n'
                                     '\n'
                                     '(3) If, during the period covered by the accounting, the covered entity has made '
                                     'multiple disclosures of protected health information to the same person or entity for a '
                                     'single purpose under  164.502(a)(2)(ii) or  164.512, the accounting may, with respect to '
                                     'such multiple disclosures, provide:\n'
                                     '\n'
                                     '(i) The information required by paragraph (b)(2) of this section for the first '
                                     'disclosure during the accounting period;\n'
                                     '\n'
                                     '(ii) The frequency, periodicity, or number of the disclosures made during the accounting '
                                     'period; and\n'
                                     '\n'
                                     '(iii) The date of the last such disclosure during the accounting period.\n'
                                     '\n'
                                     '(4)\n'
                                     '\n'
                                     '(i) If, during the period covered by the accounting, the covered entity has made '
                                     'disclosures of protected health information for a particular research purpose in '
                                     'accordance with  164.512(i) for 50 or more individuals, the accounting may, with respect '
                                     'to such disclosures for which the protected health information about the individual may '
                                     'have been included, provide:\n'
                                     '\n'
                                     '(A) The name of the protocol or other research activity;\n'
                                     '\n'
                                     '(B) A description, in plain language, of the research protocol or other research '
                                     'activity, including the purpose of the research and the criteria for selecting '
                                     'particular records;\n'
                                     '\n'
                                     '(C) A brief description of the type of protected health information that was disclosed;\n'
                                     '\n'
                                     '(D) The date or period of time during which such disclosures occurred, or may have '
                                     'occurred, including the date of the last such disclosure during the accounting period;\n'
                                     '\n'
                                     '(E) The name, address, and telephone number of the entity that sponsored the research '
                                     'and of the researcher to whom the information was disclosed; and\n'
                                     '\n'
                                     '(F) A statement that the protected health information of the individual may or may not '
                                     'have been disclosed for a particular protocol or other research activity.\n'
                                     '\n'
                                     '(ii) If the covered entity provides an accounting for research disclosures, in '
                                     'accordance with paragraph (b)(4) of this section, and if it is reasonably likely that '
                                     'the protected health information of the individual was disclosed for such research '
                                     'protocol or activity, the covered entity shall, at the request of the individual, assist '
                                     'in contacting the entity that sponsored the research and the researcher.\n'
                                     '\n'
                                     '(c) Implementation specifications: Provision of the accounting.\n'
                                     '\n'
                                     "(1) The covered entity must act on the individual's request for an accounting, no later "
                                     'than 60 days after receipt of such a request, as follows.\n'
                                     '\n'
                                     '(i) The covered entity must provide the individual with the accounting requested; or\n'
                                     '\n'
                                     '(ii) If the covered entity is unable to provide the accounting within the time required '
                                     'by paragraph (c)(1) of this section, the covered entity may extend the time to provide '
                                     'the accounting by no more than 30 days, provided that:\n'
                                     '\n'
                                     '(A) The covered entity, within the time limit set by paragraph (c)(1) of this section, '
                                     'provides the individual with a written statement of the reasons for the delay and the '
                                     'date by which the covered entity will provide the accounting; and\n'
                                     '\n'
                                     '(B) The covered entity may have only one such extension of time for action on a request '
                                     'for an accounting.\n'
                                     '\n'
                                     '(2) The covered entity must provide the first accounting to an individual in any 12 '
                                     'month period without charge. The covered entity may impose a reasonable, cost-based fee '
                                     'for each subsequent request for an accounting by the same individual within the 12 month '
                                     'period, provided that the covered entity informs the individual in advance of the fee '
                                     'and provides the individual with an opportunity to withdraw or modify the request for a '
                                     'subsequent accounting in order to avoid or reduce the fee.\n'
                                     '\n'
                                     '(d) Implementation specification: Documentation.  A covered entity must document the '
                                     'following and retain the documentation as required by  164.530(j):\n'
                                     '\n'
                                     '(1) The information required to be included in an accounting under paragraph (b) of this '
                                     'section for disclosures of protected health information that are subject to an '
                                     'accounting under paragraph (a) of this section;\n'
                                     '\n'
                                     '(2) The written accounting that is provided to the individual under this section; and\n'
                                     '\n'
                                     '(3) The titles of the persons or offices responsible for receiving and processing '
                                     'requests for an accounting by individuals.',
          'subchapter': '164.528(a):  Standard: Right to an accounting of disclosures of protected health information.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': ['Q-SEA-02.1: Does the organization standardize technology and process terminology to reduce '
                                   'confusion amongst groups and departments? .',
                                   'Q-TPM-06: Does the organization control personnel security requirements including security '
                                   'roles and responsibilities for third-party providers?.',
                                   'Q-IAC-09: Does the organization govern naming standards for usernames and systems?.'],
          'objective_title': '164.530(a)(1): Standard: Personnel designations.',
          'requirement_description': '(i) A covered entity must designate a privacy official who is responsible for the '
                                     'development and implementation of the policies and procedures of the entity.\n'
                                     '\n'
                                     '(ii) A covered entity must designate a contact person or office who is responsible for '
                                     'receiving complaints under this section and who is able to provide further information '
                                     'about matters covered by the notice required by  164.520.\n'
                                     '\n'
                                     '(2) Implementation specification: Personnel designations.  A covered entity must '
                                     'document the personnel designations in paragraph (a)(1) of this section as required by '
                                     'paragraph (j) of this section.',
          'subchapter': '164.530(a):  Standard: Personnel designations.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': [],
          'objective_title': '164.530(b)(1): Standard: Training.',
          'requirement_description': 'A covered entity must train all members of its workforce on the policies and procedures '
                                     'with respect to protected health information required by this subpart and subpart D of '
                                     'this part, as necessary and appropriate for the members of the workforce to carry out '
                                     'their functions within the covered entity.\n'
                                     '\n'
                                     '(2) Implementation specifications: Training.\n'
                                     '\n'
                                     '(i) A covered entity must provide training that meets the requirements of paragraph '
                                     '(b)(1) of this section, as follows:\n'
                                     '\n'
                                     "(A) To each member of the covered entity's workforce by no later than the compliance "
                                     'date for the covered entity;\n'
                                     '\n'
                                     '(B) Thereafter, to each new member of the workforce within a reasonable period of time '
                                     "after the person joins the covered entity's workforce; and\n"
                                     '\n'
                                     "(C) To each member of the covered entity's workforce whose functions are affected by a "
                                     'material change in the policies or procedures required by this subpart or subpart D of '
                                     'this part, within a reasonable period of time after the material change becomes '
                                     'effective in accordance with paragraph (i) of this section.\n'
                                     '\n'
                                     '(ii) A covered entity must document that the training as described in paragraph '
                                     '(b)(2)(i) of this section has been provided, as required by paragraph (j) of this '
                                     'section.',
          'subchapter': '164.530(b):  Standard: Training.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': ['Q-CRY-01: Does the organization facilitate the implementation of cryptographic protections '
                                   'controls using known public standards and trusted cryptographic technologies?.',
                                   'Q-CFG-02: Does the organization develop, document and maintain secure baseline '
                                   'configurations for technology platform that are consistent with industry-accepted system '
                                   'hardening standards? .',
                                   'Q-DCH-13.3: Does the organization ensure that the requirements for the protection of '
                                   'sensitive information processed, stored or transmitted on external systems, are '
                                   'implemented in accordance with applicable statutory, regulatory and contractual '
                                   'obligations?.'],
          'objective_title': '164.530(c)(1): Standard: Safeguards.',
          'requirement_description': 'A covered entity must have in place appropriate administrative, technical, and physical '
                                     'safeguards to protect the privacy of protected health information.\n'
                                     '\n'
                                     '(2)\n'
                                     '\n'
                                     '(i) Implementation specification: Safeguards.  A covered entity must reasonably '
                                     'safeguard protected health information from any intentional or unintentional use or '
                                     'disclosure that is in violation of the standards, implementation specifications or other '
                                     'requirements of this subpart.\n'
                                     '\n'
                                     '(ii) A covered entity must reasonably safeguard protected health information to limit '
                                     'incidental uses or disclosures made pursuant to an otherwise permitted or required use '
                                     'or disclosure.',
          'subchapter': '164.530(c):  Standard: Safeguards.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': [],
          'objective_title': '164.530(d)(1): Standard: Complaints to the covered entity.',
          'requirement_description': 'A covered entity must provide a process for individuals to make complaints concerning '
                                     "the covered entity's policies and procedures required by this subpart and subpart D of "
                                     'this part or its compliance with such policies and procedures or the requirements of '
                                     'this subpart or subpart D of this part.\n'
                                     '\n'
                                     '(2) Implementation specification: Documentation of complaints.  As required by paragraph '
                                     '(j) of this section, a covered entity must document all complaints received, and their '
                                     'disposition, if any.',
          'subchapter': '164.530(d):  Standard: Complaints to the covered entity. '},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': [],
          'objective_title': '164.530(e)(1): Standard: Sanctions.',
          'requirement_description': 'A covered entity must have and apply appropriate sanctions against members of its '
                                     'workforce who fail to comply with the privacy policies and procedures of the covered '
                                     'entity or the requirements of this subpart or subpart D of this part. This standard does '
                                     "not apply to a member of the covered entity's workforce with respect to actions that are "
                                     'covered by and that meet the conditions of  164.502(j) or paragraph (g)(2) of this '
                                     'section.\n'
                                     '\n'
                                     '(2) Implementation specification: Documentation.  As required by paragraph (j) of this '
                                     'section, a covered entity must document the sanctions that are applied, if any.',
          'subchapter': '164.530(e):  Standard: Sanctions.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': ['Q-RSK-06.2: Does the organization identify and implement compensating countermeasures to '
                                   'reduce risk and exposure to threats?.'],
          'objective_title': '164.530(f): Standard: Mitigation.',
          'requirement_description': 'A covered entity must mitigate, to the extent practicable, any harmful effect that is '
                                     'known to the covered entity of a use or disclosure of protected health information in '
                                     'violation of its policies and procedures or the requirements of this subpart by the '
                                     'covered entity or its business associate.',
          'subchapter': '164.530(f):  Standard: Mitigation. '},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': [],
          'objective_title': '164.530(g): Standard: Refraining from intimidating or retaliatory acts.',
          'requirement_description': 'A covered entity\n'
                                     '\n'
                                     '(1) May not intimidate, threaten, coerce, discriminate against, or take other '
                                     'retaliatory action against any individual for the exercise by the individual of any '
                                     'right established, or for participation in any process provided for, by this subpart or '
                                     'subpart D of this part, including the filing of a complaint under this section; and\n'
                                     '\n'
                                     '(2) Must refrain from intimidation and retaliation as provided in  160.316 of this '
                                     'subchapter.',
          'subchapter': '164.530(g):  Standard: Refraining from intimidating or retaliatory acts.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': ['Q-NET-04.7: Does the organization enforce information flow control using security policy '
                                   'filters as a basis for flow control decisions?.'],
          'objective_title': '164.530(h): Standard: Waiver of rights.',
          'requirement_description': 'A covered entity may not require individuals to waive their rights under  160.306 of '
                                     'this subchapter, this subpart, or subpart D of this part, as a condition of the '
                                     'provision of treatment, payment, enrollment in a health plan, or eligibility for '
                                     'benefits.',
          'subchapter': '164.530(h):  Standard: Waiver of rights.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': ['Q-OPS-01.1: Does the organization use Standardized Operating Procedures (SOP), or similar '
                                   'mechanisms, to identify and document day-to-day procedures to enable the proper execution '
                                   'of assigned tasks?.',
                                   'Q-WEB-01: Does the organization facilitate the implementation of an enterprise-wide web '
                                   'management policy, as well as associated standards, controls and procedures?.'],
          'objective_title': '164.530(i)(1): Standard: Policies and procedures.',
          'requirement_description': 'A covered entity must implement policies and procedures with respect to protected health '
                                     'information that are designed to comply with the standards, implementation '
                                     'specifications, or other requirements of this subpart and subpart D of this part. The '
                                     'policies and procedures must be reasonably designed, taking into account the size and '
                                     'the type of activities that relate to protected health information undertaken by a '
                                     'covered entity, to ensure such compliance. This standard is not to be construed to '
                                     'permit or excuse an action that violates any other standard, implementation '
                                     'specification, or other requirement of this subpart.',
          'subchapter': '164.530(i):  Standard: Policies and procedures.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': ['Q-AST-02.4: Does the organization document and govern instances of approved deviations '
                                   'from established baseline configurations?.',
                                   'Q-CHG-02: Does the organization govern the technical configuration change control '
                                   'processes?.',
                                   'Q-CHG-04.4: Does the organization limit operational privileges for implementing changes?.'],
          'objective_title': '164.530(i)(2): Standard: Changes to policies and procedures.',
          'requirement_description': '(i) A covered entity must change its policies and procedures as necessary and '
                                     'appropriate to comply with changes in the law, including the standards, requirements, '
                                     'and implementation specifications of this subpart or subpart D of this part.\n'
                                     '\n'
                                     '(ii) When a covered entity changes a privacy practice that is stated in the notice '
                                     'described in  164.520, and makes corresponding changes to its policies and procedures, '
                                     'it may make the changes effective for protected health information that it created or '
                                     'received prior to the effective date of the notice revision, if the covered entity has, '
                                     'in accordance with  164.520(b)(1)(v)(C), included in the notice a statement reserving '
                                     'its right to make such a change in its privacy practices; or\n'
                                     '\n'
                                     '(iii) A covered entity may make any other changes to policies and procedures at any '
                                     'time, provided that the changes are documented and implemented in accordance with '
                                     'paragraph (i)(5) of this section.\n'
                                     '\n'
                                     '(3) Implementation specification: Changes in law.  Whenever there is a change in law '
                                     "that necessitates a change to the covered entity's policies or procedures, the covered "
                                     'entity must promptly document and implement the revised policy or procedure. If the '
                                     'change in law materially affects the content of the notice required by  164.520, the '
                                     'covered entity must promptly make the appropriate revisions to the notice in accordance '
                                     'with  164.520(b)(3). Nothing in this paragraph may be used by a covered entity to excuse '
                                     'a failure to comply with the law.\n'
                                     '\n'
                                     '(4) Implementation specifications: Changes to privacy practices stated in the notice.\n'
                                     '\n'
                                     '(i) To implement a change as provided by paragraph (i)(2)(ii) of this section, a covered '
                                     'entity must:\n'
                                     '\n'
                                     '(A) Ensure that the policy or procedure, as revised to reflect a change in the covered '
                                     "entity's privacy practice as stated in its notice, complies with the standards, "
                                     'requirements, and implementation specifications of this subpart;\n'
                                     '\n'
                                     '(B) Document the policy or procedure, as revised, as required by paragraph (j) of this '
                                     'section; and\n'
                                     '\n'
                                     '(C) Revise the notice as required by  164.520(b)(3) to state the changed practice and '
                                     'make the revised notice available as required by  164.520(c). The covered entity may not '
                                     'implement a change to a policy or procedure prior to the effective date of the revised '
                                     'notice.\n'
                                     '\n'
                                     '(ii) If a covered entity has not reserved its right under  164.520(b)(1)(v)(C) to change '
                                     'a privacy practice that is stated in the notice, the covered entity is bound by the '
                                     'privacy practices as stated in the notice with respect to protected health information '
                                     'created or received while such notice is in effect. A covered entity may change a '
                                     'privacy practice that is stated in the notice, and the related policies and procedures, '
                                     'without having reserved the right to do so, provided that:\n'
                                     '\n'
                                     '(A) Such change meets the implementation specifications in paragraphs (i)(4)(i)(A)-(C) '
                                     'of this section; and\n'
                                     '\n'
                                     '(B) Such change is effective only with respect to protected health information created '
                                     'or received after the effective date of the notice.\n'
                                     '\n'
                                     '(5) Implementation specification: Changes to other policies or procedures.  A covered '
                                     'entity may change, at any time, a policy or procedure that does not materially affect '
                                     'the content of the notice required by  164.520, provided that:\n'
                                     '\n'
                                     '(i) The policy or procedure, as revised, complies with the standards, requirements, and '
                                     'implementation specifications of this subpart; and\n'
                                     '\n'
                                     '(ii) Prior to the effective date of the change, the policy or procedure, as revised, is '
                                     'documented as required by paragraph (j) of this section.',
          'subchapter': '164.530(i):  Standard: Policies and procedures.'},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': ['Q-SEA-02.1: Does the organization standardize technology and process terminology to reduce '
                                   'confusion amongst groups and departments? .',
                                   'Q-CLD-08: Does the organization ensure interoperability by requiring cloud providers to '
                                   'use industry-recognized formats and provide documentation of custom changes for review?.',
                                   'Q-DCH-24: Does the organization identify and document the location of information and the '
                                   'specific system components on which the information resides?.'],
          'objective_title': '164.530(j)(1): Standard: Documentation.',
          'requirement_description': 'A covered entity must:\n'
                                     '\n'
                                     '(i) Maintain the policies and procedures provided for in paragraph (i) of this section '
                                     'in written or electronic form;\n'
                                     '\n'
                                     '(ii) If a communication is required by this subpart to be in writing, maintain such '
                                     'writing, or an electronic copy, as documentation; and\n'
                                     '\n'
                                     '(iii) If an action, activity, or designation is required by this subpart to be '
                                     'documented, maintain a written or electronic record of such action, activity, or '
                                     'designation.\n'
                                     '\n'
                                     '(iv) Maintain documentation sufficient to meet its burden of proof under  164.414(b).\n'
                                     '\n'
                                     '(2) Implementation specification: Retention period.  A covered entity must retain the '
                                     'documentation required by paragraph (j)(1) of this section for six years from the date '
                                     'of its creation or the date when it last was in effect, whichever is later.',
          'subchapter': '164.530(j):  Standard: Documentation. '},
         {'chapter_title': '164.530: Administrative requirements.',
          'conformity_questions': [],
          'objective_title': '164.530(k): Standard: Group health plans.',
          'requirement_description': '(1) A group health plan is not subject to the standards or implementation specifications '
                                     'in paragraphs (a) through (f) and (i) of this section, to the extent that:\n'
                                     '\n'
                                     '(i) The group health plan provides health benefits solely through an insurance contract '
                                     'with a health insurance issuer or an HMO; and\n'
                                     '\n'
                                     '(ii) The group health plan does not create or receive protected health information, '
                                     'except for:\n'
                                     '\n'
                                     '(A) Summary health information as defined in  164.504(a); or\n'
                                     '\n'
                                     '(B) Information on whether the individual is participating in the group health plan, or '
                                     'is enrolled in or has disenrolled from a health insurance issuer or HMO offered by the '
                                     'plan.\n'
                                     '\n'
                                     '(2) A group health plan described in paragraph (k)(1) of this section is subject to the '
                                     'standard and implementation specification in paragraph (j) of this section only with '
                                     'respect to plan documents amended in accordance with  164.504(f).',
          'subchapter': '164.530(k):  Standard: Group health plans.'},
         {'chapter_title': '164.532: Transition provisions.',
          'conformity_questions': ['Q-AST-02.4: Does the organization document and govern instances of approved deviations '
                                   'from established baseline configurations?.',
                                   'Q-CHG-04.4: Does the organization limit operational privileges for implementing changes?.',
                                   'Q-CHG-03: Does the organization analyze proposed changes for potential security impacts, '
                                   'prior to the implementation of the change?.'],
          'objective_title': '164.532(a): Standard: Effect of prior authorizations.',
          'requirement_description': 'Notwithstanding  164.508 and 164.512(i), a covered entity may use or disclose protected '
                                     'health information, consistent with paragraphs (b) and (c) of this section, pursuant to '
                                     'an authorization or other express legal permission obtained from an individual '
                                     'permitting the use or disclosure of protected health information, informed consent of '
                                     'the individual to participate in research, a waiver of informed consent by an IRB, or a '
                                     'waiver of authorization in accordance with  164.512(i)(1)(i).\n'
                                     '\n'
                                     '(b) Implementation specification: Effect of prior authorization for purposes other than '
                                     'research.  Notwithstanding any provisions in  164.508, a covered entity may use or '
                                     'disclose protected health information that it created or received prior to the '
                                     'applicable compliance date of this subpart pursuant to an authorization or other express '
                                     'legal permission obtained from an individual prior to the applicable compliance date of '
                                     'this subpart, provided that the authorization or other express legal permission '
                                     'specifically permits such use or disclosure and there is no agreed-to restriction in '
                                     'accordance with  164.522(a).\n'
                                     '\n'
                                     '(c) Implementation specification: Effect of prior permission for research.  '
                                     'Notwithstanding any provisions in  164.508 and 164.512(i), a covered entity may, to the '
                                     'extent allowed by one of the following permissions, use or disclose, for research, '
                                     'protected health information that it created or received either before or after the '
                                     'applicable compliance date of this subpart, provided that there is no agreed-to '
                                     'restriction in accordance with  164.522(a), and the covered entity has obtained, prior '
                                     'to the applicable compliance date, either:\n'
                                     '\n'
                                     '(1) An authorization or other express legal permission from an individual to use or '
                                     'disclose protected health information for the research;\n'
                                     '\n'
                                     '(2) The informed consent of the individual to participate in the research;\n'
                                     '\n'
                                     '(3) A waiver, by an IRB, of informed consent for the research, in accordance with 7 CFR '
                                     '1c.116(d), 10 CFR 745.116(d), 14 CFR 1230.116(d), 15 CFR 27.116(d), 16 CFR 1028.116(d), '
                                     '21 CFR 50.24, 22 CFR 225.116(d), 24 CFR 60.116(d), 28 CFR 46.116(d), 32 CFR 219.116(d), '
                                     '34 CFR 97.116(d), 38 CFR 16.116(d), 40 CFR 26.116(d), 45 CFR 46.116(d), 45 CFR '
                                     '690.116(d), or 49 CFR 11.116(d), provided that a covered entity must obtain '
                                     'authorization in accordance with  164.508 if, after the compliance date, informed '
                                     'consent is sought from an individual participating in the research; or\n'
                                     '\n'
                                     '(4) A waiver of authorization in accordance with  164.512(i)(1)(i).',
          'subchapter': '164.532(a):  Standard: Effect of prior authorizations.'},
         {'chapter_title': '164.532: Transition provisions.',
          'conformity_questions': [],
          'objective_title': '164.532(d): Standard: Effect of prior contracts or other arrangements with business associates.',
          'requirement_description': 'Notwithstanding any other provisions of this part, a covered entity, or business '
                                     'associate with respect to a subcontractor, may disclose protected health information to '
                                     'a business associate and may allow a business associate to create, receive, maintain, or '
                                     'transmit protected health information on its behalf pursuant to a written contract or '
                                     'other written arrangement with such business associate that does not comply with  '
                                     '164.308(b), 164.314(a), 164.502(e), and 164.504(e), only in accordance with paragraph '
                                     '(e) of this section.\n'
                                     '\n'
                                     '(e) Implementation specification: Deemed compliance -\n'
                                     '\n'
                                     '(1) Qualification.  Notwithstanding other sections of this part, a covered entity, or '
                                     'business associate with respect to a subcontractor, is deemed to be in compliance with '
                                     'the documentation and contract requirements of  164.308(b), 164.314(a), 164.502(e), and '
                                     '164.504(e), with respect to a particular business associate relationship, for the time '
                                     'period set forth in paragraph (e)(2) of this section, if:\n'
                                     '\n'
                                     '(i) Prior to January 25, 2013, such covered entity, or business associate with respect '
                                     'to a subcontractor, has entered into and is operating pursuant to a written contract or '
                                     'other written arrangement with the business associate that complies with the applicable '
                                     'provisions of  164.314(a) or  164.504(e) that were in effect on such date; and\n'
                                     '\n'
                                     '(ii) The contract or other arrangement is not renewed or modified from March 26, 2013, '
                                     'until September 23, 2013.\n'
                                     '\n'
                                     '(2) Limited deemed compliance period.  A prior contract or other arrangement that meets '
                                     'the qualification requirements in paragraph (e) of this section shall be deemed '
                                     'compliant until the earlier of:\n'
                                     '\n'
                                     '(i) The date such contract or other arrangement is renewed or modified on or after '
                                     'September 23, 2013; or\n'
                                     '\n'
                                     '(ii) September 22, 2014.\n'
                                     '\n'
                                     '(3) Covered entity responsibilities.  Nothing in this section shall alter the '
                                     'requirements of a covered entity to comply with part 160, subpart C of this subchapter '
                                     'and  164.524, 164.526, 164.528, and 164.530(f) with respect to protected health '
                                     'information held by a business associate.',
          'subchapter': '164.532(d):  Standard: Effect of prior contracts or other arrangements with business associates.'},
         {'chapter_title': '164.532: Transition provisions.',
          'conformity_questions': ['Q-MON-14.1: Does the organization share event logs with third-party organizations based on '
                                   'specific cross-organizational sharing agreements?.',
                                   'Q-IAC-03.4: Does the organization disassociate user attributes or credential assertion '
                                   'relationships among individuals, credential service providers and relying parties?.',
                                   'Q-HRS-06: Does the organization require internal and third-party users to sign appropriate '
                                   'access agreements prior to being granted access? .'],
          'objective_title': '164.532(f): Effect of prior data use agreements.',
          'requirement_description': 'If, prior to January 25, 2013, a covered entity has entered into and is operating '
                                     'pursuant to a data use agreement with a recipient of a limited data set that complies '
                                     'with  164.514(e), notwithstanding  164.502(a)(5)(ii), the covered entity may continue to '
                                     'disclose a limited data set pursuant to such agreement in exchange for remuneration from '
                                     'or on behalf of the recipient of the protected health information until the earlier of:\n'
                                     '\n'
                                     '(1) The date such agreement is renewed or modified on or after September 23, 2013; or\n'
                                     '\n'
                                     '(2) September 22, 2014.',
          'subchapter': '164.532(f):  Effect of prior data use agreements.'},
         {'chapter_title': '164.534: Compliance dates for initial implementation of the privacy standards.',
          'conformity_questions': [],
          'objective_title': '164.534(a): Health care providers.',
          'requirement_description': 'A covered health care provider must comply with the applicable requirements of this '
                                     'subpart no later than April 14, 2003.',
          'subchapter': '164.534(a):  Health care providers.'},
         {'chapter_title': '164.534: Compliance dates for initial implementation of the privacy standards.',
          'conformity_questions': [],
          'objective_title': '164.534(b): Health plans.',
          'requirement_description': 'A health plan must comply with the applicable requirements of this subpart no later than '
                                     'the following as applicable:\n'
                                     '\n'
                                     '(1) Health plans other than small health plans.  April 14, 2003.\n'
                                     '\n'
                                     '(2) Small health plans.  April 14, 2004.',
          'subchapter': '164.534(b):  Health plans.'},
         {'chapter_title': '164.534: Compliance dates for initial implementation of the privacy standards.',
          'conformity_questions': [],
          'objective_title': '164.534(c): Health clearinghouses.',
          'requirement_description': 'A health care clearinghouse must comply with the applicable requirements of this subpart '
                                     'no later than April 14, 2003.',
          'subchapter': '164.534(c):  Health clearinghouses. '}]
