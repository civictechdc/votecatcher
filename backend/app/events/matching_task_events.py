from collections.abc import AsyncGenerator
from typing import Protocol

from app.matching.match_repository import (
    CreateMatchingTask,
    MatchingTask,
    UpdateMatchingTask,
)


class MatchingTaskMonitor(Protocol):
    async def register_task(self, new_task: CreateMatchingTask) -> MatchingTask: ...

    async def publish_updated_task_status(
        self, task_status: UpdateMatchingTask
    ) -> MatchingTask: ...

    async def get_task_status(self, task_id: str) -> MatchingTask: ...

    async def monitor_job(self, task_id: str) -> AsyncGenerator[MatchingTask]: ...
