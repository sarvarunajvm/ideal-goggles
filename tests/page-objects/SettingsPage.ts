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
    this.rootFoldersSection = page.locator('[data-testid="root-folders"]');
    this.addFolderButton = page.locator('button:has-text("Add Folder")');
    this.folderInput = page.locator('input[placeholder*="folder path"]');
    this.saveButton = page.locator('button:has-text("Save")');
    this.resetButton = page.locator('button:has-text("Reset")');
    this.indexingButton = page.locator('button:has-text("Start Indexing")');
    this.indexingStatus = page.locator('[data-testid="indexing-status"]');
    this.progressBar = page.locator('[role="progressbar"]');
    this.ocrToggle = page.locator('input[name="ocr_enabled"]');
    this.faceSearchToggle = page.locator('input[name="face_search_enabled"]');
    this.semanticSearchToggle = page.locator('input[name="semantic_search_enabled"]');
    this.batchSizeInput = page.locator('input[name="batch_size"]');
    this.thumbnailSizeSelect = page.locator('select[name="thumbnail_size"]');
  }

  async addRootFolder(path: string) {
    await this.addFolderButton.click();
    await this.folderInput.fill(path);
    await this.saveButton.click();
    await this.waitForSaveComplete();
  }

  async removeRootFolder(index: number) {
    const removeButton = await this.page.locator(`[data-testid="remove-folder-${index}"]`);
    await removeButton.click();
    await this.page.locator('button:has-text("Confirm")').click();
    await this.waitForSaveComplete();
  }

  async getRootFolders(): Promise<string[]> {
    const folders = await this.page.locator('[data-testid="folder-item"]').allTextContents();
    return folders;
  }

  async startIndexing(fullIndex: boolean = false) {
    if (fullIndex) {
      const fullIndexCheckbox = await this.page.locator('input[name="full_index"]');
      await fullIndexCheckbox.check();
    }
    await this.indexingButton.click();
    await this.waitForIndexingStart();
  }

  async stopIndexing() {
    const stopButton = await this.page.locator('button:has-text("Stop Indexing")');
    await stopButton.click();
    await this.page.waitForTimeout(1000);
  }

  async getIndexingStatus() {
    const status = await this.indexingStatus.textContent();
    const progress = await this.progressBar.getAttribute('aria-valuenow');
    return {
      status,
      progress: progress ? parseInt(progress) : 0
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
    const isChecked = await this.ocrToggle.isChecked();
    if (isChecked !== enable) {
      await this.ocrToggle.click();
      await this.waitForSaveComplete();
    }
  }

  async toggleFaceSearch(enable: boolean) {
    const isChecked = await this.faceSearchToggle.isChecked();
    if (isChecked !== enable) {
      await this.faceSearchToggle.click();
      await this.waitForSaveComplete();
    }
  }

  async toggleSemanticSearch(enable: boolean) {
    const isChecked = await this.semanticSearchToggle.isChecked();
    if (isChecked !== enable) {
      await this.semanticSearchToggle.click();
      await this.waitForSaveComplete();
    }
  }

  async setBatchSize(size: number) {
    await this.batchSizeInput.clear();
    await this.batchSizeInput.fill(size.toString());
    await this.saveButton.click();
    await this.waitForSaveComplete();
  }

  async setThumbnailSize(size: string) {
    await this.thumbnailSizeSelect.selectOption(size);
    await this.saveButton.click();
    await this.waitForSaveComplete();
  }

  async resetConfiguration() {
    await this.resetButton.click();
    await this.page.locator('button:has-text("Confirm Reset")').click();
    await this.waitForSaveComplete();
  }

  async waitForSaveComplete() {
    await this.page.waitForTimeout(500);
    const toast = await this.page.locator('[role="alert"]:has-text("Saved")');
    await toast.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    await toast.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
  }

  async getConfiguration() {
    return {
      ocrEnabled: await this.ocrToggle.isChecked(),
      faceSearchEnabled: await this.faceSearchToggle.isChecked(),
      semanticSearchEnabled: await this.semanticSearchToggle.isChecked(),
      batchSize: await this.batchSizeInput.inputValue(),
      thumbnailSize: await this.thumbnailSizeSelect.inputValue()
    };
  }
}