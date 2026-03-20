# User Guide

Welcome to the CyberBridge User Guide. This documentation will help you navigate and use the platform effectively.

## Getting Started

### Logging In

1. Navigate to the login page
2. Enter your email address and password (or use SSO with Google/Microsoft if configured)
3. Click the "Sign In" button
4. Upon successful login, you will be redirected to the Dashboard

### Navigating the Interface

The CyberBridge interface consists of:

- **Sidebar Menu**: Located on the left, provides access to all features organized by category
- **Main Content Area**: Displays the current page content
- **User Profile**: Located at the bottom of the sidebar, shows your username and logout option

### Sidebar Menu Structure

- **Dashboard**: Overview of compliance metrics and activity
- **Assessments**: Create and manage compliance assessments
- **Frameworks**: Objectives checklist, Compliance Advisor, and framework configuration (admin)
- **Assets / Products**: Register and manage organizational assets, CE Marking Checklist
- **Risks**: Risk Register, Risk Assessment, Incident Registration, and Security Advisories
- **Controls**: Control Register and Controls Library
- **Documents**: Policies, Architecture Diagrams, Evidence Library, and CRA Technical File documentation
- **Compliance Chain**: All Links view, visual Map, and Gap Analysis
- **Security Tools**: Security Scanners, Code Analysis, Dependency Check, SBOM Generator, Scan Findings (if enabled)

## Dashboard

The Dashboard provides an overview of your organization's compliance status:

- **Key Metrics**: Total Assessments, Completed Assessments, Compliance Frameworks, Total Users, Total Policies, Total Risks
- **Active Frameworks**: All compliance frameworks in use with logos and descriptions
- **Recent Assessment Activity**: Carousel of donut charts showing assessment progress
- **Framework Progress**: Aggregated completion rates across frameworks
- **Analytics**: Pie charts for assessment types, policy statuses, and risk severities; line charts for trends over time
- **User Analytics**: Role distributions and session tracking
- **Quick Actions**: Shortcuts to common operations including the User Guide wizard

## Assessments

Conduct compliance assessments against your chosen frameworks.

### Starting an Assessment

1. Navigate to **Assessments** in the sidebar
2. Click "Create Assessment"
3. Select:
   - **Framework**: Which compliance framework to assess (ISO 27001, CRA, NIS2, NIST CSF, etc.)
   - **Assessment Type**: Conformity or Audit
   - **Scope**: Product, Organization, or Other
4. Enter assessment name and description
5. Click "Create"

### Completing an Assessment

1. Select an assessment from the list (or use "Load Assessment" dropdown)
2. Answer framework questions with detailed responses
3. Upload evidence files via drag-and-drop
4. Assign relevant policies to answers using the multi-select control
5. Track progress using the completion indicator and progress bar
6. Click "Finalize" when complete

### Assessment Data Management

- **CSV Import**: Upload a formatted CSV to populate answers across the entire assessment
- **CSV Export**: Extract answers for offline review or backup
- **PDF Export**: Generate professional compliance reports for stakeholders
- **ZIP Download**: Package all evidence files for archival
- **Pause and Resume**: Save progress and continue at any time

## Assets (Products & Services)

Register products and services that require cybersecurity compliance tracking.

### Adding an Asset

1. Navigate to **Assets / Products > Manage Assets** in the sidebar
2. Fill in the asset details:
   - **Name**: Asset identifier
   - **Version**: Current version number
   - **Justification**: Reason for registration
   - **License**: Applicable license information
   - **Description**: Detailed asset description
   - **SBOM**: Software Bill of Materials (recommended for software assets)
3. Select classifications:
   - **Status**: Live or Testing
   - **Economic Operator**: Manufacturer, Importer, or Distributor
   - **Asset Type**: Hardware or Software
   - **Criticality Level**: Based on CRA classification (ANNEX III Class I/II, ANNEX IV)
4. Click "Save"

### Managing Assets

- Click any row in the asset table to load details for editing
- Delete assets with confirmation dialog
- Sort and search the asset table
- Click "Export to PDF" to generate an asset registry report

### CE Marking Checklist

Create and manage CE marking checklists to track product conformity readiness.

#### Creating a Checklist

1. Navigate to **Assets / Products > CE Marking Checklist** in the sidebar
2. Click "Create Checklist"
3. Select the **Asset** the checklist applies to
4. Select the **Product Type** (Hardware or Software)
5. Click "Create" to generate the checklist with default CE marking items

#### Working with Checklist Items

1. Select a checklist from the list to view its details
2. Use the **Items** tab to work through each CE marking requirement:
   - Check off completed items to track readiness
   - Add custom items for organisation-specific requirements
   - Delete custom items that are no longer relevant
3. Monitor the **Readiness Score** which updates automatically as items are completed
4. View checklist status:
   - **Not Started**: No items completed
   - **In Progress**: Some items completed
   - **Ready**: All items completed
   - **Approved**: Checklist has been formally approved

#### Managing CE-Specific Details

- **CE Placement**: Document where the CE marking will be placed on the product
- **Notified Body Information**: Record notified body details for products requiring third-party assessment
- **Traceability Fields**: Enter version identifier, build identifier, Declaration of Conformity publication URL, and product variant information

