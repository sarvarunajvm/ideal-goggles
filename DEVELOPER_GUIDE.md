# Photo Search & Navigation - Developer Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Backend Development](#backend-development)
5. [Frontend Development](#frontend-development)
6. [Testing Strategy](#testing-strategy)
7. [Deployment & Packaging](#deployment--packaging)
8. [Contributing Guidelines](#contributing-guidelines)

---

## Architecture Overview

Photo Search & Navigation is built as a local-first desktop application with the following architecture:

### Technology Stack
- **Frontend**: React + TypeScript + Electron
- **Backend**: Python + FastAPI + SQLite
- **AI/ML**: ONNX Runtime + CLIP + Tesseract OCR
- **Search**: SQLite FTS5 + FAISS vector database
- **Testing**: Jest (frontend) + pytest (backend) + Playwright (e2e)

### Core Components

#### Backend Services
- **FastAPI Server**: REST API for all operations
- **SQLite Database**: Photo metadata and search indexes
- **FAISS Vector Store**: Semantic similarity search
- **Worker Processes**: Async photo processing pipeline
- **File System Monitor**: Real-time file change detection

#### Frontend Application
- **Electron Main Process**: System integration and IPC
- **React Renderer**: User interface and interaction
- **State Management**: Zustand for global state
- **API Client**: Axios-based HTTP client with caching

### Design Principles
- **Privacy-First**: All processing happens locally
- **Performance**: Sub-second search across large collections
- **Scalability**: Handle 100k+ photo collections
- **Reliability**: Robust error handling and recovery
- **Cross-Platform**: Windows, macOS, and Linux support

---

## Development Setup

### Prerequisites
- **Node.js 18+** and **pnpm** for frontend development
- **Python 3.11+** and **poetry** for backend development
- **Git** for version control

### Quick Start
```bash
# Clone the repository
git clone https://github.com/photo-search/app.git
cd photo-search-app

# Setup backend
cd backend
poetry install
poetry run python -m pytest  # Run backend tests

# Setup frontend
cd ../frontend
pnpm install
pnpm run dev  # Start development server

# Start both services
pnpm run dev:full  # Starts both backend and frontend
```

### Environment Configuration

#### Backend Environment (.env)
```bash
# Database
DATABASE_URL=sqlite:///./data/photos.db
DATABASE_POOL_SIZE=20

# AI Models
CLIP_MODEL_PATH=./models/clip-vit-base-patch32
OCR_LANGUAGE=eng+fra+deu  # Tesseract languages
FACE_DETECTION_ENABLED=true

# Performance
MAX_WORKERS=4
THUMBNAIL_CACHE_SIZE=1000
VECTOR_INDEX_REBUILD_THRESHOLD=10000

# Development
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_CORS=true
```

#### Frontend Environment (.env.local)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Feature Flags
VITE_ENABLE_FACE_SEARCH=true
VITE_ENABLE_OCR_SEARCH=true
VITE_ENABLE_SEMANTIC_SEARCH=true

# Development
VITE_DEBUG=true
VITE_LOG_LEVEL=debug
```

---

## Project Structure

```
photo-search-app/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── api/               # FastAPI routes and endpoints
│   │   ├── core/              # Core business logic
│   │   ├── db/                # Database models and migrations
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # Business logic services
│   │   └── workers/           # Background processing workers
│   ├── tests/                 # Backend test suite
│   └── pyproject.toml         # Python dependencies
├── frontend/                  # React + Electron frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API clients and utilities
│   │   ├── stores/            # Zustand state stores
│   │   └── types/             # TypeScript type definitions
│   ├── electron/              # Electron main and preload scripts
│   ├── tests/                 # Frontend test suite
│   └── package.json           # Node.js dependencies
├── docs/                      # Documentation
├── specs/                     # Technical specifications
└── README.md                  # Project overview
```

### Key Directories Explained

#### Backend Structure
- `api/`: FastAPI route handlers and request/response models
- `core/`: Application configuration, logging, and utilities
- `db/`: SQLite schema, migrations, and database utilities
- `models/`: Pydantic models for data validation and serialization
- `services/`: Business logic (search, indexing, file processing)
- `workers/`: Background tasks (OCR, embeddings, thumbnails)

#### Frontend Structure
- `components/`: Reusable React components organized by feature
- `hooks/`: Custom hooks for state management and side effects
- `services/`: API clients, file system access, and OS integration
- `stores/`: Zustand stores for global application state
- `types/`: TypeScript interfaces and type definitions

---

## Backend Development

### FastAPI Application Structure

#### Core Application Setup
```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import health, search, config
from src.core.config import get_settings

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Photo Search API",
        version="1.0.0",
        description="Local photo search and navigation API"
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(search.router, prefix="/search", tags=["search"])
    app.include_router(config.router, prefix="/config", tags=["config"])

    return app
```

#### Database Models
```python
# src/models/photo.py
from sqlalchemy import Column, Integer, String, DateTime, Float
from src.db.base import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, index=True, nullable=False)
    folder = Column(String, index=True, nullable=False)
    size = Column(Integer, nullable=False)
    created_ts = Column(DateTime, nullable=False)
    modified_ts = Column(DateTime, nullable=False)
    sha1 = Column(String(40), unique=True, index=True)
```

#### Service Layer Example
```python
# src/services/search.py
class SearchService:
    def __init__(self, db: Session, vector_store: FAISSStore):
        self.db = db
        self.vector_store = vector_store

    async def search_photos(
        self,
        query: str,
        search_type: SearchType = SearchType.COMBINED,
        limit: int = 50
    ) -> SearchResponse:
        """Multi-modal photo search with ranking fusion."""

        results = []

        if search_type in [SearchType.TEXT, SearchType.COMBINED]:
            text_results = await self._text_search(query, limit)
            results.append(("text", text_results))

        if search_type in [SearchType.SEMANTIC, SearchType.COMBINED]:
            semantic_results = await self._semantic_search(query, limit)
            results.append(("semantic", semantic_results))

        # Rank fusion for combined results
        if len(results) > 1:
            final_results = self._fuse_rankings(results)
        else:
            final_results = results[0][1]

        return SearchResponse(
            results=final_results[:limit],
            total_count=len(final_results),
            query=query,
            search_type=search_type
        )
```

### Testing Backend Services

#### Unit Tests
```python
# tests/unit/test_search.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.search import SearchService

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_vector_store():
    store = Mock()
    store.search = AsyncMock(return_value=[])
    return store

@pytest.fixture
def search_service(mock_db, mock_vector_store):
    return SearchService(mock_db, mock_vector_store)

@pytest.mark.asyncio
async def test_search_photos_text_only(search_service):
    results = await search_service.search_photos(
        "test query",
        SearchType.TEXT
    )

    assert isinstance(results, SearchResponse)
    assert results.query == "test query"
```

### Performance Optimization

#### Database Indexing
```sql
-- Essential indexes for photo search
CREATE INDEX idx_photos_path ON photos(path);
CREATE INDEX idx_photos_folder ON photos(folder);
CREATE INDEX idx_photos_modified_ts ON photos(modified_ts DESC);
CREATE INDEX idx_photos_created_ts ON photos(created_ts DESC);

-- Full-text search index for OCR content
CREATE VIRTUAL TABLE ocr_fts USING fts5(
    file_id UNINDEXED,
    text,
    content='ocr',
    content_rowid='file_id'
);
```

#### Caching Strategy
```python
from functools import lru_cache
from typing import List
import aioredis

class CacheService:
    def __init__(self):
        self.redis = aioredis.Redis()

    @lru_cache(maxsize=1000)
    def get_thumbnail(self, photo_id: int) -> bytes:
        """In-memory thumbnail cache"""
        return self._generate_thumbnail(photo_id)

    async def get_search_results(self, query_hash: str) -> List[dict]:
        """Redis-backed search result cache"""
        cached = await self.redis.get(f"search:{query_hash}")
        if cached:
            return json.loads(cached)
        return None
```

---

## Frontend Development

### React Component Architecture

#### Component Organization
```typescript
// src/components/search/SearchInterface.tsx
interface SearchInterfaceProps {
  onSearch: (query: string) => void;
  loading: boolean;
  results: SearchResult[];
}

export const SearchInterface: React.FC<SearchInterfaceProps> = ({
  onSearch,
  loading,
  results
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <div className="search-interface">
      <SearchForm onSubmit={handleSubmit} />
      <SearchFilters />
      <ResultsGrid results={results} loading={loading} />
    </div>
  );
};
```

#### State Management with Zustand
```typescript
// src/stores/searchStore.ts
interface SearchState {
  query: string;
  results: SearchResult[];
  loading: boolean;
  filters: SearchFilters;
  setQuery: (query: string) => void;
  search: (query: string) => Promise<void>;
  updateFilters: (filters: Partial<SearchFilters>) => void;
}

export const useSearchStore = create<SearchState>((set, get) => ({
  query: '',
  results: [],
  loading: false,
  filters: DEFAULT_FILTERS,

  setQuery: (query) => set({ query }),

  search: async (query) => {
    set({ loading: true });
    try {
      const response = await searchAPI.search(query, get().filters);
      set({ results: response.results, loading: false });
    } catch (error) {
      console.error('Search failed:', error);
      set({ loading: false });
    }
  },

  updateFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters }
    }))
}));
```

### Electron Integration

#### Main Process Setup
```typescript
// electron/main.ts
import { app, BrowserWindow, ipcMain } from 'electron';
import { spawn } from 'child_process';
import path from 'path';

