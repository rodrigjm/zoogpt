#!/bin/bash
# ============================================================
# Zoocari Production Deployment Script
# ============================================================
# Safely deploys new version with automatic rollback on failure
#
# Usage:
#   ./scripts/deploy.sh [--skip-backup] [--no-rollback] [--profile PROFILE]
#
# This script will:
#   1. Backup current data
#   2. Build production images
#   3. Stop old containers gracefully
#   4. Start new containers
#   5. Wait for health check (with timeout)
#   6. Rollback on failure (unless --no-rollback)
#
# Expected time: 5-10 minutes
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
DOCKER_DIR="$PROJECT_ROOT/docker"
COMPOSE_FILE="$DOCKER_DIR/docker-compose.prod.yml"
HEALTH_ENDPOINT="http://localhost:8000/health"
MAX_HEALTH_CHECKS=20  # 20 attempts * 10 seconds = 3.3 minutes max wait
SKIP_BACKUP=false
NO_ROLLBACK=false
COMPOSE_PROFILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --no-rollback)
            NO_ROLLBACK=true
            shift
            ;;
        --profile)
            COMPOSE_PROFILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-backup] [--no-rollback] [--profile PROFILE]"
            exit 1
            ;;
    esac
done

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

# Rollback function
perform_rollback() {
    log_error "Deployment failed! Starting automatic rollback..."

    # Stop new containers
    log_info "Stopping new containers..."
    cd "$DOCKER_DIR"
    docker compose -f docker-compose.prod.yml down || true

    # Run rollback script if available
    if [ -f "$SCRIPT_DIR/rollback.sh" ]; then
        log_info "Running rollback script..."
        bash "$SCRIPT_DIR/rollback.sh"
    else
        log_error "Rollback script not found. Manual intervention required."
    fi

    exit 1
}

# Banner
echo "============================================================"
echo "  Zoocari Production Deployment"
echo "============================================================"
echo ""

# Pre-flight checks
log_info "Pre-flight: Verifying environment..."

# Check Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Check .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_error ".env file not found at: $PROJECT_ROOT/.env"
    log_error "Please create .env with required variables (OPENAI_API_KEY, etc.)"
    exit 1
fi

# Check required environment variables
source "$PROJECT_ROOT/.env"
if [ -z "$OPENAI_API_KEY" ]; then
    log_error "OPENAI_API_KEY not set in .env file"
    exit 1
fi

log_success "Pre-flight checks passed"

# Step 1: Backup
if [ "$SKIP_BACKUP" = false ]; then
    log_info "Step 1/6: Creating backup..."
    bash "$SCRIPT_DIR/backup.sh" --keep 5

    if [ $? -ne 0 ]; then
        log_error "Backup failed! Aborting deployment."
        exit 1
    fi

    log_success "Backup complete"
else
    log_warning "Step 1/6: Skipping backup (--skip-backup flag set)"
fi

# Step 2: Build production images
log_info "Step 2/6: Building production images..."
cd "$DOCKER_DIR"

if [ -n "$COMPOSE_PROFILE" ]; then
    log_info "Using profile: $COMPOSE_PROFILE"
    docker compose -f docker-compose.prod.yml --profile "$COMPOSE_PROFILE" build
else
    docker compose -f docker-compose.prod.yml build
fi

if [ $? -ne 0 ]; then
    log_error "Image build failed! Aborting deployment."
    exit 1
fi

log_success "Images built successfully"

# Step 3: Stop old containers gracefully
log_info "Step 3/6: Stopping old containers..."

# Give containers time to finish requests
OLD_CONTAINERS=$(docker compose -f docker-compose.prod.yml ps -q 2>/dev/null || true)
if [ -n "$OLD_CONTAINERS" ]; then
    log_info "Found running containers, stopping gracefully (30s timeout)..."
    docker compose -f docker-compose.prod.yml down --timeout 30
    log_success "Old containers stopped"
else
    log_info "No running containers found"
fi

# Step 4: Start new containers
log_info "Step 4/6: Starting new containers..."

if [ -n "$COMPOSE_PROFILE" ]; then
    docker compose -f docker-compose.prod.yml --profile "$COMPOSE_PROFILE" up -d
else
    docker compose -f docker-compose.prod.yml up -d
fi

if [ $? -ne 0 ]; then
    log_error "Failed to start containers!"
    if [ "$NO_ROLLBACK" = false ]; then
        perform_rollback
    else
        exit 1
    fi
fi

log_success "Containers started"

# Step 5: Wait for health check
log_info "Step 5/6: Waiting for health check..."

echo -n "Checking API health"
HEALTH_CHECK_COUNT=0
HEALTH_PASSED=false

while [ $HEALTH_CHECK_COUNT -lt $MAX_HEALTH_CHECKS ]; do
    # Check if container is still running
    if ! docker compose -f docker-compose.prod.yml ps | grep -q "zoocari-api-prod"; then
        echo ""
        log_error "Container exited unexpectedly!"
        log_error "Check logs with: docker logs zoocari-api-prod"

        if [ "$NO_ROLLBACK" = false ]; then
            perform_rollback
        else
            exit 1
        fi
    fi

    # Check health endpoint
    if curl -sf "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        echo ""
        log_success "Health check passed!"
        HEALTH_PASSED=true
        break
    fi

    echo -n "."
    sleep 10
    HEALTH_CHECK_COUNT=$((HEALTH_CHECK_COUNT + 1))
done

if [ "$HEALTH_PASSED" = false ]; then
    echo ""
    log_error "Health check failed after $((MAX_HEALTH_CHECKS * 10)) seconds"
    log_error "Container logs:"
    docker logs --tail 50 zoocari-api-prod

    if [ "$NO_ROLLBACK" = false ]; then
        perform_rollback
    else
        exit 1
    fi
fi

# Step 6: Verify deployment
log_info "Step 6/6: Verifying deployment..."

# Check container status
CONTAINER_STATUS=$(docker compose -f docker-compose.prod.yml ps --format json | jq -r '.[0].Health')
log_info "Container health status: $CONTAINER_STATUS"

# Check API version (if endpoint exists)
API_VERSION=$(curl -s "$HEALTH_ENDPOINT" | jq -r '.version // "unknown"' 2>/dev/null || echo "unknown")
log_info "API version: $API_VERSION"

log_success "Deployment verified"

# Final summary
echo ""
echo "============================================================"
log_success "Deployment Complete!"
echo "============================================================"
echo ""
echo "Services running:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "API endpoint:     ${GREEN}http://localhost:8000${NC}"
echo "Health endpoint:  ${GREEN}$HEALTH_ENDPOINT${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:        docker logs -f zoocari-api-prod"
echo "  Stop services:    cd $DOCKER_DIR && docker compose -f docker-compose.prod.yml down"
echo "  Restart:          cd $DOCKER_DIR && docker compose -f docker-compose.prod.yml restart"
echo "  Rollback:         ./scripts/rollback.sh"
echo ""
echo "============================================================"
