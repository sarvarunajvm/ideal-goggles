"""FastAPI application entry point."""

import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api import config, dependencies, health, indexing, people, search, batch_operations
from src.core.config import settings
from src.core.logging_config import get_logger, setup_logging
from src.core.middleware import (
    ErrorLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    RequestLoggingMiddleware,
)

# Initialize logging
setup_logging(
    log_level="DEBUG" if settings.DEBUG else "INFO",
    enable_file_logging=True,
    enable_console_logging=True,
    app_name="ideal-goggles-api",
)

logger = get_logger(__name__)

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

# Compute once for clarity and lint friendliness
_DOCS_ENABLED = settings.DEBUG or not _UI_AVAILABLE

app = FastAPI(
    title="Ideal Goggles API",
    version="1.0.8",
    description="Local API for Ideal Goggles",
    # If no UI is bundled, expose /docs by default; otherwise follow DEBUG.
    docs_url="/docs" if _DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add custom middleware for logging and monitoring
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware, threshold_ms=1000)

# CORS middleware for Electron frontend
app.add_middleware(
    CORSMiddleware,
    # Electron renderer in production loads from file:// which presents
    # as Origin "null" for CORS. Allow common local dev origins and
    # permit any origin via regex to avoid startup issues.
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3333",
        "http://127.0.0.1:3333",
        "file://",
        "null",
    ],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(config.router)
app.include_router(dependencies.router)
app.include_router(indexing.router)
app.include_router(people.router)
app.include_router(batch_operations.router)
app.include_router(search.router)

# Mount thumbnails directory for serving generated thumbnails
if settings.THUMBNAILS_DIR and settings.THUMBNAILS_DIR.exists():
    app.mount(
        "/thumbnails",
        StaticFiles(directory=str(settings.THUMBNAILS_DIR)),
        name="thumbnails",
    )
    logger.info(
        f"Mounted thumbnails directory at /thumbnails: {settings.THUMBNAILS_DIR}"
    )

# Optionally mount a static UI at /ui if a 'frontend' directory is available.
_UI_MOUNTED = False
if _UI_AVAILABLE and _UI_DIR is not None:
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
    _UI_MOUNTED = True


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Ideal Goggles API",
        "version": "1.0.8",
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
    logger.info(f"Starting Ideal Goggles API on {settings.HOST}:{settings.PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"UI available: {_UI_AVAILABLE}")
    logger.info(f"Docs enabled: {_DOCS_ENABLED}")

    try:
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            access_log=settings.DEBUG,
        )
    except Exception as e:
        logger.exception(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
