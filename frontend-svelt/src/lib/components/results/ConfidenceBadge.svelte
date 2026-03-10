<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		level: 'HIGH' | 'MEDIUM' | 'LOW';
		size?: 'sm' | 'md';
	}

	let { level, size = 'md' }: Props = $props();

	const colorClasses = {
		HIGH: 'bg-green-100 text-green-800 border-green-200',
		MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
		LOW: 'bg-red-100 text-red-800 border-red-200'
	};

	const sizeClasses = {
		sm: 'px-2 py-0.5 text-xs',
		md: 'px-2.5 py-1 text-sm'
	};
</script>

<span
	class={cn(
		'inline-flex items-center rounded-full border font-medium',
		colorClasses[level],
		sizeClasses[size]
	)}
>
	{level}
</span>
