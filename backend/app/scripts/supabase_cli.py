"""Supabase management CLI."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import structlog
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.supabase_service import (
	disconnect,
	provision_database,
	test_connection,
)
from app.settings import get_settings

console = Console()
logger = structlog.get_logger(__name__)


def cmd_status() -> None:
	"""Show current database status."""
	settings = get_settings()

	table = Table(title="Database Configuration")
	table.add_column("Property", style="cyan")
	table.add_column("Value", style="green")

	table.add_row("Type", settings.database.type)
	table.add_row("URL", "****")

	if settings.supabase.is_connected:
		from app.utils.masking import mask_url

		table.add_row("Supabase", "Connected")
		table.add_row("Project", mask_url(settings.supabase.url))
	else:
		table.add_row("Supabase", "Not configured")

	console.print(table)


def cmd_connect(args: argparse.Namespace) -> None:
	"""Configure Supabase connection."""
	console.print("[bold]Supabase Connection Setup[/bold]\n")

	project_url = os.getenv("SUPABASE_URL") or Prompt.ask("Project URL", default="")
	service_key = os.getenv("SUPABASE_SERVICE_KEY") or Prompt.ask(
		"Service Role Key", password=True
	)
	db_password = os.getenv("SUPABASE_DB_PASSWORD") or Prompt.ask(
		"Database Password", password=True
	)

	if not project_url.startswith("https://"):
		console.print("[red]Error: URL must start with https://[/red]")
		sys.exit(1)

	console.print("\n[yellow]Testing connection...[/yellow]")
	result = asyncio.run(test_connection(project_url, service_key))

	if not result.success:
		console.print(f"[red]Connection failed: {result.message}[/red]")
		sys.exit(1)

	console.print(
		f"[green]Connection successful! Project: {result.project_ref}[/green]"
	)

	if args.provision or Confirm.ask("Provision database now?"):  # pyright: ignore[reportAny]
		console.print("\n[yellow]Provisioning database...[/yellow]")
		prov_result = asyncio.run(
			provision_database(project_url, service_key, db_password)
		)

		if prov_result.success:
			console.print(f"[green]{prov_result.message}[/green]")
			if prov_result.tables_created:
				console.print(f"Tables: {', '.join(prov_result.tables_created)}")
		else:
			console.print(f"[red]Provisioning failed: {prov_result.message}[/red]")
			sys.exit(1)


def cmd_test() -> None:
	"""Test current Supabase connection."""
	settings = get_settings()

	if not settings.supabase.is_connected:
		console.print("[red]Supabase not configured. Run 'connect' first.[/red]")
		sys.exit(1)

	console.print("[yellow]Testing connection...[/yellow]")
	result = asyncio.run(
		test_connection(
			settings.supabase.url,
			settings.supabase.service_key.get_secret_value(),
		)
	)

	if result.success:
		console.print("[green]Connection successful![/green]")
		console.print(f"Project: {result.project_ref}")
	else:
		console.print(f"[red]Connection failed: {result.message}[/red]")
		sys.exit(1)


def cmd_provision() -> None:
	"""Run migrations against current database."""
	settings = get_settings()

	if not settings.supabase.is_connected:
		console.print("[red]Supabase not configured. Run 'connect' first.[/red]")
		sys.exit(1)

	console.print("[yellow]Running migrations...[/yellow]")
	result = asyncio.run(
		provision_database(
			settings.supabase.url,
			settings.supabase.service_key.get_secret_value(),
			settings.supabase.db_password.get_secret_value(),
		)
	)

	if result.success:
		console.print(f"[green]{result.message}[/green]")
	else:
		console.print(f"[red]Migration failed: {result.message}[/red]")
		sys.exit(1)


def cmd_disconnect() -> None:
	"""Remove Supabase configuration."""
	if not Confirm.ask("Are you sure you want to disconnect Supabase?"):
		console.print("Cancelled.")
		return

	asyncio.run(disconnect())
	console.print("[green]Supabase disconnected. Using SQLite.[/green]")


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Supabase management CLI",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Examples:
  # Interactive setup (recommended)
  python -m app.scripts.supabase_cli connect

  # Non-interactive via environment variables (CI/CD)
  SUPABASE_URL=https://xyz.supabase.co \
  SUPABASE_SERVICE_KEY=sb_xxx \
  SUPABASE_DB_PASSWORD=xxx \
    python -m app.scripts.supabase_cli connect --provision

  # Test connection
  python -m app.scripts.supabase_cli test
        """,
	)

	subparsers = parser.add_subparsers(dest="command", help="Command to run")

	subparsers.add_parser("status", help="Show current database status")  # pyright: ignore[reportUnusedCallResult]

	connect_parser = subparsers.add_parser(
		"connect", help="Configure Supabase connection"
	)
	connect_parser.add_argument(
		"--provision", action="store_true", help="Provision after connecting"
	)

	subparsers.add_parser("test", help="Test current connection")  # pyright: ignore[reportUnusedCallResult]
	subparsers.add_parser("provision", help="Run migrations")  # pyright: ignore[reportUnusedCallResult]
	subparsers.add_parser("disconnect", help="Remove Supabase configuration")  # pyright: ignore[reportUnusedCallResult]

	args = parser.parse_args()

	if args.command == "status":  # pyright: ignore[reportAny]
		cmd_status()
	elif args.command == "connect":  # pyright: ignore[reportAny]
		cmd_connect(args)
	elif args.command == "test":  # pyright: ignore[reportAny]
		cmd_test()
	elif args.command == "provision":  # pyright: ignore[reportAny]
		cmd_provision()
	elif args.command == "disconnect":  # pyright: ignore[reportAny]
		cmd_disconnect()
	else:
		parser.print_help()


if __name__ == "__main__":
	main()
