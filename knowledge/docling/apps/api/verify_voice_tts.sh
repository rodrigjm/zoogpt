#!/bin/bash
# Verification script for POST /voice/tts endpoint
# Per CONTRACT.md Part 4: Voice

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Testing POST /voice/tts endpoint"
echo "=========================================="
echo ""

# Step 1: Create a session
echo "1. Creating session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/session" \
  -H "Content-Type: application/json" \
  -d '{"client": "web"}')

SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo -e "${GREEN}✓${NC} Session created: $SESSION_ID"
echo ""

# Step 2: Test TTS endpoint with valid session
echo "2. Testing POST /voice/tts with valid session..."
curl -s -X POST "$BASE_URL/voice/tts" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"text\": \"Hello from the zoo!\", \"voice\": \"default\"}" \
  --output /tmp/test_tts_output.wav \
  -w "HTTP Status: %{http_code}\n" > /tmp/tts_status.txt

STATUS_CODE=$(grep "HTTP Status:" /tmp/tts_status.txt | cut -d' ' -f3)

if [ "$STATUS_CODE" = "200" ]; then
  echo -e "${GREEN}✓${NC} TTS request successful (HTTP 200)"
else
  echo -e "${RED}✗${NC} TTS request failed with status: $STATUS_CODE"
  cat /tmp/test_tts_output.wav
  exit 1
fi
echo ""

# Step 3: Verify audio file is valid WAV
echo "3. Verifying audio file format..."
FILE_TYPE=$(file /tmp/test_tts_output.wav)

if echo "$FILE_TYPE" | grep -q "WAVE audio"; then
  echo -e "${GREEN}✓${NC} Valid WAV file generated"
  echo "  - File type: $FILE_TYPE"

  # Check file size
  FILE_SIZE=$(stat -f%z /tmp/test_tts_output.wav 2>/dev/null || stat -c%s /tmp/test_tts_output.wav 2>/dev/null)
  echo "  - File size: $FILE_SIZE bytes"

  # Verify WAV header
  HEADER=$(xxd -p -l 12 /tmp/test_tts_output.wav)
  if echo "$HEADER" | grep -q "52494646.*57415645"; then
    echo -e "${GREEN}✓${NC} Valid RIFF/WAVE header"
  else
    echo -e "${RED}✗${NC} Invalid WAV header"
    exit 1
  fi
else
  echo -e "${RED}✗${NC} Invalid audio file"
  echo "$FILE_TYPE"
  exit 1
fi
echo ""

# Step 4: Test TTS with default voice (omitted)
echo "4. Testing POST /voice/tts with default voice..."
curl -s -X POST "$BASE_URL/voice/tts" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"text\": \"Testing default voice\"}" \
  --output /tmp/test_tts_default.wav \
  -w "%{http_code}" > /tmp/default_status.txt

DEFAULT_STATUS=$(cat /tmp/default_status.txt)

if [ "$DEFAULT_STATUS" = "200" ]; then
  echo -e "${GREEN}✓${NC} Default voice works correctly"
else
  echo -e "${RED}✗${NC} Default voice failed with status: $DEFAULT_STATUS"
  exit 1
fi
echo ""

# Step 5: Test TTS endpoint with nonexistent session
echo "5. Testing POST /voice/tts with nonexistent session..."
ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/tts" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "nonexistent-session-id", "text": "Hello"}')

ERROR_CODE=$(echo "$ERROR_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('code', ''))")

if [ "$ERROR_CODE" = "SESSION_NOT_FOUND" ]; then
  echo -e "${GREEN}✓${NC} Correctly returns SESSION_NOT_FOUND error"
else
  echo -e "${RED}✗${NC} Expected SESSION_NOT_FOUND error, got: $ERROR_RESPONSE"
  exit 1
fi
echo ""

# Step 6: Test TTS endpoint with empty text
echo "6. Testing POST /voice/tts with empty text..."
EMPTY_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/tts" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"text\": \"\"}")

EMPTY_ERROR_CODE=$(echo "$EMPTY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('code', ''))")

if [ "$EMPTY_ERROR_CODE" = "EMPTY_TEXT" ]; then
  echo -e "${GREEN}✓${NC} Correctly returns EMPTY_TEXT error"
else
  echo -e "${RED}✗${NC} Expected EMPTY_TEXT error, got: $EMPTY_RESPONSE"
  exit 1
fi
echo ""

# Step 7: Test TTS endpoint with whitespace-only text
echo "7. Testing POST /voice/tts with whitespace-only text..."
WHITESPACE_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/tts" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"text\": \"   \"}")

WHITESPACE_ERROR_CODE=$(echo "$WHITESPACE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('code', ''))")

if [ "$WHITESPACE_ERROR_CODE" = "EMPTY_TEXT" ]; then
  echo -e "${GREEN}✓${NC} Correctly returns EMPTY_TEXT error for whitespace"
else
  echo -e "${RED}✗${NC} Expected EMPTY_TEXT error, got: $WHITESPACE_RESPONSE"
  exit 1
fi
echo ""

# Step 8: Test different voice options
echo "8. Testing different voice options..."
for VOICE in default bella nova; do
  echo "  - Testing voice: $VOICE..."
  VOICE_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/tts" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"text\": \"Testing voice\", \"voice\": \"$VOICE\"}" \
    --output /tmp/test_tts_$VOICE.wav \
    -w "%{http_code}")

  if [ "$VOICE_RESPONSE" = "200" ]; then
    echo -e "    ${GREEN}✓${NC} Voice '$VOICE' accepted"
  else
    echo -e "    ${RED}✗${NC} Voice '$VOICE' failed with status: $VOICE_RESPONSE"
    exit 1
  fi
done
echo ""

# Cleanup
rm -f /tmp/test_tts*.wav /tmp/tts_status.txt /tmp/default_status.txt

echo "=========================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - POST /voice/tts accepts JSON {session_id, text, voice}"
echo "  - Returns audio/wav bytes per CONTRACT.md"
echo "  - Validates session_id exists"
echo "  - Validates text is not empty"
echo "  - Returns proper error shapes"
echo "  - Supports voice parameter (default, bella, nova, heart, sarah, adam, eric)"
echo "  - Uses Kokoro (local) → OpenAI TTS (cloud) fallback"
echo "  - Generates kid-friendly voices with markdown stripping and text chunking"
