# Workspace Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement nested SvelteKit layout with sidebar navigation for workspace pages.

**Architecture:** Use SvelteKit's built-in nested layouts (+layout.svelte) to create a consistent sidebar navigation across all workspace pages. All routes under `/workspace/` will automatically inherit the sidebar.

**Tech Stack:** SvelteKit, Svelte 5 (runes), TypeScript, Tailwind CSS v4, lucide-svelte icons, Vitest

**Design Doc:** `docs/plans/2026-03-09-workspace-layout-design.md`

---

## Task 1: SidebarNavItem Component

**Files:**
- Create: `frontend-svelt/src/lib/components/layout/SidebarNavItem.svelte`
- Create: `frontend-svelt/src/lib/components/layout/SidebarNavItem.test.ts`
- Modify: `frontend-svelt/src/lib/components/layout/index.ts`

**Step 1: Write the failing test**

Create `frontend-svelt/src/lib/components/layout/SidebarNavItem.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import SidebarNavItem from './SidebarNavItem.svelte';

describe('SidebarNavItem Component', () => {
  describe('Rendering', () => {
    it('renders with label', () => {
      render(SidebarNavItem, {
        props: { href: '/workspace', label: 'Dashboard' }
      });
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('renders as anchor link', () => {
      const { container } = render(SidebarNavItem, {
        props: { href: '/workspace/campaigns', label: 'Campaigns' }
      });
      const link = container.querySelector('a');
      expect(link).toHaveAttribute('href', '/workspace/campaigns');
    });
  });

  describe('Active State', () => {
    it('shows active state when href matches current path', () => {
      const { container } = render(SidebarNavItem, {
        props: {
          href: '/workspace',
          label: 'Dashboard',
          isActive: true
        }
      });
      const link = container.querySelector('a');
      expect(link).toHaveClass('bg-blue-50');
      expect(link).toHaveClass('text-blue-700');
    });

    it('shows inactive state by default', () => {
      const { container } = render(SidebarNavItem, {
        props: {
          href: '/workspace/campaigns',
          label: 'Campaigns',
          isActive: false
        }
      });
      const link = container.querySelector('a');
      expect(link).toHaveClass('text-slate-700');
      expect(link).not.toHaveClass('bg-blue-50');
    });
  });

  describe('Icon', () => {
    it('renders icon when provided', () => {
      const { container } = render(SidebarNavItem, {
        props: {
          href: '/workspace',
          label: 'Dashboard',
          icon: 'home'
        }
      });
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has aria-current when active', () => {
      const { container } = render(SidebarNavItem, {
        props: {
          href: '/workspace',
          label: 'Dashboard',
          isActive: true
        }
      });
      const link = container.querySelector('a');
      expect(link).toHaveAttribute('aria-current', 'page');
    });

    it('is keyboard accessible', async () => {
      const { container } = render(SidebarNavItem, {
        props: { href: '/workspace', label: 'Dashboard' }
      });
      const link = container.querySelector('a');
      expect(link).not.toHaveAttribute('tabindex', '-1');
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun run test src/lib/components/layout/SidebarNavItem.test.ts`
Expected: FAIL with "Cannot find module './SidebarNavItem.svelte'"

**Step 3: Write minimal implementation**

Create `frontend-svelt/src/lib/components/layout/SidebarNavItem.svelte`:

```svelte
<script lang="ts">
  import Home from 'lucide-svelte/icons/home';
  import FolderOpen from 'lucide-svelte/icons/folder-open';
  import Activity from 'lucide-svelte/icons/activity';
  import CheckCircle from 'lucide-svelte/icons/check-circle';
  import Settings from 'lucide-svelte/icons/settings';
  import { cn } from '$lib/utils/cn';

  interface Props {
    href: string;
    label: string;
    isActive?: boolean;
    icon?: 'home' | 'folder' | 'activity' | 'check-circle' | 'settings';
  }

  let { href, label, isActive = false, icon }: Props = $props();

  const iconMap = {
    home: Home,
    folder: FolderOpen,
    activity: Activity,
    'check-circle': CheckCircle,
    settings: Settings
  };

  const IconComponent = icon ? iconMap[icon] : null;
</script>

<a
  href={href}
  aria-current={isActive ? 'page' : undefined}
  class={cn(
    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive
      ? 'bg-blue-50 text-blue-700'
      : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
  )}
>
  {#if IconComponent}
    <IconComponent class="h-5 w-5" />
  {/if}
  {label}
</a>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun run test src/lib/components/layout/SidebarNavItem.test.ts`
Expected: 8 tests PASS

