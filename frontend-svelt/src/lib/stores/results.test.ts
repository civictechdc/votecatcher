import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { results, resetResultsStore } from './results';
import { getApiClient } from './api-client';

vi.mock('./api-client');

describe('Results Store', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		resetResultsStore();
	});

	describe('fetchResults', () => {
		it('starts with empty state', () => {
			const state = get(results);
			expect(state.results).toEqual([]);
			expect(state.loading).toBe(false);
			expect(state.error).toBeNull();
		});

		it('fetches results from API', async () => {
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

			const mockClient = {
				getResults: vi.fn().mockResolvedValue({
					items: mockResults,
					total: 2,
					offset: 0,
					limit: 50
				})
			};
			vi.mocked(getApiClient).mockReturnValue(mockClient as any);

			await results.fetchResults(1);

			const state = get(results);
			expect(state.results).toEqual(mockResults);
			expect(state.total).toBe(2);
			expect(state.loading).toBe(false);
			expect(mockClient.getResults).toHaveBeenCalledWith({ jobId: 1, offset: 0, limit: 50 });
		});

		it('handles fetch errors', async () => {
			const mockClient = {
				getResults: vi.fn().mockRejectedValue(new Error('Failed to fetch results'))
			};
			vi.mocked(getApiClient).mockReturnValue(mockClient as any);

			await results.fetchResults(1);

			const state = get(results);
			expect(state.error).toBe('Failed to fetch results');
			expect(state.loading).toBe(false);
		});
	});

	describe('pagination', () => {
		it('fetches paginated results', async () => {
			const mockClient = {
				getResults: vi.fn().mockResolvedValue({
					items: [],
					total: 100,
					offset: 50,
					limit: 50
				})
			};
			vi.mocked(getApiClient).mockReturnValue(mockClient as any);

			await results.fetchResults(1, { offset: 50, limit: 50 });

			const state = get(results);
			expect(state.offset).toBe(50);
			expect(state.limit).toBe(50);
			expect(mockClient.getResults).toHaveBeenCalledWith({ jobId: 1, offset: 50, limit: 50 });
		});
	});

	describe('filtering', () => {
		it('filters by confidence level', async () => {
			const mockClient = {
				getResults: vi.fn().mockResolvedValue({
					items: [],
					total: 0,
					offset: 0,
					limit: 50
				})
			};
			vi.mocked(getApiClient).mockReturnValue(mockClient as any);

			await results.fetchResults(1, { confidence: 'HIGH' });

			expect(mockClient.getResults).toHaveBeenCalledWith({
				jobId: 1,
				offset: 0,
				limit: 50,
				confidence: 'HIGH'
			});
		});
	});

	describe('exportCSV', () => {
		it('exports results to CSV', async () => {
			const csvData = 'ocr_text,prediction_1_name,score\nJohn Doe,John Doe,0.95';
			const mockClient = {
				exportResults: vi.fn().mockResolvedValue(csvData)
			};
			vi.mocked(getApiClient).mockReturnValue(mockClient as any);

			const csv = await results.exportCSV(1);

			expect(csv).toBe(csvData);
			expect(mockClient.exportResults).toHaveBeenCalledWith({ jobId: 1 });
		});

		it('handles export errors', async () => {
			const mockClient = {
				exportResults: vi.fn().mockRejectedValue(new Error('Export failed'))
			};
			vi.mocked(getApiClient).mockReturnValue(mockClient as any);

			await expect(results.exportCSV(1)).rejects.toThrow('Export failed');
		});
	});
});
