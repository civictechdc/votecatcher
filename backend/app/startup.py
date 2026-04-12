"""Application startup lifecycle manager.

Encapsulates the startup and shutdown sequences, coordinating database
initialization, configuration validation, and background worker lifecycle.

Uses dependency injection so tests can provide lightweight implementations
instead of mocking internal modules.
"""

import asyncio
from collections.abc import Callable
from typing import Any

import structlog

from app.data.database.session import init_db
from app.dependencies import warn_database_api_key_missing
from app.jobs.worker import start_worker, stop_worker

logger = structlog.get_logger(__name__)


class ApplicationStartup:
    """Application lifecycle manager.

    Coordinates startup and shutdown:
    - Startup: initialize database, validate config, launch background worker
    - Shutdown: stop background worker gracefully

    Accepts optional overrides for each lifecycle step, enabling
    testability through dependency injection.
    """

    def __init__(
        self,
        *,
        db_initializer: Callable[[], None] = init_db,
        worker_starter: Callable[[], Any] = start_worker,
        worker_stopper: Callable[[], Any] = stop_worker,
        config_validator: Callable[[], None] = warn_database_api_key_missing,
    ) -> None:
        self._db_initializer = db_initializer
        self._worker_starter = worker_starter
        self._worker_stopper = worker_stopper
        self._config_validator = config_validator
        self._worker_task: asyncio.Task | None = None

    async def startup(self) -> None:
        """Execute startup sequence: init DB → validate config → launch worker."""
        self._db_initializer()
        self._config_validator()
        self._worker_task = asyncio.create_task(self._worker_starter())
        logger.info("Application startup complete")

    async def shutdown(self) -> None:
        """Execute shutdown sequence: stop worker, cancel task if needed."""
        await self._worker_stopper()
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._worker_task = None
        logger.info("Application shutdown complete")

    @property
    def is_worker_running(self) -> bool:
        """Whether the background worker task is active."""
        return self._worker_task is not None and not self._worker_task.done()
