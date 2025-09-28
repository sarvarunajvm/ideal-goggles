import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class SearchPage extends BasePage {
  readonly searchInput: Locator;
  readonly searchButton: Locator;
  readonly textSearchButton: Locator;
  readonly semanticSearchButton: Locator;
  readonly imageSearchButton: Locator;
  readonly filterButton: Locator;
  readonly resultsContainer: Locator;
  readonly emptyState: Locator;
  readonly uploadArea: Locator;
  readonly loadingSpinner: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.locator('input[placeholder*="Search"]');
    this.searchButton = page.locator('button[type="submit"]');
    this.textSearchButton = page.locator('button:has-text("Text Search")');
    this.semanticSearchButton = page.locator('button:has-text("Semantic Search")');
    this.imageSearchButton = page.locator('button:has-text("Image Search")');
    this.filterButton = page.locator('button:has-text("Filters")');
    this.resultsContainer = page.locator('[data-testid="search-results"]');
    this.emptyState = page.locator('text=Search Your Photos');
    this.uploadArea = page.locator('text=Upload an image to search');
    this.loadingSpinner = page.locator('.animate-spin');
  }

  async performTextSearch(query: string) {
    await this.textSearchButton.click();
    await this.searchInput.fill(query);
    await this.searchButton.click();
    await this.waitForSearchComplete();
  }

  async performSemanticSearch(query: string) {
    await this.semanticSearchButton.click();
    await this.searchInput.fill(query);
    await this.searchButton.click();
    await this.waitForSearchComplete();
  }

  async uploadImageForSearch(filePath: string) {
    await this.imageSearchButton.click();
    const fileInput = await this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await this.waitForSearchComplete();
  }

  async waitForSearchComplete() {
    // Wait for loading to start
    await this.loadingSpinner.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    // Wait for loading to complete
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 30000 }).catch(() => {});
    await this.page.waitForTimeout(500);
  }

  async getSearchResults(): Promise<number> {
    const results = await this.page.locator('[data-testid="search-result-item"]').count();
    return results;
  }

  async getActiveSearchMode(): Promise<string | null> {
    const activeButton = await this.page.locator('button.bg-blue-600').textContent();
    return activeButton;
  }

  async toggleFilters() {
    await this.filterButton.click();
    await this.page.waitForTimeout(300); // Wait for animation
  }

  async setDateFilter(startDate: string, endDate: string) {
    await this.toggleFilters();
    const startInput = await this.page.locator('input[name="startDate"]');
    const endInput = await this.page.locator('input[name="endDate"]');
    await startInput.fill(startDate);
    await endInput.fill(endDate);
  }

  async clearSearch() {
    await this.searchInput.clear();
  }

  async isSearchButtonEnabled(): Promise<boolean> {
    return await this.searchButton.isEnabled();
  }

  async getSearchPlaceholder(): Promise<string | null> {
    return await this.searchInput.getAttribute('placeholder');
  }

  async selectSearchResult(index: number) {
    const result = await this.page.locator('[data-testid="search-result-item"]').nth(index);
    await result.click();
  }

  async getResultDetails(index: number) {
    const result = await this.page.locator('[data-testid="search-result-item"]').nth(index);
    return {
      title: await result.locator('[data-testid="result-title"]').textContent(),
      score: await result.locator('[data-testid="result-score"]').textContent(),
      path: await result.locator('[data-testid="result-path"]').textContent()
    };
  }
}