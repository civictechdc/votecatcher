<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { jobs } from '$lib/stores/jobs';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, Table, LoadingState, Modal, ErrorDisplay } from '$lib/components/ui';
	import type { JobResponse } from '$lib/api/generated';
	import type { SortConfig } from '$lib/components/ui/Table.svelte';
	import { PUBLIC_API_URL } from '$env/static/public';

	interface ProviderConfig {
		provider: string;
		model: string;
		is_configured: boolean;
		last_validated?: string;
	}

	type StatusFilter = 'all' | 'not_started' | 'running' | 'completed' | 'failed';

	let campaignId = $derived($page.params.id);

	let showCreateModal = $state(false);
	let showCancelModal = $state(false);
	let jobToCancel = $state<{ id: number; status: string } | null>(null);
	let providers = $state<ProviderConfig[]>([]);
	let providersLoading = $state(false);
	let formData = $state({
		providerName: '',
		providerModel: '',
		forceReprocess: false
	});
	let sortConfig = $state<SortConfig | null>({ key: 'created', direction: 'desc' });
	let statusFilter = $state<StatusFilter>('all');
	let hasScans = $state<boolean | null>(null);

	const API_BASE = (PUBLIC_API_URL || 'http://localhost:8080') + '/api';

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
		{ key: 'updated', label: 'Updated', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	function statusMatchesFilter(status: string, filter: StatusFilter): boolean {
		if (filter === 'all') return true;
		if (filter === 'not_started') return status === 'NOT_STARTED';
		if (filter === 'running') return ['OCR_PENDING', 'OCR_STARTED', 'MATCHING_PENDING', 'MATCHING'].includes(status);
		if (filter === 'completed') return ['OCR_COMPLETED', 'MATCHING_COMPLETED'].includes(status);
		if (filter === 'failed') return ['OCR_FAILED', 'OCR_TIMEOUT', 'MATCHING_ERROR', 'CANCELLED'].includes(status);
		return true;
	}

	function sortJobs(jobList: JobResponse[], config: SortConfig | null): JobResponse[] {
		if (!config) return jobList;
		return [...jobList].sort((a, b) => {
			let aVal: string | number = 0;
			let bVal: string | number = 0;

			switch (config.key) {
				case 'id':
					aVal = a.jobId;
					bVal = b.jobId;
					break;
				case 'status':
					aVal = a.status;
					bVal = b.status;
					break;
				case 'created':
					aVal = a.createdAt ? new Date(a.createdAt).getTime() : 0;
					bVal = b.createdAt ? new Date(b.createdAt).getTime() : 0;
					break;
				case 'updated':
					aVal = a.updatedAt ? new Date(a.updatedAt).getTime() : 0;
					bVal = b.updatedAt ? new Date(b.updatedAt).getTime() : 0;
					break;
				default:
					return 0;
			}

			if (aVal < bVal) return config.direction === 'asc' ? -1 : 1;
			if (aVal > bVal) return config.direction === 'asc' ? 1 : -1;
			return 0;
		});
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
			}
		} catch (error) {
			console.error('Failed to fetch providers:', error);
		} finally {
			providersLoading = false;
		}
	}

	async function checkScans() {
		try {
			const response = await fetch(`${API_BASE}/campaigns/${campaignId}/scans`);
			if (response.ok) {
				const data = await response.json();
				hasScans = data.total > 0;
			}
		} catch (error) {
			console.error('Failed to check scans:', error);
		}
	}

	onMount(() => {
		jobs.fetchAll();
		campaigns.fetchAll();
		fetchProviders();
		checkScans();
	});

	const campaignJobs = $derived($jobs.jobs.filter(job => String(job.campaignId) === String(campaignId)));
	const filteredJobs = $derived(campaignJobs.filter(job => statusMatchesFilter(job.status, statusFilter)));
	const sortedJobs = $derived(sortJobs(filteredJobs, sortConfig));

	const availableModels = $derived(() => {
		const provider = providers.find(p => p.provider === formData.providerName);
		if (!provider) return [];
		return [{ name: provider.model, configured: provider.is_configured }];
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
				updated: formatDate(job.updatedAt),
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
				providerModel: formData.providerModel || undefined,
				forceReprocess: formData.forceReprocess
			});
			showCreateModal = false;
		} catch (error) {
		}
	}

	function openCreateModal() {
		formData = { providerName: '', providerModel: '', forceReprocess: false };
		fetchProviders();
		showCreateModal = true;
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
			<Button variant="primary" text="Create Job" onclick={openCreateModal} disabled={hasScans === false} />
		</div>

		{#if hasScans === false}
			<div class="rounded-md bg-amber-50 p-4">
				<div class="flex">
					<svg class="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
					</svg>
					<div class="ml-3">
						<h3 class="text-sm font-medium text-amber-800">No uploads yet</h3>
						<p class="mt-1 text-sm text-amber-700">
							Upload petition files before creating jobs.
							<a href="/workspace/{campaignId}/upload" class="font-medium underline">Go to Upload</a>
						</p>
					</div>
				</div>
			</div>
		{/if}

		<div class="flex items-center gap-4">
			<div class="flex-1">
				<label for="status-filter" class="sr-only">Filter by status</label>
				<div class="relative inline-block">
					<select
						id="status-filter"
						bind:value={statusFilter}
						class="min-w-40 appearance-none rounded-md border border-slate-300 bg-white px-3 py-2 pr-10 text-sm shadow-sm hover:border-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
					>
						<option value="all">All Statuses</option>
						<option value="not_started">Not Started</option>
						<option value="running">Running</option>
						<option value="completed">Completed</option>
						<option value="failed">Failed</option>
					</select>
					<span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-slate-500">
						<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
						</svg>
					</span>
				</div>
			</div>
			{#if statusFilter !== 'all'}
				<span class="text-sm text-slate-500">
					{filteredJobs.length} of {campaignJobs.length} jobs
				</span>
			{/if}
		</div>

		<Table
			columns={columns}
			rows={getTableRows(sortedJobs)}
			sortable={true}
			sortConfig={sortConfig}
			onSortChange={(config) => (sortConfig = config)}
			emptyMessage={statusFilter !== 'all' ? 'No jobs match the selected filter.' : 'No jobs yet for this campaign. Create your first job to get started.'}
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
					{#each availableModels() as model}
						<option value={model.name}>{model.name}</option>
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
						Use this to refresh data with a different provider.
					</p>
				</div>
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
