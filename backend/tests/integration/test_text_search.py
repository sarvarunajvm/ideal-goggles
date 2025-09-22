"""Integration test for text search workflow."""

from fastapi.testclient import TestClient


class TestTextSearchWorkflow:
    """Test complete text search user scenario from quickstart.md."""

    def test_text_search_scenario_wedding_smith_2023(self, client: TestClient) -> None:
        """
        Test Scenario 1 from quickstart.md:
        User searches for 'wedding smith 2023' and gets results within 2 seconds
        """
        # Given: A studio has 500,000 photos indexed
        # (This will be mocked until indexing is implemented)

        # When: Operator searches for "wedding Smith 2023"
        response = client.get("/search?q=wedding%20Smith%202023")

        # Then: Relevant photos appear within 2 seconds with thumbnails and folder paths
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "wedding Smith 2023"
        assert "items" in data
        assert "took_ms" in data
        assert data["took_ms"] < 2000  # Constitutional requirement

        # Verify results structure
        for item in data["items"]:
            assert "file_id" in item
            assert "path" in item
            assert "folder" in item
            assert "filename" in item
            assert "thumb_path" in item
            assert "badges" in item

    def test_text_search_with_ocr_content(self, client: TestClient) -> None:
        """Test text search finds content in OCR extracted text."""
        response = client.get("/search?q=invitation")

        assert response.status_code == 200
        data = response.json()

        # Should find photos with OCR content matching "invitation"
        for item in data["items"]:
            if "OCR" in item["badges"]:
                assert "snippet" in item  # OCR text excerpt

    def test_text_search_with_filename_matches(self, client: TestClient) -> None:
        """Test text search finds matches in filenames."""
        response = client.get("/search?q=IMG_1234")

        assert response.status_code == 200
        data = response.json()

        # Should find photos with filename containing "IMG_1234"
        for item in data["items"]:
            filename_match = "IMG_1234" in item["filename"]
            has_filename_badge = any(
                badge in ["filename", "EXIF"] for badge in item["badges"]
            )
            if filename_match:
                assert has_filename_badge

    def test_text_search_with_folder_path_matches(self, client: TestClient) -> None:
        """Test text search finds matches in folder paths."""
        response = client.get("/search?q=2023/weddings")

        assert response.status_code == 200
        data = response.json()

        # Should find photos in folder paths containing "2023/weddings"
        for item in data["items"]:
            if "2023/weddings" in item["folder"]:
                assert any(badge in ["folder", "EXIF"] for badge in item["badges"])

    def test_text_search_performance_constitutional_requirement(
        self, client: TestClient
    ) -> None:
        """Test that text search meets constitutional performance requirement."""
        import time

        start_time = time.time()
        response = client.get("/search?q=test%20query")
        end_time = time.time()

        # Constitutional requirement: <2s for text search
        assert (end_time - start_time) < 2.0
        assert response.status_code == 200

    def test_text_search_with_date_filters(self, client: TestClient) -> None:
        """Test text search combined with date range filters."""
        response = client.get("/search?q=wedding&from=2023-01-01&to=2023-12-31")

        assert response.status_code == 200
        data = response.json()

        # Results should be filtered to 2023 date range
        for item in data["items"]:
            if item.get("shot_dt"):
                assert "2023" in item["shot_dt"]

    def test_text_search_pagination(self, client: TestClient) -> None:
        """Test text search pagination functionality."""
        # First page
        response1 = client.get("/search?q=test&limit=10&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) <= 10

        # Second page
        response2 = client.get("/search?q=test&limit=10&offset=10")
        assert response2.status_code == 200
        data2 = response2.json()

        # Items should be different between pages
        if len(data1["items"]) > 0 and len(data2["items"]) > 0:
            page1_ids = {item["file_id"] for item in data1["items"]}
            page2_ids = {item["file_id"] for item in data2["items"]}
            assert page1_ids.isdisjoint(page2_ids)  # No overlap
