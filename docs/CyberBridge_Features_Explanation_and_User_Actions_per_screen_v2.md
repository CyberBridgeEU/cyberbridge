# CyberBridge - Features Explanation and User Actions per Screen
## Video Narration Script (Voiceover)

---

## Introduction

*[Opening Scene: CyberBridge Logo Animation]*

Welcome to CyberBridge — the comprehensive cybersecurity compliance assessment platform designed to simplify and streamline the way organizations manage their security posture. Built with modern microservices architecture, CyberBridge brings together compliance tracking, risk management, policy governance, and integrated security scanning — all in one powerful, intuitive platform.

Let's take a guided tour through every screen and discover how CyberBridge empowers security teams to achieve and maintain compliance with confidence.

---

## 1. Authentication Screens

### 1.1 Login Page

*[Scene: Login Page with branded background]*

The journey begins at CyberBridge's secure login portal. Users are greeted with a clean, professional interface featuring partner logos from CyberBridge, the European Union, and ECCC — a testament to the platform's trusted credentials.

Authentication is straightforward. Users simply enter their registered email and password, then click the Login button. The system provides immediate feedback with a loading indicator, ensuring users know their request is being processed.

For those moments when a password slips the mind, the "Forgot your password?" feature comes to the rescue. With just one click, users can trigger an email-based password reset flow — no need to contact IT support.

New to CyberBridge? The registration link at the bottom seamlessly guides prospective users to create their account.

---

### 1.2 Register Page

*[Scene: Registration Form]*

Creating a CyberBridge account is quick and secure. The registration page presents a streamlined form where new users enter their email address and create a strong password.

Real-time validation ensures everything is in order before submission — the system checks email formatting and confirms that passwords match. Once registration is complete, users receive a verification email to confirm their identity.

Should the verification email go astray, the resend option is readily available. After verification, users are directed back to the login page, ready to access the full power of CyberBridge.

---

## 2. Dashboard (Home Page)

*[Scene: Dashboard with animated metrics and charts]*

Upon logging in, users arrive at the CyberBridge Dashboard — the command center for compliance operations. This isn't just a homepage; it's a real-time intelligence hub that puts critical information at the user's fingertips.

At the top, six key metrics provide an instant snapshot: Total Assessments, Completed Assessments, Compliance Frameworks, Total Users, Total Policies, and Total Risks. These numbers update dynamically, giving leadership and compliance teams immediate visibility into organizational health.

Scrolling down, the Active Frameworks section showcases all compliance frameworks in use — from CRA and ISO 27001 to NIS2, NIST CSF, PCI DSS, and beyond. Each framework displays its official logo and description, making it easy to understand what standards the organization is tracking.

The Recent Assessment Activity section features an elegant carousel of donut charts, each representing an assessment's progress. Users can scroll horizontally through their assessments, instantly identifying which ones need attention and which are on track.

Framework Progress takes this further, showing aggregated completion rates across all assessments within each framework. It's the perfect bird's-eye view for executives who need to understand compliance posture at a glance.

The analytics section transforms raw data into actionable insights. Pie charts reveal the distribution of assessment types, policy statuses, and risk severities. Line charts track assessment trends over time, helping teams identify patterns and forecast workloads.

User analytics round out the dashboard, displaying role distributions and status breakdowns — essential information for administrators managing large teams.

At the bottom, a comprehensive table lists recent assessment activity with full details: assessment name, framework, assigned user, type, progress percentage, status, and organization. Pagination controls make it easy to navigate through extensive records.

---

## 3. Assessments

*[Scene: Assessments Page with question interface]*

The Assessments screen is where compliance work happens. CyberBridge has designed this interface to make complex compliance questionnaires manageable and even intuitive.

Users begin by selecting a compliance framework from the dropdown menu. The system immediately populates available assessment types based on that selection. If the framework requires scope definition — whether product-based or organization-based — those options appear dynamically.

Creating a new assessment takes just seconds. Users name their assessment, configure the scope if needed, and click Create. The system generates the complete question set based on the selected framework and assessment type.

For ongoing work, the Load Assessment dropdown lets users pick up exactly where they left off. Every answer, every uploaded file, every policy assignment is preserved and ready for continuation.

The question interface itself is thoughtfully designed. Each question displays clearly, with ample space for detailed responses. Users can type answers directly, upload evidence files through drag-and-drop functionality, and assign relevant policies from a searchable multi-select control.

Evidence management is built right in. Files attach seamlessly to answers, creating a comprehensive audit trail. Users can preview, download, or remove files as needed.

