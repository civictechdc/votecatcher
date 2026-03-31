# Phase 3 (v2): Frontend Onboarding Wizard — Corrected Implementation Plan

> **Supersedes:** [03-frontend-onboarding.md](./03-frontend-onboarding.md) (original had Svelte 4 syntax, CSS variables, and structural issues incompatible with the actual codebase)
>
> **Prerequisite:** Phase 2 complete (engine selection works)
>
> **Reviewer:** See the "Codebase Audit Findings" section below for a list of every issue found in the original plan.

**Goal:** Create a SvelteKit onboarding wizard with database selector and Supabase connection form, built on the project's actual Svelte 5 + Tailwind + runes conventions.

**Duration Estimate:** 6-8 hours

---

## UI Preview & Feedback Protocol

Every task group that creates visual components (3B, 3C, 3D) **must** include a preview step before committing. This gives you a chance to see the UI and provide feedback on layout, spacing, colors, and interactions.

### When to Preview

| Task Group | Preview Point | What You Review |
|------------|---------------|-----------------|
| 3B | After each component is built | Card layout, form spacing, button styles, hover states |
| 3C | After route structure is in place | Page flow, transitions, first-run redirect behavior |
| 3D | After settings page is built | Status card layout, disconnect confirmation, badge colors |

### How Preview Works

The developer will spin up a **temporary preview server** using the existing SvelteKit dev server (`bun run dev`) or an isolated HTML snapshot when the backend isn't available. You'll get a URL to open in your browser. The preview includes:

1. **Standalone render** — the component rendered in isolation with mock data (no backend dependency)
2. **Interactive states** — hover effects, validation errors, loading spinners, disabled buttons
3. **Mobile viewport** — a note on how it responds to smaller screens

### Design Decisions Requiring Your Input

These are the points where the plan needs your preference before implementation continues past the preview:

| Decision | Options | Preview Shows |
|----------|---------|---------------|
| **Database selector layout** | (A) Vertical card list (B) Horizontal 3-column grid (C) Icon-focused cards with large icons | All 3 rendered side-by-side |
| **Supabase form field order** | (A) URL → Key → Password (B) Key → URL → Password | Current vs alternative |
| **Settings page status card** | (A) Compact badge-in-header (B) Full-width card with sections | Both rendered |
| **Color scheme for status badges** | (A) Green/gray default (B) Green/amber/red tri-state | Connected, disconnected, error states |
| **Warning style for service key** | (A) Amber callout box (B) Red banner (C) Inline italic text | Each variant |

### Preview Checklist (Developer)

Before flagging a component for review:

- [ ] Component renders without errors in the browser
- [ ] All interactive states work (hover, focus, disabled, loading)
- [ ] No console errors
- [ ] Responsive at 375px, 768px, 1024px widths
- [ ] Keyboard navigation works (Tab, Enter, Escape)

---

## Codebase Audit Findings

The original `03-frontend-onboarding.md` was reviewed against the actual codebase. These issues made it unimplementable as-is:

| # | Issue | Severity | Root Cause |
|---|-------|----------|------------|
| 1 | **Svelte 4 syntax** in all components (`on:click`, `createEventDispatcher`, `export let`, `$:`) | Blocking | Project uses Svelte 5 (`^5.49.2`) with runes |
| 2 | **CSS variables** (`var(--border-color)`, `var(--primary-color)`, etc.) don't exist | Blocking | Project uses **Tailwind CSS** utility classes exclusively |
| 3 | **`API_BASE_URL`** imported from non-existent `./config` | Blocking | Project uses `PUBLIC_API_URL` from `$env/static/public` and the `request`/`fetchRaw` pattern in `client.ts` |
| 4 | **No `src/lib/types/` directory** — types are co-located with API files (`api/request-types.ts`, `api/response-types.ts`) | Medium | Different file organization convention |
| 5 | **Duplicates existing onboarding** — project already has `/getting-started` wizard with `onboard` store | Medium | Needs integration, not a parallel system |
| 6 | **First-run redirect loop** — modifying root `+layout.svelte` would redirect the onboarding page itself | Blocking | Needs route groups with `(app)` / `(standalone)` layout split |
| 7 | **No tests defined** — DEVELOPER.md mandates BDD/TDD red-green-refactor | Medium | Zero test files in original plan |
| 8 | **Ignores existing UI primitives** (`Button`, `Input`, `Select`, `Modal`, `LoadingState`, `ErrorDisplay`) | Medium | Plan builds everything from scratch |
| 9 | **`Input.svelte` lacks `type="url"`** support | Low | Only supports text/email/password/number/file |
| 10 | **`api` client not extended** — plan creates a parallel fetch-based client instead of extending the existing `api` object in `client.ts` | Medium | Wastes the existing retry/middleware infrastructure |

