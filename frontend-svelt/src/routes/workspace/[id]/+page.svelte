<script lang="ts">
	import { page } from '$app/state';
	import type { PageData } from '../$types';
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import type {
		UploadResult,
		OcrMatch,
		ConfidenceThresholds,
		MatchResults
	} from '$lib/workspace-types';
	import { MatchColumn } from '$lib/workspace-types';
	import MatchConfidenceIndicator from '$lib/components/MatchConfidenceIndicator.svelte';
	import ColumnHeader from '$lib/components/match-results/ColumnHeader.svelte';
	import UploadItem from '$lib/components/match-results/UploadItem.svelte';

	let petitionFiles = $state<FileList | null>(null);

	let voterListFile = $state<FileList | null>(null);
	let selectedVoterFile: File | null = $derived(voterListFile ? voterListFile.item(0) : null);

	let data: PageData = $props();
	const DEMO_MODE: boolean = $derived(data.isDemoMode);

	$effect(() => {
		if (voterListFile) {
			for (const file of voterListFile) {
				console.log(`${file.name}: ${file.size} bytes`);
			}
		}
	});

	let uploading = $state(false);
	let filesUploaded = $state(false);
	let readyToMatch: boolean = $derived(filesUploaded && !uploading);

	const uploadProgress = writable(0); // 0-100
	let messages = $state('');
	let matchResults: MatchResults = $state({
		matchColumns: [],
		matchRecords: [],
		timestamp: new Date().toISOString()
	});
	let matches: OcrMatch[] = $derived(matchResults ? matchResults.matchRecords : []);
	let confidenceThresholds: ConfidenceThresholds = $state({ high: 0.8, medium: 0.5 });

	// results / config
	onMount(async () => {
		try {
			const res = await fetch('/static/config.json');
			if (res.ok) {
				const cfg = await res.json();
				confidenceThresholds = cfg.confidence_thresholds ?? { high: 0.8, medium: 0.5 };
			}
		} catch (err) {
			// ignore, keep defaults
		}
	});

	function pushMessage(txt: string) {
		messages = txt;
	}

	// XMLHttpRequest helper to POST files and get progress events on client side
	function postFilesWithProgress(url: string, formData: FormData, onProgress: (p: number) => void) {
		return new Promise<UploadResult>((resolve, reject) => {
			const xhr = new XMLHttpRequest();
			xhr.open('POST', url, true);
			xhr.onload = () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						const json = JSON.parse(xhr.responseText);
						resolve(json as UploadResult);
					} catch (e) {
						reject(new Error('Invalid json response'));
					}
				} else {
					reject(new Error(`Upload failed: ${xhr.status}`));
				}
			};
			xhr.onerror = () => reject(new Error('Network error during upload'));
			xhr.upload.onprogress = (ev) => {
				if (!ev.lengthComputable) return;
				const pct = Math.round((ev.loaded / ev.total) * 100);
				onProgress(pct);
			};
			xhr.send(formData);
		});
	}

	async function doUpload(kind: 'voter' | 'petition') {
		const files =
			kind === 'voter'
				? voterListFile
					? Array.from(voterListFile)
					: []
				: petitionFiles
					? Array.from(petitionFiles)
					: [];
		if (files.length === 0) {
			pushMessage('No files selected.');
			return;
		}

		// Demo short-circuit: if demo mode, simulate upload and push mock files to server endpoint
		const fd = new FormData();
		files.forEach((f) => fd.append('files', f, f.name));
		fd.append('kind', kind);
		pushMessage(`Uploading ${files.length} ${kind} file(s)...`);
		uploading = true;
		uploadProgress.set(0);
		try {
			// Use XHR wrapper to show progress in UI
			const result = await postFilesWithProgress('/workspace/api/upload', fd, (p) => {
				uploadProgress.set(p);
			});
			pushMessage(result.message ?? 'Upload completed');
			// If result provides files metadata, store names in messages
			if (result.files && result.files.length) {
				pushMessage(
					`Server received ${result.files.length} file(s): ${result.files.map((f) => f.name).join(', ')}`
				);
			}
			filesUploaded = true;
		} catch (err) {
			pushMessage(`Upload error: ${(err as Error).message}`);
		} finally {
			uploading = false;
			setTimeout(() => uploadProgress.set(0), 400);
		}
	}

	async function runMatching() {
		pushMessage('Starting matching...');
		uploading = true;
		uploadProgress.set(0);
		matchResults = {
			...matchResults,
			matchRecords: [],
			matchColumns: matchResults?.matchColumns ?? [],
			timestamp: new Date().toISOString()
		};
		try {
			// fetch matches (server simulates processing)
			const res = await fetch('/workspace/api/match', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ demo: DEMO_MODE, thresholds: confidenceThresholds })
			});
			if (!res.ok) throw new Error(`Server returned ${res.status}`);
			const payload = await res.json();
			// payload.matches: OCRMatch[]
			if (payload.matchResults as MatchResults) {
				matchResults = payload.matchResults as MatchResults;
			}
			pushMessage(`Matching complete: ${matchResults.matchRecords.length ?? 0} result(s)`);
		} catch (err) {
			pushMessage(`Matching error: ${(err as Error).message}`);
		} finally {
			uploading = false;
			uploadProgress.set(100);
			setTimeout(() => uploadProgress.set(0), 500);
		}
	}

	let currentSort: [boolean, MatchColumn | null] = $state([false, null]);
	let currentResultsOrder: OcrMatch[] = $derived(matches);

	function sortColumn(sortState: [boolean, MatchColumn]) {
		const column = sortState[1];
		currentSort[0] = !sortState[0];
		currentSort[1] = column;

		if (column.isSortable) {
			//Sort
			currentResultsOrder.sort((a, b) => {
				if (column.sort) {
					console.log('Found sort function for ', column.name, column.sort);
					return column.sort?.(a, b);
				}
				console.log('Could not find sort function for ', column.name, column.sort);
				return 0;
			});
		}
	}
