"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_key: str

    # Anthropic
    anthropic_api_key: str

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
