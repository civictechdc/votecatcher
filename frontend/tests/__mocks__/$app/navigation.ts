/**
 * `$app/navigation` mock (extension-resolvable entry for the vitest `$app`
 * alias; suites that need custom behavior replace it with `vi.mock`).
 */
export const goto = () => {};
export const invalidate = () => {};
export const invalidateAll = () => {};
export const refreshAll = () => {};
export const preload = () => {};
export const preloadRoutes = () => {};
export const beforeNavigate = () => {};
export const afterNavigate = (_callback: () => void) => {};
export const onNavigate = () => {};
export const pushState = () => {};
export const replaceState = () => {};
