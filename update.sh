#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# CyberBridge — Selective Update Script
# Detects what changed since the last install/update and rebuilds only the
# affected services.  Reuses configuration saved by install.sh.
# Usage: ./update.sh [--pull] [--force-all] [--dry-run] [--help]
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
LOG_FILE="/tmp/cyberbridge_update.log"
CONFIG_FILE="${SCRIPT_DIR}/.cyberbridge.env"
MARKER_FILE="${SCRIPT_DIR}/.cyberbridge.last_update_head"

NETWORK_NAME="cyberbridge-network"
CONTAINERS=(cyberbridge_db cyberbridge_zap cyberbridge_nmap cyberbridge_osv cyberbridge_semgrep cyberbridge_syft cyberbridge_llamacpp cyberbridge_cti_service cyberbridge_darkweb_redis cyberbridge_darkweb_scanner cyberbridge_backend cyberbridge_frontend)
HEALTH_TIMEOUT=300

# Flags
FLAG_PULL=false
FLAG_FORCE_ALL=false
FLAG_DRY_RUN=false

# Loaded from config
ARCH=""
SCENARIO=""
API_BASE_URL=""
VITE_PRODUCTION_IP=""
DEPLOY_METHOD=""
SKIP_LLM=false
COMPOSE_CMD=""
JWT_SECRET=""

# ─────────────────────────── 2. Utility Functions ────────────────────────────
log_info()    { echo -e "${BLUE}[INFO]${RESET}    $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET}   $*"; }
log_step()    { echo -e "\n${BOLD}${CYAN}>>> $*${RESET}"; }

die() {
    log_error "$*"
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
    [[ "${answer,,}" == "y" || "${answer,,}" == "yes" ]]
}

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo ""
        log_error "Update failed (exit code $exit_code)."
        log_error "Check the log file: ${LOG_FILE}"
    fi
}
trap cleanup EXIT

: > "$LOG_FILE"

# ─────────────────────────── 3. Load Configuration ───────────────────────────
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        die "Configuration file not found: ${CONFIG_FILE}
Run ./install.sh first to create it, or re-run install.sh if upgrading from an older version."
    fi

    # shellcheck source=/dev/null
    . "$CONFIG_FILE"

    ARCH="${CYBERBRIDGE_ARCH:?Missing CYBERBRIDGE_ARCH in config}"
    SCENARIO="${CYBERBRIDGE_SCENARIO:?Missing CYBERBRIDGE_SCENARIO in config}"
    API_BASE_URL="${CYBERBRIDGE_API_BASE_URL:?Missing CYBERBRIDGE_API_BASE_URL in config}"
    VITE_PRODUCTION_IP="${CYBERBRIDGE_VITE_PRODUCTION_IP:?Missing CYBERBRIDGE_VITE_PRODUCTION_IP in config}"
    DEPLOY_METHOD="${CYBERBRIDGE_DEPLOY_METHOD:?Missing CYBERBRIDGE_DEPLOY_METHOD in config}"
    SKIP_LLM="${CYBERBRIDGE_SKIP_LLM:-false}"
    COMPOSE_CMD="${CYBERBRIDGE_COMPOSE_CMD:-docker compose}"
    JWT_SECRET="${CYBERBRIDGE_JWT_SECRET:-}"

    if [[ -z "$JWT_SECRET" ]]; then
        log_warn "No JWT secret found in config (older installation). Generating a new one..."
        JWT_SECRET=$(openssl rand -base64 48 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || head -c 48 /dev/urandom | base64)
        # Persist it back to config
        echo "CYBERBRIDGE_JWT_SECRET=${JWT_SECRET}" >> "$CONFIG_FILE"
        log_success "Generated and saved new JWT secret."
    fi

    log_success "Loaded config: arch=${ARCH}  method=${DEPLOY_METHOD}  scenario=${SCENARIO}"
}

# ─────────────────────────── 4. Git Pull ─────────────────────────────────────
do_git_pull() {
    log_step "Pulling latest changes"
    PREV_HEAD="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"
    git -C "$SCRIPT_DIR" pull >> "$LOG_FILE" 2>&1 || die "git pull failed. Resolve conflicts and retry."
    CURR_HEAD="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"

    if [[ "$PREV_HEAD" == "$CURR_HEAD" ]]; then
        log_info "Already up to date."
    else
        local count
        count=$(git -C "$SCRIPT_DIR" rev-list --count "${PREV_HEAD}..${CURR_HEAD}")
        log_success "Pulled ${count} new commit(s)."
    fi
}

