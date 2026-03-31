"""Tests for persistence engines."""

from pathlib import Path

from pydantic import SecretStr
from sqlmodel import Session


class TestSqliteEngine:
	"""Tests for SQLite engine."""

	def test_creates_engine_with_name(self, tmp_path: Path):
		"""Should create engine with correct name."""
		from app.persistence.engines.sqlite import SqliteEngine

		db_path = tmp_path / "test.db"
		engine = SqliteEngine(url=f"sqlite:///{db_path}")
		assert engine.name == "sqlite"

	def test_creates_session(self, tmp_path: Path):
		"""Should create valid session."""
		from app.persistence.engines.sqlite import SqliteEngine

		db_path = tmp_path / "test.db"
		engine = SqliteEngine(url=f"sqlite:///{db_path}")
		session = engine.create_session()
		assert isinstance(session, Session)

	def test_health_check_returns_true(self, tmp_path: Path):
		"""Health check should return True for accessible database."""
		from app.persistence.engines.sqlite import SqliteEngine

		db_path = tmp_path / "test.db"
		engine = SqliteEngine(url=f"sqlite:///{db_path}")
		assert engine.health_check() is True

	def test_masks_connection_url(self, tmp_path: Path):
		"""Should not expose full path in connection_url."""
		from app.persistence.engines.sqlite import SqliteEngine

		db_path = tmp_path / "test.db"
		engine = SqliteEngine(url=f"sqlite:///{db_path}")
		url = engine.connection_url
		assert "sqlite" in url.lower()

	def test_initialize_creates_database(self, tmp_path: Path):
		"""Initialize should create database file."""
		from app.persistence.engines.sqlite import SqliteEngine

		db_path = tmp_path / "test.db"
		engine = SqliteEngine(url=f"sqlite:///{db_path}")
		engine.initialize()
		assert db_path.exists()

	def test_initialize_idempotent(self, tmp_path: Path):
		"""Initialize should be safe to call multiple times."""
		from app.persistence.engines.sqlite import SqliteEngine

		db_path = tmp_path / "test.db"
		engine = SqliteEngine(url=f"sqlite:///{db_path}")
		engine.initialize()
		engine.initialize()
		assert db_path.exists()


class TestSupabaseEngine:
	"""Tests for Supabase engine."""

	def test_name_is_supabase(self):
		"""Should have name 'supabase'."""
		from app.persistence.engines.supabase import SupabaseEngine

		engine = SupabaseEngine(
			project_url="https://test.supabase.co",
			service_key=SecretStr("test_key"),
			database_url="postgresql://test",
		)
		assert engine.name == "supabase"

	def test_health_check_without_connection(self):
		"""Health check should fail without real connection."""
		from app.persistence.engines.supabase import SupabaseEngine

		engine = SupabaseEngine(
			project_url="https://nonexistent.supabase.co",
			service_key=SecretStr("invalid"),
			database_url="postgresql://invalid",
		)
		assert engine.health_check() is False

	def test_connection_url_masks_password(self):
		"""Connection URL should mask password."""
		from app.persistence.engines.supabase import SupabaseEngine

		engine = SupabaseEngine(
			project_url="https://test.supabase.co",
			service_key=SecretStr("test_key"),
			database_url="postgresql://user:secret@host/db",  # pragma: allowlist secret
		)
		url = engine.connection_url
		assert "secret" not in url
		assert "****" in url
