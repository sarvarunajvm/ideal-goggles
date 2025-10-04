# Quickstart Guide: Ideal Goggles

## Prerequisites

### System Requirements
- **Operating System**: macOS 11+, Windows 10+, Linux (Ubuntu 20.04+)
- **Hardware**: Intel i5 or equivalent (4+ cores), 16GB RAM, SSD recommended
- **Storage**: 10GB free space for application and cache
- **Display**: 1920x1080 minimum resolution for optimal UX

### Sample Data Setup
```bash
# Create test photo library structure
mkdir -p ~/test-photos/2023/weddings/smith-johnson
mkdir -p ~/test-photos/2023/portraits/corporate
mkdir -p ~/test-photos/2024/events/birthday

# Copy sample photos (provided in test dataset)
# Includes photos with text, faces, and various EXIF data
```

## Installation and First Launch

### 1. Application Installation
```bash
# Download and run signed installer
# Windows: ideal-goggles-v1.0.0-setup.exe
# macOS: ideal-goggles-v1.0.0.dmg

# Verify installation
ideal-goggles --version
# Expected: Ideal Goggles v1.0.0
```

### 2. Initial Configuration
1. **Launch Application**
   - Application opens to setup wizard
   - Accept privacy policy and face search consent prompt

2. **Configure Root Folders**
   ```
   Settings → Folder Management → Add Root Folder
   Select: ~/test-photos
   Verify: Folder appears in configuration list
   ```

3. **Start Initial Indexing**
   ```
   Dashboard → Start Indexing
   Monitor progress: Discovery → Metadata → OCR → Embeddings
   Expected completion: ~5 minutes for 1000 test photos
   ```

## Core Feature Validation

### Test Scenario 1: Text Search Functionality
**Objective**: Verify text search across filenames, folders, and OCR content

**Steps**:
1. Enter search query: `"wedding smith 2023"`
2. Verify results display within 2 seconds
3. Check thumbnail grid shows relevant photos
4. Verify badges indicate match types (filename, OCR)

**Expected Results**:
- Photos from `/2023/weddings/smith-johnson/` appear in results
- OCR hits from invitation photos show [OCR] badge
- Results sorted by relevance score
- Metadata shows correct folder paths and dates

### Test Scenario 2: Date Range Filtering
**Objective**: Verify date-based photo filtering

**Steps**:
1. Apply date filter: From `2023-01-01` To `2023-12-31`
2. Search for photos in date range
3. Verify only 2023 photos appear in results
4. Test edge cases: single day, invalid dates

**Expected Results**:
- Only photos with 2023 EXIF dates displayed
- Photos without EXIF dates excluded from filtered results
- Date picker handles invalid input gracefully

### Test Scenario 3: Reverse Image Search
**Objective**: Verify image-based search functionality

**Steps**:
1. Select "Search by Photo" mode
2. Drag and drop a cropped/scanned version of known photo
3. Wait for processing (max 5 seconds)
4. Verify original photo appears in top 10 results

**Expected Results**:
- Original digital photo ranked highly in results
- [Photo-Match] badge displayed on similar images
- Side-by-side view shows query image and results
- Confidence scores displayed for matches

### Test Scenario 4: Face Search (Optional Feature)
**Objective**: Verify face enrollment and search functionality

**Prerequisites**: Face search enabled in settings

**Steps**:
1. Navigate to People Management
2. Enroll new person: "John Smith"
3. Select 3-5 sample photos containing the person
4. Confirm enrollment creates face profile
5. Search for "John Smith" in main search
6. Verify photos containing the person appear

**Expected Results**:
- Face enrollment completes without errors
- Person appears in people list
- Face search returns photos with [Face] badge
- Manual verification option available for results

### Test Scenario 5: Navigation and File Access
**Objective**: Verify photo opening and file exploration

**Steps**:
1. Perform any search to get results
2. Double-click thumbnail to open photo
3. Right-click thumbnail → "Reveal in Folder"
4. Test keyboard navigation (arrows, Enter, Escape)

**Expected Results**:
- Photo opens in default system viewer
- File explorer opens with photo selected
- Keyboard navigation works smoothly
- Context menu appears on right-click

## Performance Validation

### Search Performance Test
```bash
# Load test with 50,000+ photos
# Measure response times
Text search: <2s for 95% of queries
Image search: <5s for 95% of queries
Memory usage: <512MB during normal operation
```

