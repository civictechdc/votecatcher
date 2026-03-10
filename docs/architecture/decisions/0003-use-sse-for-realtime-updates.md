# ADR-0003: Use SSE for Real-time Updates

## Status

Accepted

## Context

Users need to see job progress in real-time as OCR and matching phases execute. Options for real-time updates:

1. **Polling** - Client periodically requests status
2. **Server-Sent Events (SSE)** - Server pushes updates to client
3. **WebSockets** - Bidirectional real-time communication

## Decision

We will use **Server-Sent Events (SSE)** for real-time job status updates.

### Rationale

- SSE is simpler than WebSockets for unidirectional updates
- Better user experience than polling (instant updates)
- Built-in reconnection support in browsers
- Per-job endpoint provides natural scope
- Sufficient for our use case (server → client updates only)

## Consequences

### Positive

- Instant updates improve UX
- Simpler than WebSockets (no protocol overhead)
- Native browser support with EventSource API
- Works over standard HTTP (friendly with proxies)

### Negative

- Unidirectional only (client cannot send messages over same connection)
- Some older proxy/buffering issues (rare with modern infrastructure)
- Requires connection management per job

### Neutral

- Connection is per-job, not global
- Client must reconnect if connection drops

## Implementation

### Backend

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/api/jobs/{job_id}/status")
async def job_status_stream(job_id: int):
    async def event_generator():
        while True:
            job = await get_job_status(job_id)
            yield f"event: status_update\ndata: {job.json()}\n\n"
            if job.status in ["MATCHING_COMPLETED", "ERROR"]:
                break
            await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### Frontend

```typescript
const eventSource = new EventSource(`/api/jobs/${jobId}/status`);

eventSource.addEventListener('status_update', (e) => {
    const data = JSON.parse(e.data);
    updateJobStatus(data);
});

eventSource.addEventListener('job_complete', (e) => {
    const data = JSON.parse(e.data);
    showCompletionNotification(data);
    eventSource.close();
});

eventSource.onerror = () => {
    // Reconnection logic
    setTimeout(() => reconnect(jobId), 5000);
};
```

## Alternatives Considered

### Polling

**Pros:**
- Simplest implementation
- No connection management

**Cons:**
- Delayed updates (polling interval)
- Wasted requests when no updates
- Poor UX for long-running jobs

**Why not chosen:** Poor user experience for real-time feedback

### WebSockets

**Pros:**
- Bidirectional communication
- Lower latency for high-frequency updates

**Cons:**
- More complex implementation
- Protocol upgrade overhead
- Overkill for unidirectional updates
- Requires connection management library

**Why not chosen:** Overkill for our use case (server → client only)

## Related Decisions

- [ADR-0002: Use FastAPI BackgroundTasks](./0002-use-fastapi-background-tasks.md)

## References

- [MDN: Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
