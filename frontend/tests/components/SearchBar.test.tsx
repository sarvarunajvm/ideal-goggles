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

  describe('Additional Coverage Tests', () => {
    test('handles image mode when loading - shows processing text', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={true}
        />
      );

      expect(screen.getByText(/Processing image/i)).toBeInTheDocument();
      expect(screen.queryByText(/Upload an image to search/i)).not.toBeInTheDocument();
    });

    test('image upload area has disabled state when loading', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={true}
        />
      );

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(fileInput).toBeDisabled();
    });

    test('image upload area has correct hover styles when not loading', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const uploadArea = screen.getByText(/Upload an image to search/i).parentElement?.parentElement;
      expect(uploadArea).toHaveClass('hover:border-blue-400', 'hover:bg-blue-50');
    });

    test('image upload area has cursor-not-allowed when loading', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={true}
        />
      );

      const uploadArea = screen.getByText(/Processing image/i).parentElement?.parentElement;
      expect(uploadArea).toHaveClass('cursor-not-allowed');
    });

    test('text input has correct background when loading', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={true}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      expect(input).toHaveClass('bg-gray-50', 'cursor-not-allowed');
    });

    test('text input has white background when not loading', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      expect(input).toHaveClass('bg-white');
    });

    test('submit button has correct disabled styling', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-gray-200', 'text-gray-400', 'cursor-not-allowed');
    });

    test('submit button has correct active styling when query exists', async () => {
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
      await user.type(input, 'test');

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-blue-600', 'text-white', 'hover:bg-blue-700');
    });

    test('handles image file with no files selected', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [] } });

      expect(mockOnImageSearch).not.toHaveBeenCalled();
    });

    test('handles image file that is not an image type', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [pdfFile] } });

      expect(mockOnImageSearch).not.toHaveBeenCalled();
    });

    test('handles various image types correctly', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const pngFile = new File(['image content'], 'test.png', { type: 'image/png' });
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [pngFile] } });

      expect(mockOnImageSearch).toHaveBeenCalledWith(pngFile);
    });

    test('search icon emoji displays correctly', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('🔍');
    });

    test('camera emoji displays in image mode', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      expect(screen.getByText('📸')).toBeInTheDocument();
    });

    test('form has relative positioning', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const form = document.querySelector('form');
      expect(form).toHaveClass('relative');
    });

    test('handles form submission with Enter key', async () => {
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
      await user.type(input, 'test query{Enter}');

      expect(mockOnSearch).toHaveBeenCalledWith('test query');
    });

    test('does not submit in image mode with form', async () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      // No form should exist in image mode
      const form = document.querySelector('form');
      expect(form).not.toBeInTheDocument();
    });

    test('handles query state changes', async () => {
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

      await user.type(input, 'first query');
      expect(input).toHaveValue('first query');

      await user.clear(input);
      expect(input).toHaveValue('');

      await user.type(input, 'second query');
      expect(input).toHaveValue('second query');
    });

    test('input field has correct size and padding', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      expect(input).toHaveClass('w-full', 'px-4', 'py-3', 'pr-12', 'text-lg');
    });

    test('button has correct positioning', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toHaveClass('absolute', 'right-2', 'top-1/2', 'transform', '-translate-y-1/2');
    });

    test('file input is hidden', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(fileInput).toHaveClass('hidden');
    });

    test('upload area has correct padding and border radius', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      const uploadArea = screen.getByText(/Upload an image to search/i).parentElement?.parentElement;
      expect(uploadArea).toHaveClass('p-4', 'border-2', 'border-dashed', 'rounded-lg');
    });

    test('input focus styles are correct', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="text"
          loading={false}
        />
      );

      const input = screen.getByPlaceholderText(/Search by filename/i);
      expect(input).toHaveClass('focus:ring-2', 'focus:ring-blue-500', 'focus:border-transparent');
    });

    test('displays correct instructional text in image mode', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={false}
        />
      );

      expect(screen.getByText(/Click here or drag and drop an image file/i)).toBeInTheDocument();
    });

    test('handles disabled state in image mode correctly', () => {
      render(
        <SearchBar
          onSearch={mockOnSearch}
          onImageSearch={mockOnImageSearch}
          searchMode="image"
          loading={true}
        />
      );

      const uploadArea = screen.getByText(/Processing image/i).parentElement?.parentElement;
      expect(uploadArea).toHaveClass('bg-gray-50');
    });
  });
});