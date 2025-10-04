import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useMemo } from 'react';

interface UseVirtualGridOptions {
  itemCount: number;
  columnCount: number;
  itemWidth: number;
  itemHeight: number;
  gap?: number;
  overscan?: number;
}

export function useVirtualGrid({
  itemCount,
  columnCount,
  itemWidth: _itemWidth,
  itemHeight,
  gap = 16,
  overscan = 5,
}: UseVirtualGridOptions) {
  const parentRef = useRef<HTMLDivElement>(null);

  // Calculate row count based on total items and columns
  const rowCount = Math.ceil(itemCount / columnCount);

  // Create row virtualizer
  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight + gap,
    overscan,
  });

  // Get items for each visible row
  const getItemsForRow = (rowIndex: number) => {
    const items = [];
    const startIndex = rowIndex * columnCount;
    const endIndex = Math.min(startIndex + columnCount, itemCount);

    for (let i = startIndex; i < endIndex; i++) {
      items.push({
        index: i,
        columnIndex: i % columnCount,
        rowIndex,
      });
    }

    return items;
  };

  // Calculate virtual items with their positions
  const virtualItems = useMemo(
    () =>
      rowVirtualizer.getVirtualItems().map(virtualRow => ({
        ...virtualRow,
        items: getItemsForRow(virtualRow.index),
      })),
    [rowVirtualizer.getVirtualItems(), columnCount, itemCount]
  );

  return {
    parentRef,
    virtualItems,
    totalSize: rowVirtualizer.getTotalSize(),
    scrollToIndex: rowVirtualizer.scrollToIndex,
    measureElement: rowVirtualizer.measureElement,
  };
}
