"""Supabase connection and provisioning service."""

import asyncio
import os
import re
from pathlib import Path

import structlog

from app.api_models.database import ConnectionTestResult, ProvisionResult
from app.settings.settings import BACKEND_DIR, get_settings
from app.utils.masking import mask_url

logger = structlog.get_logger(__name__)


async def test_connection(
    project_url: str,
    service_key: str,
) -> ConnectionTestResult:
    """Test Supabase credentials without saving."""
    from supabase import Client, create_client

    try:
        client: Client = create_client(project_url, service_key)

        match = re.search(
            r"^https://([a-z0-9-]+)(?:\.supabase)?\.[a-z.]+$", project_url
        )
        project_ref = match.group(1) if match else None

        auth_ok = True
        try:
            session = client.auth.get_session()
            if session is None:
                auth_ok = False
        except Exception:
            logger.warning("Auth session check failed — credentials may be invalid")
            auth_ok = False

        if not auth_ok:
            return ConnectionTestResult(
                success=False,
                message="Auth check failed. Verify credentials and try again.",
                project_ref=project_ref,
            )

        return ConnectionTestResult(
            success=True,
            message="Connection successful",
            project_ref=project_ref,
        )
    except Exception as e:
        logger.error("Supabase connection test failed", error_type=type(e).__name__)
        return ConnectionTestResult(
            success=False,
            message="Connection failed. Check credentials and try again.",
        )


async def provision_database(
    project_url: str,
    service_key: str,
    db_password: str,
) -> ProvisionResult:
    """Save credentials and provision database."""
    try:
        test_result = await test_connection(project_url, service_key)
        if not test_result.success:
            return ProvisionResult(
                success=False,
                message=test_result.message,
            )

        env_file = BACKEND_DIR / ".env.local"
        await asyncio.to_thread(
            update_env_file,
            env_file,
            {
                "SUPABASE_URL": project_url,
                "SUPABASE_SERVICE_KEY": service_key,
                "SUPABASE_DB_PASSWORD": db_password,
            },
        )

        get_settings.cache_clear()

        from app.persistence.session import clear_engine_cache

        clear_engine_cache()

        tables_created = await asyncio.to_thread(_run_migrations)

        logger.info(
            "Supabase provisioned successfully",
            project_url=mask_url(project_url),
        )

        return ProvisionResult(
            success=True,
            message="Supabase connected and database provisioned",
            tables_created=tables_created,
        )
    except Exception as e:
        logger.error("Supabase provisioning failed", error_type=type(e).__name__)
        return ProvisionResult(
            success=False,
            message="Provisioning failed. Check server logs for details.",
        )


async def disconnect() -> None:
    """Remove Supabase configuration."""
    from app.persistence.session import clear_engine_cache

    env_file = BACKEND_DIR / ".env.local"

    await asyncio.to_thread(
        update_env_file,
        env_file,
        {
            "SUPABASE_URL": "",
            "SUPABASE_SERVICE_KEY": "",
            "SUPABASE_DB_PASSWORD": "",
        },
        remove_empty=True,
    )

    get_settings.cache_clear()
    clear_engine_cache()

    logger.info("Supabase disconnected")


def update_env_file(
    env_file: Path,
    updates: dict[str, str],
    remove_empty: bool = False,
) -> None:
    """Update environment file with new values."""
    try:
        lines = env_file.read_text().splitlines() if env_file.exists() else []
    except OSError as e:
        raise OSError(f"Failed to read {env_file}: {e}") from e

    updated_keys: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        if "=" in line and not line.startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                updated_keys.add(key)
                if remove_empty and not updates[key]:
                    continue
                new_lines.append(f"{key}={updates[key]}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            if remove_empty and not value:
                continue
            new_lines.append(f"{key}={value}")

    try:
        _ = env_file.write_text("\n".join(new_lines) + "\n")
    except OSError as e:
        raise OSError(f"Failed to write secrets to {env_file}: {e}") from e
    try:
        os.chmod(env_file, 0o600)
    except OSError:
        logger.warning("Failed to set file permissions on env file", path=str(env_file))


def _run_migrations() -> list[str]:
    """Run database migrations and return list of tables created."""
    from sqlmodel import SQLModel

    from app.persistence.session import get_engine

    engine = get_engine()

    if engine.name == "supabase":
        alembic_ini = BACKEND_DIR / "alembic.ini"
        if not alembic_ini.exists():
            logger.warning(
                "alembic.ini not found — skipping migration",
                path=str(alembic_ini),
            )
            engine.initialize()
            return [table.name for table in SQLModel.metadata.sorted_tables]
        try:
            from alembic import command
            from alembic.config import Config

            alembic_cfg = Config(str(alembic_ini))
            alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            logger.warning("Alembic migration warning", error_type=type(e).__name__)
            engine.initialize()
    else:
        engine.initialize()

    return [table.name for table in SQLModel.metadata.sorted_tables]
