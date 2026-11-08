/**
 * `$app/env/public` mock — snapshot of the mutable state in
 * `tests/helpers/env-mocks.ts` (see there for usage). Re-evaluated on every
 * `vi.resetModules()`, so each re-import picks up the latest `setPublicEnv`.
 */
import { publicEnvState } from "../../../helpers/env-mocks";

const state = publicEnvState();

export const PUBLIC_API_URL = state.PUBLIC_API_URL;
export const PUBLIC_DEMO_MODE = state.PUBLIC_DEMO_MODE;
export const PUBLIC_FEATURES = state.PUBLIC_FEATURES;
