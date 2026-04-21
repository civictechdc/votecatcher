from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import event

_fallback_log = logging.getLogger(__name__)


@dataclass
class QueryLogEntry:
    statement: str
    duration_ms: float

    def is_slow(self, threshold_ms: float) -> bool:
        return self.duration_ms >= threshold_ms

    def truncated_statement(self, max_length: int = 200) -> str:
        if len(self.statement) <= max_length:
            return self.statement
        return self.statement[: max_length - 3] + "..."


def before_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: Any,
) -> None:
    try:
        conn.info["query_start_time"] = time.monotonic()
    except Exception:
        _fallback_log.debug("query_timing_start_failed", exc_info=True)


def after_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: Any,
    *,
    threshold_ms: float = 500,
    log_all: bool = False,
) -> None:
    try:
        start = conn.info.get("query_start_time")
        if start is None:
            return
        duration_ms = (time.monotonic() - start) * 1000
        entry = QueryLogEntry(statement=statement, duration_ms=duration_ms)
        log = structlog.get_logger(__name__)

        if entry.is_slow(threshold_ms):
            log.warning(
                "slow_query",
                statement=entry.truncated_statement(),
                duration_ms=round(duration_ms, 2),
                threshold_ms=threshold_ms,
            )
        elif log_all:
            log.debug(
                "query",
                statement=entry.truncated_statement(),
                duration_ms=round(duration_ms, 2),
            )
    except Exception:
        _fallback_log.debug("query_logging_failed", exc_info=True)


def attach_query_logging(
    engine: Any,
    *,
    threshold_ms: float = 500,
    log_all: bool = False,
) -> None:
    def _before(conn, cursor, statement, parameters, context, executemany):
        before_cursor_execute(conn, cursor, statement, parameters, context, executemany)

    def _after(conn, cursor, statement, parameters, context, executemany):
        after_cursor_execute(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
            threshold_ms=threshold_ms,
            log_all=log_all,
        )

    event.listen(engine, "before_cursor_execute", _before)
    event.listen(engine, "after_cursor_execute", _after)
