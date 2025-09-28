/**
 * API service for photo search backend
 */

export const getApiBaseUrl = (): string => {
  // In Electron production, backend runs at a dynamic localhost port (spawned by main)
  // In web dev, Vite proxy rewrites '/api' -> backend
  try {
    if (typeof window !== 'undefined' && (window as unknown as { electronAPI?: unknown }).electronAPI) {
      const port = (window as unknown as { BACKEND_PORT?: number }).BACKEND_PORT || 55555;
      return `http://127.0.0.1:${port}`;
    }
  } catch {}
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
    const url = `${getApiBaseUrl()}${endpoint}`;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
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
    thumbnail_size: number;
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
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value.toString());
      }
    });

    return this.request<SearchResponse>(`/search?${searchParams}`);
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
