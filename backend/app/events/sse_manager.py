"""SSE connection manager for real-time job status updates.

Manages Server-Sent Events connections per job, allowing multiple clients
to subscribe to job status updates and receive real-time notifications.
"""

import asyncio
import json
from collections import defaultdict
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class SSEConnectionManager:
    """Manages SSE connections for job status streaming.

    Features:
    - Multiple clients per job
    - Broadcast events to all subscribers
    - Automatic cleanup on disconnect
    - Thread-safe operations
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: dict[str, list[asyncio.Queue[str]]] = defaultdict(list)
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    async def connect(self, job_id: str, queue: asyncio.Queue[str]) -> None:
        """Register a new SSE client connection.

        Args:
            job_id: Job ID to subscribe to
            queue: asyncio Queue for this connection
        """
        async with self._lock:
            self.active_connections[job_id].append(queue)

        logger.info(
            "SSE client connected",
            job_id=job_id,
            total_connections=len(self.active_connections[job_id]),
        )

    def disconnect(self, job_id: str, queue: asyncio.Queue[str]) -> None:
        """Remove an SSE client connection.

        Args:
            job_id: Job ID to unsubscribe from
            queue: asyncio Queue to remove
        """
        if job_id in self.active_connections:
            try:
                self.active_connections[job_id].remove(queue)

                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

                logger.info(
                    "SSE client disconnected",
                    job_id=job_id,
                    remaining_connections=len(self.active_connections.get(job_id, [])),
                )
            except ValueError:
                pass

    async def broadcast(
        self, job_id: str, event_type: str, data: dict[str, Any]
    ) -> int:
        """Broadcast an event to all subscribers of a job.

        Args:
            job_id: Job ID to broadcast to
            event_type: Event type (status_update, matching_progress, job_complete)
            data: Event data payload

        Returns:
            Number of clients that received the event
        """
        if job_id not in self.active_connections:
            logger.debug("No active connections for job", job_id=job_id)
            return 0

        message = format_sse_message(event_type, data)

        sent_count = 0
        for queue in self.active_connections[job_id]:
            try:
                await queue.put(message)
                sent_count += 1
            except Exception as e:
                logger.error(
                    "Failed to send SSE message",
                    job_id=job_id,
                    error=str(e),
                )

        logger.debug(
            "SSE event broadcast",
            job_id=job_id,
            event_type=event_type,
            recipients=sent_count,
        )

        return sent_count


def format_sse_message(event_type: str, data: dict[str, Any]) -> str:
    """Format SSE message according to specification.

    Args:
        event_type: Event type
        data: Event data

    Returns:
        Formatted SSE message string
    """
    data_json = json.dumps(data)
    return f"event: {event_type}\ndata: {data_json}\n\n"


sse_manager = SSEConnectionManager()
