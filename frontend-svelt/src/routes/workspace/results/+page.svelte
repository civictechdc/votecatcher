<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { results } from '$lib/stores/results';
	import { Table, LoadingState, Button, ErrorDisplay } from '$lib/components/ui';
	import CsvExportButton from '$lib/components/results/CsvExportButton.svelte';
	import ConfidenceBadge from '$lib/components/results/ConfidenceBadge.svelte';

	let jobId = $derived(Number($page.url.searchParams.get('jobId') || 1));

	const columns = [
		{ key: 'extracted_text', label: 'Extracted Text', sortable: true },
		{ key: 'matched_name', label: 'Matched Name', sortable: true },
		{ key: 'score', label: 'Score', sortable: true },
		{ key: 'confidence', label: 'Confidence', sortable: true }
	];

	onMount(() => {
		results.fetchResults(jobId);
	});

	function getTableRows(resultList: typeof $results.results) {
		return resultList.map((result) => {
			const topPrediction = result.predictions[0];
			return {
				id: result.ocrResultId,
				extracted_text: result.extractedText || '-',
				matched_name: topPrediction?.voterName || '-',
				score: topPrediction?.similarityScore ? `${(topPrediction.similarityScore * 100).toFixed(1)}%` : '-',
				confidence: topPrediction?.confidence
					? `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(topPrediction.confidence)}">${topPrediction.confidence}</span>`
					: '-'
			};
		});
	}

	function getConfidenceColor(confidence: string): string {
		switch (confidence) {
			case 'HIGH': return 'bg-green-100 text-green-800';
			case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
			case 'LOW': return 'bg-red-100 text-red-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}

	function handlePrevious() {
		const newPage = Math.max(1, $results.page - 1);
		results.fetchResults(jobId, { page: newPage, pageSize: $results.pageSize });
	}

	function handleNext() {
		const newPage = $results.page + 1;
		results.fetchResults(jobId, { page: newPage, pageSize: $results.pageSize });
	}

	function handleRetry() {
		results.fetchResults(jobId);
	}

	let totalPages = $derived(Math.ceil($results.total / $results.pageSize));
	let startItem = $derived(($results.page - 1) * $results.pageSize + 1);
	let endItem = $derived(Math.min($results.page * $results.pageSize, $results.total));
</script>

<svelte:head>
	<title>Results — Votecatcher</title>
	<meta name="description" content="View signature matching results. Filter by confidence, export to CSV." />
</svelte:head>

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
		<ErrorDisplay message={$results.error} onRetry={handleRetry} />
	{:else if $results.results.length === 0}
		<div class="rounded-lg border border-slate-200 bg-white p-12 text-center">
			<p class="text-lg text-slate-600">No results found</p>
			<p class="mt-2 text-sm text-slate-500">Results will appear here after a job completes</p>
		</div>
	{:else}
		<div class="space-y-4">
			<Table
				columns={columns}
				rows={getTableRows($results.results)}
				sortable={true}
				emptyMessage="No results to display"
			/>

			{#if $results.total > 0}
				<div class="flex items-center justify-between border-t border-slate-200 px-4 py-3">
					<p class="text-sm text-slate-600">
						Showing {startItem} to {endItem} of {$results.total} results
					</p>
					<div class="flex gap-2">
						<Button
							variant="secondary"
							text="Previous"
							disabled={$results.page <= 1}
							onclick={handlePrevious}
						/>
						<Button
							variant="secondary"
							text="Next"
							disabled={$results.page >= totalPages}
							onclick={handleNext}
						/>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
