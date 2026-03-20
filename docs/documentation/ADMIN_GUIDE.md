# Organization Admin Guide

Welcome to the CyberBridge Organization Admin Guide. This documentation covers administrative features available to organization administrators.

## Overview

As an Organization Admin, you have access to all standard user features plus additional capabilities for managing your organization's compliance program.

## Admin Dashboard

The admin dashboard provides extended metrics:

- **Organization Statistics**: User count, active frameworks, assessment progress
- **Compliance Overview**: Summary of compliance status across all frameworks
- **Recent Activity**: Audit trail of recent actions in your organization
- **Quick Actions**: Shortcuts including the User Guide wizard for onboarding

## User Management

Manage users within your organization.

### Viewing Users

1. Navigate to **Administration > Users**
2. View all users in your organization
3. See user details including role, status, and last login

### Creating Users

1. Click "Add User"
2. Enter user details:
   - **Email**: User's email address (used for login)
   - **First Name**: User's first name
   - **Last Name**: User's last name
   - **Role**: Select from available roles
3. Click "Create User"
4. The user will receive login credentials via email

### User Roles

- **Org User**: Standard access to compliance features
- **Org Admin**: Administrative access within the organization

### Editing Users

1. Select a user from the list
2. Click "Edit"
3. Modify user details or role
4. Click "Save Changes"

### Deactivating Users

1. Select a user from the list
2. Click "Deactivate"
3. Confirm the action
4. The user will no longer be able to log in

### User Approvals

1. Navigate to **Administration > Users**
2. Filter by status (Pending, Approved, Rejected, Active, Inactive)
3. Approve or reject pending registration requests
4. View online users and session information

## Framework Management

Create and manage compliance frameworks for your organization.

### Adding Frameworks from Templates

1. Navigate to **Frameworks > Configuration > Manage Frameworks**
2. Select "Add from Template"
3. Choose a template:
   - **CRA**: Cyber Resilience Act
   - **ISO 27001**: Information Security Management
   - **NIS2**: Network and Information Systems
   - **NIST CSF**: Cybersecurity Framework
   - **PCI DSS**: Payment Card Industry
   - **SOC 2**: Service Organization Controls
   - **HIPAA**: Health Insurance Portability
   - **GDPR**: General Data Protection
   - **CMMC 2.0**: Cybersecurity Maturity Model
   - **DORA**: Digital Operational Resilience Act
   - **And more...**
4. Click "Create Framework"
5. The framework will be created with all chapters, objectives, and questions

### Creating Custom Frameworks

1. Navigate to **Frameworks > Configuration > Manage Frameworks**
2. Click "Create Custom Framework"
3. Enter framework name and description
4. Configure scope settings (product-based, organization-based, or both)
5. Click "Create"

### Managing Chapters and Objectives

1. Navigate to **Frameworks > Configuration > Chapters & Objectives**
2. Select a framework
3. Add, edit, or delete chapters
4. Add objectives within chapters with title, description, utilities, subchapter, and requirements
5. Organize the hierarchy: Framework > Chapter > Subchapter > Objective

### Managing Questions

1. Navigate to **Frameworks > Configuration > Framework Questions**
2. Add questions with:
   - **Question Text**: The assessment question
   - **Assessment Type**: Conformity or Audit
   - **Frameworks**: Associate with one or more frameworks
   - **Mandatory**: Whether the question is required
3. Use CSV Upload for bulk import of questions
4. Edit or delete existing questions

### Framework Updates

1. Navigate to **Frameworks > Configuration > Framework Updates**
2. Track version changes to frameworks
3. Review and approve updates to framework structure before rollout
4. Manage framework versioning across your organization
5. Compare previous and updated framework content
6. Schedule rollout of approved framework updates to assessments and objectives

### Compliance Advisor (AI)

1. Navigate to **Frameworks > Compliance Advisor**
2. Enter a website URL to analyze your organization's online presence
3. The AI scrapes the website and evaluates which compliance frameworks are relevant
4. Review the company summary and framework recommendations with relevance levels (High, Medium, Low)
5. Seed recommended frameworks directly from the results page
6. View analysis history, reload previous results, or delete history records
7. Use the Compliance Advisor when onboarding to quickly identify which frameworks apply to your organization

## Assessment Administration

Oversee assessments in your organization.

### Viewing All Assessments

