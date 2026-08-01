"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from utils.env import get_local_env_file


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_secret: str | None = None
    database_url: str | None = None

    # Claude Code
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None

    # RSS Refresh
    blog_refresh_limit_per_source: int = 20
    blog_refresh_max_sources: int | None = None
    blog_rss_failure_threshold: int = 5
    blog_rss_fetch_retries: int = 2

    # Environment
    environment: str = "development"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Worker
    worker_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=get_local_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Singleton instance
settings = Settings()
