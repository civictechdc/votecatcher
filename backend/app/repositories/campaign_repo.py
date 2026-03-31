"""Campaign repository implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from sqlmodel import select

from app.data.database.model.schema import Campaign as CampaignModel
from app.domain.campaign import Campaign

if TYPE_CHECKING:
	from app.persistence.contracts import ProvidesEngine

logger = structlog.get_logger(__name__)


def _to_domain(model: CampaignModel) -> Campaign:
	return Campaign(
		id=model.id,
		unique_name=model.unique_name,
		title=model.title,
		description=model.description,
		year=model.year,
		region_id=model.region_id,
		created_at=model.created_at,
		updated_at=model.updated_at,
	)


class CampaignRepository:
	"""Repository for Campaign persistence."""

	def __init__(self, engine: ProvidesEngine):
		self._engine = engine

	def save(self, campaign: Campaign) -> Campaign:
		with self._engine.create_session() as session:
			model = CampaignModel(
				id=campaign.id,
				unique_name=campaign.unique_name,
				title=campaign.title,
				description=campaign.description,
				year=campaign.year,
				region_id=campaign.region_id,
				created_at=campaign.created_at,
				updated_at=campaign.updated_at,
			)
			session.add(model)
			session.commit()
			session.refresh(model)
			return _to_domain(model)

	def find_by_id(self, campaign_id: UUID) -> Campaign | None:
		with self._engine.create_session() as session:
			statement = select(CampaignModel).where(CampaignModel.id == campaign_id)
			model = session.exec(statement).first()
			if model is None:
				return None
			return _to_domain(model)

	def list_active(self) -> list[Campaign]:
		from datetime import date

		current_year = str(date.today().year)
		with self._engine.create_session() as session:
			statement = select(CampaignModel).where(CampaignModel.year == current_year)
			models = session.exec(statement).all()
			return [_to_domain(m) for m in models]

	def list_all(self) -> list[Campaign]:
		with self._engine.create_session() as session:
			statement = select(CampaignModel)
			models = session.exec(statement).all()
			return [_to_domain(m) for m in models]
