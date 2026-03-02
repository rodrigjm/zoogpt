# Zoocari Voice Upgrade Plan

> Research completed: January 2025
> Current stack: OpenAI Whisper API (STT) + Kokoro-82M (TTS)

---

## Known Blocker: HTTPS Required for Production STT

> **CRITICAL**: Voice recording (STT) does not work over the internet without HTTPS.
> Browsers require a secure context for `getUserMedia()` API access.

| Environment | STT Works? | Reason |
|-------------|------------|--------|
| `localhost` | ✅ Yes | Localhost is trusted |
| `http://` (remote) | ❌ No | Insecure context |
| `https://` (remote) | ✅ Yes | Secure context |

**Solutions for Production:**

| Option | Complexity | Cost | Notes |
|--------|------------|------|-------|
| **Cloudflare Tunnel** | Easy | Free | No ports, auto-HTTPS |
| **Streamlit Cloud** | Easy | Free | Built-in HTTPS |
| **ngrok** | Easy | Free/Paid | Testing only |
| **Nginx + Let's Encrypt** | Medium | Free | Self-hosted production |
| **AWS ALB / GCP LB** | Medium | $$ | Cloud production |

See [VOICE_ROADMAP.md - Phase 5](./VOICE_ROADMAP.md) for deployment details.

---

## Executive Summary

This plan outlines options to upgrade Zoocari's voice capabilities with open-source, low-latency alternatives that reduce API costs and improve response times.

---

## Current Architecture

```
[User Voice] → [OpenAI Whisper API] → [Text Query]
                    ↓
              [LanceDB Search] → [OpenAI Chat] → [Response Text]
                    ↓
[Audio Output] ← [Kokoro TTS] ← [Text Response]
                  ↓ (fallback)
              [ElevenLabs] → [OpenAI TTS]
```

**Current Latencies:**
| Component | Latency | Cost |
|-----------|---------|------|
| STT (Whisper API) | ~800-1000ms | $0.006/min |
| TTS (Kokoro local) | ~100ms | Free |
| TTS (ElevenLabs fallback) | ~500-2000ms | $0.30/1K chars |
| TTS (OpenAI fallback) | ~300-800ms | $0.015/1K chars |

---

## Upgrade Options

### Option A: Local STT Only (Recommended - Quick Win)

**Replace OpenAI Whisper API with Faster-Whisper**

| Metric | Before | After |
|--------|--------|-------|
| STT Latency | ~800ms | ~300ms |
| STT Cost | $0.006/min | Free |
| Offline Capable | No | Yes |
| Implementation | - | 1-2 hours |

**Installation:**
```bash
pip install faster-whisper
```

**Code Changes (zoo_chat.py):**
```python
from faster_whisper import WhisperModel

# Initialize once at startup
_stt_model = None

def get_stt_model():
    global _stt_model
    if _stt_model is None:
        _stt_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _stt_model

def transcribe_audio_local(audio_bytes: bytes) -> str:
    """Local STT using Faster-Whisper - no API calls."""
    import tempfile
    import os

    # Write audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        model = get_stt_model()
        segments, _ = model.transcribe(temp_path, language="en")
        return " ".join([seg.text for seg in segments])
    finally:
        os.unlink(temp_path)

def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe with local-first, API fallback."""
    try:
        return transcribe_audio_local(audio_bytes)
    except Exception as e:
        log("STT", f"Local STT failed: {e}, falling back to API", "WARNING")
        # Existing OpenAI API code as fallback
        return transcribe_audio_openai(audio_bytes)
```

**Pros:**
- 60% faster transcription
- Zero ongoing STT costs
- Works offline
- Minimal code changes

**Cons:**
- Slightly larger Docker image (~500MB for model)
- CPU-intensive (consider GPU for high volume)

---

### Option B: Full Local Stack (Faster-Whisper + Orpheus TTS)

**Replace both STT and TTS with local models**

| Metric | Before | After |
|--------|--------|-------|
| STT Latency | ~800ms | ~300ms |
| TTS Latency | ~100ms | ~200ms |
| Total Round-trip | ~900ms | ~500ms |
| API Costs | ~$0.02/interaction | Free |
| Voice Quality | Good | Excellent (emotion control) |

**Installation:**
```bash
pip install faster-whisper orpheus-speech
# or for HuggingFace direct:
pip install transformers torch torchaudio snac
```

**New TTS Integration:**
```python
# tts_orpheus.py
from orpheus import OrpheusModel

_orpheus_model = None

def get_orpheus_model():
    global _orpheus_model
    if _orpheus_model is None:
        _orpheus_model = OrpheusModel("canopylabs/orpheus-3b-0.1-ft")
    return _orpheus_model

def generate_speech_orpheus(text: str, emotion: str = "friendly") -> bytes:
    """Generate speech with emotion control."""
    model = get_orpheus_model()

    # Wrap text with emotion tags for Zoocari's personality
    if emotion == "excited":
        tagged_text = f"<excited>{text}</excited>"
    elif emotion == "curious":
        tagged_text = f"<curious>{text}</curious>"
    else:
        tagged_text = text

    audio = model.generate(tagged_text)
    return audio.to_bytes()
```

