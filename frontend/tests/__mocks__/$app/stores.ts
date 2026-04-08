import { readable } from "svelte/store";

export const page = readable({
	url: new URL("http://localhost/workspace"),
	params: {},
	route: {},
	status: 200,
	error: null,
	data: {},
	state: {},
});

export const navigating = readable(null);
export const updated = readable(false);
export const goto = () => {};
export const invalidate = () => {};
export const invalidateAll = () => {};
export const prefetch = () => {};
export const prefetchRoutes = () => {};
export const beforeNavigate = () => {};
export const afterNavigate = () => {};
