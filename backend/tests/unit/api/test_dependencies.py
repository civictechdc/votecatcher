"""Tests for app.dependencies module."""

from unittest.mock import patch


class TestWarnDatabaseApiKeyMissing:
	def test_warns_when_supabase_enabled_no_key(self):
		"""Should warn when ENABLE_SUPABASE=1 and DATABASE_API_KEY not set."""
		from app.dependencies import warn_database_api_key_missing

		with (
			patch(
				"app.dependencies.os.getenv",
				side_effect=lambda k: {
					"ENABLE_SUPABASE": "1",
					"DATABASE_API_KEY": "",
				}.get(k, ""),
			),
			patch("app.dependencies.logger") as mock_logger,
		):
			warn_database_api_key_missing()
			mock_logger.warning.assert_called_once()
			assert "DATABASE_API_KEY" in mock_logger.warning.call_args[0][0]

	def test_no_warn_when_key_set(self):
		"""Should not warn when DATABASE_API_KEY is set."""
		from app.dependencies import warn_database_api_key_missing

		with (
			patch(
				"app.dependencies.os.getenv",
				side_effect=lambda k: {
					"ENABLE_SUPABASE": "1",
					"DATABASE_API_KEY": "secret",  # pragma: allowlist secret
				}.get(k, ""),
			),
			patch("app.dependencies.logger") as mock_logger,
		):
			warn_database_api_key_missing()
			mock_logger.warning.assert_not_called()

	def test_no_warn_when_supabase_disabled(self):
		"""Should not warn when ENABLE_SUPABASE is not set."""
		from app.dependencies import warn_database_api_key_missing

		with (
			patch(
				"app.dependencies.os.getenv",
				side_effect=lambda k: {
					"ENABLE_SUPABASE": "",
					"DATABASE_API_KEY": "",
				}.get(k, ""),
			),
			patch("app.dependencies.logger") as mock_logger,
		):
			warn_database_api_key_missing()
			mock_logger.warning.assert_not_called()
