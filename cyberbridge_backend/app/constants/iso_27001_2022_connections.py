# ISO 27001:2022 Objective -> Risks, Controls, Policies mapping
# Maps each ISO 27001 2022 objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code in control_templates (BASELINE_CONTROLS)
# - policies: matched by POL code in policy_templates

ISO_27001_2022_CONNECTIONS = {
    # =========================================================================
    # ISO 27001: Clauses  (30 objectives – management-system requirements)
    # =========================================================================

    # --- 4.x Context of the organisation ---
    '4.1: Understanding the organization and its context': {
        'risks': ['Inability to support business processes', 'Incorrect controls scoping'],
        'controls': ['GOV-5', 'GOV-11'],
        'policies': ['POL-21', 'POL-30'],
    },
    '4.2: Understanding the needs and expectations of interested parties': {
        'risks': ['Fines and judgements', 'Inability to support business processes'],
        'controls': ['GOV-5', 'GOV-8'],
        'policies': ['POL-21', 'POL-30'],
    },
    '4.3: Determining the scope of the information security management system': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-5', 'GOV-11'],
        'policies': ['POL-21'],
    },
    '4.4: Information security management system': {
        'risks': ['Inadequate internal practices', 'Lack of oversight of internal controls'],
        'controls': ['GOV-1', 'GOV-5', 'GOV-9'],
        'policies': ['POL-21'],
    },

    # --- 5.x Leadership ---
    '5.1: Leadership and commitment': {
        'risks': ['Lack of roles & responsibilities', 'Lack of oversight of internal controls'],
        'controls': ['GOV-4', 'GOV-10', 'HRM-11'],
        'policies': ['POL-21'],
    },
    '5.2: Policy': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-2', 'GOV-5'],
        'policies': ['POL-21'],
    },
    '5.3: Organizational roles, responsibilities and authorities': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-4', 'HRM-5', 'HRM-11'],
        'policies': ['POL-21', 'POL-27'],
    },

    # --- 6.x Planning ---
    '6.1.1: Actions to address risks & opportunities': {
        'risks': ['Incorrect controls scoping', 'Lack of oversight of internal controls'],
        'controls': ['GOV-6', 'RSM-2'],
        'policies': ['POL-30'],
    },
    '6.1.2: Information security risk assessment': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-6', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    '6.1.3: Information security risk treatment': {
        'risks': ['Incorrect controls scoping', 'Unmitigated vulnerabilities'],
        'controls': ['GOV-6', 'RSM-3'],
        'policies': ['POL-30'],
    },
    '6.2: Information security objectives & plans': {
        'risks': ['Inability to support business processes'],
        'controls': ['GOV-5', 'GOV-10'],
        'policies': ['POL-21', 'POL-30'],
    },
    '6.3: Planning of changes': {
        'risks': ['Unauthorized changes'],
        'controls': ['CHM-1', 'CHM-3'],
        'policies': ['POL-11'],
    },

    # --- 7.x Support ---
    '7.1: Resources': {
        'risks': ['Inability to support business processes'],
        'controls': ['GOV-4', 'GOV-10'],
        'policies': ['POL-21'],
    },
    '7.2: Competence': {
        'risks': ['Lack of cybersecurity awareness', 'Cybersecurity skills gap in managing the cloud infrastructure'],
        'controls': ['HRM-8', 'HRM-12'],
        'policies': ['POL-27'],
    },
    '7.3: Awareness': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8'],
        'policies': ['POL-27'],
    },
    '7.4: Communication': {
        'risks': ['Inability to support business processes'],
        'controls': ['CCI-3', 'GOV-1'],
        'policies': ['POL-21'],
    },
    '7.5.1: General': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['CCI-4', 'GOV-1'],
        'policies': ['POL-21'],
    },
    '7.5.2: Creating and Updating': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['CCI-4', 'GOV-1'],
        'policies': ['POL-21'],
    },
    '7.5.3: Control of documented information': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['CCI-4', 'GOV-1'],
        'policies': ['POL-21'],
    },

    # --- 8.x Operation ---
    '8.1: Operational planning and control': {
        'risks': ['Inadequate internal practices', 'Unauthorized changes'],
        'controls': ['GOV-3', 'GOV-9'],
        'policies': ['POL-21', 'POL-30'],
    },
    '8.2: Information security risk assessment': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-6', 'RSM-2'],
        'policies': ['POL-30'],
    },
    '8.3: Information security risk treatment': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['GOV-6', 'RSM-3'],
        'policies': ['POL-30'],
    },

    # --- 9.x Performance evaluation ---
    '9.1: Monitoring, measurement, analysis and evaluation': {
        'risks': ['Inadequate internal practices', 'Insufficient monitoring & alerting'],
        'controls': ['GOV-3', 'ALM-5'],
        'policies': ['POL-22', 'POL-36'],
    },
    '9.2.1: General': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    '9.2.2: Internal audit programme': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    '9.3.1: General': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-10', 'GOV-12'],
        'policies': ['POL-21'],
    },
    '9.3.2: Management review inputs': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-10', 'GOV-12'],
        'policies': ['POL-21'],
    },
    '9.3.3: Management review results': {
        'risks': ['Lack of oversight of internal controls', 'Ineffective remediation actions'],
        'controls': ['GOV-3', 'GOV-10'],
        'policies': ['POL-21'],
    },

    # --- 10.x Improvement ---
    '10.1: Continual improvement': {
        'risks': ['Inadequate internal practices', 'Ineffective remediation actions'],
        'controls': ['GOV-3', 'GOV-12'],
        'policies': ['POL-21'],
    },
    '10.2: Nonconformity and corrective action': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['GOV-3', 'IRM-2'],
        'policies': ['POL-21'],
    },

    # =========================================================================
    # ISO 27002 (2022): Controls  (93 objectives – security controls)
    # =========================================================================

    # --- 5.x Organizational controls ---
    '5.1: Policies for information security': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-2', 'GOV-5'],
        'policies': ['POL-21'],
    },
    '5.2: Information security roles and responsibilities': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-4', 'HRM-5', 'HRM-11'],
        'policies': ['POL-21', 'POL-27'],
    },
    '5.3: Segregation of duties': {
        'risks': ['Improper assignment of privileged functions', 'Privilege escalation'],
        'controls': ['IAM-1', 'IAM-4'],
        'policies': ['POL-4'],
    },
    '5.4: Management responsibilities': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-4', 'GOV-10', 'HRM-11'],
        'policies': ['POL-21'],
    },
    '5.5: Contact with authorities': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-3'],
        'policies': ['POL-20'],
    },
    '5.6: Contact with special interest groups': {
        'risks': ['Inability to maintain situational awareness'],
        'controls': ['GOV-4'],
        'policies': ['POL-21'],
    },
    '5.7: Threat intelligence': {
        'risks': ['Inability to maintain situational awareness', 'Advanced persistent threats (APT)'],
        'controls': ['CVM-1', 'ALM-3'],
        'policies': ['POL-35'],
    },
    '5.8: Information security in project management': {
        'risks': ['Inadequate internal practices'],
        'controls': ['GOV-5', 'APD-2'],
        'policies': ['POL-21', 'POL-33'],
    },
    '5.9: Inventory of information and other associated assets': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Inability to maintain individual accountability'],
        'controls': ['AST-1', 'AST-3'],
        'policies': ['POL-7'],
    },
    '5.10: Acceptable use of information and other associated assets': {
        'risks': ['Misappropriation & Misuse of devices'],
        'controls': ['AST-4', 'HRM-1'],
        'policies': ['POL-2', 'POL-7'],
    },
    '5.11: Return of assets': {
        'risks': ['Ex-Employees / disgruntled employees'],
        'controls': ['HRM-7', 'AST-2'],
        'policies': ['POL-7', 'POL-27'],
    },
    '5.12: Classification of information': {
        'risks': ['Data loss / corruption', 'Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['DCH-2', 'DCH-5'],
        'policies': ['POL-16'],
    },
    '5.13: Labelling of information': {
        'risks': ['Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['DCH-2', 'DCH-5'],
        'policies': ['POL-16'],
    },
    '5.14: Information transfer': {
        'risks': ['Data breach', 'Man in the middle (MitM) attack for Network'],
        'controls': ['CRY-1', 'NES-7'],
        'policies': ['POL-14', 'POL-19'],
    },
    '5.15: Access control': {
        'risks': ['Unauthorized access', 'Unauthorized Access', 'Improper assignment of privileged functions'],
        'controls': ['IAM-1', 'IAM-7', 'IAM-8'],
        'policies': ['POL-4'],
    },
    '5.16: Identity management': {
        'risks': ['Unauthorized access', 'Credential Stuffing'],
        'controls': ['IAM-1', 'IAM-3'],
        'policies': ['POL-4'],
    },
    '5.17: Authentication information': {
        'risks': ['Broken or weak authentication', 'Brute force attack'],
        'controls': ['IAM-5', 'IAM-6', 'IAM-9'],
        'policies': ['POL-1'],
    },
    '5.18: Access rights': {
        'risks': ['Unauthorized Access', 'Privilege escalation'],
        'controls': ['IAM-1', 'IAM-3', 'IAM-4'],
        'policies': ['POL-4'],
    },
    '5.19: Information security in supplier relationships': {
        'risks': ['Exposure to third party vendors', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-1', 'TPM-3', 'TPM-4'],
        'policies': ['POL-34'],
    },
    '5.20: Addressing information security within supplier agreements': {
        'risks': ['Exposure to third party vendors', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-2'],
        'policies': ['POL-34'],
    },
    '5.21: Managing information security in the ICT supply chain': {
        'risks': ['Third-party supply chain relationships, visibility and controls', 'Software supply chain malware attack'],
        'controls': ['TPM-1', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '5.22: Monitoring, review and change management of supplier services': {
        'risks': ['Lack of oversight of third-party controls', 'Reliance on the third-party'],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '5.23: Information security for use of cloud services': {
        'risks': ['Cloud misconfiguration', 'Availability & Disaster recovery'],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '5.24: Information security incident management planning and preparation': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '5.25: Assessment and decision on information security events': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-1', 'ALM-1'],
        'policies': ['POL-20'],
    },
    '5.26: Response to information security incidents': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },
    '5.27: Learning from information security incidents': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    '5.28: Collection of evidence': {
        'risks': ['Inability to investigate / prosecute incidents'],
        'controls': ['ALM-2', 'IRM-4'],
        'policies': ['POL-20', 'POL-22'],
    },
    '5.29: Information security during disruption': {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10'],
    },
    '5.30: ICT readiness for business continuity': {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['BCD-1', 'BCD-2', 'DRC-1'],
        'policies': ['POL-10', 'POL-18'],
    },
    '5.31: Legal, statutory, regulatory and contractual requirements': {
        'risks': ['Fines and judgements', 'Third-party compliance / legal exposure'],
        'controls': ['GOV-8'],
        'policies': ['POL-21'],
    },
    '5.32: Intellectual property rights': {
        'risks': ['Fines and judgements'],
        'controls': ['CMM-1'],
        'policies': ['POL-21'],
    },
    '5.33: Protection of records': {
        'risks': ['Data loss / corruption', 'Data loss'],
        'controls': ['DCH-4', 'DRC-1'],
        'policies': ['POL-17'],
    },
    '5.34: Privacy and protection of PII': {
        'risks': ['Data breach', 'Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['PRIV-1', 'PRIV-2', 'PRIV-6'],
        'policies': ['POL-14'],
    },
    '5.35: Independent review of information security': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    '5.36: Compliance with policies, rules and standards for information security': {
        'risks': ['Inadequate internal practices', 'Fines and judgements'],
        'controls': ['GOV-3', 'GOV-9'],
        'policies': ['POL-21', 'POL-36'],
    },
    '5.37: Documented operating procedures': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'CCI-4'],
        'policies': ['POL-21'],
    },

    # --- 6.x People controls ---
    '6.1: Screening': {
        'risks': ['Insider Threat'],
        'controls': ['HRM-2', 'HRM-4'],
        'policies': ['POL-27'],
    },
    '6.2: Terms and conditions of employment': {
        'risks': ['Insider Threat', 'Lack of a security-minded workforce'],
        'controls': ['HRM-1', 'HRM-4'],
        'policies': ['POL-27'],
    },
    '6.3: Information security awareness, education and training': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8'],
        'policies': ['POL-27'],
    },
    '6.4: Disciplinary process': {
        'risks': ['Insider Threat', 'Illegal content or abusive action'],
        'controls': ['HRM-9', 'HRM-10'],
        'policies': ['POL-27', 'POL-31'],
    },
    '6.5: Responsibilities after termination or change of employment': {
        'risks': ['Ex-Employees / disgruntled employees'],
        'controls': ['HRM-7', 'IAM-3'],
        'policies': ['POL-27'],
    },
    '6.6: Confidentiality or non-disclosure agreements': {
        'risks': ['Insider Threat', 'Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['HRM-1'],
        'policies': ['POL-14', 'POL-27'],
    },
    '6.7: Remote working': {
        'risks': ['Data theft from Laptops and other employee owned devices', 'Employee owned devices (BYOD) exploitation'],
        'controls': ['NES-7', 'MDM-1'],
        'policies': ['POL-29'],
    },
    '6.8: Information security event reporting': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-4', 'IRM-5'],
        'policies': ['POL-20'],
    },

    # --- 7.x Physical controls ---
    '7.1: Physical security perimeters': {
        'risks': ['Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)', 'Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    '7.2: Physical entry': {
        'risks': ['Unauthorized access'],
        'controls': ['PES-1', 'PES-3'],
        'policies': ['POL-28'],
    },
    '7.3: Securing offices, rooms and facilities': {
        'risks': ['Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    '7.4: Physical security monitoring': {
        'risks': ['Unauthorized access', 'Power Outages for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-2'],
        'policies': ['POL-28'],
    },
    '7.5: Protecting against physical and environmental threats': {
        'risks': ['Natural Disasters for Physical facilities(Bldg., Equip...)', 'Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-2', 'PES-4'],
        'policies': ['POL-28'],
    },
    '7.6: Working in secure areas': {
        'risks': ['Insider Threat'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    '7.7: Clear desk and clear screen': {
        'risks': ['Data theft from Laptops and other employee owned devices', 'Insider Threat'],
        'controls': ['PES-5'],
        'policies': ['POL-12', 'POL-28'],
    },
    '7.8: Equipment siting and protection': {
        'risks': ['Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-2', 'PES-4'],
        'policies': ['POL-28'],
    },
    '7.9: Security of assets off-premises': {
        'risks': ['Employee laptop / mobile / desktop/ other device theft or loss for laptops', 'Lost, damaged or stolen asset(s)'],
        'controls': ['MDM-1', 'CRY-2'],
        'policies': ['POL-23', 'POL-28'],
    },
    '7.10: Storage media': {
        'risks': ['Data loss / corruption', 'Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices'],
        'controls': ['DCH-4', 'AST-2'],
        'policies': ['POL-17'],
    },
    '7.11: Supporting utilities': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)', 'Business interruption'],
        'controls': ['PES-2', 'BCD-2'],
        'policies': ['POL-28'],
    },
    '7.12: Cabling security': {
        'risks': ['Man in the middle (MitM) attack for Network'],
        'controls': ['PES-4'],
        'policies': ['POL-28'],
    },
    '7.13: Equipment maintenance': {
        'risks': ['Business interruption'],
        'controls': ['PES-2'],
        'policies': ['POL-28'],
    },
    '7.14: Secure disposal or re-use of equipment': {
        'risks': ['Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices'],
        'controls': ['AST-2', 'DCH-4'],
        'policies': ['POL-7', 'POL-17'],
    },

    # --- 8.x Technological controls ---
    '8.1: User endpoint devices': {
        'risks': ['Misconfiguration of employee endpoints', 'Employee owned devices (BYOD) exploitation', 'Shadow IT'],
        'controls': ['MDM-1', 'CVM-5'],
        'policies': ['POL-23'],
    },
    '8.2: Privileged access rights': {
        'risks': ['Privilege escalation', 'Improper assignment of privileged functions'],
        'controls': ['IAM-4', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '8.3: Information access restriction': {
        'risks': ['Unauthorized Access', 'Broken or weak access control in the application'],
        'controls': ['IAM-1', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '8.4: Access to source code': {
        'risks': ['Source code disclosure', 'Unauthorized Access'],
        'controls': ['IAM-1', 'APD-1'],
        'policies': ['POL-4', 'POL-33'],
    },
    '8.5: Secure authentication': {
        'risks': ['Broken or weak authentication', 'Brute force attack', 'Credential Stuffing'],
        'controls': ['IAM-5', 'IAM-6', 'IAM-9'],
        'policies': ['POL-1'],
    },
    '8.6: Capacity management': {
        'risks': ['Business interruption', 'Denial of Service (DoS) Attack'],
        'controls': ['CAP-1', 'CAP-2'],
        'policies': ['POL-8'],
    },
    '8.7: Protection against malware': {
        'risks': ['Malware', 'Ransomware'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '8.8: Management of technical vulnerabilities': {
        'risks': ['Unpatched vulnerability exploitation', 'Zero-Day Exploit', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-3', 'CVM-7'],
        'policies': ['POL-26', 'POL-35'],
    },
    '8.9: Configuration management': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Cloud misconfiguration'],
        'controls': ['CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    '8.10: Information deletion': {
        'risks': ['Data loss / corruption'],
        'controls': ['DCH-4'],
        'policies': ['POL-17'],
    },
    '8.11: Data masking': {
        'risks': ['Data breach', 'Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['DCH-2', 'CRY-2'],
        'policies': ['POL-16', 'POL-19'],
    },
    '8.12: Data leakage prevention': {
        'risks': ['Data breach', 'Data loss / corruption'],
        'controls': ['DCH-1', 'DCH-3'],
        'policies': ['POL-14', 'POL-16'],
    },
    '8.13: Information backup': {
        'risks': ['Data loss', 'Accidental loss of data from data storage on cloud'],
        'controls': ['DRC-1', 'DRC-2', 'DRC-4'],
        'policies': ['POL-9'],
    },
    '8.14: Redundancy of information processing facilities': {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['BCD-2', 'BCD-4'],
        'policies': ['POL-8', 'POL-18'],
    },
    '8.15: Logging': {
        'risks': ['Insufficient logging', 'Insufficient usage and other logging'],
        'controls': ['ALM-2', 'ALM-4', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '8.16: Monitoring activities': {
        'risks': ['Insufficient monitoring & alerting', 'Inability to maintain situational awareness'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22'],
    },
    '8.17: Clock synchronization': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2'],
        'policies': ['POL-22'],
    },
    '8.18: Use of privileged utility programs': {
        'risks': ['Privilege escalation', 'Unauthorized changes'],
        'controls': ['IAM-4'],
        'policies': ['POL-4'],
    },
    '8.19: Installation of software on operational systems': {
        'risks': ['Shadow IT', 'Malware'],
        'controls': ['CMM-1', 'CVM-5'],
        'policies': ['POL-15'],
    },
    '8.20: Networks security': {
        'risks': ['DNS Spoofing', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-1', 'NES-2', 'NES-6'],
        'policies': ['POL-24'],
    },
    '8.21: Security of network services': {
        'risks': ['Denial of Service (DoS) Attack', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-4', 'NES-5'],
        'policies': ['POL-24'],
    },
    '8.22: Segregation of networks': {
        'risks': ['Data breach', 'Unauthorized access'],
        'controls': ['NES-3'],
        'policies': ['POL-24'],
    },
    '8.23: Web filtering': {
        'risks': ['Malware', 'Phishing'],
        'controls': ['NES-1', 'NES-4'],
        'policies': ['POL-24'],
    },
    '8.24: Use of cryptography': {
        'risks': ['Weak cryptography & encryption support in the application', 'Data breach'],
        'controls': ['CRY-1', 'CRY-2', 'CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '8.25: Secure development life cycle': {
        'risks': ['Lack of design reviews & security testing', 'Security misconfiguration of APIs / Applications'],
        'controls': ['APD-1', 'APD-2', 'APD-6'],
        'policies': ['POL-33'],
    },
    '8.26: Application security requirements': {
        'risks': ['Broken or weak authentication in the application', 'Broken or weak access control in the application', 'Cross-Site Scripting XSS'],
        'controls': ['APD-1', 'APD-3'],
        'policies': ['POL-6', 'POL-33'],
    },
    '8.27: Secure system architecture and engineering principles': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['APD-1', 'APD-5'],
        'policies': ['POL-33'],
    },
    '8.28: Secure coding': {
        'risks': ['SQL Injection Attack', 'Input Validation Attack', 'Buffer Overflow Attack'],
        'controls': ['APD-1', 'APD-4'],
        'policies': ['POL-33'],
    },
    '8.29: Security testing in development and acceptance': {
        'risks': ['Lack of design reviews & security testing', 'Unmitigated vulnerabilities'],
        'controls': ['APD-2', 'APD-4', 'CVM-2'],
        'policies': ['POL-33', 'POL-35'],
    },
    '8.30: Outsourced development': {
        'risks': ['Inadequate third-party practices', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-1', 'APD-6'],
        'policies': ['POL-33', 'POL-34'],
    },
    '8.31: Separation of development, test and production environments': {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['APD-5', 'CHM-4'],
        'policies': ['POL-33'],
    },
    '8.32: Change management': {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'CHM-3'],
        'policies': ['POL-11'],
    },
    '8.33: Test information': {
        'risks': ['Accidental disclosure of sensitive customer data during support or other operations', 'Data breach'],
        'controls': ['DCH-2', 'APD-5'],
        'policies': ['POL-16', 'POL-33'],
    },
    '8.34: Protection of information systems during audit testing': {
        'risks': ['Unauthorized access', 'Data breach'],
        'controls': ['GOV-12', 'IAM-4'],
        'policies': ['POL-36'],
    },
}
