# Zoocari Deployment Scripts

Automated deployment and rollback scripts for production and development environments.

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy.sh` | Production deployment with auto-rollback | `./scripts/deploy.sh` |
| `backup.sh` | Backup critical data | `./scripts/backup.sh` |
| `rollback-prod.sh` | Production rollback with backup restore | `./scripts/rollback-prod.sh` |
| `rollback.sh` | Development rollback to legacy Streamlit | `./scripts/rollback.sh` |
| `staging-validate.sh` | Validate all API endpoints and functionality | `./scripts/staging-validate.sh [url]` |
| `load-test.sh` | Performance testing with concurrent requests | `./scripts/load-test.sh [url] [n] [c]` |
| `test-deployment.sh` | Quick deployment smoke test | `./scripts/test-deployment.sh` |

## Production Deployment

### deploy.sh

Safely deploys new version with automatic rollback on failure.

**Usage:**
```bash
# Standard deployment
./scripts/deploy.sh

# Skip backup (not recommended)
./scripts/deploy.sh --skip-backup

# Deploy without auto-rollback
./scripts/deploy.sh --no-rollback

# Deploy with Cloudflare tunnel
./scripts/deploy.sh --profile cloudflare
```

**Process:**
1. Backup current data
2. Build production images
3. Stop old containers gracefully
4. Start new containers
5. Wait for health check (max 3.3 minutes)
6. Auto-rollback on failure (unless --no-rollback)

**Expected time:** 5-10 minutes

## Backup Management

### backup.sh

Creates timestamped backups of critical data.

**Usage:**
```bash
# Create backup (keep last 5)
./scripts/backup.sh

# Keep last 10 backups
./scripts/backup.sh --keep 10
```

**Backed up data:**
- SQLite sessions database (data/sessions.db)
- LanceDB vector database (data/zoo_lancedb) - skipped if >100MB

**Backup location:** `data/backups/YYYYMMDD_HHMMSS/`

## Rollback

### rollback-prod.sh

Rollback to previous backup or container version.

**Usage:**
```bash
# Rollback containers only (keep current data)
./scripts/rollback-prod.sh

# Rollback and restore from specific backup
./scripts/rollback-prod.sh --backup 20260112_143000

# Skip health check
./scripts/rollback-prod.sh --skip-health-check
```

**List available backups:**
```bash
ls -1 data/backups/
```

### rollback.sh

Rollback from new architecture to legacy Streamlit app (development only).

**Usage:**
```bash
# Rollback to legacy
./scripts/rollback.sh

# Skip health check
./scripts/rollback.sh --skip-health-check
```

## Health Checks

All scripts perform automatic health checks:

- **Production:** `http://localhost:8000/health`
- **Legacy:** `http://localhost:8501/_stcore/health`

Health check parameters:
- Interval: 10 seconds
- Max wait: 3.3 minutes (production), 2.5 minutes (legacy)
- Auto-rollback on failure (production only)

## Common Workflows

### Standard Production Deployment

```bash
# 1. Deploy new version
./scripts/deploy.sh

# If deployment succeeds, you're done!
# If it fails, automatic rollback will restore previous state
```

### Manual Rollback After Successful Deployment

```bash
# 1. List available backups
ls -1 data/backups/

# 2. Rollback to specific backup
./scripts/rollback-prod.sh --backup 20260112_140000
```

### Emergency Rollback

```bash
# Quick rollback to previous containers (no data restore)
./scripts/rollback-prod.sh --skip-health-check
```

### Deploy with Cloudflare Tunnel

```bash
# Ensure TUNNEL_TOKEN is set in .env
./scripts/deploy.sh --profile cloudflare
```

## Error Handling

All scripts include:
- Automatic error detection (`set -e`)
- Color-coded logging (INFO/SUCCESS/WARNING/ERROR)
- Health check verification
- Graceful container shutdown (30s timeout)

### Common Issues

**Docker not running:**
```
ERROR: Docker is not running
Solution: Start Docker Desktop or Docker daemon
```

**Missing .env file:**
```
ERROR: .env file not found
Solution: Create .env with OPENAI_API_KEY and other required variables
```

**Health check timeout:**
```
ERROR: Health check failed after 200 seconds
Solution: Check logs with: docker logs zoocari-api-prod
```

**Backup failure:**
```
ERROR: Backup failed! Aborting deployment.
Solution: Check disk space and permissions on data/backups/
```

## Logs and Monitoring

**View real-time logs:**
```bash
docker logs -f zoocari-api-prod
```

**View last 100 lines:**
```bash
docker logs --tail 100 zoocari-api-prod
```

**Check container status:**
```bash
docker ps | grep zoocari
```

**View all containers (including stopped):**
```bash
docker compose -f docker/docker-compose.prod.yml ps -a
```

## Staging Validation

### staging-validate.sh

Tests all API endpoints against staging environment to ensure contract compliance.

**Usage:**
```bash
# Test local development
./scripts/staging-validate.sh http://localhost:8000

# Test staging server
./scripts/staging-validate.sh https://staging.zoocari.com
```

**Tests performed:**
1. GET /health - Health check
2. POST /session - Create session
3. GET /session/{id} - Retrieve session
4. POST /chat - Send chat message
5. POST /chat/stream - Streaming chat (SSE)
6. POST /voice/stt - Speech-to-text
7. POST /voice/tts - Text-to-speech
8. Response time < 2s validation

**Exit codes:**
- 0 = All tests passed
- 1 = One or more tests failed

### load-test.sh

Performs load testing by sending concurrent requests to measure performance.

**Usage:**
```bash
# Default: 50 requests with concurrency 5
./scripts/load-test.sh http://localhost:8000

# Custom: 100 requests with concurrency 10
./scripts/load-test.sh http://localhost:8000 100 10

# Production test (use cautiously)
./scripts/load-test.sh https://staging.zoocari.com 50 5
```

**Metrics reported:**
- Success/failure counts
- Average latency
- P50, P95, P99 latencies
- Min/max response times
- Throughput (requests/second)

**Pass criteria:**
- Zero failures
- Average latency < 2000ms
- P95 latency < 5000ms (warning only)

**Note:** Load test requires GNU parallel for best performance, but falls back to background jobs if unavailable.

## Data Locations

- **SQLite sessions:** `data/sessions.db`
- **LanceDB vectors:** `data/zoo_lancedb/`
- **Backups:** `data/backups/YYYYMMDD_HHMMSS/`
- **Docker compose:** `docker/docker-compose.prod.yml`
- **Environment:** `.env` (project root)
- **Staging results:** `docs/integration/STAGING_RESULTS.md`

## Safety Features

1. **Pre-flight checks:** Verify Docker, .env, and required variables
2. **Automatic backups:** Data backed up before every deployment
3. **Health monitoring:** Wait for service health before marking success
4. **Auto-rollback:** Revert to previous state on failure
5. **Graceful shutdown:** 30-second timeout for container cleanup
6. **Backup rotation:** Keep last N backups, remove old ones

## Requirements

- Docker and Docker Compose
- curl (for health checks)
- sqlite3 (optional, for consistent database backups)
- jq (optional, for JSON parsing in health checks)
- bash 4.0+

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY` - OpenAI API key
- `CORS_ORIGINS` - Allowed CORS origins (production)

Optional in `.env`:
- `TUNNEL_TOKEN` - Cloudflare tunnel token
- `TTS_PROVIDER` - Text-to-speech provider (default: kokoro)
- `STT_PROVIDER` - Speech-to-text provider (default: faster-whisper)
- `EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)
