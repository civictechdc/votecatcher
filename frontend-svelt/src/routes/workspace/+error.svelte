<script lang="ts">
	import { Button } from '$lib/components/ui';
	import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-svelte';

	let { status, message } = $props();

	function handleRefresh() {
		window.location.reload();
	}

	function handleGoBack() {
		window.history.back();
	}
</script>

<svelte:head>
	<title>{status} — Error — Votecatcher</title>
</svelte:head>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4">
	<div class="max-w-md text-center">
		<div class="mb-6 flex justify-center">
			<div class="rounded-full bg-red-100 p-4">
				<AlertTriangle class="h-12 w-12 text-red-600" />
			</div>
		</div>

		<h1 class="mb-2 text-4xl font-bold text-slate-900">{status}</h1>
		<p class="mb-6 text-slate-600">
			{message || 'Something went wrong in your workspace.'}
		</p>

		<div class="flex flex-col gap-3 sm:flex-row sm:justify-center">
			<Button variant="secondary" onclick={handleGoBack}>
				<ArrowLeft class="mr-2 h-4 w-4" />
				Go Back
			</Button>
			<Button variant="primary" onclick={handleRefresh}>
				<RefreshCw class="mr-2 h-4 w-4" />
				Try Again
			</Button>
		</div>
	</div>
</div>
