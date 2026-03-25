# Votecatcher Development Progress

| Metric | Value |
|--------|-------|
| **Current Phase** | Event Bus |
| **Phase Status** | 📋 Planned |
| **Blocking Issues** | 0 |
| **Tests Passing** | Backend: 181 ✅ / Frontend: 35 ✅ |

---

## Phase 13: Voter List Tracking - ✅ COMPLETE

**Started:** 2026-03-19
**Completed:** 2026-03-19

**Exit Criteria:**
- [x] Voter list uploads tracked with history
- [x] Dashboard shows progress stepper (for campaigns without results)
- [x] Merge/update logic handles duplicate voters
- [x] All tests pass (unit + integration + E2E)
- [x] Documentation updated

---

## Next: Event Bus

**Design:** `docs/plans/2026-03-24-event-bus-design.md`
**Plan:** `docs/plans/2026-03-24-event-bus-implementation.md`

**Scope:**
- Typed pub-sub event bus with auto-source detection
- SSE transport for browser clients
- Replace HTTP polling in dashboard and jobs list
- Campaign-scoped real-time updates

---

## Outstanding Fix (from FEEDBACK.md)

- Dashboard voter list checkbox not updating after upload
  - Root cause: `import_voter_list()` never creates `VoterListUpload` record
  - Fix required in `file_service.import_voter_list()`
