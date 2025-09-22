"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

# Note: These fixtures use mocks since implementation doesn't exist yet
# They will be updated to use real implementations once T026-T047 are complete


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    # Mock client since main app doesn't have endpoints implemented yet
    mock_app = Mock()
    mock_client = Mock(spec=TestClient)

    # Configure mock responses for contract tests to FAIL
    # This ensures TDD compliance - tests fail before implementation
    def mock_get(url: str):
        mock_response = Mock()
        mock_response.status_code = 404  # Will fail until implemented
        mock_response.json.return_value = {"error": "Endpoint not implemented"}
        mock_response.headers = {"content-type": "application/json"}
        return mock_response

    def mock_post(url: str, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 404  # Will fail until implemented
        mock_response.json.return_value = {"error": "Endpoint not implemented"}
        mock_response.headers = {"content-type": "application/json"}
        return mock_response

    def mock_delete(url: str):
        mock_response = Mock()
        mock_response.status_code = 404  # Will fail until implemented
        mock_response.json.return_value = {"error": "Endpoint not implemented"}
        mock_response.headers = {"content-type": "application/json"}
        return mock_response

    mock_client.get = mock_get
    mock_client.post = mock_post
    mock_client.delete = mock_delete

    return mock_client


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
        "index_version": 1
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
                "snippet": "test text found in image"
            }
        ],
        "took_ms": 150
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
        "active": True
    }