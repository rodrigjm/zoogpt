# TTS Latency Optimization Research Report

**Date:** 2026-01-16  
**Scope:** Reduce TTS latency and implement streaming architecture for Zoocari voice chatbot

---

## Current Implementation Analysis

### Architecture
- **Primary:** Kokoro (local) - 82M parameter model
- **Fallback:** OpenAI TTS API (cloud)
- **Existing streaming:** `/voice/tts/stream` endpoint does sentence-by-sentence streaming

### Current Flow
1. RAG generates full response
2. Text split into sentences
3. Each sentence synthesized via `synthesize_kokoro()`
4. Audio chunks sent via SSE as base64

### Bottlenecks Identified
1. **Per-sentence synthesis latency:** Each sentence requires full model inference
2. **Sequential processing:** Sentences processed one at a time
3. **No sub-sentence streaming:** Must wait for complete sentence before TTS
4. **NumPy concatenation overhead:** `np.concatenate(all_audio)` for chunked text

---

## Optimization Recommendations

### Tier 1: Quick Wins (1-2 days implementation)

#### 1.1 Switch to Kokoro-ONNX Runtime
**Impact:** 2-3x faster inference  
**Effort:** Low

Replace the PyTorch-based `kokoro` package with `kokoro-onnx`:
```python
from kokoro_onnx import Kokoro
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
samples, sr = kokoro.create(text, voice="af_heart", speed=1.0)
```

**Benefits:**
- ONNX Runtime optimized for inference
- Supports INT8 quantization (additional 2x speedup)
- Same quality, faster execution
- CPU inference: 3-11x real-time
- GPU inference: 90-210x real-time

#### 1.2 Reduce Chunk Size
**Impact:** Lower time-to-first-audio  
**Effort:** Very Low

Current: `max_chars=800`  
Recommended: `max_chars=200-400` with phrase-level splitting

```python
# Split on phrases, not just sentences
PHRASE_ENDINGS = re.compile(r'[.!?,;:]+(?:\s|$)')
```

#### 1.3 Parallel Sentence Processing
**Impact:** 30-50% total latency reduction  
**Effort:** Medium

Use async/await with thread pool for concurrent TTS:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=3)

async def synthesize_parallel(sentences):
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(executor, synthesize_sentence, s)
        for s in sentences[:3]  # Process up to 3 ahead
    ]
    return await asyncio.gather(*tasks)
```

---

### Tier 2: Streaming Architecture (3-5 days)

#### 2.1 Use Kokoro-FastAPI as TTS Backend
**Impact:** 100-300ms latency, native streaming  
**Effort:** Medium

Deploy [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) as a sidecar service:

```yaml
# docker-compose.yml addition
kokoro-tts:
  image: ghcr.io/remsky/kokoro-fastapi-cpu:latest
  ports:
    - "8880:8880"
  environment:
    - TARGET_MIN_TOKENS=100
    - TARGET_MAX_TOKENS=200
```

**OpenAI-compatible streaming endpoint:**
```python
from openai import OpenAI

client = OpenAI(base_url="http://kokoro-tts:8880/v1", api_key="not-needed")

with client.audio.speech.with_streaming_response.create(
    model="kokoro",
    voice="af_heart",
    response_format="pcm",
    input=sentence
) as response:
    for chunk in response.iter_bytes(chunk_size=1024):
        yield chunk  # Stream directly to client
```

#### 2.2 Use RealtimeTTS Library
**Impact:** Automatic streaming, multiple engine fallback  
**Effort:** Medium

[RealtimeTTS](https://github.com/KoljaB/RealtimeTTS) provides built-in streaming:

```python
from RealtimeTTS import TextToAudioStream, KokoroEngine

engine = KokoroEngine(voice="af_heart")
stream = TextToAudioStream(engine)

# Feed text as it arrives from LLM
stream.feed("Hello ")
stream.feed("world!")
stream.play()  # Plays as audio is generated
```

**Note:** Project maintenance is limited as of 2024.

#### 2.3 True Sub-Sentence Streaming
**Impact:** Minimal time-to-first-audio  
**Effort:** High

Implement word-level or phoneme-level streaming using:
- Kokoro's word-timing callbacks
- Progressive audio buffer flushing

```python
# Conceptual - requires model-level changes
def on_word_audio(word, audio_chunk):
    websocket.send_binary(audio_chunk)
```

---

### Tier 3: Alternative TTS Providers (if local isn't fast enough)

#### 3.1 Cartesia Sonic
**Latency:** 40ms TTFB, <100ms total  
**Quality:** High  
**Cost:** ~$0.015/1000 chars

Best-in-class for real-time voice AI. WebSocket-first architecture.

```python
import cartesia

client = cartesia.Cartesia(api_key="...")
ws = client.tts.websocket()

# Start connection before first TTS request
ws.connect()

# Near-instant streaming
for chunk in ws.send(text=sentence, voice="...", stream=True):
    yield chunk
