#!/bin/bash
# ============================================================
# Zoocari Deployment Scripts Test
# ============================================================
# Tests deployment scripts without actually deploying
#
# This script verifies:
#   1. All scripts have valid syntax
#   2. Required files and directories exist
#   3. Scripts have proper permissions
#   4. Environment is configured correctly
# ============================================================

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

TESTS_PASSED=0
TESTS_FAILED=0

test_pass() {
    log_success "$1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    log_error "$1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

echo "============================================================"
echo "  Zoocari Deployment Scripts Test Suite"
echo "============================================================"
echo ""

# Test 1: Script syntax
log_info "Test 1: Checking script syntax..."
if bash -n "$SCRIPT_DIR/backup.sh" 2>/dev/null; then
    test_pass "backup.sh syntax valid"
else
    test_fail "backup.sh has syntax errors"
fi

if bash -n "$SCRIPT_DIR/deploy.sh" 2>/dev/null; then
    test_pass "deploy.sh syntax valid"
else
    test_fail "deploy.sh has syntax errors"
fi

if bash -n "$SCRIPT_DIR/rollback-prod.sh" 2>/dev/null; then
    test_pass "rollback-prod.sh syntax valid"
else
    test_fail "rollback-prod.sh has syntax errors"
fi

if bash -n "$SCRIPT_DIR/rollback.sh" 2>/dev/null; then
    test_pass "rollback.sh syntax valid"
else
    test_fail "rollback.sh has syntax errors"
fi

# Test 2: Script permissions
log_info "Test 2: Checking script permissions..."
if [ -x "$SCRIPT_DIR/backup.sh" ]; then
    test_pass "backup.sh is executable"
else
    test_fail "backup.sh is not executable"
fi

if [ -x "$SCRIPT_DIR/deploy.sh" ]; then
    test_pass "deploy.sh is executable"
else
    test_fail "deploy.sh is not executable"
fi

if [ -x "$SCRIPT_DIR/rollback-prod.sh" ]; then
    test_pass "rollback-prod.sh is executable"
else
    test_fail "rollback-prod.sh is not executable"
fi

# Test 3: Required files
log_info "Test 3: Checking required files..."
if [ -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" ]; then
    test_pass "docker-compose.prod.yml exists"
else
    test_fail "docker-compose.prod.yml missing"
fi

if [ -f "$PROJECT_ROOT/.env" ]; then
    test_pass ".env file exists"
else
    test_fail ".env file missing"
fi

# Test 4: Required directories
log_info "Test 4: Checking required directories..."
if [ -d "$PROJECT_ROOT/data" ]; then
    test_pass "data/ directory exists"
else
    test_fail "data/ directory missing"
fi

if [ -d "$PROJECT_ROOT/docker" ]; then
    test_pass "docker/ directory exists"
else
    test_fail "docker/ directory missing"
fi

# Test 5: Data files
log_info "Test 5: Checking data files..."
if [ -f "$PROJECT_ROOT/data/sessions.db" ]; then
    test_pass "sessions.db exists"
else
    log_info "sessions.db not found (will be created on first run)"
fi

if [ -d "$PROJECT_ROOT/data/zoo_lancedb" ]; then
    test_pass "zoo_lancedb/ exists"
else
    log_info "zoo_lancedb/ not found (will be created on first run)"
fi

# Test 6: Docker availability
log_info "Test 6: Checking Docker..."
if command -v docker &> /dev/null; then
    test_pass "docker command available"

    if docker info >/dev/null 2>&1; then
        test_pass "Docker daemon is running"
    else
        test_fail "Docker daemon is not running"
    fi
else
    test_fail "docker command not found"
fi

# Test 7: Required commands
log_info "Test 7: Checking required commands..."
if command -v curl &> /dev/null; then
    test_pass "curl available"
else
    test_fail "curl not found (required for health checks)"
fi

if command -v sqlite3 &> /dev/null; then
    test_pass "sqlite3 available"
else
    log_info "sqlite3 not found (optional, but recommended for consistent backups)"
fi

if command -v jq &> /dev/null; then
    test_pass "jq available"
else
    log_info "jq not found (optional, used for JSON parsing)"
fi

# Test 8: Environment variables
log_info "Test 8: Checking environment variables..."
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"

    if [ -n "$OPENAI_API_KEY" ]; then
        test_pass "OPENAI_API_KEY is set"
    else
        test_fail "OPENAI_API_KEY not set in .env"
    fi

    if [ -n "$CORS_ORIGINS" ]; then
        test_pass "CORS_ORIGINS is set"
    else
        log_info "CORS_ORIGINS not set (optional, defaults to localhost)"
    fi
fi

# Test 9: Backup directory
log_info "Test 9: Checking backup directory..."
BACKUP_DIR="$PROJECT_ROOT/data/backups"
if [ -d "$BACKUP_DIR" ]; then
    test_pass "Backup directory exists"

    # Check write permissions
    if [ -w "$BACKUP_DIR" ]; then
        test_pass "Backup directory is writable"
    else
        test_fail "Backup directory is not writable"
    fi
else
    log_info "Backup directory will be created on first backup"
fi

# Summary
echo ""
echo "============================================================"
echo "  Test Summary"
echo "============================================================"
echo ""
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Failed:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed!${NC}"
    echo ""
    echo "You can now run:"
    echo "  ./scripts/deploy.sh       - Deploy to production"
    echo "  ./scripts/backup.sh       - Create data backup"
    echo "  ./scripts/rollback-prod.sh - Rollback production"
    echo "============================================================"
    exit 0
else
    echo -e "${RED}Some tests failed. Please fix issues before deploying.${NC}"
    echo "============================================================"
    exit 1
fi
