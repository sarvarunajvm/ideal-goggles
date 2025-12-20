/**
 * API service for Ideal Goggles backend
 */

import { logger } from '../utils/logger'
import { mapErrorToUserMessage } from '../utils/errorMessages'

export const getApiBaseUrl = (): string => {
  // In Electron, backend always runs on port 5555
  // In web dev, Vite proxy rewrites '/api' -> backend
  if (
    typeof window !== 'undefined' &&
    (window as unknown as { electronAPI?: unknown }).electronAPI
  ) {
    return 'http://127.0.0.1:5555'
  }
  return '/api'
}

export const getThumbnailBaseUrl = (): string => {
  // In Electron, use direct backend URL
  // In web dev, use /thumbnails (proxied by Vite)
  if (
    typeof window !== 'undefined' &&
    (window as unknown as { electronAPI?: unknown }).electronAPI
  ) {
    return 'http://127.0.0.1:5555/thumbnails'
  }
  return '/thumbnails'
}

export interface SearchResult {
  file_id: number
  path: string
  folder: string
  filename: string
  thumb_path: string | null
  shot_dt: string | null
  score: number
  badges: string[]
  snippet: string | null
}

export interface SearchResponse {
  query: string
  total_matches: number
  items: SearchResult[]
  took_ms: number
}

export interface HealthResponse {
  status: string
  timestamp: string
  version: string
  service: string
  system: Record<string, unknown>
  database: Record<string, unknown>
  dependencies: Record<string, unknown>
}

export interface ConfigResponse {
  roots: string[]
  ocr_enabled?: boolean
  ocr_languages: string[]
  face_search_enabled: boolean
  semantic_search_enabled?: boolean
  batch_size?: number
  thumbnail_size?: string
  index_version: string
}

export interface IndexStatus {
  status: string
  progress: {
    total_files: number
    processed_files: number
    current_phase: string
  }
  errors: string[]
  started_at: string | null
  estimated_completion: string | null
}

export interface IndexStats {
  database?: {
    total_photos: number
    faces_detected: number
    indexed_photos: number
    database_size_mb: number
  }
  models?: Record<string, unknown>
  thumbnails?: Record<string, unknown>
}

export interface Person {
  id: number
  name: string
  sample_count: number
  created_at: string
  active: boolean
}

export interface DependencyStatus {
  name: string
  installed: boolean
  version: string | null
  required: boolean
  description: string
}

export interface ModelVerificationDetails {
  functional: boolean
  error: string | null
  details: {
    available_memory_gb: number
    total_memory_gb: number
    cuda_available?: boolean
    device?: string
    model_name?: string
    model_loaded?: boolean
    tesseract_version?: string
  }
}

export interface DependenciesResponse {
  core: DependencyStatus[]
  ml: DependencyStatus[]
  features: Record<string, boolean>
}

export interface DependencyVerificationResponse {
  summary: {
    all_functional: boolean
    issues_found: Array<{
      model: string
      error: string
    }>
  }
  models: Record<string, ModelVerificationDetails>
  system: {
    memory: {
      total_gb: number
      available_gb: number
      percent_used: number
    }
    python_version: string
    platform: string
    architecture: string
  }
  recommendations: string[]
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const baseUrl = getApiBaseUrl()
    const url = `${baseUrl}${endpoint}`
    const requestId = logger.generateRequestId()
    const startTime = performance.now()

    // Build headers (will be used for both fetch and logging)
    // For FormData, don't set Content-Type (browser will set it with boundary)
    const isFormData = options?.body instanceof FormData

    // Create final headers as a Headers instance to avoid type issues with HeadersInit union
    const finalHeaders = new Headers()
    finalHeaders.set('X-Request-ID', requestId)
    if (!isFormData) {
      finalHeaders.set('Content-Type', 'application/json')
    }
    const optHeaders = options?.headers
    if (optHeaders) {
      if (optHeaders instanceof Headers) {
        for (const [k, v] of optHeaders.entries()) {
          finalHeaders.set(k, String(v))
        }
      } else if (Array.isArray(optHeaders)) {
        for (const [k, v] of optHeaders) {
          finalHeaders.set(k, String(v))
        }
      } else {
        const record = optHeaders as Record<string, string>
        for (const [k, v] of Object.entries(record)) {
          finalHeaders.set(k, v)
        }
      }
    }

    // Normalize headers for logging only
    const logHeaders: Record<string, string> = {}
    for (const [k, v] of finalHeaders.entries()) {
      logHeaders[k] = v
    }

    // Log the request
    logger.logApiCall(
      options?.method || 'GET',
      endpoint,
      requestId,
      options?.body
        ? typeof options.body === 'string'
          ? options.body.length > 1000
            ? options.body.substring(0, 1000) + '...'
            : options.body
          : undefined
        : undefined,
      logHeaders
    )

