# Developer Guide

Technical reference for Ideal Goggles architecture, patterns, and advanced development.

> **New to the project?** Start with [CONTRIBUTING.md](CONTRIBUTING.md) for setup and workflow.

## Architecture

### System Layers

```
┌─────────────────────────────────────────────┐
│          Electron Desktop App               │
│  - Main Process (Node.js)                   │
│  - Preload Scripts (IPC bridge)             │
│  - Auto-updater                             │
├─────────────────────────────────────────────┤
│         React Frontend (Port 3333)          │
│  - UI Components (shadcn/ui)                │
│  - State Management (Zustand)               │
│  - API Client (Axios)                       │
│  - Routing (React Router)                   │
├─────────────────────────────────────────────┤
│        FastAPI Backend (Port 5555)          │
│  - REST API Endpoints                       │
│  - Async Request Handlers                   │
│  - WebSocket Support (future)               │
├─────────────────────────────────────────────┤
│           Service Layer                     │
│  - Photo Indexing                           │
│  - Search Implementations                   │
│  - Thumbnail Generation                     │
├─────────────────────────────────────────────┤
│            ML Layer (Optional)              │
│  - CLIP Embeddings (semantic search)        │
│  - InsightFace (face recognition)           │
│  - Tesseract OCR (text extraction)          │
│  - FAISS (vector similarity)                │
├─────────────────────────────────────────────┤
│           Data Layer                        │
│  - SQLAlchemy ORM                           │
│  - SQLite Database (local file)             │
│  - Alembic Migrations                       │
└─────────────────────────────────────────────┘
```

### Key Design Decisions

**1. Single Package.json**
- All Node.js dependencies in root
- Simplified script orchestration
- Consistent dependency versions

**2. PNPM Without Lock Files**
- Faster than npm/yarn
- Disk space efficient
- No lock files = always fresh dependencies
- Trade-off: reproducibility vs. freshness

**3. Local-First Architecture**
- All processing on user's machine
- No cloud dependencies
- Privacy by design
- Graceful degradation when ML unavailable

**4. Async-First Backend**
- FastAPI with async/await
- Non-blocking I/O for indexing
- Background workers for heavy tasks

**5. Electron Multi-Process**
- Main process: Node.js, backend lifecycle
- Renderer: React app in Chromium
- Preload: Secure IPC bridge

## Data Flow

### Photo Indexing

```
User adds folder
    ↓
Indexing API call → Backend
    ↓
Discovery Phase: Find all image files
    ↓
Metadata Phase: Extract EXIF, dimensions, dates
    ↓
OCR Phase (optional): Extract text from images
    ↓
Embedding Phase (optional): Generate CLIP vectors
    ↓
Face Phase (optional): Detect and encode faces
    ↓
Thumbnail Phase: Generate preview images
    ↓
Database: Store all metadata
    ↓
Frontend: Update UI with progress
```

### Search Flow

```
User enters query
    ↓
Frontend: Determine search mode
    ↓
API Request → Backend
    ↓
Search Service:
  - Text: SQL LIKE queries + OCR text
  - Semantic: CLIP embedding similarity
  - Face: InsightFace vector comparison
  - Similar: Image embedding distance
    ↓
Results ranked by relevance/similarity
    ↓
Frontend: Display photo grid
```

## Backend Architecture

### Directory Structure

```
backend/src/
├── api/                    # FastAPI routers
│   ├── search.py          # Search endpoints
│   ├── photos.py          # Photo CRUD
│   ├── index.py           # Indexing control
│   └── people.py          # Face management
│
├── core/                   # Core business logic
│   ├── config.py          # App configuration
│   ├── indexer.py         # Photo discovery
│   └── logging_config.py  # Logging setup
│
├── db/                     # Database layer
│   ├── session.py         # SQLAlchemy setup
│   └── migrations/        # Alembic migrations
│
├── models/                 # Data models
│   ├── database.py        # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
│
├── services/               # Feature implementations
│   ├── embedding.py       # CLIP embeddings
│   ├── face_search.py     # Face recognition
│   ├── ocr.py             # Text extraction
│   ├── thumbnail.py       # Image resizing
│   └── faiss_manager.py   # Vector search
│
├── workers/                # Background tasks
│   └── indexing.py        # Async indexing
│
└── main.py                 # Application entry
```

### Database Schema

