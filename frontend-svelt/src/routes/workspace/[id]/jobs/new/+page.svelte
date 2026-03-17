<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { campaigns } from '$lib/stores/campaigns';
	import { jobs } from '$lib/stores/jobs';
	import { Button, LoadingState, ErrorDisplay } from '$lib/components/ui';
	import { PUBLIC_API_URL } from '$env/static/public';

	interface ProviderConfig {
		provider: string;
		model: string;
		is_configured: boolean;
		last_validated?: string;
	}

	interface PetitionScan {
		id: number;
		original_filename: string;
		page_count: number | null;
		uploaded_at: string;
	}

	interface ScansResponse {
		scans: PetitionScan[];
		total: number;
	}

	let campaignId = $derived($page.params.id);
	const API_BASE = (PUBLIC_API_URL || 'http://localhost:8080') + '/api';

	let scans = $state<PetitionScan[]>([]);
	let scansLoading = $state(false);
	let providers = $state<ProviderConfig[]>([]);
	let providersLoading = $state(false);
	let selectedScans = $state<Set<number>>(new Set());
	let formData = $state({
		providerName: '',
		providerModel: '',
		forceReprocess: false
	});
	let submitting = $state(false);
	let error = $state<string | null>(null);

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));

	async function fetchScans() {
		scansLoading = true;
		try {
			const response = await fetch(`${API_BASE}/campaigns/${campaignId}/scans`);
			if (response.ok) {
				const data: ScansResponse = await response.json();
				scans = data.scans;
			} else {
				error = 'Failed to load scans';
			}
		} catch (e) {
			error = 'Failed to load scans';
			console.error(e);
		} finally {
			scansLoading = false;
		}
	}

	async function fetchProviders() {
		providersLoading = true;
		try {
			const response = await fetch(`${API_BASE}/settings/providers`);
			if (response.ok) {
				providers = await response.json();
				const configured = providers.find(p => p.is_configured);
				if (configured) {
					formData.providerName = configured.provider;
					formData.providerModel = configured.model;
				} else if (providers.length > 0) {
					formData.providerName = providers[0].provider;
					formData.providerModel = providers[0].model;
				}
			} else {
				error = 'Failed to load providers';
			}
		} catch (e) {
			error = 'Failed to load providers';
			console.error(e);
		} finally {
			providersLoading = false;
		}
	}

	function toggleScan(id: number) {
		const newSet = new Set(selectedScans);
		if (newSet.has(id)) {
			newSet.delete(id);
		} else {
			newSet.add(id);
		}
		selectedScans = newSet;
	}

	function formatDate(date: string | null): string {
		if (!date) return '-';
		const d = new Date(date);
		return d.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	async function handleSave() {
		if (!campaignId) return;
		const id = campaignId;
		if (selectedScans.size === 0) {
			error = 'Please select at least one scan';
			return;
		}
		submitting = true;
		error = null;
		try {
			await jobs.create({
				campaignId: id,
				scanIds: Array.from(selectedScans),
				providerName: formData.providerName || undefined,
				providerModel: formData.providerModel || undefined,
				forceReprocess: formData.forceReprocess
			});
			goto(`/workspace/${id}/jobs`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save job';
		} finally {
			submitting = false;
		}
	}

	async function handleRun() {
		if (!campaignId) return;
		const id = campaignId;
		if (selectedScans.size === 0) {
			error = 'Please select at least one scan';
			return;
		}
		submitting = true;
		error = null;
		try {
			const job = await jobs.create({
				campaignId: id,
				scanIds: Array.from(selectedScans),
				providerName: formData.providerName || undefined,
				providerModel: formData.providerModel || undefined,
				forceReprocess: formData.forceReprocess
			});
			if (job.jobId) {
				await jobs.start(job.jobId);
			}
			goto(`/workspace/${id}/jobs`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create and run job';
		} finally {
			submitting = false;
		}
	}

	onMount(() => {
		campaigns.fetchAll();
		fetchScans();
		fetchProviders();
	});
</script>

<svelte:head>
	<title>Create New Job — {campaign?.unique_name || campaign?.title || 'Campaign'} — Votecatcher</title>
	<meta name="description" content="Create a new job for this campaign." />
</svelte:head>

{#if scansLoading || providersLoading}
	<LoadingState loading={true} />
{:else if error && scans.length === 0}
	<ErrorDisplay message={error} onRetry={() => { error = null; fetchScans(); fetchProviders(); }} />
{:else if providers.length === 0}
	<div class="max-w-2xl mx-auto">
		<div class="rounded-md bg-amber-50 p-4 text-amber-800">
			<svg class="inline-block h-5 w-5 text-amber-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
				<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 2v2m-2 2a2 2 0 002 4h3m6v10H7l5 4m0 3-4m4 4m6 1v3m0-4V4" />
			</svg>
			<div>
				<p class="font-medium">No LLM Providers Configured</p>
				<p class="mt-1 text-sm">
					Configure an LLM provider first to create jobs.
					<a href="/workspace/settings" class="text-blue-600 hover:text-blue-800 underline">Go to Settings</a>
				</p>
			</div>
		</div>
	</div>
{:else}
	<div class="space-y-6">
		<div>
			<div class="flex items-center justify-between mb-4">
				<h1 class="text-2xl font-bold text-slate-900">Create New Job</h1>
				<p class="text-slate-600">{campaign?.unique_name || campaign?.title || 'Campaign'}</p>
			</div>
			<a href="/workspace/{campaignId}/jobs" class="text-slate-500 hover:text-slate-700 text-sm">
				Back to Jobs
			</a>
		</div>

		{#if error}
			<div class="rounded-md bg-red-50 p-4 text-red-800">
				{error}
			</div>
		{/if}

		<div class="rounded-lg border border-slate-200 p-6">
			<h2 class="text-lg font-semibold text-slate-900 mb-4">File Selection</h2>

			{#if scans.length === 0}
				<p class="text-slate-500 text-sm">No petition scans uploaded yet.</p>
				<p class="mt-2 text-sm">
					<a href="/workspace/{campaignId}/upload" class="text-blue-600 hover:text-blue-800 underline">
						Upload petition files first
					</a>
				</p>
			{:else}
				<div class="space-y-3">
					{#each scans as scan}
						<label class="flex items-center gap-3 p-3 rounded-md border border-slate-200 hover:bg-slate-50 cursor-pointer">
							<input
								type="checkbox"
								checked={selectedScans.has(scan.id)}
								onchange={() => toggleScan(scan.id)}
								class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
							/>
							<div class="flex-1">
								<p class="font-medium text-slate-900">{scan.original_filename}</p>
								<p class="text-sm text-slate-500">
									{scan.page_count ?? '?'} pages - Uploaded {formatDate(scan.uploaded_at)}
								</p>
							</div>
						</label>
					{/each}
				</div>

				<p class="text-sm text-slate-500 mt-4">
					{scans.length} scan(s) available. {selectedScans.size} selected.
				</p>
			{/if}
		</div>

		<div class="rounded-lg border border-slate-200 p-6">
			<h2 class="text-lg font-semibold text-slate-900 mb-4">Provider Selection</h2>

			<div class="space-y-3">
				<div>
					<label for="provider" class="block text-sm font-medium text-slate-700 mb-1">
						LLM Provider
					</label>
					<select
						id="provider"
						bind:value={formData.providerName}
						class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
					>
						{#each providers as provider}
							<option value={provider.provider}>
								{provider.provider.charAt(0).toUpperCase() + provider.provider.slice(1)}
								{#if !provider.is_configured}(not configured){/if}
							</option>
						{/each}
					</select>
				</div>

				<div>
					<label for="model" class="block text-sm font-medium text-slate-700 mb-1">
						Model
					</label>
					<select
						id="model"
						bind:value={formData.providerModel}
						class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
					>
						{#each providers as provider}
							<option value={provider.model}>{provider.model}</option>
						{/each}
					</select>
				</div>

				<div class="flex items-start gap-3 pt-2">
					<input
						type="checkbox"
						id="forceReprocess"
						bind:checked={formData.forceReprocess}
						class="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
					/>
					<div>
						<label for="forceReprocess" class="text-sm font-medium text-slate-700 cursor-pointer">
							Re-process all crops
						</label>
						<p class="text-xs text-slate-500">
							When checked, will re-run OCR on all crops even if results already exist.
						</p>
					</div>
				</div>
			</div>
		</div>

		<div class="flex justify-end gap-3 pt-6 border-t border-slate-200">
			<Button variant="secondary" text="Cancel" onclick={() => goto(`/workspace/${campaignId}/jobs`)} type="button" />
			<Button variant="secondary" text="Save" onclick={handleSave} disabled={submitting || selectedScans.size === 0} type="button" />
			<Button variant="primary" text="Run" onclick={handleRun} disabled={submitting || selectedScans.size === 0} type="button" />
		</div>
	</div>
{/if}