class PhotoSearchApp {
  private mainWindow: BrowserWindow | null = null;
  private backendProcess: any = null;

  async initialize() {
    await this.startBackend();
    this.createMainWindow();
    this.setupIPC();
  }

  private async startBackend() {
    const backendPath = path.join(__dirname, '../backend/dist/main.exe');
    this.backendProcess = spawn(backendPath, [], {
      stdio: 'pipe',
      detached: false
    });
  }

  private createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js')
      }
    });

    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.loadURL('http://localhost:3000');
    } else {
      this.mainWindow.loadFile('dist/index.html');
    }
  }

  private setupIPC() {
    ipcMain.handle('show-in-folder', async (_, filePath: string) => {
      const { shell } = await import('electron');
      shell.showItemInFolder(filePath);
    });
  }
}
```

#### Preload Script
```typescript
// electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

const electronAPI = {
  showInFolder: (filePath: string) =>
    ipcRenderer.invoke('show-in-folder', filePath),

  openFile: (filePath: string) =>
    ipcRenderer.invoke('open-file', filePath),

  getAppVersion: () =>
    ipcRenderer.invoke('get-app-version'),
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);
```

### Performance Optimization

#### Virtual Scrolling for Large Lists
```typescript
// src/components/VirtualGrid.tsx
import { FixedSizeGrid as Grid } from 'react-window';

