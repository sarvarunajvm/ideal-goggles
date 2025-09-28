"""
Unit tests for the health API endpoint.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app


class TestHealthAPI:
    """Test suite for health endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_health_detailed(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "system" in data
        assert "timestamp" in data
        assert "diagnostics" in data
        assert "uptime" in data["diagnostics"]

    def test_health_ready_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] in [True, False]
        assert "timestamp" in data
        assert "checks" in data

    def test_health_live_check(self, client):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] in [True, False]
        assert "timestamp" in data
