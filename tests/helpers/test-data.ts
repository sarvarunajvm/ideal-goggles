import * as path from 'path';
import * as fs from 'fs';

/**
 * Test data generator and utilities
 */
export class TestData {
  static readonly FIXTURES_DIR = path.join(__dirname, '..', 'fixtures');

  // Sample search queries
  static readonly SEARCH_QUERIES = {
    text: [
      'vacation',
      'family photo',
      'IMG_2023',
      'birthday party',
      'sunset beach',
      'wedding ceremony'
    ],
    semantic: [
      'happy family moments at the beach',
      'sunset over mountains with clouds',
      'children playing in the park',
      'delicious food on a table',
      'cityscape at night with lights',
      'group of friends laughing together'
    ]
  };

  // Sample folder paths for testing
  static readonly TEST_FOLDERS = [
    '/tmp/test-photos-1',
    '/tmp/test-photos-2',
    '/tmp/test-photos-3'
  ];

  // Sample person names
  static readonly PERSON_NAMES = [
    'John Doe',
    'Jane Smith',
    'Bob Johnson',
    'Alice Williams',
    'Charlie Brown',
    'Emma Davis'
  ];

  // Configuration presets
  static readonly CONFIG_PRESETS = {
    minimal: {
      ocr_enabled: false,
      face_search_enabled: false,
      semantic_search_enabled: false,
      batch_size: 10,
      thumbnail_size: 'small'
    },
    standard: {
      ocr_enabled: false,
      face_search_enabled: true,
      semantic_search_enabled: true,
      batch_size: 50,
      thumbnail_size: 'medium'
    },
    full: {
      ocr_enabled: true,
      face_search_enabled: true,
      semantic_search_enabled: true,
      batch_size: 100,
      thumbnail_size: 'large'
    }
  };

  /**
   * Create a test image file
   */
  static async createTestImage(filename: string): Promise<string> {
    const imagePath = path.join(this.FIXTURES_DIR, 'images', filename);

    // Ensure directory exists
    const dir = path.dirname(imagePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Create a simple PNG image (1x1 pixel)
    const pngHeader = Buffer.from([
      0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, // PNG signature
      0x00, 0x00, 0x00, 0x0D, // IHDR chunk size
      0x49, 0x48, 0x44, 0x52, // IHDR
      0x00, 0x00, 0x00, 0x01, // width = 1
      0x00, 0x00, 0x00, 0x01, // height = 1
      0x08, 0x02, // bit depth = 8, color type = 2 (RGB)
      0x00, 0x00, 0x00, // compression, filter, interlace
      0x90, 0x77, 0x53, 0xDE, // CRC
      0x00, 0x00, 0x00, 0x0C, // IDAT chunk size
      0x49, 0x44, 0x41, 0x54, // IDAT
      0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0xFE, 0xFF, 0x00, 0x00, 0x00, 0x02, // compressed data
      0x00, 0x01, // CRC
      0x00, 0x00, 0x00, 0x00, // IEND chunk size
      0x49, 0x45, 0x4E, 0x44, // IEND
      0xAE, 0x42, 0x60, 0x82  // CRC
    ]);

    fs.writeFileSync(imagePath, pngHeader);
    return imagePath;
  }

  /**
   * Create multiple test images
   */
  static async createTestImages(count: number): Promise<string[]> {
    const images: string[] = [];
    for (let i = 0; i < count; i++) {
      const filename = `test-image-${Date.now()}-${i}.png`;
      const imagePath = await this.createTestImage(filename);
      images.push(imagePath);
    }
    return images;
  }

  /**
   * Create test folders with images
   */
  static async createTestFolders(): Promise<string[]> {
    const folders: string[] = [];

    for (const folderPath of this.TEST_FOLDERS) {
      if (!fs.existsSync(folderPath)) {
        fs.mkdirSync(folderPath, { recursive: true });
      }

      // Add some test images to each folder
      for (let i = 0; i < 5; i++) {
        const imageName = `${path.basename(folderPath)}-image-${i}.png`;
        const imagePath = path.join(folderPath, imageName);

        // Copy or create test image
        const testImage = await this.createTestImage(`temp-${imageName}`);
        fs.copyFileSync(testImage, imagePath);
      }

      folders.push(folderPath);
    }

    return folders;
  }

  /**
   * Clean up test folders
   */
  static async cleanupTestFolders() {
    for (const folderPath of this.TEST_FOLDERS) {
      if (fs.existsSync(folderPath)) {
        fs.rmSync(folderPath, { recursive: true, force: true });
      }
    }
  }

  /**
   * Clean up fixtures directory
   */
  static async cleanupFixtures() {
    if (fs.existsSync(this.FIXTURES_DIR)) {
      fs.rmSync(this.FIXTURES_DIR, { recursive: true, force: true });
    }
  }

  /**
   * Generate random search query
   */
  static getRandomSearchQuery(type: 'text' | 'semantic' = 'text'): string {
    const queries = type === 'text' ? this.SEARCH_QUERIES.text : this.SEARCH_QUERIES.semantic;
    return queries[Math.floor(Math.random() * queries.length)];
  }

  /**
   * Generate random person name
   */
  static getRandomPersonName(): string {
    return this.PERSON_NAMES[Math.floor(Math.random() * this.PERSON_NAMES.length)];
  }

  /**
   * Wait for a condition to be met
   */
  static async waitForCondition(
    condition: () => Promise<boolean>,
    timeout: number = 30000,
    interval: number = 1000
  ): Promise<boolean> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }

    return false;
  }

  /**
   * Create mock API response
   */
  static createMockSearchResponse(count: number = 10) {
    const results = [];
    for (let i = 0; i < count; i++) {
      results.push({
        id: `photo-${i}`,
        path: `/photos/image-${i}.jpg`,
        filename: `image-${i}.jpg`,
        score: Math.random(),
        metadata: {
          date_taken: new Date().toISOString(),
          width: 1920,
          height: 1080,
          size: 1024 * 1024 * (1 + Math.random() * 5)
        }
      });
    }
    return {
      results,
      total: count,
      query_time: Math.random() * 2
    };
  }
}