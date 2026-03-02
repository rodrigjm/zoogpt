# TTS Latency Optimization Implementation

**Date:** 2026-01-16
**Objective:** Reduce TTS latency from ~500ms to ~150ms TTFB
**Status:** Phase 1 Complete (Kokoro-ONNX + Parallel Processing + WebSocket)

---

## Implementation Summary

This implementation follows the Phase 1 recommendations from `docs/research_tts_latency_optimization.md` to achieve immediate latency improvements while maintaining quality.

### Changes Made

#### 1. Requirements Update (`apps/api/requirements.txt`)
- Replaced `kokoro>=0.9.4` with `kokoro-onnx>=0.4.0`
- Added `onnxruntime>=1.17.0`
- Updated `httpx>=0.27.0` (from 0.26.0)

**Expected Impact:** 2-3x faster TTS inference via ONNX Runtime optimizations

#### 2. Configuration Updates (`apps/api/app/config.py`)
Added new TTS configuration parameters:
- `kokoro_tts_url: str = "http://kokoro-tts:8880"` - Kokoro-FastAPI sidecar URL
- `tts_streaming_enabled: bool = True` - Enable streaming TTS
- `tts_chunk_size: int = 300` - Reduced from 800 for lower TTFA
- `tts_max_workers: int = 3` - Parallel processing workers

#### 3. TTS Service Refactor (`apps/api/app/services/tts.py`)
**Breaking Changes:**
- Renamed `get_kokoro_pipeline()` → `get_kokoro_instance()`
- Renamed `preload_kokoro_pipeline()` → `preload_kokoro_instance()`
- Renamed `_kokoro_pipeline` → `_kokoro_instance`

**API Changes:**
- Updated `synthesize_kokoro()` to use kokoro-onnx API:
  - Old: `pipeline(text, voice, speed)` returns generator
  - New: `kokoro.create(text, voice, speed)` returns `(samples, sr)`
- Reduced default `chunk_text()` max_chars from 800 → 300
- Reduced chunking threshold from 800 → 300 chars

**Compatibility:**
- OpenAI TTS fallback remains unchanged
- Voice presets remain unchanged
- Return format (WAV bytes) remains unchanged

#### 4. New Streaming Service (`apps/api/app/services/tts_streaming.py`)
Created new service for Kokoro-FastAPI sidecar integration:

**Functions:**
- `stream_tts_audio()` - Direct streaming from Kokoro-FastAPI
- `stream_tts_with_fallback()` - Streaming with local fallback

**Features:**
- Async streaming via httpx
- Automatic fallback to local Kokoro-ONNX
- PCM audio format (lowest latency)
- Configurable chunk size (default: 4096 bytes)

#### 5. Voice Router Updates (`apps/api/app/routers/voice.py`)
**New Imports:**
- `asyncio` - For parallel processing
- `ThreadPoolExecutor` - For CPU-bound TTS tasks
- `WebSocket`, `WebSocketDisconnect` - For WebSocket endpoint

**New Infrastructure:**
- `_tts_executor` - Thread pool with configurable workers

**New Endpoint:**
- `@router.websocket("/tts/ws")` - WebSocket TTS endpoint

**WebSocket Protocol:**
```
Client → Server: {"text": "...", "voice": "...", "speed": 1.0, "use_streaming": true}
Server → Client: Binary audio chunks (PCM 24kHz)
Server → Client: {"done": true, "chunks": N}
```

**Features:**
- Native binary streaming (no base64 encoding)
- Parallel sentence processing (configurable workers)
- Dual mode: Kokoro-FastAPI streaming OR local parallel processing
- Persistent connection for multiple requests
- Graceful error handling with JSON error messages

#### 6. Startup Hook Update (`apps/api/app/main.py`)
- Updated import: `preload_kokoro_pipeline` → `preload_kokoro_instance`
- Updated call in `lifespan()` function

#### 7. Tests (`apps/api/tests/test_tts_websocket.py`)
Created basic WebSocket endpoint tests:
- Connection establishment
- Empty text validation
- Multiple sequential requests

---

## Performance Improvements

### Expected Latency Reductions

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| TTFB | ~500ms | ~150-200ms | 60-70% faster |
| Total Latency | ~800ms | ~300-400ms | 50-60% faster |
| Chunk Size | 800 chars | 300 chars | Lower TTFA |

