# Maps each DORA 2022 objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code in control_templates (Baseline Controls)
# - policies: matched by POL code in policy_templates

DORA_2022_CONNECTIONS = {
    'Article 5.1: Financial entities shall have in place an internal governance and control framework that ensures an effective and prudent management of ICT risk, in accordance with Article 6(4), in order to achieve a high level of digital operational resilience.': {
        'risks': ['Lack of oversight of internal controls', 'Incorrect controls scoping'],
        'controls': ['GOV-1', 'GOV-3', 'GOV-9'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 5.2: The management body of the financial entity shall define, approve, oversee and be responsible for the implementation of all arrangements related to the ICT risk management framework referred to in Article 6(1).': {
        'risks': ['Lack of roles & responsibilities', 'Inadequate internal practices'],
        'controls': ['GOV-10', 'GOV-4', 'RSM-2'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 5.3: Financial entities, other than microenterprises, shall establish a role in order to monitor the arrangements concluded with ICT third-party service providers on the use of ICT services, or shall designate a member of senior management as responsible for overseeing the related risk exposure and relevant documentation.': {
        'risks': ['Exposure to third party vendors', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-4'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 5.4: Members of the management body of the financial entity shall actively keep up to date with sufficient knowledge and skills to understand and assess ICT risk and its impact on the operations of the financial entity, including by following specific training on a regular basis, commensurate to the ICT risk being managed.': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'GOV-10'],
        'policies': ['POL-21', 'POL-27'],
    },
    'Article 6.1: Financial entities shall have a sound, comprehensive and well-documented ICT risk management framework as part of their overall risk management system, which enables them to address ICT risk quickly, efficiently and comprehensively and to ensure a high level of digital operational resilience.': {
        'risks': ['Inadequate internal practices', 'Incorrect controls scoping'],
        'controls': ['GOV-1', 'RSM-2', 'GOV-9'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 6.2: The ICT risk management framework shall include at least strategies, policies, procedures, ICT protocols and tools that are necessary to duly and adequately protect all information assets and ICT assets, including computer software, hardware, servers, as well as to protect all relevant physical components and infrastructures, such as premises, data centres and sensitive designated areas, to ensure that all information assets and ICT assets are adequately protected from risks including damage and unauthorised access or usage.': {
        'risks': ['Outdated policies for Process Management', 'Incorrect controls scoping'],
        'controls': ['GOV-1', 'GOV-5', 'RSM-2'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 6.3: In accordance with their ICT risk management framework, financial entities shall minimise the impact of ICT risk by deploying appropriate strategies, policies, procedures, ICT protocols and tools. They shall provide complete and updated information on ICT risk and on their ICT risk management framework to the competent authorities upon their request.': {
        'risks': ['Inadequate internal practices', 'Inability to support business processes'],
        'controls': ['GOV-3', 'RSM-2', 'RSM-3'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 6.4: Financial entities, other than microenterprises, shall assign the responsibility for managing and overseeing ICT risk to a control function and ensure an appropriate level of independence of such control function in order to avoid conflicts of interest. Financial entities shall ensure appropriate segregation and independence of ICT risk management functions, control functions, and internal audit functions, according to the three lines of defence model, or an internal risk management and control model.': {
        'risks': ['Lack of roles & responsibilities', 'Lack of oversight of internal controls'],
        'controls': ['GOV-4', 'HRM-11'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 6.5: The ICT risk management framework shall be documented and reviewed at least once a year, or periodically in the case of microenterprises, as well as upon the occurrence of major ICT-related incidents, and following supervisory instructions or conclusions derived from relevant digital operational resilience testing or audit processes. It shall be continuously improved on the basis of lessons derived from implementation and monitoring. A report on the review of the ICT risk management framework shall be submitted to the competent authority upon its request.': {
        'risks': ['Outdated policies for Process Management', 'Inadequate internal practices'],
        'controls': ['GOV-1', 'GOV-5', 'GOV-11'],
        'policies': ['POL-21', 'POL-30'],
    },
    "Article 6.6: The ICT risk management framework of financial entities, other than microenterprises, shall be subject to internal audit by auditors on a regular basis in line with the financial entities' audit plan. Those auditors shall possess sufficient knowledge, skills and expertise in ICT risk, as well as appropriate independence. The frequency and focus of ICT audits shall be commensurate to the ICT risk of the financial entity.": {
        'risks': ['Lack of oversight of internal controls', 'Incorrect controls scoping'],
        'controls': ['GOV-12', 'GOV-9'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 6.7: Based on the conclusions from the internal audit review, financial entities shall establish a formal follow-up process, including rules for the timely verification and remediation of critical ICT audit findings.': {
        'risks': ['Ineffective remediation actions', 'Lack of oversight of internal controls'],
        'controls': ['GOV-12', 'GOV-3'],
        'policies': ['POL-21'],
    },
    'Article 6.8: The ICT risk management framework shall include a digital operational resilience strategy setting out how the framework shall be implemented. To that end, the digital operational resilience strategy shall include methods to address ICT risk and attain specific ICT objectives, by:': {
        'risks': ['Business interruption', 'Inadequate internal practices'],
        'controls': ['GOV-1', 'RSM-2', 'BCD-1'],
        'policies': ['POL-21', 'POL-10'],
    },
    'Article 6.9: Financial entities may, in the context of the digital operational resilience strategy referred to in paragraph 8, define a holistic ICT multi-vendor strategy, at group or entity level, showing key dependencies on ICT third-party service providers and explaining the rationale behind the procurement mix of ICT third-party service providers.': {
        'risks': ['Exposure to third party vendors', 'Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 6.10: Financial entities may, in accordance with Union and national sectoral law, outsource the tasks of verifying compliance with ICT risk management requirements to intra-group or external undertakings. In case of such outsourcing, the financial entity remains fully responsible for the verification of compliance with the ICT risk management requirements.': {
        'risks': ['Inadequate third-party practices', 'Third-party compliance / legal exposure'],
        'controls': ['GOV-8', 'TPM-2'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 7.1:  ICT systems, protocols and tools': {
        'risks': ['Inability to support business processes', 'Unmitigated vulnerabilities'],
        'controls': ['GOV-1', 'CMM-2', 'CVM-1'],
        'policies': ['POL-21', 'POL-15'],
    },
    'Article 8.1: As part of the ICT risk management framework referred to in Article 6(1), financial entities shall identify, classify and adequately document all ICT supported business functions, roles and responsibilities, the information assets and ICT assets supporting those functions, and their roles and dependencies in relation to ICT risk. Financial entities shall review as needed, and at least yearly, the adequacy of this classification and of any relevant documentation.': {
        'risks': ['Incorrect controls scoping', 'Inability to maintain individual accountability'],
        'controls': ['AST-1', 'AST-3', 'GOV-1'],
        'policies': ['POL-7', 'POL-21'],
    },
    'Article 8.2: Financial entities shall, on a continuous basis, identify all sources of ICT risk, in particular the risk exposure to and from other financial entities, and assess cyber threats and ICT vulnerabilities relevant to their ICT supported business functions, information assets and ICT assets. Financial entities shall review on a regular basis, and at least yearly, the risk scenarios impacting them.': {
        'risks': ['Unmitigated vulnerabilities', 'Inadequate internal practices'],
        'controls': ['RSM-2', 'GOV-6', 'CVM-1'],
        'policies': ['POL-30', 'POL-35'],
    },
    'Article 8.3: Financial entities, other than microenterprises, shall perform a risk assessment upon each major change in the network and information system infrastructure, in the processes or procedures affecting their ICT supported business functions, information assets or ICT assets.': {
        'risks': ['Unauthorized changes', 'Loss of integrity through unauthorized changes'],
        'controls': ['CHM-1', 'CHM-2', 'GOV-6'],
        'policies': ['POL-11', 'POL-30'],
    },
    'Article 8.4: Financial entities shall identify all information assets and ICT assets, including those on remote sites, network resources and hardware equipment, and shall map those considered critical. They shall map the configuration of the information assets and ICT assets and the links and interdependencies between the different information assets and ICT assets.': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Incorrect controls scoping'],
        'controls': ['AST-1', 'AST-3', 'CMM-2'],
        'policies': ['POL-7', 'POL-15'],
    },
    'Article 8.5: Financial entities shall identify and document all processes that are dependent on ICT third-party service providers, and shall identify interconnections with ICT third-party service providers that provide services that support critical or important functions.': {
        'risks': ['Exposure to third party vendors', 'Reliance on the third-party'],
        'controls': ['TPM-3', 'AST-1'],
        'policies': ['POL-34', 'POL-7'],
    },
    'Article 8.6: For the purposes of paragraphs 1, 4 and 5, financial entities shall maintain relevant inventories and update them periodically and every time any major change as referred to in paragraph 3 occurs.': {
        'risks': ['Lost, damaged or stolen asset(s)', 'Inability to maintain individual accountability'],
        'controls': ['AST-1', 'AST-3'],
        'policies': ['POL-7'],
    },
    'Article 8.7: Financial entities, other than microenterprises, shall on a regular basis, and at least yearly, conduct a specific ICT risk assessment on all legacy ICT systems and, in any case before and after connecting technologies, applications or systems.': {
        'risks': ['Unmitigated vulnerabilities', 'Security misconfiguration of APIs / Applications'],
        'controls': ['CVM-1', 'GOV-6', 'RSM-2'],
        'policies': ['POL-35', 'POL-30'],
    },
    'Article 9.1: For the purposes of adequately protecting ICT systems and with a view to organising response measures, financial entities shall continuously monitor and control the security and functioning of ICT systems and tools and shall minimise the impact of ICT risk on ICT systems through the deployment of appropriate ICT security tools, policies and procedures.': {
        'risks': ['System compromise', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-5', 'GOV-1'],
        'policies': ['POL-21', 'POL-35'],
    },
    'Article 9.2: Financial entities shall design, procure and implement ICT security policies, procedures, protocols and tools that aim to ensure the resilience, continuity and availability of ICT systems, in particular for those supporting critical or important functions, and to maintain high standards of availability, authenticity, integrity and confidentiality of data, whether at rest, in use or in transit.': {
        'risks': ['Outdated policies for Process Management', 'Business interruption'],
        'controls': ['GOV-1', 'GOV-5', 'BCD-2'],
        'policies': ['POL-21', 'POL-8'],
    },
    'Article 9.3: In order to achieve the objectives referred to in paragraph 2, financial entities shall use ICT solutions and processes that are appropriate in accordance with Article 4. Those ICT solutions and processes shall:': {
        'risks': ['Security misconfiguration of APIs / Applications', 'Weak cryptography & encryption support in the application'],
        'controls': ['CRY-1', 'CRY-2', 'IAM-5'],
        'policies': ['POL-19', 'POL-4'],
    },
    'Article 9.4: As part of the ICT risk management framework referred to in Article 6(1), financial entities shall:': {
        'risks': ['Unauthorized access', 'Improper assignment of privileged functions'],
        'controls': ['IAM-1', 'IAM-4', 'IAM-7'],
        'policies': ['POL-4', 'POL-21'],
    },
    'Article 9.1: Financial entities shall have in place mechanisms to promptly detect anomalous activities, in accordance with Article 17, including ICT network performance issues and ICT-related incidents, and to identify potential material single points of failure.\nAll detection mechanisms referred to in the first subparagraph shall be regularly tested in accordance with Article 25.': {
        'risks': ['Insufficient monitoring & alerting', 'Inability to maintain situational awareness'],
        'controls': ['ALM-1', 'ALM-3', 'ALM-5'],
        'policies': ['POL-22'],
    },
    'Article 10.2: The detection mechanisms referred to in paragraph 1 shall enable multiple layers of control, define alert thresholds and criteria to trigger and initiate ICT-related incident response processes, including automatic alert mechanisms for relevant staff in charge of ICT-related incident response.': {
        'risks': ['Insufficient monitoring & alerting', 'Inability to maintain situational awareness'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22'],
    },
    'Article 10.3: Financial entities shall devote sufficient resources and capabilities to monitor user activity, the occurrence of ICT anomalies and ICT-related incidents, in particular cyber-attacks.': {
        'risks': ['Insufficient monitoring & alerting', 'Insider Threat'],
        'controls': ['ALM-1', 'ALM-2', 'ALM-5'],
        'policies': ['POL-22'],
    },
    'Article 10.4: Data reporting service providers shall, in addition, have in place systems that can effectively check trade reports for completeness, identify omissions and obvious errors, and request re-transmission of those reports.': {
        'risks': ['Insufficient monitoring & alerting', 'Insufficient logging'],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22'],
    },
    'Article 11.1: As part of the ICT risk management framework referred to in Article 6(1) and based on the identification requirements set out in Article 8, financial entities shall put in place a comprehensive ICT business continuity policy, which may be adopted as a dedicated specific policy, forming an integral part of the overall business continuity policy of the financial entity.': {
        'risks': ['Business interruption', 'Improper response to incidents'],
        'controls': ['BCD-1', 'BCD-3', 'IRM-1'],
        'policies': ['POL-10', 'POL-20'],
    },
    'Article 11.2: Financial entities shall implement the ICT business continuity policy through dedicated, appropriate and documented arrangements, plans, procedures and mechanisms aiming to:': {
        'risks': ['Business interruption', 'Reduction in productivity'],
        'controls': ['BCD-1', 'BCD-2'],
        'policies': ['POL-10', 'POL-18'],
    },
    'Article 11.3: As part of the ICT risk management framework referred to in Article 6(1), financial entities shall implement associated ICT response and recovery plans which, in the case of financial entities other than microenterprises, shall be subject to independent internal audit reviews.': {
        'risks': ['Business interruption', 'Improper response to incidents'],
        'controls': ['BCD-1', 'IRM-1', 'IRM-4'],
        'policies': ['POL-10', 'POL-20'],
    },
    'Article 11.4: Financial entities shall put in place, maintain and periodically test appropriate ICT business continuity plans, notably with regard to critical or important functions outsourced or contracted through arrangements with ICT third-party service providers.': {
        'risks': ['Business interruption', 'Data loss'],
        'controls': ['BCD-1', 'DRC-1', 'DRC-4'],
        'policies': ['POL-10', 'POL-9'],
    },
    'Article 11.5: As part of the overall business continuity policy, financial entities shall conduct a business impact analysis (BIA) of their exposures to severe business disruptions. Under the BIA, financial entities shall assess the potential impact of severe business disruptions by means of quantitative and qualitative criteria, using internal and external data and scenario analysis, as appropriate. The BIA shall consider the criticality of identified and mapped business functions, support processes, third-party dependencies and information assets, and their interdependencies. Financial entities shall ensure that ICT assets and ICT services are designed and used in full alignment with the BIA, in particular with regard to adequately ensuring the redundancy of all critical components.': {
        'risks': ['Business interruption', 'Inability to support business processes'],
        'controls': ['BCD-1', 'RSM-2'],
        'policies': ['POL-10', 'POL-30'],
    },
    'Article 11.6: As part of their comprehensive ICT risk management, financial entities shall:': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-1', 'IRM-4', 'ALM-1'],
        'policies': ['POL-20', 'POL-22'],
    },
    'Article 11.7: Financial entities, other than microenterprises, shall have a crisis management function, which, in the event of activation of their ICT business continuity plans or ICT response and recovery plans, shall, inter alia, set out clear procedures to manage internal and external crisis communications in accordance with Article 14.': {
        'risks': ['Business interruption', 'Improper response to incidents'],
        'controls': ['BCD-1', 'IRM-1', 'CCI-3'],
        'policies': ['POL-10', 'POL-20'],
    },
    'Article 11.8: Financial entities shall keep readily accessible records of activities before and during disruption events when their ICT business continuity plans and ICT response and recovery plans are activated.': {
        'risks': ['Insufficient logging', 'Inability to investigate / prosecute incidents'],
        'controls': ['ALM-2', 'ALM-4', 'IRM-4'],
        'policies': ['POL-22', 'POL-20'],
    },
    'Article 11.9: Central securities depositories shall provide the competent authorities with copies of the results of the ICT business continuity tests, or of similar exercises.': {
        'risks': ['Fines and judgements', 'Inadequate internal practices'],
        'controls': ['BCD-1', 'GOV-8'],
        'policies': ['POL-10'],
    },
    'Article 11.10:  Financial entities, other than microenterprises, shall report to the competent authorities, upon their request, an estimation of aggregated annual costs and losses caused by major ICT-related incidents.': {
        'risks': ['Expense associated with managing a loss event', 'Business interruption'],
        'controls': ['IRM-4', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 11.11:  In accordance with Article 16 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010, the ESAs, through the Joint Committee, shall by 17 July 2024 develop common guidelines on the estimation of aggregated annual costs and losses referred to in paragraph 10.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-10'],
    },
    'Article 12.1: For the purpose of ensuring the restoration of ICT systems and data with minimum downtime, limited disruption and loss, as part of their ICT risk management framework, financial entities shall develop and document:': {
        'risks': ['Data loss', 'Business interruption'],
        'controls': ['DRC-1', 'DRC-4', 'DRC-5'],
        'policies': ['POL-9', 'POL-18'],
    },
    'Article 12.2: Financial entities shall set up backup systems that can be activated in accordance with the backup policies and procedures, as well as restoration and recovery procedures and methods. The activation of backup systems shall not jeopardise the security of the network and information systems or the availability, authenticity, integrity or confidentiality of data. Testing of the backup procedures and restoration and recovery procedures and methods shall be undertaken periodically.': {
        'risks': ['Data loss', 'Availability & Disaster recovery'],
        'controls': ['DRC-1', 'DRC-2', 'BCD-2'],
        'policies': ['POL-9', 'POL-8'],
    },
    'Article 12.3: When restoring backup data using own systems, financial entities shall use ICT systems that are physically and logically segregated from the source ICT system. The ICT systems shall be securely protected from any unauthorised access or ICT corruption and allow for the timely restoration of services making use of data and system backups as necessary.': {
        'risks': ['Data loss / corruption', 'Data loss'],
        'controls': ['DRC-1', 'DRC-2'],
        'policies': ['POL-9'],
    },
    'Article 12.4: Financial entities, other than microenterprises, shall maintain redundant ICT capacities equipped with resources, capabilities and functions that are adequate to ensure business needs. Microenterprises shall assess the need to maintain such redundant ICT capacities based on their risk profile.': {
        'risks': ['Availability & Disaster recovery', 'Business interruption'],
        'controls': ['BCD-2', 'DRC-1'],
        'policies': ['POL-8', 'POL-18'],
    },
    'Article 12.5: Central securities depositories shall maintain at least one secondary processing site endowed with adequate resources, capabilities, functions and staffing arrangements to ensure business needs.': {
        'risks': ['Availability & Disaster recovery', 'Business interruption'],
        'controls': ['BCD-2', 'DRC-1', 'DRC-3'],
        'policies': ['POL-8', 'POL-18'],
    },
    'Article 12.6: In determining the recovery time and recovery point objectives for each function, financial entities shall take into account whether it is a critical or important function and the potential overall impact on market efficiency. Such time objectives shall ensure that, in extreme scenarios, the agreed service levels are met.': {
        'risks': ['Business interruption', 'Data loss'],
        'controls': ['BCD-1', 'DRC-1'],
        'policies': ['POL-10', 'POL-9'],
    },
    'Article 12.7: When recovering from an ICT-related incident, financial entities shall perform necessary checks, including any multiple checks and reconciliations, in order to ensure that the highest level of data integrity is maintained. These checks shall also be performed when reconstructing data from external stakeholders, in order to ensure that all data is consistent between systems.': {
        'risks': ['Data loss / corruption', 'Improper response to incidents'],
        'controls': ['DRC-1', 'IRM-1'],
        'policies': ['POL-9', 'POL-20'],
    },
    'Article 13.1: Financial entities shall have in place capabilities and staff to gather information on vulnerabilities and cyber threats, ICT-related incidents, in particular cyber-attacks, and analyse the impact they are likely to have on their digital operational resilience.': {
        'risks': ['Lack of cybersecurity awareness', 'Inability to maintain situational awareness'],
        'controls': ['IRM-1', 'ALM-1'],
        'policies': ['POL-20', 'POL-22'],
    },
    'Article 13.2: Financial entities shall put in place post ICT-related incident reviews after a major ICT-related incident disrupts their core activities, analysing the causes of disruption and identifying required improvements to the ICT operations or within the ICT business continuity policy referred to in Article 11.': {
        'risks': ['Improper response to incidents', 'Ineffective remediation actions'],
        'controls': ['IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'Article 13.3: Lessons derived from the digital operational resilience testing carried out in accordance with Articles 26 and 27 and from real life ICT-related incidents, in particular cyber-attacks, along with challenges faced upon the activation of ICT business continuity plans and ICT response and recovery plans, together with relevant information exchanged with counterparts and assessed during supervisory reviews, shall be duly incorporated on a continuous basis into the ICT risk assessment process. Those findings shall form the basis for appropriate reviews of relevant components of the ICT risk management framework referred to in Article 6(1).': {
        'risks': ['Unmitigated vulnerabilities', 'Ineffective remediation actions'],
        'controls': ['CVM-1', 'CVM-2', 'GOV-12'],
        'policies': ['POL-35'],
    },
    'Article 13.4: Financial entities shall monitor the effectiveness of the implementation of their digital operational resilience strategy set out in Article 6(8). They shall map the evolution of ICT risk over time, analyse the frequency, types, magnitude and evolution of ICT-related incidents, in particular cyber-attacks and their patterns, with a view to understanding the level of ICT risk exposure, in particular in relation to critical or important functions, and enhance the cyber maturity and preparedness of the financial entity.': {
        'risks': ['Inadequate internal practices', 'Lack of oversight of internal controls'],
        'controls': ['GOV-3', 'GOV-12'],
        'policies': ['POL-21'],
    },
    'Article 13.5: Senior ICT staff shall report at least yearly to the management body on the findings referred to in paragraph 3 and put forward recommendations.': {
        'risks': ['Lack of oversight of internal controls', 'Inadequate internal practices'],
        'controls': ['GOV-10', 'GOV-12'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 13.6: Financial entities shall develop ICT security awareness programmes and digital operational resilience training as compulsory modules in their staff training schemes. Those programmes and training shall be applicable to all employees and to senior management staff, and shall have a level of complexity commensurate to the remit of their functions. Where appropriate, financial entities shall also include ICT third-party service providers in their relevant training schemes in accordance with Article 30(2), point (i).': {
        'risks': ['Lack of cybersecurity awareness', 'Lack of a security-minded workforce'],
        'controls': ['HRM-8', 'GOV-1'],
        'policies': ['POL-21', 'POL-27'],
    },
    'Article 13.7: Financial entities, other than microenterprises, shall monitor relevant technological developments on a continuous basis, also with a view to understanding the possible impact of the deployment of such new technologies on ICT security requirements and digital operational resilience. They shall keep up-to-date with the latest ICT risk management processes, in order to effectively combat current or new forms of cyber-attacks.': {
        'risks': ['Unmitigated vulnerabilities', 'Lack of cybersecurity awareness'],
        'controls': ['CVM-1', 'GOV-3'],
        'policies': ['POL-35', 'POL-21'],
    },
    'Article 14.1: As part of the ICT risk management framework referred to in Article 6(1), financial entities shall have in place crisis communication plans enabling a responsible disclosure of, at least, major ICT-related incidents or vulnerabilities to clients and counterparts as well as to the public, as appropriate.': {
        'risks': ['Inadequate internal practices', 'Inability to maintain situational awareness'],
        'controls': ['CCI-3', 'IRM-3'],
        'policies': ['POL-20', 'POL-21'],
    },
    'Article 14.2: As part of the ICT risk management framework, financial entities shall implement communication policies for internal staff and for external stakeholders. Communication policies for staff shall take into account the need to differentiate between staff involved in ICT risk management, in particular the staff responsible for response and recovery, and staff that needs to be informed.': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['CCI-3', 'IRM-3', 'IRM-1'],
        'policies': ['POL-20'],
    },
    'Article 14.3: At least one person in the financial entity shall be tasked with implementing the communication strategy for ICT-related incidents and fulfil the public and media function for that purpose.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['CCI-3', 'HRM-11'],
        'policies': ['POL-20'],
    },
    'Article 15.1: Further harmonisation of ICT risk management tools, methods, processes and policies': {
        'risks': ['Fines and judgements', 'Outdated policies for Process Management'],
        'controls': ['GOV-8', 'GOV-1'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 16.1: Articles 5 to 15 of this Regulation shall not apply to small and non-interconnected investment firms, payment institutions exempted pursuant to Directive (EU) 2015/2366; institutions exempted pursuant to Directive 2013/36/EU in respect of which Member States have decided not to apply the option referred to in Article 2(4) of this Regulation; electronic money institutions exempted pursuant to Directive 2009/110/EC; and small institutions for occupational retirement provision.': {
        'risks': ['Inadequate internal practices', 'Incorrect controls scoping'],
        'controls': ['GOV-1', 'RSM-2'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 16.2: The ICT risk management framework referred to in paragraph 1, second subparagraph, point (a), shall be documented and reviewed periodically and upon the occurrence of major ICT-related incidents in compliance with supervisory instructions. It shall be continuously improved on the basis of lessons derived from implementation and monitoring. A report on the review of the ICT risk management framework shall be submitted to the competent authority upon its request.': {
        'risks': ['Outdated policies for Process Management', 'Inadequate internal practices'],
        'controls': ['GOV-1', 'GOV-5', 'RSM-2'],
        'policies': ['POL-21', 'POL-30'],
    },
    'Article 16.3: The ESAs shall, through the Joint Committee, in consultation with the ENISA, develop common draft regulatory technical standards in order to:': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-21'],
    },
    'Article 17.1: Financial entities shall define, establish and implement an ICT-related incident management process to detect, manage and notify ICT-related incidents.': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['IRM-1', 'IRM-4', 'IRM-6'],
        'policies': ['POL-20'],
    },
    'Article 17.2: Financial entities shall record all ICT-related incidents and significant cyber threats. Financial entities shall establish appropriate procedures and processes to ensure a consistent and integrated monitoring, handling and follow-up of ICT-related incidents, to ensure that root causes are identified, documented and addressed in order to prevent the occurrence of such incidents.': {
        'risks': ['Insufficient logging', 'Inability to investigate / prosecute incidents'],
        'controls': ['IRM-4', 'ALM-2'],
        'policies': ['POL-20', 'POL-22'],
    },
    'Article 17.3: The ICT-related incident management process referred to in paragraph 1 shall:': {
        'risks': ['Improper response to incidents', 'Ineffective remediation actions'],
        'controls': ['IRM-1', 'IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'Article 18.1: Financial entities shall classify ICT-related incidents and shall determine their impact based on the following criteria:': {
        'risks': ['Improper response to incidents', 'Business interruption'],
        'controls': ['IRM-4', 'IRM-1'],
        'policies': ['POL-20'],
    },
    "Article 18.2: Financial entities shall classify cyber threats as significant based on the criticality of the services at risk, including the financial entity's transactions and operations, number and/or relevance of clients or financial counterparts targeted and the geographical spread of the areas at risk.": {
        'risks': ['Insufficient monitoring & alerting', 'Inability to maintain situational awareness'],
        'controls': ['IRM-4', 'ALM-1'],
        'policies': ['POL-20'],
    },
    'Article 18.3: The ESAs shall, through the Joint Committee and in consultation with the ECB and ENISA, develop common draft regulatory technical standards further specifying the following:': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 18.4: When developing the common draft regulatory technical standards referred to in paragraph 3 of this Article, the ESAs shall take into account the criteria set out in Article 4(2), as well as international standards, guidance and specifications developed and published by ENISA, including, where appropriate, specifications for other economic sectors. For the purposes of applying the criteria set out in Article 4(2), the ESAs shall duly consider the need for microenterprises and small and medium-sized enterprises to mobilise sufficient resources and capabilities to ensure that ICT-related incidents are managed swiftly.': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 19.1: Financial entities shall report major ICT-related incidents to the relevant competent authority as referred to in Article 46 in accordance with paragraph 4 of this Article.': {
        'risks': ['Improper response to incidents', 'Fines and judgements'],
        'controls': ['IRM-4', 'IRM-5', 'CCI-3'],
        'policies': ['POL-20'],
    },
    'Article 19.2: Financial entities may, on a voluntary basis, notify significant cyber threats to the relevant competent authority when they deem the threat to be of relevance to the financial system, service users or clients. The relevant competent authority may provide such information to other relevant authorities referred to in paragraph 6.': {
        'risks': ['Insufficient monitoring & alerting'],
        'controls': ['IRM-4', 'CCI-3'],
        'policies': ['POL-20'],
    },
    'Article 19.3: Where a major ICT-related incident occurs and has an impact on the financial interests of clients, financial entities shall, without undue delay as soon as they become aware of it, inform their clients about the major ICT-related incident and about the measures that have been taken to mitigate the adverse effects of such incident.': {
        'risks': ['Business interruption', 'Diminished reputation'],
        'controls': ['IRM-4', 'CCI-3'],
        'policies': ['POL-20'],
    },
    'Article 19.4: Financial entities shall, within the time limits to be laid down in accordance with Article 20, first paragraph, point (a), point (ii), submit the following to the relevant competent authority:': {
        'risks': ['Improper response to incidents', 'Fines and judgements'],
        'controls': ['IRM-4', 'CCI-3'],
        'policies': ['POL-20'],
    },
    'Article 19.5: Financial entities may outsource, in accordance with Union and national sectoral law, the reporting obligations under this Article to a third-party service provider. In case of such outsourcing, the financial entity remains fully responsible for the fulfilment of the incident reporting requirements.': {
        'risks': ['Inadequate third-party practices'],
        'controls': ['IRM-5', 'TPM-1'],
        'policies': ['POL-20', 'POL-34'],
    },
    'Article 19.6: Upon receipt of the initial notification and of each report referred to in paragraph 4, the competent authority shall, in a timely manner, provide details of the major ICT-related incident to the following recipients based, as applicable, on their respective competences:': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'CCI-3'],
        'policies': ['POL-20'],
    },
    'Article 19.7: Following receipt of information in accordance with paragraph 6, EBA, ESMA or EIOPA and the ECB, in consultation with ENISA and in cooperation with the relevant competent authority, shall assess whether the major ICT-related incident is relevant for competent authorities in other Member States. Following that assessment, EBA, ESMA or EIOPA shall, as soon as possible, notify relevant competent authorities in other Member States accordingly. The ECB shall notify the members of the European System of Central Banks on issues relevant to the payment system. Based on that notification, the competent authorities shall, where appropriate, take all of the necessary measures to protect the immediate stability of the financial system.': {
        'risks': ['Fines and judgements'],
        'controls': ['CCI-3', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 19.8: The notification to be done by ESMA pursuant to paragraph 7 of this Article shall be without prejudice to the responsibility of the competent authority to urgently transmit the details of the major ICT-related incident to the relevant authority in the host Member State, where a central securities depository has significant cross-border activity in the host Member State, the major ICT-related incident is likely to have severe consequences for the financial markets of the host Member State and where there are cooperation arrangements among competent authorities related to the supervision of financial entities.': {
        'risks': ['Fines and judgements'],
        'controls': ['CCI-3', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 20.1: Harmonisation of reporting content and templates': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 21.1: The ESAs, through the Joint Committee, and in consultation with the ECB and ENISA, shall prepare a joint report assessing the feasibility of further centralisation of incident reporting through the establishment of a single EU Hub for major ICT-related incident reporting by financial entities. The joint report shall explore ways to facilitate the flow of ICT-related incident reporting, reduce associated costs and underpin thematic analyses with a view to enhancing supervisory convergence.': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 21.2: The joint report referred to in paragraph 1 shall comprise at least the following elements:': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 21.3: The ESAs shall submit the report referred to in paragraph 1 to the European Parliament, to the Council and to the Commission by 17 January 2025.': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'GOV-8'],
        'policies': ['POL-20'],
    },
    'Article 22.1: Without prejudice to the technical input, advice or remedies and subsequent follow-up which may be provided, where applicable, in accordance with national law, by the CSIRTs under Directive (EU) 2022/2555, the competent authority shall, upon receipt of the initial notification and of each report as referred to in Article 19(4), acknowledge receipt and may, where feasible, provide in a timely manner relevant and proportionate feedback or high-level guidance to the financial entity, in particular by making available any relevant anonymised information and intelligence on similar threats, and may discuss remedies applied at the level of the financial entity and ways to minimise and mitigate adverse impact across the financial sector. Without prejudice to the supervisory feedback received, financial entities shall remain fully responsible for the handling and for consequences of the ICT-related incidents reported pursuant to Article 19(1).': {
        'risks': ['Ineffective remediation actions', 'Fines and judgements'],
        'controls': ['IRM-2', 'GOV-3'],
        'policies': ['POL-20'],
    },
    'Article 22.2: The ESAs shall, through the Joint Committee, on an anonymised and aggregated basis, report yearly on major ICT-related incidents, the details of which shall be provided by competent authorities in accordance with Article 19(6), setting out at least the number of major ICT-related incidents, their nature and their impact on the operations of financial entities or clients, remedial actions taken and costs incurred.': {
        'risks': ['Fines and judgements'],
        'controls': ['IRM-4', 'CCI-3'],
        'policies': ['POL-20'],
    },
    'Article 23.1: Operational or security payment-related incidents concerning credit institutions,  payment institutions, account information service providers, and electronic money institutions': {
        'risks': ['Business interruption', 'Fines and judgements'],
        'controls': ['IRM-4', 'CCI-3'],
        'policies': ['POL-20'],
    },
    'Article 24.1: For the purpose of assessing preparedness for handling ICT-related incidents, of identifying weaknesses, deficiencies and gaps in digital operational resilience, and of promptly implementing corrective measures, financial entities, other than microenterprises, shall, taking into account the criteria set out in Article 4(2), establish, maintain and review a sound and comprehensive digital operational resilience testing programme as an integral part of the ICT risk-management framework referred to in Article 6.': {
        'risks': ['Unmitigated vulnerabilities', 'Lack of design reviews & security testing'],
        'controls': ['CVM-1', 'CVM-2', 'GOV-12'],
        'policies': ['POL-35', 'POL-36'],
    },
    'Article 24.2: The digital operational resilience testing programme shall include a range of assessments, tests, methodologies, practices and tools to be applied in accordance with Articles 25 and 26.': {
        'risks': ['Unmitigated vulnerabilities', 'Lack of design reviews & security testing'],
        'controls': ['CVM-1', 'CVM-2', 'APD-4'],
        'policies': ['POL-35', 'POL-6'],
    },
    'Article 24.3: When conducting the digital operational resilience testing programme referred to in paragraph 1 of this Article, financial entities, other than microenterprises, shall follow a risk-based approach taking into account the criteria set out in Article 4(2) duly considering the evolving landscape of ICT risk, any specific risks to which the financial entity concerned is or might be exposed, the criticality of information assets and of services provided, as well as any other factor the financial entity deems appropriate.': {
        'risks': ['Unmitigated vulnerabilities', 'Incorrect controls scoping'],
        'controls': ['CVM-1', 'CVM-2'],
        'policies': ['POL-35'],
    },
    'Article 24.4: Financial entities, other than microenterprises, shall ensure that tests are undertaken by independent parties, whether internal or external. Where tests are undertaken by an internal tester, financial entities shall dedicate sufficient resources and ensure that conflicts of interest are avoided throughout the design and execution phases of the test.': {
        'risks': ['Lack of design reviews & security testing'],
        'controls': ['CVM-1', 'CVM-2'],
        'policies': ['POL-35'],
    },
    'Article 24.5: Financial entities, other than microenterprises, shall establish procedures and policies to prioritise, classify and remedy all issues revealed throughout the performance of the tests and shall establish internal validation methodologies to ascertain that all identified weaknesses, deficiencies or gaps are fully addressed.': {
        'risks': ['Ineffective remediation actions', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2', 'GOV-1'],
        'policies': ['POL-35'],
    },
    'Article 24.6: Financial entities, other than microenterprises, shall ensure, at least yearly, that appropriate tests are conducted on all ICT systems and applications supporting critical or important functions.': {
        'risks': ['Unmitigated vulnerabilities', 'Lack of design reviews & security testing'],
        'controls': ['CVM-1', 'APD-4'],
        'policies': ['POL-35', 'POL-6'],
    },
    'Article 25.1: The digital operational resilience testing programme referred to in Article 24 shall provide, in accordance with the criteria set out in Article 4(2), for the execution of appropriate tests, such as vulnerability assessments and scans, open source analyses, network security assessments, gap analyses, physical security reviews, questionnaires and scanning software solutions, source code reviews where feasible, scenario-based tests, compatibility testing, performance testing, end-to-end testing and penetration testing.': {
        'risks': ['Unmitigated vulnerabilities', 'Security misconfiguration of APIs / Applications'],
        'controls': ['CVM-1', 'CVM-2', 'APD-4'],
        'policies': ['POL-35', 'POL-6'],
    },
    'Article 25.2: Central securities depositories and central counterparties shall perform vulnerability assessments before any deployment or redeployment of new or existing applications and infrastructure components, and ICT services supporting critical or important functions of the financial entity.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1', 'CVM-2'],
        'policies': ['POL-35'],
    },
    "Article 25.3: Microenterprises shall perform the tests referred to in paragraph 1 by combining a risk-based approach with a strategic planning of ICT testing, by duly considering the need to maintain a balanced approach between the scale of resources and the time to be allocated to the ICT testing provided for in this Article, on the one hand, and the urgency, type of risk, criticality of information assets and of services provided, as well as any other relevant factor, including the financial entity's ability to take calculated risks, on the other hand.": {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-1'],
        'policies': ['POL-35'],
    },
    'Article 26.1: Financial entities, other than entities referred to in Article 16(1), first subparagraph, and other than microenterprises, which are identified in accordance with paragraph 8, third subparagraph, of this Article, shall carry out at least every 3 years advanced testing by means of TLPT. Based on the risk profile of the financial entity and taking into account operational circumstances, the competent authority may, where necessary, request the financial entity to reduce or increase this frequency.': {
        'risks': ['Unmitigated vulnerabilities', 'Lack of design reviews & security testing'],
        'controls': ['CVM-2', 'GOV-12'],
        'policies': ['POL-35', 'POL-36'],
    },
    'Article 26.2: Each threat-led penetration test shall cover several or all critical or important functions of a financial entity, and shall be performed on live production systems supporting such functions.': {
        'risks': ['Unmitigated vulnerabilities', 'System compromise'],
        'controls': ['CVM-2', 'APD-4'],
        'policies': ['POL-35'],
    },
    'Article 26.3: Where ICT third-party service providers are included in the scope of TLPT, the financial entity shall take the necessary measures and safeguards to ensure the participation of such ICT third-party service providers in the TLPT and shall retain at all times full responsibility for ensuring compliance with this Regulation.': {
        'risks': ['Third-party cybersecurity exposure', 'Unmitigated vulnerabilities'],
        'controls': ['CVM-2', 'TPM-3'],
        'policies': ['POL-35', 'POL-34'],
    },
    'Article 26.4: Without prejudice to paragraph 2, first and second subparagraphs, where the participation of an ICT third-party service provider in the TLPT, referred to in paragraph 3, is reasonably expected to have an adverse impact on the quality or security of services delivered by the ICT third-party service provider to customers that are entities falling outside the scope of this Regulation, or on the confidentiality of the data related to such services, the financial entity and the ICT third-party service provider may agree in writing that the ICT third-party service provider directly enters into contractual arrangements with an external tester, for the purpose of conducting, under the direction of one designated financial entity, a pooled TLPT involving several financial entities (pooled testing) to which the ICT third-party service provider provides ICT services.': {
        'risks': ['Unmitigated vulnerabilities'],
        'controls': ['CVM-2', 'APD-4'],
        'policies': ['POL-35'],
    },
    'Article 26.5: Financial entities shall, with the cooperation of ICT third-party service providers and other parties involved, including the testers but excluding the competent authorities, apply effective risk management controls to mitigate the risks of any potential impact on data, damage to assets, and disruption to critical or important functions, services or operations at the financial entity itself, its counterparts or to the financial sector.': {
        'risks': ['Unmitigated vulnerabilities', 'Ineffective remediation actions'],
        'controls': ['CVM-2', 'IRM-1'],
        'policies': ['POL-35'],
    },
    'Article 26.6: At the end of the testing, after reports and remediation plans have been agreed, the financial entity and, where applicable, the external testers shall provide to the authority, designated in accordance with paragraph 9 or 10, a summary of the relevant findings, the remediation plans and the documentation demonstrating that the TLPT has been conducted in accordance with the requirements.': {
        'risks': ['Ineffective remediation actions'],
        'controls': ['CVM-2', 'GOV-12'],
        'policies': ['POL-35'],
    },
    'Article 26.7: Authorities shall provide financial entities with an attestation confirming that the test was performed in accordance with the requirements as evidenced in the documentation in order to allow for mutual recognition of threat led penetration tests between competent authorities. The financial entity shall notify the relevant competent authority of the attestation, the summary of the relevant findings and the remediation plans.': {
        'risks': ['Fines and judgements'],
        'controls': ['CVM-2', 'GOV-8'],
        'policies': ['POL-35'],
    },
    'Article 26.8: Financial entities shall contract testers for the purposes of undertaking TLPT in accordance with Article 27. When financial entities use internal testers for the purposes of undertaking TLPT, they shall contract external testers every three tests.': {
        'risks': ['Inadequate third-party practices', 'Lack of design reviews & security testing'],
        'controls': ['CVM-2', 'TPM-1'],
        'policies': ['POL-35', 'POL-34'],
    },
    'Article 26.9: Member States may designate a single public authority in the financial sector to be responsible for TLPT-related matters in the financial sector at national level and shall entrust it with all competences and tasks to that effect.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-35'],
    },
    'Article 26.10:  In the absence of a designation in accordance with paragraph 9 of this Article, and without prejudice to the power to identify the financial entities that are required to perform TLPT, a competent authority may delegate the exercise of some or all of the tasks referred to in this Article and Article 27 to another national authority in the financial sector.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-35'],
    },
    'Article 26.11:  The ESAs shall, in agreement with the ECB, develop joint draft regulatory technical standards in accordance with the TIBER-EU framework in order to specify further:': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-35', 'POL-36'],
    },
    'Article 27.1: Financial entities shall only use testers for the carrying out of TLPT, that:': {
        'risks': ['Lack of design reviews & security testing', 'Inadequate third-party practices'],
        'controls': ['CVM-2', 'TPM-1'],
        'policies': ['POL-35', 'POL-34'],
    },
    'Article 27.2: When using internal testers, financial entities shall ensure that, in addition to the requirements in paragraph 1, the following conditions are met:': {
        'risks': ['Lack of design reviews & security testing'],
        'controls': ['CVM-2', 'GOV-12'],
        'policies': ['POL-35'],
    },
    'Article 27.3: Financial entities shall ensure that contracts concluded with external testers require a sound management of the TLPT results and that any data processing thereof, including any generation, store, aggregation, draft, report, communication or destruction, do not create risks to the financial entity.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'CVM-2'],
        'policies': ['POL-34', 'POL-35'],
    },
    'Article 28.1: Financial entities shall manage ICT third-party risk as an integral component of ICT risk within their ICT risk management framework as referred to in Article 6(1), and in accordance with the following principles:': {
        'risks': ['Exposure to third party vendors', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 28.2: As part of their ICT risk management framework, financial entities, other than entities referred to in Article 16(1), first subparagraph, and other than microenterprises, shall adopt, and regularly review, a strategy on ICT third-party risk, taking into account the multi-vendor strategy referred to in Article 6(9), where applicable. The strategy on ICT third-party risk shall include a policy on the use of ICT services supporting critical or important functions provided by ICT third-party service providers and shall apply on an individual basis and, where relevant, on a sub-consolidated and consolidated basis. The management body shall, on the basis of an assessment of the overall risk profile of the financial entity and the scale and complexity of the business services, regularly review the risks identified in respect to contractual arrangements on the use of ICT services supporting critical or important functions.': {
        'risks': ['Exposure to third party vendors', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'TPM-4', 'GOV-8'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 28.3: As part of their ICT risk management framework, financial entities shall maintain and update at entity level, and at sub-consolidated and consolidated levels, a register of information in relation to all contractual arrangements on the use of ICT services provided by ICT third-party service providers.': {
        'risks': ['Exposure to third party vendors', 'Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3', 'AST-1'],
        'policies': ['POL-34'],
    },
    'Article 28.4: Before entering into a contractual arrangement on the use of ICT services, financial entities shall:': {
        'risks': ['Third-party cybersecurity exposure', 'Reliance on the third-party'],
        'controls': ['TPM-2', 'TPM-3', 'GOV-6'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 28.5: Financial entities may only enter into contractual arrangements with ICT third-party service providers that comply with appropriate information security standards. When those contractual arrangements concern critical or important functions, financial entities shall, prior to concluding the arrangements, take due consideration of the use, by ICT third-party service providers, of the most up-to-date and highest quality information security standards.': {
        'risks': ['Inadequate third-party practices', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-2'],
        'policies': ['POL-34'],
    },
    'Article 28.6: In exercising access, inspection and audit rights over the ICT third-party service provider, financial entities shall, on the basis of a risk-based approach, pre-determine the frequency of audits and inspections as well as the areas to be audited through adhering to commonly accepted audit standards in line with any supervisory instruction on the use and incorporation of such audit standards.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-2', 'GOV-12'],
        'policies': ['POL-34'],
    },
    'Article 28.7: Financial entities shall ensure that contractual arrangements on the use of ICT services may be terminated in any of the following circumstances:': {
        'risks': ['Exposure to third party vendors', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'Article 28.8: For ICT services supporting critical or important functions, financial entities shall put in place exit strategies. The exit strategies shall take into account risks that may emerge at the level of ICT third-party service providers, in particular a possible failure on their part, a deterioration of the quality of the ICT services provided, any business disruption due to inappropriate or failed provision of ICT services or any material risk arising in relation to the appropriate and continuous deployment of the respective ICT service, or the termination of contractual arrangements with ICT third-party service providers under any of the circumstances listed in paragraph 7.': {
        'risks': ['Reliance on the third-party', 'Business interruption'],
        'controls': ['TPM-3', 'BCD-1'],
        'policies': ['POL-34', 'POL-10'],
    },
    'Article 28.9: The ESAs shall, through the Joint Committee, develop draft implementing technical standards to establish the standard templates for the purposes of the register of information referred to in paragraph 3, including information that is common to all contractual arrangements on the use of ICT services. The ESAs shall submit those draft implementing technical standards to the Commission by 17 January 2024.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'Article 28.10:  The ESAs shall, through the Joint Committee, develop draft regulatory technical standards to further specify the detailed content of the policy referred to in paragraph 2 in relation to the contractual arrangements on the use of ICT services supporting critical or important functions provided by ICT third-party service providers.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'Article 29.1: When performing the identification and assessment of risks referred to in Article 28(4), point (c), financial entities shall also take into account whether the envisaged conclusion of a contractual arrangement in relation to ICT services supporting critical or important functions would lead to any of the following:': {
        'risks': ['Reliance on the third-party', 'Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3', 'GOV-6'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 29.2: Where the contractual arrangements on the use of ICT services supporting critical or important functions include the possibility that an ICT third-party service provider further subcontracts ICT services supporting a critical or important function to other ICT third-party service providers, financial entities shall weigh benefits and risks that may arise in connection with such subcontracting, in particular in the case of an ICT subcontractor established in a third-country.': {
        'risks': ['Reliance on the third-party', 'Business interruption'],
        'controls': ['TPM-3', 'BCD-1'],
        'policies': ['POL-34', 'POL-10'],
    },
    'Article 30.1: The rights and obligations of the financial entity and of the ICT third-party service provider shall be clearly allocated and set out in writing. The full contract shall include the service level agreements and be documented in one written document which shall be available to the parties on paper, or in a document with another downloadable, durable and accessible format.': {
        'risks': ['Third-party compliance / legal exposure', 'Exposure to third party vendors'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'Article 30.2: The contractual arrangements on the use of ICT services shall include at least the following elements:': {
        'risks': ['Inadequate third-party practices', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'Article 30.3: The contractual arrangements on the use of ICT services supporting critical or important functions shall include, in addition to the elements referred to in paragraph 2, at least the following:': {
        'risks': ['Reliance on the third-party', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-1', 'TPM-4', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 30.4: When negotiating contractual arrangements, financial entities and ICT third-party service providers shall consider the use of standard contractual clauses developed by public authorities for specific services.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'Article 30.5: The ESAs shall, through the Joint Committee, develop draft regulatory technical standards to specify further the elements referred to in paragraph 2, point (a), which a financial entity needs to determine and assess when subcontracting ICT services supporting critical or important functions.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'Article 31.1: The ESAs, through the Joint Committee and upon recommendation from the Oversight Forum established pursuant to Article 32(1), shall:': {
        'risks': ['Reliance on the third-party', 'Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.2: The designation referred to in paragraph 1, point (a), shall be based on all of the following criteria in relation to ICT services provided by the ICT third-party service provider:': {
        'risks': ['Reliance on the third-party', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.3: Where the ICT third-party service provider belongs to a group, the criteria referred to in paragraph 2 shall be considered in relation to the ICT services provided by the group as a whole.': {
        'risks': ['Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.4: Critical ICT third-party service providers which are part of a group shall designate one legal person as a coordination point to ensure adequate representation and communication with the Lead Overseer.': {
        'risks': ['Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3'],
        'policies': ['POL-34'],
    },
    'Article 31.5: The Lead Overseer shall notify the ICT third-party service provider of the outcome of the assessment leading to the designation referred in paragraph 1, point (a). Within 6 weeks from the date of the notification, the ICT third-party service provider may submit to the Lead Overseer a reasoned statement with any relevant information for the purposes of the assessment. The Lead Overseer shall consider the reasoned statement and may request additional information to be submitted within 30 calendar days of the receipt of such statement.': {
        'risks': ['Fines and judgements'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.6: The Commission is empowered to adopt a delegated act in accordance with Article 57 to supplement this Regulation by specifying further the criteria referred to in paragraph 2 of this Article, by 17 July 2024.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.7: The designation referred to in paragraph 1, point (a), shall not be used until the Commission has adopted a delegated act in accordance with paragraph 6.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.8: The designation referred to in paragraph 1, point (a), shall not apply to the following:': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.9: The ESAs, through the Joint Committee, shall establish, publish and update yearly the list of critical ICT third-party service providers at Union level.': {
        'risks': ['Reliance on the third-party'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.10:  For the purposes of paragraph 1, point (a), competent authorities shall, on a yearly and aggregated basis, transmit the reports referred to in Article 28(3), third subparagraph, to the Oversight Forum established pursuant to Article 32. The Oversight Forum shall assess the ICT third-party dependencies of financial entities based on the information received from the competent authorities.': {
        'risks': ['Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 31.11:  The ICT third-party service providers that are not included in the list referred to in paragraph 9 may request to be designated as critical in accordance with paragraph 1, point (a).': {
        'risks': ['Third-party supply chain relationships, visibility and controls'],
        'controls': ['TPM-3'],
        'policies': ['POL-34'],
    },
    'Article 31.12:  Financial entities shall only make use of the services of an ICT third-party service provider established in a third country and which has been designated as critical in accordance with paragraph 1, point (a), if the latter has established a subsidiary in the Union within the 12 months following the designation.': {
        'risks': ['Reliance on the third-party', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-1', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'Article 31.13:  The critical ICT third-party service provider referred to in paragraph 12 shall notify the Lead Overseer of any changes to the structure of the management of the subsidiary established in the Union.': {
        'risks': ['Fines and judgements'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.1: The Joint Committee, in accordance with Article 57(1) of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010, shall establish the Oversight Forum as a sub-committee for the purposes of supporting the work of the Joint Committee and of the Lead Overseer referred to in Article 31(1), point (b), in the area of ICT third-party risk across financial sectors. The Oversight Forum shall prepare the draft joint positions and the draft common acts of the Joint Committee in that area.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['GOV-8', 'TPM-3'],
        'policies': ['POL-34', 'POL-30'],
    },
    'Article 32.2: The Oversight Forum shall, on a yearly basis, undertake a collective assessment of the results and findings of the oversight activities conducted for all critical ICT third-party service providers and promote coordination measures to increase the digital operational resilience of financial entities, foster best practices on addressing ICT concentration risk and explore mitigants for cross-sector risk transfers.': {
        'risks': ['Lack of oversight of third-party controls', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.3: The Oversight Forum shall submit comprehensive benchmarks for critical ICT third-party service providers to be adopted by the Joint Committee as joint positions of the ESAs in accordance with Article 56(1) of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.4: The Oversight Forum shall be composed of:': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.5: Each Member State shall designate the relevant competent authority whose staff member shall be the high-level representative referred in paragraph 4, first subparagraph, point (b), and shall inform the Lead Overseer thereof.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.6: The independent experts referred to in paragraph 4, second subparagraph, shall be appointed by the Oversight Forum from a pool of experts selected following a public and transparent application process.': {
        'risks': ['Lack of roles & responsibilities'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.7: In accordance with Article 16 of Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010, the ESAs shall by 17 July 2024 issue, for the purposes of this Section, guidelines on the cooperation between the ESAs and the competent authorities covering the detailed procedures and conditions for the allocation and execution of tasks between competent authorities and the ESAs and the details on the exchanges of information which are necessary for competent authorities to ensure the follow-up of recommendations pursuant to Article 35(1), point (d), addressed to critical ICT third-party service providers.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.8: The requirements set out in this Section shall be without prejudice to the application of Directive (EU) 2022/2555 and of other Union rules on oversight applicable to providers of cloud computing services.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 32.9: The ESAs, through the Joint Committee and based on preparatory work conducted by the Oversight Forum, shall, on yearly basis, submit a report on the application of this Section to the European Parliament, the Council and the Commission.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 33.1: The Lead Overseer, appointed in accordance with Article 31(1), point (b), shall conduct the oversight of the assigned critical ICT third-party service providers and shall be, for the purposes of all matters related to the oversight, the primary point of contact for those critical ICT third-party service providers.': {
        'risks': ['Lack of oversight of third-party controls', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 33.2: For the purposes of paragraph 1, the Lead Overseer shall assess whether each critical ICT third-party service provider has in place comprehensive, sound and effective rules, procedures, mechanisms and arrangements to manage the ICT risk which it may pose to financial entities.': {
        'risks': ['Third-party cybersecurity exposure', 'Inadequate third-party practices'],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'Article 33.3: The assessment referred to in paragraph 2 shall cover:': {
        'risks': ['Third-party cybersecurity exposure', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'Article 33.4: Based on the assessment referred to in paragraph 2, and in coordination with the Joint Oversight Network (JON) referred to in Article 34(1), the Lead Overseer shall adopt a clear, detailed and reasoned individual oversight plan describing the annual oversight objectives and the main oversight actions planned for each critical ICT third-party service provider. That plan shall be communicated yearly to the critical ICT third-party service provider.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 33.5: Once the annual oversight plans referred to in paragraph 4 have been adopted and notified to the critical ICT third-party service providers, competent authorities may take measures concerning such critical ICT third-party service providers only in agreement with the Lead Overseer.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 34.1: To ensure a consistent approach to oversight activities and with a view to enabling coordinated general oversight strategies and cohesive operational approaches and work methodologies, the three Lead Overseers appointed in accordance with Article 31(1), point (b), shall set up a JON to coordinate among themselves in the preparatory stages and to coordinate the conduct of oversight activities over their respective overseen critical ICT third-party service providers, as well as in the course of any action that may be needed pursuant to Article 42.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 34.2: For the purposes of paragraph 1, the Lead Overseers shall draw up a common oversight protocol specifying the detailed procedures to be followed for carrying out the day-to-day coordination and for ensuring swift exchanges and reactions. The protocol shall be periodically revised to reflect operational needs, in particular the evolution of practical oversight arrangements.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 34.3: The Lead Overseers may, on an ad-hoc basis, call on the ECB and ENISA to provide technical advice, share hands-on experience or join specific coordination meetings of the JON.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.1: For the purposes of carrying out the duties laid down in this Section, the Lead Overseer shall have the following powers in respect of the critical ICT third-party service providers:': {
        'risks': ['Lack of oversight of third-party controls', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.2: When exercising the powers referred to in this Article, the Lead Overseer shall:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.3: The Lead Overseer shall consult the Oversight Forum before exercising the powers referred to in paragraph 1.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.4: The Lead Overseer shall inform the JON of the outcome of the exercise of the powers referred to in paragraph 1, points (a) and (b). The Lead Overseer shall, without undue delay, transmit the reports referred to in paragraph 1, point (c), to the JON and to the competent authorities of the financial entities using the ICT services of that critical ICT third-party service provider.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.5: Critical ICT third-party service providers shall cooperate in good faith with the Lead Overseer, and assist it in the fulfilment of its tasks.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.6: In the event of whole or partial non-compliance with the measures required to be taken pursuant to the exercise of the powers under paragraph 1, points (a), (b) and (c), and after the expiry of a period of at least 30 calendar days from the date on which the critical ICT third-party service provider received notification of the respective measures, the Lead Overseer shall adopt a decision imposing a periodic penalty payment to compel the critical ICT third-party service provider to comply with those measures.': {
        'risks': ['Fines and judgements', 'Third-party compliance / legal exposure'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.7: The periodic penalty payment referred to in paragraph 6 shall be imposed on a daily basis until compliance is achieved and for no more than a period of six months following the notification of the decision to impose a periodic penalty payment to the critical ICT third-party service provider.': {
        'risks': ['Fines and judgements', 'Third-party compliance / legal exposure'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.8: The amount of the periodic penalty payment, calculated from the date stipulated in the decision imposing the periodic penalty payment, shall be up to 1 % of the average daily worldwide turnover of the critical ICT third-party service provider in the preceding business year. When determining the amount of the penalty payment, the Lead Overseer shall take into account the following criteria regarding non-compliance with the measures referred to in paragraph 6:': {
        'risks': ['Fines and judgements', 'Third-party compliance / legal exposure'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.9: Penalty payments shall be of an administrative nature and shall be enforceable. Enforcement shall be governed by the rules of civil procedure in force in the Member State on the territory of which inspections and access shall be carried out. Courts of the Member State concerned shall have jurisdiction over complaints related to irregular conduct of enforcement. The amounts of the penalty payments shall be allocated to the general budget of the European Union.': {
        'risks': ['Fines and judgements', 'Third-party compliance / legal exposure'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.10:  The Lead Overseer shall disclose to the public every periodic penalty payment that has been imposed, unless such disclosure would seriously jeopardise the financial markets or cause disproportionate damage to the parties involved.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 35.11:  Before imposing a periodic penalty payment under paragraph 6, the Lead Overseer shall give the representatives of the critical ICT third-party service provider subject to the proceedings the opportunity to be heard on the findings and shall base its decisions only on findings on which the critical ICT third-party service provider subject to the proceedings has had an opportunity to comment.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 36.1: When oversight objectives cannot be attained by means of interacting with the subsidiary set up for the purpose of Article 31(12), or by exercising oversight activities on premises located in the Union, the Lead Overseer may exercise the powers, referred to in the following provisions, on any premises located in a third-country which is owned, or used in any way, for the purposes of providing services to Union financial entities, by a critical ICT third-party service provider, in connection with its business operations, functions or services, including any administrative, business or operational offices, premises, lands, buildings or other properties:': {
        'risks': ['Third-party compliance / legal exposure', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 36.2: Without prejudice to the respective competences of the Union institutions and of Member States, for the purposes of paragraph 1, EBA, ESMA or EIOPA shall conclude administrative cooperation arrangements with the relevant authority of the third country in order to enable the smooth conduct of inspections in the third country concerned by the Lead Overseer and its designated team for its mission in that third country. Those cooperation arrangements shall not create legal obligations in respect of the Union and its Member States nor shall they prevent Member States and their competent authorities from concluding bilateral or multilateral arrangements with those third countries and their relevant authorities.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 36.3: When the Lead Overseer is not able to conduct oversight activities outside the Union, referred to in paragraphs 1 and 2, the Lead Overseer shall:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 37.1: The Lead Overseer may, by simple request or by decision, require critical ICT third-party service providers to provide all information that is necessary for the Lead Overseer to carry out its duties under this Regulation, including all relevant business or operational documents, contracts, policies, documentation, ICT security audit reports, ICT-related incident reports, as well as any information relating to parties to whom the critical ICT third-party service provider has outsourced operational functions or activities.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 37.2: When sending a simple request for information under paragraph 1, the Lead Overseer shall:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 37.3: When requiring by decision to supply information under paragraph 1, the Lead Overseer shall:': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 37.4: The representatives of the critical ICT third-party service providers shall supply the information requested. Lawyers duly authorised to act may supply the information on behalf of their clients. The critical ICT third-party service provider shall remain fully responsible if the information supplied is incomplete, incorrect or misleading.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 37.5: The Lead Overseer shall, without delay, transmit a copy of the decision to supply information to the competent authorities of the financial entities using the services of the relevant critical ICT third-party service providers and to the JON.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 38.1: In order to carry out its duties under this Regulation, the Lead Overseer, assisted by the joint examination team referred to in Article 40(1), may, where necessary, conduct investigations of critical ICT third-party service providers.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 38.2: The Lead Overseer shall have the power to:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 38.3: The officials and other persons authorised by the Lead Overseer for the purposes of the investigation referred to in paragraph 1 shall exercise their powers upon production of a written authorisation specifying the subject matter and purpose of the investigation.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 38.4: The representatives of the critical ICT third-party service providers are required to submit to the investigations on the basis of a decision of the Lead Overseer. The decision shall specify the subject matter and purpose of the investigation, the periodic penalty payments provided for in Article 35(6), the legal remedies available under Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010, and the right to have the decision reviewed by the Court of Justice.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 38.5: In good time before the start of the investigation, the Lead Overseer shall inform competent authorities of the financial entities using the ICT services of that critical ICT third-party service provider of the envisaged investigation and of the identity of the authorised persons.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 39.1: In order to carry out its duties under this Regulation, the Lead Overseer, assisted by the joint examination teams referred to in Article 40(1), may enter in, and conduct all necessary onsite inspections on, any business premises, land or property of the ICT third-party service providers, such as head offices, operation centres, secondary premises, as well as to conduct off-site inspections.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 39.2: The officials and other persons authorised by the Lead Overseer to conduct an on-site inspection shall have the power to:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 39.3: In good time before the start of the inspection, the Lead Overseer shall inform the competent authorities of the financial entities using that ICT third-party service provider.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 39.4: Inspections shall cover the full range of relevant ICT systems, networks, devices, information and data either used for, or contributing to, the provision of ICT services to financial entities.': {
        'risks': ['Lack of oversight of third-party controls', 'Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 39.5: Before any planned on-site inspection, the Lead Overseer shall give reasonable notice to the critical ICT third-party service providers, unless such notice is not possible due to an emergency or crisis situation, or if it would lead to a situation where the inspection or audit would no longer be effective.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 39.6: The critical ICT third-party service provider shall submit to on-site inspections ordered by decision of the Lead Overseer. The decision shall specify the subject matter and purpose of the inspection, fix the date on which the inspection shall begin and shall indicate the periodic penalty payments provided for in Article 35(6), the legal remedies available under Regulations (EU) No 1093/2010, (EU) No 1094/2010 and (EU) No 1095/2010, as well as the right to have the decision reviewed by the Court of Justice.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 39.7: Where the officials and other persons authorised by the Lead Overseer find that a critical ICT third-party service provider opposes an inspection ordered pursuant to this Article, the Lead Overseer shall inform the critical ICT third-party service provider of the consequences of such opposition, including the possibility for competent authorities of the relevant financial entities to require financial entities to terminate the contractual arrangements concluded with that critical ICT third-party service provider.': {
        'risks': ['Third-party compliance / legal exposure', 'Fines and judgements'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 40.1: When conducting oversight activities, in particular general investigations or inspections, the Lead Overseer shall be assisted by a joint examination team established for each critical ICT third-party service provider.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 40.2: The joint examination team referred to in paragraph 1 shall be composed of staff members from:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 40.3: Within 3 months of the completion of an investigation or inspection, the Lead Overseer, after consulting the Oversight Forum, shall adopt recommendations to be addressed to the critical ICT third-party service provider pursuant to the powers referred to in Article 35.': {
        'risks': ['Ineffective remediation actions', 'Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 40.4: The recommendations referred to in paragraph 3 shall be immediately communicated to the critical ICT third-party service provider and to the competent authorities of the financial entities to which it provides ICT services.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 41.1: The ESAs shall, through the Joint Committee, develop draft regulatory technical standards to specify:': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 41.2: The ESAs shall submit those draft regulatory technical standards to the Commission by 17 July 2024.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.1: Within 60 calendar days of the receipt of the recommendations issued by the Lead Overseer pursuant to Article 35(1), point (d), critical ICT third-party service providers shall either notify the Lead Overseer of their intention to follow the recommendations or provide a reasoned explanation for not following such recommendations. The Lead Overseer shall immediately transmit this information to the competent authorities of the financial entities concerned.': {
        'risks': ['Ineffective remediation actions', 'Fines and judgements'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.2: The Lead Overseer shall publicly disclose where a critical ICT third-party service provider fails to notify the Lead Overseer in accordance with paragraph 1 or where the explanation provided by the critical ICT third-party service provider is not deemed sufficient. The information published shall disclose the identity of the critical ICT third-party service provider as well as information on the type and nature of the non-compliance. Such information shall be limited to what is relevant and proportionate for the purpose of ensuring public awareness, unless such publication would cause disproportionate damage to the parties involved or could seriously jeopardise the orderly functioning and integrity of financial markets or the stability of the whole or part of the financial system of the Union.': {
        'risks': ['Fines and judgements', 'Diminished reputation'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.3: Competent authorities shall inform the relevant financial entities of the risks identified in the recommendations addressed to critical ICT third-party service providers in accordance with Article 35(1), point (d).': {
        'risks': ['Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.4: Where a competent authority deems that a financial entity fails to take into account or to sufficiently address within its management of ICT third-party risk the specific risks identified in the recommendations, it shall notify the financial entity of the possibility of a decision being taken, within 60 calendar days of the receipt of such notification, pursuant to paragraph 6, in the absence of appropriate contractual arrangements aiming to address such risks.': {
        'risks': ['Fines and judgements', 'Third-party compliance / legal exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.5: Upon receiving the reports referred to in Article 35(1), point (c), and prior to taking a decision as referred to in paragraph 6 of this Article, competent authorities may, on a voluntary basis, consult the competent authorities designated or established in accordance with Directive (EU) 2022/2555 responsible for the supervision of an essential or important entity subject to that Directive, which has been designated as a critical ICT third-party service provider.': {
        'risks': ['Third-party cybersecurity exposure'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.6: Competent authorities may, as a measure of last resort, following the notification and, if appropriate, the consultation as set out in paragraph 4 and 5 of this Article, in accordance with Article 50, take a decision requiring financial entities to temporarily suspend, either in part or completely, the use or deployment of a service provided by the critical ICT third-party service provider until the risks identified in the recommendations addressed to critical ICT third-party service providers have been addressed. Where necessary, they may require financial entities to terminate, in part or completely, the relevant contractual arrangements concluded with the critical ICT third-party service providers.': {
        'risks': ['Fines and judgements', 'Reliance on the third-party'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.7: Where a critical ICT third-party service provider refuses to endorse recommendations, based on a divergent approach from the one advised by the Lead Overseer, and such a divergent approach may adversely impact a large number of financial entities, or a significant part of the financial sector, and individual warnings issued by competent authorities have not resulted in consistent approaches mitigating the potential risk to financial stability, the Lead Overseer may, after consulting the Oversight Forum, issue non-binding and non-public opinions to competent authorities, in order to promote consistent and convergent supervisory follow-up measures, as appropriate.': {
        'risks': ['Third-party compliance / legal exposure', 'Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.8: Upon receiving the reports referred to in Article 35(1), point (c), competent authorities, when taking a decision as referred to in paragraph 6 of this Article, shall take into account the type and magnitude of risk that is not addressed by the critical ICT third-party service provider, as well as the seriousness of the non-compliance, having regard to the following criteria:': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.9: The decision referred to in paragraph 6 of this Article shall be notified to the members of the Oversight Forum referred to in Article 32(4), points (a), (b) and (c), and to the JON.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.10:  Competent authorities shall regularly inform the Lead Overseer on the approaches and measures taken in their supervisory tasks in relation to financial entities as well as on the contractual arrangements concluded by financial entities where critical ICT third-party service providers have not endorsed in part or entirely recommendations addressed to them by the Lead Overseer.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 42.11:  The Lead Overseer may, upon request, provide further clarifications on the recommendations issued to guide the competent authorities on the follow-up measures.': {
        'risks': ['Lack of oversight of third-party controls'],
        'controls': ['TPM-3', 'GOV-8'],
        'policies': ['POL-34'],
    },
    "Article 43.1: The Lead Overseer shall, in accordance with the delegated act referred to in paragraph 2 of this Article, charge critical ICT third-party service providers fees that fully cover the Lead Overseer's necessary expenditure in relation to the conduct of oversight tasks pursuant to this Regulation, including the reimbursement of any costs which may be incurred as a result of work carried out by the joint examination team referred to in Article 40, as well as the costs of advice provided by the independent experts as referred to in Article 32(4), second subparagraph, in relation to matters falling under the remit of direct oversight activities.": {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 43.2: The Commission is empowered to adopt a delegated act in accordance with Article 57 to supplement this Regulation by determining the amount of the fees and the way in which they are to be paid by 17 July 2024.': {
        'risks': ['Fines and judgements'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 44.1: Without prejudice to Article 36, EBA, ESMA and EIOPA may, in accordance with Article 33 of Regulations (EU) No 1093/2010, (EU) No 1095/2010 and (EU) No 1094/2010, respectively, conclude administrative arrangements with third-country regulatory and supervisory authorities to foster international cooperation on ICT third-party risk across different financial sectors, in particular by developing best practices for the review of ICT risk management practices and controls, mitigation measures and incident responses.': {
        'risks': ['Third-party compliance / legal exposure'],
        'controls': ['GOV-8'],
        'policies': ['POL-34'],
    },
    'Article 45.1: Financial entities may exchange amongst themselves cyber threat information and intelligence, including indicators of compromise, tactics, techniques, and procedures, cyber security alerts and configuration tools, to the extent that such information and intelligence sharing:': {
        'risks': ['Improper response to incidents', 'Inability to maintain situational awareness'],
        'controls': ['CCI-3', 'IRM-3'],
        'policies': ['POL-20', 'POL-21'],
    },
    'Article 45.2: For the purpose of paragraph 1, point (c), the information-sharing arrangements shall define the conditions for participation and, where appropriate, shall set out the details on the involvement of public authorities and the capacity in which they may be associated to the information-sharing arrangements, on the involvement of ICT third-party service providers, and on operational elements, including the use of dedicated IT platforms.': {
        'risks': ['Improper response to incidents'],
        'controls': ['CCI-3', 'IRM-3'],
        'policies': ['POL-20', 'POL-21'],
    },
    'Article 45.3: Financial entities shall notify competent authorities of their participation in the information-sharing arrangements referred to in paragraph 1, upon validation of their membership, or, as applicable, of the cessation of their membership, once it takes effect.': {
        'risks': ['Fines and judgements'],
        'controls': ['CCI-3', 'GOV-8'],
        'policies': ['POL-20', 'POL-21'],
    },
}
