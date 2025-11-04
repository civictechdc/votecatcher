<script lang="ts">
	import type { OcrMatch, ConfidenceThresholds } from '$lib/workspace-types';

	interface Props {
		matchScore: number;
		confidenceThreshold: ConfidenceThresholds;
	}

	let { matchScore, confidenceThreshold }: Props = $props();

	type ConfidenceDescription = 'High' | 'Medium' | 'Low';
	interface ConfidenceIndicator {
		styleClasses: string;
		score: number;
		confidenceDescription: ConfidenceDescription;
	}

	let indicator = $derived(confidenceClass(matchScore, confidenceThreshold));

	// helper to render confidence color
	function confidenceClass(
		matchScore: number,
		thresholds: ConfidenceThresholds
	): ConfidenceIndicator {
		let styleClasses: string = 'bg-red-100 text-red-800';
		let confidenceDescription: ConfidenceDescription = 'Low';

		if (matchScore >= thresholds.high) {
			styleClasses = 'bg-green-100 text-green-800';
			confidenceDescription = 'High';
		} else if (matchScore >= thresholds.medium) {
			styleClasses = 'bg-amber-100 text-amber-800';
			confidenceDescription = 'Medium';
		}

		return {
			styleClasses: styleClasses,
			confidenceDescription: confidenceDescription,
			score: matchScore
		};
	}
</script>

<span
	class={indicator.styleClasses}
	style="padding:.25rem .5rem; border-radius:6px; font-weight:600;"
>
	{indicator.confidenceDescription}
</span>
