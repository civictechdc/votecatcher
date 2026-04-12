<script lang="ts">
	import { page } from '$app/stores';
	import { Sidebar } from '$lib/components/layout';
	let { children } = $props();

	// Check if we're on a campaign-scoped route (has ID parameter)
	const isCampaignRoute = $derived(!!$page.params.id);
</script>

{#if isCampaignRoute}
	{@render children()}
{:else}
	<div class="flex min-h-screen bg-slate-50">
		<Sidebar />
		<main class="flex-1 overflow-auto p-6">
			{@render children()}
		</main>
	</div>
{/if}
