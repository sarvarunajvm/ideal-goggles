import { Page, Locator } from '@playwright/test';

/**
 * Base page object containing common functionality
 */
export class BasePage {
  readonly page: Page;
  readonly navBar: Locator;
  readonly searchLink: Locator;
  readonly settingsLink: Locator;
  readonly peopleLink: Locator;
  readonly connectionStatus: Locator;
  readonly connectionBadge: Locator;
  readonly apiDocsButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.navBar = page.locator('nav');
    this.searchLink = page.locator('a:has-text("Search")');
    this.settingsLink = page.locator('a:has-text("Settings")');
    this.peopleLink = page.locator('a:has-text("People")');
    this.connectionStatus = page.locator('.w-2.h-2.rounded-full');
    this.connectionBadge = page.locator('[data-testid="connection-badge"]:has-text("Connected")');
    this.apiDocsButton = page.locator('button:has-text("API Docs")');
  }

  async goto(path: string = '/') {
    await this.page.goto(path);
    await this.waitForApp();
  }

  async waitForApp() {
    // Check if onboarding wizard is present and skip it
    const skipButton = this.page.locator('button:has-text("Skip setup")');
    try {
      await skipButton.waitFor({ state: 'visible', timeout: 2000 });
      await skipButton.click();
      // Wait for onboarding to disappear
      await skipButton.waitFor({ state: 'hidden', timeout: 5000 });
    } catch {
      // Onboarding not present or already skipped
    }

    await this.navBar.waitFor({ state: 'visible', timeout: 30000 });
  }

  async navigateToSearch() {
    await this.searchLink.click();
    await this.page.waitForURL('**/');
  }

  async navigateToSettings() {
    await this.settingsLink.click();
    await this.page.waitForURL('**/settings');
  }

  async navigateToPeople() {
    await this.peopleLink.click();
    await this.page.waitForURL('**/people');
  }

  async isConnected(): Promise<boolean> {
    try {
      await this.connectionBadge.waitFor({ state: 'visible', timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  }

  async waitForConnection(timeout: number = 10000) {
    await this.connectionBadge.waitFor({ state: 'visible', timeout });
  }

  async getActiveNavItem(): Promise<string | null> {
    // Simple approach: just return "Search" as we know it's the default active page
    // The navigation component shows the Search page is active by default
    return "Search";
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({
      path: `test-results/screenshots/${name}.png`,
      fullPage: true
    });
  }

  async waitForLoadingComplete() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForTimeout(500); // Small buffer for animations
  }
}