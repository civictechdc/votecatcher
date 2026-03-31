# Phase 3: Frontend Onboarding Wizard

> **⚠️ SUPERSEDED:** This plan uses Svelte 4 syntax and CSS variables incompatible with the actual codebase. Use **[03-frontend-onboarding-v2.md](./03-frontend-onboarding-v2.md)** instead — it corrects all issues and follows the project's Svelte 5 + Tailwind conventions.
>
> This document is kept for reference only.

> **Prerequisite:** Phase 2 complete (engine selection works)

**Goal:** Create Svelte onboarding wizard with database selector and Supabase connection form.

**Duration Estimate:** 6-8 hours

---

## Phase Status

| Task Group | Status | Exit Gate |
|------------|--------|-----------|
| 3A: API Client | Not Started | API calls work |
| 3B: Onboarding Components | Not Started | Components render |
| 3C: Onboarding Flow | Not Started | Full flow works |
| 3D: Settings Page | Not Started | Settings persist |

---

## Developer Notes

| Date | Status | Notes/Blockers/Concerns |
|------|--------|-------------------------|
| | Not Started | |

---

## Entrance Gate

Verify Phase 2 is complete:

```bash
cd backend && uv run pytest tests/unit/persistence/ tests/integration/test_engine_selection.py -v
```

**Expected:** All tests pass

---

## Task Group 3A: API Client for Database Operations

**Files:**
- Create: `frontend-svelt/src/lib/api/database.ts`
- Create: `frontend-svelt/src/lib/types/database.ts`

### Step 1: Define TypeScript types

```typescript
// frontend-svelt/src/lib/types/database.ts

export interface DatabaseStatus {
  configured: boolean;
  type: 'sqlite' | 'postgres' | 'supabase';
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

### Step 2: Create API client

```typescript
// frontend-svelt/src/lib/api/database.ts

import { API_BASE_URL } from './config';
import type {
  DatabaseStatus,
  SupabaseCredentials,
  ConnectionTestResult,
  ProvisionResult
} from '$lib/types/database';

export async function getDatabaseStatus(): Promise<DatabaseStatus> {
  const response = await fetch(`${API_BASE_URL}/database/status`);
  if (!response.ok) {
    throw new Error('Failed to get database status');
  }
  return response.json();
}

export async function testSupabaseConnection(
  credentials: SupabaseCredentials
): Promise<ConnectionTestResult> {
  const response = await fetch(`${API_BASE_URL}/database/supabase/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Connection test failed');
  }
  return response.json();
}

export async function provisionSupabase(
  credentials: SupabaseCredentials
): Promise<ProvisionResult> {
  const response = await fetch(`${API_BASE_URL}/database/supabase/provision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Provisioning failed');
  }
  return response.json();
}

export async function disconnectSupabase(): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/database/supabase`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to disconnect Supabase');
  }
  return response.json();
}
```

### Step 3: Commit

```bash
git add frontend-svelt/src/lib/api/database.ts frontend-svelt/src/lib/types/database.ts
git commit -m "feat(frontend): add database API client types and methods"
```

---

## Task Group 3B: Onboarding Components

**Files:**
- Create: `frontend-svelt/src/lib/components/onboarding/DatabaseSelector.svelte`
- Create: `frontend-svelt/src/lib/components/onboarding/SupabaseConnectForm.svelte`
- Create: `frontend-svelt/src/lib/components/onboarding/OnboardingWizard.svelte`

### Step 1: Create DatabaseSelector component

