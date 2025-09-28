import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class SettingsPage extends BasePage {
  readonly rootFoldersSection: Locator;
  readonly addFolderButton: Locator;
  readonly folderInput: Locator;
  readonly saveButton: Locator;
  readonly resetButton: Locator;
  readonly indexingButton: Locator;
  readonly indexingStatus: Locator;
  readonly progressBar: Locator;
  readonly ocrToggle: Locator;
  readonly faceSearchToggle: Locator;
  readonly semanticSearchToggle: Locator;
  readonly batchSizeInput: Locator;
  readonly thumbnailSizeSelect: Locator;

  constructor(page: Page) {
    super(page);
    this.rootFoldersSection = page.locator('text=Photo Directories').locator('..');
    this.addFolderButton = page.locator('button:has-text("Add")');
    this.folderInput = page.locator('input[placeholder*="path/to/your/photos"]');
    this.saveButton = page.locator('button:has-text("Save Configuration")');
    this.resetButton = page.locator('button:has-text("Reset to Defaults")');
    this.indexingButton = page.locator('button:has-text("Start Incremental")');
    this.indexingStatus = page.locator('text=Current Status').locator('..');
    this.progressBar = page.locator('.h-2').first(); // Progress bar
    this.ocrToggle = page.locator('#ocr-eng'); // English OCR checkbox
    this.faceSearchToggle = page.locator('#face-search'); // Face search switch
    this.semanticSearchToggle = page.locator('#semantic-search');
    this.batchSizeInput = page.locator('#batch-size');
    this.thumbnailSizeSelect = page.locator('#thumbnail-size');
  }

  async addRootFolder(path: string) {
    await this.folderInput.fill(path);
    await this.addFolderButton.click();
    await this.page.waitForTimeout(500);
  }

  async removeRootFolder(index: number) {
    // Click the trash icon for the folder at the given index
    const folderItems = this.page.locator('.font-mono.text-sm');
    const folder = folderItems.nth(index);
    const removeButton = folder.locator('..').locator('button').first();
    await removeButton.click();
    await this.page.waitForTimeout(500);
  }

  async getRootFolders(): Promise<string[]> {
    const folders = await this.page.locator('.font-mono.text-sm').allTextContents();
    return folders.map(f => f.trim());
  }

  async startIndexing(fullIndex: boolean = false) {
    if (fullIndex) {
      const fullIndexButton = this.page.locator('button:has-text("Full Re-Index")');
      await fullIndexButton.click();
    } else {
      await this.indexingButton.click();
    }
    await this.page.waitForTimeout(1000);
  }

  async stopIndexing() {
    const stopButton = this.page.locator('button:has-text("Stop")');
    await stopButton.click();
    await this.page.waitForTimeout(1000);
  }

  async getIndexingStatus() {
    // Navigate to Storage & Indexing tab first
    await this.page.locator('button:has-text("Storage & Indexing")').click();
    await this.page.waitForTimeout(500);

    const statusBadge = this.page.locator('text=Current Status').locator('..').locator('.capitalize');
    const status = await statusBadge.textContent().catch(() => 'idle');

    // Try to get progress if visible
    let progress = 0;
    const progressBar = this.page.locator('.h-2').first();
    if (await progressBar.isVisible().catch(() => false)) {
      const value = await progressBar.getAttribute('aria-valuenow');
      progress = value ? parseInt(value) : 0;
    }

    return {
      status: status?.trim() || 'idle',
      progress
    };
  }

  async waitForIndexingComplete(timeout: number = 60000) {
    await this.page.waitForFunction(
      () => {
        const status = document.querySelector('[data-testid="indexing-status"]');
        return status?.textContent?.includes('Complete') || status?.textContent?.includes('Idle');
      },
      { timeout }
    );
  }

  async waitForIndexingStart() {
    await this.page.waitForFunction(
      () => {
        const status = document.querySelector('[data-testid="indexing-status"]');
        return status?.textContent?.includes('Indexing') || status?.textContent?.includes('Processing');
      },
      { timeout: 10000 }
    );
  }

  async toggleOCR(enable: boolean) {
    // Navigate to Features tab first
    await this.page.locator('button:has-text("Search Features")').click();
    await this.page.waitForTimeout(500);

    const isChecked = await this.ocrToggle.isChecked();
    if (isChecked !== enable) {
      await this.ocrToggle.click();
      // Save manually since toggle doesn't auto-save
      await this.saveButton.click();
      await this.waitForSaveComplete();
    }
  }

  async toggleFaceSearch(enable: boolean) {
    // Navigate to Features tab first
    await this.page.locator('button:has-text("Search Features")').click();
    await this.page.waitForTimeout(500);

    const isChecked = await this.faceSearchToggle.isChecked();
    if (isChecked !== enable) {
      await this.faceSearchToggle.click();
      // Save manually since toggle doesn't auto-save
      await this.saveButton.click();
      await this.waitForSaveComplete();
    }
  }

  async toggleSemanticSearch(enable: boolean) {
    // Navigate to Features tab first
    await this.page.locator('button:has-text("Search Features")').click();
    await this.page.waitForTimeout(500);

    const isChecked = await this.semanticSearchToggle.isChecked();
    if (isChecked !== enable) {
      await this.semanticSearchToggle.click();
      // Save manually since toggle doesn't auto-save
      await this.saveButton.click();
      await this.waitForSaveComplete();
    }
  }

  async setBatchSize(size: number) {
    // Navigate to Features tab first
    await this.page.locator('button:has-text("Search Features")').click();
    await this.page.waitForTimeout(500);

    await this.batchSizeInput.fill(size.toString());
    // Save manually
    await this.saveButton.click();
    await this.waitForSaveComplete();
  }

  async setThumbnailSize(size: string) {
    // Navigate to Features tab first
    await this.page.locator('button:has-text("Search Features")').click();
    await this.page.waitForTimeout(500);

    await this.thumbnailSizeSelect.selectOption(size);
    // Save manually
    await this.saveButton.click();
    await this.waitForSaveComplete();
  }

  async resetConfiguration() {
    // Reset button not in new UI, just clear folders and save
    const folders = await this.getRootFolders();
    for (let i = folders.length - 1; i >= 0; i--) {
      await this.removeRootFolder(i);
    }
    await this.saveButton.click();
    await this.waitForSaveComplete();
  }

  async waitForSaveComplete() {
    await this.page.waitForTimeout(500);
    // Look for success toast
    const toast = this.page.locator('text=Configuration saved successfully');
    await toast.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    await toast.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  async getConfiguration() {
    // Navigate to Features tab to check settings
    await this.page.locator('button:has-text("Search Features")').click();
    await this.page.waitForTimeout(500);

    const semanticSearchEnabled = await this.semanticSearchToggle.isChecked().catch(() => false);
    const batchSize = await this.batchSizeInput.inputValue().catch(() => '50');
    const thumbnailSize = await this.thumbnailSizeSelect.inputValue().catch(() => 'medium');

    return {
      ocrEnabled: await this.ocrToggle.isChecked(),
      faceSearchEnabled: await this.faceSearchToggle.isChecked(),
      semanticSearchEnabled,
      batchSize,
      thumbnailSize
    };
  }
}