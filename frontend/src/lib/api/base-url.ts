export const API_BASE_URL = (import.meta.env["PUBLIC_API_URL"] ?? "http://localhost:8080")
	.toString()
	.replace(/\/$/, "");
