<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { campaignResults, sortResults, renderThumbnailCell, renderPredictionsTable, renderExpandedCropImage, toggleAccordion, escapeHtml, getConfidenceBadgeClass, type CampaignResultResponse } from '$lib/stores/campaign-results';
	import { campaigns } from '$lib/stores/campaigns';
	import { Table, LoadingState, Button, ErrorDisplay } from '$lib/components/ui';
	import CropLightbox from '$lib/components/results/CropLightbox.svelte';
	import type { SortConfig } from '$lib/components/ui/Table.svelte';

	let campaignId = $derived($page.params.id ?? '');
	let sortConfig = $state<SortConfig | null>(null);
	let expandedRowId = $state<number | null>(null);
	let lightboxUrl = $state<string | null>(null);

	const columns = [
		{ key: 'thumbnail', label: 'Crop', sortable: false },
		{ key: 'confidence', label: 'Confidence', sortable: true },
		{ key: 'extracted_name', label: 'Extracted Name', sortable: true },
		{ key: 'matched_name', label: 'Matched Name', sortable: true },
		{ key: 'extracted_address', label: 'Extracted Address', sortable: true },
		{ key: 'matched_address', label: 'Matched Address', sortable: true },
		{ key: 'score', label: 'Score', sortable: true }
	];

	onMount(() => {
		campaignResults.fetchResults(campaignId);
		campaigns.fetchAll();
	});

	const sortedResults = $derived(sortResults($campaignResults.results, sortConfig));

	function getTableRows(resultList: CampaignResultResponse[]) {
		return resultList.map((result) => {
			const topPrediction = result.predictions[0];
			return {
				id: result.ocrResultId,
				thumbnail: renderThumbnailCell(result.thumbnailUrl),
				confidence: topPrediction?.confidence
					? `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceBadgeClass(topPrediction.confidence)}">${topPrediction.confidence}</span>`
					: '-',
				extracted_name: escapeHtml(result.extractedName || '-'),
				extracted_address: escapeHtml(result.extractedAddress || '-'),
				matched_name: escapeHtml(topPrediction?.voterName || '-'),
				matched_address: escapeHtml(topPrediction?.voterAddress || '-'),
				score: topPrediction?.similarityScore ? `${(topPrediction.similarityScore * 100).toFixed(1)}%` : '-'
			};
		});
	}

	function handleRowClick(rowId: string | number) {
		expandedRowId = toggleAccordion(expandedRowId, rowId as number);
	}

	function handleCropClick(url: string, e: MouseEvent) {
		e.stopPropagation();
		lightboxUrl = url;
	}

	function closeLightbox() {
		lightboxUrl = null;
	}

	function handlePrevious() {
		const newPage = Math.max(1, $campaignResults.page - 1);
		campaignResults.fetchResults(campaignId, { page: newPage, pageSize: $campaignResults.pageSize });
	}

	function handleNext() {
		const newPage = $campaignResults.page + 1;
		campaignResults.fetchResults(campaignId, { page: newPage, pageSize: $campaignResults.pageSize });
	}

	function handleRetry() {
		campaignResults.fetchResults(campaignId);
	}

	let totalPages = $derived(Math.ceil($campaignResults.total / $campaignResults.pageSize));
	let startItem = $derived(($campaignResults.page - 1) * $campaignResults.pageSize + 1);
	let endItem = $derived(Math.min($campaignResults.page * $campaignResults.pageSize, $campaignResults.total));

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));

	function getExpandedResult(rowId: string | number): CampaignResultResponse | undefined {
		return sortedResults.find((r) => r.ocrResultId === Number(rowId));
	}
</script>

<svelte:head>
	<title>Results — {campaign?.uniqueName || campaign?.title || 'Campaign'} — Votecatcher</title>
	<meta name="description" content="View signature matching results for this campaign." />
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold text-slate-900">Results</h1>
			<p class="mt-1 text-slate-600">{campaign?.uniqueName || campaign?.title || 'Campaign'}</p>
		</div>
	</div>

	{#if $campaignResults.loading || !$campaignResults.initialized}
		<LoadingState loading={true} />
	{:else if $campaignResults.error}
		<ErrorDisplay message={$campaignResults.error} onRetry={handleRetry} />
	{:else if $campaignResults.results.length === 0}
		<div class="rounded-lg border border-slate-200 bg-white p-12 text-center">
			<p class="text-lg text-slate-600">No results found</p>
			<p class="mt-2 text-sm text-slate-500">Results will appear here after a job completes</p>
		</div>
	{:else}
		<div class="space-y-4">
			<div class="overflow-x-auto rounded-lg border border-slate-200">
				<div class="min-w-max">
					<Table
						columns={columns}
						rows={getTableRows(sortedResults)}
						sortable={true}
						sortConfig={sortConfig}
						onSortChange={(config) => (sortConfig = config)}
						onRowClick={handleRowClick}
						expandedRowId={expandedRowId}
						emptyMessage="No results to display"
					>
						{#snippet expandedRowContent(row)}
							{@const result = getExpandedResult(row['id'] as string | number)}
							{#if result}
								<div class="flex gap-6">
								{#if result.thumbnailUrl}
								<div class="shrink-0" role="button" tabindex="0" aria-label="Open full-size crop image" onclick={(e) => {
									const target = e.target as HTMLElement;
									const url = target.getAttribute('data-crop-url') || target.closest('[data-crop-url]')?.getAttribute('data-crop-url');
									if (url) handleCropClick(url, e);
								}}
								onkeydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') {
										e.preventDefault();
										const target = e.target as HTMLElement;
										const url = target.getAttribute('data-crop-url') || target.closest('[data-crop-url]')?.getAttribute('data-crop-url');
										if (url) lightboxUrl = url;
									}
								}}>
										{@html renderExpandedCropImage(result.thumbnailUrl)}
									</div>
								{/if}
									<div class="flex-1 min-w-0">
										<h4 class="text-sm font-semibold text-slate-700 mb-2">Predictions</h4>
										{@html renderPredictionsTable(result.predictions)}
									</div>
								</div>
							{/if}
						{/snippet}
					</Table>
				</div>
			</div>

			{#if $campaignResults.total > 0}
				<div class="flex items-center justify-between border-t border-slate-200 px-4 py-3">
					<p class="text-sm text-slate-600">
						Showing {startItem} to {endItem} of {$campaignResults.total} results
					</p>
					<div class="flex gap-2">
						<Button
							variant="secondary"
							text="Previous"
							disabled={$campaignResults.page <= 1}
							onclick={handlePrevious}
						/>
						<Button
							variant="secondary"
							text="Next"
							disabled={$campaignResults.page >= totalPages}
							onclick={handleNext}
						/>
					</div>
				</div>
			{/if}
		</div>
	{/if}

	<CropLightbox
		open={lightboxUrl !== null}
		imageUrl={lightboxUrl ?? ''}
		onClose={closeLightbox}
	/>
</div>
