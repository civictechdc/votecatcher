// Centralized store for onboarding state.
// This keeps state testable and modular. Components subscribe to this store.

import { writable } from 'svelte/store';
import type { OcrProvider } from '../../types/ocr';
export type OnboardAnswers = {
	selectedOcrProvider?: OcrProvider | null;
	ocrProviderApiKey?: string;
	campaign_name?: string;
	campaign_year?: string;
	campaign_description?: string;
	campaign_id?: string | null;
	registration_data?: string;
};

export const initialState = {
	currentStep: 0,
	answers: {} as OnboardAnswers,
	uploadedFile: null as File | null,
	loading: false,
};

function createOnboardStore() {
	const { subscribe, update, set } = writable({ ...initialState });

	return {
		subscribe,
		reset: () => set({ ...initialState }),
		setLoading: (val: boolean) => update((s) => ({ ...s, loading: val })),
		next: () => update((s) => ({ ...s, currentStep: Math.min(s.currentStep + 1, 2) })),
		back: () => update((s) => ({ ...s, currentStep: Math.max(s.currentStep - 1, 0) })),
		setAnswer: (field: keyof OnboardAnswers, value: string | OcrProvider | null) =>
			update((s) => ({ ...s, answers: { ...s.answers, [field]: value } })),
		setUploadedFile: (file: File | null) => update((s) => ({ ...s, uploadedFile: file })),
		setCampaignId: (id: string) =>
			update((s) => ({ ...s, answers: { ...s.answers, campaign_id: id } })),
	};
}

export const onboard = createOnboardStore();
