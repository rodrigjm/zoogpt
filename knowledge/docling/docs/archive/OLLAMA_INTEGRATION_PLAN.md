# Ollama + Phi-4 Integration Plan

> Status: COMPLETE
> Created: January 2026
> Completed: January 2026

## Objective

Replace OpenAI API calls with local Ollama inference (Phi-4 for LLM, LlamaGuard for safety) while maintaining OpenAI as fallback.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   web       │    api      │ kokoro-tts  │     ollama       │
│  (React)    │  (FastAPI)  │   (TTS)     │  (Phi-4 + Guard) │
└─────────────┴──────┬──────┴─────────────┴────────┬─────────┘
                     │                              │
                     │  1. Try Ollama (local)       │
                     ├─────────────────────────────►│
                     │                              │
                     │  2. Fallback to OpenAI       │
                     ├─────────────────────────────►  (external)
```

---

## Phase 1: Parallel Implementation Tasks

### Task 1A: DevOps - Docker/Infrastructure ✅
**Subagent**: `devops`
**Files**: `docker-compose.yml`, `.env.example`

- [x] Add Ollama service to docker-compose.yml
- [x] Configure volume for model persistence
- [x] Add health check for Ollama
- [x] Add environment variables (LLM_PROVIDER, OLLAMA_URL, OLLAMA_MODEL)
- [x] Update .env.example with new variables

### Task 1B: Backend - RAG Service Integration ✅
**Subagent**: `backend`
**Files**: `apps/api/app/services/rag.py`, `apps/api/app/services/llm.py` (new)

- [x] Create LLM abstraction service (llm.py)
- [x] Implement Ollama client with retry logic
- [x] Implement local-first, OpenAI fallback pattern
- [x] Update RAG service to use LLM abstraction
- [x] Add model preloading at startup

### Task 1C: Backend - Safety Service Integration ✅
**Subagent**: `backend`
**Files**: `apps/api/app/services/safety.py`

- [x] Add LlamaGuard local moderation function
- [x] Add prompt injection detection patterns
- [x] Implement local-first, OpenAI fallback for moderation
- [x] Add topic restriction check for zoo content

---

## Phase 2: QA & Troubleshooting (Iterative) ✅

### QA Checks
- [x] Unit tests for LLM service
- [x] Unit tests for safety guardrails
- [x] Integration test: Ollama health check
- [x] Integration test: LLM generation with fallback
- [x] Integration test: Safety check with fallback
- [x] E2E test: Full chat flow with local inference

### Acceptance Criteria
1. ✅ Ollama container starts and serves Phi-4
2. ✅ RAG responses work with Ollama (latency < 500ms for simple Q&A)
3. ✅ Safety checks work with LlamaGuard locally
4. ✅ Fallback to OpenAI works when Ollama unavailable
5. ✅ All existing tests pass

---

## Phase 3: DevOps Buildout & Deploy ✅

- [x] Build and test docker-compose locally
- [x] Verify model download/caching works
- [x] Document deployment steps
- [x] Update STATUS.md

---

## Configuration

### Environment Variables (New)
```bash
# LLM Provider
LLM_PROVIDER=ollama          # ollama | openai
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=phi4
OLLAMA_GUARD_MODEL=llama-guard3:1b

# Fallback behavior
LLM_FALLBACK_ENABLED=true    # Fall back to OpenAI if Ollama fails
```

### Docker Resources
```yaml
ollama:
  deploy:
    resources:
      limits:
        memory: 8G
      reservations:
        memory: 4G
```

---

## Rollback Plan

If issues arise:
1. Set `LLM_PROVIDER=openai` to bypass Ollama
2. Or remove `ollama` from `depends_on` in api service
3. Existing OpenAI code paths remain functional

---

## Status Updates

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1A (DevOps) | ✅ COMPLETE | Ollama service added to docker-compose.yml |
| Phase 1B (RAG) | ✅ COMPLETE | LLM service with Ollama + OpenAI fallback |
| Phase 1C (Safety) | ✅ COMPLETE | LlamaGuard integration complete |
| Phase 2 (QA) | ✅ COMPLETE | All tests passing |
| Phase 3 (Deploy) | ✅ COMPLETE | Docker build verified, docs updated |

---

## Deployment Instructions

### First Time Setup
```bash
# Navigate to project directory
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling

# Pull Ollama models (one-time)
docker compose up -d ollama
docker compose exec ollama ollama pull phi4
docker compose exec ollama ollama pull llama-guard3:1b
```

### Normal Startup
```bash
# Start all services
docker compose up -d

# Check service health
docker compose ps
docker compose logs -f ollama api
```

### Quick Commands
```bash
# Start with admin portal
docker compose --profile admin up -d

# Stop all services
docker compose down

# Remove volumes (reset models)
docker compose down -v
```

### Verification
```bash
# Check Ollama is serving models
curl http://localhost:11434/api/tags

# Check API health
curl http://localhost:8000/health

# View API logs for Ollama usage
docker compose logs api | grep -i ollama
```
