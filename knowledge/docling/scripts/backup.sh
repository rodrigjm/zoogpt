#!/bin/bash
# ============================================================
# Zoocari Backup Script
# ============================================================
# Backs up critical data before deployment
#
# Usage:
#   ./scripts/backup.sh [--keep N]
#
# This script will:
#   1. Create timestamped backup directory
#   2. Backup SQLite sessions database
#   3. Backup LanceDB vector database (optional)
#   4. Cleanup old backups (keep last N)
#
# Default: Keep last 5 backups
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
DATA_DIR="$PROJECT_ROOT/data"
BACKUP_ROOT="$DATA_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
KEEP_BACKUPS=5  # Keep last N backups

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep)
            KEEP_BACKUPS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--keep N]"
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
echo "  Zoocari Data Backup"
echo "============================================================"
echo ""

# Step 1: Create backup directory
log_info "Step 1/4: Creating backup directory..."
mkdir -p "$BACKUP_DIR"
log_success "Backup directory created: $BACKUP_DIR"

# Step 2: Backup SQLite database
log_info "Step 2/4: Backing up SQLite sessions database..."

if [ -f "$DATA_DIR/sessions.db" ]; then
    # Use sqlite3 to create a consistent backup (handles locks)
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$DATA_DIR/sessions.db" ".backup '$BACKUP_DIR/sessions.db'"
        log_success "SQLite database backed up using sqlite3"
    else
        # Fallback to cp if sqlite3 not available
        cp "$DATA_DIR/sessions.db" "$BACKUP_DIR/sessions.db"
        log_success "SQLite database backed up using cp"
    fi

    # Record size
    DB_SIZE=$(du -h "$DATA_DIR/sessions.db" | cut -f1)
    log_info "Database size: $DB_SIZE"
else
    log_warning "SQLite database not found at: $DATA_DIR/sessions.db"
    log_warning "Creating empty marker file"
    touch "$BACKUP_DIR/sessions.db.missing"
fi

# Step 3: Backup LanceDB (optional - can be large)
log_info "Step 3/4: Backing up LanceDB vector database..."

if [ -d "$DATA_DIR/zoo_lancedb" ]; then
    LANCEDB_SIZE=$(du -sh "$DATA_DIR/zoo_lancedb" | cut -f1)
    log_info "LanceDB size: $LANCEDB_SIZE"

    # Ask for confirmation if LanceDB is large (>100MB)
    LANCEDB_SIZE_MB=$(du -sm "$DATA_DIR/zoo_lancedb" | cut -f1)
    if [ "$LANCEDB_SIZE_MB" -gt 100 ]; then
        log_warning "LanceDB is large ($LANCEDB_SIZE). Backup may take time."
        log_info "Skipping LanceDB backup (vector DB can be rebuilt)..."
        touch "$BACKUP_DIR/zoo_lancedb.skipped"
    else
        log_info "Copying LanceDB directory..."
        cp -r "$DATA_DIR/zoo_lancedb" "$BACKUP_DIR/zoo_lancedb"
        log_success "LanceDB backed up"
    fi
else
    log_warning "LanceDB not found at: $DATA_DIR/zoo_lancedb"
    touch "$BACKUP_DIR/zoo_lancedb.missing"
fi

# Step 4: Cleanup old backups
log_info "Step 4/4: Cleaning up old backups (keeping last $KEEP_BACKUPS)..."

cd "$BACKUP_ROOT"
BACKUP_COUNT=$(ls -1d */ 2>/dev/null | wc -l | tr -d ' ')

if [ "$BACKUP_COUNT" -gt "$KEEP_BACKUPS" ]; then
    BACKUPS_TO_DELETE=$((BACKUP_COUNT - KEEP_BACKUPS))
    log_info "Found $BACKUP_COUNT backups, removing oldest $BACKUPS_TO_DELETE..."

    # List directories by modification time, oldest first, and remove excess
    ls -1td */ | tail -n "$BACKUPS_TO_DELETE" | while read dir; do
        log_info "Removing old backup: $dir"
        rm -rf "$dir"
    done

    log_success "Cleanup complete"
else
    log_info "Only $BACKUP_COUNT backups found, no cleanup needed"
fi

# Final summary
echo ""
echo "============================================================"
log_success "Backup Complete!"
echo "============================================================"
echo ""
echo "Backup location: ${GREEN}$BACKUP_DIR${NC}"
echo ""
echo "Backup contents:"
ls -lh "$BACKUP_DIR" | tail -n +2 | awk '{print "  "$9" ("$5")"}'
echo ""
echo "Total backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "To restore from this backup:"
echo "  ./scripts/rollback.sh --backup $TIMESTAMP"
echo "============================================================"
