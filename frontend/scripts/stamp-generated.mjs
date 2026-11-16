#!/usr/bin/env node
/**
 * Prepend `// @ts-nocheck` to every TypeScript file in src/lib/api/generated
 * except the `apis/index.ts` barrel.
 *
 * The OpenAPI generator's output does not compile under this repo's strict
 * tsconfig (erasableSyntaxOnly, noUnusedLocals, noUncheckedIndexedAccess).
 * Hand-written code keeps full strictness; generated files opt out per-file
 * via this stamp.
 *
 * The barrel is deliberately NOT stamped: its `export *` lines compile fine
 * under strict mode since the provider router dropped its dual tag
 * (ADR-free fix: `tags=["settings", "providers"]` → `tags=["providers"]`),
 * and leaving it checkable means any future tag overlap that reintroduces
 * TS2308 re-export collisions fails `bun run check` instead of hiding behind
 * the stamp.
 *
 * Run as part of `bun run generate:client` (generator runs first). Idempotent
 * and deterministic: files already stamped are left untouched, directories are
 * walked in sorted order, and nothing else in the files is modified.
 */

import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const STAMP = "// @ts-nocheck";
const ROOT = path.resolve(import.meta.dirname, "../src/lib/api/generated");
// Not stamped — see docblock above.
const UNSTAMPED_FILES = new Set([path.join("apis", "index.ts")]);

/** @returns {Promise<string[]>} sorted .ts file paths under `dir` */
async function tsFiles(dir) {
	const entries = await readdir(dir, { withFileTypes: true });
	const files = [];
	for (const entry of entries.sort((a, b) => (a.name > b.name ? 1 : -1))) {
		const full = path.join(dir, entry.name);
		if (entry.isDirectory()) files.push(...(await tsFiles(full)));
		else if (entry.name.endsWith(".ts")) files.push(full);
	}
	return files.sort();
}

const files = await tsFiles(ROOT);
let stamped = 0;
for (const file of files) {
	if (UNSTAMPED_FILES.has(path.relative(ROOT, file))) continue;
	const source = await readFile(file, "utf8");
	// Tolerate CRLF output: the first line may end in \r, which would fail the
	// exact match and prepend a duplicate stamp on every run.
	const firstLine = source.split("\n", 1)[0].replace(/\r$/, "");
	if (firstLine === STAMP) continue;
	await writeFile(file, `${STAMP}\n${source}`);
	stamped += 1;
}
console.log(
	`stamp-generated: ${stamped} of ${files.length} files stamped in src/lib/api/generated (apis/index.ts left unstamped)`,
);
