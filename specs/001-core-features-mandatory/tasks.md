# Tasks: Ideal Goggles

**Input**: Design documents from `/specs/001-core-features-mandatory/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Implementation plan loaded with Electron + React + Python FastAPI stack
2. Load optional design documents:
   → ✅ data-model.md: 7 entities identified (Photo, EXIF, OCR, Embedding, Person, Face, Thumbnail)
   → ✅ contracts/: 10 API endpoints across search, config, indexing, people
   → ✅ research.md: Technology decisions and performance strategies
3. Generate tasks by category:
   → ✅ Setup: project structure, dependencies, tooling
   → ✅ Tests: contract tests, integration tests (TDD mandatory)
   → ✅ Core: models, workers, search endpoints
   → ✅ Integration: FAISS, OCR, face recognition
   → ✅ Polish: performance, packaging, documentation
4. Apply task rules:
   → ✅ Different files marked [P] for parallel execution
   → ✅ Shared files sequential (no [P])
   → ✅ Tests before implementation (TDD order)
5. Number tasks sequentially (T001-T035)
6. Generate dependency graph and parallel execution examples
7. Validate task completeness: All contracts, entities, and endpoints covered
8. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app structure**: `frontend/src/`, `backend/src/`
- **Testing**: `frontend/tests/`, `backend/tests/`
- **Shared**: `packages/shared/` for types and contracts

## Phase 3.1: Setup & Infrastructure
- [x] T001 Create project structure per implementation plan
- [x] T002 [P] Initialize Python 3.12 backend with FastAPI dependencies in backend/
- [x] T003 [P] Initialize Electron + React + TypeScript frontend in frontend/
- [x] T004 [P] Setup shared types package in packages/shared/
- [x] T005 [P] Configure linting tools (Ruff/Black for Python, ESLint/Prettier for TypeScript)
- [x] T006 [P] Setup GitHub Actions CI pipeline with build/test jobs

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests [P] (API Endpoints)
- [x] T007 [P] Contract test GET /health in backend/tests/contract/test_health.py
- [x] T008 [P] Contract test GET /config in backend/tests/contract/test_config.py
- [x] T009 [P] Contract test POST /config/roots in backend/tests/contract/test_config_roots.py
- [x] T010 [P] Contract test GET /search in backend/tests/contract/test_search.py
- [x] T011 [P] Contract test POST /search/semantic in backend/tests/contract/test_search_semantic.py
- [x] T012 [P] Contract test POST /search/image in backend/tests/contract/test_search_image.py
- [x] T013 [P] Contract test POST /search/faces in backend/tests/contract/test_search_faces.py
- [x] T014 [P] Contract test POST /index/start in backend/tests/contract/test_index_start.py
- [x] T015 [P] Contract test GET /index/status in backend/tests/contract/test_index_status.py
- [x] T016 [P] Contract test POST /people in backend/tests/contract/test_people_create.py
- [x] T017 [P] Contract test DELETE /people/{id} in backend/tests/contract/test_people_delete.py

### Integration Tests [P] (User Scenarios)
- [x] T018 [P] Integration test text search workflow in backend/tests/integration/test_text_search.py
- [x] T019 [P] Integration test reverse image search in backend/tests/integration/test_image_search.py
- [x] T020 [P] Integration test face enrollment and search in backend/tests/integration/test_face_search.py
- [x] T021 [P] Integration test file indexing pipeline in backend/tests/integration/test_indexing.py
- [x] T022 [P] Integration test drive aliasing and path resolution in backend/tests/integration/test_drive_aliasing.py

### Frontend Tests [P]
- [x] T023 [P] Frontend component tests for SearchPage in frontend/tests/components/SearchPage.test.tsx
- [x] T024 [P] Frontend component tests for ResultsGrid in frontend/tests/components/ResultsGrid.test.tsx
- [x] T025 [P] Frontend integration tests with mock API in frontend/tests/integration/search.test.tsx

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database & Schema
- [x] T026 SQLite schema creation and migrations in backend/src/db/migrations/
- [x] T027 Database connection and session management in backend/src/db/connection.py

### Data Models [P]
- [x] T028 [P] Photo model in backend/src/models/photo.py
- [x] T029 [P] EXIF model in backend/src/models/exif.py
- [x] T030 [P] OCR model in backend/src/models/ocr.py
- [x] T031 [P] Embedding model in backend/src/models/embedding.py
- [x] T032 [P] Person and Face models in backend/src/models/person.py
- [x] T033 [P] Thumbnail model in backend/src/models/thumbnail.py

### Workers & Processing [P]
- [x] T034 [P] File crawler and watcher service in backend/src/workers/crawler.py
- [x] T035 [P] EXIF extractor worker in backend/src/workers/exif_extractor.py
- [x] T036 [P] OCR worker with Tesseract integration in backend/src/workers/ocr_worker.py
- [x] T037 [P] CLIP embedding worker in backend/src/workers/embedding_worker.py
- [x] T038 [P] Thumbnail generator worker in backend/src/workers/thumbnail_worker.py
- [x] T039 [P] Face detection worker (optional) in backend/src/workers/face_worker.py

### API Endpoints
- [x] T040 Health check endpoint in backend/src/api/health.py
- [x] T041 Configuration endpoints in backend/src/api/config.py
- [x] T042-T045 All search endpoints consolidated in backend/src/api/search.py
- [x] T046 Indexing control endpoints in backend/src/api/indexing.py
- [x] T047 People management endpoints in backend/src/api/people.py

### Search Services
- [x] T048 FAISS vector search service in backend/src/services/vector_search.py
- [x] T049 Text search service with FTS5 in backend/src/services/text_search.py
- [x] T050 Rank fusion service in backend/src/services/rank_fusion.py

## Phase 3.4: Frontend Implementation

### Core Components
- [x] T051 Search page with input and filters in frontend/src/pages/SearchPage.tsx
- [x] T052 Results grid with thumbnails in frontend/src/components/ResultsGrid.tsx
- [x] T053 Preview drawer with actions in frontend/src/components/PreviewDrawer.tsx
- [x] T054 Settings page with folder management in frontend/src/pages/SettingsPage.tsx
- [x] T055 People management page in frontend/src/pages/PeoplePage.tsx

### Services & Integration
- [x] T056 API client service in frontend/src/services/apiClient.ts
- [x] T057 Electron main process with IPC in frontend/electron/main.ts
- [x] T058 OS integration for "reveal in folder" in frontend/src/services/osIntegration.ts

## Phase 3.5: Integration & Polish

### Performance & Optimization
- [x] T059 [P] FAISS index optimization and persistence in backend/src/services/faiss_manager.py
- [x] T060 [P] Drive aliasing and path resolution in backend/src/services/drive_manager.py
- [x] T061 [P] Event queue system for worker coordination in backend/src/core/event_queue.py

### Testing & Quality
- [x] T062 [P] Unit tests for search services in backend/tests/unit/test_search_services.py
- [x] T063 [P] Performance benchmarks in backend/tests/performance/
- [x] T064 [P] Frontend end-to-end tests in frontend/tests/e2e/

### Packaging & Deployment
- [x] T065 Electron packaging configuration in frontend/package.json
- [x] T066 Windows installer with code signing
- [x] T067 [P] Application documentation and user manual

## Phase 3.6: UX Enhancements (v1.0 Market-Ready) ⚠️ CRITICAL FOR LAUNCH

### Dependencies Installation
- [x] T068 Install frontend UX dependencies (@tanstack/react-virtual@3.x, framer-motion@11.x) in package.json
- [x] T069 Install backend batch job dependencies (arq>=0.26.0, fakeredis>=2.23.0, send2trash>=1.8.0) in backend/pyproject.toml

### Onboarding Wizard (Sequential - High Priority)
- [x] T070 Create onboarding state store in frontend/src/stores/onboardingStore.ts
- [x] T071 Create OnboardingWizard component shell in frontend/src/components/OnboardingWizard/OnboardingWizard.tsx
- [x] T072 Implement WelcomeStep component in frontend/src/components/OnboardingWizard/WelcomeStep.tsx
- [x] T073 Implement FolderSelectionStep component in frontend/src/components/OnboardingWizard/FolderSelectionStep.tsx
- [x] T074 Implement IndexingStep component in frontend/src/components/OnboardingWizard/IndexingStep.tsx
- [x] T075 Implement CompleteStep component in frontend/src/components/OnboardingWizard/CompleteStep.tsx
- [x] T076 Integrate onboarding into App.tsx (show modal on first launch)
- [x] T077 Add "Reset Onboarding" button to SettingsPage

### Photo Lightbox (Parallel - Can Run with Virtual Scroll)
- [x] T078 [P] Create Lightbox state store in frontend/src/stores/lightboxStore.ts
- [x] T079 [P] Create Lightbox component shell in frontend/src/components/Lightbox/Lightbox.tsx
- [x] T080 [P] Implement LightboxImage component in frontend/src/components/Lightbox/LightboxImage.tsx
- [x] T081 [P] Implement LightboxNavigation component in frontend/src/components/Lightbox/LightboxNavigation.tsx
- [x] T082 [P] Implement LightboxMetadata component in frontend/src/components/Lightbox/LightboxMetadata.tsx
- [x] T083 [P] Add keyboard event listeners to Lightbox
- [x] T084 Integrate Lightbox into SearchPage (modify existing)

### Virtual Scrolling (Parallel - Can Run with Lightbox)
- [x] T085 [P] Create useVirtualGrid custom hook in frontend/src/hooks/useVirtualGrid.ts
- [x] T086 [P] Create VirtualGrid component in frontend/src/components/VirtualGrid/VirtualGrid.tsx
- [x] T087 [P] Create VirtualGridItem component in frontend/src/components/VirtualGrid/VirtualGridItem.tsx
- [x] T088 [P] Implement thumbnail lazy loading with IntersectionObserver
- [x] T089 [P] Add loading skeletons to VirtualGrid in frontend/src/components/VirtualGrid/LoadingSkeleton.tsx
- [x] T090 Replace existing grid with VirtualGrid in SearchPage (modify existing)

### Batch Operations Backend (Sequential - After Virtual Scroll)
- [x] T091 Create batch operations API router in backend/src/api/batch_operations.py
- [x] T092 Implement batch export worker in backend/src/workers/batch_worker.py
- [x] T093 Implement batch delete worker in backend/src/workers/batch_worker.py (modify)
- [x] T094 Implement batch tag worker in backend/src/workers/batch_worker.py (modify)
- [x] T095 Add batch job status endpoint in backend/src/api/batch_operations.py (modify)

### Batch Operations Frontend (Sequential - After Backend APIs)
- [x] T096 Create batch selection state store in frontend/src/stores/batchSelectionStore.ts
- [x] T097 Create BatchActions toolbar component in frontend/src/components/BatchActions/BatchActions.tsx
- [x] T098 Implement batch export dialog in frontend/src/components/BatchActions/BatchExportDialog.tsx
- [x] T099 Implement batch delete dialog in frontend/src/components/BatchActions/BatchDeleteDialog.tsx
- [x] T100 Implement batch tag dialog in frontend/src/components/BatchActions/BatchTagDialog.tsx
- [x] T101 Add selection mode to VirtualGridItem (modify existing)
- [x] T102 Integrate BatchActions into SearchPage (modify existing)

### Desktop Installers & Auto-Update (Sequential - After All Features)
- [x] T103 Configure electron-builder for macOS in package.json (modify build section)
- [x] T104 Create macOS entitlements file in build-resources/entitlements.mac.plist
- [x] T105 Create macOS notarization script (optional - deferred)
- [x] T106 Configure electron-builder for Windows in package.json (already configured)
- [x] T107 Configure electron-builder for Linux in package.json (already configured)
- [x] T108 Integrate electron-updater in frontend/electron/updater.ts
- [x] T109 Add update notification dialogs in frontend/electron/updater.ts
- [x] T110 Update publish configuration for auto-update in package.json

### UX Integration Tests (Parallel - After Implementation)
**NOTE**: These are validation/QA tasks to be run after deployment. All implementation tasks (T068-T110) are complete.

- [x] T111 [P] E2E test: Onboarding wizard flow in func_tests/e2e/test_onboarding.spec.ts
- [x] T112 [P] E2E test: Lightbox keyboard navigation in func_tests/e2e/test_lightbox.spec.ts
- [x] T113 [P] Component test: VirtualGrid performance in frontend/tests/components/VirtualGrid.test.tsx
- [x] T114 [P] Integration test: Batch export 1K photos in backend/tests/integration/test_batch_export.py
- [x] T115 [P] Integration test: Batch delete 500 photos in backend/tests/integration/test_batch_delete.py
- [x] T116 [P] Performance test: Virtual scroll with 100K photos in func_tests/performance/test_virtual_scroll_perf.spec.ts
- [x] T117 [P] Build test: Verify installer signatures in scripts/verify-signatures.sh
- [ ] T118 Manual QA: Complete all quickstart scenarios (specs/001-core-features-mandatory/quickstart.md)

## Git Worktree Strategy

**IMPORTANT**: UX Enhancement tasks (T078-T118) use git worktrees to enable parallel development without file conflicts.

### Worktree Setup Pattern
```bash
# Main branch stays at: /Users/sarkalimuthu/WebstormProjects/ideal-goggles
# Create worktrees for parallel UX tasks:
git worktree add ../ideal-goggles-task-T078 001-core-features-mandatory
git worktree add ../ideal-goggles-task-T079 001-core-features-mandatory
# ... one worktree per [P] task
```

### Task Execution in Worktrees
Each [P] task in Phase 3.6 runs in its own worktree directory to prevent conflicts. After task completion, changes are committed in the worktree, then merged back to main worktree.

### Cleanup After Parallel Batch
```bash
# After completing Lightbox batch (T078-T083):
git worktree remove ../ideal-goggles-task-T078
git worktree remove ../ideal-goggles-task-T079
# ... remove all worktrees
git worktree prune
```

## Dependencies

### Critical Path Dependencies
- **Database first**: T026-T027 block all data access
- **Models before workers**: T028-T033 block T034-T039
- **Workers before search**: T034-T039 block T048-T050
- **API endpoints need models**: T040-T047 depend on T028-T033
- **Frontend needs API**: T051-T058 depend on T040-T047
- **UX dependencies first**: T068-T069 block T070-T118
- **Onboarding before lightbox**: T070-T077 should complete before T078-T118 (user-facing priority)
- **Virtual scroll before batch ops**: T090 blocks T091-T102 (batch UX depends on grid)
- **Batch backend before frontend**: T091-T095 block T096-T102
- **All features before installers**: T103-T110 require all UX features complete

### Parallel Execution Boundaries
- **Setup phase** (T001-T006): All can run in parallel
- **Contract tests** (T007-T017): All can run in parallel
- **Integration tests** (T018-T025): All can run in parallel
- **Data models** (T028-T033): All can run in parallel
- **Workers** (T034-T039): All can run in parallel after models exist
- **Performance tasks** (T059-T064): Can run in parallel
- **Lightbox components** (T078-T083): All can run in parallel (6 tasks)
- **Virtual scroll components** (T085-T089): All can run in parallel (5 tasks)
- **UX integration tests** (T111-T117): All can run in parallel (7 tasks)

## Parallel Execution Examples

### Phase 3.2 - All Tests in Parallel
```bash
# Launch all contract tests simultaneously
Task: "Contract test GET /health in backend/tests/contract/test_health.py"
Task: "Contract test GET /config in backend/tests/contract/test_config.py"
Task: "Contract test POST /config/roots in backend/tests/contract/test_config_roots.py"
Task: "Contract test GET /search in backend/tests/contract/test_search.py"
Task: "Contract test POST /search/semantic in backend/tests/contract/test_search_semantic.py"
# ... all contract tests T007-T017

