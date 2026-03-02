# Zoocari Concurrency Optimization - Brainstorming Analysis

**Problem:** 20-second latency with 5 concurrent sessions (CPU-only production)
**Goal:** Maximize throughput on existing CPU hardware before GPU investment
**Date:** 2026-03-01

---

## Architecture Bottleneck Map

```
User Request → Nginx → FastAPI (1 worker) → [BOTTLENECKS BELOW]
                                              │
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                    Session Check         RAG Search          Safety Check
                    (SQLite SYNC)     (LanceDB SYNC)        (CPU regex)
                    ~5ms              ~100-500ms              ~1ms
                         │                    │
                         └────────┬───────────┘
                                  │
                           LLM Generation
                         (Ollama SYNC stream)
                         ~2,000-8,000ms  ← DOMINANT
                                  │
                           Analytics Write
                          (SQLite SYNC)
                          ~5-15ms
                                  │
                         Optional: TTS
                       (Kokoro CPU SYNC)
                       ~1,000-3,000ms
```

### Why 5 Users = 20 Seconds

| Factor | Impact | Explanation |
|--------|--------|-------------|
| **Single uvicorn worker** | CRITICAL | All requests serialize through 1 event loop |
| **Sync blocking in async handlers** | CRITICAL | `httpx.stream()`, `lancedb.search()`, `sqlite3.connect()` all block the event loop |
| **Ollama single-model inference** | HIGH | phi4 processes 1 request at a time; concurrent requests queue inside Ollama |
| **No `run_in_executor`** | HIGH | CPU-bound and blocking I/O ops run on the main thread |
| **SQLite WAL not configured** | MODERATE | Default journal mode causes write locks |

**Math:** With 1 worker and ~4s average response time, 5 concurrent users = ~20s for the last user in queue. This matches your observation exactly.

---

## Optimization Options (Ranked by Impact/Effort)

### OPTION 1: Multi-Worker Uvicorn + Gunicorn (Est. improvement: 3-4x throughput)

**What:** Run multiple uvicorn workers behind gunicorn process manager.

**Change:** Single line in Dockerfile:
```dockerfile
# FROM:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# TO:
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--timeout", "120", "--graceful-timeout", "30"]
```

**Why it works:** Each worker gets its own process + event loop. Requests distribute across workers. On a 4-core CPU, 4 workers = 4 parallel request pipelines.

**Estimated improvement:**
- 5 concurrent users: 20s → ~5-6s (4 workers handle 4 requests in parallel)
- Throughput: 1 req/4s → ~4 req/4s = **4x improvement**

**Risks:**
- Memory: Each worker loads Kokoro ONNX model (~500MB). 4 workers = ~2GB extra RAM
- LanceDB: File-based DB is safe for concurrent reads but needs care with writes
- Ollama: Still single-model inference (the real bottleneck shifts here)

**Effort:** 15 minutes. Zero code changes.

---

### OPTION 2: Async LLM Calls with `run_in_executor` (Est. improvement: 2-3x latency reduction)

**What:** Wrap all synchronous blocking calls in `asyncio.run_in_executor()` so they don't block the event loop.

**Current problem (chat.py:240):**
```python
# This is an async generator, but _stream_ollama() uses synchronous httpx.stream()
# which BLOCKS the entire event loop during iteration
for chunk_text in _rag_service.generate_response_stream(messages, context):
    yield {"data": chunk.model_dump_json()}
```

**Fix approach:**
```python
# Option A: Use httpx.AsyncClient instead of httpx (preferred)
async with httpx.AsyncClient() as client:
    async with client.stream("POST", url, json=payload) as response:
        async for line in response.aiter_lines():
            yield chunk

# Option B: Wrap sync generator in executor (simpler migration)
import asyncio
loop = asyncio.get_event_loop()
for chunk in await loop.run_in_executor(None, blocking_generator):
    yield chunk
```

**Files to change:**
1. `apps/api/app/services/rag.py` - `_stream_ollama()`, `_stream_openai()`, `search_context()`
2. `apps/api/app/services/llm.py` - `generate_ollama()`, `generate_openai()`
3. `apps/api/app/services/session.py` - All SQLite operations
4. `apps/api/app/services/analytics.py` - `record_interaction()`

**Estimated improvement:**
- Event loop unblocked: other requests (session checks, health checks, SSE keepalives) proceed during LLM generation
- With Option 1 combined: 5 users → ~4-5s (near-linear scaling)

