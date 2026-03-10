import { writable } from 'svelte/store';
import { getApiClient } from './api-client';
import { JobsApi } from '$lib/api/generated';
import type { Job, CreateJob } from '$lib/api/generated';

interface JobsState {
	currentJob: Job | null;
	loading: boolean;
	error: string | null;
}

function createJobsStore() {
	const { subscribe, set, update } = writable<JobsState>({
		currentJob: null,
		loading: false,
		error: null
	});

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

		reset() {
			set({ currentJob: null, loading: false, error: null });
		}
	};
}

export const jobs = createJobsStore();

export function resetJobsStore() {
	jobs.reset();
}
