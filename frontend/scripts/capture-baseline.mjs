#!/usr/bin/env bun
/**
 * Scripted baseline capture for the SvelteKit 3 migration (tasks 3.7/4.4
 * recaptures #2/#3). Adapted from the browser-MCP recipe in
 * `.agents/local/workspace/pre-kit3-baseline/README.md`: this script captures
 * BOTH sides (Kit 2 reference + Kit 3) with the same tooling and engine, so
 * only the upgrade differs.
 *
 * Usage (backend already running on :8080, ONE dev server on 5173 at a time):
 *   bun scripts/capture-baseline.mjs --out <dir> [--base-url http://localhost:5173] [--api-url http://localhost:8080]
 *
 * Outputs under `<dir>/`:
 *   chromium/<engine>-<route>.png   fullPage captures (deviceScaleFactor 2)
 *   firefox/<engine>-<route>.png    fullPage captures (deviceScaleFactor 1)
 *   capture-report.json             routes, console entries, failed API calls, timings
 *   non-blank-check.json            per-PNG blank guard (Pillow stdev when python3+PIL available)
 *
 * Engine notes (documented divergence, compare within engine only):
 *   - Chromium deviceScaleFactor 2 mirrors the original retina Chrome MCP captures;
 *     Firefox uses its default 1 (the Kit 2 Firefox reference did not scale).
 *   - Chrome fullPage pads short pages to viewport height; Firefox captures the
 *     raw document height. Never compare across engines.
 *
 * Seed is idempotent: campaigns are looked up fresh each run by name and the
 * 5-row voter CSV is uploaded to Alpha only when it has no voter list yet.
 */

import { chromium, firefox } from "playwright";
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

