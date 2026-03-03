# Feature Flag System - Design Document

**Date:** 2026-03-02
**Status:** Proposed
**Author:** Agent + User

## Overview

Implement a robust feature flag system that combines server-side configuration with client-side persistence and overrides. This provides environment-specific control while maintaining fast, offline-capable frontend access.

## Goals

1. Centralized feature flag management (backend + frontend)
2. Environment-specific configuration (dev/staging/prod)
3. Persistent user preferences (localStorage)
4. Type-safe flag access (TypeScript + Python)
5. Easy to add new flags
6. Developer-friendly UI for toggling (dev mode only)

## Architecture

### Data Flow

```
Environment Variables (Backend)
        │
        ▼
    Settings (Pydantic)
        │
        ▼
  /api/config/features
        │
        ├─────────────────┐
        │                 │
        ▼                 ▼
  Server Control    Client Fetch
                             │
                             ▼
                      Merge with localStorage
                             │
                             ▼
                    Feature Flag Store
                             │
                             ▼
                       Components
```

### Flag Precedence

1. **localStorage override** (highest priority) - User toggled in UI
2. **Server config** - From /api/config/features
3. **Default values** (lowest priority) - Hardcoded defaults

### Persistence Strategy

- **Server config**: Cached in memory, refreshed on page load
- **User overrides**: Persisted in localStorage under `featureFlags_overrides`
- **Merge strategy**: Override server defaults with user preferences

## Implementation

### Backend: Settings + Endpoint

**File:** `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class FeatureFlags(BaseSettings):
    """Feature flags controlled by environment variables."""
    
    # Feature: OCR Simulation Mode
    # Description: Use mock data instead of real OCR/matching
    # Default: false in prod, true in dev
    enable_simulation: bool = False
    
    # Feature: Beta Features
    # Description: Enable experimental features
    # Default: false
    enable_beta_features: bool = False
    
    # Feature: Debug Mode
    # Description: Show additional debug information
    # Default: false
    enable_debug_mode: bool = False
    
    class Config:
        env_file = ".env.local"
        env_prefix = "FEATURE_"

@lru_cache()
def get_feature_flags() -> FeatureFlags:
    """Cached feature flags instance."""
    return FeatureFlags()
```

**File:** `backend/app/routers/config_route.py` (new file)

```python
from fastapi import APIRouter
from app.config import get_feature_flags

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/features")
async def get_feature_config():
    """
    Get feature flag configuration.
    
    Returns server-side feature flags that can be overridden
    by client-side localStorage preferences.
    """
    flags = get_feature_flags()
    return {
        "simulationMode": flags.enable_simulation,
        "betaFeatures": flags.enable_beta_features,
        "debugMode": flags.enable_debug_mode,
    }
```

**File:** `backend/.env.local`

```env
# Feature Flags
FEATURE_ENABLE_SIMULATION=false
FEATURE_ENABLE_BETA_FEATURES=false
FEATURE_ENABLE_DEBUG_MODE=false
```

**File:** `backend/.env.dev` (example)

```env
# Feature Flags - Development
FEATURE_ENABLE_SIMULATION=true
FEATURE_ENABLE_BETA_FEATURES=true
FEATURE_ENABLE_DEBUG_MODE=true
```

### Frontend: Feature Flag Store

**File:** `frontend-svelt/src/lib/stores/featureFlags.ts` (new file)

