"""Contract test for GET /config endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestConfigEndpoint:
    """Test configuration endpoint contract compliance."""

    def test_config_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that config endpoint returns 200 status code."""
        response = client.get("/config")
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

    def test_config_endpoint_response_schema(self, client: TestClient) -> None:
        """Test that config endpoint returns correct schema."""
        response = client.get("/config")
        data = response.json()

        # Validate required fields exist
        assert "roots" in data
        assert "ocr_languages" in data
        assert "face_search_enabled" in data
        assert "index_version" in data

        # Validate field types
        assert isinstance(data["roots"], list)
        assert isinstance(data["ocr_languages"], list)
        assert isinstance(data["face_search_enabled"], bool)
        assert isinstance(data["index_version"], str)

        # Validate list contents
        for root in data["roots"]:
            assert isinstance(root, str)
        for lang in data["ocr_languages"]:
            assert isinstance(lang, str)

    def test_config_endpoint_default_values(self, client: TestClient) -> None:
        """Test that config endpoint returns expected default values."""
        response = client.get("/config")
        data = response.json()

        # Face search should be disabled by default (privacy requirement)
        assert data["face_search_enabled"] is False

        # OCR should include English and Tamil
        assert "eng" in data["ocr_languages"]
        assert "tam" in data["ocr_languages"]

    def test_config_endpoint_content_type(self, client: TestClient) -> None:
        """Test that config endpoint returns JSON content type."""
        response = client.get("/config")
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.performance
    def test_config_endpoint_response_time(self, client: TestClient) -> None:
        """Test that config endpoint responds quickly."""
        import time
        start_time = time.time()
        response = client.get("/config")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond in < 100ms