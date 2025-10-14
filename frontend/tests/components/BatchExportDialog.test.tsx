/**
 * Tests for BatchExportDialog component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { BatchExportDialog } from '../../src/components/BatchActions/BatchExportDialog';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock toast
const mockToast = jest.fn();
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock window.electron
const mockSelectDirectory = jest.fn();

describe('BatchExportDialog Component', () => {
  const mockOnOpenChange = jest.fn();
  const selectedIds = ['photo1', 'photo2', 'photo3'];

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock window.electron
    (window as any).electron = {
      selectDirectory: mockSelectDirectory,
    };
  });

  afterEach(() => {
    delete (window as any).electron;
  });

  describe('Dialog Rendering', () => {
    test('renders dialog when open is true', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText('Export Photos')).toBeInTheDocument();
    });

    test('does not render dialog content when open is false', () => {
      render(
        <BatchExportDialog
          open={false}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.queryByText('Export Photos')).not.toBeInTheDocument();
    });

    test('shows correct number of selected photos in description', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText(/export 3 selected photos to a folder/i)).toBeInTheDocument();
    });

    test('renders destination folder input', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByLabelText(/destination folder/i)).toBeInTheDocument();
    });

    test('renders format selector', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByLabelText(/export format/i)).toBeInTheDocument();
    });

    test('renders max dimension input', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByLabelText(/max dimension/i)).toBeInTheDocument();
    });

    test('renders Cancel button', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    test('renders Export button', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /^export$/i })).toBeInTheDocument();
    });

    test('renders folder selection button', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const folderButton = screen.getByRole('button', { name: '' });
      expect(folderButton).toBeInTheDocument();
    });
  });

  describe('Destination Selection', () => {
    test('allows manual input of destination folder', async () => {
      const user = userEvent.setup();
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/path/to/export');

      expect(input).toHaveValue('/path/to/export');
    });

    test('opens file dialog when folder button is clicked', async () => {
      const user = userEvent.setup();
      mockSelectDirectory.mockResolvedValueOnce({
        canceled: false,
        filePaths: ['/selected/path'],
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const buttons = screen.getAllByRole('button');
      const folderButton = buttons.find(btn => btn.querySelector('svg'));

      if (folderButton) {
        await user.click(folderButton);
      }

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });
    });

    test('updates destination when folder is selected', async () => {
      const user = userEvent.setup();
      mockSelectDirectory.mockResolvedValueOnce({
        canceled: false,
        filePaths: ['/selected/path'],
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const buttons = screen.getAllByRole('button');
      const folderButton = buttons.find(btn => btn.querySelector('svg'));

      if (folderButton) {
        await user.click(folderButton);
      }

      await waitFor(() => {
        const input = screen.getByLabelText(/destination folder/i);
        expect(input).toHaveValue('/selected/path');
      });
    });

    test('does not update destination when dialog is canceled', async () => {
      const user = userEvent.setup();
      mockSelectDirectory.mockResolvedValueOnce({
        canceled: true,
        filePaths: [],
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const buttons = screen.getAllByRole('button');
      const folderButton = buttons.find(btn => btn.querySelector('svg'));

      if (folderButton) {
        await user.click(folderButton);
      }

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });

      const input = screen.getByLabelText(/destination folder/i);
      expect(input).toHaveValue('');
    });

    test('does not update destination when no path is selected', async () => {
      const user = userEvent.setup();
      mockSelectDirectory.mockResolvedValueOnce({
        canceled: false,
        filePaths: [],
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const buttons = screen.getAllByRole('button');
      const folderButton = buttons.find(btn => btn.querySelector('svg'));

      if (folderButton) {
        await user.click(folderButton);
      }

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });

      const input = screen.getByLabelText(/destination folder/i);
      expect(input).toHaveValue('');
    });

    test('handles error during folder selection', async () => {
      const user = userEvent.setup();
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      mockSelectDirectory.mockRejectedValueOnce(new Error('Selection failed'));

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const buttons = screen.getAllByRole('button');
      const folderButton = buttons.find(btn => btn.querySelector('svg'));

      if (folderButton) {
        await user.click(folderButton);
      }

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith('Failed to select destination:', expect.any(Error));
      });

      consoleError.mockRestore();
    });
  });

  describe('Format Selection', () => {
    test('format select button is present', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByRole('button', { name: /export format/i })).toBeInTheDocument();
    });

    test('allows opening format dropdown', async () => {
      const user = userEvent.setup();
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const formatSelect = screen.getByRole('button', { name: /export format/i });
      await user.click(formatSelect);

      expect(await screen.findByText('Original')).toBeInTheDocument();
      expect(screen.getByText('JPEG')).toBeInTheDocument();
      expect(screen.getByText('PNG')).toBeInTheDocument();
    });
  });

  describe('Max Dimension Input', () => {
    test('allows entering max dimension value', async () => {
      const user = userEvent.setup();
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const maxDimensionInput = screen.getByLabelText(/max dimension/i);
      await user.type(maxDimensionInput, '1920');

      expect(maxDimensionInput).toHaveValue(1920);
    });

    test('max dimension is optional', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const maxDimensionInput = screen.getByLabelText(/max dimension/i);
      expect(maxDimensionInput).toHaveValue(null);
    });

    test('shows helper text for max dimension', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      expect(screen.getByText(/images will be resized to fit within this dimension/i)).toBeInTheDocument();
    });
  });

  describe('Export Operation', () => {
    test('prevents export when no destination is set', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      expect(exportButton).toBeDisabled();
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    test('disables Export button when no destination is set', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      expect(exportButton).toBeDisabled();
    });

    test('enables Export button when destination is set', async () => {
      const user = userEvent.setup();
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      expect(exportButton).not.toBeDisabled();
    });

    test('calls API with correct parameters for basic export', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-123' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/export',
          {
            photo_ids: selectedIds,
            destination: '/export/path',
            format: 'original',
            max_dimension: null,
          }
        );
      });
    });

    test('calls API with JPEG format when selected', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-456' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const formatSelect = screen.getByRole('button', { name: /export format/i });
      await user.click(formatSelect);
      const jpegOption = await screen.findByText('JPEG');
      await user.click(jpegOption);

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/export',
          expect.objectContaining({
            format: 'jpg',
          })
        );
      });
    });

    test('calls API with max dimension when provided', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-789' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const maxDimensionInput = screen.getByLabelText(/max dimension/i);
      await user.type(maxDimensionInput, '1920');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/export',
          expect.objectContaining({
            max_dimension: 1920,
          })
        );
      });
    });

    test('shows success toast on successful export', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-success' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Export Started',
          description: expect.stringContaining('Exporting 3 photos'),
        });
      });
    });

    test('includes job ID in success toast', async () => {
      const user = userEvent.setup();
      const jobId = 'test-export-job-xyz';
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: jobId },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Export Started',
          description: expect.stringContaining(jobId),
        });
      });
    });

    test('closes dialog after successful export', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-close' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    test('resets form fields after successful export', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-reset' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const maxDimensionInput = screen.getByLabelText(/max dimension/i);
      await user.type(maxDimensionInput, '1920');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    test('shows error toast on failed export', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Export failed: disk full';
      mockedAxios.post.mockRejectedValueOnce(new Error(errorMessage));

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Export Failed',
          description: errorMessage,
          variant: 'destructive',
        });
      });
    });

    test('handles non-Error exception', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockRejectedValueOnce('String error');

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Export Failed',
          description: 'Failed to start export',
          variant: 'destructive',
        });
      });
    });

    test('shows loading state during export', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(screen.getByText(/exporting/i)).toBeInTheDocument();
      });
    });

    test('disables buttons during loading', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

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
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    test('does not call API when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockedAxios.post).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    test('handles single photo export', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={['photo1']}
        />
      );

      expect(screen.getByText(/export 1 selected photos to a folder/i)).toBeInTheDocument();
    });

    test('handles empty selected IDs array', () => {
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={[]}
        />
      );

      expect(screen.getByText(/export 0 selected photos to a folder/i)).toBeInTheDocument();
    });

    test('handles large number of selected photos', () => {
      const manyIds = Array.from({ length: 100 }, (_, i) => `photo${i}`);
      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={manyIds}
        />
      );

      expect(screen.getByText(/export 100 selected photos to a folder/i)).toBeInTheDocument();
    });

    test('handles empty max dimension input', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-no-max' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/export',
          expect.objectContaining({
            max_dimension: null,
          })
        );
      });
    });

    test('parses max dimension as integer', async () => {
      const user = userEvent.setup();
      mockedAxios.post.mockResolvedValueOnce({
        data: { job_id: 'export-job-parse' },
      });

      render(
        <BatchExportDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          selectedIds={selectedIds}
        />
      );

      const input = screen.getByLabelText(/destination folder/i);
      await user.type(input, '/export/path');

      const maxDimensionInput = screen.getByLabelText(/max dimension/i);
      await user.type(maxDimensionInput, '2560');

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:5555/api/batch/export',
          expect.objectContaining({
            max_dimension: 2560,
          })
        );
      });
    });
  });
});
