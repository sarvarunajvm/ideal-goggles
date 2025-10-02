/**
 * Unit tests for SearchFilters Component
 * Priority: P1 (Core search functionality)
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import SearchFilters from '../../src/components/SearchFilters'

const mockFilters = {
  from: '2023-01-01',
  to: '2023-12-31',
  folder: '/photos/vacation',
  limit: 50,
}

const mockOnChange = jest.fn()

describe('SearchFilters Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders filters toggle button', () => {
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    expect(screen.getByText('Filters')).toBeInTheDocument()
    expect(screen.getByText('🔧')).toBeInTheDocument()
    expect(screen.getByText('▼')).toBeInTheDocument()
  })

  test('shows filters panel when toggle is clicked', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    // Initially filters should be hidden
    expect(screen.queryByDisplayValue('2023-01-01')).not.toBeInTheDocument()

    // Click to show filters
    await user.click(screen.getByText('Filters'))

    // Now filters should be visible
    expect(screen.getByDisplayValue('2023-01-01')).toBeInTheDocument()
    expect(screen.getByDisplayValue('2023-12-31')).toBeInTheDocument()
    expect(screen.getByDisplayValue('/photos/vacation')).toBeInTheDocument()
    expect(screen.getByDisplayValue('50')).toBeInTheDocument()
  })

  test('hides filters panel when toggle is clicked again', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    // Show filters
    await user.click(screen.getByText('Filters'))
    expect(screen.getByDisplayValue('2023-01-01')).toBeInTheDocument()

    // Hide filters
    await user.click(screen.getByText('Filters'))
    expect(screen.queryByDisplayValue('2023-01-01')).not.toBeInTheDocument()
  })

  test('rotates arrow icon when filters are shown/hidden', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    const arrow = screen.getByText('▼')

    // Initially should not be rotated
    expect(arrow).not.toHaveClass('rotate-180')

    // Show filters
    await user.click(screen.getByText('Filters'))
    expect(arrow).toHaveClass('rotate-180')

    // Hide filters
    await user.click(screen.getByText('Filters'))
    expect(arrow).not.toHaveClass('rotate-180')
  })

  describe('Filter Controls', () => {
    test('displays current filter values', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      expect(screen.getByDisplayValue('2023-01-01')).toBeInTheDocument()
      expect(screen.getByDisplayValue('2023-12-31')).toBeInTheDocument()
      expect(screen.getByDisplayValue('/photos/vacation')).toBeInTheDocument()
      expect(screen.getByDisplayValue('50')).toBeInTheDocument()
    })

    test('calls onChange when from date is changed', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const fromDateInput = screen.getByDisplayValue('2023-01-01')

      fireEvent.change(fromDateInput, { target: { value: '2023-06-01' } })

      expect(mockOnChange).toHaveBeenCalledWith({ from: '2023-06-01' })
    })

    test('calls onChange when to date is changed', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const toDateInput = screen.getByDisplayValue('2023-12-31')

      fireEvent.change(toDateInput, { target: { value: '2023-06-30' } })

      expect(mockOnChange).toHaveBeenCalledWith({ to: '2023-06-30' })
    })

    test('calls onChange when folder is changed', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const folderInput = screen.getByDisplayValue('/photos/vacation')

      fireEvent.change(folderInput, { target: { value: '/photos/new-folder' } })

      expect(mockOnChange).toHaveBeenCalledWith({ folder: '/photos/new-folder' })
    })

    test('calls onChange when limit is changed', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const limitSelect = screen.getByDisplayValue('50')

      fireEvent.change(limitSelect, { target: { value: '100' } })

      expect(mockOnChange).toHaveBeenCalledWith({ limit: 100 })
    })

    test('shows correct limit options', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const limitSelect = screen.getByDisplayValue('50')
      const options = limitSelect.querySelectorAll('option')

      expect(options).toHaveLength(5)
      expect(screen.getByText('10 photos')).toBeInTheDocument()
      expect(screen.getByText('25 photos')).toBeInTheDocument()
      expect(screen.getByText('50 photos')).toBeInTheDocument()
      expect(screen.getByText('100 photos')).toBeInTheDocument()
      expect(screen.getByText('200 photos')).toBeInTheDocument()
    })

    test('clears all filters when clear button is clicked', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const clearButton = screen.getByText('Clear All Filters')

      await user.click(clearButton)

      expect(mockOnChange).toHaveBeenCalledWith({
        from: '',
        to: '',
        folder: '',
        limit: 50,
      })
    })

    test('has proper accessibility attributes', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const fromDateInput = screen.getByDisplayValue('2023-01-01')
      const toDateInput = screen.getByDisplayValue('2023-12-31')
      const folderInput = screen.getByPlaceholderText('Filter by folder...')

      expect(fromDateInput).toHaveAttribute('type', 'date')
      expect(toDateInput).toHaveAttribute('type', 'date')
      expect(folderInput).toHaveAttribute('type', 'text')
      expect(folderInput).toHaveAttribute('placeholder', 'Filter by folder...')
    })

    test('applies correct CSS classes', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)
      await user.click(screen.getByText('Filters'))

      const fromDateInput = screen.getByDisplayValue('2023-01-01')
      expect(fromDateInput).toHaveClass(
        'w-full',
        'px-3',
        'py-2',
        'border',
        'border-gray-300',
        'rounded-md',
        'focus:ring-2',
        'focus:ring-blue-500',
        'focus:border-transparent'
      )

      const clearButton = screen.getByText('Clear All Filters')
      expect(clearButton).toHaveClass(
        'px-4',
        'py-2',
        'text-sm',
        'bg-gray-200',
        'text-gray-700',
        'rounded-md',
        'hover:bg-gray-300',
        'transition-colors'
      )
    })
  })

  describe('Empty Filters', () => {
    test('handles empty filter values', async () => {
      const emptyFilters = {
        from: '',
        to: '',
        folder: '',
        limit: 10,
      }

      const user = userEvent.setup()
      render(<SearchFilters filters={emptyFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      expect(screen.getByLabelText('From Date')).toHaveValue('')
      expect(screen.getByLabelText('To Date')).toHaveValue('')
      expect(screen.getByLabelText('Folder')).toHaveValue('')
      expect(screen.getByLabelText('Results Limit')).toHaveValue('10')
    })
  })

  describe('Edge Cases', () => {
    test('handles rapid toggle clicks', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      const toggleButton = screen.getByText('Filters')

      // Rapidly click multiple times
      await user.click(toggleButton)
      await user.click(toggleButton)
      await user.click(toggleButton)

      // Should end up shown
      expect(screen.getByLabelText('From Date')).toBeInTheDocument()
    })

    test('handles invalid date input gracefully', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))
      const fromDateInput = screen.getByLabelText('From Date')

      // Try to input invalid date
      fireEvent.change(fromDateInput, { target: { value: 'invalid-date' } })

      expect(mockOnChange).toHaveBeenCalledWith({ from: 'invalid-date' })
    })

    test('handles special characters in folder input', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))
      const folderInput = screen.getByLabelText('Folder')

      await user.clear(folderInput)
      await user.type(folderInput, '/photos/café & "special" chars')

      expect(mockOnChange).toHaveBeenCalledWith({ folder: '/photos/café & "special" chars' })
    })
  })

  describe('Additional Coverage Tests', () => {
    test('handles all limit option values', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))
      const limitSelect = screen.getByLabelText('Results Limit')

      // Test each limit option
      await user.selectOptions(limitSelect, '10')
      expect(mockOnChange).toHaveBeenCalledWith({ limit: 10 })

      await user.selectOptions(limitSelect, '25')
      expect(mockOnChange).toHaveBeenCalledWith({ limit: 25 })

      await user.selectOptions(limitSelect, '100')
      expect(mockOnChange).toHaveBeenCalledWith({ limit: 100 })

      await user.selectOptions(limitSelect, '200')
      expect(mockOnChange).toHaveBeenCalledWith({ limit: 200 })
    })

    test('handles multiple filter changes in sequence', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const fromDateInput = screen.getByLabelText('From Date')
      const toDateInput = screen.getByLabelText('To Date')
      const folderInput = screen.getByLabelText('Folder')
      const limitSelect = screen.getByLabelText('Results Limit')

      await user.clear(fromDateInput)
      await user.type(fromDateInput, '2024-01-01')

      await user.clear(toDateInput)
      await user.type(toDateInput, '2024-12-31')

      await user.clear(folderInput)
      await user.type(folderInput, '/new-folder')

      await user.selectOptions(limitSelect, '100')

      expect(mockOnChange).toHaveBeenCalledTimes(4)
    })

    test('clear button resets all filters to default', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))
      const clearButton = screen.getByText('Clear All Filters')

      await user.click(clearButton)

      expect(mockOnChange).toHaveBeenCalledWith({
        from: '',
        to: '',
        folder: '',
        limit: 50,
      })
    })

    test('filter panel has correct styling when shown', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const panel = screen.getByLabelText('From Date').closest('.p-4.bg-gray-50')
      expect(panel).toHaveClass('rounded-lg', 'border', 'border-gray-200')
    })

    test('toggle button has hover state', () => {
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      const toggleButton = screen.getByText('Filters')
      expect(toggleButton).toHaveClass('hover:text-gray-900')
    })

    test('grid layout is responsive', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const grid = document.querySelector('.grid-cols-1.md\\:grid-cols-4')
      expect(grid).toBeInTheDocument()
    })

    test('limit select has correct default value', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const limitSelect = screen.getByDisplayValue('50') as HTMLSelectElement
      expect(limitSelect.value).toBe('50')
    })

    test('handles onChange with single character input', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))
      const folderInput = screen.getByDisplayValue('/photos/vacation')

      fireEvent.change(folderInput, { target: { value: 'a' } })

      expect(mockOnChange).toHaveBeenCalledWith({ folder: 'a' })
    })

    test('handles empty date string', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))
      const fromDateInput = screen.getByDisplayValue('2023-01-01')

      fireEvent.change(fromDateInput, { target: { value: '' } })

      expect(mockOnChange).toHaveBeenCalledWith({ from: '' })
    })

    test('filters panel uses proper spacing', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const panel = document.querySelector('.mt-4.p-4')
      expect(panel).toBeInTheDocument()
    })

    test('input fields have proper focus styles', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const fromDateInput = screen.getByDisplayValue('2023-01-01')
      expect(fromDateInput).toHaveClass('focus:ring-2', 'focus:ring-blue-500', 'focus:border-transparent')
    })

    test('select dropdown has proper styling', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const limitSelect = screen.getByDisplayValue('50')
      expect(limitSelect).toHaveClass('w-full', 'px-3', 'py-2', 'border', 'border-gray-300', 'rounded-md')
    })

    test('labels have correct text', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      expect(screen.getByText('From Date')).toHaveClass('text-sm', 'font-medium', 'text-gray-700')
      expect(screen.getByText('To Date')).toHaveClass('text-sm', 'font-medium', 'text-gray-700')
      expect(screen.getByText('Folder')).toHaveClass('text-sm', 'font-medium', 'text-gray-700')
      expect(screen.getByText('Results Limit')).toHaveClass('text-sm', 'font-medium', 'text-gray-700')
    })

    test('toggle shows/hides with proper animation class', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      const arrow = screen.getByText('▼')
      expect(arrow).toHaveClass('transform', 'transition-transform')

      await user.click(screen.getByText('Filters'))
      expect(arrow).toHaveClass('rotate-180')
    })

    test('handleChange is called with correct key-value pairs', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))

      const fromDateInput = screen.getByDisplayValue('2023-01-01')
      fireEvent.change(fromDateInput, { target: { value: '2024-06-15' } })

      expect(mockOnChange).toHaveBeenCalledWith({ from: '2024-06-15' })
    })

    test('limit value is parsed as integer', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      await user.click(screen.getByText('Filters'))
      const limitSelect = screen.getByLabelText('Results Limit')

      await user.selectOptions(limitSelect, '100')

      expect(mockOnChange).toHaveBeenCalledWith({ limit: 100 })
      expect(typeof mockOnChange.mock.calls[0][0].limit).toBe('number')
    })

    test('maintains filter state between toggles', async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      // Show filters
      await user.click(screen.getByText('Filters'))
      const fromInput1 = screen.getByDisplayValue('2023-01-01')
      expect(fromInput1).toBeInTheDocument()

      // Hide filters
      await user.click(screen.getByText('Filters'))
      expect(screen.queryByDisplayValue('2023-01-01')).not.toBeInTheDocument()

      // Show again - values should still be there
      await user.click(screen.getByText('Filters'))
      const fromInput2 = screen.getByDisplayValue('2023-01-01')
      expect(fromInput2).toBeInTheDocument()
    })
  })
})