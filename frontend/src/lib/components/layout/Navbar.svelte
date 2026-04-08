<script lang="ts">
	import { getLogoDestination } from '$lib/utils/mode';
	export let user: { email?: string } | null = null;
</script>

<nav class="row" aria-label="Main navigation" style="justify-content:space-between">
	<div style="display:flex; gap:0.75rem; align-items:center">
		<a
			href={getLogoDestination()}
			aria-label="Votecatcher home"
			style="text-decoration:none; color:var(--vc-primary); font-weight:700">Votecatcher</a
		>
	</div>
	{#if user}
		<div class="small text-muted">
			Signed in as <span aria-label="user-email">{user.email}</span>
		</div>
	{/if}
</nav>
