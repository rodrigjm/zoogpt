"""
Configuration module using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, Union
from pathlib import Path
import json
import threading
import time
from datetime import datetime


def parse_cors_list(v: Union[str, list[str]]) -> list[str]:
    """Parse comma-separated CORS origins from environment variable."""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    return v if v else []


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # OpenAI
    openai_api_key: str

    # TTS Settings
    tts_provider: str = "kokoro"
    tts_voice: str = "af_heart"
    elevenlabs_api_key: Optional[str] = None

    # STT Settings
    stt_provider: str = "faster-whisper"

    # RAG Settings
    lancedb_path: str = "data/zoo_lancedb"
    embedding_model: str = "text-embedding-3-small"

    # Session Settings
    session_db_path: str = "data/sessions.db"

    @field_validator("lancedb_path", "session_db_path", mode="before")
    @classmethod
    def resolve_data_paths(cls, v: str) -> str:
        """Resolve relative data paths to absolute paths from project root."""
        if not Path(v).is_absolute() and v.startswith("data/"):
            # Find project root (directory containing populated data/ folder)
            current = Path(__file__).resolve()
            for parent in current.parents:
                target_path = parent / v
                # Check if the full path exists and has content
                if target_path.exists():
                    # For lancedb_path, verify it contains .lance files
                    if "lancedb" in v.lower():
                        if any(target_path.glob("*.lance")):
                            return str(target_path)
                    else:
                        return str(target_path)
        return v

    # CORS Settings - stored as string, parsed in main.py
    cors_origins: str = "http://localhost:3000,http://localhost:8501"

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as a list."""
        return parse_cors_list(self.cors_origins)


# Global settings instance
settings = Settings()


class DynamicConfig:
    """
    Dynamic configuration loaded from admin_config.json.
    Supports hot-reload by polling file modification time.
    Thread-safe access to config values.
    """

    def __init__(self, config_path: str = "data/admin_config.json", poll_interval: float = 5.0):
        """
        Initialize dynamic config loader.

        Args:
            config_path: Relative or absolute path to admin_config.json
            poll_interval: How often to check file mtime (seconds)
        """
        self._config_path = self._resolve_config_path(config_path)
        self._poll_interval = poll_interval
        self._config = self._load_default_config()
        self._last_mtime = 0.0
        self._last_check = 0.0
        self._lock = threading.RLock()

        # Initial load
        self._reload_if_changed()

    def _resolve_config_path(self, config_path: str) -> Path:
        """Resolve config path to absolute path."""
        path = Path(config_path)
        if path.is_absolute():
            return path

        # Try relative to project root (search up from this file)
        current = Path(__file__).resolve()
        for parent in current.parents:
            target = parent / config_path
            # Check if file exists (not just parent directory)
            if target.exists():
                return target

        # Fallback: try from parent directories even if file doesn't exist yet
        # (useful when config will be created by admin-api)
        current = Path(__file__).resolve()
        for parent in current.parents:
            target = parent / config_path
            if target.parent.exists():
                return target

        # Last fallback to relative path from cwd
        return path

    def _load_default_config(self) -> dict:
        """Return default configuration fallback."""
        return {
            "version": "1.0",
            "prompts": {
                "system_prompt": "You are Zoocari the Elephant, a helpful assistant.",
                "fallback_response": "I don't know about that yet!",
                "followup_questions": []
            },
            "model": {
                "name": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "tts": {
                "provider": "kokoro",
                "default_voice": "af_heart",
                "speed": 1.0,
                "fallback_provider": "openai"
            }
        }

    def _reload_if_changed(self) -> None:
        """Check file mtime and reload if changed. Throttled by poll_interval."""
        now = time.time()

        # Throttle checks using poll_interval
        if now - self._last_check < self._poll_interval:
            return

        self._last_check = now

        try:
            if not self._config_path.exists():
                # Config file doesn't exist yet, keep using defaults
                return

            current_mtime = self._config_path.stat().st_mtime

            if current_mtime > self._last_mtime:
                with self._lock:
                    # Double-check after acquiring lock
                    if current_mtime > self._last_mtime:
                        with open(self._config_path) as f:
                            new_config = json.load(f)
                        self._config = new_config
                        self._last_mtime = current_mtime
                        print(f"[DynamicConfig] Reloaded config from {self._config_path} at {datetime.now().isoformat()}")

        except (json.JSONDecodeError, OSError) as e:
            # If config is invalid, keep using previous config
            print(f"[DynamicConfig] Error loading config: {e}. Using previous config.")

    def _get_nested(self, *keys, default=None):
        """Safely get nested config value with reload check."""
        self._reload_if_changed()

        with self._lock:
            value = self._config
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                    if value is None:
                        return default
                else:
                    return default
            return value if value is not None else default

    # Convenience accessors
    @property
    def system_prompt(self) -> str:
        """Get current system prompt."""
        return self._get_nested("prompts", "system_prompt", default="You are Zoocari the Elephant.")

    @property
    def fallback_response(self) -> str:
        """Get current fallback response."""
        return self._get_nested("prompts", "fallback_response", default="I don't know about that!")

    @property
    def model_name(self) -> str:
        """Get current model name."""
        return self._get_nested("model", "name", default="gpt-4o-mini")

    @property
    def model_temperature(self) -> float:
        """Get current model temperature."""
        return self._get_nested("model", "temperature", default=0.7)

    @property
    def model_max_tokens(self) -> int:
        """Get current model max_tokens."""
        return self._get_nested("model", "max_tokens", default=500)

    @property
    def tts_provider(self) -> str:
        """Get current TTS provider."""
        return self._get_nested("tts", "provider", default="kokoro")

    @property
    def tts_default_voice(self) -> str:
        """Get current TTS default voice."""
        return self._get_nested("tts", "default_voice", default="af_heart")

    @property
    def tts_speed(self) -> float:
        """Get current TTS speed."""
        return self._get_nested("tts", "speed", default=1.0)


# Global dynamic config instance
dynamic_config = DynamicConfig()
