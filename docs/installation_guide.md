# CyberBridge Installation Guide

This guide provides two methods to install and run the CyberBridge cybersecurity compliance assessment platform(GRC).

## Quick Start (One-Command Install)

The fastest way to deploy CyberBridge is with the automated installation script. It detects your environment, installs Docker if needed, and deploys all services automatically.

```bash
# Clone the repository and run the installer
git clone <repository-url> cyberbridge
cd cyberbridge
./install.sh
```

The script will:
1. Detect your OS (Ubuntu/Debian, CentOS/RHEL, macOS) and CPU architecture (amd64/arm64)
2. Install Docker and Docker Compose if they are not already installed
3. Check disk space, RAM, and port availability
4. Ask you to choose a deployment scenario (HTTPS domain, IP address, or localhost)
5. Ask you to choose a deployment method (Docker Compose or direct docker run)
6. Build all 12 Docker images with the correct architecture-specific Dockerfiles
7. Start containers in the correct dependency order
8. Verify all services are healthy and print access URLs

**Options:**
- `--skip-llm` — Skip the LLM service (saves ~10 min build time and 13GB RAM)

```bash
# Example: deploy without the LLM service
./install.sh --skip-llm
```

**Notes:**
- The script never modifies `docker-compose.yml` — it generates `docker-compose.generated.yml` instead
- Full build output is logged to `/tmp/cyberbridge_install.log`
- Re-running the script is safe (idempotent) — it detects existing containers and offers to reinstall or keep data

---

## Updating CyberBridge

After the initial installation, use the update script to pull new changes and selectively rebuild only the services that were modified.

```bash
# Pull latest code and rebuild only what changed
./update.sh --pull

# Preview what would be rebuilt without making changes
./update.sh --pull --dry-run

# Rebuild all services (e.g. after a major release)
./update.sh --force-all

# Rebuild changed services without pulling (if you pulled manually)
./update.sh
```

**How it works:**
1. Loads deployment configuration saved by `install.sh` (architecture, URLs, deploy method)
2. Detects which files changed since the last install/update using `git diff`
3. Maps changed directories to their corresponding Docker services
4. Rebuilds and restarts only the affected containers
5. Verifies health of all services

**Options:**
- `--pull` — Run `git pull` before detecting changes
- `--force-all` — Rebuild all services regardless of what changed
- `--dry-run` — Show what would be rebuilt without actually doing it
- `--help` — Show usage information

**Notes:**
- The update script requires `.cyberbridge.env` (created automatically by `install.sh`). If you installed CyberBridge before this feature was added, re-run `./install.sh` once to generate it.
- Database migrations are handled automatically — the backend runs `alembic upgrade head` on startup.
- Changing a scanner (e.g. `nmap/`) only rebuilds that scanner. Use `--force-all` to rebuild everything.
- Build output is logged to `/tmp/cyberbridge_update.log`

---

## Manual Installation

The sections below describe how to install manually if you prefer full control over each step.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)
- Minimum 8GB RAM and 4 CPU cores recommended
- At least 20GB of free disk space

## Important: Production Configuration

When deploying to production, you must configure URLs during both the backend and frontend build processes:

1. **Backend** needs the **backend API URL** (for generating email verification and password reset links)
2. **Frontend** needs the **backend API URL** (to send API requests)

**Note**: CORS configuration is automatic - the backend will automatically allow requests from the configured frontend domain in production.

### Deployment Scenarios:

#### **Scenario 1: Production with Custom Domains and HTTPS** (Recommended)
- Frontend domain: `https://your-frontend-domain.com`
- Backend API subdomain: `https://api.your-domain.com`
- Requires: SSL certificate and reverse proxy/load balancer
- Backend API subdomain points to server IP on port 5174

#### **Scenario 2: On-Premise with IP Addresses (HTTP)**
- Frontend: `http://YOUR_SERVER_IP:5173`
- Backend API: `http://YOUR_SERVER_IP:5174`
- No SSL required, simpler setup
- Note: Not recommended for production due to security concerns

#### **Scenario 3: Local Development**
- Uses localhost defaults, no build args needed
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

**Replace the URLs in the build commands below based on your deployment scenario.**

#Steps:
Build images:

cd cyberbridge

cd zapproxy
docker build -t zap .

cd..
cd nmap
docker build -t nmap .

cd..
cd osvscanner
docker build -f Dockerfile.amd64 -t osv .

cd..
cd semgrep
docker build -t semgrep .

cd..
cd syft
docker build -t syft .

cd..
cd embeddings
docker build -t embeddings .

cd..
cd llm
docker build -t llm .

cd ..
cd postgres
docker build -f Dockerfile.defaults -t cyberbridge_postgres .

cd ..
cd cyberbridge_backend
# Replace with your BACKEND API URL (used for email verification links)
# Scenario 1 (HTTPS with domain):
docker build --build-arg API_BASE_URL_PROD=https://api.cyberbridge.eu -t cyberbridge_backend .
# Scenario 2 (HTTP with IP):
# docker build --build-arg API_BASE_URL_PROD=http://YOUR_SERVER_IP:5174 -t cyberbridge_backend .

