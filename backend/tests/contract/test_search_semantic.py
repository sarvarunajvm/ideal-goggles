"""Contract test for POST /search/semantic endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestSemanticSearchEndpoint:
    """Test semantic search endpoint contract compliance."""

    def test_semantic_search_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that semantic search endpoint returns 200 status code."""
        payload = {"text": "bride on stage", "top_k": 50}
        response = client.post("/search/semantic", json=payload)
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

    def test_semantic_search_validates_required_fields(self, client: TestClient) -> None:
        """Test that semantic search validates required fields."""
        # Missing 'text' field
        payload = {"top_k": 50}
        response = client.post("/search/semantic", json=payload)
        assert response.status_code == 422

    def test_semantic_search_accepts_optional_fields(self, client: TestClient) -> None:
        """Test that semantic search accepts optional top_k parameter."""
        payload = {"text": "wedding photos"}
        response = client.post("/search/semantic", json=payload)
        assert response.status_code == 200

    @pytest.mark.performance
    def test_semantic_search_performance_requirement(self, client: TestClient) -> None:
        """Test that semantic search meets constitutional performance requirement."""
        import time
        payload = {"text": "bride on stage"}
        start_time = time.time()
        response = client.post("/search/semantic", json=payload)
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Constitutional requirement: <5s for vector search