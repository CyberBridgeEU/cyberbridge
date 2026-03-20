# User Flow Examples

This guide provides complete, step-by-step walkthroughs of the CyberBridge compliance workflow using real-world examples. Each example follows the recommended flow from the **User Guide** (available in the Dashboard Quick Actions):

> **Framework > Assets > Risks > Controls > Policies > Assessments > Objectives**

All examples use the following scenario:

- **Company**: Clone Systems, Inc. (Network Security & Cybersecurity Solutions Provider)
- **Product**: NextGen SIEM Pro v3.0.0 (Security Information and Event Management Platform)
- **Framework**: ISO/IEC 27001:2022
- **Goal**: Achieve ISO 27001 certification readiness and EU Cyber Resilience Act compliance

---

## Step 1: Seed a Framework

> *"Navigate to Framework Management and seed a compliance framework. This populates the system with the relevant chapters, objectives, and assessment questions for your chosen standard."*

### What You Need

- Organization Admin or Super Admin role
- Access to Framework Configuration

### Walkthrough

**Navigate to**: Frameworks > Configuration > Manage Frameworks

1. Click **"Add from Template"**
2. Select the template: **ISO/IEC 27001:2022**
3. Click **"Create Framework"**

### Result

The system creates the complete framework with:

| Component | Count |
|-----------|-------|
| Chapters | 14 (Clauses 4-10 + Annex A.5 through A.8) |
| Objectives | 93 Annex A control objectives |
| Questions | Full question set for conformity and audit assessments |

### Real Example

After seeding ISO 27001, you will see chapters like:

| Chapter | Title | Objectives |
|---------|-------|------------|
| A.5 | Organizational Controls | 37 objectives |
| A.6 | People Controls | 8 objectives |
| A.7 | Physical Controls | 14 objectives |
| A.8 | Technological Controls | 34 objectives |

> **Tip**: You can seed multiple frameworks (CRA, NIS2, NIST CSF) and manage them independently. Use the Correlations feature to link related questions across frameworks.

---

## Step 2: Register Your Assets

> *"Go to Product Registration to add the assets, products, or systems that fall under your compliance scope. Fill in the product details, type, economic operator, and criticality level."*

### What You Need

- The asset/product details you want to register
- Knowledge of the product's CRA classification (if applicable)

### Walkthrough

**Navigate to**: Assets / Products > Manage Assets

Fill in the registration form:

| Field | Example Value |
|-------|---------------|
| **Asset Name** | NextGen SIEM Pro |
| **Version** | 3.0.0 |
| **Justification** | Next-generation SIEM platform with AI-powered threat detection requiring ISO 27001 compliance for enterprise market positioning and EU Cyber Resilience Act conformity |
| **License** | Commercial - Proprietary with Enterprise Licensing |
| **Description** | Advanced Security Information and Event Management platform featuring real-time threat detection, AI/ML-powered behavioral analytics, automated incident response, compliance reporting, and integration with 500+ security tools. Designed for SOC operations and enterprise security management. |
| **SBOM** | ElasticSearch v8.11.1, Apache Kafka v3.6.0, TensorFlow v2.15.0, PostgreSQL v16.1, Redis v7.2.3, Python 3.11.7, React v18.2.0 |
| **Asset Type** | Software |
| **Economic Operator** | Manufacturer |
| **Status** | Live |
| **Criticality** | ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I |

After selecting the Criticality level, choose the specific option:
- **"Security information and event management (SIEM) systems"**

Click **Save**.

### Result

- The asset appears in the asset table with all details
- It becomes available as a scope entity when creating assessments
- It can be linked to risks, incidents, and compliance chain entities

### Dropdown Reference

| Field | Available Options |
|-------|-------------------|
| Asset Type | Hardware, Software |
| Economic Operator | Manufacturer, Importer, Distributor |
| Status | Live, Testing |
| Criticality | ANNEX III - Class I, ANNEX III - Class II, ANNEX IV |

> **Tip**: Assets are the starting point of the compliance chain. Risks, controls, and policies all trace back to what you are protecting.

---

## Step 3: Identify and Assess Risks

> *"Navigate to Risk Registration to document potential risks. For each risk, define its severity, likelihood, status, and associate it with relevant assets."*

