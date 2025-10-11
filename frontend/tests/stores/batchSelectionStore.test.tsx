/**
 * Comprehensive tests for batchSelectionStore
 * Tests all batch selection state management functionality
 */

import { renderHook, act } from '@testing-library/react'
import { useBatchSelectionStore } from '../../src/stores/batchSelectionStore'

describe('batchSelectionStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useBatchSelectionStore())
    act(() => {
      result.current.disableSelectionMode()
    })
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      expect(result.current.selectionMode).toBe(false)
      expect(result.current.selectedIds).toEqual(new Set())
      expect(result.current.getSelectedCount()).toBe(0)
      expect(result.current.getSelectedIds()).toEqual([])
    })
  })

  describe('toggleSelectionMode', () => {
    it('should toggle selection mode on', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelectionMode()
      })

      expect(result.current.selectionMode).toBe(true)
    })

    it('should toggle selection mode off and clear selections', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('id1')
        result.current.toggleSelection('id2')
      })

      expect(result.current.getSelectedCount()).toBe(2)

      act(() => {
        result.current.toggleSelectionMode()
      })

      expect(result.current.selectionMode).toBe(false)
      expect(result.current.getSelectedCount()).toBe(0)
    })

    it('should maintain selections when toggling on', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelectionMode()
        result.current.toggleSelection('id1')
      })

      expect(result.current.getSelectedCount()).toBe(1)

      act(() => {
        result.current.toggleSelectionMode()
      })

      expect(result.current.getSelectedCount()).toBe(0)
    })

    it('should toggle multiple times correctly', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelectionMode() // On
      })
      expect(result.current.selectionMode).toBe(true)

      act(() => {
        result.current.toggleSelectionMode() // Off
      })
      expect(result.current.selectionMode).toBe(false)

      act(() => {
        result.current.toggleSelectionMode() // On
      })
      expect(result.current.selectionMode).toBe(true)
    })
  })

  describe('enableSelectionMode', () => {
    it('should enable selection mode', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
      })

      expect(result.current.selectionMode).toBe(true)
    })

    it('should not affect selections when enabling', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('id1')
        result.current.disableSelectionMode()
        result.current.enableSelectionMode()
      })

      expect(result.current.selectionMode).toBe(true)
      expect(result.current.getSelectedCount()).toBe(0) // Cleared on disable
    })

    it('should be idempotent', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.enableSelectionMode()
        result.current.enableSelectionMode()
      })

      expect(result.current.selectionMode).toBe(true)
    })
  })

  describe('disableSelectionMode', () => {
    it('should disable selection mode and clear selections', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('id1')
        result.current.toggleSelection('id2')
      })

      expect(result.current.getSelectedCount()).toBe(2)

      act(() => {
        result.current.disableSelectionMode()
      })

      expect(result.current.selectionMode).toBe(false)
      expect(result.current.selectedIds).toEqual(new Set())
      expect(result.current.getSelectedCount()).toBe(0)
    })

    it('should be idempotent', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.disableSelectionMode()
        result.current.disableSelectionMode()
        result.current.disableSelectionMode()
      })

      expect(result.current.selectionMode).toBe(false)
      expect(result.current.getSelectedCount()).toBe(0)
    })
  })

  describe('toggleSelection', () => {
    it('should add item to selection', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('photo1')
      })

      expect(result.current.isSelected('photo1')).toBe(true)
      expect(result.current.getSelectedCount()).toBe(1)
    })

    it('should remove item from selection', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('photo1')
      })

      expect(result.current.isSelected('photo1')).toBe(true)

      act(() => {
        result.current.toggleSelection('photo1')
      })

      expect(result.current.isSelected('photo1')).toBe(false)
      expect(result.current.getSelectedCount()).toBe(0)
    })

    it('should handle multiple items', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('photo1')
        result.current.toggleSelection('photo2')
        result.current.toggleSelection('photo3')
      })

      expect(result.current.getSelectedCount()).toBe(3)
      expect(result.current.isSelected('photo1')).toBe(true)
      expect(result.current.isSelected('photo2')).toBe(true)
      expect(result.current.isSelected('photo3')).toBe(true)
    })

    it('should toggle same item multiple times', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('photo1')
      })
      expect(result.current.isSelected('photo1')).toBe(true)

      act(() => {
        result.current.toggleSelection('photo1')
      })
      expect(result.current.isSelected('photo1')).toBe(false)

      act(() => {
        result.current.toggleSelection('photo1')
      })
      expect(result.current.isSelected('photo1')).toBe(true)
    })

    it('should work even when selection mode is off', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelection('photo1')
      })

      expect(result.current.isSelected('photo1')).toBe(true)
      expect(result.current.selectionMode).toBe(false)
    })

    it('should handle numeric string IDs', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelection('1')
        result.current.toggleSelection('2')
        result.current.toggleSelection('100')
      })

      expect(result.current.getSelectedCount()).toBe(3)
      expect(result.current.isSelected('1')).toBe(true)
      expect(result.current.isSelected('100')).toBe(true)
    })

    it('should handle special characters in IDs', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelection('photo-123')
        result.current.toggleSelection('photo_456')
        result.current.toggleSelection('photo.789')
      })

      expect(result.current.getSelectedCount()).toBe(3)
      expect(result.current.isSelected('photo-123')).toBe(true)
    })
  })

  describe('selectAll', () => {
    it('should select all provided IDs', () => {
      const { result } = renderHook(() => useBatchSelectionStore())
      const ids = ['photo1', 'photo2', 'photo3', 'photo4', 'photo5']

      act(() => {
        result.current.selectAll(ids)
      })

      expect(result.current.getSelectedCount()).toBe(5)
      expect(result.current.selectionMode).toBe(true)
      ids.forEach((id) => {
        expect(result.current.isSelected(id)).toBe(true)
      })
    })

    it('should replace existing selections', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('old1')
        result.current.toggleSelection('old2')
      })

      expect(result.current.getSelectedCount()).toBe(2)

      act(() => {
        result.current.selectAll(['new1', 'new2', 'new3'])
      })

      expect(result.current.getSelectedCount()).toBe(3)
      expect(result.current.isSelected('old1')).toBe(false)
      expect(result.current.isSelected('new1')).toBe(true)
    })

    it('should handle empty array', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.selectAll([])
      })

      expect(result.current.getSelectedCount()).toBe(0)
      expect(result.current.selectionMode).toBe(true)
    })

    it('should enable selection mode', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      expect(result.current.selectionMode).toBe(false)

      act(() => {
        result.current.selectAll(['photo1'])
      })

      expect(result.current.selectionMode).toBe(true)
    })

    it('should handle large number of items', () => {
      const { result } = renderHook(() => useBatchSelectionStore())
      const ids = Array.from({ length: 1000 }, (_, i) => `photo${i}`)

      act(() => {
        result.current.selectAll(ids)
      })

      expect(result.current.getSelectedCount()).toBe(1000)
      expect(result.current.isSelected('photo0')).toBe(true)
      expect(result.current.isSelected('photo999')).toBe(true)
    })

    it('should handle duplicate IDs in array', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.selectAll(['photo1', 'photo2', 'photo1', 'photo3', 'photo2'])
      })

      expect(result.current.getSelectedCount()).toBe(3) // Set removes duplicates
    })
  })

  describe('clearSelection', () => {
    it('should clear all selections', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('photo1')
        result.current.toggleSelection('photo2')
        result.current.toggleSelection('photo3')
      })

      expect(result.current.getSelectedCount()).toBe(3)

      act(() => {
        result.current.clearSelection()
      })

      expect(result.current.getSelectedCount()).toBe(0)
      expect(result.current.selectedIds).toEqual(new Set())
    })

    it('should not affect selection mode', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.enableSelectionMode()
        result.current.toggleSelection('photo1')
      })

      expect(result.current.selectionMode).toBe(true)

      act(() => {
        result.current.clearSelection()
      })

      expect(result.current.selectionMode).toBe(true)
      expect(result.current.getSelectedCount()).toBe(0)
    })

    it('should be idempotent', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.clearSelection()
        result.current.clearSelection()
        result.current.clearSelection()
      })

      expect(result.current.getSelectedCount()).toBe(0)
    })
  })

  describe('isSelected', () => {
    it('should return true for selected items', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelection('photo1')
      })

      expect(result.current.isSelected('photo1')).toBe(true)
    })

    it('should return false for non-selected items', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      expect(result.current.isSelected('photo1')).toBe(false)

      act(() => {
        result.current.toggleSelection('photo2')
      })

      expect(result.current.isSelected('photo1')).toBe(false)
      expect(result.current.isSelected('photo2')).toBe(true)
    })

    it('should handle non-existent IDs', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      expect(result.current.isSelected('nonexistent')).toBe(false)
    })
  })

  describe('getSelectedCount', () => {
    it('should return correct count', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      expect(result.current.getSelectedCount()).toBe(0)

      act(() => {
        result.current.toggleSelection('photo1')
      })
      expect(result.current.getSelectedCount()).toBe(1)

      act(() => {
        result.current.toggleSelection('photo2')
        result.current.toggleSelection('photo3')
      })
      expect(result.current.getSelectedCount()).toBe(3)

      act(() => {
        result.current.toggleSelection('photo2')
      })
      expect(result.current.getSelectedCount()).toBe(2)
    })

    it('should return 0 when all cleared', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.selectAll(['p1', 'p2', 'p3'])
        result.current.clearSelection()
      })

      expect(result.current.getSelectedCount()).toBe(0)
    })
  })

  describe('getSelectedIds', () => {
    it('should return array of selected IDs', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelection('photo1')
        result.current.toggleSelection('photo2')
        result.current.toggleSelection('photo3')
      })

      const selectedIds = result.current.getSelectedIds()
      expect(selectedIds).toHaveLength(3)
      expect(selectedIds).toContain('photo1')
      expect(selectedIds).toContain('photo2')
      expect(selectedIds).toContain('photo3')
    })

    it('should return empty array when nothing selected', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      expect(result.current.getSelectedIds()).toEqual([])
    })

    it('should return new array each time', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.toggleSelection('photo1')
      })

      const arr1 = result.current.getSelectedIds()
      const arr2 = result.current.getSelectedIds()

      expect(arr1).toEqual(arr2)
      expect(arr1).not.toBe(arr2) // Different references
    })

    it('should preserve order from Set iteration', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.selectAll(['photo1', 'photo2', 'photo3'])
      })

      const ids = result.current.getSelectedIds()
      expect(ids).toEqual(['photo1', 'photo2', 'photo3'])
    })
  })

  describe('Complex Workflows', () => {
    it('should handle typical user workflow', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      // User enables selection mode
      act(() => {
        result.current.enableSelectionMode()
      })
      expect(result.current.selectionMode).toBe(true)

      // User selects a few items
      act(() => {
        result.current.toggleSelection('photo1')
        result.current.toggleSelection('photo2')
        result.current.toggleSelection('photo3')
      })
      expect(result.current.getSelectedCount()).toBe(3)

      // User deselects one
      act(() => {
        result.current.toggleSelection('photo2')
      })
      expect(result.current.getSelectedCount()).toBe(2)

      // User selects all
      act(() => {
        result.current.selectAll(['photo1', 'photo2', 'photo3', 'photo4', 'photo5'])
      })
      expect(result.current.getSelectedCount()).toBe(5)

      // User cancels selection mode
      act(() => {
        result.current.disableSelectionMode()
      })
      expect(result.current.selectionMode).toBe(false)
      expect(result.current.getSelectedCount()).toBe(0)
    })

    it('should handle select all, then deselect one by one', () => {
      const { result } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result.current.selectAll(['p1', 'p2', 'p3'])
      })
      expect(result.current.getSelectedCount()).toBe(3)

      act(() => {
        result.current.toggleSelection('p1')
      })
      expect(result.current.getSelectedCount()).toBe(2)

      act(() => {
        result.current.toggleSelection('p2')
      })
      expect(result.current.getSelectedCount()).toBe(1)

      act(() => {
        result.current.toggleSelection('p3')
      })
      expect(result.current.getSelectedCount()).toBe(0)
    })
  })

  describe('Store Isolation', () => {
    it('should share state across hook instances', () => {
      const { result: result1 } = renderHook(() => useBatchSelectionStore())
      const { result: result2 } = renderHook(() => useBatchSelectionStore())

      act(() => {
        result1.current.enableSelectionMode()
        result1.current.toggleSelection('photo1')
      })

      // Both hooks should see the same state
      expect(result2.current.selectionMode).toBe(true)
      expect(result2.current.isSelected('photo1')).toBe(true)
      expect(result2.current.getSelectedCount()).toBe(1)
    })
  })
})