---

## Conventions Reference

These are extracted from the actual codebase. **All implementation must follow these.**

### Svelte 5 Patterns

```typescript
// Props (NOT export let)
interface Props {
  onSelect: (type: DatabaseType) => void;
  label?: string;
  children?: import('svelte').Snippet;
}
let { onSelect, label = '', children }: Props = $props();

// State (NOT let for reactive values)
let step = $state<'select' | 'supabase' | 'postgres' | 'complete'>('select');
let loading = $state(false);

// Derived (NOT $:)
let isValid = $derived(projectUrl.startsWith('https://') && serviceKey.length > 50);

// Effects (NOT reactive statements with side effects)
$effect(() => { /* side effect */ return () => { /* cleanup */ }; });

// Event handlers (NOT on:click)
<button onclick={() => handleSelect('supabase')}>...</button>
```

### Styling

- **Tailwind utility classes** only — no CSS variables, no `<style>` blocks with custom properties
- Existing component library at `src/lib/components/ui/` with barrel export in `index.ts`
- Uses `cn()` utility from `$lib/utils/cn` for class merging (clsx + tailwind-merge)

### API Client

- Extend `api` object in `src/lib/api/client.ts`
- Use `request<T>()` for typed results returning `ApiResult<T>`
- Use `fetchRaw()` for raw `Response` access
- Base URL from `PUBLIC_API_URL` env var
- Auto-retry on 5xx, middleware support built in

### Testing

- **Vitest** with jsdom environment (see `vitest.config.ts`)
- Unit tests in `tests/unit/`
- Mock `$app` and `$env/static/public` via `tests/__mocks__/`
- Test pattern: `vi.mock()`, `vi.fn()`, `describe/it/expect`
- Store tests use `get()` from `svelte/store`

### Stores

- Svelte stores pattern (not runes) — see `src/lib/stores/settings.ts` and `onboarding.ts`
- `writable` with custom creator functions exposing `{ subscribe, ...actions }`

---

## Phase Status

| Task Group | Status | Exit Gate |
|------------|--------|-----------|
| 3A: Types & API Client | Not Started | `vitest run tests/unit/api/database.test.ts` passes |
| 3B: Onboarding Components | Not Started | Components render in storybook |
| 3C: Onboarding Route & First-Run Guard | Not Started | Full flow works end-to-end |
| 3D: Settings Page | Not Started | Settings persist after page reload |

---

## Developer Notes

| Date | Status | Notes/Blockers/Concerns |
|------|--------|-------------------------|
| 2026-03-27 | Not Started | Original plan rewritten — Svelte 4→5, CSS vars→Tailwind, structural fixes |

---

## Entrance Gate

Verify Phase 2 is complete:

```bash
cd backend && uv run pytest tests/unit/persistence/ tests/integration/test_engine_selection.py -v
```

**Expected:** All tests pass

Also verify frontend tooling is healthy:

```bash
cd frontend-svelt && bun run check
cd frontend-svelt && bun run test:unit
```

**Expected:** Type check passes, existing unit tests pass

---

## Task Group 3A: Types & API Client

**Why this first:** Backend API endpoints don't exist yet (Phase 4), but the frontend client and types can be defined now. The `request<T>` pattern returns `ApiResult<T>`, so components can handle both `ok` and error states without throwing.

