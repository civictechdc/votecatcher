import os
from contextlib import asynccontextmanager
from typing import Annotated

import structlog
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data import DbClient, get_db_client
from app.data.database.session import get_db_session, init_db
from app.data.memory_db import get_memory_db
from app.logger_config.app_logger import (
	configure_logger,
)
from app.routers import (
	campaign_router,
	job_router,
	results_router,
	session_router,
	upload_router,
)
from app.settings.env_settings import get_settings

logger = structlog.get_logger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
	if os.getenv("DEV_LOGGING_ENABLED", "False").lower() in ("true", "1"):
		configure_logger(True)
	else:
		configure_logger(False)

	init_db()

	yield


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
