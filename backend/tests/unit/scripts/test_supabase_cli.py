"""Tests for Supabase management CLI."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from app.api_models.database import ConnectionTestResult, ProvisionResult


class TestCmdStatus:
	"""Tests for cmd_status command."""

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.get_settings")
	def test_status_shows_database_type(self, mock_settings_fn, mock_console):
		"""Should display database type from settings."""
		mock_settings = MagicMock()
		mock_settings.database.type = "sqlite"
		mock_settings.supabase.is_connected = False
		mock_settings_fn.return_value = mock_settings

		from app.scripts.supabase_cli import cmd_status

		cmd_status()

		mock_console.print.assert_called_once()
		table_arg = mock_console.print.call_args[0][0]
		assert hasattr(table_arg, "title")

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.get_settings")
	def test_status_shows_supabase_connected(self, mock_settings_fn, mock_console):
		"""Should show Supabase project when connected."""
		mock_settings = MagicMock()
		mock_settings.database.type = "supabase"
		mock_settings.supabase.is_connected = True
		mock_settings.supabase.url = "https://myproj.supabase.co"
		mock_settings_fn.return_value = mock_settings

		from app.scripts.supabase_cli import cmd_status

		cmd_status()

		mock_console.print.assert_called_once()


class TestCmdConnect:
	"""Tests for cmd_connect command."""

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.asyncio")
	@patch("app.scripts.supabase_cli.test_connection")
	def test_connect_noninteractive_no_provision(
		self, mock_test_conn, mock_asyncio, mock_console
	):
		"""Should connect without provisioning when user declines."""
		mock_asyncio.run.return_value = ConnectionTestResult(
			success=True,
			message="OK",
			project_ref="testproj",
		)

		from app.scripts.supabase_cli import cmd_connect

		args = argparse.Namespace(provision=False)

		with (
			patch.dict(
				"os.environ",
				{
					"SUPABASE_URL": "https://testproj.supabase.co",
					"SUPABASE_SERVICE_KEY": "x" * 100,
					"SUPABASE_DB_PASSWORD": "pass123",  # pragma: allowlist secret
				},
			),
			patch("app.scripts.supabase_cli.Confirm") as mock_confirm,
		):
			mock_confirm.ask.return_value = False
			cmd_connect(args)

		mock_asyncio.run.assert_called_once()

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.asyncio")
	@patch("app.scripts.supabase_cli.test_connection")
	def test_connect_rejects_non_https(
		self, mock_test_conn, mock_asyncio, mock_console
	):
		"""Should reject non-https URLs."""
		from app.scripts.supabase_cli import cmd_connect

		args = argparse.Namespace(provision=False)

		with (
			patch.dict(
				"os.environ",
				{
					"SUPABASE_URL": "http://bad.supabase.co",
					"SUPABASE_SERVICE_KEY": "x" * 100,
					"SUPABASE_DB_PASSWORD": "pass123",  # pragma: allowlist secret
				},
			),
			pytest.raises(SystemExit) as exc_info,
		):
			cmd_connect(args)
		assert exc_info.value.code == 1

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.asyncio")
	@patch("app.scripts.supabase_cli.test_connection")
	def test_connect_exits_on_connection_failure(
		self, mock_test_conn, mock_asyncio, mock_console
	):
		"""Should exit when connection test fails."""
		mock_asyncio.run.return_value = ConnectionTestResult(
			success=False,
			message="Connection refused",
		)

		from app.scripts.supabase_cli import cmd_connect

		args = argparse.Namespace(provision=False)

		with (
			patch.dict(
				"os.environ",
				{
					"SUPABASE_URL": "https://bad.supabase.co",
					"SUPABASE_SERVICE_KEY": "x" * 100,
					"SUPABASE_DB_PASSWORD": "pass123",  # pragma: allowlist secret
				},
			),
			pytest.raises(SystemExit) as exc_info,
		):
			cmd_connect(args)
		assert exc_info.value.code == 1

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.asyncio")
	@patch("app.scripts.supabase_cli.test_connection")
	@patch("app.scripts.supabase_cli.provision_database")
	def test_connect_with_provision_flag(
		self, mock_provision, mock_test_conn, mock_asyncio, mock_console
	):
		"""Should provision when --provision flag is set."""
		mock_asyncio.run.side_effect = [
			ConnectionTestResult(success=True, message="OK", project_ref="testproj"),
			ProvisionResult(
				success=True, message="Provisioned", tables_created=["campaign"]
			),
		]

		from app.scripts.supabase_cli import cmd_connect

		args = argparse.Namespace(provision=True)

		with patch.dict(
			"os.environ",
			{
				"SUPABASE_URL": "https://testproj.supabase.co",
				"SUPABASE_SERVICE_KEY": "x" * 100,
				"SUPABASE_DB_PASSWORD": "pass123",  # pragma: allowlist secret
			},
		):
			cmd_connect(args)

		assert mock_asyncio.run.call_count == 2


class TestCmdTest:
	"""Tests for cmd_test command."""

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.get_settings")
	def test_test_exits_when_not_configured(self, mock_settings_fn, mock_console):
		"""Should exit if Supabase not configured."""
		mock_settings = MagicMock()
		mock_settings.supabase.is_connected = False
		mock_settings_fn.return_value = mock_settings

		from app.scripts.supabase_cli import cmd_test

		with pytest.raises(SystemExit) as exc_info:
			cmd_test()
		assert exc_info.value.code == 1

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.asyncio")
	@patch("app.scripts.supabase_cli.test_connection")
	@patch("app.scripts.supabase_cli.get_settings")
	def test_test_success(
		self, mock_settings_fn, mock_test_conn, mock_asyncio, mock_console
	):
		"""Should report success on valid connection."""
		mock_settings = MagicMock()
		mock_settings.supabase.is_connected = True
		mock_settings.supabase.url = "https://myproj.supabase.co"
		mock_settings.supabase.service_key.get_secret_value.return_value = "secret"
		mock_settings_fn.return_value = mock_settings

		mock_asyncio.run.return_value = ConnectionTestResult(
			success=True,
			message="OK",
			project_ref="myproj",
		)

		from app.scripts.supabase_cli import cmd_test

		cmd_test()
		mock_asyncio.run.assert_called_once()


class TestCmdProvision:
	"""Tests for cmd_provision command."""

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.get_settings")
	def test_provision_exits_when_not_configured(self, mock_settings_fn, mock_console):
		"""Should exit if Supabase not configured."""
		mock_settings = MagicMock()
		mock_settings.supabase.is_connected = False
		mock_settings_fn.return_value = mock_settings

		from app.scripts.supabase_cli import cmd_provision

		with pytest.raises(SystemExit) as exc_info:
			cmd_provision()
		assert exc_info.value.code == 1

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.asyncio")
	@patch("app.scripts.supabase_cli.provision_database")
	@patch("app.scripts.supabase_cli.get_settings")
	def test_provision_success(
		self, mock_settings_fn, mock_provision, mock_asyncio, mock_console
	):
		"""Should call provision_database with settings."""
		mock_settings = MagicMock()
		mock_settings.supabase.is_connected = True
		mock_settings.supabase.url = "https://myproj.supabase.co"
		mock_settings.supabase.service_key.get_secret_value.return_value = "secret"
		mock_settings.supabase.db_password.get_secret_value.return_value = "pass"
		mock_settings_fn.return_value = mock_settings

		mock_asyncio.run.return_value = ProvisionResult(
			success=True,
			message="Provisioned",
		)

		from app.scripts.supabase_cli import cmd_provision

		cmd_provision()
		mock_asyncio.run.assert_called_once()


class TestCmdDisconnect:
	"""Tests for cmd_disconnect command."""

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.asyncio")
	@patch("app.scripts.supabase_cli.disconnect")
	@patch("app.scripts.supabase_cli.Confirm")
	def test_disconnect_confirmed(
		self, mock_confirm, mock_disconnect, mock_asyncio, mock_console
	):
		"""Should disconnect when confirmed."""
		mock_confirm.ask.return_value = True

		from app.scripts.supabase_cli import cmd_disconnect

		cmd_disconnect()

		mock_asyncio.run.assert_called_once()

	@patch("app.scripts.supabase_cli.console")
	@patch("app.scripts.supabase_cli.Confirm")
	def test_disconnect_cancelled(self, mock_confirm, mock_console):
		"""Should do nothing when cancelled."""
		mock_confirm.ask.return_value = False

		from app.scripts.supabase_cli import cmd_disconnect

		cmd_disconnect()

		assert mock_console.print.call_count == 1


class TestMain:
	"""Tests for main() argument parsing."""

	@patch("app.scripts.supabase_cli.cmd_status")
	def test_main_status(self, mock_cmd_status):
		"""Should dispatch to cmd_status."""
		import sys

		from app.scripts.supabase_cli import main

		with patch.object(sys, "argv", ["supabase_cli", "status"]):
			main()
		mock_cmd_status.assert_called_once()

	@patch("app.scripts.supabase_cli.cmd_connect")
	def test_main_connect(self, mock_cmd_connect):
		"""Should dispatch to cmd_connect."""
		import sys

		from app.scripts.supabase_cli import main

		with patch.object(
			sys,
			"argv",
			["supabase_cli", "connect"],
		):
			main()
		mock_cmd_connect.assert_called_once()
		call_args = mock_cmd_connect.call_args[0][0]
		assert call_args.provision is False

	@patch("app.scripts.supabase_cli.cmd_test")
	def test_main_test(self, mock_cmd_test):
		"""Should dispatch to cmd_test."""
		import sys

		from app.scripts.supabase_cli import main

		with patch.object(sys, "argv", ["supabase_cli", "test"]):
			main()
		mock_cmd_test.assert_called_once()

	@patch("app.scripts.supabase_cli.cmd_provision")
	def test_main_provision(self, mock_cmd_provision):
		"""Should dispatch to cmd_provision."""
		import sys

		from app.scripts.supabase_cli import main

		with patch.object(sys, "argv", ["supabase_cli", "provision"]):
			main()
		mock_cmd_provision.assert_called_once()

	@patch("app.scripts.supabase_cli.cmd_disconnect")
	def test_main_disconnect(self, mock_cmd_disconnect):
		"""Should dispatch to cmd_disconnect."""
		import sys

		from app.scripts.supabase_cli import main

		with patch.object(sys, "argv", ["supabase_cli", "disconnect"]):
			main()
		mock_cmd_disconnect.assert_called_once()
