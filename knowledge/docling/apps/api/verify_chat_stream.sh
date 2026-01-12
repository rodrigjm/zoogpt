#!/bin/bash
# Verification script for POST /chat/stream endpoint

BASE_URL="${1:-http://localhost:8000}"

echo "========================================="
echo "Testing POST /chat/stream (SSE)"
echo "Base URL: $BASE_URL"
echo "========================================="

# Step 1: Create a session
echo -e "\n[1/4] Creating session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/session" \
  -H "Content-Type: application/json" \
  -d '{"client": "test", "metadata": {}}')

SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION_ID" ]; then
  echo "ERROR: Failed to create session"
  echo "Response: $SESSION_RESPONSE"
  exit 1
fi

echo "Session created: $SESSION_ID"

# Step 2: Test streaming chat
echo -e "\n[2/4] Testing streaming chat endpoint..."
echo "Sending: 'What do elephants eat?'"
echo -e "\nStreaming response:"
echo "----------------------------------------"

curl -N -X POST "$BASE_URL/chat/stream" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"What do elephants eat?\"}" \
  2>/dev/null | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
      # Extract JSON after "data: "
      json_data="${line#data: }"

      # Parse type field
      type=$(echo "$json_data" | grep -o '"type":"[^"]*"' | cut -d'"' -f4)

      if [ "$type" = "text" ]; then
        # Extract and display content
        content=$(echo "$json_data" | grep -o '"content":"[^"]*"' | cut -d'"' -f4)
        echo -n "$content"
      elif [ "$type" = "done" ]; then
        echo -e "\n----------------------------------------"
        echo "Stream completed!"

        # Extract sources count
        sources=$(echo "$json_data" | grep -o '"sources":\[[^]]*\]')
        echo "Sources: $sources"

        # Extract followup questions
        questions=$(echo "$json_data" | grep -o '"followup_questions":\[[^]]*\]')
        echo "Follow-up questions: $questions"
      elif [ "$type" = "error" ]; then
        echo -e "\n----------------------------------------"
        echo "ERROR in stream:"
        echo "$json_data"
      fi
    fi
done

echo -e "\n"

# Step 3: Test session not found
echo -e "\n[3/4] Testing session not found (should return 404 JSON)..."
NOT_FOUND_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "non-existent", "message": "test"}')

HTTP_CODE=$(echo "$NOT_FOUND_RESPONSE" | tail -n1)
BODY=$(echo "$NOT_FOUND_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "404" ]; then
  echo "✓ Correctly returned 404"
  echo "Error response: $BODY"
else
  echo "✗ Expected 404, got $HTTP_CODE"
  echo "Response: $BODY"
fi

# Step 4: Test validation (empty message)
echo -e "\n[4/4] Testing validation (empty message should return 422)..."
VALIDATION_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/chat/stream" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"\"}")

HTTP_CODE=$(echo "$VALIDATION_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "422" ]; then
  echo "✓ Correctly returned 422 for empty message"
else
  echo "✗ Expected 422, got $HTTP_CODE"
fi

echo -e "\n========================================="
echo "POST /chat/stream verification complete!"
echo "========================================="
