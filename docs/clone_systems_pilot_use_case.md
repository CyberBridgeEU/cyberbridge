# Clone Systems, Inc. - CyberBridge GRC Platform Pilot Use Case

## 🎯 Pilot Scenario Overview

**Company:** Clone Systems, Inc.
**Website:** https://www.clone-systems.com/
**Business:** Network Security & Cybersecurity Solutions Provider
**Pilot Objective:** Demonstrate end-to-end compliance workflow for a managed security service offering
**Use Case:** Clone Systems is launching a new "SecureNet Enterprise" managed security service and needs to achieve ISO/IEC 27001:2022 certification for their Information Security Management System (ISMS)
**Timeline:** 90-day compliance readiness pilot

---

## 📋 Business Context

Clone Systems, Inc. specializes in securing business networks for enterprise clients. To differentiate themselves in the competitive MSSP (Managed Security Service Provider) market and meet client contractual requirements, they need ISO 27001 certification. This pilot demonstrates how CyberBridge helps them:

1. **Register their service offerings** as products in the compliance system
2. **Establish security policies** aligned with ISO 27001 requirements
3. **Identify and manage risks** to their service delivery and client networks
4. **Conduct compliance assessments** against ISO 27001 controls
5. **Track objective completion** toward certification readiness

---

## 🚀 Pilot User Flow (60-90 minutes)

### **Phase 1: Asset Registration** (15 minutes)

**Context:** Clone Systems offers multiple managed security services. Each service needs to be registered as an "asset" in CyberBridge for compliance tracking.

#### 1.1 Register Core Service - SecureNet Enterprise
- **Login:** Navigate to `http://38.126.154.32:5173`
- **Navigate to:** Assets → Add New Asset
- **Asset Details:**
  - **Asset Name:** "SecureNet Enterprise MSSP"
  - **Asset Type:** Software/Service
  - **Economic Operator:** Service Provider
  - **Status:** In Production
  - **Description:** "24/7 managed security monitoring, incident response, and threat intelligence service for enterprise networks"
  - **Version:** v2.5
  - **Criticality:** High (handles sensitive client security data)

#### 1.2 Register Supporting Service - Network Hardening
- **Navigate to:** Assets → Add New Asset
- **Asset Details:**
  - **Asset Name:** "Network Hardening Service"
  - **Asset Type:** Service
  - **Economic Operator:** Service Provider
  - **Status:** In Production
  - **Description:** "Firewall configuration, IDS/IPS deployment, network segmentation, and security architecture consulting"
  - **Criticality:** Medium

#### 1.3 Register Internal Platform - SOC Operations Platform
- **Navigate to:** Assets → Add New Asset
- **Asset Details:**
  - **Asset Name:** "SOC Operations Platform"
  - **Asset Type:** Software
  - **Economic Operator:** Distributor (using third-party SIEM + custom tooling)
  - **Status:** Testing (internal tool being enhanced)
  - **Description:** "Internal Security Operations Center platform combining SIEM, SOAR, and custom automation tools"
  - **Criticality:** Critical (core operational system)

**Key Points to Demonstrate:**
- Multiple asset types (services vs software)
- Different criticality levels
- Status tracking (Production vs Testing)
- Clear descriptions for audit purposes

---

### **Phase 2: Policy Registration** (20 minutes)

**Context:** ISO 27001 requires documented policies. Clone Systems needs to create, manage, and link policies to compliance objectives.

#### 2.1 Create Information Security Policy (Master Policy)
- **Navigate to:** Policies → Add New Policy
- **Policy Details:**
  - **Title:** "Information Security Policy"
  - **Status:** Approved
  - **Effective Date:** 2025-01-01
  - **Review Date:** 2026-01-01
  - **Policy Owner:** Chief Information Security Officer (CISO)
  - **Description:**
    ```
    This policy establishes Clone Systems' commitment to protecting information assets
    from all threats, whether internal or external, deliberate or accidental.
    It applies to all employees, contractors, and third parties accessing our systems
    or handling client data.

    Scope: All information systems, networks, and services operated by Clone Systems
    Compliance: ISO/IEC 27001:2022, SOC 2 Type II, GDPR
    ```
  - **Upload Policy Document:** `Information_Security_Policy_v1.0.pdf`

#### 2.2 Create Access Control Policy
- **Navigate to:** Policies → Add New Policy
- **Policy Details:**
  - **Title:** "Access Control & Identity Management Policy"
  - **Status:** Ready for Approval
  - **Description:**
    ```
    Defines requirements for user authentication, authorization, privilege management,
    and access reviews for all Clone Systems systems and client environments.

    Key Controls:
    - Multi-factor authentication (MFA) mandatory for all privileged access
    - Role-based access control (RBAC) implementation
    - Quarterly access reviews
    - Automated account deprovisioning
    - Principle of least privilege enforcement
    ```
  - **Upload Policy Document:** `Access_Control_Policy_v2.1.pdf`
  - **Link to Framework:** ISO/IEC 27001:2022
  - **Link to Objectives:**
    - A.5.15 Access control
    - A.5.16 Identity management
    - A.5.18 Access rights

