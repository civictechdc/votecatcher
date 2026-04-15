"""Tests for DemoMatchingTaskMonitor memory hygiene."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.data.database.local.demo_local_job_monitor import DemoMatchingTaskMonitor
from app.matching.match_repository import (
    CreateMatchingTask,
    MatchingStatus,
    MatchingTask,
    UpdateMatchingTask,
)


def _make_task(
    task_id: str = "task-1",
    status: MatchingStatus = MatchingStatus.PENDING,
    campaign_id: str = "camp-1",
) -> MatchingTask:
    return MatchingTask(
        id=task_id,
        status=status,
        campaign_id=campaign_id,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def task_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_matching_task = AsyncMock()
    repo.register_matching_task = AsyncMock()
    repo.update_matching_task_status = AsyncMock()
    return repo


@pytest.fixture
def ocr_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def monitor(task_repo: AsyncMock, ocr_repo: AsyncMock) -> DemoMatchingTaskMonitor:
    return DemoMatchingTaskMonitor(task_repo, ocr_repo)


class TestDemoMatchingTaskMonitorCleanup:
    """Scenario: internal dicts are cleaned up after terminal task."""

    @pytest.mark.parametrize(
        "terminal_status",
        [
            MatchingStatus.COMPLETED,
            MatchingStatus.CANCELLED,
            MatchingStatus.OCR_FAILED,
            MatchingStatus.MATCHING_FAILED,
            MatchingStatus.TIMED_OUT,
            MatchingStatus.MISC_ERROR,
        ],
    )
    async def test_dicts_empty_after_terminal_status_via_monitor_job(
        self,
        monitor: DemoMatchingTaskMonitor,
        task_repo: AsyncMock,
        terminal_status: MatchingStatus,
    ) -> None:
        """Scenario: monitor_job yields terminal task, then dicts are empty.

        Given a registered task
        When monitor_job yields a snapshot with terminal status
        Then _events and _tasks are both empty
        """
        task = _make_task(status=MatchingStatus.PENDING)
        terminal_task = _make_task(status=terminal_status)

        task_repo.register_matching_task.return_value = task
        task_repo.get_matching_task.side_effect = [task, task, terminal_task]

        create_task = CreateMatchingTask(campaign_id="camp-1")
        registered = await monitor.register_task(create_task)
        assert registered.id == task.id
        assert len(monitor._events) == 1
        assert len(monitor._tasks) == 1

        snapshots = []
        async for snapshot in monitor.monitor_job(task.id):
            snapshots.append(snapshot)

        assert len(snapshots) >= 2
        assert snapshots[-1].status == terminal_status
        assert len(monitor._events) == 0, f"_events not empty after {terminal_status}"
        assert len(monitor._tasks) == 0, f"_tasks not empty after {terminal_status}"

    async def test_dicts_empty_after_publish_terminal_status(
        self,
        monitor: DemoMatchingTaskMonitor,
        task_repo: AsyncMock,
    ) -> None:
        """Scenario: dicts cleaned when terminal status published via update.

        Given a registered task
        When publish_updated_task_status is called with a terminal status
        Then _events and _tasks are both empty
        """
        task = _make_task(status=MatchingStatus.PENDING)
        terminal_task = _make_task(status=MatchingStatus.COMPLETED)

        task_repo.register_matching_task.return_value = task
        task_repo.update_matching_task_status.return_value = terminal_task

        create_task = CreateMatchingTask(campaign_id="camp-1")
        await monitor.register_task(create_task)

        assert len(monitor._events) == 1

        update = UpdateMatchingTask(task_id=task.id, status=MatchingStatus.COMPLETED)
        await monitor.publish_updated_task_status(update)

        assert len(monitor._events) == 0
        assert len(monitor._tasks) == 0
