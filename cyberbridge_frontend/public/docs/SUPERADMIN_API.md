# Super Administrator API Reference

This document provides comprehensive API reference information for super administrators. Includes all User and Admin API endpoints plus system-wide administrative endpoints.

## Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000
```

## Authentication

All endpoints require JWT token authentication unless otherwise specified.

```
Authorization: Bearer {access_token}
```

### Login

```
POST /auth/token
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=admin@example.com&password=your_password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Organization Management

### List All Organizations

```
GET /users/get_all_organisations
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Organization Name",
    "description": "Organization description",
    "domain": "org-domain",
    "logo": "base64_encoded_logo",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Organization

```
POST /users/create_organisation
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "New Organization",
  "description": "Organization description",
  "domain": "new-org-domain"
}
```

### Delete Organization

```
DELETE /users/organisation/{organisation_id}
Authorization: Bearer {token}
```

**Warning:** This performs cascading deletes of all associated data including users, frameworks, assessments, policies, risks, and products.

---

## User Management

### List All Users (System-Wide)

```
GET /admin/all-users
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "first_name": "First",
    "last_name": "Last",
    "role_name": "org_user",
    "organisation_name": "Org Name",
    "status": "active",
    "last_activity": "2024-01-15T10:30:00Z"
  }
]
```

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

### Get Online Users

```
GET /admin/online-users
Authorization: Bearer {token}
```

Returns users active within the last 3 minutes.

### Create User

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

### Update User

```
POST /users/update_user_in_organisation
Authorization: Bearer {token}
Content-Type: application/json
```

### Delete User

```
DELETE /users/{user_id}
Authorization: Bearer {token}
```

### Get All Roles

```
GET /users/get_all_roles
Authorization: Bearer {token}
```

---

## User Sessions & Activity

### Get All User Sessions

```
GET /admin/user-sessions
Authorization: Bearer {token}
```

**Query Parameters:**
- `start_date`: Filter from date (YYYY-MM-DD)
- `end_date`: Filter to date (YYYY-MM-DD)

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

### Delete All User Sessions

```
DELETE /admin/user-sessions
Authorization: Bearer {token}
```

**Warning:** Super admin only. Clears all session history.

---

## AI Configuration

### Get Global LLM Settings

```
GET /settings/llm
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "ai_enabled": true,
  "default_provider": "llama_cpp",
  "custom_llm_url": "http://llm:8015/v1/chat/completions",
  "custom_llm_payload": "{...}"
}
```

### Update Global LLM Settings

```
PUT /settings/llm
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "ai_enabled": true,
  "default_provider": "llama_cpp",
  "custom_llm_url": "http://llm:8015/v1/chat/completions"
}
```

### Get Organization LLM Settings

```
GET /settings/org-llm/{organisation_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "organisation_id": "uuid",
  "llm_provider": "llama_cpp",
  "llama_cpp_url": "http://llm:8015",
  "llama_cpp_model": "phi-4",
  "qlon_url": null,
  "qlon_api_key": null,
  "qlon_use_tools": true,
  "is_enabled": false
}
```

### Create/Update Organization LLM Settings

```
PUT /settings/org-llm/{organisation_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "llm_provider": "qlon",
  "llama_cpp_url": null,
  "llama_cpp_model": null,
  "qlon_url": "https://qlon-api.example.com",
  "qlon_api_key": "your-api-key",
  "qlon_use_tools": true,
  "is_enabled": true
}
```

### Delete Organization LLM Settings

```
DELETE /settings/org-llm/{organisation_id}
Authorization: Bearer {token}
```

### Get Effective LLM Settings for Organization

```
GET /settings/org-llm/effective/{organisation_id}
Authorization: Bearer {token}
```

Returns the actual settings that will be used (org-specific or global defaults).

---

## Scanner Configuration

### Get Global Scanner Settings

```
GET /settings/scanners
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "scanners_enabled": true,
  "allowed_domains": ["domain1.com", "domain2.com"]
}
```

### Update Global Scanner Settings

```
PUT /settings/scanners
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "scanners_enabled": true,
  "allowed_domains": ["domain1.com", "domain2.com", "domain3.com"]
}
```

---

## SMTP Configuration

### Get SMTP Configuration

```
GET /settings/smtp-config
Authorization: Bearer {token}
```

**Response:**
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "email@gmail.com",
  "use_tls": true,
  "from_email": "noreply@cyberbridge.com",
  "from_name": "CyberBridge"
}
```

### Save SMTP Configuration

```
POST /settings/smtp-config
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "email@gmail.com",
  "smtp_password": "app_password",
  "use_tls": true,
  "from_email": "noreply@cyberbridge.com",
  "from_name": "CyberBridge"
}
```