For organizations with existing data, the CSV Import feature accelerates the process dramatically. Upload a properly formatted CSV, and answers populate automatically across the entire assessment. Conversely, CSV Export allows users to extract their work for offline review or backup purposes.

When it's time to share results, the PDF Export function generates professional reports ready for stakeholders, auditors, or regulatory bodies. The ZIP Download option packages all evidence files for convenient archival.

Progress tracking keeps everyone informed. A visual progress bar and percentage display show exactly how much work remains. Status indicators communicate whether an assessment is in progress or complete.

Deleting an assessment, when necessary, requires explicit confirmation — protecting against accidental data loss while keeping the interface uncluttered.

---

## 4. Assets (Products & Services)

*[Scene: Asset Registration Form and Table]*

Modern compliance frameworks increasingly require organizations to track their assets and understand the security implications of each. CyberBridge's Asset Registration screen provides a comprehensive asset catalog solution.

The registration form captures all essential asset information: name, version, justification for registration, licensing details, and a full description. For software assets, the SBOM (Software Bill of Materials) field allows organizations to document their dependency chains — critical information for supply chain security.

Dropdown selectors streamline data entry for standardized fields. Users select the asset status, economic operator (the responsible organization or vendor), asset type (software, hardware, service), and criticality level. These categorizations enable powerful filtering and reporting capabilities throughout the platform.

Once saved, assets appear in the main table — a sortable, searchable, paginated view of the entire asset catalog. Clicking any row loads that asset's details back into the form for editing. Deletion is available with confirmation to prevent accidents.

The PDF Export feature generates a complete asset registry report — perfect for compliance documentation or internal reviews.

Assets registered here become available as scope entities in the Assessments screen, creating a seamless connection between asset inventory and compliance tracking.

---

## 5. Policies Registration

*[Scene: Policy Form with Framework Mapping Interface]*

Policies are the backbone of any compliance program, and CyberBridge treats them with the importance they deserve. The Policies Registration screen enables organizations to create, manage, and — most importantly — map their policies to specific compliance framework objectives.

Creating a policy starts with the basics: a clear title and the policy body itself. The rich text area accommodates detailed policy content, from brief procedural statements to comprehensive governance documents.

Status tracking keeps policies organized through their lifecycle. Users select from Active, Draft, Approved, or Archived statuses, making it easy to understand which policies are currently in force.

The real power emerges in the framework mapping section. Users select one or more frameworks to associate with the policy. The interface then cascades intelligently: selecting a framework reveals its chapters, selecting a chapter shows subchapters, and finally, the specific objectives become available for mapping.

This hierarchical mapping creates explicit links between organizational policies and compliance requirements. When auditors ask "How do you address Objective 4.2.3?", the answer is just a search away.

Policy documents can be uploaded and attached directly, keeping the source files alongside their metadata. Preview functionality lets users verify they've attached the correct document.

The policies table displays all registered policies with their titles, statuses, associated frameworks, chapters, and mapped objectives. Super administrators receive helpful warnings when policies cross organizational boundaries — an important consideration in multi-tenant deployments.

PDF Export produces a comprehensive policy register, documenting the organization's policy landscape for internal governance or external audit purposes.

---

## 6. Risk Registration

*[Scene: Risk Form with Severity Indicators]*

Risk management is fundamental to cybersecurity, and CyberBridge provides a dedicated Risk Registration screen to capture, assess, and track organizational risks.

The risk form guides users through a structured assessment process. Each risk is categorized by product type and risk category — with autocomplete suggestions speeding data entry while maintaining consistency.

The description field captures the risk in detail, while the potential impact field documents what could happen if the risk materializes. The controls field records existing mitigations, creating a complete picture of the risk landscape.

Assessment dropdowns standardize risk evaluation. Users rate the likelihood (Low, Medium, High) and severity (Critical, High, Medium, Low) of each risk. After documenting controls, the residual risk field captures the remaining exposure — the risk that persists even after mitigations.

Status tracking moves risks through their lifecycle: Open risks require attention, Mitigated risks have controls in place, Accepted risks are acknowledged and tolerated, and Closed risks are resolved.

Scope assignment links risks to specific products or the organization as a whole, enabling filtered views and targeted risk reports.

The risk table presents all registered risks with color-coded severity indicators — making it immediately obvious which risks demand priority attention. Sorting and filtering capabilities help risk managers focus on what matters most.

PDF Export generates risk register reports suitable for board presentations, audit evidence, or regulatory submissions.

Risk data flows directly to the Dashboard, where analytics charts visualize the organization's risk profile alongside other compliance metrics.

---

