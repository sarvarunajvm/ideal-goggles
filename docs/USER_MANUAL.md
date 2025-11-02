# User Manual

Complete guide to using Ideal Goggles for photo organization and search.

## Getting Started

### Installation

Download the installer for your platform from [GitHub Releases](https://github.com/sarvarunajvm/ideal-goggles/releases):

**macOS:**
1. Download `ideal-goggles.dmg`
2. Open the DMG file
3. Drag Ideal Goggles to Applications folder
4. First launch: Right-click app → Open (to bypass Gatekeeper)
5. Grant permissions when prompted

**Windows:**
1. Download `ideal-goggles-Setup.exe`
2. Run installer (may need "Run as administrator")
3. If Windows Defender blocks: Click "More info" → "Run anyway"
4. Follow installation wizard
5. Launch from Start Menu

**Linux:**
1. Download `.AppImage`, `.deb`, or `.rpm`
2. For AppImage: `chmod +x ideal-goggles.AppImage && ./ideal-goggles.AppImage`
3. For Debian/Ubuntu: `sudo dpkg -i ideal-goggles.deb`
4. For Fedora/RHEL: `sudo dnf install ideal-goggles.rpm`

### First Launch

When you first open Ideal Goggles:

1. **Auto-updates** - App checks for updates on startup
   - Notifies when new version available
   - Download and install automatically
   - Can disable in Settings → Updates

2. **Add photo folders** - Click Settings → Folders → Add Folder
   - Select your Pictures folder or external drive
   - Add multiple locations if photos are scattered

3. **Start indexing** - Click "Start Index" button
   - First index takes time (1,000 photos ≈ 2 minutes)
   - You can use the app while indexing runs
   - Progress shown in status bar

4. **Start searching** - Once indexed, type in search bar
   - Basic search works immediately
   - AI features require optional ML installation (see below)

## Searching Photos

### Text Search

Type in the search bar:

```
vacation              # Find by filename/folder
"beach sunset"        # Exact phrase
2023                  # By year
birthday OR party     # Either term
-screenshot           # Exclude term
```

**Search operators:**
- `folder:europe` - Specific folder
- `date:2023-06-15` - Exact date
- `size:>5MB` - File size
- `type:jpg` - File extension

### Semantic Search (AI)

Natural language descriptions (requires ML installation):

```
"dog playing in snow"
"birthday cake with candles"
"sunset over ocean"
"person wearing red dress"
```

How it works: AI understands image content, not just filenames.

### Face Search

Find photos of specific people:

1. **Enable**: Settings → Privacy → Enable Face Search
2. **Add person**: People page → Add Person → Upload 3-5 face photos
3. **Search**: Click person's name to see all their photos

### Visual Similarity

Find similar or duplicate photos:

1. Right-click any photo → "Find Similar"
2. Or use the "Similar" tab and drag/drop a reference image
3. Adjust similarity threshold slider

## Features

### Photo Grid

- **Grid view**: Thumbnail grid (default)
- **List view**: Detailed file information
- **Timeline view**: Organized by date

**Actions:**
- Click: Select photo
- Double-click: Open in default viewer
- Right-click: Context menu (open, find similar, show in folder)
- Space bar: Quick preview

### Lightbox

View photos full-screen:
- Arrow keys: Navigate
- Escape: Close
- Zoom: Scroll or pinch
- Info panel: Press 'i' for EXIF data

### Collections

Organize photos without moving files:

1. Select photos (Ctrl/Cmd+Click for multiple)
2. Right-click → Add to Album
3. Create new album or use existing
4. Access albums from sidebar

### Tagging

Add keywords to photos:
- Select photos → Add Tags button
- Type tags separated by commas
- Auto-complete shows existing tags
- Browse by tag in sidebar

## Settings

### Folders

Manage photo locations:
- **Add Folder**: Index new location
- **Remove Folder**: Stop indexing (doesn't delete photos)
- **External Drives**: Auto-detect when connected
- **Watch Folders**: Auto-index new photos

### Privacy

Control AI features:
- **Face Search**: Enable/disable face recognition
- **Face Encryption**: Protect biometric data (recommended)
- **Search History**: Save recent searches
- **Analytics**: Anonymous usage stats (off by default)

### Performance

Adjust for your system:
- **Thumbnail Size**: Smaller = faster
- **Results per Page**: Fewer = quicker loading
- **Cache Size**: More = faster repeat searches
- **Worker Threads**: More = faster indexing (uses more CPU)

### Indexing

Control how photos are processed:
- **Auto-index**: Daily/weekly/monthly automatic updates
- **Incremental Mode**: Only new/changed files (faster)
- **Full Index**: Reprocess everything (slower, more thorough)
- **Batch Size**: Lower if indexing crashes

## Advanced Features

### ML Features (Optional)

Enable AI-powered search:

**From Settings:**
1. Settings → Advanced → ML Features
2. Click "Install ML Dependencies"
3. Wait for download and installation (1-2 GB)
4. Restart app when prompted

**Features enabled:**
- Natural language semantic search
- Face detection and recognition
- Text extraction from images (OCR)

**Note**: ML features significantly increase app size but enable powerful search.

### Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|--------------|-------|
| Search | Ctrl+F | ⌘+F |
| Select All | Ctrl+A | ⌘+A |
| Delete | Delete | Delete |
| Open Selected | Enter | Enter |
| Quick Preview | Space | Space |
| Fullscreen | F11 | ⌘+⌃+F |
| Settings | Ctrl+, | ⌘+, |

### Command Line

Start with options:

```bash
# Windows
ideal-goggles.exe --safe-mode

# macOS
open -a "Ideal Goggles" --args --safe-mode

# Linux
ideal-goggles --safe-mode
```

**Available options:**
- `--safe-mode` - Disable extensions
- `--reset-settings` - Reset to defaults
- `--rebuild-index` - Force full reindex
- `--portable` - Portable mode (no system integration)

### Export & Backup

**Export search results:**
1. Perform search
2. Click Export button
3. Choose format (CSV, JSON, HTML)
4. Save to file

**Backup database:**
1. Settings → Maintenance → Backup
2. Choose location
3. Include thumbnails (optional, larger file)
4. Schedule automatic backups (recommended)

**Restore backup:**
1. Settings → Maintenance → Restore
2. Select backup file
3. Confirm restore (overwrites current data)

## Troubleshooting

### App Won't Start

**Windows:**
- Run as Administrator
- Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Check Windows Defender isn't blocking
- Delete `%APPDATA%\ideal-goggles` and retry

**macOS:**
- Check Security & Privacy → Allow app
- Grant Full Disk Access in System Preferences
- Delete `~/Library/Application Support/ideal-goggles`
- Run: `xattr -cr /Applications/Ideal\ Goggles.app`

**Linux:**
- Check dependencies: `ldd ideal-goggles`
- Run from terminal to see error messages
- Install missing libraries (usually libgtk-3-0)

### No Search Results

**Check:**
1. Indexing is complete (status bar shows "Idle")
2. Folder is added (Settings → Folders)
3. Supported formats (JPG, PNG, HEIC, TIFF)
4. Folder permissions (app can read files)
5. Try broader search terms

**Fix:**
- Reindex folder: Right-click folder → Reindex
- Clear cache: Settings → Maintenance → Clear Cache
- Check logs: Settings → Logs → View

### Slow Performance

**Indexing:**
- Reduce batch size (Settings → Indexing)
- Close other applications
- Use SSD storage if possible
- Disable ML features temporarily

**Searching:**
- Reduce results per page (Settings → Performance)
- Clear thumbnail cache (Settings → Maintenance)
- Optimize database (Settings → Advanced → Optimize)

**Display:**
- Reduce thumbnail size (Settings → Appearance)
- Disable animations (Settings → Accessibility)
- Lower grid density (Settings → Display)

### Photos Missing

**Common causes:**
1. Unsupported format (only JPG, PNG, HEIC, TIFF)
2. Hidden files (enable in system settings)
3. Network drive disconnected
4. Insufficient permissions
5. Symbolic links not followed

**Solutions:**
- Check file format
- Verify folder still exists
- Reconnect external drives
- Grant folder permissions
- Copy files instead of linking

### Face Search Issues

**Not detecting faces:**
- Ensure face is clearly visible
- Front-facing photos work best
- Good lighting required
- Minimum face size: 80x80 pixels

**Wrong person identified:**
- Add more sample photos (5-10 recommended)
- Include different angles and expressions
- Review and correct misidentified faces
- Re-train person profile

**Face search disabled:**
- Check Settings → Privacy → Enable Face Search
- Grant permissions if prompted
- Ensure ML features installed
- Check logs for errors

## Privacy & Security

### What Gets Stored

**Locally only (never uploaded):**
- Photo metadata (EXIF, dimensions, dates)
- Generated thumbnails
- Search indexes
- Face encodings (if enabled)
- Your preferences

**What stays on disk:**
- Original photos (never moved or modified)
- Files remain in original locations
- You have full control

### Data Location

**Windows:** `%APPDATA%\ideal-goggles`
**macOS:** `~/Library/Application Support/ideal-goggles`
**Linux:** `~/.config/ideal-goggles`

### Delete Your Data

**Complete removal:**
1. Uninstall application
2. Delete data folder (see locations above)
3. Empty recycle bin
4. No traces remain

**Selective deletion:**
- Settings → Privacy → Delete Search History
- Settings → Privacy → Delete Face Data
- Settings → Maintenance → Clear Thumbnails

## FAQ

**Q: Do my photos get uploaded to the cloud?**
A: No. All processing is 100% local. Nothing leaves your computer.

**Q: Can I use this offline?**
A: Yes. The app works completely offline with no internet required.

**Q: How much disk space does it use?**
A: App: ~500MB. Thumbnails: ~100MB per 10,000 photos. Index: ~200MB per 100,000 photos.

**Q: What image formats are supported?**
A: JPG, JPEG, PNG, HEIC, HEIF, TIFF, BMP, GIF. RAW support coming soon.

**Q: Why is indexing slow?**
A: First index processes all photos. Use SSD for faster speeds. Incremental updates are much faster.

**Q: Can I search videos?**
A: Not yet, but video support is planned for a future release.

**Q: Is face recognition accurate?**
A: Typically 95%+ with good quality photos. Accuracy improves with more sample photos.

**Q: Can multiple people use the same library?**
A: Each user account has a separate index. Shared library support is planned.

**Q: How do I move my library to a new computer?**
A: Use Settings → Maintenance → Backup to export. Restore on new computer.

## Support

**Documentation:**
- [Developer Guide](DEVELOPER_GUIDE.md) - Technical details
- [Contributing](CONTRIBUTING.md) - How to contribute

**Get Help:**
- [GitHub Issues](https://github.com/sarvarunajvm/ideal-goggles/issues) - Report bugs
- [Discussions](https://github.com/sarvarunajvm/ideal-goggles/discussions) - Ask questions

**Contact:**
- Email: support@ideal-goggles.app
- GitHub: [@sarvarunajvm](https://github.com/sarvarunajvm)

---

**Version 1.0.8** • Last updated: 2025-11-02 • [View Changelog](https://github.com/sarvarunajvm/ideal-goggles/releases)
