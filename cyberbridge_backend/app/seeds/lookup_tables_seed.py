# app/seeds/lookup_tables_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class LookupTablesSeed(BaseSeed):
    """Seed lookup tables with reference data"""

    def seed(self) -> dict:
        logger.info("Creating lookup table data...")

        # Scope Types
        scope_types_data = [
            {"scope_name": "Product"},
            {"scope_name": "Organization"},
            {"scope_name": "Other"},
            {"scope_name": "Asset"},
            {"scope_name": "Project"},
            {"scope_name": "Process"}
        ]

        scope_types = {}
        for type_data in scope_types_data:
            scope_type, created = self.get_or_create(
                models.Scopes,
                {"scope_name": type_data["scope_name"]},
                type_data
            )
            scope_types[type_data["scope_name"]] = scope_type

        # Assessment Types
        assessment_types_data = [
            {"type_name": "conformity"},
            {"type_name": "audit"}
        ]

        assessment_types = {}
        for type_data in assessment_types_data:
            assessment_type, created = self.get_or_create(
                models.AssessmentType,
                {"type_name": type_data["type_name"]},
                type_data
            )
            assessment_types[type_data["type_name"]] = assessment_type

        # Policy Statuses
        policy_statuses_data = [
            {"status": "Draft"},
            {"status": "Review"},
            {"status": "Ready for Approval"},
            {"status": "Approved"}
        ]

        policy_statuses = {}
        for status_data in policy_statuses_data:
            status, created = self.get_or_create(
                models.PolicyStatuses,
                {"status": status_data["status"]},
                status_data
            )
            policy_statuses[status_data["status"]] = status

        # Economic Operators
        economic_operators_data = [
            {"name": "Manufacturer"},
            {"name": "Importer"},
            {"name": "Distributor"}
        ]

        economic_operators = {}
        for operator_data in economic_operators_data:
            operator, created = self.get_or_create(
                models.EconomicOperators,
                {"name": operator_data["name"]},
                operator_data
            )
            economic_operators[operator_data["name"]] = operator

        # Asset Categories (formerly Product Types)
        asset_categories_data = [
            {"name": "Hardware"},
            {"name": "Software"},
            {"name": "Cloud Service"},
            {"name": "Web Application"},
            {"name": "Mobile Application"},
            {"name": "API / Integration"},
            {"name": "Database / Data Store"},
            {"name": "Data Asset (PII/PHI/PCI)"},
            {"name": "Network Device"},
            {"name": "Endpoint Device"},
            {"name": "IoT / OT Device"},
            {"name": "Third-Party Vendor / Service"},
            {"name": "Identity System (IdP/SSO)"},
            {"name": "Business Process / Service"}
        ]

        asset_categories = {}
        for cat_data in asset_categories_data:
            asset_category, created = self.get_or_create(
                models.AssetCategories,
                {"name": cat_data["name"]},
                cat_data
            )
            asset_categories[cat_data["name"]] = asset_category

        # Risk Statuses
        risk_statuses_data = [
            {"risk_status_name": "Reduce"},
            {"risk_status_name": "Avoid"},
            {"risk_status_name": "Transfer"},
            {"risk_status_name": "Share"},
            {"risk_status_name": "Accept"},
            {"risk_status_name": "Remediated"}
        ]

        risk_statuses = {}
        for status_data in risk_statuses_data:
            status, created = self.get_or_create(
                models.RiskStatuses,
                {"risk_status_name": status_data["risk_status_name"]},
                status_data
            )
            risk_statuses[status_data["risk_status_name"]] = status

        # Risk Severity
        risk_severity_data = [
            {"risk_severity_name": "Low"},
            {"risk_severity_name": "Medium"},
            {"risk_severity_name": "High"},
            {"risk_severity_name": "Critical"}
        ]

        risk_severity = {}
        for severity_data in risk_severity_data:
            severity, created = self.get_or_create(
                models.RiskSeverity,
                {"risk_severity_name": severity_data["risk_severity_name"]},
                severity_data
            )
            risk_severity[severity_data["risk_severity_name"]] = severity

        # Risk Category Templates for Software-like Products
        software_risk_category_templates = [
            {
                "risk_category_name": "Vulnerabilities",
                "risk_category_description": "Unpatched or unknown vulnerabilities can be exploited by attackers.",
                "risk_potential_impact": "System compromise, data breaches",
                "risk_control": "Regular vulnerability scanning and patch management"
            },
            {
                "risk_category_name": "Access Control",
                "risk_category_description": "Weak authentication or improper access control can allow unauthorized access.",
                "risk_potential_impact": "Privilege escalation, data theft",
                "risk_control": "Implement MFA and least privilege access"
            },
            {
                "risk_category_name": "Communication Security",
                "risk_category_description": "Insecure data transmission may lead to data interception or tampering.",
                "risk_potential_impact": "Data leakage, MITM attacks",
                "risk_control": "Use modern encryption protocols and validate all inputs"
            },
            {
                "risk_category_name": "Supply Chain",
                "risk_category_description": "Incorporation of compromised third-party components without validation.",
                "risk_potential_impact": "Backdoors, supply chain attacks",
                "risk_control": "Maintain SBOM and verify supplier security practices"
            },
            {
                "risk_category_name": "Update Mechanism",
                "risk_category_description": "Insecure or missing update mechanisms allow attackers to inject malicious updates.",
                "risk_potential_impact": "Malware injection, delayed patching",
                "risk_control": "Implement signed updates and test update mechanisms"
            },
            {
                "risk_category_name": "Monitoring & Logging",
                "risk_category_description": "Lack of logging and monitoring hinders incident detection and response.",
                "risk_potential_impact": "Undetected incidents, compliance failure",
                "risk_control": "Enable secure logging and real-time monitoring"
            },
            {
                "risk_category_name": "Security-by-Design",
                "risk_category_description": "Security considerations are not embedded in the development lifecycle.",
                "risk_potential_impact": "Increased vulnerabilities, insecure architecture",
                "risk_control": "Adopt secure SDLC and perform code reviews"
            },
            {
                "risk_category_name": "User Misuse",
                "risk_category_description": "Users misconfigure or unknowingly disable security settings.",
                "risk_potential_impact": "Exploitation through user error",
                "risk_control": "Provide user training and clear documentation"
            },
            {
                "risk_category_name": "Legal & Compliance",
                "risk_category_description": "Non-compliance with CRA documentation, CE marking, or update obligations.",
                "risk_potential_impact": "Fines, legal action, product recall",
                "risk_control": "Ensure CE conformity and maintain records for 10 years"
            },
            {
                "risk_category_name": "Dependency Risk",
                "risk_category_description": "Use of outdated or unsupported dependencies or insecure configurations.",
                "risk_potential_impact": "Exploit chain through software layers",
                "risk_control": "Use supported software and conduct configuration reviews"
            }
        ]

        # Risk Category Templates for Hardware-like Products
        hardware_risk_category_templates = [
            {
                "risk_category_name": "Firmware Vulnerabilities",
                "risk_category_description": "Firmware may have exploitable bugs or lack update capabilities.",
                "risk_potential_impact": "Remote control, persistent malware",
                "risk_control": "Firmware security testing and secure update support"
            },
            {
                "risk_category_name": "Physical Security",
                "risk_category_description": "Devices may be physically tampered with or stolen.",
                "risk_potential_impact": "Theft, sabotage, physical compromise",
                "risk_control": "Tamper-evident seals, secure enclosures, GPS tracking"
            },
            {
                "risk_category_name": "Communication Interfaces",
                "risk_category_description": "Unsecured ports/interfaces may allow unauthorized access or data leakage.",
                "risk_potential_impact": "Data theft, system compromise via open interfaces",
                "risk_control": "Disable unused ports, secure interfaces with authentication"
            },
            {
                "risk_category_name": "Supply Chain Integrity",
                "risk_category_description": "Counterfeit or compromised hardware components can be introduced.",
                "risk_potential_impact": "Backdoors in the hardware level",
                "risk_control": "Validate supply chain, audit component sources"
            },
            {
                "risk_category_name": "Update Mechanism",
                "risk_category_description": "Lack of secure mechanisms to apply firmware or configuration updates.",
                "risk_potential_impact": "Undetected firmware attacks",
                "risk_control": "Implement secure boot and signed firmware updates"
            },
            {
                "risk_category_name": "Monitoring & Telemetry",
                "risk_category_description": "Hardware lacks monitoring or reporting of anomalies or failures.",
                "risk_potential_impact": "Delayed detection of failures or attacks",
                "risk_control": "Add monitoring chips or hardware health telemetry"
            },
            {
                "risk_category_name": "Design Flaws",
                "risk_category_description": "Design lacks hardware-based isolation or protections (e.g. secure boot).",
                "risk_potential_impact": "Bypass of security functions",
                "risk_control": "Include hardware-level access controls and isolation"
            },
            {
                "risk_category_name": "User Misuse",
                "risk_category_description": "Improper user handling or misconfiguration of physical settings.",
                "risk_potential_impact": "Damage, exposure due to incorrect setup",
                "risk_control": "Provide user manuals and safety/configuration guidance"
            },
            {
                "risk_category_name": "Legal & Compliance",
                "risk_category_description": "Failure to meet CRA hardware conformity, CE marking, or documentation.",
                "risk_potential_impact": "Fines, product recall, import bans",
                "risk_control": "Ensure proper technical files and CE compliance"
            },
            {
                "risk_category_name": "Component Dependency",
                "risk_category_description": "Obsolete components or reliance on insecure hardware elements.",
                "risk_potential_impact": "Inability to patch or mitigate issues effectively",
                "risk_control": "Use vetted suppliers and maintain obsolescence plans"
            }
        ]

        # Risk Category Templates for Data/Process/Vendor Products
        general_risk_category_templates = [
            {
                "risk_category_name": "Access Control",
                "risk_category_description": "Weak access controls can expose the asset or service to unauthorized use.",
                "risk_potential_impact": "Unauthorized access, data exposure, service abuse",
                "risk_control": "Least privilege, MFA, and regular access reviews"
            },
            {
                "risk_category_name": "Data Handling & Privacy",
                "risk_category_description": "Improper collection, storage, or sharing of sensitive data.",
                "risk_potential_impact": "Privacy breaches, regulatory penalties, loss of trust",
                "risk_control": "Data classification, encryption, and DLP controls"
            },
            {
                "risk_category_name": "Availability & Resilience",
                "risk_category_description": "Service or process downtime reduces operational capability.",
                "risk_potential_impact": "Business interruption, revenue loss",
                "risk_control": "Redundancy, backups, and disaster recovery plans"
            },
            {
                "risk_category_name": "Third-Party Dependency",
                "risk_category_description": "Reliance on external providers introduces supply-chain risk.",
                "risk_potential_impact": "Service disruption, security gaps",
                "risk_control": "Vendor risk management and strong SLAs"
            },
            {
                "risk_category_name": "Change Management",
                "risk_category_description": "Uncontrolled changes can introduce errors or security weaknesses.",
                "risk_potential_impact": "Instability, misconfiguration, policy drift",
                "risk_control": "Formal change control and approvals"
            },
            {
                "risk_category_name": "Monitoring & Logging",
                "risk_category_description": "Insufficient monitoring delays detection and response.",
                "risk_potential_impact": "Longer incident dwell time, compliance failure",
                "risk_control": "Centralized logging and alerting"
            },
            {
                "risk_category_name": "Compliance & Legal",
                "risk_category_description": "Failure to meet contractual or regulatory obligations.",
                "risk_potential_impact": "Fines, legal action, reputational harm",
                "risk_control": "Regular compliance reviews and documented controls"
            },
            {
                "risk_category_name": "Human Error",
                "risk_category_description": "Process misuse or mistakes lead to exposure or service impact.",
                "risk_potential_impact": "Data loss, service interruption",
                "risk_control": "Training, clear procedures, and guardrails"
            }
        ]

        software_like_categories = [
            "Software",
            "Cloud Service",
            "Web Application",
            "Mobile Application",
            "API / Integration",
            "Database / Data Store",
            "Identity System (IdP/SSO)"
        ]

        hardware_like_categories = [
            "Hardware",
            "Network Device",
            "Endpoint Device",
            "IoT / OT Device"
        ]

        general_categories = [
            "Data Asset (PII/PHI/PCI)",
            "Third-Party Vendor / Service",
            "Business Process / Service"
        ]

        risk_categories_data = []

        for cat_name in software_like_categories:
            asset_category = asset_categories.get(cat_name)
            if not asset_category:
                continue
            for template in software_risk_category_templates:
                risk_categories_data.append({
                    **template,
                    "asset_category_id": asset_category.id
                })

        for cat_name in hardware_like_categories:
            asset_category = asset_categories.get(cat_name)
            if not asset_category:
                continue
            for template in hardware_risk_category_templates:
                risk_categories_data.append({
                    **template,
                    "asset_category_id": asset_category.id
                })

        for cat_name in general_categories:
            asset_category = asset_categories.get(cat_name)
            if not asset_category:
                continue
            for template in general_risk_category_templates:
                risk_categories_data.append({
                    **template,
                    "asset_category_id": asset_category.id
                })

        risk_categories = {}
        for category_data in risk_categories_data:
            category, created = self.get_or_create(
                models.RiskCategories,
                {
                    "risk_category_name": category_data["risk_category_name"],
                    "asset_category_id": category_data["asset_category_id"]
                },
                category_data
            )
            key = f"{category_data['risk_category_name']}:{category_data['asset_category_id']}"
            risk_categories[key] = category

        # Criticalities
        criticalities_data = [
            {
                "label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I"
            },
            {
                "label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class II"
            },
            {
                "label": "ANNEX IV - CRITICAL PRODUCTS WITH DIGITAL ELEMENTS"
            }
        ]

        criticalities = {}
        for criticality_data in criticalities_data:
            criticality, created = self.get_or_create(
                models.Criticalities,
                {"label": criticality_data["label"]},
                criticality_data
            )
            criticalities[criticality_data["label"]] = criticality

        # Criticality Options
        criticality_options_data = [
            # ANNEX III Class I options
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Identity management systems and privileged access management software and hardware, including authentication and access control readers, including biometric readers"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Standalone and embedded browsers"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Password managers"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Software that searches for, removes, or quarantines malicious software"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Products with digital elements with the function of virtual private network (VPN)"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Network management systems"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Security information and event management (SIEM) systems"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Boot managers"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Public key infrastructure and digital certificate issuance software"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Physical and virtual network interfaces"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Operating systems"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Routers, modems intended for the connection to the internet, and switches"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Microprocessors with security-related functionalities"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Microcontrollers with security-related functionalities"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Application specific integrated circuits (ASIC) and field-programmable gate arrays (FPGA) with security-related functionalities"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Smart home general purpose virtual assistants"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Smart home products with security functionalities, including smart door locks, security cameras, baby monitoring systems and alarm systems"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Internet connected toys covered by Directive 2009/48/EC of the European Parliament and of the Council that have social interactive features (e.g. speaking or filming) or that have location tracking features"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I",
                "value": "Personal wearable products to be worn or placed on a human body that have a health monitoring (such as tracking) purpose and to which Regulation (EU) 2017/745 or Regulation (EU) 2017/746 do not apply, or personal wearable products that are intended for the use by and for children"
            },
            # ANNEX III Class II options
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class II",
                "value": "Hypervisors and container runtime systems that support virtualised execution of operating systems and similar environments"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class II",
                "value": "Firewalls, intrusion detection and prevention systems"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class II",
                "value": "Tamper-resistant microprocessors"
            },
            {
                "criticality_label": "ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class II",
                "value": "Tamper-resistant microcontrollers"
            },
            # ANNEX IV options
            {
                "criticality_label": "ANNEX IV - CRITICAL PRODUCTS WITH DIGITAL ELEMENTS",
                "value": "Hardware Devices with Security Boxes"
            },
            {
                "criticality_label": "ANNEX IV - CRITICAL PRODUCTS WITH DIGITAL ELEMENTS",
                "value": "Smart meter gateways within smart metering systems as defined in Article 2(23) of Directive (EU) 2019/944 of the European Parliament and of the Council and other devices for advanced security purposes, including for secure cryptoprocessing"
            },
            {
                "criticality_label": "ANNEX IV - CRITICAL PRODUCTS WITH DIGITAL ELEMENTS",
                "value": "Smartcards or similar devices, including secure elements"
            }
        ]

        criticality_options = {}
        for option_data in criticality_options_data:
            criticality_label = option_data.pop("criticality_label")
            criticality = criticalities[criticality_label]
            option_data["criticality_id"] = criticality.id

            option, created = self.get_or_create(
                models.CriticalityOptions,
                {"criticality_id": criticality.id, "value": option_data["value"]},
                option_data
            )
            criticality_options[option_data["value"]] = option

        # Compliance Statuses
        compliance_statuses_data = [
            {"status_name": "not assessed"},
            {"status_name": "not compliant"},
            {"status_name": "partially compliant"},
            {"status_name": "in review"},
            {"status_name": "compliant"},
            {"status_name": "not applicable"}
        ]

        compliance_statuses = {}
        for status_data in compliance_statuses_data:
            status, created = self.get_or_create(
                models.ComplianceStatuses,
                {"status_name": status_data["status_name"]},
                status_data
            )
            compliance_statuses[status_data["status_name"]] = status

        # Control Statuses
        control_statuses_data = [
            {"status_name": "Not Implemented"},
            {"status_name": "Partially Implemented"},
            {"status_name": "Implemented"},
            {"status_name": "N/A"}
        ]

        control_statuses = {}
        for status_data in control_statuses_data:
            status, created = self.get_or_create(
                models.ControlStatus,
                {"status_name": status_data["status_name"]},
                status_data
            )
            control_statuses[status_data["status_name"]] = status

        # Asset Statuses
        asset_statuses_data = [
            {"status": "Active"},
            {"status": "Inactive"},
            {"status": "Maintenance"},
            {"status": "Deprecated"},
            {"status": "Testing"},
            {"status": "Retired"}
        ]

        asset_statuses = {}
        for status_data in asset_statuses_data:
            status, created = self.get_or_create(
                models.AssetStatuses,
                {"status": status_data["status"]},
                status_data
            )
            asset_statuses[status_data["status"]] = status

        # Incident Statuses
        incident_statuses_data = [
            {"incident_status_name": "Open"},
            {"incident_status_name": "Investigating"},
            {"incident_status_name": "Contained"},
            {"incident_status_name": "Resolved"},
            {"incident_status_name": "Closed"},
        ]

        incident_statuses = {}
        for status_data in incident_statuses_data:
            status, created = self.get_or_create(
                models.IncidentStatuses,
                {"incident_status_name": status_data["incident_status_name"]},
                status_data
            )
            incident_statuses[status_data["incident_status_name"]] = status

        # Advisory Statuses (for Security Advisories)
        advisory_statuses_data = [
            {"status_name": "Draft"},
            {"status_name": "Review"},
            {"status_name": "Published"},
            {"status_name": "Updated"},
            {"status_name": "Archived"},
        ]

        advisory_statuses = {}
        for status_data in advisory_statuses_data:
            status, created = self.get_or_create(
                models.AdvisoryStatuses,
                {"status_name": status_data["status_name"]},
                status_data
            )
            advisory_statuses[status_data["status_name"]] = status

        return {
            "scope_types": scope_types,
            "assessment_types": assessment_types,
            "policy_statuses": policy_statuses,
            "economic_operators": economic_operators,
            "asset_categories": asset_categories,
            "risk_statuses": risk_statuses,
            "risk_severity": risk_severity,
            "risk_categories": risk_categories,
            "criticalities": criticalities,
            "criticality_options": criticality_options,
            "compliance_statuses": compliance_statuses,
            "control_statuses": control_statuses,
            "asset_statuses": asset_statuses,
            "incident_statuses": incident_statuses,
            "advisory_statuses": advisory_statuses,
        }
