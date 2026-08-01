"""Tests for local environment file helpers."""

from pathlib import Path

from utils import env as env_utils


def test_get_local_env_file_returns_path_when_readable(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SUPABASE_URL=https://example.supabase.co\n", encoding="utf-8")

    monkeypatch.setattr(env_utils, "PROJECT_ENV_FILE", env_file)
    monkeypatch.setattr(env_utils.os, "access", lambda path, mode: True)

    assert env_utils.get_local_env_file() == str(env_file)


def test_get_local_env_file_returns_none_when_unreadable(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SUPABASE_URL=https://example.supabase.co\n", encoding="utf-8")

    monkeypatch.setattr(env_utils, "PROJECT_ENV_FILE", env_file)
    monkeypatch.setattr(env_utils.os, "access", lambda path, mode: False)

    assert env_utils.get_local_env_file() is None


def test_load_local_env_if_available_skips_missing_or_unreadable_files(monkeypatch):
    load_calls: list[Path] = []

    monkeypatch.setattr(env_utils, "get_local_env_file", lambda: None)
    monkeypatch.setattr(
        env_utils,
        "load_dotenv",
        lambda env_file: load_calls.append(Path(env_file)) or True,
    )

    assert env_utils.load_local_env_if_available() is False
    assert load_calls == []


def test_load_local_env_if_available_loads_readable_file(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SUPABASE_URL=https://example.supabase.co\n", encoding="utf-8")
    load_calls: list[Path] = []

    monkeypatch.setattr(env_utils, "get_local_env_file", lambda: str(env_file))
    monkeypatch.setattr(
        env_utils,
        "load_dotenv",
        lambda path: load_calls.append(Path(path)) or True,
    )

    assert env_utils.load_local_env_if_available() is True
    assert load_calls == [env_file]


def test_settings_accepts_claude_code_environment_fields():
    from config import Settings

    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_key="public-key",
        anthropic_api_key="test-key",
        anthropic_model="sonnet",
        _env_file=None,
    )

    assert settings.anthropic_api_key == "test-key"
    assert settings.anthropic_model == "sonnet"