### What You Need

- Identified threats and vulnerabilities for your assets
- Understanding of risk severity levels
- Current and planned control measures

### Walkthrough - Risk 1: Unauthorized Access

**Navigate to**: Risks > Risk Register

Fill in the risk form:

| Field | Example Value |
|-------|---------------|
| **Product Type** | Software |
| **Risk Category** | Access Control |
| **Status** | Reduce |
| **Likelihood** | Medium |
| **Severity** | Critical |
| **Residual Risk** | Medium |

**Risk Description**:
```
Unauthorized Access to SIEM Platform and Customer Data

The NextGen SIEM Pro platform collects, stores, and analyzes sensitive
security logs and event data from customer environments. If administrative
credentials are compromised through phishing, credential stuffing, or
insider threats, unauthorized access could lead to data breaches exposing
customer security information and intellectual property.

Attack Vectors:
- Phishing attacks targeting SIEM administrators
- Credential stuffing attacks against admin portals
- SQL injection or authentication bypass vulnerabilities
- Malicious insider with administrative privileges
- Compromised API keys or service accounts
- Stolen session tokens or authentication cookies
```

**Potential Impact**:
```
- Exposure of customer security logs and threat intelligence data
- Unauthorized access to customer network topology and security posture
- Intellectual property theft (proprietary detection algorithms and rules)
- Regulatory fines under GDPR, CCPA, and industry-specific regulations
- Customer contract terminations and mass customer churn
- Loss of ISO 27001 and SOC 2 certifications
- Product ban or restrictions under EU Cyber Resilience Act

Financial Impact: $2M - $10M+
Business Impact: Potential 30-50% customer churn
```

**Control Measures**:
```
Current Controls:
- Multi-factor authentication (MFA) with TOTP or hardware tokens mandatory
- Role-based access control (RBAC) with principle of least privilege
- Automated session timeout after 15 minutes of inactivity
- Administrative action logging and audit trails
- IP whitelisting for administrative access
- Database encryption at rest (AES-256) and in transit (TLS 1.3)
- Regular penetration testing (quarterly) and vulnerability assessments

Planned Enhancements:
- Just-In-Time (JIT) privileged access provisioning (Q4 2025)
- User and Entity Behavior Analytics (UEBA) for anomaly detection
- Certificate-based authentication for API access (Q1 2026)
```

Click **Save Risk**.

### Walkthrough - Risk 2: Supply Chain Compromise

**Navigate to**: Risks > Risk Register (add another risk)

| Field | Example Value |
|-------|---------------|
| **Product Type** | Software |
| **Risk Category** | Supply Chain |
| **Status** | Reduce |
| **Likelihood** | High |
| **Severity** | Critical |
| **Residual Risk** | Medium |

**Risk Description**:
```
Supply Chain Attack via Compromised Third-Party Dependencies

NextGen SIEM Pro relies on 30+ open-source and commercial third-party
dependencies (ElasticSearch, Kafka, TensorFlow, PostgreSQL, Redis, etc.).
A supply chain attack compromising any of these dependencies could
introduce backdoors, vulnerabilities, or malicious code.

Attack Vectors:
- Compromised upstream dependency packages (npm, PyPI, Maven)
- Typosquatting attacks with malicious packages
- Dependency confusion attacks
- Compromised maintainer accounts in package registries
```

**Potential Impact**:
```
- Backdoor access to all customer SIEM deployments
- Platform compromise affecting thousands of customers simultaneously
- Regulatory violations under EU CRA (failure to secure supply chain)
- Class-action lawsuits and regulatory fines

Financial Impact: $10M - $50M+
Regulatory Impact: EU CRA non-compliance, potential market ban
```

**Control Measures**:
```
Current Controls:
- Software Bill of Materials (SBOM) maintained for all dependencies
- Dependency vulnerability scanning in CI/CD (Snyk, Dependabot)
- Package integrity verification using checksums and signatures
- Dependency pinning with lock files
- Private package registry mirror with vetted dependencies only

Planned Enhancements:
- SLSA Level 3 implementation (Q1 2026)
- Sigstore for cryptographic signing of build artifacts
- Air-gapped build environment for production releases
```

