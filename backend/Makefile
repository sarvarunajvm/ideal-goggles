APP_NAME=photo-search-backend
PYTHON ?= python3

.PHONY: install dev test lint typecheck format clean package package-windows package-mac

install:
	$(PYTHON) -m venv .venv && .venv/bin/pip install -e ".[dev]"

dev:
	uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

test:
	pytest -q

lint:
	ruff check .

typecheck:
	mypy src/

format:
	black .

clean:
	rm -rf .venv data cache performance_report.txt

# Package backend as a single executable with PyInstaller
package:
	$(PYTHON) -m venv .venv && \
	.venv/bin/pip install -e ".[dev]" && \
	.venv/bin/pip install pyinstaller && \
	.venv/bin/python -m PyInstaller --onefile --name photo-search-backend -p src -s src/main.py

package-windows:
	$(PYTHON) -m venv .venv && \
	.venv/bin/pip install -e ".[dev]" && \
	.venv/bin/pip install pyinstaller && \
	.venv/bin/python -m PyInstaller --onefile --name photo-search-backend -p src -s src/main.py

package-mac:
	$(PYTHON) -m venv .venv && \
	.venv/bin/pip install -e ".[dev]" && \
	.venv/bin/pip install pyinstaller && \
	.venv/bin/python -m PyInstaller --onefile --name photo-search-backend -p src -s src/main.py
