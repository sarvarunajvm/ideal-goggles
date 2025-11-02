# Contributing to Ideal Goggles

Thank you for your interest in contributing! This guide will help you get started quickly and efficiently.

## Quick Start

### Setup

```bash
# Clone and install
git clone https://github.com/sarvarunajvm/ideal-goggles.git
cd ideal-goggles

# Install dependencies (requires Node.js 18+, Python 3.12+, pnpm 10+)
pnpm install
make backend-install

# Start development
pnpm run dev
```

Your dev environment is ready when you see:
- Backend running on http://localhost:5555
- Frontend running on http://localhost:3333
- Electron app window opens

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test locally
   ```bash
   # Run tests
   make backend-test
   pnpm test

   # Check code quality
   make backend-lint
   pnpm run lint
   ```

3. **Commit with meaningful message**
   ```bash
   git commit -m "feat: add your feature description"
   ```

   Pre-commit hooks will automatically:
   - Check for `console.log` and `debugger` statements
   - Run ESLint and TypeScript checks
   - Run Ruff linter on Python code

4. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

[📖 Development Guide](DEVELOPER_GUIDE.md) for detailed architecture and workflows

## Project Structure

```
ideal-goggles/
├── backend/              # Python FastAPI backend
│   ├── src/
│   │   ├── api/         # REST API endpoints
│   │   ├── core/        # Business logic
│   │   └── models/      # Data models
│   └── tests/           # Backend tests (pytest)
│
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Page components
│   │   └── services/    # API clients
│   └── tests/           # Frontend tests (Jest)
│
├── frontend/electron/   # Electron desktop wrapper
└── func_tests/          # E2E tests (Playwright)
```

## Development Workflow

### Commands Reference

```bash
# Development
pnpm run dev              # Start everything (recommended)
make backend-dev          # Backend only
pnpm run dev:frontend     # Frontend only

# Testing
make backend-test         # Python tests
pnpm test                 # Frontend tests
pnpm run e2e              # End-to-end tests

# Code Quality
make backend-lint         # Ruff (Python linter)
make backend-format       # Black (Python formatter)
pnpm run lint             # ESLint + TypeScript
pnpm run type-check       # TypeScript only

# Building
pnpm run build            # Build frontend
make backend-package      # Package Python backend
pnpm run dist:mac         # Build macOS .dmg
pnpm run dist:win         # Build Windows installer
```

## Code Standards

### Python (Backend)

- **Style**: Black formatter (88 character line length)
- **Linting**: Ruff with configured rules
- **Type Hints**: Use type hints for function signatures
- **Naming**:
  - `snake_case` for functions, variables, modules
  - `PascalCase` for classes
- **Imports**: From `src.` package (e.g., `from src.api.search import router`)

**Example:**
```python
from typing import List
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/photos", tags=["photos"])

async def get_photo_by_id(photo_id: str) -> Photo:
    """Retrieve a photo by its ID."""
    photo = await photo_service.find_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo
```

### TypeScript/React (Frontend)

- **Style**: ESLint + Prettier (2-space indentation)
- **Type Safety**: Strict TypeScript, avoid `any`
- **Naming**:
  - `PascalCase` for React components
  - `camelCase` for variables, functions
- **Imports**: Use `@/` alias for src paths (e.g., `import { Button } from '@/components/ui/button'`)

**Example:**
```typescript
import React from 'react';
import { Photo } from '@/types';

interface PhotoCardProps {
  photo: Photo;
  onSelect?: (photo: Photo) => void;
}

export const PhotoCard: React.FC<PhotoCardProps> = ({ photo, onSelect }) => {
  const handleClick = () => {
    onSelect?.(photo);
  };

  return (
    <div onClick={handleClick}>
      <img src={photo.thumbnail} alt={photo.filename} />
      <span>{photo.filename}</span>
    </div>
  );
};
```

## Testing Guidelines

### Backend Tests

Organized by type using pytest markers:

```bash
# Run all tests
pytest

# Run specific types
pytest -m unit           # Fast, isolated tests
pytest -m contract       # API contract tests
pytest -m integration    # Integration tests
pytest -m "not performance"  # Skip slow performance tests
```

**Test structure:**
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_search_photos():
    """Test photo search returns results."""
    response = client.get("/search/photos?q=sunset")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### Frontend Tests

```bash
pnpm test              # Jest unit tests
pnpm test:coverage     # With coverage report
```

**Test structure:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { PhotoCard } from './PhotoCard';

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

### E2E Tests

```bash
cd func_tests
pnpm test              # Run all E2E tests
pnpm run test:ui       # Interactive mode
```

## Pull Request Guidelines

### Before Submitting

- ✅ All tests pass (`make test` and `pnpm test`)
- ✅ Code is linted (`make backend-lint` and `pnpm run lint`)
- ✅ Type checks pass (`pnpm run type-check`)
- ✅ Pre-commit hooks pass (no console.log, debugger, etc.)
- ✅ Documentation updated if needed

### PR Title Format

Use conventional commit format:

- `feat: add face recognition to search`
- `fix: resolve indexing crash on large libraries`
- `docs: update installation guide`
- `refactor: improve search performance`
- `test: add unit tests for photo service`

### PR Description Template

```markdown
## Summary
Brief description of what this PR does

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] E2E tests pass
- [ ] Manually tested on macOS/Windows/Linux

## Screenshots (if UI changes)
[Add screenshots here]

## Related Issues
Fixes #123
```

### Review Process

1. Automated checks run (CI, tests, linting)
2. Code review by maintainers
3. Address feedback and update PR
4. Approval and merge

## Best Practices

### Do's

- ✅ Write tests for new features
- ✅ Keep PRs focused and small
- ✅ Update documentation with code changes
- ✅ Use descriptive commit messages
- ✅ Follow existing code patterns
- ✅ Run tests before pushing

### Don'ts

- ❌ Commit secrets or API keys
- ❌ Include `node_modules` or `.venv`
- ❌ Leave debug statements (`console.log`, `breakpoint()`)
- ❌ Create giant PRs with multiple features
- ❌ Skip tests
- ❌ Mix unrelated changes in one PR

### Configuration Files

**Do not commit:**
- `backend/.env` (copy from `.env.example` instead)
- Lock files (`pnpm-lock.yaml`, `package-lock.json`)
- Generated files (`dist/`, `build/`, `__pycache__/`)
- Local data (`backend/data/`, `backend/cache/`)

## Getting Help

- **Documentation**: Start with [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **Issues**: Search [existing issues](https://github.com/sarvarunajvm/ideal-goggles/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/sarvarunajvm/ideal-goggles/discussions)
- **Chat**: Join our community (coming soon)

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something great together.

---

Thank you for contributing to Ideal Goggles! Every contribution, big or small, makes this project better. 🙏
