<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button } from '$lib/components/ui';
	import { API_BASE_URL } from '$lib/api/base-url';
	const API_BASE = API_BASE_URL;

	let campaignId = $derived($page.params.id ?? '');

	type Tab = 'voters' | 'petitions';
	let activeTab = $state<Tab>('petitions');

	let voterFiles = $state<FileList | null>(null);
	let petitionFiles = $state<FileList | null>(null);
	let uploading = $state(false);
	let messages = $state('');
	let messageType = $state<'success' | 'error' | 'info'>('info');

	interface PetitionScan {
		id: number;
		originalFilename: string;
		fileSize: number | null;
		pageCount: number | null;
		uploadedAt: string;
	}

	interface VoterListStatus {
		exists: boolean;
		upload?: {
			id: string;
			originalFilename: string;
			fileSize: number;
			rowCount: number;
			uploadedAt: string;
		};
	}

	let existingScans = $state<PetitionScan[]>([]);
	let loadingScans = $state(false);
	let scanToDelete = $state<PetitionScan | null>(null);
	let showDeleteConfirm = $state(false);

	let pendingDuplicates = $state<File[]>([]);
	let showDuplicateDialog = $state(false);

	let voterListStatus = $state<VoterListStatus | null>(null);
	let loadingVoterList = $state(false);
	let showVoterListDeleteConfirm = $state(false);

	onMount(() => {
		campaigns.fetchAll();
		fetchExistingScans();
		fetchVoterListStatus();
	});

	$effect(() => {
		if (campaign) {
			fetchVoterListStatus();
		}
	});

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));

	async function fetchExistingScans() {
		loadingScans = true;
		try {
			const response = await fetch(`${API_BASE}/api/campaigns/${campaignId}/scans`);
			if (response.ok) {
				const data = await response.json();
				existingScans = data.scans || [];
			}
		} catch (error) {
			console.error('Failed to fetch scans:', error);
		} finally {
			loadingScans = false;
		}
	}

	async function fetchVoterListStatus() {
		if (!campaign?.regionId) return;
		loadingVoterList = true;
		try {
			const response = await fetch(`${API_BASE}/api/regions/${campaign.regionId}/voter-list`);
			if (response.ok) {
				voterListStatus = await response.json();
			}
		} catch (error) {
			console.error('Failed to fetch voter list status:', error);
		} finally {
			loadingVoterList = false;
		}
	}

	async function deleteVoterList() {
		if (!campaign?.regionId) return;
		try {
			const response = await fetch(`${API_BASE}/api/regions/${campaign.regionId}/voter-list`, {
				method: 'DELETE'
			});
			if (response.ok) {
				voterListStatus = { exists: false };
				messages = 'Voter list deleted successfully.';
				messageType = 'success';
			} else {
				const errorData = await response.json();
				messages = `Error: ${errorData.detail || 'Failed to delete voter list.'}`;
				messageType = 'error';
			}
		} catch (error) {
			console.error('Failed to delete voter list:', error);
			messages = 'Failed to delete voter list.';
			messageType = 'error';
		} finally {
			showVoterListDeleteConfirm = false;
		}
	}

	function formatFileSize(bytes: number | null): string {
		if (bytes === null) return 'N/A';
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function checkForDuplicates(files: File[]): File[] {
		const existingNames = new Set(existingScans.map(s => s.originalFilename));
		return files.filter(f => existingNames.has(f.name));
	}

	async function uploadVoterList() {
		if (!voterFiles || voterFiles.length === 0) return;

		const file = voterFiles[0];
		if (!file) return;
		const formData = new FormData();
		formData.append('campaign_id', campaignId);
		formData.append('file', file);
		uploading = true;
		messages = '';
		messageType = 'info';

		try {
			const response = await fetch(`${API_BASE}/api/upload/voter-list`, {
				method: 'POST',
				body: formData
			});
			if (response.ok) {
				const data = await response.json();
				messages = `Voter list uploaded successfully! ${data.rowCount?.toLocaleString() || 0} records imported.`;
				messageType = 'success';
				voterFiles = null;
				await fetchVoterListStatus();
			} else {
				const errorData = await response.json();
				messages = `Error: ${errorData.detail || 'Something went wrong.'}`;
				messageType = 'error';
			}
		} catch (error) {
			messages = `Network error: ${error instanceof Error ? error.message : String(error)}`;
			messageType = 'error';
		} finally {
			uploading = false;
		}
	}

	function handlePetitionFileSelect() {
		if (!petitionFiles || petitionFiles.length === 0) return;

		const duplicates = checkForDuplicates(Array.from(petitionFiles));
		if (duplicates.length > 0) {
			pendingDuplicates = duplicates;
			showDuplicateDialog = true;
		} else {
			uploadPetitions();
		}
	}

	async function uploadPetitions(override: boolean = false) {
		if (!petitionFiles || petitionFiles.length === 0) return;

		const files = Array.from(petitionFiles);
		const formData = new FormData();
		formData.append('campaign_id', campaignId);
		if (override) {
			formData.append('override', 'true');
		}
		files.forEach((f) => formData.append('file', f));
		uploading = true;
		messages = '';
		messageType = 'info';
		showDuplicateDialog = false;

		try {
			const response = await fetch(`${API_BASE}/api/upload/petition`, {
				method: 'POST',
				body: formData
			});

			if (response.ok) {
				messages = 'Petitions uploaded successfully!';
				messageType = 'success';
				petitionFiles = null;
				await fetchExistingScans();
			} else {
				const errorData = await response.json();
				messages = `Error: ${errorData.detail || 'Something went wrong.'}`;
				messageType = 'error';
			}
		} catch (err) {
			messages = `Network error: ${err instanceof Error ? err.message : String(err)}`;
			messageType = 'error';
		} finally {
			uploading = false;
		}
	}

	function confirmDeleteScan(scan: PetitionScan) {
		scanToDelete = scan;
		showDeleteConfirm = true;
	}

	async function deleteScan() {
		if (!scanToDelete) return;
		const toDelete = scanToDelete;

		try {
			const response = await fetch(
				`${API_BASE}/api/campaigns/${campaignId}/scans/${toDelete.id}`,
				{ method: 'DELETE' }
			);

			if (response.ok) {
				existingScans = existingScans.filter(s => s.id !== toDelete.id);
				messages = `"${toDelete.originalFilename}" deleted.`;
				messageType = 'success';
			} else {
				const errorData = await response.json();
				messages = `Error: ${errorData.detail || 'Failed to delete.'}`;
				messageType = 'error';
			}
		} catch (error) {
			messages = `Network error: ${error instanceof Error ? error.message : String(error)}`;
			messageType = 'error';
		} finally {
			showDeleteConfirm = false;
			scanToDelete = null;
		}
	}

	async function deleteAllScans() {
		if (existingScans.length === 0) return;
		scanToDelete = null;
		showDeleteConfirm = true;
	}

	async function confirmDeleteAll() {
		for (const scan of existingScans) {
			try {
				await fetch(`${API_BASE}/api/campaigns/${campaignId}/scans/${scan.id}`, {
					method: 'DELETE'
				});
			} catch (error) {
				console.error('Failed to delete scan:', scan.id, error);
			}
		}
		existingScans = [];
		showDeleteConfirm = false;
		messages = 'All petition files removed.';
		messageType = 'success';
	}
</script>

	<svelte:head>
		<title>Upload — {campaign?.uniqueName || campaign?.title || 'Campaign'} — Votecatcher</title>
		<meta name="description" content="Upload voter lists and petitions for this campaign." />
	</svelte:head>

	<div class="space-y-6">
		<h1 class="text-3xl font-bold text-slate-900">Upload</h1>
		<p class="mt-1 text-slate-600">
			{#if $campaigns.loading}
				<span class="animate-pulse bg-slate-200 rounded h-4 w-16 inline-block"></span>
			{:else}
				{campaign?.uniqueName || campaign?.title || 'Campaign'}
			{/if}
		</p>
	</div>

	<div class="rounded-lg border border-slate-200 bg-white">
		<div class="flex border-b border-slate-200">
			<button
				onclick={() => activeTab = 'petitions'}
				class="px-6 py-3 text-sm font-medium {activeTab === 'petitions' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-900'}"
			>
				Petitions
			</button>
			<button
				onclick={() => activeTab = 'voters'}
				class="px-6 py-3 text-sm font-medium {activeTab === 'voters' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-900'}"
			>
				Voter List
			</button>
		</div>

		<div class="p-6">
			{#if activeTab === 'petitions'}
				<div class="space-y-6">
					<div>
						<h2 class="text-lg font-semibold text-slate-900 mb-2">Existing Petitions</h2>
						{#if loadingScans}
							<p class="text-sm text-slate-500">Loading...</p>
						{:else if existingScans.length === 0}
							<div class="rounded-md bg-slate-50 p-4 text-sm text-slate-600">
								<svg class="inline-block h-5 w-5 mr-2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								No petition files uploaded yet.
							</div>
						{:else}
							<div class="space-y-2">
								{#each existingScans as scan (scan.id)}
									<div class="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 p-3">
										<div class="flex items-center space-x-3">
											<svg class="h-8 w-8 text-red-500" fill="currentColor" viewBox="0 0 24 24">
												<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
												<path d="M14 2v6h6" fill="none" stroke="white" stroke-width="1.5"/>
												<text x="8" y="18" font-size="6" fill="white" font-weight="bold">PDF</text>
											</svg>
											<div>
												<p class="font-medium text-slate-900">{scan.originalFilename}</p>
												<p class="text-xs text-slate-500">
													{formatFileSize(scan.fileSize)}
													{#if scan.pageCount}
														· {scan.pageCount} page{scan.pageCount !== 1 ? 's' : ''}
													{/if}
													· {formatDate(scan.uploadedAt)}
												</p>
											</div>
										</div>
										<button
											onclick={() => confirmDeleteScan(scan)}
											class="rounded p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
											title="Remove file"
										>
											<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
										</button>
									</div>
								{/each}
								{#if existingScans.length > 1}
									<button
										onclick={deleteAllScans}
										class="text-sm text-red-600 hover:text-red-700"
									>
										Remove all files
									</button>
								{/if}
							</div>
						{/if}
					</div>

					<hr class="border-slate-200" />

					<div>
						<h2 class="text-lg font-semibold text-slate-900 mb-2">Upload New Petitions</h2>
						<p class="text-sm text-slate-600 mb-4">
							Upload petition PDF files containing signatures to be matched against the voter list.
						</p>

						{#if petitionFiles !== null}
							<div class="space-y-3 mb-4">
								{#each Array.from(petitionFiles) as file}
									<div class="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 p-3">
										<div class="flex items-center space-x-3">
											<svg class="h-6 w-6 text-red-500" fill="currentColor" viewBox="0 0 24 24">
												<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
											</svg>
											<span class="text-sm text-slate-700">{file.name}</span>
											<span class="text-xs text-slate-500">({formatFileSize(file.size)})</span>
										</div>
										<button
											onclick={() => petitionFiles = null}
											class="rounded p-1 text-slate-400 hover:text-slate-600"
											aria-label="Remove file"
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
											</svg>
										</button>
									</div>
								{/each}
							</div>

							<div class="flex space-x-3">
								<Button
									variant="primary"
									text="Upload Petitions"
									onclick={handlePetitionFileSelect}
									disabled={uploading}
								/>
								<Button
									variant="secondary"
									text="Cancel"
									onclick={() => petitionFiles = null}
									disabled={uploading}
								/>
							</div>
						{:else}
							<label class="block">
								<span class="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 cursor-pointer">
									<svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
									</svg>
									Select Petition Files (.pdf)
								</span>
								<input
									bind:files={petitionFiles}
									type="file"
									accept="application/pdf"
									multiple
									class="hidden"
								/>
							</label>
						{/if}
					</div>
				</div>
			{:else}
				<div class="space-y-6">
					{#if loadingVoterList}
						<div class="text-center py-8 text-slate-500">Loading...</div>
					{:else if voterListStatus?.exists && voterListStatus.upload}
						<div>
							<h2 class="text-lg font-semibold text-slate-900 mb-2">Current Voter List</h2>
							<div class="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 p-3">
								<div class="flex items-center space-x-3">
									<svg class="h-8 w-8 text-green-600" fill="currentColor" viewBox="0 0 24 24">
										<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
										<path d="M14 2v6h6" fill="none" stroke="white" stroke-width="1.5"/>
										<text x="7" y="18" font-size="6" fill="white" font-weight="bold">CSV</text>
									</svg>
									<div>
										<p class="font-medium text-slate-900">{voterListStatus.upload.originalFilename}</p>
										<p class="text-xs text-slate-500">
											{voterListStatus.upload.rowCount.toLocaleString()} voters
											· {formatFileSize(voterListStatus.upload.fileSize)}
											· {formatDate(voterListStatus.upload.uploadedAt)}
										</p>
									</div>
								</div>
								<button
									onclick={() => showVoterListDeleteConfirm = true}
									class="rounded p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
									title="Delete voter list"
								>
									<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							</div>
						</div>

						<hr class="border-slate-200" />
					{/if}

					<div>
						<h2 class="text-lg font-semibold text-slate-900 mb-2">
							{voterListStatus?.exists ? 'Upload New Voter List' : 'Upload Voter List'}
						</h2>
						<p class="text-sm text-slate-600 mb-4">
							{voterListStatus?.exists
								? 'Uploading a new file will replace the existing voter list.'
								: 'Upload a voter list file (CSV or XLSX) containing registered voters for matching.'}
						</p>

						{#if voterFiles !== null}
							<div class="space-y-4">
								{#each Array.from(voterFiles) as file}
									<div class="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 p-3">
										<div class="flex items-center space-x-3">
											<svg class="h-6 w-6 text-green-600" fill="currentColor" viewBox="0 0 24 24">
												<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
											</svg>
											<span class="text-sm text-slate-700">{file.name}</span>
										</div>
									<button
										onclick={() => voterFiles = null}
										class="rounded p-1 text-slate-400 hover:text-slate-600"
										aria-label="Remove file"
									>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
											</svg>
										</button>
									</div>
								{/each}

								<Button
									variant="primary"
									text="Upload Voter List"
									onclick={uploadVoterList}
									disabled={uploading || voterFiles === null}
								/>
							</div>
						{:else}
							<label class="block">
								<span class="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 cursor-pointer">
									<svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
									</svg>
									Select Voter File (.csv, .xlsx)
								</span>
								<input
									bind:files={voterFiles}
									type="file"
									accept=".csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
									class="hidden"
								/>
							</label>
						{/if}
					</div>
				</div>
			{/if}

			{#if messages}
				<div class="mt-4 rounded-md p-3 text-sm {messageType === 'success' ? 'bg-green-50 text-green-700' : messageType === 'error' ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-700'}">
					{messages}
				</div>
			{/if}

			{#if uploading}
				<div class="mt-4 flex items-center text-sm text-slate-600">
					<svg class="animate-spin h-5 w-5 mr-2 text-blue-600" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
					</svg>
					Uploading...
				</div>
			{/if}
		</div>
	</div>

{#if showDeleteConfirm}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true">
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
		<h3 class="text-lg font-semibold text-slate-900 mb-2">
			{#if scanToDelete}
				Remove "{scanToDelete.originalFilename}"?
			{:else}
				Remove all petition files?
			{/if}
		</h3>
			<p class="text-sm text-slate-600 mb-4">
				{#if scanToDelete}
					This action cannot be undone. The file will be permanently removed from this campaign.
				{:else}
					This will remove all {existingScans.length} petition file{existingScans.length !== 1 ? 's' : ''} from this campaign. This action cannot be undone.
				{/if}
			</p>
			<div class="flex justify-end space-x-3">
				<Button
					variant="secondary"
					text="Cancel"
					onclick={() => { showDeleteConfirm = false; scanToDelete = null; }}
				/>
				<Button
					variant="primary"
					text="Remove"
					onclick={() => { if (scanToDelete) deleteScan(); else confirmDeleteAll(); }}
				/>
			</div>
		</div>
	</div>
{/if}

{#if showDuplicateDialog}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true">
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
			<h3 class="text-lg font-semibold text-slate-900 mb-2">Duplicate File Names</h3>
			<p class="text-sm text-slate-600 mb-3">
				The following files already exist:
			</p>
			<ul class="text-sm text-slate-700 mb-4 max-h-32 overflow-y-auto">
				{#each pendingDuplicates as file}
					<li class="py-1">• {file.name}</li>
				{/each}
			</ul>
			<p class="text-sm text-slate-600 mb-4">
				Would you like to override the existing files?
			</p>
			<div class="flex justify-end space-x-3">
				<Button
					variant="secondary"
					text="Cancel"
					onclick={() => { showDuplicateDialog = false; pendingDuplicates = []; petitionFiles = null; }}
				/>
				<Button
					variant="primary"
					text="Override"
					onclick={() => uploadPetitions(true)}
				/>
			</div>
		</div>
	</div>
{/if}

{#if showVoterListDeleteConfirm}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true">
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
			<h3 class="text-lg font-semibold text-slate-900 mb-2">Delete Voter List?</h3>
			<p class="text-sm text-slate-600 mb-4">
				This will permanently delete all {voterListStatus?.upload?.rowCount?.toLocaleString() || 'registered'} voters for this region.
				This action cannot be undone.
			</p>
			<div class="flex justify-end space-x-3">
				<Button
					variant="secondary"
					text="Cancel"
					onclick={() => showVoterListDeleteConfirm = false}
				/>
				<Button
					variant="primary"
					text="Delete"
					onclick={deleteVoterList}
				/>
			</div>
		</div>
	</div>
{/if}
