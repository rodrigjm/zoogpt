# Docker Deployment Guide - Kokoro-FastAPI TTS Sidecar

## Overview
Zoocari uses Kokoro-FastAPI as a sidecar service for high-performance, low-latency TTS with streaming support.

## Architecture
- **kokoro-tts**: Standalone TTS service (ghcr.io/remsky/kokoro-fastapi-cpu:latest)
- **api**: Main FastAPI backend, connects to kokoro-tts via Docker network
- **web**: React frontend
- **admin-api/admin-web**: Admin portal (optional, profile: admin)
- **cloudflared**: HTTPS tunnel (optional, profile: tunnel)

## Quick Start

### Production
```bash
# Start core services (api, web, kokoro-tts)
docker compose up --build

# With admin portal
docker compose --profile admin up --build

# With HTTPS tunnel
docker compose --profile tunnel up --build
```

### Development
```bash
# Start dev environment with hot reload
docker compose -f docker/docker-compose.dev.yml up --build
```

## Service Details

### kokoro-tts
- **Image**: ghcr.io/remsky/kokoro-fastapi-cpu:latest
- **Port**: 8880 (exposed to host and api service)
- **Endpoints**:
  - POST /v1/audio/speech (OpenAI-compatible TTS)
  - GET /health (health check)
  - WebSocket support for streaming
- **Environment Variables**:
  - TARGET_MIN_TOKENS=100
  - TARGET_MAX_TOKENS=200
  - DEFAULT_VOICE=af_heart
- **Volume**: zoocari-kokoro-models (persists downloaded models)

### api
- **Port**: 8000
- **Dependencies**: kokoro-tts
- **Key Environment Variables**:
  - KOKORO_TTS_URL=http://kokoro-tts:8880
  - TTS_PROVIDER=kokoro
  - TTS_VOICE=af_heart
- **Volumes**:
  - ./data (LanceDB, SQLite sessions)
  - zoocari-hf-cache (HuggingFace models)
  - zoocari-torch-cache (PyTorch models)

## Healthchecks

### Verify kokoro-tts is running
```bash
curl http://localhost:8880/health
```

### Verify api can reach kokoro-tts
```bash
docker exec zoocari-api curl http://kokoro-tts:8880/health
```

### Full system health
```bash
docker compose ps
```

## Troubleshooting

### kokoro-tts fails to start
- Check Docker logs: `docker logs zoocari-kokoro-tts`
- Verify image is pulled: `docker images | grep kokoro-fastapi`
- Check port 8880 is not in use: `lsof -i :8880`

### api can't connect to kokoro-tts
- Verify both containers are on same network: `docker network inspect <network-name>`
- Check DNS resolution: `docker exec zoocari-api nslookup kokoro-tts`
- Verify KOKORO_TTS_URL env var: `docker exec zoocari-api env | grep KOKORO`

### Models not persisting
- Verify volume exists: `docker volume ls | grep kokoro-models`
- Check volume mount: `docker inspect zoocari-kokoro-tts | grep Mounts -A 10`

### High memory usage
- kokoro-tts CPU version uses ~1-2GB RAM
- api service limited to 4GB (see docker-compose.yml resources)
- Adjust limits in docker-compose.yml if needed

## Data Persistence

### Named Volumes
- `zoocari-kokoro-models`: Kokoro voice models (~500MB)
- `zoocari-hf-cache`: HuggingFace models (Whisper, embeddings)
- `zoocari-torch-cache`: PyTorch model cache

### Bind Mounts
- `./data`: LanceDB vector database and SQLite sessions

## Performance Tuning

### Target Token Configuration
Kokoro-FastAPI uses TARGET_MIN_TOKENS and TARGET_MAX_TOKENS to chunk text for streaming:
- MIN=100, MAX=200: Fast first chunk, good for short responses
- MIN=200, MAX=400: Fewer chunks, better for longer responses
- Adjust based on typical response length

### Resource Limits
Current api service limits:
- Memory limit: 4GB
- Memory reservation: 2GB

Increase if you see OOM errors or need to support more concurrent users.

## Network Configuration

### Production (docker-compose.yml)
- Uses default bridge network
- Services communicate via service names (kokoro-tts, api)

### Development (docker/docker-compose.dev.yml)
- Uses named network "zoocari"
- Port 5173 exposed for Vite HMR
- Source code mounted for hot reload

## Upgrading Kokoro-FastAPI

```bash
# Pull latest image
docker pull ghcr.io/remsky/kokoro-fastapi-cpu:latest

# Restart kokoro-tts service
docker compose up -d kokoro-tts

# Verify health
curl http://localhost:8880/health
```

## Cleanup

### Remove all containers and volumes
```bash
docker compose down -v
```

### Remove only containers (keep volumes)
```bash
docker compose down
```

### Prune unused volumes
```bash
docker volume prune
```