Click **Save Risk**.

### Walkthrough - Risk 3: EU CRA Non-Compliance

| Field | Example Value |
|-------|---------------|
| **Product Type** | Software |
| **Risk Category** | Legal & Compliance |
| **Status** | Reduce |
| **Likelihood** | Medium |
| **Severity** | High |
| **Residual Risk** | Low |

**Risk Description**:
```
EU Cyber Resilience Act Non-Compliance - Vulnerability Disclosure Failures

The EU CRA (Article 11) requires manufacturers of Class I products to
establish and maintain a coordinated vulnerability disclosure policy.
Failure to comply results in fines up to EUR 15M or 2.5% of turnover.

Compliance Gaps:
- Vulnerability disclosure policy not prominently published
- No dedicated 24/7 security contact point
- Response time SLAs not documented
- SBOM not published to customers
- ENISA incident reporting not implemented
```

**Potential Impact**:
```
- EU CRA administrative fines: EUR 15M or 2.5% of global turnover
- Market access restrictions in EU member states
- Inability to CE mark products, blocking EU sales

Financial Impact: EUR 15M+ (fines) + EUR 5M-20M (revenue loss)
```

Click **Save Risk**.

### Risk Category Reference

| Product Type | Common Categories |
|-------------|-------------------|
| **Software** | Vulnerabilities, Access Control, Communication Security, Supply Chain, Update Mechanism, Monitoring & Logging, Security-by-Design, User Misuse, Legal & Compliance, Dependency Risk |
| **Hardware** | Firmware Vulnerabilities, Physical Security, Communication Interfaces, Supply Chain Integrity, Monitoring & Telemetry, Design Flaws, Component Dependency |

| Field | Available Options |
|-------|-------------------|
| Status | Reduce, Avoid, Transfer, Share, Accept, Remediated |
| Likelihood / Severity / Residual Risk | Low, Medium, High, Critical |

> **Tip**: Each risk should be tied to an asset. This connection drives which controls and policies you need. Use the Risk Assessment page (Risks > Risk Assessment) to analyze risk distribution.

---

## Step 4: Register Controls

> *"Go to Control Register to document the technical and organisational measures that mitigate your identified risks. Controls are the concrete actions or safeguards you put in place."*

### What You Need

- Identified risks from Step 3
- Knowledge of current security measures
- Policies that govern these controls (from Step 5)

### Walkthrough - Control 1: Multi-Factor Authentication

**Navigate to**: Controls > Control Register

| Field | Example Value |
|-------|---------------|
| **Control Name** | Multi-Factor Authentication for Administrative Access |
| **Description** | All administrative access to the NextGen SIEM Pro platform requires multi-factor authentication using TOTP or hardware tokens. This control reduces the risk of unauthorized access through compromised credentials. MFA is enforced at the application level and cannot be bypassed. |
| **Implementation Status** | Implemented |
| **Control Set** | Access Control |

**Link to**:
- **Risk**: Unauthorized Access to SIEM Platform and Customer Data
- **Policy**: Information Security Policy (created in Step 5)
- **Objective**: A.8.5 - Secure Authentication

Click **Save**.

### Walkthrough - Control 2: Dependency Vulnerability Scanning

| Field | Example Value |
|-------|---------------|
| **Control Name** | Automated Dependency Vulnerability Scanning |
| **Description** | All third-party dependencies are continuously scanned for known vulnerabilities using automated tools (Snyk, Dependabot) integrated into the CI/CD pipeline. Critical vulnerabilities block deployment and trigger immediate remediation. SBOM is updated with every release. |
| **Implementation Status** | Implemented |
| **Control Set** | Supply Chain Security |

**Link to**:
- **Risk**: Supply Chain Attack via Compromised Third-Party Dependencies
- **Policy**: EU CRA Vulnerability Management Policy (created in Step 5)
- **Objective**: A.8.8 - Management of Technical Vulnerabilities

Click **Save**.

### Walkthrough - Control 3: Incident Response Hotline