#### 2.3 Create Incident Response Policy
- **Navigate to:** Policies → Add New Policy
- **Policy Details:**
  - **Title:** "Security Incident Response & Management Policy"
  - **Status:** Approved
  - **Description:**
    ```
    Establishes procedures for detecting, reporting, assessing, responding to,
    and recovering from information security incidents affecting Clone Systems
    or client environments.

    Incident Categories:
    - Critical (P1): Data breach, ransomware, system compromise
    - High (P2): Malware detection, unauthorized access attempts
    - Medium (P3): Policy violations, suspicious activity
    - Low (P4): User security awareness issues

    SLA Targets:
    - P1: 15-minute detection, 30-minute response initiation
    - P2: 1-hour detection, 4-hour response initiation
    - P3: 4-hour detection, 24-hour response initiation
    ```
  - **Upload Policy Document:** `Incident_Response_Policy_v1.5.pdf`

#### 2.4 Create Risk Management Policy
- **Navigate to:** Policies → Add New Policy
- **Policy Details:**
  - **Title:** "Enterprise Risk Management Policy"
  - **Status:** Approved
  - **Description:**
    ```
    Defines Clone Systems' approach to identifying, assessing, treating,
    and monitoring information security risks across all operations and services.

    Risk Assessment Methodology:
    - Likelihood: Rare, Unlikely, Possible, Likely, Almost Certain
    - Impact: Negligible, Minor, Moderate, Major, Catastrophic
    - Risk Appetite: Low tolerance for risks affecting client data confidentiality
    - Review Frequency: Quarterly for high risks, annually for medium/low risks
    ```
  - **Upload Policy Document:** `Risk_Management_Policy_v1.0.pdf`

#### 2.5 Create Business Continuity Policy
- **Navigate to:** Policies → Add New Policy
- **Policy Details:**
  - **Title:** "Business Continuity & Disaster Recovery Policy"
  - **Status:** Draft
  - **Description:**
    ```
    Ensures Clone Systems can maintain critical service delivery during disruptions
    and recover operations within defined timeframes.

    Key Requirements:
    - RTO (Recovery Time Objective): 4 hours for critical services
    - RPO (Recovery Point Objective): 1 hour for operational data
    - Annual DR testing with client notification
    - Alternate SOC facility maintained in different geographic region
    ```
  - **Upload Policy Document:** `Business_Continuity_Policy_DRAFT_v0.9.pdf`

**Key Points to Demonstrate:**
- Policy lifecycle management (Draft → Review → Ready for Approval → Approved)
- Policy ownership and accountability
- Version control and document management
- Linking policies to framework objectives
- Regular review schedules
- Different policy statuses in one organization

---

### **Phase 3: Risk Registration** (20 minutes)

**Context:** Clone Systems must identify risks to their MSSP operations, client data, and service delivery. These risks tie directly to ISO 27001 controls.

#### 3.1 Register Critical Risk - Insider Threat
- **Navigate to:** Risks → Add New Risk
- **Risk Details:**
  - **Risk Title:** "Malicious Insider Access to Client Environments"
  - **Category:** Human Resources Security
  - **Product Type:** Service (SecureNet Enterprise MSSP)
  - **Severity:** Critical
  - **Likelihood:** Unlikely
  - **Residual Risk:** Medium (after controls)
  - **Status:** Reduce
  - **Description:**
    ```
    SOC analysts and engineers have privileged access to client network monitoring
    and management systems. A malicious insider could abuse these privileges to
    exfiltrate client data, sabotage systems, or provide information to threat actors.
    ```
  - **Potential Impact:**
    ```
    - Data breach affecting multiple clients
    - Regulatory fines (GDPR, HIPAA, etc.)
    - Reputational damage and client contract terminations
    - Legal liability and lawsuits
    - Loss of ISO 27001 certification
    - Financial impact: $2M-$10M+
    ```
  - **Control Measures (Current):**
    ```
    - Background checks for all SOC personnel
    - MFA with hardware tokens for privileged access
    - Session recording and monitoring (Privileged Access Management)
    - Mandatory two-person approval for high-risk changes
    - Quarterly access reviews
    - Security awareness training (monthly)
    - Separation of duties between monitoring and configuration
    ```
  - **Control Measures (Additional):**
    ```
    - Implement User and Entity Behavior Analytics (UEBA)
    - Enhance insider threat detection with AI/ML anomaly detection
    - Rotate analysts across client accounts every 6 months
    - Implement "break-glass" emergency access with automated CISO notification
    ```

#### 3.2 Register High Risk - Ransomware Attack on SOC Infrastructure
- **Navigate to:** Risks → Add New Risk
- **Risk Details:**
  - **Risk Title:** "Ransomware Compromise of SOC Operations Platform"
  - **Category:** Malware & Cyber Attacks
  - **Product Type:** Software (SOC Operations Platform)
  - **Severity:** Critical
  - **Likelihood:** Possible
  - **Residual Risk:** Medium
  - **Status:** Reduce
  - **Description:**
    ```
    Ransomware attack targeting Clone Systems' internal SOC platform could encrypt
    SIEM data, security tools, and operational systems, crippling ability to monitor
    client environments and respond to incidents.
    ```
  - **Potential Impact:**
    ```
    - Complete loss of monitoring capabilities for all clients
    - Inability to detect or respond to client security incidents
    - Service Level Agreement (SLA) breaches
    - Client contract penalties and terminations
    - Recovery time: 24-72 hours
    - Financial impact: $500K-$3M (ransom, recovery, penalties)
    ```
  - **Control Measures (Current):**
    ```
    - Network segmentation (SOC network isolated from corporate)
    - Daily immutable backups with 90-day retention
    - Endpoint Detection and Response (EDR) on all SOC systems
    - Application whitelisting on critical servers
    - Email security gateway with advanced threat protection
    - Regular vulnerability scanning and patching (monthly)
    ```
  - **Control Measures (Additional):**
    ```
    - Implement offline backup copies (air-gapped)
    - Deploy deception technology (honeypots) in SOC network
    - Conduct annual ransomware tabletop exercises
    - Establish hot standby SOC environment in alternate data center
    ```

