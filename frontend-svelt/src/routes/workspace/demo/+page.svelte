<script lang="ts">
	import { demo, isDemoModeEnabled, type LoadedSessionInfo } from '$lib/stores/demo';
	import { Button, LoadingSpinner, Modal } from '$lib/components/ui';
	import { RefreshCw, Download, AlertTriangle, CheckCircle, Users, GitCompare } from 'lucide-svelte';

	let demoEnabled = $state(isDemoModeEnabled());

	async function handleReset() {
		await demo.resetData();
	}

	function handleCancelReset() {
		demo.cancelReset();
	}

	function showResetConfirmation() {
		demo.confirmReset();
	}

	async function handleLoadPrebaked(sessionId: string) {
		try {
			await demo.loadPrebaked(sessionId);
		} catch (e) {
			console.error('Failed to load pre-baked session:', e);
		}
	}

	function handleClearError() {
		demo.clearError();
	}
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold text-slate-900">Demo Mode</h1>
		<p class="mt-2 text-slate-600">Manage demo data and pre-baked sessions</p>
	</div>

	{#if !demoEnabled}
		<div class="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
			<div class="flex items-center gap-2">
				<AlertTriangle class="h-5 w-5 text-yellow-600" />
				<p class="text-yellow-800">
					Demo mode is not enabled. Set <code class="rounded bg-yellow-100 px-1">DEMO_MODE=true</code> in your environment.
				</p>
			</div>
		</div>
	{:else if $demo.error}
		<div class="rounded-lg bg-red-50 p-4">
			<p class="text-red-800">{$demo.error}</p>
			<Button variant="secondary" size="sm" onclick={handleClearError}>
				Dismiss
			</Button>
		</div>
	{:else}
		<div class="space-y-6">
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h2 class="text-lg font-medium text-slate-900">Reset Demo Data</h2>
				<p class="mt-2 text-sm text-slate-600">
					This will clear all demo data and reset the workspace to its initial state.
				</p>
				<div class="mt-4">
					<Button
						variant="danger"
						onclick={showResetConfirmation}
						disabled={$demo.resetting}
					>
						<RefreshCw class="mr-2 h-4 w-4" />
						Reset Demo
					</Button>
				</div>
			</div>

			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h2 class="text-lg font-medium text-slate-900">Pre-baked Demo Sessions</h2>
				<p class="mt-2 text-sm text-slate-600">
					Load a pre-configured demo session with sample data.
				</p>

				{#if $demo.loading}
					<div class="mt-4 flex items-center gap-2">
						<LoadingSpinner size="sm" />
						<span class="text-slate-600">Loading...</span>
					</div>
				{:else if $demo.loadedSession}
					<div class="mt-4 rounded-lg border border-green-200 bg-green-50 p-4">
						<div class="flex items-center gap-2">
							<CheckCircle class="h-5 w-5 text-green-600" />
							<p class="font-medium text-green-800">{$demo.loadedSession.message}</p>
						</div>
						<div class="mt-3 grid grid-cols-2 gap-4 text-sm">
							<div class="flex items-center gap-2">
								<Users class="h-4 w-4 text-green-600" />
								<span class="text-green-700"><strong>{$demo.loadedSession.voters_count}</strong> voters loaded</span>
							</div>
							<div class="flex items-center gap-2">
								<GitCompare class="h-4 w-4 text-green-600" />
								<span class="text-green-700"><strong>{$demo.loadedSession.match_results_count}</strong> match results</span>
							</div>
						</div>
						<p class="mt-2 text-xs text-green-600">Session ID: {$demo.loadedSession.session_id}</p>
					</div>
				{:else if $demo.prebakedSessions.length === 0}
					<p class="mt-4 text-slate-500">No pre-baked sessions available.</p>
				{:else}
					<div class="mt-4 space-y-2">
						{#each $demo.prebakedSessions as session}
							<div class="flex items-center justify-between rounded-lg border border-slate-200 p-3">
								<div>
									<p class="font-medium text-slate-900">{session.name}</p>
									<p class="text-sm text-slate-600">{session.description}</p>
								</div>
								<Button
									variant="secondary"
									size="sm"
									onclick={() => handleLoadPrebaked(session.id)}
									disabled={$demo.loading}
								>
									<Download class="mr-1 h-4 w-4" />
									Load
								</Button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<Modal
	open={$demo.showResetConfirmation}
	title="Confirm Reset"
	onClose={handleCancelReset}
>
	<div class="space-y-4">
		<p class="text-slate-600">
			Are you sure you want to reset all demo data? This action cannot be undone.
		</p>
		<div class="flex justify-end gap-2">
			<Button variant="secondary" onclick={handleCancelReset}>
				Cancel
			</Button>
			<Button
				variant="danger"
				onclick={handleReset}
				loading={$demo.resetting}
			>
				Confirm Reset
			</Button>
		</div>
	</div>
</Modal>