### Optimization Techniques Applied

1. **ONNX Runtime** - 2-3x faster inference vs PyTorch
2. **Reduced Chunking** - 300 vs 800 chars = faster first audio
3. **Parallel Processing** - Up to 3 sentences processed simultaneously
4. **Binary Streaming** - WebSocket eliminates base64 overhead (~33% smaller)
5. **Persistent Connections** - WebSocket reduces connection overhead

---

## Migration Guide

### For Existing Code

The changes are **mostly backward compatible**. The following scenarios work without changes:

#### REST Endpoints (No Changes Required)
- `POST /voice/tts` - Still works (uses updated kokoro-onnx internally)
- `POST /voice/tts/stream` - Still works (SSE-based streaming)
- `POST /voice/stt` - Unchanged

#### Service Usage (Internal)
If you're using `TTSService` directly:
```python
# Still works - API unchanged
tts_service = TTSService(openai_api_key="...")
audio = tts_service.synthesize(text="Hello", voice="af_heart")
```

### Breaking Changes

Only affects code that directly imported internal functions:

```python
# OLD (breaks)
from app.services.tts import preload_kokoro_pipeline
preload_kokoro_pipeline()

# NEW (required)
from app.services.tts import preload_kokoro_instance
preload_kokoro_instance()
```

### New Features to Adopt

#### Using WebSocket TTS (Recommended)

**Frontend Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/voice/tts/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    text: "Hello, this is a test",
    voice: "af_heart",
    speed: 1.0,
    use_streaming: true  // Use Kokoro-FastAPI sidecar
  }));
};

ws.onmessage = (event) => {
  if (event.data instanceof Blob) {
    // Binary audio chunk - play immediately
    playAudioChunk(event.data);
  } else {
    // JSON message
    const data = JSON.parse(event.data);
    if (data.done) {
      console.log(`TTS complete: ${data.chunks} chunks`);
    } else if (data.error) {
      console.error(`TTS error: ${data.message}`);
    }
  }
};
```

---

## Deployment Requirements

### Without Kokoro-FastAPI Sidecar (Local Mode Only)

**Requirements:**
- `kokoro-onnx>=0.4.0`
- `onnxruntime>=1.17.0`
- Model files (auto-downloaded on first use)

**Setup:**
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Configuration:**
```env
TTS_STREAMING_ENABLED=false  # Disables sidecar, uses local parallel processing
TTS_MAX_WORKERS=3            # Parallel sentence processing
TTS_CHUNK_SIZE=300           # Characters per chunk
```

### With Kokoro-FastAPI Sidecar (Full Streaming)

**Additional Requirements:**
- Docker/Podman for sidecar container
- `ghcr.io/remsky/kokoro-fastapi-cpu:latest` image

**Setup:**
```bash
# Start Kokoro-FastAPI sidecar
docker run -d \
  -p 8880:8880 \
  --name kokoro-tts \
  ghcr.io/remsky/kokoro-fastapi-cpu:latest

# Start API
cd apps/api
uvicorn app.main:app --reload
```

**Configuration:**
```env
TTS_STREAMING_ENABLED=true
KOKORO_TTS_URL=http://localhost:8880  # Or http://kokoro-tts:8880 in Docker network
TTS_MAX_WORKERS=3
TTS_CHUNK_SIZE=300
```

### Docker Compose Example

```yaml
services:
  kokoro-tts:
    image: ghcr.io/remsky/kokoro-fastapi-cpu:latest
    ports:
      - "8880:8880"
    environment:
      - TARGET_MIN_TOKENS=100
      - TARGET_MAX_TOKENS=200

  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    environment:
      - KOKORO_TTS_URL=http://kokoro-tts:8880
      - TTS_STREAMING_ENABLED=true
    depends_on:
      - kokoro-tts
```

---

## Testing & Verification

### 1. Verify Installation

```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/api

# Install dependencies
pip install -r requirements.txt

# Verify syntax
python3 -m py_compile app/services/tts.py app/services/tts_streaming.py
```

### 2. Run Tests

```bash
# Run all tests
pytest tests/

# Run TTS-specific tests
pytest tests/test_tts_websocket.py -v

# Run voice endpoint tests
pytest tests/test_voice_endpoints.py -v
```

### 3. Manual Testing

#### Test Local TTS
```bash
# Start server
uvicorn app.main:app --reload

