<script lang="ts">
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, Table, LoadingState, Modal, ErrorDisplay } from '$lib/components/ui';
	import type { Campaign } from '$lib/api/generated';

	let showCreateModal = $state(false);
	let formData = $state({
		name: '',
		year: 2024,
		regionId: 1
	});

	const columns = [
		{ key: 'name', label: 'Name', sortable: true },
		{ key: 'year', label: 'Year', sortable: true },
		{ key: 'regionId', label: 'Region', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	onMount(() => {
		campaigns.fetchAll();
	});

	function getTableRows(campaignList: Campaign[]) {
		return campaignList.map((campaign) => ({
			id: campaign.id,
			name: campaign.name,
			year: campaign.year,
			regionId: campaign.regionId,
			actions: `<button data-campaign-id="${campaign.id}" class="delete-btn text-red-600 hover:text-red-800 text-sm font-medium" aria-label="Delete ${campaign.name}">Delete</button>`
		}));
	}

	async function handleCreate() {
		try {
			await campaigns.create(formData);
			showCreateModal = false;
			formData = { name: '', year: 2024, regionId: 1 };
		} catch (error) {
			// Error handled by store
		}
	}

	function handleDeleteClick(event: Event) {
		const target = event.target as HTMLElement;
		if (target.classList.contains('delete-btn')) {
			const id = parseInt(target.dataset.campaignId || '0', 10);
			if (id && confirm('Are you sure you want to delete this campaign?')) {
				campaigns.delete(id);
			}
		}
	}

	function handleRetry() {
		campaigns.fetchAll();
	}
</script>

<svelte:head>
	<title>Campaigns - Votecatcher</title>
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
			<label for="regionId" class="block text-sm font-medium text-slate-700 mb-1">
				Region
			</label>
			<input
				type="number"
				id="regionId"
				bind:value={formData.regionId}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border"
				placeholder="e.g., 1 for DC"
				required
			/>
		</div>

		<div class="flex justify-end gap-3 pt-4">
			<Button variant="secondary" text="Cancel" onclick={() => (showCreateModal = false)} type="button" />
			<Button variant="primary" text="Create" type="submit" />
		</div>
	</form>
</Modal>
