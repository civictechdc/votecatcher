<script lang="ts">
	import { Button, LoadingSpinner } from '$lib/components/ui';
	import { results } from '$lib/stores/results';
	import { Download } from 'lucide-svelte';

	interface Props {
		jobId: number;
	}

	let { jobId }: Props = $props();
	let exporting = $state(false);
	let error = $state<string | null>(null);

	async function handleExport() {
		exporting = true;
		error = null;

		try {
			const csv = await results.exportCSV(jobId);

			// Create download
			const blob = new Blob([csv], { type: 'text/csv' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `results-job-${jobId}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Export failed';
		} finally {
			exporting = false;
		}
	}

	function clearError() {
		error = null;
	}
</script>

<div class="inline-block">
	{#if error}
		<div class="flex items-center gap-2">
			<p class="text-sm text-red-600">{error}</p>
			<button
				type="button"
				onclick={clearError}
				class="text-sm text-slate-600 hover:text-slate-900"
				aria-label="Dismiss error"
			>
				×
			</button>
		</div>
	{:else}
		<Button
			variant="secondary"
			onclick={handleExport}
			disabled={exporting}
		>
			{#if exporting}
				<LoadingSpinner size="sm" />
				<span>Exporting...</span>
			{:else}
				<Download class="h-4 w-4" />
				<span>Export CSV</span>
			{/if}
		</Button>
	{/if}
</div>
