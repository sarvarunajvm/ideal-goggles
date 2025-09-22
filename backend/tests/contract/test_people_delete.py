"""Contract test for DELETE /people/{id} endpoint."""

from fastapi.testclient import TestClient


class TestPeopleDeleteEndpoint:
    """Test people deletion endpoint contract compliance."""

    def test_people_delete_endpoint_returns_204(self, client: TestClient) -> None:
        """Test that people delete endpoint returns 204 status code."""
        response = client.delete("/people/1")
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 204

    def test_people_delete_handles_nonexistent_person(self, client: TestClient) -> None:
        """Test that people delete handles nonexistent person ID."""
        response = client.delete("/people/99999")
        assert response.status_code == 404

    def test_people_delete_validates_integer_id(self, client: TestClient) -> None:
        """Test that people delete validates integer ID parameter."""
        response = client.delete("/people/not_an_integer")
        assert response.status_code == 422
