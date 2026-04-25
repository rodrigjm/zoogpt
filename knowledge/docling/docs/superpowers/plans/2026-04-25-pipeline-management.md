# Pipeline Management Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Pipeline page to the admin portal where admins can hot-swap models per pipeline stage (STT, LLM, TTS), run per-stage benchmarks, and view monthly cost projections.

**Architecture:** Extends existing `DynamicConfig` polling pattern with a `pipeline` key in `admin_config.json`. Admin-api gets a `/pipeline/` router for model config and benchmark execution (asyncio background tasks). Main API gets internal `/internal/benchmark/` endpoints for isolated per-stage measurement. Admin frontend gets a new Pipeline page with StageCard components.

**Tech Stack:** Python/FastAPI (admin-api + main API), React/TypeScript/Tailwind (admin frontend), Pydantic models, pytest/pytest-asyncio, aiohttp for benchmark client

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `apps/admin-api/models/pipeline.py` | Pydantic models: PipelineStageConfig, BenchmarkRequest, BenchmarkResult, BenchmarkStatus |
| `apps/admin-api/routers/pipeline.py` | Admin API endpoints: GET/PUT pipeline config per stage, POST/GET benchmark |
| `apps/admin-api/services/benchmark.py` | Benchmark execution logic: run concurrent requests, compute percentiles, write results |
| `apps/api/app/routers/benchmark.py` | Internal per-stage benchmark endpoints (STT/LLM/TTS isolation) |
| `apps/admin/src/pages/Pipeline.tsx` | Pipeline management page — orchestrates StageCards + CostProjection |
| `apps/admin/src/components/Pipeline/StageCard.tsx` | Individual stage card: model dropdown, benchmark results, run controls |
| `apps/admin/src/components/Pipeline/CostProjection.tsx` | Monthly cost projection table |
| `tests/admin-api/test_pipeline_router.py` | Admin-api pipeline endpoint tests |
| `tests/admin-api/test_benchmark_service.py` | Benchmark service unit tests |
| `tests/api/test_benchmark_router.py` | Internal benchmark endpoint tests |

### Modified Files

| File | Change |
|------|--------|
| `apps/api/app/config.py` | Add pipeline property accessors to DynamicConfig |
| `apps/api/app/services/llm.py` | Read provider/model from dynamic_config at request time |
| `apps/api/app/services/stt.py` | Read provider from dynamic_config at request time |
| `apps/api/app/services/tts.py` | Read provider from dynamic_config at request time |
| `apps/api/app/main.py` | Register benchmark router |
| `apps/api/app/routers/__init__.py` | Export benchmark_router |
| `apps/admin-api/main.py` | Register pipeline router |
| `apps/admin/src/App.tsx` | Add Pipeline route |
| `apps/admin/src/components/Layout/index.tsx` | Add Pipeline nav item |
| `apps/admin/src/api/client.ts` | Add pipelineApi namespace |
| `apps/admin/src/types/index.ts` | Add pipeline TypeScript types |

---

## Task 1: DynamicConfig Pipeline Accessors

**Files:**
- Modify: `apps/api/app/config.py:147-258`
- Test: `tests/api/test_dynamic_config_pipeline.py` (create)

- [ ] **Step 1: Write failing test for pipeline config accessors**

Create `tests/api/test_dynamic_config_pipeline.py`:

```python
import json
import tempfile
import pytest
from apps.api.app.config import DynamicConfig


@pytest.fixture
def config_with_pipeline(tmp_path):
    config_file = tmp_path / "admin_config.json"
    config_file.write_text(json.dumps({
        "version": "1.0",
        "pipeline": {
            "stt": {"provider": "openai", "model": "whisper-1"},
            "llm": {"provider": "ollama", "model": "phi4"},
            "tts": {"provider": "openai", "model": "tts-1"}
        },
        "prompts": {"system_prompt": "test", "fallback_response": "test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
        "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0}
    }))
    return DynamicConfig(config_path=str(config_file), poll_interval=0)


@pytest.fixture
def config_without_pipeline(tmp_path):
    config_file = tmp_path / "admin_config.json"
    config_file.write_text(json.dumps({
        "version": "1.0",
        "prompts": {"system_prompt": "test", "fallback_response": "test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
        "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0}
    }))
    return DynamicConfig(config_path=str(config_file), poll_interval=0)


def test_pipeline_stt_provider(config_with_pipeline):
    assert config_with_pipeline.pipeline_stt_provider == "openai"


def test_pipeline_stt_model(config_with_pipeline):
    assert config_with_pipeline.pipeline_stt_model == "whisper-1"


def test_pipeline_llm_provider(config_with_pipeline):
    assert config_with_pipeline.pipeline_llm_provider == "ollama"


def test_pipeline_llm_model(config_with_pipeline):
    assert config_with_pipeline.pipeline_llm_model == "phi4"


def test_pipeline_tts_provider(config_with_pipeline):
    assert config_with_pipeline.pipeline_tts_provider == "openai"


def test_pipeline_tts_model(config_with_pipeline):
    assert config_with_pipeline.pipeline_tts_model == "tts-1"


def test_pipeline_fallback_to_settings_defaults(config_without_pipeline):
    """When pipeline key is missing, return None so services use settings."""
    assert config_without_pipeline.pipeline_stt_provider is None
    assert config_without_pipeline.pipeline_llm_provider is None
    assert config_without_pipeline.pipeline_tts_provider is None
    assert config_without_pipeline.pipeline_llm_model is None


def test_pipeline_hot_reload(tmp_path):
    """Config updates when file changes."""
    config_file = tmp_path / "admin_config.json"
    config_file.write_text(json.dumps({
        "version": "1.0",
        "pipeline": {
            "llm": {"provider": "ollama", "model": "qwen2.5:3b"}
        },
        "prompts": {"system_prompt": "t", "fallback_response": "t"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
        "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0}
    }))
    dc = DynamicConfig(config_path=str(config_file), poll_interval=0)
    assert dc.pipeline_llm_model == "qwen2.5:3b"

    # Update file
    import time
    time.sleep(0.1)  # ensure mtime changes
    config_file.write_text(json.dumps({
        "version": "1.0",
        "pipeline": {
            "llm": {"provider": "ollama", "model": "phi4"}
        },
        "prompts": {"system_prompt": "t", "fallback_response": "t"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
        "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0}
    }))
    assert dc.pipeline_llm_model == "phi4"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -m pytest tests/api/test_dynamic_config_pipeline.py -v`
Expected: FAIL — `DynamicConfig` has no `pipeline_stt_provider` attribute

- [ ] **Step 3: Add pipeline property accessors to DynamicConfig**

In `apps/api/app/config.py`, add these properties after the existing `tts_speed` property (after line 253):

```python
    # Pipeline stage accessors (hot-swap support)
    @property
    def pipeline_stt_provider(self) -> str | None:
        """Get pipeline STT provider override. None = use settings default."""
        return self._get_nested("pipeline", "stt", "provider", default=None)

    @property
    def pipeline_stt_model(self) -> str | None:
        """Get pipeline STT model override."""
        return self._get_nested("pipeline", "stt", "model", default=None)

    @property
    def pipeline_llm_provider(self) -> str | None:
        """Get pipeline LLM provider override."""
        return self._get_nested("pipeline", "llm", "provider", default=None)

    @property
    def pipeline_llm_model(self) -> str | None:
        """Get pipeline LLM model override."""
        return self._get_nested("pipeline", "llm", "model", default=None)

    @property
    def pipeline_tts_provider(self) -> str | None:
        """Get pipeline TTS provider override."""
        return self._get_nested("pipeline", "tts", "provider", default=None)

    @property
    def pipeline_tts_model(self) -> str | None:
        """Get pipeline TTS model override."""
        return self._get_nested("pipeline", "tts", "model", default=None)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -m pytest tests/api/test_dynamic_config_pipeline.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/config.py tests/api/test_dynamic_config_pipeline.py
git commit -m "feat: add pipeline stage accessors to DynamicConfig for hot-swap"
```

