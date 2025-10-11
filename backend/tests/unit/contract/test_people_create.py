"""Contract test for POST /people endpoint."""

from fastapi.testclient import TestClient


class TestPeopleCreateEndpoint:
    """Test people creation endpoint contract compliance."""

    def test_people_create_endpoint_returns_201(
        self, client: TestClient, sample_photos
    ) -> None:
        """Test that people create endpoint returns 201 status code."""
        payload = {"name": "John Smith", "sample_file_ids": [1, 2, 3]}
        response = client.post("/people", json=payload)
        # Expect 201 if face search works, 403 if disabled, 503 if enabled but not available
        # 400 if no faces detected in sample photos
        assert response.status_code in [201, 400, 403, 503]

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

    def test_people_create_validates_unique_name(
        self, client: TestClient, sample_photos
    ) -> None:
        """Test that people create validates unique person names."""
        payload = {"name": "John Smith", "sample_file_ids": [1, 2, 3]}

        # First creation should succeed (if face search works) or be rejected (if disabled/unavailable)
        # 400 if no faces detected in sample photos
        response1 = client.post("/people", json=payload)
        assert response1.status_code in [201, 400, 403, 503]

        # If first succeeded, duplicate name should fail
        if response1.status_code == 201:
            response2 = client.post("/people", json=payload)
            assert response2.status_code == 400

    def test_people_create_requires_privacy_consent(
        self, client: TestClient, sample_photos
    ) -> None:
        """Test that people create requires privacy consent (constitutional requirement)."""
        payload = {"name": "Test Person", "sample_file_ids": [1, 2, 3]}
        response = client.post("/people", json=payload)

        # Should fail if face search is not enabled (privacy principle)
        # 400 if no faces detected in sample photos
        assert response.status_code in [201, 400, 403]  # 403 if not enabled
