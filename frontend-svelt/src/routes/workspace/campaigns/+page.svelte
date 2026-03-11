<script lang="ts">
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, Table, LoadingState, Modal, ErrorDisplay } from '$lib/components/ui';
	import type { CampaignResponse } from '$lib/api/generated';

	let showCreateModal = $state(false);
	let showDeleteModal = $state(false);
	let campaignToDelete = $state<{ id: string; name: string } | null>(null);
	let formData = $state({
		name: '',
		year: 2024,
		region: 'DC'
	});

	const columns = [
		{ key: 'name', label: 'Name', sortable: true },
		{ key: 'year', label: 'Year', sortable: true },
		{ key: 'region', label: 'Region', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	onMount(() => {
		campaigns.fetchAll();
	});

	function getTableRows(campaignList: CampaignResponse[]) {
		return campaignList.map((campaign) => ({
			id: campaign.id,
			name: campaign.unique_name || campaign.title || '',
			year: campaign.year,
			region: campaign.region || '',
			actions: `<button data-campaign-id="${campaign.id}" data-campaign-name="${campaign.unique_name || campaign.title || ''}" class="delete-btn text-red-600 hover:text-red-800 text-sm font-medium" aria-label="Delete ${campaign.unique_name || campaign.title}">Delete</button>`
		}));
	}

	async function handleCreate() {
		try {
			await campaigns.create(formData);
			showCreateModal = false;
			formData = { name: '', year: 2024, region: 'DC' };
		} catch (error) {
			// Error handled by store
		}
	}

	function handleDeleteClick(event: Event) {
		const target = event.target as HTMLElement;
		if (target.classList.contains('delete-btn')) {
			const id = target.dataset.campaignId;
			const name = target.dataset.campaignName || 'this campaign';
			if (id) {
				campaignToDelete = { id, name };
				showDeleteModal = true;
			}
		}
	}

	async function confirmDelete() {
		if (campaignToDelete) {
			await campaigns.delete(campaignToDelete.id);
			showDeleteModal = false;
			campaignToDelete = null;
		}
	}

	function handleRetry() {
		campaigns.fetchAll();
	}
</script>

<svelte:head>
	<title>Campaigns — Votecatcher</title>
	<meta name="description" content="Manage your campaigns. Create, view, and delete election campaigns." />
</svelte:head>

{#if $campaigns.loading}
	<LoadingState loading={true} />
{:else if $campaigns.error}
	<ErrorDisplay message={$campaigns.error} onRetry={handleRetry} />
{:else}
	<div class="space-y-6" onclick={handleDeleteClick} role="region" aria-label="Campaigns list">
		<div class="flex items-center justify-between">
			<h1 class="text-3xl font-bold text-slate-900">Campaigns</h1>
			<Button variant="primary" text="Create Campaign" onclick={() => (showCreateModal = true)} />
		</div>

		<Table
			columns={columns}
			rows={getTableRows($campaigns.campaigns)}
			emptyMessage="No campaigns yet. Create your first campaign to get started."
		/>
	</div>
{/if}

<Modal open={showCreateModal} onClose={() => (showCreateModal = false)} title="Create Campaign">
	<form onsubmit={(e) => { e.preventDefault(); handleCreate(); }} class="space-y-4">
		<div>
			<label for="name" class="block text-sm font-medium text-slate-700 mb-1">
				Name
			</label>
			<input
				type="text"
				id="name"
				bind:value={formData.name}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
				placeholder="Enter campaign name"
				required
			/>
		</div>

		<div>
			<label for="year" class="block text-sm font-medium text-slate-700 mb-1">
				Year
			</label>
			<input
				type="number"
				id="year"
				bind:value={formData.year}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
				required
			/>
		</div>

		<div>
			<label for="region" class="block text-sm font-medium text-slate-700 mb-1">
				Region
			</label>
			<input
				type="text"
				id="region"
				bind:value={formData.region}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
				placeholder="e.g., DC"
				required
			/>
		</div>

		<div class="flex justify-end gap-3 pt-4">
			<Button variant="secondary" text="Cancel" onclick={() => (showCreateModal = false)} type="button" />
			<Button variant="primary" text="Create" type="submit" />
		</div>
	</form>
</Modal>

<Modal open={showDeleteModal} onClose={() => { showDeleteModal = false; campaignToDelete = null; }} title="Delete Campaign">
	<div class="space-y-4">
		<p class="text-slate-600">
			Are you sure you want to delete <strong>{campaignToDelete?.name}</strong>? This action cannot be undone.
		</p>
		<div class="flex justify-end gap-3 pt-4">
			<Button variant="secondary" text="Cancel" onclick={() => { showDeleteModal = false; campaignToDelete = null; }} type="button" />
			<Button variant="danger" text="Delete" onclick={confirmDelete} type="button" />
		</div>
	</div>
</Modal>
