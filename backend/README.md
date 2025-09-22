# Photo Search Backend

Backend API for photo search and navigation system.

## Features

- FastAPI-based REST API
- SQLite database with SQLAlchemy ORM
- Photo indexing and search capabilities
- OCR text extraction using Tesseract
- Vector similarity search using FAISS
- ONNX runtime for ML inference

## Installation

```bash
pip install -e ".[dev]"
```

## Development

```bash
# Run linting
ruff check .

# Run formatting
black .

# Run type checking
mypy src/

# Run tests
pytest
```