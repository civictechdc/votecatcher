<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, LoadingState } from '$lib/components/ui';
	import UploadItem from '$lib/components/match-results/UploadItem.svelte';
	import { PUBLIC_API_URL } from '$env/static/public';

	let campaignId = $derived($page.params.id);
	const API_BASE = PUBLIC_API_URL || 'http://localhost:8000';

	type Tab = 'voters' | 'petitions';
	let activeTab = $state<Tab>('voters');

	let voterFiles = $state<FileList | null>(null);
	let petitionFiles = $state<FileList | null>(null);
	let uploading = $state(false);
	let voterFileUploaded = $state(false);
	let petitionsUploaded = $state(false);
	let messages = $state('');
	let uploadProgress = $state(0);

	onMount(() => {
		campaigns.fetchAll();
	});

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));

	async function uploadVoterList() {
		if (!voterFiles || voterFiles.length === 0) return;

		const file = voterFiles[0];
		const formData = new FormData();
		formData.append('file', file, file.name);
		uploading = true;

		try {
			const response = await fetch(`${API_BASE}/api/upload/voter-list`, {
				method: 'POST',
				body: formData
			});
			if (response.ok) {
				messages = 'Voter list uploaded successfully!';
				voterFileUploaded = true;
			} else {
				const errorData = await response.json();
				messages = `Error: ${errorData.detail || 'Something went wrong.'}`;
			}
		} catch (error) {
			messages = `Network error: ${error instanceof Error ? error.message : String(error)}`;
		} finally {
			uploading = false;
		}
	}

	async function uploadPetitions() {
		if (!petitionFiles || petitionFiles.length === 0) return;

		const files = Array.from(petitionFiles);
		const formData = new FormData();
		formData.append('campaign_id', campaignId);
		files.forEach((f) => formData.append('file', f, f.name));
		uploading = true;

		try {
			const response = await fetch(`${API_BASE}/api/upload/petition`, {
				method: 'POST',
				body: formData
			});

			if (response.ok) {
				messages = 'Petitions uploaded successfully!';
				petitionsUploaded = true;
			} else {
				const errorData = await response.json();
				messages = `Error: ${errorData.detail || 'Something went wrong.'}`;
			}
		} catch (err) {
			messages = `Network error: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			uploading = false;
		}
	}
</script>

<svelte:head>
	<title>Upload — {campaign?.unique_name || campaign?.title || 'Campaign'} — Votecatcher</title>
	<meta name="description" content="Upload voter lists and petitions for this campaign." />
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold text-slate-900">Upload</h1>
		<p class="mt-1 text-slate-600">{campaign?.unique_name || campaign?.title || 'Campaign'}</p>
	</div>

	<div class="rounded-lg border border-slate-200 bg-white">
		<div class="flex border-b border-slate-200">
			<button
				onclick={() => activeTab = 'voters'}
				class="px-6 py-3 text-sm font-medium {activeTab === 'voters' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-900'}"
			>
				Voter List
			</button>
			<button
				onclick={() => activeTab = 'petitions'}
				class="px-6 py-3 text-sm font-medium {activeTab === 'petitions' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-900'}"
			>
				Petitions
			</button>
		</div>

		<div class="p-6">
			{#if activeTab === 'voters'}
				<div class="space-y-4">
					<p class="text-sm text-slate-600">
						Upload a voter list file (CSV or XLSX) containing registered voters for matching.
					</p>

					{#if voterFiles !== null}
						<div class="space-y-4">
							{#each Array.from(voterFiles) as file}
								<UploadItem
									{file}
									isUploaded={voterFileUploaded}
									onRemove={(_) => {
										voterFiles = null;
									}}
								/>
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
			{:else}
				<div class="space-y-4">
					<p class="text-sm text-slate-600">
						Upload petition PDF files containing signatures to be matched against the voter list.
					</p>

					{#if petitionFiles !== null}
						<div class="space-y-4">
							{#each Array.from(petitionFiles) as file}
								<UploadItem
									{file}
									isUploaded={petitionsUploaded}
									onRemove={(_) => {
										petitionFiles = null;
									}}
								/>
							{/each}

							<Button
								variant="primary"
								text="Upload Petitions"
								onclick={uploadPetitions}
								disabled={uploading || petitionFiles === null || petitionFiles.length === 0}
							/>
						</div>
					{:else}
						<label class="block">
							<span class="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 cursor-pointer">
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
			{/if}

			{#if messages}
				<div class="mt-4 rounded-md bg-slate-100 p-3 text-sm">
					{messages}
				</div>
			{/if}

			{#if uploading}
				<div class="mt-4">
					<div class="h-2 w-full rounded-full bg-slate-200">
						<div class="h-2 rounded-full bg-blue-600 transition-all" style="width: {uploadProgress}%"></div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
