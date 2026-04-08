<script lang="ts">
	import type { ConfidenceThresholds } from '$lib/workspace-types';

	// use Svelte 5 runes-style props to match the rest of the codebase
	let { matchScore, confidenceThreshold } = $props();

	type ConfidenceDescription = 'High' | 'Medium' | 'Low' | 'No Score' | 'Invalid Score';
	interface ConfidenceIndicator {
		styleClasses: string;
		score: number;
		confidenceDescription: ConfidenceDescription;
	}

	// compute indicator as a derived reactive value
	import { confidenceClass } from './matchConfidence';

	let indicator = $derived(() => confidenceClass(matchScore, confidenceThreshold));

	// Debug logging (effect)
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