| Field | Example Value |
|-------|---------------|
| **Control Name** | 24/7 Security Incident Response Hotline |
| **Description** | A dedicated security incident response hotline is available 24/7 for reporting security events. All staff are trained on reporting procedures. Incidents are triaged within 1 hour and escalated per severity level. The hotline is monitored by the Security Operations Center. |
| **Implementation Status** | Implemented |
| **Control Set** | Incident Management |

**Link to**:
- **Risk**: EU CRA Non-Compliance (Vulnerability Disclosure Failures)
- **Policy**: Information Security Policy
- **Objective**: A.6.8 - Information Security Incident Management

Click **Save**.

### Using the Controls Library

**Navigate to**: Controls > Controls Library

1. Browse pre-built control templates organized by category
2. Find controls like "Encryption at Rest", "Access Reviews", "Backup Procedures"
3. Import relevant templates directly into your Control Register
4. Customize imported controls to match your implementation

> **Tip**: Controls are the bridge between your risks and your policies. They define what you actually do to address each risk.

---

## Step 5: Create Policies

> *"Go to Policy Registration to create security and compliance policies. Link each policy to the relevant frameworks, objectives, and controls."*

### What You Need

- Framework seeded (Step 1)
- Understanding of which objectives the policy addresses
- Policy content (body text)

### Walkthrough - Policy 1: Information Security Policy

**Navigate to**: Documents > Policies

| Field | Example Value |
|-------|---------------|
| **Policy Title** | Information Security Policy |
| **Status** | Approved |
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
Version: 1.0
```

Click **Save Policy**.

### Walkthrough - Policy 2: EU CRA Vulnerability Management Policy

| Field | Example Value |
|-------|---------------|
| **Policy Title** | EU Cyber Resilience Act - Vulnerability Management Policy |
| **Status** | Approved |
| **Framework** | ISO/IEC 27001:2022 |
| **Objectives** | A.8.8 - Management of Technical Vulnerabilities |

**Policy Body**:
```
This policy establishes Clone Systems' commitment to comply with the EU Cyber
Resilience Act (Regulation (EU) 2024/2847) vulnerability handling requirements
for the NextGen SIEM Pro platform.

Scope: NextGen SIEM Pro software platform (ANNEX III - Class I product)

Vulnerability Disclosure Requirements:
- Public coordinated vulnerability disclosure policy published
- Security contact: security@clone-systems.com
- Maximum 24-hour acknowledgment for reported vulnerabilities
- Vulnerability assessment within 7 days of confirmed report
- Security patches released within 14 days for critical vulnerabilities
- Customer notification within 24 hours of patch availability

Vulnerability Monitoring:
- Continuous monitoring of CVE databases and security advisories
- SBOM maintained and updated with every release
- Third-party dependency scanning in CI/CD pipeline
- Quarterly security assessments by external auditors

Support and Update Commitment:
- Minimum 5 years security update support from product release
- End-of-life notifications provided 12 months in advance
- Security updates provided free of charge to all customers

Incident Reporting to ENISA:
- Critical vulnerabilities actively exploited reported within 24 hours
- Coordination with ENISA and national CSIRT as required

Policy Owner: Chief Information Security Officer (CISO)
Effective Date: 2025-01-15
Review Date: 2026-01-15
Version: 1.0
```

Click **Save Policy**.

### Walkthrough - Policy 3: Secure Development Lifecycle Policy

| Field | Example Value |
|-------|---------------|
| **Policy Title** | EU Cyber Resilience Act - Secure Development Lifecycle Policy |
| **Status** | Approved |
| **Framework** | ISO/IEC 27001:2022 |
| **Objectives** | A.8.25 - Secure Development Life Cycle |

**Policy Body**:
```
This policy defines Clone Systems' secure development lifecycle (SDLC)
requirements to ensure the NextGen SIEM Pro platform meets EU Cyber
Resilience Act security-by-design obligations.

Scope: All software development for NextGen SIEM Pro platform

Security-by-Design Requirements (EU CRA Annex I, Part I):
- Threat modeling completed during design phase for all new features
- Privacy-by-design principles integrated from project inception
- Security architecture review required before implementation
- Defense-in-depth strategy applied to all system components