1. Navigate to **Assessments**
2. View assessments from all users in your organization
3. Filter by framework, status, or user

### Assessment Review

1. Select an assessment
2. Review submitted answers
3. Verify evidence documentation
4. Approve or request revisions

### Generating Reports

1. Select an assessment
2. Choose export format:
   - **PDF**: Professional compliance report
   - **CSV**: Data export for analysis
   - **ZIP**: Evidence files package
3. Click the appropriate export button

## Risk Assessment

Perform detailed risk assessments with structured scoring and treatment workflows.

### Conducting a Risk Assessment

1. Navigate to **Risks > Risk Assessment**
2. Select a risk from the list of registered risks
3. Create a new assessment or view existing assessments for the selected risk
4. Score the risk across multiple dimensions:
   - **Inherent Impact and Likelihood**: The raw risk score before any controls
   - **Current Impact and Likelihood**: The risk score with existing controls in place
   - **Target Impact and Likelihood**: The desired risk level after planned treatments
   - **Residual Impact and Likelihood**: The expected remaining risk after treatments
5. Record impact categories: Health, Financial, Service, Legal, and Reputation
6. View the risk matrix visualization showing severity levels
7. Set assessment status (Draft, In Review, Approved)

### Treatment Actions

1. Within a risk assessment, navigate to the Treatment Actions tab
2. Add treatment actions with:
   - **Description**: What action needs to be taken
   - **Due Date**: Target completion date
   - **Owner**: Person responsible for the action
   - **Status**: Open, In Progress, or Completed
   - **Completion Notes**: Details upon completion
3. Track action progress and update status as treatments are implemented
4. Link the risk to assets, controls, and framework objectives from the Connections tab

## Controls Management

Manage security controls across your organization.

### Control Register

1. Navigate to **Controls > Control Register**
2. Register controls with implementation status tracking
3. Organize controls into logical control sets
4. Link controls to risks they mitigate
5. Link controls to policies that define them
6. Connect controls to framework objectives
7. Track control review status for ongoing assurance

### Controls Library

1. Navigate to **Controls > Controls Library**
2. Browse pre-built control set templates from industry standards (NIST, ISO 27001, CIS, and more)
3. Preview all controls in a set before importing
4. Import entire control sets with one click into your Control Register
5. All imported controls start with "Not Implemented" status for tracking
6. View and manage previously imported control sets

## Incident Management

Track security incidents within your organization.

1. Navigate to **Risks > Incident Registration**
2. Register and categorize security incidents
3. Link incidents to affected assets
4. Connect incidents to related risks
5. Associate incidents with relevant frameworks
6. Track incident lifecycle and resolution status

## Security Advisories

Manage security advisories to communicate vulnerability information and coordinate responses.

### Advisory Dashboard

1. Navigate to **Risks > Security Advisories**
2. View the dashboard with key statistics: total advisories, published count, drafts, and critical/high severity counts
3. Search and filter advisories by code, title, severity, or CVE IDs

### Creating Advisories

1. Click "Add Advisory"
2. Enter advisory details:
   - **Title**: Advisory title describing the vulnerability or issue
   - **Description**: Detailed description of the security issue
   - **Severity**: Critical, High, Medium, or Low
   - **Affected Versions**: Software versions impacted
   - **Fixed Version**: Version containing the fix
   - **CVE IDs**: Associated CVE identifiers
   - **Workaround**: Temporary mitigation steps
   - **Status**: Draft, Review, Published, Updated, or Archived
   - **Linked Incident**: Optionally link to a registered incident
3. Click "Save" to create the advisory

### Managing Advisories

- Edit existing advisories to update status or add resolution details
- Transition advisories through the lifecycle: Draft > Review > Published > Updated > Archived
- Link advisories to incidents for full traceability
- Delete advisories that are no longer relevant

## Compliance Chain

View and manage relationships between all compliance entities.

### All Links

1. Navigate to **Compliance Chain > All Links**
2. View every relationship between assets, risks, controls, policies, objectives, and incidents
3. Create and delete compliance links
4. Search and filter by entity type

### Visual Map

1. Navigate to **Compliance Chain > Map**
2. View an interactive graph visualization
3. Navigate connections by clicking any entity
4. Identify gaps where entities lack proper linkage

### Gap Analysis

