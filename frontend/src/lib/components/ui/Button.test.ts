import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import Button from './Button.svelte';

describe('Button Component', () => {
	describe('Rendering', () => {
		it('renders with text content', () => {
			const { getByRole } = render(Button, { text: 'Click me' });
			const button = getByRole('button');
			expect(button).toBeTruthy();
			expect(button.textContent).toBe('Click me');
		});

		it('renders with primary variant', () => {
			const { getByRole } = render(Button, {
				variant: 'primary',
				text: 'Primary',
			});
			const button = getByRole('button');
			expect(button.classList.contains('bg-blue-600')).toBe(true);
		});

		it('renders with secondary variant', () => {
			const { getByRole } = render(Button, {
				variant: 'secondary',
				text: 'Secondary',
			});
			const button = getByRole('button');
			expect(button.classList.contains('bg-gray-200')).toBe(true);
		});

		it('renders with danger variant', () => {
			const { getByRole } = render(Button, {
				variant: 'danger',
				text: 'Delete',
			});
			const button = getByRole('button');
			expect(button.classList.contains('bg-red-600')).toBe(true);
		});
	});

	describe('Sizes', () => {
		it('renders with small size', () => {
			const { getByRole } = render(Button, {
				size: 'sm',
				text: 'Small',
			});
			const button = getByRole('button');
			expect(button.classList.contains('px-3')).toBe(true);
			expect(button.classList.contains('py-1.5')).toBe(true);
			expect(button.classList.contains('text-sm')).toBe(true);
		});

		it('renders with medium size (default)', () => {
			const { getByRole } = render(Button, { text: 'Medium' });
			const button = getByRole('button');
			expect(button.classList.contains('px-4')).toBe(true);
			expect(button.classList.contains('py-2')).toBe(true);
			expect(button.classList.contains('text-base')).toBe(true);
		});

		it('renders with large size', () => {
			const { getByRole } = render(Button, {
				size: 'lg',
				text: 'Large',
			});
			const button = getByRole('button');
			expect(button.classList.contains('px-6')).toBe(true);
			expect(button.classList.contains('py-3')).toBe(true);
			expect(button.classList.contains('text-lg')).toBe(true);
		});
	});

	describe('States', () => {
		it('renders as disabled', () => {
			const { getByRole } = render(Button, {
				disabled: true,
				text: 'Disabled',
			});
			const button = getByRole('button');
			expect((button as HTMLButtonElement).disabled).toBe(true);
			expect(button.classList.contains('opacity-50')).toBe(true);
			expect(button.classList.contains('cursor-not-allowed')).toBe(true);
		});

		it('renders loading state', () => {
			const { getByRole, getByTestId } = render(Button, {
				loading: true,
				text: 'Loading',
			});
			const button = getByRole('button');
			expect((button as HTMLButtonElement).disabled).toBe(true);
			expect(getByTestId('loading-spinner')).toBeTruthy();
		});
	});

	describe('Accessibility', () => {
		it('has proper type attribute', () => {
			const { getByRole } = render(Button, {
				type: 'submit',
				text: 'Submit',
			});
			const button = getByRole('button');
			expect(button.getAttribute('type')).toBe('submit');
		});

		it('defaults to type="button"', () => {
			const { getByRole } = render(Button, { text: 'Click' });
			const button = getByRole('button');
			expect(button.getAttribute('type')).toBe('button');
		});

		it('accepts aria-label', () => {
			const { getByRole } = render(Button, {
				'aria-label': 'Close dialog',
				text: '×',
			});
			const button = getByRole('button');
			expect(button.getAttribute('aria-label')).toBe('Close dialog');
		});
	});

	describe('Events', () => {
		it('handles click events', async () => {
			let clicked = false;
			const { getByRole } = render(Button, {
				text: 'Click',
				onclick: () => {
					clicked = true;
				},
			});

			const button = getByRole('button');
			button.click();

			expect(clicked).toBe(true);
		});
	});
});
