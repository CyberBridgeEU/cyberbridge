# Organization Admin API Reference

This document provides API reference information for organization administrators. Includes all User API endpoints plus administrative endpoints for managing users, frameworks, and organizational data.

## Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000
```

## Authentication

All endpoints require JWT token authentication.

```
Authorization: Bearer {access_token}
```

---

## User Management

### List Organization Users

```
POST /users/fetch_organisation_users
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "organisation_id": "uuid"
}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "role_id": "uuid",
    "role_name": "org_user",
    "organisation_id": "uuid",
    "status": "active",
    "last_activity": "2024-01-15T10:30:00Z"
  }
]
```

### Get All Users (Admin View)

```
GET /admin/all-users
Authorization: Bearer {token}
```

Returns all users in the organization for org_admins, or all system users for super_admins.

### Get Pending Users

```
GET /admin/pending-users
Authorization: Bearer {token}
```

### Approve User

```
POST /admin/approve-user/{user_id}
Authorization: Bearer {token}
```

### Reject User

```
POST /admin/reject-user/{user_id}
Authorization: Bearer {token}
```

### Update User Status

```
PUT /admin/update-user-status/{user_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "active"
}
```

Valid statuses: `pending_approval`, `active`, `inactive`

### Create User in Organization

```
POST /users/create_user_in_organisation
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "secure_password",
  "role_id": "role_uuid",
  "organisation_id": "org_uuid"
}
```

### Update User in Organization

```
POST /users/update_user_in_organisation
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "user_uuid",
  "name": "Updated Name",
  "role_id": "new_role_uuid"
}
```

### Get Online Users

```
GET /admin/online-users
Authorization: Bearer {token}
```

Returns users active within the last 3 minutes.

### Get All Roles

```
GET /users/get_all_roles
Authorization: Bearer {token}
```

---

## Framework Management

### List Frameworks

```
GET /frameworks/
Authorization: Bearer {token}
```

Returns frameworks for the current user's organization.

### Create Framework

```
POST /frameworks/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Custom Framework",
  "description": "Framework description",
  "organisation_id": "uuid"
}
```

### Get Framework Details

```
GET /frameworks/{framework_id}
Authorization: Bearer {token}
```

### Delete Framework

```
DELETE /frameworks/{framework_id}
Authorization: Bearer {token}
```

### Get Available Templates

```
GET /frameworks/templates
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "cra_template",
    "name": "Cyber Resilience Act (CRA)",
    "description": "EU CRA compliance framework"
  },
  {
    "id": "iso27001_template",
    "name": "ISO 27001:2022",
    "description": "Information Security Management System"
  },
  {
    "id": "nis2_template",
    "name": "NIS2 Directive",
    "description": "EU Network and Information Security Directive"
  }
]
```

### Seed Framework from Template

```
POST /frameworks/seed-template
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "template_id": "cra_template"
}
```

### Add Questions to Framework

```
POST /frameworks/questions
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "framework_id": "uuid",
  "question_ids": ["question_uuid_1", "question_uuid_2"]
}
```

---

## Chapter Management

### Get All Chapters

```
GET /objectives/get_all_chapters
Authorization: Bearer {token}
```

### Create Chapter

```
POST /objectives/create_chapter
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Chapter Name",
  "framework_id": "uuid",
  "order": 1
}
```

### Update Chapter

```
POST /objectives/update_chapter
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "chapter_uuid",
  "name": "Updated Chapter Name",
  "order": 2
}
```

### Delete Chapter

```
POST /objectives/delete_chapter
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "chapter_uuid"
}
```

---

## Objective Management

### Get All Objectives

```
GET /objectives/get_all_objectives
Authorization: Bearer {token}
```

### Get Objectives Checklist

```
GET /objectives/objectives_checklist
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id`: Filter by framework (optional)

### Get Objectives by Frameworks

```
GET /objectives/by_frameworks
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_ids`: Comma-separated framework UUIDs

### Create Objective

```
POST /objectives/create_objective
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Objective Title",
  "description": "Detailed requirements",
  "utilities": "Additional guidance",
  "chapter_id": "uuid",
  "compliance_status_id": "uuid",
  "order": 1
}
```

### Update Objective

```
POST /objectives/update_objective
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "objective_uuid",
  "title": "Updated Title",
  "description": "Updated description",
  "compliance_status_id": "uuid"
}
```

### Delete Objective

```
POST /objectives/delete_objective
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "objective_uuid"
}
```

### Get Compliance Statuses

```
GET /objectives/get_compliance_statuses
Authorization: Bearer {token}
```

**Response:**
```json
[
  {"id": "uuid", "status_name": "not assessed"},
  {"id": "uuid", "status_name": "not compliant"},
  {"id": "uuid", "status_name": "partially compliant"},
  {"id": "uuid", "status_name": "in review"},
  {"id": "uuid", "status_name": "compliant"},
  {"id": "uuid", "status_name": "not applicable"}
]
```

### Analyze Objectives with AI

```
POST /objectives/analyze_with_ai
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "objective_ids": ["uuid1", "uuid2"],
  "analysis_type": "gap_analysis"
}
```

---

## Question Management

### List Questions

```
GET /questions/
Authorization: Bearer {token}
```

### Get Questions for Frameworks

```
POST /questions/for_frameworks
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "framework_ids": ["uuid1", "uuid2"]
}
```

### Create Question

```
POST /questions/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "question_text": "Assessment question text",
  "assessment_type_id": "uuid",
  "is_mandatory": true
}
```

### Update Question

```
PUT /questions/{question_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Question

```
DELETE /questions/{question_id}
Authorization: Bearer {token}
```

---

## Assessment Management

### List Assessments

```
GET /assessments/
Authorization: Bearer {token}
```

### Get Assessments for User

```
GET /assessments/user/{user_id}
Authorization: Bearer {token}
```

### Get Assessments for Framework and User

```
POST /assessments/assessments_for_framework_and_user
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "framework_id": "uuid",
  "user_id": "uuid"
}
```

### Create Assessment

```
POST /assessments/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Q1 Assessment",
  "description": "Quarterly compliance assessment",
  "framework_id": "uuid",
  "assessment_type_id": "uuid"
}
```

### Update Assessment

```
PUT /assessments/{assessment_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Complete Assessment

```
PATCH /assessments/{assessment_id}/complete
Authorization: Bearer {token}
```

### Get Assessment Answers

```
GET /assessments/{assessment_id}/answers
Authorization: Bearer {token}
```

### Fetch Assessment Answers

```
POST /assessments/fetch_assessment_answers
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "assessment_id": "uuid"
}
```

### Delete Assessment Answers

```
POST /assessments/delete_assessment_answers
Authorization: Bearer {token}
Content-Type: application/json
```

### Get Assessment Evidence

```
GET /assessments/{assessment_id}/evidence
Authorization: Bearer {token}
```

### Get Incomplete Assessments

```
GET /assessments/incomplete-assessments
Authorization: Bearer {token}
```

### Send Incomplete Assessment Reminders

```
POST /assessments/send-incomplete-reminders
Authorization: Bearer {token}
```

---

## Policy Management

### List Policies

```
GET /policies
Authorization: Bearer {token}
```

### Get Policy Statuses

```
GET /policies/statuses
Authorization: Bearer {token}
```

### Create Policy

```
POST /policies
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Security Policy",
  "description": "Policy description",
  "status_id": "uuid"
}
```

### Update Policy

```
PUT /policies/{policy_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Policy

```
DELETE /policies/{policy_id}
Authorization: Bearer {token}
```

### Add Framework to Policy

```
POST /policies/add_framework
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "policy_id": "uuid",
  "framework_id": "uuid"
}
```

### Remove Framework from Policy

```
POST /policies/remove_framework
Authorization: Bearer {token}
Content-Type: application/json
```

### Add Objective to Policy

```
POST /policies/add_objective
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "policy_id": "uuid",
  "objective_id": "uuid",
  "order": 1
}
```

### Update Objective Order in Policy

```
POST /policies/update_objective_order
Authorization: Bearer {token}
Content-Type: application/json
```

### Remove Objective from Policy

```
POST /policies/remove_objective
Authorization: Bearer {token}
Content-Type: application/json
```

### Get Policy Files

```
GET /policies/files
Authorization: Bearer {token}
```

### Preview Policy Document

```
GET /policies/files/{filename}/preview
Authorization: Bearer {token}
```

---

## Risk Management

### List Risks

```
GET /risks
Authorization: Bearer {token}
```

### Get Risk Categories

```
GET /risks/categories
Authorization: Bearer {token}
```

### Get Risk Severities

```
GET /risks/severities
Authorization: Bearer {token}
```

### Get Risk Statuses

```
GET /risks/statuses
Authorization: Bearer {token}
```

### Create Risk

```
POST /risks
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Data Breach Risk",
  "description": "Risk of unauthorized data access",
  "category_id": "uuid",
  "likelihood_id": "uuid",
  "impact_id": "uuid",
  "residual_risk_id": "uuid",
  "status_id": "uuid"
}
```

### Update Risk

```
PUT /risks/{risk_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Risk

```
DELETE /risks/{risk_id}
Authorization: Bearer {token}
```

---

## Product Management

### List Products

```
GET /products
Authorization: Bearer {token}
```

### Get Product Statuses

```
GET /products/statuses
Authorization: Bearer {token}
```

### Get Economic Operators

```
GET /products/economic-operators
Authorization: Bearer {token}
```

### Get Product Types

```
GET /products/types
Authorization: Bearer {token}
```

### Get Criticality Levels

```
GET /products/criticalities
Authorization: Bearer {token}
```

### Create Product

```
POST /products
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Product Name",
  "version": "1.0.0",
  "description": "Product description",
  "license": "MIT",
  "status_id": "uuid",
  "economic_operator_id": "uuid",
  "product_type_id": "uuid",
  "criticality_id": "uuid"
}
```

### Update Product

```
PUT /products/{product_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Product

```
DELETE /products/{product_id}
Authorization: Bearer {token}
```

---

## Security Scanners

### Nmap Scans

```
GET /scanners/nmap/scan/basic?target={target}&use_llm=true
GET /scanners/nmap/scan/fast?target={target}&use_llm=true
GET /scanners/nmap/scan/ports?target={target}&ports={ports}&use_llm=true
GET /scanners/nmap/scan/aggressive?target={target}&use_llm=true
GET /scanners/nmap/scan/os?target={target}&use_llm=true
GET /scanners/nmap/scan/network?network={network}&use_llm=true
GET /scanners/nmap/scan/stealth?target={target}&use_llm=true
GET /scanners/nmap/scan/no_ping?target={target}&use_llm=true
Authorization: Bearer {token}
```

### Semgrep Scans

```
POST /scanners/semgrep/scan
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

Form Data: `file` (ZIP), `config`, `use_llm`

```
POST /scanners/semgrep/scan-github
Authorization: Bearer {token}
```

Form Data: `github_url`, `config`, `use_llm`, `github_token` (optional)

### OSV Scans

```
POST /scanners/osv/scan
POST /scanners/osv/scan-github
Authorization: Bearer {token}
```

### Scanner History

```
GET /scanners/history
GET /scanners/history/{scanner_type}
GET /scanners/history/details/{history_id}
DELETE /scanners/history/{history_id}
DELETE /scanners/history/clear/{scanner_type}
Authorization: Bearer {token}
```

---

## History & Audit Trail

### Get History Entries

```
GET /history/
Authorization: Bearer {token}
```

**Query Parameters:**
- `table_name`: Filter by table
- `action`: Filter by action (INSERT, UPDATE, DELETE)
- `user_id`: Filter by user
- `start_date`: From date
- `end_date`: To date
- `limit`: Maximum records
- `offset`: Pagination offset

### Get Record History

```
GET /history/record/{table_name}/{record_id}
Authorization: Bearer {token}
```

### Get Tracked Tables

```
GET /history/tables
Authorization: Bearer {token}
```

---

## User Sessions & Activity

### Get User Sessions

```
GET /admin/user-sessions
Authorization: Bearer {token}
```

**Query Parameters:**
- `start_date`: From date
- `end_date`: To date

### Get Visits Per Email

```
GET /admin/visits-per-email
Authorization: Bearer {token}
```

### Get Total Visits

```
GET /admin/total-visits
Authorization: Bearer {token}
```

---

## PDF Tracking

### Track PDF Download

```
POST /admin/track-pdf-download
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_type": "assessment_report",
  "document_name": "Q1 Report",
  "document_id": "uuid"
}
```

### Get PDF Download Statistics

```
GET /admin/total-pdf-downloads
GET /admin/pdf-downloads-per-type
Authorization: Bearer {token}
```

---

## AI Tools & Correlations

### Get Question Correlations

```
GET /ai-tools/correlations
Authorization: Bearer {token}
```

### Get Correlations for Question

```
GET /ai-tools/questions/{question_id}/correlations
Authorization: Bearer {token}
```

### Check Answer Conflicts

```
POST /ai-tools/check-answer-conflicts
Authorization: Bearer {token}
Content-Type: application/json
```

---

## Asset Management

### List Assets

```
GET /assets
Authorization: Bearer {token}
```

**Query Parameters:**
- `asset_type_id`: Filter by asset type (optional)
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 100)

### Get Asset by ID

```
GET /assets/{asset_id}
Authorization: Bearer {token}
```

### Create Asset

```
POST /assets
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Web Server",
  "description": "Primary production web server",
  "ip_address": "192.168.1.10",
  "asset_type_id": "uuid",
  "asset_status_id": "uuid",
  "economic_operator_id": "uuid",
  "criticality_id": "uuid"
}
```

### Update Asset

```
PUT /assets/{asset_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Asset

```
DELETE /assets/{asset_id}
Authorization: Bearer {token}
```

### Get Asset Types

```
GET /assets/types
Authorization: Bearer {token}
```

### Get Asset Type by ID

```
GET /assets/types/{asset_type_id}
Authorization: Bearer {token}
```

### Create Asset Type

```
POST /assets/types
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "IoT Device",
  "icon_name": "robot",
  "description": "Internet of Things device",
  "default_confidentiality": 3,
  "default_integrity": 3,
  "default_availability": 4,
  "default_asset_value": 3
}
```

### Update Asset Type

```
PUT /assets/types/{asset_type_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Asset Type

```
DELETE /assets/types/{asset_type_id}
Authorization: Bearer {token}
```

Only allowed if no assets are linked to the type.

### Seed Default Asset Types

```
POST /assets/types/seed-defaults
Authorization: Bearer {token}
```

Seeds the default 21 asset types for the current user's organization. Idempotent — skips types that already exist. Requires `org_admin` or `super_admin` role.

### Get Asset Statuses

```
GET /assets/statuses
Authorization: Bearer {token}
```

### Get Asset Categories

```
GET /assets/categories
Authorization: Bearer {token}
```

### Get Economic Operators

```
GET /assets/economic-operators
Authorization: Bearer {token}
```

### Get Criticalities

```
GET /assets/criticalities
Authorization: Bearer {token}
```

### Get Risks for Asset

```
GET /assets/{asset_id}/risks
Authorization: Bearer {token}
```

### Link Asset to Risk

```
POST /assets/{asset_id}/risks/{risk_id}
Authorization: Bearer {token}
```

### Unlink Asset from Risk

```
DELETE /assets/{asset_id}/risks/{risk_id}
Authorization: Bearer {token}
```

---

## CE Marking

### Get Product Types

```
GET /ce-marking/product-types
Authorization: Bearer {token}
```

### Get Document Types

```
GET /ce-marking/document-types
Authorization: Bearer {token}
```

### List Checklists

```
GET /ce-marking/checklists
Authorization: Bearer {token}
```

### Get Checklist Detail

```
GET /ce-marking/checklists/{checklist_id}
Authorization: Bearer {token}
```

### Get Checklist for Asset

```
GET /ce-marking/checklists/asset/{asset_id}
Authorization: Bearer {token}
```

### Create Checklist

```
POST /ce-marking/checklists
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "asset_id": "uuid",
  "product_type_id": "uuid"
}
```

### Update Checklist

```
PUT /ce-marking/checklists/{checklist_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Checklist

```
DELETE /ce-marking/checklists/{checklist_id}
Authorization: Bearer {token}
```

### Update Checklist Item

```
PUT /ce-marking/items/{item_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Add Custom Item to Checklist

```
POST /ce-marking/checklists/{checklist_id}/items
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Custom Item

```
DELETE /ce-marking/items/{item_id}
Authorization: Bearer {token}
```

Only custom items can be deleted.

### Update Document Status

```
PUT /ce-marking/documents/{status_id}
Authorization: Bearer {token}
Content-Type: application/json
```

---

## Gap Analysis

### Get Gap Analysis

```
GET /gap-analysis
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id`: Filter by framework (optional)

Returns comprehensive gap analysis data for compliance reporting.

---

## Compliance Advisor

### Analyze Website

```
POST /compliance-advisor/analyze
Authorization: Bearer {token}
Content-Type: application/json
```

Scrapes a company website and uses AI to recommend relevant compliance frameworks.

**Request Body:**
```json
{
  "url": "https://example-company.com"
}
```

**Response:**
```json
{
  "company_summary": "Example Company is a...",
  "recommended_frameworks": [
    {
      "name": "Cyber Resilience Act (CRA)",
      "relevance": "high",
      "reason": "..."
    }
  ]
}
```

### Get Analysis History

```
GET /compliance-advisor/history
Authorization: Bearer {token}
```

Returns the last 20 compliance advisor analyses for the user's organisation.

### Get Latest Analysis

```
GET /compliance-advisor/latest
Authorization: Bearer {token}
```

Returns the most recent compliance advisor analysis with full results.

### Delete Analysis History Record

```
DELETE /compliance-advisor/history/{history_id}
Authorization: Bearer {token}
```

---

## Risk Assessments

### List Risks with Assessments

```
GET /risks/assessments
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 100)

Returns all risks with their latest assessment scores.

### Get Assessments for Risk

```
GET /risks/{risk_id}/assessments
Authorization: Bearer {token}
```

### Get Latest Assessment for Risk

```
GET /risks/{risk_id}/assessments/latest
Authorization: Bearer {token}
```

### Get Specific Assessment

```
GET /risks/{risk_id}/assessments/{assessment_id}
Authorization: Bearer {token}
```

### Create Risk Assessment

```
POST /risks/{risk_id}/assessments
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "likelihood": 3,
  "impact": 4,
  "notes": "Assessment notes",
  "treatment_strategy": "mitigate"
}
```

### Update Risk Assessment

```
PUT /risks/{risk_id}/assessments/{assessment_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Risk Assessment

```
DELETE /risks/{risk_id}/assessments/{assessment_id}
Authorization: Bearer {token}
```

### Get Treatment Actions

```
GET /risks/{risk_id}/assessments/{assessment_id}/actions
Authorization: Bearer {token}
```

### Create Treatment Action

```
POST /risks/{risk_id}/assessments/{assessment_id}/actions
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "description": "Implement firewall rules",
  "due_date": "2024-06-01",
  "assigned_to": "security_team"
}
```

### Update Treatment Action

```
PUT /risks/{risk_id}/assessments/{assessment_id}/actions/{action_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Treatment Action

```
DELETE /risks/{risk_id}/assessments/{assessment_id}/actions/{action_id}
Authorization: Bearer {token}
```

---

## Incidents

### List Incidents

```
GET /incidents
Authorization: Bearer {token}
```

### Get Incident Statuses

```
GET /incidents/statuses
Authorization: Bearer {token}
```

### Create Incident

```
POST /incidents
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Data Breach Attempt",
  "description": "Unauthorized access detected",
  "incident_code": "INC-001",
  "incident_severity_id": "uuid",
  "incident_status_id": "uuid",
  "reported_by": "John Doe",
  "discovered_at": "2024-01-15T10:30:00Z",
  "containment_actions": "Blocked IP address",
  "root_cause": "Weak credentials",
  "remediation_steps": "Enforce MFA"
}
```

### Update Incident

```
PUT /incidents/{incident_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Incident

```
DELETE /incidents/{incident_id}
Authorization: Bearer {token}
```

### Analyze Incident with AI

```
POST /incidents/{incident_id}/analyze
Authorization: Bearer {token}
```

Uses AI to analyze the incident and saves the analysis result.

### Get Post-Market Metrics

```
GET /incidents/metrics/post-market
Authorization: Bearer {token}
```

### Get Frameworks for Incident

```
GET /incidents/{incident_id}/frameworks
Authorization: Bearer {token}
```

### Link Framework to Incident

```
POST /incidents/{incident_id}/frameworks/{framework_id}
Authorization: Bearer {token}
```

### Unlink Framework from Incident

```
DELETE /incidents/{incident_id}/frameworks/{framework_id}
Authorization: Bearer {token}
```

### Get Risks for Incident

```
GET /incidents/{incident_id}/risks
Authorization: Bearer {token}
```

### Link Risk to Incident

```
POST /incidents/{incident_id}/risks/{risk_id}
Authorization: Bearer {token}
```

### Unlink Risk from Incident

```
DELETE /incidents/{incident_id}/risks/{risk_id}
Authorization: Bearer {token}
```

### Get Assets for Incident

```
GET /incidents/{incident_id}/assets
Authorization: Bearer {token}
```

### Link Asset to Incident

```
POST /incidents/{incident_id}/assets/{asset_id}
Authorization: Bearer {token}
```

### Unlink Asset from Incident

```
DELETE /incidents/{incident_id}/assets/{asset_id}
Authorization: Bearer {token}
```

### Get Patches for Incident

```
GET /incidents/{incident_id}/patches
Authorization: Bearer {token}
```

### Create Patch

```
POST /incidents/{incident_id}/patches
Authorization: Bearer {token}
Content-Type: application/json
```

### Update Patch

```
PUT /incidents/patches/{patch_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Patch

```
DELETE /incidents/patches/{patch_id}
Authorization: Bearer {token}
```

### Get ENISA Notification

```
GET /incidents/{incident_id}/enisa
Authorization: Bearer {token}
```

### Create ENISA Notification

```
POST /incidents/{incident_id}/enisa
Authorization: Bearer {token}
Content-Type: application/json
```

### Update ENISA Notification

```
PUT /incidents/enisa/{notification_id}
Authorization: Bearer {token}
Content-Type: application/json
```

---

## Evidence Integrity

### Get Evidence Integrity Info

```
GET /evidence/{evidence_id}/integrity
Authorization: Bearer {token}
```

Returns integrity information (stored hash) for an evidence file.

### Verify Evidence Integrity

```
POST /evidence/{evidence_id}/integrity/verify
Authorization: Bearer {token}
```

Verifies that an evidence file's current state matches its stored hash.

### Download Integrity Receipt

```
GET /evidence/{evidence_id}/integrity/receipt
Authorization: Bearer {token}
```

Downloads a PDF integrity receipt for an evidence file.

### Get Evidence Version History

```
GET /evidence/{evidence_id}/versions
Authorization: Bearer {token}
```

**Response:**
```json
{
  "versions": [...],
  "current_version": 3,
  "total_versions": 3
}
```

---

## Audit Export

### Download Review Pack

```
GET /audit-engagements/{engagement_id}/export/review-pack
Authorization: Bearer {token}
```

Generates and downloads a comprehensive PDF review pack for an audit engagement. Includes engagement summary, controls review, findings, comments, and activity log.

### Download Evidence Package

```
GET /audit-engagements/{engagement_id}/export/evidence-package
Authorization: Bearer {token}
```

Generates and downloads a ZIP package containing all evidence files for an engagement. Includes an index file and integrity manifest.

### Download PBC List

```
GET /audit-engagements/{engagement_id}/export/pbc-list
Authorization: Bearer {token}
```

Generates and downloads a PBC (Prepared by Client) list as CSV. Lists all evidence requests and their current status.

### Export Activity Log

```
GET /audit-engagements/{engagement_id}/export/activity-log
Authorization: Bearer {token}
```

**Query Parameters:**
- `format`: Export format — `csv` (default) or `json`

---

## Audit Dashboard

### Get Engagement Dashboard

```
GET /audit-engagements/{engagement_id}/dashboard
Authorization: Bearer {token}
```

Returns comprehensive dashboard data including summary, findings, comments, progress, and activity.

### Get Findings Summary

```
GET /audit-engagements/{engagement_id}/dashboard/findings
Authorization: Bearer {token}
```

Returns findings summary by severity and status.

### Get Comments Summary

```
GET /audit-engagements/{engagement_id}/dashboard/comments
Authorization: Bearer {token}
```

Returns comments summary by type and status.

### Get Review Progress

```
GET /audit-engagements/{engagement_id}/dashboard/progress
Authorization: Bearer {token}
```

### Get Sign-Off Status

```
GET /audit-engagements/{engagement_id}/dashboard/sign-offs
Authorization: Bearer {token}
```

### Get Change Radar

```
GET /audit-engagements/{engagement_id}/change-radar
Authorization: Bearer {token}
```

**Query Parameters:**
- `prior_engagement_id`: ID of prior engagement to compare against (optional; defaults to linked prior engagement)

### Get Engagement History

```
GET /audit-engagements/{engagement_id}/change-radar/history
Authorization: Bearer {token}
```

Returns the complete history chain of engagements linked through prior_engagement_id.

### Get Change Timeline

```
GET /audit-engagements/{engagement_id}/change-radar/timeline
Authorization: Bearer {token}
```

Returns a timeline of changes across all engagement history.

### Get Organization Audit Summary

```
GET /audit-engagements/organization/{organisation_id}/summary
Authorization: Bearer {token}
```

Returns audit summary for an entire organization including total engagements, status breakdown, and aggregate metrics.

---

## Controls

### List Control Sets

```
GET /controls/control-sets
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 100)

