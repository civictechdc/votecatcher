import { writable } from 'svelte/store';
import { getApiClient } from './api-client';
import { JobsApi } from '$lib/api/generated';
import type { Job, CreateJob } from '$lib/api/generated';

interface SSEState {
	connected: boolean;
	reconnectAttempts: number;
	error: string | null;
}

interface JobsState {
	currentJob: Job | null;
	loading: boolean;
	error: string | null;
	sse: SSEState;
}

	function createJobsStore() {
		const { subscribe, set, update } = writable<JobsState>({
			currentJob: null,
			loading: false,
			error: null,
			sse: { connected: false, reconnectAttempts: 0, error: null }
		});

		let eventSource: EventSource | null = null;
		const maxRetries = 3;
		const baseRetryDelay = 1000;

		function handleSSEEvent(data: { event: string; data: any }) {
			switch (data.event) {
				case 'status_update':
					update((s) => ({
						...s,
						currentJob: { ...s.currentJob, ...data.data } as Job
					}));
					break;

				case 'matching_progress':
					update((s) => ({
						...s,
						currentJob: {
							...s.currentJob,
							progress: (data.data.processed / data.data.total) * 100
						} as Job
					}));
					break;

				case 'job_complete':
					update((s) => ({
						...s,
						currentJob: { ...s.currentJob, status: 'MATCHING_COMPLETED' } as Job
					}));
					break;

				case 'job_error':
					update((s) => ({
						...s,
						currentJob: { ...s.currentJob, status: data.data.status } as Job,
						sse: { ...s.sse, error: data.data.error }
					}));
					break;
			}
		}

	return {
		subscribe,

		async create(data: CreateJob) {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new JobsApi(client);
				const job = await api.createJob({ createJob: data });
				update((s) => ({ ...s, currentJob: job, loading: false }));
				return job;
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		async fetch(id: number) {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new JobsApi(client);
				const job = await api.getJob({ jobId: id });
				update((s) => ({ ...s, currentJob: job, loading: false }));
				return job;
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		async cancel(id: number) {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new JobsApi(client);
				const job = await api.cancelJob({ jobId: id });
				update((s) => ({ ...s, currentJob: job, loading: false }));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		connectToJob(jobId: string) {
			if (eventSource) {
				eventSource.close();
			}

			const baseUrl = import.meta.env.VITE_PUBLIC_API_URL || 'http://localhost:8000';
			eventSource = new EventSource(`${baseUrl}/api/jobs/${jobId}/status`);

			eventSource.onopen = () => {
				update((s) => ({
					...s,
					sse: { connected: true, reconnectAttempts: 0, error: null }
				}));
			};

			eventSource.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);
					handleSSEEvent(data);
				} catch (e) {
					console.error('Failed to parse SSE message:', e);
				}
			};

			eventSource.onerror = () => {
				update((s) => {
					const attempts = s.sse.reconnectAttempts + 1;

					if (attempts < maxRetries) {
						const delay = baseRetryDelay * Math.pow(2, attempts);
						setTimeout(() => this.connectToJob(jobId), delay);
						return { ...s, sse: { ...s.sse, reconnectAttempts: attempts } };
					} else {
						return {
							...s,
							sse: { connected: false, reconnectAttempts: attempts, error: 'Connection lost' }
						};
					}
				});
			};
		},

		disconnect() {
			if (eventSource) {
				eventSource.close();
				eventSource = null;
			}
			update((s) => ({ ...s, sse: { connected: false, reconnectAttempts: 0, error: null } }));
		},

		reset() {
			set({
				currentJob: null,
				loading: false,
				error: null,
				sse: { connected: false, reconnectAttempts: 0, error: null }
			});
		}
	};
}

export const jobs = createJobsStore();

export function resetJobsStore() {
	jobs.reset();
}
