"""Contract test for POST /index/start endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestIndexStartEndpoint:
    """Test index start endpoint contract compliance."""

    def test_index_start_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that index start endpoint returns 200 status code."""
        payload = {"full": False}
        response = client.post("/index/start", json=payload)
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

    def test_index_start_handles_concurrent_requests(self, client: TestClient) -> None:
        """Test that index start handles concurrent indexing requests."""
        # Start indexing
        response1 = client.post("/index/start", json={"full": False})
        assert response1.status_code == 200

        # Second request while indexing should return 409 Conflict
        response2 = client.post("/index/start", json={"full": False})
        assert response2.status_code == 409

    def test_index_start_accepts_optional_parameters(self, client: TestClient) -> None:
        """Test that index start accepts optional parameters."""
        # No parameters (should use defaults)
        response = client.post("/index/start")
        assert response.status_code == 200

        # With full parameter
        response = client.post("/index/start", json={"full": True})
        assert response.status_code == 200