Secure Coding Standards:
- OWASP Secure Coding Practices enforced
- Input validation and output encoding mandatory
- Cryptographic standards: TLS 1.3, AES-256, RSA-4096 minimum
- No hardcoded credentials or secrets in source code

Security Testing Requirements:
- Static Application Security Testing (SAST) on every commit
- Dynamic Application Security Testing (DAST) on every release candidate
- Software Composition Analysis (SCA) for dependency vulnerabilities
- Penetration testing quarterly and before major releases

Secure Build and Deployment:
- Automated CI/CD pipeline with security gates
- Code signing for all production artifacts
- Immutable build artifacts with cryptographic attestation
- Supply chain security: verified dependencies only

Policy Owner: VP of Engineering
Effective Date: 2024-11-01
Review Date: 2025-11-01
Version: 2.0
```

Click **Save Policy**.

### Policy Status Reference

| Status | Meaning |
|--------|---------|
| Draft | Initial creation, not yet reviewed |
| Review | Under peer or management review |
| Ready for Approval | Review complete, awaiting formal approval |
| Approved | Active, enforceable policy |

> **Tip**: Policies formalise your controls into documented rules. Map them to framework objectives to close the compliance loop.

---

## Step 6: Run Assessments

> *"Navigate to Assessments to start a new compliance assessment. Select a framework, answer the assessment questions, and track your progress."*

### What You Need

- A seeded framework (Step 1)
- Registered assets (Step 2) if using product scope
- Policies to link to answers (Step 5)

### Walkthrough - Create and Complete an Assessment

**Navigate to**: Assessments

**Step 1: Create the Assessment**

| Field | Example Value |
|-------|---------------|
| **Framework** | ISO/IEC 27001:2022 |
| **Assessment Type** | Internal Audit |
| **Scope** | Product: NextGen SIEM Pro |
| **Assessment Name** | Pre-certification internal audit for NextGen SIEM Pro ISO 27001:2022 compliance |

Click **Create**.

**Step 2: Answer the Questions**

The system generates the complete question set for your framework. Answer each question with detailed responses:

---

**Question 1** (A.5.1): *"Has the organization established and documented an information security policy?"*

| Field | Value |
|-------|-------|
| **Answer** | Yes. The Information Security Policy was approved by the CISO on 2025-01-01. It covers all information systems including the NextGen SIEM Pro platform and supporting infrastructure. The policy is reviewed annually and addresses confidentiality, integrity, and availability requirements. |
| **Evidence** | Upload: `Information_Security_Policy_v1.0.pdf` |
| **Policy Link** | Select: "Information Security Policy" |

Click **Save Answer**.

---

**Question 2** (A.5.15): *"Is an access control policy established and documented?"*

| Field | Value |
|-------|-------|
| **Answer** | Partially. Access control procedures exist and are enforced (MFA, RBAC, IP whitelisting), but the formal standalone access control policy document is pending management approval. Expected completion: Q4 2025. |
| **Evidence** | Upload: `Access_Control_Procedures_Draft.pdf` |
| **Policy Link** | Select: "Information Security Policy" |

Click **Save Answer**.

---

**Question 3** (A.8.2): *"Is the allocation and use of privileged access rights restricted and managed?"*

| Field | Value |
|-------|-------|
| **Answer** | Yes. MFA is enforced for all administrative access to NextGen SIEM Pro. RBAC with least privilege is implemented across all system components. Administrative actions are logged with immutable audit trails. IP whitelisting restricts admin access to office and VPN IPs only. Quarterly access reviews are completed with sign-off from the CISO. |
| **Evidence** | Upload: `Quarterly_Access_Review_Q1_2025.pdf` |
| **Policy Link** | Select: "Information Security Policy" |

Click **Save Answer**.

---

**Question 4** (A.6.8): *"Are security incidents reported through appropriate management channels?"*

| Field | Value |
|-------|-------|
| **Answer** | Yes. A 24/7 security incident response hotline is established and monitored by the SOC team. All staff complete mandatory incident reporting training annually. Incident response procedures define severity levels, escalation paths, and response timelines. All incidents are documented in the incident management system. |
| **Evidence** | Upload: `Incident_Response_Procedure_v2.1.pdf` |

Click **Save Answer**.

---

**Question 5** (A.8.13): *"Are backup copies of information and software maintained and regularly tested?"*

| Field | Value |
|-------|-------|
| **Answer** | Partially. Daily automated backups are performed for all production databases and application data. Backups are encrypted and stored in geographically separate locations. However, restoration testing is currently done quarterly. Plan to increase testing to monthly starting Q4 2025 to meet best practice standards. |
| **Evidence** | Upload: `Backup_Schedule_and_Test_Results.pdf` |

Click **Save Answer**.

---

**Step 3: Track Progress**

Monitor your assessment progress:

| Metric | Value |
|--------|-------|
| Questions Answered | 5 of 93 |
| Progress | 5.4% |
| Status | In Progress |

**Step 4: Export Results**

- **PDF Export**: Generate a professional compliance report for stakeholders
- **CSV Export**: Extract answers for offline review or external analysis
- **ZIP Download**: Package all uploaded evidence files for archival

> **Tip**: You can pause and resume assessments at any time. Use CSV Import to bulk-populate answers if migrating from another tool.

---

## Step 7: Complete the Objectives Checklist

> *"Go to the Objectives Checklist to review the specific objectives from your framework chapters. Mark objectives as compliant, upload evidence files, and link policies."*

### What You Need

- A seeded framework (Step 1)
- Policies to link (Step 5)
- Evidence files to upload

### Walkthrough

**Navigate to**: Frameworks > Objectives

**Step 1**: Select **ISO/IEC 27001:2022** from the framework dropdown.

**Step 2**: Work through the objectives organized by chapter. For each objective, set the compliance status:

| Objective | Chapter | Status | Notes |
|-----------|---------|--------|-------|
| A.5.1 - Information Security Policy | Organizational Controls | **Compliant** | Policy approved 2025-01-01, reviewed by CISO |
| A.5.15 - Access Control | Organizational Controls | **Partially Compliant** | Procedures exist, formal policy pending approval |
| A.6.8 - Information Security Incident Management | People Controls | **Compliant** | 24/7 incident hotline established, all staff trained |
| A.8.2 - Privileged Access Rights | Technological Controls | **Compliant** | MFA + RBAC + IP whitelisting + quarterly reviews |
| A.8.5 - Secure Authentication | Technological Controls | **Compliant** | MFA mandatory, session timeout enforced |
| A.8.8 - Management of Technical Vulnerabilities | Technological Controls | **Compliant** | Automated scanning, quarterly pen testing |
| A.8.13 - Information Backup | Technological Controls | **Partially Compliant** | Daily backups, need monthly restoration testing |
| A.8.25 - Secure Development Life Cycle | Technological Controls | **Compliant** | SAST/DAST in CI/CD, code reviews enforced |

**Step 3**: Upload evidence files directly to objectives:
- A.5.1: Upload `Information_Security_Policy_v1.0.pdf`
- A.8.2: Upload `Quarterly_Access_Review_Q1_2025.pdf`
- A.8.8: Upload `Penetration_Test_Report_Q1_2025.pdf`

**Step 4**: Link policies to objectives:
- A.5.1 > "Information Security Policy"
- A.8.8 > "EU CRA Vulnerability Management Policy"
- A.8.25 > "EU CRA Secure Development Lifecycle Policy"

### Using AI Suggestions

1. Click **"Generate AI Suggestions"**
2. The AI analyzes objectives marked as Partially Compliant or Not Compliant
3. Review each suggestion with its confidence score:

| Objective | AI Suggestion | Confidence |
|-----------|---------------|------------|
| A.5.15 - Access Control | "Draft a formal access control policy document based on existing procedures. Include sections for user provisioning, privilege management, and access review schedules. Reference ISO 27001 A.5.15, A.8.2, and A.8.3 requirements." | 92% |
| A.8.13 - Information Backup | "Increase backup restoration testing from quarterly to monthly. Document test results with recovery time objectives (RTO) and recovery point objectives (RPO). Implement automated backup verification." | 88% |

4. Apply suggestions that fit your context
5. Dismiss suggestions that don't apply

### Compliance Summary

After completing the checklist:

| Status | Count | Percentage |
|--------|-------|------------|
| Compliant | 6 | 75% |
| Partially Compliant | 2 | 25% |
| Not Compliant | 0 | 0% |
| Not Assessed | 85 | (remaining objectives) |

**Step 5**: Click **Export to PDF** to generate the gap analysis report for stakeholders.

> **Tip**: Upload evidence files directly to each objective for audit readiness. The AI suggestions are especially useful for objectives marked as Partially Compliant.

---

## The Compliance Chain

> *"Assets > Risks > Controls > Policies > Objectives - this is how everything connects."*

After completing Steps 1-7, all your compliance entities are linked together. The Compliance Chain visualizes these relationships.

### Viewing the Chain

**Navigate to**: Compliance Chain > Map

The interactive graph shows how all entities connect:

```
NextGen SIEM Pro (Asset)
    |
    +--- Unauthorized Access Risk (Risk)
    |       |
    |       +--- MFA for Admin Access (Control)
    |       |       |
    |       |       +--- Information Security Policy (Policy)
    |       |               |
    |       |               +--- A.5.1 Information Security Policy (Objective)
    |       |               +--- A.8.5 Secure Authentication (Objective)
    |       |
    |       +--- Phishing Attempt Incident (Incident)
    |
    +--- Supply Chain Compromise Risk (Risk)
    |       |
    |       +--- Dependency Vulnerability Scanning (Control)
    |       |       |
    |       |       +--- EU CRA Vulnerability Management Policy (Policy)
    |       |               |
    |       |               +--- A.8.8 Technical Vulnerabilities (Objective)
    |       |
    |       +--- SBOM Maintenance (Control)
    |
    +--- EU CRA Non-Compliance Risk (Risk)
            |
            +--- Incident Response Hotline (Control)
            |       |
            |       +--- Information Security Policy (Policy)
            |               |
            |               +--- A.6.8 Incident Management (Objective)
            |
            +--- Secure Development Lifecycle (Control)
                    |
                    +--- EU CRA Secure Development Policy (Policy)
                            |
                            +--- A.8.25 Secure Development (Objective)
