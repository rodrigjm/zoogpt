# Voice Feature Project Plan: Zoocari Voice Mode

## Architecture Overview: OpenAI Chained Voice Pipeline

```
User Audio → [gpt-4o-transcribe] → Text → [gpt-4o-mini] → Response Text → [gpt-4o-mini-tts] → Audio Output
     ↓              ↓                         ↓                    ↓
   st.audio_input   STT API           Existing chat logic      TTS API + st.audio
```

The chained architecture is recommended because:
- High control and transparency (full transcript available)
- Robust function calling support
- Reliable, predictable responses
- Ideal for structured workflows like your kid-friendly Q&A

---

## Phased Project Roadmap

---

### Phase 1: Audio Input Integration
**Goal**: Enable voice recording from the user

| Task | Description | Files Affected |
|------|-------------|----------------|
| 1.1 | Add `st.audio_input` widget for voice recording | `zoo_chat.py` |
| 1.2 | Create audio-to-text transcription function using `gpt-4o-transcribe` or `whisper-1` | `zoo_chat.py` (new function) |
| 1.3 | Add voice mode toggle (button vs voice) in left panel | `zoo_chat.py` |
| 1.4 | Handle audio file format conversion if needed | `zoo_chat.py` |
| 1.5 | Update session state for voice input mode | `zoo_chat.py` |

**New Dependencies**: None (OpenAI client already present)

**Key Code Addition**:
```python
# New function for STT
def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert audio to text using OpenAI's transcription API."""
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"
    transcription = client.audio.transcriptions.create(
        model="whisper-1",  # or gpt-4o-transcribe
        file=audio_file,
    )
    return transcription.text
```

---

### Phase 2: Text-to-Speech Output
**Goal**: Generate audio responses alongside text streaming

| Task | Description | Files Affected |
|------|-------------|----------------|
| 2.1 | Create TTS function using `gpt-4o-mini-tts` | `zoo_chat.py` (new function) |
| 2.2 | Generate audio after text response completes | `zoo_chat.py` |
| 2.3 | Display audio player using `st.audio()` | `zoo_chat.py` |
| 2.4 | Add voice selection option (alloy, nova, etc.) | `zoo_chat.py` |
| 2.5 | Store audio in session state for replay | `zoo_chat.py` |

**Key Code Addition**:
```python
# New function for TTS
def generate_speech(text: str, voice: str = "nova") -> bytes:
    """Convert text to speech using OpenAI's TTS API."""
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=voice,
        input=text,
    ) as response:
        return response.read()
```

---

### Phase 3: UI/UX Enhancements
**Goal**: Seamless voice interaction experience

| Task | Description | Files Affected |
|------|-------------|----------------|
| 3.1 | Add voice mode toggle button (microphone icon) | `zoo_chat.py` |
| 3.2 | Add visual recording indicator | `zoo_chat.py` (CSS) |
| 3.3 | Style audio player to match Leesburg branding | `zoo_chat.py` (CSS) |
| 3.4 | Add "Listen to Answer" button | `zoo_chat.py` |
| 3.5 | Mobile-responsive voice controls | `zoo_chat.py` (CSS) |
| 3.6 | Auto-play option for TTS response | `zoo_chat.py` |

---

### Phase 4: Integration & Polish
**Goal**: Production-ready voice features

| Task | Description | Files Affected |
|------|-------------|----------------|
| 4.1 | Error handling for audio recording failures | `zoo_chat.py` |
| 4.2 | Loading states during transcription/TTS | `zoo_chat.py` |
| 4.3 | Fallback to text when voice unavailable | `zoo_chat.py` |
| 4.4 | Add voice-friendly response formatting | `zoo_chat.py` |
| 4.5 | Test with kid-appropriate voice selection | `zoo_chat.py` |
| 4.6 | Update requirements.txt if needed | `requirements.txt` |

---

## File Changes Summary

| File | Changes |
|------|---------|
| `zoo_chat.py` | +2 new functions (STT, TTS), UI updates for voice mode toggle, audio widgets, session state |
| `requirements.txt` | Verify OpenAI version supports audio APIs (should be fine with current setup) |

---

## Key Integration Points in Existing Code

1. **Line 77-79** (`set_pending_question`): Extend to handle voice input
2. **Line 147-160** (`get_chat_response`): Add TTS generation after response
3. **Line 922-928** (question form): Add voice input alternative
4. **Line 1009-1019** (response display): Add audio player for TTS output

---

## Technical Decisions Required

1. **STT Model**: `whisper-1` (stable) vs `gpt-4o-transcribe` (newer)?
2. **TTS Model**: `tts-1` (faster) vs `tts-1-hd` (higher quality)?
3. **Voice**: Which voice for Zoocari? (`nova` is friendly, `alloy` is neutral)
4. **Auto-play**: Should TTS auto-play, or require button click?
5. **Voice-only mode**: Separate mode, or alongside text input?

---

## References

- [OpenAI Voice Agents Guide](https://platform.openai.com/docs/guides/voice-agents)
- [OpenAI Audio API](https://platform.openai.com/docs/guides/audio)
- [OpenAI Text-to-Speech](https://platform.openai.com/docs/guides/text-to-speech)
- [Streamlit st.audio_input](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input)
