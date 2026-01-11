#!/bin/bash
# ============================================================
# Zoocari Rollback Script
# ============================================================
# Quickly switch from new architecture back to legacy Streamlit app
#
# Usage:
#   ./scripts/rollback.sh [--skip-health-check]
#
# This script will:
#   1. Stop new containers (if running)
#   2. Start legacy Streamlit app
#   3. Verify health (Streamlit /_stcore/health endpoint)
#   4. Provide rollback confirmation
#
# Expected time: <5 minutes
# ============================================================

set -e  # Exit on error

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LEGACY_DIR="$PROJECT_ROOT/legacy"
HEALTH_ENDPOINT="http://localhost:8501/_stcore/health"
MAX_HEALTH_CHECKS=30  # 30 attempts * 5 seconds = 2.5 minutes max wait
SKIP_HEALTH_CHECK=false

# Parse arguments
if [[ "$1" == "--skip-health-check" ]]; then
    SKIP_HEALTH_CHECK=true
fi

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "============================================================"
echo "  Zoocari Rollback to Legacy Streamlit Application"
echo "============================================================"
echo ""

# Step 1: Stop new containers
log_info "Step 1/4: Stopping new architecture containers (if running)..."

# Check for docker compose in docker/ directory
if [ -f "$PROJECT_ROOT/docker/docker-compose.yml" ]; then
    log_info "Found new docker-compose.yml, stopping containers..."
    cd "$PROJECT_ROOT/docker"
    docker compose down || log_warning "No new containers to stop (or already stopped)"
else
    log_warning "No new docker-compose.yml found at docker/docker-compose.yml"
fi

# Also check for containers with common new architecture names
log_info "Stopping any FastAPI/Next.js containers..."
docker stop zoocari-api zoocari-web zoocari-nginx 2>/dev/null || log_info "No new containers found"

cd "$PROJECT_ROOT"

# Step 2: Verify legacy directory exists
log_info "Step 2/4: Verifying legacy application files..."

if [ ! -d "$LEGACY_DIR" ]; then
    log_error "Legacy directory not found at: $LEGACY_DIR"
    log_error "Cannot proceed with rollback. Please ensure legacy files are preserved."
    exit 1
fi

if [ ! -f "$LEGACY_DIR/docker-compose.yml" ]; then
    log_error "Legacy docker-compose.yml not found at: $LEGACY_DIR/docker-compose.yml"
    exit 1
fi

log_success "Legacy application files verified"

# Step 3: Start legacy containers
log_info "Step 3/4: Starting legacy Streamlit application..."

cd "$LEGACY_DIR"

# Check if .env exists in project root, copy reference if needed
if [ -f "$PROJECT_ROOT/.env" ]; then
    log_info "Using .env from project root"
else
    log_warning "No .env file found. Make sure OPENAI_API_KEY is set."
fi

# Start legacy container
log_info "Building and starting legacy container (this may take a few minutes)..."
docker compose up -d --build

if [ $? -ne 0 ]; then
    log_error "Failed to start legacy containers"
    exit 1
fi

log_success "Legacy container started"

# Step 4: Health check
if [ "$SKIP_HEALTH_CHECK" = false ]; then
    log_info "Step 4/4: Performing health check on Streamlit app..."

    echo -n "Waiting for Streamlit to be ready"
    HEALTH_CHECK_COUNT=0

    while [ $HEALTH_CHECK_COUNT -lt $MAX_HEALTH_CHECKS ]; do
        if curl -sf "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
            echo ""
            log_success "Health check passed! Streamlit is responding."
            break
        fi

        echo -n "."
        sleep 5
        HEALTH_CHECK_COUNT=$((HEALTH_CHECK_COUNT + 1))
    done

    if [ $HEALTH_CHECK_COUNT -eq $MAX_HEALTH_CHECKS ]; then
        echo ""
        log_error "Health check failed after $((MAX_HEALTH_CHECKS * 5)) seconds"
        log_error "Container may still be starting. Check logs with:"
        log_error "  docker logs zoocari-legacy"
        exit 1
    fi
else
    log_info "Step 4/4: Skipping health check (--skip-health-check flag set)"
fi

# Final summary
echo ""
echo "============================================================"
log_success "Rollback Complete!"
echo "============================================================"
echo ""
echo "Legacy Streamlit app is now running at:"
echo "  ${GREEN}http://localhost:8501${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:        docker logs -f zoocari-legacy"
echo "  Stop app:         cd legacy && docker compose down"
echo "  Restart app:      cd legacy && docker compose restart"
echo "  View containers:  docker ps | grep zoocari"
echo ""
echo "To migrate back to new architecture, stop legacy and restart new containers."
echo "============================================================"
