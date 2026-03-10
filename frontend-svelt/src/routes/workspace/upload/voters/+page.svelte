<script lang="ts">
	import { uploads } from '$lib/stores/uploads';
	import { Button, LoadingSpinner } from '$lib/components/ui';
	import { Upload, CheckCircle, AlertCircle } from 'lucide-svelte';

	let fileInput = $state<HTMLInputElement | null>(null);
	let selectedFile: File | null = $state(null);

	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files[0]) {
			selectedFile = input.files[0];
			uploads.uploadVoterList(selectedFile);
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
			selectedFile = event.dataTransfer.files[0];
			uploads.uploadVoterList(selectedFile);
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
		<h1 class="text-3xl font-bold text-slate-900">Upload Voter List</h1>
		<p class="mt-2 text-slate-600">Upload a CSV or Excel file with voter registration data</p>
	</div>

	{#if $uploads.voterListError}
		<div class="rounded-lg bg-red-50 border border-red-200 p-6">
			<div class="flex items-start gap-4">
				<AlertCircle class="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
				<div class="flex-1">
					<h3 class="font-semibold text-red-900">Upload Failed</h3>
					<p class="mt-1 text-red-700">{$uploads.voterListError}</p>
				</div>
			</div>
			<div class="mt-4 flex gap-3">
				<Button variant="secondary" onclick={handleRetry}>
					Try Again
				</Button>
			</div>
		</div>
	{:else if $uploads.voterListUploading}
		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<div class="flex items-center gap-4">
				<LoadingSpinner />
				<div class="flex-1">
					<p class="font-medium text-slate-900">Uploading voter list...</p>
					<div class="mt-2 h-2 w-full rounded-full bg-slate-200">
						<div
							class="h-full rounded-full bg-blue-600 transition-all"
							style="width: {$uploads.voterListProgress}%"
						></div>
					</div>
					<p class="mt-1 text-sm text-slate-600">{$uploads.voterListProgress}%</p>
				</div>
			</div>
		</div>
	{:else if $uploads.voterListProgress === 100}
		<div class="rounded-lg bg-green-50 border border-green-200 p-6">
			<div class="flex items-center gap-4">
				<CheckCircle class="h-6 w-6 text-green-600" />
				<div>
					<h3 class="font-semibold text-green-900">Voter list uploaded successfully!</h3>
					<p class="mt-1 text-green-700">Your voter list has been processed and is ready to use.</p>
				</div>
			</div>
		</div>
	{:else}
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
				accept=".csv,.xlsx,.xls"
				onchange={handleFileSelect}
				class="mt-4"
				aria-label="File"
			/>

			<p class="mt-4 text-xs text-slate-500">
				Supported formats: CSV, Excel (.xlsx, .xls)
			</p>
		</div>
	{/if}
</div>
