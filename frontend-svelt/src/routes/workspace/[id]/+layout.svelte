<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { CampaignSidebar } from '$lib/components/layout';

	let { children, data } = $props();

	const campaignId = $derived($page.params.id);
	const campaign = $derived($campaigns.campaigns.find(c => c.id === campaignId));
	const campaignName = $derived(campaign?.unique_name || campaign?.title || 'Campaign');

	onMount(() => {
		if ($campaigns.campaigns.length === 0) {
			campaigns.fetchAll();
		}
	});
</script>

<div class="flex min-h-screen bg-slate-50">
	<CampaignSidebar {campaignId} {campaignName} />
	<main class="flex-1 overflow-auto p-6">
		{@render children()}
	</main>
</div>
