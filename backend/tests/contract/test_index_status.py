"""Contract test for GET /index/status endpoint."""

from fastapi.testclient import TestClient


class TestIndexStatusEndpoint:
    """Test index status endpoint contract compliance."""

    def test_index_status_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that index status endpoint returns 200 status code."""
        response = client.get("/index/status")
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

    def test_index_status_response_schema(self, client: TestClient) -> None:
        """Test that index status endpoint returns correct schema."""
        response = client.get("/index/status")
        data = response.json()

        # Validate required fields exist
        assert "status" in data
        assert data["status"] in ["idle", "indexing", "error"]

        # Validate optional fields when present
        if "progress" in data:
            progress = data["progress"]
            assert "total_files" in progress
            assert "processed_files" in progress
            assert "current_phase" in progress
            assert progress["current_phase"] in [
                "discovery",
                "metadata",
                "ocr",
                "embeddings",
                "faces",
            ]
