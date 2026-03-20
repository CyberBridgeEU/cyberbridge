# Maps each CMMC 2.0 objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code in control_templates (Baseline Controls)
# - policies: matched by POL code in policy_templates

CMMC_2_0_CONNECTIONS = {
    # ──────────────────────────────────────────────────────────────────────
    # AC: ACCESS CONTROL  (22 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'AC.L1-3.1.1: Authorized Access Control': {
        'risks': ['Unauthorized access', 'Unauthorized Access', 'Improper assignment of privileged functions'],
        'controls': ['IAM-1', 'IAM-7', 'IAM-8'],
        'policies': ['POL-4', 'POL-21'],
    },
    'AC.L1-3.1.2: Transaction & Function Control': {
        'risks': ['Unauthorized access', 'Privilege escalation'],
        'controls': ['IAM-1', 'IAM-7'],
        'policies': ['POL-4'],
    },
    'AC.L1-3.1.20: External Connections': {
        'risks': ['Unauthorized access', 'Exposure to third party vendors'],
        'controls': ['NES-4', 'NES-5', 'NES-7'],
        'policies': ['POL-24', 'POL-29'],
    },
    'AC.L1-3.1.22: Control Public Information': {
        'risks': ['Accidental disclosure of sensitive customer data during support or other operations', 'Data breach'],
        'controls': ['DCH-1', 'DCH-2'],
        'policies': ['POL-16', 'POL-14'],
    },
    'AC.L2-3.1.3: Control CUI Flow': {
        'risks': ['Data loss / corruption', 'Data breach'],
        'controls': ['DCH-1', 'DCH-2', 'DCH-3'],
        'policies': ['POL-16', 'POL-14'],
    },
    'AC.L2-3.1.4: Separation of Duties': {
        'risks': ['Improper assignment of privileged functions', 'Insider Threat'],
        'controls': ['IAM-4', 'IAM-7'],
        'policies': ['POL-4'],
    },
    'AC.L2-3.1.5: Least Privilege': {
        'risks': ['Privilege escalation', 'Improper assignment of privileged functions'],
        'controls': ['IAM-1', 'IAM-4', 'IAM-7'],
        'policies': ['POL-4'],
    },
    'AC.L2-3.1.6: Non-Privileged Account Use': {
        'risks': ['Privilege escalation', 'Improper assignment of privileged functions'],
        'controls': ['IAM-4', 'IAM-7'],
        'policies': ['POL-4'],
    },
    'AC.L2-3.1.7: Privileged Functions': {
        'risks': ['Privilege escalation', 'Unauthorized Access'],
        'controls': ['IAM-4', 'IAM-7'],
        'policies': ['POL-4'],
    },
    'AC.L2-3.1.8: Unsuccessful Logon Attempts': {
        'risks': ['Brute force attack', 'Credential Stuffing'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1', 'POL-4'],
    },
    'AC.L2-3.1.9: Privacy & Security Notices': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['IAM-5', 'GOV-1'],
        'policies': ['POL-2', 'POL-21'],
    },
    'AC.L2-3.1.10: Session Lock': {
        'risks': ['Unauthorized access', 'Unauthorized Access'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1', 'POL-4'],
    },
    'AC.L2-3.1.11: Session Termination': {
        'risks': ['Session Hijacking', 'Unauthorized access'],
        'controls': ['IAM-5'],
        'policies': ['POL-4'],
    },
    'AC.L2-3.1.12: Control Remote Access': {
        'risks': ['Unauthorized access', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-7', 'IAM-6'],
        'policies': ['POL-29'],
    },
    'AC.L2-3.1.13: Remote Access Confidentiality': {
        'risks': ['Man in the middle (MitM) attack for Network', 'Data breach'],
        'controls': ['NES-7', 'CRY-1'],
        'policies': ['POL-29', 'POL-19'],
    },
    'AC.L2-3.1.14: Remote Access Routing': {
        'risks': ['Unauthorized access', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-7', 'NES-3'],
        'policies': ['POL-29', 'POL-24'],
    },
    'AC.L2-3.1.15: Privileged Remote Access': {
        'risks': ['Privilege escalation', 'Unauthorized Access'],
        'controls': ['IAM-4', 'IAM-6', 'NES-7'],
        'policies': ['POL-29', 'POL-4'],
    },
    'AC.L2-3.1.16: Wireless Access Authorization': {
        'risks': ['Unauthorized access', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-3', 'IAM-5'],
        'policies': ['POL-24'],
    },
    'AC.L2-3.1.17: Wireless Access Protection': {
        'risks': ['Man in the middle (MitM) attack for Network', 'DNS Spoofing'],
        'controls': ['NES-3', 'CRY-1'],
        'policies': ['POL-24', 'POL-19'],
    },
    'AC.L2-3.1.18: Mobile Device Connection': {
        'risks': ['Employee laptop / mobile / desktop/ other device theft or loss for laptops', 'Misconfiguration of employee endpoints'],
        'controls': ['MDM-1', 'IAM-5'],
        'policies': ['POL-23'],
    },
    'AC.L2-3.1.19: Encrypt CUI on Mobile': {
        'risks': ['Data theft from Laptops and other employee owned devices', 'Data breach'],
        'controls': ['CRY-2', 'MDM-1'],
        'policies': ['POL-19', 'POL-23'],
    },
    'AC.L2-3.1.21: Portable Storage Use': {
        'risks': ['Data theft from Laptops and other employee owned devices', 'Data loss / corruption'],
        'controls': ['DCH-4', 'AST-3'],
        'policies': ['POL-7', 'POL-16'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # AT: AWARENESS AND TRAINING  (3 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'AT.L2-3.2.1: Role-Based Risk Awareness': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'GOV-1'],
        'policies': ['POL-39', 'POL-27'],
    },
    'AT.L2-3.2.2: Role-Based Training': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'HRM-11'],
        'policies': ['POL-39', 'POL-27'],
    },
    'AT.L2-3.2.3: Insider Threat Awareness': {
        'risks': ['Insider Threat', 'Lack of cybersecurity awareness'],
        'controls': ['HRM-8', 'HRM-1'],
        'policies': ['POL-39', 'POL-27'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # AU: AUDIT AND ACCOUNTABILITY  (9 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'AU.L2-3.3.1: System Auditing': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-2', 'ALM-5', 'GOV-12'],
        'policies': ['POL-22', 'POL-36'],
    },
    'AU.L2-3.3.2: User Accountability': {
        'risks': ['Insufficient logging', 'Inability to maintain individual accountability'],
        'controls': ['ALM-2', 'IAM-2'],
        'policies': ['POL-22'],
    },
    'AU.L2-3.3.3: Event Review': {
        'risks': ['Insufficient monitoring & alerting', 'Inability to maintain situational awareness'],
        'controls': ['ALM-3', 'ALM-5'],
        'policies': ['POL-22'],
    },
    'AU.L2-3.3.4: Audit Failure Alerting': {
        'risks': ['Insufficient monitoring & alerting', 'Insufficient logging'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22'],
    },
    'AU.L2-3.3.5: Audit Correlation': {
        'risks': ['Insufficient logging', 'Inability to maintain situational awareness'],
        'controls': ['ALM-3', 'ALM-5'],
        'policies': ['POL-22'],
    },
    'AU.L2-3.3.6: Reduction & Reporting': {
        'risks': ['Insufficient logging', 'Insufficient usage and other logging'],
        'controls': ['ALM-2', 'ALM-3'],
        'policies': ['POL-22'],
    },
    'AU.L2-3.3.7: Authoritative Time Source': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'CMM-2'],
        'policies': ['POL-22', 'POL-15'],
    },
    'AU.L2-3.3.8: Audit Protection': {
        'risks': ['Insufficient logging', 'Unauthorized changes'],
        'controls': ['ALM-4', 'IAM-7'],
        'policies': ['POL-22'],
    },
    'AU.L2-3.3.9: Audit Management': {
        'risks': ['Insufficient logging', 'Improper assignment of privileged functions'],
        'controls': ['ALM-4', 'IAM-4'],
        'policies': ['POL-22', 'POL-4'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # CM: CONFIGURATION MANAGEMENT  (9 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'CM.L2-3.4.1: System Baselining': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Cloud misconfiguration'],
        'controls': ['CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    'CM.L2-3.4.2: Security Configuration Enforcement': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Cloud misconfiguration'],
        'controls': ['CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    'CM.L2-3.4.3: System Change Management': {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'CHM-3'],
        'policies': ['POL-11'],
    },
    'CM.L2-3.4.4: Security Impact Analysis': {
        'risks': ['Unauthorized changes', 'Security misconfiguration of APIs / Applications'],
        'controls': ['CHM-1', 'CHM-4'],
        'policies': ['POL-11', 'POL-15'],
    },
    'CM.L2-3.4.5: Access Restrictions for Change': {
        'risks': ['Unauthorized changes', 'Privilege escalation'],
        'controls': ['CHM-2', 'IAM-4'],
        'policies': ['POL-11', 'POL-4'],
    },
    'CM.L2-3.4.6: Least Functionality': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Unpatched vulnerability exploitation'],
        'controls': ['CMM-1', 'CMM-2'],
        'policies': ['POL-15'],
    },
    'CM.L2-3.4.7: Nonessential Functionality': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Shadow IT'],
        'controls': ['CMM-1', 'CMM-2'],
        'policies': ['POL-15'],
    },
    'CM.L2-3.4.8: Application Execution Policy': {
        'risks': ['Malware', 'Security misconfiguration of APIs / Applications'],
        'controls': ['CMM-1', 'CVM-5'],
        'policies': ['POL-15', 'POL-5'],
    },
    'CM.L2-3.4.9: User-Installed Software': {
        'risks': ['Shadow IT', 'Malware'],
        'controls': ['CMM-1', 'CVM-5'],
        'policies': ['POL-15', 'POL-2'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # IA: IDENTIFICATION AND AUTHENTICATION  (11 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'IA.L1-3.5.1: Identification': {
        'risks': ['Unauthorized access', 'Broken or weak authentication'],
        'controls': ['IAM-1', 'IAM-5'],
        'policies': ['POL-1', 'POL-4'],
    },
    'IA.L1-3.5.2: Authentication': {
        'risks': ['Broken or weak authentication', 'Credential Stuffing'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1', 'POL-4'],
    },
    'IA.L2-3.5.3: Multifactor Authentication': {
        'risks': ['Broken or weak authentication', 'Brute force attack'],
        'controls': ['IAM-6', 'IAM-5'],
        'policies': ['POL-1', 'POL-4'],
    },
    'IA.L2-3.5.4: Replay-Resistant Authentication': {
        'risks': ['Session Hijacking', 'Broken or weak authentication'],
        'controls': ['IAM-6', 'CRY-1'],
        'policies': ['POL-1', 'POL-19'],
    },
    'IA.L2-3.5.5: Identifier Reuse': {
        'risks': ['Unauthorized access', 'Improper assignment of privileged functions'],
        'controls': ['IAM-3', 'IAM-5'],
        'policies': ['POL-4'],
    },
    'IA.L2-3.5.6: Identifier Handling': {
        'risks': ['Unauthorized access', 'Ex-Employees / disgruntled employees'],
        'controls': ['IAM-3', 'HRM-7'],
        'policies': ['POL-4'],
    },
    'IA.L2-3.5.7: Password Complexity': {
        'risks': ['Brute force attack', 'Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1'],
    },
    'IA.L2-3.5.8: Password Reuse': {
        'risks': ['Credential Stuffing', 'Brute force attack'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1'],
    },
    'IA.L2-3.5.9: Temporary Passwords': {
        'risks': ['Broken or weak authentication', 'Unauthorized Access'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1'],
    },
    'IA.L2-3.5.10: Cryptographically-Protected Passwords': {
        'risks': ['Broken or weak authentication', 'Credential dumping attack for Operating Systems'],
        'controls': ['CRY-1', 'CRY-2', 'IAM-9'],
        'policies': ['POL-1', 'POL-19'],
    },
    'IA.L2-3.5.11: Obscure Feedback': {
        'risks': ['Broken or weak authentication', 'Source code disclosure'],
        'controls': ['IAM-5', 'APD-1'],
        'policies': ['POL-1'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # IR: INCIDENT RESPONSE  (3 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'IR.L2-3.6.1: Incident Handling': {
        'risks': ['Improper response to incidents', 'Inability to investigate / prosecute incidents'],
        'controls': ['IRM-1', 'IRM-4', 'IRM-6'],
        'policies': ['POL-20'],
    },
    'IR.L2-3.6.2: Incident Reporting': {
        'risks': ['Improper response to incidents', 'Inability to investigate / prosecute incidents'],
        'controls': ['IRM-2', 'IRM-3', 'IRM-5'],
        'policies': ['POL-20'],
    },
    'IR.L2-3.6.3: Incident Response Testing': {
        'risks': ['Improper response to incidents', 'Ineffective remediation actions'],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # MA: MAINTENANCE  (6 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'MA.L2-3.7.1: Perform Maintenance': {
        'risks': ['Unpatched vulnerability exploitation', 'Security misconfiguration of APIs / Applications'],
        'controls': ['CVM-3', 'CVM-7'],
        'policies': ['POL-26'],
    },
    'MA.L2-3.7.2: System Maintenance Control': {
        'risks': ['Unpatched vulnerability exploitation', 'Unauthorized changes'],
        'controls': ['CVM-3', 'CHM-1'],
        'policies': ['POL-26', 'POL-7'],
    },
    'MA.L2-3.7.3: Equipment Sanitization': {
        'risks': ['Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices', 'Data loss / corruption'],
        'controls': ['AST-2', 'DCH-4'],
        'policies': ['POL-7', 'POL-17'],
    },
    'MA.L2-3.7.4: Media Inspection': {
        'risks': ['Malware', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-5', 'CVM-4'],
        'policies': ['POL-5', 'POL-26'],
    },
    'MA.L2-3.7.5: Nonlocal Maintenance': {
        'risks': ['Unauthorized access', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-7', 'IAM-6'],
        'policies': ['POL-29', 'POL-26'],
    },
    'MA.L2-3.7.6: Maintenance Personnel': {
        'risks': ['Insider Threat', 'Unauthorized Access'],
        'controls': ['HRM-2', 'IAM-4'],
        'policies': ['POL-27', 'POL-26'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # MP: MEDIA PROTECTION  (10 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'MP.L1-3.8.3: Media Disposal': {
        'risks': ['Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices', 'Data loss / corruption'],
        'controls': ['AST-2', 'DCH-4'],
        'policies': ['POL-17', 'POL-7'],
    },
    'MP.L2-3.8.1: Media Protection': {
        'risks': ['Data loss / corruption', 'Data breach'],
        'controls': ['DCH-2', 'DCH-5', 'AST-3'],
        'policies': ['POL-16', 'POL-14'],
    },
    'MP.L2-3.8.2: Media Access': {
        'risks': ['Unauthorized access', 'Data breach'],
        'controls': ['IAM-7', 'DCH-3'],
        'policies': ['POL-4', 'POL-16'],
    },
    'MP.L2-3.8.4: Media Markings': {
        'risks': ['Data loss / corruption', 'Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['DCH-2', 'DCH-5'],
        'policies': ['POL-16'],
    },
    'MP.L2-3.8.5: Media Accountability': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Data loss / corruption'],
        'controls': ['AST-1', 'AST-3'],
        'policies': ['POL-7'],
    },
    'MP.L2-3.8.6: Portable Storage Encryption': {
        'risks': ['Data theft from Laptops and other employee owned devices', 'Data breach'],
        'controls': ['CRY-2', 'CRY-4'],
        'policies': ['POL-19'],
    },
    'MP.L2-3.8.7: Removable Media': {
        'risks': ['Malware', 'Data breach'],
        'controls': ['CVM-5', 'DCH-5'],
        'policies': ['POL-16', 'POL-5'],
    },
    'MP.L2-3.8.8: Shared Media': {
        'risks': ['Data breach', 'Unauthorized access'],
        'controls': ['DCH-3', 'DCH-5'],
        'policies': ['POL-16', 'POL-14'],
    },
    'MP.L2-3.8.9: Protect Backups': {
        'risks': ['Data loss', 'Data loss / corruption'],
        'controls': ['DRC-1', 'DRC-2', 'DRC-5'],
        'policies': ['POL-9', 'POL-19'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # PS: PERSONNEL SECURITY  (2 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'PS.L2-3.9.1: Screen Individuals': {
        'risks': ['Insider Threat', 'Ex-Employees / disgruntled employees'],
        'controls': ['HRM-2', 'HRM-4'],
        'policies': ['POL-27'],
    },
    'PS.L2-3.9.2: Personnel Actions': {
        'risks': ['Insider Threat', 'Ex-Employees / disgruntled employees'],
        'controls': ['HRM-7', 'IAM-3'],
        'policies': ['POL-27'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # PE: PHYSICAL PROTECTION  (6 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'PE.L1-3.10.1: Limit Physical Access': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)', 'Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    'PE.L1-3.10.3: Escort Visitors': {
        'risks': ['Insider Threat', 'Unauthorized Access'],
        'controls': ['PES-3', 'PES-4'],
        'policies': ['POL-28'],
    },
    'PE.L1-3.10.4: Physical Access Logs': {
        'risks': ['Unauthorized Access', 'Insufficient logging'],
        'controls': ['PES-3', 'PES-1'],
        'policies': ['POL-28', 'POL-22'],
    },
    'PE.L1-3.10.5: Manage Physical Access': {
        'risks': ['Unauthorized Access', 'Power Outages for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    'PE.L2-3.10.2: Monitor Facility': {
        'risks': ['Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)', 'Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-2', 'PES-4'],
        'policies': ['POL-28'],
    },
    'PE.L2-3.10.6: Alternative Work Sites': {
        'risks': ['Unauthorized access', 'Business interruption'],
        'controls': ['NES-7', 'BCD-1'],
        'policies': ['POL-29', 'POL-28'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # RA: RISK ASSESSMENT  (3 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'RA.L2-3.11.1: Risk Assessments': {
        'risks': ['Incorrect controls scoping', 'Lack of oversight of internal controls'],
        'controls': ['GOV-6', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    'RA.L2-3.11.2: Vulnerability Scan': {
        'risks': ['Unpatched vulnerability exploitation', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2'],
        'policies': ['POL-35', 'POL-30'],
    },
    'RA.L2-3.11.3: Vulnerability Remediation': {
        'risks': ['Unpatched vulnerability exploitation', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-3', 'CVM-7'],
        'policies': ['POL-35', 'POL-26'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # CA: SECURITY ASSESSMENT  (4 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'CA.L2-3.12.1: Security Control Assessment': {
        'risks': ['Incorrect controls scoping', 'Lack of oversight of internal controls'],
        'controls': ['GOV-3', 'GOV-9', 'GOV-12'],
        'policies': ['POL-36', 'POL-30'],
    },
    'CA.L2-3.12.2: Plan of Action': {
        'risks': ['Ineffective remediation actions', 'Incorrect controls scoping'],
        'controls': ['GOV-3', 'RSM-3'],
        'policies': ['POL-30'],
    },
    'CA.L2-3.12.3: Security Control Monitoring': {
        'risks': ['Insufficient monitoring & alerting', 'Lack of oversight of internal controls'],
        'controls': ['GOV-3', 'GOV-12', 'ALM-3'],
        'policies': ['POL-36', 'POL-30'],
    },
    'CA.L2-3.12.4: System Security Plan': {
        'risks': ['Outdated policies for Process Management', 'Inadequate internal practices'],
        'controls': ['GOV-5', 'GOV-9'],
        'policies': ['POL-21', 'POL-30'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # SC: SYSTEM AND COMMUNICATIONS PROTECTION  (16 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'SC.L1-3.13.1: Boundary Protection': {
        'risks': ['Denial of Service (DoS) Attack', 'DNS Spoofing'],
        'controls': ['NES-1', 'NES-2', 'NES-4'],
        'policies': ['POL-24'],
    },
    'SC.L1-3.13.5: Public-Access System Separation': {
        'risks': ['Unauthorized access', 'Data breach'],
        'controls': ['NES-3', 'NES-5'],
        'policies': ['POL-24'],
    },
    'SC.L2-3.13.2: Security Engineering': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Lack of design reviews & security testing'],
        'controls': ['APD-1', 'APD-2', 'APD-6'],
        'policies': ['POL-33', 'POL-6'],
    },
    'SC.L2-3.13.3: Role Separation': {
        'risks': ['Privilege escalation', 'Improper assignment of privileged functions'],
        'controls': ['IAM-7', 'NES-3'],
        'policies': ['POL-4', 'POL-24'],
    },
    'SC.L2-3.13.4: Shared Resource Control': {
        'risks': ['Data breach', 'System compromise'],
        'controls': ['NES-3', 'IAM-7'],
        'policies': ['POL-24'],
    },
    'SC.L2-3.13.6: Network Communication by Exception': {
        'risks': ['Denial of Service (DoS) Attack', 'Unauthorized access'],
        'controls': ['NES-4', 'NES-5'],
        'policies': ['POL-24'],
    },
    'SC.L2-3.13.7: Split Tunneling': {
        'risks': ['Man in the middle (MitM) attack for Network', 'Unauthorized access'],
        'controls': ['NES-7', 'NES-3'],
        'policies': ['POL-24', 'POL-29'],
    },
    'SC.L2-3.13.8: Data in Transit': {
        'risks': ['Man in the middle (MitM) attack for Network', 'Data breach'],
        'controls': ['CRY-1', 'CRY-3'],
        'policies': ['POL-19'],
    },
    'SC.L2-3.13.9: Connections Termination': {
        'risks': ['Session Hijacking', 'Unauthorized access'],
        'controls': ['NES-6', 'IAM-5'],
        'policies': ['POL-24'],
    },
    'SC.L2-3.13.10: Key Management': {
        'risks': ['Weak cryptography & encryption support in the application', 'Data breach'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    'SC.L2-3.13.11: CUI Encryption': {
        'risks': ['Weak cryptography & encryption support in the application', 'Data breach'],
        'controls': ['CRY-1', 'CRY-2'],
        'policies': ['POL-19', 'POL-14'],
    },
    'SC.L2-3.13.12: Collaborative Device Control': {
        'risks': ['Unauthorized access', 'Data breach'],
        'controls': ['NES-6', 'IAM-7'],
        'policies': ['POL-24'],
    },
    'SC.L2-3.13.13: Mobile Code': {
        'risks': ['Malware', 'Security misconfiguration of APIs / Applications'],
        'controls': ['APD-1', 'CVM-5'],
        'policies': ['POL-6', 'POL-5'],
    },
    'SC.L2-3.13.14: Voice over Internet Protocol': {
        'risks': ['Man in the middle (MitM) attack for Network', 'Denial of Service (DoS) Attack'],
        'controls': ['NES-6', 'NES-3'],
        'policies': ['POL-24'],
    },
    'SC.L2-3.13.15: Communications Authenticity': {
        'risks': ['DNS Spoofing', 'Man in the middle (MitM) attack for Network'],
        'controls': ['CRY-1', 'NES-1'],
        'policies': ['POL-19', 'POL-24'],
    },
    'SC.L2-3.13.16: Data at Rest': {
        'risks': ['Data breach', 'Weak cryptography & encryption support in the application'],
        'controls': ['CRY-2', 'CRY-4'],
        'policies': ['POL-19'],
    },

    # ──────────────────────────────────────────────────────────────────────
    # SI: SYSTEM AND INFORMATION INTEGRITY  (7 objectives)
    # ──────────────────────────────────────────────────────────────────────
    'SI.L1-3.14.1: Flaw Remediation': {
        'risks': ['Unpatched vulnerability exploitation', 'Zero-Day Exploit'],
        'controls': ['CVM-3', 'CVM-7'],
        'policies': ['POL-26', 'POL-35'],
    },
    'SI.L1-3.14.2: Malicious Code Protection': {
        'risks': ['Malware', 'Ransomware'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    'SI.L1-3.14.4: Update Malicious Code Protection': {
        'risks': ['Malware', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-5', 'CVM-6', 'CVM-7'],
        'policies': ['POL-5', 'POL-26'],
    },
    'SI.L1-3.14.5: System & File Scanning': {
        'risks': ['Malware', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-1', 'CVM-4', 'CVM-5'],
        'policies': ['POL-5', 'POL-35'],
    },
    'SI.L2-3.14.3: Security Alerts & Advisories': {
        'risks': ['Unpatched vulnerability exploitation', 'Zero-Day Exploit'],
        'controls': ['ALM-1', 'CVM-3'],
        'policies': ['POL-35', 'POL-26'],
    },
    'SI.L2-3.14.6: Monitor Communications for Attacks': {
        'risks': ['Insufficient monitoring & alerting', 'Advanced persistent threats (APT)'],
        'controls': ['ALM-1', 'ALM-3', 'NES-2'],
        'policies': ['POL-22', 'POL-5'],
    },
    'SI.L2-3.14.7: Identify Unauthorized Use': {
        'risks': ['Insufficient monitoring & alerting', 'Unauthorized access'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22', 'POL-35'],
    },
}