**Photos Table:**
```python
class Photo(Base):
    id: str (UUID)
    path: str (unique, indexed)
    filename: str
    size: int (bytes)
    width: int
    height: int
    created_at: datetime
    modified_at: datetime
    camera_make: str (optional)
    camera_model: str (optional)
    ocr_text: str (optional)
    embedding: str (JSON, CLIP vector)
    thumbnail_path: str
```

**People Table:**
```python
class Person(Base):
    id: str (UUID)
    name: str
    created_at: datetime
    face_encodings: str (JSON, list of vectors)
    photo_count: int
```

**Photo-Person Association:**
```python
class PhotoPerson(Base):
    photo_id: str (FK)
    person_id: str (FK)
    confidence: float (0.0-1.0)
    face_box: str (JSON, [x, y, w, h])
```

### API Patterns

**Async Route Handlers:**
```python
@router.get("/photos/{photo_id}")
async def get_photo(photo_id: str) -> PhotoResponse:
    async with get_session() as session:
        photo = await session.get(Photo, photo_id)
        if not photo:
            raise HTTPException(404, "Photo not found")
        return PhotoResponse.from_orm(photo)
```

**Dependency Injection:**
```python
from fastapi import Depends
from src.services.search import SearchService

def get_search_service() -> SearchService:
    return SearchService()

@router.get("/search")
async def search(
    q: str,
    service: SearchService = Depends(get_search_service)
):
    return await service.search(q)
```

**Error Handling:**
```python
from src.core.logging_config import get_logger

logger = get_logger(__name__)

try:
    result = await risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(500, detail=str(e))
```

## Frontend Architecture

### Directory Structure

```
frontend/src/
├── components/            # React components
│   ├── ui/               # shadcn/ui primitives
│   ├── PhotoGrid/        # Photo display
│   ├── SearchBar/        # Search interface
│   └── Lightbox/         # Photo viewer
│
├── pages/                # Page components
│   ├── MainPage.tsx      # Photo grid
│   ├── SearchPage.tsx    # Search results
│   ├── PeoplePage.tsx    # Face management
│   └── SettingsPage.tsx  # Configuration
│
├── services/             # API clients
│   ├── api.ts           # Axios instance
│   ├── photos.ts        # Photo endpoints
│   └── search.ts        # Search endpoints
│
├── stores/               # Zustand stores
│   ├── searchStore.ts   # Search state
│   ├── photoStore.ts    # Photo state
│   └── settingsStore.ts # Settings state
│
├── types/                # TypeScript types
│   └── index.ts         # Shared types
│
└── utils/                # Utilities
    ├── logger.ts        # Logging utility
    └── format.ts        # Formatting helpers
```

### State Management Pattern

```typescript
// stores/photoStore.ts
import { create } from 'zustand';

interface PhotoStore {
  photos: Photo[];
  selectedIds: Set<string>;
  loading: boolean;

  setPhotos: (photos: Photo[]) => void;
  toggleSelection: (id: string) => void;
  clearSelection: () => void;
}

export const usePhotoStore = create<PhotoStore>((set) => ({
  photos: [],
  selectedIds: new Set(),
  loading: false,

  setPhotos: (photos) => set({ photos }),

  toggleSelection: (id) => set((state) => {
    const newSet = new Set(state.selectedIds);
    newSet.has(id) ? newSet.delete(id) : newSet.add(id);
    return { selectedIds: newSet };
  }),

  clearSelection: () => set({ selectedIds: new Set() })
}));
```

### API Client Pattern

```typescript
// services/api.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5555';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

// services/photos.ts
export const photoAPI = {
  search: (query: string, mode: 'text' | 'semantic' | 'face') =>
    api.get('/search/photos', { params: { q: query, mode } }),

  getById: (id: string) =>
    api.get(`/photos/${id}`),

  startIndexing: (paths: string[]) =>
    api.post('/index/start', { paths }),
};
```

## Electron Integration

### Main Process (Node.js)

```typescript
// frontend/electron/main.ts
import { app, BrowserWindow } from 'electron';
import { spawn } from 'child_process';

let backendProcess: ChildProcess;
let mainWindow: BrowserWindow;

async function startBackend() {
  const pythonPath = /* platform-specific path */;
  backendProcess = spawn(pythonPath, ['-m', 'src.main']);

  // Wait for backend to be ready
  await waitForBackend('http://localhost:5555/health');
}

app.on('ready', async () => {
  await startBackend();

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadURL('http://localhost:3333');
});

app.on('quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
```

