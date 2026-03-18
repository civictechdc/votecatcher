<script lang="ts">
	import { page } from '$app/stores';
	import { jobs } from '$lib/stores/jobs';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, LoadingSpinner, ErrorDisplay } from '$lib/components/ui';
	import { onMount, onDestroy } from 'svelte';

	let campaignId = $derived($page.params.id);
	let jobId = $derived($page.params.job_id);

	onMount(() => {
		campaigns.fetchAll();
		if (jobId) {
			jobs.connectToJob(jobId);
			jobs.fetch(parseInt(jobId));
		}
	});

	onDestroy(() => {
		jobs.disconnect();
	});

	async function handleCancel() {
		if (jobId) {
			await jobs.cancel(parseInt(jobId));
		}
	}

	function getStatusLabel(status: string): string {
		const labels: Record<string, string> = {
			NOT_STARTED: 'Not Started',
			OCR_PENDING: 'OCR Pending',
			OCR_STARTED: 'OCR In Progress',
			OCR_COMPLETED: 'OCR Completed',
			MATCHING_PENDING: 'Matching Pending',
			MATCHING: 'Matching In Progress',
			MATCHING_COMPLETED: 'Completed',
			CANCELLED: 'Cancelled',
			OCR_FAILED: 'OCR Failed',
			OCR_TIMEOUT: 'OCR Timeout',
			MATCHING_ERROR: 'Matching Error'
		};
		return labels[status] || status;
	}

	function getStatusPhase(status: string): 'pending' | 'ocr' | 'matching' | 'completed' | 'error' | 'cancelled' {
		if (status === 'CANCELLED') return 'cancelled';
		if (['OCR_FAILED', 'OCR_TIMEOUT', 'MATCHING_ERROR'].includes(status)) return 'error';
		if (status === 'MATCHING_COMPLETED') return 'completed';
		if (['MATCHING', 'MATCHING_PENDING'].includes(status)) return 'matching';
		if (['OCR_STARTED', 'OCR_PENDING', 'OCR_COMPLETED'].includes(status)) return 'ocr';
		return 'pending';
	}

	const statusSteps = [
		{ key: 'pending', label: 'Pending' },
		{ key: 'ocr', label: 'OCR Processing' },
		{ key: 'matching', label: 'Matching' },
		{ key: 'completed', label: 'Completed' }
	] as const;

	function getStepStyle(stepKey: string, jobStatus: string): { bgClass: string; textClass: string } {
		const currentPhase = getStatusPhase(jobStatus);
		const stepIndex = statusSteps.findIndex(s => s.key === currentPhase);
		const stepOrder = statusSteps.findIndex(s => s.key === stepKey);
		const isActive = stepKey === currentPhase;
		const isCompleted = stepIndex > stepOrder || (currentPhase === 'completed' && stepKey !== 'completed');
		const isError = currentPhase === 'error' && isActive;
		const isCancelled = currentPhase === 'cancelled';

		if (isError) return { bgClass: 'bg-red-500', textClass: 'text-red-600 font-medium' };
		if (isCancelled) return { bgClass: 'bg-slate-300', textClass: 'text-slate-500' };
		if (isCompleted) return { bgClass: 'bg-green-500', textClass: 'text-slate-500' };
		if (isActive) return { bgClass: 'bg-blue-500', textClass: 'text-blue-600 font-medium' };
		return { bgClass: 'bg-slate-200', textClass: 'text-slate-500' };
	}

	function isActiveStatus(status: string): boolean {
		return ['NOT_STARTED', 'OCR_PENDING', 'OCR_STARTED', 'MATCHING_PENDING', 'MATCHING'].includes(
			status
		);
	}

	function formatDate(date: Date | string | null | undefined): string {
		if (!date) return '-';
		const d = typeof date === 'string' ? new Date(date) : date;
		return d.toLocaleString();
	}

	function formatDuration(startedAt: Date | string | null, endedAt: Date | string | null): string {
		if (!startedAt || !endedAt) return '-';
		const start = typeof startedAt === 'string' ? new Date(startedAt) : startedAt;
		const end = typeof endedAt === 'string' ? new Date(endedAt) : endedAt;
		const diffMs = end.getTime() - start.getTime();
		if (diffMs < 1000) return `${diffMs}ms`;
		const diffSeconds = Math.floor(diffMs / 1000);
		if (diffSeconds < 60) return `${diffSeconds}s`;
		const diffMinutes = Math.floor(diffSeconds / 60);
		if (diffMinutes < 60) {
			const secs = diffSeconds % 60;
			return secs > 0 ? `${diffMinutes}m ${secs}s` : `${diffMinutes}m`;
		}
		const diffHours = Math.floor(diffMinutes / 60);
		if (diffHours < 24) {
			const mins = diffMinutes % 60;
			return mins > 0 ? `${diffHours}h ${mins}m` : `${diffHours}h`;
		}
		const diffDays = Math.floor(diffHours / 24);
		const hrs = diffHours % 24;
		return hrs > 1 ? `${diffDays}d ${hrs}h` : `${diffDays}d`;
	}

	function isTerminalStatus(status: string): boolean {
		return ['MATCHING_COMPLETED', 'CANCELLED', 'OCR_FAILED', 'OCR_TIMEOUT', 'MATCHING_ERROR'].includes(status);
	}

	const campaign = $derived($campaigns.campaigns.find(c => String(c.id) === String(campaignId)));
