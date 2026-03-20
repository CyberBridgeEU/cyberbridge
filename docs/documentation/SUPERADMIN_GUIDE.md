# Super Administrator Guide

Welcome to the CyberBridge Super Administrator Guide. This documentation covers system-wide administrative features available only to super administrators.

## Overview

As a Super Administrator, you have complete access to the CyberBridge platform including:

- All standard user features
- All organization admin features
- Cross-organization management
- System-wide configuration
- Framework cloning between organizations
- Multi-provider LLM configuration
- SSO and SMTP configuration
- CRA Mode and Focused Mode toggles

## Super Admin Dashboard

The super admin dashboard provides system-wide visibility:

- **Total Organizations**: Count of all organizations in the system
- **Total Users**: Count of all users across all organizations
- **Total Frameworks**: All frameworks across all organizations
- **System Health**: Status of all services and components
- **Quick Actions**: Shortcuts including the User Guide wizard

## Organization Management

### Creating Organizations

1. Navigate to **Administration > Organizations**
2. Click "Create Organisation"
3. Enter organization details:
   - **Name**: Organization name
   - **Description**: Organization description
   - **Domain**: Unique domain identifier
4. Click "Create Organisation"

### Managing Organizations

- View all organizations in the system
- Edit organization details
- View organization statistics
- Upload custom logos for organization branding (appears in header bar)
- Configure organization-specific settings

### Organization Domains

Organization domains control access to certain features:
- Security scanners are restricted by domain
- Configure allowed domains in System Settings

### History Cleanup Configuration

1. Select an organization
2. Enable automatic cleanup of historical records
3. Set retention period (days) and cleanup frequency
4. Trigger manual cleanup when needed

## Cross-Organization User Management

### Viewing All Users

1. Navigate to **Administration > Users**
2. View all users across all organizations
3. Filter by organization, role, or status

### Creating Users in Any Organization

1. Click "Add User"
2. Select the target organization
3. Enter user details
4. Assign appropriate role:
   - **Super Admin**: System-wide access
   - **Org Admin**: Organization-level admin
   - **Org User**: Standard user access
5. Click "Create User"

### Managing Super Admins

Only super admins can:
- Create other super admin accounts
- Modify super admin roles
- Deactivate super admin accounts

### User Approvals

1. Navigate to **Administration > Users**
2. Filter by status: Pending, Approved, Rejected, Active, Inactive
3. Approve or reject registration requests
4. View online users with session information (refreshes every 20 seconds)
5. Review user analytics: visit frequency, total visits, PDF download patterns

## Framework Management

### Framework Cloning

Clone frameworks between organizations:

1. Navigate to **Administration > System Settings**
2. Select "Clone Frameworks"
3. Choose source framework(s) from the list
4. Select target organization
5. Optionally provide a custom name
6. Click "Clone Selected Frameworks"

**What Gets Cloned:**
- Complete framework structure
- All chapters and objectives
- Associated questions
- Framework metadata

**What Doesn't Get Cloned:**
- Assessment data
- User answers and evidence
- Policies (organization-specific)
- Risks (organization-specific)

### Framework Template Permissions

Control which templates each organization can access:

1. Navigate to **Administration > System Settings**
2. Select "Framework Template Permissions"
3. Configure which compliance framework templates each organization can seed
4. Save changes

### Framework Configuration

As a super admin, you have full access to all framework configuration:
- **Manage Frameworks**: Navigate to Frameworks > Configuration > Manage Frameworks
- **Chapters & Objectives**: Navigate to Frameworks > Configuration > Chapters & Objectives
- **Framework Questions**: Navigate to Frameworks > Configuration > Framework Questions
- **Framework Updates**: Navigate to Frameworks > Configuration > Framework Updates

### Compliance Advisor (AI)

1. Navigate to **Frameworks > Compliance Advisor**
2. Enter a website URL to analyze any organization's online presence
3. The AI scrapes the website and evaluates which compliance frameworks are relevant
4. Review the company summary and framework recommendations with relevance levels (High, Medium, Low)
5. Seed recommended frameworks directly from the results page
6. View analysis history across all analyses performed in your organization
7. Reload previous results or delete history records
8. Use system-wide to evaluate framework needs for any organization being onboarded

## System Settings

### Scanner Access Control

