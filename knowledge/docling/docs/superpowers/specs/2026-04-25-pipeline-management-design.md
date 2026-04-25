# Pipeline Management Dashboard — Design Spec

**Date:** 2026-04-25
**Status:** Approved
**Scope:** Admin portal feature — model selection + per-stage benchmarking + cost projection

---

## 1. Overview

A single new "Pipeline" page in the admin portal that lets admins:
1. **Hot-swap** the model/provider for each pipeline stage (STT, LLM/RAG, TTS) at runtime — no container restart
2. **Run per-stage benchmarks** with configurable concurrency and rounds
3. **View benchmark results** (p50/p95/p99 latency, per-request cost)
4. **Project monthly costs** at preset daily volumes (500, 1k, 2k, 5k questions/day)

## 2. Pipeline Stages & Available Models

| Stage | Provider Options | Models |
|-------|-----------------|--------|
| **STT** | faster-whisper (local), openai | whisper-1 |
| **LLM/RAG** | ollama (local), openai | qwen2.5:3b, phi4, llama3.2:3b, gpt-4o-mini, gpt-4o |
| **TTS** | kokoro (local), openai, elevenlabs | af_heart, af_bella, af_nova, af_sarah, am_adam, am_eric (kokoro); nova, shimmer, alloy, echo, onyx (openai) |

The model list per provider is defined in admin-api config and can be extended without code changes.

## 3. Hot-Swap Mechanism

### How it works
1. Admin selects provider/model from dropdown, clicks "Apply"
2. Admin frontend sends `PUT /pipeline/{stage}` to admin-api
3. Admin-api validates the selection and writes to `admin_config.json` under a `pipeline` key:
   ```json
   {
     "pipeline": {
       "stt": { "provider": "faster-whisper", "model": null },
       "llm": { "provider": "ollama", "model": "qwen2.5:3b" },
       "tts": { "provider": "kokoro", "model": "af_heart" }
     }
   }
   ```
4. Main API's `DynamicConfig` already polls `admin_config.json` every 5 seconds
5. Each service reads provider/model from `dynamic_config.pipeline_{stage}` at request time instead of from `settings`

### Fallback behavior
- If `pipeline` key is missing from config, services fall back to current `settings` values (env vars)
- If a selected model is unavailable (e.g., Ollama model not pulled), the service returns an error and the admin dashboard shows the failure — it does NOT silently fall back

### What changes in existing services
- `stt.py`: Read `dynamic_config.stt_provider` instead of `settings.stt_provider`
- `llm.py`: Read `dynamic_config.llm_provider` and `dynamic_config.llm_model` instead of `settings.llm_provider` / `settings.ollama_model`
- `tts.py`: Read `dynamic_config.tts_provider` and `dynamic_config.tts_voice` instead of `settings.tts_provider` / `settings.tts_voice`
- `config.py` `DynamicConfig`: Add property accessors for `pipeline.stt`, `pipeline.llm`, `pipeline.tts`

## 4. Per-Stage Benchmarking

### Benchmark endpoints (admin-api)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /pipeline/{stage}/benchmark` | POST | Start a benchmark run |
| `GET /pipeline/{stage}/benchmark/status` | GET | Poll running benchmark progress |
| `GET /pipeline/{stage}/benchmark/latest` | GET | Get most recent benchmark result for stage |
| `GET /pipeline/{stage}/benchmark/history` | GET | Get all benchmark results for stage |

### Request: `POST /pipeline/{stage}/benchmark`
```json
{
  "concurrency": 5,
  "rounds": 3
}
```
- **concurrency** dropdown options: 1, 5, 10, 20, 50
- **rounds** dropdown options: 1, 3, 5

### Internal benchmark endpoints (main API)

The admin-api calls these to isolate per-stage measurement:

| Endpoint | What it tests | Test payload |
|----------|--------------|--------------|
| `POST /internal/benchmark/stt` | STT only | Pre-recorded test audio clip (~3s) |
| `POST /internal/benchmark/llm` | LLM + RAG only | Random question from test set |
| `POST /internal/benchmark/tts` | TTS only | Fixed text string (~50 words) |

These endpoints are internal-only (not exposed externally). They bypass session management and return timing + token/character counts for cost calculation.

### Execution flow
1. Admin clicks "Run" on a stage card
2. Admin-api receives `POST /pipeline/{stage}/benchmark`
3. Spawns `asyncio.create_task` to run the benchmark in background
4. For each round: fires `concurrency` parallel requests to the internal benchmark endpoint
5. Collects timing data, computes percentiles
6. Writes result to `benchmark_results.json`
7. Dashboard polls `/benchmark/status` for progress (% complete), then fetches `/benchmark/latest`

### Benchmark result schema
```json
{
  "results": [
    {
      "id": "llm_ollama_qwen2.5-3b_20260425T143000Z",
      "stage": "llm",
      "provider": "ollama",
      "model": "qwen2.5:3b",
      "timestamp": "2026-04-25T14:30:00Z",
      "concurrency": 5,
      "rounds": 3,
      "total_requests": 15,
      "metrics": {
        "p50_ms": 1200,
        "p95_ms": 3400,
        "p99_ms": 4100,
        "avg_ms": 1450,
        "min_ms": 890,
        "max_ms": 4500,
        "success_rate": 1.0
      },
      "cost_per_request": 0.002,
      "cost_breakdown": {
        "input_tokens_avg": 450,
        "output_tokens_avg": 120,
        "characters_avg": null,
        "audio_seconds_avg": null
      }
    }
  ]
}
```

