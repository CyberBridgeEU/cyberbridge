# Quick Start Example

A condensed end-to-end walkthrough following the User Guide steps. Complete this in under 15 minutes.

- **Company**: Helios Medical Systems
- **Product**: PatientVault Cloud v2.1 (Cloud-based patient records platform)
- **Framework**: NIS2
- **Goal**: NIS2 compliance for a healthcare SaaS provider

---

## 1. Seed the Framework

**Go to**: Frameworks > Configuration > Manage Frameworks

1. Click "Add from Template"
2. Select **NIS2**
3. Click "Create Framework"

---

## 2. Register the Asset

**Go to**: Assets / Products > Manage Assets

| Field | Value |
|-------|-------|
| **Name** | PatientVault Cloud |
| **Version** | 2.1 |
| **Justification** | Cloud-based electronic health records platform processing sensitive patient data across EU healthcare providers |
| **License** | SaaS - Annual Subscription |
| **Description** | Secure cloud platform for storing, managing, and sharing electronic patient health records. Supports HL7 FHIR interoperability, role-based clinical access, and encrypted data at rest and in transit. |
| **Asset Type** | Software |
| **Economic Operator** | Manufacturer |
| **Status** | Live |

Click **Save**.

---

## 3. Add a Risk

**Go to**: Risks > Risk Register

| Field | Value |
|-------|-------|
| **Product Type** | Software |
| **Risk Category** | Communication Security |
| **Likelihood** | High |
| **Severity** | Critical |
| **Residual Risk** | Medium |
| **Status** | Reduce |

**Description**:
```
Patient Data Breach via API Exploitation

PatientVault Cloud exposes FHIR-compliant APIs for clinical system
integration. Improperly authenticated API calls or injection attacks
could expose protected health information (PHI) for thousands of patients.
```

**Impact**:
```
- GDPR fines up to EUR 20M or 4% of turnover
- NIS2 penalties for essential service providers
- Patient trust destruction and class-action lawsuits
```

**Controls**:
```
- OAuth 2.0 + mTLS for all API endpoints
- Rate limiting and anomaly detection on API gateway
- Quarterly penetration testing of FHIR APIs
- Real-time intrusion detection alerts
```

Click **Save Risk**.

---

## 4. Register a Control

**Go to**: Controls > Control Register

| Field | Value |
|-------|-------|
| **Control Name** | API Gateway Security with mTLS |
| **Description** | All FHIR API endpoints require mutual TLS authentication and OAuth 2.0 bearer tokens. The API gateway enforces rate limits (100 req/min per client), validates input schemas, and logs all requests for audit. |
| **Implementation Status** | Implemented |
| **Control Set** | API Security |

Link to:
- **Risk**: Patient Data Breach via API Exploitation
- **Objective**: Network and Information Systems Security (NIS2)

Click **Save**.

---

## 5. Create a Policy

**Go to**: Documents > Policies

| Field | Value |
|-------|-------|
| **Title** | API Security and Data Protection Policy |
| **Status** | Approved |
| **Framework** | NIS2 |

**Body**:
```
Helios Medical Systems enforces strict API security controls for all
PatientVault Cloud integrations.

Requirements:
- All API connections require mTLS + OAuth 2.0
- PHI transmitted only over TLS 1.3 encrypted channels
- API access logs retained for 3 years
- Quarterly third-party API penetration testing
- Automated vulnerability scanning of API endpoints weekly
- Incident notification to national CSIRT within 24 hours

Policy Owner: CTO
Effective Date: 2025-06-01
```

Click **Save Policy**.

---

## 6. Run an Assessment

**Go to**: Assessments

**Create**:

| Field | Value |
|-------|-------|
| **Framework** | NIS2 |
| **Assessment Type** | Conformity |
| **Assessment Name** | PatientVault NIS2 Conformity Assessment |

**Answer a question**:

*"Does the entity implement appropriate technical measures to manage risks to network and information systems?"*

**Answer**: Yes. All API endpoints enforce mTLS and OAuth 2.0. Rate limiting and anomaly detection are active on the API gateway. Quarterly penetration testing validates controls. Real-time IDS alerts the SOC team of suspicious activity.

**Evidence**: Upload `API_Pentest_Report_Q1_2025.pdf`

**Policy Link**: Select "API Security and Data Protection Policy"

Click **Save Answer**.

---

## 7. Update the Objectives Checklist

**Go to**: Frameworks > Objectives

Select **NIS2**, then update:

| Objective | Status |
|-----------|--------|
| Network and Information Systems Security | **Compliant** |
| Incident Handling and Reporting | **Partially Compliant** |
| Business Continuity | **Not Assessed** |

Upload `API_Pentest_Report_Q1_2025.pdf` as evidence for the first objective.

Click **Generate AI Suggestions** to get recommendations for the Partially Compliant items.

---

## Done

In under 15 minutes you have:

- 1 NIS2 framework seeded
- 1 healthcare SaaS asset registered
- 1 critical API security risk documented
- 1 control linked to the risk
- 1 policy mapped to NIS2 objectives
- 1 assessment started with evidence
- 3 objectives evaluated

Navigate to **Compliance Chain > Map** to see how everything connects.