#### 3.3 Register Medium Risk - Third-Party SIEM Vendor Vulnerability
- **Navigate to:** Risks → Add New Risk
- **Risk Details:**
  - **Risk Title:** "Critical Vulnerability in Third-Party SIEM Platform"
  - **Category:** Supplier Relationships
  - **Product Type:** Software (SOC Operations Platform)
  - **Severity:** High
  - **Likelihood:** Likely (industry trend shows frequent SIEM vulnerabilities)
  - **Residual Risk:** Low
  - **Status:** Reduce
  - **Description:**
    ```
    Clone Systems relies on a commercial SIEM platform as the core of SOC operations.
    Zero-day or unpatched vulnerabilities in this platform could be exploited to
    compromise monitoring capabilities or gain access to aggregated client security data.
    ```
  - **Potential Impact:**
    ```
    - Unauthorized access to client security logs and event data
    - Potential data breach affecting multiple clients
    - SOC operations disruption during emergency patching
    - Regulatory compliance violations
    - Financial impact: $200K-$1M
    ```
  - **Control Measures (Current):**
    ```
    - Vendor security assessment during procurement
    - Subscription to vendor security advisories
    - Isolated SIEM deployment (no direct internet access)
    - 48-hour patching SLA for critical vulnerabilities
    - Annual third-party security audit of vendor
    ```
  - **Control Measures (Additional):**
    ```
    - Implement SIEM redundancy with secondary platform
    - Establish contractual SLAs with vendor for vulnerability disclosure
    - Deploy intrusion detection specific to SIEM infrastructure
    - Create emergency "fallback" monitoring procedures without SIEM
    ```

#### 3.4 Register Medium Risk - Client Credential Compromise
- **Navigate to:** Risks → Add New Risk
- **Risk Details:**
  - **Risk Title:** "Compromise of Client VPN/API Credentials"
  - **Category:** Access Control
  - **Product Type:** Service (SecureNet Enterprise MSSP)
  - **Severity:** High
  - **Likelihood:** Possible
  - **Residual Risk:** Low
  - **Status:** Reduce
  - **Description:**
    ```
    Clone Systems maintains VPN credentials and API keys to access client environments
    for monitoring and management. If these credentials are phished, stolen, or leaked,
    attackers could impersonate Clone Systems and gain unauthorized access to client networks.
    ```
  - **Potential Impact:**
    ```
    - Unauthorized access to client networks using legitimate credentials
    - Lateral movement within client environments
    - Data exfiltration or deployment of malware
    - Loss of client trust
    - Financial impact: $100K-$750K per affected client
    ```
  - **Control Measures (Current):**
    ```
    - Credentials stored in enterprise password vault (encrypted)
    - MFA required for password vault access
    - VPN certificates rotated every 90 days
    - API keys use short-lived tokens (4-hour expiry)
    - Failed authentication monitoring and alerting
    ```
  - **Control Measures (Additional):**
    ```
    - Implement certificate-based authentication for all client access
    - Deploy passwordless authentication where possible
    - Establish just-in-time (JIT) access provisioning
    - Implement geo-fencing for client access (SOC location only)
    ```

#### 3.5 Register Low Risk - Policy Non-Compliance by Staff
- **Navigate to:** Risks → Add New Risk
- **Risk Details:**
  - **Risk Title:** "Employee Non-Compliance with Security Policies"
  - **Category:** Organizational
  - **Product Type:** Service (General Operations)
  - **Severity:** Medium
  - **Likelihood:** Likely
  - **Residual Risk:** Low
  - **Status:** Accept
  - **Description:**
    ```
    Despite comprehensive security policies and training, employees may occasionally
    violate security procedures due to lack of awareness, convenience, or time pressure.

    Examples: Using unapproved tools, sharing passwords, bypassing approval processes
    ```
  - **Potential Impact:**
    ```
    - Minor security incidents requiring remediation
    - Potential audit findings during ISO 27001 assessments
    - Reduced effectiveness of security controls
    - Financial impact: $10K-$50K per incident
    ```
  - **Control Measures (Current):**
    ```
    - Mandatory security awareness training (quarterly)
    - Policy acknowledgment during onboarding
    - Regular internal audits and compliance checks
    - Phishing simulations (monthly)
    - HR disciplinary process for violations
    ```

**Key Points to Demonstrate:**
- Risk severity matrix (Likelihood × Impact)
- Linking risks to specific products/services
- Current vs. additional control measures
- Risk treatment strategies (Reduce, Accept, Transfer, Avoid)
- Residual risk after controls applied
- Financial impact quantification
- Risk categories aligned with ISO 27001

---

### **Phase 3.5: Control Registration** (10 minutes)

