"""Events package - typed pub-sub for real-time updates."""

from .event_bus import event_bus
from .event_types import (
    BaseEvent,
    EventType,
    JobProgressEvent,
    JobStatusEvent,
    MetricsUpdatedEvent,
)
from .sse_manager import (
    SSEConnectionManager,
    format_sse_message,
    sse_manager,
)
from .transports.sse import SSETransport, sse_transport

__all__ = [
    "event_bus",
    "EventType",
    "BaseEvent",
    "JobStatusEvent",
    "JobProgressEvent",
    "MetricsUpdatedEvent",
    "SSEConnectionManager",
    "format_sse_message",
    "sse_manager",
    "SSETransport",
    "sse_transport",
]
