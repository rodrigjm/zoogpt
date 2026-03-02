# Concurrency Optimization — Session Handoff

## Problem
Zoocari chatbot: 20-second latency with 5 concurrent sessions on CPU-only hardware.

## Root Cause
Single uvicorn worker + all synchronous blocking calls (LLM, LanceDB, SQLite) inside async handlers. Requests serialize — user #5 waits for users #1-4.

## Approved Plan
Full plan at: `/Users/jesus/.claude/plans/jaunty-gliding-peacock.md`

## Implementation Summary — 5 Options, 3 Parallel Tracks

### Track A: Multi-Worker + Ollama Tuning (Options 1 + 4)
**Files to change:**
- `apps/api/requirements.txt` — add `gunicorn>=21.0.0`
- `apps/api/Dockerfile` line 40 — CMD → `gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:8000 --timeout 120 --graceful-timeout 30 --keep-alive 5`
- `docker-compose.yml` Ollama service — add `OLLAMA_NUM_PARALLEL=2` and `OLLAMA_MAX_LOADED_MODELS=1`
- `docker-compose.yml` API service — bump memory reservation 2G → 3G

**Why 2 workers:** Each loads Kokoro+Whisper+Python (~1GB). 2 fits in 4GB limit. With async I/O, 2 workers handle 5+ concurrent users.

### Track B: Async I/O + Background Analytics (Options 2 + 3)
**Files to change:**
- `apps/api/app/utils/async_helpers.py` — **NEW** file with two utilities:
  - `run_sync(func, *args)` — wraps `asyncio.to_thread()`
  - `async_wrap_generator(sync_gen_func, *args)` — runs sync generator in background thread, yields via queue to async generator
- `apps/api/app/routers/chat.py` — wrap all blocking calls:
  - Session lookup, safety validation, RAG search → `await run_sync(...)`
  - LLM streaming → `async for chunk in async_wrap_generator(...)`
  - Analytics/history writes → `asyncio.create_task(run_sync(...))` fire-and-forget
- `apps/api/app/routers/voice.py` — same pattern for `generate_audio_stream()`

**Strategy:** Services (`rag.py`, `llm.py`, `session.py`, `analytics.py`) stay sync. All wrapping happens at the router layer. Zero new dependencies.

### Track C: Smaller Ollama Model (Option 6)
**Files to change:**
- `docker-compose.yml` line 102 — `OLLAMA_MODEL=phi4` → `OLLAMA_MODEL=qwen2.5:3b`
- `apps/api/app/config.py` line 44 — default `ollama_model: str = "qwen2.5:3b"`
- Post-deploy: `docker exec zoocari-ollama ollama pull qwen2.5:3b`

**Why:** phi4 (14B) = ~8-12 tok/s on CPU. qwen2.5:3b = ~25-40 tok/s. For kids' zoo chatbot with RAG grounding, 3B is sufficient.

## Key Architectural Decisions
1. **2 gunicorn workers, not 4** — memory budget constraint (4GB container limit)
2. **Wrap at router layer, not rewrite services** — minimally invasive, no new deps like `aiosqlite`
3. **async_wrap_generator pattern** — thread + queue bridge between sync generators and async event loop
4. **Fire-and-forget analytics** — `asyncio.create_task()` for non-critical post-response SQLite writes

## Critical Code Paths (chat streaming)
```
chat.py:chat_stream() [async]
  → run_sync(_session_service.get_session, ...)        # was blocking
  → run_sync(validate_input, ...)                       # was blocking
  → run_sync(_rag_service.search_context, ...)          # was blocking (LanceDB)
  → async_wrap_generator(generate_response_stream, ...) # was sync for-loop
      → rag.py:_stream_ollama() runs in background thread
      → yields chunks via queue → async generator → SSE
  → asyncio.create_task(run_sync(record_interaction))   # fire-and-forget
  → asyncio.create_task(run_sync(save_message))         # fire-and-forget x2
```

## Workflow Per CLAUDE.md
1. Run 3 subagents in parallel (Tracks A, B, C)
2. QA subagent: unit tests (`test_async_helpers.py`) + existing tests + benchmark
3. Troubleshooting subagent: iterate until tests pass
4. DevOps subagent: build and deploy
5. PM subagent: update ProjectPlan.md

## Expected Results
| Metric | Before | After |
|--------|--------|-------|
| 1-user latency | ~4-6s | ~1.5-3s |
| 5-user latency | ~20s | ~3-4s |
| Throughput | ~0.25 req/s | ~1.5-2 req/s |

## Known Risks & Mitigations
- **OOM with 2 workers** → reduce to `--workers 1`; async I/O alone still helps
- **SQLite "database is locked"** → add `PRAGMA journal_mode=WAL` in session.py:46 and analytics.py:50
- **qwen2.5:3b output format differs** → test follow-up question regex extraction
- **Fire-and-forget task fails silently** → add `task.add_done_callback()` error logging

## Existing Artifacts
- `docs/active/concurrency-optimization/design.md` — full brainstorming analysis with 8 options
- `tests/benchmark_concurrency.py` — automated benchmark (latency, TTFT, P50/P95/P99, throughput)
- `docs/active/concurrency-optimization/README.md` — feature tracking