**Context:** Clone Systems needs to document the security controls that mitigate identified risks and support ISO 27001 compliance objectives.

#### 3.6 Register Control - Multi-Factor Authentication
- **Navigate to:** Controls → Add New Control
- **Control Details:**
  - **Control Name:** "Multi-Factor Authentication (MFA) for Privileged Access"
  - **Control Set:** Access Control
  - **Status:** Implemented
  - **Description:** "Hardware token or TOTP-based MFA mandatory for all administrative and privileged access to SOC systems and client environments."
  - **Link to Risk:** Select "Malicious Insider Access to Client Environments"
  - **Link to Policy:** Select "Access Control & Identity Management Policy"
  - **Link to Objective:** A.5.17 - Authentication Information

**Key Points to Demonstrate:**
- Controls linked directly to risks they mitigate
- Controls mapped to policies and framework objectives
- Complete traceability: Risk → Control → Policy → Objective

---

### **Phase 4: Compliance Assessment** (25 minutes)

**Context:** Clone Systems conducts an ISO 27001 internal audit to prepare for certification. The assessment covers all Annex A controls.

#### 4.1 Create ISO 27001 Assessment
- **Navigate to:** Frameworks → Verify "ISO/IEC 27001:2022" is seeded
  - If not available: Frameworks → Seed Framework → Select ISO 27001
- **Navigate to:** Assessments → New Assessment
- **Assessment Details:**
  - **Framework:** ISO/IEC 27001:2022
  - **Assessment Type:** Internal Audit
  - **Product:** SecureNet Enterprise MSSP
  - **Assessor:** [Current User]
  - **Start Date:** 2025-10-01
  - **Target Completion Date:** 2025-12-15
  - **Description:** "Pre-certification internal audit to verify readiness for ISO 27001:2022 certification"

#### 4.2 Complete Assessment Questions - Sample Responses

**Navigate to:** Assessments → Select created assessment → Begin Assessment

**Domain A.5: Organizational Controls**

**Question 1: Information Security Policy (A.5.1)**
- **Question:** "Are information security policies documented, approved by management, communicated to relevant personnel, and reviewed at planned intervals?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Information_Security_Policy_v1.0.pdf`
- **Evidence Description:** "Approved by Board of Directors on 2025-01-01. Policy distributed to all staff via email and published on internal portal. Annual policy review scheduled."
- **Link to Policy:** Select "Information Security Policy"
- **Notes:** "Policy covers all ISO 27001 requirements including scope, objectives, compliance obligations, and management commitment."

**Question 2: Allocation of Information Security Responsibilities (A.5.2)**
- **Question:** "Are information security roles and responsibilities clearly defined, documented, and assigned to competent personnel?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Organizational_Chart_Security_Roles.pdf`
- **Evidence Description:**
  ```
  - CISO: Overall ISMS responsibility and strategic direction
  - SOC Manager: Operational security and incident response
  - GRC Manager: Compliance, risk management, audit coordination
  - IT Manager: Infrastructure security, access control, backups
  - HR Manager: Personnel security, training, background checks
  ```
- **Notes:** "Job descriptions include security responsibilities. Annual performance reviews include security KPIs."

**Question 3: Segregation of Duties (A.5.3)**
- **Question:** "Are conflicting duties identified and appropriately segregated within critical business processes?"
- **Answer:** "No"
- **Compliance Status:** Partially Compliant
- **Evidence:** Upload `Segregation_of_Duties_Matrix.xlsx`
- **Evidence Description:** "SoD matrix implemented for critical functions. However, small team size requires some overlap (e.g., SOC Manager has both monitoring and approval authority). Compensating controls are in place."
- **Link to Risk:** Select "Malicious Insider Access to Client Environments"
- **Corrective Action Required:**
  ```
  1. Implement automated approval workflows for high-risk changes (target: Q4 2025)
  2. Hire additional SOC supervisor to separate monitoring from approval authority
  3. Document compensating controls where SoD not possible due to team size
  ```
- **Notes:** "Acknowledged gap. Compensating controls include session recording, dual approval for critical changes, and quarterly management reviews."

**Domain A.5.15-A.5.18: Access Control**

**Question 4: Access Control Policy (A.5.15)**
- **Question:** "Are access control rules established based on business requirements and information security risk assessments?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Access_Control_Policy_v2.1.pdf`
- **Evidence Description:** "Policy last reviewed 2025-09-15. Covers authentication, authorization, privilege management, access reviews."
- **Link to Policy:** Select "Access Control & Identity Management Policy"
- **Notes:** "Policy approved by CISO. Next review scheduled 2026-09-15."

**Question 5: Identity Management (A.5.16)**
- **Question:** "Is there a documented identity management process covering identity creation, maintenance, and removal throughout the complete lifecycle?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Identity_Lifecycle_Procedures.pdf`
- **Evidence Description:**
  ```
  - Onboarding: HR ticket triggers IT account creation within 24 hours
  - Role changes: Manager approval required, access rights updated within 48 hours
  - Offboarding: Immediate account disable upon HR notification, 30-day retention before deletion
  - Automated reports: Weekly list of new accounts, disabled accounts, and access changes
  ```
- **Notes:** "Process integrated with HR system. Quarterly access reviews verify no orphaned accounts."