#### Documentation Status Tracking

Track the status of each supporting document required for CE marking:

- **Not Started**: Document has not been created
- **In Progress**: Document is being prepared
- **Review**: Document is under review
- **Complete**: Document is finalised and ready

#### Searching and Filtering

- Use the search bar to filter checklists by name or asset
- Switch between tabs to view all checklists or filter by status

## Risk Management

### Risk Register

Identify and assess cybersecurity risks.

#### Adding a Risk

1. Navigate to **Risks > Risk Register** in the sidebar
2. Select **Product Type** (Hardware or Software)
3. Enter or select a **Risk Category** from autocomplete
4. Fill in risk details:
   - **Risk Description**: Detailed description of the risk
   - **Potential Impact**: What could happen if the risk materializes
   - **Control Measures**: Current and planned mitigations
5. Assess severity levels:
   - **Likelihood**: Low, Medium, High, or Critical
   - **Severity**: Low, Medium, High, or Critical
   - **Residual Risk**: Remaining risk after controls
6. Set **Status**: Reduce, Avoid, Transfer, Share, Accept, or Remediated
7. Assign scope (product or organization)
8. Click "Save Risk"

#### Exporting Risk Data

- Click "Export to PDF" to generate a risk register report
- Risk data feeds into Dashboard analytics

### Risk Assessment

1. Navigate to **Risks > Risk Assessment** in the sidebar
2. View the risk assessment matrix and analytics
3. Analyze risk distribution across severity levels
4. Review risk trends and treatment effectiveness

### Risk Assessment Detail

Perform detailed risk assessments with multi-dimensional scoring and treatment action tracking.

#### Accessing a Risk Assessment

1. Navigate to **Risks > Risk Assessment** in the sidebar
2. Click on any risk in the list to open its detailed assessment view
3. Alternatively, navigate directly from a risk in the Risk Register

#### Scoring Risks

Each risk assessment uses four scoring dimensions, each combining impact and likelihood on a 1-5 scale:

- **Inherent Risk**: The raw risk level before any controls are applied
- **Current Risk**: The risk level with existing controls in place
- **Target Risk**: The desired risk level after planned mitigations
- **Residual Risk**: The remaining risk after all treatment actions are complete

For each dimension, set the **Impact** and **Likelihood** values. The system calculates the combined risk score and displays it with a severity gauge (Low, Medium, High, Critical).

#### Impact Categories

Document the potential impact across multiple categories:

- **Health & Safety**: Impact on people
- **Financial**: Monetary impact
- **Service Delivery**: Impact on operations
- **Legal & Regulatory**: Compliance and legal impact
- **Reputation**: Impact on organisational reputation

#### Treatment Actions

Manage specific actions to reduce risk:

1. Click "Add Action" to create a treatment action
2. Fill in the action details:
   - **Description**: What needs to be done
   - **Owner**: Person responsible for the action
   - **Due Date**: Target completion date
   - **Status**: Open, In Progress, or Completed
   - **Completion Notes**: Record outcome when the action is finished
3. Edit or delete existing actions as they progress
4. Track completion rates to see how treatment is advancing

#### Connection Boards

Use the connection boards to link the risk to related compliance entities:

- **Linked Assets**: Connect the risk to affected products and services
- **Linked Controls**: Connect the risk to mitigating controls
- **Linked Objectives**: Connect the risk to framework objectives

### Incident Registration

Track and manage security incidents.

#### Adding an Incident

1. Navigate to **Risks > Incident Registration** in the sidebar
2. Enter incident details:
   - **Incident Name**: Clear identifier for the incident
   - **Description**: Detailed account of what happened
   - **Status**: Current lifecycle stage
   - **Severity**: Impact level
3. Link to affected assets
4. Link to related risks
5. Associate with relevant frameworks
6. Click "Save"

### Security Advisories

Publish and manage security advisories for your products to communicate vulnerabilities and fixes.

#### Advisory Dashboard

1. Navigate to **Risks > Security Advisories** in the sidebar
2. View the dashboard tab for an overview of advisory metrics:
   - Total advisories, severity distribution, and status breakdown
3. Switch to the registry tab to see all advisories in a searchable table

#### Creating an Advisory

1. Click "Create Advisory"
2. Fill in the advisory details:
   - **Title**: Clear description of the vulnerability or issue
   - **Description**: Detailed account of the vulnerability and its potential impact
   - **Severity**: Critical, High, Medium, or Low
   - **Status**: Draft, Review, Published, Updated, or Archived
   - **CVE IDs**: Associated Common Vulnerabilities and Exposures identifiers (comma-separated)
   - **Affected Versions**: Product versions impacted by the vulnerability
   - **Fixed Version**: The version that resolves the issue
   - **Workaround**: Temporary mitigation steps if a fix is not yet available
3. Optionally link the advisory to a related **Incident**
4. Click "Save"

#### Managing Advisories

- Click any advisory row to load it for editing
- Update the status as the advisory progresses through its lifecycle
- Delete advisories that are no longer relevant
- Use the search bar to filter advisories by code, title, severity, or CVE ID