---

## Task 2: Wire Services to Read from DynamicConfig

**Files:**
- Modify: `apps/api/app/services/llm.py:9,48-54,103-119`
- Modify: `apps/api/app/services/stt.py:17`
- Modify: `apps/api/app/services/tts.py:19`

- [ ] **Step 1: Update LLM service to use dynamic_config**

In `apps/api/app/services/llm.py`:

Change line 9 import:
```python
from ..config import settings, dynamic_config
```

In `LLMService.__init__` (lines 51-54), remove the cached `self.ollama_model`:
```python
    def __init__(self, openai_api_key: str):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.ollama_url = settings.ollama_url
```

In `generate_ollama` (line 63), read model dynamically:
```python
    async def generate_ollama(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate using local Ollama."""
        model = dynamic_config.pipeline_llm_model or settings.ollama_model
        timed_print(f"  [LLM] Ollama generating ({model})...")

        client = _get_async_httpx_client()
        response = await client.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
        )
        response.raise_for_status()
        result = response.json()["message"]["content"]
        timed_print(f"  [LLM] Ollama done: {len(result)} chars")
        return result
```

In `generate` method (lines 103-119), read provider dynamically:
```python
    async def generate(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate with local-first, cloud fallback."""
        provider = dynamic_config.pipeline_llm_provider or settings.llm_provider

        # Try Ollama first if configured
        if provider == "ollama" and await is_ollama_available():
            try:
                return await self.generate_ollama(messages, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Ollama failed, falling back to OpenAI: {e}")

        # Use OpenAI (either as primary or fallback)
        openai_model = dynamic_config.pipeline_llm_model or model
        return await self.generate_openai(messages, openai_model, temperature, max_tokens)
```

- [ ] **Step 2: Update STT service to use dynamic_config**

In `apps/api/app/services/stt.py`, change line 17:
```python
from ..config import settings, dynamic_config
```

Find the function that decides which STT provider to use (the main transcribe function) and change the provider check from `settings.stt_provider` to:
```python
provider = dynamic_config.pipeline_stt_provider or settings.stt_provider
```

- [ ] **Step 3: Update TTS service**

In `apps/api/app/services/tts.py`, the import at line 19 already has `dynamic_config`. Find the main synthesis function and update the provider check:
```python
provider = dynamic_config.pipeline_tts_provider or settings.tts_provider
voice = dynamic_config.pipeline_tts_model or dynamic_config.tts_default_voice
```

- [ ] **Step 4: Smoke test — verify app still starts**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -c "from apps.api.app.services.llm import LLMService; print('LLM import OK')"`
Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -c "from apps.api.app.services.stt import *; print('STT import OK')"`
Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -c "from apps.api.app.services.tts import *; print('TTS import OK')"`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/llm.py apps/api/app/services/stt.py apps/api/app/services/tts.py
git commit -m "feat: wire services to read provider/model from DynamicConfig for hot-swap"
```

---

## Task 3: Admin-API Pydantic Models

**Files:**
- Create: `apps/admin-api/models/pipeline.py`

- [ ] **Step 1: Create pipeline models**

Create `apps/admin-api/models/pipeline.py`:

```python
"""Pydantic models for pipeline management endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PipelineStageConfig(BaseModel):
    """Configuration for a single pipeline stage."""
    provider: str
    model: Optional[str] = None


class PipelineConfig(BaseModel):
    """Full pipeline configuration across all stages."""
    stt: PipelineStageConfig
    llm: PipelineStageConfig
    tts: PipelineStageConfig


class PipelineStageUpdate(BaseModel):
    """Request to update a single stage's provider/model."""
    provider: str
    model: Optional[str] = None


class BenchmarkRequest(BaseModel):
    """Request to start a benchmark run."""
    concurrency: int = Field(5, description="Number of concurrent requests")
    rounds: int = Field(3, description="Number of rounds to run")


class BenchmarkMetrics(BaseModel):
    """Latency percentiles and success rate."""
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    success_rate: float


class CostBreakdown(BaseModel):
    """Per-request cost breakdown with token/char counts."""
    input_tokens_avg: Optional[float] = None
    output_tokens_avg: Optional[float] = None
    characters_avg: Optional[float] = None
    audio_seconds_avg: Optional[float] = None


class BenchmarkResult(BaseModel):
    """Result of a completed benchmark run."""
    id: str
    stage: str
    provider: str
    model: Optional[str]
    timestamp: str
    concurrency: int
    rounds: int
    total_requests: int
    metrics: BenchmarkMetrics
    cost_per_request: float
    cost_breakdown: CostBreakdown


class BenchmarkStatus(BaseModel):
    """Status of a running or completed benchmark."""
    stage: str
    running: bool
    progress: Optional[str] = None  # e.g., "8/15 requests"
    completed_requests: int = 0
    total_requests: int = 0
    result: Optional[BenchmarkResult] = None


# Available models per provider per stage
AVAILABLE_MODELS = {
    "stt": {
        "faster-whisper": [{"id": "base", "name": "Base (local)", "description": "Fast, free, offline"}],
        "openai": [{"id": "whisper-1", "name": "Whisper v1", "description": "OpenAI cloud STT"}],
    },
    "llm": {
        "ollama": [
            {"id": "qwen2.5:3b", "name": "Qwen 2.5 3B", "description": "Fast, lightweight"},
            {"id": "phi4", "name": "Phi-4", "description": "Microsoft, good reasoning"},
            {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "description": "Meta, general purpose"},
        ],
        "openai": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Fast, cheap"},
            {"id": "gpt-4o", "name": "GPT-4o", "description": "Most capable, higher cost"},
        ],
    },
    "tts": {
        "kokoro": [
            {"id": "af_heart", "name": "Heart", "description": "Expressive, upbeat female"},
            {"id": "af_bella", "name": "Bella", "description": "Friendly female"},
            {"id": "af_nova", "name": "Nova", "description": "Warm, engaging female"},
            {"id": "af_sarah", "name": "Sarah", "description": "Calm, gentle female"},
            {"id": "am_adam", "name": "Adam", "description": "Clear male voice"},
            {"id": "am_eric", "name": "Eric", "description": "Friendly male"},
        ],
        "openai": [
            {"id": "tts-1", "name": "TTS-1", "description": "Standard quality"},
        ],
        "elevenlabs": [
            {"id": "default", "name": "Default", "description": "ElevenLabs default voice"},
        ],
    },
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/admin-api/models/pipeline.py
git commit -m "feat: add Pydantic models for pipeline config and benchmarks"
```

---

## Task 4: Benchmark Service

**Files:**
- Create: `apps/admin-api/services/benchmark.py`
- Test: `tests/admin-api/test_benchmark_service.py` (create)

- [ ] **Step 1: Write failing test for benchmark service**

Create `tests/admin-api/test_benchmark_service.py`:

