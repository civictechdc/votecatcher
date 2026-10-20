<script lang="ts">
	import { featureFlags } from '$lib/config/featureFlags';
	import { IS_DEV } from '$lib/utils/mode';

	// Self-gates: renders nothing outside developer mode, even if a page
	// mounts this component without its own gate (defense in depth).

	let open = $state(false);
	let newFlag = $state('');
	let flags = $state(featureFlags.list());

	function toggle(f: string) {
		featureFlags.toggleLocal(f);
		flags = featureFlags.list();
	}

	function addFlag() {
		const key = newFlag.trim();
		if (!key) return;
		featureFlags.toggleLocal(key);
		newFlag = '';
		flags = featureFlags.list();
	}
</script>

{#if IS_DEV}
	{#if !open}
		<button
			type="button"
			class="fixed right-4 bottom-4 z-50 rounded-full border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-md hover:bg-gray-50"
			aria-expanded={open}
			onclick={() => (open = true)}
		>
			Flags
		</button>
	{:else}
		<div class="fixed right-4 bottom-4 z-50">
			<div class="w-72 rounded-lg border bg-white p-3 text-sm shadow-lg">
				<div class="mb-2 flex items-center justify-between">
					<div class="font-medium">Dev Flags</div>
					<button
						type="button"
						class="text-xs text-gray-500 hover:text-gray-700"
						aria-label="Close dev flags"
						onclick={() => (open = false)}
					>
						Close
					</button>
				</div>

				{#each flags as f (f)}
					<div class="mb-1 flex items-center gap-2">
						<label class="inline-flex w-full cursor-pointer items-center gap-2 p-1 -m-1">
							<input
								type="checkbox"
								checked={featureFlags.isEnabled(f)}
								onchange={() => {
									toggle(f);
								}}
								class="h-6 w-6 rounded border-gray-300"
							/>
							<span class="truncate text-xs">{f}</span>
						</label>
					</div>
				{/each}

				<div class="mt-2 flex items-center gap-1">
					<input
						class="w-full rounded border border-gray-300 px-2 py-1 text-xs"
						placeholder="Add flag (e.g. mockApi)"
						aria-label="New flag name"
						bind:value={newFlag}
						onkeydown={(e) => {
							if (e.key === 'Enter') addFlag();
						}}
					/>
					<button
						type="button"
						class="rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50"
						onclick={addFlag}
					>
						Add
					</button>
				</div>

				<div class="mt-2 text-xs text-gray-600">
					Flags persist to localStorage under <code>vc:flags</code>. Toggle <b>mockApi</b> to
					enable MSW.
				</div>
			</div>
		</div>
	{/if}
{/if}