## Controls Management

### Control Register

Register and track security controls that mitigate your identified risks.

1. Navigate to **Controls > Control Register** in the sidebar
2. Register controls with:
   - **Control Name**: Descriptive name for the control
   - **Description**: What the control does and how it works
   - **Implementation Status**: Current state of the control
   - **Control Set**: Logical grouping for the control
3. Link controls to:
   - **Risks**: The risks this control mitigates
   - **Policies**: The policies that define this control
   - **Objectives**: The framework objectives this control fulfils
4. Track review status for ongoing assurance

### Controls Library

Browse and import pre-loaded control sets from industry standards and best practices.

#### Browsing Control Sets

1. Navigate to **Controls > Controls Library** in the sidebar
2. View all available control set templates displayed as cards
3. Each card shows the control set name, description, and total number of controls
4. Review which control sets have already been imported into your organisation

#### Previewing Controls

1. Click the "Preview" button on any control set card
2. A modal displays all controls in the set with their codes, names, and descriptions
3. Review the controls to determine whether the set is relevant before importing

#### Importing Control Sets

1. Click "Import" on the control set card you want to add
2. The system imports all controls from the template into your Control Register
3. Imported controls are created with "Not Implemented" status by default
4. A summary displays the number of controls imported and any errors
5. Navigate to **Controls > Control Register** to manage and update the imported controls

#### Available Control Sets

Pre-loaded templates include industry standards such as NIST, ISO 27001, CIS Controls, and more. Each template is maintained as a versioned set that can be imported independently.

## Policy Management

Manage cybersecurity policies and link them to compliance objectives.

### Creating a Policy

1. Navigate to **Documents > Policies** in the sidebar
2. Enter policy title and body content
3. Set the policy status:
   - **Draft**: Initial creation
   - **Review**: Under review
   - **Ready for Approval**: Pending approval
   - **Approved**: Active policy
4. Map to frameworks and objectives:
   - Select one or more frameworks
   - Select chapters within the framework
   - Select specific objectives to map
5. Upload policy documents if needed
6. Click "Save Policy"

### Exporting Policies

- Click "Export to PDF" to generate a comprehensive policy register

## Objectives Checklist

Track compliance objectives within frameworks.

### Using the Checklist

1. Navigate to **Frameworks > Objectives** in the sidebar
2. Select a framework from the dropdown
3. View objectives organized by chapters and subchapters
4. Update compliance status for each objective:
   - **Not Assessed**: Not yet evaluated
   - **Not Compliant**: Requirements not met
   - **Partially Compliant**: Some requirements met
   - **In Review**: Under assessment
   - **Compliant**: All requirements satisfied
   - **Not Applicable**: Doesn't apply to your organization
5. Upload evidence files directly to objectives
6. Link objectives to policies and risks

### AI-Powered Suggestions

- Click "Generate AI Suggestions" to receive improvement recommendations
- Review each suggestion with its confidence score
- Apply suggestions that fit your context
- Export the checklist as PDF for audit documentation

## Compliance Advisor

Get AI-powered framework recommendations based on your organisation's web presence.

### Analysing a Website

1. Navigate to **Frameworks > Compliance Advisor** in the sidebar
2. Enter the website URL for your organisation or product
3. Click "Analyse" to start the AI-powered analysis
4. The system examines the website content and recommends applicable compliance frameworks
5. Review the results:
   - Each recommended framework is displayed with its name, relevance explanation, and a confidence indicator
   - Frameworks already present in your organisation are marked as "Already Seeded"

### Seeding Frameworks from Results

1. After analysis completes, review the recommended frameworks
2. Click "Seed Framework" next to any recommendation you want to add
3. The framework and its objectives are automatically created in your organisation
4. Navigate to **Frameworks > Objectives** to begin working with the newly seeded framework

### Analysis History

1. Click the "History" tab to view all past analyses
2. Each entry shows the URL analysed, date, and number of recommendations
3. Click "View" on any history entry to reload its results
4. Click "Delete" to remove historical analyses you no longer need

## Documents

### Architecture Diagrams

1. Navigate to **Documents > Architecture** in the sidebar
2. Upload architecture diagram files (images, PDFs)
3. Link diagrams to relevant frameworks and risks
4. Maintain architecture documentation for compliance reference

### Evidence Library

1. Navigate to **Documents > Evidence** in the sidebar
2. Upload and organize evidence items
3. Link evidence to frameworks and controls
4. Evidence integrity verification ensures documents haven't been tampered with
5. Centralized access for audit and compliance teams

### CRA Technical File Documentation

The CRA Technical File pages provide structured guidance and documentation templates for each area required by the EU Cyber Resilience Act. Each page presents numbered sections with descriptions of what must be documented. Navigate to these pages under **Documents > CRA Technical File** in the sidebar.

#### SBOM Management

Document your Software Bill of Materials practices:

1. **Format Requirements**: Define SBOM format (SPDX or CycloneDX) and ensure interoperability
2. **Top-Level Dependency Listing**: Document all top-level product dependencies and their versions
3. **Generation Frequency**: Set cadence for SBOM regeneration (per release or per CI/CD build)
4. **Version Tracking**: Link each SBOM to a specific product release and maintain archives
5. **Machine-Readable Delivery**: Define how SBOMs are delivered to downstream users and authorities
6. **SBOM Update Policy**: Establish processes for updating SBOMs when dependencies change

