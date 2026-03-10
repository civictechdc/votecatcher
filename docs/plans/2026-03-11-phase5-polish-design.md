# Phase 5 Polish: Error Handling, Performance, Documentation

**Date:** 2026-03-11
**Status:** Approved
**Phase:** Phase 5 - Polish & Demo

---

## Overview

This document covers Phase 5 Parts B, C, and D:
- **Part B:** Error Handling (comprehensive error scenarios)
- **Part C:** Performance (Lighthouse score >80)
- **Part D:** Documentation (auto-generated API docs + user guides)

---

## Part B: Error Handling

### Test Scenarios (TDD First)

#### 1. API Error Tests (`tests/integration/errors/`)

| Scenario | Expected Behavior |
|----------|-------------------|
| Network failure during fetch | Show error message, retry button |
| 404 Not Found | Specific "Not found" message, link to workspace |
| 500 Server Error | Generic error message, retry button |
| Timeout (>30s) | Timeout message, retry button |

#### 2. Form Validation Error Tests (per-page)

| Page | Scenario | Expected Behavior |
|------|----------|-------------------|
| Upload | Invalid file type | "Unsupported file type" message |
| Upload | Missing file | "Please select a file" message |
| Campaign Create | Missing name | "Campaign name required" message |
| Campaign Create | Invalid year | "Please select a valid year" message |
| Job Create | Missing campaign_id | "Please select a campaign" message |
| Job Create | Invalid scan_ids | "No petition scans selected" message |

#### 3. SSE Connection Error Tests (`tests/e2e/job-status.spec.ts`)

| Scenario | Expected Behavior |
|----------|-------------------|
| Connection lost | Show "Connection lost" message |
| Auto-reconnect | Exponential backoff (1s, 2s, 4s, 8s) |
| Reconnect success | Clear error, resume updates |
| Max retries exceeded | Show "Unable to reconnect" message |

#### 4. Getting-Started Error Tests (`tests/e2e/getting-started.spec.ts`)

| Scenario | Expected Behavior |
|----------|-------------------|
| Invalid API key format | "Invalid API key format" message |
| API key validation fails | "Unable to verify API key" message |
| Provider service unavailable | "Provider temporarily unavailable" message |
| Campaign creation fails (duplicate) | "Campaign name already exists" message |
| File upload validation fails | Specific validation error message |

### Components & Pages

#### Enhanced `+error.svelte`

```
Features:
- Use existing ErrorDisplay component
- Specific messages for error codes (404, 500, 422, 403)
- Retry button for recoverable errors
- Link to workspace for navigation errors
- Accessible (role="alert", aria-live)
```

#### Server-Side Error Functions

| File | Purpose |
|------|---------|
| `src/routes/workspace/campaigns/+page.server.ts` | Wrap campaign API calls with error handling |
| `src/routes/workspace/upload/+page.server.ts` | Wrap upload API calls with error handling |
| `src/routes/workspace/jobs/+page.server.ts` | Wrap job API calls with error handling |
| `src/routes/workspace/results/+page.server.ts` | Wrap results API calls with error handling |

