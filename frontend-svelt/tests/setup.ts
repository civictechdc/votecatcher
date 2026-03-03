import { vi } from 'vitest';

vi.mock('$app/environment', () => ({
	browser: false,
	dev: true,
	prerendering: false,
	SSR: true,
}));

vi.mock('$app/stores', () => {
	const { readable } = require('svelte/store');
	return {
		page: readable({
			url: new URL('http://localhost'),
			params: {},
			route: {},
			status: 200,
			error: null,
			data: {},
			state: {},
		}),
		navigating: readable(null),
		updated: readable(false),
		goto: vi.fn(),
		invalidate: vi.fn(),
		invalidateAll: vi.fn(),
		prefetch: vi.fn(),
		prefetchRoutes: vi.fn(),
		beforeNavigate: vi.fn(),
		afterNavigate: vi.fn(),
	};
});
