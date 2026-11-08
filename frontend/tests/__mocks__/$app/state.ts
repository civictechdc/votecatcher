// Extension-resolvable entry so `$app/state` (via the vitest `$app` alias)
// resolves without extension inference; the reactive mock lives in state.svelte.ts.
export { page, navigating, updated } from "./state.svelte.ts";
