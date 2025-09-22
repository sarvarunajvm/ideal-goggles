"""Main FastAPI application for photo search system."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.config import router as config_router

# Import API routers
from src.api.health import router as health_router
from src.api.indexing import router as indexing_router
from src.api.people import router as people_router
from src.api.search import router as search_router

# Import database initialization
from src.db.connection import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".photo-search" / "app.log")
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Photo Search API")

    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception:
        logger.exception("Failed to initialize database")
        raise

    # Create necessary directories
    directories = [
        Path.home() / ".photo-search",
        Path.home() / ".photo-search" / "thumbnails",
        Path.home() / ".photo-search" / "logs"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("Shutting down Photo Search API")


# Create FastAPI application
app = FastAPI(
    title="Photo Search API",
    description="Local API for photo search and navigation system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(_request, exc):
    """Global exception handler for unhandled errors."""
    logger.error("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include API routers
app.include_router(health_router, tags=["Health"])
app.include_router(config_router, prefix="/config", tags=["Configuration"])
app.include_router(search_router, prefix="/search", tags=["Search"])
app.include_router(indexing_router, prefix="/index", tags=["Indexing"])
app.include_router(people_router, prefix="/people", tags=["People"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Photo Search API",
        "version": "1.0.0",
        "description": "Local API for photo search and navigation system",
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    # Run development server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
