/**
 * Integration-style test: render the page component, simulate moving through steps.
 * Requires @testing-library/svelte and vitest to be configured.
 */
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import Page from '../+page.svelte';
import { describe, it, expect } from 'vitest';

describe('Getting started flow', () => {
	it('renders and goes through steps', async () => {
		const { getByText, getByLabelText, queryByText } = render(Page);

		// Step 1: provider
		expect(getByText('Choose AI provider')).toBeTruthy();
		const providerSelect = getByLabelText('AI Provider') as HTMLSelectElement;
		await fireEvent.change(providerSelect, { target: { value: 'OPENAI_API_KEY' } });
		const apiInput = getByLabelText('API Key') as HTMLInputElement;
		await fireEvent.input(apiInput, { target: { value: 'sk-testing' } });

		const next = getByText('Next');
		await fireEvent.click(next);

		// Step 2: campaign
		await waitFor(() => expect(getByText('Campaign details')).toBeTruthy());
		const nameInput = getByLabelText('Campaign Name') as HTMLInputElement;
		await fireEvent.input(nameInput, { target: { value: 'Test Campaign' } });

		const yearSelect = getByLabelText('Election Year') as HTMLSelectElement;
		await fireEvent.change(yearSelect, { target: { value: String(new Date().getFullYear()) } });

		await fireEvent.click(getByText('Next'));

		// Step 3: upload
		await waitFor(() => expect(getByText('Upload registration data')).toBeTruthy());
		// Simulate file selection using file input
		const file = new File(['a'], 'voters.csv', { type: 'text/csv' });
		const input = document.querySelector('input[type="file"]') as HTMLInputElement;
		await fireEvent.change(input, { target: { files: [file] } });

		// Complete button
		await fireEvent.click(getByText('Complete'));

		// After completion the page triggers a redirect (location change) in our code.
		// We assert that no validation errors are present.
		expect(queryByText('Missing')).toBeNull();
	});
});
