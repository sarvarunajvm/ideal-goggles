# 👨‍💻 Developer Guide - Ideal Googles

Comprehensive guide for developers working on the Ideal Goggles application.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Backend Development](#backend-development)
6. [Frontend Development](#frontend-development)
7. [Testing Strategy](#testing-strategy)
8. [Build & Deployment](#build--deployment)
9. [Troubleshooting](#troubleshooting)

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────┐
│           Electron Desktop App              │
├─────────────────────────────────────────────┤
│          React Frontend (Vite)              │
│         TypeScript + TailwindCSS            │
├─────────────────────────────────────────────┤
│         FastAPI Backend (Python)            │
│     Async REST API + WebSocket Support      │
├─────────────────────────────────────────────┤
│           ML Processing Layer               │
│    CLIP (Semantic) | ArcFace (Faces) |     │
│         Tesseract OCR | FAISS               │
├─────────────────────────────────────────────┤
│         SQLite Database (Local)             │
└─────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Single package.json**: Simplified dependency management
2. **No lock files**: Always fresh dependencies, better for desktop apps
3. **PNPM only**: Fast, efficient package management
4. **Local-first**: All processing on user's machine for privacy
5. **Modular architecture**: Clean separation of concerns

## Development Setup

### Prerequisites

```bash
# Required software
node --version  # 18+
pnpm --version  # 10+
python3 --version  # 3.11+
make --version  # GNU Make
```

### Quick Start

```bash
# Clone and setup
git clone https://github.com/sarvarunajvm/ideal-goggles.git
cd ideal-goggles

# Install everything
make install

# Start development
make dev
```

### Manual Setup

```bash
# Frontend dependencies (PNPM, no lock file)
pnpm install --no-lockfile

# Backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cd ..

# Start services
pnpm run dev
```

## Project Structure

### Directory Layout

```
ideal-goggles/
├── backend/              # Python FastAPI backend
│   ├── src/
│   │   ├── api/         # REST endpoints
│   │   ├── core/        # Business logic
│   │   ├── models/      # Data models
│   │   └── main.py      # Entry point
│   └── pyproject.toml   # Python config
│
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/      # Page components
│   │   ├── services/   # API clients
│   │   └── App.tsx     # Root component
│   └── vite.config.ts  # Vite config
│
├── electron/           # Electron wrapper
│   ├── main.ts        # Main process
│   └── preload.ts     # Preload scripts
│
├── package.json       # Single package.json
├── Makefile          # Build automation
└── .gitignore        # Excludes lock files
```

### Configuration Files

- `package.json` - All Node.js dependencies and scripts
- `Makefile` - Build automation and commands
- `.gitignore` - Includes `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`
- No `pnpm-workspace.yaml` - Single package structure

## Development Workflow

### Branch Strategy

```
main              # Production releases
├── develop       # Integration branch
└── feature/*     # Feature branches
    bugfix/*      # Bug fixes
    hotfix/*      # Emergency fixes
```

### Development Commands

```bash
# Start everything
make dev
# OR
pnpm run dev

# Backend only
pnpm run dev:backend
# OR
make backend-dev

# Frontend only
pnpm run dev:frontend

# Electron only
pnpm run dev:electron
```

### Code Quality

```bash
# Linting
pnpm run lint          # Frontend
make backend-lint      # Backend (ruff)

# Formatting
pnpm run lint:fix      # Frontend
make backend-format    # Backend (black)

# Type checking
pnpm run type-check    # Frontend
make backend-typecheck # Backend (mypy)
```

## Backend Development

### API Structure

```python
# src/api/search.py
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/photos")
async def search_photos(
    q: str = Query(..., description="Search query"),
    mode: str = Query("semantic", regex="^(text|semantic|face|similar)$"),
    limit: int = Query(50, ge=1, le=100)
) -> List[PhotoResult]:
    """Search photos with different modes."""
    try:
        results = await search_service.search(q, mode, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Database Models

```python
# src/models/database.py
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True)
    path = Column(String, unique=True, index=True)
    filename = Column(String)
    size = Column(Float)
    created_at = Column(DateTime)
    embedding = Column(String)  # JSON serialized
    faces = Column(String)       # JSON serialized
    ocr_text = Column(String)
```

### Running Backend

```bash
# Development server
cd backend
.venv/bin/python -m src.main

# With auto-reload
.venv/bin/python -m uvicorn src.main:app --reload --port 5555

# API docs available at:
# http://localhost:5555/docs (Swagger)
# http://localhost:5555/redoc (ReDoc)
```

## Frontend Development

### Component Structure

```tsx
// src/components/PhotoCard.tsx
import React from 'react';
import { Photo } from '@/types';
import { Card } from '@/components/ui/card';

interface PhotoCardProps {
  photo: Photo;
  selected?: boolean;
  onSelect?: (photo: Photo) => void;
}

export const PhotoCard: React.FC<PhotoCardProps> = ({
  photo,
  selected = false,
  onSelect
}) => {
  return (
    <Card
      className={`cursor-pointer ${selected ? 'ring-2' : ''}`}
      onClick={() => onSelect?.(photo)}
    >
      <img
        src={photo.thumbnail}
        alt={photo.filename}
        loading="lazy"
      />
      <p className="truncate">{photo.filename}</p>
    </Card>
  );
};
```

### State Management (Zustand)

```tsx
// src/stores/searchStore.ts
import { create } from 'zustand';

interface SearchStore {
  query: string;
  results: Photo[];
  loading: boolean;
  setQuery: (query: string) => void;
  search: () => Promise<void>;
}

export const useSearchStore = create<SearchStore>((set, get) => ({
  query: '',
  results: [],
  loading: false,

  setQuery: (query) => set({ query }),

  search: async () => {
    set({ loading: true });
    try {
      const response = await apiClient.search(get().query);
      set({ results: response.data, loading: false });
    } catch (error) {
      set({ loading: false });
    }
  }
}));
```

### API Client

```tsx
// src/services/apiClient.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5555';

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

export const searchAPI = {
  search: (query: string, mode = 'semantic') =>
    apiClient.get('/search/photos', { params: { q: query, mode } }),

  getSimilar: (photoId: string) =>
    apiClient.get(`/search/similar/${photoId}`),

  indexFolder: (path: string) =>
    apiClient.post('/index/folder', { path }),
};
```

## Testing Strategy

### Frontend Testing

```bash
# Unit tests
pnpm run test:unit

# Component tests
pnpm run test:components

# All tests
pnpm run test
```

Example test:

```tsx
// tests/components/PhotoCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { PhotoCard } from '@/components/PhotoCard';

describe('PhotoCard', () => {
  it('calls onSelect when clicked', () => {
    const mockSelect = jest.fn();
    const photo = { id: '1', filename: 'test.jpg' };

    render(<PhotoCard photo={photo} onSelect={mockSelect} />);
    fireEvent.click(screen.getByText('test.jpg'));

    expect(mockSelect).toHaveBeenCalledWith(photo);
  });
});
```

### Backend Testing

```bash
# Run all tests
make backend-test

# With coverage
cd backend
.venv/bin/pytest --cov=src --cov-report=html
```

Example test:

```python
# backend/tests/test_search.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_search_photos():
    response = client.get("/search/photos?q=sunset")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Build & Deployment

### Local Builds

```bash
# Quick builds
pnpm run build          # Frontend only
make backend-package    # Backend binary

# Full distribution builds
make dist-mac          # macOS DMG
make dist-win          # Windows installer
make dist-all          # All platforms
```

### CI/CD Pipeline

GitHub Actions automatically:
1. Runs tests on PR
2. Builds releases on version tags
3. Creates GitHub releases

### Creating a Release

```bash
# 1. Update version
npm version patch  # or minor/major

# 2. Commit and tag
git commit -am "Release v1.0.9"
git tag v1.0.9

# 3. Push to trigger release
git push origin main --tags
```

### Build Output

```
dist-electron/
├── ideal-googles-1.0.9.dmg        # macOS
├── ideal-googles-1.0.9.exe        # Windows
├── ideal-googles-1.0.9.AppImage   # Linux
└── ideal-googles-1.0.9.deb        # Debian/Ubuntu
```

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Kill process on port 5555
lsof -ti:5555 | xargs kill -9
```

**Electron won't start:**
```bash
# Rebuild Electron
rm -rf node_modules electron/dist
pnpm install --no-lockfile
pnpm run build:electron:main
```

**Backend import errors:**
```bash
# Reinstall backend
cd backend
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

**Frontend build fails:**
```bash
# Clean and rebuild
rm -rf node_modules frontend/dist
pnpm install --no-lockfile
pnpm run build:frontend
```

### Debug Mode

```bash
# Enable debug logging
DEBUG=true pnpm run dev

# Electron DevTools
# Press Ctrl+Shift+I in app

# Backend debug
cd backend
DEBUG=true .venv/bin/python -m src.main
```

## Best Practices

### Code Style

- **TypeScript**: Strict mode, explicit types
- **Python**: Type hints, docstrings
- **Commits**: Conventional commits (feat:, fix:, docs:)
- **PRs**: Small, focused, with tests

### Performance

- Lazy load components
- Virtual scrolling for large lists
- Batch API requests
- Cache thumbnails locally
- Use WebP for thumbnails

### Security

- Sanitize all inputs
- No eval() or dynamic imports
- Validate file paths
- Rate limit API endpoints
- No external dependencies for core features

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Electron Docs](https://www.electronjs.org/)
- [Vite Docs](https://vitejs.dev/)
- [PNPM Docs](https://pnpm.io/)

---

Need help? Check [GitHub Issues](https://github.com/sarvarunajvm/ideal-goggles/issues) or create a new one!
