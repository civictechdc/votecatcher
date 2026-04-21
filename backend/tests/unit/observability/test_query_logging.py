"""Tests for Database Query Logging.

Crosslink #30 — Spec: DB Query Logging.
Contract: slow queries logged at WARNING, all queries at DEBUG when LOG_SQL=true.
"""

import time
from unittest.mock import MagicMock, patch

from app.observability.query_logging import (
    QueryLogEntry,
    before_cursor_execute,
    after_cursor_execute,
    attach_query_logging,
)


class TestQueryLogEntry:
    """QueryLogEntry data structure."""

    def test_creates_with_required_fields(self):
        entry = QueryLogEntry(
            statement="SELECT * FROM voters",
            duration_ms=12.5,
        )
        assert entry.statement == "SELECT * FROM voters"
        assert entry.duration_ms == 12.5

    def test_is_slow_above_threshold(self):
        entry = QueryLogEntry(
            statement="SELECT * FROM voters",
            duration_ms=600,
        )
        assert entry.is_slow(threshold_ms=500)

    def test_is_not_slow_below_threshold(self):
        entry = QueryLogEntry(
            statement="SELECT * FROM voters",
            duration_ms=200,
        )
        assert not entry.is_slow(threshold_ms=500)

    def test_is_slow_at_exact_threshold(self):
        entry = QueryLogEntry(
            statement="SELECT * FROM voters",
            duration_ms=500,
        )
        assert entry.is_slow(threshold_ms=500)

    def test_statement_truncated_when_long(self):
        long_sql = "SELECT * FROM voters WHERE " + "x = 1 AND " * 50
        entry = QueryLogEntry(statement=long_sql, duration_ms=10)
        assert len(entry.truncated_statement(max_length=200)) <= 200

    def test_statement_not_truncated_when_short(self):
        short_sql = "SELECT 1"
        entry = QueryLogEntry(statement=short_sql, duration_ms=10)
        assert entry.truncated_statement(max_length=200) == short_sql


class TestBeforeCursorExecute:
    """before_cursor_execute stores start time in connection info."""

    def test_stores_start_time(self):
        conn = MagicMock()
        conn.info = {}
        before_cursor_execute(conn, None, "SELECT 1", None, None, None)
        assert "query_start_time" in conn.info

    def test_does_not_raise(self):
        conn = MagicMock()

        class ExplodingDict(dict):
            def __setitem__(self, key, value):
                raise RuntimeError("boom")

        conn.info = ExplodingDict()
        before_cursor_execute(conn, None, "SELECT 1", None, None, None)


class TestAfterCursorExecute:
    """after_cursor_execute logs slow queries and optionally all queries."""

    @patch("app.observability.query_logging.structlog.get_logger")
    def test_logs_slow_query_at_warning(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        conn = MagicMock()
        conn.info = {"query_start_time": 0}
        after_cursor_execute(
            conn,
            None,
            "SELECT * FROM large_table",
            None,
            None,
            None,
            threshold_ms=0,
            log_all=False,
        )
        mock_logger.warning.assert_called()

    @patch("app.observability.query_logging.structlog.get_logger")
    def test_logs_all_queries_when_log_all_true(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        conn = MagicMock()
        conn.info = {"query_start_time": time.monotonic()}
        after_cursor_execute(
            conn,
            None,
            "SELECT 1",
            None,
            None,
            None,
            threshold_ms=5000,
            log_all=True,
        )
        mock_logger.debug.assert_called()

    @patch("app.observability.query_logging.structlog.get_logger")
    def test_does_not_log_fast_query_when_log_all_false(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        conn = MagicMock()
        import time

        conn.info = {"query_start_time": time.time()}
        after_cursor_execute(
            conn,
            None,
            "SELECT 1",
            None,
            None,
            None,
            threshold_ms=5000,
            log_all=False,
        )
        mock_logger.warning.assert_not_called()
        mock_logger.debug.assert_not_called()

    @patch("app.observability.query_logging.structlog.get_logger")
    def test_never_raises_on_error(self, mock_get_logger):
        mock_get_logger.side_effect = Exception("logger broken")
        conn = MagicMock()
        conn.info = {"query_start_time": 0}
        after_cursor_execute(
            conn,
            None,
            "SELECT 1",
            None,
            None,
            None,
            threshold_ms=0,
            log_all=False,
        )


class TestAttachQueryLogging:
    """attach_query_logging wires event listeners to engine."""

    def test_attaches_listeners(self):
        mock_engine = MagicMock()
        mock_event = MagicMock()
        with patch("app.observability.query_logging.event") as mock_event_mod:
            mock_event_mod.listen = mock_event
            attach_query_logging(mock_engine, threshold_ms=500, log_all=False)
            assert mock_event.call_count >= 2
