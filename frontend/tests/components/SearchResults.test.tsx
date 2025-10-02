/**
 * Unit tests for SearchResults Component
 * Priority: P1 (Core search results display)
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import SearchResults from '../../src/components/SearchResults'
import { SearchResponse } from '../../src/services/apiClient'

// Mock the apiClient module
jest.mock('../../src/services/apiClient', () => ({
  getThumbnailBaseUrl: () => 'http://localhost:5555/thumbnails',
}))

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
})

// Mock window.open
const mockWindowOpen = jest.fn()
Object.defineProperty(window, 'open', {
  value: mockWindowOpen,
  writable: true,
})

const mockEmptyResults: SearchResponse = {
  query: 'test query',
  total_matches: 0,
  items: [],
  took_ms: 45,
}

const mockResults: SearchResponse = {
  query: 'vacation photos',
  total_matches: 25,
  took_ms: 120,
  items: [
    {
      file_id: '1',
      filename: 'beach_sunset.jpg',
      path: '/photos/vacation/beach_sunset.jpg',
      folder: '/photos/vacation',
      thumb_path: 'thumbnails/beach_sunset_thumb.jpg',
      shot_dt: '2023-07-15T18:30:00Z',
      score: 0.95,
      badges: ['visual', 'semantic'],
      snippet: 'beautiful sunset over the ocean',
    },
    {
      file_id: '2',
      filename: 'family_photo.jpg',
      path: '/photos/vacation/family_photo.jpg',
      folder: '/photos/vacation',
      thumb_path: null,
      shot_dt: null,
      score: 0.87,
      badges: ['face', 'text'],
      snippet: null,
    },
    {
      file_id: '3',
      filename: 'mountain_view.png',
      path: '/photos/vacation/mountains/mountain_view.png',
      folder: '/photos/vacation/mountains',
      thumb_path: 'thumbnails/mountain_view_thumb.jpg',
      shot_dt: '2023-07-20T10:15:00Z',
      score: 0.78,
      badges: ['filename', 'metadata'],
      snippet: 'spectacular mountain landscape',
    },
  ],
}

describe('SearchResults Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Empty Results', () => {
    test('displays empty state when no results found', () => {
      render(<SearchResults results={mockEmptyResults} />)

      expect(screen.getByText('🔍')).toBeInTheDocument()
      expect(screen.getByText('No photos found')).toBeInTheDocument()
      expect(screen.getByText('Try a different search term or adjust your filters.')).toBeInTheDocument()
    })

    test('does not display results grid when empty', () => {
      render(<SearchResults results={mockEmptyResults} />)

      expect(screen.queryByText('photos found')).not.toBeInTheDocument()
      expect(screen.queryByRole('img')).not.toBeInTheDocument()
    })
  })

  describe('Results Display', () => {
    test('displays correct results header information', () => {
      render(<SearchResults results={mockResults} />)

      expect(screen.getByText('25 photos found')).toBeInTheDocument()
      expect(screen.getByText('Search for "vacation photos" completed in 120ms')).toBeInTheDocument()
    })

    test('handles singular vs plural photo text correctly', () => {
      const singleResult = { ...mockResults, total_matches: 1, items: [mockResults.items[0]] }
      render(<SearchResults results={singleResult} />)

      expect(screen.getByText('1 photo found')).toBeInTheDocument()
    })

    test('displays all search result items', () => {
      render(<SearchResults results={mockResults} />)

      expect(screen.getByText('beach_sunset.jpg')).toBeInTheDocument()
      expect(screen.getByText('family_photo.jpg')).toBeInTheDocument()
      expect(screen.getByText('mountain_view.png')).toBeInTheDocument()
    })

    test('formats numbers correctly with locale', () => {
      const manyResults = { ...mockResults, total_matches: 1234 }
      render(<SearchResults results={manyResults} />)

      expect(screen.getByText('1,234 photos found')).toBeInTheDocument()
    })
  })

  describe('Image Display', () => {
    test('displays images with thumbnails', () => {
      render(<SearchResults results={mockResults} />)

      const images = screen.getAllByRole('img')
      expect(images).toHaveLength(2) // Only items with thumb_path

      expect(images[0]).toHaveAttribute('src', 'http://localhost:5555/thumbnails/thumbnails/beach_sunset_thumb.jpg')
      expect(images[0]).toHaveAttribute('alt', 'beach_sunset.jpg')
      expect(images[1]).toHaveAttribute('src', 'http://localhost:5555/thumbnails/thumbnails/mountain_view_thumb.jpg')
    })

    test('displays camera icon when no thumbnail available', () => {
      render(<SearchResults results={mockResults} />)

      const cameraIcons = screen.getAllByText('📷')
      expect(cameraIcons.length).toBeGreaterThan(0)

      // Check that one of them is visible (not hidden)
      const visibleIcon = cameraIcons.find(icon => !icon.classList.contains('hidden'))
      expect(visibleIcon).toBeInTheDocument()
    })

    test('handles image load errors', () => {
      render(<SearchResults results={mockResults} />)

      const image = screen.getAllByRole('img')[0]
      fireEvent.error(image)

      expect(image.style.display).toBe('none')
    })
  })

  describe('File Information', () => {
    test('displays file information correctly', () => {
      render(<SearchResults results={mockResults} />)

      // Check folder names (last part of path)
      expect(screen.getByText('vacation')).toBeInTheDocument()
      expect(screen.getByText('mountains')).toBeInTheDocument()

      // Check formatted dates
      expect(screen.getByText('7/15/2023')).toBeInTheDocument() // beach_sunset
      expect(screen.getByText('7/20/2023')).toBeInTheDocument() // mountain_view

      // Check scores
      expect(screen.getByText('Score: 95.0%')).toBeInTheDocument()
      expect(screen.getByText('Score: 87.0%')).toBeInTheDocument()
      expect(screen.getByText('Score: 78.0%')).toBeInTheDocument()
    })

    test('handles missing date information', () => {
      render(<SearchResults results={mockResults} />)

      // family_photo.jpg has null shot_dt, so date section should not appear
      const familyPhotoCard = screen.getByText('family_photo.jpg').closest('div')!
      expect(familyPhotoCard.querySelector('span:contains("📅")')).toBeNull()
    })

    test('displays file tooltips on hover', () => {
      render(<SearchResults results={mockResults} />)

      const filename = screen.getByText('beach_sunset.jpg')
      expect(filename).toHaveAttribute('title', 'beach_sunset.jpg')

      const folder = screen.getByText('vacation')
      expect(folder).toHaveAttribute('title', '/photos/vacation')
    })
  })

  describe('Badges', () => {
    test('displays badges with correct colors', () => {
      render(<SearchResults results={mockResults} />)

      // Check various badge types
      expect(screen.getByText('visual')).toHaveClass('bg-indigo-100', 'text-indigo-800')
      expect(screen.getByText('semantic')).toHaveClass('bg-pink-100', 'text-pink-800')
      expect(screen.getByText('face')).toHaveClass('bg-red-100', 'text-red-800')
      expect(screen.getByText('text')).toHaveClass('bg-blue-100', 'text-blue-800')
      expect(screen.getByText('filename')).toHaveClass('bg-green-100', 'text-green-800')
      expect(screen.getByText('metadata')).toHaveClass('bg-orange-100', 'text-orange-800')
    })

    test('does not display badge section when no badges', () => {
      const noBadgeResults = {
        ...mockResults,
        items: [{ ...mockResults.items[0], badges: [] }]
      }
      render(<SearchResults results={noBadgeResults} />)

      expect(screen.queryByText('visual')).not.toBeInTheDocument()
    })

    test('handles unknown badge types with default color', () => {
      const unknownBadgeResults = {
        ...mockResults,
        items: [{ ...mockResults.items[0], badges: ['unknown-type'] }]
      }
      render(<SearchResults results={unknownBadgeResults} />)

      expect(screen.getByText('unknown-type')).toHaveClass('bg-gray-100', 'text-gray-800')
    })
  })

  describe('Snippets', () => {
    test('displays snippets when available', () => {
      render(<SearchResults results={mockResults} />)

      expect(screen.getByText('"beautiful sunset over the ocean"')).toBeInTheDocument()
      expect(screen.getByText('"spectacular mountain landscape"')).toBeInTheDocument()
    })

    test('does not display snippet section when snippet is null', () => {
      render(<SearchResults results={mockResults} />)

      // family_photo.jpg has null snippet
      const familyPhotoCard = screen.getByText('family_photo.jpg').closest('div')!
      expect(familyPhotoCard.querySelector('.bg-yellow-50')).toBeNull()
    })
  })

  describe('Actions', () => {
    test('copy path button copies file path to clipboard', async () => {
      const user = userEvent.setup()
      render(<SearchResults results={mockResults} />)

      const copyButtons = screen.getAllByText('📋 Copy Path')
      await user.click(copyButtons[0])

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('/photos/vacation/beach_sunset.jpg')
    })

    test('view button opens file in new window', async () => {
      const user = userEvent.setup()
      render(<SearchResults results={mockResults} />)

      const viewButtons = screen.getAllByText('👁️ View')
      await user.click(viewButtons[0])

      expect(mockWindowOpen).toHaveBeenCalledWith('file:///photos/vacation/beach_sunset.jpg', '_blank')
    })

    test('action buttons have correct titles and styling', () => {
      render(<SearchResults results={mockResults} />)

      const copyButton = screen.getAllByText('📋 Copy Path')[0]
      expect(copyButton).toHaveAttribute('title', 'Copy file path')
      expect(copyButton).toHaveClass('bg-gray-100', 'text-gray-700', 'hover:bg-gray-200')

      const viewButton = screen.getAllByText('👁️ View')[0]
      expect(viewButton).toHaveClass('bg-blue-100', 'text-blue-700', 'hover:bg-blue-200')
    })
  })

  describe('Load More', () => {
    test('displays load more button when more results available', () => {
      const partialResults = {
        ...mockResults,
        total_matches: 100,
        items: mockResults.items,
      }
      render(<SearchResults results={partialResults} />)

      expect(screen.getByText('Load More Photos')).toBeInTheDocument()
    })

    test('does not display load more button when all results shown', () => {
      const allResults = {
        ...mockResults,
        total_matches: 3,
        items: mockResults.items,
      }
      render(<SearchResults results={allResults} />)

      expect(screen.queryByText('Load More Photos')).not.toBeInTheDocument()
    })
  })

  describe('Date Formatting', () => {
    test('handles invalid date strings gracefully', () => {
      const invalidDateResults = {
        ...mockResults,
        items: [{ ...mockResults.items[0], shot_dt: 'invalid-date' }]
      }
      render(<SearchResults results={invalidDateResults} />)

      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    test('handles null dates', () => {
      const nullDateResults = {
        ...mockResults,
        items: [{ ...mockResults.items[0], shot_dt: null }]
      }
      render(<SearchResults results={nullDateResults} />)

      // Date section should not appear
      const card = screen.getByText('beach_sunset.jpg').closest('div')!
      expect(card.textContent).not.toContain('📅')
    })
  })

  describe('Accessibility', () => {
    test('images have proper alt text', () => {
      render(<SearchResults results={mockResults} />)

      const images = screen.getAllByRole('img')
      expect(images[0]).toHaveAttribute('alt', 'beach_sunset.jpg')
      expect(images[1]).toHaveAttribute('alt', 'mountain_view.png')
    })

    test('buttons are properly labeled', () => {
      render(<SearchResults results={mockResults} />)

      const copyButtons = screen.getAllByRole('button', { name: /copy path/i })
      const viewButtons = screen.getAllByRole('button', { name: /view/i })

      expect(copyButtons).toHaveLength(3)
      expect(viewButtons).toHaveLength(3)
    })
  })
})