**Question 6: Authentication Information (A.5.17)**
- **Question:** "Is authentication information managed through controlled processes with clear guidance provided to users?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Password_Standards_and_MFA_Configuration.pdf`
- **Evidence Description:**
  ```
  Password Requirements:
  - Minimum 14 characters
  - Complexity: uppercase, lowercase, numbers, special characters
  - 90-day expiration (180 days with MFA)
  - Password history: 12 previous passwords blocked

  MFA Implementation:
  - Mandatory for all privileged access (TOTP or hardware token)
  - Enforced for VPN and remote access
  - Backup codes generated and securely stored
  ```
- **Notes:** "MFA adoption: 100% for privileged accounts, 87% for standard users (voluntary). Target: 100% by Q1 2026."

**Question 7: Access Rights (A.5.18)**
- **Question:** "Are access rights regularly reviewed, updated, and removed in accordance with established access control policies?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Access_Rights_Management_Procedure.pdf` and `Q3_2025_Access_Review_Report.xlsx`
- **Evidence Description:** "Quarterly access reviews completed. Last review (Q3 2025) identified 7 unnecessary access grants, all remediated within 2 weeks."
- **Notes:** "Role-based access control (RBAC) implemented. Principle of least privilege enforced."

**Domain A.6: People Controls**

**Question 8: Screening (A.6.1)**
- **Question:** "Are background verification checks conducted proportionally based on role requirements, information classification, and risk assessment?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Background_Check_Policy.pdf`
- **Evidence Description:**
  ```
  All employees undergo:
  - Criminal background check (federal and state)
  - Employment verification (previous 3 employers)
  - Education verification
  - Credit check (for positions with financial access)
  - Enhanced screening for SOC personnel (includes social media review)

  Third-party vendor: [Redacted Background Check Company]
  Refresh: Every 3 years for existing employees
  ```
- **Notes:** "100% completion rate. HR maintains signed acknowledgment forms."

**Question 9: Terms and Conditions of Employment (A.6.2)**
- **Question:** "Do employment contracts clearly define both personnel and organizational responsibilities for information security?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Employment_Agreement_Security_Clauses.pdf` and `Confidentiality_Agreement_Template.pdf`
- **Evidence Description:** "All employment contracts include security and confidentiality clauses. Separate NDAs signed for client data access."
- **Notes:** "Legal review completed 2024. Contracts updated to reflect ISO 27001 requirements."

**Question 10: Information Security Awareness, Education, and Training (A.6.3)**
- **Question:** "Is information security awareness, education, and training provided systematically to all personnel based on their roles and responsibilities?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Security_Training_Program_Overview.pdf` and `2025_Training_Completion_Report.xlsx`
- **Evidence Description:**
  ```
  Training Program:
  - New Hire: Security awareness training (mandatory, within 7 days)
  - Quarterly: Security updates and policy changes (1 hour)
  - Role-specific: SOC analyst training (40 hours annually), secure coding, incident response
  - Phishing simulations: Monthly tests with immediate feedback

  2025 Completion Rates:
  - General awareness: 98% (2 new hires pending)
  - Phishing simulation click rate: 4% (down from 12% in 2024)
  ```
- **Notes:** "LMS tracks completion. Non-completion escalated to HR and management."

**Domain A.7: Physical and Environmental Security**

**Question 11: Physical Security Perimeters (A.7.1)**
- **Question:** "Are physical security perimeters clearly defined and implemented around areas containing information and information processing facilities?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `SOC_Physical_Security_Plan.pdf` and `Access_Log_Sample.xlsx`
- **Evidence Description:**
  ```
  SOC Facility Security:
  - Dedicated office space with card access control
  - 24/7 security guard (building security)
  - Badge access required (employees only)
  - Visitor log maintained (escort required)
  - CCTV monitoring (90-day retention)
  - Biometric access for server room
  ```
- **Notes:** "Co-located in secure office building. Annual security audit by building management."

**Question 12: Physical Entry Controls (A.7.2)**
- **Question:** "Are appropriate entry controls implemented to ensure only authorized personnel can access secure areas?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Access_Control_System_Configuration.pdf`
- **Evidence Description:** "Electronic badge system logs all entry/exit events. Quarterly access list reviews. Terminated employees removed same day."
- **Notes:** "Shared building access system. Clone Systems has separate card reader for SOC area."

**Domain A.8: Technological Controls**

**Question 13: User Endpoint Devices (A.8.1)**
- **Question:** "Are user endpoint devices managed with security controls appropriate to the information they access and process?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Endpoint_Security_Standards.pdf`
- **Evidence Description:**
  ```
  Endpoint Protection:
  - EDR deployed on all workstations and laptops (100% coverage)
  - Full disk encryption (BitLocker/FileVault) mandatory
  - Automatic screen lock after 5 minutes inactivity
  - Company-issued devices only (BYOD prohibited for SOC staff)
  - Mobile device management (MDM) for tablets/phones
  - USB ports disabled on SOC workstations
  ```
- **Notes:** "Monthly compliance scans verify endpoint configuration. Non-compliant devices quarantined until remediated."

**Question 14: Privileged Access Rights (A.8.2)**
- **Question:** "Are privileged access rights allocated, managed, and monitored according to the principle of least privilege?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Privileged_Access_Management_Procedure.pdf` and `PAM_Audit_Report_Q3_2025.pdf`
- **Evidence Description:**
  ```
  PAM Implementation:
  - Dedicated privileged access workstations (jump servers)
  - Session recording for all privileged access (180-day retention)
  - Just-in-time (JIT) access for administrative tasks
  - No shared privileged accounts
  - Emergency "break glass" accounts with automatic alerts to CISO
  - Quarterly privileged access reviews
  ```
