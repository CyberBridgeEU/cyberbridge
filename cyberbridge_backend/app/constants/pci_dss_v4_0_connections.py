# Auto-generated mapping of PCI DSS v4.0 objectives to risks, controls, and policies.
# Maps each objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code in control_templates (Baseline Controls)
# - policies: matched by POL code in policy_templates

PCI_DSS_V4_0_CONNECTIONS = {
    '1.1.1: All security policies and operational procedures that are identified in Requirement 1 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-24', 'POL-21'],
    },
    '1.1.2: Roles and responsibilities for performing activities in Requirement 1 are documented, assigned, and understood.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-24'],
    },
    '1.2.1: Configuration standards for NSC rulesets are Defined, Implemented and Maintained.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['NES-1', 'NES-3', 'CM-3'],
        'policies': ['POL-24', 'POL-15'],
    },
    '1.2.2: All changes to network connections and to configurations of NSCs are approved and managed in accordance with the change control process defined at Requirement 6.5.1.': {
        'risks': ['Unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'NES-1'],
        'policies': ['POL-24', 'POL-11'],
    },
    '1.2.3: An accurate network diagram(s) is maintained.': {
        'risks': ['DNS Spoofing'],
        'controls': ['NES-3', 'NES-6'],
        'policies': ['POL-24'],
    },
    '1.2.4: An accurate data-flow diagram(s) is maintained.': {
        'risks': ['Data loss / corruption'],
        'controls': ['DCH-1', 'NES-3'],
        'policies': ['POL-24'],
    },
    '1.2.5: All services, protocols and ports allowed  are identified, approved, and have a defined business need.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['NES-5', 'NES-3'],
        'policies': ['POL-24'],
    },
    '1.2.6: Security features are defined and implemented for all services, protocols, and ports that are in use and considered to be insecure, such that the risk is mitigated.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['NES-5', 'NES-1'],
        'policies': ['POL-24'],
    },
    '1.2.7: Configurations of NSCs are reviewed at least once every six months to confirm they are relevant and effective.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['NES-1', 'GOV-3'],
        'policies': ['POL-24'],
    },
    '1.2.8: Configuration files for NSCs are secured from unauthorized access and kept consistent with active network configurations.': {
        'risks': ['Unauthorized access'],
        'controls': ['NES-1', 'CM-3'],
        'policies': ['POL-24', 'POL-15'],
    },
    '1.3.1: Inbound traffic to the CDE is restricted.': {
        'risks': ['Denial Of Service (DoS)'],
        'controls': ['NES-1', 'NES-4'],
        'policies': ['POL-24'],
    },
    '1.3.2: Outbound traffic from the CDE is restricted.': {
        'risks': ['Data breach'],
        'controls': ['NES-1', 'NES-5'],
        'policies': ['POL-24'],
    },
    '1.3.3: NSCs are installed between all wireless networks and the CDE, regardless of whether the wireless network is a CDE.': {
        'risks': ['Man in the middle (MitM) attack for Network'],
        'controls': ['NES-3', 'NES-1'],
        'policies': ['POL-24'],
    },
    '1.4.1: NSCs are implemented between trusted and untrusted networks.': {
        'risks': ['Denial of Service (DoS) Attack'],
        'controls': ['NES-1', 'NES-3'],
        'policies': ['POL-24'],
    },
    '1.4.2: Inbound traffic from untrusted networks to trusted networks is restricted.': {
        'risks': ['Unauthorized Access'],
        'controls': ['NES-1', 'NES-4'],
        'policies': ['POL-24'],
    },
    '1.4.3: Anti-spoofing measures are implemented to detect and block forged source IP addresses from entering the trusted network.': {
        'risks': ['DNS Spoofing'],
        'controls': ['NES-1', 'NES-4'],
        'policies': ['POL-24'],
    },
    '1.4.4: System components that store cardholder data are not directly accessible from untrusted networks.': {
        'risks': ['Unauthorized Access'],
        'controls': ['NES-3', 'NES-1'],
        'policies': ['POL-24'],
    },
    '1.4.5: The disclosure of internal IP addresses and routing information is limited to only authorized parties.': {
        'risks': ['DNS Spoofing'],
        'controls': ['NES-3', 'NES-5'],
        'policies': ['POL-24'],
    },
    '1.5.1: Security controls are implemented on any computing devices, including company- and employee-owned devices, that connect to both untrusted networks (including the Internet) and the CDE': {
        'risks': ['Misconfiguration of employee endpoints', 'Man in the middle (MitM) attack for Network'],
        'controls': ['NES-7', 'NES-1'],
        'policies': ['POL-24', 'POL-29'],
    },
    '2.1.1: All security policies and operational procedures that are identified in Requirement 2 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-15', 'POL-21'],
    },
    '2.1.2: Roles and responsibilities for performing activities in Requirement 2 are documented, assigned, and understood.  New requirement- effective immediately': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-15'],
    },
    '2.2.1: Configuration standards are developed, implemented, and maintained': {
        'risks': ['Cloud misconfiguration', 'Security misconfiguration of APIs / Applications'],
        'controls': ['CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    '2.2.2: Vendor default accounts are managed': {
        'risks': ['Unauthorized Access', 'Brute force attack'],
        'controls': ['IAM-5', 'CM-3'],
        'policies': ['POL-15', 'POL-1'],
    },
    '2.2.3: Primary functions requiring different security levels are managed': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['NES-3', 'CM-3'],
        'policies': ['POL-15'],
    },
    '2.2.4: Only necessary services, protocols, daemons, and functions are enabled, and all unnecessary functionality is removed or disabled.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['CMM-1', 'CM-3'],
        'policies': ['POL-15'],
    },
    '2.2.5: If any insecure services, protocols, or daemons are present then i.) Business justification is documented.ii.) Additional security features are documented and implemented that reduce the risk of using insecure services, protocols, or daemons.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['CMM-1', 'CM-3'],
        'policies': ['POL-15'],
    },
    '2.2.6: System security parameters are configured to prevent misuse.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['CM-3', 'CMM-2'],
        'policies': ['POL-15'],
    },
    '2.2.7: All non-console administrative access is encrypted using strong cryptography.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'CM-3'],
        'policies': ['POL-15', 'POL-19'],
    },
    '2.3.1: For wireless environments connected to the CDE or transmitting account data, all wireless vendor defaults are changed at installation or are confirmed to be secure.': {
        'risks': ['Cloud misconfiguration', 'Man in the middle (MitM) attack for Network'],
        'controls': ['CM-3', 'NES-3'],
        'policies': ['POL-15', 'POL-24'],
    },
    '2.3.2: For wireless environments connected to the CDE or transmitting account data, wireless encryption keys are changed': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CM-3'],
        'policies': ['POL-15', 'POL-19'],
    },
    '3.1.1: All security policies and operational procedures that are identified in Requirement 3 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-16', 'POL-21'],
    },
    '3.1.2: Roles and responsibilities for performing activities in Requirement 3 are documented, assigned, and understood.* New requirement- effective immediately': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-16'],
    },
    '3.2.1: Account data storage is kept to a minimum through implementation of data retention and disposal policies, procedures, and processes': {
        'risks': ['Data loss / corruption', 'Data breach'],
        'controls': ['DCH-4', 'DCH-2'],
        'policies': ['POL-17', 'POL-16'],
    },
    '3.3.1: SAD is not retained after authorization, even if encrypted. All sensitive authentication data received is rendered unrecoverable upon completion of the authorization process': {
        'risks': ['Data breach', 'Data loss / corruption'],
        'controls': ['DCH-4', 'DCH-2'],
        'policies': ['POL-17', 'POL-16'],
    },
    '3.3.1.1: The full contents of any track are not retained upon completion of the authorization process.': {
        'risks': ['Data breach', 'Data loss / corruption'],
        'controls': ['DCH-4', 'DCH-2'],
        'policies': ['POL-17', 'POL-16'],
    },
    '3.3.1.2: The card verification code is not retained upon completion of the authorization process.': {
        'risks': ['Data breach', 'Data loss / corruption'],
        'controls': ['DCH-4', 'DCH-2'],
        'policies': ['POL-17', 'POL-16'],
    },
    '3.3.1.3: The personal identification number (PIN) and the PIN block are not retained upon completion of the authorization process.': {
        'risks': ['Data breach', 'Data loss / corruption'],
        'controls': ['DCH-4', 'DCH-2'],
        'policies': ['POL-17', 'POL-16'],
    },
    '3.3.2: SAD that is stored electronically prior to completion of authorization is encrypted using strong cryptography.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-2', 'DCH-2'],
        'policies': ['POL-19', 'POL-16'],
    },
    '3.3.3: Additional requirement for issuers and companies that support issuing services and store sensitive authentication data.': {
        'risks': ['Data breach'],
        'controls': ['DCH-2', 'CRY-2'],
        'policies': ['POL-16', 'POL-19'],
    },
    '3.4.1: PAN is masked when displayed (the BIN and last four digits are the maximum number of digits to be displayed), such that only personnel with a legitimate business need can see more than the BIN and last four digits of the PAN.': {
        'risks': ['Accidental disclosure of sensitive customer data during support or other operations'],
        'controls': ['DCH-2', 'IAM-7'],
        'policies': ['POL-16', 'POL-14'],
    },
    '3.4.2: When using remote-access technologies, technical controls prevent copy and/or relocation of PAN for all personnel, except for those with documented, explicit authorization and a legitimate, defined business need.': {
        'risks': ['Data theft from Laptops and other employee owned devices'],
        'controls': ['DCH-2', 'IAM-7'],
        'policies': ['POL-16', 'POL-29'],
    },
    '3.5.1: PAN is rendered unreadable anywhere it is stored.': {
        'risks': ['Data breach', 'Weak cryptography & encryption support in the application'],
        'controls': ['CRY-2', 'DCH-2'],
        'policies': ['POL-19', 'POL-16'],
    },
    '3.5.1.1: Hashes used to render PAN unreadable (per the first bullet of Requirement 3.5.1), are keyed cryptographic hashes of the entire PAN, with associated key-management processes and procedures in accordance with Requirements 3.6 and 3.7.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-2', 'CRY-3'],
        'policies': ['POL-19'],
    },
    '3.5.1.2: If disk-level or partition-level encryption (rather than file-, column-, or field-level database encryption) is used to render PAN unreadable, it is implemented only as follows.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-2', 'CRY-3'],
        'policies': ['POL-19'],
    },
    '3.5.1.3: If disk-level or partition-level encryption is used (rather than file-, column-, or field--level database encryption) to render PAN unreadable, it is managed.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-2', 'CRY-3'],
        'policies': ['POL-19'],
    },
    '3.6.1: Procedures are defined and implemented to protect cryptographic keys used to protect stored account data against disclosure and misuse.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '3.6.1.1: Additional requirement for service providers only: A documented description of the cryptographic architecture is maintained.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '3.6.1.2: Secret and private keys used to encrypt/decrypt stored account data are stored.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-2', 'CRY-3'],
        'policies': ['POL-19'],
    },
    '3.6.1.3: Access to cleartext cryptographic key components is restricted to the fewest number of custodians necessary.': {
        'risks': ['Unauthorized access'],
        'controls': ['CRY-3', 'IAM-4'],
        'policies': ['POL-19', 'POL-4'],
    },
    '3.6.1.4: Cryptographic keys are stored in the fewest possible locations.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3'],
        'policies': ['POL-19'],
    },
    '3.7.1: Key-management policies and procedures are implemented to include generation of strong cryptographic keys used to protect stored account data.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '3.7.2: Key-management policies and procedures are implemented to include secure distribution of cryptographic keys used to protect stored account data.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '3.7.3: Key-management policies and procedures are implemented to include secure storage of cryptographic keys used to protect stored account data.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '3.7.4: Key management policies and procedures are implemented for cryptographic key changes for keys that have reached the end of their cryptoperiod, as defined by the associated application vendor or key owner, and based on industry best practices and guidelines': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '3.7.5: Key management policies procedures are implemented to include the retirement, replacement, or destruction of keys used to protect stored account data.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '3.7.6: Where manual cleartext cryptographic key-management operations are performed by personnel, key-management policies and procedures are implemented include managing these operations using split knowledge and dual control.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3'],
        'policies': ['POL-19'],
    },
    '3.7.7: Key management policies and procedures are implemented to include the prevention of unauthorized substitution of cryptographic keys.': {
        'risks': ['Unauthorized changes'],
        'controls': ['CRY-3'],
        'policies': ['POL-19'],
    },
    '3.7.8: Key management policies and procedures are implemented to include that cryptographic key custodians formally acknowledge (in writing or electronically) that they understand and accept their key-custodian responsibilities.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['CRY-3', 'HRM-1'],
        'policies': ['POL-19'],
    },
    '3.7.9: Additional requirement for service providers only: Where a service provider shares cryptographic keys with its customers for transmission or storage of account data, guidance on secure transmission, storage and updating of such keys is documented and distributed to the service provider\'s customers.': {
        'risks': ['Exposure to third party vendors'],
        'controls': ['CRY-3', 'TPM-1'],
        'policies': ['POL-19', 'POL-34'],
    },
    '4.1.1: All security policies and operational procedures that are identified in Requirement 4 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-19', 'POL-21'],
    },
    '4.1.2: Roles and responsibilities for performing activities in Requirement 4 are documented, assigned, and understood.  New requirement- effective immediately': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-19'],
    },
    '4.2.1: Strong cryptography and security protocols are implemented to safeguard PAN during transmission over open, public networks.': {
        'risks': ['Man in the middle (MitM) attack for Network', 'Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'CRY-3'],
        'policies': ['POL-19'],
    },
    '4.2.1.1: An inventory of the entity\'s trusted keys and certificates is maintained.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-3', 'CRY-1'],
        'policies': ['POL-19'],
    },
    '4.2.1.2: Wireless networks transmitting PAN or connected to the CDE use industry best practices to implement strong cryptography for authentication and transmission.': {
        'risks': ['Man in the middle (MitM) attack for Network', 'Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'NES-3'],
        'policies': ['POL-19', 'POL-24'],
    },
    '4.2.2: PAN is secured with strong cryptography whenever it is sent via end-user messaging technologies.': {
        'risks': ['Data breach', 'Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'CRY-2'],
        'policies': ['POL-19'],
    },
    '5.1.1: All security policies and operational procedures that are identified in Requirement 5 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-5', 'POL-21'],
    },
    '5.1.2: Roles and responsibilities for performing activities in Requirement 5 are documented, assigned, and understood.  New requirement- effective immediately': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-5'],
    },
    '5.2.1: An anti-malware solution(s) is deployed on all system components, except for those system components identified in periodic evaluations per Requirement 5.2.3 that concludes the system components are not at risk from malware.': {
        'risks': ['Malware'],
        'controls': ['CVM-5', 'CVM-6', 'GOV-6'],
        'policies': ['POL-5'],
    },
    '5.2.2: The deployed anti-malware solution(s), detects all known types of malware and removes, blocks, or contains all known types of malware.': {
        'risks': ['Malware', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '5.2.3: Any system components that are not at risk for malware are evaluated periodically.': {
        'risks': ['Malware'],
        'controls': ['CVM-5', 'CVM-6', 'GOV-6'],
        'policies': ['POL-5'],
    },
    '5.2.3.1: The frequency of periodic evaluations of system components identified as not at risk for malware is defined in the entity\'s targeted risk analysis, which is performed according to all elements specified in Requirement 12.3.1.': {
        'risks': ['Malware'],
        'controls': ['CVM-5', 'CVM-6', 'GOV-6'],
        'policies': ['POL-5'],
    },
    '5.3.1: The anti-malware solution(s) is kept current via automatic updates.': {
        'risks': ['Malware'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '5.3.2: The anti-malware solution(s):- Performs periodic scans and active or real-time scans OR- Performs continuous behavioral analysis of systems or processes.': {
        'risks': ['Malware'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '5.3.2.1: If periodic malware scans are performed to meet Requirement 5.3.2, the frequency of scans is defined in the entity\'s targeted risk analysis, which is performed according to all elements specified in Requirement 12.3.1.': {
        'risks': ['Malware'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '5.3.3: For removable electronic media, the anti-malware solution(s): - Performs automatic scans of when the media is inserted, connected, or logically mounted, OR- Performs continuous behavioral analysis of systems or processes when the media is inserted, connected, or logically mounted.': {
        'risks': ['Malware'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '5.3.4: Audit logs for the anti-malware solution(s) are enabled and retained in accordance with Requirement 10.5.1.': {
        'risks': ['Insufficient logging'],
        'controls': ['CVM-5', 'ALM-2'],
        'policies': ['POL-5', 'POL-22'],
    },
    '5.3.5: Anti-malware mechanisms cannot be disabled or altered by users, unless specifically documented, and authorized by management on a case-by-case basis for a limited time period.': {
        'risks': ['Malware', 'Insider Threat'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '5.4.1: Processes and automated mechanisms are in place to detect and protect personnel against phishing attacks.': {
        'risks': ['Phishing', 'Malware'],
        'controls': ['CVM-5', 'HRM-8'],
        'policies': ['POL-5', 'POL-21'],
    },
    '6.1.1: All security policies and operational procedures that are identified in Requirement 6 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-6', 'POL-21'],
    },
    '6.1.2: Roles and responsibilities for performing activities in Requirement 6 are documented, assigned, and understood.  New requirement- effective immediately.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-6'],
    },
    '6.2.1: Bespoke and custom software are developed securely.': {
        'risks': ['Cross-Site Scripting XSS', 'SQL Injection Attack', 'Input Validation Attack'],
        'controls': ['APD-1', 'APD-6'],
        'policies': ['POL-33', 'POL-6'],
    },
    '6.2.2: Software development personnel working on bespoke and custom software are trained at least once every 12 months.': {
        'risks': ['Lack of design reviews & security testing'],
        'controls': ['APD-1', 'HRM-8'],
        'policies': ['POL-33'],
    },
    '6.2.3: Bespoke and custom software is reviewed prior to being released into production or to customers, to identify and correct potential coding vulnerabilities.': {
        'risks': ['Lack of design reviews & security testing', 'Source code disclosure'],
        'controls': ['APD-4', 'APD-2'],
        'policies': ['POL-33', 'POL-6'],
    },
    '6.2.3.1: If manual code reviews are performed for bespoke and custom software prior to release to production.': {
        'risks': ['Lack of design reviews & security testing'],
        'controls': ['APD-4', 'APD-2'],
        'policies': ['POL-33'],
    },
    '6.2.4: Software engineering techniques or other methods are defined and in use by software development personnel to prevent or mitigate common software attacks and related vulnerabilities for bespoke and custom software.': {
        'risks': ['Cross-Site Scripting XSS', 'SQL Injection Attack', 'Buffer Overflow Attack'],
        'controls': ['APD-1', 'APD-4'],
        'policies': ['POL-33'],
    },
    '6.3.1: Security vulnerabilities are identified and managed.': {
        'risks': ['Unpatched vulnerability exploitation', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-3'],
        'policies': ['POL-35', 'POL-26'],
    },
    '6.3.2: An inventory of bespoke and custom software, and third-party software components incorporated into bespoke and custom software is maintained to facilitate vulnerability and patch management.': {
        'risks': ['Software supply chain malware attack'],
        'controls': ['CMM-1', 'AST-1'],
        'policies': ['POL-7', 'POL-6'],
    },
    '6.3.3: All system components are protected from known vulnerabilities by installing applicable security patches/updates.': {
        'risks': ['Unpatched vulnerability exploitation'],
        'controls': ['CVM-3', 'CVM-7'],
        'policies': ['POL-26'],
    },
    '6.4.1: For public-facing web applications, new threats and vulnerabilities are addressed on an ongoing basis and these applications are protected against known attacks.': {
        'risks': ['Unpatched vulnerability exploitation', 'Zero-Day Exploit'],
        'controls': ['NES-1', 'CVM-1'],
        'policies': ['POL-6', 'POL-35'],
    },
    '6.4.2: For public-facing web applications, an automated technical solution is deployed that continually detects and prevents web-based attacks.': {
        'risks': ['Cross-Site Scripting XSS', 'SQL Injection Attack'],
        'controls': ['NES-1', 'APD-4'],
        'policies': ['POL-6'],
    },
    '6.4.3: All payment page scripts that are loaded and executed in the consumer\'s browser are managed.': {
        'risks': ['Cross-Site Scripting XSS'],
        'controls': ['APD-1', 'APD-4'],
        'policies': ['POL-6'],
    },
    '6.5.1: Changes to all system components in the production environment are made according to established procedures.': {
        'risks': ['Unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'CHM-4'],
        'policies': ['POL-11'],
    },
    '6.5.2: Upon completion of a significant change, all applicable PCI DSS requirements are confirmed to be in place on all new or changed systems and networks, and documentation is updated as applicable.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['CHM-1', 'GOV-3'],
        'policies': ['POL-11'],
    },
    '6.5.3: Pre-production environments are separated from production environments and the separation is enforced with access controls.': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['APD-5', 'NES-3'],
        'policies': ['POL-33'],
    },
    '6.5.4: Roles and functions are separated between production and pre-production environments to provide accountability such that only reviewed and approved changes are deployed.': {
        'risks': ['Unauthorized changes'],
        'controls': ['APD-5', 'IAM-7'],
        'policies': ['POL-33', 'POL-4'],
    },
    '6.5.5: Live PANs are not used in pre-production environments, except where those environments are included in the CDE and protected in accordance with all applicable PCI DSS requirements.': {
        'risks': ['Data breach'],
        'controls': ['APD-5', 'DCH-2'],
        'policies': ['POL-33', 'POL-16'],
    },
    '6.5.6: Test data and test accounts are removed from system components before the system goes into production.': {
        'risks': ['Data breach'],
        'controls': ['APD-5', 'CHM-4'],
        'policies': ['POL-33'],
    },
    '7.1.1: All security policies and operational procedures that are identified in Requirement 7 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-4', 'POL-21'],
    },
    '7.1.2: Roles and responsibilities for performing activities in Requirement 7 are documented, assigned, and understood.  New requirement- effective immediately': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-4'],
    },
    '7.2.1: An access control model is defined and includes granting access.': {
        'risks': ['Unauthorized Access', 'Privilege escalation'],
        'controls': ['IAM-7', 'IAM-8'],
        'policies': ['POL-4'],
    },
    '7.2.2: Access is assigned to users, including privileged users, based on:- Job classification and function.- Least privileges necessary to perform job responsibilities.': {
        'risks': ['Improper assignment of privileged functions'],
        'controls': ['IAM-7', 'IAM-1'],
        'policies': ['POL-4'],
    },
    '7.2.3: Required privileges are approved by authorized personnel.': {
        'risks': ['Privilege escalation'],
        'controls': ['IAM-4', 'IAM-1'],
        'policies': ['POL-4'],
    },
    '7.2.4: All user accounts and related access privileges, including third-party/vendor accounts, are reviewed.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-3', 'IAM-4'],
        'policies': ['POL-4'],
    },
    '7.2.5: All application and system accounts and related access privileges are assigned and managed.': {
        'risks': ['Unauthorized Access', 'Improper assignment of privileged functions'],
        'controls': ['IAM-7', 'IAM-3'],
        'policies': ['POL-4'],
    },
    '7.2.5.1: All access by application and system accounts and related access privileges are reviewed.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-3', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '7.2.6: All user access to query repositories of stored cardholder data is restricted.': {
        'risks': ['Data breach', 'Unauthorized Access'],
        'controls': ['IAM-7', 'DCH-3'],
        'policies': ['POL-4', 'POL-16'],
    },
    '7.3.1: An access control system(s) is in place that restricts access based on a user\'s need to know and covers all system components.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-7', 'IAM-1'],
        'policies': ['POL-4'],
    },
    '7.3.2: The access control system(s) is configured to enforce privileges assigned to individuals, applications, and systems based on job classification and function.': {
        'risks': ['Improper assignment of privileged functions'],
        'controls': ['IAM-7'],
        'policies': ['POL-4'],
    },
    '7.3.3: The access control system(s) is set to ï¿½deny all- by default.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-7'],
        'policies': ['POL-4'],
    },
    '8.1.1: All security policies and operational procedures that are identified in Requirement 8 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-1', 'POL-21'],
    },
    '8.1.2: Roles and responsibilities for performing activities in Requirement 8 are documented, assigned, and understood. New requirement- effective immediately.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-1'],
    },
    '8.2.1: All users are assigned a unique ID before access to system components or cardholder data is allowed.': {
        'risks': ['Unauthorized Access', 'Inability to maintain individual accountability'],
        'controls': ['IAM-5', 'IAM-1'],
        'policies': ['POL-4', 'POL-1'],
    },
    '8.2.2: Group, shared, or generic accounts, or other shared authentication credentials are only used when necessary on an exception basis, and are managed.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-5', 'IAM-3'],
        'policies': ['POL-4', 'POL-1'],
    },
    '8.2.3: Additional requirement for service providers only: Service providers with remote access to customer premises use unique authentication factors for each customer premises.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1', 'POL-4'],
    },
    '8.2.4: Addition, deletion, and modification of user IDs, authentication factors, and other identifier objects are managed.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-1', 'IAM-3'],
        'policies': ['POL-4'],
    },
    '8.2.5: Access for terminated users is immediately revoked.': {
        'risks': ['Ex-Employees / disgruntled employees'],
        'controls': ['HRM-7', 'IAM-3'],
        'policies': ['POL-4', 'POL-27'],
    },
    '8.2.6: Inactive user accounts are removed or disabled within 90 days of inactivity.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-3'],
        'policies': ['POL-4'],
    },
    '8.2.7: Accounts used by third parties to access, support, or maintain system components via remote access are managed.': {
        'risks': ['Exposure to third party vendors', 'Unauthorized Access'],
        'controls': ['IAM-4', 'TPM-1'],
        'policies': ['POL-4', 'POL-34'],
    },
    '8.2.8: If a user session has been idle for more than 15 minutes, the user is required to re-authenticate to re-activate the terminal or session.': {
        'risks': ['Session Hijacking'],
        'controls': ['IAM-5'],
        'policies': ['POL-1'],
    },
    '8.3.1: All user access to system components for users and administrators is authenticated via at least one of the following authentication factors:- Something you know, such as a password or passphrase.- Something you have, such as a token device or smart card.- Something you are, such as a biometric element.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    '8.3.2: Strong cryptography is used to render all authentication factors unreadable during transmission and storage on all system components.': {
        'risks': ['Credential Stuffing', 'Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'IAM-5'],
        'policies': ['POL-1', 'POL-19'],
    },
    '8.3.3: User identity is verified before modifying any authentication factor.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-5'],
        'policies': ['POL-1'],
    },
    '8.3.4: Invalid authentication attempts are limited by:- Locking out the user ID after not more than 10 attempts.- Setting the lockout duration to a minimum of 30 minutes or until the user\'s identity is confirmed.': {
        'risks': ['Brute force attack'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1'],
    },
    '8.3.5: If passwords/passphrases are used as authentication factors to meet Requirement 8.3.1, they are set and reset for each user.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    '8.3.6: If passwords/passphrases are used as authentication factors to meet Requirement 8.3.1, they meet the following minimum level of complexity.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    '8.3.7: Individuals are not allowed to submit a new password/passphrase that is the same as any of the last four passwords/passphrases used.': {
        'risks': ['Credential Stuffing'],
        'controls': ['IAM-9'],
        'policies': ['POL-1'],
    },
    '8.3.8: Authentication policies and procedures are documented and communicated to all users .': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-9', 'GOV-1'],
        'policies': ['POL-1'],
    },
    '8.3.9: If passwords/passphrases are used as the only authentication factor for user access (i.e., in any single-factor authentication implementation) then either:- Passwords/passphrases are changed at least once every 90 days,  OR- The security posture of accounts is dynamically analyzed, and real-time access to resources is automatically determined accordingly.': {
        'risks': ['Brute force attack', 'Broken or weak authentication'],
        'controls': ['IAM-9', 'IAM-5'],
        'policies': ['POL-1'],
    },
    '8.3.10: Additional requirement for service providers only: If passwords/passphrases are used as the only authentication factor for customer user access to cardholder data (i.e., in any single-factor authentication implementation), then guidance is provided to customer users.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    '8.3.10.1: Additional requirement for service providers only: If passwords/passphrases are used as the only authentication factor for customer user access (i.e., in any single-factor authentication implementation).': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    '8.3.11: Where authentication factors such as physical or logical security tokens, smart cards, or certificates are used:- Factors are assigned to an individual user and not shared among multiple users.- Physical and/or logical controls ensure only the intended user can use that factor to gain access.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    '8.4.1: MFA is implemented for all non-console access into the CDE for personnel with administrative access.': {
        'risks': ['Unauthorized Access', 'Broken or weak authentication'],
        'controls': ['IAM-6'],
        'policies': ['POL-1', 'POL-4'],
    },
    '8.4.2: MFA is implemented for all access into the CDE.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-6'],
        'policies': ['POL-1', 'POL-4'],
    },
    '8.4.3: MFA is implemented for all remote network access originating from outside the entity\'s network that could access or impact the CDE.': {
        'risks': ['Unauthorized Access', 'Man in the middle (MitM) attack for Network'],
        'controls': ['IAM-6', 'NES-7'],
        'policies': ['POL-1', 'POL-29'],
    },
    '8.5.1: MFA systems are implemented.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-6', 'IAM-5'],
        'policies': ['POL-1'],
    },
    '8.6.1: If accounts used by systems or applications can be used for interactive login, they are managed.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-5', 'IAM-3'],
        'policies': ['POL-1', 'POL-4'],
    },
    '8.6.2: Passwords/passphrases for any application and system accounts that can be used for interactive login are not hard coded in scripts, configuration/property files, or bespoke and custom source code. Note: stored passwords/ passphrases are required to be encrypted in accordance with PCI DSS Requirement 8.3.2.': {
        'risks': ['Credential Stuffing', 'Source code disclosure'],
        'controls': ['IAM-9', 'APD-1'],
        'policies': ['POL-1', 'POL-33'],
    },
    '8.6.3: Passwords/passphrases for any application and system accounts are protected against misuse.': {
        'risks': ['Credential Stuffing', 'Brute force attack'],
        'controls': ['IAM-9', 'IAM-5'],
        'policies': ['POL-1'],
    },
    '9.1.1: All security policies and operational procedures that are identified in Requirement 9 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-28', 'POL-21'],
    },
    '9.1.2: Roles and responsibilities for performing activities in Requirement 9 are documented, assigned, and understood. New requirement- effective immediately.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-28'],
    },
    '9.2.1: Appropriate facility entry controls are in place to restrict physical access to systems in the CDE.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-1'],
        'policies': ['POL-28'],
    },
    '9.2.1.1: Individual physical access to sensitive areas within the CDE is monitored with either video cameras or physical access control mechanisms (or both) .': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-1', 'PES-2'],
        'policies': ['POL-28'],
    },
    '9.2.2: Physical and/or logical controls are implemented to restrict use of publicly accessible network jacks within the facility.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-1', 'NES-3'],
        'policies': ['POL-28'],
    },
    '9.2.3: Physical access to wireless access points, gateways, networking/communications hardware, and telecommunication lines within the facility is restricted.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    '9.2.4: Access to consoles in sensitive areas is restricted via locking when not in use.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-1'],
        'policies': ['POL-28'],
    },
    '9.3.1: Procedures are implemented for authorizing and managing physical access of personnel to the CDE.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-1', 'PES-3'],
        'policies': ['POL-28'],
    },
    '9.3.1.1: Physical access to sensitive areas within the CDE for personnel is controlled.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-1', 'IAM-7'],
        'policies': ['POL-28'],
    },
    '9.3.2: Procedures are implemented for authorizing and managing visitor access to the CDE.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-3'],
        'policies': ['POL-28'],
    },
    '9.3.3: Visitor badges or identification are surrendered or deactivated before visitors leave the facility or at the date of expiration.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-3'],
        'policies': ['POL-28'],
    },
    '9.3.4: A visitor log is used to maintain a physical record of visitor activity within the facility and within sensitive areas.': {
        'risks': ['Unauthorized Access'],
        'controls': ['PES-3'],
        'policies': ['POL-28'],
    },
    '9.4.1: All media with cardholder data is physically secured.': {
        'risks': ['Data breach', 'Data loss / corruption'],
        'controls': ['PES-4', 'DCH-2'],
        'policies': ['POL-28', 'POL-16'],
    },
    '9.4.1.1: Offline media backups with cardholder data are stored in a secure location.': {
        'risks': ['Data loss / corruption'],
        'controls': ['DRC-1', 'DRC-2', 'PES-4'],
        'policies': ['POL-28', 'POL-9'],
    },
    '9.4.1.2: The security of the offline media backup location(s) with cardholder data is reviewed at least once every 12 months.': {
        'risks': ['Data loss / corruption'],
        'controls': ['DRC-2', 'PES-4'],
        'policies': ['POL-28', 'POL-9'],
    },
    '9.4.2: All media with cardholder data is classified in accordance with the sensitivity of the data.': {
        'risks': ['Data breach'],
        'controls': ['DCH-2', 'DCH-5'],
        'policies': ['POL-16', 'POL-28'],
    },
    '9.4.3: Media with cardholder data sent outside the facility is secured.': {
        'risks': ['Data breach'],
        'controls': ['DCH-2', 'PES-4'],
        'policies': ['POL-28', 'POL-16'],
    },
    '9.4.4: Management approves all media with cardholder data that is moved outside the facility (including when media is distributed to individuals).': {
        'risks': ['Data breach'],
        'controls': ['DCH-2', 'PES-4'],
        'policies': ['POL-28'],
    },
    '9.4.5: Inventory logs of all electronic media with cardholder data are maintained.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['AST-1', 'AST-3'],
        'policies': ['POL-7', 'POL-28'],
    },
    '9.4.5.1: Inventories of electronic media with cardholder data are conducted at least once every 12 months.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['AST-1'],
        'policies': ['POL-7', 'POL-28'],
    },
    '9.4.6: Hard-copy materials with cardholder data are destroyed when no longer needed for business or legal reasons.': {
        'risks': ['Data breach'],
        'controls': ['DCH-4', 'AST-2'],
        'policies': ['POL-17', 'POL-28'],
    },
    '9.4.7: Electronic media with cardholder data is destroyed when no longer needed for business or legal reasons via one of the following:- The electronic media is destroyed.- The cardholder data is rendered unrecoverable so that it cannot be reconstructed.': {
        'risks': ['Data breach'],
        'controls': ['DCH-4', 'AST-2'],
        'policies': ['POL-17', 'POL-28'],
    },
    '9.5.1: POI devices that capture payment card data via direct physical interaction with the payment card form factor are protected from tampering and unauthorized substitution.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    '9.5.1.1: An up-to-date list of POI devices is maintained, including:- Make and model of the device.- Location of device.- Device serial number or other methods of unique identification.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['AST-1', 'PES-1'],
        'policies': ['POL-28', 'POL-7'],
    },
    '9.5.1.2: POI device surfaces are periodically inspected to detect tampering and unauthorized substitution.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['PES-1'],
        'policies': ['POL-28'],
    },
    '9.5.1.2.1: The frequency of periodic POI device inspections and the type of inspections performed is defined in the entity\'s targeted risk analysis, which is performed according to all elements specified in Requirement 12.3.1.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['PES-1', 'GOV-6'],
        'policies': ['POL-28'],
    },
    '9.5.1.3: Training is provided for personnel in POI environments to be aware of attempted tampering or replacement of POI devices.': {
        'risks': ['Lack of cybersecurity awareness'],
        'controls': ['HRM-8', 'PES-1'],
        'policies': ['POL-28'],
    },
    '10.1.1: All security policies and operational procedures that are identified in Requirement 10 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-22', 'POL-21'],
    },
    '10.1.2: Roles and responsibilities for performing activities in Requirement 10 are documented, assigned, and understood. New requirement- effective immediately.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-22'],
    },
    '10.2.1: Audit logs are enabled and active for all system components and cardholder data.': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '10.2.1.1: Audit logs capture all individual user access to cardholder data.': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '10.2.1.2: Audit logs capture all actions taken by any individual with administrative access, including any interactive use of application or system accounts.': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '10.2.1.3: Audit logs capture all access to audit logs.': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '10.2.1.4: Audit logs capture all invalid logical access attempts.': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '10.2.1.5: Audit logs capture all changes to identification and authentication credentials including, but not limited to:- Creation of new accounts.- Elevation of privileges.- All changes, additions, or deletions to accounts with administrative access.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'IAM-2'],
        'policies': ['POL-22'],
    },
    '10.2.1.6: Audit logs capture the following:- All initialization of new audit logs, and- All starting, stopping, or pausing of the existing audit logs.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'CVM-4'],
        'policies': ['POL-22'],
    },
    '10.2.1.7: Audit logs capture all creation and deletion of system-level objects.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2'],
        'policies': ['POL-22'],
    },
    '10.2.2: Audit logs record the following details for each auditable event:- User identification.- Type of event.- Date and time.- Success and failure indication.- Origination of event.- Identity or name of affected data, system component, resource, or service (for example, name and protocol).': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '10.3.1: Read access to audit logs files is limited to those with a job-related need.': {
        'risks': ['Unauthorized Access'],
        'controls': ['ALM-2', 'IAM-7'],
        'policies': ['POL-22'],
    },
    '10.3.2: Audit log files are protected to prevent modifications by individuals.': {
        'risks': ['Unauthorized changes'],
        'controls': ['ALM-2', 'CVM-4'],
        'policies': ['POL-22'],
    },
    '10.3.3: Audit log files, including those for external-facing technologies, are promptly backed up to a secure, central, internal log server(s) or other media that is difficult to modify.': {
        'risks': ['Data loss / corruption'],
        'controls': ['ALM-2', 'DRC-1'],
        'policies': ['POL-22', 'POL-9'],
    },
    '10.3.4: File integrity monitoring or change-detection mechanisms is used on audit logs to ensure that existing log data cannot be changed without generating alerts.': {
        'risks': ['Unauthorized changes'],
        'controls': ['CVM-4', 'ALM-2'],
        'policies': ['POL-22'],
    },
    '10.4.1: Audit logs are reviewed at least once daily.': {
        'risks': ['Insufficient monitoring & alerting'],
        'controls': ['ALM-3', 'ALM-2'],
        'policies': ['POL-22'],
    },
    '10.4.1.1: Automated mechanisms are used to perform audit log reviews.': {
        'risks': ['Insufficient monitoring & alerting'],
        'controls': ['ALM-3', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '10.4.2: Logs of all other system components (those not specified in Requirement 10.4.1) are reviewed periodically.': {
        'risks': ['Insufficient monitoring & alerting'],
        'controls': ['ALM-3', 'ALM-2'],
        'policies': ['POL-22'],
    },
    '10.4.2.1: The frequency of periodic log reviews for all other system components (not defined in Requirement 10.4.1) is defined in the entity\'s targeted risk analysis, which is performed according to all elements specified in Requirement 12.3.1.': {
        'risks': ['Insufficient monitoring & alerting'],
        'controls': ['ALM-3', 'ALM-2'],
        'policies': ['POL-22'],
    },
    '10.4.3: Exceptions and anomalies identified during the review process are addressed.': {
        'risks': ['Improper response to incidents'],
        'controls': ['ALM-3', 'IRM-4'],
        'policies': ['POL-22', 'POL-20'],
    },
    '10.5.1: Retain audit log history for at least 12 months, with at least the most recent three months immediately available for analysis.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-4', 'ALM-2'],
        'policies': ['POL-22'],
    },
    '10.6.1: System clocks and time are synchronized using time-synchronization technology.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'CM-3'],
        'policies': ['POL-22', 'POL-15'],
    },
    '10.6.2: Systems are configured to the correct and consistent time.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'CM-3'],
        'policies': ['POL-22'],
    },
    '10.6.3: Time synchronization settings and data are protected.': {
        'risks': ['Unauthorized changes'],
        'controls': ['ALM-2', 'IAM-7'],
        'policies': ['POL-22'],
    },
    '10.7.1: Additional requirement for service providers only: Failures of critical security control systems are detected, alerted, and addressed promptly.': {
        'risks': ['Insufficient monitoring & alerting', 'Improper response to incidents'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22', 'POL-20'],
    },
    '10.7.2: Failures of critical security control systems are detected, alerted, and addressed promptly.': {
        'risks': ['Insufficient monitoring & alerting', 'Improper response to incidents'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22', 'POL-20'],
    },
    '10.7.3: Failures of any critical security controls systems are responded to promptly.': {
        'risks': ['Improper response to incidents'],
        'controls': ['ALM-1', 'IRM-1'],
        'policies': ['POL-22', 'POL-20'],
    },
    '11.1.1: All security policies and operational procedures that are identified in Requirement 11 are documented, kept up to date, in use and known to all affected parties.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-35', 'POL-21'],
    },
    '11.1.2: Roles and responsibilities for performing activities in Requirement 11 are documented, assigned, and understood. New requirement- effective immediately.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-35'],
    },
    '11.2.1: Authorized and unauthorized wireless access points are managed.': {
        'risks': ['Man in the middle (MitM) attack for Network'],
        'controls': ['NES-3', 'AST-1'],
        'policies': ['POL-35', 'POL-24'],
    },
    '11.2 2: An inventory of authorized wireless access points is maintained, including a documented business justification.': {
        'risks': [],
        'controls': ['GOV-1'],
        'policies': ['POL-21'],
    },
    '11.3.1: Internal vulnerability scans are performed.': {
        'risks': ['Unmitigated vulnerabilities', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-1'],
        'policies': ['POL-35'],
    },
    '11.3.1.1: All other applicable vulnerabilities (those not ranked as high-risk or critical (per the entity\'s vulnerability risk rankings defined at Requirement 6.3.1) are managed.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-3'],
        'policies': ['POL-35'],
    },
    '11.3.1.2: Internal vulnerability scans are performed via authenticated scanning.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1'],
        'policies': ['POL-35'],
    },
    '11.3.1.3: Internal vulnerability scans are performed after any significant change.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CHM-1'],
        'policies': ['POL-35', 'POL-11'],
    },
    '11.3.2: External vulnerability scans are performed.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2'],
        'policies': ['POL-35'],
    },
    '11.3.2.1: External vulnerability scans are performed after any significant change.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CHM-1'],
        'policies': ['POL-35'],
    },
    '11.4.1: A penetration testing methodology is defined, documented, and implemented by the entity.': {
        'risks': ['Unmitigated vulnerabilities', 'Lack of design reviews & security testing'],
        'controls': ['CVM-2'],
        'policies': ['POL-35'],
    },
    '11.4.2: Internal penetration testing is performed:- Per the entity\'s defined methodology- At least once every 12 months.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-2'],
        'policies': ['POL-35'],
    },
    '11.4.3: External penetration testing is performed:- Per the entity\'s defined methodology- At least once every 12 months.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-2'],
        'policies': ['POL-35'],
    },
    '11.4.4: Exploitable vulnerabilities and security weaknesses found during penetration testing are corrected.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2'],
        'policies': ['POL-35'],
    },
    '11.4.5: If segmentation is used to isolate the CDE from other networks, penetration tests are performed on segmentation controls as follows:- At least once every 12 months and after any changes to segmentation controls/methods.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-2', 'NES-3'],
        'policies': ['POL-35', 'POL-24'],
    },
    '11.4.6: Additional requirement for service providers only: If segmentation is used to isolate the CDE from other networks, penetration tests are performed on segmentation controls as follows:- At least once every six months and after any changes to segmentation controls/methods .': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-2', 'NES-3'],
        'policies': ['POL-35', 'POL-24'],
    },
    '11.4.7: Additional requirement for third-party hosted/cloud service providers only: Third-party hosted/cloud service providers support to their customers for external penetration testing per Requirement 11.4.3 and 11.4.4.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-2'],
        'policies': ['POL-35'],
    },
    '11.5.1: Intrusion-detection and/or intrusion-prevention techniques are used to detect and/or prevent intrusions into the network.': {
        'risks': ['Denial of Service (DoS) Attack', 'Advanced persistent threats (APT)'],
        'controls': ['NES-2', 'ALM-1'],
        'policies': ['POL-35', 'POL-24'],
    },
    '11.5.1.1: Additional requirement for service providers only: Intrusion-detection and/or intrusion-prevention techniques detect, alert on/prevent, and address covert malware communication channels.': {
        'risks': ['Malware', 'Advanced persistent threats (APT)'],
        'controls': ['NES-2', 'ALM-1'],
        'policies': ['POL-35', 'POL-24'],
    },
    '11.5.2: A change-detection mechanism (for example, file integrity monitoring tools) is deployed.': {
        'risks': ['Unauthorized changes'],
        'controls': ['CVM-4', 'ALM-2'],
        'policies': ['POL-35', 'POL-22'],
    },
    '11.6.1: A change- and tamper-detection mechanism is deployed.': {
        'risks': ['Unauthorized changes', 'Cross-Site Scripting XSS'],
        'controls': ['CVM-4', 'APD-4'],
        'policies': ['POL-35', 'POL-6'],
    },
    '12.1.1: An overall information security policy is:- Established.- Published.- Maintained.- Disseminated to all relevant personnel, as well as to relevant vendors and business partners.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-21'],
    },
    '12.1.2: The information security policy is:- Reviewed at least once every 12 months.- Updated as needed to reflect changes to business objectives or risks to the environment.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-21'],
    },
    '12.1.3: The security policy clearly defines information security roles and responsibilities for all personnel, and all personnel are aware and acknowledge their information security responsibilities.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-21'],
    },
    '12.1.4: Responsibility for information security is formally assigned to a Chief Information Security Officer or other information security knowledgeable member of executive management.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-4'],
        'policies': ['POL-21'],
    },
    '12.2.1: Acceptable use policies for end-user technologies are documented and implemented, including:- Explicit approval by authorized parties.- Acceptable uses of the technology.- List of products approved by the company for employee use, including hardware and software.': {
        'risks': ['Misappropriation & Misuse of devices'],
        'controls': ['AST-4', 'MDM-1'],
        'policies': ['POL-2', 'POL-23'],
    },
    '12.3.1: Each PCI DSS requirement that provides flexibility for how frequently it is performed (for example, requirements to be performed periodically) is supported by a targeted risk analysis that is documented.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-6', 'RSM-2'],
        'policies': ['POL-30'],
    },
    '12.3.2: A targeted risk analysis is performed for each PCI DSS requirement that the entity meets with the customized approach.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-6', 'RSM-2'],
        'policies': ['POL-30'],
    },
    '12.3.3: Cryptographic cipher suites and protocols in use are documented and reviewed at least once every 12 months.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-4', 'GOV-3'],
        'policies': ['POL-19'],
    },
    '12.3.4: Hardware and software technologies in use are reviewed at least once every 12 months.': {
        'risks': ['Unpatched vulnerability exploitation'],
        'controls': ['CMM-1', 'AST-1'],
        'policies': ['POL-7'],
    },
    '12.4.1: Additional requirement for service providers only: Responsibility is established by executive management for the protection of cardholder data and a PCI DSS compliance program to include:- Overall accountability for maintaining PCI DSS compliance.- Defining a charter for a PCI DSS compliance program and communication to executive management.': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-10', 'GOV-4'],
        'policies': ['POL-21'],
    },
    '12.4.2: Additional requirement for service providers only: Reviews are performed at least once every three months to confirm personnel are performing their tasks in accordance with all security policies and all operational procedures.': {
        'risks': ['Inadequate internal practices'],
        'controls': ['GOV-12', 'GOV-3'],
        'policies': ['POL-21'],
    },
    '12.4.2.1: Additional requirement for service providers only: Reviews conducted in accordance with Requirement 12.4.2 are documented.': {
        'risks': ['Inadequate internal practices'],
        'controls': ['GOV-12'],
        'policies': ['POL-21'],
    },
    '12.5.1: An inventory of system components that are in scope for PCI DSS, including a description of function/use, is maintained and kept current.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['AST-1', 'GOV-9'],
        'policies': ['POL-21', 'POL-7'],
    },
    '12.5.2: PCI DSS scope is documented and confirmed by the entity at least once every 12 months and upon significant change to the in-scope environment.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-9', 'GOV-11'],
        'policies': ['POL-21'],
    },
    '12.5.2.1: Additional requirement for service providers only: PCI DSS scope is documented and confirmed by the entity at least once every six months and after significant changes. At a minimum, the scoping validation includes all the elements specified in Requirement 12.5.2.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-9', 'GOV-11'],
        'policies': ['POL-21'],
    },
    '12.5.3: Additional requirement for service providers only: Significant changes to organizational structure result in a documented (internal) review of the impact to PCI DSS scope and applicability of controls, with results communicated to executive management.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-11', 'GOV-3'],
        'policies': ['POL-21'],
    },
    '12.6.1: A formal security awareness program is implemented to make all personnel aware of the entity\'s information security policy and procedures and their role in protecting the cardholder data.': {
        'risks': ['Lack of cybersecurity awareness'],
        'controls': ['HRM-8'],
        'policies': ['POL-21'],
    },
    '12.6.2: The security awareness program is:- Reviewed at least once every 12 months, and- Updated as needed to address any new threats and vulnerabilities that may impact the security of the entity\'s CDE, or the information provided to personnel about their role in protecting cardholder data.': {
        'risks': ['Lack of cybersecurity awareness'],
        'controls': ['HRM-8', 'GOV-3'],
        'policies': ['POL-21'],
    },
    '12.6.3: Personnel receive security awareness training as follows:- Upon hire and at least once every 12 months.': {
        'risks': ['Lack of cybersecurity awareness'],
        'controls': ['HRM-8'],
        'policies': ['POL-21'],
    },
    '12.6.3.1: Security awareness training includes awareness of threats and vulnerabilities that could impact the security of the CDE, including but not limited to:- Phishing and related attacks.- Social engineering.': {
        'risks': ['Phishing', 'Lack of cybersecurity awareness'],
        'controls': ['HRM-8'],
        'policies': ['POL-21'],
    },
    '12.6.3.2: Security awareness training includes awareness about the acceptable use of end-user technologies in accordance with Requirement 12.2.1.': {
        'risks': ['Lack of cybersecurity awareness'],
        'controls': ['HRM-8', 'AST-4'],
        'policies': ['POL-21', 'POL-2'],
    },
    '12.7.1: Potential personnel who will have access to the CDE are screened, within the constraints of local laws, prior to hire to minimize the risk of attacks from internal sources.': {
        'risks': ['Insider Threat'],
        'controls': ['HRM-2', 'HRM-4'],
        'policies': ['POL-27'],
    },
    '12.8.1: A list of all third-party service providers (TPSPs) with which account data is shared or that could affect the security of account data is maintained, including a description for each of the services provided.': {
        'risks': ['Exposure to third party vendors', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-1', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '12.8.2: Written agreements with TPSPs are maintained as follows:- Written agreements are maintained with all TPSPs with which account data is shared or that could affect the security of the CDE.': {
        'risks': ['Exposure to third party vendors'],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    '12.8.3: An established process is implemented for engaging TPSPs, including proper due diligence prior to engagement.': {
        'risks': ['Exposure to third party vendors'],
        'controls': ['TPM-3'],
        'policies': ['POL-34'],
    },
    '12.8.4: A program is implemented to monitor TPSPs- PCI DSS compliance status at least once every 12 months.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '12.8.5: Information is maintained about which PCI DSS requirements are managed by each TPSP, which are managed by the entity, and any that are shared between the TPSP and the entity.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-1', 'TPM-2'],
        'policies': ['POL-34'],
    },
    '12.9.1: Additional requirement for service providers only: TPSPs acknowledge in writing to customers that they are responsible for the security of account data the TPSP possesses or otherwise stores, processes, or transmits on behalf of the customer, or to the extent that they could impact the security of the customer\'s CDE.': {
        'risks': ['Exposure to third party vendors'],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    '12.9.2: Additional requirement for service providers only: TPSPs support their customers- requests for information to meet Requirements 12.8.4 and 12.8.5.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-2'],
        'policies': ['POL-34'],
    },
    '12.10.1: An incident response plan exists and is ready to be activated in the event of a suspected or confirmed security incident.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '12.10.2: At least once every 12 months, the security incident response plan is:- Reviewed and the content is updated as needed.- Tested, including all elements listed in Requirement 12.10.1.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '12.10.3: Specific personnel are designated to be available on a 24/7 basis to respond to suspected or confirmed security incidents.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-3'],
        'policies': ['POL-20'],
    },
    '12.10.4: Personnel responsible for responding to suspected and confirmed security incidents are appropriately and periodically trained on their incident response responsibilities.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'HRM-8'],
        'policies': ['POL-20'],
    },
    '12.10.4.1: The frequency of periodic training for incident response personnel is defined in the entity\'s targeted risk analysis which is performed according to all elements specified in Requirement 12.3.1.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'HRM-8', 'GOV-6'],
        'policies': ['POL-20'],
    },
    '12.10.5: The security incident response plan includes monitoring and responding to alerts from security monitoring systems.': {
        'risks': ['Insufficient monitoring & alerting'],
        'controls': ['ALM-1', 'IRM-4'],
        'policies': ['POL-20', 'POL-22'],
    },
    '12.10.6: The security incident response plan is modified and evolved according to lessons learned and to incorporate industry developments.': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['IRM-2', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '12.10.7: Incident response procedures are in place, to be initiated upon the detection of stored PAN anywhere it is not expected.': {
        'risks': ['Data breach'],
        'controls': ['IRM-4', 'DCH-1'],
        'policies': ['POL-20', 'POL-16'],
    },
    'A1.1.1: Logical separation is implemented as follows:- The provider cannot access its customers- environments without authorization.- Customers cannot access the provider\'s environment without authorization.': {
        'risks': ['Unauthorized Access', 'Privilege escalation'],
        'controls': ['NES-3', 'IAM-7'],
        'policies': ['POL-24', 'POL-4'],
    },
    'A1.1.2: Controls are implemented such that each customer only has permission to access its own cardholder data and CDE.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-7', 'DCH-3'],
        'policies': ['POL-4'],
    },
    'A1.1.3: Controls are implemented such that each customer can only access resources allocated to them.': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-7', 'NES-3'],
        'policies': ['POL-4'],
    },
    'A1.1.4: The effectiveness of logical separation controls used to separate customer environments is confirmed at least once every six months via penetration testing.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-2', 'NES-3'],
        'policies': ['POL-35'],
    },
    'A1.2.1: Audit log capability is enabled for each customer\'s environment that is consistent with PCI DSS Requirement 10.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    'A1.2.2: Processes or mechanisms are implemented to support and/or facilitate prompt forensic investigations in the event of a suspected or confirmed security incident for any customer.': {
        'risks': ['Inability to investigate / prosecute incidents'],
        'controls': ['ALM-2', 'IRM-1'],
        'policies': ['POL-22', 'POL-20'],
    },
    'A1.2.3: Processes or mechanisms are implemented for reporting and addressing suspected or confirmed security incidents and vulnerabilities.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-4', 'IRM-5'],
        'policies': ['POL-20'],
    },
    'A2.1.1: Where POS POI terminals at the merchant or payment acceptance location use SSL and/or early TLS, the entity confirms the devices are not susceptible to any known exploits for those protocols.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'CM-3'],
        'policies': ['POL-19', 'POL-15'],
    },
    'A2.1.2: Additional requirement for service providers only: All service providers with existing connection points to POS POI terminals that use SSL and/or early TLS as defined in A2.1 have a formal Risk Mitigation and Migration Plan in place.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'RSM-3'],
        'policies': ['POL-19', 'POL-30'],
    },
    'A2.1.3: Additional requirement for service providers only: All service providers provide a secure service offering.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1'],
        'policies': ['POL-19'],
    },
}
