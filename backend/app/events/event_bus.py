import asyncio
import inspect
from collections import defaultdict

import structlog

from .event_types import BaseEvent

_SOURCE_CACHE: dict[int, str] = {}
_SOURCE_CACHE_MAX_SIZE = 128


class EventBus:
	"""Typed pub-sub event bus with topic routing and auto-source detection."""

	MAX_QUEUE_SIZE = 100

	def __init__(self):
		self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
		self._logger = structlog.get_logger()

	def _infer_source(
		self, code_obj_id: int, has_self: bool, class_name: str, skip_frames: int = 2
	) -> str:
		"""Derive source from callsite: 'module.function' or 'module.Class.method'"""
		if code_obj_id in _SOURCE_CACHE:
			return _SOURCE_CACHE[code_obj_id]

		if len(_SOURCE_CACHE) >= _SOURCE_CACHE_MAX_SIZE:
			_SOURCE_CACHE.clear()

		frame = inspect.currentframe()
		for _ in range(skip_frames):
			frame = frame.f_back if frame else None

		if not frame:
			return "unknown"

		module = inspect.getmodule(frame)
		module_name = module.__name__.replace("app.", "") if module else "unknown"
		func_name = frame.f_code.co_name

		if has_self:
			result = f"{module_name}.{class_name}.{func_name}"
		else:
			result = f"{module_name}.{func_name}"

		_SOURCE_CACHE[code_obj_id] = result
		return result

	def _get_topics(self, event: BaseEvent) -> list[str]:
		"""Derive topics from event attributes."""
		topics = ["global"]
		if event.campaign_id:
			topics.append(f"campaign:{event.campaign_id}")
		if event.job_id:
			topics.append(f"job:{event.job_id}")
		return topics

	def _cleanup_empty_topics(self):
		"""Remove topics with no active subscribers."""
		empty = [t for t, q in self._subscribers.items() if not q]
		for topic in empty:
			del self._subscribers[topic]

	async def publish(self, event: BaseEvent, source: str | None = None) -> None:
		"""Publish event to all relevant topics."""
		if event.source is None:
			if source:
				event.source = source
			else:
				frame = inspect.currentframe()
				caller_frame = frame.f_back if frame else None
				if caller_frame:
					code_obj_id = id(caller_frame.f_code)
					has_self = "self" in caller_frame.f_locals
					class_name = (
						caller_frame.f_locals["self"].__class__.__name__
						if has_self
						else ""
					)
					event.source = self._infer_source(code_obj_id, has_self, class_name)
				else:
					event.source = "unknown"

		topics = self._get_topics(event)
		subscriber_count = sum(len(self._subscribers.get(t, set())) for t in topics)

		if subscriber_count == 0:
			self._cleanup_empty_topics()
			return

		self._logger.info(
			"event_published",
			event_id=event.event_id,
			trace_id=event.trace_id,
			event_type=event.event_type.value,
			source=event.source,
			topics=topics,
			subscriber_count=subscriber_count,
		)

		message = event.model_dump_json()

		for topic in topics:
			for queue in list(self._subscribers.get(topic, set())):
				try:
					queue.put_nowait(message)
				except asyncio.QueueFull:
					self._logger.warning("queue_full_dropped", topic=topic)

		self._cleanup_empty_topics()

	def subscribe(self, topic: str) -> asyncio.Queue:
		"""Subscribe to a specific topic. Returns queue for consumer."""
		queue: asyncio.Queue = asyncio.Queue(maxsize=self.MAX_QUEUE_SIZE)
		self._subscribers[topic].add(queue)
		return queue

	def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
		"""Unsubscribe from topic."""
		self._subscribers[topic].discard(queue)


event_bus = EventBus()
