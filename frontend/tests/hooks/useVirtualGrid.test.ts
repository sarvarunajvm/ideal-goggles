/**
 * Comprehensive tests for useVirtualGrid hook
 * Achieves 100% coverage
 * Priority: P0 (Critical UI infrastructure)
 */

import { renderHook, act } from '@testing-library/react';
import { useVirtualGrid } from '../../src/hooks/useVirtualGrid';

// Mock @tanstack/react-virtual
const mockGetVirtualItems = jest.fn();
const mockGetTotalSize = jest.fn();
const mockScrollToIndex = jest.fn();
const mockMeasureElement = jest.fn();

jest.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: jest.fn((options) => {
    // Store options for testing
    (useVirtualizer as any).lastOptions = options;

    return {
      getVirtualItems: mockGetVirtualItems,
      getTotalSize: mockGetTotalSize,
      scrollToIndex: mockScrollToIndex,
      measureElement: mockMeasureElement,
    };
  }),
}));

const { useVirtualizer } = require('@tanstack/react-virtual');

describe('useVirtualGrid', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetVirtualItems.mockReturnValue([]);
    mockGetTotalSize.mockReturnValue(0);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Hook Initialization', () => {
    test('initializes with basic parameters', () => {
      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.parentRef).toBeDefined();
      expect(result.current.parentRef.current).toBeNull();
      expect(result.current.virtualItems).toEqual([]);
      expect(result.current.totalSize).toBe(0);
      expect(result.current.scrollToIndex).toBe(mockScrollToIndex);
      expect(result.current.measureElement).toBe(mockMeasureElement);
    });

    test('initializes with custom gap', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
          gap: 24,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(150 + 24); // itemHeight + gap
    });

    test('initializes with custom overscan', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
          overscan: 10,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.overscan).toBe(10);
    });

    test('uses default gap of 16 when not provided', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(150 + 16); // itemHeight + default gap
    });

    test('uses default overscan of 5 when not provided', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.overscan).toBe(5);
    });
  });

  describe('Row Count Calculation', () => {
    test('calculates correct row count for evenly divisible items', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(25); // 100 / 4 = 25 rows
    });

    test('rounds up row count for non-evenly divisible items', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 103,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(26); // Math.ceil(103 / 4) = 26 rows
    });

    test('handles single column', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 50,
          columnCount: 1,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(50); // 50 / 1 = 50 rows
    });

    test('handles single item', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 1,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(1); // Math.ceil(1 / 4) = 1 row
    });

    test('handles zero items', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 0,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(0); // Math.ceil(0 / 4) = 0 rows
    });
  });

  describe('Scroll Element Configuration', () => {
    test('provides scroll element getter function', () => {
      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      const scrollElement = options.getScrollElement();

      expect(scrollElement).toBeNull(); // parentRef.current is null initially
      expect(scrollElement).toBe(result.current.parentRef.current);
    });

    test('returns parent element when ref is set', () => {
      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      // Simulate ref attachment
      const mockElement = document.createElement('div');
      act(() => {
        (result.current.parentRef as any).current = mockElement;
      });

      const options = (useVirtualizer as any).lastOptions;
      const scrollElement = options.getScrollElement();

      expect(scrollElement).toBe(mockElement);
    });
  });

  describe('Size Estimation', () => {
    test('estimates size correctly with default gap', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(166); // 150 + 16
    });

    test('estimates size correctly with custom gap', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
          gap: 32,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(182); // 150 + 32
    });

    test('estimates size correctly with zero gap', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
          gap: 0,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(150); // 150 + 0
    });

    test('estimates size with large item height', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 500,
          gap: 20,
        })
      );

      const options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(520); // 500 + 20
    });
  });

  describe('Virtual Items Calculation', () => {
    test('calculates virtual items for full row', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
        { index: 1, start: 166, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 8,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toHaveLength(2);

      // First row should have 4 items (indices 0-3)
      expect(result.current.virtualItems[0].items).toHaveLength(4);
      expect(result.current.virtualItems[0].items[0]).toEqual({
        index: 0,
        columnIndex: 0,
        rowIndex: 0,
      });
      expect(result.current.virtualItems[0].items[3]).toEqual({
        index: 3,
        columnIndex: 3,
        rowIndex: 0,
      });

      // Second row should have 4 items (indices 4-7)
      expect(result.current.virtualItems[1].items).toHaveLength(4);
      expect(result.current.virtualItems[1].items[0]).toEqual({
        index: 4,
        columnIndex: 0,
        rowIndex: 1,
      });
      expect(result.current.virtualItems[1].items[3]).toEqual({
        index: 7,
        columnIndex: 3,
        rowIndex: 1,
      });
    });

    test('calculates virtual items for partial row', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
        { index: 1, start: 166, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 6, // Only 6 items total
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toHaveLength(2);

      // First row should have 4 items
      expect(result.current.virtualItems[0].items).toHaveLength(4);

      // Second row should have only 2 items (indices 4-5)
      expect(result.current.virtualItems[1].items).toHaveLength(2);
      expect(result.current.virtualItems[1].items[0]).toEqual({
        index: 4,
        columnIndex: 0,
        rowIndex: 1,
      });
      expect(result.current.virtualItems[1].items[1]).toEqual({
        index: 5,
        columnIndex: 1,
        rowIndex: 1,
      });
    });

    test('calculates column indices correctly', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 5,
          columnCount: 5,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const items = result.current.virtualItems[0].items;
      expect(items).toHaveLength(5);

      // Verify column indices are 0, 1, 2, 3, 4
      items.forEach((item, idx) => {
        expect(item.columnIndex).toBe(idx);
      });
    });

    test('handles single item row', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 1,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toHaveLength(1);
      expect(result.current.virtualItems[0].items).toHaveLength(1);
      expect(result.current.virtualItems[0].items[0]).toEqual({
        index: 0,
        columnIndex: 0,
        rowIndex: 0,
      });
    });

    test('handles empty virtual items', () => {
      mockGetVirtualItems.mockReturnValue([]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toEqual([]);
    });

    test('preserves original virtual row properties', () => {
      mockGetVirtualItems.mockReturnValue([
        {
          index: 0,
          start: 0,
          size: 166,
          lane: 0,
          key: 'row-0'
        },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 4,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems[0]).toMatchObject({
        index: 0,
        start: 0,
        size: 166,
        lane: 0,
        key: 'row-0',
        items: expect.any(Array),
      });
    });
  });

  describe('Edge Cases', () => {
    test('handles zero items', () => {
      mockGetVirtualItems.mockReturnValue([]);
      mockGetTotalSize.mockReturnValue(0);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 0,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toEqual([]);
      expect(result.current.totalSize).toBe(0);
    });

    test('handles single item', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);
      mockGetTotalSize.mockReturnValue(166);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 1,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toHaveLength(1);
      expect(result.current.virtualItems[0].items).toHaveLength(1);
      expect(result.current.totalSize).toBe(166);
    });

    test('handles large dataset (10,000 items)', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
        { index: 1, start: 166, size: 166 },
        { index: 2, start: 332, size: 166 },
      ]);
      mockGetTotalSize.mockReturnValue(416500);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 10000,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      // Should only render visible rows, not all 2500 rows
      expect(result.current.virtualItems).toHaveLength(3);
      expect(result.current.totalSize).toBe(416500);

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(2500); // Math.ceil(10000 / 4)
    });

    test('handles single column layout', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
        { index: 1, start: 166, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 10,
          columnCount: 1,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      // Each row should have exactly 1 item
      result.current.virtualItems.forEach((row) => {
        expect(row.items).toHaveLength(1);
        expect(row.items[0].columnIndex).toBe(0);
      });
    });

    test('handles many columns (10 columns)', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 25,
          columnCount: 10,
          itemWidth: 100,
          itemHeight: 150,
        })
      );

      // First row should have all 10 items
      expect(result.current.virtualItems[0].items).toHaveLength(10);

      // Verify column indices
      result.current.virtualItems[0].items.forEach((item, idx) => {
        expect(item.columnIndex).toBe(idx);
      });
    });

    test('handles items count equal to column count', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 4,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toHaveLength(1);
      expect(result.current.virtualItems[0].items).toHaveLength(4);

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(1); // Exactly one row
    });

    test('handles items count less than column count', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 2,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toHaveLength(1);
      expect(result.current.virtualItems[0].items).toHaveLength(2);

      const options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(1); // Still one row
    });
  });

  describe('Total Size', () => {
    test('returns total size from virtualizer', () => {
      mockGetTotalSize.mockReturnValue(5000);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.totalSize).toBe(5000);
    });

    test('updates when total size changes', () => {
      mockGetTotalSize.mockReturnValue(5000);

      const { result, rerender } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.totalSize).toBe(5000);

      // Simulate size change
      mockGetTotalSize.mockReturnValue(8000);
      rerender();

      expect(result.current.totalSize).toBe(8000);
    });

    test('handles zero total size', () => {
      mockGetTotalSize.mockReturnValue(0);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 0,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.totalSize).toBe(0);
    });
  });

  describe('Scroll and Measurement Functions', () => {
    test('exposes scrollToIndex function', () => {
      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.scrollToIndex).toBe(mockScrollToIndex);
      expect(typeof result.current.scrollToIndex).toBe('function');
    });

    test('exposes measureElement function', () => {
      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.measureElement).toBe(mockMeasureElement);
      expect(typeof result.current.measureElement).toBe('function');
    });

    test('can call scrollToIndex', () => {
      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      act(() => {
        result.current.scrollToIndex(10);
      });

      expect(mockScrollToIndex).toHaveBeenCalledWith(10);
    });

    test('can call measureElement', () => {
      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const mockElement = document.createElement('div');

      act(() => {
        result.current.measureElement(mockElement);
      });

      expect(mockMeasureElement).toHaveBeenCalledWith(mockElement);
    });
  });

  describe('Re-rendering and Updates', () => {
    test('updates when itemCount changes', () => {
      const { rerender } = renderHook(
        (props) =>
          useVirtualGrid({
            itemCount: props.itemCount,
            columnCount: 4,
            itemWidth: 200,
            itemHeight: 150,
          }),
        { initialProps: { itemCount: 100 } }
      );

      let options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(25); // 100 / 4

      rerender({ itemCount: 200 });

      options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(50); // 200 / 4
    });

    test('updates when columnCount changes', () => {
      const { rerender } = renderHook(
        (props) =>
          useVirtualGrid({
            itemCount: 100,
            columnCount: props.columnCount,
            itemWidth: 200,
            itemHeight: 150,
          }),
        { initialProps: { columnCount: 4 } }
      );

      let options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(25); // 100 / 4

      rerender({ columnCount: 5 });

      options = (useVirtualizer as any).lastOptions;
      expect(options.count).toBe(20); // 100 / 5
    });

    test('updates virtual items when getVirtualItems changes', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result, rerender } = renderHook(() =>
        useVirtualGrid({
          itemCount: 8,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      expect(result.current.virtualItems).toHaveLength(1);

      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
        { index: 1, start: 166, size: 166 },
      ]);

      rerender();

      expect(result.current.virtualItems).toHaveLength(2);
    });

    test('recalculates items when columnCount changes', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result, rerender } = renderHook(
        (props) =>
          useVirtualGrid({
            itemCount: 10,
            columnCount: props.columnCount,
            itemWidth: 200,
            itemHeight: 150,
          }),
        { initialProps: { columnCount: 5 } }
      );

      expect(result.current.virtualItems[0].items).toHaveLength(5);

      rerender({ columnCount: 2 });

      // Now first row should have only 2 items
      expect(result.current.virtualItems[0].items).toHaveLength(2);
    });

    test('updates when itemHeight changes', () => {
      const { rerender } = renderHook(
        (props) =>
          useVirtualGrid({
            itemCount: 100,
            columnCount: 4,
            itemWidth: 200,
            itemHeight: props.itemHeight,
          }),
        { initialProps: { itemHeight: 150 } }
      );

      let options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(166); // 150 + 16

      rerender({ itemHeight: 200 });

      options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(216); // 200 + 16
    });

    test('updates when gap changes', () => {
      const { rerender } = renderHook(
        (props) =>
          useVirtualGrid({
            itemCount: 100,
            columnCount: 4,
            itemWidth: 200,
            itemHeight: 150,
            gap: props.gap,
          }),
        { initialProps: { gap: 16 } }
      );

      let options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(166); // 150 + 16

      rerender({ gap: 24 });

      options = (useVirtualizer as any).lastOptions;
      expect(options.estimateSize()).toBe(174); // 150 + 24
    });
  });

  describe('Row Index Calculation', () => {
    test('calculates correct row indices for multiple rows', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
        { index: 1, start: 166, size: 166 },
        { index: 2, start: 332, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 12,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      // Check that all items in row 0 have rowIndex 0
      result.current.virtualItems[0].items.forEach((item) => {
        expect(item.rowIndex).toBe(0);
      });

      // Check that all items in row 1 have rowIndex 1
      result.current.virtualItems[1].items.forEach((item) => {
        expect(item.rowIndex).toBe(1);
      });

      // Check that all items in row 2 have rowIndex 2
      result.current.virtualItems[2].items.forEach((item) => {
        expect(item.rowIndex).toBe(2);
      });
    });

    test('item indices are sequential across rows', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
        { index: 1, start: 166, size: 166 },
      ]);

      const { result } = renderHook(() =>
        useVirtualGrid({
          itemCount: 8,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      // Row 0: items 0, 1, 2, 3
      expect(result.current.virtualItems[0].items.map(i => i.index)).toEqual([0, 1, 2, 3]);

      // Row 1: items 4, 5, 6, 7
      expect(result.current.virtualItems[1].items.map(i => i.index)).toEqual([4, 5, 6, 7]);
    });
  });

  describe('Memory and Performance', () => {
    test('does not create unnecessary objects on re-render', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result, rerender } = renderHook(() =>
        useVirtualGrid({
          itemCount: 4,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const firstRef = result.current.parentRef;
      rerender();
      const secondRef = result.current.parentRef;

      // parentRef should be stable across re-renders
      expect(firstRef).toBe(secondRef);
    });

    test('useMemo prevents unnecessary virtualItems recalculation', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result, rerender } = renderHook(() =>
        useVirtualGrid({
          itemCount: 4,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const firstVirtualItems = result.current.virtualItems;

      // Re-render without changing dependencies
      rerender();

      const secondVirtualItems = result.current.virtualItems;

      // Should be the same reference due to useMemo
      expect(firstVirtualItems).toBe(secondVirtualItems);
    });

    test('virtualItems update when dependencies change', () => {
      mockGetVirtualItems.mockReturnValue([
        { index: 0, start: 0, size: 166 },
      ]);

      const { result, rerender } = renderHook(
        (props) =>
          useVirtualGrid({
            itemCount: props.itemCount,
            columnCount: 4,
            itemWidth: 200,
            itemHeight: 150,
          }),
        { initialProps: { itemCount: 4 } }
      );

      const firstVirtualItems = result.current.virtualItems;

      // Change itemCount (a dependency)
      rerender({ itemCount: 8 });

      const secondVirtualItems = result.current.virtualItems;

      // Should be different references when dependencies change
      expect(firstVirtualItems).not.toBe(secondVirtualItems);
    });
  });

  describe('Integration with useVirtualizer', () => {
    test('passes all required options to useVirtualizer', () => {
      renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
          gap: 20,
          overscan: 8,
        })
      );

      expect(useVirtualizer).toHaveBeenCalled();

      const options = (useVirtualizer as any).lastOptions;
      expect(options).toHaveProperty('count');
      expect(options).toHaveProperty('getScrollElement');
      expect(options).toHaveProperty('estimateSize');
      expect(options).toHaveProperty('overscan');

      expect(typeof options.getScrollElement).toBe('function');
      expect(typeof options.estimateSize).toBe('function');
    });

    test('useVirtualizer is called on each render', () => {
      const { rerender } = renderHook(() =>
        useVirtualGrid({
          itemCount: 100,
          columnCount: 4,
          itemWidth: 200,
          itemHeight: 150,
        })
      );

      const callCount = (useVirtualizer as jest.Mock).mock.calls.length;

      rerender();

      expect((useVirtualizer as jest.Mock).mock.calls.length).toBeGreaterThan(callCount);
    });
  });
});
