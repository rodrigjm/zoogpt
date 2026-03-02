#!/bin/bash
# ============================================================
# Zoocari Production Rollback Script
# ============================================================
# Rollback to previous backup or container version
#
# Usage:
#   ./scripts/rollback-prod.sh [--backup TIMESTAMP] [--skip-health-check]
#
# This script will:
#   1. Stop current containers
#   2. Restore from backup (if specified)
#   3. Start previous version containers
#   4. Verify health
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
DOCKER_DIR="$PROJECT_ROOT/docker"
DATA_DIR="$PROJECT_ROOT/data"
BACKUP_ROOT="$DATA_DIR/backups"
COMPOSE_FILE="$DOCKER_DIR/docker-compose.prod.yml"
HEALTH_ENDPOINT="http://localhost:8000/health"
MAX_HEALTH_CHECKS=20  # 20 attempts * 10 seconds = 3.3 minutes max wait
SKIP_HEALTH_CHECK=false
BACKUP_TIMESTAMP=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup)
            BACKUP_TIMESTAMP="$2"
            shift 2
            ;;
        --skip-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--backup TIMESTAMP] [--skip-health-check]"
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

# Banner
echo "============================================================"
echo "  Zoocari Production Rollback"
echo "============================================================"
echo ""

# Step 1: Stop current containers
log_info "Step 1/4: Stopping current containers..."

cd "$DOCKER_DIR"
if docker compose -f docker-compose.prod.yml ps -q | grep -q .; then
    log_info "Stopping containers gracefully (30s timeout)..."
    docker compose -f docker-compose.prod.yml down --timeout 30
    log_success "Containers stopped"
else
    log_info "No running containers found"
fi

# Step 2: Restore from backup (if specified)
if [ -n "$BACKUP_TIMESTAMP" ]; then
    log_info "Step 2/4: Restoring from backup: $BACKUP_TIMESTAMP..."

    BACKUP_DIR="$BACKUP_ROOT/$BACKUP_TIMESTAMP"

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup not found: $BACKUP_DIR"
        log_error "Available backups:"
        ls -1 "$BACKUP_ROOT" 2>/dev/null || echo "  (none)"
        exit 1
    fi

    # Restore SQLite database
    if [ -f "$BACKUP_DIR/sessions.db" ]; then
        log_info "Restoring SQLite database..."
        cp "$BACKUP_DIR/sessions.db" "$DATA_DIR/sessions.db"
        log_success "SQLite database restored"
    elif [ -f "$BACKUP_DIR/sessions.db.missing" ]; then
        log_warning "Original backup had no SQLite database"
    else
        log_warning "No SQLite backup found in $BACKUP_DIR"
    fi

    # Restore LanceDB (if exists)
    if [ -d "$BACKUP_DIR/zoo_lancedb" ]; then
        log_info "Restoring LanceDB..."
        rm -rf "$DATA_DIR/zoo_lancedb"
        cp -r "$BACKUP_DIR/zoo_lancedb" "$DATA_DIR/zoo_lancedb"
        log_success "LanceDB restored"
    elif [ -f "$BACKUP_DIR/zoo_lancedb.skipped" ]; then
        log_info "LanceDB was skipped in backup (too large)"
    elif [ -f "$BACKUP_DIR/zoo_lancedb.missing" ]; then
        log_warning "Original backup had no LanceDB"
    else
        log_info "No LanceDB backup to restore"
    fi

    log_success "Backup restoration complete"
else
    log_info "Step 2/4: No backup specified, keeping current data"
fi

# Step 3: Start containers
log_info "Step 3/4: Starting containers..."

cd "$DOCKER_DIR"

# Try to pull previous images if available
log_info "Checking for previous images..."
docker compose -f docker-compose.prod.yml pull || log_info "No newer images to pull"

# Start containers
docker compose -f docker-compose.prod.yml up -d

if [ $? -ne 0 ]; then
    log_error "Failed to start containers!"
    log_error "Check logs with: docker logs zoocari-api-prod"
    exit 1
fi

log_success "Containers started"

# Step 4: Health check
if [ "$SKIP_HEALTH_CHECK" = false ]; then
    log_info "Step 4/4: Performing health check..."

    echo -n "Waiting for API to be ready"
    HEALTH_CHECK_COUNT=0
    HEALTH_PASSED=false

    while [ $HEALTH_CHECK_COUNT -lt $MAX_HEALTH_CHECKS ]; do
        # Check if container is still running
        if ! docker compose -f docker-compose.prod.yml ps | grep -q "zoocari-api-prod"; then
            echo ""
            log_error "Container exited unexpectedly!"
            log_error "Check logs with: docker logs zoocari-api-prod"
            exit 1
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
        log_error "Container may still be starting. Check logs with:"
        log_error "  docker logs zoocari-api-prod"
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
echo "API is now running at:"
echo "  ${GREEN}http://localhost:8000${NC}"
echo ""
echo "Health endpoint:"
echo "  ${GREEN}$HEALTH_ENDPOINT${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:        docker logs -f zoocari-api-prod"
echo "  Stop app:         cd $DOCKER_DIR && docker compose -f docker-compose.prod.yml down"
echo "  Restart app:      cd $DOCKER_DIR && docker compose -f docker-compose.prod.yml restart"
echo "  View containers:  docker ps | grep zoocari"
echo ""
if [ -n "$BACKUP_TIMESTAMP" ]; then
    echo "Restored from backup: $BACKUP_TIMESTAMP"
else
    echo "Data was not restored (no backup specified)"
fi
echo "============================================================"
