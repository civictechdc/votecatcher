import { writable } from "svelte/store";
import { API_BASE_URL } from "$lib/api/base-url";

function toAbsoluteUrl(url: string): string {
	if (!url || url.startsWith("http")) return url;
	return `${API_BASE_URL}${url}`;
}

export interface CampaignMatchPrediction {
	rank: number;
	voterName: string;
	voterAddress: string;
	similarityScore: number;
	confidence: string;
}

export interface CampaignResultResponse {
	ocrResultId: number;
	extractedName: string;
	extractedAddress: string;
	cropId: number;
	jobId: number;
	thumbnailUrl: string;
	predictions: CampaignMatchPrediction[];
	cropCoordinates?: { top: number; bottom: number } | null;
	entryCoordinates?: { top: number; bottom: number } | null;
	pageNumber?: number | null;
	documentName?: string;
	scanId?: number | null;
}

interface CampaignResultsState {
	results: CampaignResultResponse[];
	total: number;
	page: number;
	pageSize: number;
	confidence?: string;
	loading: boolean;
	initialized: boolean;
	error: string | null;
}

interface FetchOptions {
	page?: number;
	pageSize?: number;
	confidence?: string;
}

function createCampaignResultsStore() {
	const { subscribe, set, update } = writable<CampaignResultsState>({
		results: [],
		total: 0,
		page: 1,
		pageSize: 50,
		confidence: undefined,
		loading: false,
		initialized: false,
		error: null,
	});

	return {
		subscribe,

		async fetchResults(campaignId: string, options: FetchOptions = {}) {
			const page = options.page ?? 1;
			const pageSize = options.pageSize ?? 50;
			const confidence = options.confidence;

			update((s) => ({
				...s,
				loading: true,
				error: null,
				page,
				pageSize,
				confidence,
			}));

			try {
				const params = new URLSearchParams({
					page: String(page),
					page_size: String(pageSize),
				});
				if (confidence) {
					params.append("confidence", confidence);
				}

				const response = await fetch(
					`${API_BASE_URL}/api/campaigns/${campaignId}/results?${params.toString()}`,
				);

				if (!response.ok) {
					throw new Error(`HTTP ${response.status}: ${response.statusText}`);
				}

				const data = await response.json();

				update((s) => ({
					...s,
					results: data.results,
					total: data.total,
					loading: false,
					initialized: true,
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : "Unknown error";
				update((s) => ({
					...s,
					loading: false,
					error: message,
				}));
			}
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		reset() {
			set({
				results: [],
				total: 0,
				page: 1,
				pageSize: 50,
				confidence: undefined,
				loading: false,
				initialized: false,
				error: null,
			});
		},
	};
}

export const campaignResults = createCampaignResultsStore();

export function escapeHtml(str: string): string {
	return str
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

export function resetCampaignResultsStore() {
	campaignResults.reset();
}

export function renderExpandedCropImage(
	thumbnailUrl: string,
	clipCoords?: { top: number; bottom: number } | null,
): string {
	if (!thumbnailUrl) return "";
	const absolute = toAbsoluteUrl(thumbnailUrl);
	const safe = escapeHtml(absolute);
	const clip = clipCoords
		? `clip-path:inset(${(clipCoords.top * 100).toFixed(2)}% 0 ${(100 - clipCoords.bottom * 100).toFixed(2)}% 0);`
		: "";
	return `<img src="${safe}" alt="Enlarged crop" data-crop-url="${safe}" class="cursor-pointer hover:opacity-80 transition-opacity" style="max-width:400px;max-height:300px;border-radius:0.5rem;object-fit:contain;${clip}" />`;
}

export function getConfidenceBadgeClass(confidence: string): string {
	switch (confidence) {
		case "HIGH":
			return "bg-green-100 text-green-800";
		case "MEDIUM":
			return "bg-yellow-100 text-yellow-800";
		case "LOW":
			return "bg-red-100 text-red-800";
		default:
			return "bg-gray-100 text-gray-800";
	}
}

export function renderPredictionsTable(predictions: CampaignMatchPrediction[]): string {
	if (predictions.length === 0) {
		return '<p class="text-sm text-gray-500 italic">No predictions available</p>';
	}

	const rows = predictions
		.slice(0, 5)
		.map((p) => {
			const badge = getConfidenceBadgeClass(p.confidence);
			const score = `${(p.similarityScore * 100).toFixed(1)}%`;
			const name = escapeHtml(p.voterName || "-");
			const address = escapeHtml(p.voterAddress || "-");
			return `<tr class="border-t border-gray-100">
			<td class="px-3 py-2 text-sm">${name}</td>
			<td class="px-3 py-2 text-sm">${address}</td>
			<td class="px-3 py-2 text-sm"><span class="px-2 py-0.5 rounded-full text-xs font-medium ${badge}">${p.confidence}</span></td>
			<td class="px-3 py-2 text-sm">${score}</td>
		</tr>`;
		})
		.join("");

	return `<table class="w-full text-left">
		<thead><tr class="text-xs text-gray-500 uppercase">
			<th class="px-3 py-1 font-medium">Name</th>
			<th class="px-3 py-1 font-medium">Address</th>
			<th class="px-3 py-1 font-medium">Confidence</th>
			<th class="px-3 py-1 font-medium">Score</th>
		</tr></thead>
		<tbody>${rows}</tbody>
	</table>`;
}

export function renderThumbnailCell(
	thumbnailUrl: string,
	clipCoords?: { top: number; bottom: number } | null,
): string {
	if (!thumbnailUrl) return '<span class="text-slate-400">—</span>';
	const safe = escapeHtml(toAbsoluteUrl(thumbnailUrl));
	const clip = clipCoords
		? `clip-path:inset(${(clipCoords.top * 100).toFixed(2)}% 0 ${(100 - clipCoords.bottom * 100).toFixed(2)}% 0);`
		: "";
	return `<img src="${safe}" loading="lazy" width="60" height="40" alt="Crop thumbnail" class="rounded object-cover" style="${clip}" />`;
}

export function getScanPageUrl(scanId: number, pageNumber: number): string {
	return `${API_BASE_URL}/api/scans/${scanId}/pages/${pageNumber}/image`;
}

export function toggleAccordion(currentExpanded: number | null, clickedId: number): number | null {
	return currentExpanded === clickedId ? null : clickedId;
}

export function sortResults(
	results: CampaignResultResponse[],
	config: { key: string; direction: "asc" | "desc" } | null,
): CampaignResultResponse[] {
	if (!config) return results;

	return [...results].sort((a, b) => {
		let aVal: string | number;
		let bVal: string | number;

		const topA = a.predictions[0];
		const topB = b.predictions[0];

		switch (config.key) {
			case "extracted_name":
				aVal = a.extractedName.toLowerCase();
				bVal = b.extractedName.toLowerCase();
				break;
			case "extracted_address":
				aVal = a.extractedAddress.toLowerCase();
				bVal = b.extractedAddress.toLowerCase();
				break;
			case "matched_name":
				aVal = (topA?.voterName ?? "").toLowerCase();
				bVal = (topB?.voterName ?? "").toLowerCase();
				break;
			case "matched_address":
				aVal = (topA?.voterAddress ?? "").toLowerCase();
				bVal = (topB?.voterAddress ?? "").toLowerCase();
				break;
			case "confidence":
				aVal = topA?.confidence ?? "";
				bVal = topB?.confidence ?? "";
				break;
			case "score":
				aVal = topA?.similarityScore ?? 0;
				bVal = topB?.similarityScore ?? 0;
				break;
			default:
				return 0;
		}

		if (aVal < bVal) return config.direction === "asc" ? -1 : 1;
		if (aVal > bVal) return config.direction === "asc" ? 1 : -1;
		return 0;
	});
}
