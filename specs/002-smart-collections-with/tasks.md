# Tasks: Smart Collections with Auto-Tagging and Event Detection

**Input**: Design documents from `/Users/sarkalimuthu/WebstormProjects/ideal-goggles/specs/002-smart-collections-with/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**Branch**: `002-smart-collections-with`

---

## Git Worktree Strategy

**IMPORTANT**: All parallel tasks use git worktrees to avoid file conflicts.

### Worktree Setup Pattern
```bash
# Main branch stays at: /Users/sarkalimuthu/WebstormProjects/ideal-goggles
# Create worktrees for parallel tasks:
git worktree add ../ideal-goggles-task-T004 002-smart-collections-with
git worktree add ../ideal-goggles-task-T005 002-smart-collections-with
# ... one worktree per parallel task
```

### Task Execution in Worktrees
Each [P] task runs in its own worktree directory to prevent conflicts. After task completion, changes are committed in the worktree, then merged back to main worktree.

### Cleanup After Parallel Batch
```bash
# After completing parallel tasks T004-T024:
git worktree remove ../ideal-goggles-task-T004
git worktree remove ../ideal-goggles-task-T005
# ... remove all worktrees
git worktree prune
```

---

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel using git worktrees (different files, no dependencies)
- File paths are absolute for worktree compatibility

---

## Phase 3.1: Setup & Dependencies

- [ ] **T001** Create database migration for new tables
  **File**: `backend/src/db/migrations/002_smart_collections.py`
  **Details**: Create tags, photo_tags, events, event_members, collections, collection_members, smart_albums, duplicate_groups, duplicate_group_members tables + tags_fts virtual table. Include indexes and triggers per data-model.md.
  **Dependencies**: None
  **Worktree**: No (sequential setup task)

- [ ] **T002** Install new Python dependencies
  **File**: `backend/pyproject.toml`
  **Details**: Add scikit-learn>=1.5.0, imagehash>=4.3.0 to dependencies. Run `pip install -e ".[dev]"` to verify.
  **Dependencies**: None
  **Worktree**: No (modifies shared config)

- [ ] **T003** Install new frontend dependencies
  **File**: `package.json`
  **Details**: Add @tanstack/react-query@5.x to dependencies. Run `pnpm install` to verify.
  **Dependencies**: None
  **Worktree**: No (modifies shared config)

---

## Phase 3.2: Database Models (TDD: Models Before Tests)

- [ ] **T004** [P] Create Tag model
  **File**: `backend/src/models/tag.py`
  **Details**: SQLAlchemy model for tags table with name, source_type, usage_count fields. Include from_db_row() and to_dict() methods.
  **Dependencies**: T001 (migration created)
  **Worktree**: `../ideal-goggles-task-T004`

- [ ] **T005** [P] Create PhotoTag model
  **File**: `backend/src/models/photo_tag.py`
  **Details**: Junction table model for photo_tags with photo_id, tag_id, confidence, source fields.
  **Dependencies**: T001
  **Worktree**: `../ideal-goggles-task-T005`

- [ ] **T006** [P] Create Event model
  **File**: `backend/src/models/event.py`
  **Details**: Model for events table with name, event_type, start_dt, end_dt, parent_event_id, photo_count. Support hierarchical events.
  **Dependencies**: T001
  **Worktree**: `../ideal-goggles-task-T006`

- [ ] **T007** [P] Create Collection model
  **File**: `backend/src/models/collection.py`
  **Details**: Model for collections with name, collection_type (manual/auto_event/smart_album), cover_photo_id, photo_count.
  **Dependencies**: T001
  **Worktree**: `../ideal-goggles-task-T007`

- [ ] **T008** [P] Create SmartAlbum model
  **File**: `backend/src/models/smart_album.py`
  **Details**: Model with rules JSON field, last_evaluated_at. Include JSON schema validation for rules.
  **Dependencies**: T001
  **Worktree**: `../ideal-goggles-task-T008`

- [ ] **T009** [P] Create DuplicateGroup model
  **File**: `backend/src/models/duplicate_group.py`
  **Details**: Model with recommended_photo_id, avg_similarity, status (pending/reviewed/resolved).
  **Dependencies**: T001
  **Worktree**: `../ideal-goggles-task-T009`

---

## Phase 3.3: Contract Tests (TDD: Tests Before Implementation) ⚠️ MUST COMPLETE BEFORE 3.4

- [ ] **T010** [P] Contract test: GET /api/tags
  **File**: `backend/tests/contract/test_tags_list.py`
  **Details**: Test list tags endpoint with source filter, min_usage filter, pagination. Assert 200 response with tags array.
  **Dependencies**: T004 (Tag model exists)
  **Worktree**: `../ideal-goggles-task-T010`

- [ ] **T011** [P] Contract test: POST /api/tags
  **File**: `backend/tests/contract/test_tags_create.py`
  **Details**: Test create manual tag. Assert 201 on success, 409 if duplicate name.
  **Dependencies**: T004
  **Worktree**: `../ideal-goggles-task-T011`

- [ ] **T012** [P] Contract test: DELETE /api/tags/{id}
  **File**: `backend/tests/contract/test_tags_delete.py`
  **Details**: Test delete tag (cascades to photo_tags). Assert 204 on success, 404 if not found.
  **Dependencies**: T004, T005
  **Worktree**: `../ideal-goggles-task-T012`

- [ ] **T013** [P] Contract test: GET /api/photos/{id}/tags
  **File**: `backend/tests/contract/test_photo_tags_get.py`
  **Details**: Test get photo tags with confidence scores. Assert 200 with array of PhotoTag objects.
  **Dependencies**: T005
  **Worktree**: `../ideal-goggles-task-T013`

- [ ] **T014** [P] Contract test: POST /api/photos/{id}/tags
  **File**: `backend/tests/contract/test_photo_tags_add.py`
  **Details**: Test add manual tag to photo. Assert 201 on success, 409 if already tagged.
  **Dependencies**: T005
  **Worktree**: `../ideal-goggles-task-T014`

- [ ] **T015** [P] Contract test: DELETE /api/photos/{id}/tags
  **File**: `backend/tests/contract/test_photo_tags_remove.py`
  **Details**: Test remove tag from photo. Assert 204 on success.
  **Dependencies**: T005
  **Worktree**: `../ideal-goggles-task-T015`

- [ ] **T016** [P] Contract test: GET /api/events
  **File**: `backend/tests/contract/test_events_list.py`
  **Details**: Test list events. Assert 200 with events array sorted by start_dt desc.
  **Dependencies**: T006
  **Worktree**: `../ideal-goggles-task-T016`

- [ ] **T017** [P] Contract test: POST /api/events/detect
  **File**: `backend/tests/contract/test_events_detect.py`
  **Details**: Test trigger event detection. Assert 202 (accepted), returns job_id for status polling.
  **Dependencies**: T006
  **Worktree**: `../ideal-goggles-task-T017`

- [ ] **T018** [P] Contract test: PUT /api/events/{id}
  **File**: `backend/tests/contract/test_events_update.py`
  **Details**: Test rename event, merge events, split event. Assert 200 with updated event.
  **Dependencies**: T006
  **Worktree**: `../ideal-goggles-task-T018`

- [ ] **T019** [P] Contract test: GET /api/collections
  **File**: `backend/tests/contract/test_collections_list.py`
  **Details**: Test list collections with type filter. Assert 200 with collections array.
  **Dependencies**: T007
  **Worktree**: `../ideal-goggles-task-T019`

- [ ] **T020** [P] Contract test: POST /api/collections
  **File**: `backend/tests/contract/test_collections_create.py`
  **Details**: Test create manual collection. Assert 201 with new collection object.
  **Dependencies**: T007
  **Worktree**: `../ideal-goggles-task-T020`

- [ ] **T021** [P] Contract test: POST /api/collections/{id}/photos
  **File**: `backend/tests/contract/test_collections_add_photo.py`
  **Details**: Test add photo to collection. Assert 201 on success.
  **Dependencies**: T007
  **Worktree**: `../ideal-goggles-task-T021`

- [ ] **T022** [P] Contract test: GET /api/smart-albums
  **File**: `backend/tests/contract/test_smart_albums_list.py`
  **Details**: Test list smart albums with rule preview. Assert 200 with dynamic photo counts.
  **Dependencies**: T008
  **Worktree**: `../ideal-goggles-task-T022`

- [ ] **T023** [P] Contract test: POST /api/smart-albums
  **File**: `backend/tests/contract/test_smart_albums_create.py`
  **Details**: Test create smart album with JSON rules. Assert 201, validate rules schema.
  **Dependencies**: T008
  **Worktree**: `../ideal-goggles-task-T023`

- [ ] **T024** [P] Contract test: GET /api/duplicates
  **File**: `backend/tests/contract/test_duplicates_list.py`
  **Details**: Test list duplicate groups with status filter. Assert 200 with groups array.
  **Dependencies**: T009
  **Worktree**: `../ideal-goggles-task-T024`

---

## Phase 3.4: Workers (Core Logic)

- [ ] **T025** [P] Create AutoTaggingWorker
  **File**: `backend/src/workers/auto_tagging_worker.py`
  **Details**: Implement CLIP zero-shot classification per research.md. Use existing CLIP model, pre-defined tag vocabulary (50+ tags). Generate 3-10 tags per photo with confidence scores. Target 600ms/photo.
  **Dependencies**: T004, T005 (models exist)
  **Worktree**: `../ideal-goggles-task-T025`

- [ ] **T026** [P] Create EventDetectionWorker
  **File**: `backend/src/workers/event_detection_worker.py`
  **Details**: Implement DBSCAN temporal clustering per research.md. Use scikit-learn, eps=4 hours (configurable), min_samples=3. Name events "[Type] - [Date]". Target <5s for 10K photos.
  **Dependencies**: T006 (Event model)
  **Worktree**: `../ideal-goggles-task-T026`

- [ ] **T027** [P] Create DuplicateDetectionWorker
  **File**: `backend/src/workers/duplicate_detection_worker.py`
  **Details**: Two-stage detection per research.md: (1) perceptual hashing with imagehash, (2) CLIP embedding similarity. Threshold: phash distance <=8, embedding similarity >=0.85. Recommend best photo by resolution × file size. Target <30s for 1K photos.
  **Dependencies**: T009 (DuplicateGroup model)
  **Worktree**: `../ideal-goggles-task-T027`

- [ ] **T028** [P] Create SmartAlbumEvaluator
  **File**: `backend/src/services/smart_album_evaluator.py`
  **Details**: Parse JSON rules AST, compile to SQL WHERE clause. Support operators: contains, not_contains, =, !=, <, <=, >, >=, between. Support fields: tags, shot_dt, location, camera_make, lens, iso, aperture, file_size. Cache results for 5 minutes.
  **Dependencies**: T008 (SmartAlbum model)
  **Worktree**: `../ideal-goggles-task-T028`

---

## Phase 3.5: API Implementation (ONLY after contract tests written)

### Tags API Router

- [ ] **T029** Implement GET /api/tags
  **File**: `backend/src/api/tags.py` (create new router)
  **Details**: List tags with optional source filter, min_usage filter, limit. Query tags table with indexes. Return 200 with tags array.
  **Dependencies**: T010 (contract test exists and fails)
  **Worktree**: No (sequential API implementation to avoid router conflicts)

- [ ] **T030** Implement POST /api/tags
  **File**: `backend/src/api/tags.py` (same router)
  **Details**: Create manual tag. Validate name (2-50 chars, alphanumeric). Check uniqueness, insert into tags table. Return 201 or 409.
  **Dependencies**: T011 (contract test), T029 (router exists)
  **Worktree**: No

- [ ] **T031** Implement DELETE /api/tags/{id}
  **File**: `backend/src/api/tags.py`
  **Details**: Delete tag, cascade to photo_tags via foreign key. Return 204 or 404.
  **Dependencies**: T012 (contract test), T030
  **Worktree**: No

- [ ] **T032** Implement GET /api/photos/{id}/tags
  **File**: `backend/src/api/tags.py`
  **Details**: Get all tags for photo. Join photo_tags + tags tables. Return 200 with array including confidence scores.
  **Dependencies**: T013 (contract test), T031
  **Worktree**: No

- [ ] **T033** Implement POST /api/photos/{id}/tags
  **File**: `backend/src/api/tags.py`
  **Details**: Add manual tag to photo. Create tag if doesn't exist, insert photo_tags row with confidence=1.0, source='manual'. Return 201 or 409 if already tagged.
  **Dependencies**: T014 (contract test), T032
  **Worktree**: No

- [ ] **T034** Implement DELETE /api/photos/{id}/tags
  **File**: `backend/src/api/tags.py`
  **Details**: Remove tag from photo. Delete photo_tags row. Update tag usage_count via trigger. Return 204.
  **Dependencies**: T015 (contract test), T033
  **Worktree**: No

### Events API Router

- [ ] **T035** Implement GET /api/events
  **File**: `backend/src/api/events.py` (create new router)
  **Details**: List events sorted by start_dt desc. Support pagination. Return 200 with events array including photo_count.
  **Dependencies**: T016 (contract test)
  **Worktree**: No

- [ ] **T036** Implement POST /api/events/detect
  **File**: `backend/src/api/events.py`
  **Details**: Trigger async event detection using EventDetectionWorker (T026). Return 202 with job_id for polling status. Use background task queue.
  **Dependencies**: T017 (contract test), T026 (worker exists), T035
  **Worktree**: No

- [ ] **T037** Implement PUT /api/events/{id}
  **File**: `backend/src/api/events.py`
  **Details**: Support rename, merge multiple events, split event. Validate operations, update events + event_members tables. Return 200 with updated event.
  **Dependencies**: T018 (contract test), T036
  **Worktree**: No

- [ ] **T038** Implement DELETE /api/events/{id}
  **File**: `backend/src/api/events.py`
  **Details**: Delete event and event_members. Set event_id to NULL for orphaned photos (soft delete). Return 204.
  **Dependencies**: T037
  **Worktree**: No

### Collections API Router

- [ ] **T039** Implement GET /api/collections
  **File**: `backend/src/api/collections.py` (create new router)
  **Details**: List collections with type filter (manual/auto_event/smart_album). Return 200 with photo_count for each.
  **Dependencies**: T019 (contract test)
  **Worktree**: No

- [ ] **T040** Implement POST /api/collections
  **File**: `backend/src/api/collections.py`
  **Details**: Create manual collection. Validate name (1-100 chars, unique). Insert into collections table with type='manual'. Return 201.
  **Dependencies**: T020 (contract test), T039
  **Worktree**: No

- [ ] **T041** Implement POST /api/collections/{id}/photos
  **File**: `backend/src/api/collections.py`
  **Details**: Add photo to manual collection. Insert collection_members row with auto-incremented display_order. Return 201.
  **Dependencies**: T021 (contract test), T040
  **Worktree**: No

- [ ] **T042** Implement DELETE /api/collections/{id}/photos/{photo_id}
  **File**: `backend/src/api/collections.py`
  **Details**: Remove photo from collection. Delete collection_members row, update photo_count via trigger. Return 204.
  **Dependencies**: T041
  **Worktree**: No

### Smart Albums API Router

- [ ] **T043** Implement GET /api/smart-albums
  **File**: `backend/src/api/smart_albums.py` (create new router)
  **Details**: List smart albums. For each, evaluate rules using SmartAlbumEvaluator (T028) to get dynamic photo count. Cache results. Return 200.
  **Dependencies**: T022 (contract test), T028 (evaluator exists)
  **Worktree**: No

- [ ] **T044** Implement POST /api/smart-albums
  **File**: `backend/src/api/smart_albums.py`
  **Details**: Create smart album. Validate rules JSON schema. Create collection with type='smart_album', then smart_albums row. Return 201.
  **Dependencies**: T023 (contract test), T043
  **Worktree**: No

- [ ] **T045** Implement PUT /api/smart-albums/{id}/rules
  **File**: `backend/src/api/smart_albums.py`
  **Details**: Update smart album rules. Validate new rules, update smart_albums.rules JSON field. Invalidate cache. Return 200.
  **Dependencies**: T044
  **Worktree**: No

- [ ] **T046** Implement POST /api/smart-albums/{id}/evaluate
  **File**: `backend/src/api/smart_albums.py`
  **Details**: Force re-evaluation of smart album rules. Run SmartAlbumEvaluator, return photo count and sample results. Return 200.
  **Dependencies**: T045
  **Worktree**: No

### Duplicates API Router

- [ ] **T047** Implement GET /api/duplicates
  **File**: `backend/src/api/duplicates.py` (create new router)
  **Details**: List duplicate groups with status filter (pending/reviewed/resolved). Join duplicate_groups + duplicate_group_members. Return 200 with similarity scores.
  **Dependencies**: T024 (contract test)
  **Worktree**: No

- [ ] **T048** Implement POST /api/duplicates/detect
  **File**: `backend/src/api/duplicates.py`
  **Details**: Trigger async duplicate detection using DuplicateDetectionWorker (T027). Return 202 with job_id. Use background task queue.
  **Dependencies**: T027 (worker exists), T047
  **Worktree**: No

- [ ] **T049** Implement POST /api/duplicates/{id}/resolve
  **File**: `backend/src/api/duplicates.py`
  **Details**: Mark duplicate group as resolved. Update status field, optionally delete non-preferred photos. Return 200.
  **Dependencies**: T048
  **Worktree**: No

---

## Phase 3.6: Frontend Components

- [ ] **T050** [P] Create CollectionsPage component
  **File**: `frontend/src/pages/CollectionsPage.tsx`
  **Details**: Main collections view listing events, manual collections, smart albums. Use TanStack Query for data fetching. Show photo count badges, cover thumbnails. Grid layout with search/filter.
  **Dependencies**: T039, T043, T047 (APIs exist)
  **Worktree**: `../ideal-goggles-task-T050`

- [ ] **T051** [P] Create TagEditor component
  **File**: `frontend/src/components/TagEditor.tsx`
  **Details**: Inline tag editing for photos. Show auto/manual tags with confidence scores. Support add/remove tags. Use tags API (T032-T034).
  **Dependencies**: T032, T033, T034 (APIs exist)
  **Worktree**: `../ideal-goggles-task-T051`

- [ ] **T052** [P] Create SmartAlbumBuilder component
  **File**: `frontend/src/components/SmartAlbumBuilder.tsx`
  **Details**: Visual rule builder with drag-and-drop. Support AND/OR/NOT logic, field selectors (tags, date, metadata), operator dropdowns. Preview photo count live. Use smart albums API (T044-T046).
  **Dependencies**: T044, T045, T046 (APIs exist)
  **Worktree**: `../ideal-goggles-task-T052`

- [ ] **T053** [P] Create DuplicateReview component
  **File**: `frontend/src/components/DuplicateReview.tsx`
  **Details**: Side-by-side duplicate comparison. Show similarity scores, recommended photo badge. Support mark preferred, delete others, skip group. Use duplicates API (T047-T049).
  **Dependencies**: T047, T048, T049 (APIs exist)
  **Worktree**: `../ideal-goggles-task-T053`

- [ ] **T054** [P] Create EventDetailsView component
  **File**: `frontend/src/components/EventDetailsView.tsx`
  **Details**: Event photo grid with sub-event tabs. Support rename event, merge/split actions. Show timeline visualization. Use events API (T035-T038).
  **Dependencies**: T035, T037, T038 (APIs exist)
  **Worktree**: `../ideal-goggles-task-T054`

- [ ] **T055** Integrate tags into SearchPage
  **File**: `frontend/src/pages/SearchPage.tsx` (modify existing)
  **Details**: Add tag filter dropdown in search interface. Support multi-select tags with AND/OR logic. Show tag badges on result thumbnails. Use tags API (T029, T032).
  **Dependencies**: T050-T054 (components exist), T029, T032 (APIs exist)
  **Worktree**: No (modifies existing file, sequential)

- [ ] **T056** Create Collections navigation link
  **File**: `frontend/src/App.tsx` (modify existing)
  **Details**: Add "Collections" nav item to sidebar. Route to CollectionsPage (T050). Show badge with collection count.
  **Dependencies**: T055
  **Worktree**: No (modifies App.tsx, must be sequential)

---

## Phase 3.7: Integration with Existing Indexing

- [ ] **T057** Integrate auto-tagging into indexing pipeline
  **File**: `backend/src/api/indexing.py` (modify existing)
  **Details**: After Phase 4 (Embedding generation), call AutoTaggingWorker (T025) for batch tagging. Insert photo_tags rows with confidence scores. Update progress tracking.
  **Dependencies**: T025 (worker exists)
  **Worktree**: No (modifies critical indexing flow, sequential)

- [ ] **T058** Trigger event detection after indexing complete
  **File**: `backend/src/api/indexing.py` (modify existing)
  **Details**: After indexing finishes, automatically trigger EventDetectionWorker (T026) in background. Create events + event_members. Update collections table with auto_event collections.
  **Dependencies**: T026 (worker exists), T057
  **Worktree**: No

- [ ] **T059** Add Settings toggle for auto-tagging/events
  **File**: `frontend/src/pages/SettingsPage.tsx` (modify existing)
  **Details**: Add checkboxes to enable/disable auto-tagging, event detection, duplicate detection independently. Store preferences in localStorage. Show "Detect Duplicates" button.
  **Dependencies**: T056
  **Worktree**: No (modifies Settings, sequential)

---

## Phase 3.8: Integration Tests

- [ ] **T060** [P] Integration test: Auto-tagging flow
  **File**: `backend/tests/integration/test_auto_tagging_flow.py`
  **Details**: Index 10 test photos, verify tags generated with confidence scores. Assert FTS5 search works. Verify tag usage_count updated.
  **Dependencies**: T057 (auto-tagging integrated)
  **Worktree**: `../ideal-goggles-task-T060`

- [ ] **T061** [P] Integration test: Event detection
  **File**: `backend/tests/integration/test_event_detection.py`
  **Details**: Create 50 test photos with timestamps 4 hours apart. Run event detection, verify events created with correct photo grouping. Test hierarchical events.
  **Dependencies**: T058 (event detection integrated)
  **Worktree**: `../ideal-goggles-task-T061`

- [ ] **T062** [P] Integration test: Tag search with AND/OR
  **File**: `backend/tests/integration/test_tag_search.py`
  **Details**: Tag photos with "sunset", "beach", "people" combinations. Test FTS5 queries: "sunset beach", "sunset NOT people". Verify results accuracy.
  **Dependencies**: T060
  **Worktree**: `../ideal-goggles-task-T062`

- [ ] **T063** [P] Integration test: Smart album dynamic membership
  **File**: `backend/tests/integration/test_smart_albums.py`
  **Details**: Create smart album with rules. Add photos matching criteria, verify auto-inclusion. Modify rules, verify membership updates. Test cache invalidation.
  **Dependencies**: T044, T045, T046 (APIs exist)
  **Worktree**: `../ideal-goggles-task-T063`

- [ ] **T064** [P] Integration test: Duplicate detection accuracy
  **File**: `backend/tests/integration/test_duplicate_detection.py`
  **Details**: Create test set with 10 originals + 5 duplicates (slightly rotated/cropped). Run detection, verify 95%+ accuracy. Test phash + embedding stages.
  **Dependencies**: T048, T049 (APIs exist)
  **Worktree**: `../ideal-goggles-task-T064`

- [ ] **T065** [P] E2E test: Collections page load performance
  **File**: `func_tests/e2e/test_collections_performance.ts`
  **Details**: Create 100 collections with 10K photos. Measure CollectionsPage load time. Assert <2s initial render. Use Playwright performance API.
  **Dependencies**: T050 (CollectionsPage exists)
  **Worktree**: `../ideal-goggles-task-T065`

---

## Phase 3.9: Performance & Polish

- [ ] **T066** [P] Performance test: Auto-tagging throughput
  **File**: `backend/tests/performance/test_auto_tagging_speed.py`
  **Details**: Tag 100 test photos, measure time. Assert >=100 photos/min (600ms/photo target). Profile CLIP inference, identify bottlenecks.
  **Dependencies**: T060 (integration test passes)
  **Worktree**: `../ideal-goggles-task-T066`

- [ ] **T067** [P] Performance test: Event detection scale
  **File**: `backend/tests/performance/test_event_detection_scale.py`
  **Details**: Generate 10K test photos with random timestamps. Run DBSCAN clustering. Assert <5s execution time. Test memory usage <512MB.
  **Dependencies**: T061 (integration test passes)
  **Worktree**: `../ideal-goggles-task-T067`

- [ ] **T068** [P] Performance test: Duplicate detection
  **File**: `backend/tests/performance/test_duplicate_detection_perf.py`
  **Details**: Process 1K photos for duplicates. Assert <30s total time. Measure phash stage (<10s) vs embedding stage (<20s) separately.
  **Dependencies**: T064 (integration test passes)
  **Worktree**: `../ideal-goggles-task-T068`

- [ ] **T069** [P] Unit test: SmartAlbumEvaluator edge cases
  **File**: `backend/tests/unit/test_smart_album_evaluator.py`
  **Details**: Test rule compiler with complex nested AND/OR/NOT. Test invalid JSON, unsupported operators, SQL injection prevention. 100% code coverage.
  **Dependencies**: T028 (evaluator exists)
  **Worktree**: `../ideal-goggles-task-T069`

- [ ] **T070** [P] Frontend unit tests: TagEditor
  **File**: `frontend/src/components/__tests__/TagEditor.test.tsx`
  **Details**: Test add tag, remove tag, confidence score display. Mock API calls. Assert accessibility (ARIA labels, keyboard navigation).
  **Dependencies**: T051 (component exists)
  **Worktree**: `../ideal-goggles-task-T070`

- [ ] **T071** [P] Frontend unit tests: SmartAlbumBuilder
  **File**: `frontend/src/components/__tests__/SmartAlbumBuilder.test.tsx`
  **Details**: Test rule builder interactions: add condition, change operator, nest groups. Mock API, verify correct JSON generated.
  **Dependencies**: T052 (component exists)
  **Worktree**: `../ideal-goggles-task-T071`

- [ ] **T072** Run full quickstart validation
  **File**: `specs/002-smart-collections-with/quickstart.md`
  **Details**: Execute all 6 user acceptance scenarios manually. Verify performance benchmarks. Document any deviations. Get product owner sign-off.
  **Dependencies**: T056, T059 (all features integrated)
  **Worktree**: No (manual testing, sequential)

---

## Dependencies Summary

```
Setup (T001-T003) → Models (T004-T009) → Contract Tests (T010-T024)
                                       ↓