Control which organizations can use security scanners:

1. Navigate to **Administration > System Settings**
2. Select "Scanner Configuration"
3. Toggle scanners on or off globally
4. Add or remove allowed organization domains
5. Save changes

### LLM Configuration (Multi-Provider)

Configure the AI backbone for the platform with support for multiple providers:

1. Navigate to **Administration > System Settings**
2. Select "LLM Configuration"
3. Choose your provider:
   - **llama.cpp** (self-hosted): Configure endpoint URL and model
   - **OpenAI**: Configure API key and model selection
   - **Anthropic**: Configure API key and model selection
   - **Google**: Configure API key and model selection
   - **X AI**: Configure API key and model selection
   - **QLON**: Configure endpoint and credentials
4. Set endpoint URL, API key, model name, and payload template per provider
5. Test the connection
6. Save configuration

This powers all AI features: Compliance Advisor, question correlations, scan analysis, objective recommendations, and policy alignment suggestions.

### SSO Configuration

Enable Single Sign-On through external identity providers:

1. Navigate to **Administration > System Settings**
2. Select "SSO Configuration"
3. Configure **Google OAuth2**:
   - Client ID
   - Client Secret
   - Callback URL
4. Configure **Microsoft OAuth2**:
   - Client ID
   - Client Secret
   - Callback URL
5. Save and test each provider

Users can then authenticate with their corporate Google or Microsoft accounts.

### SMTP Configuration

Connect CyberBridge to email infrastructure for notifications:

1. Navigate to **Administration > System Settings**
2. Select "SMTP Configuration"
3. Add SMTP server entries (multiple records supported):
   - Server hostname and port
   - Authentication credentials
   - Sender address
   - TLS/SSL settings
4. Send a test email to verify configuration
5. Save changes

Once configured, CyberBridge can send password reset emails, verification messages, and notifications.

### CRA Mode Toggle

Enable or disable Cyber Resilience Act specific features per organization:

1. Navigate to **Administration > System Settings**
2. Select "CRA Mode"
3. Toggle CRA Mode on or off for specific organizations
4. When enabled, users see a streamlined interface focused on EU CRA compliance workflows

### Super Admin Focused Mode

Enable a simplified administrative interface:

1. Navigate to **Administration > System Settings**
2. Toggle "Super Admin Focused Mode"
3. When enabled, the sidebar menu is streamlined to show only:
   - Dashboard
   - Frameworks (with all configuration options)
   - Organizations
   - Users
   - Activity Log
   - Correlations
   - Background Jobs
   - System Settings
4. This reduces visual clutter for power users managing multiple organizations

### Domain Blacklist

Prevent registration from unwanted email domains:

1. Navigate to **Administration > System Settings**
2. Select "Domain Blacklist"
3. Add email domains to block (e.g., temporary email services)
4. Users with blacklisted email domains cannot register

## Correlations

Manage cross-framework question correlations:

1. Navigate to **Administration > Correlations**
2. Select two frameworks to compare
3. Manually create correlations between related questions
4. Use AI-powered suggestion engine with configurable confidence thresholds
5. Review and apply suggestions
6. Manage all correlations in a searchable table
7. Use Correlation Audit to validate data integrity with auto-fix

### LLM Optimization Settings

Tune the AI correlation engine:
- Question limits per batch
- Timeout settings
- Confidence thresholds
- Maximum correlations per question

## Background Jobs

Monitor scheduled and running tasks across the system:

1. Navigate to **Administration > Background Jobs**
2. View active and completed background jobs
3. Track job status, execution history, and errors

### NVD Synchronization

1. Navigate to the **NVD Sync** tab within Background Jobs
2. View NVD sync settings: schedule configuration, API key status, and last sync time
3. Review sync statistics: total CVEs cached, severity breakdown, and CPE match count
4. Trigger a manual NVD sync to fetch the latest CVE data from the NVD API 2.0
5. View sync history with details on CVEs processed, added, and updated per sync run
6. NVD data enriches scan findings with CVE descriptions, CVSS scores, and severity levels

### EUVD Synchronization

1. Navigate to the **EUVD Sync** tab within Background Jobs
2. View EUVD sync settings: sync interval, enabled/disabled status, and last sync time
3. Edit sync interval (hours and seconds) and toggle sync on or off
4. Trigger a manual EUVD sync to fetch the latest vulnerability data from ENISA
5. Review sync history with details on vulnerabilities processed, added, and updated
6. View total cached EUVD vulnerabilities including exploited, latest, and critical categories

