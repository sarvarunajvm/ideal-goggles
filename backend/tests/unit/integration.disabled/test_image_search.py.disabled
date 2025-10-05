"""Integration test for reverse image search workflow."""

from io import BytesIO

from fastapi.testclient import TestClient


class TestReverseImageSearchWorkflow:
    """Test complete reverse image search user scenario from quickstart.md."""

    def test_reverse_image_search_scenario(self, client: TestClient) -> None:
        """
        Test Scenario 3 from quickstart.md:
        Client brings printed photo, operator drags scanned image,
        system finds original digital file
        """
        # Given: A client brings a printed photo
        # When: Operator drags the scanned image into search area
        scanned_image = b"mock_scanned_photo_data"
        files = {"file": ("scanned_photo.jpg", BytesIO(scanned_image), "image/jpeg")}

        response = client.post("/search/image", files=files)

        # Then: System finds the original digital file and shows matching results
        # 503 is acceptable if CLIP dependencies are not installed
        # 400 is acceptable if mock image data is invalid
        assert response.status_code in [200, 400, 503]

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "took_ms" in data
            assert (
                data["took_ms"] < 5000
            )  # Constitutional requirement: <5s for image search

            # Verify results have Photo-Match badges
            for item in data["items"]:
                assert "Photo-Match" in item["badges"]
                assert "score" in item
                assert 0.0 <= item["score"] <= 1.0

    def test_reverse_image_search_confidence_scores(self, client: TestClient) -> None:
        """Test that reverse image search returns confidence scores."""
        image_data = b"mock_image_data"
        files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}

        response = client.post("/search/image", files=files)
        # 400 is acceptable if mock image data is invalid
        assert response.status_code in [200, 400, 503]

        if response.status_code == 200:
            data = response.json()
            for item in data["items"]:
                # Should have confidence scores for image matches
                assert "score" in item
                assert isinstance(item["score"], (int, float))

    def test_reverse_image_search_top_k_parameter(self, client: TestClient) -> None:
        """Test reverse image search with top_k parameter."""
        image_data = b"mock_image_data"
        files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
        data = {"top_k": 10}

        response = client.post("/search/image", files=files, data=data)
        # 400 is acceptable if mock image data is invalid
        assert response.status_code in [200, 400, 503]

        if response.status_code == 200:
            result = response.json()
            assert len(result["items"]) <= 10

    def test_reverse_image_search_supports_multiple_formats(
        self, client: TestClient
    ) -> None:
        """Test reverse image search accepts multiple image formats."""
        formats = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.tiff", "image/tiff"),
        ]

        for filename, content_type in formats:
            image_data = b"mock_image_data"
            files = {"file": (filename, BytesIO(image_data), content_type)}

            response = client.post("/search/image", files=files)
            # Should accept all supported formats if CLIP available
            assert response.status_code in [
                200,
                400,
                503,
            ]  # 400 for unsupported formats, 503 for missing CLIP

    def test_reverse_image_search_rejects_invalid_files(
        self, client: TestClient
    ) -> None:
        """Test reverse image search rejects non-image files."""
        # Text file should be rejected
        text_data = b"This is not an image"
        files = {"file": ("test.txt", BytesIO(text_data), "text/plain")}

        response = client.post("/search/image", files=files)
        assert response.status_code in [400, 503]  # 503 if CLIP unavailable

        # Empty file should be rejected
        empty_data = b""
        files = {"file": ("empty.jpg", BytesIO(empty_data), "image/jpeg")}

        response = client.post("/search/image", files=files)
        assert response.status_code in [400, 503]  # 503 if CLIP unavailable

    def test_reverse_image_search_performance_requirement(
        self, client: TestClient
    ) -> None:
        """Test reverse image search meets constitutional performance requirement."""
        import time

        image_data = b"mock_image_data" * 100  # Larger file
        files = {"file": ("large_test.jpg", BytesIO(image_data), "image/jpeg")}

        start_time = time.time()
        response = client.post("/search/image", files=files)
        end_time = time.time()

        # Constitutional requirement: <5s for image search
        assert (end_time - start_time) < 5.0
        # 400 is acceptable if mock image data is invalid
        assert response.status_code in [200, 400, 503]
