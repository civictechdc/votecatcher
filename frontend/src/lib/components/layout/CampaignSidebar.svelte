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

	interface Props {
		campaignId: string;
		campaignName?: string;
	}

	let { campaignId, campaignName = 'Campaign' }: Props = $props();

	let isOpen = $state(false);
	let showCampaignSwitcher = $state(false);

	const navItems = $derived([
		{ href: `/workspace/${campaignId}`, label: 'Dashboard', icon: 'home' as const },
		{ href: `/workspace/${campaignId}/upload`, label: 'Upload', icon: 'upload' as const },
		{ href: `/workspace/${campaignId}/jobs`, label: 'Jobs', icon: 'activity' as const },
		{ href: `/workspace/${campaignId}/results`, label: 'Results', icon: 'check-circle' as const }
	]);

	const globalNavItems = [
		{ href: '/workspace/campaigns', label: 'All Campaigns', icon: 'folder' as const },
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

	function switchCampaign(newId: string) {
		const currentPath = $page.url.pathname;
		const currentSegment = currentPath.replace(/^\/workspace\/[^/]+/, '');
		goto(`/workspace/${newId}${currentSegment}`);
		showCampaignSwitcher = false;
	}

	onMount(() => {
		campaigns.fetchAll();
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
	<nav aria-label="Campaign navigation" class="flex h-full flex-col">
		<div class="flex h-16 items-center border-b border-slate-200 px-6">
			<a href={getLogoDestination()} class="text-xl font-bold text-blue-600">Votecatcher</a>
		</div>

		<div class="flex-1 overflow-y-auto p-4">
			<div class="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
                <button
                    onclick={toggleCampaignSwitcher}
                    class="flex w-full items-center justify-between text-sm font-medium text-slate-700"
                    aria-expanded={showCampaignSwitcher}
                >
                    {#if $campaigns.loading}
                        <span class="animate-pulse bg-slate-200 rounded h-4 w-24 inline-block"></span>
                    {:else}
                        <span class="truncate">{campaignName}</span>
                    {/if}
                    <ChevronDown class="h-4 w-4" />
                </button>

				{#if showCampaignSwitcher}
					<ul class="mt-2 max-h-48 overflow-y-auto rounded border border-slate-200 bg-white">
						{#each $campaigns.campaigns as campaign}
							{#if campaign.id !== String(campaignId)}
								<li>
									<button
										onclick={() => campaign.id && switchCampaign(campaign.id)}
										class="w-full px-3 py-2 text-left text-sm hover:bg-slate-100"
									>
										{campaign.unique_name || campaign.title || 'Untitled'}
									</button>
								</li>
							{/if}
						{/each}
						<li class="border-t border-slate-200">
							<a
								href="/workspace/campaigns"
								class="block px-3 py-2 text-sm text-blue-600 hover:bg-slate-100"
							>
								Manage Campaigns...
							</a>
						</li>
					</ul>
				{/if}
			</div>

			<div class="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
				Campaign
			</div>
			<ul class="mb-4 space-y-1">
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

			<div class="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
				Global
			</div>
			<ul class="space-y-1">
				{#each globalNavItems as item}
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
