import asyncio

from fastapi.responses import StreamingResponse

from ..event_bus import event_bus
from .base import EventTransport


class SSETransport(EventTransport):
    """SSE transport for browser clients using EventBus."""

    SSE_HEADERS = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    def __init__(self):
        self._active_subscriptions: dict[asyncio.Queue, str] = {}

    _MAX_LIFETIME_SECONDS = 3600

    async def _create_stream_generator(self, topic: str, queue: asyncio.Queue):
        """Create SSE generator for a topic subscription."""
        try:
            async with asyncio.timeout(self._MAX_LIFETIME_SECONDS):
                while True:
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        if message is None:
                            break
                        yield f"data: {message}\n\n"
                    except TimeoutError:
                        yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        except TimeoutError:
            pass
        finally:
            event_bus.unsubscribe(topic, queue)
            self._active_subscriptions.pop(queue, None)

    async def subscribe_to_campaign(self, campaign_id: str) -> StreamingResponse:
        """Create SSE stream for campaign events."""
        topic = f"campaign:{campaign_id}"
        queue = event_bus.subscribe(topic)
        self._active_subscriptions[queue] = topic
        return StreamingResponse(
            self._create_stream_generator(topic, queue),
            media_type="text/event-stream",
            headers=self.SSE_HEADERS,
        )

    async def subscribe_to_job(self, job_id: str) -> StreamingResponse:
        """Create SSE stream for job events."""
        topic = f"job:{job_id}"
        queue = event_bus.subscribe(topic)
        self._active_subscriptions[queue] = topic
        return StreamingResponse(
            self._create_stream_generator(topic, queue),
            media_type="text/event-stream",
            headers=self.SSE_HEADERS,
        )

    async def close(self):
        """Clean up all active connections by sending sentinel to unblock generators."""
        for queue, topic in list(self._active_subscriptions.items()):
            event_bus.unsubscribe(topic, queue)
            await queue.put(None)
        self._active_subscriptions.clear()


sse_transport = SSETransport()
