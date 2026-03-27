# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CyberBridge is a cybersecurity compliance assessment platform with a microservices architecture. It includes a React frontend, FastAPI backend, and multiple security scanning services (Nmap, ZAP Proxy, Semgrep, OSV Scanner) orchestrated with Docker Compose.

## Architecture

### Core Components
- **Frontend**: React + TypeScript + Vite + Ant Design, using Zustand for state management and Wouter for routing
- **Backend**: FastAPI with SQLAlchemy ORM, PostgreSQL database
- **Security Services**: Containerized microservices for vulnerability scanning
- **CTI Service**: Cyber Threat Intelligence aggregation microservice with MITRE ATT&CK and CISA KEV feeds
- **Dark Web Scanner**: Tor-based dark web intelligence gathering service with PDF report generation
- **LLM Integration**: llama.cpp with phi-4 model for AI-powered analysis
- **Embeddings Service**: SentenceTransformer-based semantic search for RAG (Retrieval-Augmented Generation)
- **SearXNG**: Self-hosted meta-search engine for regulatory change monitoring

### Directory Structure
- `cyberbridge_frontend/` - React frontend application
- `cyberbridge_backend/` - FastAPI backend with MVC architecture
- `nmap/`, `zapproxy/`, `semgrep/`, `osvscanner/` - Security scanning microservices
- `syft/` - SBOM generator microservice
- `cti/service/` - CTI microservice (stores scanner results in PostgreSQL, serves aggregated threat intelligence)
- `darkweb/` - Dark web scanner microservice (Tor-based search, PDF reports, PostgreSQL queue)
- `llamacpp/` - LLM service container (llama.cpp)
- `embeddings/` - Embeddings microservice (SentenceTransformer, pgvector RAG)
- `searxng/` - SearXNG meta-search engine configuration for regulatory monitoring
- `postgres/` - Database initialization scripts (includes pgvector extension)
- `docs/` - Project documentation

### Backend Architecture
The FastAPI backend follows MVC pattern:
- `models/` - SQLAlchemy database models
- `repositories/` - Data access layer
- `routers/` - API controllers/endpoints  
- `services/` - Business logic layer
- `seeds/` - Database seeding utilities
- `dtos/` - Pydantic schemas for request/response validation

### Frontend Architecture  
React application with:
- `pages/` - Route components for different screens
- `components/` - Reusable UI components
- `store/` - Zustand stores for state management
- `constants/` - API URLs and grid column definitions
- `utils/` - PDF generation utilities

## Development Commands

### Frontend Development
```bash
cd cyberbridge_frontend
npm install          # Install dependencies
npm run dev          # Start development server (port 5173)
npm run build        # Build for production
npm run lint         # Run ESLint
npm run preview      # Preview production build
```

### Backend Development
```bash
cd cyberbridge_backend
pip install -r requirements.txt    # Install dependencies
uvicorn app.main:app --reload      # Start development server (port 8000)
```

### Docker Development
```bash
docker-compose up -d               # Start all services
docker-compose down                # Stop all services
docker-compose logs [service]      # View service logs
```

## Service Ports
- Frontend: 5173
- Backend API: 8000
- Database: 5433 (mapped from 5432)
- ZAP Proxy: 8010
- Nmap: 8011
- OSV Scanner: 8012
- Semgrep: 8013
- Syft (SBOM): 8014
- LLM (llama.cpp): 8015
- Embeddings (RAG): 8016
- CTI Service: 8020
- Dark Web Scanner: 8030 (internal 8001)
- SearXNG (Regulatory Monitor): 8040 (internal 8080)

## Key Features
- User authentication and role-based access control (JWT, SSO, magic links for auditors)
- Framework-based compliance assessments (CRA, ISO 27001, NIS2, NIST, etc.)
- Risk and policy management with compliance chain visualization
- Asset registration and CE marking checklists
- Controls management with library templates
- Security scanning integration (OWASP ZAP, Nmap, Semgrep, OSV, Syft)
- Cyber Threat Intelligence (CTI) dashboard with MITRE ATT&CK mapping
- Dark web intelligence scanning with Tor-based search across 23 engines
- Incident management with ENISA notification support
- External audit engagements with magic link authentication
- PDF export functionality
- AI-powered analysis (llama.cpp, OpenAI, Anthropic, Google, X AI, QLON)
- RAG-enhanced AI Assistant with semantic search over framework objectives (pgvector embeddings)
- AI Compliance Roadmap generation for non-compliant objectives
- Regulatory Change Monitor with SearXNG web scanning and LLM analysis
- Compliance Certificate generation with SHA256 verification and 1-year validity
- Regulatory Submissions to authorities with pre-configured email directory
- Framework snapshot and revert system for regulatory updates
- EU Vulnerability Database (EUVD) and NVD synchronization
- Automated backup and restore system

