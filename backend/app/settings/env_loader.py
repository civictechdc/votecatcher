"""Shared env loading with correct priority.

Loads env vars from the correct .env file into os.environ, matching
the same priority as the Settings system:
  SETTINGS_ENV_FILE → ENV_FILE → .env.local → .env.{NODE_ENV}

This replaces bare load_dotenv() calls that incorrectly loaded .env
with lowest priority, overriding higher-priority env files.
"""

import os
from pathlib import Path

from app.settings.env_parser import load_env_into_os

BACKEND_DIR = Path(__file__).parent.parent.parent

_loaded = False


def load_env() -> None:
    """Load the correct env file into os.environ (once)."""
    global _loaded
    if _loaded:
        return
    _loaded = True

    override = os.environ.get("SETTINGS_ENV_FILE")
    if override:
        load_env_into_os(Path(override), override=True)
        return

    env_file = os.environ.get("ENV_FILE")
    if env_file:
        path = BACKEND_DIR / env_file
        if path.exists():
            load_env_into_os(path, override=True)
            return

    local_path = BACKEND_DIR / ".env.local"
    if local_path.exists():
        load_env_into_os(local_path, override=True)
        return

    node_env = os.environ.get("NODE_ENV", "development")
    env_path = BACKEND_DIR / f".env.{node_env}"
    if env_path.exists():
        load_env_into_os(env_path, override=True)
