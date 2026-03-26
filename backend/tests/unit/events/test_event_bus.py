import asyncio
import json

import pytest

from app.events.event_bus import EventBus
from app.events.event_types import JobStatusEvent


class TestEventBus:
	def test_subscribe_returns_queue(self):
		bus = EventBus()
		queue = bus.subscribe("campaign:123")
		assert queue is not None
		assert queue.maxsize == 100

	def test_publish_derives_campaign_topic(self):
		bus = EventBus()
		queue = bus.subscribe("campaign:123")

		event = JobStatusEvent(campaign_id="123", job_id="1", status="MATCHING")
		asyncio.run(bus.publish(event))

		message = queue.get_nowait()
		data = json.loads(message)
		assert data["event_type"] == "job:status_changed"
		assert data["campaign_id"] == "123"

	def test_publish_derives_job_topic(self):
		bus = EventBus()
		queue = bus.subscribe("job:42")

		event = JobStatusEvent(job_id="42", status="MATCHING")
		asyncio.run(bus.publish(event))

		message = queue.get_nowait()
		data = json.loads(message)
		assert data["job_id"] == "42"

	def test_publish_to_global_topic(self):
		bus = EventBus()
		queue = bus.subscribe("global")

		event = JobStatusEvent(job_id="1", status="MATCHING")
		asyncio.run(bus.publish(event))

		message = queue.get_nowait()
		assert message is not None

	def test_unsubscribe_removes_queue(self):
		bus = EventBus()
		queue = bus.subscribe("campaign:123")

		bus.unsubscribe("campaign:123", queue)

		event = JobStatusEvent(campaign_id="123", job_id="1", status="MATCHING")
		asyncio.run(bus.publish(event))

		with pytest.raises(asyncio.QueueEmpty):
			queue.get_nowait()

	def test_auto_source_detection(self):
		bus = EventBus()
		queue = bus.subscribe("global")

		async def publish_from_here():
			await bus.publish(JobStatusEvent(job_id="1", status="MATCHING"))

		asyncio.run(publish_from_here())

		message = queue.get_nowait()
		data = json.loads(message)
		assert "test_event_bus" in data["source"]

	def test_queue_full_drops_gracefully(self, monkeypatch):
		bus = EventBus()
		monkeypatch.setattr(bus, "MAX_QUEUE_SIZE", 1)

		queue = bus.subscribe("global")
		queue.put_nowait("{}")

		asyncio.run(bus.publish(JobStatusEvent(job_id="1", status="MATCHING")))

	def test_cleanup_removes_empty_topics(self):
		bus = EventBus()
		queue = bus.subscribe("campaign:123")
		bus.unsubscribe("campaign:123", queue)

		bus._cleanup_empty_topics()

		assert "campaign:123" not in bus._subscribers

	def test_skip_serialization_when_no_subscribers(self):
		bus = EventBus()
		asyncio.run(bus.publish(JobStatusEvent(job_id="1", status="MATCHING")))
		assert "global" not in bus._subscribers
