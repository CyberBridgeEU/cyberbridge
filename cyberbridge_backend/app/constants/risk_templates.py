# risk_templates.py
# Risk templates organized by category
# 104 unique risks with sequential codes RSK-1 through RSK-104

RISK_TEMPLATE_CATEGORIES = [
    {
        "id": "endpoint_device",
        "name": "Endpoint & Device Risks",
        "description": "Risks related to laptops, mobile devices, endpoints, and BYOD",
        "risk_count": 9
    },
    {
        "id": "cloud",
        "name": "Cloud Security Risks",
        "description": "Risks specific to cloud computing environments and services",
        "risk_count": 5
    },
    {
        "id": "app_api",
        "name": "Application & API Risks",
        "description": "Application and API development security risks",
        "risk_count": 20
    },
    {
        "id": "network",
        "name": "Network Security Risks",
        "description": "Risks related to network infrastructure and communications",
        "risk_count": 3
    },
    {
        "id": "data",
        "name": "Data Security Risks",
        "description": "Risks related to data protection, privacy, and breaches",
        "risk_count": 7
    },
    {
        "id": "identity_access",
        "name": "Identity & Access Risks",
        "description": "Risks related to authentication, authorization, and identity management",
        "risk_count": 10
    },
    {
        "id": "malware",
        "name": "Malware & Attack Risks",
        "description": "Risks from malicious software and cyber attacks",
        "risk_count": 5
    },
    {
        "id": "insider",
        "name": "Insider & Human Risks",
        "description": "Risks from employees, social engineering, and human factors",
        "risk_count": 8
    },
    {
        "id": "compliance",
        "name": "Compliance & Governance Risks",
        "description": "Risks related to compliance, policies, and governance",
        "risk_count": 11
    },
    {
        "id": "third_party",
        "name": "Third Party & Supply Chain Risks",
        "description": "Risks from vendors, contractors, and supply chain",
        "risk_count": 6
    },
    {
        "id": "physical",
        "name": "Physical Security Risks",
        "description": "Risks related to physical security and facilities",
        "risk_count": 3
    },
    {
        "id": "operational",
        "name": "Operational & Business Risks",
        "description": "Risks affecting business operations and continuity",
        "risk_count": 17
    },
]

