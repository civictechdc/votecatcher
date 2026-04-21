from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.middleware.cors import build_cors_config
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.rate_limit import RateLimitConfig, create_rate_limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.observability.health import HealthChecker
from app.observability.sentry import init_sentry as _init_sentry_lib
from app.routers import (
    campaign_router,
    config_router,
    crop_router,
    database_router,
    demo_router,
    events_router,
    job_router,
    provider_router,
    region_router,
    results_router,
    scan_router,
    session_router,
    upload_router,
)
from app.settings.settings import get_settings
from app.startup import ApplicationStartup


def _default_spec_loader():
    from app.persistence.session import get_engine
    from app.repositories.field_spec_repo import FieldSpecRepositoryImpl
    from app.services.field_spec_service import FieldSpecService

    engine = get_engine()
    repo = FieldSpecRepositoryImpl(engine)
    service = FieldSpecService(repo)
    return service.load_all_specs(fail_fast=True)


_startup = ApplicationStartup(spec_loader=_default_spec_loader)


@asynccontextmanager
async def lifespan(_application: FastAPI):
    await _startup.startup()
    _init_sentry(_application)
    yield
    await _startup.shutdown()


def _init_sentry(application: FastAPI) -> None:
    s = get_settings()
    _init_sentry_lib(
        dsn=s.sentry_dsn or None,
        environment=s.environment,
        traces_sample_rate=s.sentry_traces_sample_rate,
    )


app = FastAPI(root_path="/api", lifespan=lifespan)

settings = get_settings()

is_production = settings.environment == "production"

app.add_middleware(
    SecurityHeadersMiddleware,
    is_production=is_production,
)

cors_config = build_cors_config(settings.environment, settings.cors_origins)
app.add_middleware(CORSMiddleware, **cors_config)

rate_limit_config = RateLimitConfig(
    enabled=settings.rate_limit_enabled,
    default_limit=settings.rate_limit_default,
    upload_limit=settings.rate_limit_upload,
    job_create_limit=settings.rate_limit_job_create,
)
limiter = create_rate_limiter(rate_limit_config)
if limiter is not None:
    app.state.limiter = limiter

app.include_router(campaign_router)
app.include_router(config_router)
app.include_router(crop_router)
app.include_router(database_router)
app.include_router(demo_router)
app.include_router(events_router)
app.include_router(job_router)
app.include_router(provider_router)
app.include_router(region_router)
app.include_router(results_router)
app.include_router(scan_router)
app.include_router(session_router)
app.include_router(upload_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
