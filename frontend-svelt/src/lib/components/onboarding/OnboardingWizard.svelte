<script lang="ts">
	import type { DatabaseType } from '$lib/api/database-types';
	import DatabaseSelector from './DatabaseSelector.svelte';
	import SupabaseConnectForm from './SupabaseConnectForm.svelte';
	import { Button } from '$lib/components/ui';

	interface Props {
		onComplete: () => void;
	}

	let { onComplete }: Props = $props();

	type Step = 'select' | 'supabase' | 'postgres' | 'complete';
	let step = $state<Step>('select');

	function handleSelect(type: DatabaseType) {
		if (type === 'supabase') {
			step = 'supabase';
		} else if (type === 'postgres') {
			step = 'postgres';
		} else {
			step = 'complete';
			onComplete();
		}
	}

	function handleBack() {
		step = 'select';
	}
</script>

<div class="flex min-h-screen items-center justify-center p-6">
	{#if step === 'select'}
		<DatabaseSelector onSelect={handleSelect} />
	{:else if step === 'supabase'}
		<SupabaseConnectForm onBack={handleBack} onSuccess={onComplete} />
	{:else if step === 'postgres'}
		<div class="mx-auto max-w-sm text-center">
			<h2 class="mb-2 text-xl font-semibold text-slate-900">Custom Database Setup</h2>
			<p class="mb-6 text-sm text-slate-500">Connect your own PostgreSQL database — coming soon.</p>
			<Button variant="secondary" onclick={handleBack} text="Back" />
		</div>
	{/if}
</div>
