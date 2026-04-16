<script lang="ts">
	import { onMount } from 'svelte';
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { campaigns } from '$lib/stores/campaigns';
	import { jobs } from '$lib/stores/jobs';
	import { Button, LoadingState } from '$lib/components/ui';
	import { ConfidenceDonut, ProgressStepper } from '$lib/components/dashboard';
	import { API_BASE_URL } from '$lib/api/base-url';
	const API_BASE = API_BASE_URL;
	const campaignId = $derived($page.params.id ?? '');

	let metrics = $state({
		totalSignatures: 0,
		processed: 0,
		highConfidence: 0,
		mediumConfidence: 0,
		lowConfidence: 0,
		progressPercentage: 0,
		voterListCount: null as number | null
	});
	let loading = $state(true);

	interface SetupStatus {
		voter_list: {
			exists: boolean;
			rowCount: number | null;
			uploadedAt: string | null;
			regionName: string | null;
		};
		petitions: {
			exists: boolean;
			fileCount: number;
			signatureCount: number;
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
				const data = await response.json();
				setupStatus = {
					voter_list: {
						exists: data.voter_list?.exists ?? false,
						rowCount: data.voter_list?.rowCount ?? null,
						uploadedAt: data.voter_list?.uploadedAt ?? null,
						regionName: data.voter_list?.regionName ?? null,
					},
					petitions: {
						exists: data.petitions?.exists ?? false,
						fileCount: data.petitions?.fileCount ?? 0,
						signatureCount: data.petitions?.signatureCount ?? 0,
					},
					jobs: data.jobs ?? { total: 0, active: 0 },
					state: data.state ?? "empty",
				};
			}
		} catch (error) {
			console.error('Failed to fetch setup status:', error);
		} finally {
			loadingStatus = false;
		}
	}

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));
	const campaignJobs = $derived(
		$jobs.jobs
			.filter(job => String(job.campaignId) === String(campaignId))
			.sort((a, b) => {
				const aTime = a.createdAt ? new Date(a.createdAt).getTime() : 0;
				const bTime = b.createdAt ? new Date(b.createdAt).getTime() : 0;
				return bTime - aTime;
			})
	);
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
					totalSignatures: data.totalSignatures ?? 0,
					processed: data.processed ?? 0,
					highConfidence: data.highConfidence ?? 0,
					mediumConfidence: data.mediumConfidence ?? 0,
					lowConfidence: data.lowConfidence ?? 0,
					progressPercentage: data.progressPercentage ?? 0,
					voterListCount: data.voterListCount ?? null
				};
			}
		} catch (error) {
			console.error('Failed to fetch metrics:', error);
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		campaigns.fetchAll();
		jobs.fetchAll();
		fetchMetrics();
		fetchSetupStatus();

		document.addEventListener('votecatcher:setup:updated', fetchSetupStatus as EventListener);

		return () => {
			document.removeEventListener('votecatcher:setup:updated', fetchSetupStatus as EventListener);
		};
	});

	afterNavigate(({ from, to }) => {
		if (from?.url.pathname !== to?.url.pathname) {
			fetchSetupStatus();
		}
	});
</script>

<svelte:head>
	<title>{campaign?.uniqueName || campaign?.title || 'Campaign'} — Votecatcher</title>
	<meta name="description" content="Campaign dashboard for signature verification." />
</svelte:head>

{#if loading}
	<LoadingState loading={true} />
{:else}
	<div class="space-y-6">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-3xl font-bold text-slate-900">{campaign?.uniqueName || campaign?.title || 'Campaign'}</h1>
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
				<h3 class="text-sm font-medium text-slate-600">Voter List</h3>
				<p class="mt-2 text-3xl font-bold {metrics.voterListCount ? 'text-slate-900' : 'text-slate-400'}">
					{metrics.voterListCount ?? 'N/A'}
				</p>
				{#if metrics.voterListCount}
					<p class="mt-1 text-sm text-slate-500">registered voters</p>
				{:else}
					<p class="mt-1 text-sm text-slate-500">
						<a href="/workspace/{campaignId}/upload" class="text-blue-600 hover:underline">Upload voter list</a>
					</p>
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
									<div class="text-right">
										<div class="text-xs text-slate-500">{job.createdAt ? new Date(job.createdAt).toLocaleDateString() : '-'}</div>
										<div class="text-xs text-slate-400">{job.createdAt ? new Date(job.createdAt).toLocaleTimeString() : ''}</div>
									</div>
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