### Backup Management

1. Navigate to the **Backups** tab within Background Jobs
2. View a list of all backup records with filename, size, type (scheduled or manual), and status
3. Trigger a manual backup for the current organization
4. Download completed backup files
5. Delete old backups that are no longer needed
6. Restore from a backup to recover organization data
7. Configure backup settings per organization:
   - **Enable/Disable**: Toggle automatic backups
   - **Frequency**: Daily, weekly, or monthly
   - **Retention Period**: Number of years to retain backups

### Scan Schedule Management

1. Navigate to the **Scan Schedules** tab within Background Jobs
2. View all recurring scan schedules with scanner type, target, frequency, and status
3. Create new scan schedules with:
   - **Scanner Type**: ZAP, Nmap, Semgrep, OSV, or Syft
   - **Scan Target**: URL, IP address, or repository
   - **Schedule Type**: Interval-based or cron-based
   - **Interval Settings**: Months, days, hours, minutes, and seconds between runs
   - **Cron Settings**: Day of week, hour, and minute for scheduled runs
4. Edit existing schedules to change targets, frequency, or configuration
5. Enable or disable individual schedules without deleting them
6. Delete schedules that are no longer needed
7. Monitor last run time, next run time, run count, and error messages

### Database Cleanup

1. Navigate to the **History Cleanup** tab within Background Jobs
2. View current cleanup configuration: enabled status, retention days, and cleanup interval
3. Configure cleanup settings:
   - **Retention Period**: Number of days to keep historical records
   - **Cleanup Interval**: Hours between automatic cleanup runs
   - **Enable/Disable**: Toggle automatic cleanup
4. Trigger manual cleanup to remove records older than the retention period

## Activity Log (History)

Access complete audit history across all organizations:

1. Navigate to **Administration > Activity Log**
2. View all actions across all organizations
3. Advanced filtering:
   - By organization
   - By user
   - By action type (create, update, delete, export)
   - By entity type
   - By date range
4. Export comprehensive audit reports
5. Delete individual entries or clear all history for an organization

## Audit Engagements

Create and manage external audit engagements:

1. Navigate to **Audit Engagements**
2. Create time-bound audit engagements
3. Invite external auditors via magic link authentication
4. Assign roles: Guest Auditor (read-only) or Auditor Lead (findings + sign-off)
5. Configure IP allowlisting for auditor access
6. Monitor audit activity and notification badges
7. Track comments, findings, evidence requests, and sign-off

## Controls Management

System-wide control management:

1. Navigate to **Controls > Control Register** to register and manage controls
2. Navigate to **Controls > Controls Library** to browse and import templates
3. Link controls to risks, policies, and framework objectives
4. Track implementation and review status across organizations

## Incident Management

1. Navigate to **Risks > Incident Registration**
2. View and manage incidents across organizations
3. Link incidents to assets, risks, and frameworks
4. Track incident lifecycle and resolution

## Compliance Chain

1. Navigate to **Compliance Chain > All Links** to view all entity relationships
2. Navigate to **Compliance Chain > Map** for interactive visualization
3. Analyze cross-organization compliance patterns
4. Identify gaps in compliance coverage

### Gap Analysis

1. Navigate to **Compliance Chain > Gap Analysis**
2. Select any framework across any organization to analyze
3. Review the compliance summary including overall compliance score
4. Examine objectives analysis (compliant, partially compliant, not compliant, not assessed), assessment completion rates, and policy coverage
5. Review chapter-by-chapter compliance breakdown
6. Identify specific gaps: objectives without evidence, non-compliant objectives, and objectives without policies
7. Export gap analysis reports to PDF for cross-organization reporting

## CE Marking Checklists

System-wide oversight of CE marking checklists across organizations.

1. Navigate to **Assets / Products > CE Marking Checklist**
2. View all CE marking checklists across organizations
3. Monitor checklist completion status: Not Started, In Progress, Ready, Approved
4. Review document completion tracking for required CE marking documents
5. Oversee checklist item progress and custom item additions

## Security Advisories

System-wide management of security advisories across all organizations.