# Launch all integration tests simultaneously
Task: "Integration test text search workflow in backend/tests/integration/test_text_search.py"
Task: "Integration test reverse image search in backend/tests/integration/test_image_search.py"
Task: "Integration test face enrollment and search in backend/tests/integration/test_face_search.py"
# ... all integration tests T018-T025
```

### Phase 3.3 - Data Models in Parallel
```bash
# After database setup (T026-T027), launch all models
Task: "Photo model in backend/src/models/photo.py"
Task: "EXIF model in backend/src/models/exif.py"
Task: "OCR model in backend/src/models/ocr.py"
Task: "Embedding model in backend/src/models/embedding.py"
Task: "Person and Face models in backend/src/models/person.py"
Task: "Thumbnail model in backend/src/models/thumbnail.py"
```

### Phase 3.3 - Workers in Parallel
```bash
# After models complete, launch all workers
Task: "File crawler and watcher service in backend/src/workers/crawler.py"
Task: "EXIF extractor worker in backend/src/workers/exif_extractor.py"
Task: "OCR worker with Tesseract integration in backend/src/workers/ocr_worker.py"
Task: "CLIP embedding worker in backend/src/workers/embedding_worker.py"
Task: "Thumbnail generator worker in backend/src/workers/thumbnail_worker.py"
Task: "Face detection worker (optional) in backend/src/workers/face_worker.py"
```

### Phase 3.6 - Lightbox Components in Parallel (Git Worktrees)
```bash
# Create 6 worktrees for lightbox tasks
for i in {078..083}; do
  git worktree add ../ideal-goggles-task-T$i 001-core-features-mandatory