Use SvelteKit's `error()` and `fail()` functions for proper error boundaries.

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/routes/+error.svelte` | Modify | Enhanced error page |
| `src/routes/workspace/*/+page.server.ts` | Modify | Add error handling |
| `tests/integration/errors/test_api_errors.ts` | Create | API error tests |
| `tests/e2e/errors.spec.ts` | Create | E2E error scenarios |
| `tests/e2e/getting-started.spec.ts` | Modify | Add error scenarios |

---

## Part C: Performance (Lighthouse Score >80)

### Lighthouse Audit Areas

#### 1. Performance Metrics
- First Contentful Paint (FCP) - Target: <1.8s
- Largest Contentful Paint (LCP) - Target: <2.5s
- Cumulative Layout Shift (CLS) - Target: <0.1
- Total Blocking Time (TBT) - Target: <200ms

#### 2. Accessibility (already Phase 5 Part A)
- Color contrast: 4.5:1 minimum
- ARIA labels on all interactive elements
- Keyboard navigation
- Screen reader support

#### 3. Best Practices
- No browser console errors
- Modern JavaScript (no deprecated APIs)
- Proper HTTPS (production)

#### 4. SEO
- Document title on all pages
- Meta description on all pages
- Proper heading hierarchy (h1 → h2 → h3)
- Image alt attributes

### Likely Fixes Based on Current State

#### High Impact (Priority 1)

| Issue | Fix | Files |
|-------|-----|-------|
| Missing meta description | Add `<svelte:head>` with meta | All `+page.svelte` |
| Missing page titles | Add `<svelte:head><title>` | All `+page.svelte` |
| Deprecated event handlers | `on:change` → `onchange` | `getting-started/+page.svelte` |

#### Medium Impact (Priority 2)

| Issue | Fix | Files |
|-------|-----|-------|
| Missing image alt | Add alt attributes | Components with images |
| External links without noopener | Add `rel="noopener noreferrer"` | All external links |
| Heading hierarchy | Ensure h1 → h2 → h3 | All pages |

#### Low Impact (Priority 3)

| Issue | Fix | Files |
|-------|-----|-------|
| Unused CSS | Purge with Tailwind | Build config |
| Bundle size | Code splitting if needed | `vite.config.ts` |

### Test Approach

1. Run Lighthouse on key pages:
   - `/workspace` (dashboard)
   - `/workspace/campaigns`
   - `/workspace/jobs`
   - `/workspace/results`
   - `/getting-started`

2. Fix issues until all pages score >80

3. Document final scores in PROGRESS.md

### Files to Modify

| File | Purpose |
|------|---------|
| `src/routes/**/+page.svelte` | Add meta tags, titles |
| `src/app.html` | Global meta tags if needed |
| `svelte.config.js` | Prerendering config if needed |

---

## Part D: Documentation

### 1. API Documentation (Auto-Generated)

**Tool:** `@redocly/cli`

**Source:** `backend/openapi.yaml`

**Output:** `docs/api/index.html`

**Build Script:**
```json
{
  "scripts": {
    "docs:api": "redocly build-doc backend/openapi.yaml -o docs/api/index.html"
  }
}
```

**Features:**
- Interactive API explorer
- Request/response examples
- Authentication details
- Error response documentation

### 2. User Guide Structure

**Main Entry:** `docs/user-guide/README.md`

```
docs/user-guide/
├── README.md              # Overview + navigation
├── getting-started.md     # First-time setup
├── uploading-data.md      # Voter list, petition uploads
├── running-jobs.md        # Job creation, monitoring
├── viewing-results.md     # Results table, filtering, export
├── sessions.md            # Session management
└── demo-mode.md           # Demo features
```

### Document Templates

#### README.md (Main Entry)

```markdown
# VoteCatcher User Guide

## Quick Links

- [Getting Started](./getting-started.md) - Set up your first campaign
- [Uploading Data](./uploading-data.md) - Upload voter lists and petitions
- [Running Jobs](./running-jobs.md) - Create and monitor OCR/matching jobs
- [Viewing Results](./viewing-results.md) - Analyze matching results
- [Sessions](./sessions.md) - Save and restore workspace state
- [Demo Mode](./demo-mode.md) - Try VoteCatcher with sample data

## Overview

[2-3 sentence overview of VoteCatcher workflow]
```

#### Per-Guide Template

```markdown
# [Workflow Name]

## Overview

[What this workflow accomplishes in 1-2 sentences]

## Prerequisites

- [Requirement 1]
- [Requirement 2]

## Steps

### Step 1: [Action]

[Instructions with screenshots if helpful]

### Step 2: [Action]

[Instructions]

## Troubleshooting

### [Common Issue 1]

**Problem:** [Description]
**Solution:** [Fix]

### [Common Issue 2]

**Problem:** [Description]
**Solution:** [Fix]

## Related

- [Link to related guide]
- [Link to API docs]
```

### Files to Create

| File | Content |
|------|---------|
| `docs/api/index.html` | Auto-generated API docs |
| `docs/user-guide/README.md` | User guide home |
| `docs/user-guide/getting-started.md` | Setup guide |
| `docs/user-guide/uploading-data.md` | Upload workflows |
| `docs/user-guide/running-jobs.md` | Job management |
| `docs/user-guide/viewing-results.md` | Results analysis |
| `docs/user-guide/sessions.md` | Session features |
| `docs/user-guide/demo-mode.md` | Demo walkthrough |

### Files to Modify

| File | Change |
|------|--------|
| `README.md` | Add links to user-guide and api docs |
| `package.json` | Add `docs:api` script |

---

## Implementation Order

1. **Part C: Performance** (quickest win)
   - Run Lighthouse, fix issues
   - Estimated: 2-3 hours

2. **Part B: Error Handling** (most complex)
   - Write tests first (TDD)
   - Implement error pages and handlers
   - Estimated: 4-5 hours

3. **Part D: Documentation** (straightforward)
   - Generate API docs
   - Write user guides
   - Estimated: 3-4 hours

**Total Estimated Time:** 9-12 hours

---

## Success Criteria

### Part B: Error Handling
- [ ] All error scenarios have tests
- [ ] Error pages show user-friendly messages
- [ ] Retry functionality works for recoverable errors
- [ ] SSE auto-reconnect works with exponential backoff

### Part C: Performance
- [ ] All key pages score >80 on Lighthouse
- [ ] No console errors
- [ ] Proper meta tags on all pages
- [ ] Documented scores in PROGRESS.md

### Part D: Documentation
- [ ] API docs generated and accessible
- [ ] All user guide documents created
- [ ] README links to documentation
- [ ] Guides tested with fresh user perspective
