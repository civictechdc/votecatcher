# Votecatcher Development Progress

| Metric | Value |
|--------|-------|
| **Current Phase** | Post-MVP Polish |
| **Phase Status** | ✅ Complete |
| **Blocking Issues** | 0 |
| **Tests Passing** | Backend: 345 ✅ / Frontend: 44 ✅ |

---

## Current Work

**Task:** P4 Polish Items (Session 5)
**Status:** ✅ Complete (2026-03-26)

**Approach:** Dispatched 5 parallel subagents with guard rails

**Fixed This Session:**
| # | Issue | Resolution |
|---|-------|------------|
| #7 | Campaign context lost on settings nav | ✅ Already implemented - "Jump to Campaign" selector in generic Sidebar |
| #36 | Source inference not memoized | ✅ Added `@lru_cache(maxsize=128)` to `_infer_source()` |
| #40 | E2E event flow not verified | ✅ Added test: "SSE job status change updates job list in real-time" |
| #42 | Test assertion unreachable | ✅ Added explicit assertion for sentinel behavior |
| #43 | Campaign/job ID type inconsistency | ✅ Standardized both to `str` type |

**All Issues Resolved** - 37 fixed, 3 documented, 0 open

---

## Recently Completed

**Task:** P3/P4 Polish Items (Session 3)
**Status:** ✅ Complete (2026-03-26)

**Session Goals:**
- [x] P3 #1: Add E2E test verifying job status event updates UI
- [x] P3 #2: Add `loaded` flag to campaigns store, update Sidebar
- [x] P4 L1: Fix/remove unreachable test assertion
- [x] P4 L2: Add heartbeat debug logging to events.ts
- [x] P4 L4: Standardize campaign_id/job_id types (deferred - low priority, no bugs)

**Completed This Session:**
- [x] Added 2 E2E tests for CustomEvent handling (event-stream.spec.ts)
- [x] Added `loaded` flag to CampaignsState interface
- [x] Updated campaigns store to set `loaded: true` on successful fetch
- [x] Updated Sidebar to use `loaded` flag instead of `campaigns.length === 0`
- [x] Fixed pre-existing bug in campaigns.test.ts mock method name
- [x] Removed unreachable assertion in test_sse_transport.py
- [x] Added debug logging to events.ts for SSE connection status
- [x] Backend tests: 345 passed, 5 skipped
- [x] Frontend TypeScript check: 0 errors

---

## Recently Completed

**Task:** Issue #27 TypeScript Test Mocks Fix
**Status:** ✅ Complete (2026-03-25)

**Completed This Session:**
- [x] Fixed `vi.mock` pattern in campaigns-page.test.ts
- [x] Added proper factory function with mocked store methods
- [x] Imported mocked module after mock definition
- [x] TypeScript check: 0 errors (was 87)
- [x] Store unit tests: 27 passing

---

**Task:** Issue Cleanup (Medium Priority)
**Status:** ✅ Complete (2026-03-25)

**Completed:**
- [x] #28 SSE Transport Code Duplication - Extracted shared `_create_stream_generator()` method
- [x] #29 E2E Tests Fragile - Created test fixtures with seeded campaigns
- [x] #5 Type Safety in Job Status Handler - Replaced `as any` with `JobStatusEnum`
- [x] Documented dual SSE architecture (ADR-0001)
- [x] Updated ISSUES-AND-CHANGES.md - marked 6 issues resolved

---

## Recently Completed