```typescript
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { api } from '$lib/api/client';

/**
 * Feature flag configuration from server
 */
export interface FeatureFlags {
  simulationMode: boolean;
  betaFeatures: boolean;
  debugMode: boolean;
}

/**
 * Feature flag overrides (user preferences)
 */
interface FeatureFlagOverrides {
  [key: string]: boolean | undefined;
}

const DEFAULT_FLAGS: FeatureFlags = {
  simulationMode: false,
  betaFeatures: false,
  debugMode: false,
};

const STORAGE_KEY = 'featureFlags_overrides';

/**
 * Load user overrides from localStorage
 */
function loadOverrides(): FeatureFlagOverrides {
  if (!browser) return {};
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

/**
 * Save user overrides to localStorage
 */
function saveOverrides(overrides: FeatureFlagOverrides): void {
  if (!browser) return;
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(overrides));
  } catch (error) {
    console.error('Failed to save feature flag overrides:', error);
  }
}

/**
 * Merge server config with user overrides
 */
function mergeFlags(
  serverFlags: FeatureFlags,
  overrides: FeatureFlagOverrides
): FeatureFlags {
  return {
    simulationMode: overrides.simulationMode ?? serverFlags.simulationMode,
    betaFeatures: overrides.betaFeatures ?? serverFlags.betaFeatures,
    debugMode: overrides.debugMode ?? serverFlags.debugMode,
  };
}

/**
 * Create the feature flag store
 */
function createFeatureFlagStore() {
  // Initialize with defaults
  const { subscribe, set, update } = writable<FeatureFlags>(DEFAULT_FLAGS);
  
  // Track overrides separately
  let overrides: FeatureFlagOverrides = loadOverrides();
  
  // Track server config
  let serverFlags: FeatureFlags = DEFAULT_FLAGS;
  
  return {
    subscribe,
    
    /**
     * Load feature flags from server and merge with overrides
     */
    async load(): Promise<void> {
      try {
        const response = await fetch('/api/config/features');
        if (response.ok) {
          serverFlags = await response.json();
          const merged = mergeFlags(serverFlags, overrides);
          set(merged);
        }
      } catch (error) {
        console.error('Failed to load feature flags:', error);
        // Fall back to defaults + overrides
        set(mergeFlags(DEFAULT_FLAGS, overrides));
      }
    },
    
    /**
     * Toggle a feature flag (sets override)
     */
    toggle(flag: keyof FeatureFlags): void {
      update(current => {
        const newValue = !current[flag];
        overrides[flag] = newValue;
        saveOverrides(overrides);
        return { ...current, [flag]: newValue };
      });
    },
    
    /**
     * Set a feature flag value (sets override)
     */
    setFlag(flag: keyof FeatureFlags, value: boolean): void {
      update(current => {
        overrides[flag] = value;
        saveOverrides(overrides);
        return { ...current, [flag]: value };
      });
    },
    
    /**
     * Reset a specific flag to server default
     */
    reset(flag: keyof FeatureFlags): void {
      update(current => {
        delete overrides[flag];
        saveOverrides(overrides);
        return { ...current, [flag]: serverFlags[flag] };
      });
    },
    
    /**
     * Reset all flags to server defaults
     */
    resetAll(): void {
      overrides = {};
      saveOverrides(overrides);
      set(serverFlags);
    },
    
    /**
     * Get current overrides (for debugging)
     */
    getOverrides(): FeatureFlagOverrides {
      return { ...overrides };
    },
    
    /**
     * Get server defaults (for debugging)
     */
    getServerFlags(): FeatureFlags {
      return { ...serverFlags };
    },
  };
}

export const featureFlags = createFeatureFlagStore();

/**
 * Derived store: Check if any flags are overridden
 */
export const hasOverrides = derived(
  featureFlags,
  ($flags, set) => {
    const overrides = loadOverrides();
    set(Object.keys(overrides).length > 0);
  }
);
```

### Frontend: Feature Flag Panel (Dev Mode)

**File:** `frontend-svelt/src/lib/components/FeatureFlagsPanel.svelte` (new file)

