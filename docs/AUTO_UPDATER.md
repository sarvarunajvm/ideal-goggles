# Auto-Updater Documentation

## Overview

Ideal Goggles includes an automatic update system that keeps the application up-to-date with the latest features and security patches. The auto-updater runs in the background and notifies users when new versions are available.

## Features

- **Automatic Update Detection**: Checks for updates on startup (after a 5-second delay)
- **Manual Update Check**: Users can manually check for updates from the settings
- **Update Channels**: Support for stable and beta release channels
- **Release Notes**: Display what's new in each update
- **Download Progress**: Show download progress to users
- **Smart Installation**: Updates are installed when the app quits
- **GitHub Integration**: Updates are distributed via GitHub Releases

## How It Works

### Update Flow

1. **Check for Updates**: On startup or manual trigger
2. **Update Available**: Dialog shows new version and release notes
3. **Download**: User chooses to download now or later
4. **Progress Tracking**: Download progress is tracked and displayed
5. **Installation**: Update installs automatically on app quit or immediate restart

### Update Channels

#### Stable Channel (Default)
- Only receives stable releases (e.g., `v1.0.25`)
- Recommended for most users
- Most tested and reliable

#### Beta Channel
- Receives pre-release versions (e.g., `v1.0.25-beta.1`)
- Early access to new features
- May contain bugs

## Implementation

### Backend (Electron Main Process)

The auto-updater is implemented in `frontend/electron/updater.ts`:

```typescript
import { initializeAutoUpdater, checkForUpdatesManually, setUpdateChannel, getUpdateChannel } from './updater';

// Initialize on app startup
initializeAutoUpdater();

// Set update channel
setUpdateChannel('beta'); // or 'stable'

// Get current channel
const channel = getUpdateChannel();

// Manual check
checkForUpdatesManually();
```

### Frontend Integration

The preload script exposes auto-updater APIs to the renderer:

```typescript
// Check for updates manually
window.electronAPI.checkForUpdates();

// Get current update channel
const channel = await window.electronAPI.getUpdateChannel();

// Set update channel
await window.electronAPI.setUpdateChannel('beta');

// Listen for update events
window.electronAPI.onUpdateAvailable((info) => {
  console.log('Update available:', info.version);
  console.log('Release notes:', info.releaseNotes);
});

window.electronAPI.onUpdateDownloadProgress((progress) => {
  console.log(`Download progress: ${progress.percent}%`);
});

window.electronAPI.onUpdateDownloaded((info) => {
  console.log('Update downloaded:', info.version);
});
```

## GitHub Release Configuration

### Package.json

The `build.publish` configuration in `package.json`:

```json
{
  "build": {
    "publish": [
      {
        "provider": "github",
        "owner": "ideal-goggles",
        "repo": "ideal-goggles",
        "releaseType": "release",
        "publishAutoUpdate": true
      }
    ]
  }
}
```

### Release Workflow

The `.github/workflows/release.yml` workflow:

1. Builds for all platforms (macOS, Windows, Linux)
2. Generates update metadata files (`latest-mac.yml`, `latest.yml`)
3. Uploads all artifacts to GitHub Release
4. Automatically detects pre-release versions (beta, alpha, rc)

### Creating a Release

#### Stable Release
```bash
# Create and push a version tag
pnpm run tag:patch  # or tag:minor, tag:major
git push origin --tags
```

#### Beta Release
```bash
# Create a beta version tag
git tag v1.0.26-beta.1
git push origin v1.0.26-beta.1
```

The release workflow will:
- Build the app for all platforms
- Create a GitHub Release
- Upload installers and update metadata
- Set `prerelease: true` for beta versions

## Update Metadata Files

The auto-updater uses YAML metadata files uploaded with each release:

### macOS: `latest-mac.yml`
```yaml
version: 1.0.25
files:
  - url: ideal-goggles-1.0.25-arm64.dmg
    sha512: [checksum]
    size: [bytes]
path: ideal-goggles-1.0.25-arm64.dmg
sha512: [checksum]
releaseDate: '2025-01-15T10:00:00.000Z'
```

### Windows: `latest.yml`
```yaml
version: 1.0.25
files:
  - url: ideal-goggles-Setup-1.0.25.exe
    sha512: [checksum]
    size: [bytes]
path: ideal-goggles-Setup-1.0.25.exe
sha512: [checksum]
releaseDate: '2025-01-15T10:00:00.000Z'
```

## Security

### Code Signing

