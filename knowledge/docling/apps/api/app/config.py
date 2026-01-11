"""
Configuration module using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


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

    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]


# Global settings instance
settings = Settings()
