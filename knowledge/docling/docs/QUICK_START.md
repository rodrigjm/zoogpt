# Zoocari Quick Start Guide

## Prerequisites

- Docker + Docker Compose
- 12GB+ RAM
- 10GB+ disk space
- OpenAI API key

---

## Option 1: Basic Setup (5 minutes)

```bash
# Clone repository
git clone https://github.com/rodrigjm/zoogpt.git
cd zoogpt

# Create environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Pull LLM models (one-time, ~7GB)
docker compose up -d ollama
docker compose exec ollama ollama pull phi4
docker compose exec ollama ollama pull llama-guard3:1b

# Start all services
docker compose up -d

# Verify
docker compose ps
curl http://localhost:8000/health

# Open app
open http://localhost:3000
```

---

## Option 2: With Admin Portal

```bash
# Start with admin profile
docker compose --profile admin up -d

# Services running:
# - http://localhost:3000  - Main app
# - http://localhost:3001  - Admin portal
# - http://localhost:8000  - API
# - http://localhost:8001  - Admin API

# Default admin credentials:
# Username: admin
# Password: zoocari-admin
```

To customize admin credentials, add to `.env`:
```bash
ADMIN_USERNAME=your-username
ADMIN_PASSWORD=your-secure-password
JWT_SECRET=generate-random-string
```

---

## Option 3: With HTTPS Tunnel (Mobile Voice)

Voice recording requires HTTPS on mobile devices. Use Cloudflare Tunnel:

```bash
# 1. Create tunnel at https://one.dash.cloudflare.com/
#    - Go to Networks > Tunnels > Create
#    - Copy the tunnel token

# 2. Add to .env
CLOUDFLARE_TUNNEL_TOKEN=your-token-here

# 3. Start with tunnel profile
docker compose --profile tunnel up -d

# Your app is now accessible via your Cloudflare domain with HTTPS
```

See [CLOUDFLARE_TUNNEL_SETUP.md](./CLOUDFLARE_TUNNEL_SETUP.md) for detailed instructions.

---

## Option 4: OpenAI-Only Mode (No Local LLM)

If you don't have enough RAM for Ollama:

```bash
# Edit .env
LLM_PROVIDER=openai
TTS_PROVIDER=openai
STT_PROVIDER=openai

# Start without Ollama
docker compose up -d web api kokoro-tts
```

---

## Service Overview

| Service | Port | Memory | Purpose |
|---------|------|--------|---------|
| **web** | 3000 | 100MB | React frontend |
| **api** | 8000 | 2-4GB | FastAPI backend |
| **ollama** | 11434 | 4-8GB | Local LLM (Phi-4, LlamaGuard) |
| **kokoro-tts** | 8880 | 1GB | Local text-to-speech |
| **admin-web** | 3001 | 100MB | Admin portal (optional) |
| **admin-api** | 8001 | 500MB | Admin API (optional) |

---

## Health Checks

```bash
# All services
docker compose ps

# API health
curl http://localhost:8000/health

# Ollama models
curl http://localhost:11434/api/tags

# Kokoro TTS
curl http://localhost:8880/health

# View logs
docker compose logs -f api
docker compose logs -f ollama
```

---

## Common Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up --build -d

# Reset everything (removes models!)
docker compose down -v
```

---

## Troubleshooting

### Ollama not responding
```bash
docker compose exec ollama ollama list    # Check models
docker compose restart ollama              # Restart
docker compose logs ollama                 # View logs
```

### API errors
```bash
docker compose exec api env | grep -E 'OPENAI|OLLAMA'  # Check env
docker compose logs api                                 # View logs
```

### Slow performance
```bash
docker stats                   # Check resources
# Temporarily use OpenAI:
# Set LLM_PROVIDER=openai in .env
docker compose restart api
```

### Voice not working on mobile
- Requires HTTPS - see Option 3 above
- Or use localhost for testing

---

## Next Steps

- [Full Deployment Guide](./DEPLOYMENT.md)
- [Admin Portal Architecture](./design/admin-portal-architecture.md)
- [Ollama Integration Details](./integration/OLLAMA_INTEGRATION_PLAN.md)
- [API Documentation](http://localhost:8000/docs)
