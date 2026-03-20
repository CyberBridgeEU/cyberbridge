# Onboarding Training Guide

This guide serves as a **training video script reference** for CyberBridge platform onboarding. It follows a top-down role progression — Super Admin sets up the system, Org Admin configures the organization, and Org User performs day-to-day compliance work.

Each section is structured as a scene-by-scene walkthrough with exact navigation paths, button clicks, and expected results — ready to use as a video recording script.

---

## Role Permissions Matrix

Before diving into the flows, here is a complete reference of what each role can access:

| Feature / Action | Org User | Org Admin | Super Admin |
|------------------|----------|-----------|-------------|
| **Dashboard & Navigation** | | | |
| View Dashboard | Yes | Yes | Yes |
| AI Assistant (Chatbot) | Yes | Yes | Yes |
| Documentation | Yes | Yes | Yes |
| Profile & Password | Yes | Yes | Yes |
| **Frameworks** | | | |
| View Objectives Checklist | Yes | Yes | Yes |
| Compliance Advisor | No | Yes | Yes |
| Manage Frameworks | No | Yes (own org) | Yes (all) |
| Chapters & Objectives | No | Yes | Yes |
| Framework Questions | No | Yes | Yes |
| Framework Updates | No | Yes | Yes |
| Seed Frameworks from Templates | No | Yes | Yes |
| Clone Frameworks across Orgs | No | No | Yes |
| **Assets & Products** | | | |
| Manage Assets/Products | Yes | Yes | Yes |
| CE Marking Checklist | Yes | Yes | Yes |
| **Risk Management** | | | |
| Risk Register | Yes | Yes | Yes |
| Risk Assessment | Yes | Yes | Yes |
| Incident Registration | Yes | Yes | Yes |
| Security Advisories | Yes | Yes | Yes |
| **Controls** | | | |
| Control Register | Yes | Yes | Yes |
| Controls Library | Yes | Yes | Yes |
| **Documents** | | | |
| Policies | Yes | Yes | Yes |
| Architecture | Yes | Yes | Yes |
| Evidence | Yes | Yes | Yes |
| CRA Technical File (6 pages) | CRA Mode | CRA Mode | CRA Mode |
| EU Declaration of Conformity | CRA Mode | CRA Mode | CRA Mode |
| **Compliance Chain** | | | |
| All Links | Yes | Yes | Yes |
| Visual Map | Yes | Yes | Yes |
| Gap Analysis | Yes | Yes | Yes |
| **Security Tools** | Domain | Domain | Domain |
| Security Scanners (ZAP/Nmap) | Domain | Domain | Domain |
| Code Analysis (Semgrep) | Domain | Domain | Domain |
| Dependency Check (OSV) | Domain | Domain | Domain |
| SBOM Generator (Syft) | Domain | Domain | Domain |
| Scan Findings | Domain | Domain | Domain |
| **Assessments** | | | |
| Conduct Assessments | Yes | Yes | Yes |
| AI Suggest Answers | Yes | Yes | Yes |
| View Reports | Yes | Yes | Yes |
| **Audit** | | | |
| Audit Engagements | No | Yes | Yes |
| **Administration** | | | |
| Manage Users | No | Yes (own org) | Yes (all) |
| Manage Organizations | No | Own org only | Yes (all) |
| Activity Log / History | No | Yes | Yes |
| Correlations | No | Yes | Yes |
| Background Jobs | No | Yes | Yes |
| System Settings | No | Limited | Full |
| LLM Configuration | No | No | Yes |
| SSO Configuration | No | No | Yes |
| SMTP Configuration | No | No | Yes |
| CRA Mode Toggle | No | No | Yes |
| Focused Mode | No | No | Yes |
| Domain Blacklist | No | No | Yes |
| NVD / EUVD Sync | No | No | Yes |
| Backup Management | No | No | Yes |
| Scan Schedules | No | Yes | Yes |
| **Public Tools (no login)** | | | |
| CRA Scope Assessment | Public | Public | Public |
| CRA Readiness Assessment | Public | Public | Public |

