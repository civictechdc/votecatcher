<script lang="ts">
	interface Props {
		open: boolean;
		imageUrl: string;
		onClose: () => void;
		clipCoords?: { top: number; bottom: number } | null;
	}

	let { open, imageUrl, onClose, clipCoords }: Props = $props();

	$effect(() => {
		if (open) {
			const prev = document.body.style.overflow;
			document.body.style.overflow = "hidden";
			return () => { document.body.style.overflow = prev; };
		}
	});

	function handleDialogClick(e: MouseEvent) {
		if (!clipCoords) {
			e.stopPropagation();
			return;
		}
		const img = (e.currentTarget as HTMLElement).querySelector("img");
		if (!img) return;
		const rect = img.getBoundingClientRect();
		const visibleTop = rect.top + rect.height * clipCoords.top;
		const visibleBottom = rect.top + rect.height * clipCoords.bottom;
		if (e.clientY >= visibleTop && e.clientY <= visibleBottom) {
			e.stopPropagation();
		}
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

	let clipStyle = $derived(
		clipCoords
			? `clip-path:inset(${(clipCoords.top * 100).toFixed(2)}% 0 ${(100 - clipCoords.bottom * 100).toFixed(2)}% 0);`
			: ""
	);
</script>

<svelte:window onkeydown={handleKeyDown} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/75"
		onclick={onClose}
	>
		<div
			role="dialog"
			aria-modal="true"
			aria-label="Image lightbox"
			class="relative z-10 max-w-[90vw] max-h-[90vh]"
			onclick={handleDialogClick}
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
				style={clipStyle}
			/>
		</div>
	</div>
{/if}