**Effort:** 2-4 hours. Moderate code changes.

---

### OPTION 3: Async Analytics / Background Task Offloading (Est. improvement: 10-15% latency per request)

**What:** Move non-critical work (analytics recording, chat history saves) off the hot path.

**Current problem (chat.py:268-286):**
```python
# These 3 SQLite writes happen AFTER response but BEFORE stream closes
_analytics_service.record_interaction(...)     # ~5-10ms, blocking
_session_service.save_message(...)             # ~5ms, blocking
_session_service.save_message(...)             # ~5ms, blocking
```

**Fix:**
```python
import asyncio

# Fire-and-forget background tasks
asyncio.create_task(asyncio.to_thread(
    _analytics_service.record_interaction, ...
))
asyncio.create_task(asyncio.to_thread(
    _session_service.save_message, session_id, "user", body.message
))
```

**Estimated improvement:**
- Per-request: shaves 15-25ms off each response
- Under load: removes 3 SQLite write locks from the hot path, reducing contention
- Combined with Option 1: eliminates SQLite write lock contention across workers

**Effort:** 30 minutes. Minimal code changes.

---

### OPTION 4: Ollama Concurrency Tuning (Est. improvement: 2-3x for LLM-bound requests)

**What:** Configure Ollama to handle parallel inference requests.

**Current:** Ollama defaults to processing 1 request at a time. Additional requests queue.

**Fix (docker-compose.yml):**
```yaml
ollama:
  environment:
    - OLLAMA_KEEP_ALIVE=24h
    - OLLAMA_NUM_PARALLEL=2         # Process 2 requests concurrently
    - OLLAMA_MAX_LOADED_MODELS=1    # Keep 1 model loaded (phi4)
```

**How it works:** Ollama can interleave KV-cache for multiple requests on the same model, sharing weights but maintaining separate contexts. On CPU, this increases memory usage but allows concurrent generation.

**Estimated improvement:**
- 2 concurrent LLM requests processed simultaneously
- Per-user latency increase: ~20-30% (shared CPU), but total throughput: ~1.6-1.8x
- 5 users: 20s → ~12s (2 parallel slots instead of 1)

**Tradeoff:** Each individual request is ~20-30% slower due to CPU sharing, but total queue time drops significantly.

**Effort:** 5 minutes. Config change only.

---

### OPTION 5: Response Caching for Common Questions (Est. improvement: 50-80% for cache hits)

**What:** Cache RAG+LLM responses for frequently asked questions. Zoo chatbot has a finite knowledge domain - kids ask the same questions repeatedly.

**Implementation:**
```python
from functools import lru_cache
import hashlib

# Simple in-memory cache (or Redis for multi-worker)
_response_cache: dict[str, tuple[str, list, float]] = {}

def search_and_generate(query: str) -> tuple[str, list, float]:
    # Normalize query for cache key
    cache_key = hashlib.md5(query.lower().strip().encode()).hexdigest()

    if cache_key in _response_cache:
        return _response_cache[cache_key]

    # ... normal RAG + LLM flow ...

    # Cache for 1 hour (responses don't change often for zoo facts)
    _response_cache[cache_key] = (response, sources, confidence)
    return response, sources, confidence
```

**More sophisticated: Semantic cache using LanceDB embeddings:**
- Before LLM call, check if a similar question (cosine similarity > 0.95) was answered recently
- Return cached response if found
- LanceDB search is already happening - add a `recent_responses` table

**Estimated improvement:**
- Cache hit rate for zoo Q&A: estimated 30-50% (kids ask similar questions)
- Cache hits: ~50ms instead of ~4000ms = **80x faster for cached queries**
- Effective throughput with 40% cache hit: ~1.7x improvement

**Effort:** 1-2 hours for basic cache. 4-6 hours for semantic cache.

---

### OPTION 6: Smaller/Faster Ollama Model (Est. improvement: 2-4x LLM speed)

**What:** Switch from `phi4` (14B params) to a smaller model that's faster on CPU.

**Options:**
| Model | Params | CPU Speed (tok/s) | Quality | Est. Response Time |
|-------|--------|-------------------|---------|-------------------|
| phi4 (current) | 14B | ~8-12 tok/s | Excellent | 3-5s |
| phi3.5-mini | 3.8B | ~25-35 tok/s | Good | 1-2s |
| qwen2.5:3b | 3B | ~30-40 tok/s | Good | 0.8-1.5s |
| gemma2:2b | 2B | ~40-50 tok/s | Adequate | 0.5-1s |
| llama3.2:3b | 3B | ~25-35 tok/s | Good | 1-2s |

