#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# CyberBridge — One-Command Installation Script
# Detects environment, installs Docker if needed, and deploys all services.
# Usage: ./install.sh [--skip-llm]
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ─────────────────────────── 1. Constants & Colors ───────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/cyberbridge_install.log"

# Service configuration
NETWORK_NAME="cyberbridge-network"
CONTAINERS=(cyberbridge_db cyberbridge_zap cyberbridge_nmap cyberbridge_osv cyberbridge_semgrep cyberbridge_syft cyberbridge_llamacpp cyberbridge_embeddings cyberbridge_backend cyberbridge_frontend cyberbridge_cti_service cyberbridge_darkweb_redis cyberbridge_darkweb_scanner)
PORTS=(5433 8010 8011 8012 8013 8014 11435 8016 5174 5173 8020 6382 8030)
PORT_LABELS=("PostgreSQL DB" "ZAP Proxy" "Nmap Scanner" "OSV Scanner" "Semgrep" "Syft SBOM" "llama.cpp LLM" "Embeddings" "Backend API" "Frontend" "CTI Service" "Redis DarkWeb" "Dark Web Scanner")

MIN_DISK_GB=40
MIN_RAM_GB=16
LLM_RAM_GB=10

SKIP_LLM=false
DEPLOY_METHOD=""
SCENARIO=""
API_BASE_URL=""
VITE_PRODUCTION_IP=""
VITE_BACKEND_PORT=""
ARCH=""
OS_FAMILY=""
COMPOSE_CMD=""
HEALTH_TIMEOUT=300  # 5 minutes
JWT_SECRET=""

# ─────────────────────────── 2. Utility Functions ────────────────────────────
log_info()    { echo -e "${BLUE}[INFO]${RESET}    $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET}   $*"; }
log_step()    { echo -e "\n${BOLD}${CYAN}>>> $*${RESET}"; }

die() {
    log_error "$*"
    log_error "See ${LOG_FILE} for details."
    exit 1
}

spinner() {
    local pid=$1
    local label=$2
    local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  ${CYAN}${frames[$i]}${RESET} %s " "$label"
        i=$(( (i + 1) % ${#frames[@]} ))
        sleep 0.1
    done
    wait "$pid"
    local exit_code=$?
    printf "\r"
    return $exit_code
}

confirm() {
    local prompt="$1"
    local default="${2:-y}"
    local answer
    if [[ "$default" == "y" ]]; then
        read -rp "$(echo -e "${BOLD}${prompt} [Y/n]:${RESET} ")" answer
        answer="${answer:-y}"
    else
        read -rp "$(echo -e "${BOLD}${prompt} [y/N]:${RESET} ")" answer
        answer="${answer:-n}"
    fi
    local lower
    lower=$(echo "$answer" | tr '[:upper:]' '[:lower:]')
    [[ "$lower" == "y" || "$lower" == "yes" ]]
}

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo ""
        log_error "Installation failed (exit code $exit_code)."
        log_error "Check the log file: ${LOG_FILE}"
    fi
}
trap cleanup EXIT

: > "$LOG_FILE"

# ─────────────────────────── 3. Detection Functions ──────────────────────────
detect_os() {
    if [[ "$(uname)" == "Darwin" ]]; then
        OS_FAMILY="macos"
        return
    fi
    if [[ -f /etc/os-release ]]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        case "$ID" in
            ubuntu|debian|linuxmint|pop) OS_FAMILY="debian" ;;
            centos|rhel|rocky|almalinux|fedora) OS_FAMILY="rhel" ;;
            *) OS_FAMILY="unknown" ;;
        esac
    else
        OS_FAMILY="unknown"
    fi
}

detect_arch() {
    local machine
    machine="$(uname -m)"
    case "$machine" in
        x86_64|amd64)  ARCH="amd64" ;;
        aarch64|arm64) ARCH="arm64" ;;
        *) die "Unsupported architecture: $machine (expected x86_64 or arm64)" ;;
    esac
}

detect_docker() {
    if command -v docker &>/dev/null; then
        if docker info &>/dev/null; then
            return 0
        else
            return 2  # installed but daemon not running
        fi
    fi
    return 1  # not installed
}

detect_docker_compose() {
    if docker compose version &>/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        return 0
    elif command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
        return 0
    fi
    return 1
}

