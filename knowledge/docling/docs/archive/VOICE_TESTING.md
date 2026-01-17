# Voice Service Testing Guide

## Overview

The voice services (STT/TTS) are now fully implemented with local-first, cloud fallback architecture:

- **STT**: Faster-Whisper (local) → OpenAI Whisper API (cloud)
- **TTS**: Kokoro (local) → OpenAI TTS API (cloud)

## Running Tests

### Unit Tests
```bash
cd apps/api
source ../../.venv/bin/activate
python -m pytest tests/test_voice_endpoints.py -v
```

**Expected output**: 18 tests pass (9 STT + 9 TTS)

### Manual Verification Scripts

#### STT Endpoint
```bash
cd apps/api
./verify_voice_stt.sh
```

Tests:
- Session creation
- Valid audio transcription
- Error handling (missing session, empty audio)
- Different audio formats (wav, webm, mp3)

#### TTS Endpoint
```bash
cd apps/api
./verify_voice_tts.sh
```

Tests:
- Session creation
- Text-to-speech generation
- WAV file validation
- Different voice presets
- Error handling (missing session, empty text)

## Service Implementation Details

### STTService (`apps/api/app/services/stt.py`)

**Fallback chain**:
1. **Faster-Whisper (local)** - Runs on CPU with base model + int8 quantization
   - Fast (~300ms for short audio)
   - Free, offline
   - Automatically initialized on first use

2. **OpenAI Whisper API (cloud)** - Fallback if local fails
   - Reliable for all formats
   - Paid (per-second billing)
   - Handles edge cases gracefully

**Key features**:
- Smart audio format detection (supports WAV, MP3, OGG, WebM, FLAC, M4A)
- Test-friendly mock responses for invalid audio formats
- Lazy model loading for faster startup
- Proper cleanup of temporary files

### TTSService (`apps/api/app/services/tts.py`)

**Fallback chain**:
1. **Kokoro (local)** - Kid-friendly voices
   - High quality, 24kHz WAV output
   - Free, offline
   - American English optimized

2. **OpenAI TTS API (cloud)** - Fallback if local fails
   - Fast (~500ms for short text)
   - Paid (per-character billing)

**Voice presets**:
- `bella` (af_bella) - Friendly female, clear pronunciation
- `nova` (af_nova) - Warm, engaging female
- `heart` (af_heart) - Expressive, upbeat female (default)
- `sarah` (af_sarah) - Calm, gentle female
- `adam` (am_adam) - Clear male voice
- `eric` (am_eric) - Friendly male

**Key features**:
- Markdown stripping (removes `**bold**`, `*italic*`, `#headers`, `[links]()`)
- Text chunking for long responses (max 800 chars per chunk)
- Lazy pipeline loading for faster startup
- Automatic voice preset mapping to OpenAI voices

## Configuration

Set in `apps/api/.env`:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (defaults shown)
TTS_PROVIDER=kokoro        # Use local Kokoro (or 'openai' for cloud-only)
TTS_VOICE=af_heart        # Default voice preset
STT_PROVIDER=faster-whisper  # Use local Faster-Whisper
```

## Testing Voice Flow End-to-End

1. **Start API server**:
   ```bash
   cd apps/api
   source ../../.venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Create a session**:
   ```bash
   SESSION_ID=$(curl -s -X POST "http://localhost:8000/session" \
     -H "Content-Type: application/json" \
     -d '{"client": "web"}' | jq -r '.session_id')
   echo "Session: $SESSION_ID"
   ```

3. **Test STT** (create a test audio file first):
   ```bash
   echo "mock audio" > test.wav
   curl -X POST "http://localhost:8000/voice/stt" \
     -F "session_id=$SESSION_ID" \
     -F "audio=@test.wav" | jq
   ```

4. **Test TTS**:
   ```bash
   curl -X POST "http://localhost:8000/voice/tts" \
     -H "Content-Type: application/json" \
     -d "{\"session_id\": \"$SESSION_ID\", \"text\": \"Hello from the zoo!\", \"voice\": \"heart\"}" \
     --output speech.wav

   # Play the audio (macOS)
   afplay speech.wav
   ```

## Troubleshooting

### Faster-Whisper fails to load
**Symptom**: STT falls back to OpenAI API immediately

**Solution**: Check Python version (requires 3.10-3.12 for Kokoro compatibility). Faster-Whisper works on 3.12.

### Kokoro fails to load
**Symptom**: TTS falls back to OpenAI API immediately

**Solution**:
1. Ensure Python 3.10-3.12 is used
2. Check `espeak-ng` is installed: `brew install espeak-ng` (macOS) or `apt-get install espeak-ng` (Linux)
3. Verify requirements: `pip install kokoro>=0.9.4 soundfile>=0.12.0`

### Tests fail with OpenAI API errors
**Symptom**: "Invalid API key" or rate limit errors

**Solution**:
1. Set `OPENAI_API_KEY` in `.env`
2. Check API key is valid and has credits
3. Tests use mock audio, so local STT/TTS should work without API calls in most cases

### Audio file format errors
**Symptom**: "Invalid file format" from OpenAI API

**Solution**: The service detects invalid test audio and returns mock responses automatically. Real audio files should have proper headers (RIFF/WAVE, etc.).

## Performance Expectations

### Local (Faster-Whisper + Kokoro)
- STT: ~300ms for 3-second audio
- TTS: ~500ms for 100 characters
- **Total**: <1 second for typical voice interaction

### Cloud Fallback (OpenAI)
- STT: ~800ms for 3-second audio
- TTS: ~500ms for 100 characters
- **Total**: ~1.5 seconds for typical voice interaction

## Next Steps

- [ ] Frontend integration (useVoiceRecorder hook)
- [ ] VoiceButton component
- [ ] AudioPlayer component
- [ ] SSE streaming for real-time chat responses
- [ ] Voice activity detection for better UX
