#!/usr/bin/env bash
#
# Staging Validation Script
# Tests all API endpoints and verifies response shapes match CONTRACT.md
#
# Usage:
#   ./scripts/staging-validate.sh [API_BASE_URL]
#
# Example:
#   ./scripts/staging-validate.sh http://localhost:8000
#   ./scripts/staging-validate.sh https://staging.zoocari.com
#

set -euo pipefail

# Configuration
API_BASE_URL="${1:-http://localhost:8000}"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Test result tracking
declare -a FAILURES

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILURES+=("$1")
    ((FAILED++))
}

# Helper to check JSON field exists
check_field() {
    local response="$1"
    local field="$2"
    echo "$response" | jq -e ".$field" > /dev/null 2>&1
}

# Helper to check HTTP status
check_status() {
    local actual="$1"
    local expected="$2"
    [[ "$actual" == "$expected" ]]
}

echo "=========================================="
echo "Zoocari Staging Validation"
echo "=========================================="
echo "API Base URL: $API_BASE_URL"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Test 1: Health Check
log_info "Test 1: GET /health"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/health")
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n 1)
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | tail -n 1)

if check_status "$HEALTH_STATUS" "200" && echo "$HEALTH_BODY" | jq -e '.ok == true' > /dev/null 2>&1; then
    log_pass "Health check returned 200 with {ok: true}"
else
    log_fail "Health check failed (status: $HEALTH_STATUS, body: $HEALTH_BODY)"
fi

# Test 2: Create Session
log_info "Test 2: POST /session"
SESSION_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/session" \
    -H "Content-Type: application/json" \
    -d '{"client": "web", "metadata": {}}')
SESSION_BODY=$(echo "$SESSION_RESPONSE" | head -n 1)
SESSION_STATUS=$(echo "$SESSION_RESPONSE" | tail -n 1)

if check_status "$SESSION_STATUS" "200" && check_field "$SESSION_BODY" "session_id" && check_field "$SESSION_BODY" "created_at"; then
    SESSION_ID=$(echo "$SESSION_BODY" | jq -r '.session_id')
    log_pass "Session created (ID: $SESSION_ID)"
else
    log_fail "Session creation failed (status: $SESSION_STATUS, body: $SESSION_BODY)"
    SESSION_ID=""
fi

# Test 3: Retrieve Session
if [[ -n "$SESSION_ID" ]]; then
    log_info "Test 3: GET /session/{id}"
    GET_SESSION_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/session/$SESSION_ID")
    GET_SESSION_BODY=$(echo "$GET_SESSION_RESPONSE" | head -n 1)
    GET_SESSION_STATUS=$(echo "$GET_SESSION_RESPONSE" | tail -n 1)

    if check_status "$GET_SESSION_STATUS" "200" && check_field "$GET_SESSION_BODY" "session_id"; then
        RETRIEVED_ID=$(echo "$GET_SESSION_BODY" | jq -r '.session_id')
        if [[ "$RETRIEVED_ID" == "$SESSION_ID" ]]; then
            log_pass "Session retrieved correctly"
        else
            log_fail "Session ID mismatch (expected: $SESSION_ID, got: $RETRIEVED_ID)"
        fi
    else
        log_fail "Session retrieval failed (status: $GET_SESSION_STATUS)"
    fi
else
    log_fail "Skipping session retrieval (no session ID)"
fi

# Test 4: Chat Message
if [[ -n "$SESSION_ID" ]]; then
    log_info "Test 4: POST /chat"
    CHAT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Tell me about elephants\", \"mode\": \"rag\", \"metadata\": {}}")
    CHAT_BODY=$(echo "$CHAT_RESPONSE" | head -n 1)
    CHAT_STATUS=$(echo "$CHAT_RESPONSE" | tail -n 1)

    if check_status "$CHAT_STATUS" "200" && check_field "$CHAT_BODY" "reply" && check_field "$CHAT_BODY" "message_id"; then
        REPLY=$(echo "$CHAT_BODY" | jq -r '.reply')
        log_pass "Chat message returned reply (length: ${#REPLY} chars)"
    else
        log_fail "Chat message failed (status: $CHAT_STATUS, body: $CHAT_BODY)"
    fi
