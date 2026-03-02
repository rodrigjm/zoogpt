"""
Tests for dynamic configuration system.
"""

import json
import tempfile
import time
from pathlib import Path

import pytest

from app.config import DynamicConfig


def test_dynamic_config_loads_defaults():
    """Test that DynamicConfig falls back to defaults when file doesn't exist."""
    # Create config pointing to non-existent file
    config = DynamicConfig(config_path="/tmp/nonexistent_config_12345.json", poll_interval=0.1)

    # Should return defaults
    assert config.model_name == "gpt-4o-mini"
    assert config.model_temperature == 0.7
    assert config.model_max_tokens == 500
    assert config.tts_provider == "kokoro"
    assert config.tts_default_voice == "af_heart"


def test_dynamic_config_loads_from_file():
    """Test that DynamicConfig loads from existing file."""
    # Create temp config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "version": "1.0",
            "prompts": {
                "system_prompt": "Test prompt",
                "fallback_response": "Test fallback"
            },
            "model": {
                "name": "gpt-4o",
                "temperature": 0.5,
                "max_tokens": 1000
            },
            "tts": {
                "provider": "openai",
                "default_voice": "nova",
                "speed": 1.5
            }
        }
        json.dump(config_data, f)
        temp_path = f.name

    try:
        # Load config
        config = DynamicConfig(config_path=temp_path, poll_interval=0.1)

        # Verify loaded values
        assert config.system_prompt == "Test prompt"
        assert config.fallback_response == "Test fallback"
        assert config.model_name == "gpt-4o"
        assert config.model_temperature == 0.5
        assert config.model_max_tokens == 1000
        assert config.tts_provider == "openai"
        assert config.tts_default_voice == "nova"
        assert config.tts_speed == 1.5
    finally:
        # Cleanup
        Path(temp_path).unlink()


def test_dynamic_config_hot_reload():
    """Test that DynamicConfig reloads when file changes."""
    # Create temp config file with initial values
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "version": "1.0",
            "prompts": {
                "system_prompt": "Initial prompt",
                "fallback_response": "Initial fallback"
            },
            "model": {
                "name": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "tts": {
                "provider": "kokoro",
                "default_voice": "af_heart",
                "speed": 1.0
            }
        }
        json.dump(config_data, f)
        temp_path = f.name

    try:
        # Load config with short poll interval
        config = DynamicConfig(config_path=temp_path, poll_interval=0.1)

        # Verify initial values
        assert config.model_name == "gpt-4o-mini"
        assert config.model_temperature == 0.7

        # Wait a moment to ensure mtime differs
        time.sleep(0.2)

        # Update config file
        with open(temp_path, 'w') as f:
            config_data["model"]["name"] = "gpt-4o"
            config_data["model"]["temperature"] = 0.9
            json.dump(config_data, f)

        # Wait for poll interval to pass
        time.sleep(0.2)

        # Force reload check by accessing property
        new_model = config.model_name
        new_temp = config.model_temperature

        # Verify values have been reloaded
        assert new_model == "gpt-4o"
        assert new_temp == 0.9
    finally:
        # Cleanup
        Path(temp_path).unlink()


def test_dynamic_config_handles_invalid_json():
    """Test that DynamicConfig handles invalid JSON gracefully."""
    # Create temp config file with valid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "version": "1.0",
            "prompts": {"system_prompt": "Valid prompt"},
            "model": {"name": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
            "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0}
        }
        json.dump(config_data, f)
        temp_path = f.name

    try:
        # Load config
        config = DynamicConfig(config_path=temp_path, poll_interval=0.1)
        assert config.model_name == "gpt-4o-mini"

        # Wait to ensure mtime differs
        time.sleep(0.2)

        # Write invalid JSON
        with open(temp_path, 'w') as f:
            f.write("{invalid json}")

        # Wait for poll interval
        time.sleep(0.2)

        # Should still return previous valid config
        assert config.model_name == "gpt-4o-mini"
    finally:
        # Cleanup
        Path(temp_path).unlink()


def test_dynamic_config_nested_access():
    """Test _get_nested method for safe nested dict access."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "version": "1.0",
            "prompts": {"system_prompt": "Test"},
            "model": {"name": "gpt-4o", "temperature": 0.7, "max_tokens": 500},
            "tts": {"provider": "kokoro", "default_voice": "af_heart", "speed": 1.0}
        }
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = DynamicConfig(config_path=temp_path, poll_interval=0.1)

        # Test valid nested access
        assert config._get_nested("model", "name") == "gpt-4o"

        # Test missing key returns default
        assert config._get_nested("model", "nonexistent", default="fallback") == "fallback"

        # Test deeply nested missing key
        assert config._get_nested("a", "b", "c", default="default") == "default"
    finally:
        Path(temp_path).unlink()
