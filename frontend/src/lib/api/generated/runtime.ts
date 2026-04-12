export interface ConfigurationParameters {
	basePath?: string;
	fetchApi?: typeof fetch;
	middleware?: Middleware[];
	queryParamsStringify?: (params: Record<string, unknown>) => string;
}

export class Configuration {
	basePath: string;
	fetchApi?: typeof fetch;
	middleware: Middleware[];
	queryParamsStringify: (params: Record<string, unknown>) => string;

	constructor(configuration: ConfigurationParameters = {}) {
		this.basePath = configuration.basePath || "http://localhost:8080/api";
		this.fetchApi = configuration.fetchApi;
		this.middleware = configuration.middleware || [];
		this.queryParamsStringify = configuration.queryParamsStringify || defaultQueryParamsStringify;
	}
}

interface Middleware {
	pre?: (context: RequestContext) => Promise<RequestContext>;
	post?: (context: ResponseContext) => Promise<ResponseContext>;
}

interface RequestContext {
	url: string;
	init: RequestInit;
}

interface ResponseContext {
	response: Response;
}

function defaultQueryParamsStringify(params: Record<string, unknown>): string {
	const searchParams = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== null && value !== undefined) {
			searchParams.set(key, String(value));
		}
	}
	return searchParams.toString();
}

export interface RequestOptions {
	headers?: Record<string, string>;
}

export async function request<T>(
	config: Configuration,
	method: string,
	url: string,
	body?: unknown,
	options?: RequestOptions,
): Promise<T> {
	const fetchApi = config.fetchApi || fetch;
	const fullUrl = `${config.basePath}${url}`;

	const init: RequestInit = {
		method,
		headers: {
			"Content-Type": "application/json",
			...options?.headers,
		},
	};

	if (body !== undefined) {
		init.body = JSON.stringify(body);
	}

	let context: RequestContext = { url: fullUrl, init };

	for (const mw of config.middleware) {
		if (mw.pre) {
			context = await mw.pre(context);
		}
	}

	const response = await fetchApi(context.url, context.init);

	if (!response.ok) {
		const errorBody = await response.text();
		throw new Error(errorBody || `HTTP ${response.status}`);
	}

	if (response.status === 204) {
		return undefined as T;
	}

	return response.json();
}

export async function requestBlob(
	config: Configuration,
	method: string,
	url: string,
	options?: RequestOptions,
): Promise<Blob> {
	const fetchApi = config.fetchApi || fetch;
	const fullUrl = `${config.basePath}${url}`;

	const init: RequestInit = {
		method,
		headers: {
			...options?.headers,
		},
	};

	const response = await fetchApi(fullUrl, init);

	if (!response.ok) {
		const errorBody = await response.text();
		throw new Error(errorBody || `HTTP ${response.status}`);
	}

	return response.blob();
}
