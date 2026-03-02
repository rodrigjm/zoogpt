# Production Cutover Runbook

**Version:** 1.0
**Last Updated:** 2026-01-12
**Owner:** DevOps Team
**Estimated Duration:** 2-4 hours (including monitoring period)

---

## Table of Contents

1. [Pre-Cutover Checklist](#pre-cutover-checklist)
2. [Cutover Procedure](#cutover-procedure)
3. [Post-Cutover Verification](#post-cutover-verification)
4. [Rollback Procedure](#rollback-procedure)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Emergency Contacts](#emergency-contacts)

---

## Pre-Cutover Checklist

Complete ALL items before starting cutover. DO NOT proceed if any critical item fails.

### Environment Verification

- [ ] **Staging validation complete** - All tests passing in staging environment
  - [ ] API endpoints responding correctly
  - [ ] Chat functionality working
  - [ ] Voice recording/playback working
  - [ ] Session persistence working
  - [ ] TTS/STT working correctly
- [ ] **Production environment ready**
  - [ ] Docker installed and running (`docker --version`)
  - [ ] Docker Compose v2+ installed (`docker compose version`)
  - [ ] Sufficient disk space (>20GB free: `df -h`)
  - [ ] Sufficient memory (>8GB available: `free -h`)
- [ ] **Data directory prepared**
  - [ ] `data/zoo_lancedb/` exists and populated
  - [ ] `data/sessions.db` exists (or will be created)
  - [ ] Directory permissions correct (`ls -la data/`)

### Configuration Verification

- [ ] **Environment file ready**
  - [ ] `docker/.env` file exists
  - [ ] `OPENAI_API_KEY` set and valid
  - [ ] `CORS_ORIGINS` set to production URL
  - [ ] `TTS_PROVIDER` configured (default: kokoro)
  - [ ] `TUNNEL_TOKEN` set if using Cloudflare (optional)
- [ ] **Build artifacts ready**
  - [ ] Frontend built: `apps/web/dist/index.html` exists
  - [ ] Frontend build tested locally
  - [ ] Production Dockerfile tested: `docker/Dockerfile.api`

### Backup & Rollback Readiness

- [ ] **Backup scripts tested**
  - [ ] `scripts/backup.sh` runs successfully
  - [ ] Backup location has sufficient space
  - [ ] Test restore from backup completed
- [ ] **Rollback scripts tested**
  - [ ] `scripts/rollback.sh` runs successfully
  - [ ] Legacy environment still available (if applicable)
  - [ ] Rollback procedure documented and understood
- [ ] **Final backup created**
  - [ ] Run: `./scripts/backup.sh`
  - [ ] Verify backup integrity
  - [ ] Note backup timestamp: `_______________`

### Communication & Timing

- [ ] **Team notified**
  - [ ] Deployment time communicated to team
  - [ ] Key stakeholders informed
  - [ ] On-call engineer available
- [ ] **Maintenance window scheduled**
  - [ ] Start time: `_______________`
  - [ ] Expected end time: `_______________`
  - [ ] User notification sent (if applicable)
- [ ] **Monitoring configured**
  - [ ] Health check endpoint accessible
  - [ ] Log aggregation working
  - [ ] Alert channels tested

### Load Testing & Performance

- [ ] **Load test completed** (`scripts/load-test.sh`)
  - [ ] Error rate <1%
  - [ ] P95 latency <3s
  - [ ] Memory usage stable under load
- [ ] **Performance baseline captured**
  - [ ] Current error rate: `_______________`
  - [ ] Current P95 latency: `_______________`
  - [ ] Current memory usage: `_______________`

---

## Cutover Procedure

**CRITICAL:** Follow steps in exact order. Do NOT skip steps.

### Step 1: Final Pre-Flight Checks

**Duration:** 5 minutes

```bash
# Navigate to project root
cd /path/to/zoocari

# Verify git status (should be clean on deployment branch)
git status
git log -1

# Verify all files present
ls -la docker/
ls -la apps/web/dist/
ls -la data/zoo_lancedb/

# Check current system resources
df -h
free -h
docker ps
```

**Verification:**
- [ ] Git branch is correct (e.g., `main` or `production`)
- [ ] No uncommitted changes
- [ ] All required files present
- [ ] System resources adequate

---

### Step 2: Create Final Backup

**Duration:** 2-5 minutes

```bash
# Create timestamped backup
./scripts/backup.sh

# Verify backup created
ls -lh backups/
```

**Verification:**
- [ ] Backup file created with current timestamp
- [ ] Backup size reasonable (>1MB)
- [ ] Backup location noted: `_______________`

**Rollback Trigger:** If backup fails, STOP and investigate.

---

### Step 3: Stop Legacy System (If Applicable)

**Duration:** 1 minute

```bash
# If running legacy Streamlit app
docker compose -f legacy/docker-compose.yml down

# Verify stopped
docker ps | grep streamlit
# Should return nothing
```

**Verification:**
- [ ] Legacy containers stopped
- [ ] No conflicting ports in use (8000, 8501)

**Note:** Skip this step if running fresh installation.

---

### Step 4: Build Production Images

**Duration:** 5-10 minutes

```bash
# Navigate to docker directory
cd docker/

# Build images (no cache for clean build)
docker compose -f docker-compose.prod.yml build --no-cache

# Verify image built
docker images | grep zoocari
```

**Verification:**
- [ ] Build completed without errors
- [ ] Image size reasonable (<2GB)
- [ ] Image tagged correctly

**Rollback Trigger:** If build fails, check logs and fix issues before proceeding.

---

### Step 5: Start Production Containers

**Duration:** 1 minute

```bash
# Start containers (without Cloudflare by default)
docker compose -f docker-compose.prod.yml up -d

# Verify containers starting
docker ps
docker compose -f docker-compose.prod.yml logs -f
# Watch logs for 30 seconds, then Ctrl+C
```

**Verification:**
- [ ] Containers started successfully
- [ ] No immediate crash loops
- [ ] Logs show normal startup messages

**Rollback Trigger:** If containers fail to start, rollback immediately.

---

### Step 6: Wait for Health Checks

**Duration:** 1-3 minutes

```bash
# Wait for API to be healthy
echo "Waiting for health check..."
for i in {1..20}; do
  if curl -f http://localhost:8000/health 2>/dev/null; then
    echo "Health check passed on attempt $i"
    break
  fi
  echo "Attempt $i failed, waiting 10s..."
  sleep 10
done

# Check final health status
curl -v http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "timestamp": "2026-01-12T..."
}
```

**Verification:**
- [ ] Health check returns HTTP 200
- [ ] Response includes `"status": "ok"`
- [ ] Health check passes within 3 minutes

**Rollback Trigger:** If health check fails after 3 minutes, rollback.

---

### Step 7: Smoke Test Critical Paths

**Duration:** 5-10 minutes

Run each test and verify expected behavior:

#### Test 1: API Root
```bash
curl http://localhost:8000/
```
**Expected:** HTML page with frontend content

#### Test 2: Health Endpoint
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status": "ok", ...}`

#### Test 3: Chat Endpoint (Text)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "smoke-test", "message": "Tell me about lions"}'
```
**Expected:** JSON response with `response`, `followup_questions`, `sources`

#### Test 4: Session Endpoint
```bash
curl http://localhost:8000/api/session?session_id=smoke-test
```
**Expected:** Session info with message_count > 0

#### Test 5: STT Endpoint (if available)
```bash
# Upload a test audio file
curl -X POST http://localhost:8000/api/stt \
  -F "audio=@test_audio.wav"
```
**Expected:** JSON with transcribed text

#### Test 6: Frontend Loading
Open browser: `http://localhost:8000` or production URL

**Expected:**
- [ ] Page loads without errors
- [ ] Zoocari branding visible
- [ ] Welcome message displays
- [ ] Animal quick buttons visible
- [ ] Voice button visible (on HTTPS)
- [ ] No console errors

**Verification:**
- [ ] All 6 smoke tests pass
- [ ] Response times acceptable (<3s)
- [ ] No errors in docker logs

**Rollback Trigger:** If 2+ critical tests fail, rollback.

---

### Step 8: Update Cloudflare Tunnel (If Applicable)

**Duration:** 5 minutes

```bash
# Start Cloudflare tunnel service
docker compose -f docker-compose.prod.yml --profile cloudflare up -d

# Verify tunnel connected
docker compose -f docker-compose.prod.yml logs cloudflared
```

**Alternative:** Update tunnel configuration in Cloudflare dashboard to point to new deployment.

**Verification:**
- [ ] Tunnel shows "connected" status
- [ ] Production URL resolves correctly
- [ ] HTTPS certificate valid

---

### Step 9: Production Smoke Test

**Duration:** 5 minutes

Test from production URL (not localhost):

1. **Open production URL in browser**
   - [ ] Page loads over HTTPS
   - [ ] No mixed content warnings
   - [ ] Frontend renders correctly

2. **Test chat functionality**
   - [ ] Send text message: "Tell me about lions"
   - [ ] Response received within 3 seconds
   - [ ] Follow-up questions displayed
   - [ ] Sources shown at bottom

3. **Test voice features (mobile device)**
   - [ ] Voice button visible
   - [ ] Microphone permission prompt appears
   - [ ] Can record audio
   - [ ] Transcription works
   - [ ] TTS playback works

**Verification:**
- [ ] All production smoke tests pass
- [ ] No errors in browser console
- [ ] No errors in docker logs

**Rollback Trigger:** If critical functionality broken, rollback.

---

### Step 10: Enable Monitoring

**Duration:** 2 minutes

```bash
# Start monitoring logs
docker compose -f docker-compose.prod.yml logs -f api > logs/cutover.log &

# Monitor health endpoint
watch -n 30 'curl -s http://localhost:8000/health | jq'

# Monitor docker stats
docker stats zoocari-api-prod
```

**Verification:**
- [ ] Log monitoring active
- [ ] Health checks passing every 30s
- [ ] Memory usage stable (<4GB)
- [ ] CPU usage reasonable (<80%)

---

### Step 11: Observe for 30 Minutes

**Duration:** 30 minutes

**During this period:**
- Monitor logs for errors
- Check health endpoint every 5 minutes
- Test a few user interactions manually
- Monitor memory/CPU usage
- Watch for any crashes or restarts

**Metrics to watch:**
- Error rate: Should be <1%
- Response time: P95 <3s
- Memory usage: Should stay below 3GB
- Container restarts: Should be 0

**Verification:**
- [ ] No errors in logs
- [ ] Health checks continuously passing
- [ ] Memory usage stable
- [ ] No container restarts
- [ ] User interactions working

**Rollback Trigger:**
- Error rate >5% for 5+ minutes
- Multiple container crashes
- Memory leak detected (usage growing continuously)
- P95 latency >5s

---

### Step 12: Declare Success

**Duration:** 5 minutes

```bash
# Capture final metrics
docker stats --no-stream zoocari-api-prod
curl http://localhost:8000/health

# Document deployment
echo "Deployment successful at $(date)" >> logs/deployments.log
```

**Final Checklist:**
- [ ] 30 minute observation period complete
- [ ] No critical issues detected
- [ ] All smoke tests passing
- [ ] Monitoring active
- [ ] Rollback procedure ready (just in case)

**Next Steps:**
- Continue monitoring for next 48 hours
- Keep legacy system available for 48 hours (if applicable)
- Notify team of successful deployment
- Update documentation if needed

---

## Post-Cutover Verification

Run these checks at intervals after cutover:

### 1 Hour Post-Cutover

```bash
# Health check
curl http://localhost:8000/health

# Check logs for errors
docker compose -f docker-compose.prod.yml logs api | grep -i error | tail -20

# Verify sessions persisting
curl http://localhost:8000/api/session?session_id=test-session

# Check memory usage
docker stats --no-stream zoocari-api-prod
```

**Verification:**
- [ ] Health check passing
- [ ] No critical errors in logs
- [ ] Sessions persisting correctly
- [ ] Memory usage stable

---

### 4 Hours Post-Cutover

```bash
# Check log files for patterns
tail -100 logs/cutover.log | grep -i "error\|warning\|exception"

# Verify disk space
df -h

# Check container uptime
docker ps --format "table {{.Names}}\t{{.Status}}"

# Test a full user flow
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-4hr", "message": "What animals are at the zoo?"}'
```

**Verification:**
- [ ] No error patterns detected
- [ ] Sufficient disk space (>10GB)
- [ ] Containers running continuously
- [ ] Full user flow working

---

### 24 Hours Post-Cutover

```bash
# Review full logs
docker compose -f docker-compose.prod.yml logs api --since 24h | grep -i error

# Check session database size
ls -lh data/sessions.db

# Verify log rotation working
ls -lh logs/

# Performance check
./scripts/load-test.sh
```

**Verification:**
- [ ] Error rate still <1%
- [ ] Session database growing reasonably
- [ ] Log rotation working (files <10MB)
- [ ] Load test results acceptable

---

### 48 Hours Post-Cutover

```bash
# Final verification before decommissioning legacy
./scripts/staging-validate.sh

# Compare metrics to baseline
# Error rate: Target <1%
# P95 latency: Target <3s
# Memory usage: Target <3GB

# If all checks pass, decommission legacy
docker compose -f legacy/docker-compose.yml down
docker system prune -f
```

**Verification:**
- [ ] All metrics within targets
- [ ] No critical issues reported
- [ ] User feedback positive
- [ ] Ready to decommission legacy

**Final Actions:**
- [ ] Remove legacy containers
- [ ] Archive legacy code (do not delete)
- [ ] Update production documentation
- [ ] Send deployment success notification

---

## Rollback Procedure

### When to Rollback

**IMMEDIATE ROLLBACK** if any of these occur:

1. **Critical Failures**
   - API health check fails for >3 minutes
   - Container crashes repeatedly (>3 times in 10 minutes)
   - Data corruption detected
   - Complete loss of functionality

2. **Performance Degradation**
   - Error rate >5% for >5 minutes
   - P95 latency >5 seconds consistently
   - Memory leak causing OOM
   - CPU pegged at 100% continuously

3. **Functionality Broken**
   - Chat responses failing for all users
   - Voice features completely broken on mobile
   - Session persistence not working
   - Database connection lost

**CONSIDER ROLLBACK** for:
- Error rate 2-5% for >10 minutes
- Intermittent failures affecting >20% of requests
- Degraded performance (P95 latency 3-5s)
- Non-critical features broken

### Quick Rollback (<5 minutes)

**Automated rollback using script:**

```bash
# Run rollback script
cd /path/to/zoocari
./scripts/rollback.sh

# Verify rollback successful
curl http://localhost:8000/health
# OR for legacy Streamlit:
curl http://localhost:8501/_stcore/health

# Monitor logs
docker logs -f [container-name]
```

**The rollback script will:**
1. Stop new containers
2. Restore data from backup
3. Start previous version
4. Verify health checks

**Verification:**
- [ ] Previous version running
- [ ] Health checks passing
- [ ] Functionality restored
- [ ] Data intact

---

### Manual Rollback

If automated rollback fails:

```bash
# Step 1: Stop new containers
cd docker/
docker compose -f docker-compose.prod.yml down

# Step 2: Verify stopped
docker ps | grep zoocari
# Should return nothing

# Step 3: Restore data from backup (if needed)
cd ..
./scripts/backup.sh --restore backups/backup-TIMESTAMP.tar.gz

# Step 4: Start legacy system (if applicable)
docker compose -f legacy/docker-compose.yml up -d

# Step 5: Verify legacy running
curl http://localhost:8501/_stcore/health

# Step 6: Monitor logs
docker compose -f legacy/docker-compose.yml logs -f
```

**Verification:**
- [ ] Legacy containers running
- [ ] Previous functionality restored
- [ ] Users can access application
- [ ] Data restored correctly

---

### Post-Rollback Actions

```bash
# 1. Capture logs for analysis
docker compose -f docker-compose.prod.yml logs > logs/failed-deployment-$(date +%Y%m%d-%H%M%S).log

# 2. Document the failure
echo "Rollback at $(date): [REASON]" >> logs/deployments.log

# 3. Notify team
# Send notification with failure details
```

**Required Actions:**
- [ ] Failure documented in logs
- [ ] Root cause identified
- [ ] Team notified of rollback
- [ ] Post-mortem scheduled
- [ ] Fix identified and tested
- [ ] New deployment scheduled

---

## Monitoring & Alerting

### Key Metrics to Monitor

**Health Check**
```bash
# Every 30 seconds (automated by Docker)
curl http://localhost:8000/health
```
**Alert:** If fails 3 times in a row (90 seconds)

**Error Rate**
```bash
# Check logs for error patterns
docker logs zoocari-api-prod | grep -i "error" | wc -l
```
**Alert:** If >10 errors per minute

**Response Time**
```bash
# Test response time
time curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "monitor", "message": "test"}'
```
**Alert:** If P95 >3 seconds

**Memory Usage**
```bash
# Check memory consumption
docker stats --no-stream zoocari-api-prod | awk '{print $4}'
```
**Alert:** If >3.5GB (approaching 4GB limit)

**Container Status**
```bash
# Check container health
docker ps --filter "name=zoocari" --format "{{.Status}}"
```
**Alert:** If container restarts or becomes unhealthy

---

### Log Locations

- **Container logs:** `docker compose -f docker-compose.prod.yml logs api`
- **Host logs:** `logs/cutover.log`
- **Deployment log:** `logs/deployments.log`
- **Rotated logs:** Check log rotation (10MB max, 3 files)

---

### Useful Monitoring Commands

```bash
# Watch logs in real-time
docker compose -f docker-compose.prod.yml logs -f api

# Filter for errors only
docker compose -f docker-compose.prod.yml logs api | grep -i error

# Check last 100 lines
docker compose -f docker-compose.prod.yml logs --tail 100 api

# Monitor resource usage
docker stats zoocari-api-prod

# Check health endpoint continuously
watch -n 10 'curl -s http://localhost:8000/health | jq'

# Count requests per minute (from logs)
docker logs zoocari-api-prod --since 1m | grep "POST /api/chat" | wc -l
```

---

## Emergency Contacts

**Deployment Team:**
- Primary: [Name] - [Phone] - [Email]
- Secondary: [Name] - [Phone] - [Email]

**On-Call Engineer:**
- Current: [Name] - [Phone] - Available: [Hours]

**Escalation:**
- Technical Lead: [Name] - [Contact]
- Product Owner: [Name] - [Contact]

**External Services:**
- OpenAI Status: https://status.openai.com/
- Cloudflare Status: https://www.cloudflarestatus.com/

---

## Appendix: Command Reference

### Quick Commands

```bash
# Check deployment status
docker compose -f docker/docker-compose.prod.yml ps

# View logs
docker compose -f docker/docker-compose.prod.yml logs api -f

# Restart service
docker compose -f docker/docker-compose.prod.yml restart api

# Check health
curl http://localhost:8000/health

# Run backup
./scripts/backup.sh

# Run rollback
./scripts/rollback.sh

# Test deployment
./scripts/test-deployment.sh
```

### Environment Files

- Production config: `docker/.env`
- Compose file: `docker/docker-compose.prod.yml`
- Dockerfile: `docker/Dockerfile.api`

### Data Locations

- Vector DB: `data/zoo_lancedb/`
- Session DB: `data/sessions.db`
- Backups: `backups/`
- Logs: `logs/`

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | DevOps Agent | Initial production runbook |

