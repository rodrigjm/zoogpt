# Zoocari Deployment Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- 12GB+ available RAM (8GB for Ollama, 4GB for other services)
- OpenAI API key (for fallback and STT)

### Environment Setup

1. Create `.env` file in project root:
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
LLM_PROVIDER=ollama              # ollama | openai
TTS_PROVIDER=kokoro              # kokoro | elevenlabs
STT_PROVIDER=faster-whisper      # faster-whisper | openai
TTS_VOICE=af_heart               # Kokoro voice preset

# Admin portal (if using --profile admin)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me-in-production
JWT_SECRET=generate-random-secret
```

2. First-time model download:
```bash
# Start Ollama service
docker compose up -d ollama

# Pull models (one-time, ~7GB total)
docker compose exec ollama ollama pull phi4
docker compose exec ollama ollama pull llama-guard3:1b

# Verify models
docker compose exec ollama ollama list
```

3. Start all services:
```bash
# Core services (web, api, ollama, kokoro-tts)
docker compose up -d

# With admin portal
docker compose --profile admin up -d

# Check status
docker compose ps
```

## Services

### Core Services
| Service | Port | Description |
|---------|------|-------------|
| web | 3000 | React frontend |
| api | 8000 | FastAPI backend |
| ollama | 11434 | Local LLM (Phi-4, LlamaGuard) |
| kokoro-tts | 8880 | Text-to-speech sidecar |

### Optional Services
| Service | Port | Profile | Description |
|---------|------|---------|-------------|
| admin-web | 3001 | admin | Admin portal frontend |
| admin-api | 8001 | admin | Admin portal backend |
| cloudflared | - | tunnel | Cloudflare HTTPS tunnel |

## Health Checks

```bash
# Check all containers
docker compose ps

# Ollama models
curl http://localhost:11434/api/tags

# API health
curl http://localhost:8000/health

# Kokoro TTS
curl http://localhost:8880/health

# View logs
docker compose logs -f api
docker compose logs -f ollama
```

## Data Persistence

All data is stored in `./data/` directory:
```
data/
├── zoo_lancedb/          # Vector database (RAG)
├── sessions.db           # Chat session history
├── admin_config.json     # Admin portal config
└── animal_metadata.csv   # Animal info (optional)
```

Named Docker volumes:
- `zoocari-ollama-models` - Phi-4 and LlamaGuard models (~7GB)
- `zoocari-kokoro-models` - Kokoro TTS models (~500MB)
- `zoocari-hf-cache` - HuggingFace model cache
- `zoocari-torch-cache` - PyTorch cache

## Common Operations

### Update and Rebuild
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up --build -d
```

### Reset Models
```bash
# Remove all volumes (will re-download models)
docker compose down -v

# Re-pull Ollama models
docker compose up -d ollama
docker compose exec ollama ollama pull phi4
docker compose exec ollama ollama pull llama-guard3:1b
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Filter for Ollama usage
docker compose logs api | grep -i ollama
```

### Stop Services
```bash
# Stop all
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Troubleshooting

### Ollama not responding
```bash
# Check Ollama health
curl http://localhost:11434/api/tags

# Restart Ollama
docker compose restart ollama

# Check logs
docker compose logs ollama
```

### API fails to start
```bash
# Check if LanceDB exists
ls -la data/zoo_lancedb/

# Check environment variables
docker compose exec api env | grep -E 'OPENAI|OLLAMA|LANCEDB'

# Check logs
docker compose logs api
```

### Slow responses
```bash
# Check Ollama model is loaded
curl http://localhost:11434/api/tags

# Monitor resource usage
docker stats

# Switch to OpenAI temporarily
# Set LLM_PROVIDER=openai in .env and restart
docker compose restart api
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   web       │    api      │ kokoro-tts  │     ollama       │
│  (React)    │  (FastAPI)  │   (TTS)     │  (Phi-4 + Guard) │
└─────────────┴──────┬──────┴─────────────┴────────┬─────────┘
                     │                              │
                     │  1. Try Ollama (local)       │
                     ├─────────────────────────────►│
                     │                              │
                     │  2. Fallback to OpenAI       │
                     ├─────────────────────────────► (external)
```

## Configuration Details

### LLM Provider (Ollama vs OpenAI)
- Default: Ollama with Phi-4 (local inference)
- Fallback: OpenAI GPT-4 when Ollama unavailable
- Toggle: Set `LLM_PROVIDER=openai` to skip Ollama

### TTS Provider (Kokoro vs ElevenLabs)
- Default: Kokoro-FastAPI (local, low latency)
- Alternative: ElevenLabs (cloud, requires API key)
- Toggle: Set `TTS_PROVIDER=elevenlabs`

### STT Provider (Faster-Whisper vs OpenAI)
- Default: Faster-Whisper (local)
- Alternative: OpenAI Whisper (cloud)
- Toggle: Set `STT_PROVIDER=openai`

## Performance Expectations

### With Ollama (Local)
- Simple Q&A: <500ms
- Complex Q&A: <2s
- Safety check: <200ms
- TTS generation: <500ms (streaming)

### With OpenAI (Fallback)
- Simple Q&A: <1s
- Complex Q&A: <3s
- Safety check: <500ms
- TTS generation: <1s

## Resource Usage

### Memory
- Ollama: 4-8GB (8GB limit, 4GB reservation)
- API: 2-4GB (4GB limit, 2GB reservation)
- Kokoro-TTS: ~1GB
- Web: ~100MB
- Total: ~12GB recommended

### Disk
- Ollama models: ~7GB
- Kokoro models: ~500MB
- Application code: ~500MB
- LanceDB: ~100MB
- Total: ~8GB minimum

## Security Notes

- Never commit `.env` file with API keys
- Change `ADMIN_PASSWORD` and `JWT_SECRET` in production
- Use Cloudflare tunnel (`--profile tunnel`) for HTTPS
- API keys are only used in backend container
- All data stays local except OpenAI fallback calls

## Support

For issues or questions:
- Check logs: `docker compose logs -f`
- Review docs: `/docs/integration/`
- GitHub: https://github.com/rodrigjm/zoogpt
