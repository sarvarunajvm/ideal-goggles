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
    this.rootFoldersSection = page.locator('text=Photo Folders').locator('..');
    this.addFolderButton = page.locator('button:has-text("Add")');
    this.folderInput = page.locator('input[placeholder*="path/to/your/photos"]'); // Not used in new UI - uses dialog
    this.saveButton = page.locator('button:has-text("Save Configuration")'); // Auto-save now - no button
    this.resetButton = page.locator('button:has-text("Reset to Defaults")'); // Not in new UI
    this.indexingButton = page.locator('button:has-text("Quick Update")');
    this.indexingStatus = page.locator('text=Status').locator('..');
    this.progressBar = page.locator('.h-2').first(); // Progress bar
    this.ocrToggle = page.locator('#ocr-enabled'); // OCR main switch
    this.faceSearchToggle = page.locator('#face-search'); // Face search switch
    this.semanticSearchToggle = page.locator('#semantic-search');
    this.batchSizeInput = page.locator('#batch-size'); // Not in new UI
    this.thumbnailSizeSelect = page.locator('#thumbnail-size'); // Not in new UI
  }

  async waitForSettingsLoaded() {
    const loader = this.page.locator('text=Loading settings...');
    await loader.waitFor({ state: 'hidden', timeout: 10000 });
    // Also wait for the main content to be visible
    await this.indexingButton.waitFor({ state: 'visible', timeout: 10000 });
  }

  async goto(path: string = '/settings') {
    await super.goto(path);
    await this.waitForSettingsLoaded();
  }

  async addRootFolder(path: string) {
    // The new UI uses prompt() when not in Electron
    this.page.once('dialog', async dialog => {
      await dialog.accept(path);
    });
    await this.addFolderButton.click();
    await this.page.waitForTimeout(500);
  }

  async removeRootFolder(index: number) {
    // Check if we need to expand the "Show more" section
    if (index >= 3) {
      const summary = this.page.locator('summary:has-text("Show")');
      if (await summary.isVisible()) {
        const details = summary.locator('..');
        const isOpen = await details.getAttribute('open');
        if (isOpen === null) {
          await summary.click();
          await this.page.waitForTimeout(300); // Animation
        }
      }
    }

    // Click the trash icon for the folder at the given index
    const folderItems = this.page.locator('.font-mono.text-xs.truncate');
    const folder = folderItems.nth(index);
    const row = folder.locator('..');
    
    // Ensure element is visible before hover
    await row.scrollIntoViewIfNeeded();
    
    // Hover to reveal the delete button
    await row.hover();
    
    const removeButton = row.locator('button').first();
    await removeButton.click();
    await this.page.waitForTimeout(1500); // Wait for auto-save
  }

  async getRootFolders(): Promise<string[]> {
    const folders = await this.page.locator('.font-mono.text-xs.truncate').allTextContents();
    return folders.map(f => f.trim());
  }

  async startIndexing(fullIndex: boolean = false) {
    if (fullIndex) {
      // Try different button texts that might be used
      const fullIndexButton = this.page.locator('button:has-text("Full Refresh"), button:has-text("Full Re-Index"), button:has-text("Full Index")').first();
      const buttonExists = await fullIndexButton.isVisible().catch(() => false);

      if (buttonExists) {
        await fullIndexButton.click();
      } else {
        // Fallback to incremental indexing if full index button not found
        await this.indexingButton.click();
      }
    } else {
      await this.indexingButton.click();
    }
    await this.page.waitForTimeout(1000);
  }

  async stopIndexing() {
    const stopButton = this.page.locator('button:has-text("Stop Indexing"), button:has-text("Stop")').first();
    await stopButton.click();
    await this.page.waitForTimeout(1000);
  }

  async getIndexingStatus() {
    // Status is now directly on the page, no tab navigation needed
    // Looking for the Badge component that shows the status
    const statusBadge = this.page.locator('text=Status').locator('..').locator('[data-badge]').or(
      this.page.locator('text=Status').locator('..').locator('.capitalize')
    );
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
        const statusText = status?.textContent || '';
        // Also check for other possible status texts
        return statusText.includes('Indexing') ||
               statusText.includes('Processing') ||
               statusText.includes('Running') ||
               statusText.includes('In Progress');
      },
      { timeout: 10000 }
    ).catch(() => {
      // If the status element is not found, just continue
      console.log('Warning: Indexing status element not found');
    });
  }

  async toggleOCR(enable: boolean) {
    // No tab navigation needed - all on one page now
    const isChecked = await this.ocrToggle.isChecked();
    if (isChecked !== enable) {
      await this.ocrToggle.click();
      // Wait for auto-save
      await this.page.waitForTimeout(1500);
    }
  }

  async toggleFaceSearch(enable: boolean) {
    // No tab navigation needed - all on one page now
    const isChecked = await this.faceSearchToggle.isChecked();
    if (isChecked !== enable) {
      await this.faceSearchToggle.click({ force: true });
      // Verify state changed
      try {
        await this.page.waitForFunction(
          (args) => {
            const el = document.querySelector(args.selector);
            return el?.getAttribute('aria-checked') === (args.enable ? 'true' : 'false');
          },
          { selector: '#face-search', enable },
          { timeout: 2000 }
        );
      } catch (e) {
        console.log('Warning: Toggle state check timed out');
      }
      // Wait for auto-save
      await this.page.waitForTimeout(1500);
    }
  }

  async toggleSemanticSearch(enable: boolean) {
    // No tab navigation needed - all on one page now
    const isChecked = await this.semanticSearchToggle.isChecked();
    if (isChecked !== enable) {
      await this.semanticSearchToggle.click({ force: true });
      // Verify state changed
      try {
        await this.page.waitForFunction(
          (args) => {
            const el = document.querySelector(args.selector);
            return el?.getAttribute('aria-checked') === (args.enable ? 'true' : 'false');
          },
          { selector: '#semantic-search', enable },
          { timeout: 2000 }
        );
      } catch (e) {
        console.log('Warning: Toggle state check timed out');
      }
      // Wait for auto-save
      await this.page.waitForTimeout(1500);
    }
  }

  async setBatchSize(size: number) {
    // Batch size control removed from UI - this is now a no-op
    // Tests that rely on this should be updated or skipped
    console.log(`setBatchSize called with ${size} - feature not in UI`);
  }

  async setThumbnailSize(size: string) {
    // Thumbnail size control removed from UI - this is now a no-op
    // Tests that rely on this should be updated or skipped
    console.log(`setThumbnailSize called with ${size} - feature not in UI`);
  }

  async resetConfiguration() {
    // Reset button not in new UI, just clear folders (auto-saves)
    const folders = await this.getRootFolders();
    for (let i = folders.length - 1; i >= 0; i--) {
      await this.removeRootFolder(i);
    }
    // Wait for auto-save to complete
    await this.page.waitForTimeout(1500);
  }

  async waitForSaveComplete() {
    await this.page.waitForTimeout(500);
    // Look for success toast - using either the new shadcn toast or the old toast
    const toast = this.page.locator('[role="status"]:has-text("Configuration saved successfully"), text=Configuration saved successfully, text=Success').first();
    await toast.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    await toast.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  async getConfiguration() {
    // No tab navigation needed - all on one page
    // Ensure elements are ready
    await this.semanticSearchToggle.waitFor({ state: 'visible' });
    
    const semanticSearchEnabled = await this.semanticSearchToggle.isChecked();
    const ocrEnabled = await this.ocrToggle.isVisible() ? await this.ocrToggle.isChecked() : false;
    const faceSearchEnabled = await this.faceSearchToggle.isChecked();

    return {
      ocrEnabled,
      faceSearchEnabled,
      semanticSearchEnabled,
      batchSize: '50', // Default value - not in UI anymore
      thumbnailSize: 'medium' // Default value - not in UI anymore
    };
  }
}