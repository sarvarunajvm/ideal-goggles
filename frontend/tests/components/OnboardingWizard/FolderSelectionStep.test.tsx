import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { FolderSelectionStep } from '@/components/OnboardingWizard/FolderSelectionStep';
import { useOnboardingStore } from '@/stores/onboardingStore';

// Mock the store
jest.mock('@/stores/onboardingStore', () => ({
  useOnboardingStore: jest.fn(),
}));

describe('FolderSelectionStep', () => {
  const mockAddFolder = jest.fn();
  const mockRemoveFolder = jest.fn();
  const mockNextStep = jest.fn();
  const mockPrevStep = jest.fn();

  const defaultStore = {
    selectedFolders: [],
    addFolder: mockAddFolder,
    removeFolder: mockRemoveFolder,
    nextStep: mockNextStep,
    prevStep: mockPrevStep,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useOnboardingStore as any).mockReturnValue(defaultStore);

    // Mock window.electronAPI
    (window as any).electronAPI = {
      selectDirectory: jest.fn(),
    };
  });

  afterEach(() => {
    delete (window as any).electronAPI;
  });

  describe('Rendering', () => {
    test('renders heading and description', () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      expect(screen.getByText(/Where Are Your Photos\?/)).toBeInTheDocument();
      expect(screen.getByText(/Choose the folders where you keep your photos/)).toBeInTheDocument();
    });

    test('shows platform-specific default folder hint', () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const hint = screen.getByText(/Default: your Pictures folder/);
      expect(hint).toBeInTheDocument();
    });

    test('shows empty state when no folders selected', () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      expect(screen.getByText(/No folders selected yet/)).toBeInTheDocument();
      expect(screen.getByText(/Click "Add Folder" to get started/)).toBeInTheDocument();
    });

    test('renders Add Folder button', () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      expect(addButton).toBeInTheDocument();
    });

    test('renders navigation buttons', () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    });

    test('Next button is disabled when no folders selected', () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    test('Next button is enabled when folders are selected', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: ['/path/to/photos'],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).not.toBeDisabled();
    });
  });

  describe('Folder Selection - Electron', () => {
    test('opens native folder picker on Add Folder click', async () => {
      const mockSelectDirectory = jest.fn().mockResolvedValue({
        canceled: false,
        filePaths: ['/selected/folder'],
      });
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });
    });

    test('adds folder when selected from native picker', async () => {
      const mockSelectDirectory = jest.fn().mockResolvedValue({
        canceled: false,
        filePaths: ['/selected/folder'],
      });
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockAddFolder).toHaveBeenCalledWith('/selected/folder');
      });
    });

    test('does not add folder when picker is canceled', async () => {
      const mockSelectDirectory = jest.fn().mockResolvedValue({
        canceled: true,
        filePaths: [],
      });
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });

      expect(mockAddFolder).not.toHaveBeenCalled();
    });

    test('does not add duplicate folders', async () => {
      const mockSelectDirectory = jest.fn().mockResolvedValue({
        canceled: false,
        filePaths: ['/existing/folder'],
      });
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: ['/existing/folder'],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });

      expect(mockAddFolder).not.toHaveBeenCalled();
    });

    test('shows loading state while selecting', async () => {
      const mockSelectDirectory = jest.fn().mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          canceled: false,
          filePaths: ['/folder'],
        }), 100))
      );
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      expect(screen.getByText('Selecting...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Add Folder')).toBeInTheDocument();
      });
    });
  });

  describe('Folder Selection - Web/Fallback', () => {
    beforeEach(() => {
      delete (window as any).electronAPI;
    });

    test('shows manual input when Electron API not available', async () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('/path/to/your/photos')).toBeInTheDocument();
      });
    });

    test('adds folder from manual input', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      const input = await screen.findByPlaceholderText('/path/to/your/photos');
      await user.type(input, '/manual/path');

      const addManualButton = screen.getByRole('button', { name: /^add$/i });
      await user.click(addManualButton);

      expect(mockAddFolder).toHaveBeenCalledWith('/manual/path');
    });

    test('adds folder on Enter key in manual input', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      const input = await screen.findByPlaceholderText('/path/to/your/photos');
      await user.type(input, '/manual/path{Enter}');

      expect(mockAddFolder).toHaveBeenCalledWith('/manual/path');
    });

    test('cancels manual input', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      const cancelButton = await screen.findByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(screen.queryByPlaceholderText('/path/to/your/photos')).not.toBeInTheDocument();
    });

    test('does not add empty manual path', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      const addManualButton = await screen.findByRole('button', { name: /^add$/i });
      await user.click(addManualButton);

      expect(mockAddFolder).not.toHaveBeenCalled();
    });

    test('manual Add button is disabled when input is empty', async () => {
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      const addManualButton = await screen.findByRole('button', { name: /^add$/i });
      expect(addManualButton).toBeDisabled();
    });
  });

  describe('Folder List Management', () => {
    test('displays selected folders', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: ['/folder1', '/folder2', '/folder3'],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      expect(screen.getByText('/folder1')).toBeInTheDocument();
      expect(screen.getByText('/folder2')).toBeInTheDocument();
      expect(screen.getByText('/folder3')).toBeInTheDocument();
    });

    test('removes folder when X button clicked', async () => {
      const user = userEvent.setup();
      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: ['/folder/to/remove'],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const removeButton = screen.getByRole('button', { name: /remove folder/i });
      await user.click(removeButton);

      expect(mockRemoveFolder).toHaveBeenCalledWith('/folder/to/remove');
    });

    test('shows folder icon for each selected folder', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: ['/folder1', '/folder2'],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      // Check for folder icons (by class)
      const folderIcons = document.querySelectorAll('.lucide-folder');
      expect(folderIcons.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Navigation', () => {
    test('calls prevStep when Back button clicked', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      expect(mockPrevStep).toHaveBeenCalled();
    });

    test('calls nextStep when Next button clicked with folders', async () => {
      const user = userEvent.setup();
      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: ['/some/folder'],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      expect(mockNextStep).toHaveBeenCalled();
    });

    test('does not call nextStep when no folders selected', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      expect(mockNextStep).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    test('handles error in Electron folder selection', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const mockSelectDirectory = jest.fn().mockRejectedValue(new Error('Selection failed'));
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith('Failed to select folder:', expect.any(Error));
      });

      // Should show manual input as fallback
      expect(screen.getByPlaceholderText('/path/to/your/photos')).toBeInTheDocument();

      consoleError.mockRestore();
    });

    test('handles missing filePaths in Electron response', async () => {
      const mockSelectDirectory = jest.fn().mockResolvedValue({
        canceled: false,
        // filePaths missing
      });
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });

      expect(mockAddFolder).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    test('handles empty filePaths array from Electron', async () => {
      const mockSelectDirectory = jest.fn().mockResolvedValue({
        canceled: false,
        filePaths: [],
      });
      (window as any).electronAPI.selectDirectory = mockSelectDirectory;

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      const addButton = screen.getByRole('button', { name: /add folder/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockSelectDirectory).toHaveBeenCalled();
      });

      expect(mockAddFolder).not.toHaveBeenCalled();
    });

    test('handles long folder paths', () => {
      const longPath = '/very/long/path/to/some/deeply/nested/folder/structure/that/goes/on/and/on';
      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: [longPath],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      expect(screen.getByText(longPath)).toBeInTheDocument();
    });

    test('handles special characters in folder paths', () => {
      const specialPath = '/path/with spaces/and-dashes/under_scores/[brackets]/';
      (useOnboardingStore as any).mockReturnValue({
        ...defaultStore,
        selectedFolders: [specialPath],
      });

      render(
        <BrowserRouter>
          <FolderSelectionStep />
        </BrowserRouter>
      );

      expect(screen.getByText(specialPath)).toBeInTheDocument();
    });
  });
});