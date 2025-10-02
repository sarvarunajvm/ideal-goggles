/**
 * Unit tests for Checkbox UI Component
 * Priority: P2 (UI Component testing)
 */

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { Checkbox } from '../../../src/components/ui/checkbox'
import { useState } from 'react'

describe('Checkbox Component', () => {
  describe('rendering', () => {
    test('renders without crashing', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeInTheDocument()
    })

    test('renders with default unchecked state', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
    })

    test('renders in checked state when checked prop is true', () => {
      render(<Checkbox checked={true} />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'checked')
      expect(checkbox).toHaveAttribute('aria-checked', 'true')
    })

    test('renders in unchecked state when checked prop is false', () => {
      render(<Checkbox checked={false} />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
      expect(checkbox).toHaveAttribute('aria-checked', 'false')
    })

    test('renders in indeterminate state', () => {
      render(<Checkbox checked="indeterminate" />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'indeterminate')
      expect(checkbox).toHaveAttribute('aria-checked', 'mixed')
    })

    test('applies custom className', () => {
      render(<Checkbox className="custom-class" />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveClass('custom-class')
    })

    test('merges custom className with default classes', () => {
      render(<Checkbox className="custom-border" />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveClass('custom-border', 'peer', 'h-4', 'w-4', 'shrink-0', 'rounded-sm')
    })

    test('renders check icon when checked', () => {
      const { container } = render(<Checkbox checked={true} />)
      // The Check icon from lucide-react should be rendered
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveClass('h-4', 'w-4')
    })

    test('has correct display name', () => {
      expect(Checkbox.displayName).toBe('Checkbox')
    })
  })

  describe('accessibility', () => {
    test('has correct role', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeInTheDocument()
    })

    test('has aria-checked attribute reflecting state', () => {
      const { rerender } = render(<Checkbox checked={false} />)
      let checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('aria-checked', 'false')

      rerender(<Checkbox checked={true} />)
      checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('aria-checked', 'true')
    })

    test('has aria-checked="mixed" for indeterminate state', () => {
      render(<Checkbox checked="indeterminate" />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('aria-checked', 'mixed')
    })

    test('supports disabled state with proper attributes', () => {
      render(<Checkbox disabled />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeDisabled()
      expect(checkbox).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50')
    })

    test('supports aria-label', () => {
      render(<Checkbox aria-label="Accept terms" />)
      const checkbox = screen.getByRole('checkbox', { name: 'Accept terms' })
      expect(checkbox).toBeInTheDocument()
    })

    test('supports aria-labelledby', () => {
      render(
        <div>
          <span id="checkbox-label">Accept terms</span>
          <Checkbox aria-labelledby="checkbox-label" />
        </div>
      )
      const checkbox = screen.getByRole('checkbox', { name: 'Accept terms' })
      expect(checkbox).toHaveAttribute('aria-labelledby', 'checkbox-label')
    })

    test('supports aria-describedby', () => {
      render(
        <div>
          <Checkbox aria-describedby="description" />
          <span id="description">This is required</span>
        </div>
      )
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('aria-describedby', 'description')
    })

    test('is keyboard accessible with Tab', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')

      // Checkbox should be focusable
      checkbox.focus()
      expect(checkbox).toHaveFocus()
    })

    test('has focus-visible styles', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveClass(
        'focus-visible:outline-none',
        'focus-visible:ring-2',
        'focus-visible:ring-ring',
        'focus-visible:ring-offset-2'
      )
    })
  })

  describe('interactions', () => {
    test('calls onCheckedChange when clicked', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      await user.click(checkbox)

      expect(handleChange).toHaveBeenCalledTimes(1)
      expect(handleChange).toHaveBeenCalledWith(true)
    })

    test('toggles from unchecked to checked on click', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox checked={false} onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      await user.click(checkbox)

      expect(handleChange).toHaveBeenCalledWith(true)
    })

    test('toggles from checked to unchecked on click', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox checked={true} onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      await user.click(checkbox)

      expect(handleChange).toHaveBeenCalledWith(false)
    })

    test('does not call onCheckedChange when disabled', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox disabled onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      await user.click(checkbox)

      expect(handleChange).not.toHaveBeenCalled()
    })

    test('can be toggled with Space key', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      checkbox.focus()
      await user.keyboard(' ')

      expect(handleChange).toHaveBeenCalledWith(true)
    })

    test('focuses on Tab key press', async () => {
      const user = userEvent.setup()

      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')

      await user.tab()

      expect(checkbox).toHaveFocus()
    })

    test('does not respond to keyboard when disabled', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox disabled onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      checkbox.focus()
      await user.keyboard(' ')

      expect(handleChange).not.toHaveBeenCalled()
    })
  })

  describe('controlled component behavior', () => {
    test('works as controlled component', async () => {
      const user = userEvent.setup()
      const ControlledCheckbox = () => {
        const [checked, setChecked] = useState(false)
        return (
          <div>
            <Checkbox
              checked={checked}
              onCheckedChange={setChecked}
              data-testid="checkbox"
            />
            <span data-testid="state">{checked ? 'checked' : 'unchecked'}</span>
          </div>
        )
      }

      render(<ControlledCheckbox />)
      const checkbox = screen.getByTestId('checkbox')
      const state = screen.getByTestId('state')

      expect(state).toHaveTextContent('unchecked')

      await user.click(checkbox)

      expect(state).toHaveTextContent('checked')
    })

    test('maintains controlled state across multiple toggles', async () => {
      const user = userEvent.setup()
      const ControlledCheckbox = () => {
        const [checked, setChecked] = useState(false)
        return (
          <Checkbox
            checked={checked}
            onCheckedChange={setChecked}
          />
        )
      }

      render(<ControlledCheckbox />)
      const checkbox = screen.getByRole('checkbox')

      expect(checkbox).toHaveAttribute('data-state', 'unchecked')

      await user.click(checkbox)
      expect(checkbox).toHaveAttribute('data-state', 'checked')

      await user.click(checkbox)
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')

      await user.click(checkbox)
      expect(checkbox).toHaveAttribute('data-state', 'checked')
    })
  })

  describe('uncontrolled component behavior', () => {
    test('works as uncontrolled component with defaultChecked', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox defaultChecked={true} onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      expect(checkbox).toHaveAttribute('data-state', 'checked')

      await user.click(checkbox)

      expect(handleChange).toHaveBeenCalledWith(false)
    })

    test('starts unchecked when no defaultChecked provided', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
    })
  })

  describe('additional props and attributes', () => {
    test('forwards ref correctly', () => {
      const ref = jest.fn()
      render(<Checkbox ref={ref} />)
      expect(ref).toHaveBeenCalledWith(expect.any(Object))
    })

    test('passes through data attributes', () => {
      render(<Checkbox data-testid="test-checkbox" data-custom="value" />)
      const checkbox = screen.getByTestId('test-checkbox')
      expect(checkbox).toHaveAttribute('data-custom', 'value')
    })

    test('passes through id attribute', () => {
      render(<Checkbox id="my-checkbox" />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('id', 'my-checkbox')
    })

    test('accepts name prop', () => {
      // Radix UI Checkbox handles name internally for form submission
      render(<Checkbox name="terms" />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeInTheDocument()
    })

    test('passes through value attribute', () => {
      render(<Checkbox value="accepted" />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('value', 'accepted')
    })

    test('passes through required attribute', () => {
      render(<Checkbox required />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('aria-required', 'true')
    })

    test('applies data-state attribute correctly', () => {
      const { rerender } = render(<Checkbox checked={false} />)
      let checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')

      rerender(<Checkbox checked={true} />)
      checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'checked')

      rerender(<Checkbox checked="indeterminate" />)
      checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'indeterminate')
    })
  })

  describe('styling and theming', () => {
    test('applies default styling classes', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveClass(
        'peer',
        'h-4',
        'w-4',
        'shrink-0',
        'rounded-sm',
        'border',
        'border-primary',
        'ring-offset-background'
      )
    })

    test('includes state-based styling classes', () => {
      render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox.className).toContain('data-[state=checked]:bg-primary')
      expect(checkbox.className).toContain('data-[state=checked]:text-primary-foreground')
    })

    test('check indicator has correct classes', () => {
      const { container } = render(<Checkbox checked={true} />)
      // Find the indicator span
      const indicator = container.querySelector('[class*="flex items-center justify-center"]')
      expect(indicator).toBeInTheDocument()
      expect(indicator).toHaveClass('flex', 'items-center', 'justify-center', 'text-current')
    })
  })

  describe('edge cases', () => {
    test('handles rapid clicks', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Checkbox onCheckedChange={handleChange} />)
      const checkbox = screen.getByRole('checkbox')

      await user.click(checkbox)
      await user.click(checkbox)
      await user.click(checkbox)

      expect(handleChange).toHaveBeenCalledTimes(3)
    })

    test('handles being disabled after mount', () => {
      const { rerender } = render(<Checkbox />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).not.toBeDisabled()

      rerender(<Checkbox disabled />)
      expect(checkbox).toBeDisabled()
    })

    test('handles checked state changes from parent', () => {
      const { rerender } = render(<Checkbox checked={false} />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')

      rerender(<Checkbox checked={true} />)
      expect(checkbox).toHaveAttribute('data-state', 'checked')

      rerender(<Checkbox checked="indeterminate" />)
      expect(checkbox).toHaveAttribute('data-state', 'indeterminate')

      rerender(<Checkbox checked={false} />)
      expect(checkbox).toHaveAttribute('data-state', 'unchecked')
    })

    test('maintains focus when state changes', async () => {
      const user = userEvent.setup()
      const { rerender } = render(<Checkbox checked={false} />)
      const checkbox = screen.getByRole('checkbox')

      await user.tab()
      expect(checkbox).toHaveFocus()

      rerender(<Checkbox checked={true} />)
      expect(checkbox).toHaveFocus()
    })
  })
})
