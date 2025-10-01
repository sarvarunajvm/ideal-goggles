/**
 * Unit tests for API Client Service
 * Priority: P0 (Critical infrastructure)
 */

import { apiService, getApiBaseUrl } from '../../src/services/apiClient'

// Mock the logger to avoid import issues
jest.mock('../../src/utils/logger', () => ({
  logger: {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn(),
    generateRequestId: jest.fn(() => 'test-request-id'),
    logApiCall: jest.fn(),
    logApiResponse: jest.fn(),
    startPerformance: jest.fn(),
    endPerformance: jest.fn()
  }
}))

// Mock fetch globally
global.fetch = jest.fn()

describe('API Client Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(global.fetch as jest.Mock).mockClear()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Base Configuration', () => {
    test('uses correct base URL for web', () => {
      // In non-Electron environment, should use /api
      expect(getApiBaseUrl()).toBe('/api')
    })

    test('uses electron URL when in electron context', () => {
      // Mock Electron environment
      (window as any).electronAPI = {}
      expect(getApiBaseUrl()).toBe('http://127.0.0.1:5555')
      delete (window as any).electronAPI
    })
  })

  describe('Health Check', () => {
    test('gets health status', async () => {
      const mockHealth = {
        status: 'healthy',
        timestamp: '2024-01-01T00:00:00Z',
        version: '1.0.0',
        service: 'ideal-goggles'
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealth
      })

      const result = await apiService.getHealth()

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/health',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Request-ID': 'test-request-id'
          })
        })
      )
      expect(result).toEqual(mockHealth)
    })
  })

  describe('Configuration', () => {
    test('gets configuration', async () => {
      const mockConfig = {
        roots: ['/photos'],
        ocr_languages: ['eng'],
        face_search_enabled: true,
        index_version: '1.0.0'
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig
      })

      const result = await apiService.getConfig()
      expect(result).toEqual(mockConfig)
    })

    test('updates roots', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      })

      await apiService.updateRoots(['/photos', '/documents'])

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/config/roots',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ roots: ['/photos', '/documents'] })
        })
      )
    })

    test('updates configuration', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      })

      await apiService.updateConfig({
        face_search_enabled: false,
        thumbnail_size: '512'
      })

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/config',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({
            face_search_enabled: false,
            thumbnail_size: '512'
          })
        })
      )
    })
  })

  describe('Search Functionality', () => {
    test('performs photo search', async () => {
      const mockResponse = {
        query: 'test',
        items: [],
        total_matches: 0,
        took_ms: 10
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await apiService.searchPhotos({
        q: 'test',
        limit: 50
      })

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/search?q=test&limit=50',
        expect.any(Object)
      )
      expect(result).toEqual(mockResponse)
    })

    test('performs semantic search', async () => {
      const mockResponse = {
        items: [],
        total_matches: 0,
        took_ms: 15
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await apiService.semanticSearch('test text', 100)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/search/semantic',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            text: 'test text',
            top_k: 100
          })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    test('performs image search', async () => {
      const mockResponse = {
        items: [],
        total_matches: 0,
        took_ms: 20
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const result = await apiService.imageSearch(file, 75)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/search/image',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
      expect(result).toEqual(mockResponse)
    })

    test('searches faces by person', async () => {
      const mockResponse = {
        items: [],
        total_matches: 5,
        took_ms: 25
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await apiService.searchFaces(123, 50)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/search/faces',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            person_id: 123,
            top_k: 50
          })
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Index Management', () => {
    test('gets index status', async () => {
      const mockStatus = {
        status: 'running',
        progress: {
          total_files: 1000,
          processed_files: 500,
          current_phase: 'processing'
        },
        errors: [],
        started_at: '2024-01-01T00:00:00Z',
        estimated_completion: null
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus
      })

      const result = await apiService.getIndexStatus()
      expect(result).toEqual(mockStatus)
    })

    test('starts indexing', async () => {
      const mockResponse = { status: 'started' }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await apiService.startIndexing(true)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/index/start',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ full: true })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    test('stops indexing', async () => {
      const mockResponse = { status: 'stopped' }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await apiService.stopIndexing()

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/index/stop',
        expect.objectContaining({
          method: 'POST'
        })
      )
      expect(result).toEqual(mockResponse)
    })

    test('gets index stats', async () => {
      const mockStats = {
        total_files: 10000,
        indexed_files: 9500,
        total_size: 1000000000
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      })

      const result = await apiService.getIndexStats()
      expect(result).toEqual(mockStats)
    })
  })

  describe('People Management', () => {
    test('gets all people', async () => {
      const mockPeople = [
        { id: 1, name: 'John Doe' },
        { id: 2, name: 'Jane Smith' }
      ]

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPeople
      })

      const result = await apiService.getPeople()
      expect(result).toEqual(mockPeople)
    })

    test('creates a person', async () => {
      const mockPerson = {
        id: 3,
        name: 'New Person'
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPerson
      })

      const result = await apiService.createPerson('New Person', [1, 2, 3])

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/people',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            name: 'New Person',
            sample_file_ids: [1, 2, 3]
          })
        })
      )
      expect(result).toEqual(mockPerson)
    })
  })

  describe('Dependencies', () => {
    test('gets dependencies status', async () => {
      const mockDeps = {
        core: [
          {
            name: 'sqlite',
            installed: true,
            version: '3.40.0',
            required: true,
            description: 'Database engine'
          }
        ],
        ml: [],
        features: {
          face_detection: true,
          ocr: true
        }
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDeps
      })

      const result = await apiService.getDependencies()
      expect(result).toEqual(mockDeps)
    })

    test('installs dependencies', async () => {
      const mockResponse = {
        status: 'installing',
        components: ['face_recognition']
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await apiService.installDependencies(['face_recognition'])

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/dependencies/install',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            components: ['face_recognition']
          })
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Error Handling', () => {
    test('handles network errors', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      )

      await expect(apiService.getHealth()).rejects.toThrow('Network error')
    })

    test('handles non-OK responses', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Internal Server Error'
      })

      await expect(apiService.getHealth()).rejects.toThrow(
        'HTTP error! status: 500'
      )
    })

    test('handles JSON parse errors', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON')
        }
      })

      await expect(apiService.getHealth()).rejects.toThrow('Invalid JSON')
    })
  })

  describe('Request Headers', () => {
    test('includes required headers', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      })

      await apiService.getHealth()

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Request-ID': expect.any(String)
          })
        })
      )
    })

    test('handles FormData correctly', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      })

      const file = new File(['test'], 'test.jpg')
      await apiService.imageSearch(file)

      const callArgs = (global.fetch as jest.Mock).mock.calls[0]
      expect(callArgs[1].body).toBeInstanceOf(FormData)
      // FormData should not have Content-Type header (browser sets it)
      expect(callArgs[1].headers['Content-Type']).toBeUndefined()
    })
  })
})