from __future__ import annotations

import logging

import structlog
from typing import NotRequired, TypedDict

_fallback_log = logging.getLogger(__name__)


class OcrApiCallEvent(TypedDict, total=False):
    event: str
    gen_ai_system: str
    gen_ai_request_model: str
    latency_ms: float
    gen_ai_usage_input_tokens: NotRequired[int]
    gen_ai_usage_output_tokens: NotRequired[int]
    gen_ai_response_finish_reason: NotRequired[str]
    job_id: NotRequired[str]
    error_type: NotRequired[str]
    status_code: NotRequired[int]
    retry_attempt: NotRequired[int]


def log_ocr_call(
    *,
    provider: str,
    model: str,
    latency_ms: float,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    finish_reason: str | None = None,
    job_id: str | None = None,
    error_type: str | None = None,
    status_code: int | None = None,
    retry_attempt: int | None = None,
) -> None:
    try:
        log = structlog.get_logger(__name__)
        kwargs: dict = {
            "event": "ocr_api_call",
            "gen_ai_system": provider,
            "gen_ai_request_model": model,
            "latency_ms": latency_ms,
        }
        if input_tokens is not None:
            kwargs["gen_ai_usage_input_tokens"] = input_tokens
        if output_tokens is not None:
            kwargs["gen_ai_usage_output_tokens"] = output_tokens
        if finish_reason is not None:
            kwargs["gen_ai_response_finish_reason"] = finish_reason
        if job_id is not None:
            kwargs["job_id"] = job_id
        if error_type is not None:
            kwargs["error_type"] = error_type
        if status_code is not None:
            kwargs["status_code"] = status_code
        if retry_attempt is not None:
            kwargs["retry_attempt"] = retry_attempt

        if error_type is not None:
            log.error("ocr_api_call_failed", **kwargs)
        else:
            log.info("ocr_api_call", **kwargs)
    except Exception:
        _fallback_log.debug("ocr_logging_failed", exc_info=True)
