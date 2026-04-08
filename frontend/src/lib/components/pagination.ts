export function getPageCount(totalItems: number, pageSize: number) {
	return Math.max(1, Math.ceil(totalItems / pageSize));
}

export function getVisibleRows<T>(rows: T[], page: number, pageSize: number) {
	const start = page * pageSize;
	return rows.slice(start, start + pageSize);
}