**Pros:**
- Human-level speech quality
- Emotion control (excited, curious, happy)
- Zero API costs
- Full offline capability
- Voice cloning possible

**Cons:**
- Requires GPU for best performance (3B model)
- Larger Docker image (~3GB)
- More complex setup
- Slightly higher TTS latency than Kokoro

---

### Option C: Enhanced Kokoro + Local STT (Balanced)

**Keep Kokoro TTS, add Faster-Whisper STT**

| Metric | Before | After |
|--------|--------|-------|
| STT Latency | ~800ms | ~300ms |
| TTS Latency | ~100ms | ~100ms |
| Offline STT | No | Yes |
| Offline TTS | Yes | Yes |

This is essentially Option A - minimal changes, maximum benefit.

---

### Option D: Streaming Architecture (Future)

**Full streaming with WebSockets**

```
[Mic Stream] → [WhisperLiveKit] → [Streaming Text]
                     ↓
              [LLM Streaming] → [Token Stream]
                     ↓
[Audio Stream] ← [Marvis TTS] ← [Token-by-Token]
```

**Components:**
- **WhisperLiveKit**: Real-time streaming STT with VAD
- **Marvis TTS**: Streams audio as text is generated

**Benefits:**
- Sub-100ms perceived latency
- Audio starts before response completes
- True conversational feel

**Requirements:**
- WebSocket infrastructure
- Significant refactoring
- GPU recommended

---

## Comparison Matrix

| Option | STT | TTS | Latency | Cost | Effort | Offline |
|--------|-----|-----|---------|------|--------|---------|
| Current | Whisper API | Kokoro | 900ms | $$ | - | Partial |
| **A (Recommended)** | Faster-Whisper | Kokoro | 400ms | Free | Low | Yes |
| B | Faster-Whisper | Orpheus | 500ms | Free | Medium | Yes |
| C | Faster-Whisper | Kokoro | 400ms | Free | Low | Yes |
| D (Future) | WhisperLiveKit | Marvis | <100ms | Free | High | Yes |

---

## Implementation Roadmap

### Phase 1: Quick Win (1-2 hours) ✅ COMPLETED
- [x] Add `faster-whisper` to requirements.txt
- [x] Implement `transcribe_audio_local()` function
- [x] Add fallback logic to existing `transcribe_audio()`
- [x] Update Dockerfile for model caching
- [ ] Test locally

### Phase 2: Optimization (2-4 hours)
- [ ] Add model warmup to `entrypoint.sh`
- [ ] Implement STT result caching for repeated queries
- [ ] Add metrics/logging for latency comparison
- [ ] Load test with concurrent users

### Phase 3: Enhanced TTS (Optional, 4-8 hours)
- [ ] Evaluate Orpheus vs Chatterbox for kid-friendly voices
- [ ] Implement emotion detection from LLM response
- [ ] Add emotion tags to TTS generation
- [ ] Create voice persona for Zoocari

### Phase 4: Streaming (Future)
- [ ] Evaluate WebSocket infrastructure needs
- [ ] Prototype WhisperLiveKit integration
- [ ] Prototype streaming TTS
- [ ] Full streaming pipeline

---

## Requirements.txt Updates

```txt
# Current
kokoro>=0.9.4
soundfile

# Add for Option A/B/C
faster-whisper>=1.0.0

# Add for Option B (Orpheus TTS)
orpheus-speech>=0.1.0
# or direct HuggingFace:
# snac
# bitsandbytes

# Add for Option D (Streaming)
# whisperlivekit>=0.1.0
```

---

## Dockerfile Updates

```dockerfile
# Add after current COPY commands:

# Pre-download Faster-Whisper model (reduces cold start)
RUN python -c "\
from faster_whisper import WhisperModel; \
print('Pre-loading Faster-Whisper model...'); \
m = WhisperModel('base', device='cpu', compute_type='int8'); \
print('Faster-Whisper model cached!')" || echo "Model pre-load skipped"
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Model accuracy differs from API | Low | Medium | Test with real kid queries |
| Docker image too large | Medium | Low | Use model quantization |
| CPU performance issues | Medium | Medium | Add GPU support option |
| Orpheus requires GPU | High | Medium | Keep Kokoro as fallback |

---

## Decision

**Recommended: Option A (Local STT Only)**

Reasons:
1. Lowest implementation effort
2. Highest ROI (60% faster, zero cost)
3. Preserves working Kokoro TTS
4. Easy rollback if issues

**Next Step:** Implement Phase 1 to add Faster-Whisper with API fallback.

---

## References

- [Faster-Whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [WhisperLiveKit PyPI](https://pypi.org/project/whisperlivekit/)
- [Orpheus TTS GitHub](https://github.com/canopyai/Orpheus-TTS)
- [Marvis TTS HuggingFace](https://huggingface.co/blog/prince-canuma/introducing-marvis-tts)
- [Modal: Open Source STT Models](https://modal.com/blog/open-source-stt)
- [BentoML: Open Source TTS Models](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
