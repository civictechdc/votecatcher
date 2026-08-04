import { describe, expect, it } from "vitest";
import { projectFiles } from "archunit";

const ARCH_TIMEOUT = 60000;

describe("frontend architecture", () => {
	it(
		"keeps production source free of import cycles",
		async () => {
			const rule = projectFiles().inFolder("src/**").should().haveNoCycles();

			const violations = await rule.check();
			expect(violations).toEqual([]);
		},
		ARCH_TIMEOUT,
	);

	it(
		"prevents browser routes from importing server-only libraries",
		async () => {
			const rule = projectFiles()
				.inPath("src/routes/**/*.{ts,svelte}", {
					except: { withName: "+*.server.ts" },
				})
				.shouldNot()
				.dependOnFiles()
				.inFolder("src/lib/server/**");

			const violations = await rule.check();
			expect(violations).toEqual([]);
		},
		ARCH_TIMEOUT,
	);

	it(
		"prevents stores from importing server-only libraries",
		async () => {
			const rule = projectFiles()
				.inFolder("src/lib/stores/**")
				.shouldNot()
				.dependOnFiles()
				.inFolder("src/lib/server/**");

			const violations = await rule.check();
			expect(violations).toEqual([]);
		},
		ARCH_TIMEOUT,
	);

	it(
		"prevents server libraries from importing route UI",
		async () => {
			const rule = projectFiles()
				.inFolder("src/lib/server/**")
				.shouldNot()
				.dependOnFiles()
				.inFolder("src/routes/**");

			const violations = await rule.check();
			expect(violations).toEqual([]);
		},
		ARCH_TIMEOUT,
	);
});
