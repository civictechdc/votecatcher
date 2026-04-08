import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import Page from './+page.svelte';

const createMockDemoStore = (initialState = {}) => {
	const state = {
		showResetConfirmation: false,
		resetting: false,
		loading: false,
		error: null,
		prebakedSessions: [
			{ id: 'dc-2024', name: 'DC Demo 2024', description: 'Sample DC petition data' },
		],
		...initialState,
	};

	const store = writable(state);

	return {
		subscribe: store.subscribe,
		confirmReset: vi.fn(() => store.update((s) => ({ ...s, showResetConfirmation: true }))),
		cancelReset: vi.fn(() => store.update((s) => ({ ...s, showResetConfirmation: false }))),
		resetData: vi.fn(async () => {
			store.update((s) => ({ ...s, resetting: true }));
			store.update((s) => ({
				...s,
				resetting: false,
				showResetConfirmation: false,
			}));
		}),
		loadPrebaked: vi.fn(async (id: string) => ({ id, loaded: true })),
		clearError: vi.fn(() => store.update((s) => ({ ...s, error: null }))),
		fetchPrebakedSessions: vi.fn(),
	};
};

vi.mock('$lib/stores/demo', () => ({
	get demo() {
		return createMockDemoStore();
	},
	isDemoModeEnabled: () => true,
	setDemoMode: vi.fn(),
}));

describe('Demo Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should display demo page title', () => {
		render(Page);
		expect(screen.getByText(/demo mode/i)).toBeInTheDocument();
	});

	it('should show reset button', () => {
		render(Page);
		expect(screen.getByRole('button', { name: /reset demo/i })).toBeInTheDocument();
	});

	it('should show available pre-baked sessions', () => {
		render(Page);
		expect(screen.getByText('DC Demo 2024')).toBeInTheDocument();
	});
});
