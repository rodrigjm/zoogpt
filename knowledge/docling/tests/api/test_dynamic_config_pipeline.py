import json
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api"))

from app.config import DynamicConfig


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
