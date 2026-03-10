import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import Modal from './Modal.svelte';

describe('Modal Component', () => {
	describe('Rendering', () => {
		it('renders when open is true', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});
			expect(getByRole('dialog')).toBeTruthy();
		});

		it('does not render when open is false', () => {
			const { queryByRole } = render(Modal, {
				props: {
					open: false,
					onClose: () => {}
				}
			});
			expect(queryByRole('dialog')).toBeNull();
		});

		it('renders with title', () => {
			const { getByText } = render(Modal, {
				props: {
					open: true,
					title: 'Confirm Action',
					onClose: () => {}
				}
			});
			expect(getByText('Confirm Action')).toBeTruthy();
		});

		it('renders content area for slotted content', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});
			const dialog = getByRole('dialog');
			const contentArea = dialog.querySelector('.p-4');
			expect(contentArea).toBeTruthy();
		});
	});

	describe('Size Variants', () => {
		it('renders with small size', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					size: 'sm',
					onClose: () => {}
				}
			});
			const dialog = getByRole('dialog');
			expect(dialog.classList.contains('max-w-sm')).toBe(true);
		});

		it('renders with medium size (default)', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});
			const dialog = getByRole('dialog');
			expect(dialog.classList.contains('max-w-md')).toBe(true);
		});

		it('renders with large size', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					size: 'lg',
					onClose: () => {}
				}
			});
			const dialog = getByRole('dialog');
			expect(dialog.classList.contains('max-w-lg')).toBe(true);
		});
	});

	describe('Close Button', () => {
		it('renders close button', () => {
			const { getByLabelText } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});
			expect(getByLabelText('Close modal')).toBeTruthy();
		});

		it('calls onClose when close button is clicked', async () => {
			const onClose = vi.fn();
			const { getByLabelText } = render(Modal, {
				props: {
					open: true,
					onClose
				}
			});

			const closeButton = getByLabelText('Close modal');
			await fireEvent.click(closeButton);

			expect(onClose).toHaveBeenCalledTimes(1);
		});
	});

	describe('Backdrop Click', () => {
		it('calls onClose when backdrop is clicked (default behavior)', async () => {
			const onClose = vi.fn();
			const { container } = render(Modal, {
				props: {
					open: true,
					onClose
				}
			});

			const backdrop = container.querySelector('.fixed.inset-0.z-50');
			if (backdrop) {
				await fireEvent.click(backdrop);
			}

			expect(onClose).toHaveBeenCalledTimes(1);
		});

		it('does not call onClose when backdrop click is disabled', async () => {
			const onClose = vi.fn();
			const { container } = render(Modal, {
				props: {
					open: true,
					closeOnBackdrop: false,
					onClose
				}
			});

			const backdrop = container.querySelector('.fixed.inset-0.z-50');
			if (backdrop) {
				await fireEvent.click(backdrop);
			}

			expect(onClose).not.toHaveBeenCalled();
		});
	});

	describe('Keyboard Navigation', () => {
		it('calls onClose when Escape key is pressed', async () => {
			const onClose = vi.fn();
			render(Modal, {
				props: {
					open: true,
					onClose
				}
			});

			await fireEvent.keyDown(document, { key: 'Escape' });

			expect(onClose).toHaveBeenCalled();
		});

		it('does not call onClose for other keys', async () => {
			const onClose = vi.fn();
			render(Modal, {
				props: {
					open: true,
					onClose
				}
			});

			await fireEvent.keyDown(document, { key: 'Enter' });
			await fireEvent.keyDown(document, { key: 'Tab' });

			expect(onClose).not.toHaveBeenCalled();
		});
	});

	describe('Accessibility', () => {
		it('has role="dialog"', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});
			expect(getByRole('dialog')).toBeTruthy();
		});

		it('has aria-modal="true"', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});
			const dialog = getByRole('dialog');
			expect(dialog.getAttribute('aria-modal')).toBe('true');
		});

		it('has aria-labelledby when title is provided', () => {
			const { getByRole } = render(Modal, {
				props: {
					open: true,
					title: 'Test Modal',
					onClose: () => {}
				}
			});
			const dialog = getByRole('dialog');
			expect(dialog.getAttribute('aria-labelledby')).toBeTruthy();
		});

		it('close button has accessible label', () => {
			const { getByLabelText } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});
			expect(getByLabelText('Close modal')).toBeTruthy();
		});
	});

	describe('Focus Management', () => {
		beforeEach(() => {
			document.body.innerHTML = '';
		});

		afterEach(() => {
			document.body.innerHTML = '';
		});

		it('has autofocus on close button when modal opens', async () => {
			const { getByLabelText } = render(Modal, {
				props: {
					open: true,
					onClose: () => {}
				}
			});

			await new Promise(resolve => setTimeout(resolve, 0));

			const closeButton = getByLabelText('Close modal');
			expect(document.activeElement).toBe(closeButton);
		});

		it('prevents Tab from escaping the modal', async () => {
			const onClose = vi.fn();
			const { getByLabelText } = render(Modal, {
				props: {
					open: true,
					onClose
				}
			});

			await new Promise(resolve => setTimeout(resolve, 0));

			const closeButton = getByLabelText('Close modal');
			closeButton.focus();

			await fireEvent.keyDown(closeButton, { key: 'Tab' });

			expect(document.activeElement).toBe(closeButton);
		});

		it('handles Shift+Tab to cycle backwards', async () => {
			const onClose = vi.fn();
			const { getByLabelText } = render(Modal, {
				props: {
					open: true,
					onClose
				}
			});

			await new Promise(resolve => setTimeout(resolve, 0));

			const closeButton = getByLabelText('Close modal');
			closeButton.focus();

			await fireEvent.keyDown(closeButton, { key: 'Tab', shiftKey: true });

			expect(document.activeElement).toBe(closeButton);
		});
	});
});