1. Navigate to **Compliance Chain > Gap Analysis**
2. Select a framework to analyze from the dropdown
3. Review the compliance summary with overall compliance score
4. Examine detailed breakdowns:
   - **Objectives Analysis**: Compliant, Partially Compliant, Not Compliant, In Review, Not Assessed, and Not Applicable counts with evidence coverage
   - **Assessment Analysis**: Total assessments, completion rate, unanswered questions
   - **Policy Analysis**: Policy status distribution, approved percentage, and policy coverage of objectives
5. Review the chapter-by-chapter compliance breakdown table
6. Identify specific gaps:
   - Objectives without evidence
   - Objectives marked as not compliant
   - Objectives without linked policies
7. Export the gap analysis to PDF for reporting and audit documentation

## Documents

### Policies

1. Navigate to **Documents > Policies**
2. Create, edit, and manage security policies
3. Map policies to frameworks and objectives
4. Track policy lifecycle (Draft > Review > Ready for Approval > Approved)

### Architecture Diagrams

1. Navigate to **Documents > Architecture**
2. Upload and manage architecture diagram files
3. Link diagrams to frameworks and risks

### Evidence Library

1. Navigate to **Documents > Evidence**
2. Upload and organize evidence items
3. Link evidence to frameworks and controls
4. Evidence integrity verification

### EU Declaration of Conformity

1. Navigate to **Documents > EU Declaration of Conformity**
2. Manage the EU Declaration of Conformity document required under the Cyber Resilience Act
3. Track completion status and ensure all required fields are addressed

### CRA Technical File Documentation

The Technical File section under Documents contains CRA-specific documentation pages required for EU Cyber Resilience Act compliance. Each page provides structured templates and tracking for the required technical documentation.

**Patch & Support Policy**

1. Navigate to **Documents > Technical File > Patch & Support Policy**
2. Document your organization's patch management and support commitments
3. Define update delivery mechanisms, support duration, and end-of-life policies

**Vulnerability Disclosure Policy**

1. Navigate to **Documents > Technical File > Vulnerability Disclosure**
2. Document your coordinated vulnerability disclosure process
3. Define reporting channels, response timelines, and disclosure procedures as required by CRA Article 11

**SBOM Management**

1. Navigate to **Documents > Technical File > SBOM Management**
2. Document your Software Bill of Materials management practices
3. Track SBOM generation, maintenance, and distribution processes

**Secure SDLC Evidence**

1. Navigate to **Documents > Technical File > Secure SDLC Evidence**
2. Document evidence of secure software development lifecycle practices
3. Record security activities performed during each development phase

**Security Design Documentation**

1. Navigate to **Documents > Technical File > Security Design**
2. Document security architecture decisions and design rationale
3. Describe how essential cybersecurity requirements are met in the product design

**Dependency Policy**

1. Navigate to **Documents > Technical File > Dependency Policy**
2. Document your third-party dependency management policies
3. Define processes for evaluating, approving, and monitoring dependencies

## CE Marking Checklists

Manage CE marking checklists for products with digital elements.

### Creating Checklists

1. Navigate to **Assets / Products > CE Marking Checklist**
2. Click "Create Checklist"
3. Select an asset and product type
4. The system generates a checklist with required items based on the product type

### Managing Checklist Items

1. Select a checklist from the list
2. View checklist items organized by category
3. Toggle items as complete or incomplete
4. Add custom checklist items specific to your product
5. Delete custom items that are no longer needed

### Document Status Tracking

1. Within a checklist, navigate to the Documents tab
2. Track completion status of required documents (EU DoC, Technical File, User Manual, Risk Assessment, Test Reports, SBOM)
3. Update document status: Not Started, In Progress, Review, or Complete
4. Monitor the overall checklist progress through the progress indicator

### Checklist Lifecycle

- Track overall checklist status: Not Started, In Progress, Ready, Approved
- Edit checklist details and update status as work progresses
- Delete checklists that are no longer needed

## Security Scanners

Access security scanning tools (if enabled for your organization).

### Available Scanners

- **Security Scanners (ZAP)**: Web application vulnerability scanning (Spider, Active, Full, API scans)
- **Network Scanner (Nmap)**: Network reconnaissance and port scanning
- **Code Analysis (Semgrep)**: Static code analysis for security issues
- **Dependency Check (OSV)**: Dependency vulnerability scanning
- **SBOM Generator (Syft)**: Software Bill of Materials generation

### Scan Findings

