import os
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated, Any

from app.data import DbClient, get_db_client
from app.data.memory_db import get_memory_db
from app.dependencies import oauth2_scheme
from app.logging.app_logger import (
    configure_dev_logging,
    configure_logger,
    configure_prod_logging,
)
from app.routers import auth, config_route, file, ocr_route, workspace
from app.settings.env_settings import AppSettings
from app.utils.app_logger import logger
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

load_dotenv()


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # During start-up
    if os.getenv("DEV_LOGGING_ENABLED", "False").lower() in ("true", "1"):
        configure_logger(True)
    else:
        configure_logger(False)

    # When shutting down
    yield


# TODO: Improve switching between different databases
if os.getenv("ENABLE_SUPABASE") == "1":
    app: FastAPI = FastAPI(
        root_path="/api", dependencies=[Depends(get_db_client)], lifespan=lifespan
    )
else:
    app: FastAPI = FastAPI(
        root_path="/api", dependencies=[Depends(get_memory_db)], lifespan=lifespan
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

app.include_router(file.router)
app.include_router(workspace.router)
app.include_router(auth.router)
app.include_router(ocr_route.router)
app.include_router(config_route.router)
