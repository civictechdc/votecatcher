import { vi } from "vitest";
import { JSDOM } from "jsdom";
import { readable } from "svelte/store";

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
	PUBLIC_DEMO_MODE: "",
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

import { mount, unmount } from "svelte";
import Button from "$lib/components/ui/Button.svelte";
import { Menu, Download } from "lucide-svelte";
import MenuIcon from "lucide-svelte/icons/menu";
import XIcon from "lucide-svelte/icons/x";
import ChevronDownIcon from "lucide-svelte/icons/chevron-down";
import FolderOpenIcon from "lucide-svelte/icons/folder-open";
import SettingsIcon from "lucide-svelte/icons/settings";
import RefreshCwIcon from "lucide-svelte/icons/refresh-cw";
import Table from "$lib/components/ui/Table.svelte";
import LoadingSpinner from "$lib/components/ui/LoadingSpinner.svelte";

function warmup(Component: any, props: Record<string, unknown> = {}) {
	try {
		const target = document.createElement("div");
		document.body.appendChild(target);
		const c = mount(Component, { target, props });
		unmount(c);
		target.remove();
	} catch {}
}

warmup(Button, { text: "warmup" });
warmup(Menu, { class: "h-4 w-4" });
warmup(Download, { class: "h-4 w-4" });
warmup(MenuIcon, { class: "h-6 w-6" });
warmup(XIcon, { class: "h-6 w-6" });
warmup(ChevronDownIcon, { class: "h-4 w-4" });
warmup(FolderOpenIcon, { class: "h-5 w-5" });
warmup(SettingsIcon, { class: "h-5 w-5" });
warmup(RefreshCwIcon, { class: "h-4 w-4" });
warmup(LoadingSpinner, { size: "sm" });
warmup(Table, {
	props: {
		columns: [{ key: "id", label: "ID", sortable: true }],
		rows: [{ id: 1 }],
		sortable: true,
		onSortChange: () => {},
	},
});
warmup(Table, {
	props: {
		columns: [{ key: "id", label: "ID" }],
		rows: [],
		emptyMessage: "empty",
		sortable: true,
		onSortChange: () => {},
	},
});