1. Navigate to **Risks > Security Advisories**
2. View and manage advisories across organizations
3. Create, edit, and delete security advisories with severity levels (Critical, High, Medium, Low)
4. Track advisory lifecycle: Draft, Review, Published, Updated, Archived
5. Link advisories to incidents for cross-organization traceability
6. Monitor advisory statistics: total count, published, drafts, and severity distributions

## CRA Technical File Access Control

Control access to CRA-specific documentation pages per organization.

1. CRA Technical File pages are available under **Documents > Technical File** when CRA Mode is enabled
2. Pages include: Patch & Support Policy, Vulnerability Disclosure, SBOM Management, Secure SDLC Evidence, Security Design, and Dependency Policy
3. Enable or disable CRA Mode per organization through **Administration > System Settings > CRA Mode**
4. When CRA Mode is enabled, users see the Technical File submenu and EU Declaration of Conformity page
5. When CRA Mode is disabled, these pages are hidden from the organization's menu

## Documents

### Policies

1. Navigate to **Documents > Policies**
2. View policies across organizations (with cross-org warnings)
3. Create, edit, and manage policies with framework/objective mapping

### Architecture Diagrams

1. Navigate to **Documents > Architecture**
2. Manage architecture documentation linked to frameworks and risks

### Evidence Library

1. Navigate to **Documents > Evidence**
2. Manage evidence items with integrity verification
3. Link evidence to frameworks and controls

## Cyber Threat Intelligence (CTI)

System-wide threat intelligence aggregation and monitoring.

### CTI Dashboard

1. Navigate to **Threat Intelligence > Overview**
2. View aggregated threat statistics across all scanner sources
3. Monitor: Total Indicators, Sightings, Malware Families, MITRE ATT&CK Patterns
4. Threat Timeline showing detection trends over configurable time periods
5. Source breakdown cards for Suricata IDS, Wazuh SIEM, and CAPE sandbox

### MITRE ATT&CK View

1. Navigate to **Threat Intelligence > MITRE ATT&CK**
2. Top detected techniques ranked by frequency
3. Source distribution pie chart across all integrations
4. Recent indicators with confidence scores and labels
5. Recent attack patterns with MITRE IDs

### Scanner CTI Views

Navigate to scanner-specific pages for detailed breakdowns:

- **Network** (`/cti/network`): Nmap findings by host, port, service
- **Web Vulnerabilities** (`/cti/web-vulns`): ZAP findings by risk and CWE
- **Code Analysis** (`/cti/code-analysis`): Semgrep findings by severity and OWASP
- **Dependencies** (`/cti/dependencies`): OSV findings by CVE severity and ecosystem

### CTI Service Administration

The CTI microservice runs independently on port 8020 with three background jobs:

| Job | Interval | Purpose |
|-----|----------|---------|
| Scanner Connector Run | 1 hour | Polls scanner APIs and ingests findings |
| MITRE ATT&CK Sync | 7 days | Syncs enterprise techniques from MITRE GitHub |
| CISA KEV Sync | 1 day | Syncs Known Exploited Vulnerabilities from CISA |

Configuration is done via environment variables:
- `SCANNER_POLL_INTERVAL`: Scanner polling interval in seconds (default 3600)
- `MITRE_SYNC_INTERVAL`: MITRE sync interval in seconds (default 604800)
- `KEV_SYNC_INTERVAL`: KEV sync interval in seconds (default 86400)
- `NMAP_TARGETS`, `ZAP_TARGETS`: Comma-separated scan targets

## Dark Web Intelligence

System-wide dark web monitoring with Tor-based search capabilities.

### Dark Web Dashboard

1. Navigate to **Dark Web Intelligence > Dashboard**
2. View real-time KPIs: Queue Length, Processing Count, Active Workers, Total Scans
3. Recent scan activity table with status tracking
4. Quick action panel for common operations

### Running Dark Web Scans

1. Navigate to **Dark Web Intelligence > Scans**
2. Create scans with keywords to search across 23 dark web engines
3. Scans are queued and processed asynchronously via Tor proxy
4. Monitor progress with auto-refreshing status updates
5. View, download, or delete completed scans

### Dark Web Scan Results

Completed scans include:
- Findings categorized by type: passwords, databases, credentials, emails, leaks
- Severity scoring (0-100) based on category weights and occurrence density
- Context snippets with keyword highlighting
- PDF threat intelligence reports with charts and detailed findings

