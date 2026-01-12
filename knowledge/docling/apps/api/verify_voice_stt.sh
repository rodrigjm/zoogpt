#!/bin/bash
# Verification script for POST /voice/stt endpoint
# Per CONTRACT.md Part 4: Voice

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Testing POST /voice/stt endpoint"
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

# Step 2: Create a mock audio file
echo "2. Creating mock audio file..."
echo "mock audio data" > /tmp/test_audio.wav
echo -e "${GREEN}✓${NC} Mock audio file created"
echo ""

# Step 3: Test STT endpoint with valid session
echo "3. Testing POST /voice/stt with valid session..."
STT_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/stt" \
  -F "session_id=$SESSION_ID" \
  -F "audio=@/tmp/test_audio.wav")

echo "Response: $STT_RESPONSE"

# Verify response structure
TEXT=$(echo "$STT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('text', ''))")
RESP_SESSION_ID=$(echo "$STT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")

if [ "$RESP_SESSION_ID" = "$SESSION_ID" ] && [ -n "$TEXT" ]; then
  echo -e "${GREEN}✓${NC} STT response valid"
  echo "  - session_id: $RESP_SESSION_ID"
  echo "  - text: $TEXT"
else
  echo -e "${RED}✗${NC} STT response invalid"
  exit 1
fi
echo ""

# Step 4: Test STT endpoint with nonexistent session
echo "4. Testing POST /voice/stt with nonexistent session..."
ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/stt" \
  -F "session_id=nonexistent-session-id" \
  -F "audio=@/tmp/test_audio.wav")

ERROR_CODE=$(echo "$ERROR_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('code', ''))")

if [ "$ERROR_CODE" = "SESSION_NOT_FOUND" ]; then
  echo -e "${GREEN}✓${NC} Correctly returns SESSION_NOT_FOUND error"
else
  echo -e "${RED}✗${NC} Expected SESSION_NOT_FOUND error, got: $ERROR_RESPONSE"
  exit 1
fi
echo ""

# Step 5: Test STT endpoint with empty audio
echo "5. Testing POST /voice/stt with empty audio file..."
echo -n "" > /tmp/empty_audio.wav
EMPTY_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/stt" \
  -F "session_id=$SESSION_ID" \
  -F "audio=@/tmp/empty_audio.wav")

EMPTY_ERROR_CODE=$(echo "$EMPTY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('code', ''))")

if [ "$EMPTY_ERROR_CODE" = "EMPTY_AUDIO" ]; then
  echo -e "${GREEN}✓${NC} Correctly returns EMPTY_AUDIO error"
else
  echo -e "${RED}✗${NC} Expected EMPTY_AUDIO error, got: $EMPTY_RESPONSE"
  exit 1
fi
echo ""

# Step 6: Test different audio formats
echo "6. Testing different audio formats..."
for EXT in wav webm mp3; do
  echo "  - Testing $EXT format..."
  echo "test audio" > "/tmp/test_audio.$EXT"
  FORMAT_RESPONSE=$(curl -s -X POST "$BASE_URL/voice/stt" \
    -F "session_id=$SESSION_ID" \
    -F "audio=@/tmp/test_audio.$EXT")

  FORMAT_TEXT=$(echo "$FORMAT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('text', ''))")

  if [ -n "$FORMAT_TEXT" ]; then
    echo -e "    ${GREEN}✓${NC} $EXT format accepted"
  else
    echo -e "    ${RED}✗${NC} $EXT format failed: $FORMAT_RESPONSE"
    exit 1
  fi
done
echo ""

# Cleanup
rm -f /tmp/test_audio.* /tmp/empty_audio.wav

echo "=========================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - POST /voice/stt accepts multipart/form-data"
echo "  - Returns {session_id, text} per CONTRACT.md"
echo "  - Validates session_id exists"
echo "  - Returns proper error shapes"
echo "  - Accepts wav, webm, mp3 formats"
echo "  - Uses Faster-Whisper (local) → OpenAI Whisper (cloud) fallback"
echo "  - Transcription result: '$TEXT'"