# ─────────────────────────── 4. Pre-flight Checks ───────────────────────────
preflight_checks() {
    log_step "Running pre-flight checks"
    local warnings=0 failures=0

    # Disk space
    local free_gb
    if [[ "$OS_FAMILY" == "macos" ]]; then
        free_gb=$(df -g / | awk 'NR==2 {print $4}')
    else
        free_gb=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
    fi
    if (( free_gb < MIN_DISK_GB )); then
        log_warn "Disk: ${free_gb}GB free (recommended: ${MIN_DISK_GB}GB+)"
        ((warnings++))
    else
        log_success "Disk: ${free_gb}GB free"
    fi

    # RAM
    local total_ram_gb
    if [[ "$OS_FAMILY" == "macos" ]]; then
        local total_bytes
        total_bytes=$(sysctl -n hw.memsize)
        total_ram_gb=$(( total_bytes / 1073741824 ))
    else
        total_ram_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
    fi
    if (( total_ram_gb < MIN_RAM_GB )); then
        log_warn "RAM: ${total_ram_gb}GB (minimum: ${MIN_RAM_GB}GB)"
        ((warnings++))
    elif (( total_ram_gb < LLM_RAM_GB )); then
        log_warn "RAM: ${total_ram_gb}GB — LLM service requires ${LLM_RAM_GB}GB, consider --skip-llm"
        ((warnings++))
    else
        log_success "RAM: ${total_ram_gb}GB"
    fi

    # Port availability
    local port_issues=0
    for i in "${!PORTS[@]}"; do
        local port="${PORTS[$i]}"
        local label="${PORT_LABELS[$i]}"
        if command -v ss &>/dev/null; then
            if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
                log_warn "Port ${port} (${label}) is already in use"
                ((port_issues++))
            fi
        elif command -v lsof &>/dev/null; then
            if lsof -i :"${port}" -sTCP:LISTEN &>/dev/null; then
                log_warn "Port ${port} (${label}) is already in use"
                ((port_issues++))
            fi
        fi
    done
    if (( port_issues == 0 )); then
        log_success "All required ports are available"
    else
        ((warnings += port_issues))
    fi

    # Existing containers
    local existing=()
    for c in "${CONTAINERS[@]}"; do
        if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$c"; then
            existing+=("$c")
        fi
    done
    if (( ${#existing[@]} > 0 )); then
        echo ""
        log_warn "Found existing CyberBridge containers: ${existing[*]}"
        echo ""
        echo -e "  ${BOLD}1)${RESET} Remove and reinstall (fresh deployment)"
        echo -e "  ${BOLD}2)${RESET} Stop, remove, and reinstall"
        echo -e "  ${BOLD}3)${RESET} Abort installation"
        echo ""
        local choice
        read -rp "$(echo -e "${BOLD}Select option [1-3]:${RESET} ")" choice
        case "$choice" in
            1|2)
                log_info "Removing existing containers..."
                for c in "${existing[@]}"; do
                    docker rm -f "$c" >> "$LOG_FILE" 2>&1 || true
                done
                log_success "Existing containers removed"
                ;;
            *)
                die "Installation aborted by user."
                ;;
        esac

        # Existing volumes
        local vol_exists=false
        for vol in postgres_data zap_data; do
            if docker volume inspect "$vol" &>/dev/null; then
                vol_exists=true
                break
            fi
        done
        if $vol_exists; then
            echo ""
            log_warn "Existing data volumes found (postgres_data, zap_data)."
            if confirm "Keep existing volumes and data?" "y"; then
                log_info "Keeping existing volumes."
            else
                log_warn "Removing volumes — this will DELETE your database data!"
                if confirm "Are you sure?" "n"; then
                    docker volume rm postgres_data zap_data >> "$LOG_FILE" 2>&1 || true
                    log_success "Volumes removed."
                else
                    log_info "Keeping existing volumes."
                fi
            fi
        fi
    fi

    # Summary
    echo ""
    if (( failures > 0 )); then
        die "Pre-flight checks failed with ${failures} error(s). Fix them before continuing."
    elif (( warnings > 0 )); then
        log_warn "${warnings} warning(s) detected. Installation may still proceed."
        if ! confirm "Continue anyway?"; then
            die "Installation aborted by user."
        fi
    else
        log_success "All pre-flight checks passed!"
    fi
}

# ─────────────────────────── 5. Docker Installation ─────────────────────────
install_docker() {
    log_step "Docker Installation"

    local docker_status=0
    detect_docker || docker_status=$?

    if [[ $docker_status -eq 0 ]]; then
        log_success "Docker is installed and running"
        detect_docker_compose || log_warn "Docker Compose not found — direct docker run will be used."
        return
    fi

    if [[ $docker_status -eq 2 ]]; then
        log_warn "Docker is installed but the daemon is not running."
        if [[ "$OS_FAMILY" == "macos" ]]; then
            die "Please start Docker Desktop and re-run this script."
        else
            log_info "Attempting to start Docker daemon..."
            sudo systemctl start docker >> "$LOG_FILE" 2>&1 || die "Failed to start Docker daemon."
            sudo systemctl enable docker >> "$LOG_FILE" 2>&1 || true
            log_success "Docker daemon started."
            detect_docker_compose || true
            return
        fi
    fi

    # Docker not installed
    if [[ "$OS_FAMILY" == "macos" ]]; then
        die "Docker is not installed. Please install Docker Desktop from https://docker.com/products/docker-desktop and re-run this script."
    fi

    if ! confirm "Docker is not installed. Install it now?"; then
        die "Docker is required. Install it manually and re-run this script."
    fi

    case "$OS_FAMILY" in
        debian)
            log_info "Installing Docker via official apt repository..."
            (
                sudo apt-get update
                sudo apt-get install -y ca-certificates curl gnupg
                sudo install -m 0755 -d /etc/apt/keyrings
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                sudo chmod a+r /etc/apt/keyrings/docker.gpg
                # shellcheck source=/dev/null
                . /etc/os-release
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" | \
                    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ) >> "$LOG_FILE" 2>&1 || die "Docker installation failed. Check ${LOG_FILE}."
            ;;
        rhel)
            log_info "Installing Docker via official yum/dnf repository..."
            (
                sudo yum install -y yum-utils || sudo dnf install -y dnf-plugins-core
                sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo 2>/dev/null || \
                    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin || \
                    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ) >> "$LOG_FILE" 2>&1 || die "Docker installation failed. Check ${LOG_FILE}."
            ;;
        *)
            die "Unsupported OS for automatic Docker installation. Install Docker manually."
            ;;
    esac

    sudo systemctl start docker >> "$LOG_FILE" 2>&1 || die "Failed to start Docker after installation."
    sudo systemctl enable docker >> "$LOG_FILE" 2>&1 || true

    # Add current user to docker group if not root
    if [[ $EUID -ne 0 ]]; then
        if ! groups | grep -q docker; then
            sudo usermod -aG docker "$USER" 2>> "$LOG_FILE" || true
            log_warn "Added $USER to docker group. You may need to log out and back in."
        fi
    fi

    docker info >> "$LOG_FILE" 2>&1 || die "Docker installation verification failed."
    log_success "Docker installed successfully."
    detect_docker_compose || true
}

