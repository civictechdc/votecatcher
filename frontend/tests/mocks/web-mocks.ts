export function baseUrl(path: string): URL {
	return new URL(path, 'https://testserver.com/');
}

export function baseUrlString(path: string): string {
	return baseUrl(path).href;
}
