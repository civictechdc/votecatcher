"""Persistence engine and repository contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable
from uuid import UUID

from sqlmodel import Session

if TYPE_CHECKING:
	from app.domain.campaign import Campaign
	from app.domain.petition import Petition
	from app.domain.voter import RegisteredVoter


@runtime_checkable
class ProvidesEngine(Protocol):
	"""Any database engine that can create sessions."""

	@property
	def name(self) -> str: ...

	@property
	def connection_url(self) -> str: ...

	def create_session(self) -> Session: ...

	def initialize(self) -> None: ...

	def health_check(self) -> bool: ...


@runtime_checkable
class PetitionRepository(Protocol):
	"""Manages petition persistence."""

	def save(self, petition: Petition) -> Petition: ...

	def find_by_id(self, petition_id: int) -> Petition | None: ...

	def find_by_campaign(self, campaign_id: UUID) -> list[Petition]: ...


@runtime_checkable
class CampaignRepository(Protocol):
	"""Manages campaign persistence."""

	def save(self, campaign: Campaign) -> Campaign: ...

	def find_by_id(self, campaign_id: UUID) -> Campaign | None: ...

	def list_active(self) -> list[Campaign]: ...

	def list_all(self) -> list[Campaign]: ...


@runtime_checkable
class VoterRepository(Protocol):
	"""Manages voter persistence."""

	def save(self, voter: RegisteredVoter) -> RegisteredVoter: ...

	def find_by_id(self, voter_id: int) -> RegisteredVoter | None: ...

	def find_by_region(self, region_id: UUID) -> list[RegisteredVoter]: ...
