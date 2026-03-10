<script lang="ts">
	import { cn } from '$lib/utils/cn';

	interface Props {
		id: string;
		type?: 'text' | 'email' | 'password' | 'number' | 'file';
		label?: string;
		name?: string;
		value?: string | number;
		placeholder?: string;
		helperText?: string;
		errorMessage?: string;
		disabled?: boolean;
		readonly?: boolean;
		required?: boolean;
		error?: boolean;
		class?: string;
	}

	let {
		id,
		type = 'text',
		label = '',
		name = id,
		value = '',
		placeholder = '',
		helperText = '',
		errorMessage = '',
		disabled = false,
		readonly = false,
		required = false,
		error = false,
		class: className = ''
	}: Props = $props();

	const helperId = $derived(`${id}-helper`);
	const errorId = $derived(`${id}-error`);

	const inputClasses = $derived(
		cn(
			'w-full px-3 py-2 border rounded-md shadow-sm',
			'focus:outline-none focus:ring-2 focus:ring-offset-0',
			'bg-white text-gray-900',
			error
				? 'border-red-500 focus:ring-red-500 focus:border-red-500'
				: 'border-gray-300 focus:ring-blue-500 focus:border-blue-500',
			disabled && 'opacity-50 cursor-not-allowed bg-gray-50',
			className
		)
	);
</script>

<div class="w-full">
	{#if label}
		<label for={id} class="block text-sm font-medium text-gray-700 mb-1">
			{label}
			{#if required}
				<span class="text-red-500" aria-label="required">*</span>
			{/if}
		</label>
	{/if}

	<input
		{id}
		{type}
		{name}
		{value}
		{placeholder}
		{disabled}
		{readonly}
		{required}
		class={inputClasses}
		aria-invalid={error ? 'true' : undefined}
		aria-describedby={helperText ? helperId : undefined}
		aria-errormessage={error && errorMessage ? errorId : undefined}
	/>

	{#if helperText && !error}
		<p {id} class="mt-1 text-sm text-gray-500">{helperText}</p>
	{/if}

	{#if error && errorMessage}
		<p {id} class="mt-1 text-sm text-red-600">{errorMessage}</p>
	{/if}
</div>
