from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import warn_database_api_key_missing
from app.routers import (
    campaign_router,
    config_router,
    database_router,
    demo_router,
    job_router,
    provider_router,
    results_router,
    session_router,
    upload_router,
)


@asynccontextmanager
async def lifespan(_application: FastAPI):
    warn_database_api_key_missing()
    yield


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
app.include_router(database_router)
app.include_router(demo_router)
app.include_router(job_router)
app.include_router(provider_router)
app.include_router(results_router)
app.include_router(session_router)
app.include_router(upload_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
