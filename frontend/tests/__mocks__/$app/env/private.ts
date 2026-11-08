/**
 * `$app/env/private` mock — server-only declared variables from `src/env.ts`.
 * Snapshot of the mutable state in `tests/helpers/env-mocks.ts`; re-evaluated
 * on every `vi.resetModules()`.
 */
import { privateEnvState } from "../../../helpers/env-mocks";

const state = privateEnvState();

export const ORIGIN = state.ORIGIN;
export const TRUSTED_ORIGINS = state.TRUSTED_ORIGINS;
export const DATABASE_URL = state.DATABASE_URL;
export const BETTER_AUTH_SECRET = state.BETTER_AUTH_SECRET;
export const DEMO_MODE = state.DEMO_MODE;
export const OCR_PROVIDER_NAME = state.OCR_PROVIDER_NAME;
export const OCR_PROVIDER_MODEL = state.OCR_PROVIDER_MODEL;
export const OCR_PROVIDER_API_KEY = state.OCR_PROVIDER_API_KEY;
