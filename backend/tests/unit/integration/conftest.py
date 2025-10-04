"""
Shared fixtures for integration tests.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.main import app


@pytest.fixture
def client():
    """Create test client for integration tests."""
    return TestClient(app)


@pytest.fixture
def temp_photos_dir():
    """Create temporary directory with test photos."""
    with tempfile.TemporaryDirectory(prefix="integration_test_") as temp_dir:
        # Create photos directory structure
        photos_dir = Path(temp_dir) / "photos"
        thumbs_dir = Path(temp_dir) / "thumbs"
        photos_dir.mkdir()
        thumbs_dir.mkdir()

        yield temp_dir


@pytest.fixture
def mock_photos():
    """Generate mock photo records for batch operations."""
    photos = []
    temp_dir = tempfile.mkdtemp(prefix="batch_test_")

    try:
        for i in range(10):  # Smaller number for fixture
            # Create actual test files
            photo_path = os.path.join(temp_dir, f"photo_{i:04d}.jpg")
            thumb_path = os.path.join(temp_dir, "thumbs", f"thumb_{i:04d}.jpg")

            # Create directories if needed
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)

            # Create dummy files
            Path(photo_path).touch()
            Path(thumb_path).touch()

            photos.append(
                {
                    "file_id": i + 1,
                    "path": photo_path,
                    "filename": f"photo_{i:04d}.jpg",
                    "folder": temp_dir,
                    "size": 1024 * 1024 * (i % 5 + 1),  # 1-5 MB files
                    "sha1": f"sha1_{i:040x}",
                    "thumb_path": thumb_path,
                    "_temp_dir": temp_dir,  # Store for cleanup
                }
            )

        yield photos

    finally:
        # Cleanup temp directory
        import contextlib
        import shutil

        with contextlib.suppress(Exception):
            shutil.rmtree(temp_dir)


@pytest.fixture
def mock_database_manager():
    """Mock database manager for integration tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "integration_test.db"
        from src.database.manager import DatabaseManager

        manager = DatabaseManager(str(db_path))
        yield manager


@pytest.fixture
def mock_search_service():
    """Mock search service responses."""
    return {
        "status": "available",
        "text_search": {"enabled": True, "response_time_ms": 50},
        "semantic_search": {"enabled": True, "response_time_ms": 150},
        "image_search": {"enabled": True, "response_time_ms": 200},
        "face_search": {"enabled": False, "reason": "Privacy mode enabled"},
    }


@pytest.fixture
def mock_photo_data():
    """Standard photo data for integration tests."""
    return {
        "photo_id": 1,
        "file_path": "/test/photos/beach_vacation.jpg",
        "file_size": 2048000,
        "file_hash": "abc123def456789",
        "date_taken": "2024-01-15T14:30:00",
        "date_added": "2024-01-15T14:30:00",
        "width": 3840,
        "height": 2160,
        "format": "JPEG",
        "camera_make": "Sony",
        "camera_model": "A7R IV",
        "location_data": {"latitude": 21.3099, "longitude": -157.8581},
        "tags": ["vacation", "beach", "hawaii", "sunset"],
        "description": "Beautiful sunset at Waikiki Beach",
        "thumbnail_path": "/test/thumbs/beach_vacation_thumb.jpg",
        "score": 0.95,
    }


@pytest.fixture
def valid_test_image():
    """Create a valid test image file for upload tests."""
    # Create a minimal valid PNG image (1x1 pixel red)
    image_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x00\x03\x00\x01^\xf3\xff\x0f\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return ("test_image.png", image_data, "image/png")


@pytest.fixture
def mock_indexing_state():
    """Mock indexing state data."""
    return {
        "status": "idle",
        "progress": {
            "total_files": 1000,
            "processed_files": 0,
            "current_phase": "Ready to start",
            "processing_rate": 0.0,
        },
        "errors": [],
        "started_at": None,
        "estimated_completion": None,
        "full_reindex": False,
    }


@pytest.fixture
def enrollment_payload():
    """Sample person enrollment payload for face search tests."""
    return {
        "name": "John Doe",
        "photos": [
            "/photos/john_doe_1.jpg",
            "/photos/john_doe_2.jpg",
        ],
        "consent_given": True,
        "date_enrolled": "2024-01-15T10:00:00",
    }


@pytest.fixture
def search_performance_data():
    """Performance test data for search operations."""
    return {
        "text_search_limit": 2.0,  # seconds
        "semantic_search_limit": 5.0,  # seconds
        "image_search_limit": 5.0,  # seconds
        "face_search_limit": 3.0,  # seconds
        "batch_size": 100,
        "concurrent_requests": 5,
    }
