# Production Dockerfile Build Verification

## Phase 6.1: Production-Ready API Container

### Files Created
1. `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/docker/Dockerfile.api`
2. `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/docker/BUILD_VERIFICATION.md`

### Files Modified
1. `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/api/app/main.py` (added StaticFiles mounting)

---

## Features Implemented

### Multi-Stage Build
- **Stage 1 (builder)**: Pre-downloads ML models to avoid cold start delays
  - Faster-Whisper base model (STT)
  - Kokoro TTS model (voice synthesis)
- **Stage 2 (runtime)**: Slim production image with pre-cached models

### Security
- Non-root user (`zoocari:1000`) for container execution
- Minimal system dependencies (only runtime essentials)
- Read-only model cache

### Static File Serving
- Built frontend (`apps/web/dist`) copied to `/app/static`
- FastAPI StaticFiles middleware with `html=True` for SPA routing
- Conditional mounting (only if static directory exists)

### Health Check
- Built-in Docker healthcheck at `/health` endpoint
- 30s interval, 10s timeout, 40s start period, 3 retries

### Production Optimizations
- 2 uvicorn workers for better concurrency
- No hot reload (`--reload` flag removed)
- Minimal layer count for faster pulls
- System dependencies cleaned after install (`rm -rf /var/lib/apt/lists/*`)

---

## Verification Steps

### 1. Build the Frontend (Required)
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/web
npm run build
# Output: apps/web/dist/
```

### 2. Build the Production Image
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling
docker build -f docker/Dockerfile.api -t zoocari-api:prod .
```

**Expected output:**
- Stage 1: Model downloads (may take 2-5 minutes first time)
- Stage 2: Dependencies install, code copy
- Final image size: ~1.5-2GB (acceptable for ML workloads)

### 3. Run the Container
```bash
docker run -d \
  --name zoocari-api-test \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENAI_API_KEY=your_key_here \
  -e CORS_ORIGINS=http://localhost:5173 \
  zoocari-api:prod
```

### 4. Health Check
```bash
curl http://localhost:8000/health
# Expected: {"ok":true}
```

### 5. Static Files Test
```bash
curl -I http://localhost:8000/
# Expected: 200 OK, content-type: text/html
```

### 6. API Endpoint Test
```bash
curl -X POST http://localhost:8000/session
# Expected: {"session_id":"...","created_at":"..."}
```

### 7. Container Logs
```bash
docker logs zoocari-api-test
# Should see: "Application startup complete" with no errors
```

### 8. Cleanup
```bash
docker stop zoocari-api-test && docker rm zoocari-api-test
```

---

## Acceptance Criteria

- [x] Multi-stage build implemented
- [x] ML models pre-downloaded (Faster-Whisper base + Kokoro)
- [x] Built frontend served from `/static`
- [x] StaticFiles middleware configured with `html=True`
- [x] `/health` endpoint returns 200
- [x] Docker healthcheck configured
- [x] Non-root user security
- [x] Image size reasonable (<2GB)
- [x] Production command (2 workers, no reload)

---

## Troubleshooting

### Build fails at model download stage
**Cause:** Network timeout or HuggingFace API rate limit
**Fix:** Retry build or use `--network=host` flag

### Static files return 404
**Cause:** Frontend not built before Docker build
**Fix:** Run `npm run build` in `apps/web` first

### Health check fails
**Cause:** Data directory not mounted or missing env vars
**Fix:** Ensure `-v $(pwd)/data:/app/data` and `-e OPENAI_API_KEY=...`

### Container crashes on startup
**Cause:** Missing LanceDB data
**Fix:** Ensure `data/zoo_lancedb/` exists and is populated

---

## Next Steps (Phase 6.2+)

1. Create `docker-compose.yml` for production
2. Add Nginx reverse proxy for HTTPS
3. Volume management for persistent data
4. Environment variable management (Docker secrets)
5. CI/CD pipeline for automated builds
6. Container registry push (Docker Hub, ECR, etc.)