**Files:**
- Create: `frontend-svelt/src/lib/api/database-types.ts`
- Modify: `frontend-svelt/src/lib/api/client.ts` (add database methods to `api` object)
- Create: `frontend-svelt/tests/unit/api/database.test.ts`

### Step 1: Define TypeScript types

```typescript
// frontend-svelt/src/lib/api/database-types.ts

export type DatabaseType = 'sqlite' | 'postgres' | 'supabase';

export interface DatabaseStatus {
  configured: boolean;
  type: DatabaseType;
  connected: boolean;
  message: string;
}

export interface SupabaseCredentials {
  project_url: string;
  service_key: string;
  db_password: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  project_ref?: string;
}

export interface ProvisionResult {
  success: boolean;
  message: string;
  tables_created?: string[];
}
```

> **Note:** Types are placed alongside the API code in `api/database-types.ts`, following the existing convention of `api/request-types.ts` and `api/response-types.ts`.

### Step 2: Extend the API client

Add these methods to the `api` object in `frontend-svelt/src/lib/api/client.ts`:

```typescript
import type {
  DatabaseStatus,
  SupabaseCredentials,
  ConnectionTestResult,
  ProvisionResult,
} from './database-types';

// Add to the `api` object:
database: {
  getStatus: () =>
    request<DatabaseStatus>('/database/status', { method: 'GET' }),

  testSupabase: (credentials: SupabaseCredentials) =>
    request<ConnectionTestResult>('/database/supabase/test', {
      method: 'POST',
      body: credentials,
    }),

  provisionSupabase: (credentials: SupabaseCredentials) =>
    request<ProvisionResult>('/database/supabase/provision', {
      method: 'POST',
      body: credentials,
    }),

  disconnectSupabase: () =>
    request<{ success: boolean }>('/database/supabase', {
      method: 'DELETE',
    }),
},
```

> **Design choice:** Grouped under `api.database.*` namespace to avoid polluting the top-level `api` object and to make it clear these are database-specific calls. Uses the existing `request<T>()` which returns `ApiResult<T>` — callers destructure `{ ok, data, error }`.

### Step 3: Write tests (RED phase)

```typescript
// frontend-svelt/tests/unit/api/database.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('$env/static/public', () => ({
  PUBLIC_API_URL: 'http://localhost:8000/api',
}));

describe('api.database', () => {
  beforeEach(() => {
    vi.resetModules();
    global.fetch = vi.fn();
  });

  it('getStatus returns DatabaseStatus on success', async () => {
    const mockStatus = {
      configured: true,
      type: 'sqlite',
      connected: true,
      message: 'SQLite connected',
    };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: () => Promise.resolve(mockStatus),
    });

    const { api } = await import('$lib/api/client');
    const result = await api.database.getStatus();
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.type).toBe('sqlite');
      expect(result.data.connected).toBe(true);
    }
  });

  it('getStatus returns error on failure', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      headers: { get: () => 'application/json' },
      json: () => Promise.resolve({}),
    });

    const { api } = await import('$lib/api/client');
    const result = await api.database.getStatus();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBeTruthy();
    }
  });

  it('testSupabase sends credentials and returns result', async () => {
    const mockResult = { success: true, message: 'Connected', project_ref: 'abc' };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: () => Promise.resolve(mockResult),
    });

    const { api } = await import('$lib/api/client');
    const result = await api.database.testSupabase({
      project_url: 'https://test.supabase.co',
      service_key: 'sk_test_1234567890123456789012345678901234567890', // pragma: allowlist secret
      db_password: 'password', // pragma: allowlist secret
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.success).toBe(true);
    }
  });

  it('provisionSupabase sends credentials and returns result', async () => {
    const mockResult = { success: true, message: 'Provisioned', tables_created: ['voters'] };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: () => Promise.resolve(mockResult),
    });

    const { api } = await import('$lib/api/client');
    const result = await api.database.provisionSupabase({
      project_url: 'https://test.supabase.co',
      service_key: 'sk_test_1234567890123456789012345678901234567890', // pragma: allowlist secret
      db_password: 'password', // pragma: allowlist secret
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.tables_created).toContain('voters');
    }
  });

  it('disconnectSupabase sends DELETE and returns result', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: () => Promise.resolve({ success: true }),
    });

    const { api } = await import('$lib/api/client');
    const result = await api.database.disconnectSupabase();
    expect(result.ok).toBe(true);

    expect((global.fetch as ReturnType<typeof vi.fn>)).toHaveBeenCalledWith(
      expect.stringContaining('/database/supabase'),
      expect.objectContaining({ method: 'DELETE' }),
    );
  });
});
```

