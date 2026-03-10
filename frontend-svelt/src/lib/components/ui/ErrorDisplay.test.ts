import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import ErrorDisplay from './ErrorDisplay.svelte';

describe('ErrorDisplay Component', () => {
	describe('Rendering', () => {
		it('renders with error message', () => {
			const { getByText } = render(ErrorDisplay, { message: 'Something went wrong' });
			expect(getByText('Something went wrong')).toBeTruthy();
		});

		it('renders with optional title', () => {
			const { getByText } = render(ErrorDisplay, {
				title: 'Error Title',
				message: 'Error message'
			});
			expect(getByText('Error Title')).toBeTruthy();
			expect(getByText('Error message')).toBeTruthy();
		});

		it('renders without title when not provided', () => {
			const { queryByRole } = render(ErrorDisplay, { message: 'Error' });
			const heading = queryByRole('heading');
			expect(heading).toBeFalsy();
		});
	});

	describe('Variants', () => {
		it('renders with error variant (default)', () => {
			const { container } = render(ErrorDisplay, { message: 'Error' });
			const alert = container.querySelector('[role="alert"]');
			expect(alert?.classList.contains('bg-red-50')).toBe(true);
			expect(alert?.classList.contains('border-red-200')).toBe(true);
			expect(alert?.classList.contains('text-red-800')).toBe(true);
		});

		it('renders with warning variant', () => {
			const { container } = render(ErrorDisplay, {
				message: 'Warning',
				variant: 'warning'
			});
			const alert = container.querySelector('[role="alert"]');
			expect(alert?.classList.contains('bg-yellow-50')).toBe(true);
			expect(alert?.classList.contains('border-yellow-200')).toBe(true);
			expect(alert?.classList.contains('text-yellow-800')).toBe(true);
		});

		it('renders with info variant', () => {
			const { container } = render(ErrorDisplay, {
				message: 'Info',
				variant: 'info'
			});
			const alert = container.querySelector('[role="alert"]');
			expect(alert?.classList.contains('bg-blue-50')).toBe(true);
			expect(alert?.classList.contains('border-blue-200')).toBe(true);
			expect(alert?.classList.contains('text-blue-800')).toBe(true);
		});
	});

	describe('Retry Button', () => {
		it('shows retry button when onRetry provided', () => {
			const { getByRole } = render(ErrorDisplay, {
				message: 'Error',
				onRetry: () => {}
			});
			expect(getByRole('button', { name: /try again/i })).toBeTruthy();
		});

		it('does not show retry button when onRetry not provided', () => {
			const { queryByRole } = render(ErrorDisplay, { message: 'Error' });
			expect(queryByRole('button')).toBeFalsy();
		});

		it('handles retry button click', async () => {
			const onRetry = vi.fn();
			const { getByRole } = render(ErrorDisplay, {
				message: 'Error',
				onRetry
			});
			const button = getByRole('button', { name: /try again/i });
			button.click();
			expect(onRetry).toHaveBeenCalledTimes(1);
		});
	});

	describe('Accessibility', () => {
		it('has role="alert"', () => {
			const { container } = render(ErrorDisplay, { message: 'Error' });
			const alert = container.querySelector('[role="alert"]');
			expect(alert).toBeTruthy();
		});

		it('has aria-live="assertive"', () => {
			const { container } = render(ErrorDisplay, { message: 'Error' });
			const alert = container.querySelector('[role="alert"]');
			expect(alert?.getAttribute('aria-live')).toBe('assertive');
		});
	});
});
