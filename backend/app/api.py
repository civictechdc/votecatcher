import os
from contextlib import asynccontextmanager
from typing import Annotated, Any

import structlog
from app.data import DbClient, get_db_client
from app.data.database.local.demo_local_db import (
    create_db_and_tables,
    create_demo_records,
    get_db_session,
)
from app.data.memory_db import get_memory_db
from app.dependencies import (  # get_ocr_job_repository,
    get_campaign_repository,
    get_file_repository,
    get_matching_results_repository,
    get_matching_task_repository,
    get_ocr_provider_repository,
    get_ocr_results_repository,
    get_scanned_documents_repository,
    oauth2_scheme,
)
from app.files.file_repository import (
    RegisteredVoterRepository,
    ScannedPetitionRepository,
)
from app.logging.app_logger import (
    configure_dev_logging,
    configure_logger,
    configure_prod_logging,
)
from app.routers import auth, config_route, file_route, ocr_route, workspace
from app.settings.env_settings import AppSettings, get_settings
from app.utils.app_logger import logger
from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

logger = structlog.get_logger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # During start-up
    if os.getenv("DEV_LOGGING_ENABLED", "False").lower() in ("true", "1"):
        configure_logger(True)
    else:
        configure_logger(False)

    create_db_and_tables()
    create_demo_records()

    # When shutting down
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
            Depends(get_file_repository),
            Depends(get_scanned_documents_repository),
            # Depends(get_ocr_job_repository),
            Depends(get_matching_results_repository),
            Depends(get_campaign_repository),
            Depends(get_matching_task_repository),
            Depends(get_ocr_provider_repository),
            Depends(get_ocr_results_repository),
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

app.include_router(file_route.router)
app.include_router(workspace.router)
app.include_router(auth.router)
app.include_router(ocr_route.router)
app.include_router(config_route.router)
app.include_router(config_route.router)
app.include_router(config_route.router)