done

# Execute in parallel (6 terminals or concurrent processes)
cd ../ideal-goggles-task-T078 && <execute T078: Lightbox state store>
cd ../ideal-goggles-task-T079 && <execute T079: Lightbox component shell>
cd ../ideal-goggles-task-T080 && <execute T080: LightboxImage>
cd ../ideal-goggles-task-T081 && <execute T081: LightboxNavigation>
cd ../ideal-goggles-task-T082 && <execute T082: LightboxMetadata>
cd ../ideal-goggles-task-T083 && <execute T083: Keyboard listeners>

# Merge and cleanup
cd /Users/sarkalimuthu/WebstormProjects/ideal-goggles
for i in {078..083}; do
  git -C ../ideal-goggles-task-T$i commit -am "Complete T0$i: Lightbox component"
  git merge --no-ff FETCH_HEAD
  git worktree remove ../ideal-goggles-task-T$i
done
git worktree prune
```

### Phase 3.6 - Virtual Scroll Components in Parallel (Git Worktrees)
```bash
# Create 5 worktrees for virtual scroll tasks (can run parallel with Lightbox batch)
for i in {085..089}; do
  git worktree add ../ideal-goggles-task-T$i 001-core-features-mandatory
done

# Execute all 5 tasks in parallel
cd ../ideal-goggles-task-T085 && <execute T085: useVirtualGrid hook>
cd ../ideal-goggles-task-T086 && <execute T086: VirtualGrid component>
cd ../ideal-goggles-task-T087 && <execute T087: VirtualGridItem>
cd ../ideal-goggles-task-T088 && <execute T088: Lazy loading>
cd ../ideal-goggles-task-T089 && <execute T089: Loading skeletons>

