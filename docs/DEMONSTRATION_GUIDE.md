# CyberBridge GRC Platform - Demonstration Guide

## 🎯 Demonstration Scenario

**Company:** TechSecure IoT Solutions
**Product:** Smart Home Security Camera System (Hardware + Software)
**Compliance Need:** EU Cyber Resilience Act (CRA) - Annex III Class I Product
**Timeline:** Pre-market conformity assessment before CE marking

---

## 📋 Demonstration Flow (30-45 minutes)

### **Phase 1: System Overview & User Management** (5 minutes)

#### 1.1 Login as Super Admin
- **URL:** `http://38.126.154.32:5173`
- **Credentials:** `superadmin@clone-systems.com`
- Show the dashboard overview

#### 1.2 Organization Setup
- Navigate to **Admin Panel** → **Organizations**
- Show existing organization: "Clone Systems"
- Explain the multi-tenant architecture

#### 1.3 User Management
- Navigate to **Users Management**
- Show different user roles:
  - **Super Admin:** Full system access
  - **Org Admin:** Organization-level management
  - **Org User:** Limited access to assessments
- **Action:** Create a new user account
  - Email: `assessor@clone-systems.com`
  - Role: Org User
  - Show email verification process

---

### **Phase 2: Asset Registration & Risk Assessment** (8-10 minutes)

#### 2.1 Register the Asset
- Navigate to **Assets** → **Add New Asset**
- **Fill in details:**
  - Asset Name: "SecureVision Pro Camera"
  - Asset Type: Hardware
  - Economic Operator: Manufacturer
  - Status: Testing
  - Criticality: ANNEX III - Class I
  - Select criticality option: "Smart home products with security functionalities"

#### 2.2 Risk Identification
- Navigate to **Risks** → **Add New Risk**
- **Create Risk #1:**
  - Risk Title: "Weak Authentication Vulnerability"
  - Category: Access Control
  - Asset Type: Hardware
  - Severity: High
  - Likelihood: Medium
  - Description: "Default credentials not enforced to change on first use"
  - Potential Impact: "Unauthorized access to camera feeds"
  - Control Measures: "Implement mandatory password change on first login with complexity requirements"
  - Status: Reduce

- **Create Risk #2:**
  - Risk Title: "Unencrypted Video Transmission"
  - Category: Communication Security
  - Severity: Critical
  - Likelihood: High
  - Description: "Video streams transmitted without end-to-end encryption"
  - Potential Impact: "Data interception, MITM attacks"
  - Control Measures: "Implement TLS 1.3 for all communications"
  - Status: Remediated

- **Show Risk Dashboard:**
  - Visual representation of risk severity
  - Risk matrix visualization
  - Export risk report as PDF

---

### **Phase 3: Framework Selection & Assessment Setup** (5-7 minutes)

#### 3.1 Framework Management
- Navigate to **Frameworks** → **Seed Framework**
- **Select Framework:** EU Cyber Resilience Act (CRA)
- **Upload Excel/Import:**
  - Show framework import capabilities
  - Demonstrate bulk question import from Excel
  - Explain how frameworks are structured:
    - Chapters (e.g., Annex I - Essential Requirements)
    - Objectives (specific requirements)
    - Questions (assessment criteria)

#### 3.2 Create Assessment
- Navigate to **Assessments** → **New Assessment**
- **Assessment Details:**
  - Framework: EU Cyber Resilience Act
  - Assessment Type: Conformity Assessment
  - Product: SecureVision Pro Camera
  - Assessor: Select current user
  - Start Date: Today

---

### **Phase 4: Conducting the Assessment** (10-12 minutes)

#### 4.1 Answering Questions
- Navigate to **Assessments** → Select created assessment
- **Show different question types and responses:**

**Example 1: Security Documentation**
- Question: "Does the product have comprehensive security documentation?"
- Answer: "Yes"
- Compliance Status: Compliant
- Evidence: Upload "Security_Architecture.pdf"
- Evidence Description: "Detailed security architecture document including threat model"

