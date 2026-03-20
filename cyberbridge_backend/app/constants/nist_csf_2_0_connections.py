# Maps each NIST CSF 2.0 objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code in control_templates (BASELINE_CONTROLS)
# - policies: matched by POL code in policy_templates

NIST_CSF_2_0_CONNECTIONS = {
    # =========================================================================
    # GV: GOVERN
    # =========================================================================

    # GV.OC: Organizational Context
    'GV.OC-01:  The organizational mission is understood and informs cybersecurity risk management': {
        'risks': ['Inability to support business processes'],
        'controls': ['GOV-2', 'GOV-5', 'RSM-2'],
        'policies': ['POL-21', 'POL-30'],
    },
    'GV.OC-02:  Internal and external stakeholders are understood, and their needs and expectations regarding cybersecurity risk management are understood and considered': {
        'risks': ['Inadequate internal practices'],
        'controls': ['GOV-2', 'GOV-5', 'RSM-2'],
        'policies': ['POL-21', 'POL-30'],
    },
    'GV.OC-03:  Legal, regulatory, and contractual requirements regarding cybersecurity - including privacy and civil liberties obligations - are understood and managed': {
        'risks': ['Fines and judgements', 'Third-party compliance / legal exposure'],
        'controls': ['GOV-5', 'GOV-11', 'RSM-2'],
        'policies': ['POL-21', 'POL-30', 'POL-36'],
    },
    'GV.OC-04:  Critical objectives, capabilities, and services that stakeholders depend on or expect from the organization are understood and communicated': {
        'risks': ['Business interruption'],
        'controls': ['GOV-2', 'GOV-5', 'BCD-1'],
        'policies': ['POL-21', 'POL-10'],
    },
    'GV.OC-05:  Outcomes, capabilities, and services that the organization depends on are understood and communicated': {
        'risks': ['Reliance on the third-party', 'Business interruption'],
        'controls': ['GOV-2', 'GOV-5', 'TPM-1'],
        'policies': ['POL-21', 'POL-34'],
    },

    # GV.RM: Risk Management Strategy
    'GV.RM-01:  Risk management objectives are established and agreed to by organizational stakeholders': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-5', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    'GV.RM-02:  Risk appetite and risk tolerance statements are established, communicated, and maintained': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-5', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    'GV.RM-03:  Cybersecurity risk management activities and outcomes are included in enterprise risk management processes': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-5', 'RSM-2', 'RSM-4'],
        'policies': ['POL-30', 'POL-21'],
    },
    'GV.RM-04:  Strategic direction that describes appropriate risk response options is established and communicated': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['RSM-2', 'RSM-3', 'GOV-5'],
        'policies': ['POL-30'],
    },
    'GV.RM-05:  Lines of communication across the organization are established for cybersecurity risks, including risks from suppliers and other third parties': {
        'risks': ['Exposure to third party vendors', 'Inadequate third-party practices'],
        'controls': ['GOV-5', 'RSM-2', 'TPM-1'],
        'policies': ['POL-30', 'POL-34'],
    },
    'GV.RM-06:  A standardized method for calculating, documenting, categorizing, and prioritizing cybersecurity risks is established and communicated': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['RSM-2', 'RSM-3', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'GV.RM-07:  Strategic opportunities (i.e., positive risks) are characterized and are included in organizational cybersecurity risk discussions': {
        'risks': [],
        'controls': ['RSM-2', 'GOV-5'],
        'policies': ['POL-30'],
    },

    # GV.RR: Roles, Responsibilities, and Authorities
    'GV.RR-01:  Organizational leadership is responsible and accountable for cybersecurity risk and fosters a culture that is risk-aware, ethical, and continually improving': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-4', 'GOV-9', 'GOV-10'],
        'policies': ['POL-21', 'POL-13'],
    },
    'GV.RR-02:  Roles, responsibilities, and authorities related to cybersecurity risk management are established, communicated, understood, and enforced': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-4', 'HRM-5', 'HRM-11'],
        'policies': ['POL-21', 'POL-27'],
    },
    'GV.RR-03:  Adequate resources are allocated commensurate with the cybersecurity risk strategy, roles, responsibilities, and policies': {
        'risks': ['Inability to support business processes'],
        'controls': ['GOV-4', 'GOV-5', 'RSM-4'],
        'policies': ['POL-21', 'POL-30'],
    },
    'GV.RR-04:  Cybersecurity is included in human resources practices': {
        'risks': ['Lack of a security-minded workforce'],
        'controls': ['HRM-1', 'HRM-2', 'HRM-4'],
        'policies': ['POL-27', 'POL-39'],
    },

    # GV.PO: Policy
    'GV.PO-01:  Policy for managing cybersecurity risks is established based on organizational context, cybersecurity strategy, and priorities and is communicated and enforced': {
        'risks': ['Outdated policies for Process Management', 'Inadequate internal practices'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-21', 'POL-40'],
    },
    'GV.PO-02:  Policy for managing cybersecurity risks is reviewed, updated, communicated, and enforced to reflect changes in requirements, threats, technology, and organizational mission': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5', 'GOV-12'],
        'policies': ['POL-21', 'POL-40', 'POL-37'],
    },

    # GV.OV: Oversight
    'GV.OV-01:  Cybersecurity risk management strategy outcomes are reviewed to inform and adjust strategy and direction': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-3', 'GOV-10', 'RSM-2'],
        'policies': ['POL-30', 'POL-37'],
    },
    'GV.OV-02:  The cybersecurity risk management strategy is reviewed and adjusted to ensure coverage of organizational requirements and risks': {
        'risks': ['Incorrect controls scoping', 'Lack of oversight of internal controls'],
        'controls': ['GOV-3', 'GOV-10', 'RSM-2'],
        'policies': ['POL-30', 'POL-37'],
    },
    'GV.OV-03:  Organizational cybersecurity risk management performance is evaluated and reviewed for adjustments needed': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['GOV-3', 'GOV-10', 'GOV-12'],
        'policies': ['POL-36', 'POL-37'],
    },

    # GV.SC: Supply Chain Risk Management
    'GV.SC-01:  A cybersecurity supply chain risk management program, strategy, objectives, policies, and processes are established and agreed to by organizational stakeholders': {
        'risks': ['Third-party supply chain relationships, visibility and controls', 'Exposure to third party vendors'],
        'controls': ['TPM-1', 'TPM-2', 'GOV-5'],
        'policies': ['POL-34', 'POL-21'],
    },
    'GV.SC-02:  Cybersecurity roles and responsibilities for suppliers, customers, and partners are established, communicated, and coordinated internally and externally': {
        'risks': ['Inadequate third-party practices'],
        'controls': ['TPM-1', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'GV.SC-03:  Cybersecurity supply chain risk management is integrated into cybersecurity and enterprise risk management, risk assessment, and improvement processes': {
        'risks': ['Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-1', 'TPM-2', 'RSM-2'],
        'policies': ['POL-34', 'POL-30'],
    },
    'GV.SC-04:  Suppliers are known and prioritized by criticality': {
        'risks': ['Reliance on the third-party'],
        'controls': ['TPM-1', 'TPM-2'],
        'policies': ['POL-34'],
    },
    'GV.SC-05:  Requirements to address cybersecurity risks in supply chains are established, prioritized, and integrated into contracts and other types of agreements with suppliers and other relevant third parties': {
        'risks': ['Exposure to third party vendors', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-3', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'GV.SC-06:  Planning and due diligence are performed to reduce risks before entering into formal supplier or other third-party relationships': {
        'risks': ['Lack of oversight of third-party controls', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-1', 'TPM-2', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'GV.SC-07:  The risks posed by a supplier, their products and services, and other third parties are understood, recorded, prioritized, assessed, responded to, and monitored over the course of the relationship': {
        'risks': ['Third-party cybersecurity exposure', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-1', 'TPM-2', 'TPM-3'],
        'policies': ['POL-34', 'POL-30'],
    },
    'GV.SC-08:  Relevant suppliers and other third parties are included in incident planning, response, and recovery activities': {
        'risks': ['Inadequate third-party practices'],
        'controls': ['TPM-1', 'IRM-1', 'BCD-1'],
        'policies': ['POL-34', 'POL-20'],
    },
    'GV.SC-09:  Supply chain security practices are integrated into cybersecurity and enterprise risk management programs, and their performance is monitored throughout the technology product and service life cycle': {
        'risks': ['Software supply chain malware attack', 'Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-1', 'TPM-2', 'RSM-2'],
        'policies': ['POL-34', 'POL-30'],
    },
    'GV.SC-10:  Cybersecurity supply chain risk management plans include provisions for activities that occur after the conclusion of a partnership or service agreement': {
        'risks': ['Reliance on the third-party'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },

    # =========================================================================
    # ID: IDENTIFY
    # =========================================================================

    # ID.AM: Asset Management
    'ID.AM-01:  Inventories of hardware managed by the organization are maintained': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Misconfiguration of employee endpoints'],
        'controls': ['AST-1', 'AST-2', 'AST-3'],
        'policies': ['POL-7'],
    },
    'ID.AM-02:  Inventories of software, services, and systems managed by the organization are maintained': {
        'risks': ['Shadow IT', 'Lost, damaged or stolen asset(s)'],
        'controls': ['AST-1', 'AST-2', 'AST-3'],
        'policies': ['POL-7'],
    },
    "ID.AM-03:  Representations of the organization's authorized network communication and internal and external network data flows are maintained": {
        'risks': ['Man in the middle (MitM) attack for Network'],
        'controls': ['NES-1', 'NES-2', 'NES-3'],
        'policies': ['POL-24'],
    },
    'ID.AM-04:  Inventories of services provided by suppliers are maintained': {
        'risks': ['Exposure to third party vendors', 'Reliance on the third-party'],
        'controls': ['AST-1', 'TPM-1', 'TPM-2'],
        'policies': ['POL-7', 'POL-34'],
    },
    'ID.AM-05:  Assets are prioritized based on classification, criticality, resources, and impact on the mission': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['AST-1', 'AST-2', 'AST-4'],
        'policies': ['POL-7', 'POL-16'],
    },
    'ID.AM-07:  Inventories of data and corresponding metadata for designated data types are maintained': {
        'risks': ['Data loss / corruption', 'Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['DCH-1', 'DCH-2', 'AST-1'],
        'policies': ['POL-16', 'POL-17'],
    },
    'ID.AM-08:  Systems, hardware, software, services, and data are managed throughout their life cycles': {
        'risks': ['Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices', 'Shadow IT'],
        'controls': ['AST-1', 'AST-2', 'AST-4'],
        'policies': ['POL-7', 'POL-17'],
    },

    # ID.RA: Risk Assessment
    'ID.RA-01:  Vulnerabilities in assets are identified, validated, and recorded': {
        'risks': ['Unpatched vulnerability exploitation', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2', 'CVM-3'],
        'policies': ['POL-35'],
    },
    'ID.RA-02:  Cyber threat intelligence is received from information sharing forums and sources': {
        'risks': ['Advanced persistent threats (APT)', 'Zero-Day Exploit'],
        'controls': ['GOV-6', 'RSM-2'],
        'policies': ['POL-30', 'POL-35'],
    },
    'ID.RA-03:  Internal and external threats to the organization are identified and recorded': {
        'risks': ['Insider Threat', 'Advanced persistent threats (APT)'],
        'controls': ['RSM-2', 'RSM-3', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'ID.RA-04:  Potential impacts and likelihoods of threats exploiting vulnerabilities are identified and recorded': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    'ID.RA-05:  Threats, vulnerabilities, likelihoods, and impacts are used to understand inherent risk and inform risk response prioritization': {
        'risks': ['Incorrect controls scoping', 'Lack of oversight of internal controls'],
        'controls': ['RSM-2', 'RSM-3', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'ID.RA-06:  Risk responses are chosen, prioritized, planned, tracked, and communicated': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['RSM-2', 'RSM-3', 'RSM-4'],
        'policies': ['POL-30'],
    },
    'ID.RA-07:  Changes and exceptions are managed, assessed for risk impact, recorded, and tracked': {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'RSM-2'],
        'policies': ['POL-11', 'POL-30'],
    },
    'ID.RA-08:  Processes for receiving, analyzing, and responding to vulnerability disclosures are established': {
        'risks': ['Unpatched vulnerability exploitation', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2', 'CVM-5'],
        'policies': ['POL-35'],
    },
    'ID.RA-09:  The authenticity and integrity of hardware and software are assessed prior to acquisition and use': {
        'risks': ['Software supply chain malware attack'],
        'controls': ['CVM-4', 'AST-1', 'CM-3'],
        'policies': ['POL-7', 'POL-35'],
    },
    'ID.RA-10:  Critical suppliers are assessed prior to acquisition': {
        'risks': ['Exposure to third party vendors', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-1', 'TPM-2', 'TPM-4'],
        'policies': ['POL-34'],
    },

    # ID.IM: Improvement
    'ID.IM-01:  Improvements are identified from evaluations': {
        'risks': ['Ineffective remediation actions', 'Inadequate internal practices'],
        'controls': ['GOV-12', 'GOV-3'],
        'policies': ['POL-38', 'POL-36'],
    },
    'ID.IM-02:  Improvements are identified from security tests and exercises, including those done in coordination with suppliers and relevant third parties': {
        'risks': ['Lack of design reviews & security testing'],
        'controls': ['GOV-12', 'CVM-5', 'CVM-6'],
        'policies': ['POL-38', 'POL-35'],
    },
    'ID.IM-03:  Improvements are identified from execution of operational processes, procedures, and activities': {
        'risks': ['Inadequate internal practices', 'Ineffective remediation actions'],
        'controls': ['GOV-12', 'GOV-3'],
        'policies': ['POL-38'],
    },
    'ID.IM-04:  Incident response plans and other cybersecurity plans that affect operations are established, communicated, maintained, and improved': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-2', 'IRM-5'],
        'policies': ['POL-20', 'POL-38'],
    },

    # =========================================================================
    # PR: PROTECT
    # =========================================================================

    # PR.AA: Identity Management, Authentication, and Access Control
    'PR.AA-01:  Identities and credentials for authorized users, services, and hardware are managed by the organization': {
        'risks': ['Unauthorized Access', 'Broken or weak authentication'],
        'controls': ['IAM-1', 'IAM-2', 'IAM-3'],
        'policies': ['POL-4', 'POL-1'],
    },
    'PR.AA-02:  Identities are proofed and bound to credentials based on the context of interactions': {
        'risks': ['Credential Stuffing', 'Brute force attack'],
        'controls': ['IAM-1', 'IAM-2', 'IAM-7'],
        'policies': ['POL-4', 'POL-1'],
    },
    'PR.AA-03:  Users, services, and hardware are authenticated': {
        'risks': ['Broken or weak authentication', 'Credential Stuffing'],
        'controls': ['IAM-1', 'IAM-2', 'IAM-3'],
        'policies': ['POL-1', 'POL-4'],
    },
    'PR.AA-04:  Identity assertions are protected, conveyed, and verified': {
        'risks': ['Session Hijacking', 'Application access token mis-use'],
        'controls': ['IAM-1', 'IAM-7', 'CRY-1'],
        'policies': ['POL-4', 'POL-19'],
    },
    'PR.AA-05:  Access permissions, entitlements, and authorizations are defined in a policy, managed, enforced, and reviewed, and incorporate the principles of least privilege and separation of duties': {
        'risks': ['Improper assignment of privileged functions', 'Privilege escalation', 'Unauthorized access'],
        'controls': ['IAM-4', 'IAM-5', 'IAM-6'],
        'policies': ['POL-4'],
    },
    'PR.AA-06:  Physical access to assets is managed, monitored, and enforced commensurate with risk': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)', 'Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-2', 'PES-3'],
        'policies': ['POL-28'],
    },

    # PR.AT: Awareness and Training
    'PR.AT-01:  Personnel are provided with awareness and training so that they possess the knowledge and skills to perform general tasks with cybersecurity risks in mind': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'HRM-12'],
        'policies': ['POL-39', 'POL-27'],
    },
    'PR.AT-02:  Individuals in specialized roles are provided with awareness and training so that they possess the knowledge and skills to perform relevant tasks with cybersecurity risks in mind': {
        'risks': ['Lack of cybersecurity awareness', 'Cybersecurity skills gap in managing the cloud infrastructure'],
        'controls': ['HRM-8', 'HRM-11', 'HRM-12'],
        'policies': ['POL-39', 'POL-27'],
    },

    # PR.DS: Data Security
    'PR.DS-01:  The confidentiality, integrity, and availability of data-at-rest are protected': {
        'risks': ['Data loss / corruption', 'Data breach', 'Weak cryptography & encryption support in the application'],
        'controls': ['DCH-1', 'DCH-2', 'CRY-1'],
        'policies': ['POL-14', 'POL-19', 'POL-16'],
    },
    'PR.DS-02:  The confidentiality, integrity, and availability of data-in-transit are protected': {
        'risks': ['Man in the middle (MitM) attack for Network', 'Data breach'],
        'controls': ['CRY-1', 'CRY-2', 'NES-5'],
        'policies': ['POL-19', 'POL-14'],
    },
    'PR.DS-10:  The confidentiality, integrity, and availability of data-in-use are protected': {
        'risks': ['Data loss / corruption', 'Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['DCH-1', 'DCH-3', 'IAM-5'],
        'policies': ['POL-14', 'POL-16'],
    },
    'PR.DS-11:  Backups of data are created, protected, maintained, and tested': {
        'risks': ['Data loss', 'Availability & Disaster recovery'],
        'controls': ['BCD-2', 'DRC-1', 'DRC-2'],
        'policies': ['POL-9', 'POL-18'],
    },

    # PR.PS: Platform Security
    'PR.PS-01:  Configuration management practices are established and applied': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Cloud misconfiguration'],
        'controls': ['CMM-1', 'CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    'PR.PS-02:  Software is maintained, replaced, and removed commensurate with risk': {
        'risks': ['Unpatched vulnerability exploitation', 'Shadow IT'],
        'controls': ['CVM-1', 'CVM-2', 'CVM-6'],
        'policies': ['POL-26', 'POL-35'],
    },
    'PR.PS-03:  Hardware is maintained, replaced, and removed commensurate with risk': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices'],
        'controls': ['AST-1', 'AST-2', 'AST-4'],
        'policies': ['POL-7'],
    },
    'PR.PS-04:  Log records are generated and made available for continuous monitoring': {
        'risks': ['Insufficient logging', 'Insufficient usage and other logging'],
        'controls': ['ALM-1', 'ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    'PR.PS-05:  Installation and execution of unauthorized software are prevented': {
        'risks': ['Shadow IT', 'Malware'],
        'controls': ['CMM-1', 'AST-4', 'CM-3'],
        'policies': ['POL-15', 'POL-5'],
    },
    'PR.PS-06:  Secure software development practices are integrated, and their performance is monitored throughout the software development life cycle': {
        'risks': ['Lack of design reviews & security testing', 'Source code disclosure'],
        'controls': ['APD-1', 'APD-2', 'APD-6'],
        'policies': ['POL-33', 'POL-41', 'POL-6'],
    },

    # PR.IR: Technology Infrastructure Resilience
    'PR.IR-01:  Networks and environments are protected from unauthorized logical access and usage': {
        'risks': ['DNS Spoofing', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-1', 'NES-2', 'NES-6'],
        'policies': ['POL-24'],
    },
    "PR.IR-02:  The organization's technology assets are protected from environmental threats": {
        'risks': ['Natural Disasters for Physical facilities(Bldg., Equip...)', 'Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-4', 'PES-5'],
        'policies': ['POL-28'],
    },
    'PR.IR-03:  Mechanisms are implemented to achieve resilience requirements in normal and adverse situations': {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['BCD-1', 'BCD-2', 'BCD-3'],
        'policies': ['POL-10', 'POL-8'],
    },
    'PR.IR-04:  Adequate resource capacity to ensure availability is maintained': {
        'risks': ['Denial of Service (DoS) Attack', 'Business interruption'],
        'controls': ['BCD-1', 'BCD-4', 'NES-7'],
        'policies': ['POL-8'],
    },

    # =========================================================================
    # DE: DETECT
    # =========================================================================

    # DE.CM: Continuous Monitoring
    'DE.CM-01:  Networks and network services are monitored to find potentially adverse events': {
        'risks': ['Insufficient monitoring & alerting', 'Inability to maintain situational awareness'],
        'controls': ['ALM-1', 'ALM-2', 'NES-4'],
        'policies': ['POL-22', 'POL-24'],
    },
    'DE.CM-02:  The physical environment is monitored to find potentially adverse events': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-2', 'ALM-1'],
        'policies': ['POL-28', 'POL-22'],
    },
    'DE.CM-03:  Personnel activity and technology usage are monitored to find potentially adverse events': {
        'risks': ['Insider Threat', 'Inability to maintain situational awareness'],
        'controls': ['ALM-1', 'ALM-2', 'ALM-3'],
        'policies': ['POL-22'],
    },
    'DE.CM-06:  External service provider activities and services are monitored to find potentially adverse events': {
        'risks': ['Lack of oversight of third-party controls', 'Third-party cybersecurity exposure'],
        'controls': ['ALM-1', 'TPM-2', 'ALM-5'],
        'policies': ['POL-22', 'POL-34'],
    },
    'DE.CM-09:  Computing hardware and software, runtime environments, and their data are monitored to find potentially adverse events': {
        'risks': ['Malware', 'Unpatched vulnerability exploitation'],
        'controls': ['ALM-1', 'ALM-2', 'CVM-1'],
        'policies': ['POL-22', 'POL-5'],
    },

    # DE.AE: Adverse Event Analysis
    'DE.AE-02:  Potentially adverse events are analyzed to better understand associated activities': {
        'risks': ['Inability to maintain situational awareness', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-3', 'IRM-4', 'ALM-2'],
        'policies': ['POL-22', 'POL-20'],
    },
    'DE.AE-03:  Information is correlated from multiple sources': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-3', 'ALM-5', 'IRM-4'],
        'policies': ['POL-22'],
    },
    'DE.AE-04:  The estimated impact and scope of adverse events are understood': {
        'risks': ['Improper response to incidents'],
        'controls': ['ALM-3', 'IRM-1', 'IRM-4'],
        'policies': ['POL-20', 'POL-22'],
    },
    'DE.AE-06:  Information on adverse events is provided to authorized staff and tools': {
        'risks': ['Inability to maintain situational awareness'],
        'controls': ['ALM-3', 'ALM-4', 'IRM-3'],
        'policies': ['POL-22', 'POL-20'],
    },
    'DE.AE-07:  Cyber threat intelligence and other contextual information are integrated into the analysis': {
        'risks': ['Advanced persistent threats (APT)', 'Zero-Day Exploit'],
        'controls': ['ALM-3', 'GOV-6', 'IRM-4'],
        'policies': ['POL-22', 'POL-30'],
    },
    'DE.AE-08:  Incidents are declared when adverse events meet the defined incident criteria': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-2', 'ALM-4'],
        'policies': ['POL-20'],
    },

    # =========================================================================
    # RS: RESPOND
    # =========================================================================

    # RS.MA: Incident Management
    'RS.MA-01:  The incident response plan is executed in coordination with relevant third parties once an incident is declared': {
        'risks': ['Improper response to incidents', 'Inadequate third-party practices'],
        'controls': ['IRM-1', 'IRM-2', 'IRM-3'],
        'policies': ['POL-20'],
    },
    'RS.MA-02:  Incident reports are triaged and validated': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'RS.MA-03:  Incidents are categorized and prioritized': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'RS.MA-04:  Incidents are escalated or elevated as needed': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-3', 'IRM-5'],
        'policies': ['POL-20'],
    },
    'RS.MA-05:  The criteria for initiating incident recovery are applied': {
        'risks': ['Business interruption'],
        'controls': ['IRM-1', 'BCD-1', 'DRC-1'],
        'policies': ['POL-20', 'POL-18'],
    },

    # RS.AN: Incident Analysis
    'RS.AN-03:  Analysis is performed to establish what has taken place during an incident and the root cause of the incident': {
        'risks': ['Inability to investigate / prosecute incidents', 'Insufficient logging'],
        'controls': ['IRM-4', 'ALM-3', 'IRM-6'],
        'policies': ['POL-20', 'POL-22'],
    },
    "RS.AN-06:  Actions performed during an investigation are recorded, and the records' integrity and provenance are preserved": {
        'risks': ['Inability to investigate / prosecute incidents'],
        'controls': ['IRM-4', 'ALM-1', 'IRM-6'],
        'policies': ['POL-20', 'POL-22'],
    },
    'RS.AN-07:  Incident data and metadata are collected, and their integrity and provenance are preserved': {
        'risks': ['Inability to investigate / prosecute incidents', 'Insufficient usage and other logging'],
        'controls': ['IRM-4', 'ALM-1', 'ALM-5'],
        'policies': ['POL-22', 'POL-20'],
    },
    "RS.AN-08:  An incident's magnitude is estimated and validated": {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },

    # RS.CO: Incident Response Reporting and Communication
    'RS.CO-02:  Internal and external stakeholders are notified of incidents': {
        'risks': ['Improper response to incidents', 'Fines and judgements'],
        'controls': ['IRM-3', 'CCI-3'],
        'policies': ['POL-20', 'POL-46'],
    },
    'RS.CO-03:  Information is shared with designated internal and external stakeholders': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-3', 'CCI-3', 'CCI-4'],
        'policies': ['POL-20'],
    },

    # RS.MI: Incident Mitigation
    'RS.MI-01:  Incidents are contained': {
        'risks': ['Improper response to incidents', 'Business interruption'],
        'controls': ['IRM-1', 'IRM-5'],
        'policies': ['POL-20'],
    },
    'RS.MI-02:  Incidents are eradicated': {
        'risks': ['Improper response to incidents', 'Ineffective remediation actions'],
        'controls': ['IRM-1', 'IRM-5', 'CVM-1'],
        'policies': ['POL-20'],
    },

    # =========================================================================
    # RC: RECOVER
    # =========================================================================

    # RC.RP: Incident Recovery Plan Execution
    'RC.RP-01:  The recovery portion of the incident response plan is executed once initiated from the incident response process': {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['DRC-1', 'DRC-2', 'BCD-1'],
        'policies': ['POL-18', 'POL-10'],
    },
    'RC.RP-02:  Recovery actions are selected, scoped, prioritized, and performed': {
        'risks': ['Business interruption', 'Ineffective remediation actions'],
        'controls': ['DRC-1', 'DRC-2', 'DRC-3'],
        'policies': ['POL-18', 'POL-10'],
    },
    'RC.RP-03:  The integrity of backups and other restoration assets is verified before using them for restoration': {
        'risks': ['Data loss', 'Data loss / corruption'],
        'controls': ['DRC-1', 'DRC-2', 'BCD-2'],
        'policies': ['POL-9', 'POL-18'],
    },
    'RC.RP-04:  Critical mission functions and cybersecurity risk management are considered to establish post-incident operational norms': {
        'risks': ['Business interruption'],
        'controls': ['BCD-1', 'DRC-3', 'RSM-2'],
        'policies': ['POL-10', 'POL-30'],
    },
    'RC.RP-05:  The integrity of restored assets is verified, systems and services are restored, and normal operating status is confirmed': {
        'risks': ['Business interruption', 'Data loss / corruption'],
        'controls': ['DRC-1', 'DRC-4', 'DRC-5'],
        'policies': ['POL-18'],
    },
    'RC.RP-06:  The end of incident recovery is declared based on criteria, and incident-related documentation is completed': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['DRC-1', 'IRM-1', 'IRM-6'],
        'policies': ['POL-18', 'POL-20'],
    },

    # RC.CO: Incident Recovery Communication
    'RC.CO-03:  Recovery activities and progress in restoring operational capabilities are communicated to designated internal and external stakeholders': {
        'risks': ['Diminished reputation', 'Business interruption'],
        'controls': ['CCI-3', 'IRM-3', 'BCD-1'],
        'policies': ['POL-10', 'POL-20'],
    },
    'RC.CO-04:  Public updates on incident recovery are shared using approved methods and messaging': {
        'risks': ['Diminished reputation'],
        'controls': ['CCI-3', 'CCI-4'],
        'policies': ['POL-10', 'POL-20'],
    },
}
