"""
Consolidated search tests - combining all search endpoint tests in one place.
Eliminates duplication from multiple test files.
"""

import json
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from PIL import Image

from src.main import app

client = TestClient(app)


class TestTextSearch:
    """Tests for text-based search endpoint."""

    def test_search_no_params(self):
        """Test search with no parameters."""
        response = client.get("/search")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "query" in data
        assert "total_matches" in data
        assert "items" in data
        assert "took_ms" in data
        assert isinstance(data["items"], list)

    def test_search_with_query(self):
        """Test search with query parameter."""
        response = client.get("/search", params={"q": "test"})
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["query"] == "test"

        # Verify item structure if results exist
        for item in data["items"]:
            assert "file_id" in item
            assert "path" in item
            assert "score" in item
            assert 0.0 <= item["score"] <= 1.0

    def test_search_with_filters(self):
        """Test search with date and folder filters."""
        response = client.get(
            "/search",
            params={
                "q": "photo",
                "from": "2024-01-01",
                "to": "2024-12-31",
                "folder": "/Photos/2024"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_search_pagination(self):
        """Test search pagination."""
        response = client.get(
            "/search",
            params={"limit": 10, "offset": 20}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) <= 10

    @pytest.mark.performance
    def test_search_performance(self):
        """Test search meets performance requirements."""
        import time
        start = time.time()
        response = client.get("/search", params={"q": "test"})
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        assert duration < 2.0  # Must complete within 2 seconds


class TestSemanticSearch:
    """Tests for semantic search endpoint."""

    def test_semantic_search_basic(self):
        """Test basic semantic search."""
        response = client.post(
            "/search/semantic",
            json={"text": "beach sunset", "top_k": 20}
        )

        # May return 503 if CLIP not installed
        if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            assert "CLIP" in response.json().get("detail", "")
            return

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "beach sunset"

    def test_semantic_search_validation(self):
        """Test semantic search input validation."""
        # Missing text
        response = client.post("/search/semantic", json={"top_k": 50})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Invalid top_k
        response = client.post(
            "/search/semantic",
            json={"text": "test", "top_k": 500}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestImageSearch:
    """Tests for image search endpoint."""

    def test_image_search_valid(self):
        """Test image search with valid image."""
        # Create test image
        img = Image.new('RGB', (100, 100), color='red')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp.name, format='JPEG')
            tmp_path = tmp.name

        try:
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    "/search/image",
                    files={"file": ("test.jpg", f, "image/jpeg")},
                    data={"top_k": 25}
                )

            # May return 503 if CLIP not installed
            if response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
                return

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "Image:" in data["query"]

        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_image_search_invalid_file(self):
        """Test image search with invalid file."""
        response = client.post(
            "/search/image",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            data={"top_k": 50}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestFaceSearch:
    """Tests for face search endpoint."""

    @patch("src.api.search.DatabaseHelper.get_config")
    def test_face_search_disabled(self, mock_config):
        """Test face search when disabled."""
        mock_config.return_value = {"face_search_enabled": False}

        response = client.post(
            "/search/faces",
            json={"person_id": 1, "top_k": 50}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_face_search_validation(self):
        """Test face search input validation."""
        # Missing person_id
        response = client.post("/search/faces", json={"top_k": 50})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPhotoRetrieval:
    """Tests for photo retrieval endpoint."""

    @patch("src.api.search.get_database_manager")
    @patch("src.api.search.os.path.exists")
    def test_get_photo_success(self, mock_exists, mock_db):
        """Test successful photo retrieval."""
        # Setup mocks
        mock_db_instance = MagicMock()
        mock_db_instance.execute_query.return_value = [("/photos/test.jpg",)]
        mock_db.return_value = mock_db_instance
        mock_exists.return_value = True

        # Create temporary test image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            img = Image.new('RGB', (100, 100))
            img.save(tmp.name, format='JPEG')
            tmp_path = tmp.name

        try:
            mock_db_instance.execute_query.return_value = [(tmp_path,)]
            response = client.get("/photos/123/original")
            assert response.status_code == status.HTTP_200_OK
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @patch("src.api.search.get_database_manager")
    def test_get_photo_not_found(self, mock_db):
        """Test photo not found."""
        mock_db_instance = MagicMock()
        mock_db_instance.execute_query.return_value = []
        mock_db.return_value = mock_db_instance

        response = client.get("/photos/999/original")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSearchContract:
    """Contract validation tests."""

    def test_response_schema(self):
        """Test response matches OpenAPI schema."""
        response = client.get("/search", params={"q": "test"})
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Required fields
        required = ["query", "total_matches", "items", "took_ms"]
        for field in required:
            assert field in data

        # Type validation
        assert isinstance(data["query"], str)
        assert isinstance(data["total_matches"], int)
        assert isinstance(data["items"], list)
        assert isinstance(data["took_ms"], int)

        # Item validation
        for item in data["items"]:
            item_required = ["file_id", "path", "folder", "filename", "score", "badges"]
            for field in item_required:
                assert field in item

    def test_error_response_format(self):
        """Test error responses follow standard format."""
        response = client.get("/search", params={"from": "invalid-date"})

        if response.status_code >= 400:
            data = response.json()
            assert "detail" in data or "error" in data

    def test_badges_enum_values(self):
        """Test badges contain only valid values."""
        response = client.get("/search")
        assert response.status_code == status.HTTP_200_OK

        valid_badges = ["filename", "folder", "exif", "image", "face"]
        data = response.json()

        for item in data["items"]:
            for badge in item.get("badges", []):
                assert badge in valid_badges