**Example 2: Vulnerability Management**
- Question: "Is there a process for handling vulnerability disclosures?"
- Answer: "Partially"
- Compliance Status: Partially Compliant
- Evidence: Upload "Vulnerability_Disclosure_Policy.pdf"
- Evidence Description: "Policy exists but needs to include timeline commitments"
- **Link to Risk:** Connect to "Weak Authentication Vulnerability" risk

**Example 3: Update Mechanism**
- Question: "Does the product support secure automatic updates?"
- Answer: "Yes"
- Compliance Status: Compliant
- Evidence: Upload "Update_Mechanism_Specification.pdf"
- Evidence Description: "Signed OTA updates with rollback capability"

**Example 4: Supply Chain Security**
- Question: "Is an SBOM (Software Bill of Materials) maintained?"
- Answer: "No"
- Compliance Status: Not Compliant
- Evidence: None
- Notes: "SBOM generation to be implemented in next sprint"

#### 4.2 AI-Powered Features (Show Innovation)
- Navigate to **AI Tools** → **Question Correlations**
- **Demonstrate:**
  - Upload a technical document (e.g., product specification)
  - Show AI analyzing and mapping content to framework questions
  - AI suggests relevant answers based on document content
  - Confidence scores for each suggestion

---

### **Phase 5: Policy Management** (5-7 minutes)

#### 5.1 Create Security Policy
- Navigate to **Policies** → **Add New Policy**
- **Policy Details:**
  - Title: "Secure Software Development Lifecycle Policy"
  - Status: Draft
  - Description: "Guidelines for secure coding practices and code review requirements"
  - Upload policy document: "SSDLC_Policy.docx"
  - **Link to Framework:** EU Cyber Resilience Act
  - **Link to Objectives:** Multiple security-by-design objectives

#### 5.2 Policy-Objective Mapping
- Show how policies support multiple compliance objectives
- Demonstrate policy approval workflow:
  - Draft → Review → Ready for Approval → Approved

---

### **Phase 6: Objectives & Compliance Tracking** (5 minutes)

#### 6.1 Objectives Dashboard
- Navigate to **Objectives** → Select framework chapter
- **Show compliance status tracking:**
  - Not Assessed (grey)
  - Not Compliant (red)
  - Partially Compliant (yellow)
  - In Review (blue)
  - Compliant (green)
  - Not Applicable (grey striped)

#### 6.2 Gap Analysis
- Filter objectives by compliance status
- Show "Not Compliant" and "Partially Compliant" items
- Generate gap analysis report
- Export action items for remediation

---

### **Phase 7: Security Scanning Integration** (5-7 minutes)

#### 7.1 Configure Scanners
- Navigate to **Admin Panel** → **Scanner Settings**
- **Show available scanners:**
  - OWASP ZAP (Web Application Scanner)
  - Nmap (Network Scanner)
  - Semgrep (SAST - Static Code Analysis)
  - OSV Scanner (Dependency Vulnerability Scanner)
  - Syft (SBOM Generator)

#### 7.2 Run Vulnerability Scan
- Navigate to **Scanners** → **Run Scan**
- **Demo scan configuration:**
  - Target: Camera web interface URL
  - Scanner: OWASP ZAP
  - Scan Type: Baseline scan
- Show scan results in real-time
- Demonstrate vulnerability findings integration

#### 7.3 Link Scan Results to Risks
- Show how scan findings automatically create/update risks
- Link vulnerabilities to assessment questions
- Generate compliance evidence from scan reports

#### 7.4 Controls Management (New Feature)
- Navigate to **Controls** → **Control Register**
- Create a control linked to the identified risks
- Show how controls map to framework objectives
- Navigate to **Controls Library** for pre-built control templates

