import type { MatchRow } from '$lib/workspace-types';
import { DEMO_MODE } from '$env/static/private';

export const isDemoMode = (): boolean => {
	return DEMO_MODE === '1' || DEMO_MODE === 'true';
};

export type DemoState = {
	matchList: MatchRow[];
};