### Send Test Email

```
POST /settings/test-email
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "recipient_email": "test@example.com"
}
```

---

## Domain Blacklist Management

### Get Blacklisted Domains

```
GET /settings/domain-blacklist
Authorization: Bearer {token}
```

### Add Domain to Blacklist

```
POST /settings/domain-blacklist
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "domain": "blocked-domain.com",
  "reason": "Security concern"
}
```

### Remove Domain from Blacklist

```
DELETE /settings/domain-blacklist/{domain}
Authorization: Bearer {token}
```

### Check Domain Status (Public)

```
GET /settings/domain-status/{domain}
```

### Bulk Import Domains from CSV

```
POST /settings/domain-blacklist/bulk-csv
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

### Download Sample CSV

```
GET /settings/domain-blacklist/sample-csv
Authorization: Bearer {token}
```

---

## Framework Management

### List All Frameworks

```
GET /frameworks/
Authorization: Bearer {token}
```

### Get All Frameworks for Cloning

```
GET /frameworks/all-for-cloning
Authorization: Bearer {token}
```

### Get Framework Templates

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
  }
]
```

### Seed Framework Template

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

### Clone Framework

```
POST /frameworks/clone
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "framework_ids": ["source_framework_uuid"],
  "organisation_id": "target_org_uuid",
  "custom_name": "Optional Custom Name"
}
```

### Delete Framework

```
DELETE /frameworks/{framework_id}
Authorization: Bearer {token}
```

### Set Framework Permissions

```
POST /settings/framework-permissions
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "organization_id": "uuid",
  "framework_ids": ["framework_uuid_1", "framework_uuid_2"]
}
```

### Get Framework Permissions

```
GET /settings/framework-permissions/{organization_id}
Authorization: Bearer {token}
```

### Get Framework Updates

```
GET /frameworks/{framework_id}/updates
Authorization: Bearer {token}
```

### Preview Framework Update

```
GET /frameworks/{framework_id}/updates/{version}/preview
Authorization: Bearer {token}
```

### Apply Framework Update

```
POST /frameworks/{framework_id}/updates/{version}/apply
Authorization: Bearer {token}
```

### Download Update Prompts Guide

```
GET /frameworks/update-prompts-guide
Authorization: Bearer {token}
```

---

## Security Scanners

### Nmap Scans

All Nmap endpoints support optional LLM analysis via `use_llm` parameter.

#### Basic Scan
```
GET /scanners/nmap/scan/basic?target={target}&use_llm=true
Authorization: Bearer {token}
```

#### Fast Scan
```
GET /scanners/nmap/scan/fast?target={target}&use_llm=true
Authorization: Bearer {token}
```

#### Port Scan
```
GET /scanners/nmap/scan/ports?target={target}&ports={ports}&use_llm=true
Authorization: Bearer {token}
```

#### All Ports Scan
```
GET /scanners/nmap/scan/all_ports?target={target}&use_llm=true
Authorization: Bearer {token}
```

#### Aggressive Scan
```
GET /scanners/nmap/scan/aggressive?target={target}&use_llm=true
Authorization: Bearer {token}
```

#### OS Detection Scan
```
GET /scanners/nmap/scan/os?target={target}&use_llm=true
Authorization: Bearer {token}
```

#### Network Scan
```
GET /scanners/nmap/scan/network?network={network}&use_llm=true
Authorization: Bearer {token}
```

#### Stealth Scan
```
GET /scanners/nmap/scan/stealth?target={target}&use_llm=true
Authorization: Bearer {token}
```

#### No Ping Scan
```
GET /scanners/nmap/scan/no_ping?target={target}&use_llm=true
Authorization: Bearer {token}
```

### Semgrep Scans

#### Scan ZIP File
```
POST /scanners/semgrep/scan
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: ZIP file containing source code
- `config`: Semgrep config (auto, p/ci, p/security-audit, p/owasp-top-ten)
- `use_llm`: Enable AI analysis (true/false)

#### Scan GitHub Repository
```
POST /scanners/semgrep/scan-github
Authorization: Bearer {token}
Content-Type: application/x-www-form-urlencoded
```

**Form Data:**
- `github_url`: Repository URL
- `config`: Semgrep config
- `use_llm`: Enable AI analysis
- `github_token`: PAT for private repos (optional)

### OSV Scans

#### Scan ZIP File
```
POST /scanners/osv/scan
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

#### Scan GitHub Repository
```
POST /scanners/osv/scan-github
Authorization: Bearer {token}
Content-Type: application/x-www-form-urlencoded
```

### Scanner History

#### Get All Scanner History
```
GET /scanners/history
Authorization: Bearer {token}
```

