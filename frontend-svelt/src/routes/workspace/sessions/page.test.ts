import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Page from './+page.svelte';
import { sessions } from '$lib/stores/sessions';
import type { Session } from '$lib/stores/sessions';

vi.mock('$lib/stores/sessions');

describe('Sessions Page', () => {
	const mockSessions: Session[] = [
		{
			id: 1,
			name: 'Session 1',
			campaign_id: null,
			session_type: 'REAL' as const,
			snapshot_data: {},
			created_at: '2024-01-01T00:00:00',
			updated_at: '2024-01-01T00:00:00'
		},
		{
			id: 2,
			name: 'Demo Session',
			campaign_id: 'camp-1',
			session_type: 'DEMO' as const,
			snapshot_data: { job_ids: [1, 2] },
			created_at: '2024-01-02T00:00:00',
			updated_at: '2024-01-02T00:00:00'
		}
	];

	beforeEach(() => {
		vi.clearAllMocks();
		vi.mocked(sessions.subscribe).mockImplementation((fn: any) => {
			fn({
				sessions: mockSessions,
				currentSession: null,
				loading: false,
				saving: false,
				error: null
			});
			return () => {};
		});
	});

	it('displays page title', () => {
		render(Page);
		expect(screen.getByText('Sessions')).toBeInTheDocument();
	});

	it('lists saved sessions', () => {
		render(Page);
		expect(screen.getByText('Session 1')).toBeInTheDocument();
		expect(screen.getByText('Demo Session')).toBeInTheDocument();
	});

	it('shows session type badges', () => {
		render(Page);
		expect(screen.getByText('REAL')).toBeInTheDocument();
		expect(screen.getByText('DEMO')).toBeInTheDocument();
	});

	it('has save session button', () => {
		render(Page);
		expect(screen.getByRole('button', { name: /save.*session/i })).toBeInTheDocument();
	});

	it('shows export button for each session', () => {
		render(Page);
		const exportButtons = screen.getAllByRole('button', { name: /export/i });
		expect(exportButtons.length).toBe(2);
	});

	it('shows load button for each session', () => {
		render(Page);
		const loadButtons = screen.getAllByRole('button', { name: /load/i });
		expect(loadButtons.length).toBe(2);
	});

	it('shows delete button for each session', () => {
		render(Page);
		const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
		expect(deleteButtons.length).toBe(2);
	});

	it('opens save modal when save button clicked', async () => {
		render(Page);
		const saveButton = screen.getByRole('button', { name: /save.*session/i });
		await fireEvent.click(saveButton);
		expect(screen.getByLabelText(/session name/i)).toBeInTheDocument();
	});

	it('calls save when form submitted', async () => {
		vi.mocked(sessions.save).mockResolvedValue(mockSessions[0]);

		render(Page);
		const saveButton = screen.getByRole('button', { name: /save.*session/i });
		await fireEvent.click(saveButton);

		const nameInput = screen.getByLabelText(/session name/i);
		await fireEvent.input(nameInput, { target: { value: 'New Session' } });

		const submitButton = screen.getByRole('button', { name: /^save$/i });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(sessions.save).toHaveBeenCalledWith('New Session', {});
		});
	});

	it('calls load when load button clicked', async () => {
		vi.mocked(sessions.load).mockResolvedValue(mockSessions[0]);

		render(Page);
		const loadButtons = screen.getAllByRole('button', { name: /load/i });
		await fireEvent.click(loadButtons[0]);

		await waitFor(() => {
			expect(sessions.load).toHaveBeenCalledWith(1);
		});
	});

	it('calls export when export button clicked', async () => {
		vi.mocked(sessions.export).mockResolvedValue(undefined);

		render(Page);
		const exportButtons = screen.getAllByRole('button', { name: /export/i });
		await fireEvent.click(exportButtons[0]);

		await waitFor(() => {
			expect(sessions.export).toHaveBeenCalledWith(1);
		});
	});

	it('calls delete when delete button clicked with confirmation', async () => {
		vi.mocked(sessions.delete).mockResolvedValue(undefined);

		vi.spyOn(window, 'confirm').mockReturnValue(true);

		render(Page);
		const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
		await fireEvent.click(deleteButtons[0]);

		await waitFor(() => {
			expect(sessions.delete).toHaveBeenCalledWith(1);
		});
	});

	it('does not delete if confirmation cancelled', async () => {
		vi.spyOn(window, 'confirm').mockReturnValue(false);

		render(Page);
		const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
		await fireEvent.click(deleteButtons[0]);

		expect(sessions.delete).not.toHaveBeenCalled();
	});
});
