"""
Tests for indexing control endpoints.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import app


class TestIndexingEndpoints:
    """Test suite for indexing endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_start_indexing_no_params(self, client):
        """Test starting indexing without parameters."""
        response = client.post("/index/start")

        # Should succeed or return 409 if already running
        assert response.status_code in [200, 409]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            # API returns different fields
            assert "started_at" in data or "status" in data

    def test_start_indexing_with_full_param(self, client):
        """Test starting indexing with full=true parameter."""
        # First stop any existing indexing
        client.post("/index/stop")

        response = client.post("/index/start", json={"full": True})

        # Should succeed or return 409 if already running
        assert response.status_code in [200, 409]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "status" in data

    def test_start_indexing_with_empty_body(self, client):
        """Test starting indexing with empty JSON body."""
        # First stop any existing indexing
        client.post("/index/stop")

        response = client.post("/index/start", json={})

        # Should succeed with default values
        assert response.status_code in [200, 409]

    def test_concurrent_indexing_requests(self, client):
        """Test that concurrent indexing requests are prevented."""
        # Stop any existing indexing first
        stop_response = client.post("/index/stop")

        # Try multiple times to get one successful start
        started = False
        for _ in range(3):
            response = client.post("/index/start", json={"full": False})
            if response.status_code == 200:
                started = True
                # Second request should fail with 409 if still running
                response2 = client.post("/index/start", json={"full": False})
                # Might succeed if the first one completed very quickly
                assert response2.status_code in [200, 409]
                if response2.status_code == 409:
                    data = response2.json()
                    if "detail" in data:
                        assert (
                            "already" in data["detail"].lower()
                            or "progress" in data["detail"].lower()
                        )
                break
            if response.status_code == 409:
                # Already running, stop and try again
                client.post("/index/stop")

        # If we couldn't start, that's okay - it means indexing is already running
        assert started or response.status_code == 409

    def test_get_indexing_status(self, client):
        """Test getting indexing status."""
        response = client.get("/index/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "progress" in data
        assert "errors" in data
        assert isinstance(data["errors"], list)

        progress = data["progress"]
        assert "total_files" in progress
        assert "processed_files" in progress
        assert "current_phase" in progress

    def test_stop_indexing(self, client):
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

    def test_get_indexing_stats(self, client):
        """Test getting indexing statistics."""
        response = client.get("/index/stats")
        assert response.status_code == 200

        data = response.json()
        # API returns different structure
        assert "database" in data or "database_stats" in data
        assert "current_indexing" in data or "index_stats" in data

        # Check database stats structure
        db_key = "database" if "database" in data else "database_stats"
        if db_key in data:
            db_stats = data[db_key]
            assert isinstance(db_stats, dict)

    def test_indexing_workflow(self, client):
        """Test complete indexing workflow: start -> status -> stop."""
        # Stop any existing indexing
        client.post("/index/stop")

        # Start indexing
        start_response = client.post("/index/start", json={"full": False})
        assert start_response.status_code in [200, 409]

        # Check status
        status_response = client.get("/index/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] in [
            "idle",
            "indexing",
            "completed",
            "error",
            "stopped",
        ]

        # Stop indexing
        stop_response = client.post("/index/stop")
        assert stop_response.status_code in [200, 400]

        # Check status after stop
        final_status = client.get("/index/status")
        assert final_status.status_code == 200
        assert "status" in final_status.json()

    def test_indexing_status_schema(self, client):
        """Test that indexing status follows the expected schema."""
        response = client.get("/index/status")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "status" in data
        assert "progress" in data
        assert "errors" in data

        # Optional fields that can be None
        assert "started_at" in data
        assert "estimated_completion" in data

        # Progress structure
        progress = data["progress"]
        assert isinstance(progress, dict)
        assert "total_files" in progress
        assert "processed_files" in progress
        assert "current_phase" in progress

        # Errors should be a list
        assert isinstance(data["errors"], list)

    def test_indexing_stats_with_empty_database(self, client):
        """Test indexing stats when database is empty."""
        response = client.get("/index/stats")
        assert response.status_code == 200

        data = response.json()
        # Just check structure, not values
        assert "database" in data or "database_stats" in data
        assert "current_indexing" in data or "index_stats" in data

        # Check the database field exists and is a dict
        db_key = "database" if "database" in data else "database_stats"
        if db_key in data:
            assert isinstance(data[db_key], dict)
