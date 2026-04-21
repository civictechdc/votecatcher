from __future__ import annotations

import sys
from typing import Any

_OCR_API_CALL_FIELDS = frozenset({
    "event",
    "gen_ai_system",
    "gen_ai_request_model",
    "latency_ms",
    "gen_ai_usage_input_tokens",
    "gen_ai_usage_output_tokens",
    "gen_ai_response_finish_reason",
    "job_id",
    "error_type",
    "status_code",
    "retry_attempt",
})

_SLOW_QUERY_FIELDS = frozenset({
    "event",
    "statement",
    "duration_ms",
    "threshold_ms",
})

_EVENT_SCHEMAS: dict[str, frozenset[str]] = {
    "ocr_api_call": _OCR_API_CALL_FIELDS,
    "ocr_api_call_failed": _OCR_API_CALL_FIELDS,
    "slow_query": _SLOW_QUERY_FIELDS,
    "query": _SLOW_QUERY_FIELDS,
}

_STRUCTLOG_META = frozenset({
    "event",
    "_record",
    "_from_structlog",
    "timestamp",
    "level",
    "request_id",
})


def validate_event_schema(
    logger: Any,
    method: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    event_name = event_dict.get("event")
    if event_name is None:
        return event_dict

    allowed = _EVENT_SCHEMAS.get(event_name)
    if allowed is None:
        return event_dict

    extra = set(event_dict.keys()) - allowed - _STRUCTLOG_META
    if extra:
        print(
            f"[event-validation] unknown fields in {event_name!r}: {sorted(extra)}",
            file=sys.stderr,
        )

    return event_dict
