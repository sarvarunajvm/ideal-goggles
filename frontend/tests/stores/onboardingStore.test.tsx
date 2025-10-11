/**
 * Comprehensive tests for onboardingStore
 * Tests onboarding flow state management with persistence
 */

import { renderHook, act } from '@testing-library/react'
import { useOnboardingStore } from '../../src/stores/onboardingStore'

// Mock localStorage for persistence testing
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('onboardingStore', () => {
  beforeEach(() => {
    // Clear localStorage and reset store before each test
    localStorageMock.clear()
    const { result } = renderHook(() => useOnboardingStore())
    act(() => {
      result.current.reset()
    })
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useOnboardingStore())

      expect(result.current.completed).toBe(false)
      expect(result.current.currentStep).toBe(0)
      expect(result.current.selectedFolders).toEqual([])
      expect(result.current.indexingStarted).toBe(false)
      expect(result.current.skipOnboarding).toBe(false)
    })
  })

  describe('setCompleted', () => {
    it('should mark onboarding as completed', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCompleted()
      })

      expect(result.current.completed).toBe(true)
    })

    it('should persist completed state', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCompleted()
      })

      // Create new hook instance to test persistence
      const { result: result2 } = renderHook(() => useOnboardingStore())

      expect(result2.current.completed).toBe(true)
    })

    it('should not affect other state', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.nextStep()
        result.current.addFolder('/photos')
        result.current.setCompleted()
      })

      expect(result.current.currentStep).toBe(1)
      expect(result.current.selectedFolders).toEqual(['/photos'])
    })
  })

  describe('nextStep', () => {
    it('should advance to next step', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.nextStep()
      })

      expect(result.current.currentStep).toBe(1)

      act(() => {
        result.current.nextStep()
      })

      expect(result.current.currentStep).toBe(2)
    })

    it('should handle multiple sequential steps', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.nextStep()
        result.current.nextStep()
        result.current.nextStep()
      })

      expect(result.current.currentStep).toBe(3)
    })

    it('should not have upper limit', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        for (let i = 0; i < 10; i++) {
          result.current.nextStep()
        }
      })

      expect(result.current.currentStep).toBe(10)
    })
  })

  describe('prevStep', () => {
    it('should go to previous step', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCurrentStep(3)
      })

      act(() => {
        result.current.prevStep()
      })

      expect(result.current.currentStep).toBe(2)
    })

    it('should not go below 0', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.prevStep()
        result.current.prevStep()
      })

      expect(result.current.currentStep).toBe(0)
    })

    it('should handle navigation back to first step', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.nextStep()
        result.current.nextStep()
        result.current.prevStep()
        result.current.prevStep()
      })

      expect(result.current.currentStep).toBe(0)
    })
  })

  describe('setCurrentStep', () => {
    it('should set specific step', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCurrentStep(5)
      })

      expect(result.current.currentStep).toBe(5)
    })

    it('should allow jumping to any step', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCurrentStep(10)
      })

      expect(result.current.currentStep).toBe(10)

      act(() => {
        result.current.setCurrentStep(3)
      })

      expect(result.current.currentStep).toBe(3)
    })

    it('should allow setting to 0', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCurrentStep(5)
        result.current.setCurrentStep(0)
      })

      expect(result.current.currentStep).toBe(0)
    })
  })

  describe('addFolder', () => {
    it('should add folder to selected folders', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/photos')
      })

      expect(result.current.selectedFolders).toEqual(['/photos'])
    })

    it('should add multiple folders', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/photos')
        result.current.addFolder('/documents')
        result.current.addFolder('/downloads')
      })

      expect(result.current.selectedFolders).toEqual([
        '/photos',
        '/documents',
        '/downloads',
      ])
    })

    it('should preserve order of added folders', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/path1')
        result.current.addFolder('/path2')
        result.current.addFolder('/path3')
      })

      expect(result.current.selectedFolders[0]).toBe('/path1')
      expect(result.current.selectedFolders[1]).toBe('/path2')
      expect(result.current.selectedFolders[2]).toBe('/path3')
    })

    it('should allow duplicate folders', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/photos')
        result.current.addFolder('/photos')
      })

      expect(result.current.selectedFolders).toHaveLength(2)
      expect(result.current.selectedFolders).toEqual(['/photos', '/photos'])
    })

    it('should handle paths with special characters', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/Users/John Doe/My Photos')
        result.current.addFolder('/path-with-dash')
        result.current.addFolder('/path_with_underscore')
      })

      expect(result.current.selectedFolders).toHaveLength(3)
    })
  })

  describe('removeFolder', () => {
    it('should remove folder from selected folders', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/photos')
        result.current.addFolder('/documents')
      })

      expect(result.current.selectedFolders).toHaveLength(2)

      act(() => {
        result.current.removeFolder('/photos')
      })

      expect(result.current.selectedFolders).toEqual(['/documents'])
    })

    it('should handle removing non-existent folder', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/photos')
        result.current.removeFolder('/nonexistent')
      })

      expect(result.current.selectedFolders).toEqual(['/photos'])
    })

    it('should remove all occurrences of duplicate', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/photos')
        result.current.addFolder('/photos')
        result.current.removeFolder('/photos')
      })

      expect(result.current.selectedFolders).toEqual([])
    })

    it('should handle removing all folders', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.addFolder('/path1')
        result.current.addFolder('/path2')
        result.current.removeFolder('/path1')
        result.current.removeFolder('/path2')
      })

      expect(result.current.selectedFolders).toEqual([])
    })
  })

  describe('setIndexingStarted', () => {
    it('should mark indexing as started', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setIndexingStarted(true)
      })

      expect(result.current.indexingStarted).toBe(true)
    })

    it('should mark indexing as not started', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setIndexingStarted(true)
        result.current.setIndexingStarted(false)
      })

      expect(result.current.indexingStarted).toBe(false)
    })
  })

  describe('setSkipOnboarding', () => {
    it('should set skip onboarding flag', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setSkipOnboarding(true)
      })

      expect(result.current.skipOnboarding).toBe(true)
    })

    it('should unset skip onboarding flag', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setSkipOnboarding(true)
        result.current.setSkipOnboarding(false)
      })

      expect(result.current.skipOnboarding).toBe(false)
    })
  })

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCompleted()
        result.current.setCurrentStep(5)
        result.current.addFolder('/photos')
        result.current.addFolder('/documents')
        result.current.setIndexingStarted(true)
        result.current.setSkipOnboarding(true)
      })

      // Verify state has changed
      expect(result.current.completed).toBe(true)
      expect(result.current.currentStep).toBe(5)
      expect(result.current.selectedFolders).toHaveLength(2)
      expect(result.current.indexingStarted).toBe(true)
      expect(result.current.skipOnboarding).toBe(true)

      act(() => {
        result.current.reset()
      })

      expect(result.current.completed).toBe(false)
      expect(result.current.currentStep).toBe(0)
      expect(result.current.selectedFolders).toEqual([])
      expect(result.current.indexingStarted).toBe(false)
      expect(result.current.skipOnboarding).toBe(false)
    })

    it('should be idempotent', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.reset()
        result.current.reset()
        result.current.reset()
      })

      expect(result.current.completed).toBe(false)
      expect(result.current.currentStep).toBe(0)
    })
  })

  describe('Complete Onboarding Workflow', () => {
    it('should handle typical onboarding flow', () => {
      const { result } = renderHook(() => useOnboardingStore())

      // Step 1: Welcome screen
      expect(result.current.currentStep).toBe(0)

      act(() => {
        result.current.nextStep()
      })

      // Step 2: Folder selection
      expect(result.current.currentStep).toBe(1)

      act(() => {
        result.current.addFolder('/Users/photos')
        result.current.addFolder('/Users/documents')
      })

      expect(result.current.selectedFolders).toHaveLength(2)

      act(() => {
        result.current.nextStep()
      })

      // Step 3: Start indexing
      expect(result.current.currentStep).toBe(2)

      act(() => {
        result.current.setIndexingStarted(true)
        result.current.nextStep()
      })

      // Step 4: Complete
      act(() => {
        result.current.setCompleted()
      })

      expect(result.current.completed).toBe(true)
      expect(result.current.indexingStarted).toBe(true)
      expect(result.current.selectedFolders).toHaveLength(2)
    })

    it('should handle user going back to change folders', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setCurrentStep(1)
        result.current.addFolder('/photos')
        result.current.nextStep()
      })

      expect(result.current.currentStep).toBe(2)

      // User goes back
      act(() => {
        result.current.prevStep()
      })

      expect(result.current.currentStep).toBe(1)

      // Change folder selection
      act(() => {
        result.current.removeFolder('/photos')
        result.current.addFolder('/documents')
        result.current.nextStep()
      })

      expect(result.current.currentStep).toBe(2)
      expect(result.current.selectedFolders).toEqual(['/documents'])
    })

    it('should handle skip onboarding workflow', () => {
      const { result } = renderHook(() => useOnboardingStore())

      act(() => {
        result.current.setSkipOnboarding(true)
        result.current.setCompleted()
      })

      expect(result.current.skipOnboarding).toBe(true)
      expect(result.current.completed).toBe(true)
      expect(result.current.selectedFolders).toEqual([])
    })
  })

  describe('Persistence', () => {
    it('should persist state across hook instances', () => {
      const { result: result1 } = renderHook(() => useOnboardingStore())

      act(() => {
        result1.current.setCurrentStep(3)
        result1.current.addFolder('/photos')
        result1.current.setCompleted()
      })

      // Create new hook instance
      const { result: result2 } = renderHook(() => useOnboardingStore())

      expect(result2.current.currentStep).toBe(3)
      expect(result2.current.selectedFolders).toEqual(['/photos'])
      expect(result2.current.completed).toBe(true)
    })

    it('should persist after reset', () => {
      const { result: result1 } = renderHook(() => useOnboardingStore())

      act(() => {
        result1.current.setCompleted()
        result1.current.reset()
      })

      // Create new hook instance to verify reset was persisted
      const { result: result2 } = renderHook(() => useOnboardingStore())

      expect(result2.current.completed).toBe(false)
    })
  })

  describe('Store Isolation', () => {
    it('should share state across all hook instances', () => {
      const { result: result1 } = renderHook(() => useOnboardingStore())
      const { result: result2 } = renderHook(() => useOnboardingStore())

      act(() => {
        result1.current.addFolder('/photos')
        result1.current.nextStep()
      })

      // Both hooks should see the same state
      expect(result2.current.selectedFolders).toEqual(['/photos'])
      expect(result2.current.currentStep).toBe(1)
    })
  })
})
