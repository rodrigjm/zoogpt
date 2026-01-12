"""
Configuration module using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, Union
from pathlib import Path


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
