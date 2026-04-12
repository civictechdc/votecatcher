"""SQLite database engine."""

from __future__ import annotations

import re
from typing import override

import structlog
from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

from app.persistence.engines.base import BaseEngine
from app.persistence.engines.model_imports import import_models

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
            logger.warning(
                "Some tables could not be created", error_type=type(e).__name__
            )
        logger.info("SQLite database initialized")

    def health_check(self) -> bool:
        try:
            with self._engine.connect() as conn:
                _ = conn.execute(text("SELECT 1"))
            return True
        except OperationalError as e:
            logger.error("SQLite health check failed", error_type=type(e).__name__)
            return False
        except Exception as e:
            logger.error(
                "SQLite health check unexpected error",
                error_type=type(e).__name__,
            )
            return False

    def _import_models(self) -> None:
        import_models()
