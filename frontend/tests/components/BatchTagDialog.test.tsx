/**
 * Tests for BatchTagDialog component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { BatchTagDialog } from '../../src/components/BatchActions/BatchTagDialog';
import { useBatchSelectionStore } from '../../src/stores/batchSelectionStore';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock the store
jest.mock('../../src/stores/batchSelectionStore');

// Mock toast
const mockToast = jest.fn();
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

describe('BatchTagDialog Component', () => {
  const mockOnOpenChange = jest.fn();
  const mockClearSelection = jest.fn();
  const selectedIds = ['photo1', 'photo2', 'photo3'];

  beforeEach(() => {
    jest.clearAllMocks();

    (useBatchSelectionStore as unknown as jest.Mock).mockReturnValue({
      clearSelection: mockClearSelection,
    });
  });

  describe('Dialog Rendering', () => {
    test('renders dialog when open is true', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText('Tag Photos')).toBeInTheDocument();
    });

    test('does not render dialog content when open is false', () => {
      render(
        <BatchTagDialog
          open={false}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.queryByText('Tag Photos')).not.toBeInTheDocument();
    });

    test('shows correct number of selected photos in description for add operation', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText(/add tags to 3 selected photos/i)).toBeInTheDocument();
    });

    test('renders operation selector', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByLabelText(/operation/i)).toBeInTheDocument();
    });

    test('renders tag input field', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByLabelText(/tags/i)).toBeInTheDocument();
    });

    test('renders add tag button', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const buttons = screen.getAllByRole('button');
      const addButton = buttons.find(btn => btn.querySelector('svg'));
      expect(addButton).toBeInTheDocument();
    });

    test('renders Cancel button', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    test('renders Apply Tags button', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /apply tags/i })).toBeInTheDocument();
    });
  });

  describe('Operation Selection', () => {
    test('operation select button is present', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /operation/i })).toBeInTheDocument();
    });

    test('allows opening operation dropdown', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const operationSelect = screen.getByRole('button', { name: /operation/i });
      await user.click(operationSelect);

      expect(await screen.findByText('Add tags (keep existing)')).toBeInTheDocument();
      expect(screen.getByText('Remove tags')).toBeInTheDocument();
      expect(screen.getByText('Replace all tags')).toBeInTheDocument();
    });

    test('updates description when operation changes to remove', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const operationSelect = screen.getByRole('button', { name: /operation/i });
      await user.click(operationSelect);

      const removeOption = await screen.findByText('Remove tags');
      await user.click(removeOption);

      await waitFor(() => {
        expect(screen.getByText(/remove tags from 3 selected photos/i)).toBeInTheDocument();
      });
    });

    test('updates description when operation changes to replace', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const operationSelect = screen.getByRole('button', { name: /operation/i });
      await user.click(operationSelect);

      const replaceOption = await screen.findByText('Replace all tags');
      await user.click(replaceOption);

      await waitFor(() => {
        expect(screen.getByText(/replace all tags on 3 selected photos/i)).toBeInTheDocument();
      });
    });
  });

  describe('Tag Input and Management', () => {
    test('allows entering tag text', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'vacation');

      expect(tagInput).toHaveValue('vacation');
    });

    test('adds tag when Enter key is pressed', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'vacation{Enter}');

      expect(screen.getByText('vacation')).toBeInTheDocument();
      expect(tagInput).toHaveValue('');
    });

    test('adds tag when add button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'landscape');

      const buttons = screen.getAllByRole('button');
      const addButton = buttons.find(btn => btn.querySelector('svg') && !btn.disabled);

      if (addButton) {
        await user.click(addButton);
      }

      expect(screen.getByText('landscape')).toBeInTheDocument();
      expect(tagInput).toHaveValue('');
    });

    test('trims whitespace from tags', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, '  nature  {Enter}');

      expect(screen.getByText('nature')).toBeInTheDocument();
    });

    test('does not add empty tag', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, '   {Enter}');

      expect(screen.queryByText(/selected tags/i)).not.toBeInTheDocument();
    });

    test('does not add duplicate tags', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'summer{Enter}');
      await user.type(tagInput, 'summer{Enter}');

      const tags = screen.getAllByText('summer');
      expect(tags).toHaveLength(1);
    });

    test('can add multiple different tags', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'vacation{Enter}');
      await user.type(tagInput, 'beach{Enter}');
      await user.type(tagInput, 'sunset{Enter}');

      expect(screen.getByText('vacation')).toBeInTheDocument();
      expect(screen.getByText('beach')).toBeInTheDocument();
      expect(screen.getByText('sunset')).toBeInTheDocument();
    });

    test('shows tag count', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'tag1{Enter}');
      await user.type(tagInput, 'tag2{Enter}');
      await user.type(tagInput, 'tag3{Enter}');

      expect(screen.getByText(/selected tags \(3\)/i)).toBeInTheDocument();
    });

    test('can remove tag by clicking X button', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'removeMe{Enter}');

      expect(screen.getByText('removeMe')).toBeInTheDocument();

      const removeButtons = screen.getAllByRole('button');
      const removeTagButton = removeButtons.find(btn =>
        btn.querySelector('svg') && btn.className.includes('hover:bg-destructive')
      );

      if (removeTagButton) {
        await user.click(removeTagButton);
      }

      await waitFor(() => {
        expect(screen.queryByText('removeMe')).not.toBeInTheDocument();
      });
    });

    test('disables add button when input is empty', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const buttons = screen.getAllByRole('button');
      const addButton = buttons.find(btn => btn.querySelector('svg') && !btn.textContent?.includes('Cancel'));

      expect(addButton).toBeDisabled();
    });

    test('enables add button when input has text', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test');

      const buttons = screen.getAllByRole('button');
      const addButton = buttons.find(btn => btn.querySelector('svg') && !btn.textContent?.includes('Cancel'));

      expect(addButton).not.toBeDisabled();
    });

    test('does not show tag list when no tags added', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.queryByText(/selected tags/i)).not.toBeInTheDocument();
    });

    test('shows tag list when tags are added', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'family{Enter}');

      expect(screen.getByText(/selected tags/i)).toBeInTheDocument();
    });
  });

  describe('Tag Operation', () => {
    test('prevents applying when no tags are added', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      expect(applyButton).toBeDisabled();
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    test('disables Apply Tags button when no tags are added', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      expect(applyButton).toBeDisabled();
    });

    test('enables Apply Tags button when tags are added', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      expect(applyButton).not.toBeDisabled();
    });

    test('calls API with correct parameters for add operation', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'tag-job-123' },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'vacation{Enter}');
      await user.type(tagInput, 'beach{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/tag',
          {
            photo_ids: selectedIds,
            tags: ['vacation', 'beach'],
            operation: 'add',
          }
        );
      });
    });

    test('calls API with correct parameters for remove operation', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'tag-job-456' },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const operationSelect = screen.getByRole('button', { name: /operation/i });
      await user.click(operationSelect);
      const removeOption = await screen.findByText('Remove tags');
      await user.click(removeOption);

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'old-tag{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/tag',
          {
            photo_ids: selectedIds,
            tags: ['old-tag'],
            operation: 'remove',
          }
        );
      });
    });

    test('calls API with correct parameters for replace operation', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'tag-job-789' },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const operationSelect = screen.getByRole('button', { name: /operation/i });
      await user.click(operationSelect);
      const replaceOption = await screen.findByText('Replace all tags');
      await user.click(replaceOption);

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'new-tag{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/tag',
          {
            photo_ids: selectedIds,
            tags: ['new-tag'],
            operation: 'replace',
          }
        );
      });
    });

    test('shows success toast on successful tagging', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'tag-job-success' },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Tagging Started',
          description: expect.stringContaining('Processing 3 photos'),
        });
      });
    });

    test('includes job ID in success toast', async () => {
      const user = userEvent.setup();
      const jobId = 'test-tag-job-xyz';
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: jobId },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Tagging Started',
          description: expect.stringContaining(jobId),
        });
      });
    });

    test('clears selection after successful tagging', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'tag-job-clear' },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockClearSelection).toHaveBeenCalled();
      });
    });

    test('closes dialog after successful tagging', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'tag-job-close' },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    test('resets form fields after successful tagging', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'tag-job-reset' },
      });

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    test('shows error toast on failed tagging', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Tagging failed: database error';
      mockedAxios.post.mockRejectedValueOnce(new Error(errorMessage));

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Tagging Failed',
          description: errorMessage,
          variant: 'destructive',
        });
      });
    });

    test('handles non-Error exception', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockRejectedValueOnce('String error');

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Tagging Failed',
          description: 'Failed to start tagging operation',
          variant: 'destructive',
        });
      });
    });

    test('shows loading state during tagging', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(screen.getByText(/processing/i)).toBeInTheDocument();
      });
    });

    test('disables buttons during loading', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const applyButton = screen.getByRole('button', { name: /apply tags/i });
      await user.click(applyButton);

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
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    test('resets tags when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      expect(screen.getByText('test')).toBeInTheDocument();

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    test('resets input value when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'partial');

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    test('resets operation when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const operationSelect = screen.getByRole('button', { name: /operation/i });
      await user.click(operationSelect);
      const removeOption = await screen.findByText('Remove tags');
      await user.click(removeOption);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    test('does not call API when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockedAxios.post).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    test('handles single photo tagging', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={['photo1']}
        />
      );

      expect(screen.getByText(/add tags to 1 selected photos/i)).toBeInTheDocument();
    });

    test('handles empty selected IDs array', () => {
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={[]}
        />
      );

      expect(screen.getByText(/add tags to 0 selected photos/i)).toBeInTheDocument();
    });

    test('handles large number of selected photos', () => {
      const manyIds = Array.from({ length: 100 }, (_, i) => `photo${i}`);
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={manyIds}
        />
      );

      expect(screen.getByText(/add tags to 100 selected photos/i)).toBeInTheDocument();
    });

    test('handles tags with special characters', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'tag-with-dashes{Enter}');
      await user.type(tagInput, 'tag_with_underscores{Enter}');
      await user.type(tagInput, 'tag.with.dots{Enter}');

      expect(screen.getByText('tag-with-dashes')).toBeInTheDocument();
      expect(screen.getByText('tag_with_underscores')).toBeInTheDocument();
      expect(screen.getByText('tag.with.dots')).toBeInTheDocument();
    });

    test('handles long tag names', async () => {
      const user = userEvent.setup();
      const longTag = 'a'.repeat(100);
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, `${longTag}{Enter}`);

      expect(screen.getByText(longTag)).toBeInTheDocument();
    });

    test('handles many tags', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);

      for (let i = 0; i < 10; i++) {
        await user.type(tagInput, `tag${i}{Enter}`);
      }

      expect(screen.getByText(/selected tags \(10\)/i)).toBeInTheDocument();
    });

    test('prevents Enter from submitting form in tag input', async () => {
      const user = userEvent.setup();
      render(
        <BatchTagDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const tagInput = screen.getByPlaceholderText(/enter a tag and press enter/i);
      await user.type(tagInput, 'test{Enter}');

      // Should add tag but not submit form
      expect(screen.getByText('test')).toBeInTheDocument();
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });
  });
});
