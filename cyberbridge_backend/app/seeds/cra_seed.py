# app/seeds/cra_seed.py
import io
import logging
from .base_seed import BaseSeed
from app.models import models
from app.constants.cra_connections import CRA_CONNECTIONS
from app.utils.html_converter import convert_html_to_plain_text

logger = logging.getLogger(__name__)


class CraSeed(BaseSeed):
    """Seed CRA framework and its associated questions"""

    def __init__(self, db, organizations, assessment_types):
        super().__init__(db)
        self.organizations = organizations
        self.assessment_types = assessment_types

    def seed(self) -> dict:
        logger.info("Creating frameworks and questions...")

        # Get default organization (assuming first one is default)
        default_org = list(self.organizations.values())[0]
        conformity_assessment_type = self.assessment_types["conformity"]
        audit_assessment_type = self.assessment_types["audit"]

        # Create CRA Framework
        cra_framework, created = self.get_or_create(
            models.Framework,
            {"name": "CRA", "organisation_id": default_org.id},
            {
                "name": "CRA",
                "description": "Cyber Resilience Act compliance framework",
                "organisation_id": default_org.id,
                "allowed_scope_types": '["Product", "Other"]',
                "scope_selection_mode": 'required'
            }
        )

        # If framework already exists, skip question creation but still seed chapters/objectives
        if not created:
            logger.info("CRA framework already exists, skipping question creation but seeding chapters/objectives")

            # Get existing conformity questions for this framework
            existing_conformity_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == cra_framework.id,
                models.Question.assessment_type_id == conformity_assessment_type.id
            ).all()

            # Get existing audit questions for this framework
            existing_audit_questions = self.db.query(models.Question).join(
                models.FrameworkQuestion,
                models.Question.id == models.FrameworkQuestion.question_id
            ).filter(
                models.FrameworkQuestion.framework_id == cra_framework.id,
                models.Question.assessment_type_id == audit_assessment_type.id
            ).all()

            logger.info(f"Found existing CRA framework with {len(existing_conformity_questions)} conformity questions and {len(existing_audit_questions)} audit questions")

            # Continue to seed chapters/objectives below (don't return early)
            # This ensures new chapters (Importer/Distributor) and applicable_operators tags are added

        # CRA Questions
        cra_questions_data = [
            "Have you undertaken an assessment of the cybersecurity risks associated with your product with digital elements?",
            "Do you take the outcome of the cybersecurity risk assessment into account during the planning, design, development, production, delivery and maintenance phases?",
            "Is your cybersecurity risk assessment documented and updated as appropriate during the support period?",
            "Does your cybersecurity risk assessment comprise an analysis based on the intended purpose and reasonably foreseeable use of the product?",
            "Does your risk assessment take into account the conditions of use, operational environment, and assets to be protected?",
            "Does your risk assessment consider the length of time the product is expected to be in use?",
            "Does your cybersecurity risk assessment indicate whether and how the security requirements are applicable to your product?",
            "Do you include the cybersecurity risk assessment in the technical documentation when placing the product on the market?",
            "Where certain essential cybersecurity requirements are not applicable, do you include clear justification in the technical documentation?",
            "Do you systematically document relevant cybersecurity aspects concerning your products with digital elements?",
            "Do you document vulnerabilities of which you become aware and relevant information provided by third parties?",
            "Are your products with digital elements designed, developed and produced to ensure an appropriate level of cybersecurity based on the risks?",
            "Are your products with digital elements delivered without any known exploitable vulnerabilities?",
            "Are your products made available on the market with a secure by default configuration?",
            "Do you provide the possibility to reset the product to its original state?",
            "Do you ensure that vulnerabilities can be addressed through security updates?",
            "Are automatic security updates installed within an appropriate timeframe enabled as a default setting?",
            "Do you provide a clear and easy-to-use opt-out mechanism for automatic updates?",
            "Do you notify users of available updates with the option to temporarily postpone them?",
            "Do you ensure protection from unauthorized access by appropriate control mechanisms?",
            "Do you implement authentication, identity or access management systems?",
            "Do you report on possible unauthorized access?",
            "Do you protect the confidentiality of stored, transmitted or otherwise processed data through encryption?",
            "Do you use state-of-the-art mechanisms for encrypting relevant data at rest or in transit?",
            "Do you protect the integrity of stored, transmitted or otherwise processed data, commands, programs and configuration?",
            "Do you protect against manipulation or modification not authorized by the user?",
            "Do you report on corruptions of data, commands, programs and configuration?",
            "Do you process only data that is adequate, relevant and limited to what is necessary for the intended purpose?",
            "Do you protect the availability of essential and basic functions, also after an incident?",
            "Do you implement resilience and mitigation measures against denial-of-service attacks?",
            "Do you minimize the negative impact by your products on the availability of services provided by other devices or networks?",
            "Are your products designed, developed and produced to limit attack surfaces, including external interfaces?",
            "Are your products designed to reduce the impact of an incident using appropriate exploitation mitigation mechanisms?",
            "Do you provide security-related information by recording and monitoring relevant internal activity?",
            "Do you monitor access to or modification of data, services or functions with an opt-out mechanism for users?",
            "Do you provide the possibility for users to securely and easily remove all data and settings on a permanent basis?",
            "Where data can be transferred to other products or systems, do you ensure this is done in a secure manner?",
            "Do you identify and document vulnerabilities and components contained in your products with digital elements?",
            "Do you draw up a software bill of materials in a commonly used and machine-readable format?",
            "Does your software bill of materials cover at least the top-level dependencies of the products?",
            "Do you apply effective and regular tests and reviews of the security of your products with digital elements?",
            "Once a security update is made available, do you share and publicly disclose information about fixed vulnerabilities?",
            "Do you provide a description of vulnerabilities, affected products, impacts, severity and remediation information?",
            "Do you have a policy on coordinated vulnerability disclosure in place and enforced?",
            "Do you facilitate the sharing of information about potential vulnerabilities in your product and third-party components?",
            "Do you provide a contact address for reporting vulnerabilities discovered in your products?",
            "Do you provide mechanisms to securely distribute updates for your products with digital elements?",
            "Do you ensure vulnerabilities are fixed or mitigated in a timely manner through updates?",
            "Where applicable, are security updates distributed in an automatic manner?",
            "Do you disseminate security updates without delay when they are available to address identified security issues?",
            "Are security updates provided free of charge (unless otherwise agreed for tailor-made products)?",
            "Do you accompany security updates with advisory messages providing users with relevant information?"
        ]

        # Create questions and link them to the CRA framework
        cra_questions = []
        for i, question_text in enumerate(cra_questions_data):
            question, created = self.get_or_create(
                models.Question,
                {
                    "text": question_text,
                    "assessment_type_id": conformity_assessment_type.id
                },
                {
                    "text": question_text,
                    "description": f"CRA compliance question {i+1}",
                    "mandatory": True,
                    "assessment_type_id": conformity_assessment_type.id
                }
            )
            cra_questions.append(question)

            # Create framework-question relationship
            framework_question, created = self.get_or_create(
                models.FrameworkQuestion,
                {
                    "framework_id": cra_framework.id,
                    "question_id": question.id
                },
                {
                    "framework_id": cra_framework.id,
                    "question_id": question.id,
                    "order": i + 1
                }
            )
            # Ensure the order is set correctly even if the record already existed
            if not created and framework_question.order != i + 1:
                framework_question.order = i + 1
                self.db.commit()

        # CRA Audit Questions
        cra_audit_questions_data = [
            "Has the organization formally documented the scope of the CRA's applicability to its product portfolio and identified the role (manufacturer, importer, distributor)?",
            "Is there a comprehensive list of all products with digital elements, clearly indicating which are in scope of the CRA?",
            "Are security requirements formally defined and integrated into your product design and development lifecycle?",
            "Is there a formal, documented process for managing vulnerabilities throughout the product's entire lifecycle?",
            "How are Incidents identified, assessed, prioritized, and remediated? Can you show records of this process?",
            "Is there an approved Information Security Policy that explicitly addresses commitments related to CRA compliance and product cybersecurity?",
            "Are roles, responsibilities, and authorities for product cybersecurity clearly defined and communicated within the organization?",
            "Is comprehensive technical documentation (as per CRA requirements) available and up-to-date for each product?",
            "Is there a formal Coordinated Vulnerability Disclosure (CVD) policy in place, and is it accessible?",
            "Are security updates managed and distributed to users throughout the product's expected lifetime?",
            "Is there an established incident response plan specifically for cybersecurity incidents affecting products?",
            "Are there clear procedures for detecting, analyzing, containing, eradicating, and recovering from product-related security incidents?",
            "Are reporting obligations to ENISA and relevant CSIRTs clearly defined, including timelines and formats?",
            "Is there an approved Information Security Policy that outlines the organization's commitment to product cybersecurity and CRA compliance?",
            "Are roles, responsibilities, and authorities for cybersecurity clearly defined and communicated across all relevant teams (e.g., R&D, operations, legal)?",
            "Is a product-level cybersecurity risk management framework in place, and is it continuously applied throughout the product's lifecycle? Can you provide evidence of its application (e.g., risk registers, risk treatment plans)?",
            "Are user manuals and accompanying documentation clear, accessible, and comprehensive regarding the product's security features and secure operation?",
            "Is information on how users can report vulnerabilities or cybersecurity incidents to the manufacturer clearly provided in the product documentation?",
            "Is the defined support period for security updates clearly communicated and easily understandable by users in the product documentation?",
            "Does the organization have an EU Declaration of Conformity for each product with digital elements placed on the market?",
            "Is comprehensive technical documentation available for each product, covering all aspects required by Annex V of the CRA?",
            "Does the technical documentation include a general description, design/manufacturing info, risk assessment results, list of essential requirements, test reports, SBOM, and security update plan?",
            "Can you provide evidence of adherence to the chosen conformity assessment procedure (e.g., Module A, B+C, H) for each product category? (e.g., internal audit reports for Module A, Notified Body certificates for Modules B+C or H).",
            "Are regular internal audits conducted to verify ongoing compliance with CRA requirements for product cybersecurity?",
            "Are periodic management reviews of the ISMS conducted, including a review of product cybersecurity performance and CRA compliance status?",
            "Are procedures in place for cooperating with market surveillance authorities, including providing necessary information and assistance upon request?",
            "Are defined metrics and procedures in place for monitoring product cybersecurity performance (e.g., number of vulnerabilities, patch deployment rates, incident response times)?",
            "Are these metrics regularly collected, analyzed, and reported to relevant stakeholders?",
            "Are there established mechanisms for identifying opportunities for improvement in product cybersecurity processes and controls (e.g., lessons learned from incidents, feedback from users)?",
            "Do you have a Comprehensive Secure Development Lifecycle (SDLC) policy document?",
            "Do you have evidence of security requirements gathering in early development phases?",
            "Do you have a risk-based decision framework for security controls implementation?",
            "Do you have pre-release vulnerability scanning process documentation?",
            "Do you have a vulnerability remediation prioritization framework?",
            "Do you have documentation of secure default configurations for each product?",
            "Do you have evidence of unnecessary features and services being disabled by default?",
            "Do you have factory reset functionality design and implementation?",
            "Do you have user documentation describing secure configuration options?",
            "Does the organization periodically review system configurations to identify and disable unnecessary and/or non-secure functions, ports, protocols and services?",
            "How does the organisation ensure that only authorised users have access to systems and data, and that access is granted based on defined roles and responsibilities?",
            "What identity and access management (IAM) controls are in place to authenticate users and control their access to critical systems?",
            "Are authentication mechanisms (e.g., MFA, password policies) implemented and regularly reviewed?",
            "How is access reviewed and revoked when no longer needed (e.g., user offboarding, role change)?",
            "Are cryptographic keys securely managed and stored?",
            "What mechanisms are in place to ensure that data, software, and configurations are not tampered with or altered without authorisation?",
            "Are integrity checks (e.g. hashing, digital signatures) implemented and validated regularly?",
            "How are system and application configuration changes tracked and controlled?",
            "Is there a documented justification for each category of data processed by the product or service?",
            "Are regular reviews conducted to assess whether the data collected is still necessary?",
            "Are availability requirements defined for critical services?",
            "Is there a business continuity or disaster recovery plan to restore services in case of disruption?",
            "Are there incident detection and response mechanisms in place for availability-related threats?",
            "Does the product avoid generating unnecessary network traffic that could degrade the performance of other devices or services?",
            "Is the product designed to detect and prevent malfunctioning behaviours that could flood or overload networks or other devices?",
            "Are unnecessary services, ports, and interfaces disabled or removed from the final product?",
            "Is access to external interfaces restricted to authorised users or components only?",
            "Has a formal threat modeling or attack surface analysis been conducted during the design phase?",
            "Are secure coding practices followed to reduce vulnerabilities in the exposed functionalities?",
            "Are built-in mechanisms in place to limit the damage in case of successful exploitation (e.g., sandboxing, privilege separation)?",
            "Are security controls in place to detect and contain unusual behaviours or indicators of compromise?",
            "Are regular security updates and patches delivered to reduce residual risk from known exploits?",
            "Are logs generated for access to or modification of sensitive data, services, or configurations?",
            "Are privileged user activities and administrative actions recorded and reviewed periodically?",
            "Is alerting enabled for specific security events (e.g., failed logins, privilege escalations, data access anomalies)?",
            "Is there a defined process for developing and releasing security updates to address identified vulnerabilities?",
            "Does the product support secure delivery of updates (e.g., signed updates, secure channels)?",
            "Is automatic updating supported and enabled by default where appropriate?",
            "Are update failures logged and reported for investigation?",
            "Is there a maintained and regularly updated Software Bill of Materials (SBOM) for each release of the product?",
            "Are vulnerabilities in included components regularly identified (e.g., via automated vulnerability scanning or databases)?",
            "Is the SBOM used as part of the vulnerability management and risk assessment process?",
            "Is there a formal process to assess, prioritise, and remediate vulnerabilities based on risk?",
            "Are vulnerabilities remediated promptly in accordance with their criticality/severity (e.g., CVSS score, exploitability)?",
            "Are security updates developed and released without undue delay once a vulnerability is identified?",
            "Are regular security assessments (e.g. vulnerability scans, penetration tests, code reviews) performed on the product?",
            "Is security testing conducted during both development and post-deployment phases?",
            "Are secure coding practices enforced and verified through regular code audits or automated tools (e.g., SAST, DAST)?",
            "Are third-party components regularly tested or reviewed as part of overall product security testing?",
            "Is there a defined process for publicly disclosing fixed vulnerabilities after a security update is released?",
            "Is a clear and accessible communication channel (e.g. security advisory page, RSS feed, mailing list) available to users?",
            "Are vulnerability disclosures written in a structured format including severity (e.g., CVSS), impact, and remediation guidance?",
            "Is there a public-facing Coordinated Vulnerability Disclosure (CVD) Policy available (e.g., on your website)?",
            "Does the CVD policy define how external parties can report vulnerabilities securely (e.g., via encrypted email or web form)?",
            "Is there a dedicated, publicly accessible security contact address?",
            "Is the contact method secured (e.g., PGP key provided for encrypted communication)?",
            "Are internal procedures in place to triage and respond to vulnerability reports in a timely manner?",
            "Are vulnerability reports related to third-party components (e.g., open-source libraries) tracked and evaluated?",
            "Are security updates distributed through secure channels (e.g., TLS, VPN, secure APIs)?",
            "Are updates digitally signed to ensure their authenticity and integrity?",
            "Is there a mechanism in place to verify update authenticity before installation?",
            "Are security updates delivered automatically or promptly made available to users?",
            "Are all security patches and updates provided to users free of charge?",
            "Are patches distributed promptly once vulnerabilities are identified and fixes are available?",
            "Do users receive advisory messages along with patches or updates, explaining the issue, severity, and any action needed?"
        ]

        # Create audit questions and link them to the CRA framework
        cra_audit_questions = []
        # Start audit questions after conformity questions (52 conformity questions + 1)
        audit_start_order = len(cra_questions_data) + 1
        
        for i, question_text in enumerate(cra_audit_questions_data):
            question, created = self.get_or_create(
                models.Question,
                {
                    "text": question_text,
                    "assessment_type_id": audit_assessment_type.id
                },
                {
                    "text": question_text,
                    "description": f"CRA audit question {i+1}",
                    "mandatory": True,
                    "assessment_type_id": audit_assessment_type.id
                }
            )
            cra_audit_questions.append(question)

            # Create framework-question relationship
            framework_question, created = self.get_or_create(
                models.FrameworkQuestion,
                {
                    "framework_id": cra_framework.id,
                    "question_id": question.id
                },
                {
                    "framework_id": cra_framework.id,
                    "question_id": question.id,
                    "order": audit_start_order + i  # Start after conformity questions
                }
            )
            # Ensure the order is set correctly even if the record already existed
            if not created and framework_question.order != audit_start_order + i:
                framework_question.order = audit_start_order + i
                self.db.commit()

        # Create CRA Chapters and Objectives
        cra_chapters_objectives_data = self._get_objectives_data()

        # Create chapters and objectives for CRA framework
        cra_chapters = []
        cra_objectives = []

        for chapter_data in cra_chapters_objectives_data:
            # Create chapter
            chapter, created = self.get_or_create(
                models.Chapters,
                {
                    "title": chapter_data["chapter_title"],
                    "framework_id": cra_framework.id
                },
                {
                    "title": chapter_data["chapter_title"],
                    "framework_id": cra_framework.id
                }
            )
            cra_chapters.append(chapter)

            # Create objectives for this chapter
            for objective_data in chapter_data["objectives"]:
                objective, created = self.get_or_create(
                    models.Objectives,
                    {
                        "title": objective_data["title"],
                        "chapter_id": chapter.id
                    },
                    {
                        "title": objective_data["title"],
                        "subchapter": objective_data.get("subchapter", ""),
                        "chapter_id": chapter.id,
                        "requirement_description": objective_data["description"],
                        "objective_utilities": objective_data["needs"],
                        "applicable_operators": objective_data.get("applicable_operators")
                    }
                )
                # Update applicable_operators for existing objectives
                if not created and objective.applicable_operators != objective_data.get("applicable_operators"):
                    objective.applicable_operators = objective_data.get("applicable_operators")
                    self.db.commit()
                cra_objectives.append(objective)

        # Wire risks, controls, and policies to objectives
        if not self.skip_wire_connections:
            self._wire_connections(cra_framework, default_org, cra_chapters, cra_objectives)
        self.db.commit()

        return {
            "frameworks": {"CRA": cra_framework},
            "cra_questions": cra_questions,
            "cra_audit_questions": cra_audit_questions,
            "cra_chapters": cra_chapters,
            "cra_objectives": cra_objectives
        }

    @staticmethod
    def _get_objectives_data():
        """Return the CRA chapters and objectives seed data.
        Static so it can be called from chain_links_service without instantiating."""
        return [
            {
                "chapter_title": "Chapter I - General Provisions",
                "objectives": [
                    {
                        "title": "Article 1 - Subject Matter and Article 2: Scope",
                        "description": "Understanding the applicability of the CRA to products with digital elements and key terminology.",
                        "needs": "Information Security Objectives and Plan, CRA Strategy Policy and Scope, Product Registry Form",
                        "subchapter": "Scope and Applicability",
                        "applicable_operators": None
                    },
                    {
                        "title": "Article 6 (Requirements for Products with Digital Elements) & Annex I (Essential Requirements)",
                        "description": "Products with digital elements must meet essential cybersecurity requirements throughout their lifecycle, including security by design, vulnerability management, and incident prevention.",
                        "needs": "Product Registry Form, Secure Development Policy, Vulnerability Management Policy, Patch Management Policy, Logging And Monitoring Policy",
                        "subchapter": "Essential Cybersecurity Requirements",
                        "applicable_operators": None
                    }
                ]
            },
            {
                "chapter_title": "Chapter II - Obligations of Economic Operators",
                "objectives": [
                    {
                        "title": "Article 13 (Obligations of Manufacturers)",
                        "description": "Manufacturers have comprehensive obligations, including ensuring products meet essential requirements, drawing up technical documentation, conducting conformity assessments, providing security updates, and handling vulnerabilities.",
                        "needs": "Information Security Policy, Organizational Roles, Responsibilities And Authorities, Product Registry Form, Vulnerability Management Policy, Incident Management Policy, Corrective Action Procedures, Product Lifecycle Management (PLM) Policy",
                        "subchapter": "Manufacturer Obligations and Responsibilities",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "Article 14 (Reporting of Actively Exploited Vulnerabilities and Incidents)",
                        "description": "Manufacturers must report actively exploited vulnerabilities and serious cybersecurity incidents to ENISA and relevant CSIRTs within specified timelines.",
                        "needs": "Incident Management Policy, Corrective Action Procedures, External Communications Policy, Contact Procedure With Local Authorities",
                        "subchapter": "Vulnerability and Incident Reporting",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "Article 25 (Security Measures)",
                        "description": "Manufacturers must put in place appropriate and proportionate internal processes and measures to ensure compliance with the CRA.",
                        "needs": "Information Security Policy, Product Cybersecurity Policy, Management Review Minutes, Information Security Objectives & Plan, Confidentiality Policy, Physical Security Policy, Secure Code Policy, Encryption Policy, Risk Management Policy, Risk Assessment Methodology",
                        "subchapter": "Internal Security Processes and Controls",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "Article 26 (Guidance)",
                        "description": "Manufacturers should provide users with clear and accessible instructions and information on the secure installation, operation, and maintenance of the product.",
                        "needs": "Product Registry Form, Information Security Policy, Secure Development Policy, Acceptable use Policy, Vulnerability Management Policy",
                        "subchapter": "User Documentation and Guidance",
                        "applicable_operators": '["Manufacturer"]'
                    }
                ]
            },
            {
                "chapter_title": "Chapter III - Conformity of the Products with Digital Elements",
                "objectives": [
                    {
                        "title": "Article 28 (EU Declaration of Conformity) & Annex V (Technical Documentation)",
                        "description": "Manufacturers must draw up an EU declaration of conformity and compile technical documentation demonstrating that the product meets the essential requirements.",
                        "needs": "EU Declaration of Conformity Template, Product Registry Form, Procedure For Control Of Documented Information",
                        "subchapter": "Conformity Assessment and Documentation",
                        "applicable_operators": '["Manufacturer"]'
                    }
                ]
            },
            {
                "chapter_title": "Chapter V - Market Surveillance, Control of Products with Digital Elements Entering the Union Market and Union Safeguard Procedure",
                "objectives": [
                    {
                        "title": "Article 52 (Market Surveillance Authorities) & Article 54 (Procedure at National Level for Products Presenting a Cybersecurity Risk)",
                        "description": "Market surveillance authorities will monitor compliance, and procedures are in place for addressing non-compliant products.",
                        "needs": "Internal Audit Procedure, Corrective Action Procedures, Information Security Policy, Procedure For Control Of Documented Information, Management Review Procedure, Information Security Communication Plan",
                        "subchapter": "Market Surveillance and Compliance Monitoring",
                        "applicable_operators": None
                    },
                    {
                        "title": "Article 70 (Evaluation and Review)",
                        "description": "The Commission will evaluate the CRA, highlighting the importance of ongoing performance assessment by economic operators.",
                        "needs": "Performance Measurement Policy, Management Review Procedure, Information Security Objectives & Plan, Information Security Policy, Information Security Communication Plan",
                        "subchapter": "Continuous Evaluation and Improvement",
                        "applicable_operators": None
                    }
                ]
            },
            {
                "chapter_title": "ANNEX I",
                "objectives": [
                    {
                        "title": "1",
                        "description": "Products with digital elements shall be designed, developed and produced in such a way that they ensure an appropriate level of cybersecurity based on the risks",
                        "needs": "Comprehensive Secure Development Lifecycle (SDLC) policy document, Vulnerability Management Policy, Acceptable Use Policy",
                        "subchapter": "Secure Product Design and Development",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "2",
                        "description": "Products with digital elements shall be delivered without any known exploitable vulnerabilities",
                        "needs": "Vulnerability Management Policy, Patch Management Policy",
                        "subchapter": "Secure Product Design and Development",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3a",
                        "description": "Be delivered with a secure by default configuration, including the possibility to reset the product to its original state",
                        "needs": "Asset Management Policy, Secure Coding Policy, Password Policy, Encryption Policy, Information Security Policy, Configuration Management Policy",
                        "subchapter": "Secure Configuration Management",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3b",
                        "description": "ensure protection from unauthorised access by appropriate control mechanisms, including but not limited to authentication, identity or access management systems;",
                        "needs": "Password Policy, Encryption Policy, Access Control Policy, Log and Monitoring Policy, Awareness Policy",
                        "subchapter": "Access Control and Authentication",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3c",
                        "description": "Protect the confidentiality of stored, transmitted or otherwise processed data through encryption",
                        "needs": "Encryption Policy",
                        "subchapter": "Data Protection",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3d",
                        "description": "Protect the integrity of stored, transmitted or otherwise processed data, commands, programs and configuration against manipulation or modification",
                        "needs": "Change Management Policy, Encryption Policy, Secure Development Policy, Logging and Monitoring Policy, Access Control Policy",
                        "subchapter": "Data Protection",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3e",
                        "description": "process only data, personal or other, that are adequate, relevant and limited to what is necessary in relation to the intended use of the product ('minimisation of data');",
                        "needs": "Data Retention Policy, Data Protection Policy, Access Control Policy, Third-Party Data Processing Policy, Product Registry Entry",
                        "subchapter": "Data Protection",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3f",
                        "description": "protect the availability of essential functions, including the resilience against and mitigation of denial of service attacks;",
                        "needs": "Monitoring and Logging Policy, Network Security Policy, Availability Policy",
                        "subchapter": "Availability and Resilience",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3g",
                        "description": "Minimize their own negative impact on the availability of services provided by other devices or networks",
                        "needs": "Incident Response Plan, Logging and Monitoring Policy",
                        "subchapter": "Availability and Resilience",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3h",
                        "description": "Be designed, developed and produced to limit attack surfaces, including external interfaces",
                        "needs": "Secure Development Policy, Software Development Lifecycle (SDLC), Configuration Management Procedure, Change Management Policy, Vulnerability Management Procedure",
                        "subchapter": "Attack Surface and Incident Mitigation",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3i",
                        "description": "Be designed, developed and produced to reduce the impact of an incident using appropriate exploitation mitigation mechanisms and techniques;",
                        "needs": "Secure Development Policy, Vulnerability Management Procedure, Incident Response Plan, System Hardening Standards, Logging and Monitoring Policy",
                        "subchapter": "Attack Surface and Incident Mitigation",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3j",
                        "description": "provide security related information by recording and/or monitoring relevant internal activity, including the access to or modification of data, services or functions;",
                        "needs": "Logging and Monitoring Policy, Privileged Access Management Procedure",
                        "subchapter": "Security Monitoring and Logging",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3k",
                        "description": "ensure that vulnerabilities can be addressed through security updates, including, where applicable, through automatic updates and the notification of available updates to users.",
                        "needs": "Vulnerability Management Procedure, Secure Development Policy, Software Update and Patch Management Policy, Change Management Policy",
                        "subchapter": "Security Update Management",
                        "applicable_operators": '["Manufacturer"]'
                    }
                ]
            },
            {
                "chapter_title": "Vulnerability Handling",
                "objectives": [
                    {
                        "title": "1",
                        "description": "identify and document vulnerabilities and components contained in the product, including by drawing up a software bill of materials in a commonly used and machine-readable format covering at the very least the top-level dependencies of the product;",
                        "needs": "Product Registry Entry, Third-Party Software Policy, Secure Development Policy, Vulnerability Management Procedure, Supply Chain Risk Management Policy, Release Management Procedure",
                        "subchapter": "Vulnerability Identification and Testing",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "2",
                        "description": "In relation to the risks posed to the products with digital elements, address and remediate vulnerabilities without delay, including by providing security updates;",
                        "needs": "Vulnerability Management Procedure, Security Patch and Update Policy, Change Management Policy, Threat Intelligence and Monitoring Procedure",
                        "subchapter": "Vulnerability Identification and Testing",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "3",
                        "description": "apply effective and regular tests and reviews of the security of the product with digital elements;",
                        "needs": "Secure Development Lifecycle (SDLC) Policy, Vulnerability Management Policy",
                        "subchapter": "Vulnerability Identification and Testing",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "4",
                        "description": "once a security update has been made available, publically disclose information about fixed vulnerabilities, including a description of the vulnerabilities, information allowing users to identify the product with digital elements affected, the impacts of the vulnerabilities, their severity and information helping users to remediate the vulnerabilities;",
                        "needs": "Incident Response and Communication Plan, Security Communications Plan, Secure Development Policy",
                        "subchapter": "Vulnerability Disclosure",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "5",
                        "description": "put in place and enforce a policy on coordinated vulnerability disclosure;",
                        "needs": "Vulnerability Management Policy, Incident Response Plan",
                        "subchapter": "Vulnerability Disclosure",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "6",
                        "description": "take measures to facilitate the sharing of information about potential vulnerabilities in their product with digital elements as well as in third party components contained in that product, including by providing a contact address for the reporting of the vulnerabilities discovered in the product with digital elements;",
                        "needs": "Vulnerability Management Policy, Third-Party Security Policy",
                        "subchapter": "Vulnerability Disclosure",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "7",
                        "description": "provide for mechanisms to securely distribute updates for products with digital elements to ensure that exploitable vulnerabilities are fixed or mitigated in a timely manner;",
                        "needs": "Patch Management and Update Policy, Secure Software Delivery Procedure, Change Management Policy, Monitoring and Logging Policy, Product Lifecycle and Support Policy",
                        "subchapter": "Security Update Distribution",
                        "applicable_operators": '["Manufacturer"]'
                    },
                    {
                        "title": "8",
                        "description": "ensure that, where security patches or updates are available to address identified security issues, they are disseminated without delay and free of charge, accompanied by advisory messages providing users with the relevant information, including on potential action to be taken.",
                        "needs": "Security Patch Management Policy, Security Advisory Communication Procedure, Incident Response Plan, Vulnerability Disclosure Policy",
                        "subchapter": "Security Update Distribution",
                        "applicable_operators": '["Manufacturer"]'
                    }
                ]
            },
            {
                "chapter_title": "Obligations of Importers",
                "objectives": [
                    {
                        "title": "Article 19(1) - Market Placement Due Diligence",
                        "description": "Importers shall only place products with digital elements on the Union market that comply with the essential cybersecurity requirements set out in Annex I.",
                        "needs": "Importer Due Diligence Procedure, Product Compliance Checklist, CRA Strategy Policy and Scope",
                        "subchapter": "Importer Due Diligence",
                        "applicable_operators": '["Importer"]'
                    },
                    {
                        "title": "Article 19(2) - Conformity Verification",
                        "description": "Before placing a product with digital elements on the market, importers shall ensure that the manufacturer has carried out the appropriate conformity assessment procedure and has drawn up the technical documentation.",
                        "needs": "Conformity Assessment Verification Procedure, Technical Documentation Review Checklist",
                        "subchapter": "Importer Due Diligence",
                        "applicable_operators": '["Importer"]'
                    },
                    {
                        "title": "Article 19(3) - CE Marking and Documentation",
                        "description": "Importers shall ensure that the product with digital elements bears the CE marking and is accompanied by the EU declaration of conformity and required information and instructions to the user.",
                        "needs": "CE Marking Verification Procedure, Product Documentation Checklist",
                        "subchapter": "Importer Compliance",
                        "applicable_operators": '["Importer"]'
                    },
                    {
                        "title": "Article 19(4) - Importer Identification",
                        "description": "Importers shall indicate their name, registered trade name or registered trademark, and the postal and email address at which they can be contacted on the product or its packaging, or in a document accompanying the product.",
                        "needs": "Importer Identification Procedure, Product Labelling Policy",
                        "subchapter": "Importer Compliance",
                        "applicable_operators": '["Importer"]'
                    },
                    {
                        "title": "Article 19(5) - Non-Conformity Actions",
                        "description": "Where an importer considers or has reason to believe that a product with digital elements is not in conformity with the essential requirements, the importer shall not place the product on the market until it has been brought into conformity, and shall inform the manufacturer and market surveillance authorities.",
                        "needs": "Non-Conformity Handling Procedure, Corrective Action Procedures, Market Surveillance Communication Plan",
                        "subchapter": "Importer Corrective Actions",
                        "applicable_operators": '["Importer"]'
                    },
                    {
                        "title": "Article 19(6) - Vulnerability Awareness",
                        "description": "Importers who become aware of vulnerabilities in a product with digital elements shall inform the manufacturer without undue delay and cooperate with the manufacturer on corrective measures.",
                        "needs": "Vulnerability Reporting Procedure, Manufacturer Communication Protocol, Incident Management Policy",
                        "subchapter": "Importer Corrective Actions",
                        "applicable_operators": '["Importer"]'
                    }
                ]
            },
            {
                "chapter_title": "Obligations of Distributors",
                "objectives": [
                    {
                        "title": "Article 20(1) - Due Care",
                        "description": "Distributors shall act with due care in relation to the requirements of the CRA when making a product with digital elements available on the market.",
                        "needs": "Distributor Due Care Policy, CRA Compliance Checklist, Product Handling Procedures",
                        "subchapter": "Distributor Due Diligence",
                        "applicable_operators": '["Distributor"]'
                    },
                    {
                        "title": "Article 20(2) - Verification Before Distribution",
                        "description": "Before making a product with digital elements available on the market, distributors shall verify that the product bears the CE marking, the manufacturer and the importer have complied with their identification and documentation obligations.",
                        "needs": "Pre-Distribution Verification Checklist, CE Marking Verification Procedure, Documentation Review Procedure",
                        "subchapter": "Distributor Due Diligence",
                        "applicable_operators": '["Distributor"]'
                    },
                    {
                        "title": "Article 20(3) - Non-Conformity Actions",
                        "description": "Where a distributor considers or has reason to believe that a product with digital elements is not in conformity with the essential requirements, the distributor shall not make the product available on the market until it has been brought into conformity.",
                        "needs": "Non-Conformity Handling Procedure, Corrective Action Procedures, Product Quarantine Policy",
                        "subchapter": "Distributor Corrective Actions",
                        "applicable_operators": '["Distributor"]'
                    },
                    {
                        "title": "Article 20(4) - Risk Notification",
                        "description": "Distributors shall inform the relevant market surveillance authorities if a product with digital elements presents a significant cybersecurity risk, providing details on non-conformity and any corrective measures taken.",
                        "needs": "Market Surveillance Notification Procedure, Risk Assessment Policy, Incident Management Policy",
                        "subchapter": "Distributor Corrective Actions",
                        "applicable_operators": '["Distributor"]'
                    },
                    {
                        "title": "Article 20(5) - Record Keeping",
                        "description": "Distributors shall maintain records of products with digital elements they have made available on the market and keep such records available for market surveillance authorities for a period of ten years.",
                        "needs": "Record Keeping Policy, Product Traceability Procedure, Data Retention Policy",
                        "subchapter": "Distributor Documentation",
                        "applicable_operators": '["Distributor"]'
                    }
                ]
            }
        ]

    # ── Chapters whose objectives use composite keys in CRA_CONNECTIONS ──
    _COMPOSITE_KEY_CHAPTERS = {"ANNEX I", "Vulnerability Handling"}

    def _wire_connections(self, framework, org, chapters_list, objectives_list):
        """
        Create org-level risks, controls, policies from templates and wire
        them to CRA objectives using the CRA_CONNECTIONS mapping.
        """
        import mammoth

        # ── Step 1: Look up defaults ──
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
            logger.warning("Missing lookup defaults — skipping CRA connection wiring")
            return

        # Collect all unique entity references from the mapping
        all_risk_names = set()
        all_control_codes = set()
        all_policy_codes = set()
        for conn in CRA_CONNECTIONS.values():
            all_risk_names.update(conn["risks"])
            all_control_codes.update(conn["controls"])
            all_policy_codes.update(conn["policies"])

        # ── Step 2: Create org-level risks ──
        risk_name_to_id = {}

        # Fetch risk templates by name
        risk_templates = self.db.query(models.RiskTemplate).filter(
            models.RiskTemplate.risk_category_name.in_(all_risk_names)
        ).all()
        risk_template_map = {rt.risk_category_name: rt for rt in risk_templates}

        # Prefer asset category from risk categories when available
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

        # Check existing org risks
        existing_risks = self.db.query(models.Risks).filter(
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
        max_code_row = self.db.query(models.Risks.risk_code).filter(
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
            self.db.add(risk)
            self.db.flush()
            risk_name_to_id[risk_name] = risk.id

        logger.info(f"CRA wiring: {len(risk_name_to_id)} risks ready")

        # ── Step 3: Create org-level controls (Baseline only) ──
        control_code_to_id = {}

        # Get or create Baseline ControlSet
        baseline_set, _ = self.get_or_create(
            models.ControlSet,
            {"name": "Baseline Controls", "organisation_id": org.id},
            {"name": "Baseline Controls",
             "description": "General baseline controls covering HR, Governance, Risk Management, Security, and Compliance",
             "organisation_id": org.id}
        )

        # Fetch control templates
        control_templates = self.db.query(models.ControlTemplate).filter(
            models.ControlTemplate.code.in_(all_control_codes)
        ).all()
        ctrl_template_map = {ct.code: ct for ct in control_templates}

        # Check existing org controls
        existing_controls = self.db.query(models.Control).filter(
            models.Control.organisation_id == org.id,
            models.Control.code.in_(all_control_codes)
        ).all()
        for c in existing_controls:
            control_code_to_id[c.code] = c.id

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

        logger.info(f"CRA wiring: {len(control_code_to_id)} controls ready")

        # ── Step 4: Create org-level policies ──
        policy_code_to_id = {}

        # Check existing org policies
        existing_policies = self.db.query(models.Policies).filter(
            models.Policies.organisation_id == org.id,
            models.Policies.policy_code.in_(all_policy_codes)
        ).all()
        for p in existing_policies:
            policy_code_to_id[p.policy_code] = p.id

        # Fetch policy templates
        policy_templates = self.db.query(models.PolicyTemplate).filter(
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
                    logger.warning(f"CRA wiring: docx conversion failed for {pol_code}: {conv_err}")
            policy = models.Policies(
                title=tmpl.title if tmpl else pol_code,
                policy_code=pol_code,
                status_id=draft_status.id,
                body=body_text,
                organisation_id=org.id,
            )
            self.db.add(policy)
            self.db.flush()
            policy_code_to_id[pol_code] = policy.id

        logger.info(f"CRA wiring: {len(policy_code_to_id)} policies ready")

        # ── Step 5: Create connections ──
        # Build objective lookup using composite keys for chapters with
        # short/numeric titles that overlap (ANNEX I, Vulnerability Handling).
        chapter_id_to_title = {ch.id: ch.title for ch in chapters_list}
        obj_key_to_id = {}
        for obj in objectives_list:
            ch_title = chapter_id_to_title.get(obj.chapter_id, "")
            if ch_title in self._COMPOSITE_KEY_CHAPTERS:
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

        for obj_key, conn in CRA_CONNECTIONS.items():
            obj_id = obj_key_to_id.get(obj_key)
            if not obj_id:
                logger.warning(f"CRA wiring: objective not found for key '{obj_key}'")
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
                existing = self.db.query(models.ObjectiveRisk).filter_by(
                    objective_id=obj_id, risk_id=risk_id
                ).first()
                if not existing:
                    self.db.add(models.ObjectiveRisk(objective_id=obj_id, risk_id=risk_id))
                    obj_risk_count += 1

            # ObjectiveControl links
            for ctrl_code in conn["controls"]:
                ctrl_id = control_code_to_id.get(ctrl_code)
                if not ctrl_id:
                    continue
                resolved_control_ids.append(ctrl_id)
                existing = self.db.query(models.ObjectiveControl).filter_by(
                    objective_id=obj_id, control_id=ctrl_id
                ).first()
                if not existing:
                    self.db.add(models.ObjectiveControl(objective_id=obj_id, control_id=ctrl_id))
                    obj_ctrl_count += 1

            # PolicyObjective links
            for pol_code in conn["policies"]:
                pol_id = policy_code_to_id.get(pol_code)
                if not pol_id:
                    continue
                resolved_policy_ids.append(pol_id)
                existing = self.db.query(models.PolicyObjectives).filter_by(
                    policy_id=pol_id, objective_id=obj_id
                ).first()
                if not existing:
                    self.db.add(models.PolicyObjectives(policy_id=pol_id, objective_id=obj_id))
                    pol_obj_count += 1
                policy_framework_pairs.add((pol_id, framework.id))

            # Derive ControlRisk links from each objective's risk/control sets.
            # This powers the risk -> control segment in Compliance Chain Map.
            for ctrl_id in resolved_control_ids:
                for risk_id in resolved_risk_ids:
                    pair = (ctrl_id, risk_id, framework.id)
                    if pair in planned_control_risk_pairs:
                        continue
                    existing = self.db.query(models.ControlRisk).filter_by(
                        control_id=ctrl_id, risk_id=risk_id, framework_id=framework.id
                    ).first()
                    if not existing:
                        self.db.add(models.ControlRisk(control_id=ctrl_id, risk_id=risk_id, framework_id=framework.id))
                        ctrl_risk_count += 1
                    planned_control_risk_pairs.add(pair)

            # Derive ControlPolicy links from each objective's control/policy sets.
            # This powers the control -> policy segment in Compliance Chain Map.
            for ctrl_id in resolved_control_ids:
                for pol_id in resolved_policy_ids:
                    pair = (ctrl_id, pol_id, framework.id)
                    if pair in planned_control_policy_pairs:
                        continue
                    existing = self.db.query(models.ControlPolicy).filter_by(
                        control_id=ctrl_id, policy_id=pol_id, framework_id=framework.id
                    ).first()
                    if not existing:
                        self.db.add(models.ControlPolicy(control_id=ctrl_id, policy_id=pol_id, framework_id=framework.id))
                        ctrl_pol_count += 1
                    planned_control_policy_pairs.add(pair)

        # PolicyFramework links
        pf_count = 0
        for pol_id, fw_id in policy_framework_pairs:
            existing = self.db.query(models.PolicyFrameworks).filter_by(
                policy_id=pol_id, framework_id=fw_id
            ).first()
            if not existing:
                self.db.add(models.PolicyFrameworks(policy_id=pol_id, framework_id=fw_id))
                pf_count += 1

        self.db.flush()
        logger.info(
            f"CRA wiring complete: {obj_risk_count} objective-risk, "
            f"{obj_ctrl_count} objective-control, {pol_obj_count} policy-objective, "
            f"{ctrl_risk_count} control-risk, {ctrl_pol_count} control-policy, "
            f"{pf_count} policy-framework links created"
        )