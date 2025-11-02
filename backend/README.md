# Ideal Goggles Backend

FastAPI backend service providing photo indexing, search, and AI-powered features for Ideal Goggles.

## Features

- **Photo Indexing**: Automatic discovery and metadata extraction
- **Multi-modal Search**:
  - Text search with OCR
  - Semantic search with CLIP embeddings
  - Face recognition and search
  - Visual similarity search
- **Thumbnail Generation**: Optimized caching
- **Multi-drive Support**: Index photos across external drives

## Quick Start

### Basic Installation

```bash
# Create virtual environment and install core dependencies
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### ML Dependencies (Optional)

For AI-powered features (semantic search, face recognition):

```bash
# Install and verify all ML models
python scripts/setup_ml_models.py --all

# Or use Make targets
make install-ml      # Install dependencies
make verify-models   # Verify models work
```

**What gets installed:**
- PyTorch (CPU/MPS/CUDA optimized)
- CLIP (OpenAI ViT-B/32)
- InsightFace (buffalo_l model)
- ONNX Runtime
- OpenCV

The app gracefully degrades if ML dependencies aren't installed.

[📖 Full ML Setup Guide](../docs/ML_SETUP.md)

## Running

### Development Server

```bash
# From backend directory
python -m src.main

# Or with auto-reload
python -m uvicorn src.main:app --reload --port 5555
```

Server starts at: http://localhost:5555

**API Documentation:**
- Swagger UI: http://localhost:5555/docs
- ReDoc: http://localhost:5555/redoc

### Production

```bash
# Package with PyInstaller
make package          # With ML dependencies
make package-lite     # Without ML dependencies
```

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test types
pytest -m unit                    # Fast unit tests
pytest -m contract                # API contract tests
pytest -m integration             # Integration tests
pytest -m "not performance"       # Skip slow tests
```

### Test Organization

```
tests/
├── unit/            # Fast, isolated tests
├── contract/        # API endpoint tests
├── integration/     # Database and service integration
└── performance/     # Benchmarks and load tests
```

## Project Structure

```
backend/
├── src/
│   ├── api/             # FastAPI route handlers
│   │   ├── search.py   # Search endpoints
│   │   ├── photos.py   # Photo management
│   │   └── index.py    # Indexing operations
│   │
│   ├── core/            # Business logic
│   │   ├── indexer.py  # Photo discovery and indexing
│   │   ├── search.py   # Search implementations
│   │   └── config.py   # Configuration
│   │
│   ├── models/          # Data models
│   │   ├── database.py # SQLAlchemy models
│   │   └── schemas.py  # Pydantic schemas
│   │
│   ├── services/        # Feature implementations
│   │   ├── embedding.py    # CLIP embeddings
│   │   ├── face_search.py  # Face recognition
│   │   └── ocr.py          # Text extraction
│   │
│   ├── workers/         # Background tasks
│   │   └── indexing.py # Async indexing workers
│   │
│   └── main.py          # Application entry point
│
├── tests/               # Test suites
├── scripts/             # Utility scripts
└── pyproject.toml       # Dependencies and config
```

## Development

### Code Quality

```bash
# Linting
make lint              # Ruff linter
make format            # Black formatter

# Type checking
make typecheck         # mypy (relaxed mode)

# All checks
make check             # lint + format + typecheck
```

### Configuration

**Environment Variables** (create `.env` from `.env.example`):

```bash
# Database
DATABASE_URL=sqlite:///./data/photos.db

# Optional ML Features
ENABLE_CLIP_SEARCH=true
ENABLE_FACE_SEARCH=true
ENABLE_OCR=true

# Logging
LOG_LEVEL=INFO
```

### API Examples

**Search photos:**
```bash
curl "http://localhost:5555/search/photos?q=sunset&mode=semantic"
```

**Start indexing:**
```bash
curl -X POST "http://localhost:5555/index/start" \
  -H "Content-Type: application/json" \
  -d '{"paths": ["/Users/you/Pictures"]}'
```

**Check index status:**
```bash
curl "http://localhost:5555/index/status"
```

## Architecture

```
┌─────────────────────────────────────┐
│        FastAPI Application          │
├─────────────────────────────────────┤
│  API Layer (REST endpoints)         │
├─────────────────────────────────────┤
│  Service Layer (business logic)     │
│  - Indexing                          │
│  - Search (text, semantic, face)    │
│  - Thumbnail generation             │
├─────────────────────────────────────┤
│  Data Layer                          │
│  - SQLAlchemy ORM                    │
│  - SQLite database                   │
├─────────────────────────────────────┤
│  ML Layer (optional)                 │
│  - CLIP embeddings                   │
│  - Face recognition                  │
│  - OCR text extraction               │
└─────────────────────────────────────┘
```

## Troubleshooting

**Import errors:**
```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

**ML models not working:**
```bash
# Verify model installation
python scripts/setup_ml_models.py --verify-only

# Reinstall specific model
python scripts/setup_ml_models.py --clip-only
python scripts/setup_ml_models.py --face-only
```

**Database issues:**
```bash
# Reset database (WARNING: deletes all data)
rm -rf data/photos.db
python -m src.main  # Recreates schema
```

**Port already in use:**
```bash
# Kill process on port 5555
lsof -ti:5555 | xargs kill -9
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [CLIP Model](https://github.com/openai/CLIP)
- [InsightFace](https://github.com/deepinsight/insightface)

---

[📖 Main Documentation](../README.md) | [📖 Developer Guide](../docs/DEVELOPER_GUIDE.md) | [📖 API Docs](http://localhost:5555/docs)
