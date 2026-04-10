<script lang="ts">
	import { Button } from '$lib/components/ui';
	import { AlertTriangle, Home, RefreshCw } from 'lucide-svelte';

	let { status, message } = $props();

	const statusMessage: Record<number, string> = {
		400: 'Bad Request',
		401: 'Unauthorized',
		403: 'Forbidden',
		404: 'Page Not Found',
		500: 'Server Error',
		502: 'Bad Gateway',
		503: 'Service Unavailable'
	};

	function getStatusTitle(code: number): string {
		return statusMessage[code] || 'Error';
	}

	function handleRefresh() {
		window.location.reload();
	}
</script>

<svelte:head>
	<title>{status} — {getStatusTitle(status)} — Votecatcher</title>
</svelte:head>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4">
	<div class="max-w-md text-center">
		<div class="mb-6 flex justify-center">
			<div class="rounded-full bg-red-100 p-4">
				<AlertTriangle class="h-12 w-12 text-red-600" />
			</div>
		</div>

		<h1 class="mb-2 text-6xl font-bold text-slate-900">{status}</h1>
		<h2 class="mb-4 text-xl font-medium text-slate-700">{getStatusTitle(status)}</h2>

		<p class="mb-8 text-slate-600">
			{message || 'An unexpected error occurred. Please try again.'}
		</p>

		<div class="flex flex-col gap-3 sm:flex-row sm:justify-center">
			<a href="/">
				<Button variant="primary">
					<Home class="mr-2 h-4 w-4" />
					Return Home
				</Button>
			</a>
			<Button variant="secondary" onclick={handleRefresh}>
				<RefreshCw class="mr-2 h-4 w-4" />
				Try Again
			</Button>
		</div>

		{#if status >= 500}
			<p class="mt-6 text-sm text-slate-500">
				If this problem persists, please contact support.
			</p>
		{/if}
	</div>
</div>