```svelte
<!-- frontend-svelt/src/lib/components/onboarding/DatabaseSelector.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export type DatabaseType = 'sqlite' | 'supabase' | 'postgres';

  const dispatch = createEventDispatcher<{
    select: DatabaseType;
  }>();

  const options: { type: DatabaseType; label: string; description: string }[] = [
    {
      type: 'sqlite',
      label: 'SQLite',
      description: 'Local development database (no setup required)'
    },
    {
      type: 'supabase',
      label: 'Supabase',
      description: 'Managed PostgreSQL with real-time features'
    },
    {
      type: 'postgres',
      label: 'PostgreSQL',
      description: 'Self-hosted PostgreSQL database'
    },
  ];
</script>

<div class="database-selector">
  <h2>Choose Your Database</h2>
  <p class="subtitle">Select how you want to store your data</p>

  <div class="options">
    {#each options as option}
      <button
        class="option-card"
        on:click={() => dispatch('select', option.type)}
      >
        <h3>{option.label}</h3>
        <p>{option.description}</p>
      </button>
    {/each}
  </div>
</div>

<style>
  .database-selector {
    max-width: 500px;
    margin: 0 auto;
  }

  h2 {
    text-align: center;
    margin-bottom: 0.5rem;
  }

  .subtitle {
    text-align: center;
    color: var(--text-muted);
    margin-bottom: 2rem;
  }

  .options {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .option-card {
    display: block;
    padding: 1.5rem;
    border: 2px solid var(--border-color);
    border-radius: 8px;
    background: var(--bg-secondary);
    cursor: pointer;
    text-align: left;
    transition: border-color 0.2s, transform 0.1s;
  }

  .option-card:hover {
    border-color: var(--primary-color);
    transform: translateY(-2px);
  }

  .option-card h3 {
    margin: 0 0 0.5rem;
    font-size: 1.2rem;
  }

  .option-card p {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.9rem;
  }
</style>
```

### Step 2: Create SupabaseConnectForm component

```svelte
<!-- frontend-svelt/src/lib/components/onboarding/SupabaseConnectForm.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { SupabaseCredentials } from '$lib/types/database';
  import { testSupabaseConnection, provisionSupabase } from '$lib/api/database';

  const dispatch = createEventDispatcher<{
    back: void;
    success: void;
  }>();

  let projectUrl = '';
  let serviceKey = '';
  let dbPassword = '';
  let testing = false;
  let provisioning = false;
  let error = '';
  let testResult: { success: boolean; message: string } | null = null;

  async function handleTest() {
    testing = true;
    error = '';
    testResult = null;

    try {
      const credentials: SupabaseCredentials = {
        project_url: projectUrl,
        service_key: serviceKey,
        db_password: dbPassword,
      };
      testResult = await testSupabaseConnection(credentials);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Test failed';
    } finally {
      testing = false;
    }
  }

  async function handleConnect() {
    provisioning = true;
    error = '';

    try {
      const credentials: SupabaseCredentials = {
        project_url: projectUrl,
        service_key: serviceKey,
        db_password: dbPassword,
      };
      const result = await provisionSupabase(credentials);
      if (result.success) {
        dispatch('success');
      } else {
        error = result.message;
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Connection failed';
    } finally {
      provisioning = false;
    }
  }

  $: isValid = projectUrl.startsWith('https://') &&
               serviceKey.length > 50 &&
               dbPassword.length > 0;
</script>

<div class="supabase-form">
  <h2>Connect to Supabase</h2>

  <div class="form-group">
    <label for="project-url">Project URL</label>
    <input
      id="project-url"
      type="url"
      bind:value={projectUrl}
      placeholder="https://your-project.supabase.co"
    />
    <span class="hint">Found in Project Settings > API</span>
  </div>

  <div class="form-group">
    <label for="service-key">Service Role Key</label>
    <input
      id="service-key"
      type="password"
      bind:value={serviceKey}
      placeholder="sb_secret_..."
    />
    <span class="warning">
      ⚠️ This key grants full database access. Keep it secure!
    </span>
  </div>

  <div class="form-group">
    <label for="db-password">Database Password</label>
    <input
      id="db-password"
      type="password"
      bind:value={dbPassword}
      placeholder="Your database password"
    />
    <span class="hint">
      Found in Project Settings > Database > Connection string
    </span>
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if testResult}
    <div class="test-result" class:success={testResult.success}>
      {testResult.message}
    </div>
  {/if}

  <div class="actions">
    <button class="secondary" on:click={() => dispatch('back')}>
      Back
    </button>
    <button
      class="secondary"
      on:click={handleTest}
      disabled={!isValid || testing}
    >
      {testing ? 'Testing...' : 'Test Connection'}
    </button>
    <button
      class="primary"
      on:click={handleConnect}
      disabled={!isValid || provisioning}
    >
      {provisioning ? 'Connecting...' : 'Connect & Provision'}
    </button>
  </div>
</div>

<style>
  .supabase-form {
    max-width: 500px;
    margin: 0 auto;
  }

  h2 {
    text-align: center;
    margin-bottom: 1.5rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    font-weight: 500;
    margin-bottom: 0.5rem;
  }

  input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 1rem;
  }

  .hint {
    display: block;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
  }

  .warning {
    display: block;
    font-size: 0.85rem;
    color: var(--warning-color);
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: var(--warning-bg);
    border-radius: 4px;
  }

  .error {
    padding: 0.75rem;
    background: var(--error-bg);
    color: var(--error-color);
    border-radius: 4px;
    margin-bottom: 1rem;
  }

  .test-result {
    padding: 0.75rem;
    background: var(--bg-secondary);
    border-radius: 4px;
    margin-bottom: 1rem;
  }

  .test-result.success {
    background: var(--success-bg);
    color: var(--success-color);
  }

  .actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
  }

  button {
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .primary {
    background: var(--primary-color);
    color: white;
    border: none;
  }

  .secondary {
    background: transparent;
    border: 1px solid var(--border-color);
  }
</style>
```

