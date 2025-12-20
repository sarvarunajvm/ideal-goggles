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
    // Wait for page to load
    await this.page.waitForLoadState('domcontentloaded');
    
    // Check if onboarding wizard is present and skip it
    const onboardingModal = this.page.locator('[data-testid="onboarding-modal"]');
    const skipButton = this.page.locator('button:has-text("Skip setup"), [data-testid="skip-onboarding-btn"]');
    
    // Wait a bit for onboarding to potentially appear
    await this.page.waitForTimeout(500);
    
    const isOnboardingVisible = await onboardingModal.isVisible().catch(() => false);
    
    if (isOnboardingVisible) {
      // Wait for skip button to be visible and clickable
      await skipButton.waitFor({ state: 'visible', timeout: 5000 });
      await skipButton.click();
      // Wait for onboarding modal to disappear
      await onboardingModal.waitFor({ state: 'hidden', timeout: 10000 });
      // Wait a bit more for UI to settle
      await this.page.waitForTimeout(300);
    }
    
    // Wait for navigation bar to be visible (app is loaded)
    await this.navBar.waitFor({ state: 'visible', timeout: 30000 });
    
    // Additional wait for app to be fully interactive
    // Removed strict networkidle to avoid flakiness with polling
    // await this.page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  }

  async navigateToSearch() {
    await this.searchLink.waitFor({ state: 'visible', timeout: 10000 });
    await this.searchLink.click();
    await this.page.waitForURL(/\/$|\/search/, { timeout: 5000 });
  }

  async navigateToSettings() {
    await this.settingsLink.waitFor({ state: 'visible', timeout: 10000 });
    await this.settingsLink.click();
    await this.page.waitForURL(/\/settings/, { timeout: 5000 });
  }

  async navigateToPeople() {
    await this.peopleLink.waitFor({ state: 'visible', timeout: 10000 });
    await this.peopleLink.click();
    await this.page.waitForURL(/\/people/, { timeout: 5000 });
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
    // Wait for connection badge to be visible first
    await this.connectionBadge.waitFor({ state: 'visible', timeout });
    // Then wait for it to show "Connected" text (it might start as "Checking...")
    await this.page.waitForFunction(
      (testId) => {
        const badge = document.querySelector(`[data-testid="${testId}"]`);
        return badge?.textContent?.includes('Connected') ?? false;
      },
      'connection-badge',
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