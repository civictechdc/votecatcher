// Server-side upload endpoint (simulated). Keeps sensitive handling on server.
// Accepts multipart/form-data with "files" and "kind".
// Demo behavior when DEMO_MODE=true, otherwise returns minimal success response.

import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";
import { randomUUID } from "crypto";
import { api, type ApiResult } from "$lib/api/client";
import { env } from "$env/dynamic/private";

const SERVER_DEMO = (env["DEMO_MODE"] ?? "false") === "true";

function getErrorMessage(result: ApiResult<unknown>): string {
	return !result.ok ? result.error : "Unknown error";
}

async function uploadPetitions(formData: FormData) {
	const petitions = formData.getAll("petition");
	if (petitions.length === 0) {
		return new Response(
			JSON.stringify({
				detail: `File to upload is null.`,
			}),
			{ status: 500 },
		);
	}

	if (SERVER_DEMO) {
		const fd = new FormData();
		petitions.forEach((file) => {
			fd.append("files", file);
		});

		console.log(`Petition file lists: ${fd.getAll("files").length}`);
		const response = await api.demoUploadPetitions(fd);

		console.log(`File upload response status: ${response.ok}}`);

		if (response.ok) {
			return json(response, { status: 200 });
		} else {
			return new Response(
				JSON.stringify({
					detail: `Server error: ${getErrorMessage(response)}`,
				}),
				{ status: 500 },
			);
		}
	}
	//TODO Add real endpoint call in else

	return new Response(
		JSON.stringify({
			detail: `Client server error uploading ${petitions.length} petitions.`,
		}),
		{ status: 500 },
	);
}

async function uploadVoterList(formData: FormData) {
	if (SERVER_DEMO) {
		const response = await api.demoUploadVoters(formData);

		console.log(`File upload response status: ${response.ok}}`);

		if (response.ok) {
			return json(response, { status: 200 });
		} else {
			return new Response(
				JSON.stringify({
					detail: `Server error: ${getErrorMessage(response)}`,
				}),
				{ status: 500 },
			);
		}
	}

	//TODO Add real endpoint call in else

	return new Response(
		JSON.stringify({
			detail: `Client server error uploading ${formData.getAll("file")}}.`,
		}),
		{ status: 500 },
	);
}

export const POST: RequestHandler = async ({ request }) => {
	// parse form data (SvelteKit request.formData available on server)
	const form = await request.formData();
	const files: { name: string; size: number; id: string }[] = [];
	for (const entry of form.entries()) {
		const [_key, value] = entry;
		if (value instanceof File) {
			files.push({ name: value.name, size: value.size, id: randomUUID() });
			// NOTE: In production you'd stream the file to object storage (S3/Supabase) securely here.
		}
	}

	await new Promise((r) => setTimeout(r, 400));

	console.log(`Get all petitions: ${form.getAll("petition").length}`);

	if (form.getAll("petition").length > 0) {
		return await uploadPetitions(form);
	} else {
		return await uploadVoterList(form);
	}
};