else
    log_fail "Skipping chat test (no session ID)"
fi

# Test 5: Chat Streaming (basic check)
if [[ -n "$SESSION_ID" ]]; then
    log_info "Test 5: POST /chat/stream (SSE)"
    STREAM_STATUS=$(curl -s -w "%{http_code}" -o "$TEMP_DIR/stream.txt" -X POST "$API_BASE_URL/chat/stream" \
        -H "Content-Type: application/json" \
        -H "Accept: text/event-stream" \
        -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Quick question\", \"mode\": \"rag\", \"metadata\": {}}")

    if check_status "$STREAM_STATUS" "200" && grep -q "data:" "$TEMP_DIR/stream.txt"; then
        log_pass "Streaming endpoint returned SSE data"
    else
        log_fail "Streaming endpoint failed (status: $STREAM_STATUS)"
    fi
else
    log_fail "Skipping stream test (no session ID)"
fi

# Test 6: STT Endpoint (requires audio file)
log_info "Test 6: POST /voice/stt"
# Create a minimal WAV file (1 second of silence, 16kHz mono)
# WAV header for 16kHz, 16-bit, mono, 1 second
printf "RIFF\x24\x58\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x58\x00\x00" > "$TEMP_DIR/test.wav"
dd if=/dev/zero bs=1 count=22528 >> "$TEMP_DIR/test.wav" 2>/dev/null

if [[ -n "$SESSION_ID" ]]; then
    STT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/voice/stt" \
        -F "session_id=$SESSION_ID" \
        -F "audio=@$TEMP_DIR/test.wav")
    STT_BODY=$(echo "$STT_RESPONSE" | head -n 1)
    STT_STATUS=$(echo "$STT_RESPONSE" | tail -n 1)

    if check_status "$STT_STATUS" "200" && check_field "$STT_BODY" "text"; then
        log_pass "STT endpoint accepts audio and returns text"
    else
        log_fail "STT endpoint failed (status: $STT_STATUS, body: $STT_BODY)"
    fi
else
    log_fail "Skipping STT test (no session ID)"
fi

# Test 7: TTS Endpoint
if [[ -n "$SESSION_ID" ]]; then
    log_info "Test 7: POST /voice/tts"
    TTS_STATUS=$(curl -s -w "%{http_code}" -o "$TEMP_DIR/output.audio" -X POST "$API_BASE_URL/voice/tts" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\", \"text\": \"Hello\", \"voice\": \"default\"}")

    if check_status "$TTS_STATUS" "200" && [[ -s "$TEMP_DIR/output.audio" ]]; then
        FILE_SIZE=$(wc -c < "$TEMP_DIR/output.audio")
        log_pass "TTS endpoint returned audio (size: $FILE_SIZE bytes)"
    else
        log_fail "TTS endpoint failed (status: $TTS_STATUS)"
    fi
else
    log_fail "Skipping TTS test (no session ID)"
fi

# Test 8: Performance Check (Response Time)
log_info "Test 8: Response time check"
if [[ -n "$SESSION_ID" ]]; then
    START_TIME=$(date +%s%N)
    PERF_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"What animals are here?\", \"mode\": \"rag\", \"metadata\": {}}")
    END_TIME=$(date +%s%N)
    PERF_STATUS=$(echo "$PERF_RESPONSE" | tail -n 1)

    ELAPSED_MS=$(( (END_TIME - START_TIME) / 1000000 ))

    if check_status "$PERF_STATUS" "200" && [[ $ELAPSED_MS -lt 2000 ]]; then
        log_pass "Chat response time acceptable (${ELAPSED_MS}ms < 2000ms)"
    else
        log_fail "Chat response time too slow (${ELAPSED_MS}ms >= 2000ms)"
    fi
else
    log_fail "Skipping performance test (no session ID)"
fi

# Summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo "Failed Tests:"
    for failure in "${FAILURES[@]}"; do
        echo "  - $failure"
    done
    echo ""
    exit 1
else
    echo ""
    echo -e "${GREEN}All validation checks passed!${NC}"
    exit 0
fi
