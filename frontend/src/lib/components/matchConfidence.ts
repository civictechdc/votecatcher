import type { ConfidenceThresholds } from "$lib/workspace-types";

type ConfidenceDescription = "High" | "Medium" | "Low" | "No Score" | "Invalid Score";
interface ConfidenceIndicator {
	styleClasses: string;
	score: number;
	confidenceDescription: ConfidenceDescription;
}

export function confidenceClass(
	matchScore: number | string,
	thresholds?: ConfidenceThresholds,
): ConfidenceIndicator {
	// Default thresholds per request: high >=95, medium >=90
	const thr = thresholds ?? { high: 95, medium: 90 };

	let styleClasses = "bg-red-100 text-red-800";
	let confidenceDescription: ConfidenceDescription = "Low";

	if (matchScore === undefined || matchScore === null || matchScore === "") {
		return {
			styleClasses: "bg-gray-100 text-gray-800",
			confidenceDescription: "No Score",
			score: 0,
		};
	}

	let score: number;
	if (typeof matchScore === "string") {
		score = parseFloat(matchScore as string);
		if (!isNaN(score) && score >= 0 && score <= 1) {
			score = score * 100;
		}
	} else {
		score = matchScore as number;
	}

	if (isNaN(score)) {
		return {
			styleClasses: "bg-gray-100 text-gray-800",
			confidenceDescription: "Invalid Score",
			score: 0,
		};
	}

	if (score >= thr.high) {
		// darker green background with white text for contrast
		styleClasses = "bg-green-600 text-white";
		confidenceDescription = "High";
	} else if (score >= thr.medium) {
		// light amber background with dark text for readability
		styleClasses = "bg-amber-100 text-amber-800";
		confidenceDescription = "Medium";
	} else {
		// Low
		styleClasses = "bg-red-600 text-white";
		confidenceDescription = "Low";
	}

	return { styleClasses, confidenceDescription, score };
}
