# CyberBridge User Manual

**Version:** 10.0
**Last Updated:** February 2025

## Overview

CyberBridge is a comprehensive cybersecurity Governance, Risk, and Compliance (GRC) platform that helps organizations manage their security posture, conduct compliance assessments, track risks and incidents, manage controls and policies, and maintain regulatory requirements across multiple frameworks.

## Getting Started

### System Access
- Access the application through your web browser at the provided URL
- Log in with your assigned credentials, or use Single Sign-On (SSO) with Google or Microsoft if configured
- Your access level depends on your assigned role (Super Admin, Org Admin, Org User)
- External auditors access the platform through a separate auditor portal with magic link authentication

### Dashboard Overview
Upon login, you'll see the main dashboard with:
- Key compliance metrics (frameworks, assessments, risks, policies, controls)
- Active frameworks and progress indicators
- Recent assessment activity carousel
- Assessment analytics (pie charts, line charts, funnel)
- Policy and risk analytics
- User analytics and session tracking
- Quick actions including a user guide wizard

## Core Features

### 1. Compliance Assessments

**Creating an Assessment**
1. Navigate to "Assessments" from the main menu
2. Click "New Assessment"
3. Select your compliance framework (ISO 27001, CRA, NIS2, NIST CSF, PCI DSS, SOC 2, HIPAA, GDPR, CMMC 2.0, DORA, etc.)
4. Choose assessment type and scope (Product, Organization, or Other)
5. Begin answering questions systematically

**Completing Questions**
- Questions are organized by framework chapters and objectives
- Provide detailed responses with supporting evidence
- Upload relevant documents as evidence files
- Link answers to policies for traceability
- Use the AI Compliance Advisor for guidance on complex requirements
- Save progress frequently - assessments can be completed over multiple sessions
- Correlated questions across frameworks are automatically linked

**Assessment Status Tracking**
- Monitor completion progress for each framework section
- Review answered vs. pending questions
- Track evidence collection status
- Export assessments as PDF or ZIP (with evidence files)
- Import/export assessment data via CSV

### 2. Risk Management

**Risk Registry**
- View all identified risks across your organization
- Risks are categorized by asset category and severity
- Monitor risk status: Reduce, Avoid, Transfer, Share, Accept, Remediated
- Link risks to specific assets and compliance objectives
- Link risks to scan findings from security scanners

**Risk Assessment**
- Define risk likelihood, severity, and residual risk (Low, Medium, High, Critical)
- Assign risk categories aligned with your framework
- Scope risks to specific products or organizations
- Document current and planned control measures
- Use risk templates for common risk patterns

**Risk Reporting**
- Export risk registers to PDF
- View risk analytics on the dashboard

### 3. Incident Management

**Incident Registry**
- Record and track security incidents
- Categorize incidents by status and severity
- Link incidents to affected assets and risks
- Link incidents to relevant frameworks
- Track incident timeline and resolution

### 4. Controls Management

**Control Registry**
- Register and track security controls
- Organize controls into control sets
- Link controls to risks they mitigate
- Link controls to policies that define them
- Link controls to framework objectives
- Track control implementation and review status

**Controls Library**
- Browse pre-built control templates
- Import controls from control set templates
- Map controls across multiple frameworks

### 5. Policy Management

**Policy Library**
- Centralized repository of organizational policies
- Link policies to compliance frameworks and objectives
- Track policy lifecycle: Draft, Review, Ready for Approval, Approved
- Upload and manage policy documents
- Link policies to specific controls and objectives

**Policy Assignment**
- Assign policies to specific compliance objectives
- Map policies across multiple frameworks
- AI-powered policy alignment suggests framework mappings

### 6. Assets (Products & Services)

**Asset Inventory**
- Register all organizational assets, products, and services
- Categorize by asset type, category, and criticality level
- Track asset lifecycle and compliance requirements
- EU CRA classification support (ANNEX III Class I/II, ANNEX IV)
- Economic operator roles (Manufacturer, Importer, Distributor)
- Software Bill of Materials (SBOM) tracking

**Asset Compliance Tracking**
- Monitor compliance status for each asset
- Link assets to assessments, risks, and scan findings
- Generate asset-specific documentation

### 7. Compliance Chain

**Compliance Chain Links**
- View and manage all links between compliance entities
- See relationships: Assets, Risks, Controls, Policies, Objectives, Incidents
- Create and delete compliance links

**Compliance Chain Map**
- Visual interactive map showing all compliance relationships
- Navigate entity connections graphically
- Identify gaps in compliance coverage

### 8. Framework Management (Admin)

**Framework Configuration**
- Seed frameworks from 15+ built-in templates
- Create custom frameworks
- Import frameworks from Excel files
- Manage chapters and objectives hierarchy
- Manage framework questions with CSV bulk import
- Track framework version updates

**Compliance Advisor (AI)**
- AI-powered compliance guidance per framework
- Get contextual recommendations for objectives
- Analyze compliance gaps with AI assistance

**Objectives Checklist**
- Track compliance status per objective: Compliant, Partially Compliant, Not Compliant, In Review, Not Assessed, Not Applicable
- AI-powered compliance suggestions with confidence scores
- Upload evidence files directly to objectives
- Link objectives to policies and risks
- Export gap analysis reports as PDF

### 9. Security Scanning Integration

**Available Scanners** (domain-based access control)

- **ZAP Proxy (OWASP ZAP)**: Web application security scanning
  - Scan types: Spider, Active, Full, API
  - AI-powered remediation suggestions
  - Scan history with results tracking

- **Nmap**: Network discovery and security auditing
  - Scan types: Basic, Port Scan, All Ports, Aggressive, OS Detection, Network, Stealth, No Ping, Fast
  - CVE correlation with NVD database
  - AI-powered remediation suggestions

