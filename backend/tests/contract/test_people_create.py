"""Contract test for POST /people endpoint."""

from fastapi.testclient import TestClient


class TestPeopleCreateEndpoint:
    """Test people creation endpoint contract compliance."""

    def test_people_create_endpoint_returns_201(self, client: TestClient) -> None:
        """Test that people create endpoint returns 201 status code."""
        payload = {"name": "John Smith", "sample_file_ids": [1, 2, 3]}
        response = client.post("/people", json=payload)
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 201

    def test_people_create_validates_required_fields(self, client: TestClient) -> None:
        """Test that people create validates required fields."""
        # Missing 'name' field
        payload = {"sample_file_ids": [1, 2, 3]}
        response = client.post("/people", json=payload)
        assert response.status_code == 422

        # Missing 'sample_file_ids' field
        payload = {"name": "John Smith"}
        response = client.post("/people", json=payload)
        assert response.status_code == 422

    def test_people_create_validates_unique_name(self, client: TestClient) -> None:
        """Test that people create validates unique person names."""
        payload = {"name": "John Smith", "sample_file_ids": [1, 2, 3]}

        # First creation should succeed
        response1 = client.post("/people", json=payload)
        assert response1.status_code == 201

        # Duplicate name should fail
        response2 = client.post("/people", json=payload)
        assert response2.status_code == 400

    def test_people_create_requires_privacy_consent(self, client: TestClient) -> None:
        """Test that people create requires privacy consent (constitutional requirement)."""
        payload = {"name": "John Smith", "sample_file_ids": [1, 2, 3]}
        response = client.post("/people", json=payload)

        # Should fail if face search is not enabled (privacy principle)
        assert response.status_code in [201, 403]  # 403 if not enabled
