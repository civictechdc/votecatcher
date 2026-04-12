<script lang="ts">
	import { Button } from '$lib/components/ui';
	import type { VoterListStatus, PetitionsStatus } from '$lib/api/generated/models/Campaign';

	interface Props {
		voterListStatus: VoterListStatus | null;
		petitionStatus: PetitionsStatus | null;
		hasJobs: boolean;
		campaignId: string;
	}

	let { voterListStatus, petitionStatus, hasJobs, campaignId }: Props = $props();

	const state = $derived(() => {
		const hasVoterList = voterListStatus?.exists ?? false;
		const hasPetitions = petitionStatus?.exists ?? false;

		if (!hasVoterList && !hasPetitions) return 'empty';
		if (hasVoterList && !hasPetitions) return 'voter_only';
		if (!hasVoterList && hasPetitions) return 'petitions_only';
		if (!hasJobs) return 'ready_to_process';
		return 'has_jobs';
	});

	function formatCount(count: number | undefined): string {
		if (!count) return '0';
		return count.toLocaleString();
	}

	function formatDate(dateStr: string | undefined): string {
		if (!dateStr) return '';
		return new Date(dateStr).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric'
		});
	}

	const ctaConfig = $derived(() => {
		switch (state()) {
			case 'empty':
				return { text: 'Upload Voter List', href: `/workspace/${campaignId}/upload` };
			case 'voter_only':
				return { text: 'Upload Petitions', href: `/workspace/${campaignId}/upload` };
			case 'petitions_only':
				return { text: 'Upload Voter List', href: `/workspace/${campaignId}/upload` };
			case 'ready_to_process':
				return { text: 'Create Job', href: `/workspace/${campaignId}/jobs` };
			default:
				return null;
		}
	});

	function navigate(href: string) {
		window.location.href = href;
	}
</script>

{#if state() !== 'has_jobs'}
	<div class="rounded-lg border border-slate-200 bg-white p-6 mb-6">
		<h2 class="text-lg font-semibold text-slate-900 mb-4">Campaign Setup</h2>

		<div class="space-y-3">
			<!-- Voter List Step -->
			<div class="flex items-center gap-3">
				{#if voterListStatus?.exists}
					<div class="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
						<svg class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div class="flex-1">
						<span class="font-medium text-slate-900">Voter List</span>
						<span class="text-sm text-slate-500 ml-2">
							{formatCount(voterListStatus.rowCount ?? undefined)} voters
							{#if voterListStatus.regionName}• {voterListStatus.regionName}{/if}
							{#if voterListStatus.uploadedAt}• Updated {formatDate(voterListStatus.uploadedAt)}{/if}
						</span>
					</div>
				{:else}
					<div class="flex-shrink-0 w-6 h-6 rounded-full border-2 border-slate-300"></div>
					<span class="text-slate-500">Voter List</span>
				{/if}
			</div>

			<!-- Petitions Step -->
			<div class="flex items-center gap-3">
				{#if petitionStatus?.exists}
					<div class="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
						<svg class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div class="flex-1">
						<span class="font-medium text-slate-900">Petitions</span>
						<span class="text-sm text-slate-500 ml-2">
							{petitionStatus.fileCount ?? 0} files
							{#if petitionStatus.signatureCount}• {petitionStatus.signatureCount} signatures{/if}
						</span>
					</div>
				{:else}
					<div class="flex-shrink-0 w-6 h-6 rounded-full border-2 border-slate-300"></div>
					<span class="text-slate-500">Petitions</span>
				{/if}
			</div>

			<!-- Run Job Step -->
			<div class="flex items-center gap-3">
				{#if hasJobs}
					<div class="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
						<svg class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
						</svg>
					</div>
					<span class="font-medium text-slate-900">Run Job</span>
				{:else}
					<div class="flex-shrink-0 w-6 h-6 rounded-full border-2 border-slate-300"></div>
					<span class="text-slate-500">Run Job</span>
				{/if}
			</div>
		</div>

		{#if ctaConfig()}
			<div class="mt-4 pt-4 border-t border-slate-200">
				<Button variant="primary" text={ctaConfig()!.text} onclick={() => navigate(ctaConfig()!.href)} />
			</div>
		{/if}
	</div>
{/if}
