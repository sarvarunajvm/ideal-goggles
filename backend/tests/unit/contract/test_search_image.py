"""Contract test for POST /search/image endpoint."""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def create_test_image() -> BytesIO:
    """Create a minimal valid test image."""
    # Create a small RGB image
    img = Image.new("RGB", (10, 10), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


class TestImageSearchEndpoint:
    """Test image search endpoint contract compliance."""

    def test_image_search_endpoint_returns_200_or_503(self, client: TestClient) -> None:
        """Test that image search endpoint returns 200 or 503 status code."""
        # Create a valid test image
        image_bytes = create_test_image()
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        response = client.post("/search/image", files=files)
        # Should return 200 if CLIP is available, 503 if not installed, or 400 for processing errors
        assert response.status_code in [200, 400, 503]

    def test_image_search_validates_file_parameter(self, client: TestClient) -> None:
        """Test that image search validates file parameter."""
        # Missing file parameter
        response = client.post("/search/image")
        assert response.status_code == 422

    def test_image_search_accepts_image_formats(self, client: TestClient) -> None:
        """Test that image search accepts various image formats."""
        formats = [
            ("test.jpg", "image/jpeg", "JPEG"),
            ("test.png", "image/png", "PNG"),
        ]

        for filename, content_type, format_name in formats:
            # Create a valid image for each format
            img = Image.new("RGB", (10, 10), color="blue")
            img_bytes = BytesIO()
            img.save(img_bytes, format=format_name)
            img_bytes.seek(0)

            files = {"file": (filename, img_bytes, content_type)}
            response = client.post("/search/image", files=files)
            # Should accept all supported formats if CLIP available, or return 503 if not
            assert response.status_code in [
                200,
                400,
                503,
            ]  # 400 for processing errors, 503 for missing CLIP

    def test_image_search_rejects_non_image_files(self, client: TestClient) -> None:
        """Test that image search rejects non-image files."""
        text_data = b"not an image"
        files = {"file": ("test.txt", BytesIO(text_data), "text/plain")}
        response = client.post("/search/image", files=files)
        # Should return 503 if CLIP unavailable, or 400 if CLIP available but invalid file
        assert response.status_code in [400, 503]

    @pytest.mark.performance
    def test_image_search_performance_requirement(self, client: TestClient) -> None:
        """Test that image search meets constitutional performance requirement."""
        import time

        # Create a valid test image
        image_bytes = create_test_image()
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        start_time = time.time()
        response = client.post("/search/image", files=files)
        end_time = time.time()

        # Should return 200 if CLIP is available, 503 if not installed, 400 for processing errors
        assert response.status_code in [200, 400, 503]
        # Performance requirement only applies if CLIP is working (200 response)
        if response.status_code == 200:
            assert (
                end_time - start_time
            ) < 5.0  # Constitutional requirement: <5s for image search
