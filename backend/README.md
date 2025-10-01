# Backend - Ideal Goggles

FastAPI backend for the Ideal Goggles desktop application.

## Quick Start

```bash
# Install dependencies
make backend-install

# Install ML dependencies (optional)
make backend-install-ml

# Run development server
make backend-dev  # Runs on http://localhost:5555
```

## Project Structure

```
backend/
├── src/            # Source code
│   ├── api/       # REST API endpoints
│   ├── core/      # Core business logic
│   ├── models/    # Database models
│   └── services/  # Service layer
├── tests/         # Test suites
│   ├── unit/      # Unit tests
│   ├── contract/  # API contract tests
│   └── integration/ # Integration tests
└── pyproject.toml # Dependencies & config
```

## Testing

```bash
make backend-test         # Run all tests
make backend-test-unit    # Unit tests only
make backend-coverage     # Generate coverage report
```

## Development Commands

```bash
make backend-lint         # Lint with ruff
make backend-format       # Format with black
make backend-typecheck    # Type check with mypy
```

📚 For complete documentation, see the main [README](../README.md) and [DEVELOPER_GUIDE](../DEVELOPER_GUIDE.md)
