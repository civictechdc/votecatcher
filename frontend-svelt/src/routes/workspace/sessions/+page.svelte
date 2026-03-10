<script lang="ts">
	import { sessions } from '$lib/stores/sessions';
	import { Button, LoadingSpinner, Modal } from '$lib/components/ui';
	import { Save, Download, Upload, Trash2, FileDown } from 'lucide-svelte';

	let showModal = $state(false);
	let sessionName = $state('');
	let isLoading = $state(false);

	async function handleSave() {
		if (!sessionName.trim()) return;

		isLoading = true;
		try {
			await sessions.save(sessionName, {});
			showModal = false;
			sessionName = '';
		} catch (e) {
			console.error('Failed to save session:', e);
		} finally {
			isLoading = false;
		}
	}

	async function handleLoad(id: number) {
		isLoading = true;
		try {
			await sessions.load(id);
		} catch (e) {
			console.error('Failed to load session:', e);
		} finally {
			isLoading = false;
		}
	}

	async function handleExport(id: number) {
		try {
			await sessions.export(id);
		} catch (e) {
			console.error('Failed to export session:', e);
		}
	}

	async function handleDelete(id: number) {
		if (!confirm('Are you sure you want to delete this session?')) return;

		try {
			await sessions.delete(id);
		} catch (e) {
			console.error('Failed to delete session:', e);
		}
	}
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold text-slate-900">Sessions</h1>
			<p class="mt-2 text-slate-600">Save, load, and export your workspace state</p>
		</div>
		<Button onclick={() => (showModal = true)}>
			<Save class="mr-2 h-4 w-4" />
			Save Session
		</Button>
	</div>

	{#if $sessions.loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" />
		</div>
	{:else if $sessions.error}
		<div class="rounded-lg bg-red-50 p-4">
			<p class="text-red-800">{$sessions.error}</p>
		</div>
	{:else if $sessions.sessions.length === 0}
		<div class="rounded-lg border border-slate-200 bg-white p-12 text-center">
			<FileDown class="mx-auto h-12 w-12 text-slate-400" />
			<p class="mt-4 text-lg font-medium text-slate-900">No saved sessions</p>
			<p class="mt-2 text-slate-600">Save your current workspace state to access it later</p>
		</div>
	{:else}
		<div class="space-y-4">
			{#each $sessions.sessions as session}
				<div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<div class="flex items-center gap-2">
								<h3 class="text-lg font-medium text-slate-900">{session.name}</h3>
								<span
									class="rounded-full px-2 py-0.5 text-xs font-medium {session.session_type === 'DEMO'
										? 'bg-purple-100 text-purple-800'
										: 'bg-blue-100 text-blue-800'}"
								>
									{session.session_type}
								</span>
							</div>
							<p class="mt-1 text-sm text-slate-600">
								{new Date(session.updated_at).toLocaleDateString('en-US', {
									year: 'numeric',
									month: 'short',
									day: 'numeric',
									hour: '2-digit',
									minute: '2-digit'
								})}
							</p>
							{#if session.campaign_id}
								<p class="mt-1 text-sm text-slate-500">Campaign: {session.campaign_id}</p>
							{/if}
						</div>
						<div class="flex gap-2">
							<Button variant="secondary" size="sm" onclick={() => handleLoad(session.id)}>
								<Upload class="mr-1 h-4 w-4" />
								Load
							</Button>
							<Button variant="secondary" size="sm" onclick={() => handleExport(session.id)}>
								<Download class="mr-1 h-4 w-4" />
								Export
							</Button>
							<Button variant="danger" size="sm" onclick={() => handleDelete(session.id)}>
								<Trash2 class="h-4 w-4" />
							</Button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<Modal bind:open={showModal} title="Save Session">
	<div class="space-y-4">
		<div>
			<label for="session-name" class="block text-sm font-medium text-slate-700">
				Session Name
			</label>
			<input
				id="session-name"
				type="text"
				bind:value={sessionName}
				class="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
				placeholder="Enter session name"
			/>
		</div>
		<div class="flex justify-end gap-2">
			<Button variant="secondary" onclick={() => (showModal = false)}>Cancel</Button>
			<Button onclick={handleSave} loading={isLoading} disabled={!sessionName.trim()}>
				Save
			</Button>
		</div>
	</div>
</Modal>
