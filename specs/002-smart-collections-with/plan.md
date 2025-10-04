# Implementation Plan: Smart Collections with Auto-Tagging and Event Detection

**Branch**: `002-smart-collections-with` | **Date**: 2025-10-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/sarkalimuthu/WebstormProjects/ideal-goggles/specs/002-smart-collections-with/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Implement intelligent photo organization using AI-powered auto-tagging, temporal event detection, duplicate identification, and rule-based smart albums. The system will automatically analyze indexed photos to generate descriptive tags using CLIP zero-shot classification, cluster photos into events based on capture time proximity, detect near-duplicates using perceptual hashing + embeddings similarity, and enable dynamic smart albums with complex filtering rules. All processing remains 100% local, maintaining privacy while delivering <2s collections page load times for 10K+ photo libraries.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.115+, CLIP (ONNX), scikit-learn 1.5+ (DBSCAN), imagehash 4.3+, SQLAlchemy 2.0+
- Frontend: React 19, Zustand 5.0 (state), TanStack Query 5.x (data fetching)
**Storage**: SQLite with FTS5 (full-text tag search) + new tables (tags, events, collections, smart_albums, duplicate_groups)
**Testing**: pytest 8.x (backend contract/integration), Jest 30.x + React Testing Library (frontend)
**Target Platform**: Desktop (macOS, Windows, Linux) via Electron 38+
**Project Type**: Web (frontend + backend) - existing Ideal Goggles architecture
**Performance Goals**:
- Auto-tagging: 100 photos/min (600ms per photo including CLIP inference)
- Event detection: <5s for 10K photos using optimized DBSCAN
- Duplicate detection: <30s for 1K photos using phash + FAISS
- Collections view: <2s initial load with lazy thumbnail loading
**Constraints**:
- 100% offline operation (no network calls)
- Non-destructive (all generated data stored in DB, original photos untouched)
- Memory: <512MB for auto-tagging batch processing
- Database queries: <100ms for tag/collection lookups
**Scale/Scope**: Support 1M+ photos, 10K+ tags, 1K+ events, 100+ smart albums without performance degradation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Local-First Privacy ✅ PASS
- All tagging, event detection, and duplicate analysis runs locally
- CLIP model bundled in application (no downloads)
- Tags/events/collections stored in local SQLite
- No external API calls or telemetry

### II. Test-Driven Development ✅ PASS
- Contract tests for all new API endpoints (tags, events, collections, smart albums)
- Integration tests for auto-tagging pipeline, event detection, duplicate grouping
- Frontend component tests for CollectionsPage, TagEditor, DuplicateReview
- TDD cycle: tests first → fail → implement → pass

### III. Specification-Driven Development ✅ PASS
- Complete spec with 40 functional requirements
- Clear acceptance scenarios (6 primary + edge cases)
- Measurable success criteria (performance targets, accuracy thresholds)

### IV. Performance & Reliability ✅ PASS
- Auto-tagging: 100 photos/min target (FR-032)
- Event detection: <5s for 10K photos (FR-033)
- Duplicate detection: <30s for 1K photos (FR-034)
- Collections view: <2s load time (FR-035)
- Fail-safe: errors in one photo don't break batch processing
- Incremental: can resume interrupted operations

### V. User-Centric Design ✅ PASS
- Progressive disclosure: Collections view hidden until auto-detection enabled
- Zero-learning curve: Auto-tagging happens transparently during indexing
- Clear indicators: Confidence scores shown for auto-generated tags
- Manual control: Users can edit/remove tags, rename/merge/split events
- Simple defaults: 4-hour event threshold, 85% duplicate similarity

**Initial Constitution Check: PASS** - No violations detected

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 2 (Web application) - Existing Ideal Goggles uses frontend/ + backend/ structure

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. **Database & Models** (from data-model.md):
   - Create migration for new tables (tags, events, collections, smart_albums, duplicate_groups)
   - Create SQLAlchemy models for each entity
   - Create database triggers for auto-updating counts

2. **Contract Tests** (from contracts/*.yaml):
   - Tags API: 5 contract tests (GET/POST/DELETE tags, GET/POST/DELETE photo tags)
   - Events API: 4 contract tests (list, detect, get, update/delete)
   - Collections API: 5 contract tests (CRUD + add/remove photos)
   - Smart Albums API: 4 contract tests (CRUD + evaluate)
   - Duplicates API: 3 contract tests (list, detect, resolve)

3. **Workers** (from research.md):
   - AutoTaggingWorker using CLIP zero-shot classification
   - EventDetectionWorker using DBSCAN clustering
   - DuplicateDetectionWorker using phash + CLIP similarity
   - SmartAlbumEvaluator for rule-based queries

4. **API Endpoints** (to make contract tests pass):
   - Implement 5 routers (tags, events, collections, smart_albums, duplicates)
   - 21 total endpoints across all routers

5. **Frontend Components** (from quickstart.md scenarios):
   - CollectionsPage with event/album list
   - TagEditor component for manual tagging
   - SmartAlbumBuilder with visual rule editor
   - DuplicateReview component with side-by-side comparison
   - Integration with existing SearchPage for tag filters

6. **Integration Tests** (from quickstart.md):
   - Auto-tagging during indexing flow
   - Event detection end-to-end
   - Tag search with AND/OR logic
   - Smart album dynamic membership
   - Duplicate detection and resolution

**Ordering Strategy**:
1. **Phase 3.1**: Database migration + models [Sequential: must run first]
2. **Phase 3.2**: Contract tests [Parallel: independent test files]
3. **Phase 3.3**: Workers [Parallel: independent modules]
4. **Phase 3.4**: API endpoints [Partially parallel: after contract tests written]
5. **Phase 3.5**: Frontend components [Parallel after API complete]
6. **Phase 3.6**: Integration tests [After all implementation]

**Estimated Output**:
- Setup/Migration: 3 tasks
- Contract Tests: 21 tasks [P]
- Workers: 4 tasks [P]
- API Implementation: 21 tasks (some [P])
- Frontend: 10 tasks [P]
- Integration Tests: 6 tasks [P]
- **Total: ~65 tasks** in dependency order

**Parallelization Opportunities**:
- All contract tests can run simultaneously (21 parallel)
- All 4 workers can be developed in parallel
- Frontend components parallel after API complete
- Total dev time estimate: 2-3 weeks with proper task distribution

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅
- [x] Complexity deviations documented (None - no violations) ✅

**Artifacts Generated**:
- [x] research.md - Technology decisions and best practices
- [x] data-model.md - Complete schema with 10 entities
- [x] contracts/tags-api.yaml - Detailed Tags API contract
- [x] contracts/README.md - All 5 API contracts summary
- [x] quickstart.md - User acceptance test scenarios

**Ready for /tasks command** ✅

---
*Based on Constitution v1.0.1 - See `.specify/memory/constitution.md`*
