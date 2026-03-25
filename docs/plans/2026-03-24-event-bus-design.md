# Event Bus Design

**Date:** 2026-03-24
**Status:** Approved
**Scope:** Phase 10 Enhancement (SSE)
**Effort:** ~5 hours

---

## Summary

A typed pub-sub event bus that decouples event publishers (workers, services) from subscribers (SSE transports). Replaces HTTP polling with real-time SSE streams for dashboard and job list updates. Designed for extensibility to support WebSocket transport in the future.

## Goals

- Eliminate HTTP polling from frontend (dashboard, jobs list)
- Provide campaign-scoped real-time updates (all jobs in a campaign)
- Decouple publishers from subscribers for maintainability
- Enable future WebSocket addition without refactoring

## Non-Goals

- WebSocket implementation (deferred)
- Event persistence/replay
- Guaranteed delivery (in-memory only, acceptable for status updates)

---

## Architecture

### Component Structure

```
backend/app/events/
├── __init__.py           # Public API exports
├── event_types.py        # Typed event definitions (Pydantic)
├── event_bus.py          # Core pub-sub with auto-source
└── transports/
    ├── __init__.py
    ├── base.py           # Transport interface
    └── sse.py            # SSE implementation
```

### Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Worker          │     │ Upload Service  │     │ Any Publisher   │
│                 │     │                 │     │                 │
│ event_bus.      │     │ event_bus.      │     │ event_bus.      │
│   publish(event)│     │   publish(event)│     │   publish(event)│
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │      EVENT BUS         │
                    │  (in-memory, typed)    │
                    │                        │
                    │  Topics derived from   │
                    │  event attributes:     │
                    │  • campaign:{id}       │
                    │  • job:{id}            │
                    │  • global              │
                    └───────────┬────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ SSE Transport   │  │ WS Transport    │  │ Future: Webhook │
│ subscribe(topic)│  │ subscribe(topic)│  │ subscribe(event)│
│ (implemented)   │  │ (future)        │  │ (future)        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Boundary Contracts

| Role | Knows About | Doesn't Know About |
|------|-------------|-------------------|
| **Frontend** | SSE URLs, event JSON schema | Event bus, topics, queues |
| **Router** | URL → transport mapping | Event bus internals |
| **Transport** | `subscribe(topic)`, `unsubscribe()` | Publishers, event creation |
| **Event Bus** | Events, topics, queues | Transports, HTTP, publishers |
| **Publisher** | `publish(event)` | Transports, subscribers, topics |

---

## Event Types

```python
# event_types.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
from uuid import uuid4

class EventType(str, Enum):
    JOB_STATUS_CHANGED = "job:status_changed"
    JOB_PROGRESS = "job:progress"
    METRICS_UPDATED = "metrics:updated"

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: str | None = None
    source: str | None = None  # Auto-filled by bus
    campaign_id: str | None = None
    job_id: int | None = None

class JobStatusEvent(BaseEvent):
    event_type: Literal[EventType.JOB_STATUS_CHANGED]
    status: str
    previous_status: str | None

class JobProgressEvent(BaseEvent):
    event_type: Literal[EventType.JOB_PROGRESS]
    processed: int
    total: int
    percentage: float

class MetricsUpdatedEvent(BaseEvent):
    event_type: Literal[EventType.METRICS_UPDATED]
    total_signatures: int
    processed: int
    high_confidence: int
```

---

## Event Bus Implementation

```python
# event_bus.py
import asyncio
import inspect
import structlog
from collections import defaultdict
from .event_types import BaseEvent

class EventBus:
    """Typed publish-subscribe event bus with topic routing and auto-source detection."""

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
            subscriber_count=sum(len(self._subscribers[t]) for t in topics)
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
```

---

## Transport Interface

