<script lang="ts">
	export let user: { email?: string } | null = null;
</script>

<nav class="row" aria-label="Main navigation" style="justify-content:space-between">
	<div style="display:flex; gap:0.75rem; align-items:center">
		<a
			href="/"
			aria-label="Votecatcher home"
			style="text-decoration:none; color:var(--vc-primary); font-weight:700">Votecatcher</a
		>
		<span class="text-muted small">Onboarding</span>
	</div>
	<div class="small text-muted">
		{#if user}
			Signed in as <span aria-label="user-email">{user.email}</span>
		{:else}
			<a href="/login" class="small">Sign in</a>
		{/if}
	</div>
</nav>
