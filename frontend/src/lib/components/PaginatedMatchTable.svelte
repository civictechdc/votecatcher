<script lang="ts">
	import MatchConfidenceIndicator from './MatchConfidenceIndicator.svelte';
	import type { ConfidenceThresholds } from '$lib/workspace-types';

	const PAGE_SIZE_OPTIONS = [20, 50, 100] as const;

	interface Column {
		name: string;
		label?: string;
		isScore?: boolean;
	}

	interface Props {
		rows?: Record<string, unknown>[];
		columns?: Column[];
		pageSize?: number;
		confidenceThreshold?: ConfidenceThresholds;
	}

	let {
		rows = [],
		columns = [],
		confidenceThreshold = { high: 95, medium: 90 } as ConfidenceThresholds
	}: Props = $props();

	let currentPage = $state(0);
	let pageSizeState = $state(PAGE_SIZE_OPTIONS[0]);

	let pageCount = $derived(Math.max(1, Math.ceil(rows.length / pageSizeState)));
	let start = $derived(currentPage * pageSizeState);
	let visibleRows = $derived(rows.slice(start, start + pageSizeState));
	let totalRows = $derived(rows.length);
	let startRow = $derived(totalRows === 0 ? 0 : start + 1);
	let endRow = $derived(Math.min(start + pageSizeState, totalRows));

	$effect(() => {
		if (pageSizeState) {
			currentPage = 0;
		}
	});

	function goto(page: number) {
		currentPage = Math.max(0, Math.min(page, pageCount - 1));
	}
</script>

<div class="w-full">
	<div class="overflow-auto rounded-md border">
		<table class="min-w-full table-auto text-sm">
			<thead class="sticky top-0 bg-slate-50">
				<tr>
					{#each columns as col}
						<th class="px-3 py-2 text-left font-medium text-slate-700">{col.label ?? col.name}</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#if visibleRows.length === 0}
					<tr><td class="p-4 text-center text-slate-500" colspan={columns.length}>No rows</td></tr>
				{:else}
					{#each visibleRows as row}
						<tr class="odd:bg-white even:bg-slate-50 hover:bg-slate-100">
							{#each columns as col}
								<td class="px-3 py-2 align-top">
									{#if col.isScore}
										<MatchConfidenceIndicator matchScore={row[col.name]} {confidenceThreshold} />
										<div class="mt-1 text-xs text-slate-500">{String(row[col.name])}</div>
									{:else}
										{row[col.name]}
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>

	<div class="mt-3 flex items-center justify-between">
		<div class="text-sm text-slate-500">
			{startRow}-{endRow} of {totalRows} rows
		</div>
		<div class="text-sm text-slate-600">
			<label for="page-size" class="mr-2">Rows per page:</label>
			<select id="page-size" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm focus:border-blue-500 focus:outline-none" bind:value={pageSizeState}>
				{#each PAGE_SIZE_OPTIONS as size}
					<option value={size}>{size}</option>
				{/each}
			</select>
		</div>
		<div class="flex items-center gap-1">
			<button
				class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
				onclick={() => goto(0)}
				disabled={currentPage === 0}>First</button
			>
			<button
				class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
				onclick={() => goto(currentPage - 1)}
				disabled={currentPage === 0}>Prev</button
			>
			<span class="px-2 text-sm text-slate-600">
				Page {currentPage + 1} of {pageCount}
			</span>
			<button
				class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
				onclick={() => goto(currentPage + 1)}
				disabled={currentPage >= pageCount - 1}>Next</button
			>
			<button
				class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
				onclick={() => goto(pageCount - 1)}
				disabled={currentPage >= pageCount - 1}>Last</button
			>
		</div>
	</div>
</div>

<style>
	thead.sticky {
		position: sticky;
		top: 0;
	}
</style>
