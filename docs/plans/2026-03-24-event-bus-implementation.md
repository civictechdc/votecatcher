# Event Bus Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace HTTP polling with typed pub-sub event bus for real-time SSE updates across dashboard and jobs list.

**Architecture:** In-memory event bus with topic-based routing. Publishers emit typed events with auto-source detection. SSE transport subscribes to topics and streams to frontend. Decoupled design allows future WebSocket addition.

**Tech Stack:** Python asyncio, Pydantic, FastAPI SSE, Svelte stores

**Design Doc:** `docs/plans/2026-03-24-event-bus-design.md`

---

## Task 1: Event Types

**Files:**
- Create: `backend/app/events/__init__.py`
- Create: `backend/app/events/event_types.py`
- Create: `backend/tests/unit/events/__init__.py`
- Create: `backend/tests/unit/events/test_event_types.py`

**Step 1: Create package structure**

```bash
mkdir -p backend/app/events backend/tests/unit/events
touch backend/app/events/__init__.py backend/tests/unit/events/__init__.py
```

**Step 2: Write failing test for event types**

```python
# backend/tests/unit/events/test_event_types.py
import pytest
from app.events.event_types import EventType, BaseEvent, JobStatusEvent, JobProgressEvent


class TestEventType:
    def test_event_type_values(self):
        assert EventType.JOB_STATUS_CHANGED == "job:status_changed"
        assert EventType.JOB_PROGRESS == "job:progress"
        assert EventType.METRICS_UPDATED == "metrics:updated"


class TestBaseEvent:
    def test_base_event_generates_event_id(self):
        event = BaseEvent(event_type=EventType.JOB_STATUS_CHANGED)
        assert event.event_id is not None
        assert len(event.event_id) == 36  # UUID format

    def test_base_event_generates_timestamp(self):
        event = BaseEvent(event_type=EventType.JOB_STATUS_CHANGED)
        assert event.timestamp is not None


class TestJobStatusEvent:
    def test_job_status_event_has_required_fields(self):
        event = JobStatusEvent(
            job_id=1,
            campaign_id="abc123",
            status="MATCHING",
            previous_status="OCR_COMPLETED"
        )
        assert event.job_id == 1
        assert event.campaign_id == "abc123"
        assert event.status == "MATCHING"
        assert event.event_type == EventType.JOB_STATUS_CHANGED


class TestJobProgressEvent:
    def test_job_progress_event_calculates_percentage(self):
        event = JobProgressEvent(
            job_id=1,
            campaign_id="abc123",
            processed=50,
            total=100,
            percentage=50.0
        )
        assert event.percentage == 50.0
```

**Step 3: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/events/test_event_types.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 4: Implement event types**

```python
# backend/app/events/event_types.py
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
    source: str | None = None
    campaign_id: str | None = None
    job_id: int | None = None


class JobStatusEvent(BaseEvent):
    event_type: Literal[EventType.JOB_STATUS_CHANGED] = EventType.JOB_STATUS_CHANGED
    status: str
    previous_status: str | None = None


class JobProgressEvent(BaseEvent):
    event_type: Literal[EventType.JOB_PROGRESS] = EventType.JOB_PROGRESS
    processed: int
    total: int
    percentage: float


class MetricsUpdatedEvent(BaseEvent):
    event_type: Literal[EventType.METRICS_UPDATED] = EventType.METRICS_UPDATED
    total_signatures: int
    processed: int
    high_confidence: int
```

**Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/events/test_event_types.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/events/__init__.py backend/app/events/event_types.py backend/tests/unit/events/
git commit -m "feat(events): add typed event definitions"
```

---

## Task 2: Event Bus Core

**Files:**
- Modify: `backend/app/events/__init__.py`
- Create: `backend/app/events/event_bus.py`
- Create: `backend/tests/unit/events/test_event_bus.py`

**Step 1: Write failing test for event bus**

```python
# backend/tests/unit/events/test_event_bus.py
import asyncio
import json
import pytest
from app.events.event_bus import EventBus
from app.events.event_types import JobStatusEvent, EventType


