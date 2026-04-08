import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import Sidebar from './Sidebar.svelte';

// Mock $app/stores
vi.mock('$app/stores', () => ({
	page: {
		subscribe: vi.fn((fn) => {
			fn({ url: { pathname: '/workspace' } });
			return { unsubscribe: vi.fn() };
		}),
	},
}));

describe('Sidebar Component', () => {
	describe('Rendering', () => {
		it('renders all navigation items', () => {
			const { getByText } = render(Sidebar);
			expect(getByText('Dashboard')).toBeTruthy();
			expect(getByText('Campaigns')).toBeTruthy();
			expect(getByText('Jobs')).toBeTruthy();
			expect(getByText('Results')).toBeTruthy();
			expect(getByText('Settings')).toBeTruthy();
		});

		it('renders logo/branding', () => {
			const { getByText } = render(Sidebar);
			expect(getByText('Votecatcher')).toBeTruthy();
		});
	});

	describe('Active State', () => {
		it('highlights active nav item based on current path', () => {
			const { getByText } = render(Sidebar);
			const dashboardLink = getByText('Dashboard').closest('a');
			expect(dashboardLink?.classList.contains('bg-blue-50')).toBe(true);
		});
	});

	describe('Mobile Behavior', () => {
		it('shows hamburger menu button on mobile', () => {
			const { container } = render(Sidebar);
			const menuButton = container.querySelector('button[aria-label="Toggle menu"]');
			expect(menuButton).toBeTruthy();
		});

		it('toggles sidebar visibility on mobile', async () => {
			const { container } = render(Sidebar);
			const menuButton = container.querySelector('button[aria-label="Toggle menu"]');

			// Click to open
			await fireEvent.click(menuButton!);

			// Sidebar should be visible (check for transform class)
			const sidebar = container.querySelector('aside');
			expect(sidebar?.classList.contains('translate-x-0')).toBe(true);
		});
	});

	describe('Accessibility', () => {
		it('has proper nav landmark', () => {
			const { container } = render(Sidebar);
			const nav = container.querySelector('nav');
			expect(nav?.getAttribute('aria-label')).toBe('Workspace navigation');
		});
	});
});
