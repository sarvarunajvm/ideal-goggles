import { app, BrowserWindow, shell, ipcMain, dialog } from 'electron';
import { join } from 'path';
import { spawn, ChildProcess } from 'child_process';
import { existsSync, mkdirSync } from 'fs';

// Keep a global reference of the window object
let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;

const isDev = process.env.NODE_ENV === 'development';
const BACKEND_PORT = 8000;

// Backend management
async function startBackend(): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      // In development, assume backend is running separately
      if (isDev) {
        console.log('Development mode: assuming backend is running on port', BACKEND_PORT);
        resolve();
        return;
      }

      // In production, start the packaged backend binary (PyInstaller output)
      const backendPath = join(process.resourcesPath, 'backend');
      const binaryName = process.platform === 'win32' ? 'photo-search-backend.exe' : 'photo-search-backend';
      const backendExecutable = join(backendPath, binaryName);

      if (!existsSync(backendExecutable)) {
        console.error('Backend executable not found:', { backendExecutable });
        reject(new Error('Backend executable not found'));
        return;
      }

      // Compute writable data and cache directories under userData
      const userDataDir = app.getPath('userData');
      const dataDir = join(userDataDir, 'data');
      const cacheDir = join(userDataDir, 'cache');
      // Ensure directories exist
      mkdirSync(dataDir, { recursive: true });
      mkdirSync(cacheDir, { recursive: true });

      // Build database URL pointing to user data dir
      const databaseUrl = `sqlite+aiosqlite:///${join(dataDir, 'photos.db').replace(/\\/g, '/')}`;
      // Models directory packaged with app (optional ML features)
      const modelsDir = join(process.resourcesPath, 'models');

      backendProcess = spawn(backendExecutable, [], {
        cwd: backendPath,
        env: {
          ...process.env,
          PORT: BACKEND_PORT.toString(),
          DATA_DIR: dataDir,
          CACHE_DIR: cacheDir,
          DATABASE_URL: databaseUrl,
          MODELS_DIR: modelsDir,
        },
      });

      backendProcess.stdout?.on('data', (data) => {
        console.log('Backend stdout:', data.toString());
      });

      backendProcess.stderr?.on('data', (data) => {
        console.log('Backend stderr:', data.toString());
      });

      backendProcess.on('close', (code) => {
        console.log('Backend process exited with code:', code);
        backendProcess = null;
      });

      backendProcess.on('error', (error) => {
        console.error('Backend process error:', error);
        reject(error);
      });

      // Give backend time to start
      setTimeout(() => {
        if (backendProcess && !backendProcess.killed) {
          resolve();
        } else {
          reject(new Error('Backend failed to start'));
        }
      }, 3000);

    } catch (error) {
      console.error('Failed to start backend:', error);
      reject(error);
    }
  });
}

function stopBackend(): void {
  if (backendProcess && !backendProcess.killed) {
    console.log('Stopping backend process...');
    backendProcess.kill('SIGTERM');

    // Force kill after 5 seconds if still running
    setTimeout(() => {
      if (backendProcess && !backendProcess.killed) {
        console.log('Force killing backend process...');
        backendProcess.kill('SIGKILL');
      }
    }, 5000);
  }
}

function createWindow(): void {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    show: false, // Don't show until ready
    autoHideMenuBar: true,
    titleBarStyle: 'default',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: join(__dirname, 'preload.js'),
    },
    icon: join(__dirname, '../../assets/icon.png'), // App icon
  });

  // Load the app
  const startUrl = isDev
    ? 'http://localhost:5173'  // Vite dev server
    : `file://${join(__dirname, '../dist/index.html')}`;

  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();

    if (isDev) {
      mainWindow?.webContents.openDevTools();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Security: prevent new window creation
  mainWindow.webContents.on('new-window', (event, url) => {
    event.preventDefault();
    shell.openExternal(url);
  });

  // Handle navigation security
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);

    if (parsedUrl.origin !== new URL(startUrl).origin) {
      event.preventDefault();
    }
  });
}

// IPC handlers for OS integration
function setupIpcHandlers(): void {
  // Reveal file in folder
  ipcMain.handle('reveal-in-folder', async (_, filePath: string) => {
    try {
      shell.showItemInFolder(filePath);
    } catch (error) {
      console.error('Failed to reveal file:', error);
      throw error;
    }
  });

  // Open file externally
  ipcMain.handle('open-external', async (_, filePath: string) => {
    try {
      await shell.openPath(filePath);
    } catch (error) {
      console.error('Failed to open file:', error);
      throw error;
    }
  });

  // Get app version
  ipcMain.handle('get-version', () => {
    return app.getVersion();
  });

  // Get platform
  ipcMain.handle('get-platform', () => {
    return process.platform;
  });

  // Show error dialog
  ipcMain.handle('show-error-dialog', async (_, title: string, content: string) => {
    const result = await dialog.showMessageBox(mainWindow!, {
      type: 'error',
      title,
      message: title,
      detail: content,
      buttons: ['OK'],
    });
    return result;
  });

  // Show info dialog
  ipcMain.handle('show-info-dialog', async (_, title: string, content: string) => {
    const result = await dialog.showMessageBox(mainWindow!, {
      type: 'info',
      title,
      message: title,
      detail: content,
      buttons: ['OK'],
    });
    return result;
  });

  // Select folder dialog
  ipcMain.handle('select-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      properties: ['openDirectory'],
      title: 'Select Photo Folder',
    });
    return result;
  });

  // Select files dialog
  ipcMain.handle('select-files', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      properties: ['openFile', 'multiSelections'],
      title: 'Select Photos',
      filters: [
        { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'tiff', 'tif'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });
    return result;
  });
}

// App event handlers
app.whenReady().then(async () => {
  try {
    // Start backend first
    await startBackend();

    // Setup IPC handlers
    setupIpcHandlers();

    // Create main window
    createWindow();

    app.on('activate', () => {
      // On macOS, re-create window when dock icon is clicked
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  } catch (error) {
    console.error('Failed to start application:', error);

    // Show error dialog and quit
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start Photo Search application:\n\n${error}`
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  // Stop backend when all windows are closed
  stopBackend();

  // On macOS, apps typically stay active until explicitly quit
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Ensure backend is stopped before quitting
  stopBackend();
});

app.on('will-quit', (event) => {
  // Give backend time to shut down gracefully
  if (backendProcess && !backendProcess.killed) {
    event.preventDefault();
    stopBackend();

    setTimeout(() => {
      app.quit();
    }, 2000);
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (_, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});

// Handle certificate errors (for development)
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  if (isDev) {
    // In development, ignore certificate errors for localhost
    event.preventDefault();
    callback(true);
  } else {
    // In production, use default behavior
    callback(false);
  }
});

// Export for testing
export { createWindow, startBackend, stopBackend };