### Dark Web Reports

1. Navigate to **Dark Web Intelligence > Reports**
2. View all completed scans as report cards with Breach/Secure status
3. Download reports in PDF or JSON format
4. Search and filter by keyword

### Dark Web Settings (Admin)

1. Navigate to **Dark Web Intelligence > Settings**
2. **Worker Configuration**: Slider to set max concurrent scans (1-10)
3. **Search Engine Configuration**: Toggle 23 available dark web engines on/off
4. Settings are persisted per organization in PostgreSQL

### Dark Web Service Administration

The dark web scanner runs independently on port 8030 (internal 8001) with:
- Built-in Tor daemon for SOCKS5 proxy (port 9050)
- PostgreSQL-based job queue with `FOR UPDATE SKIP LOCKED` atomicity
- Automatic recovery of orphaned scans on service restart
- Configurable worker pool (1-10 threads)

Environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `MAX_SCAN_WORKERS`: Initial worker count (default 3)

## Security Tools

Full access to all security scanning tools:

- **Security Scanners (ZAP)**: Web application scanning
- **Network Scanner (Nmap)**: Network discovery and auditing
- **Code Analysis (Semgrep)**: Static code analysis
- **Dependency Check (OSV)**: Dependency vulnerability scanning
- **SBOM Generator (Syft)**: Software Bill of Materials generation
- **Scan Findings**: Unified dashboard of findings across all scanners

## Best Practices for Super Admins

### Security

1. **Limit Super Admin Accounts**: Only create super admin accounts when absolutely necessary
2. **Regular Audits**: Review super admin activity regularly
3. **Strong Passwords**: Enforce strong password policies
4. **Access Reviews**: Periodically review all user access levels
5. **Domain Blacklisting**: Block disposable email domains from registration

### Organization Management

1. **Consistent Naming**: Use consistent naming conventions for organizations
2. **Logo Branding**: Upload organization logos for a professional experience
3. **History Cleanup**: Configure retention policies for each organization
4. **Template Permissions**: Only grant framework templates relevant to each organization

### LLM Configuration

1. **Provider Selection**: Choose the provider that best fits privacy, performance, and cost needs
2. **Test Connections**: Always test LLM connections after configuration changes
3. **Monitor Usage**: Track AI feature usage through background jobs
4. **Tune Thresholds**: Adjust correlation confidence thresholds based on result quality

### Framework Management

1. **Version Control**: Track framework versions through Framework Updates
2. **Template Management**: Keep framework templates up to date
3. **Testing**: Test framework clones before production use
4. **Cross-Framework Correlations**: Set up correlations to reduce duplicate work

### Monitoring

1. **Background Jobs**: Check background jobs regularly for failed tasks
2. **Activity Log**: Review activity logs for unusual patterns
3. **User Sessions**: Monitor online users and session durations
4. **Scanner Access**: Regularly review which organizations have scanner access

## Troubleshooting

### Organization Issues

**Organization not appearing:**
- Verify organization was created successfully
- Check for duplicate domain names
- Review system logs for errors

**Users can't access organization:**
- Verify user is assigned to correct organization
- Check user's active status
- Verify role permissions

### Framework Issues

**Framework clone failed:**
- Check source framework integrity
- Verify target organization exists
- Review system logs for specific errors

**Questions not appearing:**
- Verify question-framework associations
- Check assessment type configuration
- Refresh framework data

### System Issues

**LLM not responding:**
- Verify LLM provider configuration (endpoint URL, API key, model)
- Test the connection from System Settings
- Check Background Jobs for processing errors
- If using llama.cpp, ensure the service container is running

**SSO login failing:**
- Verify OAuth2 client ID and secret
- Check callback URL configuration
- Ensure user's email domain matches organization domain

**SMTP not sending emails:**
- Verify SMTP server settings and credentials
- Send a test email from System Settings
- Check that TLS/SSL settings match the server requirements

**Performance degradation:**
- Check database connections
- Review Background Jobs for stuck tasks
- Monitor resource utilization
- Review Activity Log for excessive operations

**Authentication failures:**
- Verify JWT configuration
- Check token expiration settings
- Review authentication logs

### CTI Issues