## 7. Framework Management

*[Scene: Framework Management Interface with Questions and Objectives]*

For administrators, the Framework Management screen unlocks CyberBridge's full customization potential. This is where compliance frameworks are created, configured, and populated with questions and objectives.

Creating a new framework is straightforward. Administrators enter a name and description, then configure scope settings — determining whether assessments against this framework will be scoped to products, organizations, or both.

For organizations adopting standard frameworks, the Template Seeding feature is transformative. Select a framework and a template (ISO 27001, NIST CSF, and others are available), click Seed, and the framework populates with industry-standard questions and objectives. Hours of manual setup compressed into seconds.

The Questions Management section enables fine-grained control. Administrators add questions individually, specifying the question text, target frameworks, assessment type, and whether the question is mandatory. The CSV Upload feature enables bulk import — ideal for migrating from existing compliance tools or loading custom question sets.

Questions display in a searchable, filterable table. Clicking a question loads it for editing; changes save back seamlessly. Unnecessary questions can be removed without affecting historical assessment data.

Chapter and Objective Management brings structure to frameworks. Administrators create chapters as organizational containers, then add objectives within those chapters. Each objective includes a title, description, utilities information, subchapter assignment, and requirement description.

This hierarchical structure — Framework > Chapter > Subchapter > Objective — mirrors how real compliance frameworks are organized, making CyberBridge intuitive for compliance professionals who already understand their regulatory landscape.

---

## 8. Objectives Checklist

*[Scene: Objectives Checklist with AI Suggestions Panel]*

The Objectives Checklist screen transforms compliance tracking from a documentation exercise into an actionable workflow. Here, users systematically work through framework objectives, recording compliance status and receiving AI-powered improvement suggestions.

After selecting a framework, the screen populates with all objectives organized hierarchically by chapter and subchapter. Each row displays the objective's title, requirement description, and utilities — everything needed to understand what compliance requires.

The compliance status dropdown is where assessment happens. For each objective, users select the current state: Compliant, Partially Compliant, Non-Compliant, or Not Applicable. These selections save automatically, and the system tracks changes over time.

But CyberBridge goes beyond simple status tracking. The AI-powered suggestions feature leverages integrated LLM technology to analyze objectives and generate improvement recommendations. Click "Generate AI Suggestions," and the system processes each objective, returning targeted advice with confidence scores.

Users review each suggestion, applying those that add value and dismissing those that don't fit their context. It's human expertise augmented by artificial intelligence — the best of both worlds.

A page-leave warning protects users from accidentally navigating away during AI processing, ensuring no work is lost.

PDF Export produces a complete checklist report showing all objectives and their current compliance statuses — ready for auditors, executives, or regulatory submissions.

---

## 9. Update Password

*[Scene: Password Update Form]*

Security starts at home, and CyberBridge makes it easy for users to maintain strong authentication credentials. The Update Password screen provides a simple, focused interface for changing account passwords.

The screen displays the current user's email for confirmation, then presents a single password field for entering the new credential. Clear guidance reminds users to choose strong, unique passwords — mixing letters, numbers, and symbols while avoiding personal information.

With one click, the password updates across the system. Success and error notifications provide immediate feedback, and users can continue their work knowing their account is secured with fresh credentials.

---

## 10. Admin Area

*[Scene: Admin Area Navigation]*

CyberBridge's Admin Area provides powerful tools for platform administrators. Access is role-based — super administrators see everything, while organization administrators see tools relevant to their scope.

---

### 10.1 Settings

*[Scene: Settings Page with Multiple Configuration Sections]*

The Settings screen is the super administrator's control room. From here, system-wide configurations shape how CyberBridge operates across all organizations.

Framework Cloning enables rapid deployment of compliance frameworks to new organizations. Select the frameworks to clone, choose the target organization, customize the name if desired, and execute. The complete framework — questions, objectives, chapters, and all — replicates instantly.

Scanner Access Control determines which organizations can use CyberBridge's integrated security scanning tools. Toggle scanners on or off globally, then specify which organization domains have access. This granular control ensures scanning capabilities reach those who need them while maintaining appropriate boundaries.

SMTP Configuration connects CyberBridge to organizational email infrastructure. The multi-record SMTP configuration supports multiple mail server entries, allowing organizations to configure different SMTP providers for different purposes. Enter server details, authentication credentials, and sender address, then verify the setup with a test email. Once configured, CyberBridge can send password reset emails, verification messages, and notifications.

SSO Configuration enables Single Sign-On through Google OAuth2 and Microsoft OAuth2 providers. Administrators configure client IDs, client secrets, and callback URLs for each provider, allowing users to authenticate seamlessly with their existing corporate identities.

