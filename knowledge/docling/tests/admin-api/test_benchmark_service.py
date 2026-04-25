import json
import pytest
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "admin-api"))

from services.benchmark import (
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
    assert history[0]["id"] == "llm_test_2"
