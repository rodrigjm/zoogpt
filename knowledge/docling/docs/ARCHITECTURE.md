# Zoocari Architecture

## System Overview

Zoocari is a voice-first zoo Q&A chatbot built with a microservices architecture. All services run in Docker containers with a local-first, cloud-fallback pattern.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              User (Browser)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         web:3000 (React + Vite)                          │
│  - Voice-first UI with tap-to-talk                                       │
│  - Audio recording (MediaRecorder API)                                   │
│  - Audio playback (Web Audio API)                                        │
│  - Kid-friendly design (ages 6-12)                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         api:8000 (FastAPI)                               │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────────────┐  │
│  │    STT      │    RAG      │   Safety    │         TTS             │  │
│  │ (Whisper)   │ (LanceDB)   │ (Guards)    │      (Kokoro)           │  │
│  └─────────────┴─────────────┴─────────────┴─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
          │                │              │                  │
          ▼                ▼              ▼                  ▼
    ┌──────────┐    ┌───────────┐   ┌──────────┐      ┌───────────┐
    │ Ollama   │    │ LanceDB   │   │ Ollama   │      │ Kokoro    │
    │ (Phi-4)  │    │ (Vector)  │   │(LlamaGrd)│      │ FastAPI   │
    └──────────┘    └───────────┘   └──────────┘      └───────────┘
          │                                │
          └────────── Fallback ────────────┘
                         │
                         ▼
                   ┌──────────┐
                   │ OpenAI   │
                   │   API    │
                   └──────────┘
```

---

## Services

### Core Services

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **web** | React + Vite + TypeScript | 3000 | Voice-first frontend |
| **api** | FastAPI + Python 3.12 | 8000 | Backend orchestration |
| **ollama** | Ollama | 11434 | Local LLM (Phi-4 + LlamaGuard) |
| **kokoro-tts** | Kokoro-FastAPI | 8880 | Local text-to-speech |

### Optional Services

| Service | Technology | Port | Profile | Purpose |
|---------|------------|------|---------|---------|
| **admin-web** | React + Vite | 3001 | `admin` | Admin portal UI |
| **admin-api** | FastAPI | 8001 | `admin` | Admin portal API |
| **cloudflared** | Cloudflare Tunnel | - | `tunnel` | HTTPS for mobile |

---

## Data Flow

### Voice Chat Flow

```
1. User taps microphone button
2. Browser records audio (WebM/Opus)
3. Frontend sends audio to POST /api/voice/chat
4. API pipeline:
   a. STT: Audio → Text (Faster-Whisper local, OpenAI fallback)
   b. Safety: Input validation (prompt injection, PII, topic check)
   c. RAG: Query LanceDB → Retrieve context
   d. LLM: Generate response (Ollama Phi-4 local, OpenAI fallback)
   e. Safety: Output validation (content moderation)
   f. TTS: Text → Audio (Kokoro local)
5. API returns audio + text response
6. Frontend plays audio, displays text
```

### Text Chat Flow

```
1. User types question
2. Frontend sends to POST /api/chat
3. API pipeline:
   a. Safety: Input validation
   b. RAG: Query LanceDB
   c. LLM: Generate response
   d. Safety: Output validation
