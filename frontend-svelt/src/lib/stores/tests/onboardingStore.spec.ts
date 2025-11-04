import { onboard, initialState } from '../onboarding';
import { get } from 'svelte/store';
import { describe, it, expect, beforeEach } from 'vitest';

describe('onboard store', () => {
	beforeEach(() => {
		onboard.reset();
	});

	it('initializes correctly', () => {
		const s = get(onboard);
		expect(s.currentStep).toBe(initialState.currentStep);
		expect(s.answers).toEqual({});
	});

	it('navigates steps', () => {
		onboard.next();
		expect(get(onboard).currentStep).toBe(1);
		onboard.back();
		expect(get(onboard).currentStep).toBe(0);
	});

	it('sets answers and uploaded file', () => {
		onboard.setAnswer('campaign_name', 'Team X');
		expect(get(onboard).answers.campaign_name).toBe('Team X');
		const file = new File(['a'], 'test.csv', { type: 'text/csv' });
		onboard.setUploadedFile(file);
		expect(get(onboard).uploadedFile?.name).toBe('test.csv');
	});
});
