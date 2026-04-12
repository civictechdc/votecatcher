# ADR-0002: Use FastAPI BackgroundTasks for Job Orchestration

## Status

Accepted

## Context

Votecatcher needs to orchestrate asynchronous OCR and matching jobs. The system must:

- Submit batch requests to LLM providers
- Poll for completion at intervals
- Update job status in real-time
- Handle partial failures gracefully

### Options Considered

1. **Celery/RQ** - Dedicated task queue with workers
2. **FastAPI BackgroundTasks** - Built-in async task execution
3. **Custom threading** - Manual thread management

## Decision

We will use **FastAPI BackgroundTasks** for job orchestration.

### Rationale

- LLM batch APIs are inherently asynchronous (submit → poll → retrieve)
- No need for persistent job queue - jobs are tracked in database
- BackgroundTasks sufficient for polling intervals (30-60 seconds)
- Simpler deployment (no additional workers/Redis)
- Fits MVP scale (1-5 concurrent users)

## Consequences

### Positive

- No additional infrastructure (Celery broker, Redis)
- Simpler deployment (single process)
- Built into FastAPI, well-documented
- Sufficient for MVP scale

### Negative

- Tasks lost if server restarts during processing (mitigated by persisting job state in DB)
- Not suitable for high-throughput scenarios (not a concern for MVP)

### Neutral

- Job state must be persisted in database for recovery
- Polling intervals must be reasonable (30-60s)

## Alternatives Considered

### Celery with Redis

**Pros:**
- Persistent task queue
- Better for high throughput
- Distributed workers

**Cons:**
- Additional infrastructure (Redis, Celery broker)
- More complex deployment
- Overkill for MVP scale

**Why not chosen:** Adds complexity without benefit at current scale

## Related Decisions

- [ADR-0003: Use SSE for Real-time Updates](./0003-use-sse-for-realtime-updates.md)

## References

- [FastAPI BackgroundTasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [OpenAI Batch API](https://platform.openai.com/docs/api-reference/batch)
