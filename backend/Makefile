.PHONY: install dev test coverage lint typecheck format package check-ml

PYTHON ?= python3

install:
	$(PYTHON) -m venv .venv && \
		.venv/bin/pip install --upgrade pip && \
		.venv/bin/pip install -e ".[dev]"

dev:
	.venv/bin/python -m src.main

test:
	.venv/bin/pytest -q

coverage:
	.venv/bin/pytest --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml

lint:
	.venv/bin/ruff check .

typecheck:
	.venv/bin/mypy src/

format:
	.venv/bin/black .

package:
	$(PYTHON) -m venv .venv && \
		.venv/bin/pip install -e ".[dev]" && \
		.venv/bin/pip install pyinstaller && \
		.venv/bin/python -m PyInstaller --onefile --name ideal-goggles-backend -p src -s src/main.py

check-ml:
	$(PYTHON) scripts/install_ml_dependencies.py --verify-only