### Create Control Set

```
POST /controls/control-sets
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "ISO 27001 Controls",
  "description": "Control set for ISO 27001"
}
```

### Get Control Statuses

```
GET /controls/statuses
Authorization: Bearer {token}
```

### Get Control Templates

```
GET /controls/templates
Authorization: Bearer {token}
```

Returns all available pre-loaded control set templates that can be imported.

### Get Control Template Detail

```
GET /controls/templates/{template_name}
Authorization: Bearer {token}
```

Returns detailed information about a specific control set template, including all controls.

### Import Controls from Template

```
POST /controls/import-template
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "template_name": "iso27001"
}
```

**Response:**
```json
{
  "success": true,
  "imported_count": 93,
  "failed_count": 0,
  "message": "Imported 93 controls from 'ISO 27001', skipped 0 duplicate(s)",
  "imported_control_ids": ["uuid1", "uuid2"],
  "errors": []
}
```

### List Controls

```
GET /controls
Authorization: Bearer {token}
```

**Query Parameters:**
- `control_set_id`: Filter by control set (optional)
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 1000)

### Get Control by ID

```
GET /controls/{control_id}
Authorization: Bearer {token}
```

### Create Control

```
POST /controls
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "A.5.1",
  "name": "Information Security Policy",
  "description": "Policies for information security",
  "control_set_id": "uuid",
  "control_status_id": "uuid"
}
```

