"""Contract test for POST /config/roots endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestConfigRootsEndpoint:
    """Test configuration roots endpoint contract compliance."""

    def test_config_roots_endpoint_returns_200(self, client: TestClient, temp_dirs) -> None:
        """Test that config/roots endpoint returns 200 for valid request."""
        payload = {"roots": [temp_dirs["photos"], temp_dirs["another"]]}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 200

    def test_config_roots_endpoint_accepts_valid_payload(
        self, client: TestClient, temp_dirs
    ) -> None:
        """Test that config/roots endpoint accepts valid JSON payload."""
        payload = {"roots": [temp_dirs["photos"], temp_dirs["another"]]}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 200

    def test_config_roots_endpoint_validates_required_fields(
        self, client: TestClient
    ) -> None:
        """Test that config/roots endpoint validates required fields."""
        # Missing 'roots' field
        payload = {}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 422  # Validation error

        # Empty payload
        response = client.post("/config/roots")
        assert response.status_code == 422

    def test_config_roots_endpoint_validates_array_type(
        self, client: TestClient
    ) -> None:
        """Test that config/roots endpoint validates roots as array."""
        # roots should be array, not string
        payload = {"roots": "/single/path"}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 422

        # roots should be array, not object
        payload = {"roots": {"path": "/single/path"}}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 422

    def test_config_roots_endpoint_validates_string_elements(
        self, client: TestClient
    ) -> None:
        """Test that config/roots endpoint validates array elements are strings."""
        # Array elements should be strings
        payload = {"roots": [123, 456]}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 422

        # Mixed types should fail
        payload = {"roots": ["/valid/path", 123, None]}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 422

    def test_config_roots_endpoint_handles_empty_array(
        self, client: TestClient
    ) -> None:
        """Test that config/roots endpoint handles empty array."""
        payload = {"roots": []}
        response = client.post("/config/roots", json=payload)
        # Should be valid to clear all roots
        assert response.status_code == 200

    def test_config_roots_endpoint_validates_path_format(
        self, client: TestClient
    ) -> None:
        """Test that config/roots endpoint validates path format."""
        # Empty strings should fail
        payload = {"roots": [""]}
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 422  # Validation error

        # Valid absolute paths should pass - use root directory which should exist
        payload = {"roots": ["/"]}  # Root directory exists on Unix systems
        response = client.post("/config/roots", json=payload)
        assert response.status_code == 200

    def test_config_roots_endpoint_content_type(self, client: TestClient, temp_dirs) -> None:
        """Test that config/roots endpoint returns JSON content type."""
        payload = {"roots": [temp_dirs["photos"]]}
        response = client.post("/config/roots", json=payload)
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.performance
    def test_config_roots_endpoint_response_time(self, client: TestClient, temp_dirs) -> None:
        """Test that config/roots endpoint responds quickly."""
        import time

        payload = {"roots": [temp_dirs["photos"]]}
        start_time = time.time()
        response = client.post("/config/roots", json=payload)
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.5  # Should respond in < 500ms