### Indexing Performance Test
```bash
# Measure indexing throughput
Expected: 100k photos/day on target hardware
Monitor: CPU usage, memory consumption
Verify: Graceful handling of interruptions
```

## Error Scenarios and Recovery

### Test Scenario 6: Corrupted Image Handling
**Objective**: Verify graceful handling of unreadable files

**Steps**:
1. Place corrupted image file in watched folder
2. Start indexing process
3. Monitor indexing log for warnings
4. Verify indexing continues with other files

**Expected Results**:
- Corrupted file skipped with warning
- Indexing process continues uninterrupted
- Error logged but not displayed to user
- Valid files processed normally

### Test Scenario 7: Drive Disconnection
**Objective**: Verify handling of missing storage drives

**Steps**:
1. Index photos from external drive
2. Safely eject drive during normal operation
3. Attempt search including photos from missing drive
4. Reconnect drive and verify recovery

**Expected Results**:
- Missing files show offline indicator
- Search continues with available photos
- Reconnection automatically resumes access
- No data corruption or application crashes

### Test Scenario 8: Large Library Stress Test
**Objective**: Verify performance with maximum supported library size

**Steps**:
1. Configure system with 1M+ photo library
2. Perform complete indexing
3. Test search performance under load
4. Monitor memory and CPU usage

**Expected Results**:
- Indexing completes within expected timeframe
- Search remains responsive under load
- Memory usage stays within limits
- UI remains interactive during heavy operations

## Integration Test Automation

### Automated Test Suite
```python
# Run complete integration test suite
pytest backend/tests/integration/
# Tests cover all quickstart scenarios
# Includes performance benchmarking
# Generates test report with metrics
```

### Continuous Validation
```bash
# Daily smoke tests
pnpm run test:integration
# Verifies core functionality
# Alerts on performance regressions
# Validates with fresh test data
```

## Success Criteria Verification

### Functional Requirements Validation
- [ ] FR-001: Text search across all content types ✓
- [ ] FR-002: Date range filtering functional ✓
- [ ] FR-003: Reverse image search operational ✓
- [ ] FR-004: Face search with enrollment ✓
- [ ] FR-005: Performance targets met ✓
- [ ] FR-006-010: Navigation features complete ✓
- [ ] FR-011-017: Indexing capabilities verified ✓
- [ ] FR-018-020: Privacy and security confirmed ✓

### Performance Standards Met
- [ ] <2s text search response time ✓
- [ ] <5s image search response time ✓
- [ ] 1M photo library support ✓
- [ ] <512MB memory usage ✓
- [ ] 99%+ indexing coverage ✓

### User Experience Validation
- [ ] Zero-learning-curve for basic search ✓
- [ ] Intuitive interface with progressive disclosure ✓
- [ ] Clear visual indicators for match types ✓
- [ ] Smooth keyboard and mouse navigation ✓
- [ ] Graceful error handling and recovery ✓

## Troubleshooting Guide

### Common Issues and Solutions

**Slow Indexing Performance**:
- Check available disk space (need 10%+ free)
- Verify SSD vs HDD performance impact
- Monitor CPU usage during OCR/embedding phases

**Search Returns No Results**:
- Verify indexing completed successfully
- Check search syntax and filters
- Confirm photos in configured root folders

**Face Search Not Working**:
- Verify face search enabled in settings
- Check person enrollment with quality photos
- Confirm adequate lighting in sample images

**Application Won't Start**:
- Check Python backend service status
- Verify port 5555 not in use by other apps
- Review application logs for errors

---

## UX Enhancement Scenarios (v1.0 Market-Ready)

### Scenario 7: First-Run Onboarding

**Steps**:
1. Double-click installer to install Ideal Goggles
2. Launch app for the first time
3. Onboarding wizard appears automatically
4. Step 1: Welcome screen explains app features (30 seconds read)
5. Step 2: Click "Add Photo Folder" → select folder with 500 wedding photos
6. Step 3: Review selected folder, click "Start Indexing"
7. Progress bar shows indexing phases (Scanning → Thumbnails → Embeddings → Tagging)
8. Step 4: Indexing completes, shows summary ("500 photos indexed, 3 faces detected")
9. Click "Finish" → lands on SearchPage with 500 photos visible

