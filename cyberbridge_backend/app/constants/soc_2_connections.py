# Auto-generated from SOC2_Objectives_Risks_Controls_Policies.xlsx
# Maps each SOC 2 objective title to its connected risks, controls, and policies.
#
# - risks: matched by risk_category_name in risk_templates
# - controls: matched by control code (or fallback by control name) in control_templates
# - policies: matched by POL code (or fallback by policy title) in policy_templates

SOC2_CONNECTIONS = {
    'CC1.1.1: Sets the Tone at the Top': {
        'risks': [],
        'controls': ['HRM-1', 'HRM-10'],
        'policies': ['POL-13', 'POL-27', 'POL-31', 'POL-32'],
    },
    'CC1.1.2: Establishes Standards of Conduct': {
        'risks': [],
        'controls': ['AST-4', 'HRM-10'],
        'policies': ['POL-32'],
    },
    'CC1.1.3: Evaluates Adherence to Standards of Conduct': {
        'risks': [],
        'controls': ['HRM-1', 'HRM-10'],
        'policies': ['POL-13', 'POL-27', 'POL-31', 'POL-32'],
    },
    'CC1.1.4: Addresses Deviations in a Timely Manner': {
        'risks': [],
        'controls': ['HRM-10', 'HRM-9'],
        'policies': ['POL-32'],
    },
    'CC1.1.5: Considers Contractors and Vendor Employees in Demonstrating Its Commitment': {
        'risks': [],
        'controls': ['HRM-10'],
        'policies': ['POL-32'],
    },
    'CC1.2.1: Establishes Oversight Responsibilities': {
        'risks': [],
        'controls': ['GOV-10', 'GOV-3', 'GOV-9'],
        'policies': [],
    },
    'CC1.2.2: Applies Relevant Expertise': {
        'risks': [],
        'controls': ['GOV-4', 'HRM-11'],
        'policies': [],
    },
    'CC1.2.3: Operates Independently': {
        'risks': [],
        'controls': ['GOV-10'],
        'policies': [],
    },
    'CC1.2.4: Supplements Board Expertise': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC1.3.1: Considers All Structures of the Entity': {
        'risks': [],
        'controls': ['HRM-5'],
        'policies': [],
    },
    'CC1.3.2: Establishes Reporting Lines': {
        'risks': [],
        'controls': ['HRM-5'],
        'policies': [],
    },
    'CC1.3.3: Defines, Assigns, and Limits Authorities and Responsibilities': {
        'risks': [],
        'controls': ['GOV-4', 'HRM-11'],
        'policies': [],
    },
    'CC1.3.4: Addresses Specific Requirements When Defining Authorities and Responsibilities': {
        'risks': [],
        'controls': ['HRM-11'],
        'policies': [],
    },
    'CC1.3.5: Considers Interactions With External Parties When Establishing Structures, Reporting ': {
        'risks': [],
        'controls': ['GOV-6', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'CC1.3.6: Establishes Structures, Reporting Lines, and Authorities to Support Compliance With ': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC1.4.1: Establishes Policies and Practices': {
        'risks': [],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-21', 'POL-27'],
    },
    'CC1.4.2: Evaluates Competence and Addresses Shortcomings': {
        'risks': [],
        'controls': ['HRM-11', 'HRM-12', 'HRM-6'],
        'policies': [],
    },
    'CC1.4.3: Attracts, Develops, and Retains Individuals': {
        'risks': [],
        'controls': ['HRM-11', 'HRM-12', 'HRM-6'],
        'policies': [],
    },
    'CC1.4.4: Plans and Prepares for Succession': {
        'risks': [],
        'controls': ['HRM-6'],
        'policies': [],
    },
    'CC1.4.5: Considers the Background of Individuals': {
        'risks': [],
        'controls': ['HRM-2'],
        'policies': ['POL-27'],
    },
    'CC1.4.6: Considers the Technical Competency of Individuals': {
        'risks': [],
        'controls': ['HRM-12'],
        'policies': [],
    },
    'CC1.4.7: Provides Training to Maintain Technical Competencies': {
        'risks': [],
        'controls': ['HRM-8'],
        'policies': ['POL-27'],
    },
    'CC1.5.1: Enforces Accountability Through Structures, Authorities, and Responsibilities': {
        'risks': [],
        'controls': ['HRM-11', 'HRM-5'],
        'policies': ['POL-27', 'POL-31'],
    },
    'CC1.5.2: Establishes Performance Measures, Incentives, and Rewards': {
        'risks': [],
        'controls': ['HRM-12', 'HRM-6'],
        'policies': [],
    },
    'CC1.5.3: Evaluates Performance Measures, Incentives, and Rewards for Ongoing Relevance': {
        'risks': [],
        'controls': ['HRM-11', 'HRM-12', 'HRM-6'],
        'policies': [],
    },
    'CC1.5.4: Considers Excessive Pressures': {
        'risks': [],
        'controls': ['HRM-11', 'HRM-12'],
        'policies': [],
    },
    'CC1.5.5: Evaluates Performance and Rewards or Disciplines Individuals': {
        'risks': [],
        'controls': ['HRM-12', 'HRM-9'],
        'policies': [],
    },
    'CC1.5.6: Takes Disciplinary Actions': {
        'risks': [],
        'controls': ['HRM-9'],
        'policies': [],
    },
    'CC2.1.1: Identifies Information Requirements': {
        'risks': [],
        'controls': ['GOV-3', 'GOV-8'],
        'policies': ['POL-16'],
    },
    'CC2.1.2: Captures Internal and External Sources of Data': {
        'risks': [],
        'controls': ['GOV-6', 'TPM-3'],
        'policies': ['POL-30', 'POL-34'],
    },
    'CC2.1.3: Processes Relevant Data Into Information': {
        'risks': [],
        'controls': ['GOV-3', 'GOV-9'],
        'policies': [],
    },
    'CC2.1.4: Maintains Quality Throughout Processing': {
        'risks': [],
        'controls': ['GOV-3', 'GOV-9'],
        'policies': [],
    },
    'CC2.1.5: Documents Data Flow': {
        'risks': [],
        'controls': ['DCH-1'],
        'policies': ['POL-14'],
    },
    'CC2.1.6: Manages Assets': {
        'risks': [],
        'controls': ['AST-1'],
        'policies': ['POL-2', 'POL-3', 'POL-7'],
    },
    'CC2.1.7: Classifies Information': {
        'risks': [],
        'controls': ['AST-3'],
        'policies': ['POL-2', 'POL-3', 'POL-7'],
    },
    'CC2.1.8: Uses Information That Is Complete and Accurate': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC2.1.9: Manages the Location of Assets': {
        'risks': [],
        'controls': ['AST-1'],
        'policies': ['POL-2', 'POL-3', 'POL-7'],
    },
    'CC2.2.1: Communicates Internal Control Information': {
        'risks': [],
        'controls': ['CCI-3', 'GOV-1'],
        'policies': [],
    },
    'CC2.2.2: Communicates With the Board of Directors': {
        'risks': [],
        'controls': ['GOV-8'],
        'policies': [],
    },
    'CC2.2.3: Provides Separate Communication Lines': {
        'risks': [],
        'controls': ['HRM-3'],
        'policies': [],
    },
    'CC2.2.4: Selects Relevant Method of Communication': {
        'risks': [],
        'controls': ['CCI-3'],
        'policies': [],
    },
    'CC2.2.5: Communicates Responsibilities': {
        'risks': [],
        'controls': ['HRM-11'],
        'policies': [],
    },
    'CC2.2.6: Communicates Information on Reporting Failures, Incidents, Concerns, and Other Matters': {
        'risks': [],
        'controls': ['IRM-5'],
        'policies': [],
    },
    'CC2.2.7: Communicates Objectives and Changes to Objectives': {
        'risks': [],
        'controls': ['GOV-2'],
        'policies': [],
    },
    'CC2.2.8: Communicates Information to Improve Security Knowledge and Awareness': {
        'risks': [],
        'controls': ['HRM-8'],
        'policies': ['POL-27'],
    },
    'CC2.2.9: Communicates Information About System Operation and Boundaries': {
        'risks': [],
        'controls': ['GOV-2'],
        'policies': [],
    },
    'CC2.2.10: Communicates System Objectives': {
        'risks': [],
        'controls': ['GOV-2'],
        'policies': [],
    },
    'CC2.2.11: Communicates System Changes': {
        'risks': [],
        'controls': ['GOV-10', 'GOV-2'],
        'policies': [],
    },
    'CC2.2.12: Communicates Information to Improve Privacy Knowledge and Awareness': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC2.2.13: Communicates Incident Reporting Methods': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC2.3.1: Communicates to External Parties': {
        'risks': [],
        'controls': ['CCI-3'],
        'policies': [],
    },
    'CC2.3.2: Enables Inbound Communications': {
        'risks': [],
        'controls': ['IRM-5'],
        'policies': [],
    },
    'CC2.3.3: Communicates With the Board of Directors': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'CC2.3.4: Provides Separate Communication Lines': {
        'risks': [],
        'controls': ['HRM-3'],
        'policies': [],
    },
    'CC2.3.5: Selects Relevant Method of Communication': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC2.3.6: Communicates Objectives Related to Confidentiality and Changes to Those Objectives': {
        'risks': [],
        'controls': ['GOV-1', 'GOV-10', 'GOV-2'],
        'policies': [],
    },
    'CC2.3.7: Communicates Objectives Related to Privacy and Changes to Those Objectives': {
        'risks': [],
        'controls': ['GOV-1', 'TPM-1'],
        'policies': ['POL-34'],
    },
    'CC2.3.8: Communicates Information About System Operation and Boundaries': {
        'risks': [],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    'CC2.3.9: Communicates System Objectives': {
        'risks': [],
        'controls': ['GOV-2'],
        'policies': [],
    },
    'CC2.3.10: Communicates System Responsibilities': {
        'risks': [],
        'controls': ['GOV-1', 'HRM-11', 'TPM-1'],
        'policies': ['POL-34'],
    },
    'CC2.3.11: Communicates Information on Reporting System Failures, Incidents, Concerns, and Other ': {
        'risks': [],
        'controls': ['IRM-5'],
        'policies': [],
    },
    'CC2.3.12: Communicates Incident Reporting Methods': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC3.1.1: Reflects Management': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-8'],
        'policies': ['POL-30'],
    },
    'CC3.1.2: Considers Tolerances for Risk': {
        'risks': [],
        'controls': ['GOV-11', 'RSM-2'],
        'policies': ['POL-30'],
    },
    'CC3.1.3: Includes Operations and Financial Performance Goals': {
        'risks': [],
        'controls': ['GOV-8'],
        'policies': [],
    },
    'CC3.1.4: Forms a Basis for Committing of Resources': {
        'risks': [],
        'controls': ['GOV-8'],
        'policies': [],
    },
    'CC3.1.5: Complies With Applicable Accounting Standards': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.1.6: Considers Materiality': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.1.7: Reflects Entity Activities': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.1.8: Complies With Externally Established Frameworks': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6', 'GOV-8'],
        'policies': ['POL-30'],
    },
    'CC3.1.9: Considers the Required Level of Precision': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.1.10: Reflects Entity Activities': {
        'risks': [],
        'controls': ['GOV-11'],
        'policies': [],
    },
    'CC3.1.11: Reflects Management': {
        'risks': [],
        'controls': ['GOV-11'],
        'policies': [],
    },
    'CC3.1.12: Considers the Required Level of Precision': {
        'risks': [],
        'controls': ['GOV-6', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    'CC3.1.13: Reflects Entity Activities': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.1.14: Reflects External Laws and Regulations': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6', 'GOV-8'],
        'policies': ['POL-30'],
    },
    'CC3.1.15: Considers Tolerances for Risk': {
        'risks': [],
        'controls': ['GOV-11', 'RSM-2'],
        'policies': ['POL-30'],
    },
    'CC3.1.16: Establishes Sub Objectives for Risk Assessment': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-8'],
        'policies': [],
    },
    'CC3.2.1: Includes Entity, Subsidiary, Division, Operating Unit, and Functional Levels': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.2.2: Analyzes Internal and External Factors': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.2.3: Involves Appropriate Levels of Management': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.2.4: Estimates Significance of Risks Identified': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.2.5: Determines How to Respond to Risks': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.2.6: Identifies Threats to Objectives': {
        'risks': [],
        'controls': ['AST-4', 'GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.2.7: Analyzes Threats and Vulnerabilities From Vendors, Business Partners, and Other Parties': {
        'risks': [],
        'controls': ['GOV-6', 'TPM-3'],
        'policies': ['POL-30', 'POL-34'],
    },
    'CC3.2.8: Assesses the Significance of the Risks': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.2.9: Identifies Vulnerability of System Components': {
        'risks': [],
        'controls': ['CVM-1'],
        'policies': ['POL-35'],
    },
    'CC3.3.1: Considers Various Types of Fraud': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30', 'POL-34'],
    },
    'CC3.3.2: Assesses Incentives and Pressures': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.3.3: Assesses Opportunities': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.3.4: Assesses Attitudes and Rationalizations': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.3.5: Considers the Risks Related to the Use of IT and Access to Information': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': [],
    },
    'CC3.4.1: Assesses Changes in the External Environment': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6'],
        'policies': ['POL-11', 'POL-30'],
    },
    'CC3.4.2: Assesses Changes in the Business Model': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-3', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC3.4.3: Assesses Changes in Leadership': {
        'risks': [],
        'controls': ['CHM-3', 'GOV-11'],
        'policies': ['POL-30'],
    },
    'CC3.4.4: Assess Changes in Systems and Technology': {
        'risks': [],
        'controls': ['CHM-2', 'CHM-3', 'GOV-11', 'GOV-6'],
        'policies': ['POL-11', 'POL-30'],
    },
    'CC3.4.5: Assess Changes in Vendor and Business Partner': {
        'risks': [],
        'controls': ['GOV-11', 'GOV-6', 'TPM-3'],
        'policies': ['POL-30', 'POL-34'],
    },
    'CC3.4.6: Assesses Changes in Threats and Vulnerabilities': {
        'risks': [],
        'controls': ['CVM-1', 'CVM-2', 'GOV-6'],
        'policies': ['POL-35'],
    },
    'CC4.1.1: Considers a Mix of Ongoing and Separate Evaluations': {
        'risks': [],
        'controls': ['APD-2', 'GOV-3'],
        'policies': ['POL-30', 'POL-33'],
    },
    'CC4.1.2: Considers Rate of Change': {
        'risks': [],
        'controls': ['APD-2', 'CHM-3'],
        'policies': ['POL-33'],
    },
    'CC4.1.3: Establishes Baseline Understanding': {
        'risks': [],
        'controls': ['GOV-9'],
        'policies': [],
    },
    'CC4.1.4: Uses Knowledgeable Personnel': {
        'risks': [],
        'controls': ['HRM-12'],
        'policies': [],
    },
    'CC4.1.5: Integrates With Business Processes': {
        'risks': [],
        'controls': ['APD-2', 'GOV-3'],
        'policies': ['POL-33'],
    },
    'CC4.1.6: Adjusts Scope and Frequency': {
        'risks': [],
        'controls': ['GOV-3', 'GOV-6'],
        'policies': ['POL-30'],
    },
    'CC4.1.7: Objectively Evaluates': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'CC4.1.8: Considers Different Types of Ongoing and Separate Evaluations': {
        'risks': [],
        'controls': ['CVM-1', 'CVM-2', 'TPM-2'],
        'policies': ['POL-34', 'POL-35'],
    },
    'CC4.2.1: Assesses Results': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': ['POL-35'],
    },
    'CC4.2.2: Communicates Deficiencies': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'CC4.2.3: Monitors Corrective Action': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'CC5.1.1: Integrates With Risk Assessment': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC5.1.2: Considers entity': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC5.1.3: Determines Relevant Business Processes': {
        'risks': [],
        'controls': ['GOV-1', 'GOV-6', 'RSM-2', 'RSM-3'],
        'policies': ['POL-30'],
    },
    'CC5.1.4: Evaluates a Mix of Control Activity Types': {
        'risks': [],
        'controls': ['GOV-9'],
        'policies': [],
    },
    'CC5.1.5: Considers at What Level Activities Are Applied': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'CC5.1.6: Addresses Segregation of Duties': {
        'risks': [],
        'controls': ['GOV-9'],
        'policies': [],
    },
    'CC5.2.1: Determines Dependency Between the Use of Technology in Business Processes and ': {
        'risks': [],
        'controls': ['GOV-1', 'GOV-3', 'GOV-6'],
        'policies': ['POL-6', 'POL-30', 'POL-33'],
    },
    'CC5.2.2: Establishes Relevant Technology Infrastructure Control Activities': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC5.2.3: Establishes Relevant Security Management Process Controls Activities': {
        'risks': [],
        'controls': ['GOV-6', 'GOV-9'],
        'policies': ['POL-30'],
    },
    'CC5.2.4: Establishes Relevant Technology Acquisition, Development, and Maintenance Process ': {
        'risks': [],
        'controls': ['GOV-6'],
        'policies': ['POL-30'],
    },
    'CC5.3.1: Establishes Policies and Procedures to Support Deployment of Management ?s Directives': {
        'risks': [],
        'controls': ['GOV-1', 'GOV-5'],
        'policies': ['POL-21'],
    },
    'CC5.3.2: Establishes Responsibility and Accountability for Executing Policies and Procedures': {
        'risks': [],
        'controls': ['HRM-11', 'HRM-5'],
        'policies': [],
    },
    'CC5.3.3: Performs in a Timely Manner': {
        'risks': [],
        'controls': ['GOV-1', 'HRM-11'],
        'policies': [],
    },
    'CC5.3.4: Takes Corrective Action': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'CC5.3.5: Performs Using Competent Personnel': {
        'risks': [],
        'controls': ['HRM-12', 'HRM-4'],
        'policies': [],
    },
    'CC5.3.6: Reassesses Policies and Procedures': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'CC6.1.1: Identifies and Manages the Inventory of Information Assets': {
        'risks': [],
        'controls': ['AST-1', 'AST-3'],
        'policies': ['POL-1', 'POL-2', 'POL-3', 'POL-4', 'POL-7', 'POL-14', 'POL-24', 'POL-25', 'POL-29'],
    },
    'CC6.1.2: Restricts  Logical Access': {
        'risks': [],
        'controls': ['IAM-1', 'IAM-4', 'IAM-7', 'IAM-8'],
        'policies': ['POL-1', 'POL-4', 'POL-25'],
    },
    'CC6.1.3: Identifies and Authenticates Users': {
        'risks': [],
        'controls': ['IAM-5'],
        'policies': ['POL-1', 'POL-25'],
    },
    'CC6.1.4: Considers Network Segmentation': {
        'risks': [],
        'controls': ['APD-5', 'NES-3'],
        'policies': ['POL-6', 'POL-24'],
    },
    'CC6.1.5: Manages Points of Access': {
        'risks': [],
        'controls': ['IAM-2', 'IAM-5', 'IAM-7'],
        'policies': ['POL-1', 'POL-25'],
    },
    'CC6.1.6: Restricts Access to Information Assets': {
        'risks': [],
        'controls': ['AST-3', 'IAM-1', 'IAM-3', 'IAM-4', 'IAM-7', 'IAM-8'],
        'policies': ['POL-1', 'POL-2', 'POL-3', 'POL-4', 'POL-7', 'POL-25'],
    },
    'CC6.1.7: Manages Identification and Authentication': {
        'risks': [],
        'controls': ['IAM-5', 'IAM-6'],
        'policies': ['POL-1', 'POL-25'],
    },
    'CC6.1.8: Manages Credentials for Infrastructure and Software': {
        'risks': [],
        'controls': ['IAM-3', 'IAM-4'],
        'policies': ['POL-4'],
    },
    'CC6.1.9: Uses Encryption to Protect Data': {
        'risks': [],
        'controls': ['CRY-1', 'CRY-2'],
        'policies': ['POL-19'],
    },
    'CC6.1.10: Protects Cryptographic Keys': {
        'risks': [],
        'controls': ['CRY-3', 'CRY-4'],
        'policies': ['POL-19'],
    },
    'CC6.1.11: Assesses New Architectures': {
        'risks': [],
        'controls': [],
        'policies': ['POL-19'],
    },
    'CC6.1.12: Restricts Access to and Use of Confidential Information for Identified Purposes': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC6.1.13: Restricts Access to and the Use of Personal Information': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC6.2.1: Creates Access Credentials to Protected Information Assets': {
        'risks': [],
        'controls': ['IAM-1'],
        'policies': ['POL-4'],
    },
    'CC6.2.2: Reviews Validity of Access Credentials': {
        'risks': [],
        'controls': ['HRM-7', 'IAM-3', 'IAM-4'],
        'policies': ['POL-4'],
    },
    'CC6.2.3: Prevents the Use of Credentials When No Longer Valid': {
        'risks': [],
        'controls': ['IAM-3', 'IAM-4'],
        'policies': ['POL-4'],
    },
    'CC6.3.1: Creates or Modifies Access to Protected Information Assets': {
        'risks': [],
        'controls': ['IAM-1', 'IAM-8'],
        'policies': ['POL-1', 'POL-4', 'POL-25'],
    },
    'CC6.3.2: Removes Access to Protected Information Asset': {
        'risks': [],
        'controls': ['IAM-3', 'IAM-4'],
        'policies': ['POL-4'],
    },
    'CC6.3.3: Uses Access Control Structures': {
        'risks': [],
        'controls': ['IAM-7'],
        'policies': [],
    },
    'CC6.3.4: Reviews Access Roles and Rules': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC6.4.1: Creates or Modifies Physical Access': {
        'risks': [],
        'controls': ['PES-1', 'PES-3', 'PES-4'],
        'policies': ['POL-28'],
    },
    'CC6.4.2: Removes Physical Access': {
        'risks': [],
        'controls': ['IAM-3', 'PES-1', 'PES-4'],
        'policies': ['POL-28'],
    },
    'CC6.4.3: Reviews Physical Access': {
        'risks': [],
        'controls': ['PES-1', 'PES-3', 'PES-4'],
        'policies': ['POL-28'],
    },
    'CC6.4.4: Recovers Physical Devices': {
        'risks': [],
        'controls': ['AST-2'],
        'policies': ['POL-2', 'POL-3', 'POL-7'],
    },
    'CC6.5.1: Identifies Data and Software for Disposal': {
        'risks': [],
        'controls': ['AST-2'],
        'policies': ['POL-2', 'POL-3', 'POL-7', 'POL-16', 'POL-17'],
    },
    'CC6.5.2: Removes Data and Software for disposal': {
        'risks': [],
        'controls': ['AST-2'],
        'policies': ['POL-2', 'POL-3', 'POL-7'],
    },
    'CC6.6.1: Restricts Access': {
        'risks': [],
        'controls': ['CVM-4', 'NES-4', 'NES-5'],
        'policies': ['POL-24', 'POL-29'],
    },
    'CC6.6.2: Protects Identification and Authentication Credentials': {
        'risks': [],
        'controls': ['CRY-1', 'IAM-9'],
        'policies': ['POL-19'],
    },
    'CC6.6.3: Requires Additional Authentication or Credentials': {
        'risks': [],
        'controls': ['IAM-6'],
        'policies': ['POL-1', 'POL-25'],
    },
    'CC6.6.4: Implements Boundary Protection Systems': {
        'risks': [],
        'controls': ['NES-1', 'NES-2'],
        'policies': ['POL-24'],
    },
    'CC6.7.1: Restricts the Ability to Perform Transmission': {
        'risks': [],
        'controls': ['CRY-1', 'NES-5', 'NES-6', 'NES-7'],
        'policies': ['POL-14', 'POL-19', 'POL-23', 'POL-24', 'POL-29'],
    },
    'CC6.7.2: Uses Encryption Technologies or Secure Communication Channels to Protect Data': {
        'risks': [],
        'controls': ['CRY-1'],
        'policies': [],
    },
    'CC6.7.3: Protects Removal Media': {
        'risks': [],
        'controls': ['AST-2', 'AST-3'],
        'policies': ['POL-2', 'POL-3', 'POL-7'],
    },
    'CC6.7.4: Protects Endpoint Devices': {
        'risks': [],
        'controls': ['AST-1', 'MDM-1'],
        'policies': ['POL-2', 'POL-3', 'POL-7', 'POL-23'],
    },
    'CC6.8.1: Restricts Installation and modification Application and Software': {
        'risks': [],
        'controls': ['CMM-1', 'CMM-2'],
        'policies': ['POL-5', 'POL-15', 'POL-24', 'POL-29'],
    },
    'CC6.8.2: Detects Unauthorized Changes to Software and Configuration Parameters': {
        'risks': [],
        'controls': ['CVM-4', 'IAM-2', 'NES-6', 'PES-2'],
        'policies': ['POL-24'],
    },
    'CC6.8.3: Uses a Defined Change Control Process': {
        'risks': [],
        'controls': ['CHM-1', 'CHM-3'],
        'policies': ['POL-11'],
    },
    'CC6.8.4: Uses Antivirus and Anti-Malware Software': {
        'risks': [],
        'controls': ['CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    'CC6.8.5: Scans Information Assets From Outside the Entity for Malware and Other Unauthorized ': {
        'risks': [],
        'controls': ['CMM-1', 'CVM-5', 'CVM-6'],
        'policies': ['POL-5'],
    },
    'CC7.1.1: Uses Defined Configuration Standards': {
        'risks': [],
        'controls': ['CMM-2'],
        'policies': ['POL-15', 'POL-35'],
    },
    'CC7.1.2: Monitors Infrastructure and Software': {
        'risks': [],
        'controls': ['ALM-3', 'CMM-1'],
        'policies': [],
    },
    'CC7.1.3: Implements Change': {
        'risks': [],
        'controls': ['ALM-1', 'CVM-4'],
        'policies': ['POL-22'],
    },
    'CC7.1.4: Detects Unknown or Unauthorized Components': {
        'risks': [],
        'controls': ['ALM-3', 'NES-2'],
        'policies': [],
    },
    'CC7.1.5: Conducts Vulnerability Scans': {
        'risks': [],
        'controls': ['CVM-1', 'CVM-3', 'CVM-7'],
        'policies': ['POL-26', 'POL-35'],
    },
    'CC7.2.1: Implements Detection Policies, Procedures, and Tools': {
        'risks': [],
        'controls': ['ALM-1', 'ALM-2', 'ALM-3', 'NES-6'],
        'policies': ['POL-22', 'POL-24', 'POL-30'],
    },
    'CC7.2.2: Designs Detection Measures': {
        'risks': [],
        'controls': ['ALM-1', 'ALM-3', 'NES-2', 'PES-2'],
        'policies': ['POL-22'],
    },
    'CC7.2.3: Implements Filters to Analyze Anomalies': {
        'risks': [],
        'controls': ['ALM-3', 'NES-6'],
        'policies': ['POL-24'],
    },
    'CC7.2.4: Monitors Detection Tools for Effective Operation': {
        'risks': [],
        'controls': ['ALM-3', 'ALM-5', 'NES-2'],
        'policies': [],
    },
    'CC7.3.1: Responds to Security Incidents': {
        'risks': [],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': ['POL-20', 'POL-22', 'POL-30'],
    },
    'CC7.3.2: Communicates and Reviews Detected Security Events': {
        'risks': [],
        'controls': ['IRM-2', 'IRM-4', 'IRM-6'],
        'policies': ['POL-20'],
    },
    'CC7.3.3: Develops and Implements Procedures to Analyze Security Incidents': {
        'risks': [],
        'controls': ['IRM-1', 'IRM-6'],
        'policies': [],
    },
    'CC7.3.4: Assesses the Impact on Personal Information': {
        'risks': [],
        'controls': ['ALM-3', 'IRM-1', 'IRM-2'],
        'policies': ['POL-20'],
    },
    'CC7.3.5: Determines Personal Information Used or Disclosed': {
        'risks': [],
        'controls': ['IRM-1'],
        'policies': [],
    },
    'CC7.3.6: Assesses the Impact on Confidential Information': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC7.3.7: Determines Confidential Information Used or Disclosed': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC7.4.1: Assigns Roles and Responsibilities': {
        'risks': [],
        'controls': ['IRM-1'],
        'policies': ['POL-20'],
    },
    'CC7.4.2: Contains and Responds to Security Incidents': {
        'risks': [],
        'controls': ['IRM-1', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.4.3: Mitigates Ongoing Security Incidents': {
        'risks': [],
        'controls': ['IRM-1', 'IRM-3', 'IRM-5'],
        'policies': [],
    },
    'CC7.4.4: Resolves Security Incidents': {
        'risks': [],
        'controls': ['IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.4.5: Restores Operations': {
        'risks': [],
        'controls': ['BCD-1'],
        'policies': ['POL-10', 'POL-18'],
    },
    'CC7.4.6: Develops and Implements Communication of Security Incidents': {
        'risks': [],
        'controls': ['IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.4.7: Obtains Understanding of Nature of Incident and Determines Containment Strategy': {
        'risks': [],
        'controls': ['IRM-1'],
        'policies': [],
    },
    'CC7.4.8: Remediates Identified Vulnerabilities': {
        'risks': [],
        'controls': ['CVM-3', 'CVM-7', 'RSM-3'],
        'policies': ['POL-26'],
    },
    'CC7.4.9: Communicates Remediation Activities': {
        'risks': [],
        'controls': ['IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.4.10: Evaluates the Effectiveness of Incident Resposes': {
        'risks': [],
        'controls': ['IRM-1', 'IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.4.11: Periodically Evaluates Incidents': {
        'risks': [],
        'controls': ['IRM-2'],
        'policies': ['POL-20'],
    },
    'CC7.4.12: Communicates Unauthorized Use and Disclosure': {
        'risks': [],
        'controls': ['IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.4.13: Application of Sanctions': {
        'risks': [],
        'controls': ['HRM-9'],
        'policies': [],
    },
    'CC7.4.14: Applies Breach Response Procedures': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC7.5.1: Restores the Affected Environment': {
        'risks': [],
        'controls': ['BCD-1'],
        'policies': ['POL-9', 'POL-10', 'POL-18'],
    },
    'CC7.5.2: Communicates Information About the Incident': {
        'risks': [],
        'controls': ['IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.5.3: Determines Root Cause of the Incident': {
        'risks': [],
        'controls': ['IRM-1', 'IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.5.4: Implements Changes to Prevent and Detect Recurrences': {
        'risks': [],
        'controls': ['IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.5.5: Improves Response and Recovery Procedures': {
        'risks': [],
        'controls': ['DRC-5', 'IRM-1', 'IRM-2', 'IRM-4'],
        'policies': ['POL-20'],
    },
    'CC7.5.6: Implements Incident Recovery Plan Testing': {
        'risks': [],
        'controls': ['BCD-1', 'BCD-3', 'DRC-5'],
        'policies': ['POL-10', 'POL-18'],
    },
    'CC8.1.1: Manages Changes Throughout the System Lifecycle': {
        'risks': [],
        'controls': ['CHM-3', 'GOV-1'],
        'policies': ['POL-6', 'POL-11', 'POL-15', 'POL-33'],
    },
    'CC8.1.2: Authorizes Changes': {
        'risks': [],
        'controls': ['CHM-2'],
        'policies': ['POL-11'],
    },
    'CC8.1.3: Designs and Develops Changes': {
        'risks': [],
        'controls': ['CHM-1', 'CHM-3', 'CHM-4'],
        'policies': ['POL-11'],
    },
    'CC8.1.4: Documents Changes': {
        'risks': [],
        'controls': ['CHM-1'],
        'policies': ['POL-11'],
    },
    'CC8.1.5: Tracks System Changes': {
        'risks': [],
        'controls': ['CHM-1'],
        'policies': ['POL-11'],
    },
    'CC8.1.6: Configures Software': {
        'risks': [],
        'controls': ['CMM-2'],
        'policies': ['POL-15'],
    },
    'CC8.1.7: Tests System Changes': {
        'risks': [],
        'controls': ['CHM-1', 'CHM-3'],
        'policies': ['POL-11'],
    },
    'CC8.1.8: Approves System Changes': {
        'risks': [],
        'controls': ['CHM-2'],
        'policies': ['POL-11'],
    },
    'CC8.1.9: Deploys System Changes': {
        'risks': [],
        'controls': ['CHM-1', 'CHM-3'],
        'policies': ['POL-11'],
    },
    'CC8.1.10: Identifies and Evaluates System Changes': {
        'risks': [],
        'controls': ['CHM-1', 'CHM-3'],
        'policies': ['POL-11'],
    },
    'CC8.1.11: Identifies Changes in Infrastructure, Data, Software, and Procedures Required to ': {
        'risks': [],
        'controls': ['CHM-3', 'CHM-4'],
        'policies': [],
    },
    'CC8.1.12: Creates Baseline Configuration of IT Technology': {
        'risks': [],
        'controls': ['CMM-2'],
        'policies': ['POL-15'],
    },
    'CC8.1.13: Provides for Changes Necessary in Emergency Situations': {
        'risks': [],
        'controls': ['CHM-1', 'CHM-2', 'CHM-3'],
        'policies': ['POL-11'],
    },
    'CC8.1.14: Protects Confidential Information': {
        'risks': [],
        'controls': ['CHM-3', 'DCH-5'],
        'policies': [],
    },
    'CC8.1.15: Protects Personal Information': {
        'risks': [],
        'controls': ['CHM-3'],
        'policies': [],
    },
    'CC8.1.16: Manages Patch Changes': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC8.1.17: Considers System Resilience': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC8.1.18: Privacy by Design': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'CC9.1.1: Considers Mitigation of Risks of Business Disruption': {
        'risks': [],
        'controls': ['RSM-3'],
        'policies': ['POL-10', 'POL-34'],
    },
    'CC9.1.2: Considers the Use of Insurance to Mitigate Financial Impact Risks': {
        'risks': [],
        'controls': ['RSM-3', 'RSM-4'],
        'policies': [],
    },
    'CC9.2.1: Establishes Requirements for Vendor and Business Partner Engagements': {
        'risks': [],
        'controls': ['TPM-1', 'TPM-4'],
        'policies': ['POL-34'],
    },
    'CC9.2.2: Assesses Vendor and Business Partner Risks': {
        'risks': [],
        'controls': ['TPM-3'],
        'policies': ['POL-34'],
    },
    'CC9.2.3: Assigns Responsibility and Accountability for Managing Vendors and Business Partners': {
        'risks': [],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    'CC9.2.4: Establishes Communication Protocols for Vendors and Business Partners': {
        'risks': [],
        'controls': ['IRM-5'],
        'policies': [],
    },
    'CC9.2.5: Establishes Exception Handling Procedures From Vendors and Business Partners': {
        'risks': [],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    'CC9.2.6: Assesses Vendor and Business Partner Performance': {
        'risks': [],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'CC9.2.7: Implements Procedures for Addressing Issues Identified During Vendor and Business ': {
        'risks': [],
        'controls': ['TPM-3'],
        'policies': ['POL-34'],
    },
    'CC9.2.8: Implements Procedures for Terminating Vendor and Business Partner Relationships': {
        'risks': [],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    'CC9.2.9: Obtains Confidentiality Commitments From Vendors and Business Partners': {
        'risks': [],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    'CC9.2.10: Assesses Compliance With Confidentiality Commitments of Vendors and Business Partners': {
        'risks': [],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'CC9.2.11: Obtains Privacy Commitments From Vendors and Business Partners': {
        'risks': [],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    'CC9.2.12: Assesses Compliance With Privacy Commitments of Vendors and Business Partners': {
        'risks': [],
        'controls': ['TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'CC9.2.13: Identifies Vulnerabilities': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'C1.1.1: Defines and Identifies Confidential information': {
        'risks': [],
        'controls': ['AST-3', 'DCH-2', 'DCH-5'],
        'policies': ['POL-2', 'POL-3', 'POL-7', 'POL-14', 'POL-16'],
    },
    'C1.1.2: Protects Confidential Information from Destruction': {
        'risks': [],
        'controls': ['DCH-4'],
        'policies': ['POL-14', 'POL-17'],
    },
    'C1.1.3: Retains Confidential Information': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'C1.2.1: Identifies Confidential Information for Destruction': {
        'risks': [],
        'controls': ['DCH-1', 'DCH-4'],
        'policies': ['POL-14', 'POL-17'],
    },
    'C1.2.2: Destroys Confidential Information': {
        'risks': [],
        'controls': ['DCH-4'],
        'policies': ['POL-14', 'POL-17'],
    },
    'PI1.1.1: Identifies Functional and Nonfunctional Requirements and Information Specifications': {
        'risks': [],
        'controls': ['PRI-2'],
        'policies': ['POL-6', 'POL-33'],
    },
    'PI1.1.2: Defines Data Necessary to Support a Product or Service': {
        'risks': [],
        'controls': ['PRI-2'],
        'policies': [],
    },
    'PI1.2.1: Defines Characteristics of Processing Inputs': {
        'risks': [],
        'controls': ['PRI-2'],
        'policies': ['POL-6', 'POL-33'],
    },
    'PI1.2.2: Evaluates Processing Inputs': {
        'risks': [],
        'controls': ['PRI-2'],
        'policies': [],
    },
    'PI1.2.3: Creates and Maintains Records of System Input': {
        'risks': [],
        'controls': ['PRI-2', 'PRI-5'],
        'policies': [],
    },
    'PI1.3.1: Defines Processing Specifications': {
        'risks': [],
        'controls': ['PRI-1'],
        'policies': ['POL-6', 'POL-33'],
    },
    'PI1.3.2: Defines Processing Activities': {
        'risks': [],
        'controls': ['PRI-1'],
        'policies': [],
    },
    'PI1.3.3: Detects and Corrects Processing or Production Activity Errors': {
        'risks': [],
        'controls': ['PRI-1'],
        'policies': [],
    },
    'PI1.3.4: Records System Processing Activities': {
        'risks': [],
        'controls': ['PRI-1', 'PRI-5'],
        'policies': [],
    },
    'PI1.3.5: Processes Inputs': {
        'risks': [],
        'controls': ['PRI-1', 'PRI-2'],
        'policies': [],
    },
    'PI1.4.1: Protects Output': {
        'risks': [],
        'controls': ['PRI-3', 'PRI-4'],
        'policies': ['POL-6', 'POL-22', 'POL-33'],
    },
    'PI1.4.2: Distributes Output Only to Intended Parties': {
        'risks': [],
        'controls': ['PRI-3', 'PRI-4'],
        'policies': [],
    },
    'PI1.4.3: Distributes Output Completely and Accurately': {
        'risks': [],
        'controls': ['PRI-1', 'PRI-3', 'PRI-4'],
        'policies': [],
    },
    'PI1.4.4: Creates and Maintains Records of System Output Activities': {
        'risks': [],
        'controls': ['PRI-3', 'PRI-5'],
        'policies': [],
    },
    'PI1.5.1: Protects Stored Items': {
        'risks': [],
        'controls': ['PRI-4'],
        'policies': ['POL-6', 'POL-17', 'POL-22', 'POL-33'],
    },
    'PI1.5.2: Archives and Protects System Records': {
        'risks': [],
        'controls': ['PRI-4'],
        'policies': [],
    },
    'PI1.5.3: Stores Data Completely and Accurately': {
        'risks': [],
        'controls': ['PRI-1', 'PRI-4', 'PRI-5'],
        'policies': [],
    },
    'PI1.5.4: Creates and Maintains Records of Storage Activities': {
        'risks': [],
        'controls': ['PRI-4', 'PRI-5'],
        'policies': [],
    },
    'A1.1.1: Measures Current Usage': {
        'risks': [],
        'controls': ['CAP-1'],
        'policies': ['POL-8'],
    },
    'A1.1.2: Forecasts Capacity': {
        'risks': [],
        'controls': ['CAP-2'],
        'policies': [],
    },
    'A1.1.3: Makes Changes Based on Forecasts': {
        'risks': [],
        'controls': ['CHM-2'],
        'policies': ['POL-11'],
    },
    'A1.2.1: Identifies Environmental Threats': {
        'risks': [],
        'controls': ['PES-2'],
        'policies': ['POL-8', 'POL-9', 'POL-18', 'POL-28', 'POL-30'],
    },
    'A1.2.2: Designs Detection Measures': {
        'risks': [],
        'controls': ['ALM-1'],
        'policies': ['POL-22'],
    },
    'A1.2.3: Implements and Maintains Environmental Protection Mechanisms': {
        'risks': [],
        'controls': ['PES-2'],
        'policies': [],
    },
    'A1.2.4: Implements Alerts to Analyze Anomalies': {
        'risks': [],
        'controls': ['ALM-1', 'ALM-3'],
        'policies': ['POL-22'],
    },
    'A1.2.5: Responds to Environmental Threat Events': {
        'risks': [],
        'controls': ['GOV-1', 'GOV-9'],
        'policies': [],
    },
    'A1.2.6: Communicates and Reviews Detected Environmental Threat Events': {
        'risks': [],
        'controls': ['ALM-1'],
        'policies': ['POL-22'],
    },
    'A1.2.7: Determines Data Requiring Backup': {
        'risks': [],
        'controls': ['DRC-5'],
        'policies': [],
    },
    'A1.2.8: Performs Data Backup': {
        'risks': [],
        'controls': ['DRC-1', 'DRC-2', 'DRC-4', 'DRC-5'],
        'policies': ['POL-9', 'POL-17'],
    },
    'A1.2.9: Addresses Offsite Storage': {
        'risks': [],
        'controls': ['BCD-4', 'DRC-3'],
        'policies': ['POL-8', 'POL-9'],
    },
    'A1.2.10: Implements Alternate Processing Infrastructure': {
        'risks': [],
        'controls': ['BCD-1', 'BCD-4'],
        'policies': ['POL-10', 'POL-18'],
    },
    'A1.2.11: Considers Data Recoverability': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'A1.3.1: Implements Business Continuity Plan Testing': {
        'risks': [],
        'controls': ['BCD-1', 'BCD-3'],
        'policies': ['POL-10', 'POL-18'],
    },
    'A1.3.2: Tests Integrity and Completeness of Back-Up Data': {
        'risks': [],
        'controls': ['BCD-1'],
        'policies': ['POL-10', 'POL-18'],
    },
    'P1.1.1: Communicates to Data Subjects': {
        'risks': [],
        'controls': ['PRIV-1', 'PRIV-2', 'PRIV-5'],
        'policies': [],
    },
    'P1.1.2: Provides Notice to Data Subjects': {
        'risks': [],
        'controls': ['PRIV-2', 'PRIV-4'],
        'policies': [],
    },
    'P1.1.3: Covers Entities and Activities in Notice': {
        'risks': [],
        'controls': ['PRIV-1'],
        'policies': [],
    },
    'P1.1.4: Uses Clear Language and Presents a Current Privacy Notice in a Location Easily Found by ': {
        'risks': [],
        'controls': ['PRIV-1'],
        'policies': [],
    },
    'P1.1.5: Reviews the Privacy Notice': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'P1.1.6: Communicates Changes to Notice': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'P1.1.7: Retains Prior Notices': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'P2.1.1: Communicates to Data Subjects': {
        'risks': [],
        'controls': ['PRIV-1', 'PRIV-2', 'PRIV-4', 'PRIV-6'],
        'policies': [],
    },
    'P2.1.2: Communicates Consequences of Denying or Withdrawing Consent': {
        'risks': [],
        'controls': ['PRIV-1', 'PRIV-5'],
        'policies': [],
    },
    'P2.1.3: Obtains Implicit or Explicit Consent': {
        'risks': [],
        'controls': ['PRIV-2'],
        'policies': [],
    },
    'P2.1.4: Documents and Obtains Consent for New Purpose and Uses': {
        'risks': [],
        'controls': ['PRIV-4'],
        'policies': [],
    },
    'P2.1.5: Obtains Explicit Consent for Sensitive Information': {
        'risks': [],
        'controls': ['PRIV-2', 'PRIV-4'],
        'policies': [],
    },
    'P2.1.6: Obtains Consent for Data Transfers': {
        'risks': [],
        'controls': ['PRIV-4'],
        'policies': [],
    },
    'P3.1.1: Limits the Collection of Personal Information': {
        'risks': [],
        'controls': ['PRIV-6'],
        'policies': [],
    },
    'P3.1.2: Collects Information by Fair and Lawful Means': {
        'risks': [],
        'controls': ['PRIV-5'],
        'policies': [],
    },
    'P3.1.3: Collects Information From Reliable Sources': {
        'risks': [],
        'controls': ['PRIV-11', 'PRIV-5'],
        'policies': [],
    },
    'P3.1.4: Informs Data Subjects When Additional Information Is Acquired': {
        'risks': [],
        'controls': ['PRIV-4'],
        'policies': [],
    },
    'P3.2.1: Informs Data Subjects of Consequences of Failure to Provide Consent': {
        'risks': [],
        'controls': ['PRIV-2', 'PRIV-4'],
        'policies': [],
    },
    'P3.2.2: Documents Explicit Consent to Retain Informatation': {
        'risks': [],
        'controls': ['PRIV-3'],
        'policies': [],
    },
    'P4.1.1: Uses Personal Information for Intended Purposes': {
        'risks': [],
        'controls': ['PRIV-6'],
        'policies': [],
    },
    'P4.2.1: Retains Personal Information': {
        'risks': [],
        'controls': ['PRIV-1', 'PRIV-8'],
        'policies': [],
    },
    'P4.2.2: Protects Personal Information': {
        'risks': [],
        'controls': ['PRIV-8'],
        'policies': [],
    },
    'P4.3.1: Captures, Identifies, and Flags Requests for Deletion': {
        'risks': [],
        'controls': ['PRIV-9'],
        'policies': [],
    },
    'P4.3.2: Disposes of, Destroys, and Redacts Personal Information': {
        'risks': [],
        'controls': ['PRIV-8'],
        'policies': [],
    },
    'P4.3.3: Destroys Personal Information': {
        'risks': [],
        'controls': ['PRIV-8'],
        'policies': [],
    },
    'P5.1.1: Authenticates Data Subjects': {
        'risks': [],
        'controls': ['PRIV-10'],
        'policies': [],
    },
    'P5.1.2: Permits Data Subjects Access to Their Personal Information': {
        'risks': [],
        'controls': ['PRIV-10'],
        'policies': [],
    },
    'P5.1.3: Provides Understandable Personal Information Within Reasonable Time': {
        'risks': [],
        'controls': ['PRIV-10'],
        'policies': [],
    },
    'P5.1.4: Informs Data Subjects If Access Is Denied': {
        'risks': [],
        'controls': ['PRIV-10'],
        'policies': [],
    },
    'P5.1.5: Responds to Data Controller Requests': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'P5.2.1: Communicates Denial of Access Requests': {
        'risks': [],
        'controls': ['PRIV-10'],
        'policies': [],
    },
    'P5.2.2: Permits Data Subjects to Update or Correct Personal Information': {
        'risks': [],
        'controls': ['PRIV-11', 'PRIV-13'],
        'policies': [],
    },
    'P5.2.3: Communicates Denial of Correction Requests': {
        'risks': [],
        'controls': ['PRIV-10'],
        'policies': [],
    },
    'P5.2.4: Responds to Data Controller Requests': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'P6.1.1: Communicates Privacy Policies to Third Parties': {
        'risks': [],
        'controls': ['TPM-1'],
        'policies': ['POL-34'],
    },
    'P6.1.2: Discloses Personal Information Only When Appropriate': {
        'risks': [],
        'controls': ['PRIV-11'],
        'policies': [],
    },
    'P6.1.3: Discloses Personal Information Only to Appropriate Third Parties': {
        'risks': [],
        'controls': ['TPM-1', 'TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'P6.1.4: Discloses Information to Third Parties for New Purposes and Uses': {
        'risks': [],
        'controls': ['PRIV-11'],
        'policies': [],
    },
    'P6.2.1: Creates and Retains Record of Authorized Disclosures': {
        'risks': [],
        'controls': ['PRIV-11', 'PRIV-12'],
        'policies': [],
    },
    'P6.3.1: Creates and Retains Record of Detected or Reported Unauthorized Disclosures': {
        'risks': [],
        'controls': ['IRM-4', 'PRIV-12', 'PRIV-7'],
        'policies': ['POL-20'],
    },
    'P6.4.1: Evaluates Third-Party Compliance With Privacy Commitments': {
        'risks': [],
        'controls': ['PRIV-11', 'TPM-1', 'TPM-2', 'TPM-3'],
        'policies': ['POL-34'],
    },
    'P6.4.2: Remediates Misuse of Personal Information by a Third Party': {
        'risks': [],
        'controls': ['IRM-1', 'TPM-1'],
        'policies': ['POL-34'],
    },
    'P6.4.3: Obtains Commitments to Report Unauthorized Disclosures': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'P6.5.1: Remediates Misuse of Personal Information by a Third Party': {
        'risks': [],
        'controls': ['IRM-1', 'TPM-1'],
        'policies': ['POL-34'],
    },
    'P6.5.2: Reports Actual or Suspected Unauthorized Disclosures': {
        'risks': [],
        'controls': ['IRM-5'],
        'policies': [],
    },
    'P6.6.1: Identifies Reporting Requirements': {
        'risks': [],
        'controls': ['IRM-1', 'PRIV-11', 'TPM-1'],
        'policies': ['POL-34'],
    },
    'P6.6.2: Provides Notice of Breaches and Incidents': {
        'risks': [],
        'controls': ['IRM-3', 'IRM-4'],
        'policies': [],
    },
    'P6.7.1: Identifies Types of Personal Information and Handling Process': {
        'risks': [],
        'controls': ['PRIV-11', 'PRIV-6', 'PRIV-7'],
        'policies': [],
    },
    'P6.7.2: Captures, Identifies, and Communicates Requests for Information': {
        'risks': [],
        'controls': ['PRIV-10'],
        'policies': [],
    },
    'P6.7.3: Responds to Data Controller Requests': {
        'risks': [],
        'controls': [],
        'policies': [],
    },
    'P7.1.1: Ensures Accuracy and Completeness of Personal Information': {
        'risks': [],
        'controls': ['PRIV-13'],
        'policies': [],
    },
    'P7.1.2: Ensures Relevance of Personal Information': {
        'risks': [],
        'controls': ['PRIV-6'],
        'policies': [],
    },
    'P8.1.1: Communicates to Data Subjects': {
        'risks': [],
        'controls': ['PRIV-12'],
        'policies': [],
    },
    'P8.1.2: Addresses Inquiries, Complaints, and Disputes': {
        'risks': [],
        'controls': ['PRIV-12'],
        'policies': [],
    },
    'P8.1.3: Documents and Communicates Dispute Resolution': {
        'risks': [],
        'controls': ['PRIV-12'],
        'policies': [],
    },
    'P8.1.4: Documents and Reports Compliance Review Results': {
        'risks': [],
        'controls': ['GOV-3'],
        'policies': [],
    },
    'P8.1.5: Documents and Reports Instances of Noncompliance': {
        'risks': [],
        'controls': ['PRIV-12'],
        'policies': [],
    },
    'P8.1.6: Performs Ongoing Monitoring': {
        'risks': [],
        'controls': ['GOV-3', 'GOV-9'],
        'policies': [],
    },
}
