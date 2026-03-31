"""SQLite database engine."""

from __future__ import annotations

import re
from typing import override

import structlog
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

from app.persistence.engines.base import BaseEngine

logger = structlog.get_logger(__name__)


class SqliteEngine(BaseEngine):
	"""SQLite database engine."""

	def __init__(self, url: str):
		self._url = url
		self._engine = create_engine(url, echo=False)

	@property
	def name(self) -> str:
		return "sqlite"

	@property
	def connection_url(self) -> str:
		return re.sub(r"sqlite:///.*", "sqlite:///****", self._url)

	@property
	@override
	def raw_engine(self) -> Engine:
		return self._engine

	def create_session(self) -> Session:
		return Session(self._engine)

	def initialize(self) -> None:
		self._import_models()
		try:
			SQLModel.metadata.create_all(self._engine)
		except Exception as e:
			logger.warning("Some tables could not be created", error=str(e))
			SQLModel.metadata.create_all(
				self._engine,
				tables=[
					t
					for t in SQLModel.metadata.tables.values()
					if t.name
					in (
						"regions",
						"campaigns",
						"petition_scans",
						"petition_crops",
						"ocr_results",
						"match_results",
						"users",
						"sessions",
						"llm_provider_configs",
						"ocr_jobs",
						"matcher_jobs",
						"voter_list_uploads",
					)
				],
			)
		logger.info("SQLite database initialized")

	def health_check(self) -> bool:
		try:
			with self._engine.connect() as conn:
				conn.execute(__import__("sqlalchemy").text("SELECT 1"))
			return True
		except OperationalError as e:
			logger.error("SQLite health check failed", error=str(e))
			return False
		except Exception as e:
			logger.error("SQLite health check unexpected error", error=str(e))
			return False

	def _import_models(self) -> None:
		from app.data.database.model.jobs import (  # noqa: F401
			MatcherJob,
			OcrJob,
		)
		from app.data.database.model.llm_provider_config import (
			LlmProviderConfig,  # noqa: F401
		)
		from app.data.database.model.match_result import MatchResult  # noqa: F401
		from app.data.database.model.ocr_result import OcrResult  # noqa: F401
		from app.data.database.model.petition_crop import PetitionCrop  # noqa: F401
		from app.data.database.model.petition_scan import PetitionScan  # noqa: F401
		from app.data.database.model.registered_voter import (
			RegisteredVoter,  # noqa: F401
		)
		from app.data.database.model.schema import Campaign, Region  # noqa: F401
		from app.data.database.model.session import (
			Session as SessionModel,  # noqa: F401
		)
		from app.data.database.model.user import User  # noqa: F401
		from app.data.database.model.voter_list_upload import (
			VoterListUpload,  # noqa: F401
		)