# ─────────────────────────── 6. Interactive Configuration ────────────────────
configure_deployment() {
    log_step "Deployment Configuration"

    # Step 1: Deployment scenario
    echo ""
    echo -e "  ${BOLD}Select deployment scenario:${RESET}"
    echo -e "  ${BOLD}1)${RESET} Production with HTTPS + custom domain ${GREEN}(recommended)${RESET}"
    echo -e "  ${BOLD}2)${RESET} On-premise with IP address (HTTP)"
    echo -e "  ${BOLD}3)${RESET} Local development (localhost)"
    echo ""
    local scenario_choice
    read -rp "$(echo -e "${BOLD}Select [1-3]:${RESET} ")" scenario_choice

    case "$scenario_choice" in
        1)
            SCENARIO="domain"
            echo ""
            read -rp "$(echo -e "${BOLD}Enter your API domain (e.g. api.example.com):${RESET} ")" domain
            [[ -z "$domain" ]] && die "Domain cannot be empty."
            API_BASE_URL="https://${domain}"
            VITE_PRODUCTION_IP="https://${domain}"
            ;;
        2)
            SCENARIO="ip"
            echo ""
            # Auto-suggest IP
            local suggested_ip=""
            if command -v hostname &>/dev/null; then
                suggested_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
            fi
            if [[ -n "$suggested_ip" ]]; then
                read -rp "$(echo -e "${BOLD}Enter server IP [${suggested_ip}]:${RESET} ")" server_ip
                server_ip="${server_ip:-$suggested_ip}"
            else
                read -rp "$(echo -e "${BOLD}Enter server IP:${RESET} ")" server_ip
            fi
            [[ -z "$server_ip" ]] && die "IP address cannot be empty."
            API_BASE_URL="http://${server_ip}:5174"
            # VITE_PRODUCTION_IP is used as a base URL — scanner ports are appended to it,
            # so it must NOT include a port. The backend port is set separately.
            VITE_PRODUCTION_IP="http://${server_ip}"
            VITE_BACKEND_PORT="5174"
            ;;
        3)
            SCENARIO="local"
            API_BASE_URL="http://localhost:5174"
            VITE_PRODUCTION_IP="http://localhost"
            VITE_BACKEND_PORT="5174"
            ;;
        *)
            die "Invalid selection."
            ;;
    esac

    # Step 2: Deployment method
    echo ""
    echo -e "  ${BOLD}Select deployment method:${RESET}"
    echo -e "  ${BOLD}1)${RESET} Docker Compose ${GREEN}(recommended)${RESET}"
    echo -e "  ${BOLD}2)${RESET} Direct docker run"
    echo ""
    local method_choice
    read -rp "$(echo -e "${BOLD}Select [1-2]:${RESET} ")" method_choice

    case "$method_choice" in
        1)
            DEPLOY_METHOD="compose"
            if [[ -z "$COMPOSE_CMD" ]]; then
                detect_docker_compose || die "Docker Compose is not available. Use 'Direct docker run' or install docker-compose-plugin."
            fi
            ;;
        2) DEPLOY_METHOD="direct" ;;
        *) die "Invalid selection." ;;
    esac

    # Step 3: Summary
    echo ""
    echo -e "  ${BOLD}─── Configuration Summary ───${RESET}"
    echo -e "  Scenario:       ${CYAN}${SCENARIO}${RESET}"
    echo -e "  Architecture:   ${CYAN}${ARCH}${RESET}"
    echo -e "  Backend URL:    ${CYAN}${API_BASE_URL}${RESET}"
    echo -e "  Frontend Build: ${CYAN}VITE_PRODUCTION_IP=${VITE_PRODUCTION_IP}${RESET}"
    echo -e "  Method:         ${CYAN}${DEPLOY_METHOD}${RESET}"
    echo -e "  Skip LLM:      ${CYAN}${SKIP_LLM}${RESET}"
    echo ""
    if ! confirm "Proceed with this configuration?"; then
        die "Installation aborted by user."
    fi

    # Generate a unique JWT secret for this installation
    JWT_SECRET=$(openssl rand -base64 48 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || head -c 48 /dev/urandom | base64)
    log_success "Generated unique JWT secret for this installation"
}