```python
# transports/base.py
from abc import ABC, abstractmethod

class EventTransport(ABC):
    """Abstract base for event transport implementations."""

    @abstractmethod
    async def subscribe_to_campaign(self, campaign_id: str):
        """Subscribe to all events for a campaign."""
        ...

    @abstractmethod
    async def subscribe_to_job(self, job_id: int):
        """Subscribe to all events for a job."""
        ...

    @abstractmethod
    async def close(self):
        """Clean up subscriptions."""
        ...
```

---

## SSE Transport

```python
# transports/sse.py
import asyncio
from fastapi.responses import StreamingResponse
from ..event_bus import event_bus

class SSETransport(EventTransport):
    """SSE transport for browser clients."""

    def __init__(self):
        self._active_queues: set[asyncio.Queue] = set()

    async def subscribe_to_campaign(self, campaign_id: str) -> StreamingResponse:
        """Create SSE stream for campaign events."""
        topic = f"campaign:{campaign_id}"
        queue = event_bus.subscribe(topic)
        self._active_queues.add(queue)

        async def generate():
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield f"data: {message}\n\n"
                    except asyncio.TimeoutError:
                        yield ": heartbeat\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                event_bus.unsubscribe(topic, queue)
                self._active_queues.discard(queue)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    async def subscribe_to_job(self, job_id: int) -> StreamingResponse:
        """Create SSE stream for job events."""
        topic = f"job:{job_id}"
        queue = event_bus.subscribe(topic)
        self._active_queues.add(queue)

        async def generate():
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield f"data: {message}\n\n"
                    except asyncio.TimeoutError:
                        yield ": heartbeat\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                event_bus.unsubscribe(topic, queue)
                self._active_queues.discard(queue)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    async def close(self):
        """Clean up all active connections."""
        for queue in self._active_queues:
            try:
                queue.put_nowait(None)
            except:
                pass
        self._active_queues.clear()


sse_transport = SSETransport()
```

---

## Router

```python
# events_router.py
from fastapi import APIRouter
from .transports.sse import sse_transport

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/campaigns/{campaign_id}/stream")
async def campaign_event_stream(campaign_id: str):
    """SSE stream for all events in a campaign."""
    return await sse_transport.subscribe_to_campaign(campaign_id)

@router.get("/jobs/{job_id}/stream")
async def job_event_stream(job_id: int):
    """SSE stream for job status updates."""
    return await sse_transport.subscribe_to_job(job_id)
```

---

## Public API Exports

```python
# events/__init__.py
"""Events package - typed pub-sub for real-time updates.

Usage for PUBLISHERS (workers, services):
    from app.events import event_bus, JobStatusEvent

    await event_bus.publish(JobStatusEvent(
        job_id=42,
        campaign_id="abc",
        status="MATCHING"
    ))

Usage for TRANSPORTS (SSE router):
    from app.events import sse_transport

    stream = await sse_transport.subscribe_to_campaign(campaign_id)
"""

from .event_types import (
    EventType,
    BaseEvent,
    JobStatusEvent,
    JobProgressEvent,
    MetricsUpdatedEvent,
)
from .event_bus import event_bus
from .transports.sse import sse_transport

__all__ = [
    "event_bus",
    "EventType",
    "BaseEvent",
    "JobStatusEvent",
    "JobProgressEvent",
    "MetricsUpdatedEvent",
    "sse_transport",
]
```

---

## Frontend Integration

### Event Store

```typescript
// stores/events.ts
import { writable } from 'svelte/store';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface EventStore {
    connect: (campaignId: string) => void;
    disconnect: () => void;
    status: { subscribe: (fn: (v: ConnectionStatus) => void) => void };
    lastEvent: { subscribe: (fn: (v: any) => void) => void };
}

function createEventStore(): EventStore {
    let eventSource: EventSource | null = null;

    const status = writable<ConnectionStatus>('disconnected');
    const lastEvent = writable<any>(null);

    return {
        status: { subscribe: status.subscribe },
        lastEvent: { subscribe: lastEvent.subscribe },

        connect(campaignId: string) {
            if (eventSource) eventSource.close();

            status.set('connecting');
            const baseUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8080';
            eventSource = new EventSource(`${baseUrl}/api/events/campaigns/${campaignId}/stream`);

            eventSource.onopen = () => status.set('connected');
            eventSource.onerror = () => status.set('error');

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                lastEvent.set(data);

                switch (data.event_type) {
                    case 'job:status_changed':
                        jobs.handleStatusEvent(data);
                        break;
                    case 'job:progress':
                        jobs.handleProgressEvent(data);
                        break;
                    case 'metrics:updated':
                        campaigns.handleMetricsEvent(data);
                        break;
                }
            };
        },

        disconnect() {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            status.set('disconnected');
        }
    };
}

export const events = createEventStore();
```

