/**
 * API service for Ideal Goggles backend
 */

import { logger } from '../utils/logger';

export const getApiBaseUrl = (): string => {
  // In Electron, backend always runs on port 5555
  // In web dev, Vite proxy rewrites '/api' -> backend
  if (typeof window !== 'undefined' && (window as unknown as { electronAPI?: unknown }).electronAPI) {
    return 'http://127.0.0.1:5555';
  }
  return '/api';
};

export interface SearchResult {
  file_id: number;
  path: string;
  folder: string;
  filename: string;
  thumb_path: string | null;
  shot_dt: string | null;
  score: number;
  badges: string[];
  snippet: string | null;
}

export interface SearchResponse {
  query: string;
  total_matches: number;
  items: SearchResult[];
  took_ms: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  service: string;
  system: Record<string, unknown>;
  database: Record<string, unknown>;
  dependencies: Record<string, unknown>;
}

export interface ConfigResponse {
  roots: string[];
  ocr_languages: string[];
  face_search_enabled: boolean;
  semantic_search_enabled?: boolean;
  batch_size?: number;
  thumbnail_size?: string;
  index_version: string;
}

export interface IndexStatus {
  status: string;
  progress: {
    total_files: number;
    processed_files: number;
    current_phase: string;
  };
  errors: string[];
  started_at: string | null;
  estimated_completion: string | null;
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}${endpoint}`;
    const requestId = logger.generateRequestId();
    const startTime = performance.now();

    // Log the request
    logger.logApiCall(
      options?.method || 'GET',
      endpoint,
      requestId,
      options?.body ? (
        typeof options.body === 'string' ?
          (options.body.length > 1000 ? options.body.substring(0, 1000) + '...' : options.body) :
          undefined
      ) : undefined,
      options?.headers as Record<string, string>
    );

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId,
          ...options?.headers,
        },
        ...options,
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        const errorText = await response.text();
        logger.logApiResponse(
          options?.method || 'GET',
          endpoint,
          requestId,
          response.status,
          duration,
          errorText
        );

        const error = new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        logger.error(`API request failed: ${endpoint}`, error, {
          requestId,
          status: response.status,
          endpoint,
        });
        throw error;
      }

      const data = await response.json();

      // Log successful response
      logger.logApiResponse(
        options?.method || 'GET',
        endpoint,
        requestId,
        response.status,
        duration,
        data
      );

      return data;
    } catch (error) {
      const duration = performance.now() - startTime;

      // Log network or other errors
      logger.error(`API request exception: ${endpoint}`, error as Error, {
        requestId,
        endpoint,
        duration,
      });

      throw error;
    }
  }

  // Health and system endpoints
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // Configuration endpoints
  async getConfig(): Promise<ConfigResponse> {
    return this.request<ConfigResponse>('/config');
  }

  async updateRoots(roots: string[]): Promise<void> {
    return this.request('/config/roots', {
      method: 'POST',
      body: JSON.stringify({ roots }),
    });
  }

  async updateConfig(config: Partial<{
    ocr_languages: string[];
    face_search_enabled: boolean;
    semantic_search_enabled: boolean;
    batch_size: number;
    thumbnail_size: string;
    thumbnail_quality: number;
  }>): Promise<void> {
    return this.request('/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  // Search endpoints
  async searchPhotos(params: {
    q?: string;
    from?: string;
    to?: string;
    folder?: string;
    limit?: number;
    offset?: number;
  }): Promise<SearchResponse> {
    logger.startPerformance('searchPhotos');

    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value.toString());
      }
    });

    try {
      const result = await this.request<SearchResponse>(`/search?${searchParams}`);

      logger.info('Search completed', {
        query: params.q,
        resultCount: result.items.length,
        took_ms: result.took_ms,
      });

      return result;
    } finally {
      logger.endPerformance('searchPhotos');
    }
  }

  async semanticSearch(text: string, topK = 50): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/semantic', {
      method: 'POST',
      body: JSON.stringify({ text, top_k: topK }),
    });
  }

  async imageSearch(file: File, topK = 50): Promise<SearchResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('top_k', topK.toString());

    return this.request<SearchResponse>('/search/image', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  // Indexing endpoints
  async getIndexStatus(): Promise<IndexStatus> {
    return this.request<IndexStatus>('/index/status');
  }

  async startIndexing(full = false): Promise<Record<string, unknown>> {
    logger.info('Starting indexing', { full });

    return this.request('/index/start', {
      method: 'POST',
      body: JSON.stringify({ full }),
    });
  }

  async stopIndexing(): Promise<Record<string, unknown>> {
    return this.request('/index/stop', {
      method: 'POST',
    });
  }

  async getIndexStats(): Promise<Record<string, unknown>> {
    return this.request('/index/stats');
  }

  // People endpoints
  async getPeople(): Promise<Record<string, unknown>[]> {
    return this.request('/people');
  }

  async createPerson(name: string, sampleFileIds: number[]): Promise<Record<string, unknown>> {
    return this.request('/people', {
      method: 'POST',
      body: JSON.stringify({
        name,
        sample_file_ids: sampleFileIds,
      }),
    });
  }

  async searchFaces(personId: number, topK = 50): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/faces', {
      method: 'POST',
      body: JSON.stringify({
        person_id: personId,
        top_k: topK,
      }),
    });
  }
}

export const apiService = new ApiService();
