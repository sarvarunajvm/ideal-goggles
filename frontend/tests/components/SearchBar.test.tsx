/**
 * Tests for SearchBar component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import SearchBar from '../../src/components/SearchBar';

describe('SearchBar Component', () => {
  const mockOnSearch = jest.fn();
  const mockOnImageSearch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Text Search Mode', () => {
    test('renders text input with correct placeholder', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename, folder, or content/i);
      expect(input).toBeInTheDocument();
    });

    test('handles text input and submission', async () => {
      const user = userEvent.setup();

      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      await user.type(input, 'vacation photos');
      await user.type(input, '{Enter}');

      expect(mockOnSearch).toHaveBeenCalledWith('vacation photos');
    });

    test('trims whitespace from search query', async () => {
      const user = userEvent.setup();

      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      await user.type(input, '  test query  ');
      await user.type(input, '{Enter}');

      expect(mockOnSearch).toHaveBeenCalledWith('test query');
    });

    test('does not submit empty queries', async () => {
      const user = userEvent.setup();

      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      await user.type(input, '   '); // Only spaces
      await user.type(input, '{Enter}');

      expect(mockOnSearch).not.toHaveBeenCalled();
    });

    test('disables input when loading', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={true}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      expect(input).toBeDisabled();
    });

    test('shows loading spinner when loading', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={true}
        />
      );

      const spinner = screen.getByRole('button').querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Semantic Search Mode', () => {
    test('renders with semantic search placeholder', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="semantic"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Describe what you're looking for/i);
      expect(input).toBeInTheDocument();
    });

    test('handles semantic search submission', async () => {
      const user = userEvent.setup();

      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="semantic"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Describe what you're looking for/i);
      await user.type(input, 'sunset over mountains');
      await user.type(input, '{Enter}');

      expect(mockOnSearch).toHaveBeenCalledWith('sunset over mountains');
    });
  });

  describe('Image Search Mode', () => {
    test('renders image upload area', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      expect(screen.getByText(/Upload an image to search/i)).toBeInTheDocument();
      expect(screen.getByText('📸')).toBeInTheDocument();
    });

    test('handles image file selection', async () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const file = new File(['image content'], 'test.jpg', { type: 'image/jpeg' });
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      expect(mockOnImageSearch).toHaveBeenCalledWith(file);
    });

    test('only accepts image files', async () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const textFile = new File(['text content'], 'test.txt', { type: 'text/plain' });
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [textFile] } });

      expect(mockOnImageSearch).not.toHaveBeenCalled();
    });

    test('shows loading state for image search', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={true}
        />
      );

      expect(screen.getByText(/Processing image/i)).toBeInTheDocument();
    });

    test('clicking upload area triggers file input', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const uploadArea = screen.getByText(/Upload an image to search/i).parentElement?.parentElement;
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      // Mock click method
      const clickSpy = jest.spyOn(fileInput, 'click');

      fireEvent.click(uploadArea!);

      expect(clickSpy).toHaveBeenCalled();
    });
  });

  describe('Button States', () => {
    test('disables search button when query is empty', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    test('enables search button when query is entered', async () => {
      const user = userEvent.setup();

      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      const button = screen.getByRole('button');

      await user.type(input, 'test');

      expect(button).not.toBeDisabled();
    });

    test('clicking search button triggers search', async () => {
      const user = userEvent.setup();

      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      const button = screen.getByRole('button');

      await user.type(input, 'search term');
      await user.click(button);

      expect(mockOnSearch).toHaveBeenCalledWith('search term');
    });
  });
});