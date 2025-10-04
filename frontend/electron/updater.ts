import { app, dialog } from 'electron';

// Lazily resolve autoUpdater and logger to avoid hard dependency in dev
let autoUpdater: any = null;
let log: any = null;

function ensureAutoUpdater(): boolean {
  if (autoUpdater && log) return true;
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const updater = require('electron-updater');
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    log = require('electron-log');
    autoUpdater = updater.autoUpdater;

    // Configure logging
    autoUpdater.logger = log;
    (autoUpdater.logger as typeof log).transports.file.level = 'info';

    // Auto-update configuration
    autoUpdater.autoDownload = false; // Ask user before downloading
    autoUpdater.autoInstallOnAppQuit = true; // Install updates on quit
    return true;
  } catch (e) {
    console.warn('[Updater] Auto-updater unavailable:', (e as any)?.message || e);
    return false;
  }
}

export function initializeAutoUpdater() {
  // Skip auto-update in development
  if (process.env.NODE_ENV === 'development') {
    console.log('[Updater] Auto-updater disabled in development mode');
    return;
  }

  if (!ensureAutoUpdater()) {
    console.warn('[Updater] initializeAutoUpdater skipped: auto-updater not available');
    return;
  }

  // Check for updates on startup (after a delay)
  setTimeout(() => {
    checkForUpdates();
  }, 5000);

  // Set up auto-update event listeners
  setupUpdateListeners();
}

function setupUpdateListeners() {
  if (!ensureAutoUpdater()) return;
  autoUpdater.on('checking-for-update', () => {
    log.info('Checking for updates...');
  });

  autoUpdater.on('update-available', (info: any) => {
    log.info('Update available:', info.version);

    dialog
      .showMessageBox({
        type: 'info',
        title: 'Update Available',
        message: `A new version (${info.version}) is available!`,
        detail: 'Would you like to download it now? The update will be installed when you quit the app.',
        buttons: ['Download', 'Later'],
        defaultId: 0,
        cancelId: 1,
      })
      .then((result) => {
        if (result.response === 0) {
          // User clicked "Download"
          autoUpdater.downloadUpdate();
        }
      });
  });

  autoUpdater.on('update-not-available', (info: any) => {
    log.info('Update not available. Current version:', info.version);
  });

  autoUpdater.on('error', (err: any) => {
    log.error('Error in auto-updater:', err);
  });

  autoUpdater.on('download-progress', (progressObj: any) => {
    const logMessage = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}%`;
    log.info(logMessage);
  });

  autoUpdater.on('update-downloaded', (info: any) => {
    log.info('Update downloaded:', info.version);

    dialog
      .showMessageBox({
        type: 'info',
        title: 'Update Ready',
        message: 'Update downloaded successfully!',
        detail:
          'The update will be automatically installed when you close the application. Would you like to restart now?',
        buttons: ['Restart Now', 'Later'],
        defaultId: 0,
        cancelId: 1,
      })
      .then((result) => {
        if (result.response === 0) {
          // User clicked "Restart Now"
          setImmediate(() => {
            app.removeAllListeners('window-all-closed');
            autoUpdater.quitAndInstall(false, true);
          });
        }
      });
  });
}

export function checkForUpdates() {
  if (process.env.NODE_ENV === 'development') {
    console.log('[Updater] Skipping update check in development');
    return;
  }

  if (!ensureAutoUpdater()) {
    console.warn('[Updater] checkForUpdates skipped: auto-updater not available');
    return;
  }

  autoUpdater.checkForUpdates().catch((err: any) => {
    log.error('Failed to check for updates:', err);
  });
}

export function checkForUpdatesManually() {
  if (process.env.NODE_ENV === 'development') {
    dialog.showMessageBox({
      type: 'info',
      title: 'Updates',
      message: 'Auto-update is disabled in development mode',
    });
    return;
  }

  if (!ensureAutoUpdater()) {
    dialog.showMessageBox({
      type: 'info',
      title: 'Updates',
      message: 'Update subsystem not available',
    });
    return;
  }

  autoUpdater
    .checkForUpdates()
    .then((result: any) => {
      if (!result || !result.updateInfo) {
        dialog.showMessageBox({
          type: 'info',
          title: 'No Updates',
          message: 'You are running the latest version!',
        });
      }
    })
    .catch((err: any) => {
      log.error('Failed to check for updates:', err);
      dialog.showMessageBox({
        type: 'error',
        title: 'Update Error',
        message: 'Failed to check for updates',
        detail: err.message,
      });
    });
}
