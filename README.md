# 📸 Ideal Googles - Photo Search Desktop App

[![CI](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/ci.yml)
[![Release](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/release.yml/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/release.yml)
[![Dependabot Updates](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/sarvarunajvm/ideal-goggles/actions/workflows/dependabot/dependabot-updates)

A privacy-focused desktop application for intelligent photo search and organization. Search your photos using natural language, faces, and text within images - all processed locally on your machine.

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
- **Python** 3.11+
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/sarvarunajvm/ideal-goggles.git
cd ideal-goggles

# Install all dependencies (no lock files)
pnpm install --no-lockfile

# Install backend dependencies
cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cd ..

# Start development environment
pnpm run dev
```

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
├── frontend/            # React frontend
│   ├── src/            # Frontend source code
│   │   ├── components/ # React components
│   │   ├── pages/     # Application pages
│   │   └── services/  # API services
│   └── vite.config.ts # Vite configuration
│
├── electron/           # Electron desktop wrapper
│   ├── main.ts        # Main process
│   └── preload.ts     # Preload scripts
│
├── package.json       # Single package.json for all Node.js deps
├── Makefile          # Build automation commands
└── .gitignore        # Includes lock files (not tracked)
```

## 🛠️ Development

### Available Commands

```bash
# Development
pnpm run dev              # Start full dev environment
pnpm run dev:backend      # Start backend only
pnpm run dev:frontend     # Start frontend only

# Testing
pnpm run test            # Run frontend tests
make backend-test        # Run backend tests

# Linting & Formatting
pnpm run lint           # Lint frontend
make backend-lint       # Lint backend (ruff)
make backend-format     # Format backend (black)

# Building
pnpm run build          # Build frontend
make backend-package    # Package backend with PyInstaller
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

### Build for your platform:

```bash
# macOS (.dmg)
pnpm run dist:mac

# Windows (.exe installer)
pnpm run dist:win

# All platforms
pnpm run dist:all
```

Built installers will be in the `dist-electron/` directory.

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

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for detailed development guidelines.

## 📚 Documentation

- [USER_MANUAL.md](USER_MANUAL.md) - End user guide
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Developer documentation
- [API Documentation](http://localhost:5555/docs) - When backend is running

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check Python version (needs 3.11+)
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

Made with ❤️ by the Photo Search Team
