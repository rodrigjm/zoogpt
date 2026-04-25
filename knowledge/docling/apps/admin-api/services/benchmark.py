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
    token_counts = []
    char_counts = []
    audio_durations = []

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
