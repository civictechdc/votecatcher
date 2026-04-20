"""Tests for OCR API Call Logging.

Crosslink #31 — Spec: OCR API Call Logging.
Contract: structured logging with gen_ai.* OTel naming at provider boundary.
"""

import pytest
from unittest.mock import MagicMock, patch
import time

from app.observability.events import (
    OcrApiCallEvent,
    log_ocr_call,
)


class TestOcrApiCallEvent:
    """OcrApiCallEvent TypedDict structure."""

    def test_required_fields(self):
        event = OcrApiCallEvent(
            event="ocr_api_call",
            gen_ai_system="openai",
            gen_ai_request_model="gpt-4o",
            latency_ms=1500.0,
        )
        assert event["event"] == "ocr_api_call"
        assert event["gen_ai_system"] == "openai"
        assert event["gen_ai_request_model"] == "gpt-4o"
        assert event["latency_ms"] == 1500.0

    def test_optional_fields(self):
        event = OcrApiCallEvent(
            event="ocr_api_call",
            gen_ai_system="openai",
            gen_ai_request_model="gpt-4o",
            latency_ms=1500.0,
            gen_ai_usage_input_tokens=1500,
            gen_ai_usage_output_tokens=800,
            gen_ai_response_finish_reason="stop",
            job_id="job_123",
        )
        assert event["gen_ai_usage_input_tokens"] == 1500
        assert event["gen_ai_usage_output_tokens"] == 800
        assert event["gen_ai_response_finish_reason"] == "stop"
        assert event["job_id"] == "job_123"


class TestLogOcrCall:
    """log_ocr_call structured logging behavior."""

    @patch("app.observability.events.structlog.get_logger")
    def test_logs_successful_call_at_info(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        log_ocr_call(
            provider="openai",
            model="gpt-4o",
            latency_ms=1500.0,
            input_tokens=1500,
            output_tokens=800,
            finish_reason="stop",
            job_id="job_123",
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["gen_ai_system"] == "openai"
        assert call_kwargs["gen_ai_request_model"] == "gpt-4o"
        assert call_kwargs["latency_ms"] == 1500.0
        assert call_kwargs["gen_ai_usage_input_tokens"] == 1500
        assert call_kwargs["gen_ai_usage_output_tokens"] == 800
        assert call_kwargs["gen_ai_response_finish_reason"] == "stop"

    @patch("app.observability.events.structlog.get_logger")
    def test_logs_failed_call_at_error(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        log_ocr_call(
            provider="openai",
            model="gpt-4o",
            latency_ms=5000.0,
            error_type="timeout",
            status_code=408,
            retry_attempt=1,
        )
        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["error_type"] == "timeout"
        assert call_kwargs["status_code"] == 408
        assert call_kwargs["retry_attempt"] == 1

    @patch("app.observability.events.structlog.get_logger")
    def test_omits_optional_fields_when_not_provided(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        log_ocr_call(
            provider="gemini",
            model="gemini-1.5-flash",
            latency_ms=800.0,
        )
        call_kwargs = mock_logger.info.call_args[1]
        assert "gen_ai_usage_input_tokens" not in call_kwargs
        assert "gen_ai_usage_output_tokens" not in call_kwargs
        assert "job_id" not in call_kwargs

    @patch("app.observability.events.structlog.get_logger")
    def test_never_raises_on_logging_failure(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_logger.info.side_effect = Exception("log fail")
        mock_get_logger.return_value = mock_logger
        log_ocr_call(
            provider="openai",
            model="gpt-4o",
            latency_ms=100.0,
        )