### Cost calculation
Pricing constants (from existing `load_test.py`):
- **Embedding input:** $0.13 / 1M tokens
- **GPT-4o-mini input:** $0.15 / 1M tokens
- **GPT-4o-mini output:** $0.60 / 1M tokens
- **Whisper:** $0.006 / minute of audio
- **OpenAI TTS:** $15.00 / 1M characters
- **Local models** (Kokoro, faster-whisper, Ollama): $0.00 API cost

Per-request cost is computed from actual token/character/audio counts returned by the internal benchmark endpoint.

## 5. Monthly Cost Projection

Computed **client-side** in the admin dashboard. Formula:

```
monthly_cost_per_stage = cost_per_request × daily_volume × 30
total_monthly = sum(all stages)
```

### Projection table columns
| Daily Volume | STT Cost | LLM/RAG Cost | TTS Cost | Total / Month |
|-------------|----------|-------------|----------|---------------|
| 500/day | — | — | — | — |
| 1,000/day | — | — | — | — |
| 2,000/day | — | — | — | — |
| 5,000/day | — | — | — | — |

- Values auto-update when benchmark results change or model selection changes
- Local models always show "$0.00" with footnote: "Local model — compute/infra cost not included"
- If no benchmark has been run for a stage, the cost column shows "—" with a prompt to run a benchmark

## 6. UI Design

### Page layout
- **Top:** Page title "Pipeline Management" + health status indicator
- **Middle:** Three stage cards in a horizontal row (responsive — stacks on narrow screens)
- **Bottom:** Monthly cost projection table

### Stage card contents (per card)
1. **Header:** Stage number, name, color-coded badge (STT=blue, LLM=purple, TTS=orange)
2. **Model selection:** Single dropdown with provider as optgroup labels and models as options (e.g., optgroup "Ollama" → qwen2.5:3b, phi4; optgroup "OpenAI" → gpt-4o-mini, gpt-4o) + "Apply" button + status indicator (✓ Active / ⟳ Applying / ✗ Error)
3. **Benchmark results:** p50/p95 latency + per-request cost from latest run, with timestamp
4. **Run benchmark controls:** Concurrency dropdown (1/5/10/20/50) + Rounds dropdown (1/3/5) + "Run" button
5. **Running state:** Progress bar with "Running... 8/15 requests" when benchmark is in progress

### Navigation
- Add "Pipeline" to the admin sidebar nav, between "Dashboard" and "Configuration"

## 7. Files to Create / Modify

### New files
| File | Purpose |
|------|---------|
| `apps/admin-api/routers/pipeline.py` | Pipeline config + benchmark API endpoints |
| `apps/admin-api/models/pipeline.py` | Pydantic models for pipeline config + benchmark |
| `apps/admin-api/services/benchmark.py` | Benchmark execution logic (async tasks) |
| `apps/api/app/routers/benchmark.py` | Internal per-stage benchmark endpoints |
| `apps/admin/src/pages/Pipeline.tsx` | Pipeline management page |
| `apps/admin/src/components/Pipeline/StageCard.tsx` | Individual stage card component |
| `apps/admin/src/components/Pipeline/BenchmarkResults.tsx` | Benchmark metrics display |
| `apps/admin/src/components/Pipeline/CostProjection.tsx` | Monthly cost projection table |
| `apps/admin/src/hooks/usePipeline.ts` | API hooks for pipeline endpoints |
| `data/benchmark_results.json` | Benchmark results storage |

### Modified files
| File | Change |
|------|--------|
| `apps/api/app/config.py` | Add `pipeline` property accessors to `DynamicConfig` |
| `apps/api/app/services/stt.py` | Read provider from `dynamic_config` instead of `settings` |
| `apps/api/app/services/llm.py` | Read provider/model from `dynamic_config` instead of `settings` |
| `apps/api/app/services/tts.py` | Read provider/model from `dynamic_config` instead of `settings` |
| `apps/admin-api/main.py` | Register pipeline router |
| `apps/admin/src/App.tsx` (or router config) | Add Pipeline route |
| `apps/admin/src/components/Layout/` | Add Pipeline to sidebar nav |

## 8. Error Handling

- **Model unavailable:** If admin selects a model that isn't pulled/available, the `PUT /pipeline/{stage}` returns 400 with a clear message. Dashboard shows error inline.
- **Benchmark failure:** If benchmark requests fail (service down, timeout), partial results are still saved with `success_rate < 1.0`. Dashboard shows warning.
- **Concurrent benchmarks:** Only one benchmark per stage can run at a time. Attempting to start a second returns 409 Conflict.
- **Config file corruption:** Same pattern as existing `DynamicConfig` — if `admin_config.json` is invalid, keep previous config and log error.

## 9. Testing Strategy

- **Admin-api unit tests:** Pipeline config CRUD, benchmark result storage/retrieval
- **Integration test:** Model hot-swap end-to-end (change model via admin-api → verify main API uses new model)
- **Benchmark accuracy:** Verify per-stage benchmarks measure only that stage's latency (not E2E)
- **Frontend:** Component tests for StageCard, CostProjection (cost math correctness)
- **Cost calculation:** Unit test that cost projection math matches expected values at each volume tier

## 10. Out of Scope

- Infrastructure/compute cost estimation for local models (only API costs)
- A/B traffic splitting between models
- Automatic model recommendations based on benchmarks
- Benchmark scheduling (cron-based recurring runs)
- Safety model (LlamaGuard) selection — stays as env var for now
