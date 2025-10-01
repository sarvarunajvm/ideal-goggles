/**
 * Component tests for ResultsGrid
 */

import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ResultsGrid from '../../src/components/ResultsGrid'
import { SearchResultItem } from '@shared/types/api'

const mockResults: SearchResultItem[] = [
  {
    file_id: 1,
    path: '/test/photos/wedding1.jpg',
    folder: '/test/photos',
    filename: 'wedding1.jpg',
    thumb_path: 'cache/thumbs/abc123.webp',
    shot_dt: '2023-06-15T14:30:00Z',
    score: 0.95,
    badges: ['OCR', 'EXIF'],
    snippet: 'Found text: wedding ceremony'
  },
  {
    file_id: 2,
    path: '/test/photos/portrait1.jpg',
    folder: '/test/photos',
    filename: 'portrait1.jpg',
    thumb_path: 'cache/thumbs/def456.webp',
    shot_dt: '2023-07-20T16:45:00Z',
    score: 0.87,
    badges: ['Face', 'Photo-Match'],
    snippet: undefined
  }
]

const mockProps = {
  results: mockResults,
  totalMatches: 2,
  isLoading: false,
  onItemClick: jest.fn(),
  onItemDoubleClick: jest.fn(),
  onItemRightClick: jest.fn()
}

describe('ResultsGrid Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders grid with photo thumbnails', () => {
    render(<ResultsGrid {...mockProps} />)

    // Will fail until ResultsGrid component is implemented
    expect(screen.getByTestId('results-grid')).toBeInTheDocument()
    expect(screen.getAllByRole('img')).toHaveLength(2)
  })

  test('displays photo metadata correctly', () => {
    render(<ResultsGrid {...mockProps} />)

    expect(screen.getByText('wedding1.jpg')).toBeInTheDocument()
    expect(screen.getByText('portrait1.jpg')).toBeInTheDocument()
    // Both items have the same folder, so we expect 2 instances
    const folderElements = screen.getAllByText('/test/photos')
    expect(folderElements).toHaveLength(2)
  })

  test('shows match type badges', () => {
    render(<ResultsGrid {...mockProps} />)

    expect(screen.getByText('OCR')).toBeInTheDocument()
    expect(screen.getByText('EXIF')).toBeInTheDocument()
    expect(screen.getByText('Face')).toBeInTheDocument()
    expect(screen.getByText('Photo-Match')).toBeInTheDocument()
  })

  test('displays relevance scores', () => {
    render(<ResultsGrid {...mockProps} />)

    expect(screen.getByText('95%')).toBeInTheDocument() // 0.95 as percentage
    expect(screen.getByText('87%')).toBeInTheDocument() // 0.87 as percentage
  })

  test('shows OCR snippet when available', () => {
    render(<ResultsGrid {...mockProps} />)

    expect(screen.getByText('Found text: wedding ceremony')).toBeInTheDocument()
  })

  test('handles item click events', async () => {
    const user = userEvent.setup()
    render(<ResultsGrid {...mockProps} />)

    const firstItem = screen.getByTestId('result-item-1')
    await user.click(firstItem)

    expect(mockProps.onItemClick).toHaveBeenCalledWith(mockResults[0])
  })

  test('handles double-click to open in viewer', async () => {
    const user = userEvent.setup()
    render(<ResultsGrid {...mockProps} />)

    const firstItem = screen.getByTestId('result-item-1')
    await user.dblClick(firstItem)

    expect(mockProps.onItemDoubleClick).toHaveBeenCalledWith(mockResults[0])
  })

  test('handles right-click for context menu', async () => {
    render(<ResultsGrid {...mockProps} />)

    const firstItem = screen.getByTestId('result-item-1')
    fireEvent.contextMenu(firstItem)

    expect(mockProps.onItemRightClick).toHaveBeenCalledWith(mockResults[0])
  })

  test('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    render(<ResultsGrid {...mockProps} />)

    const grid = screen.getByTestId('results-grid')
    await user.tab() // Focus on grid

    // Arrow keys should navigate between items
    await user.keyboard('{ArrowRight}')
    expect(screen.getByTestId('result-item-2')).toHaveFocus()

    // Enter should trigger double-click action
    await user.keyboard('{Enter}')
    expect(mockProps.onItemDoubleClick).toHaveBeenCalled()
  })

  test('shows loading state', () => {
    render(<ResultsGrid {...mockProps} isLoading={true} />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  test('shows empty state when no results', () => {
    render(<ResultsGrid {...mockProps} results={[]} totalMatches={0} />)

    expect(screen.getByText(/no photos found/i)).toBeInTheDocument()
  })

  test('displays total match count', () => {
    render(<ResultsGrid {...mockProps} />)

    expect(screen.getByText(/2 photos found/i)).toBeInTheDocument()
  })

  test('thumbnails have minimum 256px size requirement', () => {
    render(<ResultsGrid {...mockProps} />)

    const thumbnails = screen.getAllByRole('img')
    thumbnails.forEach(img => {
      // Thumbnails should meet constitutional requirement
      expect(img).toHaveStyle({ minWidth: '256px' })
    })
  })
})