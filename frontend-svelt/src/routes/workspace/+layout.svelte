<script lang="ts">
	import { Sidebar } from '$lib/components/layout';
	let { children } = $props();
</script>

<div class="flex min-h-screen bg-slate-50">
	<Sidebar />
	<main class="flex-1 overflow-auto p-6">
		{@render children()}
	</main>
</div>
