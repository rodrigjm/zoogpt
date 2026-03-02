# Docker Development Setup Verification

This document provides step-by-step verification for Task 0.4 acceptance criteria.

## Prerequisites

Before starting, ensure you have:
- Docker Desktop installed and running
- Git repository cloned
- OPENAI_API_KEY available

## Setup Steps

### 1. Configure Environment

```bash
cd docker
cp .env.example .env
```

Edit `.env` and add your actual OPENAI_API_KEY:
```bash
OPENAI_API_KEY=sk-proj-...
```

### 2. Verify Data Directory

```bash
ls -la ../data/
```

Expected output:
```
drwxr-xr-x  4 user  staff   128 Jan 10 13:02 .
drwxr-xr-x 41 user  staff  1312 Jan 10 18:55 ..
-rw-r--r--  1 user  staff 28672 Jan 10 13:02 sessions.db
drwxr-xr-x  3 user  staff    96 Jan  3 17:44 zoo_lancedb
```

If missing, the vector database needs to be built (separate task).

## Acceptance Criteria Verification

### Criterion 1: `docker compose up` starts both services

```bash
# From project root
docker compose -f docker/docker-compose.dev.yml up --build
```

Expected output:
```
[+] Building ...
[+] Running 3/3
 ✔ Network zoocari          Created
 ✔ Container zoocari-api-dev   Started
 ✔ Container zoocari-web-dev   Started
```

Wait for:
```
zoocari-api-dev  | INFO:     Uvicorn running on http://0.0.0.0:8000
zoocari-web-dev  | VITE v6.0.3  ready in XXX ms
zoocari-web-dev  | ➜  Local:   http://localhost:5173/
```

Verify services:
```bash
# In another terminal
curl http://localhost:8000/health
# Expected: {"ok":true}

curl http://localhost:5173
# Expected: HTML content
```

**Status:** [ ] Pass [ ] Fail

### Criterion 2: Hot reload works for Python changes

With containers running, edit a Python file:

```bash
# Edit apps/api/app/main.py or any route
echo '# test comment' >> ../apps/api/app/main.py
```

Watch API logs:
```bash
docker compose -f docker/docker-compose.dev.yml logs -f api
```

Expected output:
```
zoocari-api-dev  | INFO:     Will watch for changes in these directories: ['/app/apps/api']
zoocari-api-dev  | WARNING:  Detected file change in 'app/main.py'. Reloading...
zoocari-api-dev  | INFO:     Application startup complete.
```

Verification:
- [ ] File change detected within 2 seconds
- [ ] Server reloaded automatically
- [ ] API still responds at http://localhost:8000/health

**Status:** [ ] Pass [ ] Fail

### Criterion 3: Hot reload works for React changes

With containers running, edit a React file:

```bash
# Edit apps/web/src/App.tsx or any component
echo '// test comment' >> ../apps/web/src/App.tsx
```

Watch web logs and browser:
```bash
docker compose -f docker/docker-compose.dev.yml logs -f web
```

Expected behavior:
1. Vite detects change within 1 second
2. Browser auto-updates without refresh (HMR)

Logs should show:
```
zoocari-web-dev  | 12:34:56 PM [vite] hmr update /src/App.tsx
```

Verification:
- [ ] File change detected within 1 second
- [ ] Browser updates automatically
- [ ] Page still loads at http://localhost:5173

**Status:** [ ] Pass [ ] Fail

### Criterion 4: Shared data volume accessible

Verify API can access data directory:

```bash
docker exec zoocari-api-dev ls -la /app/data
```

Expected output:
```
drwxr-xr-x 4 root root  128 Jan 10 13:02 .
drwxr-xr-x 1 root root 4096 Jan 10 19:00 ..
-rw-r--r-- 1 root root 28672 Jan 10 13:02 sessions.db
drwxr-xr-x 3 root root   96 Jan  3 17:44 zoo_lancedb
```