cd ..
cd cyberbridge_frontend
# Replace with your BACKEND API URL (for making API requests)
# Scenario 1 (HTTPS with domain - no port needed, handled by reverse proxy):
docker build --build-arg VITE_PRODUCTION_IP=https://api.cyberbridge.eu -t cyberbridge_frontend .
docker build --no-cache --build-arg VITE_PRODUCTION_IP=https://api.cyberbridge.eu -t cyberbridge_frontend .
# Scenario 2 (HTTP with IP):
# docker build --build-arg VITE_PRODUCTION_IP=http://YOUR_SERVER_IP:5174 -t cyberbridge_frontend .


Create Network:
docker network create cyberbridge-network

Stop and Remove in 1 Command:
Force remove (stops and removes in one command)
  docker rm -f cyberbridge_frontend cyberbridge_backend

Run Containers:
docker run -d --name zap --network cyberbridge-network -p 8010:8000 -v zap_data:/root/.ZAP --restart unless-stopped zap
docker run -d --name nmap --network cyberbridge-network -p 8011:8000 --restart unless-stopped nmap
docker run -d --name osv --network cyberbridge-network -p 8012:8000 --restart unless-stopped osv
docker run -d --name semgrep --network cyberbridge-network -p 8013:8000 --restart unless-stopped semgrep
docker run -d --name syft --network cyberbridge-network -p 8014:8000 --restart unless-stopped syft
docker run -d --name llm --network cyberbridge-network -p 8015:8015 \
  --memory="13g" --memory-swap="13g" \
  --restart unless-stopped \
  llm
docker run -d --name cyberbridge_db --network cyberbridge-network -p 5433:5432 --restart unless-stopped cyberbridge_postgres
docker run -d --name embeddings --network cyberbridge-network -p 8016:8000 --memory="1g" --restart unless-stopped embeddings
docker run -d --name searxng --network cyberbridge-network -p 8040:8080 -v $(pwd)/searxng/settings.yml:/etc/searxng/settings.yml:ro --restart unless-stopped searxng/searxng:latest
docker run -d --name cyberbridge_backend --network cyberbridge-network -p 5174:8000 --restart unless-stopped cyberbridge_backend
docker run -d --name cyberbridge_frontend -p 5173:5173 --restart unless-stopped cyberbridge_frontend

UPDATE OPTION(in case you want to add a flag to container for example...):
Option 1: Update existing containers (quick)
  docker update --restart unless-stopped zap nmap osv semgrep syft llm embeddings searxng cyberbridge_db cyberbridge_backend cyberbridge_frontend
  docker start zap nmap osv semgrep syft llm embeddings searxng cyberbridge_db cyberbridge_backend cyberbridge_frontend

  Option 2: Recreate containers (recommended - uses updated commands from installation_guide.md)
  # Stop and remove all
  docker rm -f cyberbridge_frontend cyberbridge_backend cyberbridge_db llm embeddings searxng zap nmap osv semgrep syft

### Access the Application via the linux environment(not inside the docker container):
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5174
- **Database**: localhost:5433
- **Security Services**:
  - ZAP Proxy: http://localhost:8010
  - Nmap: http://localhost:8011
  - OSV Scanner: http://localhost:8012
  - Semgrep: http://localhost:8013
  - Syft SBOM: http://localhost:8014
- **LLM Service**: http://localhost:8015
- **Embeddings Service**: http://localhost:8016
- **SearXNG (Regulatory Monitor)**: http://localhost:8040

---

## Troubleshooting

### Common Issues

**Scanner services (Nmap, Semgrep, OSV, ZAP, Syft) not working:**
- Ensure all containers are on the `cyberbridge-network`
- The backend uses container names as hostnames (e.g., `http://nmap:8000`)
- Check container logs: `docker logs -f [container_name]`

**Disk full / 500 errors / CORS errors on login:**
- ZAP accumulates session data in `/root/.ZAP` which can fill the disk over time
- The ZAP container includes automatic cleanup on startup and every 6 hours, but always use the `-v zap_data:/root/.ZAP` volume flag to keep ZAP data in a managed Docker volume
- To manually clear ZAP data: `docker exec zap sh -c 'rm -rf /root/.ZAP/session/* /root/.ZAP/transfer/* /root/.ZAP/db/*'`
- Check disk usage: `df -h`

### Reinstalling a Container
```bash
cd path_to_dockerfile
docker build -t container_name .
docker stop container_name
docker rm container_name
docker run [options] container_name
docker logs -f container_name  # View logs
```

### Drop and Recreate the Database

If you need to completely reset the database (e.g., after schema changes, corrupted data, or to start fresh), run the following SQL commands against your PostgreSQL instance:

```sql
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
ALTER ROLE postgres SET search_path TO public;
```

**How to execute:**

**Option 1: Using a database client** (e.g., DBeaver, pgAdmin, DataGrip, or VS Code SQL tools)
- Connect to `localhost:5433` with user `postgres` / password `postgres`
- Run the SQL commands above

**Option 2: Using the command line**
```bash
docker exec -i cyberbridge_db psql -U postgres -d postgres -c "
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
ALTER ROLE postgres SET search_path TO public;
"
```

