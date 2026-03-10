import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import Page from './+page.svelte';
import { results } from '$lib/stores/results';

vi.mock('$lib/stores/results');

describe('Results Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		vi.mocked(results.subscribe).mockImplementation((fn: any) => {
			fn({
				results: [],
				total: 0,
				offset: 0,
				limit: 50,
				loading: false,
				error: null
			});
			return () => {};
		});
	});

	it('displays page title', () => {
		render(Page);
		expect(screen.getByText(/results/i)).toBeInTheDocument();
	});

	it('shows loading state', async () => {
		vi.mocked(results.subscribe).mockImplementation((fn: any) => {
			fn({
				results: [],
				total: 0,
				offset: 0,
				limit: 50,
				loading: true,
				error: null
			});
			return () => {};
		});

		render(Page);
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it('shows error state', async () => {
		vi.mocked(results.subscribe).mockImplementation((fn: any) => {
			fn({
				results: [],
				total: 0,
				offset: 0,
				limit: 50,
				loading: false,
				error: 'Failed to load results'
			});
			return () => {};
		});

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

		vi.mocked(results.subscribe).mockImplementation((fn: any) => {
			fn({
				results: mockResults,
				total: 2,
				offset: 0,
				limit: 50,
				loading: false,
				error: null
			});
			return () => {};
		});

		render(Page);

		expect(screen.getByText('John Doe')).toBeInTheDocument();
		expect(screen.getByText('Jane Smith')).toBeInTheDocument();
		expect(screen.getByText(/high/i)).toBeInTheDocument();
		expect(screen.getByText(/medium/i)).toBeInTheDocument();
	});

	it('shows empty state when no results', async () => {
		vi.mocked(results.subscribe).mockImplementation((fn: any) => {
			fn({
				results: [],
				total: 0,
				offset: 0,
				limit: 50,
				loading: false,
				error: null
			});
			return () => {};
		});

		render(Page);
		expect(screen.getByText(/no results/i)).toBeInTheDocument();
	});
});
