/**
 * Comprehensive tests for developerModeStore
 * Tests developer mode toggle functionality
 */

import { renderHook, act } from '@testing-library/react'
import { useDeveloperModeStore } from '../../src/stores/developerModeStore'

describe('developerModeStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useDeveloperModeStore())
    act(() => {
      result.current.setDeveloperMode(false)
    })
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      expect(result.current.isDeveloperMode).toBe(false)
    })
  })

  describe('setDeveloperMode', () => {
    it('should enable developer mode', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result.current.setDeveloperMode(true)
      })

      expect(result.current.isDeveloperMode).toBe(true)
    })

    it('should disable developer mode', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result.current.setDeveloperMode(true)
      })
      expect(result.current.isDeveloperMode).toBe(true)

      act(() => {
        result.current.setDeveloperMode(false)
      })
      expect(result.current.isDeveloperMode).toBe(false)
    })

    it('should toggle between states', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      // Initial: false
      expect(result.current.isDeveloperMode).toBe(false)

      // Enable
      act(() => {
        result.current.setDeveloperMode(true)
      })
      expect(result.current.isDeveloperMode).toBe(true)

      // Disable
      act(() => {
        result.current.setDeveloperMode(false)
      })
      expect(result.current.isDeveloperMode).toBe(false)

      // Enable again
      act(() => {
        result.current.setDeveloperMode(true)
      })
      expect(result.current.isDeveloperMode).toBe(true)
    })

    it('should be idempotent when setting same value', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result.current.setDeveloperMode(true)
        result.current.setDeveloperMode(true)
        result.current.setDeveloperMode(true)
      })

      expect(result.current.isDeveloperMode).toBe(true)

      act(() => {
        result.current.setDeveloperMode(false)
        result.current.setDeveloperMode(false)
        result.current.setDeveloperMode(false)
      })

      expect(result.current.isDeveloperMode).toBe(false)
    })

    it('should handle rapid toggling', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result.current.setDeveloperMode(true)
        result.current.setDeveloperMode(false)
        result.current.setDeveloperMode(true)
        result.current.setDeveloperMode(false)
        result.current.setDeveloperMode(true)
      })

      expect(result.current.isDeveloperMode).toBe(true)
    })
  })

  describe('Store Isolation', () => {
    it('should share state across hook instances', () => {
      const { result: result1 } = renderHook(() => useDeveloperModeStore())
      const { result: result2 } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result1.current.setDeveloperMode(true)
      })

      // Both hooks should see the same state
      expect(result1.current.isDeveloperMode).toBe(true)
      expect(result2.current.isDeveloperMode).toBe(true)
    })

    it('should update all hook instances when state changes', () => {
      const { result: result1 } = renderHook(() => useDeveloperModeStore())
      const { result: result2 } = renderHook(() => useDeveloperModeStore())
      const { result: result3 } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result2.current.setDeveloperMode(true)
      })

      expect(result1.current.isDeveloperMode).toBe(true)
      expect(result2.current.isDeveloperMode).toBe(true)
      expect(result3.current.isDeveloperMode).toBe(true)

      act(() => {
        result3.current.setDeveloperMode(false)
      })

      expect(result1.current.isDeveloperMode).toBe(false)
      expect(result2.current.isDeveloperMode).toBe(false)
      expect(result3.current.isDeveloperMode).toBe(false)
    })
  })

  describe('Edge Cases', () => {
    it('should handle truthy values correctly', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result.current.setDeveloperMode(1 as any)
      })
      expect(result.current.isDeveloperMode).toBe(1 as any)

      act(() => {
        result.current.setDeveloperMode('yes' as any)
      })
      expect(result.current.isDeveloperMode).toBe('yes' as any)
    })

    it('should handle falsy values correctly', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result.current.setDeveloperMode(true)
      })
      expect(result.current.isDeveloperMode).toBe(true)

      act(() => {
        result.current.setDeveloperMode(0 as any)
      })
      expect(result.current.isDeveloperMode).toBe(0 as any)

      act(() => {
        result.current.setDeveloperMode('' as any)
      })
      expect(result.current.isDeveloperMode).toBe('' as any)

      act(() => {
        result.current.setDeveloperMode(null as any)
      })
      expect(result.current.isDeveloperMode).toBe(null as any)
    })
  })

  describe('Real-world Usage Scenarios', () => {
    it('should enable developer mode for debugging', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      // Simulate user enabling developer mode
      act(() => {
        result.current.setDeveloperMode(true)
      })

      expect(result.current.isDeveloperMode).toBe(true)

      // User can now see developer features
      // Simulate user disabling it when done
      act(() => {
        result.current.setDeveloperMode(false)
      })

      expect(result.current.isDeveloperMode).toBe(false)
    })

    it('should persist developer mode state during navigation', () => {
      // Simulate first component using the store
      const { result: page1 } = renderHook(() => useDeveloperModeStore())

      act(() => {
        page1.current.setDeveloperMode(true)
      })

      // Simulate navigation to another page
      const { result: page2 } = renderHook(() => useDeveloperModeStore())

      // Developer mode should still be enabled
      expect(page2.current.isDeveloperMode).toBe(true)
    })

    it('should allow checking developer mode status without changing it', () => {
      const { result } = renderHook(() => useDeveloperModeStore())

      act(() => {
        result.current.setDeveloperMode(true)
      })

      // Multiple reads shouldn't change the state
      const status1 = result.current.isDeveloperMode
      const status2 = result.current.isDeveloperMode
      const status3 = result.current.isDeveloperMode

      expect(status1).toBe(true)
      expect(status2).toBe(true)
      expect(status3).toBe(true)
      expect(result.current.isDeveloperMode).toBe(true)
    })
  })
})
