<script lang="ts">
	import { onMount } from 'svelte';
	import { featureFlags } from '$lib/stores/featureFlags';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();

	onMount(() => {
		featureFlags.load();
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