```python
import json
import pytest
import statistics
from pathlib import Path
from apps.admin_api.services.benchmark import (
    compute_percentiles,
    calculate_cost_per_request,
    BenchmarkResultStore,
)


def test_compute_percentiles():
    latencies = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    result = compute_percentiles(latencies)
    assert result["p50_ms"] == pytest.approx(550, abs=50)
    assert result["p95_ms"] == pytest.approx(950, abs=50)
    assert result["p99_ms"] == pytest.approx(990, abs=20)
    assert result["avg_ms"] == pytest.approx(550, abs=1)
    assert result["min_ms"] == 100
    assert result["max_ms"] == 1000


def test_compute_percentiles_single_value():
    result = compute_percentiles([250])
    assert result["p50_ms"] == 250
    assert result["p95_ms"] == 250
    assert result["avg_ms"] == 250


def test_calculate_cost_local_model():
    cost = calculate_cost_per_request("llm", "ollama", "qwen2.5:3b", {})
    assert cost == 0.0


def test_calculate_cost_openai_llm():
    cost = calculate_cost_per_request("llm", "openai", "gpt-4o-mini", {
        "input_tokens_avg": 450,
        "output_tokens_avg": 120,
    })
    # (450 * 0.15 / 1_000_000) + (120 * 0.60 / 1_000_000)
    expected = (450 * 0.15 + 120 * 0.60) / 1_000_000
    assert cost == pytest.approx(expected, rel=0.01)


def test_calculate_cost_openai_tts():
    cost = calculate_cost_per_request("tts", "openai", "tts-1", {
        "characters_avg": 200,
    })
    expected = 200 * 15.00 / 1_000_000
    assert cost == pytest.approx(expected, rel=0.01)


def test_calculate_cost_openai_stt():
    cost = calculate_cost_per_request("stt", "openai", "whisper-1", {
        "audio_seconds_avg": 3.0,
    })
    expected = (3.0 / 60.0) * 0.006
    assert cost == pytest.approx(expected, rel=0.01)


def test_result_store_save_and_load(tmp_path):
    store = BenchmarkResultStore(results_path=str(tmp_path / "results.json"))
    result = {
        "id": "llm_ollama_qwen_123",
        "stage": "llm",
        "provider": "ollama",
        "model": "qwen2.5:3b",
        "timestamp": "2026-04-25T14:00:00Z",
        "concurrency": 5,
        "rounds": 3,
        "total_requests": 15,
        "metrics": {
            "p50_ms": 1200, "p95_ms": 3400, "p99_ms": 4100,
            "avg_ms": 1450, "min_ms": 890, "max_ms": 4500,
            "success_rate": 1.0,
        },
        "cost_per_request": 0.0,
        "cost_breakdown": {
            "input_tokens_avg": None, "output_tokens_avg": None,
            "characters_avg": None, "audio_seconds_avg": None,
        },
    }
    store.save_result(result)
    latest = store.get_latest("llm")
    assert latest is not None
    assert latest["id"] == "llm_ollama_qwen_123"


def test_result_store_get_latest_returns_none_for_empty(tmp_path):
    store = BenchmarkResultStore(results_path=str(tmp_path / "results.json"))
    assert store.get_latest("stt") is None


def test_result_store_history(tmp_path):
    store = BenchmarkResultStore(results_path=str(tmp_path / "results.json"))
    for i in range(3):
        store.save_result({
            "id": f"llm_test_{i}",
            "stage": "llm",
            "provider": "ollama",
            "model": "qwen2.5:3b",
            "timestamp": f"2026-04-25T1{i}:00:00Z",
            "concurrency": 5, "rounds": 1, "total_requests": 5,
            "metrics": {"p50_ms": 100, "p95_ms": 200, "p99_ms": 250,
                        "avg_ms": 150, "min_ms": 50, "max_ms": 300, "success_rate": 1.0},
            "cost_per_request": 0.0,
            "cost_breakdown": {"input_tokens_avg": None, "output_tokens_avg": None,
                               "characters_avg": None, "audio_seconds_avg": None},
        })
    history = store.get_history("llm")
    assert len(history) == 3
    # Most recent first
    assert history[0]["id"] == "llm_test_2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -m pytest tests/admin-api/test_benchmark_service.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement benchmark service**

Create `apps/admin-api/services/benchmark.py`:

```python
"""
Benchmark execution service.

Runs per-stage benchmarks by firing concurrent requests at the main API's
internal benchmark endpoints, then computes percentile metrics and cost.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# Pricing constants (from scripts/load_test.py)
PRICING = {
    "embedding_input": 0.13,       # per 1M tokens
    "gpt4o_mini_input": 0.15,      # per 1M input tokens
    "gpt4o_mini_output": 0.60,     # per 1M output tokens
    "gpt4o_input": 2.50,           # per 1M input tokens
    "gpt4o_output": 10.00,         # per 1M output tokens
    "whisper_per_min": 0.006,      # per minute of audio
    "tts_per_1m_chars": 15.00,     # per 1M characters
}

# Local providers have zero API cost
LOCAL_PROVIDERS = {"ollama", "faster-whisper", "kokoro"}


def compute_percentiles(latencies_ms: list[float]) -> dict:
    """Compute p50, p95, p99, avg, min, max from latency list."""
    sorted_lat = sorted(latencies_ms)
    n = len(sorted_lat)

    def percentile(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = int(k)
        c = f + 1
        if c >= n:
            return sorted_lat[-1]
        return sorted_lat[f] + (k - f) * (sorted_lat[c] - sorted_lat[f])

    return {
        "p50_ms": round(percentile(50), 1),
        "p95_ms": round(percentile(95), 1),
        "p99_ms": round(percentile(99), 1),
        "avg_ms": round(statistics.mean(latencies_ms), 1),
        "min_ms": round(min(latencies_ms), 1),
        "max_ms": round(max(latencies_ms), 1),
    }


def calculate_cost_per_request(
    stage: str,
    provider: str,
    model: Optional[str],
    breakdown: dict,
) -> float:
    """Calculate per-request cost based on provider and usage metrics."""
    if provider in LOCAL_PROVIDERS:
        return 0.0

    if stage == "stt" and provider == "openai":
        audio_secs = breakdown.get("audio_seconds_avg") or 0
        return (audio_secs / 60.0) * PRICING["whisper_per_min"]

    if stage == "llm" and provider == "openai":
        input_tokens = breakdown.get("input_tokens_avg") or 0
        output_tokens = breakdown.get("output_tokens_avg") or 0
        if model and "gpt-4o-mini" in model:
            return (input_tokens * PRICING["gpt4o_mini_input"]
                    + output_tokens * PRICING["gpt4o_mini_output"]) / 1_000_000
        else:
            return (input_tokens * PRICING["gpt4o_input"]
                    + output_tokens * PRICING["gpt4o_output"]) / 1_000_000

    if stage == "tts" and provider == "openai":
        chars = breakdown.get("characters_avg") or 0
        return chars * PRICING["tts_per_1m_chars"] / 1_000_000

    return 0.0


class BenchmarkResultStore:
    """Read/write benchmark results to a JSON file."""

    def __init__(self, results_path: str = "data/benchmark_results.json"):
        self._path = Path(results_path)

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        with open(self._path) as f:
            data = json.load(f)
        return data.get("results", [])

    def _save(self, results: list[dict]):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump({"results": results}, f, indent=2)

    def save_result(self, result: dict):
        results = self._load()
        results.append(result)
        self._save(results)

    def get_latest(self, stage: str) -> Optional[dict]:
        results = self._load()
        stage_results = [r for r in results if r["stage"] == stage]
        if not stage_results:
            return None
        return sorted(stage_results, key=lambda r: r["timestamp"], reverse=True)[0]

    def get_history(self, stage: str) -> list[dict]:
        results = self._load()
        stage_results = [r for r in results if r["stage"] == stage]
        return sorted(stage_results, key=lambda r: r["timestamp"], reverse=True)


# Track running benchmarks
_running_benchmarks: dict[str, dict] = {}


def get_benchmark_status(stage: str) -> dict:
    """Get status of a running benchmark for a stage."""
    return _running_benchmarks.get(stage, {
        "stage": stage,
        "running": False,
        "progress": None,
        "completed_requests": 0,
        "total_requests": 0,
        "result": None,
    })


async def run_benchmark(
    stage: str,
    concurrency: int,
    rounds: int,
    main_api_url: str,
    store: BenchmarkResultStore,
    provider: str,
    model: Optional[str],
):
    """
    Run a per-stage benchmark.

    Fires concurrent requests at the main API's internal benchmark endpoint
    and collects latency metrics.
    """
    total_requests = concurrency * rounds
    endpoint = f"{main_api_url}/internal/benchmark/{stage}"

    _running_benchmarks[stage] = {
        "stage": stage,
        "running": True,
        "progress": f"0/{total_requests} requests",
        "completed_requests": 0,
        "total_requests": total_requests,
        "result": None,
    }

    latencies = []
    successes = 0
    token_counts = []  # For LLM: list of {input_tokens, output_tokens}
    char_counts = []   # For TTS: list of character counts
    audio_durations = []  # For STT: list of audio durations

    async with aiohttp.ClientSession() as session:
        for round_num in range(rounds):
            tasks = []
            for _ in range(concurrency):
                tasks.append(_benchmark_request(session, endpoint, stage))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in results:
                if isinstance(r, Exception):
                    logger.warning(f"Benchmark request failed: {r}")
                    continue
                successes += 1
                latencies.append(r["latency_ms"])
                if r.get("input_tokens"):
                    token_counts.append(r)
                if r.get("characters"):
                    char_counts.append(r)
                if r.get("audio_seconds"):
                    audio_durations.append(r)

                _running_benchmarks[stage]["completed_requests"] = len(latencies)
                _running_benchmarks[stage]["progress"] = f"{len(latencies)}/{total_requests} requests"

    if not latencies:
        logger.error(f"All benchmark requests failed for {stage}")
        _running_benchmarks[stage] = {
            "stage": stage, "running": False,
            "progress": "Failed — all requests errored",
            "completed_requests": 0, "total_requests": total_requests, "result": None,
        }
        return

    metrics = compute_percentiles(latencies)
    metrics["success_rate"] = round(successes / total_requests, 3)

    breakdown = {
        "input_tokens_avg": (statistics.mean([t["input_tokens"] for t in token_counts])
                             if token_counts else None),
        "output_tokens_avg": (statistics.mean([t["output_tokens"] for t in token_counts])
                              if token_counts else None),
        "characters_avg": (statistics.mean([t["characters"] for t in char_counts])
                           if char_counts else None),
        "audio_seconds_avg": (statistics.mean([t["audio_seconds"] for t in audio_durations])
                              if audio_durations else None),
    }

    cost = calculate_cost_per_request(stage, provider, model, breakdown)
    model_slug = (model or "default").replace(":", "-").replace(".", "-")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    result = {
        "id": f"{stage}_{provider}_{model_slug}_{ts}",
        "stage": stage,
        "provider": provider,
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "concurrency": concurrency,
        "rounds": rounds,
        "total_requests": total_requests,
        "metrics": metrics,
        "cost_per_request": round(cost, 8),
        "cost_breakdown": breakdown,
    }

    store.save_result(result)

    _running_benchmarks[stage] = {
        "stage": stage,
        "running": False,
        "progress": "Complete",
        "completed_requests": total_requests,
        "total_requests": total_requests,
        "result": result,
    }


async def _benchmark_request(
    session: aiohttp.ClientSession,
    endpoint: str,
    stage: str,
) -> dict:
    """Fire a single benchmark request and return timing + metadata."""
    start = time.monotonic()
    async with session.post(endpoint, json={}, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        resp.raise_for_status()
        data = await resp.json()
    elapsed_ms = (time.monotonic() - start) * 1000

    return {
        "latency_ms": round(elapsed_ms, 1),
        "input_tokens": data.get("input_tokens"),
        "output_tokens": data.get("output_tokens"),
        "characters": data.get("characters"),
        "audio_seconds": data.get("audio_seconds"),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -m pytest tests/admin-api/test_benchmark_service.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/admin-api/services/benchmark.py tests/admin-api/test_benchmark_service.py
git commit -m "feat: add benchmark execution service with percentile metrics and cost calculation"
```

---

## Task 5: Admin-API Pipeline Router

**Files:**
- Create: `apps/admin-api/routers/pipeline.py`
- Modify: `apps/admin-api/main.py:93-97`

- [ ] **Step 1: Create pipeline router**

Create `apps/admin-api/routers/pipeline.py`:

```python
"""
Pipeline management API endpoints.