Framework Template Permissions control which compliance framework templates each organization can access. Some organizations might only need ISO 27001; others require the full library. Permissions ensure users see relevant options without overwhelming choices.

The Domain Blacklist management prevents registration from unwanted email domains — a valuable security control for organizations concerned about unauthorized access attempts.

LLM Configuration connects CyberBridge to its AI backbone with multi-provider support. Administrators can configure connections to llama.cpp (self-hosted), OpenAI, Anthropic, Google, X AI, or QLON — selecting the provider that best fits their organization's requirements for privacy, performance, and cost. Endpoint URLs, API keys, model selection, and payload templates are all configurable per provider. This powers the AI suggestion features throughout the platform, from objective recommendations to correlation insights.

CRA Mode Toggle allows administrators to enable or disable Cyber Resilience Act (CRA) specific features on a per-organization basis, adapting the platform to each organization's regulatory requirements.

Super Admin Focused Mode provides super administrators with a streamlined interface that reduces visual clutter by focusing only on the most critical administrative functions, improving efficiency for power users managing multiple organizations.

---

### 10.2 Correlations

*[Scene: Correlations Interface with Two-Framework View]*

Compliance frameworks often overlap. A control that satisfies ISO 27001 might also address NIST CSF requirements. The Correlations screen helps organizations identify and document these connections, reducing duplicate effort and creating a unified compliance view.

The interface presents two framework selection panels side by side. Users select Framework A, its assessment type, and a specific question. Then they select Framework B, its assessment type, and another question. If these questions address related requirements, clicking Correlate creates an explicit link between them.

But manual correlation is just the beginning. The AI-powered suggestion engine analyzes questions across frameworks, identifying potential correlations that humans might miss. With configurable confidence thresholds, users control how aggressive the AI recommendations should be.

Generated suggestions appear with confidence scores. Users review each one, applying those that make sense and dismissing false positives. Over time, the correlation database grows into a valuable knowledge asset.

The All Correlations view presents every documented relationship in a searchable table. Bulk operations enable cleanup when needed. The Correlation Audit feature validates data integrity, with auto-fix capabilities to resolve any issues discovered.

LLM Optimization Settings let administrators tune the AI engine — adjusting question limits, timeouts, confidence thresholds, and maximum correlations to balance thoroughness against performance.

---

### 10.3 Organizations (User Management)

*[Scene: Organization and User Management Interface]*

Multi-tenant by design, CyberBridge enables a single platform instance to serve multiple organizations securely. The Organizations screen is where this multi-tenancy is managed.

Super administrators can create new organizations, specifying names and domains. Each organization becomes an isolated compliance environment, with its own users, frameworks, assessments, and data.

Organization branding is supported through logo management. Upload a custom logo, and it appears in the header bar for all users within that organization — reinforcing brand identity throughout the compliance workflow.

User management covers the complete lifecycle. Administrators create users by specifying email, initial password, role assignment (super_admin, org_admin, or org_user), and organization membership. Existing users can be edited — changing roles or organization assignments as needs evolve. Users no longer requiring access can be deleted cleanly.

The user table provides a comprehensive view of all accounts: email, role, organization, and status at a glance.

History Cleanup Configuration addresses data retention requirements. Organizations can enable automatic cleanup of historical records, specifying how many days to retain data and how frequently cleanup should run. Manual cleanup triggers immediate processing when needed.

---

### 10.4 Approvals

*[Scene: Approvals Dashboard with User Status Controls]*

User lifecycle management continues on the Approvals screen, where administrators review and process user registration requests.

The user table displays all accounts with comprehensive filtering options. Filter by status (Pending, Approved, Rejected, Active, Inactive), by role, or by organization. Search by email to find specific users quickly.

Status changes happen inline. Select a user, choose the new status from the dropdown, and the change applies immediately. Approve a pending user, and they gain access. Reject suspicious registrations, and access is denied. Deactivate users who have left the organization. Reactivate when they return.

Real-time monitoring shows who's currently online. The Online Users list refreshes every twenty seconds, giving administrators visibility into platform activity. Session information reveals last activity timestamps and session durations.

Analytics transform user data into actionable insights. Charts display visit frequency by user, total visit counts, and PDF download patterns by report type. Date range filters focus analytics on specific periods. Export functionality extracts data for further analysis in external tools.

---

### 10.5 History

*[Scene: History Table with Filters]*

Compliance requires accountability, and accountability requires audit trails. The History screen provides complete visibility into platform activity — who did what, when, and to which entities.

