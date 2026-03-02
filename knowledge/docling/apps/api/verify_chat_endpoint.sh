#!/bin/bash
# Verification script for POST /chat endpoint
# Per CONTRACT.md Part 4: Chat

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "================================"
echo "POST /chat Endpoint Verification"
echo "================================"
echo ""

# Step 1: Create a session
echo "Step 1: Creating session..."
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/session" \
  -H "Content-Type: application/json" \
  -d '{"client": "web", "metadata": {}}')

echo "Session created: $SESSION_RESPONSE"

# Extract session_id (using grep/sed for compatibility)
SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"session_id":"[^"]*"' | sed 's/"session_id":"\([^"]*\)"/\1/')
echo "Session ID: $SESSION_ID"
echo ""

# Step 2: Send chat message
echo "Step 2: Sending chat message..."
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What do lemurs eat?\",
    \"mode\": \"rag\",
    \"metadata\": {}
  }")

echo "Chat response: $CHAT_RESPONSE"
echo ""

# Verify response structure
echo "Step 3: Verifying response structure..."
if echo "$CHAT_RESPONSE" | grep -q '"session_id"' && \
   echo "$CHAT_RESPONSE" | grep -q '"message_id"' && \
   echo "$CHAT_RESPONSE" | grep -q '"reply"' && \
   echo "$CHAT_RESPONSE" | grep -q '"sources"' && \
   echo "$CHAT_RESPONSE" | grep -q '"created_at"'; then
    echo "✓ Response has all required fields"
else
    echo "✗ Response is missing required fields"
    exit 1
fi

# Step 4: Test error case - invalid session
echo ""
echo "Step 4: Testing error case (invalid session)..."
ERROR_RESPONSE=$(curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "invalid-session-id",
    "message": "Test message"
  }')

echo "Error response: $ERROR_RESPONSE"

if echo "$ERROR_RESPONSE" | grep -q '"error"' && \
   echo "$ERROR_RESPONSE" | grep -q '"SESSION_NOT_FOUND"'; then
    echo "✓ Error response has correct shape"
else
    echo "✗ Error response is incorrect"
    exit 1
fi

echo ""
echo "================================"
echo "✓ All verifications passed!"
echo "================================"
