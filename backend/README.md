# Ideal Goggles Backend

FastAPI backend service for the Ideal Goggles photo management application.

## Features

- **Photo Management**: Automatic photo discovery and indexing
- **Search Capabilities**:
  - Text search with OCR
  - Face recognition and search
  - Semantic search with CLIP embeddings
- **Thumbnail Generation**: Automatic thumbnail creation and caching
- **External Drive Support**: Multi-drive photo management

## Installation

```bash
pip install -e ".[dev]"
```

## Running

```bash
python -m src.main
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

## API Documentation

When running, visit:
- API Docs: http://localhost:5555/docs
- ReDoc: http://localhost:5555/redoc

## Project Structure

```
backend/
├── src/                 # Source code
│   ├── api/            # API endpoints
│   ├── db/             # Database models and connection
│   ├── models/         # Domain models
│   ├── services/       # Business logic services
│   └── workers/        # Background workers
├── tests/              # Test suites
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── contract/      # API contract tests
└── scripts/           # Utility scripts
```