Provides model selection per pipeline stage (hot-swap)
and per-stage benchmark execution.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user, User
from config import settings
from models.pipeline import (
    PipelineStageConfig,
    PipelineConfig,
    PipelineStageUpdate,
    BenchmarkRequest,
    BenchmarkResult,
    BenchmarkStatus,
    AVAILABLE_MODELS,
)
from services.benchmark import (
    BenchmarkResultStore,
    get_benchmark_status,
    run_benchmark,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Shared result store
_result_store = BenchmarkResultStore(
    results_path=str(Path(settings.admin_config_path).parent / "benchmark_results.json")
)


def _get_config_path() -> Path:
    """Get path to admin config file."""
    path = Path(settings.admin_config_path)
    if not path.is_absolute():
        current = Path(__file__).resolve()
        for parent in current.parents:
            target = parent / settings.admin_config_path
            if target.parent.exists():
                return target
    return path


def _load_config() -> dict:
    path = _get_config_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_config(config: dict):
    path = _get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2, default=str)


# =============================================================================
# Model Selection
# =============================================================================

@router.get("", response_model=PipelineConfig)
async def get_pipeline_config(user: User = Depends(get_current_user)):
    """Get current pipeline configuration for all stages."""
    config = _load_config()
    pipeline = config.get("pipeline", {})

    return PipelineConfig(
        stt=PipelineStageConfig(
            provider=pipeline.get("stt", {}).get("provider", "faster-whisper"),
            model=pipeline.get("stt", {}).get("model"),
        ),
        llm=PipelineStageConfig(
            provider=pipeline.get("llm", {}).get("provider", "ollama"),
            model=pipeline.get("llm", {}).get("model", "qwen2.5:3b"),
        ),
        tts=PipelineStageConfig(
            provider=pipeline.get("tts", {}).get("provider", "kokoro"),
            model=pipeline.get("tts", {}).get("model", "af_heart"),
        ),
    )


@router.put("/{stage}", response_model=PipelineStageConfig)
async def update_stage_config(
    stage: str,
    body: PipelineStageUpdate,
    user: User = Depends(get_current_user),
):
    """Update provider/model for a pipeline stage. Takes effect within 5 seconds (hot-swap)."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    # Validate provider exists for this stage
    stage_providers = AVAILABLE_MODELS.get(stage, {})
    if body.provider not in stage_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{body.provider}' for {stage}. "
                   f"Available: {list(stage_providers.keys())}",
        )

    # Validate model exists for this provider (if model specified)
    if body.model:
        valid_models = [m["id"] for m in stage_providers[body.provider]]
        if body.model not in valid_models:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model '{body.model}' for {body.provider}. "
                       f"Available: {valid_models}",
            )

    config = _load_config()
    if "pipeline" not in config:
        config["pipeline"] = {}
    config["pipeline"][stage] = {
        "provider": body.provider,
        "model": body.model,
    }
    _save_config(config)

    return PipelineStageConfig(provider=body.provider, model=body.model)


@router.get("/models")
async def get_available_models(user: User = Depends(get_current_user)):
    """Get all available models grouped by stage and provider."""
    return AVAILABLE_MODELS


# =============================================================================
# Benchmarks
# =============================================================================

@router.post("/{stage}/benchmark", response_model=BenchmarkStatus)
async def start_benchmark(
    stage: str,
    body: BenchmarkRequest,
    user: User = Depends(get_current_user),
):
    """Start a benchmark run for a pipeline stage."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    if body.concurrency not in (1, 5, 10, 20, 50):
        raise HTTPException(status_code=400, detail="Concurrency must be 1, 5, 10, 20, or 50")

    if body.rounds not in (1, 3, 5):
        raise HTTPException(status_code=400, detail="Rounds must be 1, 3, or 5")

    # Check if already running
    current = get_benchmark_status(stage)
    if current.get("running"):
        raise HTTPException(status_code=409, detail=f"Benchmark already running for {stage}")

    # Get current provider/model for this stage
    config = _load_config()
    pipeline = config.get("pipeline", {})
    stage_config = pipeline.get(stage, {})
    defaults = {"stt": "faster-whisper", "llm": "ollama", "tts": "kokoro"}
    provider = stage_config.get("provider", defaults[stage])
    model = stage_config.get("model")

    main_api_url = settings.main_api_url

    # Launch benchmark in background
    asyncio.create_task(
        run_benchmark(
            stage=stage,
            concurrency=body.concurrency,
            rounds=body.rounds,
            main_api_url=main_api_url,
            store=_result_store,
            provider=provider,
            model=model,
        )
    )

    return BenchmarkStatus(
        stage=stage,
        running=True,
        progress=f"0/{body.concurrency * body.rounds} requests",
        total_requests=body.concurrency * body.rounds,
    )


