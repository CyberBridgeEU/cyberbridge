# app/seeds/australia_energy_aescsf_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class AustraliaEnergyAescsfSeed(BaseSeed):
    """Seed Australia Energy (AESCSF) framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating Australia Energy (AESCSF) framework and questions...")

        # Get default organization
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]

        # Create Australia Energy (AESCSF) Framework
        australia_energy_aescsf_framework, created = self.get_or_create(
            models.Framework,
            {"name": "Australia Energy (AESCSF)", "organisation_id": default_org.id},
            {
                "name": "Australia Energy (AESCSF)",
                "description": "",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Organization", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation to prevent duplicates
        if not created:
            logger.info("Australia Energy (AESCSF) framework already exists, skipping question creation to prevent duplicates")

            # Get existing questions for this framework
            existing_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == australia_energy_aescsf_framework.id
            ).all()

            # Get existing objectives for this framework
            existing_objectives = self.db.query(models.Objectives).join(
                models.Chapters,
                models.Objectives.chapter_id == models.Chapters.id
            ).filter(
                models.Chapters.framework_id == australia_energy_aescsf_framework.id
            ).all()

            logger.info(f"Found existing Australia Energy (AESCSF) framework with {len(existing_questions)} questions and {len(existing_objectives)} objectives")

            return {
                "framework": australia_energy_aescsf_framework,
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
                description="Australia Energy (AESCSF) conformity question",
                mandatory=True,
                assessment_type_id=conformity_assessment_type.id
            )
            self.db.add(question)
            self.db.flush()  # Get the question ID
            conformity_questions.append(question)

            # Create framework-question relationship
            framework_question = models.FrameworkQuestion(
                framework_id=australia_energy_aescsf_framework.id,
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
                        "framework_id": australia_energy_aescsf_framework.id
                    },
                    {
                        "title": chapter_title,
                        "framework_id": australia_energy_aescsf_framework.id
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

        logger.info(f"Created Australia Energy (AESCSF) framework with {len(unique_conformity_questions)} conformity questions and {len(unique_objectives_data)} objectives")

        return {
            "framework": australia_energy_aescsf_framework,
            "conformity_questions": conformity_questions,
            "objectives": objectives_list
        }

    def _get_unique_conformity_questions(self):
        """Returns the list of unique conformity questions (pre-deduplicated)"""
        return []

    def _get_unique_objectives(self):
        """Returns the list of unique objectives (pre-deduplicated)"""
        return [{'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-1A: There is an inventory of OT and IT assets that are important to the delivery of the '
                             'function; management of the inventory may be ad hoc',
          'requirement_description': 'Have you recorded the technology assets that exist within your organisation? Asset '
                                     'inventories may be centralised (e.g. in an asset management system), or be maintained '
                                     'separately within each function. This includes technology assets within Operational '
                                     'Technology (OT) environments, including Industrial Control Systems (ICS).\n'
                                     'Recording technology assets in an inventory enables an organisation to maintain '
                                     'visibility of what systems and equipment exist, what their purpose is, who owns them, '
                                     'where they are located and other useful information to support the management of those '
                                     'assets throughout their lifecycle.',
          'subchapter': 'ACM-1: Manage Asset Inventory'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-1B: There is an inventory of information assets that are important to the delivery of the '
                             'function (e.g., SCADA set points, customer information, financial data); management of the '
                             'inventory may be ad hoc',
          'requirement_description': 'Have you recorded the information assets that exist within your organisation? Asset '
                                     'inventories may be centralised (e.g. in an information management system), or be '
                                     'maintained separately within each function.\n'
                                     "This practice may be performed as part of an organisation's broader Information "
                                     'Management function.\n'
                                     'Recording information assets in an inventory enables an organisation to maintain '
                                     'visibility of what data exists, how important it is to the business, who owns it, and '
                                     'other useful information to support the management of the asset throughout its '
                                     'lifecycle.',
          'subchapter': 'ACM-1: Manage Asset Inventory'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-1C: Inventory attributes include information to support the Cyber Security strategy (e.g., '
                             'location, asset owner, applicable Security requirements, service dependencies, service level '
                             'agreements, and conformance of assets to relevant industry standards)',
          'requirement_description': 'Building on ACM-1a and ACM-1b, do your asset inventories contain sufficient information '
                                     'about each asset to enable you to adequately secure those assets throughout their '
                                     'lifecycle?\n'
                                     'This information may include (but is not limited to) the purpose of the asset, '
                                     'technology environment where the asset exists, support method for the asset (e.g. wholly '
                                     'in-house, vendor-supported, vendor-managed).',
          'subchapter': 'ACM-1: Manage Asset Inventory'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-1D: Inventoried assets are prioritised based on their importance to the delivery of the '
                             'function',
          'requirement_description': 'Have you established the importance of each inventoried asset in supporting '
                                     'business-critical activities? Examples of asset prioritisation may include:\n'
                                     '- Assigning a business criticality rating based on the results of a Business Impact '
                                     'Assessment (BIA);\n'
                                     "- Assigning a Security classification rating based on an organisation's Security "
                                     'classification framework.\n'
                                     '\n'
                                     'By understanding the importance of an asset, organisations are able to determine the '
                                     'level of Security protection which that asset requires.',
          'subchapter': 'ACM-1: Manage Asset Inventory'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-1E: There is an inventory for all connected IT and OT assets related to the delivery of the '
                             'function',
          'requirement_description': 'Has the organisation documented how technology assets within each function are '
                                     'physically and logically interconnected? This may take the form of data flow diagrams '
                                     'and/or network diagrams. \n'
                                     '\n'
                                     ' Additionally, this practice could involve documenting the relationships between '
                                     'technology assets (including at the component level) and the services which they '
                                     'support.\n'
                                     '\n'
                                     ' At MIL-3, an organisation should have a thorough understanding of the relationships and '
                                     'interdependencies of technology assets relating to the delivery of the function.',
          'subchapter': 'ACM-1: Manage Asset Inventory'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-1F: The asset inventory is current (as defined by the organisation)',
          'requirement_description': 'Has your organisation defined a requirement for how often the asset inventory should be '
                                     'updated? If so, has the inventory been updated in accordance with this requirement?\n'
                                     '\n'
                                     ' Asset inventories may be updated manually (e.g. via physical asset audits) or '
                                     'automatically (e.g. via automated asset discovery scanning).',
          'subchapter': 'ACM-1: Manage Asset Inventory'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-2A: Configuration baselines are established, at least in an ad hoc manner, for inventoried '
                             'assets where it is desirable to ensure that multiple assets are configured similarly',
          'requirement_description': 'Have you defined a list of settings that you can use to consistently configure multiple '
                                     'assets of the same type?\n'
                                     '\n'
                                     ' This may take the form of system build checklists, configuration snapshots or images.',
          'subchapter': 'ACM-2: Manage Asset Configuration'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-2B: Configuration baselines are used, at least in an ad hoc manner, to configure assets at '
                             'deployment',
          'requirement_description': 'When deploying multiple assets that are required to operate the same way, do you apply '
                                     'the settings identified in ACM-2a?',
          'subchapter': 'ACM-2: Manage Asset Configuration'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-2C: The design of configuration baselines includes Cyber Security objectives',
          'requirement_description': 'In developing the configuration baselines in ACM-2a, did you consider any applicable '
                                     'Security requirements and settings? \n'
                                     '\n'
                                     'Common examples include disabling built-in/default user accounts, changing default '
                                     'passwords, disabling unnecessary or deprecated services, configuring secure remote '
                                     'access methods, hardening configurations, etc. \n'
                                     '\n'
                                     'Mis-configured assets can introduce Security weaknesses which may be exploited. '
                                     'Equipment vendors and independent industry bodies have defined good-practice consensus '
                                     'configuration baselines for a range of common technology systems and platforms.',
          'subchapter': 'ACM-2: Manage Asset Configuration'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-2D: Configuration of assets are monitored for consistency with baselines throughout the '
                             "assets' life cycle",
          'requirement_description': 'Do you check whether assets that have been configured using a baseline remain consistent '
                                     'with that baseline over time?\n'
                                     '\n'
                                     ' These checks may be manually performed, aided by an assessment tool, or automated as '
                                     'part of a more mature configuration management solution.',
          'subchapter': 'ACM-2: Manage Asset Configuration'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-2E: Configuration baselines are reviewed and updated at an organisationally-defined '
                             'frequency',
          'requirement_description': 'Has your organisation defined a requirement for how often configuration baselines should '
                                     'be reviewed and updated? If so, have your configuration baselines been reviewed and '
                                     'updated in accordance with this requirement?\n'
                                     '\n'
                                     ' Asset configurations may need to be adjusted over time in order to address the changing '
                                     'Security threat landscape. E.g. certain configurations may be found to be unsecure due '
                                     'to previously-unidentified vulnerabilities.',
          'subchapter': 'ACM-2: Manage Asset Configuration'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-3A: Changes to inventoried assets are evaluated, at least in an ad hoc manner, before being '
                             'implemented',
          'requirement_description': 'Before making a change to an asset, do you try and understand the nature and potential '
                                     'adverse impact of the change?',
          'subchapter': 'ACM-3: Manage Changes to Assets'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-3B: Changes to inventoried assets are logged, at least in an ad hoc manner',
          'requirement_description': 'Do you keep track of the changes you make to assets within your organisation? This might '
                                     'include documenting a change as part of a formal change management system, or capturing '
                                     'modifications made via maintenance records, etc.',
          'subchapter': 'ACM-3: Manage Changes to Assets'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-3C: Changes to assets are tested prior to being deployed, whenever possible',
          'requirement_description': 'Changes made to assets may have adverse impacts on their integrity or performance. As '
                                     'such, it is important where possible to test planned changes prior to deployment to '
                                     'ensure they will not have unexpected consequences.\n'
                                     '\n'
                                     ' This may include testing planned changes in a development, test or pre-production '
                                     'environment.',
          'subchapter': 'ACM-3: Manage Changes to Assets'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-3D: Change management practices address the full life cycle of assets (i.e., acquisition, '
                             'deployment, operation, retirement)',
          'requirement_description': 'Does your organisation have a formal change management process? If so, does it account '
                                     'for the full life cycle of an asset?\n'
                                     '\n'
                                     ' This may include:\n'
                                     ' -Changes introduced by the implementation or deployment of a new asset;\n'
                                     ' -Changes made to operational assets as part of scheduled maintenance;\n'
                                     ' -Changes made to operational assets in response to issues (e.g. break-fix) or '
                                     'incidents;\n'
                                     ' -Changes made to operational environments as part of asset decommissioning activities.',
          'subchapter': 'ACM-3: Manage Changes to Assets'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-3E: Changes to assets are tested for Cyber Security impact prior to being deployed',
          'requirement_description': 'Changes to assets may introduce Security weaknesses which could be exploited. As such, '
                                     'it is important to identify potentially risky changes and test them to gain comfort that '
                                     'they will not adversely impact the Security of an asset.  \n'
                                     ' Have you identified particular types of high-risk changes that require Security '
                                     'assessment prior to deployment? Examples may include:\n'
                                     ' -Firewall rule changes;\n'
                                     ' -Changes made to Internet-facing web applications;\n'
                                     ' -Network perimeter routing configuration changes. \n'
                                     ' How changes are tested for Security impact may differ depending on the type of change, '
                                     'for example:\n'
                                     ' -Secure code review or code scanning;\n'
                                     ' -Vulnerability scanning or penetration testing;\n'
                                     ' -Secure configuration reviews;\n'
                                     ' -Security architecture / design assessments.',
          'subchapter': 'ACM-3: Manage Changes to Assets'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-3F: Change logs include information about modifications that impact the Cyber Security '
                             'requirements of assets (availability, integrity, confidentiality)',
          'requirement_description': 'When a change is identified as impacting the Security of an asset, does the change '
                                     'assessment (and change ticket/log) explicitly capture the nature and/or magnitude of the '
                                     'impact in terms of confidentiality, integrity and availability?',
          'subchapter': 'ACM-3: Manage Changes to Assets'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-AP1: Changes to Internet-facing assets are not assessed or tested to identify potential '
                             'cyber security vulnerabilities arising from the change itself, prior to implementation',
          'requirement_description': 'Internet-facing assets (such as networks, systems, and applications) may be accessible '
                                     'to anyone on the Internet, which can increase the level of attention that they receive '
                                     'from malicious threat actors.\n'
                                     '\n'
                                     ' As a result, you should test and validate changes affecting an Internet-facing asset, '
                                     'ensuring that the change does not introduce cyber security vulnerabilities that could be '
                                     'exploited.',
          'subchapter': 'ACM-AP: ACM Anti-Patterns'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-AP2: The management of asset inventories is not linked to data governance or business impact '
                             'assessment activities',
          'requirement_description': 'Asset inventories are used as a source of truth to support other business activities.\n'
                                     '\n'
                                     ' As a result, the management of your asset inventories should be linked to data '
                                     'governance or business impact assessment (BIA) activities, to provide confidence that '
                                     'the inventories contain accurate and complete information.\n'
                                     '\n'
                                     'BIAs support you in determining which assets the organisation considers to be critical '
                                     'and/or sensitive.',
          'subchapter': 'ACM-AP: ACM Anti-Patterns'},
         {'chapter_title': 'ACM: Asset, Change, and Configuration Management',
          'conformity_questions': [],
          'objective_title': 'ACM-AP3: Asset inventories have not been updated in the past 24 months',
          'requirement_description': 'Building on ACM-AP2, asset inventories are used as a source of truth to support other '
                                     'business activities, such as:\n'
                                     ' -Configuration and change management\n'
                                     ' -Threat and vulnerability management\n'
                                     ' -Backup management\n'
                                     ' -Service continuity and disaster recovery.\n'
                                     '\n'
                                     'Given the reliance on asset inventories, it is important that they are periodically '
                                     'updated to reflect the changing organisational environment. According to the Australian '
                                     'Cyber Security Centre (ACSC), asset inventories should be updated at least every 24 '
                                     'months, however a higher frequency is recommended.',
          'subchapter': 'ACM-AP: ACM Anti-Patterns'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1A: Privacy requirements applicable to the organisation have been identified, even in an '
                             'ad-hoc manner.',
          'requirement_description': 'Privacy requirements may be imposed by applicable legislation, for example:\n'
                                     ' -Federal legislation (Privacy Act);\n'
                                     ' -State-based legislation (e.g. Health Records and Information Privacy Act 2002 NSW, '
                                     'Health Records Act 2001 VIC, Health Records Privacy and Access Act 1997 ACT).\n'
                                     '\n'
                                     'Privacy requirements may also be imposed by contracts/agreements with customers or '
                                     'suppliers.',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1B: The organisation has defined what it considers personal information in the context of '
                             'its business activities, even in an ad-hoc manner.',
          'requirement_description': "Do you have a defined understanding of what 'personal information' means within your "
                                     'organisation? Does your organisation understand why they collect, use and hold personal '
                                     'information?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1C: There is a point of contact (person or role) to whom privacy issues could be reported, '
                             'even in an ad-hoc manner.',
          'requirement_description': 'Do you have a commonly acknowledged place to report perceived or real privacy issues?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1D: Business activities which involve the collection, processing, storage or transmission of '
                             'personal information have been identified',
          'requirement_description': 'Has your organisation identified which business activities collect, process, store, and '
                                     'use personal information? For example, personal information being collected to on-board '
                                     'a new customer.',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': "APM-1E: The organisation's personal information holdings are documented",
          'requirement_description': 'The organisation documents where (onshore or offshore) and how personal information is '
                                     'collected, processed, stored and transmitted as part of business activities. This might '
                                     'include business processes, IT systems, third party vendors, etc.',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1F: A privacy policy has been documented and communicated within the organisation and the '
                             'general public',
          'requirement_description': 'Does your organisation have a privacy policy that is available for public access?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': "APM-1G: The organisation's requirements for handling of personal information have been defined "
                             'within the privacy policy',
          'requirement_description': 'Do you have a defined understanding of how to handle personal information? Does your '
                                     'understanding conform with the privacy policy?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1H: Specific roles and accountabilities have been assigned for privacy management within the '
                             'organisation',
          'requirement_description': 'Does your organisations have defined roles and accountabilities for privacy management?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': "APM-1I: A privacy management plan has been implemented to govern the organisation's ongoing "
                             'compliance with applicable privacy requirements',
          'requirement_description': "Does your privacy management plan drive ongoing compliance with your organisation's "
                                     'privacy requirements?\n'
                                     ' A privacy management plan defined by the Office of the Australia Information '
                                     'Commissioner is a document that identifies specific, measurable goals and targets that '
                                     'identify how you will meet your privacy obligation commitments',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1J: Privacy related risks have been identified, assessed and documented in a risk register',
          'requirement_description': 'Does your organisation have a risk register that documents privacy related risks?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1K: A documented process exists for responding to privacy enquiries and complaints, '
                             'including customer correction of their personal information',
          'requirement_description': 'Does your organisation have documented procedures on how to handle enquiries and '
                                     "complaints, including procedures on how customers' can correct their personal "
                                     'information?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1L: The organisation provides privacy training to staff responsible for handling personal '
                             'information',
          'requirement_description': 'Does your organisation provide privacy training to your staff?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1M: Existing incident response plan specifically consider data breach scenarios involving '
                             'personal information',
          'requirement_description': 'Does your organisation have an incident response management plan for personal '
                                     'information data breach events?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1N: Incident response plans for data breach scenarios are tested periodically and updated '
                             'based on improvement opportunities identified',
          'requirement_description': 'Does your organisation test the incident response plan for data breach scenarios, at '
                                     'least once a year?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': "APM-1O: The organisation's compliance with applicable privacy requirements is periodically "
                             'assessed and reported to senior management',
          'requirement_description': 'Does your organisation review its privacy obligations at least once a year, to ensure '
                                     'compliance with state, federal and international obligations and/or licensing '
                                     'agreements?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-1P: The privacy management plan is periodically updated to reflect the changing threat and '
                             'regulatory environment',
          'requirement_description': 'Does your organisation review and update your privacy management plan at least once a '
                                     'year?',
          'subchapter': 'APM-1: Manage personal information and privacy'},
         {'chapter_title': 'APM: Australian Privacy Management',
          'conformity_questions': [],
          'objective_title': 'APM-AP1: The function is unaware whether personal information is collected',
          'requirement_description': 'Personal Information is also referred to as Personally Identifiable Information (PII). '
                                     'The Australian Privacy Act defines personal information as information or an opinion '
                                     'about an identified individual, or an individual who is reasonably identifiable:\n'
                                     '(a) whether the information or opinion is true or not; and\n'
                                     '(b) whether the information or opinion is recorded in a material form or not.\n'
                                     '\n'
                                     'One example of PII is a spreadsheet that contains the name, phone number, and email '
                                     'address of one or more individuals. There are many other examples.\n'
                                     '\n'
                                     'Under the Notifiable Data Breaches (NDB) scheme any organisation or agency the Privacy '
                                     'Act 1988 covers must notify affected individuals and the OAIC when a data breach is '
                                     'likely to result in serious harm to an individual whose personal information is '
                                     'involved. Additional information can be obtained from the Australian Government Office '
                                     'of the Australian Information Commissioner (OAIC).',
          'subchapter': 'APM-AP: APM Anti-Patterns'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-1A: The organisation has a Cyber Security program strategy, which may be developed and '
                             'managed in an ad hoc manner',
          'requirement_description': 'Has the organisation defined a series of activities/functions that it will undertake to '
                                     'manage, operate and uplift its Cyber Security capabilities? This might be documented in '
                                     'a formal Cyber Security strategy, or informally in a program of work.',
          'subchapter': 'CPM-1: Establish Cyber Security Program Strategy'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': "CPM-1B: The Cyber Security program strategy defines objectives for the organisation's Cyber "
                             'Security activities',
          'requirement_description': 'Does the strategy in CPM-1a include define clear objectives for each distinct Cyber '
                                     'Security activity/function? CPM-1a must be completed as a pre-requisite for this '
                                     'practice.\n'
                                     '\n'
                                     'Defining clear objectives enables an organisation to measure and assess whether each '
                                     'Cyber Security activity/function is fulfilling its purpose and providing the value '
                                     'required.',
          'subchapter': 'CPM-1: Establish Cyber Security Program Strategy'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-1C: The Cyber Security program strategy and priorities are documented and aligned with the '
                             "organisation's strategic objectives and risk to critical infrastructure",
          'requirement_description': 'Are the objectives defined in the Cyber Security program strategy aligned to the '
                                     "organisation's broader strategic objectives (e.g. values, purpose, guiding principles)? "
                                     'Where the organisation plays a role in critical infrastructure, is this articulated in '
                                     'the Cyber Security strategy, and are the Cyber Security activities/functions defined in '
                                     'a manner that seeks to address the associated risks? CPM-1a must be completed as a '
                                     'pre-requisite for this practice.\n'
                                     '\n'
                                     " Aligning the Cyber Security strategy with an organisation's broader technology and "
                                     'business strategies enables management to articulate how Cyber Security '
                                     'activities/functions are directly contributing to protecting and enabling the '
                                     "organisation's business-critical functions. Demonstrating alignment between Cyber "
                                     'Security and broader organisational objectives also makes it easier to justify requests '
                                     'for funding of specific Cyber Security initiatives.',
          'subchapter': 'CPM-1: Establish Cyber Security Program Strategy'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': "CPM-1D: The Cyber Security program strategy defines the organisation's approach to provide "
                             'program oversight and governance for Cyber Security activities',
          'requirement_description': 'Does the Cyber Security strategy define a clear governance model for how Cyber Security '
                                     'activities/functions will be implemented and managed? This should include '
                                     'accountabilities, roles and responsibilities, as well as governance forums such as '
                                     'program steering committees and Cyber Security working groups, as well as tracking and '
                                     'reporting mechanisms. CPM-1a must be completed as a pre-requisite for this practice.\n'
                                     '\n'
                                     'Without effective governance structures in place, the activities/functions defined in '
                                     'the Cyber Security strategy may not be successfully implemented or realise their full '
                                     'value to the organisation.',
          'subchapter': 'CPM-1: Establish Cyber Security Program Strategy'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-1E: The Cyber Security program strategy defines the structure and organisation of the Cyber '
                             'Security program',
          'requirement_description': "Does the Cyber Security strategy define how the organisation's Cyber Security "
                                     'activities/functions are grouped in terms of organisational structure, accountabilities '
                                     'and reporting lines? Each specific Cyber Security activity/function outlined in the '
                                     "strategy should have an owner defined, and thus a clear 'home' in the organisation's "
                                     'structure. CPM-1a must be completed as a pre-requisite for this practice.\n'
                                     '\n'
                                     ' Assigning ownership and accountability for implementation and management of Cyber '
                                     'Security activities/functions provides clarity within an organisation around which teams '
                                     'are responsible for delivering what activities, and how the leadership structure will '
                                     'enable decision-making.',
          'subchapter': 'CPM-1: Establish Cyber Security Program Strategy'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-1F: The Cyber Security program strategy is approved by senior management',
          'requirement_description': 'Has your Cyber Security strategy been socialised and endorsed/approved by senior '
                                     'management? Who provides this approval may differ between organisations depending on '
                                     'where Cyber Security sits within the organisational structure. Regardless of who '
                                     'provides this approval, the key outcome should be that the Cyber Security program as '
                                     'defined in the strategy is backed by senior leadership and provided with sufficient '
                                     'support in the way of funding, resource allocation and advocacy. CPM-1a must be '
                                     'completed as a pre-requisite for this practice.',
          'subchapter': 'CPM-1: Establish Cyber Security Program Strategy'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-1G: The Cyber Security program strategy is updated to reflect business changes, changes in '
                             'the operating environment, and changes in the threat profile (TVM-1d)',
          'requirement_description': 'How often is your Cyber Security strategy refreshed? When it was last reviewed and '
                                     'updated, did you take into account the following:\n'
                                     " -Changes in your organisation's structure or activities;\n"
                                     ' -Changes in the Cyber threat environment;\n'
                                     ' -Changes in the regulatory environment.\n'
                                     '\n'
                                     'Periodically updating the Cyber Security strategy in response to the above drivers '
                                     'enables an organisation to ensure that its Cyber Security activities/functions '
                                     'continually evolve to address the threats and risks facing the organisation.',
          'subchapter': 'CPM-1: Establish Cyber Security Program Strategy'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2A: Resources (people, tools, and funding) are provided, at least in an ad hoc manner, to '
                             'support the Cyber Security program',
          'requirement_description': 'Do you have staff and funding dedicated to your Cyber Security team/function?',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2B: Senior management provides sponsorship for the Cyber Security program, at least in an ad '
                             'hoc manner',
          'requirement_description': 'Do leaders in your organisation generally recognise and communicate the importance of '
                                     'Cyber Security activities/functions within the organisation?',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2C: The Cyber Security program is established according to the Cyber Security program '
                             'strategy',
          'requirement_description': 'Does your organisation implement, operate and manage Cyber Security activities/functions '
                                     'in alignment with those defined in the Cyber Security strategy? CPM-1a and CPM-2a must '
                                     'be completed as a pre-requisite for this practice.\n'
                                     '\n'
                                     'Completing this practice ensures that the Cyber Security program of work can achieve the '
                                     'objectives and priorities that it is expected to, according the Cyber Security program '
                                     'strategy.',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2D: Adequate funding and other resources (i.e., people and tools) are provided to establish '
                             'and operate a Cyber Security program aligned with the program strategy',
          'requirement_description': 'Building on CPM-2b, does your organisation allocate dedicated funding to ensure that the '
                                     'Cyber Security strategy can be implemented in its entirety? Do you have the right '
                                     'people, technology and resources to sustain your Cyber Security program of work? CPM-1a '
                                     'and CPM-2a must be completed as a pre-requisite for this practice.',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2E: Senior management sponsorship for the Cyber Security program is visible and active '
                             '(e.g., the importance and value of Cyber Security activities is regularly communicated by senior '
                             'management)',
          'requirement_description': 'Do leaders in your organisation actively champion the importance of Cyber Security '
                                     'within the business? Support in this context could include:\n'
                                     ' -Communicating the importance of Cyber Security in company-wide newsletters or '
                                     'executive communications;\n'
                                     ' -Providing executive support and funding for Cyber Security awareness initiatives;\n'
                                     ' -Driving positive Cyber Security behaviours within their respective business '
                                     'teams/functions (outside of the core Cyber Security function);\n'
                                     '\n'
                                     'CPM-2a must be completed as a pre-requisite for this practice.',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2F: If the organisation develops or procures software, secure software development practices '
                             'are sponsored as an element of the Cyber Security program',
          'requirement_description': 'Are there teams within your organisation that develop software or implement '
                                     'custom-developed (i.e. not COTS) software? If so, is your Cyber Security function '
                                     'actively involved in those software development/procurement activities to ensure that '
                                     'Cyber Security requirements are identified and understood, and that associated risks are '
                                     'adequately managed? This involvement may be as simple as providing guidance on secure '
                                     'software development practices, or as involved as embedding Security assessments within '
                                     'software development processes (e.g. source code reviews, penetration testing, etc.). \n'
                                     '\n'
                                     ' Embedding Security into software development and procurement activities helps to reduce '
                                     "the risk of Security vulnerabilities being introduced into an organisation's technology "
                                     'environment. Refer to CPM-4: Perform Secure Software Development for more detail.',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2G: The development and maintenance of Cyber Security policies is sponsored',
          'requirement_description': 'Has your organisation assigned accountabilities, resources and support to ensure that '
                                     'Cyber Security policies are documented, periodically updated and communicated within the '
                                     'organisation? \n'
                                     '\n'
                                     'Cyber Security policies should support the Cyber Security strategy by defining '
                                     'principles-based requirements for implementing, operating and improving Cyber Security '
                                     'capabilities and controls throughout an organisation.',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2H: Responsibility for the Cyber Security program is assigned to a role with requisite '
                             'authority',
          'requirement_description': 'Has the management of your Cyber Security program been specifically assigned to someone? '
                                     'If so, does this person operate in a role or at a level of seniority that carries the '
                                     'appropriate authority to execute the program of work? Responsibility for executing and '
                                     'managing aspects of the Cyber Security program may be distributed across a number of '
                                     'different functions within an organisation, but one person should ultimately be '
                                     'accountable for the program overall. CPM-2a must be completed as a pre-requisite for '
                                     'this practice.\n'
                                     '\n'
                                     ' The Cyber Security program will typically be owned by one of the following roles within '
                                     'an organisation: \n'
                                     ' -Chief Information Security Officer (CISO)\n'
                                     ' -Cyber Security Manager\n'
                                     ' -Cyber Security Program Manager',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2I: The performance of the Cyber Security program is monitored to ensure it aligns with the '
                             'Cyber Security program strategy',
          'requirement_description': 'Does the organisation periodically assess its Cyber Security function and program of '
                                     'work to ensure it is delivering against the objectives identified in the overarching '
                                     'strategy? \n'
                                     '\n'
                                     ' This may include the use of formal metrics, monitoring and reporting. Another example '
                                     'may include an organisation conducting an holistic assessment of its Cyber Security '
                                     'capabilities and controls to identify areas for improvement. \n'
                                     '\n'
                                     "Completing this practice ensures that the organisation's Cyber Security activities "
                                     'ultimately progress towards the desired state.',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2J: The Cyber Security program is independently reviewed (i.e., by reviewers who are not in '
                             'the program) for achievement of Cyber Security program objectives',
          'requirement_description': 'Does your organisation conduct independent (internal or external) reviews of the Cyber '
                                     'Security program? If so, does this review consider whether Cyber Security program '
                                     'objectives have been met?\n'
                                     '\n'
                                     'Independent reviews are particularly useful in that they provide an unbiased opinion on '
                                     "the level of success of an organisation's Cyber Security program.",
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2K: The Cyber Security program addresses and enables the achievement of regulatory '
                             'compliance as appropriate',
          'requirement_description': 'Is your organisation subject to any technology-related regulatory requirements that '
                                     'impact (or are supported by) Cyber Security activities/functions? Examples may include:\n'
                                     ' -Market license conditions;\n'
                                     ' -Notifiable Data Breaches scheme (NDB);\n'
                                     ' -Australian Privacy Act;\n'
                                     ' -General Data Protection Regulation (GDPR);\n'
                                     ' -PCI-DSS.\n'
                                     '\n'
                                     'If so, has your organisation identified these requirements and captured them in a way '
                                     'that they can be managed and assessed for compliance? This may take the form of a '
                                     'technology legal/regulatory compliance program.',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-2L: The Cyber Security program monitors and/or participates in selected industry Cyber '
                             'Security standards or initiatives',
          'requirement_description': "Does your organisation's Cyber Security program seek alignment with particular industry "
                                     'standards? Examples may include: \n'
                                     ' -ISO/IEC 27001\n'
                                     ' -NIST SP 800-53\n'
                                     ' -ISA 62443\n'
                                     '\n'
                                     ' Alternatively, does your organisation seek to participate in the development and review '
                                     'of such standards, or other industry-led Cyber Security forums / working groups?',
          'subchapter': 'CPM-2: Sponsor Cyber Security Program'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': "CPM-3A: A strategy to architecturally isolate the organisation's IT systems from OT systems is "
                             'implemented, at least in an ad hoc manner',
          'requirement_description': 'Has your organisation attempted to segregate its IT and OT environments in any way? This '
                                     'could include physical segregation (i.e. using separate hardware and equipment), or '
                                     'logical segregation (i.e. via locating systems in separate network zones with access '
                                     'controls enforced between zones).\n'
                                     '\n'
                                     'When assessing network segregation activities, consider the following;\n'
                                     ' -Is any aspect of your Operational Technology (OT) or Industrial Control Systems (ICS) '
                                     'directly accessible from the Internet (e.g. via a web portal)?\n'
                                     ' -Is there any network connectivity between your OT / ICS environment and your IT '
                                     'environment?\n'
                                     ' -Where you operate other services (e.g. Telecommunications, Data Centres), is there any '
                                     'network connectivity between these services and your OT / ICS / IT environments?',
          'subchapter': 'CPM-3: Establish and Maintain Cyber Security Architecture'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-3B: A Cyber Security architecture is in place to enable segmentation, isolation, and other '
                             'requirements that support the Cyber Security strategy',
          'requirement_description': 'Has your organisation implemented Cyber Security controls to enforce the segregation of '
                                     'IT and OT environments (refer CPM-3a)? These controls may include network segmentation '
                                     'and access control, network traffic filtering, identity & access management, etc. CPM-3a '
                                     'must be completed as a pre-requisite for this practice.',
          'subchapter': 'CPM-3: Establish and Maintain Cyber Security Architecture'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-3C: Architectural segmentation and isolation is maintained according to a documented plan',
          'requirement_description': 'Has your organisation documented a Cyber Security architecture (aka Enterprise Security '
                                     'Architecture) to inform the segregation of IT and OT environments in CPM-3a? A Cyber '
                                     'Security architecture typically defines a logical Security zone model, the Security '
                                     'services available within each zone, and the Security controls to be applied to systems '
                                     'and communications within (and between) these Security zones. CPM-3a must be completed '
                                     'as a pre-requisite for this practice.',
          'subchapter': 'CPM-3: Establish and Maintain Cyber Security Architecture'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-3D: Cyber Security architecture is updated at an organisation-defined frequency to keep it '
                             'current',
          'requirement_description': 'Does your organisation update the Cyber Security architecture (documented in CPM-3c) at '
                                     'a defined interval? \n'
                                     '\n'
                                     'Cyber Security architectures should be reviewed and updated periodically to ensure they '
                                     'continue to adequately address the relevant Cyber threats and risks facing an '
                                     'organisation.',
          'subchapter': 'CPM-3: Establish and Maintain Cyber Security Architecture'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-4A: Software to be deployed on assets that are important to the delivery of the function is '
                             'developed using secure software development practices',
          'requirement_description': 'Before deploying new/changed software to technology assets that support critical '
                                     'business functions, does your organisation seek to gain comfort that the software has '
                                     'been developed securely, and that its deployment will not introduce any Security '
                                     'weakness/vulnerability into the asset? This may involve performing a range of Cyber '
                                     'Security activities, including:\n'
                                     ' -Embedding secure software development principles into the software development '
                                     'lifecycle;\n'
                                     ' -Source code reviews;\n'
                                     ' -Automated code testing (e.g. fuzzing);\n'
                                     ' -Vulnerability scanning or penetration testing.\n'
                                     '\n'
                                     ' Embedding Security into software development and procurement activities helps to reduce '
                                     "the risk of Security vulnerabilities being introduced into an organisation's technology "
                                     'environment.',
          'subchapter': 'CPM-4: Perform Secure Software Development'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-4B: Policies require that software that is to be deployed on assets that are important to '
                             'the delivery of the function be developed using secure software development practices',
          'requirement_description': 'Has your organisation defined formal policy requirements that any software which will be '
                                     'deployed to critical technology assets is developed securely and subject to Cyber '
                                     'Security assessment (refer CPM-4a)?\n'
                                     '\n'
                                     'Defining requirements in policy helps to drive the implementation and enforcement of '
                                     'behaviours within an organisation.',
          'subchapter': 'CPM-4: Perform Secure Software Development'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-AP1: Operational assets can route traffic directly to the Internet',
          'requirement_description': 'If an operational asset (such as a network, system, or application) has the ability to '
                                     'route traffic directly to the Internet, a malicious threat actor may be able to utilise '
                                     'that connection to access, and gain remote control of that asset without your knowledge '
                                     'or consent.\n'
                                     '\n'
                                     'Direct Internet access refers to access that is uncontrolled or circumvents network '
                                     'security controls. An example of direct Internet access includes any instances where '
                                     'operational assets (including field devices) have been equipped with an uncontrolled '
                                     'cellular data connection.\n'
                                     '\n'
                                     'You should consider defence-in-depth approaches when securing operational assets. This '
                                     'may include the complete segregation of network traffic between operational assets and '
                                     'other technology assets.',
          'subchapter': 'CPM-AP: CPM Anti-Patterns'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-AP2: Remote or third-party access to assets circumvents network security controls',
          'requirement_description': 'Building on CPM-AP1, you should apply defence-in-depth approaches when securing '
                                     'operational assets. This should be consistently applied for all types of identities '
                                     '(users) and levels of access.\n'
                                     '\n'
                                     'For example, operational assets (including field devices) that are equipped with '
                                     'cellular connections to enable direct remote support over the Internet may indicate that '
                                     'remote access or third-party access to that asset circumvents your network security '
                                     'controls.\n'
                                     '\n'
                                     'Remote access or third-party access may represent a higher risk to your organisation, so '
                                     'it is important that network security controls are applied consistently.',
          'subchapter': 'CPM-AP: CPM Anti-Patterns'},
         {'chapter_title': 'CPM: Cybersecurity Program Management',
          'conformity_questions': [],
          'objective_title': 'CPM-AP3: Critical assets cannot be isolated from non-critical assets in response to a cyber '
                             'security threat or incident',
          'requirement_description': 'In the event of a serious cyber security incident, having the ability to isolate '
                                     'critical assets (such as networks, systems, and applications required to continue '
                                     'operating important business functions) from other non-critical assets may be required '
                                     'to protect against the propagation of malware or other threats.',
          'subchapter': 'CPM-AP: CPM Anti-Patterns'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-1A: Important IT and OT supplier dependencies are identified (i.e., external parties on '
                             'which the delivery of the function depend, including operating partners), at least in an ad hoc '
                             'manner',
          'requirement_description': 'Are you aware of any external vendors who the organisation is dependant on for the '
                                     'management, operation or support of business-critical IT or OT systems?',
          'subchapter': 'EDM-1: Identify Dependencies'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-1B: Important customer dependencies are identified (i.e., external parties that are '
                             'dependent on the delivery of the function including operating partners), at least in an ad hoc '
                             'manner',
          'requirement_description': 'Are you aware of any external parties who are heavily dependent on your organisation? '
                                     'Examples may include critical energy customers, telecommunications networks, '
                                     'organisations which co-locate equipment in your data centre, etc.',
          'subchapter': 'EDM-1: Identify Dependencies'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-1C: Supplier dependencies are identified according to established criteria',
          'requirement_description': 'Have you established specific criteria by which you can identify external vendors who '
                                     'the organisation is dependant on for the management, operation or support of '
                                     'business-critical IT or OT systems?\n'
                                     '\n'
                                     " This activity is commonly performed within an organisation's Vendor/Category Management "
                                     'function.\n'
                                     '\n'
                                     ' EDM-1a must be completed as a pre-requisite for this practice.',
          'subchapter': 'EDM-1: Identify Dependencies'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-1D: Customer dependencies are identified according to established criteria',
          'requirement_description': 'Have you established specific criteria by which you can identify external parties who '
                                     'are heavily dependant on your organisation? \n'
                                     '\n'
                                     ' EDM-1b must be completed as a pre-requisite for this practice.\n'
                                     '\n'
                                     'Completing this practice ensures that an organisation can consistently identify its '
                                     'downstream customer/partner dependencies.',
          'subchapter': 'EDM-1: Identify Dependencies'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-1E: Single-source and other essential dependencies are identified',
          'requirement_description': 'Are any of your external vendor dependencies (refer EDM-1a and EDM-1c) known to be a '
                                     'single point of failure for a critical business function within your organisation? '
                                     'Examples of a single point of failure may include:\n'
                                     ' -You have implemented technology assets that are only able to be supported or '
                                     'maintained by a single vendor;\n'
                                     ' -Your organisation operates in a location that is serviced by a single provider of a '
                                     'given service (e.g. electricity supply, internet provider, etc.).',
          'subchapter': 'EDM-1: Identify Dependencies'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-1F: Dependencies are prioritised',
          'requirement_description': 'Once external dependencies have been identified, are these prioritised in any way? Does '
                                     'the organisation know which suppliers and customers are most important/critical to the '
                                     'function? \n'
                                     '\n'
                                     'Prioritisation may include an assessment of potential impacts to the business should the '
                                     'third party cease to operate or their services become unavailable for a period of time. '
                                     'This prioritisation may be directly or indirectly informed by how an organisation '
                                     'prioritises its assets, for example a vendor that supports a business-critical asset may '
                                     'in turn be considered a business-critical vendor. \n'
                                     '\n'
                                     ' EDM-1a or EDM-1b must be completed as a pre-requisite for this practice.',
          'subchapter': 'EDM-1: Identify Dependencies'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': "EDM-1G: Dependency prioritisation and identification are based on the function's or "
                             "organisation's risk criteria (RM-1c)",
          'requirement_description': 'Is the prioritisation of external dependencies (refer EDM-1f) informed by a risk '
                                     "assessment conducted in accordance with your organisation's risk management framework? \n"
                                     '\n'
                                     'Completing this practice enables an organisation to identify, assess and manage third '
                                     'party dependency risks in a consistent and structured manner.',
          'subchapter': 'EDM-1: Identify Dependencies'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2A: Significant Cyber Security risks due to suppliers and other dependencies are identified '
                             'and addressed, at least in an ad hoc manner',
          'requirement_description': 'Have you assessed the Security risks associated with your existing third party '
                                     'technology vendors and providers?\n'
                                     '\n'
                                     ' Third party Security risks may include (but are not limited to):\n'
                                     ' -Availability risk arising from third parties who may become unable to provide '
                                     'business-critical products or services;\n'
                                     ' -Integrity risk arising from inappropriate third party use of persistent remote '
                                     'access;\n'
                                     ' -Confidentiality and privacy risk arising from third parties who fail to securely store '
                                     'or process sensitive information.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2B: Cyber Security requirements are considered, at least in an ad hoc manner, when '
                             'establishing relationships with suppliers and other third parties',
          'requirement_description': 'When engaging with new external third parties, does your organisation consider whether '
                                     'the engagement will introduce any Cyber Security risks that need to be assessed and '
                                     'managed? Do you apply any Cyber Security requirements during the process of identifying, '
                                     'selecting and on boarding these third parties? \n'
                                     '\n'
                                     'Did you consider Security requirements when you engaged/on boarded your existing '
                                     'external technology vendors?',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2C: Identified Cyber Security dependency risks are entered into the risk register (RM-2j)',
          'requirement_description': "Do your organisation's Cyber Security risk registers (refer RM-2j) include any risks "
                                     'identified relating to the use of third party vendors? EDM-2a and RM-2j must be '
                                     'completed as a pre-requisite for this practice.\n'
                                     '\n'
                                     "Documenting third party risks in the organisation's Cyber Security risk register enables "
                                     'the tracking and management of those risks in accordance with established risk '
                                     'management procedures.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2D: Contracts and agreements with third parties incorporate sharing of Cyber Security threat '
                             'information',
          'requirement_description': 'When establishing any contract or agreement with a third party (e.g. software vendor, '
                                     'hardware vendor, contracted personnel), do you ensure that this includes provisions that '
                                     'require and enable the two parties to share Cyber threat information? EDM-2b must be '
                                     'completed as a pre-requisite for this practice.\n'
                                     '\n'
                                     'Completing this practice ensures that the business function or organisation has a '
                                     'contractual and legal right to be notified of Cyber Security events that involve your '
                                     'third party suppliers.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2E: Cyber Security requirements are established for suppliers according to a defined '
                             'practice, including requirements for secure software development practices where appropriate',
          'requirement_description': 'Building on EDM-2b, has your organisation defined formal Cyber Security requirements '
                                     'that must be considered when engaging new third party vendors? This may include specific '
                                     'requirements for different vendor types in accordance with the product/service they will '
                                     'be providing to the organisation.\n'
                                     '\n'
                                     ' EDM-2b must be completed as a pre-requisite for this practice.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2F: Agreements with suppliers and other external entities include Cyber Security '
                             'requirements',
          'requirement_description': "Building on EDM-2b, completing this practice ensures that an organisation's third party "
                                     'vendors are contractually obliged to operate and manage appropriate Cyber Security '
                                     'controls.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2G: Evaluation and selection of suppliers and other external entities includes consideration '
                             'of their ability to meet Cyber Security requirements',
          'requirement_description': 'Building on EDM-2b and 2e, does your organisation seek to understand whether new '
                                     'external third party vendors are able to meet your defined Cyber Security requirements? '
                                     'Is there a formal process for performing these assessment? \n'
                                     '\n'
                                     ' EDM-2b and EDM-2e must be completed as a pre-requisite for this practice.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2H: Agreements with suppliers require notification of Cyber Security incidents related to '
                             'the delivery of the product or service',
          'requirement_description': 'Similar to EDM-2d, when establishing a contract or agreement with an external third '
                                     'party (e.g. software vendor, hardware vendor, contracted personnel), do you ensure that '
                                     'this includes provisions for the third party to notify your organisation of any Cyber '
                                     'Security incidents affecting their operations?\n'
                                     '\n'
                                     'Completing this practice ensures that the business function or organisation has a '
                                     'contractual and legal right to be notified of Cyber Security incidents that involve your '
                                     'third party suppliers. \n'
                                     '\n'
                                     ' EDM-2f must be completed as a pre-requisite for this practice',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2I: Suppliers and other external entities are periodically reviewed for their ability to '
                             'continually meet the Cyber Security requirements',
          'requirement_description': 'Do you periodically assess your existing external third party vendors to ensure that '
                                     'they are meeting the Cyber Security requirements defined in the applicable '
                                     'contract/agreement? This assessment could be targeted at particular vendors based on '
                                     'their risk profile, or more broadly as part of an ongoing vendor management/governance '
                                     'function.\n'
                                     '\n'
                                     'Completing this practice ensures that the organisation maintains a current view of their '
                                     'external vendor risk profile, and is able to take any action required should that risk '
                                     "profile fall outside of the organisation's risk tolerance. \n"
                                     '\n'
                                     ' EDM-2b, and EDM-2f must be completed as a pre-requisite for this practice',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2J: Cyber Security risks due to external dependencies are managed according to the '
                             "organisation's risk management criteria and process",
          'requirement_description': 'Does your organisation apply the same risk management processes (e.g. risk '
                                     'identification, documentation, tracking, review and reporting) to external third party '
                                     'risks as it does to other categories of Cyber Security risk? \n'
                                     '\n'
                                     'Completing this practice ensures that an organisation is managing all types of Cyber '
                                     'Security risk consistently in accordance with defined processes and risk criteria (refer '
                                     'RM-1c).\n'
                                     '\n'
                                     ' EDM-2c, RM-1j and RM-1c must be completed as a pre-requisite for this practice.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2K: Cyber Security requirements are established for supplier dependencies based on the '
                             "organisation's risk criteria (RM-1c)",
          'requirement_description': 'Does your organisation identify and define third party Cyber Security requirements in a '
                                     'way that is linked to its assessment of third party Security risk identified in EDM-2j?\n'
                                     '\n'
                                     'For example, a risk assessment may identify a Confidentiality risk relating to a third '
                                     'party who stores or processes Personally Identifiable Information (PII) collected by '
                                     'your organisation. The outcome of this risk assessment may identify several Security '
                                     'controls that you require the third party to implement (e.g. encryption or tokenisation '
                                     'of data). \n'
                                     '\n'
                                     ' EDM-2e and RM-1c must be completed as a pre-requisite for this practice.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2L: Agreements with suppliers require notification of vulnerability-inducing product defects '
                             'throughout the intended life cycle of delivered products',
          'requirement_description': 'Do your contracts/agreements with external third parties require that they inform you if '
                                     'they become aware that one of their products/services (which they supply to your '
                                     'organisation) is affected by a Security vulnerability?',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2M: Acceptance testing of procured assets includes testing for Cyber Security requirements',
          'requirement_description': 'Prior to deploying new technology assets acquired from external third party vendors, '
                                     'organisations should test them to ensure that they will operate as expected and not have '
                                     "any adverse impact on the organisation's existing technology environment. \n"
                                     '\n'
                                     'Does your organisation perform such testing? If so, does this testing include assessment '
                                     'to identify any Cyber Security vulnerabilities or weaknesses?',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'EDM: Supply Chain and External Dependencies Management',
          'conformity_questions': [],
          'objective_title': 'EDM-2N: Information sources are monitored to identify and avoid supply chain threats (e.g., '
                             'counterfeit parts, software, and services)',
          'requirement_description': 'Does your organisation have processes in place to identify and respond to Cyber threats '
                                     'affecting its supply chain? This may include monitoring external threat intelligence '
                                     'sources (refer ISC-1a, TVM-1a, TVM-2a).\n'
                                     '\n'
                                     "State-sponsored Cyber threat actors are known to exploit organisations' technology "
                                     'supply chains in order to introduce Cyber Security vulnerabilities that can be exploited '
                                     'for the purposes of corporate espionage or malicious attack.',
          'subchapter': 'EDM-2: Manage Dependency Risk'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-1A: Identities are provisioned, at least in an ad hoc manner, for personnel and other '
                             'entities (e.g., services, devices) who require access to assets (note that this does not '
                             'preclude shared identities)',
          'requirement_description': 'Do you create user identities and accounts for people who need access to technology '
                                     'assets and systems within your organisation?\n'
                                     '\n'
                                     ' Any access to a technology asset should be able to be attributed to a specific user '
                                     'identity/account (even if the account is a system account or an account shared by '
                                     'multiple people), and ultimately to someone who is accountable for that '
                                     'identity/account.',
          'subchapter': 'IAM-1: Establish and Maintain Identities'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-1B: Credentials are issued, at least in an ad hoc manner, for personnel and other entities '
                             'that require access to assets (e.g., passwords, smart cards, certificates, keys)',
          'requirement_description': 'Do you seek to prevent unauthorised access to technology assets and systems using any of '
                                     'the following types of credentials?\n'
                                     ' -Passwords\n'
                                     ' -PIN codes\n'
                                     ' -Digital certificates\n'
                                     ' -Physical tokens\n'
                                     ' -Smart Cards\n'
                                     ' -Biometrics',
          'subchapter': 'IAM-1: Establish and Maintain Identities'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-1C: Identities are deprovisioned, at least in an ad hoc manner, when no longer required',
          'requirement_description': 'Do you disable/remove user identities and accounts that are associated with personnel '
                                     'who no longer require them (e.g. due to employment termination)?',
          'subchapter': 'IAM-1: Establish and Maintain Identities'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-1D: Identity repositories are periodically reviewed and updated to ensure validity (i.e., to '
                             'ensure that the identities still need access)',
          'requirement_description': 'Do you review identity repositories (e.g. Active Directory, or a dedicated Identity '
                                     'Management system) to ensure they are still current? If these reviews highlight '
                                     'identities which are no longer required (e.g. a user has left the organisation but their '
                                     'identity and accounts are still active), do you update the repository (e.g. by disabling '
                                     'or removing the identity)?\n'
                                     '\n'
                                     ' As the source of truth for who has access to technology networks and systems within '
                                     "your organisation, it's important that identity repositories are kept accurate and "
                                     'up-to-date. Completing this practice is required to support access management activities '
                                     'in the next objective, IAM-2.',
          'subchapter': 'IAM-1: Establish and Maintain Identities'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-1E: Credentials are periodically reviewed to ensure that they are associated with the '
                             'correct person or entity',
          'requirement_description': 'Do you check that access credentials (e.g. accounts, smart cards, certificates, keys or '
                                     'other credentials from IAM-1b) are linked to the right identity/user? Do you do this at  '
                                     'a defined interval (i.e. periodically)?\n'
                                     '\n'
                                     'Credentials are essential to controlling and restricting access to assets and systems. '
                                     'Completing this practice enables an organisation to ensure that credentials (and by '
                                     'extension the access that they grant) are assigned to the right individuals and '
                                     'entities.',
          'subchapter': 'IAM-1: Establish and Maintain Identities'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-1F: Identities are deprovisioned within organisationally defined time thresholds when no '
                             'longer required',
          'requirement_description': 'Building on IAM-1d, once it is known that an identity no longer requires access (e.g. '
                                     'due to a user having left the organisation), do you deprovision (i.e. disconnect, '
                                     'disable or remove) that identity within a certain timeframe (e.g. 48 hours)? Have you '
                                     'defined the required deprovisioning timeframes for different types of access (e.g. '
                                     'Active Directory / network access, remote access, email accounts, mobile device '
                                     'accounts, etc.)?\n'
                                     '\n'
                                     'Completing this practice enables an organisation to ensure that access is removed in a '
                                     'timely manner from individuals and entities that no longer require it.',
          'subchapter': 'IAM-1: Establish and Maintain Identities'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': "IAM-1G: Requirements for credentials are informed by the organisation's risk criteria (e.g., "
                             'multifactor credentials for higher risk access) (RM-1c)',
          'requirement_description': 'Do you implement stronger authentication controls for access to higher-risk technology '
                                     'assets and systems? Such controls may include: \n'
                                     ' -Requiring passwords to be longer and more complex than normal;\n'
                                     ' -Requiring multi-factor authentication (e.g. password + one-time PIN);\n'
                                     ' -Limiting the time that successful authentication events are valid for. \n'
                                     '\n'
                                     "If so, are higher-risk assets and systems identified using the organisation's defined "
                                     'risk criteria?',
          'subchapter': 'IAM-1: Establish and Maintain Identities'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2A: Access requirements, including those for remote access, are determined',
          'requirement_description': 'Establishing organisational and function-specific access requirements is critical. '
                                     'Access can be either:\n'
                                     ' -physical, such as a person entering and being physically present in a location, and '
                                     '(or);\n'
                                     ' -logical, such as an identity (user) logging in to (accessing) assets (such as '
                                     'networks, systems, and applications).\n'
                                     '\n'
                                     ' Has your organisation determined: \n'
                                     '1) Who should have access to specific technology and operational assets, and;\n'
                                     '2) How these assets should be accessed?',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2B: Access is granted to identities, at least in an ad hoc manner, based on requirements',
          'requirement_description': 'Before giving someone access to a technology asset or system, do you first identify '
                                     'whether there is a genuine requirement for that person to have that access?',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2C: Access is revoked, at least in an ad hoc manner, when no longer required',
          'requirement_description': 'When a person no longer requires access to a particular asset (such as a network, '
                                     'system, or application), do you disable and remove that specific access? Additionally, '
                                     'do you ensure that physical access granted through keys etc. is revoked (by ensuring the '
                                     'key is returned to its custodian)?\n'
                                     '\n'
                                     'In addition to revoking general access and disabling associated identities (users) when '
                                     "an individual's employment is terminated, this practice also involves disabling and "
                                     'removing access to specific assets (e.g. if a user changes roles within an organisation '
                                     'and no longer required it).\n'
                                     '\n'
                                     'Where an identity (user) record directly provides access to assets (e.g. an Active '
                                     'Directory account), deprovisioning the identity would remove associated general access '
                                     'to assets, satisfying the intent of this practice.',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2D: Access requirements incorporate least privilege and separation of duties principles',
          'requirement_description': 'Do you give people the least amount of access that they need to perform their role? \n'
                                     '\n'
                                     'Do you identify particular combinations of access that might result in a conflict of '
                                     'interest scenario (e.g. the ability to create a request and approve that same request), '
                                     'and seek to prevent people from being given that type of access?',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2E: Access requests are reviewed and approved by the asset owner',
          'requirement_description': 'When someone requests access to an asset or system, does someone else with authority '
                                     'over that system (e.g. asset owner, business application owner, etc.) review and approve '
                                     'the request before the access is provided?',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2F: Root privileges, administrative access, emergency access, and shared accounts receive '
                             'additional scrutiny and monitoring',
          'requirement_description': 'These types of access pose a greater Cyber Security risk to an organisation, and as such '
                                     'they should be subject to stronger Security controls, including (where feasible and '
                                     'deemed appropriate):\n'
                                     ' -Additional approvals required (e.g. Line Manager AND System Owner) prior to access '
                                     'being provisioned;\n'
                                     ' -More frequent revalidation of user access;\n'
                                     ' -Longer and more complex passwords;\n'
                                     ' -Multi-factor authentication;\n'
                                     ' -Time-limited access sessions (e.g. via forced session timeout);\n'
                                     ' -More detailed and granular Security event logging;\n'
                                     ' -Monitoring for specific Security events associated with misuse of privileged access.',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2G: Access privileges are reviewed and updated to ensure validity, at an organisationally '
                             'defined frequency',
          'requirement_description': 'Does your organisation periodically review the existing access granted to people to '
                                     'determine whether they still require that access? \n'
                                     '\n'
                                     'If your organisation only performs these reviews in an ad-hoc manner (i.e. not in '
                                     'accordance with a defined frequency/schedule), this practice is considered incomplete.',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2H: Access to assets is granted by the asset owner based on risk to the function',
          'requirement_description': 'Building on IAM-2e, does the asset/system owner use risk management guidance from RM-1 '
                                     'and RM-2 to approve or deny access requests? IAM-2e must be completed as a pre-requisite '
                                     'for this practice.\n'
                                     '\n'
                                     ' Adopting a risk-based approach toward approving or denying access requests enables an '
                                     'organisation to manage access to systems within its risk tolerance/threshold.',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-2I: Anomalous access attempts are monitored as indicators of Cyber Security events',
          'requirement_description': 'As part of the Security event logging and monitoring performed in SA-1a, do you log and '
                                     'monitor unusual/suspicious access attempts? Examples may include:\n'
                                     ' -A large number of repeated unsuccessful authentication attempts in a short space of '
                                     'time (an indicator of a brute-force attack taking place);\n'
                                     ' -Authentication events outside of normal business hours (or outside of an established '
                                     'baseline of normal behaviour).\n'
                                     '\n'
                                     ' This practices supports the effectiveness of the Common Operating Picture (COP) in '
                                     'SA-3.',
          'subchapter': 'IAM-2: Control Access'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP1: Identities (users) are created, and access to assets is provisioned, before confirming '
                             'if the identity (user) has a genuine need for access',
          'requirement_description': 'Identities (users) are the means used to enable access to assets (such as networks, '
                                     'systems, and applications).\n'
                                     '\n'
                                     'It is important that access provisioning follows the principle of least privilege. This '
                                     'means it is important that:\n'
                                     '(a) identities (users) are only created for individuals with a genuine business need for '
                                     'access, and;\n'
                                     '(b) access is only provisioned to identities (users) after the requirement for the level '
                                     'of access has been established.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP2: A complete and current register of identities (users) with privileged access is not '
                             'maintained',
          'requirement_description': 'Privileged access, such as an administrator account, represents a higher level of risk '
                                     'to the function, given the potential for an administrator to make broad and irreversible '
                                     'changes to assets (such as networks, systems, and applications).\n'
                                     '\n'
                                     ' To support privileged access management activities, you should:\n'
                                     ' -Ensure that identities (users) provisioned privilege access are recorded within a '
                                     'privileged access register maintained separately from the master access control lists '
                                     'retained on individual assets;\n'
                                     ' -Automate and optimise the steps taken to ensure that the register of identities '
                                     '(users) with privileged access is maintained; and\n'
                                     ' -Establish a periodicity within which privileged access reviews are to be completed '
                                     'with reference the register.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP3: Identity (user) deprovisioning is not informed and supported by organisational risk '
                             'criteria (RM-1C)',
          'requirement_description': 'RM-1C must be at least Partially Implemented for this Anti-Pattern to be Not Present.\n'
                                     '\n'
                                     'Deprovisioning of access (both at the point of employment termination and with a role '
                                     'change) should follow a defined process that includes consideration of organisational '
                                     'risk criteria.\n'
                                     '\n'
                                     ' This may include:\n'
                                     ' -Deprovisioning privileged access as a priority;\n'
                                     ' -Validating that all access to critical assets is deprovisioned\n'
                                     ' -Ensuring that identities (users) in Active Directory do not remain active '
                                     'indefinitely;\n'
                                     ' -Expediting the deprovisioning of access under extenuating circumstances surrounding '
                                     'employment termination.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP4: Non-public, Internet-facing assets can be accessed using single-factor authentication',
          'requirement_description': 'Providing remote access to any type of asset over the Internet is risky, and should not '
                                     'be taken lightly. A common method of reducing this risk is to use multi-factor '
                                     'authentication.\n'
                                     '\n'
                                     'Multi-factor authentication often involves the use of passphrases in addition to one or '
                                     'more of the following multi-factor authentication methods every time a user logs into an '
                                     'asset:\n'
                                     ' -Universal 2nd Factor (U2F) security keys;\n'
                                     ' -physical one-time PIN (OTP) tokens;\n'
                                     ' -biometrics;\n'
                                     ' -smartcards;\n'
                                     ' -mobile apps;\n'
                                     ' -Short Message Service (SMS) messages, emails or voice calls, or;\n'
                                     ' -software certificates.\n'
                                     '\n'
                                     'If an authentication method at any time offers a user the ability to reduce the number '
                                     'of authentication factors to a single factor it is by definition no longer a '
                                     'multi-factor authentication method. A common example of this is when a user is offered '
                                     "the ability to 'remember this computer' for a public web resource.\n"
                                     '\n'
                                     ' The Australian Cyber Security Centre (ACSC) recommends the use of multi-factor '
                                     'authentication as one of their Essential Eight strategies to Mitigate Cyber Security '
                                     'Incidents - advising that it is one of the most effective controls that an organisation '
                                     'can implement to prevent an adversary from gaining access to an asset.\n'
                                     'Source: ACSC Implementing Multi-Factor Authentication',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP5: Privileged access to one or more assets is provisioned by default',
          'requirement_description': 'Privileged access to assets (such as networks, systems, and applications) enables '
                                     'identities (users) to bypass security controls and can cause more severe impact to the '
                                     'business if the account is compromised or misused (including accidentally).\n'
                                     '\n'
                                     ' As a result, it is important that access provisioning follows the principle of least '
                                     'privilege. This means that identities (users) should only be granted privileged access '
                                     'following validation of a genuine business need, and not by default.\n'
                                     '\n'
                                     'For example, if an identity (user) is provisioned with administrator access on their '
                                     'corporate computer by default, that would indicate that this Anti-Pattern is Present.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP6: Identities (users) have been provisioned with access to assets which breaches a '
                             'segregation of duties requirement',
          'requirement_description': 'Segregation of duties is an important access control principle designed to prevent '
                                     'identities (users) from bypassing validation and verification checks when performing '
                                     'actions, and significantly limits the potential for unauthorised activity.\n'
                                     '\n'
                                     'Segregation of duty violations must be identified and mitigated, given the increased '
                                     'risk that they present to business activities.\n'
                                     '\n'
                                     ' Example activities that indicate this Anti-Pattern is Present include:\n'
                                     ' -if an identity (user) has the ability to both create and approve a request for access '
                                     'to assets (such as networks, systems, and applications), or;\n'
                                     ' -if an employee has the ability to request and approve a configuration change to a '
                                     'critical asset.\n'
                                     'For both of these examples, segregation of duties would suggest that another employee or '
                                     'process be inserted between the create/request and approve actions to ensure that there '
                                     'has been sufficient oversight.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP7: Identities (users) cannot be individually identified and attributed to a person',
          'requirement_description': 'Organisations need to be able to uniquely identify individuals who use assets (such as '
                                     'networks, systems, and applications) relevant to the function. This involves '
                                     'consideration of the principles of attribution and non-repudiation.\n'
                                     '\n'
                                     'Without the ability to distinguish identities (users) between individuals, anonymous '
                                     'users can perform malicious or illegal activity without their actions being linked back '
                                     'to them.\n'
                                     '\n'
                                     'For the context of this Anti-Pattern:\n'
                                     ' -service accounts should be considered, and each service account should be associated '
                                     'with (owned by) an individual.\n'
                                     ' -generic accounts can still be utilised provided a secondary means of attribution '
                                     'exists for any actions performed (eg via privileged session management controls).',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP8: Unusual or suspicious access to assets is not monitored by security monitoring '
                             'solutions',
          'requirement_description': 'Identities (users) are the means used to provision access to assets (such as networks, '
                                     'systems, and applications). It is important that security monitoring solutions, such as '
                                     'a SIEM (Security Information and Event Management) tool, are actively used to monitor '
                                     'identities (users) for suspicious or unusual activity.\n'
                                     '\n'
                                     ' This may include consideration of behavioural trends such as: \n'
                                     ' -Identities (users) authenticating from overseas locations where the organisation does '
                                     'not have a presence;\n'
                                     ' -Volumes of unsuccessful authentication attempts (either in short bursts, or over a '
                                     'longer period of time); and\n'
                                     ' -The time of day (or night) that the identity (user) is active.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP9: Unknown or unauthorised identities (users) and assets can connect to known assets',
          'requirement_description': 'Each identity (user) should be authorised before being provisioned with access to assets '
                                     '(such as networks, systems, and applications).\n'
                                     '\n'
                                     ' This excludes Guest wireless network access, which provides Internet access only, and '
                                     'does not allow access to other organisational assets.\n'
                                     '\n'
                                     " An example of an unauthorised asset is an employee's personal computer that is not "
                                     'managed by the function. Remote desktop access from an unauthorised asset should be '
                                     'considered when assessing this Anti-Pattern.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP10: The continued need for an identity (user) to have access to an asset is not validated '
                             'when identity (user) repositories are reviewed',
          'requirement_description': 'The objective of a user access review is to assess the appropriateness of access that '
                                     'has been provisioned to identities (users). It also involves checking whether any access '
                                     'to assets (such as networks, systems, and applications) is commensurate with their role '
                                     'and duties within the function.\n'
                                     '\n'
                                     ' Access reviews should follow the principle of least privilege, and complete access '
                                     'validation beyond a basic check of whether the individual associated with an identity '
                                     '(user) is still employed by the function.\n'
                                     '\n'
                                     'For example, if the review only checks whether the user is still active within the '
                                     'organisation, and not whether there is a continued need for the access, that would '
                                     'indicate that this Anti-Pattern is Present.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IAM: Identify and Access Management',
          'conformity_questions': [],
          'objective_title': 'IAM-AP11: Identities (users) are not prohibited (by organisational policy) from connecting to '
                             'critical assets using unknown or unauthorised assets',
          'requirement_description': 'In addition to logical and physical access controls (IAM-AP9), organisational policy '
                                     'should make it clear to personnel that they are prohibited from accessing critical '
                                     'assets using unknown or unauthorised assets.\n'
                                     '\n'
                                     " An example of an unauthorised asset is an employee's personal computer that is not "
                                     'managed by the function. Remote desktop access from an unauthorised asset should be '
                                     'considered when assessing this Anti-Pattern.\n'
                                     '\n'
                                     'Note that by design, some platforms such as Microsoft Outlook Web Access are intended to '
                                     'be accessed on non-managed devices. Such use cases should not affect the assessment of '
                                     'this Anti-Pattern.',
          'subchapter': 'IAM-AP: IAM Anti-Patterns'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1A: There is a point of contact (person or role) to whom Cyber Security events could be '
                             'reported',
          'requirement_description': 'Have people in your organisation been told who they should contact if they suspect or '
                                     'identify a Cyber Security event/incident? Examples may include the IT Service Desk, an '
                                     'Incident Manager or a dedicated Security email inbox.',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1B: Detected Cyber Security events are reported, at least in an ad hoc manner',
          'requirement_description': 'Do people speak up when they suspect or identify a Cyber Security event/incident? This '
                                     'may include:\n'
                                     ' -A user calling the IT Service Desk to report a spam email;\n'
                                     ' -A user notifying a member of the Cyber Security team of suspicious system behaviour;\n'
                                     ' -An anti-virus agent generating an alert when it detects a malware infection;\n'
                                     ' A Security monitoring solution generating an automated alert when it detects '
                                     'suspicious/malicious network traffic.',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1C: Cyber Security events are logged and tracked, at least in an ad hoc manner',
          'requirement_description': 'When a perceived or real Cyber Security event is reported (e.g. to the point of contact '
                                     'in IR-1a), is the event recorded somewhere and followed up?',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1D: Criteria are established for Cyber Security event detection (e.g., what constitutes an '
                             'event, where to look for events)',
          'requirement_description': 'Has your organisation defined and documented what it considers to be a Cyber Security '
                                     'event worth knowing about, and where these events can be identified from? This '
                                     'information may be defined in a Security Event Logging and Monitoring Standard. \n'
                                     'Note that once Security event types are defined, their detection is often facilitated by '
                                     'technology-driven solutions such as:\n'
                                     ' -Endpoint protection agents;\n'
                                     ' -Host-based and network-based IDS/IPS;\n'
                                     ' -System-generated Security event logging (e.g. Windows event log, Unix Syslog, etc.).\n'
                                     '\n'
                                     ' This practice is interdependent with Situational Awareness practices such as SA-1a and '
                                     'SA-2a, in that Cyber Security events may be identified from logging data. Upon '
                                     'investigation, a Security event may be escalated to a Security incident (refer IR-2a).',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1E: There is a repository where Cyber Security events are logged based on the established '
                             'criteria',
          'requirement_description': 'Once a Cyber Security event has been identified in accordance with the criteria '
                                     'established in IR-1d, is it recorded anywhere? This may involve someone manually '
                                     'recording an event, or a system generating a Security log that is stored locally on the '
                                     'device or sent to a centralised storage location (e.g. a Syslog server).\n'
                                     '\n'
                                     ' This practice is interdependent with Situational Awareness practices such as SA-1a and '
                                     'SA-2a.',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1F: Event information is correlated to support incident analysis by identifying patterns, '
                             'trends, and other common features',
          'requirement_description': 'When investigating a Security incident, are you able to analyse event logs from '
                                     'different sources across your technology environment to form a broader understanding of '
                                     'events? This practice is made easier when event logs are stored in a centralised '
                                     'location for the purpose of correlation (which may be automated by a SIEM solution). \n'
                                     '\n'
                                     'IR-1e must be completed as a pre-requisite for this practice.',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1G: Cyber Security event detection activities are adjusted based on information from the '
                             "organisation's risk register (RM-2j) and threat profile (TVM-1d) to help detect known threats "
                             'and monitor for identified risks',
          'requirement_description': 'Do you periodically review and update your Security event definitions (refer IR-1d) and '
                                     'subsequently your Security event logging configurations in alignment with your '
                                     "organisation's changing risk profile (refer RM-2j) and the broader Cyber threat "
                                     'environment (TVM-1d)?\n'
                                     '\n'
                                     'For example, if a specific type of Cyber threat became more prevalent in your industry '
                                     'sector, would you look to adjust your Security logging and monitoring to better identify '
                                     'events in your technology environment that could be indicators of that threat?',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-1H: The common operating picture for the function is monitored to support the identification '
                             'of Cyber Security events (SA-3a)',
          'requirement_description': 'Using the Common Operating Picture (COP) that you have implemented in SA-3a, do you have '
                                     'a process, procedure, or set of steps that are followed, to monitor the COP for events '
                                     'that may be Cyber Security events?\n'
                                     '\n'
                                     ' As per SA-3a, a COP is a consolidated view (i.e. "single pane of glass"") of the '
                                     'current state of Cyber Security operations within an organisation.\n'
                                     'SA-3a must be completed as a pre-requisite for this practice.."',
          'subchapter': 'IR-1: Detect Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2A: Criteria for Cyber Security event escalation are established, including Cyber Security '
                             'incident declaration criteria, at least in an ad hoc manner',
          'requirement_description': 'Has your organisation defined thresholds for when Cyber Security events need to be '
                                     'escalated for further investigation? This may include a certain number of events '
                                     'occurring in sequence (or within a given timespan), or specific event types occurring '
                                     'together. \n'
                                     '\n'
                                     ' Has your organisation defined what it considers to be a Cyber Security incident?',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2B: Cyber Security events are analysed, at least in an ad hoc manner, to support escalation '
                             'and the declaration of Cyber Security incidents',
          'requirement_description': 'When a perceived or real Cyber Security event is reported, does the point of contact '
                                     'from IR-1a follow the steps in IR-2a to investigate the event and declare an incident if '
                                     'the criteria are met?',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2C: Escalated Cyber Security events and incidents are logged and tracked, at least in an ad '
                             'hoc manner',
          'requirement_description': 'When a Cyber Security event has been escalated or declared an incident, is this recorded '
                                     'somewhere so it can be monitored, tracked and reported?',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2D: Criteria for Cyber Security event escalation, including Cyber Security incident criteria, '
                             'are established based on the potential impact to the function',
          'requirement_description': 'Building on IR-2a, are the Cyber Security event escalation thresholds and incident '
                                     'declaration criteria informed by an assessment of the potential adverse impact to the '
                                     'affected technology asset or system?\n'
                                     'IR-2a must be completed as a pre-requisite for this practice.\n'
                                     '\n'
                                     'Completing this practice enables an organisation to prioritise Cyber Security event and '
                                     'incident response activities based on their potential impact to the function.',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2E: Criteria for Cyber Security event escalation, including Cyber Security incident '
                             'declaration criteria, are updated at an organisation-defined frequency',
          'requirement_description': 'Has your organisation defined how often you should periodically review and update your '
                                     'Security event escalation criteria (refer IR-2a)?',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2F: There is a repository where escalated Cyber Security events and Cyber Security incidents '
                             'are logged and tracked to closure',
          'requirement_description': 'Where do you record active Cyber Security incidents? This may be an informal '
                                     'spreadsheet-based tracker, or a dedicated incident management solution with automated '
                                     'workflows and ticketing functionality.\n'
                                     '\n'
                                     'Do you track Cyber Security incidents through to closure?',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2G: Criteria for Cyber Security event escalation, including Cyber Security incident '
                             "declaration criteria, are adjusted according to information from the organisation's risk "
                             'register (RM-2j) and threat profile (TVM-1d)',
          'requirement_description': 'Do you periodically review and update your Security event escalation criteria (refer '
                                     "IR-2a) in alignment with your organisation's changing risk profile (refer RM-2j) and the "
                                     'broader Cyber threat environment?',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2H: Escalated Cyber Security events and declared Cyber Security incidents inform the common '
                             'operating picture (SA-3a) for the function',
          'requirement_description': "Do you update your organisation's Common Operating Picture (COP, refer SA-3a) to reflect "
                                     'when there are active Cyber Security incidents being investigated? \n'
                                     '\n'
                                     ' As per SA-3a, a COP is a consolidated view (i.e. "single pane of glass"") of the '
                                     'current state of Cyber Security operations within an organisation."',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-2I: Escalated Cyber Security events and declared incidents are correlated to support the '
                             'discovery of patterns, trends, and other common features',
          'requirement_description': 'Do you periodically review previous Cyber Security incidents to identify common traits, '
                                     'repeated occurrences or themes that might point to a broader issue that requires '
                                     'investigating? For example, multiple incidents of the same nature may indicate a control '
                                     'weakness that needs to be addressed.',
          'subchapter': 'IR-2: Escalate Cyber Security Events and Declare Incidents'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3A: Cyber Security event and incident response personnel are identified and roles are '
                             'assigned, at least in an ad hoc manner',
          'requirement_description': 'People who are responsible for responding to Cyber Security events and incidents know '
                                     'that they are responsible, and what they are responsible for',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3B: Responses to escalated Cyber Security events and incidents are implemented, at least in '
                             'an ad hoc manner, to limit impact to the function and restore normal operations',
          'requirement_description': 'When you respond to Security incidents, do you take steps to limit the impact and '
                                     'restore normal services? This may include:\n'
                                     ' -Isolating affected systems to prevent them from adversely impacting other systems;\n'
                                     ' -Using a tool to scan and disinfect any systems affected by malware;\n'
                                     ' -Restoring systems from known-good backups.',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3C: Reporting of escalated Cyber Security events and incidents is performed (e.g., internal '
                             'reporting, ACSC), at least in an ad hoc manner',
          'requirement_description': 'How are Security incidents reported within your organisation, both during and after an '
                                     'incident?\n'
                                     '\n'
                                     'Where required, do you report Cyber Security incidents to external authorities?',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3D: Cyber Security event and incident response is performed according to defined procedures '
                             'that address all phases of the incident life cycle (e.g., triage, handling, communication, '
                             'coordination, and closure)',
          'requirement_description': 'Has your organisation defined and documented a formal process for managing Cyber '
                                     'Security incidents? Does this process include all phases of an incident lifecycle? Are '
                                     'Cyber Security incidents managed in accordance with this process?\n'
                                     '\n'
                                     ' This practice enables an organisation to respond to Security incidents in a consistent '
                                     'manner.',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3E: Cyber Security event and incident response plans are exercised at an organisation- '
                             'defined frequency',
          'requirement_description': 'Periodically testing your Cyber Security incident response plans (e.g. via table-top '
                                     'exercises or incident simulations) helps people involved in response to remain familiar '
                                     'with the process. It also helps to highlight any issues or weaknesses in the process so '
                                     'these can be addressed prior to a real incident occurring.',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3F: Cyber Security event and incident response plans address OT and IT assets important to '
                             'the delivery of the function',
          'requirement_description': 'Are your Cyber Security incident response plans designed such that they can be invoked '
                                     'for your business-critical technology assets?',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3G: Training is conducted for Cyber Security event and incident response teams',
          'requirement_description': 'Are staff involved with Cyber Security incident response activities provided with '
                                     'opportunities to practice their roles, for example as part of simulation exercises '
                                     '(refer to IR-3e)?\n'
                                     '\n'
                                     ' This empowers personnel who have been assigned a role within the Cyber Security '
                                     'incident response process with the skills and knowledge to be able to successfully '
                                     'execute their role.',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3H: Cyber Security event and incident root-cause analysis and lessons-learned activities are '
                             'performed, and corrective actions are taken',
          'requirement_description': 'Do you seek to identify the root cause of Cyber Security incidents, either during or '
                                     'after an incident? Is this then used to update your Cyber Security controls (e.g. if a '
                                     'weakness was identified as the root cause)?',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3I: Cyber Security event and incident responses are coordinated with law enforcement and '
                             'other government entities as appropriate, including support for evidence collection and '
                             'preservation',
          'requirement_description': 'Does your organisation engage with law enforcement (e.g. Australian Federal Police) and '
                                     'other government entities (e.g. Australian Cyber Security Centre) to support Cyber '
                                     'Security incident response activities?',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3J: Cyber Security event and incident response personnel participate in joint Cyber Security '
                             'exercises with other organisations (e.g., table top, simulated incidents)',
          'requirement_description': 'Incident simulation exercises allow an organisation to practice executing their incident '
                                     'response plans. Conducting exercises with other organisations enables the sharing of '
                                     'information and lessons learned.',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3K: Cyber Security event and incident response plans are reviewed and updated at an '
                             'organisation-defined frequency',
          'requirement_description': 'Cyber Security incident response activities may need to be adjusted to better deal with '
                                     'the changing Cyber threat landscape.',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3L: Cyber Security event and incident response activities are coordinated with relevant '
                             'external entities',
          'requirement_description': 'Similar to IR-3i, does your organisation engage with external specialists when '
                                     'responding to a Cyber Security incident? This may include incident response and '
                                     'technology forensics specialists.',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': "IR-3M: Cyber Security event and incident response plans are aligned with the function's risk "
                             'criteria (RM-1c) and threat profile (TVM-1d)',
          'requirement_description': 'Are your Cyber Security incident response plans designed such that they are informed by '
                                     "your organisation's established threat profile (refer TVM-1d)? This may include the "
                                     'development of tailored incident response playbooks for specific types of Cyber Security '
                                     'incidents arising from threats that the organisation has identified as prevalent (e.g. '
                                     'ransomware outbreak).',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3N: Policy and procedures for reporting Cyber Security event and incident information to '
                             'designated authorities conform with applicable laws, regulations, and contractual agreements',
          'requirement_description': 'Do you have policies and procedures in place for Cyber Security incident reporting? If '
                                     'so, do these policies and procedures identify any external reporting requirements? This '
                                     'may include contractual obligations (e.g. reporting an incident to your customers), or '
                                     'legal/regulatory obligations (e.g. Australian Notifiable Data Breach scheme (NDB)).',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-3O: Restored assets are configured appropriately and inventory information is updated '
                             'following execution of response plans',
          'requirement_description': 'If you make changes to a technology asset/system while responding to a Cyber Security '
                                     'incident, do you ensure that these changes are reflected in your asset inventories '
                                     '(refer ACM-1)?',
          'subchapter': 'IR-3: Respond to Incidents and Escalated Cyber Security Events'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4A: The activities necessary to sustain minimum operations of the function are identified, at '
                             'least in an ad hoc manner',
          'requirement_description': 'Has your organisation identified which IT/OT operational activities, processes and '
                                     'systems are necessary to support business-critical operations?',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4B: The sequence of activities necessary to return the function to normal operation is '
                             'identified, at least in an ad hoc manner',
          'requirement_description': 'If a Cyber Security incident results in the degradation or outage of a business-critical '
                                     'function, does your organisation know how to restore those functions back to normal '
                                     'operations? This may take the form of a technology disaster recovery plan.',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4C: Continuity plans are developed, at least in an ad hoc manner, to sustain and restore '
                             'operation of the function',
          'requirement_description': 'In the event of an extended Cyber Security incident, does your organisation know how to '
                                     'ensure that its business-critical operations can continue? This may take the form of a '
                                     'business continuity plan.',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4D: Business impact analyses inform the development of continuity plans',
          'requirement_description': 'A Business Impact Assessment (BIA) seeks to identify and define how important a '
                                     'particular activity, process, asset or system is to the ongoing operation of an '
                                     'organisation, and what the potential impact would be if that thing became unavailable. \n'
                                     '\n'
                                     'Do you use the output of BIAs to inform your business continuity plans? This might '
                                     'include how you prioritise the allocation of resources to ensuring the ongoing '
                                     'continuity of particular activities or processes.',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4E: Recovery time objectives (RTO) and recovery point objectives (RPO) for the function are '
                             'incorporated into continuity plans',
          'requirement_description': 'Do you have Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) defined '
                                     'for business-critical activities, assets and systems? Are these included in your '
                                     'business continuity plans?',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4F: Continuity plans are evaluated and exercised',
          'requirement_description': 'Do you test the business continuity plans developed in IR-4c? If so, does the testing '
                                     'include criteria to establish the effectiveness of the plans?\n'
                                     '\n'
                                     'Completing this practice ensures that the business function or organisation has tested '
                                     'the whether it is feasible to execute their business continuity plans as intended, and '
                                     'can highlight areas where future updates to the plans are required.\n'
                                     '\n'
                                     'IR-4a, IR-4b, and IR-4c must be completed as a pre-requisite for this practice.',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4G: Business impact analyses are periodically reviewed and updated',
          'requirement_description': 'Do you review the business impact analyses (IR-4d) that your business function or '
                                     'organisation has conducted? If so, does this occur at a defined interval, or ad-hoc? Do '
                                     'you update the analyses where required?',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4H: Recovery time objectives (RTO) and recovery point objectives (RPO) are aligned with the '
                             "function's risk criteria (RM-1c)",
          'requirement_description': "The organisation's risk criteria (refer RM-1c) may inform your priorities for how "
                                     'quickly business-critical systems need to be recovered from an outage.',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4I: The results of continuity plan testing and/or activation are compared to recovery '
                             'objectives, and plans are improved accordingly',
          'requirement_description': 'When continuity plans are evaluated and exercised (IR-4f), do you establish whether the '
                                     'Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) were achieved? Do you '
                                     'update and improve the continuity plans (e.g. with lessons learnt)?',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4J: Continuity plans are periodically reviewed and updated',
          'requirement_description': 'Has your organisation defined a requirement for how often continuity plans should be '
                                     'reviewed and updated? If so, have your continuity plans been reviewed and updated in '
                                     'accordance with this requirement?',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-4K: Restored assets are configured appropriately and inventory information is updated '
                             'following execution of continuity plans',
          'requirement_description': 'If your response to a Cyber Security incident necessitates restoring technology '
                                     'assets/systems (e.g. from backups) or replacing them entirely, do you ensure that these '
                                     'are configured in line with your previously defined configuration baselines (refer '
                                     'ACM-2), and update your asset inventories accordingly (refer ACM-1)?',
          'subchapter': 'IR-4: Plan for Continuity'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-AP1: Critical functions have not been identified',
          'requirement_description': 'Important business functions are sometimes known to employees through their day-to-day '
                                     'business activities. Other times, important functions are less obvious. As a result, '
                                     'identifying critical functions requires you to:\n'
                                     ' -comprehensively analyse each organisational function;\n'
                                     ' -determine (through your analysis) the interdependencies that exist between '
                                     'organisational functions, and;\n'
                                     ' -consider (through your analysis) the importance of that function to the achievement of '
                                     'organisational objectives.\n'
                                     '\n'
                                     ' A business impact assessment (BIA) is a type of assessment that can help your '
                                     'organisation understand which functions are more important than others.\n'
                                     '\n'
                                     ' An example of an important function might be the accounts payable department who '
                                     'ensures that employees and third parties are paid.',
          'subchapter': 'IR-AP: IR Anti-Patterns'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-AP2: Services and assets that support the delivery of critical functions have not been '
                             'identified (IR-AP1)',
          'requirement_description': 'IR-AP1 must be Not Present for this Anti-Pattern to be Not Present.\n'
                                     '\n'
                                     'Building on IR-AP1, a business impact assessment (BIA) can also help your organisation '
                                     'understand which assets (such as networks, systems, and applications) support the '
                                     'delivery of critical functions.\n'
                                     '\n'
                                     'When identifying the assets that support the delivery of critical functions, '
                                     'consideration should be given to how continuity of use will be maintained during an '
                                     'incident, and recovery managed post an incident. For example, access to cloud based '
                                     'asset may not be possible during a denial of service incident. \n'
                                     ' Examples of important assets may include:\n'
                                     ' -server that is responsible for Supervisory Control and Data Acquisition (SCADA), and '
                                     'allows your organisation to intelligently control the electricity network, and (or);\n'
                                     ' -a mail server that allows your organisation to send and receive emails (such as '
                                     'payslips and tax invoices). \n'
                                     ' Examples of important services (performed by an asset) may include:\n'
                                     ' -a Network Time Protocol (NTP) server that synchronises the clocks of assets (SA-AP5), '
                                     'and (or);\n'
                                     ' -a Voice over Internet Protocol (VOIP) server that enables telephony. \n'
                                     ' A service may be fully or semi-automated, and involve a combination of people, process '
                                     'and technology (assets).',
          'subchapter': 'IR-AP: IR Anti-Patterns'},
         {'chapter_title': 'IR: Event and Incident Response, Continuity of Operations',
          'conformity_questions': [],
          'objective_title': 'IR-AP3: Incident responders do not know which authorities (including law enforcement) should be '
                             'contacted or how to contact them',
          'requirement_description': 'Depending on the nature and severity of a cyber security incident, there may be '
                                     'situations where law enforcement entities need to be contacted.\n'
                                     '\n'
                                     'Incident response plans and procedures should include guidance on when law enforcement '
                                     'entities need to be contacted, and include contact details such as phone numbers.',
          'subchapter': 'IR-AP: IR Anti-Patterns'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1A: Information is collected from and provided to selected individuals and/or organisations, '
                             'at least in an ad hoc manner',
          'requirement_description': 'Many organisations already produce and share Cyber threat information internally. For '
                                     'example, a Security team may identify malicious files on a compromised system when '
                                     'responding to an incident and produce an associated set of indicators (e.g., file names, '
                                     'sizes, hash values). These indicators might then be shared with system administrators '
                                     'who configure Security tools, such as intrusion detection systems, to detect the '
                                     'presence of these indicators on other systems. \n'
                                     '\n'
                                     'Likewise, the Security team may launch an email Security awareness initiative in '
                                     'response to an observed rise in phishing attacks within the organisation. These examples '
                                     'demonstrate information sharing within an organisation.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1B: Responsibility for Cyber Security reporting obligations are assigned to personnel (e.g., '
                             'internal reporting to management, external reporting to government (e.g. ACSC) or law '
                             'enforcement (e.g. AFP), at least in an ad hoc manner',
          'requirement_description': 'Has the organisation identified the role(s) responsible for reporting Cyber Security '
                                     'information (e.g. identified threats, active incidents, confirmed breaches, etc.) both '
                                     'internally and externally?',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1C: Information-sharing stakeholders are identified based on their relevance to the '
                             'continued operation of the function (e.g., connected utilities, vendors, sector organisations, '
                             'regulators, internal entities)',
          'requirement_description': 'Does the organisation share Cyber Security information with internal and external '
                                     'stakeholders that are known to be essential to maintaining continuity of business '
                                     'operations? \n'
                                     '\n'
                                     " The breadth of an organisation's information sharing activities should be consistent "
                                     'with its resources,\n'
                                     ' Abilities, and objectives. Information sharing efforts should focus on activities that '
                                     'provide the greatest\n'
                                     'value to an organisation and its external sharing partners.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1D: Information is collected from and provided to identified information-sharing '
                             'stakeholders',
          'requirement_description': 'By exchanging Cyber threat information within a sharing community, organisations can '
                                     'leverage the collective knowledge, experience, and capabilities of that sharing '
                                     'community to gain a more complete understanding of the threats the organisation may '
                                     'face. Using this knowledge, an organisation can make threat-informed decisions regarding '
                                     'defensive capabilities, threat detection techniques, and mitigation strategies.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1E: Technical sources are identified that can be consulted on Cyber Security issues',
          'requirement_description': 'Within (or in addition to) the sharing community described in ISC-1d, has the '
                                     'organisation identified and established relationships with technical subject matter '
                                     'experts who can provide specialist advice or capability when required?\n'
                                     '\n'
                                     ' Examples may include vendor Security specialists, threat intelligence specialists '
                                     '(whether government-led or commercial providers), incident response providers, etc.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1F: Provisions are established and maintained to enable secure sharing of sensitive or '
                             'classified information',
          'requirement_description': 'Sensitive information such as classified material and personally identifiable '
                                     'information (PII) may be encountered when handling Cyber threat information. The '
                                     'improper disclosure of such information could cause financial loss; violate laws, '
                                     "regulations, and contracts; be cause for legal action; or damage an organisation's or "
                                     "individual's reputation. \n"
                                     '\n'
                                     ' Accordingly, organisations should implement the necessary Security and privacy controls '
                                     'and handling procedures to protect this information from unauthorised disclosure or '
                                     'modification.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1G: Information-sharing practices address both standard operations and emergency operations',
          'requirement_description': 'Completing this practice ensures that Incident Response activities (within the Event and '
                                     'Incident Response, Continuity of Operations (IR) Domain) have considered the '
                                     'unavailability of information systems or computer networks',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1H: Information-sharing stakeholders are identified based on shared interest in and risk to '
                             'critical infrastructure',
          'requirement_description': 'Threat information exchanged within communities organised around specific industries or '
                                     'sectors (e.g. Critical Infrastructure) can be particularly beneficial because the member '
                                     'organisations often face actors that use common TTPs that target the same types of '
                                     'systems and information.\n'
                                     '\n'
                                     'Cyber defence is most effective when organisations work together to deter and defend '
                                     'against well-organised, capable actors. Such collaboration helps to reduce risk and '
                                     "improve the organisation's Security posture.",
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1I: The function or the organisation participates with information sharing and analysis '
                             'centres',
          'requirement_description': 'Does the organisation engage and participate in external information sharing groups, '
                                     'such as the Joint Cyber Security Centres (JCSC) or industry-specific Cyber working '
                                     'groups?',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1J: Information-sharing requirements have been defined for the function and address timely '
                             'dissemination of Cyber Security information',
          'requirement_description': 'Has the organisation defined clear requirements (e.g. in a policy or strategy) for how '
                                     'it will share Cyber Security information? Do these requirements specifically address the '
                                     'type of information to be shared, and the timeframes that this information should be '
                                     'communicated in? \n'
                                     '\n'
                                     'One example could include a policy requirement that when a Cyber Security event is '
                                     'escalated to be managed as a high-priority incident, a formal incident notification must '
                                     'be provided to management within a certain timeframe. Another example may involve a '
                                     'requirement that newly identified Cyber threat indicators (e.g. IOCs) must be applied to '
                                     "an organisation's endpoint protection solutions within a certain timeframe.\n"
                                     '\n'
                                     'Organisations may implement automated workflows to publish, consume, analyse, and act '
                                     'upon Cyber threat information. The use of standardised data formats and transport '
                                     'protocols to share Cyber threat information makes it easier to automate threat '
                                     'information processing. The use of automation enables Cyber threat information to be '
                                     'rapidly shared, transformed, enriched, analysed, and acted upon with less need for '
                                     'manual intervention.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1K: Procedures are in place to analyse and de-conflict received information',
          'requirement_description': 'Information sharing procedures should control the publication and distribution of threat '
                                     'information, and consequently help to prevent the dissemination of information that, if '
                                     'improperly disclosed, may have adverse consequences for an organisation, its customers, '
                                     'or its business partners. \n'
                                     '\n'
                                     'Information sharing procedures should take into consideration the trustworthiness of the '
                                     'information source or recipient, the sensitivity of the shared information, and the '
                                     'potential impact of sharing (or not sharing) specific types of information.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'ISC: Information Sharing and Communications',
          'conformity_questions': [],
          'objective_title': 'ISC-1L: A network of internal and external trust relationships (formal and/or informal) has been '
                             'established to vet and validate information about Cyber events',
          'requirement_description': 'Does the organisation prioritise its Cyber Security information sharing sources based on '
                                     'their relative trustworthiness or credibility? \n'
                                     '\n'
                                     ' An example may involve an organisation receiving notification of an active Cyber threat '
                                     'within its sector, and then utilising an independent trusted party (e.g. a government '
                                     'agency) to confirm/deny the validity of the threat.',
          'subchapter': 'ISC-1: Share Cyber Security Information'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-1A: There is a documented Cyber Security risk management strategy',
          'requirement_description': 'A Cyber Security risk management strategy describes at a high level how an organisation '
                                     'will identify, assess, prioritise and manage Cyber Security risks. It should:\n'
                                     ' -Define the activities that the organisation will use to identify cyber security '
                                     'risks;\n'
                                     ' -Define a methodology for risk assessment/evaluation and prioritisation (considering '
                                     'likelihood and impact);\n'
                                     ' -Define risk appetite, tolerance and appropriate risk responses (based on risk '
                                     'prioritisation);\n'
                                     ' -Define the processes and systems/tools to be used to document and monitor identified '
                                     'risks;\n'
                                     ' -Define a governance structure for how identified risks are to be tracked and reported '
                                     'throughout their lifecycle.',
          'subchapter': 'RM-1: Establish Cyber Security Risk Management Strategy'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-1B: The Cyber Security risk management strategy provides an approach for risk prioritisation, '
                             'including consideration of impact',
          'requirement_description': 'Does the Cyber Security risk management strategy in RM-1a define a criteria/framework '
                                     'with which to assess Cyber Security risks to determine an overall risk rating/priority '
                                     'that takes into account the potential likelihood and impact of the risk occurring?',
          'subchapter': 'RM-1: Establish Cyber Security Risk Management Strategy'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-1C: Organisational risk criteria (objective criteria that the organisation uses for '
                             'evaluating, categorising, and prioritising operational risks based on impact, tolerance for '
                             'risk, and risk response approaches) are defined and available',
          'requirement_description': 'The Cyber Security risk management strategy should define (or demonstrate alignment to) '
                                     "the organisation's broader enterprise/corporate risk management framework, including "
                                     'definition of the following:\n'
                                     '\n'
                                     ' -Impact categories (e.g. health & safety, reputation, legal, financial, etc.);\n'
                                     ' -Impact thresholds (e.g. insignificant, low, moderate, high, severe, etc.);\n'
                                     ' -Likelihood thresholds (e.g. Not likely, possible, almost certain, etc.);\n'
                                     ' -An overall risk rating matrix;\n'
                                     ' -Possible risk responses (e.g. mitigate, transfer, avoid, accept);\n'
                                     ' -Risk tolerance / appetite.',
          'subchapter': 'RM-1: Establish Cyber Security Risk Management Strategy'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-1D: The Cyber Security risk management strategy is periodically updated to reflect the '
                             'current threat environment',
          'requirement_description': 'Using Cyber threat information collected (refer TVM-1a), does the organisation update '
                                     'its Cyber Security risk management strategy to ensure that it adequately addresses the '
                                     'evolving Cyber threat landscape?',
          'subchapter': 'RM-1: Establish Cyber Security Risk Management Strategy'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-1E: An organisation-specific risk taxonomy is documented and is used in risk management '
                             'activities',
          'requirement_description': 'A risk taxonomy is the definition of a common set of risk categories into a hierarchy, '
                                     'whereby higher-level risks (e.g. those defined in a corporate/strategic risk register) '
                                     'are broken down into more specific/granular risks (e.g. those defined in an '
                                     'operational/tactical risk register).\n'
                                     '\n'
                                     ' An example of a simple risk taxonomy may defined the following risk types:\n'
                                     ' -Confidentiality/Access Risk\n'
                                     ' -Integrity/Change Risk\n'
                                     ' -Availability/Continuity Risk\n'
                                     '\n'
                                     "Using a risk taxonomy can help to strengthen and better integrate an organisation's risk "
                                     'assessment and risk management activities, by facilitating the aggregation of risks '
                                     'within defined categories from across the organisation.',
          'subchapter': 'RM-1: Establish Cyber Security Risk Management Strategy'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2A: Cyber Security risks are identified, at least in an ad hoc manner',
          'requirement_description': 'Cyber Security risks may be identified through a variety of mechanisms, including (but '
                                     'not limited to):\n'
                                     '\n'
                                     ' -Known Security issues or weaknesses;\n'
                                     ' -Top-down Cyber risk assessments;\n'
                                     ' -Security control effectiveness testing / audits;\n'
                                     ' -Vulnerability assessments or penetration testing;\n'
                                     ' -Project-based Security architecture / design assessments.',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2B: Identified Cyber Security risks are mitigated, accepted, tolerated, or transferred, at '
                             'least in an ad hoc manner',
          'requirement_description': 'When Cyber Security risks are identified, does the organisation seek to respond to them '
                                     'in some way?',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2C: Cyber Security risk assessments are performed to identify risks in accordance with the '
                             'risk management strategy',
          'requirement_description': 'Building on RM-2a, does the organisation perform Cyber Security risk assessments in '
                                     'accordance with its Cyber Security Risk Management Strategy (refer RM-1a)?\n'
                                     'RM-1a must be completed as a pre-requisite for this practice.',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2D: Identified Cyber Security risks are documented',
          'requirement_description': 'Risks may be documented in separate artefacts (e.g. risk assessment reports) or '
                                     'centrally in a dedicated risk register (refer RM-2j).',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2E: Identified Cyber Security risks are analysed to prioritise response activities in '
                             'accordance with the Cyber Security risk management strategy',
          'requirement_description': 'Once a risk has been identified and documented, the guidance in the Cyber Security Risk '
                                     "Management Strategy (refer RM-1a) is used to define the organisation's response to that "
                                     'risk (e.g. avoid, accept, mitigate, transfer).',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2F: Identified Cyber Security risks are monitored in accordance with the Cyber Security risk '
                             'management strategy',
          'requirement_description': 'Cyber Security risks which have been identified and documented by the organisation are '
                                     'monitored and managed using guidance in the Cyber Security Risk Management Strategy '
                                     '(refer RM-1a). \n'
                                     '\n'
                                     ' This might include periodic re-assessment of the risk in accordance with the changing '
                                     'Cyber threat landscape, testing the effectiveness of mitigating controls, tracking the '
                                     'implementation progress of treatment plans, etc.',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2G: Cyber Security risk analysis is informed by network (IT and/or OT) architecture',
          'requirement_description': 'When the organisation assesses an identified Cyber Security risk, does the assessment '
                                     "take into account  where the risks exists in the context of the organisation's network "
                                     'architecture - taking into account the characteristics and respective risk profiles of '
                                     'the various network zones which may increase or decrease the likelihood or impact the '
                                     'risk being assessed?\n'
                                     '\n'
                                     'For example, the risk of un-encrypted network traffic being intercepted in transit may '
                                     "be lower within an organisation's internal datacentre network zone compared to network "
                                     'traffic transmitted within a semi-trusted zone such as a DMZ or over a wireless network '
                                     'link.',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2H: The Cyber Security risk management program defines and operates risk management policies '
                             'and procedures that implement the Cyber Security risk management strategy',
          'requirement_description': 'Has the organisation developed policies, processes and procedures to govern the '
                                     'activities described in the Cyber Security Risk Management Strategy (refer RM-1a)?\n'
                                     '\n'
                                     ' Examples may include (but are not limited to):\n'
                                     ' -Policy requirements stating when certain types of Security risk assessments need to '
                                     'occur (e.g. annual penetration testing of Internet-accessible systems);\n'
                                     ' -Processes to formally define the activities, roles and responsibilities for '
                                     'documenting and tracking identified Cyber Security risks;\n'
                                     ' -Procedures to provide detailed guidance for how to perform certain Cyber Security risk '
                                     'management activities (e.g. how to configure and run a vulnerability scanning tool).',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2I: A current Cyber Security architecture is used to inform Cyber Security risk analysis',
          'requirement_description': 'Building on RM-2g, when the organisation assesses an identified Cyber Security risk, '
                                     "does the assessment take into account the organisation's Cyber Security controls "
                                     'architecture - taking into account the respective risk profiles of defined Security '
                                     'zones, and the Security controls and services provided within those zones which may '
                                     'mitigate some aspect of the risk being assessed? This may be facilitated by a formally '
                                     'defined Enterprise Security Architecture.\n'
                                     '\n'
                                     'For example, the likelihood of an Internet-based Cyber attack compromising your '
                                     "organisation's OT environment may be lower if your Security architecture provides a "
                                     'defence-in-depth model with multiple layers of Security controls between the Internet '
                                     'and the OT network, compared to the likelihood of that risk occurring if your OT '
                                     'environment is directly-accessible from the Internet.',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-2J: A Cyber Security risk register (a structured repository of identified risks) is used to '
                             'support Cyber Security risk management activities',
          'requirement_description': 'Does the organisation maintain a dedicated risk register where identified Cyber Security '
                                     'risks are captured and maintained? The risk register may be managed informally as a '
                                     'spreadsheet, or more formally as part of an enterprise risk management solution.\n'
                                     '\n'
                                     ' As a MIL-3 practice, the expectation here is that Cyber Security risks are represented '
                                     "in an organisation's risk registers at various levels of granularity and in accordance "
                                     "with the organisation's defined Risk Taxonomy (refer RM-1e), e.g. \n"
                                     ' -One or more corporate/strategic Cyber Security risks captured in an organisation-level '
                                     'risk register that gets reported to the board;\n'
                                     ' -Multiple operational/tactical Cyber Security risks captured in '
                                     'department/function-level Security risk registers.',
          'subchapter': 'RM-2: Manage Cyber Security Risk'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-AP1: Identified risks are not periodically reviewed',
          'requirement_description': 'In order to effectively treat identified risks, it is important that risk governance '
                                     'structures are in place and include regular review of identified cyber security risks.\n'
                                     '\n'
                                     ' This may include:\n'
                                     ' -Validating the appropriateness of inherent and residual risk ratings (including '
                                     'likelihood and consequence ratings);\n'
                                     ' -Validating risk treatment approaches (planned and current), and;\n'
                                     ' -Reviewing control effectiveness.',
          'subchapter': 'RM-AP: RM Anti-Patterns'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-AP2: Identified cyber security risks remain untreated for long periods of time',
          'requirement_description': 'Identified cyber security risks should be resolved in a manner commensurate with the '
                                     'potential for adverse impact. This may mean that some cyber security risks need to be '
                                     'resolved before other cyber security risks, based on their likelihood and consequence.\n'
                                     '\n'
                                     'You should consider the period of time that a cyber security risk has remained '
                                     'unresolved and ensure that no cyber security risk remains unresolved indefinitely.',
          'subchapter': 'RM-AP: RM Anti-Patterns'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-AP3: Assets are risk-assessed in isolation. Interdependencies with other assets are not '
                             'considered',
          'requirement_description': 'Interconnected assets may carry additional cyber security risk when compared to '
                                     'standalone assets. Additionally, the interconnection itself may be a cyber security risk '
                                     'if not carefully architected.\n'
                                     '\n'
                                     'You should consider other interconnected assets when determining an overall risk rating '
                                     'for an asset.',
          'subchapter': 'RM-AP: RM Anti-Patterns'},
         {'chapter_title': 'RM: Risk Management',
          'conformity_questions': [],
          'objective_title': 'RM-AP4: Cyber security risk management activities are not informed and supported by '
                             'organisational risk criteria (RM-1C)',
          'requirement_description': 'RM-1C must be at least Partially Implemented for this Anti-Pattern to be Not Present.\n'
                                     '\n'
                                     'Cyber security risk management activities should be informed and supported by '
                                     'organisational risk criteria.\n'
                                     '\n'
                                     ' This ensures that cyber security risks can be consolidated from many functions, and '
                                     'aggregated into one or many organisational risks. It also ensures a consistent approach '
                                     'to risk assessment and grading is used.',
          'subchapter': 'RM-AP: RM Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-1A: Logging is occurring, at least in an ad hoc manner, for assets important to the function, '
                             'where possible',
          'requirement_description': "Systems and devices that support the organisation's critical business functions are "
                                     'configured to generate Security event logs.',
          'subchapter': 'SA-1: Perform Logging'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-1B: Logging requirements have been defined for all assets important to the function (e.g., '
                             'scope of activity and coverage of assets, Cyber Security requirements [confidentiality, '
                             'integrity, availability])',
          'requirement_description': 'Has the organisation defined specific requirements for systems and devices that support '
                                     "the organisation's critical business functions to generate Security event logs? \n"
                                     '\n'
                                     'Such requirements may be documented in a Security Logging & Monitoring Standard, and '
                                     'should specify:\n'
                                     ' -The type of events that are required to be logged for each type of system/device;\n'
                                     ' -The information to be captured in event logs;\n'
                                     ' -Requirements for aggregating and protecting event logs from unauthorised access, '
                                     'modification and deletion.',
          'subchapter': 'SA-1: Perform Logging'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-1C: Log data are being aggregated within the function',
          'requirement_description': 'Do you have centralised repositories where Security event logs are stored for the '
                                     'purpose of protection and aggregation? \n'
                                     '\n'
                                     'SA-1a must be completed as a pre-requisite for this practice.',
          'subchapter': 'SA-1: Perform Logging'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-1D: Logging requirements are based on the risk to the function',
          'requirement_description': 'Are the logging requirements defined in SA-1b informed by (or aligned to) your '
                                     "organisation's understanding of the Cyber risk profile of different system/device "
                                     'types?\n'
                                     '\n'
                                     'For example, business-critical systems located in Internet-facing network zones are more '
                                     'susceptible to certain types of Cyber threats, and as such might be configured with more '
                                     'detailed Security event logging compared to a non-critical asset located in an internal '
                                     'network zone. \n'
                                     '\n'
                                     'SA-1b must be completed as a pre-requisite for this practice.',
          'subchapter': 'SA-1: Perform Logging'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-1E: Log data support other business and Security processes (e.g., incident response, asset '
                             'management)',
          'requirement_description': 'Based on completing the other practices within this section, Security event logs which '
                                     'have been generated, aggregated and adequately protected should enable an organisation '
                                     'to perform other Cyber Security processes such as:\n'
                                     ' -Security event monitoring and alerting;\n'
                                     ' -Security investigation and incident response;\n'
                                     ' -Asset configuration and change management.',
          'subchapter': 'SA-1: Perform Logging'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2A: Cyber Security monitoring activities are performed (e.g., periodic reviews of log data), '
                             'at least in an ad hoc manner',
          'requirement_description': 'Security event logs should be proactively reviewed to identify suspicious or malicious '
                                     'events, either manually or via an automated solution (e.g. SIEM).',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2B: Operational environments are monitored, at least in an ad hoc manner, for anomalous '
                             'behaviour that may indicate a Cyber Security event',
          'requirement_description': 'Do you know how to differentiate between normal and abnormal behaviour within your '
                                     'technology environments? \n'
                                     '\n'
                                     'Monitoring may include reviewing Security event logs to identify suspicious events '
                                     '(refer SA-2a) or other types of behavioural monitoring that would provide sufficient '
                                     'indication that a Cyber Security event may have occurred.',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2C: Monitoring and analysis requirements have been defined for the function and address '
                             'timely review of event data',
          'requirement_description': 'Has the organisation defined specific requirements for the periodic review of Security '
                                     'event logs, and how often/quickly this should occur?\n'
                                     '\n'
                                     'Such requirements may be documented in a Security Logging & Monitoring Standard.',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2D: Alarms and alerts are configured to aid in the identification of Cyber Security events '
                             '(IR-1b)',
          'requirement_description': 'Where the review of Security event logs (refer SA-2c) identifies a suspicious/malicious '
                                     'event that warrants further investigation, is there a mechanism in place to generate an '
                                     'alert/alarm?\n'
                                     '\n'
                                     ' This would typically be facilitated by a log monitoring and analysis solution (e.g. '
                                     'SIEM), with automated alerts generated in accordance with predefined criteria (e.g. '
                                     'high-risk Security events are detected, or a pre-set threshold for repeated events is '
                                     'reached).',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2E: Indicators of anomalous activity have been defined and are monitored across the '
                             'operational environment',
          'requirement_description': 'Has the organisation defined specific system behaviours (e.g. Security event types or '
                                     'combinations of different events) or known threat-related Indicators of Compromise '
                                     '(IOCs) which may indicate that a Cyber threat has impacted (or is impacting) your '
                                     'technology systems? \n'
                                     '\n'
                                     ' Are these indicators actively monitored across the organisation?',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': "SA-2F: Monitoring activities are aligned with the function's threat profile (TVM-1d)",
          'requirement_description': "An organisation's Security logging and monitoring tools and processes should be informed "
                                     'by its defined threat profile (refer TVM-1d) to ensure that it is able to identify when '
                                     'specific Cyber threats are impacting technology systems. \n'
                                     '\n'
                                     'For example, the threat profile may indicate that a particular type of Cyber threat is '
                                     'more likely to impact a system or asset within the organisation. In this case, the '
                                     'organisation should ensure that systems susceptible to that threat are generating '
                                     'Security event logs that would indicate that the threat is impacting them, and Security '
                                     'monitoring solutions should be configured to look for specific evidence of that threat '
                                     '(e.g. IOCs) within logs and generate alerts accordingly.\n'
                                     '\n'
                                     ' This supports a risk-based approach to Security logging and monitoring within an '
                                     'organisation, recognising that some Cyber threats pose a greater risk and thus warrant '
                                     'enhanced detection capabilities.\n'
                                     '\n'
                                     ' TVM-1d must be completed as a pre-requisite for this practice.',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2G: Monitoring requirements are based on the risk to the function',
          'requirement_description': "Are your organisation's Security monitoring capabilities designed and implemented in "
                                     'alignment with your understanding of the likelihood and potential impact of Cyber risks '
                                     'facing the organisation?\n'
                                     '\n'
                                     'For example, an organisation may have identified a high-rated Cyber risk related to the '
                                     'external compromise of business critical web-based systems over the Internet. This would '
                                     'warrant that organisation focusing its Security monitoring activities on that particular '
                                     'system to ensure that it was able to detect and respond to Security events in a timely '
                                     'manner, thus limiting the impact to that asset. \n'
                                     '\n'
                                     ' This practice supports a risk-based approach to Security logging and monitoring within '
                                     'an organisation, recognising that some systems are more critical to the business and '
                                     'thus warrant enhanced monitoring capabilities.',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2H: Monitoring is integrated with other business and Security processes (e.g., incident '
                             'response, asset management)',
          'requirement_description': 'Based on completing the other practices within this section, Security monitoring '
                                     'activities should enable an organisation to perform other Cyber Security processes such '
                                     'as:\n'
                                     ' -Security investigation and incident response;\n'
                                     ' -Inform the Common Operating Picture (refer SA-3).',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2I: Continuous monitoring is performed across the operational environment to identify '
                             'anomalous activity',
          'requirement_description': 'Has the organisation implemented technology solutions and processes which enable it to '
                                     'continuously monitor its technology environments for Security events and incidents? Are '
                                     'these tools and processes supported by sufficient personnel (e.g. 24/7 coverage)?\n'
                                     '\n'
                                     ' A continuous Security monitoring capability may be entirely in-house, or augmented by a '
                                     'third party service provider.',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2J: Risk register (RM-2j) content is used to identify indicators of anomalous activity',
          'requirement_description': "Similar to SA-2f, an organisation's Security logging and monitoring tools and processes "
                                     'should be informed by an understanding of Cyber risks facing the business.  \n'
                                     '\n'
                                     'For example, an organisation may use a tactical / operational cyber security risk '
                                     'register to document and manage a specific Cyber risk relating to compromise of a '
                                     'business-critical asset by a known and active Cyber threat (e.g. WannaCry). In this '
                                     'case, the organisation should ensure that Security monitoring solutions are configured '
                                     'to look for specific evidence of that threat (e.g. IOCs) within logs and generate alerts '
                                     'accordingly.\n'
                                     '\n'
                                     ' This supports a risk-based approach to Security logging and monitoring within an '
                                     'organisation, recognising that some Cyber threats pose a greater risk and thus warrant '
                                     'specific or enhanced monitoring capabilities.',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-2K: Alarms and alerts are configured according to indicators of anomalous activity',
          'requirement_description': 'Building on SA-2d, does your organisation periodically update its Security monitoring '
                                     'solutions to look for specific Indicators of Compromise (IOCs) associated with known '
                                     'Cyber threats?',
          'subchapter': 'SA-2: Perform Monitoring'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-3A: Methods of communicating the current state of Cyber Security for the function are '
                             'established and maintained',
          'requirement_description': 'Does the organisation have established mechanisms in place which enable it to actively '
                                     'communicate operational Cyber Security information (e.g. identified threats, active '
                                     'incidents, etc.)? Examples may include:\n'
                                     '\n'
                                     ' -Cyber Security notification emails sent from a dedicated inbox (e.g. to notify staff '
                                     'of an active incident);\n'
                                     ' -Operational Cyber Security briefings/calls to inform key stakeholders of any notable '
                                     'information or events;\n'
                                     ' -Cyber Security reporting mechanisms to inform management of escalated Cyber Security '
                                     'issues;\n'
                                     ' -A dedicated Intranet site/page where Cyber Security notifications can be posted to '
                                     'inform the broader user population.',
          'subchapter': 'SA-3: Establish and Maintain a Common Operating Picture'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-3B: Monitoring data are aggregated to provide an understanding of the operational state of '
                             'the function (i.e., a common operating picture; a COP may or may not include visualisation or be '
                             'presented graphically)',
          'requirement_description': 'Does the organisation maintain a Common Operating Picture (COP) for Cyber Security '
                                     'across its technology environments? \n'
                                     '\n'
                                     ' A COP is a consolidated view (i.e. "single pane of glass"") of the current state of '
                                     'Cyber Security operations within an organisation."',
          'subchapter': 'SA-3: Establish and Maintain a Common Operating Picture'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-3C: Information from across the organisation is available to enhance the common operating '
                             'picture',
          'requirement_description': "Does the organisation's Cyber Security COP (refer SA-3b) take into account information "
                                     "gathered from across the organisation's technology environments, including Security "
                                     'logging, monitoring and alerting (refer SA-1, SA-2)?',
          'subchapter': 'SA-3: Establish and Maintain a Common Operating Picture'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-3D: Monitoring data are aggregated to provide near-real-time understanding of the Cyber '
                             'Security state for the function to enhance the common operating picture',
          'requirement_description': "Is the organisation's Cyber Security COP (refer SA-3b) automatically updated based on "
                                     'near-real-time monitoring and alerting of Cyber Security events (refer SA-1, SA-2)?',
          'subchapter': 'SA-3: Establish and Maintain a Common Operating Picture'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-3E: Information from outside the organisation is collected to enhance the common operating '
                             'picture',
          'requirement_description': "Does the organisation's Cyber Security COP (refer SA-3b) take into account external "
                                     'Cyber threat monitoring (refer TVM-1) and information sharing (refer ISC-1)?',
          'subchapter': 'SA-3: Establish and Maintain a Common Operating Picture'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-3F: Predefined states of operation are defined and invoked (manual or automated process) '
                             'based on the common operating picture',
          'requirement_description': '\n'
                                     'Does the organisation have an established framework/model to define and communicate the '
                                     '"current state" of Cyber Security operations at any given point in time based on '
                                     'internal monitoring and external threat information?\n'
                                     ' \n'
                                     'A COP may use a color-coded scale to define the current threat level (e.g. Green, '
                                     'Yellow, Amber, Red), with specific processes and procedures defined for each threat '
                                     'level. For example, if a high-profile Cyber threat was identified as actively targeting '
                                     'the organisation\'s industry, the COP may be elevated to "Amber" and specific response '
                                     'strategies invoked (e.g. heightened Security monitoring and alerting, more restrictive '
                                     'network access controls, etc.).\n'
                                     ' \n'
                                     'A tangible analogy is the Australian National Terrorism Threat Advisory System, which '
                                     'defines a scale of five levels to provide advice about the likelihood of an act of '
                                     'terrorism occurring in Australia (Not Expected / Possible / Probable / Expected / '
                                     'Certain). When the threat level changes, the Australian Government provides advice on '
                                     'what the threat level means, where the threat is coming from, potential targets and how '
                                     'a terrorist act may be carried out. The National Terrorism Threat Level is regularly '
                                     'reviewed in line with the Security environment and intelligence.',
          'subchapter': 'SA-3: Establish and Maintain a Common Operating Picture'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP1: Operational assets are monitored only for performance and not for cyber security events',
          'requirement_description': 'Performance-related monitoring (such as uptime, bandwidth, and latency statistics) may '
                                     'not provide the function with the visibility needed to detect and respond to a cyber '
                                     'security incident. It is important that monitoring of operational assets (such as '
                                     'networks, systems, and applications) includes security-related statistics (such as '
                                     'failed authentication attempts) in addition to any performance-related statistics.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP2: Logging data is only monitored when a cyber security incident occurs',
          'requirement_description': 'Logging data that is collected from your assets (such as networks, systems, and '
                                     'applications) can serve as a key source of information to support the early detection of '
                                     'a cyber security threat.\n'
                                     '\n'
                                     ' As a result, you should proactively monitor logging data in addition to monitoring '
                                     'during and after a cyber security incident.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP3: Normal asset operation is not sufficiently baselined to support the identification of '
                             'abnormal asset operation',
          'requirement_description': 'Logging data generated by assets (such as networks, systems, and applications) can '
                                     'become more useful over time, as normal patterns become apparent within security '
                                     'monitoring solutions.\n'
                                     '\n'
                                     'Understanding normal asset operation is critical to identifying abnormal asset '
                                     'operation.\n'
                                     '\n'
                                     'Baselines may be established for individual assets (e.g. a field device) or for a '
                                     'collection of interconnected assets.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP4: Alerts and alarms are not configured to include security events',
          'requirement_description': 'Performance-only monitoring of assets (such as networks, systems, and applications) may '
                                     'not provide the function with the visibility needed to detect and respond to a cyber '
                                     'security incident.\n'
                                     '\n'
                                     ' Alerts and alarms that are configured for performance-only reasons are limited in '
                                     'scope, and should be enhanced by integrating security monitoring statistics.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP5: Logging data is not time synchronised',
          'requirement_description': 'You should ensure that assets (such as networks, systems, and applications) are '
                                     'synchronised to a centralised and trusted time source (e.g. using Network Time Protocol '
                                     '(NTP)) to enable accurate event correlation from logging data.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP6: Logging data from critical assets is only stored on the asset and not centralised',
          'requirement_description': 'Logging data that is collected from your assets (such as networks, systems, and '
                                     'applications) can serve as a key source of information to support the early detection of '
                                     'a cyber security threat.\n'
                                     '\n'
                                     ' As a result, if logging data is only stored locally, this may limit your ability to '
                                     'perform comprehensive monitoring and proactively identify cyber security threats.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP7: Identities (users) have edit (write) access to centralised logging data without a '
                             'confirmed need',
          'requirement_description': 'The confidentiality and integrity of centralised logging data should be protected by '
                                     'restricting the identities (users) that have access. This ensures the logging data can '
                                     'be used to build an accurate chain of events when investigating a cyber security '
                                     'incident.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP8: Third party vendors or services have privileged access that is not logged',
          'requirement_description': 'Privileged access, such as an administrator account, represents a higher level of risk '
                                     'to the function, given the potential for an administrator to make broad and irreversible '
                                     'changes to assets (such as networks, systems, and applications).\n'
                                     '\n'
                                     'If you provision third parties with privileged access, you should ensure that logging '
                                     'data is collected, and that the access does not circumvent your security controls.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP9: Indicators of Compromise (IOCs) are only monitored and considered during or after a '
                             'cyber security incident',
          'requirement_description': 'Indicators of Compromise (IOCs) are known malicious signatures that are shared in threat '
                                     'intelligence forums (both free and paid).\n'
                                     '\n'
                                     'Similarly to SA-AP2, you should proactively monitor IOC repositories for new and updated '
                                     'indicators, in addition to mointoring them during and after a cyber security incident.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP10: Logging data from impacted assets cannot be inspected when investigating a cyber '
                             'security event',
          'requirement_description': 'Logging data that is collected from your assets (such as networks, systems, and '
                                     'applications) can serve as a key source of information to support the early detection of '
                                     'a cyber security threat.\n'
                                     '\n'
                                     ' Ensuring that logging data is available when investigating a cyber security event is '
                                     'also important. When assets are impacted, and logging data generated by those assets is '
                                     'unavailable, you have a limited ability to respond.\n'
                                     '\n'
                                     ' Example activities that indicate this Anti-Pattern is Present include:\n'
                                     ' -Logging data is stored in a cloud (Internet) based repository, and logging data in '
                                     'this repository cannot be inspected during a Distributed Denial of Service (DDOS) '
                                     'attack, or;\n'
                                     ' -Logging data cannot be centrally inspected by your security monitoring solution as it '
                                     'is stored in a segregated network inaccessible during an incident, or;\n'
                                     ' -Logging data cannot be inspected given security logging requirements were not '
                                     'established by the function, and therefore the logging data is not fit-for-purpose or is '
                                     'unintelligible.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'SA: Situational Awareness',
          'conformity_questions': [],
          'objective_title': 'SA-AP11: Indicators of Compromise cannot be added to security monitoring solutions that monitor '
                             'critical assets',
          'requirement_description': 'Indicators of Compromise (IOCs) are known malicious signatures that are shared in threat '
                                     'intelligence forums (both free and paid).\n'
                                     '\n'
                                     'You should ensure that IOCs can be added to the security monitoring solutions that '
                                     "monitor the function's critical assets (such as networks, systems, and applications). "
                                     'This can support your ability to perform comprehensive monitoring and proactively '
                                     'identify cyber security threats.',
          'subchapter': 'SA-AP: SA Anti-Patterns'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1A: Information sources to support threat management activities are identified, at least in '
                             'an ad hoc manner.',
          'requirement_description': 'Have you determined where you will obtain external Cyber threat information? This may '
                                     'come from government sources (e.g. ACSC), industry information sharing forums, or '
                                     'private organisations (e.g. AusCERT).',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1B: Cyber Security threat information is gathered and interpreted for the function, at least '
                             'in an ad hoc manner',
          'requirement_description': 'Are you currently receiving and assessing Cyber threat information from the sources '
                                     'identified in TVM-1a?\n'
                                     '\n'
                                     'Cyber threat information is any information that can help an organization identify, '
                                     'assess, monitor, and respond to Cyber threats. Examples include indicators (system '
                                     'artefacts or observables associated with an attack), tactics, techniques, and procedures '
                                     '(TTPs), Security alerts, threat intelligence reports, and recommended Security tool '
                                     'configurations.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1C: Threats that are considered important to the function are addressed (e.g., implement '
                             'mitigating controls, monitor threat status), at least in an ad hoc manner',
          'requirement_description': "Once you've assessed Cyber threat information received from external sources and "
                                     'determined that a specific threat could adversely impact your organisation, do you '
                                     'identify and implement response strategies? This may include enhanced Security '
                                     'monitoring or deploying additional Security controls where deemed necessary.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1D: A threat profile for the function is established that includes characterisation of '
                             'likely intent, capability, and target of threats to the function',
          'requirement_description': 'A threat profile is a consolidated view of the following:\n'
                                     " -An organisation's assets which may become the target of a Cyber attack, and their "
                                     'criticality to the business;\n'
                                     ' -Known Cyber threat types (e.g. DDoS, ransomware, hacking, etc.);\n'
                                     ' -Known threat actor types (e.g. State sponsored groups, hacktivists, Cyber criminals, '
                                     'insider threat, etc.) and their motivation, intent, capabilities and likely targets;\n'
                                     ' -Cyber threat scenarios (attacks), mapping the use of Cyber threats by a threat actor '
                                     'against an asset within the organisation. The definition of threat scenarios should '
                                     'include their likelihood and complexity to carry out, and the potential impact to the '
                                     'organisation. \n'
                                     '\n'
                                     'Developing a threat profile allows an organisation to better understand and prepare for '
                                     'Cyber threats, and manage the associated risks. \n'
                                     '\n'
                                     ' TVM-1a, TVM-1b, and TVM-1c must be completed as a pre-requisite for this practice.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1E: Threat information sources that address all components of the threat profile are '
                             'prioritised and monitored',
          'requirement_description': 'Are you confident that your existing Cyber threat information sources (refer TVM-1a) '
                                     'provide adequate visibility of the Cyber threats and threat actors identified in your '
                                     'threat profile (refer TVM-1d)? \n'
                                     '\n'
                                     ' TVM-1a, TVM-1b and TVM-1d must be completed as a pre-requisite for this practice.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1F: Identified threats are analysed and prioritised',
          'requirement_description': 'Building on TVM-1b, do you assign a formal prioritisation (e.g. classification rating) '
                                     'to identified Cyber threats? \n'
                                     '\n'
                                     ' This prioritisation may simply involve using a rating provided by the external threat '
                                     'information source (e.g. a vendor-supplied vulnerability rating using CVSS), or '
                                     'alternatively the organisation may have defined its own priority/classification scheme '
                                     'for Cyber threats based on likelihood and potential impact to the function. \n'
                                     '\n'
                                     ' TVM-1b must be completed as a pre-requisite for this practice.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1G: Threats are addressed according to the assigned priority',
          'requirement_description': "Are the organisation's responses to identified Cyber threats driven or guided by the "
                                     "threat's assigned priority/classification rating? \n"
                                     '\n'
                                     'For example, a lower-priority threat may only require the organisation to monitor for '
                                     'evidence of the threat as part of BAU activities, whereas a higher-priority threat may '
                                     'warrant a more in-depth response strategy involving adjustments to Security controls '
                                     '(e.g. more restrictive access controls, enhanced Security event monitoring and alerting, '
                                     'isolation of critical network segments, etc.).\n'
                                     '\n'
                                     ' TVM-1f must be completed as a pre-requisite for this practice.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1H: The threat profile for the function is validated at an organisation-defined frequency',
          'requirement_description': 'The Cyber threat landscape is constantly changing, with new threats being developed and '
                                     "more threat actors becoming increasingly sophisticated. Similarly, organisations' "
                                     'technology environments change over time as new systems and capabilities are '
                                     'introduced.\n'
                                     '\n'
                                     ' An organisation should periodically review and update its threat profile (refer TVM-1d) '
                                     "to ensure that it continues to address the organisation's critical assets, and "
                                     'accurately reflects the current Cyber threat landscape. \n'
                                     '\n'
                                     ' TVM-1d must be completed as a pre-requisite for this practice.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': "TVM-1I: Analysis and prioritisation of threats are informed by the function's (or "
                             "organisation's) risk criteria (RM-1c)",
          'requirement_description': "Building on TVM-1f, do you use information from the organisation's threat profile (refer "
                                     'TVM-1d) to determine the priority/classification rating to Cyber threats? \n'
                                     '\n'
                                     ' This would include the assets which are likely to be targeted by the threat and the '
                                     'potential impact to the business should the threat scenario eventuate, assessed in '
                                     "accordance with the organisation's broader risk management framework (refer RM-1c).\n"
                                     '\n'
                                     ' TVM-1b and TVM-1f must be completed as a pre-requisite for this practice.',
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-1J: Threat information is added to the risk register (RM-2j)',
          'requirement_description': "Organisations' Cyber Security risk registers (refer RM-2j) define certain risk scenarios "
                                     'based on likelihood and potential impact - these attributes should be informed by '
                                     "information in the organisation's Cyber threat profile.\n"
                                     '\n'
                                     'For example, if you became aware of a high-priority Cyber threat which was being widely '
                                     'exploited (e.g. WannaCry, NotPetya) and was likely to be used against the organisation '
                                     'in a way which might impact its critical assets, this should be added to a tactical risk '
                                     "register and managed for the duration of the threat's lifecycle in accordance with the "
                                     "organisation's broader risk management framework, including assessment, tracking and "
                                     'reporting. \n'
                                     '\n'
                                     ' Another example involves using trend information from the threat profile (e.g. a '
                                     'particular threat type may become more prevalent over time) to adjust the likelihood of '
                                     "existing Cyber Security risks defined in an organisation's risk registers.",
          'subchapter': 'TVM-1: Identify and Respond to Threats'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2A: Information sources to support Cyber Security vulnerability discovery are identified '
                             '(e.g. industry associations, vendors, federal briefings, internal assessments), at least in an '
                             'ad hoc manner',
          'requirement_description': 'Vulnerability information sources may include:\n'
                                     ' -Vendor patch notifications;\n'
                                     ' -Independent Security vulnerability disclosures;\n'
                                     ' -Government bodies (e.g. ACSC);\n'
                                     ' -Commercial providers (e.g. AusCERT);\n'
                                     ' -Internal Security assessments (e.g. vulnerability scanning, penetration testing, '
                                     'etc.).',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2B: Cyber Security vulnerability information is gathered and interpreted for the function, '
                             'at least in an ad hoc manner',
          'requirement_description': 'Does the organisation actively consume vulnerability notifications from the sources '
                                     'identified in TVM-2a?',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2C: Cyber Security vulnerabilities that are considered important to the function are '
                             'addressed (e.g., implement mitigating controls, apply Cyber Security patches), at least in an ad '
                             'hoc manner',
          'requirement_description': 'Does the organisation seek to remediate or otherwise mitigated identified '
                                     'vulnerabilities? Examples may include: \n'
                                     ' -Applying a Security patch;\n'
                                     ' -Implementing a workaround;\n'
                                     ' -Updating a configuration setting;\n'
                                     ' -Implementing a compensating control (e.g. enhanced monitoring).',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2D: Cyber Security vulnerability information sources that address all assets important to '
                             'the function are monitored',
          'requirement_description': 'Is the organisation confident that it is receiving vulnerability information for all its '
                                     'business-critical technology systems and assets? Examples may include:\n'
                                     ' -Operating systems (e.g. Windows, Linux);\n'
                                     ' -Virtualisation platforms (e.g. VMWare);\n'
                                     ' -Business applications (e.g. MS Office, Adobe, Java);\n'
                                     ' -Network communications equipment (e.g. routers, switches, firewalls, etc.);\n'
                                     ' -Storage platforms and devices;\n'
                                     ' -Operational Technology systems (e.g. SCADA applications, Energy Management Systems).',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2E: Cyber Security vulnerability assessments are performed (e.g., architectural reviews, '
                             'penetration testing, Cyber Security exercises, vulnerability identification tools)',
          'requirement_description': 'Does the organisation proactively seek to identify Security vulnerabilities within its '
                                     'technology environments?',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2F: Identified Cyber Security vulnerabilities are analysed and prioritised',
          'requirement_description': 'When Cyber Security vulnerabilities are identified, does the organisation assess the '
                                     'associated risks and apply a prioritisation/risk rating (e.g. Low / Medium / High / '
                                     'Critical)?',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2G: Cyber Security vulnerabilities are addressed according to the assigned priority',
          'requirement_description': 'Has the organisation defined requirements for remediation of identified Cyber Security '
                                     'vulnerabilities in accordance with their assigned prioritisation/risk rating? \n'
                                     'For example, High/Critical vulnerabilities may be required to be remediated in a matter '
                                     'of hours or days, whereas lower-risk vulnerabilities may be allowed longer remediation '
                                     'timeframes.',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2H: Operational impact to the function is evaluated prior to deploying Cyber Security '
                             'patches',
          'requirement_description': 'Organisations may choose to first apply Security patches to test or staging environments '
                                     'before deploying them to business-critical production systems.',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2I: Cyber Security vulnerability assessments are performed for all assets important to the '
                             'delivery of the function, at an organisation-defined frequency',
          'requirement_description': 'Is the organisation confident that it is performing vulnerability assessments across all '
                                     'its business-critical technology systems and assets? Examples may include:\n'
                                     ' -Operating systems (e.g. Windows, Linux);\n'
                                     ' -Virtualisation platforms (e.g. VMWare);\n'
                                     ' -Business applications (e.g. MS Office, Adobe, Java);\n'
                                     ' -Network communications equipment (e.g. routers, switches, firewalls, etc.);\n'
                                     ' -Storage platforms and devices;\n'
                                     ' -Operational Technology systems (e.g. SCADA applications, Energy Management Systems).\n'
                                     'Vulnerability assessments may be performed more frequently for some systems based on '
                                     'their criticality to the business or relative exposure to Cyber threats (e.g. '
                                     'Internet-accessible systems).',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': "TVM-2J: Cyber Security vulnerability assessments are informed by the function's (or "
                             "organisation's) risk criteria (RM-1c)",
          'requirement_description': 'Has the organisation defined a risk-based approach to performing Cyber Security '
                                     'vulnerability assessments? \n'
                                     'Vulnerability assessments may be performed more frequently for some systems based on '
                                     'their criticality to the business or relative exposure to Cyber threats (e.g. '
                                     'Internet-accessible systems). The nature of vulnerability assessment required may also '
                                     'be informed by an understanding of risk (e.g. Internet-accessible systems may be subject '
                                     'to penetration testing instead of just vulnerability scanning).',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2K: Cyber Security vulnerability assessments are performed by parties that are independent '
                             'of the operations of the function',
          'requirement_description': 'Are Cyber Security vulnerability assessments (refer TVM-2e and TVM-2i) performed by '
                                     'personnel who are independent of the system being assessed? \n'
                                     '\n'
                                     " An independent assessment may be performed internally (e.g. by an organisation's "
                                     'Internal Audit function) or externally (e.g. by a specialist provider).',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2L: Analysis and prioritisation of Cyber Security vulnerabilities are informed by the '
                             "function's (or organisation's) risk criteria (RM-1c)",
          'requirement_description': 'Are identified Cyber Security vulnerabilities assessed and prioritised in accordance '
                                     "with the organisation's broader risk management framework (refer RM-1c)? This may "
                                     'include consideration of how likely the vulnerability is to be exploited, and the '
                                     'potential impact of this occurring.',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2M: Cyber Security vulnerability information is added to the risk register (RM-2j)',
          'requirement_description': 'When Cyber Security vulnerabilities are identified, does the organisation capture these '
                                     'in a dedicated vulnerability tracker or risk register? \n'
                                     '\n'
                                     ' High-risk or high-profile vulnerabilities (e.g. WannaCry, NotPetya) may warrant their '
                                     'own entries in an operational/tactical risk register so they can be formally tracked, '
                                     'managed and reported throughout their lifecycle.\n'
                                     '\n'
                                     ' An organisation may also seek to use aggregated vulnerability information (e.g. from a '
                                     'dedicated vulnerability tracker) to adjust the likelihood of existing Cyber Security '
                                     'risks captured in its operational or strategic Security risk registers.',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-2N: Risk monitoring activities validate the responses to Cyber Security vulnerabilities '
                             '(e.g., deployment of patches or other activities)',
          'requirement_description': 'Does the organisation seek to validate that vulnerability remediation activities were '
                                     'carried out successfully? \n'
                                     '\n'
                                     ' Examples may include periodic vulnerability scanning to identify missing patches, or '
                                     're-testing of systems which have had high-rated vulnerabilities recently remediated.',
          'subchapter': 'TVM-2: Reduce Cyber Security Vulnerabilities'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-AP1: Where technical or business reasons restrict the ability to remediate an identified '
                             'vulnerability, no mitigating or compensating controls are investigated and applied',
          'requirement_description': 'Assets (such as networks, systems, and applications) can have cyber vulnerabilities. '
                                     'Some vulnerabilities are already known, and can be patched. Other vulnerabilities are '
                                     'yet to be discovered, highlighting the importance of preventative and compensating '
                                     'controls.\n'
                                     '\n'
                                     ' Applying a security patch is a common method to remediate a cyber security '
                                     'vulnerability, however it is not the only method. If applying a security patch is '
                                     'infeasible, you should explore and implement alternate controls.',
          'subchapter': 'TVM-AP: TVM Anti-Patterns'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-AP2: Internet-facing assets are not periodically assessed for cyber security vulnerabilities',
          'requirement_description': 'Internet-facing assets (such as networks, systems, and applications) may be accessible '
                                     'to anyone on the Internet, which can increase the level of attention that they receive '
                                     'from malicious threat actors.\n'
                                     '\n'
                                     ' As a result, there is an increased likelihood that cyber security vulnerabilities on '
                                     'Internet-facing assets may be exploited. Ensuring that Internet-facing assets are '
                                     'periodically assessed for cyber security vulnerabilities can support your ability to '
                                     'proactively remediate any cyber security vulnerabilities that are discovered.',
          'subchapter': 'TVM-AP: TVM Anti-Patterns'},
         {'chapter_title': 'TVM: Threat and Vulnerability Management',
          'conformity_questions': [],
          'objective_title': 'TVM-AP3: Controls are not updated in response to new and emerging high priority cyber threats',
          'requirement_description': 'The cyber security threat landscape is dynamic in nature - and new cyber security '
                                     'threats are frequently emerging.\n'
                                     'New cyber security threats that have the potential to impact the function should trigger '
                                     'a review of control effectiveness. Controls that are no longer effective considering the '
                                     'new cyber security threat should be updated.',
          'subchapter': 'TVM-AP: TVM Anti-Patterns'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-1A: Cyber Security responsibilities for the function are identified, at least in an ad hoc '
                             'manner',
          'requirement_description': 'Has the organisation defined the Cyber Security activities and processes which it needs '
                                     'to operate and maintain?',
          'subchapter': 'WM-1: Assign Cyber Security Responsibilities'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-1B: Cyber Security responsibilities are assigned to specific people, at least in an ad hoc '
                             'manner',
          'requirement_description': 'Are the Cyber Security activities identified in WM-1a assigned to specific people within '
                                     'the organisation?',
          'subchapter': 'WM-1: Assign Cyber Security Responsibilities'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-1C: Cyber Security responsibilities are assigned to specific roles, including external '
                             'service providers',
          'requirement_description': 'Rather than informally assigning Cyber Security responsibilities to individuals on an '
                                     'ad-hoc or best-efforts basis (refer WM-1b), has the organisation formally mapped its '
                                     'defined Cyber Security activities to specific roles or functions within the '
                                     'organisational structure? \n'
                                     '\n'
                                     ' An organisation may also decide to outsource the operation, management and support of '
                                     'some Cyber Security activities to external service providers, and this should also be '
                                     'reflected in the mapping of activities to roles.',
          'subchapter': 'WM-1: Assign Cyber Security Responsibilities'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-1D: Cyber Security responsibilities are documented (e.g., in position descriptions)',
          'requirement_description': 'Building on WM-1b and WM-1c, has the organisation formally documented the mapping of '
                                     'Cyber Security responsibilities to specific roles? This may include defining Cyber '
                                     'Security responsibilities in employee position descriptions, as well as within '
                                     'applicable policy, process and procedure documentation (e.g. RACI tables).',
          'subchapter': 'WM-1: Assign Cyber Security Responsibilities'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-1E: Cyber Security responsibilities and job requirements are reviewed and updated as '
                             'appropriate',
          'requirement_description': 'The Cyber Security activities performed by an organisation may change over time due to a '
                                     'range of factors, including:\n'
                                     ' -Changes in the Cyber threat environment;\n'
                                     ' -Introduction of new regulation and legislation;\n'
                                     ' -Broader organisational strategies that push towards in-sourcing or out-sourcing of '
                                     'Cyber Security capabilities.\n'
                                     '\n'
                                     ' As such, it is important that an organisation periodically assesses whether its '
                                     'existing Cyber Security capabilities are still meeting the needs of the business. This '
                                     'may result in changes to the structure or activities of the Cyber Security function.',
          'subchapter': 'WM-1: Assign Cyber Security Responsibilities'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-1F: Cyber Security responsibilities are included in job performance evaluation criteria',
          'requirement_description': 'Do you include the assigned and documented Cyber Security personnel requirements in job '
                                     'performance and evaluation criteria (e.g. performance reviews, promotional '
                                     'consideration, Key Performance Indicators (KPI))? \n'
                                     '\n'
                                     'Completing this practice ensures that the business function or organisation has '
                                     'established criteria to assess the ongoing suitability of personnel in roles with '
                                     'assigned Cyber Security requirements',
          'subchapter': 'WM-1: Assign Cyber Security Responsibilities'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-1G: Assigned Cyber Security responsibilities are managed to ensure adequacy and redundancy of '
                             'coverage',
          'requirement_description': "Do you also ensure that key person risks within the organisation's Cyber Security "
                                     'function are reduced  through cross-skilling of staff or other contingency measures?',
          'subchapter': 'WM-1: Assign Cyber Security Responsibilities'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2A: Personnel vetting (e.g., background checks, drug tests) is performed, at least in an ad '
                             'hoc manner, at hire for positions that have access to the assets required for delivery of the '
                             'function',
          'requirement_description': 'Do you conduct background checks and other vetting procedures when hiring personnel into '
                                     'positions that have access to business-critical assets? \n'
                                     '\n'
                                     ' Examples may include system administrators, control room operators, etc.',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2B: Personnel termination procedures address Cyber Security, at least in an ad hoc manner',
          'requirement_description': 'Are Cyber Security requirements considered when someone moves on from the organisation? '
                                     'Examples may include:\n'
                                     ' -Return of IT assets which may contain sensitive information (laptops, smartphones, '
                                     'etc.);\n'
                                     ' -Deprovisioning of user identities, access and credentials to systems;\n'
                                     ' -Enhanced monitoring for suspicious user behaviour in cases where employment was '
                                     'terminated for disciplinary reasons.',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2C: Personnel vetting is performed at an organisation-defined frequency for positions that '
                             'have access to the assets required for delivery of the function',
          'requirement_description': 'Are the background checks and other vetting procedures defined in WM-2a re-performed '
                                     'periodically for staff with access to business-critical assets?\n'
                                     '\n'
                                     'Completing this practice ensures that the business function or organisation has '
                                     'acknowledged that the results of personnel vetting may change over time, and that '
                                     'personnel who are suitable for a role at hire may not be suitable for a role at a later '
                                     'point in time.',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2D: Personnel transfer procedures address Cyber Security',
          'requirement_description': 'When personnel transfer between roles internally, does the transfer procedure include '
                                     'consideration of any specific Cyber Security requirements?\n'
                                     '\n'
                                     ' Examples may include reviewing and updating access to systems based on changing job '
                                     'responsibilities.',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2E: Risk designations are assigned to all positions that have access to the assets required '
                             'for delivery of the function',
          'requirement_description': 'Are job roles/positions within the organisation specifically identified as '
                                     'low/medium/high risk (or some other organisationally-defined designation) in accordance '
                                     'with the activities performed by those personnel? \n'
                                     '\n'
                                     'For example, are personnel with privileged access to business-critical assets (e.g. '
                                     'system administrators, control room operators, etc.) identified as high-risk?',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2F: Vetting is performed for all positions (including employees, vendors, and contractors) at '
                             'a level commensurate with position risk designation',
          'requirement_description': 'Building on WM-2a and WM-2c, do you change the level of vetting that is performed for a '
                                     'position based on its risk designation (WM-2e)? If so, does this occur equally for '
                                     'internal and external personnel? \n'
                                     '\n'
                                     'Completing this practice ensures that the business function or organisation has '
                                     'acknowledged the potential for insider threats to arise, both from internal personnel '
                                     'and third parties (contractors, suppliers, other entities). In some cases, personnel '
                                     'vetting commensurate with risk designation is mandated within a Network Service '
                                     "Provider's Operating License. Ensure that this has been considered when completing this "
                                     'practice',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2G: Succession planning is performed for personnel based on risk designation',
          'requirement_description': 'Similar to WM-1g, have you planned in advance for the succession of key personnel who '
                                     'have a high risk designation? If not, why not?\n'
                                     'Completing this practice ensures that key personnel who have a high risk designation '
                                     'have had their resignation or exit process defined in advance, and that redundancy of '
                                     'coverage has been considered (WM-1g)',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-2H: A formal accountability process that includes disciplinary actions is implemented for '
                             'personnel who fail to comply with established Security policies and procedures',
          'requirement_description': "Disciplinary processes would typically be managed by an organisation's Human Resources "
                                     '(HR / HC) function, consistent with how breaches of other policy are handled.',
          'subchapter': 'WM-2: Control the Workforce Life Cycle'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3A: Cyber Security training is made available, at least in an ad hoc manner, to personnel '
                             'with assigned Cyber Security responsibilities',
          'requirement_description': 'Does the organisation provide Cyber Security training to personnel with assigned Cyber '
                                     'Security responsibilities (refer WM-1b)?',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3B: Cyber Security knowledge, skill, and ability gaps are identified',
          'requirement_description': 'An organisation may identify that there are Cyber Security activities which are not able '
                                     'to be carried out by the existing workforce, requiring up-skilling of staff or hiring of '
                                     'new personnel.',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3C: Identified gaps are addressed through recruiting and/or training',
          'requirement_description': 'Where Cyber Security skills/capability gaps are identified (refer WM-3b), does the '
                                     'organisation take steps to fill these?',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3D: Cyber Security training is provided as a prerequisite to granting access to assets that '
                             'support the delivery of the function (e.g., new personnel training, personnel transfer training)',
          'requirement_description': 'An organisation may identify certain systems or assets that, due to their business '
                                     'criticality or risk profile, warrant specific user training to be undertaken prior to '
                                     'personnel being given access. \n'
                                     '\n'
                                     ' Examples may include an Energy Management System, SCADA application or Control Room.',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3E: Cyber Security workforce management objectives that support current and future '
                             'operational needs are established and maintained',
          'requirement_description': 'Has the organisation defined forward-looking objectives for its Cyber Security workforce '
                                     'to ensure that it can continue to implement, operate and improve the required Cyber '
                                     'Security capabilities and controls?\n'
                                     '\n'
                                     ' An example objective may include targeted hiring of specific Cyber Security skillsets '
                                     '(e.g. threat detection, incident response, etc.).',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3F: Recruiting and retention are aligned to support Cyber Security workforce management '
                             'objectives',
          'requirement_description': 'Does the organisation maintain a staff recruitment/continuity plan that covers its Cyber '
                                     'Security workforce? Has the plan been reviewed to ensure that it aligns to and supports '
                                     'the objectives defined in WM-3e?',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3G: Training programs are aligned to support Cyber Security workforce management objectives',
          'requirement_description': 'Does the organisation maintain a staff training/development plan that covers its Cyber '
                                     'Security workforce? Has the plan been reviewed to ensure that it aligns to and supports '
                                     'the objectives defined in WM-3e?',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3H: The effectiveness of training programs is evaluated at an organisation-defined frequency '
                             'and improvements are made as appropriate',
          'requirement_description': 'Has the organisation established how it will measure the effectiveness of Cyber Security '
                                     'training activities?\n'
                                     '\n'
                                     'One example may involve conducting red-teaming exercises to test the effectiveness of '
                                     'Security event detection capabilities.',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-3I: Training programs include continuing education and professional development opportunities '
                             'for personnel with significant Cyber Security responsibilities',
          'requirement_description': 'Does the organisation maintain professional development plans for personnel with key '
                                     'Cyber Security responsibilities? Development plans may highlight the need for staff to '
                                     'uplift certain skillsets or obtain specific qualifications or certifications.',
          'subchapter': 'WM-3: Develop Cyber Security Workforce'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-4A: Cyber Security awareness activities occur, at least in an ad hoc manner',
          'requirement_description': 'Does the organisation seek to increase the Cyber Security awareness of its workforce?',
          'subchapter': 'WM-4: Increase Cyber Security Awareness'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-4B: Objectives for Cyber Security awareness activities are established and maintained',
          'requirement_description': 'Has the organisation defined specific objectives for its Cyber Security awareness '
                                     'program? \n'
                                     '\n'
                                     ' Example objectives may include:\n'
                                     ' -Increasing the level of Cyber Security vigilance across the general user population;\n'
                                     ' -Reduce the number of Security incidents raised due to users clicking on suspicious '
                                     'links in phishing emails.',
          'subchapter': 'WM-4: Increase Cyber Security Awareness'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': "WM-4C: Cyber Security awareness content is based on the organisation's threat profile (TVM-1d)",
          'requirement_description': "Are the organisation's Cyber Security awareness initiatives specifically designed to "
                                     "address components of the organisation's Cyber threat profile (TVM-1d)? \n"
                                     '\n'
                                     'For example, if the threat profile has identified increase in spear-phishing attempts, '
                                     'are the Cyber Security awareness activities focused on how to identify and avoid a '
                                     'phishing email?\n'
                                     '\n'
                                     ' TVM-1d must be completed as a pre-requisite to this practice.',
          'subchapter': 'WM-4: Increase Cyber Security Awareness'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-4D: Cyber Security awareness activities are aligned with the predefined states of operation '
                             '(SA-3f)',
          'requirement_description': "Are the organisation's Cyber Security awareness initiatives specifically adjusted in "
                                     'accordance with the pre-defined states of operation (refer SA-3f) and the broader Common '
                                     'Operating Picture (refer SA-3)?\n'
                                     '\n'
                                     'For example, if the COP was elevated due to the identification of an active Cyber '
                                     'threat, does the organisation invoke pre-planned awareness mechanisms (e.g. '
                                     'whole-of-staff notification emails)?\n'
                                     '\n'
                                     'SA-3f must be completed as a pre-requisite to this practice.',
          'subchapter': 'WM-4: Increase Cyber Security Awareness'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-4E: The effectiveness of Cyber Security awareness activities is evaluated at an '
                             'organisation-defined frequency and improvements are made as appropriate',
          'requirement_description': 'Has the organisation established how it will measure the effectiveness of Cyber Security '
                                     'training activities?\n'
                                     '\n'
                                     'One example may involve conducting periodic phishing simulations to determine the '
                                     'overall Cyber Security awareness level of staff.',
          'subchapter': 'WM-4: Increase Cyber Security Awareness'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-AP1: Cyber security capabilities are dependent on one or two key personnel and no succession '
                             'plan is in place to ensure retention of critical knowledge',
          'requirement_description': 'Over time, organisations build cyber security knowledge that can become critical to the '
                                     'ongoing operation of their cyber security capabilities. If this cyber security knowledge '
                                     'is not documented, and only shared with one or two key personnel, then it may be lost '
                                     'should those personnel resign - especially if there is no succession plan in place.\n'
                                     '\n'
                                     'Cyber security knowledge that is critical to the ongoing operation of your cyber '
                                     'security capabilities should be documented and transitioned to the appropriate personnel '
                                     'as part of succession planning.',
          'subchapter': 'WM-AP: WM Anti-Patterns'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-AP2: Personnel interacting with critical assets are not assigned additional cyber security '
                             'responsibilities',
          'requirement_description': 'Critical assets (such as networks, systems, and applications) often carry a higher-risk '
                                     'of malicious targeting.\n'
                                     ' As a result, you should ensure that personnel who interact with these assets have been '
                                     'assigned additional cyber security responsibilities.\n'
                                     ' An example of an additional cyber security responsibility is ensuring that personnel '
                                     'who interact with critical assets have undergone advanced cyber security awareness '
                                     'training.',
          'subchapter': 'WM-AP: WM Anti-Patterns'},
         {'chapter_title': 'WM: Workforce Management',
          'conformity_questions': [],
          'objective_title': 'WM-AP3: Personnel interacting with critical assets are not aware of their additional assigned '
                             'cyber security responsibilities (WM-AP2)',
          'requirement_description': 'WM-AP2 must be Not Present for this Anti-Pattern to be Not Present.Similarly to WM-AP3, '
                                     'personnel who interact with critical assets (such as networks, systems, and '
                                     'applications) should be aware of their additional assigned cyber security '
                                     'responsibilities.',
          'subchapter': 'WM-AP: WM Anti-Patterns'}]
