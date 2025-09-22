"""Contract test for DELETE /people/{id} endpoint."""

from fastapi.testclient import TestClient


class TestPeopleDeleteEndpoint:
    """Test people deletion endpoint contract compliance."""

    def test_people_delete_endpoint_returns_204(self, client: TestClient) -> None:
        """Test that people delete endpoint returns 204 status code."""
        # Create a test person in database first
        from src.db.connection import get_database_manager
        db_manager = get_database_manager()

        # Insert a test person directly to avoid face recognition dependencies
        db_manager.execute_update(
            "INSERT OR IGNORE INTO people (id, name, face_vector, sample_count, created_at, updated_at, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, "Test Person", b"dummy_vector", 0, 1640995200.0, 1640995200.0, 1)
        )

        response = client.delete("/people/1")
        assert response.status_code == 204

    def test_people_delete_handles_nonexistent_person(self, client: TestClient) -> None:
        """Test that people delete handles nonexistent person ID."""
        response = client.delete("/people/99999")
        assert response.status_code == 404

    def test_people_delete_validates_integer_id(self, client: TestClient) -> None:
        """Test that people delete validates integer ID parameter."""
        response = client.delete("/people/not_an_integer")
        assert response.status_code == 422
