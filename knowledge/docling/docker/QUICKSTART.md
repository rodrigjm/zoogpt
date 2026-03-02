# Docker Development - Quick Start

One-page reference for developers to get up and running fast.

## TL;DR

```bash
cd docker
cp .env.example .env
# Add your OPENAI_API_KEY to .env
./dev.sh start
```

Then open:
- Frontend: http://localhost:5173
- API: http://localhost:8000/docs

## Commands

| Command | Description |
|---------|-------------|
| `./dev.sh start` | Start in foreground (Ctrl+C to stop) |
| `./dev.sh up` | Start in background |
| `./dev.sh stop` | Stop services |
| `./dev.sh logs` | View all logs |
| `./dev.sh logs api` | View API logs only |
| `./dev.sh status` | Check service health |
| `./dev.sh shell api` | Open shell in API container |
| `./dev.sh clean` | Stop and remove everything |

## Manual Docker Compose

If you prefer raw docker compose commands:

```bash
# Start
docker compose -f docker/docker-compose.dev.yml up --build

# Start in background
docker compose -f docker/docker-compose.dev.yml up -d --build

# Stop
docker compose -f docker/docker-compose.dev.yml down

# Logs
docker compose -f docker/docker-compose.dev.yml logs -f

# Rebuild
docker compose -f docker/docker-compose.dev.yml up --build --force-recreate
```

## Hot Reload

Hot reload is automatic for both services:

- **Python:** Edit any `.py` file in `apps/api/` → uvicorn auto-reloads
- **React:** Edit any `.tsx` file in `apps/web/` → Vite HMR updates browser

No restart needed!

## Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |

## Troubleshooting

**API won't start:**
```bash
# Check logs
docker compose -f docker/docker-compose.dev.yml logs api

# Most common: Missing OPENAI_API_KEY in docker/.env
```

**Web can't reach API:**
```bash
# Verify API is healthy
curl http://localhost:8000/health

# Should return: {"ok":true}
```

**Port already in use:**
```bash
# Find what's using the port
lsof -i :8000  # or :5173

# Kill it
kill -9 <PID>
```

**Hot reload not working:**
```bash
# Restart services
./dev.sh restart

# Or rebuild from scratch
./dev.sh rebuild
```

## File Structure

```
docker/
├── docker-compose.dev.yml    # Main orchestration file
├── Dockerfile.api.dev        # Python 3.12 + dependencies
├── Dockerfile.web.dev        # Node 20 + Vite
├── .env.example              # Environment template
├── .env                      # Your secrets (git-ignored)
├── dev.sh                    # Helper script
├── README.md                 # Full documentation
├── VERIFICATION.md           # Test checklist
└── QUICKSTART.md             # This file
```

## Data Volumes

The `data/` directory is mounted in the API container:

```
data/
├── zoo_lancedb/     # Vector database
└── sessions.db      # SQLite sessions
```

Changes persist between container restarts.

## Environment Variables

Required in `docker/.env`:

```bash
OPENAI_API_KEY=sk-proj-...
```

Optional (with defaults):

```bash
TTS_PROVIDER=kokoro
TTS_VOICE=af_heart
STT_PROVIDER=faster-whisper
EMBEDDING_MODEL=text-embedding-3-small
```

## Next Steps

- See `README.md` for detailed documentation
- See `VERIFICATION.md` for acceptance criteria testing
- See `docs/integration/CONTRACT.md` for API contracts
