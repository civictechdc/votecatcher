# Votecatcher Development Progress

| Metric | Value |
|--------|-------|
| **Current Phase** | Event Bus |
| **Phase Status** | 📋 Planned |
| **Blocking Issues** | 0 |
| **Tests Passing** | Backend: 181 ✅ / Frontend: 35 ✅ |

---

## Current Work

**Phase:** Event Bus (Phase 10 Enhancement)
**Status:** 📋 Ready to implement

**Design:** `docs/plans/2026-03-24-event-bus-design.md`
**Plan:** `docs/plans/2026-03-24-event-bus-implementation.md`

**Exit Criteria:**
- [ ] Event bus publishes typed events with auto-source
- [ ] SSE transport streams events to frontend
- [ ] Worker publishes job status/progress events
- [ ] Frontend connects to campaign event stream
- [ ] Polling removed from dashboard and jobs list
- [ ] All tests pass

---

## Completed Phases

| Phase | Status | Completed |
|-------|--------|-----------|
| Phase 1-6 (MVP) | ✅ | 2026-03-12 |
| Phase 7-13 (Post-MVP) | ✅ | 2026-03-18 |

---

## Outstanding Items

### From FEEDBACK.md
- Dashboard voter list checkbox not updating after upload
  - Root cause: `import_voter_list()` never creates `VoterListUpload` record
  - Fix required in `file_service.import_voter_list()`

---

## Blockers

| # | Issue | Impact | Status | Resolution |
|---|-------|--------|--------|------------|
| (none) | | | | |

---

## Questions & Concerns

| # | Type | Question/Concern | Status | Answer |
|---|------|------------------|--------|--------|
| (none) | | | | |

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-24 | Event bus with SSE-only transport | WebSocket deferred, ~2hr add later |
| 2026-03-24 | Auto-source detection via inspect | DX improvement, accurate traceability |

---

## Verification Commands

```bash
# Backend tests
cd backend && uv run pytest tests/unit tests/integration -v

# Frontend tests
cd frontend-svelt && bun run test:e2e

# Type check
cd frontend-svelt && bun run check
```
