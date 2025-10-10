# 🥽 Ideal Goggles - Desktop App

[![Quick CI](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci-quick.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci-quick.yml)
[![E2E Tests](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/e2e.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/e2e.yml)
[![Coverage Report](https://codecov.io/gh/sarvarunajvm/ideal-goggles/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/sarvarunajvm/ideal-goggles)
[![Release](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/release.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/release.yml)
[![Dependabot Updates](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/dependabot/dependabot-updates)

A privacy-focused desktop application for intelligent photo search and organization. Ideal Goggles lets you search your photos using natural language, faces, and text within images — all processed locally on your machine.

## ✨ Features

- 🔍 **Smart Search**: Find photos using natural language descriptions
- 👤 **Face Recognition**: Group and search photos by people
- 📝 **OCR Text Search**: Find photos containing specific text
- 🖼️ **Similar Image Search**: Find visually similar photos
- 🔒 **100% Private**: All processing happens locally - no cloud uploads
- ⚡ **Fast Performance**: Handles 1M+ photos with sub-2s search times
- 🖥️ **Cross-Platform**: Works on macOS, Windows, and Linux

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+
- **PNPM** 10+ (install with `npm install -g pnpm`)
- **Python** 3.12+
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/sarvarunajvm/ideal-goggles.git
cd ideal-goggles

# Install all dependencies
pnpm install

# Install backend dependencies
make backend-install

# Start development environment
pnpm run dev
```

### Optional: ML Dependencies

Ideal Goggles works out of the box with basic search functionality. To enable advanced features like OCR, semantic search, and face recognition, install the optional ML dependencies:

```bash
# Install all ML dependencies (semantic search, face recognition)
# This installs PyTorch, CLIP, InsightFace and verifies they work
pnpm run backend:install-ml

# Or use Make:
make backend-install-ml

# Verify models work correctly
pnpm run backend:verify-models
```

**ML Features:**
- **Tesseract OCR**: Extract and search text within images
- **CLIP**: Natural language semantic search ("photos of sunset at beach")
- **InsightFace**: Face detection and recognition for people search

These dependencies are optional and can be installed later if needed. The app will gracefully disable features that require missing dependencies.

📖 **See [docs/ML_SETUP.md](docs/ML_SETUP.md) for complete ML setup guide, platform compatibility, and troubleshooting.**

The app will launch with:
- Backend API on http://localhost:5555
- Frontend on http://localhost:3333
- Electron desktop app

## 📁 Project Structure

```
ideal-goggles/
├── backend/              # Python FastAPI backend
│   ├── src/             # Backend source code
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core functionality
│   │   └── models/      # Data models
│   └── pyproject.toml   # Python dependencies
│
├── frontend/            # React frontend (Vite)
│   ├── src/            # Frontend source code
│   │   ├── components/ # React components
│   │   ├── pages/     # Application pages
│   │   └── services/  # API services
│   └── vite.config.ts # Vite configuration
│
├── frontend/electron/  # Electron desktop wrapper
│   ├── main.ts        # Main process
│   └── preload.ts     # Preload scripts
│
├── package.json       # Root scripts and Electron builder config
├── Makefile          # Build automation commands
└── .gitignore        # Ignores build artifacts and local data
```

## 🛠️ Development

### Available Commands

```bash
# Development
pnpm run dev              # Start full dev environment (backend 5555, frontend 3333, electron)
make backend-dev          # Start backend only
pnpm run dev:frontend     # Start frontend only

# Testing
pnpm run test            # Run frontend tests
make backend-test        # Run backend tests

# Linting & Formatting
pnpm run lint:frontend  # Lint frontend
make backend-lint       # Lint backend (ruff)
make backend-format     # Format backend (black)

# Building
pnpm run build          # Build frontend
make backend-package    # Package backend with PyInstaller

### Test Coverage

```bash
# Backend coverage (HTML + XML)
make backend-coverage             # Outputs: backend/htmlcov/index.html, backend/coverage.xml

# Frontend coverage (lcov + HTML)
make frontend-coverage            # Outputs: frontend/coverage/lcov-report/index.html

# Combined convenience target
make coverage                     # Runs both backend and frontend coverage

# Enforce minimum backend coverage (e.g., 70%)
make backend-coverage COV_MIN=70
```
```

### Using Make Commands

The project includes a comprehensive Makefile:

```bash
make help              # Show all available commands
make install          # Install all dependencies
make dev              # Start development environment
make test             # Run all tests
make clean            # Clean build artifacts

# Distribution builds
make dist-mac         # Build macOS DMG
make dist-win         # Build Windows installer
make dist-all         # Build for all platforms
```

## 📦 Building for Production

**Production builds automatically include all ML dependencies** so end users don't need to install anything manually. All AI features (face recognition, semantic search, OCR) work out of the box.

### Build for your platform:

```bash
# macOS (.dmg) - includes all ML features
pnpm run dist:mac

# Windows (.exe installer) - includes all ML features
pnpm run dist:win

# All platforms - includes all ML features
pnpm run dist:all
```

Built installers will be in the `dist-electron/` directory.

### Build Options:

**Full Build (Recommended - ~3-4 GB):**
```bash
# Backend is packaged with all ML dependencies
pnpm run backend:package      # Full backend with ML
pnpm run dist:mac             # Full macOS app
```

**Lite Build (~150 MB, no ML features):**
```bash
# For testing or when ML features are not needed
pnpm run backend:package-lite # Backend without ML
pnpm run dist:mac             # Lite macOS app
```

### What's Included in Production Builds:

✅ **Face Recognition** - InsightFace models pre-installed
✅ **Semantic Search** - PyTorch + CLIP models included
✅ **OCR Text Search** - Tesseract with language packs
✅ **Vector Search** - FAISS for fast similarity search
✅ **All dependencies bundled** - End users install nothing

📖 **For platform-specific build details and packaging strategy, see [docs/ML_SETUP.md](docs/ML_SETUP.md).**

Functional tests live under `func_tests/`. To run:

```bash
cd func_tests
pnpm install
pnpm test
```

## 🔧 Configuration

### Package Management
- **PNPM only**: No npm or yarn
- **No lock files**: Dependencies stay fresh, `.gitignore` excludes all lock files
- **Single package.json**: All Node.js dependencies in root

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React + TypeScript + Vite + TailwindCSS |
| Backend | Python + FastAPI + SQLAlchemy |
| Desktop | Electron |
| AI/ML | ONNX Runtime (CLIP, ArcFace models) |
| OCR | Tesseract |
| Database | SQLite (local) |
| Package Manager | PNPM (no lock files) |

## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

📖 **See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) and [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for detailed development guidelines.**

## 📚 Documentation

Complete documentation available in `/docs`:

- **[docs/README.md](docs/README.md)** - Documentation index and navigation
- **[docs/USER_MANUAL.md](docs/USER_MANUAL.md)** - Complete user guide
- **[docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** - Developer setup and architecture
- **[docs/ML_SETUP.md](docs/ML_SETUP.md)** - ML dependencies, packaging, and platforms
- **[docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md)** - Testing approach and priorities
- **[docs/COVERAGE.md](docs/COVERAGE.md)** - CI/CD and coverage documentation
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[API Documentation](http://localhost:5555/docs)** - Interactive API docs (when backend is running)

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check Python version (needs 3.12+)
python3 --version

# Reinstall backend dependencies
cd backend && rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

**Frontend build fails:**
```bash
# Clear cache and reinstall
rm -rf node_modules dist
pnpm install --no-lockfile
```

**Electron app won't launch:**
```bash
# Rebuild Electron
pnpm run build:electron:main
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CLIP model by OpenAI for semantic image search
- ArcFace for face recognition capabilities
- Tesseract OCR for text extraction
- The amazing open-source community

## 📧 Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/sarvarunajvm/ideal-goggles/issues)
- Check existing issues for solutions

---

Made with ❤️ by the Ideal Goggles Team