# ─────────────────────────── 5. Change Detection ────────────────────────────
detect_changes() {
    log_step "Detecting changes"

    local diff_range=""

    # Priority 1: If --pull was used, diff the pull range
    if $FLAG_PULL && [[ -n "${PREV_HEAD:-}" ]] && [[ -n "${CURR_HEAD:-}" ]] && [[ "$PREV_HEAD" != "$CURR_HEAD" ]]; then
        diff_range="${PREV_HEAD}..${CURR_HEAD}"
        log_info "Diffing pull range: ${diff_range}"

    # Priority 2: Use saved marker from last update
    elif [[ -f "$MARKER_FILE" ]]; then
        local saved_head
        saved_head="$(cat "$MARKER_FILE")"
        local current_head
        current_head="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"
        if [[ "$saved_head" == "$current_head" ]]; then
            log_info "No new commits since last update."
            if ! $FLAG_FORCE_ALL; then
                log_success "Nothing to update."
                save_marker
                exit 0
            fi
        fi
        diff_range="${saved_head}..HEAD"
        log_info "Diffing from last update marker: ${diff_range}"

    # Priority 3: Fallback to last commit
    else
        diff_range="HEAD~1..HEAD"
        log_info "No marker found, diffing last commit: ${diff_range}"
    fi

    # Get changed files
    CHANGED_FILES=()
    if [[ -n "$diff_range" ]]; then
        while IFS= read -r file; do
            [[ -n "$file" ]] && CHANGED_FILES+=("$file")
        done < <(git -C "$SCRIPT_DIR" diff --name-only "$diff_range" 2>/dev/null || true)
    fi

    if (( ${#CHANGED_FILES[@]} == 0 )) && ! $FLAG_FORCE_ALL; then
        log_info "No file changes detected."
        log_success "Nothing to update."
        save_marker
        exit 0
    fi

    log_info "Changed files: ${#CHANGED_FILES[@]}"
}

# ─────────────────────────── 6. Map Changes to Services ──────────────────────
map_services() {
    log_step "Mapping changes to services"

    # Directory → service name mapping
    declare -A DIR_SERVICE_MAP=(
        ["postgres/"]="cyberbridge_db"
        ["zapproxy/"]="zap"
        ["nmap/"]="nmap"
        ["osvscanner/"]="osv"
        ["semgrep/"]="semgrep"
        ["syft/"]="syft"
        ["llamacpp/"]="llamacpp"
        ["cyberbridge_backend/"]="cyberbridge_backend"
        ["cyberbridge_frontend/"]="cyberbridge_frontend"
        ["cti/service/"]="cti-service"
        ["darkweb/"]="darkweb-scanner"
    )

    SERVICES_TO_REBUILD=()
    local compose_changed=false

    if $FLAG_FORCE_ALL; then
        for svc in "${CONTAINERS[@]}"; do
            if $SKIP_LLM && [[ "$svc" == "cyberbridge_llamacpp" ]]; then
                continue
            fi
            SERVICES_TO_REBUILD+=("$svc")
        done
        log_info "Force-all: rebuilding all services."
        return
    fi

    # Deduplicate using associative array
    declare -A seen_services

    for file in "${CHANGED_FILES[@]}"; do
        local matched=false

        for dir in "${!DIR_SERVICE_MAP[@]}"; do
            if [[ "$file" == "${dir}"* ]]; then
                local svc="${DIR_SERVICE_MAP[$dir]}"
                if $SKIP_LLM && [[ "$svc" == "llamacpp" ]]; then
                    continue
                fi
                if [[ -z "${seen_services[$svc]:-}" ]]; then
                    seen_services["$svc"]=1
                    SERVICES_TO_REBUILD+=("$svc")
                fi
                matched=true
                break
            fi
        done

        if ! $matched; then
            # Check for docker-compose.yml changes
            if [[ "$file" == "docker-compose.yml" ]]; then
                compose_changed=true
            fi
            # Root-level files (install.sh, *.md, .gitignore, etc.) — no rebuild
        fi
    done

    if $compose_changed; then
        echo ""
        log_warn "docker-compose.yml has changed."
        log_warn "Consider running with --force-all to rebuild everything, or"
        log_warn "re-run ./install.sh if the compose structure changed significantly."
        echo ""
    fi

    if (( ${#SERVICES_TO_REBUILD[@]} == 0 )); then
        log_info "No service directories were affected by the changes."
        log_success "Nothing to rebuild."
        save_marker
        exit 0
    fi

    # Display what will be rebuilt
    echo ""
    echo -e "  ${BOLD}Services to rebuild:${RESET}"
    for svc in "${SERVICES_TO_REBUILD[@]}"; do
        echo -e "    ${CYAN}${svc}${RESET}"
    done
    echo ""

    # Show changed files per service
    for svc in "${SERVICES_TO_REBUILD[@]}"; do
        local dir_prefix=""
        for dir in "${!DIR_SERVICE_MAP[@]}"; do
            if [[ "${DIR_SERVICE_MAP[$dir]}" == "$svc" ]]; then
                dir_prefix="$dir"
                break
            fi
        done
        local count=0
        for file in "${CHANGED_FILES[@]}"; do
            if [[ "$file" == "${dir_prefix}"* ]]; then
                ((count++)) || true
            fi
        done
        echo -e "    ${svc}: ${count} file(s) changed in ${dir_prefix}"
    done
    echo ""
}

# ─────────────────────────── 7. Rebuild (Compose Mode) ───────────────────────
rebuild_compose() {
    local generated_file="${SCRIPT_DIR}/docker-compose.generated.yml"

    # Regenerate compose file if docker-compose.yml is in the changed files
    local needs_regen=false
    for file in "${CHANGED_FILES[@]}"; do
        if [[ "$file" == "docker-compose.yml" ]]; then
            needs_regen=true
            break
        fi
    done

    if $needs_regen || [[ ! -f "$generated_file" ]]; then
        log_info "Regenerating docker-compose.generated.yml..."
        cp "${SCRIPT_DIR}/docker-compose.yml" "$generated_file"

        # Same sed patches as install.sh
        sed -i.bak "s|dockerfile: Dockerfile\.amd64.*# Use Dockerfile\.arm64 for ARM architecture|dockerfile: Dockerfile.${ARCH}|" "$generated_file"
        sed -i.bak "s|dockerfile: Dockerfile\.arm64.*# Use Dockerfile\.amd64 for x86 architecture|dockerfile: Dockerfile.${ARCH}|" "$generated_file"
        sed -i.bak "s|dockerfile: Dockerfile\.amd64|dockerfile: Dockerfile.${ARCH}|g" "$generated_file"
        sed -i.bak "s|dockerfile: Dockerfile\.arm64|dockerfile: Dockerfile.${ARCH}|g" "$generated_file"
        sed -i.bak "s|API_BASE_URL_PROD:.*|API_BASE_URL_PROD: ${API_BASE_URL}|" "$generated_file"
        sed -i.bak "s|VITE_PRODUCTION_IP:.*|VITE_PRODUCTION_IP: ${VITE_PRODUCTION_IP}|" "$generated_file"
        sed -i.bak "s|SECRET_KEY: REPLACE_WITH_GENERATED_SECRET|SECRET_KEY: ${JWT_SECRET}|" "$generated_file"
        rm -f "${generated_file}.bak"

        if $SKIP_LLM; then
            python3 -c "
import re, sys
with open('$generated_file', 'r') as f:
    content = f.read()
content = re.sub(r'  # llama\.cpp LLM Service.*?restart: unless-stopped\n', '', content, flags=re.DOTALL)
content = re.sub(r'      llamacpp:\n        condition: service_healthy\n', '', content)
with open('$generated_file', 'w') as f:
    f.write(content)
" 2>> "$LOG_FILE" || log_warn "Could not auto-remove LLM from compose file."
        fi

        log_success "Regenerated compose file."
    fi

    # Build and restart only the affected services
    local service_list="${SERVICES_TO_REBUILD[*]}"
    log_info "Rebuilding: ${service_list}"
    log_info "Build output is logged to ${LOG_FILE}"

    # Step 1: Pre-build images while old containers keep running (no downtime)
    # shellcheck disable=SC2086
    $COMPOSE_CMD -f "$generated_file" build ${service_list} >> "$LOG_FILE" 2>&1 &
    local build_pid=$!
    spinner $build_pid "Building images..." || die "Docker Compose build failed."
    log_success "Images built."

    # Step 2: Swap to new containers (only seconds of downtime)
    # shellcheck disable=SC2086
    $COMPOSE_CMD -f "$generated_file" up -d ${service_list} >> "$LOG_FILE" 2>&1 &
    local restart_pid=$!
    spinner $restart_pid "Restarting services..." || die "Docker Compose restart failed."
    log_success "Services restarted with new images."
}

# ─────────────────────────── 8. Rebuild (Direct Mode) ────────────────────────

# Build order for direct mode (tier-based)
declare -A SERVICE_TIER=(
    ["cyberbridge_db"]=1
    ["zap"]=2
    ["nmap"]=3
    ["osv"]=3
    ["semgrep"]=3
    ["syft"]=3
    ["llamacpp"]=3
    ["cti-service"]=3
    ["darkweb-redis"]=3
    ["darkweb-scanner"]=4
    ["cyberbridge_backend"]=5
    ["cyberbridge_frontend"]=6
)

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

rebuild_direct_service() {
    local svc="$1"

    case "$svc" in
        cyberbridge_db)
            build_image "cyberbridge_postgres" "./postgres" "-f Dockerfile.defaults"
            run_container "cyberbridge_db" \
                "-d --name cyberbridge_db --network ${NETWORK_NAME} -p 5433:5432 -v postgres_data:/var/lib/postgresql/data -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres --restart unless-stopped cyberbridge_postgres"
            wait_for_container "cyberbridge_db" "pg_isready -U postgres" 60
            ;;
        zap)
            build_image "zap" "./zapproxy" ""
            run_container "cyberbridge_zap" \
                "-d --name cyberbridge_zap --network ${NETWORK_NAME} -p 8010:8000 -p 8080:8080 -v zap_data:/root/.ZAP --restart unless-stopped zap"
            wait_for_container "cyberbridge_zap" "python3 -c \"import requests; requests.get('http://127.0.0.1:8080/', timeout=3)\"" 90
            ;;
        nmap)
            build_image "nmap" "./nmap" ""
            run_container "cyberbridge_nmap" \
                "-d --name cyberbridge_nmap --network ${NETWORK_NAME} -p 8011:8000 --restart unless-stopped nmap"
            wait_for_container "cyberbridge_nmap" "curl -f http://localhost:8000/ 2>/dev/null" 30
            ;;
        osv)
            build_image "osv" "./osvscanner" "-f Dockerfile.${ARCH}"
            run_container "cyberbridge_osv" \
                "-d --name cyberbridge_osv --network ${NETWORK_NAME} -p 8012:8000 --restart unless-stopped osv"
            wait_for_container "cyberbridge_osv" "curl -f http://localhost:8000/ 2>/dev/null" 30
            ;;
        semgrep)
            build_image "semgrep" "./semgrep" ""
            run_container "cyberbridge_semgrep" \
                "-d --name cyberbridge_semgrep --network ${NETWORK_NAME} -p 8013:8000 --restart unless-stopped semgrep"
            wait_for_container "cyberbridge_semgrep" "curl -f http://localhost:8000/ 2>/dev/null" 30
            ;;
        syft)
            build_image "syft" "./syft" "-f Dockerfile.${ARCH}"
            run_container "cyberbridge_syft" \
                "-d --name cyberbridge_syft --network ${NETWORK_NAME} -p 8014:8000 --restart unless-stopped syft"
            wait_for_container "cyberbridge_syft" "curl -f http://localhost:8000/ 2>/dev/null" 30
            ;;
        llamacpp)
            build_image "llamacpp" "./llamacpp" ""
            run_container "cyberbridge_llamacpp" \
                "-d --name cyberbridge_llamacpp --network ${NETWORK_NAME} -p 11435:11435 --memory=10g --memory-swap=10g --restart unless-stopped llamacpp"
            wait_for_container "cyberbridge_llamacpp" "curl -sf http://localhost:11435/health 2>/dev/null" 120
            ;;
        cyberbridge_backend)
            build_image "cyberbridge_backend" "./cyberbridge_backend" "" "--build-arg API_BASE_URL_PROD=${API_BASE_URL}"
            run_container "cyberbridge_backend" \
                "-d --name cyberbridge_backend --network ${NETWORK_NAME} -p 5174:8000 -e CONTAINER_ENV=docker -e DB_HOST=cyberbridge_db -e DB_PORT=5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres -e NMAP_SERVICE_URL=http://nmap:8000 -e SEMGREP_SERVICE_URL=http://semgrep:8000 -e OSV_SERVICE_URL=http://osv:8000 -e ZAP_SERVICE_URL=http://zap:8000 -e SYFT_SERVICE_URL=http://syft:8000 -e SECRET_KEY=${JWT_SECRET} --restart on-failure cyberbridge_backend"
            wait_for_container "cyberbridge_backend" "curl -f http://localhost:8000/docs 2>/dev/null" 60
            ;;
        cyberbridge_frontend)
            build_image "cyberbridge_frontend" "./cyberbridge_frontend" "" "--build-arg VITE_PRODUCTION_IP=${VITE_PRODUCTION_IP}"
            run_container "cyberbridge_frontend" \
                "-d --name cyberbridge_frontend --network ${NETWORK_NAME} -p 5173:5173 --restart unless-stopped cyberbridge_frontend"
            wait_for_container "cyberbridge_frontend" "wget --no-verbose --tries=1 --spider http://localhost:5173 2>/dev/null" 45
            ;;

        # ── CTI Service (build-based) ──
        cti-service)
            build_image "cti-service" "./cti/service" ""
            run_container "cyberbridge_cti_service" \
                "-d --name cyberbridge_cti_service --network ${NETWORK_NAME} -p 8020:8000 -e DATABASE_URL=postgresql://postgres:postgres@cyberbridge_db:5432/postgres -e NMAP_SERVICE_URL=http://nmap:8000 -e ZAP_SERVICE_URL=http://zap:8000 -e SEMGREP_SERVICE_URL=http://semgrep:8000 -e OSV_SERVICE_URL=http://osv:8000 -e NMAP_TARGETS=${NMAP_TARGETS:-127.0.0.1} -e ZAP_TARGETS=${ZAP_TARGETS:-http://localhost} --restart unless-stopped cti-service"
            wait_for_container "cyberbridge_cti_service" "curl -f http://localhost:8000/api/health 2>/dev/null" 60
            ;;

        # ── Dark Web Scanner Stack ──
        darkweb-redis)
            docker pull redis:7-alpine >> "$LOG_FILE" 2>&1 &
            spinner $! "Pulling Redis (Dark Web) image..." || die "Failed to pull Redis image"
            docker rm -f cyberbridge_darkweb_redis >> "$LOG_FILE" 2>&1 || true
            run_container "cyberbridge_darkweb_redis" \
                "-d --name cyberbridge_darkweb_redis --network ${NETWORK_NAME} -p 6382:6379 -v redis_darkweb_data:/data --restart unless-stopped redis:7-alpine redis-server --appendonly yes"
            wait_for_container "cyberbridge_darkweb_redis" "redis-cli ping" 30
            ;;
        darkweb-scanner)
            build_image "darkweb-scanner" "./darkweb" ""
            run_container "cyberbridge_darkweb_scanner" \
                "-d --name cyberbridge_darkweb_scanner --network ${NETWORK_NAME} -p 8030:8001 -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@cyberbridge_db:5432/postgres -e POSTGRES_SERVER=cyberbridge_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres -e REDIS_HOST=redis-darkweb -e REDIS_PORT=6379 -e REDIS_DB=0 -e MAX_SCAN_WORKERS=3 -e SECRET_KEY=${DARKWEB_SECRET_KEY:-change-me-in-production} -e ALGORITHM=HS256 -e ACCESS_TOKEN_EXPIRE_MINUTES=15 -e REFRESH_TOKEN_EXPIRE_DAYS=7 -e ENVIRONMENT=production --restart unless-stopped darkweb-scanner"
            wait_for_container "cyberbridge_darkweb_scanner" "curl -f http://localhost:8001/health 2>/dev/null" 60
            ;;
    esac
}

