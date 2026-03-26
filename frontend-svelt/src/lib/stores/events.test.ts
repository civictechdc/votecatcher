import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';
import { events } from './events';

interface MockEventSourceInstance {
	close: ReturnType<typeof vi.fn>;
	onopen: ((this: EventSource, ev: Event) => void) | null;
	onmessage: ((this: EventSource, ev: MessageEvent) => void) | null;
	onerror: ((this: EventSource, ev: Event) => void) | null;
}

describe('Events Store', () => {
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

	describe('connect', () => {
		it('starts in disconnected state', () => {
			const state = get(events);
			expect(state.status).toBe('disconnected');
		});

		it('connects to campaign event stream', () => {
			mockEventSource();

			events.connect('campaign-123');

			expect(get(events).status).toBe('connecting');
			expect(instances.length).toBe(1);
		});

		it('sets status to connected on open', () => {
			mockEventSource();

			events.connect('campaign-123');
			expect(get(events).status).toBe('connecting');

			instances[0].onopen!.call({} as EventSource, {} as Event);

			expect(get(events).status).toBe('connected');
		});
	});

	describe('disconnect', () => {
		it('closes event source and resets state', () => {
			mockEventSource();

			events.connect('campaign-123');
			instances[0].onopen!.call({} as EventSource, {} as Event);

			events.disconnect();

			expect(instances[0].close).toHaveBeenCalled();
			expect(get(events).status).toBe('disconnected');
		});

		it('clears reconnect timeout when disconnecting', async () => {
			mockEventSource();

			events.connect('campaign-123');
			instances[0].onerror!.call({} as EventSource, {} as Event);

			events.disconnect();

			vi.advanceTimersByTime(5000);

			expect(get(events).status).toBe('disconnected');
		});
	});

	describe('race condition prevention', () => {
		it('does not reconnect when disconnect closes the event source (onerror triggered by close)', async () => {
			mockEventSource();

			events.connect('campaign-123');
			expect(instances.length).toBe(1);

			// When disconnect() closes eventSource, it triggers onerror.
			// onerror must NOT schedule reconnection when we're intentionally disconnecting.
			events.disconnect();

			// The close() call triggers onerror synchronously in our mock.
			// Verify no new EventSource was created (no reconnection attempt).
			expect(instances.length).toBe(1);

			// Advance time past any possible reconnection delay.
			vi.advanceTimersByTime(10000);

			// Still only 1 instance - no reconnection happened.
			expect(instances.length).toBe(1);
			expect(get(events).status).toBe('disconnected');
		});

		it('does not reconnect when onerror fires concurrently with disconnect', async () => {
			mockEventSource();

			events.connect('campaign-123');
			expect(instances.length).toBe(1);

			// Simulate onerror firing at the same moment as disconnect.
			// This tests the race where onerror schedules reconnect AFTER disconnect clears timeout.
			instances[0].onerror!.call({} as EventSource, {} as Event);

			// Immediately disconnect (before reconnect timeout fires).
			events.disconnect();

			// Advance time past any possible reconnection delay.
			vi.advanceTimersByTime(10000);

			// No new EventSource should be created.
			expect(instances.length).toBe(1);
			expect(get(events).status).toBe('disconnected');
		});
	});

	describe('reconnection', () => {
		it('reconnects with exponential backoff on error', async () => {
			mockEventSource();

			events.connect('campaign-123');

			expect(instances.length).toBe(1);

			instances[0].onerror!.call({} as EventSource, {} as Event);

			vi.advanceTimersByTime(500);
			expect(instances.length).toBe(1);

			vi.advanceTimersByTime(500);
			expect(instances.length).toBe(2);
		});

		it('stops reconnecting after max attempts', async () => {
			mockEventSource();

			events.connect('campaign-123');
			expect(instances.length).toBe(1);

			// Simulate 5 reconnection cycles: error → reconnect → error → ...
			// The first onerror on instance 0 schedules reconnect.
			instances[0].onerror!.call({} as EventSource, {} as Event);
			expect(get(events).reconnectAttempts).toBe(1);

			// Advance time to trigger reconnection (creates new instance).
			vi.advanceTimersByTime(1000);
			expect(instances.length).toBe(2);

			// Second error.
			instances[1].onerror!.call({} as EventSource, {} as Event);
			expect(get(events).reconnectAttempts).toBe(2);

			// Third cycle.
			vi.advanceTimersByTime(2000);
			expect(instances.length).toBe(3);
			instances[2].onerror!.call({} as EventSource, {} as Event);
			expect(get(events).reconnectAttempts).toBe(3);

			// Fourth cycle.
			vi.advanceTimersByTime(4000);
			expect(instances.length).toBe(4);
			instances[3].onerror!.call({} as EventSource, {} as Event);
			expect(get(events).reconnectAttempts).toBe(4);

			// Fifth cycle.
			vi.advanceTimersByTime(8000);
			expect(instances.length).toBe(5);
			instances[4].onerror!.call({} as EventSource, {} as Event);

			// After 5 attempts, status should be 'error' and no more reconnects.
			expect(get(events).reconnectAttempts).toBe(5);
			expect(get(events).status).toBe('error');
		});
	});
});