</script>

<div class="container">
	<div style="display:flex; gap:1rem;">
		<aside class="sidebar w-1/3">
			<h3 style="margin:0 0 .5rem 0">Workspace — Upload</h3>
			<p class="muted">
				Upload voter lists (.csv, .xlsx) and petition PDFs (.pdf). Demo mode: {DEMO_MODE
					? 'ON'
					: 'OFF'}
			</p>

			<div style="margin-top:1rem;" class="relative w-full">
				{#if selectedVoterFile !== null}
					<div class="mb-4">
						<UploadItem
							file={selectedVoterFile}
							onRemove={(_) => {
								voterListFile = null;
							}}
						/>
					</div>
					<button
						class="inline-flex items-center justify-center rounded-md bg-blue-600 px-8 py-3 text-sm text-white hover:bg-blue-700"
						onclick={() => doUpload('voter')}
						disabled={uploading}
						title="Upload voter files">Upload</button
					>
				{:else}
					<label class="hover:to-blue-400" for="upload_voter_list">
						<p
							class="inline-flex items-center justify-center rounded-md bg-blue-600 px-2 py-2 text-sm text-white hover:bg-blue-700"
						>
							Add Voter file (.csv, .xlsx)
						</p>
						<div class="file-row" style="margin-top:.5rem;">
							<input
								bind:files={voterListFile}
								type="file"
								accept=".csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
								id="upload_voter_list"
								class="hidden"
							/>
						</div>
					</label>
				{/if}
			</div>

			<div style="margin-top:1rem;">
				{#if petitionFiles !== null}
					{#each petitionFiles as file}
						<div class="mb-4">
							<UploadItem
								{file}
								onRemove={(_) => {
									petitionFiles = null;
								}}
							/>
						</div>
					{/each}

					<button
						class="inline-flex items-center justify-center rounded-md bg-red-600 px-8 py-3 text-sm text-white hover:bg-red-700"
						onclick={() => doUpload('petition')}
						disabled={filesUploaded}
						title="Upload petitions">Upload</button
					>
				{:else}
					<label class="muted">
						<p
							class="inline-flex items-center justify-center rounded-md bg-blue-600 px-2 py-2 text-sm text-white hover:bg-blue-700"
						>
							Petition files (.pdf)
						</p>
						<div class="file-row" style="margin-top:.5rem;">
							<input
								bind:files={petitionFiles}
								type="file"
								accept="application/pdf"
								multiple
								class="hidden"
							/>
						</div>
					</label>
				{/if}
			</div>

			<div style="margin-top:1rem;">
				<button
					onclick={runMatching}
					class="inline-flex items-center justify-center rounded-md bg-green-600 px-8 py-3 text-sm text-white hover:bg-green-700 disabled:bg-green-200 disabled:text-gray-500"
					disabled={!readyToMatch}>Run Matching</button
				>
			</div>

			<div style="margin-top:1rem;">
				<div class="muted">Progress</div>
				<div class="progress" style="margin-top:.5rem;">
					<div class="bar" style="width: {$uploadProgress}%"></div>
				</div>
				<div class="muted" style="margin-top:.25rem">{$uploadProgress}%</div>
			</div>

			<div style="margin-top:1rem;">
				<div class="muted">Messages</div>
				<ul>
					<li class="muted">{messages}</li>
				</ul>
			</div>
		</aside>

		<main class="main w-2/3">
			<h3 style="margin:0 0 .5rem 0">Matches</h3>
			<p class="muted">
				Confidence thresholds: high ≥ {confidenceThresholds.high}, medium ≥ {confidenceThresholds.medium}
			</p>
			<div
				style="relative flex flex-col w-full h-full margin-top:0.75rem; overflow:scroll; border:1px solid #eef2f7; border-radius:6px;"
			>
				<table>
					{#if matches.length > 0}
						<caption class="caption-top">
							{matches.length} matches found.
						</caption>
					{/if}
					<thead>
						<tr>
							{#each matchResults?.matchColumns as col}
								<th>
									<ColumnHeader
										column={col}
										sortAscending={currentSort[0]}
										toggleSort={(sortState: [boolean, MatchColumn]) => sortColumn(sortState)}
									/>
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#if matches.length === 0}
							<tr
								><td colspan="9" class="muted" style="text-align:center; padding:1rem;"
									>No matches yet — upload files and press Run Matching</td
								></tr
							>
						{:else}
							{#each matches as m}
								<tr class="hover:bg-blue-200">
									<td>{m.registeredName}</td>
									<td>{m.ocrPredictedName}</td>
									<td>
										<MatchConfidenceIndicator
											matchScore={m.predictionScore}
											confidenceThreshold={confidenceThresholds}
										/>
									</td>
									<td>{m.nameDistance ?? '—'}</td>
									<td>{m.registeredAddress}</td>
									<td>{m.addressDistance ?? '—'}</td>
									<td>{m.predictedAddress}</td>
									<td>{m.ward ?? '—'}</td>
									<td>{m.petitionPageNumber ?? '—'}</td>
									<td>{m.petitionRowNumber ?? '—'}</td>
									<td>{m.matchRank ?? '—'}</td>
								</tr>
							{/each}
						{/if}
					</tbody>
				</table>
			</div>
		</main>
	</div>
</div>

<style>
	/* Minimal scoped styles to ensure readable, consistent layout */
	.container {
		max-width: 85%;
		margin: 0 auto;
		padding: 1rem;
	}
	.sidebar {
		width: 320px;
		padding: 1rem;
		border-right: 1px solid var(--slate-200);
		min-height: calc(100vh - 2rem);
	}
	.main {
		flex: 1;
		padding: 1rem;
	}
	.file-row {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
	.progress {
		height: 10px;
		background: #e6e6e6;
		border-radius: 999px;
		overflow: hidden;
	}
	.progress > .bar {
		height: 100%;
		background: linear-gradient(90deg, #16a34a, #059669);
		transition: width 0.2s ease;
	}
	table {
		width: 100%;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.5rem;
		border-bottom: 1px solid #eef2f7;
		text-align: left;
		font-size: 0.95rem;
	}
	.muted {
		color: #64748b;
		font-size: 0.9rem;
	}
</style>
