<script lang="ts">
	import { cn } from '$lib/utils/cn';

	interface Props {
		message: string;
		title?: string;
		variant?: 'error' | 'warning' | 'info';
		onRetry?: () => void;
	}

	let {
		message,
		title,
		variant = 'error',
		onRetry
	}: Props = $props();

	const variantClasses: Record<string, string> = {
		error: 'bg-red-50 border-red-200 text-red-800',
		warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
		info: 'bg-blue-50 border-blue-200 text-blue-800'
	};

	const iconColorClasses: Record<string, string> = {
		error: 'text-red-500',
		warning: 'text-yellow-500',
		info: 'text-blue-500'
	};

	const buttonVariantClasses: Record<string, string> = {
		error: 'bg-red-100 hover:bg-red-200 text-red-800',
		warning: 'bg-yellow-100 hover:bg-yellow-200 text-yellow-800',
		info: 'bg-blue-100 hover:bg-blue-200 text-blue-800'
	};
</script>

<div
	role="alert"
	aria-live="assertive"
	class={cn(
		'rounded-lg border p-4',
		variantClasses[variant]
	)}
>
	<div class="flex items-start gap-3">
		<svg
			class={cn('h-5 w-5 flex-shrink-0 mt-0.5', iconColorClasses[variant])}
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			stroke-width="1.5"
			stroke="currentColor"
			aria-hidden="true"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
			/>
		</svg>
		<div class="flex-1">
			{#if title}
				<h3 class="font-medium mb-1">{title}</h3>
			{/if}
			<p class="text-sm">{message}</p>
			{#if onRetry}
				<button
					type="button"
					onclick={onRetry}
					class={cn(
						'mt-3 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
						buttonVariantClasses[variant]
					)}
				>
					Try Again
				</button>
			{/if}
		</div>
	</div>
</div>
