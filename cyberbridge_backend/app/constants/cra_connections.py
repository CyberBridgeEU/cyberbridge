# CRA (Cyber Resilience Act) objective-to-entity connections.
# Maps each CRA objective title to its connected risks, controls, and policies.
#
# - risks:    matched by risk_category_name in risk_templates
# - controls: matched by control code (e.g. "APD-1", "CVM-1") in Baseline Controls
# - policies: matched by POL code (e.g. "POL-21") in policy_templates
#
# Objectives from ANNEX I and Vulnerability Handling use composite keys
# ("ChapterTitle::ObjectiveTitle") because their short numeric titles overlap.

CRA_CONNECTIONS = {
    # ── Chapter I - General Provisions ──────────────────────────────────────

    "Article 1 - Subject Matter and Article 2: Scope": {
        "risks": [
            "Fines and judgements",
            "Inability to support business processes",
            "Incorrect controls scoping",
        ],
        "controls": [
            "GOV-5",   # Information Security Policy
            "GOV-8",   # Maintain list of statutory/regulatory requirements
            "GOV-11",  # Review scope of ISMS
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-21",  # Information Security Policy
            "POL-55",  # Information Security Objectives And Plan
            "POL-49",  # CRA Strategy Policy And Scope
            "POL-50",  # Product Registry Form
        ],
    },

    "Article 6 (Requirements for Products with Digital Elements) & Annex I (Essential Requirements)": {
        "risks": [
            "Unpatched vulnerability exploitation",
            "Unmitigated vulnerabilities",
            "Lack of design reviews & security testing",
        ],
        "controls": [
            "APD-1",   # Secure coding practices
            "APD-2",   # Periodic security review
            "APD-6",   # Software development policy
            "CVM-1",   # Vulnerability scan quarterly
            "CVM-7",   # Patch management policy
            "ALM-5",   # Logging and monitoring policy
        ],
        "policies": [
            "POL-33",  # Software Development Lifecycle Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-26",  # Patch Management Policy
            "POL-22",  # Logging And Monitoring Policy
            "POL-50",  # Product Registry Form
        ],
    },

    # ── Chapter II - Obligations of Economic Operators ──────────────────────

    "Article 13 (Obligations of Manufacturers)": {
        "risks": [
            "Fines and judgements",
            "Lack of roles & responsibilities",
            "Inadequate internal practices",
            "Improper response to incidents",
        ],
        "controls": [
            "GOV-4",   # Security team / CISO
            "GOV-5",   # Information Security Policy
            "HRM-11",  # Defined roles and responsibilities
            "IRM-6",   # Incident management policy
            "CVM-1",   # Vulnerability scan
            "APD-2",   # Security review
        ],
        "policies": [
            "POL-21",  # Information Security Policy
            "POL-20",  # Incident Management Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-38",  # Corrective Action Procedures
            "POL-52",  # Organizational Roles Responsibilities And Authorities
            "POL-50",  # Product Registry Form
            "POL-53",  # Product Lifecycle Management Policy
        ],
    },

    "Article 14 (Reporting of Actively Exploited Vulnerabilities and Incidents)": {
        "risks": [
            "Improper response to incidents",
            "Inability to investigate / prosecute incidents",
            "Fines and judgements",
        ],
        "controls": [
            "IRM-1",   # Incident response team
            "IRM-2",   # Management reviews incidents monthly
            "IRM-3",   # Contact info for authorities
            "IRM-4",   # Incidents tracked and reported
            "IRM-5",   # Incident reporting for employees/vendors
            "IRM-6",   # Incident management policy
            "CCI-3",   # Information Security Communication plans
        ],
        "policies": [
            "POL-20",  # Incident Management Policy
            "POL-38",  # Corrective Action Procedures
            "POL-37",  # Contact Procedure With Local Authorities
            "POL-54",  # External Communications Policy
        ],
    },

    "Article 25 (Security Measures)": {
        "risks": [
            "Inadequate internal practices",
            "Lack of oversight of internal controls",
            "Incorrect controls scoping",
        ],
        "controls": [
            "GOV-3",   # Internal controls monitored and adjusted
            "GOV-5",   # Information Security Policy
            "GOV-6",   # Annual risk assessment
            "GOV-10",  # Review objectives periodically
            "GOV-12",  # Internal audits at regular intervals
            "PES-4",   # Physical security policy
            "CRY-4",   # Cryptography policy
            "RSM-2",   # Risk assessment and management policy
        ],
        "policies": [
            "POL-21",  # Information Security Policy
            "POL-14",  # Confidentiality Policy
            "POL-28",  # Physical Security Policy
            "POL-19",  # Encryption Policy
            "POL-30",  # Risk Management Policy
            "POL-33",  # Software Development Lifecycle Policy (Secure Code Policy)
            "POL-51",  # Product Cybersecurity Policy
            "POL-91",  # Management Review Minutes
            "POL-55",  # Information Security Objectives And Plan
            "POL-58",  # Risk Assessment Methodology
        ],
    },

    "Article 26 (Guidance)": {
        "risks": [
            "Lack of cybersecurity awareness",
            "Lack of a security-minded workforce",
        ],
        "controls": [
            "GOV-1",   # Policies available to all personnel
            "APD-1",   # Secure coding practices
            "HRM-8",   # Security awareness training
            "AST-4",   # Acceptable use policy
        ],
        "policies": [
            "POL-21",  # Information Security Policy
            "POL-33",  # Software Development Lifecycle Policy
            "POL-2",   # Acceptable Use Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-50",  # Product Registry Form
        ],
    },

    # ── Chapter III - Conformity of Products ────────────────────────────────

    "Article 28 (EU Declaration of Conformity) & Annex V (Technical Documentation)": {
        "risks": [
            "Fines and judgements",
            "Incorrect controls scoping",
        ],
        "controls": [
            "GOV-8",   # Statutory/regulatory requirements
            "GOV-12",  # Internal audits
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-48",  # Procedure For Control Of Documented Information
            "POL-89",  # EU Declaration Of Conformity Template
            "POL-50",  # Product Registry Form
        ],
    },

    # ── Chapter V - Market Surveillance ─────────────────────────────────────

    "Article 52 (Market Surveillance Authorities) & Article 54 (Procedure at National Level for Products Presenting a Cybersecurity Risk)": {
        "risks": [
            "Fines and judgements",
            "Inadequate internal practices",
            "Lack of oversight of internal controls",
        ],
        "controls": [
            "GOV-3",   # Internal controls monitored
            "GOV-12",  # Internal audits
            "CCI-3",   # Communication plans
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-44",  # Internal Audit Procedure
            "POL-38",  # Corrective Action Procedures
            "POL-21",  # Information Security Policy
            "POL-48",  # Procedure For Control Of Documented Information
            "POL-45",  # Management Review Procedure
            "POL-56",  # Information Security Communication Plan
        ],
    },

    "Article 70 (Evaluation and Review)": {
        "risks": [
            "Inability to support business processes",
            "Inadequate internal practices",
        ],
        "controls": [
            "GOV-3",   # Internal controls monitored
            "GOV-10",  # Review objectives periodically
            "GOV-11",  # Review scope of ISMS
            "CCI-3",   # Communication plans
        ],
        "policies": [
            "POL-45",  # Management Review Procedure
            "POL-21",  # Information Security Policy
            "POL-57",  # Performance Measurement Policy
            "POL-55",  # Information Security Objectives And Plan
            "POL-56",  # Information Security Communication Plan
        ],
    },

    # ── ANNEX I - Essential Cybersecurity Requirements ──────────────────────
    # Keys use "ANNEX I::<title>" composite format to avoid duplicates.

    "ANNEX I::1": {
        # Secure Product Design and Development
        "risks": [
            "Lack of design reviews & security testing",
            "Unmitigated vulnerabilities",
            "System compromise",
        ],
        "controls": [
            "APD-1",   # Secure coding practices
            "APD-2",   # Periodic security review
            "APD-4",   # Static and Dynamic Code Analysis
            "APD-5",   # Separate Production and Non-Production
            "APD-6",   # Software development policy
            "GOV-6",   # Annual risk assessment
        ],
        "policies": [
            "POL-33",  # Software Development Lifecycle Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-2",   # Acceptable Use Policy
        ],
    },

    "ANNEX I::2": {
        # No Known Exploitable Vulnerabilities
        "risks": [
            "Unpatched vulnerability exploitation",
            "Zero-Day Exploit",
            "Unmitigated vulnerabilities",
        ],
        "controls": [
            "CVM-1",   # Vulnerability scan quarterly
            "CVM-2",   # Penetration testing quarterly
            "CVM-3",   # Patch server OS and container OS
            "CVM-7",   # Patch management policy
            "APD-4",   # Static and Dynamic Code Analysis
        ],
        "policies": [
            "POL-35",  # Vulnerability Management Policy
            "POL-26",  # Patch Management Policy
        ],
    },

    "ANNEX I::3a": {
        # Secure by Default Configuration
        "risks": [
            "Security misconfiguration of APIs / Applications",
            "Cloud misconfiguration",
            "Misconfiguration of employee endpoints",
        ],
        "controls": [
            "CMM-2",   # Monitor baseline configuration
            "CM-3",    # Configuration management policy
            "APD-1",   # Secure coding practices
            "IAM-9",   # Password Policy
            "CRY-2",   # Encrypt sensitive data at rest
        ],
        "policies": [
            "POL-15",  # Configuration Management Policy
            "POL-1",   # Password Policy
            "POL-19",  # Encryption Policy
            "POL-21",  # Information Security Policy
            "POL-7",   # Asset Management Policy
            "POL-33",  # Software Development Lifecycle Policy (Secure Coding Policy)
        ],
    },

    "ANNEX I::3b": {
        # Access Control and Authentication
        "risks": [
            "Unauthorized access",
            "Brute force attack",
            "Privilege escalation",
            "Broken or weak authentication",
            "Broken or weak access control in the application",
        ],
        "controls": [
            "IAM-1",   # Access on request basis after approval
            "IAM-2",   # Access logged and monitored
            "IAM-3",   # Account review; expired/orphan deleted
            "IAM-4",   # Privileged access requires approval
            "IAM-5",   # Secure authentication
            "IAM-6",   # MFA for sensitive systems
            "IAM-7",   # Access control enforcement
            "IAM-8",   # Access control policy
            "IAM-9",   # Password Policy
        ],
        "policies": [
            "POL-1",   # Password Policy
            "POL-19",  # Encryption Policy
            "POL-4",   # Access Management Policy
            "POL-22",  # Logging And Monitoring Policy
            "POL-59",  # Awareness Policy
        ],
    },

    "ANNEX I::3c": {
        # Data Confidentiality (Encryption)
        "risks": [
            "Data breach",
            "Weak cryptography & encryption support in the application",
            "Man in the middle (MitM) attack for Network",
        ],
        "controls": [
            "CRY-1",   # Encryption of data in transit
            "CRY-2",   # Encrypt sensitive data at rest
            "CRY-3",   # Key management and rotation
            "CRY-4",   # Cryptography policy
        ],
        "policies": [
            "POL-19",  # Encryption Policy
        ],
    },

    "ANNEX I::3d": {
        # Data Integrity
        "risks": [
            "Loss of integrity through unauthorized changes",
            "Unauthorized changes",
            "Data loss / corruption",
        ],
        "controls": [
            "CRY-1",   # Encryption of data in transit
            "CRY-2",   # Encrypt sensitive data at rest
            "CHM-1",   # Changes tracked, reported, communicated
            "CHM-3",   # Change Management Policy
            "IAM-7",   # Access control enforcement
            "ALM-2",   # Log management systems
            "CVM-4",   # File integrity monitoring
        ],
        "policies": [
            "POL-11",  # Change Management Policy
            "POL-19",  # Encryption Policy
            "POL-33",  # Software Development Lifecycle Policy
            "POL-22",  # Logging And Monitoring Policy
            "POL-4",   # Access Management Policy
        ],
    },

    "ANNEX I::3e": {
        # Data Minimization
        "risks": [
            "Data breach",
            "Accidental disclosure of sensitive customer data during support or other operations",
            "Third-party compliance / legal exposure",
        ],
        "controls": [
            "DCH-1",   # Sensitive data inventory documented
            "DCH-2",   # Data classified by use and sensitivity
            "DCH-4",   # Data disposed per retention policy
            "DCH-5",   # Data classification and handling policy
            "PRIV-1",  # Privacy policy shared publicly
            "PRIV-5",  # Data use communicated to subjects
            "PRIV-6",  # Personal info used for intended purposes
        ],
        "policies": [
            "POL-17",  # Data Retention Policy
            "POL-16",  # Data Classification Policy
            "POL-4",   # Access Management Policy
            "POL-60",  # Third-Party Data Processing Policy
            "POL-50",  # Product Registry Form
        ],
    },

    "ANNEX I::3f": {
        # Availability and Resilience
        "risks": [
            "Denial of Service (DoS) Attack",
            "Denial Of Service (DoS)",
            "Business interruption",
            "Availability & Disaster recovery",
        ],
        "controls": [
            "ALM-1",   # Monitoring and alarm system
            "ALM-3",   # SIEM for security events
            "NES-1",   # WAF
            "NES-2",   # IDS / IPS
            "NES-4",   # Block known malicious IPs
            "BCD-2",   # Geographically redundant infrastructure
            "BCD-4",   # Availability Policy
        ],
        "policies": [
            "POL-22",  # Logging And Monitoring Policy
            "POL-24",  # Network Management Policy
            "POL-8",   # Availability Policy
        ],
    },

    "ANNEX I::3g": {
        # Minimize Impact on Other Services
        "risks": [
            "Business interruption",
            "Denial of Service (DoS) Attack",
            "Emergent properties and/or unintended consequences",
        ],
        "controls": [
            "IRM-1",   # Incident response team
            "IRM-6",   # Incident management policy
            "ALM-1",   # Monitoring and alarm system
            "NES-3",   # Network separation
        ],
        "policies": [
            "POL-20",  # Incident Management Policy
            "POL-22",  # Logging And Monitoring Policy
        ],
    },

    "ANNEX I::3h": {
        # Attack Surface Limitation
        "risks": [
            "System compromise",
            "Information loss / corruption or system compromise due to technical attack",
            "Unmitigated vulnerabilities",
        ],
        "controls": [
            "APD-1",   # Secure coding practices
            "APD-2",   # Periodic security review
            "APD-4",   # Static and Dynamic Code Analysis
            "APD-5",   # Separate Production and Non-Production
            "CHM-4",   # Application/Infrastructure change management
            "CMM-2",   # Monitor baseline configuration
            "NES-5",   # Block unauthorized ports
        ],
        "policies": [
            "POL-33",  # Software Development Lifecycle Policy
            "POL-15",  # Configuration Management Policy
            "POL-11",  # Change Management Policy
            "POL-35",  # Vulnerability Management Policy
        ],
    },

    "ANNEX I::3i": {
        # Incident Impact Mitigation
        "risks": [
            "Improper response to incidents",
            "Ineffective remediation actions",
            "System compromise",
        ],
        "controls": [
            "IRM-1",   # Incident response team
            "IRM-4",   # Incidents tracked and reported
            "IRM-6",   # Incident management policy
            "CVM-5",   # Malware protection software
            "APD-1",   # Secure coding practices
            "ALM-1",   # Monitoring and alarm system
        ],
        "policies": [
            "POL-20",  # Incident Management Policy
            "POL-33",  # Software Development Lifecycle Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-22",  # Logging And Monitoring Policy
            "POL-61",  # System Hardening Standards
        ],
    },

    "ANNEX I::3j": {
        # Security Monitoring and Logging
        "risks": [
            "Insufficient logging",
            "Insufficient monitoring & alerting",
            "Inability to maintain individual accountability",
        ],
        "controls": [
            "ALM-1",   # Monitoring and alarm system
            "ALM-2",   # Log management systems
            "ALM-3",   # SIEM
            "ALM-4",   # Adequate log storage per retention
            "ALM-5",   # Logging and monitoring policy
            "IAM-2",   # Access logged and monitored
            "IAM-4",   # Privileged access requires approval
        ],
        "policies": [
            "POL-22",  # Logging And Monitoring Policy
            "POL-4",   # Access Management Policy
        ],
    },

    "ANNEX I::3k": {
        # Security Update Management
        "risks": [
            "Unpatched vulnerability exploitation",
            "Unmitigated vulnerabilities",
        ],
        "controls": [
            "CVM-1",   # Vulnerability scan
            "CVM-3",   # Patch server OS and container OS
            "CVM-7",   # Patch management policy
            "CHM-1",   # Changes tracked, reported, communicated
            "CHM-2",   # Change approval process
            "CHM-4",   # Application/Infrastructure change management
        ],
        "policies": [
            "POL-26",  # Patch Management Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-11",  # Change Management Policy
            "POL-33",  # Software Development Lifecycle Policy
        ],
    },

    # ── Vulnerability Handling ──────────────────────────────────────────────
    # Keys use "Vulnerability Handling::<title>" composite format.

    "Vulnerability Handling::1": {
        # Vulnerability Identification and SBOM
        "risks": [
            "Software supply chain malware attack",
            "Third-party supply chain relationships, visibility and controls",
            "Unmitigated vulnerabilities",
        ],
        "controls": [
            "CVM-1",   # Vulnerability scan
            "APD-2",   # Periodic security review
            "TPM-1",   # Vendor contracts
            "TPM-3",   # Vendor risk assessment
            "TPM-4",   # Vendor management policy
            "AST-1",   # Asset inventory
        ],
        "policies": [
            "POL-35",  # Vulnerability Management Policy
            "POL-33",  # Software Development Lifecycle Policy
            "POL-34",  # Vendor Management Policy
            "POL-50",  # Product Registry Form
            "POL-69",  # Release Management Procedure
        ],
    },

    "Vulnerability Handling::2": {
        # Vulnerability Remediation
        "risks": [
            "Unpatched vulnerability exploitation",
            "Zero-Day Exploit",
            "Unmitigated vulnerabilities",
        ],
        "controls": [
            "CVM-1",   # Vulnerability scan
            "CVM-3",   # Patch server OS and container OS
            "CVM-7",   # Patch management policy
            "CHM-1",   # Changes tracked
            "CHM-2",   # Change approval process
        ],
        "policies": [
            "POL-35",  # Vulnerability Management Policy
            "POL-26",  # Patch Management Policy
            "POL-11",  # Change Management Policy
            "POL-62",  # Threat Intelligence And Monitoring Procedure
        ],
    },

    "Vulnerability Handling::3": {
        # Regular Security Testing
        "risks": [
            "Lack of design reviews & security testing",
            "Unmitigated vulnerabilities",
        ],
        "controls": [
            "CVM-1",   # Vulnerability scan
            "CVM-2",   # Penetration testing
            "APD-2",   # Periodic security review
            "APD-4",   # Static and Dynamic Code Analysis
        ],
        "policies": [
            "POL-35",  # Vulnerability Management Policy
            "POL-33",  # Software Development Lifecycle Policy
        ],
    },

    "Vulnerability Handling::4": {
        # Vulnerability Disclosure
        "risks": [
            "Improper response to incidents",
            "Fines and judgements",
        ],
        "controls": [
            "IRM-4",   # Incidents tracked and reported
            "IRM-5",   # Incident reporting for employees/vendors
            "CCI-3",   # Communication plans
        ],
        "policies": [
            "POL-20",  # Incident Management Policy
            "POL-33",  # Software Development Lifecycle Policy
            "POL-63",  # Security Communications Plan
        ],
    },

    "Vulnerability Handling::5": {
        # Coordinated Vulnerability Disclosure Policy
        "risks": [
            "Improper response to incidents",
            "Inability to investigate / prosecute incidents",
        ],
        "controls": [
            "CVM-1",   # Vulnerability scan
            "IRM-1",   # Incident response team
            "IRM-6",   # Incident management policy
        ],
        "policies": [
            "POL-35",  # Vulnerability Management Policy
            "POL-20",  # Incident Management Policy
        ],
    },

    "Vulnerability Handling::6": {
        # Vulnerability Reporting Mechanisms
        "risks": [
            "Third-party cybersecurity exposure",
            "Exposure to third party vendors",
        ],
        "controls": [
            "IRM-5",   # Incident reporting for employees/vendors
            "TPM-1",   # Vendor contracts
            "TPM-4",   # Vendor management policy
            "CCI-3",   # Communication plans
        ],
        "policies": [
            "POL-35",  # Vulnerability Management Policy
            "POL-34",  # Vendor Management Policy
            "POL-43",  # ICT 3rd Party Security Standards
        ],
    },

    "Vulnerability Handling::7": {
        # Secure Update Distribution
        "risks": [
            "Software supply chain malware attack",
            "Unpatched vulnerability exploitation",
        ],
        "controls": [
            "CVM-3",   # Patch server OS and container OS
            "CVM-7",   # Patch management policy
            "CHM-1",   # Changes tracked
            "CHM-4",   # Application/Infrastructure change management
            "ALM-1",   # Monitoring and alarm system
            "APD-1",   # Secure coding practices
        ],
        "policies": [
            "POL-26",  # Patch Management Policy
            "POL-11",  # Change Management Policy
            "POL-22",  # Logging And Monitoring Policy
            "POL-64",  # Secure Software Delivery Procedure
            "POL-65",  # Product Lifecycle And Support Policy
        ],
    },

    "Vulnerability Handling::8": {
        # Timely and Free Security Updates
        "risks": [
            "Unpatched vulnerability exploitation",
            "Unmitigated vulnerabilities",
            "Fines and judgements",
        ],
        "controls": [
            "CVM-3",   # Patch server OS and container OS
            "CVM-7",   # Patch management policy
            "IRM-4",   # Incidents tracked and reported
            "CCI-3",   # Communication plans
        ],
        "policies": [
            "POL-26",  # Patch Management Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-20",  # Incident Management Policy
            "POL-66",  # Security Advisory Communication Procedure
        ],
    },

    # ── Obligations of Importers ────────────────────────────────────────────

    "Article 19(1) - Market Placement Due Diligence": {
        "risks": [
            "Fines and judgements",
            "Third-party compliance / legal exposure",
            "Lack of oversight of third-party controls",
        ],
        "controls": [
            "TPM-1",   # Vendor contracts
            "TPM-2",   # Vendor attestation reports
            "TPM-3",   # Vendor risk assessment
            "GOV-8",   # Statutory/regulatory requirements
        ],
        "policies": [
            "POL-34",  # Vendor Management Policy
            "POL-43",  # ICT 3rd Party Security Standards
            "POL-70",  # Importer Due Diligence Procedure
            "POL-71",  # Product Compliance Checklist
            "POL-49",  # CRA Strategy Policy And Scope
        ],
    },

    "Article 19(2) - Conformity Verification": {
        "risks": [
            "Fines and judgements",
            "Lack of oversight of third-party controls",
        ],
        "controls": [
            "TPM-2",   # Vendor attestation reports
            "GOV-12",  # Internal audits
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-34",  # Vendor Management Policy
            "POL-48",  # Procedure For Control Of Documented Information
            "POL-72",  # Conformity Assessment Verification Procedure
            "POL-73",  # Technical Documentation Review Checklist
        ],
    },

    "Article 19(3) - CE Marking and Documentation": {
        "risks": [
            "Fines and judgements",
            "Incorrect controls scoping",
        ],
        "controls": [
            "GOV-8",   # Statutory/regulatory requirements
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-48",  # Procedure For Control Of Documented Information
            "POL-74",  # CE Marking Verification Procedure
            "POL-75",  # Product Documentation Checklist
        ],
    },

    "Article 19(4) - Importer Identification": {
        "risks": [
            "Fines and judgements",
        ],
        "controls": [
            "GOV-1",   # Policies available to all
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-48",  # Procedure For Control Of Documented Information
            "POL-76",  # Importer Identification Procedure
            "POL-77",  # Product Labelling Policy
        ],
    },

    "Article 19(5) - Non-Conformity Actions": {
        "risks": [
            "Fines and judgements",
            "Inadequate third-party practices",
            "Improper response to incidents",
        ],
        "controls": [
            "IRM-3",   # Contact info for authorities
            "IRM-4",   # Incidents tracked and reported
            "TPM-1",   # Vendor contracts
        ],
        "policies": [
            "POL-38",  # Corrective Action Procedures
            "POL-37",  # Contact Procedure With Local Authorities
            "POL-78",  # Non-Conformity Handling Procedure
            "POL-79",  # Market Surveillance Communication Plan
        ],
    },

    "Article 19(6) - Vulnerability Awareness": {
        "risks": [
            "Unpatched vulnerability exploitation",
            "Third-party cybersecurity exposure",
        ],
        "controls": [
            "IRM-5",   # Incident reporting
            "TPM-1",   # Vendor contracts
            "CVM-1",   # Vulnerability scan
        ],
        "policies": [
            "POL-20",  # Incident Management Policy
            "POL-35",  # Vulnerability Management Policy
            "POL-67",  # Vulnerability Reporting Procedure
            "POL-68",  # Manufacturer Communication Protocol
        ],
    },

    # ── Obligations of Distributors ─────────────────────────────────────────

    "Article 20(1) - Due Care": {
        "risks": [
            "Fines and judgements",
            "Inadequate third-party practices",
            "Lack of oversight of third-party controls",
        ],
        "controls": [
            "GOV-8",   # Statutory/regulatory requirements
            "TPM-1",   # Vendor contracts
            "TPM-2",   # Vendor attestation reports
        ],
        "policies": [
            "POL-34",  # Vendor Management Policy
            "POL-80",  # Distributor Due Care Policy
            "POL-90",  # CRA Compliance Checklist
            "POL-81",  # Product Handling Procedures
        ],
    },

    "Article 20(2) - Verification Before Distribution": {
        "risks": [
            "Fines and judgements",
            "Lack of oversight of third-party controls",
        ],
        "controls": [
            "TPM-2",   # Vendor attestation reports
            "GOV-8",   # Statutory/regulatory requirements
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-34",  # Vendor Management Policy
            "POL-48",  # Procedure For Control Of Documented Information
            "POL-82",  # Pre-Distribution Verification Checklist
            "POL-74",  # CE Marking Verification Procedure
            "POL-83",  # Documentation Review Procedure
        ],
    },

    "Article 20(3) - Non-Conformity Actions": {
        "risks": [
            "Fines and judgements",
            "Inadequate third-party practices",
        ],
        "controls": [
            "IRM-3",   # Contact info for authorities
            "IRM-4",   # Incidents tracked and reported
            "TPM-1",   # Vendor contracts
        ],
        "policies": [
            "POL-38",  # Corrective Action Procedures
            "POL-78",  # Non-Conformity Handling Procedure
            "POL-84",  # Product Quarantine Policy
        ],
    },

    "Article 20(4) - Risk Notification": {
        "risks": [
            "Fines and judgements",
            "Improper response to incidents",
        ],
        "controls": [
            "IRM-3",   # Contact info for authorities
            "IRM-4",   # Incidents tracked and reported
            "IRM-5",   # Incident reporting
            "CCI-3",   # Communication plans
        ],
        "policies": [
            "POL-20",  # Incident Management Policy
            "POL-37",  # Contact Procedure With Local Authorities
            "POL-30",  # Risk Management Policy
            "POL-85",  # Market Surveillance Notification Procedure
            "POL-86",  # Risk Assessment Policy
        ],
    },

    "Article 20(5) - Record Keeping": {
        "risks": [
            "Fines and judgements",
            "Inability to investigate / prosecute incidents",
        ],
        "controls": [
            "DCH-4",   # Data disposed per retention policy
            "ALM-4",   # Adequate log storage per retention
            "CCI-4",   # ISMS documentation
        ],
        "policies": [
            "POL-17",  # Data Retention Policy
            "POL-48",  # Procedure For Control Of Documented Information
            "POL-87",  # Record Keeping Policy
            "POL-88",  # Product Traceability Procedure
        ],
    },
}