@router.get("/{stage}/benchmark/status", response_model=BenchmarkStatus)
async def get_stage_benchmark_status(
    stage: str,
    user: User = Depends(get_current_user),
):
    """Get status of a running benchmark for a stage."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    status_data = get_benchmark_status(stage)
    return BenchmarkStatus(**status_data)


@router.get("/{stage}/benchmark/latest", response_model=Optional[BenchmarkResult])
async def get_latest_benchmark(
    stage: str,
    user: User = Depends(get_current_user),
):
    """Get the most recent benchmark result for a stage."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    result = _result_store.get_latest(stage)
    if result is None:
        return None
    return BenchmarkResult(**result)


@router.get("/{stage}/benchmark/history")
async def get_benchmark_history(
    stage: str,
    user: User = Depends(get_current_user),
):
    """Get all benchmark results for a stage (most recent first)."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    return _result_store.get_history(stage)
```

- [ ] **Step 2: Register pipeline router in admin-api main.py**

In `apps/admin-api/main.py`, add import (near other router imports):
```python
from routers.pipeline import router as pipeline_router
```

Add registration (after line 97):
```python
app.include_router(pipeline_router, prefix="/api/admin")
```

- [ ] **Step 3: Add `main_api_url` to admin-api settings**

Check `apps/admin-api/config.py` and add if not present:
```python
main_api_url: str = "http://api:8000"
```

- [ ] **Step 4: Commit**

```bash
git add apps/admin-api/routers/pipeline.py apps/admin-api/main.py apps/admin-api/config.py
git commit -m "feat: add pipeline management router with model selection and benchmark endpoints"
```

---

## Task 6: Internal Benchmark Endpoints (Main API)

**Files:**
- Create: `apps/api/app/routers/benchmark.py`
- Modify: `apps/api/app/routers/__init__.py`
- Modify: `apps/api/app/main.py:13,64-74`

- [ ] **Step 1: Create internal benchmark router**

Create `apps/api/app/routers/benchmark.py`:

```python
"""
Internal benchmark endpoints for per-stage latency measurement.

