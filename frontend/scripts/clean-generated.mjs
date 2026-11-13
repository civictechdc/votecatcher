#!/usr/bin/env node
/**
 * Empty src/lib/api/generated before regeneration, keeping
 * .openapi-generator-ignore (generator directives must survive).
 *
 * The OpenAPI generator overwrites files but never deletes them, so a model or
 * API dropped from the contract would leave an orphaned generated file behind —
 * invisible to the CI freshness diff, which only compares regenerated output.
 * Run as the first step of `bun run generate:client` (clean → generate → stamp).
 */

import { readdir, rm } from "node:fs/promises";
import path from "node:path";

const KEEP = ".openapi-generator-ignore";
const ROOT = path.resolve(import.meta.dirname, "../src/lib/api/generated");

try {
	for (const entry of await readdir(ROOT)) {
		if (entry === KEEP) continue;
		await rm(path.join(ROOT, entry), { recursive: true, force: true });
	}
	console.log(`clean-generated: cleared src/lib/api/generated (kept ${KEEP})`);
} catch (error) {
	if (error.code !== "ENOENT") throw error;
	// Nothing generated yet — the generator creates the directory itself.
}
