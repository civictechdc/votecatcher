<script lang="ts">
	import { cn } from '$lib/utils/cn';
	import { featureFlags, hasOverrides } from '$lib/stores/featureFlags';

	interface Props {
		class?: string;
	}

	let { class: className }: Props = $props();

	const flagDescriptions: Record<string, string> = {
		simulationMode: 'Use mock data instead of real OCR/matching',
		betaFeatures: 'Enable experimental features',
		debugMode: 'Show additional debug information',
	};
</script>

<div class={cn('rounded-lg border bg-card p-4', className)}>
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-lg font-semibold">Feature Flags</h3>
		{#if $hasOverrides}
			<button
				type="button"
				onclick={() => featureFlags.resetAll()}
				class="text-sm text-muted-foreground hover:text-foreground underline"
			>
				Reset All
			</button>
		{/if}
	</div>

	<div class="space-y-3">
		{#each Object.entries($featureFlags) as [flag, value]}
			<div class="flex items-start justify-between gap-4">
				<div class="flex-1">
					<label class="flex items-center gap-2 cursor-pointer">
						<input
							type="checkbox"
							checked={value}
							onchange={() => featureFlags.toggle(flag as keyof typeof $featureFlags)}
							class="h-4 w-4 rounded border-input"
						/>
						<span class="font-medium">{flag}</span>
					</label>
					<p class="text-sm text-muted-foreground ml-6">
						{flagDescriptions[flag] || 'No description available'}
					</p>
				</div>

				<button
					type="button"
					onclick={() => featureFlags.reset(flag as keyof typeof $featureFlags)}
					class="text-xs text-muted-foreground hover:text-foreground"
					title="Reset to server default"
				>
					reset
				</button>
			</div>
		{/each}
	</div>

	{#if $hasOverrides}
		<div class="mt-4 pt-4 border-t">
			<p class="text-xs text-muted-foreground">
				⚠️ Some flags are overridden. Changes are persisted in localStorage.
			</p>
		</div>
	{/if}
</div>
