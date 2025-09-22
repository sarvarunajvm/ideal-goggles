# Research Findings: Photo Search and Navigation System

## Technology Stack Research

### Frontend Framework Decision
**Decision**: Electron + React + TypeScript
**Rationale**: Cross-platform desktop requirement with rich UI interactions. Electron provides native OS integration for "reveal in folder" functionality. React ecosystem mature for complex search interfaces.
**Alternatives considered**: Tauri (smaller bundle but less mature), Qt (native but steeper learning curve)

### Backend Framework Decision
**Decision**: Python 3.11 + FastAPI
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

## Development Phase Dependencies

**Phase 1 Prerequisites**: All research complete, no blocking unknowns
**Critical Path Items**: FAISS integration, ONNX model deployment, Electron-Python IPC
**Risk Items**: Performance tuning for large libraries, Windows installer signing setup