"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_secret: str | None = None
    database_url: str | None = None

    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-opus-4-5"

    # Ralph
    ralph_timeout_minutes: int = 30
    ralph_quality_threshold: float = 0.85
    ralph_quality_floor: float = 0.70
    ralph_cost_limit_cents: int = 100

    # Environment
    environment: str = "development"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Worker
    worker_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Singleton instance
settings = Settings()
