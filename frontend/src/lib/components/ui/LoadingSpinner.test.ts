import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import LoadingSpinner from './LoadingSpinner.svelte';

describe('LoadingSpinner Component', () => {
	describe('Rendering', () => {
		it('renders with default size (md)', () => {
			const { container } = render(LoadingSpinner);
			const svg = container.querySelector('svg');
			expect(svg).toBeTruthy();
			expect(svg?.classList.contains('h-8')).toBe(true);
			expect(svg?.classList.contains('w-8')).toBe(true);
		});

		it('renders with small size', () => {
			const { container } = render(LoadingSpinner, { size: 'sm' });
			const svg = container.querySelector('svg');
			expect(svg?.classList.contains('h-4')).toBe(true);
			expect(svg?.classList.contains('w-4')).toBe(true);
		});

		it('renders with large size', () => {
			const { container } = render(LoadingSpinner, { size: 'lg' });
			const svg = container.querySelector('svg');
			expect(svg?.classList.contains('h-12')).toBe(true);
			expect(svg?.classList.contains('w-12')).toBe(true);
		});

		it('renders with custom color class', () => {
			const { container } = render(LoadingSpinner, { color: 'text-purple-600' });
			const svg = container.querySelector('svg');
			expect(svg?.classList.contains('text-purple-600')).toBe(true);
		});

		it('spins with animate-spin class', () => {
			const { container } = render(LoadingSpinner);
			const svg = container.querySelector('svg');
			expect(svg?.classList.contains('animate-spin')).toBe(true);
		});
	});

	describe('Accessibility', () => {
		it('has proper aria-label="Loading"', () => {
			const { container } = render(LoadingSpinner);
			const svg = container.querySelector('svg');
			expect(svg?.getAttribute('aria-label')).toBe('Loading');
		});

		it('has role="status"', () => {
			const { container } = render(LoadingSpinner);
			const svg = container.querySelector('svg');
			expect(svg?.getAttribute('role')).toBe('status');
		});
	});

	describe('Loading Text', () => {
		it('renders optional loading text', () => {
			const { getByText } = render(LoadingSpinner, { text: 'Loading data...' });
			expect(getByText('Loading data...')).toBeTruthy();
		});

		it('does not render text when not provided', () => {
			const { queryByTestId } = render(LoadingSpinner);
			expect(queryByTestId('loading-text')).toBeFalsy();
		});
	});
});
