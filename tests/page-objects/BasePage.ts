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
  readonly apiDocsButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.navBar = page.locator('nav');
    this.searchLink = page.locator('a:has-text("Search")');
    this.settingsLink = page.locator('a:has-text("Settings")');
    this.peopleLink = page.locator('a:has-text("People")');
    this.connectionStatus = page.locator('.w-2.h-2.rounded-full');
    this.apiDocsButton = page.locator('button:has-text("API Docs")');
  }

  async goto(path: string = '/') {
    await this.page.goto(path);
    await this.waitForApp();
  }

  async waitForApp() {
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
    const statusClass = await this.connectionStatus.first().getAttribute('class');
    return statusClass?.includes('bg-green-500') || false;
  }

  async waitForConnection(timeout: number = 10000) {
    await this.page.waitForFunction(
      () => {
        const indicator = document.querySelector('.w-2.h-2.rounded-full');
        return indicator?.classList.contains('bg-green-500');
      },
      { timeout }
    );
  }

  async getActiveNavItem(): Promise<string | null> {
    const activeLink = await this.page.locator('a.bg-blue-100').textContent();
    return activeLink;
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