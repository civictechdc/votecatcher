/**
 * `$app/state` mock for unit tests (vitest alias `$app` -> `tests/__mocks__/$app`).
 *
 * Kit 3 replaces the legacy page readables with fine-grained Svelte 5 state, so
 * the mock must be a reactive `$state` proxy: components read `page.params` etc.
 * directly and tests mutate the same object to drive re-renders. `$state` is a
 * compiler macro, so this file lives as a `.svelte.ts` module.
 *
 * `state.ts` re-exports this module so the bare `$app/state` specifier also
 * resolves without extension inference.
 */
export const page = $state({
	url: new URL("http://localhost"),
	params: {} as Record<string, string>,
	route: {} as Record<string, unknown>,
	status: 200,
	error: null,
	data: {} as Record<string, unknown>,
	state: {} as Record<string, unknown>,
});

export const navigating = $state(null);

export const updated = $state({ current: false });
