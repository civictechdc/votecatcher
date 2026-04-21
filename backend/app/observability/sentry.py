from __future__ import annotations

import logging

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]
    FastApiIntegration = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

PII_FIELDS = frozenset({
    "voter_name",
    "address",
    "email",
    "phone",
    "date_of_birth",
})


def should_scrub_pii(event: dict, hint: dict) -> dict:
    for section_key in ("contexts", "extra", "tags"):
        section = event.get(section_key)
        if not isinstance(section, dict):
            continue
        for context_name, context_data in section.items():
            if isinstance(context_data, dict):
                for field_name in list(context_data.keys()):
                    if field_name in PII_FIELDS:
                        context_data[field_name] = "[Filtered]"
            elif context_name in PII_FIELDS:
                section[context_name] = "[Filtered]"
    return event


_default_sample_rate: float = 0.1


def traces_sampler(sampling_context: dict) -> float:
    transaction_name = sampling_context.get("transaction_context", {}).get("name", "")
    if "/health" in transaction_name:
        return 0
    if sampling_context.get("parent_sampled") is not None:
        return 1.0 if sampling_context["parent_sampled"] else 0.0
    return _default_sample_rate


def init_sentry(
    dsn: str | None,
    environment: str,
    traces_sample_rate: float = 0.1,
) -> None:
    if not dsn:
        return

    global _default_sample_rate
    _default_sample_rate = traces_sample_rate

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            traces_sampler=traces_sampler,
            before_send=should_scrub_pii,
            integrations=[FastApiIntegration()],
        )
    except Exception:
        logger.warning("Sentry initialization failed", exc_info=True)
