/**
 * `$app/env` mock (Kit 3 surface: `browser`, `dev`, `building`, `version`).
 *
 * Values mirror the repo-wide `vi.mock("$app/env")` in tests/setup.ts. Most
 * suites are SSR-flavored jsdom unit tests, hence `browser: false`.
 */
export const browser = false;
export const dev = true;
export const building = false;
export const version = "test";
