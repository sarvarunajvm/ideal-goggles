# Quickstart Guide: Ideal Goggles

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+ (primary), macOS 11+ (v1.1)
- **Hardware**: Intel i5 or equivalent, 16GB RAM, SSD recommended
- **Storage**: 10GB free space for application and cache

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

## Next Steps

After successful quickstart validation:
1. **Production Deployment**: Move to actual photo library
2. **User Training**: Familiarize studio operators with features
3. **Performance Tuning**: Optimize for specific hardware/usage
4. **Backup Strategy**: Configure regular database backups
5. **Monitoring Setup**: Enable telemetry for usage insights