4. API returns text response
5. Optional: Frontend requests TTS via POST /api/voice/tts
```

---

## Component Details

### Speech-to-Text (STT)

**Local (Primary)**: Faster-Whisper
- Model: `base` with int8 quantization
- Latency: ~2-4s for short audio
- Location: `apps/api/app/services/stt.py`

**Cloud (Fallback)**: OpenAI Whisper API
- Model: `whisper-1`
- Latency: ~1-2s (includes network)

### Large Language Model (LLM)

**Local (Primary)**: Ollama + Phi-4
- Model: `phi4` (~4GB)
- Latency: 100-500ms
- Location: `apps/api/app/services/llm.py`

**Cloud (Fallback)**: OpenAI GPT-4o-mini
- Model: `gpt-4o-mini`
- Latency: 500ms-2s (includes network)

### RAG (Retrieval-Augmented Generation)

**Vector Database**: LanceDB
- Storage: `./data/zoo_lancedb/`
- Embeddings: OpenAI `text-embedding-3-small`
- Search: Hybrid (vector + keyword)
- Location: `apps/api/app/services/rag.py`

### Text-to-Speech (TTS)

**Local (Primary)**: Kokoro-FastAPI sidecar
- Model: Kokoro ONNX
- Voice: `af_heart` (default)
- Latency: ~300ms per chunk
- Location: `apps/api/app/services/tts.py`

**Cloud (Fallback)**: OpenAI TTS
- Model: `tts-1`
- Voice: `nova`

### Safety Guardrails

**Location**: `apps/api/app/services/safety.py`

| Check | Type | Description |
|-------|------|-------------|
| Length limit | Local | Max 500 chars |
| Prompt injection | Local regex | Detects jailbreak attempts |
| PII detection | Local regex | Blocks email, phone, SSN |
| Topic restriction | Local keyword | Ensures zoo-related content |
| Content moderation | LlamaGuard → OpenAI | Violence, sexual, hate speech |

---

## Data Storage

### Local Files (`./data/`)

```
data/
├── zoo_lancedb/          # Vector database
│   ├── animals.lance/    # Animal knowledge table
│   └── _latest_manifest  # LanceDB metadata
├── sessions.db           # SQLite chat history
└── admin_config.json     # Runtime configuration
```

### Docker Volumes

| Volume | Size | Contents |
|--------|------|----------|
| `zoocari-ollama-models` | ~7GB | Phi-4, LlamaGuard models |
| `zoocari-kokoro-models` | ~500MB | Kokoro TTS models |
| `zoocari-hf-cache` | ~500MB | HuggingFace cache |
| `zoocari-torch-cache` | ~200MB | PyTorch cache |

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...           # For fallback and embeddings

# LLM
LLM_PROVIDER=ollama             # ollama | openai
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=phi4
OLLAMA_GUARD_MODEL=llama-guard3:1b

# TTS
TTS_PROVIDER=kokoro             # kokoro | elevenlabs | openai
KOKORO_TTS_URL=http://kokoro-tts:8880
TTS_VOICE=af_heart

# STT
STT_PROVIDER=faster-whisper     # faster-whisper | openai

# Admin (optional)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=zoocari-admin
JWT_SECRET=change-in-production
```

### Runtime Configuration (`admin_config.json`)

```json
{
  "prompts": {
    "system_prompt": "You are Zoocari the Elephant...",
    "fallback_response": "I'm not sure about that!"
  },
  "model": {
    "name": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 500
  },
  "tts": {
    "provider": "kokoro",
    "default_voice": "af_heart",
    "speed": 1.0
  }
}
```

---

## Security

### API Security
- CORS configured for allowed origins
- Input validation on all endpoints
- Rate limiting (configurable)

### Content Safety
- Multi-layer guardrails (see Safety Guardrails above)
- Local-first moderation (LlamaGuard)
- OpenAI Moderation API fallback

### Data Privacy
- All inference can run locally
- No data sent to cloud when using Ollama
- OpenAI calls only for fallback/embeddings

### HTTPS
- Required for mobile voice (browser security)
- Use Cloudflare Tunnel (`--profile tunnel`)
- Or deploy behind reverse proxy with TLS

---

## Performance

### Latency Targets

| Operation | Local | With OpenAI Fallback |
|-----------|-------|---------------------|
| STT | 2-4s | 1-2s |
| LLM (simple Q&A) | 100-500ms | 500ms-2s |
| Safety check | <200ms | <500ms |
| TTS (per chunk) | ~300ms | ~500ms |
| **Total voice round-trip** | **3-5s** | **3-5s** |

### Resource Usage

| Service | Memory | CPU |
|---------|--------|-----|
| Ollama | 4-8GB | High during inference |
| API | 2-4GB | Moderate |
| Kokoro-TTS | ~1GB | Moderate |
| Web | ~100MB | Low |

---

## Scaling Considerations

### Current Design
- Single-instance services
- Local storage (LanceDB, SQLite)
- Suitable for single-location deployment

### For Multi-Instance
- Replace SQLite with PostgreSQL
- Add Redis for session caching
- Use S3/GCS for model storage
- Consider vLLM for high-throughput LLM serving