### Campaign Layout

```svelte
<!-- routes/workspace/[id]/+layout.svelte -->
<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { page } from '$app/stores';
    import { events } from '$lib/stores/events';

    let { children } = $props();
    const campaignId = $derived($page.params.id);

    onMount(() => {
        if (campaignId && campaignId !== 'demo') {
            events.connect(campaignId);
        }
    });

    onDestroy(() => events.disconnect());

    $effect(() => {
        if (campaignId && campaignId !== 'demo') {
            events.connect(campaignId);
        }
    });
</script>

{@render children()}
```

### Remove Polling

```svelte
<!-- routes/workspace/[id]/+page.svelte -->
<script lang="ts">
    // REMOVED: pollInterval and setInterval

    onMount(() => {
        fetchMetrics();
        fetchSetupStatus();
    });
</script>
```

---

## Migration Path

| Phase | Changes | Risk |
|-------|---------|------|
| **1. Add Event Bus** | Create `events/` package, add router | None (additive) |
| **2. Wire Publishers** | Worker publishes events | Low (parallel to existing SSE) |
| **3. Frontend Adopts** | Campaign layout connects, remove polling | Medium (behavior change) |
| **4. Deprecate Old SSE** | Remove `SSEConnectionManager` | Low (after stability) |

### Coexistence During Migration

```
Phase 2-3:
  Worker ──→ SSEConnectionManager → /jobs/{id}/stream (job detail page)
         └──→ event_bus → /events/campaigns/{id}/stream (dashboard, jobs list)
```

---

## Testing

### Unit Tests

- Event bus topic derivation from event attributes
- Auto-source detection from callsite
- Queue full graceful drop
- Event serialization

### Integration Tests

- Campaign SSE stream receives campaign events
- Job SSE stream receives job events
- Multiple subscribers receive same event

### E2E Tests

- Dashboard updates without polling when job status changes
- Jobs list updates in real-time
- Connection status indicator on error

---

## Files Changed

| File | Change |
|------|--------|
| `backend/app/events/__init__.py` | NEW |
| `backend/app/events/event_types.py` | NEW |
| `backend/app/events/event_bus.py` | NEW |
| `backend/app/events/transports/__init__.py` | NEW |
| `backend/app/events/transports/base.py` | NEW |
| `backend/app/events/transports/sse.py` | NEW |
| `backend/app/routers/events_router.py` | NEW |
| `backend/app/main.py` | Register router |
| `backend/app/jobs/worker.py` | Publish events |
| `frontend-svelt/src/lib/stores/events.ts` | NEW |
| `frontend-svelt/src/lib/stores/jobs.ts` | Add handlers |
| `frontend-svelt/src/routes/workspace/[id]/+layout.svelte` | Connect to stream |
| `frontend-svelt/src/routes/workspace/[id]/+page.svelte` | Remove polling |
| `frontend-svelt/src/routes/workspace/[id]/jobs/+page.svelte` | Remove polling |

---

## Future: WebSocket Addition

When WebSocket is needed:

1. Create `transports/websocket.py` implementing `EventTransport`
2. Add router endpoints for WebSocket connections
3. Frontend adds WebSocket connection with fallback to SSE
4. No changes to event bus, publishers, or event types

Estimated effort: ~2-3 hours
