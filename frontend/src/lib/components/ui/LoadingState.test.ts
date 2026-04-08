import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import LoadingState from './LoadingState.svelte';

describe('LoadingState Component', () => {
	describe('Loading State', () => {
		it('shows LoadingSpinner when loading=true', () => {
			const { container } = render(LoadingState, {
				loading: true,
			});
			const spinner = container.querySelector('svg[role="status"]');
			expect(spinner).toBeTruthy();
		});

		it('hides content when loading=true', () => {
			const { queryByText } = render(LoadingState, {
				loading: true,
			});
			expect(queryByText('Content')).toBeFalsy();
		});
	});

	describe('Error State', () => {
		it('shows error when error prop provided', () => {
			const { getByText } = render(LoadingState, {
				error: 'Failed to load',
			});
			expect(getByText('Failed to load')).toBeTruthy();
		});

		it('shows error even when loading=true (error takes priority)', () => {
			const { getByText, container } = render(LoadingState, {
				loading: true,
				error: 'Error occurred',
			});
			expect(getByText('Error occurred')).toBeTruthy();
			expect(container.querySelector('svg[role="status"]')).toBeFalsy();
		});
	});

	describe('Content State', () => {
		it('shows content when loading=false and no error', () => {
			const { container } = render(LoadingState, {
				loading: false,
			});
			expect(container.querySelector('.loading-spinner-container')).toBeFalsy();
			expect(container.querySelector('[role="alert"]')).toBeFalsy();
		});

		it('shows content when both loading and error are false/undefined', () => {
			const { container } = render(LoadingState, {});
			expect(container.querySelector('.loading-spinner-container')).toBeFalsy();
			expect(container.querySelector('[role="alert"]')).toBeFalsy();
		});
	});

	describe('Component Integration', () => {
		it('uses LoadingSpinner component when loading', () => {
			const { container } = render(LoadingState, { loading: true });
			const spinner = container.querySelector('.animate-spin');
			expect(spinner).toBeTruthy();
		});

		it('uses ErrorDisplay component when error', () => {
			const { container } = render(LoadingState, { error: 'Test error' });
			const alert = container.querySelector('[role="alert"][aria-live="assertive"]');
			expect(alert).toBeTruthy();
		});
	});
});
