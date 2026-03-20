# Maps each FTC Safeguards objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code in control_templates (BASELINE_CONTROLS)
# - policies: matched by POL code in policy_templates

FTC_SAFEGUARDS_CONNECTIONS = {
    '314.4.a.1: Retain responsibility for compliance with this part': {
        'risks': ['Lack of roles & responsibilities', 'Inadequate internal practices'],
        'controls': ['GOV-1', 'GOV-4', 'GOV-5'],
        'policies': ['POL-21', 'POL-30'],
    },
    '314.4.a.2: Designate a senior member of your personnel responsible for direction and oversight of the Qualified Individual': {
        'risks': ['Lack of roles & responsibilities', 'Lack of oversight of internal controls'],
        'controls': ['GOV-3', 'GOV-9', 'GOV-10'],
        'policies': ['POL-21', 'POL-30'],
    },
    '314.4.a.3: Require the service provider or affiliate to maintain an information security program that protects you in accordance with the requirements of this part': {
        'risks': ['Exposure to third party vendors', 'Third-party cybersecurity exposure', 'Inadequate third-party practices'],
        'controls': ['TPM-1', 'TPM-2', 'TPM-3'],
        'policies': ['POL-34', 'POL-21'],
    },
    '314.4.b.1: The risk assessment shall be written': {
        'risks': ['Incorrect controls scoping', 'Inadequate internal practices'],
        'controls': ['RSM-2', 'RSM-3', 'GOV-6'],
        'policies': ['POL-30', 'POL-21'],
    },
    '314.4.b.2: Periodically perform additional risk assessments': {
        'risks': ['Incorrect controls scoping', 'Unmitigated vulnerabilities', 'Inadequate internal practices'],
        'controls': ['RSM-2', 'RSM-3', 'RSM-4'],
        'policies': ['POL-30', 'POL-36'],
    },
    '314.4.c.1: Implementing and periodically reviewing access controls, including technical and, as appropriate, physical controls': {
        'risks': ['Unauthorized access', 'Unauthorized Access', 'Improper assignment of privileged functions', 'Privilege escalation'],
        'controls': ['IAM-1', 'IAM-2', 'IAM-3', 'IAM-4', 'IAM-5', 'IAM-7'],
        'policies': ['POL-1', 'POL-4'],
    },
    '314.4.c.2: Identify and manage the data, personnel, devices, systems, and facilities that enable you to achieve business purposes in accordance with their relative importance to business objectives and your risk strategy': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Shadow IT', 'Misconfiguration of employee endpoints'],
        'controls': ['AST-1', 'AST-2', 'AST-3', 'AST-4', 'DCH-1'],
        'policies': ['POL-7', 'POL-16'],
    },
    '314.4.c.3: Protect by encryption all customer information held or transmitted by you both in transit over external networks and at rest': {
        'risks': ['Weak cryptography & encryption support in the application', 'Data loss / corruption', 'Data breach'],
        'controls': ['CRY-1', 'CRY-2', 'CRY-3', 'CRY-4', 'DCH-2'],
        'policies': ['POL-19', 'POL-14'],
    },
    '314.4.c.4: Adopt secure development practices for in-house developed applications': {
        'risks': ['Lack of design reviews & security testing', 'Security misconfiguration of APIs / Applications', 'Source code disclosure'],
        'controls': ['APD-1', 'APD-2', 'APD-3', 'APD-4', 'APD-5', 'APD-6'],
        'policies': ['POL-6', 'POL-33', 'POL-41'],
    },
    '314.4.c.5: Implement multi-factor authentication for any individual accessing any information system': {
        'risks': ['Broken or weak authentication', 'Brute force attack', 'Credential Stuffing'],
        'controls': ['IAM-1', 'IAM-2', 'IAM-6', 'IAM-8'],
        'policies': ['POL-1', 'POL-4'],
    },
    '314.4.c.6: Secure disposal and retention': {
        'risks': ['Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices', 'Data loss / corruption'],
        'controls': ['DCH-3', 'DCH-4', 'DCH-5', 'AST-4'],
        'policies': ['POL-17', 'POL-16'],
    },
    '314.4.c.7: Adopt procedures for change management': {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'CHM-3', 'CHM-4'],
        'policies': ['POL-11', 'POL-15'],
    },
    '314.4.c.8: Implement policies, procedures, and controls designed to monitor and log the activity of authorized users and detect unauthorized access or use of, or tampering with, customer information by such users': {
        'risks': ['Insufficient logging', 'Insufficient monitoring & alerting', 'Insufficient usage and other logging'],
        'controls': ['ALM-1', 'ALM-2', 'ALM-3', 'ALM-4', 'ALM-5'],
        'policies': ['POL-22', 'POL-21'],
    },
    "314.4.d.1: Regularly test or otherwise monitor the effectiveness of the safeguards' key controls, systems, and procedures, including those to detect actual and attempted attacks on, or intrusions into, information systems": {
        'risks': ['Unmitigated vulnerabilities', 'Inability to maintain situational awareness'],
        'controls': ['CVM-1', 'CVM-2', 'CVM-3', 'CVM-6', 'CVM-7'],
        'policies': ['POL-35', 'POL-36'],
    },
    '314.4.d.2: For information systems, the monitoring and testing shall include continuous monitoring or periodic penetration testing and vulnerability assessments': {
        'risks': ['Unmitigated vulnerabilities', 'Zero-Day Exploit', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-4', 'CVM-5', 'CVM-6', 'CVM-7', 'ALM-5'],
        'policies': ['POL-35', 'POL-26'],
    },
    '314.4.e.1: Providing your personnel with security awareness training that is updated as necessary to reflect risks identified by the risk assessment;': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce', 'Phishing'],
        'controls': ['HRM-8', 'HRM-1'],
        'policies': ['POL-39', 'POL-27'],
    },
    '314.4.e.2: Utilizing qualified information security personnel employed by you or an affiliate or service provider sufficient to manage your information security risks and to perform or oversee the information security program;': {
        'risks': ['Cybersecurity skills gap in managing the cloud infrastructure', 'Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'HRM-12', 'GOV-4'],
        'policies': ['POL-27', 'POL-21'],
    },
    '314.4.e.3: Providing information security personnel with security updates and training sufficient to address relevant security risks': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'HRM-11', 'HRM-12'],
        'policies': ['POL-39', 'POL-27'],
    },
    '314.4.e.4: Verifying that key information security personnel take steps to maintain current knowledge of changing information security threats and countermeasures': {
        'risks': ['Lack of a security-minded workforce', 'Cybersecurity skills gap in managing the cloud infrastructure'],
        'controls': ['HRM-8', 'HRM-12', 'GOV-4'],
        'policies': ['POL-39', 'POL-27'],
    },
    '314.4.f.1: Taking reasonable steps to select and retain service providers that are capable of maintaining appropriate safeguards for the customer information at issue': {
        'risks': ['Exposure to third party vendors', 'Lack of oversight of third-party controls', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '314.4.f.2: Requiring your service providers by contract to implement and maintain such safeguards; and': {
        'risks': ['Inadequate third-party practices', 'Third-party cybersecurity exposure', 'Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-1', 'TPM-2', 'TPM-4'],
        'policies': ['POL-34', 'POL-21'],
    },
    '314.4.f.3: Periodically assessing your service providers based on the risk they present and the continued adequacy of their safeguards': {
        'risks': ['Lack of oversight of third-party controls', 'Reliance on the third-party', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-3', 'TPM-4'],
        'policies': ['POL-34', 'POL-36'],
    },
    '314.4.g.1: Evaluate and adjust your information security program in light of the results of the testing and monitoring': {
        'risks': ['Inadequate internal practices', 'Ineffective remediation actions'],
        'controls': ['GOV-5', 'GOV-6', 'RSM-4', 'CVM-7'],
        'policies': ['POL-21', 'POL-37', 'POL-38'],
    },
    '314.4.h.1: The goals of the incident response plan': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-1', 'IRM-2'],
        'policies': ['POL-20'],
    },
    '314.4.h.2: The internal processes for responding to a security event': {
        'risks': ['Improper response to incidents', 'Inability to investigate / prosecute incidents'],
        'controls': ['IRM-1', 'IRM-2', 'IRM-3', 'IRM-4'],
        'policies': ['POL-20'],
    },
    '314.4.h.3: Definition of clear roles, responsibilities, and levels of decision-making authority': {
        'risks': ['Lack of roles & responsibilities', 'Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-5', 'HRM-5'],
        'policies': ['POL-20', 'POL-21'],
    },
    '314.4.h.4: External and internal communications and information sharing': {
        'risks': ['Improper response to incidents', 'Inability to investigate / prosecute incidents'],
        'controls': ['IRM-1', 'IRM-5', 'IRM-6'],
        'policies': ['POL-20', 'POL-46'],
    },
    '314.4.h.5: Identification of requirements for the remediation of any identified weaknesses in information systems and associated controls': {
        'risks': ['Unmitigated vulnerabilities', 'Ineffective remediation actions'],
        'controls': ['IRM-3', 'IRM-4', 'CVM-5', 'CVM-6'],
        'policies': ['POL-20', 'POL-38'],
    },
    '314.4.h.6: Documentation and reporting regarding security events and related incident response activities;': {
        'risks': ['Insufficient logging', 'Inability to investigate / prosecute incidents'],
        'controls': ['IRM-2', 'IRM-6', 'ALM-3'],
        'policies': ['POL-20', 'POL-22'],
    },
    '314.4.h.7: The evaluation and revision as necessary of the incident response plan following a security event.': {
        'risks': ['Improper response to incidents', 'Ineffective remediation actions'],
        'controls': ['IRM-1', 'IRM-5', 'IRM-6'],
        'policies': ['POL-20', 'POL-38'],
    },
    '314.4.i.1: The overall status of the information security program': {
        'risks': ['Lack of oversight of internal controls', 'Inadequate internal practices'],
        'controls': ['GOV-3', 'GOV-9', 'GOV-10', 'GOV-11'],
        'policies': ['POL-21', 'POL-37'],
    },
    '314.4.i.2: Material matters related to the information security program': {
        'risks': ['Fines and judgements', 'Lack of oversight of internal controls'],
        'controls': ['GOV-3', 'GOV-9', 'GOV-10', 'GOV-12'],
        'policies': ['POL-21', 'POL-37'],
    },
}
