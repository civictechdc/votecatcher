"""Crop storage adapter for abstracting image URL generation and path resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from sqlmodel import Session


@runtime_checkable
class CropStorageAdapter(Protocol):
    def get_image_url(self, crop_id: int) -> str: ...

    def get_image_path(self, crop_id: int) -> Path | None: ...


class LocalFileAdapter:
    def __init__(self, session: Session, storage_base: Path | None = None) -> None:
        self._session: Session = session
        self._storage_base = (
            storage_base or Path(os.getenv("UPLOAD_DIR", "./uploads"))
        ).resolve()

    def get_image_url(self, crop_id: int) -> str:
        return f"/api/crops/{crop_id}/image"

    def get_image_path(self, crop_id: int) -> Path | None:
        from app.data.database.model.petition_crop import PetitionCrop

        crop = self._session.get(PetitionCrop, crop_id)
        if not crop:
            return None
        path = Path(crop.stored_path).resolve()
        if not path.is_relative_to(self._storage_base):
            return None
        return path if path.is_file() else None
