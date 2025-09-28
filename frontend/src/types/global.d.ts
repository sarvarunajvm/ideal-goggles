import type { ElectronAPI } from '../../../electron/preload';

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    BACKEND_PORT?: number;
  }
}

export {};