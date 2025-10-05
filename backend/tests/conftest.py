"""Pytest configuration and shared fixtures."""

import contextlib
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

# Note: These fixtures use mocks since implementation doesn't exist yet
# They will be updated to use real implementations once T026-T047 are complete


@pytest.fixture(autouse=True)
def reset_database_settings():
    """Reset database settings before each test."""
    from src.db.connection import _db_manager

    # Only reset if database manager already exists
    if _db_manager is not None:
        # Clear settings table to ensure tests start with defaults
        with contextlib.suppress(Exception):
            _db_manager.execute_update(
                "DELETE FROM settings WHERE key != 'schema_version'"
            )

    yield

    # Cleanup after test
    if _db_manager is not None:
        with contextlib.suppress(Exception):
            _db_manager.execute_update(
                "DELETE FROM settings WHERE key != 'schema_version'"
            )


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    # Use real app now that endpoints are implemented
    from src.main import app

    return TestClient(app)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        photos_dir = temp_path / "photos"
        another_dir = temp_path / "another"
        photos_dir.mkdir()
        another_dir.mkdir()
        yield {
            "photos": str(photos_dir),
            "another": str(another_dir),
            "base": str(temp_path),
        }


@pytest.fixture
def sample_photos():
    """Create sample photos in database for testing."""
    from src.db.connection import get_database_manager

    db_manager = get_database_manager()

    # Insert sample photos
    sample_data = [
        (
            1,
            "/test/photo1.jpg",
            "/test",
            "photo1.jpg",
            ".jpg",
            1024,
            1640995200.0,
            1640995200.0,
            "hash1",
        ),
        (
            2,
            "/test/photo2.jpg",
            "/test",
            "photo2.jpg",
            ".jpg",
            2048,
            1640995300.0,
            1640995300.0,
            "hash2",
        ),
        (
            3,
            "/test/photo3.jpg",
            "/test",
            "photo3.jpg",
            ".jpg",
            4096,
            1640995400.0,
            1640995400.0,
            "hash3",
        ),
    ]

    for photo in sample_data:
        with contextlib.suppress(Exception):
            db_manager.execute_update(
                "INSERT OR IGNORE INTO photos (id, path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                photo,
            )

    yield sample_data

    # Cleanup
    with contextlib.suppress(Exception):
        db_manager.execute_update("DELETE FROM photos WHERE id IN (1, 2, 3)")


@pytest.fixture
def enable_face_search():
    """Enable face search for testing."""
    from src.api.config import _update_config_in_db
    from src.db.connection import get_database_manager

    db_manager = get_database_manager()

    # Enable face search
    _update_config_in_db(db_manager, "face_search_enabled", value=True)

    yield True

    # Restore to disabled (default)
    _update_config_in_db(db_manager, "face_search_enabled", value=False)


@pytest.fixture
def sample_photo_data():
    """Sample photo data for testing."""
    return {
        "id": 1,
        "path": "/test/photos/sample.jpg",
        "folder": "/test/photos",
        "filename": "sample.jpg",
        "ext": ".jpg",
        "size": 2048576,
        "created_ts": 1640995200.0,
        "modified_ts": 1640995200.0,
        "sha1": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "phash": "abc123def456",
        "indexed_at": 1640995200.0,
        "index_version": 1,
    }


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return {
        "query": "test query",
        "total_matches": 1,
        "items": [
            {
                "file_id": 1,
                "path": "/test/photos/sample.jpg",
                "folder": "/test/photos",
                "filename": "sample.jpg",
                "thumb_path": "cache/thumbs/da/da39a3ee5e6b4b0d3255bfef95601890afd80709.webp",
                "shot_dt": "2022-01-01T12:00:00Z",
                "score": 0.95,
                "badges": ["OCR"],
                "snippet": "test text found in image",
            }
        ],
        "took_ms": 150,
    }


@pytest.fixture
def sample_person_data():
    """Sample person data for testing."""
    return {
        "id": 1,
        "name": "John Smith",
        "sample_count": 3,
        "created_at": 1640995200.0,
        "updated_at": 1640995200.0,
        "active": True,
    }
