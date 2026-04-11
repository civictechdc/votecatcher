"""Database configuration API endpoints."""

import asyncio

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.api_models.database import (
    ConnectionTestResult,
    DatabaseStatus,
    ProvisionResult,
    SupabaseCredentials,
)
from app.dependencies import verify_database_api_key
from app.persistence.session import get_engine
from app.settings import get_settings

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/database",
    tags=["database"],
    dependencies=[Depends(verify_database_api_key)],
)


@router.get("/status")
async def get_database_status() -> DatabaseStatus:
    settings = get_settings()
    db_type = "supabase" if settings.supabase.is_connected else settings.database.type

    try:
        engine = get_engine()
        connected = await asyncio.to_thread(engine.health_check)
    except Exception:
        connected = False

    return DatabaseStatus(
        configured=True,
        type=db_type,
        connected=connected,
        message=f"{'Connected to' if connected else 'Unable to reach'} {db_type}",
    )


@router.post("/supabase/test")
async def test_supabase_connection(
    credentials: SupabaseCredentials,
) -> ConnectionTestResult:
    from app.services.supabase_service import test_connection

    try:
        result = await test_connection(
            project_url=credentials.project_url,
            service_key=credentials.service_key.get_secret_value(),
        )
        return result
    except Exception as e:
        logger.error("Supabase connection test failed", error_type=type(e).__name__)
        return ConnectionTestResult(
            success=False,
            message="Connection failed. Check credentials and try again.",
        )


@router.post("/supabase/provision")
async def provision_supabase(
    credentials: SupabaseCredentials,
) -> ProvisionResult:
    from app.services.supabase_service import provision_database

    try:
        result = await provision_database(
            project_url=credentials.project_url,
            service_key=credentials.service_key.get_secret_value(),
            db_password=credentials.db_password.get_secret_value(),
        )
        return result
    except Exception as e:
        logger.error("Supabase provisioning failed", error_type=type(e).__name__)
        raise HTTPException(
            status_code=500,
            detail="Provisioning failed. Check server logs for details.",
        ) from e


@router.delete("/supabase")
async def disconnect_supabase() -> dict[str, bool]:
    from app.services.supabase_service import disconnect

    try:
        await disconnect()
        return {"success": True}
    except Exception as e:
        logger.error("Supabase disconnect failed", error_type=type(e).__name__)
        raise HTTPException(
            status_code=500,
            detail="Disconnect failed. Check server logs for details.",
        ) from e
