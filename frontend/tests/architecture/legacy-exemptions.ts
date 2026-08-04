export interface LegacyExemption {
	source: string;
	target: string;
	reason: string;
	owner: string;
	removalIssue: string;
	removalCriteria: string;
}

export const legacyExemptions: readonly LegacyExemption[] = [];
