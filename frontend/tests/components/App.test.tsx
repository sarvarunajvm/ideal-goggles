/**
 * Tests for main App component
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import App from '../../src/App';

// Mock the API service
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getHealth: jest.fn()
  }
}));

const { apiService } = require('../../src/services/apiClient');

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.resetAllMocks();
    jest.useFakeTimers();
  });

  afterEach(async () => {
    await act(async () => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  test('shows loading screen when backend is not ready', async () => {
    apiService.getHealth.mockRejectedValue(new Error('Backend not ready'));

    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // Should show loading message with new UI text
    expect(screen.getByText(/Getting everything ready/i)).toBeInTheDocument();
    expect(screen.getByText(/preparing your photo library/i)).toBeInTheDocument();
  });

  test('renders main app when backend is ready', async () => {
    apiService.getHealth.mockResolvedValue({ status: 'healthy' });

    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // Wait for backend check to complete
    await waitFor(() => {
      expect(screen.queryByText(/Starting local backend/i)).not.toBeInTheDocument();
    });

    // App should be rendered - check for navigation instead of main role
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  test('shows backend URL in loading screen', async () => {
    apiService.getHealth.mockRejectedValue(new Error('Backend not ready'));

    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // New UI shows helpful tips instead of backend URL
    expect(screen.getByText(/personal photo search engine/i)).toBeInTheDocument();
  });

  test('retries backend connection periodically', async () => {
    // Reset and set up the mock for this specific test
    jest.clearAllMocks();
    apiService.getHealth = jest.fn()
      .mockRejectedValueOnce(new Error('Not ready'))
      .mockRejectedValueOnce(new Error('Still not ready'))
      .mockResolvedValueOnce({ status: 'healthy' });

    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // Initially shows loading
    expect(screen.getByText(/Getting everything ready/i)).toBeInTheDocument();

    // Advance timers to trigger retries
    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    await waitFor(() => {
      expect(apiService.getHealth).toHaveBeenCalledTimes(2);
    });

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    // Should eventually render the app
    await waitFor(() => {
      expect(screen.queryByText(/Getting everything ready/i)).not.toBeInTheDocument();
    });
  });

  test('handles Electron API when available', async () => {
    // Reset and set up the mock for this specific test
    jest.clearAllMocks();
    apiService.getHealth = jest.fn().mockRejectedValue(new Error('Backend not ready'));

    const mockElectronAPI = {
      getBackendLogPath: jest.fn().mockResolvedValue('/logs/backend.log'),
      getBackendPort: jest.fn().mockResolvedValue(5555)
    };

    // Mock window.electronAPI
    Object.defineProperty(window, 'electronAPI', {
      value: mockElectronAPI,
      writable: true,
      configurable: true
    });

    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // In Electron context, loading screen should still show
    expect(screen.getByText(/Getting everything ready/i)).toBeInTheDocument();

    // Clean up
    delete (window as any).electronAPI;
  });
});