**Query Parameters:**
- `scanner_type`: Filter by type (nmap, semgrep, osv, zap)
- `user_id`: Filter by user
- `limit`: Maximum records
- `offset`: Pagination offset

#### Get History by Scanner Type
```
GET /scanners/history/{scanner_type}
Authorization: Bearer {token}
```

#### Get History Details
```
GET /scanners/history/details/{history_id}
Authorization: Bearer {token}
```

#### Delete History Record
```
DELETE /scanners/history/{history_id}
Authorization: Bearer {token}
```

#### Clear History by Scanner Type
```
DELETE /scanners/history/clear/{scanner_type}
Authorization: Bearer {token}
```

---

## AI Tools & Correlations

### Suggest Question Correlations
```
POST /ai-tools/suggest-correlations
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "framework_id_1": "uuid",
  "framework_id_2": "uuid",
  "assessment_type": "conformity"
}
```

### Correlate Two Questions
```
POST /ai-tools/correlate-questions
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "question_id_1": "uuid",
  "question_id_2": "uuid"
}
```

### Get All Correlations
```
GET /ai-tools/correlations
Authorization: Bearer {token}
```

### Get Correlations for Question
```
GET /ai-tools/questions/{question_id}/correlations
Authorization: Bearer {token}
```

### Delete Correlation
```
DELETE /ai-tools/correlations/{correlation_id}
Authorization: Bearer {token}
```

### Delete All Correlations
```
DELETE /ai-tools/correlations
Authorization: Bearer {token}
```

### Validate Correlations
```
GET /ai-tools/correlations/validate
Authorization: Bearer {token}
```

### Fix Invalid Correlations
```
POST /ai-tools/correlations/fix-invalid
Authorization: Bearer {token}
```

### Backfill Transitive Correlations
```
POST /ai-tools/backfill-transitive-correlations
Authorization: Bearer {token}
```

### Check Answer Conflicts
```
POST /ai-tools/check-answer-conflicts
Authorization: Bearer {token}
Content-Type: application/json
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
- `organisation_id`: Filter by organization
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

### Clear Organization History
```
DELETE /history/organization/{org_id}/clear-all
Authorization: Bearer {token}
```

---

## History Cleanup Configuration

### Get Cleanup Configuration
```
GET /admin/organizations/{org_id}/history-cleanup-config
Authorization: Bearer {token}
```

**Response:**
```json
{
  "enabled": true,
  "retention_days": 30,
  "cleanup_interval_hours": 24
}
```

### Update Cleanup Configuration
```
PUT /admin/organizations/{org_id}/history-cleanup-config
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "enabled": true,
  "retention_days": 30,
  "cleanup_interval_hours": 24
}
```

### Trigger Manual Cleanup
```
POST /admin/organizations/{org_id}/cleanup-history-now
Authorization: Bearer {token}
```

---

## PDF Download Tracking

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
  "document_name": "Q1 Assessment Report",
  "document_id": "uuid"
}
```

### Get Total PDF Downloads
```
GET /admin/total-pdf-downloads
Authorization: Bearer {token}
```

**Query Parameters:**
- `start_date`: From date
- `end_date`: To date

### Get PDF Downloads by Type
```
GET /admin/pdf-downloads-per-type
Authorization: Bearer {token}
```

---

## Database Management (Use with Caution)

### Truncate All Tables
```
GET /users/truncate_all_database_tables
Authorization: Bearer {token}
```

**Warning:** This will delete all data in the database. Use only for testing/development.

### Drop All Tables
```
GET /users/drop_all_database_tables
Authorization: Bearer {token}
```

**Warning:** This will drop all database tables. Requires re-seeding. Use only for testing/development.

---

## EUVD Vulnerability Database

### Get Exploited Vulnerabilities

```
GET /euvd/exploited
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 50, max 200)
- `days`: Filter by last N days (optional, 1-365)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "euvd_id": "EUVD-2024-0001",
      "description": "Vulnerability description",
      "date_published": "2024-01-15T00:00:00",
      "base_score": 9.8,
      "base_score_version": "3.1",
      "base_score_vector": "CVSS:3.1/AV:N/AC:L/...",
      "epss": 0.95,
      "assigner": "cve@mitre.org",
      "references": [...],
      "aliases": [...],
      "products": [...],
      "vendors": [...],
      "is_exploited": true,
      "is_critical": true,
      "category": "exploited"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```

### Get Critical Vulnerabilities

```
GET /euvd/critical
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 50, max 200)
- `days`: Filter by last N days (optional, 1-365)

### Get Latest Vulnerabilities

```
GET /euvd/latest
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 50, max 200)
- `days`: Filter by last N days (optional, 1-365)