**CTI dashboard shows no data:**
- Verify the CTI service container is running: `docker logs cyberbridge_cti_service`
- Check that scanner services are running and producing results
- Verify `NMAP_TARGETS` and `ZAP_TARGETS` environment variables are set correctly
- Wait for the next scheduled connector run (default: every 1 hour)
- Trigger a manual connector run if needed via the ingest endpoint

**MITRE ATT&CK techniques not appearing:**
- Check MITRE sync job status in CTI service logs
- Verify internet connectivity from the CTI container (needs access to raw.githubusercontent.com)
- Manual sync occurs 10 seconds after service startup

### Dark Web Issues

**Dark web scans fail immediately:**
- Verify the dark web scanner container is running: `docker logs cyberbridge_darkweb_scanner`
- Check Tor daemon status inside the container
- Verify PostgreSQL connectivity from the dark web service
- Review error messages in the scan result

**Dark web scans stuck in processing:**
- Check queue overview for worker status
- Scans stuck >30 minutes are auto-recovered on service restart
- Restart the dark web scanner service to trigger recovery
- Verify Tor SOCKS5 proxy is accessible at port 9050 inside the container

**No engines available:**
- Check engine configuration via `GET /dark-web/settings/engines`
- Ensure at least one engine is enabled
- Dark web engines may be temporarily offline; check `engine_status` in scan results

### Scanner Issues

**Scanners not visible to organization:**
- Verify scanner access is enabled in System Settings
- Check that the organization's domain is in the allowed list
- Ensure scanner services are running (check Background Jobs)

## Emergency Procedures

### User Lockout

If a super admin is locked out:

1. Access database directly
2. Reset password hash
3. Clear any account locks
4. Review security logs

### Data Recovery

1. Identify data loss scope
2. Access backup systems
3. Restore from appropriate backup
4. Verify data integrity

### Service Recovery

1. Check service status via Background Jobs
2. Review error logs
3. Restart affected services
4. Verify functionality

## Support and Escalation

For issues requiring additional support:

1. Document the issue thoroughly
2. Collect relevant logs (Activity Log, Background Jobs)
3. Note steps to reproduce
4. Contact system support team

## Appendix

### Role Permission Matrix

| Feature | Org User | Org Admin | Super Admin |
|---------|----------|-----------|-------------|
| View Dashboard | Yes | Yes | Yes |
| Manage Assets | Yes | Yes | Yes |
| Manage Policies | Yes | Yes | Yes |
| Manage Risks | Yes | Yes | Yes |
| Manage Controls | Yes | Yes | Yes |
| Register Incidents | Yes | Yes | Yes |
| Conduct Assessments | Yes | Yes | Yes |
| View Compliance Chain | Yes | Yes | Yes |
| Upload Evidence | Yes | Yes | Yes |
| Run Security Scans | Domain | Domain | Domain |
| Compliance Advisor | No | Yes | Yes |
| Framework Configuration | No | Yes | Yes |
| Manage Users | No | Org Only | All |
| Manage Frameworks | No | Org Only | All |
| Audit Engagements | No | Yes | Yes |
| Clone Frameworks | No | No | Yes |
| Manage Organizations | No | No | Yes |
| System Settings | No | Limited | Full |
| LLM Configuration | No | No | Yes |
| SSO Configuration | No | No | Yes |
| SMTP Configuration | No | No | Yes |
| CRA Mode Toggle | No | No | Yes |
| Focused Mode | No | No | Yes |
| Domain Blacklist | No | No | Yes |
| Background Jobs | No | Yes | Yes |
| NVD/EUVD Sync | No | No | Yes |
| Backup Management | No | No | Yes |
| Scan Schedules | No | Yes | Yes |
| Gap Analysis | Yes | Yes | Yes |
| CE Marking Checklists | Yes | Yes | Yes |
| Security Advisories | Yes | Yes | Yes |
| Risk Assessment | Yes | Yes | Yes |
| CRA Technical File | CRA Mode | CRA Mode | CRA Mode |
| CRA Public Assessments | Public | Public | Public |
| Correlations | No | Yes | Yes |
| CTI Dashboard | Yes | Yes | Yes |
| Dark Web Scans | Yes | Yes | Yes |
| Dark Web Settings | No | Admin | Admin |

### System Architecture

