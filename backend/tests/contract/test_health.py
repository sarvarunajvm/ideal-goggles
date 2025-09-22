"""Contract test for GET /health endpoint."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint contract compliance."""

    def test_health_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that health endpoint returns 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_response_schema(self, client: TestClient) -> None:
        """Test that health endpoint returns correct schema."""
        response = client.get("/health")
        data = response.json()

        # Validate required fields exist
        assert "status" in data
        assert "timestamp" in data

        # Validate field types and values
        assert data["status"] == "healthy"
        assert isinstance(data["timestamp"], str)

        # Validate timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"])

    def test_health_endpoint_content_type(self, client: TestClient) -> None:
        """Test that health endpoint returns JSON content type."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_no_authentication_required(self, client: TestClient) -> None:
        """Test that health endpoint works without authentication."""
        # This endpoint should always be accessible
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.performance
    def test_health_endpoint_response_time(self, client: TestClient) -> None:
        """Test that health endpoint responds quickly."""
        import time
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond in < 100ms
