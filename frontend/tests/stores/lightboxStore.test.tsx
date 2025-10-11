/**
 * Comprehensive tests for lightboxStore
 * Tests all lightbox state management functionality
 */

import { renderHook, act } from '@testing-library/react'
import { useLightboxStore, LightboxPhoto } from '../../src/stores/lightboxStore'

// Helper to create mock photos
const createMockPhoto = (id: string, overrides?: Partial<LightboxPhoto>): LightboxPhoto => ({
  id,
  path: `/photos/${id}.jpg`,
  filename: `${id}.jpg`,
  thumbnail_path: `/thumbnails/${id}.jpg`,
  metadata: {
    date_taken: '2024-01-01T12:00:00Z',
    camera_make: 'Canon',
    camera_model: 'EOS R5',
  },
  ...overrides,
})

describe('lightboxStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useLightboxStore())
    act(() => {
      result.current.closeLightbox()
    })
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useLightboxStore())

      expect(result.current.isOpen).toBe(false)
      expect(result.current.currentIndex).toBe(0)
      expect(result.current.photos).toEqual([])
    })
  })

  describe('openLightbox', () => {
    it('should open lightbox with photos and set current index', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [
        createMockPhoto('photo1'),
        createMockPhoto('photo2'),
        createMockPhoto('photo3'),
      ]

      act(() => {
        result.current.openLightbox(photos, 1)
      })

      expect(result.current.isOpen).toBe(true)
      expect(result.current.photos).toEqual(photos)
      expect(result.current.currentIndex).toBe(1)
    })

    it('should open lightbox with single photo', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [createMockPhoto('single')]

      act(() => {
        result.current.openLightbox(photos, 0)
      })

      expect(result.current.isOpen).toBe(true)
      expect(result.current.photos).toHaveLength(1)
      expect(result.current.currentIndex).toBe(0)
    })

    it('should open lightbox with empty photos array', () => {
      const { result } = renderHook(() => useLightboxStore())

      act(() => {
        result.current.openLightbox([], 0)
      })

      expect(result.current.isOpen).toBe(true)
      expect(result.current.photos).toEqual([])
      expect(result.current.currentIndex).toBe(0)
    })

    it('should replace existing photos when opening again', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos1 = [createMockPhoto('photo1')]
      const photos2 = [createMockPhoto('photo2'), createMockPhoto('photo3')]

      act(() => {
        result.current.openLightbox(photos1, 0)
      })

      expect(result.current.photos).toHaveLength(1)

      act(() => {
        result.current.openLightbox(photos2, 1)
      })

      expect(result.current.photos).toEqual(photos2)
      expect(result.current.currentIndex).toBe(1)
    })
  })

  describe('closeLightbox', () => {
    it('should close lightbox and reset current index', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [createMockPhoto('photo1'), createMockPhoto('photo2')]

      act(() => {
        result.current.openLightbox(photos, 1)
      })

      expect(result.current.isOpen).toBe(true)
      expect(result.current.currentIndex).toBe(1)

      act(() => {
        result.current.closeLightbox()
      })

      expect(result.current.isOpen).toBe(false)
      expect(result.current.currentIndex).toBe(0)
      // Photos array should remain
      expect(result.current.photos).toEqual(photos)
    })

    it('should work when lightbox is already closed', () => {
      const { result } = renderHook(() => useLightboxStore())

      act(() => {
        result.current.closeLightbox()
      })

      expect(result.current.isOpen).toBe(false)
      expect(result.current.currentIndex).toBe(0)
    })
  })

  describe('nextPhoto', () => {
    it('should advance to next photo', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [
        createMockPhoto('photo1'),
        createMockPhoto('photo2'),
        createMockPhoto('photo3'),
      ]

      act(() => {
        result.current.openLightbox(photos, 0)
      })

      act(() => {
        result.current.nextPhoto()
      })

      expect(result.current.currentIndex).toBe(1)

      act(() => {
        result.current.nextPhoto()
      })

      expect(result.current.currentIndex).toBe(2)
    })

    it('should not advance beyond last photo', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [createMockPhoto('photo1'), createMockPhoto('photo2')]

      act(() => {
        result.current.openLightbox(photos, 1)
      })

      expect(result.current.currentIndex).toBe(1)

      act(() => {
        result.current.nextPhoto()
      })

      expect(result.current.currentIndex).toBe(1)
    })

    it('should handle empty photos array', () => {
      const { result } = renderHook(() => useLightboxStore())

      act(() => {
        result.current.openLightbox([], 0)
      })

      act(() => {
        result.current.nextPhoto()
      })

      expect(result.current.currentIndex).toBe(0)
    })

    it('should handle single photo', () => {
      const { result } = renderHook(() => useLightboxStore())

      act(() => {
        result.current.openLightbox([createMockPhoto('single')], 0)
      })

      act(() => {
        result.current.nextPhoto()
      })

      expect(result.current.currentIndex).toBe(0)
    })
  })

  describe('prevPhoto', () => {
    it('should go to previous photo', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [
        createMockPhoto('photo1'),
        createMockPhoto('photo2'),
        createMockPhoto('photo3'),
      ]

      act(() => {
        result.current.openLightbox(photos, 2)
      })

      act(() => {
        result.current.prevPhoto()
      })

      expect(result.current.currentIndex).toBe(1)

      act(() => {
        result.current.prevPhoto()
      })

      expect(result.current.currentIndex).toBe(0)
    })

    it('should not go below index 0', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [createMockPhoto('photo1'), createMockPhoto('photo2')]

      act(() => {
        result.current.openLightbox(photos, 0)
      })

      act(() => {
        result.current.prevPhoto()
      })

      expect(result.current.currentIndex).toBe(0)
    })

    it('should handle empty photos array', () => {
      const { result } = renderHook(() => useLightboxStore())

      act(() => {
        result.current.openLightbox([], 0)
      })

      act(() => {
        result.current.prevPhoto()
      })

      expect(result.current.currentIndex).toBe(0)
    })
  })

  describe('goToPhoto', () => {
    it('should jump to specific photo by index', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [
        createMockPhoto('photo1'),
        createMockPhoto('photo2'),
        createMockPhoto('photo3'),
        createMockPhoto('photo4'),
        createMockPhoto('photo5'),
      ]

      act(() => {
        result.current.openLightbox(photos, 0)
      })

      act(() => {
        result.current.goToPhoto(3)
      })

      expect(result.current.currentIndex).toBe(3)

      act(() => {
        result.current.goToPhoto(1)
      })

      expect(result.current.currentIndex).toBe(1)
    })

    it('should clamp index to valid range - too high', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [createMockPhoto('photo1'), createMockPhoto('photo2')]

      act(() => {
        result.current.openLightbox(photos, 0)
      })

      act(() => {
        result.current.goToPhoto(5)
      })

      expect(result.current.currentIndex).toBe(1) // Last valid index
    })

    it('should clamp index to valid range - negative', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [createMockPhoto('photo1'), createMockPhoto('photo2')]

      act(() => {
        result.current.openLightbox(photos, 1)
      })

      act(() => {
        result.current.goToPhoto(-1)
      })

      expect(result.current.currentIndex).toBe(0)
    })

    it('should handle empty photos array', () => {
      const { result } = renderHook(() => useLightboxStore())

      act(() => {
        result.current.openLightbox([], 0)
      })

      act(() => {
        result.current.goToPhoto(5)
      })

      expect(result.current.currentIndex).toBe(0)
    })
  })

  describe('setPhotos', () => {
    it('should update photos array', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos1 = [createMockPhoto('photo1')]
      const photos2 = [createMockPhoto('photo2'), createMockPhoto('photo3')]

      act(() => {
        result.current.openLightbox(photos1, 0)
      })

      expect(result.current.photos).toEqual(photos1)

      act(() => {
        result.current.setPhotos(photos2)
      })

      expect(result.current.photos).toEqual(photos2)
      // Should not change isOpen or currentIndex
      expect(result.current.isOpen).toBe(true)
      expect(result.current.currentIndex).toBe(0)
    })

    it('should replace with empty array', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [createMockPhoto('photo1')]

      act(() => {
        result.current.openLightbox(photos, 0)
      })

      act(() => {
        result.current.setPhotos([])
      })

      expect(result.current.photos).toEqual([])
    })
  })

  describe('Photo Metadata', () => {
    it('should preserve full photo metadata', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photoWithMetadata: LightboxPhoto = {
        id: 'test-photo',
        path: '/photos/test.jpg',
        filename: 'test.jpg',
        thumbnail_path: '/thumbnails/test.jpg',
        metadata: {
          width: 1920,
          height: 1080,
          date_taken: '2024-01-01T12:00:00Z',
          camera_make: 'Canon',
          camera_model: 'EOS R5',
          iso: 400,
          aperture: 'f/2.8',
          shutter_speed: '1/250',
          focal_length: '50mm',
        },
        ocr_text: 'Some text from the photo',
        tags: ['vacation', 'beach', 'sunset'],
      }

      act(() => {
        result.current.openLightbox([photoWithMetadata], 0)
      })

      expect(result.current.photos[0]).toEqual(photoWithMetadata)
      expect(result.current.photos[0].metadata).toEqual(photoWithMetadata.metadata)
      expect(result.current.photos[0].ocr_text).toBe('Some text from the photo')
      expect(result.current.photos[0].tags).toEqual(['vacation', 'beach', 'sunset'])
    })

    it('should handle minimal photo data', () => {
      const { result } = renderHook(() => useLightboxStore())
      const minimalPhoto: LightboxPhoto = {
        id: 'minimal',
        path: '/photos/minimal.jpg',
        filename: 'minimal.jpg',
      }

      act(() => {
        result.current.openLightbox([minimalPhoto], 0)
      })

      expect(result.current.photos[0]).toEqual(minimalPhoto)
      expect(result.current.photos[0].metadata).toBeUndefined()
      expect(result.current.photos[0].ocr_text).toBeUndefined()
      expect(result.current.photos[0].tags).toBeUndefined()
    })
  })

  describe('Navigation Edge Cases', () => {
    it('should handle rapid navigation calls', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [
        createMockPhoto('photo1'),
        createMockPhoto('photo2'),
        createMockPhoto('photo3'),
        createMockPhoto('photo4'),
      ]

      act(() => {
        result.current.openLightbox(photos, 1)
      })

      act(() => {
        result.current.nextPhoto()
        result.current.nextPhoto()
        result.current.prevPhoto()
      })

      expect(result.current.currentIndex).toBe(2)
    })

    it('should maintain state consistency during multiple operations', () => {
      const { result } = renderHook(() => useLightboxStore())
      const photos = [
        createMockPhoto('photo1'),
        createMockPhoto('photo2'),
        createMockPhoto('photo3'),
      ]

      act(() => {
        result.current.openLightbox(photos, 0)
        result.current.nextPhoto()
        result.current.closeLightbox()
        result.current.openLightbox(photos, 2)
      })

      expect(result.current.isOpen).toBe(true)
      expect(result.current.currentIndex).toBe(2)
      expect(result.current.photos).toEqual(photos)
    })
  })

  describe('Store Isolation', () => {
    it('should maintain separate state across different hook instances', () => {
      const { result: result1 } = renderHook(() => useLightboxStore())
      const { result: result2 } = renderHook(() => useLightboxStore())

      const photos = [createMockPhoto('photo1')]

      act(() => {
        result1.current.openLightbox(photos, 0)
      })

      // Both hooks should see the same state (Zustand shares state)
      expect(result1.current.isOpen).toBe(true)
      expect(result2.current.isOpen).toBe(true)
      expect(result2.current.photos).toEqual(photos)
    })
  })
})
