import asyncio
import inspect
from collections import defaultdict

import structlog

from .event_types import BaseEvent


class EventBus:
	"""Typed pub-sub event bus with topic routing and auto-source detection."""

	MAX_QUEUE_SIZE = 100

	def __init__(self):
		self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
		self._logger = structlog.get_logger()

	def _infer_source(self, skip_frames: int = 2) -> str:
		"""Derive source from callsite: 'module.function' or 'module.Class.method'"""
		frame = inspect.currentframe()
		for _ in range(skip_frames):
			frame = frame.f_back if frame else None

		if not frame:
			return "unknown"

		module = inspect.getmodule(frame)
		module_name = module.__name__.replace("app.", "") if module else "unknown"
		func_name = frame.f_code.co_name

		if "self" in frame.f_locals:
			class_name = frame.f_locals["self"].__class__.__name__
			return f"{module_name}.{class_name}.{func_name}"

		return f"{module_name}.{func_name}"

	def _get_topics(self, event: BaseEvent) -> list[str]:
		"""Derive topics from event attributes."""
		topics = ["global"]
		if event.campaign_id:
			topics.append(f"campaign:{event.campaign_id}")
		if event.job_id:
			topics.append(f"job:{event.job_id}")
		return topics

	async def publish(self, event: BaseEvent, source: str | None = None) -> None:
		"""Publish event to all relevant topics."""
		if event.source is None:
			event.source = source or self._infer_source()

		topics = self._get_topics(event)

		self._logger.info(
			"event_published",
			event_id=event.event_id,
			trace_id=event.trace_id,
			event_type=event.event_type.value,
			source=event.source,
			topics=topics,
			subscriber_count=sum(len(self._subscribers[t]) for t in topics),
		)

		message = event.model_dump_json()

		for topic in topics:
			for queue in list(self._subscribers.get(topic, set())):
				try:
					queue.put_nowait(message)
				except asyncio.QueueFull:
					self._logger.warning("queue_full_dropped", topic=topic)

	def subscribe(self, topic: str) -> asyncio.Queue:
		"""Subscribe to a specific topic. Returns queue for consumer."""
		queue: asyncio.Queue = asyncio.Queue(maxsize=self.MAX_QUEUE_SIZE)
		self._subscribers[topic].add(queue)
		return queue

	def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
		"""Unsubscribe from topic."""
		self._subscribers[topic].discard(queue)


event_bus = EventBus()