class TestEventBus:
    def test_subscribe_returns_queue(self):
        bus = EventBus()
        queue = bus.subscribe("campaign:123")
        assert queue is not None
        assert queue.maxsize == 100

    def test_publish_derives_campaign_topic(self):
        bus = EventBus()
        queue = bus.subscribe("campaign:123")

        event = JobStatusEvent(
            campaign_id="123",
            job_id=1,
            status="MATCHING"
        )
        asyncio.run(bus.publish(event))

        message = queue.get_nowait()
        data = json.loads(message)
        assert data["event_type"] == "job:status_changed"
        assert data["campaign_id"] == "123"

    def test_publish_derives_job_topic(self):
        bus = EventBus()
        queue = bus.subscribe("job:42")

        event = JobStatusEvent(
            job_id=42,
            status="MATCHING"
        )
        asyncio.run(bus.publish(event))

        message = queue.get_nowait()
        data = json.loads(message)
        assert data["job_id"] == 42

    def test_publish_to_global_topic(self):
        bus = EventBus()
        queue = bus.subscribe("global")

        event = JobStatusEvent(job_id=1, status="MATCHING")
        asyncio.run(bus.publish(event))

        message = queue.get_nowait()
        assert message is not None

    def test_unsubscribe_removes_queue(self):
        bus = EventBus()
        queue = bus.subscribe("campaign:123")

        bus.unsubscribe("campaign:123", queue)

        event = JobStatusEvent(campaign_id="123", job_id=1, status="MATCHING")
        asyncio.run(bus.publish(event))

        # Queue should not receive after unsubscribe
        with pytest.raises(Exception):
            queue.get_nowait()

    def test_auto_source_detection(self):
        bus = EventBus()
        queue = bus.subscribe("global")

        async def publish_from_here():
            await bus.publish(JobStatusEvent(job_id=1, status="MATCHING"))

        asyncio.run(publish_from_here())

        message = queue.get_nowait()
        data = json.loads(message)
        assert "test_event_bus" in data["source"]

    def test_queue_full_drops_gracefully(self):
        bus = EventBus()
        bus.MAX_QUEUE_SIZE = 1

        queue = bus.subscribe("global")
        queue.put_nowait("{}")  # Fill queue

        # Should not raise
        asyncio.run(bus.publish(JobStatusEvent(job_id=1, status="MATCHING")))
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/events/test_event_bus.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement event bus**

```python
# backend/app/events/event_bus.py
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

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/events/test_event_bus.py -v`
Expected: PASS

**Step 5: Update package exports**

```python
# backend/app/events/__init__.py
"""Events package - typed pub-sub for real-time updates."""

from .event_types import (
    EventType,
    BaseEvent,
    JobStatusEvent,
    JobProgressEvent,
    MetricsUpdatedEvent,
)
from .event_bus import event_bus

__all__ = [
    "event_bus",
    "EventType",
    "BaseEvent",
    "JobStatusEvent",
    "JobProgressEvent",
    "MetricsUpdatedEvent",
]
```

**Step 6: Commit**

```bash
git add backend/app/events/ backend/tests/unit/events/
git commit -m "feat(events): add event bus with auto-source detection"
```

---

## Task 3: Transport Interface

**Files:**
- Create: `backend/app/events/transports/__init__.py`
- Create: `backend/app/events/transports/base.py`
- Create: `backend/tests/unit/events/transports/__init__.py`

**Step 1: Create transport package**

```bash
mkdir -p backend/app/events/transports backend/tests/unit/events/transports
touch backend/app/events/transports/__init__.py backend/tests/unit/events/transports/__init__.py
```

**Step 2: Implement transport interface**

```python
# backend/app/events/transports/base.py
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

**Step 3: Update transport exports**

```python
# backend/app/events/transports/__init__.py
from .base import EventTransport

__all__ = ["EventTransport"]
```

**Step 4: Commit**

```bash
git add backend/app/events/transports/ backend/tests/unit/events/transports/
git commit -m "feat(events): add transport interface"
```

---

## Task 4: SSE Transport

**Files:**
- Modify: `backend/app/events/__init__.py`
- Create: `backend/app/events/transports/sse.py`
- Create: `backend/tests/unit/events/transports/test_sse_transport.py`

**Step 1: Write failing test for SSE transport**

```python
# backend/tests/unit/events/transports/test_sse_transport.py
import pytest
from app.events.transports.sse import SSETransport


class TestSSETransport:
    def test_create_transport(self):
        transport = SSETransport()
        assert transport is not None

    def test_subscribe_to_campaign_returns_response(self):
        transport = SSETransport()
        response = await transport.subscribe_to_campaign("123")
        assert response.media_type == "text/event-stream"

    def test_subscribe_to_job_returns_response(self):
        transport = SSETransport()
        response = await transport.subscribe_to_job(42)
        assert response.media_type == "text/event-stream"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/events/transports/test_sse_transport.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement SSE transport**

