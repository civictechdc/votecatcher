"""Supabase database engine."""

from __future__ import annotations

from pathlib import Path
from typing import override

import structlog
from pydantic import SecretStr
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlmodel import Session, create_engine
from supabase import Client, create_client

from app.persistence.engines.base import BaseEngine
from app.persistence.engines.model_imports import import_models
from app.utils.masking import mask_connection_url

logger = structlog.get_logger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parents[3]


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
		return mask_connection_url(self._database_url)

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
		self._run_alembic_migrations()
		engine = self._get_engine()
		try:
			with engine.connect() as conn:
				_ = conn.execute(text("SELECT 1"))
			logger.info("Supabase database initialized", status="connected")
		except (OperationalError, DBAPIError) as e:
			logger.warning(
				"Supabase database initialized but connection check failed",
				error_type=type(e).__name__,
				hint="Tables/migrations managed via Supabase dashboard or CLI",
			)

	def _run_alembic_migrations(self) -> None:
		alembic_ini = _BACKEND_DIR / "alembic.ini"
		if not alembic_ini.exists():
			logger.debug("alembic.ini not found — skipping migration check")
			return
		try:
			from alembic import command
			from alembic.config import Config

			alembic_cfg = Config(str(alembic_ini))
			alembic_cfg.set_main_option(
				"script_location", str(_BACKEND_DIR / "alembic")
			)
			alembic_cfg.set_main_option("sqlalchemy.url", self._database_url)
			command.upgrade(alembic_cfg, "head")
			logger.info("Alembic migrations applied", status="up_to_date")
		except Exception as e:
			logger.warning(
				"Alembic migration check skipped",
				error_type=type(e).__name__,
				hint="Ensure DATABASE_URL is accessible or run migrations manually",
			)

	def health_check(self) -> bool:
		try:
			engine = self._get_engine()
			with engine.connect() as conn:
				_ = conn.execute(text("SELECT 1"))
			return True
		except (OperationalError, DBAPIError) as e:
			logger.error("Supabase health check failed", error_type=type(e).__name__)
			return False
		except Exception as e:
			logger.error(
				"Supabase health check unexpected error", error_type=type(e).__name__
			)
			return False

	def _import_models(self) -> None:
		import_models()
