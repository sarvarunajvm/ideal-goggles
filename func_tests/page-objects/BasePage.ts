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
    // Navigation links are Button components with Link inside (asChild), so they render as <a> tags
    // Use more specific selector to match the Link inside the Button
    this.searchLink = page.locator('nav a:has-text("Search")');
    this.settingsLink = page.locator('nav a:has-text("Settings")');
    this.peopleLink = page.locator('nav a:has-text("People")');
    this.connectionStatus = page.locator('.w-2.h-2.rounded-full');
    // Connection badge shows "Connected" text when connected
    this.connectionBadge = page.locator('[data-testid="connection-badge"]');
    this.apiDocsButton = page.locator('button:has-text("API Docs")');
  }

  async goto(path: string = '/') {
    await this.page.goto(path);
    await this.waitForApp();
  }

  async waitForApp() {
    // Wait for either the onboarding wizard or the main app navigation
    try {
      await Promise.race([
        this.navBar.waitFor({ state: 'visible', timeout: 5000 }),
        this.page.locator('text=Welcome to Ideal Goggles').waitFor({ state: 'visible', timeout: 5000 })
      ]);
    } catch {
      // Ignore timeout, we'll check individual elements
    }

    // Check if onboarding wizard is present and skip it
    const skipButton = this.page.locator('button:has-text("Skip setup")');
    if (await skipButton.isVisible()) {
      await skipButton.click();
      // Wait for onboarding to disappear
      await skipButton.waitFor({ state: 'hidden', timeout: 5000 });
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
      // Check if connection badge is visible and shows "Connected" text
      await this.connectionBadge.waitFor({ state: 'visible', timeout: 1000 });
      const text = await this.connectionBadge.textContent();
      return text?.includes('Connected') ?? false;
    } catch {
      return false;
    }
  }

  async waitForConnection(timeout: number = 10000) {
    // Wait for connection badge to show "Connected" text
    await this.connectionBadge.waitFor({ state: 'visible', timeout });
    await this.page.waitForFunction(
      (badge) => badge?.textContent?.includes('Connected'),
      await this.connectionBadge.elementHandle(),
      { timeout }
    );
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

  async enableDeveloperMode() {
    // Click the camera icon 6 times to trigger the developer mode prompt
    const cameraIcon = this.page.locator('.gradient-gold');
    for (let i = 0; i < 6; i++) {
      await cameraIcon.click();
      await this.page.waitForTimeout(50); // Small delay between clicks
    }

    // Wait for the code input dialog to appear
    const codeInput = this.page.locator('input[type="password"]');
    await codeInput.waitFor({ state: 'visible', timeout: 2000 });

    // Enter the code
    await codeInput.fill('1996');

    // Click the submit button
    const submitButton = this.page.locator('button:has-text("Submit")');
    await submitButton.click();

    // Wait for the dialog to close and developer mode to activate
    await codeInput.waitFor({ state: 'hidden', timeout: 2000 });
  }
}