Every significant action generates a history entry: creates, updates, deletes, and exports across all entity types. The history table displays user, action type, entity type, timestamp, and detailed information for each event.

Powerful filtering narrows the view. Filter by entity type to see only assessment-related changes. Filter by action to focus on deletions. Set date ranges to examine specific time periods. Search by user email or details to investigate particular activities.

Administrative controls enable history management. Individual entries can be deleted when appropriate. The Clear All function removes all history for an organization — useful during testing or when retention policies require data removal.

Organization selection lets super administrators examine history across the entire platform or focus on specific tenants.

---

## 11. Scanners

*[Scene: Scanner Menu with Four Options]*

CyberBridge integrates four powerful security scanning tools directly into the platform. Organizations with scanner access enabled can perform vulnerability assessments, network reconnaissance, code analysis, and dependency scanning — all without leaving the compliance workflow.

**Note:** In the user interface, scanner tool names are abstracted from end users. Routes display as "Security Scanners" (ZAP), "Code Analysis" (Semgrep), "Dependency Check" (OSV), and "SBOM Generator" (Syft) — keeping the experience approachable for compliance professionals who may not be familiar with the underlying open-source tools.

---

### 11.1 Web App Scanner (ZAP)

*[Scene: ZAP Scanner Interface with Results]*

The Web App Scanner — presented to users as "Security Scanners" — brings OWASP ZAP's industry-leading web application security testing directly into CyberBridge. Security teams can assess web applications without managing separate scanning infrastructure.

Configuration is simple: enter the target URL and select the scan type. Spider scans discover content and map the application. Active scans probe for vulnerabilities. Full scans combine both approaches. API scans focus specifically on API security.

Once started, the scan runs with real-time progress updates. A visual progress bar tracks completion, while alert counts update as findings emerge. Should circumstances require, the Emergency Stop button halts scanning immediately.

Results appear in a comprehensive alerts table. Each finding shows the alert type, risk level (color-coded for quick assessment), confidence rating, and occurrence count. Expanding a finding reveals evidence, detailed descriptions, and suggested solutions.

Summary statistics provide an at-a-glance risk profile: total alerts alongside high, medium, and low severity counts.

PDF Export generates professional security assessment reports ready for stakeholders. The History feature preserves past scans for comparison and trend analysis.

With optional LLM analysis, CyberBridge's AI engine can process scan results, providing contextual insights that help security teams prioritize remediation efforts.

---

### 11.2 Network Scanner (Nmap)

*[Scene: Nmap Scanner with Network Results]*

Network reconnaissance is foundational to security assessment, and CyberBridge's integrated Nmap scanner makes it accessible to compliance teams.

The scanner accepts hostnames, IP addresses, or IP ranges as targets. Users specify ports when needed and select from a comprehensive menu of scan types: Basic scans for quick discovery, Port scans for specific services, All Ports for comprehensive coverage, Aggressive scans for maximum information, OS detection, Network discovery, Stealth scans for discretion, and Fast scans when time is short.

Results display in both raw terminal format — familiar to experienced network administrators — and structured table views that make findings accessible to broader audiences. Host information, port statuses (open, closed, filtered), and detected services all surface clearly.

The LLM analysis toggle engages AI-powered interpretation. Enable it, and CyberBridge provides contextual analysis of network findings, helping teams understand security implications without requiring deep technical expertise.

PDF Export creates network assessment reports documenting discovered hosts, open ports, and running services. The History feature enables comparison across scans, revealing how network posture changes over time.

---

### 11.3 Code Analysis (Semgrep)

*[Scene: Semgrep Scanner with Code Findings]*

Secure code is compliant code, and CyberBridge's integrated Semgrep scanner brings static analysis capabilities to the compliance workflow.

Users upload code archives — ZIP files, TAR archives, or compressed directories — through an intuitive drag-and-drop interface. Configuration options allow automatic rule selection or custom configurations for specific needs.

The scanner processes uploaded code, applying Semgrep's extensive rule library to identify security issues, code quality problems, and potential vulnerabilities.

Results present in a detailed findings table. Each issue displays the triggering rule ID, severity level, affected file, line number, and a clear description of the problem. Expanding a finding reveals the actual code snippet alongside remediation guidance — everything developers need to fix the issue.

Summary statistics break down findings by severity and category, helping teams prioritize their remediation backlog.

LLM analysis adds another dimension, with AI-generated insights contextualizing findings within the broader application security landscape.

PDF Export produces code security reports suitable for development teams, security reviews, or compliance documentation. Scan history enables trending, showing whether code quality improves or degrades over time.

