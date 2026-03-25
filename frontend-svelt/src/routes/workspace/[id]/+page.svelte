<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { campaigns } from '$lib/stores/campaigns';
	import { jobs } from '$lib/stores/jobs';
	import { Button, LoadingState } from '$lib/components/ui';
	import { ConfidenceDonut, ProgressStepper } from '$lib/components/dashboard';
	import { PUBLIC_API_URL } from '$env/static/public';

	const API_BASE = PUBLIC_API_URL || 'http://localhost:8080';

	let campaignId = $derived($page.params.id);

	let metrics = $state({
		totalSignatures: 0,
		processed: 0,
		highConfidence: 0,
		mediumConfidence: 0,
		lowConfidence: 0,
		progressPercentage: 0
	});
	let loading = $state(true);
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	interface SetupStatus {
		voter_list: {
			exists: boolean;
			row_count?: number;
			uploaded_at?: string;
			region_name?: string;
		};
		petitions: {
			exists: boolean;
			file_count?: number;
			signature_count?: number;
		};
		jobs: {
			total: number;
			active: number;
		};
		state: string;
	}

	let setupStatus = $state<SetupStatus | null>(null);
	let loadingStatus = $state(true);

	async function fetchSetupStatus() {
		try {
			const response = await fetch(`${API_BASE}/api/campaigns/${campaignId}/setup-status`);
			if (response.ok) {
				setupStatus = await response.json();
			}
		} catch (error) {
			console.error('Failed to fetch setup status:', error);
		} finally {
			loadingStatus = false;
		}
	}

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));
	const campaignJobs = $derived($jobs.jobs.filter(job => String(job.campaignId) === String(campaignId)));
	const highPercentage = $derived(metrics.totalSignatures > 0 ? (metrics.highConfidence / metrics.totalSignatures) * 100 : 0);
	const hasCrops = $derived(metrics.totalSignatures > 0);
	const hasMatchResults = $derived(metrics.processed > 0);

	function formatMetric(value: number, hasData: boolean): string | number {
		return hasData ? value : 'N/A';
	}

	async function fetchMetrics() {
		try {
			const response = await fetch(`${API_BASE}/api/campaigns/${campaignId}/metrics`);
			if (response.ok) {
				const data = await response.json();
				metrics = {
					totalSignatures: data.total_signatures ?? 0,
					processed: data.processed ?? 0,
					highConfidence: data.high_confidence ?? 0,
					mediumConfidence: data.medium_confidence ?? 0,
					lowConfidence: data.low_confidence ?? 0,
					progressPercentage: data.progress_percentage ?? 0
				};
			}
		} catch (error) {
			console.error('Failed to fetch metrics:', error);
		} finally {
			loading = false;
		}
	}

	const ACTIVE_JOB_STATES = ['NOT_STARTED', 'OCR_PENDING', 'OCR_STARTED', 'MATCHING_PENDING', 'MATCHING'];
	const POLL_INTERVAL_MS = 30000;

	onMount(() => {
		campaigns.fetchAll();
		jobs.fetchAll();
		fetchMetrics();
		fetchSetupStatus();

		pollInterval = setInterval(fetchMetrics, POLL_INTERVAL_MS);
	});

	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});
</script>

<svelte:head>
	<title>{campaign?.unique_name || campaign?.title || 'Campaign'} — Votecatcher</title>
	<meta name="description" content="Campaign dashboard for signature verification." />
</svelte:head>

