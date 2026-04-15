from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    session_router,
    upload_router,
)
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
    yield
    await _startup.shutdown()


app = FastAPI(root_path="/api", lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(session_router)
app.include_router(upload_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
