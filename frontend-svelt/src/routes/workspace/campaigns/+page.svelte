<script lang="ts">
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, Table, LoadingState, Modal, ErrorDisplay } from '$lib/components/ui';
	import type { CampaignResponse } from '$lib/api/generated';
	import type { SortConfig } from '$lib/components/ui/Table.svelte';

	let showCreateModal = $state(false);
	let showDeleteModal = $state(false);
	let campaignToDelete = $state<{ id: string; name: string } | null>(null);
	let formData = $state({
		name: '',
		year: 2024,
		region: 'DC'
	});
	let sortConfig = $state<SortConfig | null>({ key: 'created_at', direction: 'desc' });
	let searchQuery = $state('');

	const columns = [
		{ key: 'name', label: 'Name', sortable: true },
		{ key: 'year', label: 'Year', sortable: true },
		{ key: 'region', label: 'Region', sortable: true },
		{ key: 'created_at', label: 'Created', sortable: true },
		{ key: 'updated_at', label: 'Last Updated', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	onMount(() => {
		campaigns.fetchAll();
	});

	function formatDate(date: Date | null | undefined): string {
		if (!date) return '-';
		return new Date(date).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function filterCampaigns(campaignList: CampaignResponse[], query: string): CampaignResponse[] {
		if (!query.trim()) return campaignList;
		const lowerQuery = query.toLowerCase();
		return campaignList.filter(c =>
			(c.unique_name || c.title || '').toLowerCase().includes(lowerQuery) ||
			(c.region || '').toLowerCase().includes(lowerQuery) ||
			String(c.year).includes(query)
		);
	}

	function sortCampaigns(campaignList: CampaignResponse[], config: SortConfig | null): CampaignResponse[] {
		if (!config) return campaignList;

		return [...campaignList].sort((a, b) => {
			let aVal: string | number;
			let bVal: string | number;

			switch (config.key) {
				case 'name':
					aVal = (a.unique_name || a.title || '').toLowerCase();
					bVal = (b.unique_name || b.title || '').toLowerCase();
					break;
				case 'year':
					aVal = parseInt(String(a.year)) || 0;
					bVal = parseInt(String(b.year)) || 0;
					break;
				case 'region':
					aVal = (a.region || '').toLowerCase();
					bVal = (b.region || '').toLowerCase();
					break;
				case 'created_at':
					aVal = a.created_at ? new Date(a.created_at).getTime() : 0;
					bVal = b.created_at ? new Date(b.created_at).getTime() : 0;
					break;
				case 'updated_at':
					aVal = a.updated_at ? new Date(a.updated_at).getTime() : 0;
					bVal = b.updated_at ? new Date(b.updated_at).getTime() : 0;
					break;
				default:
					return 0;
			}

			if (aVal < bVal) return config.direction === 'asc' ? -1 : 1;
			if (aVal > bVal) return config.direction === 'asc' ? 1 : -1;
			return 0;
		});
	}

	const filteredAndSortedCampaigns = $derived(
		sortCampaigns(filterCampaigns($campaigns.campaigns, searchQuery), sortConfig)
	);

	function getTableRows(campaignList: CampaignResponse[]) {
		return campaignList.map((campaign) => ({
			id: campaign.id,
			name: `<a href="/workspace/${campaign.id}" class="text-blue-600 hover:text-blue-800 font-medium">${campaign.unique_name || campaign.title || ''}</a>`,
			year: campaign.year,
			region: campaign.region || '',
			created_at: formatDate(campaign.created_at),
			updated_at: formatDate(campaign.updated_at),
			actions: `<button data-campaign-id="${campaign.id}" data-campaign-name="${campaign.unique_name || campaign.title || ''}" class="delete-btn text-red-600 hover:text-red-800 text-sm font-medium" aria-label="Delete ${campaign.unique_name || campaign.title}">Delete</button>`
		}));
	}

	async function handleCreate() {
		try {
			await campaigns.create(formData);
			showCreateModal = false;
			formData = { name: '', year: 2024, region: 'DC' };
		} catch (error) {
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

		<div class="flex items-center gap-4">
			<div class="relative flex-1 max-w-md">
				<input
					type="search"
					placeholder="Search campaigns..."
					bind:value={searchQuery}
					class="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm"
					aria-label="Search campaigns"
				/>
				<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
			</div>
			{#if searchQuery}
				<span class="text-sm text-slate-500">
					{filteredAndSortedCampaigns.length} of {$campaigns.campaigns.length} campaigns
				</span>
			{/if}
		</div>

		<Table
			columns={columns}
			rows={getTableRows(filteredAndSortedCampaigns)}
			sortable={true}
			sortConfig={sortConfig}
			onSortChange={(config) => (sortConfig = config)}
			emptyMessage={searchQuery ? 'No campaigns match your search.' : 'No campaigns yet. Create your first campaign to get started.'}
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
