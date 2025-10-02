/**
 * Unit tests for Separator UI Component
 * Priority: P2 (UI Component testing)
 */

import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Separator } from '../../../src/components/ui/separator'

describe('Separator Component', () => {
  test('renders with default props', () => {
    render(<Separator data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toBeInTheDocument()
    expect(separator).toHaveAttribute('data-orientation', 'horizontal')
  })

  test('renders with horizontal orientation', () => {
    render(<Separator orientation="horizontal" data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveAttribute('data-orientation', 'horizontal')
  })

  test('renders with vertical orientation', () => {
    render(<Separator orientation="vertical" data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveAttribute('data-orientation', 'vertical')
  })

  test('applies custom className', () => {
    render(<Separator className="custom-class" data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('custom-class')
  })

  test('applies correct CSS classes for horizontal orientation', () => {
    render(<Separator orientation="horizontal" data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('shrink-0', 'bg-border', 'h-[1px]', 'w-full')
  })

  test('applies correct CSS classes for vertical orientation', () => {
    render(<Separator orientation="vertical" data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('shrink-0', 'bg-border', 'h-full', 'w-[1px]')
  })

  test('is decorative by default', () => {
    render(<Separator data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveAttribute('role', 'none')
  })

  test('can be non-decorative', () => {
    render(<Separator decorative={false} data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveAttribute('role', 'separator')
  })

  test('passes through additional props', () => {
    render(
      <Separator
        data-testid="separator"
        data-custom="test-value"
        id="test-separator"
      />
    )

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveAttribute('data-custom', 'test-value')
    expect(separator).toHaveAttribute('id', 'test-separator')
  })

  test('has correct display name', () => {
    expect(Separator.displayName).toBeDefined()
  })

  test('merges custom className with default classes', () => {
    render(<Separator className="custom-border" data-testid="separator" />)

    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('custom-border', 'shrink-0', 'bg-border')
  })
})