interface VirtualGridProps {
  items: SearchResult[];
  itemSize: number;
  height: number;
  width: number;
}

export const VirtualGrid: React.FC<VirtualGridProps> = ({
  items,
  itemSize,
  height,
  width
}) => {
  const Cell = ({ columnIndex, rowIndex, style }) => {
    const index = rowIndex * COLUMNS_PER_ROW + columnIndex;
    const item = items[index];

    if (!item) return null;

    return (
      <div style={style}>
        <PhotoThumbnail photo={item} />
      </div>
    );
  };

  return (
    <Grid
      columnCount={COLUMNS_PER_ROW}
      rowCount={Math.ceil(items.length / COLUMNS_PER_ROW)}
      columnWidth={itemSize}
      rowHeight={itemSize}
      height={height}
      width={width}
    >
      {Cell}
    </Grid>
  );
};
```

---

## Testing Strategy

### Test Pyramid Structure

#### Unit Tests (70%)
- **Backend**: Service layer logic, data models, utilities
- **Frontend**: Components, hooks, utilities
- **Coverage Target**: 80%+ for critical paths

#### Integration Tests (20%)
- **API Integration**: End-to-end API workflows
- **Database Integration**: Data persistence and queries
- **File System Integration**: Photo processing pipelines

#### End-to-End Tests (10%)
- **User Workflows**: Complete user scenarios
- **Cross-Platform**: Test on target operating systems
- **Performance**: Load testing with large photo collections

### Backend Testing

#### Test Configuration
```python
# tests/conftest.py
import pytest
import tempfile
from sqlalchemy import create_engine
from src.db.base import Base
from src.main import create_app

@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def client(test_db):
    """Test client with test database"""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db

    with TestClient(app) as client:
        yield client
```

#### API Testing
```python
# tests/api/test_search.py
def test_search_endpoint(client):
    """Test search API endpoint"""
    response = client.post("/search", json={
        "query": "test query",
        "search_type": "text",
        "limit": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_count" in data
    assert data["query"] == "test query"
```

### Frontend Testing

#### Component Testing
```typescript
// tests/components/SearchInterface.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchInterface } from '@/components/search/SearchInterface';

describe('SearchInterface', () => {
  const mockOnSearch = jest.fn();

  beforeEach(() => {
    mockOnSearch.mockClear();
  });

  it('calls onSearch when form is submitted', () => {
    render(
      <SearchInterface
        onSearch={mockOnSearch}
        loading={false}
        results={[]}
      />
    );

    const input = screen.getByPlaceholderText('Search photos...');
    const submitButton = screen.getByRole('button', { name: 'Search' });

    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.click(submitButton);

    expect(mockOnSearch).toHaveBeenCalledWith('test query');
  });
});
```

#### E2E Testing with Playwright
```typescript
// tests/e2e/search.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Photo Search', () => {
  test('can search and view results', async ({ page }) => {
    await page.goto('/');

    // Enter search query
    await page.fill('[data-testid="search-input"]', 'vacation photos');
    await page.click('[data-testid="search-button"]');

    // Wait for results
    await page.waitForSelector('[data-testid="search-results"]');

    // Verify results are displayed
    const results = await page.$$('[data-testid="photo-card"]');
    expect(results.length).toBeGreaterThan(0);

    // Click on first result
    await page.click('[data-testid="photo-card"]:first-child');

    // Verify preview opens
    await expect(page.locator('[data-testid="photo-preview"]')).toBeVisible();
  });
});
```

---

## Deployment & Packaging

### Build Process

#### Backend Build
```bash
# Build Python application
poetry build
poetry run pyinstaller --onefile src/main.py

