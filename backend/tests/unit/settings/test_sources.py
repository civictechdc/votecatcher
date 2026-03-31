"""Tests for configuration sources."""

import threading
from pathlib import Path


class TestEnvFileSource:
	"""Tests for .env file loading."""

	def test_loads_env_file(self, tmp_path: Path):
		"""Should load variables from .env file."""
		from app.settings.sources.env_file import EnvFileSource

		env_file = tmp_path / ".env.local"
		env_file.write_text("TEST_VAR=test_value\n")

		source = EnvFileSource(env_file)
		assert source.get("TEST_VAR") == "test_value"

	def test_returns_none_for_missing_var(self, tmp_path: Path):
		"""Should return None for missing variables."""
		from app.settings.sources.env_file import EnvFileSource

		env_file = tmp_path / ".env.local"
		env_file.write_text("OTHER_VAR=value\n")

		source = EnvFileSource(env_file)
		assert source.get("MISSING_VAR") is None

	def test_returns_default_for_missing(self, tmp_path: Path):
		"""Should return default for missing variables."""
		from app.settings.sources.env_file import EnvFileSource

		env_file = tmp_path / ".env.local"
		env_file.write_text("")

		source = EnvFileSource(env_file)
		assert source.get("MISSING", default="default") == "default"

	def test_handles_missing_file(self, tmp_path: Path):
		"""Should handle missing file gracefully."""
		from app.settings.sources.env_file import EnvFileSource

		source = EnvFileSource(tmp_path / ".env.nonexistent")
		assert source.get("ANY_VAR") is None

	def test_priority_order(self, tmp_path: Path):
		"""Should load .env.local before .env.{NODE_ENV}."""
		from app.settings.sources.env_file import EnvFileSource

		local = tmp_path / ".env.local"
		local.write_text("VAR=local_value\n")

		source = EnvFileSource(local)
		assert source.get("VAR") == "local_value"

	def test_thread_safe_concurrent_access(self, tmp_path: Path):
		"""Should handle concurrent access without data corruption."""
		from app.settings.sources.env_file import EnvFileSource

		env_file = tmp_path / ".env.threads"
		env_file.write_text("THREAD_VAR=thread_value\n")

		source = EnvFileSource(env_file)
		results: list[str | None] = []
		errors: list[Exception] = []

		def read_var():
			try:
				results.append(source.get("THREAD_VAR"))
			except Exception as e:
				errors.append(e)

		threads = [threading.Thread(target=read_var) for _ in range(20)]
		for t in threads:
			t.start()
		for t in threads:
			t.join()

		assert not errors
		assert all(r == "thread_value" for r in results)


class TestEnvironmentSource:
	"""Tests for OS environment variables."""

	def test_gets_from_os_environment(self, monkeypatch):
		"""Should read from os.environ."""
		from app.settings.sources.environment import EnvironmentSource

		monkeypatch.setenv("TEST_OS_VAR", "os_value")
		source = EnvironmentSource()
		assert source.get("TEST_OS_VAR") == "os_value"

	def test_returns_none_for_missing(self):
		"""Should return None for missing env vars."""
		from app.settings.sources.environment import EnvironmentSource

		source = EnvironmentSource()
		assert source.get("DEFINITELY_NOT_SET_12345") is None