```

### Using All Links View

**Navigate to**: Compliance Chain > All Links

View every relationship in a searchable table:

| Source Entity | Relationship | Target Entity |
|---------------|-------------|---------------|
| NextGen SIEM Pro | has risk | Unauthorized Access Risk |
| Unauthorized Access Risk | mitigated by | MFA for Admin Access |
| MFA for Admin Access | governed by | Information Security Policy |
| Information Security Policy | maps to | A.5.1 Information Security Policy |
| NextGen SIEM Pro | has risk | Supply Chain Compromise Risk |
| Supply Chain Compromise Risk | mitigated by | Dependency Vulnerability Scanning |
| Dependency Vulnerability Scanning | governed by | EU CRA Vulnerability Management Policy |

### Identifying Gaps

Look for:
- **Assets without risks**: Every asset should have at least one risk identified
- **Risks without controls**: Every risk should have at least one control mitigating it
- **Controls without policies**: Every control should be governed by a policy
- **Policies without objectives**: Every policy should map to framework objectives
- **Orphaned incidents**: Incidents should link to the affected asset and related risk

---

## Additional Workflows

### Running Security Scans

After registering your assets, use the Security Tools to validate your security posture:

#### Dependency Check (OSV Scanner)

**Navigate to**: Security Tools > Dependency Check

1. Upload `requirements.txt` from the NextGen SIEM Pro project
2. Click **Start Scan**
3. Review findings:

| Package | Version | Vulnerability | Severity | Fix |
|---------|---------|---------------|----------|-----|
| TensorFlow | 2.15.0 | CVE-2024-3660 | High | 2.15.1 |
| Redis | 7.2.3 | CVE-2024-31227 | Medium | 7.2.4 |
| PostgreSQL | 16.1 | CVE-2024-0985 | High | 16.2 |

4. Click **AI Analysis** for remediation guidance
5. Export results as PDF
6. Link findings to the "Supply Chain Compromise" risk

#### Web Application Scan (ZAP)

**Navigate to**: Security Tools > Security Scanners

1. Enter target URL: `https://siem.clone-systems.com`
2. Select scan type: **Full Scan**
3. Monitor progress with real-time alerts
4. Review findings by severity (High, Medium, Low, Informational)
5. Export the security assessment report as PDF

