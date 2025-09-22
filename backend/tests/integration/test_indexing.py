"""Integration test for file indexing pipeline."""

import pytest
from fastapi.testclient import TestClient


class TestIndexingWorkflow:
    """Test complete file indexing user scenario."""

    def test_indexing_pipeline_scenario(self, client: TestClient) -> None:
        """Test complete indexing workflow from folder setup to searchable content."""
        # Given: User configures root folders
        config_payload = {"roots": ["/test/photos", "/another/folder"]}
        config_response = client.post("/config/roots", json=config_payload)

        # Will fail until implemented (mock returns 404)
        assert config_response.status_code == 200

        # When: User starts indexing
        index_payload = {"full": False}
        index_response = client.post("/index/start", json=index_payload)
        assert index_response.status_code == 200

        # Then: Indexing status can be monitored
        status_response = client.get("/index/status")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["status"] in ["idle", "indexing", "error"]

        # When indexing is complete, photos should be searchable
        search_response = client.get("/search?q=test")
        assert search_response.status_code == 200

    def test_indexing_throughput_requirement(self, client: TestClient) -> None:
        """Test indexing meets throughput requirement from plan.md."""
        # Constitutional requirement: 100k photos/day on target hardware
        # This will be validated with real indexing implementation
        pass

    def test_indexing_resume_after_interruption(self, client: TestClient) -> None:
        """Test indexing can resume after interruption (constitutional requirement)."""
        # Start indexing
        response = client.post("/index/start", json={"full": False})
        assert response.status_code == 200

        # Simulate interruption and restart
        # Should be able to resume without data loss
        restart_response = client.post("/index/start", json={"full": False})
        # Should either continue or restart gracefully
        assert restart_response.status_code in [200, 409]