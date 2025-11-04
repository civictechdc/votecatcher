// Server-side upload endpoint (simulated). Keeps sensitive handling on server.
// Accepts multipart/form-data with "files" and "kind".
// Demo behavior when DEMO_MODE=true, otherwise returns minimal success response.

import type { RequestHandler } from '@sveltejs/kit';
import { json } from '@sveltejs/kit';
import { randomUUID } from 'crypto';
import type { UploadResult } from '$lib/workspace-types';

const SERVER_DEMO =
	(process.env.DEMO_MODE === '1' ||
		process.env.DEMO_MODE === 'true' ||
		(typeof process !== 'undefined' &&
			typeof (globalThis as any).__DEMO_MODE !== 'undefined' &&
			(globalThis as any).__DEMO_MODE)) ??
	false;

export const POST: RequestHandler = async ({ request }) => {
	// parse form data (SvelteKit request.formData available on server)
	const form = await request.formData();
	const kind = (form.get('kind') as string) ?? 'unknown';
	const files: { name: string; size: number; id: string }[] = [];

	for (const entry of form.entries()) {
		const [key, value] = entry;
		if (value instanceof File) {
			files.push({ name: value.name, size: value.size, id: randomUUID() });
			// NOTE: In production you'd stream the file to object storage (S3/Supabase) securely here.
		}
	}

	if (SERVER_DEMO) {
		// Simulate processing delay
		await new Promise((r) => setTimeout(r, 700 + Math.random() * 700));
		const resp: UploadResult = {
			success: true,
			message: `Demo upload accepted (${files.length})`,
			files
		};
		return json(resp, { status: 200 });
	}

	// Non-demo: still simulate short delay, but keep server-only op.
	await new Promise((r) => setTimeout(r, 400));
	const resp: UploadResult = { success: true, message: `Upload accepted (${files.length})`, files };
	return json(resp, { status: 200 });
};