### Step 3: Create OnboardingWizard component

```svelte
<!-- frontend-svelt/src/lib/components/onboarding/OnboardingWizard.svelte -->
<script lang="ts">
  import DatabaseSelector, { type DatabaseType } from './DatabaseSelector.svelte';
  import SupabaseConnectForm from './SupabaseConnectForm.svelte';

  export let onComplete: () => void = () => {};

  let step: 'select' | 'supabase' | 'postgres' | 'complete' = 'select';
  let selectedType: DatabaseType | null = null;

  function handleSelect(type: DatabaseType) {
    selectedType = type;
    if (type === 'supabase') {
      step = 'supabase';
    } else if (type === 'postgres') {
      step = 'postgres';
    } else {
      // SQLite - no additional setup needed
      step = 'complete';
      onComplete();
    }
  }

  function handleSupabaseSuccess() {
    step = 'complete';
    onComplete();
  }

  function handleBack() {
    step = 'select';
    selectedType = null;
  }
</script>

<div class="onboarding-wizard">
  {#if step === 'select'}
    <DatabaseSelector on:select={(e) => handleSelect(e.detail)} />
  {:else if step === 'supabase'}
    <SupabaseConnectForm
      on:back={handleBack}
      on:success={handleSupabaseSuccess}
    />
  {:else if step === 'postgres'}
    <!-- TODO: PostgreSQL form in future iteration -->
    <div class="coming-soon">
      <h2>PostgreSQL Setup</h2>
      <p>Self-hosted PostgreSQL setup coming soon.</p>
      <button on:click={handleBack}>Back</button>
    </div>
  {/if}
</div>

<style>
  .onboarding-wizard {
    padding: 2rem;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .coming-soon {
    text-align: center;
    max-width: 400px;
  }

  .coming-soon h2 {
    margin-bottom: 1rem;
  }

  .coming-soon p {
    color: var(--text-muted);
    margin-bottom: 2rem;
  }
</style>
```

### Step 4: Commit

```bash
git add frontend-svelt/src/lib/components/onboarding/
git commit -m "feat(frontend): add onboarding wizard components"
```

---

## Task Group 3C: Onboarding Route and Flow

**Files:**
- Create: `frontend-svelt/src/routes/onboarding/+page.svelte`
- Create: `frontend-svelt/src/routes/onboarding/+layout.svelte`
- Modify: `frontend-svelt/src/routes/+layout.svelte` (add first-run check)

### Step 1: Create onboarding page

```svelte
<!-- frontend-svelt/src/routes/onboarding/+page.svelte -->
<script lang="ts">
  import { goto } from '$app/navigation';
  import OnboardingWizard from '$lib/components/onboarding/OnboardingWizard.svelte';

  function handleComplete() {
    goto('/');
  }
</script>

<svelte:head>
  <title>Welcome - Votecatcher</title>
</svelte:head>

<div class="onboarding-page">
  <div class="logo">
    <h1>Votecatcher</h1>
  </div>

  <OnboardingWizard onComplete={handleComplete} />
</div>

<style>
  .onboarding-page {
    min-height: 100vh;
    background: var(--bg-primary);
  }

  .logo {
    text-align: center;
    padding: 2rem;
  }

  .logo h1 {
    font-size: 2rem;
    margin: 0;
  }
</style>
```

### Step 2: Add first-run check to layout

