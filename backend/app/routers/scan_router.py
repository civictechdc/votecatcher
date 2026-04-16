"""Scan router for serving scan page images."""

import asyncio
import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pdf2image import convert_from_path
from sqlmodel import Session

from app.dependencies import get_session

MAX_CONCURRENT_PAGE_READS = 20

router = APIRouter(prefix="/scans", tags=["scans"])

SessionDep = Annotated[Session, Depends(get_session)]

_CACHE_HEADERS = {"Cache-Control": "public, max-age=86400, immutable"}

_page_semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGE_READS)


def _cleanup_temp(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


@router.get("/{scan_id}/pages/{page_number}/image")
async def get_scan_page_image(
    scan_id: int,
    page_number: int,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    from app.data.database.model.petition_scan import PetitionScan

    async with _page_semaphore:
        scan = session.get(PetitionScan, scan_id)
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id} not found",
            )

        from pathlib import Path

        pdf_path = Path(scan.stored_path)
        if not pdf_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan file for {scan_id} not found on disk",
            )

        try:
            images = convert_from_path(
                str(pdf_path),
                first_page=page_number,
                last_page=page_number,
                dpi=150,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to render page {page_number}: {e}",
            ) from e

        if not images:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page_number} not found in scan {scan_id}",
            )

        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        images[0].save(tmp_path, "PNG")

        background_tasks.add_task(_cleanup_temp, tmp_path)

        return FileResponse(
            tmp_path,
            media_type="image/png",
            headers=_CACHE_HEADERS,
        )