- **Notes:** "PAM solution deployed 2024-Q2. 100% privileged access now managed through PAM."

**Question 15: Information Access Restriction (A.8.3)**
- **Question:** "Is access to information and application systems restricted according to documented access control policies?"
- **Answer:** "No"
- **Compliance Status:** Partially Compliant
- **Evidence:** Upload `Data_Classification_Policy_DRAFT.pdf`
- **Evidence Description:** "Data classification policy drafted but not yet fully implemented. Client data stored in segregated environments with access controls, but internal data not yet classified. Interim controls are operational."
- **Link to Policy:** Select "Information Security Policy" (will be updated to reference classification policy)
- **Corrective Action Required:**
  ```
  1. Finalize data classification policy (target: November 2025)
  2. Classify all existing data assets (target: Q1 2026)
  3. Implement DLP controls based on classification (target: Q2 2026)
  4. Train staff on data handling procedures
  ```
- **Notes:** "Interim controls in place: client data isolated, network segmentation enforced. Formal classification needed for ISO 27001 certification."

**Question 16: Cryptography (A.8.24)**
- **Question:** "Are cryptographic controls implemented with appropriate key management based on information protection requirements?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Cryptography_Standards.pdf`
- **Evidence Description:**
  ```
  Encryption Standards:
  - Data at rest: AES-256 encryption (databases, backups, file storage)
  - Data in transit: TLS 1.3 minimum (TLS 1.2 deprecated)
  - VPN: IPsec with AES-256
  - Client data: Encrypted with client-specific keys (key escrow with client)

  Key Management:
  - Hardware Security Module (HSM) for key storage
  - Annual key rotation for non-ephemeral keys
  - Access to key management restricted to 3 authorized personnel
  - Key backup stored in secure offsite location
  ```
- **Notes:** "Cryptographic standards reviewed annually. Next review: January 2026."

**Domain A.8.8-A.8.16: Incident Management**

**Question 17: Management of Technical Vulnerabilities (A.8.8)**
- **Question:** "Are technical vulnerabilities systematically identified, assessed, and remediated within appropriate timeframes?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Vulnerability_Management_Procedure.pdf` and `October_2025_Patch_Report.pdf`
- **Evidence Description:**
  ```
  Vulnerability Management Process:
  - Weekly vulnerability scans (internal network)
  - Monthly external penetration testing
  - Subscribed to vendor security advisories and CVE feeds
  - Patch Management SLAs:
    * Critical: 48 hours
    * High: 7 days
    * Medium: 30 days
    * Low: 90 days or next maintenance window
  - October 2025 metrics: 97% critical patches applied within SLA
  ```
- **Notes:** "3% SLA miss was due to vendor delay in patch availability. Compensating controls applied."

**Question 18: Information Security Event Reporting (A.6.8)**
- **Question:** "Are clear reporting channels established for personnel to report observed or suspected information security events?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Incident_Reporting_Procedure.pdf` and `Security_Incident_Report_Sample_REDACTED.pdf`
- **Evidence Description:**
  ```
  Reporting Mechanisms:
  - 24/7 SOC hotline for urgent incidents
  - Internal ticketing system for non-urgent events
  - Dedicated email: security@clone-systems.com
  - Monthly "Lunch and Learn" sessions encourage reporting culture

  Reporting Requirements:
  - All employees trained to report suspicious activity
  - No-blame policy to encourage reporting
  - Incidents categorized by severity (P1-P4)
  - Management notification for P1/P2 within 30 minutes
  ```
- **Link to Policy:** Select "Security Incident Response & Management Policy"
- **Notes:** "2025 YTD: 47 events reported, 8 escalated to incidents. Average reporting time: 12 minutes."

**Question 19: Response to Information Security Incidents (A.6.5)**
- **Question:** "Are information security incidents responded to according to documented procedures with appropriate escalation and communication?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Incident_Response_Playbooks.pdf` and `2025_Incident_Response_Metrics.xlsx`
- **Evidence Description:**
  ```
  Incident Response Capabilities:
  - Documented playbooks for common incident types
  - Incident response team: 5 trained personnel (24/7 on-call rotation)
  - Quarterly tabletop exercises
  - Annual live-fire cyber range training
  - Retainer agreement with forensics firm for P1 incidents

  2025 Incident Response Performance:
  - P1 incidents: 2 (mean time to contain: 3.5 hours, target: 4 hours) ✓
  - P2 incidents: 6 (mean time to contain: 9 hours, target: 12 hours) ✓
  - Client impact: Zero client-facing incidents
  ```
- **Link to Policy:** Select "Security Incident Response & Management Policy"
- **Notes:** "Post-incident reviews conducted for all P1/P2 incidents. Lessons learned documented and training updated."

**Domain A.5.7: Threat Intelligence**