```

#### 3.2 Deepgram Aura
**Latency:** ~300ms TTFB, 3x faster than ElevenLabs  
**Quality:** Good  
**Cost:** $0.0135/1000 chars

WebSocket streaming with 70% latency reduction vs REST:

```python
# WebSocket streaming
async with websockets.connect("wss://api.deepgram.com/v1/speak") as ws:
    await ws.send(json.dumps({"text": sentence}))
    async for chunk in ws:
        yield chunk
```

#### 3.3 ElevenLabs Flash v2.5
**Latency:** ~75ms inference  
**Quality:** Highest  
**Cost:** $0.18/1000 chars (expensive)

Best quality but highest cost. Use only if quality is paramount.

---

## Recommended Implementation Plan

### Phase 1: Immediate Optimizations (This Week)
1. **Replace kokoro with kokoro-onnx** - Fastest win
2. **Reduce chunk size to 300 chars** - Lower TTFA
3. **Add sentence prefetching** - Process next sentence while current plays

### Phase 2: Streaming Backend (Next Sprint)
1. **Deploy Kokoro-FastAPI** as sidecar service
2. **Update `/voice/tts/stream`** to use streaming endpoint
3. **Implement WebSocket audio delivery** instead of SSE/base64

### Phase 3: Advanced (Future)
1. **Add Cartesia as premium option** for lowest latency
2. **Implement adaptive quality** - Cartesia for short, Kokoro for long
3. **Consider speech-to-speech models** (e.g., Moshi) for <200ms total

---

## Latency Comparison Table

| Solution | TTFB | Total Latency | Quality | Cost |
|----------|------|---------------|---------|------|
| **Current (Kokoro PyTorch)** | ~500ms | ~800ms | High | Free |
| Kokoro-ONNX | ~200ms | ~400ms | High | Free |
| Kokoro-FastAPI (streaming) | ~150ms | ~300ms | High | Free |
| Cartesia Sonic | 40ms | 90ms | High | $0.015/1K |
| Deepgram Aura | ~300ms | ~400ms | Good | $0.0135/1K |
| OpenAI TTS | ~600ms | ~900ms | High | $0.015/1K |

---

## Implementation Code Snippets

### Quick Win: Kokoro-ONNX Replacement

```python
# apps/api/app/services/tts.py

from kokoro_onnx import Kokoro
import io
import soundfile as sf

_kokoro: Optional[Kokoro] = None

def get_kokoro() -> Kokoro:
    global _kokoro
    if _kokoro is None:
        _kokoro = Kokoro(
            "models/kokoro-v1.0.onnx",
            "models/voices-v1.0.bin"
        )
    return _kokoro

def synthesize_kokoro(text: str, voice: str = "af_heart") -> bytes:
    kokoro = get_kokoro()
    samples, sr = kokoro.create(text, voice=voice, speed=1.0)
    
    buffer = io.BytesIO()
    sf.write(buffer, samples, sr, format='WAV')
    buffer.seek(0)
    return buffer.read()
```

### Streaming with Kokoro-FastAPI

```python
# apps/api/app/services/tts_streaming.py

import httpx
from typing import AsyncIterator

KOKORO_URL = "http://kokoro-tts:8880/v1/audio/speech"

async def stream_tts(text: str, voice: str = "af_heart") -> AsyncIterator[bytes]:
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            KOKORO_URL,
            json={
                "input": text,
                "voice": voice,
                "model": "kokoro",
                "response_format": "pcm"
            }
        ) as response:
            async for chunk in response.aiter_bytes(chunk_size=1024):
                yield chunk
```

### WebSocket Audio Delivery (Frontend)

```typescript
// apps/web/src/hooks/useTTSStream.ts

const useTTSStream = () => {
  const audioContext = new AudioContext({ sampleRate: 24000 });
  const audioQueue: AudioBuffer[] = [];
  
  const playChunk = async (pcmData: ArrayBuffer) => {
    const samples = new Float32Array(pcmData);
    const buffer = audioContext.createBuffer(1, samples.length, 24000);
    buffer.getChannelData(0).set(samples);
    
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);
    source.start();
  };
  
  return { playChunk };
};
```

---

## Sources

- [ElevenLabs Latency Optimization](https://elevenlabs.io/docs/developers/best-practices/latency-optimization)
- [Deepgram TTS Latency](https://developers.deepgram.com/docs/text-to-speech-latency)
- [RealtimeTTS GitHub](https://github.com/KoljaB/RealtimeTTS)
- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)
- [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)
- [Cartesia Sonic](https://cartesia.ai/sonic)
- [Deepgram Aura WebSocket](https://deepgram.com/learn/aura-text-to-speech-adds-websocket-support-for-input-streaming)
- [Inferless TTS Comparison](https://www.inferless.com/learn/comparing-different-text-to-speech---tts--models-part-2)
- [Layercode TTS Guide 2025](https://layercode.com/blog/tts-voice-ai-model-guide)
