"""Field spec repository implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from sqlmodel import select

from app.data.database.model.region_field_spec import (
    RegionFieldSpecModel,
)
from app.data.database.model.schema import Region
from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)

if TYPE_CHECKING:
    from app.persistence.contracts import ProvidesEngine

logger = structlog.get_logger(__name__)


def _to_domain(model: RegionFieldSpecModel) -> RegionFieldSpecConfig:
    return RegionFieldSpecConfig(
        region_name=model.name,
        ballot_fields=[BallotField(**f) for f in model.ballot_fields],
        voter_reg_fields=[VoterRegField(**f) for f in model.voter_reg_fields],
        field_mappings=[FieldMapping(**m) for m in model.field_mappings],
        hash_fields=list(model.hash_fields),
        crop_config=CropConfig(**model.crop_config),
    )


def _to_model(
    spec: RegionFieldSpecConfig, region_id: UUID, region_key: str
) -> RegionFieldSpecModel:
    return RegionFieldSpecModel(
        region_id=region_id,
        region_key=region_key.upper(),
        name=spec.region_name,
        ballot_fields=[f.model_dump() for f in spec.ballot_fields],
        voter_reg_fields=[f.model_dump() for f in spec.voter_reg_fields],
        field_mappings=[m.model_dump() for m in spec.field_mappings],
        hash_fields=list(spec.hash_fields),
        crop_config=spec.crop_config.model_dump(),
    )


class FieldSpecRepositoryImpl:
    """Repository for field spec persistence."""

    def __init__(self, engine: ProvidesEngine):
        self._engine = engine

    def find_by_region(self, region_id: UUID) -> RegionFieldSpecConfig | None:
        with self._engine.create_session() as session:
            statement = select(RegionFieldSpecModel).where(
                RegionFieldSpecModel.region_id == region_id
            )
            model = session.exec(statement).first()
            if model is None:
                return None
            return _to_domain(model)

    def find_by_region_key(self, region_key: str) -> RegionFieldSpecConfig | None:
        with self._engine.create_session() as session:
            statement = select(RegionFieldSpecModel).where(
                RegionFieldSpecModel.region_key == region_key.upper()
            )
            model = session.exec(statement).first()
            if model is None:
                return None
            return _to_domain(model)

    def save(
        self, spec: RegionFieldSpecConfig, region_id: UUID
    ) -> RegionFieldSpecConfig:
        with self._engine.create_session() as session:
            existing = session.exec(
                select(RegionFieldSpecModel).where(
                    RegionFieldSpecModel.region_id == region_id
                )
            ).first()

            if existing:
                existing.ballot_fields = [f.model_dump() for f in spec.ballot_fields]
                existing.voter_reg_fields = [
                    f.model_dump() for f in spec.voter_reg_fields
                ]
                existing.field_mappings = [m.model_dump() for m in spec.field_mappings]
                existing.hash_fields = list(spec.hash_fields)
                existing.crop_config = spec.crop_config.model_dump()
                existing.name = spec.region_name
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return _to_domain(existing)

            region = session.exec(select(Region).where(Region.id == region_id)).first()
            model = _to_model(
                spec, region_id, region.region_key if region else "UNKNOWN"
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return _to_domain(model)

    def upsert(
        self,
        region_key: str,
        spec: RegionFieldSpecConfig,
        *,
        region_name: str,
        country_code: str = "US",
    ) -> None:
        normalized_key = region_key.upper()
        with self._engine.create_session() as session:
            region = session.exec(
                select(Region).where(Region.region_key == normalized_key)
            ).first()
            if region is None:
                region = Region(
                    region_key=normalized_key,
                    region_name=region_name,
                    country_code=country_code,
                )
                session.add(region)
                session.commit()
                session.refresh(region)

            existing = session.exec(
                select(RegionFieldSpecModel).where(
                    RegionFieldSpecModel.region_key == normalized_key
                )
            ).first()

            if existing:
                existing.ballot_fields = [f.model_dump() for f in spec.ballot_fields]
                existing.voter_reg_fields = [
                    f.model_dump() for f in spec.voter_reg_fields
                ]
                existing.field_mappings = [m.model_dump() for m in spec.field_mappings]
                existing.hash_fields = list(spec.hash_fields)
                existing.crop_config = spec.crop_config.model_dump()
                existing.name = spec.region_name
                existing.region_id = region.id
                session.add(existing)
            else:
                model = _to_model(spec, region.id, normalized_key)
                model.name = region_name
                session.add(model)

            session.commit()

    def delete(self, region_id: UUID) -> bool:
        with self._engine.create_session() as session:
            model = session.exec(
                select(RegionFieldSpecModel).where(
                    RegionFieldSpecModel.region_id == region_id
                )
            ).first()
            if model is None:
                return False
            session.delete(model)
            session.commit()
            return True

    def list_regions(self) -> list[tuple[str, str, UUID]]:
        with self._engine.create_session() as session:
            statement = select(RegionFieldSpecModel)
            models = session.exec(statement).all()
            return [(m.region_key, m.name, m.region_id) for m in models]