#### SBOM Generation (Syft)

**Navigate to**: Security Tools > SBOM Generator

1. Upload the project archive or provide container image details
2. Generate the comprehensive package inventory
3. Review the SBOM report for all dependencies
4. Use this for CRA compliance documentation (EU CRA requires SBOM maintenance)

### Registering an Incident

**Navigate to**: Risks > Incident Registration

If a security event occurs during your compliance journey:

| Field | Example Value |
|-------|---------------|
| **Incident Name** | Phishing Attempt Targeting SIEM Administrators |
| **Description** | On 2025-03-15, three SIEM administrators received targeted phishing emails impersonating the IT support team. The emails contained malicious links designed to harvest MFA credentials. All emails were detected by the email security gateway. No credentials were compromised. Post-incident review confirmed MFA would have prevented access even if credentials were captured. |
| **Status** | Resolved |
| **Severity** | Medium |

Link to:
- **Affected Asset**: NextGen SIEM Pro
- **Related Risk**: Unauthorized Access to SIEM Platform
- **Framework**: ISO/IEC 27001:2022

The incident now appears in the Compliance Chain connected to the relevant asset and risk.

### Uploading Evidence

**Navigate to**: Documents > Evidence

Upload supporting documentation for audit readiness:

| Evidence Item | Linked To |
|---------------|-----------|
| Information_Security_Policy_v1.0.pdf | ISO 27001, A.5.1 |
| Quarterly_Access_Review_Q1_2025.pdf | ISO 27001, Access Control |
| Penetration_Test_Report_Q1_2025.pdf | ISO 27001, Vulnerability Management |
| Backup_Test_Results_2025.pdf | ISO 27001, A.8.13 |
| SBOM_NextGen_SIEM_Pro_v3.0.0.spdx | CRA, Supply Chain |

