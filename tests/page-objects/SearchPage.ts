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
    this.searchInput = page.locator('input[placeholder*="Search"], input[placeholder*="Describe"]');
    this.searchButton = page.locator('button[type="submit"]');
    // Updated to use TabsTrigger buttons with proper selectors
    this.textSearchButton = page.locator('button[role="tab"]:has-text("Text Search")');
    this.semanticSearchButton = page.locator('button[role="tab"]:has-text("Semantic")');
    this.imageSearchButton = page.locator('button[role="tab"]:has-text("Image")');
    this.filterButton = page.locator('text=Filters');
    this.resultsContainer = page.locator('.grid').first(); // Grid of results
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
    // Find the active tab using aria-selected attribute
    const activeTab = await this.page.locator('button[role="tab"][aria-selected="true"]').textContent();
    return activeTab?.trim() || null;
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