Workers (T025-T028) ← ← ← ← ← ← ← ← ← ← ← ← ← API Impl (T029-T049)
      ↓                                              ↓
Frontend Components (T050-T054) → Integration (T055-T059) → Tests (T060-T065) → Polish (T066-T072)
```

---

## Parallel Execution Examples

### Batch 1: Models (Run after T001-T003)
```bash
# Create 6 worktrees
for i in {004..009}; do
  git worktree add ../ideal-goggles-task-T$i 002-smart-collections-with
done

# Execute in parallel (6 terminals or use GNU parallel)
cd ../ideal-goggles-task-T004 && <execute T004>
cd ../ideal-goggles-task-T005 && <execute T005>
cd ../ideal-goggles-task-T006 && <execute T006>
cd ../ideal-goggles-task-T007 && <execute T007>
cd ../ideal-goggles-task-T008 && <execute T008>
cd ../ideal-goggles-task-T009 && <execute T009>

# Merge and cleanup
cd /Users/sarkalimuthu/WebstormProjects/ideal-goggles
for i in {004..009}; do
  git -C ../ideal-goggles-task-T$i commit -am "Complete T00$i: Model created"
  git merge --no-ff FETCH_HEAD
  git worktree remove ../ideal-goggles-task-T$i
done
git worktree prune
```

### Batch 2: Contract Tests (Run after T004-T009)
```bash
# Create 15 worktrees for T010-T024
for i in {010..024}; do
  git worktree add ../ideal-goggles-task-T$i 002-smart-collections-with
