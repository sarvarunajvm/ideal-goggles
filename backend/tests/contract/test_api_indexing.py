"""
Unit and integration tests for the indexing API.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import app


class TestIndexingAPI:
    """Test suite for indexing endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_start_indexing_success(self, client):
        """Test starting indexing process successfully."""
        # First stop any existing indexing
        client.post("/index/stop")
        response = client.post("/index/start", json={"full": False})
        # Might already be running
        assert response.status_code in [200, 409]
        data = response.json()
        if response.status_code == 200:
            assert "message" in data
            assert "started_at" in data or "full_reindex" in data

    def test_start_indexing_already_running(self, client):
        """Test starting indexing when already running."""
        with patch("src.api.indexing._indexing_state", {"status": "indexing"}):
            response = client.post("/index/start", json={"full": False})
            assert response.status_code == 409
            data = response.json()
            assert "already in progress" in data["detail"].lower()

    def test_stop_indexing_success(self, client):
        """Test stopping indexing process."""
        response = client.post("/index/stop")
        # Returns 400 if nothing is running, 200 if stopped successfully
        assert response.status_code in [200, 400]
        data = response.json()
        if response.status_code == 200:
            assert "message" in data
            assert "status" in data
        else:
            assert "detail" in data

    def test_get_indexing_status(self, client):
        """Test getting indexing status."""
        response = client.get("/index/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data
        assert "errors" in data
        assert data["status"] in [
            "idle",
            "indexing",
            "completed",
            "failed",
            "stopped",
            "error",
        ]

    def test_get_indexing_statistics(self, client):
        """Test getting indexing statistics."""
        # Check stats endpoint
        response = client.get("/index/stats")
        assert response.status_code == 200
        stats = response.json()
        assert isinstance(stats, dict)
        # Check for expected statistics fields - actual API returns different structure
        assert "database" in stats or "database_stats" in stats
        assert "current_indexing" in stats or "index_stats" in stats

    @pytest.mark.parametrize("full_reindex", [True, False])
    def test_indexing_with_parameters(self, client, full_reindex):
        """Test indexing with different parameters."""
        response = client.post("/index/start", json={"full": full_reindex})
        # Should accept the request
        assert response.status_code in [200, 409]  # 409 if already running
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "started_at" in data

    def test_start_indexing_default_params(self, client):
        """Test starting indexing with default parameters."""
        # Send empty body - should use defaults
        response = client.post("/index/start", json={})
        assert response.status_code in [200, 409]
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "started_at" in data

    def test_concurrent_indexing_prevention(self, client):
        """Test that concurrent indexing requests are prevented."""
        with patch("src.api.indexing._indexing_state", {"status": "indexing"}):
            # Try to start another indexing while one is running
            response1 = client.post("/index/start", json={"full": True})
            assert response1.status_code == 409

            response2 = client.post("/index/start", json={"full": False})
            assert response2.status_code == 409
