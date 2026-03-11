<script lang="ts">
	import { onMount } from 'svelte';
	import { settings } from '$lib/stores/settings';
	import { Button, LoadingSpinner } from '$lib/components/ui';
	import { Key, Flag, Cpu, CheckCircle } from 'lucide-svelte';

	onMount(() => {
		settings.fetchSettings();
	});

	function handleClearError() {
		settings.clearError();
	}

	function maskApiKey(key: string | null): string {
		if (!key) return 'Not configured';
		if (key.length <= 8) return '••••••••';
		return key.substring(0, 4) + '••••••••' + key.substring(key.length - 4);
	}
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-bold text-slate-900">Settings</h1>
		<p class="mt-2 text-slate-600">Manage OCR configuration and feature flags</p>
	</div>

	{#if !$settings.initialized || $settings.loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" />
		</div>
	{:else if $settings.error}
		<div class="rounded-lg bg-red-50 p-4">
			<div class="flex items-center justify-between">
				<p class="text-red-800">{$settings.error}</p>
				<Button variant="secondary" size="sm" onclick={handleClearError}>
					Dismiss
				</Button>
			</div>
		</div>
	{:else if $settings.settings}
		{@const s = $settings.settings}
		<div class="space-y-6">
			<!-- OCR Provider Settings -->
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<div class="flex items-center gap-2 mb-4">
					<Key class="h-5 w-5 text-slate-600" />
					<h2 class="text-lg font-medium text-slate-900">OCR Provider</h2>
				</div>
				<p class="text-sm text-slate-600 mb-4">
					OCR provider configuration is managed via environment variables. Update your <code class="rounded bg-slate-100 px-1">.env.local</code> file to change these settings.
				</p>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<span class="block text-sm font-medium text-slate-700 mb-1">Provider</span>
						<div id="ocr-provider" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700">
							{s.ocr_provider ?? 'Not configured'}
						</div>
					</div>
					<div>
						<span class="block text-sm font-medium text-slate-700 mb-1">Model</span>
						<div id="ocr-model" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700">
							{s.ocr_model ?? 'Not configured'}
						</div>
					</div>
				</div>
				<div class="mt-4">
					<span class="block text-sm font-medium text-slate-700 mb-1">API Key</span>
					<div id="api-key" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-500 font-mono text-sm">
						{maskApiKey('configured')}
					</div>
					<p class="mt-1 text-xs text-slate-500">API key is hidden for security</p>
				</div>
			</div>

			<!-- Feature Flags -->
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

			<!-- Debug Info (only shown in debug mode) -->
			{#if s.features.debugMode}
				<div class="rounded-lg border border-yellow-200 bg-yellow-50 p-6">
					<div class="flex items-center gap-2 mb-4">
						<Cpu class="h-5 w-5 text-yellow-600" />
						<h2 class="text-lg font-medium text-yellow-900">Debug Information</h2>
					</div>
					<div class="rounded-lg bg-yellow-100 p-3 font-mono text-xs text-yellow-900 overflow-x-auto">
						<pre>{JSON.stringify(s, null, 2)}</pre>
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
