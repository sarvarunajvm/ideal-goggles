# Research Findings: Ideal Goggles

## Technology Stack Research

### Frontend Framework Decision
**Decision**: Electron + React + TypeScript
**Rationale**: Cross-platform desktop requirement with rich UI interactions. Electron provides native OS integration for "reveal in folder" functionality. React ecosystem mature for complex search interfaces.
**Alternatives considered**: Tauri (smaller bundle but less mature), Qt (native but steeper learning curve)

### Backend Framework Decision
**Decision**: Python 3.12 + FastAPI
**Rationale**: Excellent ML/AI library ecosystem (ONNX, FAISS, Tesseract). FastAPI provides automatic OpenAPI generation and high performance. Python excels at image processing pipelines.
**Alternatives considered**: Node.js (unified language but weaker ML tools), Rust (performance but limited ML ecosystem)

### Database and Search Decision
**Decision**: SQLite + FTS5 + FAISS
**Rationale**: SQLite FTS5 for text search, FAISS for vector similarity. Single-file database ideal for desktop apps. FAISS optimized for large-scale similarity search.
**Alternatives considered**: PostgreSQL (overkill for desktop), Elasticsearch (requires JVM), ChromaDB (newer, less proven)

### Machine Learning Pipeline Decisions

#### OCR Solution
**Decision**: Tesseract OCR with English + Tamil language packs
**Rationale**: Industry standard, offline capable, supports required languages for photo studio use case.
**Alternatives considered**: Cloud OCR services (violates privacy principle), PaddleOCR (good but larger model size)

#### Image Embeddings
**Decision**: CLIP ViT-B/32 via ONNX Runtime
**Rationale**: Best balance of accuracy and performance for semantic image search. ONNX ensures cross-platform deployment.
**Alternatives considered**: OpenCLIP (similar), ResNet features (less semantic understanding)

#### Face Recognition (Optional)
**Decision**: InsightFace ArcFace model via ONNX Runtime
**Rationale**: State-of-art accuracy for face recognition, privacy-preserving local deployment.
**Alternatives considered**: Face++ (cloud-based, violates privacy), OpenCV DNN (lower accuracy)

### Performance Optimization Research

#### Vector Index Strategy
**Decision**: FAISS with IVF,PQ for >200k photos, Flat for smaller collections
**Rationale**: IVF,PQ provides sub-linear search time with minimal accuracy loss. Auto-switching based on collection size.
**Alternatives considered**: HNSW (good but higher memory), LSH (faster indexing but lower accuracy)

#### Thumbnail Caching
**Decision**: WebP format with 256-512px max dimension, SHA-1 based file organization
**Rationale**: WebP provides best compression. SHA-1 based paths enable deduplication and avoid path length issues.
**Alternatives considered**: JPEG (larger files), AVIF (not widely supported), PNG (no compression benefit)

### Development Workflow Research

#### Testing Strategy
**Decision**: pytest (Python), Jest (TypeScript), Playwright (integration)
**Rationale**: Standard tools for respective ecosystems. Playwright enables cross-platform desktop testing.
**Alternatives considered**: unittest (less features), Cypress (web-focused), Selenium (heavier)

#### Monorepo Structure
**Decision**: apps/ui + apps/indexer + packages/shared structure
**Rationale**: Clear separation of concerns, shared types between frontend/backend, independent deployment.
**Alternatives considered**: Single repo (harder to manage), separate repos (coordination overhead)

## Architecture Patterns Research

### Inter-Process Communication
**Decision**: HTTP API between Electron and Python service
**Rationale**: Standard protocol, easy debugging, allows separate process lifecycles.
**Alternatives considered**: gRPC (more complex), IPC sockets (platform-specific), embedded Python (packaging complexity)

### Indexing Pipeline Design
**Decision**: Worker queue with backpressure control
**Rationale**: Prevents UI blocking, handles large directory scanning, graceful error recovery.
**Alternatives considered**: Synchronous scanning (blocks UI), Thread pool (GIL limitations)

### Search Result Ranking
**Decision**: Weighted fusion of FTS scores + vector similarity + metadata filters
**Rationale**: Combines multiple signals for relevance, allows user tuning of weights.
**Alternatives considered**: Single scoring method (less accurate), ML ranking (overengineering for v1)

## Performance Benchmark Research

### Target Hardware Specifications
- **CPU**: Intel i5 or equivalent (4+ cores)
- **RAM**: 16GB (allows 1M photo indexing)
- **Storage**: SSD preferred for thumbnail cache

### Expected Performance Characteristics
- **Indexing throughput**: 100k photos/day on target hardware
- **Search latency**: <2s for text/filter queries, <5s for vector queries
- **Memory usage**: <512MB during normal operation
- **Storage overhead**: ~10% of original photo size for metadata + thumbnails