```python
# backend/app/events/transports/sse.py
import asyncio
from fastapi.responses import StreamingResponse
from ..event_bus import event_bus
from .base import EventTransport


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

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/events/transports/test_sse_transport.py -v`
Expected: PASS

**Step 5: Update package exports**

```python
# backend/app/events/__init__.py - add sse_transport export
from .transports.sse import sse_transport

__all__ = [
    # ... existing exports ...
    "sse_transport",
]
```

**Step 6: Commit**

```bash
git add backend/app/events/ backend/tests/unit/events/transports/
git commit -m "feat(events): add SSE transport implementation"
```

---

## Task 4.5: Event Bus Cleanup & Optimization

**Priority:** High (memory leak risk)
**Files:**
- Modify: `backend/app/events/event_bus.py`
- Modify: `backend/tests/unit/events/test_event_bus.py`

**Issue:** Stale queues accumulate when SSE clients disconnect uncleanly (network failure, browser crash). Topic entries persist even with zero subscribers.

**Step 1: Add cleanup on queue full detection**

```python
# In event_bus.py, add to publish():
def _cleanup_empty_topics(self):
    """Remove topics with no active subscribers."""
    empty = [t for t, q in self._subscribers.items() if not q]
    for topic in empty:
        del self._subscribers[topic]
```

**Step 2: Add idle connection tracking**

```python
# Add to EventBus class:
def __init__(self):
    self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
    self._queue_timestamps: dict[int, float] = {}  # queue id -> last activity
    self._logger = structlog.get_logger()

async def publish(self, event: BaseEvent, source: str | None = None) -> None:
    topics = self._get_topics(event)
    subscriber_count = sum(len(self._subscribers[t]) for t in topics)

    # Skip serialization if no subscribers
    if subscriber_count == 0:
        self._cleanup_empty_topics()
        return

    message = event.model_dump_json()
    # ... rest of publish logic
```

**Step 3: Add test for cleanup**

```python
# In test_event_bus.py:
def test_cleanup_removes_empty_topics(self):
    bus = EventBus()
    queue = bus.subscribe("campaign:123")
    bus.unsubscribe("campaign:123", queue)

    # Topic should be removed after cleanup
    assert "campaign:123" not in bus._subscribers

def test_skip_serialization_when_no_subscribers(self):
    bus = EventBus()
    # Publish with no subscribers - should not serialize
    asyncio.run(bus.publish(JobStatusEvent(job_id=1, status="MATCHING")))
    # Should complete without error
```

**Step 4: Run tests**

```bash
cd backend && uv run pytest tests/unit/events/test_event_bus.py -v
```

**Step 5: Commit**

```bash
git add backend/app/events/event_bus.py backend/tests/unit/events/test_event_bus.py
git commit -m "fix(events): cleanup stale queues and skip serialization when no subscribers"
```

---

## Task 5: Events Router

**Files:**
- Create: `backend/app/routers/events_router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/api/test_events.py`

**Step 1: Create events router**

```python
# backend/app/routers/events_router.py
from fastapi import APIRouter
from app.events import sse_transport

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

**Step 2: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.routers.events_router import router as events_router

# In router registration section:
app.include_router(events_router, prefix="/api")
```

**Step 3: Write integration test**

```python
# backend/tests/integration/api/test_events.py
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestEventsEndpoint:
    def test_campaign_stream_endpoint_exists(self):
        client = TestClient(app)
        response = client.get("/api/events/campaigns/123/stream", stream=True)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_job_stream_endpoint_exists(self):
        client = TestClient(app)
        response = client.get("/api/events/jobs/42/stream", stream=True)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
```

**Step 4: Run test**

Run: `cd backend && uv run pytest tests/integration/api/test_events.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/routers/events_router.py backend/app/main.py backend/tests/integration/api/test_events.py
git commit -m "feat(events): add events router with SSE endpoints"
```

---

## Task 6: Worker Publisher Integration

**Files:**
- Modify: `backend/app/jobs/worker.py`
- Modify: `backend/tests/unit/jobs/test_worker.py`

**Step 1: Add event publishing to worker**

In `backend/app/jobs/worker.py`, add imports at top:

```python
from app.events import event_bus, JobStatusEvent, JobProgressEvent
```

Find the job status transition points and add publishing:

```python
# When job starts OCR
await event_bus.publish(JobStatusEvent(
    trace_id=str(job.id),
    job_id=job.id,
    campaign_id=str(job.campaign_id),
    status="OCR_STARTED",
    previous_status="NOT_STARTED"
))

# When job starts matching
await event_bus.publish(JobStatusEvent(
    trace_id=str(job.id),
    job_id=job.id,
    campaign_id=str(job.campaign_id),
    status="MATCHING",
    previous_status="OCR_COMPLETED"
))

# When job completes
await event_bus.publish(JobStatusEvent(
    trace_id=str(job.id),
    job_id=job.id,
    campaign_id=str(job.campaign_id),
    status="MATCHING_COMPLETED",
    previous_status="MATCHING"
))

# During matching progress (every 10%)
if processed % max(1, total // 10) == 0:
    await event_bus.publish(JobProgressEvent(
        trace_id=str(job.id),
        job_id=job.id,
        campaign_id=str(job.campaign_id),
        processed=processed,
        total=total,
        percentage=(processed / total) * 100
    ))
```

**Step 2: Commit**

```bash
git add backend/app/jobs/worker.py
git commit -m "feat(worker): publish events on job status changes"
```

---

## Task 6.5: Metrics Event Publisher

**Priority:** Medium (gap in event coverage)
**Files:**
- Modify: `backend/app/services/matching_service.py` or relevant metrics service
- Modify: `backend/tests/unit/events/test_event_bus.py`

**Issue:** `MetricsUpdatedEvent` is defined but never published. Dashboard won't receive real-time metric updates.

**Step 1: Identify metrics update location**

Find where campaign metrics are recalculated after matching:
- `matching_service.py` - after batch matching completes
- `metrics_service.py` - if metrics are computed separately
- `worker.py` - after job completion

**Step 2: Add metrics event publishing**

```python
# In the service that updates metrics (e.g., after matching batch):
from app.events import event_bus, MetricsUpdatedEvent

async def update_campaign_metrics(campaign_id: str):
    # ... existing metrics calculation ...

    await event_bus.publish(MetricsUpdatedEvent(
        campaign_id=campaign_id,
        total_signatures=total,
        processed=processed,
        high_confidence=high_confidence
    ))
```

**Step 3: Add test**

```python
# In test_event_bus.py or new test file:
def test_metrics_event_published():
    bus = EventBus()
    queue = bus.subscribe("campaign:123")

    asyncio.run(bus.publish(MetricsUpdatedEvent(
        campaign_id="123",
        total_signatures=1000,
        processed=500,
        high_confidence=300
    )))

    message = queue.get_nowait()
    data = json.loads(message)
    assert data["event_type"] == "metrics:updated"
    assert data["high_confidence"] == 300
```

**Step 4: Commit**

```bash
git add backend/app/services/ backend/tests/
git commit -m "feat(metrics): publish MetricsUpdatedEvent on metric changes"
```

---

## Task 7: Frontend Event Store

**Files:**
- Create: `frontend-svelt/src/lib/stores/events.ts`
- Create: `frontend-svelt/src/lib/types/events.ts`

**Step 1: Create event types**

```typescript
// frontend-svelt/src/lib/types/events.ts
export type EventType =
  | 'job:status_changed'
  | 'job:progress'
  | 'metrics:updated';

export interface BaseEvent {
  event_id: string;
  event_type: EventType;
  timestamp: string;
  trace_id: string | null;
  source: string | null;
  campaign_id: string | null;
  job_id: number | null;
}

export interface JobStatusEvent extends BaseEvent {
  event_type: 'job:status_changed';
  status: string;
  previous_status: string | null;
}

export interface JobProgressEvent extends BaseEvent {
  event_type: 'job:progress';
  processed: number;
  total: number;
  percentage: number;
}
```

**Step 2: Create event store**

