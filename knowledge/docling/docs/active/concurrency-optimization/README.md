# Concurrency Optimization - Active Feature

**Status:** IMPLEMENTED — Pending Deploy & Benchmark Verification
**Created:** 2026-03-01
**Implemented:** 2026-03-01

## Problem
20-second latency with 5 concurrent sessions on CPU-only production hardware.

## Implementation Summary
3 parallel tracks implemented:

| Track | Change | Expected Impact |
|-------|--------|-----------------|
| A: Multi-Worker + Ollama Tuning | Gunicorn 2 workers, OLLAMA_NUM_PARALLEL=2, SQLite WAL | 3-4x throughput |
| B: Async I/O + Background Analytics | `async_helpers.py` wrapping at router layer | 2x concurrency |
| C: Smaller Ollama Model | phi4 → qwen2.5:3b | 2-3x token speed |

## Files
- `design.md` - Full brainstorming analysis with 8 optimization options
- `handoff.md` - Session handoff with implementation details
- `implementation.md` - Track B implementation report
- `qa-report.md` - QA results (11/11 unit tests passed)
- `/tests/benchmark_concurrency.py` - Automated benchmark suite
- `/tests/test_async_helpers.py` - Unit tests for async utilities

## Post-Deploy Verification
```bash
# Build and deploy
docker compose up --build

# Pull new model
docker exec zoocari-ollama ollama pull qwen2.5:3b

# Run benchmark
python tests/benchmark_concurrency.py --base-url http://localhost:8000 --concurrency 1 2 5
```

## Expected Results
| Metric | Before | After |
|--------|--------|-------|
| 1-user latency | ~4-6s | ~1.5-3s |
| 5-user latency | ~20s | ~3-4s |
| Throughput | ~0.25 req/s | ~1.5-2 req/s |