#### 7.5 Compliance Chain Visualization
- Navigate to **Compliance Chain** → **Map**
- Show the visual relationship map connecting:
  - Assets → Risks → Controls → Policies → Objectives
- Demonstrate how all compliance entities are interconnected

---

### **Phase 8: Reporting & Documentation** (5 minutes)

#### 8.1 Generate Assessment Report
- Navigate to current assessment → **Export PDF**
- **Show comprehensive report including:**
  - Executive summary
  - Compliance status overview
  - Detailed question responses
  - Evidence attachments
  - Risk assessment results
  - Gap analysis
  - Remediation recommendations

#### 8.2 Audit Trail
- Navigate to **History** → **Audit Logs**
- **Demonstrate compliance audit trail:**
  - Who made changes
  - What was changed
  - When changes occurred
  - Change history for all entities (policies, risks, assessments)
- Show filtering by date range and user
- Export audit logs for compliance records

---

### **Phase 9: Dashboard & Analytics** (3 minutes)

#### 9.1 Compliance Dashboard
- Navigate to **Home/Dashboard**
- **Show key metrics:**
  - Overall compliance percentage
  - Active assessments count
  - High-severity risks
  - Pending policy approvals
  - Recent activities

#### 9.2 Real-time Collaboration
- Show **User Sessions** tracking
- Demonstrate activity monitoring
- Show who's currently working on assessments

---

### **Phase 10: Advanced Features Demo** (Optional - 5 minutes)

#### 10.1 LLM Integration
- Navigate to **Admin Panel** → **LLM Settings**
- Show multi-provider LLM configuration (llama.cpp, OpenAI, Anthropic, Google, X AI, QLON)
- Demonstrate AI-powered question suggestions
- Show confidence threshold settings

#### 10.2 Framework Updates
- Navigate to **Admin Panel** → **Framework Updates**
- Show version control for frameworks
- Demonstrate how framework updates are tracked
- Show update application workflow

#### 10.3 Email Verification & Notifications
- Show SMTP configuration
- Demonstrate email verification flow for new users
- Show password reset functionality

#### 10.4 Single Sign-On (SSO)
- Navigate to **Settings** → **SSO Configuration**
- Show Google and Microsoft OAuth2 integration
- Demonstrate SSO login flow

#### 10.5 External Audit Portal
- Navigate to **Audit Engagements** → Create New Engagement
- Show how to invite external auditors with magic link
- Demonstrate the separate auditor review workspace
- Show audit findings and sign-off workflow

#### 10.6 Incident Management
- Navigate to **Risks** → **Incidents**
- Show incident registration and tracking
- Link incidents to assets and risks

---

## 🎬 Presentation Tips

### Opening (2 minutes)
1. **Problem Statement:**
   - "With the EU Cyber Resilience Act coming into force, manufacturers of IoT devices face complex compliance requirements"
   - "Traditional compliance management using spreadsheets and documents is error-prone and inefficient"
   - "Organizations need a centralized platform to manage assessments, risks, policies, and evidence"

2. **Solution Introduction:**
   - "CyberBridge is a comprehensive GRC platform designed specifically for cybersecurity compliance"
   - "Built with modern microservices architecture"
   - "Integrates automated security scanning with compliance tracking"

### Throughout the Demo
- **Emphasize real-world value** at each step
- Point out **time-saving features** (AI assistance, automation, bulk imports)
- Highlight **compliance benefits** (audit trail, evidence management, gap analysis)
- Show **collaboration features** (multi-user, role-based access, real-time tracking)

### Closing (2 minutes)
1. **Key Benefits Summary:**
   - ✅ Centralized compliance management
   - ✅ Automated risk assessment
   - ✅ Integrated security scanning
   - ✅ AI-powered assistance
   - ✅ Complete audit trail
   - ✅ Professional reporting
   - ✅ Framework flexibility (not just CRA)

