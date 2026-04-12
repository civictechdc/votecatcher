import type { Actions, PageServerLoad } from "./$types";
import { redirect } from "@sveltejs/kit";

/**
 * Steps shown in the onboarding flow. Returned by the server so the UI remains declarative.
 * Keep this here so other server logic (e.g., translations, feature flags) can modify steps centrally.
 */
const steps = [
	{
		id: "provider",
		title: "Choose AI provider",
		description: "Select a provider and paste your API key for signature validation.",
	},
	{
		id: "campaign",
		title: "Campaign details",
		description: "Name your campaign and choose the election year.",
	},
	{
		id: "upload",
		title: "Upload registration data",
		description: "Upload a voter registration file (CSV/Excel/JSON).",
	},
];

/** Generate a short range of election years centered around the current year. */
function generateYears(): string[] {
	const currentYear = new Date().getFullYear();
	const years: string[] = [];
	for (let i = currentYear + 2; i >= currentYear - 2; i--) {
		years.push(String(i));
	}
	return years;
}

/**
 * Server-side load: verify session and return page data.
 * Uses relative fetch to the mocked /api/session route. Replace with real auth endpoint later.
 */
export const load: PageServerLoad = async ({ fetch }) => {
	const res = await fetch("/api/session");
	if (!res.ok) {
		// Not authenticated: redirect to auth page. Use 303 to prevent accidental POST resubmission.
		throw redirect(303, "/auth");
	}
	const json = await res.json();
	return {
		user: json.user ?? null,
		steps,
		years: generateYears(),
	};
};

/**
 * Actions: server-side handlers that proxy (for now) to your API routes.
 * These are provided so you can adopt progressive enhancement with forms or call them from client code via fetch to this route.
 * Each action returns a JSON-like result; adapt to your FastAPI backend when ready.
 */
export const actions: Actions = {
	storeApiKey: async ({ request, fetch }) => {
		const form = await request.formData();
		const provider = form.get("provider") as string | null;
		const apiKey = form.get("apiKey") as string | null;
		if (!provider || !apiKey) {
			return { status: 400, body: { error: "Missing provider or apiKey" } };
		}
		const res = await fetch("/api/store-ocr-provider", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ provider, apiKey }),
		});
		const payload = await res.json().catch(() => ({ error: "Invalid response" }));
		if (!res.ok) return { status: res.status, body: payload };
		return { status: 200, body: payload };
	},

	createCampaign: async ({ request, fetch }) => {
		const form = await request.formData();
		const name = form.get("name") as string | null;
		const year = form.get("year") as string | null;
		const description = form.get("description") as string | null;
		if (!name || !year) return { status: 400, body: { error: "Missing name or year" } };
		const res = await fetch("/api/create-campaign", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ name, year: Number(year), description }),
		});
		const payload = await res.json().catch(() => ({ error: "Invalid response" }));
		if (!res.ok) return { status: res.status, body: payload };
		return { status: 200, body: payload };
	},

	uploadFileMeta: async ({ request, fetch }) => {
		const form = await request.formData();
		const fileName = form.get("fileName") as string | null;
		const size = form.get("size") as string | null;
		const campaignId = form.get("campaignId") as string | null;
		if (!fileName || !size) return { status: 400, body: { error: "Missing file metadata" } };
		const res = await fetch("/api/upload-file", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ fileName, size: Number(size), campaignId }),
		});
		const payload = await res.json().catch(() => ({ error: "Invalid response" }));
		if (!res.ok) return { status: res.status, body: payload };
		return { status: 200, body: payload };
	},

	processVoterFile: async ({ request, fetch }) => {
		const form = await request.formData();
		const filePath = form.get("filePath") as string | null;
		const campaignId = form.get("campaignId") as string | null;
		if (!filePath) return { status: 400, body: { error: "Missing filePath" } };
		const res = await fetch("/api/process-voter-file", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ filePath, campaignId }),
		});
		const payload = await res.json().catch(() => ({ error: "Invalid response" }));
		if (!res.ok) return { status: res.status, body: payload };
		return { status: 200, body: payload };
	},
};