### Step 4: Run tests (GREEN phase)

```bash
cd frontend-svelt && bun run test:unit -- tests/unit/api/database.test.ts
```

### Step 5: Commit

```bash
git add frontend-svelt/src/lib/api/database-types.ts \
        frontend-svelt/src/lib/api/client.ts \
        frontend-svelt/tests/unit/api/database.test.ts
git commit -m "feat(frontend): add database API client types, methods, and tests"
```

---

## Task Group 3B: Onboarding Components

**Files:**
- Create: `frontend-svelt/src/lib/components/onboarding/DatabaseSelector.svelte`
- Create: `frontend-svelt/src/lib/components/onboarding/SupabaseConnectForm.svelte`
- Create: `frontend-svelt/src/lib/components/onboarding/OnboardingWizard.svelte`
- Create: `frontend-svelt/src/lib/components/onboarding/index.ts`

### Step 1: Create DatabaseSelector component

```svelte
<!-- frontend-svelt/src/lib/components/onboarding/DatabaseSelector.svelte -->
<script lang="ts">
  import { cn } from '$lib/utils/cn';
  import type { DatabaseType } from '$lib/api/database-types';

  interface Props {
    onSelect: (type: DatabaseType) => void;
  }

  let { onSelect }: Props = $props();

  interface DatabaseOption {
    type: DatabaseType;
    label: string;
    description: string;
    icon: string;
  }

  const options: DatabaseOption[] = [
    {
      type: 'sqlite',
      label: 'SQLite',
      description: 'Local development database (no setup required)',
      icon: '🗄️',
    },
    {
      type: 'supabase',
      label: 'Supabase',
      description: 'Managed PostgreSQL with real-time features',
      icon: '⚡',
    },
    {
      type: 'postgres',
      label: 'PostgreSQL',
      description: 'Self-hosted PostgreSQL database',
      icon: '🐘',
    },
  ];

  let hovered = $state<DatabaseType | null>(null);
</script>

<div class="mx-auto max-w-lg">
  <h2 class="mb-1 text-center text-2xl font-semibold text-gray-900">
    Choose Your Database
  </h2>
  <p class="mb-8 text-center text-sm text-gray-500">
    Select how you want to store your data
  </p>

  <div class="flex flex-col gap-3">
    {#each options as option (option.type)}
      <button
        type="button"
        class={cn(
          'block w-full rounded-lg border-2 bg-white p-4 text-left transition-all',
          'hover:border-blue-500 hover:-translate-y-0.5 hover:shadow-sm',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          hovered === option.type && 'border-blue-500 shadow-sm',
        )}
        onmouseenter={() => (hovered = option.type)}
        onmouseleave={() => (hovered = null)}
        onclick={() => onSelect(option.type)}
      >
        <div class="flex items-center gap-3">
          <span class="text-2xl" aria-hidden="true">{option.icon}</span>
          <div>
            <h3 class="text-base font-semibold text-gray-900">{option.label}</h3>
            <p class="text-sm text-gray-500">{option.description}</p>
          </div>
        </div>
      </button>
    {/each}
  </div>
</div>
```

### Step 2: Create SupabaseConnectForm component

