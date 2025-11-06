import os
from typing import Annotated, Any

from app.data import DbClient, get_db_client
from app.dependencies import oauth2_scheme
from app.fuzzy_match_helper import create_ocr_matched_df, create_select_voter_records
from app.ocr.ocr_helper import create_ocr_df
from app.routers import auth, file, ocr_route, workspace
from app.settings.settings_repo import config
from app.utils.app_logger import logger
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

if os.getenv("ENABLE_SUPABASE") == "1":
    app: FastAPI = FastAPI(root_path="/api", dependencies=[Depends(get_db_client)])
else:
    app: FastAPI = FastAPI(root_path="/api")


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
