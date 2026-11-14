#!/usr/bin/env node
/**
 * Verify the OpenAPI generator jar before codegen runs (provenance hardening).
 *
 * `@openapitools/openapi-generator-cli` normally downloads its generator jar
 * from Maven Central at runtime with no integrity check, so the jar powering
 * the contract → TS-client pipeline can silently change between runs. This
 * script pins the artifact:
 *
 *   - version is fixed to GENERATOR_VERSION below and cross-checked against
 *     frontend/openapitools.json `generator-cli.version` on every run, so the
 *     script pin and the wrapper config cannot drift apart silently;
 *   - the jar must match PINNED_SHA256 (primary check), corroborated by
 *     EXPECTED_SHA1 and EXPECTED_BYTES; any mismatch fails closed;
 *   - the verified jar is cached at .generator-jar-cache/ and its absolute
 *     path is printed to stdout so package.json can pass it to
 *     `openapi-generator-cli --custom-generator <jar> generate`, forcing the
 *     CLI to run only this jar (the wrapper's own unverified download cache is
 *     removed first — and asserted gone — so it cannot take classpath
 *     precedence);
 *   - `--jar-path <file>` verifies a caller-supplied pre-verified jar (e.g.
 *     an out-of-band download) instead of the cache. CI and the regen recipe
 *     use the default cache path, not this override.
 *
 * A corrupted or tampered cache jar is evicted and re-downloaded (the fresh
 * download is verified before it is cached), so a stale CI cache cannot wedge
 * codegen. Every other failure exits non-zero. Diagnostics go to stderr; the
 * verified jar path is the only stdout output.
 */

