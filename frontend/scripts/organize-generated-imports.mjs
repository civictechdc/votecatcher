#!/usr/bin/env node
/**
 * Remove unused imports from every TypeScript file in src/lib/api/generated.
 *
 * The OpenAPI generator emits both FromJSON and ToJSON imports per model, but
 * response-only/request-only types use only one direction, so half of these
 * imports are dead and lint rules (CodeQL) flag them. TypeScript's built-in
 * `organizeImports` code action strips exactly those; this script applies it
 * to the whole generated tree.
 *
 * Run between generation and stamping in `bun run generate:client`
 * (clean → generate → organize → stamp), so files are unstamped when analyzed
 * and the `// @ts-nocheck` stamp stays on line 1 afterwards. Side effects of
 * the action — removing unused imports and rewriting barrel imports to direct
 * per-file module specifiers — are intended: it makes imports minimal and
 * deterministic. Idempotent: a second run produces no changes.
 */

import { createRequire } from "node:module";
import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const require = createRequire(import.meta.url);
const ts = require("typescript");

const ROOT = path.resolve(import.meta.dirname, "../src/lib/api/generated");

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
const service = ts.createLanguageService({
	getScriptFileNames: () => files,
	getScriptVersion: () => "0",
	getScriptSnapshot: (fileName) => {
		const contents = ts.sys.readFile(fileName);
		return contents === undefined ? undefined : ts.ScriptSnapshot.fromString(contents);
	},
	getCurrentDirectory: () => ROOT,
	getDefaultLibFileName: () => ts.getDefaultLibFileName({}),
	getCompilationSettings: () => ({}),
	fileExists: ts.sys.fileExists,
	readFile: ts.sys.readFile,
	readDirectory: ts.sys.readDirectory,
	directoryExists: ts.sys.directoryExists,
	getDirectories: ts.sys.getDirectories,
});

let organized = 0;
let importsRemoved = 0;
for (const fileName of files) {
	const source = await readFile(fileName, "utf8");
	// Edits are original-content-relative, so applying them in reverse order
	// keeps earlier spans valid; forward application corrupts the output.
	const edits = service
		.organizeImports({ type: "file", fileName }, { skipDestructiveCodeActions: false }, {})
		.flatMap((change) => change.textChanges)
		.sort((a, b) => b.span.start - a.span.start);
	if (edits.length === 0) continue;
	// The action re-emits whole import blocks, so already-organized files can
	// still get edit sets whose application is a no-op; only changed files
	// count (and are written).
	let text = source;
	let removedHere = 0;
	for (const edit of edits) {
		const removed = text.slice(edit.span.start, edit.span.start + edit.span.length);
		if (/^\s*import[\s{]/.test(removed) && !edit.newText.includes("import")) removedHere += 1;
		text =
			text.slice(0, edit.span.start) +
			edit.newText +
			text.slice(edit.span.start + edit.span.length);
	}
	if (text === source) continue;
	await writeFile(fileName, text);
	organized += 1;
	importsRemoved += removedHere;
}

console.log(
	`organize-generated-imports: ${organized} of ${files.length} files organized, ${importsRemoved} imports removed in src/lib/api/generated`,
);
