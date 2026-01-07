# Voice Feature Project Plan: Zoocari Voice Mode

## Current Status: Kokoro Local TTS Integration

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Audio Input Integration |
| Phase 2 | ✅ Complete | Text-to-Speech Output (ElevenLabs) |
| Phase 2.5 | 🟡 In Progress | **Kokoro Local TTS** (latency optimization) |
| Phase 3 | ✅ Complete | UI/UX Enhancements |
| Phase 4 | ⏳ Pending | Integration & Polish |
| Phase 5 | ⏳ Pending | HTTPS Deployment (Mobile Support) |

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

### Phase 5: HTTPS Deployment ⏳ PENDING (NEW)
**Goal**: Enable mobile voice recording via secure context

| Task | Status | Description |
|------|--------|-------------|
| 5.1 | ⏳ | Choose deployment method |
| 5.2 | ⏳ | Configure HTTPS/SSL |
| 5.3 | ⏳ | Test mobile voice recording |
| 5.4 | ⏳ | Production deployment |

**Deployment Options**:

| Option | Complexity | Cost | Best For |
|--------|------------|------|----------|
| **Streamlit Cloud** | Easy | Free | Quick deployment |
| **Cloudflare Tunnel** | Easy | Free | Self-hosted, no ports |
| **ngrok** | Easy | Free/Paid | Testing only |
| **Nginx + Let's Encrypt** | Medium | Free | Production self-hosted |
| **Cloud Provider** | Medium | Varies | Scalable production |

**Docker + Nginx Setup** (for self-hosted):
```yaml
# docker-compose.yml additions
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/letsencrypt
    depends_on:
      - zoocari
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

## References

- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech)
- [Streamlit st.audio_input](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input)
- [MediaRecorder HTTPS Requirement](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia#privacy_and_security)
