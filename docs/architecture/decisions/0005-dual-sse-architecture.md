# ADR-0005: Dual SSE Architecture

## Status

Accepted

## Context

Votecatcher needs real-time updates for job status and metrics. After implementing the event bus (Phase 10), two SSE systems exist in the codebase:

1. **Event Bus SSE** (`/events/campaigns/{id}/stream`) - Campaign-scoped event stream
2. **Per-Job SSE** (`/api/jobs/{id}/status`) - Single job monitoring

The question arose: Should we deprecate the per-job SSE and migrate everything to the event bus?

## Decision

**Keep both SSE systems** - they serve different purposes and are both actively used.

### Architecture

| System | Endpoint | Scope | Frontend Usage | Purpose |
|--------|----------|-------|----------------|---------|
| Event Bus | `/events/campaigns/{id}/stream` | Campaign-wide | `events.ts` → Campaign layout | Dashboard metrics, jobs list, general updates |
| Per-Job SSE | `/api/jobs/{id}/status` | Single job | `jobs.connectToJob()` → Job detail page | Focused job monitoring with detailed status |

### Frontend Integration Points

```
Campaign Layout (+layout.svelte)
├── events.connect(campaignId)     → Event Bus SSE
│   └── Dispatches CustomEvents for:
│       ├── votecatcher:job:status
│       ├── votecatcher:job:progress
│       └── votecatcher:metrics:updated
│
└── Job Detail Page (jobs/[job_id]/+page.svelte)
    └── jobs.connectToJob(jobId)   → Per-Job SSE
        └── Direct status/progress updates
```

## Consequences

### Positive

- Campaign layout receives broad updates for dashboard/jobs list
- Job detail page has focused stream for detailed monitoring
- Clean separation: campaign-scoped vs job-scoped concerns
- Event bus provides typed events with auto-source detection

### Negative

- Two SSE systems to understand and maintain
- Slight code duplication in frontend store logic

### Risks

- Future developers may be confused by dual architecture
- Mitigation: This ADR documents the decision and rationale

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Migrate all to event bus | Single source of truth | Lose focused job monitoring; more complex filtering | Job detail page needs dedicated stream |
| Deprecate per-job SSE | Simpler architecture | Requires job detail page refactor; loses real-time detail | No clear benefit |
| Keep both | Clear separation of concerns | Two systems to maintain | **Selected** - best UX and maintainability |

## References

- Event store: `frontend-svelt/src/lib/stores/events.ts`
- Jobs store: `frontend-svelt/src/lib/stores/jobs.ts`

---

**Date:** 2026-03-25
**Decision Makers:** Development Team
