<script lang="ts">
	import { goto } from '$app/navigation';
	import { OnboardingWizard } from '#lib/components/onboarding/index.ts';

	function handleComplete() {
		goto('/');
	}
</script>

<svelte:head>
	<title>Database Setup — Votecatcher</title>
</svelte:head>

<OnboardingWizard onComplete={handleComplete} />
