<script lang="ts">
	import { page } from '$app/stores';
	import { jobs } from '$lib/stores/jobs';
	import { Button, LoadingSpinner, ErrorDisplay } from '$lib/components/ui';
	import { onMount, onDestroy } from 'svelte';
	import type { Job } from '$lib/api/generated';

	type JobWithProgress = Job & { progress?: number };

	let jobId = $derived($page.params.id);

	onMount(() => {
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
			OCR_STARTED: 'OCR Started',
			OCR_COMPLETED: 'OCR Completed',
			MATCHING_PENDING: 'Matching Pending',
			MATCHING: 'Matching',
			MATCHING_COMPLETED: 'Matching Completed',
			CANCELLED: 'Cancelled',
			OCR_FAILED: 'OCR Failed',
			OCR_TIMEOUT: 'OCR Timeout',
			MATCHING_ERROR: 'Matching Error'
		};
		return labels[status] || status;
	}

	function isActiveStatus(status: string): boolean {
		return ['NOT_STARTED', 'OCR_PENDING', 'OCR_STARTED', 'MATCHING_PENDING', 'MATCHING'].includes(
			status
		);
	}

	function getProgress(job: JobWithProgress): number {
		return Math.round(job.progress || 0);
	}
</script>

<svelte:head>
	<title>Job Status - Votecatcher</title>
</svelte:head>

<div class="space-y-6">
	{#if $jobs.error}
		<ErrorDisplay title="Error loading job" message={$jobs.error} />
	{:else if $jobs.loading}
		<div class="flex items-center justify-center p-12">
			<LoadingSpinner size="lg" />
		</div>
	{:else if $jobs.currentJob}
		<div>
			<h1 class="text-3xl font-bold text-slate-900">Job Status</h1>
			<p class="mt-2 text-slate-600">Job ID: {$jobs.currentJob.id}</p>
		</div>

		<div class="grid gap-6 md:grid-cols-2">
			<!-- Status Card -->
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<div class="space-y-4">
					<div>
						<p class="text-sm font-medium text-slate-600">Status</p>
						<p class="mt-1 text-2xl font-semibold text-slate-900">
							{getStatusLabel($jobs.currentJob.status)}
						</p>
					</div>

					<!-- SSE Connection Status -->
					<div class="flex items-center gap-2">
						<div
							class="h-2 w-2 rounded-full {$jobs.sse.connected ? 'bg-green-500' : 'bg-red-500'}"
						></div>
						<span class="text-sm text-slate-600">
							{$jobs.sse.connected ? 'Connected' : 'Disconnected'}
						</span>
					</div>

					<!-- Progress -->
					{#if isActiveStatus($jobs.currentJob.status)}
						<div class="space-y-2">
							<div class="flex justify-between text-sm">
								<span class="font-medium text-slate-700">Progress</span>
								<span class="font-medium text-slate-900">
									{getProgress($jobs.currentJob as JobWithProgress)}%
								</span>
							</div>
							<div
								class="h-3 w-full rounded-full bg-slate-200"
								role="progressbar"
								aria-valuenow={getProgress($jobs.currentJob as JobWithProgress)}
								aria-valuemin={0}
								aria-valuemax={100}
								aria-label="Job progress"
							>
								<div
									class="h-full rounded-full bg-blue-600 transition-all"
									style="width: {getProgress($jobs.currentJob as JobWithProgress)}%"
								></div>
							</div>
						</div>
					{/if}

					<!-- Cancel Button (only for active jobs) -->
					{#if isActiveStatus($jobs.currentJob.status)}
						<div class="pt-4">
							<Button variant="danger" onclick={handleCancel}>Cancel Job</Button>
						</div>
					{/if}
				</div>
			</div>

			<!-- Additional Info Card -->
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h2 class="text-lg font-semibold text-slate-900">Job Details</h2>
				<dl class="mt-4 space-y-3">
					<div>
						<dt class="text-sm font-medium text-slate-600">Campaign ID</dt>
						<dd class="mt-1 text-sm text-slate-900">{$jobs.currentJob.campaignId}</dd>
					</div>
					<div>
						<dt class="text-sm font-medium text-slate-600">Created At</dt>
						<dd class="mt-1 text-sm text-slate-900">
							{new Date($jobs.currentJob.createdAt).toLocaleString()}
						</dd>
					</div>
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