> **"Domain"** = Access is controlled by whether the organization's domain is in the scanner access allowlist (configured by Super Admin in System Settings).
>
> **"CRA Mode"** = Only visible when CRA Mode is enabled for the organization in System Settings.

---

## Part 1: Super Admin — System Setup

**Role**: Super Admin
**Purpose**: Establish the platform foundation — organizations, frameworks, system settings, and integrations.
**Estimated video duration**: 15–20 minutes

---

### Scene 1.1: Login & Dashboard Overview

**Navigate to**: Login Page

1. Enter Super Admin credentials and click **"Sign In"**
2. You land on the **Dashboard** — point out the key sections:
   - Quick statistics cards (users, frameworks, assessments, etc.)
   - Quick action buttons
   - Recent activity feed

> **Cut point** — Pause before moving to organization setup.

---

### Scene 1.2: Create Organizations

**Navigate to**: Administration > Organizations

1. Click **"Create Organization"**
2. Fill in the organization details:
   - **Name**: e.g., "Clone Systems Inc."
   - **Domain**: e.g., "clonesystems.com"
   - **Description**: Brief description of the organization
   - **Logo**: Upload organization logo (optional)
3. Click **"Save"**
4. Show the organization appearing in the list

**What to highlight**:
- Each organization is an isolated tenant — users, data, and frameworks are separated
- The domain field is used for scanner access control

> **Cut point**

---

### Scene 1.3: Configure System Settings

**Navigate to**: Administration > System Settings

Walk through each settings section:

1. **LLM Configuration**
   - Select LLM provider (llama.cpp, OpenAI, Anthropic, Google, X AI, QLON)
   - Set the model name and API URL
   - Test the connection
   - **Explain**: LLM powers AI Suggest Answers, Compliance Advisor, and the AI Chatbot

2. **Scanner Access**
   - Add organization domains to the scanner allowlist
   - **Explain**: Only organizations in this list can use Security Tools (ZAP, Nmap, Semgrep, OSV, Syft)

3. **CRA Mode**
   - Toggle CRA Mode on/off per organization
   - **Explain**: When enabled, users see the Technical File documentation pages (Patch Policy, Vulnerability Disclosure, SBOM Management, etc.)

4. **SSO Configuration** (if applicable)
   - Configure OAuth provider settings

5. **SMTP Configuration** (if applicable)
   - Set up email server for notifications

6. **Focused Mode**
   - Toggle to simplify the Super Admin sidebar to administrative-only items
   - **Explain**: Useful when you only need to manage system settings without the full compliance menu

7. **Domain Blacklist**
   - Add domains to block from registration

> **Cut point**

---

### Scene 1.4: Seed Frameworks from Templates

**Navigate to**: Frameworks > Configuration > Manage Frameworks

1. Click **"Add from Template"**
2. Browse available templates:
   - **ISO/IEC 27001:2022** — Information security management
   - **CRA (EU Cyber Resilience Act)** — Product cybersecurity
   - **NIS2** — Network and information security
   - Other available templates
3. Select **ISO/IEC 27001:2022** and click **"Create Framework"**
4. Show the seeded framework with its chapters, objectives, and questions
5. Repeat for **CRA** framework to demonstrate multi-framework support

**What to highlight**:
- Templates come pre-loaded with chapters, objectives, and assessment questions
- Frameworks can be cloned across organizations (Super Admin only)
- Each organization can have its own set of frameworks

> **Cut point**

---

### Scene 1.5: Set Up Correlations

**Navigate to**: Administration > Correlations

1. Select two frameworks to correlate (e.g., ISO 27001 and CRA)
2. Click **"AI Suggest"** to auto-generate correlations using LLM
3. Review the suggested correlations — accept or reject each one
4. Show the correlation mapping between framework questions

**What to highlight**:
- Correlations link related questions across different frameworks
- AI suggestions speed up the mapping process significantly
- This enables cross-framework compliance tracking

