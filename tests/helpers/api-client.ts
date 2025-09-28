import { APIRequestContext, request } from '@playwright/test';

/**
 * API client for direct backend testing
 */
export class APIClient {
  private context: APIRequestContext;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:55555') {
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

  async createPerson(name: string, photoPaths: string[]) {
    const formData = new FormData();
    formData.append('name', name);

    for (const path of photoPaths) {
      const buffer = await require('fs').promises.readFile(path);
      formData.append('photos', new Blob([buffer]), path.split('/').pop() || 'photo.jpg');
    }

    return await this.context.post('/people', {
      multipart: {
        name,
        photos: photoPaths.map(path => ({
          name: path.split('/').pop() || 'photo.jpg',
          mimeType: 'image/jpeg',
          buffer: require('fs').readFileSync(path),
        }))
      }
    });
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
      const status = await response.json();

      if (status.state === 'idle' || status.state === 'complete') {
        return true;
      }

      if (status.state === 'error') {
        throw new Error(`Indexing failed: ${status.error}`);
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    return false;
  }

  async ensureBackendReady(maxWaitTime: number = 30000) {
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitTime) {
      try {
        const response = await this.checkHealth();
        if (response.ok) {
          return true;
        }
      } catch (error) {
        // Backend not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    throw new Error('Backend failed to become ready');
  }
}