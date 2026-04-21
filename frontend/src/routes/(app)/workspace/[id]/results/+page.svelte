<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { campaignResults, sortResults, renderThumbnailCell, renderPredictionsTable, renderExpandedCropImage, toggleAccordion, escapeHtml, getConfidenceBadgeClass, getScanPageUrl, type CampaignResultResponse } from '$lib/stores/campaign-results';
	import { campaigns } from '$lib/stores/campaigns';
	import { Table, LoadingState, Button, ErrorDisplay } from '$lib/components/ui';
	import CropLightbox from '$lib/components/results/CropLightbox.svelte';
	import type { SortConfig } from '$lib/components/ui/Table.svelte';

	let campaignId = $derived($page.params.id ?? '');
	let sortConfig = $state<SortConfig | null>(null);
	let expandedRowId = $state<number | null>(null);
	let lightboxUrl = $state<string | null>(null);
	let lightboxClip = $state<{ top: number; bottom: number } | null>(null);
	let sourceLightboxUrl = $state<string | null>(null);
	let sourcePanelOpen = $state<number | null>(null);
	let sourcePageErrors = $state<Record<number, string>>({});

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
	const resultById = $derived(new Map(sortedResults.map(r => [r.ocrResultId, r])));

	function getTableRows(resultList: CampaignResultResponse[]) {
		return resultList.map((result) => {
			const topPrediction = result.predictions[0];
			return {
				id: result.ocrResultId,
				thumbnail: renderThumbnailCell(result.thumbnailUrl, getCropClip(result)),
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
		lightboxClip = null;
	}

	let cursorHistory = $state<number[]>([]);

	function handlePrevious() {
		if (cursorHistory.length === 0) return;
		const prevCursor = cursorHistory.pop()!;
		cursorHistory = [...cursorHistory];
		campaignResults.fetchResults(campaignId, { cursor: prevCursor, pageSize: $campaignResults.pageSize });
	}

	function handleNext() {
		if ($campaignResults.nextCursor !== null) {
			if ($campaignResults.cursor !== null) {
				cursorHistory = [...cursorHistory, $campaignResults.cursor];
			}
			campaignResults.fetchResults(campaignId, { cursor: $campaignResults.nextCursor, pageSize: $campaignResults.pageSize });
		}
	}

	function handleRetry() {
		cursorHistory = [];
		campaignResults.fetchResults(campaignId);
	}

	let shownCount = $derived($campaignResults.results.length);

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));

	function getExpandedResult(rowId: string | number): CampaignResultResponse | undefined {
		return resultById.get(Number(rowId));
	}

	function toggleSourcePanel(ocrResultId: number) {
		sourcePanelOpen = sourcePanelOpen === ocrResultId ? null : ocrResultId;
		const { [ocrResultId]: _, ...rest } = sourcePageErrors;
		sourcePageErrors = rest;
	}

	function getSourcePageStyle(coords: { top: number; bottom: number }): string {
		return `top: ${coords.top * 100}%; height: ${(coords.bottom - coords.top) * 100}%;`;
	}

	function getHighlightCoords(result: CampaignResultResponse): { top: number; bottom: number } | null {
		return result.entryCoordinates ?? result.cropCoordinates ?? null;
	}

	function getCropClip(result: CampaignResultResponse): { top: number; bottom: number } | null {
		const entry = result.entryCoordinates;
		const crop = result.cropCoordinates;
		if (!entry || !crop) return null;
		const cropHeight = crop.bottom - crop.top;
		if (cropHeight <= 0) return null;
		return {
			top: (entry.top - crop.top) / cropHeight,
			bottom: (entry.bottom - crop.top) / cropHeight,
		};
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
									if (url) {
										lightboxClip = getCropClip(result);
										handleCropClick(url, e);
									}
								}}
								onkeydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') {
										e.preventDefault();
										const target = e.target as HTMLElement;
										const url = target.getAttribute('data-crop-url') || target.closest('[data-crop-url]')?.getAttribute('data-crop-url');
										if (url) {
											lightboxClip = getCropClip(result);
											lightboxUrl = url;
										}
									}
								}}>
										{@html renderExpandedCropImage(result.thumbnailUrl, getCropClip(result))}
									</div>
								{/if}
									<div class="flex-1 min-w-0">
										<h4 class="text-sm font-semibold text-slate-700 mb-2">Predictions</h4>
										{@html renderPredictionsTable(result.predictions)}
									</div>
								</div>
								{#if (result.entryCoordinates ?? result.cropCoordinates) && result.scanId && result.pageNumber}
									<button
										class="mt-3 text-xs text-blue-600 hover:text-blue-800 flex items-center justify-center gap-1 py-1.5 px-3 hover:bg-blue-50 rounded transition-colors"
										onclick={() => toggleSourcePanel(result.ocrResultId)}
									>
										<svg class="w-3.5 h-3.5 transition-transform {sourcePanelOpen === result.ocrResultId ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
										{sourcePanelOpen === result.ocrResultId ? 'Hide source page' : 'Show on source page'}
									</button>
									<div class="source-panel {sourcePanelOpen === result.ocrResultId ? 'expanded' : ''}" >
										{#if sourcePanelOpen === result.ocrResultId}
											<div class="mt-4 pt-4 border-t border-slate-200">
												<div class="flex items-center justify-between mb-3">
													<div>
														<h4 class="text-xs font-semibold text-slate-500 uppercase">Source Page</h4>
														<p class="text-xs text-slate-400">{result.documentName || 'Document'} · Page {result.pageNumber}</p>
													</div>
													<button class="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1" onclick={() => toggleSourcePanel(result.ocrResultId)}>
														<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/></svg>
														Collapse
													</button>
												</div>
												<div class="bg-slate-50 rounded-lg p-4 flex items-center justify-center">
													{#if sourcePageErrors[result.ocrResultId]}
														<div class="text-center py-8">
															<p class="text-sm text-red-500">{sourcePageErrors[result.ocrResultId]}</p>
															<p class="text-xs text-slate-400 mt-1">The source PDF may not be available</p>
														</div>
													{:else}
													<div class="bg-white shadow-md rounded relative inline-block cursor-pointer" style="max-width: 400px;" onclick={() => { sourceLightboxUrl = getScanPageUrl(result.scanId!, result.pageNumber!); }}>
														<img
															src={getScanPageUrl(result.scanId!, result.pageNumber!)}
															alt="Source page {result.pageNumber} of {result.documentName}"
															class="rounded w-full"
															onerror={() => { sourcePageErrors = { ...sourcePageErrors, [result.ocrResultId]: 'Failed to load source page image' }; }}
														/>
														<div
															class="absolute left-0 right-0 pointer-events-none"
															style="background: rgba(59, 130, 246, 0.15); border-top: 2px solid rgba(59, 130, 246, 0.8); border-bottom: 2px solid rgba(59, 130, 246, 0.8); {getSourcePageStyle(getHighlightCoords(result)!)}"
														></div>
													</div>
													{/if}
												</div>
											</div>
										{/if}
									</div>
								{/if}
							{/if}
						{/snippet}
					</Table>
				</div>
			</div>

			{#if $campaignResults.total > 0}
				<div class="flex items-center justify-between border-t border-slate-200 px-4 py-3">
					<p class="text-sm text-slate-600">
						Showing {shownCount} of {$campaignResults.total} results
					</p>
					<div class="flex gap-2">
						<Button
							variant="secondary"
							text="Previous"
							disabled={cursorHistory.length === 0}
							onclick={handlePrevious}
						/>
						<Button
							variant="secondary"
							text="Next"
							disabled={$campaignResults.nextCursor === null}
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
		clipCoords={lightboxClip}
	/>

	<CropLightbox
		open={sourceLightboxUrl !== null}
		imageUrl={sourceLightboxUrl ?? ''}
		onClose={() => { sourceLightboxUrl = null; }}
	/>
</div>

<style>
	.source-panel {
		max-height: 0;
		overflow: hidden;
		transition: max-height 0.4s ease-out, opacity 0.3s ease;
		opacity: 0;
	}
	.source-panel.expanded {
		max-height: 800px;
		opacity: 1;
	}
</style>