### Search Vulnerabilities

```
GET /euvd/search
Authorization: Bearer {token}
```

**Query Parameters:**
- `text`: Free text search (optional)
- `product`: Filter by product (optional)
- `vendor`: Filter by vendor (optional)
- `fromScore`: Minimum CVSS score (optional)
- `toScore`: Maximum CVSS score (optional)
- `exploited`: Filter exploited only (optional, true/false)
- `page`: Page number (default 0)
- `size`: Page size (default 20, max 100)

### Trigger EUVD Sync

```
POST /euvd/sync
Authorization: Bearer {token}
```

Triggers a manual synchronization of vulnerability data from the EUVD API. Returns 409 if a sync is already in progress.

**Response:**
```json
{
  "message": "EUVD sync started",
  "sync_id": "uuid"
}
```

### Get Sync Status

```
GET /euvd/sync/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "started_at": "2024-01-15T10:00:00",
  "completed_at": "2024-01-15T10:05:00",
  "vulns_processed": 500,
  "vulns_added": 50,
  "vulns_updated": 30,
  "error_message": null
}
```

### Get Sync History

```
GET /euvd/sync/history
Authorization: Bearer {token}
```

**Query Parameters:**
- `limit`: Maximum records (default 20, max 100)

### Delete Sync History

```
DELETE /euvd/sync/history
Authorization: Bearer {token}
```

Super admin only. Deletes all EUVD sync history records.

### Get EUVD Statistics

```
GET /euvd/stats
Authorization: Bearer {token}
```

Returns cache statistics for the EUVD vulnerability database.

### Get EUVD Settings

```
GET /euvd/settings
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "sync_enabled": true,
  "sync_interval_hours": 24,
  "sync_interval_seconds": 0,
  "last_sync_at": "2024-01-15T10:05:00",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-15T10:05:00"
}
```

### Update EUVD Settings

```
PUT /euvd/settings
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "sync_enabled": true,
  "sync_interval_hours": 12,
  "sync_interval_seconds": 0
}
```

Updates sync settings and reschedules the background sync job accordingly.

### Delete All Vulnerabilities

```
DELETE /euvd/vulnerabilities/all
Authorization: Bearer {token}
```

Deletes all cached vulnerability data.

### Delete Vulnerabilities by Date Range

```
DELETE /euvd/vulnerabilities
Authorization: Bearer {token}
```

**Query Parameters:**
- `date_from`: Start date in YYYY-MM-DD format (optional)
- `date_to`: End date in YYYY-MM-DD format (optional)

At least one of `date_from` or `date_to` is required.

---

## Backups

### Get Backup Configuration

```
GET /backups/config/{org_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "backup_enabled": true,
  "backup_frequency": "daily",
  "backup_retention_years": 5,
  "last_backup_at": "2024-01-15T02:00:00Z",
  "last_backup_status": "completed"
}
```

### Update Backup Configuration

```
PUT /backups/config/{org_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "backup_enabled": true,
  "backup_frequency": "weekly",
  "backup_retention_years": 10
}
```

Valid frequencies: `daily`, `weekly`, `monthly`. Retention years must be between 1 and 100.

### List Backups

```
GET /backups/list/{org_id}
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip`: Pagination offset (default 0)
- `limit`: Maximum records (default 100)

**Response:**
```json
{
  "backups": [
    {
      "id": "uuid",
      "filename": "backup_2024-01-15.zip",
      "filepath": "/backups/org_uuid/backup_2024-01-15.zip",
      "backup_type": "manual",
      "status": "completed",
      "created_at": "2024-01-15T02:00:00Z"
    }
  ],
  "total_count": 15
}
```

### Create Manual Backup

```
POST /backups/create/{org_id}
Authorization: Bearer {token}
```

Creates a manual backup for the specified organization.

### Download Backup

```
GET /backups/download/{backup_id}
Authorization: Bearer {token}
```

Downloads the backup file as a ZIP archive.

### Restore from Backup

```
POST /backups/restore/{org_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Warning:** This operation will replace existing organization data.

**Request Body:**
```json
{
  "backup_id": "uuid",
  "confirm": true
}
```

The `confirm` field must be set to `true` to proceed with the restore.

### Delete Backup

```
DELETE /backups/{backup_id}
Authorization: Bearer {token}
```

Deletes both the backup file and database record.

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
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

### Permission Errors
```json
{
  "detail": "Super admin privileges required"
}
```

```json
{
  "detail": "Not authorized to access this organization"
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Standard endpoints**: 100 requests per minute
- **Scanner endpoints**: 10 requests per minute
- **AI endpoints**: 20 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642345678
```
