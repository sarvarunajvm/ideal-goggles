# Backend Test Coverage Improvement Plan

## Goal
- **Target Coverage**: 90% (from current 45%)
- **Test Success Rate**: 100%
- **Strategy**: Use git worktrees for parallel development

## Current Coverage Analysis

### Critical Modules (0% Coverage) - Priority 1
1. **src/core/event_queue.py** (267 lines) - ✅ Tests written, need to fix
2. **src/services/drive_manager.py** (272 lines) - Need tests
3. **src/services/faiss_manager.py** (287 lines) - Need tests

### Low Coverage Modules - Priority 2
1. **src/workers/face_worker.py** (17%, 233 lines uncovered)
2. **src/api/dependencies.py** (20%, 109 lines uncovered) - ✅ Tests written
3. **src/models/exif.py** (26%, 142 lines uncovered)
4. **src/models/person.py** (28%, 171 lines uncovered)

### Medium Coverage Modules - Priority 3
1. **src/workers/crawler.py** (30%, 205 lines uncovered)
2. **src/workers/thumbnail_worker.py** (34%, 154 lines uncovered)
3. **src/models/thumbnail.py** (38%, 102 lines uncovered)
4. **src/models/ocr.py** (40%, 91 lines uncovered)
5. **src/api/people.py** (41%, 131 lines uncovered)

### Modules Needing Improvement - Priority 4
1. **src/workers/exif_extractor.py** (47%, 97 lines uncovered)
2. **src/models/embedding.py** (53%, 63 lines uncovered)
3. **src/api/config.py** (55%, 88 lines uncovered)
4. **src/workers/ocr_worker.py** (58%, 104 lines uncovered)

## Git Worktree Structure

```bash
ideal-goggles/
├── backend/                    # Main branch (fixing existing tests)
├── backend-tests-storage/      # Worktree 1: drive_manager, faiss_manager
├── backend-tests-workers1/     # Worktree 2: face_worker, thumbnail_worker
├── backend-tests-workers2/     # Worktree 3: crawler, ocr_worker, exif_extractor
├── backend-tests-models/       # Worktree 4: person, exif, ocr, thumbnail, embedding
└── backend-tests-api/          # Worktree 5: people, config improvements
```

## Execution Plan

### Phase 1: Setup & Fix Existing Tests (Current Branch)
1. Fix failing tests in test_event_queue.py
2. Fix failing tests in test_api_dependencies.py
3. Fix failing tests in test_vector_search.py
4. Ensure all existing tests pass with 100% success rate

### Phase 2: Create Worktrees for Parallel Development
```bash
# Create worktrees for parallel test development
git worktree add ../backend-tests-storage main
git worktree add ../backend-tests-workers1 main
git worktree add ../backend-tests-workers2 main
git worktree add ../backend-tests-models main
git worktree add ../backend-tests-api main
```

### Phase 3: Parallel Test Development

#### Worktree 1: Storage Services (backend-tests-storage)
**Target: +20% coverage**
- [ ] test_drive_manager.py (272 lines)
- [ ] test_faiss_manager.py (287 lines)
- Mock external dependencies (Google Drive API, FAISS)
- Focus on business logic and error handling

#### Worktree 2: Worker Services 1 (backend-tests-workers1)
**Target: +15% coverage**
- [ ] test_face_worker.py (233 lines)
- [ ] test_thumbnail_worker.py (154 lines)
- Mock image processing libraries
- Test queue processing and error recovery

#### Worktree 3: Worker Services 2 (backend-tests-workers2)
**Target: +12% coverage**
- [ ] test_crawler.py (205 lines)
- [ ] test_ocr_worker.py (104 lines)
- [ ] test_exif_extractor.py (97 lines)
- Mock file system operations
- Test batch processing

#### Worktree 4: Models (backend-tests-models)
**Target: +10% coverage**
- [ ] test_models_person.py (171 lines)
- [ ] test_models_exif.py (142 lines)
- [ ] test_models_ocr.py (91 lines)
- [ ] test_models_thumbnail.py (102 lines)
- [ ] Improve test_models_embedding.py (63 lines)
- Test data validation and transformations

#### Worktree 5: API Endpoints (backend-tests-api)
**Target: +8% coverage**
- [ ] test_api_people.py (131 lines)
- [ ] Improve test_api_config.py (88 lines)
- Test request/response validation
- Test error handling and edge cases

### Phase 4: Integration & Merge
1. Run tests in each worktree to ensure 100% pass rate
2. Create feature branches from each worktree
3. Merge all branches into main
4. Run comprehensive coverage report
5. Address any conflicts or integration issues

## Test Writing Guidelines

### 1. Mock Strategy
```python
# Always mock external dependencies
@patch('src.services.drive_manager.build')  # Google API
@patch('faiss.IndexFlatIP')  # FAISS
@patch('PIL.Image.open')  # Image processing
@patch('pytesseract.image_to_string')  # OCR
```

### 2. Test Structure
```python
class TestModule:
    @pytest.fixture
    def setup(self):
        # Setup test data
        pass

    def test_initialization(self):
        # Test class initialization
        pass

    def test_normal_operation(self):
        # Test happy path
        pass

    def test_error_handling(self):
        # Test error cases
        pass

    def test_edge_cases(self):
        # Test boundary conditions
        pass
```

### 3. Coverage Focus Areas
- Constructor/initialization code
- Public methods
- Error handling paths
- Edge cases and boundary conditions
- Configuration variations
- Thread safety (where applicable)

## Success Metrics
- [ ] Overall coverage ≥ 90%
- [ ] All tests passing (100% success rate)
- [ ] No flaky tests
- [ ] Tests run in < 2 minutes
- [ ] Each module has ≥ 80% coverage

## Commands for Parallel Execution

```bash
# Terminal 1 - Main branch (fix existing tests)
pytest tests/unit/test_event_queue.py -xvs

# Terminal 2 - Storage tests
cd ../backend-tests-storage
pytest tests/unit/test_drive_manager.py tests/unit/test_faiss_manager.py -xvs

# Terminal 3 - Worker tests 1
cd ../backend-tests-workers1
pytest tests/unit/test_face_worker.py tests/unit/test_thumbnail_worker.py -xvs

# Terminal 4 - Worker tests 2
cd ../backend-tests-workers2
pytest tests/unit/test_crawler.py tests/unit/test_ocr_worker.py -xvs

# Terminal 5 - Model tests
cd ../backend-tests-models
pytest tests/unit/test_models_*.py -xvs

# Terminal 6 - API tests
cd ../backend-tests-api
pytest tests/unit/test_api_*.py -xvs
```

## Final Coverage Check
```bash
# After merging all branches
pytest --cov=src --cov-report=html --cov-report=term
# Open htmlcov/index.html to see detailed coverage
```

## Estimated Timeline
- Phase 1 (Fix existing): 1 hour
- Phase 2 (Setup worktrees): 15 minutes
- Phase 3 (Parallel development): 3-4 hours
- Phase 4 (Integration): 30 minutes
- **Total: 5-6 hours**

## Risk Mitigation
1. **Test Isolation**: Ensure tests don't depend on each other
2. **Mock Consistency**: Use shared mock utilities
3. **Merge Conflicts**: Keep changes isolated to test files
4. **Performance**: Use pytest-xdist for parallel test execution
5. **Flaky Tests**: Add retries for network/timing-sensitive tests