"""Contract test for POST /search/image endpoint."""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient


class TestImageSearchEndpoint:
    """Test image search endpoint contract compliance."""

    def test_image_search_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that image search endpoint returns 200 status code."""
        # Create a mock image file
        image_data = b"fake_image_data"
        files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}
        response = client.post("/search/image", files=files)
        # Will fail until implemented (mock returns 404)
        assert response.status_code == 200

    def test_image_search_validates_file_parameter(self, client: TestClient) -> None:
        """Test that image search validates file parameter."""
        # Missing file parameter
        response = client.post("/search/image")
        assert response.status_code == 422

    def test_image_search_accepts_image_formats(self, client: TestClient) -> None:
        """Test that image search accepts various image formats."""
        formats = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.tiff", "image/tiff"),
        ]

        for filename, content_type in formats:
            image_data = b"fake_image_data"
            files = {"file": (filename, BytesIO(image_data), content_type)}
            response = client.post("/search/image", files=files)
            # Should accept all supported formats
            assert response.status_code in [200, 400]  # 400 for invalid format is OK

    def test_image_search_rejects_non_image_files(self, client: TestClient) -> None:
        """Test that image search rejects non-image files."""
        text_data = b"not an image"
        files = {"file": ("test.txt", BytesIO(text_data), "text/plain")}
        response = client.post("/search/image", files=files)
        assert response.status_code == 400

    @pytest.mark.performance
    def test_image_search_performance_requirement(self, client: TestClient) -> None:
        """Test that image search meets constitutional performance requirement."""
        import time
        image_data = b"fake_image_data"
        files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}

        start_time = time.time()
        response = client.post("/search/image", files=files)
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Constitutional requirement: <5s for image search