{#if loading}
	<LoadingState loading={true} />
{:else}
	<div class="space-y-6">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-3xl font-bold text-slate-900">{campaign?.unique_name || campaign?.title || 'Campaign'}</h1>
				<p class="mt-1 text-slate-600">{campaign?.region || ''} • {campaign?.year || ''}</p>
			</div>
			<div class="flex gap-3">
				<Button variant="secondary" text="Upload Files" onclick={() => window.location.href = `/workspace/${campaignId}/upload`} />
				<Button variant="primary" text="New Job" onclick={() => window.location.href = `/workspace/${campaignId}/jobs`} />
			</div>
		</div>

		{#if !loadingStatus && setupStatus && !hasMatchResults}
			<ProgressStepper
				voterListStatus={setupStatus.voter_list}
				petitionStatus={setupStatus.petitions}
				hasJobs={setupStatus.jobs.total > 0}
				{campaignId}
			/>
		{/if}

		<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4" data-testid="metrics">
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Total Signatures</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">{formatMetric(metrics.totalSignatures, hasCrops)}</p>
			</div>
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Processed</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">{formatMetric(metrics.processed, hasMatchResults)}</p>
				{#if hasMatchResults}
					<p class="mt-1 text-sm text-slate-500">{metrics.progressPercentage.toFixed(1)}% complete</p>
				{/if}
			</div>
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Active Jobs</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">{campaignJobs.filter(j => ['NOT_STARTED', 'OCR_PENDING', 'OCR_STARTED', 'MATCHING'].includes(j.status)).length}</p>
			</div>
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">High Confidence</h3>
				<p class="mt-2 text-3xl font-bold {hasMatchResults ? 'text-green-600' : 'text-slate-400'}">{formatMetric(metrics.highConfidence, hasMatchResults)}</p>
				{#if hasMatchResults}
					<p class="mt-1 text-sm text-slate-500">{highPercentage}% of total</p>
				{/if}
			</div>
		</div>

		<div class="grid gap-6 lg:grid-cols-2">
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h2 class="text-lg font-semibold text-slate-900">Confidence Distribution</h2>
				<p class="mt-1 text-sm text-slate-500">Match confidence breakdown</p>

				<div class="mt-6">
					{#if hasMatchResults}
						<ConfidenceDonut
							high={metrics.highConfidence}
							medium={metrics.mediumConfidence}
							low={metrics.lowConfidence}
							total={metrics.totalSignatures}
						/>
					{:else}
						<div class="flex flex-col items-center justify-center py-8 text-slate-500">
							<svg class="w-12 h-12 mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
							</svg>
							<p class="text-sm">No match results yet</p>
							<p class="text-xs mt-1">Run a job to see confidence distribution</p>
						</div>
					{/if}
				</div>
			</div>

			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<div class="flex items-center justify-between">
					<h2 class="text-lg font-semibold text-slate-900">Recent Jobs</h2>
					<a href="/workspace/{campaignId}/jobs" class="text-sm text-blue-600 hover:text-blue-700">View all</a>
				</div>

				{#if campaignJobs.length === 0}
					<p class="mt-4 text-sm text-slate-500">No jobs yet. Create your first job to get started.</p>
				{:else}
					<div class="mt-4 space-y-3">
						{#each campaignJobs.slice(0, 5) as job}
							<a href="/workspace/{campaignId}/jobs/{job.jobId}" class="block rounded-lg border border-slate-200 p-3 hover:bg-slate-50">
								<div class="flex items-center justify-between">
									<span class="text-sm font-medium text-slate-900">Job #{job.jobId}</span>
									<span class="text-xs text-slate-500">{job.createdAt ? new Date(job.createdAt).toLocaleDateString() : '-'}</span>
								</div>
								<span class="mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium {job.status === 'MATCHING_COMPLETED' ? 'bg-green-100 text-green-800' : job.status.includes('FAILED') || job.status.includes('ERROR') ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}">
									{job.status.replace(/_/g, ' ')}
								</span>
							</a>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<h2 class="text-lg font-semibold text-slate-900">Quick Actions</h2>
			<div class="mt-4 flex flex-wrap gap-3">
				<Button variant="secondary" text="Upload Voter List" onclick={() => window.location.href = `/workspace/${campaignId}/upload`} />
				<Button variant="secondary" text="Upload Petitions" onclick={() => window.location.href = `/workspace/${campaignId}/upload`} />
				{#if hasMatchResults}
					<Button variant="secondary" text="View Results" onclick={() => window.location.href = `/workspace/${campaignId}/results`} />
				{/if}
			</div>
		</div>
	</div>
{/if}