**Question 20: Threat Intelligence (A.5.7)**
- **Question:** "Is threat intelligence systematically collected, analyzed, and used to enhance information security measures?"
- **Answer:** "Yes"
- **Compliance Status:** Compliant
- **Evidence:** Upload `Threat_Intelligence_Program_Overview.pdf`
- **Evidence Description:**
  ```
  Threat Intelligence Sources:
  - Commercial threat feed subscriptions (2 providers)
  - Open-source intelligence (OSINT) monitoring
  - Information Sharing and Analysis Center (ISAC) membership
  - Dark web monitoring service
  - Vendor threat bulletins

  Intelligence Analysis:
  - Daily threat briefings for SOC team
  - Weekly threat reports distributed to client stakeholders
  - Monthly executive threat briefings
  - Threat intelligence integrated into SIEM for automated detection
  ```
- **Notes:** "Threat intel program matured significantly in 2025. Contributed to early detection of 3 emerging threats affecting clients."

#### 4.3 Assessment Summary Actions
- **Navigate to:** Assessment → View Progress Dashboard
- **Demonstrate:**
  - Overall compliance percentage calculation
  - Breakdown by compliance status (Compliant, Partially Compliant, Not Compliant, Not Assessed)
  - List of items requiring corrective action
  - Evidence upload summary
  - Assessment timeline and progress tracking

**Expected Results:**
- 85% Compliant
- 10% Partially Compliant
- 5% Not Assessed
- Key gaps identified: Data classification, segregation of duties (resource constraints)

**Key Points to Demonstrate:**
- Variety of compliance statuses (realistic assessment)
- Evidence documentation for each control
- Linking answers to policies and risks
- Identifying gaps and corrective actions
- Compliance tracking across domains
- Assessment progress monitoring

---

### **Phase 5: Objectives Checklist & Gap Analysis** (15 minutes)

**Context:** After completing the assessment, Clone Systems reviews objectives to track certification readiness and identify remaining gaps.

#### 5.1 Review Objectives Dashboard
- **Navigate to:** Objectives → Select Framework "ISO/IEC 27001:2022"
- **Demonstrate:**
  - List of all Annex A controls organized by domain
  - Compliance status color coding:
    - ✅ **Compliant** (Green): Controls fully implemented
    - ⚠️ **Partially Compliant** (Yellow): Controls implemented but with gaps
    - ❌ **Not Compliant** (Red): Controls not implemented
    - ⏳ **In Review** (Blue): Controls under assessment
    - 🔘 **Not Assessed** (Grey): Controls not yet evaluated
    - ➖ **Not Applicable** (Grey striped): Controls not relevant

#### 5.2 Filter Objectives Requiring Action
- **Action:** Apply filter → Show only "Partially Compliant" and "Not Compliant"
- **Expected Results:**
  - **A.5.3 - Segregation of Duties:** Partially Compliant
    - Gap: SOC Manager has both monitoring and approval authority
    - Linked Assessment Answer: References SoD matrix and compensating controls
    - Corrective Action: Hire SOC supervisor, implement workflow automation
    - Target Date: Q4 2025
    - Owner: CISO

  - **A.8.3 - Information Access Restriction:** Partially Compliant
    - Gap: Data classification policy not yet implemented
    - Linked Assessment Answer: References draft policy
    - Corrective Action: Finalize policy, classify assets, implement DLP
    - Target Date: Q2 2026
    - Owner: GRC Manager

#### 5.3 Link Objectives to Policies
- **Navigate to:** Objectives → Select "A.5.15 - Access Control"
- **Demonstrate:**
  - View linked policies:
    - Information Security Policy
    - Access Control & Identity Management Policy
  - Show how policy implementation supports objective compliance
  - Display policy document directly from objective view

#### 5.4 Link Objectives to Risks
- **Navigate to:** Objectives → Select "A.5.18 - Access Rights"
- **Demonstrate:**
  - View linked risks:
    - "Malicious Insider Access to Client Environments"
    - "Compromise of Client VPN/API Credentials"
  - Show how objective compliance mitigates identified risks
  - Display risk treatment plan from objective view

#### 5.5 Generate Gap Analysis Report
- **Navigate to:** Objectives → Export → Generate Gap Analysis Report
- **Report Contents:**
  - Executive Summary:
    - 85% of objectives compliant
    - 10% partially compliant (2 objectives)
    - 5% not assessed (1 objective - supply chain security, pending vendor audit)
    - 0% not compliant
  - Gap Summary Table:
    - Objective ID, Title, Current Status, Gap Description, Corrective Action, Owner, Target Date
  - Risk Implications:
    - Gaps that increase residual risk exposure
    - Prioritization based on risk severity
  - Certification Readiness:
    - Assessment: "Ready for certification audit with minor findings expected"
    - Recommendations: Complete data classification implementation, finalize SoD documentation
  - Action Plan Timeline:
    - Visual Gantt chart of corrective actions
    - Critical path items highlighted

**Key Points to Demonstrate:**
- Visual compliance tracking across all objectives
- Easy identification of gaps requiring remediation
- Direct link between objectives, policies, and risks (traceability)
- Prioritization based on compliance impact
- Executive-level reporting for management visibility
- Actionable insights for certification preparation

---

### **Phase 5.5: Compliance Chain Visualization** (5 minutes)

**Context:** Show how all compliance entities are interconnected.

#### 5.6 View Compliance Chain Map
- **Navigate to:** Compliance Chain → Map
- **Demonstrate:**
  - Visual relationship map showing all connections
  - Assets → Risks → Controls → Policies → Objectives
  - Click on any entity to see its connections
  - Identify gaps where entities are not linked

