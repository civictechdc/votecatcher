import { writable } from "svelte/store";
import { PUBLIC_API_URL } from "$env/static/public";

export type EventType = "job:status_changed" | "job:progress" | "metrics:updated" | "setup:updated";

export interface BaseEvent {
	event_id: string;
	event_type: EventType;
	timestamp: string;
	trace_id: string | null;
	source: string | null;
	campaign_id: string | null;
	job_id: number | null;
}

export interface JobStatusEvent extends BaseEvent {
	event_type: "job:status_changed";
	status: string;
	previous_status: string | null;
}

export interface JobProgressEvent extends BaseEvent {
	event_type: "job:progress";
	processed: number;
	total: number;
	percentage: number;
}

export interface MetricsUpdatedEvent extends BaseEvent {
	event_type: "metrics:updated";
	total_signatures: number;
	processed: number;
	high_confidence: number;
}

export interface SetupUpdatedEvent extends BaseEvent {
	event_type: "setup:updated";
	upload_type: string;
}

export type AppEvent = JobStatusEvent | JobProgressEvent | MetricsUpdatedEvent | SetupUpdatedEvent;

function isValidEvent(data: unknown): data is AppEvent {
	if (typeof data !== "object" || data === null) return false;
	const evt = data as Record<string, unknown>;
	if (typeof evt["event_type"] !== "string") return false;
	if (typeof evt["event_id"] !== "string") return false;
	const validTypes: EventType[] = ["job:status_changed", "job:progress", "metrics:updated", "setup:updated"];
	return validTypes.includes(evt["event_type"] as EventType);
}

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

interface EventStoreState {
	status: ConnectionStatus;
	lastEvent: AppEvent | null;
	reconnectAttempts: number;
}

function createEventStore() {
	let eventSource: EventSource | null = null;
	let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
	let currentCampaignId: string | null = null;

	const MAX_RECONNECT_ATTEMPTS = 5;
	const BASE_DELAY = 1000;

	const { subscribe, set, update } = writable<EventStoreState>({
		status: "disconnected",
		lastEvent: null,
		reconnectAttempts: 0,
	});

	function handleEvent(event: AppEvent) {
		update((s) => ({ ...s, lastEvent: event }));

		switch (event.event_type) {
			case "job:status_changed":
				document.dispatchEvent(new CustomEvent("votecatcher:job:status", { detail: event }));
				break;
			case "job:progress":
				document.dispatchEvent(new CustomEvent("votecatcher:job:progress", { detail: event }));
				break;
			case "metrics:updated":
				document.dispatchEvent(new CustomEvent("votecatcher:metrics:updated", { detail: event }));
				break;
			case "setup:updated":
				document.dispatchEvent(new CustomEvent("votecatcher:setup:updated", { detail: event }));
				break;
		}
	}

	function doConnect(campaignId: string, isReconnect: boolean = false) {
		if (eventSource) {
			eventSource.close();
		}
		if (reconnectTimeout) {
			clearTimeout(reconnectTimeout);
			reconnectTimeout = null;
		}

		currentCampaignId = campaignId;
		update((s) => ({
			status: "connecting",
			lastEvent: null,
			reconnectAttempts: isReconnect ? s.reconnectAttempts : 0,
		}));

		const baseUrl = PUBLIC_API_URL || "http://localhost:8080";
		const url = `${baseUrl}/events/campaigns/${campaignId}/stream`;

		eventSource = new EventSource(url);

		eventSource.onopen = () => {
			console.debug("[SSE] Connected to campaign event stream");
			set({ status: "connected", lastEvent: null, reconnectAttempts: 0 });
		};

		eventSource.onerror = () => {
			console.debug("[SSE] Connection error, attempting reconnect");
			if (eventSource) {
				eventSource.close();
				eventSource = null;
			}
			update((s) => {
				if (s.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
					return { ...s, status: "error" as ConnectionStatus };
				}

				const delay = BASE_DELAY * Math.pow(2, s.reconnectAttempts);

				reconnectTimeout = setTimeout(() => {
					if (currentCampaignId) {
						doConnect(currentCampaignId, true);
					}
				}, delay);

				return { ...s, status: "error", reconnectAttempts: s.reconnectAttempts + 1 };
			});
		};

		eventSource.onmessage = (event) => {
			if (!event.data || event.data === "") {
				console.debug("[SSE] Heartbeat received");
				return;
			}
			try {
				const data = JSON.parse(event.data);
				if (!isValidEvent(data)) {
					console.error("[SSE] Invalid event shape:", data);
					return;
				}
				handleEvent(data);
			} catch (e) {
				console.error("[SSE] Failed to parse event:", e);
			}
		};
	}

	return {
		subscribe,

		connect(campaignId: string) {
			doConnect(campaignId);
		},

		disconnect() {
			if (reconnectTimeout) {
				clearTimeout(reconnectTimeout);
				reconnectTimeout = null;
			}
			if (eventSource) {
				eventSource.close();
				eventSource = null;
			}
			currentCampaignId = null;
			set({ status: "disconnected", lastEvent: null, reconnectAttempts: 0 });
		},

		reset() {
			this.disconnect();
		},
	};
}

export const events = createEventStore();
