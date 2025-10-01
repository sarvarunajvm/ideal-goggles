.PHONY: help install dev test coverage clean build dist-mac dist-win dist-all

# Configuration
APP_NAME = ideal-goggles
BACKEND_NAME = ideal-goggles-backend
PYTHON ?= python3
NODE_PM ?= pnpm
COV_MIN ?= 0

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m # No Color

help:
	@echo "$(GREEN)Available targets:$(NC)"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  install            Install all dependencies (backend + frontend)"
	@echo "  dev                Start development environment (backend + frontend + electron)"
	@echo "  test               Run all tests (backend + frontend)"
	@echo "  coverage           Generate test coverage (backend + frontend)"
	@echo ""
	@echo "$(YELLOW)Backend:$(NC)"
	@echo "  backend-install    Install backend dependencies"
	@echo "  backend-install-ml Install optional ML dependencies (OCR, semantic search, face)"
	@echo "  backend-check-ml   Check ML dependencies status"
	@echo "  backend-dev        Run backend development server"
	@echo "  backend-test       Run backend tests"
	@echo "  backend-lint       Run backend linter (ruff)"
	@echo "  backend-typecheck  Run backend type checking (mypy)"
	@echo "  backend-format     Format backend code (black)"
	@echo "  backend-package    Build backend binary with PyInstaller"
	@echo ""
	@echo "$(YELLOW)Frontend:$(NC)"
	@echo "  frontend-install   Install frontend dependencies"
	@echo "  frontend-dev       Run frontend development server"
	@echo "  frontend-build     Build frontend for production"
	@echo "  frontend-test      Run frontend tests"
	@echo "  frontend-lint      Run frontend linter"
	@echo ""
	@echo "$(YELLOW)Electron:$(NC)"
	@echo "  electron-build     Build Electron main process"
	@echo "  dist-mac           Build macOS DMG installer"
	@echo "  dist-win           Build Windows installer"
	@echo "  dist-all           Build all platform installers"
	@echo ""
	@echo "$(YELLOW)Utility:$(NC)"
	@echo "  clean              Clean all build artifacts and dependencies"
	@echo ""
	@echo "$(YELLOW)Variables:$(NC)"
	@echo "  PYTHON=$(PYTHON)      Python interpreter"
	@echo "  NODE_PM=$(NODE_PM)    Node package manager"

# === Main Targets ===

install: backend-install frontend-install root-install
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(NODE_PM) -w run dev

test: backend-test frontend-test
	@echo "$(GREEN)✓ All tests completed$(NC)"

coverage: backend-coverage frontend-coverage
	@echo "$(GREEN)✓ Coverage reports generated$(NC)"

build: frontend-build electron-build backend-package
	@echo "$(GREEN)✓ Build completed$(NC)"

clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf backend/.venv backend/dist backend/build backend/*.spec
	rm -rf backend/data backend/cache backend/performance_report.txt
	rm -rf frontend/dist frontend/node_modules/.ignored
	rm -rf electron/dist
	rm -rf dist-electron node_modules
	rm -rf tests/node_modules tests/test-results
	@echo "$(GREEN)✓ Clean completed$(NC)"

# === Backend Targets ===

backend-install:
	@echo "$(YELLOW)Installing backend dependencies...$(NC)"
	cd backend && $(PYTHON) -m venv .venv && \
		.venv/bin/pip install --upgrade pip && \
		.venv/bin/pip install -e ".[dev]"

backend-install-ml:
	@echo "$(YELLOW)Installing ML dependencies (OCR, semantic search, face recognition)...$(NC)"
	@cd backend && $(PYTHON) scripts/install_ml_dependencies.py
	@echo "$(GREEN)✓ ML dependencies installed$(NC)"

backend-check-ml:
	@echo "$(YELLOW)Checking ML dependencies status...$(NC)"
	@cd backend && $(PYTHON) scripts/install_ml_dependencies.py --verify-only

backend-dev:
	cd backend && .venv/bin/python -m src.main

backend-test:
	cd backend && .venv/bin/pytest -q

backend-coverage:
	@echo "$(YELLOW)Generating backend coverage...$(NC)"
	cd backend && .venv/bin/pytest --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=$(COV_MIN)
	@echo "$(GREEN)✓ Backend coverage: backend/htmlcov/index.html, backend/coverage.xml$(NC)"

backend-lint:
	cd backend && .venv/bin/ruff check .

backend-typecheck:
	cd backend && .venv/bin/mypy src/

backend-format:
	cd backend && .venv/bin/black .

backend-package:
	@echo "$(YELLOW)Building backend binary...$(NC)"
	cd backend && \
		$(PYTHON) -m venv .venv && \
		.venv/bin/pip install -e ".[dev]" && \
		.venv/bin/pip install pyinstaller && \
		.venv/bin/python -m PyInstaller --onefile --name $(BACKEND_NAME) -p src -s src/main.py
	@echo "$(GREEN)✓ Backend binary built: backend/dist/$(BACKEND_NAME)$(NC)"

backend-package-windows: backend-package

backend-package-mac: backend-package

# === Frontend Targets ===

frontend-install:
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	cd frontend && $(NODE_PM) install

frontend-dev:
	cd frontend && $(NODE_PM) run dev

frontend-build:
	@echo "$(YELLOW)Building frontend...$(NC)"
	cd frontend && $(NODE_PM) run build

frontend-test:
	cd frontend && $(NODE_PM) run test

frontend-coverage:
	@echo "$(YELLOW)Running frontend tests with coverage...$(NC)"
	cd frontend && $(NODE_PM) run test:coverage

coverage: backend-coverage frontend-coverage
	@echo "$(GREEN)✓ All coverage reports generated$(NC)"
	@echo "$(YELLOW)Run 'make coverage-report' to view combined report$(NC)"

coverage-report:
	@echo "$(YELLOW)Generating combined coverage report...$(NC)"
	@bash scripts/run-coverage.sh
	@echo "$(GREEN)✓ Coverage report available at coverage-reports/index.html$(NC)"
	@echo "$(GREEN)✓ Frontend coverage: frontend/coverage/lcov-report/index.html$(NC)"

frontend-lint:
	cd frontend && $(NODE_PM) run lint

# === Electron Targets ===

root-install:
	@echo "$(YELLOW)Installing root dependencies...$(NC)"
	$(NODE_PM) install

electron-build:
	@echo "$(YELLOW)Building Electron main process...$(NC)"
	$(NODE_PM) run build:electron:main

dist-mac: backend-package frontend-build electron-build
	@echo "$(YELLOW)Building macOS installer...$(NC)"
	$(NODE_PM) run build:electron -- --mac
	@echo "$(GREEN)✓ macOS installer built$(NC)"

dist-win: backend-package frontend-build electron-build
	@echo "$(YELLOW)Building Windows installer...$(NC)"
	$(NODE_PM) run build:electron -- --win
	@echo "$(GREEN)✓ Windows installer built$(NC)"

dist-all: backend-package frontend-build electron-build
	@echo "$(YELLOW)Building all platform installers...$(NC)"
	$(NODE_PM) run build:electron -- -mwl
	@echo "$(GREEN)✓ All installers built$(NC)"

# === Quick Commands ===

# Quick dev with automatic backend start
quick-dev:
	@trap 'kill %1' INT; \
	cd backend && $(PYTHON) -m src.main & \
	sleep 2 && \
	$(NODE_PM) -w run dev

# Install and run
fresh-start: clean install dev

# Full rebuild
rebuild: clean install build

.DEFAULT_GOAL := help
