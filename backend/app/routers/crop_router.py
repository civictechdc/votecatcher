"""Crop image serving router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.dependencies import get_session

router = APIRouter(prefix="/crops", tags=["crops"])

SessionDep = Annotated[Session, Depends(get_session)]

_CACHE_HEADERS = {"Cache-Control": "public, max-age=86400, immutable"}


@router.get("/{crop_id}/image")
def get_crop_image(
    crop_id: int,
    session: SessionDep,
) -> FileResponse:
    from app.storage.crop_storage import LocalFileAdapter

    adapter = LocalFileAdapter(session)
    path = adapter.get_image_path(crop_id)

    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop image {crop_id} not found",
        )

    return FileResponse(
        path,
        media_type="image/png",
        headers=_CACHE_HEADERS,
    )
