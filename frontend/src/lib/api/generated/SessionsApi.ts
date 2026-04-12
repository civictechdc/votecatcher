import { Configuration, request } from "./runtime";
import type { SessionResponse } from "./models/Session";

export class SessionsApi {
	private config: Configuration;

	constructor(config: Configuration) {
		this.config = config;
	}

	async saveSessionSessionsPost(params: {
		name: string;
		data?: unknown;
	}): Promise<SessionResponse> {
		return request<SessionResponse>(this.config, "POST", "/sessions", params);
	}

	async loadSessionSessionsSessionIdLoadPost(params: {
		sessionId: number;
	}): Promise<SessionResponse> {
		return request<SessionResponse>(this.config, "POST", `/sessions/${params.sessionId}/load`);
	}
}
