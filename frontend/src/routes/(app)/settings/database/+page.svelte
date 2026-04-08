<script lang="ts">
	import { onMount } from 'svelte';
	import { cn } from '$lib/utils/cn';
	import { api } from '$lib/api/client';
	import { Button, LoadingState, ErrorDisplay } from '$lib/components/ui';
	import type { DatabaseStatus } from '$lib/api/database-types';

	let status = $state<DatabaseStatus | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let disconnecting = $state(false);

	onMount(loadStatus);

	async function loadStatus() {
		loading = true;
		error = null;
		const result = await api.database.getStatus();
		if (result.ok) {
			status = result.data;
		} else {
			error = result.error;
		}
		loading = false;
	}

	async function handleDisconnect() {
		if (!confirm('Are you sure? This will remove Supabase configuration and return to SQLite.')) {
			return;
		}

		disconnecting = true;
		const result = await api.database.disconnectSupabase();
		if (result.ok) {
			await loadStatus();
		} else {
			error = result.error;
		}
		disconnecting = false;
	}
</script>

<svelte:head>
	<title>Database Settings — Votecatcher</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-8">
	<h1 class="mb-6 text-2xl font-bold text-slate-900">Database Settings</h1>

	{#if loading}
		<LoadingState />
	{:else if error}
		<ErrorDisplay message={error} />
	{:else if status}
		<div class="rounded-lg border border-blue-200 bg-white p-6">
			<div class="mb-4 flex items-center justify-between">
				<h2 class="text-lg font-semibold text-slate-900">{status.type.toUpperCase()}</h2>
				<span
					class={cn(
						'rounded-full px-3 py-0.5 text-xs font-medium',
						status.connected
							? 'bg-green-100 text-green-700'
							: 'bg-slate-100 text-slate-600',
					)}
				>
					{status.connected ? 'Connected' : 'Disconnected'}
				</span>
			</div>

			<p class="text-sm text-slate-500">{status.message}</p>

			{#if status.type === 'supabase'}
				<div class="mt-6 border-t border-blue-200 pt-4">
					<Button
						variant="danger"
						onclick={handleDisconnect}
						disabled={disconnecting}
						loading={disconnecting}
						text={disconnecting ? 'Disconnecting...' : 'Disconnect Supabase'}
					/>
				</div>
			{/if}
		</div>
	{/if}
</div>