**Expected Results**:
- ✅ Onboarding wizard appears on first launch (not on subsequent launches)
- ✅ Folder picker uses native OS dialog
- ✅ Indexing progress shows current phase and percentage
- ✅ Indexing completes in <2 minutes for 500 photos
- ✅ App lands on SearchPage with photos immediately visible
- ✅ Settings page has "Reset Onboarding" button (for testing)

**Performance**: Onboarding wizard load <500ms, indexing ≥250 photos/min

---

### Scenario 8: Full-Screen Photo Viewing with Lightbox

**Steps**:
1. Open SearchPage with 50 photos visible
2. Click on 5th photo thumbnail
3. Lightbox opens with photo in full-screen
4. Press `→` (right arrow) 3 times → navigates to 8th photo
5. Press `←` (left arrow) 1 time → navigates back to 7th photo
6. Press `i` or `Space` → metadata overlay appears (EXIF, tags, location)
7. Click metadata overlay → it stays visible
8. Press `i` or `Space` again → metadata overlay hides
9. Press `Esc` → lightbox closes, returns to SearchPage grid

**Expected Results**:
- ✅ Lightbox opens instantly (<100ms) with smooth zoom animation from thumbnail
- ✅ Photo switch time <100ms with smooth crossfade transition
- ✅ Keyboard shortcuts work: `←/→` (nav), `Esc` (close), `Space`/`i` (metadata)
- ✅ Metadata overlay shows: filename, size, EXIF (camera, lens, ISO, aperture, date), tags, location
- ✅ Preloading: Next/previous photos load in background (no delay when navigating)
- ✅ Closing lightbox returns to exact scroll position on grid
- ✅ Focus trap: Tab key cycles through lightbox controls only
- ✅ Screen reader announces current photo (e.g., "Photo 7 of 50")

**Performance**: Lightbox open <100ms, photo switch <100ms, 60fps animations

---

### Scenario 9: Batch Export Operations

**Steps**:
1. Open SearchPage with 100 photos
2. Click "Select" button in toolbar → enters selection mode
3. Click on 10 photo thumbnails → each gets checkmark overlay
4. Click 5th photo while holding `Shift` → selects range from last clicked to 5th (total 15 selected)
5. Click "Select All" button → all 100 photos selected
6. Click "Deselect All" → all photos deselected
7. Re-select 50 photos manually
8. Click "Export" button in batch actions toolbar
9. Native folder picker appears → select destination: `~/Desktop/Export`
10. Export dialog shows progress: "Exporting 50 photos... 25 of 50 (50%)"
11. Export completes → notification appears: "50 photos exported successfully"
12. Open `~/Desktop/Export` folder → verify 50 photos present with original filenames

**Expected Results**:
- ✅ Selection mode toggles on/off with "Select" button
- ✅ Checkmark overlay appears on selected thumbnails
- ✅ Selection counter shows "50 selected" in toolbar
- ✅ Shift+Click range selection works correctly
- ✅ "Select All" button selects all photos in current view
- ✅ Export progress dialog updates in real-time (every 100ms)
- ✅ Export completes in <30 seconds for 50 photos
- ✅ Exported photos preserve original filenames and metadata
- ✅ Selection mode exits automatically after export completes

**Performance**: Selection UI lag-free, export ≥100 photos/min (50 photos in <30s)

---

### Scenario 10: Virtual Scrolling Performance with Large Library

**Steps**:
1. Index 50,000 test photos (can use duplicate small files for testing)
2. Open SearchPage → verify initial load shows first 100 thumbnails
3. Scroll down rapidly using mouse wheel for 30 seconds
4. Observe scrolling smoothness (should be 60fps, no stuttering)
5. Jump to middle of library using scrollbar thumb drag
6. Verify thumbnails load within 1 second of stopping scroll
7. Search for "sunset" → results filter to 500 photos
8. Scroll through filtered results → verify smooth performance
9. Clear search → return to full 50K library view
10. Scroll to bottom of library → verify last photos load correctly

**Expected Results**:
- ✅ Initial page load <2 seconds (first 100 thumbnails rendered)
- ✅ Scrolling framerate: 60fps (no frame drops)
- ✅ Memory usage: <500MB with 50K photos library
- ✅ Thumbnail lazy loading: Visible within 500ms of entering viewport
- ✅ Overscan: 5 rows above/below viewport preloaded
- ✅ Placeholder skeletons shown while thumbnails load
- ✅ Jump scrolling (scrollbar drag) works smoothly
- ✅ Filtering to 500 results updates grid instantly (<200ms)
- ✅ DevTools Performance: 60fps average, no long tasks >50ms, CLS <0.1

