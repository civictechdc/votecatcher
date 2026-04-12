"""Load configuration from .env files."""

import threading
from pathlib import Path

import structlog

from app.settings.env_parser import parse_env_file

logger = structlog.get_logger(__name__)


class EnvFileSource:
    """Load configuration from a .env file."""

    def __init__(self, path: Path):
        self._path = path
        self._values: dict[str, str | None] = {}
        self._loaded = False
        self._lock = threading.Lock()

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        with self._lock:
            if self._loaded:
                return

            if self._path.exists():
                self._values = parse_env_file(self._path)
                logger.debug("Loaded env file", path=str(self._path))
            else:
                logger.debug("Env file not found", path=str(self._path))

            self._loaded = True

    def get(self, key: str, default: str | None = None) -> str | None:
        self._ensure_loaded()
        return self._values.get(key, default)
