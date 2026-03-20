# User API Reference

This document provides API reference information for standard users of the CyberBridge platform.

## Authentication

All API requests require authentication using a JWT token.

### Login

```
POST /api/token
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=your_email@example.com&password=your_password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:
```
Authorization: Bearer your_access_token
```

## Products

### List Products

```
GET /api/products
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Product Name",
    "version": "1.0.0",
    "description": "Product description",
    "license": "MIT",
    "sbom": "...",
    "status_id": "uuid",
    "economic_operator_id": "uuid",
    "product_type_id": "uuid",
    "criticality_id": "uuid"
  }
]
```

### Get Product by ID

```
GET /api/products/{product_id}
Authorization: Bearer {token}
```

### Create Product

```
POST /api/products
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
  "sbom": "Software Bill of Materials",
  "status_id": "uuid",
  "economic_operator_id": "uuid",
  "product_type_id": "uuid",
  "criticality_id": "uuid"
}
```

## Policies

### List Policies

```
GET /api/policies
Authorization: Bearer {token}
```

### Create Policy

```
POST /api/policies
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Policy Name",
  "description": "Policy description",
  "status_id": "uuid"
}
```

### Link Policy to Framework

```
POST /api/policies/{policy_id}/frameworks/{framework_id}
Authorization: Bearer {token}
```

### Link Policy to Objective

```
POST /api/policies/{policy_id}/objectives/{objective_id}
Authorization: Bearer {token}
```

## Risks

### List Risks

```
GET /api/risks
Authorization: Bearer {token}
```

### Create Risk

```
POST /api/risks
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Risk Name",
  "description": "Risk description",
  "risk_category_id": "uuid",
  "likelihood_id": "uuid",
  "risk_severity_id": "uuid",
  "residual_risk_id": "uuid",
  "risk_status_id": "uuid"
}
```

## Assessments

### List Assessments

```
GET /api/assessments
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Assessment Name",
    "description": "Assessment description",
    "framework_id": "uuid",
    "assessment_type_id": "uuid",
    "user_id": "uuid",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Assessment

```
POST /api/assessments
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Assessment Name",
  "description": "Assessment description",
  "framework_id": "uuid",
  "assessment_type_id": "uuid"
}
```

### Get Assessment Answers

```
GET /api/assessments/{assessment_id}/answers
Authorization: Bearer {token}
```

### Submit Answer

```
POST /api/answers
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "assessment_id": "uuid",
  "question_id": "uuid",
  "answer_text": "Your answer",
  "is_compliant": true
}
```

## Frameworks

### List Frameworks

```
GET /api/frameworks
Authorization: Bearer {token}
```

### Get Framework Objectives

```
GET /api/frameworks/{framework_id}/objectives
Authorization: Bearer {token}
```

## Evidence

### Upload Evidence

```
POST /api/evidence
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: The evidence file
- `answer_id`: UUID of the associated answer
- `description`: Description of the evidence

### Get Evidence for Answer

```
GET /api/answers/{answer_id}/evidence
Authorization: Bearer {token}
```

## User Profile

### Get Current User

```
GET /api/users/me
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role_name": "org_user",
  "organisation_id": "uuid",
  "organisation_name": "Organization Name"
}
```

### Change Password

```
POST /api/users/change-password
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

## Chatbot

### Stream Chat Response

```
POST /api/chatbot/stream
Authorization: Bearer {token}
Content-Type: application/json
```

Stream a chatbot response using Server-Sent Events (SSE). Uses the organisation's configured LLM provider. Conversation history is limited to the last 8 user messages.

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "How do I create a compliance assessment?"},
    {"role": "assistant", "content": "To create a compliance assessment..."},
    {"role": "user", "content": "What frameworks are supported?"}
  ]
}
```

**Response:** Server-Sent Events stream

```
data: {"content": "CyberBridge supports"}
data: {"content": " several compliance"}
data: {"content": " frameworks..."}
data: [DONE]
```

If AI is disabled for the organisation:
```
data: {"error": "AI is disabled for your organisation. Please contact your administrator."}
data: [DONE]
```

---

## Cyber Threat Intelligence (CTI)

### Get CTI Statistics

```
GET /cti/stats
Authorization: Bearer {token}
```

**Response:**
```json
{
  "suricata": {"indicators": 0, "sightings": 0},
  "wazuh": {"indicators": 0, "sightings": 0},
  "cape": {"indicators": 0, "sightings": 0},
  "totals": {"indicators": 150, "sightings": 0, "malware_families": 0, "attack_patterns": 25}
}
```

### Get CTI Timeline

```
GET /cti/timeline?days=7
Authorization: Bearer {token}
```

Returns daily detection counts by source over the specified number of days.

### Get CTI Indicators

```
GET /cti/indicators
Authorization: Bearer {token}
```

Returns recent indicators with metadata (name, confidence, source, labels, created timestamp).

### Get Attack Patterns

```
GET /cti/attack-patterns
Authorization: Bearer {token}
```

Returns MITRE ATT&CK techniques with counts and source attribution.

### Get Scanner CTI Results

```
GET /cti/nmap/results
GET /cti/zap/results
GET /cti/semgrep/results
GET /cti/osv/results
Authorization: Bearer {token}
```

Returns aggregated scanner findings normalized into the CTI data model. Each endpoint returns totals, breakdowns by category (risk, severity, CWE, OWASP, ecosystem), and recent findings.

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

**Response:**
```json
{
  "scan_id": "uuid",
  "status": "queued",
  "queue_position": 1,
  "estimated_wait_minutes": 2
}
```

### List Dark Web Scans

```
GET /dark-web/scans
Authorization: Bearer {token}
```

Returns all scans for the current user with status, timestamps, and metadata.

### Get Scan Result

```
GET /dark-web/scan/json/{scan_id}
Authorization: Bearer {token}
```

Returns detailed scan results including findings, summary, categorized findings, and engine status.

### Download Scan PDF Report

```
GET /dark-web/download/pdf/{scan_id}
Authorization: Bearer {token}
```

Downloads the generated PDF threat intelligence report for a completed scan.

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

**Response:**
```json
{
  "queue_length": 2,
  "processing_count": 1,
  "active_workers": 3,
  "max_workers": 3,
  "currently_processing": ["scan_id_1"]
}
```

---

## Error Responses

All endpoints may return error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to access this resource"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
