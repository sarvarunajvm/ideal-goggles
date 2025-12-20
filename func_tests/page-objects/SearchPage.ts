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
    // Search input placeholder changes based on mode: "Search by filename, date, or text..." or "Describe what you're looking for..."
    this.searchInput = page.locator('input[type="text"][placeholder*="Search"], input[type="text"][placeholder*="Describe"]').first();
    // Search button is a submit button with text "Search"
    this.searchButton = page.locator('button[type="submit"]:has-text("Search")').first();
    // Search mode buttons use aria-label attributes - these are icon buttons
    this.textSearchButton = page.locator('button[aria-label*="Quick Find"]').first();
    this.semanticSearchButton = page.locator('button[aria-label*="Smart Search"]').first();
    this.imageSearchButton = page.locator('button[aria-label*="Similar Photos"]').first();
    // Filter button has title="Advanced filters"
    this.filterButton = page.locator('button[title="Advanced filters"]').first();
    // Results are displayed in a grid
    this.resultsContainer = page.locator('.grid').first(); // Grid of results
    // Empty state message - check for common empty state texts
    this.emptyState = page.locator('text=Start searching your photos, text=No results found, text=Welcome to Ideal Goggles').first();
    // Upload area for image search mode
    this.uploadArea = page.locator('text=Drop an image or click to browse, text=Upload').first();
    this.loadingSpinner = page.locator('.animate-spin').first();
  }

  async goto(path: string = '/') {
    await super.goto(path);
    // Wait for search input to be visible to ensure page is loaded
    await this.searchInput.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
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
    const results = await this.page.locator('[data-testid="search-result-item"]').count();
    return results;
  }

  async getActiveSearchMode(): Promise<string | null> {
    // Check if image mode is active by looking for upload area (image mode shows upload area instead of input)
    const uploadAreaVisible = await this.uploadArea.isVisible().catch(() => false);
    if (uploadAreaVisible) {
      return 'Image Search';
    }

    // Check the placeholder text to determine active mode
    const placeholder = await this.searchInput.getAttribute('placeholder').catch(() => null);

    if (placeholder) {
      if (placeholder.includes('Describe')) {
        return 'Semantic Search';
      } else if (placeholder.includes('filename') || placeholder.includes('date') || placeholder.includes('text')) {
        return 'Text Search';
      }
    }

    // Default to Semantic Search (the default mode in the current implementation)
    return 'Semantic Search';
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
    // In image mode, there's no search button - upload triggers search automatically
    const activeMode = await this.getActiveSearchMode();
    if (activeMode === 'Image Search') {
      return true; // Image mode doesn't use search button
    }
    
    // Wait a bit for button state to update
    await this.page.waitForTimeout(100);
    const isEnabled = await this.searchButton.isEnabled().catch(() => false);
    // Also check if button is visible (might be hidden in image mode)
    const isVisible = await this.searchButton.isVisible().catch(() => false);
    return isEnabled && isVisible;
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
    const activeMode = await this.getActiveSearchMode();
    
    if (activeMode === 'Image Search') {
      // Image mode doesn't have a search button - upload triggers search
      // This method shouldn't be called in image mode, but handle it gracefully
      await this.waitForSearchComplete();
      return;
    }
    
    // Check if search button is visible and enabled
    const isVisible = await this.searchButton.isVisible().catch(() => false);
    if (isVisible && await this.searchButton.isEnabled()) {
      await this.searchButton.click();
    } else {
      // Fallback: submit the form by pressing Enter
      await this.searchInput.press('Enter');
    }
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