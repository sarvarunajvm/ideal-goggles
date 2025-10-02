/**
 * Simple unit tests for SearchFilters Component
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

  test('calls onChange when form inputs are changed', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    // Show filters
    await user.click(screen.getByText('Filters'))

    // Test from date change
    const fromInput = screen.getByDisplayValue('2023-01-01')
    await user.clear(fromInput)
    await user.type(fromInput, '2023-06-01')

    expect(mockOnChange).toHaveBeenCalledWith({ from: '2023-06-01' })
  })

  test('clears all filters when clear button is clicked', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    // Show filters
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

    // Check that inputs exist with empty values
    const inputs = screen.getAllByRole('textbox')
    expect(inputs[0]).toHaveValue('')
    expect(inputs[1]).toHaveValue('')
    expect(inputs[2]).toHaveValue('')

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('10')
  })

  test('has proper form structure', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    await user.click(screen.getByText('Filters'))

    // Check for proper input types
    const dateInputs = screen.getAllByDisplayValue('2023-01-01')
    expect(dateInputs[0]).toHaveAttribute('type', 'date')

    const textInputs = screen.getAllByRole('textbox')
    expect(textInputs.find(input => input.getAttribute('type') === 'text')).toBeInTheDocument()

    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()
  })

  test('shows correct limit options', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    await user.click(screen.getByText('Filters'))

    expect(screen.getByText('10 photos')).toBeInTheDocument()
    expect(screen.getByText('25 photos')).toBeInTheDocument()
    expect(screen.getByText('50 photos')).toBeInTheDocument()
    expect(screen.getByText('100 photos')).toBeInTheDocument()
    expect(screen.getByText('200 photos')).toBeInTheDocument()
  })

  test('applies correct CSS classes', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    await user.click(screen.getByText('Filters'))

    const fromInput = screen.getByDisplayValue('2023-01-01')
    expect(fromInput).toHaveClass(
      'w-full',
      'px-3',
      'py-2',
      'border',
      'border-gray-300',
      'rounded-md'
    )

    const clearButton = screen.getByText('Clear All Filters')
    expect(clearButton).toHaveClass(
      'px-4',
      'py-2',
      'text-sm',
      'bg-gray-200',
      'text-gray-700',
      'rounded-md'
    )
  })

  test('handles rapid toggle clicks', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    const toggleButton = screen.getByText('Filters')

    // Rapidly click multiple times
    await user.click(toggleButton)
    await user.click(toggleButton)
    await user.click(toggleButton)

    // Should end up shown
    expect(screen.getByDisplayValue('2023-01-01')).toBeInTheDocument()
  })

  test('handles invalid input gracefully', async () => {
    const user = userEvent.setup()
    render(<SearchFilters filters={mockFilters} onChange={mockOnChange} />)

    await user.click(screen.getByText('Filters'))
    const fromInput = screen.getByDisplayValue('2023-01-01')

    // Try to input invalid date
    fireEvent.change(fromInput, { target: { value: 'invalid-date' } })

    expect(mockOnChange).toHaveBeenCalledWith({ from: 'invalid-date' })
  })
})