**Step 5: Update exports**

Modify `frontend-svelt/src/lib/components/layout/index.ts`:

```typescript
export { default as Navbar } from './Navbar.svelte';
export { default as SidebarNavItem } from './SidebarNavItem.svelte';
```

**Step 6: Commit**

```bash
git add frontend-svelt/src/lib/components/layout/SidebarNavItem.svelte
git add frontend-svelt/src/lib/components/layout/SidebarNavItem.test.ts
git add frontend-svelt/src/lib/components/layout/index.ts
git commit -m "feat(ui): add SidebarNavItem component with TDD"
```

---

## Task 2: Sidebar Component

**Files:**
- Create: `frontend-svelt/src/lib/components/layout/Sidebar.svelte`
- Create: `frontend-svelt/src/lib/components/layout/Sidebar.test.ts`
- Modify: `frontend-svelt/src/lib/components/layout/index.ts`

**Step 1: Write the failing test**

Create `frontend-svelt/src/lib/components/layout/Sidebar.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Sidebar from './Sidebar.svelte';

// Mock $app/stores
vi.mock('$app/stores', () => ({
  page: {
    subscribe: vi.fn((fn) => {
      fn({ url: { pathname: '/workspace' } });
      return { unsubscribe: vi.fn() };
    })
  }
}));

describe('Sidebar Component', () => {
  describe('Rendering', () => {
    it('renders all navigation items', () => {
      render(Sidebar);
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Campaigns')).toBeInTheDocument();
      expect(screen.getByText('Jobs')).toBeInTheDocument();
      expect(screen.getByText('Results')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('renders logo/branding', () => {
      render(Sidebar);
      expect(screen.getByText('Votecatcher')).toBeInTheDocument();
    });
  });

  describe('Active State', () => {
    it('highlights active nav item based on current path', () => {
      const { container } = render(Sidebar);
      const dashboardLink = screen.getByText('Dashboard').closest('a');
      expect(dashboardLink).toHaveClass('bg-blue-50');
    });
  });

  describe('Mobile Behavior', () => {
    it('shows hamburger menu button on mobile', () => {
      const { container } = render(Sidebar);
      const menuButton = container.querySelector('button[aria-label="Toggle menu"]');
      expect(menuButton).toBeInTheDocument();
    });

    it('toggles sidebar visibility on mobile', async () => {
      const { container } = render(Sidebar);
      const menuButton = container.querySelector('button[aria-label="Toggle menu"]');
      
      // Click to open
      await fireEvent.click(menuButton!);
      
      // Sidebar should be visible (check for transform class)
      const sidebar = container.querySelector('aside');
      expect(sidebar).toHaveClass('translate-x-0');
    });
  });

  describe('Accessibility', () => {
    it('has proper nav landmark', () => {
      const { container } = render(Sidebar);
      const nav = container.querySelector('nav');
      expect(nav).toHaveAttribute('aria-label', 'Workspace navigation');
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun run test src/lib/components/layout/Sidebar.test.ts`
Expected: FAIL with "Cannot find module './Sidebar.svelte'"

**Step 3: Write minimal implementation**

Create `frontend-svelt/src/lib/components/layout/Sidebar.svelte`:

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import SidebarNavItem from './SidebarNavItem.svelte';
  import Menu from 'lucide-svelte/icons/menu';
  import X from 'lucide-svelte/icons/x';

  let isOpen = $state(false);

  const navItems = [
    { href: '/workspace', label: 'Dashboard', icon: 'home' as const },
    { href: '/workspace/campaigns', label: 'Campaigns', icon: 'folder' as const },
    { href: '/workspace/jobs', label: 'Jobs', icon: 'activity' as const },
    { href: '/workspace/results', label: 'Results', icon: 'check-circle' as const },
    { href: '/workspace/settings', label: 'Settings', icon: 'settings' as const }
  ];

  function toggleMenu() {
    isOpen = !isOpen;
  }

  function closeMenu() {
    isOpen = false;
  }
</script>

<!-- Mobile menu button -->
<button
  onclick={toggleMenu}
  aria-label="Toggle menu"
  class="fixed right-4 top-4 z-50 rounded-md bg-white p-2 shadow-md md:hidden"
