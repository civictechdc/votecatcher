<script lang="ts">
	import { cn } from '$lib/utils/cn';
	import { tick } from 'svelte';

	interface Props {
		open: boolean;
		title?: string;
		size?: 'sm' | 'md' | 'lg';
		closeOnBackdrop?: boolean;
		onClose: () => void;
		children?: import('svelte').Snippet;
	}

	let {
		open,
		title = '',
		size = 'md',
		closeOnBackdrop = true,
		onClose,
		children
	}: Props = $props();

	let modalRef: HTMLDivElement | undefined = $state();
	let closeButtonRef: HTMLButtonElement | undefined = $state();
	let previouslyFocusedElement: HTMLElement | undefined = $state();

	const sizeClasses: Record<string, string> = {
		sm: 'max-w-sm',
		md: 'max-w-md',
		lg: 'max-w-lg'
	};

	const modalClasses = $derived(
		cn(
			'bg-white rounded-lg shadow-xl',
			'w-full mx-4',
			'max-h-[90vh] overflow-y-auto',
			sizeClasses[size]
		)
	);

	function handleBackdropClick(e: MouseEvent) {
		if (closeOnBackdrop && e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (!open) return;

		if (e.key === 'Escape') {
			onClose();
			return;
		}

		if (e.key === 'Tab' && modalRef) {
			const focusableElements = modalRef.querySelectorAll<HTMLElement>(
				'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
			);

			if (focusableElements.length === 0) {
				e.preventDefault();
				return;
			}

			const firstElement = focusableElements[0];
			const lastElement = focusableElements[focusableElements.length - 1];

			if (e.shiftKey && document.activeElement === firstElement) {
				e.preventDefault();
				lastElement.focus();
			} else if (!e.shiftKey && document.activeElement === lastElement) {
				e.preventDefault();
				firstElement.focus();
			}
		}
	}

	$effect(() => {
		if (open) {
			previouslyFocusedElement = document.activeElement as HTMLElement;

			document.addEventListener('keydown', handleKeyDown);

			tick().then(() => {
				if (closeButtonRef) {
					closeButtonRef.focus();
				}
			});

			return () => {
				document.removeEventListener('keydown', handleKeyDown);
				if (previouslyFocusedElement) {
					previouslyFocusedElement.focus();
				}
			};
		}
	});
</script>

<svelte:window on:keydown={handleKeyDown} />

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center"
		onclick={handleBackdropClick}
	>
		<!-- Backdrop -->
		<div
			class="fixed inset-0 bg-black/50 transition-opacity"
			aria-hidden="true"
		></div>

		<!-- Modal -->
		<div
			bind:this={modalRef}
			role="dialog"
			aria-modal="true"
			aria-labelledby={title ? 'modal-title' : undefined}
			class={modalClasses}
		>
			<!-- Header -->
			<div class="flex items-center justify-between p-4 border-b border-gray-200">
				{#if title}
					<h2 id="modal-title" class="text-lg font-semibold text-gray-900">
						{title}
					</h2>
				{/if}

				<button
					bind:this={closeButtonRef}
					type="button"
					class="ml-auto text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md p-1 -mr-1"
					aria-label="Close modal"
					onclick={onClose}
				>
					<svg
						class="w-5 h-5"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-4">
				{#if children}
					{@render children()}
				{/if}
			</div>
		</div>
	</div>
{/if}
