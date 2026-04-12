<script lang="ts">
	import { cn } from '$lib/utils/cn';
	import { Button, Input } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import type { SupabaseCredentials, ConnectionTestResult } from '$lib/api/database-types';

	interface Props {
		onBack: () => void;
		onSuccess: () => void;
	}

	let { onBack, onSuccess }: Props = $props();

	let projectUrl = $state('');
	let serviceKey = $state('');
	let dbPassword = $state('');
	let testing = $state(false);
	let provisioning = $state(false);
	let error = $state('');
	let testResult = $state<ConnectionTestResult | null>(null);

	let isValid = $derived(
		projectUrl.startsWith('https://') &&
			serviceKey.length > 50 &&
			dbPassword.length > 0,
	);

	async function handleTest() {
		testing = true;
		error = '';
		testResult = null;

		const credentials: SupabaseCredentials = {
			project_url: projectUrl,
			service_key: serviceKey,
			db_password: dbPassword,
		};

		const result = await api.database.testSupabase(credentials);
		if (result.ok) {
			testResult = result.data;
		} else {
			error = result.error;
		}
		testing = false;
	}

	async function handleConnect() {
		provisioning = true;
		error = '';

		const credentials: SupabaseCredentials = {
			project_url: projectUrl,
			service_key: serviceKey,
			db_password: dbPassword,
		};

		const result = await api.database.provisionSupabase(credentials);
		if (result.ok && result.data.success) {
			onSuccess();
		} else {
			error = result.ok ? result.data.message : result.error;
		}
		provisioning = false;
	}
</script>

<div class="mx-auto max-w-lg">
	<h2 class="mb-6 text-center text-2xl font-semibold text-slate-900">
		Connect to Supabase
	</h2>

	<div class="space-y-4">
		<Input
			id="project-url"
			type="text"
			label="Project URL"
			placeholder="https://your-project.supabase.co"
			bind:value={projectUrl}
			required
		/>
		<p class="mt-0.5 text-xs text-slate-400">
			Found in Project Settings &gt; API &mdash;
			<a href="https://supabase.com/docs/guides/api#api-url" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline hover:text-blue-800">how to find your API URL</a>
		</p>

		<div>
			<Input
				id="service-key"
				type="password"
				label="Service Role Key"
				placeholder="eyJhbGciOi..."
				bind:value={serviceKey}
				required
			/>
			<p class="mt-1 rounded bg-amber-50 p-2 text-xs text-amber-700">
				This key grants full database access. Keep it secure!
			</p>
			<p class="mt-0.5 text-xs text-slate-400">
				Found in Project Settings &gt; API &gt; Project API keys &mdash;
				<a href="https://supabase.com/docs/guides/api#api-keys" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline hover:text-blue-800">about API keys</a>
			</p>
		</div>

		<div>
			<Input
				id="db-password"
				type="password"
				label="Database Password"
				placeholder="Your database password"
				bind:value={dbPassword}
				required
			/>
			<p class="mt-0.5 text-xs text-slate-400">
				Set when you created the project &mdash;
				<a href="https://supabase.com/docs/guides/database/connecting-to-postgres#finding-your-connection-string" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline hover:text-blue-800">finding your connection details</a>
			</p>
		</div>

		{#if error}
			<div class="rounded bg-red-50 p-3 text-sm text-red-700" role="alert">
				{error}
			</div>
		{/if}

		{#if testResult}
			<div
				class={cn(
					'rounded p-3 text-sm',
					testResult.success
						? 'bg-green-50 text-green-700'
						: 'bg-gray-50 text-gray-700',
				)}
			>
				{testResult.message}
			</div>
		{/if}

		<div class="flex justify-end gap-2 pt-2">
			<Button variant="secondary" onclick={onBack} text="Back" />
			<Button
				variant="secondary"
				onclick={handleTest}
				disabled={!isValid || testing}
				loading={testing}
				text={testing ? 'Testing...' : 'Test Connection'}
			/>
			<Button
				variant="primary"
				onclick={handleConnect}
				disabled={!isValid || provisioning}
				loading={provisioning}
				text={provisioning ? 'Connecting...' : 'Connect & Provision'}
			/>
		</div>
	</div>
</div>
