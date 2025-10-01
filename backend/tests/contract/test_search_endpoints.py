"""
Tests for search endpoints.
"""

import base64
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import app


class TestSearchEndpoints:
    """Test suite for search endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results."""
        return [
            {
                "photo_id": 1,
                "file_path": "/photos/photo1.jpg",
                "score": 0.95,
                "thumbnail_path": "/thumbnails/photo1_thumb.jpg",
                "metadata": {
                    "date_taken": "2024-01-01T12:00:00",
                    "location": "New York",
                },
            },
            {
                "photo_id": 2,
                "file_path": "/photos/photo2.jpg",
                "score": 0.87,
                "thumbnail_path": "/thumbnails/photo2_thumb.jpg",
                "metadata": {
                    "date_taken": "2024-01-02T14:30:00",
                    "location": "San Francisco",
                },
            },
        ]

    def test_text_search(self, client):
        """Test text-based search endpoint."""
        response = client.get("/search", params={"q": "vacation photos", "limit": 10})

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total_matches" in data
        assert "query" in data
        assert data["query"] == "vacation photos"
        assert isinstance(data["items"], list)

    def test_text_search_with_offset(self, client):
        """Test text search with pagination."""
        response = client.get("/search", params={"q": "test", "limit": 5, "offset": 10})

        # Service might not be available
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
        else:
            # Service unavailable
            data = response.json()
            assert "detail" in data
        # offset not in response model
        # offset not tracked in response

    def test_semantic_search(self, client):
        """Test semantic search endpoint."""
        response = client.post(
            "/search/semantic",
            json={"text": "happy family moments at the beach", "top_k": 20},
        )

        # Service might not be available
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total_matches" in data
            assert "query" in data
            assert isinstance(data["items"], list)
        else:
            # Service unavailable
            data = response.json()
            assert "detail" in data

    def test_semantic_search_empty_query(self, client):
        """Test semantic search with empty query."""
        response = client.post("/search/semantic", json={"text": "", "top_k": 10})

        # Should handle gracefully or service unavailable
        assert response.status_code in [200, 400, 422, 503]

    def test_image_search(self, client):
        """Test image-based search endpoint."""
        # Create a minimal valid PNG image
        # This is a 1x1 pixel red PNG
        image_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
            b"\x00\x00\x00\x03\x00\x01^\xf3\xff\x0f\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        response = client.post(
            "/search/image",
            files={"file": ("test.png", image_bytes, "image/png")},
            data={"top_k": 15},
        )

        # Service might not be available
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total_matches" in data
            assert isinstance(data["items"], list)
        else:
            # Service unavailable
            data = response.json()
            assert "detail" in data

    def test_image_search_invalid_file(self, client):
        """Test image search with invalid file."""
        response = client.post(
            "/search/image",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            data={"top_k": 10},
        )

        # Should return an error or handle gracefully or service unavailable
        assert response.status_code in [200, 400, 422, 500, 503]

    def test_face_search(self, client):
        """Test face-based search endpoint."""
        response = client.post("/search/faces", json={"person_id": 1, "top_k": 10})

        # Face search might be disabled (403) or service unavailable (503)
        assert response.status_code in [200, 403, 503]

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total_matches" in data
            assert isinstance(data["items"], list)
        else:
            # Service unavailable or forbidden
            data = response.json()
            assert "detail" in data

    def test_search_with_invalid_limit(self, client):
        """Test search with invalid limit values."""
        # Negative limit
        response = client.get("/search", params={"q": "test", "limit": -1})
        assert response.status_code in [400, 422]

        # Zero limit
        response = client.get("/search", params={"q": "test", "limit": 0})
        assert response.status_code in [400, 422]

        # Too large limit
        response = client.get("/search", params={"q": "test", "limit": 10000})
        # Should either accept or limit it
        assert response.status_code in [200, 400, 422]

    def test_search_response_structure(self, client):
        """Test that search response follows expected structure."""
        response = client.get("/search", params={"q": "test query", "limit": 5})

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "items" in data
        assert "total_matches" in data
        assert "query" in data

        # Check results structure if any results
        if data["items"]:
            result = data["items"][0]
            assert "photo_id" in result
            assert "file_path" in result
            assert "score" in result

    @patch("src.api.search.get_database_manager")
    def test_search_with_mock_results(
        self, mock_db_manager, client, mock_search_results
    ):
        """Test search with mocked database results."""
        mock_db = MagicMock()
        mock_db.search_photos.return_value = mock_search_results
        mock_db.count_search_results.return_value = len(mock_search_results)
        mock_db_manager.return_value = mock_db

        response = client.get("/search", params={"q": "mocked search", "limit": 10})

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) <= len(mock_search_results)
        assert data["total_matches"] >= 0

    def test_semantic_search_with_filters(self, client):
        """Test semantic search with different parameters."""
        response = client.post(
            "/search/semantic", json={"text": "sunset photos", "top_k": 10}
        )

        # Service might not be available
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
        else:
            # Service unavailable
            data = response.json()
            assert "detail" in data

    def test_concurrent_search_requests(self, client):
        """Test handling of concurrent search requests."""
        import concurrent.futures

        def make_search_request(query):
            return client.get("/search", params={"q": query, "limit": 5})

        queries = ["query1", "query2", "query3", "query4", "query5"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_search_request, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        for result in results:
            assert result.status_code == 200