### Update Control

```
PUT /controls/{control_id}
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete Control

```
DELETE /controls/{control_id}
Authorization: Bearer {token}
```

### Link Control to Risk

```
POST /controls/{control_id}/risks/{risk_id}?framework_id={framework_id}
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id` (required): Framework ID for this connection

### Unlink Control from Risk

```
DELETE /controls/{control_id}/risks/{risk_id}?framework_id={framework_id}
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id` (required): Framework ID for this connection

### Get Risks for Control

```
GET /controls/{control_id}/risks
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id`: Filter by framework ID (optional)

### Link Control to Policy

```
POST /controls/{control_id}/policies/{policy_id}?framework_id={framework_id}
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id` (required): Framework ID for this connection

### Unlink Control from Policy

```
DELETE /controls/{control_id}/policies/{policy_id}?framework_id={framework_id}
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id` (required): Framework ID for this connection

### Get Policies for Control

```
GET /controls/{control_id}/policies
Authorization: Bearer {token}
```

**Query Parameters:**
- `framework_id`: Filter by framework ID (optional)

---

## Cyber Threat Intelligence (CTI)

All CTI endpoints are proxied through the backend to the CTI microservice (port 8020).

### Get CTI Statistics

```
GET /cti/stats
Authorization: Bearer {token}
```

Returns aggregated indicator and sighting counts by source (suricata, wazuh, cape) plus totals including malware families and attack patterns.

### Get CTI Timeline

```
GET /cti/timeline?days=7
Authorization: Bearer {token}
```

Returns daily detection buckets over the specified number of days.

### Get CTI Indicators

```
GET /cti/indicators
Authorization: Bearer {token}
```

Returns recent indicators with id, name, confidence, source, labels, and created timestamp.

### Get Attack Patterns

```
GET /cti/attack-patterns
Authorization: Bearer {token}
```

Returns MITRE ATT&CK techniques with indicator counts and source attribution.

### Get Scanner CTI Results

```
GET /cti/nmap/results
GET /cti/zap/results
GET /cti/semgrep/results
GET /cti/osv/results
Authorization: Bearer {token}
```

Returns aggregated scanner findings. Each endpoint provides totals, category breakdowns, and recent items (max 50).

**Nmap Response:** Totals, open ports by count, services, protocols, hosts with discovered ports.

**ZAP Response:** Totals, risk distribution (High/Medium/Low/Info), CWE breakdown, top vulnerabilities.

**Semgrep Response:** Totals, severity distribution (ERROR/WARNING/INFO), OWASP categories, check IDs.

**OSV Response:** Totals, severity distribution (Critical/High/Medium/Low), ecosystems, top vulnerable packages.

### Ingest Scanner Results (Push)

```
POST /cti/ingest/{source}
Authorization: Bearer {token}
Content-Type: application/json
```

**Path Parameters:**
- `source`: One of `nmap`, `zap`, `semgrep`, `osv`

**Request Body:** Array of scanner result items (format varies by source).

**Response:**
```json
{
  "ingested": 15
}
```

### Get CTI Health

```
GET /cti/health
Authorization: Bearer {token}
```

---

## Dark Web Intelligence

### Create Dark Web Scan

```
POST /dark-web/scan
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "keyword": "company-name",
  "mp_units": 2,
  "limit": 3
}
```

### List Dark Web Scans

```
GET /dark-web/scans
Authorization: Bearer {token}
```

### Get Scan Result (JSON)

```
GET /dark-web/scan/json/{scan_id}
Authorization: Bearer {token}
```

### Download Scan PDF

```
GET /dark-web/download/pdf/{scan_id}
Authorization: Bearer {token}
```

### Delete Scan

```
DELETE /dark-web/scan/{scan_id}
Authorization: Bearer {token}
```

### Get Queue Overview

```
GET /dark-web/queue/overview
Authorization: Bearer {token}
```

### Get Worker Settings

```
GET /dark-web/settings/workers
Authorization: Bearer {token}
```

### Update Worker Settings

```
PUT /dark-web/settings/workers?max_workers=5
Authorization: Bearer {token}
```

Updates the maximum number of concurrent dark web scan workers (1-10).

### Get Available Engines

```
GET /dark-web/settings/engines
Authorization: Bearer {token}
```

Returns all 23 available dark web search engines with their enabled/disabled status.

### Update Enabled Engines

```
PUT /dark-web/settings/engines
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "enabled_engines": ["ahmia", "phobos", "torch", "haystack"]
}
```

### Dark Web Health

```
GET /dark-web/health
Authorization: Bearer {token}
```

---

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |
