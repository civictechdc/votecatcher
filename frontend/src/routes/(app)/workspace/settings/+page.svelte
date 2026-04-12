<script lang="ts">
	import { onMount } from 'svelte';
	import { settings } from '$lib/stores/settings';
	import { Button, LoadingSpinner } from '$lib/components/ui';
	import { Key, Flag, Cpu, CheckCircle, Trash2, AlertTriangle } from 'lucide-svelte';
	import ProviderConfigCard from '$lib/components/ProviderConfigCard.svelte';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { getAppMode } from '$lib/utils/mode';

	const BASE_URL = (PUBLIC_API_URL ?? 'http://localhost:8080') + '/api';
	const showFeatureFlags = getAppMode() !== 'production';
	const showResetData = getAppMode() !== 'production';

	let resetLoading = $state(false);
	let resetError = $state<string | null>(null);
	let resetSuccess = $state(false);
	let showResetConfirm = $state(false);

	interface ProviderConfig {
		provider: string;
		model: string;
		is_configured: boolean;
		last_validated: string | null;
	}

	const PROVIDER_META: Record<string, { displayName: string; models: string[] }> = {
		openai: { displayName: 'OpenAI', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4'] },
		gemini: { displayName: 'Google Gemini', models: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
		mistral: { displayName: 'Mistral AI', models: ['mistral-large-latest', 'pixtral-12b-2409'] }
	};

	let providers = $state<ProviderConfig[]>([]);
	let providersLoading = $state(true);
	let providersError = $state<string | null>(null);

	onMount(async () => {
		settings.fetchSettings();
		await loadProviders();
	});

	async function loadProviders() {
		providersLoading = true;
		providersError = null;
		try {
			const response = await fetch(`${BASE_URL}/settings/providers`);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			providers = await response.json();
		} catch (e) {
			providersError = e instanceof Error ? e.message : 'Failed to load providers';
		} finally {
			providersLoading = false;
		}
	}

	async function saveProvider(provider: string, apiKey: string, model: string) {
		const response = await fetch(`${BASE_URL}/settings/providers/${provider}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ api_key: apiKey, model })
		});
		if (!response.ok) {
			const data = await response.json().catch(() => ({}));
			throw new Error(data.detail || `Failed to save: ${response.status}`);
		}
		await loadProviders();
	}

	async function testProvider(provider: string, apiKey: string, model: string) {
		const response = await fetch(`${BASE_URL}/settings/providers/${provider}/test`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ api_key: apiKey, model })
		});
		const data = await response.json();
		return data;
	}

	async function deleteProvider(provider: string) {
		const response = await fetch(`${BASE_URL}/settings/providers/${provider}`, {
			method: 'DELETE'
		});
		if (!response.ok) {
			throw new Error(`Failed to delete: ${response.status}`);
		}
		await loadProviders();
	}

	function getProviderConfig(providerKey: string): ProviderConfig | undefined {
		return providers.find(p => p.provider === providerKey);
	}

	async function handleResetData() {
		resetLoading = true;
		resetError = null;
		resetSuccess = false;
		try {
			const response = await fetch(`${BASE_URL}/config/reset-data`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});
			if (!response.ok) {
				const data = await response.json().catch(() => ({}));
				throw new Error(data.detail || `Failed to reset data: ${response.status}`);
			}
			resetSuccess = true;
			showResetConfirm = false;
		} catch (e) {
			resetError = e instanceof Error ? e.message : 'Failed to reset data';
		} finally {
			resetLoading = false;
		}
	}
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold text-slate-900">Settings</h1>
		<p class="mt-2 text-slate-600">Manage LLM providers and application settings</p>
	</div>

	{#if !$settings.initialized || $settings.loading || providersLoading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" />
		</div>
	{:else if $settings.error || providersError}
		<div class="rounded-lg bg-red-50 p-4">
			<div class="flex items-center justify-between">
				<p class="text-red-800">{$settings.error || providersError}</p>
				<Button variant="secondary" size="sm" onclick={() => { settings.clearError(); providersError = null; }}>
					Dismiss
				</Button>
			</div>
		</div>
	{:else if $settings.settings}
		{@const s = $settings.settings}
		<div class="space-y-6">
			<!-- LLM Provider Configuration -->
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<div class="flex items-center gap-2 mb-4">
					<Key class="h-5 w-5 text-slate-600" />
					<h2 class="text-lg font-medium text-slate-900">LLM Providers</h2>
				</div>
				<p class="text-sm text-slate-600 mb-4">
					Configure API keys for LLM providers used in OCR processing. Keys are stored locally in the database.
				</p>

				<div class="space-y-4">
					{#each Object.entries(PROVIDER_META) as [providerKey, meta]}
						{@const config = getProviderConfig(providerKey)}
						<ProviderConfigCard
							provider={providerKey}
							displayName={meta.displayName}
							models={meta.models}
							configuredModel={config?.model ?? null}
							isConfigured={config?.is_configured ?? false}
							lastValidated={config?.last_validated ?? null}
							onSave={(apiKey, model) => saveProvider(providerKey, apiKey, model)}
							onTest={(apiKey, model) => testProvider(providerKey, apiKey, model)}
							onDelete={() => deleteProvider(providerKey)}
						/>
					{/each}
				</div>
			</div>

			<!-- Feature Flags (only shown in non-production modes) -->
			{#if showFeatureFlags}
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<div class="flex items-center gap-2 mb-4">
					<Flag class="h-5 w-5 text-slate-600" />
					<h2 class="text-lg font-medium text-slate-900">Feature Flags</h2>
				</div>
				<p class="text-sm text-slate-600 mb-4">
					Feature flags are controlled via environment variables. Update your <code class="rounded bg-slate-100 px-1">.env.local</code> file to enable or disable features.
				</p>
				<div class="space-y-3">
					<div class="flex items-center justify-between py-2 border-b border-slate-100">
						<div>
							<span class="font-medium text-slate-900">Simulation Mode</span>
							<p class="text-sm text-slate-500">Enable simulated OCR processing</p>
						</div>
						{#if s.features.simulationMode}
							<span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
								<CheckCircle class="h-3 w-3" />
								Enabled
							</span>
						{:else}
							<span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
								Disabled
							</span>
						{/if}
					</div>

					<div class="flex items-center justify-between py-2 border-b border-slate-100">
						<div>
							<span class="font-medium text-slate-900">Beta Features</span>
							<p class="text-sm text-slate-500">Access experimental features</p>
						</div>
						{#if s.features.betaFeatures}
							<span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
								<CheckCircle class="h-3 w-3" />
								Enabled
							</span>
						{:else}
							<span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
								Disabled
							</span>
						{/if}
					</div>

					<div class="flex items-center justify-between py-2 border-b border-slate-100">
						<div>
							<span class="font-medium text-slate-900">Debug Mode</span>
							<p class="text-sm text-slate-500">Enable verbose logging and debug tools</p>
						</div>
						{#if s.features.debugMode}
							<span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
								<CheckCircle class="h-3 w-3" />
								Enabled
							</span>
						{:else}
							<span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
								Disabled
							</span>
						{/if}
					</div>

					<div class="flex items-center justify-between py-2 border-b border-slate-100">
						<div>
							<span class="font-medium text-slate-900">Demo Mode</span>
							<p class="text-sm text-slate-500">Enable demo features and pre-baked sessions</p>
						</div>
						{#if s.features.demoMode}
							<span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
								<CheckCircle class="h-3 w-3" />
								Enabled
							</span>
						{:else}
							<span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
								Disabled
							</span>
						{/if}
					</div>

					<div class="flex items-center justify-between py-2">
						<div>
							<span class="font-medium text-slate-900">Demo Reset</span>
							<p class="text-sm text-slate-500">Allow resetting demo data</p>
						</div>
						{#if s.features.demoReset}
							<span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
								<CheckCircle class="h-3 w-3" />
								Enabled
							</span>
						{:else}
							<span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
								Disabled
							</span>
						{/if}
					</div>
				</div>
			</div>
			{/if}

			<!-- Reset Data (only shown in non-production modes) -->
			{#if showResetData}
			<div class="rounded-lg border border-red-200 bg-white p-6">
				<div class="flex items-center gap-2 mb-4">
					<Trash2 class="h-5 w-5 text-red-600" />
					<h2 class="text-lg font-medium text-slate-900">Reset Data</h2>
				</div>
				<p class="text-sm text-slate-600 mb-4">
					Permanently delete all application data including campaigns, jobs, results, and uploads. This action cannot be undone.
				</p>

				{#if resetSuccess}
					<div class="rounded-lg bg-green-50 p-3 mb-4">
						<p class="text-sm text-green-800">All data has been reset successfully.</p>
					</div>
				{:else if resetError}
					<div class="rounded-lg bg-red-50 p-3 mb-4">
						<p class="text-sm text-red-800">{resetError}</p>
					</div>
				{/if}

				{#if showResetConfirm}
					<div class="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
						<div class="flex items-start gap-3">
							<AlertTriangle class="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
							<div class="flex-1">
								<p class="text-sm font-medium text-red-800">Are you absolutely sure?</p>
								<p class="text-sm text-red-700 mt-1">
									This will permanently delete ALL data including campaigns, jobs, results, and uploads. This action cannot be undone.
								</p>
								<div class="flex gap-2 mt-3">
									<Button
										variant="danger"
										size="sm"
										disabled={resetLoading}
										onclick={handleResetData}
									>
										{#if resetLoading}
											<LoadingSpinner size="sm" />
										{:else}
											Yes, Reset All Data
										{/if}
									</Button>
									<Button
										variant="secondary"
										size="sm"
										disabled={resetLoading}
										onclick={() => showResetConfirm = false}
									>
										Cancel
									</Button>
								</div>
							</div>
						</div>
					</div>
				{:else}
					<Button
						variant="danger"
						size="sm"
						onclick={() => { resetSuccess = false; resetError = null; showResetConfirm = true; }}
					>
						<Trash2 class="h-4 w-4 mr-1" />
						Reset All Data
					</Button>
				{/if}
			</div>
			{/if}

			<!-- Debug Info (only shown in debug mode) -->
			{#if s.features.debugMode}
				<div class="rounded-lg border border-yellow-200 bg-yellow-50 p-6">
					<div class="flex items-center gap-2 mb-4">
						<Cpu class="h-5 w-5 text-yellow-600" />
						<h2 class="text-lg font-medium text-yellow-900">Debug Information</h2>
					</div>
					<div class="rounded-lg bg-yellow-100 p-3 font-mono text-xs text-yellow-900 overflow-x-auto">
						<pre>{JSON.stringify({ settings: s, providers }, null, 2)}</pre>
					</div>
				</div>
			{/if}
		</div>
	{:else}
		<div class="rounded-lg border border-slate-200 bg-white p-6 text-center">
			<p class="text-slate-600">No settings available</p>
		</div>
	{/if}
</div>
