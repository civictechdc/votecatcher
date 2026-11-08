/**
 * Mutable backing state for the `$app/env/public` / `$app/env/private` vitest
 * mocks (`tests/__mocks__/$app/env/`). Kit 3 replaces `$env/static/public`
 * with declared variables from `src/env.ts`; the mock files export snapshots
 * of this state, so tests drive module-load-time reads with the familiar
 * set → `vi.resetModules()` → dynamic-import flow:
 *
 *   setPublicEnv({ PUBLIC_FEATURES: ["mockApi"] });
 *   vi.resetModules();
 *   const mod = await import("#lib/config/featureFlags.ts");
 *
 * `tests/setup.ts` resets both states to defaults before every test.
 */

export interface PublicEnvMockState {
	PUBLIC_API_URL: string;
	PUBLIC_DEMO_MODE: boolean;
	PUBLIC_FEATURES: string[];
}

export interface PrivateEnvMockState {
	ORIGIN: string | undefined;
	TRUSTED_ORIGINS: string[] | undefined;
	DATABASE_URL: string;
	BETTER_AUTH_SECRET: string;
	DEMO_MODE: boolean;
	OCR_PROVIDER_NAME: string | undefined;
	OCR_PROVIDER_MODEL: string | undefined;
	OCR_PROVIDER_API_KEY: string | undefined;
}

export const DEFAULT_PUBLIC_ENV: PublicEnvMockState = {
	// Mirrors frontend/.env so tests that don't override see the real dev base.
	PUBLIC_API_URL: "http://localhost:8080",
	PUBLIC_DEMO_MODE: false,
	PUBLIC_FEATURES: [],
};

export const DEFAULT_PRIVATE_ENV: PrivateEnvMockState = {
	ORIGIN: "http://localhost:5173",
	TRUSTED_ORIGINS: ["http://localhost", "http://localhost:5173"],
	DATABASE_URL: "postgresql://test:test@localhost:5432/test", // pragma: allowlist secret
	BETTER_AUTH_SECRET: "test-secret-not-for-prod", // pragma: allowlist secret
	DEMO_MODE: false,
	OCR_PROVIDER_NAME: undefined,
	OCR_PROVIDER_MODEL: undefined,
	OCR_PROVIDER_API_KEY: undefined,
};

interface EnvMockCarrier {
	__vcPublicEnvMock?: PublicEnvMockState;
	__vcPrivateEnvMock?: PrivateEnvMockState;
}

const carrier = globalThis as typeof globalThis & EnvMockCarrier;

export function publicEnvState(): PublicEnvMockState {
	return (carrier.__vcPublicEnvMock ??= { ...DEFAULT_PUBLIC_ENV });
}

export function privateEnvState(): PrivateEnvMockState {
	return (carrier.__vcPrivateEnvMock ??= { ...DEFAULT_PRIVATE_ENV });
}

export function setPublicEnv(patch: Partial<PublicEnvMockState>): void {
	Object.assign(publicEnvState(), patch);
}

export function setPrivateEnv(patch: Partial<PrivateEnvMockState>): void {
	Object.assign(privateEnvState(), patch);
}

export function resetEnvMocks(): void {
	carrier.__vcPublicEnvMock = { ...DEFAULT_PUBLIC_ENV };
	carrier.__vcPrivateEnvMock = { ...DEFAULT_PRIVATE_ENV };
}
