// Explanation: Simple vitest test to ensure getSession calls the correct URL.
// Reasoning: keep tests focused and fast; no DOM required.
import { describe, it, expect, vi } from 'vitest';
import { getSession } from '$lib/api/auth';

describe('getSession', () => {
	it('calls backend session endpoint and returns parsed json', async () => {
		const fake = { user: { id: 'u1' } };
		global.fetch = vi.fn(() =>
			Promise.resolve({ ok: true, json: () => Promise.resolve(fake) } as unknown as Response)
		);

		const result = await getSession('http://api.test');
		expect(result).toEqual(fake);
		expect(global.fetch as any).toHaveBeenCalledWith(
			'http://api.test/auth/session',
			expect.any(Object)
		);
	});
});
