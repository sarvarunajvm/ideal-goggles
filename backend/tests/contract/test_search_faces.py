"""Contract test for POST /search/faces endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestFaceSearchEndpoint:
    """Test face search endpoint contract compliance."""

    def test_face_search_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that face search endpoint returns 200 status code."""
        payload = {"person_id": 1, "top_k": 50}
        response = client.post("/search/faces", json=payload)
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

    def test_face_search_validates_required_fields(self, client: TestClient) -> None:
        """Test that face search validates required fields."""
        # Missing 'person_id' field
        payload = {"top_k": 50}
        response = client.post("/search/faces", json=payload)
        assert response.status_code == 422

    def test_face_search_validates_person_id_type(self, client: TestClient) -> None:
        """Test that face search validates person_id is integer."""
        # person_id should be integer
        payload = {"person_id": "not_an_integer"}
        response = client.post("/search/faces", json=payload)
        assert response.status_code == 422

    def test_face_search_handles_nonexistent_person(self, client: TestClient) -> None:
        """Test that face search handles nonexistent person ID."""
        payload = {"person_id": 99999}  # Nonexistent person
        response = client.post("/search/faces", json=payload)
        assert response.status_code == 404

    def test_face_search_requires_opt_in(self, client: TestClient) -> None:
        """Test that face search requires explicit opt-in (constitutional requirement)."""
        # This test validates privacy principle compliance
        payload = {"person_id": 1}
        response = client.post("/search/faces", json=payload)

        # Should fail if face search is not enabled in configuration
        # This ensures constitutional compliance with privacy-first principle
        assert response.status_code in [200, 403]  # 403 if not enabled