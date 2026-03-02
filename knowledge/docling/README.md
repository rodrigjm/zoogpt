# Zoocari

Voice-first, kid-friendly zoo Q&A chatbot for Leesburg Animal Park.

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/rodrigjm/zoogpt.git
cd zoogpt
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 2. Pull LLM models (one-time, ~7GB)
docker compose up -d ollama
docker compose exec ollama ollama pull phi4
docker compose exec ollama ollama pull llama-guard3:1b

# 3. Start all services
docker compose up -d

# 4. Open in browser
open http://localhost:3000
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   web:3000  │  api:8000   │kokoro:8880  │  ollama:11434    │
│   (React)   │  (FastAPI)  │   (TTS)     │ (Phi-4+Guard)    │
└─────────────┴──────┬──────┴─────────────┴────────┬─────────┘
                     │                              │
                     └── Local-first, OpenAI fallback ──┘
```

| Service | Port | Purpose |
|---------|------|---------|
| **web** | 3000 | React frontend (voice UI) |
| **api** | 8000 | FastAPI backend (RAG, safety) |
| **ollama** | 11434 | Local LLM (Phi-4) + safety (LlamaGuard) |
| **kokoro-tts** | 8880 | Local text-to-speech |

## Features

- **Voice-First**: Tap-to-talk interface optimized for kids 6-12
- **Local LLM**: Phi-4 via Ollama for fast, private inference
- **RAG Pipeline**: LanceDB vector search over curated zoo content
- **Safety Guardrails**: LlamaGuard + prompt injection detection
- **Local TTS**: Kokoro for low-latency speech synthesis
- **OpenAI Fallback**: Automatic failover when local services unavailable

## Services

### Core (Always Running)
```bash
docker compose up -d
```

### Admin Portal (Optional)
```bash
docker compose --profile admin up -d
# Access: http://localhost:3001
# Default: admin / zoocari-admin
```

### HTTPS Tunnel (For Mobile Voice)
```bash
docker compose --profile tunnel up -d
# Requires: CLOUDFLARE_TUNNEL_TOKEN in .env
```

## Configuration

Key environment variables in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-...

# LLM (default: local Ollama)
LLM_PROVIDER=ollama              # ollama | openai
OLLAMA_MODEL=phi4

# TTS (default: local Kokoro)
TTS_PROVIDER=kokoro              # kokoro | elevenlabs | openai

# STT (default: local Faster-Whisper)
STT_PROVIDER=faster-whisper      # faster-whisper | openai
```

## Data Storage

```
./data/
├── zoo_lancedb/          # Vector database (RAG)
├── sessions.db           # Chat session history
└── admin_config.json     # Runtime configuration

Docker volumes:
├── zoocari-ollama-models # ~7GB (Phi-4, LlamaGuard)
├── zoocari-kokoro-models # ~500MB (TTS models)
└── zoocari-hf-cache      # HuggingFace cache
```

## Development

```bash
# Backend (FastAPI)
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (React)
cd apps/web
npm install
npm run dev

# Run tests
cd apps/api && pytest tests/ -v
```

## Documentation

| Doc | Description |
|-----|-------------|
| [Quick Start](docs/QUICK_START.md) | One-command setup guide |
| [Deployment](docs/DEPLOYMENT.md) | Full deployment guide |
| [Cloudflare Tunnel](docs/CLOUDFLARE_TUNNEL_SETUP.md) | HTTPS setup for mobile |
| [Admin Portal](docs/design/admin-portal-architecture.md) | Admin portal design |
| [Ollama Integration](docs/integration/OLLAMA_INTEGRATION_PLAN.md) | Local LLM setup |

## Requirements

- Docker + Docker Compose
- 12GB+ RAM (8GB for Ollama)
- 10GB+ disk space
- OpenAI API key (for fallback)

## License

MIT
