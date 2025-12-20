import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class PeoplePage extends BasePage {
  readonly addPersonButton: Locator;
  readonly personNameInput: Locator;
  readonly savePersonButton: Locator;
  readonly peopleList: Locator;
  readonly searchInput: Locator;
  readonly deleteConfirmButton: Locator;
  readonly photoGrid: Locator;

  constructor(page: Page) {
    super(page);
    this.addPersonButton = page.locator('button:has-text("Add Person"), button:has-text("Add")');
    this.personNameInput = page.locator('input#person-name');
    this.savePersonButton = page.locator('button:has-text("Save Person")');
    this.peopleList = page.locator('[data-testid="people-list"]');
    this.searchInput = page.locator('input[placeholder*="Search people"]');
    this.deleteConfirmButton = page.locator('button:has-text("Confirm Delete")');
    this.photoGrid = page.locator('.grid.grid-cols-6 > div');
  }

  private async waitForEnabled(locator: Locator, timeoutMs: number = 15000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      if (await locator.isVisible().catch(() => false)) {
        if (await locator.isEnabled().catch(() => false)) return;
      }
      await this.page.waitForTimeout(200);
    }
    throw new Error('Element did not become enabled in time');
  }

  async addPerson(name: string, photoPaths: string[] = []) {
    await this.waitForEnabled(this.addPersonButton, 20000);
    await this.addPersonButton.click();
    await this.personNameInput.waitFor({ state: 'visible' });
    await this.personNameInput.fill(name);

    const photoCount = await this.waitForPhotoGrid();
    if (photoCount === 0) {
      throw new Error(
        'No indexed photos available to select on the People page. Ensure global setup indexed photos successfully.'
      );
    }

    // Select at least one available photo to enable Save
    const photosToSelect = Math.min(photoPaths.length || 3, photoCount);
    for (let i = 0; i < Math.max(1, photosToSelect); i++) {
      await this.photoGrid.nth(i).click();
      await this.page.waitForTimeout(150);
    }

    await this.waitForSaveEnabled();
    const createResponse = this.page.waitForResponse((resp) => {
      const url = resp.url();
      const method = resp.request().method();
      return (
        method === 'POST' &&
        (url.includes('/api/people') || url.endsWith('/people')) &&
        resp.status() >= 200 &&
        resp.status() < 300
      );
    });
    await this.savePersonButton.click();
    await createResponse;
    await this.waitForSaveComplete();
    await this.page.waitForTimeout(500);

    // Ensure the person appears in the list before continuing
    await this.page
      .locator('[data-testid="person-item"]', { hasText: name })
      .first()
      .waitFor({ state: 'visible', timeout: 15000 });

    // Ensure loading has settled so the next action doesn't race a disabled button
    await this.waitForEnabled(this.addPersonButton, 20000);
  }

  async searchPerson(name: string) {
    await this.searchInput.fill(name);
    await expect(this.searchInput).toHaveValue(name);
    await this.page.waitForTimeout(500); // Debounce
  }

  async selectPerson(name: string) {
    const personItem = this.page.locator('[data-testid="person-item"]', { hasText: name }).first();
    await personItem.scrollIntoViewIfNeeded();
    await personItem.click();
  }

  async editPerson(oldName: string, newName: string) {
    const card = this.page.locator('[data-testid="person-item"]', { hasText: oldName }).first();
    await card.locator('button:has-text("Edit")').click();
    await this.personNameInput.waitFor({ state: 'visible' });
    await this.personNameInput.fill(newName);

    const photoCount = await this.waitForPhotoGrid();
    if (photoCount === 0) {
      throw new Error(
        'No indexed photos available to select while editing a person. Ensure global setup indexed photos successfully.'
      );
    }
    await this.photoGrid.first().click();

    await this.waitForSaveEnabled();
    await this.savePersonButton.click();
    await this.waitForSaveComplete();
    await this.page.waitForTimeout(500);
  }

  async deletePerson(name: string) {
    await this.selectPerson(name);
    await this.deleteConfirmButton.waitFor({ state: 'visible', timeout: 5000 });
    await this.waitForEnabled(this.deleteConfirmButton, 15000);
    const deleteResponse = this.page.waitForResponse((resp) => {
      const url = resp.url();
      const method = resp.request().method();
      return (
        method === 'DELETE' &&
        (url.includes('/api/people/') || url.includes('/people/')) &&
        resp.status() >= 200 &&
        resp.status() < 300
      );
    });
    await this.deleteConfirmButton.click();
    await deleteResponse;
    await this.waitForDeleteComplete();
    // Force refresh to avoid any stale cached GET /people responses in the browser context
    await this.page.reload();
    await this.waitForApp();
    // Ensure the person card is removed from the list
    await this.page
      .locator('[data-testid="person-item"]', { hasText: name })
      .first()
      .waitFor({ state: 'hidden', timeout: 15000 });
  }

  async getPeopleCount(): Promise<number> {
    const people = await this.page.locator('[data-testid="person-item"]').count();
    return people;
  }

  async searchByFace(name: string) {
    const card = this.page.locator('[data-testid="person-item"]', { hasText: name }).first();
    const findButton = card.locator('button:has-text("Find Photos")');

    await findButton.waitFor({ state: 'visible', timeout: 5000 });

    // Wait until the button is enabled (it is disabled when face search is off)
    for (let i = 0; i < 20; i++) {
      if (await findButton.isEnabled()) break;
      await this.page.waitForTimeout(500);
    }

    await findButton.click();
    await this.page.waitForURL('**/?face=*', { timeout: 15000 });
  }

  async getPersonPhotos(name: string): Promise<number> {
    const card = this.page.locator('[data-testid="person-item"]', { hasText: name }).first();
    const countText = await card.locator('[data-testid="photo-count"]').textContent();
    const match = countText?.match(/(\d+)\s+sample/);
    return match ? parseInt(match[1]) : 0;
  }

  async addPhotosToExistingPerson(name: string, _photoPaths: string[] = []) {
    const card = this.page.locator('[data-testid="person-item"]', { hasText: name }).first();
    await card.locator('button:has-text("Edit")').click();
    await this.personNameInput.waitFor({ state: 'visible' });
    
    await this.waitForPhotoGrid();
    
    // Find an unselected photo and select it
    const items = this.photoGrid;
    const count = await items.count();
    let added = false;
    
    for (let i = 0; i < count; i++) {
        const item = items.nth(i);
        // Check if selected (has checkmark)
        const isSelected = await item.locator('.bg-primary.text-primary-foreground').isVisible().catch(() => false);
        
        if (!isSelected) {
            await item.click();
            added = true;
            break; 
        }
    }
    
    if (!added && count > 0) {
        // If all selected, deselect one? Or maybe we can't add more.
        console.log('Could not find unselected photo to add');
    }

    await this.savePersonButton.click();
    await this.waitForSaveComplete();
    await this.page.waitForTimeout(500);
  }

  async waitForSaveComplete() {
    await this.page.waitForTimeout(500);
    
    // Check for error
    const errorAlert = this.page.locator('.text-destructive[role="alert"]');
    if (await errorAlert.isVisible()) {
        const errorText = await errorAlert.textContent();
        throw new Error(`Failed to save person: ${errorText}`);
    }

    // The toast shows just "Saved" text
    const toast = this.page.locator('[role="alert"]', { hasText: 'Saved' });
    try {
        await toast.waitFor({ state: 'visible', timeout: 15000 });
    } catch (e) {
        console.log('Save toast not found - checking for error again');
        if (await errorAlert.isVisible()) {
            const errorText = await errorAlert.textContent();
            throw new Error(`Failed to save person: ${errorText}`);
        }
        console.log('No error found, continuing anyway');
    }
    
    // Wait for toast to disappear
    await toast.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
    // Wait for form to close
    await this.page.waitForTimeout(1000);
  }

  async waitForDeleteComplete() {
    await this.page.waitForTimeout(500);
    const toast = await this.page.locator('[role="alert"]:has-text("Deleted")');
    await toast.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    await toast.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
  }

  async getAllPeople(): Promise<string[]> {
    const peopleElements = await this.page.locator('[data-testid="person-item"] h3').allTextContents();
    return peopleElements;
  }

  private async waitForPhotoGrid(): Promise<number> {
    const loadingText = this.page.locator('text=Loading photos');
    const emptyState = this.page.locator('text=No indexed photos found');

    const start = Date.now();
    while (Date.now() - start < 20000) {
      if (await emptyState.isVisible().catch(() => false)) return 0;
      const count = await this.photoGrid.count();
      if (count > 0) return count;
      // If we see loading, keep waiting; if we don't, still allow time for initial render.
      await loadingText.isVisible().catch(() => false);
      await this.page.waitForTimeout(200);
    }

    return await this.photoGrid.count();
  }

  private async waitForSaveEnabled() {
    const start = Date.now();
    while (Date.now() - start < 15000) {
      if (await this.savePersonButton.isEnabled()) return;
      await this.page.waitForTimeout(200);
    }
    throw new Error('Save button did not become enabled in time');
  }
}