# ─────────────────────────── 7. Docker Compose Deployment ────────────────────
deploy_compose() {
    log_step "Building and deploying with Docker Compose"

    local generated_file="${SCRIPT_DIR}/docker-compose.generated.yml"

    # Copy original — never modify the version-controlled file
    cp "${SCRIPT_DIR}/docker-compose.yml" "$generated_file"

    # Patch architecture-specific Dockerfiles
    sed -i.bak "s|dockerfile: Dockerfile\.amd64.*# Use Dockerfile\.arm64 for ARM architecture|dockerfile: Dockerfile.${ARCH}|" "$generated_file"
    sed -i.bak "s|dockerfile: Dockerfile\.arm64.*# Use Dockerfile\.amd64 for x86 architecture|dockerfile: Dockerfile.${ARCH}|" "$generated_file"
    # Fallback: direct replacements if comments differ
    sed -i.bak "s|dockerfile: Dockerfile\.amd64|dockerfile: Dockerfile.${ARCH}|g" "$generated_file"
    sed -i.bak "s|dockerfile: Dockerfile\.arm64|dockerfile: Dockerfile.${ARCH}|g" "$generated_file"

    # Patch build args
    sed -i.bak "s|API_BASE_URL_PROD:.*|API_BASE_URL_PROD: ${API_BASE_URL}|" "$generated_file"
    sed -i.bak "s|VITE_PRODUCTION_IP:.*|VITE_PRODUCTION_IP: ${VITE_PRODUCTION_IP}|" "$generated_file"
    sed -i.bak "s|VITE_BACKEND_PORT:.*|VITE_BACKEND_PORT: \"${VITE_BACKEND_PORT}\"|" "$generated_file"

    # Inject generated JWT secret
    sed -i.bak "s|SECRET_KEY: REPLACE_WITH_GENERATED_SECRET|SECRET_KEY: ${JWT_SECRET}|" "$generated_file"

    # Remove sed backup files
    rm -f "${generated_file}.bak"

    if $SKIP_LLM; then
        log_warn "Removing LLM service from generated compose file (--skip-llm)"
        # Remove llm service block and its depends_on references
        python3 -c "
import re, sys
with open('$generated_file', 'r') as f:
    content = f.read()
# Remove llm service block
content = re.sub(r'  # llama\.cpp LLM Service.*?restart: unless-stopped\n', '', content, flags=re.DOTALL)
# Remove llamacpp depends_on references
content = re.sub(r'      llamacpp:\n        condition: service_healthy\n', '', content)
with open('$generated_file', 'w') as f:
    f.write(content)
" 2>> "$LOG_FILE" || log_warn "Could not auto-remove LLM from compose file. You may need to remove it manually."
    fi

    log_info "Building images (this may take several minutes)..."
    log_info "Build output is logged to ${LOG_FILE}"

    # Build
    $COMPOSE_CMD -f "$generated_file" build >> "$LOG_FILE" 2>&1 &
    local build_pid=$!
    spinner $build_pid "Building Docker images..." || die "Docker Compose build failed."
    log_success "All images built successfully."

    # Start services
    log_info "Starting services..."
    $COMPOSE_CMD -f "$generated_file" up -d >> "$LOG_FILE" 2>&1 || die "Docker Compose up failed."
    log_success "Services started."

    wait_for_healthy_compose "$generated_file"
}

