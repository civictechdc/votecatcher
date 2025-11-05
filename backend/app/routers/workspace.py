import json
from typing import Annotated

from app.data.database_client import DbClient, get_db_client
from app.dependencies import oauth2_scheme
from app.schemas import WorkspaceResponse
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from postgrest import APIResponse

router: APIRouter = APIRouter(tags=["Workspace"], prefix="/workspace")


@router.get("/demo")
async def get_demo_workspace() -> WorkspaceResponse:
    return WorkspaceResponse(
        id="demo", campaign_id="demo", campaign_name="Demo workspace"
    )


@router.get("/{id}")
async def get_workspace(
    id: str,
    db: Annotated[DbClient, Depends(get_db_client)],
    token: Annotated[OAuth2PasswordBearer, Depends(oauth2_scheme)],
) -> WorkspaceResponse:

    not_found_exception: HTTPException = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Cannot locate workspace"
    )

    try:
        result: APIResponse = (
            await db.table("campaign").select("*").eq("id", id).execute()
        )
        data = result.data
        if not data and len(data) == 0:
            raise not_found_exception

        # We'll assume one record returns based on the id
        workspace = data[0]
        return WorkspaceResponse.model_validate_json(json.dumps(workspace))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot locate workspace\n{str(e)}",
        )
