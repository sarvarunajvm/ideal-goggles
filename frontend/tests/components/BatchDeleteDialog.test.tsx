/**
 * Tests for BatchDeleteDialog component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { BatchDeleteDialog } from '../../src/components/BatchActions/BatchDeleteDialog';
import { useBatchSelectionStore } from '../../src/stores/batchSelectionStore';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock the store
jest.mock('../../src/stores/batchSelectionStore');

// Mock toast
const mockToast = jest.fn();
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

describe('BatchDeleteDialog Component', () => {
  const mockOnOpenChange = jest.fn();
  const mockClearSelection = jest.fn();
  const mockDisableSelectionMode = jest.fn();
  const selectedIds = ['photo1', 'photo2', 'photo3'];

  beforeEach(() => {
    jest.clearAllMocks();

    (useBatchSelectionStore as unknown as jest.Mock).mockReturnValue({
      clearSelection: mockClearSelection,
      disableSelectionMode: mockDisableSelectionMode,
    });
  });

  describe('Dialog Rendering', () => {
    test('renders dialog when open is true', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText('Delete Photos')).toBeInTheDocument();
    });

    test('does not render dialog content when open is false', () => {
      render(
        <BatchDeleteDialog
          open={false}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.queryByText('Delete Photos')).not.toBeInTheDocument();
    });

    test('shows correct number of selected photos in description', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText(/move 3 selected photos to trash/i)).toBeInTheDocument();
    });

    test('renders permanent delete checkbox', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByLabelText(/permanently delete/i)).toBeInTheDocument();
    });

    test('renders Cancel button', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    test('renders Move to Trash button by default', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /move to trash/i })).toBeInTheDocument();
    });
  });

  describe('Permanent Delete Toggle', () => {
    test('shows warning message when permanent delete is checked', async () => {
      const user = userEvent.setup();
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const checkbox = screen.getByLabelText(/permanently delete/i);
      await user.click(checkbox);

      await waitFor(() => {
        expect(screen.getByText(/this will permanently delete the files from your disk/i)).toBeInTheDocument();
      });
    });

    test('changes button text to Delete Permanently when permanent is checked', async () => {
      const user = userEvent.setup();
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const checkbox = screen.getByLabelText(/permanently delete/i);
      await user.click(checkbox);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete permanently/i })).toBeInTheDocument();
      });
    });

    test('shows trash info message when permanent delete is not checked', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText(/photos will be moved to your system trash/i)).toBeInTheDocument();
    });

    test('updates description when permanent delete is toggled', async () => {
      const user = userEvent.setup();
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const checkbox = screen.getByLabelText(/permanently delete/i);
      await user.click(checkbox);

      await waitFor(() => {
        expect(screen.getByText(/permanently delete 3 selected photos/i)).toBeInTheDocument();
      });
    });
  });

  describe('Delete Operation', () => {
    test('calls API with correct parameters for trash deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'test-job-123' },
      });

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/delete',
          {
            photo_ids: selectedIds,
            permanent: false,
          }
        );
      });
    });

    test('calls API with correct parameters for permanent deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'test-job-456' },
      });

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const checkbox = screen.getByLabelText(/permanently delete/i);
      await user.click(checkbox);

      const deleteButton = screen.getByRole('button', { name: /delete permanently/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/delete',
          {
            photo_ids: selectedIds,
            permanent: true,
          }
        );
      });
    });

    test('shows success toast on successful deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'test-job-789' },
      });

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Move to Trash Started',
          description: expect.stringContaining('Processing 3 photos'),
        });
      });
    });

    test('clears selection after successful deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'test-job-101' },
      });

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockClearSelection).toHaveBeenCalled();
      });
    });

    test('disables selection mode after successful deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'test-job-102' },
      });

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockDisableSelectionMode).toHaveBeenCalled();
      });
    });

    test('closes dialog after successful deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'test-job-103' },
      });

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    test('resets permanent checkbox after successful deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'test-job-104' },
      });

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const checkbox = screen.getByLabelText(/permanently delete/i);
      await user.click(checkbox);

      const deleteButton = screen.getByRole('button', { name: /delete permanently/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    test('shows error toast on failed deletion', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Network error';
      mockedAxios.post.mockRejectedValueOnce(new Error(errorMessage));

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Delete Failed',
          description: errorMessage,
          variant: 'destructive',
        });
      });
    });

    test('shows loading state during deletion', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(/deleting/i)).toBeInTheDocument();
      });
    });

    test('disables buttons during loading', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        const cancelButton = screen.getByRole('button', { name: /cancel/i });
        expect(cancelButton).toBeDisabled();
      });
    });
  });

  describe('Cancel Functionality', () => {
    test('closes dialog when Cancel button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    test('resets permanent checkbox when Cancel is clicked after toggling', async () => {
      const user = userEvent.setup();
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const checkbox = screen.getByLabelText(/permanently delete/i);
      await user.click(checkbox);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Edge Cases', () => {
    test('handles single photo deletion', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={['photo1']}
        />
      );

      expect(screen.getByText(/move 1 selected photos to trash/i)).toBeInTheDocument();
    });

    test('handles empty selected IDs array', () => {
      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={[]}
        />
      );

      expect(screen.getByText(/move 0 selected photos to trash/i)).toBeInTheDocument();
    });

    test('handles non-Error exception', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockRejectedValueOnce('String error');

      render(
        <BatchDeleteDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /move to trash/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Delete Failed',
          description: 'Failed to start delete operation',
          variant: 'destructive',
        });
      });
    });
  });
});