---

### 11.4 Dependency Analysis (OSV)

*[Scene: OSV Scanner with Vulnerability List]*

Supply chain security has become a critical compliance concern. CyberBridge's integrated OSV scanner identifies vulnerable dependencies before they become breaches.

The scanner accepts standard lock files from virtually any package ecosystem: package-lock.json for npm, requirements.txt for Python, go.mod for Go, Gemfile.lock for Ruby, Cargo.lock for Rust, pom.xml for Maven, and many more.

Upload a lock file, start the scan, and CyberBridge queries the Open Source Vulnerability database to identify known vulnerabilities in project dependencies.

Results display comprehensively: package name, installed version, vulnerability identifier (CVE or OSV ID), severity, fix status, affected version ranges, remediation recommendations, and reference links to advisories and detailed information.

Summary statistics quantify the exposure: total vulnerabilities, breakdown by severity, and count of affected packages.

AI analysis helps teams understand which vulnerabilities pose real risk in their specific context versus theoretical concerns that can be safely deprioritized.

PDF Export creates dependency security reports — essential documentation for audits, procurement decisions, and executive briefings on supply chain risk.

---

## 12. Controls Management

### Scene: Controls Management
**[Show Controls Registration Page]**

Security controls are the mechanisms that protect your organization. CyberBridge's Controls module lets you register, track, and manage every security control in your environment.

**Feature Highlights:**
- Register controls with implementation status tracking
- Organize controls into logical control sets
- Link controls directly to the risks they mitigate
- Map controls to policies that define them
- Connect controls to framework objectives
- Browse and import from the Controls Library of pre-built templates
- Track control review status for ongoing assurance

Controls complete the compliance traceability chain — from risks, through controls and policies, to framework objectives.

---

## 13. Incident Management

### Scene: Incident Management
**[Show Incident Registration Page]**

When security events occur, CyberBridge's Incident Management module ensures structured tracking and response.

**Feature Highlights:**
- Register and categorize security incidents
- Link incidents to affected assets
- Connect incidents to related risks
- Associate incidents with relevant frameworks
- Track incident lifecycle and resolution status

---

## 14. Compliance Chain

### Scene: Compliance Chain
**[Show Compliance Chain Map Page]**

The Compliance Chain is where all compliance entities come together in a visual, interactive map.

**Feature Highlights:**
- **All Links View:** See every relationship between assets, risks, controls, policies, objectives, and incidents in a comprehensive table
- **Visual Map:** Interactive graph visualization showing how all compliance entities connect
- Navigate connections by clicking on any entity
- Identify gaps where entities lack proper linkage
- Ensure complete traceability across your entire compliance program

This is what modern compliance visibility looks like — every connection mapped, every gap visible.

---

## 15. Audit Engagements

### Scene: Audit Engagements
**[Show Audit Engagements Page]**

External audits are a reality of compliance. CyberBridge's dedicated audit portal streamlines the entire process.

**Feature Highlights:**
- Create time-bound audit engagements
- Invite external auditors via secure magic link authentication
- Separate auditor workspace with role-based access (Guest Auditor, Auditor Lead)
- Structured audit comments and findings tracking
- Evidence request and review workflow
- Formal sign-off process with audit trails
- IP allowlisting for additional security
- Complete audit activity logging

No more shared drives and email chains — auditors get a professional, secure workspace.

---

## 16. SBOM Generation (Syft)

### Scene: SBOM Generation (Syft)
**[Show Syft SBOM Generator Page]**

For EU Cyber Resilience Act compliance, maintaining a Software Bill of Materials is essential. CyberBridge integrates Syft for automated SBOM generation.

**Feature Highlights:**
- Generate comprehensive package and dependency inventories
- Support for multiple package ecosystems
- SBOM report generation for compliance documentation
- Scan history tracking
- Direct integration with asset compliance tracking

---

## 17. Evidence Library & Architecture Diagrams

### Scene: Evidence Library & Architecture Diagrams
**[Show Evidence Page and Architecture Page]**

Compliance requires comprehensive documentation. CyberBridge provides centralized repositories for all your evidence and architectural documentation.

**Feature Highlights:**
- **Evidence Library:** Upload, organize, and link evidence items to frameworks and controls
- **Architecture Diagrams:** Maintain architecture documentation linked to frameworks and risks
- Evidence integrity verification ensures documents haven't been tampered with
- Centralized access for auditors and compliance teams

---

## 22. Threat Intelligence - Overview (/cti/overview)

*[Scene: CTI Overview Dashboard with KPI cards and charts]*

