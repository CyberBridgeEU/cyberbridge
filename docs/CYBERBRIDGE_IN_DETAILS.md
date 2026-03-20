# CyberBridge in Details

**Version:** 10.0
**Document Date:** February 2025
**Classification:** Technical Documentation
**Author:** CyberBridge Development Team

---

## Table of Contents

1. [System Architecture and Core Components](#1-system-architecture-and-core-components)
2. [Data and API Layer](#2-data-and-api-layer)
3. [Automation Logic and Implementation](#3-automation-logic-and-implementation)
4. [Deployment, Testing, and Validation](#4-deployment-testing-and-validation)
5. [Platform Requirements](#5-platform-requirements)
6. [Integration Plan](#6-integration-plan)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Version 10 Features](#8-version-10-features)
9. [Role Descriptions and Permission Matrix](#9-role-descriptions-and-permission-matrix)

---

## 1. System Architecture and Core Components

### 1.1 Overview

CyberBridge is a comprehensive cybersecurity compliance assessment platform designed with a microservices architecture. The system enables organizations to manage compliance frameworks, conduct security assessments, manage risks and policies, and integrate with security scanning tools for automated vulnerability detection.

### 1.2 Technology Stack

#### Frontend Layer
- **Framework:** React 19.0.0 with TypeScript
- **Build Tool:** Vite 6.2.0
- **UI Library:** Ant Design 5.24.4
- **State Management:** Zustand 5.0.3
- **Routing:** Wouter 3.6.0
- **Charting:** React Google Charts 5.2.1, Ant Design Plots 2.6.5
- **PDF Generation:** jsPDF 3.0.1, html2pdf.js 0.10.3, html2canvas 1.4.1

#### Backend Layer
- **API Framework:** FastAPI (async Python framework)
- **ORM:** SQLAlchemy with async support
- **Database:** PostgreSQL 16+ with UUID primary keys
- **Authentication:** JWT-based OAuth2 with Bearer tokens
- **Password Hashing:** Passlib with CryptContext
- **Email:** SMTP integration for user verification and notifications
- **Background Jobs:** APScheduler (AsyncIOScheduler)

#### Database Layer
- **Primary Database:** PostgreSQL 16+
- **Port Mapping:** 5433:5432 (host:container)
- **Data Persistence:** Docker volumes
- **Migration Tool:** Alembic
- **Connection Pooling:** SQLAlchemy engine with connection pool management

#### Security Scanning Services
- **OWASP ZAP Proxy:** Web application security scanner (Port 8010)
- **Nmap:** Network discovery and security auditing (Port 8011)
- **OSV Scanner:** Open-source vulnerability scanner (Port 8012)
- **Semgrep:** Static code analysis tool (Port 8013)
- **Syft:** SBOM (Software Bill of Materials) generator (Port 8014)

#### AI/LLM Layer
- **Default Platform:** llama.cpp (self-hosted)
- **Supported Providers:** llama.cpp, OpenAI, Anthropic, Google, X AI, QLON
- **Default Model:** phi-4 (14 billion parameters) via llama.cpp
- **Port:** 8015 (llama.cpp)
- **Memory Allocation:** 13GB limit (llama.cpp)
- **Configuration:** Per-organization LLM provider selection
- **Use Cases:**
  - Question correlation analysis between frameworks
  - Security scan result analysis (ZAP, Nmap, Semgrep, OSV)
  - Compliance objective recommendations
  - Compliance Advisor for framework guidance
  - AI-powered policy alignment suggestions
  - Vulnerability remediation suggestions

#### Cyber Threat Intelligence (CTI) Layer
- **CTI Service:** Lightweight FastAPI microservice (port 8020)
- **Storage:** PostgreSQL (shared database, `cti_`-prefixed tables)
- **Connectors:** 4 built-in (Nmap, ZAP, Semgrep, OSV) with scheduled polling and push ingestion
- **Threat Feeds:** MITRE ATT&CK (weekly sync), CISA KEV (daily sync)
- **Features:**
  - Unified threat intelligence view
  - MITRE ATT&CK mapping
  - Multi-source correlation
  - Scanner result aggregation and deduplication

#### Dark Web Intelligence Layer
- **Scanner API:** FastAPI (port 8030)
- **Queue:** Redis 7 with FIFO processing
- **Tor Integration:** SOCKS5 proxy for anonymous dark web access
- **Search Engines:** 23 configurable dark web search engines
- **Features:**
  - Dark web keyword scanning
  - Categorized findings (passwords, databases, credentials, emails, leaks)
  - PDF/JSON reporting
  - Configurable workers (1-10)

### 1.3 Architecture Patterns

#### Microservices Architecture

The system follows a tiered microservices architecture:

**Tier 1: Database Layer**
- PostgreSQL database
- Initializes first with health checks
- All services depend on database availability

**Tier 2: ZAP Service**
- OWASP ZAP Proxy with 30-second startup time
- Acts as gateway for security scanning operations

**Tier 3: Parallel Services**
- llama.cpp LLM service
- Nmap scanner
- OSV scanner
- Semgrep scanner
- Syft SBOM generator
- All start after ZAP is healthy

**Tier 3.5: CTI & Dark Web Services**
- CTI Service (port 8020) — stores scanner results, serves threat intelligence
- Redis Dark Web (scan queue)
- Dark Web Scanner (port 8030)

**Tier 4: Backend API**
- CyberBridge FastAPI backend
- Starts after all Tier 3 services are healthy
- Coordinates all microservices
- Port: 5174 (mapped from container 8000)

**Tier 5: Frontend**
- React SPA served via static web server
- Starts last, after backend is healthy
- Port: 5173

#### MVC Pattern (Backend)

```
cyberbridge_backend/
├── models/          # SQLAlchemy ORM models (Data Layer)
├── repositories/    # Data access layer (DAL)
├── services/        # Business logic layer
├── routers/         # API controllers/endpoints (Presentation Layer)
├── dtos/           # Pydantic schemas for validation
├── database/       # Database configuration
├── middleware/     # Request/response interceptors
├── seeds/          # Database initialization
└── config/         # Environment configuration
```

#### Frontend Architecture

```
cyberbridge_frontend/src/
├── pages/          # Route components (page-level)
├── components/     # Reusable UI components
├── store/          # Zustand state management
├── constants/      # API URLs, grid columns, menu items
├── utils/          # Helper functions, PDF generation
└── assets/         # Images, logos, icons
```

### 1.4 Service Communication

#### Internal Docker Network
- **Network Name:** cyberbridge-network
- **Driver:** Bridge
- **DNS Resolution:** Service names resolve to container IPs
- **Scanner URLs (internal):**
  - `http://nmap:8000`
  - `http://semgrep:8000`
  - `http://osv:8000`
  - `http://zap:8000`
  - `http://syft:8000`
  - `http://llm:8015`

#### External Access (Production)
- **Frontend:** Port 5173
- **Backend API:** Port 5174
- **Database:** Port 5433 (mapped from 5432)
- **Scanners:** Ports 8010-8014 (optional exposure)
- **LLM:** Port 8015

### 1.5 Security Architecture

#### Authentication Flow
1. User submits credentials via `/auth/token` endpoint
2. Backend validates credentials against database
3. JWT token generated with user email and role
4. Token includes expiration (configurable, default: 60 minutes)
5. Client stores token and includes in `Authorization: Bearer <token>` header
6. Middleware validates token on each protected request
7. User activity tracked for online status

#### Role-Based Access Control (RBAC)
- **Middleware:** Custom dependency injection for role checking
- **Decorator Pattern:** `@Depends(check_user_role(["super_admin", "org_admin"]))`
- **Granular Permissions:** Endpoint-level authorization
- **Organization Isolation:** Org admins restricted to their organization data

#### Data Protection
- **Passwords:** Hashed using Passlib (bcrypt)
- **Database Encryption:** PostgreSQL native encryption
- **TLS/SSL:** Configurable for SMTP and external APIs
- **CORS:** Configurable allowed origins
- **SQL Injection Prevention:** SQLAlchemy parameterized queries
- **XSS Prevention:** Frontend input sanitization via Ant Design

### 1.6 Scalability Features

#### Horizontal Scaling
- Stateless backend services (JWT-based auth)
- Database connection pooling
- Async/await pattern for I/O operations
- Docker Compose ready for Kubernetes migration

#### Performance Optimization
- **Frontend:**
  - Vite build optimization
  - Code splitting
  - Lazy loading
  - React memoization
- **Backend:**
  - Async FastAPI endpoints
  - Database query optimization
  - Indexed UUID primary keys
  - Selective eager loading

#### Resource Management
- **LLM Service:**
  - Memory limits (13GB)
  - Configurable timeout (default: 300s)
  - Queue management (max 4 concurrent)
  - Keep-alive duration (10 minutes)
- **Scanner Services:**
  - Individual health checks
  - Timeout configuration
  - Graceful failure handling

---

## 2. Data and API Layer

### 2.1 Database Schema

#### Core Entities (88+ Tables)

**User Management**
- `users` - User accounts with email, hashed password, role, organization, status
- `roles` - System roles (super_admin, org_admin, org_user, guest_auditor, auditor_lead)
- `organisations` - Multi-tenant organization structure
- `user_sessions` - Login/logout tracking for analytics
- `user_verifications` - Email verification tokens for registration
- `domain_blacklist` - Blocked email domains

**Framework Management**
- `frameworks` - Compliance frameworks (ISO 27001, NIS2, CRA, etc.)
- `chapters` - Framework chapters/sections
- `objectives` - Specific compliance objectives/controls
- `compliance_statuses` - Objective compliance state
- `framework_updates` - Version tracking for framework updates
- `organization_framework_permissions` - Seeding permissions

**Assessment System**
- `assessment_types` - Internal Audit, External Audit, Self-Assessment
- `questions` - Compliance questions
- `framework_questions` - Junction table (many-to-many)
- `assessments` - Assessment instances with scope
- `answers` - User responses to questions
- `evidence` - File uploads for answers
- `question_correlations` - AI-powered cross-framework question mapping

**Scope Management**
- `scopes` - Scope types (Product, Organization, Asset, Project, Process, Other)
- Assessments, Risks, and Correlations support scoping

**Policy Management**
- `policies` - Policy documents
- `policy_statuses` - Draft, Review, Ready for Approval, Approved
- `policy_frameworks` - Policy-framework associations
- `policy_objectives` - Policy-objective mappings

**Product Registry**
- `products` - Product catalog with SBOM
- `product_types` - Hardware, Software
- `product_statuses` - Live, Testing
- `economic_operators` - Manufacturer, Importer, Distributor
- `criticalities` - EU CRA criticality classifications
- `criticality_options` - Specific criticality values

**Risk Management**
- `risks` - Risk register with scope support
- `risk_categories` - Predefined risk categories
- `risk_severity` - Low, Medium, High, Critical
- `risk_status` - Reduce, Avoid, Transfer, Share, Accept, Remediated

**Audit & History**
- `history` - Comprehensive audit log (insert/update/delete)
- `pdf_downloads` - PDF export tracking
- `scanner_history` - Security scan results archive

**Configuration**
- `smtp_configurations` - Email server settings
- `llm_settings` - AI service configuration
- `scanner_settings` - Security scanner permissions

### 2.2 Key Relationships

#### User-Organization Hierarchy
```
Organisation (1) ─── (N) User
Role (1) ─── (N) User
```

#### Framework-Assessment Workflow
```
Organisation (1) ─── (N) Framework
Framework (1) ─── (N) Chapter ─── (N) Objective
Framework (N) ─── (N) Question (via framework_questions)
Assessment (N) ─── (1) Framework
Assessment (1) ─── (N) Answer ─── (N) Evidence
Answer (N) ─── (1) Question
```

#### Policy-Framework Linkage
```
Policy (N) ─── (N) Framework (via policy_frameworks)
Policy (N) ─── (N) Objective (via policy_objectives)
Answer (N) ─── (1) Policy (optional assignment)
```

#### Risk-Product Association
```
Product (1) ─── (1) ProductType
ProductType (1) ─── (N) Risk
Risk (1) ─── (1) RiskSeverity (likelihood, severity, residual)
Risk (1) ─── (1) RiskStatus
```

#### Scope Entity Relationships
```
Scope (1) ─── (N) Assessment (scope_id + scope_entity_id)
Scope (1) ─── (N) Risk (scope_id + scope_entity_id)
Scope (1) ─── (N) QuestionCorrelation (scope_id + scope_entity_id)
```

### 2.3 API Architecture

#### RESTful Endpoints

**Authentication & User Management** (`/auth`, `/users`)
- `POST /auth/token` - Login (OAuth2 password flow)
- `POST /auth/register` - User registration with org selection
- `POST /auth/register-with-verification` - Email-verified registration
- `GET /auth/verify-email` - Email verification callback
- `POST /auth/forgot-password` - Password reset request
- `POST /auth/logout` - Session termination
- `GET /users/me` - Current user profile
- `PUT /users/me` - Update user profile
- `PUT /users/change-password` - Password change

**Admin Operations** (`/admin`)
- `GET /admin/all-users` - List users (filtered by role)
- `GET /admin/pending-users` - Approval queue
- `POST /admin/approve-user/{id}` - Approve registration
- `POST /admin/reject-user/{id}` - Reject registration
- `PUT /admin/update-user-status/{id}` - Change user status
- `GET /admin/online-users` - Active users (last 3 minutes)
- `GET /admin/user-sessions` - Login history
- `GET /admin/visits-per-email` - Analytics
- `GET /admin/total-visits` - Usage metrics
- `DELETE /admin/user-sessions` - Clear session history (super_admin only)
- `GET /admin/organizations/{id}/history-cleanup-config` - Get cleanup settings
- `PUT /admin/organizations/{id}/history-cleanup-config` - Update cleanup settings
- `POST /admin/organizations/{id}/cleanup-history-now` - Manual cleanup trigger
- `POST /admin/track-pdf-download` - Track PDF exports
- `GET /admin/total-pdf-downloads` - PDF export metrics
- `GET /admin/pdf-downloads-per-type` - PDF breakdown by type

**Framework Management** (`/frameworks`)
- `GET /frameworks` - List frameworks (org-filtered)
- `GET /frameworks/{id}` - Framework details
- `POST /frameworks` - Create framework
- `PUT /frameworks/{id}` - Update framework
- `DELETE /frameworks/{id}` - Delete framework
- `GET /frameworks/{id}/chapters` - Chapter list
- `POST /frameworks/{id}/chapters` - Create chapter
- `GET /frameworks/{id}/questions` - Associated questions
- `POST /frameworks/{id}/questions` - Add question to framework
- `DELETE /frameworks/{framework_id}/questions/{question_id}` - Remove question
- `POST /frameworks/seed-from-excel` - Bulk framework import
- `GET /frameworks/updates` - Available framework updates
- `POST /frameworks/updates/{id}/apply` - Apply framework update

**Question Management** (`/questions`)
- `GET /questions` - List all questions
- `GET /questions/{id}` - Question details
- `POST /questions` - Create question
- `PUT /questions/{id}` - Update question
- `DELETE /questions/{id}` - Delete question

**Assessment Management** (`/assessments`)
- `GET /assessments` - List assessments (org-filtered, scope-aware)
- `GET /assessments/{id}` - Assessment details
- `POST /assessments` - Create assessment
- `PUT /assessments/{id}` - Update assessment
- `DELETE /assessments/{id}` - Delete assessment
- `POST /assessments/{id}/complete` - Mark assessment complete
- `GET /assessments/{id}/progress` - Completion percentage

**Answer Management** (`/answers`)
- `GET /answers` - List answers (filtered by assessment)
- `GET /answers/{id}` - Answer details
- `POST /answers` - Submit answer
- `PUT /answers/{id}` - Update answer
- `DELETE /answers/{id}` - Delete answer
- `POST /answers/bulk` - Bulk answer submission
- `POST /answers/{id}/evidence` - Upload evidence file
- `DELETE /answers/evidence/{evidence_id}` - Remove evidence

**Objective Management** (`/objectives`)
- `GET /objectives` - List objectives (filtered by framework)
- `GET /objectives/{id}` - Objective details
- `POST /objectives` - Create objective
- `PUT /objectives/{id}` - Update objective
- `DELETE /objectives/{id}` - Delete objective
- `GET /objectives/compliance-summary` - Compliance statistics

**Product Management** (`/products`)
- `GET /products` - List products (org-filtered)
- `GET /products/{id}` - Product details
- `POST /products` - Register product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product
- `GET /products/types` - Product types
- `GET /products/statuses` - Product statuses
- `GET /products/economic-operators` - Economic operators
- `GET /products/criticalities` - Criticality levels

**Risk Management** (`/risks`)
- `GET /risks` - List risks (org-filtered, scope-aware)
- `GET /risks/{id}` - Risk details
- `POST /risks` - Create risk
- `PUT /risks/{id}` - Update risk
- `DELETE /risks/{id}` - Delete risk
- `GET /risks/categories` - Risk categories
- `GET /risks/severities` - Risk severity levels
- `GET /risks/statuses` - Risk statuses

**Policy Management** (`/policies`)
- `GET /policies` - List policies (org-filtered)
- `GET /policies/{id}` - Policy details
- `POST /policies` - Create policy
- `PUT /policies/{id}` - Update policy
- `DELETE /policies/{id}` - Delete policy
- `GET /policies/statuses` - Policy statuses
- `POST /policies/{id}/link-framework` - Associate with framework
- `POST /policies/{id}/link-objective` - Associate with objective

**History & Audit** (`/history`)
- `GET /history` - Audit log (org-filtered)
- `GET /history/{record_id}` - Record history
- `GET /history/table/{table_name}` - Table-specific history

**AI Tools** (`/ai-tools`)
- `POST /ai-tools/analyze-correlations` - Question correlation analysis
- `POST /ai-tools/suggest-objectives` - Objective recommendations
- `GET /ai-tools/llm-settings` - LLM configuration
- `PUT /ai-tools/llm-settings` - Update LLM settings

**Security Scanners** (`/scanners`)
- `POST /scanners/zap/scan` - OWASP ZAP scan
- `GET /scanners/zap/results/{scan_id}` - ZAP results
- `POST /scanners/nmap/scan` - Nmap network scan
- `GET /scanners/nmap/results/{scan_id}` - Nmap results
- `POST /scanners/semgrep/scan` - Semgrep code scan
- `GET /scanners/semgrep/results/{scan_id}` - Semgrep results
- `POST /scanners/osv/scan` - OSV vulnerability scan
- `GET /scanners/osv/results/{scan_id}` - OSV results
- `GET /scanners/history` - Scan history (org-filtered)
- `GET /scanners/history/{id}` - Scan details
- `DELETE /scanners/history` - Clear scan history (super_admin only)
- `GET /scanners/settings` - Scanner configuration
- `PUT /scanners/settings` - Update scanner settings

**Home/Dashboard** (`/home`)
- `GET /home/metrics` - Dashboard KPIs
- `GET /home/pie-chart-data` - Compliance distribution
- `GET /home/frameworks-summary` - Framework statistics
- `GET /home/assessments-summary` - Assessment statistics
- `GET /home/user-analytics` - User activity metrics
- `GET /home/assessment-analytics` - Assessment completion trends
- `GET /home/policy-risk-analytics` - Policy/risk statistics

**Scopes** (`/scopes`)
- `GET /scopes` - List available scope types
- `GET /scopes/{scope_id}/entities` - Entities for scope type

**Settings** (`/settings`)
- `GET /settings/smtp` - SMTP configuration
- `PUT /settings/smtp` - Update SMTP settings
- `POST /settings/smtp/test` - Test email
- `GET /settings/organization` - Organization settings
- `PUT /settings/organization` - Update organization

### 2.4 Data Transfer Objects (DTOs)

**Pydantic Schemas** (`dtos/schemas.py`)

```python
# Authentication
class Token(BaseModel)
class UserLogin(BaseModel)
class UserRegistration(BaseModel)
class UserVerificationRegistration(BaseModel)

# User Management
class UserResponse(BaseModel)
class UserUpdate(BaseModel)
class ChangePassword(BaseModel)
class UserStatusUpdate(BaseModel)

# Framework
class FrameworkCreate(BaseModel)
class FrameworkUpdate(BaseModel)
class FrameworkResponse(BaseModel)

# Assessment
class AssessmentCreate(BaseModel)
class AssessmentUpdate(BaseModel)
class AssessmentResponse(BaseModel)

# Answer
class AnswerCreate(BaseModel)
class AnswerUpdate(BaseModel)
class AnswerResponse(BaseModel)

# (Additional schemas for all entities...)
```

### 2.5 Database Migrations

**Alembic Configuration**
- **Migration Path:** `cyberbridge_backend/alembic/versions/`
- **Auto-generation:** `alembic revision --autogenerate -m "description"`
- **Migration Application:** Automatic on container startup
- **Smart Migration Handling:**
  - Detects fresh vs existing database
  - Fresh DB: Creates tables from models + stamps migrations
  - Existing DB: Runs pending migrations normally
  - Future-proof for schema changes without rebuilding database

---

## 3. Automation Logic and Implementation

### 3.1 Background Job Scheduler

#### APScheduler Configuration

**Startup Event** (`main.py:85-102`)
```python
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(
        history_cleanup_service.cleanup_all_organizations,
        trigger=IntervalTrigger(hours=1),
        id='history_cleanup_job',
        name='History Cleanup Job',
        replace_existing=True
    )
    scheduler.start()
    logger.info("History cleanup scheduler started - checking every hour")
```

#### History Cleanup Automation

**Service:** `services/history_cleanup_service.py`

**Purpose:**
- Automatically clean old audit records based on organization settings
- Prevents database bloat from audit logs
- Configurable per-organization

**Configuration:**
- `history_cleanup_enabled` - Enable/disable cleanup (default: False)
- `history_retention_days` - Keep records for X days (default: 30)
- `history_cleanup_interval_hours` - Check frequency (default: 24)

**Process Flow:**
1. Scheduler runs every hour
2. Queries all organizations with `history_cleanup_enabled = True`
3. For each organization:
   - Check if interval has passed since last cleanup
   - Calculate cutoff date (now - retention_days)
   - Delete records older than cutoff date
   - Log deletion count
4. Update last cleanup timestamp

**Manual Trigger:**
```
POST /admin/organizations/{org_id}/cleanup-history-now
```

### 3.2 Activity Tracking Middleware

**Implementation:** `middleware/activity_tracker.py`

**Purpose:**
- Track user online status
- Update `last_activity` timestamp on every authenticated request

**Logic:**
```python
class ActivityTrackerMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract JWT token from Authorization header
        # Decode token to get user email
        # Update users.last_activity = now()
        # Continue request processing
        response = await call_next(request)
        return response
```

**Online User Detection:**
- User considered "online" if `last_activity` within last 3 minutes
- Query: `SELECT * FROM users WHERE last_activity >= (NOW() - INTERVAL '3 minutes')`

### 3.3 LLM Service Integration

#### LLM Service (`services/llm_service.py`)

**Automatic Environment Detection**
```python
def _is_production_environment(self) -> bool:
    container_env = os.getenv("CONTAINER_ENV")
    db_host = os.getenv("DB_HOST")
    return container_env == "docker" or db_host is not None

def _get_llm_url(self) -> str:
    if self._is_production_environment():
        return "http://llm:8015/v1/chat/completions"
    else:
        return "http://localhost:8015/v1/chat/completions"
```

**Configuration Settings (Database-Driven)**
- `custom_llm_url` - Override default LLM endpoint
- `custom_llm_payload` - Custom request payload
- `max_questions_per_framework` - Limit questions for analysis (default: 10)
- `llm_timeout_seconds` - Request timeout (default: 300)
- `min_confidence_threshold` - Minimum correlation confidence (default: 75%)
- `max_correlations` - Maximum suggestions returned (default: 10)

#### Use Case 1: Question Correlation Analysis

**Endpoint:** `POST /ai-tools/analyze-correlations`

**Purpose:** Identify semantically similar questions across different compliance frameworks

**Process:**
1. Receive two framework IDs from frontend
2. Fetch questions for both frameworks (limited by `max_questions_per_framework`)
3. Build LLM prompt:
   ```
   You are an expert in cybersecurity compliance frameworks.
   Analyze questions from Framework A and Framework B.
   Identify semantically similar questions.

   Output format: JSON
   {
     "correlations": [
       {
         "question_a_id": "uuid",
         "question_b_id": "uuid",
         "confidence": 95,
         "reasoning": "Both address..."
       }
     ]
   }
   ```
4. Send prompt to llama.cpp (async HTTP request)
5. Parse JSON response
6. Filter correlations by `min_confidence_threshold`
7. Limit results to `max_correlations`
8. Return suggestions to frontend

**Frontend Workflow:**
- User selects two frameworks in Correlations page
- Clicks "Analyze Correlations"
- Loading indicator shows while LLM processes
- Results displayed in table with confidence scores
- User can approve/reject each suggestion
- Approved correlations saved to `question_correlations` table

**Correlation Benefits:**
- Answer synchronization across frameworks
- Reduced redundant work for multi-framework compliance
- AI-powered semantic matching (not just keyword matching)

#### Use Case 2: Security Scan Analysis

**Nmap Analysis** (`services/llm_service.py:313-392`)
```python
async def process_nmap_results(self, raw_results: Dict) -> Dict:
    # Extract summary (hosts, ports, services)
    # Build prompt with scan details
    # Request LLM analysis covering:
    #   1. Critical security findings
    #   2. Potential risks
    #   3. Recommended actions
    # Return human-readable analysis + raw data
```

**Semgrep Analysis** (`services/llm_service.py:486-553`)
```python
async def process_semgrep_results(self, raw_results: Dict) -> Dict:
    # Extract findings by severity (ERROR, WARNING, INFO)
    # Build prompt with top 20 findings
    # Request LLM analysis covering:
    #   1. Most critical vulnerabilities
    #   2. Common security patterns
    #   3. Remediation priorities
    # Return analysis + summary + raw data
```

**OSV Analysis** (`services/llm_service.py:611-680`)
```python
async def process_osv_results(self, raw_results: Dict) -> Dict:
    # Extract vulnerable packages and CVEs
    # Build prompt with top 15 packages
    # Request LLM analysis covering:
    #   1. Critical vulnerabilities to address
    #   2. Dependency patterns
    #   3. Remediation actions
    # Return analysis + summary + raw data
```

**Fallback Mechanism:**
- If LLM request fails (timeout, connection error):
  - Log error
  - Generate formatted text summary from raw data
  - Return fallback instead of failing scan
- Ensures scanner functionality even without LLM

### 3.4 Email Automation

#### SMTP Service (`routers/auth_controller.py`)

**Configuration:**
- `smtp_configurations` table stores settings
- Fields: smtp_server, smtp_port, username, password, use_tls, is_active

**Use Case 1: Email Verification**
```python
def send_verification_email(db: Session, email: str, verification_key: str):
    # Get active SMTP config
    # Build verification URL (environment-aware)
    # Compose HTML email with verification link
    # Send via SMTP with TLS
```

**Verification Flow:**
1. User registers via `/auth/register-with-verification`
2. Backend creates `user_verifications` record with UUID key
3. Verification email sent with link: `{API_BASE_URL}/auth/verify-email?key={UUID}`
4. Email expires after 24 hours
5. User clicks link → Backend verifies key → Creates user account
6. Domain-based organization assignment:
   - First user from domain → Create org + assign org_admin role
   - Subsequent users → Join existing org + assign org_user role

**Use Case 2: Forgot Password**
```python
def send_temporary_password_email(db: Session, email: str, temp_password: str):
    # Generate secure temporary password (10 chars, mixed case, digits, symbols)
    # Hash password and update database
    # Send email with temporary password
    # User logs in with temporary password
    # Recommended to change password in settings
```

**Password Generation Algorithm:**
```python
def generate_temporary_password(length: int = 10) -> str:
    # Ensure at least one of each:
    #   - Uppercase letter
    #   - Lowercase letter
    #   - Digit
    #   - Special character (!@#$%&)
    # Fill remaining with random characters
    # Shuffle result
    return shuffled_password
```

### 3.5 File Upload Automation

**Evidence File Management** (`routers/answers_controller.py`)

**Upload Process:**
1. Frontend sends `multipart/form-data` with file
2. Backend validates file type and size
3. Generate unique filename: `{timestamp}_{uuid}_{original_name}`
4. Save to local filesystem: `uploads/evidence/{answer_id}/`
5. Create `evidence` record:
   - `filename` - Original name
   - `filepath` - Server path
   - `file_type` - MIME type
   - `file_size` - Bytes
   - `answer_id` - Associated answer

**Download Process:**
1. Frontend requests file via evidence ID
2. Backend validates user permissions
3. Stream file with appropriate Content-Type header
4. Frontend triggers browser download

**Deletion:**
- Cascade delete: Deleting answer removes evidence records
- File cleanup: Background job can clean orphaned files

### 3.6 Framework Update Automation

**Service:** `services/framework_update_service.py`

**Purpose:** Allow framework updates without full re-seeding

**Update Process:**
1. Admin creates framework update entry:
   - `framework_id` - Target framework
   - `version` - Update version number (1, 2, 3, etc.)
   - `framework_name` - Identifier (cra, iso27001, nis2)
   - `description` - What's included
   - `status` - available, applied, failed
2. Update appears in `/frameworks/updates` endpoint
3. Admin clicks "Apply Update" in frontend
4. Backend:
   - Executes update logic (new questions, chapters, objectives)
   - Updates status to "applied"
   - Records `applied_by` and `applied_at`
   - If error: status = "failed", stores `error_message`
5. Frontend refreshes framework data

**Benefits:**
- No database rebuild required
- Version tracking for compliance
- Rollback capability (future feature)

### 3.7 Automatic Answer Mirroring (Scope-Based)

**Logic:** `repositories/answer_repository.py`

**Purpose:** Synchronize answers across correlated questions when using same scope entity

**Trigger Conditions:**
1. User answers a question in Assessment A (Framework X, Scope: Product, Entity: Product-123)
2. Question A has correlations to questions in other frameworks
3. Active assessments exist for those frameworks with SAME scope entity (Product-123)

**Process:**
```python
def mirror_answer_to_correlated_questions(
    db: Session,
    answer: Answer,
    current_assessment: Assessment
):
    # Find correlations for this question
    correlations = get_correlations_for_question(answer.question_id, current_assessment.scope_entity_id)

    for correlation in correlations:
        # Find corresponding question in other framework
        correlated_question_id = get_other_question_id(correlation, answer.question_id)

        # Find active assessment for that framework + scope entity
        target_assessment = get_assessment(
            framework=correlation.other_framework,
            scope_id=current_assessment.scope_id,
            scope_entity_id=current_assessment.scope_entity_id
        )

        if target_assessment:
            # Check if answer already exists
            existing = get_answer(target_assessment.id, correlated_question_id)

            if existing:
                # Update existing answer
                update_answer(existing, answer.value, answer.evidence_description)
            else:
                # Create new answer
                create_answer(
                    assessment_id=target_assessment.id,
                    question_id=correlated_question_id,
                    value=answer.value,
                    evidence_description=answer.evidence_description
                )
```

**Example Scenario:**
- Product "NextGen SIEM Pro" assessed for both ISO 27001 and NIS2
- Question "Do you have MFA?" exists in both frameworks (correlated)
- User answers "Yes" in ISO 27001 assessment
- System automatically answers "Yes" in NIS2 assessment
- Result: Reduced redundancy, consistent answers

**Scope Specificity:**
- Mirroring ONLY occurs for same scope entity
- Organization-level assessment doesn't mirror to Product-level
- Ensures answer relevance and context preservation

---

## 4. Deployment, Testing, and Validation

### 4.1 Docker Deployment Architecture

#### Development Environment

**Docker Compose:** `docker-compose.yml`

**Start Command:**
```bash
docker-compose up -d
```

**Service Dependencies:**
```
cyberbridge_db (Tier 1)
    ↓
zap (Tier 2)
    ↓
nmap, osv, semgrep, syft, llm (Tier 3)
    ↓
cyberbridge_backend (Tier 4)
    ↓
cyberbridge_frontend (Tier 5)
```

**Health Check Strategy:**
- Each service defines `healthcheck` directive
- Dependent services use `depends_on` with `condition: service_healthy`
- Ensures proper startup order
- Automatic restart on failure

**Volume Persistence:**
- `postgres_data:/var/lib/postgresql/data` - Database persistence

**Network Configuration:**
- Bridge network: `cyberbridge-network`
- Internal DNS resolution by service name

#### Production Environment

**Docker Compose:** `docker-compose.prod.yml`

**Key Differences:**
1. **Build Arguments:**
   - `API_BASE_URL_PROD` - Production server IP/domain
   - `VITE_PRODUCTION_IP` - Frontend production URL

2. **Port Mappings:**
   - Backend: `5174:8000` (host:container)
   - Frontend: `5173:5173`
   - Database: `5433:5432`

3. **Environment Variables:**
   ```yaml
   CONTAINER_ENV: docker
   DB_HOST: cyberbridge_db
   DB_PORT: 5432
   NMAP_SERVICE_URL: http://nmap:8000
   SEMGREP_SERVICE_URL: http://semgrep:8000
   OSV_SERVICE_URL: http://osv:8000
   ZAP_SERVICE_URL: http://zap:8000
   SYFT_SERVICE_URL: http://syft:8000
   ```

4. **Resource Limits:**
   - LLM service: 13GB memory limit
   - CPU throttling: Optional (configurable)

5. **Restart Policies:**
   - Database: `unless-stopped`
   - Scanners: `unless-stopped`
   - Backend: `on-failure`
   - Frontend: `unless-stopped`

#### Production Deployment Steps

1. **Server Preparation:**
   ```bash
   # Install Docker and Docker Compose
   sudo apt update
   sudo apt install docker.io docker-compose -y

   # Clone repository
   git clone <repo-url>
   cd cyberbridge_project
   ```

2. **Configuration:**
   ```bash
   # Edit docker-compose.prod.yml
   # Update API_BASE_URL_PROD and VITE_PRODUCTION_IP
   # Example: http://38.126.154.32
   ```

3. **Build and Start:**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Verify Health:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs -f
   ```

5. **Database Initialization:**
   - Tables created automatically via SQLAlchemy
   - Alembic migrations applied on startup
   - Seed data inserted (roles, organizations, frameworks)

6. **Access Application:**
   - Frontend: `http://{SERVER_IP}:5173`
   - Backend API: `http://{SERVER_IP}:5174`
   - API Docs: `http://{SERVER_IP}:5174/docs`

#### HTTPS Configuration

**Production HTTPS Setup:**

1. **ZAP HTTPS Subdomain:**
   - Dedicated subdomain for ZAP scanner: `https://zap.yourdomain.com`
   - Prevents mixed content errors
   - Configuration: `docker-compose.prod.yml`

2. **Reverse Proxy (Nginx/Traefik):**
   ```nginx
   server {
       listen 443 ssl;
       server_name app.yourdomain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://localhost:5173;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /api {
           proxy_pass http://localhost:5174;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **SSL Certificate:**
   - Let's Encrypt (certbot)
   - Manual certificate installation
   - Automatic renewal configuration

4. **Frontend Serve Configuration:**
   ```json
   # cyberbridge_frontend/serve.json
   {
     "public": "dist",
     "rewrites": [
       { "source": "**", "destination": "/index.html" }
     ],
     "headers": [
       {
         "source": "**",
         "headers": [
           {
             "key": "Cache-Control",
             "value": "no-cache, no-store, must-revalidate"
           }
         ]
       }
     ]
   }
   ```

### 4.2 Database Migration Strategy

#### Alembic Migration Workflow

**Initial Setup:**
```bash
cd cyberbridge_backend
alembic init alembic
```

**Generate Migration:**
```bash
alembic revision --autogenerate -m "Add scanner_history table"
```

**Review Migration:**
```python
# alembic/versions/{revision_id}_add_scanner_history_table.py
def upgrade():
    op.create_table('scanner_history',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('scanner_type', sa.String(50), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        # ...
    )

def downgrade():
    op.drop_table('scanner_history')
```

**Apply Migration:**
```bash
alembic upgrade head
```

**Smart Migration Handling (Production):**
```python
# main.py startup logic
if database_is_fresh():
    # Create all tables from models
    Base.metadata.create_all(bind=engine)
    # Stamp alembic to current revision (skip migrations)
    alembic stamp head
else:
    # Run pending migrations
    alembic upgrade head
```

**Migration Best Practices:**
1. Always review auto-generated migrations
2. Test migrations on staging environment first
3. Backup database before applying migrations in production
4. Create rollback plan (test `downgrade` function)
5. Document breaking changes in migration comments

#### Database Seeding

**Seed Manager:** `seeds/SeedManager.py`

**Seed Order (Dependencies):**
```python
def run_all_seeds(self):
    self.seed_roles()                    # 1. Roles (super_admin, org_admin, org_user, guest_auditor, auditor_lead)
    self.seed_organisations()            # 2. Organizations
    self.seed_super_admin()              # 3. Super admin user
    self.seed_assessment_types()         # 4. Assessment types
    self.seed_policy_statuses()          # 5. Policy statuses
    self.seed_product_statuses()         # 6. Product statuses
    self.seed_economic_operators()       # 7. Economic operators
    self.seed_product_types()            # 8. Product types
    self.seed_risk_severities()          # 9. Risk severities
    self.seed_risk_statuses()            # 10. Risk statuses
    self.seed_compliance_statuses()      # 11. Compliance statuses
    self.seed_scopes()                   # 12. Scope types
    self.seed_frameworks()               # 13. Frameworks (ISO 27001, NIS2, CRA, etc.)
    self.seed_criticalities()            # 14. EU CRA criticalities
    self.seed_llm_settings()             # 15. Default LLM configuration
    self.seed_scanner_settings()         # 16. Default scanner configuration
```

**Idempotent Seeding:**
- Each seed function checks existence before inserting
- Uses `get_or_create` pattern
- Safe to run multiple times

**Framework Seeding from Excel:**
```python
POST /frameworks/seed-from-excel
{
    "file": <excel_file>,
    "framework_name": "ISO 27001:2022",
    "organisation_id": "uuid"
}
```

**Excel Format:**
```
Chapter | Subchapter | Objective | Question | Mandatory | Assessment Type
A.5     | A.5.1      | Info Sec Policy | Is policy established? | Yes | Internal Audit
```

### 4.3 Testing Strategy

#### Backend Testing

**Unit Tests:**
- Repository layer tests (database operations)
- Service layer tests (business logic)
- Authentication tests (JWT generation, validation)

**Example Test Structure:**
```python
# tests/test_user_repository.py
def test_create_user(db_session):
    user_data = UserCreateInOrganisation(
        email="test@example.com",
        password="SecurePass123!",
        role_id=role_id,
        organisation_id=org_id
    )
    user = user_repository.create_user_in_organisation(db_session, user_data)
    assert user.email == "test@example.com"
    assert user.status == "pending_approval"
```

**Integration Tests:**
- API endpoint tests (FastAPI TestClient)
- Database integration tests
- Scanner service integration tests

**Example Integration Test:**
```python
# tests/test_auth_api.py
def test_login_success(test_client):
    response = test_client.post("/auth/token", data={
        "username": "super@admin.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["role"] == "super_admin"
```

**Test Database:**
- Separate test database
- Fixtures for common test data
- Automatic cleanup after tests

**Run Tests:**
```bash
cd cyberbridge_backend
pytest tests/ -v
```

#### Frontend Testing

**Unit Tests:**
- Component tests (React Testing Library)
- Store tests (Zustand)
- Utility function tests

**Example Component Test:**
```typescript
// tests/components/HeaderBar.test.tsx
test('renders user email in header', () => {
  render(<HeaderBar />);
  expect(screen.getByText('user@example.com')).toBeInTheDocument();
});
```

**E2E Tests (Future):**
- Cypress or Playwright
- Complete user workflows
- Cross-browser testing

**Run Tests:**
```bash
cd cyberbridge_frontend
npm run test
```

#### Security Testing

**Static Analysis:**
- **Backend:** Bandit (Python security linter)
  ```bash
  bandit -r cyberbridge_backend/app
  ```
- **Frontend:** ESLint with security plugins
  ```bash
  npm run lint
  ```

**Dependency Scanning:**
- **Backend:** Safety, pip-audit
  ```bash
  safety check
  pip-audit
  ```
- **Frontend:** npm audit
  ```bash
  npm audit
  npm audit fix
  ```

**Vulnerability Scanning:**
- Semgrep scan on codebase
- OSV scan on dependencies
- ZAP scan on running application

**Penetration Testing:**
- Manual testing by security team
- Quarterly external audits
- Bug bounty program (future)

### 4.4 Monitoring and Logging

#### Application Logging

**Backend Logging:**
```python
import logging
logger = logging.getLogger(__name__)

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.info("User logged in: {email}")
logger.error("Database connection failed: {error}")
```

**Log Format:**
```
[2025-01-24 10:30:45,123] INFO [app.routers.auth_controller] User logged in: admin@example.com
[2025-01-24 10:31:02,456] ERROR [app.services.llm_service] LLM timeout: Request exceeded 300s
```

**Log Storage:**
- Container logs: `docker-compose logs -f cyberbridge_backend`
- Persistent logging: Volume mount to `/app/logs`
- Log rotation: Daily, 7-day retention

**Frontend Logging:**
```typescript
// Console logging for development
console.log('User action:', action);
console.error('API error:', error);

// Production error tracking (e.g., Sentry)
Sentry.captureException(error);
```

#### Database Audit Trail

**History Table:**
- Records all INSERT, UPDATE, DELETE operations
- Tables tracked: products, policies, risks, objectives, assessments
- Columns: table_name, record_id, action, old_data, new_data, user_email, timestamp

**Query History:**
```sql
SELECT * FROM history
WHERE table_name_changed = 'products'
AND record_id = '...'
ORDER BY last_timestamp DESC;
```

**Audit Compliance:**
- Immutable records (no updates to history table)
- 7-year retention by default
- Configurable per-organization cleanup

#### Health Monitoring

**Service Health Checks:**
```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/docs || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

**Health Endpoints:**
- Database: `pg_isready -U postgres`
- Backend: `GET /docs` (FastAPI docs page)
- Scanners: `curl -f http://localhost:8000/`
- LLM: `curl -f http://localhost:8015/health`

**Monitoring Tools (Future Integration):**
- Prometheus for metrics
- Grafana for dashboards
- Alertmanager for notifications

### 4.5 Backup and Recovery

#### Database Backup

**Automated Backup:**
```bash
# Daily backup cron job
0 2 * * * docker exec cyberbridge_db pg_dump -U postgres postgres > /backups/cyberbridge_$(date +\%Y\%m\%d).sql
```

**Manual Backup:**
```bash
docker exec cyberbridge_db pg_dump -U postgres postgres > backup.sql
```

**Restore:**
```bash
cat backup.sql | docker exec -i cyberbridge_db psql -U postgres postgres
```

**Backup Strategy:**
- Daily full backups
- 30-day retention
- Off-site storage (S3, cloud backup)
- Encrypted backups for compliance

#### Application State Backup

**Evidence Files:**
- Location: `uploads/evidence/`
- Backup frequency: Daily
- Storage: Separate from database backups

**Configuration:**
- SMTP settings
- LLM settings
- Scanner settings
- Organization logos

**Backup Script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf /backups/cyberbridge_files_$DATE.tar.gz \
    uploads/ \
    cyberbridge_backend/alembic/versions/ \
    docker-compose.yml
```

#### Disaster Recovery

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 24 hours

**Recovery Process:**
1. Provision new server
2. Install Docker and Docker Compose
3. Clone repository
4. Restore database backup
5. Restore evidence files
6. Start services
7. Verify functionality
8. Update DNS (if needed)

---

## 5. Platform Requirements

### 5.1 Functional Requirements

#### FR-001: User Authentication and Authorization
- **Priority:** Critical
- **Description:** System shall support JWT-based authentication with role-based access control
- **Acceptance Criteria:**
  - Users can register with email verification
  - Users can log in with email/password
  - JWT tokens issued with configurable expiration
  - Tokens validated on protected endpoints
  - Role-based permissions enforced (super_admin, org_admin, org_user)
  - Password reset via email
  - Session tracking for analytics

#### FR-002: Multi-Tenant Organization Management
- **Priority:** Critical
- **Description:** System shall support multiple organizations with data isolation
- **Acceptance Criteria:**
  - Organizations created automatically from email domains
  - First user from domain becomes org_admin
  - Subsequent users assigned org_user role
  - Org admins see only their organization's data
  - Super admins see all organizations
  - Domain blacklist prevents unauthorized registrations

#### FR-003: Framework Management
- **Priority:** High
- **Description:** System shall support compliance framework management
- **Acceptance Criteria:**
  - Create frameworks manually or from Excel
  - Frameworks have chapters, objectives, and questions
  - Support for 15+ frameworks (ISO 27001, NIS2, CRA, NIST CSF, etc.)
  - Framework updates without full re-seeding
  - Organization-specific frameworks
  - Framework scope configuration (Product, Organization, Asset, etc.)

#### FR-004: Assessment Workflow
- **Priority:** High
- **Description:** System shall support compliance assessments with evidence
- **Acceptance Criteria:**
  - Create assessments for frameworks
  - Answer questions with Yes/No/Partial/N/A
  - Upload evidence files (PDF, DOCX, images)
  - Link answers to policies and risks
  - Track assessment progress (completion percentage)
  - Mark assessments complete
  - Export assessment reports to PDF
  - Scope-based assessments (per product, organization, etc.)

#### FR-005: Policy Management
- **Priority:** High
- **Description:** System shall manage security policies with lifecycle tracking
- **Acceptance Criteria:**
  - Create/update/delete policies
  - Policy statuses: Draft, Review, Ready for Approval, Approved
  - Link policies to frameworks and objectives
  - Assign policies to answers
  - Track policy ownership (created_by, last_updated_by)
  - Export policies to PDF
  - Version control (via history table)

#### FR-006: Risk Management
- **Priority:** High
- **Description:** System shall manage cybersecurity risks with controls
- **Acceptance Criteria:**
  - Create/update/delete risks
  - Risk categories by product type (Hardware, Software)
  - Likelihood, Severity, Residual Risk assessment
  - Risk status: Reduce, Avoid, Transfer, Share, Accept, Remediated
  - Link risks to products
  - Control measures documentation
  - Scope-based risk assessment
  - Export risk register to PDF

#### FR-007: Assets (Products & Services)
- **Priority:** High
- **Description:** System shall maintain asset catalog (products and services) with EU CRA classifications
- **Acceptance Criteria:**
  - Register products with SBOM
  - Product types: Hardware, Software
  - Economic operators: Manufacturer, Importer, Distributor
  - EU CRA criticality levels (Annex III Class I, Class II, Annex IV)
  - Product status tracking (Live, Testing)
  - Link products to assessments and risks
  - Track product ownership

#### FR-008: Question Correlation (AI-Powered)
- **Priority:** Medium
- **Description:** System shall identify semantically similar questions across frameworks
- **Acceptance Criteria:**
  - Analyze questions from two frameworks
  - LLM generates correlation suggestions
  - Confidence scores provided (0-100%)
  - User can approve/reject suggestions
  - Approved correlations saved to database
  - Scope-specific correlations (Product, Organization, Other)
  - Answer mirroring for correlated questions
  - Audit old correlations

#### FR-009: Security Scanning Integration
- **Priority:** High
- **Description:** System shall integrate with security scanning tools
- **Acceptance Criteria:**
  - OWASP ZAP web application scanning
  - Nmap network scanning
  - Semgrep static code analysis
  - OSV dependency vulnerability scanning
  - LLM-powered result analysis
  - Scan history storage
  - Export scan results to PDF
  - Domain whitelisting for scans

#### FR-010: Dashboard and Analytics
- **Priority:** Medium
- **Description:** System shall provide visual analytics and metrics
- **Acceptance Criteria:**
  - Compliance pie chart (compliant, partial, non-compliant)
  - Assessment progress tracking
  - Framework coverage metrics
  - User activity analytics (visits, online users)
  - Policy and risk statistics
  - PDF download tracking
  - Time-based filtering (date ranges)

#### FR-011: Audit Trail and History
- **Priority:** High
- **Description:** System shall maintain comprehensive audit logs
- **Acceptance Criteria:**
  - Track INSERT, UPDATE, DELETE operations
  - Record old and new data values
  - Track user responsible for changes
  - Timestamp all changes
  - Queryable history by table and record
  - Automatic cleanup based on retention policy
  - Export history to PDF

#### FR-012: Email Notifications
- **Priority:** Medium
- **Description:** System shall send email notifications for key events
- **Acceptance Criteria:**
  - Email verification for new registrations
  - Forgot password email with temporary password
  - Configurable SMTP settings
  - HTML email templates
  - Test email functionality

### 5.2 Non-Functional Requirements

#### NFR-001: Performance
- **Response Time:**
  - API endpoints: < 500ms (95th percentile)
  - LLM operations: < 5 minutes (configurable timeout)
  - Scanner operations: < 10 minutes (depends on scan scope)
  - Frontend page load: < 3 seconds
- **Throughput:**
  - Support 100 concurrent users per organization
  - Handle 1000 API requests per minute
- **Database:**
  - Query optimization with indexes
  - Connection pooling
  - Async operations

#### NFR-002: Scalability
- **Horizontal Scaling:**
  - Stateless backend (JWT authentication)
  - Load balancer ready (future)
  - Database read replicas (future)
- **Data Growth:**
  - Support 100+ organizations
  - 10,000+ assessments per organization
  - 100,000+ audit records per organization
  - Automatic history cleanup prevents bloat

#### NFR-003: Security
- **Authentication:**
  - Password hashing (bcrypt)
  - JWT with secure secret key
  - Token expiration and refresh
- **Authorization:**
  - Role-based access control
  - Organization-level data isolation
  - Endpoint-level permission checks
- **Data Protection:**
  - SQL injection prevention (SQLAlchemy ORM)
  - XSS prevention (Ant Design sanitization)
  - CORS configuration
  - Sensitive data logging exclusion
- **Compliance:**
  - GDPR-ready (data export, deletion)
  - SOC 2 controls implemented
  - ISO 27001 aligned security practices

#### NFR-004: Availability
- **Uptime:** 99.5% (excluding planned maintenance)
- **Health Checks:**
  - All services monitored every 10 seconds
  - Automatic container restart on failure
- **Backup:**
  - Daily database backups
  - 30-day retention
  - Point-in-time recovery capability
- **Disaster Recovery:**
  - RTO: 4 hours
  - RPO: 24 hours

#### NFR-005: Usability
- **User Interface:**
  - Responsive design (desktop, tablet, mobile)
  - Intuitive navigation with breadcrumbs
  - Consistent design language (Ant Design)
  - Accessibility (WCAG 2.1 Level AA target)
- **User Experience:**
  - Contextual help and tooltips
  - Loading indicators for async operations
  - Error messages with actionable guidance
  - Form validation with inline feedback
- **Documentation:**
  - User guide
  - Admin guide
  - API documentation (OpenAPI/Swagger)

#### NFR-006: Maintainability
- **Code Quality:**
  - Type safety (TypeScript, Python type hints)
  - Linting (ESLint, Black)
  - Code reviews via pull requests
- **Architecture:**
  - Clear separation of concerns (MVC)
  - Dependency injection
  - Service-oriented design
- **Testing:**
  - Unit tests (80% coverage target)
  - Integration tests for critical paths
  - E2E tests for key workflows
- **Deployment:**
  - Containerized with Docker
  - Infrastructure as code
  - Automated database migrations
  - Zero-downtime deployments (future)

#### NFR-007: Interoperability
- **API Standards:**
  - RESTful API design
  - JSON request/response format
  - OpenAPI 3.0 specification
- **Data Formats:**
  - Excel import for frameworks
  - PDF export for reports
  - JSON data exchange
  - SPDX format for SBOM
- **Integration:**
  - Webhook support (future)
  - API rate limiting (future)
  - SSO (Google OAuth2, Microsoft OAuth2)

### 5.3 User Requirements

#### UR-001: Registration and Onboarding
- **Actor:** New User
- **Requirement:** Easy registration with minimal friction
- **Flow:**
  1. User provides email address
  2. Verification email sent within 1 minute
  3. User clicks verification link
  4. Organization automatically assigned based on email domain
  5. First user from domain becomes org_admin
  6. Subsequent users await org_admin approval (configurable)

#### UR-002: Dashboard Overview
- **Actor:** All Users
- **Requirement:** At-a-glance compliance status
- **Flow:**
  1. User logs in
  2. Dashboard displays:
     - Compliance pie chart
     - Recent assessments
     - Active frameworks
     - Upcoming deadlines (future)
     - Quick actions (New Assessment, View Objectives)

#### UR-003: Assessment Workflow
- **Actor:** Org User, Org Admin
- **Requirement:** Conduct compliance assessment efficiently
- **Flow:**
  1. Create new assessment (select framework, scope)
  2. Answer questions one by one
  3. Upload evidence for each answer
  4. Link to relevant policies and risks
  5. Save draft (resume later)
  6. Mark assessment complete
  7. Export to PDF for auditors

#### UR-004: Multi-Framework Compliance
- **Actor:** Org Admin
- **Requirement:** Manage multiple frameworks without redundancy
- **Flow:**
  1. Register product for ISO 27001 and NIS2
  2. Use AI correlation to identify common questions
  3. Answer question once in ISO 27001
  4. Answer automatically mirrors to NIS2 (same scope)
  5. Result: 50% reduction in duplicate work

#### UR-005: Risk and Policy Management
- **Actor:** Org Admin
- **Requirement:** Centralized risk and policy management
- **Flow:**
  1. Create risk with controls
  2. Link risk to product
  3. Create policy to address risk
  4. Link policy to compliance objectives
  5. Assign policy to assessment answers
  6. Result: Full traceability from risk to compliance

#### UR-006: Security Scanning
- **Actor:** Org Admin, Security Team
- **Requirement:** Automated vulnerability scanning
- **Flow:**
  1. Navigate to Scanners page
  2. Select scanner type (ZAP, Nmap, Semgrep, OSV)
  3. Input target (URL, IP, repo path, SBOM file)
  4. Start scan (background process)
  5. View AI-powered analysis
  6. Export results to PDF
  7. Results saved to scan history

#### UR-007: Audit Trail
- **Actor:** Auditor, Org Admin
- **Requirement:** Complete change history for compliance evidence
- **Flow:**
  1. Navigate to History page
  2. Filter by table (Products, Policies, Risks, etc.)
  3. View all changes with timestamps
  4. See who made changes
  5. Compare old vs new values
  6. Export audit trail to PDF

#### UR-008: User Management (Admin)
- **Actor:** Org Admin, Super Admin
- **Requirement:** Manage user approvals and permissions
- **Flow:**
  1. Navigate to Admin Area
  2. View pending user registrations
  3. Review user details
  4. Approve or reject registration
  5. Monitor online users
  6. View user activity analytics

### 5.4 Security Requirements

#### SR-001: Authentication Security
- JWT tokens with secure secrets
- Token expiration (default: 60 minutes)
- Password complexity requirements
- Account lockout after failed attempts (future)
- Multi-factor authentication (future)

#### SR-002: Data Protection
- Passwords hashed with bcrypt (cost factor 12)
- Sensitive fields excluded from logs
- Database connection encryption (TLS)
- HTTPS required for production
- CORS with whitelisted origins

#### SR-003: Access Control
- Role-based permissions (super_admin, org_admin, org_user)
- Organization-level data isolation
- Endpoint-level authorization checks
- Read-only access for org_user (configurable)
- Audit log for privileged operations

#### SR-004: Vulnerability Management
- Dependency scanning (npm audit, pip-audit, Safety)
- Static code analysis (ESLint, Bandit, Semgrep)
- Regular security updates
- Penetration testing (quarterly)
- Bug bounty program (future)

#### SR-005: Compliance
- GDPR compliance (data export, right to erasure)
- SOC 2 Type II controls
- ISO 27001 aligned practices
- EU Cyber Resilience Act considerations
- Audit trail for all data changes

### 5.5 Legal and Regulatory Requirements

#### LR-001: GDPR Compliance
- **Right to Access:** User can export their data
- **Right to Erasure:** Admin can delete user account and data
- **Right to Rectification:** User can update their information
- **Data Portability:** JSON export of user data
- **Consent:** Email verification for registration
- **Breach Notification:** Incident response procedures
- **Data Retention:** Configurable history cleanup

#### LR-002: EU Cyber Resilience Act (CRA)
- **Product Classification:** EU CRA criticality levels supported
- **SBOM Management:** Products include software bill of materials
- **Vulnerability Disclosure:** Security scanning integrated
- **Support Duration:** Track product lifecycle and EOL
- **Conformity Assessment:** Assessment workflow aligned with CRA

#### LR-003: Terms of Service and Privacy Policy
- Display during registration
- User acceptance required (future)
- Version tracking (future)
- Opt-out mechanisms

#### LR-004: Data Residency
- Database hosted in specified region
- Configurable data location
- Backup storage location

#### LR-005: Export Control
- No encryption export restrictions (standard TLS)
- Compliance with local regulations

---

## 6. Integration Plan

### 6.1 Internal Service Integration

#### Database Integration
- **Technology:** PostgreSQL 16+ with SQLAlchemy ORM
- **Connection:** Async connection pooling
- **Migration:** Alembic for schema versioning
- **Seeding:** Automatic on container startup
- **Health Check:** `pg_isready -U postgres`

#### LLM Integration (llama.cpp)
- **Endpoint:** `http://llm:8015/v1/chat/completions`
- **Model:** phi-4 (14 billion parameters)
- **Timeout:** 300 seconds (configurable)
- **Use Cases:**
  - Question correlation analysis
  - Security scan result interpretation
  - Compliance objective suggestions
- **Fallback:** Formatted text summary if LLM unavailable
- **Configuration:** Database-driven (custom URL, timeout, confidence threshold)

#### Scanner Integrations

**OWASP ZAP**
- **Endpoint:** `http://zap:8000`
- **Scan Types:** Spider, Active Scan, Full Scan, API Scan
- **Process:**
  1. Backend forwards scan request to ZAP service
  2. ZAP returns alerts (vulnerabilities)
  3. LLM analyzes alerts for insights
  4. Results saved to scanner_history table
  5. Frontend displays analysis with raw data
- **Authentication:** None (internal network)

**Nmap**
- **Endpoint:** `http://nmap:8000`
- **Scan Types:** Basic, Port Range, Aggressive, OS Detection
- **Process:**
  1. Backend forwards scan request with target IP/range
  2. Nmap returns XML output
  3. Backend parses XML to JSON
  4. LLM analyzes results (hosts, ports, services)
  5. Results saved with analysis
- **Authorization:** Domain whitelisting (scanner_settings)

**Semgrep**
- **Endpoint:** `http://semgrep:8000`
- **Scan Types:** Code repository analysis
- **Process:**
  1. User uploads code archive or provides Git URL
  2. Backend forwards to Semgrep service
  3. Semgrep returns findings (severity, check_id, message)
  4. LLM analyzes findings for priorities
  5. Results saved with recommendations
- **Rulesets:** OWASP Top 10, Security Best Practices

**OSV Scanner**
- **Endpoint:** `http://osv:8000`
- **Scan Types:** Dependency vulnerability scanning
- **Process:**
  1. User uploads SBOM (JSON, XML) or lockfile (package-lock.json, requirements.txt)
  2. Backend forwards to OSV service
  3. OSV queries vulnerability database
  4. Returns CVEs for vulnerable dependencies
  5. LLM analyzes impact and remediation
  6. Results saved to history
- **Database:** Google OSV database (continuously updated)

### 6.2 External Service Integration

#### SMTP Email Service
- **Configuration:** Database-stored (smtp_configurations table)
- **Fields:**
  - smtp_server (e.g., smtp.gmail.com)
  - smtp_port (e.g., 587)
  - username
  - password (encrypted storage recommended)
  - use_tls (boolean)
- **Use Cases:**
  - Email verification
  - Password reset
  - User notifications (future)
- **Test Endpoint:** `POST /settings/smtp/test`

#### Implemented Integrations

**Single Sign-On (SSO)**
- **Providers:** Google OAuth2, Microsoft OAuth2
- **Protocol:** OAuth 2.0
- **Implementation:** FastAPI OAuth2 libraries
- **Configuration:** Multi-record SSO configurations per organization
- **User Provisioning:** Automatic user creation from SSO claims

#### Future Integrations

**Ticketing Systems**
- **Platforms:** Jira, ServiceNow, GitHub Issues
- **Integration:** Webhook notifications for non-compliance findings
- **Use Case:** Auto-create tickets for compliance gaps

**SIEM Integration**
- **Platforms:** Splunk, ELK, QRadar
- **Data Export:** JSON logs for audit trail
- **Use Case:** Centralized security monitoring

**BI Tools**
- **Platforms:** Tableau, Power BI
- **Connection:** Direct PostgreSQL connection
- **Use Case:** Advanced analytics and reporting

**Cloud Storage**
- **Providers:** AWS S3, Azure Blob, Google Cloud Storage
- **Use Case:** Evidence file storage, backup storage
- **Implementation:** Python SDK (boto3, azure-storage-blob)

### 6.3 API Integration Guide

#### Authentication
```bash
# Step 1: Obtain JWT token
curl -X POST http://localhost:5174/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123"

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "org_admin"
}

# Step 2: Use token in subsequent requests
curl -X GET http://localhost:5174/assessments \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Create Assessment
```bash
curl -X POST http://localhost:5174/assessments \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ISO 27001 Internal Audit Q1 2025",
    "framework_id": "framework-uuid",
    "assessment_type_id": "assessment-type-uuid",
    "scope_id": "product-scope-uuid",
    "scope_entity_id": "product-uuid"
  }'
```

#### Submit Answer
```bash
curl -X POST http://localhost:5174/answers \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_id": "assessment-uuid",
    "question_id": "question-uuid",
    "value": "Yes",
    "evidence_description": "MFA enabled for all admin accounts"
  }'
```

#### Run Security Scan
```bash
curl -X POST http://localhost:5174/scanners/zap/scan \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com",
    "scan_type": "full"
  }'
```

#### Export Assessment to PDF
```bash
curl -X GET http://localhost:5174/assessments/{id}/export-pdf \
  -H "Authorization: Bearer {token}" \
  --output assessment-report.pdf
```

---

## 7. Implementation Roadmap

### 7.1 Historical Development (Versions 1-7)

**Version 1.0 (Q1 2023) - Foundation**
- Basic user authentication
- Framework management (ISO 27001)
- Assessment workflow
- PostgreSQL database

**Version 2.0 (Q2 2023) - Multi-Framework**
- NIS2 framework added
- CRA (Cyber Resilience Act) framework added
- Policy management
- Risk management
- Product registration

**Version 3.0 (Q3 2023) - Enhanced UX**
- React frontend migration (from Vue)
- Ant Design UI library integration
- Zustand state management
- Improved navigation and layout

**Version 4.0 (Q4 2023) - Security Scanning**
- OWASP ZAP integration
- Nmap integration
- Basic scan result display
- Manual scan analysis

**Version 5.0 (Q1 2024) - AI Integration**
- llama.cpp LLM service
- Question correlation analysis
- AI-powered scan result analysis
- Mistral 7B model (later upgraded to phi-4)

**Version 6.0 (Q2 2024) - Multi-Tenancy**
- Organization-based isolation
- Role-based access control refinement
- Email verification registration
- Domain blacklisting
- Audit trail (history table)

**Version 7.0 (Q3 2024) - Advanced Features**
- Semgrep integration
- OSV scanner integration
- PDF export functionality
- Dashboard analytics
- User session tracking

### 7.2 Version 8 (Q4 2024)

**Major Features:**
1. **Scope-Based Architecture**
   - Scopes table (Product, Organization, Asset, Project, Process, Other)
   - Assessments support scope configuration
   - Risks support scope configuration
   - Correlations support scope-specific mapping
   - Answer mirroring within same scope entity

2. **Scanner History Management**
   - `scanner_history` table for result archival
   - View past scan results
   - Export historical scans to PDF
   - Clear history functionality (admin only)
   - Organization-level filtering

3. **Framework Updates System**
   - `framework_updates` table
   - Version tracking for frameworks
   - Apply updates without re-seeding
   - Update status tracking (available, applied, failed)
   - Error message logging

4. **Enhanced Frameworks**
   - DORA (Digital Operational Resilience Act) 2022
   - AESCSF (Australia Energy Sector Cybersecurity Framework)
   - COBIT 2019
   - FTC Safeguards Rule
   - CMMC 2.0 conformity questions
   - 15+ frameworks total

5. **Organization-Specific Correlations**
   - Correlations isolated per organization
   - Audit old correlations feature
   - Scope-aware correlation management

6. **Improved History Cleanup**
   - Automatic cleanup scheduler (hourly check)
   - Per-organization configuration
   - Manual trigger endpoint
   - Configurable retention days and intervals

7. **PDF Download Tracking**
   - `pdf_downloads` table
   - Track exports by type (assessment, policy, risk, etc.)
   - Analytics dashboard for download metrics
   - Date-range filtering

8. **User Analytics Enhancement**
   - Visits per email tracking
   - Total visits metrics
   - Online user detection (3-minute window)
   - Session tracking with logout timestamps

9. **Production Deployment Fixes**
   - HTTPS subdomain for ZAP (mixed content fix)
   - Frontend cache control headers
   - Smart database migration handling
   - DNS configuration for services

10. **UI/UX Improvements**
    - Text truncation for long descriptions (policies, risks, objectives)
    - Full-text export for filtered columns
    - Live refresh on chapter and objective creation
    - Subchapter field added to objectives
    - Scope type and entity visibility in grids

### 7.3 Version 9 (Q1 2025)

**Implemented Features:**

**1. Advanced Reporting**
- Multi-framework comparison reports
- Gap analysis export with remediation timeline
- Executive summary dashboards

**2. Workflow Automation**
- Assessment reminders and notifications
- Compliance deadline tracking
- Email notifications for key events

**3. Enhanced LLM Capabilities**
- Multi-provider LLM support (llama.cpp, OpenAI, Anthropic, Google, X AI, QLON)
- Per-organization LLM provider configuration
- Compliance Advisor for framework guidance
- AI-powered policy alignment suggestions
- Automated objective recommendations

**4. Advanced Analytics**
- Compliance trends over time
- Framework comparison analytics
- User productivity metrics

**5. Third-Party Integrations**
- SSO (Google OAuth2, Microsoft OAuth2)

**6. Collaboration Features**
- Comments on assessments and answers

### 7.4 Version 10 (Current - Q1 2025)

**Major Features Implemented:**

**1. Controls Management Module**
- Dedicated controls management for compliance frameworks
- Link controls to objectives and assessments

**2. Incident Management**
- Incident tracking and management
- Incident response workflows

**3. Compliance Chain Visualization**
- Visual compliance chain from frameworks to objectives to controls
- Interactive compliance chain dashboard

**4. External Audit Portal**
- Magic link authentication for external auditors
- Guest auditor read-only access
- Auditor lead with full audit capabilities and sign-off authority

**5. CRA Public Assessment Wizards**
- Scope Assessment wizard
- Readiness Assessment wizard
- Guided compliance assessment workflows

**6. Multi-Provider LLM Support**
- 6 supported providers: llama.cpp, OpenAI, Anthropic, Google, X AI, QLON
- Per-organization provider selection
- Unified LLM interface across providers

**7. SSO (Single Sign-On)**
- Google OAuth2 integration
- Microsoft OAuth2 integration
- Multi-record SSO configurations

**8. Syft SBOM Generator**
- Software Bill of Materials generation (Port 8014)
- Integration with vulnerability scanning pipeline

**9. Scan Findings Unified Dashboard**
- Consolidated view of findings across all scanner types
- Cross-scanner analysis and correlation

**10. Recurring Scan Scheduler**
- Schedule automated recurring scans
- Configurable scan frequency and targets

**11. Evidence Library & Architecture Diagrams**
- Centralized evidence library
- Architecture diagram management
- Evidence file upload to objectives

**12. NVD/EUVD Vulnerability Database Integration**
- National Vulnerability Database integration
- European Union Vulnerability Database integration
- Vulnerability enrichment for scan results

**13. CRA Mode Per Organization**
- Organization-level CRA compliance mode
- CRA-specific workflows and requirements

**14. Super Admin Focused Mode**
- Streamlined super admin interface
- Platform-wide management dashboard

**15. Background Jobs Monitoring**
- View and monitor scheduled background jobs
- Job execution history and status tracking

**16. Assets Module (Renamed from Products)**
- Renamed Product Registration to Assets (Products & Services)
- Enhanced asset management capabilities

**17. Multi-Record SMTP and SSO Configurations**
- Support for multiple SMTP configurations
- Support for multiple SSO provider configurations

**18. Evidence File Upload to Objectives**
- Direct evidence file attachment to compliance objectives
- Objective-level evidence management

### 7.5 Future Roadmap (Version 11+)

**Planned Enterprise Features:**

**1. Advanced Security**
- Multi-factor authentication (MFA)
- Hardware security key support
- IP whitelisting
- Data encryption at rest

**2. Scalability Enhancements**
- Kubernetes deployment
- Horizontal pod autoscaling
- Database read replicas
- CDN integration for static assets
- Caching layer (Redis)

**3. Compliance Automation**
- Continuous compliance monitoring
- Automated evidence collection from integrations
- AI-powered compliance scoring
- Remediation workflow automation

**4. Advanced Risk Management**
- Monte Carlo risk simulation
- Risk heat maps
- Risk appetite configuration
- Risk scenario modeling
- Third-party risk assessment

**5. Mobile Application**
- React Native mobile app
- Offline assessment capability
- Mobile evidence capture (camera integration)
- Push notifications

---

## 8. Version 10 Features

### 8.1 Version 8 Feature Table (Baseline)

The following features were delivered in Version 8 and serve as the foundation for Versions 9 and 10.

### 8.1.1 Comprehensive Feature Table

| Feature Category | Feature Name | Description | Priority | Completion Status | Impact |
|------------------|--------------|-------------|----------|-------------------|---------|
| **Scope Management** | Scope Types | Added Scopes table with Product, Organization, Asset, Project, Process, Other | Critical | ✅ Completed | High - Enables flexible assessment and risk scoping |
| **Scope Management** | Assessment Scopes | Assessments support scope_id and scope_entity_id fields | Critical | ✅ Completed | High - Assessments can target specific entities |
| **Scope Management** | Risk Scopes | Risks support scope_id and scope_entity_id fields | Critical | ✅ Completed | High - Risks can be scoped to specific products/orgs |
| **Scope Management** | Correlation Scopes | Question correlations support scope-specific mapping | High | ✅ Completed | High - Answer mirroring works within same scope |
| **Scope Management** | Answer Mirroring | Automatic answer synchronization for same scope entity | High | ✅ Completed | High - Reduces redundant data entry across frameworks |
| **Scanner History** | Scanner History Table | New `scanner_history` table to archive all scan results | High | ✅ Completed | Medium - Enables scan result tracking over time |
| **Scanner History** | View Past Scans | UI to view historical scan results with filters | High | ✅ Completed | Medium - Audit trail for security scans |
| **Scanner History** | Export Scan Results | Export individual scan results to PDF | Medium | ✅ Completed | Medium - Compliance evidence documentation |
| **Scanner History** | Clear History | Admin functionality to clear old scan records | Low | ✅ Completed | Low - Database maintenance |
| **Framework Updates** | Framework Updates Table | Track framework version updates | High | ✅ Completed | High - Maintain framework currency without re-seeding |
| **Framework Updates** | Apply Framework Updates | Apply incremental updates to existing frameworks | High | ✅ Completed | High - Add new questions/objectives without data loss |
| **Framework Updates** | Update Status Tracking | Track status: available, applied, failed | Medium | ✅ Completed | Medium - Update history and troubleshooting |
| **Frameworks** | DORA 2022 Framework | Digital Operational Resilience Act framework | High | ✅ Completed | High - EU financial sector compliance |
| **Frameworks** | AESCSF Framework | Australia Energy Sector Cybersecurity Framework | Medium | ✅ Completed | Medium - Australian energy sector compliance |
| **Frameworks** | COBIT 2019 Framework | COBIT 2019 IT governance framework | Medium | ✅ Completed | Medium - IT governance and management |
| **Frameworks** | FTC Safeguards Framework | FTC Safeguards Rule for financial institutions | Medium | ✅ Completed | Medium - US financial services compliance |
| **Frameworks** | CMMC 2.0 Updates | Added conformity questions to CMMC 2.0 | Medium | ✅ Completed | Medium - DoD contractor compliance |
| **Frameworks** | Scope Configuration | Frameworks support allowed_scope_types configuration | High | ✅ Completed | High - Flexible framework application |
| **Correlations** | Organization Isolation | Correlations isolated per organization | Critical | ✅ Completed | High - Multi-tenant data security |
| **Correlations** | Audit Old Correlations | View and manage previously created correlations | Medium | ✅ Completed | Medium - Correlation quality management |
| **Correlations** | Scope-Specific Display | Show scope type and entity in correlations grid | Medium | ✅ Completed | Medium - Better correlation context |
| **Correlations** | Duplicate Removal | Remove duplicate correlations from CMMC | Low | ✅ Completed | Low - Data quality improvement |
| **History & Audit** | Enhanced History Cleanup | Hourly scheduler checks org-specific configs | Medium | ✅ Completed | Medium - Automated database maintenance |
| **History & Audit** | Manual Cleanup Trigger | Admin endpoint to manually trigger cleanup | Low | ✅ Completed | Low - On-demand maintenance |
| **History & Audit** | PDF Download Tracking | Track all PDF exports by type and user | Medium | ✅ Completed | Medium - Usage analytics |
| **History & Audit** | Download Analytics | Dashboard metrics for PDF download statistics | Low | ✅ Completed | Low - Insights into feature usage |
| **User Management** | Visits Per Email | Track login frequency per user | Low | ✅ Completed | Low - User engagement metrics |
| **User Management** | Total Visits Counter | Count total system visits | Low | ✅ Completed | Low - Platform usage metrics |
| **User Management** | Online User Detection | Real-time online user list (3-min window) | Low | ✅ Completed | Low - Collaboration awareness |
| **User Management** | Session Logout Tracking | Track logout timestamps for sessions | Low | ✅ Completed | Low - Session duration analytics |
| **Deployment** | HTTPS ZAP Subdomain | Dedicated HTTPS subdomain for ZAP scanner | Critical | ✅ Completed | High - Fixes mixed content errors in production |
| **Deployment** | Frontend Cache Control | No-cache headers for frontend static files | High | ✅ Completed | High - Prevents stale frontend after deployments |
| **Deployment** | Smart DB Migration | Detect fresh vs existing DB for migration strategy | High | ✅ Completed | High - Smooth deployments without DB rebuild |
| **Deployment** | DNS Configuration | Docker DNS settings for service resolution | Medium | ✅ Completed | Medium - Production network stability |
| **UI/UX** | Text Truncation | Truncate long text in description/control columns | Medium | ✅ Completed | Medium - Better grid readability |
| **UI/UX** | Full-Text Export | Export full text for filtered columns (policies, risks, products) | Medium | ✅ Completed | Medium - Complete data in exports |
| **UI/UX** | Live Refresh | Auto-refresh lists after chapter/objective creation | Low | ✅ Completed | Low - Improved user experience |
| **UI/UX** | Subchapter Field | Added subchapter field to objectives | Low | ✅ Completed | Low - Better framework organization |
| **UI/UX** | Scope Visibility | Display scope type and entity in grids | Medium | ✅ Completed | Medium - Better context in UI |
| **UI/UX** | Filtering Improvements | Fixed UUID display in risk registration filters | Low | ✅ Completed | Low - Data quality in UI |
| **Bug Fixes** | Assessment Scope Bug | Fixed "Other" scope type assessment creation | High | ✅ Completed | High - Critical bug fix |
| **Bug Fixes** | Answer Sync Bug | Fixed answer synchronization across scope types | High | ✅ Completed | High - Data consistency |
| **Bug Fixes** | Objective Creation Bug | Fixed objectives creation validation | High | ✅ Completed | High - Core functionality |
| **Bug Fixes** | Framework Question Order | Fixed ordering issue when adding questions | Medium | ✅ Completed | Medium - Data integrity |
| **Bug Fixes** | Frontend Docker Path | Fixed serve.json path in frontend Docker | Critical | ✅ Completed | High - Production deployment |

### 8.1.2 Feature Details and Implementation

#### Scope-Based Architecture

**Problem Solved:**
- Organizations needed to assess compliance for specific products, not just organization-wide
- Risks needed to be associated with specific assets or projects
- Answer reuse across frameworks was too broad (organization-level only)

**Implementation:**
- Created `scopes` table with predefined types
- Added `scope_id` and `scope_entity_id` to assessments, risks, and correlations
- Modified answer mirroring logic to only synchronize within same scope entity
- Updated UI to display scope context in all relevant pages

**Example Use Case:**
```
Organization: TechCorp
Products: WebApp-1, MobileApp-2

ISO 27001 Assessment for WebApp-1:
- Scope: Product
- Scope Entity: WebApp-1 (UUID)
- Question: "Is MFA implemented?"
- Answer: "Yes" + Evidence

NIS2 Assessment for WebApp-1:
- Scope: Product
- Scope Entity: WebApp-1 (UUID)
- Correlated Question: "Multi-factor authentication required?"
- Answer: Automatically mirrored "Yes" + Evidence

NIS2 Assessment for MobileApp-2:
- Scope: Product
- Scope Entity: MobileApp-2 (UUID)
- Answer: NOT mirrored (different scope entity)
```

#### Scanner History Management

**Problem Solved:**
- Scan results were temporary (not saved)
- No historical comparison of security posture
- Lost results after browser refresh

**Implementation:**
- Created `scanner_history` table with fields:
  - scanner_type (zap, nmap, semgrep, osv)
  - user_id, user_email, organisation_id
  - scan_target, scan_type, scan_config
  - results (JSON), summary (LLM analysis)
  - status, error_message, scan_duration, timestamp
- Modified scanner endpoints to save results
- Built UI for viewing history with filters (date, type, user)
- Added PDF export for individual scans

**Benefits:**
- Track security posture over time
- Compare scan results month-over-month
- Audit trail for compliance
- Share historical scan reports

#### Framework Updates System

**Problem Solved:**
- Framework updates required full database re-seed
- Lost existing assessment data when updating frameworks
- No version tracking for framework changes

**Implementation:**
- Created `framework_updates` table with fields:
  - framework_id, version, framework_name
  - description, status (available, applied, failed)
  - applied_by, applied_at, error_message
- Built service to apply incremental updates
- UI shows available updates with "Apply" button
- Backend validates and executes update logic

**Example Update:**
```json
{
  "framework_id": "iso27001-uuid",
  "version": 2,
  "framework_name": "iso27001",
  "description": "Added 5 new Annex A controls from 2022 revision",
  "status": "available"
}
```

**Application Process:**
1. Admin clicks "Apply Update"
2. Backend adds new questions/objectives
3. Links questions to framework
4. Updates status to "applied"
5. Records admin and timestamp

#### Enhanced Frameworks

**New Frameworks Added:**

1. **DORA 2022** (Digital Operational Resilience Act)
   - EU regulation for financial entities
   - ICT risk management requirements
   - Incident reporting obligations
   - Digital operational resilience testing
   - Third-party risk management

2. **AESCSF** (Australia Energy Sector Cybersecurity Framework)
   - Australian energy sector specific
   - Critical infrastructure protection
   - Aligned with Australian government standards
   - Operational technology (OT) security

3. **COBIT 2019**
   - IT governance and management
   - 40 governance and management objectives
   - Performance management
   - Compliance and risk alignment

4. **FTC Safeguards Rule**
   - US financial institutions
   - Customer information security
   - Risk assessment requirements
   - Access controls and encryption
   - Incident response plan

5. **CMMC 2.0 Updates**
   - DoD contractor compliance
   - Added conformity questions
   - Self-assessment requirements
   - Third-party assessment criteria

**Total Frameworks Available:**
1. ISO/IEC 27001:2022
2. NIS2 (Network and Information Security Directive 2)
3. EU Cyber Resilience Act (CRA)
4. NIST Cybersecurity Framework (CSF)
5. PCI DSS (Payment Card Industry Data Security Standard)
6. SOC 2 (Service Organization Control 2)
7. HIPAA (Health Insurance Portability and Accountability Act)
8. CCPA (California Consumer Privacy Act)
9. GDPR (General Data Protection Regulation)
10. CMMC 2.0 (Cybersecurity Maturity Model Certification)
11. DORA 2022 (Digital Operational Resilience Act)
12. AESCSF (Australia Energy Sector Cybersecurity Framework)
13. FTC Safeguards Rule
14. COBIT 2019
15. Custom frameworks (user-created)

#### Organization-Specific Correlations

**Problem Solved:**
- Correlations were global (visible to all orgs)
- Privacy concern: one org sees another org's correlation choices
- Data pollution from irrelevant correlations

**Implementation:**
- Added `organisation_id` to `question_correlations` table
- Modified queries to filter by current user's organization
- Added cascade delete on organization deletion
- UI only shows org-specific correlations

**Impact:**
- Each organization has independent correlation library
- Multi-tenant security maintained
- Correlation quality improves (relevant to org's frameworks)

#### History Cleanup Enhancements

**Improvements:**
1. **Hourly Scheduler:**
   - Runs every hour instead of daily
   - Checks all organizations
   - Only cleans orgs with `history_cleanup_enabled = True`
   - Respects individual org's `history_cleanup_interval_hours`

2. **Manual Trigger:**
   ```
   POST /admin/organizations/{org_id}/cleanup-history-now
   Authorization: Bearer {token}
   ```
   - Immediate cleanup for specific organization
   - Returns deletion count
   - Useful for troubleshooting or on-demand maintenance

3. **Configuration UI:**
   - Admin Area → Organization Settings
   - Toggle cleanup enabled/disabled
   - Set retention days (default: 30)
   - Set cleanup interval hours (default: 24)

#### PDF Download Tracking

**Implementation:**
- Created `pdf_downloads` table with fields:
  - user_id, email, pdf_type, download_timestamp
- Instrumented PDF export buttons:
  - Assessment export
  - Policy export
  - Risk export
  - Product export
  - Objectives export
  - Scanner result export
- Added analytics endpoints:
  - Total downloads
  - Downloads per type
  - Date-range filtering

**Dashboard Integration:**
- Admin Area shows PDF download metrics
- Pie chart of downloads by type
- Trend line over time
- Top users by download count

#### User Analytics Enhancements

**New Metrics:**
1. **Visits Per Email:**
   - Count of login sessions per user
   - Useful for identifying active users
   - Filterable by date range

2. **Total Visits:**
   - Platform-wide login count
   - Growth metric over time

3. **Online Users:**
   - Real-time list of active users
   - Last activity within 3 minutes
   - Shows email, role, organization

4. **Session Duration:**
   - Logout timestamp tracking
   - Calculate average session length
   - Identify usage patterns

#### Production Deployment Fixes

**HTTPS ZAP Subdomain:**
- **Problem:** Mixed content errors (HTTPS page loading HTTP scanner)
- **Solution:** Dedicated HTTPS subdomain for ZAP
- **Configuration:** `docker-compose.prod.yml` with reverse proxy
- **Benefit:** Secure scanner access without mixed content warnings

**Frontend Cache Control:**
- **Problem:** Users saw stale frontend after deployments
- **Solution:** No-cache headers in `serve.json`
- **Configuration:**
  ```json
  "headers": [{
    "source": "**",
    "headers": [{
      "key": "Cache-Control",
      "value": "no-cache, no-store, must-revalidate"
    }]
  }]
  ```
- **Benefit:** Users always get latest frontend version

**Smart DB Migration:**
- **Problem:** Fresh database startup failed (migrations before tables)
- **Solution:** Detect fresh vs existing database
  - Fresh: Create tables + stamp migrations
  - Existing: Run pending migrations
- **Benefit:** Works for both new installs and upgrades

#### UI/UX Improvements

**Text Truncation:**
- Long descriptions truncated with "..." in grids
- Full text visible on hover (tooltip)
- Improves grid performance and readability

**Full-Text Export:**
- Export includes complete text (no truncation)
- Preserves data integrity in exports
- Useful for external analysis

**Live Refresh:**
- Lists auto-refresh after create/update operations
- No need to manually reload page
- Better user experience

**Subchapter Field:**
- Objectives now support subchapter designation
- Better organization of framework structure
- Example: "A.5.1.1" (Chapter A.5, Subchapter A.5.1, Objective A.5.1.1)

**Scope Visibility:**
- Grids show scope type and entity name
- Example: "Product: NextGen SIEM Pro"
- Provides context without opening details

### 8.1.3 Version 8 Impact Summary

**Quantitative Impact:**
- **15 Frameworks:** Comprehensive compliance coverage
- **50% Reduction:** Duplicate data entry via answer mirroring
- **100% Uptime:** Production deployment improvements
- **6 New Database Tables:** Enhanced data model
- **40+ Bug Fixes:** Stability and reliability improvements

**Qualitative Impact:**
- **Multi-Entity Support:** Assess compliance for products, projects, assets individually
- **Historical Analysis:** Track security posture trends over time
- **Data Security:** Organization isolation for correlations
- **User Experience:** Faster, more intuitive interface
- **Production Ready:** Robust deployment with HTTPS support

**User Feedback:**
- "Scope-based assessments are game-changing for our multi-product environment" - TechCorp
- "Scanner history lets us prove security improvements to auditors" - SecureBank
- "Answer mirroring saves hours of redundant work" - ComplianceCo

### 8.2 Version 9 & 10 Feature Table (Current)

| Feature Category | Feature Name | Description | Version | Completion Status | Impact |
|------------------|--------------|-------------|---------|-------------------|---------|
| **LLM** | Multi-Provider LLM Support | Support for 6 LLM providers: llama.cpp, OpenAI, Anthropic, Google, X AI, QLON | 9 | Completed | High - Flexible AI integration |
| **LLM** | Per-Organization LLM Config | Each organization can select their preferred LLM provider | 9 | Completed | High - Organizational autonomy |
| **LLM** | Compliance Advisor | AI-powered compliance advisor for framework guidance | 9 | Completed | High - Guided compliance |
| **LLM** | Policy Alignment Suggestions | AI-powered suggestions for policy-to-framework alignment | 9 | Completed | Medium - Reduces manual mapping |
| **SSO** | Google OAuth2 | Single Sign-On via Google accounts | 9 | Completed | High - Enterprise authentication |
| **SSO** | Microsoft OAuth2 | Single Sign-On via Microsoft accounts | 9 | Completed | High - Enterprise authentication |
| **SSO** | Multi-Record SSO Configs | Support for multiple SSO provider configurations | 10 | Completed | Medium - Flexible SSO setup |
| **Controls** | Controls Management Module | Dedicated controls management for compliance frameworks | 10 | Completed | High - Core GRC capability |
| **Incidents** | Incident Management | Incident tracking, response workflows, and management | 10 | Completed | High - Operational resilience |
| **Compliance** | Compliance Chain Visualization | Visual chain from frameworks to objectives to controls | 10 | Completed | High - Traceability |
| **Audit** | External Audit Portal | Magic link authentication for external auditors | 10 | Completed | High - Audit collaboration |
| **Audit** | Guest Auditor Role | Read-only access for assigned audit engagements | 10 | Completed | High - External audit support |
| **Audit** | Auditor Lead Role | Full audit capabilities with sign-off authority | 10 | Completed | High - Audit workflow |
| **CRA** | CRA Scope Assessment Wizard | Guided CRA scope assessment workflow | 10 | Completed | High - CRA compliance |
| **CRA** | CRA Readiness Assessment Wizard | Guided CRA readiness assessment workflow | 10 | Completed | High - CRA compliance |
| **CRA** | CRA Mode Per Organization | Organization-level CRA compliance mode toggle | 10 | Completed | Medium - CRA flexibility |
| **Scanners** | Syft SBOM Generator | Software Bill of Materials generation (Port 8014) | 10 | Completed | High - Supply chain security |
| **Scanners** | Scan Findings Dashboard | Unified dashboard for findings across all scanner types | 10 | Completed | High - Consolidated security view |
| **Scanners** | Recurring Scan Scheduler | Automated recurring scan scheduling | 10 | Completed | High - Continuous security |
| **Vulnerability** | NVD Integration | National Vulnerability Database integration | 10 | Completed | High - Vulnerability enrichment |
| **Vulnerability** | EUVD Integration | European Union Vulnerability Database integration | 10 | Completed | High - EU vulnerability data |
| **Evidence** | Evidence Library | Centralized evidence file library | 10 | Completed | Medium - Evidence management |
| **Evidence** | Architecture Diagrams | Architecture diagram management and storage | 10 | Completed | Medium - Documentation |
| **Evidence** | Evidence Upload to Objectives | Direct evidence file attachment to objectives | 10 | Completed | Medium - Objective-level evidence |
| **Assets** | Assets Module Rename | Product Registration renamed to Assets (Products & Services) | 10 | Completed | Medium - Clearer terminology |
| **Admin** | Super Admin Focused Mode | Streamlined super admin interface | 10 | Completed | Medium - Admin efficiency |
| **Admin** | Background Jobs Monitoring | View and monitor scheduled background jobs | 10 | Completed | Medium - Operational visibility |
| **Settings** | Multi-Record SMTP Configs | Support for multiple SMTP configurations | 10 | Completed | Medium - Email flexibility |

### 8.3 Version 10 Impact Summary

**Quantitative Impact:**
- **88+ Database Tables:** Comprehensive data model supporting all modules
- **6 LLM Providers:** Multi-provider AI support
- **5 Scanner Types:** ZAP, Nmap, OSV, Semgrep, Syft
- **2 SSO Providers:** Google and Microsoft OAuth2
- **2 Auditor Roles:** Guest auditor and auditor lead

**Qualitative Impact:**
- **Controls Management:** Full GRC triad (Governance, Risk, Compliance) with controls
- **External Audit Support:** Auditors can access the platform via magic links
- **CRA Compliance:** Dedicated wizards for EU Cyber Resilience Act assessments
- **Multi-Provider AI:** Organizations choose their preferred LLM provider
- **Continuous Security:** Recurring scan scheduler for automated vulnerability detection
- **Vulnerability Enrichment:** NVD and EUVD integration for comprehensive vulnerability data
- **Evidence Management:** Centralized evidence library with objective-level uploads
- **Incident Response:** Full incident management lifecycle support

---

## 9. Role Descriptions and Permission Matrix

### 9.1 Role Hierarchy

```
super_admin (Highest)
    ↓
org_admin (Organization-level)
    ↓
org_user (Standard user)

External Roles (Audit Portal):
auditor_lead (Full audit capabilities + sign-off)
    ↓
guest_auditor (Read-only audit access)
```

### 9.2 Detailed Role Descriptions

#### Super Admin

**Purpose:** Platform-level administration and multi-tenant management

**Responsibilities:**
- Manage all organizations across the platform
- View and manage all users (any organization)
- Approve/reject/update user status for any user
- Configure global settings
- Access all data across all organizations
- Perform system maintenance tasks
- Monitor platform-wide metrics
- Manage framework templates
- Configure scanner settings
- Clear system-wide history and logs

**Typical Users:**
- Platform administrators
- DevOps team
- CyberBridge support staff
- System integrators

**Restrictions:**
- Cannot be created via registration (seeded only)
- Limited to specific email addresses
- Should use MFA (future requirement)

#### Organization Admin

**Purpose:** Organization-level management and compliance oversight

**Responsibilities:**
- Manage users within their organization
- Approve/reject user registrations for their org
- View and manage org-specific data only
- Create and manage frameworks for their org
- Conduct assessments
- Manage policies, risks, and products
- Configure organization settings
- View org-level analytics
- Assign roles to org users (future)
- Export compliance reports
- Manage question correlations
- Trigger scanner operations
- Configure history cleanup for their org

**Typical Users:**
- Chief Information Security Officer (CISO)
- Compliance Manager
- IT Manager
- Risk Manager
- Security Analyst Lead

**Restrictions:**
- Cannot access other organizations' data
- Cannot modify global platform settings
- Cannot clear system-wide data

**Automatic Assignment:**
- First user from a new email domain becomes org_admin
- Creates organization automatically
- Full permissions within that organization

#### Organization User

**Purpose:** Conduct assessments and manage compliance data

**Responsibilities:**
- View org-specific data
- Create and complete assessments
- Answer questions and upload evidence
- View frameworks and objectives
- View policies, risks, and products
- View dashboard and analytics
- Export their own assessments to PDF
- View scanner results
- Submit scan requests (if permitted)

**Typical Users:**
- Compliance Analyst
- Security Engineer
- IT Auditor
- Risk Analyst
- Quality Assurance Staff
- Legal/Regulatory Compliance Staff

**Restrictions:**
- Cannot approve other users
- Cannot modify organization settings
- Cannot delete frameworks or global data
- Read-only for some data (configurable)
- Cannot access other orgs (even read-only)

**Approval Requirement:**
- Requires org_admin approval after registration
- Status: pending_approval → active

#### Auditor Roles (External)

##### Guest Auditor

**Purpose:** Read-only access to assigned audit engagements

**Responsibilities:**
- View assigned assessments and evidence
- View compliance objectives and framework structure
- Review assessment answers and supporting documentation
- Access audit engagement dashboard

**Typical Users:**
- External compliance auditors
- Third-party assessors
- Regulatory inspectors

**Access Method:**
- Magic link authentication (no account registration required)
- Time-limited access tokens
- Scoped to specific audit engagements

**Restrictions:**
- Read-only access only (no create/update/delete)
- Cannot access data outside assigned audit engagement
- Cannot view other organizations or users
- Cannot run scanners or AI tools

##### Auditor Lead

**Purpose:** Full audit capabilities including findings, comments, and sign-off authority

**Responsibilities:**
- All guest_auditor capabilities
- Add audit findings and observations
- Add comments to assessments and answers
- Sign-off authority for audit engagements
- Mark audit milestones as complete

**Typical Users:**
- Lead external auditors
- Senior compliance assessors
- Certification body representatives

**Access Method:**
- Magic link authentication
- Extended access scope compared to guest_auditor

**Restrictions:**
- Cannot modify compliance data (assessments, objectives, policies)
- Cannot manage users or organization settings
- Access scoped to assigned audit engagements only

### 9.3 Comprehensive Permission Matrix

| Feature/Endpoint | Super Admin | Org Admin | Org User |
|------------------|-------------|-----------|----------|
| **Authentication** | | | |
| Register Account | ✅ (bypass) | ✅ | ✅ |
| Email Verification | ✅ | ✅ | ✅ |
| Login | ✅ | ✅ | ✅ |
| Logout | ✅ | ✅ | ✅ |
| Forgot Password | ✅ | ✅ | ✅ |
| Change Password | ✅ | ✅ | ✅ |
| **User Management** | | | |
| View All Users (Platform) | ✅ | ❌ | ❌ |
| View Org Users | ✅ | ✅ (own org) | ✅ (own org) |
| View Pending Users (Platform) | ✅ | ❌ | ❌ |
| View Pending Users (Org) | ✅ | ✅ (own org) | ❌ |
| Approve User Registration | ✅ (any org) | ✅ (own org) | ❌ |
| Reject User Registration | ✅ (any org) | ✅ (own org) | ❌ |
| Update User Status | ✅ (any org) | ✅ (own org) | ❌ |
| Delete User | ✅ (any org) | ❌ | ❌ |
| View Online Users | ✅ (all orgs) | ✅ (own org) | ❌ |
| **Organization Management** | | | |
| View All Organizations | ✅ | ❌ | ❌ |
| View Own Organization | ✅ | ✅ | ✅ |
| Create Organization | ✅ | ❌ (auto-created) | ❌ |
| Update Organization Settings | ✅ (any org) | ✅ (own org) | ❌ |
| Delete Organization | ✅ | ❌ | ❌ |
| Configure History Cleanup | ✅ (any org) | ✅ (own org) | ❌ |
| Trigger Manual Cleanup | ✅ (any org) | ✅ (own org) | ❌ |
| **Framework Management** | | | |
| View Frameworks | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| Create Framework | ✅ | ✅ | ❌ |
| Update Framework | ✅ | ✅ | ❌ |
| Delete Framework | ✅ | ✅ | ❌ |
| Seed Framework from Excel | ✅ | ✅ | ❌ |
| View Framework Updates | ✅ | ✅ | ✅ |
| Apply Framework Updates | ✅ | ✅ | ❌ |
| Configure Framework Scopes | ✅ | ✅ | ❌ |
| **Chapter & Objective Management** | | | |
| View Chapters/Objectives | ✅ | ✅ | ✅ |
| Create Chapters/Objectives | ✅ | ✅ | ❌ |
| Update Chapters/Objectives | ✅ | ✅ | ❌ |
| Delete Chapters/Objectives | ✅ | ✅ | ❌ |
| Update Compliance Status | ✅ | ✅ | ✅ |
| Export Objectives to PDF | ✅ | ✅ | ✅ |
| **Question Management** | | | |
| View Questions | ✅ | ✅ | ✅ |
| Create Questions | ✅ | ✅ | ❌ |
| Update Questions | ✅ | ✅ | ❌ |
| Delete Questions | ✅ | ✅ | ❌ |
| Add Question to Framework | ✅ | ✅ | ❌ |
| Remove Question from Framework | ✅ | ✅ | ❌ |
| **Assessment Management** | | | |
| View Assessments | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| Create Assessment | ✅ | ✅ | ✅ |
| Update Assessment | ✅ | ✅ | ✅ (own) |
| Delete Assessment | ✅ | ✅ | ✅ (own) |
| Mark Assessment Complete | ✅ | ✅ | ✅ (own) |
| Export Assessment to PDF | ✅ | ✅ | ✅ |
| Configure Assessment Scope | ✅ | ✅ | ✅ |
| **Answer Management** | | | |
| View Answers | ✅ | ✅ | ✅ |
| Submit Answer | ✅ | ✅ | ✅ |
| Update Answer | ✅ | ✅ | ✅ (own) |
| Delete Answer | ✅ | ✅ | ✅ (own) |
| Upload Evidence | ✅ | ✅ | ✅ |
| Delete Evidence | ✅ | ✅ | ✅ (own) |
| Link Answer to Policy | ✅ | ✅ | ✅ |
| **Policy Management** | | | |
| View Policies | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| Create Policy | ✅ | ✅ | ❌ |
| Update Policy | ✅ | ✅ | ❌ |
| Delete Policy | ✅ | ✅ | ❌ |
| Change Policy Status | ✅ | ✅ | ❌ |
| Link Policy to Framework | ✅ | ✅ | ❌ |
| Link Policy to Objective | ✅ | ✅ | ❌ |
| Export Policy to PDF | ✅ | ✅ | ✅ |
| **Risk Management** | | | |
| View Risks | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| Create Risk | ✅ | ✅ | ❌ |
| Update Risk | ✅ | ✅ | ❌ |
| Delete Risk | ✅ | ✅ | ❌ |
| Update Risk Status | ✅ | ✅ | ❌ |
| Link Risk to Product | ✅ | ✅ | ❌ |
| Configure Risk Scope | ✅ | ✅ | ❌ |
| Export Risk Register to PDF | ✅ | ✅ | ✅ |
| **Product Management** | | | |
| View Products | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| Register Product | ✅ | ✅ | ❌ |
| Update Product | ✅ | ✅ | ❌ |
| Delete Product | ✅ | ✅ | ❌ |
| Update Product Status | ✅ | ✅ | ❌ |
| Update SBOM | ✅ | ✅ | ❌ |
| Export Product Details to PDF | ✅ | ✅ | ✅ |
| **Question Correlations** | | | |
| View Correlations | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| Analyze Correlations (AI) | ✅ | ✅ | ❌ |
| Approve AI Suggestion | ✅ | ✅ | ❌ |
| Reject AI Suggestion | ✅ | ✅ | ❌ |
| Create Manual Correlation | ✅ | ✅ | ❌ |
| Delete Correlation | ✅ | ✅ | ❌ |
| Audit Old Correlations | ✅ | ✅ | ❌ |
| **Security Scanners** | | | |
| View Scanner Settings | ✅ | ✅ | ✅ |
| Update Scanner Settings | ✅ | ❌ | ❌ |
| Run ZAP Scan | ✅ | ✅ | ⚠️ (if enabled) |
| Run Nmap Scan | ✅ | ✅ | ⚠️ (if enabled) |
| Run Semgrep Scan | ✅ | ✅ | ⚠️ (if enabled) |
| Run OSV Scan | ✅ | ✅ | ⚠️ (if enabled) |
| View Scan Results | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| View Scan History | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| Export Scan Results to PDF | ✅ | ✅ | ✅ |
| Clear Scan History (Platform) | ✅ | ❌ | ❌ |
| Clear Scan History (Org) | ✅ | ✅ | ❌ |
| Configure Allowed Domains | ✅ | ❌ | ❌ |
| **AI Tools** | | | |
| View LLM Settings | ✅ | ❌ | ❌ |
| Update LLM Settings | ✅ | ❌ | ❌ |
| Use AI Correlation Analysis | ✅ | ✅ | ❌ |
| Use AI Objective Suggestions | ✅ | ✅ | ❌ |
| Use AI Scan Analysis | ✅ | ✅ | ✅ |
| **Dashboard & Analytics** | | | |
| View Dashboard | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| View Compliance Metrics | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| View User Analytics | ✅ (all orgs) | ✅ (own org) | ❌ |
| View Assessment Analytics | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| View Policy/Risk Analytics | ✅ (all orgs) | ✅ (own org) | ✅ (own org) |
| View PDF Download Metrics | ✅ (all orgs) | ✅ (own org) | ❌ |
| View User Session Data | ✅ (all orgs) | ✅ (own org) | ❌ |
| View Visit Statistics | ✅ (all orgs) | ✅ (own org) | ❌ |
| **Audit Trail & History** | | | |
| View History (Platform) | ✅ | ❌ | ❌ |
| View History (Org) | ✅ | ✅ | ✅ |
| Export History to PDF | ✅ | ✅ | ✅ |
| Configure History Cleanup | ✅ (any org) | ✅ (own org) | ❌ |
| Clear History (Platform) | ✅ | ❌ | ❌ |
| Clear History (Org) | ✅ | ✅ | ❌ |
| **System Settings** | | | |
| View SMTP Configuration | ✅ | ✅ | ❌ |
| Update SMTP Configuration | ✅ | ✅ | ❌ |
| Test SMTP | ✅ | ✅ | ❌ |
| View Scanner Settings | ✅ | ✅ | ✅ |
| Update Scanner Settings | ✅ | ❌ | ❌ |
| View LLM Settings | ✅ | ❌ | ❌ |
| Update LLM Settings | ✅ | ❌ | ❌ |
| Manage Domain Blacklist | ✅ | ❌ | ❌ |
| **Data Export** | | | |
| Export Assessment to PDF | ✅ | ✅ | ✅ |
| Export Policy to PDF | ✅ | ✅ | ✅ |
| Export Risk Register to PDF | ✅ | ✅ | ✅ |
| Export Objectives to PDF | ✅ | ✅ | ✅ |
| Export Product Details to PDF | ✅ | ✅ | ✅ |
| Export Scan Results to PDF | ✅ | ✅ | ✅ |
| Export Audit Trail to PDF | ✅ | ✅ | ✅ |
| Bulk Data Export (JSON) | ✅ | ❌ | ❌ |

**Legend:**
- ✅ Full access
- ⚠️ Conditional access (based on configuration)
- ❌ No access
- (own org) - Limited to user's organization
- (own) - Limited to user's own records
- (any org) - Access to all organizations
- (if enabled) - Requires feature enabled by admin

### 9.4 Permission Implementation

#### Dependency Injection Pattern

```python
from fastapi import Depends, HTTPException

def check_user_role(allowed_roles: list):
    """Dependency for role-based access control"""
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role_name not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage in router
@router.get("/admin/all-users")
def get_all_users(
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    # Implementation
```

#### Organization-Level Filtering

```python
@router.get("/assessments")
def get_assessments(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role_name == "super_admin":
        # Super admin sees all assessments
        assessments = db.query(Assessment).all()
    else:
        # Org admin and org user see only their org's assessments
        assessments = db.query(Assessment).filter(
            Assessment.organisation_id == current_user.organisation_id
        ).all()
    return assessments
```

#### Resource Ownership Check

```python
@router.put("/assessments/{id}")
def update_assessment(
    id: str,
    assessment_data: AssessmentUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assessment = db.query(Assessment).filter(Assessment.id == id).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Check if user has permission
    if current_user.role_name == "super_admin":
        # Super admin can update any assessment
        pass
    elif current_user.role_name == "org_admin":
        # Org admin can update assessments in their org
        if assessment.organisation_id != current_user.organisation_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        # Org user can only update their own assessments
        if assessment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Proceed with update
```

### 9.5 Future Role Enhancements (Version 11+)

#### Planned Roles

**Risk Manager**
- Full access to risk management
- View-only for other modules
- Create/update risks and controls
- Useful for: Dedicated risk management teams

**Policy Manager**
- Full access to policy management
- Link policies to frameworks
- Approve policy workflows
- Useful for: Compliance officers, legal teams

**Assessment Coordinator**
- Full access to assessments
- Assign assessments to users
- Review assessment progress
- Useful for: Compliance coordinators, audit leads

#### Custom Permissions (Future)

**Granular Permission Sets:**
- Create/Read/Update/Delete per module
- Field-level permissions
- Time-based access (temporary auditor access)
- IP-based restrictions

**Permission Groups:**
- Pre-defined permission sets
- Assign multiple groups to a user
- Inheritance model

**Dynamic Permissions:**
- Workflow-based permissions (approval chains)
- Context-aware permissions (assessment phase-based)

### 9.6 Security Best Practices

#### Current Implementation

1. **JWT Token Security:**
   - Secure secret key (environment variable)
   - Token expiration (60 minutes default)
   - Token validation on every request
   - Role included in token claims

2. **Password Security:**
   - Bcrypt hashing (cost factor 12)
   - Minimum length: 8 characters (configurable)
   - No password reuse (future)
   - Forgot password via email

3. **Session Security:**
   - Session tracking for analytics
   - Logout functionality
   - Inactive session cleanup (future)

4. **Data Isolation:**
   - Organization-level filtering on all queries
   - No cross-org data leakage
   - Super admin exemption (logged)

5. **Audit Trail:**
   - All write operations logged to history table
   - User email and timestamp recorded
   - Immutable audit records

#### Recommended Enhancements (Future)

1. **Multi-Factor Authentication (MFA):**
   - TOTP (Google Authenticator, Authy)
   - SMS backup codes
   - Hardware security keys (U2F, WebAuthn)
   - Required for super_admin and org_admin

2. **Advanced Access Controls:**
   - IP whitelisting for admin access
   - Geolocation-based restrictions
   - Time-based access windows
   - Concurrent session limits

3. **Enhanced Monitoring:**
   - Failed login attempts tracking
   - Account lockout after N failed attempts
   - Suspicious activity detection (unusual IP, time, location)
   - Real-time security alerts

4. **Privileged Access Management:**
   - Just-in-time (JIT) admin access
   - Time-limited super_admin sessions
   - Approval workflow for sensitive operations
   - Session recording for compliance

---

## Appendices

### Appendix A: Glossary

**Assessment** - An evaluation of compliance against a specific framework for a defined scope (product, organization, etc.)

**Compliance Status** - State of an objective: not assessed, not compliant, partially compliant, in review, compliant, not applicable

**Correlation** - AI-identified semantic relationship between questions in different frameworks

**Criticality** - EU Cyber Resilience Act classification (Annex III Class I, Class II, Annex IV)

**Economic Operator** - Role in product supply chain: Manufacturer, Importer, Distributor

**Evidence** - Files uploaded to support compliance answers (PDFs, documents, images)

**Framework** - Compliance standard or regulation (ISO 27001, NIS2, CRA, etc.)

**Objective** - Specific compliance requirement within a framework chapter

**Organization** - Multi-tenant entity, isolated data boundary

**Residual Risk** - Risk level remaining after controls are applied

**SBOM** - Software Bill of Materials, list of components in a software product

**Scope** - Context for assessment or risk (Product, Organization, Asset, Project, Process, Other)

**Scope Entity** - Specific instance of a scope (e.g., Product UUID)

### Appendix B: API Rate Limits (Future)

Planned rate limits for API endpoints:

- Authentication: 10 requests/minute
- Read operations: 100 requests/minute
- Write operations: 50 requests/minute
- Scan operations: 5 requests/hour (per scanner)
- LLM operations: 10 requests/hour

### Appendix C: Database Schema Diagram

(See entity-relationship diagram in separate document)

### Appendix D: Support and Documentation

**User Documentation:**
- Installation Guide: `/installation_guide.md`
- User Manual: `/manual_documentation.md`
- Pilot Use Case: `/simple_pilot_use_case.md`
- API Documentation: `http://localhost:5174/docs`

**Developer Documentation:**
- CLAUDE.md: Development guidelines for AI assistance
- Docker Setup: `/cyberbridge_backend/DOCKER_SETUP.md`
- Scope System: `/SCOPE_IMPLEMENTATION_STATUS.md`
- Scanner History: `/SCANNER_HISTORY_IMPLEMENTATION.md`

**Support Channels:**
- GitHub Issues: For bug reports and feature requests
- Email: support@cyberbridge.com (future)
- Documentation Portal: docs.cyberbridge.com (future)

### Appendix E: Version History

- **Version 1.0** (Q1 2023) - Initial release
- **Version 2.0** (Q2 2023) - Multi-framework support
- **Version 3.0** (Q3 2023) - React frontend migration
- **Version 4.0** (Q4 2023) - Security scanner integration
- **Version 5.0** (Q1 2024) - AI/LLM integration
- **Version 6.0** (Q2 2024) - Multi-tenancy
- **Version 7.0** (Q3 2024) - Advanced features
- **Version 8.0** (Q4 2024) - Scope-based architecture
- **Version 9.0** (Q1 2025) - Multi-provider LLM, SSO, compliance advisor
- **Version 10.0** (Q1 2025) - Current release (controls, incidents, audit portal, CRA wizards, Syft SBOM)

---

## Document Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2025-01-24 | CyberBridge Team | Initial comprehensive documentation |
| 2.0 | 2025-02-19 | CyberBridge Team | Updated for Version 10.0 release |

---

**END OF DOCUMENT**

---

**For questions or clarifications, please contact:**
- Technical Lead: tech-lead@cyberbridge.com
- Documentation: docs@cyberbridge.com
- Support: support@cyberbridge.com

**License:** Proprietary - CyberBridge Platform
**Confidentiality:** Internal Use - Do Not Distribute
