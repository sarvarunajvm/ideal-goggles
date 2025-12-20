"""
Tests for health check endpoints - comprehensive test suite.
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.main import app


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    # Basic Health Checks
    def test_basic_health_check(self, client):
        """Test the basic /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "service" in data
        assert data["service"] == "ideal-goggles-api"
        assert "system" in data
        assert "database" in data
        assert "dependencies" in data

    @pytest.mark.contract
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

    def test_health_endpoint_no_authentication_required(
        self, client: TestClient
    ) -> None:
        """Test that health endpoint works without authentication."""
        # This endpoint should always be accessible
        response = client.get("/health")
        assert response.status_code == 200

    def test_detailed_health_check(self, client):
        """Test the /health/detailed endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "diagnostics" in data
        assert "uptime" in data["diagnostics"]
        assert "environment" in data["diagnostics"]
        assert "performance" in data["diagnostics"]

    def test_readiness_check(self, client):
        """Test the /health/ready endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert "ready" in data
        assert "timestamp" in data
        assert "checks" in data
        assert isinstance(data["ready"], bool)

    def test_liveness_check(self, client):
        """Test the /health/live endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["alive"] is True
        assert "timestamp" in data
        assert data["service"] == "ideal-goggles-api"

    @patch("src.api.health.get_database_manager")
    def test_health_with_database_failure(self, mock_db_manager, client):
        """Test health check when database is unavailable."""
        mock_db = MagicMock()
        mock_db.execute_query.side_effect = Exception("Database connection failed")
        mock_db_manager.return_value = mock_db

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["database"]["healthy"] is False
        assert "error" in data["database"]

    @patch("src.api.health.psutil")
    def test_health_system_info(self, mock_psutil, client):
        """Test that system information is included in health check."""
        # Mock psutil responses
        mock_memory = MagicMock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = MagicMock()
        mock_disk.total = 500 * 1024**3
        mock_disk.free = 250 * 1024**3
        mock_disk.used = 250 * 1024**3
        mock_psutil.disk_usage.return_value = mock_disk

        mock_psutil.cpu_percent.return_value = 15.5
        mock_psutil.cpu_count.return_value = 8

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        system = data.get("system", {})

        # Check memory info
        assert "memory" in system
        assert "total_gb" in system["memory"]
        assert "available_gb" in system["memory"]
        assert "used_percent" in system["memory"]

        # Check disk info
        assert "disk" in system
        assert "total_gb" in system["disk"]
        assert "free_gb" in system["disk"]
        assert "used_percent" in system["disk"]

        # Check CPU info
        assert "cpu" in system
        assert "cores" in system["cpu"]

        # Check platform
        assert "platform" in system

    def test_health_dependencies_check(self, client):
        """Test that dependency checks are included."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        deps = data.get("dependencies", {})

        assert "dependencies" in deps
        assert "all_available" in deps
        assert "critical_available" in deps

        # Check critical dependencies
        deps_info = deps.get("dependencies", {})
        assert "PIL" in deps_info
        assert "numpy" in deps_info

        # These should be available in test environment
        assert deps_info["PIL"]["available"] is True
        assert deps_info["numpy"]["available"] is True

    # Performance Tests
    @pytest.mark.performance
    def test_health_endpoint_response_time(self, client: TestClient) -> None:
        """Test that health endpoint responds quickly."""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond in < 100ms