The Threat Intelligence Overview provides a centralized command center for all cyber threat intelligence gathered across the platform. This screen aggregates data from all connected sources into a unified, actionable view.

**Feature Highlights:**
- **KPI Cards:** At-a-glance metrics showing total indicators, sightings, malware families, and attack patterns across all sources
- **Threat Timeline Chart:** Visualize threat activity trends over configurable time ranges (7-day, 14-day, and 30-day views)
- **Top MITRE ATT&CK Techniques:** Ranked display of the most frequently observed ATT&CK techniques, enabling teams to prioritize defenses
- **Source Breakdown:** Distribution of intelligence by source (Nmap, ZAP, Semgrep, OSV, and external sensors), helping teams understand their threat landscape

---

## 23. Threat Intelligence - MITRE ATT&CK (/cti/threat-intel)

*[Scene: MITRE ATT&CK mapping interface with pattern tables]*

The MITRE ATT&CK screen provides a structured view of threat intelligence mapped to the ATT&CK framework, enabling teams to understand adversary behavior and improve detection coverage.

**Feature Highlights:**
- **Top Attack Patterns:** Ranked list of the most frequently observed ATT&CK patterns across all data sources
- **Patterns by Source:** Breakdown of attack patterns per scanner or connector, showing which tools detect which techniques
- **Recent Indicators Table:** Live feed of the latest threat indicators with type, source, confidence score, and timestamp
- **Recent Attack Patterns Table:** Chronological list of newly identified attack patterns with severity and associated campaigns

---

## 24. Threat Intelligence - Network / Web / Code / Dependencies

### Network (/cti/network)
### Web Vulnerabilities (/cti/web-vulns)
### Code Analysis (/cti/code-analysis)
### Dependencies (/cti/dependencies)

*[Scene: CTI-normalized scanner views with STIX 2.1 data]*

These four screens present CTI-normalized views of scanner data, each focused on a specific domain. Data from Nmap, ZAP, Semgrep, and OSV is transformed into STIX 2.1 format and enriched with threat intelligence context.

**Feature Highlights:**
- **CTI-Normalized View:** Scanner results are converted to STIX 2.1 formatted findings, providing a standardized representation across all tools
- **Cross-Correlation:** Findings are automatically correlated with intelligence from other sources, surfacing connections that individual scanners cannot detect alone
- **Enriched Context:** Each finding includes associated MITRE ATT&CK techniques, confidence scores, and related indicators from the CTI knowledge base

---

## 25. Dark Web Intelligence - Dashboard (/dark-web/dashboard)

*[Scene: Dark Web Dashboard with queue monitoring]*

The Dark Web Intelligence Dashboard provides operational oversight of dark web scanning activities. It serves as the primary monitoring interface for tracking scan operations and system health.

**Feature Highlights:**
- **Queue Monitoring:** Real-time display of queue length, currently processing scans, active workers, and total scans executed
- **Recent Scan Activity:** Chronological feed of the latest scan operations with status indicators (queued, processing, completed, failed)
- **Quick Actions:** One-click access to create new scans, view reports, or adjust scanner settings

---

## 26. Dark Web Intelligence - Scans (/dark-web/scans)

*[Scene: Scan management interface with keyword entry]*

The Scans screen is where operators create and manage dark web intelligence gathering operations. Each scan targets specific keywords across the Tor network.

**Feature Highlights:**
- **Create New Scans:** Enter a keyword to initiate a dark web scan across configured search engines
- **Scan Status Tracking:** Each scan displays its current status — queued, processing, completed, or failed — with progress updates
- **Filter and Search:** Locate specific scans by keyword, status, or date range for efficient management of large scan volumes

---

## 27. Dark Web Intelligence - Scan Details (/dark-web/scan/:id)

*[Scene: Detailed scan results with categorized findings]*

The Scan Details screen presents the full results of a completed dark web scan, organized into actionable categories for rapid triage.

**Feature Highlights:**
- **Breach Status:** Clear, prominent indicator showing whether the scanned keyword was found in breach data (Breached or Secure)
- **Categorized Findings:** Results are organized into five categories — passwords, databases, credentials, emails, and leaks — enabling targeted response actions
- **Sites Found:** List of dark web sites where matches were detected, with discovery timestamps
- **Keywords Matched:** Specific keyword matches within each finding, with surrounding context for rapid assessment

---

## 28. Dark Web Intelligence - Reports (/dark-web/reports)

*[Scene: Reports listing with download options]*

The Reports screen provides a consolidated view of all completed dark web scan reports, enabling teams to review historical findings and share intelligence.

