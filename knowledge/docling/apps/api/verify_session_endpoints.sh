#!/bin/bash
# Verification script for session endpoints per CONTRACT.md

set -e

API_URL="http://localhost:8000"

echo "=== Testing Session Endpoints ==="
echo

echo "1. Testing POST /session (minimal)"
RESPONSE=$(curl -s -X POST $API_URL/session -H "Content-Type: application/json" -d '{}')
echo "$RESPONSE" | jq .
SESSION_ID=$(echo "$RESPONSE" | jq -r .session_id)
echo "Created session: $SESSION_ID"
echo

echo "2. Testing POST /session (with metadata)"
RESPONSE=$(curl -s -X POST $API_URL/session \
  -H "Content-Type: application/json" \
  -d '{"client": "mobile", "metadata": {"version": "1.0", "feature": "test"}}')
echo "$RESPONSE" | jq .
SESSION_ID2=$(echo "$RESPONSE" | jq -r .session_id)
echo "Created session: $SESSION_ID2"
echo

echo "3. Testing GET /session/{session_id} (existing)"
curl -s $API_URL/session/$SESSION_ID2 | jq .
echo

echo "4. Testing GET /session/{session_id} (not found - should return 404)"
curl -s $API_URL/session/nonexistent-id-12345 | jq .
echo

echo "5. Testing health endpoint"
curl -s $API_URL/health | jq .
echo

echo "=== All tests complete ==="