**macOS**: Currently disabled for development
- `hardenedRuntime: false`
- `gatekeeperAssess: false`
- `identity: null`

**Windows**: Currently disabled for development
- `verifyUpdateCodeSignature: false`
- `signAndEditExecutable: false`

**Production Recommendation**: Enable code signing for production releases:

1. **macOS**:
   - Obtain Apple Developer ID certificate
   - Set `identity` to your certificate name
   - Enable `hardenedRuntime: true`
   - Enable `gatekeeperAssess: true`

2. **Windows**:
   - Obtain code signing certificate
   - Set `certificateFile` and `certificatePassword`
   - Enable `verifyUpdateCodeSignature: true`

### Update Verification

The auto-updater verifies updates using:
- SHA-512 checksums for all files
- HTTPS-only downloads from GitHub
- Signature verification (when code signing is enabled)

## Testing

### Local Testing

1. **Create a test release**:
   ```bash
   # Build the app
   pnpm run dist:mac  # or dist:win

   # Create a GitHub release manually
   # Upload the built installer and metadata files
   ```

2. **Test with different versions**:
   - Temporarily change version in `package.json` to a lower version
   - Build and run the app
   - It should detect the newer version on GitHub

3. **Test update channels**:
   ```typescript
   // In your app
   await window.electronAPI.setUpdateChannel('beta');
   await window.electronAPI.checkForUpdates();
   ```

### Mock Testing

For development, you can skip the auto-updater:
- It's automatically disabled in development mode
- Manual check shows: "Auto-update is disabled in development mode"

## Troubleshooting

### Updates Not Detected

1. **Check GitHub Release**:
   - Ensure the release is published (not draft)
   - Verify update metadata files are uploaded
   - Check release version is higher than current

2. **Check Configuration**:
   - Verify `build.publish` in package.json
   - Ensure `publishAutoUpdate: true`
   - Check repository owner/repo names

3. **Check Logs**:
   - Auto-updater logs to electron-log
   - Check console for "[Updater]" messages

### Download Fails

1. **Network Issues**:
   - Check internet connection
   - Verify GitHub is accessible
   - Check firewall settings

2. **File Permissions**:
   - Ensure app has write permissions
   - Check available disk space

### Update Won't Install

1. **Verify Download**:
   - Ensure download completed (100%)
   - Check file integrity (SHA-512)

2. **App Quit**:
   - Update installs on quit
   - Use "Restart Now" for immediate installation

## Best Practices

1. **Versioning**:
   - Follow semantic versioning (MAJOR.MINOR.PATCH)
   - Use `-beta`, `-alpha`, `-rc` for pre-releases
   - Always increment version numbers

2. **Release Notes**:
   - Use GitHub's automatic release notes generation
   - Or write clear, concise release notes
   - Highlight breaking changes

3. **Testing**:
   - Test beta versions with beta channel users first
   - Verify auto-update works before stable release
   - Test on all platforms (macOS, Windows, Linux)

4. **Communication**:
   - Notify users of major updates
   - Provide migration guides for breaking changes
   - Keep update process transparent

## API Reference

### Main Process (Electron)

```typescript
// Initialize auto-updater
initializeAutoUpdater(): void

// Check for updates manually
checkForUpdatesManually(): void

// Set update channel
setUpdateChannel(channel: 'stable' | 'beta'): void

// Get current channel
getUpdateChannel(): 'stable' | 'beta'
```

### Renderer Process (Frontend)

```typescript
// Check for updates
window.electronAPI.checkForUpdates(): Promise<void>

// Update channel management
window.electronAPI.getUpdateChannel(): Promise<'stable' | 'beta'>
window.electronAPI.setUpdateChannel(channel: 'stable' | 'beta'): Promise<'stable' | 'beta'>

// Event listeners
window.electronAPI.onUpdateAvailable(callback: (info: UpdateInfo) => void): void
window.electronAPI.onUpdateDownloadProgress(callback: (progress: ProgressInfo) => void): void
window.electronAPI.onUpdateDownloaded(callback: (info: UpdateInfo) => void): void
```

### Type Definitions

```typescript
interface UpdateInfo {
  version: string;
  releaseNotes?: string;
  releaseName?: string;
  releaseDate?: string;
}

interface ProgressInfo {
  percent: number;
  transferred: number;
  total: number;
  bytesPerSecond: number;
}
```

## Resources

- [electron-updater Documentation](https://www.electron.build/auto-update)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)
- [Code Signing Guide](https://www.electron.build/code-signing)
