"""Application configuration via Pydantic BaseSettings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # ── Database ─────────────────────────────
    database_url: str = "postgresql+asyncpg://atlas:atlas_dev_password@localhost:5432/atlas"
    database_url_sync: str = "postgresql+psycopg2://atlas:atlas_dev_password@localhost:5432/atlas"

    # ── Redis ────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Google OAuth ─────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    gmail_scopes: str = (
        "https://www.googleapis.com/auth/gmail.readonly,"
        "https://www.googleapis.com/auth/gmail.labels"
    )

    # ── Security ─────────────────────────────
    encryption_key: str = ""
    secret_key: str = "change-me-in-production"

    # ── Sync ─────────────────────────────────
    initial_sync_days: int = 180
    sync_batch_size: int = 100

    # ── LLM ──────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    @property
    def gmail_scopes_list(self) -> list[str]:
        """Return Gmail scopes as a list."""
        return [s.strip() for s in self.gmail_scopes.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