done

# Execute all 15 contract tests in parallel
# (15 parallel workers = significant time savings)
```

### Batch 3: Workers (Run after T010-T024 written, before API impl)
```bash
# 4 parallel workers
for i in {025..028}; do
  git worktree add ../ideal-goggles-task-T$i 002-smart-collections-with
done
```

### Batch 4: Frontend Components (Run after API complete)
```bash
# 5 parallel components
for i in {050..054}; do
  git worktree add ../ideal-goggles-task-T$i 002-smart-collections-with
done
```

### Batch 5: Integration Tests (Run after all implementation)
```bash
# 6 parallel integration tests
for i in {060..065}; do
  git worktree add ../ideal-goggles-task-T$i 002-smart-collections-with
done
```

### Batch 6: Polish (Run after integration tests pass)
```bash
# 6 parallel polish tasks
for i in {066..071}; do
  git worktree add ../ideal-goggles-task-T$i 002-smart-collections-with
done
```

---

## Validation Checklist

After completing all tasks:

- [ ] All 21 contract tests pass (T010-T024)
- [ ] All 6 integration tests pass (T060-T065)
- [ ] Performance benchmarks met:
  - [ ] Auto-tagging: 100 photos/min (T066)
  - [ ] Event detection: <5s for 10K photos (T067)
  - [ ] Duplicate detection: <30s for 1K photos (T068)
  - [ ] Collections page: <2s load (T065)
- [ ] Unit tests: 100% coverage for workers and evaluator (T069-T071)
- [ ] Quickstart scenarios: All 6 pass (T072)
- [ ] Constitution compliance verified:
  - [ ] Local-First Privacy: No network calls
  - [ ] TDD: Tests written before implementation
  - [ ] Performance: All targets met
  - [ ] User-Centric: Progressive disclosure, manual controls

---

**Total Tasks**: 72
**Estimated Duration**: 2-3 weeks with 6 parallel workers
**Sequential Duration**: ~8-10 weeks (without parallelization)
**Speedup**: 3-4x faster with git worktree strategy

---

## Notes

- **Git Worktree Benefits**: Eliminates file conflicts, enables true parallelization
- **Commit Strategy**: Each task commits in its worktree, main branch merges sequentially
- **Cleanup**: Always `git worktree prune` after batch completion
- **Testing**: Contract tests (T010-T024) MUST complete before API implementation (T029-T049)
- **TDD Enforcement**: Implementation tasks depend on corresponding test tasks existing (even if failing)

---

Ready for execution via Task agents or manual development.
