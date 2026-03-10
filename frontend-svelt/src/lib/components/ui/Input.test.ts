import { describe, it, expect } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import Input from './Input.svelte';

describe('Input Component', () => {
	describe('Rendering', () => {
		it('renders with default type text', () => {
			const { getByRole } = render(Input, { props: { id: 'test-input' } });
			const input = getByRole('textbox');
			expect(input).toBeTruthy();
			expect(input.getAttribute('type')).toBe('text');
		});

		it('renders with different types', () => {
			const types = ['text', 'email', 'password', 'number'] as const;
			types.forEach((type) => {
				const { getByLabelText } = render(Input, {
					props: { id: `test-${type}`, type, label: `${type} input` }
				});
				const input = getByLabelText(`${type} input`);
				expect(input.getAttribute('type')).toBe(type);
			});
		});

		it('renders file input', () => {
			const { getByLabelText } = render(Input, {
				props: { id: 'file-input', type: 'file', label: 'Upload file' }
			});
			const input = getByLabelText('Upload file');
			expect(input.getAttribute('type')).toBe('file');
		});
	});

	describe('Labels and Helper Text', () => {
		it('renders with label', () => {
			const { getByLabelText } = render(Input, {
				props: { id: 'email', label: 'Email Address' }
			});
			const input = getByLabelText('Email Address');
			expect(input).toBeTruthy();
		});

		it('renders with helper text', () => {
			const { getByText } = render(Input, {
				props: { id: 'password', helperText: 'Must be 8+ characters' }
			});
			expect(getByText('Must be 8+ characters')).toBeTruthy();
		});

		it('associates helper text with input via aria-describedby', () => {
			const { getByLabelText } = render(Input, {
				props: { id: 'password', helperText: 'Must be 8+ characters', label: 'Password' }
			});
			const input = getByLabelText('Password');
			expect(input.getAttribute('aria-describedby')).toBe('password-helper');
		});
	});

	describe('States', () => {
		it('renders as disabled', () => {
			const { getByRole } = render(Input, {
				props: { id: 'disabled-input', disabled: true }
			});
			const input = getByRole('textbox');
			expect(input.hasAttribute('disabled')).toBe(true);
		});

		it('renders as readonly', () => {
			const { getByRole } = render(Input, {
				props: { id: 'readonly-input', readonly: true }
			});
			const input = getByRole('textbox');
			expect(input.hasAttribute('readonly')).toBe(true);
		});

		it('renders with error state', () => {
			const { getByRole } = render(Input, {
				props: { id: 'error-input', error: true }
			});
			const input = getByRole('textbox');
			expect(input.getAttribute('aria-invalid')).toBe('true');
		});

		it('renders with error message', () => {
			const { getByText } = render(Input, {
				props: { id: 'error-input', error: true, errorMessage: 'Invalid email format' }
			});
			expect(getByText('Invalid email format')).toBeTruthy();
		});
	});

	describe('Accessibility', () => {
		it('has proper id and name attributes', () => {
			const { getByRole } = render(Input, {
				props: { id: 'test-input', name: 'username' }
			});
			const input = getByRole('textbox');
			expect(input.getAttribute('id')).toBe('test-input');
			expect(input.getAttribute('name')).toBe('username');
		});

		it('uses id as name if name not provided', () => {
			const { getByRole } = render(Input, {
				props: { id: 'test-input' }
			});
			const input = getByRole('textbox');
			expect(input.getAttribute('name')).toBe('test-input');
		});

		it('sets aria-invalid when error is true', () => {
			const { getByRole } = render(Input, {
				props: { id: 'email', error: true }
			});
			const input = getByRole('textbox');
			expect(input.getAttribute('aria-invalid')).toBe('true');
		});

		it('associates error message with input', () => {
			const { getByLabelText } = render(Input, {
				props: { id: 'email', label: 'Email', error: true, errorMessage: 'Invalid format' }
			});
			const input = getByLabelText('Email');
			expect(input.getAttribute('aria-errormessage')).toBe('email-error');
		});
	});

	describe('Events', () => {
		it('handles input events', async () => {
			const { getByRole } = render(Input, { props: { id: 'test' } });
			const input = getByRole('textbox') as HTMLInputElement;
			await fireEvent.input(input, { target: { value: 'test@example.com' } });
			expect(input.value).toBe('test@example.com');
		});

		it('handles change events', async () => {
			const { getByRole } = render(Input, { props: { id: 'test' } });
			const input = getByRole('textbox') as HTMLInputElement;
			await fireEvent.change(input, { target: { value: 'new value' } });
			expect(input.value).toBe('new value');
		});
	});

	describe('Placeholder', () => {
		it('renders with placeholder', () => {
			const { getByPlaceholderText } = render(Input, {
				props: { id: 'search', placeholder: 'Search...' }
			});
			expect(getByPlaceholderText('Search...')).toBeTruthy();
		});
	});

	describe('Required Field', () => {
		it('renders with required attribute', () => {
			const { getByRole } = render(Input, {
				props: { id: 'required-input', required: true }
			});
			const input = getByRole('textbox');
			expect(input.hasAttribute('required')).toBe(true);
		});

		it('shows required indicator in label', () => {
			const { getByText } = render(Input, {
				props: { id: 'required-input', label: 'Email', required: true }
			});
			expect(getByText('*')).toBeTruthy();
		});
	});

	describe('Value Binding', () => {
		it('renders with initial value', () => {
			const { getByRole } = render(Input, {
				props: { id: 'test', value: 'initial value' }
			});
			const input = getByRole('textbox') as HTMLInputElement;
			expect(input.value).toBe('initial value');
		});
	});
});
