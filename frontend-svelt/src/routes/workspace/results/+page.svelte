<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { results } from '$lib/stores/results';
	import { Table, LoadingState, Button } from '$lib/components/ui';
	import CsvExportButton from '$lib/components/results/CsvExportButton.svelte';
	import ConfidenceBadge from '$lib/components/results/ConfidenceBadge.svelte';

	$: jobId = Number($page.url.searchParams.get('jobId') || 1);

	const columns = [
		{ key: 'prediction_1_name', label: 'Matched Name', sortable: true },
		{ key: 'prediction_1_score', label: 'Score', sortable: true },
		{ key: 'confidence_level', label: 'Confidence', sortable: true }
	];

	onMount(() => {
		results.fetchResults(jobId);
	});
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold text-slate-900">Results</h1>
			<p class="mt-2 text-slate-600">Matched signatures for job #{jobId}</p>
		</div>
		<CsvExportButton {jobId} />
	</div>

	{#if $results.loading}
		<LoadingState loading={true} />
	{:else if $results.error}
		<LoadingState error={$results.error} />
	{:else if $results.results.length === 0}
		<div class="rounded-lg border border-slate-200 bg-white p-12 text-center">
			<p class="text-lg text-slate-600">No results found</p>
			<p class="mt-2 text-sm text-slate-500">Results will appear here after a job completes</p>
		</div>
	{:else}
		<div class="space-y-4">
			<Table
				{columns}
				rows={$results.results}
				sortable={true}
				emptyMessage="No results to display"
			/>

			<div class="flex items-center justify-between border-t border-slate-200 px-4 py-3">
				<p class="text-sm text-slate-600">
					Showing {$results.offset + 1} to {Math.min($results.offset + $results.limit, $results.total)} of {$results.total} results
				</p>
				<div class="flex gap-2">
					<Button
						variant="secondary"
						size="sm"
						disabled={$results.offset === 0}
						onclick={() => results.fetchResults(jobId, { offset: Math.max(0, $results.offset - $results.limit) })}
					>
						Previous
					</Button>
					<Button
						variant="secondary"
						size="sm"
						disabled={$results.offset + $results.limit >= $results.total}
						onclick={() => results.fetchResults(jobId, { offset: $results.offset + $results.limit })}
					>
						Next
					</Button>
				</div>
			</div>
		</div>
	{/if}
</div>
