"""Contract test for GET /search endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestSearchEndpoint:
    """Test search endpoint contract compliance."""

    def test_search_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that search endpoint returns 200 status code."""
        response = client.get("/search?q=test")
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

    def test_search_endpoint_response_schema(self, client: TestClient) -> None:
        """Test that search endpoint returns correct schema."""
        response = client.get("/search?q=test")
        data = response.json()

        # Validate required fields exist
        assert "query" in data
        assert "total_matches" in data
        assert "items" in data
        assert "took_ms" in data

        # Validate field types
        assert isinstance(data["query"], str)
        assert isinstance(data["total_matches"], int)
        assert isinstance(data["items"], list)
        assert isinstance(data["took_ms"], int)

        # Validate items structure
        for item in data["items"]:
            assert "file_id" in item
            assert "path" in item
            assert "score" in item
            assert "badges" in item

    def test_search_endpoint_query_parameter(self, client: TestClient) -> None:
        """Test search endpoint with query parameter."""
        response = client.get("/search?q=wedding")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "wedding"

    def test_search_endpoint_date_filters(self, client: TestClient) -> None:
        """Test search endpoint with date filters."""
        response = client.get("/search?from=2023-01-01&to=2023-12-31")
        assert response.status_code == 200

    def test_search_endpoint_pagination(self, client: TestClient) -> None:
        """Test search endpoint pagination parameters."""
        response = client.get("/search?limit=10&offset=20")
        assert response.status_code == 200

    @pytest.mark.performance
    def test_search_endpoint_performance_requirement(self, client: TestClient) -> None:
        """Test that search endpoint meets constitutional performance requirement."""
        import time

        start_time = time.time()
        response = client.get("/search?q=test")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Constitutional requirement: <2s
