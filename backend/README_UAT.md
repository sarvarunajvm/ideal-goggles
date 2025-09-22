UAT Instructions for Photo Search Backend

Prerequisites
- Docker installed (recommended for UAT)
- Alternatively: Python 3.11 with virtualenv

Quick Start (Docker)
- Build: `docker build -t photo-search-backend:latest .`
- Run: `docker run --rm -p 8000:8000 -v $(pwd)/data:/app/data -v $(pwd)/cache:/app/cache photo-search-backend:latest`
- API base: `http://localhost:8000`
- Health: `GET /health`
- Config: `GET /config`, `GET /config/defaults`
- Roots: `POST /config/roots` with `{"roots": ["/absolute/path"]}`

Compose Option
- `docker-compose up --build`

Local (without Docker)
- `make install`
- `make dev`

Notes
- SQLite DB stored under `./data/photos.db` (mounted in container)
- CORS allows `http://localhost:3000` for frontend UAT
- Swagger docs enabled only when DEBUG=true; for UAT set DEBUG=false if preferred