wait_for_healthy_compose() {
    local compose_file="$1"
    log_info "Waiting for all services to become healthy (timeout: ${HEALTH_TIMEOUT}s)..."

    local elapsed=0
    local interval=10
    while (( elapsed < HEALTH_TIMEOUT )); do
        local all_healthy=true
        local status_line=""
        for c in "${CONTAINERS[@]}"; do
            if $SKIP_LLM && [[ "$c" == "cyberbridge_llamacpp" ]]; then
                continue
            fi
            local health
            health=$(docker inspect --format='{{.State.Health.Status}}' "$c" 2>/dev/null || echo "missing")
            case "$health" in
                healthy) status_line+="${GREEN}${c}${RESET} " ;;
                *)       status_line+="${YELLOW}${c}(${health})${RESET} "; all_healthy=false ;;
            esac
        done
        printf "\r  %b" "$status_line"

        if $all_healthy; then
            echo ""
            log_success "All services are healthy!"
            return 0
        fi
        sleep "$interval"
        (( elapsed += interval ))
    done

    echo ""
    log_error "Timeout waiting for services to become healthy."
    log_info "Current container status:"
    docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | grep -E "$(IFS='|'; echo "${CONTAINERS[*]}")" || true
    die "Some services did not become healthy within ${HEALTH_TIMEOUT} seconds."
}

