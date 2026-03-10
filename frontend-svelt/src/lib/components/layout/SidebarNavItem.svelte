<script lang="ts">
	import Home from 'lucide-svelte/icons/home';
	import FolderOpen from 'lucide-svelte/icons/folder-open';
	import Activity from 'lucide-svelte/icons/activity';
	import CheckCircle from 'lucide-svelte/icons/check-circle';
	import Settings from 'lucide-svelte/icons/settings';
	import Save from 'lucide-svelte/icons/save';
	import { cn } from '$lib/utils/cn';

	interface Props {
	 href: string;
        label: string;
        isActive?: boolean;
        icon?: 'home' | 'folder' | 'activity' | 'check-circle' | 'settings' | 'save';
    }

    let { href, label, isActive = false, icon }: Props = $props();

    const iconMap = {
        home: Home,
        folder: FolderOpen,
        activity: Activity,
        'check-circle': CheckCircle,
        settings: Settings,
        save: Save
    };

    const IconComponent = icon ? iconMap[icon] : null;
</script>

<a
	{href}
	aria-current={isActive ? 'page' : undefined}
	class={cn(
		'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
		isActive
			? 'bg-blue-50 text-blue-700'
			: 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
	)}
>
	{#if IconComponent}
		<IconComponent class="h-5 w-5" />
	{/if}
	{label}
</a>