    try {
      const response = await fetch(url, {
        ...options,
        headers: finalHeaders,
        // Avoid stale cached GET responses (config/people lists must reflect recent updates)
        cache: 'no-store',
      })

      const duration = performance.now() - startTime

      if (!response.ok) {
        const errorText = await response.text()
        logger.logApiResponse(
          options?.method || 'GET',
          endpoint,
          requestId,
          response.status,
          duration,
          errorText
        )

        const technicalError = `HTTP error! status: ${response.status}, message: ${errorText}`
        const mappedError = mapErrorToUserMessage(technicalError)

        const error = new Error(mappedError.message)
        // Attach additional properties for error handling
        ;(error as any).originalError = technicalError
        ;(error as any).severity = mappedError.severity
        ;(error as any).status = response.status

        logger.error(`API request failed: ${endpoint}`, error, {
          requestId,
          status: response.status,
          endpoint,
          originalError: technicalError,
          userMessage: mappedError.message,
          severity: mappedError.severity,
        })
        throw error
      }

      if (response.status === 204) {
        return {} as T
      }

      const data = await response.json()

      // Log successful response
      logger.logApiResponse(
        options?.method || 'GET',
        endpoint,
        requestId,
        response.status,
        duration,
        data
      )

      return data
    } catch (error) {
      const duration = performance.now() - startTime

      // Log network or other errors
      logger.error(`API request exception: ${endpoint}`, error as Error, {
        requestId,
        endpoint,
        duration,
      })

      throw error
    }
  }

  // Health and system endpoints
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health')
  }

  // Configuration endpoints
  async getConfig(): Promise<ConfigResponse> {
    return this.request<ConfigResponse>('/config')
  }

  async updateRoots(roots: string[]): Promise<void> {
    return this.request('/config/roots', {
      method: 'POST',
      body: JSON.stringify({ roots }),
    })
  }

  async updateConfig(
    config: Partial<{
      ocr_enabled: boolean
      ocr_languages: string[]
      face_search_enabled: boolean
      semantic_search_enabled: boolean
      batch_size: number
      thumbnail_size: string
      thumbnail_quality: number
    }>
  ): Promise<void> {
    return this.request('/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    })
  }

  // Search endpoints
  async searchPhotos(params: {
    q?: string
    from?: string
    to?: string
    folder?: string
    limit?: number
    offset?: number
  }): Promise<SearchResponse> {
    logger.startPerformance('searchPhotos')

    const searchParams = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value.toString())
      }
    })

    try {
      const result = await this.request<SearchResponse>(
        `/search?${searchParams}`
      )

      logger.info('Search completed', {
        query: params.q,
        resultCount: result.items.length,
        took_ms: result.took_ms,
      })

      return result
    } finally {
      logger.endPerformance('searchPhotos')
    }
  }

  async semanticSearch(text: string, topK = 50): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/semantic', {
      method: 'POST',
      body: JSON.stringify({ text, top_k: topK }),
    })
  }

  async imageSearch(file: File, topK = 50): Promise<SearchResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('top_k', topK.toString())

    return this.request<SearchResponse>('/search/image', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    })
  }

  // Indexing endpoints
  async getIndexStatus(): Promise<IndexStatus> {
    return this.request<IndexStatus>('/index/status')
  }

  async startIndexing(full = false): Promise<Record<string, unknown>> {
    logger.info('Starting indexing', { full })

    return this.request('/index/start', {
      method: 'POST',
      body: JSON.stringify({ full }),
    })
  }

  async stopIndexing(): Promise<Record<string, unknown>> {
    return this.request('/index/stop', {
      method: 'POST',
    })
  }

  async getIndexStats(): Promise<IndexStats> {
    return this.request('/index/stats')
  }

  // People endpoints
  async getPeople(): Promise<Person[]> {
    return this.request<Person[]>('/people')
  }

  async createPerson(
    name: string,
    sampleFileIds: number[]
  ): Promise<Person> {
    return this.request<Person>('/people', {
      method: 'POST',
      body: JSON.stringify({
        name,
        sample_file_ids: sampleFileIds,
      }),
    })
  }

  async updatePerson(
    personId: number,
    updates: {
      name?: string
      active?: boolean
      additional_sample_file_ids?: number[]
    }
  ): Promise<Person> {
    return this.request<Person>(`/people/${personId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  }

  async deletePerson(personId: number): Promise<void> {
    return this.request<void>(`/people/${personId}`, {
      method: 'DELETE',
    })
  }

  async searchFaces(personId: number, topK = 50): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/faces', {
      method: 'POST',
      body: JSON.stringify({
        person_id: personId,
        top_k: topK,
      }),
    })
  }

  // Get indexed photos (for selecting sample photos when creating people)
  async getIndexedPhotos(limit = 200): Promise<SearchResponse> {
    return this.searchPhotos({ limit })
  }

  // Dependencies endpoints
  async getDependencies(): Promise<DependenciesResponse> {
    return this.request<DependenciesResponse>('/dependencies')
  }

  async verifyDependencies(): Promise<DependencyVerificationResponse> {
    return this.request<DependencyVerificationResponse>('/dependencies/verify')
  }

  async installDependencies(
    components: string[] = ['all']
  ): Promise<Record<string, unknown>> {
    logger.info('Installing ML dependencies', { components })

    return this.request('/dependencies/install', {
      method: 'POST',
      body: JSON.stringify({ components }),
    })
  }
}

export const apiService = new ApiService()
