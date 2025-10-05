import { app, BrowserWindow, shell, ipcMain, dialog } from 'electron';
import { join } from 'path';
import { createWriteStream, readFileSync } from 'fs';
import net from 'net';
import { spawn, ChildProcess } from 'child_process';
import { existsSync, mkdirSync } from 'fs';
import { initializeAutoUpdater, checkForUpdatesManually } from './updater';

// Keep a global reference of the window object
let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;

const isDev = process.env.NODE_ENV === 'development';
let BACKEND_PORT = 5555; // resolved at runtime in production/dev

// Enforce single app instance
const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  console.log('[App] Another instance detected; quitting.');
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

// Backend management
async function startBackend(): Promise<void> {
  console.log('[Backend] Starting backend initialization...');
  const checkPortInUse = (port: number, host = '127.0.0.1'): Promise<boolean> => {
    return new Promise((resolve) => {
      const socket = net.connect({ port, host });
      socket.once('connect', () => {
        socket.end();
        resolve(true); // Port is in use
      });
      socket.once('error', () => {
        socket.destroy();
        resolve(false); // Port is free
      });
    });
  };

  const waitForPort = (port: number, host = '127.0.0.1', retries = 60, delayMs = 500): Promise<void> => {
    console.log(`[Backend] Waiting for port ${host}:${port} to become available...`);
    return new Promise((resolve, reject) => {
      const tryOnce = (attempt: number) => {
        if (attempt > 0 && attempt % 5 === 0) {
          console.log(`[Backend] Still waiting for port ${host}:${port}... (attempt ${attempt}/${retries})`);
        }
        const socket = net.connect({ port, host });
        socket.once('connect', () => {
          console.log(`[Backend] Port ${host}:${port} is now available!`);
          socket.end();
          resolve();
        });
        socket.once('error', () => {
          socket.destroy();
          if (attempt >= retries) {
            console.error(`[Backend] Failed: Port ${host}:${port} not responding after ${retries} attempts`);
            reject(new Error(`Backend port ${host}:${port} not responding`));
          } else {
            setTimeout(() => tryOnce(attempt + 1), delayMs);
          }
        });
      };
      tryOnce(0);
    });
  };

  return new Promise(async (resolve, reject) => {
    try {
      console.log('[Backend] isDev:', isDev);
      console.log('[Backend] NODE_ENV:', process.env.NODE_ENV);

      // Always use port 5555
      BACKEND_PORT = 5555;
      console.log('[Backend] Using fixed port:', BACKEND_PORT);

      // Check if port is already in use
      const portInUse = await checkPortInUse(BACKEND_PORT);

      if (isDev) {
        console.log('[Backend] Development mode');
        if (portInUse) {
          console.log('[Backend] Port 5555 already in use (likely dev server running), skipping backend start');
          resolve();
          return;
        }
        console.log('[Backend] Port 5555 is free, but in dev mode we expect external backend');
        resolve();
        return;
      }

      console.log('[Backend] Production mode');

      // In production, check if backend is already running
      if (portInUse) {
        console.log('[Backend] Port 5555 already in use, probing backend health');
        try {
          const http = await import('http');
          await new Promise<void>((res, rej) => {
            const req = http.get({ host: '127.0.0.1', port: BACKEND_PORT, path: '/health', timeout: 2000 }, (resp) => {
              if (resp.statusCode && resp.statusCode >= 200 && resp.statusCode < 500) {
                console.log('[Backend] Existing service responded on /health, proceeding');
                res();
              } else {
                rej(new Error('Unexpected status from /health: ' + resp.statusCode));
              }
            });
            req.on('error', rej);
            req.on('timeout', () => {
              req.destroy(new Error('Health probe timeout'));
            });
          });
          resolve();
          return;
        } catch (e) {
          console.warn('[Backend] Port is in use but /health probe failed. Will attempt to start packaged backend anyway. Error:', (e as any)?.message || e);
        }
      }

      console.log('[Backend] Port 5555 is free, starting packaged backend...');
      console.log('[Backend] resourcesPath:', process.resourcesPath);

      const backendPath = join(process.resourcesPath, 'backend');
      const binaryName = process.platform === 'win32' ? 'ideal-goggles-backend.exe' : 'ideal-goggles-backend';
      const backendExecutable = join(backendPath, binaryName);

      console.log('[Backend] Backend path:', backendPath);
      console.log('[Backend] Binary name:', binaryName);
      console.log('[Backend] Backend executable:', backendExecutable);
      console.log('[Backend] Executable exists:', existsSync(backendExecutable));

      if (!existsSync(backendExecutable)) {
        console.error('[Backend] Backend executable not found:', { backendExecutable });
        console.error('[Backend] Directory contents:', existsSync(backendPath) ? require('fs').readdirSync(backendPath) : 'Directory does not exist');
        reject(new Error('Backend executable not found'));
        return;
      }

      // Compute writable data and cache directories under userData
      const userDataDir = app.getPath('userData');
      const dataDir = join(userDataDir, 'data');
      const cacheDir = join(userDataDir, 'cache');

      console.log('[Backend] User data dir:', userDataDir);
      console.log('[Backend] Data dir:', dataDir);
      console.log('[Backend] Cache dir:', cacheDir);

      // Ensure directories exist
      mkdirSync(dataDir, { recursive: true });
      mkdirSync(cacheDir, { recursive: true });

      // Build database URL pointing to user data dir
      const databaseUrl = `sqlite+aiosqlite:///${join(dataDir, 'photos.db').replace(/\\/g, '/')}`;
      // Models directory packaged with app (optional ML features)
      const modelsDir = join(process.resourcesPath, 'models');

      console.log('[Backend] Database URL:', databaseUrl);
      console.log('[Backend] Models dir:', modelsDir);

      // Prepare logging
      const logsDir = join(userDataDir, 'logs');
      mkdirSync(logsDir, { recursive: true });
      const logFile = join(logsDir, 'backend.log');
      const logStream = createWriteStream(logFile, { flags: 'a' });

      console.log('[Backend] Log file:', logFile);

      const backendEnv = {
        ...process.env,
        PORT: '5555', // Always use port 5555
        DATA_DIR: dataDir,
        CACHE_DIR: cacheDir,
        THUMBNAILS_DIR: join(cacheDir, 'thumbs'),
        DATABASE_URL: databaseUrl,
        MODELS_DIR: modelsDir,
      };

      console.log('[Backend] Spawning backend process with env:', {
        PORT: backendEnv.PORT,
        DATA_DIR: backendEnv.DATA_DIR,
        CACHE_DIR: backendEnv.CACHE_DIR,
        THUMBNAILS_DIR: backendEnv.THUMBNAILS_DIR,
        DATABASE_URL: backendEnv.DATABASE_URL,
        MODELS_DIR: backendEnv.MODELS_DIR,
      });

      backendProcess = spawn(backendExecutable, [], {
        cwd: backendPath,
        env: backendEnv,
      });

      console.log('[Backend] Backend process spawned with PID:', backendProcess.pid);

      backendProcess.stdout?.on('data', (data) => {
        const msg = data.toString();
        console.log('[Backend STDOUT]:', msg);
        logStream.write(`[STDOUT] ${msg}`);
      });

      backendProcess.stderr?.on('data', (data) => {
        const msg = data.toString();
        console.error('[Backend STDERR]:', msg);
        logStream.write(`[STDERR] ${msg}`);
      });

      backendProcess.on('close', (code) => {
        console.log('[Backend] Process exited with code:', code);
        backendProcess = null;
      });

      backendProcess.on('error', (error) => {
        console.error('[Backend] Process spawn error:', error);
        console.error('[Backend] Error details:', {
          message: error.message,
          code: (error as any).code,
          errno: (error as any).errno,
          syscall: (error as any).syscall,
          path: (error as any).path
        });
        reject(error);
      });

      // Wait until the backend port is responsive (with one retry at higher budget)
      console.log('[Backend] Starting port wait...');
      try {
        await waitForPort(BACKEND_PORT);
        console.log('[Backend] Successfully connected to backend!');
        resolve();
        return;
      } catch (err1) {
        console.warn('[Backend] First port wait failed, retrying with extended attempts...', err1);
        try {
          await waitForPort(BACKEND_PORT, '127.0.0.1', 120, 500);
          console.log('[Backend] Connected after retry.');
          resolve();
          return;
        } catch (err2) {
          console.error('[Backend] Failed to connect to backend after retries:', err2);
          reject(err2);
          return;
        }
      }

    } catch (error) {
      console.error('[Backend] Failed to start backend:', error);
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
      preload: join(__dirname, 'preload.js'),
    },
    icon: join(__dirname, '../../../build-resources/icon.png'), // App icon
  });

  // Load the app
  const startUrl = isDev
    ? 'http://localhost:3333'  // Vite dev server (configured in vite.config.ts)
    : `file://${join(__dirname, '../../dist/index.html')}#/`;

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

  // Security: new windows are denied via setWindowOpenHandler above

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

  // Check for updates manually
  ipcMain.handle('check-for-updates', () => {
    checkForUpdatesManually();
  });

  // Get backend log file path
  ipcMain.handle('get-backend-log-path', () => {
    const userDataDir = app.getPath('userData');
    const logsDir = join(userDataDir, 'logs');
    const logFile = join(logsDir, 'backend.log');
    return logFile;
  });

  // Get current backend port selected by main
  ipcMain.handle('get-backend-port', () => {
    return BACKEND_PORT;
  });

  // Read backend log contents (last N bytes)
  ipcMain.handle('read-backend-log', () => {
    try {
      const userDataDir = app.getPath('userData');
      const logsDir = join(userDataDir, 'logs');
      const logFile = join(logsDir, 'backend.log');
      const data = readFileSync(logFile, 'utf-8');
      return data;
    } catch (e) {
      return '';
    }
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
  console.log('[App] Application ready, starting initialization...');
  console.log('[App] Platform:', process.platform);
  console.log('[App] Electron version:', process.versions.electron);
  console.log('[App] Node version:', process.versions.node);

  try {
    // Start backend first
    console.log('[App] Starting backend...');
    await startBackend();
    console.log('[App] Backend started successfully!');

    // Setup IPC handlers
    console.log('[App] Setting up IPC handlers...');
    setupIpcHandlers();

    // Initialize auto-updater
    console.log('[App] Initializing auto-updater...');
    initializeAutoUpdater();

    // Expose the selected port to renderer via global shared object BEFORE creating the window,
    // so preload can read it and expose window.BACKEND_PORT properly.
    (global as any).BACKEND_PORT = BACKEND_PORT;
    console.log('[App] Backend port exposed to global:', BACKEND_PORT);

    // Create main window
    console.log('[App] Creating main window...');
    createWindow();
    console.log('[App] Main window created!');

    app.on('activate', () => {
      // On macOS, re-create window when dock icon is clicked
      if (BrowserWindow.getAllWindows().length === 0) {
        console.log('[App] Recreating window on activate...');
        createWindow();
      }
    });
  } catch (error) {
    console.error('[App] Failed to start application:', error);

    // Show error dialog and quit
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start Ideal Goggles application:\n\n${error}`
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

// Security: Prevent new window creation for any WebContents
app.on('web-contents-created', (_, contents) => {
  contents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
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
