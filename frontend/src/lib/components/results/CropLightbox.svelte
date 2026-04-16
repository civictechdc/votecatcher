<script lang="ts">
	interface Props {
		open: boolean;
		imageUrl: string;
		onClose: () => void;
	}

	let { open, imageUrl, onClose }: Props = $props();

	$effect(() => {
		if (open) {
			const prev = document.body.style.overflow;
			document.body.style.overflow = "hidden";
			return () => { document.body.style.overflow = prev; };
		}
	});

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onClose();
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape') {
			onClose();
			return;
		}
		if (e.key === 'Tab') {
			e.preventDefault();
			const dialog = (e.currentTarget as Window).document.querySelector('[role="dialog"]');
			if (!dialog) return;
			const focusable = dialog.querySelectorAll<HTMLElement>(
				'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
			);
			if (focusable.length === 0) return;
			const active = document.activeElement;
			const first = focusable[0]!;
			const last = focusable[focusable.length - 1]!;
			if (e.shiftKey) {
				(active === first ? last : first).focus();
			} else {
				(active === last ? first : last).focus();
			}
		}
	}
</script>

<svelte:window onkeydown={handleKeyDown} />

{#if open}
	<div
		role="none"
		class="fixed inset-0 z-50 flex items-center justify-center"
		onclick={handleBackdropClick}
	>
		<div class="fixed inset-0 bg-black/75" aria-hidden="true"></div>

		<div
			role="dialog"
			aria-modal="true"
			aria-label="Image lightbox"
			class="relative z-10 max-w-[90vw] max-h-[90vh]"
		>
			<button
				type="button"
				class="absolute -top-3 -right-3 bg-white rounded-full p-1.5 shadow-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300 z-20"
				aria-label="Close lightbox"
				onclick={onClose}
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>

			<img
				src={imageUrl}
				alt="Enlarged petition signature crop"
				class="max-w-[90vw] max-h-[85vh] object-contain rounded-lg shadow-2xl"
			/>
		</div>
	</div>
{/if}
