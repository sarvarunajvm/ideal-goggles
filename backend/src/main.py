"""FastAPI application entry point."""

from pathlib import Path
from typing import Any
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.api import config, health, indexing, people, search
from src.core.config import settings

# Detect whether a bundled UI directory exists before creating the app,
# so we can enable the interactive docs by default when no UI is present.
_UI_AVAILABLE = False
_UI_DIR = None

if getattr(sys, "frozen", False):
    # Running as a packaged binary; look for a bundled UI next to the executable
    exec_dir = Path(sys.executable).resolve().parent
    for candidate in (exec_dir / "frontend" / "dist", exec_dir / "frontend"):
        if (candidate / "index.html").exists():
            _UI_AVAILABLE = True
            _UI_DIR = candidate
            break
else:
    # Dev/runtime from source: treat only built assets as a bundled UI
    for base in (
        Path(__file__).resolve().parent.parent / "frontend",
        Path.cwd() / "frontend",
    ):
        candidate = base / "dist"
        if (candidate / "index.html").exists():
            _UI_AVAILABLE = True
            _UI_DIR = candidate
            break

_DOCS_ENABLED = False  # computed below and reused for root() response

app = FastAPI(
    title="Photo Search API",
    version="1.0.0",
    description="Local API for photo search and navigation system",
    # If no UI is bundled, expose /docs by default; otherwise follow DEBUG.
    docs_url=("/docs" if ((_DOCS_ENABLED := (settings.DEBUG or not _UI_AVAILABLE))) else None),
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(config.router)
app.include_router(indexing.router)
app.include_router(people.router)
app.include_router(search.router)

# Optionally mount a static UI at /ui if a 'frontend' directory is available.
_UI_MOUNTED = False
if _UI_AVAILABLE and _UI_DIR is not None:
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
    _UI_MOUNTED = True


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "message": "Photo Search API",
        "version": "1.0.0",
        "ui": "/ui" if _UI_MOUNTED else None,
        "docs": "/docs" if _DOCS_ENABLED else None,
    }


def main() -> None:
    """Run the application.

    Note: When packaged as a single binary (e.g., with PyInstaller),
    using a string import path like "src.main:app" can fail because
    the module structure isn't importable in the frozen environment.
    Passing the in-memory `app` object avoids that issue.
    """
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        access_log=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
