import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { events } from "./events";

interface MockEventSourceInstance {
	close: ReturnType<typeof vi.fn>;
	onopen: ((this: EventSource, ev: Event) => void) | null;
	onmessage: ((this: EventSource, ev: MessageEvent) => void) | null;
	onerror: ((this: EventSource, ev: Event) => void) | null;
}

describe("Events Store — setup:updated", () => {
	const originalEventSource = globalThis.EventSource;
	let instances: MockEventSourceInstance[] = [];

	function mockEventSource(): void {
		instances = [];

		class MockES {
			close = vi.fn();
			onopen: ((this: EventSource, ev: Event) => void) | null = null;
			onmessage: ((this: EventSource, ev: MessageEvent) => void) | null = null;
			onerror: ((this: EventSource, ev: Event) => void) | null = null;
			static readonly CONNECTING = 0;
			static readonly OPEN = 1;
			static readonly CLOSED = 2;
			readonly CONNECTING = 0;
			readonly OPEN = 1;
			readonly CLOSED = 2;
			readyState = 0;

			constructor(_url: string | URL) {
				instances.push(this as unknown as MockEventSourceInstance);
			}
		}

		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		globalThis.EventSource = MockES as any;
	}

	beforeEach(() => {
		vi.useFakeTimers();
		instances = [];
	});

	afterEach(() => {
		events.reset();
		vi.useRealTimers();
		globalThis.EventSource = originalEventSource;
	});

	it("dispatches votecatcher:setup:updated DOM event on setup:updated SSE event", () => {
		mockEventSource();
		const handler = vi.fn();
		document.addEventListener("votecatcher:setup:updated", handler);

		events.connect("campaign-123");
		instances[0]!.onopen!.call({} as EventSource, {} as Event);

		const setupEventPayload = {
			event_id: "evt-1",
			event_type: "setup:updated",
			timestamp: new Date().toISOString(),
			trace_id: null,
			source: "routers.upload_router",
			campaign_id: "campaign-123",
			job_id: null,
			upload_type: "voter_list",
		};

		instances[0]!.onmessage!.call({} as EventSource, {
			data: JSON.stringify(setupEventPayload),
		} as MessageEvent);

		expect(handler).toHaveBeenCalledTimes(1);
		const customEvent = handler.mock.calls[0]![0] as CustomEvent;
		expect(customEvent.detail.upload_type).toBe("voter_list");
		expect(customEvent.detail.campaign_id).toBe("campaign-123");

		document.removeEventListener("votecatcher:setup:updated", handler);
	});

	it("dispatches setup:updated with upload_type=petition", () => {
		mockEventSource();
		const handler = vi.fn();
		document.addEventListener("votecatcher:setup:updated", handler);

		events.connect("campaign-456");
		instances[0]!.onopen!.call({} as EventSource, {} as Event);

		const setupEventPayload = {
			event_id: "evt-2",
			event_type: "setup:updated",
			timestamp: new Date().toISOString(),
			trace_id: null,
			source: "routers.upload_router",
			campaign_id: "campaign-456",
			job_id: null,
			upload_type: "petition",
		};

		instances[0]!.onmessage!.call({} as EventSource, {
			data: JSON.stringify(setupEventPayload),
		} as MessageEvent);

		expect(handler).toHaveBeenCalledTimes(1);
		const customEvent = handler.mock.calls[0]![0] as CustomEvent;
		expect(customEvent.detail.upload_type).toBe("petition");

		document.removeEventListener("votecatcher:setup:updated", handler);
	});

	it("rejects setup:updated with invalid shape", () => {
		mockEventSource();
		const handler = vi.fn();
		document.addEventListener("votecatcher:setup:updated", handler);

		events.connect("campaign-123");
		instances[0]!.onopen!.call({} as EventSource, {} as Event);

		instances[0]!.onmessage!.call({} as EventSource, {
			data: JSON.stringify({ event_type: "setup:updated" }),
		} as MessageEvent);

		expect(handler).not.toHaveBeenCalled();

		document.removeEventListener("votecatcher:setup:updated", handler);
	});
});