The CyberBridge platform consists of:

- **Frontend**: React application (Port 5173)
- **Backend API**: FastAPI (Port 8000)
- **Database**: PostgreSQL (Port 5433)
- **Security Services**: ZAP (8010), Nmap (8011), OSV (8012), Semgrep (8013), Syft (8014)
- **CTI Service**: Threat Intelligence aggregation (Port 8020)
- **Dark Web Scanner**: Tor-based dark web search (Port 8030)
- **LLM Service**: Configurable (llama.cpp, OpenAI, Anthropic, Google, X AI, QLON)

---

## Super Admin User Flow Examples

This chapter provides step-by-step walkthroughs of common super admin workflows using realistic data.

---

### Example Scenario: Onboarding a New Organization

**Goal**: Set up "Clone Systems, Inc." as a new organization with full compliance capabilities
**Role**: Super Administrator

---

### Example 1: Creating an Organization

**Navigate to**: Administration > Organizations

**Step 1**: Click "Create Organisation"

| Field | Value |
|-------|-------|
| **Name** | Clone Systems, Inc. |
| **Description** | Network Security & Cybersecurity Solutions Provider specializing in managed security services |
| **Domain** | clone-systems.com |

**Step 2**: Click "Create Organisation"

**Step 3**: Upload the organization logo:
- Click on the organization in the list
- Upload the Clone Systems logo file
- The logo will appear in the header bar for all Clone Systems users

**Result**: Clone Systems is now an isolated compliance environment with its own users, frameworks, and data.

---

### Example 2: Configuring Framework Template Permissions

**Navigate to**: Administration > System Settings > Framework Template Permissions

**Step 1**: Select "Clone Systems, Inc." from the organization dropdown

**Step 2**: Enable the following templates:
- ISO/IEC 27001:2022
- CRA (Cyber Resilience Act)
- NIS2 (Network and Information Systems)
- NIST CSF (Cybersecurity Framework)

**Step 3**: Save changes

**Result**: Clone Systems admins can now seed these four framework templates. Other templates (HIPAA, PCI DSS, etc.) will not be available to them.

---

### Example 3: Cloning a Framework to a New Organization

**Navigate to**: Administration > System Settings > Clone Frameworks

**Step 1**: Select the source framework:
- **Framework**: ISO/IEC 27001:2022 (from "Acme Corp" organization)

**Step 2**: Select the target:
- **Target Organization**: Clone Systems, Inc.
- **Custom Name**: ISO/IEC 27001:2022 (leave blank to keep original name)

**Step 3**: Click "Clone Selected Frameworks"

**Result**: Clone Systems now has a complete copy of the ISO 27001 framework with all chapters, objectives, and questions. Assessment data and policies from the source organization are not included.

---

### Example 4: Setting Up LLM Configuration

**Navigate to**: Administration > System Settings > LLM Configuration

**Option A: Self-hosted llama.cpp**

| Field | Value |
|-------|-------|
| **Provider** | llama.cpp |
| **Endpoint URL** | http://llm:8015 |
| **Model** | phi-4 |

**Option B: OpenAI**

| Field | Value |
|-------|-------|
| **Provider** | OpenAI |
| **API Key** | sk-proj-xxxxxxxxxxxx |
| **Model** | gpt-4o |

**Option C: Anthropic**

| Field | Value |
|-------|-------|
| **Provider** | Anthropic |
| **API Key** | sk-ant-xxxxxxxxxxxx |
| **Model** | claude-sonnet-4-20250514 |

Click **Test Connection** to verify the setup, then **Save**.

**Result**: AI features are now active across the platform: Compliance Advisor, question correlations, scan analysis, and objective recommendations.

---

### Example 5: Configuring SSO

**Navigate to**: Administration > System Settings > SSO Configuration

**Google OAuth2:**

| Field | Value |
|-------|-------|
| **Client ID** | 123456789.apps.googleusercontent.com |
| **Client Secret** | GOCSPX-xxxxxxxxxxxx |
| **Callback URL** | https://cyberbridge.clone-systems.com/api/auth/google/callback |

**Microsoft OAuth2:**

| Field | Value |
|-------|-------|
| **Client ID** | xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx |
| **Client Secret** | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
| **Callback URL** | https://cyberbridge.clone-systems.com/api/auth/microsoft/callback |

