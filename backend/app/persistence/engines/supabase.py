"""Supabase database engine."""

from __future__ import annotations

import re
from typing import override

import structlog
from pydantic import SecretStr
from sqlalchemy import Engine
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlmodel import Session, create_engine
from supabase import Client, create_client

from app.persistence.engines.base import BaseEngine

logger = structlog.get_logger(__name__)


class SupabaseEngine(BaseEngine):
	"""Supabase database engine using PostgreSQL."""

	def __init__(
		self,
		project_url: str,
		service_key: SecretStr,
		database_url: str,
	):
		self._project_url = project_url
		self._service_key = service_key
		self._database_url = database_url
		self._engine: Engine | None = None
		self._client: Client | None = None

	def _get_engine(self) -> Engine:
		if self._engine is None:
			url = self._database_url
			if url.startswith("postgresql://") and "+psycopg" not in url:
				url = url.replace("postgresql://", "postgresql+psycopg://", 1)
			self._engine = create_engine(url, echo=False)
		return self._engine

	@property
	def name(self) -> str:
		return "supabase"

	@property
	def connection_url(self) -> str:
		return re.sub(
			r"(postgresql(\+\w+)?://[^:]+:)[^@]+(@.*)",
			r"\1****\2",
			self._database_url,
		)

	@property
	@override
	def raw_engine(self) -> Engine:
		return self._get_engine()

	@property
	def client(self) -> Client:
		if self._client is None:
			self._client = create_client(
				self._project_url, self._service_key.get_secret_value()
			)
		return self._client

	def create_session(self) -> Session:
		return Session(self._get_engine())

	def initialize(self) -> None:
		self._import_models()
		logger.info("Supabase database initialized")

	def health_check(self) -> bool:
		try:
			engine = self._get_engine()
			with engine.connect() as conn:
				conn.execute(__import__("sqlalchemy").text("SELECT 1"))
			return True
		except (OperationalError, DBAPIError) as e:
			logger.error("Supabase health check failed", error=str(e))
			return False
		except Exception as e:
			logger.error("Supabase health check unexpected error", error=str(e))
			return False

	def _import_models(self) -> None:
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