1. Navigate to **Security Tools > Scan Findings**
2. View aggregated statistics: total findings, breakdown by scanner type (Web App, Network, Code, Dependency), and breakdown by severity (Critical, High, Medium, Low, Info)
3. Review findings grouped by scan, with expandable rows showing individual findings
4. Filter findings by scanner type, severity, risk linkage status, or remediation status
5. Search findings by title, identifier, or description
6. Toggle findings as remediated to track resolution progress
7. Link scan findings to risks in the Risk Register for full traceability
8. View CVE details including CVSS scores and published dates where available
9. Delete scan records and their associated findings when no longer needed

### Scan History

- View all scans performed by organization users
- Export scan results for compliance documentation
- Clear historical scan data as needed

## Audit Engagements

Manage external audit workflows.

### Creating an Audit Engagement

1. Navigate to **Audit Engagements**
2. Create a time-bound audit engagement
3. Configure engagement details and scope
4. Set IP allowlisting for additional security

### Inviting Auditors

1. Click "Invite Auditor" on the engagement
2. Enter the auditor's email address
3. Select role: Guest Auditor (read-only) or Auditor Lead (findings + sign-off)
4. The auditor receives a secure magic link for authentication

### Managing the Audit

- Track auditor comments and findings
- Manage evidence requests and review workflow
- Process formal sign-off
- Review complete audit activity logs
- Monitor notification badges for new audit activity

## Administration

### Correlations

View relationships between compliance elements:

1. Navigate to **Administration > Correlations**
2. Select two frameworks to compare
3. Manually correlate related questions
4. Use AI-powered suggestion engine to discover correlations
5. Review suggestions with confidence scores
6. Manage all correlations in a searchable table

### Activity Log (History)

Track all actions in your organization:

1. Navigate to **Administration > Activity Log**
2. View chronological list of all actions
3. Filter by entity type, action, date range, or user
4. Export audit logs for compliance requirements

### Background Jobs

Monitor scheduled and running tasks:

1. Navigate to **Administration > Background Jobs**
2. View active and completed background jobs
3. Monitor scan schedules with details on frequency, last run, next run, and status
4. Create, edit, enable/disable, and delete scan schedules
5. Track database synchronization tasks and processing history
6. View history cleanup configuration and trigger manual cleanup
7. Monitor backup status and history

### Organization Settings

1. Navigate to **Administration > Organization Settings**
2. Manage organization details and branding (logo upload)
3. Configure history cleanup (retention days, cleanup frequency)

### System Settings

1. Navigate to **Administration > System Settings**
2. Configure scanner access for your organization
3. Manage framework template permissions
4. View and adjust organization-level settings

### Profile Management

Users can manage their own profiles, and admins can oversee user profile information.

1. Navigate to **Profile** (accessible from the user menu)
2. Update personal details:
   - **First Name** and **Last Name**
   - **Phone Number**
   - **Job Title** and **Department**
   - **Timezone**: Select from common timezone options
3. Configure notification preferences:
   - Email notifications
   - Assessment reminders
   - Security alerts
   - Scan completed notifications
   - Assessment incomplete reminders
   - Risk status critical alerts
   - Account status change notifications
4. Upload or remove a profile picture
5. View account information: email, role, and organization

## CRA Assessments (Public Tools)

CyberBridge provides two public assessment tools accessible from the login page without requiring authentication. These help organizations evaluate their CRA compliance needs.

### CRA Scope Assessment

1. Access from the login page or navigate to **/cra-scope-assessment**
2. Complete the three-step wizard:
   - **Step 1 - Company Details**: Enter company information
   - **Step 2 - Product Details**: Describe the product with digital elements
   - **Step 3 - Market Information**: Provide EU market distribution details
3. Review the scope assessment report to determine whether your product falls under CRA and its classification category (Default, Important Class I, Important Class II, or Critical)

### CRA Readiness Assessment

1. Access from the login page or navigate to **/cra-readiness-assessment**
2. Complete the multi-section assessment covering:
   - Company and product details
   - EU market information
   - Harmonised standards alignment
   - Risk methodology evaluation
   - Security practices maturity
3. Review the readiness report with scores and recommendations for achieving CRA compliance

## Best Practices

### Framework Setup

1. Start with a template framework for standard compliance
2. Customize objectives to match your organization's specific needs
3. Add custom questions for internal requirements

### User Management

