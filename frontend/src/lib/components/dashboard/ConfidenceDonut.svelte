<script lang="ts">
	interface Props {
		high: number;
		medium: number;
		low: number;
		total: number;
		size?: 'sm' | 'md' | 'lg';
	}

	let { high, medium, low, total, size = 'md' }: Props = $props();

	const sizeClasses = {
		sm: 'w-32 h-32',
		md: 'w-48 h-48',
		lg: 'w-64 h-64'
	};

	const highPercentage = $derived(total > 0 ? (high / total) * 100 : 0);
	const mediumPercentage = $derived(total > 0 ? (medium / total) * 100 : 0);
	const lowPercentage = $derived(total > 0 ? (low / total) * 100 : 0);

	const highStrokeDash = $derived(total > 0 ? (highPercentage / 100) * 283 : 0);
	const mediumStrokeDash = $derived(total > 0 ? (mediumPercentage / 100) * 283 : 0);
	const lowStrokeDash = $derived(total > 0 ? (lowPercentage / 100) * 283 : 0);

	const highOffset = $derived(0);
	const mediumOffset = $derived(-highStrokeDash);
	const lowOffset = $derived(-(highStrokeDash + mediumStrokeDash));
</script>

<div class="flex items-center gap-6" data-testid="confidence-donut">
	<div class="relative {sizeClasses[size]}">
		<svg viewBox="0 0 100 100" class="transform -rotate-90 w-full h-full">
			<circle
				cx="50"
				cy="50"
				r="45"
				fill="none"
				stroke="#e2e8f0"
				stroke-width="10"
			/>
			{#if total > 0}
				<circle
					cx="50"
					cy="50"
					r="45"
					fill="none"
					stroke="#22c55e"
					stroke-width="10"
					stroke-dasharray="{highStrokeDash} 283"
					stroke-dashoffset="{highOffset}"
					class="transition-all duration-500"
					role="img"
					aria-label="High confidence: {highPercentage.toFixed(1)}%"
				/>
				<circle
					cx="50"
					cy="50"
					r="45"
					fill="none"
					stroke="#eab308"
					stroke-width="10"
					stroke-dasharray="{mediumStrokeDash} 283"
					stroke-dashoffset="{mediumOffset}"
					class="transition-all duration-500"
					role="img"
					aria-label="Medium confidence: {mediumPercentage.toFixed(1)}%"
				/>
				<circle
					cx="50"
					cy="50"
					r="45"
					fill="none"
					stroke="#ef4444"
					stroke-width="10"
					stroke-dasharray="{lowStrokeDash} 283"
					stroke-dashoffset="{lowOffset}"
					class="transition-all duration-500"
					role="img"
					aria-label="Low confidence: {lowPercentage.toFixed(1)}%"
				/>
			{/if}
		</svg>
		<div class="absolute inset-0 flex flex-col items-center justify-center">
			<span class="text-2xl font-bold text-slate-900">{total}</span>
			<span class="text-xs text-slate-500">total</span>
		</div>
	</div>

	<div class="space-y-3">
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full bg-green-500"></div>
			<span class="text-sm text-slate-600">High (≥80%)</span>
			<span class="ml-auto text-sm font-medium text-slate-900">{high} ({highPercentage.toFixed(1)}%)</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full bg-yellow-500"></div>
			<span class="text-sm text-slate-600">Medium (50-80%)</span>
			<span class="ml-auto text-sm font-medium text-slate-900">{medium} ({mediumPercentage.toFixed(1)}%)</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full bg-red-500"></div>
			<span class="text-sm text-slate-600">Low (&lt;50%)</span>
			<span class="ml-auto text-sm font-medium text-slate-900">{low} ({lowPercentage.toFixed(1)}%)</span>
		</div>
	</div>
</div>