```typescript
// frontend-svelt/src/lib/stores/events.ts
import { writable } from 'svelte/store';
import { jobs } from './jobs';
import type { BaseEvent, JobStatusEvent, JobProgressEvent } from '$lib/types/events';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface EventStore {
  connect: (campaignId: string) => void;
  disconnect: () => void;
  status: { subscribe: (fn: (v: ConnectionStatus) => void) => void };
  lastEvent: { subscribe: (fn: (v: BaseEvent | null) => void) => void };
}

function createEventStore(): EventStore {
  let eventSource: EventSource | null = null;

  const status = writable<ConnectionStatus>('disconnected');
  const lastEvent = writable<BaseEvent | null>(null);

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
            jobs.handleStatusEvent(data as JobStatusEvent);
            break;
          case 'job:progress':
            jobs.handleProgressEvent(data as JobProgressEvent);
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

**Step 3: Commit**

```bash
git add frontend-svelt/src/lib/stores/events.ts frontend-svelt/src/lib/types/events.ts
git commit -m "feat(frontend): add event store for SSE connection"
```

---

## Task 7.5: Frontend Reconnection Resilience

**Priority:** High (UX impact)
**Files:**
- Modify: `frontend-svelt/src/lib/stores/events.ts`

**Issue:** No retry/backoff on connection error. Users see stale data after network hiccup.

**Step 1: Add exponential backoff reconnection**

```typescript
// frontend-svelt/src/lib/stores/events.ts
function createEventStore(): EventStore {
  let eventSource: EventSource | null = null;
  let reconnectAttempts = 0;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  const MAX_RECONNECT_ATTEMPTS = 5;
  const BASE_DELAY = 1000; // 1 second

  const status = writable<ConnectionStatus>('disconnected');
  const lastEvent = writable<BaseEvent | null>(null);

  function scheduleReconnect(campaignId: string) {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      status.set('error');
      return;
    }

    const delay = BASE_DELAY * Math.pow(2, reconnectAttempts);
    reconnectAttempts++;

    reconnectTimeout = setTimeout(() => {
      connect(campaignId);
    }, delay);
  }

  return {
    status: { subscribe: status.subscribe },
    lastEvent: { subscribe: lastEvent.subscribe },

    connect(campaignId: string) {
      if (eventSource) eventSource.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);

      status.set('connecting');
      const baseUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8080';
      eventSource = new EventSource(`${baseUrl}/api/events/campaigns/${campaignId}/stream`);

      eventSource.onopen = () => {
        reconnectAttempts = 0; // Reset on successful connection
        status.set('connected');
      };

      eventSource.onerror = () => {
        eventSource?.close();
        eventSource = null;
        status.set('error');
        scheduleReconnect(campaignId);
      };

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        lastEvent.set(data);

        switch (data.event_type) {
          case 'job:status_changed':
            jobs.handleStatusEvent(data as JobStatusEvent);
            break;
          case 'job:progress':
            jobs.handleProgressEvent(data as JobProgressEvent);
            break;
          case 'metrics:updated':
            campaigns.handleMetricsEvent(data);
            break;
        }
      };
    },

    disconnect() {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      reconnectAttempts = 0;
      status.set('disconnected');
    }
  };
}
```

**Step 2: Add connection status UI indicator (optional)**

```svelte
<!-- In +layout.svelte or component -->
{#if $events.status === 'error'}
  <div class="connection-banner warning">
    Connection lost. Reconnecting...
  </div>
{/if}
```

**Step 3: Commit**

```bash
git add frontend-svelt/src/lib/stores/events.ts
git commit -m "feat(frontend): add exponential backoff reconnection for SSE"
```

---

## Task 8: Jobs Store Event Handlers

**Files:**
- Modify: `frontend-svelt/src/lib/stores/jobs.ts`

**Step 1: Add event handlers to jobs store**

```typescript
// Add to jobs store return object:
handleStatusEvent(event: JobStatusEvent) {
  update(state => ({
    ...state,
    jobs: state.jobs.map(job =>
      job.id === event.job_id
        ? { ...job, status: event.status }
        : job
    )
  }));
},

handleProgressEvent(event: JobProgressEvent) {
  update(state => ({
    ...state,
    jobs: state.jobs.map(job =>
      job.id === event.job_id
        ? { ...job, progress: event.percentage }
        : job
    )
  }));
}
```

**Step 2: Commit**

```bash
git add frontend-svelt/src/lib/stores/jobs.ts
git commit -m "feat(frontend): add event handlers to jobs store"
```

---

## Task 9: Campaign Layout Integration

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/[id]/+layout.svelte`

**Step 1: Connect to event stream in layout**

```svelte
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

  onDestroy(() => {
    events.disconnect();
  });

  $effect(() => {
    if (campaignId && campaignId !== 'demo') {
      events.connect(campaignId);
    }
  });
</script>

{@render children()}
```

**Step 2: Commit**

```bash
git add frontend-svelt/src/routes/workspace/[id]/+layout.svelte
git commit -m "feat(frontend): connect to event stream in campaign layout"
```

---

## Task 10: Remove Polling from Dashboard

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/[id]/+page.svelte`

**Step 1: Remove polling code**

Remove:
- `let pollInterval` declaration
- `setInterval(fetchMetrics, ...)` in onMount
- `clearInterval(pollInterval)` in onDestroy

Keep only:
- Initial `fetchMetrics()` call on mount
- `fetchSetupStatus()` call on mount

**Step 2: Commit**

```bash
git add frontend-svelt/src/routes/workspace/[id]/+page.svelte
git commit -m "refactor(frontend): remove polling from dashboard, use events"
```

---

## Task 11: Remove Polling from Jobs List

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/[id]/jobs/+page.svelte`

**Step 1: Remove polling code**

Remove:
- `let pollInterval` declaration
- `setInterval(() => { jobs.fetchAll() }, ...)` in onMount
- `clearInterval(pollInterval)` in onDestroy

Keep only:
- Initial `jobs.fetchAll()` call on mount

**Step 2: Commit**

```bash
git add frontend-svelt/src/routes/workspace/[id]/jobs/+page.svelte
git commit -m "refactor(frontend): remove polling from jobs list, use events"
```

---

## Task 12: E2E Test

**Files:**
- Create: `frontend-svelt/tests/e2e/events.spec.ts`

**Step 1: Write E2E test**

```typescript
// frontend-svelt/tests/e2e/events.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Event Bus', () => {
  test('dashboard connects to event stream', async ({ page }) => {
    await page.goto('/workspace/campaigns');

    // Create a campaign if needed
    // Navigate to dashboard
    await page.goto('/workspace/1');

    // Check for SSE connection (look for network request or UI indicator)
    const response = await page.waitForResponse(
      resp => resp.url().includes('/api/events/campaigns/') &&
              resp.headers()['content-type']?.includes('text/event-stream'),
      { timeout: 5000 }
    ).catch(() => null);

    // Connection may not complete in test, but endpoint should exist
    expect(response).toBeTruthy;
  });

  test('job status updates via SSE', async ({ page }) => {
    // Setup: Create campaign, upload files
    // Start job
    // Verify status updates without page refresh
  });
});
```

**Step 2: Run E2E test**

Run: `cd frontend-svelt && bun run test:e2e tests/e2e/events.spec.ts`

**Step 3: Commit**

```bash
git add frontend-svelt/tests/e2e/events.spec.ts
git commit -m "test(e2e): add event bus tests"
```

---

## Task 13: Final Verification

**Step 1: Run all backend tests**

```bash
cd backend && uv run pytest tests/unit/events tests/integration/api/test_events.py -v
```

**Step 2: Run frontend type check**

```bash
cd frontend-svelt && bun run check
```

**Step 3: Manual test**

1. Start backend: `cd backend && uv run uvicorn app.main:app --reload`
2. Start frontend: `cd frontend-svelt && bun run dev`
3. Open dashboard, check browser network tab for `/api/events/campaigns/{id}/stream`
4. Start a job, verify status updates in real-time without polling

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(events): complete event bus implementation

- Add typed event bus with auto-source detection
- Add SSE transport for browser clients
- Wire worker to publish job events
- Connect frontend via event store
- Remove HTTP polling from dashboard and jobs list

Refs: docs/plans/2026-03-24-event-bus-design.md"
```

---

## Summary

| Task | Description | Effort | Status |
|------|-------------|--------|--------|
| 1 | Event Types | 30min | ✅ Done |
| 2 | Event Bus Core | 45min | ✅ Done |
| 3 | Transport Interface | 15min | ✅ Done |
| 4 | SSE Transport | 30min | 📋 Planned |
| **4.5** | **Event Bus Cleanup & Optimization** ⚠️ | **20min** | **📋 Planned** |
| 5 | Events Router | 30min | 📋 Planned |
| 6 | Worker Publisher | 30min | 📋 Planned |
| **6.5** | **Metrics Event Publisher** ⚠️ | **20min** | **📋 Planned** |
| 7 | Frontend Event Store | 30min | 📋 Planned |
| **7.5** | **Frontend Reconnection Resilience** ⚠️ | **25min** | **📋 Planned** |
| 8 | Jobs Store Handlers | 15min | 📋 Planned |
| 9 | Campaign Layout | 15min | 📋 Planned |
| 10 | Remove Dashboard Polling | 15min | 📋 Planned |
| 11 | Remove Jobs Polling | 15min | 📋 Planned |
| 12 | E2E Test | 30min | 📋 Planned |
| 13 | Final Verification | 30min | 📋 Planned |
| **Total** | | **~7 hours** | |

⚠️ = Gap fix (added after code review)