rebuild_direct() {
    log_info "Build output is logged to ${LOG_FILE}"

    # Sort services by tier order
    local sorted=()
    for tier in 1 2 3 4 5 6; do
        for svc in "${SERVICES_TO_REBUILD[@]}"; do
            if [[ "${SERVICE_TIER[$svc]:-0}" -eq "$tier" ]]; then
                sorted+=("$svc")
            fi
        done
    done

    for svc in "${sorted[@]}"; do
        log_step "Rebuilding ${svc}"
        rebuild_direct_service "$svc"
    done

    log_success "All affected services rebuilt."
}

# ─────────────────────────── 9. Health Verification ──────────────────────────
verify_health() {
    log_step "Verifying deployment"

    echo ""
    echo -e "  ${BOLD}CONTAINER               STATUS       HEALTH${RESET}"
    echo    "  ─────────────────────  ───────────  ─────────"

    local all_ok=true
    for c in "${CONTAINERS[@]}"; do
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

# ─────────────────────────── 10. Update Marker ───────────────────────────────
save_marker() {
    git -C "$SCRIPT_DIR" rev-parse HEAD > "$MARKER_FILE" 2>/dev/null || true
}

# ─────────────────────────── 11. Summary ─────────────────────────────────────
show_summary() {
    echo ""
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${RESET}"
    echo -e "${BOLD}${GREEN}  CyberBridge Update Complete!${RESET}"
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${RESET}"
    echo ""
    echo -e "  ${BOLD}Services rebuilt:${RESET}"
    for svc in "${SERVICES_TO_REBUILD[@]}"; do
        echo -e "    ${GREEN}${svc}${RESET}"
    done
    echo ""
    echo -e "  ${BOLD}Architecture:${RESET} ${ARCH}"
    echo -e "  ${BOLD}Method:${RESET}       ${DEPLOY_METHOD}"
    echo -e "  ${BOLD}Log file:${RESET}     ${LOG_FILE}"
    echo ""
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${RESET}"
    echo ""
}

# ─────────────────────────── 12. Main Entry Point ────────────────────────────
main() {
    # Parse arguments
    for arg in "$@"; do
        case "$arg" in
            --pull)      FLAG_PULL=true ;;
            --force-all) FLAG_FORCE_ALL=true ;;
            --dry-run)   FLAG_DRY_RUN=true ;;
            --help|-h)
                echo "Usage: ./update.sh [--pull] [--force-all] [--dry-run] [--help]"
                echo ""
                echo "Options:"
                echo "  --pull       Run 'git pull' before detecting changes"
                echo "  --force-all  Rebuild all services regardless of changes"
                echo "  --dry-run    Show what would be rebuilt without doing it"
                echo "  --help       Show this help message"
                echo ""
                echo "Examples:"
                echo "  ./update.sh --pull            # Pull + rebuild changed services"
                echo "  ./update.sh --force-all       # Rebuild everything"
                echo "  ./update.sh --pull --dry-run   # Pull and preview what would change"
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
    echo -e "  ${BOLD}Selective Update Script${RESET}"
    echo ""

    # Verify running from project root
    if [[ ! -f "${SCRIPT_DIR}/docker-compose.yml" ]]; then
        die "docker-compose.yml not found. Run this script from the CyberBridge project root."
    fi

    # Load config
    load_config

    # Optional git pull
    if $FLAG_PULL; then
        do_git_pull
    fi

    # Detect changes
    detect_changes

    # Map to services
    map_services

    # Dry-run exits here
    if $FLAG_DRY_RUN; then
        echo ""
        log_info "Dry run — no changes were made."
        exit 0
    fi

    # Confirm
    if ! confirm "Proceed with rebuild?"; then
        die "Update aborted by user."
    fi

    # Rebuild
    log_step "Rebuilding affected services"
    if [[ "$DEPLOY_METHOD" == "compose" ]]; then
        rebuild_compose
    else
        rebuild_direct
    fi

    # Verify
    verify_health

    # Save marker
    save_marker

    # Summary
    show_summary
}

main "$@"