```svelte
<!-- frontend-svelt/src/lib/components/onboarding/SupabaseConnectForm.svelte -->
<script lang="ts">
  import { Button, Input } from '$lib/components/ui';
  import { api } from '$lib/api/client';
  import type { SupabaseCredentials, ConnectionTestResult, ProvisionResult } from '$lib/api/database-types';

  interface Props {
    onBack: () => void;
    onSuccess: () => void;
  }

  let { onBack, onSuccess }: Props = $props();

  let projectUrl = $state('');
  let serviceKey = $state('');
  let dbPassword = $state('');
  let testing = $state(false);
  let provisioning = $state(false);
  let error = $state('');
  let testResult = $state<ConnectionTestResult | null>(null);

  let isValid = $derived(
    projectUrl.startsWith('https://') &&
    serviceKey.length > 50 &&
    dbPassword.length > 0,
  );

  async function handleTest() {
    testing = true;
    error = '';
    testResult = null;

    const credentials: SupabaseCredentials = {
      project_url: projectUrl,
      service_key: serviceKey,
      db_password: dbPassword,
    };

    const result = await api.database.testSupabase(credentials);
    if (result.ok) {
      testResult = result.data;
    } else {
      error = result.error;
    }
    testing = false;
  }

  async function handleConnect() {
    provisioning = true;
    error = '';

    const credentials: SupabaseCredentials = {
      project_url: projectUrl,
      service_key: serviceKey,
      db_password: dbPassword,
    };

    const result = await api.database.provisionSupabase(credentials);
    if (result.ok && result.data.success) {
      onSuccess();
    } else {
      error = result.ok ? result.data.message : result.error;
    }
    provisioning = false;
  }
</script>

<div class="mx-auto max-w-lg">
  <h2 class="mb-6 text-center text-2xl font-semibold text-gray-900">
    Connect to Supabase
  </h2>

  <div class="space-y-4">
    <Input
      id="project-url"
      type="text"
      label="Project URL"
      placeholder="https://your-project.supabase.co"
      bind:value={projectUrl}
      helperText="Found in Project Settings > API"
      required
    />

    <div>
      <Input
        id="service-key"
        type="password"
        label="Service Role Key"
        placeholder="eyJhbGciOi..."
        bind:value={serviceKey}
        required
      />
      <p class="mt-1 rounded bg-amber-50 p-2 text-xs text-amber-700">
        This key grants full database access. Keep it secure!
      </p>
    </div>

    <Input
      id="db-password"
      type="password"
      label="Database Password"
      placeholder="Your database password"
      bind:value={dbPassword}
      helperText="Found in Project Settings > Database > Connection string"
      required
    />

    {#if error}
      <div class="rounded bg-red-50 p-3 text-sm text-red-700" role="alert">
        {error}
      </div>
    {/if}

    {#if testResult}
      <div
        class={cn(
          'rounded p-3 text-sm',
          testResult.success ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-700',
        )}
      >
        {testResult.message}
      </div>
    {/if}

    <div class="flex justify-end gap-2 pt-2">
      <Button variant="secondary" onclick={onBack} text="Back" />
      <Button
        variant="secondary"
        onclick={handleTest}
        disabled={!isValid || testing}
        loading={testing}
        text={testing ? 'Testing...' : 'Test Connection'}
      />
      <Button
        variant="primary"
        onclick={handleConnect}
        disabled={!isValid || provisioning}
        loading={provisioning}
        text={provisioning ? 'Connecting...' : 'Connect & Provision'}
      />
    </div>
  </div>
</div>
```

> **Note:** Uses `type="text"` for Project URL because `Input.svelte` doesn't support `type="url"` yet. Add `url` to the type union in `Input.svelte` as a follow-up (see Task Group 3B exit gate checklist).

### Step 3: Create OnboardingWizard component

