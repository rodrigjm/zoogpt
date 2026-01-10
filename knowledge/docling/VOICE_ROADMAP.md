# Voice Feature Project Plan: Zoocari Voice Mode

## ⚠️ Production Blocker: HTTPS Required for STT

> **Voice STT does NOT work over the internet without HTTPS.**
> Browser security requires secure context for microphone access (`getUserMedia()`).

| Environment | Voice Input | Notes |
|-------------|-------------|-------|
| `localhost:8501` | ✅ Works | Localhost is trusted |
| `http://10.0.0.x:8501` | ❌ Blocked | Insecure context |
| `https://zoocari.example.com` | ✅ Works | Secure context |

**Priority**: Resolve in Phase 5 before production deployment.

---

## Current Status: Kokoro Local TTS Integration

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Audio Input Integration |
| Phase 2 | ✅ Complete | Text-to-Speech Output (ElevenLabs) |
| Phase 2.5 | ✅ Complete | **Kokoro Local TTS** (latency optimization) |
| Phase 3 | ✅ Complete | UI/UX Enhancements |
| Phase 4 | ⏳ Pending | Integration & Polish |
| Phase 5 | ⏳ Pending | HTTPS Deployment (Mobile Support) |
| **Phase 6** | 🟡 **NEW** | **Local STT + Enhanced TTS Options** |

> **NEW**: See [VOICE_UPGRADE_PLAN.md](./VOICE_UPGRADE_PLAN.md) for detailed research on open-source STT/TTS alternatives.

---

## Architecture Overview: Chained Voice Pipeline

```
User Audio → [Whisper STT] → Text → [GPT-4o-mini] → Response → [TTS] → Audio
     ↓            ↓                      ↓                       ↓
st.audio_input  OpenAI API      Existing chat logic      Tiered Fallback:
                                                         1. Kokoro (local)
                                                         2. ElevenLabs (cloud)
                                                         3. OpenAI (cloud)
```

**Why chained architecture:**
- High control and transparency (full transcript available)
- Robust function calling support
- Reliable, predictable responses
- Ideal for structured workflows like kid-friendly Q&A

---

## Phase 2.5: Kokoro Local TTS 🟡 IN PROGRESS

**Goal**: Replace cloud TTS with local inference for reduced latency

### Latency Comparison
| Provider | Latency | Cost | Network |
|----------|---------|------|---------|
| **Kokoro (local)** | 50-200ms | Free | No |
| ElevenLabs | 500-2000ms | ~$0.30/1K chars | Yes |
| OpenAI TTS | 300-800ms | ~$0.015/1K chars | Yes |

### Implementation Tasks
| Task | Status | Description |
|------|--------|-------------|
| 2.5.1 | ✅ | Add `kokoro`, `soundfile` to requirements.txt |
| 2.5.2 | ✅ | Create `tts_kokoro.py` module |
| 2.5.3 | ✅ | Implement tiered fallback in `generate_speech()` |
| 2.5.4 | ⏳ | Install espeak-ng system dependency |
| 2.5.5 | ⏳ | Test local inference |
| 2.5.6 | ⏳ | Add voice selection UI |

### Kokoro Voice Options (Kid-Friendly)
| Voice | ID | Description |
|-------|-----|-------------|
| Bella | `af_bella` | Friendly female (default) |
| Nova | `af_nova` | Warm, engaging female |
| Heart | `af_heart` | Expressive, upbeat female |
| Adam | `am_adam` | Clear male voice |

### System Requirements
```bash
# macOS
brew install espeak-ng

# Ubuntu/Debian
apt-get install espeak-ng
```

### New Files
- `tts_kokoro.py` - Local Kokoro TTS inference module

---

## Phased Project Roadmap

---

### Phase 1: Audio Input Integration ✅ COMPLETE
**Goal**: Enable voice recording from the user

| Task | Status | Description |
|------|--------|-------------|
| 1.1 | ✅ | Add `st.audio_input` widget for voice recording |
| 1.2 | ✅ | Create `transcribe_audio()` function using Whisper |
| 1.3 | ✅ | Add voice mode toggle in left panel |
| 1.4 | ✅ | Handle audio file format (wav via BytesIO) |
| 1.5 | ✅ | Update session state for voice input mode |

