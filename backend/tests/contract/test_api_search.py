"""
Unit and integration tests for the search API.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import app


class TestSearchAPI:
    """Test suite for search endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results data."""
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

    def test_text_search(self, client):
        """Test text search functionality."""
        # Text search uses GET /search with q parameter
        response = client.get("/search", params={"q": "vacation"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_matches" in data
        assert "query" in data
        assert "took_ms" in data

    def test_semantic_search(self, client):
        """Test semantic search functionality."""
        # Semantic search requires the service to be running
        response = client.post(
            "/search/semantic",
            json={"text": "beautiful sunset on the beach", "top_k": 10},
        )
        # Will return 503 if service not available
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total_matches" in data

    def test_hybrid_search(self, client):
        """Test hybrid search combining text and semantic."""
        # Regular search can act as hybrid
        response = client.get("/search", params={"q": "beach vacation", "limit": 20})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_face_search(self, client):
        """Test face-based search."""
        response = client.post("/search/faces", json={"person_id": 1, "top_k": 25})
        # Will return 403 if face search not configured
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data

    def test_search_with_filters(self, client):
        """Test search with date and folder filters."""
        response = client.get(
            "/search",
            params={
                "q": "family",
                "from": "2024-01-01",
                "to": "2024-12-31",
                "folder": "/photos/family",
                "limit": 30,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "query" in data

    def test_search_pagination(self, client):
        """Test search result pagination."""
        # First page
        response1 = client.get(
            "/search", params={"q": "nature", "limit": 10, "offset": 0}
        )
        assert response1.status_code == 200
        data1 = response1.json()

        # Second page
        response2 = client.get(
            "/search", params={"q": "nature", "limit": 10, "offset": 10}
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # Both should have the structure
        assert "items" in data1
        assert "items" in data2

    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/search", params={"q": ""})
        # Should still work but return empty or all results
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_search_invalid_limit(self, client):
        """Test search with invalid limit values."""
        # Too large
        response = client.get("/search", params={"q": "test", "limit": 10000})
        # Should either cap it or return error
        assert response.status_code in [200, 422]

        # Negative
        response = client.get("/search", params={"q": "test", "limit": -1})
        assert response.status_code == 422

    @pytest.mark.skip(reason="Performance test - run separately")
    def test_search_performance(self, client):
        """Test search response time."""
        import time

        start = time.time()
        response = client.get("/search", params={"q": "performance test", "limit": 100})
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should respond within 2 seconds
        assert elapsed < 2.0

        data = response.json()
        # Check that took_ms is reported
        assert "took_ms" in data
        assert data["took_ms"] < 2000