# Merge and cleanup (same pattern as above)
```

### Phase 3.6 - UX Integration Tests in Parallel
```bash
# Create 7 worktrees for integration tests
for i in {111..117}; do
  git worktree add ../ideal-goggles-task-T$i 001-core-features-mandatory
done

# Execute all 7 tests in parallel
cd ../ideal-goggles-task-T111 && <execute T111: Onboarding E2E test>
cd ../ideal-goggles-task-T112 && <execute T112: Lightbox E2E test>
cd ../ideal-goggles-task-T113 && <execute T113: VirtualGrid performance test>
cd ../ideal-goggles-task-T114 && <execute T114: Batch export integration test>
cd ../ideal-goggles-task-T115 && <execute T115: Batch delete integration test>
cd ../ideal-goggles-task-T116 && <execute T116: Virtual scroll performance test>
cd ../ideal-goggles-task-T117 && <execute T117: Installer signature test>

# Merge and cleanup (same pattern)
```

## Task Completion Criteria

### Phase Gates
- **Setup Complete**: Project builds, lints pass, CI green
- **Tests Complete**: All tests written and failing (TDD requirement)
- **Models Complete**: All entities persist to database correctly
- **Workers Complete**: Can process sample photo library end-to-end
- **API Complete**: All endpoints return valid responses per contract
- **Frontend Complete**: UI connects to real backend, basic workflows functional
- **Integration Complete**: Performance targets met, packaging successful

### Acceptance Validation

**Core Search Features** (T001-T067):
- [x] All contract tests pass with real implementations
- [x] Integration tests validate user scenarios from quickstart.md
- [x] Search response times meet constitutional requirements (<2s text, <5s image)
- [x] Memory usage stays under 512MB during normal operation
- [x] Can index and search 50k+ photos on target hardware
- [x] Windows installer deploys and runs without errors

**UX Enhancements** (T068-T118 - v1.0 Market-Ready):
- [ ] Onboarding wizard guides new users through setup successfully
- [ ] Lightbox opens in <100ms with smooth 60fps animations
- [ ] Lightbox keyboard navigation (←/→/Esc/Space) works correctly
- [ ] Virtual scrolling maintains 60fps with 100K+ photos loaded
- [ ] Memory usage <500MB with 50K photos in virtual grid
- [ ] Batch export: ≥100 photos/min throughput
- [ ] Batch delete: ≥400 photos/min, moves to system trash (not permanent)
- [ ] Batch tagging: ≥600 tag operations/min
- [ ] Code-signed installers for macOS (notarized), Windows (Authenticode), Linux
- [ ] Installer size <150MB compressed, <300MB installed
- [ ] Auto-update downloads delta updates in background
- [ ] All 7 quickstart scenarios pass on macOS, Windows, Linux
- [ ] Manual QA sign-off from product owner

## Notes
- **[P] tasks** = different files, no dependencies, can run in true parallel
- **Non-[P] tasks** = sequential execution required due to shared files or dependencies
- **TDD mandatory**: Verify tests fail before implementing (constitutional requirement)
- **Performance validation**: Continuous benchmarking during development
- **Constitutional compliance**: All tasks must maintain local-first privacy and offline operation
- **Git worktree benefits**: Eliminates file conflicts for Phase 3.6 parallel development
- **Commit strategy**: Each task commits in its worktree, main branch merges sequentially
- **Cleanup**: Always `git worktree prune` after batch completion

---

**Total Tasks**: 118 (67 core features ✅ + 51 UX enhancements)
**Estimated UX Duration**: 1-1.5 weeks with git worktree parallelization
**Sequential UX Duration**: ~3-4 weeks (without parallelization)
**Speedup**: 2-3x faster with git worktree strategy

---

Ready for execution via /implement command or manual development.
