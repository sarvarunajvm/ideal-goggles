import { useRef, useEffect, useState } from 'react';
import { useVirtualGrid } from '../../hooks/useVirtualGrid';
import { VirtualGridItem } from './VirtualGridItem';
import { LoadingSkeleton } from './LoadingSkeleton';

export interface GridItem {
  id: string;
  [key: string]: any;
}

interface VirtualGridProps<T extends GridItem> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  columnCount?: number;
  itemWidth?: number;
  itemHeight?: number;
  gap?: number;
  loading?: boolean;
  onItemClick?: (item: T, index: number) => void;
}

export function VirtualGrid<T extends GridItem>({
  items,
  renderItem,
  columnCount = 4,
  itemWidth = 280,
  itemHeight = 360,
  gap = 24,
  loading = false,
  onItemClick,
}: VirtualGridProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate responsive column count based on container width
  const [responsiveColumns, setResponsiveColumns] = useState(columnCount);

  useEffect(() => {
    const updateColumns = () => {
      if (!containerRef.current) return;

      const containerWidth = containerRef.current.offsetWidth;
      const minItemWidth = 250;
      const calculatedColumns = Math.max(
        1,
        Math.floor((containerWidth + gap) / (minItemWidth + gap))
      );

      setResponsiveColumns(Math.min(calculatedColumns, columnCount));
    };

    updateColumns();
    window.addEventListener('resize', updateColumns);
    return () => window.removeEventListener('resize', updateColumns);
  }, [columnCount, gap]);

  const { parentRef, virtualItems, totalSize } = useVirtualGrid({
    itemCount: items.length,
    columnCount: responsiveColumns,
    itemWidth,
    itemHeight,
    gap,
    overscan: 3,
  });

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <LoadingSkeleton count={12} />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-center">
        <div className="space-y-2">
          <p className="text-lg font-medium text-muted-foreground">
            No items to display
          </p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full">
      <div
        ref={parentRef}
        className="h-[calc(100vh-300px)] overflow-auto p-2"
        style={{
          contain: 'strict',
        }}
      >
        <div
          style={{
            height: `${totalSize}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {virtualItems.map(virtualRow => (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div
                className="grid gap-6"
                style={{
                  gridTemplateColumns: `repeat(${responsiveColumns}, minmax(0, 1fr))`,
                  padding: '0 4px',
                }}
              >
                {virtualRow.items.map(({ index, columnIndex }) => {
                  const item = items[index];
                  if (!item) return null;

                  return (
                    <VirtualGridItem
                      key={item.id}
                      itemId={item.id}
                      onClick={() => onItemClick?.(item, index)}
                    >
                      {renderItem(item, index)}
                    </VirtualGridItem>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
