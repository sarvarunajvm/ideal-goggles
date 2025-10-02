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

## Dependencies

### Critical Path Dependencies
- **Database first**: T026-T027 block all data access
- **Models before workers**: T028-T033 block T034-T039
- **Workers before search**: T034-T039 block T048-T050
- **API endpoints need models**: T040-T047 depend on T028-T033
- **Frontend needs API**: T051-T058 depend on T040-T047

### Parallel Execution Boundaries
- **Setup phase** (T001-T006): All can run in parallel
- **Contract tests** (T007-T017): All can run in parallel
- **Integration tests** (T018-T025): All can run in parallel
- **Data models** (T028-T033): All can run in parallel
- **Workers** (T034-T039): All can run in parallel after models exist
- **Performance tasks** (T059-T064): Can run in parallel

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
- [ ] All contract tests pass with real implementations
- [ ] Integration tests validate user scenarios from quickstart.md
- [ ] Search response times meet constitutional requirements (<2s text, <5s image)
- [ ] Memory usage stays under 512MB during normal operation
- [ ] Can index and search 50k+ photos on target hardware
- [ ] Windows installer deploys and runs without errors

## Notes
- **[P] tasks** = different files, no dependencies, can run in true parallel
- **Non-[P] tasks** = sequential execution required due to shared files or dependencies
- **TDD mandatory**: Verify tests fail before implementing (constitutional requirement)
- **Performance validation**: Continuous benchmarking during development
- **Constitutional compliance**: All tasks must maintain local-first privacy and offline operation
