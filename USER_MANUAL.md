# 📸 Photo Search System - Complete User Manual

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Searching Photos](#searching-photos)
5. [Managing People](#managing-people)
6. [Indexing Your Photos](#indexing-your-photos)
7. [Settings & Configuration](#settings--configuration)
8. [Navigation & Organization](#navigation--organization)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Features](#advanced-features)
11. [Privacy & Security](#privacy--security)
12. [FAQ](#faq)
13. [Support](#support)

---

## Overview

Photo Search System (Ideal Goggles) is a privacy-focused desktop application that helps you search and organize your photos using:

- 🔍 **Text Search**: Find photos by filename, folder, or text in images (OCR)
- 🎨 **Semantic Search**: Natural language queries ("sunset at the beach")
- 🖼️ **Image Search**: Find similar photos by uploading an example
- 👤 **Face Recognition**: Search photos by specific people (opt-in)
- 📅 **Date Filtering**: Search within specific date ranges

**Key Features:**
- ✅ 100% local processing - photos never leave your computer
- ✅ No cloud uploads or account required
- ✅ Supports 100,000+ photos
- ✅ Fast search (<2 seconds)
- ✅ Open source and auditable

---

## Installation

### System Requirements

**Minimum:**
- **OS**: Windows 10, macOS 10.14, Ubuntu 20.04
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Processor**: 64-bit, dual-core

**Recommended:**
- **OS**: Windows 11, macOS 12+, Ubuntu 22.04
- **RAM**: 8GB or more
- **Storage**: SSD with 10GB+ free
- **Processor**: Intel i5/AMD Ryzen 5 or better

### Platform-Specific Installation

#### 🪟 Windows

1. **Download** `PhotoSearch-Setup-1.0.8.exe` from [Releases](https://github.com/sarvarunajvm/ideal-goggles/releases)
2. **Run installer** as Administrator:
   - Right-click → "Run as administrator"
   - If Windows Defender appears, click "More info" → "Run anyway"
3. **Follow installation wizard**:
   - Choose installation directory (default: `C:\Program Files\PhotoSearch`)
   - Select "Create desktop shortcut"
   - Click "Install"
4. **Launch** from Start Menu or Desktop shortcut

**Troubleshooting Windows Installation:**
- If installer fails: Temporarily disable antivirus
- Missing DLLs: Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Permission errors: Ensure you have admin rights

#### 🍎 macOS

1. **Download** `PhotoSearch-1.0.8.dmg` from [Releases](https://github.com/sarvarunajvm/ideal-goggles/releases)
2. **Open DMG file**:
   - Double-click the downloaded file
   - Drag PhotoSearch to Applications folder
3. **First launch** (security bypass):
   - Open Finder → Applications
   - Right-click PhotoSearch → Select "Open"
   - Click "Open" in security dialog
4. **Grant permissions** when prompted:
   - Photos library access (optional)
   - Full disk access (for indexing)

**Troubleshooting macOS Installation:**
- "App is damaged": Run `xattr -cr /Applications/PhotoSearch.app` in Terminal
- Gatekeeper issues: System Preferences → Security & Privacy → "Open Anyway"
- M1/M2 Macs: App runs via Rosetta 2 (automatic)

#### 🐧 Linux

**Ubuntu/Debian:**
```bash
# Download the .deb package
wget https://github.com/sarvarunajvm/ideal-goggles/releases/download/v1.0.8/photosearch_1.0.8_amd64.deb

# Install dependencies
sudo apt update
sudo apt install -y tesseract-ocr python3-pip libgtk-3-0

# Install the package
sudo dpkg -i photosearch_1.0.8_amd64.deb

# Fix any dependency issues
sudo apt-get install -f

# Launch
photosearch
```

**Fedora/RHEL:**
```bash
# Download the .rpm package
wget https://github.com/sarvarunajvm/ideal-goggles/releases/download/v1.0.8/photosearch-1.0.8.x86_64.rpm

# Install
sudo dnf install photosearch-1.0.8.x86_64.rpm

# Launch
photosearch
```

**AppImage (Universal):**
```bash
# Download AppImage
wget https://github.com/sarvarunajvm/ideal-goggles/releases/download/v1.0.8/PhotoSearch-1.0.8.AppImage

# Make executable
chmod +x PhotoSearch-1.0.8.AppImage

# Run
./PhotoSearch-1.0.8.AppImage
```

**Arch Linux (AUR):**
```bash
yay -S photosearch
# or
paru -S photosearch
```

**Troubleshooting Linux Installation:**
- Missing libraries: `ldd PhotoSearch.AppImage` to check
- Permission denied: Ensure file is executable
- Desktop integration: `./PhotoSearch.AppImage --install-desktop-file`

---

## Getting Started

### First Launch

1. **Start the application**:
   - Windows: Start Menu → PhotoSearch
   - macOS: Applications → PhotoSearch
   - Linux: Application menu or terminal

2. **Initial setup wizard** appears:
   - Choose interface language
   - Select theme (Light/Dark/Auto)
   - Configure initial settings

3. **Main interface** components:
   - Search bar at top
   - Empty photo grid (no photos indexed yet)
   - Navigation sidebar
   - Status bar at bottom

### Quick Start Guide

#### Step 1: Add Photo Folders

1. Click **Settings** → **Folders**
2. Click **Add Folder** button
3. Navigate to your photos directory:
   - Windows: `C:\Users\[Username]\Pictures`
   - macOS: `~/Pictures`
   - Linux: `~/Pictures` or `~/Photos`
4. Click **Select Folder**
5. Repeat for all photo locations

#### Step 2: Configure Indexing Options

Before indexing, choose what to enable:

- ✅ **Basic Indexing** (always on): Filenames, dates, metadata
- ☐ **OCR Text Extraction**: Read text from images
- ☐ **Semantic Search**: AI-powered visual search
- ☐ **Face Detection**: Group photos by people (privacy-conscious)

#### Step 3: Start Initial Index

1. Click **Start Full Index** button
2. Monitor progress in status bar:
   - Phase indicator (Discovery → Metadata → OCR → etc.)
   - Files processed counter
   - Estimated time remaining
3. You can use the app while indexing continues

**Indexing Times (approximate):**
- 1,000 photos: 1-2 minutes
- 10,000 photos: 10-15 minutes
- 100,000 photos: 1-2 hours

---

## Searching Photos

### Search Modes

#### 1. Text Search (Default)

Type in the search bar and press Enter:

**Examples:**
```
vacation           # Photos with "vacation" in name/path
IMG_2023          # Specific filename pattern
"exact phrase"    # Exact match with quotes
beach sunset      # Multiple keywords (AND)
beach OR sunset   # Either keyword
-excluded         # Exclude term
```

**Advanced operators:**
- `folder:europe` - Search specific folder
- `date:2023-06-15` - Specific date
- `size:>5MB` - File size filters
- `type:jpg` - File type filter

#### 2. Semantic Search (Natural Language)

Click **Semantic** tab, then describe what you want:

**Examples:**
- "golden retriever playing in park"
- "birthday party with cake and balloons"
- "sunset over ocean with sailboat"
- "person wearing red dress at wedding"
- "indoor photo with Christmas tree"

#### 3. Reverse Image Search

Click **Similar** tab:

1. Drag & drop an image OR click to browse
2. Adjust similarity threshold (slider)
3. View results ranked by similarity
4. Useful for finding:
   - Duplicates
   - Similar compositions
   - Photos from same event

#### 4. Face Search (If Enabled)

**From People page:**
1. Navigate to **People** section
2. Click on a person's profile
3. Click **Search Photos of This Person**

**Quick search:**
- Type person's name in search bar
- Results show all their photos

### Using Filters

Click **Filters** button to refine results:

#### Date Range
- **From**: Start date (calendar picker)
- **To**: End date (calendar picker)
- Presets: Today, This Week, This Month, This Year

#### File Properties
- **Type**: JPG, PNG, HEIC, RAW, etc.
- **Size**: Min/Max in MB
- **Dimensions**: Width × Height ranges
- **Orientation**: Portrait/Landscape/Square

#### Location (If GPS data exists)
- **Country/State/City** dropdowns
- **Radius**: Distance from point
- **Map view**: Visual selection

### Search Results

#### Result Display
Each photo shows:
- **Thumbnail** preview
- **Filename**
- **Folder path**
- **Date taken**
- **Match badges**:
  - 📝 Text match
  - 🖼️ Visual match
  - 👤 Face match
  - 📅 Date match

#### Result Actions

**Single-click**: Select photo
**Double-click**: Open in default viewer
**Right-click menu**:
- Open → Launch in default app
- Open With → Choose application
- Show in Folder → Reveal in file manager
- Find Similar → Search for similar images
- Copy Path → Copy full file path
- Properties → View EXIF metadata
- Add to Album → Organize in collections

#### Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| Search | Ctrl+F | ⌘+F |
| Clear search | Esc | Esc |
| Select all | Ctrl+A | ⌘+A |
| Open selected | Enter | Enter |
| Delete search | Ctrl+D | ⌘+D |
| Next page | Page Down | Page Down |
| Previous page | Page Up | Page Up |

---

## Managing People

### Setting Up Face Recognition

1. **Enable in Settings**:
   - Settings → Privacy → Enable Face Search
   - Read and accept privacy notice
   - Choose encryption option (recommended)

2. **Initial face detection**:
   - Runs during next full index
   - Groups detected faces automatically
   - Unknown faces appear in "Unnamed" section

### Adding People

#### Method 1: From Detected Faces
1. Go to **People** page
2. Click on unnamed face group
3. Click **Add Name**
4. Enter person's name
5. Confirm to apply to all similar faces

#### Method 2: Manual Addition
1. Click **➕ Add Person** button
2. Enter person's name
3. Click **Upload Photos**
4. Select 3-5 clear face photos:
   - Front-facing preferred
   - Different angles/lighting helpful
   - Avoid group photos for samples
5. Click **Save Person**

### Managing People Profiles

#### Edit Person
1. Click person's card
2. Options available:
   - **Rename**: Change display name
   - **Add Photos**: Include more samples
   - **Remove Photos**: Delete samples
   - **Merge**: Combine with another person
   - **Split**: Separate mixed identities

#### Privacy Controls
- **Active/Inactive**: Toggle search visibility
- **Private**: Hide from other users
- **Delete**: Remove completely (keeps photos)

### Best Practices

**For accurate recognition:**
- Use 5-10 sample photos per person
- Include various angles and expressions
- Update samples as people age
- Review and correct misidentified faces

**Privacy considerations:**
- Only add people with consent
- Use Private mode for sensitive profiles
- Regularly review enrolled faces
- Export/delete data when needed

---

## Indexing Your Photos

### Understanding the Index

The index enables fast searching by processing:

1. **Discovery Phase**: Finds all image files
2. **Metadata Extraction**: EXIF data, dates, camera info
3. **OCR Processing**: Text extraction from images
4. **Embedding Generation**: AI search vectors
5. **Thumbnail Creation**: Preview images
6. **Face Detection**: Identify people (optional)

### Indexing Types

#### Full Index
- Processes entire photo library
- Rebuilds all search data
- Use for initial setup or major changes
- Settings → Indexing → **Start Full Index**

#### Incremental Index
- Only new/modified files
- Runs automatically daily
- Manual trigger: **Quick Index** button
- Much faster than full index

#### Selective Index
- Specific folders only
- Right-click folder → **Reindex This Folder**
- Useful for troubleshooting

### Monitoring Progress

Status bar shows:
- **Current phase**: Discovery/OCR/Faces/etc.
- **Progress**: "5,234 of 10,000 files"
- **Time remaining**: Estimated completion
- **Errors**: Click to view issues

### Optimizing Performance

#### Before Indexing
- Close unnecessary applications
- Ensure adequate disk space (10% free)
- Connect laptop to power
- Disable sleep/hibernation

#### During Indexing
- You can continue using the app
- Search works on processed files
- Pause if system slows: **Pause Index**
- Resume later: **Resume Index**

#### Indexing Settings
- **Batch Size**: 32 (default), lower if crashes
- **Worker Threads**: 4 (default), based on CPU
- **Memory Limit**: 512MB (default)
- **Priority**: Low/Normal/High

### Troubleshooting Index Issues

**Photos not appearing:**
1. Check supported formats (JPG, PNG, HEIC, TIFF)
2. Verify folder permissions
3. Look for errors in log
4. Try selective reindex

**Indexing crashes:**
1. Reduce batch size
2. Decrease worker threads
3. Increase memory limit
4. Check disk space

**Slow indexing:**
1. Check CPU/memory usage
2. Disable other features temporarily
3. Index overnight
4. Use SSD storage

---

## Settings & Configuration

### General Settings

#### Appearance
- **Theme**: Light/Dark/Auto (follows system)
- **Language**: English (more coming)
- **Font Size**: Small/Medium/Large
- **Thumbnail Size**: 128px to 512px
- **Grid Density**: Compact/Normal/Comfortable

#### Startup
- **Launch at startup**: Auto-start with system
- **Start minimized**: To system tray
- **Check for updates**: Automatic/Manual
- **Restore last session**: Remember searches

### Search Settings

#### Performance
- **Results per page**: 25/50/100/200
- **Search timeout**: 5-30 seconds
- **Cache size**: Memory for quick results
- **Preload images**: Faster browsing

#### Defaults
- **Default search mode**: Text/Semantic/Image
- **Default sort**: Date/Name/Size/Relevance
- **Default view**: Grid/List/Timeline
- **Safe search**: Filter sensitive content

### Privacy Settings

#### Data Collection
- **Analytics**: Off by default (anonymous usage)
- **Crash reports**: Help improve stability
- **Search history**: Save recent searches
- **Telemetry**: Completely optional

#### Security
- **Face data encryption**: Protect biometric data
- **Database encryption**: Secure all metadata
- **Auto-lock**: Require password after idle
- **Secure delete**: Overwrite deleted data

### Advanced Settings

#### Processing
- **OCR Languages**: English, Spanish, French, etc.
- **Face detection sensitivity**: Low/Medium/High
- **Duplicate detection**: Find similar photos
- **Auto-tagging**: Generate keywords

#### Network
- **Proxy settings**: For corporate networks
- **Offline mode**: Disable all network
- **Update channel**: Stable/Beta/Nightly
- **Bandwidth limit**: For updates

#### Developer
- **Debug logging**: Detailed logs
- **Console output**: Show terminal
- **API endpoint**: Custom backend
- **Experimental features**: Try new functions

---

## Navigation & Organization

### Interface Overview

```
┌─────────────────────────────────────┐
│ [Search Bar]           [Filters] 🔍 │
├──────┬──────────────────────────────┤
│      │                              │
│ Nav  │     Photo Grid/Results       │
│ Bar  │                              │
│      │                              │
├──────┴──────────────────────────────┤
│ Status Bar                          │
└─────────────────────────────────────┘
```

### Navigation Sidebar

- **🔍 Search**: Main search interface
- **👥 People**: Face recognition management
- **📁 Folders**: Browse by directory
- **📅 Timeline**: Chronological view
- **⭐ Favorites**: Starred photos
- **🏷️ Tags**: Organized by keywords
- **⚙️ Settings**: Configuration

### View Modes

#### Grid View (Default)
- Thumbnail grid layout
- Adjustable size slider
- Hover for quick info
- Space bar for preview

#### List View
- Detailed file information
- Sortable columns
- Compact display
- Batch selection easy

#### Timeline View
- Grouped by date
- Chronological scroll
- Event detection
- Year/Month sections

### Photo Organization

#### Creating Albums
1. Right-click photos → **Add to Album**
2. Choose existing or **Create New Album**
3. Name album and add description
4. Albums appear in sidebar

#### Tagging Photos
- Select photos → **Add Tags**
- Type tags separated by commas
- Auto-complete from existing
- Browse by tags in sidebar

#### Batch Operations
Select multiple photos (Ctrl/Cmd+Click):
- **Export**: Save copies to folder
- **Delete from Index**: Remove from search
- **Add Tags**: Bulk tagging
- **Move/Copy**: Organize files

### Keyboard Navigation

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| Navigate photos | Arrow keys | Arrow keys |
| Page up/down | PgUp/PgDn | PgUp/PgDn |
| Home/End | Home/End | Home/End |
| Zoom in/out | Ctrl +/- | ⌘ +/- |
| Fullscreen | F11 | ⌘⌃F |
| Quick preview | Space | Space |
| Slideshow | F5 | F5 |

---

## Troubleshooting

### Application Issues

#### App Won't Start

**Windows:**
1. Run as Administrator
2. Check Windows Defender exceptions
3. Reinstall Visual C++ Redistributable
4. Delete `%APPDATA%\PhotoSearch` and retry

**macOS:**
1. Check Security & Privacy settings
2. Grant full disk access
3. Delete `~/Library/Application Support/PhotoSearch`
4. Reinstall from fresh DMG

**Linux:**
1. Check dependencies: `ldd photosearch`
2. Run from terminal for error messages
3. Delete `~/.config/photosearch`
4. Check file permissions

#### Crashes/Freezes

1. **Update to latest version**
2. **Check system resources** (RAM/CPU)
3. **Disable hardware acceleration**: Settings → Advanced
4. **Clear cache and indexes**: Settings → Maintenance
5. **Run in safe mode**: Hold Shift while starting

### Search Problems

#### No Results Found

1. **Verify indexing complete**: Check status bar
2. **Confirm folder added**: Settings → Folders
3. **Check file formats**: Only images supported
4. **Try different search terms**: Be less specific
5. **Clear filters**: May be too restrictive

#### Slow Search

1. **Reduce results per page**: Settings → Search
2. **Clear search cache**: Settings → Maintenance
3. **Defragment database**: Settings → Advanced → Optimize
4. **Check disk speed**: SSD recommended
5. **Limit search scope**: Use folder filters

#### Wrong Results

1. **Reindex affected folders**: Right-click → Reindex
2. **Update AI models**: Settings → Updates
3. **Adjust similarity threshold**: For image search
4. **Check OCR language**: Settings → Processing
5. **Report false positives**: Help → Feedback

### Indexing Problems

#### Indexing Stuck

1. **Check status details**: Click status bar
2. **View error log**: Settings → Logs
3. **Restart indexing**: Stop then Start
4. **Process smaller batches**: Reduce folder size
5. **Check disk space**: Need 10% free minimum

#### Missing Photos

1. **Supported formats only**: JPG, PNG, HEIC, TIFF
2. **Check permissions**: App needs read access
3. **Hidden files**: Enable in system settings
4. **Symbolic links**: May not follow
5. **Network drives**: Must be mounted

#### Indexing Errors

Common errors and solutions:

- **"Access denied"**: Grant folder permissions
- **"Out of memory"**: Reduce batch size
- **"Disk full"**: Free up space
- **"Corrupt image"**: Remove or repair file
- **"Unsupported format"**: Convert to supported type

### Performance Issues

#### High CPU Usage

1. **Pause indexing**: During heavy work
2. **Reduce worker threads**: Settings → Performance
3. **Disable face detection**: Temporarily
4. **Lower thumbnail quality**: Settings → Display
5. **Close other apps**: Free resources

#### High Memory Usage

1. **Reduce cache size**: Settings → Performance
2. **Lower batch size**: Settings → Indexing
3. **Clear thumbnails**: Settings → Maintenance
4. **Restart app**: Clears memory leaks
5. **Add more RAM**: If consistently high

#### Slow Loading

1. **Use SSD storage**: Much faster than HDD
2. **Optimize database**: Settings → Maintenance
3. **Reduce thumbnail size**: Settings → Display
4. **Enable preloading**: Settings → Performance
5. **Check network drives**: Local is faster

---

## Advanced Features

### Command Line Interface

```bash
# Start with options
photosearch [options]

# Options:
--safe-mode          Start in safe mode
--reset-settings     Reset to defaults
--rebuild-index      Force full reindex
--portable           Run portable mode
--debug              Enable debug logging
--minimized          Start minimized
--folder <path>      Add folder on start
```

### API Access

Enable API for third-party tools:

1. Settings → Advanced → Enable API
2. Generate API key
3. Default endpoint: `http://localhost:5555/api`

**Example usage:**
```bash
# Search via API
curl -H "X-API-Key: your-key" \
  "http://localhost:5555/api/search?q=sunset"

# Get status
curl -H "X-API-Key: your-key" \
  "http://localhost:5555/api/status"
```

### Automation

#### Scheduled Tasks

Settings → Automation:
- **Auto-index**: Daily/Weekly/Monthly
- **Cleanup**: Remove orphaned entries
- **Backup**: Export database regularly
- **Reports**: Email search statistics

#### Watch Folders

- **Real-time monitoring**: Instant indexing
- **Hot folders**: Auto-import and organize
- **Cloud sync**: Monitor synced folders
- **Action rules**: Auto-tag, move, etc.

### Export & Backup

#### Export Data

**Search Results:**
- CSV: Spreadsheet compatible
- JSON: Developer friendly
- HTML: Visual report
- PDF: Print ready

**Database Backup:**
1. Settings → Maintenance → Backup
2. Choose location
3. Include: Database, Thumbnails, Settings
4. Schedule automatic backups

#### Import Data

- **From other apps**: Lightroom, Photos, Picasa
- **Restore backup**: Previous exports
- **Merge databases**: Combine libraries
- **Migration tool**: Transfer between computers

### Power User Tips

#### Search Tricks

```
# Complex queries
(beach OR ocean) AND sunset -people
folder:2023/* AND (birthday OR party)
date:2023-06..2023-08 AND location:California

# Regular expressions (advanced)
regex:IMG_[0-9]{4}\.jpg
regex:^DSC.*\.(jpg|raw)$
```

#### Batch Processing

1. **Smart selections**: Alt+Click for similar
2. **Quick actions**: Number keys for presets
3. **Scripting**: JavaScript automation API
4. **Workflows**: Chain multiple operations

#### Performance Tuning

**For 100k+ photos:**
```ini
# Edit settings.ini
[Performance]
BatchSize=64
Workers=8
MemoryLimit=2048
CacheSize=1024
PreloadCount=50
```

---

## Privacy & Security

### Our Privacy Commitment

- ✅ **100% local processing**: No cloud uploads
- ✅ **No account required**: Use anonymously
- ✅ **No tracking**: Unless explicitly opted in
- ✅ **Open source**: Audit the code yourself
- ✅ **Your data**: Export or delete anytime

### Data Storage

#### What We Store

**Locally only:**
- Photo metadata (not photos themselves)
- Generated thumbnails
- Search indexes
- Face encodings (if enabled)
- Your settings

**Location:**
- Windows: `%APPDATA%\PhotoSearch`
- macOS: `~/Library/Application Support/PhotoSearch`
- Linux: `~/.config/photosearch`

#### What We DON'T Store

- ❌ Original photos (remain in place)
- ❌ Personal information
- ❌ Usage statistics (unless opted in)
- ❌ Search history (unless enabled)
- ❌ Any cloud backups

### Security Features

#### Encryption

- **Face data**: AES-256 encryption
- **Database**: Optional full encryption
- **Network**: TLS for any connections
- **Passwords**: Bcrypt hashing

#### Access Control

- **App lock**: Password/biometric
- **Folder permissions**: Read-only access
- **API security**: Key authentication
- **Audit logs**: Track access

### Managing Your Data

#### Export Your Data

1. Settings → Privacy → Export Data
2. Choose format (ZIP/TAR)
3. Includes all metadata and settings
4. Portable to other installations

#### Delete Your Data

**Complete removal:**
1. Uninstall application
2. Delete data folder (see locations above)
3. Empty trash/recycle bin
4. No traces remain

**Selective deletion:**
- Remove specific people
- Clear search history
- Delete thumbnails
- Reset specific folders

### GDPR & Compliance

- **Right to access**: Export all data
- **Right to deletion**: Complete removal
- **Right to portability**: Standard formats
- **Right to correction**: Edit any data
- **Consent**: Explicit opt-in for features

---

## FAQ

### General Questions

**Q: Do my photos leave my computer?**
A: No, all processing is 100% local. No uploads.

**Q: Can I use this offline?**
A: Yes, the app works completely offline.

**Q: How much space do I need?**
A: App: ~500MB, Thumbnails: ~1GB per 10,000 photos, Index: ~2GB per 100,000 photos

**Q: What image formats are supported?**
A: JPG, JPEG, PNG, HEIC, HEIF, TIFF, BMP, GIF. RAW support coming.

**Q: Can I index network drives?**
A: Yes, but performance depends on network speed.

### Feature Questions

**Q: How accurate is face recognition?**
A: Typically 95%+ with good samples. Improves over time.

**Q: What languages does OCR support?**
A: 100+ languages via Tesseract. Configure in settings.

**Q: Can I search videos?**
A: Not yet, but it's on our roadmap.

**Q: Is there a mobile app?**
A: Currently desktop only. Mobile planned for future.

**Q: Can multiple users share a library?**
A: Each user has separate index. Sharing planned.

### Technical Questions

**Q: Why is indexing slow?**
A: First index processes everything. Use SSD for speed.

**Q: Can I move my library?**
A: Yes, update folder paths in settings after moving.

**Q: How do I backup?**
A: Settings → Maintenance → Backup Database

**Q: Does it work with cloud storage?**
A: Yes, if synced locally (Dropbox, OneDrive, etc.)

**Q: Can I run multiple instances?**
A: Not recommended. Use different user accounts.

### Troubleshooting Questions

**Q: Why don't I see all my photos?**
A: Check indexing status, folder permissions, and supported formats.

**Q: Search returns nothing?**
A: Wait for indexing to complete. Check folder settings.

**Q: App crashes on startup?**
A: Delete settings folder and reinstall.

**Q: High memory usage?**
A: Normal during indexing. Adjust settings if persistent.

**Q: Can't enable face search?**
A: Check privacy settings and grant necessary permissions.

---

## Support

### Getting Help

#### Documentation
- **This Manual**: Comprehensive guide
- **README**: [GitHub README](README.md)
- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **API Docs**: [API Documentation](docs/api.md)

#### Community Support
- **GitHub Issues**: [Report bugs](https://github.com/sarvarunajvm/ideal-goggles/issues)
- **Discussions**: [Ask questions](https://github.com/sarvarunajvm/ideal-goggles/discussions)
- **Discord**: Community chat (coming soon)

#### Contact
- **Email**: support@photosearch.app
- **Twitter**: @photosearchapp
- **Website**: https://photosearch.app

### Reporting Issues

**Before reporting:**
1. Update to latest version
2. Check FAQ and troubleshooting
3. Search existing issues

**When reporting include:**
- App version (Help → About)
- Operating system
- Steps to reproduce
- Error messages
- Log files (if applicable)

### Contributing

We welcome contributions!

- **Code**: Pull requests on GitHub
- **Translations**: Help localize the app
- **Documentation**: Improve guides
- **Testing**: Beta test new features
- **Feedback**: Suggest improvements

### License & Credits

- **License**: MIT (open source)
- **Privacy**: No telemetry without consent
- **Dependencies**: See [CREDITS.md](CREDITS.md)
- **Contributors**: See [CONTRIBUTORS.md](CONTRIBUTORS.md)

---

## Appendix

### File Locations

#### Windows
```
%APPDATA%\PhotoSearch\          # Main data
  ├── database.db               # Search index
  ├── thumbnails\               # Cache
  ├── settings.ini              # Configuration
  └── logs\                     # Debug logs
```

#### macOS
```
~/Library/Application Support/PhotoSearch/
  ├── database.db
  ├── thumbnails/
  ├── settings.plist
  └── logs/
```

#### Linux
```
~/.config/photosearch/
  ├── database.db
  ├── thumbnails/
  ├── settings.conf
  └── logs/
```

### Performance Benchmarks

| Photo Count | Initial Index | RAM Usage | Disk Space |
|------------|---------------|-----------|------------|
| 1,000 | 1-2 min | 200 MB | 100 MB |
| 10,000 | 10-15 min | 500 MB | 1 GB |
| 50,000 | 45-60 min | 1 GB | 5 GB |
| 100,000 | 1.5-2 hrs | 2 GB | 10 GB |
| 500,000 | 8-10 hrs | 4 GB | 50 GB |

### Version History

- **v1.0.8** (Current): Production logging, error tracking
- **v1.0.7**: Face search, People management
- **v1.0.6**: Semantic search improvements
- **v1.0.5**: OCR multi-language support
- **v1.0.0**: Initial public release

---

Thank you for using Photo Search System! We hope it makes finding your memories effortless. 📸

**Last Updated**: 2025-09-29
**Version**: 1.0.8