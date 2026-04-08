import { vi } from "vitest";
import { JSDOM } from "jsdom";
import { readable } from "svelte/store";

// Set up jsdom environment
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
	url: "http://localhost",
	pretendToBeVisual: true,
});

globalThis.document = dom.window.document;
globalThis.window = dom.window as unknown as Window & typeof globalThis;
globalThis.navigator = dom.window.navigator;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.Event = dom.window.Event;
globalThis.MessageEvent = dom.window.MessageEvent;

// Stub localStorage for jsdom
const localStorageMock = (() => {
	let store: Record<string, string> = {};
	return {
		getItem: (key: string) => store[key] || null,
		setItem: (key: string, value: string) => {
			store[key] = value;
		},
		removeItem: (key: string) => {
			delete store[key];
		},
		clear: () => {
			store = {};
		},
		get length() {
			return Object.keys(store).length;
		},
		key: (i: number) => Object.keys(store)[i] || null,
	};
})();
vi.stubGlobal("localStorage", localStorageMock);

vi.mock("$app/environment", () => ({
	browser: false,
	dev: true,
	prerendering: false,
	SSR: true,
}));

vi.mock("$env/static/public", () => ({
	PUBLIC_API_URL: "http://localhost:8000",
}));

vi.mock("$app/stores", () => {
	return {
		page: readable({
			url: new URL("http://localhost"),
			params: {},
			route: {},
			status: 200,
			error: null,
			data: {},
			state: {},
		}),
		navigating: readable(null),
		updated: readable(false),
		goto: vi.fn(),
		invalidate: vi.fn(),
		invalidateAll: vi.fn(),
		prefetch: vi.fn(),
		prefetchRoutes: vi.fn(),
		beforeNavigate: vi.fn(),
		afterNavigate: vi.fn(),
	};
});
