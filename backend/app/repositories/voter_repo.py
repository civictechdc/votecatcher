"""Voter repository implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import select

from app.data.database.model.registered_voter import RegisteredVoter as VoterModel
from app.domain.voter import RegisteredVoter

if TYPE_CHECKING:
    from app.persistence.contracts import ProvidesEngine


def _to_domain(model: VoterModel) -> RegisteredVoter:
    return RegisteredVoter(
        id=model.id,
        region_id=model.region_id,
        name_data=model.name_data,
        address_data=model.address_data,
        other_field_data=model.other_field_data,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class VoterRepository:
    """Repository for RegisteredVoter persistence."""

    def __init__(self, engine: ProvidesEngine):
        self._engine = engine

    def save(self, voter: RegisteredVoter) -> RegisteredVoter:
        with self._engine.create_session() as session:
            model = VoterModel(
                region_id=voter.region_id,
                name_data=voter.name_data,
                address_data=voter.address_data,
                other_field_data=voter.other_field_data,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def find_by_id(self, voter_id: int) -> RegisteredVoter | None:
        with self._engine.create_session() as session:
            statement = select(VoterModel).where(VoterModel.id == voter_id)
            model = session.exec(statement).first()
            if model is None:
                return None
            return _to_domain(model)

    def find_by_region(self, region_id: UUID) -> list[RegisteredVoter]:
        with self._engine.create_session() as session:
            statement = select(VoterModel).where(VoterModel.region_id == region_id)
            models = session.exec(statement).all()
            return [_to_domain(m) for m in models]
