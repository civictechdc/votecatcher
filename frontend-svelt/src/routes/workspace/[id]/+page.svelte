<script lang="ts">
	import type { PageData } from '../$types';
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import type {
		UploadResult,
		MatchRow,
		ConfidenceThresholds,
		MatchResults
	} from '$lib/workspace-types';
	import { MatchJobStatus, type MatchingProgressResponse } from '$lib/api/response-types';
	import { MatchColumn, MatchValueFormatKeys } from '$lib/workspace-types';
	import MatchConfidenceIndicator from '$lib/components/MatchConfidenceIndicator.svelte';
	import ColumnHeader from '$lib/components/match-results/ColumnHeader.svelte';
	import UploadItem from '$lib/components/match-results/UploadItem.svelte';
	import { onDestroy } from 'svelte';

	let petitionFiles = $state<FileList | null>(null);
	let voterListFile = $state<FileList | null>(null);
	let selectedVoterFile: File | null = $derived(voterListFile ? voterListFile.item(0) : null);

	let currentMatchStatus = $state<MatchingProgressResponse | null>(null);
	let eventSource = $state<EventSource | null>(null);
	let currentMatchEventMessage = $state<string>('');

	let props: PageData = $props();
	const DEMO_MODE = $derived(props.data.isDemoMode as boolean);
	const MATCH_FIELDS = $derived(props.data.matchingFields as string[]);

	$effect(() => {
		console.log(`voter list is ${voterListFile} with state: ${selectedVoterFile}`);
		if (voterListFile) {
			for (const file of voterListFile) {
				console.log(`${file.name}: ${file.size} bytes`);
			}
		} else {
			console.log(`Voter list is ${voterListFile}`);
		}
	});

	let uploading = $state(false);
	let voterFileUploaded: boolean = $state(false);
	let petitionsUploaded: boolean = $state(false);
	let readyToMatch: boolean = $derived(voterFileUploaded && petitionsUploaded);

	let uploadProgress = $state<number>(0); // 0-100
	let messages = $state('');
	let matchResults: MatchResults = $state({
		matchColumns: [],
		matchRecords: [],
		timestamp: new Date().toISOString()
	});
	let matches: MatchRow[] = $derived(matchResults ? matchResults.matchRecords : []);
	let confidenceThresholds: ConfidenceThresholds = $state({ high: 95.0, medium: 90.0 });

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

	function observeMatchStatus() {
		if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
			console.log('Connection already open or connecting.');
			return;
		}

		eventSource = new EventSource(
			`api/match-status/${$state.snapshot(currentMatchStatus)?.task_id}`
		);

		eventSource.onopen = () => {
			currentMatchEventMessage = 'Matching status connection opened';
		};

		eventSource.onmessage = (event) => {
			console.log(`old status: ${currentMatchStatus?.job_status}`);
			currentMatchStatus = JSON.parse(event.data) as MatchingProgressResponse;
			currentMatchEventMessage = `Current status is ${currentMatchStatus}`;
			console.log(`Updated status is: ${JSON.stringify($state.snapshot(currentMatchStatus))}`);
			switch (currentMatchStatus.job_status) {
				case MatchJobStatus.CANCELLED:
				case MatchJobStatus.COMPLETED:
				case MatchJobStatus.OCR_FAILED:
				case MatchJobStatus.MATCHING_FAILED:
				case MatchJobStatus.OCR_TIMED_OUT:
				case MatchJobStatus.TIMED_OUT:
				case MatchJobStatus.MISC_ERROR:
					console.log(
						`Job status ${currentMatchStatus.job_status} with job state ${currentMatchStatus.job_status == MatchJobStatus.COMPLETED}`
					);
					stopStreaming();
					uploadProgress = 100;
					break;
				case MatchJobStatus.PENDING:
					uploadProgress = 10;
					break;
				case MatchJobStatus.OCR_IN_PROGRESS:
					uploadProgress = 50;
					break;
				case MatchJobStatus.OCR_COMPLETED:
					uploadProgress = 75;
					if (currentMatchStatus.job_status === MatchJobStatus.OCR_COMPLETED) {
						onOcrJobCompleted(currentMatchStatus.task_id);
					}
					break;
				case MatchJobStatus.MATCHING:
					uploadProgress = 80;
					break;
				default:
					console.log(`Match status is ${currentMatchStatus.job_status}`);
					break;
			}
		};

		eventSource.onerror = (error) => {
			console.error('EventSource error:', error);
			currentMatchEventMessage = 'Error or Closed';
			// Optional: Auto-reconnect logic could be added here if desired
		};
	}

	// Function to manually close the connection
	function stopStreaming() {
		if (eventSource) {
			eventSource.close();
			currentMatchEventMessage = 'Closed manually';
			console.log('Connection closed.');
		}
	}

	async function onOcrJobCompleted(jobId: string) {
		const res = await fetch(`api/match-result/${jobId}`, {
			method: 'GET'
		});

		if (!res.ok) throw new Error(`Server returned ${res.status}`);
		const payload = await res.json();
		matchResults = payload.matchResults as MatchResults;
	}

	onDestroy(() => {
		// Ensures connection is closed if the user navigates away
		if (eventSource) {
			eventSource.close();
		}
	});

	function pushMessage(txt: string) {
		messages = txt;
	}

	async function uploadVoterList() {
		if (!selectedVoterFile) {
			console.log(`No upload happened for voter list ${selectedVoterFile}`);
			return;
		}
		let message: string = '';

		const file = selectedVoterFile;
		const formData = new FormData();
		formData.append('file', file, file.name);
		uploading = true;
		try {
			const response = await fetch('api/upload', {
				method: 'POST',
				body: formData
			});
			if (response.ok) {
				message = 'File uploaded successfully!';
				pushMessage(message);
			} else {
				const errorData = await response.json();
				message = `Error: ${errorData.detail || 'Something went wrong.'}`;
			}
			voterFileUploaded = response.ok;
		} catch (error) {
			voterFileUploaded = false;
			message = `Network error: ${error instanceof Error ? error.message : String(error)}`;
		} finally {
			uploading = false;
		}
	}

	async function uploadPetitions() {
		if (!petitionFiles) {
			console.log(`No upload happened for voter list ${voterListFile}`);
			return;
		}

		const files = Array.from(petitionFiles);
		const formData = new FormData();
		files.forEach((f) => formData.append('petition', f, f.name));
		uploading = true;

		let message = '';
		try {
			const response = await fetch('api/upload', {
				method: 'POST',
				body: formData
			});

			if (response.ok) {
				message = 'File uploaded successfully!';
				pushMessage(message);
			} else {
				const errorData = await response.json();
				message = `Error: ${errorData.detail || 'Something went wrong.'}`;
			}
			petitionsUploaded = response.ok;
		} catch (err) {
			petitionsUploaded = false;
			message = `Network error: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			uploading = false;
		}
	}

	function console_log(message: string) {
		console.log(message);
	}

	async function runMatching() {
		pushMessage('Starting matching...');
		uploading = true;
		uploadProgress = 0;
		matchResults = {
			...matchResults,
			matchRecords: [],
			matchColumns: matchResults?.matchColumns ?? [],
			timestamp: new Date().toISOString()
		};
		try {
			// fetch matches (server simulates processing)

			const matchBody = {
				demo: DEMO_MODE,
				thresholds: confidenceThresholds,
				columns: MATCH_FIELDS,
				batchEnabled: true
			};

			console.log(`Stringified body: ${JSON.stringify(matchBody)}`);

			const res = await fetch('/workspace/api/match', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify(matchBody)
			});
			if (!res.ok) throw new Error(`Server returned ${res.status}`);

			const payload = await res.json();
			if (matchBody.batchEnabled) {
				console.log(
					`Current state of the response is ${JSON.stringify(payload.matchStatus)} with ${typeof payload.matchStatus}`
				);
				currentMatchStatus = payload.matchStatus as MatchingProgressResponse;
				observeMatchStatus();
			} else {
				stopStreaming();
			}
			// payload.matches: OCRMatch[]
			if (payload.matchResults as MatchResults) {
				matchResults = payload.matchResults as MatchResults;
			}
			pushMessage(`Matching complete: ${matchResults.matchRecords.length ?? 0} result(s)`);
		} catch (err) {
			pushMessage(`Matching error: ${(err as Error).message}`);
		} finally {
			uploading = false;
			uploadProgress = 100;
			setTimeout(() => (uploadProgress = 0), 500);
		}
	}

	let currentSort: [boolean, MatchColumn | null] = $state([false, null]);
	let currentResultsOrder: MatchRow[] = $derived(matches);

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
				{#if voterListFile !== null}
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
						onclick={() => uploadVoterList()}
						disabled={selectedVoterFile === null}
						title="Upload voter files">Upload voter list</button
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
						onclick={() => uploadPetitions()}
						disabled={petitionFiles === null || petitionFiles.length === 0}
						title="Upload petitions">Upload petitions</button
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
					<div class="bar" style="width: {uploadProgress}%"></div>
				</div>
				<div class="muted" style="margin-top:.25rem">{uploadProgress}%</div>
			</div>
			<progress> test </progress>

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
							{#each matches as m (m.row_idx)}
								<tr class="hover:bg-blue-200">
									<!-- Create each row value cell of arbitrary number of values -->
									{#each Object.entries(m) as [key, value]}
										{#if key === MatchValueFormatKeys.MATCH_SCORE}
											<td>
												<MatchConfidenceIndicator
													matchScore={value as number}
													confidenceThreshold={confidenceThresholds}
												/>
											</td>
										{:else}
											<td>
												{value}
											</td>
										{/if}
									{/each}
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
