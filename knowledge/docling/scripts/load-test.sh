#!/usr/bin/env bash
#
# Load Testing Script
# Sends concurrent requests to /chat endpoint and measures performance
#
# Usage:
#   ./scripts/load-test.sh [API_BASE_URL] [NUM_REQUESTS] [CONCURRENCY]
#
# Example:
#   ./scripts/load-test.sh http://localhost:8000 100 10
#   ./scripts/load-test.sh https://staging.zoocari.com 50 5
#

set -euo pipefail

# Configuration
API_BASE_URL="${1:-http://localhost:8000}"
NUM_REQUESTS="${2:-50}"
CONCURRENCY="${3:-5}"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Zoocari Load Test"
echo "=========================================="
echo "API Base URL: $API_BASE_URL"
echo "Total Requests: $NUM_REQUESTS"
echo "Concurrency: $CONCURRENCY"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Step 1: Create a test session
echo -e "${YELLOW}[1/3] Creating test session...${NC}"
SESSION_RESPONSE=$(curl -s -X POST "$API_BASE_URL/session" \
    -H "Content-Type: application/json" \
    -d '{"client": "web", "metadata": {"test": "load_test"}}')

SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.session_id')

if [[ -z "$SESSION_ID" || "$SESSION_ID" == "null" ]]; then
    echo -e "${RED}Failed to create session${NC}"
    exit 1
fi

echo "Session ID: $SESSION_ID"
echo ""

# Step 2: Generate test requests
echo -e "${YELLOW}[2/3] Running load test...${NC}"

# Test messages
MESSAGES=(
    "Tell me about elephants"
    "What animals live here?"
    "Can you tell me about lions?"
    "What do giraffes eat?"
    "Where are the monkeys?"
)

# Function to send a single request
send_request() {
    local index=$1
    local message_index=$((index % ${#MESSAGES[@]}))
    local message="${MESSAGES[$message_index]}"

    local start_time=$(date +%s%N)
    local response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"$message\", \"mode\": \"rag\", \"metadata\": {}}")
    local end_time=$(date +%s%N)

    local status=$(echo "$response" | tail -n 1)
    local elapsed_ms=$(( (end_time - start_time) / 1000000 ))

    echo "$elapsed_ms,$status" >> "$TEMP_DIR/results.csv"
}

# Export function for parallel execution
export -f send_request
export API_BASE_URL SESSION_ID TEMP_DIR
export -a MESSAGES

# Create results file
touch "$TEMP_DIR/results.csv"

# Run requests with limited concurrency
START_TIME=$(date +%s)

# Use GNU parallel if available, otherwise fall back to simple background jobs
if command -v parallel > /dev/null 2>&1; then
    seq 1 "$NUM_REQUESTS" | parallel -j "$CONCURRENCY" send_request {}
else
    # Fallback: simple background jobs with concurrency control
    for i in $(seq 1 "$NUM_REQUESTS"); do
        while [[ $(jobs -r | wc -l) -ge $CONCURRENCY ]]; do
            sleep 0.1
        done
        send_request "$i" &
    done
    wait
fi

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo ""
echo -e "${YELLOW}[3/3] Analyzing results...${NC}"

# Step 3: Calculate statistics
if [[ ! -s "$TEMP_DIR/results.csv" ]]; then
    echo -e "${RED}No results collected${NC}"
    exit 1
fi

# Count successes and failures
TOTAL_ACTUAL=$(wc -l < "$TEMP_DIR/results.csv" | tr -d ' ')
SUCCESS_COUNT=$(awk -F',' '$2 == 200 {count++} END {print count+0}' "$TEMP_DIR/results.csv")
FAILURE_COUNT=$((TOTAL_ACTUAL - SUCCESS_COUNT))

# Calculate latency statistics (only for successful requests)
awk -F',' '$2 == 200 {print $1}' "$TEMP_DIR/results.csv" | sort -n > "$TEMP_DIR/latencies.txt"

if [[ ! -s "$TEMP_DIR/latencies.txt" ]]; then
    echo -e "${RED}No successful requests${NC}"
    exit 1
fi

COUNT=$(wc -l < "$TEMP_DIR/latencies.txt" | tr -d ' ')
MIN=$(head -n 1 "$TEMP_DIR/latencies.txt")
MAX=$(tail -n 1 "$TEMP_DIR/latencies.txt")
AVG=$(awk '{sum+=$1} END {print int(sum/NR)}' "$TEMP_DIR/latencies.txt")

# Calculate percentiles
P50_LINE=$(awk "BEGIN {print int($COUNT * 0.50)}")
P95_LINE=$(awk "BEGIN {print int($COUNT * 0.95)}")
P99_LINE=$(awk "BEGIN {print int($COUNT * 0.99)}")

P50=$(sed -n "${P50_LINE}p" "$TEMP_DIR/latencies.txt")
P95=$(sed -n "${P95_LINE}p" "$TEMP_DIR/latencies.txt")
P99=$(sed -n "${P99_LINE}p" "$TEMP_DIR/latencies.txt")

# Calculate throughput
THROUGHPUT=$(awk "BEGIN {printf \"%.2f\", $SUCCESS_COUNT / $TOTAL_TIME}")

# Display results
echo ""
echo "=========================================="
echo "Load Test Results"
echo "=========================================="
echo "Total Runtime: ${TOTAL_TIME}s"
echo "Requests Sent: $TOTAL_ACTUAL"
echo -e "Successful: ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "Failed: ${RED}$FAILURE_COUNT${NC}"
echo "Throughput: ${THROUGHPUT} req/s"
echo ""
echo "Latency (ms):"
echo "  Min:  ${MIN}ms"
echo "  Avg:  ${AVG}ms"
echo "  P50:  ${P50}ms"
echo "  P95:  ${P95}ms"
echo "  P99:  ${P99}ms"
echo "  Max:  ${MAX}ms"
echo ""

# Pass/Fail criteria
PASSED=true

if [[ $FAILURE_COUNT -gt 0 ]]; then
    echo -e "${RED}FAIL: $FAILURE_COUNT requests failed${NC}"
    PASSED=false
fi

if [[ $AVG -gt 2000 ]]; then
    echo -e "${RED}FAIL: Average latency (${AVG}ms) exceeds 2000ms threshold${NC}"
    PASSED=false
fi

if [[ $P95 -gt 5000 ]]; then
    echo -e "${RED}WARN: P95 latency (${P95}ms) exceeds 5000ms${NC}"
fi

if [[ "$PASSED" == "true" ]]; then
    echo -e "${GREEN}PASS: Load test successful${NC}"
    exit 0
else
    exit 1
fi