#### Secure SDLC Evidence

Document evidence of secure development practices:

1. **Code Review Process**: Describe peer review requirements, checklists, and approval workflows
2. **SAST/DAST Integration**: Demonstrate static and dynamic testing tool integration in the pipeline
3. **CI/CD Security Gates**: Define security gates that prevent insecure code from reaching production
4. **Pre-Release Security Checklist**: Maintain a documented checklist completed before each release
5. **Dependency Scanning**: Integrate automated SCA scanning with defined remediation SLAs
6. **Penetration Testing Records**: Maintain records of scope, methodology, findings, and remediation

#### Security Design Documentation

Document security architecture decisions and threat analysis:

1. **Threat Modeling**: Conduct systematic threat modeling using methodologies such as STRIDE or PASTA
2. **Attack Surface Analysis**: Map all entry points, interfaces, APIs, and external integrations
3. **Security Architecture Decisions**: Record cryptographic choices, authentication mechanisms, and rationale
4. **Data Flow Diagrams**: Create DFDs showing data movement, classification, and security control points
5. **Trust Boundaries**: Identify privilege boundaries and document validation controls at each
6. **Security Assumptions & Constraints**: Document design assumptions and security limitation factors

#### Patch & Support Policy

Define update and support commitments:

1. **Support Period Declaration**: State the minimum support period (at least 5 years under CRA)
2. **Update Delivery Timelines**: Define maximum timeframes for security patches by severity
3. **SLA Definitions**: Establish service-level agreements for patch response times
4. **End-of-Support Policy**: Define notification periods and migration guidance
5. **Customer Notification Process**: Describe how users are informed about available updates
6. **Emergency Patch Procedures**: Document expedited processes for zero-day and actively exploited vulnerabilities

#### Vulnerability Disclosure Policy

Establish coordinated vulnerability disclosure processes:

1. **Security Contact Point**: Designate a publicly documented single point of contact for reports
2. **Disclosure Timeline**: Define acknowledgment, triage, and remediation windows by severity
3. **Coordinated Vulnerability Disclosure Process**: Structure CVD coordination with reporters and CSIRTs
4. **Triage & Prioritisation Workflow**: Document internal triage using CVSS scoring and escalation triggers
5. **ENISA Reporting**: Establish procedures for 24-hour and 72-hour ENISA notifications (CRA Article 14)
6. **Public Advisory Process**: Define the process for publishing security advisories with CVE identifiers

#### Dependency Policy

Define governance for third-party components:

1. **Acceptable License Policy**: Maintain allow-lists and deny-lists for open-source licenses
2. **Vulnerability Threshold Policy**: Set maximum acceptable vulnerability severity for dependencies
3. **Update Frequency Requirements**: Establish minimum update cadences and maximum age thresholds
4. **Approved & Blocked Component List**: Curate pre-approved components and blocked components
5. **Transitive Dependency Management**: Monitor and manage indirect dependencies with full tree visibility
6. **Supply Chain Risk Assessment**: Evaluate maintainer trust, project health, and compromise impact

#### EU Declaration of Conformity

Track and manage your Declaration of Conformity readiness:

1. Navigate to the **EU Declaration of Conformity** page under CRA Technical File
2. View the **CRA Readiness Score** based on your objectives, assessments, and evidence
3. Review mandatory declaration elements:
   - Product identification details
   - Manufacturer details and contact information
   - Sole responsibility statement
   - Object of the declaration and product classification
   - Conformity assessment procedure followed
   - Harmonised standards and specifications referenced
4. Track whether each mandatory element is addressed with a visual readiness indicator

## Compliance Chain

Visualize and manage the relationships between all compliance entities.

### All Links View

1. Navigate to **Compliance Chain > All Links** in the sidebar
2. View every relationship between Assets, Risks, Controls, Policies, Objectives, and Incidents
3. Create new links between compliance entities
4. Delete links that are no longer relevant
5. Search and filter links by entity type

### Visual Map

1. Navigate to **Compliance Chain > Map** in the sidebar
2. View an interactive graph visualization of all compliance relationships
3. Click on any entity to navigate its connections
4. Identify gaps where entities lack proper linkage
5. Ensure complete traceability across your compliance program

### Gap Analysis

Assess compliance gaps across your frameworks with a dedicated analysis dashboard.

1. Navigate to **Compliance Chain > Gap Analysis** in the sidebar
2. Select a framework from the dropdown to generate the analysis
3. Review the compliance overview:
   - **Overall Compliance Score**: Aggregated percentage across all objectives
   - **Total Frameworks, Objectives, Assessments, and Policies**: Key summary metrics
4. Examine the **Objectives Analysis** breakdown:
   - Compliant, Partially Compliant, Not Compliant, In Review, Not Assessed, and Not Applicable counts
   - Evidence coverage: objectives with and without uploaded evidence
   - Overall compliance rate percentage
