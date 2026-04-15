import asyncio
from asyncio.locks import Event
from collections.abc import AsyncGenerator
from typing import Any

import structlog

from app.data.database.model.ocr_model import OcrProviderRepository
from app.matching.match_repository import (
    CreateMatchingTask,
    MatchingTask,
    MatchTaskRepository,
    UpdateMatchingTask,
    is_terminal_matching_status,
)

logger = structlog.get_logger(__name__)

_POLL_INTERVAL: float = 5.0  # seconds


class DemoMatchingTaskMonitor:
    def __init__(
        self,
        matching_task_repository: MatchTaskRepository,
        ocr_provider_repository: OcrProviderRepository,
    ) -> None:
        self.task_repo: MatchTaskRepository = matching_task_repository
        self.ocr_provider_repo: OcrProviderRepository = ocr_provider_repository

        self._events: dict[str, asyncio.Event] = {}
        # job_id -> background poller task
        self._tasks: dict[str, asyncio.Task[MatchingTask]] = {}
        # store provider-specific clients/details if needed
        self._providers: dict[str, dict[str, Any]] = {}

    async def register_task(self, new_task: CreateMatchingTask) -> MatchingTask:
        registered_task: MatchingTask = await self.task_repo.register_matching_task(
            new_task
        )
        task_id: str = registered_task.id

        self._events[task_id] = asyncio.Event()
        self._tasks[task_id] = asyncio.create_task(
            self.task_repo.get_matching_task(task_id)
        )
        logger.debug("Registered task")
        return registered_task

    async def publish_updated_task_status(
        self, task_status: UpdateMatchingTask
    ) -> MatchingTask:
        task: MatchingTask = await self.task_repo.update_matching_task_status(
            task_status
        )
        task_id: str = task.id
        ev: Event | None = self._events.get(task_id)
        if ev:
            ev.set()
            if is_terminal_matching_status(task.status):
                self._cleanup_task(task_id)
            else:
                self._events[task_id] = asyncio.Event()

        return task

    async def get_task_status(self, task_id: str) -> MatchingTask:
        return await self.task_repo.get_matching_task(task_id)

    def _cleanup_task(self, task_id: str) -> None:
        self._events.pop(task_id, None)
        self._tasks.pop(task_id, None)
        self._providers.pop(task_id, None)

    async def monitor_job(self, task_id: str) -> AsyncGenerator[MatchingTask]:
        try:
            task: MatchingTask = await self.task_repo.get_matching_task(task_id)
            yield task
            while True:
                ev: Event | None = self._events.get(task_id)
                if not ev:
                    await asyncio.sleep(_POLL_INTERVAL)
                else:
                    try:
                        await asyncio.wait_for(ev.wait(), timeout=_POLL_INTERVAL)
                    except TimeoutError:
                        logger.warning("Timeout error")
                        new_task: MatchingTask = await self.task_repo.get_matching_task(
                            task_id
                        )
                        yield new_task
                        if is_terminal_matching_status(new_task.status):
                            return

                snapshot: MatchingTask = await self.task_repo.get_matching_task(task_id)
                yield snapshot
                if is_terminal_matching_status(snapshot.status):
                    logger.debug(
                        f"Matching task has ended with state: {snapshot.status}. "
                        f"Breaking out of loop."
                    )
                    return
        finally:
            self._cleanup_task(task_id)
