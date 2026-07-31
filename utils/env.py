"""Helpers for loading a local .env file only when it is readable."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def get_local_env_file() -> str | None:
    """Return the project .env path when it exists and is readable."""
    if not PROJECT_ENV_FILE.is_file():
        return None

    if not os.access(PROJECT_ENV_FILE, os.R_OK):
        return None

    return str(PROJECT_ENV_FILE)


def load_local_env_if_available() -> bool:
    """Load the project .env file when it is readable."""
    env_file = get_local_env_file()
    if env_file is None:
        return False

    return load_dotenv(env_file)
