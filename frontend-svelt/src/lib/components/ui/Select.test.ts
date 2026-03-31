import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import Select from './Select.svelte';

const defaultOptions = [
	{ value: 'high', label: 'High' },
	{ value: 'medium', label: 'Medium' },
	{ value: 'low', label: 'Low' },
];

describe('Select Component', () => {
	describe('Rendering', () => {
		it('renders with trigger button', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});
			const combobox = getByRole('combobox');
			expect(combobox).toBeTruthy();
		});

		it('renders with label', () => {
			const { getByLabelText } = render(Select, {
				props: { id: 'priority', label: 'Priority', options: defaultOptions },
			});
			const combobox = getByLabelText('Priority');
			expect(combobox).toBeTruthy();
		});

		it('renders with placeholder text', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, placeholder: 'Select an option' },
			});
			const combobox = getByRole('combobox');
			expect(combobox.textContent).toContain('Select an option');
		});

		it('renders with helper text', () => {
			const { getByText } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, helperText: 'Choose wisely' },
			});
			expect(getByText('Choose wisely')).toBeTruthy();
		});

		it('displays selected value label in trigger', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, value: 'medium' },
			});
			const combobox = getByRole('combobox');
			expect(combobox.textContent).toContain('Medium');
		});
	});

	describe('Dropdown Behavior', () => {
		it('opens dropdown on click', async () => {
			const { getByRole, queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			expect(queryByRole('listbox')).toBeNull();

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			expect(queryByRole('listbox')).toBeTruthy();
		});

		it('closes dropdown when clicking outside', async () => {
			const { getByRole, queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);
			expect(queryByRole('listbox')).toBeTruthy();

			await fireEvent.click(document.body);
			expect(queryByRole('listbox')).toBeNull();
		});

		it('shows all options when open', async () => {
			const { getByRole, getAllByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const options = getAllByRole('option');
			expect(options).toHaveLength(3);
		});
	});

	describe('Selection', () => {
		it('selects an option on click', async () => {
			const onValueChange = vi.fn();
			const { getByRole, getAllByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, onValueChange },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const options = getAllByRole('option');
			await fireEvent.click(options[1]);

			expect(onValueChange).toHaveBeenCalledWith('medium');
		});

		it('closes dropdown after selection', async () => {
			const { getByRole, getAllByRole, queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const options = getAllByRole('option');
			await fireEvent.click(options[0]);

			expect(queryByRole('listbox')).toBeNull();
		});

		it('shows checkmark on selected option', async () => {
			const { getByRole, getAllByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, value: 'high' },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const options = getAllByRole('option');
			expect(options[0].getAttribute('aria-selected')).toBe('true');
		});
	});

	describe('Keyboard Navigation', () => {
		it('opens dropdown with Enter key', async () => {
			const { getByRole, queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.focus(combobox);
			await fireEvent.keyDown(combobox, { key: 'Enter' });

			expect(queryByRole('listbox')).toBeTruthy();
		});

		it('opens dropdown with Space key', async () => {
			const { getByRole, queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.focus(combobox);
			await fireEvent.keyDown(combobox, { key: ' ' });

			expect(queryByRole('listbox')).toBeTruthy();
		});

		it('closes dropdown with Escape key', async () => {
			const { getByRole, queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);
			expect(queryByRole('listbox')).toBeTruthy();

			await fireEvent.keyDown(combobox, { key: 'Escape' });
			expect(queryByRole('listbox')).toBeNull();
		});

		it('navigates options with arrow keys', async () => {
			const { getByRole, getAllByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			await fireEvent.keyDown(combobox, { key: 'ArrowDown' });
			const options = getAllByRole('option');
			expect(options[0].getAttribute('data-highlighted')).toBe('true');

			await fireEvent.keyDown(combobox, { key: 'ArrowDown' });
			expect(options[1].getAttribute('data-highlighted')).toBe('true');
		});

		it('selects highlighted option with Enter', async () => {
			const onValueChange = vi.fn();
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, onValueChange },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			await fireEvent.keyDown(combobox, { key: 'ArrowDown' });
			await fireEvent.keyDown(combobox, { key: 'ArrowDown' });
			await fireEvent.keyDown(combobox, { key: 'Enter' });

			expect(onValueChange).toHaveBeenCalledWith('medium');
		});
	});

	describe('States', () => {
		it('renders as disabled', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, disabled: true },
			});
			const combobox = getByRole('combobox');
			expect(combobox.hasAttribute('disabled')).toBe(true);
		});

		it('does not open dropdown when disabled', async () => {
			const { getByRole, queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, disabled: true },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			expect(queryByRole('listbox')).toBeNull();
		});

		it('renders with error state', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, error: true },
			});
			const combobox = getByRole('combobox');
			expect(combobox.getAttribute('aria-invalid')).toBe('true');
		});

		it('renders with error message', () => {
			const { getByText } = render(Select, {
				props: {
					id: 'test-select',
					options: defaultOptions,
					error: true,
					errorMessage: 'This field is required',
				},
			});
			expect(getByText('This field is required')).toBeTruthy();
		});

		it('applies error styling to trigger', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, error: true },
			});
			const combobox = getByRole('combobox');
			expect(combobox.classList.contains('border-red-500')).toBe(true);
		});
	});

	describe('Accessibility', () => {
		it('has proper aria-expanded attribute', async () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			expect(combobox.getAttribute('aria-expanded')).toBe('false');

			await fireEvent.click(combobox);
			expect(combobox.getAttribute('aria-expanded')).toBe('true');
		});

		it('has proper aria-controls attribute', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			expect(combobox.getAttribute('aria-controls')).toBe('test-select-listbox');
		});

		it('has proper aria-haspopup attribute', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			expect(combobox.getAttribute('aria-haspopup')).toBe('listbox');
		});

		it('listbox has proper aria-label', async () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, label: 'Priority' },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const listbox = getByRole('listbox');
			expect(listbox.getAttribute('aria-label')).toBe('Priority options');
		});

		it('options have proper role and value', async () => {
			const { getByRole, getAllByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const options = getAllByRole('option');
			expect(options[0].getAttribute('data-value')).toBe('high');
			expect(options[1].getAttribute('data-value')).toBe('medium');
			expect(options[2].getAttribute('data-value')).toBe('low');
		});
	});

	describe('Search/Filter', () => {
		it('filters options when searchable', async () => {
			const { getByRole, getAllByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, searchable: true },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const searchInput = getByRole('textbox');
			await fireEvent.input(searchInput, { target: { value: 'hi' } });

			const options = getAllByRole('option');
			expect(options).toHaveLength(1);
			expect(options[0].textContent).toContain('High');
		});

		it('shows no results message when filter has no matches', async () => {
			const { getByRole, getByText } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, searchable: true },
			});

			const combobox = getByRole('combobox');
			await fireEvent.click(combobox);

			const searchInput = getByRole('textbox');
			await fireEvent.input(searchInput, { target: { value: 'xyz' } });

			expect(getByText('No options found')).toBeTruthy();
		});
	});

	describe('Clear Button', () => {
		it('shows clear button when value is selected and clearable is true', () => {
			const { getByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, value: 'high', clearable: true },
			});

			expect(getByRole('button', { name: /clear/i })).toBeTruthy();
		});

		it('clears selection when clear button is clicked', async () => {
			const onValueChange = vi.fn();
			const { getByRole } = render(Select, {
				props: {
					id: 'test-select',
					options: defaultOptions,
					value: 'high',
					clearable: true,
					onValueChange,
				},
			});

			const clearButton = getByRole('button', { name: /clear/i });
			await fireEvent.click(clearButton);

			expect(onValueChange).toHaveBeenCalledWith(undefined);
		});

		it('does not show clear button when clearable is false', () => {
			const { queryByRole } = render(Select, {
				props: { id: 'test-select', options: defaultOptions, value: 'high', clearable: false },
			});

			expect(queryByRole('button', { name: /clear/i })).toBeNull();
		});
	});
});
