"""Tests for env_loader priority logic."""

import importlib
import os
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent


class TestEnvLoaderPriority:
    """Verify env_loader loads the correct file based on priority."""

    def _reset_and_load(self):
        mod = importlib.import_module("app.settings.env_loader")
        mod._loaded = False
        mod.load_env()
        return mod

    def test_loads_env_file_from_settings_env_file(self, tmp_path: Path, monkeypatch):
        env_file = tmp_path / ".env.test"
        env_file.write_text("TEST_PRIORITY=settings_env_file\n")
        monkeypatch.setenv("SETTINGS_ENV_FILE", str(env_file))

        self._reset_and_load()
        assert os.getenv("TEST_PRIORITY") == "settings_env_file"

        monkeypatch.delenv("TEST_PRIORITY", raising=False)

    def test_loads_env_file_from_env_file_var(self, tmp_path: Path, monkeypatch):
        env_file = tmp_path / ".env.custom"
        env_file.write_text("TEST_PRIORITY=env_file_var\n")
        monkeypatch.delenv("SETTINGS_ENV_FILE", raising=False)
        monkeypatch.setenv("ENV_FILE", str(env_file))

        self._reset_and_load()
        assert os.getenv("TEST_PRIORITY") == "env_file_var"

        monkeypatch.delenv("TEST_PRIORITY", raising=False)

    def test_does_not_load_plain_dot_env(self, tmp_path: Path, monkeypatch):
        plain_env = tmp_path / ".env"
        plain_env.write_text("TEST_PLAIN=from_dot_env\n")
        local_env = tmp_path / ".env.local"
        local_env.write_text("TEST_LOCAL=from_env_local\n")

        monkeypatch.delenv("SETTINGS_ENV_FILE", raising=False)
        monkeypatch.delenv("ENV_FILE", raising=False)

        with patch("app.settings.env_loader.BACKEND_DIR", tmp_path):
            self._reset_and_load()

        assert os.getenv("TEST_LOCAL") == "from_env_local"
        assert os.getenv("TEST_PLAIN") is None

        monkeypatch.delenv("TEST_LOCAL", raising=False)
        monkeypatch.delenv("TEST_PLAIN", raising=False)
