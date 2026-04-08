# Votecatcher Technical Specification

**Status:** Post-MVP Complete
**Last Updated:** 2026-04-06

---

## Summary

All planned phases (1-13) are complete. The application is in maintenance mode with open tech debt items tracked in DEVELOPER.md.

## Architecture

- **Frontend:** SvelteKit + TypeScript + Tailwind CSS
- **Backend:** Python + FastAPI + SQLModel
- **Database:** SQLite (local) / Supabase (production)
- **Job Processing:** Background worker with OCR + LLM matching pipeline
- **Real-time Updates:** Dual SSE architecture (event bus + per-job streams)

## Route Structure

```
/                             → Marketing landing
/workspace/campaigns          → Campaign list (sortable, searchable)
/workspace/[id]               → Campaign dashboard
/workspace/[id]/upload        → Upload page (voter list + petitions)
/workspace/[id]/jobs          → Jobs scoped to campaign (SSE updates)
/workspace/[id]/jobs/new      → Job creation page
/workspace/[id]/jobs/[job_id] → Job details
/workspace/[id]/results       → Results scoped to campaign
/workspace/settings           → Global settings + LLM providers + feature flags
/workspace/demo               → Demo mode (virtual campaign)
```

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Provider storage | Snapshot only (no FK) | Survives provider deletion |
| Campaign status | On-demand compute | No cache invalidation |
| Dashboard updates | Polling (10s) | Simpler for aggregate metrics |
| Job status updates | SSE (dual architecture) | Real-time UX |
| Demo mode | In-memory virtual campaign | No persistence complexity |
| Job retry | New job with parent_job_id | Clear audit trail |

## Data Model

Core tables: `campaigns`, `matcher_job`, `match_result`, `llm_provider_config`, `ocr_results`, `voter_list_uploads`, `region_schemas`

## Open Items

See [DEVELOPER.md](./DEVELOPER.md) for current tech debt and open tasks.

## References

- [DEVELOPER.md](./DEVELOPER.md) — Developer workflow
- [docs/architecture/decisions/](../docs/architecture/decisions/) — Architecture Decision Records
