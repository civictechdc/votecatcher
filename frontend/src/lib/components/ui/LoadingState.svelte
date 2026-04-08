<script lang="ts">
	import type { Snippet } from 'svelte';
	import LoadingSpinner from './LoadingSpinner.svelte';
	import ErrorDisplay from './ErrorDisplay.svelte';

	interface Props {
		loading?: boolean;
		error?: string | null;
		children?: Snippet;
	}

	let {
		loading = false,
		error = null,
		children
	}: Props = $props();
</script>

{#if error}
	<ErrorDisplay message={error} />
{:else if loading}
	<LoadingSpinner />
{:else if children}
	{@render children()}
{/if}
