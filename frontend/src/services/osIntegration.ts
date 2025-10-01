/**
 * OS integration service for file system operations
 * Handles platform-specific operations like revealing files in folders
 */

class OSIntegrationService {
  /**
   * Check if we're running in Electron
   */
  get isElectron(): boolean {
    return typeof window.electronAPI !== 'undefined'
  }

  /**
   * Get the current platform
   */
  async getPlatform(): Promise<string> {
    if (this.isElectron && window.electronAPI?.getPlatform) {
      return await window.electronAPI.getPlatform()
    }
    return navigator.platform
  }

  /**
   * Reveal a file in the system file manager
   * @param filePath - Absolute path to the file
   */
  async revealInFolder(filePath: string): Promise<void> {
    if (this.isElectron && window.electronAPI?.revealInFolder) {
      // Use Electron's shell.showItemInFolder
      await window.electronAPI.revealInFolder(filePath)
    } else {
      // Fallback for web browsers
      this.fallbackRevealInFolder(filePath)
    }
  }

  /**
   * Open a file with the default system application
   * @param filePath - Absolute path to the file
   */
  async openExternal(filePath: string): Promise<void> {
    if (this.isElectron && window.electronAPI?.openExternal) {
      // Use Electron's shell.openExternal
      await window.electronAPI.openExternal(filePath)
    } else {
      // Fallback for web browsers
      this.fallbackOpenExternal(filePath)
    }
  }

  /**
   * Copy file path to clipboard
   * @param filePath - File path to copy
   */
  async copyToClipboard(filePath: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(filePath)
    } catch (error) {
      // Fallback for older browsers
      this.fallbackCopyToClipboard(filePath)
    }
  }

  /**
   * Get application version
   */
  async getVersion(): Promise<string> {
    if (this.isElectron && window.electronAPI?.getVersion) {
      return await window.electronAPI.getVersion()
    }
    return '1.0.0-web'
  }

  /**
   * Fallback method for revealing files (web environment)
   */
  private fallbackRevealInFolder(filePath: string): void {
    // Show notification that this feature requires desktop app
    this.showDesktopFeatureNotification('File reveal')

    // As a fallback, copy the folder path to clipboard
    const folderPath = filePath.substring(0, filePath.lastIndexOf('/'))
    this.copyToClipboard(folderPath)
  }

  /**
   * Fallback method for opening files (web environment)
   */
  private fallbackOpenExternal(filePath: string): void {
    // Show notification that this feature requires desktop app
    this.showDesktopFeatureNotification('File opening')

    // As a fallback, copy the file path to clipboard
    this.copyToClipboard(filePath)
  }

  /**
   * Fallback method for copying to clipboard
   */
  private fallbackCopyToClipboard(text: string): void {
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()

    try {
      document.execCommand('copy')
    } catch (error) {
      // Silent failure for clipboard fallback
    }

    document.body.removeChild(textArea)
  }

  /**
   * Show notification about desktop-only features
   */
  private showDesktopFeatureNotification(feature: string): void {
    // Create a temporary notification
    const notification = document.createElement('div')
    notification.className =
      'fixed top-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded z-50 max-w-sm'
    notification.innerHTML = `
      <div class="flex">
        <div class="flex-shrink-0">
          <span class="text-yellow-500">⚠️</span>
        </div>
        <div class="ml-3">
          <p class="text-sm">
            <strong>${feature}</strong> requires the desktop application.
            File path copied to clipboard instead.
          </p>
        </div>
        <div class="ml-auto pl-3">
          <button class="text-yellow-500 hover:text-yellow-600" onclick="this.parentElement.parentElement.parentElement.remove()">
            ✕
          </button>
        </div>
      </div>
    `

    document.body.appendChild(notification)

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove()
      }
    }, 5000)
  }

  /**
   * Check if a specific OS integration feature is available
   */
  isFeatureAvailable(
    feature: 'revealInFolder' | 'openExternal' | 'clipboard'
  ): boolean {
    switch (feature) {
      case 'revealInFolder':
        return (
          this.isElectron &&
          typeof window.electronAPI?.revealInFolder === 'function'
        )
      case 'openExternal':
        return (
          this.isElectron &&
          typeof window.electronAPI?.openExternal === 'function'
        )
      case 'clipboard':
        return typeof navigator.clipboard?.writeText === 'function'
      default:
        return false
    }
  }

  /**
   * Show file properties/info (if supported)
   */
  async showFileProperties(): Promise<void> {
    // This would be implemented with additional Electron APIs
    throw new Error('File properties not yet implemented')
  }

  /**
   * Create a desktop notification
   */
  async showNotification(
    title: string,
    body: string,
    icon?: string
  ): Promise<void> {
    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification(title, { body, icon })
      } else if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission()
        if (permission === 'granted') {
          new Notification(title, { body, icon })
        }
      }
    }
  }
}

export const osIntegration = new OSIntegrationService()
export default osIntegration
