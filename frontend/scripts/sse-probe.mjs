#!/usr/bin/env bun
/**
 * SSE-connectivity probe for baseline recaptures (task 3.7 / 4.4 evidence).
 *
 * Complements capture-baseline.mjs (which records console errors/failed APIs
 * but not info-level logs): this probe visits the 7 baseline routes in BOTH
 * engines and records which routes emit the `[SSE] Connected to campaign
 * event stream` console marker. Campaign views (dashboard/upload/jobs/results
 * for a real campaign id) are expected to connect; landing + campaigns list
 * are recorded for completeness.
 *
 * Usage (backend on :8080, dev server on :5173):
 *   bun sse-probe.mjs --campaign-id <alpha-id> [--beta-id <id>] \
 *     [--base-url http://localhost:5173]
 *
 * Exits non-zero if a campaign route fails to show the marker in either engine.
 */
import { chromium, firefox } from "playwright";

function arg(name, fallback) {
	const i = process.argv.indexOf(`--${name}`);
	return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const BASE_URL = arg("base-url", "http://localhost:5173");
const ALPHA = arg("campaign-id", "");
const BETA = arg("beta-id", ALPHA);

if (!ALPHA) {
	console.error("--campaign-id is required (look it up via GET /api/campaigns)");
	process.exit(1);
}

const routes = [
	{ slug: "landing", path: "/", expectSse: false },
	{ slug: "workspace-campaigns", path: "/workspace/campaigns", expectSse: false },
	{ slug: "campaign-alpha", path: `/workspace/${ALPHA}`, expectSse: true },
	{ slug: "campaign-alpha-upload", path: `/workspace/${ALPHA}/upload`, expectSse: true },
	{ slug: "campaign-alpha-jobs", path: `/workspace/${ALPHA}/jobs`, expectSse: true },
	{ slug: "campaign-alpha-results", path: `/workspace/${ALPHA}/results`, expectSse: true },
	{ slug: "campaign-beta", path: `/workspace/${BETA}`, expectSse: true },
];

const report = { capturedAt: new Date().toISOString(), baseUrl: BASE_URL, engines: [] };
let failed = 0;

for (const engine of ["chromium", "firefox"]) {
	const browserType = engine === "chromium" ? chromium : firefox;
	const browser = await browserType.launch();
	const page = await (
		await browser.newContext({ viewport: { width: 1280, height: 720 } })
	).newPage();
	const rows = [];
	for (const { slug, path, expectSse } of routes) {
		let sse = false;
		page.removeAllListeners("console");
		page.on("console", (msg) => {
			if (msg.text().includes("[SSE] Connected")) sse = true;
		});
		const navTimeout = engine === "firefox" ? 90000 : 45000;
		await page.goto(`${BASE_URL}${path}`, { waitUntil: "load", timeout: navTimeout });
		await page.waitForSelector("main", { timeout: navTimeout });
		// Firefox dev-mode hydration + SSE connect is slow (pre-kit3-baseline
		// README gotcha #2: 10-70s per navigation) — poll the marker with an
		// engine-aware budget.
		const budgetMs = engine === "firefox" ? 75000 : 12000;
		const deadline = Date.now() + budgetMs;
		while (!sse && Date.now() < deadline) {
			await page.waitForTimeout(500);
		}
		rows.push({ engine, slug, path, sseConnected: sse, expected: expectSse });
		console.log(
			`[sse-probe] ${engine} ${slug}: ${sse ? "SSE connected" : "no SSE"}${expectSse ? "" : " (not expected)"}`,
		);
		if (expectSse && !sse) failed += 1;
	}
	report.engines.push({ engine, rows });
	await browser.close();
}

console.log(JSON.stringify(report, null, 2));
process.exit(failed > 0 ? 2 : 0);
