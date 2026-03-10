# Workspace Layout Design

**Date:** 2026-03-09
**Phase:** Phase 3 - Frontend Foundation
**Status:** Approved

## Overview

Implement a nested SvelteKit layout system for the workspace area with a fixed sidebar navigation. All workspace pages will inherit the layout automatically.

## Architecture

### Route Structure

```
src/routes/workspace/
├── +layout.svelte          # Sidebar + content area
├── +layout.ts              # Shared data loading (optional)
├── +page.svelte            # Dashboard (workspace home)
├── campaigns/
│   ├── +page.svelte        # Campaign list
│   └── [id]/
│       └── +page.svelte    # Campaign detail
├── jobs/
│   ├── +page.svelte        # Job list
│   └── [id]/
│       └── +page.svelte    # Job detail with SSE status
├── results/
│   └── [job_id]/
│       └── +page.svelte    # Results table for a job
└── settings/
    └── +page.svelte        # Workspace settings
```

### Components

```
src/lib/components/layout/
├── Sidebar.svelte          # Navigation sidebar
├── SidebarNavItem.svelte   # Nav item (icon + label, active state)
└── index.ts
```

## Implementation Details

### Layout Component

**routes/workspace/+layout.svelte:**
```svelte
<script lang="ts">
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  let { children } = $props();
</script>

<div class="flex min-h-screen bg-slate-50">
  <Sidebar />
  <main class="flex-1 overflow-auto p-6">
    {@render children()}
  </main>
</div>
```

### Sidebar Component

**Features:**
- Fixed width (256px / w-64)
- Logo/branding at top
- Navigation items with active state highlighting
- Collapsible on mobile (hamburger menu)

### SidebarNavItem Component

**Features:**
- Icon + label
- Active state (highlight current route using `$page.url.pathname`)
- Hover states
- Keyboard accessible

### Navigation Items

| Label | Route | Icon (lucide-svelte) |
|-------|-------|---------------------|
| Dashboard | /workspace | Home |
| Campaigns | /workspace/campaigns | FolderOpen |
| Jobs | /workspace/jobs | Activity |
| Results | /workspace/results | CheckCircle |
| Settings | /workspace/settings | Settings |

### Mobile Behavior

- Hidden by default on mobile (< 768px)
- Hamburger button shows sidebar as overlay
- Click outside or on nav item closes overlay
- Use Tailwind responsive classes (md:)

### Styling

- Tailwind CSS v4
- Consistent with existing Button/Input components
- White background, subtle right border
- Active state: blue background, blue text

## TDD Approach

1. Write tests for SidebarNavItem first:
   - Renders with icon and label
   - Shows active state when href matches
   - Handles click events
   - Keyboard accessible

2. Write tests for Sidebar:
   - Renders all nav items
   - Mobile toggle works
   - Active item highlighted

3. Implement components to pass tests

## Exit Criteria

- [ ] Sidebar renders with all navigation items
- [ ] Active state works based on current route
- [ ] Mobile responsive (hamburger menu)
- [ ] All tests passing
- [ ] Lint and typecheck clean
- [ ] Keyboard accessible

## Migration Notes

- Existing `/workspace/[id]` route will be replaced by new structure
- Current workspace page logic moves to `/workspace/jobs/[id]` or `/workspace/results/[job_id]`
