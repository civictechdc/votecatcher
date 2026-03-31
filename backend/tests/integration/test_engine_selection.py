"""Tests for engine selection based on configuration."""


class TestEngineSelection:
	"""Tests for get_engine function."""

	def test_returns_sqlite_by_default(self, monkeypatch):
		"""Should return SQLite engine when no Supabase configured."""
		from app.persistence.engines.sqlite import SqliteEngine
		from app.persistence.session import get_engine
		from app.settings import get_settings

		get_settings.cache_clear()

		monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
		monkeypatch.delenv("SUPABASE_URL", raising=False)
		monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
		monkeypatch.delenv("SUPABASE_DB_PASSWORD", raising=False)

		get_engine.cache_clear()
		engine = get_engine()
		assert isinstance(engine, SqliteEngine)
		assert engine.name == "sqlite"

	def test_returns_supabase_when_configured(self, monkeypatch):
		"""Should return Supabase engine when configured."""
		from app.persistence.engines.supabase import SupabaseEngine
		from app.persistence.session import get_engine
		from app.settings import get_settings

		get_settings.cache_clear()

		monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
		monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
		monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test_key")
		monkeypatch.setenv("SUPABASE_DB_PASSWORD", "test_password")

		get_engine.cache_clear()
		engine = get_engine()
		assert isinstance(engine, SupabaseEngine)
		assert engine.name == "supabase"

	def test_get_engine_is_cached(self, monkeypatch):
		"""Should return same engine instance on repeated calls."""
		from app.persistence.session import get_engine
		from app.settings import get_settings

		get_settings.cache_clear()

		monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
		monkeypatch.delenv("SUPABASE_URL", raising=False)

		get_engine.cache_clear()
		engine1 = get_engine()
		engine2 = get_engine()
		assert engine1 is engine2
