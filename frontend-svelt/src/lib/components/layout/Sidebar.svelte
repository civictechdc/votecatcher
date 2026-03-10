<script lang="ts">
	import { page } from '$app/stores';
	import SidebarNavItem from './SidebarNavItem.svelte';
	import Menu from 'lucide-svelte/icons/menu';
	import X from 'lucide-svelte/icons/x';

	let isOpen = $state(false);

	const navItems = [
		{ href: '/workspace', label: 'Dashboard', icon: 'home' as const },
	 { href: '/workspace/campaigns', label: 'Campaigns', icon: 'folder' as const },
    { href: '/workspace/jobs', label: 'Jobs', icon: 'activity' as const },
    { href: '/workspace/results', label: 'Results', icon: 'check-circle' as const },
    { href: '/workspace/sessions', label: 'Sessions', icon: 'save' as const },
    { href: '/workspace/settings', label: 'Settings', icon: 'settings' as const }
];

	function toggleMenu() {
		isOpen = !isOpen;
	}

	function closeMenu() {
		isOpen = false;
	}
</script>

<!-- Mobile menu button -->
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

<!-- Sidebar -->
<aside
	class={`
		fixed left-0 top-0 z-40 h-full w-64 transform bg-white border-r border-slate-200
		transition-transform duration-200 ease-in-out
		${isOpen ? 'translate-x-0' : '-translate-x-full'}
		md:translate-x-0 md:static md:z-0
	`}
>
	<nav aria-label="Workspace navigation" class="flex h-full flex-col">
		<!-- Logo -->
		<div class="flex h-16 items-center border-b border-slate-200 px-6">
			<a href="/" class="text-xl font-bold text-blue-600">Votecatcher</a>
		</div>

		<!-- Navigation -->
		<div class="flex-1 overflow-y-auto p-4">
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

<!-- Mobile overlay -->
{#if isOpen}
	<div
		class="fixed inset-0 z-30 bg-black/50 md:hidden"
		onclick={closeMenu}
		aria-hidden="true"
	></div>
{/if}