The system verifies evidence integrity automatically to ensure documents haven't been tampered with.

### Uploading Architecture Diagrams

**Navigate to**: Documents > Architecture

| Diagram | Description | Linked To |
|---------|-------------|-----------|
| SIEM_System_Architecture.pdf | High-level system architecture showing all components | ISO 27001, Access Control Risk |
| Network_Topology.pdf | Network diagram showing security zones and firewalls | ISO 27001, Network Security |
| CI_CD_Pipeline.pdf | Build and deployment pipeline with security gates | CRA, Secure Development |

---

## Complete Workflow Summary

| Step | Action | Navigate To | Time |
|------|--------|-------------|------|
| 1 | Seed Framework | Frameworks > Configuration > Manage Frameworks | 2 min |
| 2 | Register Asset | Assets / Products > Manage Assets | 5 min |
| 3 | Identify Risks (x3) | Risks > Risk Register | 15 min |
| 4 | Register Controls (x3) | Controls > Control Register | 10 min |
| 5 | Create Policies (x3) | Documents > Policies | 15 min |
| 6 | Run Assessment | Assessments | 10 min |
| 7 | Complete Objectives | Frameworks > Objectives | 5 min |
| - | View Compliance Chain | Compliance Chain > Map | 2 min |
| - | Run Security Scans | Security Tools | 5 min |
| - | Register Incident | Risks > Incident Registration | 3 min |
| - | Upload Evidence | Documents > Evidence | 5 min |

**Total estimated time**: 45-75 minutes for a complete compliance workflow demonstration.

---

## Key Takeaways

After completing this workflow, Clone Systems has:

1. **1 framework** seeded with 93 control objectives (ISO 27001)
2. **1 asset** registered with full CRA classification (NextGen SIEM Pro)
3. **3 risks** identified with comprehensive control measures
4. **3 controls** registered and linked to risks, policies, and objectives
5. **3 policies** documented and mapped to framework objectives
6. **5 assessment questions** answered with evidence
7. **8 objectives** evaluated (6 compliant, 2 partially compliant)
8. **Complete traceability** from asset through to compliance objective

Every entity links to the others through the Compliance Chain, creating an unbroken audit trail from the product being protected all the way to the framework objectives being satisfied.