- **Semgrep**: Static code analysis
  - Security rules and custom configurations
  - Scan history tracking

- **OSV Scanner**: Open-source dependency vulnerability scanning
  - Multiple lock file format support
  - Scan history tracking

- **Syft**: Software Bill of Materials (SBOM) generation
  - Package and dependency inventory
  - SBOM report generation

**Scan Management**
- View unified scan findings dashboard
- Track scan history across all scanners
- Schedule recurring scans (hourly, daily, weekly, monthly)
- Link scan findings to risks
- Export scan results

### 10. AI-Powered Analysis

**Multi-Provider LLM Support**
- llama.cpp (self-hosted), OpenAI, Anthropic, Google, X AI, QLON
- Configurable per organization

**AI Capabilities**
- Question correlation analysis across frameworks
- Compliance Advisor for framework guidance
- Policy alignment suggestions
- Scan result analysis and remediation suggestions (ZAP, Nmap)
- Objective compliance recommendations

### 11. Audit Engagements (Admin)

**External Auditor Portal**
- Create audit engagements with time-bound access
- Invite external auditors via magic link authentication
- Role-based auditor permissions (Guest Auditor, Auditor Lead)
- Auditor comments and findings tracking
- Evidence request workflow
- Audit sign-off process
- IP allowlisting for auditor access
- Audit activity logging

### 12. Architecture Diagrams

- Upload and manage architecture diagram files
- Link diagrams to frameworks and risks
- Visual reference for compliance documentation

### 13. Evidence Library

- Centralized evidence repository
- Link evidence items to frameworks and controls
- Evidence integrity verification
- Organize evidence across compliance requirements

## Navigation Guide

### Main Menu Sections

**Assessments** - Create and manage compliance assessments

**Frameworks** (with submenu)
- Compliance Advisor (AI guidance, admin only)
- Objectives Checklist
- Configuration submenu (Framework Management, Chapters & Objectives, Questions, Updates - admin only)

**Assets** - Asset/product inventory and compliance tracking

**Risks** (with submenu)
- Risk Register
- Incident Registration

**Controls** (with submenu)
- Control Register
- Controls Library

**Documents** (with submenu)
- Policies
- Architecture Diagrams
- Evidence Library

**Compliance Chain** (with submenu)
- All Links
- Map (visual)

**Security Tools** (domain-restricted access, with submenu)
- ZAP Proxy & Nmap
- Code Analysis (Semgrep)
- Dependency Check (OSV)
- SBOM Generator (Syft)
- Scan Findings

**Audit Engagements** (admin only)

**Administration** (admin only, with submenu)
- Organizations
- Users
- Activity Log
- Correlations
- Background Jobs
- System Settings

### CRA Mode
Organizations can enable CRA Mode for a streamlined interface focused on EU Cyber Resilience Act compliance workflows.

### Super Admin Focused Mode
Super admins can enable a simplified menu showing only administrative functions.

## Data Export and Reporting

### PDF Generation
- Export assessment results to professional PDF reports
- Generate risk registers and compliance summaries
- Export objectives gap analysis reports
- Export scan results and findings

### Data Visualization
- Interactive compliance dashboards
- Assessment analytics with pie charts, line charts, and funnels
- Policy and risk analytics
- User session analytics

## User Roles and Permissions

### Super Admin
- Full system access and configuration
- All organization management
- Framework management and seeding
- System settings (LLM, SSO, SMTP, scanners)
- User approval and management
- Question correlations
- Background jobs monitoring

### Org Admin
- Organization-level administration
- Framework management within organization
- User management within organization
- Audit engagement management
- All assessment, risk, policy, and control operations

### Org User
- Assessment completion and management
- Risk, policy, and control registration
- Evidence upload and documentation
- Objectives checklist review
- Security scanner access (if permitted)

### Auditor Roles (External)
- **Guest Auditor**: Read-only access to assigned engagement
- **Auditor Lead**: Can add findings, comments, and sign-off

## Technical Requirements

### Browser Compatibility
- Modern web browsers (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Minimum 1024x768 screen resolution

### File Uploads
- Supported formats: PDF, DOC, DOCX, images, spreadsheets, CSV, Excel
- Evidence files should be clearly named and organized

## Support and Troubleshooting

### Common Issues
- **Session Timeouts**: Save work frequently, re-login if needed
- **File Upload Errors**: Check file format and size limitations
- **Scanner Access**: Scanner access is controlled by domain settings - contact your admin if scanners are not visible
- **SSO Issues**: Ensure your organization has SSO configured and your email domain matches

### Getting Help
- Contact your system administrator for technical issues
- Refer to your organization's compliance team for framework-specific questions
- Use the AI Compliance Advisor for real-time guidance during assessments
- Check the in-app Documentation page for additional resources

## Security and Privacy

### Data Protection
- All data is encrypted in transit and at rest
- Role-based access controls protect sensitive information
- Organization-level data isolation
- Regular security scans ensure platform security
- Comprehensive audit trails track all user activities
- Evidence integrity verification

### Authentication
- JWT-based authentication with configurable session duration
- Single Sign-On (SSO) support (Google, Microsoft OAuth2)
- Email verification for new accounts
- Magic link authentication for external auditors
- Domain blacklisting for registration control

### Best Security Practices
- Use strong, unique passwords
- Enable SSO where available
- Log out when sessions are complete
- Report suspicious activities immediately
- Keep evidence files organized and properly labeled

---

*This manual covers CyberBridge v10.0 features. For technical implementation details, refer to the developer documentation (CLAUDE.md). For installation, refer to the installation guide.*
