<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { Progress } from '$lib/components/ui';
	import { Navbar } from '$lib/components/layout';
	import { onboard } from '$lib/stores/onboarding';
	import { api } from '$lib/api/client';
	import { initMocks } from '$lib/mocks/init';
	import { OCR_PROVIDER_SELECTION } from '$lib/constants/ocr';

	// Data injected by the server-side load (+page.server.ts)
	let { data } = $props<{
		data: {
			user: { id?: string; email?: string } | null;
			steps: { id: string; title: string; description: string }[];
			years: string[];
		};
	}>();

	// Local reactive copies for template use
	let state = get(onboard);
	const unsubscribe = onboard.subscribe((s) => (state = s));

	const steps = data.steps;
	const years = data.years;
	let user = data.user;
	let errorMsg = '';
	let selectedProvider = '';
	let onboardingProgress = $derived(Math.round(state.currentStep + 1 / steps.length) * 100);

	// Start client mocks early so api.* calls on user interaction can be intercepted.
	onMount(async () => {
		await initMocks();
	});

	// Helpers used by the UI
	const canProceed = () => {
		const stepId = steps[state.currentStep].id;
		if (stepId === 'provider') {
			return !!state.answers.selectedOcrProvider && !!state.answers.ocrProviderApiKey;
		} else if (stepId === 'campaign') {
			return (
				!!state.answers.campaign_name &&
				!!state.answers.campaign_year &&
				state.answers.campaign_name.length >= 3
			);
		} else {
			return !!state.uploadedFile;
		}
	};

	const onOcrProviderSelected = (e: Event) => {
		const element = e.target as HTMLSelectElement;
		const value = element.value;
		if (value === '') {
			onboard.setAnswer('selectedOcrProvider', null);
		} else {
			onboard.setAnswer(
				'selectedOcrProvider',
				OCR_PROVIDER_SELECTION[(e.target as HTMLSelectElement).selectedIndex - 1]
			);
		}
		//Clear the api key field on each change
		onboard.setAnswer('ocrProviderApiKey', '');
	};

	const next = async () => {
		errorMsg = '';
		const stepId = steps[state.currentStep].id;

		if (stepId === 'provider') {
			const ocrProvider = state.answers.selectedOcrProvider;
			const ocrProviderApiKey = state.answers.ocrProviderApiKey;
			if (ocrProvider && ocrProviderApiKey) {
				onboard.setLoading(true);
				const res = await api.storeApiKey(ocrProvider.apiKeyId, ocrProviderApiKey);
				onboard.setLoading(false);
				if (!res.ok) {
					errorMsg = res.error;
					return;
				}
			}
		}

		if (stepId === 'campaign') {
			if (state.answers.campaign_name && state.answers.campaign_year) {
				onboard.setLoading(true);
				const payload = {
					name: state.answers.campaign_name,
					year: parseInt(state.answers.campaign_year),
					description: state.answers.campaign_description || undefined
				};
				const res = await api.createCampaign(payload);
				onboard.setLoading(false);
				if (!res.ok) {
					errorMsg = res.error;
					return;
				}
				// store id from response (mock returns { id })
				onboard.setCampaignId((res.data as { id: string }).id);
			} else {
				errorMsg = 'Please provide campaign name and year.';
				return;
			}
		}

		if (state.currentStep < steps.length - 1) {
			onboard.next();
			const el = document.getElementById('step-title');
			el?.focus();
		} else {
			await complete();
		}
	};

	const back = () => onboard.back();

	const complete = async () => {
		if (!user) return;
		onboard.setLoading(true);
		if (state.uploadedFile) {
			const meta = {
				fileName: state.uploadedFile.name,
				size: state.uploadedFile.size,
				campaignId: state.answers.campaign_id || null
			};
			const uploadRes = await api.uploadFileMeta(meta);
			if (!uploadRes.ok) {
				errorMsg = uploadRes.error;
				onboard.setLoading(false);
				return;
			}
			const proc = await api.triggerProcessFile({
				filePath: `${user?.id ?? 'unknown'}/${state.answers.campaign_id || 'no-campaign'}/${state.uploadedFile?.name ?? 'unknown'}`,
				campaignId: state.answers.campaign_id ?? ''
			});
			onboard.setLoading(false);
			if (!proc.ok) {
				errorMsg = proc.error;
				return;
			}
			// Redirect to workspace on success
			location.href = '/workspace';
		} else {
			onboard.setLoading(false);
			errorMsg = 'No file to process.';
		}
	};

	// File handlers
	const onFileChange = (e: Event) => {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0] ?? null;
		if (!file) return;
		const allowed = ['.csv', '.xlsx', '.xls', '.json'];
		const ext = '.' + (file.name.split('.').pop() || '').toLowerCase();
		if (!allowed.includes(ext)) {
			errorMsg = 'Unsupported file type. Use CSV/Excel/JSON.';
			return;
		}
		onboard.setUploadedFile(file);
		onboard.setAnswer('registration_data', file.name);
	};

	onDestroy(() => unsubscribe());