5. Review **Policy Coverage Metrics**:
   - Policy count by status (Draft, Review, Ready for Approval, Approved)
   - Approved policy percentage
   - Objectives with and without linked policies
   - Policy coverage percentage
6. Track **Assessment Progress**:
   - Total and completed assessments
   - Average progress across in-progress assessments
   - Unanswered questions count and completion rate
7. Explore the **Chapter-by-Chapter Breakdown** table:
   - Each chapter shows total objectives, compliant count, not compliant count, not assessed count, and compliance rate
8. Review **Identified Gaps**:
   - Objectives without evidence
   - Objectives marked as not compliant
   - Objectives without linked policies
   - Each gap entry shows the objective title, chapter, and current compliance status
9. Click **Export to PDF** to generate a gap analysis report for stakeholders or auditors

## Security Tools

Access integrated security scanning tools (if enabled for your organization).

### Security Scanners (ZAP)

Web application vulnerability scanning:

1. Navigate to **Security Tools > Security Scanners**
2. Enter the target URL
3. Select scan type: Spider, Active, Full, or API
4. Start the scan and monitor progress
5. Review results in the alerts table (risk level, confidence, occurrence count)
6. Export results as PDF
7. Use AI analysis for remediation suggestions

### Network Scanner (Nmap)

Network reconnaissance and security auditing:

1. Navigate to **Security Tools > Security Scanners** (Network tab)
2. Enter hostname, IP address, or IP range
3. Select scan type: Basic, Port Scan, All Ports, Aggressive, OS Detection, Network, Stealth, Fast
4. Review results in structured table and raw formats
5. Enable AI analysis for contextual interpretation

### Code Analysis (Semgrep)

Static code analysis for security issues:

1. Navigate to **Security Tools > Code Analysis**
2. Upload code archives (ZIP, TAR, compressed directories)
3. Configure rules or use automatic rule selection
4. Review findings with rule ID, severity, file, line number, and remediation guidance

### Dependency Check (OSV)

Dependency vulnerability scanning:

1. Navigate to **Security Tools > Dependency Check**
2. Upload lock files (package-lock.json, requirements.txt, go.mod, Gemfile.lock, Cargo.lock, pom.xml, etc.)
3. Review vulnerability findings with CVE/OSV IDs, severity, and fix status

### SBOM Generator (Syft)

Software Bill of Materials generation:

1. Navigate to **Security Tools > SBOM Generator**
2. Generate comprehensive package and dependency inventories
3. View SBOM reports for compliance documentation
4. Track scan history

### Scan Findings

View and manage aggregated findings across all security scanners in one place.

#### Viewing Findings

1. Navigate to **Security Tools > Scan Findings** in the sidebar
2. Review the summary statistics at the top:
   - Total findings, findings by severity (Critical, High, Medium, Low, Informational)
   - Remediated vs. open findings count
3. Findings are grouped by scan, showing the scanner type (Web App, Network, Code, Dependency), target, and timestamp
4. Expand any scan group to see individual findings with severity tags, descriptions, and CVE details

#### Filtering and Searching

- Filter findings by **Scanner Type**: ZAP, Nmap, Semgrep, or OSV
- Filter by **Severity**: Critical, High, Medium, Low, or Informational
- Filter by **Remediation Status**: Open or Remediated
- Use pagination to navigate through large result sets
- Click "Reset Filters" to clear all active filters

#### Remediation Tracking

1. Click the remediation toggle on any finding to mark it as remediated or reopen it
2. The summary statistics update in real time to reflect remediation progress
3. Use the remediation status filter to focus on open findings requiring attention

#### Linking Findings to Risks

1. Expand a finding to view its details
2. Click "Link to Risk" to associate the finding with an existing risk in the Risk Register
3. Linked risks are displayed alongside the finding for traceability
4. This connection feeds into the Compliance Chain and Dashboard analytics

#### Deleting Scan Records

1. Click the delete button on a scan group to remove the scan and all its findings
2. Confirm the deletion in the dialog
3. This is a permanent action and cannot be undone

## CRA Assessments

The CRA (Cyber Resilience Act) assessments are publicly accessible tools that help organisations determine their CRA obligations and readiness without requiring a login.

### CRA Scope Assessment

Determine whether your product falls within the scope of the EU Cyber Resilience Act using a guided multi-step wizard.

#### Running the Scope Assessment

1. Navigate to the CRA Scope Assessment page (accessible from the login page via "CRA Scope Assessment" link)
2. Complete the three-step wizard:

**Step 1 - Company Details**:
- Enter your company name, size, country, and sector
- Indicate the number of products with digital elements on the market

**Step 2 - Product Details**:
- Select the CRA category (Default, Important Class I, Important Class II, Critical, or Not Sure)
- Specify the product type (Hardware Only, Software Only, or Hardware & Software)
- Indicate whether the product imports third-party components
- Select the expected product lifecycle length
- Note whether the product contains open-source components

**Step 3 - Market Information**:
- Select market channels (Direct to Market, Distributor, or Both)
- Indicate EU member states where the product is sold
- Specify applicable languages for documentation
- Record any harmonised standards already applied

3. Click "Continue" to generate the scope report

#### Scope Report