Save each configuration. Users from Clone Systems can now log in using their Google or Microsoft corporate accounts.

---

### Example 6: Enabling Scanner Access

**Navigate to**: Administration > System Settings > Scanner Configuration

**Step 1**: Ensure scanners are toggled ON globally

**Step 2**: Add "clone-systems.com" to the allowed domains list

**Step 3**: Save changes

**Result**: All users in the Clone Systems organization can now access:
- Security Scanners (ZAP) for web app vulnerability scanning
- Network Scanner (Nmap) for network reconnaissance
- Code Analysis (Semgrep) for static analysis
- Dependency Check (OSV) for dependency vulnerabilities
- SBOM Generator (Syft) for bill of materials

---

### Example 7: Creating a Super Admin and Org Admin

**Navigate to**: Administration > Users

**Create the Org Admin:**

| Field | Value |
|-------|-------|
| **Email** | admin@clone-systems.com |
| **First Name** | Sarah |
| **Last Name** | Johnson |
| **Organization** | Clone Systems, Inc. |
| **Role** | org_admin |

Click **Create User**.

**Create a second Super Admin (for redundancy):**

| Field | Value |
|-------|-------|
| **Email** | sysadmin@cyberbridge.io |
| **First Name** | DevOps |
| **Last Name** | Team |
| **Organization** | CyberBridge Platform |
| **Role** | super_admin |

Click **Create User**.

**Result**: Sarah Johnson can now manage Clone Systems' users, frameworks, and audit engagements. The DevOps team account provides backup super admin access.

---

### Example 8: Setting Up SMTP for Email Notifications

**Navigate to**: Administration > System Settings > SMTP Configuration

**Step 1**: Click "Add SMTP Record"

| Field | Value |
|-------|-------|
| **Server** | smtp.gmail.com |
| **Port** | 587 |
| **Username** | notifications@clone-systems.com |
| **Password** | xxxxxxxxxxxxxxxx (app password) |
| **Sender Address** | CyberBridge <notifications@clone-systems.com> |
| **TLS** | Enabled |

**Step 2**: Click **Send Test Email** to verify the configuration

**Step 3**: Save the record

**Result**: CyberBridge can now send password reset emails, account verification messages, and audit engagement invitations via the Clone Systems email infrastructure.

---

### Example 9: Enabling CRA Mode for an Organization

**Navigate to**: Administration > System Settings > CRA Mode

**Step 1**: Select "Clone Systems, Inc." from the organization dropdown

**Step 2**: Toggle CRA Mode **ON**

**Result**: Clone Systems users now see a streamlined interface focused on EU Cyber Resilience Act compliance. The sidebar menu is simplified to show only CRA-relevant pages: Assessments, Objectives, Assets, Risks, Controls, Documents, Compliance Chain, Security Tools, and Administration.

To revert, toggle CRA Mode OFF and users will see the full menu.

---

### Example 10: Monitoring Background Jobs

**Navigate to**: Administration > Background Jobs

After enabling various features, monitor the background processing:

| Job Type | Status | Details |
|----------|--------|---------|
| Framework Seed | Completed | ISO 27001 seeded for Clone Systems |
| LLM Connection Test | Completed | LLM connection verified |
| Scan Schedule | Running | Weekly Nmap scan for clone-systems.com |
| Correlation Generation | Completed | 47 correlations found between ISO 27001 and CRA |
| History Cleanup | Scheduled | Next run: 2025-04-01 |

Use this view to:
- Identify and troubleshoot failed jobs
- Monitor scan schedule execution
- Track AI processing tasks
- Verify system health

---

### Recommended Super Admin Onboarding Workflow

When setting up a new organization:

1. **Create the organization** with name, description, and domain
2. **Upload organization logo** for branding
3. **Configure template permissions** (which frameworks they can seed)
4. **Clone frameworks** from existing organizations if applicable
5. **Create the org admin** user account
6. **Enable scanner access** for the organization's domain
7. **Configure SMTP** for email notifications
8. **Set up SSO** if the organization uses Google or Microsoft
9. **Enable CRA Mode** if the organization focuses on EU CRA compliance
10. **Configure LLM** provider for AI features
11. **Monitor Background Jobs** to verify everything is processing correctly
12. **Review Activity Log** to confirm the organization is operational
