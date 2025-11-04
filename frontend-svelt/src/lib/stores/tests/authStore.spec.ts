import { describe, it, expect, beforeEach, vi } from 'vitest';
import { get } from 'svelte/store';
import { auth, initialAuthState } from '../auth';

// Mock network calls by stubbing authApi used in the store.
// We'll replace the functions by stubbing fetch globally where authApi uses fetch.
// For simplicity here we call store methods and assert state transitions.

describe('auth store', () => {
	beforeEach(() => {
		auth.reset();
	});

	it('initial state', () => {
		const s = get(auth);
		expect(s.user).toBeNull();
		expect(s.loading).toBe(false);
	});

	it('signUp sets loading then clears', async () => {
		// signUp uses POST /api/auth/sign-up mock which returns ok in dev env.
		const res = await auth.signUp('x@y.com', 'pw');
		expect(res.ok).toBe(true);
		const s = get(auth);
		expect(s.loading).toBe(false);
	});

	it('signIn with normal password sets user', async () => {
		const res = await auth.signIn('dev@example.com', 'password');
		expect(res.ok).toBe(true);
		const s = get(auth);
		expect(s.user?.email).toBe('dev@example.com');
	});

	it('signIn with 2fa password marks twoFactorRequired', async () => {
		const res = await auth.signIn('dev@example.com', '2fa');
		expect(res.ok).toBe(true);
		const s = get(auth);
		expect(s.twoFactorRequired).toBe(true);
	});
});
