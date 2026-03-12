import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import structlog
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.data import DbClient, get_db_client
from app.data.database.session import get_db_session, init_db
from app.data.memory_db import get_memory_db
from app.jobs import worker as job_worker
from app.logger_config.app_logger import (
	configure_logger,
)
from app.routers import (
	campaign_router,
	config_router,
	demo_router,
	job_router,
	provider_router,
	results_router,
	session_router,
	upload_router,
)
from app.settings.env_settings import get_settings

logger = structlog.get_logger(__name__)

env_local = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_local, override=True)

CORS_HEADERS = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Methods": "*",
	"Access-Control-Allow-Headers": "*",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
	if os.getenv("DEV_LOGGING_ENABLED", "False").lower() in ("true", "1"):
		configure_logger(True)
	else:
		configure_logger(False)

	init_db()

	logger.info("Starting job worker")
	worker_task = asyncio.create_task(job_worker.start_worker())

	yield

	logger.info("Stopping job worker")
	await job_worker.stop_worker()
	worker_task.cancel()
	with contextlib.suppress(asyncio.CancelledError):
		await worker_task


# TODO: Improve switching between different databases
if os.getenv("ENABLE_SUPABASE") == "1":
	app: FastAPI = FastAPI(
		root_path="/api", dependencies=[Depends(get_db_client)], lifespan=lifespan
	)
else:
	app: FastAPI = FastAPI(
		root_path="/api",
		dependencies=[
			Depends(get_settings),
			Depends(get_memory_db),
			Depends(get_db_session),
		],
		lifespan=lifespan,
	)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	"""Validation error handler that ensures CORS headers."""
	errors = exc.errors()
	detail = errors[0]["msg"] if errors else "Validation error"
	field = errors[0].get("loc", ["unknown"])[-1] if errors else "unknown"

	return JSONResponse(
		status_code=422,
		content={
			"detail": detail,
			"error_code": "VALIDATION_ERROR",
			"retryable": False,
			"field": field,
		},
		headers=CORS_HEADERS,
	)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
	"""HTTP exception handler that ensures CORS headers on error responses."""
	return JSONResponse(
		status_code=exc.status_code,
		content={
			"detail": exc.detail,
			"error_code": f"HTTP_{exc.status_code}",
			"retryable": False,
		},
		headers=CORS_HEADERS,
	)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
	"""Global exception handler that ensures CORS headers on all error responses."""
	logger.error(
		"Unhandled exception",
		path=request.url.path,
		method=request.method,
		error=str(exc),
		exc_info=True,
	)
	return JSONResponse(
		status_code=500,
		content={
			"detail": "Something went wrong. Please try again.",
			"error_code": "INTERNAL_ERROR",
			"retryable": True,
		},
		headers=CORS_HEADERS,
	)


app.state.voter_records_df = None

origins: list[str] = [
	"http://localhost",
	"http://localhost:5173",  # To allow local front end to make calls
]

DB_CLIENT = Annotated[DbClient, Depends(get_db_client)]

app.add_middleware(
	middleware_class=CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(job_router)
app.include_router(campaign_router)
app.include_router(upload_router)
app.include_router(results_router)
app.include_router(session_router)
app.include_router(demo_router)
app.include_router(config_router)
app.include_router(provider_router)
