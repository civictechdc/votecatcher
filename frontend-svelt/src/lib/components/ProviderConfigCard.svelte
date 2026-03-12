<script lang="ts">
	import { Button, Input, Select } from '$lib/components/ui';
	import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-svelte';

	interface Props {
		provider: string;
		displayName: string;
		models: string[];
		configuredModel: string | null;
		isConfigured: boolean;
		lastValidated: string | null;
		onSave: (apiKey: string, model: string) => Promise<void>;
		onTest: (apiKey: string, model: string) => Promise<{ valid: boolean; models?: string[]; error?: string }>;
		onDelete: () => Promise<void>;
	}

	let {
		provider,
		displayName,
		models,
		configuredModel,
		isConfigured,
		lastValidated,
		onSave,
		onTest,
		onDelete
	}: Props = $props();

	let isExpanded = $state(false);
	let apiKey = $state('');
	let selectedModel = $state(configuredModel || models[0] || '');
	let isSaving = $state(false);
	let isTesting = $state(false);
	let isDeleting = $state(false);
	let testResult = $state<{ valid: boolean; models?: string[]; error?: string } | null>(null);
	let saveError = $state<string | null>(null);

	const modelOptions = $derived(models.map(m => ({ value: m, label: m })));

	async function handleSave() {
		if (!apiKey.trim()) {
			saveError = 'API key is required';
			return;
		}
		isSaving = true;
		saveError = null;
		try {
			await onSave(apiKey, selectedModel);
			apiKey = '';
			isExpanded = false;
		} catch (e) {
			saveError = e instanceof Error ? e.message : 'Failed to save';
		} finally {
			isSaving = false;
		}
	}

	async function handleTest() {
		if (!apiKey.trim()) {
			testResult = { valid: false, error: 'API key is required' };
			return;
		}
		isTesting = true;
		testResult = null;
		try {
			testResult = await onTest(apiKey, selectedModel);
		} catch (e) {
			testResult = { valid: false, error: e instanceof Error ? e.message : 'Test failed' };
		} finally {
			isTesting = false;
		}
	}

	async function handleDelete() {
		if (!confirm(`Delete ${displayName} configuration?`)) return;
		isDeleting = true;
		try {
			await onDelete();
		} finally {
			isDeleting = false;
		}
	}

	function toggleExpanded() {
		isExpanded = !isExpanded;
		if (!isExpanded) {
			apiKey = '';
			testResult = null;
			saveError = null;
		}
	}
</script>

<div class="rounded-lg border border-slate-200 bg-white overflow-hidden">
	<div class="p-4 flex items-center justify-between">
		<div class="flex items-center gap-3">
			{#if isConfigured}
				<CheckCircle class="h-5 w-5 text-green-500" />
			{:else}
				<AlertCircle class="h-5 w-5 text-slate-400" />
			{/if}
			<div>
				<h3 class="font-medium text-slate-900">{displayName}</h3>
				{#if isConfigured && configuredModel}
					<p class="text-sm text-slate-500">Model: {configuredModel}</p>
				{:else}
					<p class="text-sm text-slate-500">Not configured</p>
				{/if}
			</div>
		</div>
		<div class="flex items-center gap-2">
			{#if isConfigured}
				<Button variant="danger" size="sm" onclick={handleDelete} disabled={isDeleting}>
					{#if isDeleting}Deleting...{:else}Delete{/if}
				</Button>
			{/if}
			<Button variant="secondary" size="sm" onclick={toggleExpanded}>
				{#if isExpanded}Cancel{:else if isConfigured}Edit{:else}Configure{/if}
			</Button>
		</div>
	</div>

	{#if isExpanded}
		<div class="border-t border-slate-200 p-4 space-y-4">
			<Input
				id="{provider}-api-key"
				type="password"
				label="API Key"
				placeholder="Enter your API key"
				bind:value={apiKey}
				error={saveError !== null}
				errorMessage={saveError ?? undefined}
			/>

			<Select
				id="{provider}-model"
				label="Model"
				options={modelOptions}
				value={selectedModel}
				onValueChange={(v) => { if (v) selectedModel = v; }}
			/>

			{#if testResult}
				<div class={`flex items-center gap-2 p-3 rounded-lg ${testResult.valid ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
					{#if testResult.valid}
						<CheckCircle class="h-4 w-4" />
						<span>API key valid. Available models: {testResult.models?.join(', ')}</span>
					{:else}
						<XCircle class="h-4 w-4" />
						<span>{testResult.error || 'Validation failed'}</span>
					{/if}
				</div>
			{/if}

			<div class="flex items-center gap-2">
				<Button variant="secondary" onclick={handleTest} disabled={isTesting || !apiKey.trim()}>
					{#if isTesting}
						<Loader2 class="h-4 w-4 animate-spin mr-1" />
						Testing...
					{:else}
						Test Connection
					{/if}
				</Button>
				<Button onclick={handleSave} disabled={isSaving || !apiKey.trim()}>
					{#if isSaving}
						<Loader2 class="h-4 w-4 animate-spin mr-1" />
						Saving...
					{:else}
						Save
					{/if}
				</Button>
			</div>

			{#if lastValidated}
				<p class="text-xs text-slate-500">Last validated: {new Date(lastValidated).toLocaleString()}</p>
			{/if}
		</div>
	{/if}
</div>