The report provides:
- A determination of whether your product is in scope of the CRA
- The applicable product classification
- Recommended conformity assessment procedures
- Next steps for achieving compliance

### CRA Readiness Assessment

Evaluate your organisation's preparedness for CRA compliance with a comprehensive readiness questionnaire.

#### Running the Readiness Assessment

1. Navigate to the CRA Readiness Assessment page (accessible from the login page)
2. Work through the questionnaire sections using the step navigation:

- **Manufacturer Information**: Company details, contact information, staff training, and CRA impact awareness
- **Product Details**: CRA category, product type, market channels, open-source usage, and lifecycle
- **EU Market Information**: Target countries, languages, and harmonised standards
- **Development Practices**: Secure development lifecycle, code review, testing, and CI/CD practices
- **Cybersecurity Risk Management**: Risk assessment processes, threat modeling, and incident response
- **Vulnerability Management**: Vulnerability handling, disclosure processes, and patch management
- **Supply Chain**: Third-party component governance, dependency scanning, and supplier assessments
- **Technical Documentation**: SBOM practices, security documentation, and Declaration of Conformity readiness

3. Answer each question within the section before proceeding to the next
4. Click "Continue" to advance through sections, or "Back" to revise previous answers
5. After completing all sections, generate the readiness report

#### Readiness Report

The report provides:
- **Overall Readiness Score**: Aggregated percentage across all sections
- **Category Scores**: Individual scores for Risk Assessment, Vulnerabilities, and Documentation
- **Gap Identification**: Areas where your organisation needs improvement
- **Recommendations**: Specific actions to improve CRA readiness

## Profile Page

Manage your personal details, preferences, and account security.

### Viewing and Editing Your Profile

1. Click your username at the bottom of the sidebar
2. Select "Profile" to open the Profile page
3. Update your personal details:
   - **First Name** and **Last Name**
   - **Phone Number**
   - **Job Title**
   - **Department**
   - **Timezone**: Select from common timezones for accurate activity logging
4. Click "Save" to apply changes

### Profile Picture

1. Click the camera icon on your avatar
2. Select an image file to upload
3. The picture will appear next to your name throughout the platform
4. Click the delete icon to remove your current profile picture

### Notification Preferences

Toggle individual notification categories on or off:

- **Email Notifications**: General email alerts
- **Assessment Reminders**: Reminders for incomplete assessments
- **Security Alerts**: Critical security event notifications
- **Scan Completed**: Alerts when security scans finish
- **Risk Status Critical**: Notifications when risks reach critical severity
- **Account Status Change**: Alerts for account-related changes

### Changing Your Password

1. Scroll to the Security section on the Profile page (or click your username and select "Change Password")
2. Enter your new password
3. Click "Change Password"

## Logging Out

1. Click your username at the bottom of the sidebar
2. Click "Logout"
3. You will be redirected to the login page

---

## User Flow Examples

This chapter provides step-by-step walkthroughs of common compliance workflows using realistic data. These examples follow the recommended flow from the CyberBridge User Guide wizard: **Framework > Assets > Risks > Controls > Policies > Assessments > Objectives**.

---

### Example Scenario: Clone Systems ISO 27001 Compliance

**Company**: Clone Systems, Inc. (Network Security & Cybersecurity Solutions Provider)
**Product**: NextGen SIEM Pro v3.0.0 (Security Information and Event Management Platform)
**Framework**: ISO/IEC 27001:2022
**Goal**: Achieve ISO 27001 certification readiness

---

### Example 1: Registering an Asset

**Navigate to**: Assets / Products > Manage Assets

Fill in the registration form with the following values:

| Field | Value |
|-------|-------|
| **Asset Name** | NextGen SIEM Pro |
| **Version** | 3.0.0 |
| **Justification** | Next-generation SIEM platform with AI-powered threat detection requiring ISO 27001 compliance for enterprise market positioning |
| **License** | Commercial - Proprietary with Enterprise Licensing |
| **Description** | Advanced Security Information and Event Management platform featuring real-time threat detection, AI/ML-powered behavioral analytics, automated incident response, and integration with 500+ security tools |
| **SBOM** | ElasticSearch v8.11.1, Apache Kafka v3.6.0, TensorFlow v2.15.0, PostgreSQL v16.1, Redis v7.2.3 |
| **Asset Type** | Software |
| **Economic Operator** | Manufacturer |
| **Status** | Live |
| **Criticality** | ANNEX III - Class I > Security information and event management (SIEM) systems |

Click **Save**. The asset now appears in the asset table and is available as a scope entity for assessments.

---

### Example 2: Creating a Security Policy

**Navigate to**: Documents > Policies

Fill in the policy form:

| Field | Value |
|-------|-------|
| **Policy Title** | Information Security Policy |
| **Status** | Approved |
| **Policy Body** | *(see below)* |
| **Framework** | ISO/IEC 27001:2022 |
| **Objectives** | A.5.1 - Information Security Policy |