</script>

<svelte:head>
	<title>Job #{jobId} — {campaign?.unique_name || campaign?.title || 'Campaign'} — Votecatcher</title>
	<meta name="description" content="Job status and progress details." />
</svelte:head>

<div class="space-y-6">
	<div>
		<nav class="mb-2 text-sm text-slate-500">
			<a href="/workspace/{campaignId}" class="hover:text-slate-700">Dashboard</a>
			<span class="mx-2">/</span>
			<a href="/workspace/{campaignId}/jobs" class="hover:text-slate-700">Jobs</a>
			<span class="mx-2">/</span>
			<span class="text-slate-900">Job #{jobId}</span>
		</nav>
		<h1 class="text-3xl font-bold text-slate-900">Job Status</h1>
		<p class="mt-1 text-slate-600">{campaign?.unique_name || campaign?.title || 'Campaign'}</p>
	</div>

	{#if $jobs.error}
		<ErrorDisplay title="Error loading job" message={$jobs.error} />
	{:else if $jobs.loading}
		<div class="flex items-center justify-center p-12">
			<LoadingSpinner size="lg" />
		</div>
	{:else if $jobs.currentJob}
		<div class="grid gap-6 md:grid-cols-2">
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<div class="space-y-4">
					<div>
						<p class="text-sm font-medium text-slate-600">Status</p>
						<p class="mt-1 text-2xl font-semibold text-slate-900">
							{getStatusLabel($jobs.currentJob.status)}
						</p>
					</div>

					<div class="space-y-2">
						<p class="text-sm font-medium text-slate-700">Pipeline</p>
						<div class="flex items-center gap-1">
							{#each statusSteps as step}
								{@const style = getStepStyle(step.key, $jobs.currentJob.status)}
								<div class="flex-1">
									<div class="h-2 rounded-full transition-colors {style.bgClass}"></div>
									<p class="mt-1 text-xs text-center {style.textClass}">
										{step.label}
									</p>
								</div>
							{/each}
						</div>
					</div>

					{#if isActiveStatus($jobs.currentJob.status)}
						<div class="flex items-center gap-2">
							<div
								class="h-2 w-2 rounded-full {$jobs.sse.connected ? 'bg-green-500' : 'bg-red-500'}"
							></div>
							<span class="text-sm text-slate-600">
								{$jobs.sse.connected ? 'Connected' : 'Connecting...'}
							</span>
						</div>
						<div class="pt-4">
							<Button variant="danger" onclick={handleCancel}>Cancel Job</Button>
						</div>
					{/if}
				</div>
			</div>

			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h2 class="text-lg font-semibold text-slate-900">Job Details</h2>
				<dl class="mt-4 space-y-3">
					<div>
						<dt class="text-sm font-medium text-slate-600">Job ID</dt>
						<dd class="mt-1 text-sm text-slate-900">{$jobs.currentJob.jobId}</dd>
					</div>
					<div>
						<dt class="text-sm font-medium text-slate-600">Created At</dt>
						<dd class="mt-1 text-sm text-slate-900">
							{formatDate($jobs.currentJob.createdAt)}
						</dd>
					</div>
					{#if $jobs.currentJob.startedAt}
						<div>
							<dt class="text-sm font-medium text-slate-600">Started At</dt>
							<dd class="mt-1 text-sm text-slate-900">
								{formatDate($jobs.currentJob.startedAt)}
							</dd>
						</div>
					{/if}
					{#if isTerminalStatus($jobs.currentJob.status) && $jobs.currentJob.endedAt}
						<div>
							<dt class="text-sm font-medium text-slate-600">Ended At</dt>
							<dd class="mt-1 text-sm text-slate-900">
								{formatDate($jobs.currentJob.endedAt)}
							</dd>
						</div>
					{/if}
					{#if isTerminalStatus($jobs.currentJob.status) && $jobs.currentJob.startedAt && $jobs.currentJob.endedAt}
						<div>
							<dt class="text-sm font-medium text-slate-600">Duration</dt>
							<dd class="mt-1 text-sm text-slate-900">
								{formatDuration($jobs.currentJob.startedAt, $jobs.currentJob.endedAt)}
							</dd>
						</div>
					{/if}
					{#if $jobs.currentJob.providerName}
						<div>
							<dt class="text-sm font-medium text-slate-600">Provider</dt>
							<dd class="mt-1 text-sm text-slate-900">{$jobs.currentJob.providerName}</dd>
						</div>
					{/if}
					{#if $jobs.currentJob.providerModel}
						<div>
							<dt class="text-sm font-medium text-slate-600">Model</dt>
							<dd class="mt-1 text-sm text-slate-900">{$jobs.currentJob.providerModel}</dd>
						</div>
					{/if}
					{#if $jobs.currentJob.status === 'MATCHING_COMPLETED' && ($jobs.currentJob.cachedOcrCount != null || $jobs.currentJob.newOcrCount != null)}
						<div>
							<dt class="text-sm font-medium text-slate-600">OCR Processing</dt>
							<dd class="mt-1 text-sm">
								{#if $jobs.currentJob.newOcrCount != null && $jobs.currentJob.newOcrCount > 0}
									<span class="text-green-700">{$jobs.currentJob.newOcrCount} new</span>
								{/if}
								{#if $jobs.currentJob.cachedOcrCount != null && $jobs.currentJob.cachedOcrCount > 0}
									{#if $jobs.currentJob.newOcrCount != null && $jobs.currentJob.newOcrCount > 0}
										<span class="text-slate-400 mx-1">·</span>
									{/if}
									<span class="text-amber-700">{$jobs.currentJob.cachedOcrCount} cached</span>
								{/if}
								{#if $jobs.currentJob.forceReprocess}
									<span class="ml-2 px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">re-processed</span>
								{/if}
							</dd>
						</div>
					{/if}
					{#if $jobs.currentJob.errorMessage}
						<div>
							<dt class="text-sm font-medium text-red-600">Error</dt>
							<dd class="mt-1 text-sm text-red-900">{$jobs.currentJob.errorMessage}</dd>
						</div>
					{/if}
				</dl>
			</div>
		</div>
	{:else}
		<div class="rounded-lg border border-slate-200 bg-white p-12 text-center">
			<p class="text-slate-600">Job not found</p>
		</div>
	{/if}
</div>