```svelte
<!-- frontend-svelt/src/lib/components/onboarding/OnboardingWizard.svelte -->
<script lang="ts">
  import type { DatabaseType } from '$lib/api/database-types';
  import DatabaseSelector from './DatabaseSelector.svelte';
  import SupabaseConnectForm from './SupabaseConnectForm.svelte';
  import { Button } from '$lib/components/ui';

  interface Props {
    onComplete: () => void;
  }

  let { onComplete }: Props = $props();

  type Step = 'select' | 'supabase' | 'postgres' | 'complete';
  let step = $state<Step>('select');

  function handleSelect(type: DatabaseType) {
    if (type === 'supabase') {
      step = 'supabase';
    } else if (type === 'postgres') {
      step = 'postgres';
    } else {
      step = 'complete';
      onComplete();
    }
  }

  function handleBack() {
    step = 'select';
  }
</script>

<div class="flex min-h-screen items-center justify-center p-6">
  {#if step === 'select'}
    <DatabaseSelector onSelect={handleSelect} />
  {:else if step === 'supabase'}
    <SupabaseConnectForm onBack={handleBack} onSuccess={onComplete} />
  {:else if step === 'postgres'}
    <div class="mx-auto max-w-sm text-center">
      <h2 class="mb-2 text-xl font-semibold text-gray-900">PostgreSQL Setup</h2>
      <p class="mb-6 text-sm text-gray-500">Self-hosted PostgreSQL setup coming soon.</p>
      <Button variant="secondary" onclick={handleBack} text="Back" />
    </div>
  {/if}
</div>
```

### Step 4: Create barrel export

```typescript
// frontend-svelt/src/lib/components/onboarding/index.ts
export { default as DatabaseSelector } from './DatabaseSelector.svelte';
export { default as SupabaseConnectForm } from './SupabaseConnectForm.svelte';
export { default as OnboardingWizard } from './OnboardingWizard.svelte';
```

### Step 5: Preview for user feedback

**DO NOT commit until user approves the visual design.**

Spin up a temporary preview page so the user can see and comment on:

1. **DatabaseSelector** — Run `bun run dev` and create a scratch route at `/test/onboarding` that renders `DatabaseSelector` in isolation. Ask user:
   - Vertical card list vs horizontal grid?
   - Icon choices (currently emoji — want SVG icons instead)?
   - Spacing and hover animation feel?

2. **SupabaseConnectForm** — Add to the same scratch route behind a toggle. Ask user:
   - Form field order preference
   - Warning style for service key field (amber callout vs red banner)
   - Button layout (Back/Test/Connect order)

3. **Responsive check** — Ask user to resize to 375px mobile width. Does it still work?

**Commands:**
```bash
cd frontend-svelt && bun run dev
# Create: src/routes/test/onboarding/+page.svelte (scratch, not committed)
# Open: http://localhost:5173/test/onboarding
```

**After user approves, delete the scratch route and proceed to commit.**

### Step 6: Commit

```bash
rm -rf frontend-svelt/src/routes/test/
git add frontend-svelt/src/lib/components/onboarding/
git commit -m "feat(frontend): add onboarding wizard components (Svelte 5 + Tailwind)"
```

---

## Task Group 3C: Onboarding Route & First-Run Guard

**Routing Architecture:**

The original plan's approach of modifying the root `+layout.svelte` to redirect unconfigured users would cause a redirect loop (the onboarding page itself is a child of root layout). Instead, we use SvelteKit's route groups:

```
src/routes/
├── +layout.svelte              ← Root layout (minimal: feature flags, favicon)
├── (app)/
│   ├── +layout.svelte          ← App shell (Navbar, first-run guard)
│   ├── +page.svelte            ← Home page
│   ├── getting-started/        ← Existing onboarding
│   ├── workspace/              ← Existing workspace
│   └── settings/               ← New database settings
└── (standalone)/
    └── setup/
        ├── +layout.svelte      ← Bare layout (no Navbar)
        └── +page.svelte        ← Database onboarding wizard
```

**Files:**
- Create: `frontend-svelt/src/routes/(standalone)/setup/+layout.svelte`
- Create: `frontend-svelt/src/routes/(standalone)/setup/+page.svelte`
- Create: `frontend-svelt/src/routes/(app)/+layout.svelte`
- Move existing routes under `(app)/` group
- Create: `frontend-svelt/src/routes/(app)/+layout.svelte`

### Step 1: Create standalone setup layout

```svelte
<!-- frontend-svelt/src/routes/(standalone)/setup/+layout.svelte -->
<script lang="ts">
  let { children } = $props();
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-red-50">
  <div class="flex items-center justify-center p-8">
    <h1 class="text-2xl font-bold text-slate-900">VoteCatcher ✓</h1>
  </div>
  {@render children()}
</div>
```

