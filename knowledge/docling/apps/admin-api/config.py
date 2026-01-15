"""
Admin Portal configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class AdminSettings(BaseSettings):
    """Admin portal settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Settings
    admin_api_port: int = 8502
    admin_api_host: str = "0.0.0.0"

    # Main app connection
    zoocari_api_url: str = "http://localhost:8501"

    # Authentication
    admin_username: str = "admin"
    admin_password: str  # Required - no default
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # Database paths (shared with main app)
    session_db_path: str = "data/sessions.db"
    lancedb_path: str = "data/zoo_lancedb"
    admin_config_path: str = "data/admin_config.json"

    # OpenAI (for KB index rebuilding)
    openai_api_key: str

    @property
    def session_db_absolute(self) -> Path:
        """Get absolute path to sessions.db."""
        path = Path(self.session_db_path)
        if not path.is_absolute():
            # Find from project root
            current = Path(__file__).resolve()
            for parent in current.parents:
                target = parent / self.session_db_path
                if target.exists():
                    return target
        return path

    @property
    def lancedb_absolute(self) -> Path:
        """Get absolute path to LanceDB."""
        path = Path(self.lancedb_path)
        if not path.is_absolute():
            current = Path(__file__).resolve()
            for parent in current.parents:
                target = parent / self.lancedb_path
                if target.exists():
                    return target
        return path


# Global settings instance
settings = AdminSettings()
