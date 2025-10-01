import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class PeoplePage extends BasePage {
  readonly addPersonButton: Locator;
  readonly personNameInput: Locator;
  readonly uploadPhotoButton: Locator;
  readonly savePersonButton: Locator;
  readonly peopleList: Locator;
  readonly searchInput: Locator;
  readonly deleteButton: Locator;
  readonly editButton: Locator;
  readonly photoGallery: Locator;

  constructor(page: Page) {
    super(page);
    this.addPersonButton = page.locator('button:has-text("Add Person")');
    this.personNameInput = page.locator('input#person-name');
    this.uploadPhotoButton = page.locator('button:has-text("Upload Photos")');
    this.savePersonButton = page.locator('button:has-text("Save Person")').first();
    this.peopleList = page.locator('[data-testid="people-list"]');
    this.searchInput = page.locator('input[placeholder*="Search people"]');
    this.deleteButton = page.locator('[data-testid="person-item"] button:has-text("Delete")').first();
    this.editButton = page.locator('[data-testid="person-item"] button:has-text("Edit")').first();
    this.photoGallery = page.locator('[data-testid="photo-gallery"]');
  }

  async addPerson(name: string, photoPaths: string[]) {
    await this.addPersonButton.click();
    await this.personNameInput.fill(name);

    // Upload photos - use the file input that appears after clicking upload button
    const fileInput = this.page.locator('input#new-person-file');
    await fileInput.setInputFiles(photoPaths);

    await this.savePersonButton.click();
    await this.waitForSaveComplete();
  }

  async searchPerson(name: string) {
    await this.searchInput.fill(name);
    await this.page.waitForTimeout(500); // Debounce
  }

  async selectPerson(name: string) {
    const personItem = await this.page.locator(`[data-testid="person-item"]:has-text("${name}")`);
    await personItem.click();
  }

  async editPerson(oldName: string, newName: string) {
    await this.selectPerson(oldName);
    await this.editButton.click();
    // Wait for the form to appear and find the name input
    await this.page.waitForTimeout(500);
    const nameInput = this.page.locator('input#person-name');
    await nameInput.clear();
    await nameInput.fill(newName);
    // Click the first Save Person button (in the form)
    await this.page.locator('button:has-text("Save Person")').first().click();
    await this.waitForSaveComplete();
    // Wait for the list to refresh
    await this.page.waitForTimeout(1000);
  }

  async deletePerson(name: string) {
    await this.selectPerson(name);
    await this.deleteButton.click();
    await this.page.locator('button:has-text("Confirm Delete")').click();
    await this.waitForDeleteComplete();
  }

  async getPeopleCount(): Promise<number> {
    const people = await this.page.locator('[data-testid="person-item"]').count();
    return people;
  }

  async getPersonDetails(name: string) {
    await this.selectPerson(name);
    const photoCount = await this.page.locator('[data-testid="photo-count"]').textContent();
    const enrolledDate = await this.page.locator('[data-testid="enrolled-date"]').textContent();
    return {
      name,
      photoCount,
      enrolledDate
    };
  }

  async getPersonPhotos(name: string): Promise<number> {
    await this.selectPerson(name);
    const photos = await this.photoGallery.locator('img').count();
    return photos;
  }

  async addPhotosToExistingPerson(name: string, photoPaths: string[]) {
    await this.selectPerson(name);
    // The file input is specific to the selected person - find it first
    const fileInputs = await this.page.locator('input[type="file"]').all();
    // Use the last file input which should be for the selected person
    const fileInput = fileInputs[fileInputs.length - 1];
    await fileInput.setInputFiles(photoPaths);
    // Click the Save Person button for that specific person
    await this.page.locator('[data-testid="person-item"] button:has-text("Save Person")').click();
    await this.waitForSaveComplete();
  }

  async removePhotoFromPerson(name: string, photoIndex: number) {
    await this.selectPerson(name);

    // Wait for photos to load
    await this.photoGallery.waitFor({ state: 'visible' });
    const photos = await this.photoGallery.locator('img');
    await photos.nth(photoIndex).waitFor({ state: 'visible' });

    // Hover over the photo to reveal remove button
    await photos.nth(photoIndex).hover();

    // Wait for remove button and click it
    const removeButton = this.page.locator('[data-testid="remove-photo"]').nth(photoIndex);
    await removeButton.waitFor({ state: 'visible' });
    await removeButton.click();

    // Wait for confirmation dialog and confirm
    const confirmButton = this.page.locator('button#confirm-remove-btn');
    await confirmButton.waitFor({ state: 'visible', timeout: 5000 });
    await confirmButton.click();

    // Wait for the action to complete
    await this.waitForSaveComplete();

    // Wait a bit for the UI to update
    await this.page.waitForTimeout(500);
  }

  async searchByFace(name: string) {
    await this.selectPerson(name);
    const searchButton = this.page.locator('button:has-text("Search Photos of this Person")');

    // Wait for the button to be enabled (face search config to propagate)
    await searchButton.waitFor({ state: 'visible' });

    // Poll until button is enabled
    let isEnabled = false;
    for (let i = 0; i < 20; i++) { // Max 10 seconds
      isEnabled = await searchButton.isEnabled();
      if (isEnabled) break;
      await this.page.waitForTimeout(500);
    }

    if (!isEnabled) {
      throw new Error('Face search button remained disabled after 10 seconds');
    }

    await searchButton.click();
    await this.page.waitForURL('**/?face=*');
  }

  async waitForSaveComplete() {
    await this.page.waitForTimeout(500);
    const toast = await this.page.locator('[role="alert"]:has-text("Saved")');
    await toast.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    await toast.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
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
}