### Step 2: Create setup page

```svelte
<!-- frontend-svelt/src/routes/(standalone)/setup/+page.svelte -->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { OnboardingWizard } from '$lib/components/onboarding';

  function handleComplete() {
    goto('/');
  }
</script>

<svelte:head>
  <title>Database Setup — Votecatcher</title>
</svelte:head>

<OnboardingWizard onComplete={handleComplete} />
```

### Step 3: Create app layout with first-run guard

```svelte
<!-- frontend-svelt/src/routes/(app)/+layout.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto, page } from '$app/stores';
  import { get } from 'svelte/store';
  import { api } from '$lib/api/client';
  import { Navbar } from '$lib/components/layout';
  import { LoadingSpinner } from '$lib/components/ui';

  let { children } = $props();

  let checking = $state(true);

  onMount(async () => {
    const result = await api.database.getStatus();
    checking = false;

    if (result.ok && !result.data.configured) {
      const currentPath = get(page).url.pathname;
      if (!currentPath.startsWith('/setup')) {
        goto('/setup');
      }
    }
  });
</script>

{#if checking}
  <div class="flex min-h-screen items-center justify-center">
    <LoadingSpinner />
  </div>
{:else}
  <Navbar user={null} />
  <main>
    {@render children()}
  </main>
{/if}
```

### Step 4: Move existing routes under (app) group

Move the following existing routes into the `(app)` directory:

```bash
# Move routes that should have the app shell (Navbar, first-run guard)
mv src/routes/+page.svelte              src/routes/(app)/+page.svelte
mv src/routes/getting-started/          src/routes/(app)/getting-started/
mv src/routes/workspace/                src/routes/(app)/workspace/
mv src/routes/auth/                     src/routes/(app)/auth/
mv src/routes/demo/                     src/routes/(app)/demo/
mv src/routes/test-match-confidence/    src/routes/(app)/test-match-confidence/
```

> **Warning:** This is the most disruptive step. Run `bun run check` immediately after to catch any broken imports. The `(app)` group is invisible in URLs — `/workspace` stays `/workspace`.

### Step 5: Preview for user feedback

**DO NOT commit until user approves the flow.**

```bash
cd frontend-svelt && bun run dev
# Navigate to: http://localhost:5173/setup
```

Ask user to walk through the full flow and confirm:

- [ ] Does `/setup` render the wizard without the Navbar (standalone layout)?
- [ ] Does selecting SQLite redirect immediately to `/`?
- [ ] Does the first-run guard redirect to `/setup` when DB is unconfigured?
- [ ] Does the app layout (Navbar) appear on normal routes like `/workspace`?
- [ ] Are existing routes (`/getting-started`, `/workspace`) unaffected by the move to `(app)`?

### Step 6: Commit

```bash
git add frontend-svelt/src/routes/
git commit -m "feat(frontend): add setup route with first-run guard using route groups"
```

---

## Task Group 3D: Settings Page

**Files:**
- Create: `frontend-svelt/src/routes/(app)/settings/database/+page.svelte`

### Step 1: Create database settings page

