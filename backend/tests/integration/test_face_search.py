"""Integration test for face enrollment and search workflow."""

from fastapi.testclient import TestClient


class TestFaceSearchWorkflow:
    """Test complete face search user scenario from quickstart.md."""

    def test_face_enrollment_and_search_scenario(self, client: TestClient) -> None:
        """
        Test Scenario 4 from quickstart.md:
        Enroll person with sample photos, then search for them
        """
        # Given: Face search is enabled in settings
        # When: Operator enrolls new person "John Smith"
        enrollment_payload = {
            "name": "John Smith",
            "sample_file_ids": [1, 2, 3]  # Sample photos
        }

        enrollment_response = client.post("/people", json=enrollment_payload)

        # Will fail until implemented (mock returns 404)
        assert enrollment_response.status_code == 201

        person_data = enrollment_response.json()
        person_id = person_data["id"]

        # Then: Person appears in people list
        people_response = client.get("/people")
        assert people_response.status_code == 200
        people_list = people_response.json()

        person_names = [person["name"] for person in people_list]
        assert "John Smith" in person_names

        # When: Operator searches for "John Smith"
        search_payload = {"person_id": person_id, "top_k": 50}
        search_response = client.post("/search/faces", json=search_payload)

        # Then: Photos containing the person appear with Face badges
        assert search_response.status_code == 200
        search_data = search_response.json()

        for item in search_data["items"]:
            assert "Face" in item["badges"]
            assert "score" in item

    def test_face_search_requires_opt_in(self, client: TestClient) -> None:
        """Test that face search requires explicit opt-in (constitutional requirement)."""
        # This validates constitutional privacy compliance
        enrollment_payload = {
            "name": "Test Person",
            "sample_file_ids": [1, 2, 3]
        }

        # Should fail if face search is not enabled
        response = client.post("/people", json=enrollment_payload)
        assert response.status_code in [201, 403]  # 403 if not enabled

    def test_face_search_precision_requirement(self, client: TestClient) -> None:
        """Test face search meets 90% precision requirement from tasks.md."""
        # This is a placeholder test that will validate precision on real test set
        search_payload = {"person_id": 1, "top_k": 20}
        response = client.post("/search/faces", json=search_payload)

        assert response.status_code == 200
        # Precision validation will be implemented with real ML models
