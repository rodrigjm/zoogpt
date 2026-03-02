#!/bin/bash
#
# Run integration smoke tests for Phase 1 API endpoints.
# Tests verify all endpoints work correctly together in end-to-end flows.
#
# Usage:
#   ./run_smoke_tests.sh              # Run all smoke tests
#   ./run_smoke_tests.sh --verbose    # Run with verbose output
#   ./run_smoke_tests.sh --failfast   # Stop on first failure
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Phase 1 Integration Smoke Tests${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${RED}Warning: Virtual environment not activated${NC}"
    echo "Activating venv..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: venv directory not found${NC}"
        echo "Please run: python -m venv venv && source venv/bin/activate"
        exit 1
    fi
fi

# Parse arguments
PYTEST_ARGS="-m smoke"

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            PYTEST_ARGS="$PYTEST_ARGS -vv"
            shift
            ;;
        --failfast|-x)
            PYTEST_ARGS="$PYTEST_ARGS -x"
            shift
            ;;
        --quiet|-q)
            PYTEST_ARGS="$PYTEST_ARGS -q"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v    Verbose output"
            echo "  --failfast, -x   Stop on first failure"
            echo "  --quiet, -q      Minimal output"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Running smoke tests..."
echo ""

# Run pytest with smoke marker
if pytest $PYTEST_ARGS tests/test_integration_smoke.py; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}All smoke tests passed!${NC}"
    echo -e "${GREEN}================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}Some smoke tests failed!${NC}"
    echo -e "${RED}================================${NC}"
    exit 1
fi
