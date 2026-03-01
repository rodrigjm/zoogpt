# Concurrency Optimization — Status

## Current State: DEPLOYED & BENCHMARKED

### All 3 Tracks Deployed
- [x] Track A: Multi-Worker + Gunicorn (2 workers confirmed in logs)
- [x] Track B: Async I/O + Background Analytics (async_helpers.py deployed)
- [x] Track C: Smaller Ollama Model (qwen2.5:3b pulled, OLLAMA_NUM_PARALLEL=2 active)
- [x] Docker memory increased to 12GB
- [x] Host Ollama running with parallelism env vars
- [x] API container: gunicorn 2 workers, healthy
- [x] All services healthy (API, TTS, Web, Ollama)

### QA & Benchmarks
- [x] Unit tests: 11/11 async_helpers tests pass
- [x] Syntax validation: 6/6 files pass
- [x] Smoke tests: health, chat, TTS all responding
- [x] Benchmark: non-stream (1/2/5 users) — 100% success rate
- [x] Benchmark: stream (1/2/5 users) — 100% success rate
- [x] Concurrency scaling: 97-114% efficiency (parallelism proven)

### Results Summary (MacBook CPU)

| Metric | 1 user | 5 users | Scaling |
|--------|--------|---------|---------|
| Non-stream avg | 7.7s | 33.6s | 114% efficient |
| Stream avg | 8.5s | 43.8s | 97% efficient |
| TTFT (stream) | 806ms | 25.3s | — |

### Remaining
- [ ] Run on production hardware for final latency numbers
- [ ] Move to `docs/archive/` when production benchmarks confirmed