**Performance**: Initial render <2s, 60fps scrolling, <500MB memory, <500ms thumbnail load

---

### Scenario 11: Desktop Installer & Auto-Update

**macOS Installation**:
1. Download `Ideal-Goggles-1.0.0.dmg` from GitHub Releases
2. Double-click DMG file → verify it mounts without Gatekeeper warning
3. Drag app icon to Applications folder
4. Eject DMG → open Applications folder
5. Double-click Ideal Goggles.app → verify it launches without security warning
6. Verify code signing: `codesign -dv --verbose=4 /Applications/Ideal\ Goggles.app`
7. Should show: "Authority=Developer ID Application: [Your Name]"

**Windows Installation**:
1. Download `Ideal-Goggles-Setup-1.0.0.exe` from GitHub Releases
2. Double-click installer → verify Windows SmartScreen doesn't block (if code-signed)
3. Follow installer wizard → install to `C:\Program Files\Ideal Goggles`
4. Verify Start Menu shortcut created
5. Launch app from Start Menu → verify it runs correctly

**Auto-Update Flow**:
1. Simulate new version available (v1.0.1 released on GitHub)
2. Launch app with existing v1.0.0 installed
3. After 30 seconds, notification appears: "Update available (v1.0.1) - Download in background?"
4. Click "Yes" → download starts silently
5. Progress notification: "Downloading update... 50% (5MB of 10MB)"
6. Download completes → new notification: "Update ready to install. Restart now?"
7. Click "Restart" → app quits and relaunches with v1.0.1
8. Verify app version in About dialog: v1.0.1

**Expected Results**:
- ✅ macOS: DMG installer mounts without warning, app is notarized and code-signed
- ✅ Windows: Installer is Authenticode-signed, no SmartScreen warning
- ✅ Linux: AppImage runs without installation, .deb installs cleanly
- ✅ Installer size: <150MB compressed
- ✅ Installed size: <300MB
- ✅ First launch after install: <3 seconds
- ✅ Auto-update check: Happens once per day, doesn't block UI
- ✅ Delta update: Only downloads changed files (v1.0.0→v1.0.1 delta <10MB)
- ✅ Update fails gracefully: If download interrupted, retry or skip available
- ✅ Settings page has "Check for Updates" manual button
- ✅ Settings page has "Disable Auto-Updates" toggle

**Code Signing Verification**:
```bash
# macOS
codesign -dv --verbose=4 /Applications/Ideal\ Goggles.app
spctl -a -vv /Applications/Ideal\ Goggles.app

# Windows (PowerShell)
Get-AuthenticodeSignature "C:\Program Files\Ideal Goggles\Ideal Goggles.exe"
```

**Performance**: Installer <150MB, install time <30s, first launch <3s, background updates

---

## Acceptance Criteria

### Core Features (Scenarios 1-6):
- [ ] Text search returns results in <2 seconds
- [ ] Semantic search returns results in <5 seconds
- [ ] Face search works with enrolled persons
- [ ] Reverse image search finds similar photos
- [ ] Photos open in default viewer on double-click
- [ ] "Reveal in folder" works on all platforms

### UX Enhancements (Scenarios 7-11):
- [ ] Onboarding wizard guides new users through setup
- [ ] Lightbox opens in <100ms with 60fps animations
- [ ] Virtual scrolling maintains 60fps with 50K+ photos
- [ ] Batch export: ≥100 photos/min
- [ ] Code-signed installers for all platforms
- [ ] Auto-update downloads delta updates in background

### Cross-Platform Testing:
- [ ] All scenarios pass on macOS
- [ ] All scenarios pass on Windows
- [ ] All scenarios pass on Linux (Ubuntu 20.04+)

---

## Next Steps

After successful quickstart validation:
1. **Production Deployment**: Move to actual photo library
2. **User Training**: Familiarize studio operators with features
3. **Performance Tuning**: Optimize for specific hardware/usage
4. **Backup Strategy**: Configure regular database backups
5. **Update Management**: Configure auto-update preferences