# In another terminal - test REST endpoint
curl -X POST http://localhost:8000/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "text": "Hello world", "voice": "af_heart"}' \
  --output test.wav

# Play audio
ffplay test.wav
```

#### Test WebSocket TTS
```python
import asyncio
import websockets
import json

async def test_ws():
    async with websockets.connect('ws://localhost:8000/voice/tts/ws') as ws:
        await ws.send(json.dumps({
            "text": "Testing WebSocket TTS",
            "voice": "af_heart",
            "use_streaming": False
        }))

        chunks = 0
        async for message in ws:
            if isinstance(message, bytes):
                chunks += 1
                print(f"Received audio chunk {chunks}: {len(message)} bytes")
            else:
                data = json.loads(message)
                print(f"Received message: {data}")
                if data.get("done"):
                    break

asyncio.run(test_ws())
```

### 4. Performance Benchmarking

```python
import time
from app.services.tts import TTSService
from app.config import settings

tts = TTSService(openai_api_key=settings.openai_api_key)
text = "The elephant is the largest land animal in the world."

# Benchmark
start = time.perf_counter()
audio = tts.synthesize_kokoro(text, voice="af_heart")
duration = (time.perf_counter() - start) * 1000

print(f"TTS latency: {duration:.0f}ms")
print(f"Audio size: {len(audio)} bytes")
print(f"Target: <200ms TTFB")
```

---

## Troubleshooting

### kokoro-onnx Import Error

**Error:** `ModuleNotFoundError: No module named 'kokoro_onnx'`

**Solution:**
```bash
pip install kokoro-onnx>=0.4.0 onnxruntime>=1.17.0
```

### Model Download Issues

**Error:** `Failed to download model files`

**Solution:**
```bash
# Pre-download models
python3 -c "from kokoro_onnx import Kokoro; Kokoro()"
```

### WebSocket Connection Refused

**Error:** `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution:**
```bash
# Ensure FastAPI server is running
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8000/voice/tts/ws
```

### Kokoro-FastAPI Sidecar Not Responding

**Error:** `httpx.ConnectError: [Errno 61] Connection refused`

**Solution:**
```bash
# Check sidecar is running
docker ps | grep kokoro-tts

# Check logs
docker logs kokoro-tts

# Restart sidecar
docker restart kokoro-tts

# Verify endpoint
curl http://localhost:8880/health
```

### Parallel Processing Not Working

**Symptom:** No performance improvement with parallel processing

**Solution:**
```bash
# Increase workers
export TTS_MAX_WORKERS=5

# Check CPU usage during TTS
top -pid $(pgrep -f "uvicorn app.main")
```

---

## Next Steps (Phase 2)

For further latency improvements, consider:

1. **Deploy Kokoro-FastAPI in production** - Requires Docker setup
2. **Implement sub-sentence streaming** - Stream audio during word generation
3. **Add GPU support** - 90-210x real-time speed (vs 3-11x on CPU)
4. **Consider Cartesia Sonic** - 40ms TTFB (paid service)
5. **Optimize audio format** - Consider Opus for smaller payloads

See `docs/research_tts_latency_optimization.md` for detailed recommendations.

---

## Files Changed

### Modified Files
- `/apps/api/requirements.txt` - Updated TTS dependencies
- `/apps/api/app/config.py` - Added TTS configuration
- `/apps/api/app/services/tts.py` - Refactored for kokoro-onnx
- `/apps/api/app/routers/voice.py` - Added WebSocket + parallel processing
- `/apps/api/app/main.py` - Updated function name

### New Files
- `/apps/api/app/services/tts_streaming.py` - Streaming TTS service
- `/apps/api/tests/test_tts_websocket.py` - WebSocket tests
- `/docs/integration/TTS_OPTIMIZATION_IMPLEMENTATION.md` - This document

### Verification Command
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/api && \
  python3 -m py_compile app/services/tts.py app/services/tts_streaming.py app/routers/voice.py && \
  pytest tests/test_tts_websocket.py -v
```

---

## References

- Research Document: `/docs/research_tts_latency_optimization.md`
- kokoro-onnx: https://github.com/thewh1teagle/kokoro-onnx
- Kokoro-FastAPI: https://github.com/remsky/Kokoro-FastAPI
- Contract: `/docs/integration/CONTRACT.md`
