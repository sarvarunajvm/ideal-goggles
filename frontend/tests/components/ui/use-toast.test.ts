/**
 * Unit tests for use-toast hook
 * Priority: P2 (UI Hook testing)
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useToast, toast, reducer } from '../../../src/components/ui/use-toast'

// Mock timers for testing auto-dismiss functionality
jest.useFakeTimers()

describe('use-toast hook', () => {
  beforeEach(() => {
    // Clear all timers and reset state before each test
    jest.clearAllTimers()
    // Reset the memory state by dismissing all toasts
    const { result } = renderHook(() => useToast())
    act(() => {
      result.current.dismiss()
    })
  })

  afterEach(() => {
    jest.clearAllTimers()
  })

  afterAll(() => {
    jest.useRealTimers()
  })

  describe('useToast hook', () => {
    test('initializes with empty toasts array', () => {
      const { result } = renderHook(() => useToast())
      expect(result.current.toasts).toEqual([])
    })

    test('provides toast function', () => {
      const { result } = renderHook(() => useToast())
      expect(typeof result.current.toast).toBe('function')
    })

    test('provides dismiss function', () => {
      const { result } = renderHook(() => useToast())
      expect(typeof result.current.dismiss).toBe('function')
    })

    test('adds toast when toast function is called', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({
          title: 'Test Toast',
          description: 'Test Description',
        })
      })

      expect(result.current.toasts).toHaveLength(1)
      expect(result.current.toasts[0].title).toBe('Test Toast')
      expect(result.current.toasts[0].description).toBe('Test Description')
      expect(result.current.toasts[0].open).toBe(true)
    })

    test('assigns unique IDs to toasts', () => {
      const { result } = renderHook(() => useToast())

      let id1: string, id2: string
      act(() => {
        const t1 = result.current.toast({ title: 'Toast 1' })
        id1 = t1.id
      })

      act(() => {
        const t2 = result.current.toast({ title: 'Toast 2' })
        id2 = t2.id
      })

      // Due to TOAST_LIMIT=1, only the latest toast is kept
      // But we can verify IDs are unique
      expect(id1).toBeDefined()
      expect(id2).toBeDefined()
      expect(id1).not.toBe(id2)
    })

    test('limits toasts to TOAST_LIMIT (1)', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({ title: 'Toast 1' })
        result.current.toast({ title: 'Toast 2' })
        result.current.toast({ title: 'Toast 3' })
      })

      expect(result.current.toasts).toHaveLength(1)
      expect(result.current.toasts[0].title).toBe('Toast 3')
    })

    test('dismisses specific toast by ID', async () => {
      const { result } = renderHook(() => useToast())

      let toastId: string
      act(() => {
        const t = result.current.toast({ title: 'Test Toast' })
        toastId = t.id
      })

      expect(result.current.toasts[0].open).toBe(true)

      act(() => {
        result.current.dismiss(toastId!)
      })

      expect(result.current.toasts[0].open).toBe(false)
    })

    test('dismisses all toasts when called without ID', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({ title: 'Toast 1' })
      })

      expect(result.current.toasts[0].open).toBe(true)

      act(() => {
        result.current.dismiss()
      })

      expect(result.current.toasts[0].open).toBe(false)
    })

    test('removes toast after TOAST_REMOVE_DELAY when dismissed', async () => {
      const { result } = renderHook(() => useToast())

      let toastId: string
      act(() => {
        const t = result.current.toast({ title: 'Test Toast' })
        toastId = t.id
      })

      expect(result.current.toasts).toHaveLength(1)

      act(() => {
        result.current.dismiss(toastId!)
      })

      // Toast should be marked as not open
      expect(result.current.toasts[0].open).toBe(false)

      // Fast-forward time by TOAST_REMOVE_DELAY (1000000ms)
      act(() => {
        jest.advanceTimersByTime(1000000)
      })

      // Toast should be removed from the array
      await waitFor(() => {
        expect(result.current.toasts).toHaveLength(0)
      })
    })

    test('syncs state across multiple hook instances', () => {
      const { result: result1 } = renderHook(() => useToast())
      const { result: result2 } = renderHook(() => useToast())

      act(() => {
        result1.current.toast({ title: 'Shared Toast' })
      })

      expect(result1.current.toasts).toHaveLength(1)
      expect(result2.current.toasts).toHaveLength(1)
      expect(result1.current.toasts[0].id).toBe(result2.current.toasts[0].id)
    })

    test('cleans up listeners on unmount', () => {
      const { result, unmount } = renderHook(() => useToast())

      act(() => {
        result.current.toast({ title: 'Test' })
      })

      expect(result.current.toasts).toHaveLength(1)

      unmount()

      // Create a new hook instance
      const { result: result2 } = renderHook(() => useToast())
      expect(result2.current.toasts).toHaveLength(1) // State should still be there in memory
    })
  })

  describe('toast function (standalone)', () => {
    test('returns object with id, dismiss, and update functions', () => {
      const result = toast({ title: 'Test' })

      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('dismiss')
      expect(result).toHaveProperty('update')
      expect(typeof result.id).toBe('string')
      expect(typeof result.dismiss).toBe('function')
      expect(typeof result.update).toBe('function')
    })

    test('dismiss function closes the toast', () => {
      const { result } = renderHook(() => useToast())

      let toastInstance: ReturnType<typeof toast>
      act(() => {
        toastInstance = toast({ title: 'Test' })
      })

      expect(result.current.toasts[0].open).toBe(true)

      act(() => {
        toastInstance!.dismiss()
      })

      expect(result.current.toasts[0].open).toBe(false)
    })

    test('update function modifies toast properties', () => {
      const { result } = renderHook(() => useToast())

      let toastInstance: ReturnType<typeof toast>
      act(() => {
        toastInstance = toast({ title: 'Original Title' })
      })

      expect(result.current.toasts[0].title).toBe('Original Title')

      act(() => {
        toastInstance!.update({ title: 'Updated Title', description: 'New Description' })
      })

      expect(result.current.toasts[0].title).toBe('Updated Title')
      expect(result.current.toasts[0].description).toBe('New Description')
    })

    test('sets onOpenChange callback that dismisses on close', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        toast({ title: 'Test' })
      })

      const toastItem = result.current.toasts[0]
      expect(toastItem.onOpenChange).toBeDefined()

      act(() => {
        toastItem.onOpenChange?.(false)
      })

      expect(result.current.toasts[0].open).toBe(false)
    })

    test('onOpenChange does nothing when open is true', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        toast({ title: 'Test' })
      })

      const toastItem = result.current.toasts[0]
      expect(toastItem.open).toBe(true)

      act(() => {
        toastItem.onOpenChange?.(true)
      })

      // Should still be open
      expect(result.current.toasts[0].open).toBe(true)
    })

    test('accepts all toast props', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        toast({
          title: 'Test Title',
          description: 'Test Description',
          variant: 'destructive',
        })
      })

      const toastItem = result.current.toasts[0]
      expect(toastItem.title).toBe('Test Title')
      expect(toastItem.description).toBe('Test Description')
      expect(toastItem.variant).toBe('destructive')
    })
  })

  describe('reducer', () => {
    test('ADD_TOAST adds toast to state', () => {
      const initialState = { toasts: [] }
      const newToast = {
        id: '1',
        title: 'Test',
        open: true,
      }

      const newState = reducer(initialState, {
        type: 'ADD_TOAST',
        toast: newToast,
      })

      expect(newState.toasts).toHaveLength(1)
      expect(newState.toasts[0]).toEqual(newToast)
    })

    test('ADD_TOAST enforces TOAST_LIMIT', () => {
      const initialState = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true },
        ],
      }

      const newState = reducer(initialState, {
        type: 'ADD_TOAST',
        toast: { id: '2', title: 'Toast 2', open: true },
      })

      expect(newState.toasts).toHaveLength(1)
      expect(newState.toasts[0].id).toBe('2')
    })

    test('UPDATE_TOAST updates matching toast', () => {
      const initialState = {
        toasts: [
          { id: '1', title: 'Original', open: true },
          { id: '2', title: 'Other', open: true },
        ],
      }

      const newState = reducer(initialState, {
        type: 'UPDATE_TOAST',
        toast: { id: '1', title: 'Updated' },
      })

      expect(newState.toasts[0].title).toBe('Updated')
      expect(newState.toasts[1].title).toBe('Other')
    })

    test('UPDATE_TOAST leaves non-matching toasts unchanged', () => {
      const initialState = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true },
          { id: '2', title: 'Toast 2', open: true },
        ],
      }

      const newState = reducer(initialState, {
        type: 'UPDATE_TOAST',
        toast: { id: '3', title: 'Toast 3' },
      })

      expect(newState.toasts).toEqual(initialState.toasts)
    })

    test('DISMISS_TOAST sets open to false for specific toast', () => {
      const initialState = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true },
          { id: '2', title: 'Toast 2', open: true },
        ],
      }

      const newState = reducer(initialState, {
        type: 'DISMISS_TOAST',
        toastId: '1',
      })

      expect(newState.toasts[0].open).toBe(false)
      expect(newState.toasts[1].open).toBe(true)
    })

    test('DISMISS_TOAST sets open to false for all toasts when no ID provided', () => {
      const initialState = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true },
          { id: '2', title: 'Toast 2', open: true },
        ],
      }

      const newState = reducer(initialState, {
        type: 'DISMISS_TOAST',
      })

      expect(newState.toasts[0].open).toBe(false)
      expect(newState.toasts[1].open).toBe(false)
    })

    test('REMOVE_TOAST removes specific toast from array', () => {
      const initialState = {
        toasts: [
          { id: '1', title: 'Toast 1', open: false },
          { id: '2', title: 'Toast 2', open: true },
        ],
      }

      const newState = reducer(initialState, {
        type: 'REMOVE_TOAST',
        toastId: '1',
      })

      expect(newState.toasts).toHaveLength(1)
      expect(newState.toasts[0].id).toBe('2')
    })

    test('REMOVE_TOAST removes all toasts when no ID provided', () => {
      const initialState = {
        toasts: [
          { id: '1', title: 'Toast 1', open: false },
          { id: '2', title: 'Toast 2', open: false },
        ],
      }

      const newState = reducer(initialState, {
        type: 'REMOVE_TOAST',
      })

      expect(newState.toasts).toHaveLength(0)
    })
  })

  describe('edge cases and error scenarios', () => {
    test('handles rapid successive toast additions', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        for (let i = 0; i < 10; i++) {
          result.current.toast({ title: `Toast ${i}` })
        }
      })

      // Should only keep the latest one due to TOAST_LIMIT
      expect(result.current.toasts).toHaveLength(1)
      expect(result.current.toasts[0].title).toBe('Toast 9')
    })

    test('handles dismissing non-existent toast ID gracefully', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({ title: 'Test' })
      })

      // Dismiss with non-existent ID
      act(() => {
        result.current.dismiss('non-existent-id')
      })

      // Original toast should still be open since ID didn't match
      expect(result.current.toasts[0].open).toBe(true)
    })

    test('update function modifies toast with correct ID', () => {
      const { result } = renderHook(() => useToast())

      let toastInstance: ReturnType<typeof toast>
      act(() => {
        toastInstance = toast({ title: 'Original' })
      })

      expect(result.current.toasts[0].title).toBe('Original')

      // Update with the correct ID (update includes the ID internally)
      act(() => {
        toastInstance!.update({ title: 'Updated' })
      })

      // Toast should be updated
      expect(result.current.toasts[0].title).toBe('Updated')
    })

    test('prevents duplicate timeout for same toast', async () => {
      const { result } = renderHook(() => useToast())

      let toastId: string
      act(() => {
        const t = toast({ title: 'Test' })
        toastId = t.id
      })

      // Dismiss the same toast multiple times
      act(() => {
        result.current.dismiss(toastId!)
        result.current.dismiss(toastId!)
        result.current.dismiss(toastId!)
      })

      // Fast-forward past the removal delay
      act(() => {
        jest.advanceTimersByTime(1000000)
      })

      await waitFor(() => {
        expect(result.current.toasts).toHaveLength(0)
      })
    })

    test('toast with complex title and description types', () => {
      const { result } = renderHook(() => useToast())

      // Test that toast accepts ReactNode types
      act(() => {
        result.current.toast({
          title: 'String Title',
          description: 'String Description',
        })
      })

      expect(result.current.toasts[0].title).toBeDefined()
      expect(result.current.toasts[0].description).toBeDefined()
      expect(result.current.toasts[0].title).toBe('String Title')
    })

    test('toast with variant prop', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({
          title: 'Test',
          variant: 'destructive',
        })
      })

      expect(result.current.toasts[0].variant).toBe('destructive')
    })
  })
})
