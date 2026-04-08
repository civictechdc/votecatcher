<script lang="ts">
	let { children } = $props();
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-slate-50">
	<div class="flex items-center justify-center p-8">
		<h1 class="text-2xl font-bold text-slate-900">VoteCatcher</h1>
	</div>
	{@render children()}
</div>
