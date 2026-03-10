<script lang="ts">
	import { cn } from '$lib/utils/cn';
	import { tick } from 'svelte';

	interface Option {
		value: string;
		label: string;
		disabled?: boolean;
	}

	interface Props {
		id: string;
		options: Option[];
		value?: string;
		label?: string;
		placeholder?: string;
		helperText?: string;
		searchable?: boolean;
		clearable?: boolean;
		disabled?: boolean;
		error?: boolean;
		errorMessage?: string;
		required?: boolean;
		class?: string;
		onValueChange?: (value: string | undefined) => void;
	}

	let {
		id,
		options,
		value = '',
		label = '',
		placeholder = 'Select an option',
		helperText = '',
		searchable = false,
		clearable = false,
		disabled = false,
		error = false,
		errorMessage = '',
		required = false,
		class: className = '',
		onValueChange
	}: Props = $props();

	let open = $state(false);
	let searchQuery = $state('');
	let highlightedIndex = $state(-1);
	let containerRef: HTMLDivElement | undefined = $state();
	let listboxRef: HTMLUListElement | undefined = $state();
	let searchInputRef: HTMLInputElement | undefined = $state();

	const listboxId = $derived(`${id}-listbox`);
	const helperId = $derived(`${id}-helper`);
	const errorId = $derived(`${id}-error`);

	const selectedOption = $derived(options.find((opt) => opt.value === value));
	const displayLabel = $derived(selectedOption?.label ?? placeholder);
	const hasValue = $derived(value !== '' && value !== undefined);

	const filteredOptions = $derived(
		searchable && searchQuery
			? options.filter((opt) => opt.label.toLowerCase().includes(searchQuery.toLowerCase()))
			: options
	);

	const triggerClasses = $derived(
		cn(
			'w-full px-3 py-2 border rounded-md shadow-sm',
			'flex items-center justify-between gap-2',
			'bg-white text-gray-900',
			'focus:outline-none focus:ring-2 focus:ring-offset-0',
			error
				? 'border-red-500 focus:ring-red-500 focus:border-red-500'
				: 'border-gray-300 focus:ring-blue-500 focus:border-blue-500',
			disabled && 'opacity-50 cursor-not-allowed bg-gray-50',
			open && 'ring-2 ring-blue-500 border-blue-500',
			className
		)
	);

	function toggleDropdown() {
		if (disabled) return;
		open = !open;
		if (open) {
			highlightedIndex = -1;
			searchQuery = '';
		}
	}

	function closeDropdown() {
		open = false;
		highlightedIndex = -1;
		searchQuery = '';
	}

	function selectOption(optionValue: string) {
		onValueChange?.(optionValue);
		closeDropdown();
	}

	function clearSelection(e: Event) {
		e.stopPropagation();
		onValueChange?.(undefined);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (disabled) return;

		switch (e.key) {
			case 'Enter':
			case ' ':
				e.preventDefault();
				if (!open) {
					toggleDropdown();
				} else if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
					selectOption(filteredOptions[highlightedIndex].value);
				}
				break;
			case 'Escape':
				e.preventDefault();
				closeDropdown();
				break;
			case 'ArrowDown':
				e.preventDefault();
				if (!open) {
					toggleDropdown();
				} else {
					highlightedIndex = Math.min(highlightedIndex + 1, filteredOptions.length - 1);
					scrollToHighlighted();
				}
				break;
			case 'ArrowUp':
				e.preventDefault();
				if (open) {
					highlightedIndex = Math.max(highlightedIndex - 1, 0);
					scrollToHighlighted();
				}
				break;
		}
	}

	function scrollToHighlighted() {
		tick().then(() => {
			if (listboxRef && highlightedIndex >= 0) {
				const highlightedEl = listboxRef.children[highlightedIndex] as HTMLElement;
				highlightedEl?.scrollIntoView?.({ block: 'nearest' });
			}
		});
	}

	function handleClickOutside(e: MouseEvent) {
		if (containerRef && !containerRef.contains(e.target as Node)) {
			closeDropdown();
		}
	}

	function handleOptionKeydown(e: KeyboardEvent, option: Option) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			if (!option.disabled) {
				selectOption(option.value);
			}
		}
	}

	$effect(() => {
		if (open) {
			document.addEventListener('click', handleClickOutside);
			if (searchable && searchInputRef) {
				searchInputRef.focus();
			}
		}
		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});
</script>

<div bind:this={containerRef} class="relative w-full">
	{#if label}
		<label for={id} class="block text-sm font-medium text-gray-700 mb-1">
			{label}
			{#if required}
				<span class="text-red-500" aria-label="required">*</span>
			{/if}
		</label>
	{/if}

	<div class="relative">
		<button
			{id}
			type="button"
			role="combobox"
			aria-haspopup="listbox"
			aria-expanded={open ? 'true' : 'false'}
			aria-controls={listboxId}
			aria-invalid={error ? 'true' : undefined}
			aria-describedby={helperText && !error ? helperId : undefined}
			aria-errormessage={error && errorMessage ? errorId : undefined}
			{disabled}
			class={triggerClasses}
			onclick={toggleDropdown}
			onkeydown={handleKeydown}
		>
			<span class={cn('truncate', !hasValue && 'text-gray-500')}>{displayLabel}</span>
			<span class="flex items-center gap-1">
				<svg
					class={cn('w-4 h-4 text-gray-500 transition-transform', open && 'rotate-180')}
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</span>
		</button>

		{#if clearable && hasValue && !disabled}
			<button
				type="button"
				aria-label="Clear selection"
				class="absolute right-6 top-1/2 -translate-y-1/2 p-0.5 hover:bg-gray-100 rounded z-10"
				onclick={clearSelection}
			>
				<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		{/if}
	</div>

	{#if open}
		<div class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
			{#if searchable}
				<div class="p-2 border-b border-gray-200">
					<input
						bind:this={searchInputRef}
						type="text"
						placeholder="Search..."
						class="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
						bind:value={searchQuery}
						onkeydown={handleKeydown}
					/>
				</div>
			{/if}

			<ul
				bind:this={listboxRef}
				id={listboxId}
				role="listbox"
				aria-label={label ? `${label} options` : 'Options'}
				class="max-h-60 overflow-auto py-1"
			>
				{#if filteredOptions.length === 0}
					<li class="px-3 py-2 text-sm text-gray-500 italic">No options found</li>
				{:else}
					{#each filteredOptions as option, index (option.value)}
						<li
							role="option"
							tabindex="-1"
							data-value={option.value}
							aria-selected={value === option.value ? 'true' : 'false'}
							data-highlighted={highlightedIndex === index ? 'true' : undefined}
							class={cn(
								'px-3 py-2 cursor-pointer flex items-center justify-between',
								'hover:bg-gray-100',
								highlightedIndex === index && 'bg-blue-50',
								option.disabled && 'opacity-50 cursor-not-allowed',
								value === option.value && 'bg-blue-50'
							)}
							onclick={() => !option.disabled && selectOption(option.value)}
							onkeydown={(e) => handleOptionKeydown(e, option)}
							onmouseenter={() => (highlightedIndex = index)}
						>
							<span>{option.label}</span>
							{#if value === option.value}
								<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
							{/if}
						</li>
					{/each}
				{/if}
			</ul>
		</div>
	{/if}

	{#if helperText && !error}
		<p {id} class="mt-1 text-sm text-gray-500">{helperText}</p>
	{/if}

	{#if error && errorMessage}
		<p {id} class="mt-1 text-sm text-red-600">{errorMessage}</p>
	{/if}
</div>
