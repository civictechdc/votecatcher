"""Crop storage adapter for abstracting image URL generation and path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from sqlmodel import Session


@runtime_checkable
class CropStorageAdapter(Protocol):
    def get_image_url(self, crop_id: int) -> str: ...

    def get_image_path(self, crop_id: int) -> Path | None: ...


class LocalFileAdapter:
    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def get_image_url(self, crop_id: int) -> str:
        return f"/api/crops/{crop_id}/image"

    def get_image_path(self, crop_id: int) -> Path | None:
        from app.data.database.model.petition_crop import PetitionCrop

        crop = self._session.get(PetitionCrop, crop_id)
        if not crop:
            return None
        path = Path(crop.stored_path)
        return path if path.is_file() else None