# ─────────────────────────── 8. Direct Docker Run Deployment ─────────────────
deploy_direct() {
    log_step "Building and deploying with direct docker run"

    # Create network if it doesn't exist
    if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
        docker network create "$NETWORK_NAME" >> "$LOG_FILE" 2>&1
        log_success "Created network: ${NETWORK_NAME}"
    else
        log_info "Network ${NETWORK_NAME} already exists."
    fi

    # ── Build phase ──
    log_step "Building Docker images"
    log_info "Build output is logged to ${LOG_FILE}"

    build_image "cyberbridge_postgres" "./postgres" "-f Dockerfile.defaults"
    build_image "zap"                "./zapproxy" ""
    build_image "nmap"               "./nmap" ""
    build_image "osv"                "./osvscanner" "-f Dockerfile.${ARCH}"
    build_image "semgrep"            "./semgrep" ""
    build_image "syft"               "./syft" "-f Dockerfile.${ARCH}"
    if ! $SKIP_LLM; then
        log_warn "Building llama.cpp LLM image — this downloads the model and may take 10+ minutes."
        build_image "llamacpp"       "./llamacpp" ""
    else
        log_info "Skipping LLM build (--skip-llm)"
    fi
    build_image "embeddings" "./embeddings" ""
    build_image "cyberbridge_backend"  "./cyberbridge_backend" "" "--build-arg API_BASE_URL_PROD=${API_BASE_URL}"
    build_image "cyberbridge_frontend" "./cyberbridge_frontend" "" "--build-arg VITE_PRODUCTION_IP=${VITE_PRODUCTION_IP} --build-arg VITE_BACKEND_PORT=${VITE_BACKEND_PORT}"

    # CTI Service (build)
    build_image "cti-service" "./cti/service" ""

    # Dark Web services
    docker pull redis:7-alpine >> "$LOG_FILE" 2>&1 &
    local redis_dw_pid=$!
    spinner $redis_dw_pid "Pulling Redis (Dark Web)..." || die "Failed to pull Redis Dark Web image"
    log_success "Pulled Redis (Dark Web)"

    build_image "darkweb-scanner" "./darkweb" ""

    log_success "All images built."

    # ── Run phase ──
    log_step "Starting containers"

    # Tier 1: Database
    run_container "cyberbridge_db" \
        "-d --name cyberbridge_db --network ${NETWORK_NAME} -p 5433:5432 -v postgres_data:/var/lib/postgresql/data -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres --restart unless-stopped cyberbridge_postgres"
    wait_for_container "cyberbridge_db" "pg_isready -U postgres" 60

    # Tier 2: ZAP
    run_container "cyberbridge_zap" \
        "-d --name cyberbridge_zap --network ${NETWORK_NAME} -p 8010:8000 -p 8080:8080 -v zap_data:/root/.ZAP --restart unless-stopped zap"
    wait_for_container "cyberbridge_zap" "python3 -c \"import requests; requests.get('http://127.0.0.1:8080/', timeout=3)\"" 90

    # Tier 3: Scanners + LLM (launched together)
    run_container "cyberbridge_nmap" \
        "-d --name cyberbridge_nmap --network ${NETWORK_NAME} -p 8011:8000 --restart unless-stopped nmap"
    run_container "cyberbridge_osv" \
        "-d --name cyberbridge_osv --network ${NETWORK_NAME} -p 8012:8000 --restart unless-stopped osv"
    run_container "cyberbridge_semgrep" \
        "-d --name cyberbridge_semgrep --network ${NETWORK_NAME} -p 8013:8000 --restart unless-stopped semgrep"
    run_container "cyberbridge_syft" \
        "-d --name cyberbridge_syft --network ${NETWORK_NAME} -p 8014:8000 --restart unless-stopped syft"
    if ! $SKIP_LLM; then
        run_container "cyberbridge_llamacpp" \
            "-d --name cyberbridge_llamacpp --network ${NETWORK_NAME} -p 11435:11435 --memory=10g --memory-swap=10g --restart unless-stopped llamacpp"
    fi

    # Wait for tier 3
    wait_for_container "cyberbridge_nmap" "curl -f http://localhost:8000/ 2>/dev/null" 30
    wait_for_container "cyberbridge_osv" "curl -f http://localhost:8000/ 2>/dev/null" 30
    wait_for_container "cyberbridge_semgrep" "curl -f http://localhost:8000/ 2>/dev/null" 30
    wait_for_container "cyberbridge_syft" "curl -f http://localhost:8000/ 2>/dev/null" 30
    if ! $SKIP_LLM; then
        wait_for_container "cyberbridge_llamacpp" "curl -sf http://localhost:11435/health 2>/dev/null" 120
    fi

    # Embeddings service
    run_container "cyberbridge_embeddings" \
        "-d --name cyberbridge_embeddings --network ${NETWORK_NAME} -p 8016:8000 --memory=1g --restart unless-stopped embeddings"
    wait_for_container "cyberbridge_embeddings" "curl -sf http://localhost:8000/health 2>/dev/null" 60

    # Tier 4: Backend
    run_container "cyberbridge_backend" \
        "-d --name cyberbridge_backend --network ${NETWORK_NAME} -p 5174:8000 -e CONTAINER_ENV=docker -e DB_HOST=cyberbridge_db -e DB_PORT=5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres -e NMAP_SERVICE_URL=http://nmap:8000 -e SEMGREP_SERVICE_URL=http://semgrep:8000 -e OSV_SERVICE_URL=http://osv:8000 -e ZAP_SERVICE_URL=http://zap:8000 -e SYFT_SERVICE_URL=http://syft:8000 -e EMBEDDINGS_SERVICE_URL=http://embeddings:8000 -e SECRET_KEY=${JWT_SECRET} --restart on-failure cyberbridge_backend"
    wait_for_container "cyberbridge_backend" "curl -f http://localhost:8000/docs 2>/dev/null" 60

    # Tier 5: Frontend
    run_container "cyberbridge_frontend" \
        "-d --name cyberbridge_frontend --network ${NETWORK_NAME} -p 5173:5173 --restart unless-stopped cyberbridge_frontend"
    wait_for_container "cyberbridge_frontend" "wget --no-verbose --tries=1 --spider http://localhost:5173 2>/dev/null" 45

    # Tier 6: CTI Service
    run_container "cyberbridge_cti_service" \
        "-d --name cyberbridge_cti_service --network ${NETWORK_NAME} -p 8020:8000 -e DATABASE_URL=postgresql://postgres:postgres@cyberbridge_db:5432/postgres -e NMAP_SERVICE_URL=http://nmap:8000 -e ZAP_SERVICE_URL=http://zap:8000 -e SEMGREP_SERVICE_URL=http://semgrep:8000 -e OSV_SERVICE_URL=http://osv:8000 -e NMAP_TARGETS=127.0.0.1 -e ZAP_TARGETS=http://localhost --restart unless-stopped cti-service"
    wait_for_container "cyberbridge_cti_service" "curl -f http://localhost:8000/api/health 2>/dev/null" 60

    # Tier 7: Dark Web Services
    run_container "cyberbridge_darkweb_redis" \
        "-d --name cyberbridge_darkweb_redis --network ${NETWORK_NAME} -p 6382:6379 -v redis_darkweb_data:/data --restart unless-stopped redis:7-alpine redis-server --appendonly yes"
    wait_for_container "cyberbridge_darkweb_redis" "redis-cli ping" 30

    run_container "cyberbridge_darkweb_scanner" \
        "-d --name cyberbridge_darkweb_scanner --network ${NETWORK_NAME} -p 8030:8001 -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@cyberbridge_db:5432/postgres -e POSTGRES_SERVER=cyberbridge_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres -e REDIS_HOST=darkweb-redis -e REDIS_PORT=6379 -e REDIS_DB=0 -e MAX_SCAN_WORKERS=3 -e SECRET_KEY=change-me-in-production -e ALGORITHM=HS256 -e ACCESS_TOKEN_EXPIRE_MINUTES=15 -e REFRESH_TOKEN_EXPIRE_DAYS=7 -e ENVIRONMENT=production --restart unless-stopped darkweb-scanner"
    wait_for_container "cyberbridge_darkweb_scanner" "curl -f http://localhost:8001/health 2>/dev/null" 60

    log_success "All containers started and healthy."
}

