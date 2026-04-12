<script lang="ts">
	import { cn } from '$lib/utils/cn';
	import type { DatabaseType } from '$lib/api/database-types';

	interface Props {
		onSelect: (type: DatabaseType) => void;
	}

	let { onSelect }: Props = $props();

	interface DatabaseOption {
		type: DatabaseType;
		label: string;
		description: string;
		icon: string;
		note?: string;
	}

	const options: DatabaseOption[] = [
		{
			type: 'sqlite',
			label: 'Local',
			description: 'Data stored on this device using SQLite — no setup needed',
			icon: 'local',
		},
		{
			type: 'supabase',
			label: 'Cloud',
			description: 'Managed hosting via Supabase — sync across devices',
			icon: 'cloud',
			note: 'Supabase account required',
		},
		{
			type: 'postgres',
			label: 'Custom',
			description: 'Connect your own PostgreSQL database',
			icon: 'custom',
		},
	];

	let hovered = $state<DatabaseType | null>(null);
</script>

{#snippet icon(name: string)}
	{#if name === 'local'}
		<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400" aria-hidden="true">
			<rect x="2" y="3" width="20" height="14" rx="2" />
			<line x1="8" y1="21" x2="16" y2="21" />
			<line x1="12" y1="17" x2="12" y2="21" />
		</svg>
	{:else if name === 'cloud'}
		<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400" aria-hidden="true">
			<path d="M4 14.5C2.5 13 2.5 10 5 9c0-4 5-5 7-2 2-1 6 0 6 3.5 2 .5 2.5 3.5 1 5" />
			<path d="M12 12v6" />
			<path d="m9 15 3-3 3 3" />
		</svg>
	{:else}
		<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400" aria-hidden="true">
			<circle cx="12" cy="12" r="3" />
			<path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
		</svg>
	{/if}
{/snippet}

<div class="mx-auto max-w-lg">
	<h2 class="mb-1 text-center text-2xl font-semibold text-slate-900">
		Choose Your Database
	</h2>
	<p class="mb-8 text-center text-sm text-slate-500">
		Select how you want to store your data
	</p>

	<div class="flex flex-col gap-3">
		{#each options as option (option.type)}
			<button
				type="button"
				class={cn(
					'block w-full rounded-lg border-2 border-blue-200 bg-white p-4 text-left transition-all',
					'hover:border-blue-600 hover:shadow-md',
					'focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:ring-offset-0',
					hovered === option.type && 'border-blue-600 shadow-md',
				)}
				onmouseenter={() => (hovered = option.type)}
				onmouseleave={() => (hovered = null)}
				onclick={() => onSelect(option.type)}
			>
				<div class="flex items-center gap-3">
					{@render icon(option.icon)}
					<div>
						<h3 class="text-base font-semibold text-slate-900">{option.label}</h3>
						<p class="text-sm text-slate-500">{option.description}</p>
						{#if option.note}
							<p class="mt-0.5 text-xs text-slate-400">{option.note}</p>
						{/if}
					</div>
				</div>
			</button>
		{/each}
	</div>
</div>
