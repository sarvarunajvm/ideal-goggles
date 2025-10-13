# Installer Customization Guide

Complete guide to customizing installers for Ideal Goggles on Windows, macOS, and Linux.

## Overview

The installer configurations are defined in `package.json` under the `build` section. Custom scripts and assets are located in `build-resources/`.

## Table of Contents

1. [Windows (NSIS) Installer](#windows-nsis-installer)
2. [macOS (DMG) Installer](#macos-dmg-installer)
3. [Linux Installers](#linux-installers)
4. [Icon Generation](#icon-generation)
5. [Custom Scripts](#custom-scripts)
6. [Testing](#testing)

---

## Windows (NSIS) Installer

### Configuration

The NSIS installer is configured in `package.json`:

```json
{
  "nsis": {
    "oneClick": false,
    "perMachine": false,
    "allowToChangeInstallationDirectory": true,
    "allowElevation": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true,
    "shortcutName": "Ideal Goggles",
    "uninstallDisplayName": "Ideal Goggles",
    "installerIcon": "build-resources/icon.ico",
    "uninstallerIcon": "build-resources/icon.ico",
    "installerHeaderIcon": "build-resources/icon.ico",
    "installerSidebar": "build-resources/installer-sidebar.bmp",
    "uninstallerSidebar": "build-resources/installer-sidebar.bmp",
    "license": "LICENSE",
    "deleteAppDataOnUninstall": false,
    "runAfterFinish": true,
    "menuCategory": true,
    "include": "build-resources/installer.nsh"
  }
}
```

### Features

- **Two-click installer** (not one-click for user control)
- **Custom installation directory** selection
- **Desktop and Start Menu shortcuts** created automatically
- **Custom sidebar image** (164x314 pixels)
- **License agreement** display
- **Run after finish** option
- **Data preservation** on uninstall (asks user)

### Custom Script

The custom NSIS script (`build-resources/installer.nsh`) includes:

1. **Custom Welcome Page**: Branded welcome message
2. **Installation Checks**: Verifies app isn't running
3. **Additional Shortcuts**: Desktop shortcut creation
4. **Uninstall Prompts**: Ask to keep user data
5. **Custom Messages**: Branded text throughout

### Required Assets

1. **icon.ico** (Windows icon format)
   - Multiple sizes: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16
   - Generated from: `build-resources/icon.png`

2. **installer-sidebar.bmp** (NSIS sidebar)
   - Size: 164 pixels wide × 314 pixels tall
   - Format: 24-bit BMP
   - Background: Dark (#1a1a1a recommended)

### Customization Options

#### Change Installer Text

Edit `build-resources/installer.nsh`:

```nsis
!define MUI_WELCOMEPAGE_TITLE "Your Custom Title"
!define MUI_WELCOMEPAGE_TEXT "Your custom welcome message..."
```

#### Add File Associations

In `installer.nsh`:

```nsis
!macro customInstall
  WriteRegStr HKCR ".jpg" "" "IdealGoggles.Image"
  WriteRegStr HKCR "IdealGoggles.Image\DefaultIcon" "" "$INSTDIR\${APP_EXECUTABLE_FILENAME},0"
!macroend
```

#### Change Shortcuts

Modify in `installer.nsh`:

```nsis
CreateShortCut "$DESKTOP\Ideal Goggles.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}"
CreateShortCut "$SMPROGRAMS\Photography\Ideal Goggles.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}"
```

---

## macOS (DMG) Installer

### Configuration

The DMG installer is configured in `package.json`:

```json
{
  "dmg": {
    "title": "Ideal Goggles ${version}",
    "iconSize": 80,
    "iconTextSize": 12,
    "format": "UDZO",
    "background": "build-resources/dmg-background.png",
    "backgroundColor": "#1a1a1a",
    "window": {
      "width": 600,
      "height": 400
    },
    "contents": [
      {
        "x": 150,
        "y": 200,
        "type": "file"
      },
      {
        "x": 450,
        "y": 200,
        "type": "link",
        "path": "/Applications"
      }
    ],
    "internetEnabled": false,
    "sign": false
  },
  "mac": {
    "icon": "build-resources/icon.icns",
    "darkModeSupport": true,
    "category": "public.app-category.photography",
    "minimumSystemVersion": "10.15",
    "type": "distribution"
  }
}
```

### Features

- **Custom background image** (600x400 pixels)
- **Dark mode support**
- **Drag-to-Applications** UI with visual guide
- **Compressed format** (UDZO) for smaller file size
- **Version in title** for easy identification

### Required Assets

1. **icon.icns** (macOS icon format)
   - Sizes: 16x16, 32x32, 64x64, 128x128, 256x256, 512x512, 1024x1024
   - Retina variants included
   - Generated from: `build-resources/icon.png`

2. **dmg-background.png** (DMG background)
   - Size: 600 pixels wide × 400 pixels tall
   - Format: PNG
   - Should include visual guide for drag-to-install

### Customization Options

#### Change Icon Positions

Edit positions in `package.json`:

```json
{
  "contents": [
    {
      "x": 150,  // App icon X position
      "y": 200,  // App icon Y position
      "type": "file"
    },
    {
      "x": 450,  // Applications folder X position
      "y": 200,  // Applications folder Y position
      "type": "link",
      "path": "/Applications"
    }
  ]
}
```

#### Create Custom Background

Design a 600×400 background with:
1. App branding/logo
2. Visual arrow or instructions
3. Circles/boxes showing where to drag icons
4. Dark background (#1a1a1a) for consistency

Example with ImageMagick:
```bash
convert -size 600x400 xc:"#1a1a1a" \
  -font Arial -pointsize 16 -fill white \
  -gravity north -annotate +0+30 "Ideal Goggles" \
  -pointsize 12 -gravity center \
  -annotate +0+50 "Drag to Applications folder" \
  dmg-background.png
```

#### Change Window Size

```json
{
  "window": {
    "width": 800,   // Wider window
    "height": 500   // Taller window
  }
}
```

---

## Linux Installers

### AppImage Configuration

```json
{
  "appImage": {
    "artifactName": "${productName}-${version}-${arch}.${ext}"
  },
  "linux": {
    "target": ["AppImage", "deb"],
    "category": "Graphics",
    "executableName": "ideal-goggles"
  }
}
```

### Debian Package Configuration

```json
{
  "deb": {
    "packageCategory": "graphics",
    "synopsis": "Ideal Goggles desktop application",
    "description": "Privacy-focused local photo search and organization with AI capabilities.",
    "maintainer": "Ideal Goggles Team",
    "depends": ["libgtk-3-0", "libnotify4"]
  }
}
```

---

## Icon Generation

### Automated Script

Use the provided script to generate all icon formats:

```bash
bash scripts/generate-installer-assets.sh
```

This generates:
- ✅ `icon.icns` (macOS)
- ✅ `icon.ico` (Windows)
- ✅ `installer-sidebar.bmp` (NSIS)
- ✅ `dmg-background.png` (DMG)

### Requirements

**ImageMagick** (for conversion):
```bash
brew install imagemagick
```

**iconutil** (macOS only, for .icns):
- Pre-installed on macOS

### Manual Icon Generation

#### Windows .ico

```bash
magick icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

#### macOS .icns

```bash
# Create iconset directory
mkdir icon.iconset

# Generate all sizes
magick icon.png -resize 16x16 icon.iconset/icon_16x16.png
magick icon.png -resize 32x32 icon.iconset/icon_16x16@2x.png
magick icon.png -resize 32x32 icon.iconset/icon_32x32.png
magick icon.png -resize 64x64 icon.iconset/icon_32x32@2x.png
magick icon.png -resize 128x128 icon.iconset/icon_128x128.png
magick icon.png -resize 256x256 icon.iconset/icon_128x128@2x.png
magick icon.png -resize 256x256 icon.iconset/icon_256x256.png
magick icon.png -resize 512x512 icon.iconset/icon_256x256@2x.png
magick icon.png -resize 512x512 icon.iconset/icon_512x512.png
magick icon.png -resize 1024x1024 icon.iconset/icon_512x512@2x.png

# Convert to .icns
iconutil -c icns icon.iconset -o icon.icns
```

#### NSIS Sidebar (164×314)

```bash
magick icon.png -resize 164x164 \
  -background "#1a1a1a" -gravity center \
  -extent 164x314 installer-sidebar.bmp
```

---

## Custom Scripts

### NSIS Macros Available

The `installer.nsh` file supports these macros:

1. **`customHeader`** - Customize installer UI
2. **`customInstall`** - Add installation steps
3. **`customUnInstall`** - Add uninstallation steps
4. **`customInit`** - Pre-installation checks
5. **`customInstallMode`** - Installation mode setup

### Example: Add Registry Entries

```nsis
!macro customInstall
  WriteRegStr HKCU "Software\IdealGoggles" "InstallPath" "$INSTDIR"
  WriteRegStr HKCU "Software\IdealGoggles" "Version" "${VERSION}"
!macroend

!macro customUnInstall
  DeleteRegKey HKCU "Software\IdealGoggles"
!macroend
```

### Example: Check Prerequisites

```nsis
!macro customInit
  ; Check for .NET Framework
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" "Version"
  StrCmp $0 "" 0 HasDotNet
    MessageBox MB_OK "This application requires .NET Framework 4.8"
    Quit
  HasDotNet:
!macroend
```

---

## Testing

### Build Installers

```bash
# macOS
pnpm run dist:mac

# Windows
pnpm run dist:win

# All platforms
pnpm run dist:all
```

### Test Checklist

#### Windows (NSIS)
- [ ] Installer displays custom sidebar
- [ ] Welcome page shows custom text
- [ ] License agreement displays correctly
- [ ] Can choose installation directory
- [ ] Desktop shortcut created
- [ ] Start menu shortcut created
- [ ] App runs after finish (if selected)
- [ ] Uninstaller asks about keeping data
- [ ] Icons display correctly

#### macOS (DMG)
- [ ] DMG mounts with custom background
- [ ] Window size is correct (600×400)
- [ ] App icon positioned correctly (150, 200)
- [ ] Applications link positioned correctly (450, 200)
- [ ] Version shown in DMG title
- [ ] Drag-to-install works smoothly
- [ ] App icon displays correctly
- [ ] Dark mode background looks good

#### Linux
- [ ] AppImage executes directly
- [ ] Debian package installs correctly
- [ ] Menu entry created
- [ ] Icon displays in app launcher

### Test in Virtual Machines

For thorough testing:

1. **Windows**: Test on Windows 10 and 11
   - Test both 32-bit and 64-bit installers
   - Test with UAC enabled/disabled
   - Test portable version

2. **macOS**: Test on macOS 10.15+
   - Test on Intel and Apple Silicon
   - Test with Gatekeeper enabled
   - Test drag-to-install flow

3. **Linux**: Test on Ubuntu/Debian
   - Test AppImage on different distros
   - Test .deb installation

---

## Troubleshooting

### Common Issues

#### Windows: Installer sidebar not showing
- Ensure `installer-sidebar.bmp` is exactly 164×314 pixels
- Verify it's a 24-bit BMP file
- Check file is in `build-resources/` directory

#### macOS: Background not displaying
- Ensure `dmg-background.png` is exactly 600×400 pixels
- Verify file path in package.json is correct
- Check PNG is not corrupted

#### Icons not generating
- Install ImageMagick: `brew install imagemagick`
- Ensure source `icon.png` is at least 512×512 pixels
- Run: `bash scripts/generate-installer-assets.sh`

#### NSIS script errors
- Check syntax in `installer.nsh`
- Ensure all macros are properly closed
- Review build logs for specific errors

### Build Output

Installers are created in `dist-electron/`:

```
dist-electron/
├── ideal-goggles-Setup-1.0.25.exe         # Windows NSIS
├── ideal-goggles-1.0.25-x64.exe           # Windows portable
├── ideal-goggles-1.0.25-arm64.dmg         # macOS DMG
├── ideal-goggles-1.0.25-x64.AppImage      # Linux AppImage
└── ideal-goggles-1.0.25-amd64.deb         # Debian package
```

---

## Resources

### Documentation
- [electron-builder](https://www.electron.build/)
- [NSIS Documentation](https://nsis.sourceforge.io/Docs/)
- [DMG Builder](https://github.com/electron-userland/electron-builder/tree/master/packages/dmg-builder)

### Tools
- [ImageMagick](https://imagemagick.org/) - Image conversion
- [GIMP](https://www.gimp.org/) - Image editing
- [Inkscape](https://inkscape.org/) - Vector graphics

### Icon Resources
- [Icon8](https://icons8.com/) - Free/paid icons
- [Flaticon](https://www.flaticon.com/) - Icon library
- [IconFinder](https://www.iconfinder.com/) - Icon search

---

## Quick Reference

### File Specifications

| File | Size | Format | Purpose |
|------|------|--------|---------|
| `icon.png` | 512×512+ | PNG | Source icon |
| `icon.ico` | Multi-size | ICO | Windows icon |
| `icon.icns` | Multi-size | ICNS | macOS icon |
| `installer-sidebar.bmp` | 164×314 | BMP (24-bit) | NSIS sidebar |
| `dmg-background.png` | 600×400 | PNG | DMG background |

### Build Commands

```bash
# Generate assets
bash scripts/generate-installer-assets.sh

# Build installers
pnpm run dist:mac        # macOS only
pnpm run dist:win        # Windows only
pnpm run dist:linux      # Linux only
pnpm run dist:all        # All platforms
```

### Key Files

```
ideal-goggles/
├── build-resources/
│   ├── icon.png                    # Source icon
│   ├── icon.icns                   # macOS icon (generated)
│   ├── icon.ico                    # Windows icon (generated)
│   ├── installer-sidebar.bmp       # NSIS sidebar (generated)
│   ├── dmg-background.png          # DMG background (generated)
│   ├── installer.nsh               # NSIS custom script
│   └── entitlements.mac.plist      # macOS entitlements
├── scripts/
│   └── generate-installer-assets.sh # Asset generator
└── package.json                    # Build configuration
```