build_image() {
    local name="$1"
    local context="$2"
    local file_flag="$3"
    local extra_args="${4:-}"

    local full_context="${SCRIPT_DIR}/${context#./}"
    local cmd="docker build"
    [[ -n "$file_flag" ]] && cmd+=" $file_flag"
    [[ -n "$extra_args" ]] && cmd+=" $extra_args"
    cmd+=" -t $name $full_context"

    log_info "Building ${name}..."
    eval "$cmd" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    spinner $pid "Building ${name}..." || die "Failed to build image: ${name}"
    log_success "Built ${name}"
}

run_container() {
    local name="$1"
    local run_args="$2"

    # Remove existing container (idempotent)
    docker rm -f "$name" >> "$LOG_FILE" 2>&1 || true

    log_info "Starting ${name}..."
    eval "docker run $run_args" >> "$LOG_FILE" 2>&1 || die "Failed to start container: ${name}"
    log_success "Started ${name}"
}

wait_for_container() {
    local name="$1"
    local health_cmd="$2"
    local timeout="$3"

    local elapsed=0
    local interval=5
    while (( elapsed < timeout )); do
        if docker exec "$name" sh -c "$health_cmd" >> "$LOG_FILE" 2>&1; then
            log_success "${name} is healthy"
            return 0
        fi
        sleep "$interval"
        (( elapsed += interval ))
    done
    log_warn "${name} did not become healthy within ${timeout}s (continuing anyway)"
}

# ─────────────────────────── 9. Health Verification ──────────────────────────
verify_health() {
    log_step "Verifying deployment"

    echo ""
    # Use fixed-width columns with padding (ANSI codes break printf alignment)
    echo -e "  ${BOLD}CONTAINER               STATUS       HEALTH${RESET}"
    echo    "  ─────────────────────  ───────────  ─────────"

    local all_ok=true
    for c in "${CONTAINERS[@]}"; do
        # Pad container name to 24 chars
        local padded
        padded=$(printf '%-24s' "$c")
        if $SKIP_LLM && [[ "$c" == "cyberbridge_llamacpp" ]]; then
            echo -e "  ${padded}${YELLOW}skipped${RESET}      ${YELLOW}n/a${RESET}"
            continue
        fi
        local running health
        running=$(docker inspect --format='{{.State.Running}}' "$c" 2>/dev/null || echo "false")
        health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-check{{end}}' "$c" 2>/dev/null || echo "missing")

        local status_pad health_pad
        status_pad=$(printf '%-13s' "$( [[ "$running" == "true" ]] && echo "running" || echo "stopped" )")
        health_pad="$health"

        if [[ "$running" == "true" ]]; then
            if [[ "$health" == "healthy" ]]; then
                echo -e "  ${padded}${GREEN}${status_pad}${RESET}${GREEN}${health_pad}${RESET}"
            else
                echo -e "  ${padded}${GREEN}${status_pad}${RESET}${YELLOW}${health_pad}${RESET}"
            fi
        else
            echo -e "  ${padded}${RED}${status_pad}${RESET}${RED}${health_pad}${RESET}"
            all_ok=false
        fi
    done
    echo ""

    if $all_ok; then
        log_success "All services are running."
    else
        log_warn "Some services are not running. Check: docker logs <container_name>"
    fi
}

# ─────────────────────────── 10. Persist Configuration ────────────────────────
save_config() {
    local config_file="${SCRIPT_DIR}/.cyberbridge.env"
    cat > "$config_file" <<EOF
# CyberBridge deployment configuration — generated by install.sh
# This file is sourced by update.sh to reuse the same settings.
CYBERBRIDGE_ARCH=${ARCH}
CYBERBRIDGE_SCENARIO=${SCENARIO}
CYBERBRIDGE_API_BASE_URL=${API_BASE_URL}
CYBERBRIDGE_VITE_PRODUCTION_IP=${VITE_PRODUCTION_IP}
CYBERBRIDGE_DEPLOY_METHOD=${DEPLOY_METHOD}
CYBERBRIDGE_SKIP_LLM=${SKIP_LLM}
CYBERBRIDGE_COMPOSE_CMD="${COMPOSE_CMD}"
CYBERBRIDGE_JWT_SECRET=${JWT_SECRET}
EOF
    log_success "Saved deployment config to .cyberbridge.env"
}

