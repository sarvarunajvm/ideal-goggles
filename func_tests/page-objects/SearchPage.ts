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
    this.searchInput = page.locator('input[type="text"][placeholder*="Search"], input[type="text"][placeholder*="Describe"]');
    this.searchButton = page.locator('button[type="submit"]:has-text("Search")');
    // Updated to match current UI with Quick Find (Search icon) and Smart Search (Sparkles icon)
    this.textSearchButton = page.locator('button[aria-label*="Quick Find"]');
    this.semanticSearchButton = page.locator('button[aria-label*="Smart Search"]');
    this.imageSearchButton = page.locator('button[aria-label*="Similar Photos"]');
    this.filterButton = page.locator('button[title="Advanced filters"]');
    this.resultsContainer = page.locator('.grid').first(); // Grid of results
    this.emptyState = page.locator('text=Start searching your photos');
    this.uploadArea = page.locator('text=Drop an image or click to browse');
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
    // Wait for any network activity to complete
    await this.page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
    // Small buffer for UI updates
    await this.page.waitForTimeout(500);
  }

  async getSearchResults(): Promise<number> {
    // Count Card elements in the results grid
    const results = await this.page.locator('.grid > div.group').count();
    return results;
  }

  async getActiveSearchMode(): Promise<string | null> {
    // Check the placeholder text to determine active mode
    const placeholder = await this.searchInput.getAttribute('placeholder').catch(() => null);

    if (placeholder) {
      if (placeholder.includes('Describe')) {
        return 'Semantic Search';
      } else if (placeholder.includes('filename') || placeholder.includes('date') || placeholder.includes('text')) {
        return 'Text Search';
      }
    }

    // Check if image mode is active by looking for upload area
    const uploadAreaVisible = await this.uploadArea.isVisible().catch(() => false);
    if (uploadAreaVisible) {
      return 'Image Search';
    }

    // Default to Text Search (the default mode)
    return 'Text Search';
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

  async performSearch() {
    await this.searchButton.click();
    await this.waitForSearchComplete();
  }

  async hasSearchResults(): Promise<boolean> {
    const resultCount = await this.getSearchResults();
    return resultCount > 0;
  }

  async waitForLoadingToComplete() {
    const loadingIndicator = this.page.locator('[data-testid="loading-indicator"]');
    await loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  async getEmptyStateMessage(): Promise<string | null> {
    const emptyMessage = this.page.locator('[data-testid="empty-results"]');
    if (await emptyMessage.isVisible()) {
      return await emptyMessage.textContent();
    }
    return null;
  }
}