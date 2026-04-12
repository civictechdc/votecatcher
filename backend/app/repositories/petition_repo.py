"""Petition repository implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import select

from app.data.database.model.petition_scan import PetitionScan
from app.domain.petition import Petition

if TYPE_CHECKING:
    from app.persistence.contracts import ProvidesEngine


def _to_domain(model: PetitionScan) -> Petition:
    return Petition(
        id=model.id,
        campaign_id=model.campaign_id,
        original_filename=model.original_filename,
        stored_path=model.stored_path,
        file_hash=model.file_hash,
        file_size=model.file_size,
        page_count=model.page_count,
        uploaded_at=model.uploaded_at,
        uploaded_by=model.uploaded_by,
    )


class PetitionRepository:
    """Repository for Petition persistence."""

    def __init__(self, engine: ProvidesEngine):
        self._engine = engine

    def save(self, petition: Petition) -> Petition:
        with self._engine.create_session() as session:
            model = PetitionScan(
                campaign_id=petition.campaign_id,
                original_filename=petition.original_filename,
                stored_path=petition.stored_path,
                file_hash=petition.file_hash,
                file_size=petition.file_size,
                page_count=petition.page_count,
                uploaded_by=petition.uploaded_by,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def find_by_id(self, petition_id: int) -> Petition | None:
        with self._engine.create_session() as session:
            statement = select(PetitionScan).where(PetitionScan.id == petition_id)
            model = session.exec(statement).first()
            if model is None:
                return None
            return _to_domain(model)

    def find_by_campaign(self, campaign_id: UUID) -> list[Petition]:
        with self._engine.create_session() as session:
            statement = select(PetitionScan).where(
                PetitionScan.campaign_id == campaign_id
            )
            models = session.exec(statement).all()
            return [_to_domain(m) for m in models]
