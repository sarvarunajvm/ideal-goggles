/**
 * Unit tests for VirtualGrid component
 */

import { render, screen, fireEvent, act } from '@testing-library/react'

// Mock useVirtualGrid hook to control virtualization behavior
const useVirtualGridMock = jest.fn()
jest.mock('../../src/hooks/useVirtualGrid', () => ({
  useVirtualGrid: (...args: any[]) => useVirtualGridMock(...args),
}))

// Mock VirtualGridItem to avoid framer-motion/IO complexity and expose click handling
jest.mock('../../src/components/VirtualGrid/VirtualGridItem', () => ({
  VirtualGridItem: ({ children, onClick, itemId }: any) => (
    <div data-testid={`grid-item-${itemId ?? 'no-id'}`} onClick={onClick}>
      {children}
    </div>
  ),
}))

// Mock LoadingSkeleton to a simple identifiable output
jest.mock('../../src/components/VirtualGrid/LoadingSkeleton', () => ({
  LoadingSkeleton: ({ count = 12 }: any) => (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div data-testid="loading-skeleton" key={i} />
      ))}
    </>
  ),
}))

import { VirtualGrid } from '../../src/components/VirtualGrid/VirtualGrid'

type Item = { id: string; label?: string }

const renderItem = (item: Item, index: number) => (
  <div data-testid={`rendered-${item.id}`}>#{index}-{item.id}</div>
)

describe('VirtualGrid', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default virtualization: one row with three indices, one out-of-range
    useVirtualGridMock.mockReturnValue({
      parentRef: { current: null },
      virtualItems: [
        {
          key: 'row-0',
          start: 0,
          items: [{ index: 0 }, { index: 1 }, { index: 99 }],
        },
      ],
      totalSize: 720,
    })
  })

  test('renders loading skeleton when loading is true', () => {
    render(
      <VirtualGrid<Item>
        items={[]}
        renderItem={renderItem}
        loading={true}
      />
    )

    // Should render 12 skeleton items by default
    const skeletons = screen.getAllByTestId('loading-skeleton')
    expect(skeletons).toHaveLength(12)
  })

  test('shows empty state when there are no items', () => {
    render(<VirtualGrid<Item> items={[]} renderItem={renderItem} />)

    expect(screen.getByText(/No items to display/i)).toBeInTheDocument()
  })

  test('renders items via renderItem and handles item clicks', () => {
    const items: Item[] = [
      { id: 'a', label: 'Item A' },
      { id: 'b', label: 'Item B' },
    ]
    const onItemClick = jest.fn()

    const { container } = render(
      <VirtualGrid<Item> items={items} renderItem={renderItem} onItemClick={onItemClick} />
    )

    // Should not render for out-of-range index (99)
    expect(screen.queryByTestId('grid-item-no-id')).not.toBeInTheDocument()

    // Renders exactly the two items
    expect(screen.getByTestId('grid-item-a')).toBeInTheDocument()
    expect(screen.getByTestId('grid-item-b')).toBeInTheDocument()
    expect(screen.getByTestId('rendered-a')).toHaveTextContent('#0-a')
    expect(screen.getByTestId('rendered-b')).toHaveTextContent('#1-b')

    // Click triggers onItemClick with item and index
    fireEvent.click(screen.getByTestId('grid-item-b'))
    expect(onItemClick).toHaveBeenCalledTimes(1)
    expect(onItemClick).toHaveBeenCalledWith(items[1], 1)

    // Parent virtual container should have contain: strict
    const parent = Array.from(container.querySelectorAll('div')).find(
      (el) => (el as HTMLDivElement).style?.contain === 'strict'
    ) as HTMLDivElement
    expect(parent).toBeTruthy()
    expect(parent!.style.contain).toBe('strict')

    // Height should be driven by totalSize from the hook
    const heightContainer = container.querySelector('div[style*="position: relative"]') as HTMLDivElement
    expect(heightContainer).toBeTruthy()
    expect(heightContainer!.style.height).toBe('720px')
  })

  test('clicks are safe when onItemClick is undefined', () => {
    const items: Item[] = [{ id: 'a' }]

    render(<VirtualGrid<Item> items={items} renderItem={renderItem} />)

    // Clicking should not throw and simply do nothing
    expect(() => {
      fireEvent.click(screen.getByTestId('grid-item-a'))
    }).not.toThrow()
  })

  test('updates responsive column count based on container width and handles resize', () => {
    const items: Item[] = [{ id: 'a' }, { id: 'b' }]

    const { container } = render(
      <VirtualGrid<Item>
        items={items}
        renderItem={renderItem}
        columnCount={4}
        gap={24}
      />
    )

    // Set container width to trigger 3 columns: floor((800+24)/(250+24)) = 3
    const containerDiv = container.querySelector('div.w-full') as HTMLDivElement
    expect(containerDiv).toBeTruthy()

    Object.defineProperty(containerDiv, 'offsetWidth', { value: 800, configurable: true })

    act(() => {
      window.dispatchEvent(new Event('resize'))
    })

    // Find the grid element and assert computed template columns reflect 3 columns
    const grid = container.querySelector('div.grid') as HTMLDivElement
    expect(grid).toBeTruthy()
    // JSDOM may normalize 0 to 0px; assert prefix and key parts
    expect(grid!.style.gridTemplateColumns).toContain('repeat(3,')
    expect(grid!.style.gridTemplateColumns).toContain('minmax(')

    // Row wrapper should translate by virtualRow.start (0px in our mock)
    const rowWrapper = grid.parentElement as HTMLDivElement
    expect(rowWrapper).toBeTruthy()
    expect(rowWrapper!.style.transform).toBe('translateY(0px)')
    // Padding applied to inner grid container
    expect(grid!.style.padding).toBe('0px 4px')
  })

  test('caps responsive columns at provided columnCount', () => {
    const items: Item[] = [{ id: 'a' }, { id: 'b' }, { id: 'c' }]

    const { container } = render(
      <VirtualGrid<Item>
        items={items}
        renderItem={renderItem}
        columnCount={2}
        gap={24}
      />
    )

    const containerDiv = container.querySelector('div.w-full') as HTMLDivElement
    Object.defineProperty(containerDiv, 'offsetWidth', { value: 2000, configurable: true })

    act(() => {
      window.dispatchEvent(new Event('resize'))
    })

    const grid = container.querySelector('div.grid') as HTMLDivElement
    expect(grid).toBeTruthy()
    expect(grid!.style.gridTemplateColumns).toContain('repeat(2,')
  })

  test('registers and cleans up resize event listener', () => {
    const addSpy = jest.spyOn(window, 'addEventListener')
    const removeSpy = jest.spyOn(window, 'removeEventListener')

    const { unmount } = render(
      <VirtualGrid<Item> items={[{ id: 'a' }]} renderItem={renderItem} />
    )

    // Effect should register listener
    expect(addSpy).toHaveBeenCalledWith('resize', expect.any(Function))

    unmount()

    // Cleanup should remove listener
    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function))

    addSpy.mockRestore()
    removeSpy.mockRestore()
  })
})
