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
        # Note: In TestClient synchronous execution, the first request finishes before second starts.
        # So we can't truly test concurrency here without mocking the lock state.
        # For now, we'll mock the state to simulate concurrent request
        # Manually set state to indexing for testing conflict
        # We need to do this carefully as we are crossing sync/async boundaries with TestClient
        # But _state_manager uses asyncio.Lock.
        # Since we can't easily set async state from sync test without event loop,
        # we will mock the is_indexing method on the manager instance used by the router.
        # Patch the is_indexing method on the imported _state_manager instance
        import unittest.mock

        from src.api.indexing import _state_manager

        # Store original method
        original_is_indexing = _state_manager.is_indexing

        # Mock it to return True
        async def mock_is_indexing():
            return True

        with unittest.mock.patch.object(_state_manager, "is_indexing", side_effect=mock_is_indexing):
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