**For a kids' zoo chatbot:** A 3B model is likely sufficient. The RAG context provides the factual grounding; the LLM just needs to rephrase it in a kid-friendly tone.

**Estimated improvement:**
- Per-request: 4s → 1-2s = **2-3x faster**
- 5 concurrent: 20s → ~5-8s with multi-worker
- Memory savings: phi4 uses ~8GB, 3B model uses ~2GB → can run MORE workers

**Effort:** 5 minutes. Change `OLLAMA_MODEL=phi3.5-mini` in docker-compose.

---

### OPTION 7: SQLite WAL Mode + Connection Pooling (Est. improvement: 5-10% under load)

**What:** Enable WAL (Write-Ahead Logging) for SQLite to allow concurrent reads during writes.

**Current:** Default journal mode blocks all reads during writes.

**Fix (session.py):**
```python
@contextmanager
def _get_connection(self):
    conn = sqlite3.connect(str(self.db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")      # Enable WAL
    conn.execute("PRAGMA busy_timeout=5000")      # 5s busy wait
    conn.execute("PRAGMA synchronous=NORMAL")     # Faster writes
    try:
        yield conn
    finally:
        conn.close()
```

**Estimated improvement:**
- Eliminates write-lock contention between workers
- Read operations no longer blocked by concurrent writes
- Under 5 concurrent users: ~5-10% improvement on session/analytics operations

**Effort:** 10 minutes.

---

### OPTION 8: Kokoro TTS Sidecar for All Endpoints (Est. improvement: frees CPU for LLM)

**What:** Route ALL TTS requests through the `kokoro-tts` Docker sidecar instead of running Kokoro ONNX in the API process.

**Current:** The API process loads its own Kokoro ONNX model (~500MB) and runs inference on the same CPU as LLM/RAG operations.

**Fix:** Configure the TTS service to always use the HTTP sidecar:
```python
# In tts.py - always use sidecar, never local ONNX
async def synthesize(text, voice, speed):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.kokoro_tts_url}/v1/audio/speech",
            json={"input": text, "voice": voice, "speed": speed}
        )
        return response.content
```

**Estimated improvement:**
- Frees ~500MB RAM in the API container (for more workers)
- Isolates CPU-bound TTS to its own container/cores
- TTS no longer competes with LLM inference for CPU time

**Effort:** 1 hour.

---

## Recommended Implementation Order

| Priority | Option | Impact | Effort | Combined Effect |
|----------|--------|--------|--------|-----------------|
| **1** | Option 1: Multi-worker | 3-4x | 15 min | 20s → ~6s |
| **2** | Option 4: Ollama parallel | 1.5-2x | 5 min | 6s → ~4s |
| **3** | Option 6: Smaller model | 2-3x | 5 min | 4s → ~2s |
| **4** | Option 2: Async I/O | 2x | 2-4 hrs | 2s → ~1.5s |
| **5** | Option 3: Background analytics | 10-15% | 30 min | 1.5s → ~1.3s |
| **6** | Option 5: Response caching | 50-80% hits | 1-2 hrs | ~0.8s avg |
| **7** | Option 7: SQLite WAL | 5-10% | 10 min | minor improvement |
| **8** | Option 8: TTS sidecar | CPU isolation | 1 hr | TTS no longer competes |

**Estimated combined result: 20s → ~1-2s for 5 concurrent users**

---

## Projected Improvement Summary

```
CURRENT STATE (baseline):
  1 user:  ~4 seconds
  5 users: ~20 seconds (serial queue)

AFTER OPTIONS 1+4+6 (30 minutes work):
  1 user:  ~1.5 seconds
  5 users: ~3-4 seconds

AFTER ALL OPTIONS (1 day work):
  1 user:  ~0.8 seconds (cache hit) / ~1.5s (cache miss)
  5 users: ~1-2 seconds
  10 users: ~2-4 seconds
```

---

## Benchmarking Test Suite

See `tests/benchmark_concurrency.py` for the automated benchmark script that measures:
1. Single-user baseline latency
2. Concurrent user latency (1, 2, 5, 10, 15 users)
3. Time-to-first-token (streaming)
4. TTS latency (if enabled)
5. P50/P95/P99 latencies
6. Throughput (requests/second)
