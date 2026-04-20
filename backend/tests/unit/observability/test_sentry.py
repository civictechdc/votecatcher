"""Tests for Sentry Integration.

Crosslink #29 — Spec: Sentry Integration.
Contract: optional init, no-op without DSN, PII scrubbing.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.observability.sentry import init_sentry, should_scrub_pii


class TestSentryInit:
    """Sentry initialization behavior."""

    def test_no_init_when_dsn_empty(self):
        with patch("app.observability.sentry.sentry_sdk") as mock_sdk:
            init_sentry(dsn="", environment="production")
            mock_sdk.init.assert_not_called()

    def test_no_init_when_dsn_none(self):
        with patch("app.observability.sentry.sentry_sdk") as mock_sdk:
            init_sentry(dsn=None, environment="production")
            mock_sdk.init.assert_not_called()

    def test_init_called_when_dsn_provided(self):
        with patch("app.observability.sentry.sentry_sdk") as mock_sdk:
            init_sentry(
                dsn="https://key@sentry.io/123",
                environment="production",
                traces_sample_rate=0.1,
            )
            mock_sdk.init.assert_called_once()

    def test_init_passes_environment(self):
        with patch("app.observability.sentry.sentry_sdk") as mock_sdk:
            init_sentry(
                dsn="https://key@sentry.io/123",
                environment="staging",
                traces_sample_rate=0.1,
            )
            call_kwargs = mock_sdk.init.call_args[1]
            assert call_kwargs["environment"] == "staging"

    def test_init_passes_traces_sample_rate(self):
        with patch("app.observability.sentry.sentry_sdk") as mock_sdk:
            init_sentry(
                dsn="https://key@sentry.io/123",
                environment="production",
                traces_sample_rate=0.2,
            )
            call_kwargs = mock_sdk.init.call_args[1]
            assert call_kwargs["traces_sample_rate"] == 0.2

    def test_init_never_raises_on_failure(self):
        with patch("app.observability.sentry.sentry_sdk") as mock_sdk:
            mock_sdk.init.side_effect = Exception("sentry down")
            init_sentry(
                dsn="https://key@sentry.io/123",
                environment="production",
                traces_sample_rate=0.1,
            )


class TestSentryTracesSampler:
    """Health check must be excluded from tracing."""

    def test_health_check_excluded_from_traces(self):
        from app.observability.sentry import traces_sampler

        sampling_context = {
            "transaction_context": {"name": "GET /health"},
        }
        result = traces_sampler(sampling_context)
        assert result == 0

    def test_normal_route_uses_default_rate(self):
        from app.observability.sentry import traces_sampler

        sampling_context = {
            "transaction_context": {"name": "POST /api/upload"},
            "parent_sampled": True,
        }
        result = traces_sampler(sampling_context)
        assert result > 0


class TestPIIScrubbing:
    """PII fields must be scrubbed before sending to Sentry."""

    def test_scrubs_voter_name(self):
        event = {
            "contexts": {"voter": {"voter_name": "John Doe"}},
        }
        result = should_scrub_pii(event, {})
        assert result["contexts"]["voter"]["voter_name"] == "[Filtered]"

    def test_scrubs_address(self):
        event = {
            "contexts": {"voter": {"address": "123 Main St"}},
        }
        result = should_scrub_pii(event, {})
        assert result["contexts"]["voter"]["address"] == "[Filtered]"

    def test_scrubs_email(self):
        event = {
            "extra": {"email": "test@example.com"},
        }
        result = should_scrub_pii(event, {})
        assert result["extra"]["email"] == "[Filtered]"

    def test_does_not_scrub_non_pii(self):
        event = {
            "extra": {"job_id": "abc123", "status": "completed"},
        }
        result = should_scrub_pii(event, {})
        assert result["extra"]["job_id"] == "abc123"
        assert result["extra"]["status"] == "completed"

    def test_scrubs_nested_pii(self):
        event = {
            "contexts": {
                "voter": {
                    "voter_name": "Jane Smith",
                    "phone": "555-1234",
                    "city": "Washington",
                }
            }
        }
        result = should_scrub_pii(event, {})
        voter = result["contexts"]["voter"]
        assert voter["voter_name"] == "[Filtered]"
        assert voter["phone"] == "[Filtered]"
        assert voter["city"] == "Washington"