### Preload Script (IPC Bridge)

```typescript
// frontend/electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electron', {
  selectFolder: () => ipcRenderer.invoke('dialog:openDirectory'),
  getAppVersion: () => ipcRenderer.invoke('app:getVersion'),
  // Expose only safe, specific APIs
});
```

## ML Integration

### CLIP Embeddings

```python
# services/embedding.py
import torch
import clip
from typing import List
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text query."""
        text_input = clip.tokenize([text]).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_text(text_input)
            embedding /= embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy()[0].tolist()

    async def embed_image(self, image_path: str) -> List[float]:
        """Generate embedding for image."""
        from PIL import Image
        image = Image.open(image_path)
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_image(image_input)
            embedding /= embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy()[0].tolist()
```

### Face Recognition

```python
# services/face_search.py
import insightface
from insightface.app import FaceAnalysis

class FaceService:
    def __init__(self):
        self.app = FaceAnalysis(name='buffalo_l')
        self.app.prepare(ctx_id=0)

    async def detect_faces(self, image_path: str) -> List[Face]:
        """Detect faces in image."""
        import cv2
        img = cv2.imread(image_path)
        faces = self.app.get(img)

        return [
            Face(
                embedding=face.normed_embedding.tolist(),
                bbox=[int(x) for x in face.bbox],
                confidence=float(face.det_score)
            )
            for face in faces
        ]
```

## Build & Deployment

### Development Build

```bash
# Frontend only
pnpm run build

# Backend only
cd backend && make package

# Full Electron app
pnpm run build:electron
```

### Production Build

```bash
# macOS
pnpm run dist:mac

# Windows
pnpm run dist:win

# Linux
pnpm run dist:linux

# All platforms
pnpm run dist:all
```

### Build Configuration

**electron-builder.json:**
```json
{
  "productName": "Ideal Goggles",
  "appId": "com.idealgoggles.app",
  "directories": {
    "output": "dist-electron"
  },
  "files": [
    "frontend/dist/**/*",
    "backend/dist/**/*"
  ],
  "mac": {
    "category": "public.app-category.photography",
    "target": ["dmg", "zip"]
  },
  "win": {
    "target": ["nsis"]
  },
  "linux": {
    "target": ["AppImage", "deb"]
  }
}
```

## Performance Optimization

### Backend

**1. Database Indexing:**
```python
# Ensure critical fields are indexed
class Photo(Base):
    path = Column(String, unique=True, index=True)
    created_at = Column(DateTime, index=True)
    # Composite index for common queries
    __table_args__ = (
        Index('idx_date_path', 'created_at', 'path'),
    )
```

**2. Query Optimization:**
```python
# Use select loading to avoid N+1
from sqlalchemy.orm import selectinload

photos = await session.execute(
    select(Photo)
    .options(selectinload(Photo.people))
    .limit(100)
)
```

**3. Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_thumbnail_path(photo_id: str) -> str:
    return f"cache/thumbnails/{photo_id}.webp"
```

### Frontend

**1. Virtual Scrolling:**
```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const virtualizer = useVirtualizer({
  count: photos.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 200,
  overscan: 5
});
```

**2. Image Lazy Loading:**
```typescript
<img
  src={photo.thumbnail}
  loading="lazy"
  decoding="async"
/>
```

**3. Debounced Search:**
```typescript
import { useDebouncedCallback } from 'use-debounce';

const debouncedSearch = useDebouncedCallback(
  (query: string) => {
    searchAPI.search(query);
  },
  300
);
```

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\          P2: Weekly (~15 min)
       /------\
      /  API  \        P1: Nightly (~5 min)
     /----------\
    /   Unit     \     P0: Every PR (~15 sec)
   /--------------\
```

### Priority Levels

**P0 - Critical (CI on every PR):**
- Runtime: ~15 seconds
- App loads, API health, basic search, navigation
- Blocks merging if fails
- Command: `pnpm test:p0`

**P1 - Important (Nightly):**
- Runtime: ~5 minutes
- All search modes, settings, filters, responsive design
- Command: `pnpm test:p1`

**P2 - Extended (Weekly):**
- Runtime: ~15 minutes
- People management, face search, performance tests
- Command: `pnpm test:p2`

### Test Organization

