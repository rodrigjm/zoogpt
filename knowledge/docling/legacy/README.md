# Legacy Streamlit Application

This directory contains the preserved original Zoocari Streamlit application for rollback capability during the Node.js/FastAPI migration.

## Purpose

The legacy application is preserved to:
- Enable quick rollback if issues arise with the new architecture
- Provide a reference implementation during migration
- Ensure business continuity during the transition period

## Contents

### Core Application Files
- `zoo_chat.py` - Main Streamlit chatbot application
- `session_manager.py` - SQLite session handling
- `zoo_build_knowledge.py` - Knowledge base builder (Docling + LanceDB)
- `zoo_sources.py` - Curated animal education URLs

### TTS & Voice
- `tts_kokoro.py` - Local Kokoro TTS with cloud fallback chain

### Utilities
- `utils/text.py` - Markdown stripping and HTML sanitization
- `utils/tokenizer.py` - Tokenizer wrapper
- `utils/sitemap.py` - Sitemap utilities

### UI & Assets
- `static/zoocari.css` - Streamlit UI styling
- `zoocari_mascot_web.png` - Zoocari mascot image

### Docker & Configuration
- `Dockerfile` - Multi-stage build with Kokoro TTS support
- `docker-compose.yml` - Standalone compose for legacy app
- `entrypoint.sh` - Container entrypoint script
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- `OPENAI_API_KEY` environment variable or `.env` file in project root

### Running the Legacy App

From the `legacy/` directory:

```bash
# Start the legacy Streamlit app
docker compose up --build

# Access at: http://localhost:8501
```

From the project root:

```bash
# Use the rollback script (recommended)
./scripts/rollback.sh

# Or manually
cd legacy && docker compose up -d --build
```

### Environment Variables

The legacy app requires the following environment variables (set in project root `.env` or `legacy/.env`):

**Required:**
- `OPENAI_API_KEY` - OpenAI API key for chat, embeddings, and STT fallback

**Optional:**
- `ELEVENLABS_API_KEY` - ElevenLabs API key for cloud TTS fallback
- `TTS_PROVIDER` - TTS provider (kokoro, elevenlabs, or openai). Default: openai
- `TTS_VOICE` - Voice ID. Default: nova (OpenAI) or af_heart (Kokoro)
- `CLOUDFLARE_TUNNEL_TOKEN` - Cloudflare tunnel token for HTTPS access

## Data Persistence

The legacy app uses Docker volumes for persistent storage:

### Shared Data (with new architecture)
- `../data/` - Vector database (LanceDB) and SQLite sessions
  - Mounted at `/app/data` in container
  - Shared between legacy and new architecture

### Legacy-Specific Volumes
- `zoocari-legacy-hf-cache` - Hugging Face model cache (Kokoro, spaCy)
- `zoocari-legacy-torch-cache` - PyTorch cache

These volumes are separate from the new architecture to prevent conflicts.

## Rollback Procedure

### Automated Rollback (Recommended)

Use the rollback script from the project root:

```bash
./scripts/rollback.sh
```

The script will:
1. Stop new architecture containers (FastAPI, Next.js, Nginx)
2. Start legacy Streamlit container
3. Verify health via `/_stcore/health` endpoint
4. Complete in <5 minutes

### Manual Rollback

```bash
# 1. Stop new containers (if running)
cd docker
docker compose down

# 2. Start legacy container
cd ../legacy
docker compose up -d --build

# 3. Verify health
curl http://localhost:8501/_stcore/health

# Expected output: {"status": "ok"}
```

## Health Check

The legacy app exposes a health endpoint at:

```
http://localhost:8501/_stcore/health
```

Expected response when healthy:
```json
{"status": "ok"}
```

## Verification Steps

After rollback, verify the following:

1. **App Accessible**
   ```bash
   curl -I http://localhost:8501
   # Should return HTTP 200
   ```

2. **Health Check**
   ```bash
   curl http://localhost:8501/_stcore/health
   # Should return {"status": "ok"}
   ```

3. **Container Running**
   ```bash
   docker ps | grep zoocari-legacy
   # Should show running container
   ```

4. **Logs Clean**
   ```bash
   docker logs zoocari-legacy
   # Should show Streamlit startup messages, no errors
   ```

5. **Vector Database Accessible**
   ```bash
   docker exec zoocari-legacy python -c "import lancedb; db = lancedb.connect('data/zoo_lancedb'); print(f'Rows: {db.open_table(\"animals\").count_rows()}')"
   # Should print row count (e.g., "Rows: 150")
   ```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs zoocari-legacy

# Common issues:
# - Missing OPENAI_API_KEY
# - Port 8501 already in use
# - Data directory permissions
```

### Health Check Fails

```bash
# Wait for full startup (can take 60-90 seconds)
# Check if Streamlit is still initializing
docker logs -f zoocari-legacy

# Look for:
# "You can now view your Streamlit app in your browser"
```

### Vector Database Not Found

```bash
# Rebuild knowledge base
docker exec zoocari-legacy python zoo_build_knowledge.py

# This will take 5-10 minutes
```

### Port Conflict

If port 8501 is already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8502:8501"  # Change host port to 8502
```

## Migration Notes

### Data Compatibility

The legacy app uses:
- **LanceDB** for vector database (stored in `data/zoo_lancedb/`)
- **SQLite** for session storage (stored in `data/sessions.db`)

Both are file-based and shared with the new architecture through the `../data/` volume mount.

### TTS Fallback Chain

Legacy app TTS priority:
1. Kokoro (local, 50-200ms) - requires espeak-ng
2. ElevenLabs (cloud, 500-2000ms) - if API key provided
3. OpenAI TTS (cloud, 300-800ms) - fallback

For Docker deployments, OpenAI TTS is recommended (set `TTS_PROVIDER=openai`) due to faster cold starts.

### STT Fallback Chain

Legacy app STT priority:
1. Faster-Whisper (local, ~300ms) - primary
2. OpenAI Whisper API (cloud, ~800ms) - fallback

## Important Constraints

- **Python 3.12+** required for Kokoro TTS compatibility
- **HTTPS required** for browser microphone access in production (use Cloudflare tunnel)
- **Vector database must be built** before running chatbot (run `zoo_build_knowledge.py`)
- **espeak-ng** system dependency required for Kokoro TTS

## Container Architecture

The legacy Dockerfile uses a multi-stage build:

1. **Builder stage** - Compiles dependencies
2. **Runtime stage** - Minimal runtime with espeak-ng
3. **Model pre-download stage** - Caches Kokoro and Faster-Whisper models

Total image size: ~2.5GB (with pre-downloaded models)

## Support & References

- **Main docs**: See project root `CLAUDE.md` and `README.md`
- **Migration plan**: See `migration.md` in project root
- **Original repo**: https://github.com/rodrigjm/zoogpt.git

## Cleanup

To completely remove the legacy app and free up resources:

```bash
# Stop and remove containers
cd legacy
docker compose down

# Remove volumes (WARNING: deletes cached models)
docker volume rm zoocari-legacy-hf-cache zoocari-legacy-torch-cache

# Remove images
docker rmi $(docker images | grep zoocari-legacy | awk '{print $3}')
```

**Note**: The shared `data/` directory is not removed as it's used by both legacy and new architecture.

---

**Last Updated**: 2026-01-10
**Preserved From**: Main branch commit 06759a5 (gpu options script)
**Migration Status**: Phase 0, Task 0.6 - Legacy Preservation