import { createHash, randomBytes } from "node:crypto";
import {
	closeSync,
	existsSync,
	fsyncSync,
	lstatSync,
	mkdirSync,
	openSync,
	readFileSync,
	renameSync,
	rmSync,
	unlinkSync,
	writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import path from "node:path";

const GENERATOR_VERSION = "7.27.0";
// Primary pin. Cross-checked at adoption against Maven Central's served .sha1
// and the artifact byte size (corroboration constants below).
// Public Maven Central checksums — not secrets; allowlist pragma for detect-secrets.
const PINNED_SHA256 = "db9c4b738727698748746144394cb7ee96512fe50166555baaeeca9311ee1dba"; // pragma: allowlist secret
const EXPECTED_SHA1 = "1c5eb64ca278d5b018342b15594353a6569fbc9a"; // pragma: allowlist secret
const EXPECTED_BYTES = 33068535;
const DOWNLOAD_TIMEOUT_MS = 120_000;
const DOWNLOAD_URL = `https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/${GENERATOR_VERSION}/openapi-generator-cli-${GENERATOR_VERSION}.jar`;

const SCRIPT_DIR = import.meta.dirname;
const FRONTEND_DIR = path.resolve(SCRIPT_DIR, "..");
const CACHE_DIR = path.join(FRONTEND_DIR, ".generator-jar-cache");
const CACHE_JAR = path.join(CACHE_DIR, `openapi-generator-cli-${GENERATOR_VERSION}.jar`);
const OPENAPITOOLS_CONFIG = path.join(FRONTEND_DIR, "openapitools.json");
const WRAPPER_STORAGE_DEFAULT = path.join(
	FRONTEND_DIR,
	"node_modules/@openapitools/openapi-generator-cli/versions",
);

function log(message) {
	process.stderr.write(`${message}\n`);
}

function fail(message) {
	log(`ERROR: ${message}`);
	process.exit(1);
}

/**
 * Verify pinned-artifact bytes: sha256 first (primary), then sha1 and byte
 * size as corroboration. Returns { ok: true } or { ok: false, message }.
 */
function verifyIntegrity(label, bytes) {
	const actualSha256 = createHash("sha256").update(bytes).digest("hex");
	if (actualSha256 !== PINNED_SHA256) {
		return {
			ok: false,
			message:
				`${label} failed checksum verification\n` +
				`  expected sha256: ${PINNED_SHA256}\n` +
				`  actual   sha256: ${actualSha256}`,
		};
	}
	const problems = [];
	const actualSha1 = createHash("sha1").update(bytes).digest("hex");
	if (actualSha1 !== EXPECTED_SHA1) {
		problems.push(`  sha1: expected ${EXPECTED_SHA1}, actual ${actualSha1}`);
	}
	if (bytes.length !== EXPECTED_BYTES) {
		problems.push(`  bytes: expected ${EXPECTED_BYTES}, actual ${bytes.length}`);
	}
	if (problems.length > 0) {
		return {
			ok: false,
			message: `${label} matched sha256 but failed corroboration:\n${problems.join("\n")}`,
		};
	}
	log(
		`Verified generator jar ${GENERATOR_VERSION}: sha256 ${actualSha256} (sha1 + ${bytes.length} bytes corroborated)`,
	);
	return { ok: true };
}

/**
 * Cross-check the script's pin against openapitools.json and resolve the
 * wrapper's jar storage dir (honoring generator-cli.storageDir). Aborts on
 * version drift — under --custom-generator the wrapper never reads that
 * config version, so drift here would otherwise be silent.
 */
function crossCheckWrapperConfig() {
	if (!existsSync(OPENAPITOOLS_CONFIG)) {
		fail(`Missing ${OPENAPITOOLS_CONFIG} — cannot cross-check the pinned generator version.`);
	}
	let config;
	try {
		config = JSON.parse(readFileSync(OPENAPITOOLS_CONFIG, "utf8"));
	} catch (error) {
		fail(`Cannot parse ${OPENAPITOOLS_CONFIG}: ${error?.message ?? error}`);
	}
	const configured = config?.["generator-cli"]?.version;
	if (configured !== GENERATOR_VERSION) {
		fail(
			`Generator version drift: openapitools.json pins ${configured}, ` +
				`verify-generator-jar.mjs pins ${GENERATOR_VERSION}.\n` +
				`Bump GENERATOR_VERSION, PINNED_SHA256, EXPECTED_SHA1 and EXPECTED_BYTES together as one deliberate change.`,
		);
	}
	const storageDir = config?.["generator-cli"]?.storageDir;
	if (typeof storageDir === "string" && storageDir.includes("${")) {
		// The wrapper expands env placeholders (${...}) in storageDir; this
		// script does not, so a placeholder would make the wrapper cache land
		// somewhere the eviction check never looks and the unverified jar
		// could win classpath precedence. Fail closed.
		fail(
			'generator-cli.storageDir contains a "${" env placeholder (' +
				storageDir +
				") — this script does not replicate the wrapper's placeholder expansion.\n" +
				"Remove the placeholder, or keep relying on the --custom-generator java -jar-style invocation, which bypasses the wrapper's storage jar entirely.",
		);
	}
	return storageDir
		? // Mirror the wrapper's expansion exactly: it string-replaces the FIRST
			// "~" ANYWHERE (`.replace("~", homedir())`), not just a leading one —
			// diverging here would make our cache-eviction check miss its jar.
			path.resolve(FRONTEND_DIR, String(storageDir).replace("~", homedir()))
		: WRAPPER_STORAGE_DEFAULT;
}

/**
 * Remove the wrapper's own cached jar for the pinned version: when it exists
 * alongside --custom-generator, the CLI puts it FIRST on the classpath, so an
 * unverified auto-download would win over our verified jar. Assert it is gone
 * afterwards to catch storage-dir drift or an undeletable file.
 */
function removeWrapperCachedJar(wrapperStorage) {
	const wrapperJar = path.join(wrapperStorage, `${GENERATOR_VERSION}.jar`);
	if (!existsSync(wrapperJar)) return;
	rmSync(wrapperJar);
	if (existsSync(wrapperJar)) {
		fail(
			`Wrapper's cached jar still present after removal: ${wrapperJar}\n` +
				`If generator-cli.storageDir moved the wrapper cache elsewhere, it would win classpath precedence over the verified jar — refusing to continue.`,
		);
	}
	log(`Removed wrapper's cached jar: ${wrapperJar}`);
}

/**
 * Exclusive-create a unique staging file in the cache dir (O_EXCL via the
 * "wx" flag): concurrent runs cannot share a staging file and a pre-planted
 * symlink at the path cannot be followed. Returns the path and the held fd —
 * the caller writes through the fd (never by reopening the path, which would
 * reopen the create→write symlink-swap window), fsyncs, closes, then renames.
 */
function createExclusiveStagingFile() {
	for (let attempt = 0; attempt < 5; attempt++) {
		const staging = `${CACHE_JAR}.${process.pid}.${randomBytes(6).toString("hex")}.download`;
		if (existsSync(staging)) continue;
		try {
			const fd = openSync(staging, "wx");
			return { path: staging, fd };
		} catch {
			// Lost a race for this name — try another.
		}
	}
	fail("Could not create a unique staging file in .generator-jar-cache/");
}

/**
 * Check the cached jar. Returns true when it is verified and usable; false
 * when the caller should fall through to a fresh verified download (missing,
 * symlinked, or failed verification — evicted here so the rename below
 * replaces whatever was at the path).
 */
function verifyCachedJar() {
	if (!existsSync(CACHE_JAR)) return false;
	if (lstatSync(CACHE_JAR).isSymbolicLink()) {
		log("Cached jar path is a symlink — evicting the link and re-downloading.");
		unlinkSync(CACHE_JAR);
		return false;
	}
	const result = verifyIntegrity(CACHE_JAR, readFileSync(CACHE_JAR));
	if (result.ok) return true;
	// Evict and fall through: a mismatching cache must not wedge codegen (CI
	// cache keys are immutable). The fresh download below re-verifies from
	// scratch and fails closed if upstream changed.
	log(`Cached jar failed verification — evicting and re-downloading.\n${result.message}`);
	unlinkSync(CACHE_JAR);
	return false;
}

/** Download the pinned artifact and verify it before it lands in the cache. */
async function downloadVerifiedJar() {
	log(`Downloading generator jar ${GENERATOR_VERSION} from ${DOWNLOAD_URL} ...`);
	let response;
	try {
		response = await fetch(DOWNLOAD_URL, { signal: AbortSignal.timeout(DOWNLOAD_TIMEOUT_MS) });
	} catch (error) {
		fail(`Download failed: ${error?.cause?.message ?? error?.message ?? error}`);
	}
	if (!response.ok) fail(`Download failed: HTTP ${response.status} for ${DOWNLOAD_URL}`);
	// Strict Content-Length: Maven Central serves static files with an exact
	// header, so a missing or different value means proxy/interception or a
	// non-artifact response — fail closed rather than trusting the body.
	const declared = response.headers.get("content-length");
	if (declared === null || Number(declared) !== EXPECTED_BYTES) {
		fail(
			`Refusing download: Content-Length ${declared ?? "(missing)"} does not equal the pinned artifact size ${EXPECTED_BYTES}.\n` +
				`Fail closed on any transfer whose declared size differs from the pinned artifact.`,
		);
	}
	const body = Buffer.from(await response.arrayBuffer());
	const result = verifyIntegrity("Downloaded generator jar", body);
	if (!result.ok) {
		fail(
			`${result.message}\n` +
				`Refusing to cache the artifact. The pinned checksums or the upstream jar may have changed — re-pin deliberately.`,
		);
	}
	mkdirSync(CACHE_DIR, { recursive: true });
	const staging = createExclusiveStagingFile();
	let renamed = false;
	try {
		// Write through the held fd, not by reopening the path: a symlink
		// swapped in after the exclusive create must not be followed.
		// writeFileSync accepts an fd and writes the whole buffer through it
		// (retrying short writes), so no partial-write state is reachable.
		writeFileSync(staging.fd, body);
		fsyncSync(staging.fd);
		closeSync(staging.fd);
		renameSync(staging.path, CACHE_JAR);
		renamed = true;
	} finally {
		if (!renamed) {
			// ENOSPC, signal death, rename failure — do not orphan the
			// random-suffixed staging file. The fd may already be closed on
			// some failure paths; closing again is harmless.
			try {
				closeSync(staging.fd);
			} catch {
				/* already closed */
			}
			if (existsSync(staging.path)) {
				try {
					unlinkSync(staging.path);
				} catch {
					/* best effort */
				}
			}
		}
	}
	// Post-rename re-verification: proves the bytes at the final path are the
	// pinned artifact (closes the short-write invariant gap) and re-checks the
	// path immediately before anything is allowed to execute it (closes the
	// rename→exec window).
	const finalCheck = verifyIntegrity(CACHE_JAR, readFileSync(CACHE_JAR));
	if (!finalCheck.ok) {
		fail(`${finalCheck.message}\nRefusing to hand an unverified jar to codegen.`);
	}
	log(`Cached verified generator jar at ${CACHE_JAR}`);
}

async function main() {
	const wrapperStorage = crossCheckWrapperConfig();
	removeWrapperCachedJar(wrapperStorage);

	const jarPathArgIndex = process.argv.indexOf("--jar-path");
	if (jarPathArgIndex !== -1) {
		const supplied = process.argv[jarPathArgIndex + 1];
		if (!supplied) fail("--jar-path requires a file argument");
		const resolved = path.resolve(supplied);
		const result = verifyIntegrity(resolved, readFileSync(resolved));
		if (!result.ok) fail(`${result.message}\nRefusing to proceed with an unverified jar.`);
		process.stdout.write(`${resolved}\n`);
		return;
	}

	if (!verifyCachedJar()) {
		await downloadVerifiedJar();
	}
	process.stdout.write(`${CACHE_JAR}\n`);
}

main().catch((error) => fail(error?.stack ?? String(error)));