# Create distributable package
poetry run python setup.py bdist_wheel
```

#### Frontend Build
```bash
# Build React application
pnpm run build

# Package Electron application
pnpm run build:electron

# Create platform-specific installers
pnpm run dist:win    # Windows installer
pnpm run dist:mac    # macOS DMG
pnpm run dist:linux  # Linux AppImage/DEB
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/build.yml
name: Build and Test

on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: poetry install
      - run: poetry run pytest
      - run: poetry run ruff check

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: pnpm install
      - run: pnpm run test
      - run: pnpm run lint
      - run: pnpm run type-check

  build:
    needs: [test-backend, test-frontend]
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - name: Build application
        run: pnpm run build:electron
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: app-${{ matrix.os }}
          path: dist-electron/
```

### Release Management

#### Semantic Versioning
- **Major** (X.0.0): Breaking changes, new architecture
- **Minor** (X.Y.0): New features, backwards compatible
- **Patch** (X.Y.Z): Bug fixes, small improvements

#### Release Process
1. **Version Bump**: Update version in package.json and pyproject.toml
2. **Changelog**: Generate changelog from commit messages
3. **Build**: Create platform-specific builds
4. **Test**: Run full test suite on all platforms
5. **Sign**: Code sign executables (Windows/macOS)
6. **Release**: Create GitHub release with binaries
7. **Update**: Trigger auto-update mechanism

---

## Contributing Guidelines

### Code Style

#### Python (Backend)
- **Formatter**: Black with line length 100
- **Linter**: Ruff with strict settings
- **Type Checking**: mypy in strict mode
- **Import Sorting**: isort

#### TypeScript (Frontend)
- **Formatter**: Prettier
- **Linter**: ESLint with strict TypeScript rules
- **Style Guide**: Airbnb TypeScript configuration

### Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(search): add semantic search functionality
fix(db): resolve index corruption issue
docs(api): update search endpoint documentation
test(unit): add tests for photo model
perf(vector): optimize FAISS index performance
```

### Pull Request Process

1. **Fork & Branch**: Create feature branch from main
2. **Develop**: Implement changes with tests
3. **Test**: Ensure all tests pass locally
4. **Document**: Update documentation if needed
5. **Submit**: Create PR with clear description
6. **Review**: Address feedback from maintainers
7. **Merge**: Squash and merge when approved

### Development Workflow

#### Feature Development
```bash
# Start new feature
git checkout -b feat/semantic-search

# Make changes and test
pnpm run test
pnpm run lint

# Commit with conventional format
git commit -m "feat(search): implement semantic search with CLIP"

# Push and create PR
git push origin feat/semantic-search
```

#### Bug Fixes
```bash
# Start bug fix
git checkout -b fix/search-timeout

# Fix issue and add regression test
# ...

# Commit fix
git commit -m "fix(api): resolve search timeout for large queries"
```

### Performance Guidelines

#### Backend Performance
- **Database**: Use appropriate indexes and query optimization
- **Memory**: Limit memory usage, use streaming for large datasets
- **Concurrency**: Use async/await for I/O operations
- **Caching**: Implement caching at appropriate layers

#### Frontend Performance
- **Rendering**: Use React.memo and useMemo for expensive components
- **State**: Minimize state updates and re-renders
- **Assets**: Optimize images and lazy load components
- **Bundle**: Code splitting and tree shaking

### Security Considerations

#### Data Privacy
- **Local Processing**: All AI analysis must be local
- **No Telemetry**: No usage tracking or analytics
- **Secure Storage**: Encrypt sensitive data at rest
- **Minimal Permissions**: Request only necessary file access

#### Code Security
- **Dependencies**: Regular security audits
- **Input Validation**: Sanitize all user inputs
- **Error Handling**: Don't expose internal details
- **Logging**: Avoid logging sensitive information

---

*This developer guide covers the technical aspects of Photo Search & Navigation development. For user-facing documentation, see the User Manual.*