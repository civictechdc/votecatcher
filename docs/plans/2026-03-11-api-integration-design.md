# Phase 3 Part C: API Integration Design

**Date:** 2026-03-11
**Status:** Approved
**Author:** Developer Agent

## Overview

Connect frontend components to backend API endpoints using generated OpenAPI client and Svelte stores for state management.

## Architecture

### State Management Approach

**Decision:** Option A - Svelte Stores

```
Generated API Client → Svelte Stores → Page Components
                          ↓
                    Loading/Error States
                          ↓
                    UI Components
```

**Rationale:**
- Single source of truth per domain
- Reactive updates across pages
- Easy to test with mocked client
- Consistent pattern for all features

### Store Structure

```
src/lib/stores/
├── api-client.ts       # Configured generated client singleton
├── campaigns.ts        # Campaign CRUD state
├── campaigns.test.ts
├── jobs.ts             # Job orchestration state
├── jobs.test.ts
├── results.ts          # Match results state
└── results.test.ts
```

### API Client Integration

**Decision:** Option A - Generated OpenAPI Client

**Advantages:**
- Type-safe API calls
- Auto-updates when spec changes
- Works with MSW for testing
- Better IDE support

**Client Wrapper:**
```typescript
// src/lib/stores/api-client.ts
import { DefaultApi } from '$lib/api/generated';

const client = new DefaultApi({
  BASE: PUBLIC_API_URL || 'http://localhost:8000'
});

export { client };
```

**Testing with Mocking:**
- MSW for integration tests (already in devDependencies)
- Vitest mocks for store unit tests
- TypeScript types for mock responses

## Implementation Scope

### Dashboard (Minimal - Navigation Focused)

**Metrics:**
- Active Campaigns (count only)
- Quick Actions (navigation buttons)

**No per-campaign metrics** - those live in campaign detail pages.

**Rationale:** Aggregated metrics like "50 high confidence matches" lack context without campaign association.

### Campaign Detail Page Metrics

- Signatures processed
- High/Medium/Low confidence match counts
- Recent jobs for this campaign
- Upload progress (if active)
- Results needing review

## Implementation Order

### Phase 1: Foundation (Day 1 - ~4 hours)

1. **API Client Wrapper** (30 min)
   - Configure generated client with base URL
   - Add error handling middleware
   - Export singleton instance

2. **Campaigns Store** (1.5 hours)
   - CRUD operations: fetchAll, create, update, delete
   - Loading, error, data states
   - Unit tests with mocked client

3. **Dashboard Update** (1 hour)
   - Replace hardcoded "0" with campaigns count
   - Add loading skeleton
   - Error handling with retry

4. **Campaigns List Page** (1 hour)
   - Table with campaign data
   - Create campaign modal
   - Delete confirmation

### Phase 2: File Operations (Day 2 - ~3 hours)

5. **Jobs Store** (1.5 hours)
   - State transitions: create, fetch, cancel
   - Job status tracking
   - Unit tests

6. **File Upload Page** (1.5 hours)
   - Voter list upload with validation
   - Petition upload with progress
   - Job creation trigger

### Phase 3: Real-time & Results (Day 3 - ~4 hours)

7. **SSE Integration** (1.5 hours)
   - EventSource connection in jobs store
   - Auto-reconnect logic (3 retries)
   - Connection cleanup on navigation

8. **Job Status Page** (1 hour)
   - Live updates via SSE
   - Progress indicators
   - Error display

9. **Results Store** (1 hour)
   - Paginated results fetching
   - Confidence filtering
   - Unit tests

10. **Results Page** (30 min)
    - Table with pagination
    - Confidence filters
    - CSV export button

## Technical Patterns

### Store Pattern

Consistent interface across all stores:

```typescript
interface StoreState<T> {
  data: T[];
  loading: boolean;
  error: string | null;
}

// Store returns:
{
  subscribe,           // Svelte reactive subscription
  fetchAll,           // Load all items
  create,             // Create new item
  update,             // Update existing
  delete,             // Delete item
  clearError,         // Clear error state
}
```

### Error Handling

- Stores catch API errors, set `error` state
- Pages use `<LoadingState>` component
- Retry button calls store method again
- No global error boundary (MVP simplicity)

### SSE Connection Management

```typescript
// In jobs store
let eventSource: EventSource | null = null;

function connectToJob(jobId: string) {
  eventSource = new EventSource(`/api/jobs/${jobId}/status`);

  eventSource.onmessage = (event) => {
    const update = JSON.parse(event.data);
    // Update job state
  };

  eventSource.onerror = () => {
    // Retry logic (3 attempts)
  };
}

function disconnect() {
  eventSource?.close();
  eventSource = null;
}
```

## Testing Strategy

### Unit Tests (Stores)
- Mock generated client with Vitest
- Test state transitions
- Test error handling
- Target: >80% coverage

### Integration Tests (Pages)
- MSW handlers for API routes
- Test user flows
- Test loading/error states

### E2E Tests
- Real backend for critical paths
- Full workflow: create → upload → job → results

## API Endpoints Required

**Backend Status:** Phase 2.5 complete with 11 endpoints

**Used by Frontend:**
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign details
- `POST /api/upload/voter-list` - Upload voter list
- `POST /api/upload/petition` - Upload petition PDF
- `POST /api/jobs` - Create matcher job
- `GET /api/jobs/{id}` - Get job status
- `GET /api/jobs/{id}/status` - SSE endpoint
- `POST /api/jobs/{id}/cancel` - Cancel job
- `GET /api/jobs/{job_id}/results` - Get results (paginated)
- `GET /api/jobs/{job_id}/results/export` - Export CSV

**Gap Identified:** No `/api/jobs` list endpoint for "Running Jobs" count on dashboard.

**Resolution:** For MVP, omit "Running Jobs" metric. Dashboard shows:
- Active Campaigns count only
- Quick action buttons

## Design Principles

1. **Minimal Dashboard** - Navigation focused, no cross-campaign metrics
2. **Campaign-Centric Metrics** - Detailed data lives in campaign pages
3. **Consistent Stores** - Same pattern across all domains
4. **Type Safety** - Generated client ensures contract matches backend
5. **Testable Architecture** - Stores mockable, pages testable with MSW

## Success Criteria

- [ ] Dashboard loads campaign count from API
- [ ] Campaigns CRUD works with loading/error states
- [ ] File upload shows progress and creates jobs
- [ ] Job status updates in real-time via SSE
- [ ] Results page paginates and filters correctly
- [ ] All stores have >80% test coverage
- [ ] E2E test passes for full workflow

## References

- [SPEC.md §5.2](../../openspec/SPEC.md#52-key-endpoints) - API Endpoints
- [PROGRESS.md](../../openspec/PROGRESS.md) - Current implementation status
- [Frontend Architecture](../frontend-architecture.md) - Component patterns

## Next Steps

1. Invoke `writing-plans` skill to create detailed implementation plan
2. Begin Phase 1: Foundation implementation with TDD
3. Verify each phase exit criteria before proceeding
