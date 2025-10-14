import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import { useDeveloperModeStore } from '@/stores/developerModeStore';
import { useToast } from '@/components/ui/use-toast';
import { getApiBaseUrl } from '@/services/apiClient';

// Mock the stores and hooks
jest.mock('@/stores/developerModeStore');
jest.mock('@/components/ui/use-toast');
jest.mock('@/services/apiClient');

const mockUseDeveloperModeStore = useDeveloperModeStore as jest.MockedFunction<typeof useDeveloperModeStore>;
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>;
const mockGetApiBaseUrl = getApiBaseUrl as jest.MockedFunction<typeof getApiBaseUrl>;

describe('Navigation', () => {
  const mockToast = jest.fn();
  const mockSetDeveloperMode = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    // Default mocks
    mockUseDeveloperModeStore.mockReturnValue({
      isDeveloperMode: false,
      setDeveloperMode: mockSetDeveloperMode,
    });

    mockUseToast.mockReturnValue({
      toast: mockToast,
    });

    mockGetApiBaseUrl.mockReturnValue('http://localhost:5555');

    // Mock window.open
    global.open = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Rendering', () => {
    test('renders logo and brand name', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      expect(screen.getByText('Ideal Goggles')).toBeInTheDocument();
      expect(document.querySelector('.lucide-camera')).toBeInTheDocument();
    });

    test('renders all navigation items', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      expect(screen.getByText('Search')).toBeInTheDocument();
      expect(screen.getByText('People')).toBeInTheDocument();
      expect(screen.getByText('Stats')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    test('does not show developer items by default', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      expect(screen.queryByText('Dependencies')).not.toBeInTheDocument();
      expect(screen.queryByText('API Docs')).not.toBeInTheDocument();
    });

    test('shows developer items when in developer mode', () => {
      mockUseDeveloperModeStore.mockReturnValue({
        isDeveloperMode: true,
        setDeveloperMode: mockSetDeveloperMode,
      });

      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      expect(screen.getByText('Dependencies')).toBeInTheDocument();
      expect(screen.getByText('API Docs')).toBeInTheDocument();
    });

    test('shows mobile menu button', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // The mobile menu toggle button should be present
      const menuButton = screen.getByRole('button', { name: '' });
      expect(menuButton).toBeInTheDocument();
      // Menu icon should be visible initially (not X icon)
      expect(document.querySelector('.lucide-menu')).toBeInTheDocument();
    });
  });

  describe('Navigation Active State', () => {
    test('highlights active route', () => {
      render(
        <MemoryRouter initialEntries={['/people']}>
          <Navigation />
        </MemoryRouter>
      );

      const peopleLink = screen.getByRole('link', { name: /people/i });
      // With asChild prop, the Link element gets the Button's classes directly
      expect(peopleLink).toHaveClass('border-b-2', 'border-primary');
    });

    test('does not highlight inactive routes', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <Navigation />
        </MemoryRouter>
      );

      const peopleLink = screen.getByRole('link', { name: /people/i });
      expect(peopleLink).not.toHaveClass('border-b-2');
    });
  });

  describe('Developer Mode Activation', () => {
    test('shows code prompt after 6 clicks on logo', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;

      // Click 5 times - should not show dialog
      for (let i = 0; i < 5; i++) {
        await user.click(logo);
      }
      expect(screen.queryByText('Developer Mode')).not.toBeInTheDocument();

      // 6th click - should show dialog
      await user.click(logo);
      expect(screen.getByText('Developer Mode')).toBeInTheDocument();
      expect(screen.getByText('Enter the access code to enable developer features')).toBeInTheDocument();
    });

    test('resets click count after timeout', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;

      // Click 3 times
      for (let i = 0; i < 3; i++) {
        await user.click(logo);
      }

      // Wait for timeout (2000ms + buffer) - wrap in act to handle state updates
      act(() => {
        jest.advanceTimersByTime(2100);
      });

      // Click 5 more times - should not show dialog yet (count was reset, so we're only at 5 total)
      for (let i = 0; i < 5; i++) {
        await user.click(logo);
      }
      expect(screen.queryByText('Developer Mode')).not.toBeInTheDocument();

      // 6th click should show dialog
      await user.click(logo);
      expect(screen.getByText('Developer Mode')).toBeInTheDocument();
    });

    test('enables developer mode with correct code', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Trigger code prompt
      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      // Enter correct code
      const input = screen.getByPlaceholderText('Enter code');
      await user.type(input, '1996');

      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      expect(mockSetDeveloperMode).toHaveBeenCalledWith(true);
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Developer Mode Enabled',
        description: 'Advanced features are now available',
      });
    });

    test('shows error toast with incorrect code', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Trigger code prompt
      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      // Enter incorrect code
      const input = screen.getByPlaceholderText('Enter code');
      await user.type(input, 'wrong');

      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      expect(mockSetDeveloperMode).not.toHaveBeenCalled();
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Invalid Code',
        description: 'The code you entered is incorrect',
        variant: 'destructive',
      });
    });

    test('submits code on Enter key', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Trigger code prompt
      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      // Enter code and press Enter
      const input = screen.getByPlaceholderText('Enter code');
      await user.type(input, '1996{Enter}');

      expect(mockSetDeveloperMode).toHaveBeenCalledWith(true);
    });

    test('cancels code dialog', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Trigger code prompt
      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText('Developer Mode')).not.toBeInTheDocument();
      });
    });

    test('clears input on cancel', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Trigger code prompt
      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      // Type something
      const input = screen.getByPlaceholderText('Enter code');
      await user.type(input, 'test');

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Re-open dialog
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      // Input should be cleared
      const newInput = screen.getByPlaceholderText('Enter code');
      expect(newInput).toHaveValue('');
    });
  });

  describe('Mobile Menu', () => {
    test('toggles mobile menu on button click', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Initially menu icon is shown
      expect(document.querySelector('.lucide-menu')).toBeInTheDocument();
      expect(document.querySelector('.lucide-x')).not.toBeInTheDocument();

      // Click to open
      const menuButton = screen.getByRole('button', { name: '' });
      await user.click(menuButton);

      // X icon should be shown
      expect(document.querySelector('.lucide-x')).toBeInTheDocument();
      expect(document.querySelector('.lucide-menu')).not.toBeInTheDocument();
    });

    test('closes mobile menu when navigation item is clicked', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Open mobile menu
      const menuButton = screen.getByRole('button', { name: '' });
      await user.click(menuButton);

      // Click a navigation item
      const peopleLinks = screen.getAllByText('People');
      // Find the one in the mobile menu (there will be desktop and mobile versions)
      const mobileLink = peopleLinks[peopleLinks.length - 1];
      await user.click(mobileLink);

      // Menu should close
      expect(document.querySelector('.lucide-menu')).toBeInTheDocument();
      expect(document.querySelector('.lucide-x')).not.toBeInTheDocument();
    });

    test('shows all navigation items in mobile menu', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Open mobile menu
      const menuButton = screen.getByRole('button', { name: '' });
      await user.click(menuButton);

      // Check all items are present (will have duplicates from desktop)
      expect(screen.getAllByText('Search').length).toBeGreaterThan(1);
      expect(screen.getAllByText('People').length).toBeGreaterThan(1);
      expect(screen.getAllByText('Stats').length).toBeGreaterThan(1);
      expect(screen.getAllByText('Settings').length).toBeGreaterThan(1);
    });

    test('shows developer items in mobile menu when in developer mode', async () => {
      const user = userEvent.setup({ delay: null });
      mockUseDeveloperModeStore.mockReturnValue({
        isDeveloperMode: true,
        setDeveloperMode: mockSetDeveloperMode,
      });

      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Open mobile menu
      const menuButton = screen.getByRole('button', { name: '' });
      await user.click(menuButton);

      // Check developer items are present
      expect(screen.getAllByText('Dependencies').length).toBeGreaterThan(1);
      expect(screen.getAllByText('API Docs').length).toBeGreaterThan(1);
    });
  });

  describe('API Docs Link', () => {
    test('opens API docs in new tab when clicked', async () => {
      const user = userEvent.setup({ delay: null });
      mockUseDeveloperModeStore.mockReturnValue({
        isDeveloperMode: true,
        setDeveloperMode: mockSetDeveloperMode,
      });

      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      const apiDocsButton = screen.getAllByText('API Docs')[0].closest('button');
      await user.click(apiDocsButton!);

      expect(global.open).toHaveBeenCalledWith('http://localhost:5555/docs', '_blank');
    });

    test('closes mobile menu after opening API docs', async () => {
      const user = userEvent.setup({ delay: null });
      mockUseDeveloperModeStore.mockReturnValue({
        isDeveloperMode: true,
        setDeveloperMode: mockSetDeveloperMode,
      });

      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Open mobile menu
      const menuButton = screen.getByRole('button', { name: '' });
      await user.click(menuButton);

      // Click API Docs in mobile menu
      const apiDocsButtons = screen.getAllByText('API Docs');
      const mobileApiDocs = apiDocsButtons[apiDocsButtons.length - 1].closest('button');
      await user.click(mobileApiDocs!);

      expect(global.open).toHaveBeenCalledWith('http://localhost:5555/docs', '_blank');
      // Menu should close
      expect(document.querySelector('.lucide-menu')).toBeInTheDocument();
    });

    test('uses correct API base URL', async () => {
      const user = userEvent.setup({ delay: null });
      mockGetApiBaseUrl.mockReturnValue('https://api.example.com');
      mockUseDeveloperModeStore.mockReturnValue({
        isDeveloperMode: true,
        setDeveloperMode: mockSetDeveloperMode,
      });

      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      const apiDocsButton = screen.getAllByText('API Docs')[0].closest('button');
      await user.click(apiDocsButton!);

      expect(global.open).toHaveBeenCalledWith('https://api.example.com/docs', '_blank');
    });
  });

  describe('Edge Cases', () => {
    test('handles rapid clicks on logo correctly', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;

      // Rapidly click 10 times
      for (let i = 0; i < 10; i++) {
        await user.click(logo);
      }

      // Should still show dialog only once
      expect(screen.getAllByText('Developer Mode').length).toBe(1);
    });

    test('handles empty code submission', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Trigger code prompt
      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      // Submit without entering code
      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      expect(mockSetDeveloperMode).not.toHaveBeenCalled();
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Invalid Code',
        description: 'The code you entered is incorrect',
        variant: 'destructive',
      });
    });

    test('password input masks the entered code', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      // Trigger code prompt
      const logo = document.querySelector('[title="Click 6 times for developer mode"]') as HTMLElement;
      for (let i = 0; i < 6; i++) {
        await user.click(logo);
      }

      const input = screen.getByPlaceholderText('Enter code');
      expect(input).toHaveAttribute('type', 'password');
    });
  });
});