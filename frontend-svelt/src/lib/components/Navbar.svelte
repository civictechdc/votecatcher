<script lang="ts" setup>
	// Explanation: Small, focused navbar component. Accepts 'user' and 'showAuthButtons' props.
	export let user: { id?: string } | null = null;
	export let showAuthButtons: boolean = true;
</script>

<nav class="sticky top-0 z-40 w-full border-b bg-white/60 backdrop-blur">
	<div class="container mx-auto flex items-center justify-between px-4 py-3">
		<a href="/" class="text-lg font-bold text-slate-900">VoteCatcher</a>

		<div class="flex items-center gap-3">
			{#if showAuthButtons}
				{#if user}
					<a href="/workspace" class="rounded-md bg-blue-600 px-3 py-2 text-sm text-white"
						>Workspace</a
					>
				{:else}
					<a href="/auth" class="rounded-md border border-slate-200 px-3 py-2 text-sm">Sign in</a>
				{/if}
			{/if}
		</div>
	</div>
</nav>
