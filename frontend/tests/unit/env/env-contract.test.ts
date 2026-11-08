import { describe, it, expect } from "vitest";

import {
	DEFAULT_DEV_TRUSTED_ORIGINS,
	normalizeOrigin,
	parseTrustedOrigins,
	validateTrustedOrigins,
} from "../../../src/lib/origins";
import { variables } from "../../../src/env";

/**
 * Env-contract unit tests (tasks 3.1/3.5; spec: trusted-origins).
 *
 * The pure helpers are exercised with explicit dev/building flags. The
 * `variables.*.schema` wiring tests run against the repo-wide `$app/env` mock
 * (tests/setup.ts: dev=true, building=false), i.e. the development branch.
 * `defineEnvVars` wraps function schemas in a Standard Schema object, so the
 * wiring goes through `~standard.validate`; issues are re-thrown with their
 * messages, mirroring how Kit fails startup on invalid values.
 */
function schemaFor(name: string): (value: string | undefined) => unknown {
	const entry = (
		variables as unknown as Record<
			string,
			| {
					schema?: {
						"~standard": {
							validate: (value: unknown) => {
								value?: unknown;
								issues?: Array<{ message?: string }>;
							};
						};
					};
			  }
			| undefined
		>
	)[name];
	const validate = entry?.schema?.["~standard"]?.validate;
	if (typeof validate !== "function") throw new Error(`no schema declared for ${name}`);
	return (value: string | undefined) => {
		const result = validate(value);
		if (result && Array.isArray(result.issues) && result.issues.length > 0) {
			throw new Error(result.issues.map((issue) => issue.message ?? String(issue)).join("; "));
		}
		return result?.value;
	};
}

describe("parseTrustedOrigins", () => {
	it("parses, trims, lowercases, and strips trailing slashes", () => {
		expect(parseTrustedOrigins("https://App.Example.com/, https://staging.example.com")).toEqual([
			"https://app.example.com",
			"https://staging.example.com",
		]);
	});

	it("de-duplicates repeated origins", () => {
		expect(parseTrustedOrigins("https://a.example.com,https://a.example.com")).toEqual([
			"https://a.example.com",
		]);
	});

	it("supports a multi-origin allowlist (staging/prod/preview)", () => {
		expect(
			parseTrustedOrigins(
				"https://app.example.com,https://staging.example.com,https://preview.example.com",
			).length,
		).toBe(3);
	});

	it("rejects a wildcard entry", () => {
		expect(() => parseTrustedOrigins("*")).toThrow(/TRUSTED_ORIGINS.*\*/);
	});

	it("rejects a wildcard inside a list", () => {
		expect(() => parseTrustedOrigins("https://a.example.com,*")).toThrow(/\*/);
	});

	it("rejects non-origin entries (path, non-http scheme, garbage)", () => {
		expect(() => parseTrustedOrigins("https://a.example.com/app")).toThrow(/bare origins/);
		expect(() => parseTrustedOrigins("ftp://a.example.com")).toThrow(/http\(s\)/);
		expect(() => parseTrustedOrigins("not-a-url")).toThrow(/invalid origin/);
	});
});

describe("validateTrustedOrigins (spec: trusted-origins)", () => {
	it("dev + unset → localhost development defaults", () => {
		expect(validateTrustedOrigins(undefined, { dev: true, building: false })).toEqual([
			...DEFAULT_DEV_TRUSTED_ORIGINS,
		]);
	});

	it("building + unset → undefined (builds must not require runtime config)", () => {
		expect(validateTrustedOrigins(undefined, { dev: false, building: true })).toBeUndefined();
	});

	it("production + unset → actionable error naming TRUSTED_ORIGINS", () => {
		expect(() => validateTrustedOrigins(undefined, { dev: false, building: false })).toThrow(
			/TRUSTED_ORIGINS is required/,
		);
	});

	it("production + whitespace-only → actionable error naming TRUSTED_ORIGINS", () => {
		expect(() => validateTrustedOrigins("  ", { dev: false, building: false })).toThrow(
			/TRUSTED_ORIGINS/,
		);
	});

	it("production + set-but-empty (commas) → actionable error", () => {
		expect(() => validateTrustedOrigins(" , , ", { dev: false, building: false })).toThrow(
			/empty allowlist/,
		);
	});

	it("production + wildcard → rejected (wildcard disables validation)", () => {
		expect(() => validateTrustedOrigins("*", { dev: false, building: false })).toThrow(/\*/);
	});

	it("valid production allowlist parses through", () => {
		expect(
			validateTrustedOrigins("https://app.example.com,https://staging.example.com", {
				dev: false,
				building: false,
			}),
		).toEqual(["https://app.example.com", "https://staging.example.com"]);
	});
});

describe("env.ts schema wiring (dev-mode $app/env mock)", () => {
	it("TRUSTED_ORIGINS.schema falls back to dev defaults when unset", () => {
		expect(schemaFor("TRUSTED_ORIGINS")(undefined)).toEqual([...DEFAULT_DEV_TRUSTED_ORIGINS]);
	});

	it("TRUSTED_ORIGINS.schema parses an explicit allowlist", () => {
		expect(schemaFor("TRUSTED_ORIGINS")("https://x.example.com")).toEqual([
			"https://x.example.com",
		]);
	});

	it("TRUSTED_ORIGINS.schema rejects a wildcard even in dev", () => {
		expect(() => schemaFor("TRUSTED_ORIGINS")("*")).toThrow(/\*/);
	});

	it("PUBLIC_FEATURES.schema parses, trims, and de-duplicates flags", () => {
		expect(schemaFor("PUBLIC_FEATURES")("mockApi, 2fa ,mockApi")).toEqual(["mockApi", "2fa"]);
	});

	it("PUBLIC_FEATURES.schema returns an empty set when unset", () => {
		expect(schemaFor("PUBLIC_FEATURES")(undefined)).toEqual([]);
	});

	it("PUBLIC_DEMO_MODE.schema coerces to boolean", () => {
		expect(schemaFor("PUBLIC_DEMO_MODE")("true")).toBe(true);
		expect(schemaFor("PUBLIC_DEMO_MODE")("false")).toBe(false);
		expect(schemaFor("PUBLIC_DEMO_MODE")(undefined)).toBe(false);
	});

	it("PUBLIC_API_URL.schema validates and normalizes", () => {
		expect(schemaFor("PUBLIC_API_URL")("http://localhost:8080/")).toBe("http://localhost:8080");
		expect(() => schemaFor("PUBLIC_API_URL")("not-a-url")).toThrow(/PUBLIC_API_URL/);
	});

	it("PUBLIC_API_URL.schema is required outside builds (dev mock: building=false)", () => {
		expect(() => schemaFor("PUBLIC_API_URL")(undefined)).toThrow(/PUBLIC_API_URL is required/);
	});

	it("ORIGIN.schema normalizes a set origin and allows unset", () => {
		expect(schemaFor("ORIGIN")("https://app.example.com/")).toBe("https://app.example.com");
		expect(schemaFor("ORIGIN")(undefined)).toBeUndefined();
		expect(() => schemaFor("ORIGIN")("nope")).toThrow(/ORIGIN/);
	});

	it("DEMO_MODE.schema coerces to boolean", () => {
		expect(schemaFor("DEMO_MODE")("true")).toBe(true);
		expect(schemaFor("DEMO_MODE")(undefined)).toBe(false);
	});
});

describe("normalizeOrigin", () => {
	it("normalizes scheme/host casing and strips a trailing slash", () => {
		expect(normalizeOrigin("HTTPS://App.Example.com/", "ORIGIN")).toBe("https://app.example.com");
	});
});
