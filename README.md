# Photo Search and Navigation System

[![CI](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci.yml)

A local-first photo search system with multi-modal search capabilities including text, semantic, image similarity, and face recognition.

## Features

- **Multi-modal Search**: Text, semantic, image similarity, and face-based search
- **Local-First**: All processing happens locally, no external services
- **High Performance**: Handles 1M+ photos with sub-2s search times
- **Privacy Focused**: No data leaves your machine
- **Studio-Ready**: Designed for photo studios and professional workflows

## Quick Start

### Prerequisites

- Python 3.11 or higher
- 16GB RAM recommended for large photo libraries
- SSD storage recommended

### Automatic Setup

Run the setup script to automatically configure everything:

```bash
python setup.py
```

This will:
- Create a Python virtual environment
- Install required dependencies
- Optionally install advanced features (OCR, vector search, etc.)
- Create sample directory structure
- Generate start scripts

### Manual Setup

If you prefer manual setup:

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Optional: Install advanced features**:
   ```bash
   # For OCR (requires Tesseract)
   pip install pytesseract

   # For vector search
   pip install faiss-cpu

   # For semantic search
   pip install torch torchvision
   pip install git+https://github.com/openai/CLIP.git
   ```

## Running the System

### Start the API Server

```bash
# Using the start script
./start.sh  # On Windows: start.bat

# Or manually
./venv/bin/python backend/main.py  # On Windows: venv\Scripts\python backend\main.py
```

The API will be available at: http://localhost:8000

### API Documentation

- **Interactive docs**: http://localhost:8000/docs
- **OpenAPI spec**: http://localhost:8000/openapi.json

## Basic Usage

### 1. Configure Root Folders

```bash
curl -X POST "http://localhost:8000/config/roots" \
  -H "Content-Type: application/json" \
  -d '{"roots": ["/path/to/your/photos"]}'
```

### 2. Start Indexing

```bash
curl -X POST "http://localhost:8000/index/start" \
  -H "Content-Type: application/json" \
  -d '{"full": false}'
```

### 3. Check Indexing Status

```bash
curl "http://localhost:8000/index/status"
```

### 4. Search Photos

**Text Search**:
```bash
curl "http://localhost:8000/search?q=wedding&limit=10"
```

**Semantic Search**:
```bash
curl -X POST "http://localhost:8000/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"text": "sunset over mountains", "top_k": 10}'
```

**Image Search** (upload a photo):
```bash
curl -X POST "http://localhost:8000/search/image" \
  -F "file=@/path/to/query/image.jpg" \
  -F "top_k=10"
```

## Configuration

### Database Location

By default, the database is stored at: `~/.photo-search/photos.db`

### Cache Directory

Thumbnails and indexes are stored at: `~/.photo-search/`

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)

## Advanced Features

### OCR (Text Extraction)

To enable OCR, install Tesseract:

**macOS**:
```bash
brew install tesseract
```

**Ubuntu/Debian**:
```bash
sudo apt-get install tesseract-ocr
```

**Windows**: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

### Face Recognition

Face recognition is optional and requires additional setup:

```bash
pip install insightface onnxruntime
```

Enable in configuration:
```bash
curl -X PUT "http://localhost:8000/config" \
  -H "Content-Type: application/json" \
  -d '{"face_search_enabled": true}'
```

### Vector Search Optimization

For large collections (200k+ photos), the system automatically upgrades to optimized FAISS indexes for better performance.

## Development

### Project Structure

```
backend/
├── src/
│   ├── api/          # FastAPI endpoints
│   ├── db/           # Database and migrations
│   ├── models/       # Data models
│   ├── services/     # Business logic
│   └── workers/      # Background processing
├── tests/            # Test files
└── main.py          # Application entry point
```

### Running Tests

```bash
pytest backend/tests/
```

### API Endpoints

- `GET /health` - Health check
- `GET /config` - Get configuration
- `POST /config/roots` - Update root folders
- `GET /search` - Text search
- `POST /search/semantic` - Semantic search
- `POST /search/image` - Image similarity search
- `POST /search/faces` - Face search
- `POST /index/start` - Start indexing
- `GET /index/status` - Indexing status
- `GET /people` - List enrolled people
- `POST /people` - Enroll person

## Packaging & Installers

Build one‑click desktop installers that bundle the backend:

- macOS: `cd frontend && pnpm dist:mac`
- Windows: `cd frontend && pnpm dist:win`
- All (on host OS): `cd frontend && pnpm dist:all`

Notes:
- The backend is packaged with PyInstaller and auto‑started by Electron.
- App data (database, cache) is stored under the OS app data folder (e.g., `~/Library/Application Support/Photo Search`, `%AppData%/Photo Search`).

