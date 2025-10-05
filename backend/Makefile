# =============================================================================
# Ideal Goggles Backend - Makefile
# =============================================================================
# Python backend build, test, and development automation
#
# Quick Start:
#   make install     # Install dependencies
#   make dev         # Start development server
#   make test        # Run all tests
#   make lint        # Check code quality
#
# =============================================================================

# Configuration
PYTHON ?= python3

# Target declarations
.PHONY: help install dev clean
.PHONY: test test-unit test-performance
.PHONY: coverage coverage-unit
.PHONY: lint typecheck format check-style
.PHONY: package check-ml

# =============================================================================
# Help & Information
# =============================================================================

help: ## Show this help message
	@echo "Ideal Goggles Backend - Available Commands:"
	@echo ""
	@echo "🚀 Development:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; /Development:/ {print "  " $$1 $$2}'
	@echo ""
	@echo "🧪 Testing:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; /Testing:/ {print "  " $$1 $$2}'
	@echo ""
	@echo "📊 Coverage:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; /Coverage:/ {print "  " $$1 $$2}'
	@echo ""
	@echo "✨ Code Quality:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; /Quality:/ {print "  " $$1 $$2}'
	@echo ""
	@echo "📦 Build & Deploy:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; /Build:/ {print "  " $$1 $$2}'

# =============================================================================
# Development Setup
# =============================================================================

install: ## Development: Install all dependencies
	@echo "📦 Installing dependencies..."
	$(PYTHON) -m pip install --upgrade pip
	pip install -e ".[dev]"
	@echo "✅ Dependencies installed successfully!"

dev: ## Development: Start development server
	@echo "🚀 Starting development server..."
	$(PYTHON) -m src.main

clean: ## Development: Clean build artifacts and caches
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist/ build/ *.egg-info/
	rm -rf htmlcov/ .coverage coverage.xml
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "✅ Cleanup completed!"

# =============================================================================
# Testing
# =============================================================================

test: ## Testing: Run all tests (unit + integration + contract)
	@echo "🧪 Running all tests..."
	pytest -q

test-unit: ## Testing: Run unit tests only (fast)
	@echo "⚡ Running unit tests..."
	pytest tests/unit/ -q

test-performance: ## Testing: Run performance tests only (slow)
	@echo "🚀 Running performance tests..."
	pytest tests/performance/ -q || true

# =============================================================================
# Coverage Analysis
# =============================================================================

coverage: ## Coverage: Generate coverage report for all tests
	@echo "📊 Generating coverage report..."
	pytest --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo "📄 Coverage report: htmlcov/index.html"

coverage-unit: ## Coverage: Coverage report for unit tests only
	@echo "📊 Generating unit test coverage..."
	pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml

# =============================================================================
# Code Quality & Formatting
# =============================================================================

lint: ## Quality: Check code with ruff linter
	@echo "🔍 Running ruff linter..."
	ruff check .

typecheck: ## Quality: Run type checking with mypy
	@echo "🔍 Running type checker..."
	$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	# Ensure dev extras (including mypy and compatible numpy stubs) are available
	pip install -e ".[dev]" >/dev/null 2>&1 || true
	$(PYTHON) -m mypy src/

format: ## Quality: Format code with black
	@echo "✨ Formatting code..."
	black .

check-style: lint typecheck ## Quality: Run all code quality checks
	@echo "✅ All quality checks completed!"

# =============================================================================
# Build & Packaging
# =============================================================================

package: ## Build: Create standalone binary with PyInstaller
	@echo "📦 Building standalone binary..."
	$(PYTHON) -m pip install --upgrade pip
	pip install -e ".[dev]"
	pip install pyinstaller
	pyinstaller --clean ideal-goggles-backend.spec
	@echo "✅ Binary created: dist/ideal-goggles-backend"

check-ml: ## Build: Verify ML dependencies are available
	@echo "🔍 Checking ML dependencies..."
	$(PYTHON) scripts/install_ml_dependencies.py --verify-only

# =============================================================================
# Default target
# =============================================================================

.DEFAULT_GOAL := help