# Endpoint & Device Risks (9 risks: RSK-1 to RSK-9)
ENDPOINT_DEVICE_RISKS = [
    {
        "risk_code": "RSK-1",
        "risk_category_name": "Misconfiguration of employee endpoints",
        "risk_category_description": "Risk of employee data theft, company sensitvie data theft, device infection and account takeover due to misconfigured employee device  / endpoint such as laptop",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-2",
        "risk_category_name": "Employee owned devices (BYOD) exploitation",
        "risk_category_description": "Exploitation of vulnerabilities on employee owned devices due to lack of proper security  controls and configurations",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-3",
        "risk_category_name": "Misappropriation & Misuse of devices",
        "risk_category_description": "Risk of disgruntled employee using company\'s laptop or other device for unacceptable use such as stealing company data or selling trade secrets",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-4",
        "risk_category_name": "Data theft from Laptops and other employee owned devices",
        "risk_category_description": "Confidential company data can be stolen from employee owned laptops and other devices in public and insecure places",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-5",
        "risk_category_name": "Disposed asset (laptops) exploitation due to lack of proper retention and disposal polices",
        "risk_category_description": "Risk of confidential information being leaked to unauthorized users of a recycled laptop or other assets where the information is not disposed off properly",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-6",
        "risk_category_name": "Employee laptop / mobile / desktop/ other device theft or loss for laptops",
        "risk_category_description": "Risk of sensitive data being stolen as a result of theft of laptops or other devices issued to employees in public places such as airports and while traveling for business",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-7",
        "risk_category_name": "Damaged files on employee devices",
        "risk_category_description": "Risk of damaged files being exploited by a malicious user to install malicious code or steal sensitive information",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-8",
        "risk_category_name": "Shadow IT",
        "risk_category_description": "Risk of employees installing there own unapproved software creating a shadow IT environment due to a weak BYOD policy",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-9",
        "risk_category_name": "IoT attack",
        "risk_category_description": "Risk of smart devices being hacked to perform a more elaborate attack",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Cloud Security Risks (5 risks: RSK-10 to RSK-14)
CLOUD_RISKS = [
    {
        "risk_code": "RSK-10",
        "risk_category_name": "Cloud misconfiguration",
        "risk_category_description": "Lack of baseline configuration with built in security best practices as advised by the cloud provider leaves security gaps and holes in the configurations. For example open network ports, absent firewall rules, improper key management etc.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-11",
        "risk_category_name": "Denial Of Service (DoS)",
        "risk_category_description": "Although handled by your cloud provider, the risk of DoS is real and could lead to expensive system outages for your business",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-12",
        "risk_category_name": "Accidental loss of data from data storage on cloud",
        "risk_category_description": "Due to improper handling, incorrect commands, lack of training administrators or other users of a production database can accidentally delete confidential and application data from a hosted database",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-13",
        "risk_category_name": "Cybersecurity skills gap in managing the cloud infrastructure",
        "risk_category_description": "Risk of prolonged outages and inability to respond to incidents due to improper training of cybersecurity staff",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-14",
        "risk_category_name": "Availability & Disaster recovery",
        "risk_category_description": "Risk of system outage due to a disaster event for the cloud provider",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Application & API Risks (20 risks: RSK-15 to RSK-34)
APP_API_RISKS = [
    {
        "risk_code": "RSK-15",
        "risk_category_name": "Loss of integrity through unauthorized changes",
        "risk_category_description": "Unauthorized changes corrupt the integrity of the system / application / service.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-16",
        "risk_category_name": "Information loss / corruption or system compromise due to non-technical attack",
        "risk_category_description": "Social engineering, sabotage or other non-technical attack compromises data, systems, applications or services.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-17",
        "risk_category_name": "System compromise",
        "risk_category_description": "System / application / service is compromised affects its confidentiality, integrity, availability and/or safety.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-18",
        "risk_category_name": "Broken or weak authentication in the application",
        "risk_category_description": "Risk of data breaches and unauthorized access because of lack of your application not using strong password policies or not supporting advanced methods such as MFA",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-19",
        "risk_category_name": "Broken or weak access control in the application",
        "risk_category_description": "Improper access control across different roles being used for your API or application",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-20",
        "risk_category_name": "Weak cryptography & encryption support in the application",
        "risk_category_description": "Risk of data exposure due to lack of encryption at rest and encryption in transit",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-21",
        "risk_category_name": "Cross-Site Scripting XSS",
        "risk_category_description": "Risk of credentials theft, sensitive data exfiltration due to injection of malicious script on your website",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-22",
        "risk_category_name": "Input Validation Attack",
        "risk_category_description": "Risk of data exposure or vulnerability exploitation by entering specially crafted inputs into the application",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-23",
        "risk_category_name": "SQL Injection Attack",
        "risk_category_description": "Risk of data exposure directly from the database due to improper input validation",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-24",
        "risk_category_name": "Security misconfiguration of APIs / Applications",
        "risk_category_description": "Risk of bad configuration leaving exploitable vulnerabilities open in the software",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-25",
        "risk_category_name": "Lack of design reviews & security testing",
        "risk_category_description": "Risk of undetected vulnerabilities reaching live and production environment due to lack of security design review and vulnerability tests",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-26",
        "risk_category_name": "Source code disclosure",
        "risk_category_description": "Accidental source code, versions, libraries  and other sensitive information revealed in errors, logs or other places",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-27",
        "risk_category_name": "Insufficient logging",
        "risk_category_description": "Risk of not being able to determine the root cause of an incident due to lack of logs",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-28",
        "risk_category_name": "Session Hijacking",
        "risk_category_description": "Risk of session being and enter the server and access its information without having to hack a registered account",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-29",
        "risk_category_name": "Application access token mis-use",
        "risk_category_description": "Risk of valid access tokens being granted to OAUTH applications",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-30",
        "risk_category_name": "Buffer Overflow Attack",
        "risk_category_description": "Risk of application users being able to pass malformed inputs and overwrite the memory of the application server and trigger a response exposing sensitive information about the environment, infrastructure or databases.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-31",
        "risk_category_name": "Server Side Request Forgery Attack",
        "risk_category_description": "Risk of leaking of sensitive information to external applications via a internal server controlled by a malicious actor",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-32",
        "risk_category_name": "URL Interpretation Attack / Semantic URL attack",
        "risk_category_description": "Risk of exposing sensitive information when a user modifies application or website URLs",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-33",
        "risk_category_name": "Insufficient usage and other logging",
        "risk_category_description": "Risk of not being able to determine the root cause of an incident due to lack of logs",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-34",
        "risk_category_name": "Insufficient monitoring & alerting",
        "risk_category_description": "Risk of not being able to act in time before the start of the attack or during the attack",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Network Security Risks (3 risks: RSK-35 to RSK-37)
NETWORK_RISKS = [
    {
        "risk_code": "RSK-35",
        "risk_category_name": "DNS Spoofing",
        "risk_category_description": "Risk of data theft and malware distribution when a hacker mimics  the DNS of trustworthy websites and redirect traffic to untrustworthy websites",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-36",
        "risk_category_name": "Man in the middle (MitM) attack for Network",
        "risk_category_description": "Risk of malicious actor eavesdropping to sniff network packets and modify them or steal data or start a ARP poisoning attack",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-37",
        "risk_category_name": "Software supply chain malware attack",
        "risk_category_description": "Risk of infected patches or software spreading widely across the cloud infrastructure as the software moves through the supply chain",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Data Security Risks (7 risks: RSK-38 to RSK-44)
DATA_RISKS = [
    {
        "risk_code": "RSK-38",
        "risk_category_name": "Phishing",
        "risk_category_description": "Risk of data theft, account takeover, fraudulent transactions on behalf of your company employees",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-39",
        "risk_category_name": "Ransomware",
        "risk_category_description": "Data loss, theft or simply financial loss due to paying ransom to free up the locked data",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-40",
        "risk_category_name": "Accidental disclosure of sensitive customer data during support or other operations",
        "risk_category_description": "Lack of training and incorrect privileges can allow support personnel to access sensitive data",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-41",
        "risk_category_name": "Data loss / corruption",
        "risk_category_description": "There is a failure to maintain the confidentiality of the data (compromise) or data is corrupted (loss).",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-42",
        "risk_category_name": "Cross Site Request Forgery (CSRF)",
        "risk_category_description": "Risk of a malicious user hijacking a user account to get access to sensitive data or to do fradulent transactions",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-43",
        "risk_category_name": "Data loss",
        "risk_category_description": "Absence of  regular backups can lead to catastrophic data loss due to a system failure, natural disaster or a human error",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-44",
        "risk_category_name": "Data breach",
        "risk_category_description": "Open ports, unrestricted protocols can lead to malicious access to cloud instances and databases leading to data theft, ransomware etc",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Identity & Access Risks (10 risks: RSK-45 to RSK-54)
IDENTITY_ACCESS_RISKS = [
    {
        "risk_code": "RSK-45",
        "risk_category_name": "Brute force attack",
        "risk_category_description": "Risk of malicious user getting access to passwords by trial and error method",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-46",
        "risk_category_name": "Credential dumping attack for Operating Systems",
        "risk_category_description": "Risk of credentials, logins and passwords being extracted from operating systems using malicious software and then reusing them for unauthorized access",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-47",
        "risk_category_name": "Typo squatting and cyber squatting",
        "risk_category_description": "Risk of employees sharing personal details such as login credentials to attackers when attackers mimic your company\'s domain name and redirect employees to their fake websites",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-48",
        "risk_category_name": "Improper assignment of privileged functions",
        "risk_category_description": "There is a failure to implement least privileges.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-49",
        "risk_category_name": "Privilege escalation",
        "risk_category_description": "Access to privileged functions is inadequate or cannot be controlled.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-50",
        "risk_category_name": "Unauthorized access",
        "risk_category_description": "Access is granted to unauthorized individuals, groups or services.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-51",
        "risk_category_name": "Expense associated with managing a loss event",
        "risk_category_description": "There are financial repercussions from responding to an incident or loss.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-52",
        "risk_category_name": "Credential Stuffing",
        "risk_category_description": "Risk of hackers using hacked and exposed passwords from data breaches into your application or website",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-53",
        "risk_category_name": "Broken or weak authentication",
        "risk_category_description": "Risk of account hijacking or exploitation due to weak passwords and authentication on information systems. Lack of MFA or a strong password policy may increase this risk drastically",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-54",
        "risk_category_name": "Unauthorized Access",
        "risk_category_description": "Risk of unauthorized person accessing or elevating own privileges due to a lack of strong access control and identity management practices and policies",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Malware & Attack Risks (5 risks: RSK-55 to RSK-59)
MALWARE_RISKS = [
    {
        "risk_code": "RSK-55",
        "risk_category_name": "Malware",
        "risk_category_description": "Risk of data loss, large scale outages and equipment failure due to malware being introduced and distributed via emails, fake internet ads or infected applications.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-56",
        "risk_category_name": "Unpatched vulnerability exploitation",
        "risk_category_description": "Risk of known unpatched vulnerabilities being exploited by hackers",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-57",
        "risk_category_name": "Information loss / corruption or system compromise due to technical attack",
        "risk_category_description": "Malware, phishing, hacking or other technical attack compromise data, systems, applications or services.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-58",
        "risk_category_name": "Zero-Day Exploit",
        "risk_category_description": "Risk which  third party software upgrade or an operating system patching or an announcement of a vulnerability found  can allow hackers to exploit a vulnerability before it can be mitigated",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-59",
        "risk_category_name": "Advanced persistent threats (APT)",
        "risk_category_description": "Risk of an unauthorized person gaining access to cloud information systems for long periods of time.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Insider & Human Risks (8 risks: RSK-60 to RSK-67)
INSIDER_RISKS = [
    {
        "risk_code": "RSK-60",
        "risk_category_name": "Insider Threat",
        "risk_category_description": "Risk of disgruntled employees accessing information systems or company\'s physical premises with a malicious intent of causing harm and damage to employees or information systems",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-61",
        "risk_category_name": "Lack of cybersecurity awareness",
        "risk_category_description": "Risk of employees becoming victims of social engineering, phishing or malware due to lack of proper awareness",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-62",
        "risk_category_name": "Email Impersonation attack",
        "risk_category_description": "Risk of employees being duped into sharing confidential information to a hacker. Related to social engineering and phishing a fake person can impersonate as your company\'s CEO or other plausible person and ask for genuine information",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-63",
        "risk_category_name": "Directory Harvest Attacks due to weak email server configuration for Email",
        "risk_category_description": "Risk of email spam due to emails being sent to employees based on a directory harvest attack",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-64",
        "risk_category_name": "Inability to maintain situational awareness",
        "risk_category_description": "There is an inability to detect incidents.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-65",
        "risk_category_name": "Lack of a security-minded workforce",
        "risk_category_description": "The workforce lacks user-level understanding about security & privacy principles.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-66",
        "risk_category_name": "Smartphones are being used in surveillance attacks",
        "risk_category_description": "Risk of employee smartphones being tracked for social engineering and phishing",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-67",
        "risk_category_name": "DeepFakes",
        "risk_category_description": "Risk of deepfakes being used to phish information from employees",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Compliance & Governance Risks (11 risks: RSK-68 to RSK-78)
COMPLIANCE_RISKS = [
    {
        "risk_code": "RSK-68",
        "risk_category_name": "Outdated policies for Process Management",
        "risk_category_description": "Risk of an org not being able to respond appropriately during an incident or not having up to date security controls due to improper policy guidance",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-69",
        "risk_category_name": "Fines and judgements",
        "risk_category_description": "Legal and/or financial damages result from statutory / regulatory / contractual non-compliance.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-70",
        "risk_category_name": "Inability to support business processes",
        "risk_category_description": "Implemented security /privacy practices are insufficient to support the organization\'s secure technologies & processes requirements.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-71",
        "risk_category_name": "Incorrect controls scoping",
        "risk_category_description": "There is incorrect or inadequate controls scoping, which leads to a potential gap or lapse in security / privacy controls coverage.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-72",
        "risk_category_name": "Lack of roles & responsibilities",
        "risk_category_description": "Documented security / privacy roles & responsibilities do not exist or are inadequate.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-73",
        "risk_category_name": "Inadequate internal practices",
        "risk_category_description": "Internal practices do not exist or are inadequate. Procedures fail to meet \"reasonable practices\"\" expected by industry standards.\"",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-74",
        "risk_category_name": "Inadequate third-party practices",
        "risk_category_description": "Third-party practices do not exist or are inadequate. Procedures fail to meet \"reasonable practices\"\" expected by industry standards.\"",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-75",
        "risk_category_name": "Lack of oversight of internal controls",
        "risk_category_description": "There is a lack of due diligence / due care in overseeing the organization\'s internal security / privacy controls.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-76",
        "risk_category_name": "Lack of oversight of third-party controls",
        "risk_category_description": "There is a lack of due diligence / due care in overseeing security / privacy controls operated by third-party service providers.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-77",
        "risk_category_name": "Illegal content or abusive action",
        "risk_category_description": "There is abusive content / harmful speech / threats of violence / illegal content that negatively affect business operations.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-78",
        "risk_category_name": "Third-party compliance / legal exposure",
        "risk_category_description": "The inability to maintain compliance due to third-party non-compliance, criminal acts, or other relevant legal action(s).",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Third Party & Supply Chain Risks (6 risks: RSK-79 to RSK-84)
THIRD_PARTY_RISKS = [
    {
        "risk_code": "RSK-79",
        "risk_category_name": "Exposure to third party vendors",
        "risk_category_description": "Risk of confidential data loss, theft and data breaches due to risks arising from a third party vendor or independent contractors",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-80",
        "risk_category_name": "Ex-Employees / disgruntled employees",
        "risk_category_description": "Risk of data theft, unauthorized confidential information disclosure caused when an ex-employee still has access to information systems",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-81",
        "risk_category_name": "Third-party cybersecurity exposure",
        "risk_category_description": "Loss of Confidentiality, Integrity, Availability and/or Safety (CIAS) from third-party cybersecurity practices, vulnerabilities and/or incidents that affects the supply chain through impacted products and/or services.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-82",
        "risk_category_name": "Third-party physical security exposure",
        "risk_category_description": "Loss of Confidentiality, Integrity, Availability and/or Safety (CIAS) from physical security exposure of third-party structures, facilities and/or other physical assets that affects the supply chain through impacted products and/or services.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-83",
        "risk_category_name": "Third-party supply chain relationships, visibility and controls",
        "risk_category_description": "Loss of Confidentiality, Integrity, Availability and/or Safety (CIAS) from \"downstream\" third-party relationships, visibility and controls that affect the supply chain through impacted products and/or services.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-84",
        "risk_category_name": "Reliance on the third-party",
        "risk_category_description": "The inability to continue business operations, due to the reliance on the third-party product and/or service.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Physical Security Risks (3 risks: RSK-85 to RSK-87)
PHYSICAL_RISKS = [
    {
        "risk_code": "RSK-85",
        "risk_category_name": "Power Outages for Physical facilities(Bldg., Equip...)",
        "risk_category_description": "Risk of unauthorized access during a power outage or when other security systems are not available",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-86",
        "risk_category_name": "Natural Disasters for Physical facilities(Bldg., Equip...)",
        "risk_category_description": "Risk of outages and other damanges due to natural disasters",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-87",
        "risk_category_name": "Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)",
        "risk_category_description": "Risk of outages and loss due to accidents, fire and flooding",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# Operational & Business Risks (17 risks: RSK-88 to RSK-104)
OPERATIONAL_RISKS = [
    {
        "risk_code": "RSK-88",
        "risk_category_name": "Defacement of defacement of digital properties such as websites",
        "risk_category_description": "Risk of reputation loss and potential business loss when a hacker hacks digital properties and replaces the content on those properties",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-89",
        "risk_category_name": "Denial of Service (DoS) Attack",
        "risk_category_description": "Risk of Denial of service or distributed denial of service causing outages, loss in reputation and business",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-90",
        "risk_category_name": "Inability to maintain individual accountability",
        "risk_category_description": "There is a failure to maintain asset ownership and it is not possible to have non-repudiation of actions or inactions.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-91",
        "risk_category_name": "Lost, damaged or stolen asset(s)",
        "risk_category_description": "Asset(s) is/are lost, damaged or stolen.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-92",
        "risk_category_name": "Business interruption",
        "risk_category_description": "There is increased latency or a service outage that negatively impacts business operations.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-93",
        "risk_category_name": "Reduction in productivity",
        "risk_category_description": "User productivity is negatively affected by the incident.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-94",
        "risk_category_name": "Loss of revenue",
        "risk_category_description": "A financial loss occurs from either a loss of clients or an inability to generate future revenue.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-95",
        "risk_category_name": "Cancelled contract",
        "risk_category_description": "A contract is cancelled due to a violation of a contract clause.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-96",
        "risk_category_name": "Diminished competitive advantage",
        "risk_category_description": "The competitive advantage of the organization is jeopardized.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-97",
        "risk_category_name": "Diminished reputation",
        "risk_category_description": "Negative publicity tarnishes the organization\'s reputation.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-98",
        "risk_category_name": "Unmitigated vulnerabilities",
        "risk_category_description": "Umitigated technical vulnerabilities exist without compensating controls or other mitigation actions.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-99",
        "risk_category_name": "Inability to investigate / prosecute incidents",
        "risk_category_description": "Response actions either corrupt evidence or impede the ability to prosecute incidents.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-100",
        "risk_category_name": "Improper response to incidents",
        "risk_category_description": "Response actions fail to act appropriately in a timely manner to properly address the incident.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-101",
        "risk_category_name": "Ineffective remediation actions",
        "risk_category_description": "There is no oversight to ensure remediation actions are correct and/or effective.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-102",
        "risk_category_name": "Emergent properties and/or unintended consequences",
        "risk_category_description": "Emergent properties and/or unintended consequences from Artificial Intelligence & Autonomous Technologies (AAT).",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-103",
        "risk_category_name": "Use of product / service",
        "risk_category_description": "The misuse of the product / service in a manner that it was not designed or how it was approved for use.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
    {
        "risk_code": "RSK-104",
        "risk_category_name": "Unauthorized changes",
        "risk_category_description": "Risk of unauthorized changes to a system causing misconfiguration or security holes in the system especially as the business and the environment changes.",
        "risk_potential_impact": "",
        "risk_control": ""
    },
]

# All risks combined (for backward compatibility)
ALL_RISKS = (
    ENDPOINT_DEVICE_RISKS +
    CLOUD_RISKS +
    APP_API_RISKS +
    NETWORK_RISKS +
    DATA_RISKS +
    IDENTITY_ACCESS_RISKS +
    MALWARE_RISKS +
    INSIDER_RISKS +
    COMPLIANCE_RISKS +
    THIRD_PARTY_RISKS +
    PHYSICAL_RISKS +
    OPERATIONAL_RISKS
)

# Backward compatibility alias
COMMON_RISKS = ALL_RISKS

# Risk templates dictionary
RISK_TEMPLATES = {
    "endpoint_device": ENDPOINT_DEVICE_RISKS,
    "cloud": CLOUD_RISKS,
    "app_api": APP_API_RISKS,
    "network": NETWORK_RISKS,
    "data": DATA_RISKS,
    "identity_access": IDENTITY_ACCESS_RISKS,
    "malware": MALWARE_RISKS,
    "insider": INSIDER_RISKS,
    "compliance": COMPLIANCE_RISKS,
    "third_party": THIRD_PARTY_RISKS,
    "physical": PHYSICAL_RISKS,
    "operational": OPERATIONAL_RISKS,
    "all": ALL_RISKS,
    "common": COMMON_RISKS
}


# Helper functions
def get_risks_by_category(category_id: str) -> list:
    """Get risks by category ID"""
    return RISK_TEMPLATES.get(category_id, [])


def get_all_categories() -> list:
    """Get all risk categories"""
    return RISK_TEMPLATE_CATEGORIES


def get_category_by_id(category_id: str) -> dict:
    """Get a specific category by ID"""
    for cat in RISK_TEMPLATE_CATEGORIES:
        if cat["id"] == category_id:
            return cat
    return None