**Implementation**:
```python
def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert audio to text using OpenAI's Whisper API."""
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "recording.wav"
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en",
    )
    return transcription.text
```

---

### Phase 2: Text-to-Speech Output ✅ COMPLETE
**Goal**: Generate audio responses alongside text streaming

| Task | Status | Description |
|------|--------|-------------|
| 2.1 | ✅ | Create `generate_speech()` with ElevenLabs API |
| 2.2 | ✅ | Generate audio after text response completes |
| 2.3 | ✅ | Display audio player using `st.audio()` |
| 2.4 | ✅ | ElevenLabs voices (Rachel default) with OpenAI fallback |
| 2.5 | ✅ | Store audio in session state for replay |

**Implementation** (ElevenLabs with OpenAI fallback):
```python
def generate_speech(text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> bytes:
    """Convert text to speech using ElevenLabs (with OpenAI fallback)."""
    clean_text = # ... remove markdown ...

    if elevenlabs_client:
        audio = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            text=clean_text[:5000],
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        return b"".join(audio)

    # Fallback to OpenAI TTS
    with client.audio.speech.with_streaming_response.create(...) as response:
        return response.read()
```

**ElevenLabs Voice Options**:
| Voice | ID | Description |
|-------|-----|-------------|
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Warm, friendly (default) |
| Bella | `EXAVITQu4vr4xnSDxMaL` | Young, energetic |
| Josh | `TxGEqnHWrfWFTfGW9XjX` | Friendly male |

---

### Phase 3: UI/UX Enhancements ✅ COMPLETE
**Goal**: Seamless voice interaction experience

| Task | Status | Description |
|------|--------|-------------|
| 3.1 | ✅ | Voice mode toggle button |
| 3.2 | ✅ | Visual recording indicator (pulse animation) |
| 3.3 | ✅ | Style audio player to match Leesburg branding |
| 3.4 | ✅ | Call-to-action voice button design |
| 3.5 | ❌ | Mobile voice recording (requires HTTPS) |
| 3.6 | ✅ | Auto-play TTS in voice mode |

**Blocker**: Mobile voice recording requires HTTPS (see Phase 5)

**Implementation Details**:
- Pulse animation on recording indicator with orange glow effect
- Voice mode status badge shows "Voice Active" / "Text Mode"
- Styled audio player with Leesburg brown/yellow gradient
- Voice panel with clear CTA and recording hints

---

### Phase 4: Integration & Polish ⏳ PENDING
**Goal**: Production-ready voice features

| Task | Status | Description |
|------|--------|-------------|
| 4.1 | ⏳ | Error handling for audio recording failures |
| 4.2 | ⏳ | Loading states during transcription/TTS |
| 4.3 | ✅ | Fallback to text when voice unavailable |
| 4.4 | ⏳ | Voice-friendly response formatting |
| 4.5 | ⏳ | Voice selection UI for users |
| 4.6 | ✅ | Update requirements.txt (elevenlabs added) |

---

### Phase 5: HTTPS Deployment ⏳ PENDING (BLOCKER)
**Goal**: Enable voice recording via secure context (REQUIRED for production STT)

> **Why**: Browsers block `getUserMedia()` (microphone) on insecure origins.
> Voice input works on localhost but fails on `http://` remote access.

| Task | Status | Description |
|------|--------|-------------|
| 5.1 | ⏳ | Choose deployment method |
| 5.2 | ⏳ | Configure HTTPS/SSL termination |
| 5.3 | ⏳ | Test voice recording over HTTPS |
| 5.4 | ⏳ | Production deployment |

**HTTPS Termination Options**:

| Option | Complexity | Cost | Pros | Cons |
|--------|------------|------|------|------|
| **Cloudflare Tunnel** | Easy | Free | No ports, auto-HTTPS, DDoS protection | Requires Cloudflare account |
| **Streamlit Cloud** | Easy | Free | Zero config, built-in HTTPS | Limited customization |
| **ngrok** | Easy | Free | Quick testing | Not for production |
| **Caddy** | Easy | Free | Auto Let's Encrypt, simple config | Less common |
| **Nginx + Let's Encrypt** | Medium | Free | Production-grade, flexible | More setup |
| **Traefik** | Medium | Free | Docker-native, auto-certs | Learning curve |
| **AWS ALB / GCP LB** | Medium | $$ | Scalable, managed | Cloud cost |

**Recommended: Cloudflare Tunnel** (Easiest for self-hosted)
```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Login and create tunnel
cloudflared tunnel login
cloudflared tunnel create zoocari

# Run tunnel (points to local Streamlit)
cloudflared tunnel run --url http://localhost:8501 zoocari
```

**Alternative: Docker + Nginx + Let's Encrypt**
```yaml
# docker-compose.yml additions
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/letsencrypt:ro
    depends_on:
      - zoocari

  certbot:
    image: certbot/certbot
    volumes:
      - ./certs:/etc/letsencrypt
```

**Nginx Config (nginx.conf)**:
```nginx
server {
    listen 443 ssl;
    server_name zoocari.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/zoocari.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zoocari.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://zoocari:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## File Changes Summary

| File | Changes | Status |
|------|---------|--------|
| `zoo_chat.py` | STT function, TTS function (ElevenLabs), voice mode UI | ✅ Done |
| `requirements.txt` | Added `elevenlabs` package | ✅ Done |
| `.env` | `ELEVENLABS_API_KEY` (optional) | ✅ Documented |
| `docker-compose.yml` | HTTPS proxy (Phase 5) | ⏳ Pending |
| `nginx.conf` | SSL configuration (Phase 5) | ⏳ Pending |

---

## Technical Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| STT Model | `whisper-1` | Stable, reliable for kids' speech |
| TTS Provider | ElevenLabs (primary) | More natural, expressive voices |
| TTS Fallback | OpenAI `tts-1` | Works without ElevenLabs key |
| Default Voice | Rachel | Warm, friendly for kids |
| Auto-play | Yes (voice mode only) | Natural conversation flow |

---

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (enables ElevenLabs TTS)
ELEVENLABS_API_KEY=...
```

---

### Phase 6: Local STT + Enhanced TTS 🟡 NEW
**Goal**: Replace OpenAI Whisper API with local inference, evaluate enhanced TTS

> **Full Details**: See [VOICE_UPGRADE_PLAN.md](./VOICE_UPGRADE_PLAN.md)

| Task | Status | Description |
|------|--------|-------------|
| 6.1 | ⏳ | Add `faster-whisper` to requirements.txt |
| 6.2 | ⏳ | Implement `transcribe_audio_local()` function |
| 6.3 | ⏳ | Add local-first with API fallback logic |
| 6.4 | ⏳ | Update Dockerfile for model caching |
| 6.5 | ⏳ | Add warmup to entrypoint.sh |
| 6.6 | ⏳ | Evaluate Orpheus/Chatterbox for emotion control |

**Recommended Option (from research):**

| Component | Current | Upgrade | Benefit |
|-----------|---------|---------|---------|
| STT | Whisper API (~800ms) | Faster-Whisper (~300ms) | 60% faster, free |
| TTS | Kokoro (~100ms) | Keep or Orpheus (~200ms) | Emotion control |

**Quick Win Implementation:**
```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio_local(audio_bytes: bytes) -> str:
    segments, _ = model.transcribe(audio_file)
    return " ".join([seg.text for seg in segments])
```

**New Dependencies:**
```txt
faster-whisper>=1.0.0
# Optional for enhanced TTS:
# orpheus-speech>=0.1.0
```

---

## References

- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech)
- [Streamlit st.audio_input](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input)
- [MediaRecorder HTTPS Requirement](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia#privacy_and_security)
- [Faster-Whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [Orpheus TTS GitHub](https://github.com/canopyai/Orpheus-TTS)
- [Modal: Open Source STT Models](https://modal.com/blog/open-source-stt)
- [BentoML: Open Source TTS Models](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
