<script lang="ts">
	import { onMount } from 'svelte';
	import { jobs } from '$lib/stores/jobs';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, Table, LoadingState, Modal, ErrorDisplay } from '$lib/components/ui';
	import type { JobResponse } from '$lib/api/generated';

	let showCreateModal = $state(false);
	let showCancelModal = $state(false);
	let jobToCancel = $state<{ id: number; status: string } | null>(null);
	let formData = $state({
		campaignId: '',
		provider: 'openai'
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
		{ key: 'campaign', label: 'Campaign', sortable: true },
		{ key: 'status', label: 'Status', sortable: true },
		{ key: 'created', label: 'Created', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	onMount(() => {
		jobs.fetchAll();
		campaigns.fetchAll();
	});

	function getTableRows(jobList: JobResponse[]) {
		return jobList.map((job) => {
			const canCancel = CANCELABLE_STATES.includes(job.status);
			return {
				id: job.jobId,
				campaign: job.campaignName || job.campaignId,
				status: `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[job.status] || 'bg-gray-100 text-gray-800'}">${formatStatus(job.status)}</span>`,
				created: formatDate(job.createdAt),
				actions: canCancel
					? `<button data-job-id="${job.jobId}" data-job-status="${job.status}" class="cancel-btn text-red-600 hover:text-red-800 text-sm font-medium" aria-label="Cancel job ${job.jobId}">Cancel</button>`
					: `<span class="text-gray-400 text-sm">-</span>`
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
				// Error handled by store
			}
		}
	}

	async function handleCreate() {
		try {
			await jobs.create({
				campaignId: formData.campaignId,
				provider: formData.provider
			});
			showCreateModal = false;
			formData = { campaignId: '', provider: 'openai' };
		} catch (error) {
			// Error handled by store
		}
	}

	function handleRetry() {
		jobs.fetchAll();
	}

	let availableCampaigns = $derived($campaigns.campaigns);
</script>

<svelte:head>
	<title>Jobs — Votecatcher</title>
	<meta name="description" content="View and manage OCR and matching jobs. Monitor job progress in real-time." />
</svelte:head>

{#if $jobs.loading && $jobs.jobs.length === 0}
	<LoadingState loading={true} />
{:else if $jobs.error}
	<ErrorDisplay message={$jobs.error} onRetry={handleRetry} />
{:else}
	<div class="space-y-6" onclick={handleCancelClick} role="region" aria-label="Jobs list">
		<div class="flex items-center justify-between">
			<h1 class="text-3xl font-bold text-slate-900">Jobs</h1>
			<Button variant="primary" text="Create Job" onclick={() => (showCreateModal = true)} />
		</div>

		<Table
			columns={columns}
			rows={getTableRows($jobs.jobs)}
			emptyMessage="No jobs yet. Create your first job to get started."
		/>
	</div>
{/if}

<Modal open={showCreateModal} onClose={() => (showCreateModal = false)} title="Create Job">
	<form onsubmit={(e) => { e.preventDefault(); handleCreate(); }} class="space-y-4">
		<div>
			<label for="campaign" class="block text-sm font-medium text-slate-700 mb-1">
				Campaign
			</label>
			<select
				id="campaign"
				bind:value={formData.campaignId}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
				required
			>
				<option value="" disabled>Select a campaign</option>
				{#each availableCampaigns as campaign}
					<option value={campaign.id}>{campaign.unique_name || campaign.title}</option>
				{/each}
			</select>
		</div>

		<div>
			<label for="provider" class="block text-sm font-medium text-slate-700 mb-1">
				OCR Provider
			</label>
			<select
				id="provider"
				bind:value={formData.provider}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
			>
				<option value="openai">OpenAI</option>
				<option value="gemini">Gemini</option>
			</select>
		</div>

		<div class="flex justify-end gap-3 pt-4">
			<Button variant="secondary" text="Cancel" onclick={() => (showCreateModal = false)} type="button" />
			<Button variant="primary" text="Create" type="submit" />
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