2. **Technical Highlights:**
   - Modern tech stack (React, FastAPI, PostgreSQL)
   - Microservices architecture for scalability
   - Docker containerization for easy deployment
   - RESTful API for integrations
   - Role-based access control
   - Multi-tenant support

---

## 📊 Demo Data Preparation Checklist

Before the presentation, ensure:

- [ ] Super admin account is accessible
- [ ] Sample product "SecureVision Pro Camera" is created
- [ ] At least 2-3 risks are pre-populated
- [ ] EU CRA framework is seeded and available
- [ ] One sample assessment is partially completed
- [ ] 1-2 policies are created with different statuses
- [ ] Sample documents are prepared for upload:
  - [ ] Security_Architecture.pdf
  - [ ] Vulnerability_Disclosure_Policy.pdf
  - [ ] Update_Mechanism_Specification.pdf
  - [ ] SSDLC_Policy.docx
- [ ] Scanner services are running
- [ ] Test scan target is accessible
- [ ] Email verification is working
- [ ] SSO configuration is set up (if demonstrating SSO)
- [ ] At least 1 control is pre-populated
- [ ] Syft scanner service is running

---

## 🎯 Key Selling Points to Emphasize

1. **Compliance Automation:** Reduces manual effort by 60-70%
2. **Risk Integration:** Direct linkage between risks and compliance requirements
3. **Evidence Management:** Centralized storage with version control
4. **AI Assistance:** Intelligent document analysis and question mapping
5. **Security Integration:** Built-in vulnerability scanning
6. **Audit Readiness:** Complete audit trail with 10-year data retention
7. **Scalability:** Supports multiple organizations, frameworks, and products
8. **Flexibility:** Framework-agnostic (CRA, ISO 27001, NIST, etc.)
9. **External Audit Portal:** Magic link authentication for external auditors
10. **Multi-provider AI/LLM:** Support for llama.cpp, OpenAI, Anthropic, Google, X AI, and QLON
11. **SSO Integration:** Google and Microsoft OAuth2 support
12. **Controls Management:** Control register and compliance chain visualization
13. **Incident Tracking:** Incident registration and management linked to assets and risks
14. **SBOM Generation:** Software Bill of Materials generation with Syft

---

## ⚠️ Common Questions to Prepare For

1. **Q: Can we import our existing compliance data?**
   - A: Yes, via Excel import for frameworks and bulk question upload

2. **Q: How does the AI-powered analysis work?**
   - A: Supports multiple LLM providers: llama.cpp (self-hosted), OpenAI, Anthropic, Google, X AI, and QLON. Configurable per organization.

3. **Q: Is the data secure?**
   - A: Yes, role-based access control, encrypted communications, complete audit trail

4. **Q: Can external auditors access the system?**
   - A: Yes, CyberBridge has a dedicated external auditor portal with magic link authentication, time-bound access, audit comments, findings tracking, and sign-off workflows.

5. **Q: What about updates to compliance frameworks?**
   - A: Framework versioning system tracks updates and allows phased migration

6. **Q: How do you handle multi-tenant environments?**
   - A: Complete data isolation per organization, super admin can manage all

7. **Q: What deployment options are available?**
   - A: Docker containers for on-premise or cloud deployment

---

## 🚀 Alternative Demo Flows

### Quick Demo (15 minutes)
Focus on: Asset Registration → Risk Assessment → Assessment Questions → Reporting

### Technical Demo (45 minutes)
Include: Architecture overview → API demonstration → Scanner integration → LLM configuration

### Executive Demo (10 minutes)
Focus on: Dashboard → Compliance metrics → Risk overview → Sample report

---

## 📝 Post-Demo Follow-up

Provide attendees with:
1. PDF export of sample assessment report
2. Risk assessment dashboard screenshot
3. Link to documentation
4. Trial account setup (if applicable)
5. Architecture diagram
6. Integration capabilities overview

---

**Good luck with your demonstration! 🎉**
