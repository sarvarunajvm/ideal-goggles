APP_NAME=photo-search-backend
IMAGE_NAME=$(APP_NAME):latest

.PHONY: install dev test lint typecheck format run docker-build docker-run clean

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

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run --rm -p 8000:8000 -v $(PWD)/data:/app/data -v $(PWD)/cache:/app/cache $(IMAGE_NAME)

clean:
	rm -rf .venv data cache performance_report.txt
