declare global {
  interface ElectronAPI {
    // File system operations
    revealInFolder: (path: string) => Promise<void>;
    openExternal: (path: string) => Promise<void>;

    // System information
    getVersion: () => Promise<string>;
    getPlatform: () => Promise<string>;
    getBackendLogPath: () => Promise<string>;
    getBackendPort: () => Promise<number>;
    readBackendLog: () => Promise<string>;

    // Dialog operations
    showErrorDialog: (title: string, content: string) => Promise<void>;
    showInfoDialog: (title: string, content: string) => Promise<void>;

    // File/folder selection
    selectFolder: () => Promise<string>;
    selectFiles: () => Promise<string[]>;

    // Window operations
    minimizeWindow: () => Promise<void>;
    maximizeWindow: () => Promise<void>;
    closeWindow: () => Promise<void>;
    isMaximized: () => Promise<boolean>;

    // Event listeners
    onWindowStateChange: (callback: (isMaximized: boolean) => void) => void;
    removeAllListeners: (channel: string) => void;
  }

  interface Window {
    electronAPI?: ElectronAPI;
    BACKEND_PORT?: number;
  }
}

export {};