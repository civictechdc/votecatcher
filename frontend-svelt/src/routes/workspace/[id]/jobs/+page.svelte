<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { jobs } from '$lib/stores/jobs';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, Table, LoadingState, Modal, ErrorDisplay } from '$lib/components/ui';
	import type { JobResponse } from '$lib/api/generated';

	interface ProviderConfig {
		provider: string;
		model: string;
		isConfigured: boolean;
		lastValidated?: string;
	}

	let campaignId = $derived($page.params.id);

	let showCreateModal = $state(false);
	let showCancelModal = $state(false);
	let jobToCancel = $state<{ id: number; status: string } | null>(null);
	let providers = $state<ProviderConfig[]>([]);
	let providersLoading = $state(false);
	let formData = $state({
		providerName: '',
		providerModel: ''
	});

	const CANCELABLE_STATES = ['NOT_STARTED', 'OCR_PENDING', 'OCR_STARTED'];

	const statusColors: Record<string, string> = {
		NOT_STARTED: 'bg-gray-100 text-gray-800',
		OCR_PENDING: 'bg-yellow-100 text-yellow-800',
		OCR_STARTED: 'bg-blue-100 text-blue-800',
		OCR_COMPLETED: 'bg-green-100 text-green-800',
		OCR_FAILED: 'bg-red-100 text-red-800',
		OCR_TIMEOUT: 'bg-red-100 text-red-800',
		MATCHING_PENDING: 'bg-yellow-100 text-yellow-800',
		MATCHING: 'bg-blue-100 text-blue-800',
		MATCHING_COMPLETED: 'bg-green-100 text-green-800',
		MATCHING_ERROR: 'bg-red-100 text-red-800',
		CANCELLED: 'bg-gray-100 text-gray-600'
	};

	function formatStatus(status: string): string {
		return status.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
	}

	function formatDate(date: Date | string | null | undefined): string {
		if (!date) return '-';
		const d = typeof date === 'string' ? new Date(date) : date;
		return d.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	const columns = [
		{ key: 'id', label: 'ID', sortable: true },
		{ key: 'status', label: 'Status', sortable: true },
		{ key: 'created', label: 'Created', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	async function fetchProviders() {
		providersLoading = true;
		try {
			const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
			const response = await fetch(`${baseUrl}/api/settings/providers`);
			if (response.ok) {
				providers = await response.json();
				if (providers.length > 0 && !formData.providerName) {
					const configured = providers.find(p => p.isConfigured);
					if (configured) {
						formData.providerName = configured.provider;
						formData.providerModel = configured.model;
					} else {
						formData.providerName = providers[0].provider;
						formData.providerModel = providers[0].model;
					}
				}
			}
		} catch (error) {
			console.error('Failed to fetch providers:', error);
		} finally {
			providersLoading = false;
		}
	}

	onMount(() => {
		jobs.fetchAll();
		campaigns.fetchAll();
		fetchProviders();
	});

	const campaignJobs = $derived($jobs.jobs.filter(job => String(job.campaignId) === String(campaignId)));

	const availableModels = $derived(() => {
		const provider = providers.find(p => p.provider === formData.providerName);
		if (!provider) return [];
		return [{ name: provider.model, configured: provider.isConfigured }];
	});

	function handleProviderChange() {
		const provider = providers.find(p => p.provider === formData.providerName);
		if (provider) {
			formData.providerModel = provider.model;
		}
	}

	function getTableRows(jobList: JobResponse[]) {
		return jobList.map((job) => {
			const canCancel = CANCELABLE_STATES.includes(job.status);
			return {
				id: `<a href="/workspace/${campaignId}/jobs/${job.jobId}" class="text-blue-600 hover:text-blue-800 font-medium">#${job.jobId}</a>`,
				status: `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[job.status] || 'bg-gray-100 text-gray-800'}">${formatStatus(job.status)}</span>`,
				created: formatDate(job.createdAt),
				actions: canCancel
					? `<button data-job-id="${job.jobId}" data-job-status="${job.status}" class="cancel-btn text-red-600 hover:text-red-800 text-sm font-medium mr-3" aria-label="Cancel job ${job.jobId}">Cancel</button><a href="/workspace/${campaignId}/jobs/${job.jobId}" class="text-blue-600 hover:text-blue-800 text-sm font-medium">View</a>`
					: `<a href="/workspace/${campaignId}/jobs/${job.jobId}" class="text-blue-600 hover:text-blue-800 text-sm font-medium">View</a>`
			};
		});
	}

	function handleCancelClick(event: Event) {
		const target = event.target as HTMLElement;
		if (target.classList.contains('cancel-btn')) {
			const id = target.dataset.jobId;
			const status = target.dataset.jobStatus || '';
			if (id) {
				jobToCancel = { id: parseInt(id), status };
				showCancelModal = true;
			}
		}
	}

	async function confirmCancel() {
		if (jobToCancel) {
			try {
				await jobs.cancel(jobToCancel.id);
				showCancelModal = false;
				jobToCancel = null;
			} catch (error) {
			}
		}
	}

	async function handleCreate() {
		if (!campaignId) return;
		try {
			await jobs.create({
				campaignId: campaignId,
				providerName: formData.providerName || undefined,
				providerModel: formData.providerModel || undefined
			});
			showCreateModal = false;
			formData = { providerName: '', providerModel: '' };
		} catch (error) {
		}
	}

	function handleRetry() {
		jobs.fetchAll();
	}

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));
</script>

<svelte:head>
	<title>Jobs — {campaign?.unique_name || campaign?.title || 'Campaign'} — Votecatcher</title>
	<meta name="description" content="View and manage OCR and matching jobs for this campaign." />
</svelte:head>

{#if $jobs.loading && $jobs.jobs.length === 0}
	<LoadingState loading={true} />
{:else if $jobs.error}
	<ErrorDisplay message={$jobs.error} onRetry={handleRetry} />
{:else}
	<div class="space-y-6" onclick={handleCancelClick} role="region" aria-label="Jobs list">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-3xl font-bold text-slate-900">Jobs</h1>
				<p class="mt-1 text-slate-600">{campaign?.unique_name || campaign?.title || 'Campaign'}</p>
			</div>
			<Button variant="primary" text="Create Job" onclick={() => (showCreateModal = true)} />
		</div>

		<Table
			columns={columns}
			rows={getTableRows(campaignJobs)}
			emptyMessage="No jobs yet for this campaign. Create your first job to get started."
		/>
	</div>
{/if}

<Modal open={showCreateModal} onClose={() => (showCreateModal = false)} title="Create Job">
	<form onsubmit={(e) => { e.preventDefault(); handleCreate(); }} class="space-y-4">
		{#if providersLoading}
			<div class="text-slate-500">Loading providers...</div>
		{:else if providers.length === 0}
			<div class="text-amber-600 bg-amber-50 p-3 rounded-md">
				No LLM providers configured. <a href="/workspace/settings" class="underline">Configure a provider</a> first.
			</div>
		{:else}
			<div>
				<label for="provider" class="block text-sm font-medium text-slate-700 mb-1">
					LLM Provider
				</label>
				<select
					id="provider"
					bind:value={formData.providerName}
					onchange={handleProviderChange}
					class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
				>
					{#each providers as provider}
						<option value={provider.provider}>
							{provider.provider.charAt(0).toUpperCase() + provider.provider.slice(1)}
							{#if !provider.isConfigured}(not configured){/if}
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
					{#each availableModels() as model}
						<option value={model.name}>{model.name}</option>
					{/each}
				</select>
			</div>
		{/if}

		<div class="flex justify-end gap-3 pt-4">
			<Button variant="secondary" text="Cancel" onclick={() => (showCreateModal = false)} type="button" />
			<Button variant="primary" text="Create" type="submit" disabled={providers.length === 0} />
		</div>
	</form>
</Modal>

<Modal open={showCancelModal} onClose={() => { showCancelModal = false; jobToCancel = null; }} title="Cancel Job">
	<div class="space-y-4">
		<p class="text-slate-600">
			Are you sure you want to cancel job <strong>#{jobToCancel?.id}</strong>? This action cannot be undone.
		</p>
		<div class="flex justify-end gap-3 pt-4">
			<Button variant="secondary" text="No, Keep Running" onclick={() => { showCancelModal = false; jobToCancel = null; }} type="button" />
			<Button variant="danger" text="Yes, Cancel" onclick={confirmCancel} type="button" />
		</div>
	</div>
</Modal>
