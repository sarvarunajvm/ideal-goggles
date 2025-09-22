"""Contract test for POST /search/semantic endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestSemanticSearchEndpoint:
    """Test semantic search endpoint contract compliance."""

    def test_semantic_search_endpoint_returns_200_or_503(self, client: TestClient) -> None:
        """Test that semantic search endpoint returns 200 or 503 status code."""
        payload = {"text": "bride on stage", "top_k": 50}
        response = client.post("/search/semantic", json=payload)
        # Should return 200 if CLIP is available, 503 if not installed
        assert response.status_code in [200, 503]

    def test_semantic_search_validates_required_fields(
        self, client: TestClient
    ) -> None:
        """Test that semantic search validates required fields."""
        # Missing 'text' field
        payload = {"top_k": 50}
        response = client.post("/search/semantic", json=payload)
        assert response.status_code == 422

    def test_semantic_search_accepts_optional_fields(self, client: TestClient) -> None:
        """Test that semantic search accepts optional top_k parameter."""
        payload = {"text": "wedding photos"}
        response = client.post("/search/semantic", json=payload)
        # Should return 200 if CLIP is available, 503 if not installed
        assert response.status_code in [200, 503]

    @pytest.mark.performance
    def test_semantic_search_performance_requirement(self, client: TestClient) -> None:
        """Test that semantic search meets constitutional performance requirement."""
        import time

        payload = {"text": "bride on stage"}
        start_time = time.time()
        response = client.post("/search/semantic", json=payload)
        end_time = time.time()

        # Should return 200 if CLIP is available, 503 if not installed
        assert response.status_code in [200, 503]
        # Performance requirement only applies if CLIP is working (200 response)
        if response.status_code == 200:
            assert (
                end_time - start_time
            ) < 5.0  # Constitutional requirement: <5s for vector search
