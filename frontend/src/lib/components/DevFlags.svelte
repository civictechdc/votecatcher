<script lang="ts">
    import { featureFlags } from '$lib/config/featureFlags';
    import { onMount } from 'svelte';

    let flags: string[] = [];
    // canonical list of dev flags available (add more as you add mocks)
    const allFlags = [
        'mockApi',
        'mock:createCampaign:missingFields',
        'mock:createCampaign:success',
        'mock:createCampaign:delay',
        'mock:session:loggedIn',
        'mock:session:loggedOut'
    ];

    function refresh() {
        flags = featureFlags.list();
    }

    function toggle(f: string) {
        featureFlags.toggleLocal(f);
        refresh();
        // reload is intentionally avoided; MSW/handlers react to featureFlags at runtime.
    }

    onMount(() => refresh());
</script>

<div class="fixed right-4 bottom-4 z-50">
    <div class="w-72 rounded-lg border bg-white p-3 text-sm shadow-lg">
        <div class="mb-2 flex items-center justify-between">
            <div class="font-medium">Dev Flags</div>
            <button class="text-xs text-gray-500" on:click={refresh}>Refresh</button>
        </div>

        {#each allFlags as f}
            <div class="mb-1 flex items-center gap-2">
                <label class="inline-flex w-full cursor-pointer items-center gap-2 p-1 -m-1">
                    <input
                        type="checkbox"
                        checked={featureFlags.isEnabled(f)}
                        on:change={() => toggle(f)}
                        class="h-6 w-6 rounded border-gray-300"
                    />
                    <span class="truncate text-xs">{f}</span>
                </label>
            </div>
        {/each}

        <div class="mt-2 text-xs text-gray-600">
            Flags persist to localStorage under <code>vc:flags</code>. Toggle <b>mockApi</b> to enable MSW.
        </div>
    </div>
</div>