```svelte
<script lang="ts">
  import { featureFlags, hasOverrides } from '$lib/stores/featureFlags';
  import { cn } from '$lib/utils/cn';

  interface Props {
    class?: string;
  }

  let { class: className }: Props = $props();

  const flagDescriptions: Record<keyof typeof $featureFlags, string> = {
    simulationMode: 'Use mock data instead of real OCR/matching',
    betaFeatures: 'Enable experimental features',
    debugMode: 'Show additional debug information',
  };
</script>

<div class={cn("rounded-lg border bg-card p-4", className)}>
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold">Feature Flags</h3>
    {#if $hasOverrides}
      <button
        type="button"
        onclick={() => featureFlags.resetAll()}
        class="text-sm text-muted-foreground hover:text-foreground underline"
      >
        Reset All
      </button>
    {/if}
  </div>

  <div class="space-y-3">
    {#each Object.entries($featureFlags) as [flag, value]}
      {@type flag = flag as keyof typeof $featureFlags}
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value}
              onchange={() => featureFlags.toggle(flag)}
              class="h-4 w-4 rounded border-input"
            />
            <span class="font-medium">{flag}</span>
          </label>
          <p class="text-sm text-muted-foreground ml-6">
            {flagDescriptions[flag]}
          </p>
        </div>
        
        <button
          type="button"
          onclick={() => featureFlags.reset(flag)}
          class="text-xs text-muted-foreground hover:text-foreground"
          title="Reset to server default"
        >
          reset
        </button>
      </div>
    {/each}
  </div>

  {#if $hasOverrides}
    <div class="mt-4 pt-4 border-t">
      <p class="text-xs text-muted-foreground">
        ⚠️ Some flags are overridden. Changes are persisted in localStorage.
      </p>
    </div>
  {/if}
</div>
```

### Frontend: Initialize on App Load

**File:** `frontend-svelt/src/routes/+layout.svelte`

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { featureFlags } from '$lib/stores/featureFlags';
  import '../lib/styles/tokens.css';

  onMount(() => {
    // Load feature flags from server
    featureFlags.load();
  });
</script>

<slot />
```

### Frontend: Migration

**File:** `frontend-svelt/src/routes/workspace/[id]/+page.svelte`

```svelte
<script lang="ts">
  import { featureFlags } from '$lib/stores/featureFlags';
  
  // OLD: let useSimulation = $state(false);
  // NEW: Use feature flag store
  $: useSimulation = $featureFlags.simulationMode;
  
  async function fetchResultsWithSimulation(jobId: string) {
    let res;
    if (useSimulation) {
      res = await api.simulateOcrResults(jobId);
    } else {
      res = await matchApi.getMatchResults({
        campaign_id: "demo",
        job_id: jobId
      });
    }
    
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    matchResults = convertMatchResponseToMatchResults(res.data);
  }
</script>

<!-- In template -->
<label class="flex items-center gap-2 text-sm">
  <input
    type="checkbox"
    checked={useSimulation}
    onchange={() => featureFlags.toggle('simulationMode')}
    class="h-4 w-4 rounded border-input"
  />
  Use Simulated Data
</label>
```

## Usage Examples

### Adding a New Feature Flag

1. **Backend:** Add to `config.py`:
```python
class FeatureFlags(BaseSettings):
    # ... existing flags
    enable_new_feature: bool = False
```

2. **Backend:** Add to `/api/config/features` response:
```python
return {
    # ... existing flags
    "newFeature": flags.enable_new_feature,
}
```

3. **Frontend:** Add to TypeScript interface:
```typescript
export interface FeatureFlags {
  // ... existing flags
  newFeature: boolean;
}
```

4. **Frontend:** Add to defaults:
```typescript
const DEFAULT_FLAGS: FeatureFlags = {
  // ... existing flags
  newFeature: false,
};
```

5. **Frontend:** Use in component:
```svelte
<script>
  import { featureFlags } from '$lib/stores/featureFlags';
</script>

