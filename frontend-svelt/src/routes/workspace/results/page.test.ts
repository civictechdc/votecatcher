import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from './+page.svelte';
import { results } from '$lib/stores/results';
import type { Unsubscriber, Subscriber } from 'svelte/store';
import type { ResultResponse } from '$lib/api/generated';

vi.mock('$lib/stores/results');

interface ResultsState {
	results: ResultResponse[];
	total: number;
	page: number;
	pageSize: number;
	confidence?: string;
	loading: boolean;
	error: string | null;
}

type MockState = Partial<ResultsState>;

const defaultState: ResultsState = {
	results: [],
	total: 0,
	page: 1,
	pageSize: 50,
	loading: false,
	error: null
};

function createMockSubscribe(overrides: MockState = {}) {
	return (fn: Subscriber<ResultsState>): Unsubscriber => {
		fn({ ...defaultState, ...overrides });
		return () => {};
	};
}

describe('Results Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		vi.mocked(results.subscribe).mockImplementation(createMockSubscribe());
	});

	it('displays page title', () => {
		render(Page);
		expect(screen.getByText(/results/i)).toBeInTheDocument();
	});

	it('shows loading state', async () => {
		vi.mocked(results.subscribe).mockImplementation(
			createMockSubscribe({ loading: true })
		);

		render(Page);
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it('shows error state', async () => {
		vi.mocked(results.subscribe).mockImplementation(
			createMockSubscribe({ error: 'Failed to load results' })
		);

		render(Page);
		expect(screen.getByText(/failed to load results/i)).toBeInTheDocument();
	});

	it('displays results table when data is loaded', async () => {
		const mockResults = [
			{
				id: 1,
				ocr_result_id: 1,
				prediction_1_name: 'John Doe',
				prediction_1_score: 0.95,
				confidence_level: 'HIGH'
			},
			{
				id: 2,
				ocr_result_id: 2,
				prediction_1_name: 'Jane Smith',
				prediction_1_score: 0.75,
				confidence_level: 'MEDIUM'
			}
		];

		vi.mocked(results.subscribe).mockImplementation(
			createMockSubscribe({ results: mockResults as unknown as ResultResponse[], total: 2 })
		);

		render(Page);

		expect(screen.getByText('John Doe')).toBeInTheDocument();
		expect(screen.getByText('Jane Smith')).toBeInTheDocument();
		expect(screen.getByText(/high/i)).toBeInTheDocument();
		expect(screen.getByText(/medium/i)).toBeInTheDocument();
	});

	it('shows empty state when no results', async () => {
		vi.mocked(results.subscribe).mockImplementation(
			createMockSubscribe({ results: [], total: 0 })
		);

		render(Page);
		expect(screen.getByText(/no results/i)).toBeInTheDocument();
	});
});
