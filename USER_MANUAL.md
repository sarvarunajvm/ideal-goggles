# Photo Search & Navigation - User Manual

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Search Features](#search-features)
5. [Navigation & Organization](#navigation--organization)
6. [Settings & Configuration](#settings--configuration)
7. [Troubleshooting](#troubleshooting)
8. [Privacy & Security](#privacy--security)

---

## Overview

Photo Search & Navigation is a powerful desktop application that helps you organize, search, and navigate your photo collection using AI-powered search capabilities. The application processes all photos locally on your computer, ensuring complete privacy of your personal photos.

### Key Features
- **Text Search**: Find photos using natural language descriptions
- **Semantic Search**: AI-powered image understanding for content-based search
- **Face Recognition**: Identify and group photos by people (optional)
- **OCR Text Search**: Search text content within photos (documents, signs, etc.)
- **Metadata Search**: Search by camera settings, date, location, and file properties
- **Smart Organization**: Automatic categorization and tagging
- **Fast Navigation**: Keyboard shortcuts and intuitive UI for quick browsing

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 2GB free space + photo storage
- **Hardware**: Modern CPU with support for machine learning (recommended)

---

## Installation

### Windows Installation
1. Download the installer from the releases page
2. Run `PhotoSearchSetup.exe` as administrator
3. Follow the installation wizard
4. Launch from Start Menu or desktop shortcut

### macOS Installation
1. Download the `.dmg` file
2. Open the disk image and drag the app to Applications folder
3. First launch: Right-click → Open (to bypass Gatekeeper)
4. Grant necessary permissions when prompted

### Linux Installation
1. Download the `.AppImage` or `.deb` file
2. For AppImage: Make executable and run directly
3. For Debian/Ubuntu: `sudo dpkg -i photo-search.deb`

### First-Time Setup
1. **Welcome Screen**: Configure initial settings
2. **Photo Directories**: Add folders containing your photos
3. **Privacy Settings**: Choose which AI features to enable
4. **Initial Indexing**: Wait for the app to process your photos (this may take time)

---

## Getting Started

### Adding Photo Directories
1. Open **Settings** → **Photo Directories**
2. Click **Add Directory**
3. Select folders containing your photos
4. Choose indexing options:
   - **Full Indexing**: Complete AI analysis (recommended)
   - **Basic Indexing**: Metadata and thumbnails only
   - **Watch for Changes**: Automatically detect new photos

### Understanding the Interface

#### Main Window
- **Search Bar**: Enter search queries at the top
- **Results Grid**: Displays matching photos in a grid layout
- **Preview Panel**: Shows larger preview and metadata (can be toggled)
- **Navigation Bar**: Quick access to filters and sorting options
- **Status Bar**: Shows indexing progress and system status

#### Keyboard Shortcuts
- `Ctrl/Cmd + F`: Focus search bar
- `Space`: Quick preview current photo
- `Arrow Keys`: Navigate between photos
- `Enter`: Open photo in full-screen viewer
- `Ctrl/Cmd + D`: Open folder containing selected photo
- `Esc`: Close preview or modal dialogs

---

## Search Features

### Text Search
Search using natural language descriptions of what you're looking for:

**Examples:**
- `"sunset beach"` - Photos taken at sunset on a beach
- `"birthday party kids"` - Children's birthday party photos
- `"red car vintage"` - Vintage red car photos
- `"mountain hiking"` - Mountain hiking photos

**Search Tips:**
- Use quotes for exact phrases: `"golden gate bridge"`
- Combine multiple terms: `wedding flowers white`
- Use dates: `Christmas 2022` or `vacation July`

### Advanced Search Filters

#### Date Filters
- **Date Range**: Select specific date ranges
- **Quick Filters**: Today, This Week, This Month, This Year
- **Special Events**: Christmas, New Year, Summer, etc.

#### Metadata Filters
- **Camera**: Filter by camera make/model
- **Settings**: ISO, aperture, shutter speed ranges
- **File Type**: JPEG, PNG, RAW files
- **File Size**: Small, medium, large files
- **Orientation**: Portrait, landscape, square

#### Location Filters (if GPS data available)
- **City/Country**: Filter by location
- **Map Selection**: Select areas on a map
- **Distance**: Within X miles of a location

### Semantic Search
AI-powered search that understands image content:

**Examples:**
- `dogs playing` - Finds photos of dogs playing, even without text tags
- `food on table` - Identifies meal photos
- `people smiling` - Detects happy expressions
- `outdoor landscape` - Natural scenes and landscapes

### Face Search (Optional)
If enabled, the app can recognize and group photos by people:

1. **Face Detection**: Automatically finds faces in photos
2. **Face Grouping**: Groups similar faces together
3. **Name Assignment**: Manually assign names to face groups
4. **Privacy**: All face data stored locally, never uploaded

**Note**: Face recognition is optional and can be disabled in Settings.

### OCR Text Search
Searches text content found within photos:

**Examples:**
- `"stop sign"` - Photos containing stop signs
- `restaurant menu` - Photos of restaurant menus
- `business card` - Photos of business cards with text
- `street signs` - Photos with street signage

---

## Navigation & Organization

### Viewing Photos

#### Grid View
- Adjustable thumbnail sizes (Small, Medium, Large)
- Batch selection with Ctrl/Cmd + Click
- Quick actions: Delete, Copy, Move, Tag

#### Preview Mode
- Large preview with metadata panel
- Navigation arrows or keyboard controls
- Zoom and pan for detailed viewing
- EXIF data display

#### Full-Screen Viewer
- Immersive viewing experience
- Slideshow mode with customizable timing
- Zoom up to 100% for pixel-perfect viewing
- Basic editing tools (rotate, crop)

### Organization Tools

#### Smart Collections
Automatically created collections based on:
- **Recent**: Recently added or modified photos
- **Favorites**: Starred or highly-rated photos
- **Similar**: Visually similar photo groups
- **Events**: Automatically detected events/occasions

#### Manual Organization
- **Tags**: Add custom tags to photos
- **Ratings**: 1-5 star rating system
- **Folders**: Virtual folders for organization
- **Albums**: Create themed photo albums

#### Batch Operations
Select multiple photos to:
- Apply tags or ratings
- Move to folders
- Export in different formats
- Delete or archive

---

## Settings & Configuration

### General Settings
- **Theme**: Light, Dark, or System theme
- **Language**: Interface language selection
- **Startup**: Launch on system startup
- **Updates**: Automatic update checking

### Photo Directories
- **Add/Remove**: Manage indexed directories
- **Watch Folders**: Automatically detect new photos
- **Include/Exclude**: File type and folder filtering
- **Scan Frequency**: How often to check for changes

### AI & Privacy Settings
- **Semantic Search**: Enable/disable AI image analysis
- **Face Recognition**: Enable/disable face detection
- **OCR Processing**: Enable/disable text recognition
- **Data Storage**: Choose where AI models are stored
- **Processing Priority**: Balance between speed and system resources

### Performance Settings
- **Thumbnail Quality**: Balance between quality and storage
- **Cache Size**: How much disk space to use for caches
- **Background Processing**: When to run AI analysis
- **Memory Usage**: Limit memory usage for large collections

### Import/Export Settings
- **File Naming**: How to handle duplicate filenames
- **Metadata Preservation**: Keep original EXIF data
- **Format Conversion**: Automatic format conversion options
- **Backup Settings**: Backup configuration and indexes

---

## Troubleshooting

### Common Issues

#### Application Won't Start
1. Check system requirements are met
2. Ensure sufficient disk space (2GB minimum)
3. Try running as administrator (Windows) or with elevated permissions
4. Check system logs for error messages

#### Photos Not Appearing in Search
1. Verify photo directories are correctly added in Settings
2. Check if indexing is complete (see status bar)
3. Ensure file formats are supported (JPEG, PNG, TIFF, RAW)
4. Try refreshing the index: Settings → Advanced → Rebuild Index

#### Slow Performance
1. Check available RAM and disk space
2. Reduce thumbnail quality in Settings
3. Limit concurrent processing in Performance settings
4. Close other resource-intensive applications
5. Consider upgrading hardware for large photo collections

#### Search Results Inaccurate
1. Allow time for complete indexing of all photos
2. Update search terms - try more specific descriptions
3. Use multiple search terms for better results
4. Check if AI features are enabled in Settings

### Getting Help
- **Built-in Help**: Help menu → User Guide
- **Log Files**: Help → Open Log Folder (for technical support)
- **Report Issues**: Help → Report Bug (opens issue tracker)
- **Community**: Access community forums and documentation

### System Logs
Log files are stored in:
- **Windows**: `%APPDATA%\PhotoSearch\logs`
- **macOS**: `~/Library/Logs/PhotoSearch`
- **Linux**: `~/.local/share/PhotoSearch/logs`

---

## Privacy & Security

### Local Processing
Photo Search & Navigation is designed with privacy as a core principle:

- **No Cloud Processing**: All AI analysis happens on your computer
- **No Data Upload**: Your photos never leave your device
- **Offline Operation**: Works completely offline
- **Local Storage**: All indexes and metadata stored locally

### Data Storage
The application stores the following data locally:

#### Photo Metadata
- Thumbnails for fast display
- EXIF data extracted from photos
- AI-generated descriptions and tags
- User-added tags and ratings

#### AI Models
- Image recognition models (downloaded once)
- Face recognition models (if enabled)
- OCR text recognition models
- Natural language processing models

#### Application Data
- User settings and preferences
- Search history (optional, can be disabled)
- Application logs for troubleshooting

### Privacy Controls
- **Disable Face Recognition**: Completely disable face detection
- **Clear Search History**: Remove all search history
- **Export Data**: Export your metadata and settings
- **Data Deletion**: Completely remove all application data

### Security Features
- **No Network Access**: Application can run completely offline
- **File Permissions**: Only accesses directories you explicitly add
- **Secure Storage**: Application data encrypted at rest
- **No Analytics**: No usage tracking or analytics collection

### Data Portability
- Export settings and metadata to JSON format
- Backup and restore configuration
- Move installation to different computers
- Open format for future compatibility

---

## Advanced Features

### Command Line Interface
For power users, Photo Search includes CLI tools:

```bash
# Search from command line
photo-search search "vacation photos"

# Bulk operations
photo-search tag --add "vacation" --path "/Photos/2023"

# Export operations
photo-search export --format json --output metadata.json
```

### API Integration
Local REST API for integration with other tools:
- **Search API**: Programmatic search capabilities
- **Metadata API**: Access photo metadata
- **Import API**: Automate photo import workflows

### Scripting and Automation
- **Watch Folders**: Automatic processing of new photos
- **Batch Processing**: Custom scripts for bulk operations
- **Scheduled Tasks**: Automatic maintenance and optimization

---

## Appendix

### Supported File Formats
- **Images**: JPEG, PNG, TIFF, BMP, GIF, WebP
- **RAW Formats**: CR2, NEF, ARW, DNG, RAF, ORF
- **Video**: MP4, MOV, AVI (basic support)

### Keyboard Shortcuts Reference
| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Search | Ctrl + F | Cmd + F |
| Open Photo | Enter | Enter |
| Delete | Delete | Delete |
| Select All | Ctrl + A | Cmd + A |
| Copy | Ctrl + C | Cmd + C |
| Show in Folder | Ctrl + D | Cmd + D |
| Fullscreen | F11 | Ctrl + Cmd + F |
| Settings | Ctrl + , | Cmd + , |

### Performance Recommendations

#### For Large Collections (50,000+ photos):
- 16GB+ RAM recommended
- SSD storage for application and cache
- Dedicated graphics card (optional but helpful)
- Regular index optimization

#### For Slow Computers:
- Reduce thumbnail quality
- Disable real-time processing
- Process photos during off-hours
- Increase cache cleanup frequency

---

*This user manual covers version 1.0 of Photo Search & Navigation. For the latest updates and features, check the application's Help menu or visit our documentation website.*