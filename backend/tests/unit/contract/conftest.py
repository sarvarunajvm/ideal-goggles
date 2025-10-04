"""
Shared fixtures for contract tests.
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
    """Create test client for contract tests."""
    return TestClient(app)


@pytest.fixture
def mock_search_results():
    """Mock search results data for testing."""
    return [
        {
            "photo_id": 1,
            "file_path": "/photos/vacation/beach.jpg",
            "score": 0.95,
            "thumbnail": "base64_thumbnail_data",
            "metadata": {"date_taken": "2024-01-01", "location": "Hawaii"},
        },
        {
            "photo_id": 2,
            "file_path": "/photos/vacation/sunset.jpg",
            "score": 0.87,
            "thumbnail": "base64_thumbnail_data_2",
            "metadata": {"date_taken": "2024-01-02", "location": "California"},
        },
    ]


@pytest.fixture
def mock_database_manager():
    """Mock database manager for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        from src.database.manager import DatabaseManager

        manager = DatabaseManager(str(db_path))
        yield manager


@pytest.fixture
def mock_db_manager_patch(mock_database_manager):
    """Patch database manager getter for API tests."""
    with (
        patch("src.api.search.get_database_manager") as mock_search,
        patch("src.api.indexing.get_database_manager") as mock_indexing,
        patch("src.api.health.get_database_manager") as mock_health,
    ):

        mock_search.return_value = mock_database_manager
        mock_indexing.return_value = mock_database_manager
        mock_health.return_value = mock_database_manager
        yield mock_database_manager


@pytest.fixture
def mock_photo_data():
    """Mock photo data for testing."""
    return {
        "photo_id": 1,
        "file_path": "/test/photos/photo1.jpg",
        "file_size": 1024000,
        "file_hash": "abc123def456",
        "date_taken": "2024-01-01T12:00:00",
        "date_added": "2024-01-01T12:00:00",
        "width": 1920,
        "height": 1080,
        "format": "JPEG",
        "camera_make": "Canon",
        "camera_model": "EOS R5",
        "location_data": {"latitude": 37.7749, "longitude": -122.4194},
        "tags": ["vacation", "beach", "sunset"],
        "description": "Beautiful sunset at the beach",
    }


@pytest.fixture
def valid_png_image():
    """Create a minimal valid PNG image for testing."""
    # This is a 1x1 pixel red PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x00\x03\x00\x01^\xf3\xff\x0f\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture
def indexing_status_data():
    """Mock indexing status data."""
    return {
        "status": "idle",
        "progress": {
            "total_files": 1000,
            "processed_files": 750,
            "current_phase": "Processing images",
        },
        "errors": [],
        "started_at": None,
        "estimated_completion": None,
    }


@pytest.fixture
def health_system_data():
    """Mock system health data."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00",
        "version": "1.0.0",
        "service": "ideal-goggles-api",
        "system": {
            "memory": {"total_gb": 16.0, "available_gb": 8.0, "used_percent": 50.0},
            "disk": {"total_gb": 500.0, "free_gb": 250.0, "used_percent": 50.0},
            "cpu": {"cores": 8},
            "platform": "darwin",
        },
        "database": {"healthy": True, "response_time_ms": 2.5},
        "dependencies": {
            "all_available": True,
            "critical_available": True,
            "dependencies": {
                "PIL": {"available": True, "version": "10.0.0"},
                "numpy": {"available": True, "version": "1.24.0"},
            },
        },
    }