## Security and Privacy Research

### Data Encryption Strategy
**Decision**: SQLite encryption for face data, OS keystore for keys
**Rationale**: Transparent encryption at database level, secure key management via platform APIs.
**Alternatives considered**: Application-level encryption (complexity), no encryption (privacy risk)

### Installation Security
**Decision**: Code signing with timestamping
**Rationale**: Prevents tampering, enables Windows SmartScreen bypass, user trust.
**Alternatives considered**: No signing (user warnings), self-signed (still shows warnings)

## Risk Mitigation Strategies

### Large Library Performance
- Incremental indexing with checkpoints
- FAISS index optimization (IVF,PQ configuration)
- Thumbnail cache LRU eviction
- Background processing with UI priority

### Drive Letter Changes (Windows)
- Device ID to logical name mapping
- Hash-based file relinking
- Graceful handling of offline drives

### Poor Scan Quality (Reverse Search)
- Manual cropping interface
- Confidence score display
- Multiple embedding strategies

## UX Enhancement Technology Decisions (v1.0 Market-Ready)

### Virtual Scrolling Library
**Decision**: TanStack Virtual 3.x
**Rationale**: React 19 compatible, TypeScript-first, lightweight (4KB gzipped), supports dynamic row heights for mixed aspect ratios. Active maintenance by TanStack team.
**Alternatives considered**: react-window (lacks TypeScript-first design), react-virtualized (legacy, 28KB), custom implementation (too complex)

### Photo Lightbox Component
**Decision**: Custom implementation with Framer Motion 11.x
**Rationale**: Full control over keyboard shortcuts, swipe gestures, metadata overlay positioning. Framer Motion provides smooth 60fps hardware-accelerated animations. Tight integration with existing photo metadata API.
**Alternatives considered**: yet-another-react-lightbox (45KB, opinionated styling), react-image-lightbox (outdated, React 16), photoswipe (jQuery-based)

### Background Job Queue
**Decision**: ARQ 0.26+ with fakeredis (embedded)
**Rationale**: Python-native async library, integrates seamlessly with FastAPI. Uses in-memory Redis (fakeredis) eliminating external broker dependency. Full type hints, Pydantic V2 compatible. Built-in progress tracking for UI updates.
**Alternatives considered**: Celery (requires Redis/RabbitMQ broker, over-engineered), RQ (still needs Redis server), custom SQLite queue (no retry/error handling)

### Desktop Installer Build Tool
**Decision**: electron-builder 25.x
**Rationale**: Industry standard (VS Code, Slack, Discord use it). Single config for macOS (.dmg/.pkg), Windows (.exe), Linux (.AppImage/.deb). Built-in code signing support, integrates with electron-updater for delta updates. LZMA compression reduces installer size 40-60%.
**Alternatives considered**: electron-forge (more modular but requires more config, less mature signing), electron-packager (low-level, no signing or updates)

### Auto-Update Strategy
**Decision**: electron-updater 6.x with GitHub Releases
**Rationale**: Privacy-first (no external update servers, uses GitHub Releases API). Delta updates save bandwidth. Rollback support if update fails. Silent background downloads, applies on restart. Validates code signatures before applying.
**Alternatives considered**: Electron's built-in (deprecated in v38+), custom solution (complex delta updates), Squirrel.Windows (Windows-only)

### Onboarding State Management
**Decision**: Zustand 5.0 + localStorage persistence
**Rationale**: Already used in existing app for global state. Built-in persist middleware. Minimal boilerplate compared to Redux/MobX. Full TypeScript support with immer middleware.
**Alternatives considered**: Redux (too much boilerplate), MobX (less TypeScript support), Context API (performance issues with frequent updates)

### Batch Selection State Management
**Decision**: Custom Zustand hook with Set<number> for IDs
**Rationale**: Handles complex state (selected IDs, selection mode, Shift+Click range selection). Zustand's shallow equality checks prevent unnecessary re-renders. Reusable across SearchPage, CollectionsPage, PeoplePage.
**Performance target**: Handle 10K+ photo selections without UI lag

### Thumbnail Lazy Loading Strategy
**Decision**: IntersectionObserver API with TanStack Virtual
**Rationale**: Native browser API (no library needed). Only loads thumbnails in viewport + overscan area (200px margin). Memory efficient - unloads off-screen images automatically. Works seamlessly with TanStack Virtual's viewport calculations.
**Performance target**: <100ms thumbnail load latency, <200MB memory for viewport

## Development Phase Dependencies

**Phase 1 Prerequisites**: All research complete, no blocking unknowns
**Critical Path Items**: FAISS integration, ONNX model deployment, Electron-Python IPC, Virtual scrolling integration, Code signing setup
**Risk Items**: Performance tuning for large libraries (100K+ photos), Windows/macOS code signing setup, Auto-update testing across platforms
