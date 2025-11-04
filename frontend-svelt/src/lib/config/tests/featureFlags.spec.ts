import { describe, it, expect, beforeEach } from 'vitest';
import { featureFlags } from '../featureFlags';

describe('featureFlags (dev local toggle)', () => {
	beforeEach(() => {
		try {
			localStorage.removeItem('vc:flags');
		} catch {}
	});

	it('toggles a flag on and off locally', () => {
		const key = 'test-flag';
		// ensure off
		try {
			localStorage.removeItem('vc:flags');
		} catch {}
		expect(featureFlags.isEnabled(key)).toBe(false);
		featureFlags.toggleLocal(key);
		expect(featureFlags.isEnabled(key)).toBe(true);
		featureFlags.toggleLocal(key);
		expect(featureFlags.isEnabled(key)).toBe(false);
	});
});
