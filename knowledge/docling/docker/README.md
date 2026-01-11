# Docker Development Environment

This directory contains Docker configuration for local development of the Zoocari application.

## Quick Start

1. **Set up environment variables:**
   ```bash
   cd docker
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start development environment:**
   ```bash
   docker compose -f docker/docker-compose.dev.yml up --build
   ```

3. **Access services:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Architecture

### Services

#### API (Backend)
- **Image:** Python 3.12
- **Port:** 8000
- **Hot Reload:** Yes (uvicorn --reload)
- **Source:** `apps/api/` mounted at `/app/apps/api`
- **Data:** `data/` mounted at `/app/data`
- **Health Check:** GET /health

#### Web (Frontend)
- **Image:** Node 20
- **Port:** 5173
- **Hot Reload:** Yes (Vite HMR)
- **Source:** `apps/web/` mounted at `/app`
- **API URL:** http://api:8000 (via Docker network)

### Volumes

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./apps/api` | `/app/apps/api` | API source code hot reload |
| `./apps/web` | `/app` | Web source code hot reload |
| `./data` | `/app/data` | LanceDB + SQLite persistence |

### Network

Both services run on the `zoocari` bridge network, allowing web to reach api via hostname `api:8000`.

## Development Workflow

### Making Changes

**Python/FastAPI changes:**
- Edit files in `apps/api/`
- Uvicorn will auto-reload on save
- Check logs: `docker compose -f docker/docker-compose.dev.yml logs -f api`

**React/TypeScript changes:**
- Edit files in `apps/web/`
- Vite will hot-reload in browser
- Check logs: `docker compose -f docker/docker-compose.dev.yml logs -f web`

### Common Commands

```bash
# Start services
docker compose -f docker/docker-compose.dev.yml up

# Start in background
docker compose -f docker/docker-compose.dev.yml up -d

# Rebuild after dependency changes
docker compose -f docker/docker-compose.dev.yml up --build

# View logs
docker compose -f docker/docker-compose.dev.yml logs -f

# Stop services
docker compose -f docker/docker-compose.dev.yml down

# Stop and remove volumes
docker compose -f docker/docker-compose.dev.yml down -v
```

### Health Checks

Verify API health:
```bash
curl http://localhost:8000/health
# Expected: {"ok": true}
```

Check service status:
```bash
docker compose -f docker/docker-compose.dev.yml ps
```

## Troubleshooting

### API won't start

**Issue:** Container exits immediately or health check fails

**Solutions:**
1. Check logs: `docker compose -f docker/docker-compose.dev.yml logs api`
2. Verify OPENAI_API_KEY is set in `docker/.env`
3. Ensure `data/zoo_lancedb/` directory exists
4. Check port 8000 isn't already in use: `lsof -i :8000`

### Web can't connect to API

**Issue:** Frontend shows network errors

**Solutions:**
1. Verify API is healthy: `curl http://localhost:8000/health`
2. Check CORS settings in API allow `http://localhost:5173`
3. Ensure both services are on same network: `docker network inspect zoocari`
4. Check web container can resolve `api`: `docker exec zoocari-web-dev ping api`

### Hot reload not working

**Python hot reload:**
1. Verify volume mount: `docker exec zoocari-api-dev ls -la /app/apps/api`
2. Check uvicorn is running with --reload flag
3. Ensure file permissions allow Docker to read changed files

**Vite hot reload:**
1. Verify browser console shows WebSocket connection
2. Check Vite server logs: `docker compose logs web`
3. Ensure host.docker.internal or localhost:5173 is accessible

### Port conflicts

**Issue:** Port 8000 or 5173 already in use

**Solution:**
```bash
# Find process using port
lsof -i :8000
lsof -i :5173

# Kill process or change port in docker-compose.dev.yml
```

### Data persistence issues

**Issue:** LanceDB or SQLite data not persisting

**Solutions:**
1. Verify data directory exists: `ls -la data/`
2. Check volume mount: `docker exec zoocari-api-dev ls -la /app/data`
3. Ensure correct paths in environment variables:
   - LANCEDB_PATH=/app/data/zoo_lancedb
   - SESSION_DB_PATH=/app/data/sessions.db

### Dependency changes not applied

**Issue:** New npm or pip packages not installed

**Solution:**
```bash
# Rebuild containers
docker compose -f docker/docker-compose.dev.yml up --build

# Or rebuild specific service
docker compose -f docker/docker-compose.dev.yml build api
docker compose -f docker/docker-compose.dev.yml build web
```

## Environment Variables

See `.env.example` for all available variables. Key ones:

- `OPENAI_API_KEY` - **Required** for embeddings, LLM, and STT fallback
- `TTS_PROVIDER` - kokoro (local), elevenlabs, or openai
- `STT_PROVIDER` - faster-whisper (local) or openai
- `ELEVENLABS_API_KEY` - Optional, for cloud TTS fallback

## Production vs Development

This setup is for **local development only**. Key differences from production:

| Feature | Development | Production (Task 6.1) |
|---------|-------------|----------------------|
| Hot reload | Yes | No |
| Source mounts | Yes | Copied at build time |
| Build optimization | No | Yes (multi-stage) |
| Security | Permissive | Hardened |
| Logs | Verbose | Structured |

## Next Steps

- Task 6.1 will create production-ready Dockerfiles
- CI/CD pipeline will automate builds and deployments
- See `docs/integration/CONTRACT.md` for API contracts
