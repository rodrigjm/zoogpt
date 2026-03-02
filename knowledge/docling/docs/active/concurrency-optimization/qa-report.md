# Concurrency Optimization — QA Report

## Date: 2026-03-01

## Test Results

### 1. New async_helpers Unit Tests — 11/11 PASSED
```
tests/test_async_helpers.py::test_run_sync_basic PASSED
tests/test_async_helpers.py::test_run_sync_with_kwargs PASSED
tests/test_async_helpers.py::test_run_sync_exception PASSED
tests/test_async_helpers.py::test_run_sync_does_not_block_loop PASSED
tests/test_async_helpers.py::test_async_wrap_generator_basic PASSED
tests/test_async_helpers.py::test_async_wrap_generator_with_args PASSED
tests/test_async_helpers.py::test_async_wrap_generator_empty PASSED
tests/test_async_helpers.py::test_async_wrap_generator_exception PASSED
tests/test_async_helpers.py::test_fire_and_forget_executes PASSED
tests/test_async_helpers.py::test_fire_and_forget_with_kwargs PASSED
tests/test_async_helpers.py::test_fire_and_forget_error_does_not_propagate PASSED

11 passed in 0.78s
```

### 2. Syntax Validation — 6/6 PASSED
All modified files pass `py_compile`:
- `apps/api/app/utils/async_helpers.py` — OK
- `apps/api/app/routers/chat.py` — OK
- `apps/api/app/routers/voice.py` — OK
- `apps/api/app/services/session.py` — OK
- `apps/api/app/services/analytics.py` — OK
- `apps/api/app/config.py` — OK

### 3. Import Validation — PASSED
```
python -c "from apps.api.app.utils.async_helpers import run_sync, async_wrap_generator, fire_and_forget"
>>> Import successful
```

### 4. Existing Integration Tests — SKIPPED (requires Docker services)
The `apps/api/tests/` suite requires running Ollama, Kokoro-TTS, and other Docker services. These tests should be run post-deploy (`docker compose up` + `pytest apps/api/tests/ -v`).

## Files Changed Summary

### Track A: Multi-Worker + Ollama Tuning
| File | Change |
|------|--------|
| `apps/api/requirements.txt` | Added `gunicorn>=21.0.0` |
| `apps/api/Dockerfile` | CMD → gunicorn with 2 UvicornWorkers |
| `docker-compose.yml` | Added `OLLAMA_NUM_PARALLEL=2`, `OLLAMA_MAX_LOADED_MODELS=1` |
| `docker-compose.yml` | API memory reservation 2G → 3G |
| `apps/api/app/services/session.py` | Added WAL pragmas to `_get_connection()` |
| `apps/api/app/services/analytics.py` | Added WAL pragmas to `_get_connection()` |

### Track B: Async I/O + Background Analytics
| File | Change |
|------|--------|
| `apps/api/app/utils/async_helpers.py` | NEW — `run_sync()`, `async_wrap_generator()`, `fire_and_forget()` |
| `apps/api/app/routers/chat.py` | Wrapped blocking calls, fire-and-forget analytics/history |
| `apps/api/app/routers/voice.py` | Same pattern for session lookup, TTS, analytics |

### Track C: Smaller Ollama Model
| File | Change |
|------|--------|
| `docker-compose.yml` | `OLLAMA_MODEL=phi4` → `OLLAMA_MODEL=qwen2.5:3b` |
| `apps/api/app/config.py` | Default `ollama_model` → `"qwen2.5:3b"` |

### New Test File
| File | Change |
|------|--------|
| `tests/test_async_helpers.py` | NEW — 11 unit tests for async utilities |

## Post-Deploy Verification Checklist
- [ ] `docker compose up --build` succeeds
- [ ] `docker exec zoocari-ollama ollama pull qwen2.5:3b`
- [ ] Chat endpoint returns valid response
- [ ] Streaming chat endpoint returns SSE events
- [ ] TTS endpoint returns audio
- [ ] Run `pytest apps/api/tests/ -v` inside container
- [ ] Run `python tests/benchmark_concurrency.py --concurrency 1 2 5` for latency comparison