**Backend (pytest):**
```bash
# All tests
pytest

# By type
pytest -m unit           # Fast, isolated
pytest -m contract       # API contracts
pytest -m integration    # DB + services
pytest -m "not performance"  # Skip slow tests

# With coverage
pytest --cov=src --cov-report=html
```

**Frontend (Jest):**
```bash
# All tests
pnpm test

# With coverage
pnpm test:coverage

# Watch mode
pnpm test:watch
```

**E2E (Playwright):**
```bash
cd func_tests

# All E2E tests
pnpm test

# Quick smoke tests
pnpm test:smoke

# Interactive UI
pnpm test:ui

# Specific priority
pnpm exec playwright test --grep @P0
```

### Coverage Targets

- **Backend**: 70%+ line coverage
- **Frontend**: 60%+ line coverage
- **E2E**: Critical user paths (P0/P1)

### CI/CD Pipeline

**On every PR:**
1. Lint check (ESLint, Ruff)
2. Type check (TypeScript, mypy)
3. Unit tests (Backend + Frontend)
4. P0 E2E tests (~15 sec)

**Nightly:**
1. Full test suite
2. Coverage reports
3. Performance benchmarks

**On release:**
1. All tests pass
2. Build all platforms
3. Smoke test installers

## Git Hooks

Pre-commit and pre-push hooks enforce code quality automatically.

### Pre-commit Hook

Runs before every commit to catch issues early:

**Frontend checks:**
- ❌ Blocks `console.log()` statements (use logger instead)
- ❌ Blocks `debugger` statements
- ❌ Runs ESLint on staged files
- ❌ Runs TypeScript type check

**Backend checks:**
- ⚠️ Warns on `print()` statements (use logger)
- ❌ Blocks `breakpoint()` and `pdb` statements
- ❌ Runs Ruff linter on staged files

**Installation:**
```bash
# Automatic via postinstall
pnpm install

# Manual installation
bash scripts/setup-hooks.sh
```

**Bypass (use sparingly):**
```bash
git commit --no-verify
```

### Pre-push Hook

Prevents version mismatches on releases:
- Checks `package.json` version matches git tag
- Checks `backend/pyproject.toml` version matches tag

**Fix version mismatch:**
```bash
pnpm run version:update 1.0.27
```

### Hook Files

- **Source**: `scripts/git-hooks/pre-commit`, `scripts/git-hooks/pre-push`
- **Installed**: `.git/hooks/` (copied by setup script)
- **Uses**: pnpm for all linting/type-check operations

## Security Best Practices

**1. Input Validation:**
```python
from pydantic import BaseModel, validator

class SearchRequest(BaseModel):
    query: str
    mode: str

    @validator('query')
    def validate_query(cls, v):
        if len(v) > 1000:
            raise ValueError('Query too long')
        return v
```

**2. Path Traversal Prevention:**
```python
import os
from pathlib import Path

def safe_path_join(base: str, user_path: str) -> str:
    base_path = Path(base).resolve()
    full_path = (base_path / user_path).resolve()

    if not full_path.is_relative_to(base_path):
        raise ValueError("Path traversal detected")

    return str(full_path)
```

**3. No Secrets in Code:**
```bash
# Use environment variables
DATABASE_URL=sqlite:///./data/photos.db
API_KEY=${API_KEY}  # Never hardcode

# backend/.env.example shows required vars
# backend/.env is gitignored
```

## Troubleshooting

### Common Development Issues

**Port conflicts:**
```bash
# Kill stuck processes
lsof -ti:5555 | xargs kill -9  # Backend
lsof -ti:3333 | xargs kill -9  # Frontend
```

**Import errors:**
```bash
# Backend: Reinstall in editable mode
cd backend && pip install -e ".[dev]"

# Frontend: Clear cache
rm -rf node_modules .vite && pnpm install
```

**Database locked:**
```bash
# SQLite write lock - close all connections
# Or delete and recreate (loses data)
rm backend/data/photos.db
```

## Resources

**Official Documentation:**
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Electron](https://www.electronjs.org/)
- [PNPM](https://pnpm.io/)
- [Zustand](https://github.com/pmndrs/zustand)

**Project Documentation:**
- [User Manual](USER_MANUAL.md) - End-user guide
- [Contributing](CONTRIBUTING.md) - Setup and workflow
- [ML Setup](ML_SETUP.md) - AI features and model installation

---

**Questions?** Check [GitHub Discussions](https://github.com/sarvarunajvm/ideal-goggles/discussions) or open an issue.
