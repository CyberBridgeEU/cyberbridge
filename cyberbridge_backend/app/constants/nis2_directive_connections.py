# Auto-generated NIS2 Directive connections mapping
# Maps each NIS2 Directive objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code in control_templates (Baseline Controls)
# - policies: matched by POL code in policy_templates

NIS2_DIRECTIVE_CONNECTIONS = {
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 1: Policy on the security of network and information systems
    #   (8 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '1.1.1: For the purpose of Article 21(2), point (a) of Directive (EU) 2022/2555, the policy on the security of network and information systems shall': {
        'risks': ['Outdated policies for Process Management', 'Lack of roles & responsibilities'],
        'controls': ['GOV-5', 'GOV-1', 'HRM-11'],
        'policies': ['POL-21', 'POL-30'],
    },
    '1.1.2: The network and information system security policy shall be reviewed and, where appropriate, updated by management bodies at least annually and when significant incidents or significant changes to operations or risks occur. The result of the reviews shall be documented.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-5', 'GOV-11'],
        'policies': ['POL-21'],
    },
    "1.2.1: As part of their policy on the security of network and information systems referred to in point 1.1, the relevant entities shall lay down responsibilities and authorities for network and information system security and assign them to roles, allocate them according to the relevant entities' needs, and communicate them to the management bodies.": {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-11', 'GOV-4'],
        'policies': ['POL-21'],
    },
    '1.2.2: The relevant entities shall require all personnel and third parties to apply network and information system security in accordance with the established network and information security policy, topic-specific policies and procedures of the relevant entities.': {
        'risks': ['Lack of a security-minded workforce', 'Inadequate third-party practices'],
        'controls': ['GOV-1', 'HRM-8'],
        'policies': ['POL-21', 'POL-27'],
    },
    '1.2.3: At least one person shall report directly to the management bodies on matters of network and information system security.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-4', 'HRM-11'],
        'policies': ['POL-21'],
    },
    '1.2.4: Depending on the size of the relevant entities, network and information system security shall be covered by dedicated roles or duties carried out in addition to existing roles.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-4', 'HRM-11'],
        'policies': ['POL-21'],
    },
    '1.2.5: Conflicting duties and conflicting areas of responsibility shall be segregated, where applicable.': {
        'risks': ['Improper assignment of privileged functions'],
        'controls': ['HRM-11', 'IAM-7'],
        'policies': ['POL-21', 'POL-4'],
    },
    '1.2.6: Roles, responsibilities and authorities shall be reviewed and, where appropriate, updated by management bodies at planned intervals and when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Lack of roles & responsibilities', 'Outdated policies for Process Management'],
        'controls': ['HRM-11', 'GOV-11'],
        'policies': ['POL-21'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 2: Risk management
    #   (11 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '2.1.1: For the purpose of Article 21(2), point (a) of Directive (EU) 2022/2555, the relevant entities shall establish and maintain an appropriate risk management framework to identify and address the risks posed to the security of network and information systems. The relevant entities shall perform and document risk assessments and, based on the results, establish, implement and monitor a risk treatment plan. Risk assessment results and residual risks shall be accepted by management bodies or, where applicable, by persons who are accountable and have the authority to manage risks, provided that the relevant entities ensure adequate reporting to the management bodies.': {
        'risks': ['Incorrect controls scoping', 'Lack of oversight of internal controls'],
        'controls': ['GOV-6', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    "2.1.2: For the purpose of point 2.1.1, the relevant entities shall establish procedures for identification, analysis, assessment and treatment of risks ('cybersecurity risk management process'). The cybersecurity risk management process shall be an integral part of the relevant entities' overall risk management process, where applicable. As part of the cybersecurity risk management process, the relevant entities shall:": {
        'risks': ['Incorrect controls scoping', 'Inability to support business processes'],
        'controls': ['GOV-6', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    '2.1.3: When identifying and prioritising appropriate risk treatment options and measures, the relevant entities shall take into account the risk assessment results, the results of the procedure to assess the effectiveness of cybersecurity risk-management measures, the cost of implementation in relation to the expected benefit, the asset classification referred to in point 12.1, and the business impact analysis referred to in point 4.1.3.': {
        'risks': ['Incorrect controls scoping'],
        'controls': ['GOV-6', 'RSM-3'],
        'policies': ['POL-30'],
    },
    '2.1.4: The relevant entities shall review and, where appropriate, update the risk assessment results and the risk treatment plan at planned intervals and at least annually, and when significant changes to operations or risks or significant incidents occur.': {
        'risks': ['Outdated policies for Process Management', 'Lack of oversight of internal controls'],
        'controls': ['GOV-6', 'GOV-3'],
        'policies': ['POL-30'],
    },
    '2.2.1: The relevant entities shall regularly review the compliance with their policies on network and information system security, topic-specific policies, rules, and standards. The management bodies shall be informed of the status of network and information security on the basis of the compliance reviews by means of regular reporting.': {
        'risks': ['Fines and judgements', 'Inadequate internal practices'],
        'controls': ['GOV-12', 'GOV-3'],
        'policies': ['POL-30', 'POL-36'],
    },
    "2.2.2: The relevant entities shall put in place an effective compliance reporting system which shall be appropriate to their structures, operating environments and threat landscapes. The compliance reporting system shall be capable to provide to the management bodies an informed view of the current state of the relevant entities' management of risks.": {
        'risks': ['Fines and judgements', 'Inability to support business processes'],
        'controls': ['GOV-12', 'GOV-3'],
        'policies': ['POL-30', 'POL-36'],
    },
    '2.2.3: The relevant entities shall perform the compliance monitoring at planned intervals and when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    '2.3.1: The relevant entities shall review independently their approach to managing network and information system security and its implementation including people, processes and technologies.': {
        'risks': ['Lack of oversight of internal controls', 'Inadequate internal practices'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    '2.3.2: The relevant entities shall develop and maintain processes to conduct independent reviews which shall be carried out by individuals with appropriate audit competence. Where the independent review is conducted by staff members of the relevant entity, the persons conducting the reviews shall not be in the line of authority of the personnel of the area under review. If the size of the relevant entities does not allow such separation of line of authority, the relevant entities shall put in place alternative measures to guarantee the impartiality of the reviews.': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    "2.3.3: The results of the independent reviews, including the results from the compliance monitoring pursuant to point 2.2 and the monitoring and measurement pursuant to point 7, shall be reported to the management bodies. Corrective actions shall be taken or residual risk accepted according to the relevant entities' risk acceptance criteria.": {
        'risks': ['Lack of oversight of internal controls', 'Fines and judgements'],
        'controls': ['GOV-12', 'GOV-3'],
        'policies': ['POL-30', 'POL-36'],
    },
    '2.3.4: The independent reviews shall take place at planned intervals and when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 3: Incident handling
    #   (22 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '3.1.1: For the purpose of Article 21(2), point (b) of Directive (EU) 2022/2555, the relevant entities shall establish and implement an incident handling policy laying down the roles, responsibilities, and procedures for detecting, analysing, containing or responding to, recovering from, documenting and reporting of incidents in a timely manner.': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '3.1.2: The policy referred to in point 3.1.1 shall be coherent with the business continuity and disaster recovery plan referred to in point 4.1. The policy shall include:': {
        'risks': ['Improper response to incidents', 'Business interruption'],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '3.1.3: The roles, responsibilities and procedures laid down in the policy shall be tested and reviewed and, where appropriate, updated at planned intervals and after significant incidents or significant changes to operations or risks.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '3.2.1: The relevant entities shall lay down procedures and use tools to monitor and log activities on their network and information systems to detect events that could be considered as incidents and respond accordingly to mitigate the impact.': {
        'risks': ['Inability to maintain situational awareness', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-1', 'ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '3.2.2: To the extent feasible, monitoring shall be automated and carried out either continuously or in periodic intervals, subject to business capabilities. The relevant entities shall implement their monitoring activities in a way which minimises false positives and false negatives.': {
        'risks': ['Inability to maintain situational awareness', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22'],
    },
    '3.2.3: Based on the procedures referred to in point 3.2.1, the relevant entities shall maintain, document, and review logs. The relevant entities shall establish a list of assets to be subject to logging based on the results of the risk assessment carried out pursuant to point 2.1. Where appropriate, logs shall include:': {
        'risks': ['Insufficient logging', 'Insufficient usage and other logging'],
        'controls': ['ALM-2', 'ALM-4'],
        'policies': ['POL-22'],
    },
    '3.2.4: The logs shall be regularly reviewed for any unusual or unwanted trends. Where appropriate, the relevant entities shall lay down appropriate values for alarm thresholds. If the laid down values for alarm threshold are exceeded, an alarm shall be triggered, where appropriate, automatically. The relevant entities shall ensure that, in case of an alarm, a qualified and appropriate response is initiated in a timely manner.': {
        'risks': ['Inability to maintain situational awareness', 'Insufficient monitoring & alerting'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22'],
    },
    '3.2.5: The relevant entities shall maintain and back up logs for a predefined period and shall protect them from unauthorised access or changes.': {
        'risks': ['Insufficient logging', 'Inability to investigate / prosecute incidents'],
        'controls': ['ALM-2', 'ALM-4'],
        'policies': ['POL-22'],
    },
    '3.2.6: To the extent feasible, the relevant entities shall ensure that all systems have synchronised time sources to be able to correlate logs between systems for event assessment. The relevant entities shall establish and keep a list of all assets that are being logged and ensure that monitoring and logging systems are redundant. The availability of the monitoring and logging systems shall be monitored independent of the systems they are monitoring.': {
        'risks': ['Insufficient logging', 'Inability to maintain situational awareness'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '3.2.7: The procedures as well as the list of assets that are being logged shall be reviewed and, where appropriate, updated at regular intervals and after significant incidents.': {
        'risks': ['Insufficient logging'],
        'controls': ['ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    '3.3.1: The relevant entities shall put in place a simple mechanism allowing their employees, suppliers, and customers to report suspicious events.': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-4', 'IRM-5'],
        'policies': ['POL-20'],
    },
    '3.3.2: The relevant entities shall, where appropriate, communicate the event reporting mechanism to their suppliers and customers, and shall regularly train their employees how to use the mechanism.': {
        'risks': ['Lack of cybersecurity awareness', 'Improper response to incidents'],
        'controls': ['IRM-4', 'IRM-5', 'HRM-8'],
        'policies': ['POL-20'],
    },
    '3.4.1: The relevant entities shall assess suspicious events to determine whether they constitute incidents and, if so, determine their nature and severity.': {
        'risks': ['Inability to maintain situational awareness', 'Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },
    '3.4.2: For the purpose of point 3.4.1, the relevant entities shall act in the following manner:': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },
    '3.5.1: The relevant entities shall respond to incidents in accordance with documented procedures and in a timely manner.': {
        'risks': ['Improper response to incidents', 'Ineffective remediation actions'],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '3.5.2: The incident response procedures shall include the following stages:': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '3.5.3: The relevant entities shall establish communication plans and procedures:': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-3', 'CCI-3'],
        'policies': ['POL-20'],
    },
    '3.5.4: The relevant entities shall log incident response activities in accordance with the procedures referred to in point 3.2.1, and record evidence.': {
        'risks': ['Inability to investigate / prosecute incidents', 'Insufficient logging'],
        'controls': ['IRM-4', 'ALM-2'],
        'policies': ['POL-20', 'POL-22'],
    },
    '3.5.5: The relevant entities shall test at planned intervals their incident response procedures.': {
        'risks': ['Improper response to incidents'],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': ['POL-20'],
    },
    '3.6.1: Where appropriate, the relevant entities shall carry out post-incident reviews after recovery from incidents. The post-incident reviews shall identify, where possible, the root cause of the incident and result in documented lessons learned to reduce the occurrence and consequences of future incidents.': {
        'risks': ['Ineffective remediation actions', 'Improper response to incidents'],
        'controls': ['IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    '3.6.2: The relevant entities shall ensure that post-incident reviews contribute to improving their approach to network and information security, to risk treatment measures, and to incident handling, detection and response procedures.': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    '3.6.3: The relevant entities shall review at planned intervals if incidents led to post-incident reviews.': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['IRM-2'],
        'policies': ['POL-20'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 4: Business continuity and crisis management
    #   (14 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '4.1.1: For the purpose of Article 21(2), point (c) of Directive (EU) 2022/2555, the relevant entities shall lay down and maintain a business continuity and disaster recovery plan to apply in the case of incidents.': {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10', 'POL-18'],
    },
    "4.1.2: The relevant entities' operations shall be restored according to the business continuity and disaster recovery plan. The plan shall be based on the results of the risk assessment carried out pursuant to point 2.1 and shall include, where appropriate, the following:": {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10', 'POL-18'],
    },
    '4.1.3: The relevant entities shall carry out a business impact analysis to assess the potential impact of severe disruptions to their business operations and shall, based on the results of the business impact analysis, establish continuity requirements for the network and information systems.': {
        'risks': ['Business interruption', 'Reduction in productivity'],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10'],
    },
    '4.1.4: The business continuity plan and disaster recovery plan shall be tested, reviewed and, where appropriate, updated at planned intervals and following significant incidents or significant changes to operations or risks. The relevant entities shall ensure that the plans incorporate lessons learnt from such tests.': {
        'risks': ['Business interruption', 'Availability & Disaster recovery'],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10', 'POL-18'],
    },
    '4.2.1: The relevant entities shall maintain backup copies of data and provide sufficient available resources, including facilities, network and information systems and staff, to ensure an appropriate level of redundancy.': {
        'risks': ['Data loss', 'Availability & Disaster recovery'],
        'controls': ['DRC-1', 'DRC-4', 'DRC-5'],
        'policies': ['POL-9'],
    },
    '4.2.2: Based on the results of the risk assessment carried out pursuant to point 2.1 and the business continuity plan, the relevant entities shall lay down backup plans which include the following:': {
        'risks': ['Data loss', 'Data loss / corruption'],
        'controls': ['DRC-1', 'DRC-2', 'DRC-5'],
        'policies': ['POL-9'],
    },
    '4.2.3: The relevant entities shall perform regular integrity checks on the backup copies.': {
        'risks': ['Data loss'],
        'controls': ['DRC-1', 'DRC-3'],
        'policies': ['POL-9'],
    },
    '4.2.4: Based on the results of the risk assessment carried out pursuant to point 2.1 and the business continuity plan, the relevant entities shall ensure sufficient availability of resources by at least partial redundancy of the following:': {
        'risks': ['Availability & Disaster recovery', 'Business interruption'],
        'controls': ['BCD-2', 'BCD-4', 'CAP-1'],
        'policies': ['POL-8', 'POL-10'],
    },
    '4.2.5: Where appropriate, the relevant entities shall ensure that monitoring and adjustment of resources, including facilities, systems and personnel, is duly informed by backup and redundancy requirements.': {
        'risks': ['Business interruption'],
        'controls': ['CAP-1', 'CAP-2'],
        'policies': ['POL-8'],
    },
    '4.2.6: The relevant entities shall carry out regular testing of the recovery of backup copies and redundancies to ensure that, in recovery conditions, they can be relied upon and cover the copies, processes and knowledge to perform an effective recovery. The relevant entities shall document the results of the tests and, where needed, take corrective action.': {
        'risks': ['Data loss', 'Availability & Disaster recovery'],
        'controls': ['DRC-1', 'BCD-1'],
        'policies': ['POL-9', 'POL-18'],
    },
    '4.3.1: The relevant entities shall put in place a process for crisis management.': {
        'risks': ['Business interruption', 'Improper response to incidents'],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10'],
    },
    '4.3.2: The relevant entities shall ensure that the crisis management process addresses at least the following elements:': {
        'risks': ['Business interruption', 'Improper response to incidents'],
        'controls': ['BCD-1', 'BCD-3', 'CCI-3'],
        'policies': ['POL-10'],
    },
    '4.3.3: The relevant entities shall implement a process for managing and making use of information received from the CSIRTs or, where applicable, the competent authorities, concerning incidents, vulnerabilities, threats or possible mitigation measures.': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-3', 'BCD-3'],
        'policies': ['POL-10', 'POL-20'],
    },
    '4.3.4: The relevant entities shall test, review and, where appropriate, update the crisis management plan on a regular basis or following significant incidents or significant changes to operations or risks.': {
        'risks': ['Business interruption'],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 5: Supply chain security
    #   (8 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '5.1.1: For the purpose of Article 21(2), point (d) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a supply chain security policy which governs the relations with their direct suppliers and service providers in order to mitigate the identified risks to the security of network and information systems. In the supply chain security policy, the relevant entities shall identify their role in the supply chain and communicate it to their direct suppliers and service providers.': {
        'risks': ['Exposure to third party vendors', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    '5.1.2: As part of the supply chain security policy referred to in point 5.1.1, the relevant entities shall lay down criteria to select and contract suppliers and service providers. Those criteria shall include the following:': {
        'risks': ['Exposure to third party vendors', 'Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-1', 'TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '5.1.3: When establishing their supply chain security policy, relevant entities shall take into account the results of the coordinated security risk assessments of critical supply chains carried out in accordance with Article 22(1) of Directive (EU) 2022/2555, where applicable.': {
        'risks': ['Third-party cybersecurity exposure', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-6'],
        'policies': ['POL-34'],
    },
    '5.1.4: Based on the supply chain security policy and taking into account the results of the risk assessment carried out in accordance with point 2.1 of this Annex, the relevant entities shall ensure that their contracts with the suppliers and service providers specify, where appropriate through service level agreements, the following, where appropriate:': {
        'risks': ['Exposure to third party vendors', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    '5.1.5: The relevant entities shall take into account the elements referred to in point 5.1.2 and 5.1.3 as part of the selection process of new suppliers and service providers, as well as part of the procurement process referred to in point 6.1.': {
        'risks': ['Exposure to third party vendors', 'Inadequate third-party practices'],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '5.1.6: The relevant entities shall review the supply chain security policy, and monitor, evaluate and, where necessary, act upon changes in the cybersecurity practices of suppliers and service providers, at planned intervals and when significant changes to operations or risks or significant incidents related to the provision of ICT services or having impact on the security of the ICT products from suppliers and service providers occur.': {
        'risks': ['Lack of oversight of third-party controls', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'TPM-4'],
        'policies': ['POL-34'],
    },
    '5.1.7: For the purpose of point 5.1.6, the relevant entities shall:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    '5.2.1: The relevant entities shall maintain and keep up to date a registry of their direct suppliers and service providers, including:': {
        'risks': ['Reliance on the third-party', 'Exposure to third party vendors'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 6: Network and information systems security
    #   (31 objectives)
    # ──────────────────────────────────────────────────────────────────────
    "6.1.1: For the purpose of Article 21(2), point (e) of Directive (EU) 2022/2555, the relevant entities shall set and implement processes to manage risks stemming from the acquisition of ICT services or ICT products for components that are critical for the relevant entities' security of network and information systems, based on the risk assessment carried out pursuant to point 2.1, from suppliers or service providers throughout their life cycle.": {
        'risks': ['Security misconfiguration of APIs / Applications', 'Exposure to third party vendors'],
        'controls': ['APD-2', 'TPM-3'],
        'policies': ['POL-6', 'POL-34'],
    },
    '6.1.2: For the purpose of point 6.1.1, the processes referred to in point 6.1.1 shall include:': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['APD-2', 'CHM-1'],
        'policies': ['POL-6', 'POL-11'],
    },
    '6.1.3: The relevant entities shall review and, where appropriate, update the processes at planned intervals and when significant incidents occur.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['CHM-3', 'GOV-3'],
        'policies': ['POL-11'],
    },
    '6.2.1: Before developing a network and information system, including software, the relevant entities shall lay down rules for the secure development of network and information systems and apply them when developing network and information systems in-house, or when outsourcing the development of network and information systems. The rules shall cover all development phases, including specification, design, development, implementation and testing.': {
        'risks': ['Lack of design reviews & security testing', 'Security misconfiguration of APIs / Applications'],
        'controls': ['APD-1', 'APD-6'],
        'policies': ['POL-33'],
    },
    '6.2.2: For the purpose of point 6.2.1, the relevant entities shall:': {
        'risks': ['Lack of design reviews & security testing'],
        'controls': ['APD-1', 'APD-4', 'APD-6'],
        'policies': ['POL-33'],
    },
    '6.2.3: For outsourced development of network and information systems, the relevant entities shall also apply the policies and procedures referred to in points 5 and 6.1.': {
        'risks': ['Exposure to third party vendors', 'Lack of design reviews & security testing'],
        'controls': ['APD-6', 'TPM-1'],
        'policies': ['POL-33', 'POL-34'],
    },
    '6.2.4: The relevant entities shall review and, where necessary, update their secure development rules at planned intervals.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['APD-6'],
        'policies': ['POL-33'],
    },
    '6.3.1: The relevant entities shall take the appropriate measures to establish, document, implement, and monitor configurations, including security configurations of hardware, software, services and networks.': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Cloud misconfiguration'],
        'controls': ['CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    '6.3.2: For the purpose of point 6.3.1, the relevant entities shall:': {
        'risks': ['Security misconfiguration of APIs / Applications'],
        'controls': ['CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    '6.3.3: The relevant entities shall review and, where appropriate, update configurations at planned intervals or when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Unauthorized changes'],
        'controls': ['CMM-2', 'CM-3'],
        'policies': ['POL-15'],
    },
    "6.4.1: The relevant entities shall apply change management procedures to control changes of network and information systems. Where applicable, the procedures shall be consistent with the relevant entities' general policies concerning change management.": {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['CHM-1', 'CHM-3'],
        'policies': ['POL-11'],
    },
    '6.4.2: The procedures referred to in point 6.4.1 shall be applied for releases, modifications and emergency changes of any software and hardware in operation and changes to the configuration. The procedures shall ensure that those changes are documented and, based on the risk assessment carried out pursuant to point 2.1, tested and assessed in view of the potential impact before being implemented.': {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'CHM-4'],
        'policies': ['POL-11'],
    },
    '6.4.3: In the event that the regular change management procedures could not be followed due to an emergency, the relevant entities shall document the result of the change, and the explanation for why the procedures could not be followed.': {
        'risks': ['Unauthorized changes'],
        'controls': ['CHM-1', 'CHM-3'],
        'policies': ['POL-11'],
    },
    '6.4.4: The relevant entities shall review and, where appropriate, update the procedures at planned intervals and when significant incidents or significant changes to operations or risks.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['CHM-3'],
        'policies': ['POL-11'],
    },
    '6.5.1: The relevant entities shall establish, implement and apply a policy and procedures for security testing.': {
        'risks': ['Lack of design reviews & security testing', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2'],
        'policies': ['POL-35'],
    },
    '6.5.2: The relevant entities shall:': {
        'risks': ['Lack of design reviews & security testing', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2', 'APD-4'],
        'policies': ['POL-35'],
    },
    '6.5.3: The relevant entities shall review and, where appropriate, update their security testing policies at planned intervals.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['CVM-1'],
        'policies': ['POL-35'],
    },
    '6.6.1: The relevant entities shall specify and apply procedures, coherent with the change management procedures referred to in point 6.4.1 as well as with vulnerability management, risk management and other relevant management procedures, for ensuring that:': {
        'risks': ['Unpatched vulnerability exploitation', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-3', 'CVM-7'],
        'policies': ['POL-26'],
    },
    '6.6.2: By way of derogation from point 6.6.1(a), the relevant entities may choose not to apply security patches when the disadvantages of applying the security patches outweigh the cybersecurity benefits. The relevant entities shall duly document and substantiate the reasons for any such decision.': {
        'risks': ['Unpatched vulnerability exploitation'],
        'controls': ['CVM-3', 'CVM-7'],
        'policies': ['POL-26'],
    },
    '6.7.1: The relevant entities shall take the appropriate measures to protect their network and information systems from cyber threats.': {
        'risks': ['System compromise', 'Information loss / corruption or system compromise due to technical attack'],
        'controls': ['NES-1', 'NES-2'],
        'policies': ['POL-24'],
    },
    '6.7.2: For the purpose of point 6.7.1, the relevant entities shall:': {
        'risks': ['System compromise', 'Denial of Service (DoS) Attack'],
        'controls': ['NES-1', 'NES-2', 'NES-4', 'NES-5'],
        'policies': ['POL-24'],
    },
    '6.7.3: The relevant entities shall review and, where appropriate, update these measures at planned intervals and when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['NES-1', 'NES-6'],
        'policies': ['POL-24'],
    },
    "6.8.1: The relevant entities shall segment systems into networks or zones in accordance with the results of the risk assessment referred to in point 2.1. They shall segment their systems and networks from third parties' systems and networks.": {
        'risks': ['System compromise', 'Data breach'],
        'controls': ['NES-3'],
        'policies': ['POL-24'],
    },
    '6.8.2: For that purpose, the relevant entities shall:': {
        'risks': ['System compromise'],
        'controls': ['NES-3', 'NES-5'],
        'policies': ['POL-24'],
    },
    '6.8.3: The relevant entities shall review and, where appropriate, update network segmentation at planned intervals and when significant incidents or significant changes to operations or risks.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['NES-3'],
        'policies': ['POL-24'],
    },
    '6.9.1: The relevant entities shall protect their network and information systems against malicious and unauthorised software.': {
        'risks': ['Malware', 'Information loss / corruption or system compromise due to technical attack'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '6.9.2: For that purpose, the relevant entities shall in particular implement measures that detect or prevent the use of malicious or unauthorised software. The relevant entities shall, where appropriate, ensure that their network and information systems are equipped with detection and response software, which is updated regularly in accordance with the risk assessment carried out pursuant to point 2.1 and the contractual agreements with the providers.': {
        'risks': ['Malware', 'Zero-Day Exploit'],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    '6.10.1: The relevant entities shall obtain information about technical vulnerabilities in their network and information systems, evaluate their exposure to such vulnerabilities, and take appropriate measures to manage the vulnerabilities.': {
        'risks': ['Unmitigated vulnerabilities', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-1', 'CVM-3'],
        'policies': ['POL-35'],
    },
    '6.10.2: For the purpose of point 6.10.1, the relevant entities shall:': {
        'risks': ['Unmitigated vulnerabilities', 'Unpatched vulnerability exploitation'],
        'controls': ['CVM-1', 'CVM-2', 'CVM-3'],
        'policies': ['POL-35', 'POL-26'],
    },
    '6.10.3: When justified by the potential impact of the vulnerability, the relevant entities shall create and implement a plan to mitigate the vulnerability. In other cases, the relevant entities shall document and substantiate the reason why the vulnerability does not require remediation.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'RSM-3'],
        'policies': ['POL-35'],
    },
    '6.10.4: The relevant entities shall review and, where appropriate, update at planned intervals the channels they use for monitoring vulnerability information.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1'],
        'policies': ['POL-35'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 7: Policies and procedures to assess the effectiveness of
    #   cybersecurity risk-management measures  (3 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '7.1: For the purpose of Article 21(2), point (f) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a policy and procedures to assess whether the cybersecurity risk-management measures taken by the relevant entity are effectively implemented and maintained.': {
        'risks': ['Lack of oversight of internal controls', 'Inadequate internal practices'],
        'controls': ['GOV-12'],
        'policies': ['POL-36', 'POL-37'],
    },
    '7.2: The policy and procedures referred to in point 7.1 shall take into account results of the risk assessment pursuant to point 2.1 and past significant incidents. The relevant entities shall determine:': {
        'risks': ['Lack of oversight of internal controls'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    '7.3: The relevant entities shall review and, where appropriate, update the policy and procedures at planned intervals and when significant incidents or significant changes to operations or risks.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['GOV-12'],
        'policies': ['POL-36'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 8: Basic cyber hygiene practices and security training
    #   (8 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '8.1.1: For the purpose of Article 21(2), point (g) of Directive (EU) 2022/2555, the relevant entities shall ensure that their employees, including members of management bodies, as well as direct suppliers and service providers are aware of risks, are informed of the importance of cybersecurity and apply cyber hygiene practices.': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8'],
        'policies': ['POL-39', 'POL-27'],
    },
    '8.1.2: For the purpose of point 8.1.1, the relevant entities shall offer to their employees, including members of management bodies, as well as to direct suppliers and service providers where appropriate in accordance with point 5.1.4, an awareness raising programme, which shall:': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8'],
        'policies': ['POL-39', 'POL-27'],
    },
    '8.1.3: The awareness raising programme shall, where appropriate, be tested in terms of effectiveness. The awareness raising programme shall be updated and offered at planned intervals taking into account changes in cyber hygiene practices, and the current threat landscape and risks posed to the relevant entities.': {
        'risks': ['Lack of cybersecurity awareness'],
        'controls': ['HRM-8'],
        'policies': ['POL-39'],
    },
    '8.2.1: The relevant entities shall identify employees, whose roles require security relevant skill sets and expertise, and ensure that they receive regular training on network and information system security.': {
        'risks': ['Lack of a security-minded workforce', 'Cybersecurity skills gap in managing the cloud infrastructure'],
        'controls': ['HRM-8', 'HRM-12'],
        'policies': ['POL-27'],
    },
    '8.2.2: The relevant entities shall establish, implement and apply a training program in line with the network and information security policy, topic-specific policies and other relevant procedures on network and information security which lays down the training needs for certain roles and positions based on criteria.': {
        'risks': ['Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'HRM-12'],
        'policies': ['POL-27'],
    },
    '8.2.3: The training referred to in point 8.2.1 shall be relevant to the job function of the employee and its effectiveness shall be assessed. Training shall take into consideration security measures in place and cover the following:': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8'],
        'policies': ['POL-27'],
    },
    '8.2.4: The relevant entities shall apply training to staff members who transfer to new positions or roles which require security relevant skill sets and expertise.': {
        'risks': ['Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'HRM-6'],
        'policies': ['POL-27'],
    },
    '8.2.5: The program shall be updated and run periodically taking into account applicable policies and rules, assigned roles, responsibilities, as well as known cyber threats and technological developments.': {
        'risks': ['Lack of cybersecurity awareness'],
        'controls': ['HRM-8'],
        'policies': ['POL-27', 'POL-39'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 9: Cryptography
    #   (3 objectives)
    # ──────────────────────────────────────────────────────────────────────
    "9.1: For the purpose of Article 21(2), point (h) of Directive (EU) 2022/2555, the relevant entities shall establish, implement and apply a policy and procedures related to cryptography, with a view to ensuring adequate and effective use of cryptography to protect the confidentiality, authenticity and integrity of data in line with the relevant entities' asset classification and the results of the risk assessment carried out pursuant to point 2.1.": {
        'risks': ['Weak cryptography & encryption support in the application', 'Data loss / corruption'],
        'controls': ['CRY-1', 'CRY-2', 'CRY-4'],
        'policies': ['POL-19'],
    },
    '9.2: The policy and procedures referred to in point 9.1 shall establish:': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'CRY-2', 'CRY-3'],
        'policies': ['POL-19'],
    },
    '9.3: The relevant entities shall review and, where appropriate, update their policy and procedures at planned intervals, taking into account the state of the art in cryptography.': {
        'risks': ['Weak cryptography & encryption support in the application'],
        'controls': ['CRY-4'],
        'policies': ['POL-19'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 10: Human resources security
    #   (10 objectives)
    # ──────────────────────────────────────────────────────────────────────
    "10.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall ensure that their employees and direct suppliers and service providers, wherever applicable, understand and commit to their security responsibilities, as appropriate for the offered services and the job and in line with the relevant entities' policy on the security of network and information systems.": {
        'risks': ['Insider Threat', 'Lack of a security-minded workforce'],
        'controls': ['HRM-1', 'HRM-10'],
        'policies': ['POL-27', 'POL-13'],
    },
    '10.1.2: The requirement referred to in point 10.1.1 shall include the following:': {
        'risks': ['Insider Threat', 'Lack of a security-minded workforce'],
        'controls': ['HRM-1', 'HRM-4'],
        'policies': ['POL-27', 'POL-13'],
    },
    '10.1.3: The relevant entities shall review the assignment of personnel to specific roles as referred to in point 1.2, as well as their commitment of human resources in that regard, at planned intervals and at least annually. They shall updatethe assignment where necessary.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['HRM-6', 'HRM-11'],
        'policies': ['POL-27'],
    },
    '10.2.1: The relevant entities shall ensure to the extent feasible verification of the background of their employees, and where applicable of direct suppliers and service providers in accordance with point 5.1.4, if necessary for their role, responsibilities and authorisations.': {
        'risks': ['Insider Threat', 'Ex-Employees / disgruntled employees'],
        'controls': ['HRM-2'],
        'policies': ['POL-27'],
    },
    '10.2.2: For the purpose of point 10.2.1, the relevant entities shall:': {
        'risks': ['Insider Threat'],
        'controls': ['HRM-2'],
        'policies': ['POL-27'],
    },
    '10.2.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and update it where necessary.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['HRM-2'],
        'policies': ['POL-27'],
    },
    '10.3.1: The relevant entities shall ensure that network and information system security responsibilities and duties that remain valid after termination or change of employment of their employees are contractually defined and enforced.': {
        'risks': ['Ex-Employees / disgruntled employees', 'Insider Threat'],
        'controls': ['HRM-7'],
        'policies': ['POL-27'],
    },
    "10.3.2: For the purpose of point 10.3.1, the relevant entities shall include in the individual's terms and conditions of employment, contract or agreement the responsibilities and duties that are still valid after termination of employment or contract, such as confidentiality clauses.": {
        'risks': ['Ex-Employees / disgruntled employees'],
        'controls': ['HRM-7', 'HRM-1'],
        'policies': ['POL-27', 'POL-14'],
    },
    '10.4.1: The relevant entities shall establish, communicate and maintain a disciplinary process for handling violations of network and information system security policies. The process shall take into consideration relevant legal, statutory, contractual and business requirements.': {
        'risks': ['Insider Threat', 'Illegal content or abusive action'],
        'controls': ['HRM-9'],
        'policies': ['POL-31'],
    },
    '10.4.2: The relevant entities shall review and, where appropriate, update the disciplinary process at planned intervals, and when necessary due to legal changes or significant changes to operations or risks.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['HRM-9'],
        'policies': ['POL-31'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 11: Access control
    #   (21 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '11.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall establish, document and implement logical and physical access control policies for the access to their network and information systems, based on business requirements as well as network and information system security requirements.': {
        'risks': ['Unauthorized access', 'Unauthorized Access'],
        'controls': ['IAM-8', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '11.1.2: The policies referred to in point 11.1.1. shall:': {
        'risks': ['Unauthorized access', 'Improper assignment of privileged functions'],
        'controls': ['IAM-7', 'IAM-8'],
        'policies': ['POL-4'],
    },
    '11.1.3: The relevant entities shall review and, where appropriate, update the policies at planned intervals and when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['IAM-8'],
        'policies': ['POL-4'],
    },
    '11.2.1: The relevant entities shall provide, modify, remove and document access rights to network and information systems in accordance with the access control policy referred to in point 11.1.': {
        'risks': ['Unauthorized access', 'Privilege escalation'],
        'controls': ['IAM-1', 'IAM-3'],
        'policies': ['POL-4'],
    },
    '11.2.2: The relevant entities shall:': {
        'risks': ['Unauthorized access', 'Privilege escalation'],
        'controls': ['IAM-1', 'IAM-3', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '11.2.3: The relevant entities shall review access rights at planned intervals and shall modify them based on organisational changes. The relevant entities shall document the results of the review including the necessary changes of access rights.': {
        'risks': ['Unauthorized access', 'Improper assignment of privileged functions'],
        'controls': ['IAM-3', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '11.3.1: The relevant entities shall maintain policies for management of privileged accounts and system administration accounts as part of the access control policy referred to in point 11.1.': {
        'risks': ['Privilege escalation', 'Unauthorized Access'],
        'controls': ['IAM-4', 'IAM-8'],
        'policies': ['POL-4'],
    },
    '11.3.2: The policies referred to in point 11.3.1 shall:': {
        'risks': ['Privilege escalation', 'Improper assignment of privileged functions'],
        'controls': ['IAM-4'],
        'policies': ['POL-4'],
    },
    '11.3.3: The relevant entities shall review access rights of privileged accounts and system administration accounts at planned intervals and be modified based on organisational changes, and shall document the results of the review, including the necessary changes of access rights.': {
        'risks': ['Privilege escalation', 'Unauthorized Access'],
        'controls': ['IAM-3', 'IAM-4'],
        'policies': ['POL-4'],
    },
    '11.4.1: The relevant entities shall restrict and control the use of system administration systems in accordance with the access control policy referred to in point 11.1.': {
        'risks': ['Privilege escalation', 'Unauthorized Access'],
        'controls': ['IAM-4', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '11.4.2: For that purpose, the relevant entities shall:': {
        'risks': ['Privilege escalation'],
        'controls': ['IAM-4', 'IAM-2'],
        'policies': ['POL-4'],
    },
    '11.5.1: The relevant entities shall manage the full life cycle of identities of network and information systems and their users.': {
        'risks': ['Unauthorized Access', 'Broken or weak authentication'],
        'controls': ['IAM-1', 'IAM-3'],
        'policies': ['POL-4', 'POL-1'],
    },
    '11.5.2: For that purpose, the relevant entities shall:': {
        'risks': ['Unauthorized Access'],
        'controls': ['IAM-1', 'IAM-3'],
        'policies': ['POL-4'],
    },
    '11.5.3: The relevant entities shall only permit identities assigned to multiple persons, such as shared identities, where they are necessary for business or operational reasons and are subject to an explicit approval process and documentation. The relevant entities shall take identities assigned to multiple persons into account in the cybersecurity risk management framework referred to in point 2.1.': {
        'risks': ['Unauthorized Access', 'Inability to maintain individual accountability'],
        'controls': ['IAM-1', 'IAM-7'],
        'policies': ['POL-4'],
    },
    '11.5.4: The relevant entities shall regularly review the identities for network and information systems and their users and, if no longer needed, deactivate them without delay.': {
        'risks': ['Unauthorized Access', 'Ex-Employees / disgruntled employees'],
        'controls': ['IAM-3'],
        'policies': ['POL-4'],
    },
    '11.6.1: The relevant entities shall implement secure authentication procedures and technologies based on access restrictions and the policy on access control.': {
        'risks': ['Broken or weak authentication', 'Credential Stuffing'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1'],
    },
    '11.6.2: For that purpose, the relevant entities shall:': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6', 'IAM-9'],
        'policies': ['POL-1'],
    },
    '11.6.3: The relevant entities shall to the extent feasible use state-of-the-art authentication methods, in accordance with the associated assessed risk and the classification of the asset to be accessed, and unique authentication information.': {
        'risks': ['Broken or weak authentication', 'Credential Stuffing'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    '11.6.4: The relevant entities shall review the authentication procedures and technologies at planned intervals.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-9'],
        'policies': ['POL-1'],
    },
    "11.7.1: The relevant entities shall ensure that users are authenticated by multiple authentication factors or continuous authentication mechanisms for accessing the relevant entities' network and information systems, where appropriate, in accordance with the classification of the asset to be accessed.": {
        'risks': ['Broken or weak authentication', 'Unauthorized Access'],
        'controls': ['IAM-6'],
        'policies': ['POL-1', 'POL-4'],
    },
    '11.7.2: The relevant entities shall ensure that the strength of authentication is appropriate for the classification of the asset to be accessed.': {
        'risks': ['Broken or weak authentication'],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 12: Asset management
    #   (13 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '12.1.1: For the purpose of Article 21(2), point (i) of Directive (EU) 2022/2555, the relevant entities shall lay down classification levels of all assets, including information, in scope of their network and information systems for the level of protection required.': {
        'risks': ['Inability to maintain individual accountability', 'Lost, damaged or stolen asset(s)'],
        'controls': ['AST-3', 'DCH-2'],
        'policies': ['POL-7', 'POL-16'],
    },
    '12.1.2: For the purpose of point 12.1.1, the relevant entities shall:': {
        'risks': ['Inability to maintain individual accountability'],
        'controls': ['AST-3', 'DCH-2', 'DCH-5'],
        'policies': ['POL-16'],
    },
    '12.1.3: The relevant entities shall conduct periodic reviews of the classification levels of assets and update them, where appropriate.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['AST-3'],
        'policies': ['POL-7', 'POL-16'],
    },
    '12.2.1: The relevant entities shall establish, implement and apply a policy for the proper handling of assets, including information, in accordance with their network and information security policy, and shall communicate the policy on proper handling of assets to anyone who uses or handles assets.': {
        'risks': ['Data loss / corruption', 'Lost, damaged or stolen asset(s)'],
        'controls': ['AST-4', 'DCH-5'],
        'policies': ['POL-7'],
    },
    '12.2.2: The policy shall:': {
        'risks': ['Data loss / corruption'],
        'controls': ['AST-4', 'DCH-1', 'DCH-5'],
        'policies': ['POL-7', 'POL-16'],
    },
    '12.2.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['AST-4'],
        'policies': ['POL-7'],
    },
    "12.3.1: The relevant entities shall establish, implement and apply a policy on the management of removable storage media and communicate it to their employees and third parties who handle removable storage media at the relevant entities' premises or other locations where the removable media is connected to the relevant entities' network and information systems.": {
        'risks': ['Data loss / corruption', 'Data theft from Laptops and other employee owned devices'],
        'controls': ['AST-4', 'DCH-5'],
        'policies': ['POL-7'],
    },
    '12.3.2: The policy shall:': {
        'risks': ['Data loss / corruption'],
        'controls': ['AST-2', 'DCH-4'],
        'policies': ['POL-7', 'POL-17'],
    },
    '12.3.3: The relevant entities shall review and, where appropriate, update the policy at planned intervals and when significant incidents or significant changes to operations or risks occur.': {
        'risks': ['Outdated policies for Process Management'],
        'controls': ['AST-4'],
        'policies': ['POL-7'],
    },
    '12.4.1: The relevant entities shall develop and maintain a complete, accurate, up-to-date and consistent inventory of their assets. They shall record changes to the entries in the inventory in a traceable manner.': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Inability to maintain individual accountability'],
        'controls': ['AST-1'],
        'policies': ['POL-7'],
    },
    '12.4.2: The granularity of the inventory of the assets shall be at a level appropriate for the needs of the relevant entities. The inventory shall include the following:': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['AST-1', 'DCH-3'],
        'policies': ['POL-7'],
    },
    '12.4.3: The relevant entities shall regularly review and update the inventory and their assets and document the history of changes.': {
        'risks': ['Lost, damaged or stolen asset(s)'],
        'controls': ['AST-1'],
        'policies': ['POL-7'],
    },
    "12.5.1: The relevant entities shall establish, implement and apply procedures which ensure that their assets which are under custody of personnel are deposited, returned or deleted upon termination of employment, and shall document the deposit, return and deletion of those assets. Where the deposit, return or deletion of assets is not possible, the relevant entities shall ensure that the assets can no longer access the relevant entities' network and information systems in accordance with point 12.2.2.": {
        'risks': ['Ex-Employees / disgruntled employees', 'Lost, damaged or stolen asset(s)'],
        'controls': ['HRM-7', 'AST-2'],
        'policies': ['POL-7', 'POL-27'],
    },
    # ──────────────────────────────────────────────────────────────────────
    # Chapter 13: Environmental and physical security
    #   (9 objectives)
    # ──────────────────────────────────────────────────────────────────────
    '13.1.1: For the purpose of Article 21(2)(c) of Directive (EU) 2022/2555, the relevant entities shall prevent loss, damage or compromise of network and information systems or interruption to their operations due to the failure and disruption of supporting utilities.': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)', 'Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-2', 'PES-4'],
        'policies': ['POL-28'],
    },
    '13.1.2: For that purpose, the relevant entities shall, where appropriate:': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-2', 'PES-4'],
        'policies': ['POL-28'],
    },
    '13.1.3: The relevant entities shall test, review and, where appropriate, update the protection measures on a regular basis or following significant incidents or significant changes to operations or risks.': {
        'risks': ['Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-4'],
        'policies': ['POL-28'],
    },
    '13.2.1: For the purpose of Article 21(2)(e) of Directive (EU) 2022/2555, the relevant entities shall prevent or reduce the consequences of events originating from physical and environmental threats, such as natural disasters and other intentional or unintentional threats, based on the results of the risk assessment carried out pursuant to point 2.1.': {
        'risks': ['Natural Disasters for Physical facilities(Bldg., Equip...)', 'Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-2', 'PES-4'],
        'policies': ['POL-28'],
    },
    '13.2.2: For that purpose, the relevant entities shall, where appropriate:': {
        'risks': ['Natural Disasters for Physical facilities(Bldg., Equip...)', 'Accidental fire, water, electrical  damage for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-2'],
        'policies': ['POL-28'],
    },
    '13.2.3: The relevant entities shall test, review and, where appropriate, update the protection measures against physical and environmental threats on a regular basis or following significant incidents or significant changes to operations or risks.': {
        'risks': ['Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-4'],
        'policies': ['POL-28'],
    },
    '13.3.1: For the purpose of Article 21(2)(i) of Directive (EU) 2022/2555, the relevant entities shall prevent and monitor unauthorised physical access, damage and interference to their network and information systems.': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)', 'Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-3', 'PES-4'],
        'policies': ['POL-28'],
    },
    '13.3.2: For that purpose, the relevant entities shall:': {
        'risks': ['Power Outages for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-3'],
        'policies': ['POL-28'],
    },
    '13.3.3: The relevant entities shall test, review and, where appropriate, update the physical access control measures on a regular basis or following significant incidents or significant changes to operations or risks.': {
        'risks': ['Natural Disasters for Physical facilities(Bldg., Equip...)'],
        'controls': ['PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
}