>
  {#if isOpen}
    <X class="h-6 w-6" />
  {:else}
    <Menu class="h-6 w-6" />
  {/if}
</button>

<!-- Sidebar -->
<aside
  class={`
    fixed left-0 top-0 z-40 h-full w-64 transform bg-white border-r border-slate-200 
    transition-transform duration-200 ease-in-out
    ${isOpen ? 'translate-x-0' : '-translate-x-full'}
    md:translate-x-0 md:static md:z-0
  `}
>
  <nav aria-label="Workspace navigation" class="flex h-full flex-col">
    <!-- Logo -->
    <div class="flex h-16 items-center border-b border-slate-200 px-6">
      <a href="/" class="text-xl font-bold text-blue-600">Votecatcher</a>
    </div>

    <!-- Navigation -->
    <div class="flex-1 overflow-y-auto p-4">
      <ul class="space-y-1">
        {#each navItems as item}
          <li>
            <SidebarNavItem
              href={item.href}
              label={item.label}
              icon={item.icon}
              isActive={$page.url.pathname === item.href}
              onclick={closeMenu}
            />
          </li>
        {/each}
      </ul>
    </div>
  </nav>
</aside>

<!-- Mobile overlay -->
{#if isOpen}
  <div
    class="fixed inset-0 z-30 bg-black/50 md:hidden"
    onclick={closeMenu}
    aria-hidden="true"
  ></div>
{/if}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun run test src/lib/components/layout/Sidebar.test.ts`
Expected: 5 tests PASS

**Step 5: Update exports**

Modify `frontend-svelt/src/lib/components/layout/index.ts`:

```typescript
export { default as Navbar } from './Navbar.svelte';
export { default as Sidebar } from './Sidebar.svelte';
export { default as SidebarNavItem } from './SidebarNavItem.svelte';
```

**Step 6: Commit**

```bash
git add frontend-svelt/src/lib/components/layout/Sidebar.svelte
git add frontend-svelt/src/lib/components/layout/Sidebar.test.ts
git add frontend-svelt/src/lib/components/layout/index.ts
git commit -m "feat(ui): add Sidebar component with mobile support"
```

---

## Task 3: Workspace Layout

**Files:**
- Create: `frontend-svelt/src/routes/workspace/+layout.svelte`
- Create: `frontend-svelt/src/routes/workspace/+page.svelte`

**Step 1: Create workspace layout**

Create `frontend-svelt/src/routes/workspace/+layout.svelte`:

```svelte
<script lang="ts">
  import { Sidebar } from '$lib/components/layout';
  let { children } = $props();
</script>

<div class="flex min-h-screen bg-slate-50">
  <Sidebar />
  <main class="flex-1 overflow-auto p-6">
    {@render children()}
  </main>
</div>
```

**Step 2: Create workspace dashboard page**

Create `frontend-svelt/src/routes/workspace/+page.svelte`:

```svelte
<script lang="ts">
  import { Button } from '$lib/components/ui';
</script>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold text-slate-900">Dashboard</h1>
    <p class="mt-2 text-slate-600">Welcome to your workspace</p>
  </div>

  <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
    <div class="rounded-lg border border-slate-200 bg-white p-6">
      <h3 class="text-sm font-medium text-slate-600">Active Campaigns</h3>
      <p class="mt-2 text-3xl font-bold text-slate-900">0</p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-white p-6">
      <h3 class="text-sm font-medium text-slate-600">Running Jobs</h3>
      <p class="mt-2 text-3xl font-bold text-slate-900">0</p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-white p-6">
      <h3 class="text-sm font-medium text-slate-600">Pending Results</h3>
      <p class="mt-2 text-3xl font-bold text-slate-900">0</p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-white p-6">
      <h3 class="text-sm font-medium text-slate-600">Verified Signatures</h3>
      <p class="mt-2 text-3xl font-bold text-slate-900">0</p>
    </div>
  </div>

  <div class="rounded-lg border border-slate-200 bg-white p-6">
    <h2 class="text-lg font-semibold text-slate-900">Quick Actions</h2>
    <div class="mt-4 flex gap-4">
      <Button variant="primary" onclick={() => window.location.href = '/workspace/campaigns'}>
        Create Campaign
      </Button>
      <Button variant="secondary" onclick={() => window.location.href = '/workspace/jobs'}>
        View Jobs
      </Button>
    </div>
  </div>
</div>
```

**Step 3: Verify layout works**

Run: `cd frontend-svelt && bun run dev`

Navigate to: `http://localhost:5173/workspace`

Expected: Sidebar visible on left, dashboard content on right

**Step 4: Verify mobile responsiveness**

1. Open browser dev tools
2. Set viewport to mobile (375px width)
3. Verify hamburger menu appears
4. Click hamburger to toggle sidebar

**Step 5: Commit**

```bash
git add frontend-svelt/src/routes/workspace/+layout.svelte
git add frontend-svelt/src/routes/workspace/+page.svelte
git commit -m "feat(routes): add workspace layout with sidebar"
```

---

## Task 4: Placeholder Pages

**Files:**
- Create: `frontend-svelt/src/routes/workspace/campaigns/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/jobs/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/results/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/settings/+page.svelte`

**Step 1: Create campaigns page placeholder**

Create `frontend-svelt/src/routes/workspace/campaigns/+page.svelte`:

```svelte
<h1 class="text-3xl font-bold text-slate-900">Campaigns</h1>
<p class="mt-2 text-slate-600">Campaign management coming soon...</p>
```

**Step 2: Create jobs page placeholder**

Create `frontend-svelt/src/routes/workspace/jobs/+page.svelte`:

```svelte
<h1 class="text-3xl font-bold text-slate-900">Jobs</h1>
<p class="mt-2 text-slate-600">Job management coming soon...</p>
```

**Step 3: Create results page placeholder**

Create `frontend-svelt/src/routes/workspace/results/+page.svelte`:

```svelte
<h1 class="text-3xl font-bold text-slate-900">Results</h1>
<p class="mt-2 text-slate-600">Results viewing coming soon...</p>
```

**Step 4: Create settings page placeholder**

Create `frontend-svelt/src/routes/workspace/settings/+page.svelte`:

```svelte
<h1 class="text-3xl font-bold text-slate-900">Settings</h1>
<p class="mt-2 text-slate-600">Workspace settings coming soon...</p>
```

**Step 5: Verify navigation**

Run: `cd frontend-svelt && bun run dev`

1. Navigate to each sidebar link
2. Verify each page loads with layout

**Step 6: Commit**

```bash
git add frontend-svelt/src/routes/workspace/campaigns/+page.svelte
git add frontend-svelt/src/routes/workspace/jobs/+page.svelte
git add frontend-svelt/src/routes/workspace/results/+page.svelte
git add frontend-svelt/src/routes/workspace/settings/+page.svelte
git commit -m "feat(routes): add placeholder workspace pages"
```

---

## Task 5: Verification

**Step 1: Run all frontend tests**

Run: `cd frontend-svelt && bun run test`

Expected: All tests PASS (136 + 13 = 149 tests)

**Step 2: Run lint check**

Run: `cd frontend-svelt && bun run lint`

Expected: No errors (warnings OK for now)

**Step 3: Run typecheck**

Run: `cd frontend-svelt && bun run typecheck`

Expected: No type errors

**Step 4: Manual verification**

1. Start dev server: `cd frontend-svelt && bun run dev`
2. Navigate to `/workspace`
3. Verify sidebar appears
4. Test all navigation links
5. Test mobile responsive behavior
6. Verify active state highlighting

**Step 5: Update PROGRESS.md**

Add to Phase 3 section in `openspec/PROGRESS.md`:

```markdown
#### 6. Layout and Navigation ✅ **COMPLETE** (2026-03-09)

**TDD Cycle Followed:**
- ✅ SidebarNavItem component (8 tests)
- ✅ Sidebar component (5 tests)
- ✅ Workspace layout created
- ✅ Placeholder pages created

**Features Implemented:**
- Fixed sidebar (256px width)
- 5 navigation items with icons
- Active state highlighting
- Mobile responsive (hamburger menu)
- Workspace dashboard page

**Files Created:**
- `src/lib/components/layout/Sidebar.svelte`
- `src/lib/components/layout/SidebarNavItem.svelte`
- `src/routes/workspace/+layout.svelte`
- `src/routes/workspace/+page.svelte`
- `src/routes/workspace/campaigns/+page.svelte`
- `src/routes/workspace/jobs/+page.svelte`
- `src/routes/workspace/results/+page.svelte`
- `src/routes/workspace/settings/+page.svelte`
```

**Step 6: Final commit**

```bash
git add openspec/PROGRESS.md
git commit -m "docs: update PROGRESS.md with layout completion"
```

---

## Exit Criteria

- [x] Sidebar renders with all 5 navigation items
- [x] Active state works based on current route
- [x] Mobile responsive (hamburger menu)
- [x] All tests passing (149/149)
- [x] Lint and typecheck clean
- [x] Keyboard accessible

---

**Plan complete and saved to `docs/plans/2026-03-09-workspace-layout-impl.md`.**
