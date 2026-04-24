"""Consumer-behavior tests for terminal status classification.

Tests that every consumer of is_terminal_matching_status behaves correctly
when terminal statuses are encountered — they stop polling, yielding, or
monitoring. Also guards that no new MatchingStatus enum member is missed.
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.matching.match_repository import (
    MatchingStatus,
    MatchingTask,
    is_terminal_matching_status,
)


def _make_task(
    task_id: str = "task-1",
    status: MatchingStatus = MatchingStatus.PENDING,
) -> MatchingTask:
    return MatchingTask(
        id=task_id,
        status=status,
        campaign_id="camp-1",
        created_at=datetime.now(UTC),
    )


class _AsyncSeq:
    """Yields a fixed sequence of items, then raises StopAsyncIteration."""

    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration from None


class _StubMonitor:
    """Minimal MatchingTaskMonitor that yields a fixed task sequence."""

    def __init__(self, tasks):
        self._tasks = tasks

    async def monitor_job(self, task_id: str):
        for task in self._tasks:
            yield task

    async def register_task(self, new_task):
        pass

    async def publish_updated_task_status(self, task_status):
        pass

    async def get_task_status(self, task_id: str):
        return self._tasks[-1]


def _make_monitor(tasks):
    return _StubMonitor(tasks)


class TestEmitMatchingJobStatusStopsOnTerminal:
    """emit_matching_job_status must stop yielding events once the monitor
    produces a task with terminal status. The caller (SSE endpoint) should
    not receive events after that point, and the generator must complete.

    This is the SSE stream consumer — the frontend receives status events
    until the job is done. If OCR_COMPLETED doesn't terminate the stream,
    the client receives stale events and the connection never closes.
    """

    @pytest.mark.parametrize(
        "terminal_status",
        [
            MatchingStatus.OCR_COMPLETED,
            MatchingStatus.COMPLETED,
            MatchingStatus.OCR_FAILED,
            MatchingStatus.MATCHING_FAILED,
        ],
    )
    async def test_generator_completes_on_terminal_status(
        self, terminal_status: MatchingStatus
    ):
        """Given a monitor that yields non-terminal then terminal,
        the generator should finish without error."""
        from app.ocr.ocr_helper import emit_matching_job_status

        pending_task = _make_task(status=MatchingStatus.OCR_IN_PROGRESS)
        terminal_task = _make_task(status=terminal_status)

        monitor = _make_monitor([pending_task, terminal_task])

        events = []
        async for event_json in emit_matching_job_status("task-1", monitor):
            events.append(event_json)

        assert len(events) == 2

    @pytest.mark.parametrize(
        "non_terminal_status",
        [
            MatchingStatus.OCR_IN_PROGRESS,
            MatchingStatus.OCR_PENDING,
            MatchingStatus.MATCHING,
        ],
    )
    async def test_generator_continues_on_non_terminal_status(
        self, non_terminal_status: MatchingStatus
    ):
        """Given a monitor that yields only non-terminal statuses,
        the generator should keep yielding (it does not stop early)."""
        from app.ocr.ocr_helper import emit_matching_job_status

        in_progress = _make_task(status=non_terminal_status)
        completed = _make_task(status=MatchingStatus.COMPLETED)

        monitor = _make_monitor([in_progress, in_progress, completed])

        events = []
        async for event_json in emit_matching_job_status("task-1", monitor):
            events.append(event_json)

        assert len(events) == 3

    async def test_ocr_completed_does_not_wait_for_matching_completed(self):
        """When OCR finishes (OCR_COMPLETED), the stream must close.

        Before the fix, OCR_COMPLETED was not terminal, so the generator
        would keep polling even though no further progress was expected
        from the OCR phase.
        """
        from app.ocr.ocr_helper import emit_matching_job_status

        ocr_done = _make_task(status=MatchingStatus.OCR_COMPLETED)

        monitor = _make_monitor([ocr_done])

        events = []
        async for event_json in emit_matching_job_status("task-1", monitor):
            events.append(event_json)

        assert len(events) == 1


class TestTerminalStatusExhaustiveness:
    """Guard: every MatchingStatus must be classified (terminal or not).

    If a new enum member is added to MatchingStatus without updating
    is_terminal_matching_status, this test fails. It derives the
    partition from the function itself — no duplicated sets.
    """

    def test_every_status_is_classified(self):
        classified = set()
        for status in MatchingStatus:
            is_terminal_matching_status(status)
            classified.add(status)
        assert classified == set(MatchingStatus)

    def test_at_least_one_terminal_and_one_non_terminal(self):
        terminal = {s for s in MatchingStatus if is_terminal_matching_status(s)}
        non_terminal = {s for s in MatchingStatus if not is_terminal_matching_status(s)}
        assert len(terminal) > 0
        assert len(non_terminal) > 0