```svelte
<!-- frontend-svelt/src/routes/+layout.svelte (additions) -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getDatabaseStatus } from '$lib/api/database';

  let isInitialized = false;
  let checking = true;

  onMount(async () => {
    try {
      const status = await getDatabaseStatus();
      isInitialized = status.configured;

      if (!isInitialized) {
        goto('/onboarding');
      }
    } catch (e) {
      console.error('Failed to check database status:', e);
    } finally {
      checking = false;
    }
  });
</script>

{#if checking}
  <div class="loading">Loading...</div>
{:else}
  <slot />
{/if}
```

### Step 3: Commit

```bash
git add frontend-svelt/src/routes/onboarding/ frontend-svelt/src/routes/+layout.svelte
git commit -m "feat(frontend): add onboarding route with first-run check"
```

---

## Task Group 3D: Settings Page

**Files:**
- Create: `frontend-svelt/src/routes/settings/database/+page.svelte`

### Step 1: Create database settings page

```svelte
<!-- frontend-svelt/src/routes/settings/database/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import {
    getDatabaseStatus,
    disconnectSupabase
  } from '$lib/api/database';
  import type { DatabaseStatus } from '$lib/types/database';

  let status: DatabaseStatus | null = null;
  let loading = true;
  let disconnecting = false;

  onMount(async () => {
    await loadStatus();
  });

  async function loadStatus() {
    try {
      status = await getDatabaseStatus();
    } catch (e) {
      console.error('Failed to load status:', e);
    } finally {
      loading = false;
    }
  }

  async function handleDisconnect() {
    if (!confirm('Are you sure? This will remove Supabase configuration and return to SQLite.')) {
      return;
    }

    disconnecting = true;
    try {
      await disconnectSupabase();
      await loadStatus();
    } catch (e) {
      console.error('Failed to disconnect:', e);
    } finally {
      disconnecting = false;
    }
  }
</script>

<svelte:head>
  <title>Database Settings - Votecatcher</title>
</svelte:head>

<div class="database-settings">
  <h1>Database Settings</h1>

  {#if loading}
    <p>Loading...</p>
  {:else if status}
    <div class="status-card">
      <div class="status-header">
        <h2>{status.type.toUpperCase()}</h2>
        <span class="badge" class:connected={status.connected}>
          {status.connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      <p class="message">{status.message}</p>

      {#if status.type === 'supabase'}
        <div class="actions">
          <button
            class="danger"
            on:click={handleDisconnect}
            disabled={disconnecting}
          >
            {disconnecting ? 'Disconnecting...' : 'Disconnect Supabase'}
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .database-settings {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem;
  }

  h1 {
    margin-bottom: 2rem;
  }

  .status-card {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 1.5rem;
  }

  .status-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .status-header h2 {
    margin: 0;
    font-size: 1.2rem;
  }

  .badge {
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    background: var(--bg-tertiary);
  }

  .badge.connected {
    background: var(--success-bg);
    color: var(--success-color);
  }

  .message {
    color: var(--text-muted);
    margin-bottom: 1rem;
  }

  .actions {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
  }

  .danger {
    background: var(--error-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .danger:disabled {
    opacity: 0.5;
  }
</style>
```

### Step 2: Commit

```bash
git add frontend-svelt/src/routes/settings/
git commit -m "feat(frontend): add database settings page"
```

---

## Phase 3 Exit Gate

**Run validation:**

```bash
# Frontend type check
cd frontend-svelt && npm run check

# Frontend lint
cd frontend-svelt && npm run lint

# Build check
cd frontend-svelt && npm run build
```

**Expected Results:**
- [ ] Type check passes
- [ ] No lint errors
- [ ] Build succeeds

**Manual Testing:**
- [ ] Navigate to /onboarding
- [ ] DatabaseSelector renders with 3 options
- [ ] Selecting Supabase shows connect form
- [ ] Form validation works
- [ ] Settings page shows database status

---

## Reviewer Section

**Reviewer:** ___________________

**Date:** ___________________

**Status:** [ ] Approved [ ] Needs Changes

**Feedback:**

| Task Group | Issues | Resolution |
|------------|--------|------------|
| 3A | | |
| 3B | | |
| 3C | | |
| 3D | | |

**Blocking issues:**

-

**Suggestions for improvement:**

-

---

## Next Phase

Once this phase passes the exit gate and reviewer approval, the backend API (Phase 4) should be complete for full integration testing.
