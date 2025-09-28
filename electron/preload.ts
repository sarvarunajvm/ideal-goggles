import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
const electronAPI = {
  // File system operations
  revealInFolder: (path: string) => ipcRenderer.invoke('reveal-in-folder', path),
  openExternal: (path: string) => ipcRenderer.invoke('open-external', path),

  // System information
  getVersion: () => ipcRenderer.invoke('get-version'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),
  getBackendLogPath: () => ipcRenderer.invoke('get-backend-log-path'),
  getBackendPort: () => ipcRenderer.invoke('get-backend-port'),
  readBackendLog: () => ipcRenderer.invoke('read-backend-log'),

  // Dialog operations
  showErrorDialog: (title: string, content: string) =>
    ipcRenderer.invoke('show-error-dialog', title, content),
  showInfoDialog: (title: string, content: string) =>
    ipcRenderer.invoke('show-info-dialog', title, content),

  // File/folder selection
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  selectFiles: () => ipcRenderer.invoke('select-files'),

  // Window operations
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  isMaximized: () => ipcRenderer.invoke('is-maximized'),

  // Listen to window events
  onWindowStateChange: (callback: (isMaximized: boolean) => void) => {
    ipcRenderer.on('window-state-changed', (_, isMaximized) => callback(isMaximized));
  },

  // Remove listeners
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  },
};

// Security: Only expose specific API methods to the renderer process
contextBridge.exposeInMainWorld('electronAPI', electronAPI);
// Backend always runs on port 5555
contextBridge.exposeInMainWorld('BACKEND_PORT', 5555);

// Backend port is declared in frontend/src/types/global.d.ts

// Type declaration for TypeScript
export type ElectronAPI = typeof electronAPI;