These endpoints are called by the admin-api benchmark service to measure
individual stage performance in isolation. Not exposed to external traffic.
"""

import io
import logging
import time
from pathlib import Path

from fastapi import APIRouter

from ..config import settings, dynamic_config
from ..services.llm import LLMService, is_ollama_available
from ..services.rag import search_knowledge_base
from ..services.tts import synthesize_speech

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/benchmark", tags=["benchmark"])

# Test data
TEST_QUESTIONS = [
    "What do elephants eat?",
    "How fast can a cheetah run?",
    "Do penguins live at the zoo?",
    "What sounds does a lion make?",
    "How long do turtles live?",
]

TEST_TTS_TEXT = (
    "Elephants are amazing animals! They can eat up to 300 pounds of food every single day. "
    "They love munching on grasses, leaves, bark, and fruit. At Leesburg Animal Park, "
    "our elephants get a special diet to keep them healthy and happy!"
)

import random


@router.post("/stt")
async def benchmark_stt():
    """
    Benchmark STT stage.
    Uses a pre-generated short audio clip for consistent measurement.
    Returns timing and audio metadata.
    """
    from ..services.stt import transcribe_audio

    # Generate a short silent WAV for consistent benchmarking
    import numpy as np
    import soundfile as sf
    sample_rate = 16000
    duration = 2.0
    audio_data = np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.01
    buf = io.BytesIO()
    sf.write(buf, audio_data, sample_rate, format="WAV")
    audio_bytes = buf.getvalue()

    start = time.monotonic()
    try:
        result = await transcribe_audio(audio_bytes)
    except Exception as e:
        logger.warning(f"STT benchmark failed: {e}")
        result = ""
    elapsed_ms = (time.monotonic() - start) * 1000

    return {
        "latency_ms": round(elapsed_ms, 1),
        "audio_seconds": duration,
        "transcript_length": len(result),
    }


@router.post("/llm")
async def benchmark_llm():
    """
    Benchmark LLM + RAG stage.
    Runs a random test question through RAG retrieval + LLM generation.
    Returns timing and token counts.
    """
    question = random.choice(TEST_QUESTIONS)

    start = time.monotonic()

    # RAG retrieval
    context = await search_knowledge_base(question)
    context_text = context if isinstance(context, str) else str(context)

    # LLM generation
    messages = [
        {"role": "system", "content": "You are a helpful zoo assistant. Answer briefly."},
        {"role": "user", "content": f"Context: {context_text}\n\nQuestion: {question}"},
    ]

    llm = LLMService(openai_api_key=settings.openai_api_key)
    response = await llm.generate(messages, temperature=0.7, max_tokens=200)

    elapsed_ms = (time.monotonic() - start) * 1000

    # Approximate token counts (1 token ~ 4 chars)
    input_text = " ".join(m["content"] for m in messages)
    input_tokens = len(input_text) // 4
    output_tokens = len(response) // 4

    return {
        "latency_ms": round(elapsed_ms, 1),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


@router.post("/tts")
async def benchmark_tts():
    """
    Benchmark TTS stage.
    Synthesizes a fixed test text and returns timing and character count.
    """
    start = time.monotonic()

    try:
        audio_bytes = await synthesize_speech(TEST_TTS_TEXT)
    except Exception as e:
        logger.warning(f"TTS benchmark failed: {e}")
        audio_bytes = b""

    elapsed_ms = (time.monotonic() - start) * 1000

    return {
        "latency_ms": round(elapsed_ms, 1),
        "characters": len(TEST_TTS_TEXT),
        "audio_bytes": len(audio_bytes),
    }
```

- [ ] **Step 2: Export benchmark_router from routers __init__**

In `apps/api/app/routers/__init__.py`, add:
```python
from .benchmark import router as benchmark_router
```

- [ ] **Step 3: Register benchmark router in main API**

In `apps/api/app/main.py`, add to import (line 13):
```python
from .routers import session_router, chat_router, voice_router, feedback_router, benchmark_router
```

Add registration (after line 67):
```python
api_router.include_router(benchmark_router)
```

Also register without prefix for dev compatibility (after line 74):
```python
app.include_router(benchmark_router)
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/routers/benchmark.py apps/api/app/routers/__init__.py apps/api/app/main.py
git commit -m "feat: add internal per-stage benchmark endpoints for STT, LLM, TTS"
```

---

## Task 7: Frontend TypeScript Types

**Files:**
- Modify: `apps/admin/src/types/index.ts`

- [ ] **Step 1: Add pipeline types**

Append to `apps/admin/src/types/index.ts`:

```typescript
// Pipeline Types
export interface PipelineStageConfig {
  provider: string
  model: string | null
}

export interface PipelineConfig {
  stt: PipelineStageConfig
  llm: PipelineStageConfig
  tts: PipelineStageConfig
}

export interface PipelineStageUpdate {
  provider: string
  model?: string | null
}

export interface BenchmarkRequest {
  concurrency: number
  rounds: number
}

export interface BenchmarkMetrics {
  p50_ms: number
  p95_ms: number
  p99_ms: number
  avg_ms: number
  min_ms: number
  max_ms: number
  success_rate: number
}

export interface CostBreakdown {
  input_tokens_avg: number | null
  output_tokens_avg: number | null
  characters_avg: number | null
  audio_seconds_avg: number | null
}

export interface BenchmarkResult {
  id: string
  stage: string
  provider: string
  model: string | null
  timestamp: string
  concurrency: number
  rounds: number
  total_requests: number
  metrics: BenchmarkMetrics
  cost_per_request: number
  cost_breakdown: CostBreakdown
}

export interface BenchmarkStatus {
  stage: string
  running: boolean
  progress: string | null
  completed_requests: number
  total_requests: number
  result: BenchmarkResult | null
}

export interface ModelOption {
  id: string
  name: string
  description: string
}

export type AvailableModels = Record<string, Record<string, ModelOption[]>>
```

- [ ] **Step 2: Commit**

```bash
git add apps/admin/src/types/index.ts
git commit -m "feat: add pipeline TypeScript types"
```

---

## Task 8: Frontend API Client

**Files:**
- Modify: `apps/admin/src/api/client.ts`

- [ ] **Step 1: Add pipelineApi namespace**

Append to `apps/admin/src/api/client.ts` (after `feedbackApi`):

```typescript
// Pipeline API
export const pipelineApi = {
  getConfig: () =>
    api<import('../types').PipelineConfig>('/pipeline'),

  updateStage: (stage: string, data: import('../types').PipelineStageUpdate) =>
    api<import('../types').PipelineStageConfig>(`/pipeline/${stage}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  getAvailableModels: () =>
    api<import('../types').AvailableModels>('/pipeline/models'),

  startBenchmark: (stage: string, data: import('../types').BenchmarkRequest) =>
    api<import('../types').BenchmarkStatus>(`/pipeline/${stage}/benchmark`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getBenchmarkStatus: (stage: string) =>
    api<import('../types').BenchmarkStatus>(`/pipeline/${stage}/benchmark/status`),

  getLatestBenchmark: (stage: string) =>
    api<import('../types').BenchmarkResult | null>(`/pipeline/${stage}/benchmark/latest`),

  getBenchmarkHistory: (stage: string) =>
    api<import('../types').BenchmarkResult[]>(`/pipeline/${stage}/benchmark/history`),
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/admin/src/api/client.ts
git commit -m "feat: add pipelineApi client methods"
```

---

## Task 9: StageCard Component

**Files:**
- Create: `apps/admin/src/components/Pipeline/StageCard.tsx`

- [ ] **Step 1: Create StageCard component**

Create directory and file `apps/admin/src/components/Pipeline/StageCard.tsx`:

```tsx
import { useState, useEffect, useRef } from 'react'
import { pipelineApi } from '../../api/client'
import type {
  PipelineStageConfig,
  BenchmarkResult,
  BenchmarkStatus,
  ModelOption,
} from '../../types'

interface StageCardProps {
  stage: 'stt' | 'llm' | 'tts'
  title: string
  label: string
  config: PipelineStageConfig
  models: Record<string, ModelOption[]>
  latestBenchmark: BenchmarkResult | null
  onConfigChange: () => void
}

const STAGE_COLORS: Record<string, { badge: string; badgeText: string; button: string }> = {
  stt: { badge: 'bg-blue-900', badgeText: 'text-blue-300', button: 'bg-blue-900 text-blue-300' },
  llm: { badge: 'bg-purple-900', badgeText: 'text-purple-300', button: 'bg-purple-900 text-purple-300' },
  tts: { badge: 'bg-orange-900', badgeText: 'text-orange-300', button: 'bg-orange-900 text-orange-300' },
}

const CONCURRENCY_OPTIONS = [1, 5, 10, 20, 50]
const ROUND_OPTIONS = [1, 3, 5]

export default function StageCard({
  stage,
  title,
  label,
  config,
  models,
  latestBenchmark,
  onConfigChange,
}: StageCardProps) {
  const [selectedProvider, setSelectedProvider] = useState(config.provider)
  const [selectedModel, setSelectedModel] = useState(config.model || '')
  const [applyStatus, setApplyStatus] = useState<'idle' | 'applying' | 'success' | 'error'>('idle')
  const [applyError, setApplyError] = useState('')
  const [concurrency, setConcurrency] = useState(5)
  const [rounds, setRounds] = useState(3)
  const [benchmarkStatus, setBenchmarkStatus] = useState<BenchmarkStatus | null>(null)
  const pollRef = useRef<number | null>(null)
  const colors = STAGE_COLORS[stage]

  // Build grouped options: provider -> models
  const providerNames = Object.keys(models)

  // When provider changes, auto-select first model
  const handleProviderModelChange = (value: string) => {
    // value format: "provider/model"
    const [prov, ...modelParts] = value.split('/')
    const model = modelParts.join('/')
    setSelectedProvider(prov)
    setSelectedModel(model)
    setApplyStatus('idle')
  }

  const currentValue = `${selectedProvider}/${selectedModel}`

  const handleApply = async () => {
    setApplyStatus('applying')
    setApplyError('')
    try {
      await pipelineApi.updateStage(stage, {
        provider: selectedProvider,
        model: selectedModel || null,
      })
      setApplyStatus('success')
      onConfigChange()
      setTimeout(() => setApplyStatus('idle'), 3000)
    } catch (err: any) {
      setApplyStatus('error')
      setApplyError(err.message || 'Failed to apply')
    }
  }

  const handleRunBenchmark = async () => {
    try {
      const status = await pipelineApi.startBenchmark(stage, { concurrency, rounds })
      setBenchmarkStatus(status)
      startPolling()
    } catch (err: any) {
      alert(err.message || 'Failed to start benchmark')
    }
  }

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = window.setInterval(async () => {
      try {
        const status = await pipelineApi.getBenchmarkStatus(stage)
        setBenchmarkStatus(status)
        if (!status.running) {
          if (pollRef.current) clearInterval(pollRef.current)
          pollRef.current = null
          onConfigChange() // refresh latest benchmark
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current)
        pollRef.current = null
      }
    }, 1000)
  }

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const stageNumber = stage === 'stt' ? 1 : stage === 'llm' ? 2 : 3

  return (
    <div className="flex-1 min-w-[280px] bg-gray-800 rounded-xl p-5 border border-gray-700">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wider">Stage {stageNumber}</div>
          <div className="text-lg font-semibold text-white">{title}</div>
        </div>
        <div className={`${colors.badge} ${colors.badgeText} px-3 py-1 rounded-lg text-xs font-medium`}>
          {label}
        </div>
      </div>

      {/* Model Selection */}
      <div className="mb-4">
        <div className="text-xs text-gray-400 mb-1">Provider / Model</div>
        <div className="flex gap-2">
          <select
            value={currentValue}
            onChange={(e) => handleProviderModelChange(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-600 text-white p-2 rounded-md text-sm"
          >
            {providerNames.map((prov) => (
              <optgroup key={prov} label={prov}>
                {models[prov].map((m) => (
                  <option key={`${prov}/${m.id}`} value={`${prov}/${m.id}`}>
                    {m.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          <button
            onClick={handleApply}
            disabled={applyStatus === 'applying'}
            className="bg-green-800 text-white px-4 py-2 rounded-md text-xs hover:bg-green-700 disabled:opacity-50"
          >
            {applyStatus === 'applying' ? '...' : 'Apply'}
          </button>
        </div>
        <div className="text-xs mt-1">
          {applyStatus === 'success' && <span className="text-green-400">&#10003; Active — applied at runtime</span>}
          {applyStatus === 'error' && <span className="text-red-400">&#10007; {applyError}</span>}
          {applyStatus === 'idle' && <span className="text-green-400">&#10003; Active</span>}
        </div>
      </div>

      {/* Benchmark Results */}
      <div className="bg-gray-900 rounded-lg p-3 mb-3">
        {latestBenchmark ? (
          <>
            <div className="text-xs text-gray-500 mb-2">
              Last Benchmark — {new Date(latestBenchmark.timestamp).toLocaleDateString()}
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-lg font-semibold text-blue-300">
                  {latestBenchmark.metrics.p50_ms < 1000
                    ? `${Math.round(latestBenchmark.metrics.p50_ms)}ms`
                    : `${(latestBenchmark.metrics.p50_ms / 1000).toFixed(1)}s`}
                </div>
                <div className="text-[10px] text-gray-500">p50 latency</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-yellow-300">
                  {latestBenchmark.metrics.p95_ms < 1000
                    ? `${Math.round(latestBenchmark.metrics.p95_ms)}ms`
                    : `${(latestBenchmark.metrics.p95_ms / 1000).toFixed(1)}s`}
                </div>
                <div className="text-[10px] text-gray-500">p95 latency</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-green-400">
                  ${latestBenchmark.cost_per_request.toFixed(4)}
                </div>
                <div className="text-[10px] text-gray-500">per request</div>
              </div>
            </div>
          </>
        ) : (
          <div className="text-xs text-gray-500 text-center py-2">
            No benchmark data — run a benchmark to see metrics
          </div>
        )}
      </div>

      {/* Run Benchmark */}
      {benchmarkStatus?.running ? (
        <div className="text-center">
          <div className="text-sm text-blue-300 mb-1">Running...</div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{
                width: `${benchmarkStatus.total_requests > 0
                  ? (benchmarkStatus.completed_requests / benchmarkStatus.total_requests) * 100
                  : 0}%`,
              }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">{benchmarkStatus.progress}</div>
        </div>
      ) : (
        <div className="flex gap-2 items-center">
          <select
            value={concurrency}
            onChange={(e) => setConcurrency(Number(e.target.value))}
            className="bg-gray-900 border border-gray-600 text-white p-1.5 rounded-md text-xs"
          >
            {CONCURRENCY_OPTIONS.map((c) => (
              <option key={c} value={c}>{c} user{c > 1 ? 's' : ''}</option>
            ))}
          </select>
          <select
            value={rounds}
            onChange={(e) => setRounds(Number(e.target.value))}
            className="bg-gray-900 border border-gray-600 text-white p-1.5 rounded-md text-xs"
          >
            {ROUND_OPTIONS.map((r) => (
              <option key={r} value={r}>{r} round{r > 1 ? 's' : ''}</option>
            ))}
          </select>
          <button
            onClick={handleRunBenchmark}
            className={`${colors.button} px-3 py-1.5 rounded-md text-xs hover:opacity-80`}
          >
            &#9654; Run
          </button>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
mkdir -p apps/admin/src/components/Pipeline
git add apps/admin/src/components/Pipeline/StageCard.tsx
git commit -m "feat: add StageCard component for pipeline model selection and benchmarking"
```

---

## Task 10: CostProjection Component

**Files:**
- Create: `apps/admin/src/components/Pipeline/CostProjection.tsx`

- [ ] **Step 1: Create CostProjection component**

Create `apps/admin/src/components/Pipeline/CostProjection.tsx`:

```tsx
import type { BenchmarkResult } from '../../types'

interface CostProjectionProps {
  sttBenchmark: BenchmarkResult | null
  llmBenchmark: BenchmarkResult | null
  ttsBenchmark: BenchmarkResult | null
}

const DAILY_VOLUMES = [500, 1000, 2000, 5000]
const DAYS_PER_MONTH = 30

function formatCost(cost: number): string {
  if (cost === 0) return '$0.00'
  if (cost < 0.01) return '< $0.01'
  return `$${cost.toFixed(2)}`
}

export default function CostProjection({ sttBenchmark, llmBenchmark, ttsBenchmark }: CostProjectionProps) {
  const sttCost = sttBenchmark?.cost_per_request ?? null
  const llmCost = llmBenchmark?.cost_per_request ?? null
  const ttsCost = ttsBenchmark?.cost_per_request ?? null

  const hasBenchmarks = sttCost !== null || llmCost !== null || ttsCost !== null

  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
      <div className="mb-4">
        <div className="text-lg font-semibold text-white">Monthly Cost Projection</div>
        <div className="text-xs text-gray-500">
          Based on current model selection and latest benchmark per-request costs
        </div>
      </div>

      {hasBenchmarks ? (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left p-2.5 text-gray-500 font-medium">Daily Volume</th>
                <th className="text-right p-2.5 text-blue-400 font-medium">STT</th>
                <th className="text-right p-2.5 text-purple-400 font-medium">LLM/RAG</th>
                <th className="text-right p-2.5 text-orange-400 font-medium">TTS</th>
                <th className="text-right p-2.5 text-white font-semibold">Total / Month</th>
              </tr>
            </thead>
            <tbody>
              {DAILY_VOLUMES.map((volume) => {
                const sttMonthly = sttCost !== null ? sttCost * volume * DAYS_PER_MONTH : null
                const llmMonthly = llmCost !== null ? llmCost * volume * DAYS_PER_MONTH : null
                const ttsMonthly = ttsCost !== null ? ttsCost * volume * DAYS_PER_MONTH : null

                const total = (sttMonthly ?? 0) + (llmMonthly ?? 0) + (ttsMonthly ?? 0)
                const allPresent = sttMonthly !== null && llmMonthly !== null && ttsMonthly !== null

                return (
                  <tr key={volume} className="border-b border-gray-900">
                    <td className="p-2.5 text-gray-300">
                      {volume.toLocaleString()} questions/day
                    </td>
                    <td className="p-2.5 text-right text-blue-300">
                      {sttMonthly !== null ? formatCost(sttMonthly) : '—'}
                    </td>
                    <td className="p-2.5 text-right text-purple-300">
                      {llmMonthly !== null ? formatCost(llmMonthly) : '—'}
                    </td>
                    <td className="p-2.5 text-right text-orange-300">
                      {ttsMonthly !== null ? formatCost(ttsMonthly) : '—'}
                    </td>
                    <td className="p-2.5 text-right text-white font-semibold">
                      {allPresent ? formatCost(total) : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div className="text-[11px] text-gray-600 mt-2">
            * Local models (Kokoro, faster-whisper, Ollama) show $0.00 API cost — compute/infra cost not included.
          </div>
        </>
      ) : (
        <div className="text-center text-gray-500 text-sm py-8">
          Run benchmarks for each stage to see cost projections
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/admin/src/components/Pipeline/CostProjection.tsx
git commit -m "feat: add CostProjection component for monthly cost table"
```

---

## Task 11: Pipeline Page + Routing

**Files:**
- Create: `apps/admin/src/pages/Pipeline.tsx`
- Modify: `apps/admin/src/App.tsx:1-47`
- Modify: `apps/admin/src/components/Layout/index.tsx:5-13`

- [ ] **Step 1: Create Pipeline page**

Create `apps/admin/src/pages/Pipeline.tsx`:

```tsx
import { useState, useEffect, useCallback } from 'react'
import { pipelineApi } from '../api/client'
import StageCard from '../components/Pipeline/StageCard'
import CostProjection from '../components/Pipeline/CostProjection'
import type { PipelineConfig, BenchmarkResult, AvailableModels } from '../types'

export default function Pipeline() {
  const [config, setConfig] = useState<PipelineConfig | null>(null)
  const [models, setModels] = useState<AvailableModels>({})
  const [sttBenchmark, setSttBenchmark] = useState<BenchmarkResult | null>(null)
  const [llmBenchmark, setLlmBenchmark] = useState<BenchmarkResult | null>(null)
  const [ttsBenchmark, setTtsBenchmark] = useState<BenchmarkResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = useCallback(async () => {
    try {
      const [configData, modelsData, sttLatest, llmLatest, ttsLatest] = await Promise.all([
        pipelineApi.getConfig(),
        pipelineApi.getAvailableModels(),
        pipelineApi.getLatestBenchmark('stt').catch(() => null),
        pipelineApi.getLatestBenchmark('llm').catch(() => null),
        pipelineApi.getLatestBenchmark('tts').catch(() => null),
      ])

      setConfig(configData)
      setModels(modelsData)
      setSttBenchmark(sttLatest)
      setLlmBenchmark(llmLatest)
      setTtsBenchmark(ttsLatest)
      setError('')
    } catch (err: any) {
      setError(err.message || 'Failed to load pipeline configuration')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading pipeline configuration...</div>
      </div>
    )
  }

  if (error || !config) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <div className="text-red-400">{error || 'Failed to load configuration'}</div>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Pipeline Management</h1>
        <span className="bg-green-900 text-green-300 px-3 py-1 rounded-full text-xs">
          ● All Services Healthy
        </span>
      </div>

      {/* Stage Cards */}
      <div className="flex gap-4 flex-wrap mb-6">
        <StageCard
          stage="stt"
          title="Speech-to-Text"
          label="STT"
          config={config.stt}
          models={models.stt || {}}
          latestBenchmark={sttBenchmark}
          onConfigChange={loadData}
        />
        <StageCard
          stage="llm"
          title="LLM / RAG"
          label="LLM"
          config={config.llm}
          models={models.llm || {}}
          latestBenchmark={llmBenchmark}
          onConfigChange={loadData}
        />
        <StageCard
          stage="tts"
          title="Text-to-Speech"
          label="TTS"
          config={config.tts}
          models={models.tts || {}}
          latestBenchmark={ttsBenchmark}
          onConfigChange={loadData}
        />
      </div>

      {/* Cost Projection */}
      <CostProjection
        sttBenchmark={sttBenchmark}
        llmBenchmark={llmBenchmark}
        ttsBenchmark={ttsBenchmark}
      />
    </div>
  )
}
```

- [ ] **Step 2: Add Pipeline route to App.tsx**

In `apps/admin/src/App.tsx`, add import at line 11 (after Feedback import):
```typescript
import Pipeline from './pages/Pipeline'
```

Add route after the `/configuration` route (line 39):
```tsx
<Route path="/pipeline" element={<Pipeline />} />
```

- [ ] **Step 3: Add Pipeline to sidebar nav**

In `apps/admin/src/components/Layout/index.tsx`, add to the `navItems` array after the Dashboard entry (line 6):
```typescript
  { to: '/pipeline', label: 'Pipeline', icon: '🔧' },
```

This places it second in the nav, right after Dashboard and before Sessions.

- [ ] **Step 4: Commit**

```bash
git add apps/admin/src/pages/Pipeline.tsx apps/admin/src/App.tsx apps/admin/src/components/Layout/index.tsx
git commit -m "feat: add Pipeline page with routing and sidebar navigation"
```

---

## Task 12: Integration Smoke Test

**Files:**
- Create: `tests/admin-api/test_pipeline_router.py`

- [ ] **Step 1: Write integration test for pipeline endpoints**

Create `tests/admin-api/test_pipeline_router.py`:

```python
"""
Integration tests for pipeline management endpoints.
Tests config CRUD and benchmark result retrieval.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def config_dir(tmp_path):
    """Create a temp config directory with default admin_config.json."""
    config_file = tmp_path / "admin_config.json"
    config_file.write_text(json.dumps({
        "version": "1.0",
        "prompts": {"system_prompt": "test", "fallback_response": "test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
        "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0},
    }))
    return tmp_path


@pytest.fixture
def client(config_dir):
    """Create test client with mocked config path and auth."""
    with patch("routers.pipeline.settings") as mock_settings, \
         patch("routers.pipeline.get_current_user") as mock_auth:
        mock_settings.admin_config_path = str(config_dir / "admin_config.json")
        mock_settings.main_api_url = "http://localhost:8000"
        mock_auth.return_value = MagicMock(username="admin")

        # Need to import after patching
        from routers.pipeline import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/admin")

        yield TestClient(app)


def test_get_pipeline_config(client):
    """Pipeline config returns defaults when no pipeline key exists."""
    response = client.get("/api/admin/pipeline")
    assert response.status_code == 200
    data = response.json()
    assert data["stt"]["provider"] == "faster-whisper"
    assert data["llm"]["provider"] == "ollama"
    assert data["tts"]["provider"] == "kokoro"


def test_update_stage_config(client):
    """Updating a stage writes to config and returns updated values."""
    response = client.put(
        "/api/admin/pipeline/llm",
        json={"provider": "openai", "model": "gpt-4o-mini"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4o-mini"

    # Verify it persists
    response2 = client.get("/api/admin/pipeline")
    assert response2.json()["llm"]["provider"] == "openai"


def test_update_invalid_stage(client):
    response = client.put(
        "/api/admin/pipeline/invalid",
        json={"provider": "openai"},
    )
    assert response.status_code == 400


def test_update_invalid_provider(client):
    response = client.put(
        "/api/admin/pipeline/llm",
        json={"provider": "nonexistent"},
    )
    assert response.status_code == 400


def test_update_invalid_model(client):
    response = client.put(
        "/api/admin/pipeline/llm",
        json={"provider": "ollama", "model": "nonexistent-model"},
    )
    assert response.status_code == 400


def test_get_available_models(client):
    response = client.get("/api/admin/pipeline/models")
    assert response.status_code == 200
    data = response.json()
    assert "stt" in data
    assert "llm" in data
    assert "tts" in data
    assert "ollama" in data["llm"]
    assert len(data["llm"]["ollama"]) > 0


def test_get_latest_benchmark_empty(client):
    response = client.get("/api/admin/pipeline/llm/benchmark/latest")
    assert response.status_code == 200
    assert response.json() is None
```

- [ ] **Step 2: Run tests**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -m pytest tests/admin-api/test_pipeline_router.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/admin-api/test_pipeline_router.py
git commit -m "test: add integration tests for pipeline management endpoints"
```

---

## Task 13: Frontend Build Verification

- [ ] **Step 1: Verify frontend builds without errors**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling/apps/admin && npm run build`
Expected: Build succeeds with no TypeScript errors

- [ ] **Step 2: Fix any build errors**

If there are TypeScript errors, fix them in the relevant files.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A apps/admin/src/
git commit -m "fix: resolve TypeScript build errors in pipeline components"
```

---

## Task 14: Final Run — All Tests

- [ ] **Step 1: Run all backend tests**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS (existing + new pipeline tests)

- [ ] **Step 2: Run frontend build**

Run: `cd /home/jesus/Documents/zoogpt/knowledge/docling/apps/admin && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "chore: final pipeline management integration fixes"
```
