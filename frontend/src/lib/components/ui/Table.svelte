<script lang="ts">
	import { cn } from '$lib/utils/cn';
	import Pagination from './Pagination.svelte';

	export interface Column {
		key: string;
		label: string;
		sortable?: boolean;
	}

	export interface SortConfig {
		key: string;
		direction: 'asc' | 'desc';
	}

	interface Props {
		columns: Column[];
		rows: Record<string, unknown>[];
		rowKey?: string;
		sortable?: boolean;
		sortConfig?: SortConfig | null;
		loading?: boolean;
		emptyMessage?: string;
		selectable?: boolean;
		selectedRows?: (string | number)[];
		pagination?: boolean;
		totalItems?: number;
		pageSize?: number;
		currentPage?: number;
		ariaLabel?: string;
		class?: string;
		onSortChange?: (config: SortConfig) => void;
		onSelectionChange?: (selectedIds: (string | number)[]) => void;
		onPageChange?: (page: number) => void;
		onPageSizeChange?: (size: number) => void;
	}

	let {
		columns,
		rows,
		rowKey = 'id',
		sortable = false,
		sortConfig = null,
		loading = false,
		emptyMessage = 'No results found',
		selectable = false,
		selectedRows = [],
		pagination = false,
		totalItems = 0,
		pageSize = 10,
		currentPage = 1,
		ariaLabel = 'Data table',
		class: className,
		onSortChange,
		onSelectionChange,
		onPageChange,
		onPageSizeChange
	}: Props = $props();

	const effectiveColumns = $derived(
		selectable ? [{ key: '__select__', label: '', sortable: false }, ...columns] : columns
	);

	const allSelected = $derived(
		selectable && rows.length > 0 && selectedRows.length === rows.length
	);

	const someSelected = $derived(
		selectable && selectedRows.length > 0 && selectedRows.length < rows.length
	);

	function getAriaSort(column: Column): 'ascending' | 'descending' | 'none' | undefined {
		if (!sortable || !column.sortable) return undefined;
		if (!sortConfig || sortConfig.key !== column.key) return 'none';
		return sortConfig.direction === 'asc' ? 'ascending' : 'descending';
	}

	function handleHeaderClick(column: Column) {
		if (!sortable || !column.sortable || !onSortChange) return;

		if (sortConfig && sortConfig.key === column.key) {
			onSortChange({
				key: column.key,
				direction: sortConfig.direction === 'asc' ? 'desc' : 'asc'
			});
		} else {
			onSortChange({ key: column.key, direction: 'asc' });
		}
	}

	function handleSelectAll() {
		if (!onSelectionChange) return;

		if (allSelected) {
			onSelectionChange([]);
		} else {
			onSelectionChange(rows.map((row) => row[rowKey] as string | number));
		}
	}

	function handleRowSelect(rowId: string | number) {
		if (!onSelectionChange) return;

		if (selectedRows.includes(rowId)) {
			onSelectionChange(selectedRows.filter((id) => id !== rowId));
		} else {
			onSelectionChange([...selectedRows, rowId]);
		}
	}

	function handleKeyDown(event: KeyboardEvent, column: Column) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleHeaderClick(column);
		}
	}
</script>

<div class={cn('w-full', className)}>
	<div class="overflow-x-auto rounded-lg border border-gray-200">
		<table
			role="grid"
			aria-label={ariaLabel}
			class="w-full text-sm text-left text-gray-700"
		>
			<thead class="text-xs text-gray-700 uppercase bg-gray-50 border-b border-gray-200">
				<tr>
					{#each effectiveColumns as column}
						<th
							role="columnheader"
							scope="col"
							aria-sort={getAriaSort(column)}
							class={cn(
								'px-4 py-3 font-semibold',
								sortable && column.sortable && 'cursor-pointer hover:bg-gray-100 select-none',
								column.key === '__select__' && 'w-12'
							)}
							onclick={() => handleHeaderClick(column)}
							onkeydown={(e) => handleKeyDown(e, column)}
							tabindex={sortable && column.sortable ? 0 : undefined}
						>
							{#if column.key === '__select__'}
								{#if selectable}
									<input
										type="checkbox"
										aria-label="Select all rows"
										checked={allSelected}
										indeterminate={someSelected}
										onchange={handleSelectAll}
										class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
									/>
								{/if}
							{:else}
								<div class="flex items-center gap-2">
									<span>{column.label}</span>
									{#if sortable && column.sortable}
										<span class="text-gray-400" aria-hidden="true">
											{#if sortConfig && sortConfig.key === column.key}
												{#if sortConfig.direction === 'asc'}
													<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
													</svg>
												{:else}
													<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
													</svg>
												{/if}
											{:else}
												<svg class="w-4 h-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
												</svg>
											{/if}
										</span>
									{/if}
								</div>
							{/if}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody class="bg-white divide-y divide-gray-200">
				{#if loading}
					<tr>
						<td colspan={effectiveColumns.length} class="px-4 py-8 text-center">
							<div data-testid="table-loading" class="flex flex-col items-center gap-3">
								<svg
									class="animate-spin h-8 w-8 text-blue-600"
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									aria-label="Loading"
								>
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
								</svg>
								<span class="text-gray-500">Loading...</span>
							</div>
						</td>
					</tr>
				{:else if rows.length === 0}
					<tr>
						<td colspan={effectiveColumns.length} class="px-4 py-8 text-center text-gray-500">
							{emptyMessage}
						</td>
					</tr>
				{:else}
					{#each rows as row}
						{@const rowId = row[rowKey] as string | number}
						<tr class="hover:bg-gray-50 transition-colors">
							{#if selectable}
								<td role="gridcell" class="px-4 py-3">
									<input
										type="checkbox"
										aria-label="Select row"
										checked={selectedRows.includes(rowId)}
										onchange={() => handleRowSelect(rowId)}
										class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
									/>
								</td>
							{/if}
							{#each columns as column}
								<td role="gridcell" class="px-4 py-3">
									{@html row[column.key]?.toString() ?? ''}
								</td>
							{/each}
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>

	{#if pagination && !loading && rows.length > 0}
		<Pagination
			{totalItems}
			{pageSize}
			{currentPage}
			onPageChange={onPageChange ?? (() => {})}
			onPageSizeChange={onPageSizeChange ?? (() => {})}
		/>
	{/if}
</div>