> **Cut point**

---

### Scene 1.6: Background Jobs & Maintenance

**Navigate to**: Administration > Background Jobs

1. **NVD Synchronization**
   - Configure NVD API key
   - Trigger a manual sync
   - Show CVE statistics (total, severity breakdown)

2. **EUVD Synchronization**
   - Configure ENISA EUVD sync interval
   - Trigger a manual sync

3. **Backup Management**
   - Show backup list
   - Trigger a manual backup
   - Demonstrate download and restore options
   - Configure backup frequency and retention per organization

4. **Scan Schedules**
   - Create a scheduled scan (select scanner type, target, interval)

**What to highlight**:
- NVD/EUVD sync keeps vulnerability data current for Security Advisories
- Backups should be configured for production environments
- Scan schedules automate recurring security assessments

> **Cut point**

---

### Scene 1.7: Create Users

**Navigate to**: Administration > Users

1. Click **"Create User"**
2. Create an **Org Admin** user:
   - Fill in name, email, password
   - Select organization: "Clone Systems Inc."
   - Select role: **Organization Admin**
   - Click **"Save"**
3. Create an **Org User**:
   - Same process, select role: **Org User**
   - Click **"Save"**
4. Show both users in the users list with their roles and statuses

**What to highlight**:
- Super Admin can create users in any organization
- Users with "pending_approval" status need to be activated
- Each user inherits their organization's framework and settings context

> **Cut point** — End of Super Admin section. Transition to Org Admin.

---

### Scene 1.8: Activity Log

**Navigate to**: Administration > Activity Log

1. Show the activity log with recent actions
2. Filter by user, action type, or date range
3. **Explain**: All significant actions are logged for audit trails

> **Cut point** — End of Part 1.

---

## Part 2: Org Admin — Organization Configuration

**Role**: Organization Admin (log out of Super Admin, log in as Org Admin)
**Purpose**: Configure the organization's compliance environment — chain links, policies, products, and assessments.
**Estimated video duration**: 25–35 minutes

---

### Scene 2.1: Login & Dashboard

**Navigate to**: Login Page

1. Log in with Org Admin credentials
2. Point out dashboard differences from Super Admin:
   - Organization-specific statistics
   - Same quick actions but scoped to own organization

> **Cut point**

---

### Scene 2.2: Seed Frameworks & Review Objectives

**Navigate to**: Frameworks > Configuration > Manage Frameworks

1. Show any frameworks already seeded by Super Admin (if applicable)
2. Click **"Add from Template"** to seed a new framework:
   - Select a template (e.g., ISO/IEC 27001:2022)
   - Click **"Create Framework"**
   - Show the seeded framework with chapters, objectives, and questions
3. **Explain**: Org Admins can seed frameworks from templates for their own organization; only Super Admins can clone frameworks across organizations

**Navigate to**: Frameworks > Configuration > Chapters & Objectives

4. Browse chapters and their objectives
5. Show how to add custom chapters or objectives if needed
6. **Explain**: These objectives form the basis of the compliance checklist

> **Cut point**

---

### Scene 2.3: Compliance Advisor

**Navigate to**: Frameworks > Compliance Advisor