#### 5.7 View Compliance Chain Links
- **Navigate to:** Compliance Chain → All Links
- **Demonstrate:**
  - Tabular view of all compliance relationships
  - Filter by entity type
  - Create new links between entities

---

## 🎯 Pilot Success Criteria

By the end of this 60-90 minute pilot, Clone Systems will have demonstrated:

1. ✅ **Asset Registration:** 3 assets/services registered with appropriate metadata
2. ✅ **Policy Management:** 5 key security policies created, documented, and linked to framework objectives
3. ✅ **Risk Assessment:** 5 risks identified, assessed, and documented with control measures
4. ✅ **Compliance Assessment:** 20 ISO 27001 controls assessed with evidence and compliance status
5. ✅ **Objectives Tracking:** Gap analysis completed, corrective actions identified, certification readiness evaluated
6. ✅ **Control Registration:** Security controls documented and linked to risks and objectives
7. ✅ **Compliance Chain:** Full traceability demonstrated between all compliance entities

---

## 🚀 Pilot Outcomes & Business Value

### Immediate Benefits Demonstrated

1. **Centralized Compliance Management**
   - Single platform for all ISO 27001 certification activities
   - Real-time visibility into compliance status
   - Eliminates spreadsheet chaos and document version control issues

2. **Risk-Informed Compliance**
   - Direct linkage between risks and compliance controls
   - Demonstrates ROI of security investments
   - Prioritizes remediation based on risk severity

3. **Audit Readiness**
   - Complete evidence documentation for every control
   - Audit trail of all compliance activities
   - Professional reports for external auditors
   - Reduces certification audit time by 40-50%

4. **Policy Lifecycle Management**
   - Version control and approval workflows
   - Automated review reminders
   - Clear ownership and accountability
   - Ensures policies remain current and effective

5. **Traceability & Accountability**
   - Every objective linked to policies and risks
   - Every assessment answer linked to evidence
   - Clear ownership for corrective actions
   - Management visibility into compliance progress

### Long-Term Strategic Value

1. **Framework Flexibility:** ISO 27001 today, SOC 2, NIST CSF, or CRA tomorrow
2. **Client Differentiation:** Professional compliance reporting increases client confidence
3. **Operational Efficiency:** 60% reduction in compliance management overhead
4. **Continuous Improvement:** Ongoing risk and compliance monitoring
5. **Scalability:** Supports growth without proportional compliance team expansion

---

## 📊 Key Metrics to Highlight

- **Time Savings:** Reduced compliance assessment time from 6 weeks to 2 weeks
- **Evidence Management:** 100% traceability for all compliance controls
- **Risk Visibility:** Real-time dashboard of top risks and mitigation status
- **Certification Readiness:** Achieved 85% compliance in 90-day pilot
- **Audit Efficiency:** Estimated 50% reduction in certification audit duration
- **Cost Avoidance:** Prevented potential non-compliance penalties and client contract loss

---

## 🎬 Presentation Tips

### Opening Statement
"Clone Systems provides network security services to enterprise clients. To differentiate in a competitive market and meet client requirements, we need ISO 27001 certification. Traditional compliance management is time-consuming, error-prone, and doesn't provide real-time visibility. CyberBridge transforms how we manage compliance—from product registration to policy management, risk assessment, compliance evaluation, and certification readiness—all in one platform."

### Throughout the Demo
- Emphasize **practical workflows** that security teams actually use
- Highlight **time savings** at each step (e.g., "This risk assessment that used to take 2 hours now takes 15 minutes")
- Show **traceability** between risks, policies, and compliance objectives
- Demonstrate **audit readiness** with comprehensive evidence documentation

### Closing Statement
"In 90 minutes, we've registered our services, documented our policies, assessed our risks, evaluated 20 ISO 27001 controls, and identified our path to certification. With CyberBridge, Clone Systems has a clear, data-driven view of compliance readiness and a structured approach to achieving ISO 27001 certification. This isn't just compliance management—it's strategic risk management that supports business growth."

---

## ⚠️ Common Questions & Answers

**Q: Can we import our existing policies and risk register?**
- A: Yes, policies can be uploaded as PDF/Word documents and linked to framework objectives. Risks can be bulk-imported via Excel or API integration.

**Q: How does this scale as we add more clients or services?**
- A: Each product/service can have separate assessments. You can clone framework assessments for recurring evaluations. Multi-tenant architecture supports unlimited products.

**Q: What if ISO 27001 requirements change?**
- A: Framework versioning allows you to migrate to updated versions while preserving historical assessment data. You can run side-by-side assessments during transition periods.

**Q: Can external auditors access the platform?**
- A: Yes, CyberBridge has a dedicated external auditor portal with magic link authentication, time-bound access, role-based permissions, audit comments, findings tracking, and sign-off workflows.

**Q: How do we track corrective actions?**
- A: Each "Partially Compliant" or "Not Compliant" objective can have assigned corrective actions with owners, due dates, and progress tracking. Dashboard shows overdue items.

**Q: Can we use this for client assessments?**
- A: Absolutely. Create separate assessments for each client, track their compliance maturity, and generate client-specific reports. Great for QBR (Quarterly Business Review) presentations.

---

**End of Clone Systems Pilot Use Case Guide** 🎉
