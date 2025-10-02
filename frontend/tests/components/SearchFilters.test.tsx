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
    expect(screen.queryByLabelText('From Date')).not.toBeInTheDocument()

    // Click to show filters
    await user.click(screen.getByText('Filters'))

    // Now filters should be visible
    expect(screen.getByLabelText('From Date')).toBeInTheDocument()
    expect(screen.getByLabelText('To Date')).toBeInTheDocument()
    expect(screen.getByLabelText('Folder')).toBeInTheDocument()
    expect(screen.getByLabelText('Results Limit')).toBeInTheDocument()
  })

  test('hides filters panel when toggle is clicked again', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    // Show filters
    await user.click(screen.getByText('Filters'))
    expect(screen.getByLabelText('From Date')).toBeInTheDocument()

    // Hide filters
    await user.click(screen.getByText('Filters'))
    expect(screen.queryByLabelText('From Date')).not.toBeInTheDocument()
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
    beforeEach(async () => {
      const user = userEvent.setup()
      render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

      // Show filters panel
      await user.click(screen.getByText('Filters'))
    })

    test('displays current filter values', () => {
      expect(screen.getByDisplayValue('2023-01-01')).toBeInTheDocument()
      expect(screen.getByDisplayValue('2023-12-31')).toBeInTheDocument()
      expect(screen.getByDisplayValue('/photos/vacation')).toBeInTheDocument()
      expect(screen.getByDisplayValue('50')).toBeInTheDocument()
    })

    test('calls onChange when from date is changed', async () => {
      const user = userEvent.setup()
      const fromDateInput = screen.getByLabelText('From Date')

      await user.clear(fromDateInput)
      await user.type(fromDateInput, '2023-06-01')

      expect(mockOnChange).toHaveBeenCalledWith({ from: '2023-06-01' })
    })

    test('calls onChange when to date is changed', async () => {
      const user = userEvent.setup()
      const toDateInput = screen.getByLabelText('To Date')

      await user.clear(toDateInput)
      await user.type(toDateInput, '2023-06-30')

      expect(mockOnChange).toHaveBeenCalledWith({ to: '2023-06-30' })
    })

    test('calls onChange when folder is changed', async () => {
      const user = userEvent.setup()
      const folderInput = screen.getByLabelText('Folder')

      await user.clear(folderInput)
      await user.type(folderInput, '/photos/new-folder')

      expect(mockOnChange).toHaveBeenCalledWith({ folder: '/photos/new-folder' })
    })

    test('calls onChange when limit is changed', async () => {
      const user = userEvent.setup()
      const limitSelect = screen.getByLabelText('Results Limit')

      await user.selectOptions(limitSelect, '100')

      expect(mockOnChange).toHaveBeenCalledWith({ limit: 100 })
    })

    test('shows correct limit options', () => {
      const limitSelect = screen.getByLabelText('Results Limit')
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
      const clearButton = screen.getByText('Clear All Filters')

      await user.click(clearButton)

      expect(mockOnChange).toHaveBeenCalledWith({
        from: '',
        to: '',
        folder: '',
        limit: 50,
      })
    })

    test('has proper accessibility attributes', () => {
      expect(screen.getByLabelText('From Date')).toHaveAttribute('type', 'date')
      expect(screen.getByLabelText('To Date')).toHaveAttribute('type', 'date')
      expect(screen.getByLabelText('Folder')).toHaveAttribute('type', 'text')
      expect(screen.getByLabelText('Folder')).toHaveAttribute('placeholder', 'Filter by folder...')
    })

    test('applies correct CSS classes', () => {
      const fromDateInput = screen.getByLabelText('From Date')
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
})