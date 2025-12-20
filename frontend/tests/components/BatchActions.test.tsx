/**
 * Tests for BatchActions component
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { BatchActions } from '../../src/components/BatchActions/BatchActions';
import { useBatchSelectionStore } from '../../src/stores/batchSelectionStore';

// Mock axios
jest.mock('axios');

// Mock the store
jest.mock('../../src/stores/batchSelectionStore');

// Mock UI components with proper exports
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

describe('BatchActions Component', () => {
  const mockToggleSelectionMode = jest.fn();
  const mockClearSelection = jest.fn();
  const mockGetSelectedCount = jest.fn();
  const mockDisableSelectionMode = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Default store mock - selection mode disabled
    (useBatchSelectionStore as unknown as jest.Mock).mockReturnValue({
      selectionMode: false,
      selectedIds: new Set(),
      getSelectedCount: mockGetSelectedCount.mockReturnValue(0),
      toggleSelectionMode: mockToggleSelectionMode,
      clearSelection: mockClearSelection,
      disableSelectionMode: mockDisableSelectionMode,
    });
  });

  describe('Selection Mode Disabled', () => {
    test('renders photo count when selection mode is disabled', () => {
      render(<BatchActions totalItems={42} />);

      expect(screen.getByText('42 photos')).toBeInTheDocument();
    });

    test('renders Select button when selection mode is disabled', () => {
      render(<BatchActions totalItems={100} />);

      const selectButton = screen.getByRole('button', { name: /select/i });
      expect(selectButton).toBeInTheDocument();
    });

    test('clicking Select button toggles selection mode', async () => {
      const user = userEvent.setup();
      render(<BatchActions totalItems={100} />);

      const selectButton = screen.getByRole('button', { name: /select/i });
      await user.click(selectButton);

      expect(mockToggleSelectionMode).toHaveBeenCalledTimes(1);
    });
  });

  describe('Selection Mode Enabled - No Items Selected', () => {
    beforeEach(() => {
      (useBatchSelectionStore as unknown as jest.Mock).mockReturnValue({
        selectionMode: true,
        selectedIds: new Set(),
        getSelectedCount: mockGetSelectedCount.mockReturnValue(0),
        toggleSelectionMode: mockToggleSelectionMode,
        clearSelection: mockClearSelection,
        disableSelectionMode: mockDisableSelectionMode,
      });
    });

    test('shows selection count badge', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.getByText('0 selected')).toBeInTheDocument();
    });

    test('does not show action buttons when no items selected', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.queryByRole('button', { name: /export/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /tag/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
    });

    test('shows Cancel button', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    test('clicking Cancel button toggles selection mode off', async () => {
      const user = userEvent.setup();
      render(<BatchActions totalItems={100} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockToggleSelectionMode).toHaveBeenCalledTimes(1);
    });

    test('Clear button is disabled when no items selected', () => {
      render(<BatchActions totalItems={100} />);

      const clearButton = screen.getByRole('button', { name: /clear/i });
      expect(clearButton).toBeDisabled();
    });
  });

  describe('Selection Mode Enabled - Items Selected', () => {
    beforeEach(() => {
      (useBatchSelectionStore as unknown as jest.Mock).mockReturnValue({
        selectionMode: true,
        selectedIds: new Set(['photo1', 'photo2', 'photo3']),
        getSelectedCount: mockGetSelectedCount.mockReturnValue(3),
        toggleSelectionMode: mockToggleSelectionMode,
        clearSelection: mockClearSelection,
        disableSelectionMode: mockDisableSelectionMode,
      });
    });

    test('shows correct selection count', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.getByText('3 selected')).toBeInTheDocument();
    });

    test('shows Export button when items are selected', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    });

    test('shows Tag button when items are selected', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.getByRole('button', { name: /tag/i })).toBeInTheDocument();
    });

    test('shows Delete button when items are selected', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });

    test('Clear button is enabled when items are selected', () => {
      render(<BatchActions totalItems={100} />);

      const clearButton = screen.getByRole('button', { name: /clear/i });
      expect(clearButton).not.toBeDisabled();
    });

    test('clicking Clear button clears selection', async () => {
      const user = userEvent.setup();
      render(<BatchActions totalItems={100} />);

      const clearButton = screen.getByRole('button', { name: /clear/i });
      await user.click(clearButton);

      expect(mockClearSelection).toHaveBeenCalledTimes(1);
    });

    test('clicking Export button opens export dialog', async () => {
      const user = userEvent.setup();
      render(<BatchActions totalItems={100} />);

      const exportButton = screen.getByRole('button', { name: /export/i });
      await user.click(exportButton);

      // Dialog should open - check for dialog title
      await waitFor(() => {
        expect(screen.getByText('Export Photos')).toBeInTheDocument();
      });
    });

    test('clicking Delete button opens delete dialog', async () => {
      const user = userEvent.setup();
      render(<BatchActions totalItems={100} />);

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Dialog should open - check for dialog title
      await waitFor(() => {
        expect(screen.getByText('Delete Photos')).toBeInTheDocument();
      });
    });

    test('clicking Tag button opens tag dialog', async () => {
      const user = userEvent.setup();
      render(<BatchActions totalItems={100} />);

      const tagButton = screen.getByRole('button', { name: /tag/i });
      await user.click(tagButton);

      // Dialog should open - check for dialog content
      await waitFor(() => {
        expect(screen.getByText(/tag photos/i)).toBeInTheDocument();
      });
    });
  });

  describe('Select All Functionality', () => {
    beforeEach(() => {
      (useBatchSelectionStore as unknown as jest.Mock).mockReturnValue({
        selectionMode: true,
        selectedIds: new Set(['photo1']),
        getSelectedCount: mockGetSelectedCount.mockReturnValue(1),
        toggleSelectionMode: mockToggleSelectionMode,
        clearSelection: mockClearSelection,
        disableSelectionMode: mockDisableSelectionMode,
      });
    });

    test('shows Select All button when onSelectAll prop is provided', () => {
      const mockOnSelectAll = jest.fn();
      render(<BatchActions totalItems={100} onSelectAll={mockOnSelectAll} />);

      expect(screen.getByRole('button', { name: /select all/i })).toBeInTheDocument();
    });

    test('does not show Select All button when onSelectAll prop is not provided', () => {
      render(<BatchActions totalItems={100} />);

      expect(screen.queryByRole('button', { name: /select all/i })).not.toBeInTheDocument();
    });

    test('clicking Select All button calls onSelectAll callback', async () => {
      const mockOnSelectAll = jest.fn();
      const user = userEvent.setup();
      render(<BatchActions totalItems={100} onSelectAll={mockOnSelectAll} />);

      const selectAllButton = screen.getByRole('button', { name: /select all/i });
      await user.click(selectAllButton);

      expect(mockOnSelectAll).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases', () => {
    test('handles zero total items', () => {
      render(<BatchActions totalItems={0} />);

      expect(screen.getByText('0 photos')).toBeInTheDocument();
    });

    test('handles large number of total items', () => {
      render(<BatchActions totalItems={999999} />);

      expect(screen.getByText('999999 photos')).toBeInTheDocument();
    });

    test('handles large number of selected items', () => {
      const largeSet = new Set(Array.from({ length: 1000 }, (_, i) => `photo${i}`));
      (useBatchSelectionStore as unknown as jest.Mock).mockReturnValue({
        selectionMode: true,
        selectedIds: largeSet,
        getSelectedCount: mockGetSelectedCount.mockReturnValue(1000),
        toggleSelectionMode: mockToggleSelectionMode,
        clearSelection: mockClearSelection,
        disableSelectionMode: mockDisableSelectionMode,
      });

      render(<BatchActions totalItems={2000} />);

      expect(screen.getByText('1000 selected')).toBeInTheDocument();
    });
  });
});
