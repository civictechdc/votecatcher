<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { campaigns } from '$lib/stores/campaigns';
	import { getLogoDestination } from '$lib/utils/mode';
	import SidebarNavItem from './SidebarNavItem.svelte';
	import Menu from 'lucide-svelte/icons/menu';
	import X from 'lucide-svelte/icons/x';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';

	let isOpen = $state(false);
	let showCampaignSwitcher = $state(false);

	const navItems = [
		{ href: '/workspace/campaigns', label: 'Campaigns', icon: 'folder' as const },
		{ href: '/workspace/settings', label: 'Settings', icon: 'settings' as const }
	];

	function toggleMenu() {
		isOpen = !isOpen;
	}

	function closeMenu() {
		isOpen = false;
	}

	function toggleCampaignSwitcher() {
		showCampaignSwitcher = !showCampaignSwitcher;
	}

	function navigateToCampaign(campaignId: string) {
		goto(`/workspace/${campaignId}`);
		showCampaignSwitcher = false;
	}

	onMount(() => {
		if (!$campaigns.loaded && !$campaigns.loading) {
			campaigns.fetchAll();
		}
	});
</script>

<button
	onclick={toggleMenu}
	aria-label="Toggle menu"
	class="fixed right-4 top-4 z-50 rounded-md bg-white p-2 shadow-md md:hidden"
>
	{#if isOpen}
		<X class="h-6 w-6" />
	{:else}
		<Menu class="h-6 w-6" />
	{/if}
</button>

<aside
	class={`
		fixed left-0 top-0 z-40 h-full w-64 transform bg-white border-r border-slate-200
		transition-transform duration-200 ease-in-out
		${isOpen ? 'translate-x-0' : '-translate-x-full'}
		md:translate-x-0 md:static md:z-0
	`}
>
	<nav aria-label="Workspace navigation" class="flex h-full flex-col">
		<div class="flex h-16 items-center border-b border-slate-200 px-6">
			<a href={getLogoDestination()} class="text-xl font-bold text-blue-600">Votecatcher</a>
		</div>

		<div class="flex-1 overflow-y-auto p-4">
			{#if $campaigns.campaigns.length > 0}
				<div class="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
					<button
						onclick={toggleCampaignSwitcher}
						class="flex w-full items-center justify-between text-sm font-medium text-slate-700"
						aria-expanded={showCampaignSwitcher}
					>
						<span class="truncate">Jump to Campaign</span>
						<ChevronDown class="h-4 w-4" />
					</button>

					{#if showCampaignSwitcher}
						<ul class="mt-2 max-h-48 overflow-y-auto rounded border border-slate-200 bg-white">
							{#each $campaigns.campaigns as campaign}
								<li>
									<button
										onclick={() => campaign.id && navigateToCampaign(campaign.id)}
										class="w-full px-3 py-2 text-left text-sm hover:bg-slate-100"
									>
										{campaign.unique_name || campaign.title || 'Untitled'}
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			{/if}

			<ul class="space-y-1">
				{#each navItems as item}
					<li>
						<SidebarNavItem
							href={item.href}
							label={item.label}
							icon={item.icon}
							isActive={$page.url.pathname === item.href}
						/>
					</li>
				{/each}
			</ul>
		</div>
	</nav>
</aside>

{#if isOpen}
	<div
		class="fixed inset-0 z-30 bg-black/50 md:hidden"
		onclick={closeMenu}
		aria-hidden="true"
	></div>
{/if}
