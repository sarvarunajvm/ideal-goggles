# Quickstart: Smart Collections Feature

## User Acceptance Test

This quickstart validates all primary user scenarios from the specification.

### Prerequisites
- Ideal Goggles app running (backend + frontend)
- Sample dataset: 50+ photos from a wedding event

### Scenario 1: Auto-Tagging During Indexing

**Steps**:
1. Open Settings → Indexing
2. Enable "Auto-generate tags"
3. Add folder with 50 wedding photos
4. Click "Start Indexing"

**Expected Results**:
- ✅ Progress shows "Phase 4: Auto-tagging"
- ✅ Each photo receives 3-10 tags (bride, ceremony, outdoor, etc.)
- ✅ Tags visible in photo details panel
- ✅ Tag confidence scores shown (e.g., "sunset: 92%")
- ✅ Indexing completes within 30 seconds for 50 photos

### Scenario 2: Event Detection

**Steps**:
1. Navigate to Collections page
2. Verify "Wedding Event - 2024-06-15" collection appears
3. Click on event to view photos
4. Check sub-collections (Ceremony, Reception, Candids)

**Expected Results**:
- ✅ Event auto-created with all 50 photos
- ✅ Hierarchical sub-events detected (if time gaps > 2 hours)
- ✅ Event name includes date
- ✅ Photo count badge shows "50 photos"
- ✅ Collections page loads in <2 seconds

### Scenario 3: Tag-Based Search

**Steps**:
1. Go to Search page
2. Search for "sunset ceremony"
3. Verify results

**Expected Results**:
- ✅ Only photos tagged with BOTH "sunset" AND "ceremony" appear
- ✅ Results ranked by relevance score
- ✅ Tag badges shown on each result thumbnail
- ✅ Search completes in <500ms

### Scenario 4: Duplicate Detection

**Steps**:
1. Open Settings → Collections
2. Click "Detect Duplicates"
3. Wait for detection to complete
4. Navigate to Duplicates tab

**Expected Results**:
- ✅ Duplicate groups listed with similarity scores
- ✅ Side-by-side comparison view
- ✅ "Recommended" badge on best quality photo
- ✅ "Delete others" button available
- ✅ Detection completes in <10 seconds for 50 photos

### Scenario 5: Create Smart Album

**Steps**:
1. Collections page → "New Smart Album"
2. Name: "Outdoor Sunset Photos 2024"
3. Add rules:
   - Tag contains "sunset"
   - AND Tag contains "outdoor"
   - AND Date between 2024-01-01 and 2024-12-31
   - NOT Tag contains "people"
4. Save

**Expected Results**:
- ✅ Smart album appears in Collections sidebar
- ✅ Photo count updates dynamically
- ✅ Opening album shows all matching photos
- ✅ Adding new matching photo auto-includes in album
- ✅ Album loads in <1 second

### Scenario 6: Manual Tag Editing

**Steps**:
1. Select any photo
2. View auto-generated tags
3. Click "Edit Tags"
4. Add custom tag "first dance"
5. Remove incorrect auto tag
6. Save

**Expected Results**:
- ✅ Manual tag added with 100% confidence
- ✅ Auto tag removed successfully
- ✅ Changes reflected immediately in search
- ✅ Tag edit history preserved

## Performance Benchmarks

Run these tests to verify performance targets:

```bash
# Auto-tagging speed
pytest backend/tests/performance/test_auto_tagging_speed.py
# Expected: 100 photos/min (600ms per photo)

# Event detection
pytest backend/tests/performance/test_event_detection_scale.py
# Expected: <5s for 10K photos

# Duplicate detection
pytest backend/tests/performance/test_duplicate_detection.py
# Expected: <30s for 1K photos

# Collections page load
pytest func_tests/e2e/test_collections_performance.py
# Expected: <2s initial render
```

## Acceptance Criteria

- [  ] All 6 scenarios pass without errors
- [  ] Performance benchmarks meet targets
- [  ] Zero data loss (original photos untouched)
- [  ] No network calls during operations
- [  ] User can disable features independently

## Sign-off

- [ ] Product Owner reviewed and approved
- [ ] QA tested all scenarios
- [ ] Performance validated
- [ ] Constitution compliance verified
