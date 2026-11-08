#!/usr/bin/env node
/**
 * Minimal reverse proxy for the header-derived-origin prod smoke
 * (playwright.proxy-smoke.config.ts, task 4.2).
 *
 * Simulates the deployment shape documented for adapter-node 6: the app
 * runs with PROTOCOL_HEADER/HOST_HEADER pointing at the standard forwarded
 * headers, so SvelteKit derives every request's origin from
 * x-forwarded-proto/x-forwarded-host instead of the socket. This proxy is
 * the "reverse proxy" that sets them:
 *
 * - listens on PROXY_PORT (the public origin the browser and the backend
 *   dev CORS allowlist use),
 * - forwards to UPSTREAM_PORT (the adapter-node server),
 * - rewrites Host to the upstream host, so a passing CSRF/form check can
 *   only come from the x-forwarded-* headers (not a coincidental Host
 *   match),
 * - injects x-forwarded-proto + x-forwarded-host from PUBLIC_ORIGIN,
 * - streams both ways (SSE-safe; no body buffering).
 *
 * Usage: PROXY_PORT=5173 UPSTREAM_PORT=5174 node scripts/reverse-proxy.mjs
 */
import { createServer, request as httpRequest } from "node:http";

const PROXY_PORT = Number(process.env["PROXY_PORT"] ?? 5173);
const UPSTREAM_PORT = Number(process.env["UPSTREAM_PORT"] ?? 5174);
const PUBLIC_ORIGIN = process.env["PUBLIC_ORIGIN"] ?? `http://localhost:${PROXY_PORT}`;

const publicUrl = new URL(PUBLIC_ORIGIN);

const server = createServer((req, res) => {
	const upstream = httpRequest({
		host: "localhost",
		port: UPSTREAM_PORT,
		method: req.method,
		path: req.url,
		headers: {
			...req.headers,
			// rewrite Host to the upstream so origin derivation must come
			// from the forwarded headers below (see file docblock)
			host: `localhost:${UPSTREAM_PORT}`,
			"x-forwarded-proto": publicUrl.protocol.replace(":", ""),
			"x-forwarded-host": publicUrl.host,
		},
	});

	upstream.on("response", (upstreamRes) => {
		res.writeHead(upstreamRes.statusCode ?? 502, upstreamRes.headers);
		upstreamRes.pipe(res, { end: true });
	});

	upstream.on("error", (error) => {
		if (!res.headersSent) {
			res.writeHead(502, { "content-type": "text/plain" });
		}
		res.end(`reverse-proxy: upstream unavailable (${error.code ?? error.message})`);
	});

	req.pipe(upstream, { end: true });
});

server.listen(PROXY_PORT, () => {
	console.log(
		`[reverse-proxy] http://localhost:${PROXY_PORT} -> http://localhost:${UPSTREAM_PORT} ` +
			`(x-forwarded-host: ${publicUrl.host}, x-forwarded-proto: ${publicUrl.protocol.replace(":", "")})`,
	);
});