## Performance Tuning

### For Large Libraries (1M+ photos)

1. **Use SSD storage** for better I/O performance
2. **Increase memory** - 16GB+ recommended
3. **Batch processing** - The system automatically uses optimal batch sizes
4. **Index optimization** - FAISS indexes automatically upgrade for large collections

### Search Performance

- **Text search**: <2s for most queries
- **Semantic search**: <5s for most queries
- **Index building**: ~100k photos/day on typical hardware

## Troubleshooting

### Common Issues

**Import errors**: Make sure virtual environment is activated and dependencies are installed

**Tesseract not found**: Install Tesseract and ensure it's in your PATH

**Out of memory**: Reduce batch sizes or increase system memory

**Slow indexing**: Check disk I/O and consider using SSD storage

### Logs

Application logs are stored at: `~/.photo-search/app.log`

### Database Issues

To reset the database:
```bash
rm ~/.photo-search/photos.db
# Restart the application to recreate
```

## Contributing

Thank you for considering contributing! This repository contains:
- Python FastAPI backend in `backend/`
- React + Vite + Electron frontend in `frontend/`
- Shared TypeScript types in `packages/shared/`
- Product specs in `specs/`

Please follow the guidelines below to set up your environment, run tests, and submit changes.

### Developer Setup

Backend (Python 3.11+):
1. Create and activate a virtualenv
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   ```
2. Install deps
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Optional extras (OCR, vector, semantics, faces) are noted in `backend/requirements.txt` and in the Advanced Features section above.

Frontend (Node 18+ recommended):
1. Install Node dependencies
   ```bash
   cd frontend
   npm install
   ```
2. Start dev environment (Vite + Electron)
   ```bash
   npm run dev
   ```

Shared package:
```bash
cd packages/shared
npm install
npm run build
```

### Running Locally

- Start backend API:
  ```bash
  ./venv/bin/python backend/main.py  # Windows: venv\\Scripts\\python backend\\main.py
  ```
- Start frontend app:
  ```bash
  cd frontend && npm run dev
  ```

### Coding Standards

- Python: Ruff + Black + Mypy are configured via `backend/pyproject.toml`.
  - Format: `ruff --fix backend && black backend`
  - Type-check: `mypy backend`
- TypeScript/React: ESLint + Prettier are configured under `frontend/`.
  - Lint: `npm run lint` (in `frontend/`)
  - Format: follow `frontend/prettier.config.js`
- Commit messages: Use clear, imperative style (e.g., "Add face search endpoint").

### Tests

- Backend tests:
  ```bash
  pytest backend/tests
  ```
- Frontend unit/integration tests:
  ```bash
  cd frontend
  npm test
  ```
- Frontend E2E (Playwright):
  ```bash
  cd frontend
  npm run test:e2e
  ```

### Branching & PRs

- Create feature branches from `main`.
- Keep PRs focused and small; include a brief description and screenshots for UI changes.
- Ensure all tests pass and linters are clean before requesting review.
- Link the relevant spec/task from `specs/` when applicable.

### Environment and Secrets

- Do not commit real secrets. Use environment files and keep `.env` files out of Git (see `.gitignore`).
- If needed, add `.env.example` with safe placeholders and document variables in this README.

### Project Scripts Quick Reference

- Backend: see `backend/pyproject.toml` for tool config; dependencies are managed via `backend/requirements.txt`.
- Frontend scripts (run inside `frontend/`):
  - `npm run dev` – Run Vite + Electron in development
  - `npm run build` – Build React app
  - `npm run build:electron` – Package Electron app
  - `npm run test` – Run unit tests
  - `npm run test:e2e` – Run Playwright tests
  - `npm run lint` – Lint code

### Architecture Overview

- Backend exposes REST API (FastAPI) for search, indexing, and people management. See `backend/src/api/` for routes and `backend/tests/` for expected behavior.
- Workers in `backend/src/workers/` handle long-running tasks (indexing, OCR, embeddings, thumbnails).
- Frontend communicates with backend via `frontend/src/services/api.ts`.
- Shared TypeScript types live in `packages/shared/` and can be built and consumed by the frontend.

### Spec-Driven Development

This implementation follows the specification under `specs/001-core-features-mandatory/`. When adding new features, consider adding or updating specs under `specs/` and aligning tests accordingly.

### Reporting Issues

- Include OS, Python/Node versions, steps to reproduce, logs (see `~/.photo-search/app.log`), and screenshots where helpful.


## License

See LICENSE file for details.

## Support

For issues and questions, check the logs and API documentation first. The system is designed to be self-contained and work offline.
