import { Page, Locator } from '@playwright/test';
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

  async addPerson(name: string, photoPaths: string[] = []) {
    await this.addPersonButton.click();
    await this.personNameInput.waitFor({ state: 'visible' });
    await this.personNameInput.fill(name);

    const photoCount = await this.waitForPhotoGrid();

    // Select at least one available photo to enable Save
    const photosToSelect = Math.min(photoPaths.length || 3, Math.max(photoCount, 1));
    for (let i = 0; i < Math.min(photoCount, photosToSelect); i++) {
      await this.photoGrid.nth(i).click();
      await this.page.waitForTimeout(150);
    }

    await this.waitForSaveEnabled();
    await this.savePersonButton.click();
    await this.waitForSaveComplete();
    await this.page.waitForTimeout(500);
  }

  async searchPerson(name: string) {
    await this.searchInput.fill(name);
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
    if (photoCount > 0) {
      await this.photoGrid.first().click();
    }

    await this.waitForSaveEnabled();
    await this.savePersonButton.click();
    await this.waitForSaveComplete();
    await this.page.waitForTimeout(500);
  }

  async deletePerson(name: string) {
    await this.selectPerson(name);
    await this.deleteConfirmButton.waitFor({ state: 'visible', timeout: 5000 });
    await this.deleteConfirmButton.click();
    await this.waitForDeleteComplete();
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

  async waitForSaveComplete() {
    await this.page.waitForTimeout(500);
    // The toast shows just "Saved" text
    const toast = this.page.locator('[role="alert"]', { hasText: 'Saved' });
    await toast.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {
      console.log('Save toast not found - continuing anyway');
    });
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
    // Wait for loading indicator to disappear if present
    const loadingText = this.page.locator('text=Loading photos');
    await loadingText.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});

    // Wait for grid items or empty state
    await this.page.waitForTimeout(300);
    await this.photoGrid.first().waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    return this.photoGrid.count();
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