## Database
PostgreSQL with UUID primary keys, role-based user system, and comprehensive audit trailing. Database automatically seeds on startup with default roles, organizations, and lookup data.

### Database Schema Relationships

**Core Entities:**
- Role has many User
- User belongs to one Role
- Organisation has many User
- User belongs to one Organisation
- Organisation has many Framework
- Framework belongs to one Organisation

**Assessment Framework:**
- AssessmentType has many Question
- Question belongs to one AssessmentType
- Framework has many FrameworkQuestion (junction table)
- Question has many FrameworkQuestion (junction table)
- FrameworkQuestion belongs to one Framework
- FrameworkQuestion belongs to one Question

**Assessment Process:**
- Framework has many Assessment
- Assessment belongs to one Framework
- User has many Assessment
- Assessment belongs to one User
- AssessmentType has many Assessment
- Assessment belongs to one AssessmentType
- Assessment has many Answer
- Answer belongs to one Assessment
- Question has many Answer
- Answer belongs to one Question

**Policy Management:**
- PolicyStatus has many Policy
- Policy belongs to one PolicyStatus
- Policy has many Answer (optional assignment)
- Answer belongs to one Policy (optional)
- Policy has many PolicyFramework (junction table)
- Framework has many PolicyFramework (junction table)
- PolicyFramework belongs to one Policy
- PolicyFramework belongs to one Framework

**Chapter and Objectives:**
- Framework has many Chapter
- Chapter belongs to one Framework
- Chapter has many Objective
- Objective belongs to one Chapter
- ComplianceStatus has many Objective (optional)
- Objective belongs to one ComplianceStatus (optional)
- Policy has many PolicyObjective (junction table)
- Objective has many PolicyObjective (junction table)
- PolicyObjective belongs to one Policy
- PolicyObjective belongs to one Objective

**Evidence and Files:**
- Answer has many Evidence
- Evidence belongs to one Answer

**Product Management:**
- ProductStatus has many Product
- Product belongs to one ProductStatus
- EconomicOperator has many Product
- Product belongs to one EconomicOperator
- ProductType has many Product
- Product belongs to one ProductType
- Criticality has many Product (optional)
- Product belongs to one Criticality (optional)
- Criticality has many CriticalityOption
- CriticalityOption belongs to one Criticality

**Risk Management:**
- ProductType has many Risk (optional)
- Risk belongs to one ProductType (optional)
- ProductType has many RiskCategory (optional)
- RiskCategory belongs to one ProductType (optional)
- RiskSeverity has many Risk (as likelihood)
- Risk belongs to one RiskSeverity (as likelihood)
- RiskSeverity has many Risk (as residual_risk)
- Risk belongs to one RiskSeverity (as residual_risk)
- RiskSeverity has many Risk (as risk_severity_id)
- Risk belongs to one RiskSeverity (as risk_severity_id)
- RiskStatus has many Risk
- Risk belongs to one RiskStatus

**CTI (Cyber Threat Intelligence):**
- CtiIndicator stores normalized findings from all scanners (name, source, confidence, severity, CWE, port, URL, etc.)
- CtiAttackPattern stores MITRE ATT&CK techniques (mitre_id, name, tactic, URL)
- CtiIndicatorAttackPattern junction table links indicators to attack patterns
- CtiSighting records when/where indicators were observed
- CtiMalware stores malware family information
- CtiKevEntry stores CISA Known Exploited Vulnerabilities (cve_id, vendor, product, due_date)
- CtiThreatFeed tracks feed sync status (mitre_attack, cisa_kev)

**Dark Web Intelligence:**
- DarkwebScan tracks scan jobs (keyword, status, engines, params, result with base64 PDF, timestamps)
- DarkwebSettings stores per-org configuration (max_workers 1-10, enabled_engines list)

## Testing
Test files are present in both frontend and backend directories. Run tests using standard frameworks for each technology stack.