{#if $featureFlags.newFeature}
  <NewFeature />
{/if}
```

### Conditional Feature Based on Flag

```svelte
<script>
  import { featureFlags } from '$lib/stores/featureFlags';
  
  async function fetchData() {
    const endpoint = $featureFlags.simulationMode 
      ? '/api/simulate/data' 
      : '/api/real/data';
    // ...
  }
</script>
```

## Testing Strategy

### Backend Tests

**File:** `backend/tests/test_config.py`

```python
import pytest
from app.config import FeatureFlags

def test_feature_flags_defaults():
    """Test default feature flag values."""
    flags = FeatureFlags()
    assert flags.enable_simulation is False
    assert flags.enable_beta_features is False
    assert flags.enable_debug_mode is False

def test_feature_flags_from_env(monkeypatch):
    """Test loading feature flags from environment."""
    monkeypatch.setenv("FEATURE_ENABLE_SIMULATION", "true")
    flags = FeatureFlags()
    assert flags.enable_simulation is True
```

### Frontend Tests

**File:** `frontend-svelt/src/lib/stores/featureFlags.test.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { featureFlags } from './featureFlags';

describe('featureFlags', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('loads default flags', () => {
    const flags = get(featureFlags);
    expect(flags.simulationMode).toBe(false);
  });

  it('toggles flags', () => {
    featureFlags.toggle('simulationMode');
    const flags = get(featureFlags);
    expect(flags.simulationMode).toBe(true);
  });

  it('persists overrides to localStorage', () => {
    featureFlags.toggle('simulationMode');
    const stored = localStorage.getItem('featureFlags_overrides');
    expect(stored).toContain('"simulationMode":true');
  });

  it('resets flags', () => {
    featureFlags.toggle('simulationMode');
    featureFlags.reset('simulationMode');
    const flags = get(featureFlags);
    expect(flags.simulationMode).toBe(false);
  });
});
```

## Security Considerations

1. **Server-side validation:** Always validate feature flags on backend for sensitive operations
2. **No sensitive data:** Don't expose secrets via `/api/config/features`
3. **Environment isolation:** Different .env files for dev/staging/prod
4. **User permissions:** Consider user roles for flag visibility (future enhancement)

## Future Enhancements

1. **User-specific flags:** Store overrides per user in database
2. **A/B testing:** Track flag usage and conversion metrics
3. **Gradual rollout:** Percentage-based flag rollout
4. **Flag expiration:** Auto-disable flags after certain date
5. **Audit logging:** Track when flags are changed

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| 1 | Backend feature flags load from env | `FEATURE_ENABLE_SIMULATION=true uv run main.py` |
| 2 | `/api/config/features` returns correct flags | `curl http://localhost:8080/api/config/features` |
| 3 | Frontend loads flags on app start | Check network tab, localStorage |
| 4 | Toggle persists across page reloads | Toggle flag, reload, verify persisted |
| 5 | Reset clears localStorage override | Toggle, reset, verify cleared |
| 6 | FeatureFlagsPanel shows all flags | Add to dev mode page, verify UI |
| 7 | simulationMode controls API endpoint | Toggle, verify correct endpoint called |
| 8 | Type safety enforced | TypeScript catches invalid flag names |

## Documentation Updates

Update `docs/running-locally.md`:

```markdown
## Feature Flags

Feature flags control which features are enabled. They can be configured via:

### Server-Side (Environment Variables)

Set in `.env.local`:

```env
FEATURE_ENABLE_SIMULATION=true
FEATURE_ENABLE_BETA_FEATURES=false
FEATURE_ENABLE_DEBUG_MODE=true
```

### Client-Side (localStorage)

Users can override server defaults via the Feature Flags panel (dev mode only).

Overrides are stored in `localStorage.featureFlags_overrides`.

### Available Flags

| Flag | Description | Default |
|------|-------------|---------|
| `simulationMode` | Use mock data instead of real OCR | `false` |
| `betaFeatures` | Enable experimental features | `false` |
| `debugMode` | Show debug information | `false` |
```

---

## Summary

**Implementation Time:** ~2-3 hours

**Files Created:**
- `backend/app/config.py` (modify)
- `backend/app/routers/config_route.py` (create)
- `frontend-svelt/src/lib/stores/featureFlags.ts` (create)
- `frontend-svelt/src/lib/components/FeatureFlagsPanel.svelte` (create)

**Files Modified:**
- `backend/app/api.py` (add config router)
- `backend/.env.local` (add flags)
- `frontend-svelt/src/routes/+layout.svelte` (load flags)
- `frontend-svelt/src/routes/workspace/[id]/+page.svelte` (use flags)

**Benefits:**
- ✅ Centralized feature flag management
- ✅ Environment-specific configuration
- ✅ Persistent user preferences
- ✅ Type-safe flag access
- ✅ Easy to extend
- ✅ Developer-friendly UI