function arg(name, fallback) {
	const i = process.argv.indexOf(`--${name}`);
	return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const OUT = resolve(arg("out", "capture-out"));
const BASE_URL = arg("base-url", "http://localhost:5173");
const API_URL = arg("api-url", "http://localhost:8080");
const VIEWAREA = { width: 1280, height: 720 };

const CAMPAIGN_ALPHA = "Kit3 Baseline Alpha";
const CAMPAIGN_BETA = "Kit3 Baseline Beta";
const VOTER_CSV = [
	"First_Name,Last_Name,Street_Number,Street_Name",
	"Jane,Doe,101,Elm St",
	"John,Smith,202,Maple Ave",
	"Alice,Jones,303,Cedar Ln",
	"Bob,Brown,404,Birch Blvd",
	"Carol,White,505,Ash Ct",
].join("\n");

const log = (...m) => console.log(`[capture] ${new Date().toISOString()} ${m.join(" ")}`);

// ---------- seed (idempotent) ----------

async function api(path, init) {
	const res = await fetch(`${API_URL}${path}`, init);
	if (!res.ok) throw new Error(`API ${path} -> ${res.status}: ${await res.text()}`);
	return res.status === 204 ? null : res.json();
}

async function seed() {
	const { campaigns } = await api("/api/campaigns");
	// The API exposes campaigns as { uniqueName, title, ... } — no `name` key.
	const find = (name) => campaigns.find((c) => c.uniqueName === name);
	let alpha = find(CAMPAIGN_ALPHA);
	let beta = find(CAMPAIGN_BETA);
	if (!alpha)
		alpha = await api("/api/campaigns", {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify({ name: CAMPAIGN_ALPHA, year: 2024, region: "DC" }),
		});
	if (!beta)
		beta = await api("/api/campaigns", {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify({ name: CAMPAIGN_BETA, year: 2024, region: "DC" }),
		});
	log(`seed: alpha=${alpha.id} beta=${beta.id}`);

	// Upload the voter CSV to Alpha only if it has no voter data yet. The
	// metrics endpoint's voterListCount is the authoritative signal — a fresh
	// upload's scan record is NOT visible in /scans immediately, which made a
	// scans-based check re-upload every run (observed 119 vs 124 metric drift).
	const metrics = await api(`/api/campaigns/${alpha.id}/metrics`).catch(() => null);
	const hasVoters = !!metrics && (metrics.voterListCount ?? 0) > 0;
	if (!hasVoters) {
		const tmp = mkdtempSync(join(tmpdir(), "kit3-seed-"));
		const csvPath = join(tmp, "voters.csv");
		writeFileSync(csvPath, VOTER_CSV);
		const form = new FormData();
		form.set("campaign_id", alpha.id);
		form.set("file", new Blob([readFileSync(csvPath)], { type: "text/csv" }), "voters.csv");
		const res = await fetch(`${API_URL}/api/upload/voter-list`, { method: "POST", body: form });
		if (!res.ok) throw new Error(`voter-list upload -> ${res.status}: ${await res.text()}`);
		log(`seed: voter CSV uploaded to alpha (${res.status})`);
	} else {
		log("seed: alpha already has voter data, skipping upload");
	}
	return { alpha: alpha.id, beta: beta.id };
}

// ---------- capture ----------

async function captureEngine(engine, ids) {
	const browserType = engine === "chromium" ? chromium : firefox;
	const browser = await browserType.launch();
	const context = await browser.newContext({
		viewport: VIEWAREA,
		// Chromium ×2 mirrors the original retina Chrome MCP baseline; Firefox
		// baseline used its default 1. Same choice on both sides of the diff.
		deviceScaleFactor: engine === "chromium" ? 2 : 1,
	});
	const page = await context.newPage();

	const consoleEntries = [];
	const failedApi = [];
	let abortedSseNavigations = 0;
	page.on("console", (msg) => {
		const type = msg.type();
		if (type !== "error" && type !== "warning") return;
		const text = msg.text();
		if (text.includes("[vite]")) return; // dev-server connect noise
		// Navigating away tears down the SSE stream; Firefox reports this as a
		// console error ("interrupted" mid-stream or "can't establish" when the
		// connect races the fast re-navigation). Deterministic capture artifact
		// on both sides of the diff, not an app failure.
		if (
			text.includes("/events/campaigns") &&
			(text.includes("interrupted") || text.includes("establish a connection"))
		)
			return;
		consoleEntries.push({ type, text, route: page.url() });
	});
	page.on("pageerror", (err) =>
		consoleEntries.push({ type: "pageerror", text: String(err), route: page.url() }),
	);
	page.on("response", (res) => {
		if (!res.url().startsWith(API_URL)) return;
		if (res.status() >= 400) {
			failedApi.push({
				status: res.status(),
				url: res.url(),
				method: res.request().method(),
				route: page.url(),
			});
		}
	});
	page.on("requestfailed", (req) => {
		if (!req.url().startsWith(API_URL)) return;
		if (req.url().includes("/events/")) {
			abortedSseNavigations += 1;
			return;
		}
		failedApi.push({
			status: null,
			url: req.url(),
			method: req.method(),
			route: page.url(),
			failure: req.failure()?.errorText,
		});
	});

	const routes = [
		{ slug: "landing", path: "/" },
		{ slug: "workspace-campaigns", path: "/workspace" },
		{ slug: "campaign-alpha", path: `/workspace/${ids.alpha}` },
		{ slug: "campaign-alpha-upload", path: `/workspace/${ids.alpha}/upload` },
		{ slug: "campaign-alpha-jobs", path: `/workspace/${ids.alpha}/jobs` },
		{ slug: "campaign-alpha-results", path: `/workspace/${ids.alpha}/results` },
		{ slug: "campaign-beta", path: `/workspace/${ids.beta}` },
	];

	const outDir = join(OUT, engine);
	mkdirSync(outDir, { recursive: true });
	const shots = [];

	for (const { slug, path } of routes) {
		const started = Date.now();
		// Readiness: `load` + <main> visible + settle. The app opens an SSE
		// campaign-event stream, so `networkidle` never settles (each route
		// would burn its whole timeout) — the original recipe's fallback arm
		// (<main> + settle) is the operative readiness signal.
		await page.goto(`${BASE_URL}${path}`, { waitUntil: "load", timeout: 45000 });
		await page.waitForSelector("main", { timeout: 45000 });
		await page.waitForTimeout(1500);

		const file = join(outDir, `${engine}-${slug}.png`);
		await page.screenshot({ path: file, fullPage: true });
		shots.push({ engine, slug, path, file, ms: Date.now() - started });
		log(`${engine} ${slug}: ${shots.at(-1).ms}ms`);
	}

	await browser.close();
	return { engine, screenshots: shots, consoleEntries, failedApi, abortedSseNavigations };
}

// ---------- non-blank guard ----------

function pngDimensions(buf) {
	// PNG IHDR: width at offset 16, height at 20 (big-endian).
	return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

function nonBlankCheck(report) {
	const results = {};
	for (const shot of report.engines.flatMap((r) => r.screenshots)) {
		const buf = readFileSync(shot.file);
		const { width, height } = pngDimensions(buf);
		const entry = { bytes: buf.length, width, height, method: "png-size-sanity", blank: null };
		// Authoritative Pillow stdev/unique-level check when available.
		const probe = spawnSync("python3", [
			"-c",
			`
import sys
from PIL import Image, ImageStat
img = Image.open(sys.argv[1]).convert("L")
stat = ImageStat.Stat(img)
colors = img.getcolors(maxcolors=1 << 24)
print(f"{stat.stddev[0]:.4f} {0 if colors is None else len(colors)}")
`,
			shot.file,
		]);
		if (probe.status === 0) {
			const [stdev, colors] = probe.stdout.toString().trim().split(/\s+/).map(Number);
			Object.assign(entry, {
				method: "pillow-stdev",
				stdev,
				uniqueGrayLevels: colors,
				blank: stdev < 1.0 || colors < 2,
			});
		} else {
			// Size sanity: a rendered app page is never a few hundred bytes.
			entry.blank = buf.length < 10_000;
		}
		results[shot.file] = entry;
		if (entry.blank) log(`NON-BLANK GUARD FAILED: ${shot.file}`);
	}
	const method = Object.values(results)[0]?.method ?? "none";
	writeFileSync(join(OUT, "non-blank-check.json"), JSON.stringify({ method, results }, null, 2));
	log(
		`non-blank guard method: ${method}, all non-blank: ${Object.values(results).every((r) => !r.blank)}`,
	);
}

// ---------- main ----------

const t0 = Date.now();
mkdirSync(OUT, { recursive: true });
const ids = await seed();
const engines = [];
for (const engine of ["chromium", "firefox"]) {
	engines.push(await captureEngine(engine, ids));
}
const report = {
	capturedAt: new Date().toISOString(),
	baseUrl: BASE_URL,
	apiUrl: API_URL,
	ids,
	engines,
};
writeFileSync(join(OUT, "capture-report.json"), JSON.stringify(report, null, 2));
nonBlankCheck(report);
const total = report.engines.reduce((n, e) => n + e.consoleEntries.length, 0);
const failed = report.engines.reduce((n, e) => n + e.failedApi.length, 0);
log(
	`done in ${((Date.now() - t0) / 1000).toFixed(1)}s — console entries: ${total}, failed API calls: ${failed}`,
);
if (total > 0 || failed > 0) process.exitCode = 2;
