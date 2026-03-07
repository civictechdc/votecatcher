# Debug Flag System Design

**Status:** Draft
**Created:** 2026-03-07
**Related Concern:** Simulation toggle UI placement bug

---

## Problem Statement

The "Use Simulated Data" checkbox is incorrectly placed in the workspace page — it only appears after match results exist, but users need to toggle it BEFORE running matching. Additionally, the project has two disconnected debug/feature flag systems:

1. **DevFlags.svelte** — MSW mock toggles (localStorage-based)
2. **FeatureFlagsPanel.svelte** — Feature flags (never imported/used)
3. **$featureFlags store** — Runtime toggles (connected to simulation mode)

This creates confusion and poor developer UX.

---

## Research Summary

### Best Practices for Small Teams

| Category | Recommended Approach |
|----------|---------------------|
| **Primary Toggle Mechanism** | Environment variables |
| **Client-side Toggles** | URL params + localStorage (layered) |
| **Discovery** | Keyboard shortcut + URL param |
| **Security** | Never trust client-side flags for security decisions |
| **Cleanup** | Remove flags after feature rollout |

### Security Checklist (OWASP-aligned)

- [ ] Never expose stack traces in production
- [ ] Never expose debug endpoints without authentication
- [ ] Never trust client-side flags for security decisions
- [ ] Use environment-based checks for sensitive features
- [ ] Log all debug access attempts in production
- [ ] Remove/disable debug routes in production builds
- [ ] Sanitize PII from debug output
- [ ] Use safe defaults (DEBUG=false in production)

---

## Recommended Architecture

### 1. Unified Flag Hierarchy

```text
Priority (highest to lowest):
1. URL params (?debug=true&simulation=true) — Immediate, shareable
2. localStorage overrides — Persistent across sessions
3. Server-provided defaults (via /api/config/features) — Team defaults
4. Environment variables — Build-time defaults
```

### 2. Frontend Components

#### A. Fix Simulation Toggle Placement

**Current (broken):**
```svelte
{#if matchResults && matchResults.matchRecords.length > 0}
    <label>Use Simulated Data</label>
{/if}
```

**Option 1 — Move outside condition:**
```svelte
<label class="flex items-center gap-2 text-sm">
    <input type="checkbox" bind:checked={$featureFlags.simulationMode} />
    Use Simulated Data
</label>

{#if matchResults && matchResults.matchRecords.length > 0}
    <!-- Results table -->
{/if}
```

**Option 2 — Add to sidebar before Run Matching:**
```svelte
<aside>
    <!-- Upload sections -->
    
    <div class="mt-4 p-3 bg-muted rounded">
        <label class="flex items-center gap-2">
            <input type="checkbox" bind:checked={$featureFlags.simulationMode} />
            Use Simulated Data
        </label>
        <p class="text-xs text-muted-foreground mt-1">
            Bypasses OCR and returns fake data for testing
        </p>
    </div>
    
    <button onclick={runMatching}>Run Matching</button>
</aside>
```

#### B. Consolidated Debug Panel

Create a single `DebugPanel.svelte` that replaces both `DevFlags.svelte` and `FeatureFlagsPanel.svelte`:

```svelte
<script lang="ts">
    import { featureFlags, hasOverrides } from '$lib/stores/featureFlags';
    import { onMount } from 'svelte';

    let visible = $state(false);
    let activeTab = $state<'flags' | 'mocks'>('flags');

    // Show only in dev mode or with ?debug=true
    onMount(() => {
        const urlDebug = new URLSearchParams(window.location.search).get('debug');
        visible = import.meta.env.DEV || urlDebug === 'true';
        
        // Keyboard shortcut: Ctrl+Shift+D
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                visible = !visible;
            }
        });
    });
</script>

{#if visible}
    <div class="fixed bottom-4 right-4 z-50 w-80 rounded-lg border bg-background shadow-lg">
        <!-- Tabs for Flags vs Mocks -->
        <!-- Feature flags section -->
        <!-- MSW mock toggles section -->
        <!-- Reset all button -->
    </div>
{/if}
```

### 3. Backend Debug Endpoints

#### Protected Debug Router

```python
# backend/app/debug/router.py
from fastapi import APIRouter, HTTPException, Request
from app.settings.env_settings import settings

router = APIRouter(prefix="/_debug", tags=["debug"])

def require_debug_mode(request: Request):
    """Guard: Only allow in debug mode."""
    if not settings.DEBUG:
        raise HTTPException(404)  # Pretend it doesn't exist
    # Optional: Check for internal IP or special header
    return True

@router.get("/flags")
async def get_all_flags(request: Request):
    require_debug_mode(request)
    return {
        "flags": {
            "simulation_mode": settings.FEATURE_SIMULATION_MODE,
            "beta_features": settings.FEATURE_BETA,
        },
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }

@router.get("/health/detailed")
async def detailed_health(request: Request):
    require_debug_mode(request)
    return {
        "database": "connected",  # Actually check
        "ocr_provider": settings.OCR_PROVIDER,
        "features": {...}
    }
```