```svelte
<!-- frontend-svelt/src/routes/(app)/settings/database/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { Button, LoadingState, ErrorDisplay } from '$lib/components/ui';
  import type { DatabaseStatus } from '$lib/api/database-types';

  let status = $state<DatabaseStatus | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let disconnecting = $state(false);

  onMount(loadStatus);

  async function loadStatus() {
    loading = true;
    error = null;
    const result = await api.database.getStatus();
    if (result.ok) {
      status = result.data;
    } else {
      error = result.error;
    }
    loading = false;
  }

  async function handleDisconnect() {
    if (!confirm('Are you sure? This will remove Supabase configuration and return to SQLite.')) {
      return;
    }

    disconnecting = true;
    const result = await api.database.disconnectSupabase();
    if (result.ok) {
      await loadStatus();
    } else {
      error = result.error;
    }
    disconnecting = false;
  }
</script>

<svelte:head>
  <title>Database Settings — Votecatcher</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-8">
  <h1 class="mb-6 text-2xl font-bold text-gray-900">Database Settings</h1>

  {#if loading}
    <LoadingState />
  {:else if error}
    <ErrorDisplay message={error} />
  {:else if status}
    <div class="rounded-lg border border-gray-200 bg-white p-6">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-gray-900">{status.type.toUpperCase()}</h2>
        <span
          class={cn(
            'rounded-full px-3 py-0.5 text-xs font-medium',
            status.connected
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-600',
          )}
        >
          {status.connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      <p class="text-sm text-gray-500">{status.message}</p>

      {#if status.type === 'supabase'}
        <div class="mt-6 border-t border-gray-200 pt-4">
          <Button
            variant="danger"
            onclick={handleDisconnect}
            disabled={disconnecting}
            loading={disconnecting}
            text={disconnecting ? 'Disconnecting...' : 'Disconnect Supabase'}
          />
        </div>
      {/if}
    </div>
  {/if}
</div>
```

> **Note:** The `cn` import is needed for the badge class — add `import { cn } from '$lib/utils/cn';` to the script block.

### Step 2: Preview for user feedback

**DO NOT commit until user approves the visual design.**

Add a scratch route `/test/settings` that renders the settings page with mock data. Ask user:

- **Badge style**: Green/gray for connected/disconnected, or green/amber/red tri-state?
- **Card layout**: Compact badge-in-header (current) vs full-width with separate sections?
- **Disconnect button placement**: Bottom of card vs top-right corner?
- **Overall spacing**: Too cramped / too spacious / just right?

```bash
cd frontend-svelt && bun run dev
# Create: src/routes/test/settings/+page.svelte (scratch, not committed)
# Open: http://localhost:5173/test/settings
```

**After user approves, delete the scratch route and proceed to commit.**

### Step 3: Commit

```bash
rm -rf frontend-svelt/src/routes/test/
git add frontend-svelt/src/routes/\(app\)/settings/
git commit -m "feat(frontend): add database settings page"
```

---

## Phase 3 Exit Gate

### Automated Checks

```bash
# Type check
cd frontend-svelt && bun run check

# Lint
cd frontend-svelt && bun run lint

# Unit tests (including new database API tests)
cd frontend-svelt && bun run test:unit

# Build
cd frontend-svelt && bun run build
```

**Expected Results:**
- [ ] `bun run check` — type check passes
- [ ] `bun run lint` — no lint errors
- [ ] `bun run test:unit` — all tests pass (including new `tests/unit/api/database.test.ts`)
- [ ] `bun run build` — build succeeds

### Manual Testing

- [ ] Navigate to `/setup` — wizard renders with 3 database options
- [ ] Click "SQLite" — redirects to home page immediately
- [ ] Click "Supabase" — shows connection form
- [ ] Form validation: "Test Connection" / "Connect & Provision" disabled until all fields filled
- [ ] Click "Back" — returns to database selector
- [ ] Navigate to `/settings/database` — shows database status card
- [ ] With unconfigured database, visiting `/` redirects to `/setup`

### Accessibility Checklist

- [ ] All buttons have visible focus indicators (Tailwind `focus:ring`)
- [ ] Form inputs have associated labels
- [ ] Error messages use `role="alert"`
- [ ] Keyboard navigation works (Tab through form, Enter to submit)
- [ ] Color contrast meets WCAG AA (Tailwind defaults pass)

---

## Reviewer Section

**Reviewer:** ___________________

**Date:** ___________________

**Status:** [ ] Approved [ ] Needs Changes

**Feedback:**

| Task Group | Issues | Resolution |
|------------|--------|------------|
| 3A: Types & API Client | | |
| 3B: Onboarding Components | | |
| 3C: Onboarding Route | | |
| 3D: Settings Page | | |

**Blocking issues:**

-

**Suggestions for improvement:**

-

---

## Next Phase

Once this phase passes the exit gate and reviewer approval, the backend API (Phase 4) should be complete for full integration testing.