1. Enter a website URL to analyze (e.g., your organization's product page)
2. Click **"Analyze"** — the AI scrapes the website and recommends relevant frameworks
3. Review recommendations with relevance scores
4. Click **"Seed Framework"** on a recommended framework to add it directly

**What to highlight**:
- AI-powered framework recommendation based on your actual product/service
- Saves time vs. manually researching which frameworks apply
- History of previous analyses is preserved

> **Cut point**

---

### Scene 2.4: Register Products / Assets

**Navigate to**: Assets / Products > Manage Assets

1. Click **"Create Asset"**
2. Fill in product details:
   - **Name**: e.g., "NextGen SIEM Pro v3.0.0"
   - **Product Type**: Select appropriate type
   - **Economic Operator**: Select or create operator
   - **Status**: Set initial status
   - **Criticality**: Select criticality level (if CRA Mode enabled)
3. Click **"Save"**
4. Show the asset in the product list

**What to highlight**:
- Products/assets are used as scope entities for the objectives checklist
- Product type drives risk categorization
- Criticality level affects CRA compliance requirements

> **Cut point**

---

### Scene 2.5: Set Up the Compliance Chain (Chain Links)

**Navigate to**: Compliance Chain > All Links

1. Click **"Check for Updates"**
   - The system analyzes the framework and identifies missing chain links
   - Review the proposed changes (new risks, controls, policies, objective links)
2. Click **"Apply Updates"** to seed all chain links
3. Show the populated chain links table with:
   - Risks linked to Controls
   - Controls linked to Policies
   - Policies linked to Objectives

**Navigate to**: Compliance Chain > Map

4. Show the visual compliance chain map
5. Click on nodes to explore connections
6. **Explain**: The chain links connect Risks → Controls → Policies → Objectives

**What to highlight**:
- Chain links create the traceability backbone of your compliance program
- "Check for Updates" can be re-run after framework changes to catch new connections
- The visual map gives stakeholders a bird's-eye view of compliance coverage

> **Cut point**

---

### Scene 2.6: Gap Analysis

**Navigate to**: Compliance Chain > Gap Analysis

1. Select a framework (e.g., ISO 27001)
2. Review the compliance score and breakdown:
   - **Objectives Analysis**: Compliant vs. non-compliant objectives
   - **Assessment Analysis**: Completed vs. pending assessments
   - **Policy Analysis**: Active vs. inactive policies
3. Identify gaps — objectives without linked policies, missing assessments
4. Show **PDF Export** — click to generate a gap analysis report

**What to highlight**:
- Gap analysis shows exactly where your compliance program has holes
- Use this to prioritize remediation efforts
- The PDF report is useful for management reviews and audit preparation

> **Cut point**

---

### Scene 2.7: Manage Policies

**Navigate to**: Documents > Policies

1. Show existing policies (seeded via chain links)
2. Click on a policy to view details:
   - Title, description, status
   - Linked frameworks
   - Linked objectives
3. Update a policy status (e.g., Draft → Active)
4. Create a new custom policy if needed

**What to highlight**:
- Policies linked to objectives appear in the objectives checklist
- Policy status affects compliance scoring
- Policies can be linked to multiple frameworks

> **Cut point**

---

### Scene 2.8: Manage Risks

**Navigate to**: Risks > Risk Register

1. Show existing risks (seeded via chain links)
2. Click on a risk to view details
3. Update risk fields: likelihood, severity, status, treatment actions

**Navigate to**: Risks > Risk Assessment

4. Select a risk to perform a full assessment
5. Walk through the scoring dimensions:
   - Inherent risk (before controls)
   - Current risk (with existing controls)
   - Target risk (desired state)
   - Residual risk (after planned controls)
6. Save the assessment

**What to highlight**:
- Risk assessment provides a structured way to evaluate and track risk treatment
- Risks linked via chain links automatically connect to controls and policies
- Risk matrix visualization shows the overall risk landscape

> **Cut point**

---

### Scene 2.9: Manage Controls

**Navigate to**: Controls > Control Register

1. Show existing controls (seeded via chain links)
2. Click on a control to view details and linked risks/policies

**Navigate to**: Controls > Controls Library

3. Browse pre-built control templates from industry standards
4. Preview a control set
5. Click **"Import"** to add a control set to the organization's register

**What to highlight**:
- Controls Library provides ready-made templates from industry standards
- Imported controls can be customized after import
- Controls form the middle layer of the compliance chain (Risks → Controls → Policies)

> **Cut point**

---

### Scene 2.10: Configure Assessments

**Navigate to**: Assessments

1. Show the assessments list
2. Click **"Create Assessment"**
3. Select:
   - **Framework**: ISO 27001
   - **Assessment Type**: e.g., Conformity Assessment
4. Begin answering questions
5. Demonstrate **"AI Suggest Answers"**:
   - Click the AI button
   - Watch as LLM generates suggested answers one by one
   - Review and accept/modify each suggestion
6. Submit the assessment

**What to highlight**:
- AI suggestions dramatically speed up assessment completion
- Each suggestion can be individually accepted, modified, or rejected
- Assessments can be saved as draft and completed later

> **Cut point**

---

### Scene 2.11: Set Up Audit Engagements

**Navigate to**: Audit Engagements

1. Click **"Create Engagement"**
2. Fill in audit details:
   - Title, scope, auditor details
   - Select framework and assessment to share
3. Generate the **magic link** for external auditors
4. **Explain**: Auditors access the platform through a separate portal using this link — no regular user account needed

> **Cut point**

---

### Scene 2.12: Organization Settings

**Navigate to**: Administration > Organization Settings

1. Review and update organization details
2. Show LLM provider selection (if multiple providers configured by Super Admin)
3. Update organization logo

**Navigate to**: Administration > Users

4. Show user management within the organization
5. Approve pending user registrations
6. Deactivate/reactivate users

> **Cut point** — End of Part 2.

---

## Part 3: Org User — Day-to-Day Compliance Work

**Role**: Org User (log out of Org Admin, log in as Org User)
**Purpose**: Perform daily compliance tasks — checklists, evidence, scans, and documentation.
**Estimated video duration**: 20–30 minutes

---

### Scene 3.1: Login & Dashboard

**Navigate to**: Login Page

1. Log in with Org User credentials
2. Point out the simplified sidebar:
   - No Administration section
   - No Framework Configuration
   - No Audit Engagements
   - All compliance features still available

> **Cut point**

---

### Scene 3.2: Objectives Checklist (Core Workflow)

**Navigate to**: Frameworks > Objectives

1. Select a **Framework** from the dropdown (e.g., ISO 27001)
2. Select **Scope Type**: Show the available options:
   - **Other** — Generic checklist with all policies (no entity selection needed)
   - **Product** — Asset-specific checklist (select which product)
   - **Organization** — Organization-scoped checklist (select which org entity)
3. Select scope type **"Other"** first:
   - Show the checklist loading with chapters and objectives
   - Each objective shows: compliance status, linked policies, evidence
4. **Update compliance status**:
   - Click the status dropdown on an objective
   - Select a status (e.g., "Compliant", "Non-Compliant", "Partially Compliant")
5. **Upload evidence**:
   - Click the evidence upload button on an objective
   - Select a file (PDF, image, document)
   - Show the uploaded evidence indicator
6. **View linked policies**:
   - Expand an objective to see its linked policies with their statuses

7. Now switch scope to **"Product"** and select an asset:
   - Show how the checklist adapts — policies are filtered to those relevant to the selected asset (via risk → control → policy chain)
   - Compliance status and evidence are independent per scope

**What to highlight**:
- Each scope has its own independent compliance tracking
- "Other" scope shows all linked policies (useful for general compliance)
- Asset/Product scope filters policies to only those relevant to that specific product
- Evidence uploads are per-objective, per-scope

> **Cut point**

---

### Scene 3.3: Complete an Assessment

**Navigate to**: Assessments

1. Open an existing assessment (created by admin) or create a new one
2. Answer questions manually:
   - Select answer options
   - Add comments/notes
   - Link to relevant policies
3. Use **"AI Suggest Answers"**:
   - Click the AI button in the toolbar
   - Watch suggestions generate one by one
   - Accept a suggestion by clicking the checkmark
   - Modify a suggestion before accepting
   - Skip/reject a suggestion
4. Save progress and submit when complete
5. **View the report**: Show the generated assessment report

**What to highlight**:
- Assessments are the formal evaluation against framework requirements
- AI suggestions provide a strong starting point but should always be reviewed
- Reports can be exported as PDF for stakeholders

> **Cut point**

---

### Scene 3.4: Risk Register & Incidents

**Navigate to**: Risks > Risk Register

1. Browse existing risks
2. View risk details and linked controls/policies
3. Update risk status or add notes

**Navigate to**: Risks > Incident Registration

4. Click **"Create Incident"**
5. Fill in incident details:
   - Title, description, severity
   - Link to relevant risks (optional)
6. Save the incident

**What to highlight**:
- Incidents feed into the risk management lifecycle
- Linking incidents to risks helps track recurring issues
- Incident history supports audit evidence

> **Cut point**

---

### Scene 3.5: Security Scanning

> **Note**: Security Tools are only visible if your organization's domain is in the scanner access allowlist.

**Navigate to**: Security Tools > Security Scanners

1. Select scanner type: **ZAP Proxy** (web vulnerability scanning)
2. Enter target URL
3. Click **"Start Scan"**
4. Show scan progress and results:
   - Vulnerabilities found with severity levels
   - CVE references
   - Remediation recommendations (AI-generated)

**Navigate to**: Security Tools > Code Analysis

5. Run a **Semgrep** scan on a code repository
6. Show code analysis results with findings

**Navigate to**: Security Tools > Dependency Check

7. Run an **OSV** scan for dependency vulnerabilities
8. Show dependency vulnerability results

**Navigate to**: Security Tools > SBOM Generator

9. Run **Syft** to generate a Software Bill of Materials
10. Show the generated SBOM

**Navigate to**: Security Tools > Scan Findings

11. Show the aggregated findings dashboard
12. Filter by scanner type, severity
13. Toggle remediation status on findings
14. Link a finding to a risk in the risk register

**What to highlight**:
- Multiple scanner types cover different attack surfaces
- AI-generated remediation suggestions help prioritize fixes
- Findings can be linked to risks for traceability
- Scan history is preserved for audit evidence

> **Cut point**

---

### Scene 3.6: Documents & Evidence

**Navigate to**: Documents > Policies

1. Browse policies and their statuses
2. Show how policies link to objectives and frameworks

**Navigate to**: Documents > Architecture

3. Upload architecture documents or diagrams

**Navigate to**: Documents > Evidence

4. Browse all uploaded evidence files
5. Upload new evidence
6. **Explain**: Evidence uploaded here is separate from objective-specific evidence — this is for general compliance documentation

#### CRA Technical File (if CRA Mode enabled)

Walk through each documentation page:

**Navigate to**: Documents > Technical File > Patch & Support Policy

5. Show the documentation form and fill in key sections

**Navigate to**: Documents > Technical File > Vulnerability Disclosure

6. Fill in vulnerability disclosure policy details

**Navigate to**: Documents > Technical File > SBOM Management

7. Document SBOM management practices

**Navigate to**: Documents > Technical File > Secure SDLC Evidence

8. Upload SDLC evidence and documentation

**Navigate to**: Documents > Technical File > Security Design

9. Document security design decisions

**Navigate to**: Documents > Technical File > Dependency Policy

10. Fill in dependency management policy

**What to highlight**:
- CRA Technical File pages are required for EU Cyber Resilience Act compliance
- Each page covers a specific CRA requirement
- These are only visible when CRA Mode is enabled by Super Admin

> **Cut point**

---

### Scene 3.7: CE Marking Checklist

**Navigate to**: Assets / Products > CE Marking Checklist

1. Select a product
2. Show the CE marking checklist items
3. Check off completed items
4. Upload supporting documents per item
5. **Explain**: CE Marking tracks the conformity assessment process for product certification

> **Cut point**

---

### Scene 3.8: Security Advisories

**Navigate to**: Risks > Security Advisories

1. Browse current security advisories
2. View advisory details:
   - Severity level
   - CVE references
   - Affected systems
   - Linked incidents
3. Create a new advisory (if applicable)

**What to highlight**:
- Advisories are fed by NVD/EUVD sync (configured by Super Admin)
- They provide early warning for relevant vulnerabilities
- Linking to incidents creates a response trail

> **Cut point**

---

### Scene 3.9: Compliance Chain Review

**Navigate to**: Compliance Chain > All Links

1. Browse the chain links table
2. Filter by type (Risk, Control, Policy, Objective)
3. Show the traceability from a risk through to an objective

**Navigate to**: Compliance Chain > Map

4. Navigate the visual map
5. Click on nodes to see connections
6. **Explain**: This gives a holistic view of how risks, controls, policies, and objectives connect

**Navigate to**: Compliance Chain > Gap Analysis

7. Review the compliance score
8. Identify remaining gaps
9. Export the gap analysis report as PDF

> **Cut point**

---

### Scene 3.10: AI Assistant & Profile

**Click**: AI Assistant icon (bottom of sidebar)

1. Open the chatbot drawer
2. Ask a compliance question (e.g., "What controls address data encryption?")
3. Show the AI response

**Click**: Profile icon (bottom of sidebar)

4. Open the profile modal
5. Update personal details
6. Change notification preferences
7. Upload profile picture

> **Cut point** — End of Part 3.

---

## Part 4: Public CRA Tools (No Login Required)

**Purpose**: Demonstrate the two public assessment tools available without authentication.
**Estimated video duration**: 5–10 minutes

---

### Scene 4.1: CRA Scope Assessment

**Navigate to**: `/cra-scope-assessment` (direct URL, no login)

1. Walk through the 3-step wizard:
   - **Step 1**: Product category selection
   - **Step 2**: Product characteristics and intended use
   - **Step 3**: Review and submit
2. View the generated scope report at `/cra-scope-report`
3. **Explain**: This helps manufacturers determine if their product falls under the EU Cyber Resilience Act

> **Cut point**

---

### Scene 4.2: CRA Readiness Assessment

**Navigate to**: `/cra-readiness-assessment` (direct URL, no login)

1. Walk through the multi-section evaluation:
   - Security requirements
   - Vulnerability handling
   - Documentation readiness
   - Supply chain security
2. View the readiness report at `/cra-readiness-report`
3. **Explain**: This evaluates how prepared an organization is for CRA compliance

> **Cut point** — End of training.

---

## Video Production Notes

### Recommended Recording Order

| Video | Role | Scenes | Est. Duration |
|-------|------|--------|---------------|
| Video 1 | Super Admin | Scenes 1.1–1.8 | 15–20 min |
| Video 2 | Org Admin | Scenes 2.1–2.12 | 25–35 min |
| Video 3 | Org User | Scenes 3.1–3.10 | 20–30 min |
| Video 4 | Public Tools | Scenes 4.1–4.2 | 5–10 min |

### Before Recording

- Start with a clean demo environment (fresh database with seed data)
- Ensure all services are running (frontend, backend, LLM, scanners)
- Have sample files ready for uploads (evidence docs, architecture diagrams, SBOM files)
- Have a sample target URL ready for security scanning demos
- Enable CRA Mode for at least one organization to show Technical File pages
- Add the demo organization's domain to the scanner access allowlist

### Screen Recording Tips

- Use 1920x1080 resolution for consistent framing
- Zoom into form fields when filling them out for readability
- Pause briefly (2–3 seconds) after each action to let viewers follow
- Use the cut points marked above as natural edit boundaries
- Consider adding chapter markers in the video at each Scene heading

### Demo Data Suggestions

| Entity | Example Value |
|--------|---------------|
| Organization | Clone Systems Inc. |
| Domain | clonesystems.com |
| Product | NextGen SIEM Pro v3.0.0 |
| Framework 1 | ISO/IEC 27001:2022 |
| Framework 2 | CRA (EU Cyber Resilience Act) |
| Scan Target | https://demo.clonesystems.com |
| Auditor Email | auditor@example.com |
| Incident | "Unauthorized API access attempt detected" |
| Risk | "Insufficient encryption of data at rest" |
