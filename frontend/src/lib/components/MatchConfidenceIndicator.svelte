<script lang="ts">
	import { confidenceClass } from './matchConfidence';

	let { matchScore, confidenceThreshold } = $props();

	let indicator = $derived(() => confidenceClass(matchScore, confidenceThreshold));

	$effect(() => {
		console.log('MatchConfidenceIndicator received:', {
			matchScore,
			type: typeof matchScore,
			thresholds: confidenceThreshold,
			indicator
		});
	});
</script>

<span
	role="status"
	aria-label={'Match confidence: ' + indicator().confidenceDescription}
	class="inline-flex items-center rounded px-2 py-1 text-sm font-medium ring-1 ring-inset {indicator().styleClasses}"
>
	{indicator().confidenceDescription}
</span>
