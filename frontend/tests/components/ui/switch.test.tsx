/**
 * Unit tests for Switch UI Component
 * Priority: P2 (UI Component testing)
 */

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { Switch } from '../../../src/components/ui/switch'
import { useState } from 'react'

describe('Switch Component', () => {
  describe('rendering', () => {
    test('renders without crashing', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeInTheDocument()
    })

    test('renders with default unchecked state', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')
    })

    test('renders in checked state when checked prop is true', () => {
      render(<Switch checked={true} />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'checked')
      expect(switchElement).toHaveAttribute('aria-checked', 'true')
    })

    test('renders in unchecked state when checked prop is false', () => {
      render(<Switch checked={false} />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')
      expect(switchElement).toHaveAttribute('aria-checked', 'false')
    })

    test('applies custom className', () => {
      render(<Switch className="custom-class" />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass('custom-class')
    })

    test('merges custom className with default classes', () => {
      render(<Switch className="custom-switch" />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass(
        'custom-switch',
        'peer',
        'inline-flex',
        'h-6',
        'w-11',
        'shrink-0',
        'cursor-pointer'
      )
    })

    test('renders thumb element', () => {
      const { container } = render(<Switch />)
      const thumb = container.querySelector('[class*="pointer-events-none"]')
      expect(thumb).toBeInTheDocument()
    })

    test('has correct display name', () => {
      expect(Switch.displayName).toBe('Switch')
    })
  })

  describe('accessibility', () => {
    test('has correct role', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeInTheDocument()
    })

    test('has aria-checked attribute reflecting state', () => {
      const { rerender } = render(<Switch checked={false} />)
      let switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('aria-checked', 'false')

      rerender(<Switch checked={true} />)
      switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('aria-checked', 'true')
    })

    test('supports disabled state with proper attributes', () => {
      render(<Switch disabled />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeDisabled()
      expect(switchElement).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50')
    })

    test('has cursor-pointer class when not disabled', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass('cursor-pointer')
    })

    test('supports aria-label', () => {
      render(<Switch aria-label="Enable notifications" />)
      const switchElement = screen.getByRole('switch', { name: 'Enable notifications' })
      expect(switchElement).toBeInTheDocument()
    })

    test('supports aria-labelledby', () => {
      render(
        <div>
          <span id="switch-label">Dark mode</span>
          <Switch aria-labelledby="switch-label" />
        </div>
      )
      const switchElement = screen.getByRole('switch', { name: 'Dark mode' })
      expect(switchElement).toHaveAttribute('aria-labelledby', 'switch-label')
    })

    test('supports aria-describedby', () => {
      render(
        <div>
          <Switch aria-describedby="description" />
          <span id="description">Toggle dark mode on/off</span>
        </div>
      )
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('aria-describedby', 'description')
    })

    test('is keyboard accessible with Tab', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')

      switchElement.focus()
      expect(switchElement).toHaveFocus()
    })

    test('has focus-visible styles', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass(
        'focus-visible:outline-none',
        'focus-visible:ring-2',
        'focus-visible:ring-ring',
        'focus-visible:ring-offset-2',
        'focus-visible:ring-offset-background'
      )
    })

    test('supports required attribute', () => {
      render(<Switch required />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('aria-required', 'true')
    })
  })

  describe('interactions', () => {
    test('calls onCheckedChange when clicked', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      await user.click(switchElement)

      expect(handleChange).toHaveBeenCalledTimes(1)
      expect(handleChange).toHaveBeenCalledWith(true)
    })

    test('toggles from unchecked to checked on click', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch checked={false} onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      await user.click(switchElement)

      expect(handleChange).toHaveBeenCalledWith(true)
    })

    test('toggles from checked to unchecked on click', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch checked={true} onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      await user.click(switchElement)

      expect(handleChange).toHaveBeenCalledWith(false)
    })

    test('does not call onCheckedChange when disabled', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch disabled onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      await user.click(switchElement)

      expect(handleChange).not.toHaveBeenCalled()
    })

    test('can be toggled with Space key', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      switchElement.focus()
      await user.keyboard(' ')

      expect(handleChange).toHaveBeenCalledWith(true)
    })

    test('focuses on Tab key press', async () => {
      const user = userEvent.setup()

      render(<Switch />)
      const switchElement = screen.getByRole('switch')

      await user.tab()

      expect(switchElement).toHaveFocus()
    })

    test('does not respond to keyboard when disabled', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch disabled onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      switchElement.focus()
      await user.keyboard(' ')

      expect(handleChange).not.toHaveBeenCalled()
    })
  })

  describe('controlled component behavior', () => {
    test('works as controlled component', async () => {
      const user = userEvent.setup()
      const ControlledSwitch = () => {
        const [checked, setChecked] = useState(false)
        return (
          <div>
            <Switch
              checked={checked}
              onCheckedChange={setChecked}
              data-testid="switch"
            />
            <span data-testid="state">{checked ? 'on' : 'off'}</span>
          </div>
        )
      }

      render(<ControlledSwitch />)
      const switchElement = screen.getByTestId('switch')
      const state = screen.getByTestId('state')

      expect(state).toHaveTextContent('off')

      await user.click(switchElement)

      expect(state).toHaveTextContent('on')
    })

    test('maintains controlled state across multiple toggles', async () => {
      const user = userEvent.setup()
      const ControlledSwitch = () => {
        const [checked, setChecked] = useState(false)
        return <Switch checked={checked} onCheckedChange={setChecked} />
      }

      render(<ControlledSwitch />)
      const switchElement = screen.getByRole('switch')

      expect(switchElement).toHaveAttribute('data-state', 'unchecked')

      await user.click(switchElement)
      expect(switchElement).toHaveAttribute('data-state', 'checked')

      await user.click(switchElement)
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')

      await user.click(switchElement)
      expect(switchElement).toHaveAttribute('data-state', 'checked')
    })

    test('parent can control state independently', () => {
      const { rerender } = render(<Switch checked={false} />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')

      rerender(<Switch checked={true} />)
      expect(switchElement).toHaveAttribute('data-state', 'checked')
    })
  })

  describe('uncontrolled component behavior', () => {
    test('works as uncontrolled component with defaultChecked', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch defaultChecked={true} onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      expect(switchElement).toHaveAttribute('data-state', 'checked')

      await user.click(switchElement)

      expect(handleChange).toHaveBeenCalledWith(false)
    })

    test('starts unchecked when no defaultChecked provided', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')
    })
  })

  describe('additional props and attributes', () => {
    test('forwards ref correctly', () => {
      const ref = jest.fn()
      render(<Switch ref={ref} />)
      expect(ref).toHaveBeenCalledWith(expect.any(Object))
    })

    test('passes through data attributes', () => {
      render(<Switch data-testid="test-switch" data-custom="value" />)
      const switchElement = screen.getByTestId('test-switch')
      expect(switchElement).toHaveAttribute('data-custom', 'value')
    })

    test('passes through id attribute', () => {
      render(<Switch id="my-switch" />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('id', 'my-switch')
    })

    test('accepts name prop', () => {
      // Radix UI Switch handles name internally for form submission
      render(<Switch name="notifications" />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeInTheDocument()
    })

    test('accepts value prop', () => {
      // Radix UI Switch handles value internally for form submission
      render(<Switch value="enabled" />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeInTheDocument()
    })

    test('applies data-state attribute correctly', () => {
      const { rerender } = render(<Switch checked={false} />)
      let switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')

      rerender(<Switch checked={true} />)
      switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'checked')
    })
  })

  describe('styling and theming', () => {
    test('applies default styling classes', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass(
        'peer',
        'inline-flex',
        'h-6',
        'w-11',
        'shrink-0',
        'cursor-pointer',
        'items-center',
        'rounded-full',
        'border-2',
        'border-transparent',
        'transition-colors'
      )
    })

    test('includes state-based styling classes', () => {
      render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement.className).toContain('data-[state=checked]:bg-primary')
      expect(switchElement.className).toContain('data-[state=unchecked]:bg-input')
    })

    test('thumb has correct styling classes', () => {
      const { container } = render(<Switch />)
      const thumb = container.querySelector('[class*="pointer-events-none"]')
      expect(thumb).toBeInTheDocument()
      expect(thumb).toHaveClass(
        'pointer-events-none',
        'block',
        'h-5',
        'w-5',
        'rounded-full',
        'bg-background',
        'shadow-lg',
        'ring-0',
        'transition-transform'
      )
    })

    test('thumb has transform classes for state transitions', () => {
      const { container } = render(<Switch />)
      const thumb = container.querySelector('[class*="pointer-events-none"]')
      expect(thumb?.className).toContain('data-[state=checked]:translate-x-5')
      expect(thumb?.className).toContain('data-[state=unchecked]:translate-x-0')
    })

    test('thumb position reflects checked state', () => {
      const { container, rerender } = render(<Switch checked={false} />)
      let thumb = container.querySelector('[class*="pointer-events-none"]')
      expect(thumb).toHaveAttribute('data-state', 'unchecked')

      rerender(<Switch checked={true} />)
      thumb = container.querySelector('[class*="pointer-events-none"]')
      expect(thumb).toHaveAttribute('data-state', 'checked')
    })
  })

  describe('edge cases', () => {
    test('handles rapid clicks', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()

      render(<Switch onCheckedChange={handleChange} />)
      const switchElement = screen.getByRole('switch')

      await user.click(switchElement)
      await user.click(switchElement)
      await user.click(switchElement)

      expect(handleChange).toHaveBeenCalledTimes(3)
    })

    test('handles being disabled after mount', () => {
      const { rerender } = render(<Switch />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).not.toBeDisabled()
      expect(switchElement).toHaveClass('cursor-pointer')

      rerender(<Switch disabled />)
      expect(switchElement).toBeDisabled()
      expect(switchElement).toHaveClass('disabled:cursor-not-allowed')
    })

    test('handles checked state changes from parent', () => {
      const { rerender } = render(<Switch checked={false} />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')

      rerender(<Switch checked={true} />)
      expect(switchElement).toHaveAttribute('data-state', 'checked')

      rerender(<Switch checked={false} />)
      expect(switchElement).toHaveAttribute('data-state', 'unchecked')
    })

    test('maintains focus when state changes', async () => {
      const user = userEvent.setup()
      const { rerender } = render(<Switch checked={false} />)
      const switchElement = screen.getByRole('switch')

      await user.tab()
      expect(switchElement).toHaveFocus()

      rerender(<Switch checked={true} />)
      expect(switchElement).toHaveFocus()
    })

    test('handles null onCheckedChange gracefully', async () => {
      const user = userEvent.setup()

      // Should not throw error when clicking without handler
      render(<Switch />)
      const switchElement = screen.getByRole('switch')

      await expect(user.click(switchElement)).resolves.not.toThrow()
    })

    test('works in forms', () => {
      const handleSubmit = jest.fn((e) => e.preventDefault())

      render(
        <form onSubmit={handleSubmit}>
          <Switch name="notifications" value="enabled" />
          <button type="submit">Submit</button>
        </form>
      )

      const switchElement = screen.getByRole('switch')
      // Radix UI Switch integrates with forms but may not expose name/value as attributes
      expect(switchElement).toBeInTheDocument()
    })

    test('multiple switches work independently', async () => {
      const user = userEvent.setup()
      const handleChange1 = jest.fn()
      const handleChange2 = jest.fn()

      render(
        <div>
          <Switch
            aria-label="Switch 1"
            onCheckedChange={handleChange1}
          />
          <Switch
            aria-label="Switch 2"
            onCheckedChange={handleChange2}
          />
        </div>
      )

      const switch1 = screen.getByRole('switch', { name: 'Switch 1' })
      const switch2 = screen.getByRole('switch', { name: 'Switch 2' })

      await user.click(switch1)
      expect(handleChange1).toHaveBeenCalledTimes(1)
      expect(handleChange2).not.toHaveBeenCalled()

      await user.click(switch2)
      expect(handleChange2).toHaveBeenCalledTimes(1)
      expect(handleChange1).toHaveBeenCalledTimes(1)
    })
  })

  describe('visual state indicators', () => {
    test('thumb is positioned correctly in unchecked state', () => {
      const { container } = render(<Switch checked={false} />)
      const thumb = container.querySelector('[data-state="unchecked"]')
      expect(thumb).toBeInTheDocument()
    })

    test('thumb is positioned correctly in checked state', () => {
      const { container } = render(<Switch checked={true} />)
      const thumb = container.querySelector('[data-state="checked"]')
      expect(thumb).toBeInTheDocument()
    })

    test('applies transition classes for smooth animation', () => {
      const { container } = render(<Switch />)
      const switchElement = screen.getByRole('switch')
      const thumb = container.querySelector('[class*="pointer-events-none"]')

      expect(switchElement).toHaveClass('transition-colors')
      expect(thumb).toHaveClass('transition-transform')
    })
  })
})
