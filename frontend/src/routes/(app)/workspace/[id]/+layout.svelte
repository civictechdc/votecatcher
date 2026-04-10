<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { events } from '$lib/stores/events';
	import { jobs } from '$lib/stores/jobs';
	import { CampaignSidebar } from '$lib/components/layout';

	let { children } = $props();

	const campaignId = $derived($page.params.id ?? '');
	const campaignName = $derived(
	 $campaigns.loading
         ? ''
         : $campaigns.campaigns.find(c => c.id === campaignId)?.uniqueName || $campaigns.campaigns.find(c => c.id === campaignId)?.title || 'Campaign'
     );

	function handleJobStatusEvent(e: CustomEvent) {
		jobs.handleStatusEvent(e.detail);
	}

	function handleJobProgressEvent(e: CustomEvent) {
		jobs.handleProgressEvent(e.detail);
	}

	function handleMetricsUpdatedEvent(e: CustomEvent) {
		campaigns.handleMetricsEvent(e.detail);
	}

	onMount(() => {
		if ($campaigns.campaigns.length === 0) {
			campaigns.fetchAll();
		}

		if (campaignId && campaignId !== 'demo') {
			events.connect(campaignId);
			document.addEventListener('votecatcher:job:status', handleJobStatusEvent as EventListener);
			document.addEventListener('votecatcher:job:progress', handleJobProgressEvent as EventListener);
			document.addEventListener('votecatcher:metrics:updated', handleMetricsUpdatedEvent as EventListener);
		}

		return () => {
			events.disconnect();
			document.removeEventListener('votecatcher:job:status', handleJobStatusEvent as EventListener);
			document.removeEventListener('votecatcher:job:progress', handleJobProgressEvent as EventListener);
			document.removeEventListener('votecatcher:metrics:updated', handleMetricsUpdatedEvent as EventListener);
		};
	});
</script>

<div class="flex min-h-screen bg-slate-50">
	<CampaignSidebar {campaignId} {campaignName} />
	<main class="flex-1 overflow-auto p-6">
		{@render children()}
	</main>
</div>
