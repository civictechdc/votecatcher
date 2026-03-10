<script lang="ts">
	import { uploads } from '$lib/stores/uploads';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, LoadingSpinner } from '$lib/components/ui';
	import { Upload, CheckCircle, AlertCircle } from 'lucide-svelte';
	import { onMount } from 'svelte';

	let fileInput = $state<HTMLInputElement | null>(null);
	let selectedFile: File | null = $state(null);
	let selectedCampaignId = $state<string>('');

	// Use derived to calculate campaign options
	const campaignOptions = $derived(
		$campaigns.campaigns.map((c) => ({
			value: String(c.id),
			label: c.name
		}))
	);

	onMount(() => {
		campaigns.fetchAll();
	});

	$effect(() => {
		if ($campaigns.campaigns.length > 0 && !selectedCampaignId) {
			selectedCampaignId = String($campaigns.campaigns[0].id);
		}
	});

	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files[0]) {
			selectedFile = input.files[0];
			uploads.uploadPetition(selectedFile, selectedCampaignId);
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
			selectedFile = event.dataTransfer.files[0];
			uploads.uploadPetition(selectedFile, selectedCampaignId);
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
	}

	function handleRetry() {
		selectedFile = null;
		uploads.clearErrors();
		if (fileInput) {
			fileInput.value = '';
		}
	}
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold text-slate-900">Upload Petition</h1>
		<p class="mt-2 text-slate-600">Upload a PDF petition to extract signatures</p>
	</div>

	{#if $uploads.petitionError}
		<div class="rounded-lg bg-red-50 border border-red-200 p-6">
			<div class="flex items-start gap-4">
				<AlertCircle class="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
				<div class="flex-1">
					<h3 class="font-semibold text-red-900">Upload Failed</h3>
					<p class="mt-1 text-red-700">{$uploads.petitionError}</p>
				</div>
			</div>
			<div class="mt-4 flex gap-3">
				<Button variant="secondary" onclick={handleRetry}>
					Try Again
				</Button>
			</div>
		</div>
	{:else if $uploads.petitionUploading}
		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<div class="flex items-center gap-4">
				<LoadingSpinner />
				<div class="flex-1">
					<p class="font-medium text-slate-900">Uploading petition...</p>
					<div class="mt-2 h-2 w-full rounded-full bg-slate-200">
						<div
							class="h-full rounded-full bg-blue-600 transition-all"
							style="width: {$uploads.petitionProgress}%"
						></div>
					</div>
					<p class="mt-1 text-sm text-slate-600">{$uploads.petitionProgress}%</p>
				</div>
			</div>
		</div>
	{:else if $uploads.petitionProgress === 100 && $uploads.lastUploadResult}
		<div class="rounded-lg bg-green-50 border border-green-200 p-6">
			<div class="flex items-center gap-4">
				<CheckCircle class="h-6 w-6 text-green-600" />
				<div>
					<h3 class="font-semibold text-green-900">Petition uploaded successfully!</h3>
					<p class="mt-1 text-green-700">
						{$uploads.lastUploadResult.crop_count} signatures detected and ready for processing.
					</p>
				</div>
			</div>
		</div>
	{:else if $campaigns.campaigns.length === 0}
		<div class="rounded-lg bg-yellow-50 border border-yellow-200 p-6">
			<p class="text-yellow-900">
				Please create a campaign first before uploading petitions.
			</p>
		</div>
	{:else}
		<div class="space-y-4">
			<div>
				<label for="campaign" class="block text-sm font-medium text-slate-700 mb-1">
					Campaign
				</label>
				<select
					id="campaign"
					bind:value={selectedCampaignId}
					class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
					aria-label="Campaign"
				>
					{#each campaignOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
			</div>

			<div
				class="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-12 text-center"
				ondrop={handleDrop}
				ondragover={handleDragOver}
				role="button"
				tabindex="0"
			>
				<Upload class="mx-auto h-12 w-12 text-slate-400" />
				<p class="mt-4 text-lg font-medium text-slate-900">Drag and drop your file here</p>
				<p class="mt-2 text-sm text-slate-600">or click to browse</p>

				<input
					bind:this={fileInput}
					type="file"
					accept=".pdf"
					onchange={handleFileSelect}
					class="mt-4"
					disabled={$campaigns.campaigns.length === 0}
					aria-label="File"
				/>

				<p class="mt-4 text-xs text-slate-500">
					Supported formats: PDF only
				</p>
			</div>
		</div>
	{/if}
</div>
