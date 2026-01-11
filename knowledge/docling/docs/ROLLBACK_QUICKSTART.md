# Rollback Quick Reference

Emergency rollback procedure to restore the original Streamlit application.

## One-Command Rollback

From project root:

```bash
./scripts/rollback.sh
```

**Time**: <5 minutes
**Health Check**: Automatic (Streamlit `/_stcore/health`)
**Access**: http://localhost:8501

---

## Manual Rollback

If automated script fails:

```bash
# 1. Stop new containers
cd docker && docker compose down

# 2. Start legacy app
cd ../legacy && docker compose up -d --build

# 3. Verify health
curl http://localhost:8501/_stcore/health
# Expected: {"status": "ok"}
```

---

## Verification Checklist

After rollback, confirm:

- [ ] Container running: `docker ps | grep zoocari-legacy`
- [ ] Health check passes: `curl http://localhost:8501/_stcore/health`
- [ ] App accessible: http://localhost:8501
- [ ] Logs clean: `docker logs zoocari-legacy` (no errors)
- [ ] Vector DB accessible: Check row count in logs

---

## Common Issues

### Port 8501 Already in Use

```bash
# Find process using port
lsof -i :8501

# Or change port in legacy/docker-compose.yml
ports:
  - "8502:8501"
```

### Missing OPENAI_API_KEY

```bash
# Add to .env in project root
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Container Won't Start

```bash
# Check logs for detailed error
docker logs zoocari-legacy

# Rebuild from scratch
cd legacy
docker compose down -v
docker compose up --build
```

### Health Check Timeout

```bash
# Streamlit can take 60-90 seconds to start
# Watch logs for startup message
docker logs -f zoocari-legacy

# Look for: "You can now view your Streamlit app in your browser"
```

---

## Rollback Script Options

```bash
# Standard rollback with health check
./scripts/rollback.sh

# Skip health check (faster, but no verification)
./scripts/rollback.sh --skip-health-check
```

---

## Container Management

```bash
# View logs (live)
docker logs -f zoocari-legacy

# Restart container
cd legacy && docker compose restart

# Stop container
cd legacy && docker compose down

# View container status
docker ps | grep zoocari
```

---

## Data Persistence

The legacy app shares data with the new architecture:

- **Vector DB**: `data/zoo_lancedb/` (LanceDB)
- **Sessions**: `data/sessions.db` (SQLite)

No data migration needed for rollback.

---

## Migration Back to New Architecture

When ready to return to new architecture:

```bash
# 1. Stop legacy
cd legacy && docker compose down

# 2. Start new architecture
cd ../docker && docker compose up -d --build

# 3. Verify new services
curl http://localhost:3000      # Next.js web
curl http://localhost:8000/health  # FastAPI backend
```

---

## Support

For detailed documentation, see:
- `legacy/README.md` - Full legacy app documentation
- `migration.md` - Migration plan and architecture
- `CLAUDE.md` - Project guidelines

---

**Last Updated**: 2026-01-10
**Script Location**: `/scripts/rollback.sh`
**Legacy Location**: `/legacy/`