</script>

<svelte:head>
	<title>Getting started — Votecatcher</title>
</svelte:head>

<div class="container" role="main">
	<Navbar {user} />
	<div class="card" style="margin-top:1rem;">
		<div class="space-y-4">
			<div aria-live="polite" class="sr-only">Step {state.currentStep + 1} of {steps.length}</div>
			<Progress value={onboardingProgress} />
			<h2 id="step-title" tabindex="-1">{steps[state.currentStep].title}</h2>
			<p class="text-muted">{steps[state.currentStep].description}</p>

			{#if steps[state.currentStep].id === 'provider'}
				<div class="space-y-4">
					<label class="label" for="provider">AI Provider</label>
					<select
						id="provider"
						class="select"
						bind:value={selectedProvider}
						on:change={onOcrProviderSelected}
					>
						<option value="" selected>Select OCR provider...</option>
						{#each OCR_PROVIDER_SELECTION as provider}
							<option value={provider.apiKeyId}>{provider.name}</option>
						{/each}
					</select>

					{#if state.answers.selectedOcrProvider}
						<label class="label" for="api-key">API Key</label>
						<p class="text-muted">
							To obtain an API key, visit <a
								class="text-muted provider-api-key-guide-link"
								href={state.answers.selectedOcrProvider.apiKeyDocs}
								target="_blank"
								title={state.answers.selectedOcrProvider.apiKeyDocs}
								>{state.answers.selectedOcrProvider.name}'s page</a
							> for more information.
						</p>
						<input
							id="api-key"
							class="input"
							type="password"
							placeholder="sk-..."
							bind:value={state.answers.ocrProviderApiKey}
							on:input={(e) =>
								onboard.setAnswer('ocrProviderApiKey', (e.target as HTMLInputElement).value)}
							aria-describedby="api-hint"
						/>
						<div id="api-hint" class="text-muted small">
							We store API keys securely via backend. Keys are not shown again.
						</div>
					{/if}
				</div>
			{/if}

			{#if steps[state.currentStep].id === 'campaign'}
				<div class="space-y-4">
					<label class="label" for="campaign-name">Campaign Name</label>
					<input
						id="campaign-name"
						class="input"
						placeholder="e.g., Smith for Mayor"
						bind:value={state.answers.campaign_name}
						on:input={(e) =>
							onboard.setAnswer('campaign_name', (e.target as HTMLInputElement).value)}
					/>
					<div class="small text-muted">Name must be at least 3 characters.</div>

					<label class="label" for="campaign-year">Election Year</label>
					<select
						id="campaign-year"
						class="select"
						bind:value={state.answers.campaign_year}
						on:change={(e) =>
							onboard.setAnswer('campaign_year', (e.target as HTMLSelectElement).value)}
					>
						<option value="">Select year</option>
						{#each years as year}
							<option value={year}>{year}</option>
						{/each}
					</select>

					<label class="label" for="campaign-desc">Description (optional)</label>
					<textarea
						id="campaign-desc"
						class="textarea"
						rows="3"
						placeholder="Describe your campaign"
						bind:value={state.answers.campaign_description}
						on:input={(e) =>
							onboard.setAnswer('campaign_description', (e.target as HTMLTextAreaElement).value)}
					></textarea>
				</div>
			{/if}

			{#if steps[state.currentStep].id === 'upload'}
				<div class="space-y-4">
					<label class="label" for="file-input">Registration file</label>
					<input
						id="file-input"
						class="sr-only"
						type="file"
						accept=".csv,.xlsx,.xls,.json"
						on:change={onFileChange}
					/>
					<div class="row">
						<button
							class="button"
							on:click={() => document.getElementById('file-input')?.click()}
							disabled={state.loading}>Choose file</button
						>
						{#if state.uploadedFile}
							<div class="small text-muted">
								{state.uploadedFile.name} — {state.uploadedFile.size} bytes
							</div>
						{/if}
					</div>
					<div class="text-muted small">Accepted: CSV, Excel, JSON</div>
				</div>
			{/if}

			{#if errorMsg}
				<div role="alert" style="color:var(--vc-danger)" class="small">{errorMsg}</div>
			{/if}

			<div class="row" style="justify-content:space-between;">
				{#if state.currentStep !== 0}
					<button class="button-outline" on:click={back} disabled={state.currentStep === 0}
						>Back</button
					>
				{/if}
				<div style="display:flex; gap:0.5rem;">
					<button
						class="button-outline"
						on:click={() => {
							onboard.reset();
							location.href = '/';
						}}>Cancel</button
					>
					<button class="button" on:click={next} disabled={!canProceed() || state.loading}>
						{state.currentStep === steps.length - 1
							? state.loading
								? 'Processing...'
								: 'Complete'
							: 'Next'}
					</button>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	@import '$lib/styles/theme.css';
	h2 {
		margin: 0;
	}

	.provider-api-key-guide-link {
		text-decoration: underline;
	}
</style>
