APP_NAME=photo-search-backend

.PHONY: install dev test lint typecheck format run clean package package-windows package-mac

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

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
	python -m venv .venv && . .venv/bin/activate && pip install . && pip install pyinstaller && \
	python -m PyInstaller --onefile --name photo-search-backend src/main.py

package-windows:
	python -m PyInstaller --onefile --name photo-search-backend src/main.py

package-mac:
	python -m venv .venv && . .venv/bin/activate && pip install . && pip install pyinstaller && \
	python -m PyInstaller --onefile --name photo-search-backend src/main.py