After resetting the database, restart the backend to trigger automatic seeding:
```bash
docker restart cyberbridge_backend
```

> **Note:** This will delete ALL data (users, assessments, frameworks, scan history, etc.). The backend will re-seed default roles, organizations, and lookup data on restart.

## Service Ports Summary

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 | React web application |
| Backend API | 5174 | FastAPI REST service |
| Database | 5433 | PostgreSQL database |
| ZAP Proxy | 8010 | Security scanning service |
| Nmap | 8011 | Network scanning service |
| OSV Scanner | 8012 | Vulnerability scanning service |
| Semgrep | 8013 | Code analysis service |
| Syft SBOM | 8014 | SBOM generation service |
| LLM (llama.cpp) | 8015 | AI/ML inference service |
| CTI Service | 8020 | Cyber Threat Intelligence aggregation service |
| Redis Dark Web | 6382 | Dark web scan queue |
| Dark Web Scanner | 8030 | Dark web scanning service |
| Embeddings | 8016 | Semantic search embeddings service |
| SearXNG | 8040 | Meta-search engine for regulatory monitoring |

---

## CTI Service and Dark Web Scanner

### CTI Service

The CTI (Cyber Threat Intelligence) service is a lightweight FastAPI microservice that stores scanner results directly in the shared PostgreSQL database and serves aggregated threat intelligence data. It replaces the previous OpenCTI-based stack with a single container.

**Key features:**
- Polls scanner APIs (Nmap, ZAP) on a configurable schedule
- Accepts pushed results via `POST /api/ingest/{source}` for real-time updates
- Syncs MITRE ATT&CK and CISA KEV threat feeds automatically
- Stores all data in `cti_`-prefixed PostgreSQL tables

**Environment variables** (set in `docker-compose.yml`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@cyberbridge_db:5432/postgres` |
| `NMAP_SERVICE_URL` | Nmap scanner API URL | `http://nmap:8000` |
| `ZAP_SERVICE_URL` | ZAP scanner API URL | `http://zap:8000` |
| `SEMGREP_SERVICE_URL` | Semgrep scanner API URL | `http://semgrep:8000` |
| `OSV_SERVICE_URL` | OSV scanner API URL | `http://osv:8000` |
| `SCANNER_POLL_INTERVAL` | Polling interval in seconds | `3600` |

### Dark Web Scanner Configuration

The dark web scanner can be configured through the frontend settings page (`/dark-web/settings`) or via environment variables:

- **Max Workers:** Controls the number of concurrent scan workers (1-10). Higher values increase throughput but consume more resources.
- **Search Engines:** 23 dark web search engines are available and can be individually enabled or disabled through the settings page.
- **Tor Proxy:** The scanner uses a built-in SOCKS5 proxy for Tor network access. No additional Tor configuration is required.

> **Note:** The dark web scanner settings page is restricted to admin users only.

---

## Embeddings Service (RAG)

The Embeddings service provides semantic search capabilities using vector embeddings for Retrieval-Augmented Generation (RAG). It embeds framework objectives into a pgvector database and enables the AI chatbot to retrieve relevant compliance context.

**Key features:**
- Uses SentenceTransformer model (all-MiniLM-L6-v2) for 384-dimensional embeddings
- Stores embeddings in PostgreSQL using the pgvector extension
- Provides semantic search for the AI Assistant chatbot
- Memory limit: 1GB

**Environment variables** (set in `docker-compose.yml`):

| Variable | Description | Default |
|----------|-------------|---------|
| (none required) | The service is self-contained | - |

> **Note:** The pgvector extension is automatically installed by the PostgreSQL Dockerfile (`postgres/init-pgvector.sql`).

---

## SearXNG (Regulatory Change Monitor)

SearXNG is a self-hosted meta-search engine used by the Regulatory Change Monitor feature to scan the web for regulatory updates affecting compliance frameworks.

**Key features:**
- Aggregates results from Google, Bing, DuckDuckGo, and Google Scholar
- Provides web search capabilities for regulatory change detection
- Self-hosted for privacy — no external API keys required

**Configuration:**
- Settings file: `searxng/settings.yml`
- The backend connects via `SEARXNG_URL` environment variable (default: `http://searxng:8080`)

---

## Production Deployment Notes

When deploying with custom domains (e.g., `https://access.cyberbridge.eu` and `https://api.cyberbridge.eu`):

### Important Points

1. **Docker containers only need correct build arguments** - Already configured in lines 72 and 80 above
2. **Exposed ports remain the same**:
   - Frontend: port **5173**
   - Backend: port **5174**
3. **DNS, SSL, and Reverse Proxy** are handled by your network administrator (external to this server)
4. **The containers just need to be running** - The reverse proxy will route traffic to them

### For Network Administrators

If your network admin needs to configure the reverse proxy/load balancer:
- Route `https://access.cyberbridge.eu` → `[SERVER_IP]:5173`
- Route `https://api.cyberbridge.eu` → `[SERVER_IP]:5174`

The Docker containers will automatically configure CORS to accept requests from your frontend domain.

---


