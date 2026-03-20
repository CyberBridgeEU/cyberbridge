# CRA Start Example

A condensed end-to-end walkthrough following the User Guide steps for a **Cyber Resilience Act (CRA)** compliance scenario. Complete this in under 15 minutes.

- **Company**: SecureSight Technologies
- **Product**: Wazuh SIEM with AI Remediation Actions
- **Framework**: CRA (Cyber Resilience Act)
- **CRA Criticality**: ANNEX III - Important Products with Digital Elements - Class I
- **Goal**: CRA compliance for a SIEM platform with AI-powered automated remediation

---

## 1. Seed the Framework

**Go to**: Frameworks > Configuration > Manage Frameworks

1. Click "Add from Template"
2. Select **CRA**
3. Click "Create Framework"

---

## 2. Register the Asset

**Go to**: Assets / Products > Manage Assets

| Field | Value |
|-------|-------|
| **Name** | Wazuh SIEM with AI Remediation |
| **Version** | 4.9 |
| **Justification** | Security information and event management (SIEM) system with AI-powered automated remediation actions, classified as an Important Product with Digital Elements (ANNEX III, Class I) under the Cyber Resilience Act |
| **License** | Open Source - GPLv2 with Commercial Support |
| **Description** | Enterprise SIEM platform that collects, analyzes, and correlates security events across endpoints, networks, and cloud environments. Integrates AI/ML models to automatically recommend and execute remediation actions for detected threats. Supports log management, file integrity monitoring, vulnerability detection, and regulatory compliance reporting. |
| **Asset Type** | Software |
| **Economic Operator** | Manufacturer |
| **Status** | Live |
| **Criticality** | ANNEX III - IMPORTANT PRODUCTS WITH DIGITAL ELEMENTS - Class I |
| **Criticality Option** | Security information and event management (SIEM) systems |

Click **Save**.

---

## 3. Add a Risk

**Go to**: Risks > Risk Register

| Field | Value |
|-------|-------|
| **Product Type** | Software |
| **Risk Category** | AI & Autonomous Operations |
| **Likelihood** | High |
| **Severity** | Critical |
| **Residual Risk** | Medium |
| **Status** | Reduce |

**Description**:
```
Emergent Properties and Unintended Consequences from AI Remediation

The AI remediation engine may produce emergent behaviors or unintended
consequences when autonomously executing response actions. Automated
remediation could quarantine legitimate services, block valid traffic,
or cascade across dependent systems without adequate human oversight.
```

**Impact**:
```
- CRA non-compliance fines up to EUR 15M or 2.5% of global turnover
- Uncontrolled AI actions disrupting critical infrastructure monitoring
- Loss of customer trust in automated security operations
- Regulatory scrutiny under EU AI Act for high-risk AI systems
```

**Controls**:
```
- AI governance framework with kill switches and approval gates
- Human-in-the-loop oversight for high-impact remediation actions
- AI risk mapping linking capabilities to operational and legal risks
- Continuous monitoring of AI remediation effectiveness and drift
```

Click **Save Risk**.

---

## 4. Register a Control

**Go to**: Controls > Control Register

| Field | Value |
|-------|-------|
| **Control Name** | AI & Autonomous Technologies Internal Controls |
| **Description** | Specific controls govern all AI-driven remediation actions within the SIEM platform including kill switches to halt automated responses, approval gates for high-impact actions, and rollback mechanisms to reverse unintended changes. All AI remediation decisions are logged with full audit trails. |
| **Implementation Status** | Implemented |
| **Control Set** | SCF - AI & Autonomous Tech |

Link to:
- **Risk**: Emergent Properties and Unintended Consequences from AI Remediation
- **Objective**: Minimize negative impact on other services (ANNEX I Art. 3g)

Click **Save**.

---

## 5. Create a Policy

**Go to**: Documents > Policies

| Field | Value |
|-------|-------|
| **Title** | Risk Management Policy |
| **Status** | Approved |
| **Framework** | CRA |

**Body**:
```
SecureSight Technologies maintains a comprehensive risk management
policy governing AI/ML-specific risks inherent in automated SIEM
remediation.

Requirements:
- All AI remediation capabilities are inventoried and risk-mapped
- AI governance policies reviewed annually by senior management
- Kill switches and approval gates for all high-impact automated actions
- AI risk mapping to CRA legal, operational, and safety requirements
- Quarterly assessment of AI remediation effectiveness and drift
- Annual risk assessment covering SIEM operations and AI capabilities
- Incident notification to ENISA and CSIRTs for actively exploited vulns

Policy Owner: CISO
Effective Date: 2025-09-01
```

Click **Save Policy**.

---

## 6. Run an Assessment

**Go to**: Assessments

**Create**:

| Field | Value |
|-------|-------|
| **Framework** | CRA |
| **Assessment Type** | Conformity |
| **Assessment Name** | Wazuh SIEM CRA Conformity Assessment |

**Answer a question**:

*"Does the product ensure an appropriate level of cybersecurity based on the risks?"*

**Answer**: Yes. The Wazuh SIEM platform undergoes quarterly vulnerability scans and penetration testing. Secure coding practices are enforced across all SIEM customizations, AI model integrations, and API extensions. An annual risk assessment evaluates SIEM operations and AI remediation capabilities. 65 controls (55 Baseline + 10 SCF AI-specific) are mapped across 30 identified risks spanning 8 risk categories.

**Evidence**: Upload `CRA_Conformity_Technical_Documentation_2025.pdf`

**Policy Link**: Select "Risk Management Policy"

Click **Save Answer**.

---

## 7. Update the Objectives Checklist

**Go to**: Frameworks > Objectives

Select **CRA**, then update:

| Objective | Status |
|-----------|--------|
| Appropriate cybersecurity based on risks (ANNEX I Art. 1) | **Compliant** |
| No known exploitable vulnerabilities (ANNEX I Art. 2) | **Compliant** |
| Secure by default configuration (ANNEX I Art. 3a) | **Compliant** |
| Protection from unauthorised access (ANNEX I Art. 3b) | **Compliant** |
| Security monitoring and logging (ANNEX I Art. 3j) | **Compliant** |
| Minimize negative impact on other services (ANNEX I Art. 3g) | **Partially Compliant** |
| SBOM and component documentation (Vuln. Handling Obj. 1) | **Not Assessed** |

Upload `CRA_Conformity_Technical_Documentation_2025.pdf` as evidence for the first objective.

Click **Generate AI Suggestions** to get recommendations for the Partially Compliant and Not Assessed items.

---

## Done

In under 15 minutes you have:

- 1 CRA framework seeded with 27 objectives across 8 chapters
- 1 SIEM product registered as ANNEX III Class I critical
- 1 AI-specific risk documented with remediation strategy
- 1 SCF AI control linked to the risk
- 1 policy mapped to CRA objectives
- 1 conformity assessment started with evidence
- 7 objectives evaluated across secure design, access control, and vulnerability handling

Navigate to **Compliance Chain > Map** to see how everything connects.

> **Tip**: The CRA requires manufacturers of Important Products (Class I) to apply harmonised standards or undergo third-party conformity assessment. Use the Traceability Matrix in the Excel mapping file to trace every risk through its mitigating controls, governing policies, and CRA objectives.
