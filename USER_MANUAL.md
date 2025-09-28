# 📖 User Manual - Ideal Googles

Welcome to Ideal Googles! This guide will help you get started with your privacy-focused photo search and organization app.

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Search Features](#search-features)
5. [Navigation & Organization](#navigation--organization)
6. [Settings & Configuration](#settings--configuration)
7. [Tips & Tricks](#tips--tricks)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Overview

Ideal Googles is a desktop application that helps you search and organize your photos using:
- **Natural language search** ("sunset at the beach")
- **Face recognition** (find all photos of specific people)
- **Text in images** (OCR - find photos containing text)
- **Similar images** (find visually similar photos)

All processing happens locally on your computer - your photos never leave your machine!

## Installation

### System Requirements

- **Operating System**: macOS 10.14+, Windows 10+, or Ubuntu 20.04+
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: SSD recommended for best performance
- **Processor**: Intel i5 or AMD Ryzen 5 (or better)

### Download & Install

1. **Download the installer** from [Releases](https://github.com/sarvarunajvm/ideal-goggles/releases)
   - macOS: `ideal-googles-1.0.x.dmg`
   - Windows: `ideal-googles-1.0.x.exe`
   - Linux: `ideal-googles-1.0.x.AppImage`

2. **Install the application**:

   **macOS:**
   - Open the DMG file
   - Drag Ideal Googles to Applications folder
   - First time: Right-click and select "Open" (security prompt)

   **Windows:**
   - Run the installer EXE
   - Follow the installation wizard
   - Choose installation directory (default recommended)

   **Linux:**
   - Make AppImage executable: `chmod +x ideal-googles-*.AppImage`
   - Double-click to run or execute from terminal

## Getting Started

### First Launch

1. **Open Ideal Googles** from your Applications/Programs
2. The app will start with:
   - Main search interface
   - Empty photo library (no photos indexed yet)

### Adding Photos

1. Click **"Add Photos"** button or use `File → Add Folder`
2. Select a folder containing your photos
3. Choose indexing options:
   - ✅ **Basic indexing** (fast, metadata only)
   - ✅ **Semantic search** (AI-powered descriptions)
   - ✅ **Face detection** (group by people)
   - ✅ **Text extraction** (OCR)
4. Click **"Start Indexing"**
5. Wait for indexing to complete (progress bar shows status)

## Search Features

### 1. Natural Language Search

Type naturally in the search bar:
- "sunset at the beach"
- "birthday party with cake"
- "red car in parking lot"
- "mountains with snow"

Press **Enter** or click 🔍 to search.

### 2. Face Search

1. Go to **People** tab
2. Browse detected faces
3. Click on a face to see all photos of that person
4. Name people by clicking "Add Name"

### 3. Text Search (OCR)

Find photos containing specific text:
- Put quotes for exact match: `"Happy Birthday"`
- Search for signs, documents, screenshots
- Supports multiple languages

### 4. Similar Image Search

1. Right-click any photo
2. Select **"Find Similar"**
3. View visually similar images

### 5. Advanced Filters

Click **Filter** button to refine results:
- **Date Range**: From/To dates
- **File Type**: JPG, PNG, HEIC, etc.
- **Size**: Minimum/Maximum file size
- **Location**: If GPS data available

## Navigation & Organization

### Photo Grid View

- **Thumbnail Size**: Slider at bottom right
- **Sort By**: Date, Name, Size (dropdown menu)
- **View Mode**: Grid/List toggle

### Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| Search | `Ctrl+F` | `⌘+F` |
| Add Folder | `Ctrl+O` | `⌘+O` |
| Settings | `Ctrl+,` | `⌘+,` |
| Fullscreen | `F11` | `⌘+Ctrl+F` |
| Next Photo | `→` | `→` |
| Previous Photo | `←` | `←` |
| Select All | `Ctrl+A` | `⌘+A` |

### Photo Actions

Right-click on any photo for:
- **Open** - View in default app
- **Show in Folder** - Reveal in file explorer
- **Find Similar** - Search for similar images
- **Copy Path** - Copy file path to clipboard
- **Properties** - View metadata

## Settings & Configuration

Access via **Settings** button or `File → Preferences`

### General Settings

- **Theme**: Light/Dark mode
- **Language**: English (more coming soon)
- **Startup**: Launch at system startup

### Search Settings

- **Results per page**: 25/50/100
- **Default search mode**: Semantic/Text/Face
- **Thumbnail quality**: Low/Medium/High

### Performance Settings

- **Max memory usage**: Limit RAM usage
- **Concurrent processing**: Number of parallel tasks
- **Cache size**: Thumbnail cache limit

### Privacy Settings

- **Analytics**: Disable all telemetry (off by default)
- **Crash reports**: Send anonymous crash data
- **Clear cache**: Remove temporary files

## Tips & Tricks

### 🚀 Performance Tips

1. **Index in batches**: Add folders with <10,000 photos at a time
2. **Use SSD**: Store photo library on SSD for faster access
3. **Close other apps**: Free up RAM during initial indexing

### 🔍 Search Tips

1. **Be specific**: "golden retriever playing" vs just "dog"
2. **Combine terms**: "beach AND sunset" for better results
3. **Use filters**: Narrow down by date/size after searching

### 📸 Organization Tips

1. **Name faces early**: Makes future searches easier
2. **Keep originals**: App works with copies but keep originals safe
3. **Regular folders**: Organize photos in dated folders

## Troubleshooting

### App Won't Start

1. **Check system requirements** (see above)
2. **Restart computer** and try again
3. **Run as administrator** (Windows) or with permissions (macOS)
4. **Check antivirus** - may need to whitelist app

### Search Not Working

1. **Wait for indexing** to complete fully
2. **Re-index folder**: Settings → Manage Folders → Re-index
3. **Clear cache**: Settings → Privacy → Clear Cache
4. **Check disk space**: Need 10% free space minimum

### Slow Performance

1. **Reduce thumbnail quality**: Settings → Performance
2. **Limit results per page**: Settings → Search
3. **Close background apps** to free RAM
4. **Update graphics drivers** for better rendering

### Photos Not Found

1. **Check file formats**: Supports JPG, PNG, HEIC, TIFF, BMP
2. **Verify permissions**: App needs read access to folders
3. **Re-add folder**: Remove and add folder again
4. **Check file corruption**: Try opening in another app

## FAQ

**Q: Are my photos uploaded anywhere?**
A: No! All processing happens locally on your computer. Nothing is uploaded.

**Q: How much disk space do I need?**
A: The app itself needs ~500MB. Thumbnails cache uses ~1GB per 10,000 photos.

**Q: Can I use network drives?**
A: Yes, but performance depends on network speed. Local drives recommended.

**Q: Does it work offline?**
A: Yes! The app works completely offline. No internet required.

**Q: Can I index RAW files?**
A: Basic support for common RAW formats (CR2, NEF, ARW). Full support coming.

**Q: How do I backup my index?**
A: Copy the folder: `~/Library/Application Support/ideal-googles` (macOS) or `%APPDATA%/ideal-googles` (Windows)

**Q: Can multiple users share an index?**
A: Each user has their own index. Sharing planned for future version.

**Q: Is there a mobile app?**
A: Not yet, but it's on our roadmap!

## Support

Need more help?

- 📧 **Email**: Open an issue on [GitHub](https://github.com/sarvarunajvm/ideal-goggles/issues)
- 📚 **Documentation**: Check [README](README.md) and [Developer Guide](DEVELOPER_GUIDE.md)
- 🐛 **Report Bugs**: [GitHub Issues](https://github.com/sarvarunajvm/ideal-goggles/issues/new)

## Privacy & Security

Your privacy is our priority:
- ✅ **100% local processing**
- ✅ **No cloud uploads**
- ✅ **No account required**
- ✅ **No tracking or analytics** (unless you opt-in)
- ✅ **Open source** - audit the code yourself!

---

Thank you for using Ideal Googles! We hope it makes finding your photos a breeze. 📸