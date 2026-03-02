#!/usr/bin/env python
"""
Verification script for hot-reload dynamic configuration.

This script demonstrates:
1. Loading config from admin_config.json
2. Accessing config values
3. Hot-reload when config file changes
"""

import sys
from pathlib import Path

# Add apps/api to path
api_path = Path(__file__).parent / "apps" / "api"
sys.path.insert(0, str(api_path))

from app.config import dynamic_config


def main():
    print("=" * 60)
    print("Dynamic Configuration Verification")
    print("=" * 60)
    print()

    # Check config path
    print(f"Config file path: {dynamic_config._config_path}")
    print(f"Config file exists: {dynamic_config._config_path.exists()}")
    print()

    # Display current config values
    print("Current Configuration Values:")
    print("-" * 60)
    print(f"Model Name:          {dynamic_config.model_name}")
    print(f"Model Temperature:   {dynamic_config.model_temperature}")
    print(f"Model Max Tokens:    {dynamic_config.model_max_tokens}")
    print()
    print(f"TTS Provider:        {dynamic_config.tts_provider}")
    print(f"TTS Default Voice:   {dynamic_config.tts_default_voice}")
    print(f"TTS Speed:           {dynamic_config.tts_speed}")
    print()
    print(f"System Prompt:       {dynamic_config.system_prompt[:100]}...")
    print(f"Fallback Response:   {dynamic_config.fallback_response}")
    print()

    # Poll interval info
    print(f"Poll Interval:       {dynamic_config._poll_interval} seconds")
    print()

    print("=" * 60)
    print("Verification Complete!")
    print("=" * 60)
    print()
    print("To test hot-reload:")
    print(f"1. Edit {dynamic_config._config_path}")
    print("2. Change model.name, model.temperature, or tts.default_voice")
    print("3. Wait 5+ seconds")
    print("4. Run this script again to see updated values")
    print()


if __name__ == "__main__":
    main()
