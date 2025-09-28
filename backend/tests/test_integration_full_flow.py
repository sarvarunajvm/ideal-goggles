"""
Integration tests for complete application workflows.
"""

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.main import app


class TestIntegrationFullFlow:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_health_check_workflow(self, client):
        """Test complete health check workflow."""
        # Basic health check
        response = client.get("/health")
        assert response.status_code == 200
        basic_health = response.json()
        assert basic_health["status"] in ["healthy", "degraded"]

        # Detailed health check
        response = client.get("/health/detailed")
        assert response.status_code == 200
        detailed_health = response.json()
        assert "diagnostics" in detailed_health

        # Readiness check
        response = client.get("/health/ready")
        assert response.status_code == 200
        ready = response.json()
        assert "ready" in ready

    def test_configuration_workflow(self, client):
        """Test complete configuration workflow."""
        # Step 1: Get current configuration
        config = client.get("/config")
        assert config.status_code in [200, 404]

        if config.status_code == 200:
            config_data = config.json()
            # API returns "roots" not "photo_directories"
            assert "roots" in config_data or "photo_directories" in config_data

        # Step 2: Update configuration
        new_config = {"photo_directories": ["/test/photos"], "thumbnail_size": 300}
        response = client.post("/config", json=new_config)
        # Might be 405 if update not allowed
        assert response.status_code in [200, 405]

        # Step 3: Verify configuration (if update succeeded)
        if response.status_code == 200:
            verify = client.get("/config")
            assert verify.status_code == 200

    def test_indexing_and_search_workflow(self, client):
        """Test indexing followed by search workflow."""
        # Stop any existing indexing
        client.post("/index/stop")

        # Step 1: Start indexing
        response = client.post("/index/start", json={"full": False})
        assert response.status_code in [200, 409]

        # Step 2: Check status
        response = client.get("/index/status")
        assert response.status_code == 200
        status = response.json()
        assert "status" in status

        # Step 3: Stop indexing
        response = client.post("/index/stop")
        assert response.status_code in [200, 400]

        # Step 4: Perform search
        response = client.get("/search", params={"q": "test"})
        assert response.status_code == 200

    def test_semantic_search_workflow(self, client):
        """Test semantic search workflow."""
        # Step 1: Ensure system is ready
        response = client.get("/health/ready")
        assert response.status_code == 200

        # Step 2: Text search first
        response = client.get("/search", params={"q": "vacation"})
        assert response.status_code == 200
        text_results = response.json()
        assert "items" in text_results or "results" in text_results

        # Step 3: Semantic search
        response = client.post(
            "/search/semantic", json={"text": "beach vacation photos", "top_k": 20}
        )
        # Service might not be available
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            semantic_results = response.json()
            assert "items" in semantic_results or "results" in semantic_results
            results_key = "items" if "items" in semantic_results else "results"
            assert isinstance(semantic_results[results_key], list)

        # Step 4: Image search
        # Create a minimal valid image
        image_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
            b"\x00\x00\x00\x03\x00\x01^\xf3\xff\x0f\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        response = client.post(
            "/search/image",
            files={"file": ("test.png", image_bytes, "image/png")},
            data={"top_k": 10},
        )
        # Service might not be available
        assert response.status_code in [200, 503]

    def test_error_recovery_workflow(self, client):
        """Test error recovery workflow."""
        # Step 1: Get current status
        response = client.get("/index/status")
        assert response.status_code == 200

        # Step 2: Stop any running process
        response = client.post("/index/stop")
        assert response.status_code in [200, 400]

        # Verify indexing can be restarted after error
        client.post("/index/stop")  # Stop first
        response = client.post("/index/start", json={"full": False})
        assert response.status_code in [200, 409]

        # Step 3: Stop again
        response = client.post("/index/stop")
        assert response.status_code in [200, 400]

    def test_indexing_state_management(self, client):
        """Test indexing state transitions."""
        # Stop any existing indexing
        client.post("/index/stop")

        # Start indexing
        response = client.post("/index/start", json={"full": False})
        start_status = response.status_code

        if start_status == 200:
            # Attempt to start again immediately (should fail if still running)
            response = client.post("/index/start", json={"full": False})
            # Might succeed if the first one completed very quickly
            assert response.status_code in [200, 409]
            if response.status_code == 409:
                # Verify the error message indicates it's already running
                data = response.json()
                assert "detail" in data

        # Stop indexing
        response = client.post("/index/stop")
        assert response.status_code in [200, 400]

        # Can start again after stop
        response = client.post("/index/start", json={"full": True})
        assert response.status_code in [200, 409]

    def test_concurrent_search_requests(self, client):
        """Test handling concurrent search requests."""
        import concurrent.futures

        def search_request(query):
            return client.get("/search", params={"q": query})

        queries = ["test1", "test2", "test3"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(search_request, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        for result in results:
            assert result.status_code == 200

    def test_pagination_workflow(self, client):
        """Test search pagination workflow."""
        # Page 1
        page1 = client.get("/search", params={"q": "test", "limit": 5, "offset": 0})
        assert page1.status_code == 200

        # Page 2
        page2 = client.get("/search", params={"q": "test", "limit": 5, "offset": 5})
        assert page2.status_code == 200

        # Results should be different (if there are results)
        page1_data = page1.json()
        page2_data = page2.json()
        results_key = "items" if "items" in page1_data else "results"

        if page1_data.get(results_key) and page2_data.get(results_key):
            # Check that results are different
            page1_ids = [
                r.get("photo_id", r.get("file_id")) for r in page1_data[results_key]
            ]
            page2_ids = [
                r.get("photo_id", r.get("file_id")) for r in page2_data[results_key]
            ]
            assert page1_ids != page2_ids or len(page1_ids) == 0

    def test_complete_user_journey(self, client, temp_dir):
        """Test a complete user journey through the application."""
        # Step 1: Check system health
        health = client.get("/health")
        assert health.status_code == 200

        # Step 2: Get configuration
        config = client.get("/config")
        # Might not be implemented
        assert config.status_code in [200, 404]

        # Step 3: Stop any existing indexing
        client.post("/index/stop")

        # Step 4: Check indexing status
        status = client.get("/index/status")
        assert status.status_code == 200

        # Step 5: Perform text search
        text_search = client.get("/search", params={"q": "nature"})
        assert text_search.status_code == 200

        # Step 6: Perform semantic search
        semantic_search = client.post(
            "/search/semantic", json={"text": "happy moments", "top_k": 10}
        )
        # Service might not be available
        assert semantic_search.status_code in [200, 503]

        # Step 7: Check people (might not be available)
        people = client.get("/people")
        assert people.status_code in [200, 404]

        # Step 8: Stop indexing
        index_stop = client.post("/index/stop")
        assert index_stop.status_code in [200, 400]

        # Step 9: Final health check
        final_health = client.get("/health")
        assert final_health.status_code == 200