1. Follow principle of least privilege
2. Regularly review user access
3. Deactivate users promptly when they leave
4. Approve pending registrations in a timely manner

### Assessment Management

1. Establish regular assessment schedules
2. Require evidence for critical compliance items
3. Review and approve assessments promptly
4. Use CSV import for bulk data migration

### Controls Management

1. Link every risk to at least one control
2. Link controls to the policies that govern them
3. Map controls to framework objectives for traceability
4. Regularly review control implementation status

### Security Scanning

1. Schedule regular security scans
2. Address high-severity findings immediately
3. Maintain scan history for audit purposes
4. Link scan findings to risks in the Risk Register

### Compliance Chain

1. Regularly review the Compliance Chain Map for gaps
2. Ensure every asset has associated risks identified
3. Verify all risks have controls and policies assigned
4. Confirm policies map to framework objectives

## Troubleshooting

### Common Issues

**User cannot log in:**
- Verify user account is active (not Pending or Rejected)
- Reset password if needed
- Check email address is correct
- Verify SSO configuration if using Google/Microsoft login

**Framework not appearing:**
- Ensure framework is associated with your organization
- Refresh the page
- Contact super admin if issue persists

**Assessment won't finalize:**
- Ensure all mandatory questions are answered
- Check for validation errors
- Verify required evidence is uploaded

**Scanner not visible:**
- Scanner access is controlled by domain settings
- Contact your super admin to enable scanner access for your organization

**Audit engagement issues:**
- Verify auditor email is correct
- Check IP allowlisting configuration
- Ensure magic link hasn't expired

## Getting Support

For issues beyond this documentation:
- Contact your organization's super administrator
- Use the contextual help (?) icons throughout the application
- Use the AI Compliance Advisor for framework guidance
- Visit the Documentation page for additional resources and API references

---

## Admin User Flow Examples

This chapter provides step-by-step walkthroughs of common administrative workflows using realistic data.

---

### Example Scenario: Setting Up Clone Systems for ISO 27001 Certification

**Company**: Clone Systems, Inc.
**Goal**: Set up the organization for ISO 27001 certification with proper frameworks, users, and controls
**Role**: Organization Admin

---

### Example 1: Seeding a Compliance Framework

**Navigate to**: Frameworks > Configuration > Manage Frameworks

**Step 1**: Click "Add from Template"

**Step 2**: Select the template:
- **Template**: ISO/IEC 27001:2022

**Step 3**: Click "Create Framework"

**Result**: The system creates the complete framework with:
- 14 chapters (A.5 through A.8, plus organizational clauses)
- 93 Annex A control objectives
- Assessment questions for conformity and audit types

You can now do the same for additional frameworks like CRA or NIS2 if needed.

---

### Example 2: Creating a User and Assigning Roles

**Navigate to**: Administration > Users

**Step 1**: Click "Add User"

**Step 2**: Fill in the user details:

| Field | Value |
|-------|-------|
| **Email** | j.smith@clone-systems.com |
| **First Name** | John |
| **Last Name** | Smith |
| **Role** | Org User |

**Step 3**: Click "Create User"

**Result**: John Smith now has access to Clone Systems' compliance data as a standard user. He can create assessments, register risks and policies, and run security scans.

To grant administrative access later, edit the user and change the role to "Org Admin".

---

### Example 3: Adding Framework Questions

**Navigate to**: Frameworks > Configuration > Framework Questions

**Option A: Add Individual Question**

| Field | Value |
|-------|-------|
| **Question Text** | Does the organization maintain a Software Bill of Materials (SBOM) for all products with digital elements? |
| **Assessment Type** | Conformity |
| **Frameworks** | ISO/IEC 27001:2022, CRA |
| **Mandatory** | Yes |

Click **Save**.

**Option B: Bulk Import via CSV**

1. Prepare a CSV file with columns: question_text, assessment_type, framework_names
2. Click "CSV Upload"
3. Select the file and confirm import
4. Verify imported questions in the table

---

### Example 4: Managing Chapters and Objectives

**Navigate to**: Frameworks > Configuration > Chapters & Objectives

**Step 1**: Select "ISO/IEC 27001:2022" from the framework dropdown

**Step 2**: Add a custom chapter:

| Field | Value |
|-------|-------|
| **Chapter Name** | Supply Chain Security |
| **Description** | Controls specific to software supply chain security per EU CRA requirements |

**Step 3**: Add an objective within the chapter:

| Field | Value |
|-------|-------|
| **Title** | SBOM Maintenance |
| **Description** | The organization shall maintain and publish a Software Bill of Materials for all products |
| **Subchapter** | Dependency Management |
| **Requirement** | SBOM must be updated with every software release and made available to customers |

Click **Save**. The new objective is now available in the Objectives Checklist and can be linked to policies.

---

### Example 5: Setting Up Correlations Between Frameworks

**Navigate to**: Administration > Correlations

**Step 1**: Select Framework A: **ISO/IEC 27001:2022**, Assessment Type: **Conformity**

**Step 2**: Select a question from Framework A:
- "Has the organization established an information security policy?"

**Step 3**: Select Framework B: **CRA**, Assessment Type: **Conformity**

**Step 4**: Select a related question from Framework B:
- "Does the manufacturer ensure essential cybersecurity requirements are met?"

**Step 5**: Click **Correlate** to link these questions.

**AI-Powered Alternative**:
1. Click "Generate AI Suggestions"
2. Set confidence threshold (e.g., 70%)
3. Review the suggested correlations with confidence scores
4. Apply relevant suggestions and dismiss false positives

**Result**: When a user answers one of these correlated questions in an assessment, they will see the related question from the other framework, reducing duplicate effort.

---

### Example 6: Creating an Audit Engagement

**Navigate to**: Audit Engagements

**Step 1**: Click "Create Audit Engagement"

| Field | Value |
|-------|-------|
| **Engagement Name** | ISO 27001 Stage 1 Audit - Q2 2025 |
| **Description** | External audit of Clone Systems ISMS for ISO 27001:2022 certification |
| **Start Date** | 2025-04-01 |
| **End Date** | 2025-04-15 |

**Step 2**: Click **Create**

**Step 3**: Invite the external auditor:

| Field | Value |
|-------|-------|
| **Auditor Email** | auditor@certificationbody.com |
| **Role** | Auditor Lead |

The auditor receives a secure magic link via email. They can access the audit workspace without creating a CyberBridge account.

**Step 4**: Configure IP allowlisting (optional):
- Add the auditor's office IP range for additional security

**During the Audit**:
- The auditor reviews assessments, objectives, and evidence
- They add comments and findings directly in the platform
- Evidence requests are tracked in the engagement
- The auditor signs off when the audit is complete
- All activity is logged for your records

---

### Example 7: Using the Compliance Advisor (AI)

**Navigate to**: Frameworks > Compliance Advisor

**Step 1**: Enter the Clone Systems website URL: `https://www.clone-systems.com`

**Step 2**: Click "Analyze" and wait for the AI to scrape and evaluate the website

**Step 3**: Review the results:
- **Company Summary**: AI-generated overview of Clone Systems' business profile and compliance needs
- **Framework Recommendations**: Ranked list of relevant frameworks with relevance levels:
  - ISO/IEC 27001:2022 - **High** relevance
  - CRA - **High** relevance
  - NIS2 - **Medium** relevance
  - NIST CSF - **Low** relevance

**Step 4**: Click "Seed Framework" next to any recommendation to add it directly to your organization

**Step 5**: View analysis history to revisit previous results or delete old records

This is particularly useful when onboarding a new organization or evaluating which frameworks apply to your business.

---

### Example 8: Reviewing the Compliance Chain

**Navigate to**: Compliance Chain > Map

After your team has registered assets, risks, controls, policies, and completed assessments, the Compliance Chain Map provides a visual overview:

1. **Identify gaps**: Look for assets without associated risks, or risks without controls
2. **Verify traceability**: Ensure each control links to both a risk and a policy
3. **Check objective coverage**: Confirm policies map to all relevant framework objectives
4. **Assess incident impact**: See which assets and risks are connected to recorded incidents

Navigate to **Compliance Chain > All Links** to export the relationships table or make bulk updates.

---

### Recommended Admin Workflow

1. **Seed frameworks** from templates (ISO 27001, CRA, NIS2, etc.)
2. **Create user accounts** for your compliance team
3. **Add custom questions** for organization-specific requirements
4. **Set up correlations** between frameworks to reduce duplicate effort
5. **Configure scanner access** if security scanning is needed
6. **Monitor progress** through the Dashboard and Activity Log
7. **Schedule audit engagements** when certification readiness is achieved
8. **Review the Compliance Chain** regularly to identify and close gaps