**Task:** Verify Voter List Checkbox Fix (FEEDBACK.md #2)
**Status:** ✅ Complete (2026-03-25)

**Verification:**
- Added integration tests for `/api/campaigns/{id}/setup-status`
- Tests verify voter_list.exists updates correctly after upload
- 4 new tests added: `tests/integration/api/test_setup_status.py`

**Completed This Session:**
- [x] `test_setup_status_empty_campaign` - baseline test
- [x] `test_setup_status_campaign_not_found` - error handling
- [x] `test_setup_status_after_voter_list_upload` - **verifies the fix**
- [x] `test_setup_status_after_petition_upload` - petitions status

---

## Recently Completed

**Phase:** Event Bus (Phase 10 Enhancement)
**Status:** ✅ Complete (2026-03-25)

**Design:** `docs/plans/2026-03-24-event-bus-design.md`
**Plan:** `docs/plans/2026-03-24-event-bus-implementation.md`

**Exit Criteria:**
- [x] Event bus publishes typed events with auto-source
- [x] SSE transport streams events to frontend
- [x] Worker publishes job status/progress events
- [x] Frontend connects to campaign event stream
- [x] Polling removed from dashboard and jobs list
- [x] All tests pass

**Tasks:**

| # | Task | Status | Notes |
||---|------|--------|-------|
| 1 | Event Types | ✅ | |
| 2 | Event Bus Core | ✅ | |
| 3 | Transport Interface | ✅ | |
| 4 | SSE Transport | ✅ | Implemented, tests pass |
| **4.5** | **Cleanup & Optimization** | ✅ | Already in `event_bus.py:47-51` |
| 5 | Events Router | ✅ | Routes at /events/* |
| 6 | Worker Publisher | ✅ | Events at OCR/MATCHING transitions |
| **6.5** | **Metrics Event Publisher** | ✅ | Added `MetricsUpdatedEvent` publish after job completes |
| 7 | Frontend Event Store | ✅ | Created with reconnection resilience |
| **7.5** | **Reconnection Resilience** | ✅ | Included in Task 7 |
| 8 | Jobs Store Handlers | ✅ | Added handleStatusEvent, handleProgressEvent |
| 9 | Campaign Layout | ✅ | Connects to event stream on mount |
| 10 | Remove Dashboard Polling | ✅ | Polling removed |
| 11 | Remove Jobs Polling | ✅ | Polling removed |
| 12 | E2E Test | ✅ | Added `event-stream.spec.ts` |
| 13 | Final Verification | ✅ | All 322 backend tests pass |

---

## Completed Phases

| Phase | Status | Completed |
|-------|--------|-----------|
| Phase 1-6 (MVP) | ✅ | 2026-03-12 |
| Phase 7-13 (Post-MVP) | ✅ | 2026-03-18 |
| Phase 10 Enhancement (Event Bus) | ✅ | 2026-03-25 |
| Voter List Checkbox Fix Verification | ✅ | 2026-03-25 |

---

## Outstanding Items

### From FEEDBACK.md

**✅ RESOLVED: Dashboard voter list checkbox not updating after upload**

Fixed and verified via integration test (`test_setup_status.py`). The `VoterListUpload` record is correctly created and `get_active_upload()` finds it for the setup-status endpoint.

---

## Code Review: 2026-03-25 (RESOLVED)

**Reviewer:** AI Code Review
**Scope:** Event Bus implementation (Tasks 1-13)
**Status:** ✅ All issues resolved

### ✅ What's Done Well

- Clean typed events with Pydantic + Literal for discriminated unions
- Auto-source detection via `inspect` - great DX feature
- Graceful queue full handling, topic cleanup
- SSE transport with heartbeats and proper cleanup
- Exponential backoff reconnection (5 attempts, 1s base)
- CustomEvent dispatch pattern decouples event store from handlers
- Polling fully removed (verified - no `setInterval` in codebase)
- Good unit test coverage for event bus (10 tests) and types (7 tests)
- Metrics event now published after job completion

### ✅ Issues Fixed

| # | Priority | Issue | Status | Resolution |
|---|----------|-------|--------|------------|
| 1 | **High** | `MetricsUpdatedEvent` never published | ✅ Fixed | Added `_compute_job_metrics()` and publish in `worker.py` |
| 2 | **High** | Indentation error in sse.py | ✅ Fixed | Fixed tabs/spaces in `close()` method |
| 3 | **Medium** | E2E test missing | ✅ Fixed | Added `event-stream.spec.ts` |
| 4 | **Medium** | Dual SSE architecture | 📝 Documented | Note: old `connectToJob()` not called from campaign layout |
| 5 | **Low** | No metrics handler in frontend | ✅ Fixed | Added `handleMetricsEvent()` to campaigns store |

---

## Code Review: 2026-03-25 (Follow-up)

**Reviewer:** AI Code Review (Pass 2)
**Scope:** Event Bus, SSE Transport, E2E Tests
**Status:** 🔶 Minor improvements recommended

### Issues to Address

| # | Priority | Issue | Location | Recommendation |
|---|----------|-------|----------|----------------|
| 1 | **Medium** | Code duplication in SSE transport | `sse.py:21-34`, `sse.py:51-63` | Extract shared `generate()` logic to helper method |
| 2 | **Medium** | E2E tests are fragile | `event-stream.spec.ts` | Seed test data so tests don't skip when no campaigns exist |
| 3 | **Low** | Inconsistent ID types | `event_types.py:21-22` | Standardize `campaign_id` and `job_id` to same type (str or int) |
| 4 | **Low** | Late import in worker | `worker.py:261` | Move `MetricsService` import to top-level or use DI |

### Minor Nits

| File | Line | Issue |
|------|------|-------|
| `events.ts` | 91-105 | `handleMetricsEvent` doesn't validate event shape before update |
| `event_bus.py` | 19-36 | `_infer_source` could memoize for performance |
| `test_event_bus.py` | 75-82 | `MAX_QUEUE_SIZE = 1` mutation on class could affect parallel tests |

### Recommended Refactor for Issue #1

```python
# sse.py - Extract shared generator
def _create_stream_generator(self, topic: str, queue: asyncio.Queue):
    async def generate():
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {message}\n\n"
                except TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(topic, queue)
            self._active_queues.discard(queue)
    return generate()

async def subscribe_to_campaign(self, campaign_id: str) -> StreamingResponse:
    topic = f"campaign:{campaign_id}"
    queue = event_bus.subscribe(topic)
    self._active_queues.add(queue)
    return StreamingResponse(
        self._create_stream_generator(topic, queue),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
```

---

## Code Review: 2026-03-25 (Pass 3)

**Reviewer:** AI Code Review
**Scope:** Event Bus Implementation Review
**Status:** ✅ Complete - 3 new issues logged

### New Issues Found

| # | Priority | Issue | Location | Status |
|---|----------|-------|----------|--------|
| #32 | **Low** | No event validation before store update | `events.ts:127-128` | Open |
| #33 | **Low** | Test class attribute mutation | `test_event_bus.py:77` | Open |
| #34 | **Low** | E2E tests don't verify job events | `event-stream.spec.ts` | Open |

### Summary

All high/medium issues from previous passes resolved. Remaining items are low-priority polish:
- #30, #31 (from Pass 2) still open
- #32, #33, #34 (new) logged to ISSUES-AND-CHANGES.md

---

## Code Review: 2026-03-25 (Pass 4)

**Reviewer:** AI Code Review
**Scope:** Event Bus Implementation (DDD/BDD Review)
**Status:** ✅ Complete - 4 new issues logged

### Overall Assessment: 8/10

Clean implementation with good typed events, proper cleanup, and nice DX features. A few reliability and test coverage gaps.

### ✅ What's Done Well

| Area | Details |
|------|---------|
| **Typed Events** | Pydantic + Literal for discriminated unions |
| **Auto-source detection** | `inspect`-based source inference - great for debugging |
| **Queue management** | Graceful `QueueFull` handling, topic cleanup |
| **SSE cleanup** | Proper unsubscribe in finally block |
| **Reconnection resilience** | Exponential backoff, max attempts |
| **Decoupled handlers** | CustomEvent pattern keeps stores independent |

### New Issues Found

| # | Priority | Issue | Location | Status |
|---|----------|-------|----------|--------|
| #35 | **Medium** | Race condition in event disconnect | `events.ts`, `+layout.svelte` | Open |
| #36 | **Low** | Source inference not memoized | `event_bus.py:19-36` | Open |
| #37 | **Low** | Heartbeat not acknowledged by client | `events.ts` | Open |
| #38 | **Medium** | SSE transport unit tests missing | `tests/unit/events/` | Open |

### Summary

Implementation is solid for MVP. New issues are polish/reliability items:
- #35 (race condition) - defensive fix recommended for P3
- #36 (memoization) - low priority, may be YAGNI
- #37 (heartbeat) - nice to have, not critical
- #38 (tests) - should add before declaring event bus "done"

### Files Logged

| File | Issue # |
|------|---------|
| `frontend-svelt/src/lib/stores/events.ts` | #35, #37 |
| `backend/app/events/event_bus.py` | #36 |
| `backend/tests/unit/events/transports/test_sse.py` | #38 (NEW file needed) |

---

## Code Review: 2026-03-26 (Pass 6 - Session 2)

**Reviewer:** AI Code Review
**Scope:** SSE Transport Sentinel Fix (#39) + Campaign Switcher (#7)
**Status:** ✅ Production-Ready (3 minor items)

### Overall: 8/10

### ✅ What's Done Well

| Area | Assessment |
|------|------------|
| **Sentinel pattern (#39)** | Clean fix - `None` sentinel unblocks generators immediately on `close()`. Tests verify <1s exit time. |
| **Shared generator extraction** | `_create_stream_generator()` eliminates duplication between campaign/job subscriptions |
| **Event validation** | `isValidEvent()` type guard prevents malformed events |
| **Test coverage** | 15 SSE transport tests including edge cases like quick-exit verification |

### 🔶 Minor Issues

| # | Priority | Issue | Location |
|---|----------|-------|----------|
| **R1** | Low | `test_close_sends_sentinel...` assertion unreachable | `test_sse_transport.py:179-181` |
| **R2** | Low | Heartbeat not logged client-side | `events.ts` |
| **R3** | Low | Sidebar fetches on every mount | `Sidebar.svelte:37-41` |

#### R1: Test assertion unreachable

```python
# test_sse_transport.py:179-181 - assertion path never hit
assert result is None or result == "", ...
```

Generator breaks on `None` without yielding, so `StopAsyncIteration` is caught instead. Test passes but assertion is misleading.

**Fix:** Remove assertion block or document expected `StopAsyncIteration` path.

#### R2: Heartbeat silently ignored

Server sends `": heartbeat\n\n"` (SSE comment format) but client `onmessage` only parses JSON. Fine for keep-alive, but could log for debugging.

#### R3: Sidebar fetch pattern

```svelte
onMount(() => {
    if ($campaigns.campaigns.length === 0) {
        campaigns.fetchAll();
    }
});
```

Every mount checks length. Consider `loaded` flag in store to avoid redundant checks.

---

## Code Review: 2026-03-26 (Pass 7 - Comprehensive)

**Reviewer:** AI Code Review
**Scope:** Full Event Bus + P3 Polish Items Review
**Status:** ✅ Production-Ready (2 medium, 4 low items)

### Overall: 8/10

Comprehensive review of SSE transport, event bus, campaign switcher, voter list metrics, OCR batching, and E2E tests.

### ✅ What's Done Well

| Area | Assessment |
|------|------------|
| **Sentinel pattern (#39)** | Clean `None` sentinel unblocks generators immediately. Tests verify <1s exit. |
| **DRY in SSE transport** | `_create_stream_generator()` eliminates duplication |
| **Event validation** | `isValidEvent()` type guard prevents malformed events |
| **Test coverage** | 15 SSE transport tests including quick-exit edge cases |
| **Typed events** | Pydantic + Literal discriminated unions for type safety |
| **Auto-source detection** | `inspect`-based inference great for debugging |
| **Graceful shutdown** | Queue cleanup + sentinel ensures no hanging generators |
| **Campaign switcher** | Clean UI with proper ARIA attributes |
| **Voter list count** | Proper `None` handling when no voter list uploaded |
| **OCR batching** | Configurable threshold + feature flag with tests |

### 🔶 Medium Issues (2)

| # | Issue | Location | Effort |
|---|-------|----------|--------|
| **M1** | E2E tests don't verify actual event flow | `event-stream.spec.ts:51-95` | ~30min |
| **M2** | Sidebar fetches campaigns on every mount | `Sidebar.svelte:37-41` | ~15min |

#### M1: E2E Event Flow Not Verified

Job event tests check `typeof eventSourceConnected === 'boolean'` but don't verify events are actually received and processed.

**Fix:**
```typescript
// Trigger a real job event and verify UI updates
test('job status event updates job list', async ({ page, seededCampaign }) => {
  // 1. Start a job via API
  // 2. Wait for SSE event to arrive
  // 3. Assert job status changed in UI
});
```

#### M2: Sidebar Redundant Fetches

Every Sidebar mount checks `$campaigns.campaigns.length === 0` and may trigger fetch.

**Fix:** Add `loaded` flag to campaigns store:
```typescript
// campaigns.ts
interface CampaignState {
  campaigns: Campaign[];
  loaded: boolean;  // Add this
  loading: boolean;
  error: string | null;
}

// Sidebar.svelte
onMount(() => {
  if (!$campaigns.loaded && !$campaigns.loading) {
    campaigns.fetchAll();
  }
});
```

### 💡 Low Priority (4)

| # | Issue | Location | Effort |
|---|-------|----------|--------|
| **L1** | Test assertion unreachable | `test_sse_transport.py:179-181` | ~5min |
| **L2** | Heartbeat silently ignored client-side | `events.ts` | ~5min |
| **L3** | `_infer_source` not memoized | `event_bus.py:19-36` | ~10min |
| **L4** | Campaign/job ID type inconsistency | `event_types.py:21-22` | ~15min |

#### L1: Unreachable Test Assertion

Generator breaks on `None` sentinel without yielding, so `StopAsyncIteration` is caught - assertion at line 179 never executes.

**Fix:** Remove assertion block or document expected `StopAsyncIteration` path.

#### L2: Heartbeat Not Logged

Server sends `: heartbeat\n\n` (SSE comment) but client `onmessage` only parses JSON. Fine for keepalive, but logging would help debugging.

**Fix:**
```typescript
eventSource.onmessage = (event) => {
  // Heartbeat comments don't trigger onmessage, but if using a different format:
  if (event.data === '') {
    console.debug('SSE heartbeat received');
    return;
  }
  // ... existing logic
};
```

#### L3: Source Inference Not Memoized

`_infer_source()` uses `inspect` on every publish. For high-frequency events, this could add overhead.

**Fix:** Consider caching or accept as YAGNI (current volume is low).

#### L4: ID Type Inconsistency

```python
campaign_id: str | None  # Line 21
job_id: int | None       # Line 22
```

**Recommendation:** Standardize to one type (str for UUID compatibility) for consistency.

### Security Review

- ✅ No secrets in code
- ✅ Event data validated with type guards
- ✅ No SQL injection vectors
- ⚠️ Verify SSE endpoint has auth middleware (not reviewed in this pass)

### Test Coverage Summary

| Area | Tests | Status |
|------|-------|--------|
| SSE Transport | 15 | ✅ Excellent |
| Event Bus | 10 | ✅ Good |
| Event Types | 7 | ✅ Good |
| Integration | 30 | ✅ Good |
| E2E Events | 4 | ⚠️ Needs event flow verification |
| OCR Batching | 5 | ✅ Good |

---

## Actionable Items

### P3 (Should Do)

| # | Task | Priority | Effort | Status |
|---|------|----------|--------|--------|
| 1 | Add E2E test that verifies job status event updates UI | Medium | 30min | ✅ Done |
| 2 | Add `loaded` flag to campaigns store, update Sidebar | Medium | 15min | ✅ Done |

### P4 (Nice to Have)

| # | Task | Priority | Effort | Status |
|---|------|----------|--------|--------|
| 3 | Fix/remove unreachable test assertion (L1) | Low | 5min | ✅ Done |
| 4 | Add heartbeat debug logging (L2) | Low | 5min | ✅ Done |
| 5 | Standardize campaign_id/job_id types (L4) | Low | 15min | Deferred (no bugs) |
| 6 | Memoize `_infer_source` if perf becomes issue (L3) | Low | 10min | Deferred |

---

## Code Review: 2026-03-26 (Pass 5)

**Reviewer:** AI Code Review
**Scope:** Full Event Bus Implementation Review
**Status:** ✅ Production-Ready (1 minor issue)

### Overall Assessment: 8/10

Clean implementation with good typed events, proper cleanup, and solid DX features.

### ✅ What's Done Well

| Area | Assessment |
|------|------------|
| **Typed Events** | Pydantic + Literal for discriminated unions - excellent type safety |
| **Auto-source detection** | `inspect`-based inference at `event_bus.py:19-36` - great for debugging |
| **Queue management** | Graceful `QueueFull` handling, automatic topic cleanup |
| **SSE cleanup** | Proper unsubscribe in `finally` block (`sse.py:32-34`) |
| **Code reuse** | `_create_stream_generator()` extracted (Issue #28 fixed) |
| **Reconnection resilience** | Exponential backoff, 5 max attempts (`events.ts:60-61`) |
| **Event validation** | `isValidEvent()` type guard before processing (`events.ts:38-45`) |
| **Decoupled handlers** | CustomEvent pattern keeps stores independent |

### Test Coverage

```
tests/unit/events/test_event_bus.py: 10 passed
tests/unit/events/test_event_types.py: 7 passed
tests/integration/api/test_events.py: 30 passed
Total: 47 passed, 2 skipped ✅
```

### Issues Found

| # | Priority | Issue | Location | Status |
|---|----------|-------|----------|--------|
| **N1** | Medium | `close()` doesn't cancel active generators | `sse.py:58-62` | Open |
| **N2** | Low | `_infer_source` not memoized | `event_bus.py:19-36` | Tracked (#36) |

#### N1: `close()` doesn't cancel active generators

```python
# sse.py:58-62 - current implementation
async def close(self):
    for queue, topic in self._active_subscriptions.items():
        event_bus.unsubscribe(topic, queue)
    self._active_subscriptions.clear()
```

The generators in `_create_stream_generator()` are still running - they'll only exit when they try to get from an empty queue. This could cause a brief resource leak on shutdown.

**Recommended Fix:**
```python
async def close(self):
    for queue, topic in list(self._active_subscriptions.items()):
        event_bus.unsubscribe(topic, queue)
        await queue.put(None)  # Sentinel to unblock generator
    self._active_subscriptions.clear()
```

Then update `_create_stream_generator()` to check for sentinel:
```python
message = await asyncio.wait_for(queue.get(), timeout=30.0)
if message is None:  # Shutdown sentinel
    break
yield f"data: {message}\n\n"
```

**Impact:** Low - only affects graceful shutdown, not runtime behavior.
**Effort:** ~10 minutes

### Open P3 Items (Correctly Tracked)

These remain as low priority polish:
- #7 Campaign Context Lost (UI polish)
- #11 Redundant High Confidence Card (UI polish)
- #13 OCR Batching Threshold (enhancement)
- #34 E2E Tests Don't Verify Job Events (test coverage)
- #36 Source Inference Performance (YAGNI - negligible impact)

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
| 2026-03-25 | Use MetricsService for metrics event | Reuses existing logic, consistent metrics |

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
