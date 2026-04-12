<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { LoadingSpinner } from '$lib/components/ui';

	const STATUS_TIMEOUT_MS = 5000;

	let { children } = $props();

	let checking = $state(true);
	let connectionWarning = $state(false);

	onMount(async () => {
		let timedOut = false;
		const timer = setTimeout(() => {
			timedOut = true;
			checking = false;
			connectionWarning = true;
		}, STATUS_TIMEOUT_MS);

		try {
			const result = await api.database.getStatus();
			clearTimeout(timer);

			if (!timedOut) {
				if (result.ok && !result.data.configured) {
					goto('/setup');
					return;
				}
			}
		} catch {
			clearTimeout(timer);
			if (!timedOut) {
				connectionWarning = true;
			}
		} finally {
			checking = false;
		}
	});
</script>

{#if checking}
	<div class="flex min-h-screen items-center justify-center">
		<LoadingSpinner />
	</div>
{:else}
	{#if connectionWarning}
		<div class="bg-amber-50 px-4 py-2 text-center text-sm text-amber-700" role="status">
			Could not reach the backend. Some features may be unavailable.
		</div>
	{/if}
	<main>
		{@render children()}
	</main>
{/if}
