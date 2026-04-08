"""Tests for worker event publishing behavior.

Tests that the worker publishes appropriate events during job processing.
"""

import json

import pytest

from app.events.event_bus import EventBus
from app.events.event_types import EventType, MetricsUpdatedEvent


class TestWorkerEventPublishing:
    """Test that MetricsUpdatedEvent can be published via event bus."""

    @pytest.mark.asyncio
    async def test_metrics_event_published_to_campaign_topic(self):
        """MetricsUpdatedEvent should be published to campaign topic."""
        bus = EventBus()
        queue = bus.subscribe("campaign:abc123")

        event = MetricsUpdatedEvent(
            campaign_id="abc123",
            job_id=1,
            total_signatures=100,
            processed=75,
            high_confidence=50,
        )
        await bus.publish(event)

        message = queue.get_nowait()
        data = json.loads(message)
        assert data["event_type"] == EventType.METRICS_UPDATED.value
        assert data["campaign_id"] == "abc123"
        assert data["job_id"] == 1
        assert data["total_signatures"] == 100
        assert data["processed"] == 75
        assert data["high_confidence"] == 50

    @pytest.mark.asyncio
    async def test_metrics_event_published_to_global_topic(self):
        """MetricsUpdatedEvent should also publish to global topic."""
        bus = EventBus()
        queue = bus.subscribe("global")

        event = MetricsUpdatedEvent(
            campaign_id="abc123",
            total_signatures=100,
            processed=75,
            high_confidence=50,
        )
        await bus.publish(event)

        message = queue.get_nowait()
        data = json.loads(message)
        assert data["event_type"] == EventType.METRICS_UPDATED.value