#### Conditional Inclusion in main.py

```python
# backend/main.py
from app.debug.router import router as debug_router
from app.settings.env_settings import settings

# Only include debug routes if explicitly enabled
if settings.DEBUG and settings.ENABLE_DEBUG_ROUTES:
    app.include_router(debug_router)
```

### 4. Environment Configuration

```bash
# .env.example

# Debug Mode (NEVER true in production)
DEBUG=false
ENABLE_DEBUG_ROUTES=false

# Feature Flags
FEATURE_SIMULATION_MODE=false
FEATURE_BETA_DASHBOARD=false
```

```python
# backend/app/settings/env_settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Debug
    DEBUG: bool = False
    ENABLE_DEBUG_ROUTES: bool = False
    
    # Features
    FEATURE_SIMULATION_MODE: bool = False
    FEATURE_BETA_DASHBOARD: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 5. Frontend Flag Store Enhancement

Update the existing `featureFlags.ts` to support URL params:

```typescript
// frontend-svelt/src/lib/stores/featureFlags.ts

function parseUrlFlags(): Partial<FeatureFlags> {
    const params = new URLSearchParams(window.location.search);
    const overrides: Partial<FeatureFlags> = {};
    
    // Support ?simulation=true
    if (params.get('simulation') === 'true') {
        overrides.simulationMode = true;
    }
    if (params.get('debug') === 'true') {
        overrides.debugMode = true;
    }
    
    return overrides;
}

// Merge priority: URL > localStorage > server defaults
export function initializeFlags(serverFlags: FeatureFlags): void {
    const urlOverrides = parseUrlFlags();
    const storedOverrides = parseStoredOverrides();
    
    // URL takes highest priority
    const finalOverrides = { ...storedOverrides, ...urlOverrides };
    
    if (Object.keys(finalOverrides).length > 0) {
        overrides.set(finalOverrides);
    }
}
```

---

## Implementation Plan

### Phase 14: Debug Flag System (Future Work)

| Task | Effort | Priority |
|------|--------|----------|
| 14.1 Fix simulation toggle placement | 15 min | High |
| 14.2 Create unified DebugPanel.svelte | 1 hr | Medium |
| 14.3 Add URL param support to featureFlags.ts | 30 min | Medium |
| 14.4 Add keyboard shortcut (Ctrl+Shift+D) | 15 min | Low |
| 14.5 Create backend debug router | 1 hr | Low |
| 14.6 Add environment-based debug guards | 30 min | High |
| 14.7 Update documentation | 30 min | Medium |
| 14.8 Remove stale DevFlags.svelte | 5 min | Low |

**Total Estimate:** ~4 hours

---

## Security Considerations

### Must Do Before Production

1. **Environment guards** — `DEBUG=false` in production `.env`
2. **Conditional router inclusion** — Debug routes not mounted in production
3. **No sensitive data in flags** — Flags control features, not security
4. **Sanitize debug output** — No PII, credentials, or tokens in debug endpoints
5. **Log debug access** — Audit trail for any debug endpoint usage

### Safe Defaults

| Setting | Dev | Production |
|---------|-----|------------|
| `DEBUG` | `true` | `false` |
| `ENABLE_DEBUG_ROUTES` | `true` | `false` |
| Debug panel visible | `true` | `false` |
| URL param override | Allowed | Ignored |

---

## Developer UX

### How to Enable Debug Mode

1. **Development:** Automatic (via `import.meta.env.DEV`)
2. **URL Parameter:** Add `?debug=true` to any URL
3. **Keyboard Shortcut:** Press `Ctrl+Shift+D` (or `Cmd+Shift+D` on Mac)
4. **localStorage:** `localStorage.setItem('debugMode', 'true')`

### How to Enable Simulation Mode

1. **UI:** Toggle "Use Simulated Data" checkbox (now visible before running)
2. **URL:** Add `?simulation=true` to workspace URL
3. **localStorage:** Toggle in debug panel

---

## Cleanup Plan

After implementation:

1. **Remove** `DevFlags.svelte` (replaced by unified DebugPanel)
2. **Remove** `FeatureFlagsPanel.svelte` (consolidated into DebugPanel)
3. **Update** `running-locally.md` with new debug panel instructions
4. **Update** `simulation-testing.md` with URL param examples

---

## References

- Martin Fowler's Feature Toggles: https://martinfowler.com/articles/feature-toggles.html
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- SvelteKit Environment Variables: https://kit.svelte.dev/docs/modules#$env-static-public
