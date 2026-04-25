"""
Integration tests for pipeline management endpoints.
Tests config CRUD and benchmark result retrieval.
"""

import json
import importlib
import sys
from pathlib import Path

import pytest

ADMIN_API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "admin-api"
sys.path.insert(0, str(ADMIN_API_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.basic import User, get_current_user

# Load pipeline router module directly to avoid triggering routers/__init__
# (which imports kb.py → lancedb, not needed for these unit tests)
_spec = importlib.util.spec_from_file_location(
    "pipeline_router_module",
    ADMIN_API_ROOT / "routers" / "pipeline.py",
)
pipeline_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pipeline_module)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client with isolated config dir and auth override."""
    config_file = tmp_path / "admin_config.json"
    config_file.write_text(json.dumps({
        "version": "1.0",
        "prompts": {"system_prompt": "test", "fallback_response": "test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
        "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0},
    }))

    monkeypatch.setattr(pipeline_module.settings, "admin_config_path", str(config_file))
    monkeypatch.setattr(pipeline_module, "_get_config_path", lambda: config_file)
    monkeypatch.setattr(
        pipeline_module,
        "_result_store",
        pipeline_module.BenchmarkResultStore(
            results_path=str(tmp_path / "benchmark_results.json")
        ),
    )

    app = FastAPI()
    app.include_router(pipeline_module.router, prefix="/api/admin")
    app.dependency_overrides[get_current_user] = lambda: User(username="admin")

    return TestClient(app)


def test_get_pipeline_config_defaults(client):
    """Pipeline config returns defaults when no pipeline key exists."""
    response = client.get("/api/admin/pipeline")
    assert response.status_code == 200
    data = response.json()
    assert data["stt"]["provider"] == "faster-whisper"
    assert data["llm"]["provider"] == "ollama"
    assert data["tts"]["provider"] == "kokoro"


def test_update_stage_config_persists(client):
    """Updating a stage writes to config and persists across reads."""
    response = client.put(
        "/api/admin/pipeline/llm",
        json={"provider": "openai", "model": "gpt-4o-mini"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4o-mini"

    response2 = client.get("/api/admin/pipeline")
    assert response2.json()["llm"]["provider"] == "openai"
    assert response2.json()["llm"]["model"] == "gpt-4o-mini"


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


def test_benchmark_status_for_idle_stage(client):
    """Status endpoint returns 'not running' for stages with no benchmark."""
    response = client.get("/api/admin/pipeline/stt/benchmark/status")
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "stt"
    assert data["running"] is False


def test_benchmark_history_empty(client):
    response = client.get("/api/admin/pipeline/tts/benchmark/history")
    assert response.status_code == 200
    assert response.json() == []