**Policy Body**:
```
Clone Systems is committed to protecting information assets from all threats,
whether internal or external, deliberate or accidental.

Scope: All information systems, networks, and services operated by Clone Systems,
including the NextGen SIEM Pro platform and its supporting infrastructure.

Key Requirements:
- Protect confidentiality, integrity, and availability of information
- Comply with ISO/IEC 27001:2022, SOC 2 Type II, and applicable regulations
- Report security incidents immediately through established channels
- Complete mandatory security awareness training annually
- Adhere to access control and authentication requirements
- Maintain business continuity and disaster recovery capabilities

Policy Owner: Chief Information Security Officer (CISO)
Effective Date: 2025-01-01
Review Date: 2026-01-01
```

Click **Save**. The policy is now linked to the ISO 27001 framework and the A.5.1 objective.

---

### Example 3: Identifying a Risk

**Navigate to**: Risks > Risk Register

Fill in the risk form:

| Field | Value |
|-------|-------|
| **Product Type** | Software |
| **Risk Category** | Access Control |
| **Status** | Reduce |
| **Likelihood** | Medium |
| **Severity** | Critical |
| **Residual Risk** | Medium |

**Risk Description**:
```
Unauthorized Access to SIEM Platform and Customer Data

The NextGen SIEM Pro platform collects and analyzes sensitive security logs
from customer environments. If administrative credentials are compromised
through phishing, credential stuffing, or insider threats, unauthorized access
could lead to data breaches exposing customer security information.

Attack Vectors:
- Phishing attacks targeting SIEM administrators
- Credential stuffing attacks against admin portals
- SQL injection or authentication bypass vulnerabilities
- Compromised API keys or service accounts
```

**Potential Impact**:
```
- Exposure of customer security logs and threat intelligence data
- Regulatory fines under GDPR and industry-specific regulations
- Customer contract terminations and reputational damage
- Loss of ISO 27001 certification

Financial Impact: $2M - $10M+
```

**Control Measures**:
```
Current Controls:
- Multi-factor authentication (MFA) mandatory for all admin access
- Role-based access control (RBAC) with least privilege
- Automated session timeout after 15 minutes of inactivity
- Administrative action logging and audit trails
- IP whitelisting for administrative access
- Database encryption at rest (AES-256) and in transit (TLS 1.3)

Planned Enhancements:
- Just-In-Time (JIT) privileged access provisioning
- User and Entity Behavior Analytics (UEBA) for anomaly detection
```

Click **Save Risk**. The risk is now documented and feeds into the Dashboard analytics.

---

### Example 4: Registering a Control

**Navigate to**: Controls > Control Register

Register a control that mitigates the access risk identified above:

| Field | Value |
|-------|-------|
| **Control Name** | Multi-Factor Authentication for Administrative Access |
| **Description** | All administrative access to the NextGen SIEM Pro platform requires multi-factor authentication using TOTP or hardware tokens. This control reduces the risk of unauthorized access through compromised credentials. |
| **Implementation Status** | Implemented |
| **Control Set** | Access Control |

Link this control to:
- **Risk**: "Unauthorized Access to SIEM Platform and Customer Data"
- **Policy**: "Information Security Policy"
- **Objective**: A.8.5 - Secure Authentication (ISO 27001)

Click **Save**. The control now bridges the gap between the identified risk and the policy governing it.

You can also browse **Controls > Controls Library** to import pre-built control templates for common security measures like encryption, backup procedures, and incident response.

---

### Example 5: Running a Compliance Assessment

**Navigate to**: Assessments

**Step 1: Create the Assessment**

| Field | Value |
|-------|-------|
| **Framework** | ISO/IEC 27001:2022 |
| **Assessment Type** | Internal Audit |
| **Scope** | Product: NextGen SIEM Pro |
| **Assessment Name** | Pre-certification internal audit for NextGen SIEM Pro |

Click **Create**.

**Step 2: Answer Questions**

Answer the assessment questions. Here are example responses for key controls:

**Question: "Has the organization established and documented an information security policy?" (A.5.1)**
- **Answer**: Yes. The Information Security Policy was approved by the CISO on 2025-01-01. It covers all information systems including the NextGen SIEM Pro platform.
- **Evidence**: Upload `Information_Security_Policy.pdf`
- **Policy Link**: Select "Information Security Policy"

**Question: "Is the allocation and use of privileged access rights restricted and managed?" (A.8.2)**
- **Answer**: Yes. MFA is enforced for all administrative access. RBAC with least privilege is implemented. Administrative actions are logged with IP whitelisting active. Quarterly access reviews are completed.
- **Policy Link**: Select "Information Security Policy"

**Question: "Are backup copies of information and software maintained and regularly tested?" (A.8.13)**
- **Answer**: Partially. Daily backups are performed but restoration testing is only done quarterly. Plan to increase testing to monthly starting Q4 2025.

Track your progress using the progress bar. You can pause and resume the assessment at any time.

**Step 3: Export Results**
- Click **Export to PDF** for a professional compliance report
- Click **Export ZIP** to package all evidence files

---

### Example 6: Completing the Objectives Checklist

**Navigate to**: Frameworks > Objectives

**Step 1**: Select **ISO/IEC 27001:2022** from the framework dropdown.

**Step 2**: Work through the objectives by chapter. For each objective, set the compliance status:

| Objective | Status | Evidence/Notes |
|-----------|--------|----------------|
| A.5.1 - Information Security Policy | Compliant | Policy approved 2025-01-01 |
| A.5.15 - Access Control | Partially Compliant | Procedures exist, formal policy pending |
| A.6.8 - Incident Management | Compliant | 24/7 incident hotline established |
| A.8.2 - Privileged Access Rights | Compliant | MFA + RBAC + IP whitelisting |
| A.8.13 - Information Backup | Partially Compliant | Increase test frequency to monthly |

**Step 3**: Upload evidence files directly to each objective for audit readiness.

**Step 4**: Click **Generate AI Suggestions** to receive improvement recommendations for objectives marked as Partially Compliant or Not Compliant.

**Step 5**: Export the checklist as PDF for stakeholders or auditors.

---

### Example 7: Registering an Incident

**Navigate to**: Risks > Incident Registration

If a security event occurs, document it:

| Field | Value |
|-------|-------|
| **Incident Name** | Phishing Attempt Targeting SIEM Administrators |
| **Description** | On 2025-03-15, three SIEM administrators received targeted phishing emails impersonating the IT support team. The emails contained malicious links designed to harvest MFA credentials. All emails were detected by the email security gateway and no credentials were compromised. |
| **Status** | Resolved |
| **Severity** | Medium |

Link to:
- **Affected Asset**: NextGen SIEM Pro
- **Related Risk**: Unauthorized Access to SIEM Platform and Customer Data
- **Framework**: ISO/IEC 27001:2022

Click **Save**. The incident is now tracked and linked to the relevant compliance entities.

---

### Example 8: Viewing the Compliance Chain

**Navigate to**: Compliance Chain > Map

After completing the steps above, the Compliance Chain map will show the full traceability:

```
NextGen SIEM Pro (Asset)
    |
    +-- Unauthorized Access Risk (Risk)
    |       |
    |       +-- MFA for Admin Access (Control)
    |       |       |
    |       |       +-- Information Security Policy (Policy)
    |       |               |
    |       |               +-- A.5.1 Information Security Policy (Objective)
    |       |               +-- A.8.5 Secure Authentication (Objective)
    |       |
    |       +-- Phishing Attempt Incident (Incident)
    |
    +-- Supply Chain Risk (Risk)
            |
            +-- Dependency Scanning Control (Control)
                    |
                    +-- Vulnerability Management Policy (Policy)
                            |
                            +-- A.8.8 Management of Technical Vulnerabilities (Objective)
```

Navigate to **Compliance Chain > All Links** to see every relationship in a searchable table format.

---

### Example 9: Running a Security Scan

**Navigate to**: Security Tools > Dependency Check

Scan the NextGen SIEM Pro dependencies for known vulnerabilities:

1. Upload `requirements.txt` containing the project dependencies
2. Click **Start Scan**
3. Review the findings:

| Package | Vulnerability | Severity | Fix Available |
|---------|--------------|----------|---------------|
| TensorFlow 2.15.0 | CVE-2024-XXXX | High | Yes (2.15.1) |
| Redis 7.2.3 | CVE-2024-YYYY | Medium | Yes (7.2.4) |

4. Click **AI Analysis** for contextual remediation suggestions
5. Export results as PDF for compliance documentation
6. Link findings to the "Supply Chain Compromise" risk in the Risk Register

You can also:
- Run **Security Scanners** (ZAP) against web endpoints with target URL `https://siem.clone-systems.com`
- Run **Code Analysis** (Semgrep) by uploading a ZIP of the source code
- Generate an **SBOM** using the SBOM Generator for CRA compliance

---

### Example 10: Uploading Evidence and Architecture

**Evidence Library** (Documents > Evidence):
- Upload the penetration test report from the latest quarterly assessment
- Link it to ISO 27001 framework and the "Vulnerability Management" control
- The system verifies evidence integrity automatically

**Architecture Diagrams** (Documents > Architecture):
- Upload the NextGen SIEM Pro system architecture diagram
- Link it to ISO 27001 and the access control risks
- Reference this during audit engagements

---

### Putting It All Together

Following the Compliance Chain workflow ensures complete traceability:

1. **Assets** are the products and systems you need to protect
2. **Risks** are the threats and vulnerabilities each asset faces
3. **Controls** are the safeguards you implement to mitigate those risks
4. **Policies** formalise controls into documented rules for your organisation
5. **Objectives** are the framework goals that your policies and controls fulfil, proving compliance
6. **Assessments** evaluate how well you meet each objective
7. **Incidents** document security events and link them back to risks and assets
8. **Evidence** and **Architecture** provide supporting documentation for auditors

Each entity links to the others, creating an unbroken chain from asset to compliance objective. Use the **Compliance Chain Map** to visualize these relationships and identify any gaps.

---

## Getting Help

If you need assistance:

- Use the **User Guide** wizard on the Dashboard for a step-by-step walkthrough
- Check the info icons (?) next to section titles for contextual help
- Use the **AI Compliance Advisor** for real-time guidance during assessments
- Visit the **Documentation** page for role-based guides and API references
- Contact your organization administrator for access or configuration issues