Verify paths in environment:
```bash
docker exec zoocari-api-dev env | grep -E '(LANCEDB|SESSION_DB)'
```

Expected:
```
LANCEDB_PATH=/app/data/zoo_lancedb
SESSION_DB_PATH=/app/data/sessions.db
```

Test data persistence:
```bash
# Create a test file in data directory
echo "test" > ../data/test.txt

# Check it's visible in container
docker exec zoocari-api-dev cat /app/data/test.txt
# Expected: test

# Clean up
rm ../data/test.txt
```

Verification:
- [ ] Data directory mounted correctly
- [ ] Environment variables point to correct paths
- [ ] Files created on host visible in container
- [ ] Files created in container visible on host

**Status:** [ ] Pass [ ] Fail

## Additional Verifications

### Network connectivity

Verify web can reach api by container name:

```bash
docker exec zoocari-web-dev ping -c 2 api
```

Expected:
```
PING api (172.x.x.x): 56 data bytes
64 bytes from 172.x.x.x: seq=0 ttl=64 time=0.XXX ms
```

### Health check

Check API health check is working:

```bash
docker inspect zoocari-api-dev | grep -A 10 Health
```

Expected status: "healthy" after ~10 seconds

### Volume mounts

Verify all expected mounts:

```bash
docker inspect zoocari-api-dev | grep -A 5 Mounts
docker inspect zoocari-web-dev | grep -A 5 Mounts
```

Expected for API:
- Source: .../apps/api → Destination: /app/apps/api
- Source: .../data → Destination: /app/data

Expected for Web:
- Source: .../apps/web → Destination: /app
- Anonymous volume for /app/node_modules

### Environment variables

Verify all required env vars are set:

```bash
docker exec zoocari-api-dev env | grep -E '(API_|OPENAI|TTS|STT|LANCEDB|SESSION|CORS)'
```

Expected:
```
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
OPENAI_API_KEY=sk-...
TTS_PROVIDER=kokoro
STT_PROVIDER=faster-whisper
LANCEDB_PATH=/app/data/zoo_lancedb
SESSION_DB_PATH=/app/data/sessions.db
CORS_ORIGINS=http://localhost:5173,http://web:5173
```

## Troubleshooting Reference

### Issue: API health check fails

**Symptom:**
```
zoocari-api-dev  | ERROR:    [Errno 2] No such file or directory: '/app/data/zoo_lancedb'
```

**Solution:**
LanceDB not built yet. Either:
1. Build it first (separate task), or
2. Comment out LanceDB initialization for now

### Issue: Port conflicts

**Symptom:**
```
Error response from daemon: driver failed programming external connectivity:
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solution:**
```bash
# Find and kill process using port
lsof -i :8000
kill -9 <PID>
```

### Issue: Permission denied on data volume

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/app/data/sessions.db'
```

**Solution:**
```bash
# Fix permissions on host
chmod -R 755 ../data
```

### Issue: Hot reload not working

**API Python:**
1. Verify --reload flag: `docker exec zoocari-api-dev ps aux | grep uvicorn`
2. Check file ownership matches container user
3. Ensure WSL2 users have proper file watching enabled

**Web React:**
1. Check Vite HMR WebSocket connection in browser console
2. Verify VITE_HMR_HOST environment variable
3. Ensure port 5173 is accessible

## Sign-off Checklist

Before marking Task 0.4 complete:

- [ ] All 4 acceptance criteria verified
- [ ] Both services start without errors
- [ ] Hot reload confirmed for both services
- [ ] Data volume accessible and persistent
- [ ] Health check passes
- [ ] Network connectivity confirmed
- [ ] Documentation reviewed (README.md)
- [ ] Helper script tested (dev.sh)

## Cleanup

To stop and remove all containers:

```bash
docker compose -f docker/docker-compose.dev.yml down

# To also remove volumes:
docker compose -f docker/docker-compose.dev.yml down -v
```