# ─────────────────────────── 11. Summary Display ─────────────────────────────
show_summary() {
    local access_ip
    case "$SCENARIO" in
        domain)
            # Extract domain from VITE_PRODUCTION_IP (e.g. https://api.example.com → api.example.com)
            access_ip="${VITE_PRODUCTION_IP#https://}"
            access_ip="${access_ip#http://}"
            ;;
        ip)
            access_ip="${API_BASE_URL#http://}"
            access_ip="${access_ip%:*}"
            ;;
        local)
            access_ip="localhost"
            ;;
    esac

    echo ""
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${RESET}"
    echo -e "${BOLD}${GREEN}  CyberBridge Deployment Complete!${RESET}"
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${RESET}"
    echo ""
    if [[ "$SCENARIO" == "domain" ]]; then
        echo -e "  ${BOLD}Frontend:${RESET}     https://${access_ip}:5173  (or via reverse proxy)"
        echo -e "  ${BOLD}Backend API:${RESET}  ${VITE_PRODUCTION_IP}/docs"
    else
        echo -e "  ${BOLD}Frontend:${RESET}     http://${access_ip}:5173"
        echo -e "  ${BOLD}Backend API:${RESET}  http://${access_ip}:5174/docs"
    fi
    echo -e "  ${BOLD}Database:${RESET}     localhost:5433"
    echo ""
    echo -e "  ${BOLD}Scanners:${RESET}"
    echo -e "    ZAP Proxy:    http://${access_ip}:8010"
    echo -e "    Nmap:         http://${access_ip}:8011"
    echo -e "    OSV Scanner:  http://${access_ip}:8012"
    echo -e "    Semgrep:      http://${access_ip}:8013"
    echo -e "    Syft SBOM:    http://${access_ip}:8014"
    if ! $SKIP_LLM; then
        echo -e "    LLM (llama.cpp): http://${access_ip}:11435"
    else
        echo -e "    LLM (llama.cpp): ${YELLOW}skipped${RESET}"
    fi
    echo ""
    echo -e "  ${BOLD}Architecture:${RESET} ${ARCH}"
    echo -e "  ${BOLD}Method:${RESET}       ${DEPLOY_METHOD}"
    echo -e "  ${BOLD}Log file:${RESET}     ${LOG_FILE}"
    echo ""
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${RESET}"

    if [[ "$DEPLOY_METHOD" == "compose" ]]; then
        echo ""
        echo -e "  ${BOLD}Manage with:${RESET}"
        echo -e "    Stop:    ${CYAN}${COMPOSE_CMD} -f docker-compose.generated.yml down${RESET}"
        echo -e "    Start:   ${CYAN}${COMPOSE_CMD} -f docker-compose.generated.yml up -d${RESET}"
        echo -e "    Logs:    ${CYAN}${COMPOSE_CMD} -f docker-compose.generated.yml logs -f [service]${RESET}"
        echo -e "    Rebuild: ${CYAN}${COMPOSE_CMD} -f docker-compose.generated.yml up -d --build${RESET}"
    else
        echo ""
        echo -e "  ${BOLD}Manage with:${RESET}"
        echo -e "    Stop all:  ${CYAN}docker stop ${CONTAINERS[*]}${RESET}"
        echo -e "    Start all: ${CYAN}docker start ${CONTAINERS[*]}${RESET}"
        echo -e "    Logs:      ${CYAN}docker logs -f <container_name>${RESET}"
    fi
    echo ""
}

# ─────────────────────────── 12. Main Entry Point ────────────────────────────
main() {
    # Parse arguments
    for arg in "$@"; do
        case "$arg" in
            --skip-llm) SKIP_LLM=true ;;
            --help|-h)
                echo "Usage: ./install.sh [--skip-llm]"
                echo ""
                echo "Options:"
                echo "  --skip-llm   Skip building and running the LLM service (llama.cpp)"
                echo "  --help       Show this help message"
                exit 0
                ;;
            *) die "Unknown argument: $arg. Use --help for usage." ;;
        esac
    done

    # Banner
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "   ____      _               ____       _     _            "
    echo "  / ___|   _| |__   ___ _ __| __ ) _ __(_) __| | __ _  ___ "
    echo " | |  | | | | '_ \\ / _ \\ '__|  _ \\| '__| |/ _\` |/ _\` |/ _ \\"
    echo " | |__| |_| | |_) |  __/ |  | |_) | |  | | (_| | (_| |  __/"
    echo "  \\____\\__, |_.__/ \\___|_|  |____/|_|  |_|\\__,_|\\__, |\\___|"
    echo "       |___/                                     |___/      "
    echo -e "${RESET}"
    echo -e "  ${BOLD}One-Command Installation Script${RESET}"
    echo ""

    # Verify running from project root
    if [[ ! -f "${SCRIPT_DIR}/docker-compose.yml" ]]; then
        die "docker-compose.yml not found. Run this script from the CyberBridge project root."
    fi

    # Detection
    log_step "Detecting environment"
    detect_os
    log_success "OS: ${OS_FAMILY}"
    detect_arch
    log_success "Architecture: ${ARCH}"

    # Install Docker if needed
    install_docker

    # Pre-flight checks
    preflight_checks

    # Interactive configuration
    configure_deployment

    # Deploy
    if [[ "$DEPLOY_METHOD" == "compose" ]]; then
        deploy_compose
    else
        deploy_direct
    fi

    # Verify
    verify_health

    # Persist config for update.sh
    save_config

    # Summary
    show_summary
}

main "$@"
