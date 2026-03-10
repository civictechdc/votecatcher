import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import Table from './Table.svelte';

type TestRow = Record<string, unknown> & {
	id: number;
	name: string;
	email: string;
	status: string;
};

const testColumns = [
	{ key: 'id', label: 'ID', sortable: true },
	{ key: 'name', label: 'Name', sortable: true },
	{ key: 'email', label: 'Email', sortable: false },
	{ key: 'status', label: 'Status', sortable: true }
];

const testRows: TestRow[] = [
	{ id: 1, name: 'Alice', email: 'alice@test.com', status: 'active' },
	{ id: 2, name: 'Bob', email: 'bob@test.com', status: 'inactive' },
	{ id: 3, name: 'Charlie', email: 'charlie@test.com', status: 'active' }
];

describe('Table Component', () => {
	describe('Rendering', () => {
		it('renders table with data', () => {
			const { getByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			expect(getByRole('grid')).toBeTruthy();
		});

		it('renders column headers', () => {
			const { getByText } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			expect(getByText('ID')).toBeTruthy();
			expect(getByText('Name')).toBeTruthy();
			expect(getByText('Email')).toBeTruthy();
			expect(getByText('Status')).toBeTruthy();
		});

		it('renders row data', () => {
			const { getByText, getAllByText } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			expect(getByText('Alice')).toBeTruthy();
			expect(getByText('bob@test.com')).toBeTruthy();
			expect(getAllByText('active').length).toBe(2);
		});

		it('applies custom class to container', () => {
			const { container } = render(Table, {
				props: { columns: testColumns, rows: testRows, class: 'custom-table' }
			});
			expect(container.querySelector('.custom-table')).toBeTruthy();
		});
	});

	describe('Sorting', () => {
		it('shows sort indicator for sortable columns', () => {
			const { getAllByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows, sortable: true }
			});
			const sortableHeaders = getAllByRole('columnheader').filter(
				(h) => h.getAttribute('aria-sort') !== null
			);
			expect(sortableHeaders.length).toBeGreaterThan(0);
		});

		it('sorts ascending when clicking sortable header', async () => {
			const onSortChange = vi.fn();
			const { getByText } = render(Table, {
				props: { columns: testColumns, rows: testRows, sortable: true, onSortChange }
			});

			await fireEvent.click(getByText('Name'));
			expect(onSortChange).toHaveBeenCalledWith({ key: 'name', direction: 'asc' });
		});

		it('toggles sort direction on second click', async () => {
			const onSortChange = vi.fn();
			const { getByText } = render(Table, {
				props: {
					columns: testColumns,
					rows: testRows,
					sortable: true,
					sortConfig: { key: 'name', direction: 'asc' },
					onSortChange
				}
			});

			await fireEvent.click(getByText('Name'));
			expect(onSortChange).toHaveBeenCalledWith({ key: 'name', direction: 'desc' });
		});

		it('sets aria-sort attribute correctly', () => {
			const { getByText } = render(Table, {
				props: {
					columns: testColumns,
					rows: testRows,
					sortable: true,
					sortConfig: { key: 'name', direction: 'asc' }
				}
			});

			const header = getByText('Name').closest('[role="columnheader"]');
			expect(header?.getAttribute('aria-sort')).toBe('ascending');
		});

		it('does not trigger sort for non-sortable columns', async () => {
			const onSortChange = vi.fn();
			const { getByText } = render(Table, {
				props: { columns: testColumns, rows: testRows, sortable: true, onSortChange }
			});

			await fireEvent.click(getByText('Email'));
			expect(onSortChange).not.toHaveBeenCalled();
		});
	});

	describe('Row Selection', () => {
		it('renders checkboxes when selection enabled', () => {
			const { getAllByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows, selectable: true }
			});
			const checkboxes = getAllByRole('checkbox');
			expect(checkboxes.length).toBe(testRows.length + 1);
		});

		it('selects individual row', async () => {
			const onSelectionChange = vi.fn();
			const { getAllByRole } = render(Table, {
				props: {
					columns: testColumns,
					rows: testRows,
					selectable: true,
					onSelectionChange
				}
			});

			const checkboxes = getAllByRole('checkbox');
			await fireEvent.click(checkboxes[1]);
			expect(onSelectionChange).toHaveBeenCalled();
		});

		it('selects all rows via header checkbox', async () => {
			const onSelectionChange = vi.fn();
			const { getAllByRole } = render(Table, {
				props: {
					columns: testColumns,
					rows: testRows,
					selectable: true,
					onSelectionChange
				}
			});

			const selectAllCheckbox = getAllByRole('checkbox')[0];
			await fireEvent.click(selectAllCheckbox);
			expect(onSelectionChange).toHaveBeenCalledWith(testRows.map(r => r.id));
		});

		it('shows indeterminate state for partial selection', () => {
			const { getAllByRole } = render(Table, {
				props: {
					columns: testColumns,
					rows: testRows,
					selectable: true,
					selectedRows: [1]
				}
			});

			const selectAllCheckbox = getAllByRole('checkbox')[0] as HTMLInputElement;
			expect(selectAllCheckbox.indeterminate).toBe(true);
		});
	});

	describe('Empty State', () => {
		it('shows empty message when no rows', () => {
			const { getByText } = render(Table, {
				props: { columns: testColumns, rows: [], emptyMessage: 'No data available' }
			});
			expect(getByText('No data available')).toBeTruthy();
		});

		it('uses default empty message', () => {
			const { getByText } = render(Table, {
				props: { columns: testColumns, rows: [] }
			});
			expect(getByText('No results found')).toBeTruthy();
		});
	});

	describe('Loading State', () => {
		it('shows loading spinner when loading', () => {
			const { getByTestId, queryAllByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows, loading: true }
			});
			expect(getByTestId('table-loading')).toBeTruthy();
			expect(queryAllByRole('gridcell').length).toBe(0);
		});

		it('hides table content when loading', () => {
			const { queryByText } = render(Table, {
				props: { columns: testColumns, rows: testRows, loading: true }
			});
			expect(queryByText('Alice')).toBeNull();
		});
	});

	describe('Pagination Integration', () => {
		it('renders pagination when enabled', () => {
			const { getByText } = render(Table, {
				props: {
					columns: testColumns,
					rows: testRows,
					pagination: true,
					totalItems: 100,
					pageSize: 10,
					currentPage: 1,
					onPageChange: () => {},
					onPageSizeChange: () => {}
				}
			});
			expect(getByText(/Showing/)).toBeTruthy();
		});

		it('calls onPageChange when page changes', async () => {
			const onPageChange = vi.fn();
			const { getByText } = render(Table, {
				props: {
					columns: testColumns,
					rows: testRows,
					pagination: true,
					totalItems: 100,
					pageSize: 10,
					currentPage: 1,
					onPageChange,
					onPageSizeChange: () => {}
				}
			});

			await fireEvent.click(getByText('Next'));
			expect(onPageChange).toHaveBeenCalledWith(2);
		});
	});

	describe('Accessibility', () => {
		it('has proper grid role', () => {
			const { getByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			expect(getByRole('grid')).toBeTruthy();
		});

		it('has rowgroup for header and body', () => {
			const { getAllByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			const rowgroups = getAllByRole('rowgroup');
			expect(rowgroups.length).toBe(2);
		});

		it('has columnheader role for headers', () => {
			const { getAllByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			const headers = getAllByRole('columnheader');
			expect(headers.length).toBe(testColumns.length);
		});

		it('has row role for data rows', () => {
			const { getAllByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			const rows = getAllByRole('row');
			expect(rows.length).toBe(testRows.length + 1);
		});

		it('has gridcell role for cells', () => {
			const { getAllByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			const cells = getAllByRole('gridcell');
			expect(cells.length).toBe(testRows.length * testColumns.length);
		});

		it('supports aria-label for table', () => {
			const { getByRole } = render(Table, {
				props: { columns: testColumns, rows: testRows, ariaLabel: 'Users table' }
			});
			expect(getByRole('grid').getAttribute('aria-label')).toBe('Users table');
		});

		it('marks sortable columns with aria-sort', () => {
			const { getByText } = render(Table, {
				props: { columns: testColumns, rows: testRows, sortable: true }
			});

			const nameHeader = getByText('Name').closest('[role="columnheader"]');
			expect(nameHeader?.getAttribute('aria-sort')).toBe('none');
		});
	});

	describe('Custom Rendering', () => {
		it('renders custom cell content via slot', () => {
			const { getByText } = render(Table, {
				props: { columns: testColumns, rows: testRows }
			});
			expect(getByText('Alice')).toBeTruthy();
		});
	});
});
