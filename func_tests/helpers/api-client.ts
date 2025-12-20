import { APIRequestContext, request } from '@playwright/test';

/**
 * API client for direct backend testing
 */
export class APIClient {
  private context: APIRequestContext;
  private baseURL: string;

  // Use 127.0.0.1 to avoid IPv6 ::1 resolution issues on some machines (backend binds to IPv4).
  constructor(baseURL: string = 'http://127.0.0.1:5555') {
    this.baseURL = baseURL;
  }

  async initialize() {
    this.context = await request.newContext({
      baseURL: this.baseURL,
      extraHTTPHeaders: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
  }

  async dispose() {
    await this.context.dispose();
  }

  // Health endpoints
  async checkHealth() {
    return await this.context.get('/health');
  }

  async checkDetailedHealth() {
    return await this.context.get('/health/detailed');
  }

  // Configuration endpoints
  async getConfig() {
    return await this.context.get('/config');
  }

  async setRootFolders(roots: string[]) {
    return await this.context.post('/config/roots', {
      data: { roots }
    });
  }

  async updateConfig(config: any) {
    return await this.context.put('/config', {
      data: config
    });
  }

  async resetConfig() {
    return await this.context.post('/config/reset');
  }

  async deleteRootFolder(index: number) {
    return await this.context.delete(`/config/roots/${index}`);
  }

  // Indexing endpoints
  async startIndexing(full: boolean = false) {
    return await this.context.post('/index/start', {
      data: { full }
    });
  }

  async getIndexingStatus() {
    return await this.context.get('/index/status');
  }

  async stopIndexing() {
    return await this.context.post('/index/stop');
  }

  async getIndexingStats() {
    return await this.context.get('/index/stats');
  }

  // Search endpoints
  async textSearch(query: string, limit: number = 20, offset: number = 0) {
    return await this.context.get('/search', {
      params: { q: query, limit, offset }
    });
  }

  async semanticSearch(text: string, topK: number = 10) {
    return await this.context.post('/search/semantic', {
      data: { text, top_k: topK }
    });
  }

  async imageSearch(imagePath: string, topK: number = 10) {
    const formData = new FormData();
    const imageBuffer = await require('fs').promises.readFile(imagePath);
    formData.append('file', new Blob([imageBuffer]), 'image.jpg');
    formData.append('top_k', topK.toString());

    return await this.context.post('/search/image', {
      multipart: {
        file: {
          name: 'image.jpg',
          mimeType: 'image/jpeg',
          buffer: imageBuffer,
        },
        top_k: topK.toString(),
      }
    });
  }

  async faceSearch(personId: string, topK: number = 10) {
    return await this.context.post('/search/faces', {
      data: { person_id: personId, top_k: topK }
    });
  }

  // People endpoints
  async getPeople() {
    return await this.context.get('/people');
  }

  async getPerson(personId: string) {
    return await this.context.get(`/people/${personId}`);
  }

  async createPerson(name: string, sample_file_ids: number[]) {
    return await this.context.post('/people', {
      data: {
        name,
        sample_file_ids
      }
    });
  }

  // Helper to get indexed photos for testing
  async getIndexedPhotos(limit: number = 20) {
    const response = await this.textSearch('', limit);
    const data = await response.json();
    return data.items || [];
  }

  async updatePerson(personId: string, updates: any) {
    return await this.context.put(`/people/${personId}`, {
      data: updates
    });
  }

  async deletePerson(personId: string) {
    return await this.context.delete(`/people/${personId}`);
  }

  async getPersonPhotos(personId: string) {
    return await this.context.get(`/people/${personId}/photos`);
  }

  // Utility methods
  async waitForIndexingComplete(maxWaitTime: number = 60000) {
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitTime) {
      const response = await this.getIndexingStatus();
      if (!response.ok) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        continue;
      }
      const status = await response.json();
      // Backend returns { status: 'idle' | 'indexing' | 'completed' | 'error', errors?: [] }
      if (status.status === 'idle' || status.status === 'completed') {
        return true;
      }
      if (status.status === 'error') {
        const errMsg = Array.isArray(status.errors) && status.errors.length > 0 ? status.errors[0] : 'unknown error';
        throw new Error(`Indexing failed: ${errMsg}`);
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    return false;
  }

  async ensureBackendReady(maxWaitTime: number = 30000) {
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitTime) {
      try {
        // Prefer indexing status endpoint since health may fail if ML models are missing
        const response = await this.getIndexingStatus();
        if (response.ok) return true;
        // Fallback to health
        const health = await this.checkHealth();
        if (health.ok) return true;
      } catch (error) {
        // Backend not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    throw new Error('Backend failed to become ready');
  }
}