**Feature Highlights:**
- **Download Reports:** Export scan results as PDF or JSON for offline analysis, archival, or sharing with stakeholders
- **Scan Summaries:** Each report entry displays the scan keyword, execution date, breach status, and finding counts for quick triage

---

## 29. Dark Web Intelligence - Settings (/dark-web/settings)

*[Scene: Admin settings panel for dark web scanner]*

The Settings screen (admin only) provides configuration controls for the dark web scanning infrastructure. Access is restricted to administrators to prevent unauthorized modifications.

**Feature Highlights:**
- **Max Workers Configuration:** Adjust the number of concurrent scan workers (1-10) to balance throughput against available system resources
- **Search Engine Management:** Enable or disable individual dark web search engines from the available pool of 23 engines, tailoring scan coverage to organizational needs

---

## Closing

*[Scene: CyberBridge Dashboard with activity, fading to logo]*

From authentication to assessment, from policy management to security scanning, CyberBridge provides a unified platform for comprehensive cybersecurity compliance. Every feature has been designed with real compliance workflows in mind — reducing friction, improving visibility, and accelerating the path to security maturity.

Whether an organization is pursuing ISO 27001 certification, demonstrating NIS2 compliance, or managing a multi-framework compliance program, CyberBridge provides the tools, the structure, and the intelligence to succeed.

Welcome to CyberBridge. Welcome to compliance, simplified.

*[End Scene: CyberBridge Logo with tagline]*

---

## Document Information

**Document Type:** Video Narration Script (Voiceover)
**Version:** 2.0
**Target Duration:** Approximately 35-40 minutes (full product tour)
**Tone:** Professional, informative, marketing-oriented
**Audience:** Prospective customers, new users, stakeholders
**Application:** CyberBridge Cybersecurity Compliance Assessment Platform

---

## Scene Notes for Video Production

| Section | Suggested Visuals | Duration |
|---------|-------------------|----------|
| Introduction | Logo animation, platform overview shots | 30-45 sec |
| Login Page | Screen recording of login flow | 45-60 sec |
| Register Page | Screen recording of registration | 45-60 sec |
| Dashboard | Animated dashboard with data populating | 2-3 min |
| Assessments | Question answering workflow demo | 3-4 min |
| Assets (Products & Services) | Form completion and table view | 1.5-2 min |
| Policies Registration | Policy creation with mapping demo | 2-2.5 min |
| Risk Registration | Risk assessment workflow | 1.5-2 min |
| Framework Management | Admin creating framework and questions | 2-2.5 min |
| Objectives Checklist | Status updates and AI suggestions | 2-2.5 min |
| Update Password | Quick screen demo | 30 sec |
| Settings | Configuration overview | 2-2.5 min |
| Correlations | AI correlation demonstration | 1.5-2 min |
| Organizations | User and org management | 1.5-2 min |
| Approvals | User approval workflow | 1-1.5 min |
| History | Audit trail exploration | 1 min |
| ZAP Scanner | Live scan demonstration | 1.5-2 min |
| Nmap Scanner | Network scan demo | 1.5-2 min |
| Semgrep Scanner | Code analysis demo | 1.5-2 min |
| OSV Scanner | Dependency scan demo | 1.5-2 min |
| Controls Management | Control registration and linking demo | 1.5-2 min |
| Incident Management | Incident registration and linking demo | 1-1.5 min |
| Compliance Chain | All links view and visual map demo | 1.5-2 min |
| Audit Engagements | Audit creation and auditor workflow | 2-2.5 min |
| SBOM Generation (Syft) | SBOM generation demo | 1-1.5 min |
| Evidence Library & Architecture | Evidence upload and architecture docs | 1-1.5 min |
| Threat Intelligence - Overview | CTI dashboard with KPI cards and charts | 2-2.5 min |
| Threat Intelligence - MITRE ATT&CK | ATT&CK mapping and indicator tables | 1.5-2 min |
| Threat Intelligence - Scanner Views | CTI-normalized Network/Web/Code/Deps | 2-3 min |
| Dark Web Intelligence - Dashboard | Queue monitoring and scan activity | 1-1.5 min |
| Dark Web Intelligence - Scans | Scan creation and status tracking | 1.5-2 min |
| Dark Web Intelligence - Scan Details | Categorized findings and breach status | 1.5-2 min |
| Dark Web Intelligence - Reports | Report download and summaries | 1 min |
| Dark Web Intelligence - Settings | Admin configuration demo | 1 min |
| Closing | Dashboard activity, logo fade | 30-45 sec |
