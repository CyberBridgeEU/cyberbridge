# CyberBridge — Functional & Non-Functional Requirements

> **Project**: 101249702 — CYBER-BRIDGE — DIGITAL-ECCC-2024-DEPLOY-CYBER-07
> **Document scope**: Captures the functional (FR) and non-functional (NFR) requirements of the CyberBridge platform as implemented in this repository, traced to the initial tasks defined in the Grant Agreement (pages 75–81), the project KPIs, and the Key Exploitable Results (KER).
> **Verification baseline**: This document was reconciled against the actual code in `cyberbridge_backend/app/` and `docker-compose.yml`. Each requirement carries an implementation status and (where relevant) file evidence. Any drift between this document and the codebase should be reported and the doc updated.

### Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ **Implemented** | Verified in code today; behaviour matches the requirement. |
| 🟡 **Partial** | Implemented in part, or implemented differently than the worded requirement. The "Notes" column explains the delta. |
| ⚪ **Planned** | Defined in the Grant Agreement / KPI / KER but not yet present in the code (intent, not implementation). |

---

## Contents

1. [Introduction](#1-introduction)
2. [Integration with Grant Agreement Initial Tasks](#2-integration-with-grant-agreement-initial-tasks)
   - [WP1 — Project Management, Risk Oversight & Innovation Coordination](#wp1--project-management-risk-oversight--innovation-coordination)
   - [WP2 — Cross-Border Compliance Architecture & System Design](#wp2--cross-border-compliance-architecture--system-design)
   - [WP3 — Compliance Tools & Certification Framework](#wp3--compliance-tools--certification-framework)
   - [WP4 — Platform Development & Tool Integration](#wp4--platform-development--tool-integration)
   - [WP5 — Pilot Testing, Validation & Training](#wp5--pilot-testing-validation--training)
   - [WP6 — Impact, Dissemination & Exploitation](#wp6--impact-dissemination--exploitation)
3. [Stakeholders & Actors](#3-stakeholders--actors)
4. [Functional Requirements](#4-functional-requirements)
   - [4.1 Frameworks, Chapters & Objectives (FR-FRA)](#41-frameworks-chapters--objectives-fr-fra)
   - [4.2 Compliance Engine & Assessments (FR-COMP)](#42-compliance-engine--assessments-fr-comp)
   - [4.3 Risk Management (FR-RSK)](#43-risk-management-fr-rsk)
   - [4.4 Security Scanning (FR-SCAN)](#44-security-scanning-fr-scan)
   - [4.5 Cyber Threat Intelligence (FR-CTI)](#45-cyber-threat-intelligence-fr-cti)
   - [4.6 Dark Web Intelligence (FR-DW)](#46-dark-web-intelligence-fr-dw)
   - [4.7 AI / RAG Advisory (FR-AI)](#47-ai--rag-advisory-fr-ai)
   - [4.8 Audit Engagements & Evidence (FR-AUD)](#48-audit-engagements--evidence-fr-aud)
   - [4.9 Incident Management & Forensics (FR-INC)](#49-incident-management--forensics-fr-inc)
   - [4.10 Regulatory Monitoring (FR-REG)](#410-regulatory-monitoring-fr-reg)
   - [4.11 Documentation Generator (FR-DOC)](#411-documentation-generator-fr-doc)
   - [4.12 User Experience & Dashboard (FR-UX)](#412-user-experience--dashboard-fr-ux)
   - [4.13 Authentication, Authorisation & Identity (FR-AUTH)](#413-authentication-authorisation--identity-fr-auth)
   - [4.14 Certification Framework (FR-CERT)](#414-certification-framework-fr-cert)
   - [4.15 Backup & Restore (FR-BAK)](#415-backup--restore-fr-bak)
5. [Non-Functional Requirements](#5-non-functional-requirements)
   - [5.1 Security (NFR-SEC)](#51-security-nfr-sec)
   - [5.2 Privacy & Data Protection (NFR-PRIV)](#52-privacy--data-protection-nfr-priv)
   - [5.3 Legal & Ethics (NFR-LEG)](#53-legal--ethics-nfr-leg)
   - [5.4 Performance & Scalability (NFR-PERF)](#54-performance--scalability-nfr-perf)
   - [5.5 Availability & Reliability (NFR-AVAIL)](#55-availability--reliability-nfr-avail)
   - [5.6 Architecture & Interoperability (NFR-ARC)](#56-architecture--interoperability-nfr-arc)
   - [5.7 Quality Assurance (NFR-QA)](#57-quality-assurance-nfr-qa)
   - [5.8 Data Management (NFR-DM)](#58-data-management-nfr-dm)
   - [5.9 Innovation, Communication, Training, Exploitation](#59-innovation-communication-training-exploitation-nfr-inn--nfr-comm--nfr-train--nfr-exp)
   - [5.10 Governance & Usability (NFR-GOV / NFR-USAB / NFR-DEPLOY)](#510-governance--usability-nfr-gov--nfr-usab--nfr-deploy)
6. [KPIs and KERs](#6-kpis-and-kers)
   - [6.1 Project KPIs](#61-project-kpis-from-kpipng)
   - [6.2 Key Exploitable Results](#62-key-exploitable-results-from-kerpng)
7. [Requirements → Architecture Mapping](#7-requirements--architecture-mapping)
   - [7.1 By Functional Cluster](#71-by-functional-cluster)
   - [7.2 By NFR](#72-by-nfr)
8. [Interfaces, APIs & Integration Points](#8-interfaces-apis--integration-points)
   - [8.1 External (User-Facing) Interfaces](#81-external-user-facing-interfaces)
   - [8.2 Internal REST APIs](#82-internal-rest-apis)
   - [8.3 Service-to-Service Interfaces](#83-service-to-service-interfaces-internal-docker-network)
   - [8.4 Outbound Integrations](#84-outbound-integrations-third-party-apis--feeds)
   - [8.5 Persistence Interfaces](#85-persistence-interfaces)
   - [8.6 Network Boundary Summary](#86-network-boundary-summary)
9. [Verification Pass — Summary of Gaps](#9-verification-pass--summary-of-gaps-2026-04-20)
10. [Document Maintenance](#10-document-maintenance)

---

## 1. Introduction

CyberBridge is a cross-border cybersecurity compliance platform whose mission, as defined in the Grant Agreement, is to help SMEs, SOCs, CSIRTs, and critical-infrastructure operators meet the obligations of **NIS2**, the **Cyber Resilience Act (CRA)**, **GDPR**, and adjacent EU cybersecurity frameworks. The platform combines compliance tracking, AI-assisted advisory, automated documentation, security scanning, threat intelligence, dark-web probing, incident management, regulatory monitoring, and certification workflows in a single Docker-orchestrated stack.

This document is the authoritative requirements baseline. Each requirement is uniquely identified (`FR-xxx` / `NFR-xxx`) and traced to:

- the **Grant Agreement task** that originated it (T1.1 → T6.4),
- the **KPI(s)** it contributes to,
- the **KER(s)** it materialises,
- and the **architecture component(s)** that satisfy it (see §7 Mapping).

---

## 2. Integration with Grant Agreement Initial Tasks

The Grant Agreement defines 21 initial tasks across 6 work packages. The table below summarises each task and lists the requirements (defined in §4 and §5) that operationalise it inside the CyberBridge codebase.

### WP1 — Project Management, Risk Oversight & Innovation Coordination

| Task | Coordinator | Description (GA) | Realised by requirements |
|------|-------------|------------------|--------------------------|
| **T1.1** Project coordination, financial & technical management | I-ELINK | Coordination of partners, timelines, budgets, EC compliance. | NFR-GOV-01, NFR-GOV-02 |
| **T1.2** Quality Assurance & Risk Management | DNSC | Risk identification, mitigation, QA across deliverables. | NFR-QA-01, NFR-QA-02, FR-INC-01..05 |
| **T1.3** Data Management & Innovation Management | CLONE | DMP, innovation tracking, market translation. | NFR-DM-01..03, NFR-INN-01 |
| **T1.4** Regulatory Compliance & Ethics Oversight | ENC | NIS2/CRA/GDPR alignment, ethics, data protection. | NFR-LEG-01..04, NFR-PRIV-01..03 |

### WP2 — Cross-Border Compliance Architecture & System Design

| Task | Coordinator | Description (GA) | Realised by requirements |
|------|-------------|------------------|--------------------------|
| **T2.1** Detailed Scenarios & Use-Case Definition | DNSC | Cross-border use cases, stakeholder mapping. | FR-FRA-01, FR-AUD-01..03 |
| **T2.2** Requirements Analysis (NIS2/CRA/EU) | BOLTON | Compliance obligations, requirements matrix. | FR-FRA-01..06, FR-COMP-01..04 |
| **T2.3** System design & platform architecture | CLONE | Scalable, secure, interoperable platform architecture. | NFR-ARC-01..05, see `docs/architecture-diagram.md` |

### WP3 — Compliance Tools & Certification Framework

| Task | Coordinator | Description (GA) | Realised by requirements |
|------|-------------|------------------|--------------------------|
| **T3.1** Compliance-tracking tools | DNSC | Automated gap detection, dashboards, regulatory updates. | FR-COMP-01..06, FR-REG-01..04 |
| **T3.2** AI-enhanced regulatory assistant | CLONE | NLP/LLM advisor for NIS2/CRA. | FR-AI-01..04 |
| **T3.3** AI compliance agent | CLONE | ML-based risk identification & continuous improvement. | FR-AI-05..07, FR-RSK-01..05 |
| **T3.4** Penetration-testing & dark-web tools (EU-aligned) | CLONE | Adapted scanners + dark-web probing with privacy controls. | FR-SCAN-01..06, FR-DW-01..04, NFR-PRIV-02 |
| **T3.5** CYBER-BRIDGE certification framework | EPG | Interoperable certification schemes (CRA/NIS2/ENISA). | FR-CERT-01..04 |

### WP4 — Platform Development & Tool Integration

| Task | Coordinator | Description (GA) | Realised by requirements |
|------|-------------|------------------|--------------------------|
| **T4.1** Platform requirements for automated compliance verification | BOLTON | Real-time monitoring, automated reporting. | FR-COMP-01..06, NFR-PERF-01..03 |
| **T4.2** Smart Documentation Generator | CLONE | AI-driven policy, IR plans, ENISA cross-border notification. | FR-DOC-01..04, FR-INC-01..05 |
| **T4.3** User-friendly dashboard | CLONE | Central UI, real-time status, recommendations. | FR-UX-01..05 |
| **T4.4** Threat detection enhancement & SOC cooperation | CERTH | SOC integration, validated detection mechanisms. | FR-CTI-01..06, FR-SCAN-01..06 |

### WP5 — Pilot Testing, Validation & Training

| Task | Coordinator | Description (GA) | Realised by requirements |
|------|-------------|------------------|--------------------------|
| **T5.1** Pilot setup, execution & demonstration | EPG | Multi-jurisdiction pilots, twin-scheme validation. | FR-AUD-01..05, NFR-DEPLOY-01..03 |
| **T5.2** Cyber Range exercises | CLONE | Cross-border IR exercises, training scenarios. | FR-INC-01..05, NFR-TRAIN-01 |
| **T5.3** Penetration testing & performance evaluation | BOLTON | Vulnerability tests, simulated attacks, performance. | NFR-SEC-01..06, NFR-PERF-01..04 |

### WP6 — Impact, Dissemination & Exploitation

| Task | Coordinator | Description (GA) | Realised by requirements |
|------|-------------|------------------|--------------------------|
| **T6.1** Dissemination & outreach | I-ELINK | Workshops, webinars, publications, social media. | NFR-COMM-01 |
| **T6.2** Stakeholder engagement & training | DNSC | Capacity building, Cyber Range, ECSA collaboration. | NFR-TRAIN-01, FR-UX-05 |
| **T6.3** Replicability, market analysis, business modelling | BOLTON | Sustainable business models, exploitation strategy. | NFR-EXP-01, see KERs in §6 |
| **T6.4** Policy recommendations | ENC | Translate outcomes into NIS2/CRA policy guidance. | FR-REG-01..04, NFR-LEG-04 |

---

## 3. Stakeholders & Actors

| Actor | Role |
|-------|------|
| **Compliance Officer / SME admin** | Primary tenant operator; runs assessments, manages risks, approves policies. |
| **SOC Operator / Analyst** | Consumes scanner results, CTI dashboards, incident timelines; collaborates on response. |
| **External Auditor** | Magic-link authenticated read/write access to assigned engagements only. |
| **Regulator / National CSIRT** | Recipient of ENISA-conformant incident notifications and certificate verifications. |
| **Pilot Stakeholder (CRA/NIS2 Essential & Important Entities)** | Validates the platform across the twin-scheme pilots. |
| **CyberBridge System Administrator** | Owns infrastructure, backups, RBAC, framework snapshots. |

---

## 4. Functional Requirements

Each requirement uses the form `FR-<MODULE>-<NN>`. The "GA" column lists the originating Grant-Agreement task; "KPI/KER" lists the KPIs and KERs the requirement contributes to.

### 4.1 Frameworks, Chapters & Objectives (FR-FRA)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-FRA-01 | The platform SHALL support multiple compliance frameworks (CRA, NIS2, NIST, ISO 27001, GDPR, DORA) organised as Framework → Chapter → Objective hierarchies. | T2.2, T2.3 | KPI_07, KER.2 | ✅ | `frameworks_controller.py`, `models.Framework:84`, `models.Chapters:371`, `models.Objective:380`. Templates seeded via `POST /frameworks/{id}/seed/{template}`. |
| FR-FRA-02 | Each Objective SHALL carry a `ComplianceStatus` and link to `Policy`, `Risk`, `Evidence`, and `Answer` records. | T2.2 | KPI_07 | ✅ | `models.Objective:380`, `PolicyObjectives:402`. |
| FR-FRA-03 | The platform SHALL provide framework **snapshot** and **revert** so regulatory updates can be applied without losing prior assessment state. | T3.1, T6.4 | KPI_08 | ✅ | `frameworks_controller.py:980` (snapshots GET), `:996` (revert POST); `FrameworkSnapshot:2511`. |
| FR-FRA-04 | A **Compliance Chain Visualizer** SHALL render Risk → Policy → Objective → Framework relationships. | T2.3, T4.3 | KPI_13, KER.7 | ✅ | Frontend page in `cyberbridge_frontend/src/pages/`, fed by frameworks/policies/risks endpoints. |
| FR-FRA-05 | Frameworks SHALL be assignable per Organisation (multi-tenant). | T1.4, T2.3 | NFR-PRIV-01 | ✅ | `organisation_id` FK on `Framework` and downstream models. |
| FR-FRA-06 | The system SHALL ship pre-seeded `Question`, `AssessmentType`, and `FrameworkQuestion` data for the supported frameworks. | T2.2 | KPI_05 | ✅ | Template seeders in `app/seeds/` invoked via `frameworks_controller.py` seed endpoint. |

### 4.2 Compliance Engine & Assessments (FR-COMP)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-COMP-01 | Authenticated users SHALL create, edit, and submit `Assessment` instances against a chosen Framework. | T3.1, T4.1 | KPI_01, KER.2 | ✅ | `assessments_controller.py:23`, `models.Assessment:160`. |
| FR-COMP-02 | The system SHALL automatically compute compliance gaps from `Answer` records and surface them on the dashboard. | T3.1 | KPI_07 | ✅ | `home_controller.py:19` (`/dashboard/metrics`), `:37` (`/dashboard/pie-chart-data`). |
| FR-COMP-03 | The system SHALL generate a **Compliance Certificate** with SHA-256 verification hash and 1-year validity. | T3.5 | KPI_15, KER.6 | ✅ | `certificate_controller.py:22` (`POST /certificates/generate`), `models.ComplianceCertificate:2671` (`verification_hash`, `issued_at`, `expires_at`). |
| FR-COMP-04 | The system SHALL produce **Regulatory Submissions** to authorities using a pre-configured email directory. | T6.4 | KPI_07 | ✅ | `submission_controller.py:20`; `models.CertificateSubmission:2699`, `SubmissionEmailConfig:2721`. |
| FR-COMP-05 | The system SHALL allow exporting any assessment, risk register, or audit pack as PDF. | T4.2, T4.3 | KPI_02, KER.7 | ✅ | `audit_export_controller.py` and per-domain PDF endpoints; frontend uses `jsPDF`. |
| FR-COMP-06 | The system SHALL track `PolicyStatus`, `Policy`, and `PolicyObjective` junctions to evidence policy coverage of objectives. | T3.1 | KPI_07 | ✅ | `models.Policies:340`, `PolicyObjectives:402`, `PolicyFrameworks:365`. |

### 4.3 Risk Management (FR-RSK)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-RSK-01 | The system SHALL maintain a `Risk` register with likelihood, residual_risk, severity, status, and product/category linkage. | T3.3 | KPI_05, KER.1 | ✅ | `risks_controller.py`, `models.Risks:439`, `RiskSeverity:477`, `RiskStatuses:482`. |
| FR-RSK-02 | The system SHALL support `Product`, `ProductType`, `EconomicOperator`, `Criticality` taxonomies aligned with CRA. | T2.2, T3.3 | KPI_05, KER.2 | ✅ | `assets_controller.py`; `Criticalities` model with CIA rating fields. |
| FR-RSK-03 | The system SHALL produce CE-marking checklists for products with digital elements. | T3.5 | KPI_05, KER.6 | ✅ | `ce_marking_controller.py` — checklist + items endpoints. |
| FR-RSK-04 | The AI Compliance Agent SHALL recommend risk treatments using Phi-4 with retrieved framework context. | T3.3 | KPI_05, KER.1 | ✅ | `compliance_advisor_controller.py:45` (`POST /compliance-advisor/analyze`); `chatbot_controller.py:92` (`POST /chatbot/stream`). Uses pluggable LLM provider (default llama.cpp/Phi-4). |
| FR-RSK-05 | The system SHALL render risk heatmaps and trend dashboards. | T4.3 | KPI_13, KER.7 | ✅ | Frontend pages backed by `home_controller.py` and `risks_controller.py`. |

### 4.4 Security Scanning (FR-SCAN)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-SCAN-01 | The Scan Orchestrator SHALL invoke the Nmap, OWASP ZAP, Semgrep, OSV, and Syft microservices over HTTP. | T3.4, T4.4 | KPI_06, KER.2 | ✅ | `scanners_controller.py`: Nmap (5 variants `:149`+), ZAP (`/zap/scan`, `/zap/scan-github`), Semgrep (`:845`, `:952`), OSV (`:1165`, `:1521`), Syft (`:1251`, `:1337`). |
| FR-SCAN-02 | Network scan findings SHALL be enriched with NVD CVE / CVSS data via CPE lookup. | T3.4, T4.4 | KPI_16, KER.4 | ✅ | `models.NmapServiceVulnerability:1528`, `CVE:1339`, `CPEMatch:1415`. |
| FR-SCAN-03 | The system SHALL persist `ScannerHistory` and `ScanFindings` per organisation. | T4.1 | KPI_06 | ✅ | `models.ScannerHistory:721`, `ScanFinding:746` (incl. dedup `finding_hash`, `normalized_severity`, `is_remediated`). |
| FR-SCAN-04 | The system SHALL synchronise the **EUVD** and **NVD** vulnerability feeds. | T3.4 | KPI_16, KER.4 | ✅ | `nvd_controller.py` (`POST /nvd/sync`, daily 03:00 via APScheduler in `main.py:171`); `euvd_controller.py` (configurable schedule `main.py:190`). |
| FR-SCAN-05 | The system SHALL produce a CycloneDX SBOM via Syft for any uploaded artefact. | T3.4 | KPI_05, KER.2 | ✅ | `scanners_controller.py:1251` (`POST /scanners/syft/scan`) and `:1337` (`/scanners/syft/scan-github`). |
| FR-SCAN-06 | The system SHALL allow re-running scans on demand and surface delta findings. | T4.4 | KPI_06 | 🟡 | Re-run is supported (POST again); finding-level dedup via `finding_hash` exists, but an explicit "delta findings since last scan" view is not exposed as a dedicated endpoint. |

### 4.5 Cyber Threat Intelligence (FR-CTI)

> **Architecture note:** CTI tables (`CtiIndicator`, `CtiAttackPattern`, `CtiKevEntry`, `CtiThreatFeed`, `CtiSighting`, `CtiMalware`) live in the **`cti-service` microservice**, not in the main backend `models.py`. The main backend only proxies via `cti_controller.py`. This was incorrectly described in earlier drafts of this document.

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-CTI-01 | The CTI service SHALL poll all scanner microservices on a scheduled cadence (e.g. 1 h). | T4.4 | KPI_12, KER.4 | 🟡 | Polling is performed inside the `cti-service` container, not in the main backend's APScheduler. Cadence is configured per the `cti-service` source (not visible from the main API). |
| FR-CTI-02 | Scanner findings SHALL be normalised into `CtiIndicator` records (source, confidence, severity, CWE, port, URL). | T4.4 | KPI_06, KER.4 | 🟡 | Normalisation occurs inside `cti-service`; main backend exposes the results via `cti_controller.py:143` (`GET /cti/indicators`). Fields are surfaced through the proxy. |
| FR-CTI-03 | The CTI service SHALL synchronise the MITRE ATT&CK and CISA KEV feeds. | T3.1, T4.4 | KER.4 | 🟡 | MITRE ATT&CK exposed via `GET /cti/attack-patterns:128`. **CISA KEV endpoint NOT exposed** in the main API today (gap). |
| FR-CTI-04 | Indicators SHALL be linked to `CtiAttackPattern` (MITRE techniques) via a junction. | T4.4 | KER.4 | 🟡 | Junction lives in `cti-service` schema (not main DB). Reachable via the proxy. |
| FR-CTI-05 | The platform SHALL render a CTI dashboard with stats, timeline, and per-scanner result summaries. | T4.3, T4.4 | KPI_13, KER.7 | ✅ | `cti_controller.py` — `/cti/stats:64`, `/cti/timeline:75`, `/cti/{nmap,zap,semgrep,osv}/results`, plus `/cti/suricata/alerts:91`, `/cti/wazuh/alerts:102`. ATT&CK heatmap UI is fed by `/cti/attack-patterns`. |
| FR-CTI-06 | Sync state SHALL be tracked per feed source. | T4.4 | KER.4 | ⚪ | No dedicated sync-state endpoint surfaced via the main API; tracked internally in `cti-service`. |

### 4.6 Dark Web Intelligence (FR-DW)

> **Architecture note:** `DarkwebScan` and `DarkwebSettings` tables live inside the **`dark-web-scanner` microservice** (not main `models.py`). The main backend exposes a proxy router in `dark_web_controller.py`.

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-DW-01 | The Dark Web Scanner SHALL search across multiple Tor-hosted engines via a SOCKS5 proxy. | T3.4 | KPI_06, KER.4 | ✅ | `dark_web_controller.py:24` (`POST /dark-web/scan`); request accepts `keyword`, `engines`, `mp_units` (2–10), `proxy`, `limit` (1–50). Tor egress configured in the microservice container. |
| FR-DW-02 | Scans SHALL be queued with status, keyword, engines, params, and PDF result retrievable by ID. | T3.4 | KPI_06, KER.4 | ✅ | `GET /dark-web/scans:55`, `/dark-web/scan/{id}:91`, `/dark-web/scan/{id}/json:76`. |
| FR-DW-03 | Each org SHALL configure worker concurrency (e.g. `max_workers`) and the enabled engine list. | T1.4, T3.4 | NFR-PRIV-02 | 🟡 | `mp_units` (per-scan concurrency) is exposed on the request. Container-level `MAX_SCAN_WORKERS` is set in `docker-compose.yml`. A per-org persisted settings endpoint is **not** present in the main API. |
| FR-DW-04 | The service SHALL generate a PDF report per completed scan. | T3.4, T4.2 | KPI_02, KER.3 | ✅ | `GET /dark-web/scan/{id}/pdf:106`. |

### 4.7 AI / RAG Advisory (FR-AI)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-AI-01 | The platform SHALL embed framework objectives (384-dim vectors) and store them in **pgvector**. | T3.2 | KER.1 | ✅ | `models.ObjectiveEmbedding:2741` `embedding = Column(Vector(384), nullable=False)`; embed rebuild via `chatbot_controller.py:190`. |
| FR-AI-02 | The AI Compliance Advisor SHALL run a RAG pipeline (embed → similarity search → LLM completion). | T3.2 | KPI_03, KER.1 | ✅ | `compliance_advisor_controller.py:45` (`POST /compliance-advisor/analyze`) and `chatbot_controller.py:92` (`POST /chatbot/stream`, SSE). |
| FR-AI-03 | The platform SHALL support pluggable AI providers (llama.cpp, OpenAI, Anthropic, Google, X AI, QLON). | T3.2, T3.3 | KER.1 | ✅ | `models.OrganizationLLMSettings:607` enumerates: `llama.cpp` (default), `qlon`, `openai`, `anthropic`, `xai`, `google`. Provider chosen via `get_effective_llm_settings_for_user`. |
| FR-AI-04 | The Smart Documentation Generator SHALL produce policies, IR plans, audit reports, and ENISA notifications using LLM templates. | T4.2 | KPI_02, KER.1 | 🟡 | Audit report export exists (`audit_export_controller.py`); per-objective AI roadmap exists (`objectives_controller.py:302`, `:340`). Dedicated standalone "policy / IR plan / ENISA notification document generator" endpoints are not consolidated under one router; functionality is spread across the audit, incidents, and submission modules. |
| FR-AI-05 | The AI Compliance Roadmap generator SHALL emit step-by-step remediation plans for non-compliant objectives. | T3.3 | KPI_07, KER.1 | ✅ | `objectives_controller.py:302` (`POST /objectives/roadmap/{objective_id}`), `:340` (`POST /objectives/roadmap/bulk`). |
| FR-AI-06 | LLM responses SHALL be cached by query hash to amortise inference cost. | T3.2 | NFR-PERF-02 | ⚪ | Not implemented. An in-memory TTL cache exists for **scanner results** (`scanners_controller.py:26-59`), but there is no LLM-query-hash cache. |
| FR-AI-07 | All AI advisory output SHALL cite the retrieved objectives so recommendations are auditable. | T1.4, T3.2 | NFR-LEG-03 | 🟡 | RAG retrieval populates the prompt with relevant objectives, but explicit citation rendering in the response payload is not enforced; depends on prompt design. |

### 4.8 Audit Engagements & Evidence (FR-AUD)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-AUD-01 | The platform SHALL support external **audit engagements** with magic-link authentication. | T2.1, T5.1 | KPI_04, KER.6 | ✅ | `audit_engagements_controller.py`, `auditor_auth_controller.py:76` (`POST /auditor-auth/request-magic-link`), `validate-magic-link`. `AuditorInvitation:939` carries `access_token`, `token_expires_at`, MFA flag, watermark/download restriction. |
| FR-AUD-02 | Auditors SHALL only access engagements they are assigned to. | T1.4, T2.1 | NFR-SEC-03 | ✅ | `auditor_review_controller.py` enforces engagement scope; `check_user_role` and engagement FK checks throughout. |
| FR-AUD-03 | Each `Answer` SHALL accept multiple `Evidence` attachments stored under `audit_attachments`. | T2.1 | KER.3 | ✅ | `evidence_controller.py` upload endpoint; volume `backend_audit_attachments` declared in `docker-compose.yml`. |
| FR-AUD-04 | Evidence SHALL support **legal hold** to prevent deletion or modification. | T1.2, T1.4 | NFR-LEG-02, KER.3 | ✅ | `legal_hold_controller.py:34` (`POST /legal-holds/evidence/{id}`), `:77` (GET), `lift`; `models.LegalHold:2601` (`target_type`, `expires_at`, `status`). |
| FR-AUD-05 | The platform SHALL capture an immutable **chain-of-custody** record (who, when, action) for every evidence event. | T1.2, T1.4 | NFR-LEG-02, KER.3 | ✅ | `chain_of_custody_controller.py:28`; `models.CustodyTransfer:263` is hash-chained (`previous_transfer_hash`, `transfer_hash`, `transfer_index`). `AuditActivityLog:1206` is also hash-chained. |

### 4.9 Incident Management & Forensics (FR-INC)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-INC-01 | The system SHALL record incidents and trigger **ENISA-conformant cross-border notifications**. | T4.2 | KPI_17, KER.5 | 🟡 | `incidents_controller.py:21+` provides full CRUD; `models.ENISANotifications:2278` exists, but a dedicated `POST /incidents/{id}/enisa-notification` route is not present in the public router today (notifications are produced internally / via the submissions module). |
| FR-INC-02 | Each incident SHALL have a **forensic timeline** with evidence linking. | T1.2, T4.4 | KPI_17, KER.3 | 🟡 | Linkage via `IncidentEvidence:1898`, `IncidentRisk:1884`, `IncidentAsset:1891`, `IncidentFramework:1877`, plus `IncidentPatches:2222` (SLA tracking). There is no dedicated `IncidentTimeline` table; the timeline is derived from these joins + `AuditActivityLog`. |
| FR-INC-03 | Incident artefacts SHALL be timestamped via **FreeTSA RFC 3161** to prove temporal integrity. | T1.2, T1.4 | NFR-LEG-03, KER.3 | ✅ | `timestamp_controller.py` (`/timestamps/...`); `models.TimestampToken:2638` (`tsa_url`, `gen_time`, `payload_hash`, `token_b64`). Used by `ComplianceCertificate` and `AuditSignOff`. |
| FR-INC-04 | Incident reports SHALL be exportable as PDF for law-enforcement / national-CSIRT submission. | T4.2 | KPI_02, KER.5 | ✅ | Export via `audit_export_controller.py` and `submission_controller.py:20` (delivery). |
| FR-INC-05 | Incidents SHALL be linkable to CTI indicators and scanner findings. | T4.4 | KER.5 | 🟡 | Link to scanner findings (`ScanFinding`) and assets is supported. Direct CTI-indicator FK does not exist in main DB (CTI lives in the microservice); correlation is done at the UI layer. |

### 4.10 Regulatory Monitoring (FR-REG)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-REG-01 | A **Regulatory Change Monitor** SHALL run scheduled SearXNG queries across multiple search engines. | T3.1, T6.4 | KPI_08, KER.2 | ✅ | `regulatory_monitor_controller.py` + `searxng` container (`docker-compose.yml`). Scheduled via APScheduler (`main.py:224`, daily/weekly/biweekly per `RegulatoryMonitorSettings:2538`). |
| FR-REG-02 | Detected changes SHALL be summarised by the LLM and written to a change log. | T3.1, T3.2 | KPI_08, KER.1 | ✅ | `models.RegulatoryChange:2580` (`framework_type`, `confidence`, `status`); `RegulatoryScanResult:2566`. |
| FR-REG-03 | Operators SHALL acknowledge or dismiss changes; acknowledged changes SHALL update framework snapshots. | T3.1 | KPI_08 | ✅ | `regulatory_monitor_controller.py:415` (revert via snapshot). Acknowledge/dismiss flows reflected in `RegulatoryChange.status` (`pending → approved/rejected/applied`). |
| FR-REG-04 | The system SHALL allow defining custom monitored frameworks and search terms. | T2.2, T3.1 | KPI_08 | ✅ | `RegulatorySource:2522` configurations (CRA, NIS2, ISO 27001, …); settings endpoints in `regulatory_monitor_controller.py`. |

### 4.11 Documentation Generator (FR-DOC)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-DOC-01 | The Smart Documentation Generator SHALL produce policies, IR plans, audit reports, and notifications from templates. | T4.2 | KPI_02, KER.1 | 🟡 | Audit reports via `audit_export_controller.py`; AI roadmaps via `objectives_controller.py:302/340`. Dedicated "policy generator" and "IR plan generator" endpoints are not yet a single coordinated module. |
| FR-DOC-02 | Generated documents SHALL be exportable as PDF and editable inline before export. | T4.2, T4.3 | KPI_02 | ✅ | PDF export across audit, certificate, dark-web, and submission modules. Frontend uses `jsPDF`. |
| FR-DOC-03 | The generator SHALL pre-populate fields from compliance, risk, scanner, and CTI data. | T4.2 | KPI_02, KER.1 | ✅ | Generators pull from the relevant repositories (compliance, risks, scanner findings) at render time. |
| FR-DOC-04 | Documents SHALL be versioned and stored under `backend_uploads` (or `backend_audit_attachments`). | T4.2, T1.3 | NFR-DM-01 | ✅ | Volumes `backend_uploads` and `backend_audit_attachments` declared in `docker-compose.yml`. |

### 4.12 User Experience & Dashboard (FR-UX)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-UX-01 | The frontend SHALL be a React + TypeScript + Vite + Ant Design SPA. | T4.3 | KPI_13, KER.7 | ✅ | `cyberbridge_frontend/package.json` and project structure confirm. |
| FR-UX-02 | The dashboard SHALL show compliance status, risk heatmaps, scan summaries, and CTI insights. | T4.3 | KPI_13, KER.7 | ✅ | Backed by `home_controller.py` (`/dashboard/metrics`, `/dashboard/pie-chart-data`, `/dashboard/frameworks`, `/dashboard/assessments`). |
| FR-UX-03 | Routing SHALL use Wouter; state SHALL use Zustand stores (one per domain). | T4.3 | NFR-ARC-04 | ✅ | 54 stores under `cyberbridge_frontend/src/store/`; 73 pages under `src/pages/`. |
| FR-UX-04 | The UI SHALL provide light/dark theme and responsive layouts. | T4.3 | NFR-USAB-01 | 🟡 | Ant Design tokens support theming; full dark-mode coverage and a documented responsive baseline are not yet centrally tracked. |
| FR-UX-05 | The dashboard SHALL ship guided **demonstration** flows for training. | T5.2, T6.2 | NFR-TRAIN-01, KER.8 | ✅ | `docs/DEMONSTRATION_GUIDE.md`; demo flows referenced from the UI. |

### 4.13 Authentication, Authorisation & Identity (FR-AUTH)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-AUTH-01 | The platform SHALL authenticate users with JWT bearer tokens. | T1.4, T4.1 | NFR-SEC-01 | ✅ | `auth_controller.py:28` (`POST /auth/token`), `auth_service.py`. |
| FR-AUTH-02 | The platform SHALL support **SSO** (Google + Microsoft OAuth2). | T2.3, T4.1 | NFR-SEC-01 | 🟡 | Google + Microsoft OAuth2 only (`auth_controller.py:598/611/630/643`, `models.SSOSettings:685`). **SAML is NOT supported** today. |
| FR-AUTH-03 | The platform SHALL support **magic-link** authentication for external auditors. | T2.1, T5.1 | KER.6 | ✅ | `auditor_auth_controller.py:76` request + validate; `AuditorInvitation:939` (`access_token`, `token_expires_at`, `mfa_enabled`, `download_restricted`, `watermark_downloads`). |
| FR-AUTH-04 | RBAC SHALL be enforced at the route and service layers via the `Role` model. | T1.4 | NFR-SEC-03 | ✅ | `auth_service.check_user_role(...)` dependency on admin endpoints (e.g. `certificate_controller.py:26`, `legal_hold_controller.py:39`). |
| FR-AUTH-05 | All sessions SHALL expire and be revocable. | T1.4 | NFR-SEC-04 | ✅ | `models.UserSessions:47`; JWT TTL enforced. |

### 4.14 Certification Framework (FR-CERT)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-CERT-01 | The platform SHALL deliver a **Compliance Certificate** with SHA-256 verification hash. | T3.5 | KPI_15, KER.6 | ✅ | `certificate_controller.py:22` (`POST /certificates/generate`); `models.ComplianceCertificate:2671` (`verification_hash`). |
| FR-CERT-02 | Certificates SHALL be valid for 1 year and revocable. | T3.5 | KPI_15, KER.6 | ✅ | `expires_at` + `revoked` fields; `POST /certificates/{id}/revoke:126`. |
| FR-CERT-03 | Certificate verification SHALL be possible via a public hash-lookup endpoint. | T3.5 | KER.6 | ✅ | `GET /certificates/verify/{verification_hash}:82`. |
| FR-CERT-04 | Certification scope SHALL align with ENISA / ISO/IEC 27000 / 15408 / IEC 62443 / NIST SP 800. | T3.5 | KPI_15, KER.6 | 🟡 | Frameworks for ISO 27001, NIS2, CRA, etc. are seedable; alignment with IEC 62443 / ISO/IEC 15408 / NIST SP 800 is content-driven and not all templates are in-tree. |

### 4.15 Backup & Restore (FR-BAK)

| ID | Requirement | GA | KPI/KER | Status | Evidence / Notes |
|----|-------------|----|---------|--------|------------------|
| FR-BAK-01 | The platform SHALL ship an automated backup mechanism producing artefacts under `backend_backups`. | T1.2, T1.3 | NFR-AVAIL-02 | ✅ | `backups_controller.py`; APScheduler daily 02:00 (`main.py:151`), weekly cleanup Sun 03:00 (`:161`); `models.Backup:791` (`is_encrypted`, `expires_at`). 10-year retention default. |
| FR-BAK-02 | The platform SHALL support restore from any backup. | T1.2, T1.3 | NFR-AVAIL-02 | ✅ | `POST /backups/restore/{org_id}:209`. Restores schema rows and evidence files. (PITR semantics depend on backup snapshot frequency; per-backup restore is what is implemented.) |

---

## 5. Non-Functional Requirements

### 5.1 Security (NFR-SEC)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-SEC-01 | Authentication SHALL use industry-standard JWT signing; secrets SHALL be sourced from environment variables, never hard-coded. | T1.4, T5.3 | ✅ | `auth_service.py` reads JWT secret from env. |
| NFR-SEC-02 | All sensitive cryptographic primitives SHALL use the pinned `cryptography`/`pyasn1` versions; KDF salts SHALL be loaded from env. | T1.4 | ✅ | `requirements.txt` pins; recent commit `74e3893` moved KDF salt to env. |
| NFR-SEC-03 | RBAC SHALL be enforced server-side on every API; the frontend MUST NOT be the primary authorisation boundary. | T1.4 | ✅ | `check_user_role(...)` dependency widely applied (e.g. `certificate_controller.py:26`, `submission_controller.py:24`, `legal_hold_controller.py:39`). |
| NFR-SEC-04 | The platform SHALL pass internal penetration testing (T5.3) without critical findings before each release. | T5.3 | ⚪ | Process requirement — to be evidenced per release in WP5 reports. |
| NFR-SEC-05 | Internal microservices (CTI, scanners) SHALL NOT be exposed to the host network unless explicitly required. | T2.3 | 🟡 | `cti-service` is **internal-only** (no host port — confirmed in `docker-compose.yml`). Scanners (`nmap`, `zap`, `osv`, `semgrep`, `syft`) and `embeddings`, `dark-web-scanner`, `searxng`, `llamacpp` **are** exposed to the host on 8010–8016 / 8030 / 8040 / 11435 — appropriate for dev, but should be locked down in production. |
| NFR-SEC-06 | Secrets and credentials SHALL never be committed to the repo; `.env` SHALL be gitignored. | T1.4 | ✅ | `.env` and `.env.local` excluded by `.gitignore`. |

### 5.2 Privacy & Data Protection (NFR-PRIV)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-PRIV-01 | All tenant data SHALL be scoped per `Organisation` and isolated at the repository layer. | T1.4 | ✅ | `organisation_id` FK on every business model; repositories filter by `current_user.organisation_id`. |
| NFR-PRIV-02 | Dark-web probing SHALL implement privacy-preserving controls; differential-privacy techniques SHALL be investigated. | T3.4 | ⚪ | Differential privacy is **not** implemented. Per-scan `mp_units` and Tor isolation provide network-level controls only. |
| NFR-PRIV-03 | Personal data processing SHALL comply with GDPR; data subjects SHALL have export/erasure paths. | T1.4 | 🟡 | Per-org data isolation supports erasure-by-org; subject-level export/erasure endpoints are not exposed today. |

### 5.3 Legal & Ethics (NFR-LEG)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-LEG-01 | The platform SHALL align with NIS2, CRA, GDPR, DORA, and ENISA certification guidance. | T1.4, T2.2 | 🟡 | Frameworks for NIS2, CRA, ISO 27001 are seedable; DORA template is not in-tree. ENISA notification model exists but not exposed as a public endpoint. |
| NFR-LEG-02 | Evidence on legal hold SHALL be tamper-evident; the chain-of-custody log SHALL be append-only. | T1.2 | ✅ | `LegalHold:2601`; `CustodyTransfer:263` is hash-chained with `previous_transfer_hash`/`transfer_hash`/`transfer_index`. |
| NFR-LEG-03 | Forensic artefacts SHALL be timestamped (RFC 3161) so non-repudiation can be proven. | T1.2 | ✅ | `timestamp_authority_service.py` (FreeTSA); `TimestampToken:2638`; `timestamp_controller.py` verify endpoints. |
| NFR-LEG-04 | Generated policy recommendations SHALL be auditable (cite source objectives). | T1.4, T6.4 | 🟡 | RAG retrieval includes objectives in the prompt; explicit citation block in the response payload is not enforced. |

### 5.4 Performance & Scalability (NFR-PERF)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-PERF-01 | Dashboard pages SHALL render initial content quickly (target ≤2 s) on a typical SOC workstation against the seeded database. | T4.1, T5.3 | ⚪ | No formal performance test in CI; verified informally during pilot. |
| NFR-PERF-02 | LLM responses SHALL be cached by query hash; identical queries SHALL not re-invoke the model. | T3.2 | ⚪ | Not implemented. Scanner-results have a TTL cache (`scanners_controller.py:26-59`); LLM query cache is a future improvement. |
| NFR-PERF-03 | Scanner microservices SHALL run as independent containers and SHALL be horizontally scalable. | T2.3, T4.4 | ✅ | Each scanner is its own service in `docker-compose.yml`; replicas can be added. |
| NFR-PERF-04 | Forensic-evidence collection time SHALL be reduced by ≥30 % compared to the pre-CYBER-BRIDGE baseline. | T5.3, KPI_18 | ⚪ | KPI to be measured during WP5 pilot evaluation. |

### 5.5 Availability & Reliability (NFR-AVAIL)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-AVAIL-01 | All services SHALL declare Docker health-checks; dependent services SHALL only start when prerequisites are healthy. | T2.3 | ✅ | `docker-compose.yml` declares health-checks on every service and uses `condition: service_healthy` on dependencies. |
| NFR-AVAIL-02 | Backups SHALL run on schedule; restore SHALL be a single-command operation. | T1.2 | ✅ | Daily 02:00 backup, weekly Sun 03:00 cleanup; `POST /backups/restore/{org_id}`. |
| NFR-AVAIL-03 | The platform SHALL recover from any single microservice failure without data loss. | T2.3 | ✅ | Stateless scanner microservices; persistence isolated in `postgres_data` and named volumes. |

### 5.6 Architecture & Interoperability (NFR-ARC)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-ARC-01 | The backend SHALL follow MVC (`models/`, `repositories/`, `routers/`, `services/`, `dtos/`, `seeds/`). | T2.3 | ✅ | Layout confirmed under `cyberbridge_backend/app/`. |
| NFR-ARC-02 | All inter-service traffic SHALL be HTTP/JSON (or OpenAI-compatible for LLM). | T2.3 | ✅ | All scanner, CTI, dark-web, embeddings, and LLM calls are HTTP/JSON. |
| NFR-ARC-03 | All entities SHALL use UUID primary keys. | T2.3 | ✅ | Standard pattern across `app/models/models.py`. |
| NFR-ARC-04 | The frontend SHALL maintain one Zustand store per functional domain. | T4.3 | ✅ | 54 stores under `cyberbridge_frontend/src/store/`. |
| NFR-ARC-05 | The platform SHALL be deployable as a single `docker-compose up -d` invocation. | T2.3, T5.1 | ✅ | `docker-compose.yml` orchestrates the full stack with tiered health-check dependencies. |

### 5.7 Quality Assurance (NFR-QA)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-QA-01 | Each release SHALL pass linting (`npm run lint`) and the backend test suite. | T1.2 | 🟡 | Lint script exists. CI gating not formalised yet. |
| NFR-QA-02 | Pull requests SHALL receive code review before merging into `main`. | T1.2 | ⚪ | Process requirement; tracked outside the repo. |

### 5.8 Data Management (NFR-DM)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-DM-01 | Persistent volumes SHALL exist for `postgres_data`, `backend_uploads`, `backend_audit_attachments`, `backend_backups`, `zap_data`. | T1.3, T2.3 | ✅ | All five volumes declared in `docker-compose.yml`. |
| NFR-DM-02 | Database SHALL self-seed roles, organisations, and lookup data on first start. | T2.3 | ✅ | `app/seeds/` invoked at startup; default roles, organisations, lookup tables. |
| NFR-DM-03 | Schemas SHALL be migrated forward via versioned migrations; destructive migrations require sign-off. | T1.3 | 🟡 | SQLAlchemy `create_all` is used; formal Alembic migration history is not in tree. |

### 5.9 Innovation, Communication, Training, Exploitation (NFR-INN / NFR-COMM / NFR-TRAIN / NFR-EXP)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-INN-01 | Innovations SHALL be tracked and translated into market-ready outputs. | T1.3 | ⚪ | Tracked in WP1 / WP6 governance, not in code. |
| NFR-COMM-01 | The project website and dissemination channels SHALL be maintained per KPI_19/KPI_20. | T6.1 | ⚪ | External — not in this repo. |
| NFR-TRAIN-01 | Cyber-Range training scenarios and onboarding flows SHALL be provided for stakeholders. | T5.2, T6.2 | ✅ | `docs/DEMONSTRATION_GUIDE.md` and pilot use-case docs. |
| NFR-EXP-01 | The platform SHALL be packaged for SaaS / on-prem exploitation per the KER strategies. | T6.3 | ✅ | Single `docker-compose up -d` deployment supports both modes. |

### 5.10 Governance & Usability (NFR-GOV / NFR-USAB / NFR-DEPLOY)

| ID | Requirement | Origin | Status | Evidence / Notes |
|----|-------------|--------|--------|------------------|
| NFR-GOV-01 | Project artefacts (deliverables, decisions, risk register) SHALL be versioned in the repo or PMS. | T1.1 | 🟡 | `docs/` holds architecture, requirements, demo guide; deliverables tracked externally. |
| NFR-GOV-02 | EC reporting SHALL be supported by exportable KPI reports. | T1.1 | 🟡 | Per-feature exports exist; consolidated KPI report export is not a single endpoint. |
| NFR-USAB-01 | The UI SHALL meet WCAG 2.1 AA where reasonably achievable. | T4.3 | ⚪ | No formal accessibility audit has been run; not enforced in CI. |
| NFR-DEPLOY-01 | Deployment manifests SHALL be reproducible across pilot sites. | T5.1 | ✅ | Single `docker-compose.yml` with versioned image refs. |
| NFR-DEPLOY-02 | The stack SHALL boot in tiered order (DB → ZAP → Tier-3 services → API → Frontend). | T2.3, T5.1 | ✅ | Confirmed via `condition: service_healthy` chain in `docker-compose.yml`; see `docs/architecture-diagram.md`. |
| NFR-DEPLOY-03 | Each microservice SHALL expose a `/health` endpoint. | T2.3 | 🟡 | Scanner microservices expose `/health`; the main FastAPI backend has root `/` and dashboard endpoints, but **no dedicated `/health`** route — the Docker health-check uses an alternative readiness probe. Adding a real `/health` is a small follow-up. |

---

## 6. KPIs and KERs

### 6.1 Project KPIs (from `KPI.png`)

| KPI | Description | Baseline → Target | Realised by |
|-----|-------------|-------------------|-------------|
| KPI_01 | SMEs using CYBER-BRIDGE compliance tools | 0 → 15 in 2 yrs | FR-COMP-01, FR-FRA-01 |
| KPI_02 | Compliance reports via Smart Documentation Generator | 0 → 200 in 1.5 yrs | FR-DOC-01..04, FR-COMP-05 |
| KPI_03 | SOCs adopting CYBER-BRIDGE threat detection | 0 → 6 in 2 yrs | FR-CTI-01..06, FR-AI-02 |
| KPI_04 | Pilots conducted | 0 → 4 by project end | FR-AUD-01..05 |
| KPI_05 | Products/services automating CRA compliance | 0 → ≥2 | FR-RSK-01..03, FR-FRA-06, FR-SCAN-05 |
| KPI_06 | IT-based solutions for cybersecurity incident handling | 0 → ≥4 | FR-SCAN-01..06, FR-CTI-01..06, FR-DW-01..04 |
| KPI_07 | Organisations meeting CRA/NIS2 via CYBER-BRIDGE | 0 → 20 | FR-COMP-01..06, FR-FRA-01..06 |
| KPI_08 | Tool updates from feedback / regulatory changes | 0 → quarterly | FR-FRA-03, FR-REG-01..04 |
| KPI_09 | Stakeholder participation in training | 0 → 100 in 2 yrs | NFR-TRAIN-01, FR-UX-05 |
| KPI_10 | Adoption in critical sectors | 0 → 4 by project end | FR-FRA-05, NFR-DEPLOY-01 |
| KPI_11 | Cyber Range collaborative exercises | 0 → 5 | NFR-TRAIN-01, FR-INC-01..05 |
| KPI_12 | Collaborations with DIGITAL projects | 0 → 3 in 3 yrs | FR-CTI-01..06, NFR-ARC-02 |
| KPI_13 | Stakeholders using the dashboard | 0 → 75 in 2 yrs | FR-UX-01..05, FR-FRA-04 |
| KPI_14 | Outreach events | 0 → 10 | NFR-COMM-01 |
| KPI_15 | Certification frameworks delivered | 0 → 1 actionable | FR-CERT-01..04 |
| KPI_16 | IT solutions for handling exploited vulnerabilities (CRA scope) | 0 → ≥2 | FR-SCAN-02, FR-SCAN-04, FR-CTI-03 |
| KPI_17 | Successful cross-border forensic investigations | 0 → ≥2 | FR-INC-01..05, FR-AUD-04..05 |
| KPI_18 | Reduction in time to collect/process digital evidence | ≥30 % reduction | NFR-PERF-04, FR-INC-01..05 |
| KPI_19 | Project website operational by M3 | live, monthly updates | NFR-COMM-01 |
| KPI_20 | Visibility & dissemination reach | 2 000 visits / 500 followers | NFR-COMM-01 |

### 6.2 Key Exploitable Results (from `KER.png`)

| KER | Description | End-Users | Exploitation Strategy | Realised in CyberBridge by |
|-----|-------------|-----------|-----------------------|----------------------------|
| **KER.1** | AI-Driven compliance management tool | SMEs, SOC operators, regulators | SaaS subscription; OSS components for integration | FR-AI-01..07, FR-RSK-04, FR-COMP-02 |
| **KER.2** | Automated compliance tools | SMEs, critical-infra operators, compliance officers | Modular toolkit + SME subscription | FR-COMP-01..06, FR-FRA-01..06, FR-SCAN-01..06 |
| **KER.3** | Forensics investigation tools | SOC operators, researchers, law enforcement | Standalone or integrated; licensing + training | FR-AUD-03..05, FR-INC-01..05 |
| **KER.4** | Threat intelligence sharing tools | SOCs, CERTs, CSIRTs, critical-infra managers | Licensing for SOC integration; EU-wide TI interop | FR-CTI-01..06, FR-DW-01..04 |
| **KER.5** | Collaborative incident-response tool for SOCs | SOCs, CERTs, SMEs | Real-time collaboration + training programs | FR-INC-01..05, FR-CTI-05 |
| **KER.6** | CYBER-BRIDGE certification framework | Regulators, auditors, critical-infra operators | Consultancy + ENISA-aligned roadmaps | FR-CERT-01..04, FR-AUTH-03, FR-AUD-01..02 |
| **KER.7** | User-friendly dashboard | SMEs, SOC operators, critical-infra operators | SaaS with customisable visualisations | FR-UX-01..05, FR-FRA-04 |
| **KER.8** | Training & education program | SOC analysts, students, SMEs | Workshops, webinars, Cyber-Range packages | NFR-TRAIN-01, FR-UX-05 |
| **KER.9** | Ethical, legal & social compliance toolkit | Regulators, policymakers, SMEs | Guidelines, frameworks, workshops | NFR-LEG-01..04, NFR-PRIV-01..03 |

---

## 7. Requirements → Architecture Mapping

This section maps requirement clusters to the concrete architecture components shown in `docs/architecture-diagram.md`. Components are referenced by their canonical name in the architecture diagrams (e.g. `Backend (FastAPI)`, `llama.cpp`, `pgvector`).

### 7.1 By Functional Cluster

| Requirement cluster | Architecture component(s) | Architectural rationale |
|---------------------|---------------------------|-------------------------|
| **FR-FRA, FR-COMP, FR-RSK** (compliance & risk core) | `Backend (FastAPI)` Compliance Engine + Risk Management modules → `PostgreSQL` (Frameworks, Chapters, Objectives, Risks, Policies, junctions) | Centralised in the API tier so all gap analysis, certificate generation, and chain visualisation can be transactional. UUID PKs (NFR-ARC-03) keep cross-tenant joins safe. |
| **FR-SCAN-01..06** (security scanning) | `Scan Orchestrator` (in Backend) → `Nmap`, `OWASP ZAP`, `Semgrep`, `OSV`, `Syft` microservices → `NVD API` for CPE/CVE enrichment | Each scanner runs in its own container so they can be scaled, replaced, or upgraded independently (NFR-PERF-03). Findings persist via the backend so RBAC and tenant scoping remain server-side (NFR-SEC-03). |
| **FR-CTI-01..06** (threat intelligence) | `CTI Service` (internal :8000) → polls scanners via APScheduler → `MITRE ATT&CK` + `CISA KEV` feeds → `PostgreSQL` (`CtiIndicator`, `CtiAttackPattern`, `CtiKevEntry`, `CtiThreatFeed`) | CTI is decoupled into its own service so the user-facing scan path stays synchronous while threat aggregation runs asynchronously (NFR-PERF-01). The service is intentionally not exposed to the host network (NFR-SEC-05). |
| **FR-DW-01..04** (dark-web probing) | `Dark Web Scanner` (host :8030) → `Tor SOCKS5 :9050` → `PostgreSQL` queue (`DarkwebScan`, `DarkwebSettings`) | Tor and PDF generation are isolated from the API process to avoid leaking the egress route (NFR-SEC-05). Per-org `max_workers` and engine list satisfy NFR-PRIV-02. |
| **FR-AI-01..07** (RAG advisory) | `Embeddings Service` (all-MiniLM-L6-v2) + `pgvector` + `llama.cpp` (Phi-4 Q4_K_M) | Embeddings are a separate microservice so the API stays Python-pure and does not load PyTorch into every worker. pgvector keeps vectors next to the canonical objective rows (no extra datastore). llama.cpp exposes an OpenAI-compatible API (NFR-ARC-02) so any provider can be swapped in (FR-AI-03). |
| **FR-REG-01..04** (regulatory monitor) | `Regulatory Module` (in Backend) → `SearXNG` (host :8040) → `llama.cpp` for change summarisation → framework snapshots in `PostgreSQL` | SearXNG isolates the platform from search-engine quotas / blocking. LLM summarisation is reused (KER.1). Snapshots make the change loop reversible (FR-FRA-03). |
| **FR-AUD, FR-INC** (audit, evidence, incident, forensics) | `Audit Module` + `Incident Module` (in Backend) → `audit_attachments` volume → `FreeTSA` for RFC 3161 → `PostgreSQL` (chain-of-custody, legal hold) | RFC 3161 timestamping is delegated to FreeTSA so the platform is not its own time authority (NFR-LEG-03). Magic-link auditor sessions (FR-AUTH-03) reuse the same RBAC enforcement points (NFR-SEC-03). |
| **FR-DOC-01..04** (smart documentation) | `Backend` Documentation Generator → `llama.cpp` → `backend_uploads` volume → `pgvector` for retrieval | Document templates live in code; LLM is called with retrieved compliance/risk context so generated docs remain grounded (NFR-LEG-04). |
| **FR-UX-01..05** (UI) | `Frontend (React + TS + Vite + Ant Design)` → REST + JWT to Backend; Wouter routing; Zustand stores per domain | One store per domain (NFR-ARC-04) keeps components decoupled. SPA topology lets the same artefact serve operators, auditors, and pilots. |
| **FR-AUTH-01..05, FR-CERT-01..04** (identity & certification) | `Auth & RBAC Module` (in Backend) → JWT, SSO, magic links → `Role`/`User`/`Organisation` in `PostgreSQL` → Certificate hashing | All authorisation enforcement is in the API (NFR-SEC-03). Certificates are verified by SHA-256 hash so verification needs no shared secret (FR-CERT-03). |
| **FR-BAK-01..02** (backup/restore) | `Backend` backup module → `backend_backups` volume → `PostgreSQL` dump | Volume-mounted backups survive container recreation (NFR-AVAIL-02). |

### 7.2 By NFR

| NFR cluster | Architectural choice that satisfies it |
|-------------|----------------------------------------|
| **NFR-SEC** (security) | JWT + SSO + magic-link in the auth module; secrets via env vars; CTI/scanners on the internal Docker network only; pinned cryptography deps; RBAC enforced server-side. |
| **NFR-PRIV** (privacy & GDPR) | Per-`Organisation` scoping in every repository; dark-web service has tenant-level engine controls; data subject endpoints planned in compliance module. |
| **NFR-LEG** (legal & ethics) | Append-only chain-of-custody log; RFC 3161 timestamps via FreeTSA; LLM citations attached to advisory output. |
| **NFR-PERF** (performance) | Microservice fan-out for scanners; LLM response cache; async CTI ingestion path; pgvector for sub-second similarity search. |
| **NFR-AVAIL** (availability) | Tiered Docker startup with health checks; named volumes for stateful data; one-command restore. |
| **NFR-ARC** (architecture) | MVC backend layout; UUID PKs; OpenAI-compatible LLM API; Zustand domain stores; single `docker-compose up -d` deployment. |
| **NFR-DM** (data management) | Five named volumes; self-seeding DB; versioned migrations. |
| **NFR-TRAIN / NFR-COMM / NFR-EXP** (impact) | Demo flows in the UI; KPI/KER tracking baked into the dashboard; SaaS-ready container packaging. |

For the visual end-to-end view of these mappings, see `docs/architecture-diagram.md` — in particular the **High-Level System Architecture** and **Component Catalog** diagrams.

---

## 8. Interfaces, APIs & Integration Points

This section enumerates every interface CyberBridge exposes or consumes, the protocol it uses, and which requirement(s) it serves. All host ports are taken from `CLAUDE.md` and `docker-compose.yml`.

### 8.1 External (User-Facing) Interfaces

| Interface | Protocol / Port | Producer → Consumer | Purpose | Requirement(s) |
|-----------|-----------------|---------------------|---------|----------------|
| **Web UI** | HTTPS (host :5173) | Browser → React SPA | Primary stakeholder UI: dashboards, assessments, scans, CTI, incidents, audit, AI advisor. | FR-UX-01..05 |
| **Magic-link landing** | HTTPS (host :5173/auditor) | Browser → React SPA → Backend `/auth/magic` | External-auditor session bootstrap. | FR-AUTH-03, FR-AUD-01..02 |
| **PDF export** | HTTP download | Backend → Browser | Compliance reports, audit packs, forensic reports, dark-web reports, certificates. | FR-COMP-05, FR-DOC-02, FR-DW-04, FR-INC-04, FR-CERT-01 |
| **Certificate verification** | HTTPS GET `/certificates/verify/{hash}` | External verifier → Backend | Public SHA-256 lookup of a CyberBridge certificate. | FR-CERT-03 |

### 8.2 Internal REST APIs

The FastAPI app exposes ~54 router files. The actual router prefixes and notable paths (verified against `cyberbridge_backend/app/routers/`) are:

| Router prefix | Notable paths (method) | Purpose | Source file | Requirement(s) |
|---------------|------------------------|---------|-------------|----------------|
| `/auth` | `POST /token`; `GET /sso/google/login`; `GET /sso/google/callback`; `GET /sso/microsoft/login`; `GET /sso/microsoft/callback`; `GET /sso/providers` | Local JWT login + Google/Microsoft OAuth2. | `auth_controller.py` | FR-AUTH-01..02, FR-AUTH-04..05 |
| `/auditor-auth` | `POST /request-magic-link`; `POST /validate-magic-link`; `GET /external/login` | External-auditor magic-link auth. | `auditor_auth_controller.py` | FR-AUTH-03, FR-AUD-01..02 |
| `/frameworks` | CRUD; `GET /{id}/snapshots`; `POST /{id}/snapshots/{snapshot_id}/revert`; `POST /{id}/seed/{template}` | Framework hierarchy + snapshots + template seeding. | `frameworks_controller.py` | FR-FRA-01..06 |
| `/objectives` | CRUD; `POST /roadmap/{objective_id}`; `POST /roadmap/bulk` | Objectives + AI compliance-roadmap generation. | `objectives_controller.py` | FR-FRA-02, FR-AI-05 |
| `/assessments` | CRUD; `POST /{id}/complete` | Assessment lifecycle. | `assessments_controller.py` | FR-COMP-01 |
| `/answers` | CRUD | Answer to framework question. | `answers_controller.py` | FR-COMP-01 |
| `/evidence` | `POST /upload`; CRUD; `GET /{id}/download` | Evidence files (stored under `backend_uploads`). | `evidence_controller.py` | FR-AUD-03 |
| `/legal-holds` | `POST /evidence/{id}`; `GET /evidence/{id}`; `POST /evidence/{id}/lift` | Legal hold on evidence/engagements. | `legal_hold_controller.py` | FR-AUD-04, NFR-LEG-02 |
| `/custody` | `POST /{evidence_id}/transfer`; `GET /{evidence_id}/chain` | Hash-chained chain-of-custody. | `chain_of_custody_controller.py` | FR-AUD-05 |
| `/policies` | CRUD; `POST /{id}/approve`; `GET /{id}/alignments` | Policy management. | `policies_controller.py` | FR-COMP-06 |
| `/policy-aligner` | `POST /align` | AI-powered policy ↔ question alignment. | `policy_aligner_controller.py` | FR-AI-04 |
| `/risks` | CRUD; `POST /{id}/assessment` | Risk register & assessment. | `risks_controller.py` | FR-RSK-01, FR-RSK-04 |
| `/assets` | CRUD | Products / assets (CRA scope). | `assets_controller.py` | FR-RSK-02 |
| `/ce-marking` | `POST /checklists`; `POST /checklists/{id}/items`; `PUT .../items/{item_id}` | CE-marking checklists. | `ce_marking_controller.py` | FR-RSK-03 |
| `/scanners` | `GET /nmap/scan/{basic,fast,ports,all_ports,aggressive}`; `POST /zap/scan` (+ `/zap/scan-github`); `POST /semgrep/scan` (+ `/semgrep/scan-github`); `POST /osv/scan` (+ `/osv/scan-github`); `POST /syft/scan` (+ `/syft/scan-github`); `POST /history`; finding endpoints | Scanner orchestration + history/findings. | `scanners_controller.py` | FR-SCAN-01..06 |
| `/cti` | `GET /health`; `/stats`; `/timeline`; `/indicators`; `/attack-patterns`; `/malware`; `/{nmap,zap,semgrep,osv}/results`; `/suricata/alerts`; `/wazuh/alerts` | Proxy to internal `cti-service`. **No CISA-KEV or sync-state endpoint today.** | `cti_controller.py` | FR-CTI-01..05 |
| `/dark-web` | `POST /scan`; `GET /scans`; `GET /scan/{id}`; `GET /scan/{id}/json`; `GET /scan/{id}/pdf`; `DELETE /scan/{id}` | Tor-based dark-web scanning + PDF report. | `dark_web_controller.py` | FR-DW-01..04 |
| `/regulatory-monitor` | `POST /search`; `GET /changes`; `POST /changes/{id}/{acknowledge,dismiss}`; `GET/POST /settings`; `GET /scan-runs`; `POST /scan-runs/trigger`; `POST /frameworks/{id}/snapshots/{snapshot_id}/revert` | Regulatory change monitor over SearXNG. | `regulatory_monitor_controller.py` | FR-REG-01..04 |
| `/incidents` | CRUD; `POST /{id}/analyze`; `GET /statuses` | Incident management (timeline derived). | `incidents_controller.py` | FR-INC-01, FR-INC-04..05 |
| `/timestamps` | `GET /certificates/{id}`; `POST /certificates/{id}/verify`; `GET /sign-offs/{id}`; `POST /sign-offs/{id}/verify` | RFC 3161 timestamp issuance/verification (FreeTSA). | `timestamp_controller.py` | FR-INC-03, NFR-LEG-03 |
| `/compliance-advisor` | `POST /analyze`; `GET /history`; `GET /latest`; `DELETE /history/{id}` | URL-based AI compliance analysis (RAG). | `compliance_advisor_controller.py` | FR-AI-02 |
| `/chatbot` | `POST /stream` (SSE); `POST /embeddings/rebuild`; `GET /embeddings/status` | RAG chatbot (streaming). | `chatbot_controller.py` | FR-AI-01..02 |
| `/audit-export` | `POST /generate-report`; `GET /download/{id}` | Audit-report PDF generator. | `audit_export_controller.py` | FR-DOC-01, FR-INC-04 |
| `/certificates` | `POST /generate`; `GET /`; `GET /verify/{verification_hash}`; `GET /{id}/download`; `POST /{id}/revoke` | Compliance certificates (SHA-256 hash, 1-year validity). | `certificate_controller.py` | FR-CERT-01..04 |
| `/audit-engagements` | CRUD; `GET /summary` | External-audit engagements. | `audit_engagements_controller.py` | FR-AUD-01..02 |
| `/audit-review` | `GET /{engagement_id}/controls`; `POST /{engagement_id}/controls/{answer_id}/status` | Auditor review workflow. | `auditor_review_controller.py` | FR-AUD-01..02 |
| `/audit-comments` | CRUD | Threaded audit comments. | `audit_comments_controller.py` | FR-AUD-01..02 |
| `/audit-findings` | CRUD | Audit findings & remediation. | `audit_findings_controller.py` | FR-AUD-01..02 |
| `/audit-log-chain` | hash-chain query endpoints | Tamper-evident audit log. | `audit_log_chain_controller.py` | NFR-LEG-02 |
| `/backups` | `POST /create`; `GET /list`; `GET /download/{id}`; `POST /restore/{org_id}` | Encrypted backups + restore. | `backups_controller.py` | FR-BAK-01..02, NFR-AVAIL-02 |
| `/nvd` | `POST /sync`; `GET /sync-status`; `GET /cves` | NVD CVE database sync (daily 03:00). | `nvd_controller.py` | FR-SCAN-04 |
| `/euvd` | `POST /sync`; `GET /sync-status` | EU Vulnerability Database sync. | `euvd_controller.py` | FR-SCAN-04 |
| `/submissions` | `POST /`; `GET /`; `POST /{id}/feedback` | Regulatory submissions to authorities (seeded email directory). | `submission_controller.py` | FR-COMP-04 |
| `/dashboard` | `GET /metrics`; `/pie-chart-data`; `/frameworks`; `/assessments` | Aggregated dashboard data. | `home_controller.py` | FR-UX-02 |

All routes accept and return JSON. Mutating routes require a JWT in `Authorization: Bearer <token>` (NFR-SEC-01); admin routes additionally enforce `check_user_role(...)` server-side (NFR-SEC-03). Response shapes are defined by Pydantic DTOs in `app/dtos/` (NFR-ARC-01).

> **Known gaps surfaced during the verification pass:** no dedicated public `/health` endpoint on the main API (NFR-DEPLOY-03 🟡); no public CISA-KEV endpoint on `/cti` (FR-CTI-03 🟡); no LLM-query-hash cache (FR-AI-06 ⚪); no SAML SSO (FR-AUTH-02 🟡); no differential-privacy controls in dark-web probing (NFR-PRIV-02 ⚪); no consolidated DORA framework template in tree (NFR-LEG-01 🟡).

### 8.3 Service-to-Service Interfaces (Internal Docker Network)

| Producer → Consumer | Protocol / Port (container) | Purpose | Requirement(s) |
|---------------------|------------------------------|---------|----------------|
| Backend → `nmap:8000` | HTTP/JSON | Submit scan + collect results. | FR-SCAN-01 |
| Backend → `zap:8000` (and `:8080` proxy) | HTTP/JSON | Spider + active scan. | FR-SCAN-01 |
| Backend → `semgrep:8000` | HTTP/JSON (multipart upload) | SAST on uploaded source. | FR-SCAN-01 |
| Backend → `osv:8000` | HTTP/JSON | Lock-file dependency scan. | FR-SCAN-01 |
| Backend → `syft:8000` | HTTP/JSON | CycloneDX SBOM. | FR-SCAN-05 |
| Backend → `llamacpp:11435/v1/chat/completions` | OpenAI-compatible HTTP | LLM completions (Phi-4). | FR-AI-02..04 |
| Backend → `embeddings:8000/embed` | HTTP/JSON | Embed text → 384-dim vector. | FR-AI-01 |
| Backend → `cti-service:8000` | HTTP proxy | Read-through to CTI dashboards. | FR-CTI-01..06 |
| Backend → `dark-web-scanner:8001` | HTTP proxy | Submit/poll dark-web jobs. | FR-DW-01..04 |
| Regulatory module → `searxng:8080` | HTTP search API | Meta-search across engines. | FR-REG-01 |
| Backend → `db:5432` | SQLAlchemy / asyncpg | Primary data store. | NFR-ARC-03, NFR-DM-01 |
| CTI service → `db:5432` | SQLAlchemy | CTI tables. | FR-CTI-02..06 |
| Dark Web Scanner → `db:5432` | SQLAlchemy | Queue + settings. | FR-DW-02..03 |
| Embeddings → `db:5432` (pgvector) | SQL | Vector storage. | FR-AI-01 |
| CTI service → scanner microservices | HTTP poll (APScheduler 1 h) | Aggregate findings. | FR-CTI-01 |
| Dark Web Scanner → `tor:9050` | SOCKS5 | Egress to .onion search engines. | FR-DW-01 |

### 8.4 Outbound Integrations (Third-Party APIs & Feeds)

| Integration | Protocol | Direction | Purpose | Requirement(s) |
|-------------|----------|-----------|---------|----------------|
| **NVD API v2.0** | HTTPS REST | Outbound | CVE/CVSS lookup, CPE enrichment. | FR-SCAN-02, FR-SCAN-04 |
| **EU Vulnerability Database (EUVD)** | HTTPS REST | Outbound | EU-specific vuln sync. | FR-SCAN-04 |
| **MITRE ATT&CK** | HTTPS (CTI feed) | Outbound | Technique/tactic mapping. | FR-CTI-03..04 |
| **CISA KEV** | HTTPS (JSON feed) | Outbound | Known exploited vuln matching. | FR-CTI-03 |
| **FreeTSA.org** | HTTPS (RFC 3161) | Outbound | Tamper-evident timestamps for evidence/incidents. | NFR-LEG-03, FR-INC-03 |
| **Tor network** | SOCKS5 | Outbound | Dark-web search. | FR-DW-01 |
| **Search engines (Google, Bing, DDG, Scholar)** | HTTPS via SearXNG | Outbound | Regulatory change detection. | FR-REG-01 |
| **SMTP server** | SMTP/SMTPS | Outbound | Notification & magic-link delivery; ENISA submissions. | FR-AUTH-03, FR-COMP-04, FR-INC-01 |
| **External LLM providers** (OpenAI, Anthropic, Google, X AI, QLON) | HTTPS | Outbound (optional) | Pluggable model backends. | FR-AI-03 |

### 8.5 Persistence Interfaces

| Volume | Bound to | Purpose | Requirement(s) |
|--------|----------|---------|----------------|
| `postgres_data` | `db` container | Primary relational + pgvector store. | NFR-DM-01 |
| `backend_uploads` | `backend` container | User-uploaded source code, generated documents. | FR-DOC-04, FR-SCAN-05 |
| `audit_attachments` | `backend` container | Audit-engagement evidence. | FR-AUD-03..05, NFR-LEG-02 |
| `backend_backups` | `backend` container | Scheduled backups. | FR-BAK-01..02, NFR-AVAIL-02 |
| `zap_data` | `zap` container | ZAP session and config persistence. | FR-SCAN-01 |

### 8.6 Network Boundary Summary

- **Externally exposed (host):** 5173 (Frontend), 5174 (Backend), 5433 (Postgres), 8010–8016 (scanners + embeddings), 8030 (Dark Web), 8040 (SearXNG), 11435 (llama.cpp).
- **Internal-only (no host port):** `cti-service` — all access funnels through the Backend proxy, satisfying NFR-SEC-05.
- **Egress:** NVD, EUVD, MITRE, CISA, FreeTSA, Tor, search engines, SMTP, optional LLM providers.

---

## 9. Verification Pass — Summary of Gaps (2026-04-20)

The first reconciliation pass against the codebase produced this short list of gaps to track:

| ID | Gap | Severity | Fix sketch |
|----|-----|----------|------------|
| FR-CTI-03 | CISA-KEV feed not exposed via main API | Low | Add `GET /cti/kev` proxy + UI tile. |
| FR-CTI-06 | CTI sync-state not exposed | Low | Surface `cti-service` sync state via proxy. |
| FR-INC-01 | ENISA notification model exists but no public endpoint | Med | Add `POST /incidents/{id}/enisa-notification`. |
| FR-INC-02 | Forensic timeline derived (no dedicated `IncidentTimeline` model/route) | Low | Add a read-only timeline endpoint that joins existing tables. |
| FR-AI-04 | Smart Documentation Generator scattered | Med | Consolidate into one `/documents/*` router with templates. |
| FR-AI-06 | LLM responses not cached by query hash | Low | Add a `LLMResponseCache` table keyed by `sha256(prompt+model+context)`. |
| FR-AI-07 / NFR-LEG-04 | RAG citations not enforced in payload | Med | Wrap LLM output to include the retrieved objective IDs. |
| FR-AUTH-02 | SSO supports OAuth2 only (no SAML) | Low | Add SAML provider on demand. |
| FR-CERT-04 | DORA / IEC 62443 / NIST 800 templates not all in tree | Low | Add seed templates per framework. |
| FR-SCAN-06 | "Delta findings since last scan" not surfaced | Low | Reuse `finding_hash` to compute delta in a dedicated endpoint. |
| NFR-PRIV-02 | Differential privacy not implemented in dark-web | Low | Investigate per WP3.4 research note. |
| NFR-PRIV-03 | No subject-level export/erasure endpoints | Med | Add `/users/{id}/export`, `/users/{id}/erase` for GDPR Art. 15/17. |
| NFR-DEPLOY-03 | No `/health` endpoint on main API | Trivial | Add `GET /health` returning DB + dependency status. |
| NFR-USAB-01 | No formal WCAG 2.1 AA audit | Low | Run `axe` in CI; track A/AA findings. |
| NFR-DM-03 | Schema managed via `create_all`, not Alembic | Med | Introduce Alembic before next breaking schema change. |
| NFR-QA-01/02 | CI gating not formalised | Med | Add GitHub Actions for lint + tests + required reviews. |

## 10. Document Maintenance

- Re-run the verification pass whenever a new requirement is added, a KPI/KER is revised, or an architecture choice changes. Each row's **Status** column must be re-checked.
- Cross-reference every new requirement back to a Grant Agreement task (T1.1–T6.4) and at least one KPI or KER.
- Architecture-side changes should be reflected in `docs/architecture-diagram.md` and re-mapped in §7 here.
- Treat the **Status** column as code: a row that says ✅ but isn't actually true is a bug in this document.
