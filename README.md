# 🥽 Ideal Goggles

> Privacy-first photo search and organization powered by AI - everything runs on your computer

[![Quick CI](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci-quick.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci-quick.yml)
[![E2E Tests](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/e2e.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/e2e.yml)
[![Release](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/release.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/release.yml)

[![Coverage Report](https://codecov.io/gh/sarvarunajvm/ideal-goggles/graph/badge.svg?token=WYPXWO5QU4)](https://codecov.io/gh/sarvarunajvm/ideal-goggles)

[![Coverage Tree](https://codecov.io/gh/sarvarunajvm/ideal-goggles/graphs/tree.svg?token=WYPXWO5QU4)](https://codecov.io/gh/sarvarunajvm/ideal-goggles)

Search your photo library using natural language, face recognition, and OCR — all running locally on your machine. No cloud uploads, no subscriptions, no privacy concerns.

## What Makes It Special

**🔒 Privacy First**
- All AI processing happens on your computer
- Zero cloud uploads or third-party services
- Open source - verify the code yourself

**🎯 Powerful Search**
- Natural language: "dog playing in snow"
- Face recognition: Find all photos of a person
- OCR: Search text within images
- Visual similarity: Find duplicates or similar shots

**⚡ Fast & Scalable**
- Handles 100,000+ photos
- Sub-2-second search times
- Works on macOS, Windows, and Linux

## Quick Start

### For Users

Download the latest installer for your platform:
- **macOS**: [ideal-goggles.dmg](https://github.com/sarvarunajvm/ideal-goggles/releases)
- **Windows**: [ideal-goggles-Setup.exe](https://github.com/sarvarunajvm/ideal-goggles/releases)
- **Linux**: [.AppImage / .deb / .rpm](https://github.com/sarvarunajvm/ideal-goggles/releases)

[📖 Full Installation Guide](docs/USER_MANUAL.md#installation)

### For Developers

```bash
# Prerequisites: Node.js 22+, Python 3.13+, pnpm 10+
git clone https://github.com/sarvarunajvm/ideal-goggles.git
cd ideal-goggles

# Install dependencies
pnpm install
make backend-install

# Start development
pnpm run dev
```

[📖 Developer Setup Guide](docs/DEVELOPER_GUIDE.md)

### ML Features (Optional)

Advanced AI features are optional. Install when ready:

```bash
# Install ML dependencies (PyTorch, CLIP, InsightFace)
pnpm run backend:install-ml

# Verify everything works
pnpm run backend:verify-models
```

**What you get:**
- Natural language search ("sunset at beach")
- Face recognition and grouping
- OCR text extraction from images

[📖 ML Setup Guide](docs/ML_SETUP.md)

## Architecture

```
┌─────────────────────────────────┐
│   Electron Desktop App          │
├─────────────────────────────────┤
│   React + TypeScript Frontend   │
│   (Vite + TailwindCSS)          │
├─────────────────────────────────┤
│   FastAPI Python Backend        │
│   (Async REST API)              │
├─────────────────────────────────┤
│   ML Layer (Optional)           │
│   CLIP | InsightFace | OCR      │
├─────────────────────────────────┤
│   SQLite Database (Local)       │
└─────────────────────────────────┘
```

**Tech Stack:** React 19 · Python 3.13 · FastAPI · Electron · SQLite · PyTorch (optional)

## Development

### Common Commands

```bash
# Start everything
pnpm run dev                    # Backend + Frontend + Electron

# Development
make backend-dev                # Python API server (port 5555)
pnpm run dev:frontend           # React dev server (port 3333)

# Testing
make backend-test               # Python tests with pytest
pnpm test                       # Frontend tests with Jest
pnpm run e2e                    # End-to-end tests

# Code Quality
make backend-lint               # Ruff linter
pnpm run lint                   # ESLint + TypeScript check

# Building
pnpm run dist:mac               # macOS .dmg
pnpm run dist:win               # Windows installer
pnpm run dist:all               # All platforms
```

**All commands:** Run `make help` for full list

[📖 Development Guide](docs/DEVELOPER_GUIDE.md) | [📖 Contributing](docs/CONTRIBUTING.md) | [📖 ML Setup](docs/ML_SETUP.md)

## Documentation

| Document | Description |
|----------|-------------|
| [User Manual](docs/USER_MANUAL.md) | Complete user guide |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Architecture, patterns, testing, and workflows |
| [Contributing](docs/CONTRIBUTING.md) | Setup and contribution guidelines |
| [ML Setup](docs/ML_SETUP.md) | AI features and model installation |
| [API Documentation](http://localhost:5555/docs) | Interactive API docs (when running) |

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

Quick steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and test (`make test`)
4. Commit with pre-commit hooks (`git commit -m "feat: add feature"`)
5. Push and open a Pull Request

## Troubleshooting

**App won't start?**
```bash
# Backend
cd backend && rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# Frontend
rm -rf node_modules && pnpm install

# Electron
pnpm run build:electron:main
```

**Port conflicts?**
```bash
lsof -ti:5555 | xargs kill -9  # Kill backend
lsof -ti:3333 | xargs kill -9  # Kill frontend
```

[📖 Full Troubleshooting Guide](docs/DEVELOPER_GUIDE.md#troubleshooting)

## License

MIT License - see [LICENSE](LICENSE) for details

## Support

- **Issues**: [GitHub Issues](https://github.com/sarvarunajvm/ideal-goggles/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sarvarunajvm/ideal-goggles/discussions)

## Credits

Built with:
- [OpenAI CLIP](https://github.com/openai/CLIP) - Semantic image search
- [InsightFace](https://github.com/deepinsight/insightface) - Face recognition
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Text extraction
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [React](https://react.dev/) - UI framework
- [Electron](https://www.electronjs.org/) - Desktop platform

---

**Privacy-first photo management** • Made with care by the Ideal Goggles Team
