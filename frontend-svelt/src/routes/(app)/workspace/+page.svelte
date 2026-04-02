<script lang="ts">
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, LoadingState } from '$lib/components/ui';

	let { data } = $props();

	onMount(() => {
		campaigns.fetchAll();
	});
</script>

<svelte:head>
	<title>Dashboard — Votecatcher</title>
	<meta name="description" content="Votecatcher campaign signature verification dashboard. View campaigns, jobs, and matching results." />
</svelte:head>

{#if $campaigns.loading}
	<LoadingState loading={true} />
{:else if $campaigns.error}
	<LoadingState error={$campaigns.error} />
{:else}
	<div class="space-y-6">
		<div>
			<h1 class="text-3xl font-bold text-slate-900">Dashboard</h1>
			<p class="mt-2 text-slate-600">Welcome to your workspace</p>
		</div>

		<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Active Campaigns</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">{$campaigns.campaigns.length}</p>
			</div>
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Running Jobs</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">0</p>
			</div>
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Pending Results</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">0</p>
			</div>
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Verified Signatures</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">0</p>
			</div>
		</div>

		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<h2 class="text-lg font-semibold text-slate-900">Quick Actions</h2>
			<div class="mt-4 flex gap-4">
				<Button variant="primary" onclick={() => window.location.href = '/workspace/campaigns'}>
					Create Campaign
				</Button>
				<Button variant="secondary" onclick={() => window.location.href = '/workspace/jobs'}>
					View Jobs
				</Button>
			</div>
		</div>
	</div>
{/if}
